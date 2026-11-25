"""Number check for the cloud AI write-ups in research_feed/ (learn, deep, sessions, bonds, forecast, macro_voice, ai_view).

Those routines write with web sources the site never sees, so wsb.ai.numcheck (every number must be in the prompt) can't
run on them.  What the site does know is its own close for the headline markets.  When an AI sentence quotes one of them
for the same session — a level or a day change — and it is off by more than the daily-check tolerance, the sentence keeps
its text and gets the site's own figure right after it:  〔數字查核：本站收盤 標普 500（11-09）7,550，+2.35%〕.
A wrong 台幣升值/貶值 is flagged the same way.

Only clear cases are touched: the number must follow the market's name closely, the write-up must be dated after that
close and within 3 days of it, and sentences about intraday moves, other periods or scenarios (盤中、本週、若跌破 …) are
skipped.  prime(eng) is called once per build; without it scrub() changes nothing."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# ticker, display name, name pattern, level tolerance (relative, or absolute for the 10Y), decimals, session
MARKETS = [
    ("^GSPC", "標普 500", r"標普\s*500|標普(?!\s*\d)|S&P\s*500|標準普爾\s*500", 0.003, 0, "us"),
    ("^NDX", "那指 100", r"那指\s*100|那斯達克\s*100|Nasdaq[- ]?100", 0.003, 0, "us"),
    ("^VIX", "VIX", r"VIX(?:\s*恐慌指數)?|恐慌指數", 0.005, 2, "us"),
    ("^TNX", "美債 10 年殖利率", r"(?:美債|美國公債)\s*10\s*年期?(?:殖利率)?|10\s*年期?\s*(?:美債|美國公債|公債)?\s*殖利率", 0.03, 3, "us"),
    ("^TWII", "台股加權", r"台股加權指數|台股加權|加權指數|台股|TAIEX", 0.003, 0, "tw"),
    ("TWD=X", "美元/台幣", r"美元兌新?台幣|新台幣|台幣", 0.003, 3, "tw"),
    ("GC=F", "黃金", r"黃金|金價", 0.015, 0, "us"),
    ("BZ=F", "布蘭特原油", r"布蘭特(?:原油)?|Brent", 0.015, 2, "us"),
]
ABS_TOL = {"^TNX"}                  # yield level: absolute percentage points
NO_PCT = {"^TNX"}                   # "4.86%" is the level, not a change
PCT_TOL = 0.15                      # day change: off by more than 0.15 pp and 5 % of the change
PCT_TOL_WIDE = {"GC=F": 0.5, "BZ=F": 0.5}   # futures settle vs spot / snapshot time: a wider band
FOREIGN_RX = re.compile(r"(?:英國|日本|德國|歐元區|歐洲|中國|義大利|法國|加拿大|澳洲|韓國|台灣|瑞士|印度)\s*$")
SKIP_RX = re.compile(r"盤中|盤前|夜盤|期貨|本週|上週|這週|週線|一週|今年|年初|以來|累計|個月|月線|高點|低點|最高|最低|"
                     r"目標|預估|預期|預判|若|如果|可能|跌破|站上|支撐|壓力|關卡|一個月後|下週|明天|今晚|早盤|午盤|尾盤|→|前收|從")
SENT_RX = re.compile(r"[^。！？!?\n]*[。！？!?\n]?")
DATE_RX = re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?![\d/])|(\d{1,2})\s*月\s*(\d{1,2})\s*日|\d{4}-(\d{2})-(\d{2})")
NUM_RX = re.compile(r"[-+−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[-+−]?\d+(?:\.\d+)?")
NAMES = re.compile("|".join(f"(?:{m[2]})" for m in MARKETS))
NOTE = "〔數字查核：本站收盤 {name}（{asof}）{lvl}{chg}〕"
UNITS = ("bp", "基點", "個", "倍", "檔", "天", "日", "年", "億", "萬", "兆", "家", "次")
SKIP_KEYS = {"updated", "date", "url", "src", "source", "sources", "link", "added", "by", "ts"}
FACTS: Dict[str, Dict] = {}


def prime(eng) -> None:
    """Remember this build's closes for the headline markets (called once before rendering)."""
    FACTS.clear()
    for t, *_ in MARKETS:
        try:
            q = eng.market.q(t) or {}
        except Exception:  # noqa: BLE001
            q = {}
        if q.get("price") is not None and q.get("asof"):
            FACTS[t] = {"price": float(q["price"]), "chg": q.get("chg_pct"), "asof": str(q["asof"])[:10]}


def _when(s) -> Optional[datetime]:
    s = str(s or "").strip().replace("T", " ")
    for n, fmt in ((16, "%Y-%m-%d %H:%M"), (10, "%Y-%m-%d")):
        try:
            return datetime.strptime(s[:n], fmt)
        except ValueError:
            continue
    return None


def _same_session(t: str, sess: str, ctx: Tuple) -> bool:
    """Was the write-up (Taipei time) made after this close and within 3 days of it, and is the item it sits in
    (its own 'date', when it has one) about this session or later — not an older day kept in a history list?"""
    f = FACTS.get(t)
    written, day_hint = ctx
    if not f or not written:
        return False
    day = datetime.strptime(f["asof"], "%Y-%m-%d")
    if day_hint and day_hint.date() < day.date():
        return False
    close = day + (timedelta(hours=14) if sess == "tw" else timedelta(days=1, hours=5))   # TW 13:30 / US 16:00 NY ≈ 05:00 Taipei
    if sess == "tw" and written.date() > day.date() and 9 <= written.hour < 14:
        return False                                          # written while Taiwan was trading again
    return close <= written <= close + timedelta(days=3)


def _dates_ok(sent: str, asof: str) -> bool:
    """A sentence that names a day must name this close's day (「11/6 收 39,701」 is history, not today's quote)."""
    mo, dd = int(asof[5:7]), int(asof[8:10])
    for m in DATE_RX.finditer(sent):
        g = [x for x in m.groups() if x]
        if len(g) == 2 and (int(g[0]), int(g[1])) != (mo, dd):
            return False
    return True


def _val(raw: str) -> float:
    return float(raw.replace(",", "").replace("−", "-"))


def _fmt(t: str, dg: int) -> str:
    f = FACTS[t]
    lvl = f"{f['price']:,.{dg}f}" + ("%" if t in ABS_TOL else "")
    chg = "" if f["chg"] is None or t in NO_PCT else f"，{f['chg']:+.2f}%"
    return lvl, chg


def _check_one(sent: str, m: re.Match, nxt: int, mk, ctx) -> bool:
    t, name, _rx, tol, dg, sess = mk
    if not _same_session(t, sess, ctx):
        return False
    f = FACTS[t]
    win = sent[m.end():min(nxt, m.end() + 24)]
    if t == "TWD=X":
        c = f["chg"]
        if c is not None and (("升值" in win and c > 0.1) or ("貶值" in win and c < -0.1)):
            return True
    lvl_seen = pct_seen = False
    for n in NUM_RX.finditer(win):
        raw, tail = n.group(), win[n.end():n.end() + 4]
        try:
            v = _val(raw)
        except ValueError:
            continue
        is_pct = tail.lstrip().startswith("%")
        if not is_pct and tail.lstrip().startswith(UNITS):  # basis points, counts, multiples, money amounts
            continue
        if t in NO_PCT or not is_pct:
            if lvl_seen:
                continue
            p = f["price"]
            if not p or abs(abs(v) - p) > 0.3 * p:          # not this market's level (a points change, "500", …)
                continue
            lvl_seen = True
            off = abs(abs(v) - p) if t in ABS_TOL else abs(abs(v) - p) / p
            if off > tol + 1e-9:
                return True
        else:
            if pct_seen or f["chg"] is None or abs(v) > 15:
                continue
            pct_seen = True
            c = f["chg"]
            signed = raw[0] in "+-−"
            if t == "TWD=X":                                  # 台幣升值 0.9% is USD/TWD −0.9%
                v = -abs(v) if "升值" in win else abs(v) if "貶值" in win else v
                signed = signed or "升值" in win or "貶值" in win
            diff = abs(v - c) if signed else abs(abs(v) - abs(c))
            if diff > PCT_TOL_WIDE.get(t, PCT_TOL) and diff > 0.05 * abs(c):
                return True
    return False


def check_text(text: str, written, day_hint=None) -> Tuple[str, int]:
    """→ (text with the site's figure after each sentence that misquotes it, how many were flagged).
    written: when the write-up was made (Taipei); day_hint: the 'date' of the item the text sits in, if any."""
    if not FACTS or not text or not isinstance(text, str):
        return text, 0
    written = written if isinstance(written, datetime) or written is None else _when(written)
    day_hint = day_hint if isinstance(day_hint, datetime) or day_hint is None else _when(day_hint)
    if not written:
        return text, 0
    ctx = (written, day_hint)
    out, n = [], 0
    for sm in SENT_RX.finditer(text):
        sent = sm.group()
        if not sent:
            continue
        notes: List[str] = []
        hits = list(NAMES.finditer(sent))
        for i, m in enumerate(hits):
            mk = next((x for x in MARKETS if re.fullmatch(x[2], m.group())), None)
            if not mk or mk[0] not in FACTS or FOREIGN_RX.search(sent[max(0, m.start() - 4):m.start()]):
                continue
            a = max(sent.rfind(c, 0, m.start()) for c in "；;") + 1
            b = min([j for j in (sent.find(c, m.end()) for c in "；;") if j >= 0] or [len(sent)])
            clause = sent[a:b]                                # skip words and dates are judged clause by clause
            if SKIP_RX.search(clause) or not _dates_ok(clause if DATE_RX.search(clause) else sent, FACTS[mk[0]]["asof"]):
                continue
            nxt = min(hits[i + 1].start() if i + 1 < len(hits) else len(sent), b)
            if _check_one(sent, m, nxt, mk, ctx):
                lvl, chg = _fmt(mk[0], mk[4])
                note = NOTE.format(name=mk[1], asof=FACTS[mk[0]]["asof"][5:], lvl=lvl, chg=chg)
                if note not in notes:
                    notes.append(note)
        if notes:
            n += len(notes)
            body = sent.rstrip("\n")
            sent = body + "".join(notes) + sent[len(body):]
        out.append(sent)
    return "".join(out), n


def scrub(d, written=None, day_hint=None):
    """Walk a research_feed JSON and check every text field.  The top-level 'updated' says when it was written; a
    nested 'date' says which day an item is about (older days in a history list are left alone); intraday items
    (phase 盤中 / 盤前) are left alone too."""
    if not FACTS:
        return d
    if isinstance(d, dict):
        if any(x in str(d.get("phase") or "") for x in ("盤中", "盤前")):
            return d
        own = str(d.get("updated") or "")
        w = _when(own) if len(own) >= 16 or not written else written
        w = w or written or _when(d.get("date"))
        hint = _when(d.get("date")) if written and d.get("date") else day_hint
        return {k: (v if k in SKIP_KEYS else scrub(v, w, hint)) for k, v in d.items()}
    if isinstance(d, list):
        return [scrub(x, written, day_hint) for x in d]
    if isinstance(d, str) and len(d) > 6:
        return check_text(d, written, day_hint)[0]
    return d
