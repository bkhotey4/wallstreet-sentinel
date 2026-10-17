"""Company earnings releases from SEC EDGAR (8-K item 2.02 / 6-K): this quarter's reported numbers, the company's own
guidance for next quarter / the year, capex, and how this quarter landed against the guidance it gave last time.

Source is the company's filing itself (press release, CFO commentary, earnings presentation), never news.  Parsing is
pattern-based and conservative: a number is kept only when its metric, unit and (for guidance) the word "expect…" are
in the same sentence; anything ambiguous is left out rather than guessed.  Each kept item carries the sentence it came
from, so the page can show the company's own words next to the number."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR, SEC_USER_AGENT
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_release.json"            # earn_* is kept by the site workflow's cache
HDR = {"User-Agent": SEC_USER_AGENT}

_NUM = r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
_CUR = r"(US\$|NT\$|\$|€|£|¥)"
_UNIT = r"\s*(billion|million|bn)\b"
MONEY_RANGE = re.compile(_CUR + r"\s?" + _NUM + r"(?:" + _UNIT + r")?\s*(?:and|to|-)\s*" + _CUR + r"?\s?" + _NUM + _UNIT, re.I)
MONEY_PM = re.compile(_CUR + r"\s?" + _NUM + _UNIT + r",?\s*plus or minus\s*" + _NUM + r"\s*%", re.I)
MONEY_PM_ABS = re.compile(_CUR + r"\s?" + _NUM + _UNIT + r",?\s*plus or minus\s*" + _CUR + r"?\s?" + _NUM + _UNIT, re.I)
MONEY_ONE = re.compile(r"(?:around|approximately|about|of|be|at)?\s*" + _CUR + r"\s?" + _NUM + _UNIT, re.I)
PCT_RANGE = re.compile(_NUM + r"\s*(?:%|percent)?\s*(?:and|to|-)\s*" + _NUM + r"\s*(?:%|percent)", re.I)
PCT_PM = re.compile(_NUM + r"\s*%,?\s*plus or minus\s*" + _NUM + r"\s*(basis points|bps|%)", re.I)
PCT_ONE = re.compile(_NUM + r"\s*(?:%|percent)", re.I)
METRICS = [("gross_margin", re.compile(r"gross (?:profit )?margins?", re.I), "pct"),
           ("op_margin", re.compile(r"operating (?:profit )?margins?", re.I), "pct"),
           ("opex", re.compile(r"operating expenses", re.I), "money"),
           ("capex", re.compile(r"capital (?:expenditures?|spending|budget)|\bcapex\b", re.I), "money"),
           ("revenue", re.compile(r"\b(?:total net sales|net sales|net revenues?|revenues?)\b", re.I), "money")]
EXPECT = re.compile(r"\b(?:expects?|expected|expecting|anticipates?|forecasts?|projects?)\b|\boutlook (?:for|is)\b|\bguidance (?:for|is)\b", re.I)
QUARTER = re.compile(r"\b(?:Q[1-4]|[1-4]Q(?:\d\d)?|(?:first|second|third|fourth)[- ]quarter|next quarter)\b", re.I)
FULLYEAR = re.compile(r"full[- ]year|\bfor (?:fiscal (?:year )?)?20\d\d\b(?!\s+(?:first|second|third|fourth))|\b20\d\d (?:total )?(?:net sales|revenues?|capital expenditures|capex|operating expenses)|\bannual\b|fiscal (?:year )?20\d\d\b(?!\s+(?:first|second|third|fourth))", re.I)
GROWTH = re.compile(r"(?:increase|grow|growth|decline|decrease|up|down)\w*\s+(?:by\s+)?(?:around|approximately|about|mid-|high-|low-)?\s*" + _NUM + r"\s*%", re.I)
LABEL = {"revenue": ("營收", "Revenue"), "gross_margin": ("毛利率", "Gross margin"), "op_margin": ("營業利益率", "Operating margin"),
         "opex": ("營業費用", "Opex"), "capex": ("資本支出", "Capex"), "revenue_growth": ("營收成長", "Revenue growth")}


def _f(x: str) -> float:
    return float(x.replace(",", ""))


def _cur(c: Optional[str]) -> str:
    return {"$": "USD", "US$": "USD", "NT$": "TWD", "€": "EUR", "£": "GBP", "¥": "JPY"}.get((c or "").upper().replace("US$", "US$"), c or "")


def _scale(v: float, unit: Optional[str]) -> float:
    """→ billions"""
    u = (unit or "").lower()
    return v / 1000 if u == "million" else v


def clean(text: str) -> str:
    t = text.replace("–", "-").replace("—", "-").replace("−", "-").replace("\xa0", " ")
    t = t.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", t).strip()


def segments(text: str) -> List[str]:
    parts = re.split(r"\s*[•▪●■]\s*|;\s+|(?<=[a-z0-9%)\]])\.\s+(?=[A-Z\"(])", clean(text))
    return [p.strip() for p in parts if len(p.strip()) > 8]


def _money(s: str) -> Optional[Dict]:
    m = MONEY_RANGE.search(s)
    if m:
        lo, hi = _scale(_f(m.group(2)), m.group(3) or m.group(6)), _scale(_f(m.group(5)), m.group(6))
        if lo > hi * 1.0001:                           # "approximately $9.2 billion and $9.0 billion, respectively"
            return {"lo": lo, "hi": lo, "cur": _cur(m.group(1)), "single": True, "m": m}
        return {"lo": lo, "hi": hi, "cur": _cur(m.group(1)), "m": m}
    m = MONEY_PM_ABS.search(s)
    if m:                                      # "$13 billion, plus or minus $300 million"
        v, w = _scale(_f(m.group(2)), m.group(3)), _scale(_f(m.group(5)), m.group(6))
        return {"lo": v - w, "hi": v + w, "cur": _cur(m.group(1)), "m": m}
    m = MONEY_PM.search(s)
    if m:
        v, p = _scale(_f(m.group(2)), m.group(3)), _f(m.group(4)) / 100
        return {"lo": v * (1 - p), "hi": v * (1 + p), "cur": _cur(m.group(1)), "m": m}
    m = MONEY_ONE.search(s)
    if m:
        v = _scale(_f(m.group(2)), m.group(3))
        return {"lo": v, "hi": v, "cur": _cur(m.group(1)), "single": True, "m": m}
    return None


def _pct(s: str) -> Optional[Dict]:
    if re.search(r"respectively", s, re.I):
        m = PCT_ONE.search(s)
        return {"lo": _f(m.group(1)), "hi": _f(m.group(1)), "single": True, "m": m} if m else None
    m = PCT_PM.search(s)
    if m:
        v, w = _f(m.group(1)), _f(m.group(2))
        w = w / 100 if m.group(3).lower().startswith(("basis", "bp")) else w
        return {"lo": v - w, "hi": v + w, "m": m}
    m = PCT_RANGE.search(s)
    if m and _f(m.group(1)) <= _f(m.group(2)) and _f(m.group(2)) - _f(m.group(1)) < 15:
        return {"lo": _f(m.group(1)), "hi": _f(m.group(2)), "m": m}
    m = PCT_ONE.search(s)
    if m:
        return {"lo": _f(m.group(1)), "hi": _f(m.group(1)), "single": True, "m": m}
    return None


def _metric_spans(s: str) -> List[Tuple[int, str, str]]:
    hits = []
    for name, rx, kind in METRICS:
        for m in rx.finditer(s):
            if name == "revenue" and any(a <= m.start() < b for a, b in [(h[3], h[4]) for h in hits]):
                continue
            hits.append((m.start(), name, kind, m.start(), m.end()))
    hits.sort()
    # drop revenue hits that sit inside a longer metric phrase already found at the same place
    out, last_end = [], -1
    for h in hits:
        if h[0] < last_end:
            continue
        out.append(h)
        last_end = h[4]
    return [(h[0], h[1], h[2]) for h in out]


def guidance(text: str) -> List[Dict]:
    """Forward-looking numbers, one per (metric, period), with the sentence they came from."""
    out: Dict[Tuple[str, str], Dict] = {}
    carry = 0                                              # bullets after "management expects:" inherit the expectation
    lead_period = None
    for s in segments(text):
        lead = bool(EXPECT.search(s)) and s.rstrip().endswith(":")
        if lead:
            carry = 6
            lead_period = ("year" if re.search(r"full[- ]year|fiscal (?:year )?20\d\d\b(?!\s+(?:first|second|third|fourth))|\bannual\b|\bfor 20\d\d\b", s, re.I)
                           and not QUARTER.search(s) else "next_q" if QUARTER.search(s) else None)
            continue
        if carry == 0:
            lead_period = None
        inherited = carry > 0 and not EXPECT.search(s)
        carry = max(0, carry - 1)
        if not (EXPECT.search(s) or inherited) or re.search(r"\b(?:was|were|came in)\b[^.]{0,40}\bguidance\b", s, re.I):
            continue
        if re.search(r"tax rate|share count|dividend", s, re.I) and not re.search(r"revenue|sales|margin", s, re.I):
            continue
        if len(s) > 480:                                   # a table dump / long paragraph, not a guidance sentence
            continue
        e = EXPECT.search(s).start() if EXPECT.search(s) else 0
        win = s[e:e + 160]                                 # the forward-looking clause decides first: a headline glued to
        period = ("year" if FULLYEAR.search(win) and not QUARTER.search(win[:60])   # "…second-quarter results" must not turn
                  else "next_q" if QUARTER.search(win)          # "expects 2026 total net sales" into next-quarter guidance
                  else "year" if re.search(r"full[- ]year|\bannual\b", s, re.I) else "next_q" if QUARTER.search(s)
                  else "year" if FULLYEAR.search(s) else (lead_period if inherited and lead_period else "next_q"))
        spans = _metric_spans(s)
        for i, (pos, name, kind) in enumerate(spans):
            if pos < e - 120:                              # the metric must belong to the forward-looking clause
                continue
            end = spans[i + 1][0] if i + 1 < len(spans) else len(s)
            local = s[max(0, pos - 60):pos + 30]
            per = ("year" if re.search(r"full[- ]year|\bannual\b", local, re.I) or FULLYEAR.search(local) and not QUARTER.search(local)
                   else "next_q" if QUARTER.search(local) else period)
            if name == "capex" and not QUARTER.search(local):
                per = "year"                               # capex guidance is an annual budget unless a quarter is named
            start = max(pos, e)                            # the number must come after "expect…"
            seg = s[start:min(end, start + 170)] if end > start else ""
            v = _money(seg) if kind == "money" else _pct(seg)
            nm = name
            if name == "revenue" and v is None:
                g = GROWTH.search(seg)
                if g:
                    v, nm = {"lo": _f(g.group(1)), "hi": _f(g.group(1)), "single": True}, "revenue_growth"
                    if re.search(r"declin|decreas|down", g.group(0), re.I):
                        v["lo"] = v["hi"] = -v["lo"]
            if not v:
                continue
            k = (nm, per)
            if k in out:
                continue
            basis = "ng" if (re.search(r"non-?\s?GAAP", local, re.I) and not re.search(r"GAAP and non-?\s?GAAP", s, re.I)) else "g"
            out[k] = {"metric": nm, "period": per, "basis": basis if nm in ("gross_margin", "op_margin") else "g", "lo": round(v["lo"], 4), "hi": round(v["hi"], 4),
                      "mid": round((v["lo"] + v["hi"]) / 2, 4), "single": bool(v.get("single")),
                      "cur": v.get("cur") if (kind == "money" and nm != "revenue_growth") else None,
                      "unit": "B" if (kind == "money" and nm != "revenue_growth") else "%",
                      "text": s[max(0, min(pos, e) - 20):max(pos, e) + 260].strip()}
    return list(out.values())


ACT_REV = re.compile(r"(?:revenues?|net sales)\b(?:[^$€.]{0,60}?)\b(?:was|were|of|totaled|reached|came in at)\s+(?:a record\s+)?(?:approximately\s+)?" + _CUR + r"\s?" + _NUM + _UNIT, re.I)
ACT_GM = re.compile(r"gross (?:profit )?margins?\b(?:[^%.]{0,40}?)\b(?:was|were|of|came in at)\s+(?:both\s+)?" + _NUM + r"\s*%", re.I)
ACT_OM = re.compile(r"operating (?:profit )?margins?\b(?:[^%.]{0,40}?)\b(?:was|were|of|came in at)\s+(?:both\s+)?" + _NUM + r"\s*%", re.I)
CAPEX_ROW = re.compile(r"capital expenditures?\s*\(\s*\$?\s?" + _NUM + r"\s*\)", re.I)
UNIT_HDR = re.compile(r"\((?:in|In) (NT\$|US\$|\$|€|euros?|millions? of (?:euros|dollars|U\.S\. dollars))?\s*(billions|millions)?[^)]{0,40}\)", re.I)


FWD_WORDS = re.compile(r"in the range of|\bexpect|\banticipat|\boutlook\b|\bguidance\b|\bforecast|plus or minus|\bbetween\b", re.I)


def _sentence(t: str, a: int, b: int) -> str:
    """The sentence / bullet around t[a:b]."""
    back = t[max(0, a - 220):a]
    cut = max(back.rfind("•"), back.rfind("▪"), back.rfind(";"), back.rfind(". "))
    fwd = t[b:b + 120]
    ends = [i for i in (fwd.find("•"), fwd.find("▪"), fwd.find(";"), fwd.find(". ")) if i >= 0]
    return back[cut + 1:] + t[a:b] + fwd[:min(ends) if ends else len(fwd)]


def _in_outlook_list(t: str, a: int) -> bool:
    """True when position `a` sits in a bullet list introduced by a forward-looking line ending in ':'."""
    back = t[max(0, a - 900):a]
    k = back.rfind(":")
    while k >= 0:
        if EXPECT.search(back[max(0, k - 160):k]):
            rest = back[k + 1:]
            return rest.count("•") + rest.count("▪") <= 6 and bool(re.match(r"\s*[•▪]", rest))
        k = back.rfind(":", 0, k)
        if k >= 0 and len(back) - k > 900:
            break
    return False


def actuals(text: str) -> Dict[str, Dict]:
    """This quarter's reported numbers (first statement of each kind; revenue kept per currency)."""
    t = clean(text)
    out: Dict[str, Dict] = {}
    revs: Dict[str, Dict] = {}
    for m in ACT_REV.finditer(t):
        pre = t[max(0, m.start() - 60):m.start()].lower()
        if re.search(r"data center|segment|gaming|automotive|cloud|installed base", pre + t[m.start():m.start() + 30].lower()):
            continue                                             # a segment line, not the total
        if FWD_WORDS.search(_sentence(t, m.start(), m.end())) or _in_outlook_list(t, m.start()):
            continue                                             # an outlook bullet ("in the range of …"), not this quarter
        c = _cur(m.group(1))
        if c not in revs:
            raw = m.group(2).replace(",", "")
            dec = len(raw.split(".")[1]) if "." in raw else 0
            step = 10 ** -dec / (1000 if (m.group(3) or "").lower() == "million" else 1)
            revs[c] = {"v": round(_scale(_f(m.group(2)), m.group(3)), 4), "cur": c, "step": step,
                       "text": t[max(0, m.start() - 80):m.end() + 20]}
    if revs:
        out["revenue"] = revs
    for key, rx in (("gross_margin", ACT_GM), ("op_margin", ACT_OM)):
        for m in rx.finditer(t):
            ctx = t[max(0, m.start() - 160):m.end() + 40]
            if FWD_WORDS.search(_sentence(t, m.start(), m.end())) or _in_outlook_list(t, m.start()):
                continue                                         # forward-looking sentence / outlook list → not an actual
            pre = t[max(0, m.start() - 45):m.end()].lower()
            both = "gaap and non-gaap" in pre or "both" in m.group(0).lower()
            ng = re.search(r"non-?\s?gaap", pre) and not both
            raw = m.group(1)
            rec = {"v": _f(raw), "step": 10 ** -(len(raw.split(".")[1]) if "." in raw else 0), "text": ctx}
            if ng:
                out.setdefault(key + "_ng", rec)
            else:
                out.setdefault(key, rec)
                if both:
                    out.setdefault(key + "_ng", rec)
            if key in out and key + "_ng" in out:
                break
    for m in CAPEX_ROW.finditer(t):
        hdrs = list(UNIT_HDR.finditer(t[max(0, m.start() - 2500):m.start()]))
        if not hdrs:
            continue
        h = hdrs[-1]
        cur_s = (h.group(0) or "").lower()
        doc_cur = next(iter(revs), "USD") if revs else "USD"
        cur = ("TWD" if "nt$" in cur_s else "EUR" if ("eur" in cur_s or "€" in cur_s)
               else "USD" if ("$" in cur_s or "dollar" in cur_s) else doc_cur)
        unit = (h.group(2) or ("millions" if "million" in cur_s else "")).lower()
        if not unit:
            continue
        v = _f(m.group(1)) / (1000 if unit.startswith("million") else 1)
        # only the first column is used: whether the next one is last quarter or last year differs by company
        out["capex"] = {"v": round(v, 4), "cur": cur, "text": t[max(0, m.start() - 20):m.end() + 40]}
        break
    return out


def parse(text: str) -> Dict:
    return {"actual": actuals(text), "guide": guidance(text)}


def compare(actual: Dict, prev_guide: List[Dict]) -> List[Dict]:
    """How this quarter landed vs the next-quarter guidance the company gave last time."""
    out = []
    for g in prev_guide or []:
        if g["period"] != "next_q":
            continue
        a = actual.get(g["metric"] + ("_ng" if g.get("basis") == "ng" else ""))
        if g["metric"] == "revenue":
            a = (a or {}).get(g.get("cur") or "")
        if not a:
            continue
        v = a["v"]
        if g["unit"] == "B" and g["mid"] and abs(v / g["mid"] - 1) > 0.4:
            continue                                       # not the same period (e.g. a full-year figure) → no comparison
        tol = (0.25 if g["unit"] == "%" else g["mid"] * 0.01) if g.get("single") else 1e-9
        tol = max(tol, a.get("step", 0) / 2)               # a rounded figure ("$3.3 billion", "54%") gets half a digit
        pos = "above" if v > g["hi"] + tol else "below" if v < g["lo"] - tol else "within"
        out.append({"metric": g["metric"], "actual": v, "lo": g["lo"], "hi": g["hi"], "cur": g.get("cur"), "pos": pos,
                    "single": bool(g.get("single")), "basis": g.get("basis", "g"),
                    "vs_mid": round((v / g["mid"] - 1) * 100, 2) if g["unit"] == "B" and g["mid"] else round(v - g["mid"], 2)})
    return out


def outlook_vs_now(actual: Dict, guide: List[Dict]) -> List[Dict]:
    """Next-quarter guidance midpoint vs this quarter's actual (implied QoQ change / margin change)."""
    out = []
    for g in guide:
        if g["period"] != "next_q":
            continue
        a = actual.get(g["metric"] + ("_ng" if g.get("basis") == "ng" else ""))
        if g["metric"] == "revenue":
            a = (a or {}).get(g.get("cur") or "")
        if not a:
            continue
        chg = (g["mid"] / a["v"] - 1) * 100 if g["unit"] == "B" else g["mid"] - a["v"]
        out.append({"metric": g["metric"], "mid": g["mid"], "now": a["v"], "chg": round(chg, 2), "unit": g["unit"], "cur": g.get("cur")})
    return out


# ------------------------------------------------------------------------------------------------ EDGAR fetching
_SKIP_DOC = re.compile(r"index|^R\d+\.htm|\.xsd$|_(?:lab|pre|cal|def)\.xml$|FilingSummary|MetaLinks", re.I)


async def _docs(url: str, primary: str) -> List[Tuple[str, str]]:
    idx = await http.get(url + "index.json", headers=HDR, timeout=25, retries=1)
    names = [f["name"] for f in idx.get("directory", {}).get("item", [])
             if f["name"].lower().endswith((".htm", ".html", ".txt")) and not _SKIP_DOC.search(f["name"])
             and not re.fullmatch(r"\d{10}-\d{2}-\d{6}\.txt", f["name"])]
    ex = [n for n in names if n != primary] or names              # exhibits first; the cover page only if nothing else
    out = []
    for n in ex[:4]:
        await asyncio.sleep(0.12)                                  # SEC fair access
        try:
            html = await http.get(url + n, headers=HDR, kind="text", timeout=30, retries=1)
        except Exception as e:  # noqa: BLE001
            log.info("EDGAR doc %s failed: %s", n, e)
            continue
        from .sec import _html_to_text
        out.append((n, _html_to_text(html)[:120000]))
    return out


_SUBS: Dict[str, Tuple[float, List[Dict]]] = {}


async def filings(sec, sym: str) -> List[Dict]:
    """All recent 8-K / 6-K filings of a company (the full 'recent' list, not just the last 25 of any form)."""
    hit = _SUBS.get(sym)
    if hit and time.time() - hit[0] < 600:
        return hit[1]
    await sec._load_map()
    cik = sec.cik.get(sym.upper().replace(".", "-"))
    if not cik:
        return []
    js = await http.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HDR, timeout=30, retries=1)
    r = js.get("filings", {}).get("recent", {})
    n = len(r.get("form", []))
    col = lambda k: (r.get(k) or [""] * n)  # noqa: E731
    out = []
    for form, dt, acc, items, doc in zip(col("form"), col("filingDate"), col("accessionNumber"), col("items"), col("primaryDocument")):
        if form in ("8-K", "6-K"):
            out.append({"form": form, "date": dt, "acc": acc, "items": items, "doc": doc,
                        "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/"})
    _SUBS[sym] = (time.time(), out)
    return out


def _is_release(form: str, items: str, names_text: str) -> bool:
    if form == "8-K":
        return "2.02" in (items or "")
    t = names_text.lower()
    return bool(re.search(r"quarter|results|earnings|net sales|revenue", t) and re.search(r"margin|eps|earnings per", t))


async def find_release(sec, sym: str, d: str, lo_days: int = 3, hi_days: int = 4) -> Optional[Dict]:
    """The earnings filing for a report on US date `d` (8-K 2.02, or a 6-K whose documents read like results)."""
    items = await filings(sec, sym)
    a = (date.fromisoformat(d) - timedelta(days=lo_days)).isoformat()
    b = (date.fromisoformat(d) + timedelta(days=hi_days)).isoformat()
    for it in items:
        if it["form"] not in ("8-K", "6-K") or not (a <= it["date"] <= b):
            continue
        if it["form"] == "8-K" and "2.02" not in (it.get("items") or ""):
            continue
        docs = await _docs(it["url"], it.get("doc") or "")
        text = " ".join(t for _n, t in docs)
        if not _is_release(it["form"], it.get("items") or "", text[:20000]):
            continue
        return {"acc": it["acc"], "form": it["form"], "date": it["date"], "url": it["url"], "docs": [n for n, _ in docs], "text": text}
    return None


async def find_previous(sec, sym: str, before: str, hint: Optional[str] = None) -> Optional[Dict]:
    """The earnings filing about one quarter earlier (for 'actual vs the guidance given last time').
    `hint` = the previous report date from the earnings calendar; without it, the first earlier release that
    actually contains guidance is used."""
    if hint:
        rel = await find_release(sec, sym, hint)
        if rel and guidance(rel["text"]):
            return {"acc": rel["acc"], "date": rel["date"], "text": rel["text"], "form": rel["form"]}
    items = await filings(sec, sym)
    lo = (date.fromisoformat(before) - timedelta(days=130)).isoformat()
    hi = (date.fromisoformat(before) - timedelta(days=45)).isoformat()
    tried = 0
    for it in items:
        if lo <= it["date"] <= hi and (it["form"] == "6-K" or "2.02" in (it.get("items") or "")):
            tried += 1
            if tried > 4:
                break
            docs = await _docs(it["url"], it.get("doc") or "")
            text = " ".join(t for _n, t in docs)
            if _is_release(it["form"], it.get("items") or "", text[:20000]) and guidance(text):
                return {"acc": it["acc"], "date": it["date"], "text": text, "form": it["form"]}
    return None


def load() -> Dict[str, Dict]:
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save(d: Dict[str, Dict]) -> None:
    try:
        keep = dict(sorted(d.items(), key=lambda kv: kv[1].get("date", ""))[-300:])
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(keep, ensure_ascii=False), encoding="utf-8")
        tmp.replace(FILE)
    except OSError as e:
        log.warning("earnings release cache not saved: %s", e)


def sanitize(actual: Dict, guide: List[Dict], ref: Optional[float], form: str) -> Tuple[Dict, List[Dict]]:
    """Drop numbers that cannot be right.  `ref` = last known quarterly revenue in US$ billions (SEC XBRL), if any.
    - US revenue far from the reference is a segment or annual figure → dropped.  Without a reference, an 8-K's
      revenue is not shown at all (too easy to pick up a segment line); 6-K filers keep theirs (checked by currency).
    - next-quarter revenue guidance must be 0.75–1.5× the quarter; 2.5–5.5× is a full-year figure; else dropped."""
    actual = {k: (dict(v) if k == "revenue" else v) for k, v in actual.items()}
    rv = actual.get("revenue") or {}
    if "USD" in rv:
        v = rv["USD"]["v"]
        if (ref and not (0.7 * ref <= v <= 1.45 * ref)) or (not ref and form == "8-K"):
            rv.pop("USD")
    if not rv:
        actual.pop("revenue", None)
    out = []
    for g in guide:
        g = dict(g)
        if g["metric"] == "revenue" and g.get("unit") == "B":
            base = ((actual.get("revenue") or {}).get(g.get("cur") or "") or {}).get("v")
            if base is None and g.get("cur") == "USD":
                base = ref
            if base:
                r = g["mid"] / base
                if g["period"] == "next_q" and not (0.75 <= r <= 1.5):
                    if 2.5 <= r <= 5.5:
                        g["period"] = "year"
                    else:
                        continue
                if g["period"] == "year" and not (3.0 <= r <= 5.0):
                    continue
            elif g.get("cur") == "USD" and form == "8-K":
                continue                                   # no way to check it → leave it out
        out.append(g)
    seen, uniq = set(), []
    for g in out:                                          # a reclassified item may now duplicate one already there
        k = (g["metric"], g["period"])
        if k not in seen:
            seen.add(k)
            uniq.append(g)
    return actual, uniq


PARSER_V = 2          # bump when parsing changes: cached records of the last 120 days are rebuilt


def build_record(sym: str, d: str, rel: Dict, prev: Optional[Dict], ref: Optional[float] = None) -> Dict:
    p = parse(rel["text"])
    p["actual"], p["guide"] = sanitize(p["actual"], p["guide"], ref, rel.get("form", ""))
    pg = sanitize({}, guidance(prev["text"]), ref, prev.get("form", rel.get("form", "")))[1] if prev else []
    return {"sym": sym, "date": d, "acc": rel["acc"], "form": rel["form"], "filed": rel["date"], "url": rel["url"], "docs": rel["docs"],
            "actual": p["actual"], "guide": p["guide"], "prev_guide": pg, "prev_date": prev["date"] if prev else None,
            "vs_prev_guide": compare(p["actual"], pg), "outlook_vs_now": outlook_vs_now(p["actual"], p["guide"]),
            "excerpt": clean(rel["text"])[:9000], "ts": time.time(), "pv": PARSER_V}


async def refresh(eng, want: List[Tuple[str, str]], budget_s: float = 120) -> int:
    """Fetch the filings for (symbol, US report date) pairs not cached yet.  Not-found is retried every 2 h for 5 days."""
    from .sec import SecWatcher
    sec = getattr(eng, "sec", None) or SecWatcher()
    cache = load()
    t_end = time.monotonic() + budget_s
    n = 0
    for sym, d in want:
        if time.monotonic() > t_end:
            break
        k = f"{sym}|{d}"
        c = cache.get(k) or {}
        if c.get("acc") and (c.get("pv", 1) >= PARSER_V or (date.today() - date.fromisoformat(d)).days > 120):
            continue
        age_d = (date.today() - date.fromisoformat(d)).days
        if c.get("missing") and (time.time() - c.get("ts", 0) < (1200 if age_d <= 2 else 7200) or age_d > 5):
            continue
        try:
            rel = await find_release(sec, sym, d)
            if not rel:
                cache[k] = {"sym": sym, "date": d, "missing": True, "ts": time.time()}
                continue
            ed = getattr(eng, "earnings", None)
            past = sorted(q["date"] for q in (((getattr(ed, "surprise", None) or {}).get(sym) or {}).get("rows") or [])
                          if q.get("date") and q["date"] < (date.fromisoformat(d) - timedelta(days=30)).isoformat())
            prev = await find_previous(sec, sym, d, past[-1] if past else None)
            fq = sorted((q for q in ((((getattr(ed, "facts", None) or {}).get(sym) or {}).get("q")) or [])
                         if q.get("rev") and q.get("end") and q["end"] < d), key=lambda q: q["end"])
            ref = fq[-1]["rev"] / 1e9 if fq else None
            cache[k] = build_record(sym, d, rel, prev, ref)
            n += 1
        except Exception as e:  # noqa: BLE001
            log.info("earnings release %s %s: %s", sym, d, e)
    save(cache)
    return n


CUR_SIGN = {"USD": "US$", "TWD": "NT$", "EUR": "€", "GBP": "£", "JPY": "¥"}


def fmt_val(metric: str, v: float, cur: Optional[str] = None) -> str:
    if metric in ("revenue", "opex", "capex"):
        return f"{CUR_SIGN.get(cur or '', cur or '')}{v:,.2f}B"
    return f"{v:.1f}%"


def fmt_range(g: Dict) -> str:
    if g.get("single") or abs(g["hi"] - g["lo"]) < 1e-9:
        if g["metric"] == "revenue_growth":
            return f"約 {g['mid']:+.1f}%"
        return "約 " + fmt_val(g["metric"], g["mid"], g.get("cur"))
    if g["unit"] == "%":
        return f"{g['lo']:.1f}%–{g['hi']:.1f}%"
    return f"{fmt_val(g['metric'], g['lo'], g.get('cur'))}–{g['hi']:,.2f}B"


POS = {"above": "高於指引上緣", "within": "落在指引區間內", "below": "低於指引下緣"}


def summary_lines(rec: Dict) -> List[str]:
    """Plain-language key points from a parsed release (numbers only, each traceable to the filing)."""
    L = []
    a = rec.get("actual") or {}
    rv = a.get("revenue") or {}
    head = []
    for c in ("USD", "EUR", "TWD"):
        if c in rv:
            head.append(f"營收 {fmt_val('revenue', rv[c]['v'], c)}")
            break
    for k in ("gross_margin", "op_margin"):
        if k in a:
            head.append(f"{LABEL[k][0]} {a[k]['v']:.1f}%")
        elif k + "_ng" in a:
            head.append(f"{LABEL[k][0]}（non-GAAP） {a[k + '_ng']['v']:.1f}%")
    if head:
        L.append("本季：" + "、".join(head))
    vp = rec.get("vs_prev_guide") or []
    if vp:
        def rng(x):
            if x.get("single"):
                return "約 " + fmt_val(x["metric"], x["lo"], x.get("cur"))
            if x["metric"] in ("revenue", "opex", "capex"):
                return f"{fmt_val(x['metric'], x['lo'], x.get('cur'))}–{x['hi']:,.2f}B"
            return f"{x['lo']:.1f}%–{x['hi']:.1f}%"
        pos_single = {"above": "高於指引", "within": "大致符合指引", "below": "低於指引"}
        L.append("對照上次給的指引：" + "；".join(
            f"{LABEL[x['metric']][0]}{'（non-GAAP）' if x.get('basis') == 'ng' else ''} {fmt_val(x['metric'], x['actual'], x.get('cur'))}"
            f"（指引 {rng(x)}，{(pos_single if x.get('single') else POS)[x['pos']]}）" for x in vp))
    gq = [g for g in rec.get("guide") or [] if g["period"] == "next_q"]
    if gq:
        ov = {x["metric"]: x for x in rec.get("outlook_vs_now") or []}
        parts = []
        for g in gq:
            t = f"{LABEL[g['metric']][0]}{'（non-GAAP）' if g.get('basis') == 'ng' else ''} {fmt_range(g)}"
            o = ov.get(g["metric"])
            if o:
                t += (f"（中值較本季 {o['chg']:+.1f}%）" if o["unit"] == "B" else f"（中值較本季 {o['chg']:+.1f} 個百分點）")
            parts.append(t)
        L.append("下季指引：" + "；".join(parts))
    gy = [g for g in rec.get("guide") or [] if g["period"] == "year"]
    if gy:
        L.append("全年展望：" + "；".join(f"{LABEL[g['metric']][0]} {fmt_range(g)}" for g in gy))
    if "capex" in a:
        L.append(f"資本支出（本期現金流量表）：{fmt_val('capex', a['capex']['v'], a['capex']['cur'])}")
    return L


def latest(sym: str, cache: Optional[Dict] = None) -> Optional[Dict]:
    cache = cache if cache is not None else load()
    recs = [v for v in cache.values() if v.get("sym") == sym and v.get("acc")]
    return max(recs, key=lambda v: v["date"]) if recs else None
