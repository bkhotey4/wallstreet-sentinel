"""財報資料：美股財報日曆、EPS 預期與驚喜、SEC 季報數字（精選池與全市場科技股）、台股電子業月營收。

  * Nasdaq earnings calendar  api.nasdaq.com/api/calendar/earnings?date=D  (no date shift; past dates carry eps + surprise)
  * Nasdaq earnings surprise  api.nasdaq.com/api/company/SYM/earnings-surprise   (last 4 quarters, EPS vs consensus)
  * Nasdaq quarterly financials (fallback for foreign filers without US-GAAP quarters, e.g. TSM / ASML)
  * SEC XBRL companyfacts (curated tech + semis): full quarterly history; Q4 = fiscal year − Q1..Q3
  * SEC XBRL frames (whole US tech list): one request returns every filer's value for one concept and calendar quarter
  * TWSE / TPEx open data t187ap05: latest monthly revenue of every listed / OTC company (archived month by month)"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR, SEC_USER_AGENT, SETTINGS
from ..health import HEALTH
from . import http
from .econcal import NQ_HDR, num, us_today

log = logging.getLogger(__name__)
F_DAYS = DATA_DIR / "earn_days.json"
F_SURP = DATA_DIR / "earn_surprise.json"
F_FACTS = DATA_DIR / "earn_facts.json"
F_FRAMES = DATA_DIR / "earn_frames.json"
F_TW = DATA_DIR / "earn_twrev.json"
F_TWPE = DATA_DIR / "earn_twpe.json"
F_ANN = DATA_DIR / "earn_nqann.json"
SEC_HDR = {"User-Agent": SEC_USER_AGENT, "Accept": "application/json"}
TECH_THEMES = ("半導體", "AI伺服器與雲端", "科技平台", "軟體與資安")
TW_ELEC = ("半導體業", "電腦及週邊設備業", "光電業", "通信網路業", "電子零組件業", "電子通路業", "資訊服務業", "其他電子業", "數位雲端")


def cfg() -> Dict:
    return SETTINGS.get("earnings", {}) or {}


def _load(p) -> Dict:
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", p.name, e)
    return {}


def _save(p, d) -> None:
    try:
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        tmp.replace(p)
    except Exception as e:  # noqa: BLE001
        log.warning("%s not saved: %s", p.name, e)


# ============================================================ earnings calendar
def parse_cal(js: Dict) -> List[Dict]:
    out = []
    for r in ((js or {}).get("data") or {}).get("rows") or []:
        sym = str(r.get("symbol") or "").strip().upper()
        if not sym:
            continue
        t = str(r.get("time") or "")
        out.append({"sym": sym.replace(".", "-"), "name": str(r.get("name") or "").strip(),
                    "time": "pre" if "pre" in t else "after" if "after" in t else "",
                    "fq": str(r.get("fiscalQuarterEnding") or ""), "eps_f": num(r.get("epsForecast")), "n_est": num(r.get("noOfEsts")),
                    "eps_ly": num(r.get("lastYearEPS")), "mcap": num(r.get("marketCap")), "eps": num(r.get("eps")),
                    "surprise": num(r.get("surprise"))})
    return out


async def _cal_day(d: date) -> List[Dict]:
    js = await http.get("https://api.nasdaq.com/api/calendar/earnings", params={"date": d.isoformat()}, headers=NQ_HDR, timeout=20, retries=1)
    return parse_cal(js)


async def refresh_calendar(budget_s: float = 90, force_days: Optional[List[date]] = None) -> Dict[str, Dict]:
    days = _load(F_DAYS)
    today, now, t0 = us_today(), time.time(), time.time()
    back, ahead = int(cfg().get("cal_back", 10)), int(cfg().get("cal_ahead", 45))
    q = list(force_days or [])
    for i in range(-back, ahead + 1):
        d = today + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        rec = days.get(d.isoformat())
        age = now - float((rec or {}).get("ts", 0))
        if rec is None or (i < -3 and not rec.get("final")) or (-3 <= i <= 2 and age > 1800) or (2 < i <= 10 and age > 6 * 3600) \
                or (i > 10 and age > 20 * 3600):
            q.append(d)
    ok = err = 0
    for d in q:
        if time.time() - t0 > budget_s:
            break
        try:
            days[d.isoformat()] = {"ts": time.time(), "rows": await _cal_day(d), "final": (today - d).days > 3}
            ok += 1
        except Exception as e:  # noqa: BLE001
            err += 1
            log.info("earnings calendar %s: %s", d, e)
            if err >= 5 and not ok:
                break
        await asyncio.sleep(0.25)
    cut = (today - timedelta(days=back + 5)).isoformat()
    days = {k: v for k, v in days.items() if k >= cut}
    if ok:
        _save(F_DAYS, days)
    (HEALTH.fail("earnings_calendar", RuntimeError("Nasdaq earnings calendar failed"), every=3600) if err and not ok
     else HEALTH.ok("earnings_calendar", ok, every=3600))
    return days


# ============================================================ EPS surprise history (curated tech)
def parse_surprise(js: Dict) -> List[Dict]:
    rows = ((((js or {}).get("data") or {}).get("earningsSurpriseTable") or {}).get("rows")) or []
    out = []
    for r in rows:
        try:
            dr = datetime.strptime(str(r.get("dateReported")), "%m/%d/%Y").date().isoformat()
        except ValueError:
            dr = None
        out.append({"fq": r.get("fiscalQtrEnd"), "date": dr, "eps": num(r.get("eps")), "cons": num(r.get("consensusForecast")),
                    "surp": num(r.get("percentageSurprise"))})
    return out


async def refresh_surprises(syms: List[str], reported: Dict[str, str], budget_s: float = 60) -> Dict[str, Dict]:
    """Daily per symbol; again right after a new report date (reported = {sym: last report date seen in the calendar})."""
    cache = _load(F_SURP)
    t0, ok = time.time(), 0
    for s in syms:
        rec = cache.get(s) or {}
        last_seen = max([r.get("date") or "" for r in rec.get("rows", [])] or [""])
        stale = time.time() - float(rec.get("ts", 0)) > 20 * 3600
        new_rep = reported.get(s, "") > last_seen and time.time() - float(rec.get("ts", 0)) > 1800
        if not (stale or new_rep):
            continue
        if time.time() - t0 > budget_s:
            break
        try:
            js = await http.get(f"https://api.nasdaq.com/api/company/{s.replace('-', '.')}/earnings-surprise", headers=NQ_HDR, timeout=20, retries=1)
            cache[s] = {"ts": time.time(), "rows": parse_surprise(js)}
            ok += 1
        except Exception as e:  # noqa: BLE001
            log.info("earnings surprise %s: %s", s, e)
        await asyncio.sleep(0.3)
    if ok:
        _save(F_SURP, cache)
    return cache


# ============================================================ SEC companyfacts → quarterly series
REV_TAGS = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
            "SalesRevenueNet", "RevenuesNetOfInterestExpense")
CONCEPTS = {"gp": ("GrossProfit",), "cogs": ("CostOfRevenue", "CostOfGoodsAndServicesSold"), "op": ("OperatingIncomeLoss",),
            "ni": ("NetIncomeLoss",), "eps": ("EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted"),
            "rnd": ("ResearchAndDevelopmentExpense",), "inv": ("InventoryNet",)}


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _periods(facts: List[Dict], instant: bool = False) -> Tuple[Dict[Tuple[str, str], float], Dict[Tuple[str, str], float]]:
    """(quarters, years) keyed by (start, end) → value; duplicates resolved by the latest filing."""
    qs, ys, filed = {}, {}, {}
    for f in facts:
        if "end" not in f or f.get("val") is None:
            continue
        if instant:
            k = ("", f["end"])
            if f.get("filed", "") >= filed.get(k, ""):
                qs[k], filed[k] = float(f["val"]), f.get("filed", "")
            continue
        if "start" not in f:
            continue
        n = (_d(f["end"]) - _d(f["start"])).days
        k = (f["start"], f["end"])
        if f.get("filed", "") < filed.get(k, ""):
            continue
        filed[k] = f.get("filed", "")
        if 80 <= n <= 100:
            qs[k] = float(f["val"])
        elif 350 <= n <= 380:
            ys[k] = float(f["val"])
    return qs, ys


def quarterly(facts: List[Dict]) -> Dict[str, float]:
    """end date → quarterly value, with Q4 derived as fiscal year minus the three reported quarters inside it."""
    qs, ys = _periods(facts)
    out = {e: v for (s, e), v in qs.items()}
    for (ys_, ye), yv in ys.items():
        if ye in out:
            continue
        inside = sorted([(s, e, v) for (s, e), v in qs.items() if s >= ys_ and e < ye], key=lambda x: x[1])
        if len(inside) == 3 and (_d(ye) - _d(inside[-1][1])).days <= 100:
            out[ye] = yv - sum(v for *_x, v in inside)
    return out


def _units(cf: Dict, tag: str) -> List[Dict]:
    u = (((cf.get("facts") or {}).get("us-gaap") or {}).get(tag) or {}).get("units") or {}
    for k in ("USD", "USD/shares"):
        if k in u:
            return u[k]
    return next(iter(u.values()), []) if u else []


def parse_facts(cf: Dict) -> List[Dict]:
    """Quarterly table (newest last) from a companyfacts document: revenue, gross profit, operating income, net income,
    diluted EPS, R&D, inventory."""
    best, best_end = {}, ""
    for tag in REV_TAGS:                              # the revenue tag with the most recent quarter wins
        q = quarterly(_units(cf, tag))
        if q and max(q) > best_end:
            best, best_end = q, max(q)
    if not best:
        return []
    ser = {"rev": best}
    for k, tags in CONCEPTS.items():
        merged: Dict[str, float] = {}
        for tag in tags:
            if k == "inv":
                qs, _ = _periods(_units(cf, tag), instant=True)
                q = {e: v for (_s, e), v in qs.items()}
            else:
                q = quarterly(_units(cf, tag))
            for e, v in q.items():
                merged.setdefault(e, v)
        ser[k] = merged
    rows = []
    for e in sorted(best):
        r = {"end": e, "rev": best[e]}
        for k in CONCEPTS:
            r[k] = ser[k].get(e)
        if r["gp"] is None and r.get("cogs") is not None:
            r["gp"] = r["rev"] - r["cogs"]
        r.pop("cogs", None)
        rows.append(r)
    return rows[-16:]


def parse_nq_financials(js: Dict) -> List[Dict]:
    """Nasdaq quarterly income statement (4 quarters, values in $ thousands) → the same row shape."""
    t = (((js or {}).get("data") or {}).get("incomeStatementTable")) or {}
    hdr, rows = t.get("headers") or {}, t.get("rows") or []
    cols = [k for k in hdr if k != "value1"]
    get = {str(r.get("value1", "")).strip(): r for r in rows}
    out = []
    for c in cols:
        try:
            end = datetime.strptime(str(hdr[c]), "%m/%d/%Y").date().isoformat()
        except ValueError:
            continue
        v = lambda name: (num((get.get(name) or {}).get(c)) or None)  # noqa: E731
        k = lambda x: None if x is None else x * 1000  # noqa: E731
        rev = k(v("Total Revenue"))
        if rev is None:
            continue
        out.append({"end": end, "rev": rev, "gp": k(v("Gross Profit")), "op": k(v("Operating Income")), "ni": k(v("Net Income")),
                    "eps": None, "rnd": k(v("Research and Development")), "inv": None, "src": "nasdaq"})
    return sorted(out, key=lambda r: r["end"])


async def refresh_facts(syms: List[str], reported: Dict[str, str], budget_s: float = 150) -> Dict[str, Dict]:
    from .edgar_holdings import ticker_map
    cache = _load(F_FACTS)
    try:
        tmap = await ticker_map()
    except Exception as e:  # noqa: BLE001
        log.warning("SEC ticker map unavailable: %s", e)
        tmap = {}
    t0, ok, err = time.time(), 0, 0
    today = us_today().isoformat()
    for s in syms:
        rec = cache.get(s) or {}
        age = time.time() - float(rec.get("ts", 0))
        rep = reported.get(s, "")
        last_end = (rec.get("q") or [{}])[-1].get("end", "")
        recent_rep = rep and rep > last_end and (date.fromisoformat(today) - date.fromisoformat(rep)).days <= 75
        if not (age > 7 * 86400 or (recent_rep and age > 20 * 3600)):
            continue
        if time.time() - t0 > budget_s:
            break
        rows: List[Dict] = []
        cik = (tmap.get(s) or tmap.get(s.replace("-", ".")) or {}).get("cik")
        try:
            if cik:
                cf = await http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=40, retries=1)
                rows = parse_facts(cf)
                await asyncio.sleep(0.2)
            if not rows or rows[-1]["end"] < (date.fromisoformat(today) - timedelta(days=200)).isoformat():
                js = await http.get(f"https://api.nasdaq.com/api/company/{s.replace('-', '.')}/financials", params={"frequency": 2},
                                    headers=NQ_HDR, timeout=20, retries=1)
                nq = parse_nq_financials(js)
                if nq and (not rows or nq[-1]["end"] > rows[-1]["end"]):
                    rows = nq
            if rows:
                cache[s] = {"ts": time.time(), "q": rows, "cik": cik}
                ok += 1
        except Exception as e:  # noqa: BLE001
            err += 1
            log.info("facts %s: %s", s, e)
    if ok:
        _save(F_FACTS, cache)
    (HEALTH.fail("sec_facts", RuntimeError("companyfacts failed"), every=86400) if err and not ok else HEALTH.ok("sec_facts", ok, every=86400))
    return cache


# ============================================================ SEC frames (whole-market US tech, latest quarter)
FRAME_TAGS = {"rev": REV_TAGS[:3], "gp": ("GrossProfit",), "op": ("OperatingIncomeLoss",), "ni": ("NetIncomeLoss",),
              "eps": ("EarningsPerShareDiluted",), "ocf": ("NetCashProvidedByUsedInOperatingActivities",)}
INSTANT_TAGS = ("Goodwill", "CashAndCashEquivalentsAtCarryingValue", "ShortTermInvestments")


def cy_quarters(today: date, n: int = 6) -> List[str]:
    y, q = today.year, (today.month - 1) // 3 + 1
    out = []
    for _ in range(n):
        out.append(f"CY{y}Q{q}")
        q -= 1
        if q == 0:
            y, q = y - 1, 4
    return out


class FrameReader:
    """Values of one company from the cached frames, always from ONE tag per concept (the tag with the most quarters),
    so a company that switched revenue tags never mixes two definitions; CY Q4 = calendar year − Q1..Q3 of that tag."""

    def __init__(self, frames: Dict[str, Dict], pers: List[str]):
        self.fr, self.pers, self._best = frames or {}, pers, {}

    def _raw(self, tag: str, cik: str, per: str) -> Optional[float]:
        return ((self.fr.get(f"{tag}/{per}") or {}).get("v") or {}).get(cik)

    def tag_val(self, tag: str, cik: str, per: str) -> Optional[float]:
        v = self._raw(tag, cik, per)
        if v is None and per.endswith("Q4") and len(per) == 8:
            yv = self._raw(tag, cik, per[:6])
            parts = [self._raw(tag, cik, f"{per[:6]}Q{i}") for i in (1, 2, 3)]
            if yv is not None and all(p is not None for p in parts):
                v = yv - sum(parts)
        return v

    def best(self, k: str, cik: str) -> Optional[str]:
        key = (k, cik)
        if key not in self._best:
            score = [(sum(1 for p in self.pers if self.tag_val(t, cik, p) is not None), -i, t) for i, t in enumerate(FRAME_TAGS[k])]
            n, _i, t = max(score)
            self._best[key] = t if n else None
        return self._best[key]

    def val(self, k: str, cik: str, per: str) -> Optional[float]:
        t = self.best(k, cik)
        return self.tag_val(t, cik, per) if t else None


def parse_frame(js: Dict) -> Dict[str, float]:
    return {str(int(r["cik"])): float(r["val"]) for r in (js or {}).get("data") or [] if r.get("val") is not None}


async def refresh_frames(budget_s: float = 150) -> Dict[str, Dict]:
    cache = _load(F_FRAMES)
    today = us_today()
    qs = cy_quarters(today, int(cfg().get("frame_quarters", 10)))
    years = sorted({f"CY{int(q[2:6])}" for q in qs})[:-1] or [f"CY{today.year - 1}"]
    t0, ok = time.time(), 0
    inst = [q + "I" for q in qs[:7]]                 # goodwill at quarter ends: a jump flags acquisition-driven growth
    plan = [(k, tag, qs + years) for k, tags in FRAME_TAGS.items() for tag in tags] + [("i", t, inst) for t in INSTANT_TAGS]
    for k, tag, pers in plan:
        unit = "USD-per-shares" if k == "eps" else "USD"
        if True:
            for i, per in enumerate(pers):
                key = f"{tag}/{per}"
                rec = cache.get(key) or {}
                fresh = 20 * 3600 if (i < 3 or per in years[-1:]) else 7 * 86400
                if time.time() - float(rec.get("ts", 0)) < fresh:
                    continue
                if time.time() - t0 > budget_s:
                    break
                try:
                    js = await http.get(f"https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/{unit}/{per}.json", headers=SEC_HDR, timeout=40, retries=0)
                    cache[key] = {"ts": time.time(), "v": parse_frame(js)}
                    ok += 1
                except Exception as e:  # noqa: BLE001
                    msg = str(e)
                    if "404" in msg:                 # quarter not populated yet → remember for a while
                        cache[key] = {"ts": time.time(), "v": {}}
                    else:
                        log.info("frame %s: %s", key, e)
                await asyncio.sleep(0.2)
    keep = {f"{t}/{p}" for ts in FRAME_TAGS.values() for t in ts for p in qs + years} | {f"{t}/{p}" for t in INSTANT_TAGS for p in inst}
    cache = {k: v for k, v in cache.items() if k in keep}
    if ok:
        _save(F_FRAMES, cache)
    HEALTH.ok("sec_frames", ok, every=86400)
    return cache


# ============================================================ Taiwan monthly revenue
def parse_twrev(rows: List[Dict], board: str) -> Dict[str, Dict]:
    out = {}
    for r in rows or []:
        code = str(r.get("公司代號", "")).strip()
        ym = str(r.get("資料年月", "")).strip()
        if not code or len(ym) < 4:
            continue
        try:
            y, m = int(ym[:-2]) + 1911, int(ym[-2:])
        except ValueError:
            continue
        g = lambda k: num(r.get(k))  # noqa: E731
        out[code] = {"code": code, "name": str(r.get("公司名稱", "")).strip(), "ind": str(r.get("產業別", "")).strip(), "board": board,
                     "ym": f"{y}-{m:02d}", "rev": g("營業收入-當月營收"), "mom": g("營業收入-上月比較增減(%)"),
                     "yoy": g("營業收入-去年同月增減(%)"), "cum_yoy": g("累計營業收入-前期比較增減(%)"), "ly": g("營業收入-去年當月營收")}
    return out


async def refresh_twrev() -> Dict:
    arc = _load(F_TW)
    if time.time() - float(arc.get("ts", 0)) < 6 * 3600:
        return arc
    got: Dict[str, Dict] = {}
    for url, board in (("https://openapi.twse.com.tw/v1/opendata/t187ap05_L", "上市"),
                       ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O", "上櫃")):
        try:
            got.update(parse_twrev(await http.get(url, timeout=40, retries=1), board))
        except Exception as e:  # noqa: BLE001
            log.info("TW monthly revenue %s: %s", board, e)
    if got:
        months = arc.get("months") or {}
        for code, r in got.items():
            months.setdefault(r["ym"], {})[code] = {k: r[k] for k in ("rev", "mom", "yoy", "cum_yoy")}
        months = {k: months[k] for k in sorted(months)[-24:]}
        arc = {"ts": time.time(), "latest": got, "months": months}
        _save(F_TW, arc)
        HEALTH.ok("tw_monthly_revenue", len(got), every=86400)
    else:
        HEALTH.fail("tw_monthly_revenue", RuntimeError("TWSE/TPEx open data unavailable"), every=86400)
    return arc


# ============================================================ Taiwan valuation (P/E, P/B, yield)
def parse_twpe(rows: List[Dict], board: str) -> Dict[str, Dict]:
    out = {}
    for r in rows or []:
        code = str(r.get("Code") or r.get("SecuritiesCompanyCode") or "").strip()
        if not code:
            continue
        pe = num(r.get("PEratio") if "PEratio" in r else r.get("PriceEarningRatio"))
        pb = num(r.get("PBratio") if "PBratio" in r else r.get("PriceBookRatio"))
        dy = num(r.get("DividendYield") if "DividendYield" in r else r.get("YieldRatio"))
        out[code] = {"pe": pe, "pb": pb, "dy": dy, "name": str(r.get("Name") or r.get("CompanyName") or "").strip(), "board": board}
    return out


async def refresh_twpe() -> Dict:
    cache = _load(F_TWPE)
    if time.time() - float(cache.get("ts", 0)) < 12 * 3600:
        return cache
    got: Dict[str, Dict] = {}
    for url, board in (("https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL", "上市"),
                       ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis", "上櫃")):
        try:
            got.update(parse_twpe(await http.get(url, timeout=40, retries=1), board))
        except Exception as e:  # noqa: BLE001
            log.info("TW P/E %s: %s", board, e)
    if got:
        cache = {"ts": time.time(), "v": got}
        _save(F_TWPE, cache)
        HEALTH.ok("tw_pe", len(got), every=86400)
    return cache


# ============================================================ Nasdaq annual statements (foreign filers: no US-GAAP quarters)
def parse_nq_annual(js: Dict) -> List[Dict]:
    t = (((js or {}).get("data") or {}).get("incomeStatementTable")) or {}
    hdr, rows = t.get("headers") or {}, t.get("rows") or []
    get = {str(r.get("value1", "")).strip(): r for r in rows}
    out = []
    for c in [k for k in hdr if k != "value1"]:
        try:
            end = datetime.strptime(str(hdr[c]), "%m/%d/%Y").date().isoformat()
        except ValueError:
            continue
        v = lambda name: num((get.get(name) or {}).get(c))  # noqa: E731
        k = lambda x: None if x is None else x * 1000  # noqa: E731
        rev = k(v("Total Revenue"))
        if rev:
            out.append({"end": end, "rev": rev, "gp": k(v("Gross Profit")), "op": k(v("Operating Income")), "ni": k(v("Net Income"))})
    return sorted(out, key=lambda r: r["end"])


async def refresh_nq_annual(syms: List[str], budget_s: float = 90) -> Dict[str, Dict]:
    cache = _load(F_ANN)
    t0, ok = time.time(), 0
    for s in syms:
        if time.time() - float((cache.get(s) or {}).get("ts", 0)) < 7 * 86400:
            continue
        if time.time() - t0 > budget_s:
            break
        try:
            js = await http.get(f"https://api.nasdaq.com/api/company/{s.replace('-', '.')}/financials", params={"frequency": 1},
                                headers=NQ_HDR, timeout=20, retries=1)
            cache[s] = {"ts": time.time(), "y": parse_nq_annual(js)}
            ok += 1
        except Exception as e:  # noqa: BLE001
            cache[s] = {"ts": time.time() - 6 * 86400, "y": (cache.get(s) or {}).get("y", [])}   # retry tomorrow
            log.info("nasdaq annual %s: %s", s, e)
        await asyncio.sleep(0.3)
    if ok:
        _save(F_ANN, cache)
    return cache


# ============================================================ holder
class EarningsData:
    def __init__(self) -> None:
        self.days: Dict[str, Dict] = _load(F_DAYS)
        self.surprise: Dict[str, Dict] = _load(F_SURP)
        self.facts: Dict[str, Dict] = _load(F_FACTS)
        self.frames: Dict[str, Dict] = _load(F_FRAMES)
        self.tw: Dict = _load(F_TW)
        self.twpe: Dict = _load(F_TWPE)
        self.nqann: Dict = _load(F_ANN)
        self.ts = 0.0

    def reported(self) -> Dict[str, str]:
        """Latest report date per symbol seen in the (past part of the) calendar."""
        today = us_today().isoformat()
        out: Dict[str, str] = {}
        for d, rec in self.days.items():
            if d > today:
                continue
            for r in rec.get("rows", []):
                if d > out.get(r["sym"], ""):
                    out[r["sym"]] = d
        return out

    async def refresh(self, tech_syms: List[str], force: bool = False, frames: bool = True) -> None:
        if not cfg().get("enabled", True):
            return
        if not force and time.time() - self.ts < float(cfg().get("refresh_s", 1800)):
            return
        b = float(cfg().get("budget_s", 240))
        try:
            self.days = await refresh_calendar(b * 0.3)
        except Exception as e:  # noqa: BLE001
            log.warning("earnings calendar refresh failed: %s", e)
        rep = self.reported()
        res = await asyncio.gather(refresh_surprises(tech_syms, rep, b * 0.25), refresh_facts(tech_syms, rep, b * 0.5),
                                   refresh_frames(b * 0.5) if frames else asyncio.sleep(0, result=self.frames), refresh_twrev(),
                                   refresh_twpe(), return_exceptions=True)
        for nm, r in zip(("surprise", "facts", "frames", "tw", "twpe"), res):
            if isinstance(r, Exception):
                log.warning("earnings %s refresh failed: %s", nm, r)
            else:
                setattr(self, nm, r)
        self.ts = time.time()

    async def poll_day(self, d: date) -> List[Dict]:
        rows = await _cal_day(d)
        self.days[d.isoformat()] = {"ts": time.time(), "rows": rows, "final": False}
        _save(F_DAYS, self.days)
        return rows
