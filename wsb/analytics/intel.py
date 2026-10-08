"""Intelligence fusion: news narrative × market pricing × macro regime → one explainable risk verdict.

Why: the Stress Index and the shock radar only see PRICES; the news wire only sees HEADLINES; the regime model only
sees the macro MIX.  A risk that shows up in all three is far more credible than one that shows up in one.

  1. channels   – every headline is tagged to one of the six transmission paths used by the shock radar
                  (信用事件, 利率／債市衝擊, 套息拆倉, 波動率／槓桿去化, 景氣衰退, 商品／地緣能源), weighted by its
                  keyword risk score and recency.  Each channel's heat is ranked against its OWN 30-day history
                  (stored in SQLite), so a normally noisy channel (geopolitics) is not always "hot".
  2. fusion     – per channel, news heat × market ignition (shock radar):
                    確認      headlines AND prices both flag it            → highest priority
                    敘事領先  headlines are loud, prices calm               → early warning or noise; watch the blocks
                    無聲壓力  prices stressed, headlines quiet              → positioning/funding-driven; often under-reported
                    平靜      neither
  3. pillars    – 量化 (SSI), 總經 (quadrant + drift + liquidity + risk appetite), 情報 (news heat) → weighted
                  composite with every point traceable, plus a confidence that reflects how much the pillars agree.

Honesty note: only the quant pillar is backtested (crash-odds / walk-forward).  The news baseline is only as old as
the bot's own history, and the composite weights are a transparent judgment framework, not a fitted model."""
from __future__ import annotations

import math
import re
import time
from typing import Dict, List, Optional, Tuple

from ..config import SETTINGS
from .. import store

CFG = SETTINGS.get("intel", {})

DEFAULT_CHANNELS: Dict[str, Dict[str, List[str]]] = {
    "信用事件": {
        "risk": ["private credit", "default", "defaults", "bankruptcy", "chapter 11", "downgrade", "downgraded",
                 "credit spreads", "junk bond", "junk bonds", "high-yield", "bdc", "redemption", "redemptions",
                 "gated", "writedown", "write-down", "bank run", "deposit outflows", "regional bank", "regional banks",
                 "commercial real estate", "loan losses", "delinquency", "delinquencies", "liquidity crisis",
                 "contagion", "insolvency", "違約", "破產", "倒閉", "擠兌", "降評", "私募信貸", "壞帳", "信用利差"],
        "relief": ["bailout", "rescue", "backstop", "recapitalization", "紓困", "注資"]},
    "利率／債市衝擊": {
        "risk": ["bond selloff", "bond sell-off", "yields surge", "yields jump", "yields soar", "term premium",
                 "treasury auction", "weak auction", "rate hike", "rate hikes", "hawkish", "higher for longer",
                 "deficit", "debt ceiling", "bond vigilantes", "treasury yields", "gilt", "jgb",
                 "美債", "殖利率", "升息", "鷹派", "標售", "赤字"],
        "relief": ["rate cut", "rate cuts", "dovish", "yields fall", "yields drop", "yields ease", "降息", "鴿派"]},
    "套息拆倉": {
        "risk": ["yen", "boj", "bank of japan", "carry trade", "unwind", "currency intervention", "intervention",
                 "dollar surges", "strong dollar", "yuan", "renminbi", "korean won", "capital outflows",
                 "emerging markets selloff", "日圓", "日銀", "套息", "干預", "人民幣", "韓元", "匯率"],
        "relief": ["yen weakens", "dollar eases"]},
    "波動率／槓桿去化": {
        "risk": ["vix", "volatility", "selloff", "sell-off", "plunge", "plunges", "crash", "rout", "margin call",
                 "margin calls", "deleveraging", "liquidation", "circuit breaker", "trading halt", "hedge fund",
                 "hedge funds", "short squeeze", "gamma", "崩盤", "暴跌", "熔斷", "斷頭", "去槓桿"],
        "relief": ["rally", "rallies", "rebound", "rebounds", "record high", "record highs", "反彈", "創新高"]},
    "景氣衰退": {
        "risk": ["recession", "layoffs", "job cuts", "jobless claims", "unemployment", "payrolls", "slowdown",
                 "contraction", "consumer spending", "profit warning", "guidance cut", "cuts guidance",
                 "衰退", "裁員", "失業", "景氣"],
        "relief": ["soft landing", "strong jobs", "beats expectations", "軟著陸"]},
    "商品／地緣能源": {
        "risk": ["oil", "crude", "opec", "brent", "natural gas", "sanctions", "missile", "missiles", "invasion",
                 "blockade", "war", "drone", "drones", "taiwan strait", "middle east", "iran", "israel", "russia",
                 "ukraine", "red sea", "hormuz", "tariff", "tariffs", "export controls",
                 "油價", "制裁", "飛彈", "戰爭", "台海", "封鎖", "關稅", "地緣"],
        "relief": ["ceasefire", "truce", "peace talks", "停火", "和談"]},
}

_M = (CFG.get("model") or {})                       # settings.yaml → intel.model (defaults = original design)
QUAD_RISK = {k: float(v) for k, v in (_M.get("quadrant_risk") or
                                      {"金髮女孩": 30.0, "再通膨": 45.0, "通縮衰退": 65.0, "停滯性通膨": 75.0}).items()}
_LV = _M.get("levels") or [65, 50, 35]
LEVELS = [(_LV[0], "高", "🔴"), (_LV[1], "偏高", "🟠"), (_LV[2], "中性", "🟡"), (0, "低", "🟢")]
_PTS = {"liq_contract": 10, "liq_expand": -5, "risk_off": 10, "risk_on": -5, "quad_worse": 8, "quad_better": -4,
        "growth_drift": 5, "stagflation_drift": 5, **(_M.get("macro_points") or {})}
_SIDE = _M.get("side_thresholds") or [55, 40]
STATE_TEXT = {
    "確認": "新聞與價格同時示警——可信度最高，應優先處理",
    "敘事領先": "新聞很吵、價格還沒反應——可能是早期訊號，也可能只是雜訊；盯住相關區塊是否跟上",
    "無聲壓力": "價格已在施壓、新聞卻安靜——常見於部位／融資驅動的賣壓，容易被低估",
    "平靜": "新聞與價格都沒有異常",
}


def _cfg(k: str, default):
    return CFG.get(k, default)


def _match(title: str, kws: List[str]) -> List[str]:
    t = title.lower()
    out = []
    for kw in kws:
        k = str(kw).lower()
        pat = rf"\b{re.escape(k)}\b" if k.isascii() else re.escape(k)
        if re.search(pat, t):
            out.append(str(kw))
    return out


def level_of(x: Optional[float]) -> Tuple[str, str]:
    if x is None:
        return "資料缺", "⚪"
    for th, name, emo in LEVELS:
        if x >= th:
            return name, emo
    return LEVELS[-1][1], LEVELS[-1][2]


# ---------------------------------------------------------------- 1) news → channels
def channel_heat(items, now: Optional[float] = None) -> Dict[str, Dict]:
    """Tag each headline to transmission channels; heat = Σ (0.5 + 0.5·risk score) · recency decay.
    A headline with no risk keyword at all (score 0, e.g. a routine central-bank data release) weighs half."""
    now = now or time.time()
    half = float(_cfg("half_life_hours", 12))
    chans = _cfg("channels", None) or DEFAULT_CHANNELS
    out = {c: {"heat": 0.0, "n": 0, "relief": 0.0, "n_relief": 0, "top": []} for c in chans}
    for it in items:
        age_h = max(0.0, (now - it.ts) / 3600)
        w = (0.5 + 0.5 * max(int(it.score), 0)) * 0.5 ** (age_h / half)
        for c, kw in chans.items():
            r, ok = _match(it.title, kw.get("risk", [])), _match(it.title, kw.get("relief", []))
            if not r and not ok:
                continue
            d = out[c]
            if len(ok) > len(r):                       # the headline is about the risk EASING
                d["relief"] += w
                d["n_relief"] += 1
            else:
                d["heat"] += w
                d["n"] += 1
                d["top"].append((w, it.source, it.title, r))
    for d in out.values():
        d["top"] = [{"source": s, "title": t, "hits": h} for _, s, t, h in sorted(d["top"], key=lambda x: -x[0])[:3]]
    return out


def news_levels(heat: Dict[str, Dict], history: Optional[Dict[str, List[float]]] = None) -> None:
    """Adds 0–100 `level` per channel: percentile vs the channel's own 30-day heat history; until that baseline has
    `min_baseline` snapshots, a saturating map of absolute heat is used and the channel is flagged as warm-up."""
    min_n = int(_cfg("min_baseline", 48))
    scale = float(_cfg("warmup_heat_scale", 5))
    for c, d in heat.items():
        hist = (history or {}).get(c)
        if hist is None:
            hist = store.heat_history(c, float(_cfg("baseline_days", 30)))
        if len(hist) >= min_n:
            below = sum(1 for h in hist if h < d["heat"])
            ties = sum(1 for h in hist if h == d["heat"])
            d["level"] = 100.0 * (below + 0.5 * ties) / len(hist)
            d["baseline"] = len(hist)
            d["warmup"] = False
        else:
            d["level"] = 100.0 * (1 - math.exp(-d["heat"] / scale))
            d["baseline"] = len(hist)
            d["warmup"] = True
        hot_lv, warm_lv = float(_cfg("news_hot", 80)), float(_cfg("news_warm", 60))
        warm_n = int(_cfg("news_warm_count", 5))                # ≥5 risk headlines are never "quiet"
        d["news_state"] = ("熱" if d["level"] >= hot_lv and d["n"] >= 2 else
                           "溫" if (d["level"] >= warm_lv and d["n"] >= 1) or d["n"] >= warm_n else "冷")
        d["easing"] = d["n_relief"] >= 2 and d["relief"] > d["heat"]


# ---------------------------------------------------------------- 2) fusion with the shock radar
def _drivers(st, blocks: List[str], k: int = 2) -> List[str]:
    if st is None:
        return []
    comps = [c for c in st.components if c.block in blocks and c.score is not None]
    return [f"{c.id} {c.score:.0f}分" for c in sorted(comps, key=lambda c: -c.score)[:k]]


def fuse(heat: Dict[str, Dict], shock: Dict, st=None) -> List[Dict]:
    wm = float(_cfg("market_weight", 0.65))
    paths = {p["name"]: p for p in (shock or {}).get("paths", [])}
    rows = []
    for c, d in heat.items():
        p = paths.get(c)
        ign = p["ignition"] if p else None
        m_hot = p is not None and p["state"] in ("高度警戒", "留意")
        ns = d["news_state"]
        if m_hot:
            state = "確認" if ns in ("熱", "溫") else "無聲壓力"       # 無聲 only when headlines are genuinely quiet
        else:
            state = "敘事領先" if ns == "熱" else "平靜"
        mk = max(0.0, min(100.0, ign)) if ign is not None else None
        fused = d["level"] if mk is None else wm * mk + (1 - wm) * d["level"]
        blocks = p["blocks"] if p else []
        bl = ", ".join(f"{b} {st.blocks[b]:.0f}" for b in blocks if st is not None and b in st.blocks)
        watch = ""
        if state == "敘事領先":
            watch = f"盯 {bl or '相關區塊'}：點火分數 {ign:.0f} → ≥58 代表價格開始確認" if ign is not None else "市場資料不足，無法確認"
        elif state == "無聲壓力":
            dr = _drivers(st, blocks)
            watch = "價格端主要推手：" + ("、".join(dr) if dr else bl or "—")
        elif state == "確認":
            watch = f"已確認；{bl}" + (f"（主要推手 {'、'.join(_drivers(st, blocks))}）" if _drivers(st, blocks) else "")
        rows.append({"channel": c, "state": state, "explain": STATE_TEXT[state], "fused": fused,
                     "news_level": d["level"], "news_state": d["news_state"], "news_n": d["n"],
                     "relief_n": d["n_relief"], "easing": d["easing"], "warmup": d["warmup"],
                     "ignition": ign, "market_state": p["state"] if p else None, "blocks": blocks,
                     "watch": watch, "top": d["top"], "story": p.get("story", "") if p else ""})
    order = {"確認": 0, "無聲壓力": 1, "敘事領先": 2, "平靜": 3}
    return sorted(rows, key=lambda r: (order[r["state"]], -r["fused"]))


# ---------------------------------------------------------------- 3) pillars & verdict
def quadrant_base(g: float, i: float, full_z: float = 0.5) -> float:
    """Smooth quadrant risk: bilinear blend of the four quadrant scores.  At |z| ≥ full_z a side counts fully; near 0 the
    score sits between the neighbouring quadrants, so a z of +0.02 → -0.01 no longer jumps the score by 30 points."""
    pg = min(1.0, max(0.0, 0.5 + g / (2 * full_z)))
    pi = min(1.0, max(0.0, 0.5 + i / (2 * full_z)))
    Q = QUAD_RISK
    return (pg * (pi * Q["再通膨"] + (1 - pi) * Q["金髮女孩"])
            + (1 - pg) * (pi * Q["停滯性通膨"] + (1 - pi) * Q["通縮衰退"]))


def macro_pillar(rg: Dict) -> Tuple[Optional[float], List[Tuple[float, str]]]:
    q = rg.get("quadrant") or ""
    g, i = rg.get("growth_z"), rg.get("inflation_z")
    if g is not None and i is not None:
        base = quadrant_base(g, i)
    else:
        base = next((v for k, v in QUAD_RISK.items() if q.startswith(k)), None)
    if base is None:
        return None, []
    edge = g is not None and i is not None and min(abs(g), abs(i)) < 0.5
    why: List[Tuple[float, str]] = [(base, f"象限 {q}（基準分 {base:.0f}" + ("，位於象限邊界、已依 z 值內插" if edge else "") + "）")]
    liq = rg.get("liquidity_mode") or ""
    if liq.startswith("收縮"):
        why.append((_PTS["liq_contract"], f"聯準會淨流動性 13 週 {rg.get('net_liquidity_chg_13w_bn', 0):+,.0f}bn，收縮逆風"))
    elif liq.startswith("擴張"):
        why.append((_PTS["liq_expand"], f"淨流動性 13 週 {rg.get('net_liquidity_chg_13w_bn', 0):+,.0f}bn，擴張順風"))
    rm = rg.get("risk_mode") or ""
    if rm.startswith("Risk-OFF"):
        why.append((_PTS["risk_off"], f"風險偏好轉弱（z {rg.get('risk_appetite_z', 0):+.2f}）"))
    elif rm.startswith("Risk-ON"):
        why.append((_PTS["risk_on"], f"風險偏好強（z {rg.get('risk_appetite_z', 0):+.2f}）"))
    clear = g is not None and i is not None and min(abs(g), abs(i)) >= 0.25   # a flip on z≈0 is noise, not a regime change
    if rg.get("quadrant_changed") and clear:
        base = next((v for k, v in QUAD_RISK.items() if q.startswith(k)), base)
        old = next((v for k, v in QUAD_RISK.items() if (rg.get("quadrant_1m") or "").startswith(k)), base)
        if base > old:
            why.append((_PTS["quad_worse"], f"一個月內由「{rg.get('quadrant_1m')}」轉入「{q}」，往較差的組合移動"))
        elif base < old:
            why.append((_PTS["quad_better"], f"一個月內由「{rg.get('quadrant_1m')}」改善為「{q}」"))
    gd = rg.get("growth_drift")
    if gd is not None and gd <= -0.5:
        why.append((_PTS["growth_drift"], f"成長動能一個月內明顯轉弱（z {gd:+.2f}）"))
    idr = rg.get("inflation_drift")
    if idr is not None and idr >= 0.5 and (rg.get("growth_z") or 0) <= -0.25:
        why.append((_PTS["stagflation_drift"], f"成長偏弱時通膨卻升溫（z {idr:+.2f}），滯脹壓力"))
    return max(0.0, min(100.0, sum(p for p, _ in why))), why


def watchlist(rg: Dict, fused: List[Dict]) -> List[str]:
    out = [f"{r['channel']}［{r['state']}］：{r['watch']}" for r in fused if r["state"] != "平靜" and r["watch"]][:4]
    g, i = rg.get("growth_z"), rg.get("inflation_z")
    edge = float(_cfg("quadrant_edge_z", 0.3))
    if g is not None and i is not None:
        if abs(g) < edge:
            from .regime import QUADRANTS
            out.append(f"成長 z {g:+.2f} 接近 0：若{'跌破' if g >= 0 else '站上'} 0，象限將轉為「{QUADRANTS[(g < 0, i >= 0)][0]}」")
        if abs(i) < edge:
            from .regime import QUADRANTS
            out.append(f"通膨 z {i:+.2f} 接近 0：若{'跌破' if i >= 0 else '站上'} 0，象限將轉為「{QUADRANTS[(g >= 0, i < 0)][0]}」")
    return out


def verdict(st, rg: Dict, fused: List[Dict], odds: Optional[Dict] = None) -> Dict:
    w = {"量化": 0.5, "總經": 0.25, "情報": 0.25}
    w.update(_cfg("weights", {}) or {})
    ledger: List[Dict] = []
    pillars: Dict[str, Optional[float]] = {}

    # 量化：SSI is the only pillar with a backtest behind it
    if st is not None:
        pillars["量化"] = float(st.score)
        ledger += [{"pillar": "量化", "pts": None, "text": f"{c.id} 分數 {c.score:.0f}（z {c.z:+.2f}）", "dir": "+"}
                   for c in st.drivers(3) if c.score is not None and c.z is not None]
        h = next((h for h in (odds or {}).get("horizons", []) if h["days"] == 63), None)
        if h and h.get("lift_adj") is not None:
            ledger.append({"pillar": "量化", "pts": None, "dir": "+" if h["lift_adj"] > 1 else "-",
                           "text": f"63 日跌≥10% 經驗機率 {(h.get('adjusted') if h.get('adjusted') is not None else h.get('conditional') or 0):.1f}%，為基準的 {h['lift_adj']:.2f} 倍"})
    else:
        pillars["量化"] = None

    m, why = macro_pillar(rg or {})
    pillars["總經"] = m
    ledger += [{"pillar": "總經", "pts": p, "text": t, "dir": "=" if j == 0 else "+" if p > 0 else "-"}
               for j, (p, t) in enumerate(why)]                                  # first entry = quadrant base score

    lv = sorted((r["news_level"] for r in fused), reverse=True)
    n_news = sum(r["news_n"] for r in fused)
    topn = int(_M.get("news_top_channels", 2))
    pillars["情報"] = (sum(lv[:topn]) / len(lv[:topn])) if lv and n_news else None
    for r in fused:
        if r["news_state"] in ("熱", "溫") and r["top"]:
            ledger.append({"pillar": "情報", "pts": None, "dir": "+",
                           "text": f"{r['channel']} 新聞熱度 {r['news_level']:.0f}（{r['news_n']} 則）：{r['top'][0]['title'][:70]}"})
        if r["easing"]:
            ledger.append({"pillar": "情報", "pts": None, "dir": "-", "text": f"{r['channel']} 出現 {r['relief_n']} 則緩和消息"})

    warm = any(r["warmup"] for r in fused)
    if warm and pillars.get("情報") is not None:
        w = dict(w, 情報=w["情報"] * float(_M.get("warmup_news_weight", 0.5)))
    avail = {k: v for k, v in pillars.items() if v is not None}
    if not avail:
        return {"available": False, "pillars": pillars, "ledger": ledger}
    tot_w = sum(w[k] for k in avail)
    base = sum(w[k] * v for k, v in avail.items()) / tot_w
    confirmed = [r["channel"] for r in fused if r["state"] == "確認"]
    bonus = min(float(_cfg("confirm_bonus", 4)) * len(confirmed), float(_cfg("confirm_bonus_cap", 8)))
    if bonus:
        ledger.append({"pillar": "融合", "pts": bonus, "dir": "+",
                       "text": f"新聞與價格同時確認：{'、'.join(confirmed)}（+{bonus:.0f}）"})
    score = max(0.0, min(100.0, base + bonus))

    side = {k: ("警戒" if v >= _SIDE[0] else "平穩" if v <= _SIDE[1] else "中性") for k, v in avail.items()}
    vals = list(side.values())
    agree = max(vals.count(x) for x in vals)
    # deterministic tie-break: the more cautious reading wins
    top_side = next(x for x in ("警戒", "中性", "平穩") if vals.count(x) == agree)
    conf = "高" if agree == 3 else "中" if agree >= 2 else "低"
    if agree >= 2:
        consensus = f"{agree}/{len(avail)} 個支柱判斷「{top_side}」"
    else:
        consensus = "支柱看法分歧（" + "、".join(f"{k}{v}" for k, v in side.items()) + "）"
    caveats = []
    if warm:
        caveats.append("新聞熱度基準仍在累積（不足 1 天歷史），情報分數以絕對熱度估計，權重暫時減半")
        conf = {"高": "中", "中": "低"}.get(conf, conf)
    if st is not None and st.coverage < 0.9:
        caveats.append(f"SSI 資料覆蓋僅 {st.coverage * 100:.0f}%")
        conf = {"高": "中", "中": "低"}.get(conf, conf)
    if len(avail) < 3:
        caveats.append("缺少：" + "、".join(k for k in pillars if pillars[k] is None))
    label, emoji = level_of(score)
    lead = fused[0] if fused and fused[0]["state"] != "平靜" else None
    headline = (f"綜合風險 {emoji}{label}（{score:.0f}）｜" + " / ".join(f"{k} {v:.0f}" for k, v in avail.items())
                + (f"｜主軸：{lead['channel']}［{lead['state']}］" if lead else "｜六條傳導路徑皆平靜"))
    return {"available": True, "score": score, "base": base, "bonus": bonus, "label": label, "emoji": emoji,
            "pillars": pillars, "sides": side, "weights": w, "consensus": consensus,
            "confidence": conf, "caveats": caveats, "ledger": ledger, "headline": headline}


# ---------------------------------------------------------------- facade
def build(engine, record: bool = True, history: Optional[Dict[str, List[float]]] = None,
          now: Optional[float] = None) -> Dict:
    news = engine.news
    items = list(getattr(news, "items", []) or [])
    heat = channel_heat(items, now)
    # only feed the baseline with a live news wire (an outage would otherwise teach it that "zero" is normal)
    if record and items and time.time() - float(getattr(news, "ts", 0) or 0) < 3 * 3600:
        store.heat_record({c: (d["heat"], d["n"]) for c, d in heat.items()},
                          min_gap_s=float(_cfg("record_every_minutes", 30)) * 60)
    news_levels(heat, history)
    fused = fuse(heat, getattr(engine, "shock", None) or {}, engine.stress)
    rg = getattr(engine, "regime", None) or {}
    v = verdict(engine.stress, rg, fused, getattr(engine, "odds", None))
    return {"channels": fused, "verdict": v, "watch": watchlist(rg, fused), "news_items": len(items),
            "regime": {k: rg.get(k) for k in ("quadrant", "quadrant_1m", "drift", "quadrant_changed", "growth_z",
                                               "inflation_z", "risk_mode", "liquidity_mode")}}
