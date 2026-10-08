"""Market-structure / liquidity calendar.

Computed (no network): monthly & quarterly option expiry, VIX expiry, month- / quarter-end rebalancing.
Fetched (best effort): Treasury 10/20/30-year auctions from TreasuryDirect — heavy supply days that can push yields.
Every event: {date, event, type: 'liquidity', id, importance 1-3, note}."""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd


log = logging.getLogger(__name__)
_FED_HOL = None


def _holidays():
    global _FED_HOL
    if _FED_HOL is None:
        from pandas.tseries.holiday import USFederalHolidayCalendar
        _FED_HOL = USFederalHolidayCalendar()
    return _FED_HOL


def _is_holiday(d: date) -> bool:
    ts = pd.Timestamp(d)
    return bool(len(_holidays().holidays(start=ts, end=ts)))


def prev_bday(d: date) -> date:
    """Last trading-ish day on or before d (weekends and US federal holidays skipped)."""
    while d.weekday() >= 5 or _is_holiday(d):
        d -= timedelta(days=1)
    return d


def third_friday(year: int, month: int) -> date:
    d = date(year, month, 1)
    d += timedelta(days=(4 - d.weekday()) % 7)           # first Friday
    return prev_bday(d + timedelta(days=14))             # holiday → the Thursday before (e.g. Juneteenth)


def vix_expiry(year: int, month: int) -> date:
    """VIX options/futures settle on the Wednesday 30 days before the NEXT month's standard expiry."""
    ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
    d = third_friday(ny, nm) - timedelta(days=30)
    while d.weekday() != 2:                              # walk to the Wednesday
        d -= timedelta(days=1)
    return d


def month_end(year: int, month: int) -> date:
    ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
    return prev_bday(date(ny, nm, 1) - timedelta(days=1))


def computed_events(today: Optional[date] = None, days: int = 45) -> List[Dict]:
    from zoneinfo import ZoneInfo
    today = today or datetime.now(ZoneInfo("America/New_York")).date()
    end = today + timedelta(days=days)
    out: List[Dict] = []
    y, m = today.year, today.month
    for k in range(0, 4):
        yy, mm = y + (m - 1 + k) // 12, (m - 1 + k) % 12 + 1
        quad = mm in (3, 6, 9, 12)
        tf = third_friday(yy, mm)
        out.append({"date": tf.isoformat(), "type": "liquidity", "id": f"opex{yy}{mm:02d}",
                    "event": "四巫日：股票/指數期貨選擇權同日到期" if quad else "月選擇權到期日（OPEX）",
                    "importance": 3 if quad else 2,
                    "note": "選擇權部位集中平倉，造市商 Gamma 大幅重置，到期前後波動與成交量常放大"
                            + ("；季底 + 指數成分調整，影響更大" if quad else "")})
        vx = vix_expiry(yy, mm)
        out.append({"date": vx.isoformat(), "type": "liquidity", "id": f"vixx{yy}{mm:02d}",
                    "event": "VIX 期貨/選擇權到期", "importance": 1,
                    "note": "VIX 結算價由 SPX 選擇權報價決定，結算日前後 VIX 易失真，勿過度解讀"})
        me = month_end(yy, mm)
        qe = mm in (3, 6, 9, 12)
        out.append({"date": me.isoformat(), "type": "liquidity", "id": f"mend{yy}{mm:02d}",
                    "event": "季底資產再平衡／窗飾" if qe else "月底資產再平衡",
                    "importance": 3 if qe else 1,
                    "note": "退休/平衡型基金依月（季）漲跌幅被動調整股債比重，股強債弱的月份常見月底賣股壓力"})
    return sorted([e for e in out if today <= date.fromisoformat(e["date"]) <= end], key=lambda e: e["date"])


async def treasury_auctions(days: int = 30) -> List[Dict]:
    from . import http
    js = await http.get("https://www.treasurydirect.gov/TA_WS/securities/upcoming", params={"format": "json"})
    from zoneinfo import ZoneInfo
    out, today = [], datetime.now(ZoneInfo("America/New_York")).date()
    for r in js if isinstance(js, list) else []:
        term = str(r.get("originalSecurityTerm") or r.get("securityTerm", ""))   # reopenings: "9-Year 10-Month" remaining
        typ = str(r.get("securityType", ""))
        m = re.match(r"(\d+)-Year", term)
        if typ not in ("Note", "Bond") or not m or int(m.group(1)) not in (10, 20, 30):
            continue
        try:
            d = datetime.fromisoformat(str(r["auctionDate"])[:19]).date()
        except Exception:  # noqa: BLE001
            continue
        if not (today <= d <= today + timedelta(days=days)):
            continue
        amt = r.get("offeringAmount")
        try:
            amt_s = f"{float(amt) / 1e9:.0f}B" if amt not in (None, "", "null") else ""
        except (TypeError, ValueError):
            amt_s = ""
        yrs = int(m.group(1))
        reopen = "增額" if str(r.get("reopening", "")).lower() == "yes" else "新發"
        out.append({"date": d.isoformat(), "type": "liquidity", "id": f"auc{yrs}{d.isoformat()}",
                    "event": f"美債 {yrs} 年期標售（{reopen}）" + (f" ${amt_s}" if amt_s else ""),
                    "importance": 3 if yrs >= 10 else 2,
                    "note": "標售尾差（tail）大／需求弱 → 殖利率跳升，長天期資產與成長股承壓"})
    return out
