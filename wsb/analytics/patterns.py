"""Classic chart-pattern tags and top-exhaustion flags from daily closes + volume (the price cache has no intraday
high/low, so every rule here is defined on closing prices).  Descriptive labels only — not signals."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

TAGS = {"squeeze": ("布林壓縮", "BB squeeze"), "ma_gc": ("20／60 日線黃金交叉", "20/60-day golden cross"),
        "ma_dc": ("20／60 日線死亡交叉", "20/60-day death cross"), "w_form": ("W 底成形", "Double bottom forming"),
        "w_break": ("W 底突破頸線", "Double-bottom breakout"), "box": ("箱型整理", "Trading range"),
        "box_break": ("箱型突破", "Range breakout"), "box_fail": ("假突破・跌回箱內", "Failed breakout")}
TAG_DEF = {
    "squeeze": "20 日布林通道寬度落在近 120 日最窄的 10%（或接近半年最窄）：波動收斂，常出現在大波動之前（方向不一定）。",
    "ma_gc": "近 5 個交易日內 20 日線上穿 60 日線。", "ma_dc": "近 5 個交易日內 20 日線下穿 60 日線。",
    "w_form": "近 60 日出現兩個相差 3% 以內的低點（間隔 ≥ 10 日），中間反彈 ≥ 5%；現價距頸線 3% 以內、尚未突破。",
    "w_break": "W 底成立，且近 5 日內收盤站上頸線（兩低點之間的最高收盤）。",
    "box": "前 30 個交易日收盤高低差 ≤ 12%，價格仍在箱內。",
    "box_break": "近 5 日內收盤突破前 30 日箱頂 1% 以上，且突破日成交量 ≥ 1.5 倍均量。",
    "box_fail": "近 5 日內曾收在箱頂上方，但現在又跌回箱內。"}
EXH = {"rsi": ("RSI 過熱", "RSI overbought"), "stretch": ("離 50 日線過遠", "Far above the 50-day"),
       "rsi_div": ("RSI 頂背離", "RSI bearish divergence"), "vol_div": ("價漲量縮", "Rally on fading volume"),
       "dist": ("高檔爆量收黑", "Heavy-volume down day near the high")}
EXH_DEF = {
    "rsi": "14 日 RSI ≥ 75。", "stretch": "收盤高於 50 日線的幅度，落在這檔股票近兩年最高的 5%，且至少 +10%。",
    "rsi_div": "近 40 日股價創新高，但 RSI 比前一個高點（RSI 當時 ≥ 70）低 5 以上。",
    "vol_div": "近 3 日創 20 日新高，但近 5 日均量不到 50 日均量的 8 成。",
    "dist": "近 5 日在 52 週高點 5% 以內出現下跌日，且成交量 ≥ 2 倍均量（可能有大戶出貨）。"}


def _rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _pivots_low(x: np.ndarray, w: int = 5) -> List[int]:
    return [i for i in range(w, len(x) - w) if x[i] == x[i - w:i + w + 1].min()]


def tags(c: pd.Series, v: Optional[pd.Series] = None) -> List[str]:
    c = c.dropna()
    c = c[c > 0]
    out: List[str] = []
    if len(c) < 80:
        return out
    v = (v.reindex(c.index).fillna(0) if v is not None and len(v) else pd.Series(0.0, index=c.index))
    ma20, ma60 = c.rolling(20).mean(), c.rolling(60).mean()
    if len(c) >= 140:
        bw = 4 * c.rolling(20).std() / ma20
        lastw = bw.iloc[-120:]
        prior = bw.iloc[-121:-1]
        if lastw.notna().sum() > 100 and (bw.iloc[-1] <= lastw.quantile(0.10) or bw.iloc[-1] <= prior.min() * 1.1):
            out.append("squeeze")
    diff = (ma20 - ma60).iloc[-6:]
    if diff.notna().all():
        s = np.sign(diff.values)
        if s[-1] > 0 and (s[:-1] <= 0).any():
            out.append("ma_gc")
        elif s[-1] < 0 and (s[:-1] >= 0).any():
            out.append("ma_dc")
    # double bottom (W): two similar lows in the last 60 sessions with a ≥5% bounce between them
    win = c.iloc[-60:].values
    piv = _pivots_low(win[:-1], 4)
    if len(piv) >= 2:
        best = None
        for i in range(len(piv)):
            for j in range(i + 1, len(piv)):
                a, b = piv[i], piv[j]
                if b - a < 10:
                    continue
                lo1, lo2 = win[a], win[b]
                if abs(lo1 / lo2 - 1) > 0.03:
                    continue
                neck = win[a:b + 1].max()
                if neck < max(lo1, lo2) * 1.05:
                    continue
                prior_hi = c.iloc[max(0, len(c) - 60 - 40):len(c) - 60 + a + 1].max()
                if prior_hi < min(lo1, lo2) * 1.10:          # needs a real decline before the first low
                    continue
                if best is None or b > best[1]:
                    best = (a, b, neck)
        if best:
            a, b, neck = best
            after = win[b + 1:]
            px = win[-1]
            crossed = [k for k in range(len(after)) if after[k] > neck]
            if crossed and len(after) - crossed[0] <= 5 and px > neck:
                out.append("w_break")
            elif not crossed and neck * 0.97 <= px <= neck:
                out.append("w_form")
    # trading range / breakout / failed breakout
    box = c.iloc[-35:-5]
    hi, lo = box.max(), box.min()
    if lo > 0 and hi / lo - 1 <= 0.12:
        last5 = c.iloc[-5:]
        vavg = v.rolling(50, min_periods=20).mean()
        above = last5 > hi * 1.01                              # a real close above the box, not noise
        if above.any():
            first = int(np.argmax(above.values))
            vi = v.iloc[-5 + first]
            va = vavg.iloc[-5 + first]
            if c.iloc[-1] > hi and va and va > 0 and vi >= 1.5 * va:
                out.append("box_break")
            elif c.iloc[-1] <= hi * 1.005:
                out.append("box_fail")
        elif last5.min() >= lo * 0.99:
            out.append("box")
    return out


def exhaustion(c: pd.Series, v: Optional[pd.Series] = None) -> Dict:
    c = c.dropna()
    c = c[c > 0]
    if len(c) < 120:
        return {"flags": [], "n": 0, "detail": {}}
    v = (v.reindex(c.index).fillna(0) if v is not None and len(v) else pd.Series(0.0, index=c.index))
    r = _rsi(c)
    flags, det = [], {}
    if pd.notna(r.iloc[-1]) and r.iloc[-1] >= 75:
        flags.append("rsi")
        det["rsi"] = round(float(r.iloc[-1]))
    ma50 = c.rolling(50).mean()
    st = (c / ma50 - 1).dropna()
    if len(st) > 200:
        cur, p95 = float(st.iloc[-1]), float(st.iloc[-504:].quantile(0.95))
        if cur >= max(0.10, p95):
            flags.append("stretch")
            det["stretch"] = round(cur * 100, 1)
    w = c.iloc[-40:]
    if w.iloc[-3:].max() >= w.max() * 0.999:
        i_now = int(np.argmax(w.values[-3:])) + len(w) - 3
        prev = w.iloc[:max(0, i_now - 9)]
        if len(prev) >= 5:
            i_prev = int(np.argmax(prev.values))
            rw = r.iloc[-40:]
            rp, rn = rw.iloc[i_prev], rw.iloc[i_now]
            if pd.notna(rp) and pd.notna(rn) and rp >= 70 and rn <= rp - 5 and w.iloc[i_now] > prev.iloc[i_prev]:
                flags.append("rsi_div")
                det["rsi_div"] = (round(float(rp)), round(float(rn)))
    v50 = v.rolling(50, min_periods=30).mean()
    if v.iloc[-60:].sum() > 0 and pd.notna(v50.iloc[-1]) and v50.iloc[-1] > 0:
        if c.iloc[-3:].max() >= c.iloc[-20:].max() * 0.999 and v.iloc[-5:].mean() < 0.8 * v50.iloc[-1]:
            flags.append("vol_div")
            det["vol_div"] = round(float(v.iloc[-5:].mean() / v50.iloc[-1]), 2)
        h52 = c.iloc[-252:].max()
        for k in range(-5, 0):
            if c.iloc[k] < c.iloc[k - 1] and c.iloc[k] >= h52 * 0.95 and pd.notna(v50.iloc[k]) and v50.iloc[k] > 0 and v.iloc[k] >= 2 * v50.iloc[k]:
                flags.append("dist")
                det["dist"] = round(float(v.iloc[k] / v50.iloc[k]), 1)
                break
    return {"flags": flags, "n": len(flags), "detail": det}


def exh_text(e: Dict) -> str:
    d = e.get("detail") or {}
    parts = []
    for f in e.get("flags", []):
        lab = EXH[f][0]
        if f == "rsi":
            lab += f" {d['rsi']}"
        elif f == "stretch":
            lab += f" +{d['stretch']}%"
        elif f == "rsi_div":
            lab += f"（{d['rsi_div'][0]}→{d['rsi_div'][1]}）"
        elif f == "vol_div":
            lab += f"（量 {d['vol_div']} 倍）"
        elif f == "dist":
            lab += f"（{d['dist']} 倍量）"
        parts.append(lab)
    return "、".join(parts)
