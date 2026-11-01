"""崩盤還是錯殺: the classes, a deep drop is measured against each stock's own usual move, the past uses only what was
public then, and the card has no trading words.
Run: python -m tests.test_drop_check"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_dc_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import drop_check as D  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "加碼參考區", "進場參考區")


def test_classify():
    assert D.classify({"label": "down", "s_accel": 1, "fcf_lv": 10}) == "weak"
    assert D.classify({"label": "flat", "s_accel": -1, "fcf_lv": -3}) == "weak"
    assert D.classify({"label": "up", "s_accel": 0, "fcf_lv": 8}) == "ok"
    assert D.classify({"label": "flat", "s_accel": 0, "fcf_lv": None, "nm_lv": 20}) == "ok"       # banks: net margin
    assert D.classify({"label": "flat", "s_accel": -1, "fcf_lv": 5}) == "check"


def _closes(n=40, weeks=300, crash=None):
    idx = pd.date_range("2020-11-02", periods=weeks, freq="W-MON")
    rng = np.random.default_rng(1)
    vol = np.linspace(0.02, 0.06, n)                                   # each stock its own usual move
    c = pd.DataFrame(100 * np.cumprod(1 + rng.normal(0.002, 1, (weeks, n)) * vol, axis=0), index=idx, columns=[f"S{i}" for i in range(n)])
    if crash:
        for s, k in crash.items():
            c.loc[c.index[-4:], s] *= np.linspace(1 - k / 4, 1 - k, 4)
    return c


def test_deep_uses_own_volatility():
    c = _closes(crash={"S0": 0.25, "S39": 0.12})
    r, sd, big = D.deep(c)
    assert bool(big["S0"].iloc[-1])                                   # calm stock, −25 %: deep
    assert not bool(big["S39"].iloc[-1])                              # wild stock, −12 %: normal for it


def test_history_uses_public_dates():
    c = _closes(crash={"S0": 0.25})
    q = [f"{y}Q{k}" for y in range(2019, 2027) for k in range(1, 5)][:-2]
    df = pd.DataFrame({"label": ["up"] * len(q), "s_accel": 0, "fcf_lv": 5.0, "nm_lv": 5.0, "g": 10.0, "accel": 0.0}, index=q)
    f = D.feats(df, 60)
    assert f.index[0] == pd.Timestamp("2019-05-15")                   # Q1 public 45 days after the quarter
    h = D.history(c, {s: f for s in c.columns})
    assert h["n"] > 0 and set(D.CLS) >= {k for k in h if k in D.CLS}
    cur = D.current(c, {s: f for s in c.columns}, {s: {"name": s, "ind": "科技"} for s in c.columns})
    assert cur and cur[0]["sym"] == "S0" and cur[0]["cls"] == "ok"


def test_card():
    from tools import site_drop as S
    assert S.sec_drop_check(None) in ("",) or "崩盤還是錯殺" in S.sec_drop_check(None)
    c = _closes(crash={"S0": 0.25})
    q = [f"{y}Q{k}" for y in range(2019, 2027) for k in range(1, 5)][:-2]
    df = pd.DataFrame({"label": ["down"] * len(q), "s_accel": -1, "fcf_lv": -2.0, "nm_lv": -1.0, "g": -5.0, "accel": -3.0}, index=q)
    fb = {"scored": {s: df for s in c.columns}, "metas": {s: {"name": s, "ind": "科技"} for s in c.columns}}
    m = D.build_market("us", fb, c)
    old = D.build
    D.build = lambda eng=None: {"markets": {"us": m}, "rates": {"chg": 35.0, "sd": 18.0, "z": 1.9, "y": 4.6}}
    try:
        h = S.sec_drop_check(None)
    finally:
        D.build = old
    assert "崩盤還是錯殺" in h and "利率急升" in h and "本業也在轉弱" in h
    for w in BANNED:
        assert w not in h


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
