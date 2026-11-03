"""FOMC statement watcher: fetch the new statement, diff it against the previous one, let the AI read the tone shift.
The diff itself is deterministic (what words changed); only the interpretation uses the LLM."""
from __future__ import annotations

import difflib
import html as _html
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR
from . import econcal

log = logging.getLogger(__name__)


def decision_dates(page_html: str) -> List[date]:
    """All scheduled decision dates (last day of each meeting) on the Fed calendar page, ascending.  Shares
    econcal.parse_fomc, which skips notation votes and handles abbreviated cross-month meetings ("Oct/Nov 31-1")."""
    return [date.fromisoformat(m["date"]) for m in econcal.parse_fomc(page_html)]


def statement_url(d: date) -> str:
    return f"https://www.federalreserve.gov/newsevents/pressreleases/monetary{d:%Y%m%d}a.htm"


def extract_text(page_html: str) -> Optional[str]:
    """Plain text of the statement body (paragraphs only)."""
    paras = re.findall(r"<p[^>]*>(.*?)</p>", page_html, re.S | re.I)
    clean = []
    for p in paras:
        t = _html.unescape(re.sub(r"<[^>]+>", " ", p))
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) > 40:
            clean.append(t)
    body = [t for t in clean if "Committee" in t or "inflation" in t.lower()]
    return "\n".join(body) if len(body) >= 2 else None


def _sentences(t: str) -> List[str]:
    return [x.strip() for x in re.split(r"(?<=[.;])\s+", t.replace("\n", " ")) if x.strip()]


def diff(prev: str, new: str) -> Dict:
    a, b = _sentences(prev), _sentences(new)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    removed, added = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace"):
            removed += a[i1:i2]
        if op in ("insert", "replace"):
            added += b[j1:j2]
    ratio = sm.ratio()
    return {"removed": removed, "added": added, "similarity": ratio, "changed": bool(removed or added)}


def cache_path(d: date) -> Path:
    return DATA_DIR / f"fomc_{d:%Y%m%d}.txt"


async def fetch_statement(d: date) -> Optional[str]:
    p = cache_path(d)
    if p.exists():
        return p.read_text(encoding="utf-8")
    from . import http
    try:
        page = await http.get(statement_url(d), kind="text", retries=1)
    except Exception as e:  # noqa: BLE001
        log.info("FOMC statement %s not available yet: %s", d, str(e)[:80])
        return None
    txt = extract_text(page)
    if txt:
        p.write_text(txt, encoding="utf-8")
    return txt


async def latest_pair(today: Optional[date] = None, max_age_days: int = 3):
    """(date, new_text, prev_date, prev_text) for the most recent decision within `max_age_days`, else None."""
    today = today or date.today()
    ds = [date.fromisoformat(m["date"]) for m in await econcal.fomc_meetings()]
    ds = [d for d in ds if d <= today]
    if len(ds) < 2 or (today - ds[-1]).days > max_age_days:
        return None
    new = await fetch_statement(ds[-1])
    if not new:
        return None
    prev = await fetch_statement(ds[-2])
    return ds[-1], new, ds[-2], prev
