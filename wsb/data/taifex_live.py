"""台指期即時報價：期交所官方行情頁（mis.taifex.com.tw）用的同一支 JSON，免金鑰。

夜盤（15:00～隔天 05:00）是台股收盤後唯一還在交易的台灣行情，美股晚上大跌時它會先反應。
這裡只讀「臺股期貨」近月（成交量最大的那個月份）：最新價、參考價（日盤結算價）、漲跌幅、是否還在交易。
欄位是期交所自己的名稱；Status 為 TC 表示該盤已收盤。讀不到就回空，不猜。"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

import aiohttp

URL = "https://mis.taifex.com.tw/futures/api/getQuoteList"
HDR = {"Content-Type": "application/json;charset=UTF-8", "User-Agent": "Mozilla/5.0 (WallStreet Sentinel)"}


def _f(x) -> Optional[float]:
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def near(rows: List[Dict]) -> Optional[Dict]:
    """The front contract (largest volume) among the TX futures rows; None when nothing has traded."""
    best = None
    for r in rows or []:
        if not re.fullmatch(r"TXF[A-L]\d-[FM]", str(r.get("SymbolID") or "")):      # monthly contracts only (no spot row, no weeklies)
            continue
        vol, last, ref = _f(r.get("CTotalVolume")), _f(r.get("CLastPrice")), _f(r.get("CRefPrice"))
        if not vol or not last or not ref:
            continue
        if best is None or vol > best["vol"]:
            best = {"sym": r["SymbolID"], "name": r.get("DispCName") or "", "last": last, "ref": ref, "chg": last - ref,
                    "pct": (last / ref - 1) * 100, "time": str(r.get("CTime") or ""), "status": str(r.get("Status") or ""), "vol": vol}
    return best


async def quotes(sess: aiohttp.ClientSession, night: bool = True) -> List[Dict]:
    body = {"MarketType": "1" if night else "0", "SymbolType": "F", "KindID": "1", "CID": "TXF", "ExpireMonth": "", "RowSize": "全部",
            "PageNo": "", "SortColumn": "", "AscDesc": "A"}
    async with sess.post(URL, json=body, headers=HDR, timeout=aiohttp.ClientTimeout(total=20)) as r:
        if r.status >= 300:
            return []
        js = await r.json(content_type=None)
    return ((js or {}).get("RtData") or {}).get("QuoteList") or []
