"""美國主要公司信用體檢 — for the largest members of each sector: can the company carry its debt, what is due within a
year, and what a 2-percentage-point rise in its borrowing cost would do to interest coverage.

Balance sheets and trailing-twelve-month flows come from the same SEC companyfacts cache as the distress radar
(distress_data), Altman Z'' and naive Merton from distress.py, the bankruptcy-filing probability from bankruptcy.py.
Grade (a rule-of-thumb stand-in for a rating, not a rating):
  強   net cash, or coverage ≥ 8× with net debt / EBITDA ≤ 2
  穩健 coverage ≥ 4× and net debt / EBITDA ≤ 3.5
  普通 coverage ≥ 2× and net debt / EBITDA ≤ 5
  偏弱 coverage ≥ 1× or net debt / EBITDA ≤ 6
  危險 anything worse, or Merton default probability ≥ 5 %, or Altman Z'' < 1.1 with coverage < 2×
Banks and insurers (XLF) are graded on capital instead (equity / assets), REITs and utilities carry high debt by design,
which the page says next to their grade.  Rules from common credit-analysis conventions, not fitted here."""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import pandas as pd

from . import distress as DZ
from . import bankruptcy as BK

GRADES = ["強", "穩健", "普通", "偏弱", "危險"]
HEAVY_BY_DESIGN = {"XLU": "公用事業：受監管、靠借錢蓋電網是常態", "XLRE": "不動產：靠借錢買物業是常態"}


def _f(x) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def one(sym: str, b: Dict, px: pd.Series, etf: str, today, shock_pp: float = 2.0) -> Dict:
    r: Dict = {"sym": sym, "etf": etf, "end": b.get("end")}
    debt, cash = DZ._debt(b), _f(b.get("cash")) or 0.0
    ebit, intr = _f(b.get("ebit_ttm")), _f(b.get("interest_ttm"))
    da, ocf, capex = _f(b.get("da_ttm")), _f(b.get("ocf_ttm")), _f(b.get("capex_ttm"))
    r["debt"], r["cash"] = debt, cash
    r["net_debt"] = (debt - cash) if debt is not None else None
    r["cov"] = ebit / intr if ebit is not None and intr and intr > 0 else None
    ebitda = ebit + da if ebit is not None and da is not None else None
    r["lev"] = (r["net_debt"] / ebitda) if r["net_debt"] is not None and ebitda and ebitda > 0 else None
    r["ebitda_neg"] = ebitda is not None and ebitda <= 0 and (r["net_debt"] or 0) > 0       # owes money and earns nothing to pay it
    due = (_f(b.get("ltd_cur")) or 0.0) + (_f(b.get("debt_cur")) or 0.0)
    r["due_1y"] = due
    r["due_cover"] = (cash / due) if due > 0 else None
    r["fcf"] = (ocf - capex) if ocf is not None and capex is not None else None
    if debt and ebit is not None and intr is not None:
        r["cov_shock"] = ebit / (intr + debt * shock_pp / 100) if (intr + debt * shock_pp / 100) > 0 else None
    else:
        r["cov_shock"] = None
    r["z"] = DZ.altman(b)
    m = DZ.merton_pd(px, b) if len(px) >= 200 else None
    r["merton"] = m["pd"] if m else None
    try:
        r["bk"] = BK.prob(b, today)
    except Exception:  # noqa: BLE001
        r["bk"] = None
    eq, ta = _f(b.get("equity")), _f(b.get("assets"))
    r["eq_assets"] = eq / ta * 100 if eq is not None and ta else None
    r["grade"], r["why"] = grade(r, etf)
    return r


def grade(r: Dict, etf: str):
    if etf == "XLF":
        ea = r.get("eq_assets")
        if ea is None:
            return None, "金融業：看資本，不看利息保障"
        g = "強" if ea >= 12 else "穩健" if ea >= 8 else "普通" if ea >= 6 else "偏弱" if ea >= 4 else "危險"
        return g, f"金融業看資本：權益／資產 {ea:.1f}%"
    nd, cov, lev = r.get("net_debt"), r.get("cov"), r.get("lev")
    if nd is not None and nd <= 0:
        return "強", "淨現金：現金多於負債"
    if cov is None and lev is None and not r.get("ebitda_neg"):
        return None, "財報數字不足"
    # Altman Z'' counts only alongside weak coverage: buy-back heavy companies (negative book equity) and utilities
    # score low on it without being near default.  A missing figure never counts against the company.
    danger = (r.get("merton") or 0) >= 0.05 or (etf not in HEAVY_BY_DESIGN and r.get("z") is not None and r["z"] < 1.1
                                                 and cov is not None and cov < 2)
    c = cov if cov is not None else 99.0
    lv = 99.0 if r.get("ebitda_neg") else lev if lev is not None else 0.0
    if danger:
        g = "危險"
    elif c >= 8 and lv <= 2:
        g = "強"
    elif c >= 4 and lv <= 3.5:
        g = "穩健"
    elif c >= 2 and lv <= 5:
        g = "普通"
    elif c >= 1 or lv <= 6:
        g = "偏弱"
    else:
        g = "危險"
    why = []
    if cov is not None:
        why.append(f"利息保障 {cov:.1f} 倍")
    if lev is not None:
        why.append(f"淨負債／EBITDA {lev:.1f} 倍")
    elif r.get("ebitda_neg"):
        why.append("EBITDA 為負（有負債、本業沒賺錢）")
    if (r.get("merton") or 0) >= 0.05:
        why.append(f"Merton 違約機率 {r['merton'] * 100:.1f}%")
    return g, "、".join(why)


def build(members: Dict, cache: Dict, px: pd.DataFrame, today, n: int = 15) -> Dict:
    rows: List[Dict] = []
    for etf, v in (members.get("sectors") or {}).items():
        for row in sorted(v.get("members") or [], key=lambda x: -x[1])[:n]:
            t, name = row[0], (row[2] if len(row) > 2 else row[0])
            y = t.replace(".", "-")
            rec = cache.get(y) or cache.get(t) or {}
            b = rec.get("bs") or {}
            if not b or not b.get("end"):
                continue
            s = px[y].dropna() if px is not None and y in getattr(px, "columns", []) else pd.Series(dtype=float)
            r = one(y, b, s, etf, today)
            r["name"] = name
            r["heavy"] = HEAVY_BY_DESIGN.get(etf)
            rows.append(r)
    order = {g: i for i, g in enumerate(GRADES)}
    rows.sort(key=lambda r: (r["grade"] is None, -order.get(r["grade"], 0), -(r.get("merton") or 0)))     # weakest first
    by = {}
    for r in rows:
        if r["grade"]:
            by.setdefault(r["etf"], {g: 0 for g in GRADES})[r["grade"]] += 1
    weak = [r for r in rows if r["grade"] in ("偏弱", "危險")]
    shock = [r for r in rows if r.get("cov") and r.get("cov_shock") and r["cov"] >= 2 > r["cov_shock"]]
    return {"available": bool(rows), "rows": rows, "by_sector": by, "n": len(rows), "weak": len(weak),
            "shock_fall": [r["sym"] for r in shock], "counts": {g: sum(1 for r in rows if r["grade"] == g) for g in GRADES}}
