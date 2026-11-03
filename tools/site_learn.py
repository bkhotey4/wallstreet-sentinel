"""每日學習筆記 (top of 個股情報): a daily cloud routine reads what Wall Street is talking about and writes
research_feed/learn.json —
- 華爾街情資: today's stories, each split into what is confirmed by a document and what is only reported.
- 術語: market terms explained in plain words, e.g. 耳語預期 or 二階導, and whether this site measures them.
Static content: the routine commits the JSON and the site shows it as written."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "learn.json"   # public repo only
SITE = {"已在本站": "up", "可以做": "", "做不到": "muted"}


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
        name = _e(s.get("name") or "來源") + (f'（{_e(s.get("date"))}）' if s.get("date") else "")
        out.append(f'<a href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">{name}</a>' if u.startswith("https://") else name)
    return "、".join(out)


def _story(it: Dict) -> str:
    li = lambda xs: "".join(f"<li>{_e(x)}</li>" for x in xs or [] if x)               # noqa: E731
    conf, rep = li(it.get("confirmed")), li(it.get("reported"))
    body = ((f'<p class="small"><b>已確認（有文件）</b></p><ul class="small">{conf}</ul>' if conf else "")
            + (f'<p class="small"><b>只是報導或預測（還沒有官方文件）</b></p><ul class="small">{rep}</ul>' if rep else "")
            + (f'<p class="small"><b>市場反應</b>：{_e(it["market"])}</p>' if it.get("market") else "")
            + (f'<p class="small"><b>連帶影響</b>：{_e(it["spill"])}</p>' if it.get("spill") else "")
            + (f'<p class="small"><b>接下來看</b>：{_e(it["watch"])}</p>' if it.get("watch") else "")
            + (f'<p class="small muted">來源：{_src(it.get("sources"))}</p>' if it.get("sources") else ""))
    return (f'<div class="rpt"><h3>{_e(it.get("topic"))} <span class="muted small">{_e(it.get("date"))}</span></h3>'
            f'<p>{_e(it.get("one"))}</p><details class="sgx"><summary>細節</summary>{body}</details></div>')


def _term(t: Dict) -> str:
    st = str(t.get("site") or "")
    tag = f'<span class="pill {SITE.get(st, "")}">{_e(st)}</span>' if st else ""
    return (f'<li><b>{_e(t.get("term"))}</b>' + (f'（{_e(t["en"])}）' if t.get("en") else "") + f' {tag}：{_e(t.get("plain"))}'
            + (f'<div class="small muted">例子：{_e(t["example"])}</div>' if t.get("example") else "")
            + (f'<div class="small muted">本站：{_e(t["how"])}</div>' if t.get("how") else "") + "</li>")


def sec_learn(eng) -> str:
    d = load()
    stories = [x for x in (d.get("stories") or []) if isinstance(x, dict) and x.get("topic") and x.get("one")]
    terms = [x for x in (d.get("terms") or []) if isinstance(x, dict) and x.get("term") and x.get("plain")]
    if not stories and not terms:
        return ""
    stories.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
    top = stories[0] if stories else None
    lead = ("一句話看懂：" + (f'{_e(top["topic"])}——{_e(top["one"])}' if top else f"本站目前收錄 {len(terms)} 個華爾街常用術語，附白話解釋。"))
    newt = [t for t in terms if str(t.get("added") or "") == str(d.get("updated") or "")[:10]]
    body = (f'<p class="rimp big2"><b>{lead}</b></p>'
            + (f'<p class="small">今天新學的術語：{"、".join(_e(t["term"]) for t in newt)}</p>' if newt else "")
            + "".join(_story(x) for x in stories[:6])
            + (f'<details class="sgx"><summary>華爾街術語小辭典（{len(terms)} 個）</summary><ul class="lines">'
               + "".join(_term(t) for t in sorted(terms, key=lambda t: str(t.get("added") or ""), reverse=True)) + "</ul></details>" if terms else "")
            + f'<p class="note">每天由雲端 AI 讀可靠媒體與官方文件整理，「已確認」只放有文件的事實，「只是報導」要等官方證實。'
              f'最後更新 {_e(d.get("updated"))}。不構成投資建議。</p>')
    return card("每日學習筆記：華爾街在談什麼", "Daily notes: what Wall Street is talking about", body, "wide",
                sub="今天的華爾街情資，以及學到的術語")
