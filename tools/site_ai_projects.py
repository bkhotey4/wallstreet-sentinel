"""AI 資料中心專案清單（AI 視角看風險；2026-11-28）。

使用者 11/28 拿 OpenAI 8/17 公告的 PORTS-Pike 專案（8 GW、SB Energy／NVIDIA／美國能源部）問「為何網頁上沒有相關資料」。
網站的新聞只留 30 天、公司部落格公告也不是新聞來源，而且沒有任何地方整理「已宣布的大型 AI 資料中心專案」：
誰出錢、多大、什麼時候上線、電從哪來、要等哪些條件。這些專案決定 AI 資本支出會不會真的變成訂單，也是泡沫風險的來源
（承諾很大、條件很多）。資料在 research_feed/ai_projects.json，每一列都要附公司或政府的官方原文網址（Gemini IND 段協助找，
Claude 讀過原文才放上來）。卡片不估算金額，只整理原文寫了什麼。"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, esc, fold_rows

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "ai_projects.json"


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except (OSError, ValueError):
        return {}


def lead(items: List[Dict]) -> str:
    """Pure: totals and the one thing the reader should take away — these are conditional promises with dates years out."""
    gw = sum(float(x.get("gw") or 0) for x in items)
    late = [x for x in items if "2028" in str(x.get("first")) or "2029" in str(x.get("first")) or "2030" in str(x.get("first"))]
    s = f"一句話看懂：這裡整理了 {len(items)} 個已宣布的大型 AI 資料中心專案，合計約 {gw:,.1f} GW（吉瓦）的運算容量。"
    if late:
        s += f"其中 {len(late)} 個的第一期要到 2028 年以後才上線，"
    s += ("這些都是「有條件的承諾」：要等電廠、輸電線、許可與融資到位才會變成真的訂單。對你的意思：AI 供應鏈未來幾年的訂單能見度"
          "很大一部分建立在這些承諾上；如果融資變貴或電力跟不上而延期，最先受影響的是預期最高的伺服器、電力與散熱股。")
    return s


def sec_ai_projects(eng=None) -> str:
    d = load()
    items = sorted((x for x in d.get("items") or [] if x.get("name")), key=lambda x: str(x.get("date")), reverse=True)
    if not items:
        return ""
    trs = []
    for x in items:
        src = "、".join(f'<a href="{esc(s.get("url"))}" target="_blank" rel="noopener">{esc(s.get("name"))}</a>'
                        for s in x.get("src") or [] if str(s.get("url") or "").startswith("https://"))
        trs.append(f'<tr><td class="nw">{esc(x.get("date"))}</td><td><b>{esc(x["name"])}</b><div class="small">{esc(x.get("who"))}</div></td>'
                   f'<td class="r">{esc(str(x.get("gw") or "—"))}</td><td class="small">{esc(x.get("first"))}<div class="muted">{esc(x.get("phase"))}</div></td>'
                   f'<td class="small">{esc(x.get("power"))}</td><td class="small">{esc(x.get("terms"))}<div class="muted">條件：{esc(x.get("conditions"))}</div></td>'
                   f'<td class="small">{esc(x.get("tw"))}</td><td class="small">{src}</td></tr>')
    head = ('<tr><th>宣布</th><th>專案與參與者</th><th class="r">規模（GW）</th><th>什麼時候上線</th><th>電從哪來</th>'
            '<th>合約與條件</th><th>和台灣的關係</th><th>官方原文</th></tr>')
    note = ("每一列都只寫公司或政府官方原文說了什麼（例如容量、時程、誰出錢），不估算金額；「和台灣的關係」若公告沒提，會標「推論」。"
            "GW（吉瓦）是電力容量，1 GW 約等於一座大型核電機組。資料由 Gemini 協助找官方公告、Claude 讀過原文後加入，"
            f"最後更新 {esc(d.get('updated') or '—')}。新聞只留 30 天，所以舊的大型專案放在這裡，不會被洗掉。")
    return card("AI 資料中心專案清單：誰承諾蓋多大、什麼時候上線", "Announced AI data-center projects",
                f'<p class="rimp big2"><b>{esc(lead(items))}</b></p>' + fold_rows(trs, 10, head, "個專案") + f'<p class="note">{note}</p>', "wide")
