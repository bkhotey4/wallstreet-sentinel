"""產業體檢 — company fundamentals that show real-economy strain before it reaches prices, from SEC XBRL (companyfacts).

Per company (US-GAAP filers), the latest trailing-twelve-month (TTM) flows and quarter-end balances, each next to the
same figure one year earlier, so every metric is compared with the company's OWN history:
  funding gap   capex − operating cash flow (positive = the gap is paid with new debt, equity or cash on hand)
  not in use    construction in progress ÷ gross property & equipment (bought but not yet in service)
  inventory     inventory growth minus revenue growth (goods piling up faster than they sell)
  collections   days sales outstanding = receivables ÷ TTM revenue × 365 (customers paying slower)
  interest      interest expense ÷ operating income (how much of the profit the lenders take)
  debt          total debt growth over the year
Missing tags are reported as "not disclosed", never as zero.  Companyfacts is fetched at most weekly per company,
oldest first, inside a time budget; the parsed result is cached in data_cache/earn_fund.json (earn_* is already in
the site workflow's cache — no cache-key change)."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import timedelta
from typing import Dict, List, Optional

from ..config import DATA_DIR
from . import http
from .distress_data import SEC_HDR, _d, _facts, instants, ttm, ttm_ex

log = logging.getLogger(__name__)
CACHE = DATA_DIR / "earn_fund.json"
PV = 1
FLOW = {"rev": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"),
        "ocf": ("NetCashProvidedByUsedInOperatingActivities",),
        "capex": ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"),
        "ebit": ("OperatingIncomeLoss",),
        "interest": ("InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt")}
INST = {"inv": ("InventoryNet", "InventoryGross"),
        "ar": ("AccountsReceivableNetCurrent", "ReceivablesNetCurrent"),
        "cip": ("ConstructionInProgressGross",),
        "ppe_gross": ("PropertyPlantAndEquipmentGross",),
        "debt": ("LongTermDebt", "LongTermDebtAndCapitalLeaseObligations", "DebtLongtermAndShorttermCombinedAmount"),
        "debt_cur": ("DebtCurrent", "ShortTermBorrowings", "CommercialPaper"),
        "fin_lease": ("FinanceLeaseLiability",),
        "cash": ("CashAndCashEquivalentsAtCarryingValue",)}


def _ttm_pair(cf: Dict, tags) -> Dict:
    """Latest TTM and the TTM one year before it (from facts that ended by then)."""
    best = None
    for t in tags:
        fs = _facts(cf, t)
        r = ttm_ex(fs)
        if r and (best is None or r[0] > best[0][0]):
            best = (r, fs)
    if not best:
        return {}
    (end, val, ann), fs = best
    cut = (_d(end) - timedelta(days=330)).isoformat()
    prev = ttm([f for f in fs if f.get("end", "9999") <= cut])
    ok_prev = prev and 330 <= (_d(end) - _d(prev[0])).days <= 400
    return {"end": end, "v": val, "ann": ann, "prev": prev[1] if ok_prev else None, "prev_end": prev[0] if ok_prev else None}


def _inst_pair(cf: Dict, tags, at: str) -> Dict:
    """Value at the balance-sheet date `at` (±40 days) and one year earlier (±45 days)."""
    for t in tags:
        s = instants(_facts(cf, t))
        if not s:
            continue
        near = [e for e in s if abs((_d(e) - _d(at)).days) <= 40]
        if not near:
            continue
        e = max(near)
        prior = [x for x in s if abs((_d(e) - _d(x)).days - 365) <= 45]
        return {"end": e, "v": s[e], "prev": s[max(prior)] if prior else None}
    return {}


def parse(cf: Dict) -> Optional[Dict]:
    out = {k: _ttm_pair(cf, tags) for k, tags in FLOW.items()}
    at = max([v["end"] for v in out.values() if v] or [""])
    if not at:
        return None
    for k, v in out.items():                      # a flow that stopped being tagged years ago must not meet today's numbers
        if v and abs((_d(at) - _d(v["end"])).days) > 40:
            out[k] = {"stale": v["end"]}
    for k, tags in INST.items():
        out[k] = _inst_pair(cf, tags, at)
    out["end"], out["pv"] = at, PV
    return out


def _g(a, b) -> Optional[float]:
    return (a / b - 1) * 100 if a is not None and b not in (None, 0) and b > 0 else None


def metrics(p: Dict) -> Dict:
    """The six strain metrics (None = not disclosed / not comparable)."""
    v = lambda k: (p.get(k) or {}).get("v")  # noqa: E731   (a stale flow has no "v" → None = not disclosed)
    pv = lambda k: (p.get(k) or {}).get("prev")  # noqa: E731
    capex, ocf = v("capex"), v("ocf")
    m: Dict = {"end": p.get("end")}
    m["gap"] = (capex - ocf) if capex is not None and ocf is not None else None
    m["capex_ocf"] = capex / ocf if capex is not None and ocf and ocf > 0 else None
    m["capex_ocf_prev"] = pv("capex") / pv("ocf") if pv("capex") is not None and pv("ocf") and pv("ocf") > 0 else None
    m["ocf_negative"] = ocf is not None and ocf < 0
    cip, gross = v("cip"), v("ppe_gross")
    m["cip_share"] = cip / gross * 100 if cip is not None and gross else None
    m["cip_share_prev"] = pv("cip") / pv("ppe_gross") * 100 if pv("cip") is not None and pv("ppe_gross") else None
    gi, gr = _g(v("inv"), pv("inv")), _g(v("rev"), pv("rev"))
    material = v("inv") is not None and v("rev") and v("inv") / v("rev") >= 0.03      # inventory that matters to the business
    m["inv_minus_rev"] = gi - gr if gi is not None and gr is not None and material else None
    rev, rev_p = v("rev"), pv("rev")
    m["dso"] = v("ar") / rev * 365 if v("ar") is not None and rev and rev > 0 else None
    m["dso_prev"] = pv("ar") / rev_p * 365 if pv("ar") is not None and rev_p and rev_p > 0 else None
    ebit, intr = v("ebit"), v("interest")
    m["int_burden"] = intr / ebit * 100 if intr is not None and ebit and ebit > 0 else None
    m["int_burden_prev"] = pv("interest") / pv("ebit") * 100 if pv("interest") is not None and pv("ebit") and pv("ebit") > 0 else None
    m["ebit_negative"] = ebit is not None and ebit <= 0 and intr is not None and intr > 0
    debt = sum(x for x in (v("debt"), v("debt_cur"), v("fin_lease")) if x is not None) if v("debt") is not None else None
    debt_p = sum(x for x in (pv("debt"), pv("debt_cur"), pv("fin_lease")) if x is not None) if pv("debt") is not None else None
    m["debt"], m["debt_growth"] = debt, _g(debt, debt_p)
    m["rev"], m["ocf"], m["capex"], m["rev_growth"] = rev, ocf, capex, gr
    return m


# ------------------------------------------------------------------ fixed reading rules (stated on the page)
RULES = [("gap", "資金缺口：資本支出大於營運現金流", "Funding gap: capex above operating cash flow",
          lambda m: (m.get("capex_ocf") is not None and m["capex_ocf"] > 1.0) or m.get("ocf_negative")),
         ("cip", "買了還沒上線：在建工程佔固定資產 ≥20% 且比一年前高", "Not yet in service: construction in progress ≥20% of gross PP&E and rising",
          lambda m: m.get("cip_share") is not None and m["cip_share"] >= 20 and m.get("cip_share_prev") is not None and m["cip_share"] > m["cip_share_prev"]),
         ("inv", "存貨堆積：存貨成長比營收成長快 20 個百分點以上", "Inventory building: inventory growth ≥20pp above revenue growth",
          lambda m: m.get("inv_minus_rev") is not None and m["inv_minus_rev"] >= 20),
         ("dso", "收款變慢：應收帳款天數比一年前多 15 天以上", "Slower collections: DSO up ≥15 days y/y",
          lambda m: m.get("dso") is not None and m.get("dso_prev") is not None and m["dso"] - m["dso_prev"] >= 15),
         ("int", "利息壓力：利息吃掉營業利益 ≥30%（或營業虧損仍要付息）", "Interest burden: interest ≥30% of operating income (or a loss with interest due)",
          lambda m: (m.get("int_burden") is not None and m["int_burden"] >= 30) or m.get("ebit_negative")),
         ("debt", "負債快速擴張：總負債一年增加 ≥30%", "Fast debt growth: total debt +30% y/y",
          lambda m: m.get("debt_growth") is not None and m["debt_growth"] >= 30)]


def flags(m: Dict) -> List[str]:
    return [k for k, _zh, _en, f in RULES if f(m)]


# ------------------------------------------------------------------ EDGAR refresh
def load() -> Dict[str, Dict]:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


async def refresh(syms: List[str], budget_s: float = 60, ttl_h: float = 168) -> Dict[str, Dict]:
    from .edgar_holdings import ticker_map
    cache = load()
    try:
        tmap = await ticker_map()
    except Exception as e:  # noqa: BLE001
        log.warning("SEC ticker map unavailable: %s", e)
        return cache
    t0, n = time.time(), 0
    for s in sorted(syms, key=lambda x: float((cache.get(x) or {}).get("ts", 0))):          # oldest first
        if time.time() - t0 > budget_s:
            break
        rec = cache.get(s) or {}
        if time.time() - float(rec.get("ts", 0)) < ttl_h * 3600 and rec.get("pv") == PV:
            continue
        cik = (tmap.get(s) or tmap.get(s.replace(".", "-")) or {}).get("cik")
        if not cik:
            cache[s] = {"ts": time.time(), "pv": PV, "error": "no CIK"}
            continue
        try:
            cf = await http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=40, retries=1)
            p = parse(cf or {})
            cache[s] = {"ts": time.time(), "pv": PV, "cik": cik, "p": p, "m": metrics(p) if p else None}
            n += 1
            await asyncio.sleep(0.15)
        except Exception as e:  # noqa: BLE001
            log.info("fundamentals %s: %s", s, e)
            cache[s] = {**rec, "ts": time.time() - (ttl_h - 24) * 3600, "pv": PV}        # retry in a day
    if n:
        tmp = CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        tmp.replace(CACHE)
    return cache
