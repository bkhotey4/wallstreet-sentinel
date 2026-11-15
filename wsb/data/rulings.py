"""法院與監管機關的決定（2026-11-16，使用者選的第 8 項）：美國最高法院判決、SEC 與 CFTC 的新規則與重大處分、司法部反壟斷。

  * 最高法院：官方「Opinions of the Court」頁（www.supremecourt.gov/opinions/slipopinion/{開庭年度}），本年度與上一年度；
    每列是判決日期、案號、案名、官方摘要（滑鼠提示文字）與判決書 PDF
  * SEC、CFTC：官方新聞稿 RSS，只留規則（adopts／final rule／proposes／approves）與市場結構相關的
  * 司法部：官方新聞 RSS，只留反壟斷（antitrust／merger／monopol…）
每一項用關鍵字對到「最先會動的資產」（聯準會與利率 → 美債 10 年殖利率；關稅 → 標普 500；…），網站再算那一天它動了多少。
FTC 的新聞 RSS 網址現在回 404，沒有加入。快取 data_cache/econ_rulings.json（6 小時一次）。"""
from __future__ import annotations

import html as _html
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_rulings.json"
TTL = 6 * 3600
DAYS = 75
HDR = {"User-Agent": "WallStreetSentinel research (public data reader)"}
SCOTUS = "https://www.supremecourt.gov/opinions/slipopinion/{t:02d}"
FEEDS = (("sec", "SEC", "https://www.sec.gov/news/pressreleases.rss",
          r"adopt|final rule|propos|approv|amendment|exempt|market structure|exchange-traded|\betf\b|crypto|digital asset|stablecoin|treasury clearing|short sale"),
         ("cftc", "CFTC", "https://www.cftc.gov/RSS/RSSGP/rssgp.xml",
          r"final rule|propos|approv|interpretation|event contract|prediction market|crypto|digital asset|jurisdiction|swap"),
         ("doj", "司法部反壟斷", "https://www.justice.gov/news/rss?type=press_release&component=376",
          r"antitrust|monopol|merger|acquisition|sherman act|clayton act|price-fixing|bid rigging"))
SRC_ZH = {"scotus": "最高法院", "sec": "SEC", "cftc": "CFTC", "doj": "司法部反壟斷"}
# checked before the Federal Register topics: (topic, keywords, first-moving asset, its name)
EXTRA = (("聯準會與利率", r"federal reserve|board of governors|for[- ]cause removal|removal of .{0,30}governor|monetary policy", "^TNX", "美債 10 年殖利率"),
         ("反壟斷", r"antitrust|monopol|sherman act|clayton act|merger", "^NDX", "那斯達克 100"),
         ("證券與市場規則", r"securities|exchange act|investment adviser|market structure|clearing|short sale|\betf\b", "^GSPC", "標普 500"),
         ("預測市場與衍生品", r"event contract|prediction market|swap|futures|derivative", "^GSPC", "標普 500"))


def topic(text: str) -> Optional[Dict]:
    t = text.lower()
    for zh, rx, sym, szh in EXTRA:
        if re.search(rx, t):
            return {"topic": zh, "sym": sym, "sym_zh": szh}
    from .fed_register import topic as fr_topic
    return fr_topic(text, "")


def term_of(d: date) -> int:
    """Supreme Court term (two digits) that starts on the first Monday of October."""
    return (d.year if d.month >= 10 else d.year - 1) % 100


ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
LINK = re.compile(r"""<a\s+href=['"]([^'"]+)['"][^>]*?title=["']([^"']*)["'][^>]*>([^<]+)</a>""", re.S)


def parse_scotus(page: str) -> List[Dict]:
    out = []
    for row in ROW.findall(page):
        cells = CELL.findall(row)
        if len(cells) < 4:
            continue
        m = LINK.search(row)
        dt = re.sub(r"<[^>]+>", "", cells[1]).strip()
        if not m or not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2}", dt):
            continue
        mm, dd, yy = (int(x) for x in dt.split("/"))
        href, summ, name = m.group(1), _html.unescape(m.group(2)).strip(), _html.unescape(m.group(3)).strip()
        out.append({"src": "scotus", "date": date(2000 + yy, mm, dd).isoformat(), "title": name, "sum": summ[:600],
                    "docket": re.sub(r"<[^>]+>", "", cells[2]).strip(),
                    "url": href if href.startswith("http") else "https://www.supremecourt.gov" + href})
    return out


ITEM = re.compile(r"<item>(.*?)</item>", re.S)


def _tag(x: str, t: str) -> str:
    m = re.search(rf"<{t}[^>]*>(.*?)</{t}>", x, re.S)
    v = m.group(1) if m else ""
    v = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", v, flags=re.S)
    return _html.unescape(re.sub(r"<[^>]+>", " ", v)).strip()


def parse_rss(xml: str, src: str, keep: str) -> List[Dict]:
    out = []
    for it in ITEM.findall(xml):
        title, link, pub = _tag(it, "title"), _tag(it, "link"), _tag(it, "pubDate")
        desc = _tag(it, "description")[:400]
        if not title or not re.search(keep, f"{title} {desc}", re.I):
            continue
        try:
            d = parsedate_to_datetime(pub).date().isoformat()
        except (TypeError, ValueError):
            continue
        out.append({"src": src, "date": d, "title": title, "sum": desc, "url": link})
    return out


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def refresh(force: bool = False) -> Dict:
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts_try", 0)) < TTL:
        return d
    d["ts_try"] = now
    items, bad, ok = [], [], 0
    t = term_of(date.today())
    for term in (t, t - 1):
        try:
            items += parse_scotus(await http.get(SCOTUS.format(t=term), kind="text", headers=HDR, timeout=40, retries=1))
            ok += 1
        except Exception as e:  # noqa: BLE001
            bad.append(f"scotus {term}: {e if str(e) else type(e).__name__}")
    for src, _zh, url, keep in FEEDS:
        try:
            items += parse_rss(await http.get(url, kind="text", headers=HDR, timeout=30, retries=1), src, keep)
            ok += 1
        except Exception as e:  # noqa: BLE001
            bad.append(f"{src}: {e if str(e) else type(e).__name__}")
    cut = (date.today() - timedelta(days=DAYS)).isoformat()
    old = {x["url"]: x for x in d.get("items") or [] if x.get("date", "") >= cut}
    for x in items:
        if x["date"] >= cut:
            x.update(topic(f"{x['title']} {x.get('sum', '')}") or {})
            x["seen"] = (old.get(x["url"]) or {}).get("seen") or now
            old[x["url"]] = x
    d["items"] = sorted(old.values(), key=lambda x: (x["date"], x["src"]), reverse=True)
    if ok:
        d["ts"] = now
    if bad:
        log.warning("rulings: %s", "; ".join(bad))
        HEALTH.fail("rulings", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("rulings", len(d["items"]), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def alerts(d: Dict, now: float, fresh_h: float = 30) -> List[Dict]:
    """New items with a market topic, first seen in the last 30 hours (a first fill never floods)."""
    out = []
    first = min((float(x.get("seen") or now) for x in d.get("items") or []), default=now)
    for x in d.get("items") or []:
        if not x.get("topic") or now - float(x.get("seen") or 0) > fresh_h * 3600 or float(x.get("seen") or 0) <= first + 60:
            continue
        if x["src"] in ("sec", "cftc") and not re.search(r"adopt|final rule|approv", x["title"], re.I):
            continue                                       # proposals stay on the page; only decided rules are pushed
        out.append({"key": f"ruling:{x['src']}:{x['url'][-80:]}", "item": x, "lv": 1})
    return out[:3]
