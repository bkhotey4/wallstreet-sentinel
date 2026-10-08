"""Systemic Stress Index (SSI, 0–100).

Each component is a live cross-asset signal (credit, vol, liquidity, rates,
FX carry, equity internals, global/EM, commodities/crypto). Instead of fixed
thresholds, every component is scored against ITS OWN rolling history
(z-score → normal CDF → 0-100), so the index adapts to regime changes.
The full daily history of the composite is rebuilt each cycle, which powers
trend analysis and the empirical crash-odds backtest."""
from __future__ import annotations

import math
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

log = logging.getLogger(__name__)
_erf = np.vectorize(math.erf)


# FRED publication lag (business days between the observation date and its release)
PUB_LAG = {"NFCI": 5, "STLFSI4": 5, "WALCL": 1, "WTREGEN": 1, "WRESBAL": 1, "ICSA": 5, "SAHMREALTIME": 25,
           "BAMLH0A0HYM2": 1, "BAMLH0A3HYC": 1, "BAMLC0A0CM": 1}
# forward-fill reach (business days) between prints: monthly series must bridge a whole month
FFILL_LIMIT = {"SAHMREALTIME": 45}
# how old a real observation may be before the component is excluded as stale (calendar days)
STALE_DAYS = {"NFCI": 14, "STLFSI4": 14, "WALCL": 12, "WTREGEN": 12, "WRESBAL": 12, "ICSA": 14, "SAHMREALTIME": 75}   # monthly series dated on the 1st: up to ~65 days old before the next print


def _slog(x):
    """log that ignores non-positive prices (e.g. WTI futures went negative in 2020) instead of emitting NaN warnings."""
    return np.log(x.where(x > 0)) if hasattr(x, "where") else np.log(x)


def norm_cdf(z):
    return 0.5 * (1.0 + _erf(np.asarray(z, dtype=float) / math.sqrt(2.0)))


def rolling_z(s: pd.Series, window: int, min_periods: int) -> pd.Series:
    mu = s.rolling(window, min_periods=min_periods).mean()
    sd = s.rolling(window, min_periods=min_periods).std()
    return (s - mu) / sd.replace(0, np.nan)


def avg_pairwise_corr(prices: pd.DataFrame, window: int) -> pd.Series:
    r = _slog(prices).diff()
    r = r.dropna(how="all")
    n = r.shape[1]
    if n < 3:
        return pd.Series(dtype=float)
    c = r.rolling(window, min_periods=int(window * 0.8)).corr()
    tot = c.groupby(level=0).sum(min_count=1).sum(axis=1)
    cnt = c.groupby(level=0).count().sum(axis=1)
    k = np.sqrt(cnt)                                     # effective n per date
    out = (tot - k) / (k * (k - 1))
    return out.where(cnt >= 9)


@dataclass
class ComponentResult:
    id: str
    block: str
    raw: Optional[float]
    z: Optional[float]
    score: Optional[float]
    weight: float
    asof: Optional[str] = None
    status: str = "ok"          # ok | no_data | stale | warmup | error:<msg>  (why a component is excluded)


@dataclass
class StressResult:
    score: float
    label: str
    emoji: str
    blocks: Dict[str, float]
    components: List[ComponentResult]
    history: pd.Series = field(repr=False)
    block_history: pd.DataFrame = field(repr=False)
    chg_1d: Optional[float] = None
    chg_5d: Optional[float] = None
    chg_20d: Optional[float] = None
    pctile_all: Optional[float] = None
    coverage: float = 0.0

    def drivers(self, n: int = 6) -> List[ComponentResult]:
        valid = [c for c in self.components if c.score is not None]
        return sorted(valid, key=lambda c: c.weight * (c.score - 50), reverse=True)[:n]

    def relief(self, n: int = 3) -> List[ComponentResult]:
        valid = [c for c in self.components if c.score is not None]
        return sorted(valid, key=lambda c: c.weight * (c.score - 50))[:n]


def level_for(score: float):
    for lv in SETTINGS.get("stress_levels", []):
        if score < lv["max"]:
            return lv["label"], lv["emoji"]
    return "極端", "🚨"


class StressEngine:
    def __init__(self, market, fred) -> None:
        self.market = market
        self.fred = fred

    # ---------------- raw component series ----------------
    def _base_index(self) -> pd.DatetimeIndex:
        h = self.market.history
        return h.index[h.index.dayofweek < 5]

    def _px(self, t: str, idx) -> pd.Series:
        return self.market.series(t).reindex(idx, method="ffill", limit=5) if t in self.market.history else pd.Series(index=idx, dtype=float)

    def _fr(self, sid: str, idx) -> pd.Series:
        s = self.fred.get(sid)
        if s.empty:
            return pd.Series(index=idx, dtype=float)
        s = s.copy()
        s.index = s.index + pd.offsets.BDay(PUB_LAG.get(sid, 1))   # align to *release* date → no look-ahead
        s = s[~s.index.duplicated(keep="last")]                    # Fri+Sat both roll to Monday → keep the newest value
        return s.reindex(s.index.union(idx)).ffill(limit=FFILL_LIMIT.get(sid, 10)).reindex(idx)

    def source_last_date(self, comp: dict) -> Optional[pd.Timestamp]:
        """Date of the newest *real* observation behind a component (before any forward-fill)."""
        src, series, kind = comp["src"], comp["series"], str(comp["kind"])
        dates = []
        if kind.startswith("corr:"):
            dates = [self.market.series(t).index.max() for t in SETTINGS.group("sectors") if not self.market.series(t).empty]
            return min(dates) if dates else None
        if kind.startswith("netliq:"):
            nl = self.fred.net_liquidity()
            return None if nl.empty else nl.index.max()
        s = self.market.series(series) if src == "px" else self.fred.get(series)
        if not s.empty:
            dates.append(s.index.max())
        m = re.match(r"(rel:\d+:|ratio:)(.+)$", kind)
        if m:
            b = self.market.series(m.group(2))
            dates.append(b.index.max() if not b.empty else None)
        return None if not dates or any(d is None for d in dates) else min(dates)

    def raw_series(self, comp: dict, idx) -> pd.Series:
        src, series, kind = comp["src"], comp["series"], str(comp["kind"])
        if kind.startswith("corr:"):
            w = int(kind.split(":")[1])
            cols = [t for t in SETTINGS.group("sectors") if t in self.market.history]
            px = pd.DataFrame({t: self._px(t, idx) for t in cols})
            return avg_pairwise_corr(px, w).reindex(idx)
        if kind.startswith("netliq:"):
            n = int(kind.split(":")[1])
            nl = self.fred.net_liquidity()
            if nl.empty:
                return pd.Series(index=idx, dtype=float)
            nl = nl.copy()
            nl.index = nl.index + pd.offsets.BDay(1)
            nl = nl[~nl.index.duplicated(keep="last")]
            nl = nl.reindex(nl.index.union(idx)).ffill(limit=10).reindex(idx)
            return nl.pct_change(n, fill_method=None)
        s = self._px(series, idx) if src == "px" else self._fr(series, idx)
        if kind == "level":
            return s
        m = re.match(r"ret:(\d+)$", kind)
        if m:
            return s.pct_change(int(m.group(1)), fill_method=None)
        m = re.match(r"rel:(\d+):(.+)$", kind)
        if m:
            n, b = int(m.group(1)), self._px(m.group(2), idx)
            return s.pct_change(n, fill_method=None) - b.pct_change(n, fill_method=None)
        m = re.match(r"ratio:(.+)$", kind)
        if m:
            return s / self._px(m.group(1), idx)
        m = re.match(r"diff:(\d+)$", kind)
        if m:
            return s.diff(int(m.group(1)))
        m = re.match(r"rvol:(\d+)$", kind)                # realized volatility (annualized, log returns)
        if m:
            n = int(m.group(1))
            return _slog(s).diff().rolling(n, min_periods=int(n * 0.8)).std() * np.sqrt(252)
        m = re.match(r"dist_ma:(\d+)$", kind)
        if m:
            n = int(m.group(1))
            return s / s.rolling(n, min_periods=int(n * 0.9)).mean() - 1
        raise ValueError(f"unknown kind {kind}")

    # ---------------- composite ----------------
    def compute(self) -> Optional[StressResult]:
        if self.market.history.empty:
            return None
        idx = self._base_index()
        win = int(SETTINGS.get("stress_zscore_window", 756))
        minp = int(SETTINGS.get("stress_zscore_min", 252))
        comps = SETTINGS.get("stress_components", [])
        scores, weights, blocks, results = {}, {}, {}, []
        for c in comps:
            err = None
            try:
                raw = self.raw_series(c, idx)
            except Exception as e:  # noqa: BLE001
                err = f"{type(e).__name__}: {e}"
                raw = pd.Series(index=idx, dtype=float)
            z = rolling_z(raw, win, minp) * float(c.get("direction", 1))
            sc = pd.Series(norm_cdf(z.clip(-6, 6).fillna(np.nan)) * 100, index=idx).where(z.notna())
            # a component is only 'live' if its newest REAL observation is recent (not forward-filled)
            last_valid = raw.last_valid_index()
            src_last = self.source_last_date(c)
            max_age = STALE_DAYS.get(c["series"], 7) if c["src"] == "fred" else (12 if str(c["kind"]).startswith("netliq") else 7)
            stale = last_valid is None or src_last is None or \
                (pd.Timestamp.today().normalize() - pd.Timestamp(src_last).normalize()).days > max_age
            scores[c["id"]] = sc
            weights[c["id"]] = float(c.get("weight", 1))
            blocks.setdefault(c["block"], []).append(c["id"])
            cur_sc = None if stale or pd.isna(sc.iloc[-1]) else float(sc.iloc[-1])
            if err:
                status = f"error:{err[:80]}"
            elif last_valid is None:
                status = "no_data"
            elif stale:
                status = f"stale(最新資料 {None if src_last is None else pd.Timestamp(src_last).strftime('%Y-%m-%d')})"
            elif cur_sc is None:
                status = "warmup"
            else:
                status = "ok"
            results.append(ComponentResult(
                c["id"], c["block"],
                None if last_valid is None else float(raw.loc[last_valid]),
                None if cur_sc is None else float(z.iloc[-1]),
                cur_sc, weights[c["id"]],
                None if last_valid is None else last_valid.strftime("%Y-%m-%d"), status))

        S = pd.DataFrame(scores)
        W = pd.Series(weights)
        excluded = {r.id: r.status for r in results if r.score is None}
        if excluded != getattr(self, "_last_excluded", None):          # log only when the excluded set changes
            self._last_excluded = excluded
            if excluded:
                log.warning("SSI excluded components: %s", excluded)

        def wavg(cols):
            sub = S[cols]
            w = sub.notna().mul(W[cols], axis=1)
            return (sub.fillna(0) * W[cols]).sum(axis=1) / w.sum(axis=1).replace(0, np.nan)

        comp_hist = wavg(list(S.columns))
        # require ≥40% of total weight present for a valid historical point
        coverage_hist = S.notna().mul(W, axis=1).sum(axis=1) / W.sum()
        comp_hist = comp_hist.where(coverage_hist >= 0.4).dropna()
        block_hist = pd.DataFrame({b: wavg(ids) for b, ids in blocks.items()})

        # current score uses only non-stale components
        live = {r.id: r for r in results if r.score is not None}
        if not live:
            return None
        wl = sum(live[i].weight for i in live)
        cur = sum(live[i].weight * live[i].score for i in live) / wl
        cur_blocks = {}
        for b, ids in blocks.items():
            li = [live[i] for i in ids if i in live]
            if li:
                cur_blocks[b] = sum(x.weight * x.score for x in li) / sum(x.weight for x in li)
        label, emoji = level_for(cur)
        # like-for-like: when a component is stale it is excluded from `cur`, so the changes/percentile must be measured
        # against the history of the same live set (otherwise a stale low-score component fakes an SSI jump)
        live_hist = wavg([i for i in live if i in S.columns]).where(coverage_hist >= 0.4).dropna()
        ref = live_hist if len(live_hist) > 20 else comp_hist

        def chg(n):
            return float(cur - ref.iloc[-1 - n]) if len(ref) > n else None
        return StressResult(
            score=float(cur), label=label, emoji=emoji, blocks=cur_blocks, components=results,
            history=comp_hist, block_history=block_hist,
            chg_1d=chg(1), chg_5d=chg(5), chg_20d=chg(20),
            pctile_all=float((ref < cur).mean() * 100) if len(ref) else None,
            coverage=wl / W.sum())
