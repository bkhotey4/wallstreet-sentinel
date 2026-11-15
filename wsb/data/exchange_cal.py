"""美股與台股的休市、提早收盤（2026-11-16，使用者選的第 12 項）：一份共用的交易所行事曆。

  * 美股（紐約證交所）：全日休市來自 python-holidays 的 NYSE 行事曆（交易所公布的固定規則：耶穌受難日休市、
    退伍軍人節照開、元旦落在週六不補假）；提早在美東 13:00 收盤的半天：感恩節隔天、聖誕夜、7/3（各自落在交易日時；
    7/3 只有週一到週四才是半天，落在週五就是 7/4 的補假）。臨時休市（國喪、天災）規則算不出來，會在卡片上說。
  * 台股（證交所）：直接讀證交所官方「市場開休市日期」（www.twse.com.tw/rwd/zh/holidaySchedule，一年一份），
    「開始交易日／最後交易日」是有交易的日子，其他列（放假、只辦結算交割）是沒有交易的日子。快取 data_cache/econ_exchange_cal.json。
美東時間換成台北時間用 zoneinfo，所以夏令時間（3 月第二個週日～11 月第一個週日）會自動差一小時。"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_exchange_cal.json"
TTL = 7 * 86400
TW_URL = "https://www.twse.com.tw/rwd/zh/holidaySchedule/holidaySchedule"
TW_PAGE = "https://www.twse.com.tw/zh/trading/holiday.html"
HDR = {"User-Agent": "WallStreetSentinel research (public data reader)"}
NY, TPE = ZoneInfo("America/New_York"), ZoneInfo("Asia/Taipei")
US_OPEN, US_CLOSE, US_EARLY = (9, 30), (16, 0), (13, 0)
TW_OPEN, TW_CLOSE = (9, 0), (13, 30)


# ------------------------------------------------------------------ US (rules, no network)
def us_holidays(y0: int, y1: int) -> Dict[str, str]:
    """{iso date: holiday name} for NYSE full-day closures."""
    try:
        import holidays
        cal = holidays.financial_holidays("NYSE", years=range(y0, y1 + 1))
        return {d.isoformat(): str(n) for d, n in cal.items()}
    except Exception:  # noqa: BLE001
        return {}


def us_early(y0: int, y1: int, hol: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """{iso date: reason} for the 13:00 New York closes."""
    hol = us_holidays(y0, y1) if hol is None else hol
    out = {}
    for y in range(y0, y1 + 1):
        nov = date(y, 11, 1)
        thanks = nov + timedelta(days=(3 - nov.weekday()) % 7 + 21)
        for d, why, ok in ((thanks + timedelta(days=1), "感恩節隔天", True), (date(y, 12, 24), "聖誕夜", True),
                           (date(y, 7, 3), "美國獨立紀念日前一天", date(y, 7, 3).weekday() <= 3)):
            if ok and d.weekday() < 5 and d.isoformat() not in hol:
                out[d.isoformat()] = why
    return out


def us_open(d: date, hol: Optional[Dict[str, str]] = None) -> bool:
    hol = us_holidays(d.year, d.year) if hol is None else hol
    return d.weekday() < 5 and d.isoformat() not in hol


def us_session_tpe(d: date, early: bool = False) -> str:
    """'21:30–04:00' style: the New York session of day d in Taipei time (daylight saving handled)."""
    a = datetime(d.year, d.month, d.day, *US_OPEN, tzinfo=NY).astimezone(TPE)
    b = datetime(d.year, d.month, d.day, *(US_EARLY if early else US_CLOSE), tzinfo=NY).astimezone(TPE)
    return f"{a:%H:%M}–{'隔天 ' if b.date() > a.date() else ''}{b:%H:%M}"


# ------------------------------------------------------------------ Taiwan (official file)
def parse_tw(js: Dict) -> List[Dict]:
    """TWSE schedule rows → [{date, name, open}] ; 'open' True only for 開始交易日／最後交易日 rows."""
    out = []
    for r in js.get("data") or []:
        if len(r) < 2:
            continue
        name = str(r[1]).strip()
        out.append({"date": str(r[0])[:10], "name": name, "open": name.endswith("交易日")})
    return out


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def refresh(force: bool = False, today: Optional[date] = None) -> Dict:
    d = load()
    today = today or date.today()
    now = time.time()
    if not force and now - float(d.get("ts", 0)) < TTL and str(today.year) in (d.get("tw") or {}):
        return d
    tw = dict(d.get("tw") or {})
    bad = []
    for y in (today.year, today.year + 1):
        try:
            js = json.loads(await http.get(TW_URL, params={"response": "json", "date": f"{y}0101"}, kind="text", headers=HDR,
                                           timeout=30, retries=1))
            rows = parse_tw(js)
            if rows and rows[0]["date"].startswith(str(y)):
                tw[str(y)] = rows
            elif y == today.year:
                bad.append(f"{y}: no rows")
        except Exception as e:  # noqa: BLE001
            if y == today.year:
                bad.append(f"{y}: {e if str(e) else type(e).__name__}")
    d.update(tw={k: v for k, v in tw.items() if int(k) >= today.year - 1}, ts=now if not bad else d.get("ts", 0), ts_try=now)
    if bad:
        log.warning("exchange calendar: %s", "; ".join(bad))
        HEALTH.fail("exchange_cal", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("exchange_cal", sum(len(v) for v in tw.values()), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def tw_closed(d: Optional[Dict] = None) -> Dict[str, str]:
    """{iso date: name} for weekdays the Taiwan market does not trade (official file only)."""
    d = load() if d is None else d
    return {r["date"]: r["name"] for rows in (d.get("tw") or {}).values() for r in rows
            if not r["open"] and date.fromisoformat(r["date"]).weekday() < 5}


def tw_known(d: Optional[Dict] = None, y: Optional[int] = None) -> bool:
    d = load() if d is None else d
    return str(y or date.today().year) in (d.get("tw") or {})


def upcoming(today: date, days: int = 60, d: Optional[Dict] = None) -> List[Dict]:
    """Every weekday in the next `days` on which either market is closed or the US closes early, oldest first:
    [{date, us: 'closed'|'early'|'open', us_why, tw: 'closed'|'open'|'?', tw_why, us_hours}]"""
    d = load() if d is None else d
    hol = us_holidays(today.year, (today + timedelta(days=days)).year)
    early = us_early(today.year, (today + timedelta(days=days)).year, hol)
    twc = tw_closed(d)
    out = []
    for i in range(days + 1):
        x = today + timedelta(days=i)
        if x.weekday() >= 5:
            continue
        k = x.isoformat()
        us = "closed" if k in hol else "early" if k in early else "open"
        tw = "closed" if k in twc else ("open" if tw_known(d, x.year) else "?")
        if us != "open" or tw == "closed":
            out.append({"date": k, "us": us, "us_why": hol.get(k) or early.get(k) or "", "tw": tw, "tw_why": twc.get(k, ""),
                        "us_hours": us_session_tpe(x, us == "early") if us != "closed" else ""})
    return out
