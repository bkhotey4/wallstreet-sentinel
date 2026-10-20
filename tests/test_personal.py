"""我的持股（私人）: event radar, data checks, today's P&L split — pure functions, no network.
Run: python -m tests.test_personal"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_pers_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.analytics import personal as P  # noqa: E402


def test_events():
    w = {"GOOG": 9.6, "KLAC": 27.9, "TSM": 20.4, "NU": 5.4}
    cal = [{"sym": "GOOGL", "date": "2026-10-28", "time": "after"},      # other share class still matches GOOG
           {"sym": "KLAC", "date": "2026-11-04"},                        # beyond 14 days → left out
           {"sym": "NU", "date": "2026-10-22", "time": "pre"},
           {"sym": "XYZ", "date": "2026-10-22"}]                         # not held → left out
    ev = [{"key": "fomc", "zh": "FOMC", "date": "2026-10-28", "imp": 3, "released": False, "tpe": "10/29 02:00"},
          {"key": "pce", "zh": "PCE", "date": "2026-10-29", "imp": 3, "released": False},
          {"key": "ppi", "zh": "PPI", "date": "2026-10-23", "imp": 2, "released": False},   # below the importance bar
          {"key": "cpi", "zh": "CPI", "date": "2026-10-21", "imp": 3, "released": True}]     # already out
    r = P.events(w, cal, ev, date(2026, 10, 20), days=14, macro_min_imp=3)
    ds = {d["date"]: d for d in r["days"]}
    assert set(ds) == {"2026-10-22", "2026-10-28", "2026-10-29"}, ds
    assert ds["2026-10-28"]["stacked"] and [x["kind"] for x in ds["2026-10-28"]["items"]] == ["macro", "earn"]
    assert ds["2026-10-28"]["items"][1]["sym"] == "GOOG" and ds["2026-10-28"]["items"][1]["weight"] == 9.6
    assert not ds["2026-10-22"]["stacked"]
    assert r["n_earn"] == 2 and r["n_macro"] == 2 and abs(r["earn_weight"] - 15.0) < 1e-9
    assert r["busiest"]["date"] == "2026-10-28"
    assert P.events({}, cal, [], date(2026, 10, 20))["days"] == []


def test_sanity():
    rows = [{"sym": "TSM", "cost": 339.84, "price": 417.4, "chg_pct": 1.2, "asof": "2026-10-19", "market": "us"},   # fine (1.2×)
            {"sym": "TYPO", "cost": 39.98, "price": 417.4, "chg_pct": 1.2, "asof": "2026-10-19", "market": "us"},  # 10× off
            {"sym": "SPLIT", "cost": 100, "price": 52, "chg_pct": -50.0, "asof": "2026-10-19", "market": "us"},
            {"sym": "OLD", "cost": 10, "price": 10, "chg_pct": 0, "asof": "2026-10-10", "market": "us"},
            {"sym": "NOPX", "cost": 10, "price": None, "market": "us"},
            {"sym": "SMR", "cost": 8.885, "price": 5.76, "chg_pct": -1.2, "asof": "2026-10-19", "market": "us"}]       # a real loss, not a typo
    out = P.sanity(rows, {"us": "2026-10-19"})
    codes = {(i["sym"], i["code"]) for i in out}
    assert codes == {("TYPO", "cost_far"), ("SPLIT", "jump"), ("OLD", "stale"), ("NOPX", "no_price")}, codes
    assert all(i["zh"] and i["en"] for i in out)


def test_split():
    # 10 shares 100 → 110 while USD/TWD 32.0 → 32.32 (+1%), plus 1,000 USD cash; a TWD stock 50 → 55 × 1000
    rows = [{"shares": 10, "price": 110.0, "chg_pct": 10.0, "currency": "USD"},
            {"shares": 1000, "price": 55.0, "chg_pct": 10.0, "currency": "TWD"},
            {"shares": 5, "price": 20.0, "chg_pct": None, "currency": "USD"}]
    s = P.day_split(rows, 32.32, 1.0, usd_cash=1000)
    fx0 = 32.32 / 1.01
    assert abs(s["price"] - (10 * 10 * fx0 + 1000 * 5)) < 1e-6
    assert abs(s["fx"] - (10 * 110 * (32.32 - fx0) + 1000 * (32.32 - fx0))) < 1e-6
    assert abs(s["total"] - ((10 * 110 * 32.32 - 10 * 100 * fx0) + 5000 + 1000 * (32.32 - fx0))) < 1e-6   # adds up exactly
    assert s["missing"] == 1
    assert P.day_split(rows, None, 1.0) is None
    assert P.day_split(rows, 32.0, None)["fx"] == 0                      # no rate change known → all price


def main():
    test_events()
    test_sanity()
    test_split()
    print("PERSONAL TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
