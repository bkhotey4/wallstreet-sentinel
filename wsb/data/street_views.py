"""華爾街機構觀點（背景）— what large firms are publicly saying, plus how institutions are actually positioned.

* Views: the latest titles + links from free, public, first-party publications —
  Morgan Stanley "Thoughts on the Market" (podcast feed, transcripts on their site), Goldman Sachs "Exchanges"
  (podcast feed), BlackRock Investment Institute weekly commentary (web page).  Titles, dates and links only:
  no article text is copied.  Background only — never an input to any risk score or signal.
* Positioning: CFTC Traders in Financial Futures (US government open data, weekly): asset managers' and leveraged
  funds' net positions in E-mini S&P 500 and E-mini Nasdaq-100 futures, as % of open interest, with the 3-year
  percentile and the weekly change.  Descriptive; positioning extremes are not timing signals by themselves.
Cached in data_cache/econ_street.json (econ_* is already in the site workflow's cache — no cache-key change)."""
from __future__ import annotations

import html
import json
import logging
import re
import time
from typing import Dict, List, Optional

from ..config import DATA_DIR
from . import http

log = logging.getLogger(__name__)
CACHE = DATA_DIR / "econ_street.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
FEEDS = [("ms", "摩根士丹利〈Thoughts on the Market〉", "Morgan Stanley — Thoughts on the Market", "https://rss.art19.com/thoughts-on-the-market",
          "https://www.morganstanley.com/insights/podcasts/thoughts-on-the-market"),
         ("gs", "高盛〈Exchanges〉", "Goldman Sachs — Exchanges", "https://feeds.megaphone.fm/GLD9218176758",
          "https://www.goldmansachs.com/insights/goldman-sachs-exchanges")]
BLACKROCK = ("br", "貝萊德投資研究院週評", "BlackRock Investment Institute — Weekly commentary",
             "https://www.blackrock.com/corporate/insights/blackrock-investment-institute/publications/weekly-commentary")
CFTC = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
CONTRACTS = {"13874A": ("E-mini 標普 500", "E-mini S&P 500"), "209742": ("E-mini 那斯達克 100", "E-mini Nasdaq-100")}


def parse_feed(text: str, n: int = 5) -> List[Dict]:
    """Items from an RSS document — tolerant of a truncated download (only complete <item> blocks are read)."""
    out = []
    for block in re.findall(r"<item\b.*?</item>", text, re.S)[:n]:
        def tag(t):
            m = re.search(rf"<{t}\b[^>]*>(.*?)</{t}>", block, re.S)
            if not m:
                return ""
            v = m.group(1).strip()
            v = re.sub(r"^<!\[CDATA\[(.*)\]\]>$", r"\1", v, flags=re.S)
            return html.unescape(re.sub(r"<[^>]+>", "", v)).strip()
        title, date, link = tag("title"), tag("pubDate"), tag("link")
        if title:
            out.append({"title": title[:160], "date": date[:16], "link": link if link.startswith("http") else ""})
    return out


def parse_blackrock(page: str) -> List[Dict]:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    d = re.search(r"\b([A-Z][a-z]{2,8} \d{1,2}, 20\d\d)\b", page)
    if not m:
        return []
    title = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
    return [{"title": title[:160], "date": d.group(1) if d else "", "link": BLACKROCK[3]}] if title else []


def positioning(rows: List[Dict]) -> Optional[Dict]:
    """rows: CFTC TFF records of one contract, newest first → net % of open interest, 3-year percentile, weekly change."""
    pts = []
    for r in rows:
        try:
            oi = float(r["open_interest_all"])
            am = (float(r["asset_mgr_positions_long"]) - float(r["asset_mgr_positions_short"])) / oi * 100
            lm = (float(r["lev_money_positions_long"]) - float(r["lev_money_positions_short"])) / oi * 100
            pts.append((r["report_date_as_yyyy_mm_dd"][:10], am, lm))
        except (KeyError, ValueError, ZeroDivisionError):
            continue
    if len(pts) < 30:
        return None
    pts.sort()
    am_s, lm_s = [p[1] for p in pts], [p[2] for p in pts]

    def pct(xs):
        return sum(x < xs[-1] for x in xs[:-1]) / (len(xs) - 1) * 100
    return {"asof": pts[-1][0], "n_weeks": len(pts), "am": am_s[-1], "am_chg": am_s[-1] - am_s[-2], "am_pct": pct(am_s),
            "lm": lm_s[-1], "lm_chg": lm_s[-1] - lm_s[-2], "lm_pct": pct(lm_s), "since": pts[0][0]}


async def refresh(max_age_h: float = 6) -> Dict:
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        old = {}
    if time.time() - float(old.get("ts", 0)) < max_age_h * 3600:
        return old
    out = {"ts": time.time(), "views": dict(old.get("views", {})), "pos": dict(old.get("pos", {}))}
    for key, zh, en, url, home in FEEDS:
        try:
            # Morgan Stanley's feed is ~20 MB of history: the newest items are at the top, so ask for the first part only
            txt = await http.get(url, kind="text", timeout=40, retries=1, headers={**UA, "Range": "bytes=0-400000"})
            items = parse_feed(txt)
            if items:
                out["views"][key] = {"zh": zh, "en": en, "home": home, "items": items[:3], "checked": time.time()}
        except Exception as e:  # noqa: BLE001
            log.warning("street view %s failed: %s", key, e)
    try:
        page = await http.get(BLACKROCK[3], kind="text", timeout=40, retries=1, headers=UA)
        items = parse_blackrock(page)
        if items:
            out["views"]["br"] = {"zh": BLACKROCK[1], "en": BLACKROCK[2], "home": BLACKROCK[3], "items": items, "checked": time.time()}
    except Exception as e:  # noqa: BLE001
        log.warning("street view blackrock failed: %s", e)
    for code, (zh, en) in CONTRACTS.items():
        try:
            rows = await http.get(CFTC, timeout=40, retries=1, params={
                "$where": f"cftc_contract_market_code='{code}'", "$order": "report_date_as_yyyy_mm_dd DESC", "$limit": "160"})
            p = positioning(rows or [])
            if p:
                out["pos"][code] = {"zh": zh, "en": en, **p}
        except Exception as e:  # noqa: BLE001
            log.warning("CFTC %s failed: %s", code, e)
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE)
    return out


def load() -> Dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
