"""信用與利率：現在的關係 — what the credit market and the stock market are doing to each other, measured, not assumed.

All from weekly data, recomputed every build:
  * co-movement: correlation of weekly S&P 500 returns with weekly changes of the Baa − 10-year spread (since 1990) and
    of HYG ÷ IEF (since 2007), and whether the spread move LEADS stocks (correlation with returns 1–8 weeks later);
  * warning power: AUC of the Baa spread's 3-year percentile for an S&P 500 fall ≥ 10 % within 13 weeks;
  * the "credit divergence" story (spreads widening while the S&P 500 is near its high): how often a ≥ 10 % fall
    followed, against any week;
  * stocks vs yields: the 52-week correlation of S&P 500 returns with 10-year yield changes, now against its history
    (negative = rising yields hurt stocks, as in 2022);
  * where the stress sits: 13-week change percentiles of CCC − BB, high yield, investment grade and Baa spreads.
ICE BofA and Moody's series are licensed: only directions and percentiles are shown, never their levels."""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd


def _auc(score: pd.Series, y: pd.Series) -> Optional[float]:
    j = pd.concat([score, y], axis=1).dropna()
    if len(j) < 100:
        return None
    s, t = j.iloc[:, 0].values, j.iloc[:, 1].astype(bool).values
    p, n = s[t], s[~t]
    if not len(p) or not len(n):
        return None
    return float((p[:, None] > n[None, :]).mean() + 0.5 * (p[:, None] == n[None, :]).mean())


def _pct(x: pd.Series, n: int = 156) -> Optional[float]:
    x = x.dropna()
    if len(x) < 30:
        return None
    w = x.iloc[-n:]
    return float((w < w.iloc[-1]).mean() * 100)


def build(eng) -> Dict:
    fr, mk = eng.fred, eng.market
    spx = mk.series("^GSPC").dropna()
    baa = fr.get("BAA10Y").dropna()
    y10 = fr.get("DGS10").dropna()
    if len(spx) < 1000 or len(baa) < 1000 or len(y10) < 1000:
        return {"available": False}
    W = pd.DataFrame({"spx": spx.resample("W-FRI").last(), "baa": baa.resample("W-FRI").last(), "y10": y10.resample("W-FRI").last()})
    hyg, ief = mk.series("HYG").dropna(), mk.series("IEF").dropna()
    if len(hyg) > 300 and len(ief) > 300:
        W["hyief"] = (-np.log(hyg / ief)).resample("W-FRI").last() * 100        # up = high yield lagging Treasuries
    W = W[W.index >= "1990-01-01"].ffill(limit=2)
    r = W["spx"].pct_change() * 100
    mn = W["spx"][::-1].rolling(13, min_periods=13).min()[::-1].shift(-1)
    dd13 = (mn / W["spx"] - 1) * 100
    out: Dict = {"available": True, "asof": W.index[-1].strftime("%Y-%m-%d")}
    # 1. co-movement and lead
    co = {}
    for k in ("baa", "hyief"):
        if k not in W:
            continue
        d = W[k].diff()
        j = pd.concat([r, d], axis=1).dropna()
        lead = max((abs(pd.concat([d, r.shift(-L)], axis=1).dropna().corr().iloc[0, 1]), L) for L in range(1, 9))
        co[k] = {"same": float(j.corr().iloc[0, 1]), "lead_abs": float(lead[0]), "lead_w": int(lead[1]),
                 "since": W[k].dropna().index[0].strftime("%Y")}
    out["co"] = co
    # 2. warning power of the Baa spread level
    lvl = W["baa"].rolling(156, min_periods=104).apply(lambda v: (v < v[-1]).mean(), raw=True)
    y = dd13 <= -10
    out["auc_level"] = _auc(lvl, y)
    out["auc_chg"] = _auc(W["baa"].diff(13), y)
    out["baa_pct"] = float(lvl.dropna().iloc[-1] * 100) if lvl.notna().any() else None
    # 3. divergence: Baa 13-week change in its top 20 % while the S&P 500 is within 3 % of its 52-week high
    ch = W["baa"].diff(13)
    top = ch >= ch.rolling(520, min_periods=156).quantile(0.8)
    near = W["spx"] >= W["spx"].rolling(52, min_periods=20).max() * 0.97
    div = (top & near).fillna(False)
    j = pd.concat({"m": div, "dd": dd13}, axis=1).dropna()
    ep = div & ~div.shift(1).rolling(8, min_periods=1).max().fillna(0).astype(bool)
    out["div"] = {"weeks": int(j["m"].sum()), "episodes": int(ep.sum()),
                  "p": float((j.loc[j["m"].astype(bool), "dd"] <= -10).mean() * 100) if j["m"].any() else None,
                  "base": float((j["dd"] <= -10).mean() * 100), "now": bool(div.iloc[-1])}
    # 4. stocks vs yields
    sb = r.rolling(52).corr(W["y10"].diff())
    cb = W["baa"].diff().rolling(52).corr(W["y10"].diff())
    out["stock_yield"] = {"now": float(sb.iloc[-1]), "median": float(sb.median()), "pct": _pct(sb, 1560), "since": sb.dropna().index[0].strftime("%Y")}
    out["credit_yield"] = {"now": float(cb.iloc[-1]), "median": float(cb.median())}
    y3 = W["y10"].diff(13).iloc[-1]
    out["y10_chg13"] = float(y3) if pd.notna(y3) else None
    # 5. where the stress sits (13-week change, 3-year percentile)
    tiers = {}
    for k, sid in (("ccc_bb", None), ("hy", "BAMLH0A0HYM2"), ("ig", "BAMLC0A0CM"), ("baa", "BAA10Y")):
        s = (fr.get("BAMLH0A3HYC") - fr.get("BAMLH0A1HYBB")).dropna() if k == "ccc_bb" else fr.get(sid).dropna()
        if len(s) < 200:
            continue
        w = s.resample("W-FRI").last().dropna()
        c13 = w.diff(13)
        tiers[k] = {"pct": _pct(c13), "up": bool(c13.iloc[-1] > 0)}
    out["tiers"] = tiers
    lo_q = (tiers.get("ccc_bb") or {}).get("pct")
    # investment grade: the ICE index when it is there (Baa − 10y also moves with the 10-year yield itself)
    hi_q = ((tiers.get("ig") or tiers.get("baa") or {}).get("pct")) or 0
    out["pattern"] = ("low" if lo_q is not None and lo_q >= 80 and hi_q < 60 else
                      "broad" if lo_q is not None and lo_q >= 80 and hi_q >= 80 else
                      "calm" if (lo_q or 0) < 60 and hi_q < 60 else "mixed")
    return out
