"""Taiwan ETFs for the 台灣 ETF page.  All free, keyless, official sources:

* 證交所 ETF 即時淨值 (mis.twse.com.tw/stock/data/all_etf.txt): every listed ETF's market price, the issuer's estimated
  NAV, premium / discount, units outstanding and today's change in units (creations − redemptions).  Snapshotted every
  build into a daily history, so flows and premiums can be compared with each ETF's own past.
* 證交所 除權除息預告表 (OpenAPI TWT48U_ALL): upcoming ex-dividend dates and cash dividends.
* 集保結算所 集保戶股權分散表 (opendata, weekly): number of holders per ETF, snapshotted weekly.
* Yahoo chart API: 5 years of daily closes and cash dividends for the tracked ETFs (total return, yield, drawdown, 填息).
Cached in data_cache/econ_tw_etf.json (kept between site builds)."""
from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import os
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from ..config import DATA_DIR
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_etf.json"          # econ_* is kept between CI builds
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
NAV_URL = "https://mis.twse.com.tw/stock/data/all_etf.txt"
EXDIV_URL = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
TDCC_URL = "https://opendata.tdcc.com.tw/getOD.ashx?id=1-5"
PX_TTL = 12 * 3600
KEEP_DAYS = 800

# the ETFs most Taiwanese investors hold, by kind (the top ones by size are added automatically on top of these)
CORE = {
    "市值型": ["0050", "006208"],
    "高股息": ["0056", "00878", "00919", "00929", "00713", "00940"],
    "主動式": ["00981A"],
    "債券": ["00679B", "00687B", "00937B", "00720B", "00751B"],
    "槓桿反向": ["00631L", "00632R"],
}
N_TOP = 10


def kind_of(code: str, name: str = "") -> str:
    for k, xs in CORE.items():
        if code in xs:
            return k
    if code.endswith("B"):
        return "債券"
    if code.endswith(("L", "R")):
        return "槓桿反向"
    if code.endswith("A"):
        return "主動式"
    if code.endswith("U") or "期貨" in name:
        return "商品期貨"
    if "息" in name or "收益" in name:
        return "高股息"
    return "其他股票型"


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)


def _num(x) -> Optional[float]:
    try:
        return float(str(x).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ parsers (pure, tested)
def parse_nav(j: Dict) -> Dict[str, Dict]:
    """all_etf.txt → {code: {name, units, dunits, px, nav, prem, prev_nav, date}}.  Numbers come as numbers or as
    strings with commas depending on the issuer; a missing or zero NAV leaves the premium unknown (None), never 0."""
    out = {}
    for g in (j or {}).get("a1") or []:
        for r in g.get("msgArray") or []:
            code = str(r.get("a") or "").strip()
            if not code:
                continue
            px, nav = _num(r.get("e")), _num(r.get("f"))
            prem = _num(r.get("g"))
            if not nav or not px:
                prem = None
            d = str(r.get("i") or "")
            out[code] = {"name": str(r.get("b") or "").split("(")[0].split("（")[0].strip(), "units": _num(r.get("c")),
                         "dunits": _num(r.get("d")), "px": px or None, "nav": nav or None, "prem": prem,
                         "prev_nav": _num(r.get("h")), "date": f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else None,
                         "time": str(r.get("j") or "")[:5] or None}
    return out


def _roc(s: str) -> Optional[str]:
    s = str(s or "").strip()
    if len(s) != 7 or not s.isdigit():
        return None
    return f"{int(s[:3]) + 1911}-{s[3:5]}-{s[5:7]}"


def parse_exdiv(rows: List[Dict]) -> List[Dict]:
    """TWT48U_ALL → ETF ex-dividend notices [{date, code, name, cash}] (cash None until the issuer announces it)."""
    out = []
    for r in rows or []:
        code = str(r.get("Code") or "").strip()
        d = _roc(r.get("Date"))
        if not d or not code.startswith("00") or "息" not in str(r.get("Exdividend") or ""):
            continue
        out.append({"date": d, "code": code, "name": str(r.get("Name") or "").strip(), "cash": _num(r.get("CashDividend")) or None})
    return sorted(out, key=lambda x: x["date"])


def parse_tdcc(text: str, codes) -> Dict:
    """集保股權分散表 CSV → (date, {code: [holders, holders under 1,000 units]}).  Level 17 is the total; levels 1–2 are
    holdings under 5,000 units… we keep level 1 (1–999 units, odd lots) as the 'small savers' count."""
    want, out, dt = set(codes), {}, None
    for row in csv.reader(io.StringIO(text.lstrip("﻿"))):
        if len(row) < 4 or not row[0].isdigit():
            continue
        code = row[1].strip()
        if code not in want:
            continue
        dt = dt or f"{row[0][:4]}-{row[0][4:6]}-{row[0][6:8]}"
        lv, n = row[2].strip(), _num(row[3])
        if lv == "17":
            out.setdefault(code, [None, None])[0] = n
        elif lv == "1":
            out.setdefault(code, [None, None])[1] = n
    return {"date": dt, "rows": out}


def parse_chart(js: Dict) -> Optional[Dict]:
    """Yahoo chart → {"c": [[date, close]], "dv": [[ex-date, cash]]}."""
    try:
        r = js["chart"]["result"][0]
    except (KeyError, IndexError, TypeError):
        return None
    ts = r.get("timestamp") or []
    cl = ((r.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    off = int((r.get("meta") or {}).get("gmtoffset") or 28800)
    day = lambda t: datetime.utcfromtimestamp(int(t) + off).strftime("%Y-%m-%d")      # noqa: E731  Taipei calendar day
    c = [[day(t), round(v, 4)] for t, v in zip(ts, cl) if v]
    dv = sorted([day(x["date"]), float(x["amount"])] for x in ((r.get("events") or {}).get("dividends") or {}).values()
                if x.get("amount"))
    return {"c": fix_splits(c, {x for x, _ in dv}), "dv": dv} if len(c) > 20 else None


def fix_splits(c: List, div_days=()) -> List:
    """Yahoo misses some Taiwan ETF splits (0052 split 1:7 in 2025-11 shows as a −86 % day).  A one-day move of −40 % or
    worse (or +100 % or more, a reverse split) that is within 5 % of a whole-number ratio, on a day with no dividend, is
    treated as a split and the earlier closes are rescaled."""
    out = [list(x) for x in c]
    for i in range(1, len(out)):
        a, b = out[i - 1][1], out[i][1]
        if not a or not b or out[i][0] in div_days:
            continue
        k = a / b if b < a else b / a
        if (b / a <= 0.6 or b / a >= 2.0) and round(k) >= 2 and abs(k / round(k) - 1) <= 0.05:
            f = round(k) if b < a else 1 / round(k)
            for j in range(i):
                out[j][1] = round(out[j][1] / f, 4)
    return out


# ------------------------------------------------------------------ refresh
async def _chart(code: str, d: Dict) -> None:
    sfx = (d.get("sfx") or {}).get(code)
    for s in ([sfx] if sfx else [".TW", ".TWO"]):
        try:
            js = await http.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{s}?range=5y&interval=1d&events=div",
                                headers={"User-Agent": "Mozilla/5.0"}, timeout=25, retries=1)
        except Exception:  # noqa: BLE001
            continue
        p = parse_chart(js)
        if p:
            d.setdefault("sfx", {})[code] = s
            d.setdefault("px", {})[code] = {**p, "ts": time.time()}
            return


def tracked(nav: Dict[str, Dict]) -> List[str]:
    """Core list + the largest ETFs by assets (units × NAV) that are not already in it."""
    core = [c for xs in CORE.values() for c in xs]
    size = sorted(((v["units"] or 0) * (v["nav"] or 0), k) for k, v in nav.items() if v.get("units") and v.get("nav"))
    top = [k for _, k in reversed(size) if k not in core][:N_TOP]
    return core + top


async def refresh(force: bool = False) -> Dict:
    d = load()
    try:
        j = await http.get(NAV_URL, headers=UA, timeout=25)
        nav = parse_nav(j)
        if nav:
            d["nav"] = nav
            dt = max((v["date"] for v in nav.values() if v.get("date")), default=None)
            if dt:                                  # daily snapshot: units, NAV, premium (the flow / premium history)
                hist = d.setdefault("daily", {})
                hist[dt] = {k: [v["units"], v["nav"], v["prem"]] for k, v in nav.items() if v.get("units")}
                cut = (date.fromisoformat(dt) - timedelta(days=KEEP_DAYS)).isoformat()
                d["daily"] = {k: v for k, v in sorted(hist.items()) if k >= cut}
            d["nav_ts"] = time.time()
    except Exception as e:  # noqa: BLE001
        log.warning("TWSE ETF NAV unavailable: %s", e)
    try:
        d["exdiv"] = parse_exdiv(await http.get(EXDIV_URL, headers=UA, timeout=25))
    except Exception as e:  # noqa: BLE001
        log.warning("TWSE ex-dividend notices unavailable: %s", e)
    codes = tracked(d.get("nav") or {})
    hold = d.setdefault("holders", {})
    last = max(hold) if hold else None
    if force or not last or (date.today() - date.fromisoformat(last)).days >= 6:
        try:
            t = await http.get(TDCC_URL, kind="bytes", headers=UA, timeout=60)
            p = parse_tdcc(t.decode("utf-8", "replace"), set(codes) | set((d.get("nav") or {}).keys()))
            if p["date"] and p["rows"]:
                hold[p["date"]] = p["rows"]
                d["holders"] = dict(sorted(hold.items())[-120:])
        except Exception as e:  # noqa: BLE001
            log.warning("TDCC holders unavailable: %s", e)
    old = [c for c in codes if force or time.time() - float(((d.get("px") or {}).get(c) or {}).get("ts", 0)) > PX_TTL]
    sem = asyncio.Semaphore(4)

    async def one(c):
        async with sem:
            await _chart(c, d)
    await asyncio.gather(*(one(c) for c in old))
    d["px"] = {k: v for k, v in (d.get("px") or {}).items() if k in codes}
    d["ts"] = time.time()
    _save(d)
    return d
