"""風險退潮檢查 — after a stress episode, which gauges are back to normal, and what the S&P 500 did after past "cool-downs".

Today: seven plain checks (stress index falling, VIX < 20, VIX term structure back in contango, high-yield bonds above their
50-day average, S&P 500 above its 200-day average, more than half of stocks above their 200-day average, OFR stress < 0).

History, two ways (each episode counted once):
* VIX since 1990: VIX closed ≥ 30, then the first close < 20 afterwards = one cool-down.
* Five-gauge version since ~2007 (VIX, term structure, HYG, 200-day trend, OFR): at most 1 of 5 normal at some point in the
  previous 6 months, then at least 4 of 5 normal = one cool-down.
For each: S&P 500 return 3 / 6 / 12 months later, the deepest fall within the next 6 months, and how often VIX went back
above 30 within 6 months (a false all-clear) — next to the same numbers for every day, so the reader can see whether a
cool-down is any better than a random day.  History, not a forecast, and not a buy signal."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

H = {"3m": 63, "6m": 126, "12m": 252}
REFLARE_D = 126


def _s(eng, sym: str) -> pd.Series:
    try:
        return eng.market.series(sym).dropna()
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)


def _fsi() -> pd.Series:
    try:
        from wsb.data import transmission as TR
        f = TR.load().get("fsi") or {}
        if f.get("dates"):
            return pd.Series(f["OFR FSI"], index=pd.to_datetime(f["dates"])).dropna()
    except Exception:  # noqa: BLE001
        log.debug("fsi unavailable", exc_info=True)
    return pd.Series(dtype=float)


def _breadth(eng) -> Optional[float]:
    b = ((getattr(eng, "rotation", None) or {}).get("breadth") or {})
    v = b.get("us") or next(iter(b.values()), None)
    return float(v["now"]) if v and v.get("now") is not None else None


def checks(eng) -> List[Dict]:
    """[{k, zh, ok, txt}] — ok is None when the data is missing."""
    out = []
    st = getattr(eng, "stress", None)
    ssi = st.history.dropna() if st is not None and getattr(st, "history", None) is not None else pd.Series(dtype=float)
    if len(ssi) > 21:
        now, ago = float(ssi.iloc[-1]), float(ssi.iloc[-21])
        out.append({"k": "ssi", "short": "壓力指數", "zh": "壓力指數 SSI 回到 50 以下、而且比一個月前低", "ok": now < 50 and now < ago, "txt": f"SSI {now:.0f}（一個月前 {ago:.0f}）"})
    vix, v3 = _s(eng, "^VIX"), _s(eng, "^VIX3M")
    if len(vix):
        out.append({"k": "vix", "short": "VIX", "zh": "恐慌指數 VIX 回到 20 以下", "ok": float(vix.iloc[-1]) < 20, "txt": f"VIX {vix.iloc[-1]:.1f}"})
    if len(vix) and len(v3):
        r = float(vix.iloc[-1] / v3.iloc[-1])
        out.append({"k": "term", "short": "期限結構", "zh": "VIX 期限結構恢復正常（近月比遠月低）", "ok": r < 0.95, "txt": f"VIX÷VIX3M {r:.2f}"})
    hyg = _s(eng, "HYG")
    if len(hyg) > 60:
        ma = float(hyg.tail(50).mean())
        out.append({"k": "credit", "short": "高收益債", "zh": "高收益債 ETF（HYG）站回 50 日均線", "ok": float(hyg.iloc[-1]) > ma, "txt": f"離 50 日線 {(hyg.iloc[-1] / ma - 1) * 100:+.1f}%"})
    spx = _s(eng, "^GSPC")
    if len(spx) > 210:
        ma = float(spx.tail(200).mean())
        out.append({"k": "trend", "short": "200 日線", "zh": "標普 500 站回 200 日均線", "ok": float(spx.iloc[-1]) > ma, "txt": f"離 200 日線 {(spx.iloc[-1] / ma - 1) * 100:+.1f}%"})
    br = _breadth(eng)
    if br is not None:
        out.append({"k": "breadth", "short": "市場寬度", "zh": "超過一半的股票站上 200 日均線（不是只有少數大型股在撐）", "ok": br > 50, "txt": f"{br:.0f}% 的股票在 200 日線之上"})
    fsi = _fsi()
    if len(fsi):
        out.append({"k": "fsi", "short": "OFR 壓力", "zh": "OFR 金融壓力指數回到 0 以下（低於長期平均）", "ok": float(fsi.iloc[-1]) < 0, "txt": f"OFR {fsi.iloc[-1]:+.2f}"})
    return out


def _fwd_stats(spx: pd.Series, vix: pd.Series, days: List[pd.Timestamp]) -> Dict:
    rows = []
    last = spx.index[-1]
    for d in days:
        i = spx.index.get_indexer([d], method="bfill")[0]
        if i < 0:
            continue
        p0 = spx.iloc[i]
        r = {"date": spx.index[i].strftime("%Y-%m-%d")}
        for k, n in H.items():
            r[k] = float(spx.iloc[i + n] / p0 - 1) * 100 if i + n < len(spx) else None
        seg = spx.iloc[i:i + REFLARE_D + 1]
        r["dd6"] = float(seg.min() / p0 - 1) * 100 if len(seg) > REFLARE_D else None
        vs = vix[(vix.index > spx.index[i]) & (vix.index <= spx.index[min(i + REFLARE_D, len(spx) - 1)])]
        r["reflare"] = bool((vs >= 30).any()) if i + REFLARE_D < len(spx) else None
        rows.append(r)
    return {"rows": rows, **_summ(rows)}


def _summ(rows: List[Dict]) -> Dict:
    s = {}
    for k in list(H) + ["dd6"]:
        v = [r[k] for r in rows if r.get(k) is not None]
        s[k] = {"n": len(v), "med": float(np.median(v)) if v else None, "up": float(np.mean([x > 0 for x in v]) * 100) if v else None}
    rf = [r["reflare"] for r in rows if r.get("reflare") is not None]
    s["reflare"] = {"n": len(rf), "pct": float(np.mean(rf) * 100) if rf else None}
    return {"sum": s}


def baseline(spx: pd.Series, vix: pd.Series, start: pd.Timestamp) -> Dict:
    """Every trading day since `start`: what a random day scored."""
    p = spx[spx.index >= start]
    out = {}
    for k, n in H.items():
        f = (spx.shift(-n) / spx - 1).reindex(p.index).dropna() * 100
        out[k] = {"n": len(f), "med": float(f.median()), "up": float((f > 0).mean() * 100)}
    lo = spx[::-1].rolling(REFLARE_D + 1, min_periods=REFLARE_D + 1).min()[::-1]
    dd = ((lo / spx - 1) * 100).reindex(p.index).dropna()
    out["dd6"] = {"n": len(dd), "med": float(dd.median()), "up": None}
    vmax = vix[::-1].rolling(REFLARE_D, min_periods=REFLARE_D).max()[::-1].shift(-1)
    rf = (vmax >= 30).reindex(p.index)[vmax.reindex(p.index).notna()]
    out["reflare"] = {"n": len(rf), "pct": float(rf.mean() * 100) if len(rf) else None}
    return out


def vix_cooldowns(vix: pd.Series, hi: float = 30, lo: float = 20) -> List[pd.Timestamp]:
    out, armed = [], False
    for d, v in vix.items():
        if v >= hi:
            armed = True
        elif armed and v < lo:
            out.append(d)
            armed = False
    return out


def gauge_frame(eng) -> pd.DataFrame:
    vix, v3, hyg, spx, fsi = _s(eng, "^VIX"), _s(eng, "^VIX3M"), _s(eng, "HYG"), _s(eng, "^GSPC"), _fsi()
    idx = spx.index
    f = pd.DataFrame(index=idx)
    f["vix"] = vix.reindex(idx).ffill(limit=3) < 20
    f["term"] = (vix / v3).reindex(idx).ffill(limit=3) < 0.95
    hma = hyg.rolling(50).mean()
    f["credit"] = (hyg > hma).astype(float).where(hma.notna()).reindex(idx).ffill(limit=3) > 0.5
    f["trend"] = spx > spx.rolling(200).mean()
    f["fsi"] = fsi.reindex(idx).ffill(limit=10) < 0
    ok = pd.concat([vix.reindex(idx), v3.reindex(idx), hyg.rolling(50).mean().reindex(idx), spx.rolling(200).mean(), fsi.reindex(idx).ffill(limit=10)], axis=1).notna().all(axis=1)
    return f[ok].astype(int)


def gauge_cooldowns(f: pd.DataFrame, need: int = 4, low: int = 1, look: int = 126, gap: int = 63) -> List[pd.Timestamp]:
    sc = f.sum(axis=1)
    was_low = (sc <= low).rolling(look, min_periods=1).max().astype(bool)
    out, last = [], None
    for i, (d, v) in enumerate(sc.items()):
        if v >= need and was_low.iloc[i] and (last is None or i - last >= gap):
            # the stress has to end here: reset so one recovery is counted once
            out.append(d)
            last = i
            was_low.iloc[i:i + look] = False
    return out


def build(eng) -> Dict:
    spx, vix = _s(eng, "^GSPC"), _s(eng, "^VIX")
    cks = checks(eng)
    have = [c for c in cks if c["ok"] is not None]
    out = {"available": bool(have), "checks": cks, "n_ok": sum(1 for c in have if c["ok"]), "n": len(have)}
    if len(spx) < 2000 or len(vix) < 2000:
        return out
    try:
        vs = vix[vix.index >= spx.index[0]]
        cd = vix_cooldowns(vs)
        out["vix"] = {**_fwd_stats(spx, vs, cd), "base": baseline(spx, vs, vs.index[0]), "since": vs.index[0].strftime("%Y")}
        f = gauge_frame(eng)
        if len(f) > 1000:
            gd = gauge_cooldowns(f)
            out["gauge"] = {**_fwd_stats(spx, vs, gd), "base": baseline(spx, vs, f.index[0]), "since": f.index[0].strftime("%Y")}
        # where we are now: days since VIX last closed ≥ 30
        hot = vix[vix >= 30]
        out["since_hot"] = int((vix.index > hot.index[-1]).sum()) if len(hot) else None
        out["last_hot"] = hot.index[-1].strftime("%Y-%m-%d") if len(hot) else None
    except Exception:  # noqa: BLE001
        log.exception("cool-down history failed")
    return out


def phase(r: Dict) -> str:
    """平時 / 壓力中 / 退燒中 — from today's checks and how recently VIX was ≥ 30."""
    n, k = r.get("n") or 0, r.get("n_ok") or 0
    recent = r.get("since_hot") is not None and r["since_hot"] <= 126
    if n and k * 2 < n:
        return "stress"
    if recent:
        return "cooling"
    return "calm" if k >= n - 1 else "mixed"
