"""記憶體現貨價：DRAMeXchange（TrendForce 旗下）首頁公開的現貨報價表（2026-11-26）。

為什麼要有：TrendForce 11/19 的報告說 NAND 現貨價近期已修正逾 20%，接著合約價預測轉成跌價，Sandisk、美光大跌。
現貨通常比合約價早反應，但本站沒有任何記憶體報價資料，只靠一週一次的 AI 筆記轉述。

來源：https://www.dramexchange.com/ 首頁的 DRAM／模組／Flash／GDDR／Wafer 現貨表（公開顯示，不需登入）。
每張表有自己的「Last Update」：DRAM 現貨每天更新，模組與晶圓等通常一週一次，所以每一列都標自己的更新日（不借日期）。
本站從 2026-11-26 開始每天存一筆歷史（data_cache/mem_spot.json），累積後才算得出 30 天變化；雲端抓不到時用電腦端接力的 seed。"""
from __future__ import annotations

import html as _html
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "mem_spot.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "mem_spot_seed.json"
PAGE = "https://www.dramexchange.com/"
TTL = 3 * 3600
HDR = {"User-Agent": "Mozilla/5.0 (WallStreetSentinel research bot)"}
TABLES = {"DRAM Spot Price": "DRAM 現貨", "Module Spot Price": "記憶體模組", "Flash Spot Price": "Flash 現貨",
          "GDDR Spot Price": "顯示記憶體 GDDR", "Wafer Spot Price": "NAND 晶圓"}
KEEP_DAYS = 400


def _t(s: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def _num(s: str) -> Optional[float]:
    try:
        return float(str(s).replace(",", "").replace("%", "").strip())
    except ValueError:
        return None


def _upd(s: str) -> Optional[str]:
    """'Last Update: Nov.26 2026 18:10 (GMT+8)' → '2026-11-26 18:10'."""
    m = re.search(r"([A-Z][a-z]{2})\.?\s*(\d{1,2}),?\s+(\d{4})\s+(\d{1,2}:\d{2})", s or "")
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)} {m.group(4)}", "%b %d %Y %H:%M").strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return None


def parse(page: str) -> Dict[str, Dict]:
    """Homepage → {table zh: {"en", "upd", "items": {item: {"avg", "chg"}}}}.  A title table ('X Spot Price' + Last Update)
    is followed by its item table (Item … Session Average, Session/Average Change)."""
    out: Dict[str, Dict] = {}
    cur = None
    for tb in re.findall(r"<table.*?</table>", page or "", re.S):
        rows = [[_t(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)] for r in re.findall(r"<tr.*?</tr>", tb, re.S)]
        rows = [r for r in rows if r]
        if not rows:
            continue
        head = rows[0]
        if head[0] in TABLES:
            cur = {"en": head[0], "upd": _upd(" ".join(head[1:])), "items": {}}
            out[TABLES[head[0]]] = cur
            continue
        if cur is not None and head[0] == "Item" and not cur["items"]:
            try:
                ia = next(i for i, h in enumerate(head) if "Average" in h and "Change" not in h)
                ic = next(i for i, h in enumerate(head) if "Change" in h)
            except StopIteration:
                continue
            for r in rows[1:]:
                if len(r) > max(ia, ic) and _num(r[ia]) is not None:
                    cur["items"][r[0]] = {"avg": _num(r[ia]), "chg": _num(r[ic])}
            cur = None
    return {k: v for k, v in out.items() if v["items"]}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def add_history(d: Dict, snap: Dict[str, Dict]) -> Dict:
    """Pure: one point per item per table update date (the table's own Last Update), never the fetch day."""
    hist = d.setdefault("hist", {})
    for tz, t in snap.items():
        day = (t.get("upd") or "")[:10]
        if not day:
            continue
        for item, v in t["items"].items():
            h = hist.setdefault(f"{tz}|{item}", [])
            if not h or h[-1][0] < day:
                h.append([day, v["avg"]])
            elif h[-1][0] == day:
                h[-1][1] = v["avg"]
            del h[:-KEEP_DAYS]
    return d


async def refresh(force: bool = False, now: float = 0) -> Dict:
    d = load()
    now = now or time.time()
    if not force and now - float(d.get("ts_try") or 0) < TTL:
        return d
    d["ts_try"] = now
    try:
        snap = parse(await http.get(PAGE, kind="text", headers=HDR, timeout=30, retries=1))
        if not snap:
            raise ValueError("no price tables parsed (page layout changed?)")
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("mem_spot", str(e) or type(e).__name__, every=TTL)
        log.info("memory spot: %s", e)
        seed = _seed()
        if seed.get("snap") and float(seed.get("ts") or 0) > float(d.get("ts") or 0):
            d.update(snap=seed["snap"], ts=seed["ts"], relayed=True)
            for k, h in (seed.get("hist") or {}).items():          # the PC's history fills days this cache missed
                mine = {x[0]: x for x in d.setdefault("hist", {}).get(k, [])}
                mine.update({x[0]: x for x in h})
                d["hist"][k] = sorted(mine.values())[-KEEP_DAYS:]
        FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return d
    d.update(snap=snap, ts=now, relayed=False)
    add_history(d, snap)
    HEALTH.ok("mem_spot")
    FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def _seed() -> Dict:
    try:
        return json.loads(SEED.read_text(encoding="utf-8")) if SEED.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def write_seed(path: Path) -> Dict:
    d = load()
    if not d.get("snap") or d.get("relayed"):
        return {}
    out = {"ts": d.get("ts"), "snap": d["snap"], "hist": d.get("hist") or {}}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
