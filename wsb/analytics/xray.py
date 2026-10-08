"""Portfolio X-ray: how many INDEPENDENT bets do you really hold, what happens in custom shocks, where are the
volatility-based stops, which positions face an event soon, and how much should exposure shrink when volatility rises.

All pure functions on price history + the portfolio snapshot (no network)."""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

CFG = SETTINGS.get("xray", {})
DEFAULT_SCENARIOS = [
    {"name": "利率 +100bp", "shocks": {"rate": 1.0}},
    {"name": "美元 +10%", "shocks": {"usd": 0.10}},
    {"name": "標普 −20%", "shocks": {"mkt": -0.20}},
    {"name": "半導體族群額外 −20%（大盤持平）", "shocks": {"semi": -0.20}},
    {"name": "滯脹：利率+1%、美元+5%、股−10%", "shocks": {"rate": 1.0, "usd": 0.05, "mkt": -0.10}},
]


def _rets(market, sym: str, n: int = 504) -> pd.Series:
    s = market.series(sym)
    s = s[s > 0]
    return np.log(s).diff().dropna().iloc[-n:]


def _positions(portfolio: Dict) -> List[Dict]:
    return [p for p in (portfolio or {}).get("positions", []) if p.get("value_usd")] if portfolio and not portfolio.get("error") else []


# ---------------------------------------------------------------- 1) diversification
def diversification(market, portfolio: Dict, window: int = 252) -> Dict:
    pos = _positions(portfolio)
    cols = {}
    for p in pos:
        r = _rets(market, p["sym"], window)
        if len(r) >= 120:
            cols[p["sym"]] = r
    if len(cols) < 2:
        return {"available": False, "n_positions": len(pos)}
    R = pd.concat(cols, axis=1).dropna()
    if len(R) < 100:
        return {"available": False, "n_positions": len(pos)}
    syms = list(R.columns)
    w = np.array([next(p["value_usd"] for p in pos if p["sym"] == s) for s in syms], dtype=float)
    w = w / w.sum()
    cov = np.cov(R.values.T)
    cov = np.atleast_2d(cov)
    sig = np.sqrt(np.diag(cov))
    port_var = float(w @ cov @ w)
    corr = np.corrcoef(R.values.T)
    n = len(syms)
    off = ~np.eye(n, dtype=bool)
    ww = np.outer(w, w)
    avg_corr = float((ww * corr)[off].sum() / ww[off].sum())
    lam, V = np.linalg.eigh(cov)
    lam = np.clip(lam, 0, None)
    y = V.T @ w
    contrib = (y ** 2) * lam
    pk = contrib / contrib.sum() if contrib.sum() > 0 else np.ones(n) / n
    enb = float(np.exp(-(pk[pk > 0] * np.log(pk[pk > 0])).sum()))
    eff_w = float(1 / (w ** 2).sum())
    # clusters: connected components with correlation >= thr
    thr = float(CFG.get("cluster_corr", 0.70))
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            if corr[i, j] >= thr:
                parent[find(i)] = find(j)
    groups: Dict[int, List[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    clusters = []
    for g in groups.values():
        if len(g) < 2:
            continue
        sub = corr[np.ix_(g, g)]
        clusters.append({"members": [syms[i] for i in g], "weight": float(w[g].sum() * 100),
                         "avg_corr": float(sub[~np.eye(len(g), dtype=bool)].mean())})
    clusters.sort(key=lambda c: -c["weight"])
    return {"available": True, "n_positions": len(pos), "n_used": n, "eff_n_weight": eff_w, "enb": enb,
            "avg_corr": avg_corr, "div_ratio": float((w * sig).sum() / math.sqrt(port_var)) if port_var > 0 else None,
            "clusters": clusters, "cluster_thr": thr, "window": len(R)}


# ---------------------------------------------------------------- 2) factor scenarios
def _factors(market, n: int = 504) -> Optional[pd.DataFrame]:
    mk = _rets(market, "^GSPC", n)
    if len(mk) < 200:
        return None
    F = pd.DataFrame({"mkt": mk})
    tnx = market.series("^TNX")
    if len(tnx) > 250:
        sc = 0.1 if float(tnx.iloc[-1]) > 20 else 1.0            # legacy quote scale (yield x10)
        F["rate"] = (tnx * sc).diff()
    dx = _rets(market, "DX-Y.NYB", n)
    if len(dx) > 250:
        F["usd"] = dx
    sm = _rets(market, "SMH", n)
    if len(sm) > 250:
        j = pd.concat([sm.rename("s"), mk.rename("m")], axis=1).dropna()
        b = float(np.cov(j["s"], j["m"])[0, 1] / j["m"].var())
        F["semi"] = (j["s"] - b * j["m"]).reindex(F.index)          # semis return orthogonal to the market
    return F.dropna(how="all")


def betas(market, sym: str, F: pd.DataFrame, n: int = 504, fallback_beta: Optional[float] = None) -> Optional[Dict]:
    r = _rets(market, sym, n)
    j = pd.concat([r.rename("y"), F], axis=1).dropna()
    if len(j) < 150:
        if fallback_beta is None:
            return None
        return {"b": {"mkt": fallback_beta}, "r2": None, "n": len(j), "proxy": True}
    X = j[F.columns].values
    y = j["y"].values
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1
    Z = (X - mu) / sd
    lam = 2.0                                               # light ridge: stabilises collinear factors
    A = np.hstack([np.ones((len(Z), 1)), Z])
    pen = np.eye(A.shape[1]) * lam
    pen[0, 0] = 0
    coef = np.linalg.solve(A.T @ A + pen, A.T @ y)
    b = coef[1:] / sd                                       # back to natural units
    pred = A @ coef
    r2 = float(1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum())
    return {"b": dict(zip(F.columns, b.tolist())), "r2": r2, "n": len(j), "proxy": False}


def scenarios(market, portfolio: Dict) -> Dict:
    pos = _positions(portfolio)
    F = _factors(market)
    if F is None or not pos:
        return {"available": False}
    total = sum(p["value_usd"] for p in pos)
    est = {}
    for p in pos:
        e = betas(market, p["sym"], F, fallback_beta=p.get("beta"))
        if e:
            est[p["sym"]] = e
    out = []
    for sc in CFG.get("scenarios", DEFAULT_SCENARIOS):
        rows = []
        for p in pos:
            e = est.get(p["sym"])
            if not e:
                continue
            ret = sum(e["b"].get(f, 0.0) * x for f, x in sc["shocks"].items())
            rows.append({"sym": p["sym"], "ret_pct": ret * 100, "usd": ret * p["value_usd"]})
        pnl = sum(r["usd"] for r in rows)
        rows.sort(key=lambda r: r["usd"])
        out.append({"name": sc["name"], "pnl_usd": pnl, "pnl_pct": pnl / total * 100 if total else 0.0,
                    "worst": rows[:3], "shocks": sc["shocks"]})
    wr2 = [(est[p["sym"]]["r2"], p["value_usd"]) for p in pos if p["sym"] in est and est[p["sym"]]["r2"] is not None]
    r2 = sum(a * b for a, b in wr2) / sum(b for _, b in wr2) if wr2 else None
    return {"available": True, "scenarios": out, "r2": r2, "factors": list(F.columns), "total": total,
            "n_proxy": sum(1 for e in est.values() if e.get("proxy"))}


# ---------------------------------------------------------------- 3) volatility stops
def stops(market, portfolio: Dict, mult: Optional[float] = None, lookback: int = 22, atr_n: int = 14) -> List[Dict]:
    mult = float(mult if mult is not None else CFG.get("stop_atr_mult", 3.0))
    out = []
    for p in _positions(portfolio):
        s = market.series(p["sym"])
        if len(s) < lookback + atr_n + 2:
            continue
        hi = float(s.iloc[-lookback:].max())
        atr = float(s.diff().abs().iloc[-atr_n:].mean())
        stop = hi - mult * atr
        px = float(p.get("price") or s.iloc[-1])
        out.append({"sym": p["sym"], "price": px, "high": hi, "stop": stop, "dist_pct": (px / stop - 1) * 100,
                    "breached": px < stop, "weight": float(p.get("weight") or 0), "asof": str(s.index[-1])[:10]})
    out.sort(key=lambda r: r["dist_pct"])
    return out


# ---------------------------------------------------------------- 4) event exposure
def event_exposure(portfolio: Dict, events: List[Dict]) -> Dict:
    wmap = {p["sym"]: float(p.get("weight") or 0) for p in _positions(portfolio)}
    rows = [{"date": e["date"], "sym": e["ticker"], "weight": wmap[e["ticker"]]} for e in events
            if e.get("type") == "earnings" and e.get("ticker") in wmap]
    rows.sort(key=lambda r: r["date"])
    macro = [e for e in events if e.get("type") in ("fomc", "macro", "liquidity")]
    return {"earnings": rows, "earnings_weight": sum(r["weight"] for r in rows), "macro": macro[:8]}


# ---------------------------------------------------------------- 5) volatility targeting
def vol_target(market, portfolio: Dict, target_pct: Optional[float] = None) -> Dict:
    pos = _positions(portfolio)
    cols = {p["sym"]: _rets(market, p["sym"], 260) for p in pos}
    cols = {k: v for k, v in cols.items() if len(v) >= 60}
    if not cols:
        return {"available": False}
    R = pd.concat(cols, axis=1).dropna()
    if len(R) < 60:
        return {"available": False}
    w = np.array([next(p["value_usd"] for p in pos if p["sym"] == s) for s in R.columns], dtype=float)
    total = float(sum(p["value_usd"] for p in pos))
    w = w / w.sum()
    pr = pd.Series(R.values @ w, index=R.index)
    ann = math.sqrt(252)
    v20, v60 = float(pr.iloc[-20:].std() * ann * 100), float(pr.iloc[-60:].std() * ann * 100)
    v252 = float(pr.std() * ann * 100)
    tgt = float(target_pct if target_pct is not None else CFG.get("vol_target_pct", 25))
    cur = max(v20, v60)                                      # be conservative: the higher of short / medium windows
    scale = min(1.0, tgt / cur) if cur > 0 else 1.0
    return {"available": True, "vol20": v20, "vol60": v60, "vol252": v252, "target": tgt, "current": cur,
            "scale": scale, "trim_pct": (1 - scale) * 100, "trim_usd": total * (1 - scale)}


def build(engine) -> Dict:
    m, pf = engine.market, engine.portfolio
    if not pf or pf.get("error"):
        return {"available": False}
    return {"available": True, "div": diversification(m, pf), "scen": scenarios(m, pf), "stops": stops(m, pf),
            "events": event_exposure(pf, engine.calendar.upcoming(14)), "vol": vol_target(m, pf)}
