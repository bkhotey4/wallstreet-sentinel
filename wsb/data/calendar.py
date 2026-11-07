"""Forward event calendar: US macro releases (FRED release schedule),
FOMC meeting dates (scraped live from federalreserve.gov), earnings dates
for portfolio holdings (yfinance)."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime, timedelta
from typing import List

from ..config import FRED_API_KEY, SETTINGS
from ..health import HEALTH
from . import http
from . import liquidity as liq

log = logging.getLogger(__name__)


def us_today() -> date:
    """Event dates here are US dates: compare them with the New York calendar day, not Taipei's."""
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("America/New_York")).date()


async def _fred_releases(days: int = 21) -> List[dict]:
    if not FRED_API_KEY:                                   # no key → report it, don't pretend "0 events, healthy"
        raise RuntimeError("FRED_API_KEY not set: macro release calendar (CPI/NFP…) unavailable")
    today = us_today()
    js = await http.get("https://api.stlouisfed.org/fred/releases/dates", params={
        "api_key": FRED_API_KEY, "file_type": "json",
        "realtime_start": today.isoformat(), "realtime_end": (today + timedelta(days=days)).isoformat(),
        "include_release_dates_with_no_data": "true", "limit": 1000, "sort_order": "asc"})
    wanted = [w.lower() for w in SETTINGS.get("calendar_releases", [])]
    out, seen = [], set()
    for r in js.get("release_dates", []):
        name = r.get("release_name", "")
        if any(w in name.lower() for w in wanted) and (name, r["date"]) not in seen:
            seen.add((name, r["date"]))
            out.append({"date": r["date"], "event": name, "type": "macro"})
    return out


def fomc_events(meetings: List[dict]) -> List[dict]:
    """Scheduled decisions within 120 days (meetings from econcal.parse_fomc: no notation votes, cross-month ok)."""
    out = []
    for m in meetings:
        d = date.fromisoformat(m["date"])
        if us_today() <= d <= us_today() + timedelta(days=120):
            out.append({"date": d.isoformat(), "event": "FOMC 利率決議", "type": "fomc"})
    return out


async def _fomc() -> List[dict]:
    from . import econcal
    meetings = await econcal.fomc_meetings()             # shared parser + 7-day cache with the econ calendar
    if not meetings:
        raise RuntimeError("no FOMC meetings (Fed calendar page and cache both empty)")
    return fomc_events(meetings)


def _earnings(tickers: List[str]) -> List[dict]:
    import yfinance as yf
    out = []
    for t in tickers:
        try:
            cal = yf.Ticker(t).calendar
            dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
            if dates:
                d = dates[0] if isinstance(dates, list) else dates
                d = d if isinstance(d, date) else datetime.fromisoformat(str(d)).date()
                if us_today() <= d <= us_today() + timedelta(days=60):
                    out.append({"date": d.isoformat(), "event": f"{t} 財報", "type": "earnings", "ticker": t})
        except Exception:  # noqa: BLE001
            continue
    return out


class EventCalendar:
    def __init__(self) -> None:
        self.events: List[dict] = []
        self.last: dict = {}           # each source's last good rows
        self.failed: List[str] = []
        self.ts = 0.0

    async def refresh(self, holdings: List[str]) -> None:
        every = SETTINGS["refresh"]["calendar"]
        res = await asyncio.gather(_fred_releases(), _fomc(), asyncio.to_thread(_earnings, holdings),
                                   liq.treasury_auctions(), return_exceptions=True)
        events = []
        try:                                                   # computed locally → cannot fail on network
            events += liq.computed_events(days=60)
        except Exception as ex:  # noqa: BLE001
            log.warning("liquidity calendar failed: %s", ex)
        self.failed = []
        for name, r in zip(("fred_calendar", "fomc_calendar", "earnings_calendar", "treasury_auctions"), res):
            if isinstance(r, Exception):
                HEALTH.fail(name, r, every=every)
                self.failed.append(name)
                events += self.last.get(name, [])   # a failed source keeps its rows instead of vanishing from the list
            else:
                HEALTH.ok(name, len(r), every=every)
                self.last[name] = r
                events += r
        self.events = sorted(events, key=lambda e: e["date"])
        if not self.failed:
            self.ts = time.time()

    def upcoming(self, days: int = 14) -> List[dict]:
        lim = (us_today() + timedelta(days=days)).isoformat()
        today = us_today().isoformat()
        return [e for e in self.events if today <= e["date"] <= lim]
