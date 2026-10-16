"""財經日曆結論: FedWatch arithmetic, macro follow-through + conclusion, earnings verdicts, site rendering.
Run: python -m tests.test_conclusions"""
from __future__ import annotations

import os
import sys
import tempfile
import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_concl_"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import earn_verdict as EV  # noqa: E402
from wsb.analytics import macro_events as ME  # noqa: E402
from wsb.data import fedwatch as FW  # noqa: E402


def test_fedwatch():
    # real quotes of 2026-10-15: EFFR 3.88, Oct 96.115, Nov 96.045 …  → Oct 28 meeting ≈ 30% hike
    fut = {(2026, 10): 96.115, (2026, 11): 96.045, (2026, 12): 95.89, (2027, 1): 95.815}
    rows = FW.implied(["2026-10-28", "2026-12-09", "2027-01-27", "2027-03-17"], fut, 3.88)
    assert rows[0]["probs"] == {"0": 0.7, "25": 0.3}, rows[0]
    assert abs(rows[0]["rate_after"] - 3.955) < 1e-9                       # late-month → November contract
    assert rows[1]["probs"]["25"] > 0.8 and abs(rows[1]["cum_bp"] - 29.3) < 0.2
    assert len(rows) == 3, "no March contract → stop, never extrapolate"
    # a cut, mid-month meeting from the meeting-month contract itself: 15 days at 4.33, 15 at 4.08 → avg 4.205
    cut = FW.implied(["2025-09-15"], {(2025, 9): 100 - (15 * 4.33 + 15 * 4.08) / 30}, 4.33)
    assert cut[0]["probs"] == {"-25": 1.0}, cut
    half = FW.implied(["2025-09-15"], {(2025, 9): 100 - (15 * 4.33 + 15 * 4.205) / 30}, 4.33)
    assert half[0]["probs"] == {"-25": 0.5, "0": 0.5}, half
    assert FW.outcome_label(-50)[0].startswith("降息 2 碼") and FW.outcome_label(0)[0] == "維持不變"
    assert FW.ticker(2026, 11) == "ZQX26.CBT" and FW.ticker(2027, 1) == "ZQF27.CBT"
    # snapshots: what was priced before a meeting
    fw = FW.FedWatch()
    fw.quotes = {"ZQX26.CBT": [96.0, "2026-10-20"]}
    fw.record([{"date": "2026-10-28", "probs": {"0": 0.7, "25": 0.3}, "rate_after": 3.95, "chg_bp": 7.5}])
    eng = types.SimpleNamespace(fedwatch=fw)
    assert FW.priced_before(eng, "2026-10-28")["probs"]["25"] == 0.3 and FW.priced_before(eng, "2026-12-09") is None


def test_macro():
    idx = pd.bdate_range("2026-01-01", periods=80)
    ndx = pd.Series(np.linspace(100, 179, 80), index=idx)
    tnx = pd.Series(4.0, index=idx)
    tw = pd.Series(np.linspace(200, 279, 80), index=idx)
    hist = pd.DataFrame({"^NDX": ndx, "^TNX": tnx, "^TWII": tw})
    day = idx[10].strftime("%Y-%m-%d")
    f5 = ME.forward(hist, day, 5)
    assert abs(f5["^NDX"] - (ndx.iloc[15] / ndx.iloc[10] - 1) * 100) < 1e-9 and f5["^TNX"] == 0
    assert ME.forward(hist, idx[-3].strftime("%Y-%m-%d"), 5)["^NDX"] is None        # not enough future → None
    assert abs(ME.tw_next(hist, day) - (tw.iloc[11] / tw.iloc[10] - 1) * 100) < 1e-9
    past = [{"id": f"cpi:{d:%F}", "key": "cpi", "date": d.strftime("%Y-%m-%d"), "dir": "hot", "rows": [{}]} for d in idx[5:40:7]]
    st = ME.history_stats(past, hist)["cpi"]["by"]["hot"]
    assert st["fwd"]["n20"] == 5 and st["fwd"]["f20"]["^NDX"] > 0 and st["fwd"]["tw"] > 0
    e = {"key": "cpi", "dir": "hot", "move": {"^NDX": -1.2, "^TNX": 8.0}, "tw_next": -0.8, "stats": {"by": {"hot": st}}}
    c = ME.conclusion(e)["zh"]
    assert "高於預期" in c and "-1.20%" in c and "台股隔日 -0.80%" in c and "20 個交易日平均" in c and "樣本少" in c
    assert ME.conclusion({"key": "cpi", "dir": None}) is None
    c2 = ME.conclusion({"key": "fomc", "dir": "inline", "move": {}, "stats": None})["zh"]
    assert "符合預期" in c2 and "等美股收盤" in c2


def test_earnings():
    base = {"eps": 1.1, "eps_f": 1.0, "surp": 10.0, "result": "beat"}
    v = EV.verdict({**base, "react": -5.0, "mv": 4.0})["zh"]
    assert "優於預期但股價下跌" in v and "1.2 倍" in v and "指引" in v
    assert "市場買單" in EV.verdict({**base, "react": 3.0})["zh"]
    assert "等公布後第一個完整交易日" in EV.verdict({**base, "react": None})["zh"]
    assert "利空出盡" in EV.verdict({"eps": 0.9, "eps_f": 1.0, "surp": -10.0, "result": "miss", "react": 4.0})["zh"]
    assert EV.result_of(1.5) == "inline" and EV.result_of(2.5) == "beat" and EV.result_of(-3) == "miss" and EV.result_of(None) is None
    idx = pd.bdate_range("2026-06-01", "2026-10-30")
    px = pd.Series(np.arange(len(idx), dtype=float) + 100, index=idx)
    assert EV.next_session(px, "2026-10-15") == (px.loc["2026-10-16"] / px.loc["2026-10-15"] - 1) * 100
    assert EV.drift(px, "2026-07-16", 20) == (px[px.index > "2026-07-16"].iloc[20] / px[px.index > "2026-07-16"].iloc[0] - 1) * 100
    assert EV.drift(px, "2026-10-20", 20) is None
    # full build with a fake engine: TSM reported (pending today) + NVDA peer; Taiwan ADR mapping; headlines filtered by date
    series = {"TSM": px * 1.0, "NVDA": px * 2.0, "2330.TW": px * 10.0}
    eng = types.SimpleNamespace(
        techearn={"calendar": {"past": [{"sym": "TSM", "name": "台積電 ADR", "date": "2026-10-15", "time": "pre", "cur": True,
                                         "eps": 4.6, "eps_f": 4.45, "surp": None}],
                               "up": [{"sym": "NVDA", "name": "輝達", "date": "2026-10-15", "time": "after", "cur": True, "eps_f": 1.0}]}},
        stockprices=types.SimpleNamespace(series=lambda s: series.get(s, pd.Series(dtype=float))),
        market=types.SimpleNamespace(series=lambda s: pd.Series(dtype=float)),
        earnings=types.SimpleNamespace(surprise={"TSM": {"rows": [{"date": "2026-07-16"}, {"date": "2026-04-16"}]}}),
        stocknews=types.SimpleNamespace(items={"TSM": [{"t": "TSMC beats", "l": "https://x.test/a", "ts": pd.Timestamp("2026-10-15").timestamp(), "src": "R"},
                                                       {"t": "old", "l": "https://x.test/b", "ts": pd.Timestamp("2026-09-01").timestamp()}]}),
        sx={"earn": [{"sym": "TSM", "date": "2026-10-15", "time": "pre", "mv": 5.5, "asof": "2026-10-14 20:10 UTC"},
                     {"sym": "SCHW", "date": "2026-10-15", "time": "pre", "mv": 3.8, "asof": "2026-10-15 11:56 UTC"},   # after the report
                     {"sym": "NFLX", "date": "2026-10-15", "time": "after", "mv": 8.0, "asof": "2026-10-15 15:00 UTC"}]})
    from wsb.data import earn_release as R
    R.save({"NVDA|2026-10-15": {**R.build_record("NVDA", "2026-10-15", {"acc": "n1", "form": "8-K", "date": "2026-10-15", "url": "https://www.sec.gov/x/",
                                                                         "docs": [], "text": NVDA}, None)}})
    import wsb.analytics.sessions as SS
    _real = SS.completed
    SS.completed = lambda px, sym="", now=None: px          # fixture dates run past "today": treat every bar as closed
    try:
        out = EV.build(eng, now=pd.Timestamp("2026-10-15").date())
    finally:
        SS.completed = _real
    rows = {r["sym"]: r for r in out["rows"]}
    t = rows["TSM"]
    assert t["result"] == "beat" and abs(t["surp"] - 3.4) < 0.05 and t["mv"] == 5.5 and t["tw"]["sym"] == "2330.TW"
    assert t["tw"]["move"] is not None and [n["t"] for n in t["news"]] == ["TSMC beats"]
    assert t["peers"]["theme"] if "peers" in t else True
    nv = rows["NVDA"]                                   # the 8-K is out before Nasdaq's EPS field → a verdict from the filing
    assert nv["status"] == "reported" and any("下季指引" in x for x in nv["release"]["lines"])
    assert "今天公布" not in nv["verdict"]["zh"] and nv["release"]["acc"] == "n1"
    snap = EV._load_implied()
    assert snap["TSM|2026-10-15"]["mv"] == 5.5 and snap["NFLX|2026-10-15"]["mv"] == 8.0   # saved for afterwards
    assert "SCHW|2026-10-15" not in snap                       # a quote taken after a pre-market report is not "beforehand"
    import json as _json
    EV.IMPLIED.write_text(_json.dumps({**snap, "AMD|2026-10-15": {"mv": 6.0, "asof": "2026-10-15 11:56 UTC"}}), encoding="utf-8")
    eng.sx = {"earn": []}
    assert "AMD|2026-10-15" not in EV.remember_implied(eng)     # a same-day snapshot from before this rule is purged
    return eng, out


def test_site(eng, out):
    from tools import site_econ as SE
    eng.earn_verdict = out
    eng.earn_verdict["rows"][0]["news"].append({"t": "<script>x</script>", "l": "javascript:alert(1)", "src": "", "ts": 0})
    html = SE.sec_earn_verdict(eng)
    assert "財報結論" in html and "台積電" in html and "<script>x" not in html and "javascript:" not in html
    assert "未列入結論" in html
    eng.fedwatch_view = {"available": True, "asof": "2026-10-15", "r0": 3.88, "r0_date": "2026-10-13", "contracts": 6,
                         "meetings": FW.implied(["2026-10-28", "2026-12-09"], {(2026, 10): 96.115, (2026, 11): 96.045, (2026, 12): 95.89, (2027, 1): 95.815}, 3.88)}
    eng.econ_view = {"stats": {"fomc": {"by": {"inline": {"n": 4, "^NDX": 0.3, "^TNX": -2.0, "fwd": {"f20": {"^NDX": 1.5}}},
                                               "hot": {"n": 2, "^NDX": -1.1, "^TNX": 6.0, "fwd": {"f20": {"^NDX": -2.0}}}}}}}
    cut = {"available": True, "asof": "2026-10-15", "r0": 3.88, "r0_date": "2026-10-13", "contracts": 6,
           "meetings": [{"date": "2026-10-28", "rate_after": 3.70, "chg_bp": -18, "cum_bp": -18, "probs": {"-25": 0.7, "0": 0.3}}]}
    keep = eng.fedwatch_view
    eng.fedwatch_view = cut
    fc = SE._fw_block(eng, 3.75, 4.0)                                       # consensus: cut to 3.75 → −25 is "in line"
    row = fc[fc.index("降息 1 碼"):fc.index("降息 1 碼") + 400]
    assert "符合預期" in row and "偏鷹" in fc[fc.index("維持不變"):fc.index("維持不變") + 400]
    eng.fedwatch_view = keep
    fb = SE._fw_block(eng, None, 4.0)
    assert "70%" in fb and "30%" in fb and "升息 1 碼" in fb and "偏鷹" in fb and "符合預期" in fb and "-1.10%" in fb
    assert "CME FedWatch" in fb
    # 各公司最新財報重點 + a verdict that only has the company's filing so far (Nasdaq EPS not updated yet)
    eng.latest_reports = {"available": True, "rows": [
        {"sym": "TSM", "name": "台積電 ADR", "theme": "半導體", "date": "2026-10-15", "acc": "a1", "form": "6-K",
         "url": "https://www.sec.gov/Archives/edgar/data/1046179/x/", "lines": ["本季：營收 US$46.72B", "下季指引：營收 US$52.30B–54.30B"],
         "react": None, "tw": {"sym": "2330.TW", "name": "台積電", "move": -1.2}, "ai": {"text": "重點<b>", "engine": "t"}},
        {"sym": "X", "name": "Evil", "theme": "", "date": "2026-10-14", "acc": "a2", "form": "8-K", "url": "javascript:alert(1)", "lines": [], "react": 1.0, "tw": None}]}
    lr = SE.sec_latest_reports(eng)
    assert "各公司最新財報重點" in lr and "US$52.30B" in lr and "台股隔日" in lr and "重點&lt;b&gt;" in lr
    assert "javascript:" not in lr and "https://www.sec.gov/Archives/edgar/data/1046179/x/" in lr


def test_logic_fixes():
    from datetime import datetime, timezone
    from wsb.analytics.sessions import completed
    idx = pd.to_datetime(["2026-10-14", "2026-10-15", "2026-10-16"])
    px = pd.Series([1.0, 2.0, 3.0], index=idx)
    open_ = datetime(2026, 10, 16, 15, 0, tzinfo=timezone.utc)            # 11:00 ET → session running
    closed = datetime(2026, 10, 16, 21, 0, tzinfo=timezone.utc)           # 17:00 ET
    assert len(completed(px, "NVDA", open_)) == 2 and len(completed(px, "NVDA", closed)) == 3
    assert len(completed(px, "2330.TW", datetime(2026, 10, 16, 3, 0, tzinfo=timezone.utc))) == 2    # 11:00 Taipei
    assert len(completed(px, "2330.TW", datetime(2026, 10, 16, 7, 0, tzinfo=timezone.utc))) == 3    # 15:00 Taipei
    from wsb.data import earn_release as R
    assert R.fmt_range({"metric": "revenue_growth", "single": True, "lo": -5, "hi": -5, "mid": -5.0, "unit": "%"}) == "約 -5.0%"
    # FedWatch: EFFR still shows the pre-decision rate → r0 follows the target change
    fw = FW.FedWatch()
    fw.quotes = {"ZQX26.CBT": [96.37, "2026-10-29"], "ZQZ26.CBT": [96.37, "2026-10-29"], "ZQF27.CBT": [96.37, "2026-10-29"]}
    ser = {"EFFR": pd.Series([3.88], index=pd.to_datetime(["2026-10-28"])),
           "DFEDTARU": pd.Series([4.00, 3.75], index=pd.to_datetime(["2026-10-28", "2026-10-29"])),
           "DFEDTARL": pd.Series([3.75, 3.50], index=pd.to_datetime(["2026-10-28", "2026-10-29"]))}
    fred = types.SimpleNamespace(series=ser, get=lambda sid: ser.get(sid))
    ec = types.SimpleNamespace(fomc=[{"date": "2026-12-09", "sep": True}])
    v = FW.view(types.SimpleNamespace(fedwatch=fw, fred=fred, econ=ec))
    assert abs(v["r0"] - 3.63) < 1e-9 and v["meetings"][0]["probs"] == {"0": 1.0}, v      # no fake cut at the next meeting


def test_discord():
    from wsb.bot import econ_push as EP
    m = {"probs": {"0": 0.7, "25": 0.3}, "rate_after": 3.955}
    assert EP._fw_txt(m) == "維持不變 70%、升息 1 碼（25bp） 30%（會後隱含利率 3.96%）" and EP._fw_txt(None) == ""
    e = {"stats": {"by": {"hot": {"fwd": {"f5": {"^NDX": 0.6}, "f20": {"^NDX": -2.7}, "tw": -0.5, "n20": 3}}}}}
    assert "20 個交易日平均 -2.7%" in EP._fwd_txt(e, "hot") and EP._fwd_txt(e, "cool") == ""
    r = {"sym": "TSM", "name": "台積電 ADR", "result": "beat", "react": 3.2, "verdict": {"zh": "測試結論。"},
         "peers": {"theme": "半導體", "top": [("NVDA", "輝達", 2.1)]}}
    em = EP.verdict_embed(r)
    assert "優於預期" in em.title and "+3.2%" in em.title and em.description == "測試結論。"


TSMC = ("In US dollars, third quarter revenue was $46.72 billion, which increased 41.2% year-over-year. Gross margin for the quarter was 66.4%, "
        "operating margin was 58.7%, and net profit margin was 51.1%. Based on the Company's current business outlook, management expects the "
        "overall performance for fourth quarter 2026 to be as follows: • Revenue is expected to be between US$52.3 billion and US$54.3 billion; "
        "And, based on the exchange rate assumption of 1 US dollar to 31.8 NT dollars, • Gross profit margin is expected to be between 65% and 67%; "
        "• Operating profit margin is expected to be between 56.5% and 58.5%. Cash Flows (In NT$ billions) 3Q26 2Q26 3Q25 Cash from operating "
        "activities 919.77 783.36 426.83 Capital expenditures (443.21) (496.00) (287.45) Future Outlook Based on our current business outlook, "
        "management expects: ▪ 2026 revenue to increase by around 44% in US dollar terms Unleash Innovation")
NVDA = ("Outlook NVIDIA's outlook for the third quarter of fiscal 2027 is as follows: • Revenue is expected to be $108.0 billion, plus or minus 2%. "
        "• GAAP and non-GAAP gross margins are expected to be 74.0%, plus or minus 50 basis points. • GAAP and non-GAAP operating expenses are "
        "expected to be approximately $9.2 billion and $9.0 billion, respectively. Revenue $96,221 $81,615 Capital expenditures 7 1 - - 8")
ASML = ("ASML reports €11.7 billion total net sales and €5.0 billion net income in Q3 2026 Full-year 2026 total net sales expected to be between "
        "€44 billion and €45 billion, with a gross margin around 56% VELDHOVEN • Q3 total net sales of €11.7 billion, gross margin of 57.5%, net "
        "income of €5.0 billion • ASML expects Q4 2026 total net sales between €14.2 billion and €15.2 billion, and a gross margin around 57%")


def test_release_parser():
    from wsb.data import earn_release as R
    p = R.parse(TSMC)
    a, g = p["actual"], {(x["metric"], x["period"]): x for x in p["guide"]}
    assert a["revenue"]["USD"]["v"] == 46.72 and a["gross_margin"]["v"] == 66.4 and a["op_margin"]["v"] == 58.7
    assert a["capex"]["v"] == 443.21 and a["capex"]["cur"] == "TWD"
    assert (g[("revenue", "next_q")]["lo"], g[("revenue", "next_q")]["hi"], g[("revenue", "next_q")]["cur"]) == (52.3, 54.3, "USD")
    assert (g[("gross_margin", "next_q")]["lo"], g[("gross_margin", "next_q")]["hi"]) == (65.0, 67.0)
    assert (g[("op_margin", "next_q")]["lo"], g[("op_margin", "next_q")]["hi"]) == (56.5, 58.5)
    assert g[("revenue_growth", "year")]["mid"] == 44.0 and g[("revenue_growth", "year")]["unit"] == "%"     # bullet after "expects:"
    ov = {x["metric"]: x for x in R.outlook_vs_now(a, p["guide"])}
    assert abs(ov["revenue"]["chg"] - 14.08) < 0.01 and abs(ov["gross_margin"]["chg"] + 0.4) < 1e-9
    n = R.parse(NVDA)
    gn = {(x["metric"], x["period"]): x for x in n["guide"]}
    assert abs(gn[("revenue", "next_q")]["lo"] - 105.84) < 1e-6 and abs(gn[("revenue", "next_q")]["hi"] - 110.16) < 1e-6
    assert (gn[("gross_margin", "next_q")]["lo"], gn[("gross_margin", "next_q")]["hi"]) == (73.5, 74.5)
    assert gn[("opex", "next_q")]["single"] and gn[("opex", "next_q")]["lo"] == 9.2         # "X and Y, respectively" ≠ a range
    assert "capex" not in n["actual"]                                  # an unrelated "Capital expenditures 7 1" row is not capex
    s = R.parse(ASML)
    gs = {(x["metric"], x["period"]): x for x in s["guide"]}
    assert (gs[("revenue", "year")]["lo"], gs[("revenue", "year")]["hi"]) == (44.0, 45.0)      # not the €11.7B / €5.0B headline
    assert (gs[("revenue", "next_q")]["lo"], gs[("revenue", "next_q")]["hi"]) == (14.2, 15.2)  # "Q4 2026 total net sales" is a quarter
    assert gs[("gross_margin", "next_q")]["mid"] == 57.0 and gs[("gross_margin", "year")]["mid"] == 56.0
    assert s["actual"]["revenue"]["EUR"]["v"] == 11.7 and s["actual"]["gross_margin"]["v"] == 57.5
    # compare with last time's guidance: range position, point tolerance, GAAP/non-GAAP basis, wrong-period guard
    prev = R.guidance("• Revenue is expected to be between US$44.6 billion and US$45.8 billion; • Gross profit margin is expected to be between 65% and 67%")
    cmp_ = {x["metric"]: x for x in R.compare(a, prev)}
    assert cmp_["revenue"]["pos"] == "above" and cmp_["gross_margin"]["pos"] == "within"
    amd_act = R.actuals("Gross margin was 54%, operating income was $1.2 billion. Non-GAAP gross margin was 56%. Revenue was $11.5 billion.")
    amd_prev = R.guidance("For the second quarter of 2026, AMD expects revenue to be approximately $11.2 billion. Non-GAAP gross margin is expected to be approximately 56%.")
    c2 = {x["metric"]: x for x in R.compare(amd_act, amd_prev)}
    assert c2["gross_margin"]["basis"] == "ng" and c2["gross_margin"]["actual"] == 56.0 and c2["gross_margin"]["pos"] == "within"
    assert c2["revenue"]["pos"] == "above"
    pm = {x["metric"]: x for x in R.guidance("For the third quarter of 2026, AMD expects revenue to be approximately $13 billion, plus or minus $300 million.")}
    assert (round(pm["revenue"]["lo"], 2), round(pm["revenue"]["hi"], 2)) == (12.7, 13.3) and not pm["revenue"]["single"]
    assert R.compare(s["actual"], [{"metric": "revenue", "period": "next_q", "lo": 43, "hi": 45, "mid": 44, "unit": "B", "cur": "EUR"}]) == []
    # sanity: a segment revenue far from the XBRL reference is dropped; an annual figure is not next quarter
    act, gd = R.sanitize({"revenue": {"USD": {"v": 27.5}}}, [{"metric": "revenue", "period": "next_q", "lo": 197, "hi": 202, "mid": 199.5,
                                                             "unit": "B", "cur": "USD"}], 200.6, "8-K")
    assert "revenue" not in act and gd[0]["period"] == "next_q"
    _a2, gd2 = R.sanitize({"revenue": {"USD": {"v": 1.58}}}, [{"metric": "revenue", "period": "next_q", "lo": 6.0, "hi": 6.1, "mid": 6.05,
                                                              "unit": "B", "cur": "USD"}], 1.47, "8-K")
    assert gd2[0]["period"] == "year"
    assert R.sanitize({"revenue": {"USD": {"v": 7.75}}}, [], None, "8-K")[0] == {}       # no reference → an 8-K revenue is not shown
    # rounding: "$3.3 billion" vs guidance $3.345–3.355B is not "below guidance"
    rnd = R.actuals("Revenue was $3.3 billion, up 15%.")
    c3 = R.compare(rnd, [{"metric": "revenue", "period": "next_q", "lo": 3.345, "hi": 3.355, "mid": 3.35, "unit": "B", "cur": "USD"}])
    assert c3[0]["pos"] == "within", c3
    # an outlook bullet is never this quarter's actual (Palo Alto style: "Total revenue in the range of …")
    pa = R.actuals("Fiscal first quarter 2027 guidance: • Total revenue in the range of $3.300 billion to $3.310 billion. "
                   "• Non-GAAP operating margin in the range of 29.5% to 29.8%.")
    assert "revenue" not in pa and "op_margin" not in pa and "op_margin_ng" not in pa, pa
    panw = ("Fourth quarter revenue grew 16% to $2.6 billion. For the fiscal first quarter 2027, we expect: • Total revenue in the range of "
            "$3.300 billion to $3.310 billion, representing growth of 33% to 34%. • Diluted non-GAAP net income per share in the range of $1.0. "
            "For the fiscal year 2027, we expect: • Total revenue in the range of $14.10 billion to $14.20 billion, representing growth of 23%. "
            "• Non-GAAP operating margin of 29.5%. • Diluted non-GAAP net income per share in the range of $4.0.")
    pg = {(x["metric"], x["period"]): x for x in R.guidance(panw)}
    assert pg[("revenue", "next_q")]["lo"] == 3.3 and pg[("revenue", "year")]["lo"] == 14.1 and pg[("op_margin", "year")]["mid"] == 29.5, pg.keys()
    assert ("op_margin", "next_q") not in pg
    pact = R.actuals(panw)
    assert "op_margin_ng" not in pact and "op_margin" not in pact, pact            # the FY guidance bullet is not an actual
    # quarterly opex guidance stays next quarter; capex guidance is annual unless a quarter is named
    gm = {(x["metric"], x["period"]) for x in R.guidance("For the third quarter, we expect non-GAAP operating expenses of approximately $1.01 billion. "
                                                          "We expect 2026 capital expenditures to be in the range of $130 billion to $145 billion.")}
    assert ("opex", "next_q") in gm and ("capex", "year") in gm, gm
    lines = R.summary_lines({**R.parse(TSMC), "vs_prev_guide": R.compare(a, prev), "outlook_vs_now": R.outlook_vs_now(a, p["guide"])})
    j = "\n".join(lines)
    assert "營收 US$46.72B" in j and "高於指引上緣" in j and "下季指引" in j and "+14.1%" in j and "NT$443.21B" in j and "+44.0%" in j


def main():
    test_release_parser()
    test_discord()
    test_fedwatch()
    test_macro()
    eng, out = test_earnings()
    test_site(eng, out)
    test_logic_fixes()                       # last: it records FedWatch snapshots in the shared cache
    print("CONCLUSIONS TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
