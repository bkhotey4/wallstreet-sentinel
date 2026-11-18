"""卡片之間互相對答案（2026-11-17）。

使用者問：「為何每次都是要我說？」原因是本站的自我檢查只往內看（抓到的資料有沒有顯示、有沒有過期），
不往外看：網站自己的「每日學習筆記」從 11/11 就寫「Anthropic 11/19 掛牌」，IPO 卡卻寫「約 11/26」，
兩張卡互相矛盾 6 天沒人發現；輝達財報那次也是同一類。

這支把「AI 寫的文字」（每日學習筆記、每日總經語音稿）裡提到的日期，和「程式算的卡片」比對：
  * IPO：IPO 卡上每一家公司的名字；文字說「X 某月某日掛牌／上市／定價」→ 和 IPO 卡的日期差超過 2 天、或卡上沒有日期 → 提醒
  * 財報：財報日曆上前後 10 天、市值 100 億美元以上的公司（中文名、英文名、代號）；文字說「X 某月某日財報」
    → 和日曆差超過 1 天（台北和美東差一天是正常的）→ 提醒
提醒不代表哪一邊錯：可能是 AI 寫錯，也可能是程式的資料慢了（這次是程式慢了）。純函式，方便測試。"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

SUFFIX = re.compile(r"\s+(Inc\.?|Corp\.?|Corporation|Ltd\.?|Limited|PBC|plc|Holdings?|Co\.|Company|N\.V\.|S\.A\.)$", re.I)
WIN = 60                                  # the name must appear within this many characters before the date
MD = re.compile(r"(?<!\d)(1[0-2]|0?[1-9])/([12]\d|3[01]|0?[1-9])(?!\d)")
IPO_KW = re.compile(r"^[^。；，\n]{0,12}?(掛牌|上市|定價|IPO)")
EARN_KW = re.compile(r"^[^。；，\n]{0,14}?(財報|公布第.財季|公布業績)")


def _year(m: int, d: int, today: date) -> Optional[date]:
    y = today.year + (1 if m < today.month - 6 else 0) - (1 if m > today.month + 6 else 0)
    try:
        return date(y, m, d)
    except ValueError:
        return None


def mentions(text: str, names: Iterable[str], kw: re.Pattern, today: date) -> List[Tuple[str, date, str]]:
    """(name, date, snippet) for every 'name … M/D … keyword' in the text; the name is the one closest before the date."""
    names = [n for n in dict.fromkeys(names) if n and len(n) >= 2]
    out = []
    for m in MD.finditer(text):
        if not kw.search(text[m.end():m.end() + 20]):
            continue
        before = text[max(0, m.start() - WIN):m.start()]
        cut = max(before.rfind(c) for c in ("。", "；", chr(10)))   # the name must be in the same sentence as the date
        if cut >= 0:
            before = before[cut + 1:]
        best, pos = None, -1
        for n in names:
            i = before.rfind(n)
            if i > pos:
                best, pos = n, i
        d = _year(int(m.group(1)), int(m.group(2)), today)
        if best and d:
            out.append((best, d, text[max(0, m.start() - 30):m.end() + 12].replace("\n", " ")))
    return out


def ipo_dates(html: str) -> Dict[str, Optional[str]]:
    """IPO card HTML → {short name: 'MM-DD' of its likely pricing, or None}.  Each filer row starts with
    '<tr><td><b>NAME</b>' (nested tables inside a row never start that way); the date cell is '<b>…約…</b> MM-DD'.
    Short name = the part before the first comma ('Anthropic, PBC' → 'Anthropic')."""
    out: Dict[str, Optional[str]] = {}
    parts = re.split(r"<tr><td><b>", html)
    for chunk in parts[1:]:
        m = re.match(r"([^<]{2,80})</b>", chunk)
        if not m:
            continue
        short = SUFFIX.sub("", m.group(1).split(",")[0]).strip()
        # two shapes: the estimate '<b>約 MM-DD</b>', and the company's own timetable '<b>MM-DD <span>掛牌</span></b>'
        # (11-18: the timetable shape was added on 11-17 and this read it as 'no date' — a false 卡片互相矛盾)
        d = (re.search(r"<b>(?:<span[^>]*>)?約(?:</span>)?\s*(\d\d-\d\d)</b>", chunk)
             or re.search(r"<b>(\d\d-\d\d)\s*(?:<span[^>]*>)?(?:掛牌|上市|定價)", chunk))
        out.setdefault(short, d.group(1) if d else None)
    return out


def ipo_issues(ai_text: str, card_html: str, today: date, tol: int = 2) -> List[Dict]:
    cards = ipo_dates(card_html)
    out, seen = [], set()
    for name, d, snip in mentions(ai_text, cards.keys(), IPO_KW, today):
        if d < today - timedelta(days=1) or (name, d) in seen:
            continue
        seen.add((name, d))
        c = cards.get(name)
        cd = _year(int(c[:2]), int(c[3:]), today) if c else None
        if cd is None or abs((cd - d).days) > tol:
            out.append({"kind": "ipo", "name": name, "text_date": d.isoformat(), "card_date": cd.isoformat() if cd else None, "snip": snip})
    return out


def earn_issues(ai_text: str, earn_days: Dict, zh: Dict[str, str], today: date, tol: int = 1,
                floor: float = 1e10, days: int = 10) -> List[Dict]:
    """earn_days = {US date: {rows: [{sym, name, mcap}]}}; zh = {sym: 中文名}."""
    lo, hi = (today - timedelta(days=days)).isoformat(), (today + timedelta(days=days)).isoformat()
    cal: Dict[str, Tuple[str, str]] = {}                       # alias → (sym, date)
    for day, v in earn_days.items():
        if not (lo <= day <= hi):
            continue
        for r in (v.get("rows") if isinstance(v, dict) else None) or []:
            if float(r.get("mcap") or 0) < floor or not r.get("sym"):
                continue
            sym = str(r["sym"]).upper()
            for a in (sym if len(sym) >= 3 else None, zh.get(sym), str(r.get("name") or "").split(",")[0].split(" Inc")[0].strip()):
                if a and len(a) >= 2:
                    cal[a] = (sym, day)
    out, seen = [], set()
    for alias, d, snip in mentions(ai_text, cal.keys(), EARN_KW, today):
        sym, day = cal[alias]
        if (sym, d) in seen:
            continue
        seen.add((sym, d))
        if abs((date.fromisoformat(day) - d).days) > tol:
            out.append({"kind": "earn", "name": alias, "sym": sym, "text_date": d.isoformat(), "card_date": day, "snip": snip})
    return out


def describe(issues: List[Dict]) -> str:
    parts = []
    for i in issues[:6]:
        what = "掛牌" if i["kind"] == "ipo" else "財報"
        card = "IPO 卡" if i["kind"] == "ipo" else "財報日曆"
        cd = i["card_date"][5:].replace("-", "/") if i.get("card_date") else "沒有日期"
        parts.append(f"{i['name']}{what}：文字寫 {i['text_date'][5:].replace('-', '/')}，{card} {cd}")
    return "；".join(parts)
