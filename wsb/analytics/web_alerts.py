"""網頁警示 — the public subset of the Discord alert rules, evaluated at each site build.

The site has no server-side memory, so each item carries a stable key (rule + bar date / week); the browser remembers
which keys it has already shown (localStorage) and pops up only the new ones.  Holdings-based rules (portfolio drawdown,
stops, the personal rulebook, concentration) are never evaluated here — they stay in the private Discord DM.

lv "alert" = pop-up (+ desktop notification if the viewer allowed it); "watch" = listed under the bell only.
Every rule is a fixed threshold on model data (news headlines are not an input).  Descriptive, not a forecast."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

import numpy as np

from ..config import SETTINGS


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
        out.append({"key": f"sigma:{t}:{x['asof']}:{int(np.sign(sg))}", "lv": "alert", "tab": "markets",
                    "zh": f"異常波動：{names.get(t, t)} {mv}（{sg:+.1f}σ）", "en": f"Unusual move: {t} {mv} ({sg:+.1f}σ)",
                    "detail": f"單日變動是自己近 60 日波動的 {abs(sg):.1f} 倍"})
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


def build(eng) -> Dict:
    now = datetime.now(timezone.utc)
    out: List[Dict] = []
    for f in (lambda: _danger(eng, out), lambda: _stress(eng, out, now), lambda: _vol(eng, out, now), lambda: _models(eng, out, now), lambda: _bottom(eng, out, now),
              lambda: _stability(eng, out, now)):
        try:
            f()
        except Exception:  # noqa: BLE001  (one broken rule must not hide the others)
            pass
    out.sort(key=lambda x: 0 if x["lv"] == "alert" else 1)
    return {"ts": int(now.timestamp()), "items": out}
