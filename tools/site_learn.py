"""每日學習筆記 (top of 個股情報): a daily cloud routine reads what happened in the world and on Wall Street and writes
research_feed/learn.json —
- 今天的故事: the day told as a story, who did what and why, so nobody needs a video to follow it.
- 今天人類世界發生什麼: the day's biggest events in any field, what led to them, what follows, and how they reach
  US stocks, Treasuries and the wider economy.
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
STATUS = {"已確認": "up", "據報": "muted"}
WORLD_SHOWN = 6


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
    return (f'<details class="sgx"><summary><b>{_e(it.get("topic"))}</b> <span class="muted small">{_e(it.get("date"))}</span></summary>'
            f'<p class="small">{_e(it.get("one"))}</p>{body}</details>')


def _world(it: Dict) -> str:
    st = str(it.get("status") or "")
    tag = f'<span class="pill {STATUS.get(st, "")}">{_e(st)}</span>' if st else ""
    macro = "".join(f'<li><b>{_e(m["asset"])}</b>：{_e(m["how"])}' + (f'<div class="small muted">實際反應：{_e(m["seen"])}</div>' if m.get("seen") else "") + "</li>"
                    for m in it.get("macro") or [] if isinstance(m, dict) and m.get("asset") and m.get("how"))
    body = ((f'<p class="small"><b>前因</b>：{_e(it["cause"])}</p>' if it.get("cause") else "")
            + (f'<p class="small"><b>後果</b>：{_e(it["effect"])}</p>' if it.get("effect") else "")
            + (f'<p class="small"><b>為什麼重要</b>：{_e(it["why"])}</p>' if it.get("why") else "")
            + (f'<p class="small"><b>怎麼影響總經與市場</b></p><ul class="small">{macro}</ul>' if macro else "")
            + (f'<p class="small"><b>和台灣的關聯</b>：{_e(it["link"])}</p>' if it.get("link") else "")
            + (f'<p class="small"><b>後續進展</b>：{_e(it["followup"])}</p>' if it.get("followup") else "")
            + (f'<p class="small muted">來源：{_src(it.get("sources"))}</p>' if it.get("sources") else ""))
    return (f'<details class="sgx"><summary><b>{_e(it.get("title"))}</b> {tag} <span class="muted small">{_e(it.get("area"))} · {_e(it.get("date"))}</span></summary>'
            f'<p class="small">{_e(it.get("what"))}</p>{body}</details>')


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
    world = [x for x in (d.get("world") or []) if isinstance(x, dict) and x.get("title") and x.get("what")]
    if not stories and not terms and not world:
        return ""
    world.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
    stories.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
    top = stories[0] if stories else None
    lead = ("一句話看懂：" + (f'{_e(world[0]["title"])}——{_e(world[0]["what"])}' if world else f'{_e(top["topic"])}——{_e(top["one"])}' if top else f"本站目前收錄 {len(terms)} 個華爾街常用術語，附白話解釋。"))
    newt = [t for t in terms if str(t.get("added") or "") == str(d.get("updated") or "")[:10]]
    story = d.get("story") if isinstance(d.get("story"), dict) else {}
    paras = [f"<p>{_e(p)}</p>" for p in story.get("paragraphs") or [] if p]
    told = (paras[0] + (f'<details class="sgx"><summary>看完整故事</summary>{"".join(paras[1:])}</details>' if paras[1:] else "")) if paras else ""
    if told and story.get("title"):
        lead = "一句話看懂：" + _e(story["title"])
    body = (f'<p class="rimp big2"><b>{lead}</b></p>'
            + (f'<div class="rpt"><h3>今天的故事 <span class="muted small">{_e(story.get("date"))}</span></h3>{told}</div>' if told else "")
            + (f'<p class="small">今天新學的術語：{"、".join(_e(t["term"]) for t in newt)}</p>' if newt else "")
            + (f'<h3>今天人類世界發生什麼</h3>' + "".join(_world(x) for x in world[:WORLD_SHOWN]) if world else "")
            + (f'<h3>華爾街在談什麼</h3>' if world and stories else "")
            + "".join(_story(x) for x in stories[:6])
            + (f'<details class="sgx"><summary>華爾街術語小辭典（{len(terms)} 個）</summary><ul class="lines">'
               + "".join(_term(t) for t in sorted(terms, key=lambda t: str(t.get("added") or ""), reverse=True)) + "</ul></details>" if terms else "")
            + f'<p class="note">每天由雲端 AI 讀可靠媒體、學術期刊與官方文件整理，「已確認」只放有文件的事實，「只是報導」要等官方證實。'
              f'最後更新 {_e(d.get("updated"))}。不構成投資建議。</p>')
    return card("每日學習筆記：世界今天發生什麼", "Daily notes: what happened in the world", body, "wide",
                sub="全世界的大事、華爾街情資，以及學到的術語")
