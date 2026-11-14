"""各國危機雷達：金融海嘯不一定從美國開始（1997 年泰國、1998 年俄羅斯、2018 年土耳其）。這裡看 14 個新興市場，
每一國回答兩個問題：市場現在有多怕？國家的帳本撐不撐得住？再回答第三個：是一國的事，還是正在擴散？

  市場（每天）  Yahoo Finance：貨幣對美元的 1 個月／12 個月變化、離 5 年最弱多遠；在美國掛牌的單一國家 ETF（美元計價，
                等於外國投資人實際的感受）離一年高點多遠
  帳本（慢）    外匯存底（國際貨幣基金資料，經 FRED，月）：12 個月變化
                外匯存底可以付幾個月進口、一年內到期的外債相當於存底的幾 %（世界銀行，年）
                經常帳占 GDP、政府債占 GDP、GDP 占全球多少（國際貨幣基金 WEO，含當年估計值）
亮燈用的是文獻與實務常用的門檻（下面 FLAGS），是「這幾項踩線了」，不是預測模型；本站沒有對它做回測。
新興市場匯率的日線常在幾天內來回跳 3% 以上（例如央行進場干預後又貶回去），所以變化一律用幾天的中位數算，不用單日收盤：
一個月、一年的變化用 5 天中位數，「兩週內一起貶」用最近 10 天對前 10 天。
國際貨幣基金的 API 會拒絕假裝成瀏覽器的連線，這裡用老實的程式名稱連線。世界銀行的 API 常常暫時失敗，失敗就留空、下次再試。
快取 data_cache/econ_country_risk.json（CI 保留 econ_*）。"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import statistics
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_country_risk.json"
HDR = {"User-Agent": "WallStreet-Sentinel/1.0 (research site; https://wallstreet-sentinel.pages.dev)", "Accept": "application/json"}
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=5y&interval=1d"
IMF = "https://www.imf.org/external/datamapper/api/v1/{ind}"
WB = "https://api.worldbank.org/v2/country/all/indicator/{ind}"
TTL_PX, TTL_RES, TTL_SLOW = 6 * 3600, 7 * 86400, 30 * 86400
# (ISO3, ISO2, 中文, 貨幣中文, Yahoo 匯率代號 = 1 美元換多少當地貨幣, 美國掛牌的國家 ETF)
COUNTRIES = (("IDN", "ID", "印尼", "盧比", "IDR=X", "EIDO"), ("TUR", "TR", "土耳其", "里拉", "TRY=X", "TUR"), ("ARG", "AR", "阿根廷", "披索", "ARS=X", "ARGT"),
             ("BRA", "BR", "巴西", "雷亞爾", "BRL=X", "EWZ"), ("ZAF", "ZA", "南非", "蘭特", "ZAR=X", "EZA"), ("IND", "IN", "印度", "盧比", "INR=X", "INDA"),
             ("MEX", "MX", "墨西哥", "披索", "MXN=X", "EWW"), ("KOR", "KR", "南韓", "韓元", "KRW=X", "EWY"), ("THA", "TH", "泰國", "泰銖", "THB=X", "THD"),
             ("PHL", "PH", "菲律賓", "披索", "PHP=X", "EPHE"), ("MYS", "MY", "馬來西亞", "令吉", "MYR=X", "EWM"), ("VNM", "VN", "越南", "越南盾", "VND=X", "VNM"),
             ("EGY", "EG", "埃及", "埃及鎊", "EGP=X", ""), ("CHN", "CN", "中國", "人民幣", "CNY=X", "MCHI"))
IMF_IND = (("BCA_NGDPD", "ca"), ("GGXWDG_NGDP", "debt"), ("NGDPD", "gdp"))
WB_IND = (("FI.RES.TOTL.MO", "mo"), ("DT.DOD.DSTC.IR.ZS", "st"))
PAST = (("THA", "泰國", 1997), ("IDN", "印尼", 1997), ("KOR", "南韓", 1997), ("RUS", "俄羅斯", 1998), ("TUR", "土耳其", 2018))   # 當年出事的國家，用同一份 IMF 資料算占比
# 亮燈門檻：(代號, 白話, 判斷)。常見出處：外匯存底 3 個月進口、短期外債不超過存底（Greenspan–Guidotti）、經常帳逆差 4% 以上、
# 貨幣一年貶值 15% 以上（Frankel–Rose 的貨幣危機定義是 25%，這裡取較早的警戒線）
FLAGS = (("fx_y1", "貨幣一年貶超過 15%", lambda r: r.get("fx_y1") is not None and r["fx_y1"] <= -15),
         ("weak", "貨幣在 5 年最弱附近", lambda r: r.get("weak") is not None and r["weak"] >= -2),
         ("res_y1", "外匯存底一年少超過 10%", lambda r: r.get("res_y1") is not None and r["res_y1"] <= -10),
         ("mo", "存底不夠付 3 個月進口", lambda r: r.get("mo") is not None and r["mo"] < 3),
         ("st", "一年內到期的外債比存底多", lambda r: r.get("st") is not None and r["st"] > 100),
         ("ca", "經常帳逆差超過 GDP 的 4%", lambda r: r.get("ca") is not None and r["ca"] < -4),
         ("off", "股市（美元計價）離高點超過 30%", lambda r: r.get("off") is not None and r["off"] <= -30))
RED, YELLOW = 4, 2
WEAK_M1, WEAK_N, LAG_PTS, W2_DROP, W2_N = -3.0, 5, -3.0, -2.0, 3


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


# ------------------------------------------------------------------ pure maths
def smooth(c: List[float], back: int = 0, k: int = 5) -> Optional[float]:
    """Median of k closes ending `back` days ago: one bad tick (or an alternating quote source) cannot move it."""
    end = len(c) - back
    w = [x for x in c[max(0, end - k):end] if x]
    return statistics.median(w) if len(w) >= 3 else None


def fx_stats(c: List[float]) -> Dict:
    """c = local currency per US dollar, daily.  All results are the CURRENCY's change against the dollar (negative = weaker)."""
    now = smooth(c)
    if not now or len(c) < 300:
        return {}
    val = lambda old: (old / now - 1) * 100 if old else None  # noqa: E731
    top = max(x for x in (smooth(c, b) for b in range(0, len(c) - 5, 5)) if x)        # its weakest in the window (most local per dollar)
    # weak: 0 = at its weakest of the window; −10 = the dollar costs 10 % less of it than at the weakest
    a, b = smooth(c, 0, 10), smooth(c, 10, 10)                 # the last two weeks against the two before: steadier than any single week
    return {"rate": c[-1], "fx_w2": (b / a - 1) * 100 if a and b else None, "fx_m1": val(smooth(c, 21)), "fx_y1": val(smooth(c, 252)),
            "weak": (now / top - 1) * 100 if top else None}


def etf_stats(c: List[float]) -> Dict:
    c = [x for x in c if x]
    if len(c) < 260:
        return {}
    return {"off": (c[-1] / max(c[-252:]) - 1) * 100, "etf_m1": (c[-1] / c[-22] - 1) * 100}


def res_stats(m: Dict[str, float]) -> Dict:
    ks = sorted(m or {})
    if len(ks) < 13:
        return {}
    return {"res": m[ks[-1]], "res_month": ks[-1], "res_y1": (m[ks[-1]] / m[ks[-13]] - 1) * 100 if m[ks[-13]] else None}


def year_val(series: Dict, year: int) -> Optional[float]:
    """This year's figure (an IMF estimate), else last year's."""
    for y in (year, year - 1):
        v = (series or {}).get(str(y))
        if isinstance(v, (int, float)):
            return float(v)
    return None


def flags_of(r: Dict) -> List[str]:
    return [zh for _k, zh, f in FLAGS if f(r)]


def light(n: int) -> int:
    return 2 if n >= RED else 1 if n >= YELLOW else 0


def spreading(rows: List[Dict], emb3: Optional[float], ief3: Optional[float]) -> Dict:
    """One country or many?  red count, how many currencies lost > 3 % in a month, and EM dollar bonds against US Treasuries."""
    red = [r["zh"] for r in rows if r["light"] == 2]
    weak = [r["zh"] for r in rows if r.get("fx_m1") is not None and r["fx_m1"] <= WEAK_M1]
    lag = emb3 - ief3 if emb3 is not None and ief3 is not None else None
    state = ("spread" if len(red) >= 3 or len(weak) >= WEAK_N or (lag is not None and lag <= LAG_PTS)
             else "local" if red or any(r["light"] == 1 for r in rows) else "calm")
    return {"red": red, "weak": weak, "emb3": emb3, "ief3": ief3, "lag": lag, "state": state}


def week_drop(rows: List[Dict]) -> List[Dict]:
    return [r for r in rows if r.get("fx_w2") is not None and r["fx_w2"] <= W2_DROP]


def alerts(rows: List[Dict], sp: Dict, day: str) -> List[Dict]:
    """What is worth a Discord message, each with a key that stays the same for the month (a red light, a joint slide, spreading)."""
    out = []
    month = day[:7]
    for r in rows:
        if r["light"] == 2:
            out.append({"key": f'cr:red:{r["iso3"]}:{month}', "lv": 2, "title": f'各國危機雷達：{r["zh"]}亮紅燈（{len(r["flags"])} 項踩線）',
                        "text": f'{r["zh"]}踩線的項目：' + "、".join(r["flags"]) + "。"})
    wk = week_drop(rows)
    if len(wk) >= W2_N:
        # one message a month: replayed on 5 years of prices this fires in 22 months (8 of them in 2022, the dollar's strongest year)
        out.append({"key": f"cr:fx:{month}", "lv": 2 if len(wk) >= 5 else 1, "title": f"新興市場貨幣同時走弱：{len(wk)} 國兩週內貶超過 {abs(W2_DROP):g}%",
                    "text": "、".join(f'{r["zh"]}{r["cur"]} {r["fx_w2"]:+.1f}%' for r in sorted(wk, key=lambda r: r["fx_w2"])) + "。好幾國同時貶，通常是資金一起撤出新興市場，不是哪一國自己的事。"})
    if sp["state"] == "spread":
        why = ([f'{len(sp["red"])} 國紅燈'] if len(sp["red"]) >= 3 else []) + ([f'{len(sp["weak"])} 國貨幣一個月貶超過 3%'] if len(sp["weak"]) >= WEAK_N else []) \
            + ([f'新興市場美元債三個月比美國公債多跌 {abs(sp["lag"]):.1f} 個百分點'] if sp["lag"] is not None and sp["lag"] <= LAG_PTS else [])
        out.append({"key": f"cr:spread:{month}", "lv": 2, "title": "各國危機雷達：壓力正在擴散", "text": "、".join(why) + "。"})
    return out


# ------------------------------------------------------------------ fetch
def parse_yahoo(js: Dict) -> Dict[str, list]:
    r = js["chart"]["result"][0]
    t, c = r["timestamp"], r["indicators"]["quote"][0]["close"]
    pts = [(datetime.fromtimestamp(a, timezone.utc).strftime("%Y-%m-%d"), round(float(b), 6)) for a, b in zip(t, c) if b]
    return {"d": [p[0] for p in pts], "c": [p[1] for p in pts]}


def parse_imf(js: Dict, ind: str, want: List[str]) -> Dict[str, Dict[str, float]]:
    v = (js.get("values") or {}).get(ind) or {}
    return {c: {y: x for y, x in (v.get(c) or {}).items() if isinstance(x, (int, float))} for c in want if v.get(c)}


def parse_wb(js, want: List[str]) -> Dict[str, list]:
    rows = js[1] if isinstance(js, list) and len(js) > 1 and js[1] else []
    return {r["countryiso3code"]: [str(r["date"]), float(r["value"])] for r in rows if r.get("countryiso3code") in want and r.get("value") is not None}


async def _prices(syms: List[str]) -> Dict[str, Dict]:
    sem = asyncio.Semaphore(4)

    async def one(s: str):
        async with sem:
            try:
                return s, parse_yahoo(await http.get(YAHOO.format(s=s), timeout=30, retries=1))
            except Exception as e:  # noqa: BLE001
                log.info("country px %s: %s", s, e if str(e) else type(e).__name__)
                return s, None
    return {s: v for s, v in await asyncio.gather(*(one(s) for s in syms)) if v and len(v["c"]) >= 260}


async def refresh(force: bool = False) -> Dict:
    from .euro_asia import _fred
    from .freshness import due
    d = load()
    now = time.time()
    d["ts_check"] = now
    each = d.setdefault("ts_each", {})
    d.setdefault("try_each", {})
    bad = []
    iso3 = [c[0] for c in COUNTRIES]
    if due(d, ["px"], TTL_PX, now, force):
        d["try_each"]["px"] = now
        syms = [c[4] for c in COUNTRIES] + [c[5] for c in COUNTRIES if c[5]]
        got = await _prices(syms)
        if len(got) >= len(syms) * 0.7:
            d["px"], each["px"] = {**(d.get("px") or {}), **got}, now
        else:
            bad.append(f"prices: only {len(got)}/{len(syms)}")
        _save(d)                                             # a build timeout later keeps what is already here
    if due(d, ["res"], TTL_RES, now, force):
        d["try_each"]["res"] = now
        res = dict(d.get("res") or {})
        n = 0
        for c in COUNTRIES:
            try:
                v = await _fred(f"TRESEG{c[1]}M052N")
                if v:
                    res[c[0]] = dict(sorted(v.items())[-36:])
                    n += 1
            except Exception as e:  # noqa: BLE001
                log.info("country reserves %s: %s", c[0], e if str(e) else type(e).__name__)
            await asyncio.sleep(0.6)
        if n >= 8:
            d["res"], each["res"] = res, now
        else:
            bad.append(f"reserves: only {n}/{len(COUNTRIES)}")
        _save(d)
    for ind, key in IMF_IND:
        k = "imf_" + key
        if not due(d, [k], TTL_SLOW, now, force):
            continue
        d["try_each"][k] = now
        try:
            v = parse_imf(await http.get(IMF.format(ind=ind), headers=HDR, timeout=60, retries=1), ind, iso3 + ["WEOWORLD"] + [p[0] for p in PAST])
            if len(v) < 8:
                raise ValueError(f"only {len(v)} countries")
            d[k], each[k] = v, now
        except Exception as e:  # noqa: BLE001
            bad.append(f"imf {ind}: {e if str(e) else type(e).__name__}")
    for ind, key in WB_IND:
        k = "wb_" + key
        if not due(d, [k], TTL_SLOW, now, force):
            continue
        d["try_each"][k] = now
        try:
            v = parse_wb(await http.get(WB.format(ind=ind), headers=HDR, params={"format": "json", "mrnev": 1, "per_page": 400}, timeout=45, retries=0), iso3)
            if len(v) < 6:
                raise ValueError(f"only {len(v)} countries")
            d[k], each[k] = v, now
        except Exception as e:  # noqa: BLE001
            bad.append(f"world bank {ind}: {e if str(e) else type(e).__name__}")
    if bad:
        log.warning("country risk data: %s", "; ".join(bad))
        HEALTH.fail("country_risk", "; ".join(bad), every=TTL_PX)
    else:
        HEALTH.ok("country_risk", len(d.get("px") or {}), every=TTL_PX)
    _save(d)
    return d


def _save(d: Dict) -> None:
    d["ts"] = float((d.get("ts_each") or {}).get("px") or 0)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)


# ------------------------------------------------------------------ view
def build_rows(d: Dict, year: int) -> List[Dict]:
    px, res = d.get("px") or {}, d.get("res") or {}
    world = year_val((d.get("imf_gdp") or {}).get("WEOWORLD") or {}, year)
    rows = []
    for iso3, _iso2, zh, cur, fx, etf in COUNTRIES:
        r: Dict = {"iso3": iso3, "zh": zh, "cur": cur, "fx": fx, "etf": etf}
        r.update(fx_stats((px.get(fx) or {}).get("c") or []))
        r.update(etf_stats((px.get(etf) or {}).get("c") or []) if etf else {})
        r.update(res_stats(res.get(iso3) or {}))
        r["ca"] = year_val((d.get("imf_ca") or {}).get(iso3) or {}, year)
        r["debt"] = year_val((d.get("imf_debt") or {}).get(iso3) or {}, year)
        g = year_val((d.get("imf_gdp") or {}).get(iso3) or {}, year)
        r["share"] = g / world * 100 if g and world else None
        for key in ("mo", "st"):
            w = (d.get("wb_" + key) or {}).get(iso3)
            r[key], r[key + "_year"] = (w[1], w[0]) if w else (None, None)
        if r.get("rate") is None:
            continue                                          # no market price: nothing to say about the country today
        r["flags"] = flags_of(r)
        r["light"] = light(len(r["flags"]))
        rows.append(r)
    return sorted(rows, key=lambda r: (-len(r["flags"]), r.get("fx_y1") or 0))


def past_shares(d: Dict) -> List[Dict]:
    g = d.get("imf_gdp") or {}
    out = []
    for iso3, zh, y in PAST:
        a, w = (g.get(iso3) or {}).get(str(y)), (g.get("WEOWORLD") or {}).get(str(y))
        if a and w:
            out.append({"zh": zh, "year": y, "share": a / w * 100})
    return out


def _ret3(eng, sym: str) -> Optional[float]:
    try:
        s = eng.market.series(sym).dropna()
        return float(s.iloc[-1] / s.iloc[-64] - 1) * 100 if len(s) > 70 else None
    except Exception:  # noqa: BLE001
        return None


def view(eng=None, d: Optional[Dict] = None, today: Optional[str] = None) -> Dict:
    d = d if d is not None else load()
    px = d.get("px") or {}
    last = max((v["d"][-1] for v in px.values() if v.get("d")), default="")
    today = today or last or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = build_rows(d, int(today[:4]))
    if not rows:
        return {}
    sp = spreading(rows, _ret3(eng, "EMB") if eng is not None else None, _ret3(eng, "IEF") if eng is not None else None)
    miss = [zh for key, zh in (("res", "外匯存底"), ("imf_ca", "經常帳"), ("wb_mo", "存底可付幾個月進口"), ("wb_st", "短期外債對存底")) if not d.get(key)]
    return {"rows": rows, "spread": sp, "past": past_shares(d), "asof": last, "missing": miss, "alerts": alerts(rows, sp, today),
            "ts_check": d.get("ts_check"), "week_drop": [r["zh"] for r in week_drop(rows)]}


def public(v: Dict) -> Dict:
    """country_risk.json: the lights, the reasons and the alert list, for the push program and the voice editions."""
    keep = ("iso3", "zh", "cur", "light", "flags", "rate", "fx_w2", "fx_m1", "fx_y1", "weak", "off", "res_y1", "res_month", "mo", "st", "ca", "share")
    return {"ts": int(v.get("ts_check") or 0), "asof": v.get("asof"), "spread": v.get("spread"), "alerts": v.get("alerts") or [],
            "rows": [{k: (round(r[k], 2) if isinstance(r.get(k), float) else r.get(k)) for k in keep} for r in v.get("rows") or []]}
