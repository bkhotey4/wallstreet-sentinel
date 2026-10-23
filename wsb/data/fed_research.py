"""Two free Federal Reserve research series the literature review ranked highest (學術研究 page):

  * Excess Bond Premium (Gilchrist & Zakrajšek 2012) — monthly CSV from the Board: date, gz_spread, ebp, est_prob
    (staff model, probability of a recession within 12 months).  Past values are revised as balance-sheet data arrive,
    so every fetch also records what the newest month said ON THAT DAY (vintages) — the site's own real-time record.
  * Market-based probabilities (Minneapolis Fed) — weekly option-implied distribution of the S&P 500 six and twelve
    months out: probability of a ≥ 20 % fall / rise, 10th/50th/90th percentiles, skew.  Risk-neutral probabilities,
    which overstate real-world odds of a fall (investors pay for crash insurance).

Cached in data_cache/econ_fedres.json (the CI build keeps econ_*), fetched at most once a day."""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_fedres.json"
EBP_URL = "https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv"
MPD_URL = "https://www.minneapolisfed.org/-/media/files/banking/mpd/mpd_stats.csv"
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research)"}
TTL = 20 * 3600


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", FILE.name, e)
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)


def parse_ebp(text: str) -> List[List]:
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        try:
            rows.append([r["date"][:7], round(float(r["gz_spread"]), 4), round(float(r["ebp"]), 4), round(float(r["est_prob"]) * 100, 2)])
        except (KeyError, TypeError, ValueError):
            continue
    return rows


def parse_mpd(text: str, markets=("sp6m", "sp12m")) -> Dict[str, List[List]]:
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.replace('"', "").startswith("market,")), None)   # header is quoted
    out: Dict[str, List[List]] = {m: [] for m in markets}
    if start is None:
        return out
    for r in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
        m = r.get("market")
        if m not in out:
            continue
        try:
            d = datetime.strptime(r["idt"], "%m/%d/%Y").strftime("%Y-%m-%d")
            out[m].append([d, round(float(r["prDec"]) * 100, 2), round(float(r["prInc"]) * 100, 2), float(r["p10"]), float(r["p50"]),
                           float(r["p90"]), float(r["skew"]), float(r["lg_change_decr"])])
        except (KeyError, TypeError, ValueError):
            continue
    for m in out:
        out[m].sort()
    return out


async def refresh(force: bool = False) -> Dict:
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts", 0)) < TTL and d.get("ebp") and d.get("mpd"):
        return d
    bad = []
    try:
        rows = parse_ebp(await http.get(EBP_URL, kind="text", headers=UA, timeout=40))
        if len(rows) < 100:
            raise ValueError(f"only {len(rows)} rows")
        d["ebp"] = rows
        vint = d.setdefault("ebp_vintages", {})
        vint[datetime.utcnow().strftime("%Y-%m-%d")] = rows[-1]          # what the newest month said today
        d["ebp_vintages"] = dict(sorted(vint.items())[-800:])
    except Exception as e:  # noqa: BLE001
        bad.append(f"ebp: {e if str(e) else type(e).__name__}")
    try:
        mp = parse_mpd(await http.get(MPD_URL, kind="text", headers=UA, timeout=60))
        if not mp.get("sp6m"):
            raise ValueError("no S&P rows")
        d["mpd"] = mp
    except Exception as e:  # noqa: BLE001
        bad.append(f"mpd: {e if str(e) else type(e).__name__}")
    if len(bad) < 2:
        d["ts"] = now
        _save(d)
    if bad:
        log.warning("fed research data: %s", "; ".join(bad))
        HEALTH.fail("fed_research", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("fed_research", len(d.get("ebp") or []), every=TTL)
    return d
