"""台灣 ETF: TWSE NAV / ex-dividend / TDCC parsers, split repair, total return, 填息, flows vs own history, alerts, page.
Run: python -m tests.test_tw_etf"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, datetime

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_etf_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402


def test_parsers():
    from wsb.data import tw_etf as D
    j = {"a1": [{"msgArray": [
        {"a": "0056", "b": "元大高股息", "c": "14,833,534,000", "d": "24,000,000", "e": "56.55", "f": "56.59", "g": "-0.07", "h": "56.16", "i": "20261027"},
        {"a": "00999", "b": "某ETF(說明)", "c": 1000, "d": 0, "e": 10, "f": 0, "g": "5.0", "h": "-", "i": "20261027"}]}]}
    n = D.parse_nav(j)
    assert n["0056"]["units"] == 14_833_534_000 and n["0056"]["prem"] == -0.07 and n["0056"]["date"] == "2026-10-27"
    assert n["00999"]["prem"] is None and n["00999"]["name"] == "某ETF"           # no NAV → premium unknown, not 5 %
    ex = D.parse_exdiv([{"Date": "1151022", "Code": "0056", "Name": "元大高股息", "Exdividend": "息", "CashDividend": "1.72"},
                        {"Date": "1151103", "Code": "2330", "Name": "台積電", "Exdividend": "息", "CashDividend": "5"},
                        {"Date": "1151103", "Code": "00939", "Name": "統一台灣高息動能", "Exdividend": "息", "CashDividend": ""}])
    assert [x["code"] for x in ex] == ["0056", "00939"] and ex[0]["date"] == "2026-10-22" and ex[1]["cash"] is None
    csv = "﻿資料日期,證券代號,持股分級,人數,股數,占集保庫存數比例%\n20261022,0056  ,1,399989,1,0.77\n20261022,0056  ,17,1741232,2,100.00\n20261022,2330  ,17,5,5,100\n"
    t = D.parse_tdcc(csv, {"0056"})
    assert t["date"] == "2026-10-22" and t["rows"] == {"0056": [1741232.0, 399989.0]}
    assert D.kind_of("00679B") == "債券" and D.kind_of("0050") == "市值型" and D.kind_of("00999", "某高息") == "高股息"


def test_split_repair():
    from wsb.data import tw_etf as D
    c = [["2025-11-13", 350.0], ["2025-11-14", 351.0], ["2025-11-17", 50.2], ["2025-11-18", 50.5]]
    f = D.fix_splits(c)
    assert abs(f[0][1] - 50.0) < 0.01 and f[2][1] == 50.2                       # 1:7 split rescaled
    r = D.fix_splits([["a", 1.4], ["b", 9.6], ["c", 9.7]])                     # 7:1 reverse split (inverse ETF)
    assert abs(r[0][1] - 9.8) < 0.01
    k = D.fix_splits([["a", 100.0], ["b", 55.0]])                              # −45 % but not a whole ratio → kept
    assert k[0][1] == 100.0


def _fixture():
    idx = pd.bdate_range("2023-01-02", "2026-10-27")
    px = pd.Series(range(len(idx)), index=idx, dtype=float) * 0.01 + 30
    ex = idx[-30].strftime("%Y-%m-%d")
    px[idx >= idx[-30]] -= 1.0                                                   # dividend 1.0 not yet recovered
    c = [[d.strftime("%Y-%m-%d"), round(v, 4)] for d, v in px.items()]
    daily = {}
    for i, d in enumerate(pd.bdate_range("2026-07-01", "2026-10-27")):
        daily[d.strftime("%Y-%m-%d")] = {"0056": [1e9 + i * 1e6, 50.0, 0.1], "00679B": [5e8 + (i % 3) * 2e6 - (9e7 if d == pd.Timestamp("2026-10-27") else 0), 26.0, 0.2]}
    nav = {"0056": {"name": "元大高股息", "units": 1e9 + 200e6, "dunits": 1e6, "px": 40.0, "nav": 39.0, "prem": 2.56, "date": "2026-10-27"},
           "00679B": {"name": "元大美債20年", "units": 4e8, "dunits": -9e7, "px": 26.0, "nav": 26.0, "prem": 0.0, "date": "2026-10-27"}}
    return {"nav": nav, "daily": daily, "px": {"0056": {"c": c, "dv": [["2025-10-20", 1.0], [ex, 1.0]]}},
            "holders": {"2026-10-15": {"0056": [1_700_000, 1]}, "2026-10-22": {"0056": [1_741_232, 1]}},
            "exdiv": [{"date": "2026-11-03", "code": "0056", "name": "元大高股息", "cash": 1.0}]}


def test_build_and_alerts():
    from wsb.analytics import tw_etf as A
    r = A.build(d=_fixture(), today=date(2026, 10, 27))
    x = next(z for z in r["rows"] if z["code"] == "0056")
    assert x["fill"]["done"] is False and x["fill"]["days"] >= 28                  # not recovered → shown as open
    assert x["tr1y"] > x["r1y"]                                                    # dividends added back
    assert x["holders_1w"] == 41_232 and abs(x["aum"] - 1.2e9 * 39 / 1e8) < 1e-6
    assert abs(r["exdiv"][0]["yld"] - 2.5) < 1e-9
    assert r["kinds"]["債券"]["z"] is not None and r["kinds"]["債券"]["z"] <= -3    # the redemption day stands out
    assert "淨" in A.headline(r)
    from wsb.bot.app import Sentinel
    bot = Sentinel.__new__(Sentinel)
    al = bot._tw_etf_alerts(r, now=datetime(2026, 10, 27, 18, 0))
    keys = [a.key for a in al]
    assert "etf_prem:0056:2026-10-27" in keys and "etf_flow:債券:2026-10-27" in keys
    assert not any(k.startswith("etf_flow") for k in (a.key for a in bot._tw_etf_alerts(r, now=datetime(2026, 10, 27, 14, 0))))
    empty = A.build(d={}, today=date(2026, 10, 27))
    assert empty["available"] is False and "取不到" in A.headline(empty)


def test_page():
    from wsb.analytics import tw_etf as A
    from tools import site_tw_etf as S

    class Eng:
        pass
    e = Eng()
    e._tw_etf = A.build(d=_fixture(), today=date(2026, 10, 27))
    h = S.sec_etf_flow(e) + S.sec_etf_table(e) + S.sec_etf_div(e)
    assert "一句話看懂" in h and "尚未填息" in h and "0056" in h
    for w in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出"):
        assert w not in h + S.JS, w
    import json as _j
    from wsb.data import tw_etf as D
    D._save(_fixture())
    h2 = S.sec_etf_all(e) + S.sec_etf_tool(e)
    assert "全部台灣 ETF 查詢" in h2 and "api/quote" in S.JS and "hist" in S.JS
    rows = S.all_rows(e)
    assert rows[0][0] == "0056" and rows[0][7] == 1_741_232                      # largest first, holders attached
    for w in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出"):
        assert w not in h2, w
    from tools import site_intraday as SI
    assert "為什麼" in SI.sec_intraday(e) and "why(q,c,sec)" in SI.JS and len(SI.CORE + SI.SECTORS + SI.CROSS) <= 25
    assert len(SI.MEGA) <= 25 and len(SI.TREND) <= 25                          # one request each (quote service cap)
    assert {"能源", "必需消費", "金融", "醫療"} <= {m[2] for m in SI.MEGA}       # every sector's heavyweights, not only tech
    assert {"XLE", "XLP", "CRWV"} <= {t[0] for t in SI.TREND} and "由跌轉漲" in SI.JS
    assert "台灣 ETF" in open(os.path.join(os.path.dirname(S.__file__), "build_site.py"), encoding="utf-8").read()


def test_side_menu_zoom():
    """A+ zooms the content area (side menu included): the menu's viewport-sized height must be divided by the zoom,
    or at the largest size its lower part sits below the screen and can't be scrolled to."""
    from tools import site_layout as L
    src = open(L.__file__, encoding="utf-8").read()
    assert "max-height:calc((100vh - 110px) / var(--z,1))" in src
    b = open(os.path.join(os.path.dirname(L.__file__), "build_site.py"), encoding="utf-8").read()
    assert "setProperty('--z'" in b


def test_why_news_tags():
    """'Why' headlines are candidates tagged with companies and topics; the page keeps only those that line up with what
    moved (a mover named, a matching asset, or the minutes before the day's fastest swing)."""
    import time
    from tools import site_intraday as SI

    class Eng:
        pass
    e = Eng()
    e.news_digest = {"items": [{"title": "Nvidia chips rally as TSMC beats", "ts": time.time(), "topics": ["ai"], "syms": ["NVDA"]},
                               {"title": "Anthropic founders share a trait", "ts": time.time(), "topics": ["ai"], "syms": []},
                               {"title": "Old story", "ts": time.time() - 40 * 3600, "topics": ["market"], "syms": []},
                               {"title": "FLNC SHAREHOLDER NOTICE: Faruqi & Faruqi reminds Fluence Energy investors of class action",
                                "ts": time.time(), "topics": ["power"], "syms": []}]}
    n = SI.why_ctx(e)["news"]
    assert [x["k"] for x in n] == [["ai", "chip"], ["ai"]]                       # 40 h old dropped; chip names tagged
    assert "x.sc>=2" in SI.JS and "TP.chip" in SI.JS and "jp.t-4500" in SI.JS and "kk.length?3:1" in SI.JS
    assert chr(8) not in open(SI.__file__, encoding="utf-8").read()


def test_daily_why_archive():
    """The after-close read is stored per US session (newest rewritten until the next one), older sessions are back-filled
    from prices on the first run, and a reversal against the last 20 sessions is called out."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from tools import site_intraday as SI
    from wsb.analytics import daily_why as DW
    days = [(datetime(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(80)]
    px = {}
    for s in DW._symbols():
        c = [100.0 + (i % 3) * 0.3 for i in range(80)]
        if s == "CRWV":                                  # slides for 20 sessions, then jumps on the last day
            c = [100.0 - 2 * max(0, i - 58) + (i % 2) * 0.5 for i in range(79)] + [70.0]
        if s == "^GSPC":
            c[-1] = c[-2] * 1.007
        px[s] = {"d": days, "c": c}
    DW._save(DW.PX, {"px": px, "day": days[-1], "jump": None, "ts": 0})
    if DW.DAYS.exists():
        DW.DAYS.unlink()

    class Eng:
        pass
    arc = DW.update(Eng(), now=datetime(2026, 3, 22, 17, 0, tzinfo=ZoneInfo("America/New_York")))
    assert days[-1] in arc and not arc[days[-1]].get("backfill") and len(arc) == 6
    assert all(arc[d].get("backfill") for d in days[-6:-1])
    r = arc[days[-1]]
    assert r["one"].startswith("美股"), r
    assert any("CoreWeave" in x and "由跌轉漲" in x for x in r["trend"]), r["trend"]
    h = SI.sec_why_days(Eng())
    assert "每日盤勢解讀" in h and "補建" in h and "<details" in h
    import re
    assert SI.why_ctx and re.search("cse", open(SI.__file__, encoding="utf-8").read(), re.I)


def test_tw_daily_read():
    """Taiwan: Yahoo's holiday bars are dropped and the index rebuilt from the official TWSE closes; an ex-dividend drop
    is added back (not read as a fall); the after-close read names industries and last night's US session."""
    from wsb.analytics import daily_why as DW
    from tools import site_twlive as TL
    px = {"2330.TW": {"d": ["2026-10-21", "2026-10-22", "2026-10-23", "2026-10-27"], "c": [2420.0, 2385.0, 2385.0, 2400.0]},
          "^TWII": {"d": ["2026-10-21", "2026-10-22"], "c": [46887.8, 46041.4]}}
    DW.tw_fix(px, {"2026-10-21": 46887.8, "2026-10-22": 46041.4, "2026-10-27": 46096.2})
    assert px["2330.TW"]["d"] == ["2026-10-21", "2026-10-22", "2026-10-27"] and px["^TWII"]["c"][-1] == 46096.2
    days = [f"2026-{m:02d}-{d:02d}" for m in range(5, 11) for d in range(1, 29)][:120]
    base = {"d": days, "c": [50.0 + (i % 4) * 0.2 for i in range(120)]}
    allpx = {s: {"d": days, "c": list(base["c"])} for s in DW.tw_symbols()}
    allpx["0056.TW"]["c"][-1] = allpx["0056.TW"]["c"][-2] - 1.72                 # ex-dividend day
    allpx["0056.TW"]["dv"] = [[days[-1], 1.72]]
    allpx["2603.TW"]["c"][-1] = allpx["2603.TW"]["c"][-2] * 1.08
    q = DW.quotes(allpx, days[-1])
    assert abs(q["0056.TW"]["chg"]) < 0.5                                         # dividend added back
    r = DW.build_day_tw(allpx, {"flows": [{"d": days[-1], "f": -80.4, "t": 236.0}]}, days[-1])
    assert r and r["one"].startswith("台股") and any("航運" in x for x in r["why"]) and any("外資當天買賣超 -80.4 億" in x for x in r["why"])
    assert len(TL.LEAD) <= 25 and len(TL.GAUGE) <= 25 and len(TL.TREND) <= 25
    assert {"金融", "塑化", "航運", "食品", "電信"} <= {k for _s, _n, k in TL.LEAD}

    class Tw:                                                                     # TaiwanData keeps the newest flow first
        flows = [{"date": "2026-10-27", "foreign": -80.4, "trust": 236.0}, {"date": "2026-10-22", "foreign": -815.8, "trust": 94.9}]
        futures = {}

    class Eng:
        taiwan = Tw()
    assert TL.tw_ctx(Eng())["flows"][-1]["d"] == "2026-10-27"                     # the page reads the last one as the latest
    assert "soxB" in TL.JS and "較舊" in TL.JS                                    # tonight's US session never explains the earlier Taiwan day


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
