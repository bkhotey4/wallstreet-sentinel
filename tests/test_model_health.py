"""模型近期失準偵測: recent record vs the model's own long-run record — pure functions, synthetic data.
Run: python -m tests.test_model_health"""
from __future__ import annotations

import os
import sys
import tempfile

import numpy as np

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_mh_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.analytics import model_health as MH  # noqa: E402


def _series(years, good_until, rng):
    """One prediction per day: informative (p tracks y) up to `good_until`, pure noise after."""
    P, Y, YR = [], [], []
    for yr in years:
        y = (rng.random(250) < 0.15).astype(float)
        p = np.clip(0.1 + 0.5 * y + rng.normal(0, 0.15, 250), 0.01, 0.99) if yr <= good_until else rng.random(250)
        P += p.tolist(); Y += y.tolist(); YR += [yr] * 250
    return P, Y, YR


def test_crash():
    rng = np.random.default_rng(7)
    yrs = list(range(2005, 2026))
    ok = MH.crash_drift(*_series(yrs, 2030, rng))
    assert ok["status"] == "ok" and ok["recent_auc"] > 0.8 and ok["recent_years"] == [2023, 2024, 2025], ok
    bad = MH.crash_drift(*_series(yrs, 2022, rng))                # the last 3 years became noise
    assert bad["status"] == "drift" and bad["recent_auc"] < 0.6 and bad["overall_auc"] > bad["recent_auc"], bad
    # rare events recently → cannot judge (never reported as fine)
    P, Y, YR = _series(yrs, 2030, rng)
    Y = [0.0 if yr >= 2023 else y for y, yr in zip(Y, YR)]
    thin = MH.crash_drift(P, Y, YR)
    assert thin["status"] == "insufficient" and "無法判斷" in thin["why"]
    assert MH.crash_drift([], [], [])["status"] == "insufficient"


def test_alerts():
    now = 1_800_000_000.0
    old = [{"ts": now - 400 * 86400 + i * 86400, "results": {20: {"hit": i % 2 == 0}}} for i in range(20)]   # 50% long-run
    rec_bad = [{"ts": now - 30 * 86400 + i * 86400, "results": {20: {"hit": False}}} for i in range(6)]
    r = MH.alert_drift(old + rec_bad, now, 20)
    assert r["status"] == "drift" and r["recent_hit"] == 0 and r["recent_n"] == 6, r
    rec_ok = [{"ts": now - 30 * 86400 + i * 86400, "results": {20: {"hit": i % 2 == 0}}} for i in range(6)]
    assert MH.alert_drift(old + rec_ok, now, 20)["status"] == "ok"
    pend = [{"ts": now - 3 * 86400, "results": {20: None}}]
    assert MH.alert_drift(pend + rec_ok[:2], now, 20)["status"] == "insufficient"


def test_earn():
    ok = [{"sym": "A", "mv": 5.0, "real": r} for r in (3, -4, 6, -5, 2, 7, -3, 4, -6, 5, 3, -4)]
    assert MH.earn_drift(ok)["status"] == "ok"
    low = [{"sym": "A", "mv": 3.0, "real": r} for r in (6, -7, 8, -5, 9, 6, -7, 5, -8, 6, 7, -6)]   # options too low
    d = MH.earn_drift(low)
    assert d["status"] == "drift" and d["median_ratio"] > 1.5 and "偏低" in d["why"], d
    assert MH.earn_drift(low[:5])["status"] == "insufficient"


def test_flag():
    h = {"models": [{"key": "crash_21", "status": "ok"}, {"key": "crash_63", "status": "drift", "why": "x"},
                    {"key": "alerts", "status": "watch"}]}
    assert MH.flag(h, "crash_63")["status"] == "drift" and MH.flag(h, "crash_21") is None
    assert MH.flag(h, "crash_")["status"] == "drift" and MH.flag(None, "crash_") is None


def test_build_labels():
    import types
    eng = types.SimpleNamespace(lab={"horizons": [{"days": 63, "drawdown_pct": 10.0, "drift": {"status": "drift", "why": "w"}}]}, market=None)
    h = MH.build(eng, now_ts=1_800_000_000.0)
    m = [x for x in h["models"] if x["key"] == "crash_63"][0]
    assert "63 交易日內跌 ≥10%" in m["zh"] and m["status"] == "drift" and h["status"] == "drift", m


def main():
    test_build_labels()
    test_crash()
    test_alerts()
    test_earn()
    test_flag()
    print("MODEL HEALTH TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
