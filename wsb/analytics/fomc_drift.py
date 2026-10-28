"""FOMC 前漂移 — how the S&P 500 behaved around scheduled FOMC decisions since 1995 (prices only, news never an input).

Windows per meeting with decision day T (trading days, closes):
  pre  = close T-6 → close T-1   (the 5 sessions before the decision day)
  day  = close T-1 → close T     (the decision day, statement at 14:00 ET)
  post = close T   → close T+5
Each is compared with every window of the same length over the same years (the base rate), with a rough t-stat on the
difference of means.  Splits: 1995–2014 vs 2015+ (the pre-announcement drift found by Lucca & Moench faded after
their 2015 paper), and VIX ≥ 20 vs < 20 at the window start.  The upcoming meeting's window is tracked as it unfolds.

Meeting dates: wsb/data/fomc_history.json (Fed historical pages, scheduled meetings only) + the live Fed calendar.
Historical frequencies, small samples — descriptive, not a forecast."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

_HIST = Path(__file__).resolve().parent.parent / "data" / "fomc_history.json"
WINS = (("pre", "會前 5 日", "5 days before"), ("day", "決議當天", "Decision day"), ("post", "會後 5 日", "5 days after"))


def history_dates() -> List[str]:
    try:
        return list(json.loads(_HIST.read_text(encoding="utf-8")).get("dates") or [])
    except Exception:  # noqa: BLE001
        return []


def _stat(x: pd.Series, base: pd.Series) -> Optional[Dict]:
    x, base = x.dropna(), base.dropna()
    if len(x) < 8 or len(base) < 50:
        return None
    sd = float(x.std(ddof=1))
    t = (x.mean() - base.mean()) / (sd / np.sqrt(len(x))) if sd > 0 else None
    return {"n": int(len(x)), "mean": float(x.mean()), "med": float(x.median()), "up": float((x > 0).mean() * 100),
            "base_mean": float(base.mean()), "base_up": float((base > 0).mean() * 100), "t": None if t is None else float(t)}


def table(spx: pd.Series, vix: pd.Series, dates: List[str]) -> pd.DataFrame:
    s = spx.dropna()
    s = s[s > 0]
    v = vix.dropna().reindex(s.index).ffill()
    idx, rows = s.index, []
    for d in sorted(set(dates)):
        t = pd.Timestamp(d)
        i = idx.searchsorted(t)
        if i >= len(idx) or idx[i] != t or i < 6:
            continue                                   # decision day not a bar in the history (or too early)
        rows.append({"date": d, "pre": (s.iloc[i - 1] / s.iloc[i - 6] - 1) * 100, "day": (s.iloc[i] / s.iloc[i - 1] - 1) * 100,
                     "post": (s.iloc[i + 5] / s.iloc[i] - 1) * 100 if i + 5 < len(s) else np.nan, "vix": v.iloc[i - 6]})
    return pd.DataFrame(rows)


def _base(s: pd.Series, v: pd.Series, k: int, start: str, end: Optional[str] = None, vix_hi: Optional[bool] = None) -> pd.Series:
    r = (s / s.shift(k) - 1) * 100
    v0 = v.shift(k)
    m = r.index >= pd.Timestamp(start)
    if end:
        m &= r.index < pd.Timestamp(end)
    if vix_hi is not None:
        m &= (v0 >= 20).values if vix_hi else (v0 < 20).values
    return r[m]


def build(eng) -> Dict:
    m = getattr(eng, "market", None)
    if m is None:
        return {"available": False}
    s, v = m.series("^GSPC"), m.series("^VIX")
    s = s[s > 0]
    live = [x["date"] for x in (getattr(getattr(eng, "econ", None), "fomc", None) or [])]
    dates = sorted(set(history_dates()) | set(live))
    df = table(s, v, dates)
    if len(df) < 20:
        return {"available": False}
    v_al = v.reindex(s.index).ffill()
    first = df["date"].iloc[0]
    k = {"pre": 5, "day": 1, "post": 5}
    groups = [("all", "全部", "All", df, first, None, None), ("old", "1995–2014", "1995–2014", df[df["date"] < "2015"], first, "2015", None),
              ("new", "2015 年後", "2015+", df[df["date"] >= "2015"], "2015-01-01", None, None),
              ("hi", "VIX ≥ 20 時", "VIX ≥ 20", df[df["vix"] >= 20], first, None, True), ("lo", "VIX < 20 時", "VIX < 20", df[df["vix"] < 20], first, None, False)]
    stats = {}
    for g, zh, en, sub, a, b, hi in groups:
        stats[g] = {"zh": zh, "en": en, **{w: _stat(sub[w], _base(s, v_al, k[w], a, b, hi)) for w, _, _ in WINS}}
    out = {"available": True, "n": int(len(df)), "first": first, "last": df["date"].iloc[-1], "stats": stats,
           "recent": df.tail(8).iloc[::-1].to_dict("records")}
    from ..data.econcal import us_today
    today = us_today().isoformat()
    nxt = next((d for d in sorted(live) if d >= today), None)
    if nxt:
        t = pd.Timestamp(nxt)
        # the same window as the history table: the close 6 trading bars before the decision day.  Bars already in the
        # data are real NYSE sessions (holidays excluded); only days still ahead fall back to weekdays
        days = list(s.index[s.index < t]) + list(pd.bdate_range(s.index[-1] + pd.Timedelta(days=1), t - pd.Timedelta(days=1)))
        start = pd.Timestamp(days[-6]).normalize() if len(days) >= 6 else (t - pd.offsets.BDay(6)).normalize()
        end = pd.Timestamp(days[-1]) if days else t - pd.offsets.BDay(1)
        out["next"] = {"date": nxt, "start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d"),
                       "vix_start": None, "so_far": None}
        if start <= s.index[-1]:
            i = s.index.searchsorted(start)
            if i < len(s):
                p0 = float(s.iloc[i])
                px, asof = float(s.iloc[-1]), s.index[-1].strftime("%Y-%m-%d")
                q = m.q("^GSPC")
                if q and q.get("price") and str(q.get("asof", ""))[:10] > asof:
                    px, asof = float(q["price"]), str(q["asof"])[:10]
                out["next"].update({"start": s.index[i].strftime("%Y-%m-%d"), "p0": p0, "px": px, "asof": asof,
                                    "so_far": (px / p0 - 1) * 100, "vix_start": float(v_al.iloc[i]) if v_al.iloc[i] == v_al.iloc[i] else None})
    return out


def _sig(st: Optional[Dict]) -> str:
    t = (st or {}).get("t")
    if t is None:
        return "樣本不足"
    return "統計上明顯" if abs(t) >= 2 else ("勉強" if abs(t) >= 1.5 else "不明顯（可能只是雜訊）")


def readings(r: Dict) -> List[Dict]:
    """Plain-language lines (zh / en) for the card and the AI context."""
    if not r.get("available"):
        return []
    S, L = r["stats"], []
    a, n = S["all"]["pre"], S["new"]["pre"]
    if a:
        L.append({"zh": f"{r['first'][:4]} 年以來 {a['n']} 次會議：會前 5 日標普平均 {a['mean']:+.2f}%、上漲機率 {a['up']:.0f}%；"
                        f"任何 5 日平均 {a['base_mean']:+.2f}%、上漲 {a['base_up']:.0f}%。差距{_sig(a)}（t={a['t']:.1f}）。",
                  "en": f"Since {r['first'][:4]} ({a['n']} meetings): pre-5-day mean {a['mean']:+.2f}%, up {a['up']:.0f}% vs any 5 days {a['base_mean']:+.2f}% / {a['base_up']:.0f}% (t={a['t']:.1f})."})
    if n:
        L.append({"zh": f"2015 年後 {n['n']} 次：會前 5 日平均 {n['mean']:+.2f}%、上漲 {n['up']:.0f}%（同期任何 5 日 {n['base_mean']:+.2f}%／{n['base_up']:.0f}%），{_sig(n)}（t={n['t']:.1f}）。",
                  "en": f"2015+ ({n['n']}): pre-5-day {n['mean']:+.2f}%, up {n['up']:.0f}% vs base {n['base_mean']:+.2f}%/{n['base_up']:.0f}% (t={n['t']:.1f})."})
    d_old, d_new = S["old"]["day"], S["new"]["day"]
    if d_old and d_new:
        L.append({"zh": f"決議當天：1995–2014 平均 {d_old['mean']:+.2f}%（平常一天 {d_old['base_mean']:+.2f}%，{_sig(d_old)}，t={d_old['t']:.1f}）＝學界說的「會前漂移」；"
                        f"2015 年後只剩 {d_new['mean']:+.2f}%、上漲 {d_new['up']:.0f}%，效果已大致消失。",
                  "en": f"Decision day: {d_old['mean']:+.2f}% in 1995–2014 (vs {d_old['base_mean']:+.2f}% a normal day); only {d_new['mean']:+.2f}% since 2015."})
    hi = S["hi"]["pre"]
    if hi:
        L.append({"zh": f"會前 VIX ≥ 20 的 {hi['n']} 次：會前 5 日平均 {hi['mean']:+.2f}%、上漲 {hi['up']:.0f}%；會後 5 日平均 "
                        f"{(S['hi']['post'] or {}).get('mean', float('nan')):+.2f}%（VIX < 20 時 {(S['lo']['post'] or {}).get('mean', float('nan')):+.2f}%）。",
                  "en": f"With VIX ≥ 20 at the start ({hi['n']}): pre {hi['mean']:+.2f}%, up {hi['up']:.0f}%."})
    nx = r.get("next")
    if nx and nx.get("so_far") is not None:
        L.append({"zh": f"這次（{nx['date'][5:]} 決議）的會前窗口從 {nx['start'][5:]} 收盤算起，到 {nx['asof'][5:]} 標普已 {nx['so_far']:+.2f}%"
                        + (f"；起點 VIX {nx['vix_start']:.1f}" if nx.get("vix_start") else "") + "。",
                  "en": f"This meeting ({nx['date']}): pre-window from {nx['start']} close, S&P {nx['so_far']:+.2f}% so far."})
    elif nx:
        L.append({"zh": f"下次決議 {nx['date'][5:]}，會前窗口 {nx['start'][5:]} 收盤開始。", "en": f"Next decision {nx['date']}; window starts {nx['start']}."})
    return [{"lv": "info", **x} for x in L]
