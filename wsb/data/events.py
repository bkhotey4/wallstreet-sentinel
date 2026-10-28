"""Official event feeds polled fast, for facts that should not wait for the next news round or an AI reading:
Nasdaq trading halts (RSS), Federal Reserve monetary-policy press releases (RSS), and Taiwan listed/OTC companies'
material announcements (TWSE / TPEx OpenAPI, the official machine-readable copy of 公開資訊觀測站 重大訊息).
Each event keeps its own source time so the delay to our alert can be measured."""
from __future__ import annotations

import asyncio
import calendar
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from ..config import SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
HALT_URL = "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts"
FED_URL = "https://www.federalreserve.gov/feeds/press_monetary.xml"
TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap04_L"
TPEX_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap04_O"
ET, TPE = ZoneInfo("America/New_York"), ZoneInfo("Asia/Taipei")

# Nasdaq halt reason codes (nasdaqtrader.com "Trading Halt Codes"); the rest are shown as the raw code
HALT_REASON = {"T1": "重大消息待公布", "T2": "重大消息已公布", "T5": "單一個股暫停（盤中）", "T6": "異常市場活動",
               "T8": "ETF 相關", "T12": "交易所要求補充資訊", "H4": "未符合上市規定", "H9": "未及時申報",
               "H10": "SEC 暫停交易", "H11": "監管疑慮", "LUDP": "波動過大的暫停（價格區間機制）",
               "LUDS": "波動暫停（跨價差情況）", "MWC1": "全市場熔斷（第一級）", "MWC2": "全市場熔斷（第二級）",
               "MWC3": "全市場熔斷（第三級）", "M": "波動暫停", "D": "下市"}


def parse_halts(raw: bytes) -> List[Dict]:
    import feedparser
    out = []
    for e in feedparser.parse(raw).entries:
        sym = (e.get("ndaq_issuesymbol") or e.get("title") or "").strip().upper()
        d, t = (e.get("ndaq_haltdate") or "").strip(), (e.get("ndaq_halttime") or "").strip()
        if not sym or not d:
            continue
        try:
            ts = datetime.strptime(f"{d} {t[:8] or '00:00:00'}", "%m/%d/%Y %H:%M:%S").replace(tzinfo=ET).timestamp()
        except ValueError:
            continue
        code = (e.get("ndaq_reasoncode") or "").strip().upper()
        out.append({"sym": sym, "name": (e.get("ndaq_issuename") or "").strip(), "market": (e.get("ndaq_market") or "").strip(),
                    "code": code, "reason": HALT_REASON.get(code, code or "未說明"), "ts": ts,
                    "when": f"{d} {t[:5]} ET", "resume": (e.get("ndaq_resumptiontradetime") or "").strip()})
    return out


def parse_fed(raw: bytes) -> List[Dict]:
    import feedparser
    out = []
    for e in feedparser.parse(raw).entries[:20]:
        st = e.get("published_parsed") or e.get("updated_parsed")
        if not st or not e.get("title"):
            continue
        out.append({"title": re.sub(r"\s+", " ", e["title"]).strip(), "link": e.get("link", ""), "ts": calendar.timegm(st)})
    return out


def _roc(d: str, t: str = "") -> Optional[float]:
    """ROC date "1151026" + time "70004" / "191051" (HHMMSS, leading zero dropped) → Unix time (Taipei)."""
    d = re.sub(r"\D", "", str(d or ""))
    if len(d) < 6:
        return None
    t = re.sub(r"\D", "", str(t or "")).zfill(6)[:6]
    try:
        return datetime(int(d[:-4]) + 1911, int(d[-4:-2]), int(d[-2:]), int(t[:2]), int(t[2:4]), int(t[4:])).replace(tzinfo=TPE).timestamp()
    except ValueError:
        return None


def parse_mops(rows, market: str) -> List[Dict]:
    out = []
    for r in rows if isinstance(rows, list) else []:
        r = {str(k).strip(): v for k, v in r.items()}                 # TWSE ships "主旨 " with a trailing space
        code = str(r.get("公司代號") or r.get("SecuritiesCompanyCode") or "").strip()
        ts = _roc(r.get("發言日期"), r.get("發言時間"))
        if not code or ts is None:
            continue
        out.append({"code": code, "name": str(r.get("公司名稱") or r.get("CompanyName") or "").strip(), "market": market,
                    "subject": re.sub(r"\s+", " ", str(r.get("主旨") or "")).strip(), "clause": str(r.get("符合條款") or "").strip(),
                    "ts": ts, "when": datetime.fromtimestamp(ts, TPE).strftime("%Y-%m-%d %H:%M")})
    return out


class OfficialEvents:
    def __init__(self) -> None:
        self.halts: List[Dict] = []
        self.fed: List[Dict] = []
        self.mops: List[Dict] = []
        self.ts = 0.0

    async def _one(self, name: str, coro, every: float):
        try:
            v = await coro
            HEALTH.ok(name, len(v), every=every)
            return v
        except Exception as e:  # noqa: BLE001
            log.info("%s failed: %s", name, e)
            HEALTH.fail(name, e, every=every)
            return None

    async def refresh(self) -> None:
        every = float((SETTINGS.get("refresh") or {}).get("official_events", 120))

        async def halts():
            return parse_halts(await http.get(HALT_URL, kind="bytes", retries=1))

        async def fed():
            return parse_fed(await http.get(FED_URL, kind="bytes", retries=1))

        async def listed():
            return parse_mops(await http.get(TWSE_URL, timeout=30, retries=1), "上市")

        async def otc():
            return parse_mops(await http.get(TPEX_URL, timeout=30, retries=1), "上櫃")

        # 上市 and 上櫃 are separate sources: each has its own health light and keeps its own last good list
        h, f, m1, m2 = await asyncio.gather(self._one("nasdaq_halts", halts(), every), self._one("fed_monetary", fed(), every),
                                            self._one("tw_mops_listed", listed(), every * 5), self._one("tw_mops_otc", otc(), every * 5))
        # a failed source keeps its last good list (shown as stale by /status), never an empty "nothing happened"
        self.halts = h if h is not None else self.halts
        self.fed = f if f is not None else self.fed
        self._m1 = m1 if m1 is not None else getattr(self, "_m1", [x for x in self.mops if x.get("market") == "上市"])
        self._m2 = m2 if m2 is not None else getattr(self, "_m2", [x for x in self.mops if x.get("market") == "上櫃"])
        self.mops = self._m1 + self._m2
        self.ts = time.time()
