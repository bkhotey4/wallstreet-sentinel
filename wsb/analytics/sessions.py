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
    """(time zone, settled-close time) from the one market table in wsb.data.freshness (HK, JP, EU… not just US / TW);
    a bar counts as final 15 minutes after the close.  Exchange holidays are not modelled here."""
    from datetime import date as _date, datetime as _dt, timedelta as _td
    from ..data.freshness import MARKETS, market_of as _m
    m = _m(str(sym))
    if m in ("fx", "crypto"):
        return US
    tz, _open, close, _wk = MARKETS[m]
    settle = (_dt.combine(_date(2000, 1, 1), close) + _td(minutes=15)).time()
    return tz, settle


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
