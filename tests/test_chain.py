"""AI 產業鏈連動: chip-crash windows and the market-relative contagion table, down-day linkage (incl. the Taipei next-session
alignment), the card and tile.  Run: python -m tests.test_chain"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ch_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import ai_chain as AC  # noqa: E402


def _ff():
    months = pd.date_range("1970-01-01", periods=600, freq="MS")
    chips = np.full(600, 0.01)
    for s in (100, 250, 400):                      # three 50 % chip crashes, then recoveries
        chips[s:s + 12] = -0.06
        chips[s + 12:s + 40] = 0.05
    gold = np.where(chips < 0, 0.02, 0.0)
    banks = np.where(chips < 0, -0.05, 0.01)
    mk = lambda a: {f"{m:%Y-%m}": float(x) for m, x in zip(months, a)}  # noqa: E731
    return {"Chips": mk(chips), "Gold": mk(gold), "Banks": mk(banks), "Food ": mk(np.full(600, 0.005))}


def test_contagion():
    ff = _ff()
    eps = AC.chip_crashes(ff)
    assert len(eps) == 3 and all(e["fall"] <= -0.35 for e in eps)
    c = AC.contagion(ff)
    names = [r["ind"] for r in c["rows"]]
    assert names[0] in ("Banks", "Chips") and names[-1] == "Gold" and c["rows"][-1]["worse"] == 0


def test_chain_now_and_card():
    idx = pd.bdate_range("2024-06-03", periods=520)
    rng = np.random.default_rng(4)
    sox_r = rng.normal(0, 0.02, len(idx))
    sox = pd.Series(np.cumprod(1 + sox_r) * 100, index=idx)
    mu = pd.Series(np.cumprod(1 + 1.5 * sox_r) * 100, index=idx)          # 1.5× the SOX move
    xlu = pd.Series(np.cumprod(1 + rng.normal(0, 0.005, len(idx))) * 100, index=idx)
    tw_r = np.r_[0.0, 0.8 * sox_r[:-1]]                                   # Taipei answers the next session
    tsmc = pd.Series(np.cumprod(1 + tw_r) * 100, index=idx)
    close = pd.DataFrame({"MU": mu, "2330.TW": tsmc})
    e = types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: {"^SOX": sox, "XLU": xlu}.get(t, pd.Series(dtype=float)), q=lambda t: None),
                              stockprices=types.SimpleNamespace(close=close))
    now = AC.chain_now(e)
    by = {m["sym"]: m["beta"] for g in now["groups"] for m in g["members"]}
    assert abs(by["MU"] - 1.5) < 0.05 and abs(by["2330.TW"] - 0.8) < 0.1 and by["XLU"] < 0.3
    assert now["groups"][0]["zh"] == "記憶體"
    from tools import site_chain as SCH
    h = SCH.sec_ai_chain(e)
    assert 'id="ai-chain"' in h and "下跌連動度" in h and "回到重點" in h and SCH.tile(e)[0] == "ai-chain"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
