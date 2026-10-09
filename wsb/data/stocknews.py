"""Per-stock headlines for the scoring universe via Google News RSS (batched: one query covers ~8 names).

Each headline is tagged positive / negative with a transparent keyword list (settings.stockscore.news_pos/neg).
That is a crude reading of tone — it is shown as such on the site, never as an AI judgement."""
from __future__ import annotations

import asyncio
import calendar
import json
import logging
import re
import time
from typing import Dict, List, Tuple
from urllib.parse import quote

from ..config import DATA_DIR
from ..health import HEALTH
from . import http
from .stocks import cfg, universe

log = logging.getLogger(__name__)
_FILE = DATA_DIR / "stock_news.json"
_LANG = {"en": "hl=en-US&gl=US&ceid=US:en", "zh-TW": "hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
         "zh-HK": "hl=zh-HK&gl=HK&ceid=HK:zh-Hant"}


def _pat(word: str) -> re.Pattern:
    w = re.escape(word.lower())
    return re.compile(rf"(?<![a-z0-9]){w}(?![a-z0-9])" if word.isascii() else w)


def polarity(title: str) -> int:
    t = title.lower()
    pos = sum(1 for k in cfg().get("news_pos", []) if _pat(str(k)).search(t))
    neg = sum(1 for k in cfg().get("news_neg", []) if _pat(str(k)).search(t))
    return (pos > neg) - (neg > pos)


def match_names(title: str, names: List[Tuple[str, str]]) -> List[str]:
    """names: [(sym, keyword)] → symbols whose keyword appears in the title (case-insensitive, whole word for ASCII)."""
    t = title.lower()
    return [s for s, k in names if k and _pat(k).search(t)]


class StockNews:
    def __init__(self) -> None:
        self.items: Dict[str, List[dict]] = {}
        self.ts = 0.0
        try:
            if _FILE.exists():
                d = json.loads(_FILE.read_text(encoding="utf-8"))
                self.items, self.ts = d.get("items", {}), float(d.get("ts", 0))
        except Exception as e:  # noqa: BLE001
            log.warning("stock news cache unreadable: %s", e)

    async def _query(self, terms: List[str], lang: str) -> List[Tuple[str, str, float, str]]:
        import feedparser
        q = "(" + " OR ".join(f'"{t}"' for t in terms) + ") when:3d"
        url = f"https://news.google.com/rss/search?q={quote(q)}&{_LANG.get(lang, _LANG['en'])}"
        raw = await http.get(url, kind="bytes", retries=1, timeout=20)
        parsed = await asyncio.to_thread(feedparser.parse, raw)
        out = []
        for e in parsed.entries[:100]:
            title = re.sub(r"\s+", " ", e.get("title") or "").strip()
            src = ""
            m = re.search(r"\s+-\s+([^-]{2,40})$", title)          # Google News appends " - Publisher"
            if m:
                src, title = m.group(1).strip(), title[:m.start()].strip()
            st = e.get("published_parsed") or e.get("updated_parsed")
            out.append((title, e.get("link", ""), calendar.timegm(st) if st else time.time(), src))
        return out

    async def refresh(self, force: bool = False) -> None:
        if not cfg().get("enabled", True):
            return
        every = float(cfg().get("refresh_hours", 3)) * 3600
        if not force and self.items and time.time() - self.ts < every:
            return
        batch = int(cfg().get("news_batch", 8))
        keep_s = float(cfg().get("news_hours", 72)) * 3600
        found: Dict[str, List[dict]] = {}
        ok = fail = 0
        for mk, m in universe().items():
            lang = m.get("news_lang", "en")
            names = [(s, (zh if lang.startswith("zh") else en)) for s, (zh, en) in m["symbols"].items()]
            for i in range(0, len(names), batch):
                part = names[i:i + batch]
                try:
                    rows = await self._query([k for _, k in part], lang)
                    ok += 1
                except Exception as e:  # noqa: BLE001
                    fail += 1
                    log.debug("stock news %s batch %d failed: %s", mk, i, e)
                    continue
                for title, link, ts, src in rows:
                    if time.time() - ts > keep_s:
                        continue
                    for s in match_names(title, part):
                        lst = found.setdefault(s, [])
                        if all(x["t"] != title for x in lst):
                            lst.append({"t": title[:200], "l": link, "ts": ts, "src": src, "p": polarity(title)})
                await asyncio.sleep(0.6)
        if ok:
            for s in found:
                found[s].sort(key=lambda x: -x["ts"])
                found[s] = found[s][:12]
            self.items, self.ts = found, time.time()
            try:
                _FILE.write_text(json.dumps({"ts": self.ts, "items": self.items}, ensure_ascii=False), encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                log.warning("stock news cache not saved: %s", e)
            HEALTH.ok("stock_news", sum(len(v) for v in found.values()), every=every)
        else:
            HEALTH.fail("stock_news", f"all {fail} Google News queries failed", every=every)

    def summary(self, sym: str) -> Dict:
        lst = self.items.get(sym) or []
        pos = sum(1 for x in lst if x["p"] > 0)
        neg = sum(1 for x in lst if x["p"] < 0)
        return {"n": len(lst), "pos": pos, "neg": neg, "top": lst[:3]}
