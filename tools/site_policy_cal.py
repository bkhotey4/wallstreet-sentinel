"""政策時程表（新聞日曆頁；2026-11-28 總經缺口盤點）：美國政府已經排定、還沒發生的政策日期。

起因：301 條款那次（11/25 對 14 個經濟體提議加關稅）網站事後才串起來；更早的「意見徵詢截止」「公聽會」「生效日」其實都寫在
聯邦公報的文件裡。這張卡從 wsb/data/fed_register 讀總統文件、商務部工業安全局（出口管制）、貿易代表署（301 等）、
財政部海外資產控制辦公室（制裁）與醫療保險規則的「意見截止日、生效日、DATES 段落裡的日期」，列出接下來 60 天的每一步，
附原文與「先動的資產」。全自動，不靠人工維護。"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

from tools.sitekit import card, esc, fold_rows

HORIZON = 60


def rows(docs: List[Dict], today: date, horizon: int = HORIZON) -> List[Dict]:
    from wsb.data import fed_register as FR
    end = (today + timedelta(days=horizon)).isoformat()
    out = []
    for d in docs:
        if d.get("routine"):
            continue
        for step in FR.timeline(d, today):
            if step["date"] <= end:
                out.append({**step, "doc": d})
    return sorted(out, key=lambda x: (x["date"], x["doc"].get("topic") or ""))


def sec_policy_calendar(eng=None) -> str:
    from wsb.data import fed_register as FR
    d = FR.load()
    today = date.today()
    rs = rows(d.get("docs") or [], today)
    if not rs:
        return ""
    topics: Dict[str, int] = {}
    for r in rs:
        topics[r["doc"].get("topic") or "其他"] = topics.get(r["doc"].get("topic") or "其他", 0) + 1
    first = rs[0]
    lead = (f"一句話看懂：接下來 {HORIZON} 天，美國政府已經排定 {len(rs)} 個政策日期（"
            + "、".join(f"{k} {v} 個" for k, v in sorted(topics.items(), key=lambda x: -x[1])) + "）；"
            f"最近的是 {first['date'][5:]}「{first['doc'].get('topic')}」：{first['what'][:40]}。"
            "對你的意思：關稅、出口管制和制裁常在這些日期前後定案或生效，市場通常在日期前就開始反應；"
            "日期本身不代表結果，結果要看當天的官方文件。")
    trs = [f'<tr><td class="nw"><b>{esc(r["date"][5:])}</b></td><td class="small">{esc(r["doc"].get("topic") or "")}'
           f'<div class="muted">先動：{esc(r["doc"].get("sym_zh") or "")}</div></td>'
           f'<td class="small">{esc(r["what"])}</td>'
           f'<td class="small"><a href="{esc(r["doc"].get("url") or "")}" target="_blank" rel="noopener">{esc((r["doc"].get("title") or "")[:140])}</a>'
           f'<div class="muted">{esc(r["doc"].get("agency") or "")}・{esc(FR.type_zh(r["doc"].get("type") or ""))}・刊登 {esc((r["doc"].get("date") or "")[5:])}</div></td></tr>'
           for r in rs]
    head = '<tr><th>日期</th><th>主題</th><th>這一天發生什麼（原文）</th><th>文件</th></tr>'
    note = ("來源：美國聯邦公報 API（總統文件、商務部工業安全局、貿易代表署、財政部海外資產控制辦公室、醫療保險與醫療補助服務中心），"
            "取每份文件的意見徵詢截止日、生效日，以及文件「DATES」段落裡寫到的日期（例如公聽會），只列還沒到的。"
            "「這一天發生什麼」保留英文原文以免翻譯失真；「先動」是這類消息過去最先反應的資產。例行的展期、名單更新不列。")
    return card("政策時程表：美國政府接下來哪天會做什麼", "Policy calendar: scheduled US government dates",
                f'<p class="rimp big2"><b>{esc(lead)}</b></p>' + fold_rows(trs, 12, head, "個日期") + _auctions() + f'<p class="note">{note}</p>', "wide")


TERM_ZH = {"Year": "年", "Month": "個月"}


def _term(t: str) -> str:
    """'9-Year 11-Month' → '10 年期（增額）' style: round reopenings to the original tenor people know."""
    import re
    m = re.match(r"(\d+)-Year(?: (\d+)-Month)?", t or "")
    if not m:
        return t or ""
    y = int(m.group(1)) + (1 if m.group(2) and int(m.group(2)) >= 6 else 0)
    return f"{y} 年期"


def _auctions() -> str:
    """接下來的中長期美債標售（TreasuryDirect 官方 API）：長天期標售需求不好時，殖利率常當天急升。"""
    try:
        from wsb.data import ust_auctions as UA
        items = [x for x in UA.load().get("items") or [] if x.get("issue")]
    except Exception:  # noqa: BLE001
        items = []
    if not items:
        return ""
    lis = "".join(f'<li>{esc(x["announce"][5:])} 公布規模 → {esc(x["issue"][5:])} 交割：<b>{esc(_term(x["term"]))}{"（增額）" if x.get("reopen") else ""}</b>'
                  + (f'，{x["amount_b"] * 10:,.0f} 億美元' if x.get("amount_b") else "")
                  + '</li>' for x in items[:10])
    return ('<h3>接下來的中長期美債標售</h3><ul class="small">' + lis + '</ul>'
            '<p class="small muted">標售日在公布日與交割日之間（財政部 API 沒有給確切標售日，以財政部公告為準）。'
            '對你的意思：10 年、30 年期標售時，若得標倍數偏低、得標殖利率比市場高（尾差），長期利率常當天急升，房貸與成長股跟著受壓。</p>')
