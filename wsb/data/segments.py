"""營收曝險 — where a company's revenue comes from (geography) and how concentrated its customers are, read from
the XBRL of its latest annual report on SEC EDGAR (10-K, or 20-F / 40-F for foreign filers).

The companyfacts API leaves out dimensional facts, so the filing's own XBRL instance is parsed:
* geography: revenue facts whose context carries one geographic axis (srt:StatementGeographicalAxis,
  ifrs-full:GeographicalAreasAxis …) for the latest full fiscal year, as a share of that year's total revenue;
  when only percentages are tagged (ConcentrationRiskPercentage1 + GeographicConcentrationRiskMember) those are used.
* customers: ConcentrationRiskPercentage1 tagged CustomerConcentrationRiskMember against revenue
  (e.g. "largest customer 19 %"), else customer revenue facts on srt:MajorCustomersAxis ÷ total.
Members are labelled from their names (country:CN → 中國, klac:EuropeAndIsraelMember → Europe And Israel).
Companies tag differently — when nothing usable is tagged the result says so instead of guessing.
Cached per accession in data_cache/sec_segments.json; a refresh downloads at most `budget` new filings."""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import date
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from ..config import DATA_DIR, SEC_USER_AGENT, SETTINGS
from . import http

log = logging.getLogger(__name__)
CACHE = DATA_DIR / "sec_segments.json"
HDR = {"User-Agent": SEC_USER_AGENT, "Accept": "application/json, text/xml, */*"}
PARSER_V = 2                     # 2: customer groups ("Four Customers", region-based end customers) are not "one customer"
NS_X = "{http://www.xbrl.org/2003/instance}"
NS_D = "{http://xbrl.org/2006/xbrldi}"
REV = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
       "Revenue", "SalesRevenueNet", "RevenueFromContractsWithCustomers")
COUNTRY = {"CN": ("中國", "China"), "TW": ("台灣", "Taiwan"), "US": ("美國", "United States"), "KR": ("南韓", "South Korea"),
           "JP": ("日本", "Japan"), "SG": ("新加坡", "Singapore"), "HK": ("香港", "Hong Kong"), "DE": ("德國", "Germany"),
           "GB": ("英國", "United Kingdom"), "IE": ("愛爾蘭", "Ireland"), "NL": ("荷蘭", "Netherlands"), "IN": ("印度", "India"),
           "BR": ("巴西", "Brazil"), "MX": ("墨西哥", "Mexico"), "CA": ("加拿大", "Canada"), "FR": ("法國", "France"),
           "IL": ("以色列", "Israel"), "MY": ("馬來西亞", "Malaysia"), "VN": ("越南", "Vietnam"), "CO": ("哥倫比亞", "Colombia"),
           "CH": ("瑞士", "Switzerland"), "AU": ("澳洲", "Australia")}
WORDS = {"China": "中國", "Taiwan": "台灣", "UnitedStates": "美國", "Americas": "美洲", "NorthAmerica": "北美", "Europe": "歐洲",
         "Asia": "亞洲", "AsiaPacific": "亞太", "Japan": "日本", "Korea": "南韓", "Brazil": "巴西", "Mexico": "墨西哥",
         "EMEA": "歐非中東", "RestOfWorld": "其他地區", "RestOfAsia": "亞洲其他", "Other": "其他", "International": "國際",
         "Domestic": "本國"}


def _cfg() -> Dict:
    return {"budget": 6, "recheck_days": 7, "max_mb": 40, **(SETTINGS.get("segments", {}) or {})}


def label(member: str) -> Dict[str, str]:
    """country:CN → 中國 / China;  klac:EuropeAndIsraelMember → Europe And Israel (+ a Chinese label when known)."""
    m = re.match(r"country:([A-Z]{2})$", member or "")
    if m:
        zh, en = COUNTRY.get(m.group(1), (m.group(1), m.group(1)))
        return {"zh": zh, "en": en, "iso": m.group(1)}
    raw = (member or "").split(":")[-1]
    raw = re.sub(r"Member$", "", raw)
    zh = WORDS.get(raw)
    if zh is None:
        for k, v in WORDS.items():
            if raw.startswith(k) and len(k) >= 4:
                zh = v + ("等" if raw != k else "")
                break
    en = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", raw).strip() or raw
    return {"zh": zh or en, "en": en, "iso": None}


GROUP_WORDS = ("Customers", "Based", "EndCustomer", "UnitedStates", "Europe", "Asia", "America", "Distributors", "Others",
               "Two", "Three", "Four", "Five", "Ten", "Top")


def single_customer(member: str) -> bool:
    """A named / numbered single customer (Customer A, Largest customer, Major Customer One) — not a group or a region."""
    raw = re.sub(r"Member$", "", (member or "").split(":")[-1])
    if raw.endswith("One") and "Customer" in raw and "Customers" not in raw:
        return True
    return not any(w in raw for w in GROUP_WORDS)


def _geo_axis(d: str) -> bool:
    return "Geograph" in d


def _region_flags(mem: str, lab: Dict[str, str]) -> Dict[str, bool]:
    s = (mem + " " + lab["en"]).lower()
    return {"china": lab.get("iso") in ("CN", "HK") or "china" in s or "prc" in s,
            "taiwan": lab.get("iso") == "TW" or "taiwan" in s,
            "us": lab.get("iso") == "US" or "unitedstates" in s.replace(" ", "")}


def parse_instance(xml: bytes) -> Dict:
    """→ {"period", "total", "geo": [{member, zh, en, share}], "customers": [{member, zh, en, share}], "china", "taiwan", "us", "basis"}."""
    root = ET.fromstring(xml)
    ctx = {}
    for c in root.iter(NS_X + "context"):
        per = c.find(NS_X + "period")
        if per is None:
            continue
        st, en = per.find(NS_X + "startDate"), per.find(NS_X + "endDate")
        inst = per.find(NS_X + "instant")
        dims = {m.get("dimension"): (m.text or "").strip() for m in c.iter(NS_D + "explicitMember")}
        if st is not None and en is not None:
            ctx[c.get("id")] = (st.text.strip(), en.text.strip(), dims)
        elif inst is not None:
            ctx[c.get("id")] = (None, inst.text.strip(), dims)
    rev, conc = [], []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        cr = el.get("contextRef")
        if cr not in ctx or el.text is None:
            continue
        try:
            v = float(el.text.strip())
        except ValueError:
            continue
        if tag in REV:
            rev.append((tag, ctx[cr], v))
        elif tag == "ConcentrationRiskPercentage1":
            conc.append((ctx[cr], v))
    annual = sorted({(c[1], c[0]) for _, c, _ in rev if c[0] and 340 <= (date.fromisoformat(c[1]) - date.fromisoformat(c[0])).days <= 380})
    if not annual:
        return {"error": "沒有年度營收"}
    end, start = annual[-1]
    totals = {t: v for t, c, v in rev if c[0] == start and c[1] == end and not c[2]}
    out: Dict = {"period": end, "total": max(totals.values()) if totals else None, "geo": [], "customers": [], "basis": None}
    # geography from revenue amounts: the concept with the most single-axis geographic facts
    by_tag: Dict[str, Dict[str, float]] = {}
    for t, c, v in rev:
        if c[0] == start and c[1] == end and len(c[2]) == 1:
            ax, mem = next(iter(c[2].items()))
            if _geo_axis(ax):
                by_tag.setdefault(t, {})[mem] = v
    if by_tag:
        t = max(by_tag, key=lambda k: len(by_tag[k]))
        tot = totals.get(t) or out["total"]
        if tot:
            out["basis"] = "amount"
            out["geo"] = [{"member": m, **label(m), "share": v / tot} for m, v in by_tag[t].items() if v > 0]
    if not out["geo"]:                                   # percentages only
        for c, v in conc:
            if c[1] != end or len(c[2]) != 3:
                continue
            ax = [a for a in c[2] if _geo_axis(a)]
            if ax and "Geographic" in c[2].get("us-gaap:ConcentrationRiskByTypeAxis", "") and "Revenue" in c[2].get("us-gaap:ConcentrationRiskByBenchmarkAxis", ""):
                m = c[2][ax[0]]
                out["geo"].append({"member": m, **label(m), "share": v if v <= 1.0 else v / 100})
        if out["geo"]:
            out["basis"] = "percent"
    # a parent region and its own sub-countries can both be tagged: keep the leaves when they nearly add up
    out["geo"].sort(key=lambda g: -g["share"])
    for c, v in conc:
        if c[1] != end:
            continue
        typ, bench = c[2].get("us-gaap:ConcentrationRiskByTypeAxis", ""), c[2].get("us-gaap:ConcentrationRiskByBenchmarkAxis", "")
        if "Customer" in typ and "Revenue" in bench:
            mem = next((m for a, m in c[2].items() if a not in ("us-gaap:ConcentrationRiskByTypeAxis", "us-gaap:ConcentrationRiskByBenchmarkAxis")), "")
            sh = v if v <= 1.0 else v / 100
            if mem and 0 < sh < 1 and single_customer(mem):
                out["customers"].append({"member": mem, **label(mem), "share": sh})
    if not out["customers"] and out["total"]:
        for t, c, v in rev:
            if c[0] == start and c[1] == end and len(c[2]) == 1 and "MajorCustomers" in next(iter(c[2])):
                m = next(iter(c[2].values()))
                if single_customer(m):
                    out["customers"].append({"member": m, **label(m), "share": v / out["total"]})
    seen, cust = set(), []
    for x in sorted(out["customers"], key=lambda x: -x["share"]):
        if x["member"] not in seen:
            seen.add(x["member"])
            cust.append(x)
    out["customers"] = cust[:5]
    for k in ("china", "taiwan", "us"):                  # None = not broken out (e.g. only "North America"), never a fake 0 %
        hit = [g["share"] for g in out["geo"] if _region_flags(g["member"], g)[k]]
        out[k] = round(sum(hit), 4) if hit else None
    for g in out["geo"] + out["customers"]:
        g["share"] = round(g["share"], 4)
    if not out["geo"] and not out["customers"]:
        out["note"] = "年報沒有用標準標籤揭露地區或客戶營收"
    return out


# ------------------------------------------------------------------ EDGAR plumbing
def load() -> Dict[str, Dict]:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save(d: Dict) -> None:
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE)


async def _latest_annual(cik: int) -> Optional[Dict]:
    sub = await http.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", headers=HDR, timeout=30, retries=1)
    r = (sub or {}).get("filings", {}).get("recent", {})
    for i, f in enumerate(r.get("form", [])):
        if f in ("10-K", "20-F", "40-F"):
            return {"acc": r["accessionNumber"][i], "form": f, "filed": r["filingDate"][i]}
    return None


async def _instance(cik: int, acc: str, max_mb: float) -> Optional[bytes]:
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/"
    idx = await http.get(base + "index.json", headers=HDR, timeout=30, retries=1)
    items = (idx or {}).get("directory", {}).get("item", [])
    xs = [x for x in items if x["name"].endswith(".xml") and not re.search(r"_(cal|def|lab|pre)\.xml$|FilingSummary", x["name"])]
    if not xs:
        return None
    x = max(xs, key=lambda x: int(x.get("size") or 0))
    if int(x.get("size") or 0) > max_mb * 1e6:
        return None
    return await http.get(base + x["name"], kind="bytes", headers=HDR, timeout=120, retries=1)


async def refresh(symbols: Dict[str, int], budget: Optional[int] = None, time_budget_s: float = 120) -> Dict[str, Dict]:
    """symbols: {ticker: cik}.  Re-checks each company's latest annual filing every `recheck_days`; parses new ones."""
    c = _cfg()
    budget = int(budget if budget is not None else c["budget"])
    cache = load()
    t0, done = time.time(), 0
    order = sorted(symbols, key=lambda s: (cache.get(s, {}).get("checked", 0)))      # least recently checked first
    for sym in order:
        if done >= budget or time.time() - t0 > time_budget_s:
            break
        rec = cache.get(sym) or {}
        if rec.get("v") == PARSER_V and time.time() - rec.get("checked", 0) < c["recheck_days"] * 86400:
            continue
        try:
            la = await _latest_annual(int(symbols[sym]))
            if not la:
                cache[sym] = {"v": PARSER_V, "checked": time.time(), "error": "沒有 10-K／20-F"}
                continue
            if rec.get("acc") == la["acc"] and rec.get("v") == PARSER_V:
                rec["checked"] = time.time()
                cache[sym] = rec
                continue
            xml = await _instance(int(symbols[sym]), la["acc"], c["max_mb"])
            done += 1
            parsed = parse_instance(xml) if xml else {"error": "找不到 XBRL"}
            cache[sym] = {"v": PARSER_V, "checked": time.time(), **la, **parsed}
        except Exception as e:  # noqa: BLE001
            log.debug("segments %s: %s", sym, e)
            cache[sym] = {**rec, "checked": time.time() - (c["recheck_days"] - 1) * 86400}       # retry tomorrow
    save(cache)
    return cache


def public(cache: Dict[str, Dict]) -> Dict[str, Dict]:
    """Compact per-ticker view for pages and the bot."""
    out = {}
    for s, r in cache.items():
        if r.get("geo") or r.get("customers"):
            out[s] = {"period": r.get("period"), "form": r.get("form"), "china": r.get("china"), "taiwan": r.get("taiwan"),
                      "us": r.get("us"), "basis": r.get("basis"),
                      "geo": [[g["zh"], g["en"], g["share"]] for g in r["geo"][:8]],
                      "cust": [[g["zh"], g["en"], g["share"]] for g in r.get("customers", [])[:3]]}
    return out


async def refresh_for(tickers, time_budget_s: float = 120) -> Dict[str, Dict]:
    """tickers → CIKs via the SEC ticker map (class shares like BRK.B use the dash form), then refresh()."""
    from .edgar_holdings import ticker_map
    tm = await ticker_map()
    syms = {}
    for t in tickers:
        k = str(t).upper()
        hit = tm.get(k) or tm.get(k.replace(".", "-"))
        if hit:
            syms[k] = int(hit["cik"])
    return await refresh(syms, time_budget_s=time_budget_s)
