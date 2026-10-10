"""Holdings × transmission-path exposure: which positions get hurt most when a given shock path heats up?

For each shock path (信用事件, 利率／債市衝擊, …) the path level is the mean of its Stress-Index blocks.  Each holding's
5-trading-day log return is regressed on the 5-day change of that level over the last ~3 years (non-overlapping weeks,
so ~150 independent observations and Taiwan/US session timing washes out).  The slope is reported as "% move of the
position per +10 points of path stress", with its t-statistic, so a weak relationship is shown as weak.

This is historical co-movement, not causation; positions in TWD are measured in local currency."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS
from .shock import DEFAULT_PATHS

CFG = SETTINGS.get("exposure", {}) or {}


def _slope(x: np.ndarray, y: np.ndarray):
    """OLS slope, its t-statistic and the correlation for y = a + b·x."""
    n = len(x)
    if n < 40:
        return None
    xm, ym = x - x.mean(), y - y.mean()
    sxx = float((xm ** 2).sum())
    if sxx <= 0:
        return None
    b = float((xm * ym).sum() / sxx)
    resid = ym - b * xm
    se = float(np.sqrt((resid ** 2).sum() / (n - 2) / sxx)) if n > 2 else np.nan
    corr = float(np.corrcoef(x, y)[0, 1])
    return b, (b / se if se and np.isfinite(se) and se > 0 else None), corr, n


def path_levels(block_history: pd.DataFrame, paths: Optional[List[Dict]] = None) -> Dict[str, pd.Series]:
    paths = paths or (SETTINGS.get("shock", {}) or {}).get("paths") or DEFAULT_PATHS
    out = {}
    for p in paths:
        cols = [b for b in p["blocks"] if b in block_history.columns]
        if cols:
            out[p["name"]] = block_history[cols].mean(axis=1).dropna()
    return out


def sensitivities(prices: Dict[str, pd.Series], levels: Dict[str, pd.Series], step: int = 5,
                  lookback: int = 756) -> Dict[str, Dict[str, Dict]]:
    """{path: {sym: {sens_pct_per10, t, corr, n}}} — sens = position % move for +10 points of path level."""
    out: Dict[str, Dict[str, Dict]] = {}
    for path, lvl in levels.items():
        lvl = lvl.iloc[-lookback:]
        idx = lvl.index
        res = {}
        for sym, px in prices.items():
            s = px[px > 0]
            if s.empty:
                continue
            s = s.reindex(s.index.union(idx)).ffill(limit=5).reindex(idx)       # align to the stress calendar
            j = pd.DataFrame({"l": lvl, "p": np.log(s)}).dropna()
            j = j.iloc[::-1].iloc[::step].iloc[::-1]                           # non-overlapping, ending at the latest row
            d = j.diff().dropna()
            fit = _slope(d["l"].values, d["p"].values)
            if fit is None:
                continue
            b, t, corr, n = fit
            res[sym] = {"sens_pct_per10": float((np.exp(b * 10) - 1) * 100), "t": t, "corr": corr, "n": n}
        out[path] = res
    return out


DEFAULT_UNIVERSE = ["XLK", "SMH", "XLF", "KRE", "XLE", "XLI", "XLY", "XLP", "XLV", "XLU", "XLRE", "IWM",
                    "^TWII", "2330.TW", "EEM", "TLT", "GC=F", "BTC-USD"]


def build(engine) -> Dict:
    """Holdings mode when a portfolio is loaded (private); otherwise universe mode over sector ETFs / key assets
    (no personal data, so it can be shown publicly — e.g. when the bot runs as a public intelligence station)."""
    st = getattr(engine, "stress", None)
    if st is None:
        return {"available": False}
    pf = getattr(engine, "portfolio", None) or {}
    pos = [p for p in pf.get("positions", []) if "value_usd" in p] if not pf.get("error") else []
    mode = "portfolio" if pos else "universe"
    if mode == "universe":
        uni = [t for t in (CFG.get("universe") or DEFAULT_UNIVERSE) if not engine.market.series(t).empty]
        pos = [{"sym": t, "value_usd": 10000.0, "weight": None} for t in uni]      # equal notional, for ranking only
    if not pos:
        return {"available": False}
    names = SETTINGS.names()
    prices = {p["sym"]: engine.market.series(p["sym"]) for p in pos}
    levels = path_levels(st.block_history)
    sens = sensitivities(prices, levels, int(CFG.get("step_days", 5)), int(CFG.get("lookback_days", 756)))
    t_min = float(CFG.get("min_t", 2.0))
    channels = {r["channel"]: r for r in (getattr(engine, "intel", None) or {}).get("channels", [])}
    rows = []
    for path, by in sens.items():
        hold = []
        for p in pos:
            s = by.get(p["sym"])
            if not s:
                continue
            hold.append({"sym": p["sym"], "name": names.get(p["sym"], p["sym"]), "weight": p.get("weight"), **s,
                         "usd_per10": p["value_usd"] * s["sens_pct_per10"] / 100,
                         "significant": s["t"] is not None and abs(s["t"]) >= t_min})
        if not hold:
            continue
        ch = channels.get(path) or {}
        row = {"path": path, "state": ch.get("state"), "fused": ch.get("fused"),
               "holdings": sorted(hold, key=lambda h: h["sens_pct_per10"] if mode == "universe" else h["usd_per10"])}
        if mode == "portfolio":
            row["port_usd_per10"] = sum(h["usd_per10"] for h in hold)
            row["port_pct_per10"] = row["port_usd_per10"] / pf["total_value_usd"] * 100 if pf.get("total_value_usd") else None
        else:
            row["port_usd_per10"] = row["port_pct_per10"] = None
        rows.append(row)
    # most dangerous first: active paths (確認/無聲壓力/敘事領先), then the biggest loss per +10 points
    active = {"確認": 0, "無聲壓力": 1, "敘事領先": 2}
    rows.sort(key=lambda r: (active.get(r["state"], 3),
                             r["port_usd_per10"] if r["port_usd_per10"] is not None else r["holdings"][0]["sens_pct_per10"]))
    note = "歷史共同變動（每週、近 3 年），不是因果；台股以新台幣價格計算"
    if mode == "universe":
        note = "未載入個人持倉：改看產業 ETF 與重點資產。" + note
    return {"available": bool(rows), "mode": mode, "paths": rows, "t_min": t_min, "note": note}


def summary_lines(exp: Dict, n_paths: int = 6, n_hold: int = 3) -> List[str]:
    """Compact text for the DATA PACK / embeds."""
    out = []
    uni = (exp or {}).get("mode") == "universe"
    fmt_h = lambda h: f"{h['name'] if uni else h['sym']} {h['sens_pct_per10']:+.1f}%" + ("" if h["significant"] else "(弱)")  # noqa: E731
    for r in (exp or {}).get("paths", [])[:n_paths]:
        if uni:
            worst = [h for h in r["holdings"] if h["sens_pct_per10"] < 0][:n_hold]
            best = [h for h in reversed(r["holdings"]) if h["sens_pct_per10"] > 0 and h["significant"]][:2]
            out.append(f"{r['path']}［{r['state'] or 'NA'}］路徑壓力 +10 點 → 最受傷："
                       + (", ".join(fmt_h(h) for h in worst) or "無") + ("；相對抗跌：" + ", ".join(fmt_h(h) for h in best) if best else ""))
            continue
        worst = [h for h in r["holdings"] if h["usd_per10"] < 0][:n_hold]
        pct = f"{r['port_pct_per10']:+.2f}%" if r["port_pct_per10"] is not None else "NA"
        out.append(f"{r['path']}［{r['state'] or 'NA'}］路徑壓力 +10 點 → 持倉 {pct}（${r['port_usd_per10']:+,.0f}）"
                   + (f"；最受傷：{', '.join(fmt_h(h) for h in worst)}" if worst else "；無明顯受傷部位"))
    return out
