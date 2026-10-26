"""即時層: the strip tiles carry their ticker, the live bar/JS ship on the page, and the rules are well formed.
Run: python -m tests.test_live"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_live_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_live as SL  # noqa: E402


def test_rules_and_js():
    for r in SL.RULES:
        assert r["op"] in (">=", "<=") and r["f"] in ("lvl", "chg", "ratio") and r["zh"] and r["en"]
        assert r["sym"] in SL.EXTRA and (r["f"] != "ratio" or r["den"] in SL.EXTRA)
    assert "__RULES__" not in SL.JS and "api/quote" in SL.JS and "^VIX3M" in SL.JS
    assert 'id="lqbar" hidden' in SL.bar_html()


def test_anomaly_scan():
    import json
    import types
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2025-06-01", periods=300)
    h = pd.DataFrame({"^GSPC": 100 * np.cumprod(1 + rng.normal(0, 0.01, 300)), "JPY=X": [150.0] * 300}, index=idx)
    sig = SL.sigmas(types.SimpleNamespace(market=types.SimpleNamespace(history=h)))
    assert 0.8 < sig["^GSPC"] < 1.2 and "JPY=X" not in sig            # flat series: no normal move to compare against
    assert SL.sigmas(None) == {} and len(SL.EXTRA) <= 25                 # one /api/quote request carries every symbol
    bar = SL.bar_html(types.SimpleNamespace(market=types.SimpleNamespace(history=h)))
    assert "data-sig=" in bar and json.dumps(sig).replace('"', "&quot;") in bar and 'id="lqan"' in bar
    assert all(a[0] in SL.EXTRA for a in SL.ANOM) and all(v[3] in ("up", "down") for v in SL.VOLS)
    keys = {a[0] for a in SL.ANOM} | {b[0] for b in SL.BASKETS}
    for k, zh, en, lv, why, legs in SL.COMBOS:                          # every leg points at a market the scan measures
        assert lv in (-1, 0, 1, 2) and zh and en and why and legs and all(s in keys and op in (">=", "<=") for s, op, _z in legs), k
    assert {c[3] for c in SL.COMBOS} >= {-1, 0, 1, 2} and all(s in keys for s in SL.BAD_UP + SL.NEUTRAL)
    assert "往好的方向" in SL.JS and "沒有壓力訊號" in SL.JS
    assert len({c[0] for c in SL.COMBOS}) == len(SL.COMBOS) and "組合訊號" in SL.JS and "sd1y" in SL.JS
    assert "ES=F" in SL.JS and "&vol=" in SL.JS and "異常波動掃描" in SL.JS and "大量賣壓" in SL.JS


def test_lookup_card():
    h = SL.sec_lookup(None)
    assert "一句話看懂" in h and 'id="lqf"' in h and "pages.dev" in h and "不是投資建議" in h


def test_strip_tiles_tagged():
    import types
    import pandas as pd
    from tools import build_site as B
    s = pd.Series([1.0, 2.0], index=pd.to_datetime(["2026-10-22", "2026-10-23"]))
    eng = types.SimpleNamespace(market=types.SimpleNamespace(q=lambda t: None, series=lambda t: s))
    h = B.sec_strip(eng)
    assert 'data-lq="^VIX"' in h and 'data-dg="2"' in h and 'id="lqbar"' in h


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
