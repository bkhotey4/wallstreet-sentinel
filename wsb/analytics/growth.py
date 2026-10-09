"""成長股估值篩選（美股＋台股）——找「營收成長快、估值相對不貴」的公司。規則計算，不是投資建議。

美股：SEC XBRL frames 的季營收（第 4 季＝全年減前三季）算近 4 季營收（TTM）與年增、最新一季年增與是否加速、毛利率、
營益率；市值來自 Nasdaq 名單。本銷比 P/S＝市值÷近 4 季營收；成長調整本銷比 PSG＝P/S÷營收年增率（%），越低代表
「每一分成長付的價格」越便宜；40 法則＝營收年增＋營益率。外國公司（SEC 沒有季報格式，例如 NU）市值夠大時用 Nasdaq 年報補。
台股：證交所／櫃買月營收的「今年累計年增」與單月年增，搭配本益比、股價淨值比、殖利率；PEG（營收版）＝本益比÷累計營收年增。

排名分數＝在合格名單內的百分位：成長 40%、成長調整估值（越低越好）40%、毛利率（台股：單月年增）10%、40 法則（台股：股價淨值比越低越好）10%。"""
from __future__ import annotations

import json
import logging
from datetime import date
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..data import earnings_data as ED
from ..data.econcal import us_today

log = logging.getLogger(__name__)
OUT_US = DATA_DIR / "growth_us.json"
OUT_TW = DATA_DIR / "growth_tw.json"


def _r(v, n=1):
    return None if v is None or not np.isfinite(v) else round(float(v), n)


def _pct(a, b):
    if a is None or b is None or b <= 0:
        return None
    return (a / b - 1) * 100


def _rank(vals: Dict[str, Optional[float]], invert: bool = False) -> Dict[str, float]:
    ok = {k: v for k, v in vals.items() if v is not None and np.isfinite(v)}
    if len(ok) < 3:
        return {k: 50.0 for k in vals}
    s = pd.Series(ok).rank(pct=True) * 100
    if invert:
        s = 100 - s + (100 / len(s))
    return {k: float(s.get(k, 50.0)) for k in vals}


def us_rows(ed, items: List[Dict], tmap: Dict[str, Dict], tech: Optional[Dict[str, Dict]] = None, today: Optional[date] = None) -> List[Dict]:
    """One row per US company with enough revenue history (frames) or a Nasdaq annual statement (fallback)."""
    today = today or us_today()
    qs = ED.cy_quarters(today, 10)
    fr = ed.frames or {}

    def val(k: str, cik: str, per: str) -> Optional[float]:
        for tag in ED.FRAME_TAGS[k]:
            v = ((fr.get(f"{tag}/{per}") or {}).get("v") or {}).get(cik)
            if v is not None:
                return v
        if per.endswith("Q4") and len(per) == 8:
            yv = val(k, cik, per[:6])
            parts = [val(k, cik, f"{per[:6]}Q{i}") for i in (1, 2, 3)]
            if yv is not None and all(p is not None for p in parts):
                return yv - sum(parts)
        return None

    tech = tech or {}
    out = []
    for it in items:
        sym, mcap = it["sym"], it.get("mcap")
        cik = str((tmap.get(sym) or tmap.get(sym.replace("-", ".")) or {}).get("cik") or "")
        row = None
        if cik:
            rev = [val("rev", cik, p) for p in qs]
            i = next((j for j, v in enumerate(rev) if v is not None), None)
            if i is not None and i + 3 < len(qs) and all(v is not None for v in rev[i:i + 4]):
                ttm = sum(rev[i:i + 4])
                prior = rev[i + 4:i + 8]
                ttm_p = sum(prior) if len(prior) == 4 and all(v is not None for v in prior) else None
                yoy = _pct(rev[i], rev[i + 4]) if i + 4 < len(rev) else None
                yoy_p = _pct(rev[i + 1], rev[i + 5]) if i + 5 < len(rev) else None
                op = [val("op", cik, p) for p in qs[i:i + 4]]
                ni = [val("ni", cik, p) for p in qs[i:i + 4]]
                gp = val("gp", cik, qs[i])
                row = {"per": qs[i][2:6] + "Q" + qs[i][-1], "ttm": ttm, "g": _pct(ttm, ttm_p) if ttm_p else yoy, "q_yoy": yoy,
                       "accel": (yoy - yoy_p) if yoy is not None and yoy_p is not None else None,
                       "gm": (gp / rev[i] * 100) if gp is not None and rev[i] else None,
                       "om": (sum(op) / ttm * 100) if all(v is not None for v in op) and ttm else None,
                       "ni": sum(ni) if all(v is not None for v in ni) else None, "src": "SEC"}
        if row is None:
            y = ((ed.nqann or {}).get(sym) or {}).get("y") or []
            if len(y) >= 2:
                a, b = y[-1], y[-2]
                row = {"per": "FY" + a["end"][:4], "ttm": a["rev"], "g": _pct(a["rev"], b["rev"]), "q_yoy": None, "accel": None,
                       "gm": (a["gp"] / a["rev"] * 100) if a.get("gp") else None, "om": (a["op"] / a["rev"] * 100) if a.get("op") is not None else None,
                       "ni": a.get("ni"), "src": "Nasdaq 年報"}
        if row is None or not row["ttm"] or row["ttm"] <= 0:
            continue
        ps = mcap / row["ttm"] if mcap else None
        g = row["g"]
        row.update({"sym": sym, "name": it.get("name", ""), "ind": it.get("ind", ""), "sub": it.get("sub", ""), "mcap": mcap, "ps": ps,
                    "psg": (ps / g) if ps is not None and g is not None and g > 0 else None,
                    "r40": (g + row["om"]) if g is not None and row.get("om") is not None else None,
                    "pe": (mcap / row["ni"]) if mcap and row.get("ni") and row["ni"] > 0 else None})
        t = tech.get(sym) or {}
        row["st"], row["tech"] = t.get("stl"), t.get("tech")
        out.append(row)
    return out


def score_us(rows: List[Dict], min_rev: float, min_g: float) -> List[Dict]:
    elig = {r["sym"]: r for r in rows if r["ttm"] >= min_rev and (r["g"] or -1) >= min_g and r.get("psg") is not None}
    g = _rank({s: r["g"] for s, r in elig.items()})
    v = _rank({s: r["psg"] for s, r in elig.items()}, invert=True)
    gm = _rank({s: r.get("gm") for s, r in elig.items()})
    r40 = _rank({s: r.get("r40") for s, r in elig.items()})
    for r in rows:
        s = r["sym"]
        r["elig"] = s in elig
        r["score"] = round(0.4 * g[s] + 0.4 * v[s] + 0.1 * gm[s] + 0.1 * r40[s], 1) if s in elig else None
        r["small"] = r["ttm"] < 50e6
    rows.sort(key=lambda r: (-(r["score"] if r["score"] is not None else -1), -(r.get("mcap") or 0)))
    rank = 0
    for r in rows:
        if r["score"] is not None:
            rank += 1
            r["rank"] = rank
    return rows


US_COLS = ["rank", "sym", "name", "ind", "sub", "mcap", "per", "ttm", "g", "q_yoy", "accel", "gm", "om", "r40", "ps", "psg", "pe", "score", "st", "tech", "src", "small"]
TW_COLS = ["rank", "code", "name", "ind", "board", "ym", "rev", "cum_yoy", "yoy", "streak", "pe", "pb", "dy", "peg", "score", "st", "cur"]


def pack(rows: List[Dict], cols: List[str], **extra) -> Dict:
    def cv(r, k):
        v = r.get(k)
        if isinstance(v, float):
            return _r(v, 0 if k in ("mcap", "ttm") else 3 if k in ("psg",) else 2 if k in ("ps", "pe", "pb") else 1)
        return v
    return {"available": bool(rows), "n": len(rows), "cols": cols, "rows": [[cv(r, k) for k in cols] for r in rows], **extra}


def tw_rows(ed, tech: Optional[Dict[str, Dict]] = None, cur: Optional[set] = None) -> List[Dict]:
    latest = ((ed.tw or {}).get("latest")) or {}
    months = ((ed.tw or {}).get("months")) or {}
    pe = ((ed.twpe or {}).get("v")) or {}
    tech, cur = tech or {}, cur or set()
    out = []
    for code, r in latest.items():
        if not r.get("rev"):
            continue
        p = pe.get(code) or {}
        streak = 0
        for ym in sorted(months, reverse=True):
            if ym > r["ym"]:
                continue
            v = (months[ym].get(code) or {}).get("yoy")
            if v is not None and v > 0:
                streak += 1
            else:
                break
        g = r.get("cum_yoy")
        peg = (p["pe"] / g) if p.get("pe") and p["pe"] > 0 and g and g > 0 else None
        t = tech.get(code) or {}
        out.append({"code": code, "name": r["name"], "ind": r["ind"], "board": r["board"], "ym": r["ym"], "rev": r["rev"] / 1e5,
                    "cum_yoy": g, "yoy": r.get("yoy"), "streak": streak, "pe": p.get("pe"), "pb": p.get("pb"), "dy": p.get("dy"),
                    "peg": peg, "st": t.get("stl"), "cur": code in cur})
    return out


def score_tw(rows: List[Dict], min_g: float, min_rev_100m: float = 1.0) -> List[Dict]:
    elig = {r["code"]: r for r in rows if (r["cum_yoy"] or -1) >= min_g and r.get("peg") is not None and r["rev"] >= min_rev_100m}
    g = _rank({s: r["cum_yoy"] for s, r in elig.items()})
    v = _rank({s: r["peg"] for s, r in elig.items()}, invert=True)
    m = _rank({s: r.get("yoy") for s, r in elig.items()})
    pb = _rank({s: r.get("pb") for s, r in elig.items()}, invert=True)
    for r in rows:
        s = r["code"]
        r["score"] = round(0.4 * g[s] + 0.4 * v[s] + 0.1 * m[s] + 0.1 * pb[s], 1) if s in elig else None
    rows.sort(key=lambda r: (-(r["score"] if r["score"] is not None else -1), -(r["rev"] or 0)))
    rank = 0
    for r in rows:
        if r["score"] is not None:
            rank += 1
            r["rank"] = rank
    return rows


def _fs_tech(mk: str) -> Dict[str, Dict]:
    """Technical status per symbol/code from the published full-market scan, if present."""
    try:
        from . import fullscan as FS
        d = FS.published(mk) or {}
        cols = d.get("cols") or []
        out = {}
        for a in d.get("rows") or []:
            o = dict(zip(cols, a))
            out[o["sym"] if mk == "us" else o["code"]] = o
        return out
    except Exception:  # noqa: BLE001
        return {}


async def write_us(ed) -> Dict:
    """Site build only: needs the full-market US list (market caps) and the SEC frames."""
    from ..data import fullmarket as FM
    from ..data.edgar_holdings import ticker_map
    c = ED.cfg()
    lists = await FM.lists()
    items = lists.get("us") or []
    tmap = await ticker_map()
    tech = _fs_tech("us")
    rows = us_rows(ed, items, tmap, tech)
    have = {r["sym"] for r in rows}
    from ..data.stocks import universe
    cur = set(((universe().get("us") or {}).get("symbols") or {}))
    need = [it["sym"] for it in sorted(items, key=lambda x: -(x.get("mcap") or 0))
            if it["sym"] not in have and ((it.get("mcap") or 0) >= float(c.get("fallback_min_mcap", 5e9)) or it["sym"] in cur)]
    if need:
        ed.nqann = await ED.refresh_nq_annual(need, float(c.get("fallback_budget_s", 90)))
        rows = us_rows(ed, items, tmap, tech)
    rows = score_us(rows, float(c.get("growth_min_rev_usd", 2e8)), float(c.get("growth_min_growth", 15)))
    res = pack(rows, US_COLS, asof=us_today().isoformat(), listed=len(items), ranked=sum(1 for r in rows if r.get("score") is not None))
    if res["available"]:
        OUT_US.write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return res


def write_tw(ed) -> Dict:
    from ..data.stocks import universe
    cur = {s.split(".")[0] for s in ((universe().get("tw") or {}).get("symbols") or {})}
    rows = score_tw(tw_rows(ed, _fs_tech("tw"), cur), float(ED.cfg().get("growth_min_growth", 15)))
    ym = max((r["ym"] for r in rows), default="")
    res = pack(rows, TW_COLS, ym=ym, ranked=sum(1 for r in rows if r.get("score") is not None))
    if res["available"]:
        OUT_TW.write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return res


def published(mk: str) -> Optional[Dict]:
    p = OUT_US if mk == "us" else OUT_TW
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    except Exception:  # noqa: BLE001
        return None
