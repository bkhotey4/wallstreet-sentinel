"""債市深度判讀 (top of AI 視角看債券): a daily cloud routine writes research_feed/bonds.json: why rates moved, how each
Treasury auction went, what credit investors are doing, the big borrowers worth watching, and what other countries' bonds
say.  Static content: the routine commits the JSON and the site shows it as written."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "bonds.json"   # public repo only
TREND = {"改善": "up", "惡化": "dn"}


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


def _rows(xs, *keys) -> List[Dict]:
    return [x for x in xs or [] if isinstance(x, dict) and all(x.get(k) for k in keys)]


def _lines(title: str, xs: List[Dict]) -> str:
    rows = "".join(f'<li><b>{_e(x["name"])}</b>：{_e(x["read"])}' + (f'<div class="small muted">{_e(x["evidence"])}</div>' if x.get("evidence") else "") + "</li>" for x in xs)
    return f'<details class="sgx"><summary>{title}</summary><ul class="small">{rows}</ul></details>' if rows else ""


def _auctions(xs: List[Dict]) -> str:
    if not xs:
        return ""
    rows = "".join(f'<tr><td>{_e(str(x["date"])[5:])}</td><td>{_e(x["what"])}</td><td class="r">{_e(x.get("cover"))}</td><td>{_e(x["read"])}</td></tr>' for x in xs)
    return ('<p class="small"><b>公債標售</b>（政府借錢時，買家夠不夠踴躍）</p><div class="scroll"><table class="mini"><thead><tr><th>日期</th><th>標的</th>'
            f'<th class="r">投標倍數</th><th>結果</th></tr></thead><tbody>{rows}</tbody></table></div>')


def _issuers(xs: List[Dict]) -> str:
    rows = "".join(f'<li><b>{_e(x["name"])}</b> <b class="{TREND.get(x.get("trend"), "")}">{_e(x.get("trend"))}</b>：{_e(x["read"])}</li>' for x in xs)
    return f'<details class="sgx"><summary>誰在大量借錢（{len(xs)} 家）</summary><ul class="small">{rows}</ul></details>' if rows else ""


def sec_bond_read(eng) -> str:
    d = load()
    if not d.get("one"):
        return ""
    paras = [f"<p>{_e(p)}</p>" for p in d.get("story") or [] if p]
    story = (paras[0] + (f'<details class="sgx"><summary>看完整解讀</summary>{"".join(paras[1:])}</details>' if paras[1:] else "")) if paras else ""
    body = (f'<p class="rimp big2"><b>一句話看懂：{_e(d["one"])}</b></p>{story}'
            + _auctions(_rows(d.get("auctions"), "date", "what", "read"))
            + _lines("利率為什麼動：拆開來看", _rows(d.get("drivers"), "name", "read"))
            + _lines("公司債：借錢給企業的人在想什麼", _rows(d.get("credit"), "name", "read"))
            + _issuers(_rows(d.get("issuers"), "name", "read"))
            + _lines("其他國家的債市", _rows(d.get("world"), "name", "read"))
            + (f'<p class="small"><b>接下來看</b>：{_e(d["next"])}</p>' if d.get("next") else "")
            + (f'<p class="small muted">來源：{_src(d.get("sources"))}</p>' if d.get("sources") else "")
            + f'<p class="note">每個交易日早上由雲端 AI 整理，{_e(d.get("updated"))} 更新。是對當下的解讀，不是預測保證。不構成投資建議。</p>')
    return card("債市深度判讀", "Bond market read", body, "wide", sub="利率、標售、公司債與大型借款人")
