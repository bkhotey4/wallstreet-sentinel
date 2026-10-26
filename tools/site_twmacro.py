"""台灣 pages: AI 視角看台灣 (one-sentence read, the monthly analysis note, the data calendar), 台灣債市, 台灣公司債, 台灣經濟,
央行與資金, 壽險・房市・外資.  Data and rules only (wsb.analytics.twmacro); not a forecast or advice."""
from __future__ import annotations

import html
import json
from pathlib import Path

from tools.sitekit import T, card, cls, esc, num

NOTE = Path(__file__).resolve().parents[1] / "research_feed" / "tw_note.json"   # written monthly by a cloud routine (public repo only)
WD = "一二三四五六日"


def _r(eng):
    r = getattr(eng, "_twmacro", None)
    if r is None:
        from wsb.analytics import twmacro as TWM
        try:
            r = TWM.build(eng)
        except Exception:  # noqa: BLE001
            r = {"available": False}
        eng._twmacro = r
    return r


def _how(txt: str, label: str = "這張表怎麼看") -> str:
    return f'<details class="sgx"><summary>{T(label, "How to read")}</summary><p class="note">{T(txt, "")}</p></details>'


def _lead(txt: str) -> str:
    return f'<p class="rimp big2"><b>{T(txt, "")}</b></p>'


def _pctx(p, since) -> str:
    if p is None:
        return "—"
    s = f"第 {p:.0f}"
    return f'{T(s, "")}<div class="small muted">{esc(since or "")} {T("起", "")}</div>'


# ------------------------------------------------------------------ AI 視角看台灣
def sec_tw_brief(eng) -> str:
    r = _r(eng)
    if not r.get("available"):
        return ""
    rd = r["read"]
    lis = "".join(f"<li>{T(x, '')}</li>" for x in rd["imp"])
    links = " ".join(f'<a class="golink" href="#{k}" data-p="{k}">{T(z, "")} →</a>' for k, z in
                     (("tw_bonds", "台灣債市"), ("tw_credit", "台灣公司債"), ("tw_econ", "台灣經濟"), ("tw_money", "央行與資金"), ("tw_life", "壽險・房市・外資"), ("taiwan", "台股籌碼")))
    body = (_lead(rd["head"]) + f'<h3>{T("白話：這對我們代表什麼", "What it means")}</h3><ul>{lis}</ul><p class="small">{links}</p>'
            f'<p class="note">{T("每一句都依下面各頁的官方數據自動選出（央行、國發會、櫃買中心、臺北市政府），數字變了句子會跟著變。描述現況與歷史，不是預測，也不是投資建議。", "")}</p>')
    return card("台灣在說什麼：景氣、利率、資金一句話", "Taiwan at a glance", body, "wide")


def load_note(path: Path = None) -> list:
    try:
        d = json.loads((path or NOTE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = [n for n in (d.get("notes") if isinstance(d, dict) else None) or [] if isinstance(n, dict) and n.get("summary") and n.get("month")]
    out.sort(key=lambda n: str(n.get("date") or n.get("month")), reverse=True)
    return out


def _note_html(n: dict) -> str:
    e = lambda x: html.escape(str(x or ""))  # noqa: E731
    lis = "".join(f"<li>{e(x)}</li>" for x in (n.get("summary") or []) if x)
    watch = "".join(f"<li>{e(x)}</li>" for x in (n.get("watch") or []) if x)
    src = "、".join(f'<a href="{e(s.get("url"))}" target="_blank" rel="noopener">{e(s.get("name"))}</a>' for s in (n.get("sources") or [])
                   if isinstance(s, dict) and str(s.get("url") or "").startswith("https://"))
    return (f'<h3>{e(n.get("title") or n["month"] + " 台灣分析筆記")}</h3><p class="small muted">{e(n["month"])}・{e(n.get("date"))}</p><ul>{lis}</ul>'
            + (f'<p><b>接下來看什麼</b></p><ul>{watch}</ul>' if watch else "") + (f'<p class="small">資料來源：{src}</p>' if src else ""))


def sec_tw_note(eng) -> str:
    notes = load_note()
    if not notes:
        return ""
    old = "".join(f'<details class="sgx"><summary>{html.escape(str(n["month"]))}</summary>{_note_html(n)}</details>' for n in notes[1:6])
    note = ("每月國發會公布景氣燈號後（約 28 日），由 AI 分析任務讀取央行、國發會、財政部、櫃買中心的最新公開數據，整理成白話筆記。"
            "只寫數據與歷史比較，不寫預測與買賣建議；AI 整理可能有誤，請以原始資料為準。")
    return card("台灣每月分析筆記（AI 自動整理）", "Monthly Taiwan note", _note_html(notes[0]) + old + f'<p class="note">{note}</p>', "wide")


def sec_tw_calendar(eng) -> str:
    r = _r(eng)
    if not r.get("available") or not r.get("cal"):
        return ""
    rows = "".join(f'<tr><td class="nw"><b>{x["when"]:%m-%d}</b>（{WD[x["when"].weekday()]}）</td><td>{T(x["zh"], "")}</td>'
                   f'<td class="small muted">{esc(x["last"] or "—")}</td><td class="small">{T(x["why"], "")}</td></tr>' for x in r["cal"])
    first = r["cal"][0]
    lead = f"一句話看懂：下一個台灣重要數據是 {first['when']:%m-%d} 的{first['zh']}。"
    how = ("日期依各機關的慣例推算（例如國發會約每月 27 日、央行理監事會在 3／6／9／12 月），遇假日會前後移動，以官方公告為準。"
           "「本站最新資料」是目前抓到的最新月份，公布後下一次網站更新就會自動換成新數字。")
    body = (_lead(lead) + f'<div class="scroll"><table class="mini"><thead><tr><th>{T("約略日期", "Approx. date")}</th><th>{T("數據", "Release")}</th>'
            f'<th>{T("本站最新資料", "Latest here")}</th><th>{T("為什麼重要", "Why")}</th></tr></thead><tbody>{rows}</tbody></table></div>' + _how(how, "日期怎麼來"))
    return card("台灣數據日曆：接下來公布什麼", "Taiwan data calendar", body, "wide")


# ------------------------------------------------------------------ 台灣債市
def sec_tw_gov(eng) -> str:
    r = _r(eng)
    g = r.get("gov") if r.get("available") else None
    if not g:
        return ""
    cur = g["curve"]
    rows = "".join(f'<tr><td>{T(k + " 年", k + "Y")}</td><td class="r"><b>{cur[k]:.2f}%</b></td></tr>' for k in ("2", "5", "10", "20", "30") if k in cur)
    lvl = "在歷史低檔" if (g["pct10"] or 50) <= 20 else "在歷史高檔" if (g["pct10"] or 50) >= 80 else "在歷史中間位置"
    lead = (f"一句話看懂：台灣 10 年期公債利率 {g['now10']:.2f}%" + (f"，比一年前{'高' if g['chg1y'] >= 0 else '低'} {abs(g['chg1y']):.2f} 個百分點" if g.get("chg1y") is not None else "")
            + f"，{lvl}" + (f"（{g['since10']} 年以來第 {g['pct10']:.0f} 百分位）" if g.get("pct10") is not None else "")
            + (f"；仍比美國低 {g['gap_us']:.2f} 個百分點" if (g.get("gap_us") or 0) > 0 else "") + "。")
    facts = []
    if g.get("slope"):
        sl = g["slope"]
        facts.append(f"長短利差（10 年減 2 年）{sl['now']:+.0f} bp" + (f"，{sl['since']} 年以來第 {sl['pct']:.0f} 百分位" if sl.get("pct") is not None else "（歷史資料累積中）")
                     + ("：曲線正常向上，市場沒有在預期衰退。" if sl["now"] > 0 else "：曲線倒掛（短天期比長天期貴），歷史上常出現在景氣轉弱之前。"))
    if g.get("disc") is not None:
        mv = g.get("disc_move")
        facts.append(f"央行重貼現率 {g['disc']:.3f}%（{g['disc_asof']}）" + (f"，上次調整是 {mv['date']}（{'升' if mv['by'] > 0 else '降'} {abs(mv['by']):.1f} bp），之後已維持 {mv['months']} 個月" if mv else "") + "。")
    if g.get("call") is not None:
        facts.append(f"銀行間隔夜拆款利率 {g['call']:.3f}%：銀行彼此借錢的利率，反映市場資金鬆緊。")
    if g.get("gov_out") is not None:
        facts.append(f"政府公債餘額 {g['gov_out']:.2f} 兆元（{g['out_asof']}，年增 {num(g['gov_out_yoy'], 1)}%）。")
    fl = "".join(f"<li>{T(x, '')}</li>" for x in facts)
    how = ("殖利率曲線來自櫃買中心每日公布的指標公債成交殖利率（等殖成交系統成交量加權）；10 年期的長期歷史用央行月資料（次級市場利率，1994 年起）。"
           "台灣利率長期比美國低，壽險業與退休基金因此大量買美國債券賺利差；美台利差越大，往海外跑的資金越多，新台幣也越受美元影響。")
    body = (_lead(lead) + f'<div class="scroll"><table class="mini"><thead><tr><th>{T("期限", "Tenor")}</th><th class="r">{T("殖利率", "Yield")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p class="small muted">{T("資料日", "As of")} {esc(g["asof"])}</p><ul>{fl}</ul>'
            f'<p class="small"><a class="golink" href="#wbonds" data-p="wbonds">{T("和其他國家比較 →", "Other countries →")}</a></p>' + _how(how))
    return card("台灣公債：政府借錢的利率", "Taiwan government bonds", body, "wide")


# ------------------------------------------------------------------ 台灣公司債
def sec_tw_corp(eng) -> str:
    r = _r(eng)
    c = r.get("corp") if r.get("available") else None
    if not c:
        return ""
    col = {"急速擴大": "dn", "緊張": "dn", "很放心": "up", "正常": ""}
    rows = ""
    for x in c["rows"]:
        rows += (f'<tr><td class="nw">{T(x["zh"], x["k"])}</td><td class="r"><b>{x["y"]:.2f}%</b>'
                 + (f'<div class="small muted">{T("一年", "1y")} {x["y_1y"]:+.2f}</div>' if x.get("y_1y") is not None else "") + "</td>"
                 f'<td class="r">{x["spread"]:.0f} bp</td><td class="r {cls(-(x["chg3"] or 0))}">{num(x["chg3"], 0, sign=True)}{" bp" if x.get("chg3") is not None else ""}</td>'
                 f'<td class="r">{_pctx(x["pct"], x["since"])}</td><td><b class="{col[x["state"]]}">{T(x["state"], "")}</b></td></tr>')
    bbb = next((x for x in c["rows"] if x["k"] == "twBBB"), c["rows"][-1])
    word = {"急速擴大": "急速擴大，市場開始擔心較弱的企業", "緊張": "偏高，市場對較弱的企業有疑慮", "很放心": "在歷史低檔，借錢給企業的人很放心", "正常": "在正常範圍"}[bbb["state"]]
    lead = f"一句話看懂：台灣 BBB 級公司借 5 年要付 {bbb['y']:.2f}%，比政府多 {bbb['spread']:.0f} bp，利差{word}。"
    facts = []
    tr = c.get("tier")
    if tr:
        facts.append(f"BBB 和 AAA 的利率差 {tr['now']:.0f} bp" + (f"（第 {tr['pct']:.0f} 百分位）" if tr.get("pct") is not None else "")
                     + "：差距越大代表市場越會區分好壞公司。")
    if c.get("out") is not None:
        facts.append(f"國內公司債餘額 {c['out']:.2f} 兆元（{c['out_asof']}，年增 {num(c['out_yoy'], 1)}%）"
                     + (f"；近 12 個月發行 {c['iss12']:.2f} 兆元，比前一年{'多' if (c['iss12_chg'] or 0) >= 0 else '少'} {abs(c['iss12_chg']):.0f}%" if c.get("iss12_chg") is not None else "") + "。")
    if c.get("filling"):
        facts.append(f"歷史比較資料正在從 {c['since']} 起逐月補齊（目前 {c['months']} 個月），補滿 5 年後才顯示百分位與狀態判斷的完整版本。")
    fl = "".join(f"<li>{T(x, '')}</li>" for x in facts)
    how = ("台灣沒有像美國那樣的公開公司債指數，這裡用櫃買中心每天公布的「公司債參考利率」：17 家銀行、票券與證券商對各評等虛擬 5 年期債券的報價，"
           "去掉最高與最低後平均（是報價，不是成交價）。利差＝公司債利率減同年期公債。台灣公司債多由台積電、電力、電信等大型企業發行，"
           "多數由壽險與銀行持有到期，所以利差比美國平穩很多；違約率等資料沒有免費來源。狀態：3 個月的擴大幅度排在台灣自己歷史的前 10%、而且利差在中位數以上為「急速擴大」，利差第 80 百分位以上「緊張」，第 20 以下「很放心」。")
    body = (_lead(lead) + f'<div class="scroll"><table class="mini"><thead><tr><th>{T("評等", "Rating")}</th><th class="r">{T("5 年期利率", "5Y yield")}</th>'
            f'<th class="r">{T("比公債多（利差）", "Spread")}</th><th class="r">{T("3 個月變化", "3m chg")}</th><th class="r">{T("歷史百分位", "Pct")}</th><th>{T("狀態", "State")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p class="small muted">{T("資料日", "As of")} {esc(c["date"])}・{T("同年期公債", "5Y gov")} {c["g5"]:.2f}%</p><ul>{fl}</ul>'
            f'<p class="small"><a class="golink" href="#cbonds" data-p="cbonds">{T("和美國、歐洲、亞洲公司債比較 →", "Global corporate bonds →")}</a></p>' + _how(how))
    return card("台灣公司債：企業借錢的利率與利差", "Taiwan corporate bonds", body, "wide")


# ------------------------------------------------------------------ 台灣經濟
def sec_tw_econ(eng) -> str:
    r = _r(eng)
    e = r.get("econ") if r.get("available") else None
    if not e:
        return ""
    from wsb.analytics.twmacro import LIGHT
    strip = "".join(f'<span title="{esc(p)} {esc(v)}">{LIGHT.get(v, ("⚪",))[0]}</span>' for p, v in e["last12"])
    lead = (f"一句話看懂：{e['month']} 景氣燈號{e['ico']}{e['light']}燈（{e['score']:.0f} 分，{e['mood']}）"
            + (f"，已連續 {e['run']} 個月" if e["run"] >= 2 else "") + f"；分數在 {e['since']} 年以來第 {e['score_pct']:.0f} 百分位。" if e.get("score_pct") is not None else
            f"一句話看懂：{e['month']} 景氣燈號{e['ico']}{e['light']}燈（{e['score']:.0f} 分）。")
    items = [("出口（海關，年增）", e.get("exports_yoy"), "%", e.get("ex_m"), "台灣最大的經濟引擎"),
             ("工業生產（年增）", e.get("ip_yoy"), "%", e.get("ip_m"), "工廠實際生產多少"),
             ("半導體設備進口（3 個月，年增）", e.get("chip3"), "%", e.get("chip_m"), "晶片廠擴產的速度，領先產能"),
             ("領先指標（6 個月變化）", e.get("lead6"), "%", e.get("lead_m"), "預告未來半年景氣方向"),
             ("同時指標（6 個月變化）", e.get("coin6"), "%", e.get("lead_m"), "現在景氣的溫度"),
             ("外銷訂單動向指數", e.get("orders"), "", e.get("orders_m"), "高於 50＝接單增加的廠商較多"),
             ("失業率", e.get("unemp"), "%", e.get("lead_m"), "就業市場"),
             ("物價（CPI 年增）", e.get("cpi"), "%", e.get("cpi_m"), "央行通膨目標約 2%")]
    rows = "".join(f'<tr><td>{T(n, "")}</td><td class="r"><b>{num(v, 1, sign=(u == "%" and "年增" in n or "變化" in n))}{u if v is not None else ""}</b></td>'
                   f'<td class="small muted">{esc(m or "—")}</td><td class="small">{T(w, "")}</td></tr>' for n, v, u, m, w in items)
    how = ("國發會「景氣對策信號」用 9 項指標（貨幣、股價、生產、出口、進口、銷售、加班工時等）打分：45～38 紅燈（熱絡）、37～32 黃紅、31～23 綠燈（穩定）、22～17 黃藍、16～9 藍燈（低迷）。"
           "領先、同時指標用的是「不含趨勢」版本，數字高於 100 代表在長期趨勢之上。出口、生產、半導體設備進口來自國發會指標構成項目。")
    body = (_lead(lead) + f'<p>{T("最近 12 個月燈號", "Last 12 months")}：<span style="font-size:1.3em;letter-spacing:2px">{strip}</span></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("指標", "Indicator")}</th><th class="r">{T("數值", "Value")}</th><th>{T("資料月", "Month")}</th>'
            f'<th>{T("看什麼", "Why")}</th></tr></thead><tbody>{rows}</tbody></table></div>' + _how(how, "燈號怎麼算"))
    return card("台灣景氣：燈號、出口與生產", "Taiwan economy", body, "wide")


# ------------------------------------------------------------------ 央行與資金
def sec_tw_money(eng) -> str:
    r = _r(eng)
    m = r.get("money") if r.get("available") else None
    if not m:
        return ""
    g = r.get("gov") or {}
    lead = (f"一句話看懂：{m['month']} M1B 年增 {m['m1b']:.2f}%、M2 年增 {m['m2']:.2f}%，"
            + (f"M1B 比 M2 高（{m['cross'] or '已維持 ' + str(m['run']) + ' 個月'}）：活期資金充沛。" if m["gap"] > 0 else
               f"M1B 比 M2 低（{m['cross'] or '已維持 ' + str(m['run']) + ' 個月'}）：活期資金相對減少。"))
    facts = []
    t = m.get("test")
    if t:
        facts.append(f"歷史統計（{t['since']} 年起，每月）：M1B 高於 M2 的月份，之後 {t['h']} 個月加權指數中位數 {t['up_med']:+.1f}%、上漲比例 {t['up_pos']:.0f}%；"
                     f"低於 M2 的月份是 {t['dn_med']:+.1f}%、{t['dn_pos']:.0f}%（全部月份中位數 {t['all_med']:+.1f}%）。差距"
                     + ("不大，只能當背景。" if abs(t["up_med"] - t["dn_med"]) < 3 else "明顯，但期間重疊、樣本有限，仍只是背景參考。"))
    if g.get("disc") is not None:
        facts.append(f"政策利率（重貼現率）{g['disc']:.3f}%，隔夜拆款 {num(g.get('call'), 3)}%。")
    if m.get("fxres") is not None:
        facts.append(f"外匯存底 {m['fxres'] * 1000:,.0f} 億美元（{m['fx_m']}，年增 {num(m['fxres_yoy'], 1)}%）：央行手上的美元彈藥，也是調節新台幣的工具。")
    if m.get("twd") is not None:
        facts.append(f"美元兌新台幣 {m['twd']:.2f}" + (f"，3 個月新台幣{'升值' if m['twd3m'] < 0 else '貶值'} {abs(m['twd3m']):.1f}%" if m.get("twd3m") is not None else "") + "。")
    if m.get("npl") is not None:
        facts.append(f"本國銀行逾放比 {m['npl']:.2f}%（{m['npl_m']}）：銀行壞帳比例，越低越健康。")
    fl = "".join(f"<li>{T(x, '')}</li>" for x in facts)
    how = ("M1B＝通貨＋活期存款（隨時能用的錢），M2＝M1B＋定存、外幣存款等。M1B 年增率高於 M2（俗稱黃金交叉）代表錢從定存移到活存，"
           "常被解讀為資金準備進股市；跌破 M2 則相反。上面的歷史統計用央行的加權指數月資料檢驗這個說法，期間重疊、不是預測。資料：中央銀行統計資料庫。")
    body = _lead(lead) + f"<ul>{fl}</ul>" + _how(how, "M1B、M2 是什麼")
    return card("央行與資金：利率、M1B／M2、外匯存底", "Central bank & liquidity", body, "wide")


# ------------------------------------------------------------------ 壽險・房市・外資
def sec_tw_life(eng) -> str:
    r = _r(eng)
    ih = r.get("ih") if r.get("available") else None
    if not ih:
        return ""
    parts, heads = [], []
    lf = ih.get("life")
    if lf:
        heads.append(f"壽險業 {lf['share']:.0f}% 的資產在海外（{lf['foreign']:.1f} 兆元）")
        tx = (f"人壽保險業總資產 {lf['assets']:.1f} 兆元，其中國外資產 {lf['foreign']:.1f} 兆元（{lf['share']:.1f}%，{lf['month']}）"
              + (f"，比一年前{'增加' if lf['share_1y'] >= 0 else '減少'} {abs(lf['share_1y']):.1f} 個百分點" if lf.get("share_1y") is not None else "")
              + (f"；在 {lf['since']} 年以來第 {lf['share_pct']:.0f} 百分位" if lf.get("share_pct") is not None else "") + "。")
        if lf.get("eq") is not None:
            tx += f"權益（淨值）占資產 {lf['eq']:.1f}%" + ("（2026 年起改用新會計制度 IFRS 17，和去年不能直接比）" if lf.get("ifrs17") else
                                                   f"，一年{'增加' if (lf.get('eq_1y') or 0) >= 0 else '減少'} {abs(lf.get('eq_1y') or 0):.1f} 個百分點" if lf.get("eq_1y") is not None else "") + "。"
        if lf.get("twd3m") is not None and abs(lf["twd3m"]) >= 2:
            tx += (f"新台幣 3 個月{'升值' if lf['twd3m'] < 0 else '貶值'} {abs(lf['twd3m']):.1f}%："
                   + ("新台幣升值時，以美元計價的海外資產換回台幣變少，沒有避險的部分會出現匯損。" if lf["twd3m"] < 0 else "新台幣貶值對海外資產換算有利。"))
        parts.append(f'<h3>{T("🛡️ 壽險業：海外資產與匯率", "Life insurers")}</h3><p>{T(tx, "")}</p>')
    tp = ih.get("taipei")
    ln = ih.get("loans")
    if tp:
        heads.append(f"臺北市房價指數年{'增' if (tp['yoy'] or 0) >= 0 else '減'} {abs(tp['yoy'] or 0):.1f}%")
        tx = (f"臺北市住宅價格月指數 {tp['now']:.1f}（{tp['month']}），一年 {num(tp['yoy'], 1, sign=True)}%、三年 {num(tp['chg3y'], 1, sign=True)}%；"
              + ("目前就是 " + tp["since"] + " 以來的最高點。" if tp["off_peak"] >= -0.5 else f"比 {tp['since']} 以來的高點低 {abs(tp['off_peak']):.1f}%。"))
        if ln:
            tx += (f"全體金融機構購屋貸款年增 {ln['mortgage_yoy']:.1f}%" + (f"（一年前 {ln['mortgage_yoy_1y']:.1f}%）" if ln.get("mortgage_yoy_1y") is not None else "")
                   + (f"、建築貸款年增 {ln['construct_yoy']:.1f}%" if ln.get("construct_yoy") is not None else "") + f"（{ln['month']}）。")
        parts.append(f'<h3>{T("🏠 房市：價格與房貸", "Housing")}</h3><p>{T(tx, "")}</p>')
    if not parts:
        return ""
    parts.append(f'<h3>{T("🌏 外資", "Foreign investors")}</h3><p>{T("外資每天買賣台股、台指期未平倉與融資餘額在台股頁：", "")}'
                 f'<a class="golink" href="#taiwan" data-p="taiwan">{T("台股籌碼 →", "Taiwan flows →")}</a></p>')
    lead = "一句話看懂：" + "；".join(heads) + "。"
    how = ("壽險業資料來自央行「人壽保險公司資產負債統計」（月）。台灣壽險業是全球最大的海外債券買家之一，主要買美元債，部分有匯率避險、部分沒有，"
           "所以新台幣大幅升值、美國利率大幅上升都會傷到淨值，這是台灣金融體系最主要的跨境風險之一（各公司避險比率沒有免費的完整資料）。"
           "房價用臺北市政府地政局的住宅價格月指數（2012 年 8 月起）；全國房價指數只有季資料且無免費檔案可自動抓取。")
    body = _lead(lead) + "".join(parts) + _how(how, "資料怎麼來、為什麼重要")
    return card("壽險業、房市與外資", "Insurers, housing & foreign money", body, "wide")
