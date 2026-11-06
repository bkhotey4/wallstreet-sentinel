"""每日深度研判 card and the local bot's AI-off switch.  Run: python -m tests.test_deep"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點")


def render(d):
    from tools import site_deep as D
    f = Path(tempfile.mkdtemp()) / "deep.json"
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with patch.object(D, "FILE", f):
        return D.sec_deep(None)


def test_card():
    d = {"updated": "2026-11-06 06:20 台北", "days": [
        {"date": "2026-11-04", "one": "舊的一天",
         "calls": [{"claim": "VIX 回到 20 以下", "by": "2026-11-05", "measure": "VIX 收盤", "result": "錯", "note": "收在 22"}]},
        {"date": "2026-11-05", "one": "賣壓集中在半導體", "spill": "台股承壓",
         "lens": [{"name": "資金與利率", "read": "殖利率持平", "evidence": "10 年期 4.86%", "conf": "高"},
                  {"name": "沒寫內容"}],
         "signals": [{"name": "德州新規則", "read": "暫停未解除", "trend": "轉壞", "evidence": "稽核未完成", "next": "12 月中"},
                     {"name": "長線資金", "read": "沒有資料", "trend": "資料不足"}, {"name": "沒寫內容2"}],
         "checks": [{"claim": "<script>x</script>", "data": "SOX -8%", "verdict": "部分支持"}],
         "calls": [{"claim": "SOX 回到 5 日線", "by": "2026-11-12", "measure": "SOX 收盤"}],
         "lesson": "別只看單一新聞", "sources": [{"name": "SEC", "date": "2026-11-05", "url": "https://example.com/a"},
                                                  {"name": "壞", "url": "javascript:alert(1)"}]}]}
    h = render(d)
    assert "賣壓集中在半導體" in h and "舊的一天" not in h and "資金與利率" in h and "沒寫內容" not in h
    assert "評價標準變了" in h and "轉壞 1 項、資料不足 1 項" in h and "12 月中" in h and "沒寫內容2" not in h
    assert "<script>" not in h and "&lt;script&gt;" in h and 'href="javascript' not in h
    assert "待驗證 1 筆" in h and "到期的判斷 1 筆，對 0 筆、錯 1 筆" in h and "樣本還太少" in h and "收在 22" in h
    assert not any(w in h for w in BANNED)
    assert render({}) == "" and render({"days": [{"date": "2026-11-05"}]}) == ""


def test_ai_off():
    from wsb.ai import llm, news_ai as N
    from wsb.bot import present as P
    with patch.object(llm, "AI_OFF", True), patch.object(llm, "_engines") as eng:
        assert asyncio.run(llm.complete("s", "u")) == (llm.OFF_NOTE, "")
        eng.assert_not_called()
    sends = AsyncMock(return_value=True)
    with patch.object(P, "style", return_value="classic"), patch.object(P, "_send", sends):
        assert asyncio.run(P.deliver("dest", text=llm.OFF_NOTE, title="AI", content="## 標題"))
    assert sends.await_count == 1 and sends.await_args.args[1] == "## 標題\n" + llm.OFF_NOTE
    with patch.object(N, "AI_OFF", True), patch.object(N, "GEMINI_API_KEY", "x"):
        assert N.NewsClassifier().enabled is False


if __name__ == "__main__":
    test_card()
    test_ai_off()
    print("DEEP TESTS PASSED")
