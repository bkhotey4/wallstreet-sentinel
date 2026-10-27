"""Multi-source news intelligence: RSS from wires, central banks, crypto and
Google News risk queries → de-duplicated, keyword risk-scored, ranked."""
from __future__ import annotations

import asyncio
import calendar
import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List

from ..config import SETTINGS
from ..health import HEALTH
from .. import store
from . import http

log = logging.getLogger(__name__)


@dataclass
class NewsItem:
    source: str
    title: str
    link: str
    ts: float
    score: int = 0
    hits: List[str] = field(default_factory=list)
    new: bool = False
    pubs: set = field(default_factory=set)        # independent publishers carrying it (not feeds, not re-posts)

    @property
    def outlets(self) -> int:
        return max(1, len(self.pubs))

    @property
    def uid(self) -> str:
        norm = re.sub(r"[^a-z0-9一-鿿]+", "", self.title.lower())[:120]
        return hashlib.sha1(norm.encode()).hexdigest()


def publisher(feed: str, title: str) -> str:
    """Who actually wrote it.  Google News items end in " - Outlet"; two feeds of one house (CNBC / CNBC Finance) are
    one publisher, so the same wire story seen twice is never counted as independent confirmation."""
    if feed.lower().startswith("gnews"):
        m = re.search(r"\s[-–—]\s([^-–—]{2,60})$", title)
        if m:
            return m.group(1).strip().lower()
    return feed.split()[0].lower()


def story_key(title: str) -> str:
    """Merge key for one story across outlets: the title without Google News' trailing " - Outlet"."""
    t = re.sub(r"\s[-–—]\s[^-–—]{2,60}$", "", title)
    return re.sub(r"[^a-z0-9一-鿿]+", "", t.lower())[:120]


def score_title(title: str, keywords: Dict[str, int]) -> tuple[int, List[str]]:
    t = title.lower()
    hits, score = [], 0
    for kw, w in keywords.items():
        k = str(kw).lower()
        pattern = rf"\b{re.escape(k)}\b" if k.isascii() else re.escape(k)
        if re.search(pattern, t):
            hits.append(str(kw))
            score += int(w)
    return score, hits


class NewsWire:
    def __init__(self) -> None:
        self.items: List[NewsItem] = []
        self.last_fresh: List[NewsItem] = []
        self.ts = 0.0
        # undated entries keep the time we first saw them (not "now" on every refresh, which kept them forever fresh)
        self._first_seen: Dict[str, float] = {}
        try:
            fs = store.kv_get("news_first_seen", {}) or {}
            self._first_seen = {str(k): float(v) for k, v in fs.items()} if isinstance(fs, dict) else {}
        except Exception as e:  # noqa: BLE001
            log.debug("news first-seen map unavailable: %s", e)

    async def _feed(self, name: str, url: str) -> List[NewsItem]:
        import feedparser
        raw = await http.get(url, kind="bytes", retries=1)
        parsed = await asyncio.to_thread(feedparser.parse, raw)
        out = []
        for e in parsed.entries[:40]:
            title = re.sub(r"\s+", " ", (e.get("title") or "")).strip()
            if not title:
                continue
            st = e.get("published_parsed") or e.get("updated_parsed")
            it = NewsItem(name, title, e.get("link", ""), calendar.timegm(st) if st else 0.0)
            if not st:
                it.ts = self._first_seen.setdefault(it.uid, time.time())
            out.append(it)
        return out

    async def refresh(self) -> List[NewsItem]:
        """Refresh all feeds; returns NEW high-signal items (for alerting)."""
        every = SETTINGS["refresh"]["news"]
        feeds = SETTINGS.get("news_feeds", [])
        kw = SETTINGS.get("news_keywords", {})
        res = await asyncio.gather(*(self._feed(f["name"], f["url"]) for f in feeds),
                                   return_exceptions=True)
        merged: Dict[str, NewsItem] = {}
        ok = 0
        for f, r in zip(feeds, res):
            if isinstance(r, Exception):
                HEALTH.fail(f"news:{f['name']}", r, every=every)
                continue
            ok += 1
            HEALTH.ok(f"news:{f['name']}", len(r), every=every)
            for it in r:
                it.score, it.hits = score_title(it.title, kw)
                pub = publisher(f["name"], it.title)
                mk = story_key(it.title)
                prev = merged.get(mk)
                if prev is None:
                    it.pubs = {pub}
                    merged[mk] = it
                else:
                    # only a different publisher counts as corroboration (+1 each, at most +2): a re-post on the same
                    # site or a second feed of the same house is popularity, not independent evidence
                    if pub not in prev.pubs and len(prev.pubs) < 3:
                        prev.score += 1
                    prev.pubs.add(pub)
                    if f["name"] not in prev.source:
                        prev.source += f"/{f['name']}"
        cutoff = time.time() - 36 * 3600
        items = [i for i in merged.values() if i.ts >= cutoff]
        fresh = []
        for it in items:
            it.new = store.seen_check_and_mark(it.uid)
            if it.new:
                fresh.append(it)
        items.sort(key=lambda i: (i.score, i.ts), reverse=True)
        keep = time.time() - 72 * 3600                  # first-seen times only matter inside the 36 h window
        self._first_seen = {k: v for k, v in self._first_seen.items() if v >= keep}
        try:
            store.kv_set("news_first_seen", self._first_seen)
        except Exception as e:  # noqa: BLE001
            log.debug("news first-seen map not saved: %s", e)
        self.items = items
        self.ts = time.time()
        self.last_fresh = sorted(fresh, key=lambda i: i.score, reverse=True)
        return self.last_fresh

    def top(self, n: int = 15, query: str | None = None) -> List[NewsItem]:
        items = self.items
        if query:
            q = query.lower()
            items = [i for i in items if q in i.title.lower()]
        return items[:n]

    def latest(self, n: int = 15) -> List[NewsItem]:
        return sorted(self.items, key=lambda i: i.ts, reverse=True)[:n]
