"""Risk playbook + regime-break detection.

Deterministic on purpose: a stage is the sum of transparent points, so the user can see WHY the bot is at a stage
and which rule would move it.  Pure functions (no Discord / network) → unit-testable.

Stages: 0 正常 · 1 留意 · 2 戒備 · 3 防禦."""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

STAGES = [
    {"name": "正常", "emoji": "🟢", "thr": 0},
    {"name": "留意", "emoji": "🟡", "thr": 2},
    {"name": "戒備", "emoji": "🟠", "thr": 4},
    {"name": "防禦", "emoji": "🔴", "thr": 6},
]
BETA_FACTOR = [1.0, 1.0, 0.85, 0.65]          # target portfolio beta as a fraction of today's beta


def _cfg() -> Dict:
    return SETTINGS.get("playbook", {})


# ---------------------------------------------------------------- regime breaks (do the usual hedges still work?)
def _rets(market, t: str) -> pd.Series:
    s = market.series(t)
    s = s[s > 0]
    return np.log(s).diff().dropna()


def regime_breaks(market) -> Dict:
    """Detect when diversification / safe havens stop behaving: stock-bond correlation turning positive,
    'double-kill' days (stocks AND long bonds down together), havens failing on stock-down days."""
    cfg = _cfg()
    bench, bond, gold = cfg.get("equity", "^GSPC"), cfg.get("bond", "TLT"), cfg.get("gold", "GC=F")
    r_e, r_b, r_g = _rets(market, bench), _rets(market, bond), _rets(market, gold)
    out: Dict = {"flags": [], "metrics": {}}
    j = pd.concat([r_e.rename("e"), r_b.rename("b")], axis=1).dropna()
    if len(j) < 300:
        out["available"] = False
        return out
    out["available"] = True
    win = int(cfg.get("corr_window", 60))
    corr = j["e"].rolling(win).corr(j["b"]).dropna()
    cur = float(corr.iloc[-1])
    pct = float((corr < cur).mean() * 100)
    thr = float(cfg.get("stock_bond_corr", 0.30))
    out["metrics"]["stock_bond_corr"] = {"value": cur, "pctile": pct, "threshold": thr, "window": win}
    if cur >= thr:
        out["flags"].append({"key": "stock_bond", "title": "股債同漲同跌（債券失去避險功能）",
                             "detail": f"{win} 日股債相關係數 {cur:+.2f}（歷史 {pct:.0f}% 分位，門檻 +{thr:.2f}）：60/40 配置與長債避險同時失效，分散效果下降。"})
    last = j.iloc[-20:]
    kill = int(((last["e"] <= -0.005) & (last["b"] < 0)).sum())
    kmin = int(cfg.get("double_kill_days", 3))
    out["metrics"]["double_kill_20d"] = {"value": kill, "threshold": kmin}
    if kill >= kmin:
        out["flags"].append({"key": "double_kill", "title": "股債雙殺日偏多",
                             "detail": f"近 20 個交易日有 {kill} 天『標普跌≥0.5% 且長債同跌』（門檻 {kmin} 天）：典型的利率驅動型下跌，避險資產沒有接住。"})
    # havens on stock-down days (last 60 sessions)
    k = pd.concat([r_e.rename("e"), r_b.rename("b"), r_g.rename("g")], axis=1).dropna().iloc[-60:]
    down = k[k["e"] <= -0.01]
    if len(down) >= 4:
        fail = float(((down["b"] < 0) & (down["g"] < 0)).mean() * 100)
        out["metrics"]["haven_fail"] = {"value": fail, "n": int(len(down)), "threshold": float(cfg.get("haven_fail_pct", 50))}
        if fail >= float(cfg.get("haven_fail_pct", 50)):
            out["flags"].append({"key": "haven_fail", "title": "避險資產失靈",
                                 "detail": f"近 60 日標普跌≥1% 的 {len(down)} 天中，有 {fail:.0f}% 長債與黃金同時下跌：傳統避險工具靠不住，降低槓桿／持有現金比買避險資產更有效。"})
    return out


# ---------------------------------------------------------------- stage scoring
def score(ssi: Optional[float], levels: List[Dict], odds: Dict, shock: Dict, breaks: Dict, health_ok: bool = True) -> Dict:
    pts, why = 0, []
    if ssi is not None:
        idx = next((i for i, lv in enumerate(levels) if ssi < lv["max"]), len(levels) - 1)
        add = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3}.get(idx, 0)
        if add:
            pts += add
            why.append((add, f"SSI {ssi:.0f}（{levels[idx]['label']}）"))
    h63 = next((h for h in (odds or {}).get("horizons", []) if h["days"] == 63), None)
    la = (h63 or {}).get("lift_adj", (h63 or {}).get("lift")) if h63 else None
    if la is not None:
        add = 2 if la >= 2.2 else 1 if la >= 1.5 else 0
        if add:
            pts += add
            why.append((add, f"崩跌機率為歷史基準的 ×{la:.1f}"))
    paths = (shock or {}).get("paths") or []
    top = paths[0] if paths else None
    if top and top["state"] == "高度警戒":
        pts += 1
        why.append((1, f"傳導路徑「{top['name']}」高度警戒（{top['ignition']:.0f}）"))
    dv = (shock or {}).get("divergence") or {}
    if dv.get("flag"):
        hs = dv.get("hist") or {}
        pw, base = hs.get("prob_when_flagged"), hs.get("base_rate")
        if pw is not None and base and pw >= 1.2 * base:          # a rule earns its point only if history backs it
            pts += 1
            why.append((1, f"信用壓力領先股市恐慌（差 {dv['gap']:+.0f}；歷史背離後跌幅機率 {pw:.0f}% vs 基準 {base:.0f}%）"))
        else:
            why.append((0, f"信用壓力領先股市恐慌（差 {dv['gap']:+.0f}），但歷史上未顯示更高跌幅機率，不計分"))
    nb = len((breaks or {}).get("flags", []))
    if nb:
        add = 2 if nb >= 2 else 1
        pts += add
        why.append((add, f"避險機制失效訊號 {nb} 項"))
    stage = max(i for i, s in enumerate(STAGES) if pts >= s["thr"])
    return {"points": pts, "stage": stage, "name": STAGES[stage]["name"], "emoji": STAGES[stage]["emoji"], "why": why,
            "next_thr": STAGES[stage + 1]["thr"] if stage < 3 else None, "data_ok": health_ok}


def hysteresis(prev: Optional[int], cur: Dict) -> int:
    """Rise at once; fall only when points are ≥2 below the stage's entry threshold (no flip-flop alerts)."""
    st = cur["stage"]
    if prev is None or st >= prev:
        return st
    return st if cur["points"] <= STAGES[prev]["thr"] - 2 else prev


def actions(stage: int, portfolio: Dict, derisk: Optional[List[Dict]] = None, shock: Optional[Dict] = None) -> List[str]:
    """Concrete, stage-appropriate to-do list (not advice about specific trades: sizing is the user's call)."""
    pf = portfolio or {}
    beta = pf.get("beta") if not pf.get("error") else None
    tgt = (beta * BETA_FACTOR[stage]) if beta else None
    paths = (shock or {}).get("paths") or []
    top = paths[0]["name"] if paths and paths[0]["state"] != "低" else None
    out: List[str] = []
    if stage == 0:
        out += ["照常執行計畫，不需要為『可能的崩盤』改變部位。", "利用平靜期檢查：停損／再平衡規則是否寫下來、避險工具是否買得到。"]
    elif stage == 1:
        out += ["停止加碼高 β、高集中度的部位，新資金優先分批或放在低相關資產。", "把 /hedge 的避險成本記下來——壓力升高時保險會變貴，現在是相對便宜的時候。"]
    elif stage == 2:
        out += [f"將組合 β 降到約 {tgt:.2f}（目前 {beta:.2f}，×{BETA_FACTOR[2]:.2f}）。" if tgt else "將組合 β 降低約 15%。",
                "減碼風險貢獻最高的持股，或買 5–10% 價外、45–90 天的賣權（/hedge 可算成本）。",
                "未來 2 週有事件日（FOMC／四巫日／大額標售）前不要重壓。"]
    else:
        out += [f"目標 β ≈ {tgt:.2f}（目前 {beta:.2f}，×{BETA_FACTOR[3]:.2f}）：優先『減碼』而非追買賣權（此時保險費已貴）。" if tgt else "大幅降低 β（約 35%）：優先減碼。",
                "保留現金／短債作為彈藥；槓桿與保證金部位先降下來。",
                "設定明確的再進場條件（例如 SSI 回落到 60 以下且升溫速度轉『降溫』），避免情緒化來回操作。"]
    if stage >= 2 and derisk:
        out.append("優先減碼名單：" + "、".join(f"{d['sym']}（約 ${d['sell_usd']:,.0f}）" for d in derisk[:3]))
    if stage >= 1 and top:
        out.append(f"盯緊傳導路徑「{top}」：它是目前最可能點火的衝擊來源（/shock）。")
    return out
