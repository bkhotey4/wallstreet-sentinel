"""台股專區：外資台指期淨未平倉的歷史走勢與燈號（FinMind 開放資料，2018 年起每日，免金鑰）。

淨未平倉＝外資多單未平倉口數 − 空單未平倉口數。只看口數會失真（指數越高、市場越大，口數自然變大；外資也常用期貨避險現貨），
所以燈號用「和自己 2018 年以來的歷史比」的百分位；使用者熟悉的 3.5 萬、4 萬口兩條線照樣畫出來當參考。
回測：淨未平倉落在不同分位時，加權指數之後 21 個交易日內跌 ≥5% 的頻率（同一段期間的基準一起列）。
快取 data_cache/econ_tw_foi.json（CI 保留 econ_*），12 小時最多抓一次。"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_foi.json"
TTL = 12 * 3600
URL = "https://api.finmindtrade.com/api/v4/data"
LINES = (-35000, -40000)                                   # the user's reference lines (contracts)
BANDS = ((0, 5, "極端空單（歷史最低 5%）"), (5, 20, "空單偏多"), (20, 80, "常態"), (80, 101, "多單偏多"))


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def parse(rows: List[Dict]) -> Dict[str, int]:
    out = {}
    for r in rows:
        if "外資" not in str(r.get("institutional_investors", "")):
            continue
        try:
            out[r["date"][:10]] = int(r["long_open_interest_balance_volume"]) - int(r["short_open_interest_balance_volume"])
        except (KeyError, TypeError, ValueError):
            continue
    return dict(sorted(out.items()))


async def refresh(force: bool = False) -> Dict:
    d = load()
    now = time.time()
    d["ts_check"] = now
    if force or now - float(d.get("ts", 0)) > TTL or not d.get("net"):
        try:
            js = await http.get(URL, params={"dataset": "TaiwanFuturesInstitutionalInvestors", "data_id": "TX", "start_date": "2018-01-01",
                                             "end_date": time.strftime("%Y-%m-%d")}, timeout=60, retries=1)
            net = parse(js.get("data") or [])
            if len(net) < 500:
                raise ValueError(f"only {len(net)} days")
            d["net"], d["ts"] = net, now
            HEALTH.ok("tw_foi", len(net), every=TTL)
        except Exception as e:  # noqa: BLE001
            log.warning("TW foreign OI history failed: %s", e if str(e) else type(e).__name__)
            HEALTH.fail("tw_foi", e, every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def view(eng) -> Optional[Dict]:
    net = load().get("net") or {}
    if len(net) < 250:
        return None
    s = pd.Series(net, dtype=float)
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    now = float(s.iloc[-1])
    pct = float((s.iloc[:-1] < now).mean() * 100)
    band = next(z for lo, hi, z in BANDS if lo <= pct < hi)
    out = {"date": s.index[-1].strftime("%Y-%m-%d"), "net": now, "chg1": float(s.iloc[-1] - s.iloc[-2]), "chg20": float(s.iloc[-1] - s.iloc[-21]),
           "pct": pct, "band": band, "min": float(s.min()), "min_d": s.idxmin().strftime("%Y-%m-%d"), "since": s.index[0].strftime("%Y"),
           "lines": [{"v": v, "crossed": now <= v} for v in LINES], "hist": [[i.strftime("%Y-%m-%d"), float(v)] for i, v in s.tail(260).items()]}
    try:
        tw = eng.market.series("^TWII").dropna()
    except Exception:  # noqa: BLE001
        tw = pd.Series(dtype=float)
    if len(tw) > 500:
        tw = tw[tw.index >= s.index[0]]
        low = tw[::-1].rolling(21, min_periods=1).min()[::-1].shift(-1) / tw - 1
        y = (low <= -0.05).astype(float).where(low.notna())
        y[tw.index > tw.index[-1] - pd.Timedelta(days=35)] = np.nan
        pc = s.expanding(250).apply(lambda x: (x[:-1] < x[-1]).mean() * 100, raw=True).reindex(tw.index).ffill()
        rows = []
        for lo, hi, z in BANDS:
            m = (pc >= lo) & (pc < hi)
            rows.append({"band": z, "n": int(y[m].notna().sum()), "p": float(y[m].mean() * 100) if y[m].notna().any() else None, "now": lo <= pct < hi})
        out.update(rows=rows, base=float(y.mean() * 100))
    out["emoji"] = "🔴" if pct < 5 else "🟡" if pct < 20 else "🟢"
    return out
