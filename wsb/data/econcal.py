"""US economic calendar (財經日曆): release dates, consensus, previous and actual values.

Sources (all public, no key):
  * Nasdaq economic calendar  api.nasdaq.com/api/calendar/economicevents?date=D
      - quirk: the response for ?date=D lists the events of D-1 (verified against ISM = first business day, NFP Fridays and
        the Fed's own meeting calendar), so the events of day X are fetched with ?date=X+1
      - quirk: times have been in a fixed UTC-4 clock all year (an 08:30 EST release shows as 09:30); the offset is
        re-checked per day from anchor releases with a fixed US-Eastern time (clock_offset), UTC-4 when nothing to check
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
_MON3 = {m[:3].lower(): i for m, i in _MONTHS.items()}


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


DEFAULT_OFF_MIN = -240          # the clock Nasdaq has used so far: fixed UTC-4 (verified in summer and in January)
# releases whose US-Eastern clock time never changes → used to check which UTC offset Nasdaq's clock had on a given day
ANCHOR_ET = {"cpi": (8, 30), "core cpi": (8, 30), "ppi": (8, 30), "core ppi": (8, 30), "nonfarm payrolls": (8, 30),
             "retail sales": (8, 30), "core retail sales": (8, 30), "gdp": (8, 30), "initial jobless claims": (8, 30),
             "ism manufacturing pmi": (10, 0), "ism non-manufacturing pmi": (10, 0), "jolts job openings": (10, 0),
             "michigan consumer sentiment": (10, 0)}


def _hm(hhmm) -> Optional[Tuple[int, int]]:
    m = re.match(r"(\d{1,2}):(\d{2})", clean(hhmm))
    return (int(m.group(1)), int(m.group(2))) if m else None


def _utc(day: date, hhmm: str, off_min: int = DEFAULT_OFF_MIN) -> Optional[str]:
    """Nasdaq clock (UTC offset `off_min` minutes; fixed UTC-4 unless the day's anchors say otherwise) → ISO UTC timestamp."""
    hm = _hm(hhmm)
    if not hm:
        return None
    t = datetime(day.year, day.month, day.day, hm[0], hm[1], tzinfo=timezone(timedelta(minutes=off_min)))
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def clock_offset(rows: List[Dict], day: date) -> int:
    """UTC offset (minutes) of the Nasdaq clock on `day`, inferred from anchor releases with a known US-Eastern time:
    offset = shown clock − true UTC time of that release (zoneinfo handles EST/EDT).  Every anchor of the day must agree
    and the result must be a plausible US offset (−4 h / −5 h); otherwise the long-standing fixed UTC−4 is kept.
    This keeps release times right if Nasdaq switches its clock with US daylight saving (2026-11-01)."""
    from zoneinfo import ZoneInfo
    seen = set()
    for r in rows:
        et = ANCHOR_ET.get(clean(r.get("eventName") if "eventName" in r else r.get("name")).lower())
        hm = _hm(r.get("gmt", ""))
        if not et or not hm:
            continue
        true_utc = datetime(day.year, day.month, day.day, et[0], et[1], tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc)
        shown = datetime(day.year, day.month, day.day, hm[0], hm[1], tzinfo=timezone.utc)
        seen.add(int(round((shown - true_utc).total_seconds() / 60)))
    if len(seen) == 1 and next(iter(seen)) in (-240, -300):
        return next(iter(seen))
    return DEFAULT_OFF_MIN


def parse_nasdaq(js: Dict, day: date) -> List[Dict]:
    """US rows of one Nasdaq response (already the events of `day`)."""
    rows = ((js or {}).get("data") or {}).get("rows") or []
    us = [r for r in rows if clean(r.get("country")) == "United States" and clean(r.get("eventName"))]
    off = clock_offset(us, day)
    return [{"name": clean(r.get("eventName")), "utc": _utc(day, r.get("gmt", ""), off), "actual": clean(r.get("actual")),
             "cons": clean(r.get("consensus")), "prev": clean(r.get("previous"))} for r in us]


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


EMPTY_MAX = 5                    # an empty answer for a weekday is retried this many times before it is accepted as final


def empty_wait(n: int) -> float:
    """Back-off before re-trying a weekday that came back empty for the n-th time: 30 min, 1 h, 2 h, 4 h, then 6 h."""
    return min(1800.0 * 2 ** max(0, min(int(n), 10) - 1), 6 * 3600.0)


def _due(day: date, rec: Optional[Dict], today: date, now: float) -> bool:
    """How often a day is re-fetched: final days once, the live window often, the far future twice a day."""
    if rec is None:
        return True
    age = now - float(rec.get("ts", 0))
    d = (day - today).days
    if d < -3:
        if rec.get("final"):
            return False
        return age > empty_wait(rec["empty"]) if rec.get("empty") else True
    if d <= 7:
        return age > float(cfg().get("live_refresh_s", 1500))
    return age > 12 * 3600


async def _fetch(day: date) -> Tuple[List[Dict], int]:
    """(US rows, number of raw rows of any country) — the raw count tells an empty/null answer from a quiet US day."""
    js = await http.get("https://api.nasdaq.com/api/calendar/economicevents", params={"date": (day + timedelta(days=1)).isoformat()},
                        headers=NQ_HDR, timeout=20, retries=1)
    return parse_nasdaq(js, day), len(((js or {}).get("data") or {}).get("rows") or [])


async def fetch_day(day: date) -> List[Dict]:
    return (await _fetch(day))[0]


def store_day(days: Dict[str, Dict], day: date, rows: List[Dict], n_raw: int, today: date) -> Dict:
    """Write one fetched day.  An HTTP-200 answer with no rows at all for a weekday is a feed hiccup, not a quiet day:
    the previous rows are kept and the day stays non-final with a try counter (re-fetched with back-off, see _due),
    so a glitch can never be frozen into the history as an empty final day; after EMPTY_MAX tries it is accepted."""
    k = day.isoformat()
    old = days.get(k) or {}
    final = (today - day).days > 3
    if n_raw == 0 and day.weekday() < 5:
        n = int(old.get("empty", 0)) + 1
        rec = {"ts": time.time(), "rows": old.get("rows") or [], "final": final and n >= EMPTY_MAX, "empty": n}
    else:
        rec = {"ts": time.time(), "rows": rows, "final": final}
    days[k] = rec
    return rec


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
    queue += [d for d in hist if d.weekday() < 5 and _due(d, days.get(d.isoformat()), today, now)][: int(c.get("backfill_per_run", 80))]
    n_ok = n_err = 0
    for d in queue:
        if time.time() - t0 > budget:
            break
        try:
            rows, n_raw = await _fetch(d)
            store_day(days, d, rows, n_raw, today)
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
    pending = sum(1 for d in hist if d.weekday() < 5 and not (days.get(d.isoformat()) or {}).get("final"))
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
    """Scheduled meetings from the Fed's calendar page.  Cross-month meetings ("Apr/May" 30-1, "Oct/Nov" 31-1) start in
    the first month and end in the second; months match on their first three letters; lines that are not a scheduled
    meeting ("22 (notation vote)", "unscheduled") are skipped because the day cell must be just "d" or "d-d", plus "*"."""
    out = []
    for ym in re.finditer(r"(\d{4}) FOMC Meetings(.*?)(?=\d{4} FOMC Meetings|$)", page_html, re.S):
        year, block = int(ym.group(1)), ym.group(2)
        for m in re.finditer(r'fomc-meeting__month[^>]*>\s*<strong>([A-Za-z/. ]+)</strong>.*?'
                             r'fomc-meeting__date[^>]*>([^<]+)<', block, re.S):
            mons = [_MON3.get(x.strip()[:3].lower()) for x in m.group(1).split("/")]
            raw = re.sub(r"\s+", "", clean(m.group(2)))
            dm = re.match(r"^(\d+)(?:-(\d+))?(\*?)$", raw)
            if not dm or not mons or any(x is None for x in mons):
                continue
            d0, d1 = int(dm.group(1)), int(dm.group(2) or dm.group(1))
            try:
                start, end = date(year, mons[0], d0), date(year, mons[-1], d1)
            except ValueError:
                continue
            if end < start:
                continue
            out.append({"date": end.isoformat(), "sep": bool(dm.group(3)), "start": start.isoformat()})
    return sorted({x["date"]: x for x in out}.values(), key=lambda x: x["date"])


def _fomc_cached() -> List[Dict]:
    try:
        return json.loads(_FOMC_FILE.read_text(encoding="utf-8")) if _FOMC_FILE.exists() else []
    except Exception:  # noqa: BLE001
        return []


async def fomc_meetings() -> List[Dict]:
    try:
        if _FOMC_FILE.exists() and time.time() - _FOMC_FILE.stat().st_mtime < 7 * 86400:
            return json.loads(_FOMC_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    try:
        page = await http.get("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", kind="text", timeout=25, retries=1)
        out = parse_fomc(page)
        if not out:                                  # page layout changed → keep the last good list
            HEALTH.fail("fomc_dates", RuntimeError("Fed calendar page parsed to no meetings"), every=86400)
            return _fomc_cached()
        _FOMC_FILE.write_text(json.dumps(out), encoding="utf-8")
        HEALTH.ok("fomc_dates", len(out), every=86400)
        return out
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("fomc_dates", e, every=86400)
        return _fomc_cached()


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
        """Fast path for the release watcher: re-fetch one day now and store it (an empty answer keeps the old rows)."""
        rows, n_raw = await _fetch(day)
        rec = store_day(self.days, day, rows, n_raw, us_today())
        rec["final"] = False
        save(self.days)
        return rec["rows"]
