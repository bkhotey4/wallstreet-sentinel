"""產業簡報 — 美國 11 個產業各自的處境：股價相對大盤、這一季財報、背後的實體經濟數據，再用固定規則寫成判讀。

Three independent reads per sector, each scored −1 / 0 / +1:
  * 股價: the sector ETF's 3-month return minus the S&P 500's (±3 pp), plus 1-month, YTD, distance from the 52-week high
    and the 200-day average for context;
  * 財報: this season's reports from the sector's members (SPDR holdings) — share beating the estimate against the whole
    market's share (±10 pp) and the median EPS change from a year ago (≥ +15 % / < 0);
  * 經濟數據: the official series that drive the sector (FRED, read by real_economy.one: one-year change and whether it
    sits in the outer quarter of its ten years) plus a few market prices (oil, copper, 10-year yield, sub-industry ETFs).
Sum ≥ +2 → 順風, ≤ −2 → 逆風, else 中性; when price and earnings point opposite ways the text says so.
A daily snapshot of every sector's score is kept (earn_sector_brief_hist.json) so the page can show the change since a
week ago.  Descriptive rules on public data — not a forecast, not a recommendation."""
from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS
from . import real_economy as RX

log = logging.getLogger(__name__)
HIST = DATA_DIR / "earn_sector_brief_hist.json"
DAYS = DATA_DIR / "earn_days.json"

# kind: fred = real_economy.one (one-year change vs its 10 years) · fchg = FRED level change over ~3 months (pp)
#       px = 3-month % change of a price · rel = 3-month return of an ETF minus the S&P 500 · ssi = market stress level
DRIVERS: Dict[str, List[Dict]] = {
    "XLK": [{"k": "fred", "id": "IPG3344S", "zh": "半導體與電子零件產出", "good": "up", "kind": "pct"},
            {"k": "fred", "id": "PCU334413334413", "zh": "半導體出廠價格", "good": "up", "kind": "pct"},
            {"k": "rel", "id": "SMH", "zh": "半導體股相對大盤"}, {"k": "rel", "id": "IGV", "zh": "軟體股相對大盤"}],
    "XLC": [{"k": "fred", "id": "RSAFS", "zh": "零售銷售（廣告需求的背景）", "good": "up", "kind": "pct"},
            {"k": "fred", "id": "UMCSENT", "zh": "消費者信心", "good": "up", "kind": "pct"}],
    "XLY": [{"k": "fred", "id": "RSAFS", "zh": "零售銷售", "good": "up", "kind": "pct"},
            {"k": "fred", "id": "UMCSENT", "zh": "消費者信心", "good": "up", "kind": "pct"},
            {"k": "fred", "id": "DRCCLACBS", "zh": "信用卡逾期率", "good": "down", "kind": "diff"},
            {"k": "rel", "id": "XHB", "zh": "住宅建商相對大盤"}],
    "XLP": [{"k": "ssi", "zh": "市場壓力（防禦股相對受惠）"},
            {"k": "fred", "id": "UMCSENT", "zh": "消費者信心", "good": "up", "kind": "pct"}],
    "XLV": [{"k": "ssi", "zh": "市場壓力（防禦股相對受惠）"}],
    "XLF": [{"k": "fred", "id": "TOTLL", "zh": "銀行放款總額", "good": "up", "kind": "pct"},
            {"k": "fred", "id": "DRALACBN", "zh": "全部貸款逾期率", "good": "down", "kind": "diff"},
            {"k": "fred", "id": "T10Y2Y", "zh": "殖利率曲線（10 年−2 年）", "good": "up", "kind": "diff"},
            {"k": "rel", "id": "KRE", "zh": "區域銀行相對大盤"}],
    "XLI": [{"k": "fred", "id": "INDPRO", "zh": "工業生產", "good": "up", "kind": "pct"},
            {"k": "fred", "id": "DGORDER", "zh": "耐久財訂單", "good": "up", "kind": "pct"},
            {"k": "fred", "id": "TRUCKD11", "zh": "卡車運量", "good": "up", "kind": "pct"},
            {"k": "rel", "id": "IYT", "zh": "運輸股相對大盤"}],
    "XLB": [{"k": "px", "id": "HG=F", "zh": "銅價", "good": "up", "thr": 5.0},
            {"k": "fred", "id": "DTWEXBGS", "zh": "美元指數（美元強不利原物料）", "good": "down", "kind": "pct"},
            {"k": "fred", "id": "INDPRO", "zh": "工業生產", "good": "up", "kind": "pct"}],
    "XLE": [{"k": "px", "id": "CL=F", "zh": "西德州原油", "good": "up", "thr": 8.0},
            {"k": "px", "id": "NG=F", "zh": "天然氣", "good": "up", "thr": 10.0}],
    "XLU": [{"k": "fred", "id": "IPG2211S", "zh": "發電與輸電產出", "good": "up", "kind": "pct"},
            {"k": "fred", "id": "APU000072610", "zh": "平均電價", "good": "up", "kind": "pct"},
            {"k": "fchg", "id": "DGS10", "zh": "10 年期殖利率 3 個月變化", "good": "down", "thr": 0.25},
            {"k": "ssi", "zh": "市場壓力（防禦股相對受惠）"}],
    "XLRE": [{"k": "fred", "id": "MORTGAGE30US", "zh": "30 年房貸利率", "good": "down", "kind": "diff"},
             {"k": "fred", "id": "DRCRELEXFACBS", "zh": "商用不動產貸款逾期率", "good": "down", "kind": "diff"},
             {"k": "fred", "id": "HOUST", "zh": "新屋開工", "good": "up", "kind": "pct"},
             {"k": "fchg", "id": "DGS10", "zh": "10 年期殖利率 3 個月變化", "good": "down", "thr": 0.25}],
}
NAMES = {"XLK": ("資訊科技", "Technology"), "XLC": ("通訊服務", "Communication"), "XLY": ("非必需消費", "Consumer discretionary"),
         "XLP": ("必需消費", "Consumer staples"), "XLV": ("醫療保健", "Health care"), "XLF": ("金融", "Financials"),
         "XLI": ("工業", "Industrials"), "XLB": ("原物料", "Materials"), "XLE": ("能源", "Energy"), "XLU": ("公用事業", "Utilities"),
         "XLRE": ("不動產", "Real estate")}
CYCLICAL = ["XLK", "XLC", "XLY", "XLF", "XLI", "XLB", "XLE"]
DEFENSIVE = ["XLP", "XLV", "XLU", "XLRE"]


def cfg() -> Dict:
    d = {"rel_pp": 3.0, "beat_pp": 10.0, "eps_good": 15.0, "season_days": 75, "min_reports": 5, "ssi_hi": 55.0, "ssi_lo": 40.0,
         "ahead_days": 14, "top_n": 15, "companies": 8}
    return {**d, **(SETTINGS.get("sector_brief") or {})}


# ------------------------------------------------------------------ prices
def _ret(s: pd.Series, n: int) -> Optional[float]:
    s = s.dropna()
    return float(s.iloc[-1] / s.iloc[-1 - n] - 1) * 100 if len(s) > n and s.iloc[-1 - n] > 0 else None


def price_block(s: pd.Series, spy: pd.Series) -> Optional[Dict]:
    s = s.dropna()
    if len(s) < 70:
        return None
    ytd = s[s.index < pd.Timestamp(s.index[-1].year, 1, 1)]
    r3, b3 = _ret(s, 63), _ret(spy, 63)
    hi = float(s.iloc[-252:].max())
    ma = float(s.iloc[-200:].mean()) if len(s) >= 200 else None
    return {"r1m": _ret(s, 21), "r3m": r3, "ytd": float(s.iloc[-1] / ytd.iloc[-1] - 1) * 100 if len(ytd) else None,
            "rel3m": r3 - b3 if r3 is not None and b3 is not None else None,
            "rel1m": (_ret(s, 21) - _ret(spy, 21)) if _ret(s, 21) is not None and _ret(spy, 21) is not None else None,
            "off_hi": (float(s.iloc[-1]) / hi - 1) * 100 if hi else None, "above200": (float(s.iloc[-1]) > ma) if ma else None,
            "asof": s.index[-1].strftime("%Y-%m-%d")}


# ------------------------------------------------------------------ earnings season
def load_days() -> Dict:
    try:
        return json.loads(DAYS.read_text(encoding="utf-8")) if DAYS.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("earn_days unreadable: %s", e)
        return {}


def _season(rows: List[Dict]) -> Dict:
    rep = [r for r in rows if r.get("eps") is not None and r.get("eps_f") is not None]
    if not rep:
        return {"n": 0}
    beat = [r["eps"] > r["eps_f"] for r in rep]
    surp = [float(r["surprise"]) for r in rep if r.get("surprise") is not None]
    gr = [(r["eps"] - r["eps_ly"]) / abs(r["eps_ly"]) * 100 for r in rep if r.get("eps_ly") not in (None, 0) and abs(r["eps_ly"]) >= 0.05]
    return {"n": len(rep), "beat": float(np.mean(beat)) * 100, "surp": float(np.median(surp)) if surp else None,
            "eps_g": float(np.median(gr)) if len(gr) >= 3 else None, "n_g": len(gr)}


def season_rows(days: Dict, today: date, back: int) -> List[Dict]:
    lo, hi = (today - timedelta(days=back)).isoformat(), today.isoformat()
    out, seen = [], set()
    for d in sorted(days, reverse=True):
        if not (lo <= d <= hi):
            continue
        for r in (days[d] or {}).get("rows") or []:
            k = (r.get("sym"), r.get("fq"))
            if r.get("sym") and k not in seen:
                seen.add(k)
                out.append({**r, "date": d})
    return out


def upcoming(days: Dict, today: date, n: int) -> List[Dict]:
    lo, hi = (today + timedelta(days=1)).isoformat(), (today + timedelta(days=n)).isoformat()
    return [{**r, "date": d} for d in sorted(days) if lo <= d <= hi for r in (days[d] or {}).get("rows") or [] if r.get("sym")]


# ------------------------------------------------------------------ drivers
def driver(eng, dv: Dict, spy: pd.Series, c: Dict) -> Optional[Dict]:
    k = dv["k"]
    if k == "fred":
        r = RX.one(eng.fred.get(dv["id"]), dv["good"], dv["kind"])
        if not r:
            return None
        unit = "%" if dv["kind"] == "pct" else " 個百分點"
        return {"zh": dv["zh"], "txt": f'一年 {r["yoy"]:+.2f}{unit}', "state": r["state"], "date": r["date"],
                "lean": None if r["yoy"] == 0 else (r["yoy"] > 0) == (dv["good"] == "up"), "trend_good": r.get("trend_good")}
    if k == "fchg":
        s = eng.fred.get(dv["id"]).dropna()
        past = s[s.index <= s.index[-1] - pd.DateOffset(months=3)] if len(s) else s
        if not len(past):
            return None
        ch = float(s.iloc[-1] - past.iloc[-1])
        good = ch < 0 if dv["good"] == "down" else ch > 0
        st = ("better" if good else "worse") if abs(ch) >= dv["thr"] else "neutral"
        return {"zh": dv["zh"], "txt": f"{s.iloc[-1]:.2f}%（{ch:+.2f}）", "state": st, "date": s.index[-1].strftime("%Y-%m-%d"), "lean": good}
    if k in ("px", "rel"):
        s = eng.market.series(dv["id"]).dropna()
        r = _ret(s, 63)
        if r is None:
            return None
        if k == "rel":
            b = _ret(spy, 63)
            if b is None:
                return None
            v, thr, good = r - b, c["rel_pp"], True
            txt = f"3 個月 {v:+.1f} 個百分點"
        else:
            v, thr, good = r, dv["thr"], dv["good"] == "up"
            txt = f"3 個月 {v:+.1f}%"
        st = ("better" if (v > 0) == good else "worse") if abs(v) >= thr else "neutral"
        return {"zh": dv["zh"], "txt": txt, "state": st, "date": s.index[-1].strftime("%Y-%m-%d"), "lean": (v > 0) == good}
    if k == "ssi":
        sc = getattr(getattr(eng, "stress", None), "score", None)
        if sc is None:
            return None
        st = "better" if sc >= c["ssi_hi"] else "worse" if sc < c["ssi_lo"] else "neutral"
        return {"zh": dv["zh"], "txt": f"SSI {sc:.0f}", "state": st, "date": None, "lean": sc >= 50}
    return None


# ------------------------------------------------------------------ scoring and text
def _score_px(p: Optional[Dict], c: Dict) -> int:
    if not p or p.get("rel3m") is None:
        return 0
    return 1 if p["rel3m"] >= c["rel_pp"] else -1 if p["rel3m"] <= -c["rel_pp"] else 0


def _score_earn(e: Dict, mkt: Dict, c: Dict) -> int:
    if e.get("n", 0) < c["min_reports"] or not mkt.get("n"):
        return 0
    up = e["beat"] >= mkt["beat"] + c["beat_pp"] or (e.get("eps_g") is not None and e["eps_g"] >= c["eps_good"])
    dn = e["beat"] <= mkt["beat"] - c["beat_pp"] or (e.get("eps_g") is not None and e["eps_g"] < 0)
    return 0 if up == dn else (1 if up else -1)


def _score_macro(ds: List[Dict]) -> int:
    b = sum(d["state"] == "better" for d in ds) - sum(d["state"] == "worse" for d in ds)
    return 1 if b > 0 else -1 if b < 0 else 0


def verdict(total: int) -> str:
    return "tail" if total >= 2 else "head" if total <= -2 else "neutral"


def narrative(nm: str, p: Optional[Dict], e: Dict, mkt: Dict, ds: List[Dict], sc: Dict, c: Dict) -> str:
    out = []
    if p and p.get("rel3m") is not None:
        lead = "領先" if p["rel3m"] > 0 else "落後"
        out.append(f"近 3 個月{lead}大盤 {abs(p['rel3m']):.1f} 個百分點"
                   + (f"，比 52 週高點低 {-p['off_hi']:.1f}%" if p.get("off_hi") is not None and p["off_hi"] < -0.5 else "，在 52 週高點附近")
                   + ("" if p.get("above200") is None else ("，站在 200 日均線之上" if p["above200"] else "，跌破 200 日均線")) + "。")
    if e.get("n", 0) >= c["min_reports"]:
        s = f"本季已有 {e['n']} 家公布，{e['beat']:.0f}% 優於預估（全市場 {mkt['beat']:.0f}%）"
        if e.get("eps_g") is not None:
            s += f"，EPS 年增中位數 {e['eps_g']:+.0f}%"
        out.append(s + "。")
    elif e.get("n"):
        out.append(f"本季才 {e['n']} 家公布，樣本還太少，財報面先不計分。")
    else:
        out.append("本季成分股還沒有公布財報。")
    good = [d["zh"] for d in ds if d["state"] == "better"]
    bad = [d["zh"] for d in ds if d["state"] == "worse"]
    if good or bad:
        out.append("經濟數據" + (f"偏多：{'、'.join(good)}" if good else "") + ("；" if good and bad else "")
                   + (f"偏空：{'、'.join(bad)}" if bad else "") + "。")
    elif ds:
        out.append("相關經濟數據都在常態範圍內，沒有明顯方向。")
    # the reading: where the three reads disagree is the information
    if sc["px"] > 0 and sc["earn"] < 0:
        out.append("判讀：股價走在財報前面，漲勢靠預期支撐，後續財報若沒跟上，回檔風險較高。")
    elif sc["px"] < 0 and sc["earn"] > 0:
        out.append("判讀：財報不差但股價落後，市場還不買單；若經濟數據不再轉壞，這是落差可能收斂的類型。")
    elif sc["px"] > 0 and sc["macro"] < 0:
        out.append("判讀：股價強、但背後的經濟數據轉弱，要留意需求面是否追得上。")
    elif sc["px"] < 0 and sc["macro"] > 0:
        out.append("判讀：經濟數據改善、股價還沒反映，屬於基本面先行的類型。")
    elif abs(sc["total"]) >= 2:
        lab = {"px": "股價", "earn": "財報", "macro": "經濟數據"}
        sg = 1 if sc["total"] > 0 else -1
        same = [lab[k] for k in lab if sc[k] == sg]
        rest = [lab[k] for k in lab if sc[k] == 0]
        out.append(f"判讀：{'、'.join(same)}{'一致' if len(same) == 3 else '同時'}{'偏多' if sg > 0 else '偏弱'}"
                   + (f"，{'、'.join(rest)}還沒明顯表態" if rest else "") + "。")
    return "".join(out)


def overview(secs: List[Dict], mkt: Dict, prev: Dict, eng, rsp: Optional[float], spy3: Optional[float]) -> Dict:
    ok = [s for s in secs if s["px"] and s["px"].get("rel3m") is not None]
    rk = sorted(ok, key=lambda s: -s["px"]["rel3m"])
    avg = lambda L: float(np.mean([s["px"]["r3m"] for s in ok if s["etf"] in L])) if any(s["etf"] in L for s in ok) else None  # noqa: E731
    cyc, dfn = avg(CYCLICAL), avg(DEFENSIVE)
    above = [s for s in ok if s["px"].get("above200")]
    breadth = rsp - spy3 if rsp is not None and spy3 is not None else None
    tail = [s for s in secs if s["verdict"] == "tail"]
    head = [s for s in secs if s["verdict"] == "head"]
    lines = []
    if rk:
        lines.append(f"近 3 個月領漲：{'、'.join(NAMES[s['etf']][0] for s in rk[:3])}；落後：{'、'.join(NAMES[s['etf']][0] for s in rk[-3:][::-1])}。")
    if cyc is not None and dfn is not None:
        gap = cyc - dfn
        lines.append(f"景氣循環類股平均 {cyc:+.1f}%、防禦類股 {dfn:+.1f}%，"
                     + ("市場偏向追逐成長與景氣（風險偏好）。" if gap >= 3 else "資金偏向防禦（風險趨避）。" if gap <= -3 else "兩者差距不大，沒有明顯的攻守輪動。"))
    if breadth is not None:
        lines.append(f"等權重標普比市值加權 {breadth:+.1f} 個百分點，"
                     + ("漲勢集中在少數大型股，廣度偏窄。" if breadth <= -2 else "多數股票一起參與，廣度健康。" if breadth >= 2 else "廣度普通。")
                     + f"11 個產業有 {len(above)} 個在 200 日均線之上。")
    if mkt.get("n"):
        s = f"財報季：已有 {mkt['n']} 家公布，{mkt['beat']:.0f}% 優於預估"
        if mkt.get("eps_g") is not None:
            s += f"，EPS 年增中位數 {mkt['eps_g']:+.0f}%"
        if prev.get("n", 0) >= 50:
            s += f"（上一季同期資料 {prev['beat']:.0f}%）"
        lines.append(s + "。")
    sc = getattr(getattr(eng, "stress", None), "score", None)
    if sc is not None:
        lines.append(f"整體市場壓力 SSI {sc:.0f}" + ("，偏高：即使產業基本面不差，整體回檔時也很難獨善其身。" if sc >= 55 else "，在常態範圍。"))
    concl = ""
    if tail or head:
        concl = ("規則判讀為順風：" + ("、".join(NAMES[s["etf"]][0] for s in tail) or "無") + "；逆風："
                 + ("、".join(NAMES[s["etf"]][0] for s in head) or "無") + "。")
    return {"lines": lines, "concl": concl, "cyc": cyc, "def": dfn, "breadth": breadth, "n_above": len(above), "n": len(ok)}


# ------------------------------------------------------------------ daily snapshot
def _hist_load() -> Dict:
    try:
        return json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def snapshot(secs: List[Dict], today: date, keep: int = 400) -> Dict:
    h = _hist_load()
    h[today.isoformat()] = {s["etf"]: s["score"]["total"] for s in secs}
    h = {k: h[k] for k in sorted(h)[-keep:]}
    try:
        tmp = HIST.with_suffix(".tmp")
        tmp.write_text(json.dumps(h), encoding="utf-8")
        os.replace(tmp, HIST)
    except Exception as e:  # noqa: BLE001
        log.warning("sector brief history not saved: %s", e)
    return h


def week_ago(h: Dict, today: date) -> Dict:
    ks = [k for k in sorted(h) if k <= (today - timedelta(days=7)).isoformat()]
    return h[ks[-1]] if ks else {}


# ------------------------------------------------------------------ build
def build(eng, members: Dict, today: Optional[date] = None, px: Optional[pd.DataFrame] = None) -> Dict:
    from ..data.sector_members import sector_of, load_prices
    from . import sector_companies as SC
    if today is None:
        from ..data.econcal import us_today
        today = us_today()
    c = cfg()
    spy = eng.market.series("SPY").dropna()
    if len(spy) < 70:
        return {"available": False}
    smap = sector_of(members)
    from ..data import fundamentals as FU
    fcache = FU.load()
    snap = load_rev()
    days = load_days()
    rows = season_rows(days, today, int(c["season_days"]))
    prev_rows = season_rows(days, today - timedelta(days=91), int(c["season_days"]))
    mkt = _season([r for r in rows if r["sym"] in smap] or rows)
    prev = _season([r for r in prev_rows if r["sym"] in smap] or prev_rows)
    ahead = upcoming(days, today, int(c["ahead_days"]))
    if px is None:
        px = load_prices()
    dgs10 = eng.fred.get("DGS10").dropna()
    secs = []
    for etf in NAMES:
        p = price_block(eng.market.series(etf), spy)
        e = _season([r for r in rows if smap.get(r["sym"]) == etf])
        ds = []
        for dv in DRIVERS.get(etf, []):
            try:
                d = driver(eng, dv, spy, c)
            except Exception:  # noqa: BLE001
                d = None
            if d:
                ds.append(d)
        sc = {"px": _score_px(p, c), "earn": _score_earn(e, mkt, c), "macro": _score_macro(ds)}
        sc["total"] = sc["px"] + sc["earn"] + sc["macro"]
        nxt, seen = [], set()
        for r in sorted([r for r in ahead if smap.get(r["sym"]) == etf], key=lambda r: -(r.get("mcap") or 0)):
            k = (r.get("name") or r["sym"]).split(" Class")[0]            # GOOG / GOOGL: one company, one entry
            if k not in seen:
                seen.add(k)
                nxt.append(r)
        top = [t for t, *_ in sorted((members.get("sectors") or {}).get(etf, {}).get("members") or [], key=lambda x: -x[1])[:int(c["top_n"])]]
        fd = fund_block(top, fcache)
        if etf == "XLF":              # banks / insurers: operating margin and capex are not comparable to other sectors
            fd = {k: v for k, v in fd.items() if k not in ("margin", "margin_chg", "capex_g", "capex_ocf", "gap_pct")}
        rv = rev_block(snap, smap, etf)
        try:
            sv = sens_block(eng, eng.market.series(etf).dropna(), spy)
        except Exception:  # noqa: BLE001
            log.exception("sector sensitivity %s failed", etf)
            sv = {}
        try:
            cos = SC.build((members.get("sectors") or {}).get(etf, {}).get("members") or [], fcache, rows, snap,
                           upcoming(days, today, 60), px, spy, dgs10, int(c["companies"]))
        except Exception:  # noqa: BLE001
            log.exception("sector companies %s failed", etf)
            cos = []
        secs.append({"etf": etf, "zh": NAMES[etf][0], "en": NAMES[etf][1], "px": p, "earn": e, "drivers": ds, "score": sc, "companies": cos,
                     "fund": fd, "rev": rv, "sens": sv, "outlook": outlook_text(fd, rv, ds, nxt), "risk": risk_text(fd, sv, p),
                     "verdict": verdict(sc["total"]), "text": narrative(NAMES[etf][0], p, e, mkt, ds, sc, c),
                     "next": [{"sym": r["sym"], "date": r["date"]} for r in nxt[:4]], "n_next": len(nxt),
                     "members": len((members.get("sectors") or {}).get(etf, {}).get("members") or [])})
    for s_ in secs:
        s_["points"] = key_points(s_)
    hist = snapshot(secs, today)
    wk = week_ago(hist, today)
    for s in secs:
        s["prev_total"] = wk.get(s["etf"])
    rsp = _ret(eng.market.series("RSP"), 63)
    ov = overview(secs, mkt, prev, eng, rsp, _ret(spy, 63))
    try:
        ov["highlights"] = highlights(secs, eng)
    except Exception:  # noqa: BLE001
        log.exception("sector highlights failed")
        ov["highlights"] = []
    asof = [s["px"]["asof"] for s in secs if s["px"]]
    return {"available": True, "sectors": secs, "market": mkt, "prev": prev, "overview": ov, "asof": max(asof) if asof else None,
            "members_asof": next((v.get("asof") for v in (members.get("sectors") or {}).values() if v.get("asof")), None),
            "n_hist": len(hist), "week_ago": bool(wk), "today": today.isoformat()}


# ================================================================== 深入分析：未來發展 × 財務風險
REV = DATA_DIR / "earn_revisions.json"


def _med(xs: List[Optional[float]]) -> Optional[float]:
    xs = [x for x in xs if x is not None and np.isfinite(x)]
    return float(np.median(xs)) if xs else None


def _sg(x: Optional[float], d: int = 1) -> str:
    return "—" if x is None else f"{x:+.{d}f}"


def fund_block(syms: List[str], cache: Dict, min_n: int = 3) -> Dict:
    """SEC companyfacts of the sector's largest members: growth, margin trend, investment cycle, balance-sheet strain."""
    from ..data import fundamentals as FU
    rg, mg, mgc, cg, co, dg, ib = [], [], [], [], [], [], []
    n, gap, strain, gap_n, strain_n = 0, 0, 0, [], []
    for s in syms:
        rec = cache.get(s) or cache.get(s.replace("-", ".")) or cache.get(s.replace(".", "-")) or {}
        p, m = rec.get("p"), rec.get("m")
        if not p or not m:
            continue
        n += 1

        def g(k, f="v"):
            return (p.get(k) or {}).get(f)
        rg.append(m.get("rev_growth"))
        if g("rev") and g("ebit") is not None and g("rev") > 0:
            mg.append(g("ebit") / g("rev") * 100)
            if g("rev", "prev") and g("ebit", "prev") is not None and g("rev", "prev") > 0:
                mgc.append(g("ebit") / g("rev") * 100 - g("ebit", "prev") / g("rev", "prev") * 100)
        if g("capex") is not None and g("capex", "prev") and g("capex", "prev") > 0:
            cg.append((g("capex") / g("capex", "prev") - 1) * 100)
        co.append(m.get("capex_ocf"))
        dg.append(m.get("debt_growth"))
        ib.append(m.get("int_burden"))
        fl = FU.flags(m)
        if "gap" in fl:
            gap += 1
            gap_n.append(s)
        if fl:
            strain += 1
            strain_n.append(s)
    if n < min_n:
        return {"n": n}
    return {"n": n, "rev_g": _med(rg), "margin": _med(mg), "margin_chg": _med(mgc), "capex_g": _med(cg), "capex_ocf": _med(co),
            "debt_g": _med(dg), "int_burden": _med(ib), "gap_pct": gap / n * 100, "strain_pct": strain / n * 100,
            "strain_names": strain_n[:6], "gap_names": gap_n[:6]}


def load_rev() -> Dict:
    try:
        return json.loads(REV.read_text(encoding="utf-8")) if REV.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def rev_block(snap: Dict, smap: Dict[str, str], etf: str, min_days: int = 5, eps: float = 0.5) -> Dict:
    """Consensus EPS of each upcoming large-cap report (canary.record_revisions, daily): first snapshot vs latest."""
    up, dn, flat, span = [], [], 0, 0
    for k, lst in snap.items():
        sym = k.split("|")[0]
        if smap.get(sym) != etf or len(lst) < 2 or not lst[0][1]:
            continue
        d = (date.fromisoformat(lst[-1][0]) - date.fromisoformat(lst[0][0])).days
        if d < min_days:
            continue
        span = max(span, d)
        ch = (lst[-1][1] - lst[0][1]) / abs(lst[0][1]) * 100
        if ch > eps:
            up.append(sym)
        elif ch < -eps:
            dn.append(sym)
        else:
            flat += 1
    n = len(up) + len(dn) + flat
    return {"n": n, "up": len(up), "dn": len(dn), "flat": flat, "days": span, "up_names": up[:5], "dn_names": dn[:5],
            "net": (len(up) - len(dn)) / n * 100 if n else None}


def sens_block(eng, s: pd.Series, spy: pd.Series, weeks: int = 104) -> Dict:
    """Two years of weekly data: beta to the S&P 500, and the return relative to the market per +1 pp of the 10-year
    yield.  Plus the median 1-month return relative to the market after days with SSI ≥ 60 (since 2005)."""
    out: Dict = {}
    w = pd.concat({"s": s, "m": spy}, axis=1).dropna().resample("W-FRI").last().pct_change().dropna().iloc[-weeks:]
    if len(w) >= 52:
        out["beta"] = float(np.cov(w["s"], w["m"])[0, 1] / np.var(w["m"], ddof=1))
        y = eng.fred.get("DGS10").dropna()
        if len(y):
            dy = y.resample("W-FRI").last().diff().reindex(w.index)
            j = pd.concat({"rel": w["s"] - w["m"], "dy": dy}, axis=1).dropna()
            if len(j) >= 52 and j["dy"].var() > 0:
                out["rate_rel"] = float(np.cov(j["rel"], j["dy"])[0, 1] / np.var(j["dy"], ddof=1)) * 100   # % per +1 pp
    hist = getattr(getattr(eng, "stress", None), "history", None)
    if hist is not None and len(hist):
        d = pd.concat({"s": s, "m": spy}, axis=1).dropna()
        fwd = (d["s"].shift(-21) / d["s"] - d["m"].shift(-21) / d["m"]) * 100
        ssi = hist.reindex(d.index, method="ffill")
        f = fwd[(ssi >= 60) & fwd.notna() & (d.index >= pd.Timestamp("2005-01-01"))]
        if len(f) >= 60:
            out["stress_rel"], out["stress_n"], out["stress_win"] = float(f.median()), int(len(f)), float((f > 0).mean() * 100)
    return out


def outlook_text(fd: Dict, rv: Dict, ds: List[Dict], nxt: List[Dict]) -> List[str]:
    out = []
    if rv.get("n", 0) >= 3:
        tone = "上修多於下修" if rv["up"] > rv["dn"] else "下修多於上修" if rv["dn"] > rv["up"] else "上修下修相當"
        out.append(f"分析師預估：近 {rv['days']} 天，{rv['n']} 家即將公布的大型公司中 EPS 預估上修 {rv['up']} 家、下修 {rv['dn']} 家（{tone}）"
                   + (f"，下修的有 {'、'.join(rv['dn_names'][:3])}" if rv["dn"] >= 2 else "") + "。")
    if fd.get("n", 0) >= 3:
        s = f"成長與獲利：最大的 {fd['n']} 家成分股營收年增中位數 {_sg(fd.get('rev_g'))}%"
        if fd.get("margin") is not None:
            s += f"、營業利益率 {fd['margin']:.1f}%"
            if fd.get("margin_chg") is not None:
                s += (f"（比一年前 {fd['margin_chg']:+.1f} 個百分點，"
                      + ("利潤率擴張" if fd["margin_chg"] > 0.5 else "利潤率收縮" if fd["margin_chg"] < -0.5 else "大致持平") + "）")
        out.append(s + "。")
        if fd.get("capex_g") is not None:
            cyc = ("擴產期：資本支出明顯成長，公司看好未來需求，但要靠之後的營收消化" if fd["capex_g"] >= 15 else
                   "收縮期：資本支出減少，公司對未來需求較保守或在保留現金" if fd["capex_g"] <= -5 else "資本支出溫和成長，投資步調平穩")
            out.append(f"投資週期：資本支出年增中位數 {fd['capex_g']:+.0f}%，{cyc}。")
    imp = [d["zh"] for d in ds if d.get("trend_good") is True]
    det = [d["zh"] for d in ds if d.get("trend_good") is False]
    if imp or det:
        out.append("經濟數據近 3 個月的方向：" + (f"改善 {'、'.join(imp)}" if imp else "") + ("；" if imp and det else "")
                   + (f"惡化 {'、'.join(det)}" if det else "") + "。")
    if nxt:
        out.append(f"近期觀察：{'、'.join(r['sym'] + '（' + r['date'][5:] + '）' for r in nxt[:3])} 將公布財報。")
    return out


def risk_text(fd: Dict, sv: Dict, p: Optional[Dict]) -> List[str]:
    out = []
    if fd.get("n", 0) >= 3:
        s = []
        if fd.get("debt_g") is not None:
            s.append(f"負債年增中位數 {fd['debt_g']:+.0f}%")
        if fd.get("int_burden") is not None:
            s.append(f"利息佔營業利益 {fd['int_burden']:.0f}%")
        if fd.get("capex_ocf") is not None:
            s.append(f"資本支出／營運現金流 {fd['capex_ocf']:.2f} 倍")
        sp = fd.get("strain_pct") or 0
        lvl = "偏高" if sp >= 40 else "中等" if sp >= 20 else "低"
        out.append("資產負債表：" + ("、".join(s) + "；" if s else "") + f"{sp:.0f}% 的公司至少出現一項財報壓力（{lvl}）"
                   + (f"，例如 {'、'.join(fd['strain_names'][:4])}" if fd.get("strain_names") else "") + "。")
        if (fd.get("gap_pct") or 0) >= 30:
            out.append(f"資金缺口：{fd['gap_pct']:.0f}% 的公司資本支出超過營運現金流，要靠借錢或發股支應，信用收緊時最先受壓。")
    if sv.get("rate_rel") is not None:
        r = sv["rate_rel"] * 0.5
        out.append(f"利率敏感度：過去兩年，10 年期殖利率每升 0.5 個百分點，這個產業平均相對大盤 {r:+.1f}%"
                   + ("（對利率上升特別敏感）" if r <= -2 else "（利率上升時反而相對受惠）" if r >= 2 else "") + "。")
    if sv.get("beta") is not None:
        out.append(f"市場連動：β {sv['beta']:.2f}，" + ("大盤下跌時通常跌得比大盤多。" if sv["beta"] >= 1.15 else
                                                    "大盤下跌時通常跌得比大盤少。" if sv["beta"] <= 0.85 else "大致和大盤同步。"))
    if sv.get("stress_rel") is not None:
        out.append(f"壓力時期：2005 年以來 SSI ≥ 60 的 {sv['stress_n']} 個交易日之後一個月，相對大盤的中位數 {sv['stress_rel']:+.1f}%"
                   f"（跑贏大盤的比例 {sv['stress_win']:.0f}%）。")
    if p and p.get("off_hi") is not None and p["off_hi"] > -1 and (p.get("r3m") or 0) > 10:
        out.append("位置：短期漲多且在高點附近，若財報或數據不如預期，回檔幅度可能較大。")
    return out


def key_points(s: Dict) -> List[str]:
    """2–4 one-line takeaways chosen by rule from everything above, strongest first."""
    pts: List[tuple] = []
    p, fd, rv, sv, sc = s["px"] or {}, s.get("fund") or {}, s.get("rev") or {}, s.get("sens") or {}, s["score"]
    if rv.get("n", 0) >= 3 and rv.get("net") is not None and abs(rv["net"]) >= 30:
        pts.append((abs(rv["net"]), ("＋分析師預估明顯上修" if rv["net"] > 0 else "－分析師預估明顯下修") + f"（淨 {rv['net']:+.0f}%）"))
    if fd.get("margin_chg") is not None and abs(fd["margin_chg"]) >= 1:
        pts.append((abs(fd["margin_chg"]) * 10, ("＋利潤率擴張" if fd["margin_chg"] > 0 else "－利潤率收縮") + f" {fd['margin_chg']:+.1f} 個百分點"))
    if fd.get("rev_g") is not None and (fd["rev_g"] >= 10 or fd["rev_g"] < 0):
        pts.append((abs(fd["rev_g"]), ("＋營收高成長" if fd["rev_g"] > 0 else "－營收衰退") + f" {fd['rev_g']:+.0f}%"))
    if (fd.get("strain_pct") or 0) >= 40:
        pts.append((fd["strain_pct"], f"－財報壓力普遍（{fd['strain_pct']:.0f}% 公司有壓力旗標）"))
    if sv.get("rate_rel") is not None and abs(sv["rate_rel"] * 0.5) >= 2:
        pts.append((abs(sv["rate_rel"]) * 5, ("－利率上升時受傷" if sv["rate_rel"] < 0 else "＋利率上升時相對受惠")
                    + f"（升 0.5 個百分點相對大盤 {sv['rate_rel'] * 0.5:+.1f}%）"))
    if sv.get("stress_rel") is not None and abs(sv["stress_rel"]) >= 1:
        pts.append((abs(sv["stress_rel"]) * 15, ("＋壓力時期歷史上相對抗跌" if sv["stress_rel"] > 0 else "－壓力時期歷史上相對落後") + f"（{sv['stress_rel']:+.1f}%）"))
    if sc["px"] != 0 and p.get("rel3m") is not None:
        pts.append((abs(p["rel3m"]) * 3, ("＋股價領先大盤" if p["rel3m"] > 0 else "－股價落後大盤") + f" {p['rel3m']:+.1f} 個百分點"))
    pts.sort(key=lambda x: -x[0])
    return [t for _, t in pts[:4]]


def highlights(secs: List[Dict], eng) -> List[str]:
    """Cross-sector takeaways: estimate revisions, balance-sheet strain, margins, rate exposure, stress behaviour, credit."""
    out = []
    rv = [s for s in secs if (s.get("rev") or {}).get("n", 0) >= 3 and s["rev"].get("net") is not None]
    if rv:
        b, w = max(rv, key=lambda s: s["rev"]["net"]), min(rv, key=lambda s: s["rev"]["net"])
        out.append(f"分析師預估：上修最多的是{b['zh']}（淨 {b['rev']['net']:+.0f}%），下修最多的是{w['zh']}（淨 {w['rev']['net']:+.0f}%）。")
    fd = [s for s in secs if (s.get("fund") or {}).get("n", 0) >= 3]
    if fd:
        st = sorted(fd, key=lambda s: -(s["fund"].get("strain_pct") or 0))[:2]
        out.append("財報壓力最普遍：" + "、".join(f"{s['zh']}（{s['fund']['strain_pct']:.0f}% 公司）" for s in st) + "。")
        mg = [s for s in fd if s["fund"].get("margin_chg") is not None]
        if len(mg) >= 2:
            hi, lo = max(mg, key=lambda s: s["fund"]["margin_chg"]), min(mg, key=lambda s: s["fund"]["margin_chg"])
            out.append(f"利潤率：擴張最多的是{hi['zh']}（{hi['fund']['margin_chg']:+.1f} 個百分點），收縮最多的是{lo['zh']}（{lo['fund']['margin_chg']:+.1f}）。")
    rs = [s for s in secs if (s.get("sens") or {}).get("rate_rel") is not None]
    y = eng.fred.get("DGS10").dropna()
    if rs and len(y):
        past = y[y.index <= y.index[-1] - pd.DateOffset(months=3)]
        if len(past):
            ch = float(y.iloc[-1] - past.iloc[-1])
            lo, hi = min(rs, key=lambda s: s["sens"]["rate_rel"]), max(rs, key=lambda s: s["sens"]["rate_rel"])
            out.append(f"利率：10 年期殖利率近 3 個月{'上升' if ch > 0 else '下降'} {abs(ch):.2f} 個百分點；歷史上對利率上升最敏感的是{lo['zh']}，"
                       f"利率上升時相對受惠的是{hi['zh']}。")
    sr = [s for s in secs if (s.get("sens") or {}).get("stress_rel") is not None]
    sc = getattr(getattr(eng, "stress", None), "score", None)
    if sr and sc is not None and sc >= 55:
        top = sorted(sr, key=lambda s: -s["sens"]["stress_rel"])
        out.append(f"壓力情境：目前 SSI {sc:.0f}。歷史上 SSI ≥ 60 之後一個月相對抗跌的是{'、'.join(s['zh'] for s in top[:3])}，"
                   f"相對落後的是{'、'.join(s['zh'] for s in top[-2:][::-1])}。")
    hy = eng.fred.get("BAMLH0A0HYM2").dropna()
    if len(hy) > 260:
        pct = float((hy.iloc[-756:] < hy.iloc[-1]).mean() * 100)
        out.append(f"信用環境：高收益債利差 {hy.iloc[-1]:.2f}%，在近 3 年第 {pct:.0f} 百分位，"
                   + ("借錢成本偏高，負債高、需要外部資金的產業壓力較大。" if pct >= 70 else "融資環境寬鬆。" if pct <= 30 else "融資環境中性。"))
    return out
