"""今天 vs 昨天 (總覽): lists only what changed since the previous S&P 500 session across the site's main gauges.

What exists elsewhere does not cover this: the time-machine snapshots (data_cache/snap) hold no canary lights, crash odds,
spreads or yields.  So each published build upserts one small row per session into data_cache/econ_daily_changes.json
(the Actions cache keeps econ_*).  The last build of a session wins, and today's reading is compared with the newest row
of an earlier session.  An item counts as changed when a light / band changed colour, or when it moved more than its own
1σ daily change (last year of daily changes; scaled by √sessions if a build was missed).  Descriptive, not a forecast."""
from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from tools.sitekit import T, card, esc, guard_safe
from wsb.config import DATA_DIR

FILE = DATA_DIR / "econ_daily_changes.json"
KEEP = 300               # rows (about a year of sessions)
WINDOW = 252             # daily changes used for each series' own 1σ
MIN_DIFFS = 60           # fewer than this: σ of a long series is not judged
MIN_SNAP_DIFFS = 20      # σ taken from the snapshot rows themselves (gauges with no history of their own)
MAX_SHOW = 6
LIGHTS = {"ok": ("正常", "OK"), "watch": ("黃燈", "Watch"), "alert": ("紅燈", "Alert")}
RANK = {"ok": 0, "watch": 1, "alert": 2}

# key, source, id, zh, en, decimals, unit, risk (+1 up = more worry, -1 up = less, 0 neither), up meaning, down meaning (zh, en)
SERIES = (
    ("vix", "mkt", "^VIX", "VIX 恐慌指數", "VIX", 2, "", 1,
     ("市場願意付更多錢買保護，緊張程度上升。", "Investors pay more for protection."), ("買保護的需求退了，緊張程度下降。", "Demand for protection eased.")),
    ("move", "mkt", "^MOVE", "MOVE 美債波動率", "MOVE bond vol", 1, "", 1,
     ("美債價格晃得比平常大，債市不安定。", "Treasury prices are swinging more."), ("美債價格的晃動變小，債市較平靜。", "Treasury swings are calming.")),
    ("hy", "fred", "BAMLH0A0HYM2", "高收益債利差", "High-yield spread", 2, "%", 1,
     ("體質較弱的公司借錢變貴，投資人更在意違約風險。", "Weaker borrowers pay more; default worry rose."),
     ("體質較弱的公司借錢變便宜，投資人對違約較放心。", "Weaker borrowers pay less; default worry eased.")),
    ("ig", "fred", "BAMLC0A0CM", "投資級債利差", "Investment-grade spread", 2, "%", 1,
     ("連體質好的公司借錢都變貴一些，信用市場偏緊。", "Even strong borrowers pay more."), ("體質好的公司借錢變便宜，信用市場偏鬆。", "Strong borrowers pay less.")),
    ("us10y", "mkt", "^TNX", "美債 10 年殖利率", "US 10Y yield", 2, "%", 0,
     ("長天期借錢的成本上升，房貸和公司債都會感受到壓力。", "Long-term borrowing costs rose."),
     ("長天期借錢的成本下降，常見於市場轉向避險或預期降息。", "Long-term borrowing costs fell.")),
    ("twd", "mkt", "TWD=X", "美元/台幣", "USD/TWD", 2, "", 0,
     ("台幣變弱：同樣的美元要用更多台幣換，常見於資金流出。", "TWD weakened: a dollar costs more TWD."),
     ("台幣變強：同樣的美元用較少台幣就能換到，常見於資金流入。", "TWD strengthened: a dollar costs less TWD.")),
    ("dxy", "mkt", "DX-Y.NYB", "美元指數", "US Dollar Index", 2, "", 0,
     ("美元變強，對新興市場通常是壓力。", "The dollar strengthened."), ("美元變弱，新興市場的壓力通常較小。", "The dollar weakened.")),
    ("spx", "mkt", "^GSPC", "標普 500", "S&P 500", 0, "", -1,
     ("美股大盤漲幅超過平常一天的波動。", "US stocks rose more than a usual day."), ("美股大盤跌幅超過平常一天的波動。", "US stocks fell more than a usual day.")),
    ("twii", "mkt", "^TWII", "台股加權", "TAIEX", 0, "", -1,
     ("台股漲幅超過平常一天的波動。", "Taiwan stocks rose more than a usual day."), ("台股跌幅超過平常一天的波動。", "Taiwan stocks fell more than a usual day.")),
    ("oil", "mkt", "BZ=F", "布蘭特原油", "Brent crude", 2, "", 0,
     ("油價上升，通膨和運輸成本的壓力變大。", "Oil rose: more cost pressure."), ("油價下降，通膨和運輸成本的壓力變小。", "Oil fell: less cost pressure.")),
)


def load() -> List[Dict]:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = d.get("rows") if isinstance(d, dict) else None
    return sorted([r for r in rows or [] if isinstance(r, dict) and r.get("date")], key=lambda r: str(r["date"]))


def _save(rows: List[Dict]) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"rows": rows[-KEEP:]}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, FILE)


def _f(x) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _session(eng) -> Optional[str]:
    """The S&P 500 session the page describes (same key the time machine uses)."""
    try:
        d = (eng.market.q("^GSPC") or {}).get("asof")
        if not d:
            s = eng.market.series("^GSPC")
            d = s.index[-1].strftime("%Y-%m-%d") if len(s) else None
    except Exception:  # noqa: BLE001
        return None
    return str(d)[:10] if d else None


def _hist(eng, src: str, sid: str) -> pd.Series:
    try:
        return (eng.market.series(sid) if src == "mkt" else eng.fred.get(sid)).dropna()
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)


def readings(eng) -> Dict:
    """Today's values (v), band / light states (s) and FRED data dates (dt); a gauge with no data is simply absent."""
    v: Dict[str, float] = {}
    s: Dict[str, object] = {}
    dt: Dict[str, str] = {}
    st = getattr(eng, "stress", None)
    if st is not None:
        v["ssi"], s["ssi"] = round(float(st.score), 2), st.label
    for key, src, sid, *_x in SERIES:
        h = _hist(eng, src, sid)
        x = None
        if src == "mkt":
            try:
                x = _f((eng.market.q(sid) or {}).get("price"))
            except Exception:  # noqa: BLE001
                x = None
        if x is None and len(h):
            x = _f(h.iloc[-1])
        if src == "fred" and x is not None:
            dt[key] = h.index[-1].strftime("%Y-%m-%d")
        if x is not None:
            v[key] = round(x, 4)
    for h in (getattr(eng, "odds", None) or {}).get("horizons") or []:
        x = _f(h.get("adjusted"))
        if x is not None:
            v[f'crash_{h["days"]}'] = round(x, 3)
            s[f'crash_{h["days"]}'] = f'{float(h.get("drawdown_pct") or 0):.0f}'
    for r in (getattr(eng, "canary", None) or {}).get("rows") or []:
        if r.get("state") in LIGHTS:                         # warming up / stale / no data is a data gap, not a colour
            s[f'cn_{r["id"]}'] = r["state"]
    pb = getattr(eng, "playbook", None) or {}
    if pb.get("stage") is not None:
        s["stage"], s["stage_name"] = pb.get("stage"), pb.get("name")
    ol = getattr(eng, "outlook", None) or {}
    if ol.get("available") and _f(ol.get("score")) is not None:
        v["outlook"], s["outlook"] = _f(ol.get("score")), ol.get("label")
    return {"date": _session(eng), "v": v, "s": s, "dt": dt}


def record(eng) -> bool:
    """Upsert this session's row (build time).  Merged, so a feed that failed on the last build keeps its earlier value."""
    r = readings(eng)
    if not r["date"] or not r["v"]:
        return False
    rows = load()
    old = next((x for x in rows if x["date"] == r["date"]), None)
    if old:
        r = {"date": r["date"], **{k: {**(old.get(k) or {}), **r[k]} for k in ("v", "s", "dt")}}
    _save([x for x in rows if x["date"] != r["date"]] + [r])
    return True


def _crash_sigma(eng, days: int) -> Optional[float]:
    """Daily change of the shown crash probability over the last year: today's model applied to the past SSI."""
    from wsb.analytics.lab import apply_iso, predict
    from wsb.analytics.stress import ref_history
    mdl = next((h.get("base_model") for h in (getattr(eng, "lab", None) or {}).get("horizons", []) or []
                if int(h.get("days", 0)) == days and h.get("base_model")), None)
    ssi = ref_history(getattr(eng, "stress", None))
    if not mdl or ssi is None:
        return None
    x = ssi.dropna().tail(WINDOW + 1).values
    if len(x) <= MIN_DIFFS:
        return None
    raw = predict(np.array(mdl["w"]), ((x - 50) / 20.0).reshape(-1, 1))
    return float(np.std(np.diff(apply_iso((np.array(mdl["cal"][0]), np.array(mdl["cal"][1])), raw) * 100), ddof=1))


def _snap_sigma(rows: List[Dict], key: str) -> Optional[float]:
    x = [_f((r.get("v") or {}).get(key)) for r in rows]
    x = [a for a in x if a is not None]
    return float(np.std(np.diff(x[-(WINDOW + 1):]), ddof=1)) if len(x) > MIN_SNAP_DIFFS else None


def sigmas(eng, rows: List[Dict], keys) -> Dict[str, float]:
    """Each gauge's own 1σ daily change, from its history; gauges without one use the snapshot rows once there are enough."""
    out: Dict[str, Optional[float]] = {}
    for key, src, sid, *_x in SERIES:
        d = _hist(eng, src, sid).diff().dropna().tail(WINDOW)
        out[key] = float(d.std()) if len(d) >= MIN_DIFFS else None
    try:
        from wsb.analytics.stress import ref_history
        h = ref_history(getattr(eng, "stress", None))
        d = h.dropna().diff().dropna().tail(WINDOW) if h is not None else ()
        out["ssi"] = float(d.std()) if len(d) >= MIN_DIFFS else None
    except Exception:  # noqa: BLE001
        out["ssi"] = None
    for k in keys:
        if k.startswith("crash_"):
            try:
                out[k] = _crash_sigma(eng, int(k.split("_")[1]))
            except Exception:  # noqa: BLE001
                out[k] = None
    for k in keys:
        if out.get(k) is None:
            out[k] = _snap_sigma(rows, k)
    return {k: v for k, v in out.items() if v is not None}


def _fmt(x: float, d: int, u: str) -> str:
    return f"{x:,.{d}f}{u}"


def _meta(key: str, cur: Dict) -> Optional[Tuple]:
    """zh, en, decimals, unit, risk, up meaning, down meaning of a numeric gauge."""
    for k, _s, _i, zh, en, d, u, risk, up, dn in SERIES:
        if k == key:
            return zh, en, d, u, risk, up, dn
    if key == "ssi":
        return ("SSI 壓力指數", "Stress index (SSI)", 1, "", 1, ("金融市場的整體壓力比昨天高。", "Overall market stress rose."),
                ("金融市場的整體壓力比昨天低。", "Overall market stress fell."))
    if key == "outlook":
        return ("全方位風險分數", "Risk outlook score", 1, "", 1, ("把多個面向加總後的風險比昨天高。", "Combined risk rose."),
                ("把多個面向加總後的風險比昨天低。", "Combined risk fell."))
    if key.startswith("crash_"):
        days, dd = key.split("_")[1], (cur.get("s") or {}).get(key) or "?"
        return (f"崩跌機率（{days} 日內跌 ≥{dd}%）", f"Crash odds ({days}d, ≥{dd}%)", 1, "%", 1,
                ("模型估的大跌機率上升，比昨天更需要留意。", "The estimated odds of a sharp fall rose."),
                ("模型估的大跌機率下降，比昨天稍微放鬆。", "The estimated odds of a sharp fall eased."))
    return None


def _numeric(cur: Dict, prev: Dict, sig: Dict, gap: int, out: Dict) -> None:
    cv, pv, cs, ps = cur.get("v") or {}, prev.get("v") or {}, cur.get("s") or {}, prev.get("s") or {}
    for k, x in cv.items():
        p, x, m = _f(pv.get(k)), _f(x), _meta(k, cur)
        if x is None or p is None or m is None:
            continue
        zh, en, d, u, risk, up, dn = m
        if k in (cur.get("dt") or {}) and cur["dt"][k] == (prev.get("dt") or {}).get(k):
            out["same"].append(zh)                           # FRED has not published a newer day yet
            continue
        delta, s = x - p, sig.get(k)
        band = bool(k in ("ssi", "outlook") and cs.get(k) and ps.get(k) and cs[k] != ps[k])
        thr = None if s is None else s * math.sqrt(gap)
        out["table"].append((zh, en, _fmt(p, d, u), _fmt(x, d, u), f"{delta:+,.{d}f}", "—" if s is None else f"{s:,.{max(d, 2)}f}"))
        if thr is None and not band:
            out["unknown"].append(zh)
        elif band or (delta != 0 and abs(delta) > thr):
            mz, me = up if delta > 0 else dn
            if band:
                mz, me = f"區間從「{ps[k]}」變成「{cs[k]}」。{mz}", f"Band changed. {me}"
            out["items"].append({"key": k, "zh": zh, "en": en, "was": _fmt(p, d, u) + (f"（{ps[k]}）" if band else ""),
                                 "now": _fmt(x, d, u) + (f"（{cs[k]}）" if band else ""), "mz": mz, "me": me,
                                 "risk": (1 if delta > 0 else -1) * risk, "band": band, "z": abs(delta) / s if s else 0.0})
        else:
            out["same"].append(zh)


def _lights(eng, cur: Dict, prev: Dict, out: Dict) -> None:
    cs, ps = cur.get("s") or {}, prev.get("s") or {}
    for r in (getattr(eng, "canary", None) or {}).get("rows") or []:
        k = f'cn_{r["id"]}'
        a, b = ps.get(k), cs.get(k)
        if a not in LIGHTS or b not in LIGHTS:
            continue
        if a == b:
            out["same"].append(str(r.get("zh")))
            continue
        worse = RANK[b] > RANK[a]
        out["items"].append({"key": k, "zh": str(r.get("zh")), "en": str(r.get("en") or r.get("zh")), "was": LIGHTS[a][0], "now": LIGHTS[b][0],
                             "mz": ("燈號變差。" if worse else "燈號好轉。") + str(r.get("why") or ""),
                             "me": "The light turned worse." if worse else "The light improved.", "risk": 1 if worse else -1, "band": True, "z": 0.0})
    if cs.get("stage") is None or ps.get("stage") is None:
        return
    if cs["stage"] == ps["stage"]:
        out["same"].append("風險劇本")
        return
    a, b = _f(ps["stage"]), _f(cs["stage"])
    worse = None if a is None or b is None else b > a
    out["items"].append({"key": "stage", "zh": "風險劇本", "en": "Risk playbook", "was": str(ps.get("stage_name") or ps["stage"]),
                         "now": str(cs.get("stage_name") or cs["stage"]),
                         "mz": "市場走到比較緊張的階段。" if worse else "市場回到比較緩和的階段。" if worse is False else "市場所處的階段變了。",
                         "me": "The stage changed.", "risk": 0 if worse is None else 1 if worse else -1, "band": True, "z": 0.0})


def compare(eng, cur: Dict, prev: Dict, rows: List[Dict]) -> Dict:
    """Changed items (light or band first, then by size), plus what stayed the same and what cannot be judged yet."""
    try:
        gap = max(1, int(np.busday_count(prev["date"], cur["date"])))
    except Exception:  # noqa: BLE001
        gap = 1
    out: Dict = {"items": [], "same": [], "unknown": [], "table": [], "gap": gap}
    _numeric(cur, prev, sigmas(eng, rows, list(cur.get("v") or {})), gap, out)
    _lights(eng, cur, prev, out)
    out["items"].sort(key=lambda i: (not i["band"], -i["risk"], -i["z"]))
    return out


def _e(x) -> str:
    return esc(guard_safe(str(x)))


def _li(i: Dict) -> str:
    c = "dn" if i["risk"] > 0 else "up" if i["risk"] < 0 else ""
    return (f'<li><b class="{c}">{T(guard_safe(i["zh"]), i["en"])}</b>：{_e(i["was"])} → <b>{_e(i["now"])}</b>'
            f'<div class="small muted">{T(guard_safe(i["mz"]), i["me"])}</div></li>')


def _waiting(n: int) -> str:
    body = (f'<p class="rimp big2"><b>{T("一句話看懂：資料累積中，要有兩天的紀錄才比得出今天和昨天差在哪。", "In short: still collecting. Two sessions are needed to compare.")}</b></p>'
            f'<p class="note">{T(f"目前已存 {n} 天的紀錄。每次網站更新會記下當天的主要指標，下一個交易日起這裡就會列出變化。", f"{n} session(s) saved so far.")}</p>')
    return card("今天 vs 昨天：變化總表", "Today vs yesterday: what changed", body, "wide")


def sec_changes(eng) -> str:
    rows, cur = load(), readings(eng)
    prior = [r for r in rows if cur["date"] and str(r["date"]) < cur["date"]]
    if not prior:
        return _waiting(len(rows))
    prev = prior[-1]
    c = compare(eng, cur, prev, prior)
    its = c["items"]
    n, bad, good = len(its), sum(i["risk"] > 0 for i in its), sum(i["risk"] < 0 for i in its)
    pd_, when = prev["date"][5:], f'{prev["date"][5:]} → {cur["date"][5:]}'
    if n:
        lz = f"一句話看懂：今天有 {n} 項變了（和 {pd_} 比），{bad} 項偏向風險升高、{good} 項偏向風險降低。"
        le = f"In short: {n} item(s) changed since {pd_}: {bad} riskier, {good} calmer."
    else:
        lz = f"一句話看懂：今天沒有明顯變化（和 {pd_} 比），燈號都沒換，數字也都在各自平常一天的波動內。"
        le = f"In short: nothing notable since {pd_}."
    more = f'<ul class="lines">{"".join(_li(i) for i in its[MAX_SHOW:])}</ul>' if len(its) > MAX_SHOW else ""
    tr = "".join(f'<tr><td>{T(a, b)}</td><td class="r">{_e(x)}</td><td class="r">{_e(y)}</td><td class="r">{_e(d)}</td><td class="r">{_e(s)}</td></tr>'
                 for a, b, x, y, d, s in c["table"])
    same = guard_safe("、".join(dict.fromkeys(c["same"])))
    gapz = f"中間少了紀錄，相隔 {c['gap']} 個交易日，門檻已按天數放大。" if c["gap"] > 1 else ""
    body = (f'<p class="rimp big2"><b>{T(lz, le)}</b></p>'
            + (f'<ul class="lines">{"".join(_li(i) for i in its[:MAX_SHOW])}</ul>' if its else "")
            + f'<details class="sgx"><summary>{T("細節：比較日期、門檻和沒變的項目", "Details")}</summary>{more}'
            + f'<p class="small">{T(f"比較 {when}。{gapz}", f"Compared {when}.")}</p>'
            + (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("指標", "Gauge")}</th><th class="r">{T("前次", "Before")}</th><th class="r">{T("今天", "Now")}</th>'
               f'<th class="r">{T("變動", "Change")}</th><th class="r">{T("平常一天的波動（1σ）", "Usual day (1σ)")}</th></tr></thead><tbody>{tr}</tbody></table></div>' if tr else "")
            + (f'<p class="small">{T("沒變的項目：" + same, "Unchanged: " + same)}</p>' if same else "")
            + (f'<p class="small muted">{T("還判斷不了（歷史太短，算不出平常波動）：" + "、".join(c["unknown"]), "Cannot judge yet: " + ", ".join(c["unknown"]))}</p>' if c["unknown"] else "")
            + f'<p class="note">{T("燈號或區間換顏色一定列出；數字要超過自己近一年平常一天的變動（1σ）才列出，所以每個指標的門檻都不一樣。這裡只描述變化，不是預測，也不構成投資建議。", "A light or band change is always listed; a number must move more than its own 1σ daily change over the past year. Descriptive only, not advice.")}</p></details>')
    return card("今天 vs 昨天：變化總表", "Today vs yesterday: what changed", body, "wide")
