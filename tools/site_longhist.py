"""人類與市場的長歷史 page: from the first American government bonds and stock trades to today, told through what people
believed and feared, what stocks and bonds did, and which rules changed afterwards, plus the patterns that recur.
research_feed/history.json holds the researched text and sources; the site shows it as written."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "history.json"   # public repo only
CONF = {"高": "up", "中": "", "低": "muted"}


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _e(x) -> str:
    return html.escape(guard_safe(str(x or "")))


def _src(xs) -> str:
    out = []
    for s in xs or []:
        if not isinstance(s, dict):
            continue
        u = str(s.get("url") or "")
        name = _e(s.get("name") or "來源")
        out.append(f'<a href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">{name}</a>' if u.startswith("https://") else name)
    return "、".join(out)


def _conf(x: Dict) -> str:
    c = str(x.get("conf") or "")
    return f'<span class="pill {CONF.get(c, "")}">把握度{_e(c)}</span>' if c else ""


def _rows(xs, *keys) -> List[Dict]:
    return [x for x in xs or [] if isinstance(x, dict) and all(x.get(k) for k in keys)]


def _line(label: str, x: Dict, key: str) -> str:
    return f'<p class="small"><b>{label}</b>：{_e(x[key])}</p>' if x.get(key) else ""


def _era(x: Dict) -> str:
    body = (_line("當時的人", x, "people") + _line("發生什麼", x, "what") + _line("股市", x, "stocks") + _line("債市與利率", x, "bonds")
            + _line("之後改變了什麼", x, "after")
            + (f'<p class="small muted">來源：{_src(x.get("sources"))}</p>' if x.get("sources") else ""))
    return (f'<div class="rpt"><h3>{_e(x["years"])}　{_e(x["title"])} {_conf(x)}</h3><p>{_e(x.get("lesson"))}</p>'
            f'<details class="sgx"><summary>細節</summary>{body}</details></div>')


def _pattern(x: Dict) -> str:
    seen = "、".join(_e(e) for e in x.get("eras") or [] if e)
    return (f'<div class="rpt"><h3>{_e(x["name"])} {_conf(x)}</h3><p>{_e(x.get("what"))}</p>'
            + (f'<p class="small muted">出現過：{seen}</p>' if seen else "")
            + _line("今天像的地方", x, "like") + _line("今天不像的地方", x, "unlike") + "</div>")


def sec_longhist(eng) -> str:
    d = load()
    eras = _rows(d.get("eras"), "years", "title")
    if not eras:
        return ""
    patterns = _rows(d.get("patterns"), "name")
    notes = "".join(f"<li>{_e(n)}</li>" for n in d.get("notes") or [] if n)
    body = (f'<p class="rimp big2"><b>一句話看懂：{_e(d.get("one"))}</b></p>'
            + "".join(f"<p>{_e(p)}</p>" for p in d.get("intro") or [] if p)
            + ("<h3>會重複出現的模式</h3>" + "".join(_pattern(x) for x in patterns) if patterns else "")
            + f"<h3>從頭看起（{len(eras)} 個時期）</h3>" + "".join(_era(x) for x in eras)
            + (f'<details class="sgx"><summary>資料的限制</summary><ul class="small">{notes}</ul></details>' if notes else "")
            + f'<p class="note">歷史不會照抄，這裡的比較只幫助理解，不是股價預測。越早期的數字越粗略。整理日期 {_e(d.get("updated"))}。不構成投資建議。</p>')
    return card("人類與市場的長歷史：從第一批美國公債開始", "People and markets since the first US bonds", body, "wide",
                sub="1790 年至今，股市、債市與人的故事")
