"""韓國出口快報（2026-11-16，使用者選的第 6 項）：韓國關稅廳每月 11 日（1～10 日）、21 日（1～20 日）、1 日（上個月）公布的
出口初值，含晶片（半導體）出口金額。比台灣的出口數據早兩到三週，是全世界最早的晶片需求數字之一。

來源：韓國關稅廳官方報導資料版（www.customs.go.kr，보도자료），標題「YYYY년 M월 1일 ~ M월 D일 수출입 현황 [잠정치]」與
「YYYY년 M월 수출입 현황 [잠정치]」。列表用網站本身的搜尋（標題含「수출입」），內文用網站本身開啟文章的表單（POST），
和用瀏覽器點開一樣，不繞過任何檢查。從內文讀出口金額、年增率、晶片出口金額（有寫年增率就讀，沒有就和去年同期那篇比）、
依工作天數調整後的日均出口年增率。快取 data_cache/econ_korea_exports.json。"""
from __future__ import annotations

import html as _html
import json
import logging
import os
import re
import time
from datetime import date
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_korea_exports.json"
TTL = 3 * 3600
BASE = "https://www.customs.go.kr/kcs/na/ntt"
PAGE = "https://www.customs.go.kr/kcs/na/ntt/selectNttList.do?mi=2891&bbsId=1362"
HDR = {"User-Agent": "WallStreetSentinel research (public data reader)"}
PART = re.compile(r"(\d{4})년\s*(\d{1,2})월\s*1일\s*~\s*(\d{1,2})월\s*(\d{1,2})일\s*수출입\s*현황")
MONTH = re.compile(r"(\d{4})년\s*(\d{1,2})월\s*(?:월간\s*)?수출입\s*현황\s*\[잠정치\]")
ROW = re.compile(r'data-id="(\d+)"\s+data-url="([0-9a-f]+)"\s+class="nttInfoBtn"\s+title="([^"]*)"')


def key_of(title: str) -> Optional[Tuple[str, str]]:
    """('2026-11-10', 'part') for 1–10 Nov 2026, ('2026-10-M', 'month') for the October preliminary month; else None."""
    m = PART.search(title)
    if m and int(m.group(2)) == int(m.group(3)):
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(4)):02d}", "part"
    m = MONTH.search(title)
    if m and "확정" not in title:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-M", "month"
    return None


def parse_list(page: str) -> List[Dict]:
    out = []
    for nid, url, title in ROW.findall(page):
        t = _html.unescape(title).strip()
        k = key_of(t)
        if k:
            out.append({"id": nid, "u": url, "title": t, "key": k[0], "kind": k[1]})
    return out


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def parse_detail(page: str) -> Dict:
    """Numbers from one release (whitespace removed before matching, so '335 억 달러' and '335억달러' both read)."""
    txt = _html.unescape(re.sub(r"<[^>]+>", " ", page)).replace("\xa0", " ")
    s = re.sub(r"\s+", "", txt)
    out: Dict = {}
    m = re.search(r"수출(?:은|이)?([\d,\.]+)억달러(?:로|를기록)?[,，]?(?:전년동[기월]대비|전년대비)([\d\.]+)%(증가|감소)", s)
    if m:
        out["exp"] = _num(m.group(1))
        out["yoy"] = _num(m.group(2)) * (1 if m.group(3) == "증가" else -1)
    m = re.search(r"반도체\(?([\d,\.]+)억달러", s)
    if m:
        out["chip"] = _num(m.group(1))
    m = re.search(r"반도체[^%]{0,40}?\(([+\-−△]?)([\d\.]+)%\)", s)
    if m:
        out["chip_yoy"] = _num(m.group(2)) * (-1 if m.group(1) in ("-", "−", "△") else 1)
    m = re.search(r"일평균수출액\[\(’?\d\d\.\d+\.\)([\d\.]+),\(’?\d\d\.\d+\.\)([\d\.]+)억달러\]([\d\.]+)%(증가|감소)", s)
    if m:
        out["day0"], out["day1"] = _num(m.group(1)), _num(m.group(2))
        out["day_yoy"] = _num(m.group(3)) * (1 if m.group(4) == "증가" else -1)
    return out


def prior_key(k: str) -> str:
    return f"{int(k[:4]) - 1:04d}{k[4:]}"


def view(d: Optional[Dict] = None) -> Dict:
    """Releases newest first with chip year-on-year filled from last year's same period when the text gave none."""
    d = load() if d is None else d
    rel = d.get("rel") or {}
    rows = []
    for k in sorted(rel, key=lambda x: (x[:7], x[8:] if x[8:] != "M" else "99"), reverse=True):
        r = dict(rel[k], key=k)
        p = rel.get(prior_key(k)) or {}
        if r.get("chip_yoy") is None and r.get("chip") and p.get("chip"):
            r["chip_yoy"], r["chip_yoy_calc"] = (r["chip"] / p["chip"] - 1) * 100, True
        rows.append(r)
    return {"rows": rows, "ts": d.get("ts")}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def refresh(force: bool = False, pages: int = 3, per_run: int = 30) -> Dict:
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts_try", 0)) < TTL:
        return d
    d["ts_try"] = now
    rel = dict(d.get("rel") or {})
    bad = []
    items: List[Dict] = []
    for p in range(1, (pages if len(rel) < 20 else 1) + 1):          # three pages once (about three years), then page 1
        try:
            page = await http.get(f"{BASE}/selectNttList.do", params={"mi": "2891", "bbsId": "1362", "searchType": "sj",
                                  "searchValue": "수출입", "listCo": "50", "currPage": str(p)}, kind="text", headers=HDR, timeout=40, retries=1)
            items += parse_list(page)
        except Exception as e:  # noqa: BLE001
            bad.append(f"list {p}: {e if str(e) else type(e).__name__}")
            break
    todo = [x for x in items if x["key"] not in rel][:per_run]
    for x in todo:
        try:
            page = await http.post(f"{BASE}/selectNttInfo.do", data={"mi": "2891", "bbsId": "1362", "nttSn": x["id"], "nttSnUrl": x["u"]},
                                   kind="text", headers=HDR, timeout=40, retries=1)
            v = parse_detail(page)
            if v.get("exp") is not None:
                rel[x["key"]] = dict(v, title=x["title"], kind=x["kind"], id=x["id"], u=x["u"], seen=now)
        except Exception as e:  # noqa: BLE001
            bad.append(f"{x['key']}: {e if str(e) else type(e).__name__}")
    d["rel"] = rel
    if items:
        d["ts"] = now
    if bad:
        log.warning("korea exports: %s", "; ".join(bad[:4]))
        HEALTH.fail("korea_exports", "; ".join(bad[:4]), every=TTL)
    else:
        HEALTH.ok("korea_exports", len(rel), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def released(k: str) -> date:
    """The day a release comes out: the day after a part-month period (1–10 → the 11th), the 1st of the next month for a month."""
    y, m = int(k[:4]), int(k[5:7])
    if k.endswith("-M"):
        return date(y + (m == 12), m % 12 + 1, 1)
    return date(y, m, int(k[8:10])) .fromordinal(date(y, m, int(k[8:10])).toordinal() + 1)


def alerts(v: Dict, today: date) -> List[Dict]:
    """The newest release once, only within two days of its release day (a first backfill never sends old ones)."""
    rows = v.get("rows") or []
    if not rows:
        return []
    r = rows[0]
    if (today - released(r["key"])).days > 2:
        return []
    return [{"key": f"korea:{r['key']}", "row": r, "lv": 1}]
