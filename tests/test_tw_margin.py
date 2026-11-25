"""追繳線與證交所措施（2026-11-25）。Run: python -m tests.test_tw_margin"""
import re
from pathlib import Path

from wsb.data import tw_margin as M
from wsb.data import tw_preopen as P

U = "https://www.twse.com.tw/zh/about/news/news/content.html?x"
ROWS = [{"Title": "自115年11月24日起，信用交易擔保維持率最低標準由130%調降至120%", "Url": U + "1", "Date": "1151123"},
        {"Title": "9家上市公司法說會展現獲利成長與營運韌性", "Url": U + "2", "Date": "1151123"},
        {"Title": "自116年3月2日起，信用交易擔保維持率最低標準由120%調升至130%", "Url": U + "3", "Date": "1160226"}]


def test_floor():
    n = M.parse_news(ROWS)
    assert [r["date"] for r in n] == ["2027-02-26", "2026-11-23"] and n[0]["by"] == "證交所"
    assert M.floor_on("2026-11-23", []) == 130 and M.floor_on("2026-11-24", []) == 120
    assert M.floor_on("2027-03-01", n) == 120 and M.floor_on("2027-03-02", n) == 130      # restored by an official title
    assert M.parse_news("bad") == []


def test_void_calendar():
    tw = [["2026-11-19", 100.0], ["2026-11-20", 93.0], ["2026-11-23", 95.0], ["2026-11-24", 100.0], ["2026-11-25", 95.0]]
    cal = P.call_calendar(["2026-11-20", "2026-11-25"], tw, {}, {})
    assert [c["void"] for c in cal] == [True, False]
    assert not M.voided("2026-11-16", "2026-11-19")                                      # already over, not cancelled


def test_ratio_same_day():
    from wsb.data import tw_chips as C
    mg = {"date": "20261124", "tables": [{"data": [["融資金額(仟元)", "0", "0", "0", "0", "1,000"]]}, {"data": [["2330", "x", "", "", "", "", "1"]]}]}
    px = lambda day: [{"Date": day, "Code": "2330", "ClosingPrice": "1620"}]      # noqa: E731
    r = C.margin_ratio(mg, px("1151124"))
    assert r["ratio"] == 162.0 and r["px_date"] == "20261124"
    assert C.margin_ratio(mg, px("1151123")) is None                                     # two different days are never combined


def test_unfinished_session():
    from datetime import datetime
    ds = ["2026-11-24", "2026-11-25"]
    assert P.closed_days(ds, datetime(2026, 11, 25, 10, 30)) == ds[:1]
    assert P.closed_days(ds, datetime(2026, 11, 25, 14, 0)) == ds


def test_no_typed_floor():
    for f in ("tools/site_twpreopen.py", "tools/site_tw_chips.py", "tools/sec_push.py"):
        assert not re.search(r"低於 1[123]0%", (Path(__file__).resolve().parents[1] / f).read_text(encoding="utf-8")), f


def test_push_without_floor():
    from tools import sec_push as S
    p = {"mratio": 160.0, "mg": {}}
    assert "160%" in S.twal_embed({"kind": "pre", "p": p, "due": []})["description"]
    assert "低於 120%" in S.twal_embed({"kind": "pre", "p": {**p, "floor": 120}, "due": []})["description"]


if __name__ == "__main__":
    test_floor(); test_void_calendar(); test_no_typed_floor(); test_push_without_floor(); test_ratio_same_day(); test_unfinished_session(); print("ok")
