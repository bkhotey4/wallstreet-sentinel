"""聯準會官員講話：理事會官網的演講 RSS（主席、副主席與理事，全部有 FOMC 永久投票權）＋官網行事曆（接下來兩週誰要講）。

每篇演講抓原文（美國政府著作，公有領域），算：
  * 提到通膨幾次、提到就業／勞動市場幾次 → 這篇比較擔心哪一邊
  * 講到利率、而且是講者自己看法（I / my）的第一句原文，當作「這篇的重點句」
市場反應（卡片端算）：演講當天 2 年期美債殖利率（FRED DGS2；FRED 還沒刊的最近幾天用財政部當天的殖利率曲線補）變多少，和平常一天的波動比。同一天常有其他消息，
所以只說「同一天」，不說「因為這篇演講」。字數統計不是 AI 判讀，只是讓你知道這篇在講什麼。
地方聯準會總裁的演講不在理事會 RSS 裡，這裡沒有。快取 data_cache/econ_fedspeech.json，6 小時一次。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_fedspeech.json"
TTL = 6 * 3600
RSS = "https://www.federalreserve.gov/feeds/speeches.xml"
CAL = "https://www.federalreserve.gov/json/calendar.json"
PAGE = "https://www.federalreserve.gov/newsevents/speeches.htm"
CAL_PAGE = "https://www.federalreserve.gov/newsevents/calendar.htm"
UST = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"   # 財政部每日殖利率曲線（當天收盤後公布）
UST_PAGE = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve"
UA = {"User-Agent": "Mozilla/5.0"}
KEEP = 40                                     # speeches kept in the cache
SCORE_V = 5                                   # bump when score() changes so cached speeches are re-read

INFL = re.compile(r"\binflation\w*|\bprices?\b", re.I)
JOBS = re.compile(r"\blabor market|\bemployment\b|\bunemployment\b|\bjobs?\b|\bhiring\b|\blayoffs?\b", re.I)
RATE = re.compile(r"policy rate|federal funds rate|monetary policy|rate cuts?|rate increases?|rate hikes?", re.I)
_RATES = r"\s+(?:in\s+|of\s+)?(?:the\s+|our\s+)?(?:policy\s+|federal\s+funds\s+|interest\s+)?rates?\b"
# direction words count only when they point at the policy rate: "reduce inflation" or "rising prices" is not a rate call
EASE = re.compile(r"\b(?:(?:cut|cuts|cutting|lower(?:ing)?|reduc(?:e|ed|ing)|eas(?:e|ing))" + _RATES
                  + r"|rate cuts?|(?:further|additional) (?:cuts|easing)|less restrictive|accommodat\w*"
                  + r"|rates?\s+(?:\w+\s+){0,3}(?:be\s+)?(?:lowered|reduced|cut)\b)", re.I)
HOLD = re.compile(r"\b(should wait|wait until|patient|patience|hold(ing)? (the|our) (policy )?rate|on hold|well positioned|maintain(ing)? the (current )?(policy|rate|target)"
                  r"|(remain|stay|keep)\w* (sufficiently |moderately )?restrictive)\b", re.I)
MINE = re.compile(r"\bmy view|\bI (?:support|expect|believe|think|see|favor|would|judge|anticipate)\b|\bin my\b")   # the speaker's own view
TIGHT = re.compile(r"\b(?:(?:rais(?:e|ed|ing)|hik(?:e|es|ing)|increas(?:e|es|ing)|tighten(?:ing)?)" + _RATES
                   + r"|rate (?:hikes?|increases?)|(?:further|additional) (?:tightening|firming|hikes|increases)|more restrictive|firming|hold(?:ing)? .{0,20}longer"
                   + r"|rates?\s+(?:\w+\s+){0,3}(?:be\s+)?(?:raised|increased|hiked)\b)", re.I)
AGENDA = re.compile(r"\bwill (then )?(turn|discuss|conclude)|\btoday I\b|before I turn|\bI (will|want to|would like to) (explain|describe|spend|focus|discuss|talk)", re.I)
ABBR = re.compile(r"\b(U\.S|U\.K|e\.g|i\.e|Mr|Ms|Mrs|Dr|St|No|vs)\.", re.I)


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def parse_ust2(xml: str) -> Dict[str, float]:
    """Treasury daily par yield curve XML → {YYYY-MM-DD: 2-year yield %}. FRED DGS2 is the same Treasury number,
    one day later; this fills the days FRED has not posted yet."""
    out = {}
    for blk in re.findall(r"<m:properties>(.*?)</m:properties>", xml, re.S):
        d = re.search(r"<d:NEW_DATE[^>]*>(\d{4}-\d{2}-\d{2})", blk)
        v = re.search(r"<d:BC_2YEAR[^>]*>([\d.]+)<", blk)
        if d and v:
            out[d.group(1)] = float(v.group(1))
    return out


def parse_rss(xml: str) -> List[Dict]:
    out = []
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        def g(tag):
            m = re.search(rf"<{tag}>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</{tag}>", it, re.S)
            return unescape(m.group(1).strip()) if m else ""
        title, link, when = g("title"), g("link"), g("pubDate")
        if not title or not link:
            continue
        who, _, topic = title.partition(",")
        try:
            dt = parsedate_to_datetime(when)
            iso = dt.strftime("%Y-%m-%dT%H:%MZ")
        except Exception:  # noqa: BLE001
            iso = ""
        out.append({"url": link, "who": who.strip(), "topic": topic.strip() or title, "where": g("description"),
                    "kind": g("category") or "Speech", "time": iso})
    return out


def text_of(html: str) -> str:
    i = html.find('id="article"')
    a = html[html.find(">", i) + 1:] if i >= 0 else html          # start after the opening tag itself
    for stop in ("Last Update", 'class="footnotes"', ">References<", ">Footnotes<"):
        j = a.find(stop)
        if j > 0:
            a = a[:j]
    a = re.sub(r"<script.*?</script>|<style.*?</style>", " ", a, flags=re.S)
    a = re.sub(r"</(p|h\d|li|div|blockquote)>", " ¶ ", a)          # block ends are sentence ends (headings have no period)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", a))).strip(" ¶")


def score(text: str) -> Dict:
    safe = ABBR.sub(lambda m: m.group(0).replace(".", "․"), text)     # "U.S." must not end a sentence
    sents = [x.strip().replace("․", ".") for x in re.split(r"(?<=[.!?])\s+|\s*¶\s*", safe) if x.strip()]
    text = text.replace("¶", " ")
    ease, tight = [], []
    for s in sents:
        if not RATE.search(s) or len(s) > 400:
            continue
        e, t = bool(EASE.search(s)), bool(TIGHT.search(s))
        if e and not t:
            ease.append(s)
        elif t and not e:
            tight.append(s)
    mine = [s for s in sents if RATE.search(s) and MINE.search(s) and 40 <= len(s) <= 400
            and not AGENDA.search(s)]
    return {"words": len(text.split()), "infl": len(INFL.findall(text)), "jobs": len(JOBS.findall(text)),
            "ease": len(ease), "tight": len(tight), "key": mine[0] if mine else "", "key_dir": key_dir(mine[0] if mine else "")}


def key_dir(s: str) -> str:
    """Direction words in the key sentence only: tight / ease / hold / '' (mixed or none)."""
    if not s:
        return ""
    t, e, h = bool(TIGHT.search(s)), bool(EASE.search(s)), bool(HOLD.search(s))
    if h:                                     # "changes should wait" outranks a passing mention of a past hike or cut
        return "hold"
    if t and not e:
        return "tight"
    if e and not t:
        return "ease"
    return ""


def parse_cal(js: Dict, today: date, days: int = 14) -> List[Dict]:
    out = []
    for e in js.get("events") or []:
        if e.get("type") not in ("Speeches", "Testimony"):
            continue
        try:
            y, m = (int(x) for x in str(e.get("month", "")).split("-"))
            ds = [int(x) for x in re.findall(r"\d+", str(e.get("days", "")))]
        except ValueError:
            continue
        for dd in ds[:1]:
            try:
                day = date(y, m, dd)
            except ValueError:
                continue
            if today <= day <= today + timedelta(days=days):
                out.append({"date": day.isoformat(), "time": e.get("time", ""), "title": e.get("title", ""),
                            "topic": e.get("description", ""), "where": e.get("location", ""), "kind": e["type"]})
    return sorted(out, key=lambda x: (x["date"], x["time"]))


async def refresh(force: bool = False) -> Dict:
    from .freshness import due
    d = load()
    now = time.time()
    d["ts_check"] = now
    todo = due(d, ["rss", "cal", "ust2"], TTL, now, force)
    bad = []
    if "rss" in todo:
        d["try_each"]["rss"] = now
        try:
            items = parse_rss(await http.get(RSS, kind="text", headers=UA, timeout=30, retries=1))
            if not items:
                raise ValueError("empty feed")
            old = {s["url"]: s for s in d.get("speeches") or []}
            for it in items:
                if it["url"] in old and old[it["url"]].get("v") == SCORE_V:
                    continue
                try:
                    it.update(score(text_of(await http.get(it["url"], kind="text", headers=UA, timeout=30, retries=1))), v=SCORE_V)
                except Exception as e:  # noqa: BLE001
                    log.warning("Fed speech %s: %s", it["url"], e)
                old[it["url"]] = {**old.get(it["url"], {}), **it}
            d["speeches"] = sorted(old.values(), key=lambda s: s.get("time", ""), reverse=True)[:KEEP]
            d["ts_each"]["rss"] = now
        except Exception as e:  # noqa: BLE001
            bad.append(f"rss: {e if str(e) else type(e).__name__}")
    if "cal" in todo:
        d["try_each"]["cal"] = now
        try:
            raw = await http.get(CAL, kind="text", headers=UA, timeout=60, retries=1)
            d["upcoming"] = parse_cal(json.loads(raw.lstrip("﻿")), date.today())
            d["ts_each"]["cal"] = now
        except Exception as e:  # noqa: BLE001
            bad.append(f"cal: {e if str(e) else type(e).__name__}")
    if "ust2" in todo:
        d["try_each"]["ust2"] = now
        try:
            first = date.today().replace(day=1)
            got: Dict[str, float] = {}
            for m in ((first - timedelta(days=1)).strftime("%Y%m"), first.strftime("%Y%m")):   # last month + this month
                got.update(parse_ust2(await http.get(UST, params={"data": "daily_treasury_yield_curve", "field_tdr_date_value_month": m},
                                                      kind="text", headers=UA, timeout=40, retries=1)))
            if not got:
                raise ValueError("no 2-year rows")
            d["ust2"] = dict(sorted({**(d.get("ust2") or {}), **got}.items())[-60:])
            d["ts_each"]["ust2"] = now
        except Exception as e:  # noqa: BLE001
            bad.append(f"ust2: {e if str(e) else type(e).__name__}")
    if todo:
        d["ts"] = min(float(d["ts_each"].get(k, 0)) for k in ("rss", "cal"))
        if bad:
            log.warning("Fed speeches: %s", "; ".join(bad))
            HEALTH.fail("fed_speeches", "; ".join(bad), every=TTL)
        else:
            HEALTH.ok("fed_speeches", len(d.get("speeches") or []), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def lean(s: Dict) -> str:
    """Which side the speech dwells on, from word counts only."""
    i, j = s.get("infl") or 0, s.get("jobs") or 0
    if i + j < 5:
        return "—"
    return "多談通膨" if i >= 1.5 * j else "多談就業" if j >= 1.5 * i else "兩邊都談"


DIR_ZH = {"tight": "重點句偏向再收緊（升息或維持高利率）", "ease": "重點句偏向放寬（降息）", "hold": "重點句偏向先觀望", "": ""}


def taipei_date(iso: str) -> Optional[str]:
    try:
        return (datetime.strptime(iso, "%Y-%m-%dT%H:%MZ") + timedelta(hours=8)).strftime("%m/%d %H:%M")
    except ValueError:
        return None
