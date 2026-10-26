"""AI 視角看進場 page, parts 3–5: the "healthy bull market" gauges Wall Street desks watch, how expensive the market is and
what that has meant for the following 10 years, and how lump-sum vs phased (12-month) investing has played out.
All computed from fetched series; history and description only — never a price to buy at or a buy signal."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def _s(eng, sym):
    try:
        return eng.market.series(sym).dropna()
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)


def _fred(eng, sid):
    try:
        return eng.fred.get(sid).dropna()
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)


def _rel3m(a: pd.Series, b: pd.Series) -> Optional[float]:
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    if len(j) < 64:
        return None
    r = j.iloc[:, 0] / j.iloc[:, 1]
    return float(r.iloc[-1] / r.iloc[-64] - 1) * 100


def bull_env(eng) -> List[Dict]:
    """[{zh, ok, txt, why}] — ok None when unknown."""
    out = []
    rot = getattr(eng, "rotation", None) or {}
    b = (rot.get("breadth") or {})
    v = b.get("us") or next(iter(b.values()), None)
    if v and v.get("now") is not None:
        out.append({"zh": "市場寬度：站上 200 日線的股票比例", "ok": v["now"] > 50, "txt": f"{v['now']:.0f}%",
                    "why": "超過一半代表多數股票都在長期上升趨勢，不是少數大型股撐盤。"})
    try:
        from wsb.analytics import vol_breadth as VB
        nh = VB.nh_nl(eng)
    except Exception:  # noqa: BLE001
        nh = None
    if nh and (nh.get("nh") or 0) + (nh.get("nl") or 0) > 0:
        out.append({"zh": "52 週新高家數減新低家數", "ok": nh["diff"] > 0, "txt": f"新高 {nh['nh']}・新低 {nh['nl']}（差 {nh['diff']:+d}）",
                    "why": "健康的多頭裡創新高的股票比創新低的多。"})
    ew = (rot.get("equal_weight") or {}).get("chg_3m")
    if ew is not None:
        out.append({"zh": "等權重標普 vs 市值加權標普（3 個月）", "ok": ew >= 0, "txt": f"{ew:+.1f}%",
                    "why": "等權重跟得上，代表一般股票也在漲；落後代表漲勢集中在少數巨頭。"})
    for a, bb, zh, why in (("XLY", "XLP", "非必需消費 vs 必需消費（3 個月相對表現）", "資金願意買景氣敏感的股票，代表對經濟有信心。"),
                           ("XLI", "XLU", "工業 vs 公用事業（3 個月相對表現）", "工業領先防禦型的公用事業，是風險胃口回來的訊號。")):
        r = _rel3m(_s(eng, a), _s(eng, bb))
        if r is not None:
            out.append({"zh": zh, "ok": r > 0, "txt": f"{r:+.1f}%", "why": why})
    rev = None
    for row in (getattr(eng, "canary", None) or {}).get("rows") or []:
        if row.get("id") == "eps_revisions":
            rev = row
    import re
    m = re.search(r"淨上修比例 ([+-]?\d+)%", (rev or {}).get("value_txt") or "")
    if m:
        net = int(m.group(1))
        out.append({"zh": "分析師獲利預估：上修家數多於下修（4 週）", "ok": net > 0, "txt": rev["value_txt"],
                    "why": "獲利預估往上修，是股價長期上漲最直接的燃料。"})
    hy = _fred(eng, "BAMLH0A0HYM2")
    if len(hy) > 70:
        ch = float(hy.iloc[-1] - hy.iloc[-64])
        out.append({"zh": "高收益債利差 3 個月內收窄", "ok": ch <= 0, "txt": f"{hy.iloc[-1]:.2f}%（3 個月 {ch:+.2f}）",
                    "why": "利差收窄代表債市願意借錢給風險較高的公司，信用環境改善。"})
    y2 = _fred(eng, "DGS2")
    if len(y2) > 70:
        ch = float(y2.iloc[-1] - y2.iloc[-64])
        out.append({"zh": "2 年期公債殖利率 3 個月內下降（市場預期降息）", "ok": ch < 0, "txt": f"{y2.iloc[-1]:.2f}%（3 個月 {ch:+.2f}）",
                    "why": "2 年期利率最貼近聯準會政策；往下代表市場預期資金會變寬鬆。"})
    return out


def valuation_10y(eng) -> Optional[Dict]:
    """Buffett indicator (Z.1 equity market value / GDP) vs the next 10 years' annualised growth of that same market value
    (price-only proxy, since 1945): bucket by the indicator's own percentile, and where today sits."""
    mv, gdp = _fred(eng, "NCBEILQ027S"), _fred(eng, "GDP")
    if len(mv) < 200 or len(gdp) < 200:
        return None
    j = pd.concat({"mv": mv, "gdp": gdp * 1000}, axis=1, join="inner").dropna()
    ratio = j["mv"] / j["gdp"] * 100
    fwd = ((j["mv"].shift(-40) / j["mv"]) ** (1 / 10) - 1) * 100
    df = pd.DataFrame({"r": ratio, "f": fwd}).dropna()
    if len(df) < 120:
        return None
    # today: the latest quarter rolled forward with the S&P 500 (same convention as the valuation page)
    now = float(ratio.iloc[-1])
    spx = _s(eng, "^GSPC")
    q_end = ratio.index[-1] + pd.offsets.QuarterEnd(0)
    base = spx[spx.index <= q_end]
    if len(base) and spx.index[-1] > q_end:
        now *= float(spx.iloc[-1] / base.iloc[-1])
    pct = float((ratio < now).mean() * 100)
    qs = np.quantile(df["r"], [0, 0.25, 0.5, 0.75, 1.0])
    rows = []
    for i, (lo, hi) in enumerate(zip(qs[:-1], qs[1:])):
        m = (df["r"] >= lo) & ((df["r"] <= hi) if i == 3 else (df["r"] < hi))
        f = df.loc[m, "f"]
        rows.append({"lo": float(lo), "hi": float(hi), "n": int(m.sum()), "med": float(f.median()), "p10": float(f.quantile(0.1)),
                     "p90": float(f.quantile(0.9)), "neg": float((f < 0).mean() * 100), "now": bool((lo <= now <= hi) or (i == 3 and now > hi))})
    corr = float(np.corrcoef(df["r"], df["f"])[0, 1])
    return {"now": now, "pct": pct, "rows": rows, "corr": corr, "since": df.index[0].strftime("%Y"), "last": df.index[-1].strftime("%Y"),
            "above_max": bool(now > float(df["r"].max()))}


def phased(eng) -> Optional[Dict]:
    """Lump sum on day one vs 12 equal monthly instalments (cash waits at 0 %), value 3 years after the start, for every month
    since the S&P 500 history starts, plus four famous bad starting points.  Price index only (no dividends)."""
    spx = _s(eng, "^GSPC")
    if len(spx) < 252 * 8:
        return None
    m = spx.resample("ME").last().dropna()
    out_rows = []
    for i in range(len(m) - 36):
        p = m.iloc[i:i + 37].values
        lump = p[36] / p[0]
        dca = float(np.mean(p[36] / p[:12]))
        out_rows.append((m.index[i], lump, dca))
    if len(out_rows) < 60:
        return None
    lump_win = float(np.mean([l > d for _, l, d in out_rows]) * 100)
    diff = float(np.median([(l - d) * 100 for _, l, d in out_rows]))
    worst_l = min(out_rows, key=lambda x: x[1])
    named = []
    for lab, d in (("2000 年網路泡沫高點", "2000-03"), ("2007 年金融海嘯前高點", "2007-10"), ("2020 年疫情崩盤前", "2020-02"), ("2022 年升息空頭前", "2022-01")):
        hit = [r for r in out_rows if r[0].strftime("%Y-%m") == d]
        if hit:
            _, l, dd = hit[0]
            named.append({"label": lab, "start": d, "lump": (l - 1) * 100, "dca": (dd - 1) * 100})
    return {"n": len(out_rows), "lump_win": lump_win, "diff_med": diff, "since": m.index[0].strftime("%Y"),
            "worst": {"start": worst_l[0].strftime("%Y-%m"), "lump": (worst_l[1] - 1) * 100, "dca": (worst_l[2] - 1) * 100}, "named": named}
