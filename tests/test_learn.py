"""每日學習筆記 card: renders the routine's learn.json (stories split into confirmed / reported, a term glossary),
escapes everything, hides itself without data, and never shows banned trading words.
Run: python -m tests.test_learn"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點")


def test_card():
    from tools import site_learn as L
    d = {"updated": "2026-11-04 01:30 台北",
         "stories": [{"date": "2026-11-02", "topic": "Anthropic 可能拿到垃圾債評級", "one": "三大機構還沒公布",
                      "confirmed": ["S-1/A 2026-11-02"], "reported": ["Blackstone 預估 BB"], "market": "費半 −7.2%",
                      "sources": [{"name": "Tech Times", "date": "2026-11-02", "url": "https://example.com/a"}, {"name": "bad", "url": "javascript:alert(1)"}]},
                     {"date": "2026-10-01", "topic": "<script>x</script>", "one": "舊的"}],
         "terms": [{"term": "二階導", "en": "Second derivative", "added": "2026-11-04", "site": "已在本站", "plain": "成長在加速還是放慢"},
                   {"term": "耳語預期", "added": "2026-11-03", "site": "做不到", "plain": "私下期待的數字"}]}
    f = Path(tempfile.mkdtemp()) / "learn.json"
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    orig = L.FILE
    L.FILE = f
    try:
        h = L.sec_learn(None)
    finally:
        L.FILE = orig
    assert "一句話看懂：Anthropic 可能拿到垃圾債評級" in h                     # newest story leads
    assert "已確認" in h and "只是報導" in h and "Blackstone" in h
    assert "今天新學的術語：二階導" in h and "耳語預期" in h and "（2 個）" in h
    assert "<script>x" not in h and "javascript:" not in h and 'href="https://example.com/a"' in h
    for w in BANNED:
        assert w not in h, w
    L.FILE = Path(tempfile.mkdtemp()) / "none.json"
    try:
        assert L.sec_learn(None) == ""
    finally:
        L.FILE = orig
    src = (Path(L.__file__).parent / "build_site.py").read_text(encoding="utf-8")
    assert "SLN.sec_learn" in src


if __name__ == "__main__":
    test_card()
    print("ok test_card")
