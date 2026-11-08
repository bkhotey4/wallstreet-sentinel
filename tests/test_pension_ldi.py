"""退休金與長天期公債: BoE / ECB parsing, the 3-day / 20-day light rules, alerts and the site card.
Run: python -m tests.test_pension_ldi"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ldi_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.data import pension_ldi as PL  # noqa: E402


def calm(n=3000, seed=1):
    idx = pd.bdate_range("2010-01-01", periods=n)
    rng = np.random.default_rng(seed)
    return pd.Series(4 + np.cumsum(rng.normal(0, 0.03, n)), index=idx)


def test_parse():
    boe = "DATE,IUDLNPY,IUDMNPY\n" + "\n".join(f"{d.strftime('%d %b %Y')},{4 + i / 1e4},{3 + i / 1e4}"
                                               for i, d in enumerate(pd.bdate_range("2015-01-01", periods=1200)))
    u = PL.parse_boe(boe)
    assert len(u["long"]) == 1200 and u["long"]["2015-01-01"] == 4.0
    ecb = "KEY,TIME_PERIOD,OBS_VALUE\nx,2026-10-26,3.5\nx,2026-10-27,3.6\n"
    assert PL.parse_ecb(ecb) == {"2026-10-26": 3.5, "2026-10-27": 3.6}


def test_rules():
    s = calm()
    r = PL.market("uk", s, s - 0.3)
    assert r["emoji"] in ("🟢", "🟡") and abs(r["slope"] - 30) < 1e-6
    hot = s.copy()
    hot.iloc[-3:] = hot.iloc[-4] + np.array([0.3, 0.7, 1.1])          # +110bp in 3 days, the 2022 kind of move
    r = PL.market("uk", hot, hot - 0.3)
    assert r["emoji"] == "🔴" and r["c3"] > 100 and r["max3_date"] == hot.index[-1].strftime("%Y-%m-%d")
    r["zh"], r["tenor"] = "英國", "20 年"
    a = PL.alerts({"rows": [r]})
    assert len(a) == 1 and a[0][0] == f"ldi:uk:{r['date']}" and "被迫賣債" in a[0][3]
    assert PL.market("uk", s.iloc[:100], s.iloc[:100]) is None        # too short to judge


def test_card():
    from tools import site_stability as S
    s = calm()
    rows = [dict(PL.market(k, s, s - 0.2), zh=zh, tenor=t, short="10 年", who=w) for k, zh, t, _st, w in PL.MARKETS]
    eng = types.SimpleNamespace(_ldi_view={"rows": rows}, _stability_view={})
    h = S.sec_st_ldi(eng)
    assert 'id="st-ldi"' in h and "一句話看懂" in h and "2022" in h and "荷蘭" in h and "250bp" in h
    for w in ("目標價", "買進", "賣出", "低估", "高估"):
        assert w not in h, w
    assert S.ldi_lead([dict(rows[0], emoji="🔴", state="急升", c3=120.0, p3=99.9)]).startswith("英國 20 年公債 3 天 +120bp")


if __name__ == "__main__":
    test_parse()
    test_rules()
    test_card()
    print("PENSION LDI TESTS PASSED [OK]")
