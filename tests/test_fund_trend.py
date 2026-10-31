"""財報走向判斷: signals use only past data, banks need two signals, the forecast falls back to 'next = this quarter'
when the regression is not better, returns before the price history are skipped, and the card has no trading words.
Run: python -m tests.test_fund_trend"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ft_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import fund_trend as F  # noqa: E402
from wsb.analytics.stock_check import _qs  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "加碼參考區", "進場參考區")
QS = _qs("2026Q2", 60)


def _co(seed, drift=0.02, improve=False):
    rng = np.random.default_rng(seed)
    rev = 100 * np.cumprod(1 + drift + rng.normal(0, 0.02, len(QS)))
    gm = 0.4 + (np.linspace(0, 0.08, len(QS)) if improve else 0) + rng.normal(0, 0.005, len(QS))
    nm = 0.15 + (np.linspace(0, 0.08, len(QS)) if improve else 0) + rng.normal(0, 0.005, len(QS))
    p = {"rev": dict(zip(QS, rev)), "gp": dict(zip(QS, rev * gm)), "ni": dict(zip(QS, rev * nm)),
         "ocf": dict(zip(QS, rev * (nm + 0.05))), "capex": dict(zip(QS, rev * 0.04)), "name": f"CO{seed}"}
    if improve:                                                   # growth speeds up at the end
        for i, q in enumerate(QS[-6:]):
            for k in ("rev", "gp", "ni", "ocf", "capex"):
                p[k][q] *= 1 + 0.04 * (i + 1)
    return p


def test_signals_and_labels():
    df = F.score(F.panel(_co(1, improve=True)))
    assert df["label"].iloc[-1] == "up" and df["n_sig"].iloc[-1] == 4
    b = F.score(F.panel({k: v for k, v in _co(2).items() if k in ("rev", "ni", "name")}, bank=True), bank=True)
    assert b["n_sig"].iloc[-1] == 2 and b["label"].iloc[-1] is not None


def test_forecast_and_track():
    panels = {f"S{i}": F.panel(_co(i)) for i in range(12)}
    m = F.forecast_model(panels)
    assert m and m["rmse"] > 0 and (m["model"] or m["b"] is None)
    if not m["model"]:
        assert F.predict(m, 12.0, 3.0) == 12.0
    idx = pd.date_range("2020-10-26", periods=320, freq="W-MON")
    px = {s: pd.Series(100 * np.cumprod(1 + np.random.default_rng(i).normal(0.002, 0.03, len(idx))), index=idx) for i, s in enumerate(panels)}
    t = F.track({s: F.score(df) for s, df in panels.items()}, px)
    for lab in ("up", "flat", "down"):
        r = t.get(lab) or {}
        if r.get("from"):
            assert r["from"] >= "2020Q3"                              # no return before the prices start


def test_card_plain():
    from tools import site_stockcheck as S
    h = S.sec_fund_trend(None)                                        # empty cache → nothing, no crash
    assert h == "" or "財報走向判斷" in h
    r = {"name": "X", "label": "down", "g": 5.0, "accel": -3.0, "gm": None, "nm": -1.0, "fcf": 0.5, "next_g": 5.0}
    txt = F.plain(r, "某公司", {"model": False, "rmse": 9.0})
    assert "轉弱中" in txt and "放慢 3.0" in txt and "若維持本季速度" in txt and "±9" in txt
    for w in BANNED:
        assert w not in txt + F.watch({"s_accel": -1}, False)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
