"""政府做了什麼卡（新聞日曆分頁）：聯邦公報上和市場有關的正式政策文件，以及「先動的資產」在刊登當天的反應。"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Dict, Optional

import pandas as pd

from tools.sitekit import T, card, esc

RECENT = 14


def day_move(px: pd.Series, day: str, roll: bool = False) -> Optional[Dict]:
    """% move of the asset on `day` (close vs previous close) and its size next to a usual day (σ of 60 prior daily moves).
    roll=True: if `day` is not a trading day (signed on a weekend/holiday), use the next trading day within 4 days."""
    s = px.dropna() if px is not None else pd.Series(dtype=float)
    if not day:
        return None
    t = pd.Timestamp(day)
    if len(s) < 70:
        return None
    if t not in s.index:
        nxt = s.index[s.index > t]
        if not roll or not len(nxt) or (nxt[0] - t).days > 4:
            return None
        t = nxt[0]
    r = s.pct_change() * 100
    i = s.index.get_loc(t)
    if i < 61:
        return None
    sig = float(r.iloc[i - 60:i].std())
    return {"pct": float(r.iloc[i]), "k": abs(float(r.iloc[i])) / sig if sig else None, "day": t.strftime("%Y-%m-%d")}


def _today() -> date:
    return date.today()


def _retopic(FR, x: Dict) -> Dict:
    """Re-match the topic with today's rules, so a cache written under older rules does not keep a wrong asset."""
    t = FR.topic(x.get("title", ""))
    return {**x, **t} if t else x


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
    docs = [_retopic(FR, x) for x in docs]
    newest = max((x["date"] for x in docs if x.get("date")), default="")
    cut = (_today() - timedelta(days=RECENT)).isoformat()     # back from today, so a stuck feed cannot pass as "recent"
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

    items, big = [], 0
    for x in docs[:10]:
        routine = x.get("routine") or bool(FR.ROUTINE.search(x.get("title", "")))
        m = day_move(series(x["sym"]), x["date"])
        sg = x.get("signed")
        ms = day_move(series(x["sym"]), sg, roll=True) if sg and sg < x["date"] else None
        if not routine and x in recent and max((m or {}).get("k") or 0, (ms or {}).get("k") or 0) >= 2:
            big += 1
        eo = f'（第 {x["eo"]} 號）' if x.get("eo") else ""
        sign_txt = ""
        if sg and sg < x["date"]:
            when = f'簽署 {sg}' + (f'（遇休市，看下一個交易日 {ms["day"]}）' if ms and ms["day"] != sg else "")
            sign_txt = f'{esc(when)}：{esc(_mv(ms, x["sym_zh"]))}；'
        items.append(f'<li><span class="small muted">{esc(x["date"])}・{esc(FR.type_zh(x.get("type")))}{esc(eo)}・{esc(x.get("agency", ""))}</span><br>'
                     f'<b>{esc(x["topic"])}</b>' + ('<span class="small muted">（每年例行延長，內容不變）</span>' if routine else '')
                     + f'：<a href="{esc(x["url"])}" target="_blank" rel="noopener">{esc(x["title"])}</a><br>'
                     f'<span class="small">{sign_txt}刊登當天 {esc(_mv(m, x["sym_zh"]))}</span></li>')
    if big:
        lead += f'其中 {big} 項（不含每年例行延長）在簽署或刊登當天對應的資產大動，但同一天常有其他消息，要對照新聞。'
    note = (f'資料：<a href="{FR.PAGE}" target="_blank" rel="noopener">美國聯邦公報</a>官方 API。只收三類：總統文件、商務部工業安全局（出口管制）、'
            '貿易代表署（301 關稅）；用關鍵字挑出和市場有關的，主題與「先動的資產」是本站的對照表，不是 AI 判讀。'
            '刊登日通常比總統簽署或宣布晚幾天，新聞往往在簽署當天就出來，所以總統文件會同時列出「簽署當天」和「刊登當天」的漲跌'
            '（簽署日遇週末或假日，看下一個交易日；機關公告多半沒有簽署日）；這只是同一天發生，不說是這份文件造成的。'
            '「大動」是當天漲跌超過平常一天波動的 2 倍。標題保留英文原文，點進去可看全文。')
    body = (f'<p class="rimp big2"><b>{lead}</b></p>'
            f'<details class="sgx" open><summary>{T("最近 10 項政策文件", "Latest 10 documents")}</summary><ul>{"".join(items)}</ul></details>'
            f'<p class="note">{note}</p>')
    return card("政府做了什麼：美國正式公布的政策", "What Washington did: official policy actions", body, "wide")
