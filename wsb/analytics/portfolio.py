"""Portfolio risk: live P&L, beta, historical VaR/CVaR, risk contribution,
correlation, and REAL historical crisis replays (actual prices over each
crisis window; beta proxy only when a holding didn't exist yet)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from ..config import ROOT, SETTINGS, env

log = logging.getLogger(__name__)


def load_holdings() -> Dict[str, dict]:
    cfg = SETTINGS.get("portfolio", {})
    if not cfg.get("enabled", True):                    # 情報站模式：完全不讀取任何持倉
        return {}
    acct = env(cfg.get("account_id_env", "PRIMARY_PORTFOLIO_USER_ID"))
    for key in ("file", "fallback_file"):
        p = (ROOT / cfg.get(key, "")).resolve() if cfg.get(key) else None
        if not p or not p.exists():
            continue
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            log.warning("holdings file %s unreadable: %s", p, e)
            continue
        raw = None
        if isinstance(data, dict) and isinstance(data.get("holdings"), list):     # portfolio_holdings.json
            raw = {h["sym"]: h for h in data["holdings"]}
        elif isinstance(data, dict):                                              # sim_trading.json
            accounts = [data.get(acct)] if acct and acct in data else list(data.values())
            for a in accounts:
                if isinstance(a, dict) and isinstance(a.get("holdings"), dict):
                    raw = a["holdings"]
                    break
        if not raw:
            continue
        out = {}
        for sym, e in raw.items():
            try:
                sh = float(e.get("shares") or 0)
                cost = float(e.get("cost_basis") or e.get("cost") or 0)
            except (TypeError, ValueError):
                continue
            if sh > 0 and cost > 0:
                cur = e.get("currency") or ("TWD" if sym.endswith((".TW", ".TWO")) else "USD")
                out[sym] = {"shares": sh, "cost": cost, "currency": cur, "name": e.get("name", sym)}
        if out:
            return out
    return {}


def _beta(r: pd.Series, b: pd.Series) -> Optional[float]:
    j = pd.concat([r, b], axis=1).dropna()
    if len(j) < 60:
        return None
    v = j.iloc[:, 1].var()
    return float(j.cov().iloc[0, 1] / v) if v else None


def analyze(market, holdings: Dict[str, dict]) -> Dict:
    cfg = SETTINGS.get("portfolio", {})
    bench = cfg.get("benchmark", "SPY")
    lb = int(cfg.get("var_lookback_days", 504))
    if not holdings:
        return {"error": "找不到持倉檔或持倉為空"}
    fx = market.series("TWD=X")
    usdtwd = float(market.q("TWD=X")["price"]) if market.q("TWD=X") else (float(fx.iloc[-1]) if len(fx) else None)

    px = {}
    for s in list(holdings) + [bench]:
        ser = market.series(s)
        if s in holdings and holdings[s]["currency"] == "TWD" and len(ser) and len(fx):
            ser = (ser / fx.reindex(ser.index, method="ffill")).dropna()
        px[s] = ser
    rows, total_val, total_cost = [], 0.0, 0.0
    for s, h in holdings.items():
        ser = px.get(s, pd.Series(dtype=float))
        q = market.q(s)
        price_local = q["price"] if q else (float(market.series(s).iloc[-1]) if len(market.series(s)) else None)
        if price_local is None:
            rows.append({"sym": s, "error": "無報價"})
            continue
        if h["currency"] == "TWD" and not usdtwd:
            rows.append({"sym": s, "error": "缺 USD/TWD 匯率"})
            continue
        conv = usdtwd if h["currency"] == "TWD" else 1.0
        val = price_local * h["shares"] / conv
        cost = h["cost"] * h["shares"] / conv
        total_val += val
        total_cost += cost
        rows.append({"sym": s, "name": h.get("name", s), "shares": h["shares"], "price": price_local,
                     "currency": h["currency"], "value_usd": val, "cost_usd": cost,
                     "pnl_usd": val - cost, "pnl_pct": (val / cost - 1) * 100,
                     "d1_pct": q["chg_pct"] if q else None, "sigma": market.sigma_move(s)})
    valid = [r for r in rows if "value_usd" in r]
    for r in valid:
        r["weight"] = r["value_usd"] / total_val * 100 if total_val else 0

    # ---- return matrix (USD), missing history → beta-proxied from benchmark ----
    if not valid or total_val <= 0:
        return {"error": "持倉皆無報價", "positions": rows}
    b = px[bench].pct_change(fill_method=None).dropna().iloc[-lb:]
    if len(b) < 60:
        return {"error": f"基準 {bench} 歷史不足", "positions": rows}
    rets, proxied = {}, []
    for r in valid:
        s = r["sym"]
        # align prices to the benchmark calendar BEFORE differencing (crypto weekends / TW holidays)
        bench_idx = px[bench].index
        ra = (px[s].reindex(px[s].index.union(bench_idx)).ffill(limit=5).reindex(bench_idx)
              .pct_change(fill_method=None).reindex(b.index))
        beta = _beta(ra, b)
        if s.endswith((".TW", ".TWO")) and beta is not None:
            # a TW close on day D mostly reflects the US move of D-1 → add the lagged-benchmark beta (Dimson 1979)
            lag = _beta(ra, b.shift(1))
            beta = beta + (lag or 0.0)
        r["beta"] = beta
        r["corr_spx_60d"] = float(ra.iloc[-60:].corr(b.iloc[-60:])) if ra.iloc[-60:].notna().sum() > 40 else None
        if ra.notna().mean() < 0.9:
            proxied.append(s)
            ra = ra.fillna(b * (beta if beta is not None else 1.0))
        rets[s] = ra.fillna(0)
    R = pd.DataFrame(rets)
    w = np.array([r["weight"] / 100 for r in valid])
    port = R.values @ w
    port_s = pd.Series(port, index=R.index)
    cov = np.cov(R.values.T) if R.shape[1] > 1 else np.array([[R.var().iloc[0]]])
    sig_p = float(np.sqrt(w @ cov @ w))
    mctr = (cov @ w) * w / (sig_p ** 2) if sig_p else np.zeros_like(w)
    for r, c in zip(valid, mctr):
        r["risk_contrib_pct"] = float(c * 100)
    var95 = -np.percentile(port, 5)
    var99 = -np.percentile(port, 1)
    tail = port[port <= np.percentile(port, 2.5)]
    cvar = -tail.mean() if len(tail) else None
    cum = (1 + port_s.iloc[-252:]).cumprod()
    mdd = float((cum / cum.cummax() - 1).min() * 100)
    hhi = float(sum((r["weight"] / 100) ** 2 for r in valid))

    # ---- historical crisis replays ----
    scen = []
    bench_full = market.series(bench)
    for sc in SETTINGS.get("stress_scenarios", []):
        a, z = pd.Timestamp(sc["start"]), pd.Timestamp(sc["end"])
        def win_ret(ser):
            ser = ser.dropna()
            s0 = ser[ser.index <= a]
            s1 = ser[ser.index <= z]
            if not len(s0) or not len(s1) or s0.index[-1] < a - pd.Timedelta(days=7):
                return None
            return float(s1.iloc[-1] / s0.iloc[-1] - 1)
        br = win_ret(bench_full)
        pnl, detail, prox = 0.0, [], []
        for r in valid:
            ret = win_ret(px[r["sym"]])
            if ret is None:
                if br is None:
                    continue
                ret = br * (r.get("beta") or 1.0)
                prox.append(r["sym"])
            pnl += r["value_usd"] * ret
            detail.append((r["sym"], ret * 100))
        if br is None and not detail:
            continue
        worst = sorted(detail, key=lambda x: x[1])[:3]
        scen.append({"name": sc["name"], "bench_pct": br * 100 if br is not None else None,
                     "port_pct": pnl / total_val * 100 if total_val else None, "pnl_usd": pnl,
                     "worst": worst, "proxied": prox})
    port_beta = _beta(port_s, b)
    betas = {bench: port_beta}
    for alt in ("QQQ", "SMH"):
        sa = market.series(alt).pct_change(fill_method=None).reindex(port_s.index)
        if sa.notna().sum() > 120:
            betas[alt] = _beta(port_s, sa)
    hypo = []
    if port_beta is not None:
        for shock in (-5, -10, -20, -30):
            hypo.append({"spx_pct": shock, "port_pct": shock * port_beta,
                         "pnl_usd": total_val * shock / 100 * port_beta})
    return {
        "total_value_usd": total_val, "total_cost_usd": total_cost,
        "pnl_usd": total_val - total_cost, "pnl_pct": (total_val / total_cost - 1) * 100 if total_cost else None,
        "day_pnl_usd": sum(r["value_usd"] * (r["d1_pct"] or 0) / (100 + (r["d1_pct"] or 0)) for r in valid),
        "positions": sorted(rows, key=lambda r: -r.get("value_usd", 0)),
        "beta": port_beta, "betas": betas, "vol_ann_pct": sig_p * np.sqrt(252) * 100,
        "var95_1d_usd": var95 * total_val, "var99_1d_usd": var99 * total_val,
        "cvar975_1d_usd": cvar * total_val if cvar is not None else None,
        "var99_10d_usd": var99 * np.sqrt(10) * total_val,
        "max_dd_1y_pct": mdd, "hhi": hhi, "effective_n": 1 / hhi if hhi else None,
        "scenarios": scen, "hypothetical": hypo, "proxied": proxied, "usdtwd": usdtwd,
        "lookback_days": int(len(port)),
    }
