"""10 年債利率壓力通知: measured against the yield's own 20-day moves, needs a 60-day high/low, plain and no trading words.
Run: python -m tests.test_rate_pressure"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rp_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import web_alerts as WA  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "加碼參考區", "進場參考區")


def _ser(tail):
    rng = np.random.default_rng(5)
    idx = pd.bdate_range(end="2026-10-30", periods=1200)
    y = 4.5 + np.cumsum(rng.normal(0, 0.04, len(idx)))
    y[-20:] = y[-21] + np.linspace(0, tail, 20)
    tnx = pd.Series(y, index=idx)
    ndx = pd.Series(20000 * np.cumprod(1 - 0.01 * np.diff(np.r_[y[0], y]) * 3 + rng.normal(0, 0.005, len(idx))), index=idx)
    return tnx, ndx


class _M:
    def __init__(self, s):
        self.s = s

    def series(self, t):
        return self.s.get(t, pd.Series(dtype=float))


class _E:
    def __init__(self, tnx, ndx):
        self.market = _M({"^TNX": tnx, "^NDX": ndx})


def test_down_and_up():
    now = datetime(2026, 10, 31, tzinfo=timezone.utc)
    for tail, key, tone in ((-1.2, "rate:dn", "good"), (1.2, "rate:up", "watch")):
        tnx, ndx = _ser(tail)
        r = WA.rate_pressure(tnx, ndx)
        assert r and abs(r["z"]) >= 1.5 and r["ndx_per10"] < 0 and 0 <= r["pct10y"] <= 100
        out = []
        WA._rates(_E(tnx, ndx), out, now)
        assert len(out) == 1 and out[0]["key"].startswith(key) and out[0]["tone"] == tone and out[0]["tab"] == "bonds"
        txt = out[0]["zh"] + out[0]["detail"]
        assert "平常" in txt and "10bp" in txt
        for w in BANNED:
            assert w not in txt


def test_quiet_and_short():
    tnx, ndx = _ser(0.0)
    out = []
    WA._rates(_E(tnx, ndx), out, datetime(2026, 10, 31, tzinfo=timezone.utc))
    assert out == []
    assert WA.rate_pressure(tnx.iloc[-300:], ndx) is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
