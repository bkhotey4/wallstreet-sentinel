"""Gemini 第二意見（新聞日曆頁，2026-11-19）：Gemini App 排程動作讀本站題目清單、用 Google 搜尋後寫回 Google 文件的回答
（wsb/data/gemini_reply.py）。有來源網址的才當事實列；沒附網址的標「Gemini 推測、未證實」；傳聞另外標。
這張卡讓使用者不用自己去問 Gemini（使用者 11-18：「為何這些你都沒告訴我...我還要問 genimi」）。"""
from __future__ import annotations

from typing import Dict, List

from tools.sitekit import T, card, esc, fold_items


def _a(x: Dict) -> str:
    return f'{esc(x["t"])}' + (f' <a href="{esc(x["url"])}" target="_blank" rel="noopener">來源</a>' if x.get("url") else "")


def block(i: Dict, zh: Dict[str, str]) -> str:
    if i["sym"].startswith("TASK"):                         # a check Claude asked for in research_feed/gemini_tasks.md
        out = [f'<h3>🔍 Claude 指定查證 <span class="tk">{esc(i["sym"])}</span>：{esc(i["why"])}</h3><ul class="small">']
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
    items: List[Dict] = d.get("items") or []
    if not items:
        return ""
    try:
        from wsb.data.stocks import universe
        zh = {s: v[0] for s, v in ((universe().get("us") or {}).get("symbols") or {}).items()}
    except Exception:  # noqa: BLE001
        zh = {}
    nf = sum(len(i.get("facts") or []) for i in items)
    ng = sum(len(i.get("guess") or []) for i in items)
    cos = [i for i in items if not i["sym"].startswith("TASK")]
    lead = (f"一句話看懂：Gemini 查了本站找不到原因的 {len(cos)} 家公司（另有 {len(items) - len(cos)} 題 Claude 指定查證），找到 {nf} 條附來源的原因"
            + (f"，另有 {ng} 條沒附來源（只是推測）" if ng else "") + f"；最大的一家是{zh.get(items[0]['sym'], items[0]['sym'])}：{items[0]['why']}。")
    blocks = [block(i, zh) for i in items]
    extra = d.get("extra") or []
    tail = ("<h3>Gemini 另外提到的大事</h3><ul class='small'>" + "".join(f"<li>{_a(x)}</li>" for x in extra) + "</ul>") if extra else ""
    how = ("使用者 Antigravity 裡的 Gemini 自動化每小時讀本站的題目清單（/api/gemini_ask：今天動最多、本站找不到對得上新聞的公司），"
           "用 Google 搜尋回答後寫進 research_feed/gemini_reply.md；本站建置時讀取。來源必須是單篇文章，只給首頁的算「無法查證」。✅＝附了來源網址；💬＝傳聞；❔＝沒附來源，只是推測，不要當事實。Gemini 也會出錯，請點來源自己看。不構成投資建議。")
    when = f"　Gemini 回答時間：台北 {esc(d['when'])}" if d.get("when") else ""
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p>' + fold_items(blocks, 4, "家") + tail
            + f'<details class="sgx"><summary>{T("怎麼產生的", "How it is made")}</summary><p class="note">{T(how, "")}{when}</p></details>')
    return card("Gemini 第二意見：本站找不到原因的大動", "Gemini second opinion", body, "wide")
