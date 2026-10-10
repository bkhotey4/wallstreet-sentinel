"""財經日曆＋科技財報（2026-10）：Nasdaq / ForexFactory / Fed / SEC / TWSE 回應格式（tests/fixtures/econ_fixture.json 為實際抓到的
回應裁切），事件分組、意外判定、歷史反應、背景、財報指標、分數、頁面與 AI 快取。     python -m tests.test_econ"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import tests.test_offline as T
import tests.test_expansion as X
from tools import build_site as B
from wsb.ai import econ_ai as EA
from wsb.analytics import macro_events as ME
from wsb.analytics import techearn as TE
from wsb.data import earnings_data as ED
from wsb.data import econcal as EC
from wsb.health import HEALTH

FX = json.loads((Path(__file__).parent / "fixtures" / "econ_fixture.json").read_text(encoding="utf-8"))
TODAY = date(2026, 10, 9)


def _freeze():
    EC.us_today = lambda: TODAY
    TE.us_today = lambda: TODAY
    ED.us_today = lambda: TODAY


def econ_days():
    days = {}
    for q, js in FX["econ"].items():
        d = date.fromisoformat(q) - timedelta(days=1)                # Nasdaq ?date=D lists the events of D-1
        days[d.isoformat()] = {"ts": time.time(), "rows": EC.parse_nasdaq(js, d), "final": True}
    return days


def test_command_names():
    """Two slash commands with the same name crash the bot at start-up (CommandAlreadyRegistered)."""
    import re
    src = (Path(__file__).parent.parent / "wsb" / "bot" / "app.py").read_text(encoding="utf-8")
    names = re.findall(r'@tree\.command\(name="([^"]+)"', src)
    dup = {n for n in names if names.count(n) > 1}
    assert not dup and "econ" in names and "techearn" in names, dup


def test_parsers():
    ap = lambda a, b: abs(a - b) < 1e-6 * max(1, abs(b))  # noqa: E731
    assert EC.num("0.3%") == 0.3 and EC.num("1,701K") == 1701 and ap(EC.num("7.271M"), 7271) and ap(EC.num("-132.07B"), -132.07e6)
    assert EC.num("&nbsp;") is None and EC.num("$4.45") == 4.45 and ap(EC.num("2.929T"), 2.929e9)
    assert EC._utc(date(2026, 12, 9), "15:00") == "2026-12-09T19:00:00Z", "fixed UTC-4 clock (14:00 EST shows as 15:00)"
    assert EC._utc(date(2026, 9, 16), "14:00") == "2026-09-16T18:00:00Z"
    days = econ_days()
    evs = ME.all_events(days, EC.parse_ff(FX["ff"]))
    by = {e["id"]: e for e in evs}
    cpi = by["cpi:2026-09-11"]
    assert [r["label"] for r in cpi["rows"]][:2] == ["核心 CPI 月增", "核心 CPI 年增"] and cpi["rows"][0]["actual"] == "0.3%"
    assert cpi["dir"] == "hot" and cpi["rows"][1]["a"] == 2.4, cpi["rows"]
    ppi = by["ppi:2026-09-10"]                                    # Nasdaq lists PPI y/y BEFORE m/m: split by magnitude
    assert ppi["rows"][0]["actual"] == "0.4%" and ppi["rows"][1]["actual"] == "5.4%" and ppi["dir"] == "inline"
    nfp = by["nfp:2026-10-02"]
    assert nfp["rows"][0]["a"] == 29 and nfp["rows"][0]["c"] == 89 and nfp["dir"] == "cool" and nfp["rows"][1]["label"] == "失業率"
    assert by["nfp:2026-09-04"]["dir"] == "hot"
    fomc = by["fomc:2026-09-16"]
    assert fomc["dir"] == "inline" and fomc["sep"] and fomc["utc"] == "2026-09-16T18:00:00Z"
    assert by["claims:2024-01-04"]["dir"] == "hot", "fewer claims than expected = labour strong (hawkish)"
    assert by["pce:2026-09-30"]["dir"] == "cool" and by["gdp:2026-09-30"]["dir"] == "hot"
    assert by["minutes:2026-10-07"]["released"] and not by["minutes:2026-10-07"]["rows"]
    assert not by["fomc:2026-12-09"]["released"]
    fm = EC.parse_fomc(FX["fed"])
    d = {m["date"]: m["sep"] for m in fm}
    assert d.get("2026-10-28") is False and d.get("2026-12-09") is True, fm[:6]
    # earnings / SEC / Nasdaq / TWSE shapes
    up = ED.parse_cal(FX["earn_up"])
    assert up[0]["sym"] == "TSM" and up[0]["time"] == "pre" and up[0]["eps_f"] == 4.45 and up[0]["mcap"] > 1e12
    past = ED.parse_cal(FX["earn_past"])
    nv = next(r for r in past if r["sym"] == "NVDA")
    assert nv["eps"] == 2.22 and nv["surprise"] == 6.22
    su = ED.parse_surprise(FX["surp"])
    assert su[0]["date"] == "2026-08-26" and su[0]["surp"] == 6.22 and len(su) == 4
    fin = ED.parse_nq_financials(FX["fin"])
    assert fin[-1]["end"] == "2026-07-26" and fin[-1]["rev"] == 96222e6 and fin[-1]["op"] == 63734e6
    cf = {"facts": {"us-gaap": {"Revenues": FX["sec_rev"], "GrossProfit": FX["sec_gp"]}}}
    q = ED.parse_facts(cf)
    ends = [r["end"] for r in q]
    assert "2026-01-25" in ends, "Q4 derived from the fiscal year minus Q1–Q3"
    q4 = next(r for r in q if r["end"] == "2026-01-25")
    assert abs(q4["rev"] - 68127e6) < 2e6 and abs(q4["gp"] - 51093e6) < 2e6, q4
    tw = ED.parse_twrev(FX["tw_l"], "上市")
    assert tw["2330"]["ym"] == "2026-08" and tw["2330"]["yoy"] > 0 and tw["2330"]["ind"] == "半導體業"
    print("  econ / earnings parsers ok")
    return days, q


def test_fixes():
    """Audit fixes 2026-10: DST clock, empty-answer retries, FOMC cross-month, fiscal-Q4 holes, Q4 EPS, currency flag,
    annual cash-burn fallback, goodwill unknown, per-board TW merge, context by label."""
    from wsb.analytics import growth as GR
    tmp = Path("/tmp/wsb_econ_fix")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    # 1) Nasdaq clock: inferred per day from anchors; fixed UTC-4 kept when there is nothing to check or anchors disagree
    us = lambda n, t: {"country": "United States", "eventName": n, "gmt": t, "actual": "", "consensus": "", "previous": ""}  # noqa: E731
    w = EC.parse_nasdaq(FX["econ"]["2024-01-05"], date(2024, 1, 4))
    assert next(r for r in w if r["name"] == "Initial Jobless Claims")["utc"] == "2024-01-04T13:30:00Z", "winter, Nasdaq on UTC-4 (09:30)"
    et = EC.parse_nasdaq({"data": {"rows": [us("CPI", "08:30"), us("Fed Interest Rate Decision", "14:00")]}}, date(2026, 12, 10))
    assert [r["utc"] for r in et] == ["2026-12-10T13:30:00Z", "2026-12-10T19:00:00Z"], "Nasdaq switched to US Eastern (EST)"
    old = EC.parse_nasdaq({"data": {"rows": [us("CPI", "09:30"), us("Fed Interest Rate Decision", "15:00")]}}, date(2026, 12, 10))
    assert [r["utc"] for r in old] == ["2026-12-10T13:30:00Z", "2026-12-10T19:00:00Z"], "Nasdaq still on fixed UTC-4"
    mixed = EC.parse_nasdaq({"data": {"rows": [us("CPI", "08:30"), us("ISM Manufacturing PMI", "11:00"), us("X", "14:00")]}}, date(2026, 12, 1))
    assert mixed[-1]["utc"] == "2026-12-01T18:00:00Z", "anchors disagree → UTC-4"
    assert EC.parse_nasdaq({"data": {"rows": [us("X", "14:00")]}}, date(2026, 12, 1))[0]["utc"] == "2026-12-01T18:00:00Z"
    # 2a) economic calendar: an HTTP-200 empty answer for a weekday is retried with back-off, old rows kept, final after 5 tries
    X_DAY, SAT = TODAY - timedelta(days=7), TODAY - timedelta(days=6)
    calls = []

    async def fake_fetch(d):
        calls.append(d)
        if d in (X_DAY, SAT):
            return [], 0
        return [{"name": "GDP", "utc": None, "actual": "1", "cons": "", "prev": ""}], 3
    saved = (EC._fetch, EC.cfg, EC._FILE)
    EC._fetch, EC._FILE = fake_fetch, tmp / "econ_days.json"
    EC.cfg = lambda: {"days_ahead": 0, "backfill_days": 10, "backfill_per_run": 5, "sleep_s": 0}
    try:
        EC.save({X_DAY.isoformat(): {"ts": 0, "rows": [{"name": "CPI", "utc": None, "actual": "0.3%", "cons": "", "prev": ""}], "final": False}})
        d1 = asyncio.run(EC.refresh(5))
        rx = d1[X_DAY.isoformat()]
        assert rx["empty"] == 1 and not rx["final"] and rx["rows"][0]["name"] == "CPI", rx
        assert d1[SAT.isoformat()]["final"] and "empty" not in d1[SAT.isoformat()], "weekend: empty is normal"
        assert d1[(TODAY - timedelta(days=4)).isoformat()]["final"]
        calls.clear()
        asyncio.run(EC.refresh(5))
        assert X_DAY not in calls, "backing off"
        for i in range(2, 6):
            dd = EC.load()
            dd[X_DAY.isoformat()]["ts"] = 0
            EC.save(dd)
            rx = asyncio.run(EC.refresh(5))[X_DAY.isoformat()]
            assert rx["empty"] == i and rx["final"] == (i >= EC.EMPTY_MAX), rx
        calls.clear()
        dd = EC.load()
        dd[X_DAY.isoformat()]["ts"] = 0
        EC.save(dd)
        asyncio.run(EC.refresh(5))
        assert X_DAY not in calls, "final after 5 empty tries"
    finally:
        EC._fetch, EC.cfg, EC._FILE = saved
    # 2b) earnings calendar: same rule
    ecalls = []

    async def fake_cal(d):
        ecalls.append(d)
        return [] if d == X_DAY else [{"sym": "AAA", "name": "A", "time": "pre", "fq": "", "eps_f": 1.0, "n_est": 1, "eps_ly": 1.0,
                                       "mcap": 1e9, "eps": None, "surprise": None}]
    saved = (ED._cal_day, ED.cfg, ED.F_DAYS)
    ED._cal_day, ED.F_DAYS = fake_cal, tmp / "earn_days.json"
    ED.cfg = lambda: {"cal_back": 8, "cal_ahead": 0}
    try:
        ed1 = asyncio.run(ED.refresh_calendar(30))
        assert ed1[X_DAY.isoformat()]["empty"] == 1 and not ed1[X_DAY.isoformat()]["final"]
        assert ed1[(TODAY - timedelta(days=4)).isoformat()]["final"]
        ecalls.clear()
        asyncio.run(ED.refresh_calendar(30))
        assert X_DAY not in ecalls
        for i in range(2, 6):
            dd = ED._load(ED.F_DAYS)
            dd[X_DAY.isoformat()]["ts"] = 0
            ED._save(ED.F_DAYS, dd)
            rx = asyncio.run(ED.refresh_calendar(30))[X_DAY.isoformat()]
            assert rx["empty"] == i and rx["final"] == (i >= 5), rx
    finally:
        ED._cal_day, ED.cfg, ED.F_DAYS = saved
    # 3) FOMC: cross-month meetings, notation votes ignored
    fm = {m["date"]: m for m in EC.parse_fomc(FX["fed"])}
    assert fm["2024-05-01"]["start"] == "2024-04-30" and fm["2023-02-01"]["start"] == "2023-01-31"
    assert fm["2023-11-01"]["start"] == "2023-10-31" and "2025-08-22" not in fm
    assert not EC.parse_fomc("<html>layout changed</html>")
    # 4) fiscal-Q4 hole of a non-December fiscal year, filled from the annual frame by its END date
    fr = {}
    for per, a5, a6, a7 in (("CY2024Q4", 120, 10, 1), ("CY2025Q1", 90, 11, 2), ("CY2025Q2", 95, 12, 3), ("CY2025Q3", None, 13, 4),
                            ("CY2025Q4", 130, None, None), ("CY2026Q1", 100, 15, 5), ("CY2026Q2", 105, 16, 6), ("CY2024Q3", 88, 9, 1),
                            ("CY2024Q2", 85, 8, 1), ("CY2024Q1", 80, 7, 1)):
        fr[f"Revenues/{per}"] = {"v": {c: v for c, v in (("5", a5), ("6", a6), ("7", a7)) if v is not None}}
    fr["Revenues/CY2025"] = {"v": {"5": 420.0, "6": 50.0, "7": 10.0}, "e": {"5": "2025-09-27", "6": "2025-12-31", "7": "2025-09-27"}}
    fr["EarningsPerShareDiluted/CY2025"] = {"v": {"5": 6.0}, "e": {"5": "2025-09-27"}}
    for per in ("CY2024Q4", "CY2025Q1", "CY2025Q2"):
        fr[f"EarningsPerShareDiluted/{per}"] = {"v": {"5": 1.5}}
    qs = ED.cy_quarters(TODAY, 10)
    rd = ED.FrameReader(fr, qs)
    assert rd.val("rev", "5", "CY2025Q3") == 420 - 120 - 90 - 95, "Sep year-end: CY Q3 = FY − the three quarters before"
    assert rd.val("rev", "6", "CY2025Q4") == 50 - 11 - 12 - 13, "Dec year-end: CY Q4 as before"
    assert rd.val("rev", "7", "CY2025Q4") is None, "never derive a quarter the fiscal year doesn't end in"
    assert rd.tag_val("EarningsPerShareDiluted", "5", "CY2025Q3") is None, "EPS is not additive"
    ed = type("Ed", (), {})()
    ed.frames, ed.nqann = fr, {}
    rows = GR.us_rows(ed, [{"sym": "SEPFY", "name": "Sep FY", "ind": "科技", "mcap": 9e9}], {"SEPFY": {"cik": 5}}, {}, TODAY)
    assert rows and rows[0]["per"] == "2026Q2" and rows[0]["ttm"] == 105 + 100 + 130 + 115, rows
    # 11) companyfacts: derived Q4 EPS is None, revenue still derived
    eps = [{"start": "2025-01-27", "end": "2025-04-27", "val": 0.76, "filed": "2025-05-28"},
           {"start": "2025-04-28", "end": "2025-07-27", "val": 1.08, "filed": "2025-08-27"},
           {"start": "2025-07-28", "end": "2025-10-26", "val": 1.30, "filed": "2025-11-19"},
           {"start": "2025-01-27", "end": "2026-01-25", "val": 4.90, "filed": "2026-02-25"}]
    cf = {"facts": {"us-gaap": {"Revenues": FX["sec_rev"], "EarningsPerShareDiluted": {"units": {"USD/shares": eps}}}}}
    qf = {r["end"]: r for r in ED.parse_facts(cf)}
    assert qf["2026-01-25"]["eps"] is None and qf["2026-01-25"]["rev"] and qf["2025-10-26"]["eps"] == 1.30
    # 5) Nasdaq annual fallback in a foreign currency → listed, unranked, flagged; unknown currency + P/S < 0.3 → suspect
    saved = GR.F_YF
    GR.F_YF = tmp / "sinfo_yf.json"
    GR.F_YF.write_text(json.dumps({"TWX": {"fcur": "TWD", "cur": "USD"}, "USX": {"fcur": "USD"}}), encoding="utf-8")
    try:
        ed.frames = {}
        ed.nqann = {"TWX": {"y": [{"end": "2024-12-31", "rev": 2.9e12, "gp": 1.6e12, "op": 1.3e12, "ni": 1.2e12},
                                  {"end": "2025-12-31", "rev": 3.8e12, "gp": 2.2e12, "op": 1.8e12, "ni": 1.7e12}]},
                    "SUS": {"y": [{"end": "2024-12-31", "rev": 40e9, "gp": None, "op": 2e9, "ni": 1e9},
                                  {"end": "2025-12-31", "rev": 50e9, "gp": None, "op": 3e9, "ni": 2e9}]},
                    "USX": {"y": [{"end": "2024-12-31", "rev": 4e9, "gp": None, "op": 1e9, "ni": 0.5e9},
                                  {"end": "2025-12-31", "rev": 5e9, "gp": None, "op": 1.2e9, "ni": 0.8e9}]}}
        items = [{"sym": "TWX", "name": "TW ADR", "ind": "科技", "mcap": 1.5e12}, {"sym": "SUS", "name": "Sus", "ind": "科技", "mcap": 10e9},
                 {"sym": "USX", "name": "Us", "ind": "科技", "mcap": 20e9}]
        rows = GR.score_us(GR.us_rows(ed, items, {}, {}, TODAY), 0, 15)
        by = {r["sym"]: r for r in rows}
        assert by["TWX"]["flag"] == GR.FLAG_FX and by["TWX"]["score"] is None and by["TWX"]["ps"] is None and by["TWX"]["gav"] is None and abs(by["TWX"]["g"] - 31.03) < 0.01
        assert by["SUS"]["flag"] == GR.FLAG_FX_SUSPECT and by["SUS"]["score"] is None
        assert not by["USX"].get("flag") and by["USX"]["ps"] == 4.0
        packed = GR.pack(rows, GR.US_COLS)
        assert GR.FLAG_FX in [dict(zip(packed["cols"], r))["flag"] for r in packed["rows"]]
    finally:
        GR.F_YF = saved
    # 7) cash burn from the latest annual operating cash flow when quarterly frames are missing; 12) goodwill unknown → no M&A flag
    ed.nqann, fr = {}, {}
    for k, per in enumerate(reversed(qs[1:9])):
        fr[f"Revenues/{per}"] = {"v": {"8": 100e6 * 1.1 ** k}}
    fr[f"Goodwill/{qs[1]}I"] = {"v": {"8": 900e6}}
    fr["NetCashProvidedByUsedInOperatingActivities/CY2025"] = {"v": {"8": -300e6}}
    fr[f"CashAndCashEquivalentsAtCarryingValue/{qs[1]}I"] = {"v": {"8": 600e6}}
    ed.frames = fr
    r8 = GR.us_rows(ed, [{"sym": "BURN", "name": "Burn", "ind": "科技", "mcap": 3e9}], {"BURN": {"cik": 8}}, {}, TODAY)[0]
    assert r8["burn"] == 300e6 and r8["runway"] == 2.0 and r8["burn_basis"] == "年度" and not r8["ma"], r8
    # 6) Taiwan: one board failing keeps that board's previous rows
    from wsb.data import http as H
    saved = (H.get, ED.F_TW, ED.F_TWPE)
    ED.F_TW, ED.F_TWPE = tmp / "tw.json", tmp / "twpe.json"
    ED._save(ED.F_TW, {"ts": 0, "months": {}, "latest": {
        "2330": {"code": "2330", "name": "台積電", "ind": "半導體業", "board": "上市", "ym": "2026-07", "rev": 1.0, "mom": 0, "yoy": 1, "cum_yoy": 1, "ly": 1},
        "3105": {"code": "3105", "name": "穩懋", "ind": "半導體業", "board": "上櫃", "ym": "2026-07", "rev": 2.0, "mom": 0, "yoy": 5, "cum_yoy": 4, "ly": 1}}})
    ED._save(ED.F_TWPE, {"ts": 0, "v": {"3105": {"pe": 12.0, "pb": 1.5, "dy": 2.0, "name": "穩懋", "board": "上櫃"}}})

    async def half_down(url, **kw):
        if "tpex" in url:
            raise RuntimeError("TPEx down")
        return FX["tw_l"] if "t187ap05" in url else [{"Code": "2330", "Name": "台積電", "PEratio": "25.0", "DividendYield": "1.5", "PBratio": "7.0"}]
    H.get = half_down
    try:
        tw = asyncio.run(ED.refresh_twrev())
        assert tw["latest"]["2330"]["ym"] == "2026-08" and tw["latest"]["3105"]["ym"] == "2026-07", "OTC rows kept"
        pe = asyncio.run(ED.refresh_twpe())
        assert pe["v"]["2330"]["pe"] == 25.0 and pe["v"]["3105"]["pe"] == 12.0
    finally:
        H.get, ED.F_TW, ED.F_TWPE = saved
    # 13) context reads rows by label: a missing payrolls row can't turn the unemployment rate into "payrolls"
    past = [{"key": "nfp", "date": "2026-10-02", "rows": [{"label": "失業率", "a": 4.3}]},
            {"key": "cpi", "date": "2026-09-11", "rows": [{"label": "CPI 年增", "a": 2.9}]}]
    ctx = ME.context(past, [], None)
    assert ctx["labor"] == "失業率 4.3%" and ctx["inflation"] == "", ctx
    print("  audit fixes ok")


def make_eng(tmp: Path, days, q):
    eng = X.make_engine(tmp)
    eng.econ.days, eng.econ.ff, eng.econ.fomc = days, EC.parse_ff(FX["ff"]), EC.parse_fomc(FX["fed"])
    eng.earnings.days = {"2026-10-15": {"ts": time.time(), "rows": ED.parse_cal(FX["earn_up"])},
                         "2026-08-26": {"ts": time.time(), "rows": ED.parse_cal(FX["earn_past"])},
                         "2026-10-07": {"ts": time.time(), "rows": [{"sym": "AMD", "name": "AMD", "time": "after", "fq": "Sep/2026", "eps_f": 1.1,
                                                                     "n_est": 20, "eps_ly": 0.9, "mcap": 4e11, "eps": 1.25, "surprise": 13.6}]}}
    rng = np.random.default_rng(1)
    facts = {"NVDA": {"ts": time.time(), "q": q}}
    surp = {"NVDA": {"ts": time.time(), "rows": ED.parse_surprise(FX["surp"])}}
    for i, s in enumerate(["AMD", "AVGO", "MU", "INTC", "MSFT", "ORCL", "CRWD", "TSM"]):
        g = 0.03 * (5 - i)
        ends = [(date(2024, 9, 30) + timedelta(days=91 * k)).isoformat() for k in range(9)]
        rows = []
        for k, e in enumerate(ends):
            rev = 1e10 * (1 + g) ** k
            rows.append({"end": e, "rev": rev, "gp": rev * (0.45 + 0.01 * k * (1 if i % 2 == 0 else -1)), "op": rev * 0.2, "ni": rev * 0.15,
                         "eps": 1 + 0.05 * k * (1 if i < 6 else -1), "rnd": rev * 0.2, "inv": 1e9 * (1.25 ** k if i == 2 else 1.0)})
        facts[s] = {"ts": time.time(), "q": rows}
        surp[s] = {"ts": time.time(), "rows": [{"fq": f"Q{j}", "date": (date(2026, 8, 20) - timedelta(days=91 * j)).isoformat(), "eps": 1.0,
                                                "cons": 0.95, "surp": float(rng.normal(3, 4))} for j in range(4)]}
    surp["AMD"]["rows"][0]["date"] = "2026-10-07"
    eng.earnings.facts, eng.earnings.surprise = facts, surp
    eng.earnings.tw = {"ts": time.time(), "latest": {**ED.parse_twrev(FX["tw_l"], "上市"), **ED.parse_twrev(FX["tw_o"], "上櫃")},
                       "months": {"2026-07": {"2330": {"yoy": 20}}, "2026-08": {"2330": {"yoy": 53}}}}
    return eng


def main():
    _freeze()
    test_command_names()
    days, q = test_parsers()
    test_fixes()
    tmp = Path("/tmp/wsb_econ")
    shutil.rmtree(tmp, ignore_errors=True)
    eng = make_eng(tmp, days, q)
    # market history must cover the event dates for the reaction stats
    h = eng.market.history
    assert "^NDX" in h.columns and "^TNX" in h.columns, h.columns[:20]
    HEALTH.ok("yahoo_quotes", 90, every=300)
    asyncio.run(eng.recompute())
    ev = eng.econ_view
    assert ev["available"] and ev["asof"] == "2026-10-09"
    ids = [e["id"] for e in ev["events"]]
    assert "fomc:2026-10-28" in ids and "fomc:2026-12-09" in ids and "cpi:2026-10-14" in ids, ids[-20:]
    cpi_next = next(e for e in ev["events"] if e["id"] == "cpi:2026-10-14")
    assert not cpi_next["released"] and cpi_next["tpe"].startswith("10/14 20:30") and cpi_next["et"] == "08:30" and cpi_next["scen"]
    dec = next(e for e in ev["events"] if e["id"] == "fomc:2026-12-09")
    assert dec["sep"] and dec["tpe"].startswith("12/10 03:00")
    assert ev["next_fomc"]["date"] == "2026-10-28"
    st = ev["stats"]
    assert st["cpi"]["n"] >= 1 and "hot" in st["cpi"]["by"] and st["nfp"]["by"]["cool"]["n"] >= 1
    assert "核心 CPI 年增 2.4%" in ev["context"]["inflation"] and "失業率 4.2%" in ev["context"]["labor"], ev["context"]
    assert "聯準會政策利率上限 4.00%" in ev["context"]["fed"] and "10/28" not in ev["context"]["fed"]
    lines = ME.summary_lines(ev)
    assert lines and "CPI" in lines[0], lines
    # tech earnings
    te = eng.techearn
    assert te["available"] and len(te["rows"]) == len(eng.tech_symbols())
    nv = next(r for r in te["rows"] if r["sym"] == "NVDA")
    assert nv["end"] == "2026-07-26" and 100 < nv["rev_yoy"] < 110, nv["rev_yoy"]          # 96.2 / 46.7 − 1
    assert nv["gm"] and nv["s"]["beats"] == 4 and nv["s"]["last_date"] == "2026-08-26" and nv["score"] is not None
    assert any("連 4 季" in t for t, _ in nv["tags"]) and "營收年增" in nv["verdict"]
    mu = next(r for r in te["rows"] if r["sym"] == "MU")
    assert any("庫存" in t for t, _ in mu["tags"]), mu["tags"]
    scores = [r["score"] for r in te["rows"] if r["score"] is not None]
    assert scores == sorted(scores, reverse=True) and all(0 <= s <= 100 for s in scores)
    assert te["groups"] and te["groups"][0]["theme"] == "半導體" and te["season"]["n"] >= 1
    cal = te["calendar"]
    assert any(x["sym"] == "TSM" and x["tech"] for x in cal["up"]) and any(x["sym"] == "AMD" and x["surp"] == 13.6 for x in cal["past"])
    assert all(x["cur"] or (x["mcap"] or 0) >= 20e9 for x in cal["up"])
    tws = te["tw"]
    assert tws["available"] and tws["industries"][0]["ind"] in ED.TW_ELEC and any(x["code"] == "2330" for x in tws["curated"])
    tt = TE.tw_table(eng.earnings)
    row = dict(zip(tt["cols"], next(r for r in tt["rows"] if r[0] == "2330")))
    assert row["streak"] == 2 and row["cur"] and row["rev"] > 5000, row
    # whole-market US tech from SEC frames (Q4 derived from the calendar-year frame)
    ed = eng.earnings
    ed.frames = {}
    for per, rv in (("CY2026Q2", 120), ("CY2025Q2", 100), ("CY2026Q1", 110), ("CY2025Q1", 95), ("CY2025Q3", 104), ("CY2025", 420)):
        ed.frames[f"Revenues/{per}"] = {"ts": 0, "v": {"1": rv * 1e6, "2": rv * 2e6}}
        ed.frames[f"GrossProfit/{per}"] = {"ts": 0, "v": {"1": rv * 0.5e6}}
    ut = TE.ustech(ed, [{"sym": "AAA", "name": "A", "sub": "Software", "mcap": 5e9}, {"sym": "BBB", "name": "B", "sub": "Chips", "mcap": 9e9}],
                   {"AAA": {"cik": 1}, "BBB": {"cik": 2}}, TODAY)
    r0 = dict(zip(ut["cols"], ut["rows"][1]))
    assert ut["n"] == 2 and r0["q"] == "2026Q2" and r0["yoy"] == 20.0 and r0["gm"] == 50.0 and r0["qoq"] == round((120 / 110 - 1) * 100, 1)
    ed.frames = {k: v for k, v in ed.frames.items() if "2026Q" not in k}
    ut2 = TE.ustech(ed, [{"sym": "AAA", "name": "A", "sub": "x", "mcap": 1}], {"AAA": {"cik": 1}}, date(2026, 2, 20))
    r1 = dict(zip(ut2["cols"], ut2["rows"][0]))
    assert r1["q"] == "2025Q4" and r1["rev"] == (420 - 95 - 100 - 104) * 1e6, r1
    # growth-at-a-value screen (US frames + Nasdaq annual fallback; Taiwan monthly revenue + P/E)
    from wsb.analytics import growth as GR
    qs = ED.cy_quarters(TODAY, 10)
    ed.frames = {}
    base = {"1": 100.0, "2": 100.0, "3": 0.01}                     # 3 = a pre-revenue company ($ tiny)
    gr = {"1": 1.10, "2": 1.03, "3": 1.5}
    for k, per in enumerate(reversed(qs[1:])):                      # oldest → newest, skip the empty current quarter
        v = {c: base[c] * gr[c] ** k * 1e6 for c in base}
        ed.frames[f"Revenues/{per}"] = {"ts": 0, "v": v}
        ed.frames[f"GrossProfit/{per}"] = {"ts": 0, "v": {c: x * 0.6 for c, x in v.items()}}
        ed.frames[f"OperatingIncomeLoss/{per}"] = {"ts": 0, "v": {c: x * 0.1 for c, x in v.items()}}
        ed.frames[f"NetIncomeLoss/{per}"] = {"ts": 0, "v": {c: x * 0.08 for c, x in v.items()}}
    ed.frames = {k: v for k, v in ed.frames.items() if not k.endswith("Q4")}            # force the Q4 = year − Q1..Q3 path
    for y in ("CY2024", "CY2025"):
        for tag, mult in (("Revenues", 1.0), ("GrossProfit", 0.6), ("OperatingIncomeLoss", 0.1), ("NetIncomeLoss", 0.08)):
            vals = {}
            for c in base:
                o = list(reversed(qs[1:]))[0]
                idx = [(int(y[2:]) * 4 + i) - (int(o[2:6]) * 4 + int(o[-1])) for i in (1, 2, 3, 4)]
                vals[c] = sum(base[c] * gr[c] ** j * 1e6 * mult for j in idx)
            ed.frames[f"{tag}/{y}"] = {"ts": 0, "v": vals}
    ed.nqann = {"NU": {"ts": 0, "y": [{"end": "2024-12-31", "rev": 11.57e9, "gp": None, "op": 2e9, "ni": 1.9e9},
                                      {"end": "2025-12-31", "rev": 15.9e9, "gp": None, "op": 3e9, "ni": 2.8e9}]}}
    items = [{"sym": "FAST", "name": "Fast Co", "ind": "科技", "mcap": 4e9}, {"sym": "SLOW", "name": "Slow Co", "ind": "科技", "mcap": 4e9},
             {"sym": "SMR", "name": "NuScale", "ind": "工業", "mcap": 8e9}, {"sym": "NU", "name": "Nu Holdings", "ind": "金融", "mcap": 70e9}]
    ed.frames["Goodwill/" + qs[1] + "I"] = {"ts": 0, "v": {"2": 900e6}}                  # SLOW bought something big this year
    ed.frames["Goodwill/" + qs[5] + "I"] = {"ts": 0, "v": {"2": 100e6}}
    for per in qs[1:6]:                                              # a pre-revenue company: only losses, cash and cash burn
        ed.frames.setdefault(f"NetIncomeLoss/{per}", {"ts": 0, "v": {}})["v"]["4"] = -50e6
        ed.frames.setdefault(f"NetCashProvidedByUsedInOperatingActivities/{per}", {"ts": 0, "v": {}})["v"]["4"] = -150e6
    ed.frames[f"CashAndCashEquivalentsAtCarryingValue/{qs[1]}I"] = {"ts": 0, "v": {"4": 1.0e9}}
    ed.frames[f"ShortTermInvestments/{qs[1]}I"] = {"ts": 0, "v": {"4": 0.2e9}}
    rows = GR.us_rows(ed, items + [{"sym": "SLOWB", "name": "Slow Co class B", "ind": "科技", "mcap": 1e9},
                                   {"sym": "OKLO", "name": "Oklo", "ind": "公用事業", "mcap": 9e9}],
                      {"FAST": {"cik": 1}, "SLOW": {"cik": 2}, "SLOWB": {"cik": 2}, "SMR": {"cik": 3}, "OKLO": {"cik": 4}}, {"FAST": {"stl": "有買點訊號"}}, TODAY)
    assert not any(r["sym"] == "SLOWB" for r in rows), "one row per company (share classes de-duplicated)"
    assert next(r for r in rows if r["sym"] == "SLOW")["ma"] and not next(r for r in rows if r["sym"] == "FAST")["ma"]
    by = {r["sym"]: r for r in rows}
    assert abs(by["FAST"]["g"] - ((1.1 ** 4) - 1) * 100) < 0.5 and abs(by["SLOW"]["g"] - ((1.03 ** 4) - 1) * 100) < 0.5, by["FAST"]["g"]
    assert by["FAST"]["gm"] == 60.0 and abs(by["FAST"]["om"] - 10) < 1e-6 and by["FAST"]["st"] == "有買點訊號"
    assert by["NU"]["src"] == "Nasdaq 年報" and abs(by["NU"]["g"] - (15.9 / 11.57 - 1) * 100) < 0.01 and abs(by["NU"]["ps"] - 70 / 15.9) < 1e-6
    pre = next(r for r in rows if r["sym"] == "OKLO")
    assert pre["ttm"] == 0 and pre["g"] is None and abs(pre["runway"] - 2.0) < 1e-9 and pre["cash"] == 1.2e9, pre
    rows = GR.score_us(rows, 0, 15)
    by = {r["sym"]: r for r in rows}
    assert by["SMR"]["small"] and by["SMR"]["score"] is not None, "small revenue is ranked too (long-term investing)"
    assert by["OKLO"]["score"] is None, "no revenue → no growth rank, but listed (early-stage list)"
    assert by["SLOW"]["score"] is None and by["FAST"]["rank"] in (1, 2, 3) and by["NU"]["rank"] in (1, 2, 3)
    odd = GR.score_us([{"sym": "ODD", "ttm": 5e8, "g": 5000.0, "base": 9e6, "psg": 0.001, "gm": 50, "r40": 99, "mcap": 1e9}] +
                      [dict(r) for r in rows], 2e8, 15)
    o = next(r for r in odd if r["sym"] == "ODD")
    assert o["score"] is not None and o["odd"], "small-base jump: ranked, growth capped at 100% for the score"
    rd = ED.FrameReader({"Revenues/CY2026Q1": {"v": {"9": 1.0}}, "RevenueFromContractWithCustomerExcludingAssessedTax/CY2026Q1": {"v": {"9": 100.0}},
                         "RevenueFromContractWithCustomerExcludingAssessedTax/CY2025Q1": {"v": {"9": 80.0}}}, ["CY2026Q1", "CY2025Q1"])
    assert rd.val("rev", "9", "CY2026Q1") == 100.0 and rd.val("rev", "9", "CY2025Q1") == 80.0, "one tag per company, never mixed"
    us_pack = GR.pack(rows, GR.US_COLS, asof="2026-10-09", listed=4, ranked=2)
    GR.OUT_US.write_text(json.dumps(us_pack, ensure_ascii=False), encoding="utf-8")
    ed.twpe = {"ts": time.time(), "v": {**ED.parse_twpe([{"Code": "2330", "Name": "台積電", "PEratio": "25.0", "DividendYield": "1.5", "PBratio": "7.0"},
                                                        {"Code": "2454", "Name": "聯發科", "PEratio": "", "DividendYield": "3", "PBratio": "5"}], "上市"),
                                         **ED.parse_twpe([{"SecuritiesCompanyCode": "3105", "CompanyName": "穩懋", "PriceEarningRatio": "12.0",
                                                           "YieldRatio": "2", "PriceBookRatio": "1.5"}], "上櫃")}}
    assert ed.twpe["v"]["3105"]["pe"] == 12.0 and ed.twpe["v"]["2454"]["pe"] is None
    tw_r = GR.score_tw(GR.tw_rows(ed, {}, {"2330"}), 15)
    t2330 = next(r for r in tw_r if r["code"] == "2330")
    assert t2330["peg"] and abs(t2330["peg"] - 25.0 / t2330["cum_yoy"]) < 1e-9 and t2330["cur"] and t2330["streak"] == 2
    assert next(r for r in tw_r if r["code"] == "2454")["score"] is None, "no P/E → not ranked"
    # AI notes: generated once (stub LLM), cached, attached, advice lines scrubbed
    calls = []

    async def fake_complete(system, prompt, max_tokens=900):
        calls.append(prompt)
        return "這次數據偏熱，殖利率上升。\n建議買進半導體。\n接下來看 PCE。", "stub"
    import wsb.ai.llm as LLM
    LLM.complete = fake_complete
    for e in ev["events"]:                                        # make two releases "recent"
        if e["id"] in ("nfp:2026-10-02", "ism_svc:2026-10-05"):
            e["move"] = {"^NDX": -1.0, "^SOX": -2.0, "^TNX": -6.0, "DX-Y.NYB": -0.3}
    n1 = asyncio.run(EA.generate(eng))
    n2 = asyncio.run(EA.generate(eng))
    assert n1 >= 2 and n2 == 0, (n1, n2)
    assert any("非農" in c for c in calls) and any("AMD" in c or "超微" in c for c in calls), "earnings note for a recent reporter"
    EA.attach(eng)
    note = next(e for e in eng.econ_view["events"] if e["id"] == "nfp:2026-10-02")["ai"]["text"]
    assert "建議買進" not in note and "PCE" in note
    # scrub is per sentence (descriptive flows kept); an all-advice note is never cached; generate() has a deadline
    assert EA.scrub("外資買進台積電，資金回流。投資人可考慮加碼。\n下一步看 CPI！") == "外資買進台積電，資金回流。\n下一步看 CPI！"
    saved_file = EA._FILE
    EA._FILE = tmp / "econ_ai_fix.json"

    async def advice_only(system, prompt, max_tokens=900):
        return "建議買進半導體。", "stub"
    LLM.complete = advice_only
    c0 = {}
    assert asyncio.run(EA._gen("x:1", "p", c0)) is None and "x:1" not in c0 and "x:1" not in EA.load()

    async def slow(system, prompt, max_tokens=900):
        await asyncio.sleep(5)
        return "慢。", "stub"
    LLM.complete = slow
    t0 = time.time()
    assert asyncio.run(EA.generate(eng, deadline_s=0.5)) == 0 and time.time() - t0 < 3, "overall deadline"
    EA._FILE, LLM.complete = saved_file, fake_complete
    # site
    out = tmp / "site"
    asyncio.run(B.build(out, use_ai=False, engine=eng))
    page = (out / "index.html").read_text(encoding="utf-8")
    for s in ("財經日曆", "科技財報", "FOMC 聯準會利率決議", "本週重要經濟數據", "美國經濟日曆", "美股財報日曆", "科技／半導體財報分析",
              "台股電子業月營收", "美股全市場科技股", 'id="ev-cpi-2026-10-14"', "若高於預期", "過去同類數據公布當天", "class=\"qchart\"",
              "接下來的重要經濟數據", "成長股估值篩選", 'data-kind="gus"', 'data-kind="gtw"', 'data-kind="gearly"', "Nu Holdings", "現金跑道"):
        assert s in page, s
    assert "建議買進" not in page
    assert (out / "market" / "twrev.json").exists() and (out / "market" / "growth_us.json").exists() and (out / "market" / "growth_tw.json").exists()
    js = json.loads((out / "market" / "twrev.json").read_text(encoding="utf-8"))
    assert js["cols"][0] == "code" and js["n"] > 10
    Path("/tmp/wsb_econ/page.html").write_text(page, encoding="utf-8")
    test_bot(eng)
    print(f"  econ events {len(ev['events'])} · tech rows {len(te['rows'])} · page {len(page) / 1024:.0f} KB")
    print("ECON TESTS PASSED ✅")


def test_bot(eng):
    """Discord: reminder before a release, result push when the actual appears, EPS result for a curated tech name."""
    from wsb.bot import econ_push as EP
    import wsb.bot.present as P
    sent = []

    async def fake_deliver(dest, **kw):
        sent.append(kw["embeds"]())
    P.deliver = fake_deliver

    class Bot:
        engine = eng

        async def _targets(self, kind, critical=False):
            return ["dest"]
    now = datetime(TODAY.year, TODAY.month, TODAY.day, 15, 0, tzinfo=__import__("datetime").timezone.utc)   # 11:00 ET on TODAY
    iso = lambda t: t.isoformat().replace("+00:00", "Z")  # noqa: E731
    day = TODAY.isoformat()
    base = [{"name": "Core CPI", "utc": iso(now - timedelta(minutes=5)), "actual": "", "cons": "0.3%", "prev": "0.3%"},
            {"name": "Core CPI", "utc": iso(now - timedelta(minutes=5)), "actual": "", "cons": "2.5%", "prev": "2.4%"},
            {"name": "PPI", "utc": iso(now + timedelta(hours=2)), "actual": "", "cons": "0.2%", "prev": "0.4%"}]
    eng.econ.days[day] = {"ts": time.time(), "rows": base}

    async def poll(d):
        rows = [dict(r) for r in base]
        rows[0]["actual"], rows[1]["actual"] = "0.5%", "2.7%"
        eng.econ.days[d.isoformat()] = {"ts": time.time(), "rows": rows}
        return rows
    eng.econ.poll_day = poll
    eng.econ_view = ME.build(eng)
    eng.full_ready = True

    async def epoll(d):
        rows = [{"sym": "NVDA", "name": "NVIDIA", "time": "pre", "fq": "Oct/2026", "eps_f": 2.4, "n_est": 12, "eps_ly": 1.2, "mcap": 5e12,
                 "eps": 2.6, "surprise": 8.3}]
        eng.earnings.days[d.isoformat()] = {"ts": time.time(), "rows": rows}
        return rows
    eng.earnings.days[day] = {"ts": time.time(), "rows": [{"sym": "NVDA", "name": "NVIDIA", "time": "pre", "fq": "Oct/2026", "eps_f": 2.4,
                                                           "n_est": 12, "eps_ly": 1.2, "mcap": 5e12, "eps": None, "surprise": None}]}
    eng.earnings.poll_day = epoll

    async def no_surp(*a, **k):
        return eng.earnings.surprise
    ED.refresh_surprises = no_surp
    yday = (TODAY - timedelta(days=1)).isoformat()                 # a result from yesterday morning: > 1 day old → not pushed
    eng.earnings.days[yday] = {"ts": time.time(), "rows": [{"sym": "AMD", "name": "AMD", "time": "pre", "fq": "Sep/2026", "eps_f": 1.0,
                                                            "n_est": 9, "eps_ly": 0.8, "mcap": 4e11, "eps": 1.2, "surprise": 20.0}]}
    asyncio.run(EP.tick(Bot(), now=now))
    titles = [e.title for e in sent]
    assert any(t.startswith("⏰ PPI") for t in titles), titles
    i_res = next(i for i, e in enumerate(sent) if e.title.startswith("📢 CPI"))
    assert "高於預期" in sent[i_res].title and not any(n == "🧠 AI 解讀" for n, _ in sent[i_res].fields), "numbers first, no AI wait"
    ai = next(i for i, e in enumerate(sent) if e.title.startswith("🧠 CPI"))
    assert ai > i_res and "PCE" in sent[ai].description and "建議買進" not in sent[ai].description
    assert any("NVDA" in t and "2.60 vs 預期 2.40" in t for t in titles), titles
    assert not any("AMD" in t for t in titles), "a day-old result after a restart is not pushed"
    n = len(sent)
    asyncio.run(EP.tick(Bot(), now=now))
    assert len(sent) == n, "each event is pushed once"
    # a failed send is NOT remembered → retried on the next tick; a slow AI note is skipped after the timeout
    from wsb import store
    # calendar time 65 min LATER than the real release (a 1-hour clock error) → still watched and pushed once the actual appears
    base2 = [{"name": "Retail Sales", "utc": iso(now + timedelta(minutes=65)), "actual": "", "cons": "0.3%", "prev": "0.2%"}]
    eng.econ.days[day]["rows"] = list(eng.econ.days[day]["rows"]) + base2

    async def poll2(d):
        rows = [dict(r) for r in eng.econ.days[d.isoformat()]["rows"]]
        for r in rows:
            if r["name"] == "Retail Sales":
                r["actual"] = "0.9%"
        eng.econ.days[d.isoformat()] = {"ts": time.time(), "rows": rows}
        return rows
    eng.econ.poll_day = poll2
    eng.econ_view = ME.build(eng)
    fail = {"on": True}

    async def flaky_deliver(dest, **kw):
        if fail["on"]:
            raise RuntimeError("discord down")
        sent.append(kw["embeds"]())
    P.deliver = flaky_deliver
    EP.AI_TIMEOUT_S = 0.2
    import wsb.ai.llm as LLM

    async def slow_complete(system, prompt, max_tokens=900):
        await asyncio.sleep(5)
        return "太慢了。", "stub"
    LLM.complete = slow_complete
    rid = next(e["id"] for e in eng.econ_view["events"] if e["id"].startswith("retail:"))
    asyncio.run(EP.tick(Bot(), now=now))
    assert not store.kv_get(f"econ_res:{rid}"), "send failed → key not written"
    fail["on"] = False
    t0 = time.time()
    asyncio.run(EP.tick(Bot(), now=now))
    assert store.kv_get(f"econ_res:{rid}") and any(e.title.startswith("📢 零售銷售") for e in sent[n:]), [e.title for e in sent[n:]]
    assert not any(e.title.startswith("🧠 零售銷售") for e in sent[n:]) and time.time() - t0 < 4, "AI timed out → skipped"
    em = EP.econ_week_embed(eng.econ_view)
    assert em.fields and EP.tech_embed(eng.techearn["rows"][0]).fields
    print(f"  discord pushes ok ({n})")


if __name__ == "__main__":
    main()
