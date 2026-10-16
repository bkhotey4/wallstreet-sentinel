"""Which daily bars are finished sessions.  Live quotes are merged into daily history, so during a session the
last bar is an in-progress price; anything presented as a "close" must drop it until the market has closed."""
from __future__ import annotations

from datetime import datetime, time as dtime
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd

US = ("America/New_York", dtime(16, 15))
TW = ("Asia/Taipei", dtime(13, 45))


def market_of(sym: str):
    s = str(sym)
    return TW if s.endswith((".TW", ".TWO")) or s == "^TWII" else US


def completed(px: pd.Series, sym: str = "", now: Optional[datetime] = None) -> pd.Series:
    """`px` without today's bar while that market's session is still open (or not yet settled)."""
    if px is None or not len(px):
        return px
    tz, close = market_of(sym)
    loc = (now or datetime.now(ZoneInfo("UTC"))).astimezone(ZoneInfo(tz))
    last = pd.Timestamp(px.index[-1]).date()
    if last >= loc.date() and loc.time() < close:
        return px[px.index < pd.Timestamp(loc.date())]
    return px
