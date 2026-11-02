"""IPO 觀察 — where each listing candidate is in the process, when it is likely to list (from the timing of past cases,
not a fixed rule), what its prospectus says, and how past IPOs actually did after listing.

US timing: among operating-company IPOs priced in the data window, the days from the first public S-1 / F-1 to the 424B4,
and from the last amendment before pricing to the 424B4 (25th / 50th / 75th percentile).  A pending filer's window is its
first public filing + those percentiles; past the 75th it is "slower than most" (many such filings are later withdrawn).
After listing (offer price from the 424B4): first-day close vs the offer, 60 / 120 trading days from the first close vs
the S&P 500, today vs the offer, and the ±5 trading days around the lock-up expiry (offer date + lock-up days, 180 when the
prospectus does not say) vs the S&P 500; also split by the money raised (>= US$100 million vs smaller), since the many
tiny Nasdaq Capital Market / NYSE American listings dominate the plain medians.  Taiwan: dates are in the 公開申購公告; after listing the first close vs 承銷價,
20 trading days vs 承銷價 and 60 days vs the TAIEX.  Descriptive statistics, not a forecast or advice."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ACTIVE_DAYS = 270
LOCK = 180
BIG_RAISE = 100.0          # US$ million raised in the IPO (offer price × shares offered on the 424B4 cover)


def _d(s: Optional[str]) -> Optional[date]:
    try:
        return date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


def _pct(v: List[float]) -> Optional[Dict]:
    if len(v) < 5:
        return None
    a = np.asarray(v, dtype=float)
    return {"p25": float(np.percentile(a, 25)), "med": float(np.median(a)), "p75": float(np.percentile(a, 75)), "n": len(a)}


def _first_bar(s: pd.Series, d: date) -> Optional[int]:
    """Index of the first close on/after the day before the 424B4 date (the IPO usually trades the day the final
    prospectus is filed or the day before)."""
    s = s.dropna()
    if s.empty:
        return None
    i = int(s.index.searchsorted(pd.Timestamp(d - timedelta(days=1))))
    return i if i < len(s) and (s.index[i].date() - d).days <= 7 else None


def _ret(s: pd.Series, i: int, j: int) -> Optional[float]:
    return float(s.iloc[j] / s.iloc[i] - 1) * 100 if 0 <= i < len(s) and 0 <= j < len(s) else None


def _bench(b: Optional[pd.Series], a: pd.Timestamp, z: pd.Timestamp) -> Optional[float]:
    if b is None or b.empty:
        return None
    b = b.dropna()
    i, j = b.index.searchsorted(a), b.index.searchsorted(z, side="right") - 1
    return float(b.iloc[j] / b.iloc[i] - 1) * 100 if 0 <= i < len(b) and 0 <= j < len(b) and j >= i else None


def after_listing(s: pd.Series, d: date, offer: Optional[float], bench: Optional[pd.Series], lock: int, today: date) -> Optional[Dict]:
    s = s.dropna()
    i = _first_bar(s, d)
    if i is None:
        return None
    t0 = s.index[i]
    out: Dict = {"first": str(t0.date()), "close1": float(s.iloc[i]), "now": float(s.iloc[-1]), "days": len(s) - 1 - i}
    if offer:
        out["day1"] = (s.iloc[i] / offer - 1) * 100
        out["vs_offer"] = (s.iloc[-1] / offer - 1) * 100
    for n in (60, 120):
        if i + n < len(s):
            r, b = _ret(s, i, i + n), _bench(bench, t0, s.index[i + n])
            out[f"x{n}"] = r - b if r is not None and b is not None else None
    ld = t0.date() + timedelta(days=lock)
    out["lock"] = str(ld)
    k = int(s.index.searchsorted(pd.Timestamp(ld)))
    if k + 5 < len(s) and k - 5 >= 0:
        r, b = _ret(s, k - 5, k + 5), _bench(bench, s.index[k - 5], s.index[k + 5])
        out["lockx"] = r - b if r is not None and b is not None else None
    return out


def us_view(d: Dict, px: pd.DataFrame, spx: Optional[pd.Series], today: date) -> Dict:
    fl = ((d.get("us") or {}).get("filers") or {})
    ipo = [{"cik": c, **f} for c, f in fl.items() if f.get("kind") == "ipo"]
    priced = [f for f in ipo if f.get("priced")]
    t_first = [(_d(f["priced"]) - _d(f["s1"])).days for f in priced if _d(f.get("s1")) and _d(f["priced"]) >= _d(f["s1"])]
    t_last = [(_d(f["priced"]) - _d(f["last_pre"])).days for f in priced if _d(f.get("last_pre"))]
    tf, tl = _pct(t_first), _pct(t_last)
    lo_act = (today - timedelta(days=ACTIVE_DAYS)).isoformat()
    pend, other = [], 0
    for f in ipo:
        if f.get("priced") or f.get("rw") or not f.get("s1") or f.get("last", "") < lo_act:
            continue
        cv = f.get("cover") or {}
        if not cv.get("exchange"):
            other += 1
            continue
        since = (today - _d(f["s1"])).days
        row = {"cik": f["cik"], "name": f.get("name"), "sicd": f.get("sicd"), "foreign": f.get("foreign"), "drs": f.get("drs"),
               "s1": f["s1"], "last": f.get("last"), "amends": f.get("amends", 0), "since": since, "exchange": cv.get("exchange"),
               "symbol": cv.get("symbol"), "lo": cv.get("lo"), "hi": cv.get("hi"), "shares": cv.get("shares"), "lockup": cv.get("lockup"),
               "acc": (f.get("doc") or {}).get("acc")}
        if tf:
            row["win_lo"] = str(_d(f["s1"]) + timedelta(days=int(tf["p25"])))
            row["win_hi"] = str(_d(f["s1"]) + timedelta(days=int(tf["p75"])))
            row["slow"] = since > tf["p75"]
        if cv.get("lo") and tl:
            row["near"] = str(_d(f["last"]) + timedelta(days=int(tl["med"])))
        pend.append(row)
    pend.sort(key=lambda r: r["last"], reverse=True)               # price range set first (closest to pricing), then newest
    pend.sort(key=lambda r: 0 if r.get("lo") else 1)
    done = []
    for f in priced:
        sym = (f.get("tickers") or [None])[0] or (f.get("cover") or {}).get("symbol")
        rec = {"name": f.get("name"), "sym": sym, "priced": f["priced"], "offer": f.get("offer"), "sicd": f.get("sicd"),
               "lockup": (f.get("cover") or {}).get("lockup") or LOCK,
               "raise": f["offer"] * f["offer_shares"] / 1e6 if f.get("offer") and f.get("offer_shares") else None}
        if sym and sym in px.columns:
            a = after_listing(px[sym], _d(f["priced"]), f.get("offer"), spx, rec["lockup"], today)
            if a:
                rec.update(a)
        done.append(rec)
    done.sort(key=lambda r: r["priced"], reverse=True)
    st = stats_us(done)
    st["big"] = stats_us([r for r in done if (r.get("raise") or 0) >= BIG_RAISE])
    st["small"] = stats_us([r for r in done if r.get("raise") is not None and r["raise"] < BIG_RAISE])
    soon = [r for r in done if r.get("lock") and today.isoformat() <= r["lock"] <= (today + timedelta(days=30)).isoformat()]
    return {"pending": pend, "other": other, "recent": [r for r in done if r["priced"] >= (today - timedelta(days=120)).isoformat()],
            "n_priced": len(priced), "t_first": tf, "t_last": tl, "stats": st, "lock_soon": sorted(soon, key=lambda r: r["lock"]),
            "from": min((f["priced"] for f in priced), default=None)}


def _share(v: List[float]) -> Optional[float]:
    return float(np.mean([x > 0 for x in v]) * 100) if v else None


def stats_us(done: List[Dict]) -> Dict:
    g = lambda k: [r[k] for r in done if r.get(k) is not None]  # noqa: E731
    out: Dict = {}
    for k in ("day1", "x60", "x120", "vs_offer", "lockx"):
        v = g(k)
        out[k] = {"n": len(v), "med": float(np.median(v)), "pos": _share(v)} if len(v) >= 10 else None
    return out


def tw_view(d: Dict, px: pd.DataFrame, twii: Optional[pd.Series], today: date) -> Dict:
    tw = d.get("tw") or {}
    rows = {(r["code"], r.get("list")): r for y in (tw.get("public") or {}).values() for r in y.get("rows", [])}
    esb = (tw.get("esb") or {}).get("rows") or {}
    fin = tw.get("fin") or {}
    lg = tw.get("apply_log") or {}
    t = today.isoformat()
    up, past = [], []
    for r in rows.values():
        rec = dict(r)
        e = esb.get(r["code"]) or {}
        f = {k: v for k, v in (fin.get(r["code"]) or {}).items() if k != "ts"}
        if e.get("avg") and r.get("price"):
            rec["esb_avg"], rec["disc"] = e["avg"], (r["price"] / e["avg"] - 1) * 100
        if f:
            rec["fin"] = f
        if lg.get(r["code"]) and r.get("list"):
            rec["wait"] = (_d(r["list"]) - _d(lg[r["code"]]["apply"])).days
        if (r.get("list") or "") >= t:
            up.append(rec)
            continue
        sym = f"{r['code']}.{'TWO' if r['mk'] == '初上櫃' else 'TW'}"
        if sym in px.columns and r.get("price"):
            s = px[sym].dropna()
            i = _first_bar(s, _d(r["list"]) + timedelta(days=1)) if r.get("list") else None
            if i is not None:
                rec["day1"] = (s.iloc[i] / r["price"] - 1) * 100
                if i + 20 < len(s):
                    rec["d20"] = (s.iloc[i + 20] / r["price"] - 1) * 100
                if i + 60 < len(s):
                    a, b = _ret(s, i, i + 60), _bench(twii, s.index[i], s.index[i + 60])
                    rec["x60"] = a - b if a is not None and b is not None else None
                rec["vs_offer"] = (s.iloc[-1] / r["price"] - 1) * 100
        past.append(rec)
    up.sort(key=lambda r: r.get("list") or "")
    past.sort(key=lambda r: r.get("list") or "", reverse=True)
    listed = {r["code"] for r in rows.values()}
    applying = []
    for c, e in esb.items():
        if not e.get("apply") or c in listed:
            continue
        f = {k: v for k, v in (fin.get(c) or {}).items() if k != "ts"}
        applying.append({"code": c, "name": e["name"], "apply": e["apply"], "to": e.get("to"), "avg": e.get("avg"),
                         "since": (today - _d(e["apply"])).days, **({"fin": f} if f else {})})
    applying.sort(key=lambda r: r["apply"])
    g = lambda k: [r[k] for r in past if r.get(k) is not None]  # noqa: E731
    st = {k: ({"n": len(g(k)), "med": float(np.median(g(k))), "pos": _share(g(k))} if len(g(k)) >= 10 else None)
          for k in ("day1", "d20", "x60", "vs_offer")}
    wins = [r["win"] for r in past if r.get("win")]
    waits = _pct([r["wait"] for r in past if r.get("wait") is not None])
    return {"upcoming": up, "past": past, "applying": applying, "stats": st, "win_med": float(np.median(wins)) if wins else None,
            "wait": waits, "from": min((r["list"] for r in past if r.get("list")), default=None)}


def build(eng=None, today: Optional[date] = None) -> Optional[Dict]:
    from ..data import ipo_data as I
    d = I.load()
    if not d:
        return None
    today = today or date.today()
    px = I.load_px()

    def ser(t):
        try:
            return eng.market.series(t) if eng is not None else None
        except Exception:  # noqa: BLE001
            return None
    out = {"us": us_view(d, px, ser("^GSPC"), today), "tw": tw_view(d, px, ser("^TWII"), today), "asof": today.isoformat()}
    try:
        from ..ai import ipo_ai
        ai = ipo_ai.load()
        for r in out["us"]["pending"]:
            if r.get("acc") and r["acc"] in ai:
                r["ai"] = ai[r["acc"]]
    except Exception:  # noqa: BLE001
        pass
    return out
