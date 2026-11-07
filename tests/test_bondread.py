"""債市深度判讀 card.  Run: python -m tests.test_bondread"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點")


def test_card():
    from tools import site_bondread as B
    d = {"updated": "2026-11-09", "one": "利率因<通膨>上升", "story": ["先講人", "再講錢"], "next": "看 CPI",
         "auctions": [{"date": "2026-11-10", "what": "10 年期公債", "cover": "2.5 倍", "read": "買氣普通"}, {"date": "2026-11-11"}],
         "drivers": [{"name": "通膨預期", "read": "小升", "evidence": "損益平衡 2.4%"}, {"name": "空"}],
         "credit": [{"name": "高收益債", "read": "利差擴大"}],
         "issuers": [{"name": "甲骨文", "trend": "惡化", "read": "負債增加"}, {"name": "空"}],
         "world": [{"name": "日本", "read": "殖利率上升"}],
         "sources": [{"name": "Treasury", "url": "https://example.com/a"}, {"name": "壞", "url": "javascript:x"}]}
    f = Path(tempfile.mkdtemp()) / "bonds.json"
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with patch.object(B, "FILE", f):
        h = B.sec_bond_read(None)
    assert "一句話看懂：利率因&lt;通膨&gt;上升" in h and "<p>先講人</p>" in h and "看完整解讀" in h and "2.5 倍" in h and "11-10" in h
    assert "損益平衡 2.4%" in h and "利差擴大" in h and "誰在大量借錢（1 家）" in h and "殖利率上升" in h and "看 CPI" in h
    assert 'class="dn">惡化' in h and "空" not in h.replace("空間", "") and 'href="javascript' not in h and not any(w in h for w in BANNED)
    with patch.object(B, "FILE", f.with_name("none.json")):
        assert B.sec_bond_read(None) == ""


if __name__ == "__main__":
    test_card()
    print("BOND READ TESTS PASSED")
