"""Whole-market stock lists and a rolling daily price archive for the 全市場 scan (website only).

Coverage (settings.fullmarket):
    US  every Nasdaq / NYSE / NYSE American common stock with market cap ≥ min_mcap_usd   (Nasdaq screener API)
    TW  every TWSE-listed (.TW) and TPEx-listed (.TWO) common stock                         (TWSE / TPEx open data)
    HK  every Main Board equity; the scan later keeps names with enough daily turnover     (HKEX list of securities)

Prices come from Yahoo in batches. Each run works through a queue within a time budget — first the names that have
no history yet (≈15 months back-fill), then the names whose last bar is older than the market's latest session —
so the first fill is spread over several runs and later runs only add the newest bars."""
from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
import time
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
_LISTS = DATA_DIR / "fullmarket_lists.json"
UA_HDR = {"Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"}
TW_IND = {"01": "水泥", "02": "食品", "03": "塑膠", "04": "紡織纖維", "05": "電機機械", "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙",
          "10": "鋼鐵", "11": "橡膠", "12": "汽車", "14": "建材營造", "15": "航運", "16": "觀光餐旅", "17": "金融保險", "18": "貿易百貨",
          "19": "綜合", "20": "其他", "21": "化學", "22": "生技醫療", "23": "油電燃氣", "24": "半導體", "25": "電腦及週邊", "26": "光電",
          "27": "通信網路", "28": "電子零組件", "29": "電子通路", "30": "資訊服務", "31": "其他電子", "32": "文化創意", "33": "農業科技",
          "34": "電子商務", "35": "綠能環保", "36": "數位雲端", "37": "運動休閒", "38": "居家生活", "80": "管理股票", "91": "存託憑證"}
US_SECTOR = {"Technology": "科技", "Finance": "金融", "Health Care": "醫療保健", "Consumer Discretionary": "非必需消費",
             "Consumer Staples": "必需消費", "Industrials": "工業", "Energy": "能源", "Utilities": "公用事業", "Real Estate": "不動產",
             "Basic Materials": "原物料", "Telecommunications": "電信", "Miscellaneous": "其他"}


def cfg() -> Dict:
    return SETTINGS.get("fullmarket", {}) or {}


def _clean_us_name(n: str) -> str:
    n = re.sub(r"\s+(Class [A-Z]\s+)?(Common Stock|Ordinary Shares?|Common Shares|American Depositary Shares?|"
               r"Depositary Shares?|Sponsored ADR|ADS)\b.*$", "", n or "", flags=re.I)
    return n.strip(" ,") or n


# ------------------------------------------------------------------ lists
async def _us() -> List[Dict]:
    js = await http.get("https://api.nasdaq.com/api/screener/stocks", params={"tableonly": "true", "limit": 25000, "download": "true"},
                        headers=UA_HDR, timeout=60, retries=1)
    rows = ((js or {}).get("data") or {}).get("rows") or []
    lo = float(cfg().get("min_mcap_usd", 1e9))
    out = []
    for r in rows:
        sym = (r.get("symbol") or "").strip().upper()
        if not sym or any(c in sym for c in "^ ") or len(sym) > 6:
            continue
        try:
            mcap = float(r.get("marketCap") or 0)
        except ValueError:
            mcap = 0.0
        if mcap < lo:
            continue
        sec = (r.get("sector") or "").strip()
        out.append({"sym": sym.replace("/", "-").replace(".", "-"), "code": sym, "name": _clean_us_name(r.get("name", "")),
                    "ind": US_SECTOR.get(sec, sec or "其他"), "sub": (r.get("industry") or "").strip(), "mcap": mcap})
    return out


async def _tw() -> List[Dict]:
    out: Dict[str, Dict] = {}
    ind: Dict[str, str] = {}
    try:
        for r in await http.get("https://openapi.twse.com.tw/v1/opendata/t187ap03_L", timeout=60, retries=1) or []:
            ind[str(r.get("公司代號", "")).strip()] = TW_IND.get(str(r.get("產業別", "")).strip(), "其他")
    except Exception as e:  # noqa: BLE001
        log.info("TWSE industry list failed: %s", e)
    try:
        for r in await http.get("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O", timeout=60, retries=1) or []:
            ind[str(r.get("SecuritiesCompanyCode", "")).strip()] = TW_IND.get(str(r.get("SecuritiesIndustryCode", "")).strip(), "其他")
    except Exception as e:  # noqa: BLE001
        log.info("TPEx industry list failed: %s", e)
    for r in await http.get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", timeout=60, retries=1) or []:
        c = str(r.get("Code", "")).strip()
        if re.fullmatch(r"[1-9]\d{3}", c):
            out[c] = {"sym": c + ".TW", "code": c, "name": str(r.get("Name", "")).strip(), "ind": ind.get(c, "其他"), "board": "上市"}
    try:
        for r in await http.get("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes", timeout=60, retries=1) or []:
            c = str(r.get("SecuritiesCompanyCode", "")).strip()
            if re.fullmatch(r"[1-9]\d{3}", c) and c not in out:
                out[c] = {"sym": c + ".TWO", "code": c, "name": str(r.get("CompanyName", "")).strip(), "ind": ind.get(c, "其他"), "board": "上櫃"}
    except Exception as e:  # noqa: BLE001
        log.info("TPEx list failed: %s", e)
    return list(out.values())


def parse_hkex(xlsx: bytes, header_key: str) -> pd.DataFrame:
    raw = pd.read_excel(io.BytesIO(xlsx), header=None, dtype=str)
    hdr = next(i for i in range(min(10, len(raw))) if any(header_key in str(x) for x in raw.iloc[i].values))
    df = raw.iloc[hdr + 1:].copy()
    df.columns = [str(x).strip() for x in raw.iloc[hdr].values]
    return df


async def _hk() -> List[Dict]:
    base = "https://www.hkex.com.hk/{}/services/trading/securities/securitieslists/ListOfSecurities{}.xlsx"
    en = parse_hkex(await http.get(base.format("eng", ""), kind="bytes", timeout=60, retries=1), "Stock Code")
    zh_names: Dict[str, str] = {}
    try:
        zh = parse_hkex(await http.get(base.format("chi", "_c"), kind="bytes", timeout=60, retries=1), "股份代號")
        ccol = next(c for c in zh.columns if "股份代號" in c)
        ncol = next(c for c in zh.columns if "股份名稱" in c)
        zh_names = {str(r[ccol]).strip().zfill(5): str(r[ncol]).strip() for _, r in zh.iterrows()}
    except Exception as e:  # noqa: BLE001
        log.info("HKEX Chinese list failed: %s", e)
    code_c = next(c for c in en.columns if "Stock Code" in c)
    name_c = next(c for c in en.columns if "Name" in c)
    cat_c = next(c for c in en.columns if c.strip() == "Category")
    sub_c = next((c for c in en.columns if "Sub-Category" in c), None)
    out = []
    for _, r in en.iterrows():
        if str(r[cat_c]).strip() != "Equity" or (sub_c and "Main Board" not in str(r[sub_c])):
            continue
        try:
            n = int(str(r[code_c]).strip())
        except ValueError:
            continue
        if n > 9999:
            continue
        code = f"{n:04d}"
        out.append({"sym": code + ".HK", "code": code, "name": zh_names.get(f"{n:05d}") or str(r[name_c]).strip(), "ind": "港股",
                    "name_en": str(r[name_c]).strip()})
    return out


def _write_json(path, obj) -> None:
    """Atomic write (tmp + os.replace): a run cancelled mid-write can't leave a truncated cache file behind."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


async def lists(force: bool = False) -> Dict[str, List[Dict]]:
    """{us: [...], tw: [...], hk: [...]} — refreshed weekly (lists change slowly); the last good copy is kept on failure.
    The refresh has its own time budget (list_budget_s); when it fails outright the next attempt waits a day
    (list_retry_hours) instead of eating into every hourly build."""
    old: Dict = {}
    try:
        if _LISTS.exists():
            old = json.loads(_LISTS.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        old = {}
    if not force and old.get("ts") and time.time() - float(old["ts"]) < float(cfg().get("list_days", 7)) * 86400:
        return old["markets"]
    if not force and old.get("fail_ts") and time.time() - float(old["fail_ts"]) < float(cfg().get("list_retry_hours", 24)) * 3600:
        return dict(old.get("markets") or {})
    mk = dict(old.get("markets") or {})
    state = {"ok": 0}

    async def _fetch_all() -> None:
        for key, fn in (("us", _us), ("tw", _tw), ("hk", _hk)):
            if key not in (cfg().get("markets") or ["us", "tw", "hk"]):
                continue
            try:
                rows = await fn()
                if len(rows) > 50:
                    mk[key] = rows
                    state["ok"] += 1
            except Exception as e:  # noqa: BLE001
                log.warning("full-market list %s failed: %s", key, e)
                HEALTH.fail(f"fullmarket_list_{key}", e, every=7 * 86400)

    try:
        await asyncio.wait_for(_fetch_all(), float(cfg().get("list_budget_s", 180)))
    except asyncio.TimeoutError:
        log.warning("full-market list refresh exceeded its %ss budget", cfg().get("list_budget_s", 180))
    try:
        if state["ok"]:
            _write_json(_LISTS, {"ts": time.time(), "markets": mk})
        else:                                           # nothing refreshed: keep the old lists, retry after a day
            _write_json(_LISTS, {**old, "markets": dict(old.get("markets") or {}), "fail_ts": time.time()})
            log.warning("full-market lists not refreshed; next attempt in ~%sh", cfg().get("list_retry_hours", 24))
    except Exception as e:  # noqa: BLE001
        log.warning("full-market lists not saved: %s", e)
    return mk if state["ok"] else dict(old.get("markets") or {})


# ------------------------------------------------------------------ prices
def _file(mk: str):
    return DATA_DIR / f"fullmarket_{mk}.pkl"


def load_prices(mk: str):
    try:
        if _file(mk).exists():
            d = pd.read_pickle(_file(mk))
            return d["close"], d["volume"]
    except Exception as e:  # noqa: BLE001
        log.warning("full-market prices %s unreadable: %s", mk, e)
    return pd.DataFrame(), pd.DataFrame()


def save_prices(mk: str, close: pd.DataFrame, volume: pd.DataFrame) -> None:
    keep = int(cfg().get("keep_bars", 330))
    close, volume = close.sort_index().tail(keep), volume.sort_index().tail(keep)
    tmp = _file(mk).with_suffix(".tmp")
    pd.to_pickle({"close": close, "volume": volume}, tmp)
    os.replace(tmp, _file(mk))


def _merge(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if old.empty:
        return new
    if new.empty:
        return old
    out = old.reindex(old.index.union(new.index))
    for c in new.columns:
        s = new[c].dropna()
        if len(s):
            if c not in out.columns:
                out[c] = float("nan")
            out.loc[s.index, c] = s.values
    return out


def _splice(old: pd.DataFrame, new: pd.DataFrame, min_overlap: int = 3, tol: float = 0.005):
    """Merge a freshly downloaded (auto-adjusted) close window onto stored history. A split or dividend since the last
    download moves Yahoo's whole adjusted series, so the median new/old ratio over the overlapping bars rescales every
    stored bar before the new window (|ratio − 1| > tol). Fewer than `min_overlap` usable overlapping bars → the column
    is dropped so the next run back-fills it in full. Returns (merged close, dropped symbols)."""
    if old.empty or new.empty:
        return _merge(old, new), []
    old = old.copy()
    dropped = []
    for c in new.columns:
        s = new[c].dropna()
        if s.empty or c not in old.columns:
            continue
        o = old[c].dropna()
        if o.empty:
            continue
        o = o.iloc[:-1]                                  # the stored last bar may have been a partial (intraday) one
        ov = o.index.intersection(s.index)
        if len(ov) < min_overlap:
            dropped.append(c)
            continue
        k = float((s.reindex(ov) / o.reindex(ov)).median())
        if k > 0 and abs(k - 1) > tol and k == k:
            old.loc[old.index < s.index.min(), c] *= k
            log.info("full-market %s re-based by %.4f (split/dividend adjustment)", c, k)
    if dropped:
        old = old.drop(columns=dropped)
        new = new.drop(columns=[c for c in dropped if c in new.columns])
        log.info("full-market: %d names lost their overlap with the stored history → full re-download next run: %s",
                 len(dropped), ", ".join(dropped[:8]))
    return _merge(old, new), dropped


def _load_json(path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def refresh_prices(mk: str, syms: List[str], ref_date: Optional[pd.Timestamp], deadline: float) -> Dict:
    """Work the queue for one market until `deadline` (time.time()). Runs in a worker thread (yfinance is blocking).
    Part of the budget (update_reserve) is kept for updating names already on file, so a big first-time back-fill
    can't leave the existing board stale."""
    from .stocks import _download
    close, volume = load_prices(mk)
    ffile = DATA_DIR / f"fullmarket_failed_{mk}.json"
    nfile = DATA_DIR / f"fullmarket_nobar_{mk}.json"
    failed, nobar = _load_json(ffile), _load_json(nfile)
    now = time.time()
    retry = now - 7 * 86400                             # names Yahoo has no data for are retried weekly, not every run
    nobar_retry = now - float(cfg().get("nobar_retry_days", 2)) * 86400   # updated, but no new bar (halted / delisted)
    last = {c: close[c].last_valid_index() for c in close.columns} if not close.empty else {}
    missing = [s for s in syms if last.get(s) is None and float(failed.get(s, 0)) < retry]
    stale = [s for s in syms if last.get(s) is not None and ref_date is not None and last[s] < ref_date
             and float(nobar.get(s, 0)) < nobar_retry]
    chunk_new, chunk_upd = int(cfg().get("chunk_backfill", 60)), int(cfg().get("chunk_update", 100))
    reserve = max(0.0, deadline - now) * float(cfg().get("update_reserve", 0.4)) if stale else 0.0
    done_new = done_upd = 0
    empty_runs = 0
    for queue, period, chunk, dl in ((missing, str(cfg().get("backfill_period", "15mo")), chunk_new, deadline - reserve),
                                     (stale, "1mo", chunk_upd, deadline)):
        for i in range(0, len(queue), chunk):
            if time.time() > dl or empty_runs >= 2:
                break
            part = queue[i:i + chunk]
            try:
                cl, vo = _download(part, period)
            except Exception as e:  # noqa: BLE001
                log.warning("full-market %s download failed: %s", mk, e)
                time.sleep(3)
                continue
            # a whole batch (of more than a handful of names) coming back empty = throttled by Yahoo, not "no such stock"
            if len(part) >= 5 and (cl.empty or cl.dropna(how="all").empty):
                empty_runs += 1
                log.warning("full-market %s: empty batch of %d (rate-limited?) — not marked as failed", mk, len(part))
                time.sleep(5)
                continue
            empty_runs = 0
            if period == "1mo":
                cl, dropped = _splice(close, cl)
                if dropped:
                    volume = volume.drop(columns=[c for c in dropped if c in volume.columns])
                    vo = vo.drop(columns=[c for c in dropped if c in vo.columns])
                close, volume = cl, _merge(volume, vo)
                done_upd += len(part)
                for s in part:
                    if s in dropped:
                        continue
                    nl = close[s].last_valid_index() if s in close.columns else None
                    if nl is None or (last.get(s) is not None and nl <= last[s]):
                        nobar[s] = time.time()            # no new bar → back off instead of re-asking every run
                    else:
                        nobar.pop(s, None)
            else:
                close, volume = _merge(close, cl), _merge(volume, vo)
                done_new += len(part)
                for s in part:
                    if s not in cl.columns or cl[s].dropna().empty:
                        failed[s] = time.time()
            time.sleep(float(cfg().get("pause_s", 1.0)))
    if done_new or done_upd:
        save_prices(mk, close, volume)
        for path, obj in ((ffile, failed), (nfile, nobar)):
            try:
                _write_json(path, obj)
            except Exception:  # noqa: BLE001
                pass
    have = set(close.columns) if not close.empty else set()
    left = len([s for s in syms if s not in have and float(failed.get(s, 0)) < retry]) + max(0, len(stale) - done_upd)
    return {"backfilled": done_new, "updated": done_upd, "pending": left, "have": len(have), "failed": len(failed),
            "nobar": len(nobar)}
