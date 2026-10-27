"""台灣 ETF: price vs NAV, size and daily creations / redemptions, total return with dividends, trailing yield,
drawdown, 填息 (how long the price took to recover a dividend), holders, upcoming ex-dividend dates, the leveraged-ETF
drag and the currency part of US-bond ETFs.  Every sentence is chosen by rules on the numbers (data from
wsb.data.tw_etf).  Description and history, not a forecast or advice."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..data import tw_etf as D

PREM_WARN = 1.0            # |premium| ≥ 1 % of NAV: you pay (or receive) noticeably more / less than the assets are worth
MIN_AUM = 10.0             # 億元: tiny ETFs are left out of the premium list (thin quotes)
MIN_HIST = 40              # daily snapshots before an ETF's own premium / flow history is used


def _tr(c: pd.Series, dv: List) -> pd.Series:
    """Total-return index: the dividend is added back on its ex-date (reinvested at that close)."""
    div = pd.Series(0.0, index=c.index)
    for d, a in dv:
        t = pd.Timestamp(d)
        if t in div.index:
            div[t] += a
    r = (c + div) / c.shift(1)
    return r.fillna(1.0).cumprod() * c.iloc[0]


def _ret(s: pd.Series, days: int) -> Optional[float]:
    p = s[s.index <= s.index[-1] - pd.Timedelta(days=days)]
    return float(s.iloc[-1] / p.iloc[-1] - 1) * 100 if len(p) and s.index[0] <= s.index[-1] - pd.Timedelta(days=days - 5) else None


def _fill(c: pd.Series, dv: List) -> Optional[Dict]:
    """Last dividend: did the price get back to the close before the ex-date, and how many calendar days it took."""
    if not dv:
        return None
    ex, amt = dv[-1]
    t = pd.Timestamp(ex)
    before = c[c.index < t]
    after = c[c.index >= t]
    if not len(before) or not len(after):
        return None
    ref = float(before.iloc[-1])
    hit = after[after >= ref]
    out = {"ex": ex, "amt": amt, "ref": ref}
    if len(hit):
        out.update(done=True, days=int((hit.index[0] - t).days))
    else:
        out.update(done=False, days=int((c.index[-1] - t).days), gap=float(c.iloc[-1] / ref - 1) * 100)
    return out


def _fill_hist(c: pd.Series, dv: List) -> Optional[Dict]:
    """Share of past dividends (older than 60 days) that were filled within 60 days, and the median days."""
    days, n_ok, n = [], 0, 0
    for ex, a in dv:
        t = pd.Timestamp(ex)
        if t > c.index[-1] - pd.Timedelta(days=60):
            continue
        f = _fill(c, [[ex, a]])
        if not f:
            continue
        n += 1
        if f["done"] and f["days"] <= 60:
            n_ok += 1
        if f["done"]:
            days.append(f["days"])
    return {"n": n, "share60": n_ok / n * 100, "median": float(np.median(days)) if days else None} if n >= 3 else None


def one(code: str, d: Dict, nav: Dict, today: date) -> Dict:
    v = nav.get(code) or {}
    out = {"code": code, "name": v.get("name") or code, "kind": D.kind_of(code, v.get("name") or ""),
           "px": v.get("px"), "nav": v.get("nav"), "prem": v.get("prem"), "asof": v.get("date")}
    if v.get("units") and v.get("nav"):
        out["aum"] = v["units"] * v["nav"] / 1e8
        out["flow"] = (v.get("dunits") or 0) * v["nav"] / 1e8 if v.get("dunits") is not None else None
    hist = sorted((k, r.get(code)) for k, r in (d.get("daily") or {}).items() if r.get(code))
    if len(hist) >= 2:
        f20 = [(b[0] - a[0]) * b[1] / 1e8 for (_, a), (_, b) in zip(hist[-21:-1], hist[-20:]) if a[0] and b[0] and b[1]]
        out["flow20"] = sum(f20) if len(f20) >= 15 else None
        out["n_hist"] = len(hist)
        pr = [r[2] for _, r in hist if r[2] is not None]
        if len(pr) >= MIN_HIST and out["prem"] is not None:
            sd = float(np.std(pr[:-1]))
            out["prem_z"] = (out["prem"] - float(np.mean(pr[:-1]))) / sd if sd > 0 else None
    p = (d.get("px") or {}).get(code)
    if p:
        c = pd.Series({pd.Timestamp(a): b for a, b in p["c"]}).sort_index()
        dv = p.get("dv") or []
        tr = _tr(c, dv)
        out.update(close=float(c.iloc[-1]), close_date=c.index[-1].strftime("%Y-%m-%d"), since=c.index[0].strftime("%Y-%m"),
                   r1m=_ret(c, 30), r1y=_ret(c, 365), tr1y=_ret(tr, 365), tr3y=_ret(tr, 365 * 3))
        yr = [a for x, a in dv if pd.Timestamp(x) > c.index[-1] - pd.Timedelta(days=365)]
        full = c.index[0] <= c.index[-1] - pd.Timedelta(days=360)
        out["div12"] = sum(yr) if full else None
        out["yld"] = sum(yr) / float(c.iloc[-1]) * 100 if full and yr else (0.0 if full else None)
        out["n_div12"] = len(yr) if full else None
        w = tr[tr.index > tr.index[-1] - pd.Timedelta(days=365)]
        if len(w) > 200:
            out["dd1y"] = float((w / w.cummax() - 1).min() * 100)
            out["off_hi"] = float(w.iloc[-1] / w.max() - 1) * 100
            out["vol1y"] = float(w.pct_change().std() * np.sqrt(250) * 100)
        out["fill"] = _fill(c, dv)
        out["fill_hist"] = _fill_hist(c, dv)
    hd = sorted((d.get("holders") or {}).items())
    hs = [(k, r[code][0]) for k, r in hd if r.get(code) and r[code][0]]
    if hs:
        out["holders"] = hs[-1][1]
        out["holders_date"] = hs[-1][0]
        out["holders_1w"] = hs[-1][1] - hs[-2][1] if len(hs) >= 2 else None
        out["holders_4w"] = hs[-1][1] - hs[-5][1] if len(hs) >= 5 else None
        ch = [b[1] - a[1] for a, b in zip(hs[:-1], hs[1:])]
        if len(ch) >= 12:
            sd = float(np.std(ch[:-1]))
            out["holders_z"] = (ch[-1] - float(np.mean(ch[:-1]))) / sd if sd > 0 else None
    return out


def build(eng=None, d: Optional[Dict] = None, today: Optional[date] = None) -> Dict:
    d = D.load() if d is None else d
    today = today or date.today()
    nav = d.get("nav") or {}
    if not nav and not d.get("px"):
        return {"available": False}
    codes = D.tracked(nav) if nav else list((d.get("px") or {}).keys())
    rows = [one(c, d, nav, today) for c in codes]
    core = {c for xs in D.CORE.values() for c in xs}
    for r in rows:
        r["core"] = r["code"] in core
    # all ETFs by kind: count, assets, today's creations − redemptions
    kinds: Dict[str, Dict] = {}
    for k, v in nav.items():
        if not (v.get("units") and v.get("nav")):
            continue
        g = kinds.setdefault(D.kind_of(k, v.get("name") or ""), {"n": 0, "aum": 0.0, "flow": 0.0, "n_flow": 0})
        g["n"] += 1
        g["aum"] += v["units"] * v["nav"] / 1e8
        if v.get("dunits") is not None:
            g["flow"] += v["dunits"] * v["nav"] / 1e8
            g["n_flow"] += 1
    # each kind's daily flow history → today's flow against its own past (σ) once enough snapshots exist
    days = sorted(d.get("daily") or {})
    if len(days) >= MIN_HIST + 1:
        names = {k: v.get("name") or "" for k, v in nav.items()}
        ser: Dict[str, List[float]] = {}
        for a, b in zip(days[:-1], days[1:]):
            A, B = d["daily"][a], d["daily"][b]
            fl: Dict[str, float] = {}
            for k, x in B.items():
                y = A.get(k)
                if y and x[0] and y[0] and x[1]:
                    kk = D.kind_of(k, names.get(k, ""))
                    fl[kk] = fl.get(kk, 0.0) + (x[0] - y[0]) * x[1] / 1e8
            for kk, f in fl.items():
                ser.setdefault(kk, []).append(f)
        for kk, xs in ser.items():
            if kk in kinds and len(xs) >= MIN_HIST:
                h = np.array(xs[:-1])
                sd = float(h.std())
                kinds[kk]["z"] = (xs[-1] - float(h.mean())) / sd if sd > 0 else None
                kinds[kk]["flow20"] = float(sum(xs[-20:]))
    prem = sorted([{"code": k, "name": v["name"], "prem": v["prem"], "aum": v["units"] * v["nav"] / 1e8}
                   for k, v in nav.items() if v.get("prem") is not None and v.get("units") and v.get("nav")
                   and abs(v["prem"]) >= PREM_WARN and v["units"] * v["nav"] / 1e8 >= MIN_AUM], key=lambda x: -abs(x["prem"]))
    n_prem_known = sum(1 for v in nav.values() if v.get("prem") is not None)
    soon = [x for x in d.get("exdiv") or [] if today.isoformat() <= x["date"] <= (today + timedelta(days=45)).isoformat()]
    for x in soon:
        px = (nav.get(x["code"]) or {}).get("px")
        x["yld"] = x["cash"] / px * 100 if x.get("cash") and px else None
    by = {r["code"]: r for r in rows}
    lev = None
    a, b = by.get("00631L"), by.get("0050")
    if a and b and a.get("r1y") is not None and b.get("r1y") is not None:
        lev = {"lev": a["r1y"], "base": b["r1y"], "x2": 2 * b["r1y"], "gap": a["r1y"] - 2 * b["r1y"],
               "inv": (by.get("00632R") or {}).get("r1y"), "vol": b.get("vol1y")}
    fx = None
    bnd = by.get("00679B")
    if eng is not None and bnd and bnd.get("r1y") is not None:
        try:
            tlt, twd = eng.market.series("TLT").dropna(), eng.market.series("TWD=X").dropna()
            rt, rx = _ret(tlt, 365), _ret(twd, 365)
            if rt is not None and rx is not None:
                fx = {"etf": bnd["r1y"], "usd": rt, "fx": rx, "combo": ((1 + rt / 100) * (1 + rx / 100) - 1) * 100}
        except Exception:  # noqa: BLE001
            fx = None
    flow_all = sum(g["flow"] for g in kinds.values()) if kinds else None
    return {"available": True, "rows": rows, "kinds": kinds, "prem": prem, "n_prem_known": n_prem_known, "n_etf": len(nav),
            "exdiv": soon, "lev": lev, "fx": fx, "flow_all": flow_all, "n_days": len(days),
            "asof": max((v.get("date") for v in nav.values() if v.get("date")), default=None),
            "holders_date": max(d.get("holders") or {"": 0}) or None, "ts": d.get("ts")}


def headline(r: Dict) -> str:
    if not r.get("available"):
        return "台灣 ETF 資料暫時取不到。"
    parts = []
    k = r.get("kinds") or {}
    if k and r.get("flow_all") is not None:
        big = sorted(((g["flow"], n) for n, g in k.items() if abs(g["flow"]) >= 1), key=lambda x: -abs(x[0]))[:2]
        parts.append(f"今天台股 ETF 合計淨{'流入' if r['flow_all'] >= 0 else '流出'} {abs(r['flow_all']):,.0f} 億元"
                     + ("（" + "、".join(f"{n} {f:+,.0f} 億" for f, n in big) + "）" if big else ""))
    if r.get("n_prem_known"):
        parts.append(f"{len(r['prem'])} 檔規模 {MIN_AUM:.0f} 億以上的 ETF 市價和淨值差 1% 以上" if r["prem"] else
                     f"規模 {MIN_AUM:.0f} 億以上的 ETF 市價都貼近淨值（差距小於 1%）")
    else:
        parts.append("淨值資料暫缺，折溢價無法判斷")
    if r.get("exdiv"):
        parts.append(f"未來 45 天有 {len(r['exdiv'])} 檔 ETF 除息")
    return "；".join(parts) + "。"
