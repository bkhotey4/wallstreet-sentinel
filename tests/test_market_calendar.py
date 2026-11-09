"""NYSE holidays and half days in the live-card session state (tools/site_session.py).
Run: python -m tests.test_market_calendar   (the browser part needs node; skipped without it)"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_session as S  # noqa: E402


def test_calendar():
    c = S.us_calendar(date(2026, 11, 8), 800)
    assert "2026-11-26" in c["hol"] and "2026-12-25" in c["hol"]
    assert c["early"]["2026-11-27"] == S.EARLY_CLOSE and "2026-12-24" in c["early"]
    assert "2027-12-24" not in c["early"]           # Christmas on a Saturday: Dec 24 is the observed holiday
    assert "2026-07-03" not in c["early"] and "2028-07-03" in c["early"]


def _state(when: datetime, quote: datetime) -> dict:
    js = (S.MKT_JS + "\nDate.now=function(){return %d};console.log(JSON.stringify(mktState([%d],'America/New_York',570,960)));"
          % (when.timestamp() * 1000, quote.timestamp()))
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_browser():
    if not shutil.which("node"):
        print("node not found: browser check skipped")
        return
    ny = ZoneInfo("America/New_York")
    cal = S.us_calendar()
    early = next(iter(cal["early"]), None)
    if early:
        d = date.fromisoformat(early)
        st = _state(datetime(d.year, d.month, d.day, 14, 0, tzinfo=ny), datetime(d.year, d.month, d.day, 12, 59, tzinfo=ny))
        assert st["st"] == "post" and st["early"], st
        st = _state(datetime(d.year, d.month, d.day, 11, 0, tzinfo=ny), datetime(d.year, d.month, d.day, 10, 59, tzinfo=ny))
        assert st["st"] == "open" and st["early"], st
    hol = next((h for h in cal["hol"] if date.fromisoformat(h) >= date.today()), None)
    if hol:
        d = date.fromisoformat(hol)
        st = _state(datetime(d.year, d.month, d.day, 8, 0, tzinfo=ny), datetime(d.year, d.month, d.day - 1 if d.day > 1 else d.day, 16, 0, tzinfo=ny))
        assert st["st"] == "closed" and st["hol"], st              # before the open the holiday is now known, not "not open yet"


def test_sessions_note():
    from datetime import timezone
    from tools import site_sessions as SS
    mon = datetime(2026, 11, 9, 3, 54, tzinfo=timezone.utc)                  # Monday noon in Taipei, still Sunday in New York
    assert "週末美股休市" in SS.stale_note("2026-11-06", mon) and "11/9（週一）21:00" in SS.stale_note("2026-11-06", mon)
    assert "節日" in SS.stale_note("2026-11-25", datetime(2026, 11, 26, 15, 0, tzinfo=timezone.utc))
    assert SS.stale_note("2026-11-06", datetime(2026, 11, 6, 23, 0, tzinfo=timezone.utc)) == ""


if __name__ == "__main__":
    test_calendar()
    test_sessions_note()
    test_browser()
    print("MARKET CALENDAR TESTS PASSED [OK]")
