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
    hi252 = c.rolling(252, min_periods=120).max()
    lo10 = c.rolling(10).min()
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
                               "ma20": ma20, "ma50": ma50, "ma200": ma200, "hi20": hi20, "hi252": hi252, "lo10": lo10,
                               "touch50": t50 & (c > ma50)})
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


STATUS = {"signal": ("有買點訊號", "Signal active"), "near_pullback": ("接近回檔買點", "Near pullback entry"),
          "near_breakout": ("接近突破", "Near breakout"), "near_golden": ("接近黃金交叉", "Near golden cross"),
          "near_oversold": ("接近超賣", "Near oversold"), "extended": ("多頭但漲多", "Uptrend, extended"),
          "uptrend": ("多頭整理", "Uptrend, consolidating"), "range": ("盤整、無明確型態", "Range-bound"),
          "downtrend": ("空頭趨勢", "Downtrend"), "nodata": ("資料不足", "Not enough history")}


def plan(k: str, df: pd.DataFrame, trig_i, inv: float) -> Dict:
    """Rule-based entry reference for an ACTIVE signal: the price zone the rule regards as the entry area, where the
    setup fails, and the nearest overhead resistance (52-week high) with the resulting reward/risk multiple."""
    last, t = df.iloc[-1], df.loc[trig_i]
    px = float(last["close"])
    if k == "pullback":
        sup = float(t["ma50"] if bool(t.get("touch50")) else t["ma20"])
        lo, hi, zh, en = sup, sup * 1.03, f"回測的均線 {sup:.2f} 到 +3%（{sup * 1.03:.2f}）之間", f"{sup:.2f}–{sup * 1.03:.2f} (the moving average it bounced off, +3%)"
    elif k == "breakout":
        lvl = float(t["hi20"])
        lo, hi, zh, en = lvl, lvl * 1.03, f"突破點 {lvl:.2f} 到 +3%（回測突破點不破）", f"{lvl:.2f}–{lvl * 1.03:.2f} (a retest of the breakout level)"
    elif k == "golden":
        m = float(last["ma200"])
        lo, hi, zh, en = m, m * 1.04, f"200 日線 {m:.2f} 到 +4%（站穩年線）", f"{m:.2f}–{m * 1.04:.2f} (holding above the 200-day)"
    else:
        lo10 = float(last["lo10"])
        lo, hi, zh, en = lo10, lo10 * 1.04, f"10 日低點 {lo10:.2f} 到 +4%（逆勢，只宜小量）", f"{lo10:.2f}–{lo10 * 1.04:.2f} (counter-trend, small size only)"
    where = ("現價在參考區內" if lo <= px <= hi else f"現價高於參考區 {((px / hi - 1) * 100):.1f}%，回到區間內較符合規則" if px > hi
             else f"現價低於參考區 {((px / lo - 1) * 100):.1f}%，需重新站回")
    where_en = ("price is inside the zone" if lo <= px <= hi else f"price is {((px / hi - 1) * 100):.1f}% above the zone" if px > hi
                else f"price is {((px / lo - 1) * 100):.1f}% below the zone")
    h52 = float(last["hi252"]) if pd.notna(last["hi252"]) else None
    tgt = h52 if h52 and h52 > px * 1.01 else None
    rr = (tgt - px) / (px - inv) if tgt and inv and px > inv else None
    return {"zone_lo": lo, "zone_hi": hi, "zone": zh, "zone_en": en, "in_zone": lo <= px <= hi, "where": where, "where_en": where_en,
            "target": tgt, "target_pct": (tgt / px - 1) * 100 if tgt else None, "rr": rr}


def trigger_text(k: str, df: pd.DataFrame) -> tuple:
    """For a stock WITHOUT a signal: the concrete condition that would turn it into one (with today's price levels)."""
    last = df.iloc[-1]
    g = lambda c: float(last[c]) if pd.notna(last[c]) else float("nan")  # noqa: E731
    m20, m50, m200, h20 = g("ma20"), g("ma50"), g("ma200"), g("hi20")
    return {
        "near_pullback": (f"等股價回到 20 日線 {m20:.2f}（或 50 日線 {m50:.2f}）附近、止跌收紅 → 成立「多頭回檔」",
                          f"Wait for a dip to the 20-day {m20:.2f} (or 50-day {m50:.2f}) and an up close"),
        "near_breakout": (f"收盤站上 {h20:.2f}（前 20 日高點）且成交量 ≥ 1.5 倍均量 → 成立「帶量突破」",
                          f"A close above {h20:.2f} (20-day high) on ≥1.5× volume"),
        "near_golden": (f"50 日線（{m50:.2f}）上穿 200 日線（{m200:.2f}）→ 成立「黃金交叉」", f"50-day {m50:.2f} crossing above the 200-day {m200:.2f}"),
        "near_oversold": ("RSI 跌破 30 後站回 5 日線 → 成立「超賣反彈」（逆勢）", "RSI below 30, then a close back above the 5-day"),
        "uptrend": (f"回測 20 日線 {m20:.2f} 止跌，或放量突破 {h20:.2f}，才會出現買點", f"A dip to {m20:.2f} that holds, or a volume break above {h20:.2f}"),
        "extended": (f"離均線太遠，規則上等回到 20 日線 {m20:.2f} 附近再看", f"Too stretched — the rules wait for a return toward {m20:.2f}"),
        "range": (f"放量突破 {h20:.2f}，或站上 200 日線 {m200:.2f}，才會出現買點", f"A volume break above {h20:.2f} or a reclaim of the 200-day {m200:.2f}"),
        "downtrend": (f"空頭：站回 200 日線 {m200:.2f} 之前，規則不給順勢買點", f"Downtrend: no trend-following entry until it reclaims the 200-day {m200:.2f}"),
    }.get(k, ("—", "—"))


def status(df: pd.DataFrame) -> Dict:
    """Where a stock without an active signal stands, judged from its latest bar (a watch-list status, not a signal)."""
    last = df.iloc[-1]
    c, m20, m50, m200, r, hi = (last.get(k) for k in ("close", "ma20", "ma50", "ma200", "rsi", "hi20"))
    d = lambda a, b: (a / b - 1) * 100 if pd.notna(a) and pd.notna(b) and b else None  # noqa: E731
    d20, d50, d200, dhi = d(c, m20), d(c, m50), d(c, m200), d(c, hi)
    m50_200 = d(m50, m200)
    pc = lambda x: "—" if x is None else f"{x + 0.0:+.1f}%".replace("-0.0%", "0.0%")  # noqa: E731
    m50_prev = df["ma50"].iloc[-6] if len(df) > 6 else np.nan
    up = d200 is not None and d200 > 0 and m50_200 is not None and m50_200 > 0
    if up and ((d20 is not None and 0 <= d20 <= 3) or (d50 is not None and 0 <= d50 <= 3)):
        k, rs = "near_pullback", (f"多頭，距 20 日線 {pc(d20)}、50 日線 {pc(d50)}，等待回測止跌",
                                  f"Uptrend, {pc(d20)} vs 20-day / {pc(d50)} vs 50-day — waiting for a bounce")
    elif dhi is not None and -2 <= dhi <= 0 and d50 is not None and d50 > 0:
        k, rs = "near_breakout", (f"距前 20 日高點 {pc(dhi)}，等待放量突破", f"{pc(dhi)} below the 20-day high — waiting for a volume breakout")
    elif m50_200 is not None and -2 <= m50_200 < 0 and pd.notna(m50_prev) and m50 > m50_prev:
        k, rs = "near_golden", (f"50 日線在 200 日線下方 {pc(m50_200)} 且上彎", f"50-day {pc(m50_200)} below the 200-day and rising")
    elif r is not None and pd.notna(r) and r < 35:
        k, rs = "near_oversold", (f"RSI {r:.0f}，接近超賣但尚未止跌", f"RSI {r:.0f}, near oversold, no bounce yet")
    elif up and d50 is not None and d50 > 10:
        k, rs = "extended", (f"多頭，但距 50 日線 {pc(d50)}（追高風險較大）", f"Uptrend but {pc(d50)} above the 50-day (stretched)")
    elif up:
        k, rs = "uptrend", (f"多頭整理，距 50 日線 {pc(d50)}", f"Uptrend, {pc(d50)} vs 50-day")
    elif d200 is not None and d200 < 0 and m50_200 is not None and m50_200 < 0:
        k, rs = "downtrend", (f"空頭趨勢，在 200 日線下方 {pc(d200)}", f"Downtrend, {pc(d200)} below the 200-day")
    else:
        k, rs = "range", (f"盤整，距 200 日線 {pc(d200)}" if d200 is not None else "盤整", "Range-bound")
    base = {"near_pullback": 45, "near_breakout": 42, "near_golden": 38, "uptrend": 35, "near_oversold": 30, "extended": 25,
            "range": 20, "downtrend": 10}[k]
    return {"status": k, "label": STATUS[k][0], "label_en": STATUS[k][1], "why": rs[0], "why_en": rs[1], "base": base,
            "d20": d20, "d50": d50, "d200": d200, "price": float(c) if pd.notna(c) else None}


def evaluate(pats: Dict[str, pd.DataFrame], score: Optional[float], base: Dict[str, float], lookback: int = 3,
             bt: Optional[Dict] = None, br: Optional[float] = None) -> List[Dict]:
    """Active signals of one stock (triggered within `lookback` sessions, not yet failed, not run away), strongest first."""
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
        if score is not None:
            s += 0.35 * (score - 50)
        if k == "breakout" and pd.notna(df.loc[trig_i, "vol_ratio"]):
            s += min(10.0, max(0.0, (float(df.loc[trig_i, "vol_ratio"]) - 1.5) * 8))
        s += 5 if 2 <= risk <= 6 else (-5 if risk > 10 else 0)
        b = (bt or {}).get(k) or {}
        if b.get("n", 0) >= 15 and b.get("win") is not None and b.get("base_win") is not None:
            s += float(np.clip((b["win"] - b["base_win"]) * 0.5, -8, 8))
        if br is not None and br < 40 and k != "oversold":
            s -= 5
        hits.append({"pattern": k, "label": PATTERNS[k][0], "label_en": PATTERNS[k][1], "strength": float(np.clip(s, 0, 100)),
                     "inv": inv, "risk_pct": risk, "trigger": trig_i.strftime("%Y-%m-%d"), "since": trig_i.strftime("%Y-%m-%d"),
                     "plan": plan(k, df, trig_i, inv),
                     "vol_ratio": None if pd.isna(df.loc[trig_i, "vol_ratio"]) else float(df.loc[trig_i, "vol_ratio"]),
                     "rsi": None if pd.isna(last["rsi"]) else float(last["rsi"])})
    return sorted(hits, key=lambda h: -h["strength"])


def build(eng, uni: Optional[Dict] = None, persist: bool = True) -> Dict:
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
    for mk, u in (uni or universe()).items():
        rows_by = {r["sym"]: r for r in (sc.get(mk) or {}).get("rows", [])}
        series, short = {}, []
        for sym in u["symbols"]:
            cl = sp.series(sym)
            if len(cl) < 230:
                short.append(sym)
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
            srow = rows_by.get(sym)
            hits = evaluate(pats, srow["score"] if srow else None, base, lookback, bt, br)
            for h in hits:
                key = f"{sym}:{h['pattern']}"
                first = seen.get(key) if seen.get(key, "") >= _days_ago(asof, 10) else None
                seen[key] = first or h["trigger"]
                h["since"] = seen[key]
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
        # every other stock too: where it stands (watch-list status), so the page covers the whole universe
        have = {r["sym"] for r in out_rows}
        rest = []
        for sym in list(series) + short:
            if sym in have:
                continue
            zh, en = u["symbols"][sym]
            srow = rows_by.get(sym) or {}
            if sym in series:
                df0 = next(iter(series[sym].values()))
                st = status(df0)
                st["when"], st["when_en"] = trigger_text(st["status"], df0)
                ready = float(np.clip(st["base"] + 0.25 * ((srow.get("score") or 50) - 50), 0, 60))
            else:
                st = {"status": "nodata", "label": STATUS["nodata"][0], "label_en": STATUS["nodata"][1], "why": "上市或掛牌未滿約一年，均線資料不足",
                      "why_en": "Less than ~1 year of history", "price": float(sp.series(sym).iloc[-1]) if len(sp.series(sym)) else None}
                ready = 0.0
            rest.append({"sym": sym, "code": sym.split(".")[0], "name": zh, "name_en": en, "theme": u["themes"].get(sym, "其他"),
                         "strength": round(ready, 1), "status": st, "price": st.get("price"), "score": srow.get("score"),
                         "r1m": srow.get("r1m"), "signal": False})
        rest.sort(key=lambda r: -r["strength"])
        allrows = [{**r, "signal": True, "status": {"status": "signal", "label": STATUS["signal"][0], "label_en": STATUS["signal"][1]}}
                   for r in out_rows] + rest
        for i, r in enumerate(allrows, 1):
            r["rank_all"] = i
        markets[mk] = {"key": mk, "label": u.get("label", mk), "label_en": u.get("label_en", mk), "rows": out_rows, "all": allrows,
                       "backtest": bt, "asof": asof, "n_universe": len(series) + len(short), "breadth": br,
                       "status_counts": {k: sum(1 for r in allrows if r["status"]["status"] == k) for k in STATUS}}
    if persist:
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
