"""利率衝擊雷達 — the chain from Treasury yields to AI / tech stocks, in one place, from data only.

1. Why yields moved: 10-year nominal = real yield (DFII10) + breakeven inflation (T10YIE); plus the ACM term premium
   (THREEFYTP10).  The 3-month change of each says which part drove it.
2. Stocks vs bonds ("Fed model" / 1987 check): aggregate earnings yield = non-financial corporate after-tax profits
   (NFCPATAX) ÷ their equity market value (NCBEILQ027S, rolled forward with the S&P 500 since the quarter end),
   minus the 10-year yield (DGS10, since 1962 — covers 1987) and minus the real yield (DFII10, since 2003).
   History shows a negative gap is a valuation statement, not a timing signal: it was negative for most of 1980–1997.
3. Tech's sensitivity to yields: rolling 126-day beta of QQQ and SOX daily returns to the 10-year change (per +10bp),
   with its percentile in its own history.
4. Watch lines that commentators cite (configurable): distance to each line, never a prediction.
5. Fiscal strain: federal interest payments ÷ federal tax receipts (BEA, quarterly), total public debt.
6. Long-end auctions: the latest 10/20/30-year results vs their recent average (from the Treasury module).
7. AI borrowing: implied cost of debt (interest ÷ debt) and debt growth of the AI ledger companies (SEC filings).
Descriptive, not a forecast."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

FRED_IDS = ("DGS10", "DFII10", "T10YIE", "THREEFYTP10", "NFCPATAX", "NCBEILQ027S", "A091RC1Q027SBEA", "W006RC1Q027SBEA", "GFDEBTN")


def cfg() -> Dict:
    d = {"beta_window": 126,
         "watch": [{"t": "^MOVE", "zh": "MOVE 美債波動率", "en": "MOVE bond volatility", "line": 125, "side": "above"},
                   {"t": "IXG", "zh": "全球金融股 ETF（IXG）", "en": "Global financials ETF (IXG)", "line": 125, "side": "below"},
                   {"t": "^TNX", "zh": "美債 10 年殖利率", "en": "10-year yield", "line": 5.25, "side": "above"},
                   {"t": "^TYX", "zh": "美債 30 年殖利率", "en": "30-year yield", "line": 5.5, "side": "above"}]}
    return {**d, **(SETTINGS.get("rates_radar", {}) or {})}


def _pct(s: pd.Series, v: float) -> Optional[float]:
    s = s.dropna()
    return float((s < v).mean() * 100) if len(s) > 20 else None


def _chg(s: pd.Series, months: int = 3) -> Optional[float]:
    s = s.dropna()
    if len(s) < 5:
        return None
    past = s[s.index <= s.index[-1] - pd.DateOffset(months=months)]
    return float(s.iloc[-1] - past.iloc[-1]) if len(past) else None


def decompose(get) -> Optional[Dict]:
    nom, real, be, tp = get("DGS10"), get("DFII10"), get("T10YIE"), get("THREEFYTP10")
    if nom is None or not len(nom.dropna()):
        return None
    out = {"nominal": float(nom.dropna().iloc[-1]), "date": nom.dropna().index[-1].strftime("%Y-%m-%d"), "d_nominal": _chg(nom)}
    for k, s in (("real", real), ("breakeven", be), ("term_premium", tp)):
        if s is not None and len(s.dropna()):
            out[k], out["d_" + k] = float(s.dropna().iloc[-1]), _chg(s)
    drv = {k: out.get("d_" + k) for k in ("real", "breakeven")}
    if all(v is not None for v in drv.values()) and out["d_nominal"] is not None and abs(out["d_nominal"]) >= 0.05:
        out["driver"] = max(drv, key=lambda k: abs(drv[k]))
    return out


def yield_gap(get, spx: Optional[pd.Series]) -> Optional[Dict]:
    prof, mv, nom, real = get("NFCPATAX"), get("NCBEILQ027S"), get("DGS10"), get("DFII10")
    if prof is None or mv is None or nom is None or not len(prof.dropna()) or not len(mv.dropna()):
        return None
    ey = (prof * 1000 / mv * 100).dropna()                    # bn → mn; earnings yield in %
    if not len(ey):
        return None
    q_end = ey.index[-1] + pd.offsets.QuarterEnd(0)
    ey_now, rolled = float(ey.iloc[-1]), False
    if spx is not None and len(spx.dropna()):
        s = spx.dropna()
        base = s[s.index <= q_end]
        if len(base):                                         # market value rolled forward with the S&P since quarter end
            ey_now = ey_now * float(base.iloc[-1]) / float(s.iloc[-1])
            rolled = True
    nq = nom.dropna().resample("QS").mean()
    gap_hist = (ey - nq.reindex(ey.index)).dropna()
    n_now = float(nom.dropna().iloc[-1])
    gap_now = ey_now - n_now
    out = {"ey": ey_now, "ey_q": ey.index[-1].strftime("%Y-%m"), "rolled": rolled, "nominal": n_now, "gap": gap_now,
           "gap_pct": _pct(gap_hist, gap_now), "since": gap_hist.index[0].strftime("%Y") if len(gap_hist) else None}
    for label, d in (("y1987", "1987-07-01"), ("y2000", "2000-01-01"), ("y2007", "2007-04-01")):
        t = pd.Timestamp(d)
        if t in gap_hist.index:
            out[label] = float(gap_hist[t])
    neg = gap_hist[gap_hist < 0]
    out["neg_share"] = float(len(neg) / len(gap_hist) * 100) if len(gap_hist) else None
    if real is not None and len(real.dropna()):
        r = real.dropna()
        out["erp"] = ey_now - float(r.iloc[-1])
        rq = r.resample("QS").mean()
        erp_hist = (ey - rq.reindex(ey.index)).dropna()
        out["erp_pct"], out["erp_since"] = _pct(erp_hist, out["erp"]), (erp_hist.index[0].strftime("%Y") if len(erp_hist) else None)
    return out


def tech_beta(px: Dict[str, pd.Series], tnx: pd.Series, window: int) -> List[Dict]:
    y = tnx.dropna()
    y = y / 10 if len(y) and y.median() > 20 else y
    dy = y.diff() * 100                                       # bp
    out = []
    for t, zh, en in (("QQQ", "那斯達克 100（QQQ）", "Nasdaq 100 (QQQ)"), ("^SOX", "費城半導體", "Semiconductors (SOX)"), ("SPY", "標普 500（SPY）", "S&P 500 (SPY)")):
        s = px.get(t)
        if s is None or len(s.dropna()) < window + 60:
            continue
        r = s.dropna().pct_change(fill_method=None) * 100
        j = pd.concat([r.rename("r"), dy.rename("y")], axis=1).dropna()
        if len(j) < window + 60:
            continue
        cov = j["r"].rolling(window).cov(j["y"])
        var = j["y"].rolling(window).var()
        beta = (cov / var * 10).dropna()                      # % move per +10bp
        corr = j["r"].rolling(window).corr(j["y"]).dropna()
        if not len(beta):
            continue
        out.append({"t": t, "zh": zh, "en": en, "beta": float(beta.iloc[-1]), "beta_pct": _pct(beta, float(beta.iloc[-1])),
                    "corr": float(corr.iloc[-1]) if len(corr) else None})
    return out


def watch_lines(series_of, items: List[Dict]) -> List[Dict]:
    out = []
    for w in items:
        s = series_of(w["t"])
        if s is None or not len(s.dropna()):
            continue
        v = float(s.dropna().iloc[-1])
        if w["t"] in ("^TNX", "^TYX") and v > 20:
            v /= 10
        hit = v >= w["line"] if w["side"] == "above" else v <= w["line"]
        dist = (w["line"] - v) if w["side"] == "above" else (v - w["line"])
        out.append({**w, "now": v, "hit": hit, "dist": dist, "dist_pct": dist / w["line"] * 100, "asof": s.dropna().index[-1].strftime("%Y-%m-%d")})
    return out


def fiscal(get) -> Optional[Dict]:
    ip, rc, debt = get("A091RC1Q027SBEA"), get("W006RC1Q027SBEA"), get("GFDEBTN")
    if ip is None or rc is None or not len(ip.dropna()) or not len(rc.dropna()):
        return None
    ratio = (ip / rc * 100).dropna()
    if not len(ratio):
        return None
    out = {"ratio": float(ratio.iloc[-1]), "q": ratio.index[-1].strftime("%Y-%m"), "pct": _pct(ratio, float(ratio.iloc[-1])),
           "since": ratio.index[0].strftime("%Y"), "interest_bn": float(ip.dropna().iloc[-1]),
           "ratio_1y": float(ratio.iloc[-5]) if len(ratio) > 5 else None, "max": float(ratio.max()), "max_q": ratio.idxmax().strftime("%Y")}
    if debt is not None and len(debt.dropna()):
        out["debt_tn"], out["debt_q"] = float(debt.dropna().iloc[-1]) / 1e6, debt.dropna().index[-1].strftime("%Y-%m")
    return out


def long_auctions(eng) -> List[Dict]:
    tr = getattr(eng, "treasury", None)
    rows = [a for a in (getattr(tr, "auctions", None) or []) if a.get("term") in ("10-Year", "20-Year", "30-Year")]
    return sorted(rows, key=lambda a: str(a.get("date", "")), reverse=True)[:4]


def ai_borrowing(eng) -> List[Dict]:
    led = (getattr(eng, "sector_health", None) or {}).get("ledger") or []
    from ..data import fundamentals as FU
    out = []
    for r in led:
        rec = FU.load().get(r["sym"]) or {}
        p = rec.get("p") or {}
        intr, debt = (p.get("interest") or {}).get("v"), r["m"].get("debt")
        d_end = next(((p.get(k) or {}).get("end") for k in ("debt_all", "debt", "debt_nc") if (p.get(k) or {}).get("v") is not None), None)
        out.append({"sym": r["sym"], "cost": (intr / debt * 100) if intr and debt else None, "debt_growth": r["m"].get("debt_growth"),
                    "int_burden": r["m"].get("int_burden"), "end": r["m"].get("end"), "debt_end": d_end, "debt_bn": debt / 1e9 if debt else None})
    return out


def build(eng) -> Dict:
    fr, m = getattr(eng, "fred", None), getattr(eng, "market", None)
    if fr is None or m is None:
        return {"available": False}
    get = lambda sid: fr.get(sid)  # noqa: E731
    c = cfg()
    px = {t: m.series(t) for t in ("QQQ", "^SOX", "SPY")}
    out = {"available": True, "decomp": decompose(get), "gap": yield_gap(get, m.series("^GSPC")),
           "beta": tech_beta(px, m.series("^TNX"), int(c["beta_window"])), "watch": watch_lines(m.series, c["watch"]),
           "fiscal": fiscal(get), "auctions": long_auctions(eng)}
    try:
        out["ai"] = ai_borrowing(eng)
    except Exception:  # noqa: BLE001
        out["ai"] = []
    return out
