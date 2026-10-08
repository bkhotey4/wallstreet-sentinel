"""Self-monitoring: (1) is the model itself healthy (data coverage, sources)?  (2) is the portfolio too concentrated?

Pure functions → easy to test.  They return plain tuples (key, severity, title, detail) so this module does
not depend on the Discord layer.  Keys that contain ':' are treated as one-shot by the alert runner
(a new date / ISO-week in the key means 'at most once per day / week while the condition persists')."""
from __future__ import annotations

import math
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from ..config import SETTINGS
from ..health import HEALTH

AlertTuple = Tuple[str, str, str, str]


# ---------------------------------------------------------------- model / data health
def health_status(stress, uptime_s: float) -> Dict:
    """Machine-readable health summary used by the alert rule and the control room."""
    cfg = SETTINGS.get("health", {})
    min_cov = float(cfg.get("min_coverage", 0.90))
    core = cfg.get("core_sources", ["yahoo_quotes", "yahoo_history", "fred", "cboe_spx"])
    out: Dict = {"coverage": None, "excluded": [], "bad_sources": [], "ok": True, "min_coverage": min_cov}
    if stress is not None:
        out["coverage"] = float(stress.coverage)
        out["excluded"] = [(c.id, c.status) for c in stress.components if c.score is None]
        if stress.coverage < min_cov:
            out["ok"] = False
    if uptime_s > float(cfg.get("grace_minutes", 15)) * 60:       # right after a restart sources are legitimately 'pending'
        for name in core:
            s = HEALTH.sources.get(name)
            if s is not None and s.state in ("stale", "down"):
                out["bad_sources"].append((name, s.state, s.error))
        if out["bad_sources"]:
            out["ok"] = False
    return out


def health_alerts(stress, uptime_s: float, today: Optional[date] = None) -> List[AlertTuple]:
    h = health_status(stress, uptime_s)
    day = (today or date.today()).strftime("%Y%m%d")
    out: List[AlertTuple] = []
    if h["coverage"] is not None and h["coverage"] < h["min_coverage"]:
        ex = "；".join(f"{i}（{s}）" for i, s in h["excluded"][:10]) or "—"
        out.append((f"health:coverage:{day}", "⚠️ WARNING",
                    f"模型資料涵蓋率偏低：{h['coverage'] * 100:.0f}%（門檻 {h['min_coverage'] * 100:.0f}%）",
                    f"以下因子沒有被計入壓力指數，分數可能失真：{ex}"))
    for name, state, err in h["bad_sources"]:
        out.append((f"health:src:{name}:{day}", "⚠️ WARNING", f"資料源異常：{name}（{state}）",
                    (err or "連續更新失敗") + "｜在這個狀態下相關分析可能過期，請用 /status 查看"))
    return out


# ---------------------------------------------------------------- concentration
def concentration(portfolio: Optional[Dict]) -> Dict:
    """Weights, risk shares and limit breaches for single names, themes and total beta."""
    cfg = SETTINGS.get("concentration", {})
    res: Dict = {"breaches": [], "themes": {}, "top": None}
    if not portfolio or portfolio.get("error") or not portfolio.get("total_value_usd"):
        return res
    V = float(portfolio["total_value_usd"])
    pos = [p for p in portfolio.get("positions", []) if p.get("value_usd")]
    max_w, max_r = float(cfg.get("max_weight_pct", 25)), float(cfg.get("max_risk_contrib_pct", 30))
    for p in sorted(pos, key=lambda x: -x["value_usd"]):
        w, r = p["weight"], p.get("risk_contrib_pct") or 0.0
        if res["top"] is None:
            res["top"] = {"sym": p["sym"], "weight": w, "risk": r}
        why = []
        if w > max_w:
            why.append(f"權重 {w:.1f}% > {max_w:.0f}%")
        if r > max_r:
            why.append(f"風險貢獻 {r:.1f}% > {max_r:.0f}%")
        if why:
            note = ""
            if w > max_w:                                          # sell x so that (Vp-x)/(V-x) = limit
                x = (p["value_usd"] - max_w / 100 * V) / (1 - max_w / 100)
                note = f"；降到 {max_w:.0f}% 約需減碼 ${x:,.0f}" + (f"（{math.ceil(x / (p['value_usd'] / p['shares']))} 股）" if p.get("shares") else "")
            res["breaches"].append({"kind": "single", "name": p["sym"], "text": "、".join(why) + note})
    for name, t in (cfg.get("themes") or {}).items():
        members = set(t.get("tickers", []))
        mem = [p for p in pos if p["sym"] in members]
        if not mem:
            continue
        T = sum(p["value_usd"] for p in mem)
        w = T / V * 100
        r = sum((p.get("risk_contrib_pct") or 0.0) for p in mem)
        res["themes"][name] = {"weight": w, "risk": r, "members": [p["sym"] for p in mem], "limit": float(t.get("max_weight_pct", 100))}
        lim = float(t.get("max_weight_pct", 100))
        if w > lim:
            x = (T - lim / 100 * V) / (1 - lim / 100)
            res["breaches"].append({"kind": "theme", "name": name,
                                    "text": f"{'＋'.join(p['sym'] for p in mem)} 合計權重 {w:.1f}% > {lim:.0f}%（風險占 {r:.0f}%）；降到上限約需減碼 ${x:,.0f}"})
    mb = float(cfg.get("max_beta", 1.5))
    beta = portfolio.get("beta")
    if beta is not None and beta > mb:
        res["breaches"].append({"kind": "beta", "name": "β",
                                "text": f"對標普 β {beta:.2f} > {mb:.2f}（大盤跌 10% 預估損失約 {beta * 10:.0f}%）；約需降低 {(1 - mb / beta) * 100:.0f}% 的大盤曝險"})
    return res


def concentration_alerts(portfolio: Optional[Dict], today: Optional[date] = None) -> List[AlertTuple]:
    c = concentration(portfolio)
    if not c["breaches"]:
        return []
    d = today or date.today()
    iso = d.isocalendar()
    lines = [f"• {b['name']}：{b['text']}" for b in c["breaches"]]
    return [(f"conc:{iso[0]}W{iso[1]:02d}", "⚠️ WARNING", f"持倉集中度超過上限（{len(c['breaches'])} 項）",
             "\n".join(lines) + "\n（上限可在 settings.yaml 的 concentration 調整；每週最多提醒一次）")]
