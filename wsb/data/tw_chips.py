"""台股籌碼深度與公司體質（2026-11-22，台股覆蓋清單補缺；使用者：「還缺的跟分工的，這 2 個部分做吧」）。

全部是官方免費資料，每天存一份，算變化：
  * 外資持股比率（類股）：證交所 OpenAPI fund/MI_QFIIS_cat
  * 借券放空餘額：證交所 exchangeReport/TWT93U（信用額度總量管制餘額表；借券賣出當日餘額＝前日＋當日賣出－還券＋調整）
  * 期貨三大法人台指期未平倉：期交所 OpenAPI MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate
  * 期貨大額交易人（台指期，全部月份 999912）：期交所 OpenAPI OpenInterestOfLargeTradersFutures（前五／前十大、全部或特定法人）
  * 董監持股質押：證交所 OpenAPI opendata/t187ap11_L（每月；資料約 10MB，一天抓一次）
  * 財測達成：證交所 OpenAPI opendata/t187ap15_L（只有公開財測的公司）
  * 季報快照：證交所 OpenAPI opendata/t187ap06_L_ci（累計數；每季存一份，之後相減得單季）
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_chips.json"
SNAP = DATA_DIR / "econ_tw_fin_snap.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_chips_seed.json"
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
U_QFII = "https://openapi.twse.com.tw/v1/fund/MI_QFIIS_cat"
U_SBL = "https://www.twse.com.tw/exchangeReport/TWT93U?response=json"
U_INST = "https://openapi.taifex.com.tw/v1/MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate"
U_LARGE = "https://openapi.taifex.com.tw/v1/OpenInterestOfLargeTradersFutures"
U_PLEDGE = "https://openapi.twse.com.tw/v1/opendata/t187ap11_L"
U_FCST = "https://openapi.twse.com.tw/v1/opendata/t187ap15_L"
U_FIN = "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci"
TTL = 4 * 3600
HEAVY_TTL = 24 * 3600
KEEP = 400
TPE = timezone(timedelta(hours=8))


def _n(s) -> Optional[float]:
    try:
        return float(re.sub(r"[,\s%]", "", str(s)))
    except (TypeError, ValueError):
        return None


def parse_qfii(rows: List[Dict]) -> List[Dict]:
    return [{"cat": str(r.get("IndustryCat") or "").strip(), "n": int(_n(r.get("Numbers")) or 0), "pct": _n(r.get("Percentage"))}
            for r in rows or [] if r.get("IndustryCat") and _n(r.get("Percentage")) is not None]


def parse_sbl(js: Dict, universe: Optional[set] = None) -> Dict:
    """Total borrowed-share short balance (shares) today vs the day before, and the stocks that added the most."""
    data = (js or {}).get("data") or []
    tot = prev = 0.0
    moves = []
    for r in data:
        if len(r) < 13:
            continue
        p, today = _n(r[8]) or 0.0, _n(r[12]) or 0.0
        tot += today
        prev += p
        if universe is None or r[0] in universe:
            moves.append({"code": r[0], "name": r[1].strip(), "bal": today, "chg": today - p})
    moves.sort(key=lambda x: -x["chg"])
    return {"date": (js or {}).get("date"), "total": tot, "prev": prev, "add": moves[:10], "cut": sorted(moves, key=lambda x: x["chg"])[:10]}


def parse_inst(rows: List[Dict]) -> Dict:
    out = {}
    for r in rows or []:
        if r.get("ContractCode") == "臺股期貨":
            out[str(r.get("Item"))] = {"net_oi": _n(r.get("OpenInterest(Net)")), "net_trade": _n(r.get("TradingVolume(Net)")), "date": r.get("Date")}
    return out


def parse_large(text: str) -> Dict:
    """台指期 all months (999912): top-5 / top-10 traders' long minus short, for all traders (0) and specific institutions (1)."""
    rows = list(csv.reader(io.StringIO((text or "").lstrip("﻿"))))
    out = {}
    for r in rows[1:]:
        if len(r) >= 10 and r[1].strip() == "TX" and r[3].strip() == "999912":
            k = "all" if r[4].strip() == "0" else "inst"
            b5, s5, b10, s10, oi = (_n(x) or 0.0 for x in r[5:10])
            out[k] = {"date": r[0], "top5_net": b5 - s5, "top10_net": b10 - s10, "oi": oi}
    return out


def parse_pledge(rows: List[Dict], universe: Optional[set] = None) -> List[Dict]:
    """Per company: insiders' (directors and their related parties) pledged shares as % of their holdings."""
    agg: Dict[str, Dict] = {}
    for r in rows or []:
        code = str(r.get("公司代號") or "").strip()
        if not code or (universe is not None and code not in universe):
            continue
        a = agg.setdefault(code, {"code": code, "name": str(r.get("公司名稱") or "").strip(), "held": 0.0, "pledged": 0.0, "ym": r.get("資料年月")})
        a["held"] += _n(r.get("目前持股")) or 0.0
        a["pledged"] += _n(r.get("設質股數")) or 0.0
    out = [{**a, "pct": a["pledged"] / a["held"] * 100} for a in agg.values() if a["held"] > 0]
    return sorted(out, key=lambda x: -x["pct"])


def parse_forecast(rows: List[Dict]) -> List[Dict]:
    out = []
    for r in rows or []:
        keys = list(r.keys())
        act = next((r[k] for k in keys if "查核" in k or "核閱數" in k), None)
        fc = next((r[k] for k in keys if "預測數" in k and "達成" not in k), None)
        rate = next((r[k] for k in keys if "達成" in k), None)
        out.append({"code": str(r.get("公司代號") or "").strip(), "name": str(r.get("公司名稱") or "").strip(), "year": r.get("年度"),
                    "q": r.get("季別"), "actual": _n(act), "forecast": _n(fc), "rate": _n(rate)})
    return [x for x in out if x["code"]]


def _get(url: str, kind: str = "json"):
    import requests
    r = requests.get(url, headers=UA, timeout=40)
    r.raise_for_status()
    if kind == "text":
        r.encoding = "utf-8"
        return r.text
    return r.json()


def _load(f) -> Dict:
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except (OSError, ValueError):
        return {}


def _save(f, d: Dict) -> None:
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, f)


def _universe() -> set:
    try:
        from . import tw_desk as D
        return set(D.universe(D.load()).get("codes") or [])
    except Exception:  # noqa: BLE001
        return set()


def snapshot_fin(rows: List[Dict], snaps: Dict) -> Dict:
    """Store the cumulative income statement once per (year, quarter); single quarters come from differences later."""
    for r in rows or []:
        y, q, code = str(r.get("年度") or ""), str(r.get("季別") or ""), str(r.get("公司代號") or "").strip()
        if not (y and q and code):
            continue
        k = f"{y}Q{q}"
        snaps.setdefault(k, {})[code] = {"rev": _n(r.get("營業收入")), "gross": _n(r.get("營業毛利（毛損）淨額")),
                                         "op": _n(r.get("營業利益（損失）")), "ni": _n(r.get("淨利（淨損）歸屬於母公司業主")),
                                         "eps": _n(r.get("基本每股盈餘（元）")), "name": str(r.get("公司名稱") or "").strip()}
    return snaps


def single_quarter(snaps: Dict, code: str, year: str, q: int) -> Optional[Dict]:
    """Q1 = cumulative; Qn = cumulative(n) − cumulative(n−1).  None until both snapshots exist."""
    cur = (snaps.get(f"{year}Q{q}") or {}).get(code)
    if not cur:
        return None
    if q == 1:
        return dict(cur)
    prev = (snaps.get(f"{year}Q{q - 1}") or {}).get(code)
    if not prev:
        return None
    return {k: (cur[k] - prev[k]) if isinstance(cur.get(k), float) and isinstance(prev.get(k), float) else cur.get(k) for k in cur}


def refresh(force: bool = False) -> Dict:
    d = _load(FILE)
    now = time.time()
    if not force and now - float(d.get("ts") or 0) < TTL:
        return d
    d["ts"] = now
    today = datetime.now(TPE).strftime("%Y-%m-%d")
    hist = d.setdefault("hist", {})
    day = hist.setdefault(today, {})
    uni = _universe()
    for name, fn in (("qfii", lambda: parse_qfii(_get(U_QFII))),
                     ("sbl", lambda: parse_sbl(_get(U_SBL), uni or None)),
                     ("inst", lambda: parse_inst(_get(U_INST))),
                     ("large", lambda: parse_large(_get(U_LARGE, "text")))):
        try:
            v = fn()
            if v:
                d[name] = v
                day[name] = v if name != "sbl" else {"date": v["date"], "total": v["total"]}
        except Exception as e:  # noqa: BLE001
            log.info("tw chips %s unavailable: %s", name, e)
    seed = _load(SEED)                                   # PC relay (11-22: the TAIFEX large-trader CSV does not reach the cloud build)
    for name in ("large",):
        sv = seed.get(name) or {}
        mine = str(((d.get(name) or {}).get("inst") or {}).get("date") or "")
        if str((sv.get("inst") or {}).get("date") or "") > mine:
            d[name] = sv
            day[name] = sv
    if force or now - float(d.get("heavy_ts") or 0) >= HEAVY_TTL:
        d["heavy_ts"] = now
        for name, fn in (("pledge", lambda: parse_pledge(_get(U_PLEDGE), uni or None)), ("forecast", lambda: parse_forecast(_get(U_FCST)))):
            try:
                v = fn()
                if v:
                    d[name] = v
            except Exception as e:  # noqa: BLE001
                log.info("tw chips %s unavailable: %s", name, e)
        try:
            _save(SNAP, snapshot_fin(_get(U_FIN), _load(SNAP)))
        except Exception as e:  # noqa: BLE001
            log.info("tw fin snapshot unavailable: %s", e)
    for k in sorted(hist)[:-KEEP]:
        hist.pop(k)
    d["fetched"] = datetime.now(TPE).strftime("%Y-%m-%d %H:%M")
    try:
        _save(FILE, d)
    except OSError:
        pass
    return d


def series(d: Dict, key, sub=None) -> List[tuple]:
    """[(day, value)] from the daily history, e.g. series(d, "inst", ("外資及陸資", "net_oi"))."""
    out = []
    for day in sorted((d.get("hist") or {})):
        v = (d["hist"][day] or {}).get(key)
        for s in sub or ():
            v = (v or {}).get(s) if isinstance(v, dict) else None
        if isinstance(v, (int, float)):
            out.append((day, float(v)))
    return out


def write_seed(path=SEED) -> Dict:
    """PC → cloud relay for the parts the cloud cannot fetch (public exchange data)."""
    out = {"fetched": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"), "large": parse_large(_get(U_LARGE, "text"))}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
