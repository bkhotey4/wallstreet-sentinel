"""Shock radar: where is the NEXT financial shock most likely to ignite, and how much should we trust the model?

Three data-driven pieces (no hard-coded 'magic' outcomes):
  1. block radar   – each risk block's level, its 20-day acceleration (percentile vs its own history) and its
                     historical predictive power (AUC against subsequent S&P drawdowns)
  2. transmission  – candidate shock paths (e.g. 私募信貸→信用) ranked by level + acceleration
  3. credibility   – walk-forward (out-of-sample) AUC / Brier skill of the crash-odds model, plus a post-mortem of
                     every past ≥10% drawdown: did the Stress Index warn before the peak?
It also reports the stock-vs-credit DIVERGENCE (credit/rates/liquidity stress running ahead of equity-implied fear),
which is the classic late-cycle signature, together with its own historical hit rate."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS
from .crash_odds import forward_min_return

CFG = SETTINGS.get("shock", {})
CREDIT_LIKE = CFG.get("credit_blocks", ["信用", "私募信貸", "利率", "流動性", "全球新興"])
EQUITY_LIKE = CFG.get("equity_blocks", ["波動率", "股市結構"])
DEFAULT_PATHS = [
    {"name": "信用事件", "blocks": ["私募信貸", "信用"],
     "story": "私募信貸/BDC 贖回與壞帳 → 區域銀行與高收益債利差擴大 → 融資收緊 → 股市被迫去槓桿"},
    {"name": "利率／債市衝擊", "blocks": ["利率", "流動性"],
     "story": "殖利率與實質利率快速上升、債市波動放大 → 長天期資產重新定價 → 成長股估值與信用同步受壓"},
    {"name": "套息拆倉", "blocks": ["匯率套息", "全球新興"],
     "story": "日圓急升或美元流動性緊縮 → 套息交易平倉 → 新興市場與高 β 資產被拋售（類似 2024/8）"},
    {"name": "波動率／槓桿去化", "blocks": ["波動率", "股市結構"],
     "story": "VIX 期限結構倒掛、造市商負 Gamma、市場廣度惡化 → 指數層級的機械式賣壓"},
    {"name": "景氣衰退", "blocks": ["景氣就業", "信用"],
     "story": "就業惡化（失業金、Sahm 指標）搭配信用利差走闊 → 盈餘預期下修 → 股市轉空頭"},
    {"name": "商品／地緣能源", "blocks": ["商品加密", "全球新興"],
     "story": "能源或商品價格劇烈變動 → 通膨預期與央行路徑重寫 → 風險資產重新定價"},
]


# ---------------------------------------------------------------- statistics helpers
def auc(score: pd.Series, y: pd.Series) -> Optional[float]:
    """Mann-Whitney AUC: P(score of a positive > score of a negative).  0.5 = no skill."""
    d = pd.concat([score.rename("s"), y.rename("y")], axis=1).dropna()
    n1, n0 = int(d["y"].sum()), int((1 - d["y"]).sum())
    if n1 < 5 or n0 < 5:
        return None
    r = d["s"].rank(method="average")
    return float((r[d["y"] == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _verdict(a: Optional[float]) -> str:
    if a is None:
        return "樣本不足"
    return "有鑑別力" if a >= 0.65 else ("鑑別力偏弱" if a >= 0.55 else "接近隨機")


# ---------------------------------------------------------------- 1) block radar
def block_radar(st, close: Optional[pd.Series] = None, horizon: int = 63, dd: float = 0.10) -> List[Dict]:
    bh: pd.DataFrame = st.block_history
    lead: Dict[str, Optional[float]] = {}
    if close is not None and len(close) > 300:
        hit = (forward_min_return(close.dropna(), horizon) <= -dd).astype(float).where(
            forward_min_return(close.dropna(), horizon).notna())
        for b in bh.columns:
            lead[b] = auc(bh[b].reindex(hit.index), hit)
    rows = []
    for b, level in st.blocks.items():
        s = bh[b].dropna() if b in bh.columns else pd.Series(dtype=float)
        chg = float(level - s.iloc[-21]) if len(s) > 21 else None
        d20 = s.diff(20).dropna()
        pct = float((d20 < chg).mean() * 100) if chg is not None and len(d20) > 100 else None
        if level >= 70 and (pct or 0) >= 70:
            state = "點火中"
        elif level >= 60 or (pct or 0) >= 90:
            state = "升溫"
        else:
            state = "平靜"
        rows.append({"block": b, "level": float(level), "chg20": chg, "accel_pctile": pct, "state": state,
                     "auc": lead.get(b), "auc_verdict": _verdict(lead.get(b))})
    return sorted(rows, key=lambda r: -(r["level"] + 0.25 * ((r["accel_pctile"] or 50) - 50)))


# ---------------------------------------------------------------- 2) transmission paths
def shock_paths(radar: List[Dict]) -> List[Dict]:
    by = {r["block"]: r for r in radar}
    paths = CFG.get("paths") or DEFAULT_PATHS
    out = []
    for p in paths:
        rs = [by[b] for b in p["blocks"] if b in by]
        if not rs:
            continue
        level = float(np.mean([r["level"] for r in rs]))
        accel = float(np.mean([r["accel_pctile"] if r["accel_pctile"] is not None else 50.0 for r in rs]))
        ign = level + 0.25 * (accel - 50)                       # level, nudged by how fast it is rising
        out.append({"name": p["name"], "blocks": p["blocks"], "story": p.get("story", ""), "level": level,
                    "accel_pctile": accel, "ignition": ign,
                    "state": "高度警戒" if ign >= 70 else ("留意" if ign >= 58 else "低")})
    return sorted(out, key=lambda x: -x["ignition"])


# ---------------------------------------------------------------- 3) credit-vs-equity divergence
def divergence(st, close: Optional[pd.Series] = None, thr: Optional[float] = None) -> Dict:
    thr = float(thr if thr is not None else CFG.get("divergence_threshold", 15))
    cur = st.blocks
    c = [cur[b] for b in CREDIT_LIKE if b in cur]
    e = [cur[b] for b in EQUITY_LIKE if b in cur]
    if not c or not e:
        return {"available": False}
    gap = float(np.mean(c) - np.mean(e))
    out = {"available": True, "credit": float(np.mean(c)), "equity": float(np.mean(e)), "gap": gap,
           "threshold": thr, "flag": gap >= thr}
    bh = st.block_history
    cc = [b for b in CREDIT_LIKE if b in bh.columns]
    ee = [b for b in EQUITY_LIKE if b in bh.columns]
    if close is not None and cc and ee and len(close) > 300:
        gh = (bh[cc].mean(axis=1) - bh[ee].mean(axis=1)).dropna()
        fmr = forward_min_return(close.dropna(), 63)
        j = pd.concat([gh.rename("g"), fmr.rename("f")], axis=1).dropna()
        if len(j) > 300:
            hit = j["f"] <= -0.10
            on = j["g"] >= thr
            out["hist"] = {"days_flagged": int(on.sum()), "base_rate": float(hit.mean() * 100),
                           "prob_when_flagged": float(hit[on].mean() * 100) if on.sum() >= 20 else None,
                           "auc": auc(j["g"], hit.astype(float))}
    return out


# ---------------------------------------------------------------- 4) credibility: walk-forward + post-mortems
def walk_forward(ssi: pd.Series, close: pd.Series, days: int, dd: float,
                 edges: Optional[List[float]] = None, min_train: int = 504) -> Dict:
    """Yearly expanding-window out-of-sample test of the bucketed crash-odds model (with an `days` embargo)."""
    edges = edges or SETTINGS.get("crash_odds", {}).get("buckets", [0, 35, 55, 70, 85, 101])
    close = close.dropna()
    df = pd.DataFrame({"ssi": ssi}).join(close.rename("px"), how="inner").dropna()
    fmr = forward_min_return(df["px"], days)
    valid = fmr.notna()
    hit = ((fmr <= -dd) & valid).astype(float)
    bucket = pd.Series(np.digitize(df["ssi"].values, edges) - 1, index=df.index).clip(0, len(edges) - 2)
    P, Y, B = [], [], []
    for yr in sorted(set(df.index.year)):
        test = (df.index.year == yr) & valid.values
        first = int(df.index.searchsorted(pd.Timestamp(year=yr, month=1, day=1)))
        cutoff = df.index[max(first - days, 0)]                 # embargo = `days` trading rows, not business days
        train = (df.index < cutoff) & valid.values
        if train.sum() < min_train or test.sum() < 20:
            continue
        base = hit[train].mean()
        probs = {}
        for b in range(len(edges) - 1):
            m = train & (bucket.values == b)
            n = int(m.sum())
            probs[b] = (hit[m].sum() + base * 30) / (n + 30)     # shrink thin buckets toward the base rate
        P.append(bucket[test].map(probs).values)
        Y.append(hit[test].values)
        B.append(np.full(int(test.sum()), base))
    if not P:
        return {"days": days, "drawdown_pct": dd * 100, "n_test": 0}
    p, y, b0 = np.concatenate(P), np.concatenate(Y), np.concatenate(B)
    bs, bs0 = float(np.mean((p - y) ** 2)), float(np.mean((b0 - y) ** 2))
    a = auc(pd.Series(p), pd.Series(y))
    return {"days": days, "drawdown_pct": dd * 100, "n_test": int(len(y)), "events": int(y.sum()),
            "auc_oos": a, "verdict": _verdict(a), "brier": bs, "brier_base": bs0,
            "skill": float(1 - bs / bs0) if bs0 > 0 else None}


def drawdown_episodes(close: pd.Series, ssi: pd.Series, min_dd: float = 0.10, warn: float = 55.0,
                      pre_days: int = 60) -> List[Dict]:
    """Every peak-to-trough fall ≥ min_dd: what did the Stress Index say before the peak?"""
    c = close.dropna()
    ssi = ssi.dropna()
    runmax = c.cummax()
    dd = c / runmax - 1
    eps, i, n = [], 0, len(c)
    idx = c.index
    while i < n:
        if dd.iloc[i] <= -min_dd:
            peak_val = runmax.iloc[i]
            pk = int(np.argmax(c.values[:i + 1] == peak_val))               # first index where that peak was hit
            j = i
            while j + 1 < n and c.iloc[j + 1] < peak_val:                   # until a new high
                j += 1
            seg = c.iloc[pk:j + 1]
            tr = seg.idxmin()
            peak_d = idx[pk]
            pre = ssi[(ssi.index >= peak_d - pd.tseries.offsets.BDay(pre_days)) & (ssi.index <= tr)]
            if len(ssi[ssi.index <= peak_d]) >= 20:                          # only judge periods the model covers
                above = pre[pre >= warn]
                first = above.index[0] if len(above) else None
                lead = None if first is None else int(np.busday_count(first.date(), peak_d.date()))
                at_peak = ssi[ssi.index <= peak_d]
                eps.append({"peak": peak_d.strftime("%Y-%m-%d"), "trough": tr.strftime("%Y-%m-%d"),
                            "depth_pct": float((c[tr] / peak_val - 1) * 100),
                            "ssi_at_peak": float(at_peak.iloc[-1]),
                            "ssi_max_pre": float(pre[pre.index <= peak_d].max()) if len(pre[pre.index <= peak_d]) else None,
                            "ssi_at_trough": float(ssi[ssi.index <= tr].iloc[-1]),
                            "first_warn": None if first is None else first.strftime("%Y-%m-%d"),
                            "lead_days": lead,
                            "warned_before_peak": lead is not None and lead >= 0})
            i = j + 1
        else:
            i += 1
    return eps


def model_quality(ssi: pd.Series, close: pd.Series) -> Dict:
    hz = SETTINGS.get("crash_odds", {}).get("horizons", [])
    wf = [walk_forward(ssi, close, int(h["days"]), float(h["drawdown"])) for h in hz]
    for w, h in zip(wf, hz):                                                  # in-sample AUC for reference
        df = pd.DataFrame({"ssi": ssi}).join(close.dropna().rename("px"), how="inner").dropna()
        fm = forward_min_return(df["px"], int(h["days"]))
        w["auc_in"] = auc(df["ssi"], ((fm <= -float(h["drawdown"])).astype(float)).where(fm.notna()))
    eps = drawdown_episodes(close, ssi)
    warned = [e for e in eps if e["warned_before_peak"]]
    early_or_during = [e for e in eps if e["first_warn"] is not None]
    return {"walk_forward": wf, "episodes": eps,
            "episode_summary": {"n": len(eps), "warned_before_peak": len(warned),
                                "warned_any": len(early_or_during),
                                "median_lead_days": float(np.median([e["lead_days"] for e in warned])) if warned else None}}


# ---------------------------------------------------------------- facade
def build(st, close: Optional[pd.Series], quality: Optional[Dict] = None) -> Dict:
    radar = block_radar(st, close)
    return {"radar": radar, "paths": shock_paths(radar), "divergence": divergence(st, close),
            "quality": quality}
