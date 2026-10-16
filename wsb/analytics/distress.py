"""企業危機雷達：銀行、科技與私募信貸公司的破產／財務危機警訊（只用財報、股價與 SEC 申報，不用新聞）。

Per company, a handful of signals, each ok / watch / alert:
  corporate  Altman Z''-score, interest coverage, cash runway, debt / EBITDA, debt growth, naive Merton default probability
  bank       AOCI (unrealised securities losses) / equity, equity / assets, deposit change, price vs the regional-bank ETF
  credit     liabilities / equity (BDC leverage)
  all        drawdown from the 52-week high, SEC red-flag filings (8-K 1.03 / 2.04 / 4.02 / 3.01 / 4.01 / 2.06, NT 10-K / 10-Q)

Thresholds come from the academic literature (Altman 1995 Z''; Bharath & Shumway 2008 naive Merton) or from common
credit-analysis conventions; they are NOT fitted or backtested in this system and are labelled as such on the site."""
from __future__ import annotations

import math
from datetime import timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS
from ..data import distress_data as DD
from ..data.econcal import us_today

PTS = {"ok": 0, "watch": 1, "alert": 2}
ALERT_PTS, WATCH_PTS = 5, 3
SKIP_THEMES = ("電信公用",)          # regulated utilities / telcos: high leverage is their normal business model


def cfg() -> Dict:
    return SETTINGS.get("distress", {}) or {}


def watchlist() -> Dict[str, Dict]:
    """symbol → {zh, kind}: the configured watch list plus the US stock-scoring universe."""
    from ..data.stocks import universe
    out: Dict[str, Dict] = {}
    us = universe().get("us") or {}
    for s, (zh, _en) in (us.get("symbols") or {}).items():
        th = us.get("themes", {}).get(s, "")
        if th in SKIP_THEMES:
            continue
        out[s] = {"zh": zh, "kind": "fin" if th == "金融" else "corp", "theme": th}
    for kind, syms in (cfg().get("watch") or {}).items():
        for s, zh in (syms or {}).items():
            out[str(s)] = {"zh": str(zh), "kind": str(kind), "theme": "觀察名單"}
    return out


def extra_symbols() -> List[str]:
    """Watch-list names outside the stock universe (their prices are downloaded with it)."""
    return [str(s) for syms in (cfg().get("watch") or {}).values() for s in (syms or {})]


def _ncdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _sig(sid: str, zh: str, state: str, txt: str) -> Dict:
    return {"id": sid, "zh": zh, "state": state, "txt": txt}


def _num(x) -> Optional[float]:
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else float(x)


def _debt(b: Dict) -> Optional[float]:
    ltd = _num(b.get("ltd"))
    if ltd is None and (b.get("ltd_nc") is not None or b.get("ltd_cur") is not None):
        ltd = (b.get("ltd_nc") or 0.0) + (b.get("ltd_cur") or 0.0)
    if ltd is None and b.get("debt_cur") is None:
        return None
    return (ltd or 0.0) + (b.get("debt_cur") or 0.0) + (b.get("fin_lease") or 0.0)


def _liab(b: Dict) -> Optional[float]:
    if b.get("liab") is not None:
        return b["liab"]
    if b.get("assets") is not None and b.get("equity") is not None:
        return b["assets"] - b["equity"]
    return None


def altman(b: Dict) -> Optional[float]:
    """Altman Z'' (1995, non-manufacturers): 6.56 WC/TA + 3.26 RE/TA + 6.72 EBIT/TA + 1.05 BVE/TL."""
    ta, tl = b.get("assets"), _liab(b)
    need = (ta, tl, b.get("cur_assets"), b.get("cur_liab"), b.get("re"), b.get("ebit_ttm"), b.get("equity"))
    if any(v is None for v in need) or ta <= 0 or tl <= 0:
        return None
    wc = b["cur_assets"] - b["cur_liab"]
    return 6.56 * wc / ta + 3.26 * b["re"] / ta + 6.72 * b["ebit_ttm"] / ta + 1.05 * b["equity"] / tl


def merton_pd(px: pd.Series, b: Dict) -> Optional[Dict]:
    """Naive Merton one-year default probability (Bharath & Shumway 2008).
    E = market cap, F = current liabilities + ½ long-term debt, σD = 0.05 + 0.25 σE, μ = the stock's past-year return."""
    if b.get("shares") is None or b.get("cur_liab") is None or len(px) < 200:
        return None
    lt = b.get("ltd_nc") if b.get("ltd_nc") is not None else (b.get("ltd") or 0.0)
    F = b["cur_liab"] + 0.5 * lt
    E = float(px.iloc[-1]) * b["shares"]
    if F <= 0 or E <= 0:
        return None
    r = np.log(px).diff().dropna().iloc[-252:]
    se = float(r.std() * math.sqrt(252))
    mu = float(px.iloc[-1] / px.iloc[-min(len(px), 253)] - 1)
    sv = E / (E + F) * se + F / (E + F) * (0.05 + 0.25 * se)
    if sv <= 0:
        return None
    dd = (math.log((E + F) / F) + (mu - 0.5 * sv * sv)) / sv
    return {"dd": dd, "pd": _ncdf(-dd), "mcap": E, "vol": se}


def _market(px: pd.Series, bench: pd.Series, kind: str) -> List[Dict]:
    out = []
    if len(px) < 120:
        return out
    hi = float(px.iloc[-252:].max())
    dd = 1 - float(px.iloc[-1]) / hi if hi > 0 else 0.0
    st = "alert" if dd >= 0.70 else "watch" if dd >= 0.50 else "ok"
    out.append(_sig("drawdown", "距 52 週高點", st, f"-{dd * 100:.0f}%"))
    if kind == "bank" and len(bench) > 70 and len(px) > 70:
        j = pd.concat([px, bench], axis=1).dropna()
        if len(j) > 64:
            rel = (j.iloc[-1, 0] / j.iloc[-64, 0]) - (j.iloc[-1, 1] / j.iloc[-64, 1])
            st = "alert" if rel <= -0.35 else "watch" if rel <= -0.20 else "ok"
            out.append(_sig("vs_kre", "3 個月相對區域銀行 ETF", st, f"{rel * 100:+.0f} 個百分點"))
    return out


def _filing_sigs(flags: List[Dict], today) -> List[Dict]:
    out = []
    lo = (today - timedelta(days=int(cfg().get("filing_days", 120)))).isoformat()
    lo_bk = (today - timedelta(days=365)).isoformat()
    for f in flags or []:
        if f["date"] >= lo or (f["code"] == "1.03" and f["date"] >= lo_bk):
            out.append({**_sig("sec_" + f["code"].replace(" ", "_").replace(".", "_"), "SEC 申報", f["level"], f"{f['date']} {f['zh']}"),
                        "url": f.get("url"), "hard": f["level"] == "alert"})
    return out


def _corp(b: Dict, px: pd.Series) -> List[Dict]:
    out = []
    z = altman(b)
    if z is not None:
        st = "alert" if z < 1.1 else "watch" if z < 2.6 else "ok"
        out.append(_sig("altman", "Altman Z''", st, f"{z:.2f}（<1.1 危險、1.1–2.6 灰色）"))
    ebit, intr, rev = b.get("ebit_ttm"), b.get("interest_ttm"), b.get("rev_ttm")
    debt, cash = _debt(b), b.get("cash")
    if debt is not None and cash is not None and cash >= debt:
        # more cash than debt: an accounting loss can't push it into default → coverage / leverage don't apply
        out.append(_sig("net_cash", "淨現金", "ok", f"現金 {cash / 1e9:.1f}B ≥ 負債 {debt / 1e9:.1f}B"))
        debt = None
    elif ebit is not None and intr and intr > 0 and (not rev or intr / abs(rev) > 0.005):
        cov = ebit / intr
        st = "alert" if cov < 1 else "watch" if cov < 2 else "ok"
        out.append(_sig("coverage", "利息保障倍數", st, f"{cov:.1f} 倍（營業利益÷利息）"))
    ocf, capex = b.get("ocf_ttm"), b.get("capex_ttm")
    if ocf is not None and cash is not None:
        fcf = ocf - (capex or 0.0)
        if fcf < 0:
            m = cash / (-fcf / 12)
            st = "alert" if m < 12 else "watch" if m < 24 else "ok"
            out.append(_sig("runway", "現金可撐", st, f"{math.floor(m)} 個月（自由現金流 {fcf / 1e9:+.1f}B／年，不再融資的話）"))
    if debt is not None and debt > 0:
        ebitda = (ebit or 0.0) + (b.get("da_ttm") or 0.0) if ebit is not None else None
        if ebitda is not None:
            if ebitda <= 0:
                out.append(_sig("leverage", "負債／EBITDA", "alert", f"EBITDA ≤ 0，負債 {debt / 1e9:.1f}B"))
            else:
                lev = debt / ebitda
                st = "alert" if lev > 6 else "watch" if lev > 4 else "ok"
                out.append(_sig("leverage", "負債／EBITDA", st, f"{lev:.1f} 倍（負債 {debt / 1e9:.1f}B）"))
        if b.get("ltd") and b.get("ltd_yago") and b["ltd_yago"] > 0:
            g = b["ltd"] / b["ltd_yago"] - 1
            out.append(_sig("debt_growth", "長期負債年增", "watch" if g > 1.0 else "ok", f"{g * 100:+.0f}%"))
    m = merton_pd(px, b)
    if m is not None:
        st = "alert" if m["pd"] >= 0.20 else "watch" if m["pd"] >= 0.05 else "ok"
        out.append({**_sig("merton", "Merton 一年違約機率", st, f"{m['pd'] * 100:.1f}%（違約距離 {m['dd']:.1f}）"), "pd": round(m["pd"], 4)})
    return out


def _bank(b: Dict) -> List[Dict]:
    out = []
    eq, ta = b.get("equity"), b.get("assets")
    if b.get("aoci") is not None and eq and eq > 0:
        htm = (-(b["htm_loss"] - (b.get("htm_gain") or 0.0)) if b.get("htm_loss") is not None
               else (b["htm_fv"] - b["htm_cost"]) if b.get("htm_fv") is not None and b.get("htm_cost") else None)
        r = (b["aoci"] + min(htm or 0.0, 0.0)) / eq
        st = "alert" if r <= -0.40 else "watch" if r <= -0.25 else "ok"
        how = "AOCI＋持有到期債券評價損失（稅前）" if htm is not None else "AOCI；未申報持有到期債券市值"
        out.append(_sig("aoci", "證券評價損失／股東權益", st, f"{r * 100:+.0f}%（{how}）"))
    if eq is not None and ta:
        r = eq / ta
        st = "alert" if r < 0.05 else "watch" if r < 0.07 else "ok"
        out.append(_sig("eq_assets", "股東權益／總資產", st, f"{r * 100:.1f}%"))
    if b.get("deposits") and b.get("deposits_q"):
        g = b["deposits"] / b["deposits_q"] - 1
        st = "alert" if g <= -0.10 else "watch" if g <= -0.05 else "ok"
        out.append(_sig("deposits", "存款季變化", st, f"{g * 100:+.1f}%"))
    return out


def _credit(b: Dict) -> List[Dict]:
    tl, eq = _liab(b), b.get("equity")
    if tl is None or not eq or eq <= 0:
        return []
    r = tl / eq
    st = "alert" if r > 1.75 else "watch" if r > 1.25 else "ok"
    return [_sig("bdc_lev", "負債／淨值", st, f"{r:.2f} 倍（法定上限約 2 倍）")]


def overall(sigs: List[Dict]) -> str:
    """Any hard SEC red flag → alert.  Otherwise points (watch 1, alert 2): ≥ 5 alert, ≥ 3 watch — one bad ratio alone
    never lights a company up (many healthy asset-light or buyback-heavy firms fail a single ratio such as Z'')."""
    if any(s.get("hard") for s in sigs):
        return "alert"
    p = sum(PTS.get(s["state"], 0) for s in sigs)
    return "alert" if p >= ALERT_PTS else "watch" if p >= WATCH_PTS else "ok"


def assess(sym: str, meta: Dict, rec: Dict, px: pd.Series, bench: pd.Series, today) -> Dict:
    b = (rec or {}).get("bs") or {}
    kind = meta["kind"]
    if kind == "fin":
        kind = "bank" if b.get("deposits") and b.get("assets") and b["deposits"] / b["assets"] > 0.4 else "fin"
    sigs: List[Dict] = []
    old = bool(b.get("end")) and (today - pd.Timestamp(b["end"]).date()).days > 200
    fresh = bool(b) and (today - pd.Timestamp(b["end"]).date()).days <= 400 if b.get("end") else False
    if fresh:
        if kind == "corp" or kind == "tech":
            sigs += _corp(b, px)
        elif kind == "bank":
            sigs += _bank(b)
        elif kind == "credit":
            sigs += _credit(b)
    sigs += _market(px, bench, kind)
    sigs += _filing_sigs((rec or {}).get("flags"), today)
    st = overall(sigs)
    return {"sym": sym, "zh": meta["zh"], "kind": kind, "theme": meta.get("theme"), "state": st,
            "points": sum(PTS.get(s["state"], 0) for s in sigs), "signals": sigs,
            "bs_end": b.get("end"), "bs_old": old, "has_bs": fresh,
            "price": float(px.iloc[-1]) if len(px) else None}


def build(eng) -> Dict:
    if not cfg().get("enabled", True):
        return {"available": False}
    cache = DD.load()
    today = us_today()
    sp = getattr(eng, "stockprices", None)
    from .sessions import completed
    h = eng.market.history
    bench = completed(h["KRE"].dropna(), "KRE") if "KRE" in h.columns else pd.Series(dtype=float)
    rows = []
    for sym, meta in watchlist().items():
        px = completed(sp.series(sym), sym) if sp is not None else pd.Series(dtype=float)
        rec = cache.get(sym) or {}
        if not rec.get("bs") and len(px) < 120 and not rec.get("flags"):
            continue
        rows.append(assess(sym, meta, rec, px, bench, today))
    if not rows:
        return {"available": False}
    order = {"alert": 0, "watch": 1, "ok": 2}
    rows.sort(key=lambda r: (order[r["state"]], -r["points"], r["sym"]))
    n = {k: sum(r["state"] == k for r in rows) for k in order}
    return {"available": True, "asof": today.isoformat(), "rows": rows, "counts": n, "total": len(rows)}
