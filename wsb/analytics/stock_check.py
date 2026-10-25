"""個股估值體檢：大型美股的「三面體檢＋本益比歷史位置＋股價反推成長＋歷史本益比情境」，全部用免費公開資料。

  ① 三面體檢（SEC 財報 XBRL 季資料，近 12 個月合計）
       成長：營收年增率；安全：自由現金流（營運現金流 − 資本支出）、流動比率、淨負債 ÷ 營運現金流；
       獲利：ROE（淨利 ÷ 平均股東權益）、毛利率、淨利率。
  ② 本益比在自己歷史的位置：每週股價 ÷ 當時已公布的近 12 個月每股盈餘（季末 + 45 天才算公布），現在落在過去 5 年第幾百分位。
  ③ 股價反推成長（reverse DCF）：企業價值（市值 + 負債 − 現金）＝ 未來 10 年自由現金流以 g 成長、之後 2.5% 永續成長、
       以 9% 折現的現值 → 解出 g，並和過去 5 年實際營收成長比較。折現率 8%／10% 的結果一起列，看假設差多少。
  ④ 歷史本益比情境：過去 5 年本益比的第 25／50／75 百分位 × 每股盈餘（有分析師預估就用預估，否則用近 12 個月）→ 對應股價。
       這是「如果市場用它過去偏低／中位／偏高的倍數」的換算，不是預測，也不是目標價。

限制：銀行的現金流與流動比率不適用（只看成長、獲利與本益比）；外國公司（IFRS 申報，如台積電 ADR、ASML）SEC 沒有 us-gaap 資料；
股東權益為負（大量買回庫藏股）時 ROE 不適用。快取 data_cache/earn_stockcheck.json（財報 7 天、股價 20 小時）。"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from .capex_link import _cal_q

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_stockcheck.json"
FACTS_TTL = 7 * 86400
PX_TTL = 20 * 3600
PV = 2
BANKS = {"JPM", "GS", "MS", "BAC", "WFC", "C"}
# the ticker moved to a new holding-company filer with no history yet: fall back to the old registrant's facts
OLD_CIK = {"XOM": 34088}
R_BASE, R_LO, R_HI, G_TERM, YEARS = 0.09, 0.08, 0.10, 0.025, 10
PUB_LAG = 45                                                    # days after quarter end before EPS counts as known

FLOWS = {"rev": (("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "RevenuesNetOfInterestExpense", "SalesRevenueNet",
                  "RevenueFromContractWithCustomerIncludingAssessedTax"), "USD"),
         "gp": (("GrossProfit",), "USD"),
         "cogs": (("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"), "USD"),
         "ni": (("NetIncomeLoss", "ProfitLoss"), "USD"),
         "ocf": (("NetCashProvidedByUsedInOperatingActivities",), "USD"),
         "capex": (("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
                    "PaymentsToAcquireOtherPropertyPlantAndEquipment"), "USD"),
         "eps": (("EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted", "EarningsPerShareBasic"), "USD/shares"),
         "shares": (("WeightedAverageNumberOfDilutedSharesOutstanding",), "shares")}
INST = {"equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
        "cur_assets": ("AssetsCurrent",), "cur_liab": ("LiabilitiesCurrent",),
        "cash": ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
        "ltd": ("LongTermDebt", "LongTermDebtAndCapitalLeaseObligations", "DebtLongtermAndShorttermCombinedAmount"),
        "ltd_nc": ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligationsNoncurrent"),
        "ltd_cur": ("LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent"),
        "st": ("ShortTermBorrowings", "CommercialPaper", "DebtCurrent")}


def universe() -> List[str]:
    from ..config import SETTINGS
    return list((SETTINGS.get("street") or {}).get("watchlist") or [])


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)


# ------------------------------------------------------------------ SEC parsing
def _units(cf: Dict, tag: str, unit: str) -> List[Dict]:
    return ((((cf.get("facts") or {}).get("us-gaap") or {}).get(tag) or {}).get("units") or {}).get(unit) or []


def split_factor(filed: str, splits) -> float:
    """Product of the stock splits that happened after a fact was filed (its per-share figure is pre-split)."""
    k = 1.0
    for d, r in splits or ():
        if filed and d > filed:
            k *= r
    return k


def q_flow(cf: Dict, tag: str, unit: str = "USD", additive: bool = True, splits=None) -> Dict[str, float]:
    """{calendar quarter: value} from duration facts; negative values kept (losses).  Additive flows also derive a
    quarter from year-to-date facts (Q = YTD − previous YTD); per-share and share counts only use 3-month facts.
    Per-share values are divided (share counts multiplied) by the splits after each fact's filing date."""
    best: Dict[tuple, Dict] = {}
    for f in _units(cf, tag, unit):
        if f.get("val") is None or not f.get("start") or not f.get("end"):
            continue
        k = (f["start"], f["end"])
        if f.get("filed", "") >= (best.get(k) or {}).get("filed", ""):
            best[k] = f
    if splits and unit in ("USD/shares", "shares"):
        for k, f in list(best.items()):
            sf = split_factor(f.get("filed", ""), splits)
            if sf != 1.0:
                best[k] = dict(f, val=float(f["val"]) / sf if unit == "USD/shares" else float(f["val"]) * sf)
    by_start: Dict[str, List] = {}
    for (s, e), f in best.items():
        span = (date.fromisoformat(e) - date.fromisoformat(s)).days
        if 80 <= span <= 380:
            by_start.setdefault(s, []).append((e, float(f["val"]), span))
    out: Dict[str, float] = {}
    for _s, rows in by_start.items():
        rows.sort()
        prev = 0.0
        for e, v, span in rows:
            q = _cal_q(e)
            if span <= 100:
                out.setdefault(q, v)
            elif additive:
                out.setdefault(q, v - prev)
            prev = v
    if not additive:
        # fourth quarters are usually filed only inside the annual figure: EPS Q4 ≈ FY − Q1..Q3, share count Q4 ≈ the annual average
        for (s, e), f in best.items():
            if (date.fromisoformat(e) - date.fromisoformat(s)).days < 300 or _cal_q(e) in out:
                continue
            inner = [float(g["val"]) for (s2, e2), g in best.items() if s2 >= s and e2 < e and (date.fromisoformat(e2) - date.fromisoformat(s2)).days <= 100]
            if len(inner) == 3:
                out[_cal_q(e)] = float(f["val"]) - sum(inner) if unit == "USD/shares" else float(f["val"])
    return dict(sorted(out.items()))


def q_merge(cf: Dict, tags, unit: str, additive: bool = True, splits=None) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for t in tags:
        for q, v in q_flow(cf, t, unit, additive, splits).items():
            out.setdefault(q, v)
    return dict(sorted(out.items()))


def inst(cf: Dict, tags) -> Dict[str, float]:
    """{calendar quarter: balance} for instant facts (latest filing wins)."""
    out: Dict[str, tuple] = {}
    for t in tags:
        for f in _units(cf, t, "USD"):
            if f.get("val") is None or not f.get("end") or f.get("start"):
                continue
            q = _cal_q(f["end"])
            cur = out.get(q)
            if cur is None or (cur[2] == t and f.get("filed", "") > cur[1]):
                out[q] = (float(f["val"]), f.get("filed", ""), t)
    return {q: v[0] for q, v in sorted(out.items())}


def parse(cf: Dict, splits=None) -> Optional[Dict]:
    p = {k: q_merge(cf, tags, unit, additive=k not in ("eps", "shares"), splits=splits) for k, (tags, unit) in FLOWS.items()}
    if len(p["rev"]) < 8:
        return None
    p.update({k: inst(cf, tags) for k, tags in INST.items()})
    p["name"] = cf.get("entityName") or ""
    return p


# ------------------------------------------------------------------ metrics
def _qs(end_q: str, n: int) -> List[str]:
    y, q = int(end_q[:4]), int(end_q[-1])
    out = []
    for _ in range(n):
        out.append(f"{y}Q{q}")
        q -= 1
        if q == 0:
            y, q = y - 1, 4
    return out[::-1]


def ttm(series: Dict[str, float], end_q: str) -> Optional[float]:
    """Sum of the four quarters ending at end_q.  Retailers with 12/12/12/16-week fiscal quarters sometimes map two
    periods to one calendar quarter, leaving a gap: then the last four periods count if they span at most five quarters."""
    qs = _qs(end_q, 4)
    if all(q in series for q in qs):
        return sum(series[q] for q in qs)
    if end_q not in series:
        return None
    have = [q for q in series if q <= end_q][-4:]
    return sum(series[q] for q in have) if len(have) == 4 and have[0] >= _qs(end_q, 5)[0] else None


def _back(q: str, n: int) -> str:
    return _qs(q, n + 1)[0]


def _g(a, b) -> Optional[float]:
    return (a / b - 1) * 100 if a is not None and b not in (None, 0) and b > 0 else None


def total_debt(p: Dict, q: str) -> Optional[float]:
    g = lambda k: (p.get(k) or {}).get(q)  # noqa: E731
    if g("ltd") is not None:
        base = g("ltd")
    elif g("ltd_nc") is not None or g("ltd_cur") is not None:
        base = (g("ltd_nc") or 0) + (g("ltd_cur") or 0)
    else:
        base = None
    st = g("st")
    if base is None and st is None:
        return None
    return (base or 0) + (st or 0)


def faces(p: Dict, bank: bool = False) -> Optional[Dict]:
    """① growth / safety / profitability on the latest quarter with full TTM revenue."""
    rev = p.get("rev") or {}
    end = next((q for q in reversed(list(rev)) if ttm(rev, q) is not None), None)
    if not end:
        return None
    r_now, r_ago = ttm(rev, end), ttm(rev, _back(end, 4))
    ni = ttm(p.get("ni") or {}, end)
    gp = ttm(p.get("gp") or {}, end)
    if gp is None and ttm(p.get("cogs") or {}, end) is not None and r_now:
        gp = r_now - ttm(p["cogs"], end)
    ocf, capex = ttm(p.get("ocf") or {}, end), ttm(p.get("capex") or {}, end)
    fcf = ocf - capex if ocf is not None and capex is not None else None
    eq = p.get("equity") or {}
    e_now, e_ago = eq.get(end), eq.get(_back(end, 4))
    roe = None
    if ni is not None and e_now is not None and e_now > 0:
        avg = (e_now + e_ago) / 2 if e_ago and e_ago > 0 else e_now
        roe = ni / avg * 100
    ca, cl = (p.get("cur_assets") or {}).get(end), (p.get("cur_liab") or {}).get(end)
    cr = ca / cl if ca and cl else None
    debt, cash = total_debt(p, end), (p.get("cash") or {}).get(end)
    net_debt = debt - cash if debt is not None and cash is not None else (-cash if debt is None and cash is not None else None)
    nd_ocf = net_debt / ocf if net_debt is not None and ocf and ocf > 0 else None
    r5 = ttm(rev, _back(end, 20)) or ttm(rev, _back(end, 12))
    yrs = 5 if ttm(rev, _back(end, 20)) else 3
    cagr = ((r_now / r5) ** (1 / yrs) - 1) * 100 if r5 and r5 > 0 and r_now and r_now > 0 else None
    f = {"end": end, "rev": r_now, "rev_yoy": _g(r_now, r_ago), "ni": ni, "gm": gp / r_now * 100 if gp is not None and r_now else None,
         "nm": ni / r_now * 100 if ni is not None and r_now else None, "roe": roe, "neg_eq": e_now is not None and e_now <= 0,
         "fcf": fcf, "ocf": ocf, "cr": cr, "debt": debt, "cash": cash, "net_debt": net_debt, "nd_ocf": nd_ocf,
         "cagr": cagr, "cagr_yrs": yrs, "bank": bank}
    f["g_grade"] = (None if f["rev_yoy"] is None else "強" if f["rev_yoy"] >= 20 else "普通" if f["rev_yoy"] >= 5 else "慢" if f["rev_yoy"] >= 0 else "衰退")
    if bank:
        f["s_grade"] = "銀行不適用"
    else:
        pts = [fcf is not None and fcf > 0, cr is None or cr >= 1, net_debt is not None and (net_debt <= 0 or (nd_ocf is not None and nd_ocf <= 2))]
        n = sum(pts)
        f["s_grade"] = "穩" if n == 3 else "普通" if n == 2 else "要留意"
    f["p_grade"] = (("權益為負" if f["neg_eq"] else None) if roe is None else "高" if roe >= 20 else "中" if roe >= 10 else "低")
    return f


def eps_ttm_series(p: Dict) -> pd.Series:
    """TTM diluted EPS indexed by the date it became public (quarter end + 45 days)."""
    eps = p.get("eps") or {}
    out = {}
    for q in eps:
        v = ttm(eps, q)
        if v is not None:
            y, n = int(q[:4]), int(q[-1])
            qend = pd.Timestamp(year=y, month=n * 3, day=1) + pd.offsets.MonthEnd(0)
            out[qend + pd.Timedelta(days=PUB_LAG)] = v
    return pd.Series(out, dtype=float).sort_index()


def pe_history(px: pd.Series, eps: pd.Series, years: int = 5) -> pd.Series:
    if px.empty or eps.empty:
        return pd.Series(dtype=float)
    e = eps.reindex(px.index.union(eps.index)).ffill().reindex(px.index)
    pe = (px / e)[e > 0].dropna()
    return pe[pe.index >= px.index[-1] - pd.DateOffset(years=years)]


def pv_equity(fcf: float, g: float, r: float = R_BASE, years: int = YEARS, gt: float = G_TERM) -> float:
    """Present value of FCF growing at g for `years`, then gt forever, discounted at r."""
    pv, cf = 0.0, fcf
    for t in range(1, years + 1):
        cf *= 1 + g
        pv += cf / (1 + r) ** t
    return pv + cf * (1 + gt) / (r - gt) / (1 + r) ** years


def implied_growth(ev: float, fcf: float, r: float = R_BASE) -> Optional[float]:
    """g (in %) that makes the DCF value equal today's enterprise value; None when FCF ≤ 0 or out of range."""
    if not fcf or fcf <= 0 or not ev or ev <= 0:
        return None
    lo, hi = -0.5, 1.5
    if pv_equity(fcf, lo, r) > ev or pv_equity(fcf, hi, r) < ev:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if pv_equity(fcf, mid, r) < ev:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2 * 100


def one(sym: str, p: Dict, px: pd.Series, fpe: Optional[float] = None) -> Optional[Dict]:
    bank = sym in BANKS
    f = faces(p, bank)
    if not f:
        return None
    price = float(px.iloc[-1]) if not px.empty else None
    eps_s = eps_ttm_series(p)
    eps_now = float(eps_s.iloc[-1]) if not eps_s.empty else None
    pe = pe_history(px, eps_s)
    pe_now = price / eps_now if price and eps_now and eps_now > 0 else None
    pct = float((pe < pe_now).mean() * 100) if pe_now and len(pe) >= 52 else None
    sh = (p.get("shares") or {})
    shares = sh[list(sh)[-1]] if sh else None
    mcap = price * shares if price and shares else None
    ev = mcap + (f["debt"] or 0) - (f["cash"] or 0) if mcap and not bank else None
    thin = bool(f["fcf"] is not None and f["ocf"] and f["ocf"] > 0 and f["fcf"] < 0.15 * f["ocf"])    # FCF squeezed by heavy investment
    ig = {k: implied_growth(ev, f["fcf"], r) for k, r in (("base", R_BASE), ("lo", R_LO), ("hi", R_HI))} if ev and not thin else {}
    eps_f = price / fpe if price and fpe and fpe > 0 else None
    eps_use, eps_src = (eps_f, "分析師預估") if eps_f else (eps_now, "近 12 個月") if eps_now and eps_now > 0 else (None, None)
    scen = None
    if eps_use and len(pe) >= 52:
        qs = [float(np.percentile(pe, k)) for k in (25, 50, 75)]
        scen = {"pe": qs, "px": [q * eps_use for q in qs], "eps": eps_use, "src": eps_src}
    return {"sym": sym, "name": p.get("name") or sym, "price": price, "px_date": px.index[-1].strftime("%Y-%m-%d") if not px.empty else None,
            **f, "eps": eps_now, "pe": pe_now, "pe_pct": pct, "pe_n": len(pe), "mcap": mcap, "ev": ev,
            "ig": ig.get("base"), "ig8": ig.get("lo"), "ig10": ig.get("hi"), "fcf_thin": thin, "scen": scen}


def build(d: Optional[Dict] = None, fpe: Optional[Dict[str, float]] = None, last: Optional[Dict[str, tuple]] = None) -> Optional[Dict]:
    """last: {sym: (date, price)} — a fresher close than the weekly history (e.g. the engine's daily prices)."""
    d = d if d is not None else load()
    rows, skipped = [], []
    for sym in universe():
        p, pxd = (d.get("facts") or {}).get(sym), (d.get("px") or {}).get(sym)
        if not p:
            skipped.append(sym)
            continue
        px = pd.Series(pxd or {}, dtype=float)
        px.index = pd.to_datetime(px.index)
        if last and sym in last and last[sym][1]:
            ld = pd.Timestamp(last[sym][0])
            if px.empty or ld > px.index.max():
                px.loc[ld] = float(last[sym][1])
        try:
            r = one(sym, p, px.sort_index(), (fpe or {}).get(sym))
        except Exception:  # noqa: BLE001
            log.exception("stock check %s", sym)
            r = None
        if r and (date.today() - (pd.Timestamp(year=int(r["end"][:4]), month=int(r["end"][-1]) * 3, day=1) + pd.offsets.MonthEnd(0)).date()).days > 300:
            r = None                                                      # the revenue tag went stale — better blank than old
        (rows.append(r) if r else skipped.append(sym))
    if not rows:
        return None
    return {"rows": rows, "skipped": skipped, "r": R_BASE * 100, "gt": G_TERM * 100}


# ------------------------------------------------------------------ refresh
def _weekly(sym: str):
    """6 years of weekly closes (split-adjusted, as Yahoo reports them) and the split history."""
    import yfinance as yf
    t = yf.Ticker(sym)
    h = t.history(period="6y", interval="1wk", auto_adjust=False)
    s = h["Close"].dropna() if "Close" in h else pd.Series(dtype=float)
    try:
        sp = [(i.strftime("%Y-%m-%d"), float(v)) for i, v in t.splits.items() if v and v > 0 and v != 1]
    except Exception:  # noqa: BLE001
        sp = []
    return {i.strftime("%Y-%m-%d"): round(float(v), 4) for i, v in s.items()}, sp


async def refresh(force: bool = False, budget_s: float = 120) -> Dict:
    from ..data import http
    from ..data.earnings_data import SEC_HDR
    from ..data.edgar_holdings import ticker_map
    d = load()
    if d.get("pv") != PV:
        d = {"pv": PV}
    now, t0 = time.time(), time.time()
    d["ts_check"] = now
    facts, fts, px, pts = d.setdefault("facts", {}), d.setdefault("fts", {}), d.setdefault("px", {}), d.setdefault("pts", {})
    splits = d.setdefault("splits", {})
    syms = universe()
    loop = asyncio.get_running_loop()
    for sym in syms:                                                      # prices + splits first (facts need the splits)
        if time.time() - t0 > budget_s / 2:
            break
        if not force and now - pts.get(sym, 0) < PX_TTL and px.get(sym):
            continue
        try:
            w, sp = await loop.run_in_executor(None, _weekly, sym)
            if len(w) >= 52:
                px[sym], pts[sym] = w, now
                if sp != splits.get(sym, []):
                    splits[sym] = sp
                    fts[sym] = 0                                          # new split → re-read the per-share history
        except Exception as e:  # noqa: BLE001
            log.info("stock check px %s: %s", sym, e)
    try:
        tmap = await ticker_map()
    except Exception as e:  # noqa: BLE001
        log.warning("stock check: no SEC ticker map: %s", e)
        tmap = {}
    for sym in sorted(syms, key=lambda s: fts.get(s, 0)):                 # oldest first, inside the budget
        if time.time() - t0 > budget_s:
            break
        if not force and now - fts.get(sym, 0) < FACTS_TTL:
            continue
        cik = (tmap.get(sym) or {}).get("cik")
        if not cik:
            fts[sym] = now
            continue
        try:
            cf = await http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=40, retries=1)
            p = parse(cf or {}, splits.get(sym))
            if not p and sym in OLD_CIK:
                cf = await http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{OLD_CIK[sym]:010d}.json", headers=SEC_HDR, timeout=40, retries=1)
                p = parse(cf or {}, splits.get(sym))
            if p:
                facts[sym] = p
            else:
                facts.pop(sym, None)
            fts[sym] = now                                                # only after a successful read (a timeout retries next run)
            await asyncio.sleep(0.15)
        except Exception as e:  # noqa: BLE001
            log.info("stock check %s: %s", sym, e)
    d["ts"] = now
    _save(d)
    return d
