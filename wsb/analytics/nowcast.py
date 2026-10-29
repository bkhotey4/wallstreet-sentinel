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


# plain-language meaning of a hot / in-line / cool print (written as transmission, not a forecast)
MEAN = {
    "pce": {"what": "PCE 是聯準會最看重的物價數字，看「東西一個月漲了多少」。聯準會希望一年只漲 2%。",
            "unit": "%", "nm": "核心 PCE 月增",
            "hot": "物價還在加速 → 聯準會更可能升息、更晚降息 → 美債殖利率往上、美元偏強；要很久才回本的科技股、AI 股通常壓力最大，台股電子跟著費半。",
            "mid": "和大家預期的差不多 → 市場鬆一口氣，影響通常不大，焦點回到財報。",
            "cool": "物價降溫 → 升息壓力變小 → 殖利率回落；成長股、半導體通常受惠。如果同時消費也明顯轉弱，市場會轉而擔心景氣。",
            "next": "接下來看：殖利率是不是跟著動、12 月升息機率有沒有變（財經日曆 FOMC 卡）。"},
    "gdp": {"what": "GDP 是美國經濟這一季成長多快（換算成一年的速度）。2% 左右算正常，0 以下代表萎縮。",
            "unit": "%", "nm": "GDP",
            "hot": "經濟比想像熱 → 聯準會更不需要降息、甚至可能升息 → 殖利率往上；景氣循環股、金融股相對受惠，估值高的科技股承壓。",
            "mid": "和預期差不多 → 影響通常有限，市場更在意同一時間公布的 PCE 物價。",
            "cool": "經濟放緩 → 衰退擔憂上升 → 殖利率回落、防禦類股相對抗跌；如果主要是庫存或進出口拖累，市場通常不太在意。",
            "next": "接下來看：扣掉庫存和進出口後的「最終銷售」，那才是真正的需求。"},
    "nfp": {"what": "非農就業是美國上個月多了多少工作（不含農業）。數字越大代表就業市場越熱。",
            "unit": "K", "nm": "非農新增就業（千人）",
            "hot": "就業很熱 → 薪水和物價壓力大 → 升息機會變高、殖利率往上；如果時薪也偏高，對股市更不利。",
            "mid": "和預期差不多 → 看失業率和時薪，失業率持平市場通常鬆一口氣。",
            "cool": "就業轉弱 → 升息壓力變小、殖利率回落；但如果失業率也明顯跳升，市場會轉為擔心衰退，股市可能跟著跌。",
            "next": "接下來看：失業率、時薪，以及前兩個月有沒有被大幅修正。"},
}


WIDTH = {"pce": 0.1, "gdp": 0.5, "nfp": 50.0}     # how far from the consensus a print must be for markets to call it a surprise


def _band(center: float, key: str) -> Tuple[float, float]:
    w = WIDTH[key]
    if key == "nfp":
        c = round(center / 10) * 10
        return c - w, c + w
    c = round(center, 1)
    return round(c - w, 1), round(c + w, 1)


def _fmt(v: float, key: str) -> str:
    return f"{v:+,.0f}K" if key == "nfp" else f"{v:.1f}%"


def describe(e: Dict, log: Dict[str, Dict]) -> Optional[Dict]:
    """A plain-language explainer for one event: what it is, the estimate, what a high / middle / low print would mean
    (upcoming), or what the actual print means (released).  "zh" is a one-line version for the calendar row."""
    tk = target_for(e["key"], e["date"])
    rec = (log or {}).get(tk) if tk else None
    if not rec:
        return None
    k, est = e["key"], rec["est"]
    mn = MEAN[k]
    if k == "pce":
        c = est.get("core") or {}
        if not c:
            return None
        v, rmse = c["mm"], c["rmse"]
        say = f"網站估 {c['month'][5:].lstrip('0')} 月核心物價比上個月漲約 {v:.2f}%" + (f"（一年約漲 {c['yy']:.1f}%）" if c.get("yy") is not None else "")
        how = (f"用同月已公布的 CPI、PPI 推算（PCE 的大部分成分這兩份已經有了）。核心 = 扣掉食物和能源。平常誤差約 ±{rmse:.2f} 個百分點"
               "（最近 36 個月走步樣本外測試，用修正後的歷史數字，實際誤差通常更大）。"
               + (f"整體 PCE（含食物能源）估月增約 {est['head']['mm']:.2f}%" + (f"、年增約 {est['head']['yy']:.1f}%" if est['head'].get('yy') is not None else "") + "。" if est.get("head") else ""))
    elif k == "gdp":
        v, rmse = est["est"], est.get("rmse") or 1.0
        say = f"亞特蘭大聯準會的即時估算（GDPNow）：第 {est['quarter'][-1]} 季經濟成長約 {v:.1f}%"
        how = f"GDPNow 隨每筆新數據自動更新。過去 {est.get('n', 0)} 季平均誤差約 ±{rmse:.1f} 個百分點（對照修正後的 GDP）。"
    else:
        v, rmse = float(est["est"]), float(est["rmse"])
        say = f"網站估 {est['month'][5:].lstrip('0')} 月新增約 {v / 10:+.0f} 萬個工作"
        src = est.get("src") or ("weekly" if est.get("weekly") else "adp")
        how = ((f"ADP 還沒公布，只用近 3 個月平均（{est.get('lag', 0):+,}K）和初領失業金推算，最不準。" if src == "claims" else
                "用 ADP 每週資料（月資料還沒出來）和初領失業金推算。" if src == "weekly" else "用 ADP 民間就業和初領失業金推算。")
               + f"平常誤差約 ±{rmse:,.0f}K（±{rmse / 10:.0f} 萬個），非農常有意外。")
    cons = _num(_row(e, mn["nm"]).get("cons"))
    ref = cons if cons is not None else v
    lo, hi = _band(ref, k)
    rn = "市場預期" if cons is not None else "網站估算"
    if k == "pce":                                  # PCE prints to one decimal: high / exactly the middle / low
        mid_lab = f"{_fmt((lo + hi) / 2, k)}（和{rn}一樣）"
        hot_lab, cool_lab = f"{_fmt(hi, k)} 以上（高於{rn}）", f"{_fmt(lo, k)} 以下（低於{rn}）"
    else:
        mid_lab = f"{_fmt(lo, k)} ～ {_fmt(hi, k)}（和{rn}差不多）"
        hot_lab, cool_lab = f"高於 {_fmt(hi, k)}（明顯高於{rn}）", f"低於 {_fmt(lo, k)}（明顯低於{rn}）"
    out = {"key": k, "what": mn["what"], "say": say, "how": how, "cons": cons, "next": mn["next"],
           "bands": [(hot_lab, mn["hot"]), (mid_lab, mn["mid"]), (cool_lab, mn["cool"])]}
    if e.get("released"):
        a = _num(_row(e, mn["nm"]).get("actual"))
        if a is None:
            return None
        side = "hot" if a >= hi - 1e-9 and (k == "pce" or a > hi) else "cool" if a <= lo + 1e-9 and (k == "pce" or a < lo) else "mid"
        word = {"hot": f"高於{rn}", "cool": f"低於{rn}", "mid": f"和{rn}差不多"}[side]
        out["result"] = f"公布 {_fmt(a, k)}（網站事前估 {_fmt(v, k)}）：{word}。代表：{mn[side]}"
        out["side"] = side
        out["zh"] = f"事前估算 {_fmt(v, k)} → 公布 {_fmt(a, k)}，{word}。"
    else:
        out["zh"] = say + f"（平常誤差 ±{_fmt(rmse, k).lstrip('+')}）" + ("" if cons is None else f"，市場預期 {_fmt(cons, k)}") + "。"
    out["en"] = f"Estimate {_fmt(v, k)} (±{rmse:g})."
    return out


def attach(events: List[Dict], log: Dict[str, Dict]) -> None:
    for e in events:
        if e.get("key") in ("pce", "nfp", "gdp"):
            try:
                x = describe(e, log)
            except Exception:  # noqa: BLE001
                x = None
            if x:
                e["nowcast"] = x
