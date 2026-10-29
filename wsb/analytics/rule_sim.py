"""規則的歷史成績單 — 1 萬次模擬：技術型態出現後，照固定的出場規則做，過去的結果長什麼樣子。

每個型態第一次成立的那天收盤當作起點（signals.detect，同一套規則），比較四種固定的出場規則：
  hold20   抱滿 20 個交易日
  stop     跌破訊號失效線（收盤）就出場，否則 20 日
  stop_tp  跌破失效線出場、或漲到「2 倍風險」（起點 + 2 ×（起點 − 失效線））出場，否則 20 日
  trail    收盤跌破 20 日線（或失效線）出場，最長 60 日
每筆報酬扣來回交易成本（signal_ledger 的 cost_bp）。對照組：同一天在同一份名單「隨機挑一檔、抱 20 日」。

1 萬次模擬（固定亂數種子，可重現）：
  * 平均報酬的 90% 區間：以「月份」為單位重複抽樣（同一個月的訊號常一起漲跌，逐筆抽樣會把區間算得太窄）。
  * 連續照規則做 20 次：每次先隨機抽一個月份、再抽該月一筆，20 筆依序複利，看最後結果的中位數、最差 5%、
    虧損的機率，以及過程中最大的回落。
限制：只有快取的約兩年價格（樣本內）、名單是現在的成分股（倖存者偏差，下市的股票不在裡面）、以收盤價成交、
沒有算滑價與跳空。這是規則的歷史統計，不是預測，也不是買賣建議。"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

N_SIM = 10_000
SEQ = 20
H = 20
H_TRAIL = 60
TP_R = 2.0
MIN_N, MIN_MONTHS = 30, 6
SEED = 20261030
RULES = {"hold20": ("抱滿 20 天", "Hold 20 days"),
         "stop": ("停損：跌破失效線就出場（否則 20 天）", "Stop at the invalidation line (else 20 days)"),
         "stop_tp": ("停損＋停利：跌破失效線、或漲到 2 倍風險就出場（否則 20 天）", "Stop + take profit at 2× risk (else 20 days)"),
         "trail": ("跟著趨勢：收盤跌破 20 日線才出場（最長 60 天）", "Trail: exit below the 20-day average (max 60 days)")}


def _exit(c: np.ndarray, ma20: np.ndarray, i: int, inv: float, rule: str) -> Optional[int]:
    n = len(c)
    last = i + (H_TRAIL if rule == "trail" else H)
    if last >= n:
        return None
    if rule == "hold20":
        return last
    tgt = c[i] + TP_R * (c[i] - inv) if rule == "stop_tp" and c[i] > inv else None
    for j in range(i + 1, last + 1):
        if np.isfinite(inv) and c[j] < inv:
            return j
        if tgt is not None and c[j] >= tgt:
            return j
        if rule == "trail" and np.isfinite(ma20[j]) and c[j] < ma20[j]:
            return j
    return last


def events(series: Dict[str, Dict[str, pd.DataFrame]], cost: float) -> Dict[str, pd.DataFrame]:
    """Per pattern: one row per first signal day with the net return (%) and days held under each rule, plus the
    random-pick 20-day return of the same market on that day."""
    closes = pd.DataFrame({s: next(iter(p.values()))["close"] for s, p in series.items()}).sort_index()
    bench = ((closes.shift(-H) / closes - 1) * 100).mean(axis=1)
    out: Dict[str, List[Dict]] = {}
    for sym, pats in series.items():
        for k, df in pats.items():
            first = df["flag"] & ~df["flag"].shift(1, fill_value=False)
            idx = np.flatnonzero(first.values)
            if not len(idx):
                continue
            c, m20, inv = df["close"].values.astype(float), df["ma20"].values.astype(float), df["inv"].values.astype(float)
            for i in idx:
                rec = {"date": df.index[i], "sym": sym}
                ok = True
                for r in RULES:
                    j = _exit(c, m20, i, inv[i], r)
                    if j is None:
                        ok = False
                        break
                    rec[r] = (c[j] / c[i] - 1) * 100 - cost * 100
                    rec[r + "_d"] = j - i
                if ok:
                    rec["base"] = float(bench.get(df.index[i], np.nan)) - cost * 100
                    out.setdefault(k, []).append(rec)
    return {k: pd.DataFrame(v) for k, v in out.items()}


def _sim(ev: pd.DataFrame, rng: np.random.Generator) -> Dict:
    months = ev["date"].dt.to_period("M")
    groups = [np.flatnonzero((months == m).values) for m in months.unique()]
    nm = len(groups)
    pick = rng.integers(0, nm, size=(N_SIM, nm))                     # block bootstrap by month for the average
    seq_m = rng.integers(0, nm, size=(N_SIM, SEQ))                   # 20 trades in a row: a random month, then a trade in it
    seq_u = rng.random((N_SIM, SEQ))
    sizes = np.array([len(g) for g in groups])
    rows = np.empty((N_SIM, SEQ), dtype=int)
    for a in range(nm):
        mask = seq_m == a
        rows[mask] = groups[a][(seq_u[mask] * sizes[a]).astype(int)]
    out = {}
    for r in list(RULES) + ["base"]:
        x = ev[r].values.astype(float)
        if np.isnan(x).all():
            continue
        x = np.nan_to_num(x, nan=float(np.nanmean(x)))
        s = np.array([x[g].sum() for g in groups])
        means = s[pick].sum(axis=1) / sizes[pick].sum(axis=1)
        if r == "base":                              # a market average, not one stock: only the average is comparable
            out[r] = {"avg": float(x.mean()), "lo": float(np.percentile(means, 5)), "hi": float(np.percentile(means, 95))}
            continue
        path = np.cumprod(1 + x[rows] / 100, axis=1)
        final = (path[:, -1] - 1) * 100
        peak = np.maximum.accumulate(np.concatenate([np.ones((N_SIM, 1)), path], axis=1), axis=1)[:, 1:]
        mdd = ((path / peak - 1) * 100).min(axis=1)
        out[r] = {"avg": float(x.mean()), "med": float(np.median(x)), "win": float((x > 0).mean() * 100),
                  "worst5": float(np.percentile(x, 5)), "days": float(ev[r + "_d"].mean()) if r + "_d" in ev else float(H),
                  "lo": float(np.percentile(means, 5)), "hi": float(np.percentile(means, 95)),
                  "seq_med": float(np.median(final)), "seq_p5": float(np.percentile(final, 5)), "seq_p95": float(np.percentile(final, 95)),
                  "seq_loss": float((final < 0).mean() * 100), "seq_mdd": float(np.median(mdd))}
    return out


def simulate(series: Dict[str, Dict[str, pd.DataFrame]], cost: float) -> Dict:
    evs = events(series, cost)
    rng = np.random.default_rng(SEED)
    res: Dict[str, Dict] = {}
    allp = [v for v in evs.values() if len(v)]
    if allp:
        evs["_all"] = pd.concat(allp, ignore_index=True)
    for k, ev in evs.items():
        months = ev["date"].dt.to_period("M").nunique() if len(ev) else 0
        rec = {"n": int(len(ev)), "months": int(months), "from": ev["date"].min().strftime("%Y-%m") if len(ev) else None,
               "to": ev["date"].max().strftime("%Y-%m") if len(ev) else None}
        if len(ev) >= MIN_N and months >= MIN_MONTHS:
            rec["rules"] = _sim(ev, rng)
            rec["best"] = max(RULES, key=lambda r: rec["rules"][r]["lo"]) if all(r in rec["rules"] for r in RULES) else None
        res[k] = rec
    return {"n_sim": N_SIM, "seq": SEQ, "tp_r": TP_R, "patterns": res}


def plain(k_label: str, rec: Dict) -> Optional[str]:
    """One plain sentence per pattern: what happened historically under the stop rule vs holding, and the 20-in-a-row odds."""
    rr = rec.get("rules")
    if not rr:
        return None
    h, s, b = rr.get("hold20"), rr.get("stop"), rr.get("base")
    if not h or not s:
        return None
    vs = ""
    if b:
        vs = f"；同一天隨機挑一檔抱 20 天平均 {b['avg']:+.1f}%"
    return (f"{k_label}：過去 {rec['n']} 次。抱滿 20 天平均每次 {h['avg']:+.1f}%，最差的 5% 會虧 {abs(min(h['worst5'], 0)):.0f}% 以上；"
            f"跌破失效線就出場，平均 {s['avg']:+.1f}%，最差 5% 縮小到虧 {abs(min(s['worst5'], 0)):.0f}%{vs}。"
            f"照「失效線停損」連續做 20 次，1 萬次模擬裡有 {s['seq_loss']:.0f}% 的機率最後是虧的，中間通常會先回落約 {abs(s['seq_mdd']):.0f}%。")
