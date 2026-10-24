"""金融穩定監測 page (市場風險 group): the four gaps found by checking the site against the Fed Financial Stability Report's
vulnerability categories — Treasury refunding, short-term funding, the Treasury basis trade, AI capex financed by debt —
plus the coverage map and the monthly gap audit (research_feed/coverage.json, written by a cloud routine).

Layout follows the AI view page: one summary card of blocks that jump to the detail cards, each detail card with a
back link.  Every reading is a fixed rule on official data (percentiles against its own history), never a headline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from tools.sitekit import T, card, esc, num, spark

COVERAGE = Path(__file__).resolve().parents[1] / "research_feed" / "coverage.json"   # public site repo root, never synced over
TAB = "stability"


def _v(eng) -> Dict:
    cache = getattr(eng, "_stability_view", None)
    if cache is None:
        from wsb.data import stability as ST
        cache = ST.view(eng)
        try:
            eng._stability_view = cache
        except Exception:  # noqa: BLE001
            pass
    return cache


def _anchor(k: str):
    def deco(f):
        def g(eng):
            h = f(eng)
            if not h:
                return h
            back = "" if k == "st-top" else f'<p class="aiback"><a href="#{TAB}" data-jump="st-top">{T("↑ 回到重點", "↑ Back to summary")}</a></p>'
            h = h.replace('<section class="card', f'<section id="{k}" class="card', 1)
            return h[:h.rindex("</section>")] + back + "</section>"
        g.__name__ = f.__name__
        return g
    return deco


def _ser(rows, i=1) -> pd.Series:
    return pd.Series([r[i] for r in rows], index=pd.to_datetime([r[0] if len(r[0]) > 7 else r[0] + "-01" for r in rows]))


def _bn(x: Optional[float]) -> str:
    return "—" if x is None else (f"{x / 1e8:,.0f} 億美元" if abs(x) < 1e12 else f"{x / 1e12:,.2f} 兆美元")


def _yoy(r: Dict) -> str:
    return f"（{(r['debt'] / r['debt_prev'] - 1) * 100:+.0f}%）" if r.get("debt") and r.get("debt_prev") else ""


def coverage() -> Dict:
    try:
        if COVERAGE.exists():
            return json.loads(COVERAGE.read_text(encoding="utf-8"))
        from wsb.data import stability as ST
        return ST.load().get("coverage") or {}
    except Exception:  # noqa: BLE001
        return {}


# What the site watches, filed under the Fed Financial Stability Report's four vulnerability categories (+ events).
MAP = [
    ("資產估值", "巴菲特指標、熱度計、投機股（高 Beta／ARKK）、EBP 信用定價、期限溢價", "valuation"),
    ("企業與家庭借貸", "高收益／BB／CCC／Baa 利差、企業危機雷達（Altman Z''、Merton）、破產模型、家庭償債比、逾期率、AI 資本支出", "industry"),
    ("金融機構槓桿", "放款標準 SLOOS、銀行存款、私募信貸 BDC、融資餘額、美債基差交易（CFTC）", "risk"),
    ("資金面（短期融資）", "SOFR−準備金利率、常設回購動用、逆回購、準備金、財政部 TGA、貼現窗口", "stability"),
    ("排定的大事件", "FOMC、財政部季度再融資（借款估算＋標售規模聲明）、美債標售、CPI／就業、財報季", "econ"),
]


@_anchor("st-top")
def sec_st_brief(eng) -> str:
    v = _v(eng)
    rf, fu, ba, ai = (v.get(k) or {} for k in ("refunding", "funding", "basis", "ai"))
    if not any((rf, fu, ba, ai)):
        return ""
    tiles = []
    if rf:
        sub = "未來幾季維持中長債標售規模" if rf["state"] == "維持" else rf["read"][:40]
        b = rf.get("bills") or {}
        tiles.append(("st-refund", f"{rf['emoji']} 財政部發債", rf["state"],
                      sub + (f"・短期國債占 {b['share']:.1f}%" if b else ""), ""))
    if fu:
        big = f"{fu['spread']:+.0f}<small> bp</small>" if fu.get("spread") is not None else f"{fu['sofr']:.2f}<small>%</small>"
        tiles.append(("st-funding", f"{fu['emoji']} 短期資金市場", fu["state"], f"SOFR 比準備金利率 {big}".replace("<small>", "").replace("</small>", ""), ""))
    if ba:
        tiles.append(("st-basis", f"{ba['emoji']} 美債基差交易", f"${ba['net']:,.0f}<small>B</small>",
                      f"{ba['state']}・{ba['since']} 年以來第 {ba['pct']:.0f} 百分位", ""))
    if ai:
        tiles.append(("st-ai", f"{ai['emoji']} AI 資本支出", f"{ai['ratio']:.2f}<small> 倍</small>",
                      f"資本支出÷營業現金流・{ai['state']}" + (f"（{'、'.join(ai['over1'])} > 1）" if ai["over1"] else ""), ""))
    cv = coverage()
    gaps = cv.get("gaps") or []
    try:
        from tools import site_transmission as STR
        tiles += STR.tiles(eng)
    except Exception:  # noqa: BLE001
        pass
    tiles.append(("st-cover", "🧭 監測覆蓋盤點", f"{len(gaps)}<small> 個缺口</small>" if cv else "待盤點",
                  f"每月對照聯準會／IMF／OFR 報告" + (f"・{cv.get('updated')}" if cv.get("updated") else ""), ""))
    reds = sum(1 for x in (rf, fu, ba, ai) if x and x.get("emoji") == "🔴")
    yel = sum(1 for x in (rf, fu, ba, ai) if x and x.get("emoji") == "🟡")
    head = ("金融穩定 4 項：" + (f"{reds} 項紅燈、" if reds else "") + (f"{yel} 項黃燈" if yel else "") + ("全部正常" if not reds and not yel else "")).rstrip("、")
    worst = [x["read"] for x in (rf, fu, ba, ai) if x and x.get("emoji") == "🔴"] or [x["read"] for x in (rf, fu, ba, ai) if x and x.get("emoji") == "🟡"]
    dates = rf.get("next") or []
    watch = []
    if len(dates) >= 2:
        watch.append(f"{dates[0]} 美東 15:00 財政部公布借款估算；{dates[1]} 美東 8:30 公布標售規模——看「維持標售規模」那句有沒有改口")
    if fu:
        watch.append("月底、季底和大額國債交割日的 SOFR 與常設回購用量（資金最緊的日子）")
    if ba:
        watch.append("基差交易規模和 SOFR、MOVE 債市波動是否同時變差（三者一起惡化才是平倉風險）")
    grid = "".join(f'<a class="aitile" href="#{TAB}" data-jump="{k}"><span class="tl">{T(lab, lab)}</span><span class="tv">{big}</span>'
                   f'<span class="tt">{T(txt, txt)}</span>{extra}<span class="go">{T("看細節 ›", "Details ›")}</span></a>'
                   for k, lab, big, txt, extra in tiles)
    w = "".join(f"<li>{T(x, x)}</li>" for x in watch)
    body = (f'<p class="rimp big2"><b>{T(head, head)}</b>' + (f'<br>{T(worst[0], worst[0])}' if worst else "") + "</p>"
            f'<div class="aigrid">{grid}</div>'
            + (f'<div class="aiwatch"><b>{T("接下來要盯的事", "What to watch")}</b><ol>{w}</ol></div>' if w else "")
            + f'<p class="note">{T("這一頁補的是聯準會《金融穩定報告》點名、但本站原本沒有的數據；全部來自官方免費資料（財政部、紐約聯準會、CFTC、SEC），用固定規則判讀，不看新聞標題。描述現況，不是預測，也不是投資建議。", "Official free data, fixed rules; not a forecast or advice.")}</p>')
    return card("金融穩定監測：財政部發債、資金市場、基差交易、AI 借錢", "Financial stability monitor", body, "wide")


@_anchor("st-refund")
def sec_st_refunding(eng) -> str:
    rf = _v(eng).get("refunding") or {}
    if not rf:
        return ""
    pol, est, b, dfc = rf.get("policy") or {}, rf.get("estimates") or {}, rf.get("bills") or {}, rf.get("deficit12") or {}
    qs = "".join(f'<li>{esc(q["quarter"])}：預計向市場淨借 <b>${q["bn"]:,.0f}B</b></li>' for q in est.get("quarters") or [])
    rev = est.get("revision")
    rev_t = f"（比 {rev['vs']} 的估算{'多' if rev['bn'] > 0 else '少'} ${abs(rev['bn']):,.0f}B）" if rev else ""
    hist = "".join(f'<tr><td>{esc(h.get("date") or h.get("seen") or "")}</td><td>{esc(h.get("label", ""))}</td>'
                   f'<td>{ {"keep": "維持", "increase": "加量", "decrease": "減量"}.get(h.get("status"), "改變")}{"（措辭改變）" if h.get("changed") else ""}</td></tr>'
                   for h in reversed(rf.get("history") or []))
    bh = b.get("hist") or []
    body = (f'<p class="rimp">{rf["emoji"]} <b>{T("標售規模：" + rf["state"], "")}</b>——{T(rf["read"], "")}</p>'
            f'<blockquote class="small">{esc(pol.get("guidance") or "—")}</blockquote>'
            f'<p class="small muted">{T("財政部原文", "Treasury wording")}：<a href="{esc(pol.get("url", ""))}" target="_blank" rel="noopener">{esc(pol.get("label", ""))}</a>'
            f'{"（" + esc(pol["date"]) + "）" if pol.get("date") else ""}' + (f'・本季發行 ${pol["offer_bn"]:,.0f}B，新籌現金約 ${pol["new_cash_bn"]:,.1f}B' if pol.get("offer_bn") else "") + "</p>"
            f'<div class="g3"><div><div class="small muted">{T("借款估算", "Borrowing estimates")}</div><ul class="small">{qs}</ul>'
            f'<div class="small muted">{T(rev_t, "")}</div></div>'
            + (f'<div><div class="small muted">{T("短期國債占可交易國債", "Bills share of marketable debt")}</div><div class="big">{b["share"]:.1f}%</div>'
               f'<div class="small muted">{b["month"]}・一年前 {num(b.get("yago"), 1)}%・{b["since"]} 年以來第 {num(b.get("pct"), 0)} 百分位</div>{spark(_ser(bh)) if len(bh) > 5 else ""}</div>' if b else "")
            + (f'<div><div class="small muted">{T("12 個月滾動赤字", "12-month deficit")}</div><div class="big">${-dfc["bn"]:,.0f}B</div>'
               f'<div class="small muted">至 {dfc["month"]}・一年前 ${-(dfc.get("yago") or 0):,.0f}B</div></div>' if dfc else "")
            + "</div>"
            + (f'<p class="small">{T("下次公布", "Next releases")}：{"、".join(esc(x) for x in rf["next"])}（第一天借款估算、第二天標售規模聲明）</p>' if rf.get("next") else "")
            + (f'<details class="sgx"><summary>{T("歷次聲明紀錄", "Statement history")}</summary><table class="mini"><tbody>{hist}</tbody></table></details>' if hist else "")
            + f'<p class="note">{T("怎麼看：財政部每季公布兩次文件。借款估算說要借多少，標售規模聲明說用什麼期限借。中長債（2–30 年）發得多，長天期殖利率通常要上升才有人接（2023 年 8 月加量後，10 年期 10 月衝破 5%）；短期國債占比高，代表財政部先用短債頂著，利率一變利息馬上跟著變。本站每次抓到新聲明，都和上一季逐字比對。資料：美國財政部、fiscaldata MSPD、FRED。", "")}</p>')
    return card("財政部發債：季度再融資與短期國債占比", "Treasury refunding and bill share", body, "wide")


@_anchor("st-funding")
def sec_st_funding(eng) -> str:
    fu = _v(eng).get("funding") or {}
    if not fu:
        return ""
    srf = fu.get("srf") or {}
    h = fu.get("hist") or []
    body = (f'<p class="rimp">{fu["emoji"]} <b>{T("短期資金：" + fu["state"], "")}</b>——{T(fu["read"], "")}</p>'
            f'<div class="g3"><div><div class="small muted">SOFR（{fu["date"]}）</div><div class="big">{fu["sofr"]:.2f}%</div>'
            f'<div class="small muted">{T("成交量", "Volume")} ${fu["vol"]:,.0f}B・{T("第 99 百分位成交", "99th pct trade")} {fu["p99"]:.2f}%</div></div>'
            + (f'<div><div class="small muted">{T("SOFR − 準備金利率 IORB", "SOFR minus IORB")}</div><div class="big">{fu["spread"]:+.0f} bp</div>'
               f'<div class="small muted">IORB {fu["iorb"]:.2f}%・近 20 天有 {fu["days_above"]} 天高於 IORB・2018 年以來第 {num(fu.get("spread_pct"), 0)} 百分位</div>'
               f'{spark(_ser(h)) if len(h) > 5 else ""}</div>' if fu.get("spread") is not None else "")
            + (f'<div><div class="small muted">{T("常設回購 SRF 動用", "Standing repo take-up")}</div><div class="big">${srf["last"][1]:,.1f}B</div>'
               f'<div class="small muted">{srf["last"][0]}・近 20 天最多 ${srf["max20"]:,.1f}B、有 {srf["days_used20"]} 天動用・紀錄 ${srf["max_all"]:,.1f}B（{srf["max_all_date"]}）</div></div>' if srf else "")
            + "</div>"
            f'<p class="note">{T("怎麼看：SOFR 是用美債抵押借一晚錢的利率。銀行把錢放在聯準會就能拿到準備金利率（IORB），所以 SOFR 平常會低於 IORB；如果 SOFR 跑到 IORB 之上、或銀行跑去常設回購跟聯準會借錢，代表市場上的現金不夠用。2019 年 9 月回購利率一天飆到 10%、聯準會被迫緊急注資，就是這個訊號先亮。月底和季底本來就比較緊，連續好幾天才算數。資料：紐約聯準會 Markets API、FRED。", "")}</p>')
    return card("短期資金市場：SOFR 與常設回購", "Funding markets: SOFR and the standing repo facility", body, "wide")


@_anchor("st-basis")
def sec_st_basis(eng) -> str:
    ba = _v(eng).get("basis") or {}
    if not ba:
        return ""
    h = ba.get("hist") or []
    by = "".join(f'<tr><td>{esc(k)}</td><td class="r">${v:,.0f}B</td></tr>' for k, v in sorted(ba["by"].items(), key=lambda x: -x[1]))
    body = (f'<p class="rimp">{ba["emoji"]} <b>{T("基差交易規模：" + ba["state"], "")}</b>——{T(ba["read"], "")}</p>'
            f'<div class="g3"><div><div class="small muted">{T("槓桿基金美債期貨淨空單（名目）", "Leveraged-fund net short, notional")}</div>'
            f'<div class="big">${ba["net"]:,.0f}B</div><div class="small muted">{ba["date"]}・一年前 ${ba["yago"]:,.0f}B・{ba["since"]} 年以來第 {ba["pct"]:.0f} 百分位'
            f'{"・歷史新高" if ba["record"] else ""}</div>{spark(_ser(h)) if len(h) > 5 else ""}</div>'
            f'<div><table class="mini"><thead><tr><th>{T("期貨", "Contract")}</th><th class="r">{T("淨空單", "Net short")}</th></tr></thead><tbody>{by}</tbody></table></div></div>'
            f'<p class="note">{T("怎麼看：避險基金常「買美債現貨、同時放空期貨」，賺兩者之間很小的價差，再用回購借錢放大好幾十倍，這就是基差交易。期貨淨空單愈大，代表這種交易愈多。它平常幫市場提供流動性；可是一旦回購借不到錢或保證金提高，就得同時賣出現貨，2020 年 3 月美債因此大跌、聯準會出手買了上兆美元。要和上一張的資金市場、MOVE 債市波動一起看。名目金額沒有依期限加權，30 年期的風險其實比 2 年期大很多。資料：CFTC 交易者持倉報告（TFF），每週五公布週二部位。", "")}</p>')
    return card("美債基差交易：避險基金槓桿", "Treasury basis trade: hedge-fund leverage", body, "wide")


@_anchor("st-ai")
def sec_st_ai(eng) -> str:
    ai = _v(eng).get("ai") or {}
    if not ai:
        return ""
    rows = "".join(f'<tr><td>{esc(r["name"])}</td><td class="r">{_bn(r["capex"])}</td><td class="r">{_bn(r["ocf"])}</td>'
                   f'<td class="r"><b class="{"dn" if (r["ratio"] or 0) > 1 else ""}">{num(r["ratio"], 2)}</b>（{num(r["ratio_prev"], 2)}）</td>'
                   f'<td class="r">{_bn(r["fcf"])}</td><td class="r">{_bn(r["debt"])}'
                   f'{_yoy(r)}</td><td>{esc(r["end"] or "")}</td></tr>'
                   for r in ai["rows"])
    body = (f'<p class="rimp">{ai["emoji"]} <b>{T("AI 巨頭合計：" + ai["state"], "")}</b>——{T(ai["read"], "")}</p>'
            f'<div class="g3"><div><div class="small muted">{T("合計資本支出（近 12 個月）", "Combined capex, TTM")}</div><div class="big">{_bn(ai["capex"])}</div>'
            f'<div class="small muted">年增 {num(ai["capex_growth"], 0)}%</div></div>'
            f'<div><div class="small muted">{T("資本支出 ÷ 營業現金流", "Capex / operating cash flow")}</div><div class="big">{ai["ratio"]:.2f} 倍</div>'
            f'<div class="small muted">超過 1 倍＝花得比賺得多</div></div>'
            f'<div><div class="small muted">{T("一年內新增負債", "Debt added in a year")}</div><div class="big">{_bn(ai["debt_add"])}</div>'
            f'<div class="small muted">總負債年增 {num(ai["debt_growth"], 0)}%（含融資租賃）</div></div></div>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("公司", "Company")}</th><th class="r">{T("資本支出", "Capex")}</th><th class="r">{T("營業現金流", "OCF")}</th>'
            f'<th class="r">{T("倍數（一年前）", "Ratio (1y ago)")}</th><th class="r">{T("自由現金流", "FCF")}</th><th class="r">{T("總負債（年增）", "Debt (YoY)")}</th><th>{T("資料至", "As of")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            f'<p class="note">{T("怎麼看：大公司用自己賺的錢蓋機房，利率高也撐得住；營業現金流不夠付資本支出的公司，要靠發債或借錢，利率一上升、再融資成本跟著跳，市場會先修理這種公司。這裡看的是「整體」，各家的利息負擔與債務成本請看「產業體檢」頁的 AI 帳本。全部來自 SEC 申報（XBRL），近 12 個月合計，和自己一年前比。", "")}</p>')
    return card("AI 資本支出：靠自己賺還是靠借錢", "AI capex: paid by cash flow or by debt", body, "wide")


@_anchor("st-cover")
def sec_st_coverage(eng) -> str:
    cv = coverage()
    rows = "".join(f'<tr><td><b>{T(a, a)}</b></td><td class="small">{T(b, b)}</td><td><a href="#{t}">{T("前往", "Open")}</a></td></tr>' for a, b, t in MAP)
    gaps = cv.get("gaps") or []
    gl = "".join(f'<li><b>{esc(g.get("risk", ""))}</b>（{esc(g.get("source", ""))}'
                 + (f'，<a href="{esc(g["url"])}" target="_blank" rel="noopener">原文</a>' if str(g.get("url", "")).startswith("https://") else "")
                 + f'）：{esc(g.get("suggest", ""))}' + (f'<span class="muted">・免費資料：{esc(g["data"])}</span>' if g.get("data") else "") + "</li>" for g in gaps)
    src = "、".join(esc(s) for s in cv.get("sources") or [])
    body = (f'<p>{T("本站把監測的數據，對照聯準會《金融穩定報告》的 4 大類脆弱度，再加上排定的大事件：", "")}</p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("類別", "Category")}</th><th>{T("本站在看的數據", "What the site watches")}</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>'
            + (f'<p><b>{T("最新一次盤點", "Latest audit")}</b>（{esc(cv.get("updated") or "—")}，對照：{src or "—"}）：'
               + (f'發現 {len(gaps)} 個本站還沒有對應數據的風險點</p><ul class="small">{gl}</ul>' if gaps else "官方報告點名的風險都已有對應數據。</p>")
               if cv else f'<p class="muted">{T("每月自動盤點尚未執行第一次。", "")}</p>')
            + f'<p class="note">{T("每月初，雲端排程會讀最新的聯準會《金融穩定報告》、IMF《全球金融穩定報告》、OFR 金融穩定監測與紐約聯準會的研究，逐條比對上表；官方點名、本站卻沒有數據的風險，會列在這裡並通知 Discord，之後補上。這樣不用等自媒體提醒。", "")}</p>')
    return card("監測覆蓋盤點：還有哪些風險沒在看", "Coverage audit: risks the site does not watch yet", body, "wide")


CSS = "[id^=st-]{scroll-margin-top:72px}"
