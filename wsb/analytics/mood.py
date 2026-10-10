"""Market-level views for the website (pure functions on cached data):

* fear_greed   — multi-factor fear / greed gauge (0–100), each factor = percentile vs its own last 2 years
* rule_backtest — how did the S&P 500 do after common "sell-off alarm" rules fired, since 1995 (vs any day)
* linkage      — overnight US theme moves → the next Taiwan session (correlation / beta) + TSM ADR premium
* expected_move — options-implied ±move bands for index ETFs (CBOE straddles) vs realised volatility"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def _s(h: pd.DataFrame, t: str) -> Optional[pd.Series]:
    if h is None or t not in h.columns:
        return None
    s = h[t].dropna()
    s = s[s > 0]
    return s if len(s) > 300 else None


def _pctile(x: pd.Series, win: int = 504) -> pd.Series:
    return x.rolling(win, min_periods=250).apply(lambda a: (a[:-1] < a[-1]).mean() * 100 if len(a) > 1 else np.nan, raw=True)


# ------------------------------------------------------------------ fear & greed
FG_LABELS = [(25, "極度恐慌", "Extreme fear"), (45, "恐慌", "Fear"), (55, "中性", "Neutral"), (75, "貪婪", "Greed"), (101, "極度貪婪", "Extreme greed")]
FG_FACTORS = {
    "mom": ("股市動能", "Momentum", "標普 500 高於 125 日均線的幅度"),
    "vix": ("波動率", "Volatility", "VIX 相對 50 日均值（越低越貪婪）"),
    "term": ("VIX 期限結構", "VIX term structure", "3 個月 VIX ÷ VIX（正價差越大越安心）"),
    "safe": ("避險需求", "Safe-haven demand", "股票 20 日報酬 − 長債 TLT 20 日報酬"),
    "junk": ("垃圾債需求", "Junk-bond demand", "高收益債 HYG − 投資級債 LQD 的 20 日報酬差"),
    "breadth": ("市場寬度", "Breadth", "等權重 RSP 相對標普 500 的 20 日表現"),
    "beta": ("投機熱度", "Risk appetite", "高 β SPHB 相對低波動 SPLV 的 20 日表現"),
}


def fg_label(x: Optional[float]):
    if x is None:
        return "—", "—"
    for lim, zh, en in FG_LABELS:
        if x < lim:
            return zh, en
    return FG_LABELS[-1][1], FG_LABELS[-1][2]


def fear_greed(h: pd.DataFrame, bench: str = "^GSPC") -> Dict:
    spx = _s(h, bench)
    if spx is None:
        return {"available": False}
    raw: Dict[str, pd.Series] = {"mom": spx / spx.rolling(125).mean() - 1}
    vix = _s(h, "^VIX")
    if vix is not None:
        raw["vix"] = -(vix / vix.rolling(50).mean() - 1)
        v3 = _s(h, "^VIX3M")
        if v3 is not None:
            raw["term"] = (v3 / vix).dropna()
    tlt = _s(h, "TLT")
    if tlt is not None:
        raw["safe"] = spx.pct_change(20) - tlt.pct_change(20)
    hyg, lqd = _s(h, "HYG"), _s(h, "LQD")
    if hyg is not None and lqd is not None:
        raw["junk"] = hyg.pct_change(20) - lqd.pct_change(20)
    rsp = _s(h, "RSP")
    if rsp is not None:
        raw["breadth"] = rsp.pct_change(20) - spx.pct_change(20)
    hb, lv = _s(h, "SPHB"), _s(h, "SPLV")
    if hb is not None and lv is not None:
        raw["beta"] = hb.pct_change(20) - lv.pct_change(20)
    idx = spx.index
    pc = pd.DataFrame({k: _pctile(v.reindex(idx).ffill(limit=3).dropna()).reindex(idx) for k, v in raw.items()})
    score = pc.mean(axis=1, skipna=True).where(pc.notna().sum(axis=1) >= 3)
    sc = score.dropna()
    if not len(sc):
        return {"available": False}
    now = float(sc.iloc[-1])
    fwd = (spx.shift(-20) / spx - 1) * 100
    buckets = []
    lo = 0
    for lim, zh, en in FG_LABELS:
        m = (score >= lo) & (score < lim) & fwd.notna()
        x = fwd[m]
        buckets.append({"zh": zh, "en": en, "lo": lo, "hi": min(lim, 100), "n": int(m.sum()),
                        "avg": float(x.mean()) if len(x) else None, "win": float((x > 0).mean() * 100) if len(x) else None})
        lo = lim
    base = fwd[score.notna() & fwd.notna()]
    last = pc.iloc[-1]
    comps = [{"k": k, "zh": FG_FACTORS[k][0], "en": FG_FACTORS[k][1], "def": FG_FACTORS[k][2],
              "v": None if pd.isna(last.get(k)) else round(float(last[k]))} for k in FG_FACTORS if k in pc.columns]
    wk = sc.iloc[-260:]
    hist = [(d.strftime("%Y-%m-%d"), round(float(x), 1)) for d, x in wk.iloc[::5].items()]
    if hist and hist[-1][0] != sc.index[-1].strftime("%Y-%m-%d"):
        hist.append((sc.index[-1].strftime("%Y-%m-%d"), round(now, 1)))

    def ago(n):
        return round(float(sc.iloc[-1 - n]), 1) if len(sc) > n else None
    zh, en = fg_label(now)
    return {"available": True, "score": round(now, 1), "label": zh, "label_en": en, "w1": ago(5), "m1": ago(21), "y1": ago(252),
            "components": comps, "hist": hist, "buckets": buckets, "since": sc.index[0].strftime("%Y"),
            "base_avg": float(base.mean()) if len(base) else None, "base_win": float((base > 0).mean() * 100) if len(base) else None,
            "asof": sc.index[-1].strftime("%Y-%m-%d")}


# ------------------------------------------------------------------ alarm-rule backtest
def _rules(h: pd.DataFrame, bench: str) -> Dict[str, tuple]:
    spx = _s(h, bench)
    out = {}
    if spx is None:
        return out
    r = spx.pct_change() * 100
    out["spx08"] = ("標普單日跌 ≥ 0.8%", "S&P 500 down ≥ 0.8% in a day", r <= -0.8)
    out["spx2"] = ("標普單日跌 ≥ 2%", "S&P 500 down ≥ 2% in a day", r <= -2)
    ndx = _s(h, "^NDX")
    if ndx is not None:
        out["ndx3"] = ("那指單日跌 ≥ 3%", "Nasdaq-100 down ≥ 3% in a day", ndx.pct_change() * 100 <= -3)
    ma = spx.rolling(200).mean()
    out["ma200"] = ("標普跌破 200 日線", "S&P 500 closes below its 200-day", (spx < ma) & (spx.shift(1) >= ma.shift(1)))
    out["dd10"] = ("標普距高點回檔 ≥ 10%", "S&P 500 10% below its 1-year high", spx / spx.rolling(252, min_periods=60).max() - 1 <= -0.10)
    vix = _s(h, "^VIX")
    if vix is not None:
        out["vix25"] = ("VIX 升破 25", "VIX crosses above 25", (vix >= 25) & (vix.shift(1) < 25))
        out["vix35"] = ("VIX 升破 35", "VIX crosses above 35", (vix >= 35) & (vix.shift(1) < 35))
        out["vixjump"] = ("VIX 單日大漲 ≥ 20%", "VIX up ≥ 20% in a day", vix.pct_change() >= 0.20)
        v9 = _s(h, "^VIX9D")
        if v9 is not None:
            inv = (v9 / vix) > 1.05
            out["vix9d"] = ("短天期 VIX 倒掛（VIX9D > VIX 5%）", "VIX9D > VIX by 5% (inversion)", inv & ~inv.shift(1, fill_value=False))
    hyg, lqd = _s(h, "HYG"), _s(h, "LQD")
    if hyg is not None and lqd is not None:
        rel = (hyg / lqd).pct_change(20) * 100
        out["credit"] = ("高收益債 20 日落後投資級債 ≥ 2%", "HYG lags LQD by ≥ 2% over 20 days", rel <= -2)
    tnx = _s(h, "^TNX")
    if tnx is not None:
        sc = 10 if tnx.median() > 15 else 1                  # Yahoo used to quote ^TNX ×10
        out["tnx"] = ("10 年債殖利率 5 日升 ≥ 25bp", "10-year yield +25bp in 5 days", (tnx - tnx.shift(5)) / sc * 100 >= 25)
    return out


def rule_backtest(h: pd.DataFrame, bench: str = "^GSPC", cooldown: int = 10) -> Dict:
    spx = _s(h, bench)
    if spx is None:
        return {"available": False}
    fwd5 = (spx.shift(-5) / spx - 1) * 100
    fwd20 = (spx.shift(-20) / spx - 1) * 100
    lows = pd.concat([spx.shift(-k) for k in range(1, 21)], axis=1).min(axis=1)
    dd = (lows / spx - 1) * 100
    valid = fwd20.notna() & lows.notna()
    base = {"avg5": float(fwd5[valid].mean()), "avg20": float(fwd20[valid].mean()), "win20": float((fwd20[valid] > 0).mean() * 100),
            "dd5": float((dd[valid] <= -5).mean() * 100), "n": int(valid.sum())}
    rows = []
    for k, (zh, en, flag) in _rules(h, bench).items():
        flag = flag.reindex(spx.index).fillna(False).astype(bool)
        ev, last = [], None
        for i, (d, f) in enumerate(flag.items()):
            if f and (last is None or i - last > cooldown):
                ev.append(d)
                last = i
            elif f:
                last = i
        evv = [d for d in ev if valid.get(d, False)]
        n = len(evv)
        a5 = float(fwd5[evv].mean()) if n else None
        a20 = float(fwd20[evv].mean()) if n else None
        w20 = float((fwd20[evv] > 0).mean() * 100) if n else None
        p = float((dd[evv] <= -5).mean() * 100) if n else None
        if n < 10:
            vd, vz, ve = "n", "樣本太少", "Too few cases"
        elif p is not None and p >= max(base["dd5"] * 1.5, base["dd5"] + 5):
            vd, vz, ve = "warn", "有預警力：之後再跌 5% 的機率明顯偏高", "Useful warning: a further 5% drop was clearly more likely"
        elif a20 is not None and a20 >= base["avg20"] + 1 and (p or 0) <= base["dd5"] * 1.5:
            vd, vz, ve = "rev", "常是短線低點：之後 20 日平均反而較好", "Often a short-term low: better than average afterwards"
        else:
            vd, vz, ve = "none", "沒有明顯預警力", "No clear edge"
        recent = [d for d in ev if d >= spx.index[max(0, len(spx) - 5)]]
        rows.append({"k": k, "zh": zh, "en": en, "n": n, "avg5": a5, "avg20": a20, "win20": w20, "dd5": p, "verdict": vd,
                     "vz": vz, "ve": ve, "last": ev[-1].strftime("%Y-%m-%d") if ev else None, "now": bool(recent)})
    order = {"warn": 0, "rev": 1, "none": 2, "n": 3}
    rows.sort(key=lambda r: (order[r["verdict"]], -(r["dd5"] or 0)))
    return {"available": True, "rows": rows, "base": base, "since": spx.index[0].strftime("%Y"), "asof": spx.index[-1].strftime("%Y-%m-%d"),
            "cooldown": cooldown}


# ------------------------------------------------------------------ US → Taiwan linkage
PAIRS = [("半導體", "半導體"), ("半導體", "電子零組件"), ("AI伺服器與雲端", "AI伺服器與雲端"), ("國防軍工", "國防軍工"),
         ("金融", "金融"), ("消費", "消費"), ("電信公用", "電信公用"), ("能源", "原物料")]


def _theme_ret(sp, syms: List[str]) -> Optional[pd.Series]:
    cols = [sp.series(s).pct_change() for s in syms if len(sp.series(s)) > 60]
    if not cols:
        return None
    return pd.concat(cols, axis=1).mean(axis=1, skipna=True).dropna() * 100


def _link(us: pd.Series, tw: pd.Series, n: int = 250) -> Dict:
    """Pair each Taiwan session with the most recent US session BEFORE it (the night before, Taipei time)."""
    us = us.dropna()
    tw = tw.dropna()
    pos = us.index.searchsorted(tw.index, side="left") - 1
    ok = pos >= 0
    x = pd.Series(us.values[pos[ok]], index=tw.index[ok])
    y = tw[ok]
    xy = pd.concat([x, y], axis=1).dropna().iloc[-n:]
    if len(xy) < 60:
        return {}
    c = float(xy.corr().iloc[0, 1])
    beta = float(np.cov(xy.iloc[:, 0], xy.iloc[:, 1])[0, 1] / np.var(xy.iloc[:, 0], ddof=1))
    big = xy[xy.iloc[:, 0].abs() >= 2]
    same = float((np.sign(big.iloc[:, 0]) == np.sign(big.iloc[:, 1])).mean() * 100) if len(big) >= 8 else None
    last_us_d = us.index[-1]
    tw_after = tw[tw.index > last_us_d]
    return {"corr": c, "beta": beta, "n": len(xy), "same_big": same, "n_big": int(len(big)), "us_d": last_us_d.strftime("%Y-%m-%d"),
            "us": float(us.iloc[-1]), "implied": beta * float(us.iloc[-1]),
            "tw": float(tw_after.iloc[0]) if len(tw_after) else None,
            "tw_d": tw_after.index[0].strftime("%Y-%m-%d") if len(tw_after) else None}


def linkage(sp, uni: Dict, h: Optional[pd.DataFrame] = None) -> Dict:
    if sp is None or getattr(sp, "close", pd.DataFrame()).empty:
        return {"available": False}
    us, tw = uni.get("us") or {}, uni.get("tw") or {}
    rows = []
    for ut, tt in PAIRS:
        usy = [s for s, t in (us.get("themes") or {}).items() if t == ut]
        tws = [s for s, t in (tw.get("themes") or {}).items() if t == tt]
        a, b = _theme_ret(sp, usy), _theme_ret(sp, tws)
        if a is None or b is None:
            continue
        r = _link(a, b)
        if r:
            rows.append({"us_theme": ut, "tw_theme": tt, "n_us": len(usy), "n_tw": len(tws), **r})
    idx = []
    for us_t, zh in (("^SOX", "費城半導體"), ("^NDX", "那斯達克 100"), ("^GSPC", "標普 500")):
        a, b = _s(h, us_t), _s(h, "^TWII")
        if a is not None and b is not None:
            r = _link(a.pct_change() * 100, b.pct_change() * 100)
            if r:
                idx.append({**{k: v for k, v in r.items() if k != "us"}, "us_ret": r["us"], "us_n": zh, "tw_n": "台股加權"})
    adr = None
    tsm, t2330 = sp.series("TSM"), sp.series("2330.TW")
    fx = _s(h, "TWD=X")
    if len(tsm) > 100 and len(t2330) > 100 and fx is not None:
        df = pd.concat([tsm.rename("adr"), t2330.rename("tw"), fx.rename("fx")], axis=1).sort_index().ffill(limit=3).dropna()
        prem = (df["adr"] / (df["tw"] * 5 / df["fx"]) - 1) * 100
        prem = prem.iloc[-500:]
        if len(prem) > 60:
            cur = float(prem.iloc[-1])
            adr = {"now": cur, "avg1y": float(prem.iloc[-250:].mean()), "pct": float((prem.iloc[-250:] < cur).mean() * 100),
                   "hi": float(prem.iloc[-250:].max()), "lo": float(prem.iloc[-250:].min()), "asof": prem.index[-1].strftime("%Y-%m-%d"),
                   "hist": [(d.strftime("%Y-%m-%d"), round(float(x), 2)) for d, x in prem.iloc[-250::5].items()]}
    return {"available": bool(rows or idx), "rows": rows, "index": idx, "adr": adr}


# ------------------------------------------------------------------ options-implied move (index ETFs)
SD = 1.2533                                                   # σ√t ÷ E|move| for a normal distribution
EM_SYMS = {"SPY": ("標普 500 ETF", "^GSPC"), "QQQ": ("那斯達克 100 ETF", "QQQ"), "IWM": ("羅素 2000 ETF", "^RUT"), "SMH": ("半導體 ETF", "SMH")}


def _pick(rows: List[Dict], lo: int, hi: int, target: int) -> Optional[Dict]:
    c = [r for r in rows if lo <= r["days"] <= hi]
    return min(c, key=lambda r: abs(r["days"] - target)) if c else None


def expected_move(opt: Dict, h: Optional[pd.DataFrame]) -> Dict:
    out = []
    for sym, (zh, proxy) in EM_SYMS.items():
        rec = opt.get(sym) or {}
        rows = rec.get("rows") or []
        if not rows:
            continue
        spot = rec.get("spot")
        px = _s(h, proxy) if h is not None else None
        rv = float(px.pct_change().iloc[-20:].std() * np.sqrt(252) * 100) if px is not None else None
        bands = []
        for lab, en, w in (("本週", "This week", _pick(rows, 1, 9, 5)), ("約一個月", "~1 month", _pick(rows, 20, 45, 30))):
            if not w:
                continue
            sd = w["mv"] * SD                                  # one standard deviation implied by the straddle
            rv_sd = rv * np.sqrt(max(w["days"], 1) / 365) if rv else None
            bands.append({"zh": lab, "en": en, "exp": w["exp"], "days": w["days"], "mv": w["mv"], "sd": sd,
                          "lo": spot * (1 - sd / 100), "hi": spot * (1 + sd / 100), "rv_sd": rv_sd,
                          "ratio": (sd / rv_sd) if rv_sd else None,
                          "iv": sd / np.sqrt(max(w["days"], 1) / 365)})
        if bands:
            out.append({"sym": sym, "zh": zh, "spot": spot, "rv20": rv, "bands": bands, "asof": rec.get("asof")})
    return {"available": bool(out), "rows": out}
