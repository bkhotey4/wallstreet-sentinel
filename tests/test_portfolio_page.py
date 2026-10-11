"""我的持股 tab: public data only, holdings never server-side, safe JSON embedding.  Run: python -m tests.test_portfolio_page"""
from __future__ import annotations

import json
import os
import re
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_pf_page_"))

from tools import site_portfolio as SP  # noqa: E402


def main():
    quotes = {"TWD=X": {"price": 32.0, "chg_pct": 0.1, "asof": "2026-10-09"},
              "SPY": {"price": 600.0, "chg_pct": -1.0, "asof": "2026-10-09"},
              "BAD": {"price": float("nan"), "chg_pct": None, "asof": ""},
              "EVIL</script>": {"price": 1.0, "chg_pct": 0.0, "asof": "x"}}
    mk = types.SimpleNamespace(quotes=quotes, q=lambda t: quotes.get(t), series=lambda t: __import__("pandas").Series(dtype=float))
    eng = types.SimpleNamespace(market=mk, holdings={"NVDA": {"shares": 15}}, portfolio={"positions": [{"sym": "NVDA"}]})
    html = SP.sec_portfolio(eng)
    m = re.search(r'<script type="application/json" id="pf-data">(.*?)</script>', html, re.S)
    data = json.loads(m.group(1))                                       # the only server-provided data
    assert set(data) == {"fx", "q"}
    assert data["fx"]["USD"] == 32.0 and abs(data["fx"]["HKD"] - 32.0 / 7.8) < 1e-9
    assert "SPY" in data["q"] and "BAD" not in data["q"]                 # NaN prices skipped
    assert "</script>" not in m.group(1)                                 # cannot break out of the JSON block
    assert "NVDA" not in m.group(1) and "15" not in json.dumps(data["fx"])  # engine holdings never embedded
    assert "localStorage" in SP.JS and "fetch('market/'" in SP.JS
    # the only network calls are GETs of the public price files — no POST/beacon/query strings carrying holdings
    assert not re.search(r"method\s*:\s*['\"]POST|sendBeacon|XMLHttpRequest|fetch\([^)]*\?", SP.JS)
    assert "innerHTML" not in SP.JS                                      # names from data are set via textContent
    from tools import build_site as B
    src = open(B.__file__, encoding="utf-8").read()
    assert '("portfolio", "我的持股", "My holdings", [SP.sec_portfolio])' in src and "{SP.JS}" in src and "{SP.CSS}" in src
    print("PORTFOLIO PAGE TESTS PASSED ✅")


if __name__ == "__main__":
    main()
