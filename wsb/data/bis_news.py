"""美國商務部工業安全局（BIS）官方新聞稿：出口管制「宣布」的當下就知道（2026-11-17）。

為什麼要有：聯邦公報（政府做了什麼卡）只收「正式刊登」的文件，BIS 常常先發新聞稿、幾天到幾週後才刊登。
11/16 美東 07:48（BIS 網站記錄的建立時間，09:21 最後修改，都在美股開盤前）BIS 發布限制遠端使用美國先進 AI 技術的規則，
本站沒有任何通知，使用者問了才知道。

來源：https://www.bis.gov/news-updates（robots.txt 允許所有程式讀取）。頁面裡的 Next.js 資料（__NEXT_DATA__）
直接帶有新聞稿清單（標題、網址、建立時間），不用解析畫面。商務部本部與 USTR 網站有防機器人驗證，不讀（不繞過）。
主題與「先動的資產」沿用 fed_register.topic；執法和解、罰款不算政策，不通知。快取 data_cache/econ_bis.json。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_bis.json"
PAGE = "https://www.bis.gov/news-updates"
BASE = "https://www.bis.gov"
TTL = 1800
KEEP_DAYS = 60
FRESH_S = 30 * 3600                        # first seen within this many hours → alert
ENFORCE = re.compile(r"settlement|penalty|to pay|pleads? guilty|sentenced|indict|charged|denial order|temporary denial", re.I)
HDR = {"User-Agent": "Mozilla/5.0 (WallStreetSentinel research bot)"}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def parse_page(html: str) -> List[Dict]:
    """The news page's __NEXT_DATA__ → [{id, title, url, ts}] (press releases, newest first)."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    try:
        props = (json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}
    except ValueError:
        return []
    out = []
    for x in props.get("pressReleaseTeasers") or []:
        path, title = x.get("path"), (x.get("title") or "").strip()
        # the agency's own release time (publishedOn) first; the CMS 'created' stamp only when it is missing
        ts = next((x[k]["timestamp"] for k in ("publishedOn", "created") if isinstance(x.get(k), dict) and x[k].get("timestamp")), None)
        if path and title and ts:
            out.append({"id": path, "title": title, "url": BASE + path, "ts": int(ts)})
    return sorted(out, key=lambda r: -r["ts"])


def classify(item: Dict) -> Optional[Dict]:
    """Topic + first-moving asset (fed_register.topic), or None for enforcement cases and off-topic releases."""
    from . import fed_register as FR
    if ENFORCE.search(item["title"]):
        return None
    t = FR.topic(item["title"])
    return {**item, **t} if t else None


async def refresh(force: bool = False, now: float = 0) -> Dict:
    d = load()
    now = now or time.time()
    if not force and now - float(d.get("ts_try") or 0) < TTL:
        return d
    d["ts_try"] = now
    try:
        html = await http.get(PAGE, kind="text", headers=HDR, timeout=30, retries=1)
        items = parse_page(html)
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("bis_news", str(e) or type(e).__name__, every=TTL)
        log.info("BIS news: %s", e)
        items = None
    if items:
        seen = {x["id"]: x for x in d.get("items") or []}
        for x in items:
            old = seen.get(x["id"])
            x["first_seen"] = old.get("first_seen") if old else now
            seen[x["id"]] = {**(old or {}), **x}
        keep_from = now - KEEP_DAYS * 86400
        d["items"] = sorted((x for x in seen.values() if x["ts"] >= keep_from), key=lambda r: -r["ts"])
        d["ts"] = now
        HEALTH.ok("bis_news", len(items), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def alerts(d: Dict, now: float) -> List[Dict]:
    """Policy press releases released and first seen within the last 30 hours."""
    out = []
    for x in d.get("items") or []:
        if now - x["ts"] > FRESH_S or now - float(x.get("first_seen") or now) > FRESH_S:
            continue
        c = classify(x)
        if c:
            out.append({"key": "bis:" + x["id"], "item": c})
    return out
