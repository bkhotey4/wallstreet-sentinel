"""台灣加油站價格：中油每週公布的參考牌價（vipmbr.cpc.com.tw 的公開 Web Service，1999 年起）。

拿來和國際油價（布蘭特，換成新台幣）比：國際油價漲跌多少，台灣加油價跟著動多少。台灣有油價平穩機制
（漲幅超過一定程度由中油吸收、政府調整稅），所以兩者常常不一樣，差多少就是誰在幫忙吸收。
快取 data_cache/econ_tw_fuel.json（CI 保留 econ_*），12 小時一次。描述現況，不是預測。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Dict, Optional

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_fuel.json"
TTL = 12 * 3600
URL = "https://vipmbr.cpc.com.tw/CPCSTN/ListPriceWebService.asmx/getCPCMainProdListPrice_Historical?prodid={p}"
PAGE = "https://www.cpc.com.tw/historyprice.aspx?n=2890"
PRODS = (("95", 2, "95 無鉛汽油"), ("diesel", 4, "超級柴油"))
ROW = re.compile(r"<牌價生效時間>(\d{4}-\d{2}-\d{2})[^<]*</牌價生效時間>\s*<產品名>[^<]*</產品名>\s*<參考牌價>([\d.]+)</參考牌價>")


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def parse(xml: str) -> Dict[str, float]:
    out = {d: float(v) for d, v in ROW.findall(xml or "") if float(v) > 0}
    if len(out) < 100:
        raise ValueError(f"CPC: only {len(out)} prices")
    return out


async def refresh(force: bool = False) -> Dict:
    from .freshness import bundle_ts, due
    d = load()
    now = time.time()
    d["ts_check"] = now
    keys = [k for k, _, _ in PRODS]
    each = d.setdefault("ts_each", {})
    todo = due(d, keys, TTL, now, force)
    if todo:
        bad = []
        for k, p, _ in PRODS:
            if k not in todo:
                continue
            d["try_each"][k] = now
            try:
                d[k], each[k] = parse(await http.get(URL.format(p=p), kind="text", timeout=60, retries=1,
                                                     headers={"User-Agent": "Mozilla/5.0"})), now
            except Exception as e:  # noqa: BLE001
                bad.append(f"{k}: {e if str(e) else type(e).__name__}")
        d["ts"] = bundle_ts(d, keys)
        if bad:
            log.warning("TW fuel data: %s", "; ".join(bad))
            HEALTH.fail("tw_fuel", "; ".join(bad), every=TTL)
        else:
            HEALTH.ok("tw_fuel", len(d.get("95") or {}), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def _ser(m: Dict) -> pd.Series:
    s = pd.Series(m or {}, dtype=float)
    if s.empty:
        return s
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def _ago(s: pd.Series, when: pd.Timestamp) -> Optional[float]:
    x = s[s.index <= when]
    return float(x.iloc[-1]) if len(x) else None


def view(brent: Optional[pd.Series] = None, twd: Optional[pd.Series] = None) -> Optional[Dict]:
    """Latest pump prices, week and year changes, and the same-period change of Brent in NT$ (how much was passed through)."""
    d = load()
    rows = []
    for k, _, zh in PRODS:
        s = _ser(d.get(k))
        if len(s) < 60:
            continue
        last = s.index[-1]
        wk, yr = _ago(s, last - pd.Timedelta(days=6)), _ago(s, last - pd.DateOffset(years=1))
        rows.append({"key": k, "zh": zh, "price": float(s.iloc[-1]), "date": last.strftime("%Y-%m-%d"),
                     "wk": (float(s.iloc[-1]) - s.iloc[-2]) if len(s) > 1 else None, "prev_date": s.index[-2].strftime("%Y-%m-%d") if len(s) > 1 else None,
                     "yoy": (float(s.iloc[-1]) / yr - 1) * 100 if yr else None, "since": s.index[0].strftime("%Y"),
                     "max": float(s.max()), "max_date": s.idxmax().strftime("%Y-%m"),
                     "hist": [[i.strftime("%Y-%m-%d"), v] for i, v in s.tail(104).items()]})
    if not rows:
        return None
    out = {"rows": rows, "date": rows[0]["date"]}
    if brent is not None and twd is not None:
        j = pd.concat([brent.dropna(), twd.dropna()], axis=1, join="inner").dropna()
        if len(j) > 260:
            ntd = j.iloc[:, 0] * j.iloc[:, 1]
            last = pd.Timestamp(out["date"])
            now_v, yr_v = _ago(ntd, last), _ago(ntd, last - pd.DateOffset(years=1))
            if now_v and yr_v:
                out.update(brent_ntd=now_v, brent_yoy=(now_v / yr_v - 1) * 100)
    return out
