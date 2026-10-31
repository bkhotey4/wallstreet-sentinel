"""網頁警示 — the public subset of the Discord alert rules, evaluated at each site build.

The site has no server-side memory, so each item carries a stable key (rule + bar date / week); the browser remembers
which keys it has already shown (localStorage) and pops up only the new ones.  Holdings-based rules (portfolio drawdown,
stops, the personal rulebook, concentration) are never evaluated here — they stay in the private Discord DM.

lv "alert" = pop-up (+ desktop notification if the viewer allowed it); "watch" = listed under the bell only.
tone (colour on the page): "risk" red, "good" green (a big move in the healthy direction), "watch" yellow (worth watching,
e.g. oversold), "regime" blue (the market backdrop turning healthier).  Only risk items pop up; good news is shown in the
bell and the top ribbon so the page is not silent on rallies.
Every rule is a fixed threshold on model data (news headlines are not an input).  Descriptive, not a forecast."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS


# which direction is the stress for a market (default: a fall) — same idea as the live layer (tools/site_live.py)
BAD_UP = ("^VIX", "^VIX3M", "^TNX", "^TYX", "^FVX", "^IRX", "DX-Y.NYB", "TWD=X", "BZ=F", "CL=F")
NEUTRAL = ("GC=F", "JPY=X")


def _week(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}W{w:02d}"


def _danger(eng, out: List[Dict]) -> None:
    from . import danger as DG
    if not SETTINGS.get("danger", {}).get("enabled", True):
        return
    q = eng.market.q
    vix, v3 = q("^VIX"), q("^VIX3M")
    back = bool(vix and v3 and vix.get("price") and v3.get("price") and vix["price"] > v3["price"] and vix.get("asof") == v3.get("asof"))
    for mkt in ("us", "tw"):
        day = DG.in_session(mkt, q)
        if not day:
            continue
        r = DG.score(mkt, q, vix_backwardation=back, day=day)
        if r["level"] < 1:
            continue
        trig = "、".join(f"{h['label']} {h['chg']:+.2f}%" if h["chg"] is not None else h["label"] for h in r["hits"][:5])
        out.append({"key": f"danger:{mkt}:{day}:{r['level']}", "lv": "alert" if r["level"] >= 2 else "watch", "tab": "overview",
                    "zh": f"{r['zh']}盤中危險訊號［{r['name']}］大盤 {r['bench_chg']:+.2f}%（{r['points']} 分）",
                    "en": f"{r['market'].upper()} intraday danger [{r['level']}]: benchmark {r['bench_chg']:+.2f}%",
                    "detail": f"觸發：{trig}。{r['nature']}（免費報價約延遲 15 分鐘）"})


def _stress(eng, out: List[Dict], now: datetime) -> None:
    st = getattr(eng, "stress", None)
    if not st or st.score is None:
        return
    levels = SETTINGS.get("stress_levels", [])
    idx = next((i for i, lv in enumerate(levels) if st.score < lv["max"]), len(levels) - 1)
    if idx >= 2:
        drv = "、".join(f"{c.id}（{c.score:.0f}）" for c in st.drivers(4))
        out.append({"key": f"ssi:{idx}:{_week(now)}", "lv": "alert", "tab": "risk",
                    "zh": f"系統性壓力 {st.emoji} {st.label}（SSI {st.score:.1f}）", "en": f"Systemic stress {st.label} (SSI {st.score:.1f})",
                    "detail": f"主要推升：{drv}"})
    jump = float(SETTINGS.get("alerts", {}).get("stress_jump_points", 8))
    if st.chg_1d is not None and st.chg_1d >= jump:
        bar = st.history.index[-1].strftime("%Y%m%d") if len(st.history) else "na"
        out.append({"key": f"ssi_jump:{bar}", "lv": "alert", "tab": "risk",
                    "zh": f"SSI 單日跳升 {st.chg_1d:+.1f} 點 → {st.score:.1f}", "en": f"SSI jumped {st.chg_1d:+.1f} pts",
                    "detail": "區塊：" + "、".join(f"{k} {v:.0f}" for k, v in sorted(st.blocks.items(), key=lambda x: -x[1])[:4])})


def _vol(eng, out: List[Dict], now: datetime) -> None:
    q = eng.market.q
    vix, v3 = q("^VIX"), q("^VIX3M")
    if vix and v3 and vix.get("price") and v3.get("price") and vix["price"] > v3["price"] and vix.get("asof") == v3.get("asof"):
        out.append({"key": f"vix_back:{vix.get('asof')}", "lv": "alert", "tab": "mood",
                    "zh": f"VIX 期限結構倒掛：VIX {vix['price']:.2f} > VIX3M {v3['price']:.2f}", "en": "VIX term structure inverted",
                    "detail": "近月恐慌高於遠月：市場在為「立即」的尾部風險付費。"})
    a = SETTINGS.get("alerts", {}) or {}
    thr = float(a.get("sigma_move", 3.0))
    names = SETTINGS.names()
    cut = (now - timedelta(days=4)).strftime("%Y-%m-%d")
    for t in a.get("key_assets", []):
        sg, x = eng.market.sigma_move(t), q(t)
        if sg is None or not x or x.get("chg_pct") is None or abs(sg) < thr or str(x.get("asof", "")) < cut:
            continue
        if not (x["chg_pct"] == x["chg_pct"]) or np.sign(sg) != np.sign(x["chg_pct"]):
            continue                                       # quote and history disagree → data glitch
        hs = eng.market.series(t).dropna()
        if len(hs) and str(x["asof"])[:10] < hs.index[-1].strftime("%Y-%m-%d"):
            continue                                       # stale quote: σ would be the newer history bar's move, the % the quote's
        mv = f"{x['chg_pct']:+.2f}%"
        if t in ("^TNX", "^TYX", "^FVX", "^IRX"):
            from .vix_explain import _bp
            b_ = _bp(x)
            mv = f"{b_:+.0f}bp" if b_ is not None else mv
        bad = t not in NEUTRAL and ((sg > 0) if t in BAD_UP else (sg < 0))
        good = t not in NEUTRAL and not bad
        lab = "大幅變動（好的方向）" if good else "異常波動"
        out.append({"key": f"sigma:{t}:{x['asof']}:{int(np.sign(sg))}", "lv": "watch" if good else "alert", "tab": "markets",
                    "tone": "good" if good else "risk" if bad else "watch",
                    "zh": f"{lab}：{names.get(t, t)} {mv}（{sg:+.1f}σ）",
                    "en": f"{'Big move (healthy direction)' if good else 'Unusual move'}: {t} {mv} ({sg:+.1f}σ)",
                    "detail": f"單日變動是自己近 60 日波動的 {abs(sg):.1f} 倍" + ("；往好的方向，不是警示" if good else "")})
    op = getattr(getattr(eng, "options", None), "spx", None) or {}
    if op.get("zero_gamma") and op.get("spot") and op["spot"] < op["zero_gamma"]:
        out.append({"key": f"gamma:{now:%Y%m%d}", "lv": "watch", "tab": "flows",
                    "zh": f"標普 {op['spot']:,.0f} 在 Gamma 翻轉點 {op['zero_gamma']:,.0f} 之下", "en": "SPX below zero gamma",
                    "detail": "造市商避險傾向放大波動"})


def _models(eng, out: List[Dict], now: datetime) -> None:
    for r in (getattr(eng, "canary", None) or {}).get("rows", []):
        if r.get("state") == "alert":
            out.append({"key": f"canary:{r['id']}:{r.get('asof') or 'na'}", "lv": "alert", "tab": "risk",
                        "zh": f"🐤 金絲雀紅燈：{r['zh']}", "en": f"Canary red: {r.get('en') or r['id']}",
                        "detail": (r.get("value_txt") or "") + ("｜" + (r.get("rule") or r.get("why") or ""))[:240]})
    pb = getattr(eng, "playbook", None) or {}
    if pb.get("stage") is not None and pb["stage"] >= 2:
        out.append({"key": f"playbook:{pb['stage']}:{_week(now)}", "lv": "alert" if pb["stage"] >= 3 else "watch", "tab": "risk",
                    "zh": f"風險劇本 {pb.get('emoji', '')} {pb.get('name', '')}（風險分 {pb.get('points')}）", "en": f"Risk playbook stage {pb['stage']}",
                    "detail": "；".join(w for _, w in (pb.get("why") or []))[:240]})
    for h in (getattr(eng, "odds", None) or {}).get("horizons", []):
        lift, p = h.get("lift_adj"), h.get("adjusted")
        if lift is None or p is None or lift < 1.5:
            continue
        out.append({"key": f"odds:{h['days']}:{int(lift * 2) / 2}:{now:%Y%m%d}", "lv": "alert" if lift >= 2 else "watch", "tab": "overview",
                    "zh": f"{h['days']} 個交易日內跌 ≥{h['drawdown_pct']:.0f}% 的機率 {p:.1f}%，是平常的 {lift:.1f} 倍",
                    "en": f"{h['days']}-day ≥{h['drawdown_pct']:.0f}% drop odds {p:.1f}% ({lift:.1f}× normal)",
                    "detail": f"平常 {h['base_rate']:.1f}%；歷史頻率，不是預測"})
    rules = (getattr(eng, "sx", None) or {}).get("rules") or {}
    base = (rules.get("base") or {}).get("dd5")
    for r in rules.get("rows", []):
        base = r.get("base_dd5", (rules.get("base") or {}).get("dd5"))     # same years as the rule's own events
        if r.get("verdict") == "warn" and r.get("now"):
            out.append({"key": f"rule:{r['k']}:{r.get('last')}", "lv": "alert", "tab": "mood",
                        "zh": f"有預警力的規則觸發：{r['zh']}", "en": f"Back-tested warning rule fired: {r['en']}",
                        "detail": f"回測：之後 20 日內再跌 5% 的機率 {r['dd5']:.0f}%（同期間任何一天 {base:.0f}%），{r.get('since', '')} 年起共 {r['n']} 次" if base is not None and r.get("dd5") is not None else ""})


def _bottom(eng, out: List[Dict], now: datetime) -> None:
    """抄底四訊號: 3 of 4 → pop-up; 2 of 4 → listed under the bell."""
    from . import bottom as BT
    r = BT.build(eng, today=now.date())           # judged against the alert clock, not the wall clock
    if not r.get("available") or r["n_hit"] < 2:
        return
    hit = "、".join(f"{s['zh']} {s['fmt'].format(s['v'])}" for s in r["signals"] if s["hit"])
    out.append({"key": f"bottom:{r['n_hit']}:{_week(now)}", "lv": "alert" if r["n_hit"] >= 3 else "watch", "tab": "mood",
                "zh": f"抄底四訊號 {r['n_hit']}/4 成立：{hit}", "en": f"Bottom checklist {r['n_hit']}/4",
                "detail": "極端恐慌的歷史統計，不是投資建議；訊號出現後市場常會再跌一段"})


def _stability(eng, out: List[Dict], now: datetime) -> None:
    """金融穩定監測: short-term funding (SOFR vs reserve rate), Treasury refunding wording, the basis trade, AI capex —
    the same events the Discord bot sends, now under the bell too (monthly coverage audit left to its own page)."""
    from ..data import stability as ST
    v = getattr(eng, "_stability_view", None) or ST.view(eng)
    for key, sev, title, detail in ST.alerts(v, now.strftime("%Y-%m-%d")):
        if key.startswith("stab:cover:"):
            continue
        out.append({"key": key, "lv": "alert" if "WARNING" in sev else "watch", "tab": "stability",
                    "zh": f"🏦 {title}", "en": title, "detail": (detail or "")[:240]})


def _momentum(eng, out: List[Dict], now: datetime) -> None:
    """強勢上漲: a main index up >= 2x its own normal daily move (one-year std), or a heavyweight up >= 2.5x with >= 1.5x
    volume.  The 3-sigma moves are already in _vol; this adds the 2-sigma rallies so the page is not silent when markets surge."""
    q = eng.market.q
    names = SETTINGS.names()
    cut = (now - timedelta(days=4)).strftime("%Y-%m-%d")
    have = {x["key"].rsplit(":", 2)[0] for x in out if x["key"].startswith("sigma:")}
    idx = ("^GSPC", "^NDX", "^SOX", "^TWII")
    heavy = ("NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO", "TSM", "2330.TW")
    for t in idx + heavy:
        x, h = q(t), eng.market.series(t).dropna()
        if not x or x.get("chg_pct") is None or str(x.get("asof", "")) < cut or len(h) < 260 or f"sigma:{t}" in have:
            continue
        r = h[h > 0].pct_change().dropna().iloc[-253:-1] * 100
        sd = float(r.std()) if len(r) > 120 else None
        if not sd:
            continue
        z = x["chg_pct"] / sd
        if z < (2.0 if t in idx else 2.5):
            continue
        vx = None
        if t in heavy:
            try:
                v = eng.stockprices.vol(t).dropna()            # the stock universe keeps daily volume
                base = float(v.iloc[-51:-1].mean()) if len(v) > 51 else 0.0
                vx = float(v.iloc[-1]) / base if base > 0 else None
            except Exception:  # noqa: BLE001
                vx = None
            if vx is None or vx < 1.5:
                continue
        nm = names.get(t, t)
        tail = f"，成交量 {vx:.1f} 倍）" if vx else "）"
        out.append({"key": f"mom:{t}:{x['asof']}", "lv": "watch", "tone": "good", "tab": "premarket" if t in idx else "signals",
                    "zh": f"強勢上漲：{nm} {x['chg_pct']:+.2f}%（平常單日波動的 {z:.1f} 倍" + tail,
                    "en": f"Strong rally: {t} {x['chg_pct']:+.2f}% ({z:.1f}x normal)",
                    "detail": "和自己過去一年的平常漲跌比；大漲常伴隨空單回補，隔天不一定延續。描述現象，不是買賣建議。"})


def _regime(eng, out: List[Dict], now: datetime) -> None:
    """多頭環境轉好 (blue): at least 4 of the healthy-market checks hold and breadth (share above the 200-day) >= 60 %."""
    from .entry_env import bull_env
    rows = [r for r in bull_env(eng) if r.get("ok") is not None]
    ok = [r for r in rows if r["ok"]]
    br = (((getattr(eng, "rotation", None) or {}).get("breadth") or {}).get("us") or {}).get("now")
    if len(rows) >= 5 and len(ok) >= 4 and br is not None and br >= 60:
        names = "、".join(r["zh"].split("：")[0].split("（")[0] for r in ok[:6])
        out.append({"key": f"regime:{len(ok)}:{_week(now)}", "lv": "watch", "tone": "regime", "tab": "entry",
                    "zh": f"多頭環境轉好：健康檢查 {len(ok)}/{len(rows)} 項成立，{br:.0f}% 股票站上 200 日線",
                    "en": f"Healthier backdrop: {len(ok)}/{len(rows)} checks, breadth {br:.0f}%",
                    "detail": f"成立：{names}。環境描述，不保證接下來會漲。"})


def _dip(eng, out: List[Dict], now: datetime) -> None:
    """兩段式超跌觀察 (instead of waiting for VIX 40): (1) 超跌 — S&P RSI(14) < 30 or a 5-day fall >= 2x its normal 5-day
    move; (2) 恐慌退潮 — within 5 sessions of (1), VIX >= 10 % below its 5-day high and the S&P up on the day."""
    from .signals import rsi_series
    spx, vix = eng.market.series("^GSPC").dropna(), eng.market.series("^VIX").dropna()
    if len(spx) < 300 or len(vix) < 10:
        return
    rsi = rsi_series(spx)
    r5 = (spx / spx.shift(5) - 1) * 100
    sd5 = float(r5.iloc[-1000:-6].std())
    deep = (rsi < 30) | (r5 <= -2 * sd5)
    if bool(deep.iloc[-1]):
        out.append({"key": f"dip1:{spx.index[-1]:%Y%m%d}", "lv": "watch", "tone": "watch", "tab": "mood",
                    "zh": f"超跌觀察：標普 RSI {rsi.iloc[-1]:.0f}、5 日 {r5.iloc[-1]:+.1f}%（平常 5 日波動 ±{sd5:.1f}%）",
                    "en": "Oversold watch: S&P RSI / 5-day drop",
                    "detail": "第一段：跌得比平常深。歷史上超跌後常再震盪，第二段「恐慌退潮」出現前不代表止跌。"})
    elif bool(deep.iloc[-6:-1].any()):
        hi5 = float(vix.iloc[-6:].max())
        if vix.iloc[-1] <= hi5 * 0.9 and spx.iloc[-1] > spx.iloc[-2]:
            out.append({"key": f"dip2:{spx.index[-1]:%Y%m%d}", "lv": "watch", "tone": "good", "tab": "mood",
                        "zh": f"恐慌退潮觀察：VIX 從 5 日高點 {hi5:.1f} 回落到 {vix.iloc[-1]:.1f}（{(vix.iloc[-1] / hi5 - 1) * 100:+.0f}%），標普收漲",
                        "en": "Fear receding after an oversold stretch",
                        "detail": "第二段：超跌後恐慌開始退。不代表已經見底，之後仍可能再測低點。"})


def _patterns(eng, out: List[Dict], now: datetime) -> None:
    """型態成立 (green, at most 3 a day across markets): the strongest new 技術型態觀察 rows of tier A with strength >= 65.
    The key carries the date the pattern first appeared, so the same stock and pattern shows once, not every day."""
    sg = getattr(eng, "signals", None) or {}
    rows = []
    for mk in (sg.get("markets") or {}).values():
        for r in mk.get("rows") or []:
            if r.get("tier") == "A" and (r.get("strength") or 0) >= 65 and r.get("new") and r.get("patterns"):
                rows.append(r)
    for r in sorted(rows, key=lambda r: -r["strength"])[:3]:
        p = r["patterns"][0]
        inv = f"，失效線 {r['inv']:.2f}" if r.get("inv") else ""
        out.append({"key": f"pat:{r['sym']}:{p['pattern']}:{r.get('since')}", "lv": "watch", "tone": "good", "tab": "signals",
                    "zh": f"型態成立：{r['name']}（{r['code']}）{p['label']}，強度 {r['strength']:.0f}{inv}",
                    "en": f"Pattern: {r.get('name_en') or r['sym']} {p.get('label_en', '')}",
                    "detail": "規則篩選出的技術型態，收盤跌破失效線代表型態失敗；歷史成績看「技術型態觀察」頁。描述型態，不是買賣建議。"})


def rate_pressure(tnx, ndx) -> Optional[Dict]:
    """10 年債利率壓力: the 20-day change of the 10-year yield against its own 3-year spread of 20-day changes, whether
    it just made a 60-day high/low, and how much the Nasdaq-100 has moved per 10 bp over the past year (measured, so no
    fixed 4.5 % / 4.8 % lines)."""
    y = tnx.dropna()
    if len(y) < 800:
        return None
    c20 = (y - y.shift(20)) * 100                                  # bp
    sd = float(c20.iloc[-756:-1].std())
    if not sd:
        return None
    now, chg = float(y.iloc[-1]), float(c20.iloc[-1])
    prior = y.iloc[-61:-1]
    out = {"y": now, "chg20": chg, "sd": sd, "z": chg / sd, "asof": y.index[-1].strftime("%Y-%m-%d"),
           "hi60": now > float(prior.max()), "lo60": now < float(prior.min()),
           "pct10y": float((y.iloc[-2520:] < now).mean() * 100),
           "yrs": round((y.index[-1] - y.iloc[-2520:].index[0]).days / 365.25)}
    n = ndx.dropna()
    j = pd.concat([n.pct_change() * 100, y.diff() * 100], axis=1, join="inner").dropna().iloc[-252:]
    if len(j) > 150 and float(j.iloc[:, 1].var()) > 0:
        b = float(np.cov(j.iloc[:, 0], j.iloc[:, 1])[0, 1] / j.iloc[:, 1].var())
        out["ndx_per10"] = b * 10
        out["r"] = float(j.corr().iloc[0, 1])
    return out


def _rates(eng, out: List[Dict], now: datetime) -> None:
    """利率壓力減輕 (green) / 升高 (yellow): a 20-day yield move >= 1.5x its normal size that also sets a 60-day low/high."""
    r = rate_pressure(eng.market.series("^TNX"), eng.market.series("^NDX"))
    if not r:
        return
    sens = ""
    if r.get("ndx_per10") is not None:
        sens = f"過去一年 10 年債每升 10bp，那指同日平均 {r['ndx_per10']:+.2f}%（相關係數 {r['r']:.2f}）。"
    lvl = f"目前 {r['y']:.2f}%，高於過去 {r['yrs']} 年 {r['pct10y']:.0f}% 的日子"
    if r["z"] <= -1.5 and r["lo60"]:
        out.append({"key": f"rate:dn:{r['asof']}", "lv": "watch", "tone": "good", "tab": "bonds",
                    "zh": f"利率壓力減輕：10 年債 20 天降 {abs(r['chg20']):.0f}bp（平常 ±{r['sd']:.0f}bp），創 60 天新低",
                    "en": f"10Y yield down {abs(r['chg20']):.0f}bp in 20 days, 60-day low",
                    "detail": f"{lvl}。{sens}利率下來對估值高的成長股壓力較小，但若是因為景氣轉差而降，股市不一定漲。描述現象，不是買賣建議。"})
    elif r["z"] >= 1.5 and r["hi60"]:
        out.append({"key": f"rate:up:{r['asof']}", "lv": "watch", "tone": "watch", "tab": "bonds",
                    "zh": f"利率壓力升高：10 年債 20 天升 {r['chg20']:.0f}bp（平常 ±{r['sd']:.0f}bp），創 60 天新高",
                    "en": f"10Y yield up {r['chg20']:.0f}bp in 20 days, 60-day high",
                    "detail": f"{lvl}。{sens}利率上升時，還沒賺錢、靠未來成長撐估值的股票通常受壓較大。描述現象，不是買賣建議。"})


def build(eng) -> Dict:
    now = datetime.now(timezone.utc)
    out: List[Dict] = []
    for f in (lambda: _danger(eng, out), lambda: _stress(eng, out, now), lambda: _vol(eng, out, now), lambda: _models(eng, out, now), lambda: _bottom(eng, out, now),
              lambda: _stability(eng, out, now), lambda: _momentum(eng, out, now), lambda: _regime(eng, out, now),
              lambda: _dip(eng, out, now), lambda: _patterns(eng, out, now), lambda: _rates(eng, out, now)):
        try:
            f()
        except Exception:  # noqa: BLE001  (one broken rule must not hide the others)
            pass
    for x in out:
        x.setdefault("tone", "risk" if x["lv"] == "alert" else "watch")
    order = {"risk": 0, "watch": 1, "good": 2, "regime": 3}
    out.sort(key=lambda x: (0 if x["lv"] == "alert" else 1, order.get(x["tone"], 1)))
    return {"ts": int(now.timestamp()), "items": out}
