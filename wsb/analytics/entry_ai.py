"""AI 視角看進場 — two walk-forward models and one "memory" of similar days, on market data only.

Questions (S&P 500):
* up12: will it be higher 12 months from now?
* dd10: will it fall ≥ 10 % below today's close at some point in the next 6 months?
Features (all point-in-time, each z-scored against its own previous 3 years): VIX level, VIX 1-month change, distance from the
200-day average, 6-month momentum, distance from the 52-week high, OFR financial stress, the site's stress index (SSI) and its
1-month change.  Ridge logistic regression, re-fitted every year on the past only, with an embargo as long as the label looks
ahead; the score that matters is the out-of-sample AUC.  A model below 0.55 is shown as 不採計 (not used).
Memory: the 30 most similar past days (outcome already known, at least 20 days apart) and what the S&P 500 did next.
History-based estimates, not a forecast and never a buy signal."""
from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .crash_odds import forward_min_return
from .lab import _z, fit_logit, predict, walk_forward_logit

log = logging.getLogger(__name__)
MIN_AUC = 0.55
LABELS = {"up12": 252, "dd10": 126}


def features(eng) -> pd.DataFrame:
    from .cooldown import _fsi, _s
    spx, vix = _s(eng, "^GSPC"), _s(eng, "^VIX")
    st = getattr(eng, "stress", None)
    ssi = st.history.dropna() if st is not None and getattr(st, "history", None) is not None else pd.Series(dtype=float)
    idx = spx.index
    v = vix.reindex(idx).ffill(limit=3)
    raw = {"vix": np.log(v), "vix_chg": np.log(v / v.shift(21)), "gap200": spx / spx.rolling(200).mean() - 1,
           "mom126": spx / spx.shift(126) - 1, "dd52": spx / spx.rolling(252, min_periods=200).max() - 1}
    f = _fsi()
    if len(f):
        raw["fsi"] = f.reindex(idx).ffill(limit=10)
    if len(ssi):
        s = ssi.reindex(idx).ffill(limit=3)
        raw["ssi"], raw["ssi_chg"] = s, s - s.shift(21)
    return pd.DataFrame({k: _z(x) for k, x in raw.items()}).dropna()


def labels(spx: pd.Series) -> Dict[str, tuple]:
    out = {}
    f12 = spx.shift(-252) / spx - 1
    out["up12"] = ((f12 > 0).astype(float), f12.notna())
    fmr = forward_min_return(spx, 126)
    out["dd10"] = ((fmr <= -0.10).astype(float), fmr.notna())
    return out


def _nearest(known: pd.DataFrame, now: np.ndarray, k: int, gap: int) -> list:
    d = np.sqrt(((known.values - now) ** 2).sum(axis=1))
    order = np.argsort(d)
    pos = []
    for i in order:
        if all(abs(i - j) >= gap for j in pos):
            pos.append(i)
        if len(pos) >= k:
            break
    return [known.index[i] for i in pos]


def memory_check(F: pd.DataFrame, spx: pd.Series, k: int = 30, gap: int = 20) -> Optional[float]:
    """Out-of-sample test of the memory: on the first trading day of every month, look up neighbours only among days whose
    12-month outcome was already known at that time; AUC of 'share of neighbours that went up' against what happened."""
    f12 = (spx.shift(-252) / spx - 1).reindex(F.index)
    firsts = F.groupby([F.index.year, F.index.month]).head(1).index
    sc, ys = [], []
    for t in firsts:
        if pd.isna(f12.get(t)):
            continue
        cut = F.index[max(F.index.searchsorted(t) - 252, 0)]
        known = F[(F.index < cut) & f12.notna()]
        if len(known) < 750:
            continue
        nb = _nearest(known, F.loc[t].values, k, gap)
        sc.append(float((f12.reindex(nb) > 0).mean()))
        ys.append(bool(f12[t] > 0))
    if len(sc) < 60:
        return None
    from .physics import auc
    return auc(np.array(sc), np.array(ys))


def memory(F: pd.DataFrame, spx: pd.Series, k: int = 30, gap: int = 20) -> Optional[Dict]:
    f12 = (spx.shift(-252) / spx - 1).reindex(F.index) * 100
    known = F[f12.notna()]
    if len(known) < 1000:
        return None
    now = F.iloc[-1].values
    d = np.sqrt(((known.values - now) ** 2).sum(axis=1))
    order = np.argsort(d)
    picked, pos = [], []
    for i in order:
        if all(abs(i - j) >= gap for j in pos):
            pos.append(i)
            picked.append(known.index[i])
        if len(picked) >= k:
            break
    r = f12.reindex(picked)
    dd = (forward_min_return(spx, 126).reindex(picked) * 100)
    a = memory_check(F, spx, k, gap)
    return {"auc": a, "used": a is not None and a >= MIN_AUC, "n": len(picked), "med12": float(r.median()), "up12": float((r > 0).mean() * 100), "dd_med": float(dd.median()),
            "dd10": float((dd <= -10).mean() * 100), "dates": sorted(d_.strftime("%Y-%m") for d_ in picked[:8])}


def build(eng) -> Dict:
    from .cooldown import _s
    spx = _s(eng, "^GSPC")
    try:
        F = features(eng)
    except Exception:  # noqa: BLE001
        log.exception("entry features failed")
        return {"available": False}
    if len(F) < 2500:
        return {"available": False}
    out = {"available": True, "asof": F.index[-1].strftime("%Y-%m-%d"), "since": F.index[0].strftime("%Y"), "feats": list(F.columns)}
    labs = labels(spx)
    for name, (y, valid) in labs.items():
        days = LABELS[name]
        try:
            wf = walk_forward_logit(F, y, valid, days)
            D = F.join(y.rename("_y")).join(valid.rename("_v")).dropna()
            D = D[D["_v"].astype(bool)]
            w = fit_logit(D[F.columns].values, D["_y"].values)
            p_now = float(predict(w, F.iloc[[-1]].values)[0]) * 100
            out[name] = {"auc": wf.get("auc"), "n": wf.get("n"), "skill": wf.get("skill"), "p": p_now, "base": float(D["_y"].mean() * 100),
                         # ranking (AUC) AND probabilities (Brier skill vs the plain base rate) must both beat "usual"
                         "used": wf.get("auc") is not None and wf["auc"] >= MIN_AUC and (wf.get("skill") or -1) > 0,
                         "coef": {c: float(x) for c, x in zip(F.columns, w[1:])}}
        except Exception:  # noqa: BLE001
            log.exception("entry model %s failed", name)
    out["memory"] = memory(F, spx)
    return out
