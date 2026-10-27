"""Cards built on the research review's top picks: 超額債券溢酬 EBP (美債 page), 選擇權隱含大跌機率 and 累積脆弱度
(全方位風險 page).  Data: Fed Board EBP CSV, Minneapolis Fed market-based probabilities, FRED — all free."""
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from tools.sitekit import T, card, esc, num, spark


def _fr():
    from wsb.data import fed_research as FR
    return FR.load()


def _pct(vals: List[float], v: float) -> Optional[float]:
    vals = [x for x in vals if x is not None]
    return float(sum(x < v for x in vals) / len(vals) * 100) if vals else None


def sec_ebp(eng) -> str:
    rows = _fr().get("ebp") or []
    if len(rows) < 24:
        return ""
    last, prev3 = rows[-1], rows[-4]
    ebp_all = [r[2] for r in rows]
    p = _pct(ebp_all[:-1], last[2])
    mood = ("風險胃納偏高：投資人要求的額外報酬低於平常，信用定價偏樂觀（研究顯示這種時候 1–2 年後經濟較易轉弱）" if last[2] < 0 and p is not None and p <= 25 else
            "風險胃納偏低：信用市場在要求額外補償，通常伴隨景氣轉弱" if last[2] > 0.5 else "在常態範圍")
    s = pd.Series([r[2] for r in rows[-120:]], index=pd.to_datetime([r[0] + "-01" for r in rows[-120:]]))
    pr = pd.Series([r[3] for r in rows[-120:]], index=s.index)
    body = (f'<div class="g3">'
            f'<div><div class="small muted">{T("超額債券溢酬 EBP", "Excess bond premium")}</div><div class="big">{last[2]:+.2f}</div>'
            f'<div class="small muted">{T("3 個月前", "3m ago")} {prev3[2]:+.2f}・{T("1973 年以來第", "pctile since 1973:")} {num(p, 0)} {T("百分位", "")}</div>{spark(s)}</div>'
            f'<div><div class="small muted">{T("GZ 公司債利差", "GZ credit spread")}</div><div class="big">{last[1]:.2f}%</div>'
            f'<div class="small muted">{T("3 個月前", "3m ago")} {prev3[1]:.2f}%</div></div>'
            f'<div><div class="small muted">{T("聯準會模型：12 個月內衰退機率", "Fed model: recession within 12 months")}</div><div class="big">{last[3]:.1f}%</div>'
            f'<div class="small muted">{T("3 個月前", "3m ago")} {prev3[3]:.1f}%</div>{spark(pr)}</div></div>'
            f'<p><b>{T(mood, mood)}</b></p>')
    note = T(f"資料：聯準會理事會 Gilchrist & Zakrajšek（2012）模型，月資料（{last[0]}），每月第 4 個營業日左右更新。"
             "GZ 利差是上千檔公司債利差的平均；EBP 是扣掉「預期違約」之後剩下的部分，代表市場的風險胃納，學術上對未來景氣的預測力優於一般利差。"
             "衰退機率預測的是經濟衰退，不是股市大跌。聯準會會回溯修正近幾個月的數字，本站每天另存當天看到的最新值。描述現況，不是預測。",
             "Fed Board GZ/EBP data. The recession probability is about recessions, not stock crashes. Revised; the site keeps vintages.")
    return card("超額債券溢酬（EBP）與聯準會衰退機率", "Excess bond premium and the Fed's recession probability", body + f'<p class="note">{note}</p>', "wide")


def sec_mpd(eng) -> str:
    mp = _fr().get("mpd") or {}
    s6, s12 = mp.get("sp6m") or [], mp.get("sp12m") or []
    if len(s6) < 20:
        return ""
    l6 = s6[-1]
    d6 = [r[1] for r in s6]
    p = _pct(d6[:-1], l6[1])
    rows = ""
    for lab, ser in (("6 個月內", s6), ("12 個月內", s12)):
        if not ser:
            continue
        r, ago = ser[-1], ser[-5] if len(ser) > 5 else ser[0]
        rows += (f'<tr><td>{T(lab, lab)}</td><td class="r"><b>{r[1]:.1f}%</b></td><td class="r">{ago[1]:.1f}%</td><td class="r">{r[2]:.1f}%</td>'
                 f'<td class="r">{r[3] * 100:+.0f}% ／ {r[4] * 100:+.0f}% ／ {r[5] * 100:+.0f}%</td><td class="r">{r[6]:.2f}</td></tr>')
    s = pd.Series(d6[-160:], index=pd.to_datetime([r[0] for r in s6[-160:]]))
    body = (f'<p>{T(f"選擇權市場目前定價：標普 500 在 6 個月內跌 20% 以上的機率 {l6[1]:.1f}%，在 {s6[0][0][:4]} 年以來的歷史第 {p:.0f} 百分位。", "")}</p>'
            f'{spark(s)}<div class="scroll"><table class="mini"><thead><tr><th>{T("期間", "Horizon")}</th><th class="r">{T("跌 ≥20% 機率", "P(fall ≥20%)")}</th>'
            f'<th class="r">{T("一個月前", "1m ago")}</th><th class="r">{T("漲 ≥20% 機率", "P(rise ≥20%)")}</th>'
            f'<th class="r">{T("10 ／ 50 ／ 90 百分位報酬", "10/50/90th pct")}</th><th class="r">{T("偏態", "Skew")}</th></tr></thead><tbody>{rows}</tbody></table></div>')
    note = T(f"資料：明尼亞波利斯聯準銀行 Market-Based Probabilities，用 S&P 500 選擇權價格推算出的報酬分布，每週更新（最新 {l6[0]}）。"
             "這是「風險中性」機率：投資人願意為崩盤保險多付錢，所以會高估真實的下跌機率；適合看變化與相對高低，不是真實發生率。"
             "偏態越負＝市場越擔心大跌勝過大漲。",
             "Minneapolis Fed option-implied probabilities (risk-neutral; overstates real-world odds).")
    return card("選擇權隱含的大跌機率（明尼亞波利斯聯準銀行）", "Option-implied odds of a 20% fall (Minneapolis Fed)", body + f'<p class="note">{note}</p>', "wide")


def sec_vulnerability(eng) -> str:
    from wsb.analytics import vulnerability as VU
    try:
        r = VU.build(eng, _fr().get("ebp"))
    except Exception:  # noqa: BLE001
        return ""
    if not r.get("available"):
        return ""
    rows = "".join(f'<tr><td>{T(x["zh"], x["zh"])}</td><td>{"<b class=dn>🔥 過熱</b>" if x["state"] == "hot" else "<span class=muted>正常</span>"}</td>'
                   f'<td class="small">{T(x["txt"], x["txt"])}</td><td class="small muted">{esc(x["date"] or "")}</td>'
                   f'<td class="small">{T(x["why"], x["why"])}</td></tr>' for x in r["lights"])
    lead = (f"累積脆弱度：{r['n']} 盞燈中 {r['n_hot']} 盞過熱。" +
            ("信用與資產同時過熱（R-zone）：研究上這是之後 1–3 年出事機率最高的組合，但抓不準時點。" if any(x["k"] == "rzone" and x["state"] == "hot" for x in r["lights"])
             else "沒有出現信用與資產同時過熱的 R-zone 組合。"))
    note = T("這一層和壓力指數 SSI 互補：SSI 是即時溫度計，量「現在有多緊」；這裡量「底下累積了多少燃料」，學術研究顯示它能領先 1–3 年，"
             "但最危險的時期 SSI 往往很平靜，而且很多次過熱之後並沒有出事、約三分之一的危機事前也沒有亮。"
             "每一盞燈都只和自己「到當時為止」的歷史比（擴張視窗），不用未來資料定門檻。季資料或月資料，公布有時間差（日期標在每列）。"
             "依據：Greenwood 等（2022）、Mian, Sufi & Verner（2017）、López-Salido, Stein & Zakrajšek（2017）、Gilchrist & Zakrajšek（2012），詳見「學術研究」頁。",
             "Slow fuel layer, not a timing tool. Expanding-window thresholds; quarterly data with lags.")
    body = (f'<p><b>{T(lead, lead)}</b></p><div class="scroll"><table class="mini"><thead><tr><th>{T("項目", "Item")}</th><th>{T("狀態", "State")}</th>'
            f'<th>{T("數字", "Reading")}</th><th>{T("資料期", "Data for")}</th><th>{T("為什麼重要", "Why")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="note">{note}</p>')
    return card("累積脆弱度：底下累積了多少燃料", "Built-up vulnerability: how much fuel is underneath", body, "wide")
