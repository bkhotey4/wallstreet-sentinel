"""重大數據公布後的市場反應統計：每次 CPI、非農、FOMC 公布後第一個收盤，標普 500、10 年期美債殖利率、台股怎麼動，
再跟「平常的一天」比，讓讀者看得出是不是雜訊。

時間點（公布後第一個收盤）：
  標普、10 年期殖利率：前一交易日收盤 → 公布當天收盤。CPI／非農美東 08:30、FOMC 14:00，都在美股收盤前。
  台股：美東公布時台股當天已收盤（13:30 台北），所以是台股「公布日或之前最後一個收盤」→「公布日之後第一個收盤」。
日期：FOMC＝fomc_history.json＋即時日曆；CPI／非農＝FRED 發布日。FRED 名單也含修正日（例如 2 月的季節因子修正），
所以有 Nasdaq 紀錄的日子以 Nasdaq 為準；還沒查過、同月又有兩個日期的就不納入。
結果對預期：Nasdaq 經濟日曆的歷史「公布值／預期值／前值」（快取 data_cache/econ_event_react.json，約 2008 年起有預期值）。
  CPI 看核心 CPI 月增，非農看新增就業，門檻沿用 macro_events.EV。FOMC 的決議幾乎都符合預期，改分升息／不變／降息（對前值）。
雜訊判斷：跟平常日子比的 Welch t 值。一次看很多組數字，光靠運氣就會有幾組 |t| ≥ 2，所以 |t| ≥ 3 才算明顯。
歷史統計，不是預測，也不是投資建議。"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..data import econcal as EC
from ..health import HEALTH
from . import event_clock as CLK
from . import macro_events as ME
from .sessions import completed

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_event_react.json"
START = "2005-01-01"             # the Nasdaq calendar has US rows from about here (consensus from about 2008)
CORE_MM_MAX = 1.0                # core CPI has never moved this much in a month; a value this size is the y/y row
MAX_TRIES = 3                    # an empty answer is a hiccup until it has been seen this many times
MIN_N = 8
FEW_N = 15                       # below this no verdict: too few events
T_CLEAR, T_MAYBE = 3.0, 2.0
TW_GAP_DAYS = 5                  # a holiday break longer than this is not "the next session"
UPCOMING_DAYS = 5
EVENTS = (("cpi", "CPI 消費者物價", "CPI", "Core CPI", "m", "美東 08:30", "08:30 ET"),
          ("nfp", "非農就業", "Jobs report", "Nonfarm Payrolls", "", "美東 08:30", "08:30 ET"),
          ("fomc", "FOMC 利率決議", "FOMC decision", "Fed Interest Rate Decision", "", "美東 14:00", "14:00 ET"))
ASSETS = (("spx", "^GSPC", "標普 500", "S&P 500", "pct"), ("y10", "^TNX", "10 年期美債殖利率", "10y yield", "bp"),
          ("tw", "^TWII", "台股加權指數", "TAIEX", "pct"))
BUCKETS = {"cpi": ("hot", "inline", "cool"), "nfp": ("hot", "inline", "cool"), "fomc": ("hike", "hold", "cut")}
LABELS = {"hike": ("升息", "Hike"), "hold": ("利率不變", "Hold"), "cut": ("降息", "Cut")}
VERDICT = {"clear": ("明顯不同", "clearly different"), "maybe": ("有差距，但可能是巧合", "a gap, possibly chance"),
           "noise": ("跟雜訊分不開", "not distinguishable from noise"), "few": ("樣本太少", "too few events")}


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, FILE)


async def _fetch(day: str) -> Tuple[List[Dict], int]:
    """(US rows, raw row count) of one calendar day; econcal's parser is not used because it would feed the live-calendar
    clock check with years-old days."""
    d = date.fromisoformat(day) + timedelta(days=1)            # Nasdaq's date parameter is one day ahead, see econcal._fetch
    from ..data import http
    js = await http.get("https://api.nasdaq.com/api/calendar/economicevents", params={"date": d.isoformat()}, headers=EC.NQ_HDR, timeout=20, retries=1)
    raw = ((js or {}).get("data") or {}).get("rows") or []
    us = [{"name": EC.clean(r.get("eventName")), "actual": EC.clean(r.get("actual")), "cons": EC.clean(r.get("consensus")), "prev": EC.clean(r.get("previous"))}
          for r in raw if EC.clean(r.get("country")) == "United States" and EC.clean(r.get("eventName"))]
    return us, len(raw)


def _pick(key: str, rows: List[Dict]) -> Optional[Dict]:
    ev = next(e for e in EVENTS if e[0] == key)
    return ME._pick(rows, ev[3], ev[4])


def _todo(eng, days: Dict, rel: Dict, today: str) -> List[Tuple[str, str]]:
    out = []
    for key, *_ in EVENTS:
        seen = days.get(key) or {}
        for x in CLK.dates_for(eng, key, rel):
            r = seen.get(x)
            if START <= x <= today and not (r and (r.get("a") or r.get("none"))):
                out.append((x, key))
    return sorted(out, reverse=True)                           # newest first: the event a reader waits for comes first


async def refresh(eng=None, budget_s: float = 90) -> Dict:
    """Record the actual / consensus / previous of each past release.  A failed request writes nothing and holds `ts` back."""
    d = load()
    days = d.setdefault("days", {})
    today = EC.us_today().isoformat()
    recent = (EC.us_today() - timedelta(days=3)).isoformat()   # a value can lag a release by a little: wait before giving up
    todo = _todo(eng, days, CLK.load(), today)
    cached, t0, ok, bad, seen = EC.load(), time.time(), 0, 0, {}
    for x, key in todo:
        rows = (cached.get(x) or {}).get("rows") or []
        r = _pick(key, rows) if rows else None
        if not (r and r.get("actual")):                        # the live calendar's cache first, then one request per day
            if x not in seen:
                if time.time() - t0 > budget_s:
                    break
                try:
                    seen[x] = await _fetch(x)
                except Exception as e:  # noqa: BLE001
                    bad += 1
                    seen[x] = None
                    log.info("event history %s: %s", x, e if str(e) else type(e).__name__)
                await asyncio.sleep(0.25)
            if seen[x] is None:
                continue
            rows, n_raw = seen[x]
            r = _pick(key, rows)
            rec = days.setdefault(key, {}).get(x) or {}
            if n_raw == 0:                                     # an empty answer is a hiccup, not "nothing happened"
                n = int(rec.get("tries", 0)) + 1
                days[key][x] = {"tries": n, **({"none": 1} if n >= MAX_TRIES else {})}
                continue
            if (r is None and x < today) or (r is not None and not r.get("actual") and x < recent):
                days[key][x] = {"none": 1}                     # the calendar answered and has no value: not a release day
                continue
        if r and r.get("actual"):
            days.setdefault(key, {})[x] = {"a": r["actual"], "c": r.get("cons") or "", "p": r.get("prev") or ""}
            ok += 1
    if not bad:
        d["ts"] = time.time()
    got = [x for v in days.values() for x, r in v.items() if r.get("a")]
    d["asof"] = max(got) if got else None
    _save(d)
    if bad and not ok:
        HEALTH.fail("event_react", f"{bad} calendar days failed", every=6 * 3600)
    else:
        HEALTH.ok("event_react", len(got), every=6 * 3600)
    return d


# ------------------------------------------------------------------ dates and outcomes
def valid_dates(key: str, dates: List[str], seen: Dict, today: str) -> List[str]:
    """Past release days.  FOMC dates come from the Fed.  FRED's CPI / jobs lists also hold revision days: where the
    calendar has been checked it decides; otherwise a month with two dates cannot be told apart and is left out."""
    past = [x for x in dates if x < today]
    if key == "fomc":
        return past
    by_month: Dict[str, int] = {}
    for x in past:
        by_month[x[:7]] = by_month.get(x[:7], 0) + 1
    out = []
    for x in past:
        r = seen.get(x) or {}
        if r.get("a") or (not r.get("none") and by_month[x[:7]] == 1):
            out.append(x)
    return out


def outcome(key: str, r: Optional[Dict]) -> Optional[str]:
    if not r or not r.get("a"):
        return None
    row = ME._row({"actual": r.get("a"), "cons": r.get("c"), "prev": r.get("p")}, "", "")
    if key == "cpi" and row["a"] is not None and abs(row["a"]) >= CORE_MM_MAX:
        return None                                            # only a year-on-year row that day (2025-12-18): not the m/m measure
    if key != "fomc":
        return ME.classify(key, row)
    if row["a"] is None or row["p"] is None:
        return None
    gap = row["a"] - row["p"]
    return "hold" if abs(gap) < 0.01 else "hike" if gap > 0 else "cut"


# ------------------------------------------------------------------ moves
def us_moves(s: pd.Series, kind: str) -> pd.Series:
    s = s.dropna()
    return ((s.diff() * 100) if kind == "bp" else (s.pct_change() * 100)).dropna()


def tw_reaction(s: pd.Series, day: str) -> Optional[pd.Timestamp]:
    """The Taiwan session that first trades after a US release on `day`: the first bar after that date."""
    t = pd.Timestamp(day)
    i = s.index.searchsorted(t, side="right")
    if i >= len(s) or i == 0 or (s.index[i] - t).days > TW_GAP_DAYS:
        return None
    return s.index[i]


def react_map(px: pd.Series, kind: str, tw: bool, dates: List[str]) -> Dict[str, Tuple[pd.Timestamp, float]]:
    """{event date: (the session that reacted, its move)}."""
    r = us_moves(px, kind)
    out = {}
    for d in dates:
        t = tw_reaction(px, d) if tw else pd.Timestamp(d)
        if t is not None and t in r.index:
            out[d] = (t, float(r.loc[t]))
    return out


def stat(x: np.ndarray, base: np.ndarray) -> Optional[Dict]:
    x, base = np.asarray(x, float), np.asarray(base, float)
    if len(x) < MIN_N or len(base) < 50:
        return None
    t = welch(x, base)
    ta = welch(np.abs(x), np.abs(base))
    ab, bb = float(np.abs(x).mean()), float(np.abs(base).mean())
    return {"n": int(len(x)), "mean": float(x.mean()), "med": float(np.median(x)), "up": float((x > 0).mean() * 100), "abs": ab,
            "base_n": int(len(base)), "base_mean": float(base.mean()), "base_med": float(np.median(base)), "base_up": float((base > 0).mean() * 100),
            "base_abs": bb, "ratio": ab / bb if bb else None, "t": t, "t_abs": ta, "dir": verdict(t, len(x)), "size": verdict(ta, len(x))}


def welch(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    if len(a) < 2 or len(b) < 2:
        return None
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else None


def verdict(t: Optional[float], n: int) -> str:
    if n < FEW_N or t is None:
        return "few"
    return "clear" if abs(t) >= T_CLEAR else "maybe" if abs(t) >= T_MAYBE else "noise"


def study(prices: Dict[str, pd.Series], events: Dict[str, List[str]], seen: Dict[str, Dict]) -> List[Dict]:
    """prices {^GSPC, ^TNX, ^TWII}; events {key: valid past dates}; seen {key: {date: record}}."""
    out = []
    for key, zh, en, _nm, _v, tm, tm_en in EVENTS:
        dates = events.get(key) or []
        rec: Dict = {"key": key, "zh": zh, "en": en, "time": tm, "time_en": tm_en, "assets": [], "n": len(dates)}
        buckets = {d: outcome(key, (seen.get(key) or {}).get(d)) for d in dates}
        for a, sym, azh, aen, kind in ASSETS:
            px = (prices.get(sym) if prices.get(sym) is not None else pd.Series(dtype=float)).dropna()
            px = px[px > 0]
            if len(px) < 300:
                continue
            tw = a == "tw"
            mv = react_map(px, kind, tw, dates)
            if not mv:
                continue
            every = us_moves(px, kind)
            busy = {t for k2 in events for t, _ in react_map(px, kind, tw, events[k2]).values()}
            first = pd.Timestamp(min(mv))
            base = every[(every.index >= first) & ~every.index.isin(list(busy))].to_numpy()
            st = stat(np.array([v for _, v in mv.values()]), base)
            if st is None:
                continue
            split = {}
            vals: Dict[str, np.ndarray] = {}
            for b in BUCKETS[key]:
                xs = np.array([v for d, (_, v) in mv.items() if buckets.get(d) == b])
                vals[b] = xs
                if len(xs):
                    split[b] = stat(xs, base) or {"n": int(len(xs)), "thin": True}
            hi, lo = BUCKETS[key][0], BUCKETS[key][2]
            spread = None
            if len(vals[hi]) >= MIN_N and len(vals[lo]) >= MIN_N:
                t = welch(vals[hi], vals[lo])
                spread = {"gap": float(vals[hi].mean() - vals[lo].mean()), "t": t, "dir": verdict(t, min(len(vals[hi]), len(vals[lo])))}
            rec["assets"].append({"key": a, "zh": azh, "en": aen, "kind": kind, "all": st, "split": split, "spread": spread})
        if rec["assets"]:
            spx = next((x for x in rec["assets"] if x["key"] == "spx"), rec["assets"][0])
            rec["n_split"] = sum(int(v.get("n", 0)) for v in spx["split"].values())
            rec["first"] = min(dates)
            maps = {a["key"]: react_map(prices[next(x[1] for x in ASSETS if x[0] == a["key"])].dropna(), a["kind"], a["key"] == "tw", dates[-6:]) for a in rec["assets"]}
            rec["recent"] = [{"date": d, "row": (seen.get(key) or {}).get(d) or {}, "b": buckets.get(d), **{k: (m.get(d) or (None, None))[1] for k, m in maps.items()}}
                             for d in dates[-6:][::-1]]
            out.append(rec)
    return out


def _name(a: Dict) -> str:
    return a["zh"].replace("10 年期美債殖利率", "10 年期殖利率").replace("台股加權指數", "台股")


def lead(evs: List[Dict]) -> Dict[str, str]:
    """One plain sentence from the measured results (no fixed conclusion)."""
    big = [(e, a) for e in evs for a in e["assets"] if a["all"]["size"] == "clear" and (a["all"]["ratio"] or 0) > 1]
    moved = [(e, a) for e in evs for a in e["assets"] if a["all"]["dir"] == "clear"]
    n = sum(len(e["assets"]) for e in evs)
    if big:
        rs = [a["all"]["ratio"] for _, a in big]
        lo, hi = min(rs), max(rs)
        rg = f"{lo:.1f} 倍" if hi - lo < 0.05 else f"{lo:.1f}–{hi:.1f} 倍"
        zh = f"這些數據公布後，{n} 組比較裡有 {len(big)} 組波動明顯比平常大（約 {rg}）"
        en = f"After these releases {len(big)} of {n} comparisons move clearly more than usual ({lo:.1f}–{hi:.1f}x)"
    else:
        zh, en = f"這些數據公布後，{n} 組比較的波動都看不出明顯比平常大", f"None of {n} comparisons moves clearly more than usual"
    if moved:
        ls = "、".join(f"{e['zh']}後的{_name(a)}" for e, a in moved[:3])
        zh += f"；平均往哪邊走，只有{ls}跟平常明顯不同。"
        en += f"; the average direction differs clearly in {len(moved)} of them."
    else:
        maybe = max(((e, a) for e in evs for a in e["assets"] if a["all"]["dir"] == "maybe"), key=lambda x: abs(x[1]["all"]["t"]), default=None)
        zh += "；但平均往哪邊走，沒有一組跟平常日子明顯不同"
        zh += f"（最接近的是{maybe[0]['zh']}後的{_name(maybe[1])}，差距可能只是巧合）。" if maybe else "，全部分不開（可能只是雜訊）。"
        en += "; the average direction is not clearly different from an ordinary day in any of them."
    gaps = [(e, a) for e in evs for a in e["assets"] if (a.get("spread") or {}).get("dir") == "clear"]
    if gaps:
        e, a = max(gaps, key=lambda x: abs(x[1]["spread"]["t"]))
        unit = "bp" if a["kind"] == "bp" else " 個百分點"
        zh += f"比較清楚的是結果好壞的差別：{e['zh']}高於和低於預期時，{_name(a)}平均差 {abs(a['spread']['gap']):.1f}{unit}。"
        en += f" Outcomes do separate: {e['en']} above vs below consensus differs by {abs(a['spread']['gap']):.1f}{'bp' if a['kind'] == 'bp' else ' pts'} in {a['en']}."
    return {"zh": zh, "en": en}


def upcoming(eng, rel: Dict, evs: List[Dict], today: date) -> List[Dict]:
    cal = EC.load()
    out = []
    for key, zh, en, *_ in EVENTS:
        nxt = next((x for x in CLK.dates_for(eng, key, rel) if x >= today.isoformat()), None)
        if not nxt or (date.fromisoformat(nxt) - today).days > UPCOMING_DAYS:
            continue
        ev = next((e for e in evs if e["key"] == key), None)
        if ev is None:
            continue
        r = _pick(key, (cal.get(nxt) or {}).get("rows") or [])
        out.append({"key": key, "zh": zh, "en": en, "date": nxt, "days": (date.fromisoformat(nxt) - today).days, "ev": ev,
                    "cons": (r or {}).get("cons") or "", "prev": (r or {}).get("prev") or "", "actual": (r or {}).get("actual") or ""})
    return sorted(out, key=lambda x: x["date"])


def build(eng) -> Dict:
    d, rel = load(), CLK.load()
    today = EC.us_today()
    m = getattr(eng, "market", None)
    if m is None:
        return {"available": False}
    prices = {}
    for _a, sym, *_ in ASSETS:
        try:
            prices[sym] = completed(m.series(sym).dropna(), sym)   # a release-day "close" must be a finished session
        except Exception:  # noqa: BLE001
            continue
    seen = d.get("days") or {}
    events = {k: valid_dates(k, CLK.dates_for(eng, k, rel), seen.get(k) or {}, today.isoformat()) for k, *_ in EVENTS}
    evs = study(prices, events, seen)
    if not evs:
        return {"available": False}
    got = {k: [x for x, r in (seen.get(k) or {}).items() if r.get("c")] for k, *_ in EVENTS}
    return {"available": True, "events": evs, "lead": lead(evs), "upcoming": upcoming(eng, rel, evs, today), "ts": d.get("ts"), "asof": d.get("asof"),
            "cons_first": {k: min(v) for k, v in got.items() if v}, "checked": sum(len(v) for v in seen.values())}
