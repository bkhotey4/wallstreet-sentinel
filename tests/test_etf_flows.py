"""ETF 資金流向: issuer parsers reject damaged input, a failed fetch keeps the last good data without fresher timestamps,
flows and sums are right, σ waits for enough history, and the card says what is missing.
Run: python -m tests.test_etf_flows"""
from __future__ import annotations

import asyncio
import io
import os
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

import numpy as np

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ef_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_etf_flows as C  # noqa: E402
from wsb.analytics import etf_flows as A  # noqa: E402
from wsb.data import etf_flows as D  # noqa: E402
from wsb.health import HEALTH  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")
TODAY = date.today().isoformat()


def _xlsx(ticker="SPY", tna=800e9, old_tna=790e9):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Fund Name:", "SPDR"])
    ws.append(["Ticker Symbol:", ticker])
    ws.append([None])
    ws.append(["Date", "NAV", "Shares Outstanding", "Total Net Assets"])
    ws.append(["03-Nov-2026", 800.0, 1e9, tna])
    ws.append(["02-Nov-2026", 790.0, 1e9, old_tna])
    ws.append(["The data is provided for information only"])
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


def _ish(sym="HYG", shares="230,400,000", d1="Nov 03, 2026", d2="20261103"):
    return (f'<html><title>iShares Fund | {sym}</title><div data="&quot;sharesOutstanding&quot;:{{&quot;visible&quot;:true,'
            f'&quot;formattedValue&quot;:&quot;{shares}&quot;,&quot;formattedAsOfDate&quot;:&quot;{d1}&quot;}},'
            f'&quot;navAmount&quot;:{{&quot;asOfDate&quot;:{d2},&quot;value&quot;:76.904128}}"></div>')


def _raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def test_parsers():
    assert D.parse_ssga(_xlsx(), "SPY") == [["2026-11-02", 1e9, 790.0], ["2026-11-03", 1e9, 800.0]]
    assert _raises(lambda: D.parse_ssga(_xlsx("QQQ"), "SPY"))                     # someone else's file
    assert _raises(lambda: D.parse_ssga(_xlsx(tna=500e9), "SPY"))                 # newest row disagrees with net assets
    assert len(D.parse_ssga(_xlsx(old_tna=500e9), "SPY")) == 1                    # an old bad row is only a gap
    j = {"ticker": "QQQ", "effectiveBusinessDate": "2026-11-03", "sharesOutstanding": 677800000, "nav": 685.495369,
         "shareclassTotalNetAssets": 464628760791.04}
    assert D.parse_invesco(j, "QQQ") == [["2026-11-03", 677800000.0, 685.495369]]
    assert _raises(lambda: D.parse_invesco({**j, "sharesOutstanding": None}, "QQQ"))   # the API answers 200 with nulls
    assert _raises(lambda: D.parse_invesco({**j, "ticker": None}, "QQQ"))
    assert _raises(lambda: D.parse_invesco({**j, "effectiveBusinessDate": "2099-01-01"}, "QQQ"))
    assert D.parse_ishares(_ish(), "HYG") == [["2026-11-03", 230400000.0, 76.904128]]
    assert _raises(lambda: D.parse_ishares(_ish("LQD"), "HYG"))
    assert _raises(lambda: D.parse_ishares(_ish(d1="Nov 02, 2026"), "HYG"))       # shares and NAV from different days
    assert _raises(lambda: D.parse_ishares("<html><title>Access Denied | HYG</title>captcha</html>", "HYG"))


def _rows(n, start="2024-01-01", shares=1e8, nav=100.0, step=None, seed=1):
    days = np.busday_offset(start, np.arange(n), roll="forward")
    rng = np.random.default_rng(seed)
    out, s = [], shares
    for i, d in enumerate(days):
        s += (step[i] if step is not None else rng.normal(0, 2e5))
        out.append([str(d), float(s), nav])
    return out


def test_failure_keeps_last_good():
    D.FILE = Path(tempfile.mkdtemp()) / "econ_etf_flows.json"
    old = _rows(10)
    t_old = time.time() - 9 * 3600
    D._save({"ts": t_old, "ts_each": {f["sym"]: t_old for f in D.FUNDS}, "funds": {f["sym"]: {"rows": old} for f in D.FUNDS}})
    orig, calls = D.http.get, []

    async def boom(url, **kw):
        calls.append(url)
        raise TimeoutError("down")
    D.http.get = boom
    try:
        d = asyncio.run(D.refresh())
    finally:
        D.http.get = orig
    assert len(calls) == len(D.FUNDS)
    assert d["ts"] == t_old and all(d["ts_each"][f["sym"]] == t_old for f in D.FUNDS)  # no fake freshness
    assert all(d["funds"][f["sym"]]["rows"] == old for f in D.FUNDS) and D.load()["funds"]["SPY"]["rows"] == old
    assert d["funds"]["SPY"]["err"] == "TimeoutError" and HEALTH.sources["etf_flows"].last_err > 0
    assert D.status(d) == (t_old, old[-1][0])
    h = C.sec_etf_flows(None, A.build(d, date.fromisoformat(old[-1][0])))
    assert "最近一次抓取失敗" in h and old[-1][0] in h                                 # shown as old, not as new
    h = C.sec_etf_flows(None, A.build(d, date.fromisoformat(old[-1][0]).replace(year=2030)))
    assert "官方資料已過期" in h
    assert "流" not in A.build(d, date(2030, 1, 1))["lead"].replace("資金流向", "")     # expired data is not read out


def test_one_fund_fails_others_move():
    D.FILE = Path(tempfile.mkdtemp()) / "econ_etf_flows.json"
    orig = D.http.get
    today = date.today().strftime("%b %d, %Y")

    async def fake(url, **kw):
        if "ssga" in url or "invesco" in url:
            raise OSError("blocked")
        sym = next(f["sym"] for f in D.FUNDS if f["url"] == url)
        return _ish(sym, d1=today, d2=date.today().strftime("%Y%m%d"))
    D.http.get = fake
    try:
        d = asyncio.run(D.refresh())
    finally:
        D.http.get = orig
    assert set(d["ts_each"]) == {"HYG", "LQD", "TLT"} and "ts" in d and not d["funds"]["SPY"]["rows"]
    r = A.build(d)
    assert [f["sym"] for f in r["missing"]] == ["SPY", "QQQ"]
    assert "資料累積中" in r["lead"]                                                  # one snapshot gives no flow yet
    h = C.sec_etf_flows(None, r)
    assert "SPY、QQQ 目前沒有驗證成功的官方資料" in h and "資料累積中" in h
    t0 = d["ts_each"]["HYG"]

    async def no_call(url, **kw):
        assert "ishares" not in url, "fetched inside its TTL"
        raise OSError("still blocked")
    D.http.get = no_call
    try:
        assert asyncio.run(D.refresh())["ts_each"]["HYG"] == t0
    finally:
        D.http.get = orig


def test_flows_and_windows():
    rows = [["2026-10-26", 100.0, 10.0], ["2026-10-27", 110.0, 11.0], ["2026-10-28", 105.0, 12.0]]
    fl = A.flows(rows)
    assert fl[0]["amt"] == 10 * 11.0 and fl[1]["amt"] == -5 * 12.0
    assert A.flows([["2026-10-26", 100.0, 100.0], ["2026-10-27", 200.0, 50.0]]) == []     # a 2-for-1 split is not an inflow
    assert D.merge([["2026-10-26", 1.0, 1.0]], [["2026-10-26", 2.0, 1.0], ["2026-10-27", 3.0, 1.0]]) == [["2026-10-26", 2.0, 1.0], ["2026-10-27", 3.0, 1.0]]

    r = _rows(30, step=[1000.0] * 30)
    assert sum(x["amt"] for x in A._window(A.flows(r), 5)) == 5 * 1000 * 100
    assert sum(x["amt"] for x in A._window(A.flows(r), 20)) == 20 * 1000 * 100
    assert A._window(A.flows(r[:4]), 5) is None                                          # too short
    assert A._window(A.flows(r[:20] + r[25:28]), 5) is None                              # days lost across the 5-day start: no sum
    assert sum(x["amt"] for x in A._window(A.flows(r[:26] + r[27:]), 5)) == 5 * 1000 * 100  # a day lost inside it: total still right


def test_sigma_waits_for_history():
    f = D.FUNDS[0]
    short = A.view(f, {"rows": _rows(30)}, date(2024, 2, 12))
    assert short["d1"]["amt"] is not None and short["d1"]["z"] is None and short["d1"]["need_z"] > 0
    step = list(np.random.default_rng(2).normal(0, 2e5, 300))
    step[-1] = -5e6                                                                        # 25σ redemption
    long = A.view(f, {"rows": _rows(300, step=step)}, date(2025, 2, 21))
    assert long["d1"]["z"] < -5 and long["d5"]["z"] is not None and long["d20"]["z"] is not None
    assert long["d1"]["amt"] == -5e6 * 100
    h = C._cell(long["d1"])
    assert "σ" in h and "資料累積中" not in h
    assert "σ 資料累積中" in C._cell(short["d1"])
    empty = A.view(f, {"rows": _rows(1)}, date(2024, 1, 2))
    assert "資料累積中" in C._cell(empty["d5"]) and empty["d5"]["amt"] is None


def _v(sym, s5, z=None):
    c = {"amt": s5, "z": z, "need": 1, "need_z": 1}
    return {"sym": sym, "zh": sym, "stale": False, "d1": c, "d5": c, "d20": c}


def test_plain_reading():
    t = A.reading([_v("HYG", -9e8, -2.4), _v("TLT", 7e8, 1.1), _v("LQD", 2e8, 0.3), _v("SPY", 5e9, 0.5)])
    assert "高收益債（垃圾債）ETF 流出 9.0 億美元" in t and "長天期美債 ETF 流入 7.0 億美元" in t
    assert "投資人變得比較保守" in t and "投資級公司債 ETF 同時流入" in t and "HYG（-2.4σ）" in t and "SPY 近 5 個交易日合計淨流入" in t
    assert "投資人比較願意承擔" in A.reading([_v("HYG", 9e8), _v("TLT", -7e8)])
    assert "還在累積" in A.reading([_v("SPY", -5e9)])
    assert "規模算不算大" in A.reading([_v("HYG", 9e8), _v("TLT", 7e8)])
    for x in (t, C.HOW, C.Z_NOTE):
        for w in BANNED:
            assert w not in x, w


def test_card_empty_and_wiring():
    h = C.sec_etf_flows(None, A.build({}))
    assert "SPY、QQQ、HYG、LQD、TLT 目前沒有驗證成功的官方資料" in h and "資料累積中" in h and "一句話看懂" in h
    for w in BANNED:
        assert w not in h, w
    root = Path(C.__file__).parent
    assert "SEF.sec_etf_flows" in (root / "build_site.py").read_text(encoding="utf-8")
    from tools import site_stamp as ST
    assert ST.CARD["sec_etf_flows"] == ["etf_flows"] and "etf_flows" in ST.SOURCES
    eng = (root.parent / "wsb" / "engine.py").read_text(encoding="utf-8")
    assert eng.count("_etf_flows()") >= 2


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn()
            print("ok", k)
