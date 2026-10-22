"""產業體檢（第二層）— the real economy behind each sector, from official FRED series (settings: real_economy).

For each series: the latest reading, its change over a year (growth rate for levels, percentage-point change for
rates), the direction of the last three months, and where that one-year change sits in the series' own last ten
years (percentile).  "Weakening" / "strengthening" is decided by the sign of the one-year change against the
series' good direction, and called "notable" only when that change is in the outer quarter of its own history.
Licensed series (fred_restricted) show direction and percentile only — never the raw level.
Descriptive, not a forecast; series are published with a lag (monthly / quarterly), shown next to each one."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from ..config import SETTINGS
from ..data import fred as FR


def _yoy(s: pd.Series, kind: str) -> pd.Series:
    """One-year change on the series' own calendar (works for weekly, monthly and quarterly data)."""
    prev = s.reindex(s.index - pd.DateOffset(years=1), method="nearest", tolerance=pd.Timedelta(days=20))
    prev.index = s.index
    return (s / prev - 1) * 100 if kind == "pct" else (s - prev)


def one(s: pd.Series, good: str, kind: str) -> Optional[Dict]:
    s = s.dropna().sort_index()
    if len(s) < 8:
        return None
    y = _yoy(s, kind).dropna()
    if not len(y):
        return None
    last, now = s.index[-1], float(y.iloc[-1])
    ten = y[y.index >= last - pd.DateOffset(years=10)]
    pct = float((ten < now).mean() * 100) if len(ten) > 8 else None
    three = s[s.index >= last - pd.DateOffset(months=3)]
    trend = float(three.iloc[-1] - three.iloc[0]) if len(three) > 1 else None
    sign = 1 if good == "up" else -1
    better = now * sign > 0
    # unusual = in the outer quarter of its own 10 years AND meaningfully away from the typical value
    # (a series that grows the same every year must not be ranked by floating-point noise)
    med = float(ten.median()) if len(ten) else now
    iqr = float(ten.quantile(0.75) - ten.quantile(0.25)) if len(ten) > 8 else 0.0
    away = abs(now - med) > max(0.5 * iqr, 1e-6 * max(1.0, abs(med)))
    notable = pct is not None and (pct >= 75 or pct <= 25) and away
    state = ("better" if better else "worse") if (notable and abs(now) > 0) else "neutral"
    return {"date": last.strftime("%Y-%m-%d"), "value": float(s.iloc[-1]), "yoy": now, "pct": pct,
            "trend": trend, "trend_good": None if trend is None or trend == 0 else (trend * sign > 0), "state": state}


def build(eng) -> Dict:
    fr = getattr(eng, "fred", None)
    cfg = SETTINGS.get("real_economy") or {}
    if fr is None or not cfg:
        return {"available": False}
    out: List[Dict] = []
    for sector, series in cfg.items():
        rows = []
        for sid, meta in (series or {}).items():
            try:
                r = one(fr.get(sid), meta.get("good", "up"), meta.get("kind", "pct"))
            except Exception:  # noqa: BLE001
                r = None
            if r:
                if FR.restricted(sid):
                    r["value"] = None                     # licensed: no raw level on the page
                    r["licensed"] = True
                rows.append({"id": sid, "zh": meta.get("zh", sid), "en": meta.get("en", sid), "kind": meta.get("kind", "pct"), **r})
        if rows:
            worse, better = sum(r["state"] == "worse" for r in rows), sum(r["state"] == "better" for r in rows)
            out.append({"sector": sector, "rows": rows, "worse": worse, "better": better,
                        "tone": "worse" if worse > better else "better" if better > worse else "mixed"})
    return {"available": bool(out), "sectors": out}
