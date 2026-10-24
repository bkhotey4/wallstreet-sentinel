"""AI 視角 page: aftershock buckets, absorption ratio, turbulence, analogue search (past-only), cross-check and cards.
Run: python -m tests.test_ai_lens"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ai_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import physics as PH  # noqa: E402


def _walk(n, vol, rng, drift=0.0003):
    return np.exp(np.cumsum(rng.standard_t(4, n) * vol / np.sqrt(2) + drift))


def fixture(sync_end=False):
    rng = np.random.default_rng(7)
    d = pd.bdate_range("1998-01-02", "2026-10-23")
    n = len(d)
    mkt = rng.standard_t(4, n) * 0.008
    cols = {}
    for k, s in enumerate(PH.SECTORS):
        own = rng.standard_t(4, n) * 0.01
        r = mkt + own
        if sync_end:
            r[-260:] = mkt[-260:] * 1.5 + own[-260:] * 0.05          # everything moves together at the end
        cols[s] = 50 * np.exp(np.cumsum(r))
    spx = 1000 * np.exp(np.cumsum(mkt + 0.0003))
    cols["^GSPC"] = spx
    cols["^VIX"] = 18 * np.exp(np.cumsum(rng.normal(0, 0.03, n)) * 0.2)
    cols["^TNX"] = 4 + np.cumsum(rng.normal(0, 0.03, n)) * 0.1
    for k in ("GC=F", "DX-Y.NYB", "CL=F"):
        cols[k] = 100 * _walk(n, 0.01, rng, 0)
    hist = pd.DataFrame(cols, index=d)
    hist.iloc[-3:, :9] *= np.array([0.9, 0.82, 0.75])[:, None]       # a jolt in the last days
    ld = pd.bdate_range("1928-01-02", "2026-10-23")
    lr = rng.standard_t(3, len(ld)) * 0.007
    lr[[3000, 9000, 15000, 20000, len(ld) - 3]] = [-0.06, 0.05, -0.08, -0.07, -0.05]   # main shocks, the last 3 days ago
    long = pd.Series(100 * np.exp(np.cumsum(lr)), index=ld)

    class M:
        history = hist

        def series(self, t):
            return hist[t].dropna() if t in hist else pd.Series(dtype=float)

        def q(self, t):
            return None

    return types.SimpleNamespace(market=M(), long_history=types.SimpleNamespace(spx=long),
                                 stress=types.SimpleNamespace(score=62.0), crypto=None,
                                 odds={"horizons": [{"days": 63, "drawdown_pct": 10.0, "adjusted": 20.0, "base_rate": 15.0, "lift_adj": 1.3}]})


def test_aftershock():
    PH._CACHE.clear()
    a = PH.build(fixture())["aftershock"]
    assert a["available"] and a["days_since"] == 2 and a["cur"] == 0, a
    assert [r["band"] for r in a["rows"]][0] == "1–5 天" and a["rows"][-1]["band"].endswith("以上")
    assert a["fit"] and a["split"] == "1990"
    print("ok aftershock")


def test_absorption_turbulence():
    PH._CACHE.clear()
    calm, hot = PH.build(fixture())["absorption"], PH.build(fixture(sync_end=True))["absorption"]
    assert calm["available"] and hot["available"] and hot["ar"] > calm["ar"] + 10 and hot["ar_pct"] >= 90, (calm["ar"], hot["ar"])
    t = PH.build(fixture())["turbulence"]
    assert t["available"] and t["pct"] >= 80 and t["on"] and t["top_d"] >= "2026-10-21", t   # the jolt reads as turbulence
    bt = t["bt"]
    assert bt["n"] == len(bt["episodes"]) and bt["hit"] <= bt["n"] and bt["ci"][0] <= bt["ci"][1]
    print("ok absorption / turbulence")


def test_analog_past_only():
    PH._CACHE.clear()
    a = PH.build(fixture())["analog"]
    assert a["available"] and len(a["nb"]) == 20 and a["n_test"] > 100 and 0 <= a["auc"] <= 1
    last_ok = (pd.Timestamp(a["asof"]) - pd.tseries.offsets.BDay(63)).strftime("%Y-%m-%d")
    assert all(x["date"] <= last_ok for x in a["nb"]), "a neighbour whose outcome was not yet known"
    ds = sorted(pd.Timestamp(x["date"]) for x in a["nb"])
    assert all(len(pd.bdate_range(x, y)) - 1 >= 10 for x, y in zip(ds, ds[1:])), "neighbours closer than 10 days"
    print("ok analog")


def test_score():
    from tools import site_ai as SAI
    PH._CACHE.clear()
    sc = PH.build(fixture())["score"]
    assert sc["available"] and 0 <= sc["now"] <= 100 and len(sc["rows"]) == 4
    for r in sc["rows"]:
        if r["n"]:
            assert abs(r["digest"] + r["pull"] + r["crash"] - 100) < 1e-6         # three outcomes cover every day
    fake = {"available": True, "cur": 0, "base": {"crash": 14.0}, "rows": [{"band": "低", "digest": 70, "pull": 15, "crash": 15}],
            "pattern": {"now": True, "digest": 58, "pull": 20, "crash": 22, "episodes": 11, "ep_crash": 1, "n": 294}}
    v = SAI.score_view(fake)
    assert v["mixed"] and "差不多" in v["verdict"] and "9%" in v["verdict"]              # days say 22 %, episodes say 9 %
    fake["pattern"]["ep_crash"] = 5
    assert "倍" in SAI.score_view(fake)["verdict"]
    print("ok score")


def test_cards():
    from tools import site_ai as SAI
    PH._CACHE.clear()
    e = fixture()
    h = "".join(f(e) for f in (SAI.sec_ai_brief, SAI.sec_ai_score, SAI.sec_ai_cross, SAI.sec_ai_intro, SAI.sec_ai_turb, SAI.sec_ai_flock, SAI.sec_ai_quake, SAI.sec_ai_analog))
    b = SAI.sec_ai_brief(e)
    assert "一眼看懂" in b and "接下來要盯的 3 件事" in b and b.count("<li>") >= 10 and "<details" not in b
    assert all("<details" in f(e) for f in (SAI.sec_ai_turb, SAI.sec_ai_flock, SAI.sec_ai_quake, SAI.sec_ai_analog, SAI.sec_ai_cross))
    for w in ("AI 風險分數", "消化", "AI 視角交叉比對", "人類世界觀", "大森定律", "吸收比率", "Mahalanobis", "k 最近鄰", "假警報", "不是投資建議"):
        assert w in h, w
    assert "未實現" not in h and "持倉" not in h
    rows = SAI.cross_rows(e)
    assert len(rows) == 4 and rows[0]["h"][1] == SAI.TENSE                     # SSI 62
    assert SAI.agree(SAI.TENSE, SAI.CALM) == "分歧" and SAI.agree(SAI.TENSE, SAI.TENSE) == "一致"
    from tools import site_layout as SLY
    assert SLY.GROUP_OF["ai"] == "risk"
    stamped = h.replace("</h2>", "</h2><span class=upd>🕒 最後更新 10-24 13:06・ 資料日 10-23</span>", 1)
    pk = SLY.picks({"ai": stamped})
    assert pk["risk"][0].startswith("AI 判斷：") and "🕒" not in pk["risk"][0] and any("AI 視角" in x for x in pk["risk"]), pk["risk"]
    assert SLY.GROUPS[1][5][0] == "ai"
    empty = types.SimpleNamespace(market=types.SimpleNamespace(history=pd.DataFrame(), series=lambda t: pd.Series(dtype=float), q=lambda t: None))
    PH._CACHE.clear()
    assert SAI.sec_ai_cross(empty) == "" and SAI.sec_ai_quake(empty) == ""
    print("ok cards")


if __name__ == "__main__":
    test_aftershock()
    test_absorption_turbulence()
    test_analog_past_only()
    test_score()
    test_cards()
    print("all AI-lens tests passed")
