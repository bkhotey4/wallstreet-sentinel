"""台股覆蓋清單（台股專業判讀頁最後一張，2026-11-22，使用者：「台股的部分，功能就這些ok了嗎?? 或不會以後我通知你才發現少放?」）。

research_feed/tw_coverage.json 列出專業台股交易台會看的項目與本站現況（有／部分／缺），每日排程依序補「缺」的、Gemini 每週核對有沒有漏列。
這張卡把清單攤開：使用者不用等到自己發現少了什麼。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from tools.sitekit import card, esc

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "tw_coverage.json"
MARK = {"有": "🟢", "部分": "🟡", "缺": "🔴"}


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def sec_tw_coverage(eng=None) -> str:
    d = load()
    items = [x for x in d.get("items") or [] if isinstance(x, dict) and x.get("zh")]
    if not items:
        return ""
    n = {k: sum(x.get("status") == k for x in items) for k in MARK}
    todo = [x for x in items if x.get("status") != "有"]
    head = f'專業台股交易台會看的 {len(items)} 項，本站有 {n["有"]} 項、部分有 {n["部分"]} 項' + (f'、還缺 {n["缺"]} 項' if n["缺"] else "")
    lead = (head + f'；{"缺的" if n["缺"] else "還不完整的"}每天依序補上，下一項是「{todo[0]["zh"]}」。' if todo
            else f'專業台股交易台會看的 {len(items)} 項，本站都有了。')
    groups = []
    for g in dict.fromkeys(x.get("group", "") for x in items):
        rows = "".join(f'<tr><td>{MARK.get(x.get("status"), "")}</td><td><b>{esc(x["zh"])}</b>'
                       + (f'<div class="small muted">還要做：{esc(x["next"])}</div>' if x.get("next") else "") + "</td>"
                       f'<td class="small">{esc(x.get("where") or "—")}</td><td class="small muted">{esc(x.get("source") or "")}</td></tr>'
                       for x in items if x.get("group") == g)
        groups.append(f'<h3>{esc(g)}</h3><div class="scroll"><table class="mini"><thead><tr><th></th><th>項目</th><th>在哪裡看</th>'
                      f'<th>來源</th></tr></thead><tbody>{rows}</tbody></table></div>')
    body = (f'<p class="rimp"><b>一句話看懂：{esc(lead)}</b></p>'
            '<p class="small">這張清單是為了不讓「少了什麼」要等你發現：🔴 缺的每日排程依序補，Gemini 每週一核對有沒有漏列、幫忙找官方免費來源。</p>'
            + "".join(groups) + f'<p class="note">{esc(d.get("note") or "")}　更新 {esc(d.get("updated") or "—")}</p>')
    return card("台股覆蓋清單：專業交易台會看的，我們有沒有", "Taiwan coverage checklist", body, "wide")
