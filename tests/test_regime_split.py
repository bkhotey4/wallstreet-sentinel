"""依環境拆開驗證 + 滯脹年代對照: regime labels (no look-ahead), the walk-forward split, analogs, similarity, readings and
the site cards.  Run: python -m tests.test_regime_split"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rs_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import regime_split as RS  # noqa: E402
from wsb.analytics import shock as SH  # noqa: E402
from tools import site_regime as SRG  # noqa: E402

D = pd.bdate_range("2000-01-03", "2026-10-20")
M = pd.date_range("1999-01-01", "2026-10-01", freq="MS")


def test_labels():
    ff = pd.Series(1.0, index=M)
    ff[ff.index >= "2022-03-01"] = np.linspace(1.0, 5.0, int((ff.index >= "2022-03-01").sum()))
    rng = np.random.default_rng(2)
    r = rng.normal(0, 0.01, len(D))
    spx = pd.Series(100 * np.cumprod(1 + r), index=D)
    dy = r * 5 + rng.normal(0, 0.01, len(D))                   # yields rise with stocks → bonds hedge (opposite)
    dy[D >= "2022-01-01"] = -r[D >= "2022-01-01"] * 5         # yields fall when stocks rise → bonds up with stocks
    y10 = pd.Series(4 + np.cumsum(dy), index=D)
    lab = RS.labels(ff, spx, y10)
    assert lab.loc["2015-06-01", "fed"] == "hold" and lab.loc["2024-06-03", "fed"] == "hiking"
    assert lab.loc["2024-06-03", "sb"] == "same" and lab["sb"].loc["2005":"2010"].eq("opposite").all()
    # the March 2022 average (first month above the step after 6 months) is only used from the following month
    first_hike = lab.index[lab["fed"] == "hiking"][0]
    assert first_hike >= pd.Timestamp("2022-04-01"), first_hike
    assert RS.current(lab) == {"fed": "hiking", "sb": "same"}
    assert RS.labels(None, None, None).empty
    print("ok labels")


def test_walk_forward_split():
    rng = np.random.default_rng(4)
    px = pd.Series(100 * np.cumprod(1 + rng.normal(0.0002, 0.012, len(D))), index=D)
    ssi = pd.Series(rng.uniform(0, 100, len(D)), index=D).rolling(20, min_periods=1).mean()
    lab = pd.DataFrame({"fed": np.where(D.year % 3 == 0, "hiking", "hold"), "sb": np.where(D.year >= 2022, "same", "opposite")}, index=D)
    w = SH.walk_forward(ssi, px, 63, 0.10, regime_labels=lab)
    assert w["n_test"] > 0 and "regimes" in w
    by = {(g["dim"], g["key"]): g for g in w["regimes"]}
    assert by[("fed", "hiking")]["days"] + by[("fed", "hold")]["days"] + by[("fed", "easing")]["days"] == w["n_test"]
    assert by[("fed", "easing")]["days"] == 0 and by[("fed", "easing")]["auc"] is None   # no such days → no AUC
    assert abs(sum(g["share"] for g in w["regimes"] if g["dim"] == "sb") - 100) < 1e-6
    assert "regimes" not in SH.walk_forward(ssi, px, 63, 0.10)                            # unchanged without labels
    print("ok walk-forward split")


def test_analogs():
    mm = pd.date_range("1960-01-01", "2026-10-01", freq="MS")
    cpi = pd.Series(np.exp(np.linspace(0, 2.5, len(mm))), index=mm)
    fred = {"CPIAUCSL": cpi, "WTISPLC": pd.Series(np.linspace(3, 90, len(mm)), index=mm), "FEDFUNDS": pd.Series(np.linspace(1, 4, len(mm)), index=mm),
            "UNRATE": pd.Series(5.0, index=mm), "DGS10": pd.Series(np.linspace(4, 5, len(mm)), index=mm)}
    dd = pd.bdate_range("1960-01-04", "2026-10-20")
    spx = pd.Series(np.linspace(60, 6000, len(dd)), index=dd)
    spx[(spx.index >= "1973-01-11") & (spx.index <= "1974-10-03")] = np.linspace(120, 60, int(((spx.index >= "1973-01-11") & (spx.index <= "1974-10-03")).sum()))
    get = lambda k: fred.get(k, pd.Series(dtype=float))  # noqa: E731
    a = RS.analogs(spx, get, today=pd.Timestamp("2026-10-20"))
    e = {x["name"]: x for x in a["episodes"]}["1973–74 石油禁運"]
    assert abs(e["spx_pct"] + 50) < 0.5 and e["spx_maxdd"] < -49 and e["oil_pct"] > 0 and e["unrate_pp"] == 0.0
    assert all(x.get("similarity") is not None for x in a["episodes"])
    sims = [x["similarity"] for x in a["episodes"]]
    assert sims[-1] == max(sims), sims                                   # 2022 is closest to 2026 on a smooth trend
    assert RS.similarity({"cpi": 1.0, "oil": None}, [{"cpi": 1.0}], {"cpi": 1.0}) == [None]   # < 3 shared dimensions
    print("ok analogs")


def test_readings_and_cards():
    r = {"available": True, "now": {"fed": "hiking", "sb": "same"},
         "by_horizon": [{"days": 63, "drawdown_pct": 10.0, "regimes": [
             {"dim": "fed", "key": "hiking", "zh": "升息中", "days": 900, "events": 80, "auc": 0.51, "share": 18.0},
             {"dim": "fed", "key": "hold", "zh": "按兵不動", "days": 3000, "events": 300, "auc": 0.70, "share": 60.0},
             {"dim": "sb", "key": "same", "zh": "股債同向（公債不避險）", "days": 400, "events": 3, "auc": None, "share": 9.0}]}],
         "analogs": {"episodes": [{"name": "2022 暴力升息", "start": "2022-01-03", "end": "2022-10-12", "spx_pct": -25.0, "spx_maxdd": -27.0,
                                   "y10_bp": 230.0, "ff_pp": 3.0, "oil_pct": 15.0, "cpi_peak": 9.1, "unrate_pp": -0.4, "similarity": 71.0}],
                     "now": {"cpi": 3.4, "oil": 40.0, "ff6": 0.5, "y10": 5.28, "un12": 0.3}}}
    rd = SRG.readings(r)
    assert rd[0]["lv"] == "alert" and "0.51" in rd[0]["zh"] and any(x["lv"] == "watch" and "3 次事件" in x["zh"] for x in rd)
    h = SRG.sec_regime_split(types.SimpleNamespace(regime_split=r))
    assert "依環境拆開" in h and "◀" in h and "0.70" in h
    h2 = SRG.sec_analogs(types.SimpleNamespace(regime_split=r))
    assert "最接近「2022 暴力升息」" in h2 and "+230bp" in h2 and "9.1%" in h2, h2[:400]
    assert SRG.sec_regime_split(types.SimpleNamespace(regime_split={})) == "" and SRG.sec_analogs(types.SimpleNamespace()) == ""
    print("ok readings + cards")


if __name__ == "__main__":
    test_labels()
    test_walk_forward_split()
    test_analogs()
    test_readings_and_cards()
    print("ALL OK")
