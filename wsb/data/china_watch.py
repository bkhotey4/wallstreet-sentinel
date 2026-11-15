"""中國經濟卡的資料（2026-11-16，使用者選的第 7 項）。中國國家統計局的資料庫擋自動讀取（403），不繞過；改用公開來源：

  * 出口、進口（月）：FRED 上的 OECD 數列 XTEXVA01CNM667S／XTIMVA01CNM667S（美元，季節調整，約晚 2～3 個月）
  * 經濟成長、物價、政府負債（年，含今年與明年預測）：IMF 世界經濟展望（DataMapper：NGDP_RPCH、PCPIPCH、GGXWDG_NGDP）
  * 市場（日）：人民幣在岸（CNY=X）與離岸（CNH=X）匯率、上證指數、恆生指數、銅價（Yahoo）。
    離岸比在岸弱＝海外資金在押人民幣貶值；銅是中國工廠與房市需求最常用的即時代理
快取 data_cache/econ_china.json（12 小時一次）。"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import date
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_china.json"
TTL = 12 * 3600
FRED_IDS = {"exp": "XTEXVA01CNM667S", "imp": "XTIMVA01CNM667S"}
IMF = "https://www.imf.org/external/datamapper/api/v1/{ind}/CHN"
IMF_IND = {"gdp": "NGDP_RPCH", "cpi": "PCPIPCH", "debt": "GGXWDG_NGDP"}
HDR = {"User-Agent": "WallStreet-Sentinel/1.0 (research site; https://wallstreet-sentinel.pages.dev)", "Accept": "application/json"}
PX = {"CNY=X": "人民幣（在岸）", "CNH=X": "人民幣（離岸）", "000001.SS": "上證指數", "^HSI": "恆生指數", "HG=F": "銅價"}


# ------------------------------------------------------------------ pure (tested)
def yoy(series: Dict[str, float]) -> Optional[Dict]:
    """Latest month and its change against the same month a year earlier."""
    ks = sorted(series)
    if not ks:
        return None
    last = ks[-1]
    prev = f"{int(last[:4]) - 1:04d}{last[4:]}"
    out = {"date": last, "v": series[last]}
    if prev in series and series[prev]:
        out["yoy"] = series[last] / series[prev] - 1
    three = ks[-3:]
    three0 = [f"{int(k[:4]) - 1:04d}{k[4:]}" for k in three]
    if len(three) == 3 and all(k in series for k in three0):
        out["yoy3"] = sum(series[k] for k in three) / sum(series[k] for k in three0) - 1
    return out


def chg(c: List[float], n: int) -> Optional[float]:
    return c[-1] / c[-n - 1] - 1 if len(c) > n and c[-n - 1] else None


def market_view(px: Dict[str, Dict]) -> Dict:
    out: Dict = {}
    for s, zh in PX.items():
        x = px.get(s)
        if not x:
            continue
        out[s] = {"zh": zh, "last": x["c"][-1], "asof": x["d"][-1], "m1": chg(x["c"], 21), "y1": chg(x["c"], 252),
                  "hi5": max(x["c"]) if len(x["c"]) > 260 else None}
    if "CNY=X" in px and "CNH=X" in px:              # Yahoo keeps only the latest offshore quote: compare the latest of each
        a, b = px["CNY=X"], px["CNH=X"]
        out["gap"] = {"now": b["c"][-1] / a["c"][-1] - 1, "asof": min(a["d"][-1], b["d"][-1])}
    return out


def imf_rows(js_by: Dict[str, Dict], this_year: int) -> Dict:
    """{key: {year: value}} for last year, this year and next year."""
    out = {}
    for k, ind in IMF_IND.items():
        v = (((js_by.get(k) or {}).get("values") or {}).get(ind) or {}).get("CHN") or {}
        out[k] = {str(y): float(v[str(y)]) for y in (this_year - 1, this_year, this_year + 1) if isinstance(v.get(str(y)), (int, float))}
    return out


# ------------------------------------------------------------------ fetch
def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def refresh(force: bool = False) -> Dict:
    from .fred import _one
    from .forced_flows import _yahoo
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts_try", 0)) < TTL:
        return d
    d["ts_try"] = now
    bad = []
    try:
        res = await asyncio.gather(*(_one(sid, "2023-01-01") for sid in FRED_IDS.values()))
        d["trade"] = {k: {i.date().isoformat(): float(x) for i, x in s.items()} for k, s in zip(FRED_IDS, res)}
    except Exception as e:  # noqa: BLE001
        bad.append(f"fred: {e if str(e) else type(e).__name__}")
    js = {}
    for k, ind in IMF_IND.items():
        try:
            js[k] = await http.get(IMF.format(ind=ind), headers=HDR, timeout=60, retries=1)
        except Exception as e:  # noqa: BLE001
            bad.append(f"imf {ind}: {e if str(e) else type(e).__name__}")
    if js:
        d["imf"] = dict(d.get("imf") or {}, **imf_rows(js, date.today().year))
    px = await _yahoo([x for x in PX if x != "CNH=X"])
    try:
        from .forced_flows import YAHOO, parse_yahoo
        cnh = parse_yahoo(await http.get(YAHOO.format(s="CNH=X"), timeout=30, retries=1))
        if cnh["c"]:
            px["CNH=X"] = cnh
    except Exception as e:  # noqa: BLE001
        bad.append(f"CNH: {e if str(e) else type(e).__name__}")
    if px:
        d["mkt"] = market_view(px)
    else:
        bad.append("prices")
    if d.get("trade") or px:
        d["ts"] = now
    if bad:
        log.warning("china watch: %s", "; ".join(bad))
        HEALTH.fail("china_watch", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("china_watch", len(px), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def view(d: Optional[Dict] = None) -> Dict:
    d = load() if d is None else d
    tr = d.get("trade") or {}
    return {"exp": yoy(tr.get("exp") or {}), "imp": yoy(tr.get("imp") or {}), "imf": d.get("imf") or {}, "mkt": d.get("mkt") or {},
            "ts": d.get("ts")}
