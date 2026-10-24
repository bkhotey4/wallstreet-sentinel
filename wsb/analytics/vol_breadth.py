"""兩個「人類常看錯」的指標，各自附回測：

  * VIX 期限結構：VIX9D（9 天）、VIX（30 天）、VIX3M（3 個月）。平常近月比遠月便宜（正價差），恐慌時近月飆過遠月（逆價差／倒掛）。
    回測（2007 年起）：VIX/VIX3M > 1 之後，標普 1 個月與 3 個月的報酬、3 個月內跌 ≥10% 的頻率，和平常比——倒掛常出現在恐慌的高點附近，
    不一定是「還會再跌」的訊號，照實寫。
  * 52 週新高 − 新低家數（NH−NL）：本站追蹤池的美股大型股，每天有幾檔收盤創 52 週新高、幾檔創新低。指數創新高但 NH−NL 為負＝
    只剩少數股票在撐（頂背離）；指數破底但 NH−NL 快速收斂＝賣壓變少（底部訊號）。追蹤池只有約 250 檔、歷史約兩年，所以只描述現況。"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd


def _fwd(px: pd.Series, h: int) -> pd.Series:
    return px.shift(-h) / px - 1


def _low(px: pd.Series, h: int) -> pd.Series:
    return px[::-1].rolling(h, min_periods=1).min()[::-1].shift(-1) / px - 1


def vix_term(eng) -> Optional[Dict]:
    try:
        v, v9, v3 = (eng.market.series(t).dropna() for t in ("^VIX", "^VIX9D", "^VIX3M"))
        spx = eng.market.series("^GSPC").dropna()
    except Exception:  # noqa: BLE001
        return None
    if len(v) < 500 or len(v3) < 500:
        return None
    j = pd.concat({"v": v, "v3": v3, "v9": v9}, axis=1).dropna(subset=["v", "v3"])
    r = j["v"] / j["v3"]
    r9 = (j["v9"] / j["v"]).dropna()
    now = float(r.iloc[-1])
    out = {"date": j.index[-1].strftime("%Y-%m-%d"), "vix": float(j["v"].iloc[-1]), "vix3m": float(j["v3"].iloc[-1]),
           "vix9d": float(j["v9"].iloc[-1]) if j["v9"].notna().iloc[-1] else None, "ratio": now, "ratio9": float(r9.iloc[-1]) if len(r9) else None,
           "pct": float((r.iloc[:-1] < now).mean() * 100), "since": j.index[0].strftime("%Y"),
           "days_inverted": int((r.tail(20) > 1).sum()), "hist": [[i.strftime("%Y-%m-%d"), float(x)] for i, x in r.tail(260).items()]}
    out["state"] = ("逆價差（倒掛）：近月恐慌比遠月高" if now > 1 else "接近倒掛" if now > 0.95 else "正價差：市場平靜")
    out["emoji"] = "🔴" if now > 1 else "🟡" if now > 0.95 else "🟢"
    if len(spx) > 1000:
        sp = spx.reindex(r.index).ffill()
        f21, f63, l63 = _fwd(sp, 21) * 100, _fwd(sp, 63) * 100, _low(sp, 63)
        cut = r.index[-1] - pd.Timedelta(days=95)
        f63[f63.index > cut] = np.nan
        f21[f21.index > r.index[-1] - pd.Timedelta(days=35)] = np.nan
        y = (l63 <= -0.10).astype(float).where(l63.notna())
        y[y.index > cut] = np.nan

        def grp(m):
            return {"n": int(f63[m].notna().sum()), "r21": float(f21[m].median()) if f21[m].notna().any() else None,
                    "r63": float(f63[m].median()) if f63[m].notna().any() else None, "up63": float((f63[m] > 0).mean() * 100) if f63[m].notna().any() else None,
                    "crash": float(y[m].mean() * 100) if y[m].notna().any() else None}
        out["bt"] = {"inv": grp(r > 1), "all": grp(r == r), "calm": grp(r < 0.9)}
    return out


def _universe_close(eng):
    """Whole US market (~2,500 stocks, built by the site job) when it is there; else the site's tracking pool."""
    try:
        from ..data import fullmarket as FM
        fm, _v = FM.load_prices("us")
        if not fm.empty and fm.shape[1] >= 300 and len(fm) >= 265:
            return fm.astype(float), "美股全市場"
    except Exception:  # noqa: BLE001
        pass
    sp = getattr(eng, "stockprices", None)
    close = getattr(sp, "close", None) if sp is not None else None
    if close is None or close.empty:
        return None, None
    try:
        from ..data.stocks import universe
        us = list(((universe().get("us") or {}).get("symbols") or {}).keys())
    except Exception:  # noqa: BLE001
        us = []
    cols = [c for c in close.columns if c in us] or [c for c in close.columns if "." not in str(c)]
    return close[cols].astype(float), "本站追蹤池"


def nh_nl(eng) -> Optional[Dict]:
    c, src = _universe_close(eng)
    if c is None or len(c) < 265 or c.shape[1] < 50:
        return None
    cols = list(c.columns)
    hi = c.rolling(252, min_periods=240).max()
    lo = c.rolling(252, min_periods=240).min()
    nh = (c >= hi).sum(axis=1)
    nl = (c <= lo).sum(axis=1)
    valid = hi.notna().sum(axis=1) >= 50
    diff = (nh - nl)[valid]
    if len(diff) < 10:
        return None
    nh, nl = nh[valid], nl[valid]
    try:
        spx = eng.market.series("^GSPC").dropna()
    except Exception:  # noqa: BLE001
        spx = pd.Series(dtype=float)
    out = {"src": src, "date": diff.index[-1].strftime("%Y-%m-%d"), "nh": int(nh.iloc[-1]), "nl": int(nl.iloc[-1]), "diff": int(diff.iloc[-1]),
           "avg10": float(diff.tail(10).mean()), "n": int(valid.iloc[-1] and hi.notna().iloc[-1].sum()),
           "hist": [[i.strftime("%Y-%m-%d"), int(x)] for i, x in diff.tail(120).items()]}
    sig = "沒有背離"
    if len(spx) > 260:
        s = spx[spx.index <= diff.index[-1]]
        near_hi = s.iloc[-1] >= s.tail(252).max() * 0.98
        near_lo = s.iloc[-1] <= s.tail(252).min() * 1.05
        d10, d10_prev = diff.tail(10).mean(), diff.iloc[-20:-10].mean() if len(diff) >= 20 else None
        out.update(spx_off=float(s.iloc[-1] / s.tail(252).max() - 1) * 100)
        if near_hi and out["avg10"] < 0:
            sig = "頂背離：指數在高點附近，但創新低的股票比創新高的多"
        elif near_lo and d10_prev is not None and d10 > d10_prev and out["avg10"] > d10_prev:
            sig = "底部訊號：指數在低點附近，但新低家數正在快速收斂"
        elif out["avg10"] < -0.05 * len(cols):
            sig = "賣壓擴散：最近 10 天平均創新低的股票明顯多於新高"
    out["signal"] = sig
    out["emoji"] = "🔴" if sig.startswith(("頂背離", "賣壓")) else "🟢" if sig.startswith("底部") else "⚪"
    return out
