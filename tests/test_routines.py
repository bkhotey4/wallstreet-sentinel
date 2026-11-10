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
    html = R.sec_routine_health()
    assert "排程健康表" in html and "<table" in html
    print("test_routines: ok")


if __name__ == "__main__":
    main()
