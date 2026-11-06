"""美股時段快報 (top of 總覽): before the open, mid-session and after the close a cloud routine writes
research_feed/sessions.json in plain words: what happened, why, what it means for the economy, what to watch.
Static content: the routine commits the JSON and the site shows the newest day as written."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "sessions.json"   # public repo only
PHASES = ("盤前", "盤中", "盤後")


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


def _item(x: Dict) -> str:
    told = "".join(f"<p>{_e(p)}</p>" for p in x.get("story") or [] if p)
    macro = "".join(f'<li><b>{_e(m.get("name"))}</b>：{_e(m.get("read"))}</li>' for m in x.get("macro") or []
                    if isinstance(m, dict) and m.get("name") and m.get("read"))
    return (f'<div class="rpt"><h3>{_e(x.get("phase"))} <span class="muted small">{_e(x.get("at"))} 台北</span></h3>'
            f'<p><b>{_e(x.get("one"))}</b></p>{told}'
            + (f'<p class="small"><b>總經情勢</b></p><ul class="small">{macro}</ul>' if macro else "")
            + (f'<p class="small"><b>接下來看</b>：{_e(x["next"])}</p>' if x.get("next") else "")
            + (f'<p class="small muted">來源：{_src(x.get("sources"))}</p>' if x.get("sources") else "") + "</div>")


def sec_sessions(eng) -> str:
    d = load()
    items = [x for x in (d.get("items") or []) if isinstance(x, dict) and x.get("date") and x.get("one") and x.get("phase") in PHASES]
    if not items:
        return ""
    day = max(str(x["date"]) for x in items)
    today = {x["phase"]: x for x in items if str(x["date"]) == day}
    shown = [today[p] for p in reversed(PHASES) if p in today]
    return card("美股今天怎麼了", "US stocks today", f'<p class="rimp big2"><b>一句話看懂：{_e(shown[0]["one"])}</b></p>'
                + "".join(_item(x) for x in shown)
                + f'<p class="note">美股開盤前、盤中、收盤後由雲端 AI 用公開資料整理，交易日 {_e(day)}。是對當下的解讀，不是股價預測。不構成投資建議。</p>',
                "wide", sub="開盤前、盤中、收盤後各更新一次")
