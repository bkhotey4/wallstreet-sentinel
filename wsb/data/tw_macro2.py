"""台灣製造業／非製造業 PMI 與失業率（2026-11-22，台股覆蓋清單最後兩項「缺」）。

來源都是政府資料開放平臺上的官方檔案（Claude 11-22 逐一下載驗證；Gemini 給的國發會網址被機器人驗證擋、主計總處 API 範例參數錯誤）：
  * PMI／NMI：data.gov.tw 資料集 6100（國家發展委員會；中華經濟研究院編製），CSV 欄位 Date, PMI, NMI，每月第一個工作日更新。
  * 失業率：data.gov.tw 資料集 6637（主計總處人力資源調查），XML，每月更新（含性別、年齡、教育別）。
  * 薪資：中華民國統計資訊網「工業及服務業每人每月經常性薪資」頁（主計總處受僱員工薪資調查），頁面內嵌 1980 年起每月
    受僱員工人數、經常性薪資、總薪資、工時（hidChartData JSON；11-22 Claude 自己找到並下載驗證，data.gov.tw 找不到對應資料集）。
PMI 50 以上＝擴張、以下＝收縮；失業率看方向比看水準重要。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_macro2.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_macro2_seed.json"
U_PMI = ("https://ws.ndc.gov.tw/Download.ashx?u=LzAwMS9hZG1pbmlzdHJhdG9yLzEwL3JlbGZpbGUvNTc4MS82MzkxL2JmOGE0ZWI3LTEwZmUtNGZhMC1iNjQ2LTMwZTg5MGQwMjE4YS5jc3Y%3d"
         "&n=6Ie654Gj5o6h6LO857aT55CG5Lq65oyH5pW4KHBtaeWPim5taSkuY3N2&icon=.csv")
U_UNEMP = "https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/230038/mp0101a07.xml"
SRC_PMI = "https://data.gov.tw/dataset/6100"
SRC_UNEMP = "https://data.gov.tw/dataset/6637"
U_WAGE = "https://www.stat.gov.tw/Point.aspx?sid=t.4&n=3583&sms=11480"
SRC_WAGE = U_WAGE
WAGE_KEYS = (("受僱員工人數", "emp"), ("經常性薪資", "reg"), ("總薪資", "total"), ("工時", "hours"))
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
TTL = 12 * 3600
TPE = timezone(timedelta(hours=8))


def parse_pmi(text: str) -> List[Dict]:
    out = []
    for line in (text or "").lstrip("﻿").splitlines()[1:]:
        c = [x.strip() for x in line.split(",")]
        if len(c) >= 3 and re.fullmatch(r"\d{6}", c[0]):
            f = lambda s: float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None  # noqa: E731
            out.append({"ym": f"{c[0][:4]}-{c[0][4:]}", "pmi": f(c[1]), "nmi": f(c[2])})
    return out


def parse_unemp(xml: str) -> List[Dict]:
    """Monthly rows only (the file also has annual rows like '1978'): 年月別 '2026M09' → total, male, female, age 15–24."""
    out = []
    for blk in re.findall(r"<失業率>(.*?)</失業率>", xml or "", re.S):
        g = lambda tag: (re.search(rf"<{tag}>([^<]*)<", blk) or [None, None])[1]  # noqa: E731
        ym = g("年月別_Year_and_month") or ""
        m = re.fullmatch(r"(\d{4})M(\d{2})", ym.strip())
        if not m:
            continue
        num = lambda s: float(s) if s and re.fullmatch(r"-?\d+(\.\d+)?", s.strip()) else None  # noqa: E731
        out.append({"ym": f"{m.group(1)}-{m.group(2)}", "total": num(g("總計_Total_百分比")), "male": num(g("男_Male_百分比")),
                     "female": num(g("女_Female_百分比")), "y15_19": num(g("age_15-19_百分比")), "y20_24": num(g("age_20-24_百分比"))})
    return out


def parse_wage(page: str) -> List[Dict]:
    """stat.gov.tw embeds every month since 1980 as JSON in the hidden input hidChartData; series are told apart by title."""
    import html as _html
    m = re.search(r'id="ContentPlaceHolder1_hidChartData" value="([^"]*)"', page or "")
    if not m:
        return []
    try:
        series = json.loads(_html.unescape(m.group(1)))
    except ValueError:
        return []
    rows: Dict[str, Dict] = {}
    for sr in series if isinstance(series, list) else []:
        key = next((k for t, k in WAGE_KEYS if t in str(sr.get("Title") or "")), None)
        for x in (sr.get("data") or []) if key else []:
            dm = re.fullmatch(r"(\d{4})/(\d{1,2})/\d{1,2}", str(x.get("Date") or ""))
            v = str(x.get("Value") or "").replace(",", "")
            if dm and re.fullmatch(r"-?\d+(\.\d+)?", v):
                ym = f"{dm.group(1)}-{int(dm.group(2)):02d}"
                rows.setdefault(ym, {"ym": ym})[key] = float(v)
    return [rows[k] for k in sorted(rows)]


# 11-26: 主計總處統計資訊網 carries October CPI / export orders / exports weeks before the 國發會 database the 台灣數據日曆 used
# (it showed 2026-09 for everything while the agencies had published October). Exact series titles (one page holds several).
U_STAT = "https://www.stat.gov.tw/Point.aspx?sid={sid}&n={n}&sms=11480"
STAT_PAGES = (("t.2", 3581), ("t.5", 3584), ("t.8", 3587))
STAT_KEYS = {"消費者物價指數年增率": "cpi_yoy", "核心CPI年增率": "core_yoy", "生產者物價指數年增率": "ppi_yoy",
             "工業生產指數年增率": "ip_yoy", "外銷訂單": "orders", "出口金額": "exports", "出口年增率": "exports_yoy",
             "進口年增率": "imports_yoy"}
SRC_STAT = "https://www.stat.gov.tw/Point.aspx?sid=t.2&n=3581&sms=11480"


def parse_stat(page: str, rows: Optional[Dict[str, Dict]] = None) -> Dict[str, Dict]:
    """hidChartData series whose title is exactly one of STAT_KEYS → {ym: {ym, key: value}}; the first value seen for a
    month wins (the export page repeats months; the CPI page has a second, shorter 年增率 series)."""
    import html as _html
    rows = {} if rows is None else rows
    m = re.search(r'id="ContentPlaceHolder1_hidChartData" value="([^"]*)"', page or "")
    if not m:
        return rows
    try:
        series = json.loads(_html.unescape(m.group(1)))
    except ValueError:
        return rows
    for sr in series if isinstance(series, list) else []:
        key = STAT_KEYS.get(str(sr.get("Title") or "").strip())
        for x in (sr.get("data") or []) if key else []:
            dm = re.fullmatch(r"(\d{4})/(\d{1,2})/\d{1,2}", str(x.get("Date") or ""))
            v = str(x.get("Value") or "").replace(",", "")
            if dm and re.fullmatch(r"-?\d+(\.\d+)?", v):
                ym = f"{dm.group(1)}-{int(dm.group(2)):02d}"
                rows.setdefault(ym, {"ym": ym}).setdefault(key, float(v))
    return rows


def fetch_stat() -> List[Dict]:
    rows: Dict[str, Dict] = {}
    for sid, n in STAT_PAGES:
        parse_stat(_get(U_STAT.format(sid=sid, n=n)), rows)
    return [rows[k] for k in sorted(rows)]


def latest_stat(d: Dict, key: str):
    """(ym, value) of the newest month that has `key`, or None."""
    for r in reversed(d.get("stat") or []):
        if r.get(key) is not None:
            return r["ym"], r[key]
    return None


def _get(url: str, kind: str = "text") -> str:
    import requests
    r = requests.get(url, headers=UA, timeout=40)
    r.raise_for_status()
    return r.content.decode("utf-8-sig", errors="replace")


def _load(f) -> Dict:
    try:
        return json.loads(Path(f).read_text(encoding="utf-8")) if Path(f).exists() else {}
    except (OSError, ValueError):
        return {}


def refresh(force: bool = False) -> Dict:
    d = _load(FILE)
    if not force and time.time() - float(d.get("ts") or 0) < TTL and d.get("pmi") and d.get("unemp") and d.get("wage") and d.get("stat"):   # all three, or a failed one waits 12 h (Gemini CODE-4, 11-22)
        return _with_seed(d)
    d["ts"] = time.time()
    for name, fn in (("pmi", lambda: parse_pmi(_get(U_PMI))), ("unemp", lambda: parse_unemp(_get(U_UNEMP))),
                     ("wage", lambda: parse_wage(_get(U_WAGE))), ("stat", fetch_stat)):
        try:
            v = fn()
            if v:
                d[name] = v
        except Exception as e:  # noqa: BLE001
            log.info("tw macro2 %s unavailable: %s", name, e)
    d["fetched"] = datetime.now(TPE).strftime("%Y-%m-%d %H:%M")
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError:
        pass
    return _with_seed(d)


def _with_seed(d: Dict) -> Dict:
    """PC relay for a cloud build that cannot reach the government file servers: newer series win."""
    s = _load(SEED)
    for name in ("pmi", "unemp", "wage", "stat"):
        mine, theirs = d.get(name) or [], s.get(name) or []
        if theirs and (not mine or theirs[-1]["ym"] > mine[-1]["ym"]):
            d[name] = theirs
    return d


def write_seed(path=SEED) -> Dict:
    d = refresh(force=True)
    out = {"fetched": d.get("fetched"), "pmi": (d.get("pmi") or [])[-60:], "unemp": (d.get("unemp") or [])[-60:],
           "wage": (d.get("wage") or [])[-60:], "stat": (d.get("stat") or [])[-60:]}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
