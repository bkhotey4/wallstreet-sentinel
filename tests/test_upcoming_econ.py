"""upcoming.json carries the econ calendar's ★★+ releases (11-23: Thanksgiving-week PCE/GDP were on 總經 but not in the file)."""
from datetime import datetime
from types import SimpleNamespace

from tools import site_events as SE

NOW = datetime(2026, 11, 23, 10, 40, tzinfo=SE.TPE)


def _eng(avail=True):
    evs = [
        {"key": "pce", "zh": "PCE 物價", "imp": 3, "released": False, "utc": "2026-11-25T13:30:00Z"},
        {"key": "gdp", "zh": "GDP", "imp": 2, "released": False, "utc": "2026-11-25T13:30:00Z"},
        {"key": "claims", "zh": "初領", "imp": 1, "released": False, "utc": "2026-11-25T13:30:00Z"},      # below ★★
        {"key": "cpi", "zh": "CPI", "imp": 3, "released": True, "utc": "2026-11-13T13:30:00Z"},          # already out
        {"key": "nfp", "zh": "非農", "imp": 3, "released": False, "utc": "2026-12-04T13:30:00Z"},        # outside 7 days
        {"key": "fomc", "zh": "FOMC", "imp": 3, "released": False, "utc": "2026-11-26T19:00:00Z"},       # countdown gave it
        {"key": "ppi", "zh": "PPI", "imp": 2, "released": False},                                        # no time → skip
    ]
    return SimpleNamespace(econ_view={"available": avail, "events": evs})


def test_econ_items_window_and_dedupe():
    got = SE.econ_items(_eng(), NOW, 7, {("fomc", "2026-11-26")})
    assert [x["key"] for x in got] == ["pce", "gdp"], got
    assert got[0]["tpe"] == "2026-11-25 21:30" and got[0]["et"] == "2026-11-25T08:30" and got[0]["kind"] == "macro"


def test_econ_items_unavailable():
    assert SE.econ_items(_eng(False), NOW, 7, set()) == []
    assert SE.econ_items(SimpleNamespace(), NOW, 7, set()) == []


if __name__ == "__main__":
    test_econ_items_window_and_dedupe(); test_econ_items_unavailable()
    print("ok")
