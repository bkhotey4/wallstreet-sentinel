"""SCFI composite (11-26): parse both weeks, merge history by date, week-over-week change, stock move window.
Run: python -m tests.test_freight"""
import pandas as pd

from tools import site_freight as S
from wsb.data import freight as F

JS = {"data": {"currentDate": "2026-11-20", "lastDate": "2026-11-13", "lineDataList": [
    {"dataItemTypeName": "SCFI_T", "currentContent": 3503.7828, "lastContent": 3572.3268},
    {"dataItemTypeName": "SCFI_L1", "currentContent": None, "lastContent": None}]}}


def test_parse_merge_change():
    pts = F.parse(JS)
    assert pts == [["2026-11-13", 3572.3268], ["2026-11-20", 3503.7828]]
    h = F.merge([["2026-11-13", 3500.0]], pts)                  # the newer reading of the same week wins
    assert h == pts and round(S.change(h, 1), 2) == -1.92 and S.change(h, 4) is None


def test_week_move():
    idx = pd.to_datetime(["2026-11-12", "2026-11-13", "2026-11-19", "2026-11-20"])
    c = pd.DataFrame({"2603.TW": [200.0, 200.0, 190.0, 196.0]}, index=idx)
    assert round(S.week_move(c, "2603.TW", "2026-11-13", "2026-11-20"), 1) == -2.0
    assert S.week_move(c, "2609.TW", "2026-11-13", "2026-11-20") is None


if __name__ == "__main__":
    test_parse_merge_change()
    test_week_move()
    print("ok freight")
