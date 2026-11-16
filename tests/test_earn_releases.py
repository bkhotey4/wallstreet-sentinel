"""財報新聞稿原文：候選名單、申報篩選、附件挑選、HTML 轉文字，不連網。Run: python -m tests.test_earn_releases"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wsb.data import earn_releases as ER  # noqa: E402


def test_pieces():
    days = {"2026-11-17": {"rows": [{"sym": "NVDA", "mcap": 4e12}, {"sym": "TINY", "mcap": 1e9}]},
            "2026-11-10": {"rows": [{"sym": "OLD", "mcap": 1e12}]}}
    assert [c["sym"] for c in ER.candidates(days, "2026-11-18")] == ["NVDA"]
    assert [c["sym"] for c in ER.candidates(days, "2026-11-18", extra=["TINY"])] == ["NVDA", "TINY"]
    js = {"filings": {"recent": {"form": ["8-K", "8-K", "6-K", "10-Q"], "items": ["2.02,9.01", "5.02", "", ""],
                                 "filingDate": ["2026-11-17", "2026-11-16", "2026-11-15", "2026-11-17"],
                                 "accessionNumber": ["a", "b", "c", "d"], "primaryDocument": ["x.htm"] * 4}}}
    assert [f["acc"] for f in ER.recent_filings(js, "2026-11-14")] == ["a", "c"]
    idx = {"directory": {"item": [{"name": "nvda-8k.htm", "size": "9000"}, {"name": "q3fy27pr-ex991.htm", "size": "50000"}]}}
    assert ER.pick_exhibit(idx) == "q3fy27pr-ex991.htm"
    assert ER.pick_exhibit({"directory": {"item": [{"name": "a.htm", "size": "10"}, {"name": "b.htm", "size": "99"}]}}) == "b.htm"
    assert ER.pick_exhibit({"directory": {"item": [{"name": "d264008d6k.htm", "size": "9000"}]}}, "6-K") is None   # cover only
    t = ER.to_text("<html><style>x{}</style><p>Revenue&nbsp;was $57.0 billion</p><p>up 62%</p></html>")
    assert t == "Revenue was $57.0 billion\nup 62%"


if __name__ == "__main__":
    test_pieces()
    print("ok test_pieces")
