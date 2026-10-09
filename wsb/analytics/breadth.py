"""Sector rotation & market breadth.

* Sector relative strength: each SPDR sector ETF's return minus the S&P 500 over 1 week / 1 / 3 / 6 months.
* Rotation map (a simplified relative-rotation graph): x = 3-month relative return (where a sector stands),
  y = last month's relative return minus a third of the 3-month one (where it is heading).
  Quadrants: 領先 leading (+,+) · 轉弱 weakening (+,−) · 落後 lagging (−,−) · 改善 improving (−,+).
* Breadth: share of the scoring universe above its 200-day average, over time; equal-weight vs cap-weight S&P."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from ..config import SETTINGS
from ..data.stocks import universe


def _cfg() -> Dict:
    return SETTINGS.get("breadth", {}) or {}


def _ret(s: pd.Series, n: int) -> Optional[float]:
    s = s.dropna()
    return float(s.iloc[-1] / s.iloc[-1 - n] - 1) * 100 if len(s) > n and s.iloc[-1 - n] > 0 else None


def pct_above(close: pd.DataFrame, n: int = 200, days: int = 260) -> pd.Series:
    """Share (%) of columns trading above their own n-day average, per day (needs ≥60% of names with data)."""
    close = close.dropna(how="all")                 # only this market's own sessions (no holiday rows from other markets)
    if close.empty:
        return pd.Series(dtype=float)
    close = close.ffill(limit=3)
    ma = close.rolling(n, min_periods=n).mean()
    ok = ma.notna() & close.notna()
    above = (close > ma) & ok
    cnt = ok.sum(axis=1)
    out = (above.sum(axis=1) / cnt.where(cnt >= max(5, int(close.shape[1] * 0.6))) * 100).dropna()
    return out.tail(days)


def build(eng) -> Dict:
    m = eng.market
    bench_sym = _cfg().get("bench", "SPY")
    bench = m.series(bench_sym)
    if bench.empty:
        bench_sym, bench = "^GSPC", m.series("^GSPC")
    wins = _cfg().get("windows") or {"1週": 5, "1月": 21, "3月": 63, "6月": 126}
    rows: List[Dict] = []
    for t in _cfg().get("sectors", []):
        s = m.series(t)
        if len(s) < 130 or bench.empty:
            continue
        j = pd.concat([s, bench], axis=1, join="inner").dropna()
        rel = {k: (None if _ret(j.iloc[:, 0], n) is None or _ret(j.iloc[:, 1], n) is None
                   else _ret(j.iloc[:, 0], n) - _ret(j.iloc[:, 1], n)) for k, n in wins.items()}
        abs_ = {k: _ret(j.iloc[:, 0], n) for k, n in wins.items()}
        x, r1 = rel.get("3月"), rel.get("1月")
        y = None if x is None or r1 is None else r1 - x * 21 / 63
        quad = None if x is None or y is None else ("領先" if x >= 0 and y >= 0 else "轉弱" if x >= 0 else "落後" if y < 0 else "改善")
        rows.append({"sym": t, "name": SETTINGS.names().get(t, t), "rel": rel, "abs": abs_, "x": x, "y": y, "quad": quad})
    rows.sort(key=lambda r: -(r["rel"].get("3月") or -1e9))
    sp = getattr(eng, "stockprices", None)
    hist = {}
    if sp is not None and not sp.close.empty:
        for mk, u in universe().items():
            cols = [c for c in u["symbols"] if c in sp.close.columns]
            if len(cols) >= 5:
                sub = sp.close[cols].dropna(how="all")
                h = pct_above(sub)
                if len(h) and (sub.index[-1] - h.index[-1]).days <= 7:     # never show a stale reading as "now"
                    hist[mk] = {"label": u.get("label", mk), "label_en": u.get("label_en", mk), "series": h,
                                "now": float(h.iloc[-1])}
    rsp, spy = m.series("RSP"), m.series("SPY") if not m.series("SPY").empty else m.series("^GSPC")
    ew = None
    if len(rsp) > 260 and len(spy) > 260:
        j = pd.concat([rsp, spy], axis=1, join="inner").dropna().tail(260)
        ratio = j.iloc[:, 0] / j.iloc[:, 1]
        ratio = ratio / ratio.iloc[0] * 100
        ew = {"series": ratio, "chg_3m": _ret(ratio, 63)}
    return {"available": bool(rows) or bool(hist), "sectors": rows, "windows": list(wins), "bench": bench_sym,
            "breadth": hist, "equal_weight": ew}


def summary_lines(b: Dict) -> List[str]:
    if not b or not b.get("available"):
        return []
    L = []
    if b.get("sectors"):
        lead = [r for r in b["sectors"] if r["quad"] == "領先"]
        lag = [r for r in b["sectors"] if r["quad"] == "落後"]
        L.append("類股輪動（相對標普 3 個月）：領先 " + ("、".join(f"{r['name']} {r['rel']['3月']:+.1f}" for r in lead[:4]) or "無")
                 + "；落後 " + ("、".join(f"{r['name']} {r['rel']['3月']:+.1f}" for r in lag[:4]) or "無"))
    for v in b.get("breadth", {}).values():
        L.append(f"{v['label']}評分池站上 200 日線比例 {v['now']:.0f}%")
    if b.get("equal_weight") and b["equal_weight"].get("chg_3m") is not None:
        L.append(f"等權重 vs 市值加權標普 3 個月 {b['equal_weight']['chg_3m']:+.1f}%（負值＝漲勢集中在少數大型股）")
    return L
