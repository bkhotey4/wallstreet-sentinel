"""被迫進出的錢（2026-11-16，使用者選的第 1–3 項）：不管看法、照規則或在固定日子一定要動的資金。全部由公開資料算出來：

  1 指數調整日曆（規則推算的日子＋過去同一種日子實際的收盤成交量）
    * 標普 500 季度調整：3、6、9、12 月第三個週五收盤後生效（和四巫日同一天）
    * 羅素指數：6 月第四個週五；2026 年起 12 月第二個週五再調一次（FTSE Russell 改為一年兩次）
    * MSCI 季度審查：2、5、8、11 月最後一個交易日收盤生效（台股在這一天收盤時調整外資的台股比重）
    * 台灣 50（0050 追蹤的指數）：3、6、9、12 月第三個週五收盤後生效
    「規則推算」的日子都拿過去幾年同一天的成交量驗證：卡片印出每種日子過去的收盤成交量是平常（前 20 個交易日中位數）的幾倍。
  2 機械式基金推估（模型估算，不是實際部位）
    * 波動控制基金：目標年化波動 10%，股票比重＝10% ÷ 近期實際波動（取 1 個月與 3 個月較高者），最多 150%
    * 趨勢跟隨基金（CTA）：每個市場看 1、3、12 個月的漲跌方向取平均（−1 全空～+1 全多），並算出「明天收在哪個價位以下，
      某個期間的趨勢就會翻負」（＝那麼多天前的收盤價）
    * 風險平價：股債 60 日相關係數（同漲同跌時兩邊一起減碼）
  3 季底再平衡（退休金）：聯準會金融帳（Z.1）退休基金持有的美股與總資產 → 季初股票比重；這一季股票（SPY）與債券（AGG）
    各漲跌多少 → 比重偏離 → 如果全部照比例調回季初的比重，要移動多少美股（上限估算；實際只有一部分會照規則調）。
Yahoo 日線（含成交量）、FRED 的 Z.1 數列；快取 data_cache/econ_forced.json（只存算好的結果與畫圖用的短序列）。"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import statistics
import time
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Tuple

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_forced.json"
TTL = 4 * 3600
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=5y&interval=1d"
Z1_EQ, Z1_TOT = "BOGZ1LM593064105Q", "BOGZ1FL594090005Q"     # pension funds: corporate equities (market value); total financial assets
# volume of the whole market on the day (the closing auction is where index funds trade): US = S&P 500 members, Taiwan = TAIEX
VOL_SYMS = {"sp": "^GSPC", "russell": "^GSPC", "msci": "^TWII", "tw50": "^TWII"}
TREND = {"^GSPC": "標普 500", "^NDX": "那斯達克 100", "^TWII": "台股加權指數", "ZN=F": "美國 10 年期公債期貨",
         "GC=F": "黃金", "CL=F": "原油", "DX-Y.NYB": "美元指數"}
OTHER = ("SPY", "AGG", "TLT")
VOL_ZH = {"^GSPC": "標普 500 成分股", "^TWII": "台股上市股票"}
LOOKS = (21, 63, 252)
TARGET_VOL, CAP = 0.10, 1.5


# ------------------------------------------------------------------ dates (pure, tested)
def nth_weekday(y: int, m: int, wd: int, n: int) -> date:
    d = date(y, m, 1)
    return d + timedelta(days=(wd - d.weekday()) % 7 + 7 * (n - 1))


def last_open(y: int, m: int, is_open: Callable[[date], bool]) -> date:
    d = (date(y + (m == 12), m % 12 + 1, 1)) - timedelta(days=1)
    while not is_open(d):
        d -= timedelta(days=1)
    return d


def on_or_before(d: date, is_open: Callable[[date], bool]) -> date:
    while not is_open(d):
        d -= timedelta(days=1)
    return d


KIND = {"sp": ("標普 500 季度調整", "S&P 500 quarterly rebalance"),
        "russell": ("羅素指數重組", "Russell reconstitution"),
        "msci": ("MSCI 季度審查生效", "MSCI quarterly review"),
        "tw50": ("台灣 50 指數季度調整", "FTSE TWSE Taiwan 50 review")}


def msci_day(y: int, m: int, us_open: Callable[[date], bool], us_early: Callable[[date], bool]) -> date:
    """MSCI quarterly reviews take effect as of the close of the month's last business day; when that is the US half day after
    Thanksgiving, MSCI used the Monday of that week instead (2024-11-25, 2025-11-24 — confirmed by the closing volume
    in Taiwan and of EWT; 2026-11-30 per MSCI's 2026-11-11 announcement)."""
    d = last_open(y, m, us_open)
    if us_early(d):
        d = on_or_before(d - timedelta(days=d.weekday()), us_open)
    return d


def index_dates(y0: int, y1: int, us_open: Callable[[date], bool], tw_open: Callable[[date], bool],
                us_early: Optional[Callable[[date], bool]] = None) -> List[Dict]:
    """Every rule-derived index event in years y0..y1: [{date, kind, market, tw_date?}] (market 'us' | 'tw').
    tw_date = the day Taiwan trades it (the event day, or the Taiwan trading day before when Taiwan is closed)."""
    us_early = us_early or (lambda d: False)
    out = []
    for y in range(y0, y1 + 1):
        for m in (3, 6, 9, 12):
            out.append({"date": on_or_before(nth_weekday(y, m, 4, 3), us_open).isoformat(), "kind": "sp", "market": "us"})
            out.append({"date": on_or_before(nth_weekday(y, m, 4, 3), tw_open).isoformat(), "kind": "tw50", "market": "tw"})
        out.append({"date": on_or_before(nth_weekday(y, 6, 4, 4), us_open).isoformat(), "kind": "russell", "market": "us"})
        if y >= 2026:
            out.append({"date": on_or_before(nth_weekday(y, 12, 4, 2), us_open).isoformat(), "kind": "russell", "market": "us"})
        for m in (2, 5, 8, 11):
            d = msci_day(y, m, us_open, us_early)
            out.append({"date": d.isoformat(), "kind": "msci", "market": "us", "tw_date": on_or_before(d, tw_open).isoformat()})
    return sorted(out, key=lambda x: (x["date"], x["kind"]))


def vol_ratio(dates: List[str], vols: List[float], day: str, n: int = 20) -> Optional[float]:
    """That day's volume ÷ the median of the n sessions before it (None when the day is missing)."""
    try:
        i = dates.index(day)
    except ValueError:
        return None
    prev = [v for v in vols[max(0, i - n): i] if v]
    return vols[i] / statistics.median(prev) if prev and vols[i] else None


# ------------------------------------------------------------------ mechanical funds (pure, tested)
def _rets(c: List[float]) -> List[float]:
    return [c[i] / c[i - 1] - 1 for i in range(1, len(c)) if c[i - 1]]


def _std(x: List[float]) -> float:
    return statistics.pstdev(x) if len(x) > 1 else float("nan")


def realized(c: List[float], n: int) -> float:
    return _std(_rets(c[-n - 1:])) * math.sqrt(252)


def vol_control(c: List[float], target: float = TARGET_VOL, cap: float = CAP) -> Optional[float]:
    if len(c) < 64:
        return None
    rv = max(realized(c, 21), realized(c, 63))
    return min(cap, target / rv) if rv > 0 else cap


def vol_control_view(c: List[float], shock: float = -0.03) -> Dict:
    now = vol_control(c)
    if now is None:
        return {}
    hist = [vol_control(c[: len(c) - k]) for k in range(0, min(504, len(c) - 64))]
    hist = [h for h in hist if h is not None]
    wk = vol_control(c[:-5]) if len(c) > 69 else None
    after = vol_control(c + [c[-1] * (1 + shock)])
    return {"now": now, "week": wk, "pct": sum(h <= now for h in hist) / len(hist) if hist else None,
            "after": after, "shock": shock, "rv21": realized(c, 21), "rv63": realized(c, 63)}


def trend_view(c: List[float]) -> Dict:
    """score −1..+1 (average sign of the 1/3/12-month moves) and each lookback's flip price (= the close that many days ago)."""
    if len(c) < max(LOOKS) + 1:
        return {}
    sig, flips = [], {}
    for n in LOOKS:
        base = c[-n - 1]
        sig.append(1 if c[-1] > base else -1)
        flips[n] = {"price": c[-n], "dist": c[-n] / c[-1] - 1, "up": c[-1] > base}   # tomorrow's base is c[-n]
    score = sum(sig) / len(sig)
    prev = [1 if c[-2] > c[-n - 2] else -1 for n in LOOKS]
    return {"score": score, "prev": sum(prev) / len(prev), "flips": flips, "last": c[-1]}


def corr(a: List[float], b: List[float]) -> Optional[float]:
    if len(a) != len(b) or len(a) < 20:
        return None
    try:
        return statistics.correlation(a, b)
    except statistics.StatisticsError:
        return None


# ------------------------------------------------------------------ pension rebalancing (pure, tested)
def pension_move(w0: float, total: float, r_eq: float, r_bd: float) -> Dict:
    """Start-of-quarter equity share w0 of `total` dollars; equities return r_eq, the rest returns r_bd.
    Dollars of equities to move back to w0 (negative = equities to reduce)."""
    eq, ot = w0 * total * (1 + r_eq), (1 - w0) * total * (1 + r_bd)
    w1 = eq / (eq + ot)
    return {"w0": w0, "w1": w1, "move": (w0 - w1) * (eq + ot), "total1": eq + ot}


def quarter_start(d: date) -> date:
    return date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


# ------------------------------------------------------------------ fetch
def parse_yahoo(js: Dict) -> Dict[str, list]:
    r = js["chart"]["result"][0]
    off = int((r.get("meta") or {}).get("gmtoffset") or 0)
    q = r["indicators"]["quote"][0]
    out = {"d": [], "c": [], "v": []}
    for t, c, v in zip(r["timestamp"], q["close"], q.get("volume") or [None] * len(q["close"])):
        if c:
            out["d"].append(datetime.fromtimestamp(t + off, timezone.utc).strftime("%Y-%m-%d"))
            out["c"].append(round(float(c), 6))
            out["v"].append(float(v) if v else 0.0)
    return out


async def _yahoo(syms: List[str]) -> Dict[str, Dict]:
    sem = asyncio.Semaphore(4)

    async def one(s: str):
        async with sem:
            try:
                return s, parse_yahoo(await http.get(YAHOO.format(s=s), timeout=30, retries=1))
            except Exception as e:  # noqa: BLE001
                log.info("forced px %s: %s", s, e if str(e) else type(e).__name__)
                return s, None
    return {s: v for s, v in await asyncio.gather(*(one(s) for s in syms)) if v and len(v["c"]) >= 260}


async def _z1() -> Dict[str, List]:
    """{quarter date: [pension equities, pension total financial assets]} in millions of dollars (FRED, the bot's key when set)."""
    from .fred import _one
    a, b = await asyncio.gather(_one(Z1_EQ, "2023-01-01"), _one(Z1_TOT, "2023-01-01"))
    out: Dict[str, List] = {}
    for k, x in a.items():
        if k in b.index:
            out[k.date().isoformat()] = [float(x), float(b[k])]
    return out


def build(px: Dict[str, Dict], z1: Dict[str, List], today: date, us_open, tw_open, us_early=None) -> Dict:
    """Everything the card and the alerts need, from the raw series."""
    v: Dict = {"asof": {s: x["d"][-1] for s, x in px.items()}}
    # 1. index events: next ones + how big the closing volume was on the same kind of day before
    evs = index_dates(today.year - 4, today.year + 1, us_open, tw_open, us_early)
    past: Dict[str, List] = {}
    for e in evs:
        s = VOL_SYMS[e["kind"]] if VOL_SYMS[e["kind"]] in px else None
        if e["date"] >= today.isoformat() or not s:
            continue
        day = e.get("tw_date") if s == "^TWII" and e.get("tw_date") else e["date"]
        if s == "^TWII" and day not in px[s]["d"]:          # a Taiwan holiday the official file of that year no longer lists
            prior = [x for x in px[s]["d"] if x < day and (date.fromisoformat(day) - date.fromisoformat(x)).days <= 4]
            day = prior[-1] if prior else day
        r = vol_ratio(px[s]["d"], px[s]["v"], day)
        if r:
            past.setdefault(e["kind"], []).append([e["date"], round(r, 2)])
    v["events"] = [e for e in evs if today.isoformat() <= e["date"] <= (today + timedelta(days=120)).isoformat()]
    v["past"] = {k: x[-12:] for k, x in past.items()}
    v["past_med"] = {k: statistics.median(r for _, r in x) for k, x in past.items() if x}
    # 2. mechanical funds
    if "^GSPC" in px:
        v["volctl"] = vol_control_view(px["^GSPC"]["c"])
    v["trend"] = {s: dict(trend_view(px[s]["c"]), name=nm, asof=px[s]["d"][-1]) for s, nm in TREND.items() if s in px and trend_view(px[s]["c"])}
    if "SPY" in px and "TLT" in px:
        a, b = px["SPY"], px["TLT"]
        common = sorted(set(a["d"]) & set(b["d"]))[-61:]
        ia, ib = {d: c for d, c in zip(a["d"], a["c"])}, {d: c for d, c in zip(b["d"], b["c"])}
        ra, rb = _rets([ia[d] for d in common]), _rets([ib[d] for d in common])
        v["rp"] = {"corr60": corr(ra, rb), "asof": common[-1] if common else None}
    # 3. pension rebalancing this quarter
    if z1 and "SPY" in px and "AGG" in px:
        q0 = quarter_start(today)
        last = max(z1)
        eq, tot = z1[last]
        def ret(s):  # noqa: E306
            d, c = px[s]["d"], px[s]["c"]
            base = [c[i] for i, x in enumerate(d) if x < q0.isoformat()]
            return (c[-1] / base[-1] - 1) if base else None
        r_eq, r_bd = ret("SPY"), ret("AGG")
        if r_eq is not None and r_bd is not None and tot > 0:
            pm = pension_move(eq / tot, tot * 1e6, r_eq, r_bd)          # Z.1 levels are in millions of dollars
            q_end = last_open(today.year, 3 * ((today.month - 1) // 3) + 3, us_open)
            v["pension"] = dict(pm, r_eq=r_eq, r_bd=r_bd, z1_date=last, q0=q0.isoformat(), q_end=q_end.isoformat(),
                                asof=min(px["SPY"]["d"][-1], px["AGG"]["d"][-1]), eq=eq * 1e6)
    return v


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _opens():
    from . import exchange_cal as XC
    hol = XC.us_holidays(date.today().year - 5, date.today().year + 2)
    early = XC.us_early(date.today().year - 5, date.today().year + 2, hol)
    twc = XC.tw_closed()

    def us(d: date) -> bool:
        return d.weekday() < 5 and d.isoformat() not in hol

    def tw(d: date) -> bool:
        return d.weekday() < 5 and d.isoformat() not in twc

    def ec(d: date) -> bool:
        return d.isoformat() in early
    return us, tw, ec


async def refresh(force: bool = False) -> Dict:
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts_try", 0)) < TTL:
        return d
    d["ts_try"] = now
    bad = []
    px = await _yahoo(sorted(set(VOL_SYMS.values()) | set(TREND) | set(OTHER)))
    if len(px) < 6:
        bad.append(f"prices {len(px)}")
    z1 = {}
    try:
        z1 = await _z1()
    except Exception as e:  # noqa: BLE001
        bad.append(f"z1: {e if str(e) else type(e).__name__}")
    if px:
        us, tw, ec = _opens()
        v = build(px, z1 or (d.get("view") or {}).get("_z1") or {}, date.today(), us, tw, ec)
        v["_z1"] = {k: z1[k] for k in sorted(z1)[-4:]} if z1 else (d.get("view") or {}).get("_z1")
        d["view"], d["ts"] = v, now
    if bad:
        log.warning("forced flows: %s", "; ".join(bad))
        HEALTH.fail("forced_flows", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("forced_flows", len(px), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def view(d: Optional[Dict] = None) -> Dict:
    d = load() if d is None else d
    return dict(d.get("view") or {}, ts=d.get("ts"))


# ------------------------------------------------------------------ alerts (pure, tested)
def alerts(v: Dict, today: date) -> List[Dict]:
    """Once each: an index event today or on the next trading day; the S&P 500 trend score turning; the vol-control share
    falling ≥ 20 % in a week."""
    out = []
    t1 = (today + timedelta(days=1)).isoformat()
    for e in v.get("events") or []:
        if e["date"] in (today.isoformat(), t1) or (today.weekday() == 4 and e["date"] <= (today + timedelta(days=3)).isoformat()):
            out.append({"key": f"forced:ev:{e['kind']}:{e['date']}", "kind": "event", "ev": e, "lv": 1})
    tr = (v.get("trend") or {}).get("^GSPC") or {}
    if tr and tr.get("prev") is not None and (tr["score"] > 0) != (tr["prev"] > 0):
        out.append({"key": f"forced:trend:^GSPC:{tr['asof']}:{'+' if tr['score'] > 0 else '-'}", "kind": "trend", "tr": tr,
                    "lv": 2 if tr["score"] <= -1 else 1})
    vc = v.get("volctl") or {}
    if vc.get("week") and vc.get("now") and vc["now"] <= vc["week"] * 0.8:
        out.append({"key": f"forced:volctl:{(v.get('asof') or {}).get('^GSPC', '')}", "kind": "volctl", "vc": vc, "lv": 1})
    return out
