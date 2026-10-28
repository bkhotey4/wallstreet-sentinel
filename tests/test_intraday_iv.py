"""盤中細項: holdings intraday parse (same-time volume, VWAP, last three bars), the owner-DM rule, rate-adjusted credit
betas for the site, and the new live combos.
Run: python -m tests.test_intraday_iv"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_iv_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

DAY0 = 1790000000 - 1790000000 % 86400 + 14 * 3600 + 1800        # 14:30 UTC session start


def _res(today_px, today_vol, n_days=21, now_bar=True):
    ts, c, h, lo, v = [], [], [], [], []
    for d in range(n_days):
        for k in range(78):
            ts.append(DAY0 + d * 86400 + k * 300)
            c.append(100.0)
            h.append(100.05)
            lo.append(99.95)
            v.append(1000.0)
    base = DAY0 + n_days * 86400
    for k, (p, vol) in enumerate(zip(today_px, today_vol)):
        ts.append(base + k * 300)
        c.append(p)
        h.append(p + 0.05)
        lo.append(p - 0.05)
        v.append(vol)
    return {"meta": {"gmtoffset": 0}, "timestamp": ts, "indicators": {"quote": [{"close": c, "high": h, "low": lo, "volume": v}]}}, ts[-1]


def test_parse_weak_and_recover():
    from wsb.data import intraday as IV
    px = [100, 99.8, 99.6, 99.4, 99.2, 99.0, 98.8, 98.7]
    res, t = _res(px, [3000] * len(px))
    r = IV.parse(res, now=t + 60)
    assert r and abs(r["rvol"] - 3.0) < 1e-9 and r["below3"] and not r["above3"] and r["chg"] < 0
    assert IV.parse(res, now=t + 3600) is None                       # no fresh bar → that market is not trading now
    from wsb.bot.app import Sentinel
    b = Sentinel.__new__(Sentinel)
    al = b._holdings_iv_alerts({"NVDA": r})
    assert len(al) == 1 and al[0].key.startswith("iv_pf:NVDA:") and al[0].key.endswith(":weak")
    from wsb import store
    assert store.is_private_alert(al[0].key)
    up = [99.0, 98.0, 97.0, 99.5, 100.5, 101.0, 101.5, 102.0]
    res2, t2 = _res(up, [3000] * len(up))
    r2 = IV.parse(res2, now=t2 + 60)
    assert r2["above3"]
    assert not b._holdings_iv_alerts({"NVDA": r2})                    # no earlier "weak" today → no recovery note
    store.alert_mark(al[0].key, "ℹ️ INFO", "t")
    r2["t"] = r["t"]
    rec = b._holdings_iv_alerts({"NVDA": r2})
    assert rec and rec[0].key.endswith(":recover")


def test_credit_betas_and_combos():
    from tools import site_live as L
    idx = pd.bdate_range("2025-01-01", periods=300)
    rng = np.random.default_rng(3)
    ief_r = rng.normal(0, 0.4, 300) / 100
    hyg_r = 0.35 * ief_r + rng.normal(0, 0.3, 300) / 100
    h = pd.DataFrame({"IEF": 100 * np.cumprod(1 + ief_r), "HYG": 80 * np.cumprod(1 + hyg_r)}, index=idx)

    class M:
        history = h

    class E:
        market = M()
    cb = L.credit_betas(E())
    assert abs(cb["HYG"]["b"] - 0.35) < 0.12 and 0.2 < cb["HYG"]["sd"] < 0.4 and "LQD" not in cb
    keys = {c[0]: c for c in L.COMBOS}
    assert [l[0] for l in keys["credit_first"][5]] == ["cr_hy", "^GSPC"] and "divfail" in keys and "credit_both" in keys
    assert "data-cr=" in L.bar_html(E()) and "ivScan" in L.JS and "&iv=" in L.JS


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
