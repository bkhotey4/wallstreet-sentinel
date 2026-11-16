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
    from datetime import date, timedelta
    fut = (date.today() + timedelta(days=3)).isoformat()
    d = {"updated": "2026-10-26", "gauges": [{"name": "CoreWeave 債券殖利率", "read": "約 15%，一個月上升"}],
         "items": [{"sym": "MSFT", "name": "微軟", "date": fut, "call": "樂觀", "probs": {"上修": 55, "維持": 35, "下修": 10},
                    "implied_move": 5.2, "scenarios": [{"name": "好", "prob": 55, "what": "資本支出再上修", "impact": "輝達、台積電"}], "basis": ["上季說會加速"]},
                   {"sym": "META", "date": "2026-10-21", "call": "中性", "probs": {"上修": 0.6, "維持": 0.3, "下修": 0.1}, "outcome": "上修"},
                   {"sym": "X", "date": "2026-10-01", "probs": {"上修": 0.2, "維持": 0.2, "下修": 0.6}, "outcome": "上修"},
                   {"sym": "OLD", "name": "舊公司", "date": "2026-01-05", "call": "中性"},          # out, result not filled in yet
                   {"name": "bad"}]}
    p = Path(tempfile.mkdtemp()) / "earn_preview.json"
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    old = SP.FILE
    SP.FILE = p
    try:
        h = SP.sec_earn_preview(None)
        assert f"一句話看懂：微軟（{fut[5:].replace('-', '/')}）樂觀" in h and "舊公司" not in h and "另有 1 家已經公布" in h and "上修 <b>55%</b>" in h and "±5.2%" in h and "CoreWeave 債券殖利率" in h
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


def test_missing_big_report_is_flagged():
    days = {"2026-11-17": {"rows": [{"sym": "NVDA", "name": "NVIDIA", "mcap": 4.0e12}, {"sym": "SMALL", "mcap": 5e9}]},
            "2026-11-25": {"rows": [{"sym": "AAPL", "mcap": 3.5e12}]}}
    assert [m["sym"] for m in SP.missing_big([], days, "2026-11-16")] == ["NVDA"]          # AAPL is 9 days away; SMALL is small
    assert SP.missing_big([{"sym": "NVDA"}], days, "2026-11-16") == []


if __name__ == "__main__":
    test_missing_big_report_is_flagged()
    print("ok test_missing_big_report_is_flagged")


def test_live_card_must_show_big_reports():
    from tools import sys_health as H
    days = {"2026-11-17": {"rows": [{"sym": "NVDA", "name": "NVIDIA", "mcap": 4e12}, {"sym": "HD", "name": "Home Depot", "mcap": 3.5e11}]}}
    feed = {"items": [{"sym": "NVDA"}, {"sym": "HD"}]}
    nav = "<nav>財報前瞻：公布前的機率估計與成績單</nav>"
    hidden = nav + "<section><h2>財報前瞻：公布前的機率估計與成績單</h2><p>家得寶 HD・2026-11-17</p></section><section>x</section>"
    shown = hidden.replace("家得寶 HD", "輝達 NVDA 家得寶 HD")
    assert [i["key"] for i in H.shown_issues(hidden, feed, days, "2026-11-16")] == ["shown:NVDA"]
    assert H.shown_issues(shown, feed, days, "2026-11-16") == []
    assert H.shown_issues("<p>nothing</p>", feed, days, "2026-11-16")[0]["key"] == "shown:preview_card"


if __name__ == "__main__":
    test_live_card_must_show_big_reports()
    print("ok test_live_card_must_show_big_reports")
