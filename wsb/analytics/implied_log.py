"""財報跳空成績單 — was the options-implied earnings move right?

Before each report (the 財報前隱含波動 rows, next 14 days) the latest implied move is kept; once the report is out the
actual two-session move (close before the report → close the session after, the same window the straddle covers) is
filled in.  If the options market prices the move fairly, the implied move ≈ the expected absolute move (≈ 0.8 σ), so
about 42 % of reports should move more than it (normal approximation) and the median |actual| ÷ implied is ≈ 0.85.
Fewer than that = options priced more than what happened.  Kept 3 years in data_cache/earn_implied_log.json
(the Actions cache keeps earn_*).  Descriptive, not a forecast."""
from __future__ import annotations

import json
import math
import os
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..config import DATA_DIR

FILE = DATA_DIR / "earn_implied_log.json"
FAIR_OVER = 2 * (1 - 0.5 * (1 + math.erf(math.sqrt(2 / math.pi) / math.sqrt(2)))) * 100   # P(|Z| > E|Z|) ≈ 42.5 %
FAIR_MED = 0.6745 / math.sqrt(2 / math.pi)                                             # median |Z| ÷ E|Z| ≈ 0.85
KEEP_DAYS = 3 * 365
MIN_N = 20


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save(log: Dict) -> None:
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(log, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError:
        pass


def record(log: Dict, rows: List[Dict], today: str) -> None:
    """Keep the newest implied move taken while the report was still ahead (after-close reports: also on the day)."""
    for r in rows or []:
        mv, d = r.get("mv"), r.get("date")
        if mv is None or not d or mv <= 0:
            continue
        if not (d > today or (d == today and r.get("time") == "after")):
            continue
        k = f"{r['sym']}|{d}"
        old = log.get(k) or {}
        if old.get("act") is not None:
            continue
        log[k] = {"sym": r["sym"], "name": r.get("name") or r["sym"], "date": d, "time": r.get("time") or "",
                  "mv": round(float(mv), 2), "exp": r.get("exp"), "asof": r.get("asof"), "hist": r.get("avg")}


def resolve(log: Dict, series, today: str) -> None:
    """Fill the actual two-session move once the session after the report has closed.  The stored move is permanent, so
    the price series is cut to finished sessions first: an in-progress bar is never recorded as the post-report close."""
    from .sessions import completed
    from .techearn import reaction
    for k, x in log.items():
        if x.get("act") is not None or x["date"] >= today:
            continue
        try:
            v = reaction(completed(series(x["sym"]), x["sym"]), x["date"])
        except Exception:  # noqa: BLE001
            v = None
        if v is not None:
            x["act"] = round(float(v), 2)
    lo = (date.fromisoformat(today) - timedelta(days=KEEP_DAYS)).isoformat()
    for k in [k for k, x in log.items() if x["date"] < lo or (x.get("act") is None and x["date"] < (date.fromisoformat(today) - timedelta(days=10)).isoformat())]:
        del log[k]                                            # old, or never resolved (no price after the report)


def _wilson(k: int, n: int, z: float = 1.645) -> tuple:
    p = k / n
    c = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    m = (p + z * z / (2 * n)) / (1 + z * z / n)
    return (m - c) * 100, (m + c) * 100


def stats(log: Dict) -> Dict:
    done = sorted((x for x in log.values() if x.get("act") is not None and x.get("mv")), key=lambda x: x["date"], reverse=True)
    out: Dict = {"n": len(done), "pending": sum(1 for x in log.values() if x.get("act") is None),
                 "fair_over": FAIR_OVER, "fair_med": FAIR_MED, "recent": done[:12],
                 "start": min((x["date"] for x in log.values()), default=None)}
    if not done:
        return out
    ratios = sorted(abs(x["act"]) / x["mv"] for x in done)
    over = sum(abs(x["act"]) > x["mv"] for x in done)
    out.update({"over": over, "over_pct": over / len(done) * 100, "med_ratio": ratios[len(ratios) // 2] if len(ratios) % 2 else
                (ratios[len(ratios) // 2 - 1] + ratios[len(ratios) // 2]) / 2,
                "up": sum(x["act"] > 0 for x in done), "since": done[-1]["date"]})
    if len(done) >= MIN_N:
        out["lo"], out["hi"] = _wilson(over, len(done))
    return out


def update(rows: List[Dict], series, today: str) -> Dict:
    log = load()
    record(log, rows, today)
    resolve(log, series, today)
    save(log)
    return stats(log)
