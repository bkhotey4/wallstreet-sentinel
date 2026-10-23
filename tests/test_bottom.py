"""抄底四訊號: CNN archive merge, signal evaluation (incl. stale data), episode counting, back-test, site card, bell.
Run: python -m tests.test_bottom"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import date, datetime, timezone

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_bt_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import bottom as BT  # noqa: E402


def ms(d):
    return datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000


def test_archive():
    js = {"fear_and_greed_historical": {"data": [{"x": ms("2026-10-20"), "y": 12.0}, {"x": ms("2026-10-21"), "y": 8.0}]},
          "put_call_options": {"data": [{"x": ms("2026-10-20"), "y": 0.85}, {"x": ms("2026-10-21"), "y": 0.95}]},
          "fear_and_greed": {"score": 7.5, "timestamp": "2026-10-22T14:00:00+00:00"}}
    a = BT.archive(js)
    assert a["fg"] == {"2026-10-20": 12.0, "2026-10-21": 8.0, "2026-10-22": 7.5} and a["pc"]["2026-10-21"] == 0.95
    a2 = BT.archive({"fear_and_greed_historical": {"data": [{"x": ms("2026-10-23"), "y": 9.0}]}})
    assert len(a2["fg"]) == 4 and a2["pc"]["2026-10-20"] == 0.85             # merged, nothing lost
    print("ok archive")


def test_episodes():
    idx = pd.bdate_range("2020-01-01", periods=60)
    m = pd.Series(False, index=idx)
    m.iloc[[5, 6, 7, 15, 40]] = True                                       # 5-7 and 15 are one wave; 40 is a new one
    e = BT.episodes(m, 20)
    assert list(e) == [idx[5], idx[40]], e
    print("ok episodes")


class Mkt:
    def __init__(self, d, q):
        self.d, self._q = d, q

    def series(self, t):
        return self.d.get(t, pd.Series(dtype=float))

    def q(self, t):
        return self._q.get(t)


def eng_fixture(vix_now=45.0):
    idx = pd.bdate_range(end="2026-10-22", periods=3000)
    spx = pd.Series(np.linspace(1000, 3000, len(idx)), index=idx)
    vix = pd.Series(18.0, index=idx)
    for start in (800, 1600, 2400):                                       # three crashes: VIX > 40, RSI < 30
        spx.iloc[start:start + 15] = np.linspace(spx.iloc[start], spx.iloc[start] * 0.75, 15)
        spx.iloc[start + 15:] = spx.iloc[start + 15:] * 0.75 / 1.0 + 0
        vix.iloc[start + 8:start + 15] = 45.0
    spx.iloc[-15:] = np.linspace(spx.iloc[-16], spx.iloc[-16] * 0.8, 15)  # now: falling hard
    vix.iloc[-1] = vix_now
    q = {"^VIX": {"price": vix_now, "asof": "2026-10-22"}}
    return types.SimpleNamespace(market=Mkt({"^GSPC": spx, "^VIX": vix}, q),
                                 crypto=types.SimpleNamespace(data={"cnn_fng": 7.5}))


def test_build():
    e = eng_fixture()
    r = BT.build(e, today=date(2026, 10, 26))
    by = {s["k"]: s for s in r["signals"]}
    assert by["vix"]["hit"] and by["rsi"]["hit"] and by["fg"]["hit"], by
    assert by["pc"]["v"] == 0.95 and by["pc"]["stale"] and not by["pc"]["hit"]    # archive's last P/C is 10-21 → stale by 10-26
    r2 = BT.build(e, today=date(2026, 10, 22))
    assert {s["k"] for s in r2["signals"] if s["hit"]} == {"fg", "vix", "rsi", "pc"} and r2["level"] == "all", r2["signals"]
    assert r2["bt"]["both"]["n"] >= 3 and r2["bt"]["both"]["3m"]["n"] >= 3 and r2["bt"]["both"]["further"] <= 0
    calm = BT.build(eng_fixture(vix_now=15.0), today=date(2026, 10, 22))
    assert not {s["k"]: s for s in calm["signals"]}["vix"]["hit"] and calm["n_hit"] == 3
    print("ok build")
    return e


def test_site_and_bell(e):
    from tools import site_bottom as SBT
    h = SBT.sec_bottom(e)
    assert "抄底四訊號" in h and "/ 4" in h and "RSI" in h and "之後再跌" in h
    assert "不是預測，也不是買賣建議" in h
    from wsb.analytics import web_alerts as WA
    out = []
    WA._bottom(e, out, datetime(2026, 10, 22, tzinfo=timezone.utc))
    assert out and out[0]["key"].startswith("bottom:") and out[0]["tab"] == "mood"
    print("ok site / bell")


if __name__ == "__main__":
    test_archive()
    test_episodes()
    test_site_and_bell(test_build())
    print("all bottom tests passed")
