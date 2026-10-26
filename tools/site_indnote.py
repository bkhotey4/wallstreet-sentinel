"""每週產業分析筆記 (top of 產業體檢): written every Saturday by a cloud routine into research_feed/industry_note.json — the
all 11 sectors (one line each), tech sub-industries, plus one focus industry picked from the site's own data.  Same format and
rules as the Taiwan note (data and history only, sources listed, no advice)."""
from __future__ import annotations

import html
from pathlib import Path

from tools.site_twmacro import _note_html, load_note
from tools.sitekit import card

NOTE = Path(__file__).resolve().parents[1] / "research_feed" / "industry_note.json"   # public repo only


def sec_industry_note(eng) -> str:
    notes = load_note(NOTE)
    if not notes:
        return ""
    e = lambda x: html.escape(str(x or ""))  # noqa: E731
    sec = [x for x in (notes[0].get("sectors") or []) if isinstance(x, dict) and x.get("name") and x.get("read")]
    rows = "".join(f'<tr><td class="nw"><b>{e(x["name"])}</b>' + (f'<div class="small muted">{e(x.get("state"))}</div>' if x.get("state") else "")
                   + f'</td><td>{e(x["read"])}</td></tr>' for x in sec)
    table = (f'<h3>各產業一句話</h3><div class="scroll"><table class="mini"><thead><tr><th>產業</th><th>這週的重點</th></tr></thead>'
             f'<tbody>{rows}</tbody></table></div>') if rows else ""
    old = "".join(f'<details class="sgx"><summary>{html.escape(str(n["month"]))}</summary>{_note_html(n)}</details>' for n in notes[1:6])
    note = ("每週六由 AI 分析任務讀取公開資料（公司財報與新聞稿、台積電月營收、記憶體價格、新雲端公司的債券與股價、本站產業體檢數據），"
            "整理成白話的產業筆記：11 大產業各一句（科技、通訊服務、非必需消費、必需消費、金融、工業、原物料、能源、醫療保健、公用事業、不動產），"
            "科技再細分半導體、記憶體、AI 伺服器、雲端與 GPU 雲端、軟體，另外依本站數據自動挑選一個「本週焦點產業」深入寫。"
            "只寫數據與歷史比較，不寫預測與買賣建議；AI 整理可能有誤，請以原始資料為準。")
    return card("每週產業分析筆記（AI 自動整理）", "Weekly industry note", _note_html(notes[0]) + table + old + f'<p class="note">{note}</p>', "wide")
