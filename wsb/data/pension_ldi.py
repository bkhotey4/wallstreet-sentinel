"""退休金與長天期公債：會不會再出一次 2022 年英國退休金危機。

退休金要在幾十年後付錢，所以手上有大量長天期公債或利率交換來「對沖」負債（LDI，負債驅動投資）。殖利率慢慢上升對它們是
好事（未來要付的錢折現後變少）；可是幾天內急升時，用槓桿做 LDI 的基金要補保證金，只好賣長債，越賣越跌。2022 年 9 月
英國就是這樣，英國央行最後進場買債。之後英國規定 LDI 基金至少要撐得住殖利率上升 2.5 個百分點（BUFFER_BP）。

這裡看四個市場的長天期公債，每個都和自己的歷史比：
  * 英國 20 年公債（英國央行每日名目平價殖利率 IUDLNPY，10 年 IUDMNPY 當對照）。
  * 歐元區 AAA 公債 30 年與 10 年（歐洲央行每日殖利率曲線）：30 年減 10 年的利差，是荷蘭退休金改革要看的地方。
  * 美國 30 年（FRED DGS30，從 engine 讀）、日本 30 年（日本財務省，從 engine 讀）。
規則：3 個交易日上升幅度落在自己歷史最高 0.5%、或超過 100bp → 紅燈；最高 2.5%（或 20 天升幅最高 2.5%）→ 黃燈。
快取 data_cache/econ_pension_ldi.json（CI 保留 econ_*），12 小時一次。描述現況，不是預測。"""
from __future__ import annotations

import io
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
FILE = DATA_DIR / "econ_pension_ldi.json"
TTL = 12 * 3600
BUFFER_BP = 250                      # 英國金融政策委員會 2023 年 3 月：LDI 基金至少撐得住約 250bp 的急升（退休金監理局 4 月寫進指引）
BUFFER_URL = "https://www.bankofengland.co.uk/financial-policy-summary-and-record/2023/bank-staff-paper-ldi-minimum-resilience"
BOE = ("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/1990&Dateto=now"
       "&SeriesCodes=IUDLNPY,IUDMNPY&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N")
ECB = "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_{t}Y?format=csvdata"
RED_PCT, YEL_PCT, RED_BP = 99.5, 97.5, 100.0
STEP, STEP20 = 3, 20
# (key, 中文, 長天期, 10 年, 誰持有這些長債)
MARKETS = (("uk", "英國", "20 年", "10 年", "英國確定給付退休金（LDI 基金用槓桿持有長債）"),
           ("eu", "歐元區 AAA", "30 年", "10 年", "荷蘭等歐洲退休金（用 30 年以上利率交換避險）"),
           ("us", "美國", "30 年", "10 年", "美國企業退休金（多用不加槓桿的長天期公司債）"),
           ("jp", "日本", "30 年", "10 年", "日本壽險公司與退休基金"))


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def parse_boe(txt: str) -> Dict[str, Dict[str, float]]:
    df = pd.read_csv(io.StringIO(txt))
    df.index = pd.to_datetime(df["DATE"], format="%d %b %Y", errors="coerce")
    df = df[df.index.notna()]
    out = {}
    for col, k in (("IUDLNPY", "long"), ("IUDMNPY", "y10")):
        s = pd.to_numeric(df.get(col), errors="coerce").dropna()
        out[k] = {i.strftime("%Y-%m-%d"): round(float(v), 4) for i, v in s.items()}
    if len(out["long"]) < 1000:
        raise ValueError(f"BoE: only {len(out['long'])} days")
    return out


def parse_ecb(txt: str) -> Dict[str, float]:
    df = pd.read_csv(io.StringIO(txt), usecols=["TIME_PERIOD", "OBS_VALUE"]).dropna()
    return {str(d)[:10]: round(float(v), 4) for d, v in zip(df["TIME_PERIOD"], df["OBS_VALUE"])}


async def refresh(force: bool = False) -> Dict:
    from .freshness import bundle_ts, due
    d = load()
    now = time.time()
    d["ts_check"] = now
    keys = ["uk", "eu"]
    each = d.setdefault("ts_each", {})
    todo = due(d, keys, TTL, now, force)
    if todo:
        bad = []
        if "uk" in todo:
            d["try_each"]["uk"] = now
            try:
                d["uk"], each["uk"] = parse_boe(await http.get(BOE, kind="text", timeout=60, retries=1,
                                                               headers={"User-Agent": "Mozilla/5.0"})), now
            except Exception as e:  # noqa: BLE001
                bad.append(f"uk: {e if str(e) else type(e).__name__}")
        if "eu" in todo:
            d["try_each"]["eu"] = now
            try:
                eu = {"long": parse_ecb(await http.get(ECB.format(t=30), kind="text", timeout=60, retries=1)),
                      "y10": parse_ecb(await http.get(ECB.format(t=10), kind="text", timeout=60, retries=1))}
                if len(eu["long"]) < 1000:
                    raise ValueError(f"only {len(eu['long'])} days")
                d["eu"], each["eu"] = eu, now
            except Exception as e:  # noqa: BLE001
                bad.append(f"eu: {e if str(e) else type(e).__name__}")
        bad += [f"{k}: stale" for k in keys if k not in todo and now - float(each.get(k, 0)) > TTL]
        d["ts"] = bundle_ts(d, keys)
        if bad:
            log.warning("pension/LDI data: %s", "; ".join(bad))
            HEALTH.fail("pension_ldi", "; ".join(bad), every=TTL)
        else:
            HEALTH.ok("pension_ldi", len((d.get("uk") or {}).get("long") or {}), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def _ser(m: Dict) -> pd.Series:
    s = pd.Series(m or {}, dtype=float)
    if s.empty:
        return s
    s.index = pd.to_datetime(s.index)
    return s.sort_index().dropna()


def _pct(hist: pd.Series, v: float) -> Optional[float]:
    hist = hist.dropna()
    return float((hist < v).mean() * 100) if len(hist) > 250 else None


def market(key: str, long: pd.Series, y10: pd.Series) -> Optional[Dict]:
    """Level, 3-day and 20-day rise (bp) against the series' own history, the record 3-day rise, and the long−10y slope."""
    long = long.dropna()
    if len(long) < 500:
        return None
    c3 = (long - long.shift(STEP)) * 100
    c20 = (long - long.shift(STEP20)) * 100
    now3, now20 = float(c3.iloc[-1]), float(c20.iloc[-1])
    top = c3.idxmax()
    out = {"key": key, "date": long.index[-1].strftime("%Y-%m-%d"), "level": float(long.iloc[-1]), "since": long.index[0].strftime("%Y"),
           "c3": now3, "c20": now20, "p3": _pct(c3.iloc[:-1], now3), "p20": _pct(c20.iloc[:-1], now20),
           "max3": float(c3.max()), "max3_date": top.strftime("%Y-%m-%d"),
           "hist": [[i.strftime("%Y-%m-%d"), round(float(v), 3)] for i, v in long[long.index >= long.index[-1] - pd.DateOffset(years=5)].resample("W-FRI").last().dropna().items()]}
    j = pd.concat([long, y10.dropna()], axis=1, join="inner").dropna()
    if len(j) > 500:
        sl = (j.iloc[:, 0] - j.iloc[:, 1]) * 100
        yago = sl[sl.index <= sl.index[-1] - pd.DateOffset(years=1)]
        out.update(slope=float(sl.iloc[-1]), slope_pct=_pct(sl.iloc[:-1], float(sl.iloc[-1])),
                   slope_1y=float(sl.iloc[-1] - yago.iloc[-1]) if len(yago) else None)
    p3, p20 = out["p3"] or 0, out["p20"] or 0
    if now3 >= RED_BP or p3 >= RED_PCT:
        out["emoji"], out["state"] = "🔴", "急升"
    elif p3 >= YEL_PCT or p20 >= YEL_PCT:
        out["emoji"], out["state"] = "🟡", "升得快"
    else:
        out["emoji"], out["state"] = "🟢", "平穩"
    return out


def view(eng=None) -> Dict:
    d = load()
    rows: List[Dict] = []
    src = {"uk": ((d.get("uk") or {}).get("long"), (d.get("uk") or {}).get("y10")),
           "eu": ((d.get("eu") or {}).get("long"), (d.get("eu") or {}).get("y10"))}
    for k, (a, b) in src.items():
        try:
            r = market(k, _ser(a), _ser(b))
            if r:
                rows.append(r)
        except Exception:  # noqa: BLE001
            log.exception("pension view %s failed", k)
    fr = getattr(eng, "fred", None)
    if fr is not None:
        try:
            a, b = fr.get("DGS30"), fr.get("DGS10")
            if a is not None and b is not None:
                r = market("us", a, b)
                if r:
                    rows.append(r)
        except Exception:  # noqa: BLE001
            log.exception("pension view us failed")
    jg = getattr(getattr(eng, "global_yields", None), "jgb", None)
    if jg is not None and len(jg) and "30Y" in jg.columns and "10Y" in jg.columns:
        try:
            r = market("jp", jg["30Y"], jg["10Y"])
            if r:
                rows.append(r)
        except Exception:  # noqa: BLE001
            log.exception("pension view jp failed")
    meta = {k: (zh, lt, st, who) for k, zh, lt, st, who in MARKETS}
    for r in rows:
        r["zh"], r["tenor"], r["short"], r["who"] = meta[r["key"]]
    rows.sort(key=lambda r: [m[0] for m in MARKETS].index(r["key"]))
    return {"rows": rows, "ts": d.get("ts"), "ts_each": d.get("ts_each") or {}}


def alerts(v: Dict) -> List[tuple]:
    """(key, severity, title, detail) — one per market per day it is red."""
    out = []
    for r in v.get("rows") or []:
        if r.get("emoji") != "🔴":
            continue
        out.append((f"ldi:{r['key']}:{r['date']}", "⚠️ WARNING",
                    f"{r['zh']} {r['tenor']}公債 3 天升 {r['c3']:+.0f}bp（{r['since']} 年以來第 {r['p3']:.1f} 百分位）",
                    f"現在 {r['level']:.2f}%。歷史最大 3 天升幅 {r['max3']:.0f}bp（{r['max3_date']}）。"
                    f"長債急升時，用槓桿避險的退休金要補保證金，可能被迫賣債。英國規定 LDI 基金至少撐得住 {BUFFER_BP}bp。"
                    "看網站「金融穩定監測」頁的退休金卡。"))
    return out
