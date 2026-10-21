"""產業體檢: TTM pairs and balances from companyfacts, stale-flow guard, strain rules, theme roll-up, site cards.
Run: python -m tests.test_industry"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ind_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.data import fundamentals as FU  # noqa: E402


def fy(tag_vals, unit="USD"):
    return {"units": {unit: tag_vals}}


def flow(s, e, v, filed="2026-08-01"):
    return {"start": s, "end": e, "val": v, "filed": filed, "form": "10-K"}


def inst(e, v, filed="2026-08-01"):
    return {"end": e, "val": v, "filed": filed, "form": "10-K"}


def cf():
    """A company with two fiscal years: capex grew past cash flow, inventory piled up, debt doubled,
    construction in progress jumped; operating income stopped being tagged in 2015 (must not be mixed in)."""
    g = {
        "Revenues": fy([flow("2024-07-01", "2025-06-30", 100e9), flow("2025-07-01", "2026-06-30", 110e9)]),
        "NetCashProvidedByUsedInOperatingActivities": fy([flow("2024-07-01", "2025-06-30", 40e9), flow("2025-07-01", "2026-06-30", 45e9)]),
        "PaymentsToAcquirePropertyPlantAndEquipment": fy([flow("2024-07-01", "2025-06-30", 30e9), flow("2025-07-01", "2026-06-30", 60e9)]),
        "OperatingIncomeLoss": fy([flow("2014-04-01", "2015-03-31", 5e9)]),
        "InterestExpense": fy([flow("2024-07-01", "2025-06-30", 1e9), flow("2025-07-01", "2026-06-30", 2e9)]),
        "InventoryNet": fy([inst("2025-06-30", 10e9), inst("2026-06-30", 16e9)]),
        "AccountsReceivableNetCurrent": fy([inst("2025-06-30", 10e9), inst("2026-06-30", 16e9)]),
        "ConstructionInProgressGross": fy([inst("2025-06-30", 10e9), inst("2026-06-30", 40e9)]),
        "PropertyPlantAndEquipmentGross": fy([inst("2025-06-30", 100e9), inst("2026-06-30", 150e9)]),
        "LongTermDebt": fy([inst("2025-06-30", 20e9), inst("2026-06-30", 40e9)]),
    }
    return {"facts": {"us-gaap": g}}


def main():
    p = FU.parse(cf())
    assert p["end"] == "2026-06-30" and p["rev"]["v"] == 110e9 and p["rev"]["prev"] == 100e9
    assert p["ebit"] == {"stale": "2015-03-31"}                         # never paired with 2026 interest
    m = FU.metrics(p)
    assert abs(m["capex_ocf"] - 60 / 45) < 1e-9 and abs(m["capex_ocf_prev"] - 0.75) < 1e-9 and m["gap"] == 15e9
    assert abs(m["cip_share"] - 40 / 150 * 100) < 1e-9 and abs(m["cip_share_prev"] - 10.0) < 1e-9
    assert abs(m["inv_minus_rev"] - (60 - 10)) < 1e-9                  # inventory +60 % vs revenue +10 %
    assert abs(m["dso"] - 16 / 110 * 365) < 1e-9 and m["dso"] - m["dso_prev"] > 15
    assert m["int_burden"] is None and not m["ebit_negative"]          # operating income not disclosed → not scored
    assert abs(m["debt_growth"] - 100) < 1e-9
    assert set(FU.flags(m)) == {"gap", "cip", "inv", "dso", "debt"}
    # tiny inventory relative to sales is not "inventory building"
    small = cf()
    small["facts"]["us-gaap"]["InventoryNet"] = fy([inst("2025-06-30", 1e8), inst("2026-06-30", 3e8)])
    assert FU.metrics(FU.parse(small))["inv_minus_rev"] is None
    # roll-up and transmission
    from wsb.analytics import sector_health as SH
    rows = [{"sym": "AAA", "name": "A", "theme": "AI", "m": m, "flags": FU.flags(m)},
            {"sym": "BBB", "name": "B", "theme": "AI", "m": {**m, "capex_ocf": 0.5, "capex_ocf_prev": 0.4, "ocf_negative": False},
             "flags": ["dso"]}]
    th = SH.by_theme(rows)
    assert th[0]["theme"] == "AI" and th[0]["flags"]["gap"] == 1 and th[0]["cover"]["gap"] == 2 and th[0]["names"]["dso"] == ["AAA", "BBB"]
    eng = types.SimpleNamespace(stress=types.SimpleNamespace(blocks={"信用": 70}), market=types.SimpleNamespace(series=lambda t: __import__("pandas").Series(dtype=float)))
    tr = SH.transmission(rows, eng)
    assert tr["gap_now"] == 1 and tr["gap_prev"] == 0 and tr["rising_gap"] and tr["tight_credit"] and tr["on"]
    # site cards
    from tools import site_industry as SI
    eng.sector_health = {"available": True, "ledger": rows[:1], "rows": rows, "themes": th, "transmission": tr, "periods": ("2026-06-30", "2026-06-30")}
    html = SI.sec_ai_ledger(eng) + SI.sec_transmission(eng) + SI.sec_themes_health(eng) + SI.sec_company_health(eng)
    assert "AI 基礎建設帳本" in html and "1.33×" in html and "融資傳導條件成立" in html and "族群體質" in html and "AAA" in html
    print("INDUSTRY TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
