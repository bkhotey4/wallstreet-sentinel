"""個股台美連動 — which US stock (or index) moves each Taiwan stock the next morning, found from data and checked
out of sample, instead of a hand-written supply-chain map.

Pairing is the same as mood._link: each Taiwan session t gets ALL US sessions since the previous Taiwan session,
compounded (Taiwan sessions with no US session in between are dropped).  For every Taiwan stock in the site universe:
  1. pick the US partner with the highest correlation on the TRAINING part (everything before the last 250 pairs);
  2. judge it only on the last 250 pairs it was not picked on: correlation, out-of-sample R² of "beta × last night"
     against predicting 0, and whether it explains more than the plain 費城半導體 index does;
  3. last night's US move × the training beta = the implied Taiwan move, and the actual one once Taiwan has traded.
Also a walk-forward record for the TAIEX open estimate (rolling one-year beta, never using the day being predicted).
Descriptive statistics, not a forecast or advice."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

TEST = 250
MIN_TRAIN = 150
KEEP_CORR = 0.25
INDEX = (("^SOX", "費城半導體"), ("^NDX", "那斯達克 100"), ("^GSPC", "標普 500"))


def paired(us: pd.DataFrame, tw_index: pd.DatetimeIndex) -> pd.DataFrame:
    """US daily % changes compounded over each Taiwan gap, indexed by the Taiwan session they lead into."""
    us = us.sort_index()
    ui = us.index
    lg = np.log1p(us.fillna(0.0).values / 100)
    cum = np.vstack([np.zeros((1, us.shape[1])), np.cumsum(lg, axis=0)])
    obs = np.vstack([np.zeros((1, us.shape[1])), np.cumsum(us.notna().values, axis=0)])
    ti = tw_index.sort_values()
    lo = ui.searchsorted(ti[:-1], side="left")
    hi = ui.searchsorted(ti[1:], side="left")
    ok = hi > lo
    x = np.expm1(cum[hi] - cum[lo]) * 100
    x[(obs[hi] - obs[lo]) == 0] = np.nan                      # the stock did not trade in that gap
    return pd.DataFrame(x[ok], index=ti[1:][ok], columns=us.columns)


def _corr(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Column-wise correlation of every x column with every y column, pairwise-complete."""
    out = np.full((x.shape[1], y.shape[1]), np.nan)
    for j in range(y.shape[1]):
        m = ~np.isnan(x) & ~np.isnan(y[:, [j]])
        n = m.sum(axis=0)
        xs, ys = np.where(m, x, 0.0), np.where(m, y[:, [j]], 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            mx, my = xs.sum(0) / n, ys.sum(0) / n
            cov = (xs * ys).sum(0) / n - mx * my
            vx = (xs * xs).sum(0) / n - mx * mx
            vy = (ys * ys).sum(0) / n - my * my
            c = cov / np.sqrt(vx * vy)
        c[n < MIN_TRAIN * 0.8] = np.nan
        out[:, j] = c
    return out


def _fit(x: pd.Series, y: pd.Series) -> Optional[Dict]:
    xy = pd.concat([x, y], axis=1).dropna()
    if len(xy) < 60 or xy.iloc[:, 0].var() == 0:
        return None
    return {"beta": float(np.cov(xy.iloc[:, 0], xy.iloc[:, 1])[0, 1] / xy.iloc[:, 0].var()), "corr": float(xy.corr().iloc[0, 1]), "n": len(xy)}


def _oos(beta: float, x: pd.Series, y: pd.Series) -> Optional[Dict]:
    xy = pd.concat([x, y], axis=1).dropna()
    if len(xy) < 60:
        return None
    a, b = xy.iloc[:, 0].values, xy.iloc[:, 1].values
    sse, sse0 = float(((b - beta * a) ** 2).sum()), float((b ** 2).sum())
    big = np.abs(a) >= np.nanstd(a)
    return {"corr": float(np.corrcoef(a, b)[0, 1]), "r2": 1 - sse / sse0 if sse0 else None, "n": len(xy),
            "same": float((np.sign(a[big]) == np.sign(b[big])).mean() * 100) if big.sum() >= 15 else None}


def stock_link(sp, names: Dict[str, tuple], h: Optional[pd.DataFrame] = None) -> Dict:
    if sp is None or getattr(sp, "close", pd.DataFrame()).empty:
        return {"available": False}
    cl = sp.close
    tw_syms = [s for s in cl.columns if names.get(s, ("", "", ""))[2] == "tw" and cl[s].notna().sum() > MIN_TRAIN + TEST]
    us_syms = [s for s in cl.columns if names.get(s, ("", "", ""))[2] == "us" and cl[s].notna().sum() > MIN_TRAIN + TEST]
    if len(tw_syms) < 5 or len(us_syms) < 10:
        return {"available": False}
    tw = cl[tw_syms].dropna(how="all")
    tw = tw[tw.index.dayofweek < 5]
    tw_r = tw.pct_change(fill_method=None) * 100
    us_px = cl[us_syms]
    for t, _zh in INDEX:
        if h is not None and t in h.columns:
            us_px = us_px.join(h[t].rename(t), how="outer")
    us_px = us_px[us_px.index.dayofweek < 5].dropna(how="all")
    us_r = us_px.pct_change(fill_method=None) * 100
    x = paired(us_r.iloc[1:], tw_r.index)
    y = tw_r.reindex(x.index)
    if len(x) < MIN_TRAIN + TEST:
        return {"available": False}
    tr, te = slice(None, len(x) - TEST), slice(len(x) - TEST, None)
    c = _corr(x.iloc[tr].values, y.iloc[tr].values)
    sox = "^SOX" if "^SOX" in x.columns else None
    last_us = us_r.index[-1]
    tw_upto = tw_r.index[tw_r.index <= last_us]
    rows = []
    for j, s in enumerate(tw_syms):
        if np.all(np.isnan(c[:, j])):
            continue
        i = int(np.nanargmax(c[:, j]))
        p = x.columns[i]
        f = _fit(x[p].iloc[tr], y[s].iloc[tr])
        o = _oos(f["beta"], x[p].iloc[te], y[s].iloc[te]) if f else None
        if not f or not o:
            continue
        base = None
        if sox and p != sox:
            fb = _fit(x[sox].iloc[tr], y[s].iloc[tr])
            ob = _oos(fb["beta"], x[sox].iloc[te], y[s].iloc[te]) if fb else None
            base = ob["r2"] if ob else None
        since = us_r[p][us_r.index >= tw_upto[-1]].dropna() if len(tw_upto) else us_r[p].iloc[-1:]
        now = float((np.prod(1 + since.values / 100) - 1) * 100) if len(since) else None
        after = tw_r[s][tw_r.index > last_us].dropna()
        nm = names.get(s, (s, s, "tw", ""))
        pn = names.get(p, (dict(INDEX).get(p, p), p, "us", ""))
        rows.append({"sym": s, "name": nm[0], "theme": nm[3], "p": p, "p_name": pn[0], "train_corr": f["corr"], "beta": f["beta"],
                     "corr": o["corr"], "r2": o["r2"], "same": o["same"], "n": o["n"], "r2_sox": base,
                     "us": now, "us_d": str(last_us.date()), "implied": f["beta"] * now if now is not None else None,
                     "tw": float(after.iloc[0]) if len(after) else None, "tw_d": str(after.index[0].date()) if len(after) else None,
                     "ok": o["corr"] >= KEEP_CORR and (o["r2"] or 0) > 0})
    rows.sort(key=lambda r: -r["corr"])
    good = [r for r in rows if r["ok"]]
    return {"available": bool(rows), "rows": rows, "n": len(rows), "n_ok": len(good),
            "n_beat_sox": sum(1 for r in good if r["r2_sox"] is not None and r["r2"] > r["r2_sox"]),
            "n_us": len(us_syms), "test": TEST, "from": str(x.index[0].date()), "split": str(x.index[len(x) - TEST].date()),
            "to": str(x.index[-1].date())}


def open_track(us: pd.Series, tw: pd.Series, win: int = 250, n: int = 500) -> Optional[Dict]:
    """Walk-forward record of beta × last night for the TAIEX: beta from the previous `win` pairs only."""
    us, tw = us.dropna(), tw.dropna()
    if len(tw) < win + 120:
        return None
    x = paired(us.pct_change().mul(100).to_frame("u").iloc[1:], tw.index)["u"]
    y = tw.pct_change().mul(100).reindex(x.index)
    xy = pd.concat([x, y], axis=1).dropna()
    xy.columns = ["x", "y"]
    cov = xy["x"].rolling(win).cov(xy["y"]).shift(1)
    var = xy["x"].rolling(win).var().shift(1)
    pred = (cov / var * xy["x"]).iloc[-n:]
    yy = xy["y"].iloc[-n:]
    m = pred.notna()
    pred, yy = pred[m], yy[m]
    if len(pred) < 120:
        return None
    big = pred.abs() >= 0.3
    return {"n": int(len(pred)), "mae": float((yy - pred).abs().mean()), "mae0": float(yy.abs().mean()),
            "hit": float((np.sign(pred[big]) == np.sign(yy[big])).mean() * 100) if big.sum() >= 30 else None, "n_big": int(big.sum()),
            "from": str(pred.index[0].date())}
