"""Hedge-cost calculator.

Given the live portfolio (value, beta to SPY / QQQ) and live CBOE put chains,
answer: "What does it cost to protect my portfolio, and what do I get back
if the market falls 10% / 20%?"  Compares index puts, inverse ETFs and
simply de-risking the highest-risk holdings."""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from ..config import SETTINGS

H = SETTINGS.get("hedge", {})
TARGET_DTES = H.get("target_dte", [45, 90])
OTM_LEVELS = H.get("otm_pct", [0, 5, 10])
SHOCKS = H.get("shocks_pct", [10, 20])
INVERSE = {"SPY": ("SH", "ProShares 標普 -1x"), "QQQ": ("PSQ", "ProShares 那指 -1x")}


def _pick_expiries(rows: List[dict]) -> List[str]:
    exps = sorted({(r["expiry"], r["dte"]) for r in rows if r["dte"] >= 20}, key=lambda x: x[1])
    chosen = []
    for t in TARGET_DTES:
        if not exps:
            break
        e = min(exps, key=lambda x: abs(x[1] - t))[0]
        if e not in chosen:
            chosen.append(e)
    return chosen


def _put_near(rows: List[dict], expiry: str, strike_target: float) -> Optional[dict]:
    puts = [r for r in rows if r["expiry"] == expiry and r["type"] == "P" and r["mid"] > 0]
    return min(puts, key=lambda r: abs(r["strike"] - strike_target)) if puts else None


def put_plans(chain: Dict, notional: float, beta: float, underlying: str) -> List[dict]:
    spot, rows = chain["spot"], chain["rows"]
    plans = []
    raw_contracts = notional / (spot * 100)
    contracts = max(1, round(raw_contracts))
    for exp in _pick_expiries(rows):
        for otm in OTM_LEVELS:
            p = _put_near(rows, exp, spot * (1 - otm / 100))
            if not p:
                continue
            cost = p["mid"] * 100 * contracts
            dte = max(p["dte"], 1)
            payoff = {}
            for d in SHOCKS:
                px_at = spot * (1 - d / 100)
                intrinsic = max(p["strike"] - px_at, 0) * 100 * contracts
                loss = notional * d / 100                     # β-weighted portfolio loss
                payoff[d] = {"unhedged": -loss, "hedged": -loss + intrinsic - cost,
                             "protected_pct": min(intrinsic / loss * 100, 999) if loss else 0}
            plans.append({
                "underlying": underlying, "expiry": p["expiry"], "dte": round(dte), "strike": p["strike"],
                "otm_pct": (1 - p["strike"] / spot) * 100, "mid": p["mid"], "iv": p["iv"],
                "contracts": contracts, "hedge_ratio": contracts * spot * 100 / notional if notional else None,
                "cost": cost, "breakeven_drop_pct": (1 - (p["strike"] - p["mid"]) / spot) * 100,
                "payoff": payoff, "spot": spot,
            })
    return plans


def _opt_near(rows: List[dict], expiry: str, typ: str, strike_target: float) -> Optional[dict]:
    cands = [r for r in rows if r["expiry"] == expiry and r["type"] == typ and r["mid"] > 0]
    return min(cands, key=lambda r: abs(r["strike"] - strike_target)) if cands else None


def structures(chain: Dict, notional: float, underlying: str) -> List[dict]:
    """Cheaper alternatives to a naked put: put spread (give up deep crash cover for a lower premium) and
    zero-cost-ish collar (sell an upside call to pay for the put).  Payoff = hedge leg only, at index -20/-10/+10%."""
    spot, rows = chain["spot"], chain["rows"]
    contracts = max(1, round(notional / (spot * 100)))
    mult = 100 * contracts
    out = []

    def hedge_pnl(legs, S):
        v = 0.0
        for kind, K, px, sign in legs:                      # sign +1 long, -1 short
            intrinsic = max(K - S, 0) if kind == "P" else max(S - K, 0)
            v += sign * (intrinsic - px) * mult
        return v
    for exp in _pick_expiries(rows):
        lp = _opt_near(rows, exp, "P", spot * 0.95)         # long 5% OTM put
        sp = _opt_near(rows, exp, "P", spot * 0.85)         # short 15% OTM put
        if lp and sp and sp["strike"] < lp["strike"]:
            legs = [("P", lp["strike"], lp["mid"], +1), ("P", sp["strike"], sp["mid"], -1)]
            net = (lp["mid"] - sp["mid"]) * mult
            out.append({"kind": "put spread", "label": "賣權價差", "underlying": underlying, "expiry": lp["expiry"], "dte": round(lp["dte"]),
                        "legs": f"買 {lp['strike']:.0f}P／賣 {sp['strike']:.0f}P", "contracts": contracts, "net_cost": net,
                        "max_cover": (lp["strike"] - sp["strike"]) * mult - net,
                        "pnl": {k: hedge_pnl(legs, spot * (1 + k / 100)) for k in (-20, -10, 10)}, "spot": spot})
        put = _opt_near(rows, exp, "P", spot * 0.95)
        if put:
            calls = [r for r in rows if r["expiry"] == exp and r["type"] == "C" and r["strike"] > spot and r["mid"] > 0]
            if calls:
                call = min(calls, key=lambda r: abs(r["mid"] - put["mid"]))       # premium closest to the put's → ~zero cost
                legs = [("P", put["strike"], put["mid"], +1), ("C", call["strike"], call["mid"], -1)]
                net = (put["mid"] - call["mid"]) * mult
                out.append({"kind": "collar", "label": "領口（Collar）", "underlying": underlying, "expiry": put["expiry"], "dte": round(put["dte"]),
                            "legs": f"買 {put['strike']:.0f}P／賣 {call['strike']:.0f}C", "contracts": contracts, "net_cost": net,
                            "max_cover": None, "cap_pct": (call["strike"] / spot - 1) * 100,
                            "pnl": {k: hedge_pnl(legs, spot * (1 + k / 100)) for k in (-20, -10, 10)}, "spot": spot})
    return out


def analyze(portfolio: Dict, chains: Dict[str, Dict], stress_score: Optional[float], cut_frac: float = 0.25) -> Dict:
    if not portfolio or portfolio.get("error"):
        return {"error": "持倉資料不可用"}
    V = float(portfolio["total_value_usd"])
    betas = portfolio.get("betas") or {"SPY": portfolio.get("beta")}
    out: Dict = {"value": V, "betas": betas, "ssi": stress_score, "underlyings": {}}
    for u, chain in chains.items():
        beta = betas.get(u)
        if beta is None or beta <= 0 or not chain:        # no index-put hedge makes sense for ≤0 beta
            continue
        notional = V * beta
        plans = put_plans(chain, notional, beta, u)
        for pl in plans:
            pl["cost_pct"] = pl["cost"] / V * 100
            pl["cost_pct_ann"] = pl["cost_pct"] * 365 / pl["dte"]
        try:
            structs = structures(chain, notional, u)
        except Exception:  # noqa: BLE001
            structs = []
        inv_sym, inv_name = INVERSE.get(u, (None, None))
        out["underlyings"][u] = {
            "beta": beta, "notional": notional, "spot": chain["spot"],
            "raw_contracts": notional / (chain["spot"] * 100), "plans": plans, "structures": structs,
            "inverse": {"symbol": inv_sym, "name": inv_name, "full_hedge_usd": notional,
                        "half_hedge_usd": notional / 2} if inv_sym else None,
        }
    # de-risk alternative: trim highest risk contributors until beta falls ~25%
    pos = [p for p in portfolio.get("positions", []) if p.get("value_usd")]
    pos.sort(key=lambda p: -(p.get("risk_contrib_pct") or 0))
    trim = []
    target_cut = cut_frac * (betas.get("SPY") or 1) * V
    cut = 0.0
    for p in pos:
        if cut >= target_cut:
            break
        b = p["beta"] if p.get("beta") is not None else 1.0
        if b <= 0.05:                                       # hedges / diversifiers: selling them raises risk
            continue
        sell = min(p["value_usd"] * 0.5, (target_cut - cut) / max(b, 0.3))
        trim.append({"sym": p["sym"], "sell_usd": sell, "shares": math.floor(sell / (p["value_usd"] / p["shares"])) if p.get("shares") else None,
                     "risk_contrib_pct": p.get("risk_contrib_pct")})
        cut += sell * b
    out["derisk"] = trim
    out["advice"] = advice(stress_score, out)
    return out


def advice(ssi: Optional[float], res: Dict) -> str:
    small = all(u["raw_contracts"] < 0.6 for u in res["underlyings"].values()) if res["underlyings"] else False
    size_note = ("你的部位小於 1 口選擇權的名目金額，買 1 口會『過度避險』；小資金用反向 ETF 或減碼較精準。"
                 if small else "")
    if ssi is None:
        return size_note or "壓力指數尚未就緒。"
    if ssi < 45:
        base = "壓力低：保險最便宜但也最不需要；若要避險，選 10% 價外、90 天，當作『災難保險』即可。"
    elif ssi < 60:
        base = "壓力中性：可用 5–10% 價外、45–90 天的賣權保護核心部位，或在財報/FOMC 前短期加保。"
    elif ssi < 75:
        base = "壓力升溫：建議建立保護——價平～5% 價外、90 天賣權，或減碼風險貢獻最高的持股。"
    else:
        base = "壓力極高：保險費已變貴，優先『減碼』而非追買賣權；剩餘部位用反向 ETF 對沖。"
    return (base + " " + size_note).strip()
