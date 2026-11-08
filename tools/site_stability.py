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

from tools.sitekit import T, card, esc, guard_safe, num, spark

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
    ("資產估值", "巴菲特指標、熱度計、投機股（高 Beta／ARKK）、EBP 信用定價、期限溢價、房價租金比", "valuation"),
    ("企業與家庭借貸", "高收益／BB／CCC／Baa 利差、企業危機雷達（Altman Z''、Merton）、破產模型、家庭償債比、逾期率、各類貸款新增嚴重逾期（紐約聯準會）、AI 資本支出", "industry"),
    ("金融機構槓桿", "放款標準 SLOOS、銀行存款、銀行證券帳面損失與未保險存款（FDIC）、避險基金槓桿（OFR）、私募信貸 BDC、融資餘額、美債基差交易（CFTC）", "risk"),
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
    ld = (_ldi(eng) or {}).get("rows") or []
    if ld:
        w = max(ld, key=lambda r: (r["p3"] or 0))
        lit = "🔴" if any(r["emoji"] == "🔴" for r in ld) else "🟡" if any(r["emoji"] == "🟡" for r in ld) else "🟢"
        tiles.append(("st-ldi", f"{lit} 退休金與長債", f"{w['c3']:+.0f}<small> bp</small>",
                      f"{w['zh']} {w['tenor']} 3 天變化・{len(ld)} 個市場" + ("都平穩" if lit == "🟢" else ""), ""))
    fw = _fsr(eng) or {}
    fl = [x for x in (fw.get(k) for k in ("house", "bank", "hedge", "rent")) if x]
    if fl:
        lit = sum(1 for x in fl if x["emoji"] == "🟡")
        au = next((r for r in (fw.get("house") or {}).get("rows") or [] if r["code"] == "AUTO"), None)
        tiles.append(("st-fsr", f"{'🟡' if lit else '🟢'} 官方點名的壓力點", f"{lit}<small> / {len(fl)} 黃燈</small>",
                      (f"車貸新增嚴重逾期 {au['flow']:.1f}%（10 年第 {au['p10']:.0f} 百分位）" if au and au.get("p10") is not None else "家庭貸款、銀行、避險基金、房價"), ""))
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
    four = (("標售規模", rf), ("短期資金", fu), ("基差交易", ba), ("AI 資本支出", ai))
    have = [z for z, x in four if x and x.get("emoji") != "⚪"]
    miss = [z for z, x in four if not x or x.get("emoji") == "⚪"]
    # "全部正常" only when all four were actually read; otherwise say how many and which are missing
    head = (f"金融穩定 {len(have)} 項：" if not miss else f"金融穩定 {len(have)}/4 項有資料：")         + ((f"{reds} 項紅燈、" if reds else "") + (f"{yel} 項黃燈" if yel else "")).rstrip("、")         + ("全部正常" if not reds and not yel and not miss else "其餘正常" if not reds and not yel and have else "")         + (f"（缺：{'、'.join(miss)}）" if miss else "")
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
               f'<div class="small muted">IORB {fu["iorb"]:.2f}%・近 20 天有 {fu["days_above"]} 天高於 IORB・{fu.get("since", "有資料")} 年以來第 {num(fu.get("spread_pct"), 0)} 百分位</div>'
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
            f'<p class="note">{T("怎麼看：避險基金常「買美債現貨、同時放空期貨」，賺兩者之間很小的價差，再用回購借錢放大好幾十倍，這就是基差交易。期貨淨空單愈大，代表這種交易愈多。它平常幫市場提供流動性；可是一旦回購借不到錢或保證金提高，就得同時拋售現貨，2020 年 3 月美債因此大跌、聯準會出手買了上兆美元。要和上一張的資金市場、MOVE 債市波動一起看。名目金額沒有依期限加權，30 年期的風險其實比 2 年期大很多。資料：CFTC 交易者持倉報告（TFF），每週五公布週二部位。", "")}</p>')
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


def _ldi(eng) -> Dict:
    c = getattr(eng, "_ldi_view", None)
    if c is None:
        try:
            from wsb.data import pension_ldi as PL
            c = PL.view(eng)
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._ldi_view = c
        except Exception:  # noqa: BLE001
            pass
    return c


def ldi_lead(rows: List[Dict]) -> str:
    hot = [r for r in rows if r["emoji"] != "🟢"]
    if not hot:
        return f"{len(rows)} 個市場的長天期公債最近 3 天都沒有急升，退休金被迫賣債的風險現在不高。"
    return "；".join(f"{r['zh']} {r['tenor']}公債 3 天 {r['c3']:+.0f}bp（{r['since']} 年以來第 {r['p3']:.0f} 百分位），{r['state']}" for r in hot) + \
        "。長債升得太快時，用槓桿避險的退休金要補保證金，可能被迫賣債。"


@_anchor("st-ldi")
def sec_st_ldi(eng) -> str:
    from wsb.data import pension_ldi as PL
    rows = (_ldi(eng) or {}).get("rows") or []
    if not rows:
        return ""
    by = {r["key"]: r for r in rows}
    tr = "".join(f'<tr{" class=hl" if r["emoji"] != "🟢" else ""}><td>{r["emoji"]} {esc(r["zh"])} {esc(r["tenor"])}</td><td class="r">{r["level"]:.2f}%</td>'
                 f'<td class="r"><b>{r["c3"]:+.0f}</b></td><td class="r">{num(r["p3"], 0)}</td><td class="r">{r["c20"]:+.0f}</td>'
                 f'<td class="r small muted">{r["max3"]:.0f}（{esc(r["max3_date"])}）</td><td class="small muted">{esc(r["date"])}</td></tr>' for r in rows)
    tbl = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("長天期公債", "Long bond")}</th><th class="r">{T("殖利率", "Yield")}</th>'
           f'<th class="r">{T("3 天變化（bp）", "3-day, bp")}</th><th class="r">{T("歷史百分位", "Pctile")}</th><th class="r">{T("20 天（bp）", "20-day, bp")}</th>'
           f'<th class="r">{T("歷史最大 3 天升幅", "Record 3-day rise")}</th><th>{T("資料日", "As of")}</th></tr></thead><tbody>{tr}</tbody></table></div>')
    uk, eu = by.get("uk"), by.get("eu")
    story = ""
    if uk:
        used = max(uk["c3"], 0) / PL.BUFFER_BP * 100
        story += (f'<p class="small"><b>2022 年發生什麼</b>：英國政府 9 月 23 日宣布大減稅又沒說錢從哪來，長債被拋售。英國 20 年公債在本站資料裡最大的 3 天升幅是 '
                  f'{uk["max3"]:.0f}bp（{esc(uk["max3_date"])}）。用槓桿做 LDI 的退休金被追繳保證金，只好賣更多長債，殖利率又再升，形成惡性循環；'
                  f'英國央行 9 月 28 日宣布緊急買債才止住。英鎊同時跌到接近 1 英鎊兌 1 美元。</p>'
                  f'<p class="small"><b>之後的規定</b>：英國金融政策委員會要求 LDI 基金至少撐得住約 {PL.BUFFER_BP}bp 的急升'
                  f'（<a href="{PL.BUFFER_URL}" target="_blank" rel="noopener">英國央行原文</a>）。最近 3 天英國 20 年公債 {uk["c3"]:+.0f}bp，'
                  + (f'約占這個緩衝的 {used:.0f}%。</p>' if uk["c3"] > 0 else '沒有上升。</p>'))
    if eu and eu.get("slope") is not None:
        story += (f'<p class="small"><b>荷蘭退休金改革（時程是官方的，對利率的影響是研究機構預估）</b>：荷蘭退休金約 1.5 兆歐元，正從「保證給多少」改成「看投資成果給」，'
                  f'各基金要在 2028 年 1 月前轉換，最大的 ABP 預定 2027 年 1 月 1 日轉換。轉換後不需要那麼多 30 年以上的避險，'
                  f'ING 等研究預期歐元 30 年利率相對 10 年會被推高（<a href="https://think.ing.com/articles/dutch-pension-reforms-are-bumping-up-rates-from-the-long-end" target="_blank" rel="noopener">ING</a>）。'
                  f'本站量到的歐元區 AAA 30 年減 10 年是 {eu["slope"]:+.0f}bp（{eu["since"]} 年以來第 {num(eu.get("slope_pct"), 0)} 百分位）'
                  + (f'，一年 {eu["slope_1y"]:+.0f}bp' if eu.get("slope_1y") is not None else "") + '。這個差距若在轉換日前後明顯拉大，代表預期正在發生。</p>')
    story += ('<p class="small"><b>連帶影響</b>：長債急升時，房貸利率、公用事業、不動產信託和還沒賺錢的成長股通常先受傷（它們的價值最看重遠期的錢）；'
              '保險公司和退休金帳上的債券跌價；如果拋售從英國或日本傳到美債，全球借錢成本一起上升。</p>'
              '<p class="small"><b>誰持有這些長債</b>：' + "；".join(f'{esc(r["zh"])}——{esc(r["who"])}' for r in rows) + "。</p>")
    sp = "".join(f'<div><div class="small muted">{esc(r["zh"])} {esc(r["tenor"])}（近 5 年）</div>{spark(_ser(r["hist"]), 160, 36)}</div>' for r in rows if r.get("hist"))
    body = (f'<p class="rimp big2"><b>{T("一句話看懂：" + ldi_lead(rows), "")}</b></p>'
            f'<p>{T("退休金答應幾十年後每個月付錢給退休的人，所以買很多 30 年左右的長債。殖利率慢慢升對它們是好事；幾天內急升，用借來的錢避險的基金就要補保證金，只好賣債，越賣越跌。", "")}</p>'
            + tbl
            + f'<details class="sgx"><summary>{T("看 2022 年英國退休金危機、荷蘭改革與連帶影響", "Details")}</summary>{story}'
            + (f'<div class="g3">{sp}</div>' if sp else "") + '</details>'
            + f'<p class="note">{T(f"燈號規則：3 個交易日升幅落在自己歷史最高 0.5%、或超過 {PL.RED_BP:.0f}bp → 🔴；最高 2.5%（或 20 天升幅最高 2.5%）→ 🟡；其餘 🟢。百分位只和同一條債自己的歷史比。資料：英國央行（20 年名目平價殖利率，2000 年起）、歐洲央行（歐元區 AAA 公債殖利率曲線，2004 年起）、FRED（美國 30 年）、日本財務省（日本 30 年）。描述現況，不是預測，也不是投資建議。", "")}</p>')
    return card("退休金與長天期公債：會不會再出一次 2022 年英國危機", "Pensions and long bonds: LDI stress", body, "wide")


def _fsr(eng) -> Dict:
    c = getattr(eng, "_fsr_view", None)
    if c is None:
        try:
            from wsb.data import fsr_watch as FW
            c = FW.view(eng, ((_v(eng) or {}).get("basis") or {}).get("pct"))
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._fsr_view = c
        except Exception:  # noqa: BLE001
            pass
    return c


def fsr_lead(v: Dict) -> str:
    from wsb.data import fsr_watch as FW
    lit = [(k, v[k]) for k in FW.NAMES if (v.get(k) or {}).get("emoji") == "🟡"]
    n = sum(1 for k in FW.NAMES if v.get(k))
    if not lit:
        return f"聯準會點名的 {n} 個壓力點，目前都沒有落在自己歷史最高的一成。"
    return f"{n} 個壓力點裡有 {len(lit)} 個亮黃燈：" + "；".join(f"{FW.NAMES[k]}（{x['state']}）" for k, x in lit) + "。"


@_anchor("st-fsr")
def sec_st_fsr(eng) -> str:
    from wsb.data import fsr_watch as FW
    v = _fsr(eng) or {}
    hf, hh, bk, rr = (v.get(k) for k in ("hedge", "house", "bank", "rent"))
    if not any((hf, hh, bk, rr)):
        return ""
    parts = []
    if hh:
        tr = "".join(f'<tr{" class=hl" if r["zh"] in hh["hot"] else ""}><td>{esc(r["zh"])}</td><td class="r"><b>{r["flow"]:.2f}%</b></td>'
                     f'<td class="r">{num(r["flow_1y"], 2)}%</td><td class="r">{num(r["p10"], 0)}</td><td class="r small muted">{r["max"]:.2f}%（{esc(r["max_date"])}）</td>'
                     f'<td class="r">{num(r["stock"], 2)}%</td></tr>' for r in hh["rows"])
        au = next((r for r in hh["rows"] if r["code"] == "AUTO"), None)
        parts.append(f'<h3>{hh["emoji"]} 家庭貸款：{esc(hh["state"])} <span class="muted small">資料季 {esc(hh["date"][:7])}</span></h3>'
                     + (f'<p>這一季大約每 100 元車貸，就有 {au["flow"]:.1f} 元新變成拖欠 90 天以上，一年前是 {num(au["flow_1y"], 1)} 元，'
                        f'在過去 10 年裡排第 {num(au["p10"], 0)} 百分位；最高是 {esc(au["max_date"][:4])} 年金融海嘯時的 {au["max"]:.1f} 元。'
                        '車是很多人上班的工具，車貸繳不出來，通常代表收入最緊的那群人先撐不住。</p>' if au else "")
                     + f'<div class="scroll"><table class="mini"><thead><tr><th>貸款</th><th class="r">新增嚴重逾期</th><th class="r">一年前</th>'
                       f'<th class="r">10 年百分位</th><th class="r">歷史最高</th><th class="r">累積逾期 90 天以上</th></tr></thead><tbody>{tr}</tbody></table></div>')
    if bk:
        parts.append(f'<h3>{bk["emoji"]} 銀行：{esc(bk["state"])} <span class="muted small">資料季 {esc(bk["date"][:7])}</span></h3>'
                     f'<p>銀行手上的債券如果現在賣掉，比當初的成本少大約 {abs(bk["unreal"]) * 10000:,.0f} 億美元，等於股東權益的 {abs(bk["ratio"]):.1f}%'
                     + (f'（一年前 {abs(bk["ratio_1y"]):.1f}%）' if bk.get("ratio_1y") is not None else "")
                     + f'；最糟是 {esc(bk["worst_date"][:7])} 的 {abs(bk["worst"]):.1f}%。另外 {bk["unins"]:.0f}% 的存款超過保險上限（{bk["since"]} 年以來第 {num(bk["unins_pct"], 0)} 百分位）。'
                     '平常不賣就不會認列損失；麻煩是存款人一起提款、銀行被迫賣債，損失就變成真的——2023 年矽谷銀行就是這樣倒的。</p>')
    if hf:
        parts.append(f'<h3>{hf["emoji"]} 避險基金：{esc(hf["state"])} <span class="muted small">資料季 {esc(hf["date"][:7])}</span></h3>'
                     f'<p>避險基金總共管理 {hf["gav"]:.1f} 兆美元的部位，其中自己的錢只有 {hf["nav"]:.1f} 兆，平均每 1 元本金撐 {hf["lev"]:.2f} 元'
                     f'（{hf["since"]} 年以來第 {num(hf["lev_pct"], 0)} 百分位，最高 {hf["lev_max"]:.2f} 倍在 {esc(hf["lev_max_date"][:7])}）。'
                     + (f'最大 10 家平均 {hf["top10"]:.1f} 倍，占全部資產 {num(hf.get("share"), 1)}%。' if hf.get("top10") is not None else "")
                     + (f'它們透過結算所借錢做美債基差交易的擔保回購約 {hf["repo"] / 1000:.2f} 兆美元，比一年前 {hf["repo_yoy"]:+.0f}%（{esc(hf["repo_date"])}）。'
                        if hf.get("repo_yoy") is not None else "")
                     + (f'CFTC 美債基差交易規模在自己歷史第 {hf["basis_pct"]:.0f} 百分位。' if hf.get("basis_pct") is not None else "")
                     + '槓桿高本身不是問題；問題是市場一急，大家同時被要求補錢、同時賣美債，2020 年 3 月就發生過。</p>')
    if rr:
        parts.append(f'<h3>{rr["emoji"]} 房價租金比：{esc(rr["state"])} <span class="muted small">資料月 {esc(rr["date"])}</span></h3>'
                     f'<p>把房價除以房租（{rr["since"]} 年＝100），現在是 {rr["idx"]:.0f}，在自己歷史第 {num(rr["pct"], 0)} 百分位'
                     + (f'；2006 年泡沫高點是 {rr["peak06"]:.0f}（{esc(rr["peak06_date"])}）' if rr.get("peak06") else "")
                     + (f'，歷史最高 {rr["max"]:.0f}（{esc(rr["max_date"])}）' if rr.get("max_date") and rr.get("max_date") != rr.get("peak06_date") else "")
                     + '。比值高代表「買房比租房貴很多」，年輕人更難買房；房價若要回到常態，不是房價跌，就是房租要漲很多年。</p>')
    spill = ('<p class="small"><b>連帶影響</b>：車貸逾期先打到次級車貸放款機構、二手車價和車廠的融資部門，再傳到買車貸證券的投資人；'
             '銀行帳面損失大，放款就保守，小企業和商用不動產最先借不到錢；避險基金一起去槓桿時，美債殖利率會在幾天內亂跳，'
             '房貸利率跟著動；房價相對房租偏高，房市交易就冷，建商、仲介和家具家電需求跟著慢。</p>')
    sp = []
    au = next((r for r in (hh or {}).get("rows") or [] if r["code"] == "AUTO"), None)
    for lab, rows in (("車貸新增嚴重逾期（%）", (au or {}).get("hist")), ("銀行債券帳面盈虧÷股東權益（%）", (bk or {}).get("hist")),
                      ("避險基金槓桿（倍）", (hf or {}).get("hist")), ("房價租金比", (rr or {}).get("hist"))):
        if rows and len(rows) > 5:
            sp.append(f'<div><div class="small muted">{lab}</div>{spark(_ser(rows), 160, 36)}</div>')
    body = (f'<p class="rimp big2"><b>{T("一句話看懂：" + fsr_lead(v), "")}</b></p>'
            f'<p>{T("聯準會每半年出一份《金融穩定報告》，點名哪裡可能出事。本站每月對照，發現這四項原本沒在看，現在補上：家庭繳不繳得出貸款、銀行債券跌價、避險基金借了多少錢、房子相對房租貴不貴。", "")}</p>'
            + (parts[0] if parts else "")
            + f'<details class="sgx"><summary>{T("看銀行、避險基金、房價租金比與連帶影響", "Details")}</summary>' + "".join(parts[1:]) + spill
            + (f'<div class="g3">{"".join(sp)}</div>' if sp else "") + '</details>'
            + f'<p class="note">{T("燈號：每項都和自己的歷史比。家庭——車貸或信用卡「這一季新增逾期 90 天以上」落在過去 10 年最高 10% → 🟡；銀行——證券帳面損失占股東權益落在 2010 年以來最大 10% → 🟡；避險基金——整體槓桿在 2013 年以來最高 10%、而且 CFTC 基差交易也在最高 10% → 🟡；房價租金比在 1987 年以來最高 10% → 🟡。", "")}'
              f'資料：<a href="{FW.NYF_PAGE}" target="_blank" rel="noopener">紐約聯準會家庭債務與信用報告</a>（季，2003 年起；沒有 FHA/VA 房貸分項）、'
              f'<a href="{FW.FDIC_PAGE}" target="_blank" rel="noopener">FDIC 全體銀行申報</a>（季）、<a href="{FW.OFR_PAGE}" target="_blank" rel="noopener">OFR 避險基金監測</a>（Form PF 季資料、結算所擔保回購）、'
              'FRED（Case-Shiller 房價、CPI 房租）。季資料大約落後 2～5 個月。描述現況，不是預測，也不是投資建議。</p>')
    return card("官方點名的四個壓力點：家庭貸款、銀行、避險基金、房價", "Fed FSR pressure points", body, "wide")


@_anchor("st-cover")
def sec_st_coverage(eng) -> str:
    cv = coverage()
    rows = "".join(f'<tr><td><b>{T(a, a)}</b></td><td class="small">{T(b, b)}</td><td><a href="#{t}">{T("前往", "Open")}</a></td></tr>' for a, b, t in MAP)
    gaps = cv.get("gaps") or []
    gl = "".join(f'<li><b>{esc(guard_safe(g.get("risk", "")))}</b>（{esc(g.get("source", ""))}'
                 + (f'，<a href="{esc(g["url"])}" target="_blank" rel="noopener">原文</a>' if str(g.get("url", "")).startswith("https://") else "")
                 + f'）：{esc(guard_safe(g.get("suggest", "")))}' + (f'<span class="muted">・免費資料：{esc(guard_safe(g["data"]))}</span>' if g.get("data") else "") + "</li>" for g in gaps)
    src = "、".join(esc(s) for s in cv.get("sources") or [])
    body = (f'<p>{T("本站把監測的數據，對照聯準會《金融穩定報告》的 4 大類脆弱度，再加上排定的大事件：", "")}</p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("類別", "Category")}</th><th>{T("本站在看的數據", "What the site watches")}</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>'
            + (f'<p><b>{T("最新一次盤點", "Latest audit")}</b>（{esc(cv.get("updated") or "—")}，對照：{src or "—"}）：'
               + (f'發現 {len(gaps)} 個本站還沒有對應數據的風險點</p><ul class="small">{gl}</ul>' if gaps else "官方報告點名的風險都已有對應數據。</p>")
               if cv else f'<p class="muted">{T("每月自動盤點尚未執行第一次。", "")}</p>')
            + f'<p class="note">{T("每月初，雲端排程會讀最新的聯準會《金融穩定報告》、IMF《全球金融穩定報告》、OFR 金融穩定監測與紐約聯準會的研究，逐條比對上表；官方點名、本站卻沒有數據的風險，會列在這裡並通知 Discord，之後補上。這樣不用等自媒體提醒。", "")}</p>')
    return card("監測覆蓋盤點：還有哪些風險沒在看", "Coverage audit: risks the site does not watch yet", body, "wide")


CSS = "[id^=st-]{scroll-margin-top:72px}"
