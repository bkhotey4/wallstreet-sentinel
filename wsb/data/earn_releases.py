"""財報新聞稿原文（2026-11-16）：雲端分析任務的網路擋掉 data.sec.gov 與新聞稿網站（globenewswire 403、prnewswire 404），
11-14～11-16 的「財報後解讀」每次都因為讀不到原文而沒有寫。網站的建置主機（GitHub Actions）連得到 SEC，所以由這裡抓：

  * 範圍：網站財報日曆（data_cache/earn_days.json）最近 3 個美東日、市值 ≥ 200 億美元的公司，加上追蹤池
  * 申報：SEC submissions 裡最近 4 天的 8-K（項目含 2.02 營運結果）或 6-K（外國公司，例如百度、台積電 ADR）
  * 原文：申報索引（index.json）裡的附件 99.1（ex99 / ex-99 / dex991），沒有就取最大的 .htm；去掉 HTML，保留前 30,000 字
  * 發布：網站根目錄 earn_releases.json，分析任務讀這份，不必自己連 SEC
快取 data_cache/earn_releases.json（保留 10 天）。這是公司自己發布的原文，網站不改寫。"""
from __future__ import annotations

import asyncio
import html as _html
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from ..config import DATA_DIR, SEC_USER_AGENT
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_releases.json"
SEC_HDR = {"User-Agent": SEC_USER_AGENT}
TTL = 1800
KEEP_DAYS = 10
MIN_MCAP = 2e10
MAX_CHARS = 30000
PER_RUN = 25
EX99 = re.compile(r"(ex[-_]?99|dex99|exhibit99|ex991)", re.I)


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def candidates(days: Dict, today: str, back: int = 3, floor: float = MIN_MCAP, extra: Optional[List[str]] = None) -> List[Dict]:
    """{sym, date, mcap} reported (calendar) in the last `back` US days, biggest first; `extra` symbols always included."""
    lo = (date.fromisoformat(today) - timedelta(days=back)).isoformat()
    out: Dict[str, Dict] = {}
    for d, v in days.items():
        if not (lo <= d <= today):
            continue
        for r in (v.get("rows") if isinstance(v, dict) else None) or []:
            s = str(r.get("sym") or "").upper()
            if s and (float(r.get("mcap") or 0) >= floor or s in set(extra or [])):
                if s not in out or d > out[s]["date"]:
                    out[s] = {"sym": s, "date": d, "mcap": float(r.get("mcap") or 0), "name": r.get("name") or s}
    return sorted(out.values(), key=lambda x: -x["mcap"])


def recent_filings(js: Dict, since: str) -> List[Dict]:
    """8-K with Item 2.02, or any 6-K, filed on/after `since`: [{acc, date, form, primary}] newest first."""
    f = ((js or {}).get("filings") or {}).get("recent") or {}
    forms = f.get("form") or []
    out = []
    for i, form in enumerate(forms):
        items = str((f.get("items") or [""] * len(forms))[i] or "")
        d = (f.get("filingDate") or [""] * len(forms))[i]
        if d < since or not ((form == "8-K" and "2.02" in items) or form == "6-K"):
            continue
        out.append({"acc": (f.get("accessionNumber") or [""] * len(forms))[i], "date": d, "form": form,
                    "primary": (f.get("primaryDocument") or [""] * len(forms))[i]})
    return out


def pick_exhibit(index: Dict, form: str = "8-K") -> Optional[str]:
    """The press release inside a filing: exhibit 99(.1) first, else (8-K only) the largest .htm.  A 6-K without an exhibit
    99 is skipped: its only .htm is usually the cover page (MUFG/SMFG/Mizuho put their results in PDFs), not the release."""
    items = (index.get("directory") or {}).get("item") or []
    htm = [x for x in items if str(x.get("name", "")).lower().endswith((".htm", ".html"))]
    ex = [x for x in htm if EX99.search(str(x["name"]))]
    if ex:
        return sorted(ex, key=lambda x: str(x["name"]))[0]["name"]
    if form == "6-K":
        return None

    def size(x):
        try:
            return int(x.get("size") or 0)
        except ValueError:
            return 0
    rest = sorted(htm, key=size, reverse=True)
    return rest[0]["name"] if rest else None


def to_text(page: str, limit: int = MAX_CHARS) -> str:
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", page)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</tr>|</div>", "\n", s)
    s = _html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = "\n".join(ln.strip() for ln in s.splitlines() if ln.strip())
    return s[:limit]


async def refresh(force: bool = False, today: Optional[str] = None, extra: Optional[List[str]] = None, budget_s: float = 75) -> Dict:
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts_try", 0)) < TTL:
        return d
    d["ts_try"] = now
    today = today or (datetime.now(timezone.utc) - timedelta(hours=5)).date().isoformat()
    try:
        days = json.loads((DATA_DIR / "earn_days.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        days = {}
    from .edgar_holdings import ticker_map
    try:
        tmap = await ticker_map()
    except Exception as e:  # noqa: BLE001
        log.warning("earn releases: SEC ticker map: %s", e)
        return d
    rel = dict(d.get("rel") or {})
    since = (date.fromisoformat(today) - timedelta(days=4)).isoformat()
    t0, got, bad = time.time(), 0, []
    for c in candidates(days, today, extra=extra)[:PER_RUN]:
        if time.time() - t0 > budget_s:
            break
        if any(k.startswith(c["sym"] + "|") and v.get("date", "") >= since for k, v in rel.items()):
            continue
        cik = (tmap.get(c["sym"]) or tmap.get(c["sym"].replace(".", "-")) or {}).get("cik")
        if not cik:
            continue
        try:
            js = await http.get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=30, retries=1)
            fl = recent_filings(js, since)
            if not fl:
                continue
            f = fl[0]
            base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{f['acc'].replace('-', '')}"
            idx = await http.get(f"{base}/index.json", headers=SEC_HDR, timeout=30, retries=1)
            name = pick_exhibit(idx, f["form"])
            if not name:
                continue
            page = await http.get(f"{base}/{name}", kind="text", headers=SEC_HDR, timeout=40, retries=1)
            text = to_text(page)
            if len(text) < 500:
                continue
            rel[f"{c['sym']}|{f['date']}"] = {"sym": c["sym"], "name": c["name"], "cal_date": c["date"], "date": f["date"], "form": f["form"],
                                             "url": f"{base}/{name}", "chars": len(text), "text": text, "seen": now}
            got += 1
            await asyncio.sleep(0.2)
        except Exception as e:  # noqa: BLE001
            bad.append(f"{c['sym']}: {e if str(e) else type(e).__name__}")
    cut = (date.fromisoformat(today) - timedelta(days=KEEP_DAYS)).isoformat()
    d["rel"] = {k: v for k, v in rel.items() if v.get("date", "") >= cut}
    d["ts"] = now
    if bad:
        log.info("earn releases: %s", "; ".join(bad[:5]))
    HEALTH.ok("earn_releases", got, every=86400) if not bad or got else HEALTH.fail("earn_releases", "; ".join(bad[:3]), every=86400)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def public(d: Optional[Dict] = None) -> Dict:
    d = load() if d is None else d
    items = sorted((x for x in (d.get("rel") or {}).values() if x.get("form") != "6-K" or EX99.search(str(x.get("url") or ""))),
                   key=lambda x: (x.get("date", ""), x.get("chars", 0)), reverse=True)   # cached 6-K cover pages stay out
    return {"updated": datetime.fromtimestamp(float(d.get("ts") or 0), timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if d.get("ts") else None,
            "note": "公司向美國證交會申報的財報新聞稿原文（8-K 項目 2.02 或 6-K 的附件 99.1），網站只去掉 HTML，前 30,000 字。",
            "items": [{k: x.get(k) for k in ("sym", "name", "date", "cal_date", "form", "url", "chars", "text")} for x in items]}
