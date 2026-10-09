"""US economic calendar (財經日曆): release dates, consensus, previous and actual values.

Sources (all public, no key):
  * Nasdaq economic calendar  api.nasdaq.com/api/calendar/economicevents?date=D
      - quirk: the response for ?date=D lists the events of D-1 (verified against ISM = first business day, NFP Fridays and
        the Fed's own meeting calendar), so the events of day X are fetched with ?date=X+1
      - quirk: times are in a fixed UTC-4 clock all year (an 08:30 EST release shows as 09:30), converted here to UTC
      - carries consensus / previous / actual, also for past dates → used to back-fill ~2 years of release history
  * ForexFactory this-week feed (nfs.faireconomy.media) — fills a missing consensus for this week's releases
  * federalreserve.gov meeting calendar — FOMC dates further out, and which meetings carry projections (SEP, the "*")

Only US rows are kept; the event keys / grouping / importance live in analytics/macro_events.py."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
_FILE = DATA_DIR / "econ_days.json"
_FOMC_FILE = DATA_DIR / "econ_fomc.json"
NQ_HDR = {"Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"}
_MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                         "September", "October", "November", "December"], 1)}


def cfg() -> Dict:
    return SETTINGS.get("econ", {}) or {}


def us_today() -> date:
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("America/New_York")).date()


# ------------------------------------------------------------------ parsing
def clean(s) -> str:
    s = "" if s is None else str(s)
    return s.replace("&nbsp;", "").replace("\xa0", "").strip()


def num(s) -> Optional[float]:
    """'0.3%' → 0.3 · '1,701K' → 1701 (thousands) · '7.271M' → 7271 · '-132.07B' → -132070 · '2.929T' → 2929000 · '' → None.
    K/M/B/T are all brought to thousands so a consensus and an actual written with different suffixes still compare."""
    s = clean(s).replace(",", "").replace("$", "")
    if not s:
        return None
    mult = 1.0
    if s[-1:] == "%":
        s = s[:-1]
    elif s[-1:].upper() in ("K", "M", "B", "T"):
        mult = {"K": 1.0, "M": 1e3, "B": 1e6, "T": 1e9}[s[-1].upper()]
        s = s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def _utc(day: date, hhmm: str) -> Optional[str]:
    """Nasdaq clock (fixed UTC-4) → ISO UTC timestamp."""
    m = re.match(r"(\d{1,2}):(\d{2})", clean(hhmm))
    if not m:
        return None
    t = datetime(day.year, day.month, day.day, int(m.group(1)), int(m.group(2)), tzinfo=timezone(timedelta(hours=-4)))
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_nasdaq(js: Dict, day: date) -> List[Dict]:
    """US rows of one Nasdaq response (already the events of `day`)."""
    rows = ((js or {}).get("data") or {}).get("rows") or []
    out = []
    for r in rows:
        if clean(r.get("country")) != "United States":
            continue
        name = clean(r.get("eventName"))
        if not name:
            continue
        out.append({"name": name, "utc": _utc(day, r.get("gmt", "")), "actual": clean(r.get("actual")),
                    "cons": clean(r.get("consensus")), "prev": clean(r.get("previous"))})
    return out


# ------------------------------------------------------------------ cache
def load() -> Dict[str, Dict]:
    try:
        if _FILE.exists():
            return json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("econ cache unreadable: %s", e)
    return {}


def save(days: Dict[str, Dict]) -> None:
    try:
        tmp = _FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(days, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        tmp.replace(_FILE)
    except Exception as e:  # noqa: BLE001
        log.warning("econ cache not saved: %s", e)


def _due(day: date, rec: Optional[Dict], today: date, now: float) -> bool:
    """How often a day is re-fetched: final days once, the live window often, the far future twice a day."""
    if rec is None:
        return True
    age = now - float(rec.get("ts", 0))
    d = (day - today).days
    if d < -3:
        return not rec.get("final")
    if d <= 7:
        return age > float(cfg().get("live_refresh_s", 1500))
    return age > 12 * 3600


async def fetch_day(day: date) -> List[Dict]:
    js = await http.get("https://api.nasdaq.com/api/calendar/economicevents", params={"date": (day + timedelta(days=1)).isoformat()},
                        headers=NQ_HDR, timeout=20, retries=1)
    return parse_nasdaq(js, day)


async def refresh(budget_s: Optional[float] = None, force_days: Optional[List[date]] = None) -> Dict[str, Dict]:
    """Bring the cache up to date: the window [-7, +ahead] first, then back-fill history (oldest gaps last) in the time left."""
    c = cfg()
    budget = float(budget_s if budget_s is not None else c.get("budget_s", 120))
    t0, now = time.time(), time.time()
    today = us_today()
    days = load()
    ahead, back = int(c.get("days_ahead", 45)), int(c.get("backfill_days", 730))
    want = [today + timedelta(days=i) for i in range(-7, ahead + 1)]
    hist = [today - timedelta(days=i) for i in range(8, back + 1)]
    queue = list(force_days or []) + [d for d in want if _due(d, days.get(d.isoformat()), today, now)]
    queue += [d for d in hist if d.weekday() < 5 and d.isoformat() not in days][: int(c.get("backfill_per_run", 80))]
    n_ok = n_err = 0
    for d in queue:
        if time.time() - t0 > budget:
            break
        try:
            rows = await fetch_day(d)
            days[d.isoformat()] = {"ts": time.time(), "rows": rows, "final": (today - d).days > 3}
            n_ok += 1
        except Exception as e:  # noqa: BLE001
            n_err += 1
            log.info("econ %s: %s", d, e)
            if n_err >= 6 and n_ok == 0:
                break
        await asyncio.sleep(float(c.get("sleep_s", 0.25)))
    if n_ok:
        cut = (today - timedelta(days=back + 30)).isoformat()
        days = {k: v for k, v in days.items() if k >= cut}
        save(days)
    if n_err and not n_ok:
        HEALTH.fail("econ_calendar", RuntimeError(f"{n_err} Nasdaq calendar requests failed"), every=3600)
    else:
        HEALTH.ok("econ_calendar", n_ok, every=3600)
    pending = sum(1 for d in hist if d.weekday() < 5 and d.isoformat() not in days)
    log.info("econ calendar: %d days fetched, %d failed, %d history days still missing", n_ok, n_err, pending)
    return days


# ------------------------------------------------------------------ ForexFactory (this week's forecasts)
FF_MAP = {  # FF title → (Nasdaq-style name, variant) — variant "m" = month-on-month, "y" = year-on-year
    "CPI m/m": ("CPI", "m"), "CPI y/y": ("CPI", "y"), "Core CPI m/m": ("Core CPI", "m"), "Core CPI y/y": ("Core CPI", "y"),
    "PPI m/m": ("PPI", "m"), "PPI y/y": ("PPI", "y"), "Core PPI m/m": ("Core PPI", "m"), "Core PPI y/y": ("Core PPI", "y"),
    "Non-Farm Employment Change": ("Nonfarm Payrolls", ""), "Unemployment Rate": ("Unemployment Rate", ""),
    "Average Hourly Earnings m/m": ("Average Hourly Earnings", "m"), "Core PCE Price Index m/m": ("Core PCE Price Index", "m"),
    "Core PCE Price Index y/y": ("Core PCE Price Index", "y"), "PCE Price Index m/m": ("PCE price index", "m"),
    "Advance GDP q/q": ("GDP", ""), "Prelim GDP q/q": ("GDP", ""), "Final GDP q/q": ("GDP", ""),
    "Retail Sales m/m": ("Retail Sales", "m"), "Core Retail Sales m/m": ("Core Retail Sales", ""),
    "ISM Manufacturing PMI": ("ISM Manufacturing PMI", ""), "ISM Services PMI": ("ISM Non-Manufacturing PMI", ""),
    "Unemployment Claims": ("Initial Jobless Claims", ""), "JOLTS Job Openings": ("JOLTS Job Openings", ""),
    "Prelim UoM Consumer Sentiment": ("Michigan Consumer Sentiment", ""), "Revised UoM Consumer Sentiment": ("Michigan Consumer Sentiment", ""),
    "Federal Funds Rate": ("Fed Interest Rate Decision", ""), "Durable Goods Orders m/m": ("Durable Goods Orders", ""),
    "Core Durable Goods Orders m/m": ("Core Durable Goods Orders", ""),
}


def parse_ff(js) -> List[Dict]:
    out = []
    for r in js or []:
        if r.get("country") != "USD" or r.get("title") not in FF_MAP:
            continue
        try:
            t = datetime.fromisoformat(str(r["date"]))
        except (KeyError, ValueError):
            continue
        nm, var = FF_MAP[r["title"]]
        out.append({"name": nm, "var": var, "date": t.date().isoformat(), "forecast": clean(r.get("forecast")),
                    "previous": clean(r.get("previous")), "impact": r.get("impact", "")})
    return out


async def ff_week() -> List[Dict]:
    try:
        js = await http.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json", timeout=20, retries=1)
        rows = parse_ff(js)
        HEALTH.ok("ff_calendar", len(rows), every=6 * 3600)
        return rows
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("ff_calendar", e, every=6 * 3600)
        return []


# ------------------------------------------------------------------ FOMC meeting calendar (dates + SEP)
def parse_fomc(page_html: str) -> List[Dict]:
    out = []
    for ym in re.finditer(r"(\d{4}) FOMC Meetings(.*?)(?=\d{4} FOMC Meetings|$)", page_html, re.S):
        year, block = int(ym.group(1)), ym.group(2)
        for m in re.finditer(r'fomc-meeting__month[^>]*>\s*<strong>([A-Za-z/]+)</strong>.*?'
                             r'fomc-meeting__date[^>]*>([^<]+)<', block, re.S):
            month = m.group(1).split("/")[-1]
            raw = m.group(2)
            days = re.findall(r"\d+", raw)
            if month in _MONTHS and days:
                try:
                    d = date(year, _MONTHS[month], int(days[-1]))
                except ValueError:
                    continue
                out.append({"date": d.isoformat(), "sep": "*" in raw, "start": f"{year}-{_MONTHS[month]:02d}-{int(days[0]):02d}"})
    return sorted({x["date"]: x for x in out}.values(), key=lambda x: x["date"])


async def fomc_meetings() -> List[Dict]:
    try:
        if _FOMC_FILE.exists() and time.time() - _FOMC_FILE.stat().st_mtime < 7 * 86400:
            return json.loads(_FOMC_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    try:
        page = await http.get("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", kind="text", timeout=25, retries=1)
        out = parse_fomc(page)
        if out:
            _FOMC_FILE.write_text(json.dumps(out), encoding="utf-8")
        HEALTH.ok("fomc_dates", len(out), every=86400)
        return out
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("fomc_dates", e, every=86400)
        try:
            return json.loads(_FOMC_FILE.read_text(encoding="utf-8")) if _FOMC_FILE.exists() else []
        except Exception:  # noqa: BLE001
            return []


class EconCalendar:
    """Holds the raw day cache + this week's ForexFactory forecasts + FOMC meeting list."""

    def __init__(self) -> None:
        self.days: Dict[str, Dict] = load()
        self.ff: List[Dict] = []
        self.fomc: List[Dict] = []
        self.ts = 0.0

    async def refresh(self, force: bool = False, budget_s: Optional[float] = None) -> None:
        if not cfg().get("enabled", True):
            return
        if not force and time.time() - self.ts < float(cfg().get("refresh_s", 1500)):
            return
        res = await asyncio.gather(refresh(budget_s), ff_week(), fomc_meetings(), return_exceptions=True)
        if not isinstance(res[0], Exception):
            self.days = res[0]
        else:
            log.warning("econ refresh failed: %s", res[0])
        self.ff = res[1] if not isinstance(res[1], Exception) else self.ff
        self.fomc = res[2] if not isinstance(res[2], Exception) else self.fomc
        self.ts = time.time()

    async def poll_day(self, day: date) -> List[Dict]:
        """Fast path for the release watcher: re-fetch one day now and store it."""
        rows = await fetch_day(day)
        self.days[day.isoformat()] = {"ts": time.time(), "rows": rows, "final": False}
        save(self.days)
        return rows
