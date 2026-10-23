"""學術研究 page: the dated review renders (sections, tables, links), the status card, and the Wilson intervals on the
crisis record.  Run: python -m tests.test_research"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rs_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_research as R  # noqa: E402
from wsb.analytics.crisis_track import wilson  # noqa: E402


def main():
    secs = R.sections()
    assert len(secs) >= 5 and secs[-1][0] == "結論", [t for t, _ in secs]
    h = R.sec_research(None)
    assert h.count('<section class="card') == len(secs) and "<table" in h and 'target="_blank"' in h and R.COMPILED in h
    assert "**" not in h and "](http" not in h                       # markdown fully converted
    st = R.sec_research_status(None)
    assert "落實進度" in st and "尚未" in st and "已完成" in st
    lo, hi = wilson(7, 7)
    assert 60 < lo < 70 and hi == 100.0
    lo, hi = wilson(11, 48)
    assert 12 < lo < 15 and 35 < hi < 38
    assert wilson(0, 0) == (None, None)
    print("all research tests passed")


if __name__ == "__main__":
    main()
