"""VIX 拆解 — why VIX moved today, from prices only (news is never an input).

1. Size: today's change in points / %, and where the level sits in its own past year.
2. Explained vs extra: the past year's daily relation between VIX points and S&P 500 returns (OLS slope) gives the VIX move
   today's index move "should" have caused; the rest is extra fear (or calm), in units of that relation's residual s.d.
3. Where the selling was: index / sector / semis moves in units of each one's own recent daily volatility (σ).
4. Cross-asset: yields (bp), credit, dollar, oil, gold, yen, bitcoin — confirm or not.
5. Term structure (VIX9D / VIX / VIX3M), VVIX, SPX zero-gamma position.
6. Distance to the VIX lines whose back-test verdict is "useful warning" (from the alarm-rule back-test, eng.sx rules).
7. Watch list: the escalation / calm-down conditions with their status now.
Descriptive, not a forecast."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

EQ = [("^GSPC", "標普 500", "S&P 500"), ("^NDX", "那指 100", "Nasdaq 100"), ("^SOX", "費城半導體", "Semiconductors"),
      ("IWM", "小型股", "Small caps")]
CROSS = [("^TNX", "美債 10 年殖利率", "10-year yield"), ("HYG", "高收益債", "High yield bonds"), ("DX-Y.NYB", "美元指數", "Dollar index"),
         ("BZ=F", "布蘭特原油", "Brent"), ("GC=F", "黃金", "Gold"), ("JPY=X", "美元/日圓", "USD/JPY"), ("BTC-USD", "比特幣", "Bitcoin")]


def cfg() -> Dict:
    d = {"lines": [25, 35], "lookback": 252, "hot_pct": 8.0, "hot_level": 25.0}
    return {**d, **(SETTINGS.get("vix_explain", {}) or {})}


def _bp(q: Optional[Dict]) -> Optional[float]:
    if not q or q.get("price") is None or q.get("chg_pct") is None:
        return None
    lvl = float(q["price"])
    lvl = lvl / 10 if lvl > 20 else lvl
    return (lvl - lvl / (1 + q["chg_pct"] / 100)) * 100


def spot_vol(vix: pd.Series, spx: pd.Series, lookback: int) -> Optional[Dict]:
    """Daily VIX point change regressed on S&P 500 % return over the past `lookback` days."""
    j = pd.concat([vix.dropna().diff().rename("dv"), (spx.dropna().pct_change(fill_method=None) * 100).rename("r")], axis=1).dropna().iloc[-lookback:]
    if len(j) < 60 or j["r"].var() == 0:
        return None
    b = float(np.cov(j["r"], j["dv"], ddof=1)[0, 1] / j["r"].var(ddof=1))
    a = float(j["dv"].mean() - b * j["r"].mean())
    res = j["dv"] - (a + b * j["r"])
    return {"a": a, "b": b, "sd": float(res.std(ddof=1)), "n": int(len(j))}


def build(eng) -> Dict:
    m = getattr(eng, "market", None)
    if m is None:
        return {"available": False}
    q: Callable[[str], Optional[Dict]] = m.q
    v = q("^VIX")
    if not v or v.get("price") is None or v.get("chg_pct") is None:
        return {"available": False}
    c = cfg()
    now, ch = float(v["price"]), float(v["chg_pct"])
    prev = now / (1 + ch / 100)
    out: Dict = {"available": True, "asof": v.get("asof"), "vix": now, "chg_pct": ch, "chg_pts": now - prev}
    hist = m.series("^VIX").dropna()
    if len(hist) > 260:
        y = hist.iloc[-252:]
        out["pct_1y"] = float((y < now).mean() * 100)
        out["avg20"] = float(hist.iloc[-20:].mean())
    spx_q = q("^GSPC")
    sv = spot_vol(hist, m.series("^GSPC"), int(c["lookback"]))
    if sv and spx_q and spx_q.get("chg_pct") is not None:
        exp = sv["a"] + sv["b"] * float(spx_q["chg_pct"])
        extra = out["chg_pts"] - exp
        out["spot_vol"] = {**sv, "spx_chg": float(spx_q["chg_pct"]), "expected": exp, "extra": extra,
                           "z": extra / sv["sd"] if sv["sd"] else None}

    def row(t, zh, en):
        x = q(t)
        if not x or x.get("chg_pct") is None:
            return None
        r = {"t": t, "zh": zh, "en": en, "chg": float(x["chg_pct"]), "price": x.get("price"), "sigma": m.sigma_move(t)}
        if t == "^TNX":
            r["bp"] = _bp(x)
        return r
    sec = [(t, n, n) for t, n in ((SETTINGS.universe.get("sectors") or {}).items()) if t not in ("MTUM", "USMV")]
    out["equity"] = [r for r in (row(*e) for e in EQ) if r]
    out["sectors"] = sorted([r for r in (row(*e) for e in sec) if r], key=lambda r: r["chg"])
    out["cross"] = [r for r in (row(*e) for e in CROSS) if r]
    tq = {k: q(k) for k in ("^VIX9D", "^VIX3M", "^VVIX", "^MOVE")}
    if tq["^VIX9D"] and tq["^VIX9D"].get("price"):
        out["vix9d"], out["r9d"] = float(tq["^VIX9D"]["price"]), float(tq["^VIX9D"]["price"]) / now
    if tq["^VIX3M"] and tq["^VIX3M"].get("price"):
        out["vix3m"], out["r3m"] = float(tq["^VIX3M"]["price"]), now / float(tq["^VIX3M"]["price"])
    for k, n in (("^VVIX", "vvix"), ("^MOVE", "move")):
        if tq[k] and tq[k].get("price"):
            out[n], out[n + "_chg"] = float(tq[k]["price"]), tq[k].get("chg_pct")
    op = getattr(getattr(eng, "options", None), "spx", None) or {}
    if op.get("zero_gamma") and op.get("spot"):
        out["gamma"] = {"spot": float(op["spot"]), "flip": float(op["zero_gamma"]), "below": op["spot"] < op["zero_gamma"]}
    rules = ((getattr(eng, "sx", None) or {}).get("rules") or {})
    base = (rules.get("base") or {}).get("dd5")
    lines = []
    for ln in c["lines"]:
        r = next((x for x in rules.get("rows", []) if f"VIX 升破 {ln}" in x.get("zh", "")), None)
        lines.append({"line": float(ln), "dist": float(ln) - now, "hit": now >= ln,
                      "dd5": r.get("dd5") if r else None, "n": r.get("n") if r else None,
                      "verdict": r.get("verdict") if r else None, "base_dd5": base})
    out["lines"] = lines
    out["hot"] = ch >= float(c["hot_pct"]) or now >= float(c["hot_level"])
    return out


def readings(r: Dict) -> List[Dict]:
    """🔑 rule readings of the numbers above (thresholds written in each sentence or in the card note)."""
    out: List[Dict] = []
    ch, pts, now = r["chg_pct"], r["chg_pts"], r["vix"]
    pct = r.get("pct_1y")
    size = f"VIX 今天 {ch:+.1f}%（{pts:+.2f} 點）到 {now:.2f}"
    if pct is not None:
        size += f"，在近一年第 {pct:.0f} 百分位"
        size += "：漲幅大，但水準還在一年的中段以下。" if abs(ch) >= 8 and pct < 60 else "。"
    out.append({"lv": "watch" if ch >= 8 else "info", "zh": size, "en": f"VIX {ch:+.1f}% to {now:.2f}."})
    sv = r.get("spot_vol")
    if sv and sv.get("z") is not None:
        z = sv["z"]
        tail = ("恐慌明顯比大盤跌幅更重：選擇權市場在為接下來的風險額外加價。" if z >= 1.5 else
                "恐慌比大盤跌幅輕：選擇權市場沒有跟著加價。" if z <= -1.0 else "大致和大盤的跌幅相符。")
        out.append({"lv": "alert" if z >= 1.5 else "info",
                    "zh": f"依過去一年的關係，標普 {sv['spx_chg']:+.2f}% 會讓 VIX 變動約 {sv['expected']:+.2f} 點；實際 {pts:+.2f} 點，"
                          f"{'多出' if sv['extra'] >= 0 else '少了'} {abs(sv['extra']):.2f} 點（{z:+.1f} 個標準差）——{tail}",
                    "en": f"S&P {sv['spx_chg']:+.2f}% implies {sv['expected']:+.2f} VIX pts; actual {pts:+.2f} ({z:+.1f} s.d.)."})
    eq = {x["t"]: x for x in r.get("equity", [])}
    s, n, sx = eq.get("^GSPC"), eq.get("^NDX"), eq.get("^SOX")
    if s and s["chg"] < 0 and (sx or n):
        worst = min([x for x in (n, sx) if x], key=lambda x: x["chg"])
        if worst["chg"] <= 2 * s["chg"]:
            out.append({"lv": "watch", "zh": f"跌勢集中在科技：{worst['zh']} {worst['chg']:+.2f}%" + (f"（{worst['sigma']:+.1f}σ）" if worst.get("sigma") is not None else "")
                                             + f"，是標普（{s['chg']:+.2f}%）的 {worst['chg'] / s['chg']:.1f} 倍。",
                        "en": f"Selling concentrated in tech: {worst['en']} {worst['chg']:+.2f}% vs S&P {s['chg']:+.2f}%."})
    cr = {x["t"]: x for x in r.get("cross", [])}
    y = cr.get("^TNX")
    if s and s["chg"] <= -0.5 and y and y.get("bp") is not None:
        if y["bp"] <= -5:
            out.append({"lv": "info", "zh": f"10 年期殖利率同時下降 {abs(y['bp']):.0f}bp：股跌債漲，資金轉進公債避險，這次的波動不是利率推升造成的。",
                        "en": f"Yields fell {y['bp']:.0f}bp: a flight to bonds, not a rates shock."})
        elif y["bp"] >= 5:
            out.append({"lv": "watch", "zh": f"10 年期殖利率同時上升 {y['bp']:.0f}bp：股債同跌，利率是壓力來源之一。",
                        "en": f"Yields rose {y['bp']:.0f}bp with stocks down: rates are part of the pressure."})
    h = cr.get("HYG")
    if h and h.get("sigma") is not None and h["sigma"] <= -2:
        out.append({"lv": "alert", "zh": f"高收益債同步重挫（{h['chg']:+.2f}%，{h['sigma']:+.1f}σ）：信用市場也在確認風險。",
                    "en": "High yield bonds confirm the stress."})
    if r.get("r3m") is not None:
        if r["r3m"] > 1:
            out.append({"lv": "alert", "zh": f"VIX 期限結構倒掛（VIX ÷ VIX3M = {r['r3m']:.2f}）：近月的恐慌高於三個月後，市場在為「立即」的風險付費。",
                        "en": f"VIX term structure inverted ({r['r3m']:.2f})."})
        elif r.get("r9d") is not None and r["r9d"] >= 1.05:
            out.append({"lv": "watch", "zh": f"9 天期 VIX 高於 VIX（{r['r9d']:.2f} 倍）：最擔心的是接下來幾天；但 VIX 仍低於 3 個月期（{r['r3m']:.2f}），還沒倒掛。",
                        "en": "Short-dated fear is highest; the 1-3 month curve is not inverted yet."})
        else:
            out.append({"lv": "info", "zh": f"期限結構沒有倒掛（VIX ÷ VIX3M = {r['r3m']:.2f}，倒掛要大於 1）。",
                        "en": f"Term structure not inverted ({r['r3m']:.2f})."})
    g = r.get("gamma")
    if g and g["below"]:
        out.append({"lv": "watch", "zh": f"標普 {g['spot']:,.0f} 在 Gamma 翻轉點 {g['flip']:,.0f} 之下：造市商的避險動作傾向放大波動。",
                    "en": f"SPX below zero gamma ({g['flip']:,.0f})."})
    for ln in r.get("lines", []):
        if ln["verdict"] == "warn":
            stat = f"回測：之後 20 日內再跌 5% 的機率 {ln['dd5']:.0f}%（任何一天是 {ln['base_dd5']:.0f}%）" if ln.get("dd5") is not None and ln.get("base_dd5") is not None else ""
            out.append({"lv": "alert" if ln["hit"] else "info",
                        "zh": (f"VIX 已在 {ln['line']:.0f} 以上。" if ln["hit"] else f"離有預警力的 VIX {ln['line']:.0f} 還差 {ln['dist']:.1f} 點。") + stat,
                        "en": f"VIX {ln['line']:.0f} line: " + ("crossed." if ln["hit"] else f"{ln['dist']:.1f} pts away.")})
            break
    order = {"alert": 0, "watch": 1, "info": 2}
    return sorted(out, key=lambda x: order[x["lv"]])


def watchlist(r: Dict) -> List[Dict]:
    """What would make it worse / calmer, with the status now (conditions, not advice)."""
    out: List[Dict] = []
    for ln in r.get("lines", []):
        tail = f"（回測：20 日內再跌 5% 機率 {ln['dd5']:.0f}%，任何一天 {ln['base_dd5']:.0f}%）" if ln.get("dd5") is not None and ln.get("base_dd5") is not None else ""
        out.append({"side": "up", "zh": f"VIX 升破 {ln['line']:.0f}" + tail, "now": f"{r['vix']:.2f}", "on": ln["hit"]})
    if r.get("r3m") is not None:
        out.append({"side": "up", "zh": "期限結構倒掛（VIX ÷ VIX3M > 1）", "now": f"{r['r3m']:.2f}", "on": r["r3m"] > 1})
    if r.get("move") is not None:
        out.append({"side": "up", "zh": "MOVE 美債波動率 > 125（債市也恐慌）", "now": f"{r['move']:.1f}", "on": r["move"] > 125})
    h = next((x for x in r.get("cross", []) if x["t"] == "HYG"), None)
    if h and h.get("sigma") is not None:
        out.append({"side": "up", "zh": "高收益債單日跌超過 2σ（信用確認）", "now": f"{h['sigma']:+.1f}σ", "on": h["sigma"] <= -2})
    g = r.get("gamma")
    if g:
        out.append({"side": "down", "zh": f"標普收復 Gamma 翻轉點 {g['flip']:,.0f}", "now": f"{g['spot']:,.0f}", "on": not g["below"]})
    if r.get("r9d") is not None:
        out.append({"side": "down", "zh": "9 天期 VIX 回到 VIX 之下（短線恐慌退潮）", "now": f"{r['r9d']:.2f}", "on": r["r9d"] < 1})
    if r.get("avg20") is not None:
        out.append({"side": "down", "zh": f"VIX 回到 20 日均值 {r['avg20']:.1f} 以下", "now": f"{r['vix']:.2f}", "on": r["vix"] <= r["avg20"]})
    return out
