"""台股專業判讀（2026-11-21）：交易台會看的四種資料，用公開免費的官方來源做。

1 被迫進出的錢日曆（flows）
  * 證交所 OpenAPI 除權除息預告表 TWT48U_ALL：台灣 50＋中型 100 的除權息日與現金股利。
  * 證交所 OpenAPI 處置有價證券 announcement/punish（上市；上櫃另抓櫃買 OpenAPI）：處置股與期間。
  * 指數與 ETF 調整日：依各指數公司公布的編製規則推算（MSCI 季度審查、台灣 50、高股息）。MSCI 網站有機器人驗證，
    本站不繞過；已公告的成分股增刪改由 Gemini 每週到官方公告頁核對後寫進 research_feed/tw_flow_seed.json（附抓取時間）。
  * ETF 規模：投信每日公布的淨值 × 受益權單位數（wsb/data/tw_etf.py 已抓），用來估「每換 1% 成分要成交多少錢」。
  * 法定期限：月營收每月 10 日前；季報第 1～3 季在季底後 45 天內、年報在年底後 3 個月內（證券交易法第 36 條）。
  * 投信季底作帳：每季最後 10 個交易日（市場慣例，不是法規），標明是慣例。
2 估值區間（valuation）、3 月營收與 AI 供應鏈（earnings）：見下方各段。
所有日期由規則或官方資料算出，不寫死；推算的會標「規則推算」，估算的會標「估算」。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import date, timedelta
from typing import Callable, Dict, List, Optional

from ..config import DATA_DIR
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_twdesk.json"                 # econ_* is kept between CI builds
TTL = 6 * 3600
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
U_EXDIV = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
U_PUNISH = "https://openapi.twse.com.tw/v1/announcement/punish"
U_PUNISH_O = "https://www.tpex.org.tw/openapi/v1/tpex_disposal_information"
UNIV_TTL = 7 * 86400
VH_BUDGET = 45                                        # seconds per build for the valuation-history backfill (TWSE limits bursts)


# ============================================================ helpers
def roc(s) -> Optional[str]:
    """'1151202' / '115/12/02' → '2026-12-02'."""
    t = re.sub(r"\D", "", str(s or ""))
    if len(t) == 7:
        y, m, d = int(t[:3]) + 1911, int(t[3:5]), int(t[5:7])
    elif len(t) == 6:
        y, m, d = int(t[:2]) + 1911, int(t[2:4]), int(t[4:6])
    else:
        return None
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return None


def _num(x) -> Optional[float]:
    try:
        v = float(str(x).replace(",", "").strip())
        return v
    except (TypeError, ValueError):
        return None


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("tw desk cache unreadable: %s", e)
        return {}


def save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, FILE)


# ============================================================ 1 flows: parsers
def parse_exdiv(rows: List[Dict], univ: Optional[set] = None) -> List[Dict]:
    out = []
    for r in rows or []:
        code = str(r.get("Code") or "").strip()
        d = roc(r.get("Date"))
        if not code or not d or (univ is not None and code not in univ):
            continue
        out.append({"date": d, "code": code, "name": str(r.get("Name") or "").strip(), "kind": str(r.get("Exdividend") or "").strip(),
                    "cash": _num(r.get("CashDividend")), "stock": _num(r.get("StockDividendRatio"))})
    return sorted(out, key=lambda x: (x["date"], x["code"]))


_PERIOD = re.compile(r"(\d{2,3})[/.](\d{1,2})[/.](\d{1,2})\D+(\d{2,3})[/.](\d{1,2})[/.](\d{1,2})")


def _period(s: str):
    m = _PERIOD.search(str(s or ""))
    if not m:
        c = re.findall(r"(?<!\d)(\d{7})(?!\d)", str(s or ""))           # TPEx: '1151123~1151127'
        return (roc(c[0]), roc(c[1])) if len(c) >= 2 else (None, None)
    a = roc(f"{int(m.group(1)):03d}{int(m.group(2)):02d}{int(m.group(3)):02d}")
    b = roc(f"{int(m.group(4)):03d}{int(m.group(5)):02d}{int(m.group(6)):02d}")
    return a, b


def parse_punish(rows: List[Dict], board: str = "上市") -> List[Dict]:
    """Disposal list → stocks only (4-digit codes; warrants and ETFs dropped), with the period parsed."""
    out = []
    for r in rows or []:
        code = str(r.get("Code") or r.get("SecuritiesCompanyCode") or "").strip()
        if not re.fullmatch(r"[1-9]\d{3}", code):
            continue
        a, b = _period(r.get("DispositionPeriod") or r.get("DispositionPeriodTime") or "")
        if not a:
            continue
        out.append({"code": code, "name": str(r.get("Name") or r.get("CompanyName") or "").strip(), "from": a, "to": b, "board": board,
                    "why": str(r.get("ReasonsOfDisposition") or r.get("DispositionReasons") or "").strip()[:30],
                    "step": str(r.get("DispositionMeasures") or "").strip()[:12]})
    return sorted(out, key=lambda x: (x["to"] or "", x["code"]))


# ============================================================ 1 flows: rule-derived dates
def deadlines(today: date, n_months: int = 3) -> List[Dict]:
    """Statutory filing deadlines ahead (證券交易法第 36 條; monthly revenue by the 10th)."""
    out = []
    y, m = today.year, today.month
    for k in range(n_months + 1):
        mm = (m - 1 + k) % 12 + 1
        yy = y + (m - 1 + k) // 12
        d = date(yy, mm, 10)
        if d >= today:
            prev = (mm - 2) % 12 + 1
            out.append({"date": d.isoformat(), "what": f"{prev} 月營收公布期限", "kind": "rev",
                        "why": "上市櫃公司每月 10 日前要公布上個月營收；營收年增突然轉弱或轉強，常是法人調整持股的第一個訊號。"})
    for yy in (today.year, today.year + 1):
        for d, what in ((date(yy, 3, 31), f"{yy - 1} 年年報"), (date(yy, 5, 15), f"{yy} 年第 1 季季報"),
                        (date(yy, 8, 14), f"{yy} 年第 2 季季報"), (date(yy, 11, 14), f"{yy} 年第 3 季季報")):
            if today <= d <= today + timedelta(days=200):
                out.append({"date": d.isoformat(), "what": what + "公布期限", "kind": "fin",
                            "why": "季報（含毛利率、存貨、合約負債）比月營收晚、但更完整；遇假日順延。"})
    return out


def quarter_window(today: date, tw_open: Callable[[date], bool], n: int = 10) -> Dict:
    """The last n Taiwan trading days of the current quarter (投信季底作帳 — a market convention, not a rule)."""
    qm = ((today.month - 1) // 3 + 1) * 3
    end = date(today.year + (qm == 12), qm % 12 + 1, 1) - timedelta(days=1)
    days, d = [], end
    while len(days) < n:
        if tw_open(d):
            days.append(d)
        d -= timedelta(days=1)
    return {"from": days[-1].isoformat(), "to": days[0].isoformat()}


# ETF review months come from each index provider's published methodology. Dates the rule fixes are computed;
# where the provider announces the effective day each time, only the month is shown ("以公告為準").
ETF_RULES = [
    {"code": "0050", "index": "臺灣 50 指數（FTSE／證交所）", "months": (3, 6, 9, 12), "rule": "3rd_fri",
     "src": "https://www.taiwanindex.com.tw/indexes/t00"},
    {"code": "0056", "index": "臺灣高股息指數（FTSE／證交所）", "months": (6, 12), "rule": "3rd_fri",
     "src": "https://www.taiwanindex.com.tw/indexes/TWDP"},
    {"code": "00878", "index": "MSCI 臺灣 ESG 永續高股息精選 30", "months": (5, 11), "rule": "msci",
     "src": "https://www.msci.com/index-review"},
    {"code": "00919", "index": "特選臺灣上市上櫃精選高股息（臺灣指數公司）", "months": (5, 12), "rule": "announce",
     "src": "https://www.taiwanindex.com.tw/"},
    {"code": "00929", "index": "特選臺灣科技優息（臺灣指數公司）", "months": (6,), "rule": "announce",
     "src": "https://www.taiwanindex.com.tw/"},
    {"code": "00940", "index": "臺灣價值高息（臺灣指數公司）", "months": (5, 11), "rule": "announce",
     "src": "https://www.taiwanindex.com.tw/"},
]


def _third_fri(y: int, m: int, tw_open) -> date:
    from .forced_flows import nth_weekday, on_or_before
    return on_or_before(nth_weekday(y, m, 4, 3), tw_open)


def etf_reviews(today: date, sizes: Dict[str, Dict], tw_open, us_open, us_early, horizon: int = 200) -> List[Dict]:
    from .forced_flows import msci_day, on_or_before
    out = []
    for r in ETF_RULES:
        s = sizes.get(r["code"]) or {}
        aum = (s.get("units") or 0) * (s.get("nav") or 0)
        nxt = None
        for k in range(0, 14):
            yy, mm = today.year + (today.month - 1 + k) // 12, (today.month - 1 + k) % 12 + 1
            if mm not in r["months"]:
                continue
            if r["rule"] == "3rd_fri":
                d = _third_fri(yy, mm, tw_open)
            elif r["rule"] == "msci":
                d = on_or_before(msci_day(yy, mm, us_open, us_early), tw_open)
            else:
                d = None
            if d is None:
                if (yy, mm) >= (today.year, today.month):
                    nxt = {"month": f"{yy}-{mm:02d}", "date": None}
                    break
                continue
            if d >= today:
                nxt = {"month": f"{yy}-{mm:02d}", "date": d.isoformat()}
                break
        if not nxt:
            continue
        out.append({"code": r["code"], "name": s.get("name") or r["code"], "index": r["index"], "months": list(r["months"]),
                    "rule": r["rule"], "src": r["src"], "next": nxt, "aum": aum or None, "per1": aum * 0.01 if aum else None,
                    "asof": s.get("date")})
    return sorted(out, key=lambda x: (x["next"]["date"] or x["next"]["month"] + "-99"))


def index_events(today: date, us_open, tw_open, us_early, horizon: int = 120) -> List[Dict]:
    from .forced_flows import index_dates
    out = []
    for e in index_dates(today.year, today.year + 1, us_open, tw_open, us_early):
        d = date.fromisoformat(e.get("tw_date") or e["date"])
        if e["kind"] in ("msci", "tw50") and today <= d <= today + timedelta(days=horizon):
            out.append({"date": d.isoformat(), "kind": e["kind"]})
    for y in (today.year, today.year + 1):                 # FTSE GEIS: quarterly, effective after the 3rd-Friday close
        for m in (3, 6, 9, 12):
            d = _third_fri(y, m, tw_open)
            if today <= d <= today + timedelta(days=horizon):
                out.append({"date": d.isoformat(), "kind": "ftse"})
    return sorted(out, key=lambda x: x["date"])


# ============================================================ universe (台灣 50 ＋ 中型 100)
def universe(d: Dict) -> Dict:
    """{'codes': [...], 'asof', 'source'} — the backtest's MoneyDJ list when this PC has it, else the copy kept in the cache."""
    try:
        from tools.tw_rules_backtest import F_UNIV
        if F_UNIV.exists():
            u = json.loads(F_UNIV.read_text(encoding="utf-8"))
            codes = sorted(set(u.get("0050") or []) | set(u.get("0051") or []))
            if len(codes) >= 100:
                return {"codes": codes, "tw50": sorted(u.get("0050") or []), "asof": u.get("asof"), "source": u.get("source")}
    except Exception:  # noqa: BLE001
        pass
    return d.get("univ") or {}


def _fetch_universe() -> Dict:
    try:
        from tools.tw_rules_backtest import fetch_universe
        u = fetch_universe()
        codes = sorted(set(u.get("0050") or []) | set(u.get("0051") or []))
        if len(codes) >= 100:
            return {"codes": codes, "tw50": sorted(u.get("0050") or []), "asof": u.get("asof"), "source": u.get("source")}
    except Exception as e:  # noqa: BLE001
        log.info("tw desk universe fetch failed: %s", e)
    return {}


# ============================================================ refresh + view
async def refresh(force: bool = False) -> Dict:
    import asyncio
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts_try", 0)) < TTL:
        return d
    d["ts_try"] = now
    u = universe(d)
    if not u.get("codes") or (u is d.get("univ") and now - float(u.get("ts", 0)) > UNIV_TTL):
        u = await asyncio.to_thread(_fetch_universe) or u
    if u.get("codes"):
        d["univ"] = dict(u, ts=now)
    errs = {}
    try:
        rows = await http.get(U_EXDIV, headers=UA, timeout=40, retries=1)
        d["exdiv_all"] = parse_exdiv(rows)
        d["exdiv_ts"] = now
    except Exception as e:  # noqa: BLE001
        errs["exdiv"] = str(e)[:80]
    pun = []
    for url, board in ((U_PUNISH, "上市"), (U_PUNISH_O, "上櫃")):
        try:
            pun += parse_punish(await http.get(url, headers=UA, timeout=40, retries=1), board)
        except Exception as e:  # noqa: BLE001
            errs["punish_" + board] = str(e)[:80]
    if pun or "punish_上市" not in errs:
        d["punish"], d["punish_ts"] = pun, now
    try:                                                   # names for the valuation table (latest BWIBBU, kept by earnings_data)
        from . import earnings_data as E
        nm = {}
        for f, key in ((E.F_TWREV if hasattr(E, "F_TWREV") else E.F_TW, "latest"), (E.F_TWPE, "v")):
            nm.update({c: r.get("name") for c, r in (E._load(f).get(key) or {}).items() if isinstance(r, dict) and r.get("name")})
        if nm:
            d["names"] = nm
    except Exception as e:  # noqa: BLE001
        errs["names"] = str(e)[:60]
    try:                                                   # TSMC vs SOX, 5 years daily (Yahoo)
        from .forced_flows import _yahoo
        px = await _yahoo(["2330.TW", "^SOX"])
        r = rel_strength(px.get("2330.TW"), px.get("^SOX"))
        if r:
            d["rel"], d["rel_ts"] = r, now
    except Exception as e:  # noqa: BLE001
        errs["rel"] = str(e)[:60]
    save(d)
    try:                                                   # each stock's own 5-year valuation history (a few month-ends per run)
        from . import valhist as VH
        d["vh"] = await VH.refresh_tw(VH_BUDGET)
    except Exception as e:  # noqa: BLE001
        errs["valhist"] = str(e)[:60]
    d["errs"] = errs
    d["ts"] = now
    save(d)
    return d


def flow_view(d: Optional[Dict] = None, today: Optional[date] = None, sizes: Optional[Dict] = None, seed: Optional[Dict] = None) -> Dict:
    from .forced_flows import _opens
    d = load() if d is None else d
    today = today or date.today()
    us_open, tw_open, us_early = _opens()
    if sizes is None:
        try:
            from . import tw_etf
            sizes = tw_etf.load().get("nav") or {}
        except Exception:  # noqa: BLE001
            sizes = {}
    u = universe(d)
    codes = set(u.get("codes") or [])
    exd = [r for r in d.get("exdiv_all") or [] if r["date"] >= today.isoformat() and (not codes or r["code"] in codes)]
    pun = [r for r in d.get("punish") or [] if (r.get("to") or "9999") >= today.isoformat()]
    return {"today": today.isoformat(), "univ": u, "exdiv": exd, "punish": pun, "deadlines": deadlines(today),
            "quarter": quarter_window(today, tw_open), "etf": etf_reviews(today, sizes, tw_open, us_open, us_early),
            "index": index_events(today, us_open, tw_open, us_early), "seed": seed or {},
            "ts": d.get("ts"), "exdiv_ts": d.get("exdiv_ts"), "punish_ts": d.get("punish_ts"), "errs": d.get("errs") or {}}


# ============================================================ 2 valuation: each stock vs its own 5 years, market ERP, TSMC
def pct_rank(hist: List[float], now: Optional[float]) -> Optional[float]:
    h = [x for x in hist if x is not None and x > 0]
    if now is None or now <= 0 or len(h) < 24:
        return None
    return round(sum(x < now for x in h) / len(h) * 100, 1)


def stock_bands(snaps: Dict[str, Dict], latest: Dict, codes: List[str], names: Dict[str, str]) -> List[Dict]:
    """P/E percentile vs the stock's own monthly history (P/B when there is no positive P/E today)."""
    days = sorted(snaps)
    out = []
    for c in codes:
        row = (latest.get("rows") or {}).get(c)
        if not row:
            continue
        for metric, i in (("本益比", 0), ("股價淨值比", 1)):
            now = row[i]
            if now is None or now <= 0:
                continue
            hist = [(snaps[k].get(c) or [None, None, None])[i] for k in days]
            p = pct_rank(hist, now)
            if p is None:
                continue
            h = sorted(x for x in hist if x and x > 0)
            out.append({"code": c, "name": names.get(c, ""), "metric": metric, "now": now, "pct": p, "n": len(h),
                        "med": h[len(h) // 2], "lo": h[0], "hi": h[-1], "yld": row[2]})
            break
    return sorted(out, key=lambda r: -r["pct"])


def erp_series(val: Dict[str, Dict], tw10y: List[List]) -> List[Dict]:
    """Monthly: earnings yield of the median listed stock (1 / median P/E) and of TSMC, minus the 10-year government bond."""
    y10 = {str(r[0])[:7]: float(r[1]) for r in tw10y or [] if r and r[1] is not None}
    out, last_y = [], None
    for day in sorted(val):
        v = val[day]
        ym = day[:7]
        y = y10.get(ym, last_y)
        if ym in y10:
            last_y = y10[ym]
        if y is None or not v.get("pe_med"):
            continue
        ey = 100 / v["pe_med"]
        te = 100 / v["tsmc_pe"] if v.get("tsmc_pe") else None
        out.append({"date": day, "ey": round(ey, 2), "y10": y, "erp": round(ey - y, 2), "tsmc_pe": v.get("tsmc_pe"),
                    "tsmc_erp": round(te - y, 2) if te else None, "pe_med": v["pe_med"]})
    return out


def rel_strength(a: Dict, b: Dict) -> Optional[Dict]:
    """TSMC price ÷ SOX (both Yahoo daily) → today's ratio and its 5-year percentile; 1-year change of each."""
    if not a or not b:
        return None
    bm = dict(zip(b["d"], b["c"]))
    pairs = [(d, c / bm[d]) for d, c in zip(a["d"], a["c"]) if bm.get(d)]
    if len(pairs) < 250:
        return None
    r = [x for _, x in pairs]
    now = r[-1]

    def yr(s):
        return (s["c"][-1] / s["c"][-252] - 1) * 100 if len(s["c"]) > 252 else None
    return {"date": pairs[-1][0], "pct": round(sum(x < now for x in r) / len(r) * 100, 1), "tsmc_1y": yr(a), "sox_1y": yr(b), "n": len(r)}


def val_view(d: Optional[Dict] = None) -> Dict:
    from . import valhist as VH
    from . import tw_bubble as TBB
    from . import twmacro as TM
    d = load() if d is None else d
    u = universe(d)
    vh = VH.load("tw")
    names = d.get("names") or {}
    bands = stock_bands(vh.get("snaps") or {}, vh.get("latest") or {}, u.get("codes") or [], names)
    try:
        val = TBB.load().get("val") or {}
    except Exception:  # noqa: BLE001
        val = {}
    try:
        tw10y = (TM.load().get("cbc") or {}).get("tw10y") or []
    except Exception:  # noqa: BLE001
        tw10y = []
    erp = erp_series(val, tw10y)
    cur = erp[-1] if erp else None
    erp_pct = pct_rank([r["erp"] + 50 for r in erp], cur["erp"] + 50) if cur else None   # shift: ERP can be negative
    tsmc_pct = pct_rank([r["tsmc_pe"] for r in erp if r.get("tsmc_pe")], cur.get("tsmc_pe")) if cur else None
    return {"bands": bands, "univ_n": len(u.get("codes") or []), "months": len(vh.get("snaps") or {}),
            "latest": (vh.get("latest") or {}).get("date"), "vh_ts": vh.get("ts"), "erp": erp, "erp_now": cur, "erp_pct": erp_pct,
            "tsmc_pct": tsmc_pct, "rel": d.get("rel"), "rel_ts": d.get("rel_ts")}
