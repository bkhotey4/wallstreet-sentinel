"""政府做了什麼：美國聯邦公報（Federal Register）官方 API，免金鑰。

抓過去 45 天三類文件：
  * 總統文件（行政命令、公告、備忘錄、國家緊急狀態延長）
  * 商務部工業安全局 BIS（出口管制、實體清單）的規則與公告
  * 美國貿易代表署 USTR（301 條款關稅、產品排除）的公告
  * （2026-11-19）醫保署 CMS 的正式與擬議規則、財政部 OFAC 制裁
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
          "executive_order_number", "document_number",
          # 11-28 gap review (the 301 miss): the forward timeline — comment deadlines, hearings, effective dates
          "comments_close_on", "effective_on", "dates")
QUERIES = (
    ("pres", {"conditions[type][]": "PRESDOCU"}),
    ("bis", {"conditions[agencies][]": "industry-and-security-bureau"}),
    ("ustr", {"conditions[agencies][]": "trade-representative-office-of-united-states"}),
    # 2026-11-19: UnitedHealth −6% and CVS −4% on a CMS anti-fraud rule that this card never saw (Gemini found it) —
    # Medicare / Medicaid rules move the insurers and drug makers; final and proposed rules only (CMS posts many notices)
    ("cms", {"conditions[agencies][]": "centers-for-medicare-medicaid-services", "conditions[type][]": "RULE"}),
    ("cms_p", {"conditions[agencies][]": "centers-for-medicare-medicaid-services", "conditions[type][]": "PRORULE"}),
    ("ofac", {"conditions[agencies][]": "foreign-assets-control-office"}),
)
# (主題, 英文, 關鍵字, 先動的資產 symbol, 資產中文) — 依序比對，第一個命中的算數
TOPICS = (
    ("出口管制／半導體", "Export controls / chips", r"export control|entity list|semiconductor|integrated circuit|chip|polysilicon|advanced computing|end-user|remote access|super ?intelligence|frontier (?:ai|model)|model weights|ai (?:model|chip|compute)",
     "SMH", "半導體 ETF"),
    ("關稅與貿易", "Tariffs & trade", r"tariff|duty|duties|section 301|section 232|import|trade agreement|reciprocal|customs|product exclusion|de minimis",
     "^GSPC", "標普 500"),
    ("能源與制裁", "Energy & sanctions", r"\biran\b|russia|venezuela|\boil\b|petroleum|crude|natural gas|\blng\b|sanction|energy emergency",
     "BZ=F", "布蘭特原油"),
    ("航運與造船", "Shipping", r"maritime|shipbuilding|vessel|port fees|logistics", "BZ=F", "布蘭特原油"),
    # 中國排在金融之前：「…Securities Investments That Finance Certain Companies of the PRC」是中國題目，不是加密資產。
    # 用美國掛牌的中概股 ETF：港股在美國公布之前就收盤了，看恒指等於看「消息出來前」的那一天
    ("中國", "China", r"\bchina\b|people's republic|chinese", "KWEB", "中概網路股 ETF"),
    ("金融與加密資產", "Finance & crypto", r"digital asset|crypto|stablecoin|\bbank|federal reserve|treasury market",
     "BTC-USD", "比特幣"),
    ("醫療保險與藥價", "Medicare & drug prices", r"medicare|medicaid|drug price|health insurance|managed care|risk adjustment|"
     r"part d\b|affordable care|program integrity|fraud, waste", "XLV", "醫療保健 ETF"),
    ("人工智慧", "AI", r"artificial intelligence|\bai\b|data center", "SMH", "半導體 ETF"),
)
# 每年例行的延長（國家緊急狀態續期）：內容不變，不算新政策，不列入「大動」
ROUTINE = re.compile(r"continuation of the national emergency|continuation of the emergency", re.I)
SKIP = re.compile(r"information collection|performance review board|temporary denial|denying export privileges|order renewing|"
                  r"sunshine act|meeting|; correction$|national .{0,30} (day|week|month)|week, 20\d\d|day, 20\d\d|monument|anniversary|honoring", re.I)


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
            "url": r.get("html_url"), "agency": ags[0] if ags else "", "routine": bool(ROUTINE.search(r.get("title", ""))),
            "close": r.get("comments_close_on"), "effective": r.get("effective_on"), "dates": (r.get("dates") or "")[:600], **t}


_MON = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE = re.compile(rf"({_MON})\s+(\d{{1,2}}),\s+(\d{{4}})")


def timeline(doc: Dict, today: date) -> List[Dict]:
    """Pure: future dated steps of one document — comment deadline, effective date, and every 'Month D, YYYY' in its DATES text
    with the clause around it (e.g. a public hearing).  One entry per date, the most specific wording kept."""
    from datetime import datetime as _dt
    out: Dict[str, str] = {}
    if doc.get("close"):
        out[doc["close"]] = "意見徵詢截止"
    if doc.get("effective"):
        out[doc["effective"]] = "生效"
    # "12:01 a.m. eastern time on January 9" — abbreviations must not end the clause (11-28)
    text = re.sub(r"\b([ap])\.m\.", r"\1m", doc.get("dates") or "", flags=re.I).replace("U.S.", "US")
    for m in _DATE.finditer(text):
        try:
            d = _dt.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").date().isoformat()
        except ValueError:
            continue
        a = max(text.rfind(".", 0, m.start()), text.rfind(";", 0, m.start())) + 1
        b = min([i for i in (text.find(".", m.end()), text.find(";", m.end())) if i >= 0] or [len(text)])
        clause = text[a:b].strip()
        out.setdefault(d, clause[:200])
    return [{"date": d, "what": w} for d, w in sorted(out.items()) if d >= today.isoformat()]


async def refresh(force: bool = False) -> Dict:
    from .freshness import due
    d = load()
    now = time.time()
    d["ts_check"] = now
    stale_fields = any("dates" not in x for x in d.get("docs") or [])   # 11-28: cached docs from before the timeline fields
    if not due(d, ["docs"], TTL, now, force or stale_fields):
        return d
    d["try_each"]["docs"] = now
    since = (date.today() - timedelta(days=DAYS)).isoformat()
    out, bad = {}, []
    for name, cond in QUERIES:
        try:
            for page in range(1, 6):                              # 100 per page; a busy 45 days can need more than one
                params = {"per_page": "100", "page": str(page), "order": "newest", "conditions[publication_date][gte]": since, **cond}
                qs = list(params.items()) + [("fields[]", f) for f in FIELDS]
                js = await http.get(API + "?" + "&".join(f"{k}={v}" for k, v in qs), timeout=60, retries=1)
                for r in js.get("results") or []:
                    k = keep(r)
                    if k and k["id"]:
                        out[k["id"]] = {**k, "src": name}
                if page >= int(js.get("total_pages") or 1):
                    break
        except Exception as e:  # noqa: BLE001
            bad.append(name)
            log.warning("Federal Register %s: %s", name, e if str(e) else type(e).__name__)
    if len(bad) < len(QUERIES):
        for x in d.get("docs") or []:                            # a failed query keeps that source's earlier docs
            if x.get("src") in bad and x.get("id") not in out and (x.get("date") or "") >= since:
                out[x["id"]] = x
        d["docs"] = sorted(out.values(), key=lambda x: (x["date"] or "", x["id"]), reverse=True)
        if not bad:                                               # partial success: retried in an hour, not after a full TTL
            d["ts_each"]["docs"], d["ts"] = now, now
    if bad:
        HEALTH.fail("fed_register", "failed: " + ", ".join(bad), every=TTL)
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
