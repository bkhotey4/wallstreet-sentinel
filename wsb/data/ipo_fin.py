"""招股書（S-1 / F-1）裡的「摘要財務資料」表：營收、毛利、營業損益、淨損益，各期間的數字與年增、獲利率。

只讀招股書自己的表格，不用 AI：找到 Summary (Consolidated) Financial Data 這一節後面第一張有「年份表頭＋營收或淨損益列」
的表，表頭的年份配上「Year Ended / Six Months Ended …」的期間，單位看「in thousands / in millions」。
年增只比同樣長度的期間（全年對全年、前 9 個月對前 9 個月）；招股書很少列單季，所以有季度表才算季增。
看不懂的表一律放棄，不猜。"""
from __future__ import annotations

import html as H
import re
from typing import Dict, List, Optional

W = r"(?:\s|&#160;|&nbsp;|&#xa0;|<[^>]+>)+"
HEAD = re.compile(r"Summary" + W + r"(?:(?:Consolidated|Combined|Historical|Selected|Carve-Out)" + W + r")*Financial", re.I)
ROWS = {  # key → label pattern (first matching row wins); labels are matched after trimming footnote marks
    "rev": r"^(?:total\s+)?(?:net\s+)?(?:revenues?|sales)(?:,?\s*net)?$|^total\s+net\s+revenues?$|^revenues?\s+from\s+contracts|^net\s+revenues?$",
    "gp": r"^gross\s+(?:profit|margin)$|^gross\s+(?:profit|loss)$",
    "op": r"^(?:income|loss|\(loss\)\s*income|income\s*\(loss\)|loss\s*from\s*operations|operating\s+(?:income|loss|profit))"
          r"(?:\s*\(loss\)|\s*\(income\))?(?:\s+from\s+operations)?$|^(?:operating\s+(?:income|loss)(?:\s*\(loss\))?)$",
    "ni": r"^net\s+(?:loss|income|\(loss\)\s*income|income\s*\(loss\)|loss\s*and\s*comprehensive\s*loss|income\s*and\s*comprehensive\s*income)"
          r"(?:\s*\(loss\))?(?:\s+for\s+the\s+(?:year|period))?$|^(?:loss|profit)\s+for\s+the\s+(?:year|period)$",
}
MONTHS = (("three", 3), ("six", 6), ("nine", 9), ("twelve", 12), ("year", 12), ("fiscal", 12), ("quarter", 3))


def _cells(tr: str) -> List[str]:
    out = []
    for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I):
        t = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", c))).replace("​", "").strip()
        if t:
            out.append(t)
    return out


def _num(cells: List[str]) -> List[Optional[float]]:
    """'$', '(9,317', ')' , '—' → numbers (parentheses = negative, dash = 0)."""
    s = " ".join(cells)
    s = re.sub(r"\$\s*", "", s)
    out = []
    for m in re.finditer(r"\(\s*([\d,]+(?:\.\d+)?)\s*\)?|(?<![\w.])([\d,]+(?:\.\d+)?)(?![\w.])|(?:^|\s)([—–-])(?=\s|$)", s):
        if m.group(1):
            out.append(-float(m.group(1).replace(",", "")))
        elif m.group(2):
            out.append(float(m.group(2).replace(",", "")))
        else:
            out.append(0.0)
    return out


def _label(cells: List[str]) -> str:
    lab = re.sub(r"\(\d\)|\*|†", "", cells[0]).strip(" :,")
    return re.sub(r"\s+", " ", lab).lower()


def _periods(rows: List[List[str]]) -> Optional[List[Dict]]:
    """Column periods from the header rows: years (in order) and their lengths from 'Year / Six Months Ended …'."""
    years, groups = None, []
    for cells in rows[:8]:
        ys = [c for c in cells if re.fullmatch(r"(?:FY\s?)?(19|20)\d\d", c)]
        if len(ys) >= 2 and len(ys) >= len(cells) - 1:
            years = [int(re.sub(r"\D", "", y)[-4:]) for y in ys]
            continue
        for c in cells:
            lc = c.lower()
            if "ended" in lc or "year" in lc or "months" in lc or "period" in lc:
                mo = next((n for w, n in MONTHS if w in lc), None)
                if mo:
                    groups.append(mo)
    if not years:
        return None
    if not groups:
        groups = [12]
    n = len(years)
    if len(groups) == 1:
        sizes = [n]
    elif n % len(groups) == 0:
        sizes = [n // len(groups)] * len(groups)
    elif len(groups) == 2 and n >= 3:
        # the usual layout: three fiscal years + the two interim periods (or the interim pair first)
        sizes = [n - 2, 2] if groups[0] == 12 else [2, n - 2]
    else:
        return None
    out, i = [], 0
    for mo, k in zip(groups, sizes):
        for y in years[i:i + k]:
            out.append({"year": y, "months": mo})
        i += k
    return out


def _unit(seg: str) -> float:
    t = re.sub(r"<[^>]+>", " ", seg[:20000]).lower()
    if re.search(r"in\s+millions|\(\$?\s*millions|us\$\s*millions", t):
        return 1e6
    if re.search(r"in\s+thousands|\(\$?\s*thousands|us\$\s*thousands|\$000", t):
        return 1e3
    return 1.0


def _table(t: str, unit: float) -> Optional[Dict]:
    rows = [c for c in (_cells(tr) for tr in re.findall(r"<tr.*?</tr>", t, re.S | re.I)) if c]
    per = _periods(rows)
    if not per:
        return None
    vals: Dict[str, List[float]] = {}
    for cells in rows:
        if not re.search(r"[A-Za-z]", cells[0]):
            continue
        lab = _label(cells)
        nums = _num(cells[1:])
        if len(nums) != len(per):
            continue
        for k, pat in ROWS.items():
            if k not in vals and re.search(pat, lab):
                vals[k] = [v * unit for v in nums]
    if "rev" not in vals and "ni" not in vals:
        return None
    return {"periods": [{**p, **{k: v[i] for k, v in vals.items()}} for i, p in enumerate(per)]}


def parse_fin(raw: str) -> Optional[Dict]:
    """The prospectus's summary financial table → periods with revenue / gross profit / operating and net income, plus
    year-on-year growth for like-for-like periods and margins.  None when no readable table is found."""
    for m in HEAD.finditer(raw or ""):
        seg = raw[m.start(): m.start() + 250000]
        unit = _unit(seg)
        for t in re.findall(r"<table.*?</table>", seg, re.S | re.I)[:4]:
            got = _table(t, unit)
            if got:
                return derive(got["periods"])
    return None


QHEAD = re.compile(r"(?:Selected\s+)?Quarterly" + W + r"(?:Results" + W + r"of" + W + r"Operations|Results|(?:Consolidated" + W + r")?Statements"
                   + W + r"of" + W + r"Operations|Financial" + W + r"Data)", re.I)
MON = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september",
                                    "october", "november", "december"], 1)}
DATE = re.compile(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+((?:19|20)\d\d)", re.I)


def _quarter_table(t: str, unit: float) -> Optional[List[Dict]]:
    rows = [c for c in (_cells(tr) for tr in re.findall(r"<tr.*?</tr>", t, re.S | re.I)) if c]
    ends = None
    for cells in rows[:6]:
        ds = [DATE.search(c) for c in cells]
        ds = [d for d in ds if d]
        if len(ds) >= 4:
            ends = [f"{d.group(3)}-{MON[d.group(1).lower()]:02d}-{int(d.group(2)):02d}" for d in ds]
            break
    if not ends:
        return None
    vals: Dict[str, List[float]] = {}
    for cells in rows:
        if not re.search(r"[A-Za-z]", cells[0]) or any("%" in c for c in cells[1:]):
            continue                                            # the "% of revenue" twin table is skipped
        nums = _num(cells[1:])
        if len(nums) != len(ends):
            continue
        lab = _label(cells)
        for k, pat in ROWS.items():
            if k not in vals and re.search(pat, lab):
                vals[k] = [v * unit for v in nums]
    if "rev" not in vals:
        return None
    qs = [{"end": e, **{k: v[i] for k, v in vals.items()}} for i, e in enumerate(ends)]
    return sorted(qs, key=lambda q: q["end"])


def parse_quarters(raw: str) -> Optional[Dict]:
    """The prospectus's quarterly results table (usually in MD&A): each quarter's revenue / gross / operating / net figures,
    quarter-on-quarter and same-quarter-last-year growth, margins, and whether growth is slowing."""
    for m in QHEAD.finditer(raw or ""):
        seg = raw[m.start(): m.start() + 300000]
        unit = _unit(seg)
        for t in re.findall(r"<table.*?</table>", seg, re.S | re.I)[:3]:
            qs = _quarter_table(t, unit)
            if qs and len(qs) >= 4:
                return quarter_stats(qs)
    return None


def quarter_stats(qs: List[Dict]) -> Dict:
    def pct(a, b):
        return None if a is None or b in (None, 0) else (a / b - 1) * 100 * (1 if b > 0 else -1)
    by_end = {q["end"]: q for q in qs}
    for i, q in enumerate(qs):
        q["qoq"] = pct(q.get("rev"), qs[i - 1].get("rev")) if i else None
        ly = f"{int(q['end'][:4]) - 1}{q['end'][4:]}"
        q["yoy"] = pct(q.get("rev"), (by_end.get(ly) or {}).get("rev"))
        q["add"] = (q["rev"] - qs[i - 1]["rev"]) if i and q.get("rev") is not None and qs[i - 1].get("rev") is not None else None
        for k in ("gp", "op", "ni"):
            if q.get(k) is not None and q.get("rev"):
                q[k + "_m"] = q[k] / q["rev"] * 100
    g = [q["qoq"] for q in qs if q.get("qoq") is not None]
    out = {"quarters": qs}
    if len(g) >= 2:
        out["slowing"] = g[-1] < g[-2]
        out["qoq_last"], out["qoq_prev"] = g[-1], g[-2]
        out["qoq_avg_prev3"] = sum(g[-4:-1]) / len(g[-4:-1]) if len(g) >= 4 else None
    adds = [q["add"] for q in qs if q.get("add") is not None]
    if len(adds) >= 2:
        out["add_last"], out["add_prev"] = adds[-1], adds[-2]
    return out


def derive(periods: List[Dict]) -> Dict:
    """Latest annual and latest interim period, each with its year-on-year change and margins; QoQ when 3-month columns exist."""
    out: Dict = {"periods": periods}

    def find(mo: int, y: int) -> Optional[Dict]:
        return next((p for p in periods if p["months"] == mo and p["year"] == y), None)

    def pct(a, b):
        return None if a is None or b in (None, 0) else (a / b - 1) * 100 * (1 if b > 0 else -1)

    for key, mos in (("annual", (12,)), ("interim", (9, 6, 3))):
        cand = [p for p in periods if p["months"] in mos]
        if not cand:
            continue
        cur = max(cand, key=lambda p: (p["year"], p["months"]))
        prev = find(cur["months"], cur["year"] - 1)
        r = {"year": cur["year"], "months": cur["months"]}
        for k in ("rev", "gp", "op", "ni"):
            if cur.get(k) is not None:
                r[k] = cur[k]
                r[k + "_yoy"] = pct(cur[k], (prev or {}).get(k))
        if cur.get("rev"):
            for k in ("gp", "op", "ni"):
                if cur.get(k) is not None:
                    r[k + "_m"] = cur[k] / cur["rev"] * 100
                    if prev and prev.get(k) is not None and prev.get("rev"):
                        r[k + "_m_prev"] = prev[k] / prev["rev"] * 100
        out[key] = r
    q3 = sorted((p for p in periods if p["months"] == 3), key=lambda p: p["year"])
    if len(q3) >= 2 and q3[-1].get("rev") and q3[-2].get("rev") and q3[-1]["year"] != q3[-2]["year"]:
        out.setdefault("interim", {})["q_yoy_only"] = True              # two Q3s a year apart: that is YoY, not QoQ
    return out
