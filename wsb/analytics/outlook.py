"""全方位風險展望 — one integrated risk assessment across macro, crisis, credit, banking, valuation, earnings,
sectors and news, with forecasts by horizon.

Every dimension is a 0–100 risk score (higher = more dangerous) with the evidence that produced it.  Forecasts only
come from models with a track record:
  • 1 / 3 / 6 months — empirical drawdown odds conditioned on the Stress Index (crash_odds, walk-forward checked)
  • 12 months recession — the New York Fed yield-curve probit (Estrella & Trubin): P = Φ(−0.5333 − 0.6330 × spread),
    spread = 10-year minus 3-month Treasury yield in percentage points (monthly average)
The composite is a transparent weighted average, not a fitted model; the page says so."""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

CFG = SETTINGS.get("outlook", {}) or {}
NYFED_A, NYFED_B = -0.5333, -0.6330
LEVELS = [(70, "高", "High"), (55, "偏高", "Elevated"), (40, "中性", "Moderate"), (0, "低", "Low")]
WEIGHTS = {"recession": 0.16, "crisis": 0.18, "credit": 0.15, "banking": 0.12, "valuation": 0.1,
           "earnings": 0.09, "sectors": 0.08, "macro": 0.07, "news": 0.05}


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _clip(x: float) -> float:
    return float(max(0.0, min(100.0, x)))


def level(score: Optional[float]):
    if score is None:
        return "資料缺", "N/A"
    for th, zh, en in LEVELS:
        if score >= th:
            return zh, en
    return LEVELS[-1][1], LEVELS[-1][2]


def _dim(key: str, zh: str, en: str, score: Optional[float], evidence: List[str], forecast: Optional[Dict] = None,
         prev: Optional[float] = None, note: str = "") -> Dict:
    lz, le = level(score)
    return {"key": key, "zh": zh, "en": en, "score": None if score is None else round(float(score), 1),
            "label": lz, "label_en": le, "evidence": evidence, "forecast": forecast,
            "prev": None if prev is None else round(float(prev), 1), "note": note}


# ---------------------------------------------------------------- 1) recession (12 months)
def nyfed_probability(spread_pct: float) -> float:
    """NY Fed model: probability (%) of a US recession 12 months ahead from the 10y–3m spread (percentage points)."""
    return 100.0 * _phi(NYFED_A + NYFED_B * spread_pct)


def recession(fred) -> Dict:
    ev: List[str] = []
    sp = fred.get("T10Y3M").dropna()
    prob = prob_1m = None
    uninvert = False
    if len(sp) >= 30:
        prob = nyfed_probability(float(sp.iloc[-21:].mean()))
        prob_1m = nyfed_probability(float(sp.iloc[-42:-21].mean()))
        ev.append(f"10年-3個月利差（近一月均值）{sp.iloc[-21:].mean():+.2f}%，紐約聯準會模型 12 個月衰退機率 {prob:.0f}%")
        last2y = sp[sp.index >= sp.index[-1] - pd.Timedelta(days=730)]
        if (last2y < 0).any() and sp.iloc[-1] > 0:
            uninvert = True
            ev.append("過去兩年曾倒掛、現已轉正：歷史上衰退常在『倒掛後轉正』階段開始")
    sahm = fred.get("SAHMREALTIME").dropna()
    s_sahm = None
    if len(sahm):
        v = float(sahm.iloc[-1])
        s_sahm = _clip(v / 0.5 * 70)                  # 0.5 = Sahm trigger → 70; 0.3 → 42
        ev.append(f"Sahm 衰退指標 {v:.2f}（≥0.50 觸發；目前{'已觸發' if v >= 0.5 else '接近觸發' if v >= 0.3 else '未觸發'}）")
    ic = fred.get("ICSA").dropna()
    s_claims = None
    if len(ic) >= 60:
        ma4 = ic.rolling(4).mean().dropna()
        low52 = ma4.iloc[-52:].min()
        rise = (ma4.iloc[-1] / low52 - 1) * 100 if low52 else 0.0
        s_claims = _clip(rise / 20 * 70)             # +20% above the 52-week low has preceded past recessions
        ev.append(f"初領失業金 4 週均 {ma4.iloc[-1] / 1000:.0f}K，比一年低點 {rise:+.0f}%（≥+20% 為歷史警訊）")
    parts = [(0.5, prob), (0.3, s_sahm), (0.2, s_claims)]
    parts = [(w, v) for w, v in parts if v is not None]
    score = sum(w * v for w, v in parts) / sum(w for w, _ in parts) if parts else None
    if score is not None and uninvert:
        score = _clip(score + 15)                    # re-steepening after an inversion: the classic recession-onset window
    fc = {"horizon_zh": "12 個月", "horizon_en": "12 months", "prob": prob, "prev": prob_1m,
          "what_zh": "美國陷入衰退", "what_en": "US recession",
          "model_zh": "紐約聯準會殖利率曲線 probit 模型", "model_en": "NY Fed yield-curve probit"} if prob is not None else None
    return _dim("recession", "總經衰退", "Recession", score, ev, fc)


# ---------------------------------------------------------------- 2) crisis / crash (1–6 months)
def crisis(st, odds: Dict) -> Dict:
    if st is None:
        return _dim("crisis", "金融海嘯／崩跌", "Crisis & crash", None, ["壓力指數尚未計算"])
    ev = [f"系統性壓力指數 SSI {st.score:.0f}/100（{st.label}），歷史百分位 {st.pctile_all or 0:.0f}%，20 日 {st.chg_20d or 0:+.1f}"]
    fcs = []
    for h in (odds or {}).get("horizons", []):
        p = h.get("adjusted") if h.get("adjusted") is not None else h.get("conditional")
        if p is None:
            continue
        fcs.append({"days": h["days"], "dd": h["drawdown_pct"], "prob": float(p), "base": float(h["base_rate"]),
                    "lift": h.get("lift_adj") or h.get("lift")})
    if fcs:                                           # one summary line; the full table is in the forecast block
        f1 = min(fcs, key=lambda f: f["days"])
        ev.append(f"{f1['days']} 個交易日內跌≥{f1['dd']:.0f}% 機率 {f1['prob']:.1f}%，是平常的 {f1['prob'] / f1['base']:.1f} 倍"
                  if f1["base"] else f"{f1['days']} 個交易日內跌≥{f1['dd']:.0f}%：{f1['prob']:.1f}%")
    lifts = [f["lift"] for f in fcs if f.get("lift")]
    lift_pts = _clip(50 + (np.mean(lifts) - 1) * 40) if lifts else st.score
    score = 0.6 * st.score + 0.4 * lift_pts
    prev = float(st.history.iloc[-22]) if st.history is not None and len(st.history) > 22 else None
    return _dim("crisis", "金融海嘯／崩跌", "Crisis & crash", score, ev, {"crash": fcs} if fcs else None,
                prev=None if prev is None else 0.6 * prev + 0.4 * lift_pts)


# ---------------------------------------------------------------- 3) credit cycle
def credit(fred) -> Dict:
    ev, parts = [], []
    hy = fred.latest("BAMLH0A0HYM2")
    phase = None
    if hy:
        lvl, chg = hy.get("pctile_3y"), (hy.get("chg_3m") or 0.0) * 100
        ev.append(f"高收益債利差 {hy['value']:.2f}%（3 年百分位 {lvl or 0:.0f}%，3 個月 {chg:+.0f}bp）")
        if lvl is not None:
            parts.append(lvl)
        parts.append(_clip(50 + chg / 150 * 50))       # +150bp in 3 months → 100
        rising = chg > 25
        if lvl is not None:
            phase = ("收縮（利差高且擴大）" if lvl >= 60 and rising else "修復（利差高但收斂）" if lvl >= 60 else
                     "轉折（利差從低檔擴大）" if rising else "過熱（利差極低，風險被低估）" if lvl <= 10 else "擴張（利差低且穩定）")
            ev.append(f"信用循環階段：{phase}")
    ccc = fred.latest("BAMLH0A3HYC")
    if ccc and ccc.get("pctile_3y") is not None:
        ev.append(f"CCC 級利差 {ccc['value']:.2f}%（3 年百分位 {ccc['pctile_3y']:.0f}%）——最弱的借款人最先出事")
        parts.append(ccc["pctile_3y"])
    baa = fred.latest("BAA10Y")
    if baa and baa.get("pctile_3y") is not None:
        ev.append(f"Baa 公司債對公債利差 {baa['value']:.2f}%")
    score = float(np.mean(parts)) if parts else None
    if phase and phase.startswith("過熱") and score is not None:
        score = max(score, 45.0)                     # very tight spreads = complacency, not safety
    return _dim("credit", "信用循環／違約", "Credit cycle", score, ev, note=phase or "")


# ---------------------------------------------------------------- 4) banking & funding
def banking(st, fred) -> Dict:
    if st is None:
        return _dim("banking", "銀行與資金", "Banks & funding", None, ["壓力指數尚未計算"])
    ev, parts = [], []
    for b in ("流動性", "私募信貸"):
        if b in st.blocks:
            parts.append(st.blocks[b])
            ev.append(f"{b}壓力 {st.blocks[b]:.0f}/100")
    kre = next((c for c in st.components if c.id == "kre" and c.score is not None), None)
    if kre:
        parts.append(kre.score)
        ev.append(f"區域銀行相對大盤 {kre.score:.0f}/100（越高越弱）")
    res = fred.get("WRESBAL").dropna()
    if len(res) > 14:
        chg = (res.iloc[-1] / res.iloc[-14] - 1) * 100
        ev.append(f"銀行準備金 13 週 {chg:+.1f}%" + ("（快速流失，資金面趨緊）" if chg < -5 else ""))
        if chg < -5:
            parts.append(70.0)
    nf = fred.latest("NFCI")
    if nf:
        ev.append(f"芝加哥金融狀況指數 NFCI {nf['value']:+.2f}（>0 代表比平常緊）")
    return _dim("banking", "銀行與資金市場", "Banks & funding", float(np.mean(parts)) if parts else None, ev)


# ---------------------------------------------------------------- 5) valuation / bubble
def valuation(val: Dict) -> Dict:
    if not (val or {}).get("available"):
        return _dim("valuation", "估值泡沫", "Valuation", None, ["估值資料暫缺"])
    items = [it for g in val["groups"] if g["key"] in ("value", "heat") for it in g["items"] if it.get("pctile") is not None]
    hot = [it["pctile"] if it.get("high_is_hot", True) else 100 - it["pctile"] for it in items]
    ev = [f"{it['label']} {it['value']:.1f}{it.get('unit', '')}（歷史百分位 {it['pctile']:.0f}%，{it['grade']}）"
          for it in sorted(items, key=lambda x: -(x["pctile"] if x.get("high_is_hot", True) else 100 - x["pctile"]))[:4]]
    return _dim("valuation", "估值泡沫", "Valuation", float(np.mean(hot)) if hot else None, ev,
                note="、".join(val.get("hot", [])[:4]))


# ---------------------------------------------------------------- 6) earnings cycle
def earnings(te: Dict) -> Dict:
    se = (te or {}).get("season") or {}
    if not se.get("n"):
        return _dim("earnings", "財報循環", "Earnings cycle", None, ["近 45 天財報樣本不足"])
    beat = se["beats"] / se["n"] * 100
    ev = [f"近 45 天 {se['n']} 家科技／成長公司財報，{beat:.0f}% 超預期，平均驚喜 {se.get('avg_surp') or 0:+.1f}%"]
    score = _clip((85 - beat) * 2 + 20)               # 85% beat → 20 (healthy), 60% → 70 (deteriorating)
    react = se.get("avg_react")
    if react is not None:
        ev.append(f"財報後平均股價反應 {react:+.1f}%")
        if beat >= 70 and react < 0:
            score = _clip(score + 10)
            ev.append("好消息不漲：超預期比例高但股價下跌，常見於估值過高或景氣循環高點")
    if se.get("rev_yoy") is not None:
        ev.append(f"營收年增中位數 {se['rev_yoy']:+.1f}%")
        if se["rev_yoy"] < 0:
            score = _clip(score + 10)
    groups = [g for g in (te or {}).get("groups", []) if g.get("beat") is not None]
    weak = [g["theme"] for g in sorted(groups, key=lambda g: g["beat"])[:2] if g["beat"] < 60]
    if weak:
        ev.append("超預期比例最低的族群：" + "、".join(weak))
    return _dim("earnings", "財報循環", "Earnings cycle", score, ev)


# ---------------------------------------------------------------- 7) sectors & breadth
DEFENSIVE = {"XLP", "XLU", "XLV"}


def sectors(rot: Dict, exposure: Optional[Dict] = None) -> Dict:
    if not (rot or {}).get("available"):
        return _dim("sectors", "產業與市場寬度", "Sectors & breadth", None, ["類股資料暫缺"])
    ev, parts = [], []
    us = ((rot.get("breadth") or {}).get("us") or {}).get("now")
    if us is not None:
        parts.append(100 - us)
        ev.append(f"美股站上 200 日線比例 {us:.0f}%" + ("（多數股票已在長期均線下）" if us < 40 else ""))
    secs = rot.get("sectors", [])
    if secs:
        lead = [s["name"] for s in secs if s.get("quad") == "領先"]
        weak = sum(1 for s in secs if s.get("quad") in ("落後", "轉弱")) / len(secs) * 100
        parts.append(weak)
        defl = [s["sym"] for s in secs if s.get("quad") == "領先" and s["sym"] in DEFENSIVE]
        ev.append(f"{weak:.0f}% 類股處於落後／轉弱象限；領先：{'、'.join(lead[:4]) or '無'}")
        if defl:
            parts.append(70.0)
            ev.append("防禦類股（必需消費／公用事業／醫療）領漲：資金轉向避險")
    eq = rot.get("equal_weight") or {}
    if eq.get("chg_3m") is not None:
        ev.append(f"等權重相對市值加權 3 個月 {eq['chg_3m']:+.1f}%" + ("（漲勢集中在少數權值股）" if eq["chg_3m"] < -3 else ""))
    for r in ((exposure or {}).get("paths") or [])[:1]:
        worst = [h for h in r["holdings"] if h.get("significant") and h["sens_pct_per10"] < 0][:3]
        if worst:
            ev.append(f"若「{r['path']}」升溫，歷史上最受傷：" + "、".join(f"{h.get('name', h['sym'])} {h['sens_pct_per10']:+.1f}%" for h in worst))
    return _dim("sectors", "產業與市場寬度", "Sectors & breadth", float(np.mean(parts)) if parts else None, ev)


# ---------------------------------------------------------------- 8) macro regime, 9) news
def macro(rg: Dict) -> Dict:
    from .intel import macro_pillar
    m, why = macro_pillar(rg or {})
    ev = [t for _, t in why]
    if (rg or {}).get("drift"):
        ev.append(f"一個月漂移：{rg['drift']}")
    return _dim("macro", "總經情勢", "Macro regime", m, ev, note=(rg or {}).get("quadrant", ""))


def news(intel: Dict) -> Dict:
    v = (intel or {}).get("verdict") or {}
    if not v.get("available"):
        return _dim("news", "新聞情報", "News intelligence", None, ["情報融合尚未計算"])
    ch = intel.get("channels", [])
    conf = [r["channel"] for r in ch if r["state"] == "確認"]
    ev = [f"新聞與價格同時示警（確認）：{'、'.join(conf) or '無'}"]
    lead = [r["channel"] for r in ch if r["state"] == "敘事領先"]
    if lead:
        ev.append("只有新聞、價格未跟（敘事領先）：" + "、".join(lead))
    top = next((r for r in ch if r["top"]), None)
    if top:
        ev.append(f"最熱頭條（{top['channel']}）：{top['top'][0]['title'][:80]}")
    score = (v.get("pillars") or {}).get("情報")
    if score is not None and conf:
        score = _clip(score + 5 * len(conf))
    if score is not None and any(r.get("warmup") for r in ch):
        score = 50 + (score - 50) * 0.5             # absolute news volume without a baseline: half confidence
        ev.append("新聞熱度歷史基準仍在累積，分數已往中間值收斂一半")
    return _dim("news", "新聞情報", "News intelligence", score, ev)


# ---------------------------------------------------------------- facade
def build(engine) -> Dict:
    st = getattr(engine, "stress", None)
    fred = engine.fred
    dims = [recession(fred), crisis(st, getattr(engine, "odds", None) or {}), credit(fred), banking(st, fred),
            valuation(getattr(engine, "valuation", None) or {}), earnings(getattr(engine, "techearn", None) or {}),
            sectors(getattr(engine, "rotation", None) or {}, getattr(engine, "exposure", None)),
            macro(getattr(engine, "regime", None) or {}), news(getattr(engine, "intel", None) or {})]
    w = dict(WEIGHTS)
    w.update(CFG.get("weights") or {})
    have = [d for d in dims if d["score"] is not None]
    if not have:
        return {"available": False, "dims": dims}
    tot = sum(w.get(d["key"], 0) for d in have)
    comp = sum(w.get(d["key"], 0) * d["score"] for d in have) / tot if tot else float(np.mean([d["score"] for d in have]))
    lz, le = level(comp)
    ranked = sorted(have, key=lambda d: -d["score"])
    top = [d for d in ranked if d["score"] >= 55][:3] or ranked[:1]
    horizons = []
    crash = next((d["forecast"]["crash"] for d in dims if d["key"] == "crisis" and d["forecast"]), [])
    for f in crash:
        months = {21: 1, 63: 3, 126: 6}.get(f["days"], round(f["days"] / 21))
        horizons.append({"months": months, "zh": f"{months} 個月內標普跌≥{f['dd']:.0f}%", "en": f"S&P −{f['dd']:.0f}% within {months}m",
                         "prob": f["prob"], "base": f["base"], "model_zh": "壓力指數條件機率（走步外樣本檢驗）",
                         "model_en": "Stress-conditioned odds (walk-forward checked)"})
    rec = next((d["forecast"] for d in dims if d["key"] == "recession" and d["forecast"]), None)
    if rec:
        horizons.append({"months": 12, "zh": "12 個月內美國衰退", "en": "US recession within 12m", "prob": rec["prob"],
                         "base": None, "prev": rec["prev"], "model_zh": rec["model_zh"], "model_en": rec["model_en"]})
    headline = (f"全方位風險 {lz}（{comp:.0f}/100）｜最大風險："
                + "、".join(f"{d['zh']} {d['score']:.0f}" for d in top))
    return {"available": True, "score": round(comp, 1), "label": lz, "label_en": le, "dims": dims, "top": [d["key"] for d in top],
            "horizons": horizons, "weights": w, "headline": headline, "coverage": len(have) / len(dims),
            "note": "綜合分數是透明的加權平均（權重可在 settings.yaml 調整），不是預測模型；預測只來自有實證紀錄的模型。"}


def summary_lines(o: Dict) -> List[str]:
    if not (o or {}).get("available"):
        return []
    out = [o["headline"]]
    for d in sorted([d for d in o["dims"] if d["score"] is not None], key=lambda d: -d["score"]):
        out.append(f"{d['zh']} {d['score']:.0f}［{d['label']}］：" + "；".join(d["evidence"][:2]))
    for h in o["horizons"]:
        out.append(f"預測｜{h['zh']}：{h['prob']:.1f}%" + (f"（平常 {h['base']:.1f}%）" if h.get("base") is not None else "")
                   + f"〔{h['model_zh']}〕")
    return out
