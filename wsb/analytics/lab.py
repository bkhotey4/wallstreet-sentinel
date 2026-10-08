"""Feature lab: does a candidate indicator REALLY make the crash forecast better?

Every candidate (breadth, VIX term slope, credit momentum, equal-weight vs cap-weight, ...) is added to the SSI
in a logistic model and judged out-of-sample with a yearly expanding walk-forward (with an embargo of `days`
so labels never leak).  A feature is adopted only when it improves AUC by a clear margin AND in most test years;
otherwise it is dropped.  The adopted set forms an 'enhanced' model whose probabilities are shown with a
reliability (calibration) table: when it says 30%, how often did 30% happen?

Pure numpy / pandas (no scikit-learn).  Caveat (reported in the output): features are chosen on the same
history they are tested on, so the reported out-of-sample gain is slightly optimistic."""
from __future__ import annotations

import time
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS
from .crash_odds import forward_min_return
from .shock import auc

CFG = SETTINGS.get("lab", {})
SECTORS = ["XLK", "XLC", "XLY", "XLP", "XLE", "XLV", "XLI", "XLU", "XLB", "XLRE"]


# ---------------------------------------------------------------- logistic regression
def _sig(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def fit_logit(X: np.ndarray, y: np.ndarray, l2: float = 5.0, iters: int = 30) -> np.ndarray:
    """Ridge-penalised logistic regression by Newton / IRLS.  X must NOT contain the intercept column."""
    n, k = X.shape
    A = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(k + 1)
    w[0] = np.log(max(y.mean(), 1e-4) / max(1 - y.mean(), 1e-4))
    pen = np.eye(k + 1) * l2
    pen[0, 0] = 0.0
    for _ in range(iters):
        p = _sig(A @ w)
        g = A.T @ (p - y) + pen @ w
        W = p * (1 - p) + 1e-9
        H = A.T @ (A * W[:, None]) + pen
        step = np.linalg.solve(H, g)
        w -= step
        if np.max(np.abs(step)) < 1e-7:
            break
    return w


def predict(w: np.ndarray, X: np.ndarray) -> np.ndarray:
    return _sig(w[0] + X @ w[1:])


# ---------------------------------------------------------------- candidate features (all point-in-time)
def _z(s: pd.Series, win: int = 756) -> pd.Series:
    m, sd = s.rolling(win, min_periods=252).mean(), s.rolling(win, min_periods=252).std()
    return ((s - m) / sd.replace(0, np.nan)).clip(-4, 4)


def _ret(h: pd.DataFrame, t: str, n: int) -> Optional[pd.Series]:
    return h[t].ffill().pct_change(n, fill_method=None) if t in h.columns else None


def candidates(h: pd.DataFrame) -> Dict[str, Dict]:
    """name -> {'label', 'series'}.  Only features whose inputs exist are returned."""
    out: Dict[str, Dict] = {}

    def add(name, label, s):
        if s is not None and s.notna().sum() > 1000:
            out[name] = {"label": label, "series": s.replace([np.inf, -np.inf], np.nan)}

    c = h.get("^GSPC")
    if "^VIX" in h and "^VIX3M" in h:
        add("vix_term", "VIX 期限結構（VIX/VIX3M，>1=倒掛）", h["^VIX"] / h["^VIX3M"])
    if "^VVIX" in h:
        add("vvix", "VVIX（波動率的波動率）", h["^VVIX"])
    if "^SKEW" in h:
        add("skew", "SKEW 尾部風險", h["^SKEW"])
    if "^MOVE" in h:
        add("move", "MOVE 美債波動率", h["^MOVE"])
    secs = [t for t in SECTORS if t in h.columns]
    if len(secs) >= 5:
        above = pd.concat([(h[t] > h[t].rolling(200, min_periods=150).mean()).where(h[t].notna()) for t in secs], axis=1)
        add("breadth200", "市場廣度（板塊站上200日線比例，低=差）", -above.mean(axis=1))
    if "RSP" in h and c is not None:
        add("narrow", "漲勢集中度（等權重落後市值加權，60日）", -(h["RSP"].ffill().pct_change(60, fill_method=None) - c.ffill().pct_change(60, fill_method=None)))
    if "HYG" in h and "IEF" in h:
        add("credit_mom", "信用動能（HYG 相對 IEF 20日，低=差）", -(h["HYG"].ffill().pct_change(20, fill_method=None) - h["IEF"].ffill().pct_change(20, fill_method=None)))
    if "KRE" in h and "XLF" in h:
        add("bank_rel", "區域銀行相對金融股（20日，低=差）", -(h["KRE"].ffill().pct_change(20, fill_method=None) - h["XLF"].ffill().pct_change(20, fill_method=None)))
    if "DX-Y.NYB" in h:
        add("dxy_mom", "美元動能（20日）", h["DX-Y.NYB"].ffill().pct_change(20, fill_method=None))
    if "HG=F" in h and "GC=F" in h:
        add("copper_gold", "銅金比（60日，低=差）", -(h["HG=F"].ffill().pct_change(60, fill_method=None) - h["GC=F"].ffill().pct_change(60, fill_method=None)))
    if c is not None:
        r = np.log(c).diff()
        add("rvol", "標普實現波動率（20日／1年均值）", r.rolling(20).std() / r.rolling(252, min_periods=120).std())
        add("dist_ma200", "標普距200日線（低=差）", -(c / c.rolling(200, min_periods=150).mean() - 1))
        add("dd_now", "標普目前回檔幅度", 1 - c / c.rolling(252, min_periods=120).max())
    return out


# ---------------------------------------------------------------- walk-forward
def _labels(close: pd.Series, days: int, dd: float):
    fmr = forward_min_return(close, days)
    valid = fmr.notna()
    return ((fmr <= -dd) & valid).astype(float), valid


def walk_forward_logit(F: pd.DataFrame, hit: pd.Series, valid: pd.Series, days: int, min_train: int = 756,
                       l2: float = 5.0) -> Dict:
    """Yearly expanding-window OOS predictions of a logistic model on the columns of F.  Returns per-year AUC too."""
    D = F.join(hit.rename("_y")).join(valid.rename("_v")).dropna()
    D = D[D["_v"].astype(bool)]
    cols = list(F.columns)
    P, Y, YR, B, per_year = [], [], [], [], {}
    cal = hit.index                                   # trading calendar of the labels
    for yr in sorted(set(D.index.year)):
        test = D[D.index.year == yr]
        # embargo = `days` TRADING rows before the first test row (labels look `days` rows ahead)
        cutoff = cal[max(int(cal.searchsorted(test.index[0])) - days, 0)]
        train = D[D.index < cutoff]
        if len(train) < min_train or len(test) < 40 or train["_y"].sum() < 20:
            continue
        w = fit_logit(train[cols].values, train["_y"].values, l2)
        p = predict(w, test[cols].values)
        P.append(p)
        Y.append(test["_y"].values)
        YR.append(np.full(len(test), yr))
        B.append(np.full(len(test), float(train["_y"].mean())))
        per_year[yr] = (p, test["_y"].values)
    if not P:
        return {"n": 0}
    p, y, yr, b0 = np.concatenate(P), np.concatenate(Y), np.concatenate(YR), np.concatenate(B)
    bs, bs0 = float(np.mean((p - y) ** 2)), float(np.mean((b0 - y) ** 2))
    return {"n": int(len(y)), "auc": auc(pd.Series(p), pd.Series(y)), "brier": bs,
            "skill": float(1 - bs / bs0) if bs0 > 0 else None, "p": p, "y": y, "yr": yr,
            "year_auc": {int(k): auc(pd.Series(v[0]), pd.Series(v[1])) for k, v in per_year.items()}}


def isotonic(p: np.ndarray, y: np.ndarray, max_pts: int = 400):
    """Pool-adjacent-violators: monotone map from a raw probability to the frequency actually observed."""
    up, inv = np.unique(p, return_inverse=True)
    cnt = np.bincount(inv).astype(float)
    mean = np.bincount(inv, weights=y.astype(float)) / cnt
    vals, wts, xs = [], [], []
    for xi, vi, wi in zip(up, mean, cnt):
        vals.append(vi); wts.append(wi); xs.append(xi)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            w = wts[-2] + wts[-1]
            v = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / w
            vals[-2:], wts[-2:], xs[-2:] = [v], [w], [xs[-1]]
    xs, vals = np.array(xs), np.array(vals)
    if len(xs) > max_pts:
        sel = np.linspace(0, len(xs) - 1, max_pts).astype(int)
        xs, vals = xs[sel], vals[sel]
    return xs, vals


def apply_iso(cal, p):
    return np.interp(p, cal[0], cal[1])


def _calibration(p: np.ndarray, y: np.ndarray, edges=(0, .05, .10, .20, .30, .45, 1.01)) -> List[Dict]:
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum() >= 30:
            out.append({"lo": lo, "hi": min(hi, 1.0), "pred": float(p[m].mean() * 100), "actual": float(y[m].mean() * 100),
                        "n": int(m.sum())})
    return out


def run_horizon(h: pd.DataFrame, ssi: pd.Series, close: pd.Series, days: int, dd: float,
                cands: Optional[Dict] = None) -> Dict:
    min_gain = float(CFG.get("min_auc_gain", 0.02))
    min_years = float(CFG.get("min_years_improved", 0.6))
    max_feat = int(CFG.get("max_features", 3))
    hit, valid = _labels(close.dropna(), days, dd)
    cands = cands if cands is not None else candidates(h)
    Z = {k: _z(v["series"]) for k, v in cands.items()}
    base_F = pd.DataFrame({"ssi": (ssi - 50) / 20.0})
    base_F = base_F.reindex(hit.index).ffill(limit=5)
    base = walk_forward_logit(base_F, hit, valid, days)
    out: Dict = {"days": days, "drawdown_pct": dd * 100, "baseline": None, "features": [], "adopted": [], "ensemble": None,
                 "calibration": [], "now": None}
    if not base.get("n") or base.get("auc") is None:
        return out
    out["baseline"] = {"auc": base["auc"], "skill": base["skill"], "n": base["n"]}
    base_full = base
    feats = []
    def same_rows_base(mask):
        b = walk_forward_logit(base_F[mask], hit, valid, days)
        return b if b.get("n") and b.get("auc") is not None else None

    for k, v in cands.items():
        zk = Z[k].reindex(base_F.index)
        F = base_F.join(zk.rename(k))
        r = walk_forward_logit(F, hit, valid, days)
        if not r.get("n") or r.get("auc") is None:
            continue
        base = same_rows_base(zk.notna()) or base
        common = [y for y in r["year_auc"] if y in base["year_auc"] and r["year_auc"][y] is not None and base["year_auc"][y] is not None]
        better = sum(r["year_auc"][y] > base["year_auc"][y] for y in common)
        d_auc = r["auc"] - base["auc"]
        frac = better / len(common) if common else 0.0
        feats.append({"name": k, "label": cands[k]["label"], "auc": r["auc"], "d_auc": d_auc,
                      "skill": r["skill"], "d_skill": (r["skill"] or 0) - (base["skill"] or 0),
                      "years": len(common), "years_better": better, "frac_better": frac,
                      "adopt": bool(d_auc >= min_gain and frac >= min_years and len(common) >= 8)})
    # multiple-testing guard: the same features, circularly time-shifted (relationship to the label destroyed, serial
    # correlation kept).  A real feature must beat the BEST of these placebo results, not just a fixed AUC margin.
    nulls = []
    for k in cands:
        zs = Z[k].reindex(base_F.index)
        for off in (0.17, 0.38, 0.59, 0.81):
            sh = pd.Series(np.roll(zs.values, int(off * len(zs))), index=zs.index, name=k)
            r = walk_forward_logit(base_F.join(sh), hit, valid, days)
            bk = same_rows_base(sh.notna())
            if r.get("auc") is not None and bk:
                nulls.append(r["auc"] - bk["auc"])
    base = base_full
    null_max = float(max(nulls)) if nulls else 0.0
    out["null_max_d_auc"] = null_max
    for f in feats:
        f["beats_placebo"] = bool(f["d_auc"] > null_max)
        f["adopt"] = bool(f["adopt"] and f["beats_placebo"])
    feats.sort(key=lambda f: -f["d_auc"])
    out["features"] = feats
    adopted = [f["name"] for f in feats if f["adopt"]][:max_feat]
    out["adopted"] = adopted
    if adopted:
        F = base_F.join(pd.concat([Z[k].rename(k) for k in adopted], axis=1).reindex(base_F.index))
        ens = walk_forward_logit(F, hit, valid, days)
        base = same_rows_base(F.notna().all(axis=1)) or base_full
        if ens.get("n") and ens.get("auc") is not None:
            out["ensemble"] = {"auc": ens["auc"], "d_auc": ens["auc"] - base["auc"], "skill": ens["skill"],
                               "d_skill": (ens["skill"] or 0) - (base["skill"] or 0), "n": ens["n"]}
            out["ensemble"]["accepted"] = bool(out["ensemble"]["d_auc"] >= min_gain and out["ensemble"]["d_skill"] > 0
                                                and (out["ensemble"]["skill"] or 0) > 0)
            out["calibration"] = _calibration(ens["p"], ens["y"])
            cal = isotonic(ens["p"], ens["y"])
            D = F.join(hit.rename("_y")).join(valid.rename("_v")).dropna()
            D = D[D["_v"].astype(bool)]
            w = fit_logit(D[list(F.columns)].values, D["_y"].values)
            last = F.iloc[-1].fillna(0.0).values.reshape(1, -1)
            wb = fit_logit(D[["ssi"]].values, D["_y"].values)
            raw = float(predict(w, last)[0])
            out["now"] = {"p_enh": raw * 100, "p_enh_cal": float(apply_iso(cal, raw) * 100),
                          "p_base": float(predict(wb, base_F.iloc[[-1]].fillna(0.0).values)[0] * 100),
                          "drivers": sorted([(c, float(Z[c].iloc[-1]) if pd.notna(Z[c].iloc[-1]) else 0.0, float(w[1 + i + 1]))
                                             for i, c in enumerate(adopted)], key=lambda t: -abs(t[1] * t[2]))}
    else:
        D = base_F.join(hit.rename("_y")).join(valid.rename("_v")).dropna()
        D = D[D["_v"].astype(bool)]
        wb = fit_logit(D[["ssi"]].values, D["_y"].values)
        out["calibration"] = _calibration(base["p"], base["y"])
        cal = isotonic(base["p"], base["y"])
        rawb = float(predict(wb, base_F.iloc[[-1]].fillna(0.0).values)[0])
        out["now"] = {"p_enh": None, "p_enh_cal": None, "p_base": rawb * 100, "p_base_cal": float(apply_iso(cal, rawb) * 100),
                      "drivers": []}
    return out


def run(history: pd.DataFrame, ssi: pd.Series, close: pd.Series) -> Dict:
    """Full lab report for each configured crash horizon."""
    t0 = time.time()
    hz = SETTINGS.get("crash_odds", {}).get("horizons", [])
    # features are built on the benchmark's trading days: the shared history also has crypto weekend rows, which
    # made every rolling window NaN (and "20 days" mean ~14 trading days)
    history = history.loc[history.index.isin(close.dropna().index)]
    cands = candidates(history)
    reps = [run_horizon(history, ssi, close, int(x["days"]), float(x["drawdown"]), cands) for x in hz]
    return {"horizons": reps, "n_candidates": len(cands), "seconds": time.time() - t0, "ts": time.time(),
            "caveat": "特徵選擇與檢驗用同一段歷史，樣本外增益可能略為樂觀。"}
