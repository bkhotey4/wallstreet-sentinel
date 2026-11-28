"""TDCC 集保戶股權分散表 (11-28): parse levels, weekly change, big holders selling while small holders grow.
Run: python -m tests.test_tw_holders"""
from wsb.analytics import macro_map as M  # noqa: F401  (imports must work together)
from wsb.data import tw_holders as T
from wsb.data import ust_auctions as U

CSV = chr(10).join(["﻿資料日期,證券代號,持股分級,人數,股數,占集保庫存數比例%",
                    "20261127,2330  ,1,2788390,332366639,1.28", "20261127,2330  ,2,485989,929925651,3.58",
                    "20261127,2330  ,15,1464,21808829716,84.09", "20261127,2330  ,17,3381152,25932370067,100.00",
                    "20261127,000218,15,1,422278902,100.00"])


def test_parse_and_changes():
    snap = T.parse(CSV)
    x = snap["20261127"]["2330"]
    assert x == {"big_pct": 84.09, "small_pct": 4.86, "small_n": 3274379, "holders": 3381152} and "000218" not in snap["20261127"]
    d = T.merge({}, {"20261120": {"2330": {"big_pct": 84.5, "small_pct": 4.7, "small_n": 3200000, "holders": 3300000}}})
    d = T.merge(d, snap)
    c = T.changes(d)[0]
    assert c["code"] == "2330" and c["d_big"] == -0.41 and c["d_small_n"] == 74379


def test_auctions_parse():
    rows = [{"securityType": "Bill", "securityTerm": "13-Week", "issueDate": "2026-12-03T00:00:00"},
            {"securityType": "Note", "securityTerm": "9-Year 11-Month", "announcementDate": "2026-12-03T00:00:00",
             "issueDate": "2026-12-15T00:00:00", "offeringAmount": "39000000000", "reopening": "Yes"}]
    a = U.parse(rows)
    assert len(a) == 1 and a[0]["amount_b"] == 39.0 and a[0]["reopen"] and a[0]["issue"] == "2026-12-15"


if __name__ == "__main__":
    test_parse_and_changes()
    test_auctions_parse()
    print("ok tw holders / auctions")
