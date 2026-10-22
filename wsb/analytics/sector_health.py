"""產業體檢 — the company strain metrics (data/fundamentals.py) rolled up by theme, the AI infrastructure ledger, and the
financing-transmission check (strain building up at the same time as tighter credit and higher rates).

Everything is a fixed rule over filed numbers; nothing here forecasts.  A theme's "share flagged" only counts
companies that disclose the metric; coverage is shown next to it."""
from __future__ import annotations

from typing import Dict, List, Optional

from ..data import fundamentals as FU

# the AI build-out: the spenders, and the ones that finance it with debt (shown even when outside the tracked list)
def ai_ledger() -> List[str]:
    from ..config import SETTINGS
    return list((SETTINGS.get("sector_health") or {}).get("ai_ledger") or ["MSFT", "GOOGL", "AMZN", "META", "ORCL", "CRWV"])


AI_LEDGER = ai_ledger()
RULE_LAB = {k: (zh, en) for k, zh, en, _f in FU.RULES}


def _row(sym: str, rec: Dict, name: str = "", theme: str = "") -> Optional[Dict]:
    m = (rec or {}).get("m")
    if not m:
        return None
    return {"sym": sym, "name": name or sym, "theme": theme, "m": m, "flags": FU.flags(m)}


def by_theme(rows: List[Dict]) -> List[Dict]:
    out: Dict[str, Dict] = {}
    for r in rows:
        t = out.setdefault(r["theme"] or "其他", {"theme": r["theme"] or "其他", "n": 0, "flags": {k: 0 for k in RULE_LAB},
                                                  "cover": {k: 0 for k in RULE_LAB}, "names": {k: [] for k in RULE_LAB}})
        t["n"] += 1
        m = r["m"]
        cov = {"gap": m.get("capex_ocf") is not None or m.get("ocf_negative"), "cip": m.get("cip_share") is not None,
               "inv": m.get("inv_minus_rev") is not None, "dso": m.get("dso") is not None and m.get("dso_prev") is not None,
               "int": m.get("int_burden") is not None or m.get("ebit_negative"), "debt": m.get("debt_growth") is not None}
        for k in RULE_LAB:
            t["cover"][k] += int(bool(cov[k]))
            if k in r["flags"]:
                t["flags"][k] += 1
                t["names"][k].append(r["sym"])
    res = list(out.values())
    for t in res:
        t["score"] = sum(t["flags"][k] / t["cover"][k] for k in RULE_LAB if t["cover"][k]) / max(1, sum(1 for k in RULE_LAB if t["cover"][k]))
    return sorted(res, key=lambda t: -t["score"])


def transmission(rows: List[Dict], eng) -> Dict:
    """Funding strain (more companies paying capex with outside money) at the same time as tighter credit / higher rates."""
    gap_now = sum(1 for r in rows if "gap" in r["flags"])
    gap_prev = sum(1 for r in rows if (r["m"].get("capex_ocf_prev") or 0) > 1.0 or r["m"].get("ocf_prev_negative"))
    cover = sum(1 for r in rows if r["m"].get("capex_ocf") is not None and r["m"].get("capex_ocf_prev") is not None)
    st = getattr(eng, "stress", None)
    credit = (getattr(st, "blocks", None) or {}).get("信用") if st is not None else None
    tnx = None
    try:
        s = eng.market.series("^TNX").dropna()
        s = s / 10 if len(s) and s.median() > 20 else s          # some feeds quote ^TNX ×10 (same rule as factors.py)
        tnx = (float(s.iloc[-1]), float(s.iloc[-1] - s.iloc[-64])) if len(s) > 64 else None
    except Exception:  # noqa: BLE001
        pass
    rising_gap = gap_now > gap_prev
    tight_credit = credit is not None and credit >= 60
    higher_rates = tnx is not None and tnx[1] > 0.25
    return {"gap_now": gap_now, "gap_prev": gap_prev, "cover": cover, "credit_score": credit, "tnx": tnx,
            "rising_gap": rising_gap, "tight_credit": tight_credit, "higher_rates": higher_rates,
            "on": rising_gap and (tight_credit or higher_rates)}


def build(eng, cache: Optional[Dict] = None) -> Dict:
    from ..data.stocks import universe
    cache = cache if cache is not None else FU.load()
    u = (universe().get("us") or {})
    names, themes = u.get("symbols") or {}, u.get("themes") or {}
    rows = [r for s in names if (r := _row(s, cache.get(s), names[s][0], themes.get(s, "其他")))]
    ledger = [r for s in AI_LEDGER if (r := _row(s, cache.get(s), (names.get(s) or (s, s))[0], themes.get(s, "AI 基礎建設")))]
    if not rows and not ledger:
        return {"available": False}
    ends = sorted(r["m"]["end"] for r in rows + ledger if r["m"].get("end"))
    return {"available": True, "n": len(rows), "themes": by_theme(rows), "ledger": ledger, "rows": rows,
            "transmission": transmission(rows + [r for r in ledger if r["sym"] not in names], eng),
            "periods": (ends[0], ends[-1]) if ends else None}
