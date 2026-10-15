"""財報結論 — after a company reports: how it did vs estimates, how the stock took it vs what options priced, whether
the move spread to its group (and, for ADRs, to Taiwan the next session), and what the stock did after past reports.

Everything here is measured from data (Nasdaq EPS, prices, the options-implied move saved before the report).
Headlines are listed separately as context; they never change the verdict.  Guidance and margins are NOT in these
feeds, so the verdict says so instead of guessing."""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..data.stocks import universe
from .techearn import reaction

log = logging.getLogger(__name__)
IMPLIED = DATA_DIR / "earn_implied.json"          # earn_* is kept by the site workflow's cache
ADR_TW = {"TSM": ("2330.TW", "台積電"), "UMC": ("2303.TW", "聯電"), "ASX": ("3711.TW", "日月光投控")}
BEAT = 2.0                                        # |EPS surprise| ≤ 2% counts as in line


def _series(eng, s: str) -> pd.Series:
    sp = getattr(eng, "stockprices", None)
    x = sp.series(s) if sp is not None else pd.Series(dtype=float)
    if (x is None or not len(x)) and getattr(eng, "market", None) is not None:
        x = eng.market.series(s)
    return x.dropna() if x is not None else pd.Series(dtype=float)


def next_session(px: pd.Series, d: str) -> Optional[float]:
    """Close on/before `d` → first close after `d` (a Taiwan stock reacting to a report released after its close)."""
    if not len(px):
        return None
    t = pd.Timestamp(d)
    a, b = px[px.index <= t], px[px.index > t]
    return (float(b.iloc[0]) / float(a.iloc[-1]) - 1) * 100 if len(a) and len(b) else None


def drift(px: pd.Series, d: str, n: int = 20) -> Optional[float]:
    """From the end of the 2-session reaction window to n sessions later (post-earnings drift)."""
    if not len(px):
        return None
    after = px[px.index > pd.Timestamp(d)]
    if len(after) <= n:
        return None
    return (float(after.iloc[n]) / float(after.iloc[0]) - 1) * 100


def _load_implied() -> Dict[str, Dict]:
    try:
        return json.loads(IMPLIED.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def remember_implied(eng) -> Dict[str, Dict]:
    """Save each upcoming report's options-implied move (computed by the site build) so it can be compared afterwards."""
    snap = _load_implied()
    changed = False
    for r in ((getattr(eng, "sx", None) or {}).get("earn") or []):
        if r.get("mv") is None or not r.get("date"):
            continue
        # only a quote taken BEFORE the report counts as "what options priced": the day before, or the same day for
        # after-close reports (pre-market and foreign reporters such as TSMC publish before the US open)
        qd = str(r.get("asof") or "")[:10]
        if not qd or not (qd < r["date"] or (qd == r["date"] and r.get("time") == "after")):
            continue
        k = f'{r["sym"]}|{r["date"]}'
        if (snap.get(k) or {}).get("mv") != r["mv"]:
            snap[k] = {"mv": r["mv"], "exp": r.get("exp"), "asof": r.get("asof")}
            changed = True
    cutoff = (date.today() - timedelta(days=90)).isoformat()
    for k in [k for k in snap if k.split("|")[-1] < cutoff]:
        snap.pop(k)
        changed = True
    if changed:
        try:
            tmp = IMPLIED.with_suffix(".tmp")
            tmp.write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
            tmp.replace(IMPLIED)
        except OSError as e:
            log.warning("implied-move snapshot not saved: %s", e)
    return snap


def result_of(surp: Optional[float]) -> Optional[str]:
    if surp is None:
        return None
    return "beat" if surp > BEAT else "miss" if surp < -BEAT else "inline"


RES = {"beat": ("優於預期", "Beat"), "inline": ("符合預期", "In line"), "miss": ("低於預期", "Miss")}


def verdict(r: Dict) -> Dict[str, str]:
    """Plain-language conclusion assembled only from the measured fields of `r`."""
    zh, en = [], []
    res = r.get("result")
    if res:
        zh.append(f"每股盈餘 {r['eps']:.2f}，{RES[res][0]}（預期 {r['eps_f']:.2f}，驚喜 {r['surp']:+.1f}%）")
        en.append(f"EPS {r['eps']:.2f}, {RES[res][1].lower()} (est. {r['eps_f']:.2f}, {r['surp']:+.1f}%)")
    rc = r.get("react")
    if rc is None:
        zh.append("股價反應：等公布後第一個完整交易日收盤")
        en.append("Price reaction: waiting for the first full session after the report")
    else:
        if res == "beat":
            z = ("市場買單" if rc > 1 else "優於預期但股價下跌：可能已提前反映，或市場更在意指引／毛利率（這些不在本站數據裡）" if rc < -1
                 else "優於預期但股價沒什麼反應")
        elif res == "miss":
            z = ("低於預期但股價上漲：可能利空出盡，或指引比數字好" if rc > 1 else "市場認賠" if rc < -1 else "低於預期但股價持穩")
        else:
            z = "股價上漲" if rc > 1 else "股價下跌" if rc < -1 else "股價持平"
        zh.append(f"前後兩個交易日 {rc:+.1f}%：{z}")
        en.append(f"2-session move {rc:+.1f}%")
        mv = r.get("mv")
        if mv:
            ratio = abs(rc) / mv
            zh.append(f"選擇權事前預期 ±{mv:.1f}%，實際波動是預期的 {ratio:.1f} 倍"
                      + ("（比市場預期激烈）" if ratio > 1.3 else "（比市場預期溫和）" if ratio < 0.7 else "（大致符合）"))
            en.append(f"options priced ±{mv:.1f}%; actual {ratio:.1f}×")
        elif r.get("avg_past"):
            zh.append(f"過去 4 次財報平均波動 ±{r['avg_past']:.1f}%")
    pe = r.get("peers") or {}
    if pe.get("avg") is not None and rc is not None:
        same = (pe["avg"] > 0) == (rc > 0) and abs(pe["avg"]) >= 1
        zh.append(f"同族群 {pe['n']} 檔同期平均 {pe['avg']:+.1f}%：" + ("族群同步，影響擴散到族群" if same else "族群沒有跟著動，偏個股因素"))
        en.append(f"peers ({pe['n']}) {pe['avg']:+.1f}%")
    tw = r.get("tw")
    if tw:
        zh.append(f"台股 {tw['name']}（{tw['sym'].split('.')[0]}）下一個交易日 " + (f"{tw['move']:+.1f}%" if tw.get("move") is not None else "：尚未開盤／收盤"))
    dr = r.get("drift") or {}
    if dr.get("n"):
        zh.append(f"過去 {dr['n']} 次財報後 20 個交易日：平均 {dr['avg']:+.1f}%，{dr['up']} 次上漲（樣本少，只是參考）")
        en.append(f"after past {dr['n']} reports, next 20 sessions avg {dr['avg']:+.1f}% ({dr['up']} up)")
    return {"zh": "；".join(zh) + "。", "en": "; ".join(en) + "."}


def build(eng, now: Optional[date] = None) -> Dict:
    te = getattr(eng, "techearn", None) or {}
    cal = (te.get("calendar") or {}) if isinstance(te, dict) else {}
    if not cal:
        return {"available": False}
    from .techearn import us_today
    today = (now or us_today()).isoformat()                 # the calendar is in US dates
    lo = (date.fromisoformat(today) - timedelta(days=7)).isoformat()
    uni = universe().get("us") or {}
    names, themes = uni.get("symbols", {}), uni.get("themes", {})
    implied = remember_implied(eng)
    ed = getattr(eng, "earnings", None)
    surp = (getattr(ed, "surprise", None) or {}) if ed is not None else {}
    news = (getattr(getattr(eng, "stocknews", None), "items", None) or {})
    rows: List[Dict] = []
    reported = [x for x in cal.get("past", []) if x["date"] >= lo]
    pending = [x for x in cal.get("up", []) if x["date"] <= today]
    for x in reported + pending:
        s, d = x["sym"], x["date"]
        if not x.get("cur") and (x.get("mcap") or 0) < 1e11:
            continue                                                # curated universe + $100B+ names only
        px = _series(eng, s)
        eps, eps_f = x.get("eps"), x.get("eps_f")
        sp = x.get("surp")
        if sp is None and eps is not None and eps_f:
            sp = (eps / eps_f - 1) * 100 * (1 if eps_f > 0 else -1)
        rc = x.get("react") if x.get("react") is not None else reaction(px, d)
        r = {"sym": s, "name": x.get("name") or s, "theme": themes.get(s, x.get("theme", "")), "date": d, "time": x.get("time") or "",
             "eps": eps, "eps_f": eps_f, "surp": None if sp is None else round(float(sp), 1), "result": result_of(sp) if eps is not None else None,
             "react": None if rc is None else round(float(rc), 2), "status": "reported" if eps is not None else "pending"}
        imp = implied.get(f"{s}|{d}") or {}
        r["mv"] = imp.get("mv")
        past_dates = sorted(q["date"] for q in (surp.get(s) or {}).get("rows", []) if q.get("date") and q["date"] < d)
        pr = [v for v in (reaction(px, q) for q in past_dates[-4:]) if v is not None]
        r["avg_past"] = round(float(np.mean(np.abs(pr))), 1) if pr else None
        th = themes.get(s)
        if th and rc is not None:
            moves = []
            for p in names:
                if p != s and themes.get(p) == th:
                    v = reaction(_series(eng, p), d)
                    if v is not None:
                        moves.append((p, names[p][0], round(v, 1)))
            if moves:
                moves.sort(key=lambda m: -abs(m[2]))
                r["peers"] = {"theme": th, "n": len(moves), "avg": round(float(np.mean([m[2] for m in moves])), 1), "top": moves[:5]}
        if s in ADR_TW:
            tsym, tname = ADR_TW[s]
            r["tw"] = {"sym": tsym, "name": tname, "move": next_session(_series(eng, tsym), d)}
        dd = [v for v in (drift(px, q) for q in past_dates[-8:]) if v is not None]
        if dd:
            r["drift"] = {"n": len(dd), "avg": round(float(np.mean(dd)), 1), "up": sum(1 for v in dd if v > 0)}
        t0 = pd.Timestamp(d).timestamp() - 86400
        r["news"] = [{"t": n["t"], "l": n["l"], "src": n.get("src", ""), "ts": n["ts"]}
                     for n in sorted(news.get(s, []), key=lambda n: -n.get("ts", 0)) if n.get("ts", 0) >= t0][:4]
        r["verdict"] = verdict(r) if r["status"] == "reported" else {
            "zh": "今天公布；每股盈餘等 Nasdaq 更新後才有結論" + (f"。選擇權事前預期 ±{r['mv']:.1f}%" if r.get("mv") else "") + "。",
            "en": "Reporting today; waiting for the numbers."}
        rows.append(r)
    rows.sort(key=lambda r: r["date"], reverse=True)
    return {"available": bool(rows), "asof": today, "rows": rows}
