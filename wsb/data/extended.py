"""US pre-market / after-hours prices (Yahoo chart, includePrePost) for the 盤前／盤後跳空 alerts.  The same rule as the
site's /api/quote?ext=: the last 5-minute trade outside the regular session, compared with the last regular close."""
from __future__ import annotations

import asyncio
from datetime import datetime, time as dtime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from . import http

NY = ZoneInfo("America/New_York")


def us_ext_session(now: Optional[datetime] = None) -> Optional[str]:
    """"pre" 04:00–09:30, "post" 16:00–20:00 New York on weekdays, else None (holidays show no extended trades)."""
    loc = (now or datetime.now(NY)).astimezone(NY)
    if loc.weekday() >= 5:
        return None
    t = loc.time()
    return "pre" if dtime(4) <= t < dtime(9, 30) else "post" if dtime(16) <= t < dtime(20) else None


def parse(res: Dict) -> Optional[Dict]:
    m = (res or {}).get("meta") or {}
    reg = (m.get("currentTradingPeriod") or {}).get("regular") or {}
    base = m.get("regularMarketPrice")
    if not isinstance(base, (int, float)) or not base or "start" not in reg:
        return None
    ts = res.get("timestamp") or []
    cl = (((res.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
    for t, c in reversed(list(zip(ts, cl))):
        if c is None or t is None:
            continue
        sess = "post" if t >= reg["end"] else "pre" if t < reg["start"] else None
        if not sess:
            return None
        return {"px": float(c), "chg": (float(c) / base - 1) * 100, "sess": sess, "t": int(t), "base": float(base)}
    return None


async def fetch(syms: List[str]) -> Dict[str, Dict]:
    sem, out = asyncio.Semaphore(6), {}

    async def one(s):
        async with sem:
            try:
                js = await http.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=1d&interval=5m&includePrePost=true",
                                    headers={"User-Agent": "Mozilla/5.0"}, timeout=15, retries=0)
                e = parse(((js.get("chart") or {}).get("result") or [None])[0])
                if e:
                    out[s] = e
            except Exception:  # noqa: BLE001
                pass
    await asyncio.gather(*(one(s) for s in syms))
    return out
