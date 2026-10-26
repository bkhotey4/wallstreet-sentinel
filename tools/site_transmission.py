"""金融穩定監測頁：第二意見與傳導管道——OFR 金融壓力指數（和本站 SSI 交叉驗證）、外國央行託管美債、日圓套利交易。
每張卡都寫清楚「它在量什麼」和「回測準不準」，回測沒有預測力的照實寫。"""
from __future__ import annotations

import pandas as pd

from tools.site_stability import _anchor
from tools.sitekit import T, card, num, spark

FSI_NOTE = ("什麼是 OFR 金融壓力指數：美國財政部金融研究辦公室每天用 33 個市場數據（信用利差、股市估值、公債與黃金等避險資產、資金市場、波動率）"
            "算的壓力指標，0 代表歷史平均。它和本站 SSI 是兩套不同人設計的方法，一致時比較可信，分歧時要看是哪裡不一樣。"
            "回測每天一筆，相鄰日子會重疊，不是獨立事件；描述現況，不是預測，也不是投資建議。")
CUSTODY_NOTE = ("什麼是託管美債：外國央行和國際機構把買的美國公債寄放在紐約聯準會，每週公布總額。減少代表外國官方在賣美債或移走——"
                "可能是為了撐自己的貨幣（例如日本干預日圓）、分散風險，或對美元的信任下降。這是「美元信任」最直接的數據，但它變化很慢，"
                "本站沒有發現它能預測股市漲跌，所以只描述趨勢。資料：FRED WMTSECL1（紐約聯準會 H.4.1）。不是投資建議。")
YEN_NOTE = ("什麼是日圓套利：借利息很低的日圓，換成美元去買利息較高的美債或美股。日圓突然變強時，借日圓的人要趕快買回日圓還錢，就得賣掉手上的資產——"
            "2024 年 8 月的全球閃崩就是這樣。但長期數據顯示，多數日圓急升並沒有帶來大跌；真正危險的是「投機客大量放空日圓」再遇上急升。"
            "資料：FRED DEXJPUS、CFTC 交易者持倉報告（日圓期貨）。不是投資建議。")


def _v(eng) -> dict:
    c = getattr(eng, "_transmission_view", None)
    if c is None:
        try:
            from wsb.data import transmission as TR
            c = TR.view(eng)
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._transmission_view = c
        except Exception:  # noqa: BLE001
            pass
    return c


def _ser(rows) -> pd.Series:
    return pd.Series([r[1] for r in rows], index=pd.to_datetime([r[0] for r in rows]))


def fsi_emoji(f: dict) -> str:
    return "🟢" if f["now"] <= 0 else "🟡" if f["now"] <= 2 else "🔴"


def yen_emoji(y: dict) -> str:
    return "🔴" if y["chg20"] <= -5 else "🟡" if y.get("carry_big") else "⚪"


def _cur_band(f: dict):
    return next((r for r in f.get("rows") or [] if r["now"]), None)


@_anchor("st-fsi")
def sec_tr_fsi(eng) -> str:
    f = _v(eng).get("fsi")
    if not f:
        return ""
    cur = _cur_band(f)
    head = f"{fsi_emoji(f)} OFR 金融壓力指數 {f['now']:+.2f}（{f['band']}）"
    if cur and cur.get("p") is not None:
        head += f"：歷史上這一檔之後 3 個月跌 ≥10% 的機率 {cur['p']:.0f}%，平常 {f['base']:.0f}%"
    vs, vs_txt = f.get("vs_ssi"), ""
    if vs and vs != "一致":
        rising = (f.get("chg21") or 0) > 0
        if f["ssi"] >= 55 and f["now"] <= 0:
            now_txt = ("現在是「短期變化在升溫、但水準仍低於長期平均」" + ("，OFR 這個月也在往上：壓力正從低處往上爬，還沒到危險區。" if rising else
                       "，而且 OFR 這個月沒有跟著上升：比較像短期驚嚇，還沒擴散成全面壓力。"))
        else:
            now_txt = ("現在是「水準偏高、但短期變化平靜」" + ("，而且 OFR 這個月還在上升：壓力在高處累積。" if rising else
                       "，OFR 這個月在回落：高壓正在慢慢消退。"))
        vs_txt = (f"和本站壓力指數 SSI（{f['ssi']:.0f}）{vs}。SSI 比較重視短期變化（例如利差一個月擴大多少、VIX 跳升），"
                  "OFR 看的是和長期平均比的水準；" + now_txt)
    parts = "、".join(f"{z} {v:+.2f}" for z, v in f["parts"])
    parts_txt = f"五個分項（越高越緊張）：{parts}；一個月變化 {f['chg21']:+.2f}。"
    rows = ""
    for r in f.get("rows") or []:
        lo = "−∞" if r["lo"] <= -99 else r["lo"]
        hi = "∞" if r["hi"] >= 99 else r["hi"]
        rows += (f'<tr{" class=hl" if r["now"] else ""}><td>{T(r["band"], "")}（{lo}～{hi}）{" ◀ 現在" if r["now"] else ""}</td>'
                 f'<td class="r"><b>{num(r["p"], 0)}%</b></td><td class="r small muted">{r["n"]:,}</td></tr>')
    note = T(FSI_NOTE + f"（資料 {f['since']} 年起）", "")
    body = (f'<p class="rimp big2"><b>{T(head, "")}</b></p>'
            + (f'<p>{T(vs_txt, "")}</p>' if vs_txt else "")
            + f'<p class="small">{T(parts_txt, "")}</p>{spark(_ser(f["hist"]))}'
            + f'<div class="scroll"><table class="mini"><thead><tr><th>{T("壓力指數落在", "")}</th><th class="r">{T("之後 3 個月跌 ≥10%", "")}</th>'
            + f'<th class="r">{T("天數", "")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            + f'<p class="note">{note}</p>')
    return card("第二意見：官方金融壓力指數（OFR）", "Second opinion: OFR Financial Stress Index", body, "wide")


@_anchor("st-custody")
def sec_tr_custody(eng) -> str:
    c = _v(eng).get("custody")
    if not c:
        return ""
    head = f"{c['emoji']} 外國央行託管的美債：{c['tn']:.2f} 兆美元，{c['state']}"
    trend = (f"13 週 {c['chg13']:+.1f}%（{c['since']} 年以來第 {c['pct13']:.0f} 百分位）、一年 {c['chg52']:+.1f}%；"
             f"最高是 {c['peak_d']} 的 {c['peak']:.2f} 兆美元。")
    body = (f'<p class="rimp big2"><b>{T(head, "")}</b></p><p>{T(trend, "")}</p>{spark(_ser(c["hist"]))}'
            f'<p class="note">{T(CUSTODY_NOTE, "")}</p>')
    return card("美元信任：外國央行在撤離美債嗎？", "Foreign official holdings of Treasuries", body, "wide")


@_anchor("st-yen")
def sec_tr_yen(eng) -> str:
    y = _v(eng).get("yen")
    if not y:
        return ""
    head = f"{yen_emoji(y)} 日圓套利交易：{y['state']}"
    lines = [f"美元兌日圓 {y['usdjpy']:.1f}（{y['date']}），近 10 年第 {y['pct10y']:.0f} 百分位；20 天變化 {y['chg20']:+.1f}%（負數＝日圓變強）。"]
    if y.get("spec") is not None:
        side = "做多" if y["spec"] > 0 else "放空"
        lines.append(f"CFTC 投機部位（槓桿基金＋資產管理機構）淨{side}日圓 {abs(y['spec']):.1f}%（占未平倉，{y['spec_date']}），歷史第 {y['spec_pct']:.0f} 百分位。")
    if y.get("bt_p") is not None:
        ratio = y["bt_p"] / y["bt_base"] if y.get("bt_base") else None
        verdict = ("明顯偏高：日圓急升之後美股比較容易跌，值得當成警訊" if ratio and ratio >= 1.5 else
                   "略高一些，但樣本少，只當參考" if ratio and ratio >= 1.15 else "差不多，所以本站不把日圓急升當成崩跌警報")
        lines.append(f"回測（{y['bt_since']} 年起）：日圓 20 天急升 ≥5% 的 {y['bt_n']} 天，之後一個月標普跌 ≥5% 的機率 {y['bt_p']:.0f}%，"
                     f"平常 {y['bt_base']:.0f}%——{verdict}。")
    body = (f'<p class="rimp big2"><b>{T(head, "")}</b></p>' + "".join(f'<p class="small">{T(x, "")}</p>' for x in lines)
            + f'<p class="note">{T(YEN_NOTE, "")}</p>')
    return card("日圓套利交易：2024 年 8 月閃崩的引信", "Yen carry trade", body, "wide")


DOLLAR_NOTE = ("換匯額度：外國央行缺美元時，可以拿自己的貨幣跟聯準會換美元。平常幾乎沒人用；用量衝到 100 億美元以上，代表全球在搶美元"
               "（2008 金融海嘯、2011 歐債危機、2020 疫情都是）。GDPNow：亞特蘭大聯準會用最新公布的經濟數據，即時估算這一季 GDP 年化成長率，"
               "比官方 GDP 早好幾週；它不是預測股市，負數才代表經濟可能在收縮。資料：FRED SWPT、GDPNOW。不是投資建議。")


@_anchor("st-dollar")
def sec_tr_dollar(eng) -> str:
    v = _v(eng).get("dollar")
    if not v:
        return ""
    sw, gn = v.get("swaps"), v.get("gdpnow")
    lines = []
    if sw:
        spells = "、".join(sw["spells"][-5:])
        lines.append(f"{sw['emoji']} 聯準會換匯額度：現在 {sw['bn'] * 10:,.1f} 億美元（{sw['date']}），{sw['state']}。"
                     f"歷史上超過 100 億美元的時期：{spells}；最高是 {sw['peak_d']} 的 {sw['peak'] * 10:,.0f} 億美元。")
    if gn:
        prev = f"（上一季 {gn['prev']:.1f}%）" if gn.get("prev") is not None else ""
        lines.append(f"{gn['emoji']} 亞特蘭大聯準會 GDPNow：{gn['quarter']} 經濟成長估計 {gn['pct']:+.1f}%（年化）{prev}。")
    if not sw or not gn:
        head = "一句話看懂：" + ("換匯額度" if not sw else "GDPNow") + "資料暫時取不到，只看得到另一項。"
    elif sw["emoji"] == "🟢" and gn["pct"] > 0:
        head = "一句話看懂：全球沒有在搶美元，經濟也還在成長。"
    else:
        head = "一句話看懂：" + ("全球在搶美元" if sw["emoji"] != "🟢" else "") + ("、" if sw["emoji"] != "🟢" and gn["pct"] <= 0 else "") \
            + ("經濟成長估計轉負" if gn["pct"] <= 0 else "") + "，看下面兩項。"
    body = (f'<p class="rimp big2"><b>{T(head, "")}</b></p>' + "".join(f'<p>{T(x, "")}</p>' for x in lines)
            + f'<details class="sgx"><summary>{T("這兩個是什麼？", "What are these?")}</summary><p class="note">{T(DOLLAR_NOTE, "")}</p></details>')
    return card("美元荒與即時景氣：換匯額度、GDPNow", "Dollar squeeze and GDPNow", body, "wide")


def tiles(eng) -> list:
    v = _v(eng)
    out = []
    f, c, y = v.get("fsi"), v.get("custody"), v.get("yen")
    if f:
        cur = _cur_band(f)
        sub = f["band"] + (f"・之後 3 個月大跌 {cur['p']:.0f}%（平常 {f['base']:.0f}%）" if cur and cur.get("p") is not None else "")
        out.append(("st-fsi", f"{fsi_emoji(f)} 官方壓力指數（OFR）", f"{f['now']:+.2f}", sub, ""))
    if c:
        out.append(("st-custody", f"{c['emoji']} 外國央行託管美債", f"{c['chg52']:+.1f}<small>% ／年</small>", f"{c['state']}・{c['tn']:.2f} 兆美元", ""))
    dv = v.get("dollar") or {}
    if dv.get("swaps"):
        sw = dv["swaps"]
        out.append(("st-dollar", f"{sw['emoji']} 美元荒（換匯額度）", sw["state"], f"{sw['bn'] * 10:,.1f} 億美元" + (f"・GDPNow {dv['gdpnow']['pct']:+.1f}%" if dv.get("gdpnow") else ""), ""))
    if y:
        out.append(("st-yen", f"{yen_emoji(y)} 日圓套利", f"{y['usdjpy']:.0f}", y["state"], ""))
    return out
