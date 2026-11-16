"""韓國出口快報卡（台灣經濟分頁，2026-11-16 使用者選的第 6 項）。資料在 wsb/data/korea_exports.py（韓國關稅廳官方報導資料）。"""
from __future__ import annotations

from datetime import date
from typing import Dict, Optional

from tools.sitekit import T, card, esc


def period_zh(k: str) -> str:
    y, m = int(k[:4]), int(k[5:7])
    return f"{y} 年 {m} 月全月" if k.endswith("-M") else f"{y} 年 {m}/1–{m}/{int(k[8:10])}"


def _pc(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:+.1f}%"


def _amt(x: Optional[float]) -> str:
    return "—" if not x else f"{x:,.0f}"


def lead_of(r: Dict) -> str:
    s = f"韓國 {period_zh(r['key'])} 出口 {r['exp']:,.0f} 億美元，比去年同期 <b>{_pc(r.get('yoy'))}</b>"
    if r.get("day_yoy") is not None:
        s += f"（扣掉工作天數差異後，每天平均 {_pc(r['day_yoy'])}）"
    if r.get("chip"):
        s += (f"；其中晶片 {r['chip']:,.0f} 億美元" + (f"（占 {r['chip_share']:.0f}%）" if r.get("chip_share") else "")
              + (f"，年增 <b>{_pc(r['chip_yoy'])}</b>" if r.get("chip_yoy") is not None else ""))
    tw = (r.get("ctry") or {}).get("台灣")
    if tw is not None:
        s += f"；出口到台灣 {_pc(tw)}"
    return s + "。"


def sec_korea_exports(eng) -> str:
    try:
        from wsb.data import korea_exports as KE
        v = KE.view()
    except Exception:  # noqa: BLE001
        return ""
    rows = v.get("rows") or []
    if not rows:
        return ""
    r0 = rows[0]
    parts = [r for r in rows if not r["key"].endswith("-M")]
    same = [r for r in parts if parts and r["key"][8:] == parts[0]["key"][8:] and r.get("day_yoy") is not None]
    trend = ""
    if len(same) >= 3:
        a, b = same[0]["day_yoy"], same[2]["day_yoy"]
        seg = f"1–{int(same[0]['key'][8:10])} 日"
        trend = (f"同一段（每月 {seg}）比，兩個月前的日均年增率 {_pc(b)}，現在 {_pc(a)}："
                 + ("成長還在加速。" if a > b + 5 else "已經轉為衰退。" if a < 0 else "成長在放慢，但仍是增加。" if a < b - 5 else "大致持平。"))
    trs = "".join(
        f'<tr><td class="nw">{esc(period_zh(r["key"]))}</td><td class="r">{r["exp"]:,.0f}</td><td class="r {"up" if (r.get("yoy") or 0) > 0 else "dn"}">{_pc(r.get("yoy"))}</td>'
        f'<td class="r">{_pc(r.get("day_yoy"))}</td><td class="r">{_amt(r.get("chip"))}</td>'
        f'<td class="r">{_pc(r.get("chip_yoy"))}{"*" if r.get("chip_yoy_calc") else ""}</td>'
        f'<td class="r">{_pc((r.get("ctry") or {}).get("台灣"))}</td><td class="r">{_pc((r.get("ctry") or {}).get("中國"))}</td>'
        f'<td class="r">{_pc((r.get("ctry") or {}).get("美國"))}</td></tr>' for r in rows[:12])
    head = (f'<tr><th>{T("期間", "Period")}</th><th class="r">{T("出口（億美元）", "Exports ($100m)")}</th><th class="r">{T("年增", "YoY")}</th>'
            f'<th class="r">{T("日均年增", "Per working day YoY")}</th><th class="r">{T("晶片（億美元）", "Chips ($100m)")}</th><th class="r">{T("晶片年增", "Chips YoY")}</th>'
            f'<th class="r">{T("到台灣", "To Taiwan")}</th><th class="r">{T("到中國", "To China")}</th><th class="r">{T("到美國", "To US")}</th></tr>')
    chain = ("<b>為什麼台灣要看</b>：韓國出口現在大約一半是晶片（多數是三星、SK 海力士的記憶體），每 10 天就公布一次，比台灣的出口和外銷訂單早兩到三週，"
             "是全世界最早的晶片需求數字之一。韓國晶片出口一轉弱，常是 AI 伺服器、記憶體庫存在變化的早期訊號，接著才反映到台積電、"
             "台灣伺服器供應鏈的營收。月初、月中的數字工作天數不同，看「日均年增」比較準。")
    note = ("資料：韓國關稅廳官方報導資料（每月 11 日公布 1～10 日、21 日公布 1～20 日、1 日公布上個月）。讀新聞稿內文；"
            "晶片年增率、晶片占出口比重、各國的出口年增率讀自新聞稿附件（HWPX 檔，只讀文字）；晶片金額＝出口 × 占比。"
            "全月的新聞稿沒有附件，所以那幾列沒有晶片數字；*＝和去年同期那篇比算出的年增率。「到台灣」大增常是晶片送到台灣封測、組裝伺服器。"
            f'<a href="{esc("https://www.customs.go.kr/kcs/na/ntt/selectNttList.do?mi=2891&bbsId=1362")}" target="_blank" rel="noopener">韓國關稅廳報導資料</a>。')
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{lead_of(r0)}</p>' + (f"<p>{trend}</p>" if trend else "") + f"<p>{chain}</p>"
            f'<div class="scroll"><table class="mini"><thead>{head}</thead><tbody>{trs}</tbody></table></div><p class="note">{note}</p>')
    return card("韓國出口快報：最早的晶片需求數字", "Korea's 10-day exports", body, "wide",
                sub="韓國每 10 天公布一次出口，比台灣早兩到三週")
