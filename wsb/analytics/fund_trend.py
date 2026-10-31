"""財報走向判斷：只看公司自己的 SEC 季報，判斷「本業正在變好還是變差」，估下一季營收成長，並公開這套判斷過去的成績。

資料：個股估值體檢（stock_check）同一份 SEC XBRL 季資料（大型美股觀察名單）與每週股價，不另抓資料。

① 四個訊號（每季，近 12 個月合計，避免季節性）
     營收成長加速：最近 2 季營收年增率的平均 − 前 2 季的平均
     毛利率變化、淨利率變化、自由現金流率變化：近 12 個月 vs 一年前（百分點）
   每個訊號和「這家公司自己過去這個訊號的平常變動」比：變動小於平常的 1/4 當作持平（死區由資料決定，不寫死門檻）。
   加總：+2 以上＝改善中、−2 以下＝轉弱中、其他＝持平／分歧。銀行沒有毛利率與自由現金流，只用其餘訊號。
② 下一季營收年增率估算：全部公司一起估一條簡單迴歸（下一季年增 ≈ a + b×本季年增 + c×加速度），走步樣本外測試
   （每次只用當時以前的資料）算誤差；若沒有比「下一季＝本季」更準，就直接用本季年增並照實標示。
③ 判斷的歷史成績：過去每一季做同樣判斷，看
     兩季後淨利率真的比較高的比例（基本面有沒有說中）
     財報公布後（季末 + 45 天）26 週，股價比同名單平均多或少多少（以季為單位重抽 1 萬次算 90% 區間）
限制：名單是現在的大型股（倖存者偏差）、只有約 20 家、股價只有約 6 年；財報數字是修正後的版本；這是描述與歷史統計，
不是預測股價，也不是買賣建議。"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .stock_check import BANKS, PUB_LAG, _qs, ttm

SIGS = {"accel": ("營收成長加速", "Revenue acceleration"), "gm": ("毛利率", "Gross margin"),
        "nm": ("淨利率", "Net margin"), "fcf": ("自由現金流率", "FCF margin")}
DEAD = 0.25              # a change smaller than a quarter of the company's own usual change counts as flat
OOS_Q = 12               # walk-forward quarters for the revenue forecast error
H_WEEKS = 26
N_SIM = 10_000
SEED = 20261031
CLIP = 100.0             # growth beyond ±100 % (mergers, tiny bases) is clipped for the regression


def _qv(p: Dict, k: str, q: str) -> Optional[float]:
    return (p.get(k) or {}).get(q)


def _ratio(p: Dict, num: str, den: str, q: str, sub: Optional[str] = None) -> Optional[float]:
    a, b = ttm(p.get(num) or {}, q), ttm(p.get(den) or {}, q)
    if sub:
        c = ttm(p.get(sub) or {}, q)
        a = None if a is None or c is None else a - c
    return a / b * 100 if a is not None and b and b > 0 else None


def _yoy(p: Dict, q: str) -> Optional[float]:
    a, b = _qv(p, "rev", q), _qv(p, "rev", _qs(q, 5)[0])
    return (a / b - 1) * 100 if a is not None and b and b > 0 else None


def panel(p: Dict, bank: bool = False) -> pd.DataFrame:
    """One row per calendar quarter: revenue YoY, acceleration and the year-on-year change of each margin."""
    qs = sorted(p.get("rev") or {})
    rows = []
    for q in qs:
        g = _yoy(p, q)
        if g is None:
            continue
        q1, q2, q3 = _qs(q, 4)[:3][::-1]
        prev = [_yoy(p, x) for x in (q1, q2, q3)]
        acc = (g + prev[0]) / 2 - (prev[1] + prev[2]) / 2 if None not in prev else None
        q4 = _qs(q, 5)[0]
        r = {"q": q, "g": g, "accel": acc}
        for k, (n, d, s) in {"gm": ("gp", "rev", None), "nm": ("ni", "rev", None), "fcf": ("ocf", "rev", "capex")}.items():
            if bank and k in ("gm", "fcf"):
                r[k] = None
                continue
            a, b = _ratio(p, n, d, q, s), _ratio(p, n, d, q4, s)
            r[k] = a - b if a is not None and b is not None else None
            r[k + "_lv"] = a
        oc, cx = ttm(p.get("ocf") or {}, q), ttm(p.get("capex") or {}, q)
        r["cx_ocf"] = cx / oc * 100 if not bank and oc and oc > 0 and cx is not None else None
        rows.append(r)
    return pd.DataFrame(rows).set_index("q") if rows else pd.DataFrame()


def score(df: pd.DataFrame, bank: bool = False) -> pd.DataFrame:
    """Each signal → +1 / 0 / −1 against the company's own usual change (dead band from the data), then the label."""
    df = df.copy()
    pts = []
    for k in SIGS:
        x = df[k].astype(float) if k in df else pd.Series(np.nan, index=df.index)
        sd = x.expanding(8).std().shift(1)                       # only what was known before this quarter
        band = DEAD * sd
        s = pd.Series(np.where(x > band, 1, np.where(x < -band, -1, 0)), index=df.index, dtype=float)
        s[x.isna() | sd.isna()] = np.nan
        df["s_" + k] = s
        pts.append(s)
    m = pd.concat(pts, axis=1)
    df["n_sig"] = m.notna().sum(axis=1)
    df["score"] = m.sum(axis=1, min_count=1)
    need = 2 if bank else 3                                       # banks have revenue and net margin only
    df["label"] = np.where(df["n_sig"] < need, None, np.where(df["score"] >= 2, "up", np.where(df["score"] <= -2, "down", "flat")))
    return df


# ------------------------------------------------------------------ next-quarter revenue growth
def _xy(panels: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for sym, df in panels.items():
        g = df["g"].clip(-CLIP, CLIP)
        nxt = g.shift(-1)
        for q in df.index:
            rows.append({"sym": sym, "q": q, "g": g[q], "acc": df.loc[q, "accel"], "y": nxt[q]})
    return pd.DataFrame(rows)


def _fit(d: pd.DataFrame) -> Optional[np.ndarray]:
    d = d.dropna(subset=["g", "acc", "y"])
    if len(d) < 60:
        return None
    A = np.column_stack([np.ones(len(d)), d["g"], d["acc"]])
    return np.linalg.lstsq(A, d["y"].values, rcond=None)[0]


def forecast_model(panels: Dict[str, pd.DataFrame]) -> Optional[Dict]:
    """Pooled regression with a walk-forward error; falls back to 'next = this quarter' when that is as good."""
    d = _xy(panels)
    if d.empty:
        return None
    qs = sorted(d.dropna(subset=["y"])["q"].unique())[-OOS_Q:]
    em, en = [], []
    for q in qs:
        b = _fit(d[d["q"] < _qs(q, 2)[0]])                 # y of the training rows must be known by quarter q
        t = d[(d["q"] == q)].dropna(subset=["g", "acc", "y"])
        if b is None or t.empty:
            continue
        em += list(t["y"] - (b[0] + b[1] * t["g"] + b[2] * t["acc"]))
        en += list(t["y"] - t["g"])
    if len(em) < 30:
        return None
    rm, rn = float(np.sqrt(np.mean(np.square(em)))), float(np.sqrt(np.mean(np.square(en))))
    b = _fit(d)
    use = b is not None and rm < rn
    return {"b": b.tolist() if use else None, "rmse": rm if use else rn, "rmse_naive": rn, "rmse_model": rm, "n_oos": len(em), "model": use}


def predict(m: Dict, g: float, acc: Optional[float]) -> float:
    g = max(-CLIP, min(CLIP, g))
    if m.get("b") and acc is not None:
        b = m["b"]
        return float(b[0] + b[1] * g + b[2] * acc)
    return float(g)


# ------------------------------------------------------------------ track record
def _qend(q: str) -> pd.Timestamp:
    return pd.Timestamp(year=int(q[:4]), month=int(q[-1]) * 3, day=1) + pd.offsets.MonthEnd(0)


def track(scored: Dict[str, pd.DataFrame], px: Dict[str, pd.Series]) -> Dict:
    """For every past label: did the net margin two quarters later come in higher, and the 26-week return after the
    report vs the same list's average (equal weight, same dates)."""
    closes = pd.DataFrame({s: v for s, v in px.items() if len(v)}).sort_index()
    rows = []
    for sym, df in scored.items():
        for q in df.index:
            lab = df.loc[q, "label"]
            if lab is None or (isinstance(lab, float) and np.isnan(lab)):
                continue
            later = [x for x in df.index if x > q]
            fut = later[1] if len(later) >= 2 else None
            nm_now, nm_fut = df.loc[q].get("nm_lv"), (df.loc[fut].get("nm_lv") if fut else None)
            hit = None if nm_now is None or nm_fut is None or pd.isna(nm_now) or pd.isna(nm_fut) else bool(nm_fut > nm_now)
            ex = None
            if sym in closes and not closes.empty:
                t0 = _qend(q) + pd.Timedelta(days=PUB_LAG)
                i0 = closes.index.searchsorted(t0)
                if t0 < closes.index[0] or i0 >= len(closes):          # before the price history starts: no return
                    i0 = len(closes)
                i1 = i0 + H_WEEKS
                if i1 < len(closes):
                    r = closes.iloc[i1] / closes.iloc[i0] - 1
                    if pd.notna(r.get(sym)):
                        ex = float((r[sym] - r.drop(sym).mean()) * 100)
            rows.append({"sym": sym, "q": q, "label": lab, "nm_up": hit, "ex": ex})
    t = pd.DataFrame(rows)
    out: Dict = {"n": int(len(t))}
    if t.empty:
        return out
    rng = np.random.default_rng(SEED)
    for lab in ("up", "flat", "down"):
        s = t[t["label"] == lab]
        f = s["nm_up"].dropna()
        e = s.dropna(subset=["ex"])
        rec = {"n": int(len(s)), "nm_hit": float(f.mean() * 100) if len(f) >= 10 else None, "nm_n": int(len(f))}
        if len(e) >= 20 and e["q"].nunique() >= 6:
            groups = [g["ex"].values for _, g in e.groupby("q")]
            sums, sizes = np.array([g.sum() for g in groups]), np.array([len(g) for g in groups])
            pick = rng.integers(0, len(groups), size=(N_SIM, len(groups)))
            means = sums[pick].sum(axis=1) / sizes[pick].sum(axis=1)
            rec.update({"ex": float(e["ex"].mean()), "ex_lo": float(np.percentile(means, 5)), "ex_hi": float(np.percentile(means, 95)),
                        "beat": float((e["ex"] > 0).mean() * 100), "ex_n": int(len(e)), "from": e["q"].min(), "to": e["q"].max()})
        out[lab] = rec
    return out


# ------------------------------------------------------------------ what to watch at the next report
def watch(r: Dict, bank: bool) -> str:
    """The weakest signal decides what to look at next time — a checklist, not a call."""
    if r.get("cx_ocf") is not None and r["cx_ocf"] >= 80:
        return f"資本支出已吃掉營運現金流的 {r['cx_ocf']:.0f}%：看下次的資本支出指引與自由現金流能否轉正或維持。"
    weak = [k for k in SIGS if r.get("s_" + k) == -1]
    if "accel" in weak:
        return "營收成長在放慢：看下一季營收指引，以及放慢是單一產品還是全面。"
    if "gm" in weak:
        return "毛利率下滑：看是價格競爭、成本上升，還是產品組合改變（公司說明會通常會講）。"
    if "fcf" in weak:
        return "自由現金流率下滑：看是投資加大（之後可能有回報）還是本業收款變慢。"
    if "nm" in weak:
        return "淨利率下滑：看營業費用、利息或一次性項目，分清楚是本業還是帳面因素。"
    if r.get("label") == "up":
        return "訊號大致改善：看能否延續，特別是營收加速有沒有帶動利潤率一起往上。"
    return "訊號互相抵銷：看下次財報哪個方向先打破僵局。"


LABEL = {"up": ("改善中", "Improving"), "flat": ("持平／分歧", "Mixed"), "down": ("轉弱中", "Weakening")}


def build(d: Optional[Dict] = None) -> Optional[Dict]:
    from . import stock_check as SCK
    d = d if d is not None else SCK.load()
    facts, pxd = d.get("facts") or {}, d.get("px") or {}
    panels, scored, px, names = {}, {}, {}, {}
    for sym in SCK.universe():
        p = facts.get(sym)
        if not p:
            continue
        df = panel(p, sym in BANKS)
        if len(df) < 12:
            continue
        panels[sym] = df
        scored[sym] = score(df, sym in BANKS)
        names[sym] = p.get("name") or sym
        s = pd.Series(pxd.get(sym) or {}, dtype=float)
        s.index = pd.to_datetime(s.index)
        px[sym] = s.sort_index()
    if not scored:
        return None
    m = forecast_model(panels)
    rows = []
    today = pd.Timestamp.today()
    for sym, df in scored.items():
        last = df.dropna(subset=["g"]).iloc[-1]
        q = df.dropna(subset=["g"]).index[-1]
        if (today - _qend(q)).days > 300:                       # stale filer — blank rather than old
            continue
        r = {"sym": sym, "name": names[sym], "q": q, "bank": sym in BANKS, "g": float(last["g"]),
             "label": last["label"], "score": None if pd.isna(last["score"]) else int(last["score"])}
        for k in SIGS:
            v = last.get(k)
            r[k] = None if v is None or pd.isna(v) else float(v)
            sv = last.get("s_" + k)
            r["s_" + k] = None if sv is None or pd.isna(sv) else int(sv)
        r["cx_ocf"] = None if pd.isna(last.get("cx_ocf")) else float(last["cx_ocf"])
        if m:
            r["next_g"] = predict(m, r["g"], r["accel"])
        r["watch"] = watch(r, r["bank"])
        rows.append(r)
    order = {"up": 0, "flat": 1, "down": 2, None: 3}
    rows.sort(key=lambda r: (order.get(r["label"], 3), -(r["score"] or 0)))
    return {"rows": rows, "model": m, "track": track(scored, px), "n": len(rows)}


def plain(r: Dict, name: Optional[str] = None, m: Optional[Dict] = None) -> str:
    """One sentence for a company (name: the display name; the SEC registrant name is a fallback)."""
    lab = LABEL.get(r["label"], ("訊號不足", ""))[0]
    bits = []
    for k, (zh, _) in SIGS.items():
        v = r.get(k)
        if v is None:
            continue
        if k == "accel":
            bits.append(f"營收成長{'加速' if v > 0 else '放慢'} {abs(v):.1f} 個百分點")
        else:
            bits.append(f"{zh}{'升' if v > 0 else '降'} {abs(v):.1f} 個百分點")
    nx = ""
    if r.get("next_g") is not None:
        nx = (f"；模型估下一季營收年增約 {r['next_g']:+.0f}%" if (m or {}).get("model") else
              f"；若維持本季速度，下一季營收年增約 {r['next_g']:+.0f}%") + (f"（過去誤差約 ±{m['rmse']:.0f} 個百分點）" if m else "")
    inner = f"營收年增 {r['g']:+.0f}%" + ("，" + "、".join(bits) if bits else "，其他訊號資料不足")
    return f"{name or r['name']}：{lab}（{inner}）{nx}。"
