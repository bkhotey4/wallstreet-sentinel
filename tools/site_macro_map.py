"""總經全貌卡（全方位風險頁最上面；2026-11-28，wsb/analytics/macro_map）。

一張表放所有面向：現在的方向、關鍵數字、對讀者的意思；上面一句話講整體在哪個階段、幾個面向在轉壞、最大的矛盾，
下面列互相打架的訊號與這週翻轉的面向。規則固定（一個月變化＋門檻），不是 AI 判讀；AI 寫的總經口播與預判在別張卡。"""
from __future__ import annotations

from typing import Dict

from tools.sitekit import card, esc

LAST: Dict = {}                       # the last build, written to macro_map.json for the AI routines
LIGHT = {1: ("🔴", "轉壞"), 0: ("🟡", "持平"), -1: ("🟢", "轉好"), None: ("⚪", "資料不足")}
# what each pillar's direction means for an ordinary reader (transmission written once, as logic — not data)
MEAN = {
    "growth": {1: "裁員與失業可能增加，企業獲利預期下修；聯準會降息的理由變多。", -1: "就業與消費撐得住，企業獲利有支撐。", 0: "就業和消費沒有明顯變化。"},
    "inflation": {1: "物價壓力回升，聯準會更難降息，房貸與借錢成本降不下來。", -1: "物價壓力在退，降息空間變大。", 0: "通膨沒有明顯變化。"},
    "rates": {1: "借錢變貴：房貸、企業融資與高估值成長股承壓，新台幣容易偏弱。", -1: "借錢變便宜，對成長股與房市有利。", 0: "利率沒有大動。"},
    "treasury": {1: "美債的真實成本或風險溢價在升、買家在減少：長期利率不容易降，房貸與高估值股票的壓力不會因為降息預期就消失。",
                 -1: "美債需求穩、實質利率在降：長期借錢成本有機會鬆一點，對成長股與房市有利。",
                 0: "美債的供需與定價沒有明顯變化。"},
    "pricing": {1: "價格在押避險：資金躲進大型股、必需消費與黃金，市場對景氣的信心比數據悲觀。",
                -1: "價格在押景氣與風險：資金願意買小型股、景氣循環與新興市場。",
                0: "跨資產的訊號沒有一致方向。"},
    "earnings": {1: "分析師在下修企業獲利：股價下跌開始有基本面理由，不只是估值修正。", -1: "分析師還在上修獲利：基本面撐著，下跌比較像估值或情緒。",
                 0: "獲利預期上修和下修差不多。"},
    "positioning": {1: "部位擁擠或恐慌升高：市場比較脆弱，壞消息容易被放大。", -1: "部位不擁擠：市場有承受壞消息的空間。", 0: "部位沒有特別擁擠。"},
    "credit": {1: "借錢給公司的人開始擔心，體質弱的公司借新還舊變難，常比股市早反應。", -1: "信用市場平靜，企業借錢順利。", 0: "金融條件沒有明顯變化。"},
    "liquidity": {1: "市場上的錢在變少，風險資產少了一股推力。", -1: "市場上的錢在變多，對股市與加密資產有利。", 0: "流動性沒有明顯變化。"},
    "dollar": {1: "美元轉強或亞洲貨幣轉弱：外資容易從台灣等亞洲市場把錢換回美元。", -1: "美元轉弱，資金比較願意留在亞洲。", 0: "匯率沒有大動。"},
    "global": {1: "日本或歐洲的長期利率在升、或美日利差在縮：日本資金比較想留在國內，借日圓買海外資產的部位有被迫平倉的風險，美債與美股少一股買盤。",
               -1: "日本長期利率整體在降、歐洲金融壓力低：日本資金沒有被拉回國內的壓力，海外資金比較願意留在美債與美股。", 0: "日本與歐洲的利率和金融壓力沒有大動。"},
    "ai": {1: "AI 股比大盤弱：台股電子、伺服器、記憶體的訂單預期可能被下修。", -1: "AI 股比大盤強：台灣供應鏈的訂單預期還在往上。", 0: "AI 股和大盤差不多。"},
    "china": {1: "中國需求或信心轉弱：原物料、航運與對中出口的台廠承壓。", -1: "中國與原物料回溫，對景氣循環股有利。", 0: "中國與原物料沒有明顯變化。"},
    "taiwan": {1: "台股走弱：前面幾個面向的壓力傳到了台灣。", -1: "台股走強。", 0: "台股沒有大動。"},
}


MIXED = {"inflation": "核心物價在加速，但油價與通膨預期在降：聯準會最看重核心，降息不會因為油價跌就變容易。"}


def _mean(p: Dict) -> str:
    if p.get("mixed") and p["state"] == 0:
        if p["key"] == "inflation" and p.get("core_up"):
            return MIXED["inflation"]
        return "裡面的訊號互相拉扯（見關鍵數字），方向還沒定，要看哪一邊先延續。"
    return MEAN.get(p["key"], {}).get(p["state"], "—")


def lead(m: Dict) -> str:
    ps = [p for p in m["pillars"] if p["state"] is not None]
    if not ps:
        return "一句話看懂：總經資料暫時不足，無法判斷全貌。"
    s = "一句話看懂："
    if m.get("regime"):
        s += f"成長和通膨的組合目前偏向「{m['regime']['name']}」。"
    s += f"{len(m['pillars'])} 個面向裡 {len(m['worse'])} 個在轉壞" + (f"（{'、'.join(m['worse'])}）" if m["worse"] else "") + \
         f"、{len(m['better'])} 個在轉好。"
    if m.get("conflicts"):
        s += "最該注意的矛盾：" + m["conflicts"][0]
    elif len(m["worse"]) >= 5:
        s += "壓力分布在多個面向，不是單一事件，通常比單點壞消息更難很快過去。"
    elif len(m["worse"]) <= 2:
        s += "壓力集中在少數面向，整體還沒有連成一片。"
    return s


def extras(eng) -> Dict:
    """Earnings revisions and margin debt, read the same way the cards that show them do."""
    out: Dict = {}
    try:
        from wsb.data import est_revisions as ER
        out["estrev"] = ER.view()
    except Exception:  # noqa: BLE001
        pass
    try:
        from wsb.data import fedwatch as FW
        out["fedwatch"] = FW.view(eng)
    except Exception:  # noqa: BLE001
        pass
    try:                                   # 集保：追蹤名單裡「大戶減、散戶增」的家數（滿兩週才有）
        from wsb.data import tw_holders as TWH
        from wsb.data.stocks import universe
        codes = {s.split(".")[0] for s in (universe().get("tw") or {}).get("symbols") or {}}
        d = TWH.load()
        ch = [c for c in TWH.changes(d) if c["code"] in codes]
        if ch:
            out["holders"] = {"n": len(ch), "week": max(d.get("weeks") or {"": 0}),
                              "dist": sum(1 for c in ch if c["d_big"] < 0 and c["d_small_n"] > 0),
                              "accum": sum(1 for c in ch if c["d_big"] > 0 and c["d_small_n"] < 0)}
        elif d.get("weeks"):
            out["holders"] = {"note": "集保大戶／散戶從 " + min(d["weeks"]) + " 開始每週存一份，滿兩週後比較"}
    except Exception:  # noqa: BLE001
        pass
    try:                                   # 近 5 週美債標售的好壞（wsb.data.treasury.judge）
        from datetime import datetime, timedelta, timezone
        from wsb.analytics.macro_map import auction_tally
        today = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d")
        out["auctions"] = auction_tally(eng.treasury.auctions, today)
    except Exception:  # noqa: BLE001
        pass
    try:                                   # 日本公債（財務省）＋歐元區 CISS（歐洲央行）
        out["jgb"] = {t: eng.global_yields.get(t) for t in ("10Y", "30Y")}
    except Exception:  # noqa: BLE001
        pass
    try:
        import pandas as pd
        from wsb.data import euro_asia as EA
        c = EA.load().get("ciss") or {}
        if c:
            cs = pd.Series(c)
            cs.index = pd.to_datetime(cs.index)
            out["ciss"] = cs.sort_index().astype(float)
    except Exception:  # noqa: BLE001
        pass
    try:
        y = eng.margin_debt.yoy()
        if y is not None and len(y.dropna()):
            out["margin_yoy"] = float(y.dropna().iloc[-1])
    except Exception:  # noqa: BLE001
        pass
    return out


def sec_macro_map(eng) -> str:
    from wsb.analytics import macro_map as MM
    try:
        m = MM.build(eng.fred, eng.market, extras=extras(eng))
    except Exception:  # noqa: BLE001
        return ""
    LAST.clear()
    LAST.update(m)
    trs = []
    for p in m["pillars"]:
        ic, lab = ("🟠", "分歧") if p.get("mixed") and p["state"] == 0 else LIGHT[p["state"]]
        trs.append(f'<tr><td><b>{esc(p["zh"])}</b></td><td class="nw">{ic} {lab}</td>'
                   f'<td class="small">{esc("；".join(p["facts"]) or "—")}</td>'
                   f'<td class="small">{esc(_mean(p))}</td></tr>')
    table = ('<div class="scroll"><table class="mini"><thead><tr><th>面向</th><th>一個月方向</th><th>關鍵數字</th><th>對你的意思</th></tr></thead>'
             f'<tbody>{"".join(trs)}</tbody></table></div>')
    reg = (f'<p><b>現在的組合：{esc(m["regime"]["name"])}</b>。{esc(m["regime"]["why"])}</p>' if m.get("regime") else "")
    conf = ("<h3>互相打架的訊號</h3><ul>" + "".join(f"<li>{esc(c)}</li>" for c in m["conflicts"]) + "</ul>") if m.get("conflicts") else \
        '<p class="small muted">目前沒有明顯互相矛盾的面向。</p>'
    flips = m.get("flips")
    if flips:
        fl = "<h3>和上週比，翻轉的面向</h3><ul>" + "".join(
            f'<li>{esc(f["zh"])}：{LIGHT[f["from"]][1]} → {LIGHT[f["to"]][1]}</li>' for f in flips) + "</ul>"
    elif "prev_ts" in m:
        fl = '<p class="small muted">和上週比，所有面向的方向都沒有翻轉。</p>'
    else:
        fl = '<p class="small muted">本站從 2026-11-28 開始每天存一份，滿一週後會列出「和上週比翻轉的面向」。</p>'
    note = ("每個面向用網站已有的官方數據與行情，比較最近和一個月前（初領失業金用近 4 週對近 13 週、核心 CPI 用近 3 個月年化對近 12 個月），"
            "超過門檻算轉好或轉壞；方向一律寫「對經濟與市場」（例如利率上升、美元轉強算轉壞）。成長與通膨兩個面向組合成四種階段："
            "金髮女孩（成長好、通膨降）、過熱、停滯性通膨的壓力、降溫。這是同一套規則的描述，不是預測；AI 寫的看法在總經口播與一個月預判。"
            "資料來源：FRED（美國勞工部、聯準會、芝加哥聯準會）、美國財政部 TreasuryDirect（標售結果）、日本財務省（公債殖利率）、歐洲央行（CISS）、Yahoo 行情。")
    return card("總經全貌：各面向一起看", "Macro map: all pillars together",
                f'<p class="rimp big2"><b>{esc(lead(m))}</b></p>' + reg + table + conf + fl + f'<p class="note">{note}</p>', "wide")
