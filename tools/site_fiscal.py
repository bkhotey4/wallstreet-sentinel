"""政府停擺與債務上限倒數卡（美債分頁，2026-11-15）。資料與規則在 wsb/data/us_fiscal.py：政府撥款到期日讀 GovInfo 的法律原文，
債務上限讀財政部每日報表；這裡只負責講成白話，並說明一旦卡關，錢會先從哪裡開始動。"""
from __future__ import annotations

from datetime import date
from typing import Dict

from tools.sitekit import card, esc


def _tn(m: float) -> str:
    """millions of dollars → 兆美元 / 億美元 in plain words."""
    return f"{m / 1e6:.2f} 兆美元" if abs(m) >= 1e6 else f"{m / 100:,.0f} 億美元"


def _mdy(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.year} 年 {d.month} 月 {d.day} 日"


def funding_lead(f: Dict) -> str:
    st = f.get("state")
    if st == "cr":
        n = f["days"]
        lamp = "🔴" if n <= 7 else "🟡" if n <= 30 else "🟢"
        return (f"{lamp} 美國政府現在靠「臨時撥款」運作，<b>{_mdy(f['end'])}到期，還有 {n} 天</b>。"
                + ("到期前國會要再通過新的撥款法律，否則沒有拿到全年預算的機關會停擺。" if n > 0 else "今天到期。"))
    if st == "lapsed":
        return (f"🔴 依法律原文，臨時撥款已在 {_mdy(f['end'])}到期，之後沒有查到新的撥款法律：<b>政府可能正在停擺</b>"
                "（法律剛通過到公布在官網之間會差幾天，請以新聞為準）。")
    if st == "funded":
        return f"🟢 這個會計年度的全年預算法律已經通過，大部分機關的錢可以用到 {_mdy(f['end'])}。"
    return "⚪ 這個會計年度還沒有查到撥款相關法律（資料來源可能延遲）。"


def debt_lead(dv: Dict) -> str:
    if not dv:
        return ""
    used = dv["used"] * 100
    s = (f"債務上限是 <b>{_tn(dv['limit'])}</b>，受上限約束的債務已經 {_tn(dv['subject'])}，用掉 {used:.1f}%，"
         f"<b>還剩約 {_tn(dv['room'])}</b>（{esc(dv['asof'])}）。")
    if dv.get("months") is not None:
        m = dv["months"]
        lamp = "🔴" if m <= 1 else "🟡" if m <= 6 else "🟢"
        s = (f"{lamp} " + s + f"照最近 {dv['span']} 天平均每天多借約 {_tn(dv['per_day'])}的速度，<b>大約 {m:.1f} 個月會用完</b>。"
             "用完之後財政部還能動用「非常措施」再撐一段時間，所以這不是違約日，而是國會要開始處理的時間點。")
    elif dv.get("per_day") is not None:
        s = "🟢 " + s + f"最近 {dv['span']} 天債務沒有增加（常見於報稅季），暫時算不出用完的時間。"
    return s


def sec_fiscal(eng) -> str:
    try:
        from wsb.data import us_fiscal as US
        v = US.view()
    except Exception:  # noqa: BLE001
        return ""
    f, dv = v.get("funding") or {}, v.get("debt") or {}
    if not f and not dv:
        return ""
    lead = funding_lead(f) if f else ""
    chain = ("<b>如果撥款到期還沒通過</b>：聯邦員工停薪或放假 → 勞工統計局等機關停止發布就業、物價數據 → 聯準會和市場少了最重要的數字，"
             "利率預期更容易亂跳 → 停越久，消費與經濟成長被拖得越多。過去停擺時股市通常反應不大，衝擊多半在數據空窗和經濟本身。")
    chain2 = ("<b>如果債務上限逼近</b>：財政部先花掉現金帳戶裡的錢、少發短期公債 → 快到期限時，"
              "在期限附近到期的短期公債殖利率會被拉高（市場擔心那幾天拿不回錢）→ 上限一調高，財政部會一口氣大量發債把現金補回來，"
              "把銀行體系的資金吸走，這段時間股市和高風險資產比較容易震盪。")
    tga = ""
    if dv.get("tga") is not None:
        tga = (f"財政部現金帳戶（一般帳戶）餘額約 {_tn(dv['tga'])}（{esc(dv['tga_asof'])}）"
               + (f"，四週前比 {'+' if dv.get('tga_chg', 0) >= 0 else '−'}{_tn(abs(dv['tga_chg']))}" if dv.get("tga_chg") is not None else "") + "。")
    laws = "".join(f'<li>{esc(x["date"])}・<a href="{esc(x.get("url", ""))}" target="_blank" rel="noopener">{esc(x["title"])}</a>'
                   + (f'（到期日 {esc(x["end"])}）' if x.get("end") else "") + "</li>" for x in (f.get("laws") or []))
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{lead}</p>'
            + (f"<p>{debt_lead(dv)}</p>" if dv else "")
            + f'<details><summary>卡關的話錢會怎麼動、資料怎麼來</summary><p class="small">{chain}</p><p class="small">{chain2}</p>'
            + (f'<p class="small">{tga}</p>' if tga else "")
            + (f'<p class="small">這個會計年度查到的撥款法律：</p><ul class="small">{laws}</ul>' if laws else "")
            + f'<p class="small muted">資料：<a href="https://www.govinfo.gov/app/collection/plaw" target="_blank" rel="noopener">GovInfo 公法原文</a>'
              f'（到期日直接讀法律條文）、<a href="{US.FD_PAGE}" target="_blank" rel="noopener">財政部每日報表：受上限約束的債務</a>。'
              "「幾個月用完」是照最近 90 天的速度推算，報稅季、大筆支出都會讓速度改變；這是倒數，不是預測。</p></details>")
    return card("政府停擺與債務上限倒數", "Shutdown & debt-limit countdown", body, "wide",
                sub="國會兩個最常卡關的期限：政府撥款到期、債務上限用完")
