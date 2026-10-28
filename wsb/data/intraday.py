"""盤中細項 for holdings (owner DM only): one month of regular-session 5-minute bars (Yahoo chart) → same-time relative
volume, VWAP and whether the last three completed bars closed under / over it.  The same rules as the site's
/api/quote?iv= (functions/api/quote.js intraFrom), so the DM and the page agree."""
from __future__ import annotations

import asyncio
import time
from statistics import median
from typing import Dict, List, Optional

from . import http


def parse(res: Dict, now: Optional[float] = None) -> Optional[Dict]:
    m = (res or {}).get("meta") or {}
    ts = (res or {}).get("timestamp") or []
    if not m or len(ts) < 50:
        return None
    q = (((res.get("indicators") or {}).get("quote") or [{}])[0])
    off = m.get("gmtoffset") or 0
    days: Dict[int, List[dict]] = {}
    for i, t in enumerate(ts):
        c = (q.get("close") or [None] * len(ts))[i]
        if t is None or c is None:
            continue
        h, lo, v = (q.get("high") or [None] * len(ts))[i], (q.get("low") or [None] * len(ts))[i], (q.get("volume") or [None] * len(ts))[i]
        days.setdefault((t + off) // 86400, []).append({"t": t, "k": (t + off) % 86400, "c": float(c), "h": h, "l": lo, "v": float(v or 0)})
    ks = sorted(days)
    if len(ks) < 6:
        return None
    today, past = days[ks[-1]], [days[k] for k in ks[:-1]][-20:]
    last = today[-1]
    if now is not None and now - last["t"] > 15 * 60:          # no fresh bar: this market is not trading right now
        return None
    cut = last["k"]
    out = {"t": last["t"], "price": last["c"], "prev": past[-1][-1]["c"], "n_days": len(past)}
    out["chg"] = (last["c"] / out["prev"] - 1) * 100 if out["prev"] else None
    pv = [sum(b["v"] for b in d if b["k"] <= cut) for d in past]
    pv = [x for x in pv if x > 0]
    vt = sum(b["v"] for b in today)
    if len(pv) >= 5 and vt > 0:
        out["rvol"] = vt / median(pv)
    if vt > 0:
        run, pvs, vs = [], 0.0, 0.0
        for b in today:
            tp = (b["h"] + b["l"] + b["c"]) / 3 if b["h"] and b["l"] else b["c"]
            pvs += tp * b["v"]
            vs += b["v"]
            run.append(pvs / vs if vs else None)
        out["vwap"] = run[-1]
        if out["vwap"]:
            out["vgap"] = (last["c"] / out["vwap"] - 1) * 100
        if len(today) >= 5:
            done = [len(today) - 1 - j for j in (1, 2, 3)]        # the newest bar is still forming
            out["below3"] = all(run[i] and today[i]["c"] < run[i] for i in done)
            out["above3"] = all(run[i] and today[i]["c"] > run[i] for i in done)
    return out


async def fetch(syms: List[str]) -> Dict[str, Dict]:
    sem, out, now = asyncio.Semaphore(6), {}, time.time()

    async def one(s):
        async with sem:
            try:
                js = await http.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=1mo&interval=5m",
                                    headers={"User-Agent": "Mozilla/5.0"}, timeout=20, retries=0)
                r = parse(((js.get("chart") or {}).get("result") or [None])[0], now)
                if r:
                    out[s] = r
            except Exception:  # noqa: BLE001
                pass
    await asyncio.gather(*(one(s) for s in syms))
    return out
