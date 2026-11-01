"""財報走向判斷的資料：美股／台股／港股的季報或年報（營收、毛利、淨利、營運現金流、資本支出）與每週股價。

  美股  市值 ≥ settings.fund_trend.us_min_mcap（預設 200 億美元，和財報後解讀同一條線）＋觀察名單
        SEC XBRL companyfacts，季資料（和個股估值體檢同一套解析）；外國公司用 IFRS 申報、沒有季資料，照實列為跳過
  台股  上市＋上櫃普通股，以「已發行股數 × 收盤價」排市值取前 tw_top 家（金融保險業營收定義不同，不評）
        FinMind 開放資料（免金鑰）：損益表是單季數字、現金流量表是年初累計，這裡把現金流拆回單季
  港股  主板，近 60 日平均成交額取前 hk_top 家（全市場掃描的價格檔；港股沒有免費的市值清單）
        多數港股半年才公布一次、免費資料只有年報，所以港股用「年度」版本判斷（Yahoo Finance 年報）

每次建置在時間預算內，最久沒更新的先抓；財報 7 天（港股 14 天）、股價 7 天更新一次。
快取 data_cache/earn_fundtrend.json（財報）與 earn_fundtrend_px.pkl（每週收盤），earn_* 已在網站工作流程的快取裡。"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR, SETTINGS
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_fundtrend.json"
PX_FILE = DATA_DIR / "earn_fundtrend_px.pkl"
PV = 1
UNI_TTL = 7 * 86400
FACTS_TTL = {"us": 7 * 86400, "tw": 7 * 86400, "hk": 14 * 86400}
PX_TTL = 7 * 86400
FINMIND = "https://api.finmindtrade.com/api/v4/data"
TW_FIN = "金融保險"
KEYS = ("rev", "gp", "ni", "ocf", "capex")


def cfg() -> Dict:
    return SETTINGS.get("fund_trend", {}) or {}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, FILE)


def load_px() -> Dict[str, pd.DataFrame]:
    try:
        return pd.read_pickle(PX_FILE) if PX_FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save_px(px: Dict[str, pd.DataFrame]) -> None:
    tmp = PX_FILE.with_suffix(".tmp")
    pd.to_pickle(px, tmp)
    os.replace(tmp, PX_FILE)


def _q(date: str) -> str:
    y, m = int(date[:4]), int(date[5:7])
    return f"{y}Q{(m - 1) // 3 + 1}"


def _f(x) -> Optional[float]:
    try:
        v = float(str(x).replace(",", ""))
        return v if v == v else None
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ universes
def us_universe(rows: List[Dict], min_mcap: float, extra: List[str]) -> List[Dict]:
    out = {r["sym"]: {"sym": r["sym"], "name": r.get("name") or r["sym"], "ind": r.get("ind") or "其他", "mcap": r.get("mcap") or 0,
                      "fin": (r.get("ind") == "金融")}
           for r in rows if (r.get("mcap") or 0) >= min_mcap}
    known = {r["sym"]: r for r in rows}
    for s in extra:
        if s not in out:
            r = known.get(s) or {}
            out[s] = {"sym": s, "name": r.get("name") or s, "ind": r.get("ind") or "其他", "mcap": r.get("mcap") or 0, "fin": r.get("ind") == "金融"}
    return sorted(out.values(), key=lambda r: -r["mcap"])


def tw_universe(rows: List[Dict], shares: Dict[str, float], price: Dict[str, float], top: int) -> List[Dict]:
    """Rank by shares × close; financials are kept out of the ranking (their revenue means something else)."""
    out = []
    for r in rows:
        c = r.get("code")
        sh, p = shares.get(c), price.get(c)
        if not sh or not p or r.get("ind") == TW_FIN:
            continue
        out.append({"sym": r["sym"], "code": c, "name": r.get("name") or c, "ind": r.get("ind") or "其他", "mcap": sh * p, "fin": False})
    return sorted(out, key=lambda r: -r["mcap"])[:top]


def hk_universe(rows: List[Dict], turnover: Dict[str, float], top: int) -> List[Dict]:
    out = [{"sym": r["sym"], "name": r.get("name") or r["sym"], "ind": "港股", "turnover": turnover[r["sym"]], "fin": False}
           for r in rows if turnover.get(r["sym"])]
    return sorted(out, key=lambda r: -r["turnover"])[:top]


async def _tw_size() -> tuple:
    shares, price = {}, {}
    for url, ck, sk in (("https://openapi.twse.com.tw/v1/opendata/t187ap03_L", "公司代號", "已發行普通股數或TDR原股發行股數"),
                        ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O", "SecuritiesCompanyCode", "IssueShares")):
        try:
            for r in await http.get(url, timeout=60, retries=1) or []:
                v = _f(r.get(sk))
                if v:
                    shares[str(r.get(ck, "")).strip()] = v
        except Exception as e:  # noqa: BLE001
            log.info("fund trend TW shares %s: %s", url, e)
    for url, ck, pk in (("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", "Code", "ClosingPrice"),
                        ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes", "SecuritiesCompanyCode", "Close")):
        try:
            for r in await http.get(url, timeout=90, retries=1) or []:
                v = _f(r.get(pk))
                if v:
                    price.setdefault(str(r.get(ck, "")).strip(), v)
        except Exception as e:  # noqa: BLE001
            log.info("fund trend TW prices %s: %s", url, e)
    return shares, price


def _hk_turnover() -> Dict[str, float]:
    from . import fullmarket as FM
    close, vol = FM.load_prices("hk")
    if close.empty or vol.empty:
        return {}
    t = (close * vol).tail(60).mean()
    return {s: float(v) for s, v in t.items() if v == v and v > 0}


def _hk_turnover_yahoo(syms: List[str], deadline: float) -> Dict[str, float]:
    """Fallback when the full-market price file is not on this machine: one month of daily bars in batches."""
    import yfinance as yf
    out: Dict[str, float] = {}
    for i in range(0, len(syms), 200):
        if time.time() > deadline:
            break
        try:
            h = yf.download(syms[i:i + 200], period="3mo", interval="1d", auto_adjust=False, progress=False, threads=True)
            t = (h["Close"] * h["Volume"]).tail(60).mean()
            out.update({s: float(v) for s, v in t.items() if v == v and v > 0})
        except Exception as e:  # noqa: BLE001
            log.info("fund trend HK turnover batch: %s", e)
    return out


async def refresh_universe(d: Dict, force: bool = False, deadline: Optional[float] = None) -> None:
    uni = d.setdefault("uni", {})
    if not force and time.time() - float(uni.get("ts", 0)) < UNI_TTL and all(uni.get(m) for m in ("us", "tw", "hk")):
        return
    from . import fullmarket as FM
    from ..analytics import stock_check as SCK
    try:
        mk = await FM.lists()
    except Exception as e:  # noqa: BLE001
        log.warning("fund trend: no market lists: %s", e)
        return
    c = cfg()
    if mk.get("us"):
        uni["us"] = us_universe(mk["us"], float(c.get("us_min_mcap", 2e10)), SCK.universe())
    if mk.get("tw"):
        sh, pr = await _tw_size()
        if sh and pr:
            uni["tw"] = tw_universe(mk["tw"], sh, pr, int(c.get("tw_top", 150)))
            uni["tw_fin"] = sum(1 for r in mk["tw"] if r.get("ind") == TW_FIN)
    if mk.get("hk"):
        to = await asyncio.to_thread(_hk_turnover)
        if not to:
            to = await asyncio.to_thread(_hk_turnover_yahoo, [r["sym"] for r in mk["hk"]], deadline or time.time() + 240)
        if to:
            uni["hk"] = hk_universe(mk["hk"], to, int(c.get("hk_top", 100)))
    uni["ts"] = time.time()


# ------------------------------------------------------------------ parsers
def parse_sec(cf: Dict) -> Optional[Dict]:
    from ..analytics.stock_check import FLOWS, q_merge
    p = {k: q_merge(cf, *FLOWS[k]) for k in ("rev", "gp", "cogs", "ni", "ocf", "capex")}
    if len(p["rev"]) < 8:
        return None
    if len(p["gp"]) < len(p["rev"]) // 2 and len(p["cogs"]) >= len(p["rev"]) // 2:      # gross profit not tagged: revenue − cost
        p["gp"] = {q: p["rev"][q] - v for q, v in p["cogs"].items() if q in p["rev"]}
    p.pop("cogs")
    return {k: {q: round(v) for q, v in p[k].items()} for k in KEYS}


def parse_finmind(inc: List[Dict], cfl: List[Dict]) -> Optional[Dict]:
    """Income statement rows are single quarters; cash-flow rows are year-to-date and are split back into quarters."""
    p: Dict[str, Dict[str, float]] = {k: {} for k in KEYS}
    ni_alt: Dict[str, float] = {}
    for r in inc:
        v, t = _f(r.get("value")), r.get("type")
        if v is None or not r.get("date"):
            continue
        q = _q(r["date"])
        if t == "Revenue":
            p["rev"][q] = v
        elif t == "GrossProfit":
            p["gp"][q] = v
        elif t == "IncomeAfterTaxes":
            p["ni"][q] = v
        elif t == "TotalConsolidatedProfitForThePeriod":
            ni_alt[q] = v
    for q, v in ni_alt.items():
        p["ni"].setdefault(q, v)
    ytd: Dict[str, Dict[str, float]] = {"ocf": {}, "ocf2": {}, "capex": {}}
    for r in cfl:
        v, t = _f(r.get("value")), r.get("type")
        if v is None or not r.get("date"):
            continue
        q = _q(r["date"])
        if t == "NetCashInflowFromOperatingActivities":
            ytd["ocf"][q] = v
        elif t == "CashFlowsFromOperatingActivities":
            ytd["ocf2"][q] = v
        elif t == "PropertyAndPlantAndEquipment":
            ytd["capex"][q] = -v                                        # filed as a cash outflow (negative)
    for q, v in ytd["ocf2"].items():
        ytd["ocf"].setdefault(q, v)
    for k in ("ocf", "capex"):
        s = ytd[k]
        for q, v in s.items():
            n = int(q[-1])
            if n == 1:
                p[k][q] = v
            else:
                prev = f"{q[:4]}Q{n - 1}"
                if prev in s:
                    p[k][q] = v - s[prev]
    if len(p["rev"]) < 8:
        return None
    return {k: {q: round(v) for q, v in sorted(s.items())} for k, s in p.items()}


def _row(df: pd.DataFrame, *names) -> Dict[str, float]:
    for n in names:
        if df is not None and not df.empty and n in df.index:
            s = df.loc[n]
            return {f"FY{c.year}": float(v) for c, v in s.items() if pd.notna(v)}
    return {}


def parse_yahoo_annual(inc: pd.DataFrame, cfl: pd.DataFrame) -> Optional[Dict]:
    p = {"rev": _row(inc, "Total Revenue", "Operating Revenue"), "gp": _row(inc, "Gross Profit"),
         "ni": _row(inc, "Net Income Common Stockholders", "Net Income"),
         "ocf": _row(cfl, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities"),
         "capex": {k: -v for k, v in _row(cfl, "Capital Expenditure", "Purchase Of PPE").items()}}
    if len(p["rev"]) < 3:
        return None
    return {k: {y: round(v) for y, v in sorted(s.items())} for k, s in p.items()}


def _hk_one(sym: str) -> Optional[Dict]:
    import yfinance as yf
    t = yf.Ticker(sym)
    return parse_yahoo_annual(t.income_stmt, t.cashflow)


# ------------------------------------------------------------------ refresh
async def _us_facts(d: Dict, syms: List[str], deadline: float, force: bool) -> None:
    from ..data.earnings_data import SEC_HDR
    from ..data.edgar_holdings import ticker_map
    from ..analytics.stock_check import OLD_CIK
    facts, fts, skip = d["facts"].setdefault("us", {}), d["fts"].setdefault("us", {}), d.setdefault("skip", {}).setdefault("us", {})
    try:
        tmap = await ticker_map()
    except Exception as e:  # noqa: BLE001
        log.warning("fund trend: no SEC ticker map: %s", e)
        return
    now = time.time()
    todo = [s for s in sorted(syms, key=lambda s: fts.get(s, 0)) if force or now - fts.get(s, 0) >= FACTS_TTL["us"]]
    sem = asyncio.Semaphore(4)

    async def one(sym: str) -> None:
        if time.time() > deadline:
            return
        cik = (tmap.get(sym) or tmap.get(sym.replace("/", "-").replace(".", "-")) or {}).get("cik") or OLD_CIK.get(sym)
        if not cik:
            fts[sym], skip[sym] = time.time(), "SEC 找不到代號"
            return
        async with sem:
            if time.time() > deadline:
                return
            try:
                cf = await http.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=60, retries=1)
                p = await asyncio.to_thread(parse_sec, cf or {})
                if p:
                    facts[sym] = p
                    skip.pop(sym, None)
                else:
                    facts.pop(sym, None)
                    skip[sym] = "沒有 us-gaap 季資料（多半是用國際會計準則申報的外國公司）"
                fts[sym] = time.time()
            except Exception as e:  # noqa: BLE001
                log.info("fund trend SEC %s: %s", sym, e)
            await asyncio.sleep(0.12)

    await asyncio.gather(*(one(s) for s in todo))


async def _tw_facts(d: Dict, uni: List[Dict], deadline: float, force: bool) -> None:
    facts, fts = d["facts"].setdefault("tw", {}), d["fts"].setdefault("tw", {})
    now, done, cap = time.time(), 0, int(cfg().get("tw_per_run", 60))     # FinMind's free quota is per hour: leave room for others
    for r in sorted(uni, key=lambda r: fts.get(r["sym"], 0)):
        sym = r["sym"]
        if time.time() > deadline or done >= cap:
            break
        if not force and now - fts.get(sym, 0) < FACTS_TTL["tw"]:
            continue
        done += 1
        try:
            got = []
            for ds in ("TaiwanStockFinancialStatements", "TaiwanStockCashFlowsStatement"):
                js = await http.get(FINMIND, params={"dataset": ds, "data_id": r["code"], "start_date": "2008-01-01"}, timeout=60, retries=1)
                if (js or {}).get("status") not in (200, None):
                    raise RuntimeError(f"FinMind {js.get('status')}: {js.get('msg')}")
                got.append((js or {}).get("data") or [])
                await asyncio.sleep(0.4)
            p = parse_finmind(*got)
            if p:
                facts[sym] = p
            fts[sym] = time.time()
        except Exception as e:  # noqa: BLE001
            log.info("fund trend FinMind %s: %s", sym, e)
            if "402" in str(e) or "429" in str(e) or "limit" in str(e).lower():
                break                                                   # hourly quota used up: the next build continues


async def _hk_facts(d: Dict, uni: List[Dict], deadline: float, force: bool) -> None:
    facts, fts = d["facts"].setdefault("hk", {}), d["fts"].setdefault("hk", {})
    now = time.time()
    for r in sorted(uni, key=lambda r: fts.get(r["sym"], 0)):
        sym = r["sym"]
        if time.time() > deadline:
            break
        if not force and now - fts.get(sym, 0) < FACTS_TTL["hk"]:
            continue
        try:
            p = await asyncio.to_thread(_hk_one, sym)
            if p:
                facts[sym] = p
            fts[sym] = time.time()
        except Exception as e:  # noqa: BLE001
            log.info("fund trend Yahoo %s: %s", sym, e)


def _weekly(syms: List[str]) -> pd.DataFrame:
    import yfinance as yf
    h = yf.download(syms, period="6y", interval="1wk", auto_adjust=False, progress=False, threads=True)
    c = h["Close"] if "Close" in h else pd.DataFrame()
    if isinstance(c, pd.Series):
        c = c.to_frame(syms[0])
    return c.dropna(how="all")


async def _prices(d: Dict, mk: str, syms: List[str], deadline: float, force: bool) -> None:
    """Weekly closes for the track record (US and Taiwan; Hong Kong has too few annual reports for one)."""
    px = load_px()
    have = px.get(mk, pd.DataFrame())
    pts = d.setdefault("pts", {}).setdefault(mk, {})
    now = time.time()
    todo = [s for s in syms if force or now - pts.get(s, 0) >= PX_TTL or s not in have]
    if not todo:
        return
    frames = []
    for i in range(0, len(todo), 100):
        if time.time() > deadline:
            break
        chunk = todo[i:i + 100]
        try:
            c = await asyncio.to_thread(_weekly, chunk)
            frames.append(c)
            for s in chunk:
                pts[s] = time.time()
        except Exception as e:  # noqa: BLE001
            log.info("fund trend weekly %s: %s", mk, e)
    if not frames:
        return
    new = pd.concat(frames, axis=1)
    keep = have.drop(columns=[c for c in new.columns if c in have.columns]) if not have.empty else pd.DataFrame()
    merged = pd.concat([keep, new], axis=1).sort_index() if not keep.empty else new.sort_index()
    merged = merged.loc[:, [c for c in merged.columns if c in set(syms)]]
    px[mk] = merged.astype("float32")
    _save_px(px)


async def refresh(force: bool = False, budget_s: float = 150) -> Dict:
    d = load()
    if d.get("pv") != PV:
        d = {"pv": PV}
    t0 = time.time()
    d.setdefault("facts", {})
    d.setdefault("fts", {})
    d["ts_check"] = t0
    await refresh_universe(d, deadline=t0 + budget_s * 0.4)
    uni = d.get("uni") or {}
    share = {"us": 0.45, "tw": 0.3, "hk": 0.25}
    left = max(10.0, budget_s - (time.time() - t0))
    t1 = time.time()
    end_us = t1 + left * share["us"]
    if uni.get("us"):
        await _us_facts(d, [r["sym"] for r in uni["us"]], end_us, force)
    end_tw = max(time.time(), end_us) + left * share["tw"]
    if uni.get("tw"):
        await _tw_facts(d, uni["tw"], end_tw, force)
    end_hk = max(time.time(), end_tw) + left * share["hk"]
    if uni.get("hk"):
        await _hk_facts(d, uni["hk"], end_hk, force)
    _save(d)
    px_end = time.time() + max(20.0, budget_s * 0.3)
    for mk in ("us", "tw"):
        if uni.get(mk):
            await _prices(d, mk, [r["sym"] for r in uni[mk]], px_end, force)
    d["ts"] = time.time()
    _save(d)
    return d
