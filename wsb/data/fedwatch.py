"""Market-implied FOMC outcomes from 30-day Fed Funds futures (CBOT ZQ), the same arithmetic CME FedWatch uses.

A ZQ contract settles at 100 − (average daily effective fed funds rate over its month).  For a meeting on day d of a
month with N days, the new rate applies from day d+1:  avg = (d·r_before + (N−d)·r_after) / N.  Walking the meetings
in order (starting from today's effective rate) gives the implied rate after each meeting; the gap to the rate before
it, in 25 bp steps, gives the probabilities.  When a meeting falls late in its month (few days at the new rate) the
next month's contract is used instead if that month has no meeting — exactly CME's rule.

Free Yahoo quotes are end-of-day / delayed.  This is what futures price, not a forecast of what the Fed will do."""
from __future__ import annotations

import asyncio
import calendar
import json
import logging
import math
import time
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_fedwatch.json"          # econ_* is kept by the site workflow's cache
CODES = "FGHJKMNQUVXZ"
STEP = 0.25


def ticker(y: int, m: int) -> str:
    return f"ZQ{CODES[m - 1]}{y % 100:02d}.CBT"


def months_ahead(today: date, n: int = 10) -> List[Tuple[int, int]]:
    y, m, out = today.year, today.month, []
    for _ in range(n):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def implied(meetings: List[str], fut: Dict[Tuple[int, int], float], r0: float) -> List[Dict]:
    """Implied post-meeting rate and per-meeting step probabilities.  `fut` maps (year, month) → futures price."""
    mdays = {}
    for d in meetings:
        x = date.fromisoformat(d)
        mdays.setdefault((x.year, x.month), x.day)
    out, r_b = [], r0
    for d in meetings:
        x = date.fromisoformat(d)
        ym, nxt = (x.year, x.month), ((x.year + 1, 1) if x.month == 12 else (x.year, x.month + 1))
        N = calendar.monthrange(x.year, x.month)[1]
        r_a = None
        if N - x.day < 8 and nxt in fut and nxt not in mdays:      # late-month meeting → next (meeting-free) month
            r_a = 100 - fut[nxt]
        elif ym in fut and N - x.day > 0:
            r_a = (N * (100 - fut[ym]) - x.day * r_b) / (N - x.day)
        elif nxt in fut and nxt not in mdays:
            r_a = 100 - fut[nxt]
        if r_a is None or not math.isfinite(r_a):
            break                                                   # no contract → stop (never extrapolate)
        chg = r_a - r_b
        k = abs(chg) / STEP
        lo = math.floor(k + 1e-9)
        frac = k - lo
        sign = -1 if chg < 0 else 1
        probs = {}
        if lo == 0 and frac < 1e-9:
            probs[0] = 1.0
        else:
            probs[int(sign * lo * 25)] = round(1 - frac, 4)
            probs[int(sign * (lo + 1) * 25)] = round(frac, 4)
            probs = {k2: v for k2, v in probs.items() if v > 0.0005}
        out.append({"date": d, "rate_before": round(r_b, 4), "rate_after": round(r_a, 4), "chg_bp": round(chg * 100, 1),
                    "cum_bp": round((r_a - r0) * 100, 1), "probs": {str(k2): v for k2, v in sorted(probs.items())}})
        r_b = r_a
    return out


def outcome_label(bp: int) -> Tuple[str, str]:
    if bp == 0:
        return "維持不變", "Hold"
    n = abs(bp) // 25
    return (f"{'降' if bp < 0 else '升'}息 {n} 碼（{abs(bp)}bp）", f"{'Cut' if bp < 0 else 'Hike'} {abs(bp)}bp")


class FedWatch:
    def __init__(self) -> None:
        self.quotes: Dict[str, List] = {}        # ticker → [price, asof]
        self.snap: Dict[str, List[Dict]] = {}    # meeting date → daily snapshots of that meeting's probabilities
        self.ts = 0.0
        try:
            d = json.loads(FILE.read_text(encoding="utf-8"))
            self.quotes, self.snap, self.ts = d.get("quotes", {}), d.get("snap", {}), float(d.get("ts", 0))
        except (OSError, ValueError):
            pass

    async def refresh(self, force: bool = False) -> None:
        if not force and time.time() - self.ts < 3600:
            return
        from .market import _download
        tickers = [ticker(y, m) for y, m in months_ahead(date.today())]
        try:
            df = await asyncio.to_thread(_download, tickers, period="5d", interval="1d")
        except Exception as e:  # noqa: BLE001
            log.warning("fed funds futures download failed: %s", e)
            return
        got = {}
        for t in tickers:
            if t in getattr(df, "columns", []):
                s = df[t].dropna()
                if len(s) and 80 < float(s.iloc[-1]) < 100:
                    got[t] = [float(s.iloc[-1]), s.index[-1].strftime("%Y-%m-%d")]
        if not got:
            log.warning("fed funds futures: no contract returned")
            return
        self.quotes, self.ts = got, time.time()
        self._save()

    def record(self, meetings: List[Dict]) -> None:
        """Keep one snapshot per day per meeting, so after the decision we can say what was priced beforehand."""
        if not meetings:
            return
        asof = max((v[1] for v in self.quotes.values()), default="")
        changed = False
        for m in meetings[:4]:
            lst = self.snap.setdefault(m["date"], [])
            if asof and asof < m["date"] and (not lst or lst[-1]["asof"] != asof):
                lst.append({"asof": asof, "probs": m["probs"], "rate_after": m["rate_after"], "chg_bp": m["chg_bp"]})
                del lst[:-30]
                changed = True
        cutoff = (date.today() - timedelta(days=730)).isoformat()
        for k in [k for k in self.snap if k < cutoff]:
            self.snap.pop(k)
            changed = True
        if changed:
            self._save()

    def _save(self) -> None:
        try:
            tmp = FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps({"ts": self.ts, "quotes": self.quotes, "snap": self.snap}, ensure_ascii=False), encoding="utf-8")
            tmp.replace(FILE)
        except OSError as e:
            log.warning("fedwatch cache not saved: %s", e)


def _last(fred, sid: str) -> Tuple[Optional[float], Optional[str]]:
    s = ((getattr(fred, "series", None) or {}).get(sid))
    if s is None:
        return None, None
    s = s.dropna()
    return (float(s.iloc[-1]), s.index[-1].strftime("%Y-%m-%d")) if len(s) else (None, None)


def view(eng) -> Dict:
    fw: Optional[FedWatch] = getattr(eng, "fedwatch", None)
    ec = getattr(eng, "econ", None)
    if fw is None or not fw.quotes:
        return {"available": False, "why": "no futures quotes"}
    r0, r0_date = _last(getattr(eng, "fred", None), "EFFR")
    if r0 is None:
        return {"available": False, "why": "no effective fed funds rate (FRED EFFR)"}
    lo, _ = _last(getattr(eng, "fred", None), "DFEDTARL")
    hi, hi_date = _last(getattr(eng, "fred", None), "DFEDTARU")
    # a decision already made but not yet in EFFR (FRED publishes it a day or two later): move r0 by the target change
    tu = (getattr(getattr(eng, "fred", None), "get", lambda _x: None)("DFEDTARU"))
    if tu is not None and r0_date and hi_date and hi_date > r0_date:
        tu = tu.dropna()
        before = tu[tu.index <= r0_date]
        if len(before):
            r0 = r0 + (float(tu.iloc[-1]) - float(before.iloc[-1]))
    asof = max(v[1] for v in fw.quotes.values())
    from .econcal import us_today
    today = us_today().isoformat()                       # meetings are US dates; the decision is at 14:00 ET
    meets = [m["date"] for m in (getattr(ec, "fomc", None) or []) if m["date"] >= today]
    fut = {}
    for t, (px, _d) in fw.quotes.items():
        fut[(2000 + int(t[3:5]), CODES.index(t[2]) + 1)] = px
    rows = implied(meets, fut, r0)
    fw.record(rows)
    seps = {m["date"]: m.get("sep", False) for m in (getattr(ec, "fomc", None) or [])}
    for r in rows:
        r["sep"] = seps.get(r["date"], False)
        prev = [x for x in fw.snap.get(r["date"], []) if x["asof"] < asof]
        wk = next((x for x in reversed(prev) if (date.fromisoformat(asof) - date.fromisoformat(x["asof"])).days >= 6), None)
        r["week_ago"] = wk
    return {"available": bool(rows), "asof": asof, "r0": r0, "r0_date": r0_date, "target": [lo, hi], "meetings": rows,
            "contracts": len(fw.quotes)}


def priced_before(eng, meeting: str) -> Optional[Dict]:
    """The last snapshot taken before a past meeting (what futures expected going in)."""
    fw = getattr(eng, "fedwatch", None)
    lst = [x for x in (getattr(fw, "snap", {}) or {}).get(meeting, []) if x["asof"] < meeting]
    return lst[-1] if lst else None
