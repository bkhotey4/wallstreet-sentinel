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
        assert f"一句話看懂：微軟（{fut[5:].replace('-', '/')}）樂觀" in h and "另有 1 家已經公布" in h and h.find("舊公司") > h.find("另有 1 家已經公布") and "上修 <b>55%</b>" in h and "±5.2%" in h and "CoreWeave 債券殖利率" in h
        assert "✅ 猜中" in h and "❌ 沒猜中" in h and "最可能的情境猜中 1 次（50%）" in h
        sc = SP.score(d["items"])
        assert sc["n"] == 2 and sc["hits"] == 1 and abs(sc["brier"] - ((0.4 ** 2 + 0.3 ** 2 + 0.1 ** 2) + (0.8 ** 2 + 0.2 ** 2 + 0.6 ** 2)) / 2) < 1e-9
        for b in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出"):
            assert b not in h
        SP.FILE = Path(tempfile.mkdtemp()) / "none.json"
        assert SP.sec_earn_preview(None) == ""
    finally:
        SP.FILE = old


def test_slow_source_flagged():
    from tools import sys_health as H
    from datetime import datetime
    lines = []
    for i in range(8):                                     # 8 runs, the SEC list timed out in 5, the news API in 1
        m = 3 * i
        if i < 5:
            lines.append(f"2026-11-17 01:{m:02d}:20,000 INFO SEC feed page 0: timeout after 14s: https://www.sec.gov/x")
        if i == 0:
            lines.append(f"2026-11-17 01:{m:02d}:30,000 INFO news: ")
        lines.append(f"2026-11-17 01:{m:02d}:50,000 INFO SEC push: 0 sent (40 s)")
    now = datetime(2026, 11, 17, 1, 30).timestamp()
    out = H.slow_source_issues(lines, now)
    assert out and "SEC 最新 8-K 清單（5/8 輪）" in out[0]["text"] and "/api/news" not in out[0]["text"], out
    assert H.slow_source_issues(lines[:6], now) == []      # too few runs to judge


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


def test_after_card_keeps_mega_caps():
    from tools import site_after as A
    from tools import sys_health as H
    fake = [{"sym": f"S{i}", "date": "2026-11-19", "mcap_b": 30, "one": "x"} for i in range(6)] + [{"sym": "NVDA", "date": "2026-11-17", "mcap_b": 4000, "one": "x"}]
    fake = sorted(fake, key=lambda x: (x["date"], x["mcap_b"]), reverse=True)
    assert [x["sym"] for x in A.shown(fake, 6)][:2] == ["NVDA", "S0"] and len(A.shown(fake, 6)) == 6
    old = [{"sym": "OLD", "date": "2026-11-01", "mcap_b": 4000, "one": "x"}] + fake
    assert "OLD" not in [x["sym"] for x in A.shown(sorted(old, key=lambda x: x["date"], reverse=True), 6)]   # pinned 7 days only
    html = '<section><h2>財報後白話解讀（美股）</h2><p>S0 S1</p></section><section>'
    assert [i["key"] for i in H.after_issues(html, fake, "2026-11-19")] == ["shown_after:NVDA"]


if __name__ == "__main__":
    test_after_card_keeps_mega_caps()
    print("ok test_after_card_keeps_mega_caps")


def test_overrun_flagged():
    from tools import sys_health as H
    from datetime import datetime
    lines = [f"2026-11-16 21:{m:02d}:00,000 WARNING out of time after 98 s: mops, holdings left for the next run" for m in (10, 30, 50)]
    now = datetime(2026, 11, 16, 22, 0).timestamp()
    out = H.overrun_issues(lines, now)
    assert out and "台股重大訊息" in out[0]["text"] and "持股私訊" in out[0]["text"]
    assert H.overrun_issues(lines[:2], now) == []


def test_offline_flagged():
    from datetime import datetime
    from tools import sys_health as H
    lines = []
    for i in range(10):
        m = 3 * i
        if i % 2 == 0:
            lines.append(f"2026-11-17 01:{m:02d}:20,000 INFO news: Cannot connect to host x:443 ssl:default [getaddrinfo failed]")
        lines.append(f"2026-11-17 01:{m:02d}:50,000 INFO SEC push: 0 sent (99 s)")
    now = datetime(2026, 11, 17, 1, 40).timestamp()
    out = H.offline_issues(lines, now)
    assert out and out[0]["key"] == "offline" and "5/10" in out[0]["text"], out
    assert H.offline_issues([ln for ln in lines if "getaddrinfo" not in ln], now) == []
    assert H.offline_issues(lines[:6], now) == []          # too few runs to judge


if __name__ == "__main__":
    test_offline_flagged()
    print("ok test_offline_flagged")
    test_overrun_flagged()
    print("ok test_overrun_flagged")
    test_slow_source_flagged()
    print("ok test_slow_source_flagged")


def test_card_never_drops_big_or_lead():
    """11-17: eight smaller 11/17 names filled the cap and Walmart (11/19, ~$1T) vanished although the lead line named it."""
    from tools import site_preview as P
    from wsb.data import econcal as EC
    items = [{"sym": f"S{i}", "name": f"Small{i}", "date": "2026-11-17", "call": "中性"} for i in range(9)]
    items += [{"sym": "WMT", "name": "沃爾瑪", "date": "2026-11-19", "call": "中性"}]
    caps = {f"S{i}": 1e10 * (i + 1) for i in range(9)} | {"WMT": 1e12}
    real = (P.load, P._mcaps, P._earn_days, EC.us_today)
    from datetime import date
    P.load, P._mcaps, P._earn_days, EC.us_today = (lambda: {"items": items}), (lambda: caps), (lambda: {}), (lambda: date(2026, 11, 17))
    try:
        h = P.sec_earn_preview(None)
    finally:
        P.load, P._mcaps, P._earn_days, EC.us_today = real
    assert "WMT" in h and "沃爾瑪" in h, "Walmart must be on the card"
    assert h.count("・2026-11-17") == 9 and "看其餘 2 家公司的前瞻" in h, h.count("・2026-11-17")   # all shown; 2 folded


if __name__ == "__main__":
    test_card_never_drops_big_or_lead()
    print("ok test_card_never_drops_big_or_lead")
