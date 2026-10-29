"""規則的歷史成績單: exit rules behave as defined, the 10,000-run simulation is reproducible, the card is plain and has
no trading-advice words.
Run: python -m tests.test_rule_sim"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rs_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import rule_sim as RS  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")


def test_exit_rules():
    c = np.array([100, 101, 97, 99, 103, 104] + [104] * 70, dtype=float)
    m20 = np.full(len(c), 98.0)
    assert RS._exit(c, m20, 0, 98.0, "hold20") == 20
    assert RS._exit(c, m20, 0, 98.0, "stop") == 2                     # 97 < 98
    up = np.array([100, 101, 103, 105] + [90] * 70, dtype=float)
    assert RS._exit(up, m20, 0, 98.0, "stop_tp") == 3                 # target 100 + 2×2 = 104 → 105 on day 3
    assert RS._exit(up, np.full(len(up), 102.0), 0, 50.0, "trail") == 1   # 101 < the 20-day line
    assert RS._exit(c[:10], m20, 0, 98.0, "hold20") is None           # not enough future bars


def _series(n_sym=12, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-10-16", periods=520)
    out = {}
    for s in range(n_sym):
        c = pd.Series(100 * np.cumprod(1 + rng.normal(0.0005, 0.02, len(idx))), index=idx)
        flag = pd.Series(rng.random(len(idx)) < 0.03, index=idx)
        df = pd.DataFrame({"flag": flag, "inv": c * 0.95, "close": c, "ma20": c.rolling(20).mean(), "ma200": c.rolling(200).mean()})
        out[f"S{s}"] = {"breakout": df, "pullback": df.assign(flag=False)}
    return out


def test_simulate_reproducible_and_plain():
    a = RS.simulate(_series(), 0.001)
    b = RS.simulate(_series(), 0.001)
    bo = a["patterns"]["breakout"]
    assert bo["n"] >= RS.MIN_N
    assert a["patterns"]["breakout"]["rules"] == b["patterns"]["breakout"]["rules"]          # fixed seed
    r = bo["rules"]["stop"]
    assert r["lo"] <= r["avg"] <= r["hi"] + 1e-9 and 0 <= r["seq_loss"] <= 100 and r["seq_mdd"] <= 0
    assert set(bo["rules"]["base"]) == {"avg", "lo", "hi"}
    assert "rules" not in a["patterns"].get("pullback", {})
    txt = RS.plain("帶量突破", bo)
    assert "1 萬次模擬" in txt and "失效線" in txt and "-" not in txt.split("虧")[1][:2]
    for w in BANNED:
        assert w not in txt


def test_card():
    from tools import site_quant as SQ

    class E:
        signals = {"available": True, "markets": {"us": {"rulesim": RS.simulate(_series(), 0.001)}}}
    h = SQ.sec_rule_sim(E())
    assert "1 萬次" in h and "倖存者偏差" in h and "隨機挑一檔" in h
    for w in BANNED:
        assert w not in h


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
