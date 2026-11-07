"""每日總經情勢 audio card and 一個月預判 card.  Run: python -m tests.test_forecast"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點")


def dump(base: Path, name: str, d) -> None:
    (base / name).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


class FakeTTS:
    def __init__(self, text, voice):
        self.text = text

    async def save(self, path):
        Path(path).write_bytes(b"mp3")


class BrokenTTS(FakeTTS):
    async def save(self, path):
        raise OSError("no network")


def test_voice():
    from tools import site_forecast as F
    base = Path(tempfile.mkdtemp())
    dump(base, "macro_voice.json", {"date": "2026-11-07", "one": "利率是主角", "script": "第一段<b>\n\n第二段"})
    with patch.object(F, "FILE", base / "forecast.json"):
        with patch.dict(sys.modules, {"edge_tts": types.SimpleNamespace(Communicate=FakeTTS)}):
            F.make_audio(base / "market")
            h = F.sec_macro_voice(None)
            assert (base / "market" / "macro.mp3").read_bytes() == b"mp3"
            assert "一句話看懂：利率是主角" in h and "<audio controls" in h and f'market/macro.mp3?v={F.AUDIO["v"]}' in h
            assert "<p>第一段&lt;b&gt;</p><p>第二段</p>" in h and "看文字稿" in h
            (base / "market" / "macro.mp3").unlink()

            async def inside_loop():                         # the real build calls this from a running event loop
                F.make_audio(base / "market")

            asyncio.run(inside_loop())
            assert F.AUDIO["v"] and (base / "market" / "macro.mp3").exists()
        with patch.dict(sys.modules, {"edge_tts": types.SimpleNamespace(Communicate=BrokenTTS)}):
            F.make_audio(base / "market")                    # audio failure leaves the text card
        h = F.sec_macro_voice(None)
        assert "<audio" not in h and "第二段" in h
    with patch.object(F, "FILE", base / "x" / "forecast.json"):
        F.make_audio(base / "market")
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
    assert "偏鷹但沒壞" in h and "偏鷹 <b>55%</b>" in h and "<td>會升息</td>" in h and "12-09" in h and "看依據" in h and "可能錯在" in h
    assert "舊預判不再列" not in h and "2 題對 1 題（50%），當時平均估 70%" in h and "AI 供應商" in h and "TSM +11%" in h and "收 3.5%" in h
    assert 'href="javascript' not in h and not any(w in h for w in BANNED)
    with patch.object(F, "FILE", base / "none.json"):
        assert F.sec_forecast(None) == ""


def test_stamp():
    from tools import site_forecast as F, site_stamp as ST
    base = Path(tempfile.mkdtemp())
    dump(base, "forecast.json", {"updated": "2026-11-07 21:10 台北"})
    dump(base, "macro_voice.json", {"updated": "2026-11-07"})
    now = 1794000000.0
    with patch.object(F, "FILE", base / "forecast.json"):
        st = ST.stamp(None, "sec_forecast", "overview", now)
        assert "最後更新" in st and "11-07 21:10" in st, st
        st = ST.stamp(None, "sec_macro_voice", "overview", now)       # a date alone: no invented time
        assert "最後更新" not in st and "11-07" in st, st


if __name__ == "__main__":
    test_voice()
    test_forecast()
    test_stamp()
    print("FORECAST TESTS PASSED")
