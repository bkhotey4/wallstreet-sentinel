"""開盤前 30 秒 — what changed overnight, what is scheduled today, and the range the market is pricing.

No direction call.  The "range" is the options market's own number: one standard deviation for one day =
VIX ÷ √252 (S&P 500).  For Taiwan there is no free VIX feed, so the TAIEX range uses the index's own 20-day
realised volatility, labelled as such.  Each range comes with its track record computed from history: how often
the next close actually landed inside ±1σ (theory ≈ 68 %) and ±2σ (≈ 95 %), all-time / last year / last 60 days —
the rule is fixed, nothing is fitted, so the record is effectively out-of-sample.  Fat tails show up as a
lower 2σ hit rate than 95 %."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

NY, TPE = ZoneInfo("America/New_York"), ZoneInfo("Asia/Taipei")
OVERNIGHT = [("ES=F", "標普期貨", "S&P futures"), ("NQ=F", "那指期貨", "Nasdaq futures"), ("^TNX", "美債 10 年", "UST 10y"),
             ("DX-Y.NYB", "美元指數", "Dollar index"), ("CL=F", "原油", "Crude oil"), ("GC=F", "黃金", "Gold"),
             ("BTC-USD", "比特幣", "Bitcoin"), ("^N225", "日經", "Nikkei"), ("^KS11", "韓國", "KOSPI"), ("^HSI", "恆生", "Hang Seng"),
             ("^TWII", "台股加權", "TAIEX"), ("^STOXX50E", "歐洲 50", "Euro Stoxx 50"), ("^GDAXI", "德國", "DAX")]
US_CLOSE = [("^GSPC", "標普 500", "S&P 500"), ("^NDX", "那指 100", "Nasdaq 100"), ("^SOX", "費城半導體", "SOX"),
            ("TSM", "台積電 ADR", "TSM ADR"), ("^VIX", "VIX", "VIX"), ("TWD=X", "美元/台幣", "USD/TWD")]


def next_open(now: datetime, tz: ZoneInfo, hh: int, mm: int) -> datetime:
    """Next weekday open at hh:mm local (holidays are not modelled)."""
    loc = now.astimezone(tz)
    d = loc.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if loc > d + timedelta(minutes=30):
        d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def band_record(close: pd.Series, sigma_pct: pd.Series) -> Dict:
    """How often |next-day return| fell within 1σ / 2σ, where σ (%) is known the evening before."""
    j = pd.concat([close.pct_change(fill_method=None).mul(100).rename("r"), sigma_pct.shift(1).rename("s")], axis=1).dropna()
    j = j[j["s"] > 0]
    if len(j) < 60:
        return {}
    z = (j["r"].abs() / j["s"])

    def rate(x):
        return {"in1": float((x <= 1).mean() * 100), "in2": float((x <= 2).mean() * 100), "n": int(len(x))}
    return {"all": rate(z), "y1": rate(z.iloc[-252:]), "d60": rate(z.iloc[-60:]), "since": j.index[0].strftime("%Y-%m-%d")}


def _q(m, t):
    q = m.q(t) if m is not None else None
    if not q or q.get("price") is None:
        return None
    return q


def build(eng, now: Optional[datetime] = None) -> Dict:
    now = now or datetime.now(timezone.utc)
    m = getattr(eng, "market", None)
    if m is None:
        return {"available": False}
    us_open, tw_open = next_open(now, NY, 9, 30), next_open(now, TPE, 9, 0)
    out: Dict = {"available": True, "built": now.astimezone(TPE).strftime("%m-%d %H:%M"),
                 "us_open": int(us_open.timestamp()), "tw_open": int(tw_open.timestamp()),
                 "us_open_tpe": us_open.astimezone(TPE).strftime("%m-%d %H:%M"), "us_date": us_open.strftime("%Y-%m-%d")}
    out["overnight"] = [{"t": t, "zh": zh, "en": en, "px": q["price"], "ch": q.get("chg_pct"), "asof": q.get("asof")}
                        for t, zh, en in OVERNIGHT if (q := _q(m, t))]
    out["us_close"] = [{"t": t, "zh": zh, "en": en, "px": q["price"], "ch": q.get("chg_pct"), "asof": q.get("asof")}
                       for t, zh, en in US_CLOSE if (q := _q(m, t))]
    # today's scheduled events (US date of the next open)
    ev = (getattr(eng, "econ_view", None) or {}).get("events") or []
    out["events"] = [{"zh": e.get("zh"), "en": e.get("en"), "tpe": e.get("tpe"), "imp": e.get("imp"), "sep": bool(e.get("sep"))}
                     for e in ev if e.get("date") == out["us_date"] and not e.get("released") and int(e.get("imp") or 0) >= 2]
    te = getattr(eng, "techearn", None)
    cal = ((te.get("calendar") or {}).get("up") or []) if isinstance(te, dict) else []
    mv = {r.get("sym"): r for r in ((getattr(eng, "sx", None) or {}).get("earn") or []) if isinstance(r, dict)}
    out["earnings"] = [{"sym": c["sym"], "name": c.get("name") or "", "time": c.get("time") or "", "mv": (mv.get(c["sym"]) or {}).get("mv")}
                       for c in cal if str(c.get("date"))[:10] == out["us_date"]][:12]
    # the priced range
    spx, vix = m.series("^GSPC").dropna(), m.series("^VIX").dropna()
    if len(spx) > 300 and len(vix) > 300:
        v = (_q(m, "^VIX") or {}).get("price") or float(vix.iloc[-1])
        s = float(v) / math.sqrt(252)
        base = float(spx.iloc[-1])
        out["us_range"] = {"vix": float(v), "sigma": s, "base": base, "lo1": base * (1 - s / 100), "hi1": base * (1 + s / 100),
                           "lo2": base * (1 - 2 * s / 100), "hi2": base * (1 + 2 * s / 100), "base_date": spx.index[-1].strftime("%Y-%m-%d"),
                           "record": band_record(spx, vix / math.sqrt(252))}
    tw = m.series("^TWII").dropna()
    if len(tw) > 300:
        rv = tw.pct_change(fill_method=None).rolling(20).std() * 100
        s = float(rv.iloc[-1])
        base = float(tw.iloc[-1])
        out["tw_range"] = {"sigma": s, "base": base, "lo1": base * (1 - s / 100), "hi1": base * (1 + s / 100),
                           "base_date": tw.index[-1].strftime("%Y-%m-%d"), "record": band_record(tw, rv)}
    lk = ((getattr(eng, "sx", None) or {}).get("link") or {})
    if lk.get("available"):
        ix = [r for r in lk.get("index", []) if r.get("implied") is not None]
        if ix:
            r = ix[0]
            out["tw_link"] = {"us_n": r.get("us_n"), "tw_n": r.get("tw_n"), "us": r.get("us_ret", r.get("us")), "beta": r.get("beta"),
                              "corr": r.get("corr"), "implied": r.get("implied"), "us_d": r.get("us_d")}
    op = getattr(getattr(eng, "options", None), "spx", None) or {}
    if op.get("zero_gamma"):
        out["levels"] = {k: op.get(k) for k in ("spot", "zero_gamma", "call_wall", "put_wall", "gex_usd_bn_per_1pct")}
    return out
