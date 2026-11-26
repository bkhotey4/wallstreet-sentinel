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


def test_tw_calendar_and_missed_run():
    """11-27: the Taiwan outlook (Mon–Fri 15:50) missed 11/26 while US Thanksgiving hid it; it must show 🟡 and name the run."""
    from datetime import datetime
    from tools import site_routines as R
    tpe = R.TPE
    ts = datetime(2026, 11, 25, 22, 55, tzinfo=tpe).timestamp()
    now = datetime(2026, 11, 27, 0, 40, tzinfo=tpe).timestamp()
    miss = R.missed_run("tw_forecast.json", ts, now)
    assert miss == datetime(2026, 11, 26, 15, 50, tzinfo=tpe).timestamp()
    assert R.missed_run("tw_forecast.json", datetime(2026, 11, 26, 16, 30, tzinfo=tpe).timestamp(), now) is None
    early = datetime(2026, 11, 26, 16, 30, tzinfo=tpe).timestamp()        # inside the 2 h grace: not missed yet
    assert R.missed_run("tw_forecast.json", ts, early) is None
    assert abs(R.tw_hours(ts, now) - (now - ts) / 3600) < 0.01            # 11/26 is a Taiwan trading day: every hour counts
    r = {"real": 19.0, "age": 2.0, "missed": None}
    assert R._ago(r) == "19 小時前（休市不算：2 小時）"


if __name__ == "__main__":
    test_tw_calendar_and_missed_run()
    print("ok test_tw_calendar_and_missed_run")
