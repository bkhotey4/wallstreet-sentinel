"""Offline end-to-end test with synthetic markets (no network, no Discord).
Run:  python -m tests.test_offline
Verifies: stress index, crash odds, regime, portfolio risk, AI data pack,
embed builders, news scoring, options GEX parsing."""
from __future__ import annotations

import sys
import types

import numpy as np
import pandas as pd

# ---- stub optional heavy deps only if missing (lets the test run anywhere) ----
for mod in ("aiohttp", "feedparser"):
    try:
        __import__(mod)
    except ImportError:
        sys.modules[mod] = types.ModuleType(mod)
try:
    import discord  # noqa: F401
except ImportError:
    d = types.ModuleType("discord")

    class Embed:
        def __init__(self, title=None, description=None, color=None, timestamp=None):
            self.title, self.description, self.color, self.fields, self.footer = title, description, color, [], None

        def add_field(self, name, value, inline=True):
            assert len(name) <= 256 and len(value) <= 1024, (name, len(value))
            self.fields.append((name, value))

        def set_footer(self, text):
            self.footer = text
    d.Embed = Embed
    abc = types.ModuleType("discord.abc")
    abc.Messageable = object
    d.abc = abc
    sys.modules["discord"] = d
    sys.modules["discord.abc"] = abc

from wsb.config import SETTINGS  # noqa: E402
from wsb.analytics.stress import StressEngine  # noqa: E402
from wsb.analytics import crash_odds, regime, portfolio  # noqa: E402
from wsb.data.market import MarketData  # noqa: E402
from wsb.data.fred import FredData  # noqa: E402
from wsb.data.news import score_title  # noqa: E402
from wsb.data.options import parse_chain  # noqa: E402

rng = np.random.default_rng(7)
# the synthetic history ends on the last business day (a fixed end date made every component "stale" a week later)
END = (pd.Timestamp.today().normalize() - pd.tseries.offsets.BDay(1)).normalize()
idx = pd.bdate_range("2012-01-02", END)
n = len(idx)

# market factor with two crash episodes
mkt = rng.normal(0.0004, 0.01, n)
for start in (1500, 2900):
    mkt[start:start + 25] = rng.normal(-0.012, 0.03, 25)
stress_factor = pd.Series(-mkt).rolling(20).mean().fillna(0).values

cols = {}
for t in SETTINGS.all_tickers() + ["NVDA", "TSM", "NEWCO"]:
    beta = rng.uniform(0.3, 1.6)
    if t.startswith("^VIX") or t in ("^VVIX", "^MOVE", "^SKEW"):
        base = 18 if t != "^VVIX" else 90
        lvl = base * np.exp(np.clip(np.cumsum(rng.normal(0, 0.02, n)) * 0.1 + stress_factor * 40 * (1.2 if t == "^VIX" else 1.0), -1, 2))
        cols[t] = lvl
        continue
    r = beta * mkt + rng.normal(0, 0.008, n)
    if t in ("HYG", "KRE", "BIZD", "AUDJPY=X", "EMB"):
        r = r + stress_factor * -0.5
    if t == "JPY=X":
        r = -0.3 * mkt + rng.normal(0, 0.005, n)
    cols[t] = 100 * np.exp(np.cumsum(r))
hist = pd.DataFrame(cols, index=idx)
hist.loc[:"2020-01-01", "NEWCO"] = np.nan   # recent IPO → beta proxy path

m = MarketData.__new__(MarketData)
m.tickers, m.history, m.history_ts, m.quotes_ts = list(hist.columns), hist, 1, 1
m.quotes = {t: {"price": float(hist[t].iloc[-1]), "prev": float(hist[t].iloc[-2]),
                "chg_pct": float(hist[t].iloc[-1] / hist[t].iloc[-2] - 1) * 100, "asof": END.strftime("%Y-%m-%d")}
            for t in hist.columns}

fr = FredData()
widx = pd.date_range("2012-01-04", END - pd.Timedelta(days=4), freq="W-WED")
fr.series = {
    "BAMLH0A0HYM2": pd.Series(4 + stress_factor * 150 + rng.normal(0, 0.1, n), index=idx)["2023-09-01":],
    "BAMLH0A3HYC": pd.Series(9 + stress_factor * 300, index=idx)["2023-09-01":],
    "NFCI": pd.Series(-0.5 + np.cumsum(rng.normal(0, 0.02, len(widx))), index=widx),
    "STLFSI4": pd.Series(np.cumsum(rng.normal(0, 0.05, len(widx))), index=widx),
    "WALCL": pd.Series(7e6 + np.cumsum(rng.normal(0, 2e4, len(widx))), index=widx),
    "WTREGEN": pd.Series(7e5 + rng.normal(0, 5e4, len(widx)), index=widx),
    "RRPONTSYD": pd.Series(np.abs(500 + np.cumsum(rng.normal(0, 20, n))), index=idx),
    "DGS2": pd.Series(3 + np.cumsum(rng.normal(0, 0.03, n)), index=idx),
    "T10Y3M": pd.Series(np.cumsum(rng.normal(0, 0.02, n)), index=idx),
    "T10YIE": pd.Series(2.3 + np.cumsum(rng.normal(0, 0.01, n)), index=idx),
}


def main():
    se = StressEngine(m, fr)
    st = se.compute()
    assert st is not None and 0 <= st.score <= 100, st
    assert len(st.history) > 1500 and st.history.between(0, 100).all()
    live = [c for c in st.components if c.score is not None]
    print(f"SSI {st.score:.1f} {st.label} | live comps {len(live)}/{len(st.components)} | cov {st.coverage:.2f}")
    print("blocks", {k: round(v, 1) for k, v in st.blocks.items()})
    print("drivers", [(c.id, round(c.score)) for c in st.drivers(4)])
    # stress should be higher during injected crashes than in calm times
    crash_mean = st.history.iloc[1510 - 300:1525 - 300].mean() if False else st.history.loc[idx[1510]:idx[1525]].mean()
    calm_mean = st.history.loc[idx[1100]:idx[1400]].mean()
    print(f"crash-window SSI {crash_mean:.1f} vs calm {calm_mean:.1f}")
    assert crash_mean > calm_mean + 10

    od = crash_odds.crash_odds(st.history, m.series("^GSPC"), st.score)
    assert od["horizons"] and all(0 <= h["base_rate"] <= 100 for h in od["horizons"])
    for h in od["horizons"]:
        print(f"  {h['days']}d ≤-{h['drawdown_pct']:.0f}%: cond {h['conditional']} base {h['base_rate']:.1f} table {[(t['zone'], round(t['prob'],1)) for t in h['table']]}")
    # regression: FRED series that carry weekend observations used to crash the release-lag shift (duplicate labels)
    import wsb.analytics.stress as _S
    _d = pd.bdate_range("2026-01-05", periods=40)
    _wk = pd.Series(1.0, index=_d.union(_d[:30] + pd.Timedelta(days=1)))      # every day also has a +1 day (Fri→Sat) twin
    fr.series["_TEST_WEEKEND"] = _wk
    try:
        _x = _S.StressEngine(m, fr)._fr("_TEST_WEEKEND", pd.bdate_range("2026-01-05", periods=60))
        assert _x.notna().sum() > 30
    finally:
        fr.series.pop("_TEST_WEEKEND", None)
    assert all(c.status for c in st.components)
    assert all((c.score is None) == (c.status != "ok") for c in st.components), "status must explain every excluded component"
    # sigma_move: a live quote newer than history is measured by its own move; a non-positive price can't break the log
    tk = "^GSPC"
    q0 = dict(m.quotes[tk]) if tk in m.quotes else None
    last_px = float(m.series(tk).iloc[-1])
    m.quotes[tk] = {"price": last_px * 0.90, "prev": last_px, "chg_pct": -10.0, "asof": "2999-01-01", "fetched": 0}
    assert m.sigma_move(tk) < -3, m.sigma_move(tk)
    if q0 is not None:
        m.quotes[tk] = q0
    mo = od["momentum"]
    print("  momentum", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in mo.items()})
    assert mo["state"] in ("升溫", "持平", "降溫") and mo["th_rising"] > mo["th_falling"]
    for h in od["horizons"]:
        assert h["adjusted"] is not None and 0 <= h["adjusted"] <= 100
        lo_, hi_ = sorted([h["conditional"], h["cell_raw"] if h["cell_raw"] is not None else h["conditional"]])
        assert lo_ - 1e-9 <= h["adjusted"] <= hi_ + 1e-9, "shrinkage must sit between cell and level estimates"
    # forcing a fast rise must classify as 升溫, and a thin cell stays near the level estimate
    od_up = crash_odds.crash_odds(st.history, m.series("^GSPC"), st.score, chg20=99.0)
    assert od_up["momentum"]["state"] == "升溫" and od_up["momentum"]["pctile"] >= 99
    assert crash_odds.lift_text(1.0).startswith("約等於") and "高於" in crash_odds.lift_text(2.1) and "低於" in crash_odds.lift_text(0.74)
    # sanity: forward_min_return correctness
    s = pd.Series([100, 90, 95, 120, 80.0])
    fm = crash_odds.forward_min_return(s, 2)
    assert abs(fm.iloc[0] - (90 / 100 - 1)) < 1e-9 and abs(fm.iloc[2] - (80 / 95 - 1)) < 1e-9 and np.isnan(fm.iloc[3])

    rg = regime.classify(m, fr)
    print("regime", rg.get("quadrant"), rg.get("risk_mode"), rg.get("liquidity_mode"))
    assert rg.get("quadrant")

    holdings = {"NVDA": {"shares": 15, "cost": 50, "currency": "USD", "name": "NVDA"},
                "TSM": {"shares": 12, "cost": 60, "currency": "USD", "name": "TSM"},
                "NEWCO": {"shares": 10, "cost": 30, "currency": "USD", "name": "NEWCO"}}
    pf = portfolio.analyze(m, holdings)
    assert not pf.get("error"), pf
    assert abs(sum(p["weight"] for p in pf["positions"]) - 100) < 1e-6
    assert abs(sum(p["risk_contrib_pct"] for p in pf["positions"]) - 100) < 1e-6
    assert pf["var99_1d_usd"] >= pf["var95_1d_usd"] > 0
    print(f"portfolio ${pf['total_value_usd']:.0f} beta {pf['beta']:.2f} VaR99 {pf['var99_1d_usd']:.0f} proxied {pf['proxied']}")
    for sc in pf["scenarios"]:
        print(f"  {sc['name']}: bench {sc['bench_pct']} port {sc['port_pct']:.1f} proxied {sc['proxied']}")

    sc_, hits = score_title("Regional bank run fears spark contagion as private credit fund gated", SETTINGS["news_keywords"])
    assert sc_ >= 12 and "bank run" in hits, (sc_, hits)
    assert score_title("台海緊張 台股暴跌", SETTINGS["news_keywords"])[0] >= 6

    # options parsing on a synthetic chain
    opts = []
    for k in range(4000, 6001, 25):
        for typ in "CP":
            opts.append({"option": f"SPXW261016{typ}{k*1000:08d}", "iv": 0.18, "open_interest": 1000 + abs(5000 - k),
                         "volume": 100, "gamma": 0})
    op = parse_chain({"data": {"current_price": 5000, "options": opts}}, max_days=9999)
    print("gamma", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in op.items()})
    assert op["put_call_oi"] > 0

    # AI data pack + embeds
    class Eng:
        pass
    eng = Eng()
    eng.market, eng.fred, eng.stress, eng.odds, eng.regime, eng.portfolio = m, fr, st, od, rg, pf
    eng.options = types.SimpleNamespace(spx=op)
    eng.crypto = types.SimpleNamespace(data={"crypto_fng": 40, "btc_dominance": 57.1})
    eng.news = types.SimpleNamespace(items=[], top=lambda n=15, q=None: [], latest=lambda n=15: [])
    eng.sec = types.SimpleNamespace(recent=[])
    eng.calendar = types.SimpleNamespace(events=[{"date": "2026-10-15", "event": "CPI", "type": "macro"}],
                                         upcoming=lambda d=14: [{"date": "2026-10-15", "event": "CPI", "type": "macro"}])
    eng.age_str = lambda: "test"
    from wsb.ai import context
    pack = context.build(eng, "full")
    assert "SSI" in pack and "NA%" not in pack.split("\n")[1]
    print(f"data pack: {len(pack)} chars, {pack.count(chr(10))} lines")
    from wsb.bot import embeds as E
    for fn in (E.dashboard, E.risk, E.crash, E.macro, E.options, E.portfolio, E.stress_test, E.calendar):
        e = fn(eng)
        assert e.description is None or len(e.description) <= 4096
    for g in SETTINGS.universe:
        E.market_group(eng, g)
    parts = E.chunks("x" * 5000 + "\n" + "line\n" * 800)
    assert all(len(p) <= 1900 for p in parts)
    # ---- hedge calculator on a synthetic SPY/QQQ chain ----
    from datetime import date, timedelta
    from wsb.analytics import hedge as HG
    from wsb.data.options import implied_move
    def chain(spot):
        rows = []
        for dte in (14, 44, 91, 180):
            exp = (date.today() + timedelta(days=dte)).isoformat()
            for k in range(int(spot * 0.7), int(spot * 1.2), 5):
                for typ in "CP":
                    intrinsic = max(k - spot, 0) if typ == "P" else max(spot - k, 0)
                    mid = intrinsic + spot * 0.2 * (dte / 365) ** 0.5 * 0.4 * np.exp(-abs(k / spot - 1) * 4)
                    rows.append({"type": typ, "strike": float(k), "expiry": exp, "dte": float(dte), "bid": mid * .98,
                                 "ask": mid * 1.02, "mid": mid, "iv": 0.2, "oi": 100, "delta": 0})
        return {"spot": spot, "rows": rows}
    pf["betas"] = {"SPY": 1.3, "QQQ": 1.05}
    hr = HG.analyze(pf, {"SPY": chain(650.0), "QQQ": chain(560.0)}, 62.0)
    assert not hr.get("error") and hr["underlyings"]["SPY"]["plans"], hr
    pl = hr["underlyings"]["SPY"]["plans"][0]
    assert pl["cost"] > 0 and pl["payoff"][20]["hedged"] > pl["payoff"][20]["unhedged"]
    print("hedge:", {k: (v["plans"][0]["expiry"], round(v["plans"][0]["cost"]), round(v["raw_contracts"], 2)) for k, v in hr["underlyings"].items()})
    print("advice:", hr["advice"])
    print("derisk:", [(d["sym"], round(d["sell_usd"])) for d in hr["derisk"]])
    im = implied_move(chain(200.0), (date.today() + timedelta(days=10)).isoformat())
    assert im and 0 < im["move_pct"] < 50, im
    print("implied move:", round(im["move_pct"], 2), im["expiry"])

    # ---- scorecard ----
    from wsb.analytics import scorecard as SC
    import time as _t
    spx = m.series("^GSPC")
    spx = spx.copy()
    spx.index = pd.bdate_range(end=pd.offsets.BDay().rollback(pd.Timestamp.today().normalize()), periods=len(spx))
    now = _t.time()
    rows_ = [(now - 40 * 86400, "ssi_level_3", "risk", "🚨 CRITICAL", "壓力升級", float(spx.iloc[-29]), 72.0),
             (now - 40 * 86400 + 3600, "vix_backwardation", "risk", "🚨 CRITICAL", "VIX倒掛", float(spx.iloc[-29]), 73.0),
             (now - 10 * 86400, "news:x", "news", "⚠️ WARNING", "銀行擠兌", float(spx.iloc[-8]), 60.0),
             (now - 3600, "sigma:^GSPC:x:-1", "risk", "🚨 CRITICAL", "標普急跌", float(spx.iloc[-1]), 65.0)]
    sc = SC.evaluate(rows_, spx)
    assert sc["summary"]["risk"]["episodes"] == 2, sc["summary"]   # first two merged into one episode
    print("scorecard:", {k: v["by_horizon"] for k, v in sc["summary"].items()})
    for fn in (lambda: E.hedge(eng, hr), lambda: [E.scorecard(eng, sc)],
               lambda: [E.earnings_preview(eng, {"ticker": "NVDA", "date": "2026-10-20", "implied": im, "value": 3000, "shares": 15})]):
        for emb in fn():
            assert emb.description is None or len(emb.description) <= 4096
    print("ALL OFFLINE TESTS PASSED ✅")


if __name__ == "__main__":
    main()
