"""中國經濟卡（全球行情分頁，2026-11-16 使用者選的第 7 項）。資料在 wsb/data/china_watch.py。"""
from __future__ import annotations

from datetime import date
from typing import Optional

from tools.sitekit import T, card, esc


def _pc(x: Optional[float], d: int = 1) -> str:
    return "—" if x is None else f"{x * 100:+.{d}f}%"


def _lv(x: float) -> str:
    return f"{x:,.0f}" if abs(x) >= 1000 else f"{x:,.4g}"


def _ym(iso: str) -> str:
    return f"{int(iso[:4])} 年 {int(iso[5:7])} 月"


def sec_china(eng) -> str:
    try:
        from wsb.data import china_watch as CW
        v = CW.view()
    except Exception:  # noqa: BLE001
        return ""
    ex, im, imf, mk = v.get("exp"), v.get("imp"), v.get("imf") or {}, v.get("mkt") or {}
    if not ex and not mk:
        return ""
    y = str(date.today().year)
    y1 = str(date.today().year + 1)
    parts = []
    if ex and ex.get("yoy") is not None:
        parts.append(f"中國 {_ym(ex['date'])}出口比去年同期 <b>{_pc(ex['yoy'])}</b>"
                     + (f"（近三個月 {_pc(ex.get('yoy3'))}）" if ex.get("yoy3") is not None else "")
                     + (f"、進口 {_pc(im.get('yoy'))}" if im and im.get("yoy") is not None else "") + "。")
    g, c = (imf.get("gdp") or {}), (imf.get("cpi") or {})
    if g.get(y) is not None:
        s = f"IMF 預估今年經濟成長 {g[y]:.1f}%" + (f"、明年 {g[y1]:.1f}%" if g.get(y1) is not None else "")
        if c.get(y) is not None:
            s += f"；物價今年 {c[y]:.1f}%" + ("，很低：東西不好賣、企業降價搶市場（通縮壓力）" if c[y] <= 1.0 else "")
        parts.append(s + "。")
    lead = "".join(parts[:2]) if parts else ""
    rows = ""
    for s, x in mk.items():
        if s == "gap":
            continue
        rows += (f'<tr><td>{esc(x["zh"])}<div class="small muted">{esc(s)}・{esc(x["asof"])}</div></td><td class="r">{_lv(x["last"])}</td>'
                 f'<td class="r">{_pc(x.get("m1"))}</td><td class="r">{_pc(x.get("y1"))}</td></tr>')
    fx = mk.get("CNY=X") or {}
    gap = mk.get("gap") or {}
    fx_txt = ""
    if fx:
        fx_txt = (f"人民幣現在 1 美元兌 {fx['last']:.4f} 元，一年來" + ("升值" if (fx.get("y1") or 0) < 0 else "貶值")
                  + f" {abs((fx.get('y1') or 0) * 100):.1f}%（數字變小＝人民幣變強）")
        if gap:
            g_ = gap["now"]
            fx_txt += (f"；離岸人民幣比在岸{'弱' if g_ > 0 else '強'} {abs(g_) * 100:.2f}%"
                       + ("，海外資金在押人民幣貶值" if g_ > 0.003 else "，海外沒有明顯押貶值" if g_ <= 0.001 else ""))
        fx_txt += "。"
    debt = (imf.get("debt") or {}).get(y)
    chain = ("<b>為什麼台灣要看</b>：中國和香港是台灣最大的出口市場之一（電子零組件、石化、機械）；中國工廠景氣好，台灣的零組件訂單跟著好。"
             "反過來，中國產能過剩時用低價大量出口（鋼鐵、石化、面板、電動車），會壓低台灣同業的價格。人民幣大貶時，亞洲貨幣常一起變弱、外資流出亞洲股市。"
             "銅價常被當成中國工廠與房市需求的即時溫度計。")
    note = ("中國國家統計局的資料庫不開放自動讀取，這裡不繞過；出口與進口用 FRED 上的 OECD 月資料（美元、季節調整，約晚 2～3 個月），"
            "成長、物價、政府負債是 IMF 世界經濟展望的年資料（今年、明年是預測），市場行情來自 Yahoo"
            + (f"。IMF 估中國政府負債今年約 GDP 的 {debt:.0f}%" if debt else "") + "。")
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{lead or fx_txt}</p>' + (f"<p>{fx_txt}</p>" if lead and fx_txt else "") + f"<p>{chain}</p>"
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("市場", "Market")}</th><th class="r">{T("現在", "Last")}</th>'
            f'<th class="r">{T("1 個月", "1m")}</th><th class="r">{T("1 年", "1y")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="note">{note}</p>')
    return card("中國經濟：工廠、物價、人民幣", "China: factories, prices, the yuan", body, "wide",
                sub="中國出口、IMF 預測、人民幣與股市；台灣最大的出口市場之一")
