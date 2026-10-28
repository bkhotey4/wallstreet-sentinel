"""財報後白話解讀 card: renders the routine's JSON (any sector), folds details, filters tech for 科技財報, never shows
trading words.  Run: python -m tests.test_after"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_card():
    from tools import site_after as A
    d = {"updated": "2026-10-29", "backdrop": "10 年債 5.0%，信用利差平穩",
         "items": [{"sym": "GOOGL", "name": "Alphabet", "sector": "科技／雲端", "date": "2026-10-28", "mcap_b": 3000,
                    "one": "雲端成長但利潤率持平", "move": {"pct": 4.2, "why": "盤後 +4.2%：Cloud 營收高於預期（新聞 16:05）"},
                    "company": ["搜尋 +15%"], "spill": [{"who": "博通", "how": "TPU 共同設計"}], "macro": ["殖利率 5%"], "sources": ["8-K"]},
                   {"sym": "KO", "name": "可口可樂", "sector": "民生消費", "date": "2026-10-28", "mcap_b": 280, "one": "價格調漲撐住營收，這裡不是買進時機"}]}
    f = Path(tempfile.mkdtemp()) / "earn_after.json"
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    orig = A.FILE
    A.FILE = f
    try:
        h = A.sec_earn_after(None)
        t = A.sec_earn_after_tech(None)
    finally:
        A.FILE = orig
    assert "Alphabet" in h and "可口可樂" in h and "<details" in h and "連帶影響" in h and "+4.2%" in h and "大環境" in h
    assert "買進" not in h
    assert "Alphabet" in t and "可口可樂" not in t
    A.FILE = Path(tempfile.mkdtemp()) / "none.json"
    try:
        assert A.sec_earn_after(None) == ""
    finally:
        A.FILE = orig


if __name__ == "__main__":
    test_card()
    print("ok test_card")
