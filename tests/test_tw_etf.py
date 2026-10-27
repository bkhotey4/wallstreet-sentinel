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
    assert "為什麼" in SI.sec_intraday(e) and "why(q,c,sec)" in SI.JS and len(SI.CORE + SI.SECTORS + SI.CROSS + SI.MEGA) <= 25
    assert "台灣 ETF" in open(os.path.join(os.path.dirname(S.__file__), "build_site.py"), encoding="utf-8").read()


def test_side_menu_zoom():
    """A+ zooms the content area (side menu included): the menu's viewport-sized height must be divided by the zoom,
    or at the largest size its lower part sits below the screen and can't be scrolled to."""
    from tools import site_layout as L
    src = open(L.__file__, encoding="utf-8").read()
    assert "max-height:calc((100vh - 110px) / var(--z,1))" in src
    b = open(os.path.join(os.path.dirname(L.__file__), "build_site.py"), encoding="utf-8").read()
    assert "setProperty('--z'" in b


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
