"""Forward event calendar: US macro releases (FRED release schedule),
FOMC meeting dates (scraped live from federalreserve.gov), earnings dates
for portfolio holdings (yfinance)."""
from __future__ import annotations

import asyncio
import logging
import re
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
_MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}


async def _fred_releases(days: int = 21) -> List[dict]:
    if not FRED_API_KEY:
        return []
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


async def _fomc() -> List[dict]:
    html = await http.get("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", kind="text")
    out = []
    # page sections: "<year> FOMC Meetings" ... month + "28-29" style
    for ym in re.finditer(r"(\d{4}) FOMC Meetings(.*?)(?=\d{4} FOMC Meetings|$)", html, re.S):
        year, block = int(ym.group(1)), ym.group(2)
        for m in re.finditer(r'fomc-meeting__month[^>]*>\s*<strong>([A-Za-z/]+)</strong>.*?'
                             r'fomc-meeting__date[^>]*>([\d\-\*]+)', block, re.S):
            month = m.group(1).split("/")[-1]
            days = re.findall(r"\d+", m.group(2))
            if month in _MONTHS and days:
                try:
                    d = date(year, _MONTHS[month], int(days[-1]))
                except ValueError:
                    continue
                if us_today() <= d <= us_today() + timedelta(days=120):
                    out.append({"date": d.isoformat(), "event": "FOMC 利率決議", "type": "fomc"})
    return out


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
        for name, r in zip(("fred_calendar", "fomc_calendar", "earnings_calendar", "treasury_auctions"), res):
            if isinstance(r, Exception):
                HEALTH.fail(name, r, every=every)
            else:
                HEALTH.ok(name, len(r), every=every)
                events += r
        self.events = sorted(events, key=lambda e: e["date"])
        self.ts = time.time()

    def upcoming(self, days: int = 14) -> List[dict]:
        lim = (us_today() + timedelta(days=days)).isoformat()
        today = us_today().isoformat()
        return [e for e in self.events if today <= e["date"] <= lim]
