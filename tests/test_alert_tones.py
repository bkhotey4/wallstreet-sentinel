"""頂部通知雙向化: healthy-direction big moves are green (not a red pop-up), 2σ index rallies, the backdrop turning
healthier (blue), the two-step oversold watch, at most 3 tier-A patterns, the ribbon on the page — and no trading words.
Run: python -m tests.test_alert_tones"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_at_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

NOW = datetime(2026, 10, 29, 3, 0, tzinfo=timezone.utc)
IDX = pd.bdate_range(end="2026-10-28", periods=400)


def _walk(seed, drift=0.0):
    rng = np.random.default_rng(seed)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(drift, 0.01, len(IDX)))), index=IDX)


class M:
    def __init__(self, ser, quotes):
        self.ser, self.quotes = ser, quotes

    def series(self, t):
        return self.ser.get(t, pd.Series(dtype=float))

    def q(self, t):
        return self.quotes.get(t)

    def sigma_move(self, t):
        x = self.quotes.get(t)
        return x.get("sg") if x else None


class E:
    pass


def test_momentum_and_green_sigma():
    from wsb.analytics import web_alerts as W
    ser = {"^GSPC": _walk(1), "^VIX": _walk(2)}
    sd = float(ser["^GSPC"].pct_change().dropna().iloc[-253:-1].std() * 100)
    e = E()
    e.market = M(ser, {"^GSPC": {"chg_pct": 2.5 * sd, "asof": "2026-10-28"}, "^VIX": {"chg_pct": -20.0, "asof": "2026-10-28", "sg": -3.5, "price": 15}})
    out = []
    W._momentum(e, out, NOW)
    assert out and out[0]["tone"] == "good" and out[0]["lv"] == "watch" and out[0]["key"].startswith("mom:^GSPC")
    class S(dict):
        def names(self):
            return {}
    orig = W.SETTINGS
    W.SETTINGS = S(alerts={"sigma_move": 3.0, "key_assets": ["^VIX"]})
    try:
        out2 = []
        W._vol(e, out2, NOW)
    finally:
        W.SETTINGS = orig
    vx = [x for x in out2 if x["key"].startswith("sigma:^VIX")]
    assert vx and vx[0]["tone"] == "good" and vx[0]["lv"] == "watch" and "好的方向" in vx[0]["zh"]   # VIX falling is not a red alarm


def test_dip_two_steps():
    from wsb.analytics import web_alerts as W
    s = _walk(3).copy()
    s.iloc[-8:-2] = s.iloc[-9] * np.cumprod([0.97] * 6)          # a sharp 6-day slide, then a bounce day
    s.iloc[-1] = s.iloc[-2] * 1.015
    v = pd.Series(18.0, index=IDX)
    v.iloc[-4] = 35.0
    v.iloc[-1] = 28.0
    e = E()
    e.market = M({"^GSPC": s, "^VIX": v}, {})
    out = []
    W._dip(e, out, NOW)
    assert [x["key"].split(":")[0] for x in out] == ["dip2"] and out[0]["tone"] == "good"


def test_patterns_capped_and_worded():
    from wsb.analytics import web_alerts as W
    e = E()
    e.signals = {"markets": {"us": {"rows": [{"sym": f"S{i}", "code": f"S{i}", "name": f"股{i}", "tier": "A", "strength": 90 - i, "new": True,
                                               "since": "2026-10-28", "inv": 10.0, "patterns": [{"pattern": "breakout", "label": "帶量突破"}]}
                                              for i in range(6)]}}}
    out = []
    W._patterns(e, out, NOW)
    assert len(out) == 3 and all(x["tone"] == "good" for x in out) and "失效線" in out[0]["zh"]
    for w in ("買點", "買進", "進場", "勝率"):
        assert all(w not in x["zh"] + x["detail"] for x in out)


def test_ribbon_on_page():
    from tools import site_alerts as A
    assert 'id="alrib"' in A.RIBBON_HTML and "ribbon(d)" in A.JS and "t-good" in A.CSS
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "build_site.py"), encoding="utf-8").read()
    assert "{SA.RIBBON_HTML}</header>" in src


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
