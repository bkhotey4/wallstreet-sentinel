"""Per-stock valuation history for the whole-market check-up ("歷史估值區間"): each stock's P/E (or P/B) against its OWN
last five years, and the prices that today's earnings would imply at its historical low / middle / high multiples.

Taiwan (all listed + OTC): the exchanges publish every stock's P/E, P/B and dividend yield each day
    TWSE  /rwd/zh/afterTrading/BWIBBU_d      TPEx  /www/zh-tw/afterTrading/peQryDate
  One snapshot per month (the month's last trading day) for 60 months plus the latest day, filled a few dates per run.
US: SEC XBRL frames (one request = one quarter for every filer) — see refresh_us.
Hong Kong: no free per-stock valuation history exists, so it is reported as unavailable (never estimated).

The output is a description of where the multiple sits in its own history — never a price to buy at."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np

from ..config import DATA_DIR
from . import http

log = logging.getLogger(__name__)
MONTHS = 60
MIN_POINTS = 24                       # at least two years of monthly readings before a stock gets a range
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}


def _file(mk: str):
    return DATA_DIR / f"fullmarket_val_{mk}.json"


def load(mk: str) -> Dict:
    try:
        if _file(mk).exists():
            return json.loads(_file(mk).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("valuation history %s unreadable: %s", mk, e)
    return {}


def save(mk: str, d: Dict) -> None:
    tmp = _file(mk).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, _file(mk))


def _f(x) -> Optional[float]:
    try:
        v = float(str(x).replace(",", "").strip())
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def month_ends(today: date, n: int = MONTHS) -> List[date]:
    """Last calendar day of each of the previous n months (newest first)."""
    out, d = [], today.replace(day=1) - timedelta(days=1)
    for _ in range(n):
        out.append(d)
        d = d.replace(day=1) - timedelta(days=1)
    return out


def parse_twse(js: Dict) -> Dict[str, list]:
    if not js or js.get("stat") != "OK" or not js.get("data"):
        return {}
    f = js.get("fields") or []
    i_code, i_pe, i_pb, i_y = f.index("證券代號"), f.index("本益比"), f.index("股價淨值比"), f.index("殖利率(%)")
    return {str(r[i_code]).strip(): [_f(r[i_pe]), _f(r[i_pb]), _f(r[i_y])] for r in js["data"]}


def parse_tpex(js: Dict) -> Dict[str, list]:
    t = ((js or {}).get("tables") or [{}])[0]
    if not t.get("data"):
        return {}
    f = t.get("fields") or []
    i_code, i_pe, i_pb, i_y = f.index("股票代號"), f.index("本益比"), f.index("股價淨值比"), f.index("殖利率(%)")
    return {str(r[i_code]).strip(): [_f(r[i_pe]), _f(r[i_pb]), _f(r[i_y])] for r in t["data"]}


async def _tw_day(d: date) -> Optional[Dict[str, list]]:
    """{} = the exchange answered but has no data (holiday); None = no proper answer (blocked / down): retry another run."""
    a = await http.get(f"https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d?date={d:%Y%m%d}&selectType=ALL&response=json",
                       headers=UA, timeout=30, retries=1)
    if not isinstance(a, dict) or "stat" not in a:
        return None
    out = parse_twse(a)
    if not out:
        return {}
    await asyncio.sleep(2.5)                                        # TWSE blocks bursts
    try:
        b = await http.get(f"https://www.tpex.org.tw/www/zh-tw/afterTrading/peQryDate?date={d:%Y/%m/%d}&response=json",
                           headers=UA, timeout=30, retries=1)
        out.update({k: v for k, v in parse_tpex(b).items() if k not in out})
    except Exception as e:  # noqa: BLE001
        log.info("TPEx P/E %s failed: %s", d, e)
    return out


async def refresh_tw(budget_s: float = 90, today: Optional[date] = None) -> Dict:
    """Fill missing month-end snapshots (newest first) and the latest trading day, within the time budget."""
    today = today or date.today()
    d = load("tw")
    snaps: Dict[str, Dict] = d.get("snaps") or {}
    tried: Dict[str, str] = d.get("tried") or {}                     # month → date already found empty (holiday streaks)
    t0, got = time.time(), 0
    want = [("latest", today)] + [(m.strftime("%Y-%m"), m) for m in month_ends(today)]
    for key, end in want:
        if time.time() - t0 > budget_s:
            break
        if key != "latest" and any(k[:7] == key for k in snaps):
            continue
        if key == "latest" and d.get("latest_day") == today.isoformat():
            continue
        for back in range(7):                                       # walk back to the month's last trading day
            day = end - timedelta(days=back)
            if day.weekday() >= 5 or tried.get(day.isoformat()):
                continue
            try:
                rows = await _tw_day(day)
            except Exception as e:  # noqa: BLE001
                log.info("TW P/E %s failed: %s", day, e)
                rows = None
            await asyncio.sleep(2.5)
            if rows is None:
                break                                               # source trouble: leave this month for a later run
            if rows:
                if key == "latest":
                    d["latest"] = {"date": day.isoformat(), "rows": rows}
                    d["latest_day"] = today.isoformat()
                else:
                    snaps[day.isoformat()] = rows
                got += 1
                break
            tried[day.isoformat()] = "empty"
            if time.time() - t0 > budget_s:
                break
    cut = (today - timedelta(days=31 * (MONTHS + 2))).isoformat()
    d["snaps"] = {k: v for k, v in snaps.items() if k >= cut}
    d["tried"] = {k: v for k, v in tried.items() if k >= cut}
    d["ts"] = time.time()
    save("tw", d)
    return {"fetched": got, "months": len(d["snaps"]), "latest": (d.get("latest") or {}).get("date")}


def _zone(hist: List[float], now: float, px: float, min_points: int = MIN_POINTS) -> Optional[Dict]:
    h = np.array([x for x in hist if x is not None and x > 0])
    if len(h) < min_points or not now or now <= 0 or not px:
        return None
    q1, q2, q3 = (float(np.percentile(h, p)) for p in (25, 50, 75))
    return {"now": now, "pct": float((h < now).mean() * 100), "n": int(len(h)),
            "p25": px * q1 / now, "p50": px * q2 / now, "p75": px * q3 / now, "m25": q1, "m50": q2, "m75": q3}


def zones_tw(prices: Dict[str, float]) -> Dict[str, Dict]:
    """code → {metric, now, pct, p25/p50/p75 (implied prices), m25/m50/m75 (multiples), n, asof}.
    P/E when the company has one today (positive earnings); otherwise P/B (losses, or P/E missing)."""
    d = load("tw")
    snaps, latest = d.get("snaps") or {}, d.get("latest") or {}
    if not latest.get("rows") or len(snaps) < MIN_POINTS:
        return {}
    days = sorted(snaps)
    out = {}
    for code, (pe, pb, y) in latest["rows"].items():
        px = prices.get(code)
        if not px:
            continue
        for metric, i, now in (("本益比", 0, pe), ("股價淨值比", 1, pb)):
            if now is None or now <= 0:
                continue
            z = _zone([(snaps[k].get(code) or [None, None, None])[i] for k in days], now, px)
            if z:
                out[code] = {"metric": metric, "asof": latest["date"], "yld": y, **{k: round(v, 3) if isinstance(v, float) else v for k, v in z.items()}}
                break
    return out


# ============================================================ US: SEC frames + Yahoo monthly prices
US_Q = 22                              # quarters of history (5 years + the TTM window)
US_MIN = 12                            # at least 3 years of quarterly readings before a stock gets a range
US_FRAMES = {"ni": ("us-gaap", "NetIncomeLoss", "USD"), "eq": ("us-gaap", "StockholdersEquity", "USD"),
             "sh": ("dei", "EntityCommonStockSharesOutstanding", "shares")}


def _quarters(today: date, n: int) -> List[str]:
    from .earnings_data import cy_quarters
    return cy_quarters(today, n + 1)[1:]                 # completed quarters only (newest first)


def _period_age(per: str, today: date) -> int:
    y = int(per[2:6])
    if len(per) == 6:
        return (today - date(y, 12, 31)).days
    return (today - date(y, int(per[-1]) * 3, 28)).days


async def refresh_us(syms: List[str], budget_s: float = 120, today: Optional[date] = None) -> Dict:
    """1) SEC frames: quarterly net income (+ annual, for the fiscal-Q4 hole), quarter-end equity and cover-page shares,
    every filer at once (~3 requests per quarter), kept and re-read weekly for 200 days as late filers arrive.
    2) Yahoo monthly closes + split history per ticker, re-read every 30 days."""
    from .earnings_data import SEC_HDR, parse_frame, parse_frame_ends
    today = today or date.today()
    d = load("us")
    fr: Dict[str, Dict] = d.get("frames") or {}
    t0, n_fr = time.time(), 0
    pers = _quarters(today, US_Q)
    years = sorted({p[:6] for p in pers})
    jobs = [(k, p) for p in pers for k in US_FRAMES] + [("ni", y) for y in years]
    for k, per in jobs:
        if time.time() - t0 > budget_s * 0.4:
            break
        tax, tag, unit = US_FRAMES[k]
        p = per + ("I" if k in ("eq", "sh") else "")
        key = f"{tag}/{p}"
        old = fr.get(key)
        if old and old.get("d"):
            age = (today - date.fromisoformat(old["d"])).days
            if age < 7 or _period_age(per, today) > 200:
                continue
        try:
            js = await http.get(f"https://data.sec.gov/api/xbrl/frames/{tax}/{tag}/{unit}/{p}.json", headers=SEC_HDR, timeout=40, retries=0)
        except Exception as e:  # noqa: BLE001
            if "404" in str(e):
                fr[key] = {"v": {}, "d": today.isoformat()}
            else:
                log.info("SEC frame %s failed: %s", key, e)
            await asyncio.sleep(0.3)
            continue
        rec = {"v": parse_frame(js), "d": today.isoformat()}
        if len(per) == 6:                                       # annual: keep each filer's fiscal year end
            rec["e"] = parse_frame_ends(js)
        fr[key] = rec
        n_fr += 1
        await asyncio.sleep(0.15)                               # SEC allows 10 requests per second
    keep = {f"{US_FRAMES[k][1]}/{p}{'I' if k in ('eq', 'sh') else ''}" for k in US_FRAMES for p in pers} | {f"NetIncomeLoss/{y}" for y in years}
    d["frames"] = {k: v for k, v in fr.items() if k in keep}
    px: Dict[str, Dict] = d.get("px") or {}
    due = [s for s in syms if not px.get(s) or time.time() - float(px[s].get("ts", 0)) > 30 * 86400]
    due.sort(key=lambda s: float((px.get(s) or {}).get("ts", 0)))
    n_px, sem = 0, asyncio.Semaphore(6)

    async def one(s: str):
        nonlocal n_px
        async with sem:
            if time.time() - t0 > budget_s:
                return
            try:
                js = await http.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=6y&interval=1mo&events=split",
                                    headers={"User-Agent": "Mozilla/5.0"}, timeout=25, retries=0)
                r = js["chart"]["result"][0]
                c = r["indicators"]["quote"][0]["close"]
                ts = r.get("timestamp") or []
                m = {date.fromtimestamp(t).strftime("%Y-%m"): round(v, 4) for t, v in zip(ts, c) if v}
                sp = [[date.fromtimestamp(int(x["date"])).isoformat(), float(x["numerator"]) / float(x["denominator"])]
                      for x in ((r.get("events") or {}).get("splits") or {}).values() if x.get("denominator")]
                px[s] = {"m": m, "sp": sorted(sp), "ts": time.time()}
                n_px += 1
            except Exception:  # noqa: BLE001
                px[s] = {**(px.get(s) or {}), "ts": time.time() - 23 * 86400}      # retry in about a week
            await asyncio.sleep(0.2)

    await asyncio.gather(*(one(s) for s in due[:1500]))
    live = set(syms)
    d["px"] = {s: v for s, v in px.items() if s in live}
    d["ts"] = time.time()
    save("us", d)
    return {"frames": n_fr, "frames_total": len(d["frames"]), "prices": n_px,
            "priced": sum(1 for v in d["px"].values() if v.get("m")), "due_left": max(0, len(due) - n_px)}


def _unadj(m: Dict[str, float], sp: List[list], ym: str) -> Optional[float]:
    """Yahoo's monthly close is split-adjusted; undo the splits that happened after that month."""
    v = m.get(ym)
    if v is None:
        return None
    f = 1.0
    for dt, r in sp:
        if dt[:7] > ym and r > 0:
            f *= r
    return v * f


def zones_us(prices: Dict[str, float], today: Optional[date] = None) -> Dict[str, Dict]:
    """ticker → same shape as zones_tw.  P/E = (price × cover-page shares) ÷ trailing-4-quarter net income at each quarter
    end, from the numbers as they stood then; P/B (÷ equity) when today's trailing earnings are not positive.  A constant
    share-class miscount (dual classes) cancels out: only today's multiple against the company's own past ones is used."""
    from .earnings_data import FrameReader
    from .edgar_holdings import _MAP_FILE
    today = today or date.today()
    d = load("us")
    fr, px = d.get("frames") or {}, d.get("px") or {}
    if not fr or not px:
        return {}
    try:
        tick = json.loads(_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    pers = _quarters(today, US_Q)[::-1]                          # oldest → newest
    rd = FrameReader(fr, pers)
    out = {}
    for s, now_px in prices.items():
        info = tick.get(s.upper().replace("-", ".")) or tick.get(s.upper())
        p = px.get(s)
        if not info or not p or not p.get("m") or not now_px:
            continue
        cik = str(info["cik"])
        ni = [rd.tag_val("NetIncomeLoss", cik, q) for q in pers]
        sh = [((fr.get(f"EntityCommonStockSharesOutstanding/{q}I") or {}).get("v") or {}).get(cik) for q in pers]
        eq = [((fr.get(f"StockholdersEquity/{q}I") or {}).get("v") or {}).get(cik) for q in pers]
        pe_h, pb_h = [], []
        last = {"ttm": None, "sh": None, "eq": None}
        for i, q in enumerate(pers):
            ym = f"{q[2:6]}-{int(q[-1]) * 3:02d}"
            price = _unadj(p["m"], p.get("sp") or [], ym)
            shares = sh[i] or (sh[i - 1] if i else None)
            win = ni[i - 3:i + 1] if i >= 3 else []
            ttm = sum(win) if len(win) == 4 and all(x is not None for x in win) else None
            if price and shares:
                mc = price * shares
                if ttm and ttm > 0:
                    pe_h.append(mc / ttm)
                if eq[i] and eq[i] > 0:
                    pb_h.append(mc / eq[i])
            if ttm is not None:
                last["ttm"] = ttm
            if shares:
                last["sh"] = shares
            if eq[i]:
                last["eq"] = eq[i]
        if not last["sh"]:
            continue
        mc_now = now_px * last["sh"]
        for metric, hist, den in (("本益比", pe_h, last["ttm"]), ("股價淨值比", pb_h, last["eq"])):
            if not den or den <= 0 or len(hist) < US_MIN:
                continue
            z = _zone(hist, mc_now / den, now_px, US_MIN)
            if z:
                out[s] = {"metric": metric, "asof": pers[-1], **{k: round(v, 3) if isinstance(v, float) else v for k, v in z.items()}}
                break
    return out
