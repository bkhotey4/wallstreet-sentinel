"""AI 視角看風險頁：獨立 AI 觀察員。雲端排程（每個交易日台北 07:00、21:00）讓另一個 AI 自己去找「人類在怕什麼」，再自己抓官方數據
逐條判決，寫進 research_feed/ai_view.json（公開網站 repo）。這裡只負責顯示；網站 CI 讀本地檔，本機 bot 從 raw GitHub 讀快取。"""
from __future__ import annotations

import json
from pathlib import Path

from tools.site_ai import _anchor
from tools.sitekit import T, card, esc, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "ai_view.json"   # public site repo root, never synced over
VERDICT_EMO = {"恐慌有根據": "🔴", "部分有根據": "🟠", "恐慌被誇大": "🟢", "數據很平靜": "🟢"}
JUDGE_CLS = {"數據支持": "dn", "部分支持": "muted", "被誇大": "up", "數據不支持": "up"}


def load() -> dict:
    try:
        if FILE.exists():
            return json.loads(FILE.read_text(encoding="utf-8"))
        from wsb.data import stability as ST
        return ST.load().get("ai_view") or {}
    except Exception:  # noqa: BLE001
        return {}


def _link(url: str, text: str) -> str:
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(text)}</a>' if str(url).startswith("https://") else esc(text)


def _txt(s) -> str:
    return esc(guard_safe(str(s or "")))


@_anchor("ai-observer")
def sec_ai_observer(eng) -> str:
    v = load()
    if not v.get("verdict"):
        body = (f'<p>{T("獨立 AI 觀察員還沒有第一份判讀。它會在每個交易日台北 07:00（美股收盤後）和 21:00（美股開盤前）自動執行。", "")}</p>'
                f'<p class="note">{T(NOTE, "")}</p>')
        return card("獨立 AI 觀察員：大家說的大跌是真的嗎？", "Independent AI observer", body, "wide")
    emo = VERDICT_EMO.get(v["verdict"], "⚪")
    rows = ""
    for n in v.get("narratives") or []:
        data = "；".join(_link(d.get("url", ""), f"{d.get('name', '')} {d.get('value', '')}") + (f"（{esc(d.get('date', ''))}）" if d.get("date") else "")
                        for d in n.get("data") or [])
        rows += (f'<tr><td><b>{_txt(n.get("claim"))}</b>' + (f'<br><span class="small muted">{_link(n.get("source", ""), "媒體來源")}</span>' if n.get("source") else "")
                 + f'</td><td class="{JUDGE_CLS.get(n.get("judgement"), "muted")}"><b>{_txt(n.get("judgement"))}</b></td>'
                 f'<td class="small">{_txt(n.get("reason"))}' + (f'<br><span class="muted">{data}</span>' if data else "") + "</td></tr>")
    watch = "".join(f"<li>{_txt(w)}</li>" for w in v.get("watch") or [])
    hist = "".join(f'<li>{esc(h.get("time", ""))}：{VERDICT_EMO.get(h.get("verdict"), "⚪")} <b>{_txt(h.get("verdict"))}</b>——{_txt(h.get("summary"))}</li>'
                   for h in (v.get("history") or [])[:20])
    head = f"{emo} {v['verdict']}：{guard_safe(v.get('summary', ''))}"
    body = (f'<p class="rimp big2"><b>{T(head, "")}</b></p>'
            f'<p class="small muted">{T("這次判讀時間：" + str(v.get("updated", "")) + "（台北）", "")}</p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("人類在怕什麼", "What people fear")}</th><th>{T("判決", "Verdict")}</th>'
            f'<th>{T("理由與數據", "Reason and data")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            + (f'<div class="aiwatch"><b>{T("出現這些，判讀才會改變", "")}</b><ul>{watch}</ul></div>' if watch else "")
            + (f'<details class="sgx"><summary>{T("看過去的判讀紀錄", "Past verdicts")}</summary><ul class="small">{hist}</ul></details>' if hist else "")
            + f'<p class="note">{T(NOTE, "")}</p>')
    return card("獨立 AI 觀察員：大家說的大跌是真的嗎？", "Independent AI observer", body, "wide")


NOTE = ("這是另一個獨立運作的 AI：它先搜尋最近 48 小時媒體與自媒體在講的市場恐慌，再自己去官方來源（OFR 金融壓力指數、FRED 信用利差與殖利率、"
        "CFTC 大錢部位等）抓數據逐條查證，不讀本站其他卡片的結論。新聞只用來找出「人類在怕什麼」，判決只看數據。"
        "每個交易日台北 07:00 與 21:00 更新；判讀改變時 Discord 會通知。它描述風險是真是假，不給任何買賣建議，也不預測哪一天漲跌。")


def tile() -> tuple:
    v = load()
    if not v.get("verdict"):
        return ("ai-observer", "⚪ 獨立 AI 觀察員", "待第一次判讀", "每個交易日台北 07:00、21:00", "")
    return ("ai-observer", f"{VERDICT_EMO.get(v['verdict'], '⚪')} 獨立 AI 觀察員", v["verdict"],
            f"{v.get('updated', '')}・{len(v.get('narratives') or [])} 個恐慌敘事逐條查證", "")
