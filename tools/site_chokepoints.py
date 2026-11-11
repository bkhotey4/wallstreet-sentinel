"""航道監測卡（能源通膨分頁）：IMF PortWatch 每日船隻通過數 → 先動的資產 → 傳到哪些產業。數字全部由 wsb.data.chokepoints 算出。"""
from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from tools.sitekit import T, card, cls, esc, line_chart, num

ICON = {"red": "🔴", "yellow": "🟡", "green": "🟢"}
WORD = {"red": "大幅減少", "yellow": "偏少", "green": "正常"}


def _px_since(eng, sym: str, day: Optional[str]) -> Optional[Dict]:
    """Price now and its % change since the trading day before `day` (None if the series does not reach back)."""
    try:
        s = eng.market.series(sym).dropna()
    except Exception:  # noqa: BLE001
        return None
    if not day or len(s) < 2:
        return None
    before = s[s.index < pd.Timestamp(day)]
    if not len(before) or (pd.Timestamp(day) - before.index[-1]).days > 10:
        return None
    return {"now": float(s.iloc[-1]), "then": float(before.iloc[-1]), "chg": (float(s.iloc[-1]) / float(before.iloc[-1]) - 1) * 100,
            "then_date": before.index[-1].strftime("%Y-%m-%d")}


def _pct_less(r: Dict) -> str:
    return f"少了 {(1 - r['ratio']) * 100:.0f}%" if r["ratio"] < 1 else f"多了 {(r['ratio'] - 1) * 100:.0f}%"


def sec_chokepoints(eng) -> str:
    try:
        from wsb.data import chokepoints as CP
        v = CP.view()
    except Exception:  # noqa: BLE001
        v = None
    if not v:
        return ""
    rows = v["rows"]
    bad = [r for r in rows if r["st"] != "green" and r["ratio"] is not None]
    worst = min(bad, key=lambda r: r["ratio"]) if bad else None
    if worst:
        lead = (f'{worst["zh"]}最近 7 天平均每天 {worst["cur"]:.0f} 艘船通過，平常約 {worst["base"]:.0f} 艘（{_pct_less(worst)}）'
                + (f'，從 {worst["since"]} 起一直偏低' if worst.get("since") else "") + "。"
                + ("".join(f'{r["zh"]}也{WORD[r["st"]]}（平常的 {r["ratio"] * 100:.0f}%' + (f'，{r["since"]} 起' if r.get("since") else "") + '）。'
                     for r in bad if r is not worst)))
    else:
        lead = f'{len(rows)} 條主要航道的船隻通過數都在平常範圍內。'
    dt = v.get("detour") or {}
    if dt.get("on"):
        lead += f'紅海的船改走非洲南端：好望角是平常的 {dt["cape"] * 100:.0f}%，航程多 1～2 週。'

    chain = []
    for r in sorted(bad, key=lambda r: r["ratio"]):
        line = f'<li><b>{esc(r["zh"])}</b>（{esc(r["what"])}）→ 先動的：{esc(r["first"])}。'
        if r["id"] in ("chokepoint6", "chokepoint5"):
            p = _px_since(eng, "BZ=F", r.get("since"))
            if p:
                line += (f'布蘭特原油在 {p["then_date"]} 是 {p["then"]:.1f} 美元，現在 {p["now"]:.1f} 美元'
                         f'（<span class="{cls(p["chg"])}">{p["chg"]:+.0f}%</span>）。')
            if r.get("tk") is not None and r.get("tk_base"):
                line += f'油輪每天 {r["tk"]:.1f} 艘，平常 {r["tk_base"]:.0f} 艘。'
        chain.append(line + "</li>")
    spill = ("<h3>接著會傳到哪裡</h3><ul class=\"small\">"
             "<li>油價：航空（燃油是最大成本之一）、塑化與化工原料、貨運卡車；台灣的中油牌價由平穩機制吸收一部分。</li>"
             "<li>運費與航程：歐洲零售與汽車業的進口零件晚到、庫存成本上升；貨櫃航運公司運價收入增加。</li>"
             "<li>通膨與利率：運輸成本最後反映到商品價格，央行降息的空間變小，這條線接到本頁的「能源傳導鏈」卡。</li></ul>") if bad else ""

    trs = "".join(
        f'<tr{" class=hl" if r["st"] != "green" else ""}><td>{ICON[r["st"]]} {T(r["zh"], r["en"])}</td>'
        f'<td class="r"><b>{r["cur"]:.0f}</b></td><td class="r">{num(r["base"], 0)}</td><td class="r">{num(r["yoy"], 0)}</td>'
        f'<td class="r {cls((r["ratio"] or 1) - 1)}">{num(r["ratio"] * 100 if r["ratio"] is not None else None, 0)}%</td>'
        f'<td class="r">{r["pct"]:.0f}</td><td class="r small">{num(r["tk"], 1)}／{num(r["tk_base"], 0)}</td>'
        f'<td class="small muted">{esc(r["since"] or "—")}</td></tr>' for r in rows)
    table = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("航道", "Chokepoint")}</th>'
             f'<th class="r">{T("最近 7 天／天", "7-day avg")}</th><th class="r">{T("平常", "Normal")}</th><th class="r">{T("去年同期", "Year ago")}</th>'
             f'<th class="r">{T("是平常的", "vs normal")}</th><th class="r">{T("2019 年來排名", "Pctile")}</th>'
             f'<th class="r">{T("油輪 現在／平常", "Tankers")}</th><th>{T("偏低起始日", "Low since")}</th></tr></thead><tbody>{trs}</tbody></table></div>')
    pick = worst or rows[0]
    chart = line_chart("cp_" + pick["id"], pick["weekly"], f'{pick["zh"]}：每天通過船數（7 天平均，每週一點）', 0,
                       fixed=(0.0, float(pick["weekly"].max()) * 1.1 or 1.0))     # ship counts start at zero
    what = "".join(f'<li><b>{esc(r["zh"])}</b>：{esc(r["what"])}。</li>' for r in rows)
    note = (f'資料：<a href="{CP.PAGE}" target="_blank" rel="noopener">IMF PortWatch</a>，用衛星收到的船舶 AIS 訊號計數，2019 年起每天一筆；'
            f'最新資料日 {esc(v["date"])}（PortWatch 約每週更新，通常落後 3～7 天）。「平常」是一年前以前所有 7 天平均的中位數。'
            '燈號是本站自訂：比平常少一半以上是 🔴，少 25% 以上或落在 2019 年以來最低 10% 是 🟡。'
            '限制：只數有開 AIS 的船，戰區船隻常關掉訊號，所以數字可能比實際少；船少不一定是封鎖，也可能是船公司自己避開。描述現況，不是預測。')
    g = v.get("gscpi")
    gline = ""
    if g:
        lvl = {"red": "很高，供應鏈明顯塞住", "yellow": "偏高，供應鏈有點塞", "green": "在正常範圍"}[g["st"]]
        trend = "" if g["chg3"] is None else (f'，3 個月前是 {g["v"] - g["chg3"]:+.2f}（' + ("變更塞" if g["chg3"] > 0.2 else "變順" if g["chg3"] < -0.2 else "差不多") + "）")
        gline = (f'<p>{ICON[g["st"]]} <b>整體供應鏈壓力</b>（紐約聯準會 GSCPI，{esc(g["month"])}）：{g["v"]:+.2f}，{lvl}{trend}。'
                 f'{g["start"]} 年以來排第 {g["pct"]:.0f} 百分位；最高是 {esc(g["peak_m"])} 疫情塞港時的 {g["peak"]:+.1f}。'
                 '<span class="small muted">（數字是「比長期平均高幾個標準差」，0 是平常；把運費、交貨時間、積壓訂單合起來算，'
                 f'<a href="{CP.GSCPI_PAGE}" target="_blank" rel="noopener">紐約聯準會</a>每月初更新。≥1 黃、≥2 紅是本站自訂。）</span></p>')
    body = (f'<p class="rimp big2"><b>{esc(lead)}</b></p>'
            + (f'<ul>{"".join(chain)}</ul>' if chain else "")
            + gline
            + chart
            + f'<details class="sgx"><summary>{T("看七條航道的數字、各走什麼貨、會傳到哪些產業", "Details")}</summary>'
            + table + spill + f'<h3>每條航道走的是什麼</h3><ul class="small">{what}</ul></details>'
            + f'<p class="note">{note}</p>')
    return card("航道監測：船還過得去嗎", "Shipping chokepoints: are ships getting through", body, "wide")
