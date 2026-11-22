"""景氣溫度：PMI 與失業率（台灣經濟頁，2026-11-22 台股覆蓋清單補缺）。資料與來源見 wsb/data/tw_macro2.py。"""
from __future__ import annotations

from typing import Dict, List

from tools.sitekit import card, esc, fold_rows


def _pct_rank(xs: List[float], v: float) -> int:
    xs = [x for x in xs if x is not None]
    return round(sum(x <= v for x in xs) / len(xs) * 100) if xs else 0


def sec_tw_pulse(eng=None) -> str:
    from wsb.data import tw_macro2 as M
    try:
        d = M.refresh()
    except Exception:  # noqa: BLE001
        return ""
    pmi, un = d.get("pmi") or [], d.get("unemp") or []
    if not pmi and not un:
        return ""
    parts = []
    if pmi:
        last = pmi[-1]
        streak = 0
        for x in reversed(pmi):
            if x["pmi"] is not None and x["pmi"] >= 50:
                streak += 1
            else:
                break
        rk = _pct_rank([x["pmi"] for x in pmi], last["pmi"])
        parts.append(f'製造業採購經理人指數 {last["ym"][5:].lstrip("0")} 月 {last["pmi"]:.1f}（連續 {streak} 個月高於 50＝擴張；比 2012 年以來 {rk}% 的月份高）'
                     + (f'，非製造業 {last["nmi"]:.1f}' if last.get("nmi") is not None else ""))
    if un:
        u = un[-1]
        ly = next((x for x in un if x["ym"] == f'{int(u["ym"][:4]) - 1}{u["ym"][4:]}'), None)
        parts.append(f'失業率 {u["ym"][5:].lstrip("0")} 月 {u["total"]:.2f}%' + (f'（去年同月 {ly["total"]:.2f}%）' if ly else ""))
    th = '<tr><th>月份</th><th class="r">製造業 PMI</th><th class="r">非製造業 NMI</th><th class="r">失業率</th><th class="r">20–24 歲失業率</th></tr>'
    by = {x["ym"]: x for x in un}
    rows = []
    for x in reversed(pmi[-24:]):
        u = by.get(x["ym"]) or {}
        rows.append(f'<tr><td>{esc(x["ym"])}</td><td class="r"><b>{"—" if x["pmi"] is None else format(x["pmi"], ".1f")}</b></td>'
                    f'<td class="r">{"—" if x.get("nmi") is None else format(x["nmi"], ".1f")}</td>'
                    f'<td class="r">{"—" if u.get("total") is None else format(u["total"], ".2f") + "%"}</td>'
                    f'<td class="r">{"—" if u.get("y20_24") is None else format(u["y20_24"], ".2f") + "%"}</td></tr>')
    body = (f'<p class="rimp"><b>一句話看懂：{esc("；".join(parts))}。</b></p>'
            '<p class="small">採購經理人指數是問企業採購主管「這個月比上個月好還是壞」：50 以上代表多數說變好。它比 GDP、出口早公布，常是景氣轉彎的第一個訊號；'
            '失業率則是景氣傳到一般人的最後一站。兩個一起看：指數還在高檔、失業率沒有上升，代表這次股市下跌還沒有傳到實體經濟。</p>'
            + fold_rows(rows, 12, th, "個月")
            + f'<p class="note">PMI／NMI：國家發展委員會（中華經濟研究院編製），<a href="{M.SRC_PMI}" target="_blank" rel="noopener noreferrer">政府資料開放平臺 6100</a>；'
              f'失業率：主計總處人力資源調查，<a href="{M.SRC_UNEMP}" target="_blank" rel="noopener noreferrer">政府資料開放平臺 6637</a>。'
              f'抓取 {esc(d.get("fetched") or "—")}。描述資料，不是預測，也不是投資建議。</p>')
    return card("景氣溫度：採購經理人指數與失業率", "PMI and unemployment", body, "wide")
