"""研究機構新聞稿：TrendForce（集邦科技）press center（2026-11-26）。

為什麼要有：11/19 TrendForce 發布「中國雲端業者削減 2027 企業級 SSD 訂單、多過北美加單，NAND 明年起跌價」，
11/20 Sandisk 跌逾 14%、美光約跌 10%，11/25 第二份報告後 Sandisk 再跌約 12%。本站一週才寫一次產業筆記，
沒有任何研究機構來源，Sandisk 也不在追蹤名單裡，所以直到使用者 11/26 拿影片標題來問才補上。

來源：https://www.trendforce.com/presscenter/news（公開新聞稿列表，含日期與標題；每篇新聞稿的 meta description 是導言）。
每份報告依標題關鍵字對到產業與本站追蹤的相關股票，卡片再用收盤價算「報告後第一個交易日」的漲跌，
讓讀者看到這份報告市場有沒有在意。快取 data_cache/research_press.json；雲端抓不到時用電腦端接力的 seed。"""
from __future__ import annotations

import html as _html
import json
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "research_press.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "research_press_seed.json"
LIST = "https://www.trendforce.com/presscenter/news"
BASE = "https://www.trendforce.com/"
TTL = 3 * 3600
KEEP = 40
HDR = {"User-Agent": "Mozilla/5.0 (WallStreetSentinel research bot)"}

# title keyword → (產業, 本站追蹤的相關代號); only symbols in the tracked universe are used by the card
TOPICS = (
    (re.compile(r"NAND|SSD|Flash", re.I), "記憶體（NAND／SSD）", ["SNDK", "MU", "WDC", "2337.TW"]),
    (re.compile(r"DRAM|HBM", re.I), "記憶體（DRAM／HBM）", ["MU", "2408.TW", "2344.TW"]),
    (re.compile(r"Memory", re.I), "記憶體（整體）", ["MU", "SNDK", "2408.TW", "2344.TW", "2337.TW"]),
    (re.compile(r"HDD|Hard Disk", re.I), "硬碟", ["STX", "WDC"]),
    (re.compile(r"Foundr|Wafer|Advanced Packaging|CoWoS", re.I), "晶圓代工與先進封裝", ["TSM", "2330.TW"]),
    (re.compile(r"AI Server|\bServers?\b|\bGPUs?\b|Data Cent", re.I), "AI 伺服器與雲端", ["NVDA", "SMCI", "DELL", "2317.TW", "2382.TW"]),
    (re.compile(r"PCB|Glass Fiber|CCL|Substrate", re.I), "PCB 與材料", ["2383.TW", "3037.TW"]),
    (re.compile(r"OLED|LCD|Panel|Monitor|Display|LED", re.I), "面板與顯示器", ["2409.TW", "3481.TW"]),
    (re.compile(r"Smartphone|Foldable|iPhone", re.I), "手機", ["AAPL", "2454.TW"]),
    (re.compile(r"\bNEV|\bEV\b|Electric Vehicle|BEV|Battery", re.I), "電動車與電池", ["TSLA"]),
    (re.compile(r"Notebook|Laptop|\bPC\b", re.I), "筆電與 PC", ["DELL", "2357.TW"]),
)
DOWN = re.compile(r"Declin|Fall|Drop|Cut|Weigh|Slow|Weak|Shrink|Oversupply|Downturn|Correct", re.I)
UP = re.compile(r"Rise|Rising|Increase|Surge|\bGrows?\b|Drive[sn]? Up|Raise|Boost|Tight|Shortage|Double|Record", re.I)


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def parse_list(page: str) -> List[Dict]:
    """Press-center page → [{id, date (YYYY-MM-DD), title, url}], newest first, one per release."""
    out, seen = [], set()
    for m in re.finditer(r'href="(?:https://www\.trendforce\.com)?/(presscenter/news/(\d{4})(\d\d)(\d\d)-(\d+)\.html)"[^>]*>(.*?)</a>', page or "", re.S):
        path, title = m.group(1), _text(m.group(6))
        if not title or path in seen:
            continue
        seen.add(path)
        out.append({"id": m.group(5), "date": f"{m.group(2)}-{m.group(3)}-{m.group(4)}", "title": title, "url": BASE + path})
    return sorted(out, key=lambda r: (r["date"], r["id"]), reverse=True)


def parse_lead(page: str) -> Optional[str]:
    m = re.search(r'<meta (?:name|property)="(?:og:)?description" content="([^"]*)"', page or "")
    if m and len(_text(m.group(1))) > 40:
        return _text(m.group(1))[:600]
    p = re.search(r"<p[^>]*>((?:(?!</p>).){80,}?)</p>", page or "", re.S)
    return _text(p.group(1))[:600] if p else None


def classify(title: str) -> Dict:
    """Pure: the report's main industry (first matching topic only — 11-26: a memory report that mentions CSPs was also
    filed under AI servers, so Quanta's tariff-day jump read as a reaction to it) + its symbols + the title's direction."""
    zh, syms = [], []
    for rx, name, ss in TOPICS:
        if rx.search(title):
            zh, syms = [name], list(ss)
            break
    d = "down" if DOWN.search(title) and not UP.search(title) else ("up" if UP.search(title) and not DOWN.search(title) else None)
    return {"topics": zh, "syms": syms, "dir": d}


async def refresh(force: bool = False, now: float = 0) -> Dict:
    d = load()
    now = now or time.time()
    if not force and now - float(d.get("ts_try") or 0) < TTL:
        return d
    d["ts_try"] = now
    try:
        items = parse_list(await http.get(LIST, kind="text", headers=HDR, timeout=30, retries=1))
        if not items:
            raise ValueError("press list parsed empty (page layout changed?)")
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("research_press", str(e) or type(e).__name__, every=TTL)
        log.info("research press: %s", e)
        seed = _seed()
        if seed and float(seed.get("ts") or 0) > float(d.get("ts") or 0):
            d.update(items=seed.get("items") or [], ts=seed.get("ts"), relayed=True)
        FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return d
    old = {x["id"]: x for x in d.get("items") or []}
    out = []
    for it in items[:KEEP]:
        x = {**old.get(it["id"], {}), **it, **classify(it["title"])}
        if not x.get("lead"):
            try:
                x["lead"] = parse_lead(await http.get(it["url"], kind="text", headers=HDR, timeout=30, retries=0))
            except Exception as e:  # noqa: BLE001
                log.info("research press lead %s: %s", it["url"], e)
        out.append(x)
    d.update(items=out, ts=now, relayed=False)
    HEALTH.ok("research_press")
    FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def _seed() -> Dict:
    try:
        return json.loads(SEED.read_text(encoding="utf-8")) if SEED.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def write_seed(path: Path) -> Dict:
    """PC → cloud relay (tools.relay_push): the PC's cleanly fetched list, with the PC's own fetch time."""
    d = load()
    if not d.get("items") or d.get("relayed"):
        return {}
    out = {"ts": d.get("ts"), "items": d["items"]}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
