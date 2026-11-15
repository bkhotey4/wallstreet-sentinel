"""法院與監管機關的決定卡（新聞日曆分頁，2026-11-16 使用者選的第 8 項）。資料在 wsb/data/rulings.py；當天漲跌沿用聯邦公報卡的算法。"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

import pandas as pd

from tools.sitekit import T, card, esc
from tools.site_fedreg import _mv, day_move

RECENT = 30


def sec_rulings(eng) -> str:
    try:
        from wsb.data import rulings as RL
        items = RL.load().get("items") or []
    except Exception:  # noqa: BLE001
        return ""
    if not items:
        return ""
    cut = (date.today() - timedelta(days=RECENT)).isoformat()
    recent = [x for x in items if x.get("date", "") >= cut]
    cnt = Counter(RL.SRC_ZH.get(x["src"], x["src"]) for x in recent)
    mk = [x for x in recent if x.get("topic")]
    lead = (f"過去 {RECENT} 天：" + ("、".join(f"{k} {v} 項" for k, v in cnt.most_common()) if cnt else "沒有新的判決或規則")
            + (f"；其中 {len(mk)} 項和市場直接有關（{'、'.join(sorted({x['topic'] for x in mk}))}）。" if mk else "。"))
    px = {}

    def series(sym):
        if sym not in px:
            try:
                px[sym] = eng.market.series(sym)
            except Exception:  # noqa: BLE001
                px[sym] = pd.Series(dtype=float)
        return px[sym]
    rows = ""
    for x in items[:25]:
        mv = _mv(day_move(series(x["sym"]), x["date"], roll=True), x["sym_zh"]) if x.get("sym") else "—"
        rows += (f'<tr><td class="nw">{esc(x["date"])}</td><td class="nw">{esc(RL.SRC_ZH.get(x["src"], x["src"]))}</td>'
                 f'<td><a href="{esc(x["url"])}" target="_blank" rel="noopener">{esc(x["title"])}</a>'
                 + (f'<div class="small muted">{esc(x["sum"][:220])}</div>' if x.get("sum") else "")
                 + f'</td><td class="small">{esc(x.get("topic") or "—")}</td><td class="small">{esc(mv)}</td></tr>')
    head = (f'<tr><th>{T("日期", "Date")}</th><th>{T("機關", "Body")}</th><th>{T("決定", "Decision")}</th>'
            f'<th>{T("主題", "Topic")}</th><th>{T("當天最先會動的資產", "First-moving asset that day")}</th></tr>')
    chain = ("<b>為什麼要看</b>：法院判決和監管規則是「規則本身變了」：例如關稅能不能照課、聯準會理事能不能被撤換、預測市場歸誰管、"
             "公司要多揭露什麼。規則一改，最先動的是直接被管到的資產（利率、指數、某個產業），然後才傳到其他地方。")
    note = ("來源：最高法院官方判決頁（本年度與上一年度開庭期）、SEC 與 CFTC 官方新聞稿 RSS（只留規則與市場結構）、司法部官方新聞 RSS（只留反壟斷）。"
            "FTC 的新聞 RSS 網址目前回 404，沒有收。「當天」用判決或公布那一天的收盤，遇休市用下一個交易日；同一天常有其他消息，"
            "漲跌不一定是這件事造成的。標題保留英文原文，避免翻錯法律用語。")
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{lead}</p><p>{chain}</p>'
            f'<details><summary>最近的判決與規則</summary><div class="scroll"><table class="mini"><thead>{head}</thead><tbody>{rows}</tbody></table></div></details>'
            f'<p class="note">{note}</p>')
    return card("法院與監管：判決、新規則、反壟斷", "Courts & regulators", body, "wide",
                sub="最高法院判決、SEC／CFTC 規則、司法部反壟斷，和當天最先會動的資產")
