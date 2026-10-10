"""Per-stock public intel for the website's 個股情報 tab (curated universe only, no holdings):

* Yahoo quote summary   → analyst consensus / target prices, dividend yield, ex-date, years of dividend growth
* SEC EDGAR submissions → recent 8-K items (and other watched forms), graded by severity
* CBOE delayed quotes   → at-the-money straddle per expiry (implied move) for indices, ETFs and stocks near earnings

Every feed keeps its own JSON cache in DATA_DIR (sinfo_*.json) and only re-fetches what is stale, inside a time budget,
so an hourly website build spreads the work over several runs."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from ..config import DATA_DIR, SEC_USER_AGENT
from . import http

log = logging.getLogger(__name__)
F_YF = DATA_DIR / "sinfo_yf.json"
F_8K = DATA_DIR / "sinfo_8k.json"
F_OPT = DATA_DIR / "sinfo_opt.json"
F_CIK = DATA_DIR / "sinfo_cik.json"


def _load(p) -> Dict:
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", p.name, e)
    return {}


def _save(p, d) -> None:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")
        tmp.replace(p)
    except Exception as e:  # noqa: BLE001
        log.warning("%s not saved: %s", p.name, e)


def _f(x) -> Optional[float]:
    try:
        v = float(x)
        return v if v == v and abs(v) != float("inf") else None
    except (TypeError, ValueError):
        return None


# ============================================================ Yahoo: analysts + dividends
REC = {"strong_buy": "強力買進", "buy": "買進", "hold": "持有", "underperform": "表現落後", "sell": "賣出", "strongbuy": "強力買進"}


def parse_info(info: Dict, annual: Dict[str, float], last_div: Optional[str] = None) -> Dict:
    """info = Yahoo quote-summary dict; annual = {calendar year: dividends paid that year}."""
    px = _f(info.get("currentPrice")) or _f(info.get("regularMarketPrice")) or _f(info.get("previousClose"))
    rate = _f(info.get("dividendRate")) or _f(info.get("trailingAnnualDividendRate"))
    yld = rate / px * 100 if rate and px else None          # computed ourselves: Yahoo changed dividendYield's units in 2025
    ex = info.get("exDividendDate")
    if isinstance(ex, (int, float)) and ex > 0:
        ex = datetime.fromtimestamp(ex, tz=timezone.utc).date().isoformat()
    elif not isinstance(ex, str):
        ex = None
    yrs = sorted(int(y) for y in annual if str(y).isdigit())
    this_year = date.today().year
    full = [y for y in yrs if y < this_year]
    streak, paid = 0, 0
    for y in reversed(full):                                  # consecutive years paid / raised, newest complete year backwards
        if annual.get(str(y), 0) > 0:
            paid += 1
        else:
            break
    for i in range(len(full) - 1, 0, -1):
        a, b = annual.get(str(full[i]), 0), annual.get(str(full[i - 1]), 0)
        if a > 0 and b > 0 and a >= b * 0.995 and full[i] - full[i - 1] == 1:
            streak += 1
        else:
            break
    tm, th, tl = _f(info.get("targetMeanPrice")), _f(info.get("targetHighPrice")), _f(info.get("targetLowPrice"))
    n = _f(info.get("numberOfAnalystOpinions"))
    return {"px": px, "cur": info.get("currency"), "tm": tm, "th": th, "tl": tl, "n": int(n) if n else None,
            "rm": _f(info.get("recommendationMean")), "rk": str(info.get("recommendationKey") or "").lower() or None,
            "up": (tm / px - 1) * 100 if tm and px else None, "uph": (th / px - 1) * 100 if th and px else None,
            "div": rate, "yld": yld, "ex": ex, "payout": _f(info.get("payoutRatio")), "y5": _f(info.get("fiveYearAvgDividendYield")),
            "paid": paid, "grow": streak, "last_div": last_div, "fpe": _f(info.get("forwardPE")),
            "ann": {str(y): round(annual[str(y)], 4) for y in yrs[-6:]}}


def _yf_one(sym: str) -> Dict:
    import yfinance as yf
    t = yf.Ticker(sym)
    info = t.info or {}
    annual, last = {}, None
    try:
        dv = t.dividends
        if dv is not None and len(dv):
            idx = dv.index
            last = str(idx[-1].date())
            for ts, v in zip(idx, dv.values):
                annual[str(ts.year)] = annual.get(str(ts.year), 0.0) + float(v)
    except Exception:  # noqa: BLE001
        pass
    return parse_info(info, annual, last)


async def refresh_yf(syms: List[str], budget_s: float = 150, max_age_h: float = 20, conc: int = 4) -> Dict[str, Dict]:
    cache = _load(F_YF)
    now = time.time()
    todo = sorted((s for s in syms if now - float((cache.get(s) or {}).get("ts", 0)) > max_age_h * 3600),
                  key=lambda s: float((cache.get(s) or {}).get("ts", 0)))
    t0, sem, done = time.time(), asyncio.Semaphore(conc), 0

    async def one(s: str):
        nonlocal done
        async with sem:
            if time.time() - t0 > budget_s:
                return
            try:
                d = await asyncio.wait_for(asyncio.to_thread(_yf_one, s), 40)
                if d.get("px") is None and not d.get("tm") and not d.get("div"):
                    raise ValueError("empty quote summary")
                d["ts"] = time.time()
                cache[s] = d
                done += 1
            except Exception as e:  # noqa: BLE001
                log.debug("yahoo info %s: %s", s, e)
                old = cache.get(s) or {}
                old["ts"] = time.time() - max_age_h * 3600 + 3 * 3600     # retry in ~3h, keep old values
                cache[s] = old
    await asyncio.gather(*(one(s) for s in todo))
    _save(F_YF, cache)
    log.info("stock info (Yahoo): %d refreshed, %d stale left", done, max(0, len(todo) - done))
    return cache


# ============================================================ SEC 8-K items
ITEM = {  # item → (label, severity 3 high / 2 medium / 1 low)
    "1.01": ("簽訂重大合約", 1), "1.02": ("終止重大合約", 2), "1.03": ("破產或接管", 3), "1.05": ("重大資安事件", 3),
    "2.01": ("完成併購／處分資產", 2), "2.02": ("財報公布", 1), "2.03": ("新增重大債務", 2), "2.04": ("債務加速到期／違約觸發", 3),
    "2.05": ("重組／裁員費用", 2), "2.06": ("重大資產減損", 3), "3.01": ("下市或不符上市規定通知", 3), "3.02": ("私募增發股份", 2),
    "3.03": ("股東權利重大變更", 2), "4.01": ("更換會計師", 3), "4.02": ("先前財報不可再信賴", 3), "5.01": ("控制權變更", 3),
    "5.02": ("高管／董事異動", 2), "5.03": ("章程修訂", 1), "5.07": ("股東會表決結果", 1), "7.01": ("公平揭露（簡報等）", 1),
    "8.01": ("其他事件", 1), "9.01": ("財務報表與附件", 0)}
FORMS = {"NT 10-K": ("延遲申報年報", 3), "NT 10-Q": ("延遲申報季報", 3), "SC 13D": ("主動型投資人持股 5%+", 2),
         "SCHEDULE 13D": ("主動型投資人持股 5%+", 2), "S-3": ("儲架增資登記", 2), "424B5": ("增資發行", 2), "S-1": ("申請發行股票", 2)}


def parse_filings(js: Dict, sym: str, days: int = 90, today: Optional[date] = None) -> List[Dict]:
    r = (js.get("filings") or {}).get("recent") or {}
    n = len(r.get("form", []))
    col = lambda k: (r.get(k) or [""] * n)  # noqa: E731
    lo = ((today or date.today()) - timedelta(days=days)).isoformat()
    cik = str(js.get("cik") or "").lstrip("0")
    out = []
    for form, dt, acc, items in zip(col("form"), col("filingDate"), col("accessionNumber"), col("items")):
        if not dt or dt < lo:
            continue
        if form in ("8-K", "8-K/A"):
            its = [i.strip() for i in str(items or "").split(",") if i.strip()]
            graded = [(i, *ITEM.get(i, ("項目 " + i, 1))) for i in its if ITEM.get(i, ("", 1))[1] > 0]
            if not graded:
                continue
            sev = max(g[2] for g in graded)
            if form == "8-K/A":
                sev = min(sev, 2)
            out.append({"sym": sym, "date": dt, "form": form, "sev": sev, "items": [g[0] for g in graded],
                        "labels": [g[1] for g in graded], "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/"})
        elif form in FORMS:
            lab, sev = FORMS[form]
            out.append({"sym": sym, "date": dt, "form": form, "sev": sev, "items": [], "labels": [lab],
                        "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/"})
    return out


async def _cik_map() -> Dict[str, str]:
    m = _load(F_CIK)
    if m.get("_ts", 0) > time.time() - 7 * 86400 and len(m) > 100:
        return m
    js = await http.get("https://www.sec.gov/files/company_tickers.json", headers={"User-Agent": SEC_USER_AGENT})
    m = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in js.values()}
    m["_ts"] = time.time()
    _save(F_CIK, m)
    return m


async def refresh_8k(syms: List[str], budget_s: float = 60, every_h: float = 6) -> Dict[str, Dict]:
    cache = _load(F_8K)
    now = time.time()
    todo = sorted((s for s in syms if now - float((cache.get(s) or {}).get("ts", 0)) > every_h * 3600),
                  key=lambda s: float((cache.get(s) or {}).get("ts", 0)))
    if not todo:
        return cache
    try:
        cik = await _cik_map()
    except Exception as e:  # noqa: BLE001
        log.warning("SEC ticker map failed: %s", e)
        return cache
    t0, done = time.time(), 0
    for s in todo:
        if time.time() - t0 > budget_s:
            break
        c = cik.get(s.upper().replace(".", "-"))
        if not c:
            cache[s] = {"ts": time.time(), "rows": [], "na": True}
            continue
        try:
            js = await http.get(f"https://data.sec.gov/submissions/CIK{c}.json", headers={"User-Agent": SEC_USER_AGENT}, timeout=20, retries=1)
            cache[s] = {"ts": time.time(), "rows": parse_filings(js, s)}
            done += 1
        except Exception as e:  # noqa: BLE001
            log.debug("SEC submissions %s: %s", s, e)
        await asyncio.sleep(0.15)                            # SEC fair access: < 10 requests / second
    _save(F_8K, cache)
    log.info("SEC 8-K: %d refreshed", done)
    return cache


# ============================================================ CBOE: ATM straddles
_OSYM = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")


def parse_cboe(js: Dict, today: Optional[date] = None, max_days: int = 70) -> Dict:
    """→ {"spot", "rows": [{"exp", "days", "k", "c", "p", "st", "mv"}]} — one ATM straddle per expiry (mid prices).
    mv = straddle ÷ spot: the move size the options market prices on average (≈ 0.8 σ√t; one standard deviation ≈ 1.25 × mv)."""
    d = (js or {}).get("data") or {}
    spot = _f(d.get("current_price")) or _f(d.get("close"))
    if not spot:
        raise ValueError("no spot")
    today = today or date.today()
    by: Dict[str, Dict[float, Dict[str, float]]] = {}
    for o in d.get("options") or []:
        m = _OSYM.match(str(o.get("option", "")))
        if not m:
            continue
        exp = datetime.strptime(m.group(2), "%y%m%d").date()
        dd = (exp - today).days
        if dd < 0 or dd > max_days:
            continue
        bid, ask = _f(o.get("bid")), _f(o.get("ask"))
        if not bid or not ask or ask < bid or bid <= 0:
            continue
        k = int(m.group(4)) / 1000
        if abs(k / spot - 1) > 0.15:
            continue
        by.setdefault(exp.isoformat(), {}).setdefault(k, {})[m.group(3)] = (bid + ask) / 2
    rows = []
    for exp, ks in sorted(by.items()):
        both = [k for k, v in ks.items() if "C" in v and "P" in v]
        if not both:
            continue
        k = min(both, key=lambda x: abs(x - spot))
        if abs(k / spot - 1) > 0.05:
            continue
        st = ks[k]["C"] + ks[k]["P"]
        rows.append({"exp": exp, "days": (date.fromisoformat(exp) - today).days, "k": k, "c": round(ks[k]["C"], 3), "p": round(ks[k]["P"], 3),
                     "st": round(st, 3), "mv": round(st / spot * 100, 2)})   # straddle ÷ spot ≈ expected |move|
    return {"spot": spot, "rows": rows}


def straddle_after(rec: Dict, d: str, after_close: bool = False) -> Optional[Dict]:
    """The first expiry that still includes the event day's reaction."""
    lim = (date.fromisoformat(d) + timedelta(days=1 if after_close else 0)).isoformat()
    for r in (rec or {}).get("rows", []):
        if r["exp"] >= lim:
            return r
    return None


async def refresh_options(syms: List[str], budget_s: float = 60, every_h: float = 4) -> Dict[str, Dict]:
    cache = _load(F_OPT)
    now = time.time()
    t0, done = time.time(), 0
    for s in syms:
        if now - float((cache.get(s) or {}).get("ts", 0)) < every_h * 3600:
            continue
        if time.time() - t0 > budget_s:
            break
        root = "_" + s.lstrip("^") if s.startswith("^") else s.replace("-", ".")
        try:
            js = await http.get(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{root}.json",
                                headers={"Referer": "https://www.cboe.com/"}, timeout=25, retries=1)
            rec = parse_cboe(js)
            rec["ts"] = time.time()
            rec["asof"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            cache[s] = rec
            done += 1
        except Exception as e:  # noqa: BLE001
            log.debug("CBOE %s: %s", s, e)
    for s in [k for k, v in cache.items() if now - float(v.get("ts", 0)) > 10 * 86400]:
        cache.pop(s, None)                                   # names that dropped out of the earnings window
    _save(F_OPT, cache)
    log.info("CBOE straddles: %d refreshed", done)
    return cache


def load_all() -> Dict[str, Dict]:
    return {"yf": _load(F_YF), "k8": _load(F_8K), "opt": _load(F_OPT)}
