"""企業危機雷達的原始資料：SEC XBRL 資產負債表／現金流（companyfacts）與 SEC 申報警訊（submissions）。

  * companyfacts → latest balance sheet + trailing-twelve-month flows (TTM = FY + YTD − prior-year YTD, so cash-flow
    statements that only report year-to-date figures still give a clean TTM)
  * submissions  → 8-K items that only appear when something is wrong (bankruptcy, debt acceleration, delisting
    notice, auditor change, non-reliance on past statements, impairments) and late-filing notices (NT 10-K / NT 10-Q)

Cached in data_cache/earn_distress.json (the CI build keeps data_cache/earn_* between runs)."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH
from . import http
from .earnings_data import SEC_HDR
from .econcal import us_today

log = logging.getLogger(__name__)
F_DIST = DATA_DIR / "earn_distress.json"

# 8-K items that are filed only when something has gone wrong (SEC Form 8-K General Instructions)
RED_ITEMS = {"1.03": ("alert", "破產或接管（8-K 1.03）"),
             "2.04": ("alert", "觸發加速償債／債務違約事件（8-K 2.04）"),
             "4.02": ("alert", "先前財報不可再依賴（8-K 4.02）"),
             "3.01": ("watch", "收到交易所下市或不符上市標準通知（8-K 3.01）"),
             "4.01": ("watch", "更換會計師（8-K 4.01）"),
             "2.06": ("watch", "重大資產減損（8-K 2.06）")}
LATE_FORMS = {"NT 10-K": ("alert", "年報逾期申報（NT 10-K）"), "NT 10-Q": ("watch", "季報逾期申報（NT 10-Q）"),
              "NT 20-F": ("alert", "外國公司年報逾期（NT 20-F）")}

INSTANT = {"assets": ("Assets",), "liab": ("Liabilities",), "cur_assets": ("AssetsCurrent",), "cur_liab": ("LiabilitiesCurrent",),
           "re": ("RetainedEarningsAccumulatedDeficit",),
           "equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
           "cash": ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
           "ltd": ("LongTermDebt", "LongTermDebtAndCapitalLeaseObligations"),
           "ltd_nc": ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligationsNoncurrent"),
           "ltd_cur": ("LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent"),
           "debt_cur": ("DebtCurrent", "ShortTermBorrowings", "CommercialPaper"),
           "fin_lease": ("FinanceLeaseLiability",), "op_lease": ("OperatingLeaseLiability",),
           "aoci": ("AccumulatedOtherComprehensiveIncomeLossNetOfTax",), "deposits": ("Deposits",),
           # held-to-maturity bonds: carried at cost, so their losses never reach AOCI (the SVB 2023 blind spot)
           "htm_loss": ("HeldToMaturitySecuritiesAccumulatedUnrecognizedHoldingLoss",),
           "htm_gain": ("HeldToMaturitySecuritiesAccumulatedUnrecognizedHoldingGain",),
           "htm_cost": ("DebtSecuritiesHeldToMaturityExcludingAccruedInterestBeforeAllowanceForCreditLoss",
                        "HeldToMaturitySecuritiesAmortizedCostAfterAllowanceForCreditLoss", "HeldToMaturitySecurities",
                        "HeldToMaturitySecuritiesAmortizedCostBeforeOtherThanTemporaryImpairment"),
           "htm_fv": ("HeldToMaturitySecuritiesFairValue",)}
FLOWS = {"ebit": ("OperatingIncomeLoss",), "rev": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"),
         "interest": ("InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt"),
         "ocf": ("NetCashProvidedByUsedInOperatingActivities",),
         "capex": ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"),
         "da": ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"),
         "ni": ("NetIncomeLoss",)}
SHARES = (("dei", "EntityCommonStockSharesOutstanding"), ("us-gaap", "CommonStockSharesOutstanding"),
          ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"), ("us-gaap", "WeightedAverageNumberOfSharesOutstandingBasic"))


def cfg() -> Dict:
    return SETTINGS.get("distress", {}) or {}


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _facts(cf: Dict, tag: str, ns: str = "us-gaap") -> List[Dict]:
    u = (((cf.get("facts") or {}).get(ns) or {}).get(tag) or {}).get("units") or {}
    return u.get("USD") or u.get("shares") or (next(iter(u.values()), []) if u else [])


def instants(facts: List[Dict]) -> Dict[str, float]:
    """end date → value (the latest filing wins)."""
    out, filed = {}, {}
    for f in facts:
        if f.get("val") is None or "end" not in f or f.get("start"):
            continue
        e = f["end"]
        if f.get("filed", "") >= filed.get(e, ""):
            out[e], filed[e] = float(f["val"]), f.get("filed", "")
    return out


def _span(f: Dict) -> int:
    return (_d(f["end"]) - _d(f["start"])).days if f.get("start") else 0


def ttm(facts: List[Dict]) -> Optional[Tuple[str, float]]:
    """(end, trailing-twelve-month value) at the latest reported period end.
    A fiscal year ending there is used as is; otherwise FY + year-to-date − the same year-to-date one year earlier."""
    per, filed = {}, {}
    for f in facts:
        if f.get("val") is None or not f.get("start") or "end" not in f:
            continue
        k = (f["start"], f["end"])
        if f.get("filed", "") >= filed.get(k, ""):
            per[k], filed[k] = float(f["val"]), f.get("filed", "")
    if not per:
        return None
    end = max(e for _s, e in per)
    fy = [v for (s, e), v in per.items() if e == end and 350 <= (_d(e) - _d(s)).days <= 380]
    if fy:
        return end, fy[0]
    for (s, e), ytd in sorted(per.items(), key=lambda kv: (_d(kv[0][1]) - _d(kv[0][0])).days, reverse=True):
        if e != end:
            continue
        n = (_d(e) - _d(s)).days
        if n < 80 or n > 300:
            continue
        prev_fy = [v for (s2, e2), v in per.items() if abs((_d(e2) - (_d(s) - timedelta(days=1))).days) <= 7
                   and 350 <= (_d(e2) - _d(s2)).days <= 380]
        prior = [v for (s2, e2), v in per.items() if abs((_d(e2) - (_d(e) - timedelta(days=365))).days) <= 7
                 and abs((_d(e2) - _d(s2)).days - n) <= 7]
        if prev_fy and prior:
            return end, prev_fy[0] + ytd - prior[0]
    return None


def _pick_instant(cf: Dict, tags: Tuple[str, ...], at: str, back_days: int = 100) -> Optional[float]:
    best = None
    for tag in tags:
        v = instants(_facts(cf, tag))
        if at in v:
            return v[at]
        near = [e for e in v if 0 <= (_d(at) - _d(e)).days <= back_days]
        if near and best is None:
            best = v[max(near)]
    return best


def _near(series: Dict[str, float], at: str, days: int, tol: int = 25) -> Optional[float]:
    tgt = _d(at) - timedelta(days=days)
    c = [e for e in series if abs((_d(e) - tgt).days) <= tol]
    return series[min(c, key=lambda e: abs((_d(e) - tgt).days))] if c else None


def parse_balance(cf: Dict) -> Optional[Dict]:
    """Latest balance sheet + TTM flows from a companyfacts document (US-GAAP filers only)."""
    a = instants(_facts(cf, "Assets"))
    if not a:
        return None
    at = max(a)
    out: Dict = {"end": at}
    for k, tags in INSTANT.items():
        out[k] = _pick_instant(cf, tags, at)
    for k, tags in FLOWS.items():
        best = None
        for tag in tags:
            r = ttm(_facts(cf, tag))
            if r and (_d(at) - _d(r[0])).days <= 100 and (best is None or r[0] > best[0]):
                best = r
        out[k + "_ttm"] = best[1] if best else None
    dep = {}
    for tag in INSTANT["deposits"]:
        dep = instants(_facts(cf, tag)) or dep
    out["deposits_q"] = _near(dep, at, 91) if dep else None          # one quarter earlier
    debt_hist = {}
    for tag in INSTANT["ltd"]:
        debt_hist = instants(_facts(cf, tag)) or debt_hist
    out["ltd_yago"] = _near(debt_hist, at, 365, 40) if debt_hist else None
    out["shares"] = None
    for ns, tag in SHARES:
        fs = _facts(cf, tag, ns)
        vals = [f for f in fs if f.get("val") and f.get("end") and (_d(at) - _d(f["end"])).days <= 200]
        if vals:
            last = max(vals, key=lambda f: (f["end"], f.get("filed", "")))
            out["shares"] = float(last["val"])
            break
    return out


def parse_flags(js: Dict, today: date, days: int = 365) -> List[Dict]:
    """Red-flag filings (8-K items, late-filing notices) from a submissions document, newest first."""
    r = (js or {}).get("filings", {}).get("recent", {})
    n = len(r.get("form", []))
    col = lambda k: (r.get(k) or [""] * n)  # noqa: E731
    cik = int(js.get("cik") or 0)
    lo = (today - timedelta(days=days)).isoformat()
    out, seen = [], set()
    for form, dt, acc, items in zip(col("form"), col("filingDate"), col("accessionNumber"), col("items")):
        if not dt or dt < lo:
            continue
        hits = []
        if form in ("8-K", "8-K/A"):
            hits = [(it, *RED_ITEMS[it]) for it in str(items or "").split(",") if it.strip() in RED_ITEMS]
            hits = [(it.strip(), lv, txt) for it, lv, txt in hits]
        elif form in LATE_FORMS:
            hits = [(form, *LATE_FORMS[form])]
        for code, lv, txt in hits:
            if (code, dt) in seen:
                continue
            seen.add((code, dt))
            out.append({"code": code, "date": dt, "level": lv, "zh": txt, "form": form,
                        "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/" if cik and acc else None})
    return sorted(out, key=lambda x: x["date"], reverse=True)


def load() -> Dict[str, Dict]:
    try:
        return json.loads(F_DIST.read_text(encoding="utf-8")) if F_DIST.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("distress cache unreadable: %s", e)
        return {}


def _save(d: Dict) -> None:
    tmp = F_DIST.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, F_DIST)


async def refresh(syms: List[str], budget_s: Optional[float] = None) -> Dict[str, Dict]:
    """Balance sheets weekly (or soon after a new 10-Q), filing flags twice a day; bounded by a time budget."""
    from .edgar_holdings import ticker_map
    cache = load()
    if not cfg().get("enabled", True):
        return cache
    budget = float(budget_s if budget_s is not None else cfg().get("budget_s", 90))
    try:
        tmap = await ticker_map()
    except Exception as e:  # noqa: BLE001
        log.warning("SEC ticker map unavailable: %s", e)
        return cache
    t0, ok, err, today = time.time(), 0, 0, us_today()
    bs_ttl, fl_ttl = float(cfg().get("balance_ttl_h", 168)) * 3600, float(cfg().get("filings_ttl_h", 12)) * 3600
    # oldest first, so a budget cut never starves the same names every run
    order = sorted(syms, key=lambda s: min(float((cache.get(s) or {}).get("bs_ts", 0)), float((cache.get(s) or {}).get("fl_ts", 0))))
    for s in order:
        if time.time() - t0 > budget:
            break
        cik = (tmap.get(s) or tmap.get(s.replace("-", ".")) or {}).get("cik")
        rec = dict(cache.get(s) or {})
        if not cik:
            rec.update({"cik": None, "bs_ts": time.time(), "fl_ts": time.time()})
            cache[s] = rec
            continue
        try:
            if time.time() - float(rec.get("fl_ts", 0)) > fl_ttl:
                js = await http.get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=30, retries=1)
                rec["flags"] = parse_flags(js, today)
                # a new 10-Q / 10-K since the cached balance sheet → refresh it now instead of waiting a week
                r = js.get("filings", {}).get("recent", {})
                last_rep = max((d for f, d in zip(r.get("form", []), r.get("reportDate", [])) if f in ("10-Q", "10-K") and d), default="")
                if last_rep and last_rep > ((rec.get("bs") or {}).get("end") or ""):
                    rec["bs_ts"] = 0
                rec["fl_ts"] = time.time()
                await asyncio.sleep(0.15)
            if time.time() - float(rec.get("bs_ts", 0)) > bs_ttl:
                cf = await http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=40, retries=1)
                rec["bs"] = parse_balance(cf)
                rec["bs_ts"] = time.time()
                await asyncio.sleep(0.15)
            rec["cik"] = cik
            cache[s] = rec
            ok += 1
        except Exception as e:  # noqa: BLE001
            err += 1
            log.info("distress %s: %s", s, e)
            if "404" in str(e):                    # no XBRL facts (e.g. a fund) → don't retry every run
                rec.update({"cik": cik, "bs_ts": time.time()})
                cache[s] = rec
    if ok or err:
        _save(cache)
    (HEALTH.fail("sec_distress", RuntimeError("SEC distress data failed"), every=86400) if err and not ok
     else HEALTH.ok("sec_distress", ok, every=86400))
    return cache
