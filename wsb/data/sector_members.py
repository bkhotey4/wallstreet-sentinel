"""產業簡報的成分股名單：11 檔 Select Sector SPDR ETF 的每日持股（State Street 公開的 xlsx），把財報季的每一家公司
對到它所屬的 GICS 產業。

Fetched at most once a day (cfg ttl_h) and cached in data_cache/earn_sector_members.json (the CI build keeps
data_cache/earn_* between runs), so a failed download keeps yesterday's list instead of emptying the page."""
from __future__ import annotations

import io
import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_sector_members.json"
URL = "https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-{t}.xlsx"
ETFS = ["XLK", "XLC", "XLY", "XLP", "XLV", "XLF", "XLI", "XLB", "XLE", "XLU", "XLRE"]


def cfg() -> Dict:
    return {"ttl_h": 24, **((SETTINGS.get("sector_brief") or {}).get("members") or {})}


def parse(raw: bytes) -> Tuple[Optional[str], List[List]]:
    """xlsx bytes → (as-of text, [[ticker, weight %], …]).  Header row is the one whose first two cells are Name / Ticker."""
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True).active
    asof, out, started = None, [], False
    for row in ws.iter_rows(values_only=True):
        a, b = (row + (None, None))[:2]
        if not started:
            if str(a or "").startswith("Holdings") and b:
                asof = str(b).replace("As of", "").strip()
            if str(a or "").strip() == "Name" and str(b or "").strip() == "Ticker":
                started = True
            continue
        if not b or not a:
            if out:
                break
            continue
        try:
            w = float(row[4])
        except (TypeError, ValueError, IndexError):
            continue
        t = str(b).strip().upper()
        if t and t != "-" and w > 0:
            out.append([t, round(w, 4)])
    return asof, out


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


async def refresh(force: bool = False) -> Dict:
    d = load()
    every = int(cfg()["ttl_h"] * 3600)
    if not force and d.get("ts") and time.time() - d["ts"] < every and len(d.get("sectors") or {}) == len(ETFS):
        return d
    sec, bad = dict(d.get("sectors") or {}), []
    for t in ETFS:
        try:
            raw = await http.get(URL.format(t=t.lower()), kind="bytes", timeout=40)
            asof, rows = parse(raw)
            if len(rows) < 10:
                raise ValueError(f"only {len(rows)} rows")
            sec[t] = {"asof": asof, "members": rows}
        except Exception as e:  # noqa: BLE001
            bad.append(f"{t}: {e if str(e) else type(e).__name__}")
    if len(bad) < len(ETFS):
        d = {"ts": time.time(), "sectors": sec}
        _save(d)
    if bad:
        log.warning("sector members: %s", "; ".join(bad[:4]))
        HEALTH.fail("sector_members", "; ".join(bad[:3]), every=every)
    else:
        HEALTH.ok("sector_members", sum(len(v["members"]) for v in sec.values()), every=every)
    return d


def sector_of(d: Dict) -> Dict[str, str]:
    """ticker → sector ETF (a ticker in two funds keeps the one where it weighs more).  BRK.B and BRK-B both map."""
    best: Dict[str, Tuple[str, float]] = {}
    for etf, v in (d.get("sectors") or {}).items():
        for t, w in v.get("members") or []:
            for k in {t, t.replace(".", "-"), t.replace("-", ".")}:
                if k not in best or w > best[k][1]:
                    best[k] = (etf, w)
    return {k: v[0] for k, v in best.items()}
