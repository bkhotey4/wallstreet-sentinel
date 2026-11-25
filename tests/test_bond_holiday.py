"""US bond-market holidays (SIFMA) for Treasury yields: wsb/data/exchange_cal.us_bond_closed + MarketData.q / series.
Run: python -m tests.test_bond_holiday"""
from __future__ import annotations

import math
import os
import sys
from datetime import date
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.data import exchange_cal as X  # noqa: E402


def test_calendar():
    c26 = X.us_bond_closed(2026, 2026)
    assert c26["2026-11-11"] == "退伍軍人節" and c26["2026-10-12"] == "哥倫布日"      # stocks open, bonds closed
    assert c26["2026-04-03"] == "耶穌受難日" and c26["2026-07-03"] == "獨立紀念日"    # July 4 on Saturday → Friday
    assert c26["2026-11-26"] == "感恩節" and "2026-11-27" not in c26
    c27 = X.us_bond_closed(2027, 2027)
    assert c27["2027-01-18"] == "金恩紀念日" and c27["2027-12-24"] == "聖誕節"          # Christmas on Saturday → Friday
    assert "2023-11-10" not in X.us_bond_closed(2023, 2023)                            # Veterans Day on Saturday: Friday open
    assert not X.bond_open(date(2026, 11, 11)) and X.bond_open(date(2026, 11, 12)) and not X.bond_open(date(2026, 11, 14))


def _market():
    from wsb.data.market import MarketData
    m = MarketData.__new__(MarketData)
    idx = pd.to_datetime(["2026-11-06", "2026-11-09", "2026-11-10", "2026-11-11"])
    m.history = pd.DataFrame({"^TNX": [4.90, 4.86, 4.98, 4.998], "^GSPC": [7377.0, 7550.0, 7600.0, 7620.0]}, index=idx)
    return m


def test_quote_on_the_holiday():
    m = _market()
    m.quotes = {"^TNX": {"price": 4.998, "prev": 4.98, "chg_pct": 0.36, "asof": "2026-11-11"},
                "^GSPC": {"price": 7620.0, "prev": 7600.0, "chg_pct": 0.26, "asof": "2026-11-11"}}
    q = m.q("^TNX")
    assert q["bond_closed"] == "退伍軍人節" and q["asof"] == "2026-11-10" and q["price"] == 4.98 and math.isnan(q["chg_pct"]), q
    assert not m.q("^GSPC").get("bond_closed") and m.q("^GSPC")["chg_pct"] == 0.26          # stocks traded
    assert list(m.series("^TNX").index.strftime("%Y-%m-%d")) == ["2026-11-06", "2026-11-09", "2026-11-10"]
    assert len(m.series("^GSPC")) == 4


def test_day_after_measures_from_the_real_close():
    m = _market()
    m.quotes = {"^TNX": {"price": 5.10, "prev": 4.998, "chg_pct": 2.04, "asof": "2026-11-12"}}
    q = m.q("^TNX")
    assert not q.get("bond_closed") and q["prev"] == 4.98 and abs(q["chg_pct"] - (5.10 / 4.98 - 1) * 100) < 1e-9   # ≈ +12bp, not +10bp


def test_treasury_note_for_ai():
    from wsb.data import treasury as TR
    m = _market()
    m.quotes = {"^TNX": {"price": 4.998, "prev": 4.98, "chg_pct": 0.36, "asof": "2026-11-11"}}
    bc = TR.bond_closed(SimpleNamespace(market=m))
    assert bc == {"name": "退伍軍人節", "date": "2026-11-11", "last_date": "2026-11-10"}, bc
    lines = TR.summary_lines({"available": True, "curves": {"now": []}, "spreads": {}, "bond_closed": bc})
    assert any("債市休市" in x and "2026-11-10" in x for x in lines), lines


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
