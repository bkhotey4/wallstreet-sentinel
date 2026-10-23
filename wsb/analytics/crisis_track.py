"""危機預警成績單 — did the stress index (SSI) warn before past crises, how early, how often it cried wolf, and what the
same reading has historically meant from here.

Crisis = the S&P 500 falls ≥ min_dd % below its 52-week high; the episode runs until it is back within reset % of the
high.  "Warned" = SSI reached the level in the window from 63 trading days before the peak up to the day the fall first
reached -10 % (so the warning came while there was still something to avoid); lead = trading days between the first
such reading and that -10 % day.  Crises that start before the SSI history (+63 days) are listed but not scored.
False alarm = SSI crossing up through the level (after ≥ 20 days below it) with the S&P 500 not falling ≥ 10 % from that
day within the next 126 trading days.  Conditional odds use every day with SSI at or above today's band (overlapping
days, so they are frequencies, not independent trials).  The SSI's components were chosen with hindsight; this is a
back-test, not an out-of-sample record, and not a forecast."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from ..config import SETTINGS


def cfg() -> Dict:
    d = {"min_dd": 15.0, "reset": 5.0, "levels": [55, 70], "early_days": 5, "pre_days": 63, "fa_days": 126, "fa_dd": 10.0}
    return {**d, **(SETTINGS.get("crisis_track") or {})}


def crises(full: pd.Series, min_dd: float, reset: float) -> List[Dict]:
    full = full.dropna()
    hi = full.rolling(252, min_periods=1).max()
    dd = (full / hi - 1) * 100
    out, i, n = [], 0, len(full)
    while i < n:
        if dd.iloc[i] <= -min_dd:
            pk = full.iloc[max(0, i - 251):i + 1].idxmax()
            j = i
            while j < n and dd.iloc[j] < -reset:
                j += 1
            seg = full[pk:full.index[min(j, n - 1)]]
            tr = seg.idxmin()
            t10 = seg[(seg / full[pk] - 1) * 100 <= -10].index[0]
            out.append({"peak": pk, "trough": tr, "dd": float(full[tr] / full[pk] - 1) * 100, "t10": t10,
                        "ongoing": j >= n})
            i = j + 1
            continue
        i += 1
    return out


def _name(pk: pd.Timestamp, tr: pd.Timestamp) -> str:
    best = None
    for sc in SETTINGS.get("stress_scenarios", []) or []:
        a, b = pd.Timestamp(sc["start"]), pd.Timestamp(sc["end"])
        if a <= tr and b >= pk:
            ov = (min(b, tr) - max(a, pk)).days
            if best is None or ov > best[0]:
                best = (ov, sc["name"])
    return best[1] if best else f"{pk:%Y} 回檔"


def wilson(k: int, n: int, z: float = 1.96):
    """95 % Wilson interval for k successes in n trials (behaves at k = n, unlike the normal approximation)."""
    if n <= 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h) * 100, min(1.0, c + h) * 100


def build(eng) -> Dict:
    c = cfg()
    st = getattr(eng, "stress", None)
    ssi = st.history.dropna() if st is not None and getattr(st, "history", None) is not None else pd.Series(dtype=float)
    full = eng.market.series("^GSPC").dropna()
    if len(ssi) < 500 or len(full) < 500:
        return {"available": False}
    start = ssi.index[0]
    rows = []
    for e in crises(full, c["min_dd"], c["reset"]):
        pi = full.index.get_loc(e["peak"])
        w0 = full.index[max(0, pi - int(c["pre_days"]))]
        scored = w0 >= start and not e["ongoing"]
        win = ssi[(ssi.index >= w0) & (ssi.index <= e["t10"])]
        r = {"name": _name(e["peak"], e["trough"]), "peak": e["peak"].strftime("%Y-%m-%d"), "trough": e["trough"].strftime("%Y-%m-%d"),
             "dd": e["dd"], "t10": e["t10"].strftime("%Y-%m-%d"), "scored": scored, "ongoing": e["ongoing"],
             "max_ssi": float(win.max()) if len(win) else None, "lead": {}}
        for lv in c["levels"]:
            above = win[win >= lv]
            r["lead"][lv] = (full.index.get_loc(e["t10"]) - full.index.get_loc(above.index[0])) if len(above) and scored else None
        rows.append(r)
    sc = [r for r in rows if r["scored"]]
    summary = {}
    for lv in c["levels"]:
        hit = [r for r in sc if r["lead"][lv] is not None]
        early = [r for r in hit if r["lead"][lv] >= c["early_days"]]
        a = ssi >= lv
        prior = a.shift(1).rolling(20, min_periods=1).max().fillna(0).astype(bool)
        ups = ssi.index[a & ~prior]
        n_up, fa = 0, 0
        for d in ups:
            seg = full[full.index >= d].iloc[:int(c["fa_days"]) + 1]
            if len(seg) <= c["fa_days"]:
                continue
            n_up += 1
            if (seg.min() / seg.iloc[0] - 1) * 100 > -c["fa_dd"]:
                fa += 1
        leads = sorted(r["lead"][lv] for r in hit)
        summary[lv] = {"n": len(sc), "hit": len(hit), "early": len(early), "ups": n_up, "false": fa,
                       "lead_med": leads[len(leads) // 2] if leads else None,
                       "hit_ci": wilson(len(hit), len(sc)), "prec": (n_up - fa) / n_up * 100 if n_up else None,
                       "prec_ci": wilson(n_up - fa, n_up)}
    # where today sits
    now = float(ssi.iloc[-1])
    band = max([lv for lv in [0] + list(c["levels"]) + [60] if lv <= now] or [0])
    j = pd.concat({"ssi": ssi, "spx": full}, axis=1).dropna()
    fmin = j["spx"][::-1].rolling(int(c["fa_days"]), min_periods=int(c["fa_days"])).min()[::-1].shift(-1)
    drop = (fmin / j["spx"] - 1) * 100
    ok = drop.notna()
    odds = {}
    for th in (10, 15, 20):
        cond = ok & (j["ssi"] >= band)
        odds[th] = {"cond": float((drop[cond] <= -th).mean() * 100) if cond.sum() else None, "n": int(cond.sum()),
                    "base": float((drop[ok] <= -th).mean() * 100)}
    beats = sum(1 for r in sc if r["max_ssi"] is not None and now >= r["max_ssi"])
    hi52 = full.iloc[-252:].max()
    return {"available": True, "rows": rows, "summary": summary, "levels": c["levels"], "since": start.strftime("%Y-%m"),
            "now": now, "band": band, "odds": odds, "beats": beats, "n_scored": len(sc),
            "dd_now": float(full.iloc[-1] / hi52 - 1) * 100, "cfg": c}
