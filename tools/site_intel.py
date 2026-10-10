"""Site sections from the 2026-10 Google_Financial feature port (eng.sx, built by wsb.analytics.siteextra):
個股情報 (analyst targets, dividends, SEC 8-K, earnings implied moves), 情緒與警報 (fear & greed, index expected moves,
alarm-rule backtest, geopolitical heat), US→TW linkage, overheating list, hard-tech explainers, AI bull/bear notes and
the brokerage-cost calculator.  Nothing here reads personal holdings."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

import pandas as pd

from tools.site_sections import _tabset, _theme_chip
from tools.sitekit import T, card, cls, esc, line_chart, num

MK = {"us": ("美股", "US"), "tw": ("台股", "Taiwan"), "hk": ("港股", "Hong Kong")}
WD = "一二三四五六日"


def _sx(eng) -> Dict:
    return getattr(eng, "sx", None) or {}


def _nm(r: Dict) -> str:
    return (f'<b>{T(r.get("name") or r.get("sym", ""), r.get("name_en") or r.get("name") or r.get("sym", ""))}</b>'
            f'<span class="tk">{esc(r.get("code") or r.get("sym", ""))}</span>')


def _td(v, txt: str, c: str = "r") -> str:
    dv = "" if v is None else f' data-v="{v:.6g}"' if isinstance(v, (int, float)) else f' data-v="{esc(str(v))}"'
    return f'<td class="{c}"{dv}>{txt}</td>'


def _th(zh: str, en: str, r: bool = True) -> str:
    return f'<th class="{"r " if r else ""}sk" title="點一下排序">{T(zh, en)}</th>'


def _wd(d: str) -> str:
    try:
        return "（" + WD[date.fromisoformat(d).weekday()] + "）"
    except Exception:  # noqa: BLE001
        return ""


# ================================================================== 個股情報
REC_T = [(1.5, "強力買進", "Strong buy"), (2.5, "買進", "Buy"), (3.5, "持有", "Hold"), (4.5, "表現落後", "Underperform"), (9, "賣出", "Sell")]


def _rec(rm: Optional[float]) -> str:
    if rm is None:
        return '<span class="muted">—</span>'
    for lim, zh, en in REC_T:
        if rm < lim:
            return f'{T(zh, en)} <span class="muted small">{rm:.1f}</span>'
    return "—"


def _analyst_table(rows: List[Dict], mk: str) -> str:
    if not rows:
        return f'<p class="muted">{T("這個市場還沒有分析師資料（每小時補抓一部分）。", "No analyst data for this market yet.")}</p>'
    tr = "".join(
        f'<tr data-q="{esc((r["name"] + " " + r["code"]).lower())}"><td class="nw">{_nm(r)}{_theme_chip(r["theme"])}</td>'
        + _td(r["px"], num(r["px"], 2)) + _td(r["tm"], num(r["tm"], 2))
        + _td(r["up"], f'<b class="{cls(r["up"])}">{num(r["up"], 0, sign=True, pct=True)}</b>')
        + _td(r.get("upl"), f'<span class="muted">{num(r.get("upl"), 0, sign=True, pct=True)} ~ {num(r.get("uph"), 0, sign=True, pct=True)}</span>')
        + _td(r.get("n"), num(r.get("n"), 0)) + _td(r.get("rm"), _rec(r.get("rm")), "") + "</tr>" for r in rows)
    return (f'<div class="scroll"><table class="mini srt"><thead><tr>{_th("個股", "Stock", False)}{_th("現價", "Price")}{_th("平均目標價", "Mean target")}'
            f'{_th("距平均目標", "To mean")}{_th("最低～最高目標", "Low ~ high")}{_th("分析師數", "Analysts")}{_th("共識評級", "Consensus", False)}'
            f'</tr></thead><tbody>{tr}</tbody></table></div>')


def sec_analyst(eng) -> str:
    st = (_sx(eng).get("stocks") or {}).get("analyst") or {}
    if not any(st.values()):
        return ""
    items = [(MK[mk][0] + f" {len(st.get(mk) or [])}", MK[mk][1], _analyst_table(st.get(mk) or [], mk)) for mk in ("us", "tw", "hk")]
    note = T("目標價與評級來自 Yahoo Finance 彙整的券商預估，通常落後股價、偏樂觀；分析師少於 3 位的樣本代表性低。"
             "評級分數 1＝強力買進、3＝持有、5＝賣出。這是市場共識的整理，不是本站的看法或建議。點欄位標題可排序。",
             "Consensus targets / ratings compiled by Yahoo Finance. They lag the price and lean optimistic. Not our view or advice.")
    return card("分析師共識與目標價", "Analyst consensus & targets", f'<p class="small muted">{note}</p>' + _tabset("an", items), "wide")


def _div_table(rows: List[Dict], mk: str) -> str:
    if not rows:
        return f'<p class="muted">{T("這個市場還沒有配息資料。", "No dividend data yet.")}</p>'
    net_h = T("扣 30% 預扣稅後", "After 30% US tax") if mk == "us" else T("實拿（不含所得稅）", "Gross")
    tr = "".join(
        f'<tr><td class="nw">{_nm(r)}{_theme_chip(r["theme"])}</td>' + _td(r["yld"], f'<b>{num(r["yld"], 2, pct=True)}</b>')
        + _td(r["net"], num(r["net"], 2, pct=True)) + _td(r["rate"], num(r["rate"], 2))
        + _td(r.get("ex") or "", (f'<b class="up">{esc(r["ex"])}</b>' if r.get("ex_soon") else esc(r.get("ex") or "—")), "nw")
        + _td(r.get("paid"), num(r.get("paid"), 0)) + _td(r.get("grow"), num(r.get("grow"), 0))
        + _td(r.get("payout"), num(r.get("payout"), 0, pct=True)) + "</tr>" for r in rows)
    return (f'<div class="scroll"><table class="mini srt"><thead><tr>{_th("個股", "Stock", False)}{_th("殖利率", "Yield")}<th class="r sk">{net_h}</th>'
            f'{_th("年配息", "Annual div.")}{_th("除息日", "Ex-date")}{_th("連續配息年數", "Years paid")}{_th("連續增配年數", "Years raised")}'
            f'{_th("配息率", "Payout")}</tr></thead><tbody>{tr}</tbody></table></div>')


def sec_dividends(eng) -> str:
    dv = (_sx(eng).get("stocks") or {}).get("div") or {}
    if not any(dv.values()):
        return ""
    items = [(MK[mk][0] + f" {len(dv.get(mk) or [])}", MK[mk][1], _div_table(dv.get(mk) or [], mk)) for mk in ("us", "tw", "hk")]
    note = T("殖利率＝年配息 ÷ 現價（自行計算）。美股股息對台灣投資人預扣 30%（台積電 ADR 等外國公司依其母國稅制，可能不同）；"
             "台股股息併入綜所稅、單筆 ≥ 2 萬元另扣 2.11% 二代健保補充保費，表上未扣。綠色除息日＝30 天內。"
             "連續年數只看最近幾年的完整年度資料；高殖利率有時是股價大跌造成，請一併看配息率是否過高。",
             "Yield = annual dividend ÷ price. US dividends carry 30% withholding for Taiwan residents. Green ex-date = within 30 days.")
    return card("股息雷達", "Dividend radar", f'<p class="small muted">{note}</p>' + _tabset("dv", items), "wide")


SEV_T = {3: ("重大", "High", "dn"), 2: ("留意", "Medium", "warn"), 1: ("一般", "Low", "muted")}


def sec_filings(eng) -> str:
    k = _sx(eng).get("k8") or {}
    rows = k.get("rows") or []
    if not k.get("covered"):
        return ""

    def tr(r):
        s = SEV_T[r["sev"]]
        return (f'<tr><td class="nw">{esc(r["date"])}</td><td><span class="pill {s[2]}">{T(s[0], s[1])}</span></td>'
                f'<td class="nw">{_nm(r)}</td><td>{esc(r["form"])}</td><td class="small">{esc("、".join(r["labels"]))}'
                f'{(" <span class=muted>(" + esc(", ".join(r["items"])) + ")</span>") if r["items"] else ""}</td>'
                f'<td><a href="{esc(r["url"])}" target="_blank" rel="noopener">SEC</a></td></tr>')
    hi = [r for r in rows if r["sev"] >= 2]
    lo = [r for r in rows if r["sev"] < 2]
    head = (f'<thead><tr><th>{T("日期", "Date")}</th><th>{T("等級", "Level")}</th><th>{T("公司", "Company")}</th><th>{T("表單", "Form")}</th>'
            f'<th>{T("內容", "Items")}</th><th></th></tr></thead>')
    body = (f'<div class="scroll"><table class="mini">{head}<tbody>{"".join(tr(r) for r in hi)}</tbody></table></div>' if hi else
            f'<p class="muted">{T("最近 30 天精選池沒有「重大／留意」等級的申報。", "No high / medium filings in the last 30 days.")}</p>')
    if lo:
        body += (f'<details class="sgx"><summary>{T("一般申報", "Routine filings")} {len(lo)}</summary><div class="scroll"><table class="mini">{head}'
                 f'<tbody>{"".join(tr(r) for r in lo[:40])}</tbody></table></div></details>')
    note = T(f"美股精選池 {k['covered']} 家公司最近 {k['days']} 天在 SEC 的申報，依 8-K 項目分級。重大＝4.02 財報不可信賴、1.03 破產、2.06 資產減損、"
             "3.01 下市通知、4.01 換會計師、2.04 債務違約觸發、延遲申報等；留意＝高管異動、併購完成、重組裁員、增資發行、主動型投資人持股。"
             "申報不等於利空，請點 SEC 看原文。", "Recent SEC filings of the curated US names, graded by 8-K item.")
    return card("SEC 重大申報", "SEC material filings",
                f'<p class="small muted">{note}</p><div class="kv"><div><span class="muted">{T("重大", "High")}</span><b class="dn">{k["n_hi"]}</b></div>'
                f'<div><span class="muted">{T("留意", "Medium")}</span><b>{k["n_mid"]}</b></div></div>' + body, "wide")


def sec_earn_moves(eng) -> str:
    rows = _sx(eng).get("earn") or []
    if not rows:
        return ""

    def verdict(r):
        x = r.get("ratio")
        if x is None:
            return '<span class="muted">—</span>'
        if x >= 1.25:
            return T("市場預期比過去大", "Pricing a bigger move than usual")
        if x <= 0.8:
            return T("市場預期比過去小", "Pricing a smaller move than usual")
        return T("和過去差不多", "In line with history")
    tm = {"pre": ("盤前", "pre-mkt"), "after": ("盤後", "after close"), "": ("時間未定", "time n/a")}
    tr = "".join(
        f'<tr><td class="nw">{esc(r["date"][5:])}{_wd(r["date"])} <span class="muted small">{T(*tm.get(r["time"], tm[""]))}</span></td>'
        f'<td class="nw">{_nm(r)}{_theme_chip(r["theme"])}</td>'
        + _td(r.get("mv"), f'<b>±{num(r["mv"], 1)}%</b>' if r.get("mv") is not None else '<span class="muted">—</span>')
        + f'<td class="small muted nw">{esc((r.get("exp") or "—")[5:])}</td>'
        + f'<td class="small nw">{" ".join(f"<span class={cls(v)}>{v:+.1f}%</span>" for v in r["reacts"]) or "—"}</td>'
        + _td(r.get("avg"), num(r.get("avg"), 1, pct=True)) + f'<td class="small">{verdict(r)}</td></tr>' for r in rows)
    note = T("隱含波動＝財報日後第一個到期日的價平跨式（買權＋賣權中價）÷ 股價，代表選擇權市場「平均預期」的漲跌幅度（約 0.8 個標準差），"
             "到期日離財報越遠、混入的非財報波動越多。過去反應＝最近 4 次財報前一日收盤到財報後一日收盤的漲跌（盤前、盤後公布都涵蓋）。"
             "CBOE 延遲報價，資料每 4 小時更新。", "Implied move = ATM straddle (first expiry after the report) ÷ price. Past reactions = last 4 reports.")
    return card("財報前隱含波動 vs 歷史反應（未來 14 天）", "Earnings implied move vs history (next 14 days)",
                f'<p class="small muted">{note}</p><div class="scroll"><table class="mini srt"><thead><tr>{_th("財報日", "Report", False)}'
                f'{_th("個股", "Stock", False)}{_th("隱含波動", "Implied")}<th>{T("到期日", "Expiry")}</th><th>{T("過去 4 次反應", "Last 4 reactions")}</th>'
                f'{_th("過去平均幅度", "Avg |move|")}<th>{T("比較", "Read")}</th></tr></thead><tbody>{tr}</tbody></table></div>', "wide")


# ================================================================== 情緒與警報
FG_COL = [(25, "#e5484d"), (45, "#ec835a"), (55, "#8f8d86"), (75, "#7fbf6a"), (101, "#2fbf71")]


def _fg_col(x):
    for lim, c in FG_COL:
        if x < lim:
            return c
    return FG_COL[-1][1]


def _fg_gauge(fg: Dict) -> str:
    x = fg["score"]
    segs = "".join(f'<i style="flex:{b - a};background:{c};opacity:.55"></i>' for (a, (b, c)) in zip([0, 25, 45, 55, 75], FG_COL))
    return (f'<div class="fgh"><div class="fgn" style="color:{_fg_col(x)}">{x:.0f}</div><div><div class="lvl">{T(fg["label"], fg["label_en"])}</div>'
            f'<div class="small muted">{T("一週前", "1w ago")} {num(fg.get("w1"), 0)}・{T("一個月前", "1m ago")} {num(fg.get("m1"), 0)}・{T("一年前", "1y ago")} {num(fg.get("y1"), 0)}</div></div></div>'
            f'<div class="gauge"><div class="track">{segs}<b style="left:{min(99.5, max(0.5, x)):.1f}%"></b></div></div>')


def sec_fg_mini(eng) -> str:
    fg = _sx(eng).get("fg") or {}
    if not fg.get("available"):
        return ""
    return card("恐慌與貪婪指數", "Fear & greed", _fg_gauge(fg) + f'<p class="note"><a href="#mood" class="golink" data-p="mood">'
                + T("看七個分項與歷史統計 →", "Factors and history →") + "</a></p>", "span4")


def sec_fg(eng) -> str:
    fg = _sx(eng).get("fg") or {}
    if not fg.get("available"):
        return ""
    comps = "".join(f'<tr><td>{T(c["zh"], c["en"])}<div class="muted small">{esc(c["def"])}</div></td>'
                    f'<td class="r" style="min-width:120px">{_fgbar(c["v"])}</td></tr>' for c in fg["components"])
    s = pd.Series([v for _, v in fg["hist"]], index=pd.to_datetime([d for d, _ in fg["hist"]]))
    ch = line_chart("fgline", s, "恐慌與貪婪", 0, fixed=(0, 100), bands=[(0, 25, "#e5484d"), (75, 100, "#2fbf71")])
    bk = "".join(f'<tr><td>{T(b["zh"], b["en"])} <span class="muted small">{b["lo"]}–{b["hi"]}</span></td><td class="r">{b["n"]}</td>'
                 f'<td class="r {cls(b["avg"])}">{num(b["avg"], 1, sign=True, pct=True)}</td><td class="r">{num(b["win"], 0, pct=True)}</td></tr>'
                 for b in fg["buckets"])
    note = T(f"七個分項各自和自己過去兩年比較，換成 0～100 的百分位再平均（≥ 3 項才計分）；50 附近＝和近兩年的平常差不多。"
             f"下表是 {fg['since']} 年以來各區間之後 20 個交易日標普 500 的表現；全部日子平均 {num(fg.get('base_avg'), 1, sign=True)}%、上漲比例 {num(fg.get('base_win'), 0)}%。"
             "極度恐慌之後平均報酬常常反而較好，但波動也大；這是歷史統計，不是預測。",
             "Seven factors, each a percentile vs its own last two years, averaged. Forward 20-day S&P 500 returns by zone since inception.")
    body = (_fg_gauge(fg) + f'<div class="g2"><div><h3>{T("分項（0＝極度恐慌，100＝極度貪婪）", "Factors (0 fear – 100 greed)")}</h3>'
            f'<table class="mini">{comps}</table></div><div><h3>{T("近一年走勢", "Last 12 months")}</h3>{ch}</div></div>'
            f'<h3>{T("歷史：落在各區間之後 20 個交易日的標普 500", "History: S&P 500 over the next 20 sessions")}</h3>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("區間", "Zone")}</th><th class="r">{T("天數", "Days")}</th>'
            f'<th class="r">{T("平均報酬", "Avg")}</th><th class="r">{T("上漲比例", "Up")}</th></tr></thead><tbody>{bk}</tbody></table></div>'
            f'<p class="note">{note}　{T("資料日", "As of")} {esc(fg["asof"])}</p>')
    return card("恐慌與貪婪指數（多因子）", "Fear & greed (multi-factor)", body, "wide")


def _fgbar(v) -> str:
    if v is None:
        return '<span class="muted">—</span>'
    return f'<div class="sbar"><i style="width:{v:.0f}%;background:{_fg_col(v)}"></i><b>{v:.0f}</b></div>'


def sec_em(eng) -> str:
    em = _sx(eng).get("em") or {}
    if not em.get("available"):
        return ""
    tr = []
    for r in em["rows"]:
        for b in r["bands"]:
            rt = b.get("ratio")
            rd = ("—" if rt is None else T("選擇權定價偏貴（預期波動 > 近期實際）", "Options rich vs realised") if rt >= 1.25
                  else T("選擇權定價偏便宜（預期 < 近期實際）", "Options cheap vs realised") if rt <= 0.8 else T("和近期實際波動相近", "In line with realised"))
            tr.append(f'<tr><td class="nw"><b>{esc(r["sym"])}</b> <span class="muted small">{esc(r["zh"])}</span></td><td>{T(b["zh"], b["en"])}'
                      f' <span class="muted small">{esc(b["exp"][5:])}（{b["days"]} {T("天", "d")}）</span></td><td class="r">{num(r["spot"], 2)}</td>'
                      f'<td class="r"><b>±{num(b["sd"], 1)}%</b></td><td class="r nw">{num(b["lo"], 2)} – {num(b["hi"], 2)}</td>'
                      f'<td class="r">±{num(b.get("rv_sd"), 1)}%</td><td class="small">{rd}</td></tr>')
    note = T("用 CBOE 延遲報價的價平跨式價推算：一個標準差 ≈ 跨式價 ÷ 股價 × 1.25，約 68% 的機率收在區間內。收盤落在區間外＝超出市場預期的「真突破／真破位」，"
             "區間內的漲跌多半是雜訊。右側用近 20 日實際波動換算同樣天數做比較。", "One standard deviation ≈ ATM straddle ÷ price × 1.25 (≈68% range).")
    return card("期權預期波動區間", "Options-implied ranges",
                f'<p class="small muted">{note}</p><div class="scroll"><table class="mini"><thead><tr><th>ETF</th><th>{T("期間", "Horizon")}</th>'
                f'<th class="r">{T("現價", "Spot")}</th><th class="r">{T("一個標準差", "1 s.d.")}</th><th class="r">{T("預期區間", "Range")}</th>'
                f'<th class="r">{T("近期實際波動", "Realised")}</th><th>{T("解讀", "Read")}</th></tr></thead><tbody>{"".join(tr)}</tbody></table></div>', "wide")


VD = {"warn": ("dn", "⚠"), "rev": ("up", "↺"), "none": ("muted", "·"), "n": ("muted", "·")}


def sec_rules(eng) -> str:
    rb = _sx(eng).get("rules") or {}
    if not rb.get("available"):
        return ""
    b = rb["base"]
    fired = ' <span class="pill warn">' + T("近 5 日觸發", "Fired ≤5d") + "</span>"
    tr = "".join(
        f'<tr><td>{T(r["zh"], r["en"])}{fired if r["now"] else ""}</td>'
        f'<td class="r">{r["n"]}</td><td class="r {cls(r["avg5"])}">{num(r["avg5"], 1, sign=True, pct=True)}</td>'
        f'<td class="r {cls(r["avg20"])}">{num(r["avg20"], 1, sign=True, pct=True)}</td><td class="r">{num(r["win20"], 0, pct=True)}</td>'
        f'<td class="r"><b>{num(r["dd5"], 0, pct=True)}</b></td><td class="small {VD[r["verdict"]][0]}">{VD[r["verdict"]][1]} {T(r["vz"], r["ve"])}</td>'
        f'<td class="small muted nw">{esc(r["last"] or "—")}</td></tr>' for r in rb["rows"] if r["n"] > 0)
    note = T(f"每條規則從 {rb['since']} 年起重跑：觸發日收盤之後標普 500 的表現（同一波 {rb['cooldown']} 個交易日內只算一次）。"
             f"比較基準＝任何一天：5 日平均 {b['avg5']:+.2f}%、20 日平均 {b['avg20']:+.2f}%、20 日上漲比例 {b['win20']:.0f}%、20 日內再跌 5% 的機率 {b['dd5']:.0f}%。"
             "「有預警力」＝再跌 5% 的機率至少是基準的 1.5 倍；「常是短線低點」＝之後 20 日平均反而比平常好。急跌後常見反彈，所以多數盤中急跌警報其實沒有預警力。",
             "Each alarm rule re-run on history: what the S&P 500 did next, vs any day.")
    return card("大盤警報規則回測", "Do the sell-off alarms work?",
                f'<p class="small muted">{note}</p><div class="scroll"><table class="mini"><thead><tr><th>{T("規則", "Rule")}</th><th class="r">{T("次數", "n")}</th>'
                f'<th class="r">{T("5 日後", "+5d")}</th><th class="r">{T("20 日後", "+20d")}</th><th class="r">{T("20 日上漲比例", "Up 20d")}</th>'
                f'<th class="r">{T("20 日內再跌 5%", "−5% within 20d")}</th><th>{T("判定", "Verdict")}</th><th>{T("最近一次", "Last")}</th></tr></thead>'
                f'<tbody>{tr}</tbody></table></div><p class="note">{T("資料日", "As of")} {esc(rb["asof"])}</p>', "wide")


GEO_COL = ["#6b7280", "#c9a227", "#ec835a", "#e5484d"]
TK_NM = {"^TWII": "台股加權", "TWD=X": "美元/台幣", "EWT": "台灣 ETF", "^STOXX50E": "歐洲 50", "BZ=F": "布蘭特原油", "NG=F": "天然氣",
         "GC=F": "黃金", "^VIX": "VIX", "^KS11": "韓國 KOSPI", "KRW=X": "美元/韓元"}


def sec_geo(eng) -> str:
    g = _sx(eng).get("geo") or {}
    if not g.get("available"):
        return ""
    cards = []
    for r in g["rows"]:
        lv = r["level"]
        rt = f'{T("約平常的", "≈")} {lv["ratio"]:.1f} {T("倍", "× normal")}' if lv.get("ratio") else T("基準累積中", "baseline building")
        mk = "".join(f'<span class="chip">{esc(TK_NM.get(m["t"], m["t"]))} <b class="{cls(m["d1"])}">{num(m["d1"], 1, sign=True, pct=True)}</b>'
                     f'{" <b class=warn>!</b>" if m.get("z") is not None and abs(m["z"]) >= 2 else ""}</span>' for m in r["mk"])
        lv_t = {3: ("重大", "L3"), 2: ("軍事／制裁", "L2"), 1: ("外交", "L1"), 0: ("", "")}
        news = "".join(f'<li><span class="pill" style="border-color:{GEO_COL[n["lv"]]};color:{GEO_COL[n["lv"]]}">{esc(lv_t[n["lv"]][0]) or "—"}</span> '
                       f'<a href="{esc(n["link"])}" target="_blank" rel="noopener">{esc(n["t"][:140])}</a></li>' for n in r["top"])
        cards.append(f'<div class="geoc" style="border-left-color:{GEO_COL[lv["k"]]}"><div class="gh"><b>{T(r["zh"], r["en"])}</b>'
                     f'<span class="pill" style="color:{GEO_COL[lv["k"]]};border-color:{GEO_COL[lv["k"]]}">{T(lv["label"], lv["label_en"])}</span>'
                     f'<span class="muted small">{T("熱度", "Heat")} {r["score"]:.0f}・{rt}・{T("72 小時", "72h")} {r["n"]} {T("則", "items")}</span></div>'
                     f'<div class="chips">{mk}</div><ul class="lines small">{news}</ul></div>')
    note = T("用 Google 新聞標題做關鍵字分級（不經 AI）：重大＝入侵、封鎖、宣戰、核試等；軍事／制裁＝飛彈、空襲、軍演、擊落、制裁等；外交＝談判、警告、停火等。"
             "熱度＝72 小時內加權則數，和這個區域自己過去 30 天的中位數比較（持續中的戰爭不會天天顯示高度緊張，看的是「變化」）。"
             "關鍵字分級會誤判，請點標題看原文；市場欄的「!」＝今日變動超過該資產兩個標準差。",
             "Keyword-graded Google News headlines (no AI), heat vs each theatre's own last 30 days, plus the related markets.")
    return card("地緣風險燈號", "Geopolitical heat", f'<p class="small muted">{note}</p><div class="geog">{"".join(cards)}</div>', "wide")


# ================================================================== 台美連動（台股頁）
def sec_link(eng) -> str:
    lk = _sx(eng).get("link") or {}
    if not lk.get("available"):
        return ""

    def row(name, r):
        tw = (f'<b class="{cls(r["tw"])}">{num(r["tw"], 2, sign=True, pct=True)}</b> <span class="muted small">{esc((r.get("tw_d") or "")[5:])}</span>'
              if r.get("tw") is not None else f'<span class="muted">{T("待台股開盤", "TW not yet open")}</span>')
        return (f'<tr><td>{name}</td><td class="r"><b class="{cls(r["us_ret"] if "us_ret" in r else r["us"])}">'
                f'{num(r["us_ret"] if "us_ret" in r else r["us"], 2, sign=True, pct=True)}</b> <span class="muted small">{esc(r["us_d"][5:])}</span></td>'
                f'<td class="r">{num(r["corr"], 2)}</td><td class="r">{num(r["beta"], 2)}</td><td class="r {cls(r["implied"])}">{num(r["implied"], 2, sign=True, pct=True)}</td>'
                f'<td class="r">{tw}</td><td class="r muted">{num(r.get("same_big"), 0, pct=True)}</td></tr>')
    head = (f'<thead><tr><th>{T("美股 → 台股", "US → Taiwan")}</th><th class="r">{T("美股前一晚", "US last night")}</th><th class="r">{T("相關係數", "Corr")}</th>'
            f'<th class="r">Beta</th><th class="r">{T("推估台股", "Implied TW")}</th><th class="r">{T("台股實際", "TW actual")}</th>'
            f'<th class="r">{T("大波動同向率", "Same-way on big moves")}</th></tr></thead>')
    idx = "".join(row(f'{esc(r["us_n"])} → {esc(r["tw_n"])}', r) for r in lk.get("index", []))
    th = "".join(row(f'{T(r["us_theme"], r["us_theme"])} <span class="muted small">({r["n_us"]})</span> → {T(r["tw_theme"], r["tw_theme"])} '
                     f'<span class="muted small">({r["n_tw"]})</span>', r) for r in lk.get("rows", []))
    body = f'<div class="scroll"><table class="mini">{head}<tbody>{idx}{th}</tbody></table></div>'
    a = lk.get("adr")
    if a and abs(a["now"]) < 60:                                  # a broken quote (e.g. a split not yet adjusted) is not shown
        s = pd.Series([v for _, v in a["hist"]], index=pd.to_datetime([d for d, _ in a["hist"]]))
        body += (f'<h3>{T("台積電 ADR 溢價", "TSMC ADR premium")}</h3><div class="kv"><div><span class="muted">{T("目前", "Now")}</span><b>{num(a["now"], 1, sign=True, pct=True)}</b></div>'
                 f'<div><span class="muted">{T("一年平均", "1y avg")}</span><b>{num(a["avg1y"], 1, sign=True, pct=True)}</b></div>'
                 f'<div><span class="muted">{T("一年區間", "1y range")}</span><b>{num(a["lo"], 0)}% ~ {num(a["hi"], 0)}%</b></div>'
                 f'<div><span class="muted">{T("一年百分位", "1y percentile")}</span><b>{num(a["pct"], 0)}</b></div></div>'
                 + f'<div class="chartbox">{line_chart("adrprem", s, "TSM ADR 溢價 %", 1)}</div>')
    note = T("台股每個交易日對應「前一晚」的美股收盤（台北時間），用近一年資料算相關係數與 Beta；推估台股＝Beta × 美股前一晚漲跌。"
             "族群用本站精選池等權平均（括號內為檔數）。大波動同向率＝美股前一晚漲跌 ≥ 2% 時台股同方向的比例。"
             "ADR 溢價＝TSM ÷（2330 × 5 ÷ 美元台幣）− 1，同日收盤比較，溢價偏高時常有回歸平均的傾向，但可以持續很久。",
             "Each Taiwan session paired with the previous US close; beta / correlation over the last year. ADR premium = TSM vs 5 × 2330 in USD.")
    return card("台美連動", "US → Taiwan linkage", f'<p class="small muted">{note}</p>' + body, "wide")


# ================================================================== 過熱清單（買點訊號頁）
def sec_exhaust(eng) -> str:
    from wsb.analytics import patterns as PT
    sg = getattr(eng, "signals", None) or {}
    if not sg.get("available"):
        return ""
    rows = []
    for mk, m in sg["markets"].items():
        for r in m.get("exhausted") or []:
            rows.append((mk, r))
    rows.sort(key=lambda x: -x[1]["exh"]["n"])
    tr = "".join(f'<tr><td class="nw">{_nm(r)}{_theme_chip(r.get("theme", "其他"))}</td><td>{T(*MK[mk])}</td><td class="r">{num(r.get("price"), 2)}</td>'
                 f'<td class="r"><b class="dn">{r["exh"]["n"]}</b></td><td class="small">{esc(PT.exh_text(r["exh"]))}</td></tr>' for mk, r in rows)
    defs = "".join(f'<li><b>{T(*PT.EXH[k])}</b>：{esc(v)}</li>' for k, v in PT.EXH_DEF.items())
    body = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("個股", "Stock")}</th><th>{T("市場", "Market")}</th><th class="r">{T("現價", "Price")}</th>'
            f'<th class="r">{T("警示數", "Flags")}</th><th>{T("哪些警示", "Which")}</th></tr></thead><tbody>{tr}</tbody></table></div>' if rows else
            f'<p class="muted">{T("目前精選池沒有同時出現 2 個以上力竭警示的股票。", "No stock shows two or more exhaustion flags right now.")}</p>')
    note = T("同時出現 2 個以上力竭警示的股票。這些是「短線追高風險較高」的描述，不代表會下跌，強勢股可以過熱很久；如果要加碼，可以等回到加碼參考區再看。",
             "Stocks with two or more exhaustion flags — higher short-term chase risk, not a sell signal.")
    return card("過熱／力竭警示", "Overheating / exhaustion watch", f'<p class="small muted">{note}</p>{body}'
                f'<details class="sgx"><summary>{T("五種警示的定義", "Definitions")}</summary><ul class="small">{defs}</ul></details>', "wide")


# ================================================================== 硬科技一分鐘科普（族群頁）
EXPLAIN = [
    ("CoWoS 先進封裝", "CoWoS packaging", ["半導體", "AI伺服器與雲端"],
     "台積電的 2.5D 封裝：把 GPU 和多顆 HBM 記憶體並排放在一片矽中介層上，用極細的線路連在一起，讓資料在晶片之間高速傳輸。"
     "AI 加速器幾乎都靠它，產能多寡直接決定 GPU 能出貨多少，所以這幾年一直是 AI 供應鏈的瓶頸之一。",
     "看點：台積電 CoWoS 月產能擴充進度、封測廠與設備商的接單、輝達與 ASIC 客戶的投片量。"),
    ("HBM 高頻寬記憶體", "HBM", ["半導體"],
     "把多層 DRAM 晶片垂直堆疊、用矽穿孔（TSV）打通，放在 GPU 旁邊，頻寬是一般記憶體的數倍。AI 模型越大越吃記憶體頻寬，"
     "每顆 AI 加速器搭配的 HBM 容量一代比一代多。主要供應商是 SK 海力士、三星與美光。",
     "看點：HBM 世代（HBM3E → HBM4）、良率與價格、記憶體廠資本支出。"),
    ("CPO 共同封裝光學／矽光子", "Co-packaged optics", ["半導體", "AI伺服器與雲端"],
     "資料中心交換器原本用可插拔光模組把電訊號轉成光訊號，耗電又佔空間。CPO 把光學引擎直接封裝在交換器晶片旁邊，"
     "縮短電訊號走的距離、降低功耗。博通與輝達都已推出 CPO 交換器，量產規模仍在爬坡。",
     "看點：大型雲端業者導入時程、與可插拔光模組的成本比較、良率與維修性。"),
    ("High-NA EUV 曝光機", "High-NA EUV", ["半導體"],
     "ASML 的新一代極紫外光曝光機，數值孔徑從 0.33 提高到 0.55，可以印出更細的線路、減少多重曝光步驟。單台價格遠高於現有 EUV。"
     "英特爾最積極導入，台積電態度較保守、先以現有 EUV 延伸。",
     "看點：ASML 出貨台數與訂單、晶圓廠在 1.4 奈米等級製程是否採用。"),
    ("GAA 環繞式閘極（2 奈米）", "Gate-all-around transistors", ["半導體"],
     "電晶體結構從 FinFET（鰭式）換成閘極四面包住通道的奈米片，能在更小尺寸下控制漏電。台積電 N2、三星 3 奈米、英特爾 18A 都採用這類結構，"
     "是製程換代的關鍵節點。",
     "看點：2 奈米良率與客戶數、晶圓價格、各家量產時程。"),
    ("背面供電", "Backside power delivery", ["半導體"],
     "把供電線路從晶片正面移到背面，正面只走訊號線，可以降低壓降、提高密度與效能。英特爾稱 PowerVia，台積電在 A16 製程導入 Super Power Rail。",
     "看點：量產時程與實際效能提升、設計工具與封裝的配合。"),
    ("AI 客製化晶片（ASIC）", "Custom AI chips", ["半導體", "AI伺服器與雲端", "科技平台"],
     "Google TPU、亞馬遜 Trainium、Meta MTIA 等雲端業者自己設計的 AI 晶片，針對自家模型最佳化，單位成本與耗電可能比通用 GPU 低。"
     "設計服務夥伴包括博通、Marvell 與台灣的 IC 設計服務公司。",
     "看點：雲端資本支出中 ASIC 的比重、與 GPU 的效能／成本差距、軟體生態。"),
    ("液冷散熱", "Liquid cooling", ["AI伺服器與雲端", "電力與工業"],
     "新一代 AI 機櫃功耗可達每櫃上百千瓦，傳統風扇吹不動，改用冷板直接貼在晶片上、用冷卻液把熱帶走，再由冷卻液分配單元（CDU）集中排熱。"
     "資料中心的機房設計、電力與散熱設備都要跟著改。",
     "看點：液冷滲透率、機櫃功耗演進、散熱與電力設備廠的訂單。"),
    ("800V 直流供電", "800V DC power", ["電力與工業", "AI伺服器與雲端"],
     "AI 機櫃功耗持續上升，用傳統交流電與 54V 配電會有大量轉換損耗與粗重銅排。輝達提出在資料中心改用 800V 高壓直流配電，"
     "減少轉換次數與用銅量，預計搭配下一代機櫃推出。",
     "看點：電源供應器、變壓與配電設備廠的規格與時程。"),
    ("SMR 小型模組化反應爐", "Small modular reactors", ["電力與工業", "能源"],
     "發電量約 300 百萬瓦以下、可在工廠預製模組再運到現場組裝的核反應爐，目標是縮短工期與降低單案風險。"
     "AI 資料中心需要大量穩定電力，科技公司陸續簽約支持核能。NuScale 的設計已取得美國核管會（NRC）核准，Oklo 等業者仍在審查流程中，"
     "目前多數 SMR 尚未有商業運轉的機組，營收規模仍小。",
     "看點：NRC 審查進度、首座機組時程與造價、與電力公司或科技公司的購電合約。"),
    ("Chiplet 小晶片／UCIe", "Chiplets / UCIe", ["半導體"],
     "把一顆大晶片拆成多個小晶片，各自用最適合的製程生產，再用先進封裝接起來，良率較高、設計可重複使用。"
     "UCIe 是業界制定的小晶片互連標準，讓不同公司的小晶片未來有機會混搭。",
     "看點：先進封裝產能、互連標準普及、處理器與加速器的設計趨勢。"),
    ("低軌衛星通訊", "LEO satellite broadband", ["國防軍工", "電信公用"],
     "在數百到兩千公里的低軌道部署大量衛星提供網路，延遲比傳統同步衛星低很多。SpaceX 的 Starlink 規模最大，"
     "亞馬遜 Kuiper 等也在佈建；國防、航空與偏遠地區通訊都是應用。",
     "看點：發射頻率、用戶數、地面設備與衛星零組件供應鏈。"),
]


def sec_explainer(eng) -> str:
    cards = "".join(f'<details class="exp"><summary><b>{esc(zh)}</b> <span class="muted small">{esc(en)}</span>'
                    f'{"".join(_theme_chip(t) for t in ths)}</summary><p>{esc(body)}</p><p class="small muted">{esc(watch)}</p></details>'
                    for zh, en, ths, body, watch in EXPLAIN)
    note = T("族群背後的關鍵技術，各用一分鐘講清楚在做什麼、為什麼重要、接下來看什麼。內容是技術背景整理，不涉及個股建議。",
             "One-minute explainers of the technologies behind the themes.")
    return card("硬科技一分鐘科普", "Hard-tech in one minute", f'<p class="small muted">{note}</p><div class="expg">{cards}</div>', "wide")


# ================================================================== AI 多空辯論（成長估值頁）
def sec_debate(eng) -> str:
    rows = _sx(eng).get("debate") or []
    if not rows:
        return ""
    out = []
    for r in rows:
        a = r.get("ai")
        head = (f'<div class="gh"><span class="muted">#{r["rank"]}</span><b>{esc(r["name"][:32])}</b><span class="tk">{esc(r["sym"])}</span>'
                f'<span class="muted small">{T("營收年增", "Rev growth")} {num(r.get("g"), 0, pct=True)}・{T("估值÷成長", "Value÷growth")} {num(r.get("gav"), 3)} {esc(r.get("basis") or "")}</span></div>')
        if a:
            body = (f'<p><b class="up">{T("多方", "Bull")}</b>　{esc(a["bull"])}</p><p><b class="dn">{T("空方", "Bear")}</b>　{esc(a["bear"])}</p>'
                    f'<p><b class="warn">{T("風控", "Risk")}</b>　{esc(a["risk"])}</p><p class="muted small">{esc(a.get("date", ""))} · {esc(a.get("engine", ""))}</p>')
        else:
            body = f'<p class="muted small">{T("這檔的 AI 短評還沒產生（每週更新）。", "Not written yet (weekly).")}</p>'
        out.append(f'<div class="deb">{head}{body}</div>')
    note = T("成長估值榜前 10 名，每週一次讓 AI 只根據表上的數字分別寫多方、空方與風控觀察。AI 可能誤讀數字，請以表格原始數據為準；這不是投資建議。",
             "Weekly AI notes (bull / bear / risk) on the growth leaders, written only from the numbers shown. Not advice.")
    return card("AI 多空辯論（成長股前 10）", "AI bull vs bear (growth top 10)", f'<p class="small muted">{note}</p><div class="debg">{"".join(out)}</div>', "wide")


# ================================================================== 工具：交易成本試算
def sec_fees(eng) -> str:
    us = (f'<div class="calc" data-m="us"><div class="cg">'
          f'<label>{T("股數", "Shares")}<input type="number" step="any" data-k="q" value="10"></label>'
          f'<label>{T("買進價（美元）", "Buy price (USD)")}<input type="number" step="any" data-k="b" value="100"></label>'
          f'<label>{T("賣出價（美元）", "Sell price (USD)")}<input type="number" step="any" data-k="s" value="110"></label>'
          f'<label>{T("手續費率 %", "Commission %")}<input type="number" step="any" data-k="r" value="0.25"></label>'
          f'<label>{T("每筆最低手續費（美元）", "Min. commission (USD)")}<input type="number" step="any" data-k="m" value="0"></label>'
          f'<label>{T("SEC 規費（每百萬美元賣出）", "SEC fee per $1M sold")}<input type="number" step="any" data-k="sec" value="0"></label>'
          f'<label>{T("FINRA TAF（每股，賣出）", "FINRA TAF per share sold")}<input type="number" step="any" data-k="taf" value="0.000166"></label>'
          f'<label>{T("每股年配息（美元，選填）", "Annual dividend / share")}<input type="number" step="any" data-k="d" value="0"></label>'
          f'</div><div class="cout"></div></div>')
    tw = (f'<div class="calc" data-m="tw"><div class="cg">'
          f'<label>{T("股數", "Shares")}<input type="number" step="any" data-k="q" value="1000"></label>'
          f'<label>{T("買進價（台幣）", "Buy price (TWD)")}<input type="number" step="any" data-k="b" value="100"></label>'
          f'<label>{T("賣出價（台幣）", "Sell price (TWD)")}<input type="number" step="any" data-k="s" value="105"></label>'
          f'<label>{T("手續費折數（1＝不打折）", "Commission discount (1 = none)")}<input type="number" step="any" data-k="dc" value="1"></label>'
          f'<label>{T("每筆最低手續費（台幣）", "Min. commission (TWD)")}<input type="number" step="any" data-k="m" value="20"></label>'
          f'<label>{T("證交稅", "Transaction tax")}<select data-k="tax"><option value="0.003">{T("股票 0.3%", "Stock 0.3%")}</option>'
          f'<option value="0.001">{T("ETF 0.1%", "ETF 0.1%")}</option><option value="0.0015">{T("現股當沖 0.15%", "Day trade 0.15%")}</option></select></label>'
          f'</div><div class="cout"></div></div>')
    note = T("所有預設值都只是範例，請改成你券商的實際費率（複委託常見有最低手續費、優惠折扣，以對帳單為準）。"
             "台股手續費＝成交金額 × 0.1425% × 折數，買賣各收一次；證交稅只在賣出收。美股股息對台灣投資人預扣 30%。"
             "SEC 規費費率每年由 SEC 公告調整，FINRA TAF 只在賣出收取且有單筆上限。計算只在你的瀏覽器裡進行，不會送出或儲存任何資料。",
             "All defaults are placeholders — enter your broker's real rates. Runs entirely in your browser; nothing is sent or stored.")
    return card("交易成本試算（手續費・稅・損益兩平）", "Trading-cost calculator",
                f'<p class="small muted">{note}</p>' + _tabset("fee", [("美股複委託", "US (sub-brokerage)", us), ("台股", "Taiwan", tw)]), "wide")


CSS = """
.chartbox{max-width:680px}.fgh{display:flex;align-items:center;gap:14px}.fgn{font-size:54px;font-weight:800;line-height:1}
.g2{display:grid;grid-template-columns:1fr 1.3fr;gap:16px}@media(max-width:760px){.g2{grid-template-columns:1fr}}
th.sk{cursor:pointer;user-select:none}th.sk:hover{color:var(--ac)}th.sk.asc:after{content:" ▲";font-size:9px}th.sk.desc:after{content:" ▼";font-size:9px}
.geog{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px}.geoc{background:var(--card2);border:1px solid var(--bd);border-left:4px solid;border-radius:8px;padding:10px 12px}
.geoc ul.lines{margin:6px 0 0;padding-left:0;list-style:none}.geoc ul.lines li{margin:4px 0}.geoc a{color:var(--tx2)}.warn{color:var(--warn)}
.expg{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:8px}details.exp{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:8px 12px}
details.exp summary{cursor:pointer}details.exp p{margin:8px 0 0;font-size:13px}
.debg{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:10px}.deb{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:10px 12px}.deb p{margin:6px 0;font-size:13px}
.calc .cg{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px}.calc label{display:flex;flex-direction:column;font-size:12px;color:var(--mu);gap:3px}
.calc input,.calc select{background:var(--card2);border:1px solid var(--bd);color:var(--tx);border-radius:6px;padding:6px 8px;font:inherit;font-size:14px}
.cout{margin-top:12px}.cout table td{padding:4px 8px}.cout b.big2{font-size:18px}
.tagc{display:inline-block;margin:2px 4px 0 0;padding:0 6px;border-radius:4px;font-size:11px;border:1px solid var(--ac);color:var(--ac)}.tagc.ex{border-color:var(--dn);color:var(--dn)}
"""

JS = r"""
(function(){var en=function(){return document.documentElement.lang==='en';};
document.querySelectorAll('table.srt').forEach(function(t){var ths=t.querySelectorAll('thead th');ths.forEach(function(th,i){if(!th.classList.contains('sk'))return;
 th.addEventListener('click',function(){var asc=th.classList.contains('desc');
  ths.forEach(function(x){x.classList.remove('asc','desc');});th.classList.add(asc?'asc':'desc');var tb=t.tBodies[0],rs=[].slice.call(tb.rows);
  rs.sort(function(a,b){var x=a.cells[i],y=b.cells[i];var vx=x&&x.dataset.v,vy=y&&y.dataset.v;var nx=parseFloat(vx),ny=parseFloat(vy);
   if(vx==null||vx==='')return 1;if(vy==null||vy==='')return -1;var c=(!isNaN(nx)&&!isNaN(ny))?nx-ny:String(vx).localeCompare(String(vy));return asc?c:-c;});
  rs.forEach(function(r){tb.appendChild(r);});});});});
function f(x,d){return isFinite(x)?Number(x).toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d}):'—';}
function row(a,b,c){return '<tr><td>'+a+'</td><td class="r">'+b+'</td>'+(c?'<td class="muted small">'+c+'</td>':'')+'</tr>';}
function calc(w){var m=w.dataset.m,v={};w.querySelectorAll('[data-k]').forEach(function(i){v[i.dataset.k]=parseFloat(i.value)||0;});
 var q=v.q,bv=q*v.b,sv=q*v.s,cur=m==='us'?'US$':'NT$',d=m==='us'?2:0,bf,sf,tax=0,taf=0,sec=0;
 if(m==='us'){bf=Math.max(bv*v.r/100,v.m);sf=Math.max(sv*v.r/100,v.m);sec=sv*v.sec/1e6;taf=Math.min(q*v.taf,8.30);}
 else{bf=Math.max(Math.floor(bv*0.001425*v.dc),v.m);sf=Math.max(Math.floor(sv*0.001425*v.dc),v.m);tax=Math.floor(sv*v.tax);}
 var fees=bf+sf+tax+sec+taf,pnl=sv-bv-fees,cost=bv+bf;
 // break-even sell price: solve q*p - fee(p) = cost (fees are near-linear; iterate)
 var p=v.b;for(var k=0;k<40;k++){var s2=q*p,f2=m==='us'?Math.max(s2*v.r/100,v.m)+s2*v.sec/1e6+Math.min(q*v.taf,8.30):Math.max(Math.floor(s2*0.001425*v.dc),v.m)+Math.floor(s2*v.tax);p=(cost+f2)/q;}
 var be=(p/v.b-1)*100,fr=fees/Math.max(bv,1)*100,L=en();
 var h='<table class="mini">'+row(L?'Buy amount':'買進金額',cur+' '+f(bv,d))+row(L?'Buy commission':'買進手續費',cur+' '+f(bf,d))
  +row(L?'Sell amount':'賣出金額',cur+' '+f(sv,d))+row(L?'Sell commission':'賣出手續費',cur+' '+f(sf,d))
  +(m==='us'?row('SEC',cur+' '+f(sec,2))+row('FINRA TAF',cur+' '+f(taf,2)):row(L?'Transaction tax':'證交稅',cur+' '+f(tax,0)))
  +row('<b>'+(L?'Total costs':'總成本')+'</b>','<b>'+cur+' '+f(fees,d)+'</b>',(L?'= ':'＝ 買進金額的 ')+f(fr,2)+'%')
  +row('<b>'+(L?'Net profit / loss':'淨損益')+'</b>','<b class="big2 '+(pnl>=0?'up':'dn')+'">'+cur+' '+f(pnl,d)+'</b>',(L?'return ':'報酬率 ')+f(pnl/Math.max(cost,1)*100,2)+'%')
  +row(L?'Break-even sell price':'損益兩平賣價',cur+' '+f(p,m==='us'?2:2),(L?'needs ':'需上漲 ')+f(be,2)+'%');
 if(m==='us'&&v.d>0){var g=v.d*q;h+=row(L?'Annual dividend (gross)':'年股息（稅前）',cur+' '+f(g,2))+row(L?'After 30% withholding':'扣 30% 預扣稅後',cur+' '+f(g*0.7,2),(L?'net yield ':'實拿殖利率 ')+f(g*0.7/Math.max(bv,1)*100,2)+'%');}
 w.querySelector('.cout').innerHTML=h+'</table>';}
document.querySelectorAll('.calc').forEach(function(w){w.querySelectorAll('input,select').forEach(function(i){i.addEventListener('input',function(){calc(w);});i.addEventListener('change',function(){calc(w);});});calc(w);});
})();
"""
