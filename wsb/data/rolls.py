"""Futures roll guard for the continuous oil quotes (BZ=F Brent, CL=F WTI).

Yahoo's continuous contract jumps to the next month a few days before the front month expires.  On that day the
"change" is partly the gap between two contracts, not a market move: 2026-10-26 showed Brent −5.83% when the
settled front month fell 0.78%, and the SSI oil-shock input took it as a real drop.

Brent and WTI move together; on a normal day their changes are close.  So a day near one contract's expiry on which
its change is more than GAP away from the other's is treated as a roll day:
- q(): that day's % change is shown as unknown (NaN → "—"), with roll=True, instead of a made-up number;
- series(): the price history before that day is scaled so the roll day's return equals the other oil's return,
  which keeps 5/20/63-day oil changes (SSI, regime, energy chain) free of the contract gap.  Today's price is unchanged.

Expiry rules (holidays ignored, the window is wide enough):
- ICE Brent: last business day of the second month before delivery → the last business day of every month.
- NYMEX WTI: 3 business days before the 25th of the month before delivery (before the business day preceding the
  25th when the 25th is not a business day) → around the 20th of every month."""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from typing import List, Optional

import pandas as pd

PEERS = {"BZ=F": "CL=F", "CL=F": "BZ=F"}
GAP = 3.0                 # percentage points between Brent's and WTI's change on the same day
BEFORE, AFTER = 6, 1      # business days around expiry in which Yahoo may switch contracts


def _bday_back(d: date, n: int) -> date:
    while n > 0:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def _last_bday(y: int, m: int) -> date:
    d = date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def _wti_expiry(y: int, m: int) -> date:
    d = date(y, m, 25)
    if d.weekday() >= 5:
        d = _bday_back(d, 1)
    return _bday_back(d, 3)


@lru_cache(maxsize=64)
def expiries(ticker: str, year: int) -> List[date]:
    f = _last_bday if ticker == "BZ=F" else _wti_expiry
    return [f(year, m) for m in range(1, 13)]


def near_expiry(ticker: str, d: date) -> bool:
    if ticker not in PEERS:
        return False
    for e in expiries(ticker, d.year) + expiries(ticker, d.year + 1)[:1]:
        lo, hi = _bday_back(e, BEFORE), e + timedelta(days=AFTER + 2 * (e.weekday() >= 4))
        if lo <= d <= hi:
            return True
    return False


def is_roll_day(ticker: str, d: date, chg: Optional[float], peer_chg: Optional[float]) -> bool:
    """Near expiry and far from the other oil's move on the same day."""
    if chg is None or peer_chg is None or chg != chg or peer_chg != peer_chg:
        return False
    return near_expiry(ticker, d) and abs(chg - peer_chg) > GAP


def adjust(s: pd.Series, peer: pd.Series, ticker: str) -> pd.Series:
    """Back-adjust a continuous oil series across detected roll days (see module doc)."""
    if s is None or len(s) < 3 or peer is None or len(peer) < 3 or ticker not in PEERS:
        return s
    r = s.pct_change() * 100
    rp = peer.reindex(s.index).pct_change(fill_method=None) * 100
    out = s.copy()
    vals = out.values.astype(float)
    cand = [i for i in range(1, len(s)) if abs(r.iloc[i] - rp.iloc[i]) > GAP]   # NaN compares False
    for i in cand:
        d = s.index[i]
        if not is_roll_day(ticker, d.date() if hasattr(d, "date") else d, r.iloc[i], rp.iloc[i]):
            continue
        k = (1 + rp.iloc[i] / 100) / (1 + r.iloc[i] / 100)       # make the roll day's return equal the peer's
        vals[:i] = vals[:i] / k
    out[:] = vals
    return out
