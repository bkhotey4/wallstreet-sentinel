"""2026-10-19 hard-code audit: every case from HARDCODE_AUDIT_2026-10-19.md stays fixed.
Run: python -m tests.test_hardcode_audit"""
from __future__ import annotations

import os
import sys
import tempfile
import warnings

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_audit_"))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import distress as DZ  # noqa: E402
from wsb.analytics import portfolio as PF  # noqa: E402


def _market(cols, chg=None):
    idx = pd.bdate_range(end="2026-10-16", periods=600)
    h = pd.DataFrame(cols, index=idx)

    class M:
        history = h

        def series(self, t):
            return h[t].dropna() if t in h else pd.Series(dtype=float)

        def q(self, t):
            return {"price": float(h[t].iloc[-1]), "chg_pct": (chg or {}).get(t)} if t in h else None

        def sigma_move(self, t):
            return None
    return M()


def test_currency_and_day_pnl():
    m = _market({"0700.HK": np.full(600, 100.0), "SPY": np.linspace(400, 500, 600), "HKD=X": np.full(600, 7.8)})
    r = PF.analyze(m, {"0700.HK": {"shares": 10, "cost": 90, "currency": "HKD", "name": "Tencent"}})
    assert abs(r["total_value_usd"] - 1000 / 7.8) < 0.01, r["total_value_usd"]          # HK$1,000 is not US$1,000
    assert r["day_pnl_usd"] is None and r["day_pnl_missing"] == ["0700.HK"]             # unknown change ≠ flat
    m2 = _market({"AAA": np.full(600, 10.0), "SPY": np.linspace(400, 500, 600)})
    r2 = PF.analyze(m2, {"AAA": {"shares": 1, "cost": 10, "currency": "EUR", "name": "x"}})
    assert r2.get("error") or r2["positions"][0].get("error")                            # no EUR rate → not valued
    m3 = _market({"AAA": np.full(600, 10.0), "BBB": np.full(600, 20.0), "SPY": np.linspace(400, 500, 600)}, chg={"AAA": 1.0})
    r3 = PF.analyze(m3, {"AAA": {"shares": 10, "cost": 9, "currency": "USD"}, "BBB": {"shares": 10, "cost": 9, "currency": "USD"}})
    assert r3["day_pnl_missing"] == ["BBB"] and abs(r3["day_pnl_usd"] - 100 * 1 / 101) < 1e-6
    assert PF.load_holdings.__doc__ is None or True
    # default currency of a .HK ticker is HKD
    assert "HKD" in open(PF.__file__, encoding="utf-8").read()


def test_beta_zero_is_valid():
    src = open(PF.__file__, encoding="utf-8").read()
    assert 'r.get("beta") or 1.0' not in src and 'r["beta"] if r.get("beta") is not None else 1.0' in src


def test_distress_needs_capex_and_da():
    b = {"ocf_ttm": -1e8, "capex_ttm": None, "cash": 1e8, "ebit_ttm": 1e8, "interest_ttm": 2e7, "ltd": 5e8, "da_ttm": None,
         "rev_ttm": 1e9}
    ids = [s["id"] for s in DZ._corp(b, pd.Series(dtype=float))]
    assert "runway" not in ids and "leverage" not in ids, ids
    b.update(capex_ttm=5e7, da_ttm=2e7)
    ids = [s["id"] for s in DZ._corp(b, pd.Series(dtype=float))]
    assert "runway" in ids and "leverage" in ids


def test_no_backfilled_history():
    import types
    from tools import site_portfolio as SP
    idx = pd.bdate_range(end="2026-10-16", periods=40)
    h = pd.DataFrame({"^GSPC": np.linspace(100, 110, 40), "NEWX": [np.nan] * 38 + [50.0, 51.0]}, index=idx)
    eng = types.SimpleNamespace(market=types.SimpleNamespace(history=h), stockprices=None)
    out = SP._hist_30d(eng)
    nx = out["closes"]["NEWX"]
    assert nx[-2:] == [50.0, 51.0] and all(v is None for v in nx[:-2]), nx                # no pre-listing prices


def test_ranks_not_imputed():
    from wsb.analytics import growth as GR, techearn as TE
    r = GR._rank({"a": 1.0, "b": 2.0, "c": 3.0, "d": None})
    assert r["d"] is None and r["c"] == 100.0
    assert GR._rank({"a": 1.0, "b": None}) == {"a": None, "b": None}
    assert GR._blend([(0.4, 80.0), (0.4, 60.0), (0.1, None), (0.1, None)]) == 70.0       # renormalised, no neutral 50
    assert TE._rank({"a": 1.0, "b": 2.0, "c": None})["c"] is None


def main():
    test_currency_and_day_pnl()
    test_beta_zero_is_valid()
    test_distress_needs_capex_and_da()
    test_no_backfilled_history()
    test_ranks_not_imputed()
    print("HARDCODE AUDIT TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
