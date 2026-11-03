"""Every Taiwan ETF judged on its own history: total return with dividends (vs 0050), whether payouts came out of
capital, bond ETFs' sensitivity to the US 10-year yield, leveraged / inverse decay, and active ETFs since launch.
Benchmarks are picked per ETF by correlation from wsb.data.tw_etf.REFS, never assumed.  Description and history,
not a forecast or advice."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..data import tw_etf as D
from .tw_etf import _ret, _tr

MIN_DAYS = 40              # trading days before an ETF gets any number
BASE = "0050"
LINK_MIN = 0.7             # |correlation| needed before a reference series counts as an ETF's underlying / benchmark
R2_MIN = 0.3               # bond ETF: how much of its weekly moves the 10-year yield + USD/TWD must explain
REF_ZH = {"0050": "0050（台灣 50）", "^TWII": "加權指數", "^GSPC": "標普 500", "^NDX": "那斯達克 100", "^DJI": "道瓊工業",
          "^SOX": "費城半導體", "^N225": "日經 225", "^HSI": "恒生指數", "^NSEI": "印度 Nifty 50",
          "GC=F": "黃金期貨", "BZ=F": "布蘭特原油期貨", "CL=F": "西德州原油期貨", "DX-Y.NYB": "美元指數", "JPY=X": "美元兌日圓",
          "TLT": "美國 20 年公債 ETF（TLT）", "SPY": "標普 500（SPY，含息、換算台幣）", "QQQ": "那斯達克 100（QQQ，含息、換算台幣）",
          "SOXX": "美國半導體（SOXX，含息、換算台幣）", "JPY": "日圓（兌美元）"}
LEV_REFS = ["0050", "^TWII", "^GSPC", "^NDX", "^DJI", "^SOX", "^N225", "^HSI", "^NSEI", "GC=F",
            "BZ=F", "CL=F", "DX-Y.NYB", "JPY", "TLT"]
ACT_REFS = ["0050", "SPY", "QQQ", "SOXX", "TLT"]
USD_REFS = {"SPY", "QQQ", "SOXX", "TLT"}


def _ser(p: Dict) -> Tuple[pd.Series, List]:
    c = pd.Series({pd.Timestamp(a): float(b) for a, b in (p.get("c") or []) if b}).sort_index()
    return c, p.get("dv") or []


def _ann(x: Optional[float], yrs: float) -> Optional[float]:
    return None if x is None or x <= -100 else ((1 + x / 100) ** (1 / yrs) - 1) * 100


def _mdd(s: pd.Series) -> Optional[float]:
    return float((s / s.cummax() - 1).min() * 100) if len(s) > 20 else None


def _asof_before(s: pd.Series, idx: pd.DatetimeIndex) -> pd.Series:
    """Value of s on the last date strictly before each date of idx (a US close is known before Taipei opens)."""
    s = s.dropna().sort_index()
    pos = s.index.searchsorted(idx, side="left") - 1
    v = np.where(pos >= 0, s.values[np.clip(pos, 0, None)], np.nan)
    return pd.Series(v, index=idx)


def _aligned(ref: pd.Series, idx: pd.DatetimeIndex, lag: int) -> pd.Series:
    """Reference levels on the ETF's trading days: same day (lag 0) or the reference's previous close (lag 1)."""
    if lag == 0:
        return ref.reindex(idx).ffill()
    return _asof_before(ref, idx)


def _weekly(c: pd.Series) -> pd.Series:
    g = c.groupby(c.index.to_period("W-FRI"))
    return pd.Series([s.iloc[-1] for _, s in g], index=pd.DatetimeIndex([s.index[-1] for _, s in g]))


def _best(c: pd.Series, refs: Dict[str, pd.Series], sign: int = 0, weeks: int = 104) -> Optional[Dict]:
    """The reference whose moves track this ETF best, same-day or the reference's previous close, whichever fits.
    Weekly returns over the last two years (Taipei trades while the US sleeps, so daily moves mix two sessions);
    daily returns for ETFs younger than half a year.  sign=−1 asks for an inverse relation."""
    best = None
    wk = len(_weekly(c)) >= 26
    x = (_weekly(c).iloc[-(weeks + 1):] if wk else c.iloc[-250:])
    r = x.pct_change()
    for k, s in refs.items():
        for lag in (0, 1):
            a = _aligned(s, x.index, lag).pct_change()
            j = pd.concat([r, a], axis=1).dropna()
            j = j[(j.iloc[:, 1] != 0)]
            if len(j) < (26 if wk else MIN_DAYS):
                continue
            rho = float(j.iloc[:, 0].corr(j.iloc[:, 1]))
            if not np.isfinite(rho) or (sign and np.sign(rho) != sign):
                continue
            if best is None or abs(rho) > abs(best["corr"]):
                best = {"ref": k, "lag": lag, "corr": rho}
    return best if best and abs(best["corr"]) >= LINK_MIN else None


def _window_ret(s: pd.Series, a: pd.Timestamp, b: pd.Timestamp) -> Optional[float]:
    x = s[(s.index >= a) & (s.index <= b)].dropna()
    return float(x.iloc[-1] / x.iloc[0] - 1) * 100 if len(x) >= 2 else None


def load(d: Optional[Dict] = None) -> Tuple[Dict, Dict, Dict]:
    """→ (nav, {code: (close, dividends)} for ETFs, {sym: (close, dividends)} for references)."""
    d = D.load() if d is None else d
    nav = d.get("nav") or {}
    allp = D.all_series(d)
    etf, ref = {}, {}
    for k, p in allp.items():
        c, dv = _ser(p)
        if len(c) < MIN_DAYS:
            continue
        (ref if k in D.REFS else etf)[k] = (c, dv)
    return nav, etf, ref


# ------------------------------------------------------------------ 1. total return of every ETF
def perf_rows(nav: Dict, etf: Dict) -> List[Dict]:
    base = etf.get(BASE)
    btr = _tr(*base) if base else None
    out = []
    for k, (c, dv) in etf.items():
        v = nav.get(k) or {}
        name = v.get("name") or k
        tr = _tr(c, dv)
        days = (c.index[-1] - c.index[0]).days
        x = {"code": k, "name": name, "kind": D.kind_of(k, name), "since": c.index[0].strftime("%Y-%m-%d"), "days": days,
             "aum": v["units"] * v["nav"] / 1e8 if v.get("units") and v.get("nav") else None,
             "tr1y": _ret(tr, 365), "tr3y": _ann(_ret(tr, 365 * 3), 3), "tr5y": _ann(_ret(tr, 365 * 5 - 10), 5)}
        w = tr[tr.index > tr.index[-1] - pd.Timedelta(days=365)]
        x["vol1y"] = float(w.pct_change().std() * np.sqrt(250) * 100) if len(w) > 120 else None
        x["mdd"] = _mdd(tr[tr.index > tr.index[-1] - pd.Timedelta(days=365 * 3)])
        if btr is not None:
            b1, b3 = _ret(btr, 365), _ann(_ret(btr, 365 * 3), 3)
            x["vs1y"] = x["tr1y"] - b1 if x["tr1y"] is not None and b1 is not None else None
            x["vs3y"] = x["tr3y"] - b3 if x["tr3y"] is not None and b3 is not None else None
        out.append(x)
    return sorted(out, key=lambda x: -(x["tr1y"] if x["tr1y"] is not None else -1e9))


def kind_summary(rows: List[Dict]) -> Dict[str, Dict]:
    g: Dict[str, Dict] = {}
    for x in rows:
        if x["code"] == BASE:
            continue
        s = g.setdefault(x["kind"], {"n": 0, "n1": 0, "beat1": 0, "n3": 0, "beat3": 0, "tr1": []})
        s["n"] += 1
        if x.get("vs1y") is not None:
            s["n1"] += 1
            s["beat1"] += x["vs1y"] > 0
            s["tr1"].append(x["tr1y"])
        if x.get("vs3y") is not None:
            s["n3"] += 1
            s["beat3"] += x["vs3y"] > 0
    for s in g.values():
        s["med1"] = float(np.median(s.pop("tr1"))) if s["n1"] else None
    return g


# ------------------------------------------------------------------ 2. did the payout come out of capital?
def payout_rows(nav: Dict, etf: Dict) -> List[Dict]:
    """ETFs that paid in the last year: over the last 3 years (1 year if younger), price change vs dividends paid.
    Price up → payouts came from gains; price down but total return ≥ 0 → part of the payout was capital handed back;
    total return < 0 → the payouts did not cover the price fall.  0050 over the same window shows how much the market
    itself moved."""
    base = etf.get(BASE)
    out = []
    for k, (c, dv) in etf.items():
        end = c.index[-1]
        y1 = [a for t, a in dv if pd.Timestamp(t) > end - pd.Timedelta(days=365)]
        if not y1 or c.index[0] > end - pd.Timedelta(days=360):
            continue
        yrs = 3 if c.index[0] <= end - pd.Timedelta(days=365 * 3 - 5) else 1
        start = c[c.index >= end - pd.Timedelta(days=365 * yrs)].index[0]
        p0 = float(c[start])
        paid = sum(a for t, a in dv if start < pd.Timestamp(t) <= end)
        pc = (float(c.iloc[-1]) / p0 - 1) * 100
        dy = paid / p0 * 100
        tr = _window_ret(_tr(c, dv), start, end)
        v = nav.get(k) or {}
        name = v.get("name") or k
        x = {"code": k, "name": name, "kind": D.kind_of(k, name), "yrs": yrs, "start": start.strftime("%Y-%m-%d"),
             "price": pc, "paid": dy, "tr": tr, "yld": sum(y1) / float(c.iloc[-1]) * 100,
             "base": _window_ret(base[0], start, end) if base else None}
        x["cls"] = "gain" if pc >= 0 else ("capital" if (tr or 0) >= 0 else "short")
        x["capital_share"] = min(100.0, -pc / dy * 100) if pc < 0 and dy > 0 else 0.0
        out.append(x)
    return sorted(out, key=lambda x: -x["yld"])


# ------------------------------------------------------------------ 3. bond ETFs vs the US 10-year yield
def rate_rows(nav: Dict, etf: Dict, ref: Dict, weeks: int = 104) -> List[Dict]:
    """Weekly total return (TWD) regressed on the change in the 10-year yield (known before Taipei opens) and the
    change in USD/TWD.  beta10 = % move per +0.1 point (10bp) of yield; −10 × beta10 ≈ the duration it behaves like."""
    tnx, fx = (ref.get("^TNX") or (None,))[0], (ref.get("TWD=X") or (None,))[0]
    if tnx is None or fx is None:
        return []
    out = []
    for k, (c, dv) in etf.items():
        v = nav.get(k) or {}
        name = v.get("name") or k
        if D.kind_of(k, name) != "債券":
            continue
        w = _weekly(_tr(c, dv)).iloc[-(weeks + 1):]
        if len(w) < 52:
            continue
        y = _asof_before(tnx, w.index)
        f = _asof_before(fx, w.index)
        j = pd.DataFrame({"r": w.pct_change() * 100, "dy": y.diff() * 10, "fx": f.pct_change() * 100}).dropna()
        if len(j) < 50:
            continue
        X = np.column_stack([np.ones(len(j)), j["dy"].values, j["fx"].values])
        b, *_ = np.linalg.lstsq(X, j["r"].values, rcond=None)
        res = j["r"].values - X @ b
        r2 = 1 - float(res.var() / j["r"].values.var()) if j["r"].values.var() > 0 else 0.0
        x = {"code": k, "name": name, "beta10": float(b[1]), "fxb": float(b[2]), "r2": r2, "n": len(j),
             "aum": v["units"] * v["nav"] / 1e8 if v.get("units") and v.get("nav") else None,
             "tr1y": _ret(_tr(c, dv), 365)}
        x["clear"] = r2 >= R2_MIN and x["beta10"] < 0
        x["dur"] = -10 * x["beta10"] if x["clear"] else None
        out.append(x)
    last = tnx.dropna()
    yr = last[last.index >= last.index[-1] - pd.Timedelta(days=365)]
    for x in out:
        x["y_now"], x["y_1y"] = float(last.iloc[-1]), float(yr.iloc[-1] - yr.iloc[0]) if len(yr) > 1 else None
    return sorted(out, key=lambda x: (not x["clear"], x["beta10"]))


# ------------------------------------------------------------------ 4. leveraged / inverse decay
def lev_factor(code: str, name: str) -> Optional[float]:
    m = re.search(r"正\s*(\d)", name)
    if m:
        return float(m.group(1))
    m = re.search(r"反\s*(\d)?", name)
    if m:
        return -float(m.group(1) or 1)
    return 2.0 if code.endswith("L") else (-1.0 if code.endswith("R") else None)


def lev_rows(nav: Dict, etf: Dict, ref: Dict) -> List[Dict]:
    """Each leveraged / inverse ETF against its multiple × the reference it tracks best (picked by correlation):
    actual 1-year (and 3-year) return vs the simple multiple, and the reference's volatility (the source of decay)."""
    cand = {k: ref[k][0] for k in LEV_REFS if k in ref}
    if "JPY=X" in ref:                                   # yen ETFs move with the yen, i.e. against USD/JPY
        cand["JPY"] = 1 / ref["JPY=X"][0]
    if BASE in etf:
        cand[BASE] = etf[BASE][0]
    out = []
    for k, (c, dv) in etf.items():
        v = nav.get(k) or {}
        name = v.get("name") or k
        if D.kind_of(k, name) != "槓桿反向" and not k.endswith(("L", "R")):
            continue
        L = lev_factor(k, name)
        if L is None:
            continue
        b = _best(c, cand, sign=1 if L > 0 else -1)
        if not b:
            out.append({"code": k, "name": name, "L": L, "ref": None})
            continue
        u = _aligned(cand[b["ref"]], c.index, b["lag"])
        tr = _tr(c, dv)
        x = {"code": k, "name": name, "L": L, "ref": b["ref"], "corr": b["corr"],
             "aum": v["units"] * v["nav"] / 1e8 if v.get("units") and v.get("nav") else None}
        for tag, days in (("1y", 365), ("3y", 365 * 3)):
            if c.index[0] > c.index[-1] - pd.Timedelta(days=days - 5):
                continue
            a = c[c.index >= c.index[-1] - pd.Timedelta(days=days)].index[0]
            act, und = _window_ret(tr, a, c.index[-1]), _window_ret(u, a, c.index[-1])
            if act is None or und is None:
                continue
            x["act" + tag], x["und" + tag] = act, und
            if L * und > -100:                       # "−1 × a +232 % rise" is not a return anyone could have had
                x["mult" + tag], x["gap" + tag] = L * und, act - L * und
        w = u[u.index > u.index[-1] - pd.Timedelta(days=365)].pct_change().dropna()
        x["vol"] = float(w.std() * np.sqrt(250) * 100) if len(w) > 120 else None
        out.append(x)
    return sorted(out, key=lambda x: (x.get("ref") is None, -(x.get("aum") or 0)))


# ------------------------------------------------------------------ 5. active ETFs since launch
def _twd(s: pd.Series, fx: Optional[pd.Series]) -> pd.Series:
    if fx is None:
        return s
    return s * fx.reindex(s.index.union(fx.index)).ffill().reindex(s.index)


def active_rows(nav: Dict, etf: Dict, ref: Dict) -> List[Dict]:
    """Each active ETF from its first close: total return vs the benchmark it moves with most (0050 or a US ETF in
    TWD, picked by correlation), and the worst fall of each over the same span."""
    fx = (ref.get("TWD=X") or (None,))[0]
    cand = {}
    for k in ACT_REFS:
        if k == BASE and BASE in etf:
            cand[k] = _tr(*etf[BASE])
        elif k in ref:
            cand[k] = _twd(_tr(*ref[k]), fx) if k in USD_REFS else _tr(*ref[k])
    out = []
    for k, (c, dv) in etf.items():
        v = nav.get(k) or {}
        name = v.get("name") or k
        if D.kind_of(k, name) != "主動式":
            continue
        tr = _tr(c, dv)
        b = _best(tr, cand, sign=1)
        x = {"code": k, "name": name, "since": c.index[0].strftime("%Y-%m-%d"), "days": len(c),
             "aum": v["units"] * v["nav"] / 1e8 if v.get("units") and v.get("nav") else None,
             "tr": float(tr.iloc[-1] / tr.iloc[0] - 1) * 100, "mdd": _mdd(tr), "ref": None}
        if b:
            u = _aligned(cand[b["ref"]], c.index, b["lag"]).dropna()
            if len(u) >= 2:
                x.update(ref=b["ref"], corr=b["corr"], ref_tr=float(u.iloc[-1] / u.iloc[0] - 1) * 100, ref_mdd=_mdd(u))
                x["diff"] = x["tr"] - x["ref_tr"]
        out.append(x)
    return sorted(out, key=lambda x: x["since"])


def build(d: Optional[Dict] = None) -> Dict:
    nav, etf, ref = load(d)
    if not etf:
        return {"available": False}
    rows = perf_rows(nav, etf)
    b = next((x for x in rows if x["code"] == BASE), None)
    return {"available": True, "rows": rows, "kinds": kind_summary(rows), "base": b, "n_nav": len(nav), "n_px": len(etf),
            "payout": payout_rows(nav, etf), "rate": rate_rows(nav, etf, ref), "lev": lev_rows(nav, etf, ref),
            "active": active_rows(nav, etf, ref),
            "asof": max((c.index[-1] for c, _ in etf.values()), default=pd.Timestamp("1970-01-01")).strftime("%Y-%m-%d")}
