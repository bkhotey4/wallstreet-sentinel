"""公司的錢從哪裡來（2026-11-16，使用者選的第 4、5 項）。全部來自 SEC 財報（distress_data 的 companyfacts 快取）與 FRED：

  4 債務到期牆：10-K 附註裡「未來第 1～5 年各要還多少本金、5 年後還有多少」（LongTermDebtMaturitiesRepaymentsOfPrincipal…），
    把追蹤的公司加總成每年的到期金額；每家公司「目前平均付的利率」＝過去 12 個月利息費用 ÷ 負債，和「現在去市場借要付的利率」比，
    算出未來兩年到期的債如果照現在的利率借新還舊，一年要多付多少利息、佔營業利益多少。
    現在的借錢利率：用利息保障倍數（營業利益 ÷ 利息）粗分三級（≥ 8 倍＝投資級、3～8 倍＝BBB、< 3 倍或虧損＝高收益），
    各用 ICE 美銀公司債殖利率（FRED；ICE 授權資料，網站只顯示算出來的結果、不顯示原始殖利率）。分級是經驗法則，不是信評。
  5 股票供給：股數和一年前比（SEC 封面上的流通股數）、過去 12 個月買回自家股票 vs 發行新股的金額、最近 180 天的增資或發債文件
    （S-3、S-3ASR、424B5、424B3、S-1）。股數一直增加＝舊股東被稀釋；一直減少＝公司在買回。
金融業（銀行、保險）負債結構不同，不列入到期牆。快取：殖利率存 data_cache/econ_corp_funding.json。"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import time
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_corp_funding.json"
TTL = 12 * 3600
YIELDS = {"ig": "BAMLC0A0CMEY", "bbb": "BAMLC0A4CBBBEY", "hy": "BAMLH0A0HYM2EY", "t10": "DGS10"}
TIER_ZH = {"ig": "投資級", "bbb": "BBB", "hy": "高收益"}
FIN_KINDS = {"fin", "bank", "credit"}         # banks, insurers, BDCs: debt is their business, not a refinancing wall
BUCKETS = (("mat1", "1 年內"), ("mat2", "第 2 年"), ("mat3", "第 3 年"), ("mat4", "第 4 年"), ("mat5", "第 5 年"), ("mat_after", "5 年以後"))


def _f(x) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _debt(b: Dict) -> Optional[float]:
    from .distress import _debt as d
    return d(b)


def tier(b: Dict) -> str:
    ebit, intr = _f(b.get("ebit_ttm")), _f(b.get("interest_ttm"))
    if ebit is None or ebit <= 0:
        return "hy"
    if not intr or intr <= 0:
        return "ig"
    cov = ebit / intr
    return "ig" if cov >= 8 else "bbb" if cov >= 3 else "hy"


def refi(b: Dict, ylds: Dict[str, float]) -> Optional[Dict]:
    """One company's two-year refinancing view (all in dollars; rates as fractions)."""
    due1, due2 = _f(b.get("mat1")), _f(b.get("mat2"))
    if due1 is None and due2 is None:
        return None
    due = (due1 or 0.0) + (due2 or 0.0)
    debt, intr, ebit = _debt(b), _f(b.get("interest_ttm")), _f(b.get("ebit_ttm"))
    t = tier(b)
    mkt = ylds.get(t)
    coupon = intr / debt if intr and debt and debt > 0 else None
    out = {"due1": due1 or 0.0, "due2": due2 or 0.0, "due": due, "debt": debt, "tier": t, "coupon": coupon,
           "cash": _f(b.get("cash")), "ebit": ebit, "mat_end": b.get("mat_end")}
    if coupon is not None and mkt is not None:
        out["gap"] = mkt - coupon
        out["extra"] = due * (mkt - coupon)
        if ebit and ebit > 0:
            out["extra_ebit"] = out["extra"] / ebit
    ocf, capex = _f(b.get("ocf_ttm")), _f(b.get("capex_ttm"))
    fcf = (ocf - (capex or 0.0)) if ocf is not None else None
    out["fcf"] = fcf
    # can the next year's principal be paid from cash plus a year of free cash flow?
    if due1:
        out["self_pay"] = ((out["cash"] or 0.0) + max(fcf or 0.0, 0.0)) / due1
    return out


def wall(cache: Dict[str, Dict], names: Dict[str, Dict]) -> Dict:
    """Sum of each maturity bucket across the public non-financial names; top names by two-year maturities."""
    tot = {k: 0.0 for k, _ in BUCKETS}
    n, rows = 0, []
    for s, meta in names.items():
        b = (cache.get(s) or {}).get("bs") or {}
        if meta.get("kind") in FIN_KINDS or b.get("deposits"):
            continue
        if b.get("mat1") is None and b.get("mat2") is None:
            continue
        n += 1
        for k, _ in BUCKETS:
            tot[k] += _f(b.get(k)) or 0.0
        rows.append(s)
    return {"tot": tot, "n": n, "syms": rows}


def refi_table(cache: Dict[str, Dict], names: Dict[str, Dict], ylds: Dict[str, float]) -> List[Dict]:
    out = []
    for s, meta in names.items():
        b = (cache.get(s) or {}).get("bs") or {}
        if meta.get("kind") in FIN_KINDS or b.get("deposits"):
            continue
        r = refi(b, ylds)
        if r and r["due"] > 0:
            out.append(dict(r, sym=s, zh=meta.get("zh") or s))
    return out


def supply(cache: Dict[str, Dict], names: Dict[str, Dict], mcap: Dict[str, float]) -> List[Dict]:
    """Per company: share-count change in a year, buybacks vs new shares (TTM, dollars), recent offering documents."""
    out = []
    for s, meta in names.items():
        rec = cache.get(s) or {}
        b = rec.get("bs") or {}
        sh, sh0 = _f(b.get("wsh")), _f(b.get("wsh_yago"))          # split-safe (restated in the same filing)
        bb, iss = _f(b.get("buyback_ttm")), _f(b.get("issue_ttm"))
        offers = rec.get("offer") or []
        if sh is None and bb is None and iss is None and not offers:
            continue
        r = {"sym": s, "zh": meta.get("zh") or s, "chg": (sh / sh0 - 1) if sh and sh0 else None, "buyback": bb, "issue": iss,
             "net": (bb or 0.0) - (iss or 0.0) if (bb is not None or iss is not None) else None, "offers": offers,
             "shares_end": b.get("wsh_end"), "mcap": mcap.get(s)}
        if r["net"] is not None and mcap.get(s):
            r["net_yield"] = r["net"] / mcap[s]
        out.append(r)
    return out


async def refresh(force: bool = False) -> Dict:
    from ..data.fred import _one
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts_try", 0)) < TTL:
        return d
    d["ts_try"] = now
    got, bad = {}, []
    res = await asyncio.gather(*(_one(sid, "2025-01-01") for sid in YIELDS.values()), return_exceptions=True)
    for (k, sid), r in zip(YIELDS.items(), res):
        if isinstance(r, Exception) or not len(r):
            bad.append(sid)
            continue
        got[k] = [r.index[-1].date().isoformat(), float(r.iloc[-1]) / 100]
    if got:
        d["yields"] = dict(d.get("yields") or {}, **got)
        d["ts"] = now
    if bad:
        log.warning("corp funding yields missing: %s", ", ".join(bad))
        HEALTH.fail("corp_funding", ", ".join(bad), every=TTL)
    else:
        HEALTH.ok("corp_funding", len(got), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def yields(d: Optional[Dict] = None) -> Dict[str, float]:
    d = load() if d is None else d
    return {k: v[1] for k, v in (d.get("yields") or {}).items()}
