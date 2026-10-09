"""Whole-market stock lists and a rolling daily price archive for the 全市場 scan (website only).

Coverage (settings.fullmarket):
    US  every Nasdaq / NYSE / NYSE American common stock with market cap ≥ min_mcap_usd   (Nasdaq screener API)
    TW  every TWSE-listed (.TW) and TPEx-listed (.TWO) common stock                         (TWSE / TPEx open data)
    HK  every Main Board equity; the scan later keeps names with enough daily turnover     (HKEX list of securities)

Prices come from Yahoo in batches. Each run works through a queue within a time budget — first the names that have
no history yet (≈15 months back-fill), then the names whose last bar is older than the market's latest session —
so the first fill is spread over several runs and later runs only add the newest bars."""
from __future__ import annotations

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


async def lists(force: bool = False) -> Dict[str, List[Dict]]:
    """{us: [...], tw: [...], hk: [...]} — refreshed weekly (lists change slowly); the last good copy is kept on failure."""
    old: Dict = {}
    try:
        if _LISTS.exists():
            old = json.loads(_LISTS.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        old = {}
    if not force and old.get("ts") and time.time() - float(old["ts"]) < float(cfg().get("list_days", 7)) * 86400:
        return old["markets"]
    mk = dict(old.get("markets") or {})
    ok = 0
    for key, fn in (("us", _us), ("tw", _tw), ("hk", _hk)):
        if key not in (cfg().get("markets") or ["us", "tw", "hk"]):
            continue
        try:
            rows = await fn()
            if len(rows) > 50:
                mk[key] = rows
                ok += 1
        except Exception as e:  # noqa: BLE001
            log.warning("full-market list %s failed: %s", key, e)
            HEALTH.fail(f"fullmarket_list_{key}", e, every=7 * 86400)
    if ok:
        try:
            _LISTS.write_text(json.dumps({"ts": time.time(), "markets": mk}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            log.warning("full-market lists not saved: %s", e)
    return mk


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


def refresh_prices(mk: str, syms: List[str], ref_date: Optional[pd.Timestamp], deadline: float) -> Dict:
    """Work the queue for one market until `deadline` (time.time()). Runs in a worker thread (yfinance is blocking)."""
    from .stocks import _download
    close, volume = load_prices(mk)
    ffile = DATA_DIR / f"fullmarket_failed_{mk}.json"
    try:
        failed = json.loads(ffile.read_text(encoding="utf-8")) if ffile.exists() else {}
    except Exception:  # noqa: BLE001
        failed = {}
    retry = time.time() - 7 * 86400                     # names Yahoo has no data for are retried weekly, not every run
    last = {c: close[c].last_valid_index() for c in close.columns} if not close.empty else {}
    missing = [s for s in syms if last.get(s) is None and float(failed.get(s, 0)) < retry]
    stale = [s for s in syms if last.get(s) is not None and ref_date is not None and last[s] < ref_date]
    chunk_new, chunk_upd = int(cfg().get("chunk_backfill", 60)), int(cfg().get("chunk_update", 100))
    done_new = done_upd = 0
    for queue, period, chunk in ((missing, str(cfg().get("backfill_period", "15mo")), chunk_new), (stale, "1mo", chunk_upd)):
        for i in range(0, len(queue), chunk):
            if time.time() > deadline:
                break
            part = queue[i:i + chunk]
            try:
                cl, vo = _download(part, period)
            except Exception as e:  # noqa: BLE001
                log.warning("full-market %s download failed: %s", mk, e)
                time.sleep(3)
                continue
            close, volume = _merge(close, cl), _merge(volume, vo)
            if period == "1mo":
                done_upd += len(part)
            else:
                done_new += len(part)
                for s in part:
                    if s not in cl.columns or cl[s].dropna().empty:
                        failed[s] = time.time()
            time.sleep(float(cfg().get("pause_s", 1.0)))
    if done_new or done_upd:
        save_prices(mk, close, volume)
        try:
            ffile.write_text(json.dumps(failed), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    have = set(close.columns) if not close.empty else set()
    left = len([s for s in syms if s not in have and float(failed.get(s, 0)) < retry]) + max(0, len(stale) - done_upd)
    return {"backfilled": done_new, "updated": done_upd, "pending": left, "have": len(have), "failed": len(failed)}
