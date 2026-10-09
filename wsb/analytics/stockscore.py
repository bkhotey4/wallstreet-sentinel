"""Stock scoring board: a rules-based screen of ~110 large caps (US / Taiwan / Hong Kong), ranked high → low.

    composite = technical × 0.6 + intel × 0.4      (intel missing → technical only, and the row says so)

Technical (0–100, ranked within each market):
    trend         price vs 50/200-day averages, golden/death cross, 200-day slope
    momentum      12-1 month, 6-month and 3-month returns (cross-sectional ranks)
    relative      3-month return minus the market index
    near_high     distance from the 52-week high
    accumulation  up-day volume vs down-day volume, last 20 sessions
    low_vol       60-day volatility (lower ranks better)
    RSI(14) > 75 / 80 subtracts a few points (over-extended)
Intel (0–100, 50 = neutral; each input in [-1, 1]):
    news tone (Google News headlines, keyword tagged), off-exchange short ratio vs own history (US, FINRA),
    insider open-market buying/selling (US, SEC Form 4), tracked managers adding/trimming (US, 13F),
    外資＋投信 5-day net buy vs turnover (Taiwan, TWSE T86)

It is a screen of what prices and public filings say right now — not a forecast and not investment advice."""
from __future__ import annotations

import json
import logging
import math

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..data.stocks import cfg, theme_names, universe

log = logging.getLogger(__name__)
_HIST = DATA_DIR / "stockscore_hist.json"
MIN_BARS = 60                             # ~3 months of trading: enough for the 50-day average, RSI and 3-month momentum


def rsi(c: pd.Series, n: int = 14) -> Optional[float]:
    d = c.diff().dropna()
    if len(d) < n + 5:
        return None
    up, dn = d.clip(lower=0), -d.clip(upper=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean().iloc[-1]
    ad = dn.ewm(alpha=1 / n, adjust=False).mean().iloc[-1]
    if ad == 0:
        return 100.0
    return float(100 - 100 / (1 + au / ad))


def _ret(c: pd.Series, a: int, b: int = 0) -> Optional[float]:
    """Return from `a` sessions ago to `b` sessions ago (b=0 → latest)."""
    if len(c) <= a:
        return None
    end = c.iloc[-1 - b] if b else c.iloc[-1]
    start = c.iloc[-1 - a]
    return float(end / start - 1) * 100 if start > 0 else None


def features(c: pd.Series, v: pd.Series, bench: pd.Series) -> Optional[Dict]:
    c = c[c > 0].dropna()
    if len(c) < MIN_BARS:                 # new listings (e.g. a recent IPO) are scored on what exists; longer factors stay None
        return None
    p = float(c.iloc[-1])
    ma50 = float(c.tail(50).mean())
    ma200 = float(c.tail(200).mean()) if len(c) >= 200 else None
    ma200_prev = float(c.iloc[-221:-21].mean()) if len(c) >= 221 else None
    trend = [p > ma50]
    if ma200 is not None:
        trend += [p > ma200, ma50 > ma200]
    if ma200 is not None and ma200_prev is not None:
        trend.append(ma200 > ma200_prev)
    yr = c.tail(252)
    lr = np.log(c).diff().dropna()
    vv = v.reindex(c.index).fillna(0) if len(v) else pd.Series(0.0, index=c.index)
    last = c.tail(21).diff().dropna()
    vol_last = vv.reindex(last.index)
    upv, dnv = float(vol_last[last > 0].sum()), float(vol_last[last < 0].sum())
    b = bench[bench > 0].dropna()
    r3 = _ret(c, 63)
    b3 = _ret(b, 63) if len(b) else None
    return {"price": p, "ma50": ma50, "ma200": ma200,
            "trend": sum(trend) / len(trend), "trend_n": len(trend),
            "above50": p > ma50, "above200": None if ma200 is None else p > ma200,
            "golden": None if ma200 is None else ma50 > ma200,
            "r1d": _ret(c, 1), "r1m": _ret(c, 21), "r3": r3, "r6": _ret(c, 126), "r12_1": _ret(c, 252, 21),
            "rel3": None if r3 is None or b3 is None else r3 - b3,
            "dist_high": float(p / yr.max() - 1) * 100, "new_high": p >= float(yr.max()) * 0.999,
            "new_low": p <= float(yr.min()) * 1.001,
            "vol60": float(lr.tail(60).std() * math.sqrt(252) * 100) if len(lr) >= 60 else None,
            "rsi": rsi(c), "accum": (upv / dnv) if dnv > 0 else (2.0 if upv > 0 else None),
            "asof": c.index[-1].strftime("%Y-%m-%d")}


def _rank(vals: Dict[str, Optional[float]], higher_better: bool = True) -> Dict[str, Optional[float]]:
    """Cross-sectional percentile (0–100) within one market; missing stays missing."""
    have = {k: v for k, v in vals.items() if v is not None and np.isfinite(v)}
    if len(have) < 3:
        return {k: None for k in vals}
    s = pd.Series(have).rank(pct=True, ascending=higher_better) * 100
    return {k: (float(s[k]) if k in s else None) for k in vals}


def _intel_inputs(eng, mk: str, sym: str, f: Dict) -> List[Dict]:
    """Each input: {key, val in [-1,1], w, zh, en}."""
    out: List[Dict] = []
    sn = getattr(eng, "stocknews", None)
    if sn is not None:
        ns = sn.summary(sym)
        if ns["pos"] + ns["neg"] > 0:
            val = (ns["pos"] - ns["neg"]) / max(3, ns["pos"] + ns["neg"])
            out.append({"key": "news", "val": float(np.clip(val, -1, 1)), "w": 1.0,
                        "zh": f"新聞語氣{'偏多' if val > 0.15 else '偏空' if val < -0.15 else '中性'}（正面 {ns['pos']}／負面 {ns['neg']} 則）",
                        "en": f"News tone {'positive' if val > 0.15 else 'negative' if val < -0.15 else 'mixed'} ({ns['pos']}+ / {ns['neg']}−)"})
    if mk == "us":
        dp = getattr(eng, "darkpool", None)
        t = dp.ticker(sym) if dp is not None and hasattr(dp, "ticker") else None
        if t and t.get("pctile") is not None:
            val = (t["pctile"] - 50) / 50
            out.append({"key": "darkpool", "val": float(val), "w": 0.8,
                        "zh": f"場外放空比例 {t['ratio_5d']:.0f}%（自身歷史第 {t['pctile']:.0f} 百分位，{'買盤偏強' if val > 0.3 else '賣壓偏重' if val < -0.3 else '中性'}）",
                        "en": f"Off-exchange short ratio {t['ratio_5d']:.0f}% (own-history pct {t['pctile']:.0f})"})
        ins = getattr(eng, "insiders", None)
        r = ins.ticker(sym) if ins is not None and hasattr(ins, "ticker") else None
        if r and (r["buy_usd"] or r["sell_disc_usd"]):
            net = r["buy_usd"] - r["sell_disc_usd"]
            val = float(np.tanh(net / 25e6))
            out.append({"key": "insider", "val": val, "w": 0.7,
                        "zh": (f"內部人 {r['days']} 天公開市場買進 ${r['buy_usd'] / 1e6:,.1f}M" if r["buy_usd"] > r["sell_disc_usd"]
                               else f"內部人 {r['days']} 天非計畫性賣出 ${r['sell_disc_usd'] / 1e6:,.1f}M"),
                        "en": f"Insiders {r['days']}d: buys ${r['buy_usd'] / 1e6:,.1f}M / discretionary sells ${r['sell_disc_usd'] / 1e6:,.1f}M"})
        gu = getattr(eng, "gurus", None)
        g = gu.ticker(sym) if gu is not None and hasattr(gu, "ticker") else None
        if g and (g["add"] or g["cut"]):
            net = g["add"] - g["cut"]
            out.append({"key": "gurus", "val": float(np.clip(net / 2, -1, 1)), "w": 0.6,
                        "zh": f"追蹤大師本季 {g['add']} 位加碼／新建倉、{g['cut']} 位減碼／出清", "en": f"Tracked managers: {g['add']} added, {g['cut']} cut"})
    if mk == "tw":
        tw = getattr(eng, "taiwan", None)
        fl = tw.stock_flow(sym.split(".")[0]) if tw is not None and hasattr(tw, "stock_flow") else None
        sp = getattr(eng, "stockprices", None)
        avgv = None
        if sp is not None:
            vol = sp.vol(sym).tail(20)
            avgv = float(vol.mean()) / 1000 if len(vol) else None            # shares → 張
        if fl and avgv:
            ratio = (fl["foreign"] + fl["trust"]) / (avgv * fl["days"])
            out.append({"key": "tw_flow", "val": float(np.clip(ratio * 5, -1, 1)), "w": 1.2,
                        "zh": f"外資＋投信 {fl['days']} 日{'買超' if ratio >= 0 else '賣超'} {abs(fl['foreign'] + fl['trust']):,.0f} 張（外資 {fl['foreign']:+,.0f}、投信 {fl['trust']:+,.0f}）",
                        "en": f"Foreign+trust {fl['days']}d net {fl['foreign'] + fl['trust']:+,.0f} lots"})
    return out


def _reasons(f: Dict, ranks: Dict, n: int) -> List[Dict]:
    R: List[Dict] = []
    if f.get("above200") and f.get("golden"):
        R.append({"zh": "站上 200 日線且均線多頭排列", "en": "Above 200-day, 50 > 200 (uptrend)", "s": 1})
    elif f.get("above200") is False and f.get("golden") is False:
        R.append({"zh": "跌破 200 日線且均線空頭排列", "en": "Below 200-day, 50 < 200 (downtrend)", "s": -1})
    elif f.get("above200") is False:
        R.append({"zh": "跌破 200 日線", "en": "Below 200-day average", "s": -1})
    if f.get("r6") is not None and ranks.get("momentum") is not None:
        top = ranks["momentum"]
        tag = "（同市場前 20%）" if top >= 80 else "（同市場後 20%）" if top <= 20 else ""
        R.append({"zh": f"近 6 個月 {f['r6']:+.0f}%{tag}", "en": f"6-month {f['r6']:+.0f}%", "s": 1 if top >= 80 else -1 if top <= 20 else 0})
    if f.get("rel3") is not None and abs(f["rel3"]) >= 5:
        R.append({"zh": f"3 個月{'強於' if f['rel3'] > 0 else '弱於'}大盤 {abs(f['rel3']):.0f} 個百分點", "en": f"3m vs index {f['rel3']:+.0f} pp",
                  "s": 1 if f["rel3"] > 0 else -1})
    if f.get("new_high"):
        R.append({"zh": "創 52 週新高", "en": "52-week high", "s": 1})
    elif f.get("dist_high") is not None and f["dist_high"] <= -30:
        R.append({"zh": f"距 52 週高點 {f['dist_high']:.0f}%", "en": f"{f['dist_high']:.0f}% from 52w high", "s": -1})
    r = f.get("rsi")
    if r is not None and r >= 75:
        R.append({"zh": f"RSI {r:.0f} 過熱", "en": f"RSI {r:.0f} overbought", "s": -1})
    elif r is not None and r <= 30:
        R.append({"zh": f"RSI {r:.0f} 超賣", "en": f"RSI {r:.0f} oversold", "s": 0})
    if f.get("accum") is not None and (f["accum"] >= 1.6 or f["accum"] <= 0.6):
        R.append({"zh": "近一月上漲日量能明顯大於下跌日（有人進貨）" if f["accum"] >= 1.6 else "近一月下跌日量能明顯較大（有人出貨）",
                  "en": "Up-day volume dominates (accumulation)" if f["accum"] >= 1.6 else "Down-day volume dominates (distribution)",
                  "s": 1 if f["accum"] >= 1.6 else -1})
    return R


def technical_scores(feats: Dict[str, Dict]) -> Dict[str, tuple]:
    """sym → (technical score 0–100, factor parts, momentum rank) with every factor ranked within `feats` (one market)."""
    tw = cfg().get("tech_weights") or {}
    W = {"trend": 0.25, "momentum": 0.30, "relative": 0.15, "near_high": 0.15, "accumulation": 0.10, "low_vol": 0.05, **tw}
    hot1, hot2 = (cfg().get("rsi_hot") or [75, 80])[:2]
    mom_parts = [_rank({k: f["r12_1"] for k, f in feats.items()}), _rank({k: f["r6"] for k, f in feats.items()}),
                 _rank({k: f["r3"] for k, f in feats.items()})]
    mom = {k: (float(np.nanmean([p[k] for p in mom_parts if p[k] is not None])) if any(p[k] is not None for p in mom_parts) else None)
           for k in feats}
    rk = {"momentum": mom,
          "relative": _rank({k: f["rel3"] for k, f in feats.items()}),
          "near_high": _rank({k: f["dist_high"] for k, f in feats.items()}),
          "accumulation": _rank({k: f["accum"] for k, f in feats.items()}),
          "low_vol": _rank({k: f["vol60"] for k, f in feats.items()}, higher_better=False)}
    out = {}
    for sym, f in feats.items():
        parts = {"trend": f["trend"] * 100, **{k: rk[k][sym] for k in rk}}
        have = {k: v for k, v in parts.items() if v is not None}
        tech = sum(W[k] * v for k, v in have.items()) / sum(W[k] for k in have)
        if f["rsi"] is not None:
            tech -= 8 if f["rsi"] >= hot2 else 4 if f["rsi"] >= hot1 else 0
        out[sym] = (float(np.clip(tech, 0, 100)), parts, mom[sym])
    return out


def build(eng, uni: Optional[Dict] = None, persist: bool = True) -> Dict:
    """uni: optional universe override (used by the on-demand /stock lookup); persist=False leaves the score history alone."""
    if not cfg().get("enabled", True):
        return {"available": False}
    sp = getattr(eng, "stockprices", None)
    if sp is None or sp.close.empty:
        return {"available": False}
    wt = cfg().get("weights") or {}
    w_tech, w_int = float(wt.get("technical", 0.6)), float(wt.get("intel", 0.4))
    prev = _load_hist()
    markets: Dict[str, Dict] = {}
    for mk, m in (uni or universe()).items():
        bench = sp.series(m.get("bench", ""))
        if bench.empty and getattr(eng, "market", None) is not None:
            bench = eng.market.series(m.get("bench", ""))
        feats = {}
        for sym in m["symbols"]:
            try:
                f = features(sp.series(sym), sp.vol(sym), bench)
            except Exception:  # noqa: BLE001
                log.exception("features %s", sym)
                f = None
            if f:
                feats[sym] = f
        if len(feats) < 5:
            continue
        tscores = technical_scores(feats)
        rows = []
        for sym, f in feats.items():
            tech, parts, mom_s = tscores[sym]
            ins = _intel_inputs(eng, mk, sym, f)
            # shrink toward neutral when the evidence is thin: one input alone can move intel at most ±(50 × w/2)
            wsum = sum(i["w"] for i in ins)
            intel = (50 + 50 * sum(i["val"] * i["w"] for i in ins) / wsum * min(1.0, wsum / 2.0)) if ins else None
            score = w_tech * tech + w_int * intel if intel is not None else tech
            zh, en = m["symbols"][sym]
            p5 = _prev_score(prev.get(mk) or {}, sym, 5, max(x["asof"] for x in feats.values()))
            rows.append({"sym": sym, "code": sym.split(".")[0], "name": zh, "name_en": en, "theme": m["themes"].get(sym, "其他"),
                         "score": round(float(score), 1),
                         "tech": round(tech, 1), "intel": None if intel is None else round(float(intel), 1),
                         "chg5": None if p5 is None else round(float(score) - p5, 1),
                         "parts": {k: (None if v is None else round(float(v), 0)) for k, v in parts.items()},
                         "intel_inputs": ins, "reasons": _reasons(f, {"momentum": mom_s}, len(feats)),
                         **{k: f[k] for k in ("price", "r1d", "r1m", "r3", "r6", "rsi", "dist_high", "asof", "above200", "above50",
                                              "new_high", "new_low")}})
        rows.sort(key=lambda r: -r["score"])
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        b = [f for f in feats.values()]
        breadth = {"n": len(b), "above200": _share([f["above200"] for f in b]), "above50": _share([f["above50"] for f in b]),
                   "new_high": sum(1 for f in b if f["new_high"]), "new_low": sum(1 for f in b if f["new_low"])}
        markets[mk] = {"key": mk, "label": m.get("label", mk), "label_en": m.get("label_en", mk), "bench": m.get("bench"),
                       "rows": rows, "breadth": breadth, "asof": max(f["asof"] for f in b),
                       "missing": [s for s in m["symbols"] if s not in feats], "themes": theme_stats(rows)}
    if persist:
        _save_hist(prev, markets)
    return {"available": bool(markets), "markets": markets, "themes": cross_themes(markets)}


def theme_stats(rows: List[Dict]) -> List[Dict]:
    """Per 族群 inside one market: average score, average 1/3/6-month return, share above the 200-day, leaders."""
    order = list(theme_names())
    by: Dict[str, List[Dict]] = {}
    for r in rows:
        by.setdefault(r["theme"], []).append(r)
    out = []
    for th, rs in by.items():
        mean = lambda k: (float(np.mean([r[k] for r in rs if r.get(k) is not None]))  # noqa: E731
                          if any(r.get(k) is not None for r in rs) else None)
        ab = [r["above200"] for r in rs if r.get("above200") is not None]
        out.append({"theme": th, "theme_en": theme_names().get(th, th), "n": len(rs), "score": mean("score"),
                    "r1m": mean("r1m"), "r3": mean("r3"), "r6": mean("r6"),
                    "above200": float(np.mean(ab) * 100) if ab else None,
                    "leaders": [(r["name"], r["code"], r["score"]) for r in sorted(rs, key=lambda r: -r["score"])[:3]],
                    "order": order.index(th) if th in order else 99})
    return sorted(out, key=lambda t: -(t["score"] or 0))


def cross_themes(markets: Dict[str, Dict]) -> List[Dict]:
    """Same 族群 across US / Taiwan / Hong Kong (e.g. 半導體 in all three)."""
    order = list(theme_names())
    allt = {t["theme"] for m in markets.values() for t in m["themes"]}
    out = []
    for th in sorted(allt, key=lambda t: order.index(t) if t in order else 99):
        per = {mk: next((t for t in m["themes"] if t["theme"] == th), None) for mk, m in markets.items()}
        sc = [t["score"] for t in per.values() if t and t["score"] is not None]
        n = sum(t["n"] for t in per.values() if t)
        out.append({"theme": th, "theme_en": theme_names().get(th, th), "per": per, "n": n,
                    "score": float(np.average(sc, weights=[t["n"] for t in per.values() if t and t["score"] is not None])) if sc else None})
    return sorted(out, key=lambda t: -(t["score"] or 0))


def _share(xs) -> Optional[float]:
    v = [x for x in xs if x is not None]
    return float(sum(v) / len(v) * 100) if v else None


def _load_hist() -> Dict[str, Dict[str, float]]:
    try:
        if _HIST.exists():
            return json.loads(_HIST.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("score history unreadable: %s", e)
    return {}


def _prev_score(hist: Dict, sym: str, back: int, asof: str) -> Optional[float]:
    """Score `back` trading sessions ago. History is keyed by each market's own data date (not the calendar day),
    so weekends / holidays never count as sessions and today's provisional entry is excluded."""
    ds = [d for d in sorted(hist) if d < asof and sym in hist[d]]
    return float(hist[ds[-back]][sym]) if len(ds) >= back else None


def _save_hist(hist: Dict, markets: Dict) -> None:
    """{market: {data date: {sym: score}}}; the latest session's entry is refreshed on every run."""
    hist = {k: v for k, v in hist.items() if k in universe()}        # drops the old calendar-keyed layout
    keep = int(cfg().get("history_days", 40))
    for mk, m in markets.items():
        h = dict(hist.get(mk) or {})
        h[m["asof"]] = {r["sym"]: r["score"] for r in m["rows"]}
        hist[mk] = dict(sorted(h.items())[-keep:])
    try:
        _HIST.write_text(json.dumps(hist, separators=(",", ":")), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log.warning("score history not saved: %s", e)


def summary_lines(res: Dict, top: int = 5) -> List[str]:
    if not res or not res.get("available"):
        return []
    L = []
    for m in res["markets"].values():
        best = "、".join(f"{r['name']}({r['code']}) {r['score']:.0f}" for r in m["rows"][:top])
        worst = "、".join(f"{r['name']}({r['code']}) {r['score']:.0f}" for r in m["rows"][-3:])
        br = m["breadth"]
        L.append(f"{m['label']}評分前段：{best}；後段：{worst}；評分池站上 200 日線 {br['above200']:.0f}%"
                 if br.get("above200") is not None else f"{m['label']}評分前段：{best}")
    th = res.get("themes") or []
    if th:
        L.append("族群強弱（跨美台港平均分數）：" + "、".join(f"{t['theme']} {t['score']:.0f}" for t in th if t["score"] is not None))
    return L
