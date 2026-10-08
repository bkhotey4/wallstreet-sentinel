"""Sunday weekly review: what happened, how the bot's alerts performed, how the portfolio moved and why,
and what is coming next week.  Facts are computed deterministically; the AI only writes the commentary."""
from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np

from . import store
from .analytics import playbook as PB
from .analytics import scorecard as SC


def _chg(s, n: int) -> Optional[float]:
    s = s.dropna()
    return float(s.iloc[-1] / s.iloc[-1 - n] - 1) * 100 if len(s) > n else None


def facts(engine, sc: Optional[Dict] = None) -> Dict:
    m, st = engine.market, engine.stress
    out: Dict = {"asof": date.today().isoformat()}
    out["spx_week"] = _chg(m.series("^GSPC"), 5)
    out["ndx_week"] = _chg(m.series("^NDX"), 5)
    vix = m.series("^VIX")
    out["vix"] = float(vix.iloc[-1]) if len(vix) else None
    out["vix_chg"] = float(vix.iloc[-1] - vix.iloc[-6]) if len(vix) > 6 else None
    if st is not None:
        h = st.history.dropna()
        out["ssi"] = float(st.score)
        out["ssi_chg"] = float(st.score - h.iloc[-6]) if len(h) > 6 else None
        out["ssi_label"] = st.label
    pbk = engine.playbook or {}
    out["stage"] = pbk.get("name")
    out["stage_idx"] = pbk.get("stage")
    out["points"] = pbk.get("points")
    last = store.kv_get("weekly_last") or {}
    out["stage_prev"] = PB.STAGES[last["stage"]]["name"] if last.get("stage") is not None else None
    # alerts this week
    rows = store.alerts_since(168)
    risk = [r for r in rows if SC.family(r[1]) != "其他" and not r[1].startswith(("sigma:",))]
    out["alerts_total"] = len(rows)
    out["alerts_crit"] = sum(1 for r in rows if r[2].startswith("🚨"))
    out["alerts_top"] = [(r[2], r[3][:60]) for r in (risk or rows)[:6]]
    # portfolio attribution (5 sessions)
    pf = engine.portfolio or {}
    contrib: List[Dict] = []
    tot_ret = None
    if pf and not pf.get("error"):
        pos = [p for p in pf["positions"] if p.get("value_usd")]
        starts, rets = [], []
        for p in pos:
            r = _chg(m.series(p["sym"]), 5)
            if r is None:
                continue
            v0 = p["value_usd"] / (1 + r / 100)
            starts.append(v0)
            rets.append(r)
            contrib.append({"sym": p["sym"], "ret": r, "v0": v0})
        t0 = sum(starts)
        if t0 > 0:
            for c in contrib:
                c["contrib"] = c["ret"] * c["v0"] / t0
            tot_ret = sum(c["contrib"] for c in contrib)
        contrib.sort(key=lambda c: c.get("contrib", 0))
    out["pf_week"] = tot_ret
    out["pf_contrib"] = contrib
    out["pf_beta"] = pf.get("beta") if pf and not pf.get("error") else None
    # events next 8 days
    out["events"] = [e for e in engine.calendar.upcoming(8)]
    # rule report card
    out["families"] = (sc or {}).get("families", {})
    q = (getattr(engine, "shock", None) or {}).get("quality") or {}
    wf = [w for w in q.get("walk_forward", []) if w.get("n_test")]
    out["model_auc"] = [(w["days"], w.get("auc_oos")) for w in wf]
    return out


def facts_text(f: Dict) -> str:
    L = [f"## 本週回顧事實（{f['asof']}）",
         f"標普500 週 {f['spx_week']:+.1f}%" if f.get("spx_week") is not None else "標普週報酬 資料缺",
         f"VIX {f['vix']:.1f}（週變 {f['vix_chg']:+.1f}）" if f.get("vix") is not None and f.get("vix_chg") is not None else "",
         f"SSI {f['ssi']:.1f}（週變 {f['ssi_chg']:+.1f}）{f.get('ssi_label', '')}" if f.get("ssi") is not None and f.get("ssi_chg") is not None else "",
         f"風險階段：{f.get('stage')}（上週 {f.get('stage_prev') or '無紀錄'}）；風險分 {f.get('points')}",
         f"本週警報 {f['alerts_total']} 則（緊急 {f['alerts_crit']}）：" + "；".join(t for _, t in f["alerts_top"])]
    if f.get("pf_week") is not None:
        L.append(f"持倉週報酬約 {f['pf_week']:+.2f}%；貢獻最大：" + "、".join(f"{c['sym']} {c['contrib']:+.2f}%" for c in f["pf_contrib"][::-1][:3])
                 + "；拖累最大：" + "、".join(f"{c['sym']} {c['contrib']:+.2f}%" for c in f["pf_contrib"][:3]))
    if f["events"]:
        L.append("未來 8 天事件：" + "；".join(f"{e['date']} {e['event']}" for e in f["events"][:10]))
    for name, fm in f.get("families", {}).items():
        r = fm["by_horizon"].get(max(fm["by_horizon"])) if fm["by_horizon"] else None
        if r and r.get("episodes"):
            L.append(f"警報規則成績「{name}」：{r['episodes']} 次、命中 {r['hit_rate']:.0f}%（基準 {r['base_rate']:.0f}%）→ {fm['verdict']}")
    return "\n".join(x for x in L if x)
