"""盤中大盤危險訊號 — intraday market-danger detector for the US and Taiwan regular sessions.

A single index print is not "danger".  This scores several INDEPENDENT groups at once — equities, volatility, credit,
banks, breadth and FX/carry — and only calls it systemic when at least three groups move together.
Levels: 1 注意 / 2 警戒 / 3 危險.  Pure functions (quotes in, verdict out) so the rules are testable; thresholds live in
settings.yaml → danger.  Free quotes are delayed ~15 minutes, which the alert text says."""
from __future__ import annotations

from datetime import datetime, time as dtime
from typing import Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

from ..config import SETTINGS

CFG = SETTINGS.get("danger", {}) or {}
LEVEL_NAMES = {1: "注意", 2: "警戒", 3: "危險"}

# (ticker, label, group, direction, [(threshold, points), ...])  direction −1: falling is bad, +1: rising is bad
US_RULES = [
    ("^GSPC", "標普500", "股市", -1, [(-1.0, 1), (-1.75, 2), (-2.5, 3), (-3.5, 4)]),
    ("^NDX", "那斯達克100", "股市", -1, [(-1.5, 1), (-2.5, 2), (-4.0, 3)]),
    ("^SOX", "費城半導體", "股市", -1, [(-3.0, 1), (-5.0, 2)]),
    ("RSP", "等權重標普", "市場寬度", -1, [(-1.5, 1), (-2.5, 2)]),
    ("^VIX", "VIX 恐慌指數", "波動率", +1, [(10.0, 1), (20.0, 2), (35.0, 3)]),
    ("HYG", "高收益債", "信用", -1, [(-0.4, 1), (-0.8, 2)]),
    ("KRE", "區域銀行", "信用", -1, [(-3.0, 1), (-5.0, 2)]),
    ("JPY=X", "美元兌日圓", "匯率套息", -1, [(-1.0, 1), (-2.0, 2)]),          # yen strength = carry unwind
]
TW_RULES = [
    ("^TWII", "台灣加權", "股市", -1, [(-1.2, 1), (-2.0, 2), (-3.0, 3), (-4.5, 4)]),
    ("2330.TW", "台積電", "股市", -1, [(-2.0, 1), (-3.5, 2)]),
    ("TWD=X", "美元兌台幣", "匯率套息", +1, [(0.5, 1), (1.0, 2)]),          # TWD weakness = foreign outflow
    ("^N225", "日經225", "區域股市", -1, [(-2.0, 1), (-3.5, 2)]),
    ("^KS11", "韓國KOSPI", "區域股市", -1, [(-2.0, 1), (-3.5, 2)]),
]
MARKETS = {
    "us": {"zh": "美股", "tz": "America/New_York", "open": dtime(9, 30), "close": dtime(16, 0), "anchor": "^GSPC",
           "rules": US_RULES, "gate": ("^GSPC", -0.8)},
    "tw": {"zh": "台股", "tz": "Asia/Taipei", "open": dtime(9, 0), "close": dtime(13, 30), "anchor": "^TWII",
           "rules": TW_RULES, "gate": ("^TWII", -1.0)},
}


def in_session(mkt: str, q: Callable[[str], Optional[dict]], now: Optional[datetime] = None) -> Optional[str]:
    """The session date (YYYY-MM-DD) if the market is in its regular session AND today's bar exists
    (holidays have no fresh bar), else None."""
    m = MARKETS[mkt]
    loc = (now or datetime.now(ZoneInfo("UTC"))).astimezone(ZoneInfo(m["tz"]))
    if loc.weekday() >= 5 or not (m["open"] <= loc.time() < m["close"]):
        return None
    a = q(m["anchor"]) or {}
    today = loc.strftime("%Y-%m-%d")
    return today if a.get("asof") == today else None


def score(mkt: str, q: Callable[[str], Optional[dict]], vix_backwardation: bool = False) -> Dict:
    m = MARKETS[mkt]
    rules = CFG.get(f"{mkt}_rules") or m["rules"]
    hits, groups, pts = [], {}, 0
    for t, label, grp, direction, steps in rules:
        x = (q(t) or {}).get("chg_pct")
        if x is None or x != x:
            continue
        p = 0
        for th, pp in steps:
            if (direction < 0 and x <= th) or (direction > 0 and x >= th):
                p = pp
        if p:
            pts += p
            groups[grp] = groups.get(grp, 0) + p
            hits.append({"ticker": t, "label": label, "group": grp, "chg": float(x), "pts": p})
    if mkt == "us" and vix_backwardation:
        pts += 1
        groups["波動率"] = groups.get("波動率", 0) + 1
        hits.append({"ticker": "^VIX/^VIX3M", "label": "VIX 期限結構倒掛", "group": "波動率", "chg": None, "pts": 1})
    gate_t, gate_th = m["gate"]
    g = (q(gate_t) or {}).get("chg_pct")
    gated = g is not None and g <= gate_th                # "大盤危險" needs the benchmark itself to be down
    th = CFG.get("level_points", [3, 6, 9])
    lvl = 0
    if gated:
        lvl = 3 if pts >= th[2] else 2 if pts >= th[1] else 1 if pts >= th[0] else 0
        crash_th = float((CFG.get("crash_pct") or {"us": -4.0, "tw": -5.0}).get(mkt, -4.0))
        if g <= crash_th:
            lvl = 3
    eq_like = {"股市", "區域股市", "市場寬度"}
    non_eq = [k for k in groups if k not in eq_like]
    systemic = len(groups) >= 3 and len(non_eq) >= 2
    return {"market": mkt, "zh": m["zh"], "level": lvl, "name": LEVEL_NAMES.get(lvl, "—"), "points": pts,
            "groups": groups, "hits": sorted(hits, key=lambda h: -h["pts"]), "systemic": systemic,
            "bench_chg": g, "nature": ("系統性：股市、" + "、".join(non_eq) + " 同步惡化" if systemic else
                                       ("集中在股市（波動率／信用／匯率未明顯同步）" if not non_eq else
                                        "股市＋" + "、".join(non_eq) + "，尚未全面擴散"))}


def macro_context(engine) -> List[str]:
    """One-glance macro backdrop to attach to an intraday alert."""
    out = []
    o = getattr(engine, "outlook", None) or {}
    if o.get("available"):
        out.append(o["headline"])
        rec = next((h for h in o.get("horizons", []) if h["months"] == 12), None)
        if rec:
            out.append(f"12 個月衰退機率 {rec['prob']:.0f}%（紐約聯準會模型）")
    st = getattr(engine, "stress", None)
    if st is not None:
        out.append(f"系統性壓力 SSI {st.score:.0f}（{st.label}）")
    rg = getattr(engine, "regime", None) or {}
    if rg.get("quadrant"):
        out.append(f"總經象限：{rg['quadrant']}；{rg.get('liquidity_mode', '')}")
    itl = getattr(engine, "intel", None) or {}
    conf = [r["channel"] for r in itl.get("channels", []) if r.get("state") == "確認"]
    if conf:
        out.append("新聞＋價格已確認的衝擊路徑：" + "、".join(conf))
    return out
