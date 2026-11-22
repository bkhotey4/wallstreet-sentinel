"""台股法說會行事曆（2026-11-22，使用者：「既然有美股財報，怎麼沒有台股財報? 例如台股財報前瞻」）。

來源：公開資訊觀測站「法人說明會一覽表」（mopsov.twse.com.tw/mops/web/ajax_t100sb02_1，上市 sii／上櫃 otc，依民國年月查詢）。
雲端主機常連不到公開資訊觀測站，所以和月營收一樣：電腦端抓好寫進 research_feed/tw_irs_seed.json（附抓取時間），雲端讀不到時用它。
每一場都標「自辦法說」或「券商論壇」：摘要裡寫「受邀」「論壇」「證券舉辦」的是券商邀請的投資論壇，通常不公布新的財務數字。
"""
from __future__ import annotations

import html as _html
import json
import logging
import os
import re
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR

log = logging.getLogger(__name__)
URL = "https://mopsov.twse.com.tw/mops/web/ajax_t100sb02_1"
FILE = DATA_DIR / "econ_tw_irs.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_irs_seed.json"
TTL = 12 * 3600
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
_ROW = re.compile(r"<tr class='(?:even|odd)' data-type='body'\s*>(.*?)</tr>", re.S)
_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
FORUM = ("受邀", "論壇", "證券舉辦", "證券主辦", "邀請", "研討會", "Conference", "conference", "Forum", "forum", "Corporate Day",
         "Corporate Access", "Tech Trip", "Tech Tour", "Summit", "NDR", "Non-Deal Roadshow")   # broker events named in English


def roc_to_iso(s: str) -> Optional[str]:
    m = re.match(r"\s*(\d{2,3})/(\d{1,2})/(\d{1,2})", s or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)) + 1911, int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def _txt(x: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", x or ""))).strip()


def parse(page: str, board: str) -> List[Dict]:
    out = []
    for row in _ROW.findall(page or ""):
        td = _TD.findall(row)
        if len(td) < 6:
            continue
        code, name, d, tm, place, summ = (_txt(x) for x in td[:6])
        iso = roc_to_iso(d)
        if not re.fullmatch(r"\d{4}[A-Z]?", code) or not iso:
            continue
        slides = bool(re.search(r"\.pdf", row, re.I))
        out.append({"code": code, "name": name, "date": iso, "time": tm, "place": place[:60], "summary": summ[:240],
                    "kind": "券商論壇" if any(k in summ for k in FORUM) else "自辦法說", "board": board, "slides": slides})
    return out


def months_ahead(today: date, n: int = 2) -> List[tuple]:
    out, y, m = [], today.year, today.month
    for _ in range(n):
        out.append((y - 1911, m))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def fetch(today: Optional[date] = None, timeout: float = 20.0) -> List[Dict]:
    """Blocking (requests): this month and next, listed and OTC.  Raises when nothing at all came back."""
    import requests
    today = today or date.today()
    rows: List[Dict] = []
    for typek, board in (("sii", "上市"), ("otc", "上櫃")):
        for y, m in months_ahead(today):
            got: List[Dict] = []
            for attempt in range(3):                       # 11-22: one of the four replies came back empty → 127 rows instead of 228
                r = requests.post(URL, data={"encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "TYPEK": typek,
                                             "year": y, "month": f"{m:02d}", "co_id": ""}, headers=UA, timeout=timeout)
                r.encoding = "utf-8"
                got = parse(r.text, board) if r.ok else []
                if got or (r.ok and "查無" in r.text):
                    break
                time.sleep(3.0 * (attempt + 1))
            rows += got
            time.sleep(1.5)
    if not rows:
        raise RuntimeError("MOPS 法說會 list empty (blocked or changed)")
    seen, out = set(), []
    for x in sorted(rows, key=lambda x: (x["date"], x["time"], x["code"])):
        k = (x["code"], x["date"], x["time"])
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


def _load(f: Path) -> Dict:
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except (OSError, ValueError):
        return {}


def refresh(force: bool = False) -> Dict:
    """Cached list, refreshed every 12 h; on failure the newer of the cache and the PC seed is used."""
    d = _load(FILE)
    if not force and d.get("rows") and time.time() - float(d.get("ts") or 0) < TTL:
        return d
    try:
        rows = fetch()
        d = {"ts": time.time(), "fetched": _tpe_now(), "source": "公開資訊觀測站法人說明會一覽表", "rows": rows}
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FILE)
        return d
    except Exception as e:  # noqa: BLE001
        log.info("MOPS 法說會 list unavailable here (%s); using cache / seed", e)
    s = _load(SEED)
    return s if str(s.get("fetched") or "") > str(d.get("fetched") or "") else d


def write_seed(path: Path = SEED) -> Dict:
    """PC → cloud relay: the same list, written to the public research_feed (public company announcements)."""
    d = refresh(force=True)
    old = _load(Path(path))
    if old.get("rows") and len(d.get("rows") or []) < 0.7 * len(old["rows"]):      # a partial fetch must not replace a good copy
        log.warning("法說會 list shrank %d → %d; seed kept", len(old["rows"]), len(d.get("rows") or []))
        return old
    if d.get("rows"):
        out = {"fetched": d.get("fetched"), "source": d.get("source"), "rows": d["rows"]}
        Path(path).write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
        return out
    return {}


def _tpe_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
