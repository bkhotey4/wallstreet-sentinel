"""排程健康表: status lights from each cloud-AI file's `updated` time.  Run: python -m tests.test_routines"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from tools import site_routines as R

TPE = ZoneInfo("Asia/Taipei")


def ep(s: str) -> float:
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=TPE).timestamp()


def main() -> None:
    assert R.parse_updated("2026-11-10 22:34 台北") == ep("2026-11-10 22:34")
    assert R.parse_updated("2026-11-10T21:10") == ep("2026-11-10 21:10")
    assert R.parse_updated("2026-11-10") == ep("2026-11-10 12:00") and R.parse_updated("") is None
    assert R.status(None, 6) == "never" and R.status(12, 6) == "ok" and R.status(20, 6) == "late" and R.status(30, 6) == "stop"
    # Fri 23:00 → Mon 10:00 Taipei: only Fri 23–Sat 08 (9 h) and Mon 08–10 (2 h) count
    assert abs(R.weekday_hours(ep("2026-11-06 23:00"), ep("2026-11-09 10:00")) - 11) < 1e-6
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "sessions.json").write_text(json.dumps({"updated": "2026-11-06 23:00 台北"}), encoding="utf-8")
        (p / "deep.json").write_text(json.dumps({"updated": "2026-11-01 06:00 台北"}), encoding="utf-8")
        (p / "tw_note.json").write_text(json.dumps({"notes": [{"date": "2026-10-28", "month": "2026-09"}]}), encoding="utf-8")
        rs = {r["file"]: r for r in R.rows(now=ep("2026-11-09 10:00"), feed_dir=p)}
        assert rs["sessions.json"]["st"] == "ok"           # 11 trading hours, under 2 × 6
        assert rs["deep.json"]["st"] == "stop"             # 8 days, over 4 × 24 h
        assert rs["tw_note.json"]["st"] == "ok"
        assert rs["learn.json"]["st"] == "never"
        assert R.newest(list(rs.values())) == ep("2026-11-06 23:00")
        (p / "tw_note.json").unlink()
        rs = {r["file"]: r for r in R.rows(now=ep("2026-11-12 00:10"), feed_dir=p)}
        assert rs["tw_note.json"]["st"] == "wait" and rs["tw_note.json"]["first"] == ep("2026-11-28 12:05")
        rs = {r["file"]: r for r in R.rows(now=ep("2026-11-28 20:00"), feed_dir=p)}
        assert rs["tw_note.json"]["st"] == "wait"          # same day as the run: within the 1-day grace
        rs = {r["file"]: r for r in R.rows(now=ep("2026-11-30 09:00"), feed_dir=p)}
        assert rs["tw_note.json"]["st"] == "never"         # run passed over a day ago and still nothing → 🔴
        rs = {r["file"]: r for r in R.rows(now=ep("2027-01-05 09:00"), feed_dir=p)}
        assert rs["tw_note.json"]["st"] == "never"         # stays 🔴 in later months
        # 11-26 backfills: a finished backlog is ⚪ done, a paused one ⚪ paused with names left, otherwise still 🔴
        w = lambda n, d: (p / n).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")  # noqa: E731
        w("earn_backlog.json", {"items": [{"sym": "AAA"}, {"sym": "BBB"}]})
        w("earn_after_more.json", {"updated": "2026-11-01 06:00 台北", "items": [{"sym": "AAA"}], "skipped": []})
        w("earn_after.json", {"updated": "2026-11-01 06:00 台北", "items": []})
        w("earn_backlog_asia.json", {"items": [{"mk": "tw", "sym": "2330"}]})
        w("earn_after_asia.json", {"updated": "2026-11-01 06:00 台北", "items": [], "later": [{"mk": "tw", "sym": "2330"}]})
        w("earn_backlog_rest.json", {"items": [{"mk": "hk", "sym": "0002"}, {"mk": "tw", "sym": "1101"}]})
        w("earn_after_rest.json", {"updated": "2026-11-01 06:00 台北", "items": [{"mk": "hk", "sym": "0002"}]})
        rs = {r["file"]: r for r in R.rows(now=ep("2026-11-26 10:00"), feed_dir=p)}
        assert rs["earn_after_more.json"]["st"] == "stop" and rs["earn_after_more.json"]["left"] == 1
        assert rs["earn_after_asia.json"]["st"] == "done"  # parked in `later` counts as handled
        assert rs["earn_after_rest.json"]["st"] == "paused" and rs["earn_after_rest.json"]["left"] == 1
        w("earn_after_more.json", {"updated": "2026-11-01 06:00 台北", "items": [{"sym": "AAA"}], "skipped": [{"sym": "BBB"}]})
        rs = {r["file"]: r for r in R.rows(now=ep("2026-11-26 10:00"), feed_dir=p)}
        assert rs["earn_after_more.json"]["st"] == "done"
        assert rs["deep.json"]["st"] == "stop"             # a normal routine never turns ⚪
    html = R.sec_routine_health()
    assert "排程健康表" in html and "<table" in html
    print("test_routines: ok")


if __name__ == "__main__":
    main()
