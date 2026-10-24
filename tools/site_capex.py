"""AI 視角看風險頁：AI 資本支出縮減時，誰的營收最受傷（SEC 季資料：雲端巨頭資本支出年增率 vs 供應鏈公司營收年增率）。"""
from __future__ import annotations

from tools.site_ai import _anchor
from tools.sitekit import T, card, esc, num

NOTE = ("怎麼算的：從 SEC 財報抓微軟、Alphabet、亞馬遜、Meta、甲骨文每一季的資本支出合計，以及每家供應鏈公司每一季的營收，都換成「近 12 個月合計的年增率」。"
        "用 2020 年以來各季做迴歸：斜率＝巨頭資本支出成長每多 1 個百分點，這家營收成長平均多幾個百分點；相關係數越接近 1，關係越明確。"
        "「如果資本支出不再成長」＝把巨頭資本支出年增率從現在的數字降到 0，用斜率推算營收年增率。"
        "限制：只有十幾到二十幾個季度、相關不等於因果；有些公司（例如輝達）訂單比巨頭的資本支出早出現，或客戶不只雲端巨頭，同一季比對會看不出關係，這種情況照實標示。不是投資建議。")


def _cl():
    try:
        from wsb.analytics import capex_link as CL
        return CL.build()
    except Exception:  # noqa: BLE001
        return None


def tier(r: dict) -> str:
    t = "明確依賴" if r["corr"] >= 0.5 else "部分依賴" if r["corr"] >= 0.3 else "數據看不出關係"
    return t + ("（樣本少）" if r["n"] < 12 and t != "數據看不出關係" else "")


def headline(b: dict) -> str:
    dep = [r for r in b["rows"] if r["corr"] >= 0.5 and r["n"] >= 12][:3]
    base = f"雲端巨頭近 12 個月資本支出合計 {b['capex_ttm'] / 1e8:,.0f} 億美元、年增 {b['capex_yoy']:.0f}%"
    if not dep:
        return base + "；目前看不出哪家供應商的營收明確跟著它走。"
    hurt = "、".join(f"{r['zh']}（營收成長 {r['rev_yoy']:+.0f}% → 約 {r['if_flat']:+.0f}%）" for r in dep)
    return base + f"。如果明年不再成長，最受傷的是：{hurt}。"


@_anchor("ai-capex")
def sec_ai_capex(eng) -> str:
    b = _cl()
    if not b:
        return ""
    rows = ""
    for r in b["rows"]:
        t = tier(r)
        show = not t.startswith("數據看不出關係")
        slope = f"{r['slope']:.2f}" if show else "—"
        flat = f"{r['if_flat']:+.0f}%" if show else "—"
        cls = "dn" if show and r["if_flat"] < 0 else ""
        rows += (f'<tr><td><b>{esc(r["zh"])}</b> <span class="small muted">{esc(r["sym"])}</span></td><td>{T(t, "")}</td>'
                 f'<td class="r">{r["corr"]:.2f}</td><td class="r">{slope}</td>'
                 f'<td class="r">{r["rev_yoy"]:+.0f}%</td><td class="r"><b class="{cls}">{flat}</b></td>'
                 f'<td class="r small muted">{r["n"]}</td></tr>')
    note = NOTE + f"（巨頭資本支出資料到 {b['capex_q']}）"
    body = (f'<p class="rimp big2"><b>{T(headline(b), "")}</b></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("公司", "Company")}</th><th>{T("依賴程度", "")}</th><th class="r">{T("相關係數", "")}</th>'
            f'<th class="r">{T("連動倍數", "")}</th><th class="r">{T("現在營收年增", "")}</th><th class="r">{T("若巨頭資本支出不再成長", "")}</th>'
            f'<th class="r">{T("季數", "")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<details class="sgx"><summary>{T("怎麼算的？", "How")}</summary><p class="note">{T(note, "")}</p></details>')
    return card("AI 資本支出縮減時，誰的營收最受傷", "If AI capex stops growing, whose revenue is hit", body, "wide")
