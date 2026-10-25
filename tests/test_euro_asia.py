"""歐洲與亞洲: ECB CISS parsing and bands, sovereign spreads vs Germany, Asian equities, the two cards.
Run: python -m tests.test_euro_asia"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ea_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.data import euro_asia as EA  # noqa: E402


def _data():
    days = pd.bdate_range("2000-01-03", "2026-10-22")
    ciss = {d.strftime("%Y-%m-%d"): float(0.05 + 0.3 * (1990 < i < 2300)) for i, d in enumerate(days)}
    months = [f"{y}-{m:02d}" for y in range(1999, 2027) for m in range(1, 13) if f"{y}-{m:02d}" <= "2026-09"]
    de = {m: 2.0 for m in months}
    fr = {m: 2.3 + (0.8 if m >= "2026-04" else 0.0) for m in months}                  # France widening to a record at the end
    it = {m: 3.0 if "2011-01" <= m <= "2012-12" else 2.6 for m in months}
    return {"ciss": ciss, "yields": {"DE": de, "FR": fr, "IT": it}}


def _eng():
    idx = pd.bdate_range("2000-01-03", "2026-10-23")
    rng = np.random.default_rng(9)
    spx = pd.Series(np.cumprod(1 + rng.normal(0.0003, 0.011, len(idx))) * 100, index=idx)
    ks = pd.Series(np.r_[np.linspace(100, 200, len(idx) - 22), np.linspace(200, 150, 22)], index=idx)
    return types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: {"^GSPC": spx, "^KS11": ks, "EUFN": spx}.get(t, pd.Series(dtype=float))))


def test_parse_and_europe():
    txt = "KEY,TIME_PERIOD,OBS_VALUE,OTHER\nx,2026-10-21,0.0213,a\nx,2026-10-22,0.021,a\n"
    assert EA.parse_ciss(txt) == {"2026-10-21": 0.0213, "2026-10-22": 0.021}
    e = EA.europe(_data(), _eng().market.series("^GSPC"))
    assert e["ciss"]["band"] == "低" and sum(r["now"] for r in e["ciss"]["rows"]) == 1
    fr = next(x for x in e["spreads"] if x["code"] == "FR")
    assert fr["pct"] >= 90 and abs(fr["spread"] - 1.1) < 1e-9 and [x["code"] for x in e["hot"]] == ["FR"]


def test_cards():
    from tools import site_euro_asia as SE
    d = _data()
    EA.FILE.write_text(json.dumps(d), encoding="utf-8")
    e = _eng()
    h = SE.sec_europe(e)
    assert "一句話看懂" in h and "法國公債比德國多付" in h and "歐洲銀行股" in h and "不是投資建議" in h
    a = SE.sec_asia(e)
    assert "韓國綜合" in a and "記憶體" in a and "歐洲銀行股" not in a


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
