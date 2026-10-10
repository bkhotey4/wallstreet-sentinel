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
    now = datetime.now(__import__("datetime").timezone.utc)
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
    asyncio.run(EP.tick(Bot()))
    titles = [e.title for e in sent]
    assert any(t.startswith("⏰ PPI") for t in titles), titles
    res = next(e for e in sent if e.title.startswith("📢 CPI"))
    assert "高於預期" in res.title and any(n == "🧠 AI 解讀" for n, _ in res.fields), res.fields
    assert any("NVDA" in t and "2.60 vs 預期 2.40" in t for t in titles), titles
    n = len(sent)
    asyncio.run(EP.tick(Bot()))
    assert len(sent) == n, "each event is pushed once"
    em = EP.econ_week_embed(eng.econ_view)
    assert em.fields and EP.tech_embed(eng.techearn["rows"][0]).fields
    print(f"  discord pushes ok ({n})")


if __name__ == "__main__":
    main()
