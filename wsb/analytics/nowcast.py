"""公布前估算（nowcast）：GDP、PCE、非農就業在公布之前，用已經公布的公開數據估一個大概的數字，並誠實標示誤差。

  * PCE：CPI 與 PPI 先公布，PCE 的大部分成分已經知道。核心 PCE 月增 ≈ a + b×核心 CPI 月增 + c×PPI（不含食品能源）月增，
    整體 PCE 用整體 CPI 與 PPI 最終需求。2012 年起（排除 2020 年疫情月份）估係數。
  * 非農：非農新增 ≈ a + b×ADP 民間就業變動 + c×初領失業金月均變動。目標月的 ADP 月資料還沒出來時，用 ADP 每週資料
    （較不準，會標示）。
  * GDP：亞特蘭大聯準會 GDPNow（FRED GDPNOW）的最新估計。

每個模型都做「走步樣本外」測試：最近 36 個月（GDP：最近 24 季）每次只用當時以前的資料估係數、再估下一期，誤差的
均方根（RMSE）就是頁面上的「誤差約 ±」。注意：FRED 給的是修正後的歷史數字，不是當初第一次公布的數字，所以真正
即時使用時誤差通常更大。描述用的估算，不是預測，也不是買賣建議。"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

OOS_N = 36
COVID = ("2020-03-01", "2021-06-01")


def _s(d: Dict, k: str) -> pd.Series:
    v = d.get(k) or {}
    if not v:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    s = pd.Series(v, dtype=float)
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def _mm(s: pd.Series) -> pd.Series:
    return (s / s.shift(1) - 1) * 100


def _fit(y: pd.Series, X: pd.DataFrame) -> Optional[np.ndarray]:
    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    df = df[(df.index < COVID[0]) | (df.index > COVID[1])]
    if len(df) < 36:
        return None
    A = np.column_stack([np.ones(len(df)), df[X.columns].values])
    return np.linalg.lstsq(A, df["y"].values, rcond=None)[0]


def _pred(b: np.ndarray, x: pd.Series) -> float:
    return float(b[0] + np.dot(b[1:], x.values))


def _oos(y: pd.Series, X: pd.DataFrame, n: int = OOS_N, start: str = "2012-01-01") -> Optional[float]:
    """Walk-forward: for each of the last n periods with a known y, fit on everything before it and predict it."""
    y, X = y[y.index >= start], X[X.index >= start]
    idx = [t for t in pd.concat([y, X], axis=1).dropna().index if not (COVID[0] <= t.strftime("%Y-%m-%d") <= COVID[1])][-n:]
    err = []
    for t in idx:
        b = _fit(y[y.index < t], X[X.index < t])
        if b is not None:
            err.append(float(y[t]) - _pred(b, X.loc[t]))
    return float(np.sqrt(np.mean(np.square(err)))) if len(err) >= n // 2 else None


def _model(y: pd.Series, X: pd.DataFrame, start: str = "2012-01-01") -> Optional[Dict]:
    y, X = y[y.index >= start], X[X.index >= start]
    b = _fit(y, X)
    rmse = _oos(y, X, start=start)
    return None if b is None or rmse is None else {"b": b, "rmse": rmse}


def _month(t: pd.Timestamp) -> str:
    return t.strftime("%Y-%m")


# ───────────────────────── PCE ─────────────────────────
def pce(d: Dict) -> Optional[Dict]:
    out: Dict = {}
    for k, ycol, xs, zh in (("core", "PCEPILFE", ("CPILFESL", "PPIFES"), "核心 PCE"), ("head", "PCEPI", ("CPIAUCSL", "PPIFIS"), "整體 PCE")):
        lv = _s(d, ycol)
        y = _mm(lv)
        X = pd.concat([_mm(_s(d, c)).rename(c) for c in xs], axis=1)
        if lv.empty or X.dropna().empty:
            continue
        m = _model(y, X)
        if m is None:
            continue
        have = X.dropna()
        tgt = have.index[-1]
        if tgt <= lv.index[-1]:                         # CPI/PPI for a month whose PCE is already out → nothing pending
            continue
        mm = _pred(m["b"], have.loc[tgt])
        yy = None
        prev, base = lv.index[-1], tgt - pd.DateOffset(months=12)
        if prev == tgt - pd.DateOffset(months=1) and base in lv.index:
            yy = (float(lv[prev]) * (1 + mm / 100) / float(lv[base]) - 1) * 100
        out[k] = {"zh": zh, "month": _month(tgt), "mm": round(mm, 3), "yy": None if yy is None else round(yy, 2),
                  "rmse": round(m["rmse"], 3), "inputs": {c: round(float(have.loc[tgt, c]), 3) for c in xs}}
    return out or None


# ───────────────────────── 非農 ─────────────────────────
def _claims_month(d: Dict) -> Tuple[pd.Series, pd.Series]:
    """Monthly mean of weekly initial claims (k) and the number of weeks seen in that month."""
    ic = _s(d, "ICSA") / 1000
    if ic.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    g = ic.groupby(ic.index.to_period("M"))
    mean, n = g.mean(), g.size()
    mean.index, n.index = mean.index.to_timestamp(), n.index.to_timestamp()
    return mean, n


def nfp(d: Dict) -> Optional[Dict]:
    pay = _s(d, "PAYEMS")
    adp = _s(d, "ADPMNUSNERSA") / 1000
    if pay.empty or adp.empty:
        return None
    y = pay.diff()
    cm, _n = _claims_month(d)
    lag = y.rolling(3).mean().shift(1)            # the recent trend (last 3 known months) — without it a claims-only
    X = pd.concat([adp.diff().rename("adp"), cm.diff().rename("claims"), lag.rename("lag")], axis=1)   # fit is just the 2012–19 average
    m = _model(y, X)
    if m is None:
        return None
    tgt = pay.index[-1] + pd.DateOffset(months=1)
    prev = tgt - pd.DateOffset(months=1)
    if tgt not in cm.index or prev not in cm.index:
        return None
    c = float(cm[tgt] - cm[prev])
    lg = float(y.dropna().iloc[-3:].mean())
    src, a = "adp", None
    if tgt in adp.index and prev in adp.index:
        a = float(adp[tgt] - adp[prev])
    else:
        w = _s(d, "ADPWNUSNERSA") / 1000
        w = w[(w.index >= tgt) & (w.index < tgt + pd.DateOffset(months=1))]
        if not w.empty and prev in adp.index:
            a, src = float(w.iloc[-1] - adp[prev]), "weekly"
    if a is None:                                   # no ADP for the month yet: claims only (its own, larger error)
        m = _model(y, X[["claims", "lag"]])
        if m is None:
            return None
        est, src = _pred(m["b"], pd.Series([c, lg])), "claims"
    else:
        est = _pred(m["b"], pd.Series([a, c, lg]))
    return {"month": _month(tgt), "est": round(est), "rmse": round(m["rmse"]), "adp": None if a is None else round(a),
            "claims": round(c, 1), "lag": round(lg), "src": src, "weekly": src == "weekly", "weeks": int(_n.get(tgt, 0))}


# ───────────────────────── GDP ─────────────────────────
def gdp(d: Dict) -> Optional[Dict]:
    gn, act = _s(d, "GDPNOW"), _s(d, "A191RL1Q225SBEA")
    if gn.empty:
        return None
    q = gn.index[-1]
    if q in act.index:                                   # the latest GDPNow quarter is already published
        return None
    both = pd.concat([gn.rename("n"), act.rename("a")], axis=1).dropna().tail(24)
    rmse = float(np.sqrt(np.mean(np.square(both["a"] - both["n"])))) if len(both) >= 12 else None
    return {"quarter": f"{q.year}Q{(q.month - 1) // 3 + 1}", "est": round(float(gn[q]), 2), "rmse": None if rmse is None else round(rmse, 2),
            "n": int(len(both))}


def _qkey(t: pd.Timestamp) -> str:
    return f"{t.year}Q{(t.month - 1) // 3 + 1}"


def estimates(d: Dict) -> Dict[str, Dict]:
    """Every pending estimate keyed by target ('pce:2026-09', 'nfp:2026-10', 'gdp:2026Q3')."""
    out: Dict[str, Dict] = {}
    p = pce(d)
    if p:
        mon = (p.get("core") or p.get("head"))["month"]
        out[f"pce:{mon}"] = p
    n = nfp(d)
    if n:
        out[f"nfp:{n['month']}"] = n
    g = gdp(d)
    if g:
        out[f"gdp:{g['quarter']}"] = g
    return out


def actual_for(d: Dict, key: str) -> Optional[Dict]:
    """The published value for a logged target, once FRED has it (same units as the estimate)."""
    kind, per = key.split(":", 1)
    if kind == "pce":
        t = pd.Timestamp(per + "-01")
        out = {}
        for k, col in (("core", "PCEPILFE"), ("head", "PCEPI")):
            lv = _s(d, col)
            if t in lv.index and t - pd.DateOffset(months=1) in lv.index:
                out[k] = round((float(lv[t]) / float(lv[t - pd.DateOffset(months=1)]) - 1) * 100, 3)
        return out or None
    if kind == "nfp":
        t = pd.Timestamp(per + "-01")
        pay = _s(d, "PAYEMS")
        if t in pay.index and t - pd.DateOffset(months=1) in pay.index:
            return {"v": round(float(pay[t] - pay[t - pd.DateOffset(months=1)]))}
        return None
    if kind == "gdp":
        act = _s(d, "A191RL1Q225SBEA")
        hit = [t for t in act.index if _qkey(t) == per]
        return {"v": round(float(act[hit[0]]), 2)} if hit else None
    return None


def update_log(d: Dict, today: Optional[date] = None) -> Dict[str, Dict]:
    """Keep the latest estimate for every target until its actual appears, then freeze it with the actual (first seen)."""
    log = dict(d.get("log") or {})
    asof = (today or date.today()).isoformat()
    for k, rec in list(log.items()):                  # actuals first, so a half-published target is never re-estimated
        if rec.get("actual") is None:
            a = actual_for(d, k)
            if a:
                log[k] = {**rec, "actual": a, "seen": asof}
    for k, est in estimates(d).items():
        rec = log.get(k) or {}
        if rec.get("actual") is None:
            log[k] = {"est": est, "asof": asof}
    keep = sorted(log)[-24:]
    return {k: log[k] for k in keep}


# ───────────────────────── 對應到財經日曆事件 ─────────────────────────
def target_for(key: str, day: str) -> Optional[str]:
    """Which period an event is about: PCE / jobs report = the previous month; GDP = the previous quarter."""
    t = pd.Timestamp(day)
    if key in ("pce", "nfp"):
        return f"{key}:{_month(t - pd.DateOffset(months=1))}"
    if key == "gdp":
        return f"gdp:{_qkey(t - pd.DateOffset(months=3))}"
    return None


def _num(x) -> Optional[float]:
    from ..data import econcal as EC
    return EC.num(x)


def _row(e: Dict, label: str) -> Dict:
    return next((r for r in e.get("rows") or [] if r.get("label") == label), {})


def _vs_cons(est: float, cons: Optional[float], rmse: float, unit: str, hot: str, cold: str) -> str:
    if cons is None:
        return ""
    gap = est - cons
    if abs(gap) < 0.5 * rmse:
        return f"；和市場預期 {cons:g}{unit} 差不多（差距小於估算誤差的一半）"
    return f"；比市場預期 {cons:g}{unit} {'高' if gap > 0 else '低'}，估算偏向「{hot if gap > 0 else cold}」，但誤差不小，只當方向參考"


def _surprise(a: float, est: float, rmse: float) -> str:
    z = (a - est) / rmse if rmse else 0
    return ("在估算誤差內（不算意外）" if abs(z) < 1 else "超出估算誤差（明顯意外）") + f"，差 {z:+.1f} 倍誤差"


def describe(e: Dict, log: Dict[str, Dict]) -> Optional[Dict[str, str]]:
    """One plain-language line for an event card: the pre-release estimate (upcoming) or estimate-vs-actual (released)."""
    tk = target_for(e["key"], e["date"])
    rec = (log or {}).get(tk) if tk else None
    if not rec:
        return None
    est = rec["est"]
    if e["key"] == "pce":
        c = est.get("core") or {}
        h = est.get("head") or {}
        if not c and not h:
            return None
        if e.get("released"):
            a = _num(_row(e, "核心 PCE 月增").get("actual"))
            if a is None or not c:
                return None
            return {"zh": f"事前估算：核心 PCE 月增 {c['mm']:.2f}%（誤差約 ±{c['rmse']:.2f}）→ 公布 {a:g}%，{_surprise(a, c['mm'], c['rmse'])}。"
                          "公布值只到小數一位，0.05 以內的差距可能只是四捨五入。",
                    "en": f"Estimate: core PCE m/m {c['mm']:.2f}% (±{c['rmse']:.2f}) → actual {a:g}%."}
        cons = _num(_row(e, "核心 PCE 月增").get("cons"))
        s = (f"公布前估算（用已公布的 {c['month']} CPI、PPI 推算）：核心 PCE 月增約 {c['mm']:.2f}%"
             + (f"、年增約 {c['yy']:.1f}%" if c.get("yy") is not None else "") + f"（過去 36 個月誤差約 ±{c['rmse']:.2f}）") if c else ""
        if h:
            s += f"；整體 PCE 月增約 {h['mm']:.2f}%" + (f"、年增約 {h['yy']:.1f}%" if h.get("yy") is not None else "")
        if c:
            s += _vs_cons(c["mm"], cons, c["rmse"], "%", "通膨偏熱", "通膨降溫")
        return {"zh": s + "。", "en": f"Pre-release estimate: core PCE m/m ~{c.get('mm', float('nan')):.2f}% (±{c.get('rmse', float('nan')):.2f})."}
    if e["key"] == "nfp":
        if e.get("released"):
            a = _num(_row(e, "非農新增就業（千人）").get("actual"))
            if a is None:
                return None
            return {"zh": f"事前估算：非農新增約 {est['est']:+,}K（誤差約 ±{est['rmse']:,}K）→ 公布 {a:+,.0f}K，{_surprise(a, est['est'], est['rmse'])}。",
                    "en": f"Estimate {est['est']:+,}k (±{est['rmse']:,}k) → actual {a:+,.0f}k."}
        cons = _num(_row(e, "非農新增就業（千人）").get("cons"))
        src = est.get("src") or ("weekly" if est.get("weekly") else "adp")
        lead = (f"ADP 還沒公布，只用近 3 個月非農平均 {est.get('lag', 0):+,}K 和初領失業金，最不準" if src == "claims" else
                f"ADP 每週資料（月資料還沒出來，較不準）變動 {est['adp']:+,}K" if src == "weekly" else f"ADP 月資料變動 {est['adp']:+,}K")
        s = (f"公布前估算（{lead}；初領失業金月均變動 {est['claims']:+.1f}K，本月已有 {est['weeks']} 週）："
             f"非農新增約 {est['est']:+,}K（過去 36 個月誤差約 ±{est['rmse']:,}K，誤差很大）")
        s += _vs_cons(est["est"], cons, est["rmse"], "K", "就業偏強", "就業偏弱")
        return {"zh": s + "。", "en": f"Pre-release estimate: payrolls ~{est['est']:+,}k (±{est['rmse']:,}k)."}
    if e["key"] == "gdp":
        err = f"（過去 {est['n']} 季誤差約 ±{est['rmse']:.1f}）" if est.get("rmse") else ""
        if e.get("released"):
            a = _num(_row(e, "GDP").get("actual"))
            if a is None:
                return None
            return {"zh": f"事前估算：GDPNow {est['est']:.1f}%{err} → 公布 {a:g}%，" + (_surprise(a, est["est"], est["rmse"]) if est.get("rmse") else f"差 {a - est['est']:+.1f} 個百分點") + "。",
                    "en": f"GDPNow {est['est']:.1f}% → actual {a:g}%."}
        cons = _num(_row(e, "GDP").get("cons"))
        s = f"公布前估算：亞特蘭大聯準會 GDPNow 估 {est['quarter']} 年化成長 {est['est']:.1f}%{err}"
        s += _vs_cons(est["est"], cons, est.get("rmse") or 1.0, "%", "成長偏強", "成長偏弱")
        return {"zh": s + "。", "en": f"GDPNow {est['quarter']}: {est['est']:.1f}%."}
    return None


def attach(events: List[Dict], log: Dict[str, Dict]) -> None:
    for e in events:
        if e.get("key") in ("pce", "nfp", "gdp"):
            try:
                x = describe(e, log)
            except Exception:  # noqa: BLE001
                x = None
            if x:
                e["nowcast"] = x
