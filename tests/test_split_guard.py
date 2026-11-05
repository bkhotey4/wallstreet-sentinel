"""A split Yahoo has not adjusted yet (QUAL, MTUM, SOXX on 2026-11-05) must not read as a -75% crash.
Run: python -m tests.test_split_guard"""
from __future__ import annotations

import os
import sys
import tempfile

import numpy as np
import pandas as pd

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_split_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.data.market import MarketData, split_factor  # noqa: E402


def bars(values):
    return pd.Series(values, index=pd.bdate_range("2026-10-30", periods=len(values)), dtype=float)


def main():
    # the three real cases: the day's own move sits on top of the split
    assert split_factor(227.02, 55.95) == 4
    assert split_factor(272.86, 64.43) == 4
    assert split_factor(450.41, 136.44) == 3
    assert split_factor(10.0, 100.0) == -10
    # ordinary moves and a possible real crash stay untouched
    assert split_factor(150.55, 135.47) is None
    assert split_factor(100.0, 50.0) is None
    assert split_factor(100.0, 45.0) is None
    assert split_factor(0.0, 10.0) is None

    m = MarketData()
    idx = pd.bdate_range("2026-06-01", "2026-11-05")
    old = pd.Series(np.linspace(200, 227, len(idx)), index=idx)
    m.history = pd.DataFrame({"QUAL": old.iloc[:-1], "^SOX": old.iloc[:-1], "KLAC": old.iloc[:-1]})
    new = old.iloc[-5:].copy()
    new.iloc[-1] = new.iloc[-2] / 4 * 0.99
    crash = old.iloc[-5:].copy()
    crash.iloc[-1] = crash.iloc[-2] * 0.9
    recent = pd.DataFrame({"QUAL": new, "^SOX": new, "KLAC": crash})

    for _ in range(2):                                 # a second refresh of the same bars must not divide again
        fixed = m._unsplit(recent)
        m.history = m._merge(fixed)
    assert m.splits["QUAL"] == (4, "2026-11-05") and set(m.splits) == {"QUAL"}, m.splits
    s = m.series("QUAL")
    assert abs(s.iloc[-1] / s.iloc[-2] - 0.99) < 1e-6, "the move after the split is the real one"
    assert abs(s.iloc[0] / old.iloc[0] - 0.25) < 1e-6, "the whole history is on the new basis"
    assert m.series("^SOX").iloc[-1] < m.series("^SOX").iloc[-2] / 3, "an index has no splits"
    assert abs(fixed["KLAC"].iloc[-2] - crash.iloc[-2]) < 1e-9

    # Yahoo catches up: no jump left, and nothing moves a second time
    before = float(m.series("QUAL").iloc[0])
    m.history = m._merge(m._unsplit(pd.DataFrame({"QUAL": fixed["QUAL"]})))
    assert not m.splits and abs(float(m.series("QUAL").iloc[0]) - before) < 1e-9
    print("SPLIT GUARD TESTS PASSED")


if __name__ == "__main__":
    main()
