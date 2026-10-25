"""AI 資本支出縮減時，誰的營收最受傷：用 SEC 財報（XBRL companyfacts）的季資料量「依賴度」。

做法：
  * 雲端巨頭（微軟、Alphabet、亞馬遜、Meta、甲骨文）每季資本支出合計 → 近 12 個月合計的年增率。
  * 每家供應鏈公司每季營收 → 近 12 個月合計的年增率。
  * 2020 年以來各季：供應商營收年增率對巨頭資本支出年增率做迴歸，斜率＝「巨頭資本支出成長每多 1 個百分點，這家營收成長平均多幾個百分點」，
    並附相關係數。推算「如果巨頭資本支出不再成長（年增 0%）」時的營收年增率＝現在 − 斜率 × 現在的資本支出年增率。
限制：季資料只有十幾個點、相關不等於因果、各公司會計年度不同（對齊到最近的日曆季）。快取 data_cache/econ_capex_link.json（7 天）。"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import date
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_capex_link.json"
TTL = 7 * 86400
PV = 2                                  # parser version: a cache made by an older parser is re-read at once
BUYERS = ("MSFT", "GOOGL", "AMZN", "META", "ORCL")
SUPPLIERS = (("NVDA", "輝達"), ("AVGO", "博通"), ("AMD", "超微"), ("MRVL", "邁威爾"), ("MU", "美光"), ("AMAT", "應用材料"), ("LRCX", "科林研發"),
             ("KLAC", "科磊"), ("ANET", "Arista 網通"), ("VRT", "Vertiv 散熱電源"), ("DELL", "戴爾"), ("SMCI", "美超微"), ("ETN", "伊頓電氣"),
             ("GEV", "GE Vernova 電網"), ("VST", "Vistra 電力"), ("CEG", "Constellation 電力"))
REV = ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax")
CAPEX = ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets")


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _cal_q(end: str) -> str:
    """Nearest calendar quarter end, e.g. NVDA's 2026-07-26 (May–Jul) → 2026Q2 (fiscal years differ by company)."""
    d = pd.Timestamp(end)
    cands = [pd.Timestamp(year=y, month=m, day=1) + pd.offsets.MonthEnd(0) for y in (d.year - 1, d.year, d.year + 1) for m in (3, 6, 9, 12)]
    q = min(cands, key=lambda c: abs((c - d).days))
    return f"{q.year}Q{(q.month - 1) // 3 + 1}"


def quarterly(cf: Dict, tags) -> Dict[str, float]:
    """{calendar quarter: value} merged over the candidate tags (companies switch tags over the years; the first tag listed wins a quarter)."""
    out: Dict[str, float] = {}
    for tag in tags:
        for q, v in _quarterly_tag(cf, tag).items():
            out.setdefault(q, v)
    return dict(sorted(out.items())) if len(out) >= 8 else {}


def _quarterly_tag(cf: Dict, tag: str) -> Dict[str, float]:
    """{calendar quarter: value} from year-to-date duration facts (Q = YTD − previous YTD in the same fiscal year; Q4 = FY − 9M)."""
    if True:
        u = ((((cf.get("facts") or {}).get("us-gaap") or {}).get(tag) or {}).get("units") or {}).get("USD") or []
        if not u:
            return {}
        best: Dict[tuple, Dict] = {}
        for f in u:
            if f.get("val") is None or not f.get("start") or not f.get("end"):
                continue
            k = (f["start"], f["end"])
            if f.get("filed", "") >= (best.get(k) or {}).get("filed", ""):
                best[k] = f
        by_start: Dict[str, List] = {}
        for (s, e), f in best.items():
            span = (date.fromisoformat(e) - date.fromisoformat(s)).days
            if 80 <= span <= 380:
                by_start.setdefault(s, []).append((e, float(f["val"]), span))
        direct: Dict[str, float] = {}
        derived: Dict[str, float] = {}
        for s, rows in by_start.items():
            rows.sort()
            prev_v, prev_span = 0.0, 0
            for e, v, span in rows:
                q = _cal_q(e)
                if span <= 100:
                    if v > 0:
                        direct.setdefault(q, v)
                elif 80 <= span - prev_span <= 100 and v - prev_v > 0:   # YTD minus the previous YTD; an annual-only fact is never a Q4
                    derived.setdefault(q, v - prev_v)
                prev_v, prev_span = v, span
        return {**derived, **direct}
    return {}


async def refresh(force: bool = False) -> Dict:
    from ..data import http
    from ..data.earnings_data import SEC_HDR
    from ..data.edgar_holdings import ticker_map
    d = load()
    now = time.time()
    d["ts_check"] = now
    if d.get("pv") != PV:
        d = {"ts_check": now}                                        # older parser turned annual / trailing-12-month facts into quarters
    if not force and now - float(d.get("ts", 0)) < TTL and d.get("rev"):
        _save(d)
        return d
    try:
        tmap = await ticker_map()
    except Exception as e:  # noqa: BLE001
        log.warning("capex link: no SEC ticker map: %s", e)
        _save(d)
        return d
    rev, cap = dict(d.get("rev") or {}), dict(d.get("capex") or {})
    for sym in list(BUYERS) + [s for s, _z in SUPPLIERS]:
        cik = (tmap.get(sym) or {}).get("cik")
        if not cik:
            continue
        try:
            cf = await http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=40, retries=1)
            if sym in BUYERS:
                q = quarterly(cf or {}, CAPEX)
                if q:
                    cap[sym] = q
            else:
                q = quarterly(cf or {}, REV)
                if q:
                    rev[sym] = q
            await asyncio.sleep(0.15)
        except Exception as e:  # noqa: BLE001
            log.info("capex link %s: %s", sym, e)
    if rev and cap:
        d.update(rev=rev, capex=cap, ts=now, pv=PV)
    _save(d)
    return d


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)


def _ttm_yoy(q: Dict[str, float]) -> pd.Series:
    s = pd.Series(q, dtype=float)
    s.index = pd.PeriodIndex(s.index, freq="Q")
    s = s.sort_index()
    s = s[~s.index.duplicated()].asfreq("Q")
    t = s.rolling(4).sum()
    return (t / t.shift(4) - 1) * 100


def build(d: Optional[Dict] = None) -> Optional[Dict]:
    d = d if d is not None else load()
    cap, rev = d.get("capex") or {}, d.get("rev") or {}
    if len(cap) < 3 or not rev:
        return None
    total: Dict[str, float] = {}
    common = None
    for q in cap.values():
        ks = set(q)
        common = ks if common is None else common & ks
    for k in sorted(common or []):
        total[k] = sum(cap[s][k] for s in cap)
    cy = _ttm_yoy(total).dropna()
    cy = cy[cy.index >= pd.Period("2020Q1", "Q")]
    if len(cy) < 8:
        return None
    rows = []
    zh = dict(SUPPLIERS)
    for sym, q in rev.items():
        ry = _ttm_yoy(q).dropna()
        j = pd.concat({"r": ry, "c": cy}, axis=1).dropna()
        if len(j) < 8:
            continue
        x, y = j["c"].values, j["r"].values
        slope = float(np.polyfit(x, y, 1)[0])
        corr = float(np.corrcoef(x, y)[0, 1])
        now_r, now_c = float(j["r"].iloc[-1]), float(j["c"].iloc[-1])
        rows.append({"sym": sym, "zh": zh.get(sym, sym), "slope": slope, "corr": corr, "n": int(len(j)), "rev_yoy": now_r,
                     "if_flat": now_r - slope * now_c, "q": str(j.index[-1])})
    if not rows:
        return None
    rows.sort(key=lambda r: -(r["slope"] if r["corr"] > 0.3 else -9))
    return {"capex_yoy": float(cy.iloc[-1]), "capex_q": str(cy.index[-1]), "capex_ttm": float(pd.Series(total).iloc[-4:].sum()) if len(total) >= 4 else None,
            "rows": rows, "buyers": sorted(cap)}
