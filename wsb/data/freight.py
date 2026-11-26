"""貨櫃運價：上海航運交易所 SCFI 綜合指數（每週五公布；2026-11-26）。

為什麼要有：長榮、陽明、萬海是台股權值與成交量都大的航運股，獲利幾乎直接跟著貨櫃運價走；本站只有航道監測（荷莫茲等），
沒有運價本身。來源：https://en.sse.net.cn/currentIndex?indexName=scfi（官方網頁自己用的 JSON，公開不需登入，
只有綜合指數有數字，分航線要登入，不讀）。每次讀到本週與上週兩個點，存進自己的歷史（data_cache/freight.json），
累積後才看得出 4 週、13 週的變化。雲端抓不到時用電腦端接力的 seed。"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict, List

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "freight.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "freight_seed.json"
URL = "https://en.sse.net.cn/currentIndex?indexName=scfi"
TTL = 6 * 3600
HDR = {"User-Agent": "Mozilla/5.0 (WallStreetSentinel research bot)"}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def parse(js: Dict) -> List[List]:
    """SSE JSON → [[date, value], …] for the composite index (last week and this week)."""
    d = (js or {}).get("data") or {}
    row = next((x for x in d.get("lineDataList") or [] if x.get("dataItemTypeName") == "SCFI_T"), None)
    if not row:
        return []
    out = []
    if d.get("lastDate") and row.get("lastContent") is not None:
        out.append([d["lastDate"], float(row["lastContent"])])
    if d.get("currentDate") and row.get("currentContent") is not None:
        out.append([d["currentDate"], float(row["currentContent"])])
    return out


def merge(hist: List[List], pts: List[List]) -> List[List]:
    """Pure: date-keyed union, newest value wins, sorted, last 10 years of weeks."""
    m = {x[0]: x for x in hist or []}
    m.update({x[0]: x for x in pts})
    return sorted(m.values())[-520:]


async def refresh(force: bool = False, now: float = 0) -> Dict:
    d = load()
    now = now or time.time()
    if not force and now - float(d.get("ts_try") or 0) < TTL:
        return d
    d["ts_try"] = now
    try:
        pts = parse(await http.get(URL, kind="json", headers=HDR, timeout=30, retries=1))
        if not pts:
            raise ValueError("SCFI composite not in the response")
        d.update(scfi=merge(d.get("scfi") or [], pts), ts=now, relayed=False)
        HEALTH.ok("freight")
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("freight", str(e) or type(e).__name__, every=TTL)
        log.info("SCFI: %s", e)
        seed = _seed()
        if seed.get("scfi"):
            d["scfi"] = merge(d.get("scfi") or [], seed["scfi"])
            if float(seed.get("ts") or 0) > float(d.get("ts") or 0):
                d.update(ts=seed["ts"], relayed=True)
    FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def _seed() -> Dict:
    try:
        return json.loads(SEED.read_text(encoding="utf-8")) if SEED.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def write_seed(path: Path) -> Dict:
    d = load()
    if not d.get("scfi") or d.get("relayed"):
        return {}
    out = {"ts": d.get("ts"), "scfi": d["scfi"]}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
