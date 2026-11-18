"""本週串起來看（新聞日曆頁第一張，2026-11-17）：tools/dots.py 找出的交集（程式），加上每日排程讀原文後寫的假設
（research_feed/dots_read.json，標明是假設，分開寫支持／反對／什麼能證實）。"""
from __future__ import annotations

import json
from typing import Dict, List

from tools.sitekit import T, card, esc, fold_items

KIND_ZH = {"sec": "SEC 申報", "earn": "財報", "policy": "政策", "ipo": "IPO", "pp": "出資 IPO", "doc": "原文補充"}


def _reads() -> Dict:
    from tools.dots import READ
    try:
        return json.loads(READ.read_text(encoding="utf-8")) if READ.exists() else {}
    except (OSError, ValueError):
        return {}


def build(eng=None) -> Dict:
    """dots.build() plus the events the daily task added after reading primary documents (dots_read.json 'events')."""
    import time
    from tools import dots as D
    from wsb.config import DATA_DIR
    rd = _reads()
    extra = [dict(e, kind=e.get("kind") or "doc") for e in rd.get("events") or [] if e.get("date") and e.get("syms")]
    if extra:                                              # into the archive first, so the clusters see them
        D.remember(extra, time.time(), DATA_DIR / "econ_dots_events.json")
    return D.build()


def _ev(e: Dict) -> str:
    link = f' <a href="{esc(e["url"])}" target="_blank" rel="noopener">原文</a>' if e.get("url") else ""
    return f'<li><span class="small muted">{esc(e["date"][5:].replace("-", "/"))}・{esc(KIND_ZH.get(e["kind"], e["kind"]))}</span> {esc(e["t"])}{link}</li>'


def _read_html(r: Dict) -> str:
    parts = [f'<p class="small"><b>可能的主線（假設，不是事實）</b>：{esc(r.get("hypothesis", ""))}</p>']
    for k, lab in (("for", "支持的證據"), ("against", "反對或還不確定的地方"), ("confirm", "什麼消息能證實或推翻")):
        if r.get(k):
            parts.append(f'<p class="small"><b>{lab}</b></p><ul class="small">' + "".join(f"<li>{esc(x)}</li>" for x in r[k]) + "</ul>")
    # 11-18: a read with plain-URL sources raised here and the whole card vanished from the page — accept both shapes
    src = [s if isinstance(s, dict) else {"url": str(s), "name": "原文"} for s in r.get("sources") or []]
    if src:
        parts.append('<p class="small muted">原文：' + "、".join(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s.get("name") or "原文")}</a>'
                                                         for s in src if s.get("url")) + "</p>")
    return "".join(parts)


def sec_dots(eng) -> str:
    from tools import dots as D
    try:
        d = build(eng)
    except Exception:  # noqa: BLE001
        return ""
    cl = d.get("clusters") or []
    if not cl:
        return ""
    rd = _reads()
    reads = {r.get("sym"): r for r in rd.get("reads") or [] if r.get("sym")}
    top = cl[0]
    lead = (f"一句話看懂：這 {len(cl)} 家公司在不同種類的事件裡重複出現，值得一起看；最多的是{top['zh']}"
            f"（{'、'.join(KIND_ZH[k] for k in top['kinds'])}）" + (f"，而且文件{'、'.join(top['flags'])}" if top["flags"] else "") + "。")
    blocks: List[str] = []
    for c in cl:
        r = reads.get(c["sym"])
        head = (f'<h3>{esc(c["zh"])} <span class="tk">{esc(c["sym"])}</span> <span class="small muted">'
                f'{"、".join(KIND_ZH[k] for k in c["kinds"])}' + (f'・文件{"、".join(c["flags"])}' if c["flags"] else "") + "</span></h3>")
        blocks.append(head + "<ul>" + "".join(_ev(e) for e in c["events"]) + "</ul>" + (_read_html(r) if r else
                      '<p class="small muted">這一組還沒有人讀原文寫假設；每日排程會挑最重要的幾組讀。</p>'))
    how = ("時間表由程式從本站各處已經抓到的事件組成：SEC 重大申報與人事（含「文件沒說的」標記，例如離職沒寫原因、立即生效、同日換董事長）、"
           f"市值 {D.EARN_FLOOR / 1e8:,.0f} 億美元以上的財報日、聯邦公報與商務部工業安全局的政策（依主題對應到 AI 產業鏈公司）、即將上市的 IPO 與同步私募的出資者；"
           "範圍是過去 10 天到未來 7 天。同一家公司在兩種以上的事件裡出現就列一組。交集只代表「值得一起看」，不代表有因果；"
           "「可能的主線」是每日排程讀原始文件後寫的假設，一定附上反對的理由和能證實的消息。不是投資建議。")
    upd = f"　假設更新 {esc(rd.get('updated'))}" if rd.get("updated") else ""
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p>' + fold_items(blocks, 3, "組")
            + f'<details class="sgx"><summary>{T("怎麼產生的", "How it is made")}</summary><p class="note">{T(how, "")}{upd}</p></details>')
    return card("本週串起來看：同一家公司、不同的事", "Connecting the week's events", body, "wide")
