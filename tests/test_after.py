"""財報後白話解讀 card: renders the routine's JSON (any sector), folds details, shows every US report on 美股財報, never shows
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
                   {"sym": "KO", "name": "可口可樂", "sector": "民生消費", "date": "2026-10-28", "mcap_b": 280, "one": "價格調漲撐住營收，這裡不是買進時機"},
                   {"mk": "tw", "sym": "2330", "name": "台積電", "sector": "半導體", "date": "2026-10-16", "mcap_b": 900, "one": "先進製程滿載"}]}
    f = Path(tempfile.mkdtemp()) / "earn_after.json"
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    orig = A.FILE
    A.FILE = f
    try:
        h = A.sec_earn_after(None)
        t = A.sec_earn_after_us(None)
    finally:
        A.FILE = orig
    assert "Alphabet" in h and "可口可樂" in h and "<details" in h and "連帶影響" in h and "+4.2%" in h and "大環境" in h
    assert "買進" not in h
    assert "Alphabet" in t and "可口可樂" in t and "台積電" not in t and "（美股）" in t        # 美股財報 tab: every US sector, not TW/HK
    A.FILE = Path(tempfile.mkdtemp()) / "none.json"
    try:
        assert A.sec_earn_after(None) == ""
    finally:
        A.FILE = orig


def test_all():
    from tools import site_after as A
    base = Path(tempfile.mkdtemp())
    day = {"items": [{"sym": "SMR", "name": "NuScale", "sector": "核能", "date": "2026-11-05", "one": "每日版"}]}
    more = {"items": [{"sym": "SMR", "name": "NuScale", "sector": "核能", "date": "2026-11-05", "one": "補寫版"},
                      {"mk": "tw", "sym": "2330", "name": "台積電", "sector": "半導體", "date": "2026-10-15", "one": "先進製程<滿載>"},
                      {"sym": "BAD", "date": "2026-10-15"}]}
    (base / "earn_after.json").write_text(json.dumps(day, ensure_ascii=False), encoding="utf-8")
    (base / "earn_after_more.json").write_text(json.dumps(more, ensure_ascii=False), encoding="utf-8")
    orig = A.FILE
    A.FILE = base / "earn_after.json"
    try:
        h = A.sec_earn_all(None)
        A.publish(base)
    finally:
        A.FILE = orig
    f = (base / "earn_all.html").read_text(encoding="utf-8")
    assert "2 份財報判讀" in h and "美股 1 份、台股 1 份、港股 0 份" in h and "market/earn_all.html" in h
    assert "每日版" in f and "補寫版" not in f and "BAD" not in f and "&lt;滿載&gt;" in f     # one read per report; text is escaped
    assert f.index("2026-11-05") < f.index("2026-10-15") and 'data-q="2330 台積電 半導體 台股"' in f


if __name__ == "__main__":
    test_card()
    test_all()
    print("ok test_card")
