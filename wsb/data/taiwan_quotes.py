"""Official TWSE/TPEx end-of-day quotes, separate from adjusted Yahoo history.

The index's unadjusted daily bars may safely extend index history. Stock/ETF
cash closes must NOT be spliced into auto-adjusted technical price series.
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "taiwan_quotes.json"
URLS = {
    "TWSE": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
    "TPEx": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
    "TWSE-index": "https://openapi.twse.com.tw/v1/indicesReport/MI_5MINS_HIST",
}


def number(value):
    try:
        n = float(str(value).replace(",", "").strip())
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def trading_date(value):
    s = re.sub(r"[/.-]", "", str(value))
    if not s.isdigit() or len(s) not in (7, 8):
        return None
    try:
        year = int(s[:-4]) + (1911 if len(s) == 7 else 0)
        d = date(year, int(s[-4:-2]), int(s[-2:]))
        return d.isoformat() if date(1990, 1, 1) <= d <= datetime.now(ZoneInfo("Asia/Taipei")).date() else None
    except ValueError:
        return None


def is_taiwan(symbol):
    return symbol == "^TWII" or symbol.endswith((".TW", ".TWO"))


def parse(rows, source):
    if not isinstance(rows, list):
        raise ValueError("Expected official quote rows")
    out = {}
    if source == "TWSE-index":
        bars = {}
        for r in rows:
            if not isinstance(r, dict):
                continue
            day, px = trading_date(r.get("Date")), number(r.get("ClosingIndex"))
            if day and px is not None and px > 0:
                bars[day] = px
        ordered = sorted(bars)
        if ordered:
            day = ordered[-1]
            px, prev = bars[day], bars[ordered[-2]] if len(ordered) > 1 else None
            out["^TWII"] = dict(price=px, prev=prev, chg_pct=(px / prev - 1) * 100 if prev else None,
                                asof=day, name="台灣加權指數", source="TWSE", bars=bars, fetched=time.time())
        return out
    tw = source == "TWSE"
    for r in rows:
        if not isinstance(r, dict):
            continue
        code = str(r.get("Code" if tw else "SecuritiesCompanyCode", "")).strip()
        # Common/preferred stocks and ETFs; exclude the much larger warrant universe.
        if not re.fullmatch(r"(?:\d{4}[A-Z]?|00\d{3,4}[A-Z]?)", code):
            continue
        day = trading_date(r.get("Date"))
        px = number(r.get("ClosingPrice" if tw else "Close"))
        if not day or px is None or px <= 0:
            continue
        change = number(r.get("Change"))
        prev = px - change if change is not None else None
        if prev is not None and prev <= 0:
            prev = None
        symbol = code + (".TW" if tw else ".TWO")
        q = dict(price=px, prev=prev, chg_pct=(px / prev - 1) * 100 if prev else None, asof=day,
                 name=str(r.get("Name" if tw else "CompanyName", code)).strip(), source=source,
                 volume=number(r.get("TradeVolume" if tw else "TradingShares")), fetched=time.time())
        if day >= out.get(symbol, {}).get("asof", ""):
            out[symbol] = q
    return out


def cached():
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) and isinstance(d.get("quotes"), dict) else {"quotes": {}}
    except (OSError, ValueError):
        return {"quotes": {}}


async def refresh(force=False):
    saved = cached()
    if not force and time.time() - saved.get("attempt", 0) < 300:
        return saved["quotes"]

    async def fetch(source, url):
        try:
            rows = await http.get(url, timeout=20, retries=1)
            quotes = parse(rows, source)
            if not quotes:
                raise ValueError("No valid dated official quotes")
            HEALTH.ok(source + "_quotes", len(quotes), every=3600)
            return quotes
        except Exception as e:
            HEALTH.fail(source + "_quotes", e, every=3600)
            log.warning("%s official quotes failed: %s", source, e)
            return {}

    quotes = dict(saved["quotes"])
    for result in await asyncio.gather(*(fetch(s, u) for s, u in URLS.items())):
        for symbol, q in result.items():
            if q["asof"] >= quotes.get(symbol, {}).get("asof", ""):
                quotes[symbol] = q
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps({"attempt": time.time(), "quotes": quotes}, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError as e:
        log.warning("Official quote cache not saved: %s", e)
    return quotes


def index_frame(quotes):
    bars = (quotes.get("^TWII") or {}).get("bars") or {}
    return pd.DataFrame({"^TWII": pd.Series(bars, dtype=float)}).rename(index=pd.Timestamp).sort_index()


def overlay_published(data, quotes):
    """Current cash quotes + explicitly dated historical technicals; no fake current entry signal."""
    data = dict(data or {"available": True, "market": "tw", "label": "台股", "label_en": "Taiwan", "asof": "", "cols": [], "rows": []})
    cols = list(data["cols"])
    for key in ("sym", "code", "name", "board", "px", "r1d", "quote_asof", "history_asof", "source", "st", "stl", "why", "tier"):
        if key not in cols:
            cols.append(key)
    rows = {a[0]: dict(zip(data["cols"], a)) for a in data["rows"]}
    for sym, q in quotes.items():
        if sym == "^TWII" or not is_taiwan(sym):
            continue
        is_new = sym not in rows
        r = rows.get(sym, {"sym": sym, "code": sym.split(".")[0], "name": q.get("name", sym), "board": "上市" if sym.endswith(".TW") else "上櫃"})
        history_day = r.get("history_asof") or ""
        if history_day and q["asof"] < history_day:
            continue        # the official file lags the scan (TWSE OpenAPI is often a day late): keep the newer scan row
        r["history_asof"] = history_day
        # TW current-price display is always official, even if a historical vendor is ahead.
        historical_price = r.get("px")
        different_basis = historical_price and abs(q["price"] / historical_price - 1) > 0.005
        r.update(px=q["price"], r1d=q.get("chg_pct"), quote_asof=q["asof"], source=q["source"])
        if is_new:          # never scanned (ETFs, small caps): a price, not a stale signal
            r.update(st="quote_only", stl="僅報價", why="未納入技術掃描，只提供官方收盤價", tier=None)
        elif not history_day or q["asof"] != history_day or different_basis:
            r.update(st="stale", stl="技術資料待更新", why="報價與技術資料日期不同或技術日期不明，暫不顯示進場區間", tier=None)
            for key in ("pk", "pat", "patl", "str", "zlo", "zhi", "inv", "risk", "tgt", "tgtp", "inz", "when", "zb", "tg", "ex"):
                r[key] = None
        rows[sym] = r
    data.update(cols=cols, rows=[[r.get(k) for k in cols] for r in rows.values()], n=len(rows))
    data["quote_asof"] = max((r.get("quote_asof") or "" for r in rows.values()), default="")
    data["counts"] = {state: sum(r.get("st") == state for r in rows.values()) for state in {r.get("st", "") for r in rows.values()}}
    return data
