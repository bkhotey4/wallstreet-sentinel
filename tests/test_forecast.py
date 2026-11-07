"""每日總經情勢 voice card and 一個月預判 card.  Run: python -m tests.test_forecast"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點")


def dump(base: Path, name: str, d) -> None:
    (base / name).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def test_voice():
    from tools import site_forecast as F
    base = Path(tempfile.mkdtemp())
    dump(base, "forecast.json", {"one": "接下來偏鷹"})
    dump(base, "sessions.json", {"items": [
        {"date": "2026-11-05", "phase": "盤後", "one": "舊的", "macro": [{"name": "利率", "read": "舊"}]},
        {"date": "2026-11-06", "phase": "盤前", "one": "早上", "macro": [{"name": "利率", "read": "早"}]},
        {"date": "2026-11-06", "phase": "盤後", "one": "收盤<b>", "macro": [{"name": "利率", "read": "10 年債 4.86%。"}, {"name": "沒寫"}], "next": "看 CPI"},
        {"date": "2026-11-07", "phase": "盤前", "one": "沒有總經"}]})
    with patch.object(F, "FILE", base / "forecast.json"):
        h = F.sec_macro_voice(None)
    assert "一句話看懂：收盤&lt;b&gt;" in h and "聽今天的總經" in h and "speechSynthesis" in h and "沒寫" not in h
    assert 'id="mvtext" hidden>2026-11-06 的總經情勢。收盤&lt;b&gt;。利率：10 年債 4.86%。接下來看：看 CPI。接下來偏鷹<' in h, h[:900]
    with patch.object(F, "FILE", base / "x" / "forecast.json"):
        assert F.sec_macro_voice(None) == ""


def test_forecast():
    from tools import site_forecast as F
    d = {"updated": "2026-11-07", "one": "偏鷹但沒壞", "paths": [{"name": "偏鷹", "prob": 55, "what": "升息"}],
         "calls": [{"name": "利率", "call": "會升息", "prob": 70, "by": "2026-12-09", "measure": "FOMC", "why": "就業強", "wrong": "CPI 轉弱", "now": "4.00%"},
                   {"name": "舊題", "call": "舊預判不再列", "prob": 80, "result": "對", "note": "收 3.5%"}, {"name": "舊題二", "call": "舊二", "prob": 60, "result": "錯"},
                   {"name": "空"}],
         "nextq": {"one": "錢往供應商移動", "groups": [{"name": "AI 供應商", "trend": "上修", "read": "預估調高", "evidence": "TSM +11%"}, {"name": "空"}]},
         "sources": [{"name": "Fed", "url": "https://example.com/a"}, {"name": "壞", "url": "javascript:x"}]}
    base = Path(tempfile.mkdtemp())
    dump(base, "forecast.json", d)
    with patch.object(F, "FILE", base / "forecast.json"):
        h = F.sec_forecast(None)
    assert "偏鷹但沒壞" in h and "約 55%" in h and "我估 70%" in h and "2026-12-09 對答案" in h and "可能錯在" in h
    assert "舊預判不再列" not in h and "2 題對 1 題（50%），當時平均估 70%" in h and "AI 供應商" in h and "TSM +11%" in h
    assert 'href="javascript' not in h and not any(w in h for w in BANNED)
    with patch.object(F, "FILE", base / "none.json"):
        assert F.sec_forecast(None) == ""


if __name__ == "__main__":
    test_voice()
    test_forecast()
    print("FORECAST TESTS PASSED")
