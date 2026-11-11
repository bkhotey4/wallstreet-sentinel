"""政府做了什麼：美國聯邦公報（Federal Register）官方 API，免金鑰。

抓過去 45 天三類文件：
  * 總統文件（行政命令、公告、備忘錄、國家緊急狀態延長）
  * 商務部工業安全局 BIS（出口管制、實體清單）的規則與公告
  * 美國貿易代表署 USTR（301 條款關稅、產品排除）的公告
只留和市場有關的（標題或摘要命中 TOPICS 關鍵字），去掉行政雜項（資料蒐集徵詢、個別公司的出口禁令續期、人事）。
每則標一個主題和「先動的資產」，卡片端算該資產在公報刊登當天漲跌，和平常一天比。
注意：刊登日常晚於簽署日（新聞通常在簽署當天就出來），所以市場反應可能早就發生；只說「刊登當天」，不說「因為這份文件」。
快取 data_cache/econ_fedreg.json，6 小時一次。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_fedreg.json"
TTL = 6 * 3600
API = "https://www.federalregister.gov/api/v1/documents.json"
PAGE = "https://www.federalregister.gov/"
DAYS = 45
FIELDS = ("title", "abstract", "publication_date", "signing_date", "type", "subtype", "html_url", "agencies",
          "executive_order_number", "document_number")
QUERIES = (
    ("pres", {"conditions[type][]": "PRESDOCU"}),
    ("bis", {"conditions[agencies][]": "industry-and-security-bureau"}),
    ("ustr", {"conditions[agencies][]": "trade-representative-office-of-united-states"}),
)
# (主題, 英文, 關鍵字, 先動的資產 symbol, 資產中文) — 依序比對，第一個命中的算數
TOPICS = (
    ("出口管制／半導體", "Export controls / chips", r"export control|entity list|semiconductor|integrated circuit|chip|polysilicon|advanced computing|end-user",
     "SMH", "半導體 ETF"),
    ("關稅與貿易", "Tariffs & trade", r"tariff|duty|duties|section 301|section 232|import|trade agreement|reciprocal|customs|product exclusion|de minimis",
     "^GSPC", "標普 500"),
    ("能源與制裁", "Energy & sanctions", r"\biran\b|russia|venezuela|\boil\b|petroleum|crude|natural gas|\blng\b|sanction|energy emergency",
     "BZ=F", "布蘭特原油"),
    ("航運與造船", "Shipping", r"maritime|shipbuilding|vessel|port fees|logistics", "BZ=F", "布蘭特原油"),
    ("金融與加密資產", "Finance & crypto", r"digital asset|crypto|stablecoin|bank|securities investments|federal reserve|treasury market",
     "BTC-USD", "比特幣"),
    ("人工智慧", "AI", r"artificial intelligence|\bai\b|data center", "SMH", "半導體 ETF"),
    ("中國", "China", r"\bchina\b|people's republic|chinese", "^HSI", "恒生指數"),
)
SKIP = re.compile(r"information collection|performance review board|temporary denial|denying export privileges|order renewing|"
                  r"sunshine act|meeting|national .{0,30} (day|week|month)|week, 20\d\d|day, 20\d\d|monument|anniversary|honoring", re.I)


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def topic(title: str, abstract: str = "") -> Optional[Dict]:
    if SKIP.search(title or ""):
        return None
    txt = f"{title} {abstract or ''}"
    for zh, en, pat, sym, sym_zh in TOPICS:
        if re.search(pat, txt, re.I):
            return {"topic": zh, "topic_en": en, "sym": sym, "sym_zh": sym_zh}
    return None


def keep(r: Dict) -> Optional[Dict]:
    t = topic(r.get("title", ""), r.get("abstract", ""))
    if not t:
        return None
    ags = [a.get("name") or a.get("raw_name") or "" for a in r.get("agencies") or []]
    return {"id": r.get("document_number"), "title": r.get("title", ""), "date": r.get("publication_date"),
            "signed": r.get("signing_date"), "type": r.get("subtype") or r.get("type"), "eo": r.get("executive_order_number"),
            "url": r.get("html_url"), "agency": ags[0] if ags else "", **t}


async def refresh(force: bool = False) -> Dict:
    from .freshness import due
    d = load()
    now = time.time()
    d["ts_check"] = now
    if not due(d, ["docs"], TTL, now, force):
        return d
    d["try_each"]["docs"] = now
    since = (date.today() - timedelta(days=DAYS)).isoformat()
    out, bad = {}, []
    for name, cond in QUERIES:
        try:
            params = {"per_page": "100", "order": "newest", "conditions[publication_date][gte]": since, **cond}
            qs = list(params.items()) + [("fields[]", f) for f in FIELDS]
            js = await http.get(API + "?" + "&".join(f"{k}={v}" for k, v in qs), timeout=60, retries=1)
            for r in js.get("results") or []:
                k = keep(r)
                if k and k["id"]:
                    out[k["id"]] = {**k, "src": name}
        except Exception as e:  # noqa: BLE001
            bad.append(f"{name}: {e if str(e) else type(e).__name__}")
    if len(bad) < len(QUERIES):
        d["docs"] = sorted(out.values(), key=lambda x: (x["date"] or "", x["id"]), reverse=True)
        d["ts_each"]["docs"], d["ts"] = now, now
    if bad:
        log.warning("Federal Register: %s", "; ".join(bad))
        HEALTH.fail("fed_register", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("fed_register", len(d.get("docs") or []), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


TYPE_ZH = {"Executive Order": "行政命令", "Proclamation": "總統公告", "Memorandum": "總統備忘錄", "Notice": "公告",
           "Rule": "規則", "Proposed Rule": "規則草案", "Presidential Document": "總統文件", "Determination": "總統裁定"}


def type_zh(t: str) -> str:
    return TYPE_ZH.get(t or "", t or "")
