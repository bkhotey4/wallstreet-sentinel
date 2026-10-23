"""私募信貸壓力的原始資料（SEC，免費）。

  * Issuer tender offers (Schedule TO-I) filed per month, all issuers and those whose documents mention a "business
    development company".  Non-traded BDCs and interval funds can only return money to investors through these
    offers, so a rising count is a redemption wave arriving in the filings before it reaches prices.
  * Net asset value per share of listed BDCs (XBRL us-gaap:NetAssetValuePerShare, quarterly), so price ÷ NAV can be
    computed with each day's close.

Cached in data_cache/earn_private_credit.json (the CI build keeps data_cache/earn_* between runs)."""
from __future__ import annotations

import asyncio
import calendar
import json
import logging
import os
import time
from datetime import date
from typing import Dict, List, Optional

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH
from . import http
from .earnings_data import SEC_HDR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_private_credit.json"
EFTS = "https://efts.sec.gov/LATEST/search-index"
FORM = "SC TO-I"
BDC_Q = '"business development company"'


def cfg() -> Dict:
    d = {"bdcs": ["ARCC", "OBDC", "BXSL", "FSK", "MAIN", "GBDC", "HTGC"], "insurers": ["APO", "KKR", "CRBG", "BHF", "IAK"],
         "months": 60, "nav_ttl_h": 168, "tender_ttl_h": 24, "hot_pct": 85.0, "discount_pct": 15.0, "rel_days": 60}
    return {**d, **(SETTINGS.get("private_credit", {}) or {})}


def months_back(today: date, n: int) -> List[str]:
    """['YYYY-MM', …] oldest first, ending with the current month."""
    y, m, out = today.year, today.month, []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return out[::-1]


def nav_history(cf: Dict) -> List[List]:
    """companyfacts → [[period end, NAV/share]] from 10-Q / 10-K, one value per period end (the latest filing wins)."""
    units = (((cf or {}).get("facts") or {}).get("us-gaap") or {}).get("NetAssetValuePerShare", {}).get("units") or {}
    rows = units.get("USD/shares") or units.get("USD") or []
    by = {}
    for f in rows:
        if str(f.get("form", "")).split("/")[0] not in ("10-Q", "10-K") or f.get("val") is None or not f.get("end"):
            continue
        k = f["end"]
        if k not in by or str(f.get("filed", "")) >= str(by[k].get("filed", "")):
            by[k] = f
    return [[k, float(by[k]["val"])] for k in sorted(by) if float(by[k]["val"]) > 0]


def _total(js: Dict) -> Optional[int]:
    t = (((js or {}).get("hits") or {}).get("total") or {})
    v = t.get("value")
    return int(v) if v is not None else None


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", FILE.name, e)
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)


async def _tender_counts(old: Dict, today: date, n: int) -> Dict[str, Dict]:
    """Monthly counts; finished months already counted are kept, the current and previous month are recounted."""
    out = dict(old or {})
    recent = set(months_back(today, 2))
    for ym in months_back(today, n):
        if ym in out and ym not in recent:
            continue
        y, m = int(ym[:4]), int(ym[5:])
        rng = {"forms": FORM, "dateRange": "custom", "startdt": f"{ym}-01",
               "enddt": f"{ym}-{min(calendar.monthrange(y, m)[1], today.day if (y, m) == (today.year, today.month) else 31):02d}"}
        a = _total(await http.get(EFTS, params=rng, headers=SEC_HDR, timeout=30, retries=1))
        await asyncio.sleep(0.2)
        b = _total(await http.get(EFTS, params={**rng, "q": BDC_Q}, headers=SEC_HDR, timeout=30, retries=1))
        await asyncio.sleep(0.2)
        if a is not None:
            out[ym] = {"all": a, "bdc": b, "partial": (y, m) == (today.year, today.month), "day": today.day}
    return {k: out[k] for k in sorted(out)[-n:]}


async def refresh(today: Optional[date] = None, force: bool = False) -> Dict:
    from .edgar_holdings import ticker_map
    from .econcal import us_today
    c, d = cfg(), load()
    today = today or us_today()
    if force or time.time() - float(d.get("tender_ts", 0)) > float(c["tender_ttl_h"]) * 3600:
        try:
            d["tenders"] = await _tender_counts(d.get("tenders") or {}, today, int(c["months"]))
            d["tender_ts"] = time.time()
            HEALTH.ok("sec_tender", len(d["tenders"]), every=86400)
        except Exception as e:  # noqa: BLE001
            log.warning("SEC tender-offer counts failed: %s", e)
            HEALTH.fail("sec_tender", e, every=86400)
    navs = d.get("nav") or {}
    stale = [s for s in c["bdcs"] if force or time.time() - float((navs.get(s) or {}).get("ts", 0)) > float(c["nav_ttl_h"]) * 3600]
    if stale:
        try:
            tmap = await ticker_map()
            for s in stale:
                cik = (tmap.get(s) or {}).get("cik")
                if not cik:
                    continue
                try:
                    cf = await http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=40, retries=1)
                    navs[s] = {"ts": time.time(), "nav": nav_history(cf)}
                except Exception as e:  # noqa: BLE001
                    log.info("BDC NAV %s: %s", s, e)
                await asyncio.sleep(0.15)
        except Exception as e:  # noqa: BLE001
            log.warning("BDC NAV refresh failed: %s", e)
        d["nav"] = navs
    try:
        _save(d)
    except Exception as e:  # noqa: BLE001
        log.warning("private credit cache not saved: %s", e)
    return d
