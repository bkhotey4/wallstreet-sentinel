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
