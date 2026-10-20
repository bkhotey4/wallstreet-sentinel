"""我的持股（私人）— three checks built only from data the engine already has; nothing here is a forecast.

* events(): the next N days of things that can move YOUR holdings — each holding's earnings date (Nasdaq calendar,
  with its weight) plus the top-importance US macro releases (FOMC / CPI / PCE / jobs …, which hit every holding),
  grouped by day; a day with two or more of them is flagged as "stacked" (e.g. FOMC and a holding's report the same night).
* sanity(): can the numbers be trusted — a cost far from the price (typo or split), a quote older than the market's
  latest date, a one-day move big enough to look like a split or a bad tick, a missing price.
* day_split(): today's P&L in TWD split into the part from share prices and the part from the USD/TWD rate.
  Exact for one day because the holdings do not change within the day; longer periods need a trade log.
Private: used only by the owner's /holdings commands and DMs, never by the public site build."""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional

from ..config import SETTINGS

DEFAULTS = {"days": 14, "macro_min_imp": 3, "cost_ratio": 3.0, "jump_pct": 40.0, "stale_days": 4}


ALIAS = {"GOOG": ("GOOGL",), "GOOGL": ("GOOG",), "BRK-B": ("BRK.B", "BRK-A"), "BRK.B": ("BRK-B",),
         "FOX": ("FOXA",), "FOXA": ("FOX",), "NWS": ("NWSA",), "NWSA": ("NWS",)}


def cfg() -> Dict:
    return {**DEFAULTS, **(SETTINGS.get("personal", {}) or {})}


def _key(sym: str) -> str:
    return str(sym or "").upper().replace(".TWO", "").replace(".TW", "")


# ------------------------------------------------------------------ 1. personal event radar
def events(weights: Dict[str, float], earn_cal: Iterable[Dict], econ_events: Iterable[Dict], today: date,
           days: Optional[int] = None, macro_min_imp: Optional[int] = None) -> Dict:
    """weights: {sym: % of the portfolio}.  earn_cal: [{sym, date, time, name}].  econ_events: macro_events.build()["events"].
    Returns {"days": [{"date", "items": [...], "stacked", "weight"}], "earn_weight", "n_earn", "n_macro", "busiest"}."""
    c = cfg()
    days = int(days if days is not None else c["days"])
    min_imp = int(macro_min_imp if macro_min_imp is not None else c["macro_min_imp"])
    lo, hi = today.isoformat(), (today + timedelta(days=days)).isoformat()
    want = {_key(s): s for s in weights}
    for k, s in list(want.items()):                               # other share classes of the same company
        for a in ALIAS.get(k, ()):
            want.setdefault(a, s)
    by: Dict[str, List[Dict]] = {}
    seen = set()
    for e in earn_cal or []:
        k = _key(e.get("sym"))
        d = str(e.get("date") or "")[:10]
        if k in want and lo <= d <= hi and k not in seen:
            seen.add(k)
            s = want[k]
            by.setdefault(d, []).append({"kind": "earn", "sym": s, "name": e.get("name") or "", "time": e.get("time") or "",
                                         "weight": round(float(weights.get(s) or 0), 1)})
    for e in econ_events or []:
        d = str(e.get("date") or "")[:10]
        if e.get("released") or not (lo <= d <= hi) or int(e.get("imp") or 0) < min_imp:
            continue
        by.setdefault(d, []).append({"kind": "macro", "key": e.get("key"), "zh": e.get("zh"), "en": e.get("en"),
                                     "tpe": e.get("tpe"), "sep": bool(e.get("sep")), "weight": 100.0})
    out = []
    for d in sorted(by):
        items = sorted(by[d], key=lambda x: (x["kind"] != "macro", -x["weight"]))
        ew = sum(x["weight"] for x in items if x["kind"] == "earn")
        out.append({"date": d, "items": items, "stacked": len(items) >= 2,
                    "weight": 100.0 if any(x["kind"] == "macro" for x in items) else round(ew, 1), "earn_weight": round(ew, 1)})
    earn = [x for dd in out for x in dd["items"] if x["kind"] == "earn"]
    busiest = max((dd for dd in out if dd["stacked"]), key=lambda dd: (len(dd["items"]), dd["earn_weight"]), default=None)
    return {"days": out, "horizon": days, "n_earn": len(earn), "earn_weight": round(sum(x["weight"] for x in earn), 1),
            "n_macro": sum(1 for dd in out for x in dd["items"] if x["kind"] == "macro"), "busiest": busiest}


# ------------------------------------------------------------------ 2. can the numbers be trusted
def sanity(rows: Iterable[Dict], latest: Optional[Dict[str, str]] = None, cost_ratio: Optional[float] = None,
           jump_pct: Optional[float] = None, stale_days: Optional[int] = None) -> List[Dict]:
    """rows: [{sym, cost, price, chg_pct, asof, market}] (price None = no quote).  latest: {market: newest quote date
    among the tracked tickers}.  Returns one issue per problem: {sym, code, zh, en}."""
    c = cfg()
    cr = float(cost_ratio or c["cost_ratio"])
    jp = float(jump_pct or c["jump_pct"])
    sd = int(stale_days or c["stale_days"])
    out = []
    for r in rows:
        s, px, cost = r.get("sym"), r.get("price"), r.get("cost")
        if px is None or (isinstance(px, float) and math.isnan(px)):
            out.append({"sym": s, "code": "no_price", "zh": "沒有報價，市值與損益未計入", "en": "no quote; left out of value and P&L"})
            continue
        if cost and cost > 0 and px > 0 and max(cost / px, px / cost) >= cr:
            out.append({"sym": s, "code": "cost_far",
                        "zh": f"成本 {cost:,.2f} 與現價 {px:,.2f} 相差 {max(cost / px, px / cost):.1f} 倍：請確認是否打錯或有拆股",
                        "en": f"cost {cost:,.2f} vs price {px:,.2f} ({max(cost / px, px / cost):.1f}×): check for a typo or a split"})
        ch = r.get("chg_pct")
        if ch is not None and ch == ch and abs(ch) >= jp:
            out.append({"sym": s, "code": "jump", "zh": f"單日 {ch:+.1f}%：可能是拆股／合股或報價錯誤，請先核對",
                        "en": f"{ch:+.1f}% in a day: possibly a split or a bad tick — verify first"})
        a, ref = str(r.get("asof") or "")[:10], (latest or {}).get(r.get("market") or "us")
        if a and ref:
            try:
                gap = (date.fromisoformat(ref) - date.fromisoformat(a)).days
            except ValueError:
                gap = 0
            if gap >= sd:
                out.append({"sym": s, "code": "stale", "zh": f"報價停在 {a}（市場最新 {ref}）：可能停牌、下市或資料源中斷",
                            "en": f"quote stuck at {a} (market {ref}): halted, delisted or a feed gap"})
    return out


# ------------------------------------------------------------------ 3. today's P&L: prices vs the USD/TWD rate
def day_split(rows: Iterable[Dict], fx_now: Optional[float], fx_chg_pct: Optional[float], usd_cash: float = 0.0) -> Optional[Dict]:
    """rows: [{shares, price, chg_pct, currency}] in local currency.  fx = TWD per USD and its % change today.
    Returns {"price": TWD, "fx": TWD, "total": TWD, "missing": n} or None without a rate.
    price part = Σ n·(p1 − p0)·fx0 ; fx part = Σ n·p1·(fx1 − fx0) (+ USD cash) → the two add up exactly."""
    if not fx_now:
        return None
    fx_prev = fx_now / (1 + fx_chg_pct / 100) if fx_chg_pct is not None and fx_chg_pct == fx_chg_pct else fx_now
    pp = fp = 0.0
    miss = 0
    for r in rows:
        p1, ch, n = r.get("price"), r.get("chg_pct"), float(r.get("shares") or 0)
        if p1 is None or ch is None or ch != ch:
            miss += 1
            continue
        p0 = p1 / (1 + ch / 100)
        if (r.get("currency") or "USD") == "USD":
            pp += n * (p1 - p0) * fx_prev
            fp += n * p1 * (fx_now - fx_prev)
        elif r.get("currency") == "TWD":
            pp += n * (p1 - p0)
        else:
            miss += 1                                            # other currencies: no daily rate change here
    fp += float(usd_cash or 0) * (fx_now - fx_prev)
    return {"price": pp, "fx": fp, "total": pp + fp, "missing": miss, "fx_chg_pct": fx_chg_pct}


# ------------------------------------------------------------------ engine glue (bot side)
def build(eng, today: Optional[date] = None) -> Dict:
    hold = getattr(eng, "holdings", None) or {}
    if not hold:
        return {"available": False}
    from ..data import econcal as EC
    today = today or EC.us_today()
    pf = getattr(eng, "portfolio", None) or {}
    pos = {p["sym"]: p for p in pf.get("positions", []) if "value_usd" in p}
    weights = {s: (pos.get(s) or {}).get("weight") or 0.0 for s in hold}
    te = getattr(eng, "techearn", None)
    cal = ((te.get("calendar") or {}).get("up") or []) if isinstance(te, dict) else []
    ev = (getattr(eng, "econ_view", None) or {}).get("events") or []
    m = eng.market
    rows, latest = [], {}
    for s, h in hold.items():
        q = m.q(s) or {}
        mk = "tw" if s.endswith((".TW", ".TWO")) else "hk" if s.endswith(".HK") else "us"
        a = str(q.get("asof") or "")[:10]
        if a and a > latest.get(mk, ""):
            latest[mk] = a
        rows.append({"sym": s, "cost": h.get("cost"), "price": q.get("price"), "chg_pct": q.get("chg_pct"), "asof": a,
                     "market": mk, "shares": h.get("shares"), "currency": h.get("currency") or "USD"})
    fxq = m.q("TWD=X") or {}
    return {"available": True, "asof": today.isoformat(), "events": events(weights, cal, ev, today),
            "sanity": sanity(rows, latest), "split": day_split(rows, fxq.get("price"), fxq.get("chg_pct"))}
