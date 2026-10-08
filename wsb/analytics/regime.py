"""Macro regime classifier (growth × inflation impulse) + risk-appetite and
liquidity regime, all from live market-implied signals."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def _z_last(s: pd.Series, window: int = 756, lag: int = 0) -> Optional[float]:
    """z-score of the observation `lag` rows before the last, against the `window` rows ending there."""
    s = s.dropna()
    if lag:
        s = s.iloc[:-lag]
    if len(s) < 120:
        return None
    t = s.iloc[-window:]
    sd = t.std()
    return float((t.iloc[-1] - t.mean()) / sd) if sd else None


def _avg(vals: List[Optional[float]]) -> Optional[float]:
    v = [x for x in vals if x is not None and np.isfinite(x)]
    return float(np.mean(v)) if v else None


QUADRANTS = {
    (True, False): ("金髮女孩 Goldilocks", "成長↑ 通膨↓：股票(成長/科技)、信用債有利"),
    (True, True): ("再通膨 Reflation", "成長↑ 通膨↑：商品、價值/週期股、抗通膨資產"),
    (False, True): ("停滯性通膨 Stagflation", "成長↓ 通膨↑：現金、黃金、能源；股債雙殺風險"),
    (False, False): ("通縮衰退 Deflationary Bust", "成長↓ 通膨↓：長天期公債、防禦股、美元"),
}


def classify(market, fred) -> Dict:
    px = market.series
    def rel(a, b, n):
        sa, sb = px(a), px(b)
        if sa.empty or sb.empty:
            return pd.Series(dtype=float)
        j = pd.concat([sa, sb], axis=1).dropna()
        return j.iloc[:, 0].pct_change(n) - j.iloc[:, 1].pct_change(n)

    def parts(lag: int = 0):
        z = lambda x: _z_last(x, lag=lag)                                   # noqa: E731
        vix = z(px("^VIX"))
        return ({"銅/金 3M": z(rel("HG=F", "GC=F", 63)),
                 "非必需/必需 3M": z(rel("XLY", "XLP", 63)),
                 "小型/大型 3M": z(rel("IWM", "SPY", 63)),
                 "10Y殖利率 3M變化": z(px("^TNX").diff(63))},
                {"10Y通膨預期 3M變化": z(fred.get("T10YIE").diff(63)) if not fred.get("T10YIE").empty else None,
                 "布蘭特 3M": z(px("BZ=F").pct_change(63)),
                 "商品指數 3M": z(px("DBC").pct_change(63))},
                {"澳幣/日圓 1M": z(px("AUDJPY=X").pct_change(21)),
                 "高收益/公債 1M": z(rel("HYG", "IEF", 21)),
                 "動能/低波 1M": z(rel("MTUM", "USMV", 21)),
                 "VIX (反向)": -vix if vix is not None else None})

    growth_parts, infl_parts, risk_parts = parts()
    g, i, r = _avg(list(growth_parts.values())), _avg(list(infl_parts.values())), _avg(list(risk_parts.values()))
    out: Dict = {"growth_z": g, "inflation_z": i, "risk_appetite_z": r,
                 "growth_parts": growth_parts, "inflation_parts": infl_parts, "risk_parts": risk_parts}
    if g is not None and i is not None:
        name, play = QUADRANTS[(g >= 0, i >= 0)]
        out.update(quadrant=name, playbook=play,
                   conviction=min(abs(g), abs(i)))
        # one month ago (21 rows): where is the macro mix DRIFTING?  a quadrant change is an early regime shift
        gp, ip, _ = parts(21)
        g1, i1 = _avg(list(gp.values())), _avg(list(ip.values()))
        if g1 is not None and i1 is not None:
            out.update(growth_z_1m=g1, inflation_z_1m=i1, quadrant_1m=QUADRANTS[(g1 >= 0, i1 >= 0)][0],
                       growth_drift=g - g1, inflation_drift=i - i1,
                       drift=f"成長{'轉強' if g > g1 else '轉弱'}（{g - g1:+.2f}）、通膨{'升溫' if i > i1 else '降溫'}（{i - i1:+.2f}）",
                       quadrant_changed=QUADRANTS[(g1 >= 0, i1 >= 0)][0] != name)
    if r is not None:
        out["risk_mode"] = "Risk-ON 追價" if r > 0.5 else "Risk-OFF 避險" if r < -0.5 else "中性/分歧"

    nl = fred.net_liquidity()
    if not nl.empty and len(nl) > 20:
        last = nl.iloc[-1]
        prev = nl[nl.index <= nl.index[-1] - pd.Timedelta(days=91)]
        out["net_liquidity_bn"] = float(last)
        if len(prev):
            out["net_liquidity_chg_13w_bn"] = float(last - prev.iloc[-1])
            out["liquidity_mode"] = "擴張 (順風)" if last > prev.iloc[-1] else "收縮 (逆風)"
    return out
