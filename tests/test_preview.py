"""財報前瞻: probabilities normalised, scenarios and gauges shown, the scorecard (hit rate, Brier) computed from the
reports already out, malformed entries skipped.  Run: python -m tests.test_preview"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_prev_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_preview as SP  # noqa: E402


def test_card_and_score():
    d = {"updated": "2026-10-26", "gauges": [{"name": "CoreWeave 債券殖利率", "read": "約 15%，一個月上升"}],
         "items": [{"sym": "MSFT", "name": "微軟", "date": "2026-10-28", "call": "樂觀", "probs": {"上修": 55, "維持": 35, "下修": 10},
                    "implied_move": 5.2, "scenarios": [{"name": "好", "prob": 55, "what": "資本支出再上修", "impact": "輝達、台積電"}], "basis": ["上季說會加速"]},
                   {"sym": "META", "date": "2026-10-21", "call": "中性", "probs": {"上修": 0.6, "維持": 0.3, "下修": 0.1}, "outcome": "上修"},
                   {"sym": "X", "date": "2026-10-01", "probs": {"上修": 0.2, "維持": 0.2, "下修": 0.6}, "outcome": "上修"},
                   {"name": "bad"}]}
    p = Path(tempfile.mkdtemp()) / "earn_preview.json"
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    old = SP.FILE
    SP.FILE = p
    try:
        h = SP.sec_earn_preview(None)
        assert "一句話看懂：微軟 樂觀" in h and "上修 <b>55%</b>" in h and "±5.2%" in h and "CoreWeave 債券殖利率" in h
        assert "✅ 猜中" in h and "❌ 沒猜中" in h and "最可能的情境猜中 1 次（50%）" in h
        sc = SP.score(d["items"])
        assert sc["n"] == 2 and sc["hits"] == 1 and abs(sc["brier"] - ((0.4 ** 2 + 0.3 ** 2 + 0.1 ** 2) + (0.8 ** 2 + 0.2 ** 2 + 0.6 ** 2)) / 2) < 1e-9
        for b in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出"):
            assert b not in h
        SP.FILE = Path(tempfile.mkdtemp()) / "none.json"
        assert SP.sec_earn_preview(None) == ""
    finally:
        SP.FILE = old


if __name__ == "__main__":
    test_card_and_score()
    print("ok test_card_and_score")
