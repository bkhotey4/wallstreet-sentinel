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
    import types
    import pandas as pd
    eng = types.SimpleNamespace(stress=types.SimpleNamespace(score=62.0),
                                fred=types.SimpleNamespace(get=lambda k: pd.Series(dtype=float)),
                                market=types.SimpleNamespace(series=lambda k: pd.Series(dtype=float)))
    h = R.sec_research(eng)
    assert h.count("隱含意義") == len(R.POINTS) == 6 and "<details" in h and R.COMPILED in h
    assert h.index("學界的眼光看現在的市場") < h.index("判讀依據") and "附錄" not in h
    full = R.md_html("x [a](https://e.org) **b**")
    assert 'target="_blank"' in full and "<b>b</b>" in full                # the review renderer still works
    now = R.now_reading(eng)
    assert now[0][0].startswith("即時層") and "偏高" in now[0][1] and now[-1][0] == "合起來怎麼看", now
    st = R.sec_research_status(None)
    assert "落實進度" in st and "尚未" in st and "已完成" in st
    lo, hi = wilson(7, 7)
    assert 60 < lo < 70 and hi == 100.0
    lo, hi = wilson(11, 48)
    assert 12 < lo < 15 and 35 < hi < 38
    assert wilson(0, 0) == (None, None)
    import json
    R.FEED = __import__("pathlib").Path(os.environ["WSB_DATA_DIR"]) / "feed.json"
    R.FEED.write_text(json.dumps({"items": [
        {"title": "Paper A", "url": "https://example.org/a", "summary": "重點 A", "implication": "意義 A", "source": "Fed", "added": "2026-10-26"},
        {"title": "Bad <script>", "url": "javascript:alert(1)", "summary": "x"},
        {"title": "Paper B", "url": "https://example.org/b", "summary": "重點 B <b>", "added": "2026-11-02"}]}), encoding="utf-8")
    f = R.sec_research_feed(None)
    assert "Paper A" in f and "Paper B" in f and "javascript:" not in f and "&lt;b&gt;" in f and f.index("Paper B") < f.index("Paper A")
    R.FEED.write_text("not json", encoding="utf-8")
    assert R.sec_research_feed(None) == ""
    print("all research tests passed")


if __name__ == "__main__":
    main()
