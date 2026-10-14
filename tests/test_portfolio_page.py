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
    assert set(data) == {"fx", "q", "gcid"}                               # fx, public quotes, Google client id (public)
    assert data["gcid"] == "" or data["gcid"].endswith(".apps.googleusercontent.com")
    assert data["fx"]["USD"] == 32.0 and abs(data["fx"]["HKD"] - 32.0 / 7.8) < 1e-9
    assert "SPY" in data["q"] and "BAD" not in data["q"]                 # NaN prices skipped
    assert "</script>" not in m.group(1)                                 # cannot break out of the JSON block
    assert "NVDA" not in m.group(1) and "15" not in json.dumps(data["fx"])  # engine holdings never embedded
    assert "localStorage" in SP.JS and "fetch('market/'" in SP.JS
    # no USD/TWD quote anywhere → no invented rate: fx is None and the page says 匯率缺
    nofx = types.SimpleNamespace(quotes={}, q=lambda t: None, series=lambda t: __import__("pandas").Series(dtype=float))
    html0 = SP.sec_portfolio(types.SimpleNamespace(market=nofx, holdings={}, portfolio={}))
    d0 = json.loads(re.search(r'id="pf-data">(.*?)</script>', html0, re.S).group(1))
    assert d0["fx"]["USD"] is None and d0["fx"]["HKD"] is None and "31.5" not in html0
    assert "匯率缺" in SP.JS and "FXOK" in SP.JS
    # the only network calls are GETs of the public price files — no POST/beacon/query strings carrying holdings
    # the page may talk to exactly two hosts: the site itself (relative URLs) and Google (the user's own Drive app
    # folder + the sign-in script); never anything else, never beacons / XHR
    hosts = {re.match(r"https?://([^/'\"]+)", u).group(1) for u in re.findall(r"https?://[^'\"\s]+", SP.JS)}
    assert hosts == {"www.googleapis.com", "accounts.google.com"}, hosts
    assert not re.search(r"sendBeacon|XMLHttpRequest", SP.JS)
    assert "drive.appdata" in SP.JS and "appDataFolder" in SP.JS                  # app-private Drive folder only
    assert "innerHTML" not in SP.JS                                      # names from data are set via textContent
    from tools import build_site as B
    src = open(B.__file__, encoding="utf-8").read()
    assert '("portfolio", "我的持股", "My holdings", [SP.sec_portfolio])' in src and "{SP.JS}" in src and "{SP.CSS}" in src
    print("PORTFOLIO PAGE TESTS PASSED ✅")


if __name__ == "__main__":
    main()
