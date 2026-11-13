"""IPO 觀察 data — who is filing to list, where each one is in the process, what the prospectus says, how past IPOs did.

US (SEC, free):
  * discovery: EDGAR full-text search (efts) for S-1 / F-1 (amendments come under the same root form) and 424B4 (the final
    prospectus, filed when the IPO is priced) — back-filled two years in 30-day chunks over a few builds, then the last days;
  * each filer's submissions history: confidential drafts (DRS), the public S-1 and its amendments, 424B4, withdrawal (RW),
    ticker / exchange once listed, and whether it already filed 10-K / 10-Q / 20-F before (then it is a follow-on, not an IPO);
  * the first 2.5 MB of the newest S-1 / F-1 (the cover, summary and summary financial data) for the exchange, symbol,
    price range, lock-up days and an excerpt for the AI summary; the 424B4 cover for the offer price.
Taiwan (TWSE / TPEx / FinMind, free):
  * TWSE 公開申購公告 (every 初上市 / 初上櫃 with 承銷價, 申購期間, 抽籤日, 撥券（掛牌）日, 中籤率), three years;
  * TPEx 興櫃 latest statistics: 興櫃均價 and the 申請上市櫃 date / status of companies queueing to list;
  * FinMind quarterly statements of the upcoming / applying companies (≤ 10 a run, 14 days; the free quota is shared).
Daily closes of the listed IPOs (yfinance) for the after-listing record.  All kept in data_cache/earn_ipo*.json / .pkl
(the Actions cache keeps earn_*)."""
from __future__ import annotations

import asyncio
import html as H
import json
import logging
import os
import re
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR, SEC_USER_AGENT
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_ipo.json"
DOCS = DATA_DIR / "earn_ipo_docs.json"
PX = DATA_DIR / "earn_ipo_px.pkl"
PV = 1
EFTS = "https://efts.sec.gov/LATEST/search-index"
SUB = "https://data.sec.gov/submissions/CIK{:010d}.json"
ARCH = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
FINMIND = "https://api.finmindtrade.com/api/v4/data"
TW_PUBLIC = "https://www.twse.com.tw/rwd/zh/announcement/publicForm"
TW_ESB = "https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics"
BACK_DAYS = 730
PERIODIC = ("10-K", "10-Q", "20-F", "40-F", "10-KT", "10-K405")
REG = ("S-1", "F-1")
HEAD_BYTES = 2_500_000
FIN_BYTES = 16_000_000          # whole prospectus: the quarterly table sits in MD&A (Anthropic's at ~5.5 MB of 14.8 MB)
FIN_PER_RUN = 6
COVER_V = 2                     # bump when parse_cover learns a new pattern: active filers' covers are read once more
LISTED_TW = ("初上市", "初上櫃", "第一上市")


def _hdr() -> Dict[str, str]:
    return {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}


def load(path=FILE) -> Dict:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(d: Dict, path=FILE) -> None:
    try:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, path)
    except OSError as e:
        log.warning("ipo cache not saved: %s", e)


def load_px() -> pd.DataFrame:
    try:
        return pd.read_pickle(PX) if PX.exists() else pd.DataFrame()
    except Exception:  # noqa: BLE001
        return pd.DataFrame()


# ------------------------------------------------------------------ parsers (pure, tested)
def text_of(raw: str) -> str:
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", H.unescape(t)).strip()


def _num(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", ""))
    except (TypeError, ValueError):
        return None


def _after(t: str, heads: List[str], skip: int = 15000) -> int:
    """First occurrence of any heading past the table of contents (the TOC lists the same headings near the top)."""
    best = -1
    for h in heads:
        for m in re.finditer(re.escape(h), t, re.I):
            if m.start() >= skip:
                best = m.start() if best < 0 else min(best, m.start())
                break
    return best


def parse_cover(t: str) -> Dict:
    """Facts from the prospectus text: exchange + symbol, price range, shares offered, lock-up days, and an excerpt.
    (Cover check-boxes such as 'emerging growth company ☐' are not read: the words appear whether ticked or not.)"""
    out: Dict = {}
    m = re.search(r"(Nasdaq (?:Global Select|Global|Capital) Market|New York Stock Exchange|NYSE American|NYSE Texas|NYSE Arca|Nasdaq)"
                  r"[^.]{0,160}?(?:symbol|ticker)\s*[“\"']\s*([A-Z][A-Z.\-]{0,6})\s*[”\"']", t)
    if m:
        out["exchange"], out["symbol"] = m.group(1), m.group(2).rstrip(".")
    elif re.search(r"(apply|applied|approved)[^.]{0,80}(Nasdaq|New York Stock Exchange|NYSE)", t[:60000], re.I):
        out["exchange"] = re.search(r"Nasdaq|New York Stock Exchange|NYSE", t[:60000]).group(0)
    # "between $X and $Y per share", or "…offering price per share will be between $X and $Y" (Anthropic's S-1/A, 2026-11-10)
    m = (re.search(r"between (?:US)?\$\s?([\d.,]+) and (?:US)?\$\s?([\d.,]+) per (?:share|ADS)", t[:80000])
         or re.search(r"price per (?:share|ADS|ordinary share)[^.$]{0,60}?between (?:US)?\$\s?([\d.,]+) and (?:US)?\$\s?([\d.,]+)", t[:80000]))
    if m and _num(m.group(1)) and _num(m.group(2)):
        out["lo"], out["hi"] = _num(m.group(1)), _num(m.group(2))
    m = re.search(r"(?:offering|are offering|is offering)\s+([\d,]{5,}) (?:shares|American Depositary Shares|ADSs)", t[:40000])
    if m:
        out["shares"] = _num(m.group(1))
    out["spac"] = bool(re.search(r"initial business combination", t[:40000], re.I))
    m = re.search(r"(?:lock-up|lock up)[^.]{0,260}?(\d{2,3}) days", t, re.I)
    if m and 30 <= int(m.group(1)) <= 720:
        out["lockup"] = int(m.group(1))
    out["excerpt"] = excerpt(t)
    return out


def excerpt(t: str, cap: int = 22000) -> str:
    """Cover + summary + summary financial data + use of proceeds + summary risk factors, for the AI summary."""
    parts = [t[:3500]]
    for heads, n in ((["Prospectus Summary", "PROSPECTUS SUMMARY"], 5000),
                     (["Summary Consolidated Financial", "Summary Financial", "Summary Historical", "Summary Combined Financial",
                       "SUMMARY CONSOLIDATED FINANCIAL", "Summary Selected"], 7000),
                     (["Summary of Risk Factors", "Summary Risk Factors", "Risk Factors Summary", "SUMMARY RISK FACTORS"], 3000),
                     (["Use of Proceeds", "USE OF PROCEEDS"], 2500)):
        i = _after(t, heads)
        if i >= 0:
            parts.append(t[i:i + n])
    return " … ".join(parts)[:cap]


def offer_price(t: str) -> Optional[float]:
    for pat in (r"initial public offering price (?:of (?:our|the|each) [\w\s]{0,40}?)?(?:of|is|was)\s+(?:US)?\$\s?([\d.,]+)",
                r"offering price[^$]{0,40}(?:US)?\$\s?([\d.,]+) per (?:share|ordinary share|ADS|unit)",
                r"price (?:US)?\$\s?([\d.,]+) per (?:share|ADS|ordinary share)", r"Price to (?:the )?public[^$]{0,30}(?:US)?\$\s?([\d.,]+)"):
        m = re.search(pat, t[:60000], re.I)
        if m and _num(m.group(1)) and 0.5 <= _num(m.group(1)) <= 5000:
            return _num(m.group(1))
    return None


def timeline(sub: Dict) -> Dict:
    """Process dates from a submissions record (recent filings, newest first)."""
    r = (sub.get("filings") or {}).get("recent") or {}
    rows = list(zip(r.get("form", []), r.get("filingDate", []), r.get("accessionNumber", []), r.get("primaryDocument", [])))
    rows.sort(key=lambda x: x[1])
    reg = [x for x in rows if x[0].split("/")[0] in REG]
    out: Dict = {"name": sub.get("name"), "tickers": sub.get("tickers") or [], "exchanges": [e for e in (sub.get("exchanges") or []) if e],
                 "sic": str(sub.get("sic") or ""), "sicd": sub.get("sicDescription") or "", "state": sub.get("stateOfIncorporation") or "",
                 "foreign": any(x[0].startswith("F-1") for x in reg)}
    drs = [x[1] for x in rows if x[0].startswith("DRS")]
    out["drs"] = drs[0] if drs else None
    if reg:
        out["s1"] = reg[0][1]
        out["last"] = reg[-1][1]
        out["amends"] = sum(1 for x in reg if "/A" in x[0])
        out["doc"] = {"acc": reg[-1][2], "file": reg[-1][3], "form": reg[-1][0], "date": reg[-1][1]}
    p = [x for x in rows if x[0] in ("424B4", "424B1") and (not reg or x[1] >= reg[0][1])]
    if p:
        out["priced"] = p[0][1]
        out["p_doc"] = {"acc": p[0][2], "file": p[0][3]}
        pre = [x[1] for x in reg if x[1] < p[0][1]]
        out["last_pre"] = pre[-1] if pre else None
    rw = [x[1] for x in rows if x[0] == "RW" and (not reg or x[1] >= reg[-1][1])]
    out["rw"] = rw[-1] if rw else None
    first = out.get("s1") or out.get("drs")
    out["prior_public"] = bool(first and any(x[0] in PERIODIC and x[1] < first for x in rows))
    return out


SPAC_RX = re.compile(r"\b(acquisition|spac|blank check)\b", re.I)
FUND_RX = re.compile(r"\b(etf|fund|trust|bitcoin|ether(?:eum)?|solana|xrp)\b", re.I)


def kind(rec: Dict) -> str:
    """ipo | spac | fund | followon"""
    nm, sic = rec.get("name") or "", rec.get("sic") or ""
    if sic == "6770" or SPAC_RX.search(nm):
        return "spac"
    if sic in ("6221", "6798", "6792", "") and FUND_RX.search(nm):
        return "fund"
    if rec.get("prior_public"):
        return "followon"
    return "ipo"


def roc(d: str) -> Optional[str]:
    """115/11/19 → 2026-11-19"""
    m = re.match(r"(\d{2,3})/(\d{1,2})/(\d{1,2})", str(d or ""))
    return f"{int(m.group(1)) + 1911:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else None


def parse_public(js: Dict) -> List[Dict]:
    f = js.get("fields") or []
    out = []
    for row in js.get("data") or []:
        r = dict(zip(f, row))
        mk = str(r.get("發行市場", "")).strip()
        if mk not in LISTED_TW:
            continue
        price = _num(str(r.get("實際承銷價(元)", ""))) or _num(str(r.get("承銷價(元)", "")))
        out.append({"code": str(r.get("證券代號", "")).strip(), "name": str(r.get("證券名稱", "")).strip(), "mk": mk,
                    "sub_lo": roc(r.get("申購開始日")), "sub_hi": roc(r.get("申購結束日")), "draw": roc(r.get("抽籤日期")),
                    "list": roc(r.get("撥券日期(上市、上櫃日期)")), "price": price,
                    "final": _num(str(r.get("實際承銷價(元)", ""))) is not None, "shares": _num(str(r.get("實際承銷股數", "")) or ""),
                    "win": _num(str(r.get("中籤率(%)", ""))), "broker": str(r.get("主辦券商", "")).strip(),
                    "cancel": bool(str(r.get("取消公開抽籤 ", r.get("取消公開抽籤", ""))).strip())})
    return out


def parse_esb(rows: List[Dict]) -> Dict[str, Dict]:
    out = {}
    for r in rows or []:
        c = str(r.get("SecuritiesCompanyCode", "")).strip()
        if not c:
            continue
        ad = str(r.get("ApplyingDate", "")).strip()
        out[c] = {"name": str(r.get("CompanyName", "")).strip(), "avg": _num(str(r.get("Average", ""))),
                  "prev": _num(str(r.get("PreviousAveragePrice", ""))), "vol": _num(str(r.get("TransactionVolume", ""))),
                  "apply": f"{ad[:4]}-{ad[4:6]}-{ad[6:8]}" if len(ad) == 8 else None,
                  "to": {"E": "上櫃", "e": "上市"}.get(str(r.get("ApplyingStatus", "")).strip())}
    return out


def tw_fin(inc: List[Dict]) -> Optional[Dict]:
    """Quarterly revenue / net income (single quarters) → latest quarter, revenue YoY, trailing-4Q revenue and net margin."""
    rev: Dict[str, float] = {}
    ni: Dict[str, float] = {}
    eps: Dict[str, float] = {}
    for r in inc or []:
        v, t, d = _num(str(r.get("value"))), r.get("type"), r.get("date")
        if v is None or not d:
            continue
        if t == "Revenue":
            rev[d] = v
        elif t in ("IncomeAfterTaxes", "TotalConsolidatedProfitForThePeriod"):
            ni.setdefault(d, v)
        elif t == "EPS":
            eps[d] = v
    if not rev:
        return None
    qs = sorted(rev)
    last = qs[-1]
    y = str(int(last[:4]) - 1) + last[4:]
    out: Dict = {"q": last, "rev_q": rev[last], "yoy": (rev[last] / rev[y] - 1) * 100 if rev.get(y) and rev[y] > 0 else None}
    if len(qs) >= 4:
        r4 = sum(rev[q] for q in qs[-4:])
        n4 = [ni.get(q) for q in qs[-4:]]
        out["rev_ttm"] = r4
        out["nm_ttm"] = sum(n4) / r4 * 100 if None not in n4 and r4 > 0 else None
        e4 = [eps.get(q) for q in qs[-4:]]
        out["eps_ttm"] = sum(e4) if None not in e4 else None
    return out


# ------------------------------------------------------------------ fetchers
async def _efts(forms: str, start: str, end: str, deadline: float) -> List[Dict]:
    out, frm = [], 0
    while time.time() < deadline:
        js = await http.get(EFTS, params={"forms": forms, "dateRange": "custom", "startdt": start, "enddt": end, "from": str(frm)},
                            headers=_hdr(), timeout=30, retries=1)
        hits = ((js or {}).get("hits") or {}).get("hits") or []
        for h in hits:
            s = h.get("_source") or {}
            ciks = s.get("ciks") or []
            if not ciks:
                continue
            out.append({"cik": int(ciks[0]), "form": s.get("form"), "date": s.get("file_date"), "name": (s.get("display_names") or [""])[0]})
        total = (((js or {}).get("hits") or {}).get("total") or {}).get("value", 0)
        frm += len(hits)
        if not hits or frm >= min(total, 9900):
            break
        await asyncio.sleep(0.15)
    return out


async def _head(url: str, limit: int = HEAD_BYTES) -> str:
    """The first `limit` bytes of a (possibly huge) EDGAR document."""
    s = await http.session()
    import aiohttp
    async with s.get(url, headers=_hdr(), timeout=aiohttp.ClientTimeout(total=60)) as r:
        r.raise_for_status()
        buf = b""
        async for chunk in r.content.iter_chunked(65536):
            buf += chunk
            if len(buf) >= limit:
                break
    return buf.decode("utf-8", errors="ignore")


async def refresh_us(d: Dict, docs: Dict, deadline: float) -> None:
    us = d.setdefault("us", {})
    filers = us.setdefault("filers", {})
    today = date.today()
    disc_to = us.get("disc_to")
    start = date.fromisoformat(disc_to) - timedelta(days=5) if disc_to else today - timedelta(days=BACK_DAYS)
    while start <= today and time.time() < deadline - 20:              # discovery, resumable 30-day chunks
        end = min(start + timedelta(days=30), today)
        try:
            hits = await _efts("S-1,F-1,424B4", start.isoformat(), end.isoformat(), deadline)
        except Exception as e:  # noqa: BLE001
            log.info("ipo efts %s: %s", start, e)
            break
        for h in hits:
            f = filers.setdefault(str(h["cik"]), {"name": h["name"]})
            f["seen"] = max(f.get("seen", ""), h["date"] or "")
            if h["form"] == "424B4":
                f["b4"] = True
        us["disc_to"] = end.isoformat()
        start = end + timedelta(days=1)
    now = time.time()

    def due(c: str, f: Dict) -> bool:
        if f.get("drop"):
            return False
        ttl = 86400 if not f.get("priced") else 14 * 86400
        if f.get("seen", "") > f.get("sub_seen", "") or (f.get("priced") and "last_pre" not in f):
            return True
        return now - f.get("sts", 0) > ttl

    todo = sorted((c for c, f in filers.items() if due(c, f)), key=lambda c: filers[c].get("seen", ""), reverse=True)
    sub_end = time.time() + max(10.0, (deadline - time.time()) * 0.55)   # leave the rest for the prospectus covers
    for c in todo:
        if time.time() > sub_end:
            break
        f = filers[c]
        try:
            sub = await http.get(SUB.format(int(c)), headers=_hdr(), timeout=30, retries=1)
            rec = timeline(sub or {})
            f.update(rec)
            f["kind"] = "spac" if f.get("spac_text") else kind(rec)          # a SPAC found from its prospectus stays one
            f["drop"] = f["kind"] in ("followon", "fund")
            f["sts"], f["sub_seen"] = time.time(), f.get("seen", "")
        except Exception as e:  # noqa: BLE001
            log.info("ipo submissions %s: %s", c, e)
        await asyncio.sleep(0.12)
    # prospectus heads: newest registration of operating IPOs still in process (and the 424B4 cover for the offer price)
    act = sorted(((int(c), f) for c, f in filers.items() if f.get("kind") == "ipo" and not f.get("rw") and f.get("doc")),
                 key=lambda x: x[1].get("last", ""), reverse=True)
    fin_n = [0]
    for cik, f in act:
        if time.time() > deadline - 5:
            break
        if not f.get("priced") and f.get("last", "") >= (today - timedelta(days=270)).isoformat() and (f.get("cover_acc") != f["doc"]["acc"] or f.get("cover_v") != COVER_V):
            try:
                raw = await _head(ARCH.format(cik=cik, acc=f["doc"]["acc"].replace("-", ""), doc=f["doc"]["file"]))
                cv = parse_cover(text_of(raw))
                docs[f["doc"]["acc"]] = cv.pop("excerpt")
                if cv.get("spac"):
                    f["kind"], f["spac_text"] = "spac", True
                f["cover"], f["cover_acc"], f["cover_v"] = cv, f["doc"]["acc"], COVER_V
            except Exception as e:  # noqa: BLE001
                log.info("ipo cover %s: %s", cik, e)
            await asyncio.sleep(0.15)
        # the prospectus's own numbers (summary table + quarterly table, often deep in MD&A): read the whole document once
        # per amendment, the newest filers first, a few per build (S-1s run to 15 MB)
        if (not f.get("priced") and f.get("last", "") >= (today - timedelta(days=270)).isoformat() and f.get("cover", {}).get("exchange")
                and f.get("fin_acc") != f["doc"]["acc"] and fin_n[0] < FIN_PER_RUN and time.time() < deadline - 30):
            fin_n[0] += 1
            try:
                from .ipo_fin import parse_fin, parse_quarters
                raw = await _head(ARCH.format(cik=cik, acc=f["doc"]["acc"].replace("-", ""), doc=f["doc"]["file"]), FIN_BYTES)
                f["fin"] = {"summary": parse_fin(raw), "q": parse_quarters(raw), "acc": f["doc"]["acc"]}
                f["fin_acc"] = f["doc"]["acc"]
            except Exception as e:  # noqa: BLE001
                log.info("ipo financials %s: %s", cik, e)
            await asyncio.sleep(0.15)
        if f.get("priced") and f.get("p_doc") and not f.get("offer") and f.get("offer_try", 0) < 2:
            f["offer_try"] = f.get("offer_try", 0) + 1
            try:
                raw = await _head(ARCH.format(cik=cik, acc=f["p_doc"]["acc"].replace("-", ""), doc=f["p_doc"]["file"]), 800_000)
                t = text_of(raw)
                f["offer"] = offer_price(t)
                cv = parse_cover(t)
                if cv.get("spac"):
                    f["kind"], f["spac_text"] = "spac", True
                if cv.get("lockup"):
                    f.setdefault("cover", {})["lockup"] = cv["lockup"]
                if cv.get("symbol"):
                    f.setdefault("cover", {})["symbol"] = cv["symbol"]
                if cv.get("shares"):
                    f["offer_shares"] = cv["shares"]
            except Exception as e:  # noqa: BLE001
                log.info("ipo 424B4 %s: %s", cik, e)
            await asyncio.sleep(0.15)


async def refresh_tw(d: Dict, deadline: float) -> None:
    tw = d.setdefault("tw", {})
    yr = date.today().year
    pub = tw.setdefault("public", {})
    for y in (yr, yr - 1, yr - 2):
        k = str(y)
        ttl = 6 * 3600 if y == yr else 30 * 86400
        if time.time() - (pub.get(k) or {}).get("ts", 0) < ttl or time.time() > deadline:
            continue
        try:
            js = await http.get(TW_PUBLIC, params={"response": "json", "date": f"{k}0101"}, timeout=30, retries=1)
            if (js or {}).get("stat") == "OK":
                pub[k] = {"ts": time.time(), "rows": parse_public(js)}
        except Exception as e:  # noqa: BLE001
            log.info("ipo TWSE public %s: %s", y, e)
    if time.time() - (tw.get("esb") or {}).get("ts", 0) > 6 * 3600 and time.time() < deadline:
        try:
            rows = await http.get(TW_ESB, timeout=30, retries=1)
            if isinstance(rows, list) and rows:
                tw["esb"] = {"ts": time.time(), "rows": parse_esb(rows)}
                lg = tw.setdefault("apply_log", {})            # application date per code, kept after it leaves 興櫃
                for c, r in tw["esb"]["rows"].items():
                    if r.get("apply"):
                        lg.setdefault(c, {"apply": r["apply"], "to": r.get("to"), "name": r["name"]})
        except Exception as e:  # noqa: BLE001
            log.info("ipo TPEx esb: %s", e)
    today = date.today().isoformat()
    want = [r["code"] for y in pub.values() for r in y.get("rows", []) if (r.get("list") or "") >= today]
    want += [c for c, r in ((tw.get("esb") or {}).get("rows") or {}).items() if r.get("apply")]
    fin = tw.setdefault("fin", {})
    n = 0
    for c in dict.fromkeys(want):
        if n >= 10 or time.time() > deadline:
            break
        if time.time() - (fin.get(c) or {}).get("ts", 0) < 14 * 86400:
            continue
        n += 1
        try:
            js = await http.get(FINMIND, params={"dataset": "TaiwanStockFinancialStatements", "data_id": c,
                                                 "start_date": (date.today() - timedelta(days=800)).isoformat()}, timeout=60, retries=1)
            if (js or {}).get("status") not in (200, None):
                raise RuntimeError(f"FinMind {js.get('status')}: {js.get('msg')}")
            fin[c] = {"ts": time.time(), **(tw_fin((js or {}).get("data") or []) or {})}
        except Exception as e:  # noqa: BLE001
            log.info("ipo FinMind %s: %s", c, e)
            if "402" in str(e) or "429" in str(e) or "limit" in str(e).lower():
                break
        await asyncio.sleep(0.4)


def _price_syms(d: Dict) -> List[str]:
    us = [(f.get("tickers") or [None])[0] or (f.get("cover") or {}).get("symbol") for f in ((d.get("us") or {}).get("filers") or {}).values()
          if f.get("kind") == "ipo" and f.get("priced")]
    tw = [f"{r['code']}.{'TW' if r['mk'] != '初上櫃' else 'TWO'}" for y in ((d.get("tw") or {}).get("public") or {}).values()
          for r in y.get("rows", []) if r.get("list") and r["list"] <= date.today().isoformat()]
    return sorted({s for s in us + tw if s})


def refresh_px(d: Dict, force: bool = False) -> None:
    syms = _price_syms(d)
    px = load_px()
    if not syms or (not force and not px.empty and time.time() - PX.stat().st_mtime < 12 * 3600 and set(syms) <= set(px.columns)):
        return
    try:
        import yfinance as yf
        df = yf.download(syms, period="3y", interval="1d", auto_adjust=True, progress=False, threads=True)["Close"]
        if isinstance(df, pd.Series):
            df = df.to_frame(syms[0])
        if not df.empty:
            tmp = PX.with_suffix(".tmp")
            pd.to_pickle(df.dropna(how="all"), tmp)
            os.replace(tmp, PX)
    except Exception as e:  # noqa: BLE001
        log.info("ipo prices: %s", e)


async def refresh(budget_s: float = 150) -> Dict:
    d = load()
    if d.get("pv") != PV:
        d = {"pv": PV}
    docs = load(DOCS)
    t0 = time.time()
    try:
        await refresh_tw(d, t0 + budget_s * 0.25)
        await refresh_us(d, docs, t0 + budget_s * 0.85)
    finally:
        keep = {(f.get("doc") or {}).get("acc") for f in ((d.get("us") or {}).get("filers") or {}).values()}
        docs = {k: v for k, v in docs.items() if k in keep}
        d["ts"] = time.time()
        _save(d)
        _save(docs, DOCS)
    await asyncio.to_thread(refresh_px, d)
    return d
