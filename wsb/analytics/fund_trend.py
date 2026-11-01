"""財報走向判斷：只看公司自己的財報，判斷「本業正在變好還是變差」，估下一季營收成長，並公開這套判斷過去的成績。

資料（wsb/data/fund_global.py）：
  美股  市值 ≥ 200 億美元＋觀察名單，SEC XBRL 季資料
  台股  市值前 150 大（金融保險業除外），FinMind 季報
  港股  成交額前 100 大，Yahoo 年報（多數港股半年才公布一次，免費資料只有年報，所以用「年度」版本）

① 四個訊號（季資料用近 12 個月合計，避免季節性）
     營收成長加速：最近 2 季營收年增率的平均 − 前 2 季的平均（年度版：今年年增 − 去年年增）
     毛利率變化、淨利率變化、自由現金流率變化：近 12 個月 vs 一年前（百分點）
   每個訊號和「這家公司自己過去這個訊號的平常變動」比：變動小於平常的 1/4 當作持平（死區由資料決定，不寫死門檻）。
   港股年報只有 4～5 年，自己的歷史太短，改和「同市場所有公司的平常變動」比。
   加總：+2 以上＝改善中、−2 以下＝轉弱中、其他＝持平／分歧。金融業沒有毛利率與自由現金流，只用其餘訊號。
② 下一季營收年增率估算（美股、台股各自估）：全部公司一起估一條簡單迴歸（下一季年增 ≈ a + b×本季年增 + c×加速度），
   走步樣本外測試（每次只用當時以前的資料）算誤差；若沒有比「下一季＝本季」更準，就直接用本季年增並照實標示。
③ 判斷的歷史成績（美股、台股）：過去每一季做同樣判斷，看
     兩季後淨利率真的比較高的比例（基本面有沒有說中）
     財報公布後 26 週，股價比同市場名單平均多或少多少（以季為單位重抽 1 萬次算 90% 區間）
     公布日：第 1～3 季以季末 + 45 天估，第 4 季（年報）美股 + 60 天、台股 + 90 天（法定期限）
限制：名單是現在的大型股（倖存者偏差）、股價只有約 6 年；財報數字是修正後的版本；港股樣本太短，沒有歷史成績；
這是描述與歷史統計，不是預測股價，也不是買賣建議。"""
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
    return (a / b - 1) * 100 if a and a > 0 and b and b > 0 else None   # a non-positive quarter is a filing artefact


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


def panel_y(p: Dict, bank: bool = False) -> pd.DataFrame:
    """Annual version (Hong Kong): one row per fiscal year — revenue growth, its change from last year, margin changes."""
    rev = p.get("rev") or {}
    ys = sorted(rev)
    lv: Dict[str, Dict[str, Optional[float]]] = {}
    for y in ys:
        r = rev[y]
        if not r or r <= 0:
            continue
        g_, n_, o_, c_ = ((p.get(k) or {}).get(y) for k in ("gp", "ni", "ocf", "capex"))
        lv[y] = {"gm": None if bank or g_ is None else g_ / r * 100, "nm": None if n_ is None else n_ / r * 100,
                 "fcf": None if bank or o_ is None or c_ is None else (o_ - c_) / r * 100,
                 "cx_ocf": c_ / o_ * 100 if not bank and o_ and o_ > 0 and c_ is not None else None}
    rows, gs = [], {}
    for y in ys:
        prev = f"FY{int(y[2:]) - 1}"
        if y not in lv or prev not in lv:
            continue
        gs[y] = (rev[y] / rev[prev] - 1) * 100
        r = {"q": y, "g": gs[y], "accel": gs[y] - gs[prev] if prev in gs else None, "cx_ocf": lv[y]["cx_ocf"]}
        for k in ("gm", "nm", "fcf"):
            a, b = lv[y][k], lv[prev][k]
            r[k] = a - b if a is not None and b is not None else None
            r[k + "_lv"] = a
        rows.append(r)
    return pd.DataFrame(rows).set_index("q") if rows else pd.DataFrame()


def peer_scale(panels: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """The usual size of each signal across every company in the market (robust: 1.4826 × median absolute deviation)."""
    out = {}
    for k in SIGS:
        v = pd.concat([df[k] for df in panels.values() if k in df], ignore_index=True).dropna().astype(float) if panels else pd.Series(dtype=float)
        if len(v) >= 20:
            out[k] = float(1.4826 * (v - v.median()).abs().median()) or float(v.std())
    return out


def score(df: pd.DataFrame, bank: bool = False, scale: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """Each signal → +1 / 0 / −1 against the company's own usual change (dead band from the data), then the label.
    scale: a fixed usual change per signal (peers), for histories too short to have their own."""
    df = df.copy()
    pts, zs = [], []
    for k in SIGS:
        x = df[k].astype(float) if k in df else pd.Series(np.nan, index=df.index)
        if scale is not None:
            sd = pd.Series(scale.get(k, np.nan), index=df.index, dtype=float)
        else:
            sd = x.expanding(8).std().shift(1)                   # only what was known before this quarter
        band = DEAD * sd
        s = pd.Series(np.where(x > band, 1, np.where(x < -band, -1, 0)), index=df.index, dtype=float)
        s[x.isna() | sd.isna()] = np.nan
        df["s_" + k] = s
        pts.append(s)
        zs.append((x / sd.replace(0, np.nan)).clip(-3, 3))
    m = pd.concat(pts, axis=1)
    df["n_sig"] = m.notna().sum(axis=1)
    df["score"] = m.sum(axis=1, min_count=1)
    df["z"] = pd.concat(zs, axis=1).sum(axis=1, min_count=1)        # how far from usual, for ordering only
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


def _pub(q: str, lag4: int) -> pd.Timestamp:
    """When the quarter's numbers were public: 45 days for interim quarters, the annual-report deadline for Q4."""
    return _qend(q) + pd.Timedelta(days=lag4 if q.endswith("Q4") else PUB_LAG)


def track(scored: Dict[str, pd.DataFrame], px: Dict[str, pd.Series], lag4: int = PUB_LAG) -> Dict:
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
                t0 = _pub(q, lag4)
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
    if r.get("g") is not None and abs(r["g"]) >= 100:
        return "營收年增超過 100%（基期小、併購或景氣循環高峰），各種比率的變化會被放大：看下一季營收能否維持，以及利潤率是不是跟著站穩。"
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


MARKETS = {"us": ("美股", "US", 60), "tw": ("台股", "Taiwan", 90), "hk": ("港股", "Hong Kong", None)}   # Q4 publication lag
STALE_DAYS = {"us": 300, "tw": 300, "hk": 600}
MIN_ROWS = {"us": 12, "tw": 12, "hk": 2}


def _row(sym: str, meta: Dict, df: pd.DataFrame, mk: str, m: Optional[Dict]) -> Optional[Dict]:
    ok = df.dropna(subset=["g"])
    if ok.empty:
        return None
    last, q = ok.iloc[-1], ok.index[-1]
    end = _qend(q) if "Q" in q else pd.Timestamp(year=int(q[2:]), month=12, day=31)
    if (pd.Timestamp.today() - end).days > STALE_DAYS[mk]:             # stale filer — blank rather than old
        return None
    bank = bool(meta.get("fin"))
    r = {"sym": sym, "name": meta.get("name") or sym, "ind": meta.get("ind") or "", "mk": mk, "q": q, "bank": bank,
         "g": float(last["g"]), "label": last["label"], "score": None if pd.isna(last["score"]) else int(last["score"]),
         "z": None if pd.isna(last.get("z")) else float(last["z"]), "mcap": meta.get("mcap")}
    for k in SIGS:
        v = last.get(k)
        r[k] = None if v is None or pd.isna(v) else float(v)
        sv = last.get("s_" + k)
        r["s_" + k] = None if sv is None or pd.isna(sv) else int(sv)
    r["cx_ocf"] = None if pd.isna(last.get("cx_ocf")) else float(last["cx_ocf"])
    if m:
        r["next_g"] = predict(m, r["g"], r["accel"])
    r["watch"] = watch(r, bank)
    return r


def industries(rows: List[Dict], min_n: int = 3) -> List[Dict]:
    """Share improving / weakening per industry — where the fundamentals are turning, not only which company."""
    by: Dict[str, List[Dict]] = {}
    for r in rows:
        if r["label"] and r.get("ind") and r["ind"] != "港股":
            by.setdefault(r["ind"], []).append(r)
    out = []
    for ind, rs in by.items():
        if len(rs) < min_n:
            continue
        up, dn = sum(r["label"] == "up" for r in rs), sum(r["label"] == "down" for r in rs)
        out.append({"ind": ind, "n": len(rs), "up": up / len(rs) * 100, "down": dn / len(rs) * 100, "net": (up - dn) / len(rs) * 100,
                    "g": float(np.median([r["g"] for r in rs]))})
    return sorted(out, key=lambda x: -x["net"])


def build_market(mk: str, uni: List[Dict], facts: Dict[str, Dict], closes: Optional[pd.DataFrame] = None) -> Optional[Dict]:
    annual = mk == "hk"
    panels, metas = {}, {}
    for meta in uni:
        p = facts.get(meta["sym"])
        if not p:
            continue
        bank = bool(meta.get("fin")) or (annual and not (p.get("gp") or {}))     # Yahoo has no gross profit for banks / insurers
        meta = {**meta, "fin": bank}
        df = panel_y(p, bank) if annual else panel(p, bank)
        if len(df) < MIN_ROWS[mk]:
            continue
        panels[meta["sym"]], metas[meta["sym"]] = df, meta
    if not panels:
        return None
    scale = peer_scale(panels) if annual else None
    scored = {s: score(df, metas[s]["fin"], scale) for s, df in panels.items()}
    m = None if annual else forecast_model(panels)
    rows = [r for r in (_row(s, metas[s], df, mk, m) for s, df in scored.items()) if r]
    order = {"up": 0, "flat": 1, "down": 2, None: 3}
    rows.sort(key=lambda r: (order.get(r["label"], 3), -(r["z"] or 0)))
    tr: Dict = {}
    if not annual and closes is not None and not closes.empty:
        px = {s: closes[s].dropna() for s in scored if s in closes}
        tr = track(scored, px, MARKETS[mk][2] or PUB_LAG)
    return {"rows": rows, "model": m, "track": tr, "n": len(rows), "inds": industries(rows), "annual": annual,
            "scale": scale, "uni": len(uni), "scored": scored, "metas": metas}


_MEMO: Dict = {}


def build(d: Optional[Dict] = None, px: Optional[Dict[str, pd.DataFrame]] = None) -> Optional[Dict]:
    """{"markets": {us|tw|hk: build_market(...)}}; memoised on the cache files' modification times."""
    from ..data import fund_global as G
    key = None
    if d is None and px is None:
        try:
            key = (G.FILE.stat().st_mtime if G.FILE.exists() else 0, G.PX_FILE.stat().st_mtime if G.PX_FILE.exists() else 0)
        except OSError:
            key = None
        if key and _MEMO.get("key") == key:
            return _MEMO["v"]
    d = d if d is not None else G.load()
    px = px if px is not None else G.load_px()
    uni, facts = d.get("uni") or {}, d.get("facts") or {}
    out: Dict = {"markets": {}, "skip": {m: len(v) for m, v in (d.get("skip") or {}).items()}, "tw_fin": uni.get("tw_fin"),
                 "ts": d.get("ts")}
    for mk in MARKETS:
        try:
            b = build_market(mk, uni.get(mk) or [], facts.get(mk) or {}, (px or {}).get(mk))
        except Exception:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).exception("fund trend %s failed", mk)
            b = None
        if b:
            out["markets"][mk] = b
    v = out if out["markets"] else None
    if key:
        _MEMO.update(key=key, v=v)
    return v


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
