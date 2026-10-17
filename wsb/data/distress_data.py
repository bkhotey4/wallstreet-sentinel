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
import re
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
           "ltd": ("LongTermDebt", "LongTermDebtAndCapitalLeaseObligations", "DebtInstrumentCarryingAmount",
                   "DebtLongtermAndShorttermCombinedAmount"),
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


def ttm_ex(facts: List[Dict]) -> Optional[Tuple[str, float, bool]]:
    """(end, value, annualized).  Like ttm(), but a company without a comparable prior year (a recent IPO: its first
    10-Qs carry no full prior fiscal year) still gets a figure: four discrete quarters if it has them, otherwise this
    year's year-to-date scaled to twelve months (flagged, because seasonal businesses distort it)."""
    r = ttm(facts)
    if r:
        return r[0], r[1], False
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
    qs = sorted([(s_, e, v) for (s_, e), v in per.items() if 80 <= (_d(e) - _d(s_)).days <= 100], key=lambda x: x[1])
    chain = [q for q in qs if q[1] == end]
    while chain and len(chain) < 4:                      # walk back through back-to-back quarters
        prev = [q for q in qs if abs((_d(chain[-1][0]) - timedelta(days=1) - _d(q[1])).days) <= 5]
        if not prev:
            break
        chain.append(prev[-1])
    if len(chain) == 4:
        return end, sum(q[2] for q in chain), False
    ytd = [((_d(e) - _d(s_)).days, v) for (s_, e), v in per.items() if e == end and 80 <= (_d(e) - _d(s_)).days <= 300]
    if ytd:
        n, v = max(ytd)
        return end, v * 365.0 / n, True
    return None


def _pick_instant(cf: Dict, tags: Tuple[str, ...], at: str, back_days: int = 100) -> Optional[float]:
    """Value at the balance-sheet date from any of the tags (in order); only if none reports that date, the latest earlier
    value within `back_days`.  (A company that switches tags — CoreWeave dropped LongTermDebt in its 2026 Q2 10-Q and
    kept DebtInstrumentCarryingAmount — must not show last quarter's debt.)"""
    vals = [instants(_facts(cf, tag)) for tag in tags]
    for v in vals:
        if at in v:
            return v[at]
    for v in vals:
        near = [e for e in v if 0 <= (_d(at) - _d(e)).days <= back_days]
        if near:
            return v[max(near)]
    return None


def _near(series: Dict[str, float], at: str, days: int, tol: int = 25) -> Optional[float]:
    tgt = _d(at) - timedelta(days=days)
    c = [e for e in series if abs((_d(e) - tgt).days) <= tol]
    return series[min(c, key=lambda e: abs((_d(e) - tgt).days))] if c else None


BS_V = 3      # balance-sheet parser version (cached sheets below it are re-read)


def parse_balance(cf: Dict) -> Optional[Dict]:
    """Latest balance sheet + TTM flows from a companyfacts document (US-GAAP filers only)."""
    a = instants(_facts(cf, "Assets"))
    if not a:
        return None
    at = max(a)
    out: Dict = {"end": at}
    for k, tags in INSTANT.items():
        out[k] = _pick_instant(cf, tags, at)
    ann = []
    for k, tags in FLOWS.items():
        best = None
        for tag in tags:
            r = ttm_ex(_facts(cf, tag))
            if r and (_d(at) - _d(r[0])).days <= 100 and (best is None or r[0] > best[0] or (r[0] == best[0] and best[2] and not r[2])):
                best = r
        out[k + "_ttm"] = best[1] if best else None
        if best and best[2]:
            ann.append(k)
    out["annualized"] = ann                                   # flows scaled up from year-to-date (recent IPO)
    out["pv"] = BS_V
    dep = {}
    for tag in INSTANT["deposits"]:
        dep = instants(_facts(cf, tag)) or dep
    out["deposits_q"] = _near(dep, at, 91) if dep else None          # one quarter earlier
    debt_hist: Dict[str, float] = {}
    for tag in reversed(INSTANT["ltd"]):                       # earlier tags in the list win on the same date
        debt_hist.update(instants(_facts(cf, tag)))
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
            if time.time() - float(rec.get("bs_ts", 0)) > bs_ttl or (rec.get("bs") and rec["bs"].get("pv", 1) < BS_V):  # parser upgrade
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


# ============================================================ automatic discovery (keeps the watch list current)
F_SCAN = DATA_DIR / "earn_distress_scan.json"        # market-wide red-flag filings (SEC full-text search)
F_SCREEN = DATA_DIR / "earn_distress_screen.json"    # market-wide balance-sheet screen (SEC frames)
F_AUTO = DATA_DIR / "earn_distress_auto.json"        # companies the radar added by itself
EFTS = "https://efts.sec.gov/LATEST/search-index"
SCAN_ITEMS = ("1.03", "2.04", "4.02")          # 3.01 is left out: most are routine (merger / exchange transfer)
SCAN_FORMS = ("NT 10-K", "NT 10-Q")
SCREEN_TAGS = {"assets": ("Assets", True), "liab": ("Liabilities", True), "equity": ("StockholdersEquity", True),
               "deposits": ("Deposits", True), "aoci": ("AccumulatedOtherComprehensiveIncomeLossNetOfTax", True),
               "htm_loss": ("HeldToMaturitySecuritiesAccumulatedUnrecognizedHoldingLoss", True),
               "cash": ("CashAndCashEquivalentsAtCarryingValue", True), "ltd": ("LongTermDebt", True),
               "ltd_nc": ("LongTermDebtNoncurrent", True),
               # flows: summed over the last four quarters (one quarter's write-off must not flag a company)
               "ebit": ("OperatingIncomeLoss", False), "interest": ("InterestExpense", False),
               "interest2": ("InterestExpenseNonoperating", False)}


def _jload(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", p.name, e)
        return default


def _jsave(p, d) -> None:
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


_TICK = re.compile(r"\(([A-Z0-9.\-]{1,7})(?:,\s*[A-Z0-9.\-]+)*\)\s+\(CIK")


def parse_efts(js: Dict) -> List[Dict]:
    """SEC full-text search hits → {cik, ticker, name, form, date, items, adsh}."""
    out = []
    for h in ((js or {}).get("hits") or {}).get("hits") or []:
        s = h.get("_source") or {}
        dn = (s.get("display_names") or [""])[0]
        m = _TICK.search(dn)
        cik = (s.get("ciks") or [None])[0]
        if not cik:
            continue
        out.append({"cik": int(cik), "ticker": m.group(1) if m else None, "name": re.sub(r"\s*\(.*$", "", dn).strip(),
                    "form": s.get("form") or (s.get("root_forms") or [""])[0], "date": s.get("file_date"),
                    "items": [str(i) for i in (s.get("items") or [])], "adsh": str(h.get("_id", "")).split(":")[0]})
    return out


async def _efts_all(params: Dict, pages: int = 3) -> List[Dict]:
    out: List[Dict] = []
    for p in range(pages):
        js = await http.get(EFTS, params={**params, "from": p * 100}, headers=SEC_HDR, timeout=30, retries=1)
        got = parse_efts(js)
        out += got
        total = (((js or {}).get("hits") or {}).get("total") or {}).get("value") or 0
        if len(got) < 100 or (p + 1) * 100 >= total:
            break
        await asyncio.sleep(0.2)
    return out


async def scan(today: Optional[date] = None, force: bool = False) -> Dict:
    """Every red-flag filing in the whole US market over the last `scan_days` days (cached `scan_ttl_h`)."""
    old = _jload(F_SCAN, {})
    if not force and time.time() - float(old.get("ts", 0)) < float(cfg().get("scan_ttl_h", 6)) * 3600:
        return old
    today = today or us_today()
    lo = (today - timedelta(days=int(cfg().get("scan_days", 30)))).isoformat()
    rng = {"dateRange": "custom", "startdt": lo, "enddt": today.isoformat()}
    hits: List[Dict] = []
    try:
        for code in SCAN_ITEMS:
            got = await _efts_all({"q": f'"Item {code}"', "forms": "8-K", **rng})
            hits += [{**g, "code": code} for g in got if code in g["items"]]     # the text match alone is not enough
            await asyncio.sleep(0.2)
        for form in SCAN_FORMS:
            hits += [{**g, "code": form} for g in await _efts_all({"forms": form, **rng})]
            await asyncio.sleep(0.2)
    except Exception as e:  # noqa: BLE001
        log.warning("distress filing scan failed: %s", e)
        HEALTH.fail("sec_scan", e, every=86400)
        return old
    res = {"ts": time.time(), "from": lo, "hits": hits}
    _jsave(F_SCAN, res)
    HEALTH.ok("sec_scan", len(hits), every=86400)
    return res


def screen_period(today: date) -> str:
    """Latest calendar quarter that ended at least 75 days ago (by then nearly every 10-Q is filed)."""
    d = today - timedelta(days=75)
    q = (d.month - 1) // 3                     # quarters fully ended before d's quarter
    return f"CY{d.year - 1}Q4" if q == 0 else f"CY{d.year}Q{q}"


def ttm_frames(per: str) -> Tuple[List[str], List[str]]:
    """Frames whose sum gives the trailing four quarters ending at `per`: (added, subtracted).
    Most companies never file a stand-alone Q4, so TTM = last calendar year + this year's quarters − the same
    quarters a year earlier (CY2026Q2 → CY2025 + 26Q1 + 26Q2 − 25Q1 − 25Q2)."""
    y, q = int(per[2:6]), int(per[7])
    if q == 4:
        return [f"CY{y}"], []
    return [f"CY{y - 1}"] + [f"CY{y}Q{i}" for i in range(1, q + 1)], [f"CY{y - 1}Q{i}" for i in range(1, q + 1)]


def screen_candidates(fr: Dict[str, Dict[int, float]], names: Dict[int, Tuple[str, str]]) -> List[Dict]:
    """Balance-sheet screen over every filer of one quarter (the radar's own red lines, labelled on the site):
      corporate  assets ≥ min and quarterly operating income below quarterly interest, or a loss with negative equity
      bank       deposits ≥ 40 % of assets, assets ≥ bank min, securities losses ≤ −25 % of equity or equity < 7 % of assets"""
    c = cfg()
    min_a, min_bank = float(c.get("screen_min_assets", 2e9)), float(c.get("screen_min_bank_assets", 10e9))
    out = []
    for cik, ta in (fr.get("assets") or {}).items():
        if cik not in names or ta < min_a:
            continue
        sym, title = names[cik]
        eq, dep = fr.get("equity", {}).get(cik), fr.get("deposits", {}).get(cik)
        why = None
        if dep and dep / ta >= 0.4:
            if ta < min_bank or eq is None or eq <= 0:
                continue
            loss = (fr.get("aoci", {}).get(cik) or 0.0) - (fr.get("htm_loss", {}).get(cik) or 0.0)
            if loss / eq <= -0.25:
                why = f"證券評價損失達股東權益的 {loss / eq * 100:.0f}%"
            elif eq / ta < 0.07:
                why = f"股東權益只有資產的 {eq / ta * 100:.1f}%"
            kind = "bank"
        else:
            ebit = fr.get("ebit", {}).get(cik)
            intr = fr.get("interest", {}).get(cik) or fr.get("interest2", {}).get(cik)
            liab = fr.get("liab", {}).get(cik)
            debt = fr.get("ltd", {}).get(cik) or fr.get("ltd_nc", {}).get(cik)
            cash = fr.get("cash", {}).get(cik)
            if debt is not None and cash is not None and cash >= debt:
                continue                                       # more cash than debt: losses can't force a default
            if ebit is not None and intr and intr > 0 and ebit < intr and (liab is None or liab / ta > 0.5):
                why = f"近四季營業利益 {ebit / 1e6:,.0f}M 不夠付利息 {intr / 1e6:,.0f}M"
            elif ebit is not None and ebit <= 0 and eq is not None and eq < 0:
                why = "近四季虧損且股東權益為負"
            kind = "auto"
        if why:
            out.append({"sym": sym, "cik": cik, "zh": title, "kind": kind, "why": why, "assets": ta})
    out.sort(key=lambda x: -x["assets"])
    return out[: int(c.get("auto_max", 40))]


def _names_by_cik(tmap: Dict[str, Dict]) -> Dict[int, Tuple[str, str]]:
    """CIK → (primary ticker, title): company_tickers.json lists the primary listing first."""
    out: Dict[int, Tuple[str, str]] = {}
    for t, v in tmap.items():
        out.setdefault(int(v["cik"]), (t, v.get("title") or t))
    return out


async def screen(tmap: Dict[str, Dict], today: Optional[date] = None, force: bool = False) -> Dict:
    old = _jload(F_SCREEN, {})
    per = screen_period(today or us_today())
    if not force and old.get("period") == per and time.time() - float(old.get("ts", 0)) < float(cfg().get("screen_ttl_h", 72)) * 3600:
        return old
    fr: Dict[str, Dict[int, float]] = {}

    async def frame(tag, p):
        js = await http.get(f"https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/{p}.json", headers=SEC_HDR, timeout=60, retries=1)
        await asyncio.sleep(0.2)
        return {int(r["cik"]): float(r["val"]) for r in (js or {}).get("data", []) if r.get("val") is not None}

    try:
        for k, (tag, inst) in SCREEN_TAGS.items():
            if inst:
                fr[k] = await frame(tag, per + "I")
                continue
            add, sub = ttm_frames(per)
            fa = [await frame(tag, p) for p in add]
            fs = [await frame(tag, p) for p in sub]
            fr[k] = {c: sum(f[c] for f in fa) - sum(f[c] for f in fs) for c in fa[0] if all(c in f for f in fa + fs)}
    except Exception as e:  # noqa: BLE001
        log.warning("distress frames screen failed: %s", e)
        HEALTH.fail("sec_screen", e, every=86400)
        return old
    if len(fr.get("assets", {})) < 1000:                     # the quarter is barely filed yet → keep the previous screen
        return old
    res = {"ts": time.time(), "period": per, "cands": screen_candidates(fr, _names_by_cik(tmap)),
           "assets": {str(k): v for k, v in fr["assets"].items()}}
    _jsave(F_SCREEN, res)
    HEALTH.ok("sec_screen", len(res["cands"]), every=86400)
    return res


def update_auto(scn: Dict, scr: Dict, tmap: Dict[str, Dict], fixed: set, today: date) -> Dict[str, Dict]:
    """Merge today's discoveries into the auto list; drop entries that stopped qualifying `auto_keep_days` ago."""
    auto = _jload(F_AUTO, {})
    names = _names_by_cik(tmap)
    assets = {int(k): v for k, v in (scr.get("assets") or {}).items()}
    min_scan = float(cfg().get("scan_min_assets", 1e9))
    td = today.isoformat()

    def hit(sym, zh, kind, why, src):
        if sym in fixed:
            return
        r = auto.get(sym) or {"added": td}
        r.update({"zh": r.get("zh") or zh, "kind": kind, "why": why, "src": src, "last_hit": td})
        auto[sym] = r

    for c in scr.get("cands") or []:
        hit(c["sym"], c["zh"], c["kind"], c["why"], "screen")
    for h in sorted(scn.get("hits") or [], key=lambda x: x.get("date") or ""):
        nm = names.get(h["cik"])
        if not nm or assets.get(h["cik"], 0) < min_scan:       # unlisted or small filers are skipped
            continue
        _lv, txt = RED_ITEMS.get(h["code"]) or LATE_FORMS.get(h["code"]) or ("watch", h["code"])
        hit(nm[0], nm[1], "auto", f"{h['date']} {txt}", "filing")
    keep = int(cfg().get("auto_keep_days", 30))
    for s in [s for s, r in auto.items() if s in fixed or (today - date.fromisoformat(r["last_hit"])).days > keep]:
        auto.pop(s)
    _jsave(F_AUTO, auto)
    return auto


def load_auto() -> Dict[str, Dict]:
    return _jload(F_AUTO, {})


async def discover(fixed: set) -> Dict[str, Dict]:
    """Market-wide scan + screen → the auto list (each step falls back to its cached result on failure)."""
    from .edgar_holdings import ticker_map
    if not cfg().get("auto_discover", True):
        return load_auto()
    try:
        tmap = await ticker_map()
    except Exception as e:  # noqa: BLE001
        log.warning("SEC ticker map unavailable: %s", e)
        return load_auto()
    scn = await scan()
    scr = await screen(tmap)
    return update_auto(scn, scr, tmap, fixed, us_today())
