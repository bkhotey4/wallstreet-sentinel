"""我的持股 tab: public data only, holdings never server-side, safe JSON embedding.  Run: python -m tests.test_portfolio_page"""
from __future__ import annotations

import json
import os
from pathlib import Path
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
    assert set(data) == {"fx", "q", "gcid", "hist", "earn", "crisis", "beta", "sym", "rules"}   # public data only
    assert set(data["rules"]) <= {"cfg", "ssi", "sym", "dz", "surp", "gb"}      # rule inputs per public symbol, no holdings
    assert set(data["sym"]) == {"beta", "vol"}
    for bad in ("600:(addSym", "w * 1.1", "found.b : 1.1", "stopPct = 0.10", "建議分批減碼", "千億美元", ": 1.0; }"):
        assert bad not in SP.JS, bad                                   # no invented prices / betas / advice
    assert data["earn"] == [] and data["crisis"] == {} and data["beta"] == {}  # no data in this fixture → nothing invented
    assert "b: 1.65" not in SP.JS and "Beta 0.15" not in SP.JS
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
    # earnings radar and crisis replay come from data, not hard-coded tables
    assert "noteZh" not in SP.JS and "move: 6.5" not in SP.JS and "semi: 0.62" not in SP.JS
    import pandas as pd
    idx = pd.bdate_range("2007-01-01", "2025-01-01")
    base = pd.Series(range(len(idx)), index=idx, dtype=float) + 100.0
    crash = base.copy(); crash.loc["2020-02-20":"2020-03-23"] = base.loc["2020-02-19"] * 0.66
    hist = types.SimpleNamespace(quotes={}, q=lambda t: None, series=lambda t: crash if t == "^GSPC" else pd.Series(dtype=float))
    cr = SP._crisis(types.SimpleNamespace(market=hist))
    import numpy as np
    rng = np.random.default_rng(1)
    mret = pd.Series(rng.normal(0, 0.01, len(idx)), index=idx)
    spx = (1 + mret).cumprod() * 100
    sox = (1 + 2 * mret).cumprod() * 100                                     # exactly twice the market's moves
    bm = types.SimpleNamespace(series=lambda t: {"^GSPC": spx, "^SOX": sox}.get(t, pd.Series(dtype=float)))
    be = SP._beta(types.SimpleNamespace(market=bm))
    assert set(be) == {"semi"} and 1.8 < be["semi"] < 2.2, be
    assert abs(cr["covid2020"]["shocks"]["other"] - 0.34) < 1e-3 and "semi" not in cr["covid2020"]["shocks"]
    ev = SP._earn(types.SimpleNamespace(techearn={"calendar": {"up": [{"sym": "NVDA", "name": "Nvidia", "date": "2026-11-19", "time": "after"}]}},
                                        sx={"earn": [{"sym": "NVDA", "date": "2026-11-19", "mv": 7.1, "avg": 6.0}]}))
    assert ev == [{"sym": "NVDA", "name": "Nvidia", "date": "2026-11-19", "time": "after", "mv": 7.1, "avg": 6.0}]
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
    # Google sync safety, run on the real page JS (Node): an empty device or an empty Drive never erases holdings,
    # an explicit 清除全部 still propagates, the replaced version is kept, Drive history can be restored
    import shutil, subprocess, tempfile as _tf
    from tools import site_portfolio as _SP
    node = shutil.which("node")
    if node:
        js = Path(_tf.mkdtemp()) / "pf.js"
        js.write_text(_SP.JS, encoding="utf-8")
        sim = Path(__file__).with_name("js") / "pf_sync_sim.js"
        r = subprocess.run([node, str(sim), str(js)], capture_output=True, text=True, encoding="utf-8", timeout=120)
        assert r.returncode == 0 and "ALL SIM PASS" in r.stdout, r.stdout[-2000:] + r.stderr[-2000:]
    else:
        print("node not installed: sync simulation skipped")
    print("PORTFOLIO PAGE TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
