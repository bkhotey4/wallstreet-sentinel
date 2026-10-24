"""金融穩定監測的 4 個缺口（對照聯準會《金融穩定報告》的 4 大類脆弱度補上的官方免費數據）。

  * 財政部發債  — 季度再融資：借款估算（Financing Estimates）＋政策聲明裡「未來幾季維持中長債標售規模」那句話有沒有改口；
                 短期國債（bills）占可交易國債的比重（fiscaldata MSPD，月資料）；12 個月滾動赤字（FRED MTSDS133FMS）。
  * 短期資金市場 — SOFR 與準備金利率 IORB 的利差、SOFR 第 99 百分位成交利率（紐約聯準會 Markets API）；
                 常設回購工具 SRF 的實際動用金額（同一個 API 的 repo 操作結果）。
  * 基差交易     — CFTC 交易者持倉報告（TFF）：槓桿基金在 2／5／10 年、超長 10 年、30 年、超長 30 年美債期貨的淨空單名目金額。
                 淨空單大＝避險基金「買現貨、賣期貨」的基差交易規模大；2020 年 3 月平倉潮是美債崩盤的主因之一。
  * AI 資本支出  — 微軟、Alphabet、亞馬遜、Meta、甲骨文、CoreWeave 的 TTM 資本支出、營業現金流、總負債（SEC XBRL，產業體檢已在抓）。

每項只用官方公開數據和固定規則（歷史百分位、和自己過去比），不看新聞標題。
快取在 data_cache/econ_stability.json（網站 CI 已保留 econ_*），每 6 小時最多抓一次。"""
from __future__ import annotations

import html as _html
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_stability.json"
TTL = 6 * 3600
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research)"}
FRED_IDS = ("IORB", "MTSDS133FMS")                      # fetched by the FRED feed (see data/fred.py)

QR_URL = "https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding/most-recent-quarterly-refunding-documents"
TSY = "https://home.treasury.gov"
MSPD_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/debt/mspd/mspd_table_1"
SOFR_URL = "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2018-04-02&endDate={end}"
REPO_URL = "https://markets.newyorkfed.org/api/rp/repo/all/results/last/{n}.json"
CFTC_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
# the monthly coverage audit (cloud routine) writes this file in the public site repo; the bot reads it from there
COVER_URL = "https://raw.githubusercontent.com/bkhotey4/wallstreet-sentinel/main/research_feed/coverage.json"
# contract → (中文, 名目面額 $) ; 2 年期一口 20 萬美元，其餘 10 萬
FUTURES = {"042601": ("2 年", 200_000), "044601": ("5 年", 100_000), "043602": ("10 年", 100_000),
           "043607": ("超長 10 年", 100_000), "020601": ("30 年", 100_000), "020604": ("超長 30 年", 100_000)}
AI_GROUP = ("MSFT", "GOOGL", "AMZN", "META", "ORCL", "CRWV")
AI_NAMES = {"MSFT": "微軟", "GOOGL": "Alphabet", "AMZN": "亞馬遜", "META": "Meta", "ORCL": "甲骨文", "CRWV": "CoreWeave"}
GUIDE_KEEP = "anticipates maintaining nominal coupon and FRN auction sizes"


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", FILE.name, e)
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)


def _text(page: str) -> str:
    page = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", page))).strip()


def _iso(s: str) -> Optional[str]:
    try:
        return datetime.strptime(re.sub(r"\s+", " ", s.strip()), "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


# ───────────────────────── 財政部季度再融資 ─────────────────────────
def parse_qr_index(page: str) -> Dict:
    """Links to the latest Financing Estimates / Policy Statement press releases + the scheduled next release dates."""
    links = {}
    for href, label in re.findall(r'href="?([^" >]+)"?[^>]*>(.*?)</a>', page, re.S):
        lab = re.sub(r"<[^>]+>", "", label).strip()
        for key, pat in (("estimates", r"^Financing Estimates"), ("policy", r"^Policy Statement")):
            if key not in links and re.match(pat, lab) and "press-releases" in href:
                links[key] = (href if href.startswith("http") else TSY + href, re.sub(r"\s+", " ", lab))
    nxt = [_iso(m) for m in re.findall(r"next release is scheduled for (?:\w+day, )?([A-Z][a-z]+ \d{1,2}, \d{4})", _html.unescape(page))]
    nxt = list(dict.fromkeys(x for x in nxt if x))
    return {"links": links, "next": nxt}


def parse_estimates(txt: str) -> Dict:
    qs = [{"quarter": f"{a}–{b} {y}", "bn": float(v.replace(",", ""))}
          for a, b, y, v in re.findall(r"During the (\w+)\s*[–-]\s*(\w+) (\d{4}) quarter, Treasury expects to borrow \$([\d,]+) billion", txt)]
    rev = re.search(r"borrowing estimate is \$([\d,]+) billion (higher|lower) than announced in (\w+ \d{4})", txt)
    return {"quarters": qs,
            "revision": {"bn": float(rev.group(1).replace(",", "")) * (1 if rev.group(2) == "higher" else -1), "vs": rev.group(3)} if rev else None}


def parse_policy(txt: str) -> Dict:
    """The forward-guidance sentence on nominal coupon / FRN auction sizes, and what it says."""
    sents = re.split(r"(?<=\.)\s+", txt)
    hit = [s for s in sents if "auction size" in s and re.search(r"anticipat|expects|increas|reduc", s)]
    guide = hit[0].strip() if hit else ""
    low = guide.lower()
    if GUIDE_KEEP.lower() in low:
        status = "keep"
    elif re.search(r"increas", low):
        status = "increase"
    elif re.search(r"reduc|decreas", low):
        status = "decrease"
    else:
        status = "unknown" if not guide else "changed"
    refund = re.search(r"offering \$([\d,.]+) billion of Treasury securities to refund approximately \$([\d,.]+) billion", txt)
    return {"guidance": guide, "status": status,
            "offer_bn": float(refund.group(1).replace(",", "")) if refund else None,
            "new_cash_bn": (float(refund.group(1).replace(",", "")) - float(refund.group(2).replace(",", ""))) if refund else None}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def merge_refunding(old: Dict, idx: Dict, est: Optional[Dict], pol: Optional[Dict], est_meta, pol_meta) -> Dict:
    """Keep a history of every policy statement seen, so a change of wording is detected against the previous one."""
    r = dict(old or {})
    r["next"] = idx.get("next") or r.get("next") or []
    if est is not None and est_meta:
        r["estimates"] = {**est, "url": est_meta[0], "label": est_meta[1], "date": est_meta[2]}
    if pol is not None and pol_meta:
        hist = list(r.get("history") or [])
        if not hist or hist[-1].get("url") != pol_meta[0]:
            prev = hist[-1] if hist else None
            changed = bool(prev and pol.get("guidance") and _norm(prev.get("guidance")) != _norm(pol.get("guidance")))
            hist.append({"url": pol_meta[0], "label": pol_meta[1], "date": pol_meta[2], "guidance": pol.get("guidance"),
                         "status": pol.get("status"), "changed": changed, "seen": time.strftime("%Y-%m-%d")})
        r["history"] = hist[-12:]
        r["policy"] = {**pol, "url": pol_meta[0], "label": pol_meta[1], "date": pol_meta[2], "changed": r["history"][-1]["changed"]}
    return r


async def _press(url: str):
    page = await http.get(url, kind="text", headers=UA, timeout=40, retries=1)
    m = re.search(r'datetime="?(\d{4}-\d{2}-\d{2})', page)
    return _text(page), (m.group(1) if m else None)


async def fetch_refunding(old: Dict) -> Dict:
    idx = parse_qr_index(await http.get(QR_URL, kind="text", headers=UA, timeout=40, retries=1))
    est = pol = em = pm = None
    if "estimates" in idx["links"]:
        u, lab = idx["links"]["estimates"]
        t, d = await _press(u)
        est, em = parse_estimates(t), (u, lab, d)
    if "policy" in idx["links"]:
        u, lab = idx["links"]["policy"]
        t, d = await _press(u)
        pol, pm = parse_policy(t), (u, lab, d)
    if not est and not pol:
        raise ValueError("no refunding documents found")
    return merge_refunding(old, idx, est, pol, em, pm)


async def fetch_bills() -> List[List]:
    """[[YYYY-MM, bills share of marketable debt %, bills $tn]] oldest first."""
    async def one(flt):
        js = await http.get(MSPD_URL, params={"filter": flt, "sort": "-record_date", "page[size]": "400",
                                              "fields": "record_date,total_mil_amt"}, headers=UA, timeout=40, retries=1)
        return {r["record_date"][:7]: float(r["total_mil_amt"]) for r in js.get("data", []) if r.get("total_mil_amt") not in (None, "null")}
    bills = await one("security_class_desc:eq:Bills,security_type_desc:eq:Marketable")
    tot = await one("security_type_desc:eq:Total Marketable")
    return [[m, round(bills[m] / tot[m] * 100, 2), round(bills[m] / 1e6, 3)] for m in sorted(bills) if tot.get(m)]


# ───────────────────────── 短期資金市場 ─────────────────────────
def parse_sofr(js: Dict) -> List[List]:
    out = []
    for r in js.get("refRates", []):
        try:
            out.append([r["effectiveDate"], float(r["percentRate"]), float(r.get("percentPercentile99") or r["percentRate"]),
                        float(r.get("volumeInBillions") or 0)])
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(out)


def parse_repo(js: Dict) -> List[List]:
    """Standing repo facility: [[date, accepted $bn]] summed over the day's operations."""
    by: Dict[str, float] = {}
    for op in (js.get("repo") or {}).get("operations", []):
        if op.get("operationType") != "Repo":
            continue
        by[op["operationDate"]] = by.get(op["operationDate"], 0.0) + float(op.get("totalAmtAccepted") or 0) / 1e9
    return sorted([d, round(v, 3)] for d, v in by.items())


# ───────────────────────── CFTC 基差交易 ─────────────────────────
def parse_cftc(rows: List[Dict]) -> List[List]:
    """[[date, leveraged-fund net short $bn (all Treasury futures), {tenor: $bn}]] oldest first."""
    by: Dict[str, Dict[str, float]] = {}
    for r in rows:
        code = r.get("cftc_contract_market_code")
        if code not in FUTURES:
            continue
        try:
            net = (float(r["lev_money_positions_short"]) - float(r["lev_money_positions_long"])) * FUTURES[code][1] / 1e9
        except (KeyError, TypeError, ValueError):
            continue
        by.setdefault(r["report_date_as_yyyy_mm_dd"][:10], {})[FUTURES[code][0]] = round(net, 2)
    return [[d, round(sum(v.values()), 1), v] for d, v in sorted(by.items())]


async def fetch_cftc() -> List[List]:
    codes = ",".join(f"'{c}'" for c in FUTURES)
    js = await http.get(CFTC_URL, params={"$select": "report_date_as_yyyy_mm_dd,cftc_contract_market_code,lev_money_positions_long,lev_money_positions_short",
                                          "$where": f"cftc_contract_market_code in({codes}) AND report_date_as_yyyy_mm_dd >= '2010-01-01'",
                                          "$order": "report_date_as_yyyy_mm_dd", "$limit": "20000"}, headers=UA, timeout=60, retries=1)
    return parse_cftc(js if isinstance(js, list) else [])


async def refresh(force: bool = False) -> Dict:
    d = load()
    now = time.time()
    if not force and now - float(d.get("ts", 0)) < TTL and d.get("sofr"):
        return d
    bad = []
    steps = (("refunding", lambda: fetch_refunding(d.get("refunding") or {})), ("bills", fetch_bills),
             ("sofr", lambda: _get_parse(SOFR_URL.format(end=time.strftime("%Y-%m-%d")), parse_sofr)),
             ("repo", lambda: _get_parse(REPO_URL.format(n=500), parse_repo)), ("cftc", fetch_cftc),
             ("coverage", lambda: _get_parse(COVER_URL, lambda js: js if isinstance(js, dict) and "gaps" in js else None)))
    for key, fn in steps:
        try:
            v = await fn()
            if not v:
                raise ValueError("empty")
            d[key] = v
            d.setdefault("ts_each", {})[key] = now
        except Exception as e:  # noqa: BLE001
            bad.append(f"{key}: {e if str(e) else type(e).__name__}")
    bad = [b for b in bad if not b.startswith("coverage")]   # optional: absent until the first monthly audit runs
    if len(bad) < len(steps):
        d["ts"] = now
        _save(d)
    if bad:
        log.warning("stability data: %s", "; ".join(bad))
        HEALTH.fail("stability", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("stability", len(d.get("cftc") or []), every=TTL)
    return d


async def _get_parse(url: str, fn):
    return fn(await http.get(url, headers=UA, timeout=40, retries=1))


# ───────────────────────── 判讀（固定規則） ─────────────────────────
def pct_rank(vals: List[float], v: float) -> Optional[float]:
    vals = [x for x in vals if x is not None]
    return float(sum(x < v for x in vals) / len(vals) * 100) if vals else None


def _fred_last(eng, sid: str):
    try:
        s = eng.fred.get(sid).dropna()
        return s if len(s) else None
    except Exception:  # noqa: BLE001
        return None


def funding_view(d: Dict, eng) -> Optional[Dict]:
    sofr = d.get("sofr") or []
    iorb = _fred_last(eng, "IORB") if eng is not None else None
    if len(sofr) < 20:
        return None
    out: Dict = {"date": sofr[-1][0], "sofr": sofr[-1][1], "p99": sofr[-1][2], "vol": sofr[-1][3]}
    if iorb is not None:
        import pandas as pd
        ib = iorb.reindex(pd.to_datetime([r[0] for r in sofr]), method="ffill")
        sp = [(r[1] - b) * 100 if b == b else None for r, b in zip(sofr, ib.values)]
        sp99 = [(r[2] - b) * 100 if b == b else None for r, b in zip(sofr, ib.values)]
        if sp[-1] is not None:
            out.update(iorb=float(ib.values[-1]), spread=sp[-1], spread99=sp99[-1],
                       spread_pct=pct_rank(sp[:-1], sp[-1]), spread99_pct=pct_rank(sp99[:-1], sp99[-1]),
                       hist=[[r[0], s] for r, s in zip(sofr, sp) if s is not None][-260:],
                       days_above=sum(1 for s in sp[-20:] if s is not None and s > 0))
    repo = d.get("repo") or []
    if repo:
        last20 = [v for _, v in repo[-20:]]
        out["srf"] = {"last": repo[-1], "max20": max(last20), "days_used20": sum(1 for v in last20 if v >= 0.5),
                      "max_all": max(v for _, v in repo), "max_all_date": max(repo, key=lambda x: x[1])[0]}
    sp, s99 = out.get("spread"), out.get("spread99")
    srf = out.get("srf") or {}
    if sp is not None and (sp >= 5 or srf.get("max20", 0) >= 25):
        out["state"], out["emoji"] = "緊繃", "🔴"
        out["read"] = "SOFR 明顯高於準備金利率或常設回購被大量動用：銀行體系的現金不夠用，2019 年 9 月回購危機就是這個樣子。"
    elif (sp is not None and sp > 0) or (s99 is not None and s99 >= 10) or srf.get("days_used20", 0) >= 2:
        out["state"], out["emoji"] = "偏緊", "🟡"
        out["read"] = "隔夜資金利率高於準備金利率、或常設回購有人動用：準備金開始不太充裕，月底、繳稅日、大額發債交割日最容易出現。"
    else:
        out["state"], out["emoji"] = "寬鬆", "🟢"
        out["read"] = "隔夜資金利率在準備金利率之下，常設回購沒人用：短期資金充足。"
    return out


def basis_view(d: Dict) -> Optional[Dict]:
    rows = d.get("cftc") or []
    if len(rows) < 60:
        return None
    vals = [r[1] for r in rows]
    last = rows[-1]
    yr = rows[-53] if len(rows) > 53 else rows[0]
    p = pct_rank(vals[:-1], last[1])
    hi52 = max(vals[-53:-1])
    out = {"date": last[0], "net": last[1], "by": last[2], "yago": yr[1], "pct": p, "hi52": hi52, "record": last[1] >= max(vals[:-1]),
           "hist": [[r[0], r[1]] for r in rows[-260:]], "since": rows[0][0][:4]}
    if p is not None and p >= 95:
        out["state"], out["emoji"] = "極大", "🔴"
        out["read"] = ("槓桿基金在美債期貨的淨空單處於歷史極端：基差交易規模非常大。平常它提供流動性，"
                       "但遇到資金或保證金壓力時會被迫一起平倉，2020 年 3 月就因此讓美債現貨大跌。")
    elif p is not None and p >= 80:
        out["state"], out["emoji"] = "偏大", "🟡"
        out["read"] = "基差交易規模偏大：本身不是警訊，但要和資金市場（SOFR）、MOVE 債市波動一起看，三者同時變差才是平倉風險。"
    else:
        out["state"], out["emoji"] = "正常", "🟢"
        out["read"] = "基差交易規模在常態範圍。"
    return out


def refunding_view(d: Dict, eng=None) -> Optional[Dict]:
    r = d.get("refunding") or {}
    if not r.get("policy") and not r.get("estimates"):
        return None
    out = dict(r)
    pol = r.get("policy") or {}
    st = pol.get("status")
    out["state"], out["emoji"], out["read"] = {
        "keep": ("維持", "🟢", "財政部仍說未來幾季「維持」中長期國債的標售規模：長債供給暫時不會突然變多，缺口用短期國債補。"),
        "increase": ("加量", "🔴", "財政部改口要增加中長期國債的標售規模：長債供給變多，買家通常要更高殖利率才肯接（2023 年 8 月就是這樣開始的）。"),
        "decrease": ("減量", "🟢", "財政部表示要減少中長期國債標售規模：長債供給壓力下降。"),
        "changed": ("措辭改變", "🟡", "財政部對標售規模的說法和上一季不同，請看原文。"),
    }.get(st, ("待確認", "⚪", "沒有抓到標售規模的說法。"))
    if pol.get("changed") and st == "keep":
        out["state"], out["emoji"] = "措辭改變", "🟡"
        out["read"] = "仍說維持，但整句措辭和上一季不同（常是改口前的鋪路），請看原文。"
    bills = d.get("bills") or []
    if bills:
        sh = [b[1] for b in bills]
        out["bills"] = {"month": bills[-1][0], "share": bills[-1][1], "tn": bills[-1][2], "yago": bills[-13][1] if len(bills) > 13 else None,
                        "pct": pct_rank(sh[:-1], sh[-1]), "since": bills[0][0][:4], "hist": bills[-120:]}
    if eng is not None:
        dfc = _fred_last(eng, "MTSDS133FMS")
        if dfc is not None and len(dfc) >= 13:
            out["deficit12"] = {"bn": float(dfc.tail(12).sum()) / 1000, "yago": float(dfc.iloc[-24:-12].sum()) / 1000 if len(dfc) >= 24 else None,
                                "month": dfc.index[-1].strftime("%Y-%m")}
    return out


def ai_view(fund: Optional[Dict] = None) -> Optional[Dict]:
    if fund is None:
        from . import fundamentals as F
        fund = F.load()
    from .fundamentals import total_debt
    rows = []
    for s in AI_GROUP:
        rec = (fund or {}).get(s) or {}
        p, m = rec.get("p") or {}, rec.get("m") or {}
        capex, ocf = (p.get("capex") or {}).get("v"), (p.get("ocf") or {}).get("v")
        if capex is None or ocf is None:
            continue
        rows.append({"sym": s, "name": AI_NAMES[s], "end": p.get("end"), "capex": capex, "capex_prev": (p.get("capex") or {}).get("prev"),
                     "ocf": ocf, "fcf": ocf - capex, "ratio": capex / ocf if ocf > 0 else None,
                     "ratio_prev": m.get("capex_ocf_prev"), "debt": total_debt(p), "debt_prev": total_debt(p, "prev"),
                     "cash": (p.get("cash") or {}).get("v")})
    if len(rows) < 3:
        return None
    cap = sum(r["capex"] for r in rows)
    capp = sum(r["capex_prev"] or 0 for r in rows)
    ocf = sum(r["ocf"] for r in rows)
    dt = [r for r in rows if r["debt"] is not None and r["debt_prev"]]
    debt, debtp = sum(r["debt"] for r in dt), sum(r["debt_prev"] for r in dt)
    out = {"rows": rows, "capex": cap, "capex_growth": (cap / capp - 1) * 100 if capp else None, "ocf": ocf, "ratio": cap / ocf if ocf else None,
           "fcf": ocf - cap, "debt": debt, "debt_add": debt - debtp, "debt_growth": (debt / debtp - 1) * 100 if debtp else None,
           "over1": [r["name"] for r in rows if r["ratio"] is not None and r["ratio"] > 1]}
    ratio = out["ratio"] or 0
    if ratio > 1:
        out["state"], out["emoji"] = "靠借錢", "🔴"
        out["read"] = "這幾家合計的資本支出已經超過營業現金流：整體 AI 建設要靠借錢或動用存款支撐，利率愈高壓力愈大。"
    elif ratio > 0.8 or out["over1"]:
        out["state"], out["emoji"] = "吃緊", "🟡"
        out["read"] = ("合計資本支出接近營業現金流的上限，" + (f"其中{'、'.join(out['over1'])}已經花得比賺得多，要靠借錢補。" if out["over1"] else "") +
                       "市場會先修理靠借錢擴張、現金最少的公司。")
    else:
        out["state"], out["emoji"] = "自己付得起", "🟢"
        out["read"] = "合計資本支出還在營業現金流之內，大部分用自己賺的錢支付。"
    return out


def view(eng=None) -> Dict:
    d = load()
    out = {"ts": d.get("ts"), "coverage": d.get("coverage")}
    for k, fn in (("refunding", lambda: refunding_view(d, eng)), ("funding", lambda: funding_view(d, eng)),
                  ("basis", lambda: basis_view(d)), ("ai", ai_view)):
        try:
            out[k] = fn()
        except Exception:  # noqa: BLE001
            log.exception("stability view %s failed", k)
            out[k] = None
    return out


def alerts(v: Dict, today: str) -> List[tuple]:
    """(key, severity, title, detail) — keys carry an id/date so each event fires once."""
    out = []
    rf = v.get("refunding") or {}
    pol = rf.get("policy") or {}
    if pol.get("url") and (pol.get("status") in ("increase", "changed", "decrease") or pol.get("changed")):
        out.append((f"stab:refund:{pol['url'].rsplit('/', 1)[-1]}", "⚠️ WARNING", f"財政部再融資聲明：標售規模說法「{rf['state']}」",
                    f"{rf['read']}\n原文：{pol.get('guidance', '')[:300]}\n{pol['url']}"))
    for nd in rf.get("next") or []:
        try:
            days = (datetime.strptime(nd, "%Y-%m-%d") - datetime.strptime(today, "%Y-%m-%d")).days
        except ValueError:
            continue
        if 0 <= days <= 1:
            out.append((f"stab:qrdate:{nd}", "ℹ️ INFO", f"{'明天' if days else '今天'}：財政部公布季度再融資文件（{nd}）",
                        "借款估算在美東 15:00、標售規模聲明在美東 8:30 公布；本站會自動比對「維持標售規模」那句話有沒有改口。"))
    fu = v.get("funding") or {}
    if fu.get("state") in ("偏緊", "緊繃"):
        wk = datetime.strptime(fu["date"], "%Y-%m-%d").strftime("%G-W%V")
        out.append((f"stab:funding:{fu['state']}:{wk}", "⚠️ WARNING" if fu["state"] == "緊繃" else "ℹ️ INFO",
                    f"短期資金市場{fu['state']}：SOFR {fu['sofr']:.2f}%" + (f"，比準備金利率 {fu['spread']:+.0f}bp" if fu.get("spread") is not None else ""),
                    fu["read"]))
    ba = v.get("basis") or {}
    if ba.get("record") or (ba.get("pct") or 0) >= 98 and ba.get("net", 0) > ba.get("hi52", 0):
        out.append((f"stab:basis:{ba['date']}", "ℹ️ INFO", f"美債基差交易規模創{'歷史' if ba.get('record') else ' 52 週'}新高：槓桿基金淨空單 ${ba['net']:,.0f}B",
                    ba.get("read", "")))
    cv = v.get("coverage") or {}
    if cv.get("updated") and cv.get("gaps"):
        gl = "\n".join(f"・{g.get('risk', '')}（{g.get('source', '')}）：{g.get('suggest', '')}" for g in cv["gaps"][:6])
        out.append((f"stab:cover:{cv['updated']}", "ℹ️ INFO", f"每月監測盤點：官方報告點名、本站還沒有數據的風險 {len(cv['gaps'])} 項",
                    gl[:900] + "\n看「金融穩定監測」頁最下方的盤點卡。"))
    ai = v.get("ai") or {}
    if ai.get("ratio") and ai["ratio"] > 1:
        out.append((f"stab:ai:{max(r['end'] for r in ai['rows'])}", "ℹ️ INFO", f"AI 巨頭合計資本支出超過營業現金流（{ai['ratio']:.2f} 倍）", ai["read"]))
    return out


def summary_lines(v: Dict) -> List[str]:
    L = []
    rf, fu, ba, ai = (v.get(k) or {} for k in ("refunding", "funding", "basis", "ai"))
    if rf:
        L.append(f"{rf['emoji']} 財政部標售規模：{rf['state']}" + (f"（下次公布 {'、'.join(rf.get('next') or [])}）" if rf.get("next") else ""))
    if fu:
        L.append(f"{fu['emoji']} 短期資金：{fu['state']}・SOFR {fu['sofr']:.2f}%" + (f"（−IORB {fu['spread']:+.0f}bp）" if fu.get("spread") is not None else ""))
    if ba:
        L.append(f"{ba['emoji']} 基差交易：{ba['state']}・槓桿基金淨空單 ${ba['net']:,.0f}B（第 {ba['pct']:.0f} 百分位）")
    if ai:
        L.append(f"{ai['emoji']} AI 資本支出：{ai['state']}・資本支出／營業現金流 {ai['ratio']:.2f} 倍")
    return L
