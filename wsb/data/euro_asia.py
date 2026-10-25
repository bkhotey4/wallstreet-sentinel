"""歐洲與亞洲：會不會從美國以外點火（歐債危機 2010–12、2015 人民幣貶值、2022 英國退休金危機都是從外面傳回來的）。

  * 歐元區系統性壓力指數 CISS（歐洲央行，1980 年起每日）：回測它落在不同水準時，標普之後 3 個月跌 ≥10% 的頻率。
  * 歐元區各國 10 年期公債對德國的利差（FRED，月資料）：義大利、法國、西班牙、希臘——歐債危機就是利差失控；和自己 1999 年以來的歷史比。
  * 歐洲銀行股（EUFN）與歐洲 50 指數的 1 個月漲跌與離高點。
  * 亞洲：上證、恆生、中國網路股（KWEB）、韓國綜合指數、日經，以及人民幣 20 天變化（回測對美股沒有預測力，只當背景）。
快取 data_cache/econ_euro_asia.json（CI 保留 econ_*），12 小時一次。"""
from __future__ import annotations

import io
import json
import logging
import os
import time
from typing import Dict, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_euro_asia.json"
TTL = 12 * 3600
CISS_URL = "https://data-api.ecb.europa.eu/service/data/CISS/D.U2.Z0Z.4F.EC.SS_CIN.IDX?format=csvdata"
COUNTRIES = (("IT", "義大利"), ("FR", "法國"), ("ES", "西班牙"), ("GR", "希臘"))
CISS_BANDS = ((0, 0.1, "低"), (0.1, 0.2, "升溫"), (0.2, 0.35, "高"), (0.35, 9, "危機級"))
EQ = (("EUFN", "歐洲銀行股"), ("^STOXX50E", "歐洲 50"), ("000001.SS", "上證指數"), ("^HSI", "恆生指數"), ("KWEB", "中國網路股"),
      ("^KS11", "韓國綜合"), ("^N225", "日經 225"))


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def _fred(sid: str) -> Dict[str, float]:
    from ..config import FRED_API_KEY
    if FRED_API_KEY:
        js = await http.get("https://api.stlouisfed.org/fred/series/observations", params={
            "series_id": sid, "api_key": FRED_API_KEY, "file_type": "json", "observation_start": "1995-01-01"}, timeout=30, retries=1)
        rows = [(o["date"][:7], o["value"]) for o in js.get("observations", [])]
    else:
        txt = await http.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": sid, "cosd": "1995-01-01"}, kind="text", timeout=30)
        rows = [(ln.split(",")[0][:7], ln.split(",")[1]) for ln in txt.splitlines()[1:] if "," in ln]
    return {m: float(v) for m, v in rows if v not in (".", "")}


def parse_ciss(txt: str) -> Dict[str, float]:
    df = pd.read_csv(io.StringIO(txt), usecols=["TIME_PERIOD", "OBS_VALUE"]).dropna()
    return {str(d)[:10]: round(float(v), 4) for d, v in zip(df["TIME_PERIOD"], df["OBS_VALUE"])}


async def refresh(force: bool = False) -> Dict:
    d = load()
    now = time.time()
    d["ts_check"] = now
    need = force or now - float(d.get("ts", 0)) > TTL or not d.get("ciss") or not d.get("yields")
    if need:
        bad = []
        try:
            c = parse_ciss(await http.get(CISS_URL, kind="text", timeout=60, retries=1))
            if len(c) < 1000:
                raise ValueError(f"only {len(c)} days")
            d["ciss"] = c
        except Exception as e:  # noqa: BLE001
            bad.append(f"ciss: {e if str(e) else type(e).__name__}")
        y = dict(d.get("yields") or {})
        for code in ["DE"] + [c for c, _z in COUNTRIES]:
            try:
                y[code] = await _fred(f"IRLTLT01{code}M156N")
            except Exception as e:  # noqa: BLE001
                bad.append(f"{code}: {e if str(e) else type(e).__name__}")
        if y:
            d["yields"] = y
        if len(bad) < 3:
            d["ts"] = now
        if bad:
            log.warning("euro/asia data: %s", "; ".join(bad))
            HEALTH.fail("euro_asia", "; ".join(bad), every=TTL)
        else:
            HEALTH.ok("euro_asia", len(d.get("ciss") or {}), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def _fwd_low(px: pd.Series, h: int) -> pd.Series:
    return px[::-1].rolling(h, min_periods=1).min()[::-1].shift(-1) / px - 1


def europe(d: Dict, spx: pd.Series) -> Optional[Dict]:
    out: Dict = {}
    c = d.get("ciss") or {}
    if len(c) > 1000:
        s = pd.Series(c)
        s.index = pd.to_datetime(s.index)
        s = s.sort_index()
        now = float(s.iloc[-1])
        band = next(z for lo, hi, z in CISS_BANDS if lo <= now < hi)
        ci = {"date": s.index[-1].strftime("%Y-%m-%d"), "now": now, "band": band, "pct": float((s.iloc[:-1] < now).mean() * 100),
              "chg21": float(s.iloc[-1] - s.iloc[-22]), "since": s.index[0].strftime("%Y"), "hist": [[i.strftime("%Y-%m-%d"), float(v)] for i, v in s.tail(260).items()]}
        if len(spx) > 1000:
            cs = s.reindex(spx.index).ffill()
            y = (_fwd_low(spx, 63) <= -0.10).astype(float).where(_fwd_low(spx, 63).notna())
            y[spx.index > spx.index[-1] - pd.Timedelta(days=95)] = np.nan
            rows = []
            for lo, hi, z in CISS_BANDS:
                m = (cs >= lo) & (cs < hi)
                rows.append({"band": z, "lo": lo, "hi": hi, "n": int(y[m].notna().sum()), "p": float(y[m].mean() * 100) if y[m].notna().any() else None,
                             "now": lo <= now < hi})
            ci.update(rows=rows, base=float(y[cs.notna()].mean() * 100))
        out["ciss"] = ci
    y = d.get("yields") or {}
    de = y.get("DE") or {}
    sp = []
    for code, zh in COUNTRIES:
        v = y.get(code) or {}
        ms = sorted(set(v) & set(de))
        if len(ms) < 60:
            continue
        s = pd.Series([v[m] - de[m] for m in ms], index=ms)
        hist = s[s.index >= "1999-01"]
        now = float(s.iloc[-1])
        sp.append({"code": code, "zh": zh, "month": ms[-1], "spread": now, "chg6": float(s.iloc[-1] - s.iloc[-7]) if len(s) > 7 else None,
                   "pct": float((hist.iloc[:-1] < now).mean() * 100), "max": float(hist.max()), "max_m": hist.idxmax(),
                   "yield": float(v[ms[-1]])})
    if sp:
        out["spreads"] = sp
        hot = [x for x in sp if x["pct"] >= 90]
        out["hot"] = hot
    return out or None


def equities(eng) -> Dict:
    rows = []
    for t, zh in EQ:
        try:
            s = eng.market.series(t).dropna()
        except Exception:  # noqa: BLE001
            continue
        if len(s) < 260:
            continue
        rows.append({"sym": t, "zh": zh, "m1": float(s.iloc[-1] / s.iloc[-22] - 1) * 100, "off": float(s.iloc[-1] / s.tail(252).max() - 1) * 100,
                     "date": s.index[-1].strftime("%Y-%m-%d")})
    out: Dict = {"rows": rows}
    try:
        cny = eng.market.series("CNY=X").dropna()
        if len(cny) > 30:
            out["cny"] = {"now": float(cny.iloc[-1]), "chg20": float(cny.iloc[-1] / cny.iloc[-21] - 1) * 100}
    except Exception:  # noqa: BLE001
        pass
    return out


def view(eng) -> Dict:
    d = load()
    try:
        spx = eng.market.series("^GSPC").dropna()
    except Exception:  # noqa: BLE001
        spx = pd.Series(dtype=float)
    out = {"ts_check": d.get("ts_check")}
    try:
        out["europe"] = europe(d, spx)
    except Exception:  # noqa: BLE001
        log.exception("europe view failed")
        out["europe"] = None
    try:
        out["asia"] = equities(eng)
    except Exception:  # noqa: BLE001
        log.exception("asia view failed")
        out["asia"] = None
    return out
