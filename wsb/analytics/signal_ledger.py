"""訊號成績單 — does a signal actually beat picking a random stock from the same list on the same day?

Two records, kept apart because they answer different questions:
* replay (歷史回放): the same fixed rules applied to the last ~2 years of cached prices.  Rules were written by hand,
  not fitted, but they were written knowing roughly what worked — treat it as in-sample.
* ledger (實盤紀錄): every signal the site publishes is written down the day it first appears, with its price.  Results
  only count after the holding period has passed — truly out-of-sample, starting from the day logging began.
Score of one signal = its forward return − the equal-weight average forward return of every stock in the same
market universe over the same window (= "a random pick that day") − round-trip cost.  Horizons 5 / 20 / 60 sessions.
Direction: entry signals should beat the random pick; overheating flags (≥2 exhaustion signs) should lag it.
Verdict needs ≥ min_n matured cases and a 90 % interval that excludes zero; otherwise it says "not enough evidence"."""
from __future__ import annotations

import json
import logging
import math
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS

log = logging.getLogger(__name__)
LEDGER = DATA_DIR / "signal_ledger.json"
HORIZONS = (5, 20, 60)
KINDS = {"A": ("★ 條件最齊全", "★ All conditions met", 1), "B": ("在參考區間內", "In the reference zone", 1),
         "C": ("有訊號・等拉回", "Signal — wait for a pullback", 1), "exh": ("過熱（≥2 個力竭警示）", "Overheated (≥2 exhaustion flags)", -1)}


def cfg() -> Dict:
    return {"cost_bp": {"us": 10, "tw": 45, "hk": 30}, "min_n": 20, "dedupe_days": 10, "keep_days": 400,
            **(SETTINGS.get("signal_ledger", {}) or {})}


def _cost(mk: str) -> float:
    return float((cfg()["cost_bp"] or {}).get(mk, 20)) / 1e4


def _fwd_table(closes: Dict[str, pd.Series], h: int) -> pd.DataFrame:
    """date × symbol forward h-session returns on each symbol's own trading days."""
    cols = {}
    for s, c in closes.items():
        c = c.dropna()
        if len(c) > h:
            cols[s] = c.shift(-h) / c - 1
    return pd.DataFrame(cols)


def summarize(x: Iterable, direction: int, min_n: int, h: int = 1) -> Dict:
    """x: [(date, excess)].  Signals on the same day move together and h-session windows overlap, so the interval is
    built from per-day averages with an effective sample of about one independent window per h sessions."""
    pts = [(d, v) for d, v in x if v is not None and v == v]
    n = len(pts)
    if n == 0:
        return {"n": 0, "verdict": "insufficient"}
    a = np.asarray([v for _, v in pts], float)
    m, md = float(a.mean()), float(np.median(a))
    daily = pd.Series(a, index=pd.to_datetime([d for d, _ in pts])).groupby(level=0).mean().sort_index()
    span = max(1, len(pd.bdate_range(daily.index[0], daily.index[-1])))
    n_eff = max(1.0, min(float(len(daily)), span / max(1, h)))
    se = float(daily.std(ddof=1) / math.sqrt(n_eff)) if len(daily) > 1 and n_eff > 1 else None
    lo, hi = (m - 1.645 * se, m + 1.645 * se) if se else (None, None)
    hit = float(((a * direction) > 0).mean())
    if n < min_n or se is None or n_eff < 8:
        v = "insufficient"
    elif (lo > 0 and direction > 0) or (hi < 0 and direction < 0):
        v = "works"
    elif (hi < 0 and direction > 0) or (lo > 0 and direction < 0):
        v = "backfires"
    else:
        v = "unclear"
    return {"n": n, "n_eff": round(n_eff, 1), "mean": m * 100, "median": md * 100, "lo": lo * 100 if lo is not None else None,
            "hi": hi * 100 if hi is not None else None, "hit": hit * 100, "verdict": v}


# ------------------------------------------------------------------ replay (in-sample, immediate)
def replay(series: Dict[str, Dict[str, pd.DataFrame]], mk: str, horizons=HORIZONS) -> Dict:
    """series: signals.detect() output per symbol.  First day of each pattern → excess forward return, net of cost."""
    closes = {s: next(iter(p.values()))["close"] for s, p in series.items()}
    cost, min_n = _cost(mk), int(cfg()["min_n"])
    out: Dict[str, Dict] = {}
    for h in horizons:
        fw = _fwd_table(closes, h)
        if fw.empty:
            continue
        bench = fw.mean(axis=1)                                      # the random pick that day
        ex = fw.sub(bench, axis=0) - cost
        per: Dict[str, List[float]] = {}
        for s, pats in series.items():
            if s not in ex.columns:
                continue
            col = ex[s]
            for k, df in pats.items():
                first = df["flag"] & ~df["flag"].shift(1, fill_value=False)
                v = col.reindex(df.index)[first].dropna()
                per.setdefault(k, []).extend(zip(v.index, v.tolist()))
        out[str(h)] = {k: summarize(v, 1, min_n, h) for k, v in per.items()}
        out[str(h)]["_all"] = summarize([x for v in per.values() for x in v], 1, min_n, h)
    return out


# ------------------------------------------------------------------ ledger (live, out-of-sample)
def load() -> List[Dict]:
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []


def save(rows: List[Dict]) -> None:
    tmp = LEDGER.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    tmp.replace(LEDGER)


def record(ledger: List[Dict], mk: str, asof: str, rows: List[Dict], allrows: List[Dict]) -> List[Dict]:
    """Append signals that are new today (not logged for the same symbol + kind within `dedupe_days`)."""
    c = cfg()
    cut = (pd.Timestamp(asof) - pd.Timedelta(days=int(c["dedupe_days"]))).strftime("%Y-%m-%d")
    recent = {(e["mk"], e["sym"], e["kind"]) for e in ledger if e["d"] >= cut}
    add = []
    for r in rows:
        k = r.get("tier")
        if k in ("A", "B", "C") and (mk, r["sym"], k) not in recent and r.get("price"):
            add.append({"d": asof, "mk": mk, "sym": r["sym"], "kind": k, "pattern": r["patterns"][0]["pattern"],
                        "px": round(float(r["price"]), 4), "strength": r.get("strength")})
    for r in allrows:
        if (r.get("exh") or {}).get("n", 0) >= 2 and (mk, r["sym"], "exh") not in recent and r.get("price"):
            add.append({"d": asof, "mk": mk, "sym": r["sym"], "kind": "exh", "pattern": "+".join(r["exh"].get("flags", [])),
                        "px": round(float(r["price"]), 4)})
    keep = (pd.Timestamp(asof) - pd.Timedelta(days=int(c["keep_days"]))).strftime("%Y-%m-%d")
    return [e for e in ledger if e["d"] >= keep] + add


def evaluate(ledger: List[Dict], mk: str, closes: Dict[str, pd.Series], horizons=HORIZONS) -> Dict:
    cost, min_n = _cost(mk), int(cfg()["min_n"])
    rows = [e for e in ledger if e["mk"] == mk]
    out = {"since": min((e["d"] for e in rows), default=None), "logged": len(rows),
           "by_kind": {k: sum(1 for e in rows if e["kind"] == k) for k in KINDS}, "h": {}}
    for h in horizons:
        fw = _fwd_table(closes, h)
        if fw.empty:
            continue
        bench = fw.mean(axis=1)
        res: Dict[str, List[float]] = {k: [] for k in KINDS}
        pending = 0
        for e in rows:
            s, d = e["sym"], pd.Timestamp(e["d"])
            if s not in fw.columns or d not in fw.index or pd.isna(fw.at[d, s]) or pd.isna(bench.get(d)):
                pending += 1
                continue
            res[e["kind"]].append((d, float(fw.at[d, s] - bench[d] - cost)))
        out["h"][str(h)] = {k: summarize(v, KINDS[k][2], min_n, h) for k, v in res.items()}
        out["h"][str(h)]["_pending"] = pending
    return out
