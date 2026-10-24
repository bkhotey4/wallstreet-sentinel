"""AI 的結論，每天都算：人類的恐懼（恐懼與貪婪、VIX 近一年百分位、壓力指數 SSI 的平均）對 AI 測到的結構風險
（physics.score_series：亂流、產業同步度、餘震階段）。差距 ≥ 20 分才換判讀，回到 15 分以內才換回來（遲滯），
避免每天在門檻附近來回跳。網站每次產生都重算今天的值，並回填過去一年的走勢與判讀變化；Discord 在判讀改變時推播。"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd

ENTER, LEAVE = 20.0, 15.0
HUMAN, MACHINE, SAME = "人類比數據緊張", "數據比人類緊張", "人類和數據差不多"


def label(gap: Optional[float], prev: Optional[str] = None) -> Optional[str]:
    """gap = fear − AI.  Enter a side at |gap| ≥ 20, leave it only when |gap| < 15."""
    if gap is None or gap != gap:
        return None
    if prev == HUMAN and gap >= LEAVE:
        return HUMAN
    if prev == MACHINE and -gap >= LEAVE:
        return MACHINE
    if gap >= ENTER:
        return HUMAN
    if -gap >= ENTER:
        return MACHINE
    return SAME


def _fg_series(eng) -> pd.Series:
    try:
        from . import bottom as BT
        return BT._ser(BT.load(), "fg").dropna()
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)


def fear_now(eng) -> Tuple[Optional[float], List[str]]:
    parts, vals = [], []
    fg = None
    try:
        cr = getattr(getattr(eng, "crypto", None), "data", None) or {}
        fg = cr.get("cnn_fng")
    except Exception:  # noqa: BLE001
        fg = None
    if fg is None:
        s = _fg_series(eng)
        fg = float(s.iloc[-1]) if len(s) else None
    if fg is not None:
        vals.append(100 - float(fg))
        parts.append(f"恐懼與貪婪 {fg:.0f}" + ("（極度恐懼）" if fg < 25 else "（恐懼）" if fg < 45 else ""))
    try:
        v = eng.market.series("^VIX").dropna()
        if len(v) > 252:
            p = float((v.iloc[-253:-1] < v.iloc[-1]).mean() * 100)
            vals.append(p)
            parts.append(f"VIX {v.iloc[-1]:.1f}（近一年第 {p:.0f} 百分位）")
    except Exception:  # noqa: BLE001
        pass
    ssi = getattr(getattr(eng, "stress", None), "score", None)
    if ssi is not None:
        vals.append(float(ssi))
        parts.append(f"壓力指數 SSI {ssi:.0f}")
    return (sum(vals) / len(vals) if vals else None), parts


def history(eng, ph: Dict, days: int = 260) -> Optional[pd.DataFrame]:
    """Daily fear, AI score, gap and label for the last `days` trading days (each input only from data known that day)."""
    from . import physics as PH
    ai = PH.score_series(ph) if ph.get("available") else pd.Series(dtype=float)
    if len(ai) < 30:
        return None
    cols = {}
    fg = _fg_series(eng)
    if len(fg):
        cols["fg"] = 100 - fg
    try:
        v = eng.market.series("^VIX").dropna()
        if len(v) > 300:
            cols["vix"] = v.rolling(253).apply(lambda x: (x[:-1] < x[-1]).mean() * 100, raw=True)
    except Exception:  # noqa: BLE001
        pass
    st = getattr(getattr(eng, "stress", None), "history", None)
    if st is not None and len(st):
        cols["ssi"] = st
    if not cols:
        return None
    f = pd.DataFrame(cols)
    f.index = pd.to_datetime(f.index).normalize()
    a = ai.copy()
    a.index = pd.to_datetime(a.index).normalize()
    df = pd.concat({"ai": a}, axis=1).join(f, how="left").ffill(limit=5).tail(days)
    df["fear"] = df[[c for c in ("fg", "vix", "ssi") if c in df]].mean(axis=1)
    df = df.dropna(subset=["ai", "fear"])
    if df.empty:
        return None
    df["gap"] = df["fear"] - df["ai"]
    labs, prev = [], None
    for g in df["gap"]:
        prev = label(g, prev)
        labs.append(prev)
    df["label"] = labs
    return df[["fear", "ai", "gap", "label"]]


def changes(df: Optional[pd.DataFrame], n: int = 8) -> List[Dict]:
    """The label changes in the history, newest first: {date, from, to, fear, ai}."""
    if df is None or df.empty:
        return []
    out, prev = [], None
    for d, r in df.iterrows():
        if r["label"] != prev and prev is not None:
            out.append({"date": d.strftime("%Y-%m-%d"), "from": prev, "to": r["label"], "fear": float(r["fear"]), "ai": float(r["ai"])})
        prev = r["label"]
    return out[::-1][:n]


def today(eng, ph: Dict) -> Dict:
    """Today's verdict with the live inputs, continuing yesterday's label (hysteresis) from the history."""
    df = history(eng, ph)
    fear, parts = fear_now(eng)
    sc = (ph.get("score") or {}) if ph else {}
    ai = float(sc["now"]) if sc.get("available") else (float(df["ai"].iloc[-1]) if df is not None else None)
    prev = None
    if df is not None and len(df) >= 2:
        prev = df["label"].iloc[-2]
    lab = label(None if fear is None or ai is None else fear - ai, prev)
    since = None
    if df is not None and lab:
        run = df[df["label"] != lab]
        since = (run.index[-1] + pd.Timedelta(days=1)).strftime("%Y-%m-%d") if len(run) else df.index[0].strftime("%Y-%m-%d")
    return {"fear": fear, "fparts": parts, "ai": ai, "label": lab, "since": since, "history": df, "changes": changes(df)}
