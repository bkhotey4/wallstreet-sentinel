"""Technical entry-signal screen (技術面買點訊號) for the stock-scoring universe — rules, not recommendations.

Four patterns, all computed from daily closes and volume:
    pullback   多頭回檔到均線   uptrend (price > 200-day, 50 > 200, 200-day rising) that dipped ≥3% to the 20- or 50-day
                                average in the last 3 sessions and is turning up again (RSI 40–62)
    breakout   帶量突破         close above the prior 20-day high on ≥1.5× the 50-day average volume, above the 50-day
    golden     黃金交叉         50-day crossed above the 200-day in the last 10 sessions, or price reclaimed the
                                200-day after spending most of the previous month below it
    oversold   超賣反彈（逆勢） RSI(14) below 30 within the last 5 sessions, now back above the 5-day average (or a ≥3%
                                up day above the close two sessions ago) — counter-trend, higher risk, flagged as such
Each signal carries an invalidation line (訊號失效線): a close below it means the pattern has failed.

Strength (0–100) = pattern base + stock composite score tilt + volume / risk-distance tweaks + the pattern's own
historical edge in that market (back-test over the cached ~2 years: share of first-day signals up 20 sessions
later vs the same market's all-day base rate).  The back-test is small-sample and in-sample — shown with its n."""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS
from ..data.stocks import universe

log = logging.getLogger(__name__)
_SEEN = DATA_DIR / "signals_seen.json"
PATTERNS = {"pullback": ("多頭回檔到均線", "Pullback to MA in uptrend"), "breakout": ("帶量突破", "Volume breakout"),
            "golden": ("黃金交叉／站回年線", "Golden cross / 200-day reclaim"), "oversold": ("超賣反彈（逆勢）", "Oversold bounce (counter-trend)")}
HORIZON = 20


def _cfg() -> Dict:
    return SETTINGS.get("signals", {}) or {}


def rsi_series(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def detect(c: pd.Series, v: pd.Series) -> Dict[str, pd.DataFrame]:
    """Boolean flag + invalidation-line series for every pattern over the whole history of one stock."""
    c = c[c > 0].dropna()
    v = v.reindex(c.index).fillna(0) if len(v) else pd.Series(0.0, index=c.index)
    ma5, ma20, ma50, ma200 = (c.rolling(n, min_periods=n).mean() for n in (5, 20, 50, 200))
    r = rsi_series(c)
    vavg = v.rolling(50, min_periods=30).mean()
    hi20 = c.rolling(20).max().shift(1)
    lo3 = c.rolling(3).min()
    up_day = c > c.shift(1)
    trend = (c > ma200) & (ma50 > ma200) & (ma200 > ma200.shift(20))
    t20, t50 = lo3 <= ma20 * 1.01, lo3 <= ma50 * 1.015
    dip = c.rolling(10).max() / lo3 - 1 >= 0.03                       # a real pullback (≥3% off the 10-day high), not drift
    pb = trend & up_day & dip & r.between(40, 62) & ((t20 & (c > ma20)) | (t50 & (c > ma50)))
    pb_inv = (ma50.where(t50 & (c > ma50), ma20)) * 0.98
    bo = (c > hi20) & (v >= 1.5 * vavg) & (c > ma50) & (vavg > 0)
    bo_inv = hi20 * 0.97
    cross = ((ma50 > ma200) & (ma50.shift(1) <= ma200.shift(1))).astype(float).rolling(10, min_periods=1).max() > 0
    below_before = (c.shift(1) < ma200.shift(1)).astype(float).rolling(20, min_periods=20).sum() >= 15
    reclaim = ((c > ma200) & (c.shift(1) <= ma200.shift(1)) & below_before).astype(float).rolling(3, min_periods=1).max() > 0
    gc = (cross | reclaim) & (c > ma200)
    gc_inv = ma200 * 0.98
    thrust = (c / c.shift(1) - 1 >= 0.03) & (c > c.shift(2))          # a strong up day after a slide also counts as "turning"
    os_ = (r.rolling(5, min_periods=1).min() < 30) & ((c > ma5) | thrust) & up_day
    os_inv = c.rolling(10).min() * 0.99
    vol_ratio = (v / vavg).replace([np.inf, -np.inf], np.nan)
    out = {}
    for k, flag, inv in (("pullback", pb, pb_inv), ("breakout", bo, bo_inv), ("golden", gc, gc_inv), ("oversold", os_, os_inv)):
        out[k] = pd.DataFrame({"flag": flag.fillna(False).astype(bool), "inv": inv, "close": c, "rsi": r, "vol_ratio": vol_ratio,
                               "ma20": ma20, "ma50": ma50, "ma200": ma200, "hi20": hi20})
    return out


def backtest(series: Dict[str, Dict[str, pd.DataFrame]], horizon: int = HORIZON) -> Dict[str, Dict]:
    """Forward `horizon`-session return after the FIRST day of each signal, pooled over one market's stocks."""
    fwd_all, by = [], {k: [] for k in PATTERNS}
    for sym, pats in series.items():
        c = next(iter(pats.values()))["close"]
        fwd = (c.shift(-horizon) / c - 1) * 100
        valid = fwd.notna() & next(iter(pats.values()))["ma200"].notna()
        fwd_all.append(fwd[valid])
        for k, df in pats.items():
            first = df["flag"] & ~df["flag"].shift(1, fill_value=False)
            by[k].append(fwd[first & valid])
    base = pd.concat(fwd_all) if fwd_all else pd.Series(dtype=float)
    base_win = float((base > 0).mean() * 100) if len(base) else None
    out = {}
    for k, parts in by.items():
        x = pd.concat(parts) if parts else pd.Series(dtype=float)
        out[k] = {"n": int(len(x)), "win": float((x > 0).mean() * 100) if len(x) else None,
                  "avg": float(x.mean()) if len(x) else None, "median": float(x.median()) if len(x) else None,
                  "base_win": base_win, "base_avg": float(base.mean()) if len(base) else None, "horizon": horizon}
    return out


def build(eng) -> Dict:
    c = _cfg()
    if not c.get("enabled", True):
        return {"available": False}
    sp = getattr(eng, "stockprices", None)
    if sp is None or sp.close.empty:
        return {"available": False}
    sc = ((getattr(eng, "scores", None) or {}).get("markets") or {})
    base = {"pullback": 60, "breakout": 62, "golden": 55, "oversold": 45, **(c.get("base") or {})}
    lookback = int(c.get("active_days", 3))
    seen = _load_seen()
    markets: Dict[str, Dict] = {}
    for mk, u in universe().items():
        rows_by = {r["sym"]: r for r in (sc.get(mk) or {}).get("rows", [])}
        series = {}
        for sym in u["symbols"]:
            cl = sp.series(sym)
            if len(cl) < 230:
                continue
            try:
                series[sym] = detect(cl, sp.vol(sym))
            except Exception:  # noqa: BLE001
                log.exception("signal detect %s", sym)
        if not series:
            continue
        bt = backtest(series)
        br = ((sc.get(mk) or {}).get("breadth") or {}).get("above200")
        asof = max(next(iter(p.values())).index[-1] for p in series.values()).strftime("%Y-%m-%d")
        out_rows = []
        for sym, pats in series.items():
            hits = []
            for k, df in pats.items():
                tail = df.tail(lookback)
                if not tail["flag"].any():
                    continue
                trig_i = tail.index[tail["flag"].values][-1]
                last = df.iloc[-1]
                inv = float(df.loc[trig_i, "inv"]) if pd.notna(df.loc[trig_i, "inv"]) else None
                px, trig_px = float(last["close"]), float(df.loc[trig_i, "close"])
                if inv is None or px <= inv or px > trig_px * 1.05:      # failed already, or ran away from the entry
                    continue
                risk = (px / inv - 1) * 100
                s = base[k]
                srow = rows_by.get(sym)
                if srow:
                    s += 0.35 * (srow["score"] - 50)
                if k == "breakout" and pd.notna(df.loc[trig_i, "vol_ratio"]):
                    s += min(10.0, max(0.0, (float(df.loc[trig_i, "vol_ratio"]) - 1.5) * 8))
                s += 5 if 2 <= risk <= 6 else (-5 if risk > 10 else 0)
                b = bt.get(k) or {}
                if b.get("n", 0) >= 15 and b.get("win") is not None and b.get("base_win") is not None:
                    s += float(np.clip((b["win"] - b["base_win"]) * 0.5, -8, 8))
                if br is not None and br < 40 and k != "oversold":
                    s -= 5
                key = f"{sym}:{k}"
                first = seen.get(key) if seen.get(key, "") >= _days_ago(asof, 10) else None
                seen[key] = first or trig_i.strftime("%Y-%m-%d")
                hits.append({"pattern": k, "label": PATTERNS[k][0], "label_en": PATTERNS[k][1], "strength": float(np.clip(s, 0, 100)),
                             "inv": inv, "risk_pct": risk, "since": seen[key], "trigger": trig_i.strftime("%Y-%m-%d"),
                             "vol_ratio": None if pd.isna(df.loc[trig_i, "vol_ratio"]) else float(df.loc[trig_i, "vol_ratio"]),
                             "rsi": None if pd.isna(last["rsi"]) else float(last["rsi"])})
            if not hits:
                continue
            hits.sort(key=lambda h: -h["strength"])
            top = hits[0]
            strength = min(100.0, top["strength"] + 5 * (len(hits) - 1))
            srow = rows_by.get(sym) or {}
            zh, en = u["symbols"][sym]
            out_rows.append({"sym": sym, "code": sym.split(".")[0], "name": zh, "name_en": en, "theme": u["themes"].get(sym, "其他"),
                             "strength": round(strength, 1), "patterns": hits, "price": float(pats[top["pattern"]]["close"].iloc[-1]),
                             "inv": top["inv"], "risk_pct": top["risk_pct"], "score": srow.get("score"), "r1m": srow.get("r1m"),
                             "new": top["since"] >= asof, "since": top["since"]})
        out_rows.sort(key=lambda r: -r["strength"])
        for i, r in enumerate(out_rows, 1):
            r["rank"] = i
        markets[mk] = {"key": mk, "label": u.get("label", mk), "label_en": u.get("label_en", mk), "rows": out_rows,
                       "backtest": bt, "asof": asof, "n_universe": len(series), "breadth": br}
    _save_seen(seen)
    return {"available": bool(markets), "markets": markets, "horizon": HORIZON}


def _days_ago(asof: str, n: int) -> str:
    return (pd.Timestamp(asof) - pd.Timedelta(days=n)).strftime("%Y-%m-%d")


def _load_seen() -> Dict[str, str]:
    try:
        if _SEEN.exists():
            return json.loads(_SEEN.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    return {}


def _save_seen(seen: Dict[str, str]) -> None:
    cut = (pd.Timestamp.today() - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
    try:
        _SEEN.write_text(json.dumps({k: v for k, v in seen.items() if v >= cut}, separators=(",", ":")), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log.warning("signals state not saved: %s", e)


def summary_lines(res: Dict, top: int = 5) -> List[str]:
    if not res or not res.get("available"):
        return []
    L = []
    for m in res["markets"].values():
        rows = m["rows"][:top]
        if rows:
            L.append(f"{m['label']}技術面訊號（強→弱）：" + "、".join(f"{r['name']}({r['code']}) {r['patterns'][0]['label']} {r['strength']:.0f}"
                                                     for r in rows))
    return L
