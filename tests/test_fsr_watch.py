"""官方點名的四個壓力點: report-name fallback, FDIC parsing, the four readings and their lights, the card.
Run: python -m tests.test_fsr_watch"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import date

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_fsr_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.data import fsr_watch as F  # noqa: E402


def qs(n, start="2003-03-31"):
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(start, periods=n, freq="QE")]


def test_quarters():
    assert F.quarters(date(2026, 11, 8))[:3] == ["2026Q3", "2026Q2", "2026Q1"]
    assert F.quarters(date(2026, 2, 1))[0] == "2025Q4"
    assert F._qdate("26:Q2") == "2026-06-30" and F._qdate("bad") is None


def test_readings():
    ds = qs(60, "2010-03-31")
    js = {"data": [{"data": {"REPDTE": d.replace("-", ""), "sum_SCHA": 1000, "sum_SCHF": 1000 - i, "sum_SCAA": 1000, "sum_SCAF": 1000,
                             "sum_EQ": 1000, "sum_DEPUNINS": 400, "sum_DEP": 1000}} for i, d in enumerate(ds)]}
    rows = F.parse_fdic(js)
    b = F.banks(rows)
    assert b["ratio"] < -5 and b["emoji"] == "🟡" and abs(b["unins"] - 40) < 1e-9          # loss grows every quarter → worst in history
    d = qs(54, "2013-03-31")
    hf = {"gav": [[x, 3 + i * 0.1] for i, x in enumerate(d)], "nav": [[x, 1.0] for x in d]}
    assert F.hedge(hf, 95)["emoji"] == "🟡" and F.hedge(hf, 50)["emoji"] == "🟢"
    q = qs(94)
    hh = {f"flow:{c}": {x: (1 + i / 50) for i, x in enumerate(q)} for c, _ in F.LOANS}
    hh.update({f"stock:{c}": {x: 1.0 for x in q} for c, _ in F.LOANS})
    h = F.household(hh, "2026Q2")
    assert h["emoji"] == "🟡" and "車貸" in h["hot"]
    idx = pd.date_range("1987-01-01", periods=480, freq="MS")
    r = F.rent_ratio({F.HPI: pd.Series(np.linspace(60, 300, 480), index=idx), F.RENT: pd.Series(np.linspace(100, 200, 480), index=idx)}.get)
    assert r["pct"] == 100 and r["emoji"] == "🟡"
    v = {"hedge": F.hedge(hf, 95), "house": h, "bank": b, "rent": r}
    assert len(F.alerts(v)) == 4
    from tools import site_stability as S
    eng = types.SimpleNamespace(_fsr_view=v)
    out = S.sec_st_fsr(eng)
    assert "未實現" not in out                          # the public-page holdings guard blocks this word
    assert 'id="st-fsr"' in out and "一句話看懂" in out and "紐約聯準會" in out
    for w in ("目標價", "買進", "賣出", "低估", "高估"):
        assert w not in out, w


if __name__ == "__main__":
    test_quarters()
    test_readings()
    print("FSR WATCH TESTS PASSED [OK]")
