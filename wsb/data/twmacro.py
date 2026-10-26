"""Taiwan macro, bonds and credit for the 台灣 pages.  All free, keyless, official sources:

* 中央銀行統計 API (cpx.cbc.gov.tw): policy rate, call rate, 10-year government bond yield, M1B / M2, FX reserves, CPI,
  bank NPL ratio, life insurers' balance sheet, corporate / government bonds outstanding, mortgage and construction loans.
  Monthly, most series from 1987.
* 國發會 景氣指標及燈號 (ZIP of CSVs, located through data.gov.tw dataset 6099): monitoring-indicator score and light,
  leading / coincident indices, export-order index, customs exports, industrial production, unemployment, chip-tool imports.
* 櫃買中心 (TPEx): today's government curve (2/5/10/20/30y) and dealer reference yields for twAAA–twBBB corporate bonds
  (bondCurve.json, archived every build), plus month-end files back to 2005/2006 (.xls, filled in a few months per build).
* 臺北市住宅價格月指數 (data.taipei).
Cached in data_cache/econ_twmacro.json (kept between site builds)."""
from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import os
import re
import time
import zipfile
from datetime import date
from typing import Dict, List, Optional

from ..config import DATA_DIR
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_twmacro.json"
TTL = 12 * 3600
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
CBC = "https://cpx.cbc.gov.tw/API/DataAPI/Get?FileName={}"
NDC_META = "https://data.gov.tw/api/v2/rest/dataset/6099"
NDC_ZIP = ("https://ws.ndc.gov.tw/Download.ashx?u=LzAwMS9hZG1pbmlzdHJhdG9yLzEwL3JlbGZpbGUvNTc4MS82MzkyL2VhMjM1YmQ5LWQwNTItNGE2OS1h"
           "YmZjLWQ1Yzc4NWQzZDBlMi56aXA%3d&n=5pmv5rCj5oyH5qiZ5Y%2bK54eI6JmfLnppcA%3d%3d&icon=.zip")
TPEX_NOW = "https://www.tpex.org.tw/data/bond/bondCurve.json"
TPEX_LIST = "https://www.tpex.org.tw/www/zh-tw/bond/govDaily2"
TPEX = "https://www.tpex.org.tw"
TAIPEI = ("https://data.taipei/api/dataset/ce4ea2c6-6334-44f8-945a-5705492b187d/resource/"
          "02c7bb70-2113-4daf-81d3-5c14b9ae26df/download")
HIST_FROM = (2006, 1)          # first month with both a government curve and corporate reference yields
HIST_BUDGET_S = 45             # seconds per build spent back-filling month-end TPEx files

# series key → (CBC file, column path as "Table1|Table2|…")
CBC_SERIES = {
    "tw10y": ("EG43M01", "十年期政府公債次級市場利率"),
    "corp5y_issue": ("EG43M01", "公司債-5年期"),
    "disc": ("EG2AM01", "重貼現率"),
    "call": ("EG41M01", "金融業拆款"),
    "m1b": ("EF01M01", "貨幣總計數-M1B|日平均|年增率"),
    "m2": ("EF01M01", "貨幣總計數-M2|日平均|年增率"),
    "taiex": ("EF07M01", "股票市場股價指數(民國５５年=１００)(１９６６=１００）"),
    "fxres": ("EF07M01", "外匯存底(百萬美元)"),
    "npl": ("EF07M01", "本國銀行逾放比率"),
    "cpi": ("EF07M01", "消費者物價指數年增率"),
    "life_foreign": ("EF67M01", "國外資產|原始值"),
    "life_assets": ("EF67M01", "資產合計=負債權益合計|原始值"),
    "life_equity": ("EF67M01", "權益|原始值"),
    "corp_out": ("EGB4M01", "公司債|餘額|原始值"),
    "corp_issue": ("EGB4M01", "公司債|發行額|原始值"),
    "fin_out": ("EGB4M01", "金融債券|餘額|原始值"),
    "gov_out": ("EGA4M01", "合計|餘額|原始值"),
    "mortgage": ("EF99M01", "消費者貸款-購置住宅貸款|原始值"),
    "mortgage_yoy": ("EF99M01", "消費者貸款-購置住宅貸款|年增率"),
    "construct_yoy": ("EF99M01", "建築貸款|年增率"),
}
# NDC CSV column (prefix match) → series key
NDC_COLS = {
    "景氣對策信號綜合分數": "light_score", "景氣對策信號": "light", "領先指標不含趨勢指數": "lead", "同時指標不含趨勢指數": "coin",
    "外銷訂單動向指數": "orders_idx", "海關出口值": "exports", "工業生產指數": "ip", "失業率": "unemp", "名目半導體設備進口": "chip_tools",
}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)


def _num(x) -> Optional[float]:
    try:
        v = float(str(x).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return v


# ------------------------------------------------------------------ parsers (pure, tested)
def cbc_columns(j: Dict) -> List[str]:
    """Column names of a CBC table: the product of Table1 × Table2 × … joined with "|"."""
    st = (j.get("data") or {}).get("structure") or {}
    tabs = [[x.get("data", "").strip() for x in st[k]] for k in sorted(st, key=lambda k: int(re.sub(r"\D", "", k) or 0))]
    cols = [""]
    for t in tabs:
        cols = [f"{c}|{x}" if c else x for c in cols for x in t]
    return cols


def _period(p: str) -> Optional[str]:
    p = str(p).strip()
    m = re.fullmatch(r"(\d{4})M(\d{2})", p)
    if m:
        return f"{m[1]}-{m[2]}"
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", p)
    if m:
        return f"{m[1]}-{m[2]}-{m[3]}"
    return None


def parse_cbc(j: Dict, col: str) -> List[List]:
    """[[YYYY-MM, value]] for one column ("-" and blanks dropped)."""
    cols = cbc_columns(j)
    if col not in cols:
        cand = [c for c in cols if c.startswith(col)]
        if not cand:
            return []
        col = cand[0]
    i = cols.index(col) + 1
    out = []
    for r in (j.get("data") or {}).get("dataSets") or []:
        if len(r) <= i:
            continue
        p, v = _period(r[0]), _num(r[i])
        if p and v is not None:
            out.append([p, v])
    return out


def parse_ndc(raw: bytes) -> Dict[str, List[List]]:
    """{key: [[YYYY-MM, value]]} from the NDC ZIP (景氣對策信號 kept as its colour text)."""
    out: Dict[str, Dict[str, object]] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in z.namelist():
            if not n.lower().endswith(".csv"):
                continue
            b = z.read(n)
            txt = None
            for enc in ("utf-8-sig", "cp950", "big5"):
                try:
                    txt = b.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            if txt is None:
                continue
            rows = list(csv.reader(io.StringIO(txt)))
            if not rows:
                continue
            head = [h.strip() for h in rows[0]]
            idx = {}
            for j, h in enumerate(head):
                for pre, key in NDC_COLS.items():
                    if h.startswith(pre) and not (pre == "景氣對策信號" and "分數" in h):
                        idx.setdefault(key, j)
            for r in rows[1:]:
                if not r or not re.fullmatch(r"\d{6}", r[0].strip()):
                    continue
                p = f"{r[0][:4]}-{r[0][4:6]}"
                for key, j in idx.items():
                    if j >= len(r):
                        continue
                    v = r[j].strip()
                    if key == "light":
                        if v and v != "-":
                            out.setdefault(key, {})[p] = v
                    else:
                        x = _num(v)
                        if x is not None:
                            out.setdefault(key, {})[p] = x
    return {k: [[p, v[p]] for p in sorted(v)] for k, v in out.items()}


def parse_tpex_now(j: Dict) -> Optional[Dict]:
    """{"date", "gov": {"2": %, …}, "corp": {"twAAA": {"12": %, "60": %, …}, …}} from bondCurve.json."""
    try:
        dd = j["bondCoCurve"]["dataDate"].replace("/", "-")
        gov = {str(int(x["time"])): float(x["index"]) for x in j["bondCruve"]["data"] if x.get("index") is not None}
        corp: Dict[str, Dict[str, float]] = {}
        for x in j["bondCoCurve"]["data"]:
            for g in ("twAAA", "twAA", "twA", "twBBB"):
                if x.get(g) is not None:
                    corp.setdefault(g, {})[str(int(x["time"]))] = round(float(x[g]) * 100, 4)
    except Exception:  # noqa: BLE001
        return None
    return {"date": dd, "gov": gov, "corp": corp} if gov and corp else None


def parse_tpex_xls(gov_raw: Optional[bytes], co_raw: Optional[bytes]) -> Dict:
    """Month-end government benchmark yields and corporate reference yields from the TPEx .xls files."""
    import xlrd
    out: Dict = {}
    if gov_raw:
        s = xlrd.open_workbook(file_contents=gov_raw, encoding_override="cp950").sheet_by_index(0)
        gov = {}
        for r in range(s.nrows):
            m = re.match(r"(\d+)年", str(s.cell_value(r, 1)))
            v = _num(s.cell_value(r, 2)) if s.ncols > 2 else None
            if m and v is not None:
                gov[m[1]] = v
        if gov:
            out["gov"] = gov
    if co_raw:
        s = xlrd.open_workbook(file_contents=co_raw, encoding_override="cp950").sheet_by_index(0)
        head, corp = None, {}
        for r in range(s.nrows):
            row = [str(s.cell_value(r, c)) for c in range(s.ncols)]
            if head is None and any("年" in c for c in row[1:]) and any("月" in c for c in row[1:]):
                head = []
                for c in row[1:]:
                    m = re.match(r"(\d+)\s*(個月|年)", c)
                    head.append(None if not m else str(int(m[1]) * (1 if m[2] == "個月" else 12)))
                continue
            g = row[0].strip()
            if head and g in ("twAAA", "twAA", "twA", "twBBB"):
                corp[g] = {t: round(float(v) * 100, 4) for t, v in zip(head, (_num(x) for x in row[1:])) if t and v is not None}
        if corp:
            out["corp"] = corp
    return out


def parse_taipei(text: str) -> List[List]:
    """[[YYYY-MM, index]] for 全市 (whole city) from the Taipei housing price index CSV (ROC year/month)."""
    out = []
    for r in csv.reader(io.StringIO(text.lstrip("﻿"))):
        if len(r) < 3 or r[0].strip() != "全市":
            continue
        m = re.fullmatch(r"(\d{2,3})/(\d{1,2})", r[1].strip())
        v = _num(r[2])
        if m and v is not None:
            out.append([f"{int(m[1]) + 1911}-{int(m[2]):02d}", v])
    return out


# ------------------------------------------------------------------ fetch
async def _post(url: str, data: Dict, timeout: float = 30) -> Dict:
    s = await http.session()
    import aiohttp
    async with s.post(url, data=data, headers=UA, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
        r.raise_for_status()
        return await r.json(content_type=None)


async def _month_files(y: int, m: int) -> Dict[str, str]:
    """Last trading day's file path of a month for Curve and COCurve."""
    out = {}
    for code in ("Curve", "COCurve"):
        j = await _post(TPEX_LIST, {"date": f"{y}/{m:02d}/01", "fileCode": code, "response": "json"})
        paths = [row[1] for t in j.get("tables") or [] for row in t.get("data") or [] if len(row) > 1 and str(row[1]).endswith(".xls")]
        if paths:
            out[code] = max(paths)
    return out


async def _backfill(d: Dict) -> None:
    hist = d.setdefault("hist", {})
    tried = d.setdefault("hist_tried", {})
    t0, today = time.time(), date.today()
    y, m = HIST_FROM
    while (y, m) < (today.year, today.month) and time.time() - t0 < HIST_BUDGET_S:
        k = f"{y}-{m:02d}"
        if k not in hist and tried.get(k, 0) < 3:
            try:
                fs = await _month_files(y, m)
                g = await http.get(TPEX + fs["Curve"], kind="bytes", headers=UA, timeout=30, retries=1) if "Curve" in fs else None
                c = await http.get(TPEX + fs["COCurve"], kind="bytes", headers=UA, timeout=30, retries=1) if "COCurve" in fs else None
                row = parse_tpex_xls(g, c)
                if row.get("gov") or row.get("corp"):
                    row["file"] = re.sub(r".*?(\d{8}).*", r"\1", fs.get("COCurve") or fs.get("Curve") or "")
                    hist[k] = row
                else:
                    tried[k] = tried.get(k, 0) + 1
            except Exception as e:  # noqa: BLE001
                tried[k] = tried.get(k, 0) + 1
                log.info("TPEx month %s failed: %s", k, e)
            await asyncio.sleep(0.3)
        m += 1
        if m > 12:
            y, m = y + 1, 1


async def refresh(force: bool = False) -> Dict:
    d = load()
    fresh = not force and time.time() - float(d.get("ts", 0)) < TTL and d.get("cbc") and d.get("ndc")
    try:                                                       # today's curve: cheap, every build (archive grows daily)
        now = parse_tpex_now(await http.get(TPEX_NOW, headers=UA, timeout=30, retries=1))
        if now:
            d.setdefault("daily", {})[now["date"]] = {"gov": now["gov"], "corp": now["corp"]}
            d["daily"] = {k: d["daily"][k] for k in sorted(d["daily"])[-800:]}
    except Exception as e:  # noqa: BLE001
        log.info("TPEx bondCurve failed: %s", e)
    try:
        await _backfill(d)
    except Exception as e:  # noqa: BLE001
        log.info("TPEx backfill failed: %s", e)
    if fresh:
        _save(d)
        return d
    cbc = d.get("cbc") or {}
    files: Dict[str, Dict] = {}
    for f in sorted({v[0] for v in CBC_SERIES.values()}):
        try:
            files[f] = await http.get(CBC.format(f), headers=UA, timeout=60, retries=1)
        except Exception as e:  # noqa: BLE001
            log.info("CBC %s failed: %s", f, e)
    upd = d.get("cbc_updated") or {}
    for key, (f, col) in CBC_SERIES.items():
        if f in files:
            rows = parse_cbc(files[f], col)
            if rows:
                cbc[key] = rows
                upd[key] = ((files[f].get("meta") or {}).get("last_updated") or "")[:10]
    d["cbc"], d["cbc_updated"] = cbc, upd
    try:
        url = NDC_ZIP
        try:
            meta = await http.get(NDC_META, headers=UA, timeout=30, retries=1)
            url = next((x["resourceDownloadUrl"] for x in meta["result"]["distribution"] if x.get("resourceFormat") == "ZIP"), url)
        except Exception:  # noqa: BLE001
            pass
        ndc = parse_ndc(await http.get(url, kind="bytes", headers=UA, timeout=60, retries=1))
        if ndc.get("light_score"):
            d["ndc"] = ndc
    except Exception as e:  # noqa: BLE001
        log.info("NDC indicators failed: %s", e)
    try:
        tp = parse_taipei(await http.get(TAIPEI, kind="text", headers=UA, timeout=60, retries=1))
        if len(tp) > 24:
            d["taipei"] = tp
    except Exception as e:  # noqa: BLE001
        log.info("Taipei housing index failed: %s", e)
    d["ts"] = time.time()
    _save(d)
    return d
