"""重大事件倒數與歷史震幅：下一次 FOMC、CPI、非農就業（NFP）、四巫日的時間（美東→倒數），以及 1995 年以來
這些日子標普 500 收盤對收盤的平均震幅，和平常的日子比。

日期：FOMC＝聯準會歷史會議（data/fomc_history.json）＋即時日曆；CPI／NFP＝FRED 的官方發布日（release_id 10／50，
含已排定的未來日期）；四巫日＝3、6、9、12 月第三個星期五（遇假日提前）。快取 data_cache/econ_releases.json（7 天）。
震幅是歷史統計，描述波動有多大，不判斷方向，也不是投資建議。"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from ..config import DATA_DIR, FRED_API_KEY

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_releases.json"
TTL = 7 * 86400
ET = ZoneInfo("America/New_York")
RELEASES = {"cpi": 10, "nfp": 50}
EVENTS = (("fomc", "FOMC 利率決議", "FOMC decision", (14, 0)), ("cpi", "CPI 消費者物價", "CPI", (8, 30)),
          ("nfp", "非農就業（NFP）", "Jobs report", (8, 30)), ("opex", "四巫日（季度選擇權／期貨到期）", "Quad witching", (16, 0)))


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def refresh(force: bool = False) -> Dict:
    d = load()
    now = time.time()
    d["ts_check"] = now
    if FRED_API_KEY and (force or now - float(d.get("ts", 0)) > TTL or not d.get("cpi")):
        from ..data import http
        try:
            for k, rid in RELEASES.items():
                js = await http.get("https://api.stlouisfed.org/fred/release/dates", params={
                    "release_id": rid, "api_key": FRED_API_KEY, "file_type": "json", "realtime_start": "1995-01-01",
                    "realtime_end": f"{date.today().year + 1}-12-31", "include_release_dates_with_no_data": "true",
                    "limit": 10000, "sort_order": "asc"}, timeout=30, retries=1)
                ds = sorted({r["date"] for r in js.get("release_dates", [])})
                if len(ds) < 100:
                    raise ValueError(f"{k}: only {len(ds)} dates")
                d[k] = ds
            d["ts"] = now
        except Exception as e:  # noqa: BLE001
            log.warning("release dates failed: %s", e if str(e) else type(e).__name__)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def quad_witching(y0: int, y1: int) -> List[str]:
    from ..data.liquidity import third_friday
    return [third_friday(y, m).isoformat() for y in range(y0, y1 + 1) for m in (3, 6, 9, 12)]


def dates_for(eng, key: str, d: Dict) -> List[str]:
    if key == "fomc":
        from .fomc_drift import history_dates
        live = [x["date"] for x in (getattr(getattr(eng, "econ", None), "fomc", None) or [])]
        return sorted(set(history_dates()) | set(live))
    if key == "opex":
        return quad_witching(1995, date.today().year + 1)
    return list(d.get(key) or [])


def move_stats(spx: pd.Series, days: List[str], since: str) -> Optional[Dict]:
    """|close-to-close %| on the event days vs every day, from `since`."""
    r = (spx.pct_change() * 100).dropna()
    r = r[r.index >= pd.Timestamp(since)]
    if len(r) < 200:
        return None
    idx = pd.DatetimeIndex(pd.to_datetime([x for x in days if x >= since]))
    ev = r.reindex(idx).dropna().abs()
    if len(ev) < 8:
        return None
    a = r.abs()
    return {"n": int(len(ev)), "mean": float(ev.mean()), "med": float(ev.median()), "big": float((ev >= 1).mean() * 100),
            "base_mean": float(a.mean()), "base_big": float((a >= 1).mean() * 100), "max": float(ev.max())}


def build(eng, now: Optional[datetime] = None) -> Dict:
    d = load()
    now = now or datetime.now(ET)
    today = now.astimezone(ET).date().isoformat()
    try:
        spx = eng.market.series("^GSPC").dropna()
    except Exception:  # noqa: BLE001
        spx = pd.Series(dtype=float)
    out = []
    for key, zh, en, (hh, mm) in EVENTS:
        ds = dates_for(eng, key, d)
        nxt = None
        for x in ds:
            t = datetime.fromisoformat(x).replace(hour=hh, minute=mm, tzinfo=ET)
            if t > now:
                nxt = t
                break
        rec = {"key": key, "zh": zh, "en": en, "next": nxt.isoformat() if nxt else None, "ts": int(nxt.timestamp()) if nxt else None,
               "days": (nxt.date() - now.astimezone(ET).date()).days if nxt else None}
        if len(spx) > 500:
            rec["all"] = move_stats(spx, [x for x in ds if x < today], "1995-01-01")
            rec["recent"] = move_stats(spx, [x for x in ds if x < today], str(now.year - 3) + "-01-01")
        out.append(rec)
    out.sort(key=lambda r: r["ts"] or 10 ** 12)
    return {"available": any(r["ts"] for r in out), "events": out, "ts_check": d.get("ts_check"), "ts": d.get("ts")}
