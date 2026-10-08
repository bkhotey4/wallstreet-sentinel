"""Empirical drawdown odds conditioned on the Stress Index.

Question answered: "Historically, when the SSI was in today's zone, how often
did the S&P 500 fall X% at some point in the next N trading days?"
This is a transparent conditional frequency from real data — not a black box.
Overlapping windows mean observations are autocorrelated, so we also report
the number of independent episodes and the unconditional base rate.

Momentum layer: the level bucket alone ignores *how fast* stress is building.
We also classify the SSI 20-day change against its own history (dynamic
percentile thresholds, not fixed points) into 升溫 / 持平 / 降溫, measure the
hit rate in the (level × momentum) cell, and shrink it toward the level-only
estimate according to how many non-overlapping windows the cell holds
(empirical Bayes). Thin cells therefore cannot produce extreme numbers."""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from ..config import SETTINGS


def forward_min_return(close: pd.Series, days: int) -> pd.Series:
    """min(close[t+1..t+days]) / close[t] - 1"""
    fwd_min = close.shift(-1)[::-1].rolling(days, min_periods=days).min()[::-1]
    return fwd_min / close - 1


def _episodes(hit: pd.Series) -> int:
    """Count distinct runs of consecutive True (independent-ish events)."""
    h = hit.astype(int)
    return int(((h.diff().fillna(h.iloc[0] if len(h) else 0)) == 1).sum())


def lift_text(lift) -> str:
    """Plain-language comparison vs the base rate."""
    if lift is None:
        return "倍數資料缺"
    if 0.9 <= lift <= 1.1:
        return f"約等於基準（×{lift:.2f}）"
    return f"{'高於' if lift > 1 else '低於'}基準 {lift:.2f} 倍"


def crash_odds(stress_hist: pd.Series, close: pd.Series, current: float, chg20: float | None = None) -> Dict:
    cfg = SETTINGS.get("crash_odds", {})
    edges = cfg.get("buckets", [0, 35, 55, 70, 85, 101])
    mcfg = cfg.get("momentum", {})
    mom_n = int(mcfg.get("lookback", 20))
    q_hi, q_lo = float(mcfg.get("rising_pctile", 80)), float(mcfg.get("falling_pctile", 20))
    prior_k = float(mcfg.get("prior_windows", 4))
    close = close.dropna()
    stress_hist = stress_hist.dropna()
    df = pd.DataFrame({"ssi": stress_hist, "mom": stress_hist.diff(mom_n)}).join(close.rename("px"), how="inner")
    df = df.dropna(subset=["ssi", "px"])
    out: Dict = {"sample_start": df.index[0].strftime("%Y-%m-%d") if len(df) else None,
                 "n_days": int(len(df)), "horizons": []}
    if len(df) < 300:
        out["error"] = "歷史樣本不足"
        return out
    bucket_idx = np.digitize([current], edges)[0] - 1
    lo, hi = edges[max(bucket_idx, 0)], edges[min(bucket_idx + 1, len(edges) - 1)]
    out["bucket"] = f"{lo}–{min(hi, 100)}"
    # ---- momentum state (dynamic thresholds from the SSI's own 20-day-change distribution)
    if chg20 is None and len(stress_hist) > mom_n:
        chg20 = float(current - stress_hist.iloc[-1 - mom_n])
    mom_hist = df["mom"].dropna()
    th_hi = float(np.percentile(mom_hist, q_hi)) if len(mom_hist) > 100 else None
    th_lo = float(np.percentile(mom_hist, q_lo)) if len(mom_hist) > 100 else None
    state = None
    if chg20 is not None and th_hi is not None:
        state = "升溫" if chg20 >= th_hi else ("降溫" if chg20 <= th_lo else "持平")
    mom_pct = float((mom_hist < chg20).mean() * 100) if chg20 is not None and len(mom_hist) else None
    out["momentum"] = {"chg20": chg20, "state": state, "pctile": mom_pct,
                       "th_rising": th_hi, "th_falling": th_lo, "lookback": mom_n}
    if state == "升溫":
        in_state = df["mom"] >= th_hi
    elif state == "降溫":
        in_state = df["mom"] <= th_lo
    elif state == "持平":
        in_state = (df["mom"] > th_lo) & (df["mom"] < th_hi)
    else:
        in_state = pd.Series(False, index=df.index)
    for h in cfg.get("horizons", []):
        n, dd = int(h["days"]), float(h["drawdown"])
        fmr = forward_min_return(df["px"], n)
        valid = fmr.notna()
        hit = (fmr <= -dd) & valid
        base = float(hit[valid].mean() * 100)
        inb = valid & (df["ssi"] >= lo) & (df["ssi"] < hi)
        cond = float(hit[inb].mean() * 100) if inb.sum() else None
        table: List[Dict] = []
        for a, b in zip(edges[:-1], edges[1:]):
            m = valid & (df["ssi"] >= a) & (df["ssi"] < b)
            if m.sum() >= 20:
                table.append({"zone": f"{a}–{min(b, 100)}", "prob": float(hit[m].mean() * 100),
                              "days": int(m.sum())})
        # ---- level × momentum cell, shrunk toward the level-only estimate
        cell = inb & in_state.fillna(False)
        n_cell = int(cell.sum())
        cell_raw = float(hit[cell].mean() * 100) if n_cell else None
        n_eff = n_cell / n                                   # ≈ non-overlapping windows in the cell
        if cond is None:
            adj = None
        elif cell_raw is None:
            adj = cond
        else:
            adj = (cell_raw * n_eff + cond * prior_k) / (n_eff + prior_k)
        lift_adj = (adj / base) if adj is not None and base > 0 else None
        out["horizons"].append({
            "days": n, "drawdown_pct": dd * 100, "base_rate": base,
            "conditional": cond, "obs_in_zone": int(inb.sum()),
            "adjusted": adj, "lift_adj": lift_adj, "lift_adj_text": lift_text(lift_adj),
            "cell_raw": cell_raw, "cell_days": n_cell, "cell_windows": round(n_eff, 1),
            "cell_episodes": _episodes(hit & cell) if n_cell else 0,
            "episodes_in_zone": _episodes(hit & inb) if inb.sum() else 0,   # runs on the full calendar
            "lift": (cond / base) if cond is not None and base > 0 else None,
            "lift_text": lift_text((cond / base) if cond is not None and base > 0 else None),
            "table": table,
            "median_fwd_min_in_zone": float(fmr[inb].median() * 100) if inb.sum() else None,
        })
    return out
