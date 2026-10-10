"""科技與半導體財報分析（規則計算，不是投資建議）。

每家公司：最新一季營收、年增率與是否加速、毛利率／營益率與年變化、EPS 與年增、近 4 季 EPS 相對預期、財報前後兩日股價
波動、下一次財報日與 EPS 預期，再把這些換成精選池內的百分位，合成「財報動能分數」。另外產出：族群彙總、本季財報季
計分板、美股財報日曆、全市場美股科技股最新一季表（SEC frames）、台股電子業月營收表。"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..data import earnings_data as ED
from ..data.econcal import us_today
from ..data.stocks import universe

log = logging.getLogger(__name__)
OUT_US = DATA_DIR / "earn_ustech.json"
OUT_TW = DATA_DIR / "earn_twrev_table.json"


def _pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0 or not np.isfinite(a) or not np.isfinite(b):
        return None
    if b < 0 and a >= 0:
        return None                                   # loss → profit: growth % is meaningless
    return (a / b - 1) * 100 * (1 if b > 0 else -1)


def _ratio(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return None if a is None or b is None or not b else a / b * 100


def _ago(rows: List[Dict], end: str, days: int = 365, tol: int = 25) -> Optional[Dict]:
    e = date.fromisoformat(end)
    best, bd = None, tol + 1
    for r in rows:
        d = abs((e - date.fromisoformat(r["end"])).days - days)
        if d <= tol and d < bd:
            best, bd = r, d
    return best


def metrics(q: List[Dict]) -> Dict:
    """Latest-quarter metrics from a quarterly table (oldest first)."""
    q = [r for r in q if r.get("rev")]
    if not q:
        return {}
    L = q[-1]
    P = q[-2] if len(q) > 1 else None
    Y = _ago(q, L["end"])
    PY = _ago(q, P["end"]) if P else None
    gm = lambda r: _ratio((r or {}).get("gp"), (r or {}).get("rev"))  # noqa: E731
    om = lambda r: _ratio((r or {}).get("op"), (r or {}).get("rev"))  # noqa: E731
    yoy = _pct(L["rev"], (Y or {}).get("rev"))
    yoy_p = _pct((P or {}).get("rev"), (PY or {}).get("rev"))
    m = {"end": L["end"], "rev": L["rev"], "rev_yoy": yoy, "rev_qoq": _pct(L["rev"], (P or {}).get("rev")),
         "accel": (yoy - yoy_p) if yoy is not None and yoy_p is not None else None,
         "gm": gm(L), "gm_yoy": (gm(L) - gm(Y)) if gm(L) is not None and gm(Y) is not None else None,
         "gm_qoq": (gm(L) - gm(P)) if gm(L) is not None and gm(P) is not None else None,
         "om": om(L), "om_yoy": (om(L) - om(Y)) if om(L) is not None and om(Y) is not None else None,
         "nm": _ratio(L.get("ni"), L["rev"]), "eps": L.get("eps"), "eps_yoy": _pct(L.get("eps"), (Y or {}).get("eps")),
         "rnd": _ratio(L.get("rnd"), L["rev"]),
         "inv_qoq": _pct(L.get("inv"), (P or {}).get("inv")), "src": L.get("src", "sec")}
    m["series"] = [{"end": r["end"], "rev": r["rev"], "gm": gm(r), "om": om(r), "yoy": _pct(r["rev"], (_ago(q, r["end"]) or {}).get("rev"))}
                   for r in q[-8:]]
    return m


def reaction(px: pd.Series, d: str) -> Optional[float]:
    """Two-session window around a report date (covers both pre-market and after-close reports)."""
    if px is None or not len(px):
        return None
    t = pd.Timestamp(d)
    before = px[px.index < t]
    after = px[px.index > t]
    if not len(before) or not len(after):
        return None
    return (float(after.iloc[0]) / float(before.iloc[-1]) - 1) * 100


def tags(m: Dict, s: Dict) -> List[Tuple[str, str]]:
    """Plain-language flags: (中文, tone) with tone up / dn / mu."""
    out = []
    y = m.get("rev_yoy")
    if y is not None:
        out.append(("營收高速成長" if y >= 30 else "營收成長" if y >= 10 else "營收持平" if y >= -3 else "營收衰退",
                    "up" if y >= 10 else "mu" if y >= -3 else "dn"))
    a = m.get("accel")
    if a is not None and a >= 3:
        out.append((f"成長加速 +{a:.0f}pp", "up"))
    elif a is not None and a <= -5:
        out.append((f"成長放緩 {a:.0f}pp", "dn"))
    g = m.get("gm_yoy")
    if g is not None and g >= 1:
        out.append((f"毛利率擴張 +{g:.1f}pp", "up"))
    elif g is not None and g <= -1:
        out.append((f"毛利率壓縮 {g:.1f}pp", "dn"))
    o = m.get("om_yoy")
    if o is not None and o >= 1.5:
        out.append((f"營益率擴張 +{o:.1f}pp", "up"))
    elif o is not None and o <= -1.5:
        out.append((f"營益率壓縮 {o:.1f}pp", "dn"))
    iv, rq = m.get("inv_qoq"), m.get("rev_qoq")
    if iv is not None and rq is not None and iv - rq >= 10:
        out.append((f"庫存季增 {iv:.0f}% 高於營收", "dn"))
    if s.get("n") and s.get("beats") == s.get("n") and s["n"] >= 4:
        out.append(("連 4 季 EPS 優於預期", "up"))
    elif s.get("last") is not None and s["last"] < 0:
        out.append(("最近一季 EPS 低於預期", "dn"))
    return out


def _rank(vals: Dict[str, Optional[float]]) -> Dict[str, float]:
    ok = {k: v for k, v in vals.items() if v is not None and np.isfinite(v)}
    if len(ok) < 3:
        return {k: 50.0 for k in vals}
    s = pd.Series(ok).rank(pct=True) * 100
    return {k: float(s.get(k, 50.0)) for k in vals}


W = {"rev_yoy": 0.30, "accel": 0.15, "gm_yoy": 0.15, "om_yoy": 0.10, "eps_yoy": 0.15, "surp": 0.15}


def _cal_index(days: Dict[str, Dict]) -> Dict[str, List[Tuple[str, Dict]]]:
    idx: Dict[str, List[Tuple[str, Dict]]] = {}
    for d, rec in sorted(days.items()):
        for r in rec.get("rows", []):
            idx.setdefault(r["sym"], []).append((d, r))
    return idx


def build(eng) -> Dict:
    ed = getattr(eng, "earnings", None)
    if ed is None:
        return {"available": False}
    uni = universe().get("us") or {}
    names, themes = uni.get("symbols", {}), uni.get("themes", {})
    tech = [s for s in names if themes.get(s) in ED.TECH_THEMES]
    today = us_today().isoformat()
    cal = _cal_index(ed.days or {})
    sp = getattr(eng, "stockprices", None)
    rows, raw = [], {}
    for s in tech:
        f = (ed.facts or {}).get(s) or {}
        m = metrics(f.get("q") or [])
        su = [r for r in ((ed.surprise or {}).get(s) or {}).get("rows", []) if r.get("surp") is not None]
        px = sp.series(s) if sp is not None else None
        reacts = [x for x in (reaction(px, r["date"]) for r in su if r.get("date")) if x is not None]
        sinfo = {"n": len(su), "beats": sum(1 for r in su if r["surp"] > 0), "avg": float(np.mean([r["surp"] for r in su])) if su else None,
                 "last": su[0]["surp"] if su else None, "last_date": su[0]["date"] if su else None, "rows": su[:4],
                 "react_avg": float(np.mean(np.abs(reacts))) if reacts else None, "react_last": reacts[0] if reacts else None}
        fut = [(d, r) for d, r in cal.get(s, []) if d >= today]
        past = [(d, r) for d, r in cal.get(s, []) if d < today]
        nxt = fut[0] if fut else None
        zh, en = names[s]
        row = {"sym": s, "name": zh, "name_en": en, "theme": themes.get(s, ""), **{k: v for k, v in m.items()}, "s": sinfo,
               "next": ({"date": nxt[0], "time": nxt[1]["time"], "eps_f": nxt[1]["eps_f"], "n_est": nxt[1]["n_est"],
                         "eps_ly": nxt[1]["eps_ly"], "g": _pct(nxt[1]["eps_f"], nxt[1]["eps_ly"])} if nxt else None),
               "last_rep": (sinfo["last_date"] or (past[-1][0] if past else None))}
        row["tags"] = tags(m, sinfo)
        rows.append(row)
        raw[s] = {"rev_yoy": m.get("rev_yoy"), "accel": m.get("accel"), "gm_yoy": m.get("gm_yoy"), "om_yoy": m.get("om_yoy"),
                  "eps_yoy": m.get("eps_yoy"), "surp": sinfo["avg"]}
    ranks = {k: _rank({s: raw[s][k] for s in raw}) for k in W}
    for r in rows:
        have = [k for k in W if raw[r["sym"]][k] is not None]
        r["score"] = round(sum(W[k] * ranks[k][r["sym"]] for k in W) / sum(W.values()), 1) if len(have) >= 3 else None
        r["verdict"] = verdict(r)
    rows.sort(key=lambda r: -(r["score"] or -1))
    groups = []
    for th in ED.TECH_THEMES:
        g = [r for r in rows if r["theme"] == th]
        if not g:
            continue
        med = lambda k: (float(np.median([x[k] for x in g if x.get(k) is not None])) if any(x.get(k) is not None for x in g) else None)  # noqa: E731
        lastq = [x for x in g if x["s"]["last"] is not None]
        groups.append({"theme": th, "n": len(g), "rev_yoy": med("rev_yoy"), "gm_yoy": med("gm_yoy"), "om": med("om"),
                       "beat": (sum(1 for x in lastq if x["s"]["last"] > 0) / len(lastq) * 100) if lastq else None,
                       "score": med("score"), "leaders": [x["name"] for x in g if x.get("score") is not None][:3]})
    lo = (date.fromisoformat(today) - timedelta(days=45)).isoformat()
    season = [r for r in rows if (r["s"]["last_date"] or "") >= lo]
    board = {"n": len(season), "beats": sum(1 for r in season if (r["s"]["last"] or 0) > 0),
             "avg_surp": float(np.mean([r["s"]["last"] for r in season])) if season else None,
             "avg_react": float(np.mean([r["s"]["react_last"] for r in season if r["s"]["react_last"] is not None]))
             if any(r["s"]["react_last"] is not None for r in season) else None,
             "rev_yoy": float(np.median([r["rev_yoy"] for r in season if r.get("rev_yoy") is not None]))
             if any(r.get("rev_yoy") is not None for r in season) else None}
    return {"available": bool(rows), "asof": today, "rows": rows, "groups": groups, "season": board,
            "calendar": calendar_view(ed, names, themes, sp, today), "tw": tw_summary(ed), "ustech_n": _ustech_count()}


def verdict(r: Dict) -> str:
    """One rule-based sentence (data only)."""
    p = []
    if r.get("rev_yoy") is not None:
        acc = r.get("accel")
        p.append(f"營收年增 {r['rev_yoy']:.0f}%" + (f"（較上季{'加速' if acc >= 0 else '放緩'} {abs(acc):.0f}pp）" if acc is not None else ""))
    if r.get("gm") is not None:
        p.append(f"毛利率 {r['gm']:.1f}%" + (f"（年變化 {r['gm_yoy']:+.1f}pp）" if r.get("gm_yoy") is not None else ""))
    if r.get("om") is not None:
        p.append(f"營益率 {r['om']:.1f}%")
    s = r["s"]
    if s.get("n"):
        p.append(f"近 {s['n']} 季 EPS 有 {s['beats']} 季優於預期（平均 {s['avg']:+.0f}%）")
    if s.get("react_avg") is not None:
        p.append(f"財報前後兩日平均波動 ±{s['react_avg']:.1f}%")
    return "，".join(p)


def calendar_view(ed, names: Dict, themes: Dict, sp, today: str) -> Dict:
    """Upcoming (21 days) and recent (7 days) reports: the curated universe plus any US company ≥ the size floor."""
    floor = float(ED.cfg().get("cal_min_mcap", 20e9))
    lo = (date.fromisoformat(today) - timedelta(days=7)).isoformat()
    hi = (date.fromisoformat(today) + timedelta(days=21)).isoformat()
    up, past = [], []
    for d, rec in sorted((ed.days or {}).items()):
        if not (lo <= d <= hi):
            continue
        for r in rec.get("rows", []):
            cur = r["sym"] in names
            if not cur and (r.get("mcap") or 0) < floor:
                continue
            x = {"date": d, "sym": r["sym"], "name": names[r["sym"]][0] if cur else r["name"], "cur": cur,
                 "theme": themes.get(r["sym"], ""), "time": r["time"], "eps_f": r["eps_f"], "n_est": r["n_est"], "eps_ly": r["eps_ly"],
                 "g": _pct(r["eps_f"], r["eps_ly"]), "mcap": r.get("mcap"), "eps": r.get("eps"), "surp": r.get("surprise"),
                 "tech": themes.get(r["sym"], "") in ED.TECH_THEMES}
            if d < today or r.get("eps") is not None:
                if cur and sp is not None:
                    x["react"] = reaction(sp.series(r["sym"]), d)
                past.append(x)
            else:
                up.append(x)
    up.sort(key=lambda x: (x["date"], -(x["mcap"] or 0)))
    past.sort(key=lambda x: (x["date"], -(x["mcap"] or 0)), reverse=True)
    return {"up": up, "past": past}


# ------------------------------------------------------------------ whole-market US tech (SEC frames)
def _q_label(cy: str) -> str:
    return cy[2:6] + "Q" + cy[-1]


def ustech(ed, items: List[Dict], tmap: Dict[str, Dict], today: Optional[date] = None) -> Dict:
    """Latest calendar quarter per company from SEC frames; Q4 derived from the calendar-year frame minus Q1–Q3."""
    today = today or us_today()
    qs = ED.cy_quarters(today, 7)
    val = ED.FrameReader(ed.frames or {}, qs).val

    cols = ["sym", "name", "sub", "mcap", "q", "rev", "yoy", "qoq", "gm", "gm_yoy", "om", "nm", "eps", "eps_yoy"]
    out = []
    for it in items:
        cik = str((tmap.get(it["sym"]) or tmap.get(it["sym"].replace("-", ".")) or {}).get("cik") or "")
        if not cik:
            continue
        per = next((p for p in qs if val("rev", cik, p) is not None), None)
        if per is None:
            continue
        i = qs.index(per)
        prev_y = f"CY{int(per[2:6]) - 1}Q{per[-1]}"
        prev_q = qs[i + 1] if i + 1 < len(qs) else None
        rev = val("rev", cik, per)
        ry, rq = val("rev", cik, prev_y), (val("rev", cik, prev_q) if prev_q else None)
        gp, op, ni, eps = val("gp", cik, per), val("op", cik, per), val("ni", cik, per), val("eps", cik, per)
        gpy = val("gp", cik, prev_y)
        gm, gmy = _ratio(gp, rev), _ratio(gpy, ry)
        out.append({"sym": it["sym"], "name": it.get("name", ""), "sub": it.get("sub", ""), "mcap": it.get("mcap"), "q": _q_label(per),
                    "rev": rev, "yoy": _pct(rev, ry), "qoq": _pct(rev, rq), "gm": gm, "gm_yoy": (gm - gmy) if gm is not None and gmy is not None else None,
                    "om": _ratio(op, rev), "nm": _ratio(ni, rev), "eps": eps, "eps_yoy": _pct(eps, val("eps", cik, prev_y))})
    out.sort(key=lambda r: -(r.get("mcap") or 0))
    rnd = lambda v, n: None if v is None or not np.isfinite(v) else round(float(v), n)  # noqa: E731
    rows = [[r["sym"], r["name"], r["sub"], rnd(r["mcap"], 0), r["q"], rnd(r["rev"], 0), rnd(r["yoy"], 1), rnd(r["qoq"], 1), rnd(r["gm"], 1),
             rnd(r["gm_yoy"], 1), rnd(r["om"], 1), rnd(r["nm"], 1), rnd(r["eps"], 2), rnd(r["eps_yoy"], 1)] for r in out]
    return {"available": bool(rows), "asof": today.isoformat(), "n": len(rows), "listed": len(items), "cols": cols, "rows": rows}


def _ustech_count() -> int:
    try:
        return int(json.loads(OUT_US.read_text(encoding="utf-8")).get("n", 0)) if OUT_US.exists() else 0
    except Exception:  # noqa: BLE001
        return 0


async def write_ustech(ed) -> Dict:
    """Build + store the whole-market US tech table (site build only; needs the full-market list)."""
    from ..data import fullmarket as FM
    from ..data.edgar_holdings import ticker_map
    lists = await FM.lists()
    items = [x for x in (lists.get("us") or []) if x.get("ind") == "科技"]
    res = ustech(ed, items, await ticker_map())
    if res.get("available"):
        OUT_US.write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return res


# ------------------------------------------------------------------ Taiwan monthly revenue
def tw_table(ed) -> Dict:
    arc = ed.tw or {}
    latest, months = arc.get("latest") or {}, arc.get("months") or {}
    cur_tw = {s.split(".")[0] for s in ((universe().get("tw") or {}).get("symbols") or {})}
    cols = ["code", "name", "ind", "board", "ym", "rev", "mom", "yoy", "cum_yoy", "streak", "cur"]
    rows = []
    for code, r in latest.items():
        if r["ind"] not in ED.TW_ELEC:
            continue
        streak = 0
        for ym in sorted(months, reverse=True):
            v = (months[ym].get(code) or {}).get("yoy")
            if ym > r["ym"]:
                continue
            if v is not None and v > 0:
                streak += 1
            else:
                break
        rnd = lambda v, n: None if v is None else round(float(v), n)  # noqa: E731
        rows.append([code, r["name"], r["ind"], r["board"], r["ym"], rnd((r["rev"] or 0) / 1e5, 2), rnd(r["mom"], 1), rnd(r["yoy"], 1),
                     rnd(r["cum_yoy"], 1), streak, code in cur_tw])
    rows.sort(key=lambda x: -(x[5] or 0))
    return {"available": bool(rows), "n": len(rows), "cols": cols, "rows": rows, "months_archived": len(months)}


def tw_summary(ed) -> Dict:
    """Industry roll-up (sum of this month vs the same month last year) + the curated names' latest month."""
    latest = (ed.tw or {}).get("latest") or {}
    if not latest:
        return {"available": False}
    agg: Dict[str, List[float]] = {}
    for r in latest.values():
        if r["ind"] in ED.TW_ELEC and r.get("rev") and r.get("ly"):
            a = agg.setdefault(r["ind"], [0.0, 0.0, 0])
            a[0] += r["rev"]
            a[1] += r["ly"]
            a[2] += 1
    inds = sorted([{"ind": k, "n": v[2], "rev": v[0] / 1e5, "yoy": (v[0] / v[1] - 1) * 100 if v[1] else None} for k, v in agg.items()],
                  key=lambda x: -x["rev"])
    tw_u = universe().get("tw") or {}
    uni, th = tw_u.get("symbols") or {}, tw_u.get("themes") or {}
    cur = []
    for s, (zh, en) in uni.items():
        if th.get(s) not in ("半導體", "AI伺服器與雲端", "電子零組件"):
            continue
        r = latest.get(s.split(".")[0])
        if r:
            cur.append({"code": r["code"], "name": zh, "ym": r["ym"], "rev": (r["rev"] or 0) / 1e5, "mom": r["mom"], "yoy": r["yoy"],
                        "cum_yoy": r["cum_yoy"]})
    cur.sort(key=lambda x: -(x["yoy"] if x["yoy"] is not None else -999))
    ym = max((r["ym"] for r in latest.values()), default="")
    return {"available": True, "ym": ym, "industries": inds, "curated": cur}


def write_tw(ed) -> Dict:
    res = tw_table(ed)
    if res.get("available"):
        OUT_TW.write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return res


def summary_lines(res: Dict) -> List[str]:
    if not res or not res.get("available"):
        return []
    L = []
    b = res["season"]
    if b.get("n"):
        L.append(f"科技／半導體財報季：精選池近 45 天 {b['n']} 家公布，{b['beats']} 家 EPS 優於預期，營收年增中位數 "
                 + (f"{b['rev_yoy']:.0f}%" if b.get("rev_yoy") is not None else "—"))
    for g in res["groups"]:
        L.append(f"{g['theme']}：營收年增中位數 " + (f"{g['rev_yoy']:.0f}%" if g.get("rev_yoy") is not None else "—")
                 + "，毛利率年變化中位數 " + (f"{g['gm_yoy']:+.1f}pp" if g.get("gm_yoy") is not None else "—")
                 + "；動能領先：" + "、".join(g["leaders"]))
    up = [x for x in res["calendar"]["up"] if x["tech"]][:8]
    if up:
        L.append("即將公布的科技財報：" + "、".join(f"{x['date'][5:]} {x['name']}（EPS 預期 {x['eps_f']}）" for x in up))
    return L
