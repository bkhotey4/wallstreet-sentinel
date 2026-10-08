"""Valuation & bubble watch — the slow variables value investors and short sellers look at.

* Buffett indicator  : US corporate equity market value / nominal GDP (Fed Z.1 + BEA, quarterly)
* Tobin's Q          : equity market value / net worth at market value (Z.1)
  Both are quarterly and published ~10 weeks late, so the latest value is rolled forward with the S&P 500's move
  since the quarter end (clearly labelled as an estimate).
* Credit cycle       : card / mortgage / CRE delinquency, bank lending standards, household debt service, Baa spread
* Speculation heat   : high-beta vs low-vol, innovation growth vs S&P, VIX complacency

Every number is computed from fetched series; when a series is missing the indicator is reported as unavailable
(never filled with a neutral value). Percentiles are against each series' own history.
These say how stretched things are — they are NOT timing signals."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS


def _cfg() -> Dict:
    return SETTINGS.get("valuation", {}) or {}


def pctile(hist: pd.Series, value: float) -> Optional[float]:
    h = hist.dropna()
    if len(h) < 20 or value is None or not np.isfinite(value):
        return None
    return float((h < value).mean() * 100)


def _q_ratio(fred, num: str, den: str, den_scale: float) -> pd.Series:
    a, b = fred.get(num).dropna(), fred.get(den).dropna()
    if a.empty or b.empty:
        return pd.Series(dtype=float)
    j = pd.concat([a, b * den_scale], axis=1, join="inner").dropna()
    j = j[j.iloc[:, 1] != 0]
    return (j.iloc[:, 0] / j.iloc[:, 1] * 100).dropna()


def _roll_forward(ratio: pd.Series, spx: pd.Series) -> Dict:
    """Latest quarterly ratio scaled by the S&P 500 change since that quarter's end."""
    if ratio.empty:
        return {}
    q_date, q_val = ratio.index[-1], float(ratio.iloc[-1])
    s = spx.dropna()
    est, since = None, None
    if len(s):
        # Z.1 dates are quarter starts (e.g. 2026-04-01 = Q2) → the level refers to the quarter END
        q_end = q_date + pd.offsets.QuarterEnd(0)
        base = s[s.index <= q_end]
        if len(base) and s.index[-1] > q_end:
            since = float(s.iloc[-1] / base.iloc[-1] - 1)
            est = q_val * (1 + since)
    return {"quarter": q_date.strftime("%Y-%m-%d"), "reported": q_val, "estimate": est,
            "spx_since_pct": None if since is None else since * 100}


def _grade(p: Optional[float], high_is_hot: bool = True) -> str:
    if p is None:
        return "資料缺"
    hot, ext = float(_cfg().get("hot_pct", 85)), float(_cfg().get("extreme_pct", 95))
    if not high_is_hot:                 # two-tailed gauges (credit spread, VIX): low = complacent, high = panic
        if p >= ext:
            return "恐慌"
        if p >= hot:
            return "緊張"
        if p <= 100 - ext:
            return "極度自滿"
        if p <= 100 - hot:
            return "自滿"
        return "正常"
    q = p
    if q >= ext:
        return "極端"
    if q >= hot:
        return "偏熱"
    if q <= 100 - hot:
        return "偏冷"
    return "正常"


def _rel(market, a: str, b: str, days: int) -> pd.Series:
    x, y = market.series(a), market.series(b)
    j = pd.concat([x, y], axis=1, join="inner").dropna()
    if len(j) <= days:
        return pd.Series(dtype=float)
    r = j.iloc[:, 0] / j.iloc[:, 1]
    return (r / r.shift(days) - 1).dropna() * 100


def _item(key, zh, en, value, hist, unit, high_is_hot, what_zh, asof=None, extra=None) -> Dict:
    p = pctile(hist, value) if value is not None else None
    return {"key": key, "label": zh, "label_en": en, "value": value, "unit": unit, "pctile": p,
            "grade": _grade(p, high_is_hot), "high_is_hot": high_is_hot, "what": what_zh, "asof": asof,
            "hist_start": hist.dropna().index[0].strftime("%Y") if len(hist.dropna()) else None, **(extra or {})}


def build(engine) -> Dict:
    fred, m = engine.fred, engine.market
    spx = m.series("^GSPC")
    value: List[Dict] = []
    credit: List[Dict] = []
    heat: List[Dict] = []

    # ---- Buffett indicator & Tobin's Q (quarterly, rolled forward)
    bi = _q_ratio(fred, "NCBEILQ027S", "GDP", 1000.0)               # millions / (billions*1000) → %
    if len(bi):
        rf = _roll_forward(bi, spx)
        v = rf.get("estimate") if rf.get("estimate") is not None else rf["reported"]
        value.append(_item("buffett", "巴菲特指標（股市總市值／GDP）", "Buffett indicator (equity value / GDP)", v, bi, "%", True,
                           "越高代表股市相對經濟規模越貴；歷史高點出現在 2000 與 2021 年前後。", rf["quarter"], rf))
    tq = _q_ratio(fred, "NCBEILQ027S", "TNWMVBSNNCB", 1.0)
    if len(tq):
        rf = _roll_forward(tq / 100.0, spx)
        v = rf.get("estimate") if rf.get("estimate") is not None else rf["reported"]
        value.append(_item("tobin_q", "托賓 Q（市值／重置成本）", "Tobin's Q", v, tq / 100.0, "×", True,
                           "大於 1 代表市場給企業資產的價格高於重建成本；越高越貴。", rf["quarter"], rf))

    # ---- credit cycle (rising delinquencies / tighter lending = stress building underneath)
    for sid, zh, en, hot, what in (
            ("DRCCLACBS", "信用卡逾期率", "Credit card delinquency", True, "消費者開始繳不出卡費，通常領先消費放緩。"),
            ("DRSFRMACBS", "住宅房貸逾期率", "Mortgage delinquency", True, "2006–2008 次貸危機前就是這項先惡化。"),
            ("DRCRELEXFACBS", "商用不動產貸款逾期率", "CRE loan delinquency", True, "辦公大樓等商用不動產壓力，區域銀行的主要風險。"),
            ("DRTSCILM", "銀行收緊企業放款的淨比例", "Banks tightening C&I standards", True, "銀行縮手借錢給企業，往往領先景氣下行。"),
            ("TDSP", "家庭償債支出占所得", "Household debt service ratio", True, "家庭負擔越重，對升息與失業越敏感。"),
            ("BAA10Y", "Baa 公司債利差", "Baa − 10Y spread", False, "利差異常『低』代表市場對信用風險過度自滿；急升代表恐慌。")):
        s = fred.get(sid).dropna()
        if s.empty:
            continue
        x = fred.latest(sid) or {}
        chg = x.get("chg_1y")
        credit.append(_item(sid, zh, en, float(s.iloc[-1]), s, "%", hot, what, s.index[-1].strftime("%Y-%m-%d"),
                            {"chg_1y": chg}))

    # ---- speculation heat (market-priced, daily)
    for key, a, b, days, zh, en, what in (
            ("hibeta", "SPHB", "SPLV", 120, "高 β 股 vs 低波動股（半年）", "High beta vs low vol (6m)", "投機性資金追逐高波動股時偏高。"),
            ("arkk", "ARKK", "^GSPC", 120, "創新成長股 vs 標普（半年）", "ARKK vs S&P 500 (6m)", "題材股相對大盤大漲，代表風險胃口高漲。")):
        r = _rel(m, a, b, days)
        if len(r):
            heat.append(_item(key, zh, en, float(r.iloc[-1]), r, "%", True, what, r.index[-1].strftime("%Y-%m-%d")))
    vix = m.series("^VIX").dropna()
    if len(vix):
        v20 = vix.rolling(20).mean().dropna()
        heat.append(_item("vix_calm", "VIX 20 日均值（自滿度）", "VIX 20d avg (complacency)", float(v20.iloc[-1]), v20, "",
                          False, "VIX 長期處於歷史低檔代表市場過度安心；放空派常把它當反向指標。", v20.index[-1].strftime("%Y-%m-%d")))

    groups = [{"key": "value", "title": "巴菲特看的：估值", "title_en": "Buffett-style: valuation", "items": value},
              {"key": "credit", "title": "放空派看的：信用週期", "title_en": "Short-seller lens: credit cycle", "items": credit},
              {"key": "heat", "title": "放空派看的：投機熱度", "title_en": "Short-seller lens: speculation", "items": heat}]
    n = sum(len(g["items"]) for g in groups)
    hot = [i for g in groups for i in g["items"] if i["grade"] in ("偏熱", "極端", "恐慌", "緊張", "自滿", "極度自滿")]
    return {"available": n > 0, "groups": groups, "n": n, "hot": [i["label"] for i in hot]}


def summary_lines(val: Dict) -> List[str]:
    if not val or not val.get("available"):
        return []
    L = []
    for g in val["groups"]:
        for i in g["items"]:
            pv = "NA" if i["pctile"] is None else f"{i['pctile']:.0f}"
            v = "NA" if i["value"] is None else f"{i['value']:.2f}{i['unit']}"
            L.append(f"{i['label']} {v}（歷史百分位 {pv}，自 {i['hist_start']}；{i['grade']}）")
    return L
