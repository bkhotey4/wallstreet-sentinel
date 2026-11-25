"""台股開盤前預估＋被迫賣方（2026-11-20，2027 台股準備清單第 3 項）。

11/20 加權指數 −6.23%：主角不是外資（−95 億），而是被迫賣股的人——融資一天減 491 億、自營商避險 −290 億、
槓桿 ETF 收盤前調整。這個模組把那天才拼出來的東西每天自動算好：

* 台積電 ADR 溢價 = ADR ÷ 5 × 美元兌台幣 ÷ 2330 收盤 − 1（1 張 ADR = 5 股）：今天、近一年百分位與中位數，
  以及「溢價回到近 20 天常態」時 2330 下一個交易日的換算區間（四分位）。
* 隔夜：費城半導體、那斯達克期貨、日經、韓股、美元兌台幣（Yahoo chart API，和台灣 ETF 頁同一個來源）。
* 融資：證交所 MI_MARGN 每天的前日／今日餘額 → 單日增減；大跌日的追繳與處分日曆
  （證交所說明：T 日收盤後通知、T+2 日前補繳、T+3 日起處分；交易日扣掉證交所休市日）。
* 證交所 BFI82U：自營商（避險）、自營商（自行買賣）、投信、外資買賣超。
* 00631L（元大台灣50正2）收盤前調整的估計 = L×(L−1)×標的當天報酬×前一天規模；
  規模與淨值用證交所 ETF 即時淨值檔（發行商估計淨值，tw_etf 已每天抓），標的報酬用 0050 的淨值變化。只是估計。

全部是計算或官方數字，每個數字帶日期；不預測、不建議。快取 data_cache/econ_tw_preopen.json（CI 之間保留）。"""
from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timedelta
from statistics import median
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR
from . import http
from .tw_margin import voided

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_preopen.json"
SYMS = ["TSM", "2330.TW", "TWD=X", "^TWII", "^SOX", "NQ=F", "^N225", "^KS11"]
PX_FRESH = 25 * 60                       # Yahoo charts: at most once per 25 minutes
RETRY = 3600                             # an official day not published yet: try again after an hour
DAYS = 8                                 # trading days of margin / BFI82U kept on the card
ADR_SHARES = 5
U_MG = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"
U_BFI = "https://www.twse.com.tw/rwd/zh/fund/BFI82U"
HDR = {"Accept": "application/json, text/plain, */*", "Referer": "https://www.twse.com.tw/"}
SRC = {"mg": "https://www.twse.com.tw/zh/trading/margin/mi-margn.html",
       "bfi": "https://www.twse.com.tw/zh/trading/foreign/bfi82u.html",
       "etf": "https://mis.twse.com.tw/stock/data/all_etf.txt",
       "rule": "https://money.udn.com/money/story/5607/9658938",
       "yahoo": "https://finance.yahoo.com/quote/TSM/history"}


def _num(s) -> Optional[float]:
    try:
        return float(str(s).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ parsers (pure)
def parse_chart(js: Dict) -> Optional[Dict]:
    """Yahoo chart → {"c": [[local date, close]], "t": unix time of the last price}.  Each symbol's own calendar day
    (TSM in New York, 2330 in Taipei): the ADR's day D trades after 2330's day D closes."""
    try:
        r = js["chart"]["result"][0]
    except (KeyError, IndexError, TypeError):
        return None
    meta = r.get("meta") or {}
    off = int(meta.get("gmtoffset") or 0)
    ts = r.get("timestamp") or []
    cl = ((r.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    c = [[datetime.utcfromtimestamp(int(t) + off).strftime("%Y-%m-%d"), round(float(v), 4)] for t, v in zip(ts, cl) if v]
    if len(c) < 2:
        return None
    t = meta.get("regularMarketTime")
    px = meta.get("regularMarketPrice")
    if px and t:
        td = datetime.utcfromtimestamp(int(t) + off).strftime("%Y-%m-%d")
        if td == c[-1][0]:
            c[-1][1] = round(float(px), 4)                # the last bar is today's: use the live price
        elif td > c[-1][0]:
            c.append([td, round(float(px), 4)])           # the daily series lags (Nikkei 11-20 missing at 00:00): add today
    return {"c": c, "t": int(t) if t else None}


def parse_mg(js: Dict) -> Optional[Tuple[float, float]]:
    """MI_MARGN (selectType=MS) → (前日餘額, 今日餘額) of 融資金額, in 億元 (the file is in 仟元)."""
    if not isinstance(js, dict) or js.get("stat") != "OK":
        return None
    for tb in js.get("tables") or []:
        for r in tb.get("data") or []:
            if r and str(r[0]).startswith("融資金額"):
                prev, now = _num(r[-2]), _num(r[-1])
                if prev and now:
                    return round(prev / 1e5, 2), round(now / 1e5, 2)
    return None


def parse_bfi(js: Dict) -> Optional[Dict[str, float]]:
    """BFI82U day → net buy (億元) of 自營商避險 / 自營商自行買賣 / 投信 / 外資 / 合計; a missing row stays out (never 0)."""
    if not isinstance(js, dict) or js.get("stat") != "OK" or not js.get("data"):
        return None
    out = {}
    for r in js["data"]:
        k, v = str(r[0]), _num(r[-1])
        if v is None:
            continue
        key = ("hedge" if "避險" in k else "self" if "自行" in k else "trust" if k.startswith("投信")
               else "foreign" if k.startswith("外資及陸資") else "total" if k.startswith("合計") else None)
        if key:
            out[key] = round(v / 1e8, 1)
    return out if "hedge" in out else None


# ------------------------------------------------------------------ calculations (pure)
def premiums(adr: List, tw: List, fx: List) -> List[Tuple[str, float]]:
    """Aligned ADR premium (%) per day D: ADR close on its day D ÷ 5 × USD/TWD on D ÷ 2330 close on D − 1."""
    a, f = dict(map(tuple, adr)), dict(map(tuple, fx))
    out, last_fx = [], None
    for d, c in tw:
        last_fx = f.get(d, last_fx)
        if d in a and last_fx and c:
            out.append((d, round((a[d] / ADR_SHARES * last_fx / c - 1) * 100, 3)))
    return out


def _q(xs: List[float], p: float) -> float:
    s = sorted(xs)
    k = (len(s) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def adr_view(adr: List, tw: List, fx: List) -> Optional[Dict]:
    """Today's premium against its own year, and the 2330 price the ADR implies if the premium goes back to its
    last-20-day normal (25th–75th percentile, median in the middle)."""
    ser = premiums(adr, tw, fx)
    if len(ser) < 30 or not adr or not tw or not fx:
        return None
    x = adr[-1][1] / ADR_SHARES * fx[-1][1]             # newest ADR in Taiwan dollars per share
    now = (x / tw[-1][1] - 1) * 100                     # against the newest 2330 close
    yr = [p for _, p in ser[-252:]]
    m20 = [p for _, p in ser[-21:-1]] or [p for _, p in ser[-20:]]   # the 20 days before today
    pct = round(sum(1 for p in yr if p <= now) / len(yr) * 100)
    q25, q50, q75 = _q(m20, .25), _q(m20, .5), _q(m20, .75)
    imp = lambda p: x / (1 + p / 100)                   # noqa: E731
    return {"now": round(now, 2), "pct": pct, "med_1y": round(median(yr), 2), "n_1y": len(yr),
            "q25": round(q25, 2), "med20": round(q50, 2), "q75": round(q75, 2), "x": round(x, 1),
            "adr": adr[-1], "fx": fx[-1], "tw": tw[-1],
            "lo": round(imp(q75), 1), "mid": round(imp(q50), 1), "hi": round(imp(q25), 1),
            "chg_mid": round((imp(q50) / tw[-1][1] - 1) * 100, 2), "since": ser[-len(yr)][0]}


def adr_light(pct: Optional[int]) -> str:
    """Self-designed: the premium at an extreme of its own year (≤5th or ≥95th percentile) is red, ≤15th / ≥85th yellow."""
    if pct is None:
        return "⚪"
    return "🔴" if pct <= 5 or pct >= 95 else "🟡" if pct <= 15 or pct >= 85 else "🟢"


def mg_light(chg_pct: Optional[float]) -> str:
    """Margin balance down 5% or more in one day = red (11/20 was −10.1%), 2.5% or more = yellow."""
    if chg_pct is None:
        return "⚪"
    return "🔴" if chg_pct <= -5 else "🟡" if chg_pct <= -2.5 else "🟢"


def tw_days_after(d: str, n: int, closed: Dict[str, str]) -> str:
    """The n-th Taiwan trading day after d (weekends and the exchange's own holiday list skipped)."""
    x = date.fromisoformat(d)
    while n > 0:
        x += timedelta(days=1)
        if x.weekday() < 5 and x.isoformat() not in closed:
            n -= 1
    return x.isoformat()


def closed_days(days: List[str], now: Optional[datetime] = None) -> List[str]:
    """Without today before the 13:30 close (+30 min): a half-finished session is not a fall yet (11-25)."""
    n = now or datetime.utcnow() + timedelta(hours=8)
    return [d for d in days if not (d == n.date().isoformat() and n.hour < 14)]


def call_calendar(days: List[str], twii: List, mg: Dict[str, List[float]], closed: Dict[str, str]) -> List[Dict]:
    """For each recent day with a big fall (TAIEX ≤ −2% or margin ≤ −2.5%): notice after that close, top up by T+2,
    disposal from T+3 (TWSE rule as explained in 2026-07)."""
    px = dict(map(tuple, twii))
    seq = [d for d, _ in twii]
    out = []
    for d in days:
        i = seq.index(d) if d in seq else -1
        ix = (px[d] / px[seq[i - 1]] - 1) * 100 if i > 0 else None
        m = mg.get(d)
        mc = (m[1] / m[0] - 1) * 100 if m and m[0] else None
        if (ix is not None and ix <= -2) or (mc is not None and mc <= -2.5):
            due = tw_days_after(d, 3, closed)
            out.append({"d": d, "void": voided(d, due), "ix": None if ix is None else round(ix, 2), "mg": None if mc is None else round(mc, 2),
                        "notice": d, "topup": tw_days_after(d, 2, closed), "dispose": due})
    return out


def lev_etf(nav: Dict[str, Dict], code: str = "00631L", base: str = "0050", lev: float = 2.0) -> Optional[Dict]:
    """Estimated close-of-day futures adjustment of a daily-reset leveraged ETF: L·(L−1)·r·(yesterday's size)."""
    e, b = nav.get(code) or {}, nav.get(base) or {}
    try:
        r = b["nav"] / b["prev_nav"] - 1
        size = e["units"] * e["prev_nav"] / 1e8
    except (KeyError, TypeError, ZeroDivisionError):
        return None
    return {"code": code, "name": e.get("name") or code, "date": e.get("date"), "r": round(r * 100, 2),
            "size": round(size, 0), "trade": round(lev * (lev - 1) * r * size, 0), "lev": lev}


def overnight(px: Dict[str, Dict]) -> List[Dict]:
    names = [("^SOX", "費城半導體"), ("NQ=F", "那斯達克期貨"), ("TSM", "台積電 ADR"), ("^N225", "日經 225"),
             ("^KS11", "韓國 KOSPI"), ("TWD=X", "美元兌台幣")]
    out = []
    for s, n in names:
        c = (px.get(s) or {}).get("c") or []
        if len(c) >= 2 and c[-2][1]:
            out.append({"s": s, "n": n, "d": c[-1][0], "p": c[-1][1], "chg": round((c[-1][1] / c[-2][1] - 1) * 100, 2),
                        "t": (px.get(s) or {}).get("t")})
    return out


# ------------------------------------------------------------------ cache + refresh
def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    try:
        FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        log.warning("tw_preopen cache not saved: %s", e)


def settled(day: str, fetched: Optional[float]) -> bool:
    """True when a stored day was read late enough to be final.  證交所 revises BFI82U the same evening (11/25: 投信
    +535.3 億 in the afternoon, +550.3 億 at 22:00) and MI_MARGN overnight, so a day keeps being re-read until noon of
    the next day, Taipei (12:00 = 04:00 UTC)."""
    if not fetched:
        return False
    return float(fetched) >= datetime.fromisoformat(day + "T04:00:00+00:00").timestamp() + 86400


async def refresh() -> Dict:
    d = load()
    now = time.time()
    if now - float(d.get("px_ts") or 0) > PX_FRESH:
        px = dict(d.get("px") or {})
        for s in SYMS:
            q = s.replace("^", "%5E")
            try:
                js = await http.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{q}?range=2y&interval=1d",
                                    headers={"User-Agent": "Mozilla/5.0"}, timeout=25, retries=1)
                p = parse_chart(js)
                if p:
                    px[s] = p
            except Exception as e:  # noqa: BLE001
                log.warning("tw_preopen %s: %s", s, e if str(e) else type(e).__name__)
        d["px"], d["px_ts"] = px, now
    days = [x for x, _ in ((d.get("px") or {}).get("2330.TW") or {}).get("c", [])][-DAYS:]
    tried = d.setdefault("tried", {})
    for kind, url, parse in (("mg", U_MG, parse_mg), ("bfi", U_BFI, parse_bfi)):
        have = d.setdefault(kind, {})
        seen = d.setdefault("seen", {})
        for day in days:
            if (day in have and settled(day, seen.get(f"{kind}:{day}"))) or now - float(tried.get(f"{kind}:{day}", 0)) < RETRY:
                continue
            tried[f"{kind}:{day}"] = now
            ymd = day.replace("-", "")
            params = ({"response": "json", "date": ymd, "selectType": "MS"} if kind == "mg"
                      else {"response": "json", "dayDate": ymd, "type": "day"})
            try:
                v = parse(await http.get(url, headers=HDR, params=params, timeout=20, retries=1))
            except Exception as e:  # noqa: BLE001
                log.warning("tw_preopen %s %s: %s", kind, day, e if str(e) else type(e).__name__)
                v = None
            if v:
                have[day] = list(v) if kind == "mg" else v
                seen[f"{kind}:{day}"] = now
        d["seen"] = {k: t for k, t in seen.items() if k.split(":")[1] in days}
        d[kind] = {k: have[k] for k in sorted(have)[-40:]}
    d["tried"] = {k: v for k, v in tried.items() if now - v < 3 * 86400}
    d["ts"] = now
    _save(d)
    return d


def view_from(d: Dict, nav: Optional[Dict] = None, closed: Optional[Dict[str, str]] = None) -> Dict:
    px = d.get("px") or {}
    c = lambda s: (px.get(s) or {}).get("c") or []        # noqa: E731
    days = [x for x, _ in c("2330.TW")][-DAYS:]
    mg, bfi = d.get("mg") or {}, d.get("bfi") or {}
    mrows = []
    for day in days:
        m = mg.get(day)
        if m:
            ch = (m[1] / m[0] - 1) * 100
            mrows.append({"d": day, "prev": m[0], "now": m[1], "diff": round(m[1] - m[0], 1), "pct": round(ch, 2),
                          "light": mg_light(ch)})
    brows = [dict(bfi[x], d=x) for x in days if x in bfi]
    adr = adr_view(c("TSM"), c("2330.TW"), c("TWD=X"))
    return {"adr": adr, "adr_light": adr_light(adr["pct"] if adr else None), "adr_t": (px.get("TSM") or {}).get("t"),
            "night": overnight(px), "mg": mrows, "bfi": brows,
            "cal": call_calendar(closed_days(days), c("^TWII"), mg, closed or {}), "lev": lev_etf(nav or {}),
            "px_ts": d.get("px_ts"), "ts": d.get("ts")}


def view() -> Dict:
    nav, closed = {}, {}
    try:
        from . import tw_etf as TE
        nav = (TE.load() if hasattr(TE, "load") else {}).get("nav") or {}
    except Exception:  # noqa: BLE001
        nav = {}
    try:
        from . import exchange_cal as XC
        closed = XC.tw_closed()
    except Exception:  # noqa: BLE001
        closed = {}
    return view_from(load(), nav, closed)
