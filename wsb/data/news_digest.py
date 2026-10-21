"""新聞整理（背景）— Business Insider's own reporting, sorted by the themes this site follows, with Chinese titles.

Sources: Business Insider's public feeds (the main feed lists free-to-read articles only; the markets feed).  Only the
title, time and link are kept — no article text.  Themes are keyword rules on the English title; companies are matched
by name against the tracked list so the private holdings page can pin news about your holdings.  Titles are translated
to Chinese by the site's AI model when available (cached by title; English shown when it is not).
Background only: news never enters any score, signal or risk model.
Cached in data_cache/econ_news_digest.json (econ_* is already in the site workflow's cache)."""
from __future__ import annotations

import html
import json
import logging
import re
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..config import DATA_DIR
from . import http

log = logging.getLogger(__name__)
CACHE = DATA_DIR / "econ_news_digest.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
FEEDS = [("Business Insider", "https://www.businessinsider.com/rss"),
         ("Business Insider Markets", "https://markets.businessinsider.com/rss/news")]
TOPICS = [("ai", "AI 與晶片", "AI & chips", r"\b(ai|a\.i\.|nvidia|chip|chips|semiconductor|gpu|data ?cent(er|re)s?|openai|anthropic|llm|hyperscaler)\b"),
          ("power", "電力與能源", "Power & energy", r"\b(power|electricity|grid|energy|nuclear|utilit(y|ies)|oil|gas|solar|uranium)\b"),
          ("fed", "聯準會與利率", "Fed & rates", r"\b(fed|federal reserve|powell|rate cut|rate hike|interest rates?|inflation|cpi|pce|treasur(y|ies)|yields?|bond market)\b"),
          ("credit", "信用與負債", "Credit & debt", r"\b(debt|credit|default|private credit|loans?|lenders?|bankrupt\w*|junk)\b"),
          ("earnings", "財報", "Earnings", r"\b(earnings|revenue|guidance|quarter|q[1-4]|profit|outlook)\b"),
          ("market", "市場動向", "Markets", r"\b(stocks?|s&p|nasdaq|dow|market|rally|selloff|sell-off|bear|bull|recession|tariffs?)\b")]


def _clean(s: str) -> str:
    s = re.sub(r"^<!\[CDATA\[(.*)\]\]>$", r"\1", (s or "").strip(), flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse(text: str, source: str) -> List[Dict]:
    """RSS <item> or Atom <entry> → [{title, link, ts, source}] (tolerant of partial documents)."""
    out = []
    for m in re.finditer(r"<(item|entry)\b(.*?)</\1>", text, re.S):
        b = m.group(2)
        t = re.search(r"<title\b[^>]*>(.*?)</title>", b, re.S)
        if not t:
            continue
        link = re.search(r"<link\b[^>]*href=\"([^\"]+)\"", b) or re.search(r"<link>(.*?)</link>", b, re.S)
        d = (re.search(r"<pubDate>(.*?)</pubDate>", b, re.S) or re.search(r"<published>(.*?)</published>", b, re.S)
             or re.search(r"<updated>(.*?)</updated>", b, re.S))
        ts = None
        if d:
            raw = d.group(1).strip()
            try:
                ts = parsedate_to_datetime(raw).timestamp() if "," in raw[:5] or raw[:3].isalpha() else \
                    datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
            except (TypeError, ValueError):
                ts = None
        out.append({"title": _clean(t.group(1))[:200], "link": _clean(link.group(1)) if link else "", "ts": ts, "source": source})
    return out


def topics(title: str) -> List[str]:
    t = title.lower()
    hit = [k for k, _zh, _en, rx in TOPICS if re.search(rx, t)]
    return hit or ["other"]


def companies(title: str, names: Dict[str, str]) -> List[str]:
    """names: {English company name: ticker} for the tracked list (word-boundary match, longest names first)."""
    found = []
    for nm in sorted(names, key=len, reverse=True):
        if len(nm) >= 3 and re.search(rf"\b{re.escape(nm)}\b", title, re.I) and names[nm] not in found:
            found.append(names[nm])
    return found[:4]


def name_map() -> Dict[str, str]:
    from .stocks import universe
    out = {}
    for mk in universe().values():
        for sym, (_zh, en) in (mk.get("symbols") or {}).items():
            base = re.sub(r"\b(Inc|Corp|Corporation|Co|Ltd|Holdings|Group|plc|S\.A|N\.V|Technologies|Platforms|Class [A-C])\.?\b", "", en or "").strip(" ,.")
            for n in {en, base}:
                if n and len(n) >= 3:
                    out[n] = sym
    out.update({"Google": "GOOGL", "Alphabet": "GOOGL", "Meta": "META", "Facebook": "META", "Nvidia": "NVDA", "TSMC": "TSM",
                "Oracle": "ORCL", "Amazon": "AMZN", "Microsoft": "MSFT", "Apple": "AAPL", "Tesla": "TSLA", "CoreWeave": "CRWV"})
    return out


async def _translate(titles: List[str]) -> Dict[str, str]:
    """English → Traditional Chinese titles via the site's AI model; {} when unavailable."""
    if not titles:
        return {}
    try:
        from ..ai import llm
        prompt = ("把下列英文新聞標題翻成自然的繁體中文（台灣用語），保留公司名稱與數字，逐行輸出，行數與順序必須完全相同，不要編號、不要加任何說明：\n"
                  + "\n".join(titles))
        text, name = await llm.complete("你是財經新聞編輯，只做翻譯。", prompt, 1500)
        if name == "none" or not text or text.startswith("⚠️"):
            return {}
        lines = [x.strip() for x in text.strip().splitlines() if x.strip()]
        return dict(zip(titles, lines)) if len(lines) == len(titles) else {}
    except Exception as e:  # noqa: BLE001
        log.info("news title translation unavailable: %s", e)
        return {}


async def refresh(max_age_min: float = 30, keep: int = 60) -> Dict:
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        old = {}
    if time.time() - float(old.get("ts", 0)) < max_age_min * 60:
        return old
    items: Dict[str, Dict] = {i["link"] or i["title"]: i for i in old.get("items", [])}
    for src, url in FEEDS:
        try:
            for it in parse(await http.get(url, kind="text", timeout=30, retries=1, headers=UA), src):
                k = it["link"] or it["title"]
                items[k] = {**items.get(k, {}), **it}
        except Exception as e:  # noqa: BLE001
            log.warning("news feed %s failed: %s", src, e)
    nm = name_map()
    rows = sorted(items.values(), key=lambda i: -(i.get("ts") or 0))[:keep]
    for r in rows:
        r["topics"], r["syms"] = topics(r["title"]), companies(r["title"], nm)
    # finance only: lifestyle stories and press-release wires carry no theme and no tracked company
    rows = [r for r in rows if r["topics"] != ["other"] or r["syms"]]
    tr = dict(old.get("zh", {}))
    need = [r["title"] for r in rows if r["title"] not in tr][:40]
    tr.update(await _translate(need))
    tr = {r["title"]: tr[r["title"]] for r in rows if r["title"] in tr}          # keep the cache small
    out = {"ts": time.time(), "items": rows, "zh": tr}
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE)
    return out


def load() -> Dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
