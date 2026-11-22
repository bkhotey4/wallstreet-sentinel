"""台灣製造業／非製造業 PMI 與失業率（2026-11-22，台股覆蓋清單最後兩項「缺」）。

來源都是政府資料開放平臺上的官方檔案（Claude 11-22 逐一下載驗證；Gemini 給的國發會網址被機器人驗證擋、主計總處 API 範例參數錯誤）：
  * PMI／NMI：data.gov.tw 資料集 6100（國家發展委員會；中華經濟研究院編製），CSV 欄位 Date, PMI, NMI，每月第一個工作日更新。
  * 失業率：data.gov.tw 資料集 6637（主計總處人力資源調查），XML，每月更新（含性別、年齡、教育別）。
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
    if not force and time.time() - float(d.get("ts") or 0) < TTL and d.get("pmi"):
        return _with_seed(d)
    d["ts"] = time.time()
    for name, fn in (("pmi", lambda: parse_pmi(_get(U_PMI))), ("unemp", lambda: parse_unemp(_get(U_UNEMP)))):
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
    for name in ("pmi", "unemp"):
        mine, theirs = d.get(name) or [], s.get(name) or []
        if theirs and (not mine or theirs[-1]["ym"] > mine[-1]["ym"]):
            d[name] = theirs
    return d


def write_seed(path=SEED) -> Dict:
    d = refresh(force=True)
    out = {"fetched": d.get("fetched"), "pmi": (d.get("pmi") or [])[-60:], "unemp": (d.get("unemp") or [])[-60:]}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
