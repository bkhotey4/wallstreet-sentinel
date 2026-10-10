"""Geopolitical news heat by theatre (Google News RSS headlines, keyword-graded) + market transmission.

Headlines are graded by keywords only (no AI): L3 escalation words, L2 military / sanction activity, L1 diplomacy.
A theatre's heat = weighted count over the last 72 hours, compared with ITS OWN history (median of the previous
days stored here), so an ongoing war does not read as "critical" every day — what counts is the change."""
from __future__ import annotations

import asyncio
import calendar
import json
import logging
import re
import statistics
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import quote_plus

from ..config import DATA_DIR
from . import http

log = logging.getLogger(__name__)
F_GEO = DATA_DIR / "sinfo_geo.json"


def _gn(q: str, zh: bool = False) -> str:
    loc = "hl=zh-TW&gl=TW&ceid=TW:zh-Hant" if zh else "hl=en-US&gl=US&ceid=US:en"
    return f"https://news.google.com/rss/search?q={quote_plus(q)}&{loc}"


THEATRES = {
    "taiwan": ("台海／印太", "Taiwan Strait / Indo-Pacific",
               [_gn("(\"Taiwan Strait\" OR PLA OR \"South China Sea\" OR \"China coast guard\") when:3d"),
                _gn("(台海 OR 共軍 OR 解放軍 OR 南海) when:3d", zh=True)],
               ["^TWII", "TWD=X", "EWT"]),
    "europe": ("俄烏／北約", "Russia-Ukraine / NATO",
               [_gn("(Ukraine OR NATO) (Russia OR Russian) (missile OR drone OR attack OR offensive OR troops) when:3d")],
               ["^STOXX50E", "BZ=F", "NG=F"]),
    "mideast": ("中東／紅海", "Middle East / Red Sea",
                [_gn("(Israel OR Iran OR Houthi OR \"Red Sea\" OR Hezbollah OR \"Strait of Hormuz\") (strike OR missile OR attack OR navy) when:3d")],
                ["BZ=F", "GC=F", "^VIX"]),
    "korea": ("朝鮮半島", "Korean Peninsula",
              [_gn("\"North Korea\" (missile OR launch OR nuclear OR artillery) when:3d")],
              ["^KS11", "KRW=X"]),
}
L3 = ["invasion", "invades", "invaded", "blockade", "declares war", "declared war", "article 5", "nuclear test", "nuclear strike",
      "full-scale", "ground offensive", "closes strait", "封鎖", "登陸", "宣戰", "入侵", "核試", "全面戰爭"]
L2 = ["missile", "missiles", "airstrike", "airstrikes", "air strike", "drone attack", "drones", "strikes", "struck", "live-fire", "live fire",
      "drills", "military exercise", "war games", "scramble", "scrambled", "incursion", "shot down", "sanctions", "warship", "warships",
      "clash", "clashes", "killed", "attack", "attacks", "軍演", "實彈", "飛彈", "導彈", "空襲", "擊落", "越界", "制裁", "衝突", "演習", "攻擊"]
L1 = ["tension", "tensions", "talks", "warns", "warning", "condemns", "ceasefire", "diplomat", "diplomatic", "protest",
      "警告", "談判", "停火", "抗議", "緊張"]
W = {3: 5.0, 2: 2.0, 1: 0.5, 0: 0.0}


def _has(t: str, words: List[str]) -> List[str]:
    out = []
    for w in words:
        pat = rf"\b{re.escape(w)}\b" if w.isascii() else re.escape(w)
        if re.search(pat, t):
            out.append(w)
    return out


def grade(title: str) -> tuple:
    t = title.lower()
    for lv, words in ((3, L3), (2, L2), (1, L1)):
        h = _has(t, words)
        if h:
            return lv, h[:3]
    return 0, []


def heat(items: List[Dict], now: Optional[float] = None, hours: int = 72) -> float:
    now = now or time.time()
    return round(sum(W[i["lv"]] for i in items if now - i["ts"] <= hours * 3600), 1)


def level(score: float, hist: List[float]) -> Dict:
    """Relative to the theatre's own recent history: ratio to the median of earlier days."""
    base = statistics.median(hist) if len(hist) >= 5 else None
    r = score / base if base and base > 0 else None
    if r is None:
        k = 0 if score < 15 else 1 if score < 40 else 2
    else:
        k = 0 if r < 1.3 else 1 if r < 1.8 else 2 if r < 2.5 else 3
    lab = [("平穩", "Calm"), ("升溫", "Rising"), ("緊張", "Tense"), ("高度緊張", "Elevated")][k]
    return {"k": k, "label": lab[0], "label_en": lab[1], "ratio": r, "base": base}


async def _feed(url: str) -> List[Dict]:
    import feedparser
    raw = await http.get(url, kind="bytes", retries=1, timeout=20)
    parsed = await asyncio.to_thread(feedparser.parse, raw)
    out = []
    for e in parsed.entries[:60]:
        title = re.sub(r"\s+", " ", (e.get("title") or "")).strip()
        if not title:
            continue
        st = e.get("published_parsed") or e.get("updated_parsed")
        out.append({"t": title, "link": e.get("link", ""), "ts": calendar.timegm(st) if st else time.time()})
    return out


def _load() -> Dict:
    try:
        if F_GEO.exists():
            return json.loads(F_GEO.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    return {}


def _save(d: Dict) -> None:
    try:
        tmp = F_GEO.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        tmp.replace(F_GEO)
    except Exception as e:  # noqa: BLE001
        log.warning("geo cache not saved: %s", e)


def assemble(raw: Dict[str, List[Dict]], cache: Dict, now: Optional[float] = None) -> Dict:
    """raw = {theatre: headlines}. Updates cache['days'] (one heat value per theatre per UTC day) and returns the view."""
    now = now or time.time()
    day = datetime.fromtimestamp(now, tz=timezone.utc).date().isoformat()
    days = cache.setdefault("days", {})
    out = {}
    for th, items in raw.items():
        seen, graded = set(), []
        for it in sorted(items, key=lambda x: -x["ts"]):
            key = re.sub(r"[^a-z0-9一-鿿]+", "", it["t"].lower())[:80]
            if key in seen or now - it["ts"] > 72 * 3600:
                continue
            seen.add(key)
            lv, hits = grade(it["t"])
            graded.append({**it, "lv": lv, "hits": hits})
        sc = heat(graded, now)
        hist = [v[th] for d, v in sorted(days.items()) if d < day and th in v][-30:]
        days.setdefault(day, {})[th] = sc
        out[th] = {"score": sc, "level": level(sc, hist), "hist": hist[-14:] + [sc], "n": len(graded),
                   "n3": sum(1 for g in graded if g["lv"] == 3), "n2": sum(1 for g in graded if g["lv"] == 2),
                   "top": sorted(graded, key=lambda g: (-g["lv"], -g["ts"]))[:6]}
    for d in sorted(days)[:-60]:
        days.pop(d, None)
    return out


async def refresh(every_h: float = 2) -> Dict:
    cache = _load()
    if cache.get("view") and time.time() - float(cache.get("ts", 0)) < every_h * 3600:
        return cache["view"]
    raw: Dict[str, List[Dict]] = {}
    ok = 0
    for th, (_, _, urls, _) in THEATRES.items():
        res = await asyncio.gather(*(_feed(u) for u in urls), return_exceptions=True)
        raw[th] = [x for r in res if not isinstance(r, Exception) for x in r]
        ok += sum(1 for r in res if not isinstance(r, Exception))
    if not ok:
        return cache.get("view") or {}
    view = assemble(raw, cache)
    cache.update({"ts": time.time(), "view": view})
    _save(cache)
    return view


def load() -> Dict:
    return _load().get("view") or {}
