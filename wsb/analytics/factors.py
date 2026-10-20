"""風格因子模型（類 Barra）— what a stock or a portfolio really is exposed to, and why it moved today.

Factors are long/short return series built from liquid ETFs (free data, daily):
    mkt     市場        SPY
    size    小型股      IWM − SPY
    value   價值        VTV − VUG          (value minus growth)
    mom     動能        MTUM − SPY
    quality 品質        QUAL − SPY
    lowvol  低波動      USMV − SPY
    rate    利率        Δ 10-year yield (percentage points)
    usd     美元        DX-Y.NYB return
    semi    半導體      SMH − SPY
A missing ETF simply drops its factor (the page says which are in use).  Each stock's loadings come from a ridge
regression of its daily returns on the factor returns over the last `lookback` sessions (standardised factors,
light ridge because several factors are correlated).  Portfolio risk = factor part (X'ΣX) + stock-specific part
(Σ w²σ²); today's attribution = loadings × today's factor returns, the rest is stock-specific.
Exposures describe the past two years of co-movement — they drift, and they are not a forecast."""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

FACTORS = [("mkt", "市場", "Market"), ("size", "小型股", "Size (small)"), ("value", "價值", "Value"), ("mom", "動能", "Momentum"),
           ("quality", "品質", "Quality"), ("lowvol", "低波動", "Low volatility"), ("rate", "利率（每 +1 個百分點）", "Rates (per +1pp)"),
           ("usd", "美元", "US dollar"), ("semi", "半導體", "Semiconductors")]
LAB = {k: (zh, en) for k, zh, en in FACTORS}


def cfg() -> Dict:
    return {"lookback": 504, "min_obs": 250, "ridge": 0.05, "cov_days": 252, **(SETTINGS.get("factors", {}) or {})}


def _ret(h: pd.DataFrame, t: str) -> Optional[pd.Series]:
    if t not in h.columns:
        return None
    s = h[t].dropna()
    return s.pct_change(fill_method=None) if len(s) > 60 else None


def factor_returns(h: pd.DataFrame) -> pd.DataFrame:
    """Daily factor returns (fractions; rate = change in yield, percentage points) on the S&P trading calendar."""
    spy = _ret(h, "SPY")
    if spy is None:
        return pd.DataFrame()
    F = {"mkt": spy}
    pairs = {"size": ("IWM", "SPY"), "value": ("VTV", "VUG"), "mom": ("MTUM", "SPY"), "quality": ("QUAL", "SPY"),
             "lowvol": ("USMV", "SPY"), "semi": ("SMH", "SPY")}
    for k, (a, b) in pairs.items():
        ra, rb = _ret(h, a), _ret(h, b)
        if ra is not None and rb is not None:
            F[k] = ra - rb
    if "^TNX" in h.columns:
        y = h["^TNX"].dropna()
        F["rate"] = (y / 10.0 if y.median() > 20 else y).diff()          # ^TNX quoted ×10 on some feeds
    usd = _ret(h, "DX-Y.NYB")
    if usd is not None:
        F["usd"] = usd
    df = pd.DataFrame(F).reindex(spy.dropna().index)
    order = [k for k, *_ in FACTORS if k in df.columns]
    return df[order].dropna(how="all")


def loadings(r: pd.Series, F: pd.DataFrame, c: Optional[Dict] = None) -> Optional[Dict]:
    """Ridge regression of one stock's daily returns on the factors → {"b": {f: loading}, "r2", "sd": specific daily %}."""
    c = c or cfg()
    j = pd.concat([r.rename("_y"), F], axis=1).dropna().iloc[-int(c["lookback"]):]
    if len(j) < int(c["min_obs"]):
        return None
    X, y = j[F.columns].values, j["_y"].values
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1
    Z = (X - mu) / sd
    lam = float(c["ridge"]) * len(Z)
    A = Z.T @ Z + lam * np.eye(Z.shape[1])
    bz = np.linalg.solve(A, Z.T @ (y - y.mean()))
    b = bz / sd
    resid = (y - y.mean()) - Z @ bz
    r2 = 1 - resid.var() / y.var() if y.var() > 0 else None
    return {"b": {k: float(v) for k, v in zip(F.columns, b)}, "r2": float(r2) if r2 is not None else None,
            "sd": float(resid.std() * 100), "n": int(len(j))}


def universe_loadings(prices: pd.DataFrame, F: pd.DataFrame) -> Dict[str, Dict]:
    out = {}
    for col in prices.columns:
        s = str(col)
        if s.startswith("^") or "=" in s or s.endswith((".TW", ".TWO", ".HK")) or "-USD" in s:
            continue
        x = prices[col].dropna()
        if len(x) < 260:
            continue
        L = loadings(x.pct_change(fill_method=None), F)
        if L:
            out[s] = L
    return out


def build_public(h: pd.DataFrame, stock_close: Optional[pd.DataFrame] = None) -> Dict:
    """Everything the pages need (no holdings): factor list, covariance, recent factor returns, per-symbol loadings."""
    F = factor_returns(h)
    if F.empty or len(F) < 300:
        return {"available": False}
    c = cfg()
    frames = [h] + ([stock_close] if stock_close is not None and not stock_close.empty else [])
    allp = pd.concat(frames, axis=1)
    allp = allp.loc[:, ~allp.columns.duplicated()]
    L = universe_loadings(allp, F)
    cov = F.dropna().iloc[-int(c["cov_days"]):].cov()
    last = F.dropna().iloc[-1]
    wk = (1 + F.dropna().iloc[-5:]).prod() - 1
    wk["rate"] = F["rate"].dropna().iloc[-5:].sum() if "rate" in F else None
    keys = list(F.columns)
    return {"available": True, "asof": F.dropna().index[-1].strftime("%Y-%m-%d"), "keys": keys,
            "labels": {k: LAB[k] for k in keys}, "cov": [[float(cov.loc[a, b]) for b in keys] for a in keys],
            "today": {k: float(last[k]) for k in keys}, "week": {k: (float(wk[k]) if wk[k] == wk[k] else None) for k in keys},
            "sym": {s: [round(v["b"][k], 4) for k in keys] + [round(v["r2"] or 0, 3), round(v["sd"], 3)] for s, v in L.items()},
            "n_sym": len(L)}


# ------------------------------------------------------------------ portfolio maths (also mirrored in the page JS)
def portfolio(weights: Dict[str, float], pub: Dict, actual_today: Optional[float] = None) -> Dict:
    """weights: {sym: fraction of the stock portfolio}.  Uses the loadings in pub["sym"]."""
    keys = pub["keys"]
    nK = len(keys)
    cov = np.array(pub["cov"])
    X = np.zeros(nK)
    spec_var, covered, missing = 0.0, 0.0, []
    for s, w in weights.items():
        row = pub["sym"].get(s) or pub["sym"].get(s.replace(".", "-"))
        if not row:
            missing.append(s)
            continue
        X += w * np.array(row[:nK])
        spec_var += (w * row[nK + 1] / 100) ** 2
        covered += w
    if covered > 0:                                     # exposures of the covered part, not shrunk by uncovered holdings
        X, spec_var = X / covered, spec_var / covered ** 2
    fvar = float(X @ cov @ X)
    tot = fvar + spec_var
    contrib = {k: float(X[i] * (cov @ X)[i] / tot) for i, k in enumerate(keys)} if tot > 0 else {}
    today = {k: float(X[i] * pub["today"][k]) for i, k in enumerate(keys)}
    out = {"exposure": {k: float(X[i]) for i, k in enumerate(keys)}, "covered": covered, "missing": missing,
           "vol_ann": math.sqrt(tot * 252) * 100 if tot > 0 else None, "factor_share": fvar / tot if tot > 0 else None,
           "risk_contrib": contrib, "today": today, "explained": sum(today.values())}
    if actual_today is not None:
        out["specific_today"] = actual_today - out["explained"]
    return out


def headline(p: Dict, pub: Dict, bench_today: Optional[float] = None) -> List[str]:
    """Plain-language lines: biggest exposures vs the market, biggest risk sources, today's drivers."""
    L = []
    ex = p["exposure"]
    act = {k: v - (1.0 if k == "mkt" else 0.0) for k, v in ex.items()}
    tops = sorted((k for k in act if k != "mkt"), key=lambda k: -abs(act[k]))[:3]
    L.append("相對大盤最大的曝險：" + "、".join(f"{LAB[k][0]} {ex[k]:+.2f}" for k in tops) + f"（市場 β {ex.get('mkt', 0):.2f}）")
    rc = sorted(p["risk_contrib"].items(), key=lambda kv: -kv[1])[:3]
    if rc:
        L.append("風險主要來自：" + "、".join(f"{LAB[k][0]} {v * 100:.0f}%" for k, v in rc)
                 + f"；個股自身 {(1 - (p['factor_share'] or 0)) * 100:.0f}%")
    td = sorted(p["today"].items(), key=lambda kv: -abs(kv[1]))[:3]
    L.append(f"因子日（{pub.get('asof', '—')}）的影響：" + "、".join(f"{LAB[k][0]} {v * 100:+.2f}%" for k, v in td)
             + (f"；個股自身 {p['specific_today'] * 100:+.2f}%" if p.get("specific_today") is not None else ""))
    return L
