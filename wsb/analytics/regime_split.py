"""依環境拆開驗證 + 滯脹年代對照.

1. Regime labels for every day, from data only:
   * Fed direction: 6-month change of the effective fed funds rate (FEDFUNDS, monthly): ≥ +0.25pp hiking,
     ≤ −0.25pp easing, otherwise on hold.
   * Stock–bond sign: 60-day correlation of S&P 500 returns with bond returns (− daily change of the 10-year yield):
     > 0 stocks and bonds move together (bonds stop hedging, 2022), otherwise opposite.
2. The out-of-sample crash-odds predictions (shock.walk_forward, labels passed to shock.model_quality) split by regime: AUC, days and events per regime, so
   it is visible when today's regime is one the model has rarely been tested in.
3. Stagflation analogs (settings.yaml regime_split.analogs): what the S&P, 10-year, fed funds, oil, CPI and
   unemployment did in each episode, and how close today's macro mix is to each episode's start.
Descriptive, not a forecast."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

FRED_IDS = ("FEDFUNDS", "WTISPLC", "CPIAUCSL", "UNRATE")      # all with full history (1950+)
FED_ZH = {"hiking": "升息中", "easing": "降息中", "hold": "按兵不動"}
SB_ZH = {"same": "股債同向（公債不避險）", "opposite": "股債反向（公債能避險）"}


def cfg() -> Dict:
    d = {"fed_step_pp": 0.25, "fed_months": 6, "corr_days": 60, "min_events": 5,
         "analogs": [{"name": "1973–74 石油禁運", "start": "1973-01-11", "end": "1974-10-03"},
                     {"name": "1980–82 Volcker 升息", "start": "1980-11-28", "end": "1982-08-12"},
                     {"name": "1990 波斯灣戰爭", "start": "1990-07-16", "end": "1990-10-11"},
                     {"name": "1994 債市屠殺", "start": "1994-02-02", "end": "1994-04-04"},
                     {"name": "2022 暴力升息", "start": "2022-01-03", "end": "2022-10-12"}]}
    return {**d, **(SETTINGS.get("regime_split", {}) or {})}


def labels(fedfunds: Optional[pd.Series], spx: Optional[pd.Series], dgs10: Optional[pd.Series], c: Optional[Dict] = None) -> pd.DataFrame:
    """Daily DataFrame with columns fed / sb (missing where the inputs do not cover the day)."""
    c = c or cfg()
    cols = {}
    if fedfunds is not None and len(fedfunds.dropna()) > int(c["fed_months"]) + 1:
        f = fedfunds.dropna()
        d6 = f - f.shift(int(c["fed_months"]))
        step = float(c["fed_step_pp"])
        lab = pd.Series(np.where(d6 >= step, "hiking", np.where(d6 <= -step, "easing", "hold")), index=f.index)[d6.notna()]
        # a month's average is known after the month ends: label the next month's days with it (no look-ahead)
        lab.index = lab.index + pd.offsets.MonthBegin(1)
        cols["fed"] = lab
    if spx is not None and dgs10 is not None and len(spx.dropna()) > 300 and len(dgs10.dropna()) > 300:
        j = pd.concat([spx.dropna().pct_change(fill_method=None).rename("s"), (-dgs10.dropna().diff()).rename("b")], axis=1).dropna()
        n = int(c["corr_days"])
        corr = j["s"].rolling(n, min_periods=n).corr(j["b"]).dropna()
        cols["sb"] = pd.Series(np.where(corr > 0, "same", "opposite"), index=corr.index)
    if not cols:
        return pd.DataFrame()
    days = cols["sb"].index if "sb" in cols else pd.bdate_range(cols["fed"].index[0], pd.Timestamp.today().normalize())
    out = pd.DataFrame(index=days)
    for k, s in cols.items():
        out[k] = s.reindex(out.index.union(s.index)).ffill().reindex(out.index) if k == "fed" else s.reindex(out.index)
    return out


def _auc(p: np.ndarray, y: np.ndarray) -> Optional[float]:
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    r = pd.Series(np.r_[pos, neg]).rank().values
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def split(oos: pd.DataFrame, lab: pd.DataFrame, min_events: int = 5) -> List[Dict]:
    """oos: DataFrame (date index) with p (predicted) and y (0/1).  One row per (dimension, regime)."""
    if oos is None or not len(oos) or lab is None or not len(lab):
        return []
    j = oos.join(lab, how="inner")
    out = []
    for dim, names in (("fed", FED_ZH), ("sb", SB_ZH)):
        if dim not in j:
            continue
        jj = j.dropna(subset=[dim])
        for k, zh in names.items():
            m = jj[jj[dim] == k]
            ev = int(m["y"].sum())
            a = _auc(m["p"].values, m["y"].values.astype(int)) if ev >= min_events and len(m) - ev >= min_events else None
            out.append({"dim": dim, "key": k, "zh": zh, "days": int(len(m)), "events": ev, "auc": a,
                        "share": float(len(m) / len(jj) * 100) if len(jj) else None})
    return out


def current(lab: pd.DataFrame) -> Dict:
    if lab is None or not len(lab):
        return {}
    last = lab.ffill().iloc[-1]
    return {k: str(last[k]) for k in lab.columns if isinstance(last.get(k), str)}


# ------------------------------------------------------------------------------------------------ analogs
def _at(s: Optional[pd.Series], d: pd.Timestamp) -> Optional[float]:
    if s is None:
        return None
    x = s.dropna()
    x = x[x.index <= d]
    return float(x.iloc[-1]) if len(x) else None


def _yoy(s: Optional[pd.Series]) -> Optional[pd.Series]:
    if s is None or len(s.dropna()) < 13:
        return None
    s = s.dropna()
    return (s / s.shift(12) - 1) * 100


def episode(a: str, b: str, spx, get) -> Dict:
    ta, tb = pd.Timestamp(a), pd.Timestamp(b)
    out: Dict = {"start": a, "end": b}
    if spx is not None and len(spx.dropna()):
        s = spx.dropna()
        w = s[(s.index >= ta) & (s.index <= tb)]
        if len(w) > 1:
            out["spx_pct"] = float(w.iloc[-1] / w.iloc[0] - 1) * 100
            out["spx_maxdd"] = float((w / w.cummax() - 1).min() * 100)
    for k, sid, kind in (("y10_bp", "DGS10", "bp"), ("ff_pp", "FEDFUNDS", "pp"), ("oil_pct", "WTISPLC", "pct"), ("unrate_pp", "UNRATE", "pp")):
        x0, x1 = _at(get(sid), ta), _at(get(sid), tb)
        if x0 is not None and x1 is not None:
            out[k] = (x1 - x0) * 100 if kind == "bp" else (x1 / x0 - 1) * 100 if kind == "pct" and x0 > 0 else (x1 - x0)
    cpi = _yoy(get("CPIAUCSL"))
    if cpi is not None:
        out["cpi_start"] = _at(cpi, ta)
        w = cpi[(cpi.index >= ta - pd.DateOffset(months=1)) & (cpi.index <= tb)].dropna()
        out["cpi_peak"] = float(w.max()) if len(w) else None
    return out


def state_vector(get, at: pd.Timestamp) -> Dict[str, Optional[float]]:
    """The macro mix on a day: CPI y/y, oil y/y, fed funds 6-month change, 10-year level, unemployment 12-month change."""
    ff, un = get("FEDFUNDS"), get("UNRATE")
    return {"cpi": _at(_yoy(get("CPIAUCSL")), at), "oil": _at(_yoy(get("WTISPLC")), at),
            "ff6": (None if _at(ff, at) is None or _at(ff, at - pd.DateOffset(months=6)) is None else _at(ff, at) - _at(ff, at - pd.DateOffset(months=6))),
            "y10": _at(get("DGS10"), at),
            "un12": (None if _at(un, at) is None or _at(un, at - pd.DateOffset(months=12)) is None else _at(un, at) - _at(un, at - pd.DateOffset(months=12)))}


def similarity(now: Dict, starts: List[Dict], scale: Dict[str, float]) -> List[Optional[float]]:
    """Distance (in historical standard deviations, averaged over the dimensions both sides have) → 0–100 score."""
    out = []
    for st in starts:
        d = [((now[k] - st[k]) / scale[k]) ** 2 for k in now if now.get(k) is not None and st.get(k) is not None and scale.get(k)]
        out.append(float(100 * np.exp(-np.sqrt(np.mean(d)))) if len(d) >= 3 else None)
    return out


def analogs(spx, get, c: Optional[Dict] = None, today: Optional[pd.Timestamp] = None) -> Dict:
    c = c or cfg()
    today = today or pd.Timestamp.today().normalize()
    eps = [{**a, **episode(a["start"], a["end"], spx, get)} for a in c["analogs"]]
    now = state_vector(get, today)
    starts = [state_vector(get, pd.Timestamp(a["start"])) for a in c["analogs"]]
    scale = {}
    for k, s in (("cpi", _yoy(get("CPIAUCSL"))), ("oil", _yoy(get("WTISPLC"))), ("y10", get("DGS10")),
                 ("ff6", None if get("FEDFUNDS") is None else get("FEDFUNDS").dropna().diff(6)),
                 ("un12", None if get("UNRATE") is None else get("UNRATE").dropna().diff(12))):
        if s is not None and len(s.dropna()) > 24:
            scale[k] = float(s.dropna().std())
    for e, st, sim in zip(eps, starts, similarity(now, starts, scale)):
        e["state"], e["similarity"] = st, sim
    return {"episodes": eps, "now": now, "asof": today.strftime("%Y-%m-%d")}


def build(eng, quality: Optional[Dict]) -> Dict:
    """quality: shock.model_quality output; its walk-forward rows carry `regimes` when labels were passed in."""
    fr, m = getattr(eng, "fred", None), getattr(eng, "market", None)
    if fr is None or m is None:
        return {"available": False}
    c = cfg()
    lab = labels(fr.get("FEDFUNDS"), m.series("^GSPC"), fr.get("DGS10"), c)
    out: Dict = {"available": True, "now": current(lab),
                 "by_horizon": [{"days": w["days"], "drawdown_pct": w["drawdown_pct"], "regimes": w.get("regimes") or []}
                                for w in (quality or {}).get("walk_forward", []) if w.get("n_test")]}
    lh = getattr(getattr(eng, "long_history", None), "spx", None)
    spx = lh if lh is not None and len(lh) else m.series("^GSPC")
    out["analogs"] = analogs(spx, fr.get, c)
    return out
