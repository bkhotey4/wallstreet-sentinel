"""崩盤還是錯殺？大跌時用資料逐項檢查：是本業真的轉壞，還是被市場一起拖下去。

對美股、台股的財報走向名單（wsb/data/fund_global.py），檢查四個面向：
  ① 終端需求：營收年增與成長加速（財報走向的訊號）——需求真的變弱，營收成長會先放慢
  ② 跌價主因：同期間 10 年債殖利率變化（和自己平常的 20 天變動比），以及它比同產業多跌多少
     利率急升時大家一起跌，多半是「估值被壓」；只有它自己跌特別多，多半有公司自己的消息
  ③ 企業利潤：近 12 個月自由現金流率、淨利率是正還是負（現金牛還是在燒錢）
  ④ 市場結構：名單裡「跌得比自己平常多」的公司比例，和過去 6 年比——很高＝全面下跌，不高＝分化
「跌得比自己平常多」＝近 4 週報酬低於自己過去 2 年 4 週報酬標準差的 −1.5 倍（每家公司自己的門檻）。

每家跌深的公司分三類（只描述，不是買賣建議）：
  本業沒變差：財報走向不是轉弱、營收成長沒有放慢、自由現金流（金融業看淨利）是正的
  本業也在轉弱：財報走向是轉弱，或營收放慢且現金流或淨利是負的
  訊號不一：其他
歷史成績：過去 6 年每次跌深（同一段下跌只算第一週），用「當時已公布」的財報分類，看之後 13 週與 26 週
比同市場名單平均多或少多少，以週為單位重抽 1 萬次算 90% 區間。限制：名單是現在的大型股（倖存者偏差）。"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .fund_trend import MARKETS, PUB_LAG, _pub

WIN = 4                  # weeks in the drop window (≈ 20 trading days)
BIG = 1.5                # a drop beyond 1.5 × the stock's own usual 4-week move counts as "deep"
SD_WEEKS = 104
HOR = (13, 26)
N_SIM = 10_000
SEED = 20261101
CLS = {"ok": ("本業沒變差", "Business intact"), "weak": ("本業也在轉弱", "Business weakening too"), "check": ("訊號不一", "Mixed")}


def classify(f: Dict) -> str:
    lab, sa = f.get("label"), f.get("s_accel")
    cash = f.get("fcf_lv") if f.get("fcf_lv") is not None and not pd.isna(f.get("fcf_lv")) else f.get("nm_lv")
    cash = None if cash is None or pd.isna(cash) else float(cash)
    if lab == "down" or (sa == -1 and cash is not None and cash < 0):
        return "weak"
    if lab in ("up", "flat") and sa != -1 and cash is not None and cash > 0:
        return "ok"
    return "check"


def feats(df: pd.DataFrame, lag4: int) -> pd.DataFrame:
    """The scored quarters re-indexed by the date each became public."""
    cols = [c for c in ("label", "s_accel", "fcf_lv", "nm_lv", "g", "accel") if c in df]
    f = df[cols].copy()
    f.index = [_pub(q, lag4) for q in df.index]
    return f.sort_index()


def deep(closes: pd.DataFrame, win: int = WIN, sd_n: int = SD_WEEKS) -> tuple:
    r = closes / closes.shift(win) - 1
    sd = r.rolling(sd_n, min_periods=sd_n // 2).std().shift(1)
    return r, sd, r < -BIG * sd


def history(closes: pd.DataFrame, fs: Dict[str, pd.DataFrame]) -> Dict:
    """Every first week of a deep drop: class known then, then the 13/26-week return vs the list's average."""
    r, sd, big = deep(closes)
    first = big & ~big.shift(1, fill_value=False).rolling(WIN, min_periods=1).max().astype(bool)
    rows = []
    idx = closes.index
    for sym in closes.columns:
        f = fs.get(sym)
        if f is None or f.empty:
            continue
        for t in idx[first[sym].values]:
            i = idx.get_loc(t)
            prev = f[f.index <= t]
            if prev.empty:
                continue
            c = classify(prev.iloc[-1].to_dict())
            rec = {"sym": sym, "t": t, "cls": c}
            for h in HOR:
                if i + h < len(idx):
                    fw = closes.iloc[i + h] / closes.iloc[i] - 1
                    if pd.notna(fw.get(sym)):
                        rec[h] = float((fw[sym] - fw.drop(sym).mean()) * 100)
            rows.append(rec)
    t = pd.DataFrame(rows)
    out: Dict = {"n": int(len(t))}
    if t.empty:
        return out
    rng = np.random.default_rng(SEED)
    for c in CLS:
        s = t[t["cls"] == c]
        rec: Dict = {"n": int(len(s))}
        for h in HOR:
            e = s.dropna(subset=[h]) if h in s else pd.DataFrame()
            if len(e) >= 20 and e["t"].nunique() >= 10:
                g = [x[h].values for _, x in e.groupby("t")]
                sums, sizes = np.array([x.sum() for x in g]), np.array([len(x) for x in g])
                pick = rng.integers(0, len(g), size=(N_SIM, len(g)))
                means = sums[pick].sum(axis=1) / sizes[pick].sum(axis=1)
                rec[h] = {"ex": float(e[h].mean()), "lo": float(np.percentile(means, 5)), "hi": float(np.percentile(means, 95)),
                          "beat": float((e[h] > 0).mean() * 100), "n": int(len(e))}
        out[c] = rec
    out["from"], out["to"] = str(t["t"].min().date()), str(t["t"].max().date())
    return out


def structure(big: pd.DataFrame, r: pd.DataFrame) -> Optional[Dict]:
    """④ Share of the list in a deep drop now, against every week of the past."""
    ok = r.notna().sum(axis=1) >= max(20, int(r.shape[1] * 0.5))
    share = (big.sum(axis=1) / r.notna().sum(axis=1) * 100)[ok]
    if len(share) < 60:
        return None
    now = float(share.iloc[-1])
    return {"share": now, "pct": float((share.iloc[:-1] < now).mean() * 100), "p90": float(share.quantile(0.9)),
            "med_r": float(r.iloc[-1].median() * 100), "asof": str(share.index[-1].date())}


def rates(tnx: Optional[pd.Series]) -> Optional[Dict]:
    """② The 10-year yield over the same window, against its own 3-year spread of 20-day moves."""
    if tnx is None:
        return None
    y = tnx.dropna()
    if len(y) < 300:
        return None
    c20 = (y - y.shift(20)) * 100
    sd = float(c20.iloc[-756:-1].std())
    return {"chg": float(c20.iloc[-1]), "sd": sd, "z": float(c20.iloc[-1] / sd) if sd else None, "y": float(y.iloc[-1])} if sd else None


def current(closes: pd.DataFrame, fs: Dict[str, pd.DataFrame], metas: Dict[str, Dict]) -> List[Dict]:
    r, sd, big = deep(closes)
    return current_from(closes, r, sd, big, fs, metas)


def current_from(closes, r, sd, big, fs: Dict[str, pd.DataFrame], metas: Dict[str, Dict]) -> List[Dict]:
    last = closes.index[-1]
    inds: Dict[str, List[float]] = {}
    for s in closes.columns:
        v = r[s].iloc[-1]
        if pd.notna(v):
            inds.setdefault((metas.get(s) or {}).get("ind") or "", []).append(float(v))
    med = {k: float(np.median(v)) for k, v in inds.items() if len(v) >= 3}
    out = []
    for s in closes.columns:
        if not bool(big[s].iloc[-1]):
            continue
        f = fs.get(s)
        prev = f[f.index <= last] if f is not None else pd.DataFrame()
        x = {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in (prev.iloc[-1].to_dict() if not prev.empty else {}).items()}
        m = metas.get(s) or {}
        ind = m.get("ind") or ""
        rv, sdv = float(r[s].iloc[-1]), float(sd[s].iloc[-1])
        rel = rv - med[ind] if ind in med else None
        out.append({"sym": s, "name": m.get("name") or s, "ind": ind, "r": rv * 100, "sd": sdv * 100, "ind_r": med[ind] * 100 if ind in med else None,
                    "rel": rel * 100 if rel is not None else None, "own": rel is not None and rel < -BIG * sdv,
                    "cls": classify(x) if x else "check", "label": x.get("label"), "g": x.get("g"), "accel": x.get("accel"),
                    "s_accel": x.get("s_accel"), "fcf_lv": x.get("fcf_lv"), "nm_lv": x.get("nm_lv"), "mcap": m.get("mcap")})
    return sorted(out, key=lambda z: z["r"])


_HIST: Dict = {}


def _history_cached(mk: str, cl: pd.DataFrame, fs: Dict[str, pd.DataFrame]) -> Dict:
    """The 5-year history only changes when the weekly closes or the filings do."""
    key = (mk, cl.shape, str(cl.index[-1]), float(np.nansum(cl.iloc[-1].values)), len(fs))
    if _HIST.get(mk, (None,))[0] != key:
        _HIST[mk] = (key, history(cl, fs))
    return _HIST[mk][1]


def build_market(mk: str, fb: Dict, closes: Optional[pd.DataFrame]) -> Optional[Dict]:
    if closes is None or closes.empty or not fb or fb.get("annual"):
        return None
    lag4 = MARKETS[mk][2] or PUB_LAG
    fs = {s: feats(df, lag4) for s, df in (fb.get("scored") or {}).items()}
    cl = closes.loc[:, [c for c in closes.columns if c in fs]].astype(float)
    if cl.shape[1] < 20 or len(cl) < SD_WEEKS:
        return None
    r, _sd, big = deep(cl)
    now_cl, daily = cl, False
    try:                                   # the full-market scan's daily closes are fresher than the weekly file
        from ..data import fullmarket as FM
        d, _v = FM.load_prices(mk)
        d = d.loc[:, [c for c in d.columns if c in fs]].astype(float) if not d.empty else d
        if d.shape[1] >= 20 and len(d) >= 200 and d.index[-1] > cl.index[-1]:
            now_cl, daily = d, True
    except Exception:  # noqa: BLE001
        pass
    if daily:
        rd, sdd, bigd = deep(now_cl, 20, 250)
        rows = current_from(now_cl, rd, sdd, bigd, fs, fb.get("metas") or {})
    else:
        rows = current(cl, fs, fb.get("metas") or {})
    return {"rows": rows, "struct": structure(big, r), "hist": _history_cached(mk, cl, fs), "daily": daily,
            "asof": str(now_cl.index[-1].date()), "n": int(cl.shape[1])}


def build(eng=None) -> Optional[Dict]:
    from ..data import fund_global as G
    from . import fund_trend as F
    fb = F.build() or {}
    px = G.load_px()
    out: Dict = {"markets": {}}
    for mk in ("us", "tw"):
        b = build_market(mk, (fb.get("markets") or {}).get(mk), px.get(mk))
        if b:
            out["markets"][mk] = b
    tnx = None
    try:
        tnx = eng.market.series("^TNX") if eng is not None else None
    except Exception:  # noqa: BLE001
        tnx = None
    out["rates"] = rates(tnx)
    return out if out["markets"] else None
