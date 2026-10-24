"""第二意見與傳導管道: OFR stress index bands and the SSI cross-check, foreign official custody, yen carry, cards.
Run: python -m tests.test_transmission"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_tr_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.data import transmission as TR  # noqa: E402

IDX = pd.bdate_range("2005-01-03", "2026-10-21")


def _spx():
    rng = np.random.default_rng(7)
    return pd.Series(np.cumprod(1 + rng.normal(0.0003, 0.011, len(IDX))) * 100, index=IDX)


def _fsi_csv(last: float) -> str:
    rng = np.random.default_rng(8)
    v = np.clip(np.cumsum(rng.normal(0, 0.15, len(IDX))), -4, 8)
    v[-1] = last
    head = "Date,OFR FSI,Credit,Equity valuation,Safe assets,Funding,Volatility,United States\n"
    return head + "\n".join(f"{d:%Y-%m-%d},{x:.3f},{x / 3:.3f},{x / 5:.3f},0.1,0.1,0.1,{x / 2:.3f}" for d, x in zip(IDX, v))


def test_fsi():
    f = TR.parse_fsi(_fsi_csv(-1.9))
    assert f["dates"][0] == "2005-01-03" and len(f["OFR FSI"]) == len(IDX) and "Credit" in f
    v = TR.fsi_view({"fsi": f}, _spx(), ssi=63)
    assert v["band"] == "壓力低" and sum(r["now"] for r in v["rows"]) == 1 and v["vs_ssi"].startswith("分歧")
    assert all(r["n"] >= 0 for r in v["rows"]) and 0 < v["base"] < 100
    v2 = TR.fsi_view({"fsi": TR.parse_fsi(_fsi_csv(6))}, _spx(), ssi=40)
    assert v2["band"] == "壓力很高" and v2["vs_ssi"].startswith("分歧")


def test_custody():
    w = pd.date_range("2010-01-06", periods=800, freq="7D")
    vals = np.r_[np.linspace(2.0e6, 3.1e6, 600), np.linspace(3.1e6, 2.5e6, 200)]
    v = TR.custody_view({"custody": {d.strftime("%Y-%m-%d"): float(x) for d, x in zip(w, vals)}})
    assert v["chg52"] < 0 and v["state"] in ("減持", "撤離加速") and abs(v["peak"] - 3.1) < 0.01


def test_yen():
    days = pd.bdate_range("1995-01-02", "2026-10-16")
    j = pd.Series(np.linspace(100, 158, len(days)), index=days)
    d = {"jpy": {k.strftime("%Y-%m-%d"): float(x) for k, x in j.items()},
         "yen_cftc": [[f"2020-{i:03d}", 10.0] for i in range(150)] + [["2026-10-20", 15.0]]}
    v = TR.yen_view(d, _spx())
    assert v["pct10y"] > 90 and not v["carry_big"] and "做多日圓" in v["state"]
    d["yen_cftc"] = [[f"2020-{i:03d}", 10.0] for i in range(150)] + [["2026-10-20", -30.0]]
    assert TR.yen_view(d, _spx())["carry_big"]


def test_cards():
    from tools import site_transmission as STR
    TR._save({"fsi": TR.parse_fsi(_fsi_csv(-1.9)), "custody": {d.strftime("%Y-%m-%d"): 2.6e6 - i * 1000 for i, d in enumerate(pd.date_range("2010-01-06", periods=800, freq="7D"))},
              "jpy": {k.strftime("%Y-%m-%d"): 150.0 for k in pd.bdate_range("1995-01-02", "2026-10-16")}})
    e = types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: _spx() if t == "^GSPC" else pd.Series(dtype=float)),
                              stress=types.SimpleNamespace(score=63))
    for f, anchor, word in ((STR.sec_tr_fsi, "st-fsi", "什麼是 OFR"), (STR.sec_tr_custody, "st-custody", "什麼是託管美債"), (STR.sec_tr_yen, "st-yen", "什麼是日圓套利")):
        h = f(e)
        assert f'id="{anchor}"' in h and word in h and "回到重點" in h and "不是投資建議" in h, anchor
    t = STR.tiles(e)
    assert [x[0] for x in t] == ["st-fsi", "st-custody", "st-yen"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
