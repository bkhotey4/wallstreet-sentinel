"""移民與民意: poll cleaning and averaging (window widening), the migration reading and the data-driven story, the card.
Run: python -m tests.test_migration_polls"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import date

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_mig_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.data import migration_polls as MP  # noqa: E402


def poll(end, who, app, dis):
    return {"end_date": end, "pollster": who, "population": "rv", "sample_size": 1000, "url": "https://x.org/p",
            "answers": [{"choice": "Approve", "pct": app}, {"choice": "Disapprove", "pct": dis}]}


def test_polls():
    raw = [poll("2026-10-01", "A", 40, 55), poll("2026-10-20", "A", 42, 54), poll("2026-10-25", "B", 38, 58), {"bad": 1},
           poll("2026-09-01", "C", 44, 50), poll("2026-07-01", "D", 45, 50)]
    ps = MP.clean_polls(raw)
    assert len(ps) == 5
    a = MP.poll_avg(ps, date(2026, 11, 1))
    assert a["n"] == 3 and a["win"] == 90 and abs(a["app"] - (42 + 38 + 44) / 3) < 1e-9     # A's latest only; widened to reach 3
    r = MP.approval({"approval": ps}, date(2026, 11, 1))
    assert r["recent"][0]["end"] == "2026-10-25" and r["net"] < 0


def series(vals, start="2015-01-01"):
    return pd.Series(vals, index=pd.date_range(start, periods=len(vals), freq="MS"))


def test_migration():
    n = 60
    F = {MP.FB: series(np.linspace(30000, 29000, n)), MP.NB: series(np.linspace(130000, 131000, n)), MP.FB_U: series([4.0] * n),
         MP.NB_U: series([3.8] * n), "PAYEMS": series(np.linspace(150000, 152000, n)), MP.WAGE_ALL: series(np.linspace(30, 33, n)),
         "CES2000000003": series(np.linspace(30, 36, n)), "CES7000000003": series(np.linspace(20, 22, n))}
    m = MP.migration(F.get)
    assert m["fb_d"] < 0 and m["emoji"] == "🟡" and "營造業" in m["hot"]
    from tools import site_people as S
    assert "人變少" in S.story(m)
    up = dict(m, fb_d=500.0, nb_d=-800.0)
    t = S.story(up)
    assert "反而比一年前多" in t and "不支持" in t and "退休" in t
    eng = types.SimpleNamespace(_mig_view={"mig": m, "app": MP.approval({"approval": MP.clean_polls([poll("2026-10-20", "A", 42, 54)] * 1)}, date(2026, 11, 1))})
    h = S.sec_migration_polls(eng)
    assert 'id="migration"' in h and "一句話看懂" in h and "VoteHub" in h
    for w in ("目標價", "買進", "賣出", "低估", "高估"):
        assert w not in h, w


if __name__ == "__main__":
    test_polls()
    test_migration()
    print("MIGRATION POLLS TESTS PASSED [OK]")
