"""Alert scorecard — does the bot's warning actually precede weakness?

Every risk alert is logged with the S&P 500 level at the time. Afterwards we
measure the S&P's worst drawdown over the next N trading days and compare
the hit rate with the unconditional base rate over the last 10 years.
Alerts within 24h are merged into one episode so a noisy day can't inflate
the score."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List

import pandas as pd

from ..config import SETTINGS
from .crash_odds import forward_min_return

NY = ZoneInfo("America/New_York")
CFG = SETTINGS.get("scorecard", {})
HORIZONS = CFG.get("horizons", [{"days": 5, "drawdown": 0.02}, {"days": 20, "drawdown": 0.04}])
KIND_NAMES = {"risk": "市場風險警報", "news": "新聞風險警報"}


FAMILIES = [("ssi_level", "壓力指數升級"), ("ssi_jump", "SSI 單日跳升"), ("vix_backwardation", "VIX 期限倒掛"),
            ("gamma_flip", "Gamma 翻轉"), ("pf_dd", "持倉單日回撤"), ("playbook:", "風險劇本升級"),
            ("shock:div", "股債背離"), ("shock:", "衝擊路徑點火"), ("regime:", "避險機制失靈"), ("sigma:", "異常波動")]


def family(key: str) -> str:
    for pre, name in FAMILIES:
        if key.startswith(pre):
            return name
    return "其他"


def _episodes(rows: List[tuple]) -> List[dict]:
    eps: List[dict] = []
    last: dict = {}                                   # last episode per kind → interleaved kinds don't split episodes
    for ts, key, kind, sev, title, spx, ssi in rows:
        e = last.get(kind)
        if e is not None and ts - e["last_ts"] < 86400:
            e["n"] += 1
            e["last_ts"] = ts
            e["critical"] |= sev.startswith("🚨")
            continue
        e = {"ts": ts, "last_ts": ts, "kind": kind, "title": title, "n": 1,
             "critical": sev.startswith("🚨"), "spx": spx, "ssi": ssi}
        eps.append(e)
        last[kind] = e
    return eps


def _first_session(ts: float) -> pd.Timestamp:
    """First US close at/after the alert: same NY date if before 16:00 NY and a weekday, else next session."""
    ny = datetime.fromtimestamp(ts, NY)
    d = ny.date() if ny.hour < 16 else ny.date() + timedelta(days=1)
    return pd.Timestamp(d)


def _grade(eps: List[dict], spx: pd.Series) -> None:
    for e in eps:
        d0 = _first_session(e["ts"])
        after = spx[spx.index >= d0]                   # includes the session the alert fired in
        before = spx[spx.index < d0]
        start_px = e["spx"] or (float(before.iloc[-1]) if len(before) else None)
        e["results"] = {}
        for h in HORIZONS:
            n = h["days"]
            if start_px is None or len(after) < n:
                e["results"][n] = None                   # pending
                continue
            window = after.iloc[:n]
            mn = float(window.min() / start_px - 1)
            e["results"][n] = {"min_ret": mn * 100, "end_ret": float(window.iloc[-1] / start_px - 1) * 100,
                               "hit": mn <= -h["drawdown"]}


def _summ(eps: List[dict], base: Dict) -> Dict:
    per = {}
    for h in HORIZONS:
        done = [e["results"][h["days"]] for e in eps if e["results"].get(h["days"])]
        if done:
            hr = sum(r["hit"] for r in done) / len(done) * 100
            per[h["days"]] = {"episodes": len(done), "hit_rate": hr, "base_rate": base[h["days"]],
                              "lift": hr / base[h["days"]] if base[h["days"]] else None,
                              "avg_min": sum(r["min_ret"] for r in done) / len(done),
                              "avg_end": sum(r["end_ret"] for r in done) / len(done)}
        else:
            per[h["days"]] = {"episodes": 0, "base_rate": base[h["days"]]}
    return per


def verdict(per: Dict, min_n: int = 5) -> str:
    """Plain-language grade of one rule from its longest-horizon result."""
    r = per.get(max(per)) if per else None
    if not r or r.get("episodes", 0) < min_n:
        return "樣本不足"
    lift = r.get("lift") or 0
    return "有用" if lift >= 1.3 else ("反效果" if lift <= 0.7 else "無明顯差別")


def evaluate(rows: List[tuple], spx: pd.Series) -> Dict:
    spx = spx.dropna()
    if len(spx) < 300:
        return {"error": "標普歷史資料不足"}
    tail = spx.iloc[-2520:]                        # ~10y base rate
    base = {}
    for h in HORIZONS:
        fm = forward_min_return(tail, h["days"]).dropna()
        base[h["days"]] = float((fm <= -h["drawdown"]).mean() * 100)
    eps = _episodes(rows)
    _grade(eps, spx)
    summary = {}
    for kind in sorted({e["kind"] for e in eps}):
        ks = [e for e in eps if e["kind"] == kind]
        summary[kind] = {"episodes": len(ks), "pending": sum(1 for e in ks if any(
            v is None for v in e["results"].values())), "by_horizon": _summ(ks, base)}
    fam: Dict[str, Dict] = {}
    risk_rows = [r for r in rows if r[2] == "risk"]
    for name in sorted({family(r[1]) for r in risk_rows}):
        feps = _episodes([(ts, k, "risk", sev, title, spx_, ssi_) for ts, k, kd, sev, title, spx_, ssi_ in risk_rows if family(k) == name])
        _grade(feps, spx)
        per = _summ(feps, base)
        fam[name] = {"episodes": len(feps), "by_horizon": per, "verdict": verdict(per)}
    return {"base": base, "summary": summary, "recent": eps[-10:][::-1], "horizons": HORIZONS,
            "total_alerts": len(rows), "families": fam}
