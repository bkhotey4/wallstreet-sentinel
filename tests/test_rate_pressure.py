"""利率壓力鏈: mortgage payment math, the four links and the worst-link pick, the card.
Run: python -m tests.test_rate_pressure"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rp_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.data import rate_pressure as R  # noqa: E402


def test_view_and_card():
    assert abs(R.payment(7.0) - 1995.9) < 1
    d = pd.bdate_range("2020-01-01", periods=1500)
    up = pd.Series(np.linspace(3, 5, 1500), index=d)
    mid = pd.Series(np.r_[np.linspace(5, 7, 1000), np.linspace(7, 6, 500)], index=d)          # mortgage and credit not at their worst
    fred = {"DGS10": up, "MORTGAGE30US": mid, "BAMLH0A0HYM2": mid - 3, "BAMLC0A0CM": pd.Series(1.0, index=d)}
    flat = pd.Series(100.0, index=d)
    falling = pd.Series(np.r_[np.full(1400, 100.0), np.linspace(100, 50, 100)], index=d)
    R.FILE.write_text(json.dumps({"neo": {s: {k.strftime("%Y-%m-%d"): v for k, v in falling.items()} for s in R.NEO}}), encoding="utf-8")
    px = {"^GSPC": flat, "^NDX": flat, "XHB": flat, "BIZD": flat}
    v = R.view(fred.get, px.get)
    keys = [l["key"] for l in v["links"]]
    assert keys == ["rate", "home", "credit", "ai"] and v["worst"]["key"] == "ai"
    from tools import site_rates as S
    h = S.sec_rate_pressure(types.SimpleNamespace(_rate_pressure=v))
    assert 'id="ratepress"' in h and "一句話看懂" in h and 'class="cchain"' in h
    for w in ("目標價", "買進", "賣出", "低估", "高估", "未實現"):
        assert w not in h, w


if __name__ == "__main__":
    test_view_and_card()
    print("RATE PRESSURE TESTS PASSED [OK]")
