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
    out = EV.build(eng, now=pd.Timestamp("2026-10-15").date())
    rows = {r["sym"]: r for r in out["rows"]}
    t = rows["TSM"]
    assert t["result"] == "beat" and abs(t["surp"] - 3.4) < 0.05 and t["mv"] == 5.5 and t["tw"]["sym"] == "2330.TW"
    assert t["tw"]["move"] is not None and [n["t"] for n in t["news"]] == ["TSMC beats"]
    assert t["peers"]["theme"] if "peers" in t else True
    assert rows["NVDA"]["status"] == "pending" and "今天公布" in rows["NVDA"]["verdict"]["zh"]
    snap = EV._load_implied()
    assert snap["TSM|2026-10-15"]["mv"] == 5.5 and snap["NFLX|2026-10-15"]["mv"] == 8.0   # saved for afterwards
    assert "SCHW|2026-10-15" not in snap                       # a quote taken after a pre-market report is not "beforehand"
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
    fb = SE._fw_block(eng, None, 4.0)
    assert "70%" in fb and "30%" in fb and "升息 1 碼" in fb and "偏鷹" in fb and "符合預期" in fb and "-1.10%" in fb
    assert "CME FedWatch" in fb


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


def main():
    test_discord()
    test_fedwatch()
    test_macro()
    eng, out = test_earnings()
    test_site(eng, out)
    print("CONCLUSIONS TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
