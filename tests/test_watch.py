"""Tests for the self-monitoring / risk-forecast modules.  Run: python -m tests.test_watch"""
from __future__ import annotations

import time
from datetime import date

import tests.test_offline as T  # noqa: F401  (installs synthetic market/FRED stubs)
from wsb.analytics import watch as W
from wsb.analytics.stress import StressEngine
from wsb.health import HEALTH


# fictional tickers and amounts (never real positions); themes are injected by the test itself
TEST_THEMES = {"主題甲": {"max_weight_pct": 45, "tickers": ["AAA", "BBB", "CCC"]},
               "主題乙": {"max_weight_pct": 60, "tickers": ["AAA", "BBB", "CCC", "DDD", "EEE"]}}


def fake_portfolio():
    pos = [("AAA", 8000, 200.0, 1.9, 34.0), ("BBB", 5000, 450.0, 1.6, 18.0), ("CCC", 3000, 230.0, 1.8, 12.0),
           ("DDD", 4000, 140.0, 1.6, 14.0), ("EEE", 2500, 340.0, 1.1, 5.0), ("FFF", 1500, 8.0, 3.0, 11.0),
           ("GGG", 500, 37.0, 3.0, 3.0), ("HHH", 3000, 55.0, 0.0, 3.0)]
    V = sum(p[1] for p in pos)
    return {"total_value_usd": float(V), "beta": 1.61,
            "positions": [{"sym": s, "value_usd": float(v), "price": px, "beta": b, "weight": v / V * 100,
                           "risk_contrib_pct": r} for s, v, px, b, r in pos]}


def main():
    # ---------------------------------------------------------------- concentration
    from wsb.config import SETTINGS
    SETTINGS.raw.setdefault("concentration", {})["themes"] = TEST_THEMES
    pf = fake_portfolio()
    c = W.concentration(pf)
    kinds = {(b["kind"], b["name"]) for b in c["breaches"]}
    assert ("single", "AAA") in kinds, c["breaches"]                  # 29% weight and 34% risk
    assert ("theme", "主題甲") in kinds and ("theme", "主題乙") in kinds, kinds
    assert ("beta", "β") in kinds
    assert ("single", "BBB") not in kinds
    th = c["themes"]["主題甲"]
    assert abs(th["weight"] - (8000 + 5000 + 3000) / pf["total_value_usd"] * 100) < 1e-6
    # the suggested trim really brings the weight down to the limit
    V = pf["total_value_usd"]
    x = (8000 - 0.25 * V) / 0.75
    assert abs((8000 - x) / (V - x) - 0.25) < 1e-9
    al = W.concentration_alerts(pf, date(2026, 10, 2))
    assert len(al) == 1 and al[0][0] == "conc:2026W40" and "AAA" in al[0][3], al
    assert W.concentration_alerts(pf, date(2026, 10, 9))[0][0] == "conc:2026W41"    # new week → new key
    ok = dict(pf)
    ok["positions"] = [dict(p, weight=10.0, risk_contrib_pct=10.0, value_usd=p["value_usd"]) for p in pf["positions"]]
    ok["beta"] = 1.0
    sm = W.concentration(ok)
    assert not [b for b in sm["breaches"] if b["kind"] in ("single", "beta")], sm["breaches"]
    assert W.concentration({"error": "x"})["breaches"] == [] and W.concentration(None)["breaches"] == []

    # ---------------------------------------------------------------- health
    se = StressEngine(T.m, T.fr)
    st = se.compute()
    h = W.health_status(st, 3600)
    assert h["coverage"] is not None and 0 < h["coverage"] <= 1
    # a missing component lowers coverage below the threshold → alert, with the reason
    class _C:  # minimal stand-in
        def __init__(self, i, s, status): self.id, self.score, self.status = i, s, status
    class _S:
        coverage = 0.8
        components = [_C("hy_oas", None, "error:x"), _C("vix", 50.0, "ok")]
    al = W.health_alerts(_S(), 3600, date(2026, 10, 2))
    assert al and al[0][0] == "health:coverage:20261002" and "hy_oas" in al[0][3], al
    assert W.health_alerts(_S(), 3600, date(2026, 10, 3))[0][0] != al[0][0]
    # source stale → alert (but not during the post-restart grace period)
    HEALTH.sources.clear()
    HEALTH.ok("fred", 5, every=60)
    HEALTH.sources["fred"].last_ok = time.time() - 3600
    assert any(a[0].startswith("health:src:fred") for a in W.health_alerts(None, 3600))
    assert not W.health_alerts(None, 60)
    HEALTH.sources.clear()
    rep = shock_tests(st)
    playbook_tests(st, rep)
    print("WATCH TESTS PASSED ✅")


def shock_tests(st):
    import numpy as np
    import pandas as pd
    from wsb.analytics import shock as SH
    # ---- AUC sanity
    y = pd.Series([0] * 50 + [1] * 50)
    assert abs(SH.auc(pd.Series(range(100)), y) - 1.0) < 1e-9
    assert abs(SH.auc(pd.Series(range(100)[::-1]), y) - 0.0) < 1e-9
    rng = np.random.default_rng(1)
    assert abs(SH.auc(pd.Series(rng.normal(size=4000)), pd.Series(rng.integers(0, 2, 4000))) - 0.5) < 0.05
    # ---- drawdown episodes: a clean synthetic series with one known 20% fall
    idx = pd.bdate_range("2010-01-01", periods=600)
    px = pd.Series(100.0, index=idx)
    px.iloc[:200] = np.linspace(100, 150, 200)                    # rise to peak at i=199
    px.iloc[200:300] = np.linspace(150, 120, 100)                 # -20% fall, trough at i=299
    px.iloc[300:] = np.linspace(120, 160, 300)                    # recovery to a new high
    ssi = pd.Series(30.0, index=idx)
    ssi.iloc[160:] = 60.0                                          # warning 40 days before the peak
    eps = SH.drawdown_episodes(px, ssi)
    assert len(eps) == 1, eps
    e = eps[0]
    assert e["peak"] == idx[199].strftime("%Y-%m-%d") and e["trough"] == idx[299].strftime("%Y-%m-%d")
    assert abs(e["depth_pct"] + 20.0) < 0.1 and e["warned_before_peak"] and 35 <= e["lead_days"] <= 45, e
    ssi2 = pd.Series(30.0, index=idx)                              # model never warns → must be reported as a miss
    assert SH.drawdown_episodes(px, ssi2)[0]["first_warn"] is None
    # ---- walk-forward on a predictable synthetic world: SSI high right before every drop
    n = 4200
    idx2 = pd.bdate_range("2000-01-03", periods=n)
    r = np.random.default_rng(7).normal(0.0003, 0.008, n)
    s_ = np.full(n, 30.0)
    for k in range(300, n - 200, 420):                            # crash episode every ~420 days
        s_[k - 40:k] = 75.0                                       # stress builds first …
        r[k:k + 30] = -0.006                                      # … then price falls ~17%
        r[k + 30:k + 90] = 0.0035                                 # … and recovers to a new high
    close = pd.Series(100 * np.exp(np.cumsum(r)), index=idx2)
    ssi3 = pd.Series(s_, index=idx2)
    wf = SH.walk_forward(ssi3, close, 63, 0.10)
    assert wf["n_test"] > 1000 and wf["auc_oos"] > 0.7 and wf["skill"] > 0.2, wf
    noise = pd.Series(np.random.default_rng(3).uniform(0, 100, n), index=idx2)       # a useless model must score ~0.5
    assert abs(SH.walk_forward(noise, close, 63, 0.10)["auc_oos"] - 0.5) < 0.1
    q = SH.model_quality(ssi3, close)
    assert q["episode_summary"]["n"] >= 5 and q["episode_summary"]["warned_any"] >= 5, q["episode_summary"]
    # ---- radar / paths / divergence on the real synthetic engine output
    spx = T.m.series("^GSPC")
    rep = SH.build(st, spx, q)
    assert rep["radar"] and all(x["state"] in ("點火中", "升溫", "平靜") for x in rep["radar"])
    assert rep["paths"] and rep["paths"][0]["ignition"] >= rep["paths"][-1]["ignition"]
    d = rep["divergence"]
    assert d["available"] and abs(d["gap"] - (d["credit"] - d["equity"])) < 1e-9
    print("  radar top:", [(x["block"], round(x["level"]), x["state"]) for x in rep["radar"][:3]],
          "| top path:", rep["paths"][0]["name"], round(rep["paths"][0]["ignition"], 1), "| gap", round(d["gap"], 1))
    return rep


def playbook_tests(st, rep):
    import types
    import numpy as np
    import pandas as pd
    from datetime import date, timedelta
    from wsb.analytics import playbook as PB
    from wsb.config import SETTINGS
    from wsb.data import liquidity as LQ
    levels = SETTINGS.get("stress_levels", [])
    # ---- scoring: monotone, transparent, thresholds as documented
    calm = PB.score(30, levels, {"horizons": [{"days": 63, "lift_adj": 0.8}]}, {"paths": [], "divergence": {}}, {"flags": []})
    assert calm["stage"] == 0 and calm["points"] == 0, calm
    hot_shock = {"paths": [{"name": "信用事件", "state": "高度警戒", "ignition": 80, "blocks": ["信用"], "story": "x"}],
                 "divergence": {"flag": True, "gap": 20}}
    hot = PB.score(75, levels, {"horizons": [{"days": 63, "lift_adj": 2.5}]}, hot_shock, {"flags": [{"key": "a"}, {"key": "b"}]})
    assert hot["stage"] == 3 and hot["points"] >= 6, hot
    # a divergence flag only scores when history backs it (here: history says it is NOT more dangerous → 0 points)
    unbacked = PB.score(30, levels, {}, {"paths": [], "divergence": {"flag": True, "gap": 20, "hist": {"prob_when_flagged": 8.0, "base_rate": 16.0}}}, {"flags": []})
    assert unbacked["points"] == 0 and unbacked["why"] and unbacked["why"][0][0] == 0, unbacked
    backed = PB.score(30, levels, {}, {"paths": [], "divergence": {"flag": True, "gap": 20, "hist": {"prob_when_flagged": 24.0, "base_rate": 16.0}}}, {"flags": []})
    assert backed["points"] == 1, backed
    mid = PB.score(62, levels, {"horizons": [{"days": 63, "lift_adj": 1.6}]}, {"paths": [], "divergence": {}}, {"flags": []})
    assert mid["stage"] == 1 and mid["points"] == 2, mid
    # ---- hysteresis: rises at once, falls only when 2 points below the entry threshold
    assert PB.hysteresis(None, mid) == 1 and PB.hysteresis(0, mid) == 1
    assert PB.hysteresis(2, {"stage": 1, "points": 3}) == 2          # 3 pts: not yet 2 below the stage-2 entry (4)
    assert PB.hysteresis(2, {"stage": 1, "points": 2}) == 1
    # ---- actions: stage 2 names a target beta below today's, stage 3 below stage 2
    pf = {"beta": 1.2}
    a2 = " ".join(PB.actions(2, pf, [{"sym": "NVDA", "sell_usd": 1000}], rep))
    a3 = " ".join(PB.actions(3, pf, [], rep))
    assert "1.02" in a2 and "NVDA" in a2 and "0.78" in a3, (a2, a3)
    assert PB.actions(0, {"error": "x"}, None, {})
    # ---- regime breaks: engineered world where bonds fall with stocks → flags fire; independent world → none
    n = 700
    idx = pd.bdate_range("2020-01-01", periods=n)
    rng = np.random.default_rng(11)
    e = rng.normal(0, 0.01, n)

    def mk(rb, rg_):
        return types.SimpleNamespace(series=lambda t: pd.Series(
            100 * np.exp(np.cumsum({"^GSPC": e, "TLT": rb, "GC=F": rg_}[t])) if t in ("^GSPC", "TLT", "GC=F") else [], index=idx[:n]) if t in ("^GSPC", "TLT", "GC=F") else pd.Series(dtype=float))
    bad = PB.regime_breaks(mk(0.8 * e + rng.normal(0, 0.002, n), 0.7 * e + rng.normal(0, 0.003, n)))
    assert bad["available"] and {f["key"] for f in bad["flags"]} >= {"stock_bond", "double_kill"}, bad
    good = PB.regime_breaks(mk(-0.6 * e + rng.normal(0, 0.003, n), -0.3 * e + rng.normal(0, 0.003, n)))
    assert good["available"] and not good["flags"], good["flags"]
    assert not PB.regime_breaks(types.SimpleNamespace(series=lambda t: pd.Series(dtype=float)))["available"]
    # ---- liquidity calendar
    assert LQ.third_friday(2026, 10) == date(2026, 10, 16)
    assert LQ.third_friday(2026, 6) == date(2026, 6, 18)             # Juneteenth (Fri) → Thursday
    assert LQ.vix_expiry(2026, 10) == date(2026, 10, 21)
    assert LQ.month_end(2026, 9) == date(2026, 9, 30) and LQ.month_end(2026, 10).weekday() < 5
    ev = LQ.computed_events(date(2026, 12, 1), 40)
    assert any(x["importance"] == 3 and "四巫日" in x["event"] for x in ev), ev            # Dec 18 quad witching
    assert any(x["importance"] == 3 and "季底" in x["event"] for x in ev), ev
    assert all(x["date"] >= "2026-12-01" for x in ev)
    # ---- views render (slides + embeds) on a synthetic engine
    from wsb.bot import command as CMD
    from wsb.analytics import crash_odds as CO, regime as RG, portfolio as PFO
    odds = CO.crash_odds(st.history, T.m.series("^GSPC"), st.score, st.chg_20d)
    brk = PB.regime_breaks(T.m)
    shock = dict(rep)
    pbk = PB.score(st.score, levels, odds, shock, brk)
    port = PFO.analyze(T.m, {"NVDA": {"shares": 15, "cost": 50, "currency": "USD", "name": "NVDA"}})
    pbk["derisk"] = []
    pbk["actions"] = PB.actions(pbk["stage"], port, [], shock)
    cal = types.SimpleNamespace(events=[], upcoming=lambda d=14: [
        {"date": (date.today() + timedelta(days=3)).isoformat(), "type": "liquidity", "event": "月選擇權到期日（OPEX）", "importance": 2},
        {"date": (date.today() + timedelta(days=5)).isoformat(), "type": "fomc", "event": "FOMC 利率決議"}])
    from wsb.analytics import lab as LB
    labrep = LB.run(T.m.history, st.history, T.m.series("^GSPC"))
    assert labrep["horizons"] and labrep["horizons"][1]["baseline"]
    eng = types.SimpleNamespace(stress=st, odds=odds, shock=shock, breaks=brk, playbook=pbk, portfolio=port, calendar=cal, lab=labrep)
    for deck in (CMD.deck_command(eng), CMD.deck_shock(eng)):
        assert deck and all(len(b) > 5000 for b in deck)
    assert len(CMD.deck_command(eng)) == 6 and len(CMD.deck_shock(eng)) == 4
    assert CMD.embed_command(eng).title and CMD.embed_shock(eng).description
    empty = types.SimpleNamespace(stress=None, playbook={}, shock={}, breaks={}, odds={}, portfolio={}, calendar=cal)
    assert len(CMD.deck_command(empty)) == 1 and len(CMD.deck_shock(empty)) == 1
    print("  playbook:", pbk["name"], pbk["points"], "| breaks:", [f["key"] for f in brk.get("flags", [])])


if __name__ == "__main__":
    main()
