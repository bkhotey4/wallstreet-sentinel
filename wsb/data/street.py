"""Wall Street earnings calendar (Nasdaq public API) + post-report scorecard
(EPS surprise from Yahoo, actual price reaction from daily prices)."""
from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from ..config import SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
NY = ZoneInfo("America/New_York")
CFG = SETTINGS.get("street", {})
_TIME = {"time-pre-market": "盤前", "time-after-hours": "盤後", "time-not-supplied": "未定"}
_cache: Dict[str, tuple] = {}


def _num(s) -> Optional[float]:
    if s in (None, "", "N/A", "--"):
        return None
    s = str(s).replace("$", "").replace(",", "").strip()
    neg = s.startswith("(") and s.endswith(")")
    try:
        v = float(s.strip("()"))
    except ValueError:
        return None
    return -v if neg else v


def ny_trade_date(now: Optional[datetime] = None) -> date:
    """The US session the user cares about next: today (NY) before 16:00, else next business day."""
    n = (now or datetime.now(NY)).astimezone(NY)
    d = n.date() if n.hour < 16 else n.date() + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


async def earnings_on(d: date) -> List[Dict]:
    key = d.isoformat()
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < 3 * 3600:
        return hit[1]
    js = await http.get("https://api.nasdaq.com/api/calendar/earnings", params={"date": key},
                        headers={"Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com",
                                 "Referer": "https://www.nasdaq.com/"}, timeout=20)
    rows = ((js or {}).get("data") or {}).get("rows") or []
    out = []
    for r in rows:
        out.append({"date": key, "symbol": (r.get("symbol") or "").upper(), "name": re.sub(r",? Inc\.?$|,? Corp(oration)?\.?$", "", r.get("name") or ""),
                    "mcap": _num(r.get("marketCap")), "when": _TIME.get(r.get("time"), "未定"),
                    "eps_fc": _num(r.get("epsForecast")), "eps_ly": _num(r.get("lastYearEPS")),
                    "n_est": _num(r.get("noOfEsts")), "quarter": r.get("fiscalQuarterEnding")})
    _cache[key] = (time.time(), out)
    HEALTH.ok("nasdaq_earnings", len(out), every=6 * 3600)
    return out


def important(rows: List[Dict], extra: List[str]) -> List[Dict]:
    min_cap = float(CFG.get("min_mcap_bn", 50)) * 1e9
    watch = {s.upper() for s in CFG.get("watchlist", [])} | {s.upper() for s in extra}
    keep = [r for r in rows if (r["mcap"] or 0) >= min_cap or r["symbol"] in watch]
    return sorted(keep, key=lambda r: -(r["mcap"] or 0))


def _bdays(start: date, n: int, forward: bool = True) -> List[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1 if forward else -1)
    return out


async def week_ahead(extra: List[str], days: int = 5) -> Dict[str, List[Dict]]:
    res: Dict[str, List[Dict]] = {}
    for d in _bdays(ny_trade_date(), days):
        try:
            res[d.isoformat()] = important(await earnings_on(d), extra)[: int(CFG.get("per_day", 8))]
        except Exception as e:  # noqa: BLE001
            HEALTH.fail("nasdaq_earnings", e, every=6 * 3600)
            log.warning("nasdaq earnings %s failed: %s", d, e)
        await asyncio.sleep(0.4)
    return res


def _surprise_and_reaction(rows: List[Dict]) -> List[Dict]:
    import yfinance as yf
    syms = [r["symbol"] for r in rows]
    if not syms:
        return []
    px = yf.download(syms, period="1mo", interval="1d", auto_adjust=True, progress=False, group_by="column")
    close = px["Close"] if "Close" in px else pd.DataFrame()
    if isinstance(close, pd.Series):
        close = close.to_frame(syms[0])
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    out = []
    for r in rows:
        rec = dict(r)
        try:
            df = yf.Ticker(r["symbol"]).get_earnings_dates(limit=4)
            if df is not None and not df.empty:
                df = df.dropna(subset=["Reported EPS"])
                if not df.empty:
                    rec["eps_act"] = float(df.iloc[0]["Reported EPS"])
                    est = df.iloc[0].get("EPS Estimate")
                    rec["eps_est"] = float(est) if pd.notna(est) else r.get("eps_fc")
                    sp = df.iloc[0].get("Surprise(%)")
                    rec["surprise"] = float(sp) if pd.notna(sp) else None
        except Exception as e:  # noqa: BLE001
            log.info("surprise %s: %s", r["symbol"], e)
        try:
            s = close[r["symbol"]].dropna()
            d0 = pd.Timestamp(r["date"])
            react_day = d0 if r["when"] == "盤前" else s.index[s.index > d0][0]
            prev = s[s.index < react_day].iloc[-1]
            rec["reaction"] = float(s.loc[react_day] / prev - 1) * 100
        except Exception:  # noqa: BLE001
            rec["reaction"] = None
        out.append(rec)
    return out


async def last_week_results(extra: List[str], days: int = 5, top: int = 12) -> List[Dict]:
    start = ny_trade_date() - timedelta(days=1)
    rows: List[Dict] = []
    for d in _bdays(start, days, forward=False):
        try:
            rows += important(await earnings_on(d), extra)[:6]
        except Exception as e:  # noqa: BLE001
            log.warning("nasdaq earnings %s failed: %s", d, e)
        await asyncio.sleep(0.4)
    rows = sorted(rows, key=lambda r: -(r["mcap"] or 0))[:top]
    return await asyncio.to_thread(_surprise_and_reaction, rows)
