"""Third round of external reviews (2026-10-28): an emptied portfolio on recompute, stamped Gamma / SSI keys in the
outbox, superseded state signals, scenario coverage, close-confirmed stops, RSI edges, the earnings cut-off in New York
time, honest add counts, the bubble horizon, accumulation ranking, FOMC trading days.
Run: python -m tests.test_review3"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rv3_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return open(os.path.join(ROOT, *p), encoding="utf-8").read()


def test_empty_portfolio_clears_engine():
    from wsb.analytics import portfolio as P
    d = tempfile.mkdtemp()
    main = os.path.join(d, "main.json")
    open(main, "w").write('{"holdings": []}')
    orig = P.SETTINGS
    P.SETTINGS = {"portfolio": {"enabled": True, "file": main}}
    try:
        assert P.load_holdings() == {} and P.LOAD_OK
        os.remove(main)
        assert P.load_holdings() == {} and not P.LOAD_OK          # no file → the engine keeps its last good set
    finally:
        P.SETTINGS = orig
    assert "if pf.LOAD_OK or not self.holdings" in _src("wsb", "engine.py")


def test_edge_keys_are_stamped_and_superseded_dropped():
    app = _src("wsb", "bot", "app.py")
    assert 'Alert(f"gamma_flip:{' in app and 'Alert(f"ssi_level_{idx}:{' in app
    from wsb import store
    from wsb.bot.app import Sentinel
    store.kv_set("rules_state:NVDA", "trim")
    assert not Sentinel._still_holds("rules:NVDA:add:2026-10-27")
    store.kv_set("rules_state:NVDA", "add")
    assert Sentinel._still_holds("rules:NVDA:add:2026-10-27")
    store.kv_set("gamma_below", False)
    assert not Sentinel._still_holds("gamma_flip:202610281000") and Sentinel._still_holds("halt:NVDA:x")
    from wsb.analytics import scorecard as SC
    assert SC.family("gamma_flip:202610281000") == "Gamma 翻轉" and SC.family("ssi_level_3:202610281000") == "壓力指數升級"


def test_scenarios_do_not_zero_missing_factors():
    from wsb.analytics import xray as X
    idx = pd.bdate_range("2024-01-01", periods=400)
    rng = np.random.default_rng(1)
    mk = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400))), index=idx)

    class M:
        def series(self, s):
            return mk if s in ("SPY", "A") else pd.Series(dtype=float)
    orig_f, orig_b = X._factors, X.betas
    X._factors = lambda m: pd.DataFrame({"mkt": mk.pct_change()}).dropna()
    X.betas = lambda m, s, F, fallback_beta=None: {"b": {"mkt": 1.0}, "r2": 0.5, "n": 300, "proxy": s != "A"} if s == "A" else None
    try:
        pf = {"positions": [{"sym": "A", "value_usd": 10.0}, {"sym": "B", "value_usd": 90.0}]}
        sc = {r["name"]: r for r in X.scenarios(M(), pf)["scenarios"]}
    finally:
        X._factors, X.betas = orig_f, orig_b
    rate = next(v for k, v in sc.items() if k.startswith("利率"))
    assert rate["pnl_pct"] is None and rate["cov_pct"] == 0                 # no rate beta anywhere → not "0%"
    mk20 = sc["標普 −20%"]
    assert mk20["pnl_pct"] is None and abs(mk20["cov_pct"] - 10) < 1e-9 and "B" in mk20["missing"]


def test_rsi_all_gains_is_100():
    from wsb.analytics import signals as S
    r = S.rsi_series(pd.Series(np.arange(1.0, 41.0)))
    assert r.iloc[-1] == 100.0
    assert S.rsi_series(pd.Series([5.0] * 40)).iloc[-1] == 50.0


def test_earnings_cutoff_in_new_york_time():
    from wsb.analytics import earn_verdict as V
    assert V._before_report("2026-10-28 19:59 UTC", "2026-10-28", "after")       # 15:59 ET
    assert not V._before_report("2026-10-28 22:00 UTC", "2026-10-28", "after")   # 18:00 ET: already out
    assert not V._before_report("2026-10-29 01:00 UTC", "2026-10-28", "after")   # UTC next day = 21:00 ET
    assert V._before_report("2026-10-27 23:00 UTC", "2026-10-28", "before")
    assert not V._before_report("2026-10-28 12:00 UTC", "2026-10-28", "before")


def test_add_counts_are_honest():
    from wsb.analytics import rulebook as R
    ck = lambda i, met: {"group": "add", "id": i, "zh": i, "met": met, "txt": "", "src": ""}      # noqa: E731
    s = R.summarize([ck("room", True), ck("ma200", True), ck("quality", True), ck("macro", True), ck("mom", None), ck("beat", None)])
    if s["state"] == "add":
        assert "全部成立" not in s["zh"] and "必備 4/4" in s["zh"]
    s = R.summarize([ck("room", True), ck("ma200", True), ck("mom", True), ck("beat", True), ck("macro", True)])   # quality not listed
    assert s["state"] != "add"


def test_bubble_counts_from_next_month():
    src = _src("wsb", "analytics", "bubble.py")
    assert "np.where(dd[1:] <= -DD)[0] + 1" in src


def test_accumulation_without_down_days_ranks_top():
    from wsb.analytics import stockscore as SS
    feats = {"A": {"accum": 2.0, "accum_rank": 1e9}, "B": {"accum": 3.0}, "C": {"accum": 1.0}, "D": {"accum": 0.5}}
    r = SS._rank({k: f.get("accum_rank", f["accum"]) for k, f in feats.items()})
    assert r["A"] == max(r.values())


def test_fomc_window_uses_trading_days_and_ny_clock():
    assert "pd.bdate_range(s.index[-1]" in _src("wsb", "analytics", "fomc_drift.py")
    tw = _src("tools", "site_twlive.py")
    assert "America/New_York" in tw and "1290" not in tw
    assert 'bnd["tr1y"]' in _src("wsb", "analytics", "tw_etf.py")
    assert 'id="reloadBtn"' in _src("tools", "build_site.py")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
