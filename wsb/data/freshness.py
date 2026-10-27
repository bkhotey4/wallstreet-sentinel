"""Is a quote current?  A successful download says nothing about how old the price is: a daily bar from Yahoo, a Stooq
backup or the TWSE file can all be a session behind.  This compares the bar date with the last session the instrument's
market should have traded (weekends and the opening hour, by market time zone; exchange holidays are not modelled, so a
holiday reads as "one session behind" — shown, never alerted on)."""
from __future__ import annotations

from datetime import datetime, time as dtime, timedelta, timezone
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo

# market → (time zone, regular open, regular close, trades on weekends)
MARKETS: Dict[str, Tuple[str, dtime, dtime, bool]] = {
    "us": ("America/New_York", dtime(9, 30), dtime(16, 0), False),
    "tw": ("Asia/Taipei", dtime(9, 0), dtime(13, 30), False),
    "jp": ("Asia/Tokyo", dtime(9, 0), dtime(15, 30), False),
    "hk": ("Asia/Hong_Kong", dtime(9, 30), dtime(16, 0), False),
    "kr": ("Asia/Seoul", dtime(9, 0), dtime(15, 30), False),
    "cn": ("Asia/Shanghai", dtime(9, 30), dtime(15, 0), False),
    "au": ("Australia/Sydney", dtime(10, 0), dtime(16, 0), False),
    "in": ("Asia/Kolkata", dtime(9, 15), dtime(15, 30), False),
    "eu": ("Europe/Berlin", dtime(9, 0), dtime(17, 30), False),
    "uk": ("Europe/London", dtime(8, 0), dtime(16, 30), False),
    "fx": ("America/New_York", dtime(0, 0), dtime(23, 59), False),     # FX and futures: nearly 24 h on weekdays
    "crypto": ("UTC", dtime(0, 0), dtime(23, 59), True),
}
_SUFFIX = {".TW": "tw", ".TWO": "tw", ".T": "jp", ".HK": "hk", ".KS": "kr", ".KQ": "kr", ".SS": "cn", ".SZ": "cn",
           ".AX": "au", ".NS": "in", ".BO": "in", ".DE": "eu", ".PA": "eu", ".AS": "eu", ".MI": "eu", ".MC": "eu",
           ".SW": "eu", ".L": "uk"}
_INDEX = {"^TWII": "tw", "^TWOII": "tw", "^N225": "jp", "^HSI": "hk", "^KS11": "kr", "000001.SS": "cn", "^AXJO": "au",
          "^NSEI": "in", "^BSESN": "in", "^GDAXI": "eu", "^FCHI": "eu", "^STOXX50E": "eu", "^FTSE": "uk"}


def market_of(ticker: str) -> str:
    t = ticker.upper()
    if t in _INDEX:
        return _INDEX[t]
    if t.endswith("-USD") or t.endswith("-USDT"):
        return "crypto"
    if t.endswith("=X") or t.endswith("=F"):
        return "fx"
    for suf, m in _SUFFIX.items():
        if t.endswith(suf):
            return m
    return "us"


def expected_bar(ticker: str, now: Optional[datetime] = None) -> str:
    """Date (YYYY-MM-DD, market time) of the newest daily bar that should exist right now."""
    tz, open_, _close, weekend = MARKETS[market_of(ticker)]
    loc = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(tz))
    d = loc.date() if loc.time() >= open_ else loc.date() - timedelta(days=1)     # before the open: yesterday's bar
    while not weekend and d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.isoformat()


def session(ticker: str, now: Optional[datetime] = None) -> str:
    """"regular" / "closed" for the instrument's own market right now (pre/post-market are "closed" for daily bars)."""
    tz, open_, close, weekend = MARKETS[market_of(ticker)]
    loc = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(tz))
    if not weekend and loc.weekday() >= 5:
        return "closed"
    return "regular" if open_ <= loc.time() <= close else "closed"


def stale(ticker: str, asof: str, now: Optional[datetime] = None) -> bool:
    """True when the bar is older than the last session the market should have traded."""
    return bool(asof) and str(asof)[:10] < expected_bar(ticker, now)
