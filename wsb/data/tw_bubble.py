"""台股泡沫觀察：證交所免費公開資料，每項都和「自己的歷史」比，不用寫死的門檻。

  * 每日成交金額與加權指數（FMTQIK，每月一檔）：成交熱度（20 日平均成交金額）、指數離 200 日均線多遠。
  * 當日沖銷占成交金額比重（TWTB4U）：短線投機的熱度。
  * 融資餘額（MI_MARGN 信用交易統計，仟元）：借錢買股的規模。
  * 全體上市股票本益比、淨值比中位數與台積電本益比（BWIBBU_d，每月最後一個交易日）：估值。
歷史一次抓不完（證交所連太快會擋），每次建置最多抓 BUDGET 筆、由新到舊補，幾個小時內補齊：
指數與成交 5 年、當沖與融資每週一筆 3 年、估值每月一筆 5 年。
燈號：和自己過去的平均差幾個標準差（z）：z ≥ 2 紅、z ≥ 1 黃，其餘綠；歷史不足 24 筆不亮燈。
每月記一次亮燈數，用來檢查「台股 2027 下半年泡沫破裂」這個假設是否越來越像真的。描述現況，不是預測。
快取 data_cache/econ_tw_bubble.json（CI 保留 econ_*）。"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import time
from datetime import date, datetime, timedelta
from statistics import median
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_bubble.json"
UA = {"User-Agent": "Mozilla/5.0"}
BASE = "https://www.twse.com.tw/rwd/zh"
U_FM = BASE + "/afterTrading/FMTQIK?date={d}&response=json"
U_DT = BASE + "/dayTrading/TWTB4U?date={d}&response=json"
U_MG = BASE + "/marginTrading/MI_MARGN?date={d}&selectType=MS&response=json"
U_VAL = BASE + "/afterTrading/BWIBBU_d?date={d}&selectType=ALL&response=json"
PAGE = {"fm": "https://www.twse.com.tw/zh/trading/historical/fmtqik.html",
        "dt": "https://www.twse.com.tw/zh/trading/day-trading/twtb4u.html",
        "mg": "https://www.twse.com.tw/zh/trading/margin/mi-margn.html",
        "val": "https://www.twse.com.tw/zh/trading/historical/bwibbu-day.html"}
YEARS_FM, YEARS_WK, YEARS_VAL = 10, 3, 10
BUDGET = 18                 # requests per build
PAUSE = 2.2                 # seconds between requests (TWSE blocks bursts)
FRESH = 6 * 3600            # current month / latest date re-checked every 6 h
MIN_HIST = 24
RED, YELLOW = 2.0, 1.0


SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_bubble_seed.json"   # PC-fetched history (public repo)


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        d = {}
    try:                                    # a fresh CI cache starts from the seed instead of hours of backfill
        s = json.loads(SEED.read_text(encoding="utf-8")) if SEED.exists() else {}
        for k in ("fm", "dt", "mg", "val", "us10"):
            for kk, vv in (s.get(k) or {}).items():
                d.setdefault(k, {}).setdefault(kk, vv)
        for kk, vv in (s.get("fm_ts") or {}).items():
            d.setdefault("fm_ts", {}).setdefault(kk, vv)
    except Exception:  # noqa: BLE001
        pass
    return d


def seed(d: Dict) -> Dict:
    """What the PC writes to research_feed/tw_bubble_seed.json: official history only (no score, no ts)."""
    return {k: d.get(k) or {} for k in ("fm", "fm_ts", "dt", "mg", "val", "us10")}


def _f(x) -> Optional[float]:
    try:
        v = float(str(x).replace(",", "").replace("%", "").strip())
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _roc_date(s: str) -> Optional[str]:
    try:
        y, m, d = str(s).split("/")
        return f"{int(y) + 1911:04d}-{int(m):02d}-{int(d):02d}"
    except (TypeError, ValueError):
        return None


# ---- parsers (pure; tested) ----
def parse_fm(js: Dict) -> List[List]:
    """FMTQIK month → [[YYYY-MM-DD, 成交金額(億元), 加權指數], ...]."""
    if not isinstance(js, dict) or js.get("stat") != "OK":
        return []
    out = []
    for r in js.get("data") or []:
        d, v, ix = _roc_date(r[0]), _f(r[2]), _f(r[4]) if len(r) > 4 else None
        if d and v is not None and ix is not None:
            out.append([d, round(v / 1e8, 1), ix])
    return out


def parse_dt(js: Dict) -> Optional[float]:
    """TWTB4U → 當沖買進成交金額占市場比重 (%)."""
    if not isinstance(js, dict) or js.get("stat") != "OK":
        return None
    for t in js.get("tables") or []:
        f = t.get("fields") or []
        for i, name in enumerate(f):
            if "買進成交金額占市場比重" in name and t.get("data"):
                return _f(t["data"][0][i])
    return None


def parse_mg(js: Dict) -> Optional[float]:
    """MI_MARGN (MS) → 融資金額今日餘額 (億元)."""
    if not isinstance(js, dict) or js.get("stat") != "OK":
        return None
    for t in js.get("tables") or []:
        f = t.get("fields") or []
        if "今日餘額" not in f:
            continue
        j = f.index("今日餘額")
        for r in t.get("data") or []:
            if str(r[0]).startswith("融資金額"):
                v = _f(r[j])
                return round(v / 1e5, 1) if v is not None else None
    return None


def parse_val(js: Dict) -> Optional[Dict]:
    """BWIBBU_d (ALL) → medians over listed stocks + TSMC (2330)."""
    if not isinstance(js, dict) or js.get("stat") != "OK":
        return None
    f = js.get("fields") or []
    try:
        ic, ipe, ipb, idy = f.index("證券代號"), f.index("本益比"), f.index("股價淨值比"), f.index("殖利率(%)")
    except ValueError:
        return None
    pes, pbs, dys, tsmc = [], [], [], {}
    for r in js.get("data") or []:
        code = str(r[ic]).strip()
        if not (code.isdigit() and len(code) == 4):        # common stocks only (ETFs / TDRs carry no P/E)
            continue
        pe, pb, dy = _f(r[ipe]), _f(r[ipb]), _f(r[idy])
        if pe and pe > 0:
            pes.append(pe)
        if pb and pb > 0:
            pbs.append(pb)
        if dy is not None:
            dys.append(dy)
        if code == "2330":
            tsmc = {"pe": pe, "pb": pb}
    if len(pes) < 300:
        return None
    return {"pe_med": round(median(pes), 2), "pb_med": round(median(pbs), 2) if pbs else None,
            "dy_med": round(median(dys), 2) if dys else None, "pe30": round(sum(p > 30 for p in pes) / len(pes) * 100, 1),
            "n": len(pes), "tsmc_pe": tsmc.get("pe"), "tsmc_pb": tsmc.get("pb")}


# ---- sampling ----
def months_back(today: date, years: int) -> List[str]:
    out, y, m = [], today.year, today.month
    for _ in range(years * 12 + 1):
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out                                             # newest first


def trading_days(d: Dict) -> List[str]:
    return sorted({r[0] for rows in (d.get("fm") or {}).values() for r in rows})


def weekly(days: List[str], years: int, today: date) -> List[str]:
    """Last trading day of each ISO week within `years`, newest first (always includes the latest day)."""
    start = (today - timedelta(days=365 * years)).isoformat()
    last: Dict[Tuple[int, int], str] = {}
    for s in days:
        if s >= start:
            k = date.fromisoformat(s).isocalendar()[:2]
            last[k] = max(last.get(k, s), s)
    return sorted(last.values(), reverse=True)


def monthly(days: List[str], years: int, today: date) -> List[str]:
    start = (today - timedelta(days=365 * years)).isoformat()
    last: Dict[str, str] = {}
    for s in days:
        if s >= start:
            last[s[:7]] = max(last.get(s[:7], s), s)
    return sorted(last.values(), reverse=True)


def plan(d: Dict, today: date, now: float) -> List[Tuple[str, str]]:
    """What to fetch this run, most useful first: [(kind, key)], kind in fm/dt/mg/val."""
    todo: List[Tuple[str, str]] = []
    fm, fts = d.get("fm") or {}, d.get("fm_ts") or {}
    for ym in months_back(today, YEARS_FM):
        ts = float(fts.get(ym, 0))
        got_then = datetime.utcfromtimestamp(ts + 8 * 3600).strftime("%Y-%m") if ts else ""
        partial = got_then == ym                            # fetched while that month was still running
        if ym not in fm or (partial and now - ts > FRESH):
            todo.append(("fm", ym))
    days = trading_days(d)
    if not days:
        return todo
    tried = d.get("tried") or {}
    def want(kind, keys):                                   # noqa: E306
        have = d.get(kind) or {}
        for k in keys:
            if k not in have and now - float(tried.get(f"{kind}:{k}", 0)) > 3600:
                todo.append((kind, k))
    wk, mo = weekly(days, YEARS_WK, today), monthly(days, YEARS_VAL, today)
    latest = days[-1]
    for kind in ("dt", "mg", "val"):                        # the newest day first, so the card is current
        want(kind, [latest])
    want("dt", wk)
    want("mg", wk)
    want("val", mo)
    seen, out = set(), []
    for t in todo:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


async def _get(url: str):
    return await http.get(url, kind="json", headers=UA, timeout=30, retries=1)


U_US10 = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS10"   # monthly US 10-year yield (台股進場環境 backtest)


def parse_us10(txt: str) -> Dict[str, float]:
    out = {}
    for line in str(txt or "").splitlines()[1:]:
        p = line.split(",")
        if len(p) == 2 and _f(p[1]) is not None:
            out[p[0][:7]] = _f(p[1])
    return out


async def refresh(budget: int = BUDGET) -> Dict:
    d = load()
    now = time.time()
    d["ts_check"] = now
    today = datetime.utcfromtimestamp(now + 8 * 3600).date()           # Taipei date
    todo = plan(d, today, now)[:budget]
    got, bad = 0, []
    if now - float((d.get("ts_us10") or 0)) > 86400:
        try:
            from .fred import _one as fred_one                      # same fetcher as the rest of the site (API key if set)
            try:
                s = await fred_one("GS10", "1960-01-01")
                us = {i.strftime("%Y-%m"): round(float(v), 3) for i, v in s.items()}
            except Exception:  # noqa: BLE001                        # API busy / no key: the public CSV
                us = parse_us10(await http.get(U_US10, kind="text", headers=UA, timeout=90, retries=1))
            if len(us) > 600:
                d["us10"], d["ts_us10"] = us, now
            else:
                d["ts_us10"] = now - 86400 + 3 * 3600               # retry in 3 h, not every build
        except Exception as e:  # noqa: BLE001
            from .fred import _redact                               # aiohttp errors carry the URL (and the API key)
            d["ts_us10"] = now - 86400 + 3 * 3600
            bad.append("us10: " + _redact(str(e) or type(e).__name__))
    for i, (kind, key) in enumerate(todo):
        if i:
            await asyncio.sleep(PAUSE)
        try:
            if kind == "fm":
                rows = parse_fm(await _get(U_FM.format(d=key.replace("-", "") + "01")))
                if rows or key != today.strftime("%Y-%m"):
                    d.setdefault("fm", {})[key] = rows
                d.setdefault("fm_ts", {})[key] = now
            else:
                d.setdefault("tried", {})[f"{kind}:{key}"] = now
                url = {"dt": U_DT, "mg": U_MG, "val": U_VAL}[kind].format(d=key.replace("-", ""))
                v = {"dt": parse_dt, "mg": parse_mg, "val": parse_val}[kind](await _get(url))
                if v is None:
                    raise ValueError("empty or new layout")
                d.setdefault(kind, {})[key] = v
            got += 1
        except Exception as e:  # noqa: BLE001
            bad.append(f"{kind} {key}: {e if str(e) else type(e).__name__}")
    if got:
        d["ts"] = now
    v = view_from(d, now)                                   # monthly record of how many lights are hot
    if v.get("scored"):
        sc = d.setdefault("score", {})
        sc[today.strftime("%Y-%m")] = {"hot": v["hot_n"], "red": v["red_n"], "of": v["scored"], "date": today.isoformat()}
    if bad:
        log.warning("TW bubble data: %s", "; ".join(bad[:5]))
        if not got:
            HEALTH.fail("tw_bubble", "; ".join(bad[:3]), every=3 * 3600)
    elif got:
        HEALTH.ok("tw_bubble", got, every=3 * 3600)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


# ---- view ----
def zscore(hist: List[float], x: float) -> Optional[float]:
    h = [v for v in hist if v is not None and math.isfinite(v)]
    if len(h) < MIN_HIST:
        return None
    m = sum(h) / len(h)
    sd = (sum((v - m) ** 2 for v in h) / (len(h) - 1)) ** 0.5
    return (x - m) / sd if sd > 0 else None


def light(z: Optional[float]) -> str:
    if z is None:
        return "⚪"
    return "🔴" if z >= RED else "🟡" if z >= YELLOW else "🟢"


def _ind(key, name, unit, ser: List[Tuple[str, float]], why: str, src: str, dg=1, note="") -> Optional[Dict]:
    ser = [(k, v) for k, v in ser if v is not None]
    if not ser:
        return None
    ser.sort()
    date_, now_v = ser[-1]
    hist = [v for _, v in ser[:-1]]
    z = zscore(hist, now_v)
    pct = round(sum(h < now_v for h in hist) / len(hist) * 100) if len(hist) >= MIN_HIST else None
    return {"key": key, "name": name, "unit": unit, "now": now_v, "date": date_, "z": None if z is None else round(z, 2),
            "pct": pct, "n": len(ser), "since": ser[0][0], "light": light(z), "why": why, "src": src, "dg": dg, "note": note,
            "max": max(v for _, v in ser), "max_date": max(ser, key=lambda t: t[1])[0], "hist": ser[-60:]}


def view_from(d: Dict, now: Optional[float] = None) -> Dict:
    rows = sorted({tuple(r) for m in (d.get("fm") or {}).values() for r in m})
    inds: List[Dict] = []
    peak = None
    if rows:                                                # what already happened: high of the last 3 years and the fall since
        cut3 = (date.fromisoformat(rows[-1][0]) - timedelta(days=365 * 3)).isoformat()
        r3 = [r for r in rows if r[0] >= cut3]
        hi = max(r3, key=lambda r: r[2])
        peak = {"date": hi[0], "high": hi[2], "now": rows[-1][2], "now_date": rows[-1][0], "dd": round((rows[-1][2] / hi[2] - 1) * 100, 1),
                "days": (date.fromisoformat(rows[-1][0]) - date.fromisoformat(hi[0])).days}
    if len(rows) >= 220:
        dates = [r[0] for r in rows]
        ix = [r[2] for r in rows]
        tv = [r[1] for r in rows]
        ext, t20 = [], []
        for i in range(len(rows)):
            if i >= 199:
                ma = sum(ix[i - 199:i + 1]) / 200
                ext.append((dates[i], round((ix[i] / ma - 1) * 100, 2)))
            if i >= 19:
                t20.append((dates[i], round(sum(tv[i - 19:i + 1]) / 20, 0)))
        cut = (date.fromisoformat(dates[-1]) - timedelta(days=365 * 3)).isoformat()
        inds.append(_ind("ext", "加權指數離 200 日均線", "%", [x for x in ext if x[0] >= cut],
                         "漲得離長期平均越遠，越容易出現急跌回補；歷次大頂前常常拉得很開。", PAGE["fm"]))
        inds.append(_ind("turn", "成交熱度（20 日平均成交金額）", "億元", [x for x in t20 if x[0] >= cut],
                         "大家搶著交易時成交金額會暴增；成交金額本身也會隨市值長大，所以看的是相對自己近 3 年的位置。", PAGE["fm"], dg=0))
    dt = d.get("dt") or {}
    inds.append(_ind("dt", "當沖占成交金額比重", "%", list(dt.items()),
                     "當天買、當天賣的短線交易占比；越高代表市場越像賭場。", PAGE["dt"]))
    mg = d.get("mg") or {}
    inds.append(_ind("mg", "上市融資餘額", "億元", list(mg.items()),
                     "借錢買股的總額；破裂時最先被迫賣的就是這些錢。數字會隨市場變大而長大，要和成交熱度一起看。", PAGE["mg"], dg=0))
    val = d.get("val") or {}
    inds.append(_ind("pe", "上市股票本益比中位數", "倍", [(k, v.get("pe_med")) for k, v in val.items()],
                     "一般股票貴不貴：中位數不受台積電這種大型股影響。", PAGE["val"]))
    inds.append(_ind("pb", "上市股票淨值比中位數", "倍", [(k, v.get("pb_med")) for k, v in val.items()],
                     "股價是公司帳面淨值的幾倍；虧錢的公司沒有本益比，但有淨值比。", PAGE["val"], dg=2))
    inds.append(_ind("tsmc", "台積電本益比", "倍", [(k, v.get("tsmc_pe")) for k, v in val.items()],
                     "台股的重心；台積電貴不貴，大致決定加權指數貴不貴。", PAGE["val"]))
    inds = [x for x in inds if x]
    scored = [x for x in inds if x["z"] is not None]
    hot = [x for x in scored if x["z"] >= YELLOW]
    red = [x for x in scored if x["z"] >= RED]
    latest_val = val[max(val)] if val else {}
    return {"inds": inds, "scored": len(scored), "hot_n": len(hot), "red_n": len(red), "hot": [x["name"] for x in hot],
            "red": [x["name"] for x in red], "score": d.get("score") or {}, "ts": d.get("ts"), "val_now": latest_val,
            "pending": [x["name"] for x in inds if x["z"] is None], "peak": peak}


def view(eng=None) -> Dict:
    return view_from(load())


def stamp() -> Tuple[Optional[float], Optional[str]]:
    d = load()
    days = trading_days(d)
    return d.get("ts"), (days[-1] if days else None)
