"""Gemini 第二意見（新聞日曆頁，2026-11-19）：Gemini App 排程動作讀本站題目清單、用 Google 搜尋後寫回 Google 文件的回答
（wsb/data/gemini_reply.py）。有來源網址的才當事實列；沒附網址的標「Gemini 推測、未證實」；傳聞另外標。
這張卡讓使用者不用自己去問 Gemini（使用者 11-18：「為何這些你都沒告訴我...我還要問 genimi」）。"""
from __future__ import annotations

from typing import Dict, List

from tools.sitekit import T, card, esc, fold_items


GROUP = {"D": "💬 和 Claude 的討論", "WIDE": "🌍 外面的世界", "TASK": "🔍 Claude 指定查證", "AN": "📝 分析師", "POL": "🏛 美國政策", "TW": "🏭 亞洲供應鏈", "EARN": "📅 財報預期",
         "FED": "🏦 聯準會", "SITE": "🛠 本站挑錯", "CALL": "🎙 法說會重點", "NEXT": "🔗 二階影響（推理）",
         "RED": "⚖️ 反方意見", "CAL": "🗓 行事曆核對", "SENT": "💬 散戶情緒（不是事實）", "WEEK": "📋 這週漏掉的", "BLIND": "🔭 本站的盲點"}
HIDE = ("CODE-",)                                           # the code audit is for Claude's daily task, not the public page


def _a(x: Dict) -> str:
    return f'{esc(x["t"])}' + (f' <a href="{esc(x["url"])}" target="_blank" rel="noopener">來源</a>' if x.get("url") else "")


def block(i: Dict, zh: Dict[str, str]) -> str:
    lab = next((v for k, v in GROUP.items() if i["sym"].startswith(k + "-")), None)
    if lab:                                                  # a section of research_feed/gemini_tasks.md, not a company
        out = [f'<h3>{lab} <span class="tk">{esc(i["sym"])}</span>：{esc(i["why"])}</h3><ul class="small">']
    else:
        out = [f'<h3>{esc(zh.get(i["sym"], ""))} <span class="tk">{esc(i["sym"])}</span>：{esc(i["why"])}</h3><ul class="small">']
    out += [f"<li>✅ 有來源：{_a(x)}</li>" for x in i.get("facts") or []]
    out += [f"<li>💬 傳聞：{_a(x)}</li>" for x in i.get("rumors") or []]
    out += [f"<li>❔ Gemini 推測、未證實：{esc(t)}</li>" for t in i.get("guess") or []]
    out += [f"<li>➕ Gemini 說本站漏掉：{_a(x)}</li>" for x in i.get("missed") or []]
    return "".join(out) + "</ul>"


def sec_gemini(eng) -> str:
    try:
        from wsb.data import gemini_reply as G
        d = G.refresh()
    except Exception:  # noqa: BLE001
        return ""
    items: List[Dict] = [i for i in d.get("items") or [] if not i["sym"].startswith(HIDE)]
    if not items:
        return ""
    try:
        from wsb.data.stocks import universe
        zh = {s: v[0] for s, v in ((universe().get("us") or {}).get("symbols") or {}).items()}
    except Exception:  # noqa: BLE001
        zh = {}
    nf = sum(len(i.get("facts") or []) for i in items)
    ng = sum(len(i.get("guess") or []) for i in items)
    cos = [i for i in items if not any(i["sym"].startswith(k + "-") for k in GROUP)]
    lead = (f"一句話看懂：Gemini 查了本站找不到原因的 {len(cos)} 家公司（另有 {len(items) - len(cos)} 條分析師、政策、供應鏈、財報預期等補充），找到 {nf} 條附來源的原因"
            + (f"，另有 {ng} 條沒附來源（只是推測）" if ng else "") + f"；" + (f"最大的一家是{zh.get(cos[0]['sym'], cos[0]['sym'])}：{cos[0]['why']}。" if cos else "。"))
    order = {k: n for n, k in enumerate(["D", "WIDE", "", "TASK", "POL", "CALL", "AN", "TW", "NEXT", "RED", "EARN", "FED", "CAL", "SENT", "WEEK", "BLIND", "SITE"])}
    key = lambda i: order.get(next((k for k in GROUP if i["sym"].startswith(k + "-")), ""), 0)  # noqa: E731
    blocks = [block(i, zh) for i in sorted(items, key=key)]
    extra = d.get("extra") or []
    tail = ("<h3>Gemini 另外提到的大事</h3><ul class='small'>" + "".join(f"<li>{_a(x)}</li>" for x in extra) + "</ul>") if extra else ""
    how = ("使用者 Antigravity 裡的 Gemini 自動化每小時讀本站的題目清單（/api/gemini_ask：今天動最多、本站找不到對得上新聞的公司），"
           "用 Google 搜尋回答後寫進 research_feed/gemini_reply.md；本站建置時讀取。來源必須是單篇文章，只給首頁的算「無法查證」。✅＝附了來源網址；💬＝傳聞；❔＝沒附來源，只是推測，不要當事實。Gemini 也會出錯，請點來源自己看。不構成投資建議。")
    when = f"　Gemini 回答時間：台北 {esc(d['when'])}" if d.get("when") else ""
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p>' + fold_items(blocks, 4, "家") + tail
            + f'<details class="sgx"><summary>{T("怎麼產生的", "How it is made")}</summary><p class="note">{T(how, "")}{when}</p></details>')
    return card("Gemini 第二意見：本站找不到原因的大動", "Gemini second opinion", body, "wide")
