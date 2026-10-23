"""能源傳導鏈 — oil → diesel → inflation expectations → Fed path, in one place, from data only.

1. Refined products vs crude: diesel crack (heating-oil futures HO=F × 42 − Brent), gasoline crack (RB=F × 42 − Brent)
   and the 3-2-1 crack vs WTI, each with its percentile in its own history.  A crack spread at the top of its range
   means the shortage is in refining / distillates, which crude alone understates.
2. Retail diesel (EIA via FRED GASDESW, weekly) and US distillate stocks vs the same week of the previous 5 years
   (EIA weekly, optional: needs a free EIA_API_KEY).
3. The chain: 3-month change of crude, diesel, 5-year breakeven inflation (T5YIE) and the 2-year yield (DGS2),
   plus how much breakevens have moved per +10% in diesel (rolling regression of 20-day changes).  When all links
   move up together the energy shock is reaching the rates market.
Descriptive, not a forecast.  Thresholds are percentiles from settings.yaml (energy_chain)."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

FRED_IDS = ("GASDESW", "T5YIE", "DGS2")
BBL_GAL = 42.0


def cfg() -> Dict:
    d = {"hot_pct": 85.0, "extreme_pct": 95.0, "beta_window": 504, "step": 20, "stocks_low_pct": -8.0}
    return {**d, **(SETTINGS.get("energy_chain", {}) or {})}


def _pct(s: pd.Series, v: float) -> Optional[float]:
    s = s.dropna()
    return float((s < v).mean() * 100) if len(s) > 20 else None


def _chg(s: pd.Series, months: int = 3, rel: bool = False) -> Optional[float]:
    s = s.dropna()
    if len(s) < 5:
        return None
    past = s[s.index <= s.index[-1] - pd.DateOffset(months=months)]
    if not len(past):
        return None
    a, b = float(s.iloc[-1]), float(past.iloc[-1])
    if rel:
        return (a / b - 1) * 100 if b > 0 else None
    return a - b


def cracks(px: Dict[str, pd.Series]) -> List[Dict]:
    """$/bbl spreads; products are quoted in $/gal."""
    ho, rb, bz, cl = (px.get(t) for t in ("HO=F", "RB=F", "BZ=F", "CL=F"))
    out = []

    def one(key, zh, en, s):
        s = s.dropna()
        s = s[np.isfinite(s)]
        if len(s) < 60:
            return
        v = float(s.iloc[-1])
        out.append({"key": key, "zh": zh, "en": en, "now": v, "pct": _pct(s, v), "d3m": _chg(s),
                    "since": s.index[0].strftime("%Y"), "asof": s.index[-1].strftime("%Y-%m-%d")})

    if ho is not None and bz is not None and len(ho) and len(bz):
        one("diesel", "柴油裂解價差（熱燃油 − 布蘭特）", "Diesel crack (HO − Brent)", ho * BBL_GAL - bz)
    if rb is not None and bz is not None and len(rb) and len(bz):
        one("gasoline", "汽油裂解價差（汽油 − 布蘭特）", "Gasoline crack (RBOB − Brent)", rb * BBL_GAL - bz)
    if ho is not None and rb is not None and cl is not None and len(ho) and len(rb) and len(cl):
        one("321", "3-2-1 煉油價差（對 WTI）", "3-2-1 crack (vs WTI)", (2 * rb * BBL_GAL + ho * BBL_GAL - 3 * cl) / 3)
    return out


def distillate_vs_5y(stocks: Optional[pd.Series]) -> Optional[Dict]:
    """Latest weekly stock vs the average of the same ISO week in the previous five years."""
    if stocks is None or len(stocks.dropna()) < 52 * 5 + 1:
        return None
    s = stocks.dropna()
    last_d, last = s.index[-1], float(s.iloc[-1])
    iso = s.index.isocalendar()
    wk = int(iso.week.iloc[-1])
    same = []
    for y in range(1, 6):
        x = s[(iso.year.values == int(iso.year.iloc[-1]) - y) & (iso.week.values == wk)]
        if len(x):
            same.append(float(x.iloc[-1]))
    if len(same) < 3:
        return None
    avg = float(np.mean(same))
    return {"now": last, "avg5": avg, "vs5_pct": (last / avg - 1) * 100, "n_years": len(same), "asof": last_d.strftime("%Y-%m-%d"),
            "d4w": float(last - s.iloc[-5]) if len(s) > 5 else None}


def pass_through(diesel: pd.Series, be: pd.Series, window: int, step: int) -> Optional[Dict]:
    """bp of 5-year breakeven per +10% move in diesel futures, from non-overlapping `step`-day changes."""
    d, b = diesel.dropna(), be.dropna()
    d = d[d > 0]
    j = pd.concat([d.rename("d"), b.rename("b")], axis=1).dropna()
    if len(j) < window:
        return None
    j = j.iloc[-window:].iloc[::-1].iloc[::step].iloc[::-1]          # every `step`-th day, anchored on today
    x = np.log(j["d"]).diff() * 100                                  # % (log) change of diesel
    y = j["b"].diff() * 100                                          # bp change of breakeven
    k = pd.concat([x, y], axis=1).dropna()
    if len(k) < 12 or float(k.iloc[:, 0].var()) == 0:
        return None
    beta = float(np.cov(k.iloc[:, 0], k.iloc[:, 1])[0, 1] / k.iloc[:, 0].var()) * 10
    corr = float(k.iloc[:, 0].corr(k.iloc[:, 1]))
    return {"bp_per_10pct": beta, "corr": corr, "n": int(len(k)), "step": step}


def chain(px: Dict[str, pd.Series], get) -> List[Dict]:
    rows = []
    for key, zh, en, s, rel, unit in (
            ("brent", "布蘭特原油", "Brent crude", px.get("BZ=F"), True, "%"),
            ("diesel_fut", "熱燃油（柴油）期貨", "Heating-oil (diesel) futures", px.get("HO=F"), True, "%"),
            ("diesel_retail", "美國柴油零售價（每週）", "US retail diesel (weekly)", get("GASDESW"), True, "%"),
            ("be5", "5 年期通膨預期", "5-year breakeven inflation", get("T5YIE"), False, "bp"),
            ("y2", "2 年期美債殖利率（反映 Fed 路徑）", "2-year Treasury (Fed path)", get("DGS2"), False, "bp")):
        if s is None or not len(s.dropna()):
            continue
        s = s.dropna()
        s = s[s > 0] if rel else s
        if not len(s):
            continue
        d = _chg(s, 3, rel)
        if d is not None and unit == "bp":
            d *= 100                                                 # percentage points → bp
        rows.append({"key": key, "zh": zh, "en": en, "now": float(s.iloc[-1]), "d3m": d, "unit": unit,
                     "asof": s.index[-1].strftime("%Y-%m-%d")})
    return rows


def build(eng) -> Dict:
    fr, m = getattr(eng, "fred", None), getattr(eng, "market", None)
    if m is None:
        return {"available": False}
    get = (lambda sid: fr.get(sid)) if fr is not None else (lambda sid: pd.Series(dtype=float))  # noqa: E731
    c = cfg()
    px = {t: m.series(t) for t in ("HO=F", "RB=F", "BZ=F", "CL=F")}
    cr = cracks(px)
    ch = chain(px, get)
    if not cr and not ch:
        return {"available": False}
    eia = getattr(eng, "eia", None)
    out = {"available": True, "cracks": cr, "chain": ch,
           "stocks": distillate_vs_5y(getattr(eia, "distillate", None)),
           "pass": pass_through(px["HO=F"], get("T5YIE"), int(c["beta_window"]), int(c["step"])) if len(px["HO=F"]) else None}
    up = [r for r in ch if r["d3m"] is not None and r["d3m"] > 0]
    out["aligned"] = len(ch) >= 4 and len(up) == len(ch)              # every link rising over 3 months
    return out
