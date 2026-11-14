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


# ------------------------------------------------------------------ 各國危機雷達（新興市場會不會點火）
CR_NOTE = ("燈號是數「踩線的項目」：貨幣一年貶超過 15%、貨幣在 5 年最弱附近（2% 以內）、外匯存底一年少超過 10%、存底不夠付 3 個月進口、"
           "一年內到期的外債比存底多、經常帳逆差超過 GDP 的 4%、股市（美元計價的國家 ETF）離一年高點超過 30%。踩 2～3 項黃燈，4 項以上紅燈。"
           "這些是文獻和實務常用的警戒線，不是預測模型，本站沒有對它做回測；踩線的國家不一定出事，沒踩線也不保證平安。"
           "「有沒有擴散」看三件事：紅燈達 3 國、一個月內貶值超過 3% 的貨幣達 5 國、或新興市場美元債三個月比美國公債多跌 3 個百分點以上。"
           "新興市場匯率常在幾天內來回跳 3% 以上，所以變化用幾天的中位數算，表上「1 美元換多少」是最新一筆收盤。"
           "資料：Yahoo Finance（匯率、在美國掛牌的單一國家 ETF）、國際貨幣基金（外匯存底經 FRED，月資料；經常帳、政府債、GDP 為當年估計值）、"
           "世界銀行（存底可付幾個月進口、短期外債對存底，年資料，會慢一年）。不是投資建議。")
CR_WHY = ("新興市場出事會傳到美股和台股，主要走三條路：外國銀行借給它們的錢收不回來；新興市場基金被贖回時，會把手上的台股、韓股一起賣掉；"
          "以及這些國家被迫升息、砍進口，全球需求變少。只有一國出事、其他國家的債沒有跟著跌，通常就停在那一國。")
LIGHT = ("🟢", "🟡", "🔴")


def _cr(eng) -> dict:
    c = getattr(eng, "_country_risk", None)
    if c is None:
        try:
            from wsb.data import country_risk as CR
            c = CR.view(eng)
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._country_risk = c
        except Exception:  # noqa: BLE001
            pass
    return c


def _p(v, d: int = 1, suf: str = "%") -> str:
    return "—" if v is None else f"{v:+.{d}f}{suf}"


def cr_headline(v: dict) -> str:
    rows, sp = v.get("rows") or [], v.get("spread") or {}
    red = [r["zh"] for r in rows if r["light"] == 2]
    yel = [r["zh"] for r in rows if r["light"] == 1]
    bonds = (f"新興市場美元債三個月 {sp['emb3']:+.1f}%、美國公債 {sp['ief3']:+.1f}%" if sp.get("emb3") is not None and sp.get("ief3") is not None else "")
    weak = sp.get("weak") or []
    wline = f"過去一個月貨幣貶超過 3% 的有 {len(weak)} 國" + (f"（{'、'.join(weak)}）" if weak else "")
    if sp.get("state") == "spread":
        return (f"一句話看懂：新興市場的壓力正在擴散：{len(red)} 國紅燈" + (f"（{'、'.join(red)}）" if red else "") + f"，{wline}" + (f"，{bonds}" if bonds else "") + "。")
    if not red and not yel:
        return f"一句話看懂：{len(rows)} 個新興市場裡，沒有國家踩到兩項以上的警戒線；{wline}。"
    who = ("、".join(red) + "紅燈" if red else "") + ("；" if red and yel else "") + ("、".join(yel) + "黃燈" if yel else "")
    return (f"一句話看懂：{len(rows)} 個新興市場裡，{who}，但還看不到擴散：{wline}" + (f"，{bonds}，沒有明顯落後" if bonds else "") + "。")


def sec_country(eng) -> str:
    v = _cr(eng)
    rows = (v or {}).get("rows")
    if not rows:
        return ""
    main = "".join(f'<tr><td>{LIGHT[r["light"]]} {T(r["zh"], "")}</td><td class="r"><b class="{"dn" if (r.get("fx_y1") or 0) <= -15 else ""}">{_p(r.get("fx_y1"))}</b></td>'
                   f'<td class="r"><b class="{"dn" if (r.get("off") or 0) <= -30 else ""}">{_p(r.get("off"), 0)}</b></td>'
                   f'<td class="small">{T("、".join(r["flags"]) or "沒有踩線", "")}</td></tr>' for r in rows)
    full = "".join(f'<tr><td>{T(r["zh"], "")}</td><td class="r nw">{r["rate"]:,.2f} {r["cur"]}</td><td class="r">{_p(r.get("fx_w2"))}</td><td class="r">{_p(r.get("fx_m1"))}</td>'
                   f'<td class="r">{_p(r.get("weak"))}</td><td class="r">{_p(r.get("res_y1"))}</td><td class="r">{_p(r.get("mo"), 1, "").lstrip("+")}</td>'
                   f'<td class="r">{_p(r.get("st"), 0).lstrip("+")}</td><td class="r">{_p(r.get("ca"))}</td><td class="r">{_p(r.get("debt"), 0).lstrip("+")}</td>'
                   f'<td class="r">{_p(r.get("share"), 2).lstrip("+")}</td></tr>' for r in rows)
    past = v.get("past") or []
    idn = next((r for r in rows if r["iso3"] == "IDN"), None)
    size = ""
    if past:
        size = ("當年出事的國家佔全球 GDP：" + "、".join(f'{p["year"]} 年{p["zh"]} {p["share"]:.2f}%' for p in past) + "。"
                + (f'現在印尼佔 {idn["share"]:.2f}%。' if idn and idn.get("share") else "") + "規模不大的國家也能引發連鎖反應，關鍵在有沒有擴散。")
    miss = v.get("missing") or []
    res_m = max((r.get("res_month") or "" for r in rows), default="")
    body = (f'<p class="rimp big2"><b>{T(cr_headline(v), "")}</b></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("國家", "")}</th><th class="r">{T("貨幣一年", "")}</th><th class="r">{T("股市離高點", "")}</th>'
            f'<th>{T("踩線的項目", "")}</th></tr></thead><tbody>{main}</tbody></table></div>'
            f'<p class="small">{T("貨幣一年＝這個貨幣對美元一年的變化，負數是貶值；股市＝在美國掛牌、用美元計價的單一國家 ETF，等於外國投資人實際的感受。資料到 " + str(v.get("asof") or "") + "。", "")}</p>'
            f'<details class="sgx"><summary>{T("每一國的完整數字", "All numbers")}</summary><div class="scroll"><table class="mini"><thead><tr>'
            + "".join(f'<th class="r">{T(h, "")}</th>' if i else f'<th>{T(h, "")}</th>' for i, h in enumerate(
                ("國家", "1 美元換", "兩週", "一個月", "離 5 年最弱", "存底一年", "可付幾個月進口", "短期外債／存底", "經常帳占 GDP", "政府債占 GDP", "佔全球 GDP")))
            + f'</tr></thead><tbody>{full}</tbody></table></div>'
            f'<p class="small">{T("離 5 年最弱＝0% 代表現在就是 5 年來最弱；外匯存底資料到 " + (res_m or "（暫缺）") + "。" + ("這次沒抓到的欄位：" + "、".join(miss) + "，下次建置會再試。" if miss else ""), "")}</p></details>'
            + (f'<details class="sgx"><summary>{T("規模夠不夠大到引發海嘯？", "Is it big enough")}</summary><p class="note">{T(size + CR_WHY, "")}</p></details>' if size else "")
            + f'<details class="sgx"><summary>{T("燈號怎麼算、資料哪裡來", "How the lights work")}</summary><p class="note">{T(CR_NOTE, "")}</p></details>')
    return card("各國危機雷達：新興市場會不會點火", "Country crisis radar", body, "wide", sub="14 個新興市場的市場壓力與國家帳本，以及有沒有擴散")
