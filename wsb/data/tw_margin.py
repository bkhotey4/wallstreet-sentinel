"""信用交易擔保維持率最低標準（追繳線）與證交所市場措施（2026-11-25）。

11/24 起追繳線由 130% 降到 120%，本站四個地方還寫死 130%，而且追繳日曆把已經取消的處分日當成會發生。
所以門檻改成：證交所官方新聞清單（OpenAPI newsList）讀到的調整＋下面核對過的歷史，不再寫在文字裡。

核對：證交所 2026-11-23 新聞稿（PDF 全文，2026-11-25 讀）——
  * 11/24 起收盤後整戶擔保維持率低於 120% 才通知追繳，通知送達日起 2 個營業日內補繳。
  * 11/24 前低於 130% 已被通知補繳者，一律取消追繳紀錄、不處分擔保品。
130%：中央社 2026-11-24 引金管會（2015 年由 120% 回到 130%；這裡只需要 2015 年之後，起用日取當年年初）。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_margin.json"
U_NEWS = "https://openapi.twse.com.tw/v1/news/newsList"
SRC = "https://www.twse.com.tw/zh/about/news/news/content.html?8a8216d6a19afd9c01a2072d582a0593"
KNOWN = (("2015-01-01", 130), ("2026-11-24", 120))         # (起用日, %)，來源見上
AMNESTY_BEFORE = "2026-11-24"                              # 這天以前的追繳通知一律取消、不處分（SRC）
TTL = 3 * 3600
TPE = timezone(timedelta(hours=8))
MEASURE = re.compile(r"維持率|平盤以下|限制放空|禁止放空|抵繳擔保|降低當沖|暫停當沖|漲跌幅限制|借券賣出.{0,6}(?:限制|暫停)|暫停.{0,6}借券賣出|融券保證金")
CHANGE = re.compile(r"自\s*(\d{2,3})年(\d{1,2})月(\d{1,2})日起.*擔保維持率.*?由\s*(\d{3})\s*%.*?[至為]\s*(\d{3})\s*%")


def _roc(s) -> Optional[str]:
    m = re.fullmatch(r"(\d{3})(\d{2})(\d{2})", str(s or ""))
    return f"{int(m.group(1)) + 1911}-{m.group(2)}-{m.group(3)}" if m else None


def parse_news(rows) -> List[Dict]:
    """證交所新聞清單 → 市場措施（標題就寫完整內容；內文是 PDF）。"""
    out = []
    for r in rows if isinstance(rows, list) else []:
        t, d = str(r.get("Title") or "").strip(), _roc(r.get("Date"))
        if d and MEASURE.search(t) and str(r.get("Url") or "").startswith("https://www.twse.com.tw/"):
            out.append({"date": d, "unit": "證交所", "title": t, "url": r["Url"], "by": "證交所"})
    return sorted(out, key=lambda r: r["date"], reverse=True)


def changes(news: List[Dict]) -> List:
    out = []
    for r in news or []:
        m = CHANGE.search(r.get("title") or "")
        if m:
            y, mo, d, _, new = m.groups()
            try:
                out.append((date(int(y) + 1911, int(mo), int(d)).isoformat(), int(new)))
            except ValueError:
                continue
    return out


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def refresh(force: bool = False) -> Dict:
    d = load()
    if not force and time.time() - float(d.get("ts") or 0) < TTL:
        return d
    d["ts"] = time.time()                                  # a failed try also waits: KNOWN still answers
    try:
        import requests
        r = requests.get(U_NEWS, headers={"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}, timeout=30)
        r.raise_for_status()
        old = {x["url"]: x for x in d.get("news") or []}
        new = {x["url"]: x for x in parse_news(r.json())}
        d["news"] = sorted({**old, **new}.values(), key=lambda x: x["date"], reverse=True)[:30]
        d["fetched"] = datetime.now(TPE).strftime("%Y-%m-%d %H:%M")
    except Exception as e:  # noqa: BLE001
        log.info("twse news unavailable: %s", e)
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError:
        pass
    return d


def floor_on(day: Optional[str] = None, news: Optional[List[Dict]] = None) -> int:
    """那一天適用的追繳線（%）：核對過的歷史＋官方新聞讀到的調整，取起用日最晚的那一個。"""
    day = day or datetime.now(TPE).date().isoformat()
    news = load().get("news") if news is None else news
    table = dict(KNOWN)
    table.update(dict(changes(news or [])))
    return max((x for x in table.items() if x[0] <= day), default=KNOWN[0])[1]


def voided(notice: str, dispose: str) -> bool:
    """追繳通知在豁免日前、處分還沒到：官方已取消。"""
    return notice < AMNESTY_BEFORE <= dispose
