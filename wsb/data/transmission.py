"""第二意見與傳導管道：會不會把局部泡沫變成全面崩跌的三條路，各用官方免費數據、各自回測。

  * OFR 金融壓力指數（美國財政部金融研究辦公室，2000 年起每日）：獨立於本站 SSI 的第二意見。0＝平均壓力，
    越高越緊張；分信用、股市估值、避險資產、資金、波動五塊。回測：落在哪一檔時，標普之後 3 個月跌 ≥10% 的頻率。
  * 外國央行託管的美債（紐約聯準會代管，FRED WMTSECL1，每週）：外國官方是在增持還是撤離美債——
    「美元信任」最直接的數據。描述趨勢，不宣稱能預測股市。
  * 日圓套利交易：美元兌日圓的水準與 20 日變化（FRED DEXJPUS）＋ CFTC 投機部位放空日圓的規模（097741）。
    1990 年以來回測：日圓 20 天急升之後，標普一個月內跌 ≥5% 的頻率和平常幾乎一樣——所以只當背景，不當警報。

快取 data_cache/econ_transmission.json（CI 保留 econ_*），每 12 小時最多抓一次。"""
from __future__ import annotations

import io
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
FILE = DATA_DIR / "econ_transmission.json"
TTL = 12 * 3600
OFR_URL = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"
CFTC_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research)"}
FSI_PARTS = (("Credit", "信用"), ("Equity valuation", "股市估值"), ("Safe assets", "避險資產"), ("Funding", "資金"), ("Volatility", "波動"))
FSI_BANDS = ((-99, -1, "壓力低"), (-1, 0, "略低於平均"), (0, 2, "略高於平均"), (2, 5, "壓力高"), (5, 99, "壓力很高"))


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)


def parse_fsi(txt: str) -> Dict[str, List]:
    df = pd.read_csv(io.StringIO(txt), index_col=0)
    cols = ["OFR FSI"] + [c for c, _z in FSI_PARTS if c in df.columns]
    df = df[cols].dropna(subset=["OFR FSI"])
    return {"dates": [str(i)[:10] for i in df.index], **{c: [round(float(v), 3) for v in df[c].values] for c in cols}}


async def _fred(sid: str, start: str) -> Dict[str, float]:
    from ..config import FRED_API_KEY
    if FRED_API_KEY:
        js = await http.get("https://api.stlouisfed.org/fred/series/observations", params={
            "series_id": sid, "api_key": FRED_API_KEY, "file_type": "json", "observation_start": start}, timeout=30, retries=1)
        rows = [(o["date"], o["value"]) for o in js.get("observations", [])]
    else:
        txt = await http.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": sid, "cosd": start}, kind="text", timeout=30)
        rows = [tuple(ln.split(",")[:2]) for ln in txt.splitlines()[1:] if "," in ln]
    return {d: float(v) for d, v in rows if v not in (".", "")}


async def _yen_cftc() -> List[List]:
    js = await http.get(CFTC_URL, params={
        "$select": "report_date_as_yyyy_mm_dd,open_interest_all,lev_money_positions_long,lev_money_positions_short,asset_mgr_positions_long,asset_mgr_positions_short",
        "$where": "cftc_contract_market_code='097741'", "$order": "report_date_as_yyyy_mm_dd", "$limit": "3000"}, headers=UA, timeout=60, retries=1)
    out = []
    for r in js if isinstance(js, list) else []:
        try:
            oi = float(r["open_interest_all"])
            spec = (float(r["lev_money_positions_long"]) + float(r["asset_mgr_positions_long"])
                    - float(r["lev_money_positions_short"]) - float(r["asset_mgr_positions_short"])) / oi * 100
            out.append([r["report_date_as_yyyy_mm_dd"][:10], round(spec, 2)])
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    return out


async def refresh(force: bool = False) -> Dict:
    d = load()
    now = time.time()
    d["ts_check"] = now
    bad = []
    if force or now - float(d.get("ts", 0)) > TTL or not d.get("fsi"):
        steps = (("fsi", lambda: _get_fsi()), ("custody", lambda: _fred("WMTSECL1", "2003-01-01")),
                 ("swaps", lambda: _fred("SWPT", "2007-01-01")), ("gdpnow", lambda: _fred("GDPNOW", "2011-01-01")),
                 ("jpy", lambda: _fred("DEXJPUS", "1990-01-01")), ("yen_cftc", _yen_cftc))
        for k, fn in steps:
            try:
                v = await fn()
                if not v:
                    raise ValueError("empty")
                d[k] = v
            except Exception as e:  # noqa: BLE001
                bad.append(f"{k}: {e if str(e) else type(e).__name__}")
        if len(bad) < len(steps):
            d["ts"] = now
    _save(d)
    if bad:
        log.warning("transmission data: %s", "; ".join(bad))
        HEALTH.fail("transmission", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("transmission", len((d.get("fsi") or {}).get("dates") or []), every=TTL)
    return d


async def _get_fsi():
    return parse_fsi(await http.get(OFR_URL, kind="text", headers=UA, timeout=60, retries=2))


# ───────────────────────── 判讀 ─────────────────────────
def _fwd_low(spx: pd.Series, h: int) -> pd.Series:
    return spx[::-1].rolling(h, min_periods=1).min()[::-1].shift(-1) / spx - 1


def fsi_view(d: Dict, spx: pd.Series, ssi: Optional[float] = None) -> Optional[Dict]:
    f = d.get("fsi") or {}
    if len(f.get("dates") or []) < 500:
        return None
    s = pd.Series(f["OFR FSI"], index=pd.to_datetime(f["dates"]))
    now = float(s.iloc[-1])
    band = next(z for lo, hi, z in FSI_BANDS if lo < now <= hi)
    out = {"date": f["dates"][-1], "now": now, "band": band, "chg21": float(s.iloc[-1] - s.iloc[-22]) if len(s) > 22 else None,
           "pct": float((s.iloc[:-1] < now).mean() * 100), "since": f["dates"][0][:4],
           "parts": [(z, float(f[c][-1])) for c, z in FSI_PARTS if c in f], "hist": [[i.strftime("%Y-%m-%d"), float(v)] for i, v in s.tail(260).items()]}
    if len(spx) > 1000:
        fs = s.reindex(spx.index).ffill()
        y = (_fwd_low(spx, 63) <= -0.10).astype(float).where(_fwd_low(spx, 63).notna())
        y[spx.index > spx.index[-1] - pd.Timedelta(days=95)] = np.nan
        rows = []
        for lo, hi, z in FSI_BANDS:
            m = (fs > lo) & (fs <= hi)
            rows.append({"band": z, "lo": lo, "hi": hi, "n": int(y[m].notna().sum()), "p": float(y[m].mean() * 100) if y[m].notna().any() else None,
                         "now": lo < now <= hi})
        out.update(rows=rows, base=float(y.mean() * 100))
    if ssi is not None:
        hi_ssi, lo_fsi = ssi >= 55, now <= 0
        out["vs_ssi"] = ("分歧：本站 SSI 說壓力升溫，OFR 說壓力低於平均" if hi_ssi and lo_fsi else
                         "分歧：本站 SSI 平靜，OFR 說壓力偏高" if not hi_ssi and now > 2 else "一致")
        out["ssi"] = ssi
    return out


def custody_view(d: Dict) -> Optional[Dict]:
    c = d.get("custody") or {}
    if len(c) < 120:
        return None
    s = pd.Series(c)
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    ch13 = s.pct_change(13) * 100
    now13 = float(ch13.iloc[-1])
    pct = float((ch13.dropna().iloc[:-1] < now13).mean() * 100)
    out = {"date": s.index[-1].strftime("%Y-%m-%d"), "tn": float(s.iloc[-1]) / 1e6, "chg13": now13, "chg52": float(s.iloc[-1] / s.iloc[-53] - 1) * 100,
           "pct13": pct, "peak": float(s.max()) / 1e6, "peak_d": s.idxmax().strftime("%Y-%m"), "since": s.index[0].strftime("%Y"),
           "hist": [[i.strftime("%Y-%m-%d"), float(v) / 1e6] for i, v in s.tail(260).items()]}
    out["state"], out["emoji"] = (("撤離加速", "🔴") if pct <= 5 else ("減持", "🟡") if pct <= 20 or out["chg52"] < -3 else ("持平或增持", "🟢"))
    return out


def yen_view(d: Dict, spx: pd.Series) -> Optional[Dict]:
    j = d.get("jpy") or {}
    if len(j) < 1000:
        return None
    s = pd.Series(j)
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    ch20 = (s / s.shift(20) - 1) * 100                         # negative = yen stronger
    out = {"date": s.index[-1].strftime("%Y-%m-%d"), "usdjpy": float(s.iloc[-1]), "chg20": float(ch20.iloc[-1]),
           "pct10y": float((s.tail(2520).iloc[:-1] < s.iloc[-1]).mean() * 100)}
    if len(spx) > 1000:
        y = (_fwd_low(spx, 21) <= -0.05).astype(float).where(_fwd_low(spx, 21).notna())
        y[spx.index > spx.index[-1] - pd.Timedelta(days=35)] = np.nan
        c = ch20.reindex(spx.index).ffill()
        m = c <= -5
        out.update(bt_n=int(y[m].notna().sum()), bt_p=float(y[m].mean() * 100) if y[m].notna().any() else None, bt_base=float(y.mean() * 100),
                   bt_since=s.index[0].strftime("%Y"))
    yc = d.get("yen_cftc") or []
    if len(yc) > 100:
        v = [r[1] for r in yc]
        out.update(spec=v[-1], spec_date=yc[-1][0], spec_pct=float(sum(x < v[-1] for x in v[:-1]) / (len(v) - 1) * 100))
    spec, sp_pct = out.get("spec"), out.get("spec_pct")
    carry_big = spec is not None and spec < 0 and sp_pct is not None and sp_pct <= 20     # speculators heavily short yen = big carry
    out["carry_big"] = carry_big
    out["state"] = ("日圓急升中（套利平倉）" if out["chg20"] <= -5 else
                    "日圓偏弱、投機客大量放空日圓（套利部位大）" if carry_big else
                    "日圓偏弱，但投機部位是做多日圓（套利部位不大）" if spec is not None and spec > 0 and out["pct10y"] >= 80 else "平穩")
    return out


def dollar_view(d: Dict) -> Optional[Dict]:
    """Fed central-bank liquidity swaps (FRED SWPT, weekly, $ millions) and the Atlanta Fed GDPNow (FRED GDPNOW, latest quarter)."""
    sw, gn = d.get("swaps") or {}, d.get("gdpnow") or {}
    if len(sw) < 50 and not gn:
        return None
    out: Dict = {}
    if len(sw) >= 50:
        s = pd.Series(sw).sort_index()
        big = s[s >= 10000]
        eps, last = [], None
        for dt in big.index:                                   # spells of ≥ $10 bn, a new spell after 26 quiet weeks
            if last is None or (pd.Timestamp(dt) - pd.Timestamp(last)).days > 182:
                eps.append(dt[:7])
            last = dt
        now = float(s.iloc[-1])
        out["swaps"] = {"date": s.index[-1], "bn": now / 1000, "peak": float(s.max()) / 1000, "peak_d": s.idxmax()[:7], "spells": eps,
                        "state": "美元荒" if now >= 10000 else "有人在借" if now >= 1000 else "正常（幾乎沒人用）",
                        "emoji": "🔴" if now >= 10000 else "🟡" if now >= 1000 else "🟢"}
    if gn:
        q = sorted(gn)[-1]
        y, m = int(q[:4]), int(q[5:7])
        out["gdpnow"] = {"quarter": f"{y}Q{(m - 1) // 3 + 1}", "pct": float(gn[q]), "prev": float(gn[sorted(gn)[-2]]) if len(gn) > 1 else None,
                         "emoji": "🔴" if gn[q] < 0 else "🟡" if gn[q] < 1 else "🟢"}
    return out


def view(eng) -> Dict:
    d = load()
    try:
        spx = eng.market.series("^GSPC").dropna()
    except Exception:  # noqa: BLE001
        spx = pd.Series(dtype=float)
    ssi = getattr(getattr(eng, "stress", None), "score", None)
    out = {"ts_check": d.get("ts_check")}
    for k, fn in (("fsi", lambda: fsi_view(d, spx, ssi)), ("custody", lambda: custody_view(d)), ("yen", lambda: yen_view(d, spx)),
                  ("dollar", lambda: dollar_view(d))):
        try:
            out[k] = fn()
        except Exception:  # noqa: BLE001
            log.exception("transmission view %s failed", k)
            out[k] = None
    return out
