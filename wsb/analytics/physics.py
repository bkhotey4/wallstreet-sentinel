"""跨領域觀測站 — three ways other sciences look at a system before it breaks, run on free daily prices.

  aftershock   地震學 Omori law: after a big shock the rate of further large moves decays as K / (t + c)^p
               (Lillo & Mantegna 2003; Petersen, Wang, Havlin & Stanley 2010).  Fitted on S&P 500 days BEFORE
               `split` and checked on the days after it (out of sample).  Tells how long the "aftershock period"
               lasts and the odds of a ≥2 % day in the next 5 sessions; it cannot see the first shock coming.
  absorption   鳥群同步度 Absorption ratio (Kritzman, Li, Page & Rigobon 2011): share of the variance of the 9
               original sector SPDRs explained by the top 2 principal components (EWMA covariance, 500 days,
               half-life 250).  ΔAR = (15-day mean − 1-year mean) / 1-year std; ≥ 1 means everything is starting
               to move together, which the paper found precedes most large drawdowns.
  turbulence   市場亂流 Financial turbulence (Kritzman & Li 2010): Mahalanobis distance of today's cross-asset move
               (9 sectors, 10-year yield, gold, dollar, oil) from the trailing 3-year mean / covariance; 5-day mean
               vs its own expanding history.  Turbulence persists, so it describes the weather now, not tomorrow.

Every threshold uses data up to that day only.  Back-tests: a signal "episode" starts on the first day on after
≥ 20 days off; hit = S&P 500 falls ≥ dd % from that day within `horizon` trading days; the rest are listed as
false alarms; Wilson 95 % intervals.  Frequencies over overlapping days are not independent trials.  Not a forecast."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .crisis_track import wilson

SECTORS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
CROSS = SECTORS + ["^TNX", "GC=F", "DX-Y.NYB", "CL=F"]
CFG = {"main": 4.0, "after": 2.0, "maxlag": 250, "split": "1990-01-01", "next": 5,
       "ar_win": 500, "ar_hl": 250, "ar_k": 2, "dar": 1.0,
       "tb_win": 756, "tb_pct": 80.0, "horizon": 63, "dd": 10.0}
_CACHE: Dict = {}


# ---------------------------------------------------------------- back-test helpers
def fwd_drop(px: pd.Series, h: int) -> pd.Series:
    """Worst close in the next h days vs today, % (NaN where the window is not complete)."""
    fmin = px[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1)
    return (fmin / px - 1) * 100


def score(sig: pd.Series, px: pd.Series, h: int, dd: float) -> Dict:
    """Episodes of a boolean signal against S&P 500 falls; conditional vs base frequency."""
    j = pd.concat({"s": sig.astype(float), "p": px}, axis=1).dropna()
    s, p = j["s"].astype(bool), j["p"]
    drop = fwd_drop(p, h)
    ok = drop.notna()
    prior = s.shift(1, fill_value=False).rolling(20, min_periods=1).max().astype(bool)
    eps = []
    for d in s.index[s & ~prior]:
        if not ok.get(d, False):
            continue
        eps.append({"date": d.strftime("%Y-%m-%d"), "drop": float(drop[d]), "hit": bool(drop[d] <= -dd)})
    k = sum(e["hit"] for e in eps)
    cond, base = drop[ok & s], drop[ok]
    return {"episodes": eps, "n": len(eps), "hit": k, "ci": wilson(k, len(eps)),
            "cond": float((cond <= -dd).mean() * 100) if len(cond) else None, "cond_days": int(len(cond)),
            "base": float((base <= -dd).mean() * 100) if len(base) else None}


# ---------------------------------------------------------------- 地震學：餘震
BUCKETS = ((1, 5), (6, 20), (21, 60), (61, 250), (251, 10 ** 9))


def _bucket(t: int) -> int:
    return next(k for k, (a, b) in enumerate(BUCKETS) if a <= t <= b)


def omori_fit(r: pd.Series, main: float, after: float, maxlag: int) -> Optional[Dict]:
    """Excess rate of big days at lag t after each main shock over the 250 days before it, fitted as K / (t + c)^p."""
    a = (r.abs() >= after).to_numpy().astype(float)
    bg = pd.Series(a, index=r.index).shift(1).rolling(250, min_periods=200).mean().to_numpy()
    shocks = [i for i in np.flatnonzero((r.abs() >= main).to_numpy()) if np.isfinite(bg[i])]
    if len(shocks) < 8:
        return None
    ex, n = np.zeros(maxlag), np.zeros(maxlag)
    for i in shocks:
        seg = a[i + 1:i + 1 + maxlag]
        ex[:len(seg)] += seg - bg[i]
        n[:len(seg)] += 1
    ex = ex / np.maximum(n, 1)
    t = np.arange(1, maxlag + 1)
    m = (ex > 0) & (n > 0)
    if m.sum() < 20:
        return None
    best = None
    for c in (0.5, 1, 2, 3, 5, 8, 12, 20):
        p, lk = np.polyfit(np.log(t[m] + c), np.log(ex[m]), 1, w=np.sqrt(n[m]))
        err = float(np.mean((np.log(ex[m]) - (lk + p * np.log(t[m] + c))) ** 2))
        if best is None or err < best["err"]:
            best = {"c": c, "p": float(-p), "K": float(np.exp(lk)), "err": err}
    return {**best, "n_main": len(shocks)}


def aftershock(spx: pd.Series, c: Dict) -> Dict:
    """Odds of a >= after % day in the next `next` sessions, by days since the last >= main % day: frequencies from
    1950 up to `split` (in sample) and after it (out of sample).  Omori exponent p fitted on the same early sample."""
    spx = spx.dropna()
    spx = spx[spx > 0]
    if len(spx) < 252 * 30:
        return {"available": False}
    r = np.log(spx).diff().dropna() * 100
    split, start, nx = pd.Timestamp(c["split"]), pd.Timestamp("1950-01-01"), int(c["next"])
    big = (r.abs() >= c["after"]).to_numpy()
    shock = (r.abs() >= c["main"]).to_numpy()
    if not shock.any():
        return {"available": False}
    last, since = -10 ** 7, np.zeros(len(r), dtype=int)
    for i in range(len(r)):
        if shock[i]:
            last = i
        since[i] = i - last
    n = len(r)
    fut = np.array([big[i + 1:i + 1 + nx].any() if i + nx < n else False for i in range(n)])
    done = np.arange(n) + nx < n
    ix = r.index
    rows = []
    for a, b in BUCKETS:
        inb = (since >= a) & (since <= b) & done
        fit_m, oos_m = inb & (ix >= start) & (ix < split), inb & (ix >= split)
        rows.append({"band": f"{a}–{b} 天" if b < 10 ** 9 else f"{a} 天以上",
                     "fit": float(fut[fit_m].mean() * 100) if fit_m.sum() else None,
                     "oos": float(fut[oos_m].mean() * 100) if oos_m.sum() else None,
                     "n_fit": int(fit_m.sum()), "n_oos": int(oos_m.sum())})
    f = omori_fit(r[(ix >= start) & (ix < split)], c["main"], c["after"], int(c["maxlag"]))
    t_now = int(since[-1])
    cur = _bucket(max(t_now, 1))
    lastd = ix[n - 1 - t_now]
    rec = r.iloc[-20:]
    bg_now = float(big[-250:].mean())
    since_s = pd.Series(since, index=ix)
    return {"available": True, "_since": since_s, "rows": rows, "cur": cur, "days_since": t_now, "last_main": lastd.strftime("%Y-%m-%d"),
            "last_main_r": float(r[lastd]), "p_now": rows[cur]["oos"], "fit": f, "next": nx, "split": c["split"][:4],
            "main": c["main"], "after": c["after"], "bg_now": bg_now * 100, "p_bg": (1 - (1 - bg_now) ** nx) * 100,
            "recent_max": float(rec.abs().max()), "recent_max_d": rec.abs().idxmax().strftime("%Y-%m-%d"),
            "recent_big": int((rec.abs() >= c["after"]).sum())}


# ---------------------------------------------------------------- AI 記憶：相似日搜尋
FEAT_ZH = {"ret20": "標普 20 日漲跌", "ret63": "標普 3 個月漲跌", "dd": "離 52 週高點", "vol21": "標普 1 個月波動",
           "vix": "VIX 水準", "vix20": "VIX 1 個月變化", "tnx63": "10 年殖利率 3 個月變化", "usd63": "美元 3 個月變化",
           "oil63": "油價 3 個月變化", "gold63": "金價 3 個月變化"}


def features(hist: pd.DataFrame) -> pd.DataFrame:
    if "^GSPC" not in hist:
        return pd.DataFrame()
    g = hist["^GSPC"].dropna()
    g = g[g > 0]
    lr = np.log(g).diff()
    f = {"ret20": g.pct_change(20) * 100, "ret63": g.pct_change(63) * 100,
         "dd": (g / g.rolling(252, min_periods=120).max() - 1) * 100, "vol21": lr.rolling(21).std() * np.sqrt(252) * 100}
    if "^VIX" in hist:
        v = hist["^VIX"].dropna()
        v = v[v > 0]
        f["vix"] = np.log(v)
        f["vix20"] = np.log(v).diff(20)
    if "^TNX" in hist:
        f["tnx63"] = hist["^TNX"].dropna().diff(63)
    for k, col in (("usd63", "DX-Y.NYB"), ("oil63", "CL=F"), ("gold63", "GC=F")):
        if col in hist:
            x = hist[col].dropna()
            f[k] = np.log(x.where(x > 0)).diff(63) * 100
    return pd.DataFrame(f).reindex(g.index).ffill(limit=3).replace([np.inf, -np.inf], np.nan).dropna()


def neighbours(z: np.ndarray, q: np.ndarray, k: int, gap: int) -> List[int]:
    d = np.sqrt(((z - q) ** 2).sum(1))
    out: List[int] = []
    for j in np.argsort(d):
        if all(abs(int(j) - o) >= gap for o in out):
            out.append(int(j))
            if len(out) == k:
                break
    return out


def auc(score: np.ndarray, y: np.ndarray) -> Optional[float]:
    pos, neg = score[y], score[~y]
    if not len(pos) or not len(neg):
        return None
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())


def analog(hist: pd.DataFrame, c: Dict) -> Dict:
    """k nearest past days on 10 standardised market features (each day scaled by the days before it only);
    neighbours only among days whose outcome was already known, at least `gap` days apart."""
    F = features(hist)
    if len(F) < 2500 or F.shape[1] < 8:
        return {"available": False}
    g = hist["^GSPC"].reindex(F.index)
    h, dd, k, gap = int(c["horizon"]), float(c["dd"]), 20, 10
    drop = fwd_drop(g, h).to_numpy()
    fret = ((g.shift(-h) / g - 1) * 100).to_numpy()
    mu, sd = F.expanding(500).mean().shift(1), F.expanding(500).std().shift(1)
    Z = ((F - mu) / sd).clip(-5, 5).dropna()
    off = len(F) - len(Z)
    z, idx = Z.to_numpy(), Z.index
    drop, fret = drop[off:], fret[off:]
    pr, ys, bp = [], [], []
    for i in range(len(Z)):
        if idx[i] < pd.Timestamp("2008-01-01") or i % 5 or not np.isfinite(drop[i]):
            continue
        ce = i - h
        if ce < 1500:
            continue
        nb = neighbours(z[:ce], z[i], k, gap)
        pr.append(float(np.mean(drop[nb] <= -dd)))
        bp.append(float(np.mean(drop[:ce] <= -dd)))
        ys.append(bool(drop[i] <= -dd))
    pr, ys, bp = np.array(pr), np.array(ys, dtype=bool), np.array(bp)
    hi = pr >= 0.3
    i = len(Z) - 1
    ce = i - h
    nb = neighbours(z[:ce], z[i], k, gap)
    rows = sorted(({"date": idx[j].strftime("%Y-%m-%d"), "drop": float(drop[j]), "ret": float(fret[j]),
                    "dist": float(np.sqrt(((z[j] - z[i]) ** 2).sum()))} for j in nb), key=lambda x: x["dist"])
    zt = Z.iloc[-1]
    far = zt.abs().sort_values(ascending=False).head(3).index
    return {"available": True, "p": float(np.mean(drop[nb] <= -dd)) * 100, "base": float(np.mean(drop[:ce] <= -dd)) * 100,
            "k": k, "nb": rows, "auc": auc(pr, ys) if len(pr) else None, "n_test": int(len(pr)),
            "brier": float(np.mean((pr - ys) ** 2)) if len(pr) else None, "brier0": float(np.mean((bp - ys) ** 2)) if len(pr) else None,
            "hi_n": int(hi.sum()), "hi_hit": float(ys[hi].mean() * 100) if hi.sum() else None,
            "lo_hit": float(ys[~hi].mean() * 100) if (~hi).sum() else None,
            "med_ret": float(np.median([x["ret"] for x in rows])), "worst": float(min(x["drop"] for x in rows)),
            "n_bad": int(sum(x["drop"] <= -dd for x in rows)),
            "unusual": [(FEAT_ZH.get(n, n), float(zt[n])) for n in far], "since": idx[0].strftime("%Y-%m"),
            "asof": idx[-1].strftime("%Y-%m-%d"), "n_feat": int(Z.shape[1])}


# ---------------------------------------------------------------- 鳥群：吸收比率
def absorption_series(px: pd.DataFrame, win: int, hl: int, k: int) -> pd.Series:
    r = np.log(px).diff().dropna().to_numpy()
    idx = np.log(px).diff().dropna().index
    w = 0.5 ** (np.arange(win)[::-1] / hl)
    w = w / w.sum()
    out = np.full(len(r), np.nan)
    for i in range(win, len(r) + 1, 1):
        x = r[i - win:i]
        xm = x - (w[:, None] * x).sum(0)
        cov = (xm * w[:, None]).T @ xm
        ev = np.linalg.eigvalsh(cov)
        out[i - 1] = ev[-k:].sum() / ev.sum()
    return pd.Series(out, index=idx).dropna()


def absorption(hist: pd.DataFrame, spx: pd.Series, c: Dict) -> Dict:
    cols = [x for x in SECTORS if x in hist.columns]
    if len(cols) < 9:
        return {"available": False}
    px = hist[cols].dropna()
    px = px[(px > 0).all(axis=1)]
    if len(px) < c["ar_win"] + 600:
        return {"available": False}
    ar = absorption_series(px, int(c["ar_win"]), int(c["ar_hl"]), int(c["ar_k"]))
    dar = (ar.rolling(15).mean() - ar.rolling(252).mean()) / ar.rolling(252).std()
    dar = dar.dropna()
    sig = dar >= c["dar"]
    bt = score(sig, spx, int(c["horizon"]), float(c["dd"]))
    pct = float((ar.iloc[:-1] < ar.iloc[-1]).mean() * 100)
    arv = ar.to_numpy()
    ar_exp = pd.Series([np.nan if i < 250 else (arv[:i] < arv[i]).mean() * 100 for i in range(len(arv))], index=ar.index)
    return {"available": True, "_ar_pct": ar_exp.dropna(), "ar": float(ar.iloc[-1]) * 100, "ar_pct": pct, "dar": float(dar.iloc[-1]),
            "on": bool(sig.iloc[-1]), "bt": bt, "since": ar.index[0].strftime("%Y-%m"), "asof": ar.index[-1].strftime("%Y-%m-%d"),
            "ar_1y": float(ar.iloc[-252:].mean()) * 100, "spark": ar.iloc[-500:] * 100}


# ---------------------------------------------------------------- 亂流：Mahalanobis 距離
def turbulence_series(hist: pd.DataFrame, win: int) -> pd.Series:
    cols = [x for x in CROSS if x in hist.columns]
    px = hist[cols].ffill(limit=3).dropna()
    ch = {}
    for x in cols:
        ch[x] = px[x].diff() if x == "^TNX" else np.log(px[x].where(px[x] > 0)).diff() * 100
    d = pd.DataFrame(ch).replace([np.inf, -np.inf], np.nan).dropna()
    x = d.to_numpy()
    out = np.full(len(x), np.nan)
    for i in range(win, len(x)):
        h = x[i - win:i]
        mu, cov = h.mean(0), np.cov(h, rowvar=False)
        try:
            inv = np.linalg.pinv(cov)
        except np.linalg.LinAlgError:
            continue
        v = x[i] - mu
        out[i] = float(v @ inv @ v) / x.shape[1]
    return pd.Series(out, index=d.index).dropna()


def turbulence(hist: pd.DataFrame, spx: pd.Series, c: Dict) -> Dict:
    if sum(x in hist.columns for x in CROSS) < 11:
        return {"available": False}
    tb = turbulence_series(hist, int(c["tb_win"]))
    if len(tb) < 1000:
        return {"available": False}
    t5 = tb.rolling(5).mean().dropna()
    # expanding percentile: each day ranked against everything before it
    vals = t5.to_numpy()
    pct = np.array([np.nan if i < 250 else (vals[:i] < vals[i]).mean() * 100 for i in range(len(vals))])
    pc = pd.Series(pct, index=t5.index).dropna()
    sig = pc >= c["tb_pct"]
    bt = score(sig, spx, int(c["horizon"]), float(c["dd"]))
    top = tb.iloc[-20:].idxmax()
    return {"available": True, "_pc": pc, "t5": float(t5.iloc[-1]), "pct": float(pc.iloc[-1]), "on": bool(sig.iloc[-1]), "bt": bt,
            "since": pc.index[0].strftime("%Y-%m"), "asof": pc.index[-1].strftime("%Y-%m-%d"),
            "top_d": top.strftime("%Y-%m-%d"), "top_v": float(tb[top]), "spark": pc.iloc[-500:]}


# ---------------------------------------------------------------- 熱度：價格動能（離趨勢多遠、是否加速、是否太平靜）
def exp_pct(sr: pd.Series, warm: int = 1000) -> pd.Series:
    """Each value's percentile among all earlier values (expanding, past only)."""
    import bisect
    v = sr.to_numpy(dtype=float)
    out = np.full(len(v), np.nan)
    seen: List[float] = []
    for i, x in enumerate(v):
        if np.isnan(x):
            continue
        if len(seen) >= warm:
            out[i] = bisect.bisect_left(seen, x) / len(seen) * 100
        bisect.insort(seen, x)
    return pd.Series(out, index=sr.index)


def curvature(lp: pd.Series, n: int = 252) -> pd.Series:
    """Quadratic coefficient of log price over the last n days (> 0 = rising faster than exponential, Sornette)."""
    t = np.arange(n) - (n - 1) / 2
    w = np.linalg.pinv(np.vstack([np.ones(n), t, t ** 2]).T)[2]
    c = np.convolve(lp.to_numpy(), w[::-1], mode="full")[n - 1:len(lp)] * n * n
    return pd.Series(c, index=lp.index[n - 1:]).reindex(lp.index)


HEAT_BANDS = ((0, 30, "冷"), (30, 60, "溫"), (60, 80, "熱"), (80, 101, "很熱"))


def heat(spx: pd.Series) -> Dict:
    spx = spx.dropna()
    spx = spx[spx > 0]
    if len(spx) < 252 * 30:
        return {"available": False}
    lp = np.log(spx)
    dev = spx / spx.rolling(200).mean() - 1
    comp = pd.DataFrame({"dev": exp_pct(dev), "acc": exp_pct(curvature(lp)), "calm": 100 - exp_pct(lp.diff().rolling(21).std())})
    h = comp.mean(axis=1, skipna=False).dropna()
    out_rows = []
    for yrs, dd in ((1, 20), (3, 30)):
        n = 252 * yrs
        fr = (spx.shift(-n) / spx - 1) * 100
        fmin = spx[::-1].rolling(n, min_periods=n).min()[::-1].shift(-1)
        fdd = (fmin / spx - 1) * 100
        j = pd.DataFrame({"h": h, "r": fr, "dd": fdd}).dropna()
        for lo, hi, zh in HEAT_BANDS:
            x = j[(j.h >= lo) & (j.h < hi)]
            out_rows.append({"yrs": yrs, "dd": dd, "band": zh, "lo": lo, "hi": min(hi, 100), "n": int(len(x)),
                             "med": float(x.r.median()) if len(x) else None, "crash": float((x.dd <= -dd).mean() * 100) if len(x) else None})
        out_rows.append({"yrs": yrs, "dd": dd, "band": "全部", "n": int(len(j)), "med": float(j.r.median()), "crash": float((j.dd <= -dd).mean() * 100)})
    now = float(h.iloc[-1])
    return {"available": True, "now": now, "band": next(z for lo, hi, z in HEAT_BANDS if lo <= now < hi),
            "comp": {k: float(comp[k].iloc[-1]) for k in comp}, "dev_pct": float(dev.iloc[-1] * 100), "rows": out_rows,
            "since": h.index[0].strftime("%Y"), "spark": h.iloc[-500:]}


# ---------------------------------------------------------------- AI 風險分數
QUAKE_PTS = (100, 80, 60, 40, 20)            # by aftershock bucket: 1–5, 6–20, 21–60, 61–250, > 250 days


def score_series(out: Dict) -> pd.Series:
    """Daily 0–100: mean of turbulence percentile, synchrony percentile (both vs their own past) and aftershock stage."""
    parts = []
    t, a, q = out.get("turbulence") or {}, out.get("absorption") or {}, out.get("aftershock") or {}
    if t.get("available"):
        parts.append(t["_pc"])
    if a.get("available"):
        parts.append(a["_ar_pct"])
    if q.get("available"):
        sn = q["_since"]
        parts.append(pd.Series([QUAKE_PTS[_bucket(max(int(x), 1))] for x in sn.to_numpy()], index=sn.index))
    if len(parts) < 2:
        return pd.Series(dtype=float)
    j = pd.concat(parts, axis=1).ffill(limit=3).dropna()
    return j.mean(axis=1)


BANDS = ((0, 40, "低"), (40, 55, "偏低"), (55, 70, "中等"), (70, 101, "偏高"))


def risk_score(out: Dict, spx: pd.Series, h: int = 63) -> Dict:
    sc = score_series(out)
    spx = spx.dropna()
    if len(sc) < 1000 or len(spx) < 1000:
        return {"available": False}
    j = pd.concat({"s": sc, "p": spx}, axis=1).dropna()
    p = j["p"]
    drop = fwd_drop(p, h)
    d21 = fwd_drop(p, 21)
    # first day the fall reached -10 % (trading days after the signal day)
    pv = p.to_numpy()
    hit_day = np.full(len(pv), np.nan)
    for i in range(len(pv) - 1):
        seg = pv[i + 1:i + 1 + h] / pv[i] - 1
        k = np.flatnonzero(seg <= -0.10)
        if len(k):
            hit_day[i] = k[0] + 1
    hd = pd.Series(hit_day, index=p.index)
    ok = drop.notna()
    rows = []
    for lo, hi, zh in BANDS:
        m = ok & (j["s"] >= lo) & (j["s"] < hi)
        dm = drop[m]
        if not len(dm):
            rows.append({"band": zh, "lo": lo, "hi": min(hi, 100), "n": 0})
            continue
        rows.append({"band": zh, "lo": lo, "hi": min(hi, 100), "n": int(len(dm)),
                     "digest": float((dm > -5).mean() * 100), "pull": float(((dm <= -5) & (dm > -10)).mean() * 100),
                     "crash": float((dm <= -10).mean() * 100), "d21": float((d21[m] <= -5).mean() * 100),
                     "days_med": float(hd[m].dropna().median()) if hd[m].notna().any() else None})
    base = {"digest": float((drop[ok] > -5).mean() * 100), "crash": float((drop[ok] <= -10).mean() * 100),
            "d21": float((d21[d21.notna()] <= -5).mean() * 100)}
    y = (drop[ok] <= -10).to_numpy()
    sv = j["s"][ok].to_numpy()
    now = float(sc.iloc[-1])
    cur = next(k for k, (lo, hi, _z) in enumerate(BANDS) if lo <= now < hi)
    # the present pattern: turbulence high while sectors move apart
    t, a = out.get("turbulence") or {}, out.get("absorption") or {}
    pat = None
    if t.get("available") and a.get("available"):
        pj = pd.concat({"t": t["_pc"], "a": a["_ar_pct"]}, axis=1).dropna()
        on = ((pj["t"] >= 80) & (pj["a"] <= 20)).reindex(drop.index, fill_value=False).astype(bool)
        pm = on & ok
        if pm.sum() >= 20:
            dm = drop[pm]
            prior = on.shift(1, fill_value=False).rolling(20, min_periods=1).max().astype(bool)
            first = on & ~prior & ok
            pat = {"n": int(pm.sum()), "episodes": int(first.sum()), "ep_crash": int((drop[first] <= -10).sum()),
                   "days_med": float(hd[pm].dropna().median()) if hd[pm].notna().any() else None,
                   "digest": float((dm > -5).mean() * 100), "crash": float((dm <= -10).mean() * 100),
                   "pull": float(((dm <= -5) & (dm > -10)).mean() * 100), "now": bool(t["pct"] >= 80 and a["ar_pct"] <= 20)}
    return {"available": True, "now": now, "pct": float((sc.iloc[:-1] < now).mean() * 100), "cur": cur, "rows": rows,
            "base": base, "auc": auc(sv, y.astype(bool)), "since": sc.index[0].strftime("%Y-%m"), "h": h,
            "pattern": pat, "spark": sc.iloc[-250:]}


# ---------------------------------------------------------------- all three
def build(eng) -> Dict:
    hist = getattr(eng.market, "history", None)
    if hist is None or not len(hist):
        return {"available": False}
    lh = getattr(getattr(eng, "long_history", None), "spx", None)
    spx_long = lh if lh is not None and len(lh) > 252 * 30 else eng.market.series("^GSPC")
    spx = eng.market.series("^GSPC")
    key = (str(hist.index[-1]), hist.shape, len(spx_long), str(spx_long.index[-1]) if len(spx_long) else "",
           int(pd.util.hash_pandas_object(hist.tail(300), index=False).sum()))
    if _CACHE.get("key") == key:
        return _CACHE["val"]
    c = CFG
    out = {"available": True, "cfg": c}
    for k, fn in (("aftershock", lambda: aftershock(spx_long, c)), ("absorption", lambda: absorption(hist, spx, c)),
                  ("turbulence", lambda: turbulence(hist, spx, c)), ("analog", lambda: analog(hist, c)), ("heat", lambda: heat(spx_long))):
        try:
            out[k] = fn()
        except Exception as e:  # noqa: BLE001
            out[k] = {"available": False, "err": str(e)}
    out["available"] = any(out[k].get("available") for k in ("aftershock", "absorption", "turbulence", "analog"))
    try:
        out["score"] = risk_score(out, spx)
    except Exception as e:  # noqa: BLE001
        out["score"] = {"available": False, "err": str(e)}
    _CACHE.update(key=key, val=out)
    return out
