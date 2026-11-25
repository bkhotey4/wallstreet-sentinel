"""Oil futures roll guard (wsb/data/rolls.py + MarketData.q / series).  Run: python -m tests.test_rolls"""
from __future__ import annotations

import math
import os
import sys
from datetime import date

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.data import rolls as R   # noqa: E402


def test_calendar():
    assert R.expiries("BZ=F", 2026)[9] == date(2026, 10, 30) and R.expiries("CL=F", 2026)[9] == date(2026, 10, 20)
    assert R.near_expiry("BZ=F", date(2026, 10, 26)) and not R.near_expiry("BZ=F", date(2026, 11, 9))
    assert R.near_expiry("CL=F", date(2026, 11, 16)) and not R.near_expiry("CL=F", date(2026, 11, 4))
    assert not R.near_expiry("GC=F", date(2026, 10, 26))


def test_roll_day():
    assert R.is_roll_day("BZ=F", date(2026, 10, 26), -5.83, -0.9)          # 2026-10-26: contract gap, WTI barely moved
    assert not R.is_roll_day("BZ=F", date(2026, 10, 26), -1.2, -0.9)       # normal day near expiry
    assert not R.is_roll_day("BZ=F", date(2026, 11, 4), -8.68, -2.0)       # big move, but nowhere near expiry
    assert not R.is_roll_day("BZ=F", date(2026, 10, 26), float("nan"), -0.9)


def test_adjust_removes_the_gap():
    idx = pd.to_datetime(["2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27"])
    bz = pd.Series([116.0, 116.5, 116.72, 109.91, 110.5], index=idx)
    cl = pd.Series([100.0, 100.4, 100.6, 99.7, 100.2], index=idx)
    a = R.adjust(bz, cl, "BZ=F")
    assert a.iloc[-1] == 110.5 and a.iloc[-2] == 109.91                       # today and the roll day keep their prices
    assert abs((a.iloc[3] / a.iloc[2] - 1) - (99.7 / 100.6 - 1)) < 1e-9      # roll-day return = WTI's
    assert abs(a.iloc[1] / a.iloc[0] - 116.5 / 116.0) < 1e-12                # other returns untouched


def test_market_q_and_series():
    from wsb.data.market import MarketData
    m = MarketData.__new__(MarketData)
    idx = pd.to_datetime(["2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26"])
    m.history = pd.DataFrame({"BZ=F": [116.0, 116.5, 116.72, 109.91], "CL=F": [100.0, 100.4, 100.6, 99.7]}, index=idx)
    m.quotes = {"BZ=F": {"price": 109.91, "prev": 116.72, "chg_pct": -5.83, "asof": "2026-10-26"},
                "CL=F": {"price": 99.7, "prev": 100.6, "chg_pct": -0.89, "asof": "2026-10-26"}}
    q = m.q("BZ=F")
    assert q["roll"] and math.isnan(q["chg_pct"]) and q["price"] == 109.91
    assert not m.q("CL=F").get("roll") and m.q("CL=F")["chg_pct"] == -0.89
    s = m.series("BZ=F")
    assert abs((s.iloc[-1] / s.iloc[-2] - 1) * 100 - (99.7 / 100.6 - 1) * 100) < 1e-9


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
