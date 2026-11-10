"""Calendar CPI fallback: a release day with no actual gets the m/m change from the official index (FRED), only when the
index already has the month before the release month. Run: python -m tests.test_cpi_fill"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from wsb.analytics import macro_events as M  # noqa: E402


def ev():
    return {"key": "cpi", "date": "2026-11-10", "released": False,
            "rows": [{"label": "核心 CPI 月增", "a": None, "c": 0.2}, {"label": "CPI 月增", "a": None, "c": 0.3}]}


def test_fill():
    idx = pd.date_range("2026-08-01", periods=3, freq="MS")
    s = {"CPIAUCSL": pd.Series([334.131, 336.298, 337.476], index=idx), "CPILFESL": pd.Series([330.0, 331.0, 332.0], index=idx)}
    e = ev()
    assert M.fill_from_fred(e, s.get) and e["released"]
    assert e["rows"][1]["actual"] == "0.4%" and e["rows"][0]["actual"] == "0.3%" and e["rows"][0]["actual_src"] == "fred"
    stale = {k: v.iloc[:-1] for k, v in s.items()}               # FRED not updated yet → leave the card as a preview
    e2 = ev()
    assert not M.fill_from_fred(e2, stale.get) and not e2["released"]
    e3 = ev()                                                    # Nasdaq published the headline only (2026-11-10): fill the core row
    e3["released"] = True
    e3["rows"][1].update(a=0.4, actual="0.4%", diff=0.1)
    assert M.fill_from_fred(e3, s.get)
    assert e3["rows"][0]["actual_src"] == "fred" and e3["rows"][1].get("actual_src") is None and e3["rows"][1]["actual"] == "0.4%"


if __name__ == "__main__":
    test_fill()
    print("CPI FILL TESTS PASSED [OK]")
