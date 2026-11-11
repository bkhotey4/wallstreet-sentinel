"""政府做了什麼卡（新聞日曆分頁）：聯邦公報上和市場有關的正式政策文件，以及「先動的資產」在刊登當天的反應。"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd

from tools.sitekit import T, card, esc

RECENT = 14


def day_move(px: pd.Series, day: str) -> Optional[Dict]:
    """% move of the asset on `day` (close vs previous close) and its size next to a usual day (σ of 60 prior daily moves)."""
    s = px.dropna() if px is not None else pd.Series(dtype=float)
    t = pd.Timestamp(day)
    if len(s) < 70 or t not in s.index:
        return None
    r = s.pct_change() * 100
    i = s.index.get_loc(t)
    if i < 61:
        return None
    sig = float(r.iloc[i - 60:i].std())
    return {"pct": float(r.iloc[i]), "k": abs(float(r.iloc[i])) / sig if sig else None}


def _mv(m: Optional[Dict], sym_zh: str) -> str:
    if not m:
        return f"{sym_zh}：當天沒有交易資料"
    size = "，大動" if (m["k"] or 0) >= 2 else "，比平常大一些" if (m["k"] or 0) >= 1 else ""
    return f'{sym_zh} {m["pct"]:+.1f}%{size}'


def sec_fed_register(eng) -> str:
    try:
        from wsb.data import fed_register as FR
        docs = FR.load().get("docs") or []
    except Exception:  # noqa: BLE001
        return ""
    if not docs:
        return ""
    newest = max(x["date"] for x in docs if x.get("date"))
    cut = (datetime.strptime(newest, "%Y-%m-%d") - timedelta(days=RECENT)).strftime("%Y-%m-%d")
    recent = [x for x in docs if (x.get("date") or "") >= cut]
    cnt = Counter(x["topic"] for x in recent)
    if recent:
        lead = (f'過去 {RECENT} 天，美國政府在聯邦公報正式刊登 {len(recent)} 項和市場有關的政策文件：'
                + "、".join(f"{k} {v} 項" for k, v in cnt.most_common()) + "。")
    else:
        lead = f'過去 {RECENT} 天聯邦公報上沒有和市場有關的新政策文件（最近一項在 {esc(newest)}）。'
    px = {}

    def series(sym):
        if sym not in px:
            try:
                px[sym] = eng.market.series(sym)
            except Exception:  # noqa: BLE001
                px[sym] = pd.Series(dtype=float)
        return px[sym]

    items = []
    for x in docs[:10]:
        m = day_move(series(x["sym"]), x["date"])
        eo = f'（第 {x["eo"]} 號）' if x.get("eo") else ""
        items.append(f'<li><span class="small muted">{esc(x["date"])}・{esc(FR.type_zh(x.get("type")))}{esc(eo)}・{esc(x.get("agency", ""))}</span><br>'
                     f'<b>{esc(x["topic"])}</b>：<a href="{esc(x["url"])}" target="_blank" rel="noopener">{esc(x["title"])}</a><br>'
                     f'<span class="small">刊登當天 {esc(_mv(m, x["sym_zh"]))}</span></li>')
    big = [x for x in docs[:10] if (day_move(series(x["sym"]), x["date"]) or {}).get("k", 0) and day_move(series(x["sym"]), x["date"])["k"] >= 2]
    if big:
        lead += f'其中 {len(big)} 項刊登當天對應的資產大動，但同一天常有其他消息，要對照新聞。'
    note = (f'資料：<a href="{FR.PAGE}" target="_blank" rel="noopener">美國聯邦公報</a>官方 API。只收三類：總統文件、商務部工業安全局（出口管制）、'
            '貿易代表署（301 關稅）；用關鍵字挑出和市場有關的，主題與「先動的資產」是本站的對照表，不是 AI 判讀。'
            '刊登日通常比總統簽署或宣布晚幾天，新聞往往在宣布當天就出來，所以市場反應可能早就發生；這裡只寫「刊登當天」，不說是這份文件造成的。'
            '「大動」是當天漲跌超過平常一天波動的 2 倍。標題保留英文原文，點進去可看全文。')
    body = (f'<p class="rimp big2"><b>{lead}</b></p>'
            f'<details class="sgx" open><summary>{T("最近 10 項政策文件", "Latest 10 documents")}</summary><ul>{"".join(items)}</ul></details>'
            f'<p class="note">{note}</p>')
    return card("政府做了什麼：美國正式公布的政策", "What Washington did: official policy actions", body, "wide")
