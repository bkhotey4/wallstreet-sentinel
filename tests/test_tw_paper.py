"""規則 v1 紙上交易帳本（tools/tw_paper.py）、網站卡（tools/site_twpaper.py）與 Discord 轉送（tools/sec_push.py）——全用假資料，不連網。"""
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from tools import tw_paper as TP

TPE = timezone(timedelta(hours=8))
BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")


def fixture():
    idx = pd.bdate_range("2025-06-02", periods=320)
    n = len(idx)
    rng = np.random.default_rng(0)
    flat = 100 + rng.normal(0, 0.3, n).cumsum() * 0.05
    a = flat.copy()
    k = 260                                              # breakout day (after the start at 255)
    a[k] = 110
    a[k + 1:k + 21] = np.linspace(112, 140, 20)          # +20% reached → half out
    a[k + 21:] = np.linspace(128, 120, n - k - 21)       # back under the 20-day line → rest out
    b = flat + 5                                         # never breaks out
    close = pd.DataFrame({"AAA.TW": a, "BBB.TW": b, "^TWII": np.linspace(30000, 36000, n), "0050.TW": np.linspace(80, 90, n)}, index=idx)
    op = close.shift(1).fillna(close) * 1.0
    op.loc[idx[k + 1], "AAA.TW"] = 111
    hi = np.maximum(close, op) * 1.002
    lo = np.minimum(close, op) * 0.998
    vol = pd.DataFrame(1_000_000.0, index=idx, columns=close.columns)
    vol.loc[idx[k], "AAA.TW"] = 4_000_000
    return {"Open": op, "High": hi, "Low": lo, "Close": close, "Volume": vol}, idx, k


def test_ledger_fills():
    px, idx, k = fixture()
    start = idx[255].strftime("%Y-%m-%d")
    m = TP.ledger(px, TP.MAIN, start, {"AAA": "甲公司"})
    kinds = [(f["sym"], f["kind"]) for f in m["fills"]]
    assert kinds[0] == ("AAA.TW", "entry"), kinds
    e = m["fills"][0]
    assert e["date"] == idx[k + 1].strftime("%Y-%m-%d") and e["px"] == 111 and e["name"] == "甲公司"   # next open, no peeking
    assert abs(e["stop"] - 111 * 0.925) < 0.01 and e["mkt_ok"] is True
    assert ("AAA.TW", "tp") in kinds and kinds[-1][1] in ("trail_ma", "trail_dd"), kinds
    assert m["closed"] == 1 and m["open"] == [] and m["hit"] == 1.0
    assert m["equity"][0][1] == 1.0 and m["bench"][0][1] == 1.0 and m["data_end"] == idx[-1].strftime("%Y-%m-%d")


def test_open_and_next():
    px, idx, k = fixture()
    cut = {key: v.iloc[:k + 1] for key, v in px.items()}            # stop on the breakout day itself
    m = TP.ledger(cut, TP.MAIN, idx[255].strftime("%Y-%m-%d"), {})
    assert m["fills"] == [] and [x["sym"] for x in m["next"]] == ["AAA.TW"] and m["next"][0]["blocked"] is False
    cut = {key: v.iloc[:k + 5] for key, v in px.items()}
    m = TP.ledger(cut, TP.MAIN, idx[255].strftime("%Y-%m-%d"), {})
    assert len(m["open"]) == 1 and m["open"][0]["since"] == idx[k + 1].strftime("%Y-%m-%d") and m["open"][0]["ret"] > 0


def test_due_boundary():
    fri = datetime(2026, 11, 20, 15, 0, tzinfo=TPE)
    assert TP.boundary(fri) == datetime(2026, 11, 20, 14, 30, tzinfo=TPE)
    assert TP.boundary(datetime(2026, 11, 23, 9, 0, tzinfo=TPE)) == datetime(2026, 11, 20, 14, 30, tzinfo=TPE)   # Monday morning → Friday
    st = {"computed_at": "2026-11-20T15:10:00+08:00", "v": TP.V}
    assert not TP.due(st, datetime(2026, 11, 22, 12, 0, tzinfo=TPE))
    assert TP.due(st, datetime(2026, 11, 23, 14, 31, tzinfo=TPE)) and TP.due({}, fri)
    assert TP.due(dict(st, v=0), datetime(2026, 11, 22, 12, 0, tzinfo=TPE))         # old cached version → recompute


def test_public_and_relay():
    from tools import sec_push as SP
    px, idx, k = fixture()
    d = {"computed_at": "x", "main": TP.ledger(px, TP.MAIN, idx[255].strftime("%Y-%m-%d"), {"AAA": "甲公司"})}
    pub = TP.public(d)
    keys = [e["key"] for e in pub["events"]]
    assert keys[0] == f"paper:{idx[k + 1]:%Y-%m-%d}:AAA.TW:entry" and len(set(keys)) == len(keys)
    day = idx[k + 1].to_pydatetime().replace(hour=15, tzinfo=TPE).timestamp()
    todo = SP.paper_todo(pub, {}, day)
    assert [e["kind"] for e in todo] == ["entry"]                     # later fills are in the future of this clock → age < 0
    assert SP.paper_todo(pub, {todo[0]["key"]: day}, day) == []      # already sent
    many = {"events": [dict(todo[0], key=f"paper:x{i}") for i in range(9)]}
    assert len(SP.paper_todo(many, {}, day)) == SP.PAPER_DAY_CAP
    used = {f"paper:y{i}": day for i in range(4)}
    assert len(SP.paper_todo(many, used, day)) == 1                  # 4 already sent today → 1 left
    old = idx[k + 1].to_pydatetime().replace(tzinfo=TPE) + timedelta(days=10)
    assert SP.paper_todo(pub, {}, old.timestamp()) == []              # older than 3 days: a cache rebuild never resends
    for e in pub["events"]:
        em = SP.paper_embed(e)
        txt = em["title"] + em["description"]
        assert "紙上" in txt and not any(b in txt for b in BANNED), txt
        assert "不構成投資建議" not in str(em)


def test_card(monkeypatch=None):
    from tools import site_twpaper as SC
    px, idx, k = fixture()
    start = idx[255].strftime("%Y-%m-%d")
    d = {"computed_at": "2026-11-21T15:00:00+08:00", "start": start, "notional": 1_000_000,
         "universe": {"n": 2, "frozen": "2026-11-21", "source": "測試"}, "mkt": {"twii": 36000, "ma200": 34000, "date": "2026-11-21"},
         "main": TP.ledger(px, TP.MAIN, start, {"AAA": "甲公司"}), "filter": TP.ledger(px, TP.FILT, start, {}), "src": "測試資料"}
    orig = TP.refresh
    TP.refresh = lambda *a, **kw: d
    try:
        html = SC.sec_tw_paper(None)
    finally:
        TP.refresh = orig
    assert "規則 v1 紙上交易成績單" in html and "一句話看懂：規則 v1" in html and "甲公司" in html and "還不到 30 筆" in html
    assert "兩本帳對照" in html and "每一筆紙上成交" in html and not any(b in html for b in BANNED)
    empty = dict(d, main=dict(d["main"], fills=[], open=[], closed=0, equity=[[start, 1.0]]))
    assert "目前還沒有任何進場訊號" in SC.lead(dict(empty, mkt={"twii": 30000, "ma200": 34000}))


def test_engine_unchanged_when_no_log():
    """The research backtest still settles at the end when no event list is given (the report's numbers stay valid)."""
    from tools import tw_rules_backtest as TB
    px, idx, k = fixture()
    pu = {key: v[["AAA.TW", "BBB.TW"]] for key, v in px.items()}
    r = TB.backtest(pu, TB.signals(pu, "B"), TP.MAIN, idx[255].strftime("%Y-%m-%d"), end=idx[k + 5].strftime("%Y-%m-%d"))
    assert "open" not in r and r["trades"] and r["trades"][-1].get("open_at_end")


if __name__ == "__main__":
    for f in (test_ledger_fills, test_open_and_next, test_due_boundary, test_public_and_relay, test_card, test_engine_unchanged_when_no_log):
        f()
    print("test_tw_paper ok")


def test_overlay_official_fills_missing_day():
    import pandas as pd
    from tools import tw_paper as P
    idx = pd.to_datetime(["2026-11-18", "2026-11-19"])
    cols = ["2330.TW", "^TWII"]
    base = pd.DataFrame([[1.0, 1.0], [1.0, 1.0]], index=idx, columns=cols)
    px = {k: base.copy() for k in ("Open", "High", "Low", "Close", "Volume")}
    q = {"^TWII": {"bars": {"2026-11-19": 99.0, "2026-11-20": 36033.29}},
         "2330.TW": {"price": 2000.0, "asof": "2026-11-20", "volume": 5.0}}
    out = P.overlay_official(px, q)
    d = pd.Timestamp("2026-11-20")
    assert out["Close"].at[d, "^TWII"] == 36033.29
    assert out["Close"].at[pd.Timestamp("2026-11-19"), "^TWII"] == 1.0          # Yahoo value kept when present
    assert out["Close"].at[d, "2330.TW"] == 2000.0 and out["Volume"].at[d, "2330.TW"] == 5.0
