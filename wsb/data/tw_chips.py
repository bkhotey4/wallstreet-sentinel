"""台股籌碼深度與公司體質（2026-11-22，台股覆蓋清單補缺；使用者：「還缺的跟分工的，這 2 個部分做吧」）。

全部是官方免費資料，每天存一份，算變化：
  * 外資持股比率（類股）：證交所 OpenAPI fund/MI_QFIIS_cat
  * 借券放空餘額：證交所 exchangeReport/TWT93U（信用額度總量管制餘額表；借券賣出當日餘額＝前日＋當日賣出－還券＋調整）
  * 期貨三大法人台指期未平倉：期交所 OpenAPI MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate
  * 期貨大額交易人（台指期，全部月份 999912）：期交所 OpenAPI OpenInterestOfLargeTradersFutures（前五／前十大、全部或特定法人）
  * 董監持股質押：證交所 OpenAPI opendata/t187ap11_L（每月；資料約 10MB，一天抓一次）
  * 財測達成：證交所 OpenAPI opendata/t187ap15_L（只有公開財測的公司）
  * 季報快照：證交所 OpenAPI opendata/t187ap06_L_ci（累計數；每季存一份，之後相減得單季）
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_chips.json"
SNAP = DATA_DIR / "econ_tw_fin_snap.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_chips_seed.json"
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
U_QFII = "https://openapi.twse.com.tw/v1/fund/MI_QFIIS_cat"
U_SBL = "https://www.twse.com.tw/exchangeReport/TWT93U?response=json"
U_INST = "https://openapi.taifex.com.tw/v1/MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate"
U_LARGE = "https://openapi.taifex.com.tw/v1/OpenInterestOfLargeTradersFutures"
U_PLEDGE = "https://openapi.twse.com.tw/v1/opendata/t187ap11_L"
U_FCST = "https://openapi.twse.com.tw/v1/opendata/t187ap15_L"
U_FCST2 = "https://openapi.twse.com.tw/v1/opendata/t187ap16_L"     # 當季 and 截至當季 side by side, same basis
U_FIN = "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci"
U_MARGN = "https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&selectType=ALL"
U_CLOSE = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
U_DAYTRADE = "https://www.twse.com.tw/exchangeReport/TWTB4U?response=json&date={d}"
U_LARGE_OPT = "https://openapi.taifex.com.tw/v1/OpenInterestOfLargeTradersOptions"   # 11-22 (fields checked on the live API)
U_SBL_O = "https://www.tpex.org.tw/openapi/v1/tpex_margin_sbl"                 # 上櫃 (Gemini TWC-4, checked 11-22)
U_WARN_L = "https://openapi.twse.com.tw/v1/announcement/notice"                # 上市注意股
U_WARN_O = "https://www.tpex.org.tw/openapi/v1/tpex_trading_warning_information"  # 上櫃注意股
TTL = 4 * 3600
HEAVY_TTL = 24 * 3600
KEEP = 400
TPE = timezone(timedelta(hours=8))


def _n(s) -> Optional[float]:
    try:
        return float(re.sub(r"[,\s%]", "", str(s)))
    except (TypeError, ValueError):
        return None


def parse_qfii(rows: List[Dict]) -> List[Dict]:
    return [{"cat": str(r.get("IndustryCat") or "").strip(), "n": int(_n(r.get("Numbers")) or 0), "pct": _n(r.get("Percentage"))}
            for r in rows or [] if r.get("IndustryCat") and _n(r.get("Percentage")) is not None]


def parse_sbl(js: Dict, universe: Optional[set] = None) -> Dict:
    """Total borrowed-share short balance (shares) today vs the day before, and the stocks that added the most."""
    data = (js or {}).get("data") or []
    tot = prev = 0.0
    moves = []
    for r in data:
        if len(r) < 13:
            continue
        p, today = _n(r[8]) or 0.0, _n(r[12]) or 0.0
        tot += today
        prev += p
        if universe is None or r[0] in universe:
            moves.append({"code": r[0], "name": r[1].strip(), "bal": today, "chg": today - p})
    moves.sort(key=lambda x: -x["chg"])
    return {"date": (js or {}).get("date"), "total": tot, "prev": prev, "add": moves[:10], "cut": sorted(moves, key=lambda x: x["chg"])[:10]}


def parse_sbl_otc(rows: List[Dict]) -> Dict:
    tot = prev = 0.0
    for r in rows or []:
        tot += _n(r.get("SecuritiesBorrowingBalanceOfTheMarketDay")) or 0.0
        prev += _n(r.get("SecuritiesBorrowingBalancePreviousDay")) or 0.0
    return {"date": (rows or [{}])[0].get("Date"), "total": tot, "prev": prev}


def parse_warn(listed: List[Dict], otc: List[Dict]) -> List[Dict]:
    out = [{"code": str(r.get("Code") or "").strip(), "name": str(r.get("Name") or "").strip(), "why": str(r.get("TradingInfoForAttention") or "").strip(),
            "board": "上市", "date": r.get("Date")} for r in listed or [] if str(r.get("Code") or "").strip()]
    out += [{"code": str(r.get("SecuritiesCompanyCode") or "").strip(), "name": str(r.get("CompanyName") or "").strip(),
             "why": str(r.get("TradingInformation") or "").strip(), "board": "上櫃", "date": r.get("Date")} for r in otc or []
            if str(r.get("SecuritiesCompanyCode") or "").strip()]
    return out


def parse_inst(rows: List[Dict]) -> Dict:
    out = {}
    for r in rows or []:
        if r.get("ContractCode") == "臺股期貨":
            out[str(r.get("Item"))] = {"net_oi": _n(r.get("OpenInterest(Net)")), "net_trade": _n(r.get("TradingVolume(Net)")), "date": r.get("Date")}
    return out


def parse_large(text: str) -> Dict:
    """台指期 all months (999912): top-5 / top-10 traders' long minus short, for all traders (0) and specific institutions (1)."""
    rows = list(csv.reader(io.StringIO((text or "").lstrip("﻿"))))
    out = {}
    for r in rows[1:]:
        if len(r) >= 10 and r[1].strip() == "TX" and r[3].strip() == "999912":
            k = "all" if r[4].strip() == "0" else "inst"
            b5, s5, b10, s10, oi = (_n(x) or 0.0 for x in r[5:10])
            out[k] = {"date": r[0], "top5_net": b5 - s5, "top10_net": b10 - s10, "oi": oi}
    return out


def parse_large_opt(rows: List[Dict]) -> Dict:
    """臺指選擇權 all months (999912): top-10 traders' long minus short for calls and puts, all traders (all) / specific institutions (inst)."""
    out: Dict = {}
    for r in rows or []:
        if r.get("Contract") != "TXO" or r.get("SettlementMonth") != "999912":
            continue
        k = "all" if str(r.get("TypeOfTraders")) == "0" else "inst"
        cp = "call" if r.get("CallPut") == "買權" else "put"
        out.setdefault(k, {"date": r.get("Date")})[cp] = {"top10_net": (_n(r.get("Top10Buy")) or 0) - (_n(r.get("Top10Sell")) or 0),
                                                         "oi": _n(r.get("OIOfMarket"))}
    return out


def margin_ratio(mg: Dict, closes: List[Dict]) -> Optional[Dict]:
    """上市整體融資維持率（估算）＝ Σ 每檔融資餘額（張）× 1,000 × 收盤價 ÷ 融資金額。和媒體常用的算法相同；個別帳戶低於 130% 會被追繳。"""
    tabs = (mg or {}).get("tables") or []
    if len(tabs) < 2:
        return None
    loan = next((_n(r[5]) for r in tabs[0].get("data") or [] if "融資金額" in str(r[0])), None)
    px = {str(r.get("Code")): _n(r.get("ClosingPrice")) for r in closes or []}
    mv = 0.0
    for r in tabs[1].get("data") or []:
        p, bal = px.get(str(r[0])), _n(r[6])
        if p and bal:
            mv += bal * 1000 * p
    if not loan:
        return None
    return {"date": mg.get("date"), "ratio": mv / (loan * 1000) * 100, "mv": mv, "loan": loan * 1000}


def parse_daytrade(js: Dict) -> Optional[Dict]:
    for tb in (js or {}).get("tables") or []:
        if "統計資訊" in str(tb.get("title")) and tb.get("data"):
            r = tb["data"][0]
            return {"date": js.get("date"), "share_pct": _n(r[1]), "value_pct": _n(r[3])}
    return None


def parse_pledge(rows: List[Dict], universe: Optional[set] = None) -> List[Dict]:
    """Per company: insiders' (directors and their related parties) pledged shares as % of their holdings."""
    agg: Dict[str, Dict] = {}
    for r in rows or []:
        code = str(r.get("公司代號") or "").strip()
        if not code or (universe is not None and code not in universe):
            continue
        a = agg.setdefault(code, {"code": code, "name": str(r.get("公司名稱") or "").strip(), "held": 0.0, "pledged": 0.0, "ym": r.get("資料年月")})
        a["held"] += _n(r.get("目前持股")) or 0.0
        a["pledged"] += _n(r.get("設質股數")) or 0.0
    out = [{**a, "pct": a["pledged"] / a["held"] * 100} for a in agg.values() if a["held"] > 0]
    return sorted(out, key=lambda x: -x["pct"])


def parse_forecast(rows: List[Dict]) -> List[Dict]:
    out = []
    for r in rows or []:
        keys = list(r.keys())
        act = next((r[k] for k in keys if "查核" in k or "核閱數" in k), None)
        fc = next((r[k] for k in keys if "預測數" in k and "達成" not in k), None)
        rate = next((r[k] for k in keys if "達成" in k), None)
        out.append({"code": str(r.get("公司代號") or "").strip(), "name": str(r.get("公司名稱") or "").strip(), "year": r.get("年度"),
                    "q": r.get("季別"), "actual": _n(act), "forecast": _n(fc), "rate": _n(rate)})
    return [x for x in out if x["code"]]


def _range(v) -> Optional[tuple]:
    """'9455288~10182350' → (9455288.0, 10182350.0); '-72844' → (-72844.0, -72844.0)."""
    m = re.fullmatch(r"\s*(-?[\d,]+(?:\.\d+)?)\s*(?:~\s*(-?[\d,]+(?:\.\d+)?))?\s*", str(v or ""))
    if not m:
        return None
    lo = float(m.group(1).replace(",", ""))
    hi = float(m.group(2).replace(",", "")) if m.group(2) else lo
    return (min(lo, hi), max(lo, hi))


def _latest_rev(rows: List[Dict]) -> Dict[str, Dict]:
    """Several 財測序號 per company = revised forecasts; keep the highest."""
    out: Dict[str, Dict] = {}
    for r in rows or []:
        c = str(r.get("公司代號") or "").strip()
        if c and (c not in out or int(r.get("財測序號") or 0) >= int(out[c].get("財測序號") or 0)):
            out[c] = r
    return out


def forecast_view(ap15: List[Dict], ap16: List[Dict], snaps: Dict[str, Dict]) -> List[Dict]:
    """財測達成（11-22）. Both TWSE files are in 千元 and on 綜合損益 (Gemini TWC-5; 中華電 32,139,221 = its year-to-date comprehensive
    income). t187ap15's 「截至該季綜合損益預測數」 is in fact the single-quarter forecast (it equals t187ap16's 「當季」 column for 中華電), so:
      * company in t187ap16 → this quarter vs this quarter's forecast, year to date vs year to date (exact, official);
      * only in t187ap15   → this quarter's forecast vs single-quarter net income attributable to the parent from the MOPS cumulative
                             statements (Q3 − Q2), marked approximate (forecast is comprehensive income; OCI such as FX differs)."""
    a16, a15 = _latest_rev(ap16), _latest_rev(ap15)
    out = []
    for c, r in {**a15, **a16}.items():
        y, q = str(r.get("年度") or ""), int(r.get("季別") or 0)
        row = {"code": c, "name": str(r.get("公司名稱") or "").strip(), "q": f"{y}Q{q}", "cover": r.get("涵蓋期間"), "rev": r.get("財測序號")}
        if c in a16:
            row.update(exact=True, q_act=_n(r.get("當季經會計師查核或核閱數")), q_fc=_range(r.get("當季稅前(綜合)損益預測數")),
                       ytd_act=_n(r.get("截至當季經會計師查核或核閱數")), ytd_fc=_range(r.get("截至當季稅前(綜合)損益預測數")))
        else:
            cur, prev = (snaps.get(f"{y}Q{q}") or {}).get(c), (snaps.get(f"{y}Q{q - 1}") or {}).get(c) if q > 1 else None
            qa = None
            if cur and cur.get("ni") is not None:
                qa = cur["ni"] - prev["ni"] if q > 1 and prev and prev.get("ni") is not None else (cur["ni"] if q == 1 else None)
            row.update(exact=False, q_act=qa, q_fc=_range(r.get("截至該季綜合損益預測數")), ytd_act=_n(r.get("截至該季經會計師查核或核閱數")), ytd_fc=None)
        for k in ("q", "ytd"):
            act, fc = row.get(f"{k}_act"), row.get(f"{k}_fc")
            if act is None or not fc:
                row[f"{k}_where"] = None
                continue
            lo, hi = fc
            row[f"{k}_where"] = "above" if act > hi else "below" if act < lo else "in"
            edge = hi if act > hi else lo if act < lo else None
            row[f"{k}_close"] = bool(not row["exact"] and edge is not None and abs(act - edge) <= 0.02 * max(abs(edge), 1.0))   # inside approx error
            mid = (lo + hi) / 2
            row[f"{k}_pct"] = act / mid * 100 if mid > 0 else None
        out.append(row)
    return sorted(out, key=lambda x: x["code"])


def _get(url: str, kind: str = "json"):
    import requests
    r = requests.get(url, headers=UA, timeout=40)
    r.raise_for_status()
    if kind == "text":
        r.encoding = "utf-8"
        return r.text
    return r.json()


def _load(f) -> Dict:
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except (OSError, ValueError):
        return {}


def _save(f, d: Dict) -> None:
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, f)


def _universe() -> set:
    try:
        from . import tw_desk as D
        return set(D.universe(D.load()).get("codes") or [])
    except Exception:  # noqa: BLE001
        return set()


def snapshot_fin(rows: List[Dict], snaps: Dict) -> Dict:
    """Store the cumulative income statement once per (year, quarter); single quarters come from differences later."""
    for r in rows or []:
        y, q, code = str(r.get("年度") or ""), str(r.get("季別") or ""), str(r.get("公司代號") or "").strip()
        if not (y and q and code):
            continue
        k = f"{y}Q{q}"
        snaps.setdefault(k, {})[code] = {"rev": _n(r.get("營業收入")), "gross": _n(r.get("營業毛利（毛損）淨額")),
                                         "op": _n(r.get("營業利益（損失）")), "ni": _n(r.get("淨利（淨損）歸屬於母公司業主")),
                                         "eps": _n(r.get("基本每股盈餘（元）")), "name": str(r.get("公司名稱") or "").strip()}
    return snaps


def single_quarter(snaps: Dict, code: str, year: str, q: int) -> Optional[Dict]:
    """Q1 = cumulative; Qn = cumulative(n) − cumulative(n−1).  None until both snapshots exist."""
    cur = (snaps.get(f"{year}Q{q}") or {}).get(code)
    if not cur:
        return None
    if q == 1:
        return dict(cur)
    prev = (snaps.get(f"{year}Q{q - 1}") or {}).get(code)
    if not prev:
        return None
    return {k: (cur[k] - prev[k]) if isinstance(cur.get(k), float) and isinstance(prev.get(k), float) else cur.get(k) for k in cur}


def _apply_seed(d: Dict, day: Optional[Dict]) -> None:
    """PC relay (11-22: the TAIFEX large-trader CSV does not reach the cloud build): use it when newer than what we have."""
    seed = _load(SEED)
    for name in ("large", "large_opt"):
        sv = seed.get(name) or {}
        mine = str(((d.get(name) or {}).get("inst") or {}).get("date") or "")
        if str((sv.get("inst") or {}).get("date") or "") > mine:
            d[name] = sv
            if day is not None:
                day[name] = sv
    for name in ("sbl_otc", "warn", "mratio", "daytrade", "fc15", "fc16"):   # use the relay when this machine has none
        if not d.get(name) and seed.get(name):
            d[name] = seed[name]


def refresh(force: bool = False) -> Dict:
    d = _load(FILE)
    now = time.time()
    if not force and now - float(d.get("ts") or 0) < TTL:
        _apply_seed(d, None)                              # the relay may be newer than this machine's cache
        return d
    d["ts"] = now
    today = datetime.now(TPE).strftime("%Y-%m-%d")
    hist = d.setdefault("hist", {})
    day = hist.setdefault(today, {})
    uni = _universe()
    for name, fn in (("qfii", lambda: parse_qfii(_get(U_QFII))),
                     ("sbl", lambda: parse_sbl(_get(U_SBL), uni or None)),
                     ("inst", lambda: parse_inst(_get(U_INST))),
                     ("large", lambda: parse_large(_get(U_LARGE, "text"))),
                     ("large_opt", lambda: parse_large_opt(_get(U_LARGE_OPT))),
                     ("mratio", lambda: margin_ratio(_get(U_MARGN), _get(U_CLOSE))),
                     ("daytrade", lambda: parse_daytrade(_get(U_DAYTRADE.format(d=(d.get("mratio") or {}).get("date") or
                                                                                  datetime.now(TPE).strftime("%Y%m%d"))))),
                     ("sbl_otc", lambda: parse_sbl_otc(_get(U_SBL_O))),
                     ("warn", lambda: parse_warn(_get(U_WARN_L), _get(U_WARN_O)))):
        try:
            v = fn()
            if v:
                d[name] = v
                day[name] = v if name not in ("sbl", "warn") else ({"date": v["date"], "total": v["total"]} if name == "sbl" else len(v))
        except Exception as e:  # noqa: BLE001
            log.info("tw chips %s unavailable: %s", name, e)
    _apply_seed(d, day)
    if force or now - float(d.get("heavy_ts") or 0) >= HEAVY_TTL or not d.get("fc16"):     # fc15/fc16 added 11-22: fill once
        d["heavy_ts"] = now
        for name, fn in (("pledge", lambda: parse_pledge(_get(U_PLEDGE), uni or None)), ("forecast", lambda: parse_forecast(_get(U_FCST))),
                         ("fc15", lambda: _get(U_FCST)), ("fc16", lambda: _get(U_FCST2))):
            try:
                v = fn()
                if v:
                    d[name] = v
            except Exception as e:  # noqa: BLE001
                log.info("tw chips %s unavailable: %s", name, e)
        try:
            _save(SNAP, snapshot_fin(_get(U_FIN), _load(SNAP)))
        except Exception as e:  # noqa: BLE001
            log.info("tw fin snapshot unavailable: %s", e)
    for k in sorted(hist)[:-KEEP]:
        hist.pop(k)
    d["fetched"] = datetime.now(TPE).strftime("%Y-%m-%d %H:%M")
    try:
        _save(FILE, d)
    except OSError:
        pass
    return d


def series(d: Dict, key, sub=None) -> List[tuple]:
    """[(day, value)] from the daily history, e.g. series(d, "inst", ("外資及陸資", "net_oi"))."""
    out = []
    for day in sorted((d.get("hist") or {})):
        v = (d["hist"][day] or {}).get(key)
        for s in sub or ():
            v = (v or {}).get(s) if isinstance(v, dict) else None
        if isinstance(v, (int, float)):
            out.append((day, float(v)))
    return out


def write_seed(path=SEED) -> Dict:
    """PC → cloud relay for the parts the cloud cannot fetch (public exchange data)."""
    out = {"fetched": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"), "large": parse_large(_get(U_LARGE, "text")),
           "large_opt": parse_large_opt(_get(U_LARGE_OPT)), "sbl_otc": parse_sbl_otc(_get(U_SBL_O)),
           "warn": parse_warn(_get(U_WARN_L), _get(U_WARN_O)), "mratio": margin_ratio(_get(U_MARGN), _get(U_CLOSE))}
    for name, u in (("fc15", U_FCST), ("fc16", U_FCST2)):
        try:
            out[name] = _get(u)
        except Exception as e:  # noqa: BLE001
            log.info("forecast relay %s: %s", name, e)
    out["daytrade"] = parse_daytrade(_get(U_DAYTRADE.format(d=(out["mratio"] or {}).get("date") or datetime.now(TPE).strftime("%Y%m%d"))))
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


# ------------------------------------------------------------------ 單季財報（11-22，Gemini TWC-6 找到的公開資訊觀測站全市場彙總表）
U_T163 = "https://mopsov.twse.com.tw/mops/web/ajax_t163sb04"
FIN_SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_fin_seed.json"
_TAB = re.compile(r"<table class='hasBorder'[^>]*>(.*?)</table>", re.S)
_TR = re.compile(r"<tr class='(?:even|odd)'>(.*?)</tr>", re.S)
_TH = re.compile(r"<th[^>]*>(.*?)</th>", re.S)
_TDC = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
FIELDS = {"rev": ("營業收入", "收益", "淨收益"), "gross": ("營業毛利（毛損）淨額", "營業毛利（毛損）"), "op": ("營業利益（損失）",),
          "ni": ("淨利（淨損）歸屬於母公司業主", "淨利（損）歸屬於母公司業主"), "eps": ("基本每股盈餘（元）",)}


def parse_t163(page: str) -> Dict[str, Dict]:
    """MOPS 綜合損益表彙總 (one table per industry format) → {code: {name, rev, gross, op, ni, eps}} (cumulative, NT$ thousand)."""
    out: Dict[str, Dict] = {}
    for tb in _TAB.findall(page or ""):
        head = [re.sub(r"<[^>]+>|\s", "", x) for x in _TH.findall(tb)]
        idx = {}
        for k, names in FIELDS.items():
            for nm in names:
                if nm in head:
                    idx[k] = head.index(nm)
                    break
        for row in _TR.findall(tb):
            c = [re.sub(r"<[^>]+>", "", x).strip() for x in _TDC.findall(row)]
            if len(c) < 3 or not re.fullmatch(r"\d{4}[A-Z]?", c[0]):
                continue
            out[c[0]] = {"name": c[1], **{k: (_n(c[i]) if i < len(c) else None) for k, i in idx.items()}}
    return out


def fetch_quarter(year_roc: int, season: int) -> Dict[str, Dict]:
    import requests
    out: Dict[str, Dict] = {}
    for typek in ("sii", "otc"):
        for attempt in range(3):
            r = requests.post(U_T163, data={"encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "TYPEK": typek,
                                            "year": year_roc, "season": f"{season:02d}"}, headers=UA, timeout=60)
            r.encoding = "utf-8"
            got = parse_t163(r.text) if r.ok else {}
            if got:
                out.update(got)
                break
            time.sleep(3.0 * (attempt + 1))
        time.sleep(1.5)
    return out


def latest_quarters(today: Optional[date] = None, n: int = 3) -> List[tuple]:
    """The last n quarters whose filing deadline has passed (Q1 May 15, Q2 Aug 14, Q3 Nov 14, Q4 with the annual report Mar 31)."""
    today = today or date.today()
    out = []
    y, q = today.year, 4
    while len(out) < n and y > today.year - 3:
        dl = {1: date(y, 5, 15), 2: date(y, 8, 14), 3: date(y, 11, 14), 4: date(y + 1, 3, 31)}[q]
        if dl <= today:
            out.append((y - 1911, q))
        y, q = (y, q - 1) if q > 1 else (y - 1, 4)
    return out


def write_fin_seed(path=FIN_SEED) -> Dict:
    """PC → cloud relay: cumulative statements of the last three filed quarters (public filings), keys like '115Q3'."""
    snaps = {}
    for y, q in latest_quarters():
        got = fetch_quarter(y, q)
        if got:
            snaps[f"{y}Q{q}"] = got
    old = _load(Path(path))
    if old.get("snaps") and sum(len(v) for v in snaps.values()) < 0.7 * sum(len(v) for v in old["snaps"].values()):
        return old                                       # a partial fetch must not replace a good copy
    out = {"fetched": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"), "source": "公開資訊觀測站綜合損益表彙總表（累計數，千元）", "snaps": snaps}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def fin_view(snaps: Dict, codes: Optional[set] = None) -> Dict:
    """Newest single quarter per company (Qn − Qn−1 cumulative; Q1 as is), with gross / operating margin, and the same quarter a
    year earlier when available — never guessed."""
    keys = sorted(snaps, key=lambda k: (int(k.split("Q")[0]), int(k.split("Q")[1])), reverse=True)
    if not keys:
        return {}
    k0 = keys[0]
    y, q = int(k0.split("Q")[0]), int(k0.split("Q")[1])
    rows = []
    for code, cur in (snaps.get(k0) or {}).items():
        if codes is not None and code not in codes:
            continue
        sq = single_quarter(snaps, code, str(y), q) if q > 1 else dict(cur)
        if not sq or not sq.get("rev"):
            continue
        rev = sq["rev"]
        pq = (single_quarter(snaps, code, str(y), q - 1) if q > 2 else (snaps.get(f"{y}Q1") or {}).get(code)) if q > 1 else None
        m = lambda a, b: (a / b * 100) if a is not None and b else None  # noqa: E731
        # 11-22: subtracting cumulative EPS breaks when a company restates its share count (stock split / dividend: 緯穎 came out
        # at −62 元).  Single-quarter EPS = single-quarter net income ÷ the share count implied by that quarter's cumulative figures.
        def eps_of(single, cum):
            if not single or not cum or not cum.get("ni") or not cum.get("eps") or single.get("ni") is None:
                return None
            return single["ni"] * cum["eps"] / cum["ni"]

        rows.append({"code": code, "name": cur.get("name"), "rev": rev, "eps": eps_of(sq, cur), "ni": sq.get("ni"),
                     "gm": m(sq.get("gross"), rev), "om": m(sq.get("op"), rev), "eps_ytd": cur.get("eps"),
                     "rev_qoq": m(rev - pq["rev"], pq["rev"]) if pq and pq.get("rev") else None,
                     "gm_prev": m(pq.get("gross"), pq.get("rev")) if pq else None, "eps_prev": eps_of(pq, cur)})   # same (current) share basis
    return {"q": k0, "rows": sorted(rows, key=lambda r: -(r["rev"] or 0))}
