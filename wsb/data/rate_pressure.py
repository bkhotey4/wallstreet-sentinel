"""利率回到 5% 附近，壓力傳到哪裡：把四個環節放在一起看，每個都和自己的歷史比。

  1. 10 年期公債殖利率（FRED DGS10，1962 年起）：水準、3 個月變化、一年內最高。
  2. 一般人：30 年房貸利率（FRED MORTGAGE30US，每週）與住宅建商股（XHB）3 個月表現。
  3. 公司借錢：高收益債與投資級公司債利差（ICE BofA，授權限制只顯示百分位與方向，FRED 只給近 3 年）。
  4. 靠借錢擴張的 AI 算力公司（CRWV、NBIS、APLD、IREN 平均）與私募信貸（BIZD）3 個月表現，和自己過去一年比。
每環節算一個「壓力百分位」（越高越緊），最高的就是目前最先撐不住的地方。Yahoo 價格快取 data_cache/econ_rate_pressure.json，
每天一次。描述現況，不是預測。"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_rate_pressure.json"
TTL = 24 * 3600
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=2y&interval=1d"
NEO = ("CRWV", "NBIS", "APLD", "IREN")
STEP = 63                                # 約 3 個月的交易日
FRED_IDS = ("DGS10", "MORTGAGE30US", "BAMLH0A0HYM2", "BAMLC0A0CM")


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def refresh(force: bool = False) -> Dict:
    from .fsr_watch import parse_chart
    from .freshness import bundle_ts, due
    d = load()
    now = time.time()
    d["ts_check"] = now
    each = d.setdefault("ts_each", {})
    if due(d, ["neo"], TTL, now, force):
        d["try_each"]["neo"] = now
        try:
            px = {s: parse_chart(await http.get(YAHOO.format(s=s), headers={"User-Agent": "Mozilla/5.0"}, timeout=30, retries=1)) for s in NEO}
            if sum(1 for v in px.values() if len(v) > 120) < 2:
                raise ValueError("Yahoo: too little history")
            d["neo"], each["neo"] = px, now
            HEALTH.ok("rate_pressure", len(px), every=TTL)
        except Exception as e:  # noqa: BLE001
            log.warning("rate pressure data: %s", e)
            HEALTH.fail("rate_pressure", str(e) or type(e).__name__, every=TTL)
        d["ts"] = bundle_ts(d, ["neo"])
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def _pct(hist: pd.Series, v: float) -> Optional[float]:
    hist = hist.dropna()
    return float((hist < v).mean() * 100) if len(hist) >= 30 else None


def _chg(s: pd.Series, days: int) -> Optional[float]:
    s = s.dropna()
    back = s[s.index <= s.index[-1] - pd.Timedelta(days=days)]
    return float(s.iloc[-1] - back.iloc[-1]) if len(back) else None


def payment(rate_pct: float, principal: float = 300_000, years: int = 30) -> float:
    r, n = rate_pct / 100 / 12, years * 12
    return principal * r / (1 - (1 + r) ** -n) if r else principal / n


def _rel(a: pd.Series, b: pd.Series) -> Optional[pd.Series]:
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    if len(j) <= STEP + 30:
        return None
    return ((j.iloc[:, 0] / j.iloc[:, 0].shift(STEP)) - (j.iloc[:, 1] / j.iloc[:, 1].shift(STEP))).dropna() * 100


def view(get, px) -> Dict:
    """get(fred_id) → Series; px(ticker) → Series (site price history)."""
    out: Dict = {"links": []}
    y = get("DGS10")
    if y is not None and len(y.dropna()) > 500:
        y = y.dropna()
        yr = y[y.index > y.index[-1] - pd.DateOffset(years=1)]
        out["links"].append({"key": "rate", "zh": "10 年期公債殖利率", "now": float(y.iloc[-1]), "date": y.index[-1].strftime("%Y-%m-%d"),
                             "chg3": (_chg(y, 91) or 0) * 100, "hi": float(yr.max()), "hi_date": yr.idxmax().strftime("%Y-%m-%d"),
                             "since": y.index[0].strftime("%Y"), "pct": _pct(y.iloc[:-1], float(y.iloc[-1]))})
    m = get("MORTGAGE30US")
    if m is not None and len(m.dropna()) > 100:
        m = m.dropna()
        c3 = _chg(m, 91)
        link = {"key": "home", "zh": "30 年房貸利率（美國）", "now": float(m.iloc[-1]), "date": m.index[-1].strftime("%Y-%m-%d"),
                "chg3": (c3 or 0) * 100, "since": m.index[0].strftime("%Y"), "pct": _pct(m.iloc[:-1], float(m.iloc[-1])),
                "pay": payment(float(m.iloc[-1])), "pay3": payment(float(m.iloc[-1]) - c3) if c3 is not None else None}
        xhb, spx = px("XHB"), px("^GSPC")
        if xhb is not None and spx is not None:
            r = _rel(xhb, spx)
            if r is not None:
                link["stock"], link["stock_zh"] = float(r.iloc[-1]), "住宅建商股（XHB）"
        out["links"].append(link)
    for sid, zh in (("BAMLH0A0HYM2", "高收益債（垃圾債）利差"), ("BAMLC0A0CM", "投資級公司債利差")):
        s = get(sid)
        if s is not None and len(s.dropna()) > 120:
            s = s.dropna()
            c3 = _chg(s, 91)
            out.setdefault("credit", []).append({"zh": zh, "pct": _pct(s.iloc[:-1], float(s.iloc[-1])), "since": s.index[0].strftime("%Y"),
                                                 "dir": "擴大" if (c3 or 0) > 0.05 else "收斂" if (c3 or 0) < -0.05 else "持平",
                                                 "date": s.index[-1].strftime("%Y-%m-%d")})
    if out.get("credit"):
        cr = out["credit"]
        out["links"].append({"key": "credit", "zh": "公司借錢的利差", "pct": max(c["pct"] or 0 for c in cr), "rows": cr})
    neo = load().get("neo") or {}
    ser = [pd.Series(v, dtype=float).rename(k) for k, v in neo.items() if len(v) > 120]
    ndx = px("^NDX")
    if ser and ndx is not None:
        for s in ser:
            s.index = pd.to_datetime(s.index)
        basket = pd.concat([s / s.dropna().iloc[0] for s in ser], axis=1).mean(axis=1).dropna()
        r = _rel(basket, ndx)
        if r is not None:
            rk = _pct(r.iloc[:-1], float(r.iloc[-1]))           # 0 = the worst 3 months in its own history (0 is a real value, not missing)
            link = {"key": "ai", "zh": "靠借錢擴張的 AI 算力公司", "rel": float(r.iloc[-1]), "pct": None if rk is None else 100 - rk,
                    "date": r.index[-1].strftime("%Y-%m-%d"), "names": [s.name for s in ser]}
            bizd = px("BIZD")
            if bizd is not None and px("^GSPC") is not None:
                rb = _rel(bizd, px("^GSPC"))
                if rb is not None:
                    link["bizd"] = float(rb.iloc[-1])
            out["links"].append(link)
    ranked = [l for l in out["links"] if l.get("pct") is not None and l["key"] != "rate"]
    out["worst"] = max(ranked, key=lambda l: l["pct"]) if ranked else None
    return out
