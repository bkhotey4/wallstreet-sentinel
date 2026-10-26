"""全球行情頁：歐洲與亞洲會不會從美國以外點火。兩張卡都先一句白話，細節收進「點開看」。"""
from __future__ import annotations

import pandas as pd

from tools.sitekit import T, card, num, spark

EU_NOTE = ("CISS 是歐洲央行每天算的「歐元區系統性壓力指數」，把股市、債市、匯市、銀行的壓力合成一個 0～1 的數字；2008 年和 2011 年歐債危機時衝到 0.5 以上。"
           "公債利差＝這個國家 10 年期公債殖利率減德國：市場越擔心這國還不出錢，利差越大；2011 年義大利一度超過 5 個百分點。"
           "回測 1980 年起每天一筆：CISS 落在不同水準時，美股之後 3 個月跌 ≥10% 的頻率。資料：歐洲央行、FRED（月資料）。不是投資建議。")
AS_NOTE = ("亞洲是全球科技供應鏈的上游：韓國股市以三星、SK 海力士等記憶體股為主，台股以台積電為主，常比美股更早反映半導體景氣。"
           "人民幣 20 天急貶（例如 2015 年 8 月）曾引發全球股災；本站沒有對它做回測，所以只當背景，不計入判斷。"
           "資料：Yahoo Finance。不是投資建議。")


def _v(eng) -> dict:
    c = getattr(eng, "_euro_asia", None)
    if c is None:
        try:
            from wsb.data import euro_asia as EA
            c = EA.view(eng)
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._euro_asia = c
        except Exception:  # noqa: BLE001
            pass
    return c


def eu_headline(e: dict) -> str:
    ci, hot = e.get("ciss") or {}, e.get("hot") or []
    parts = []
    if ci:
        cur = next((r for r in ci.get("rows") or [] if r["now"]), None)
        parts.append(f"歐元區整體壓力{ci['band']}（CISS {ci['now']:.2f}）" + (f"，歷史上這種時候美股 3 個月內大跌機率 {cur['p']:.0f}%（平常 {ci['base']:.0f}%）" if cur and cur.get("p") is not None else ""))
    for x in hot:
        parts.append(f"但{x['zh']}公債比德國多付 {x['spread']:.2f} 個百分點，是 1999 年以來第 {x['pct']:.0f} 百分位（歐債危機時最高 {x['max']:.2f}），半年 {x['chg6']:+.2f}")
    return "一句話看懂：" + "；".join(parts) + "。" if parts else ""


def sec_europe(eng) -> str:
    e = (_v(eng) or {}).get("europe")
    if not e:
        return ""
    ci = e.get("ciss") or {}
    rows = "".join(f'<tr{" class=hl" if x["pct"] >= 90 else ""}><td>{T(x["zh"], "")}</td><td class="r">{x["yield"]:.2f}%</td><td class="r"><b>{x["spread"]:+.2f}</b></td>'
                   f'<td class="r">{num(x["chg6"], 2, sign=True)}</td><td class="r">{x["pct"]:.0f}</td><td class="r small muted">{x["max"]:.2f}（{x["max_m"]}）</td>'
                   f'<td class="r small muted">{x["month"]}</td></tr>' for x in e.get("spreads") or [])
    tbl = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("國家", "")}</th><th class="r">{T("10 年殖利率", "")}</th><th class="r">{T("比德國多（百分點）", "")}</th>'
           f'<th class="r">{T("半年變化", "")}</th><th class="r">{T("1999 年以來百分位", "")}</th><th class="r">{T("歷史最高", "")}</th><th class="r">{T("資料月", "")}</th></tr></thead>'
           f'<tbody>{rows}</tbody></table></div>') if rows else ""
    bt = "".join(f'<tr{" class=hl" if r["now"] else ""}><td>{T(r["band"], "")}（{r["lo"]}～{r["hi"] if r["hi"] < 9 else "∞"}）{" ◀ 現在" if r["now"] else ""}</td>'
                 f'<td class="r"><b>{num(r["p"], 0)}%</b></td><td class="r small muted">{r["n"]:,}</td></tr>' for r in ci.get("rows") or [])
    btt = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("CISS 落在", "")}</th><th class="r">{T("美股 3 個月內跌 ≥10%", "")}</th>'
           f'<th class="r">{T("天數", "")}</th></tr></thead><tbody>{bt}</tbody></table></div>') if bt else ""
    eq = [r for r in ((_v(eng) or {}).get("asia") or {}).get("rows") or [] if r["sym"] in EU_SYMS]
    eql = "；".join(f"{r['zh']}一個月 {r['m1']:+.1f}%、離一年高點 {r['off']:+.1f}%" for r in eq)
    body = (f'<p class="rimp big2"><b>{T(eu_headline(e), "")}</b></p>' + tbl + (f'<p class="small">{T(eql + "。", "")}</p>' if eql else "")
            + (spark(pd.Series([r[1] for r in ci["hist"]], index=pd.to_datetime([r[0] for r in ci["hist"]]))) if ci.get("hist") else "")
            + f'<details class="sgx"><summary>{T("看 CISS 回測與說明", "Backtest and notes")}</summary>{btt}<p class="note">{T(EU_NOTE, "")}</p></details>')
    return card("歐洲：歐債壓力會不會再來", "Europe: is sovereign stress back?", body, "wide")


EU_SYMS = ("EUFN", "^STOXX50E")


def as_headline(a: dict) -> str:
    rows = [r for r in a.get("rows") or [] if r["sym"] not in EU_SYMS]
    worst = sorted(rows, key=lambda r: r["m1"])[:2]
    if not worst:
        return ""
    w = "、".join(f"{r['zh']}一個月 {r['m1']:+.0f}%（離高點 {r['off']:+.0f}%）" for r in worst)
    kr = any(r["sym"] == "^KS11" for r in worst)
    return f"一句話看懂：亞洲跌得最兇的是 {w}" + ("；韓國以記憶體股為主，跟 AI 產業鏈的壓力是同一件事。" if kr else "。")


def sec_asia(eng) -> str:
    a = (_v(eng) or {}).get("asia")
    if not a or not a.get("rows"):
        return ""
    rows = "".join(f'<tr><td>{T(r["zh"], "")}</td><td class="r"><b class="{"dn" if r["m1"] < -5 else ""}">{r["m1"]:+.1f}%</b></td>'
                   f'<td class="r">{r["off"]:+.1f}%</td></tr>' for r in a["rows"] if r["sym"] not in EU_SYMS)
    cny = a.get("cny")
    cline = f"人民幣：美元兌人民幣 {cny['now']:.3f}，20 天 {cny['chg20']:+.2f}%（正數＝人民幣變弱）。" if cny else ""
    body = (f'<p class="rimp big2"><b>{T(as_headline(a), "")}</b></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("市場", "")}</th><th class="r">{T("一個月", "")}</th><th class="r">{T("離一年高點", "")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>' + (f'<p class="small">{T(cline, "")}</p>' if cline else "")
            + f'<details class="sgx"><summary>{T("為什麼要看亞洲？", "Why Asia")}</summary><p class="note">{T(AS_NOTE, "")}</p></details>')
    return card("亞洲：中國、香港、韓國、日本", "Asia: China, Hong Kong, Korea, Japan", body, "wide")
