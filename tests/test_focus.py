"""華爾街關注焦點: each item builder on synthetic data, ranking, interpretation rules depend on co-moves, site card.
Run: python -m tests.test_focus"""
from __future__ import annotations

import os
import sys
import tempfile
import types
import warnings
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_focus_"))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import focus as FC  # noqa: E402

TODAY = date(2026, 10, 19)


def _mkt(overrides):
    idx = pd.bdate_range(end="2026-10-16", periods=900)
    rng = np.random.default_rng(3)
    cols = {}
    for t in list(FC.KEY) + ["XLP", "XLU", "XLV", "XLK", "XLY", "XLF", "MTUM", "USMV"]:
        cols[t] = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 900)))
    cols["^TNX"] = 4 + np.cumsum(rng.normal(0, 0.02, 900))
    for t, f in overrides.items():
        cols[t] = f(cols[t])
    h = pd.DataFrame(cols, index=idx)
    return types.SimpleNamespace(series=lambda t: h[t].rename(t) if t in h else pd.Series(dtype=float))


def test_fed():
    fv = {"meetings": [{"date": "2026-10-28", "probs": {"0": 0.82, "25": 0.18}, "cum_bp": 4},
                       {"date": "2026-12-09", "probs": {"0": 0.18, "25": 0.82}, "cum_bp": 25},
                       {"date": "2027-01-27", "probs": {"0": 0.64, "25": 0.36}, "cum_bp": 34}]}
    eng = types.SimpleNamespace(econ_view={"next_fomc": {"date": "2026-10-28", "tpe": "10/29 02:00"}}, fedwatch_view=fv)
    it = FC.fed(eng, TODAY)
    assert "維持不變 82%" in it["data"][0] and any("2026-12-09" in h for h in it["hidden"]), it
    assert any("升息循環" in h for h in it["hidden"]) and it["score"] > 60


def test_moves_meaning_depends_on_comoves():
    def crash(x):
        y = x.copy()
        y[-5:] = y[-6] * np.linspace(0.97, 0.85, 5)
        return y

    def up_rates(x):
        y = x.copy()
        y[-5:] = y[-6] + np.linspace(0.1, 0.5, 5)
        return y
    eng = types.SimpleNamespace(market=_mkt({"^SOX": crash, "^TNX": up_rates}))
    its = {i["key"]: i for i in FC.moves(eng)}
    assert "move:^SOX" in its and "估值" in its["move:^SOX"]["hidden"][0], its.keys()
    eng2 = types.SimpleNamespace(market=_mkt({"^SOX": crash, "^TNX": lambda x: x - np.r_[np.zeros(895), np.linspace(0.1, 0.5, 5)]}))
    its2 = {i["key"]: i for i in FC.moves(eng2)}
    assert "成長" in its2["move:^SOX"]["hidden"][0]                           # same semis fall, falling yields → growth scare


def test_credit_and_rank():
    idx = pd.bdate_range(end="2026-10-16", periods=60)
    ccc = pd.Series(np.r_[np.full(38, 9.0), np.linspace(9.0, 12.0, 22)], index=idx)
    bb = pd.Series(np.full(60, 2.0), index=idx)
    fr = types.SimpleNamespace(get=lambda sid: {"BAMLH0A3HYC": ccc, "BAMLH0A1HYBB": bb, "BAMLH0A0HYM2": bb + 1}.get(sid))
    it = FC.credit(types.SimpleNamespace(fred=fr))
    assert it and "尚未擴散" in it["hidden"][0]
    bb2 = pd.Series(np.r_[np.full(38, 2.0), np.linspace(2.0, 3.0, 22)], index=idx)
    fr2 = types.SimpleNamespace(get=lambda sid: {"BAMLH0A3HYC": ccc, "BAMLH0A1HYBB": bb2}.get(sid))
    it2 = FC.credit(types.SimpleNamespace(fred=fr2))
    assert "擴散" in it2["hidden"][0] and it2["score"] > it["score"]


def test_build_and_card():
    eng = types.SimpleNamespace(market=_mkt({}), econ_view={}, fedwatch_view={}, earnings=None, fred=None,
                                canary={"rows": [{"state": "alert", "zh": "CCC − BB 利差", "why": "最弱的公司先出事"}]},
                                stress=types.SimpleNamespace(score=63.0, chg_20d=19.5), odds={"horizons": [{"days": 63, "adjusted": 20.7, "base_rate": 15.0}]})
    out = FC.build(eng)
    assert out["available"] and [i["score"] for i in out["items"]] == sorted((i["score"] for i in out["items"]), reverse=True)
    assert {i["key"] for i in out["items"]} >= {"canary", "stress"}
    from tools import site_sections as S2
    html = S2.sec_focus(types.SimpleNamespace(focus=out))
    assert "華爾街關注焦點" in html and "隱藏涵意" in html and "不用新聞標題" in html
    assert S2.sec_focus(types.SimpleNamespace(focus={})) == ""


def main():
    test_fed()
    test_moves_meaning_depends_on_comoves()
    test_credit_and_rank()
    test_build_and_card()
    print("FOCUS TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
