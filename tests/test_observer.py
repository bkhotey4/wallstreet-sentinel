"""獨立 AI 觀察員 card: empty state before the first run, a filled verdict, the tile, links and escaping.
Run: python -m tests.test_observer"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ob_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_observer():
    from tools import site_observer as SOB
    from wsb.data import stability as ST
    if SOB.FILE.exists():                                   # the public repo has the real file; test the cache path only
        return
    h = SOB.sec_ai_observer(None)
    assert "還沒有第一份判讀" in h and 'id="ai-observer"' in h and SOB.tile()[2] == "待第一次判讀"
    d = ST.load()
    d["ai_view"] = {"updated": "2026-10-26T21:00", "verdict": "恐慌被誇大", "summary": "AI 泡沫有部分根據，但整體壓力低於平均",
                    "narratives": [{"claim": "AI 泡沫即將破裂", "source": "https://example.com/a", "judgement": "部分支持",
                                    "reason": "半導體從高點跌 26%，但信用利差仍在收窄<script>", "data": [
                                        {"name": "OFR 壓力指數", "value": "-1.98", "date": "2026-10-21", "url": "https://www.financialresearch.gov/"},
                                        {"name": "壞連結", "value": "1", "url": "javascript:alert(1)"}]}],
                    "watch": ["OFR 壓力指數升破 0"], "history": [{"time": "2026-10-26T21:00", "verdict": "恐慌被誇大", "summary": "第一次"}]}
    ST._save(d)
    h = SOB.sec_ai_observer(None)
    assert "🟢 恐慌被誇大" in h and "AI 泡沫即將破裂" in h and "部分支持" in h and "出現這些，判讀才會改變" in h
    assert "<script>" not in h and "javascript:" not in h and 'href="https://www.financialresearch.gov/"' in h
    assert SOB.tile()[2] == "恐慌被誇大"


if __name__ == "__main__":
    test_observer()
    print("ok test_observer")
