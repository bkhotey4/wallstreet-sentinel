"""產業體檢 tab — real-economy strain from company filings: AI infrastructure ledger, sector roll-up, company table,
and the financing-transmission check."""
from __future__ import annotations

from tools.sitekit import T, card, cls, esc, num
from wsb.data import fundamentals as FU


def _b(x) -> str:
    return "—" if x is None else f"{x / 1e9:,.1f}B"


def _flagchips(fl) -> str:
    lab = {k: zh.split("：")[0] for k, zh, _en, _f in FU.RULES}
    return "".join(f'<span class="pill warn">{esc(lab[k])}</span> ' for k in fl) or '<span class="muted small">—</span>'


def sec_ai_ledger(eng) -> str:
    sh = getattr(eng, "sector_health", None) or {}
    led = sh.get("ledger") or []
    if not led:
        return ""
    rows = ""
    for r in led:
        m = r["m"]
        rows += (f'<tr><td class="nw"><b>{esc(r["sym"])}</b> <span class="muted small">{esc(r["name"])}</span></td>'
                 f'<td class="r">{_b(m.get("capex"))}</td><td class="r">{_b(m.get("ocf"))}</td>'
                 f'<td class="r"><b class="{"dn" if (m.get("capex_ocf") or 0) > 1 else ""}">{num(m.get("capex_ocf"), 2)}×</b>'
                 f'<div class="small muted">{T("一年前", "1y ago")} {num(m.get("capex_ocf_prev"), 2)}×</div></td>'
                 f'<td class="r">{(num(m["cip_share"], 0) + "%") if m.get("cip_share") is not None else T("未單獨揭露", "n/d")}</td>'
                 f'<td class="r {cls(-(m.get("debt_growth") or 0))}">{num(m.get("debt_growth"), 0, sign=True, pct=True)}</td>'
                 f'<td class="r">{(num(m["int_burden"], 1) + "%") if m.get("int_burden") is not None else "—"}</td>'
                 f'<td class="small muted">{esc(m.get("end") or "")}</td></tr>')
    note = T("近 12 個月（TTM）資本支出與營運現金流，來自各公司向 SEC 申報的財報。倍數 > 1 代表花的比賺的多，差額要靠借錢、發股或動用現金；"
             "在建工程比例＝已經買下但還沒啟用的設備與廠房（例如等電力、等廠房完工的伺服器）佔全部固定資產的比例，有些公司沒有單獨標註。"
             "負債年增與利息佔營業利益比例，顯示這些支出有多少靠借錢、利率上升時壓力多大。數據描述現況，不是預測。",
             "TTM capex vs operating cash flow from SEC filings; >1× = spending more than the business generates. Construction in progress = "
             "bought but not yet in service. Descriptive, not a forecast.")
    body = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("公司", "Company")}</th><th class="r">{T("資本支出", "Capex")}</th>'
            f'<th class="r">{T("營運現金流", "Op. cash flow")}</th><th class="r">{T("支出／現金流", "Capex / OCF")}</th>'
            f'<th class="r">{T("在建工程比例", "Not yet in service")}</th><th class="r">{T("負債年增", "Debt y/y")}</th>'
            f'<th class="r">{T("利息／營業利益", "Interest / EBIT")}</th><th>{T("財報期", "Period")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="note">{note}</p>')
    return card("AI 基礎建設帳本：花的錢 vs 賺的錢", "AI infrastructure ledger: spending vs cash generated", body, "wide")


def sec_transmission(eng) -> str:
    tr = (getattr(eng, "sector_health", None) or {}).get("transmission") or {}
    if not tr:
        return ""
    tnx = tr.get("tnx")
    items = [(T("資金缺口公司數（支出 > 現金流）", "Companies with a funding gap"), f'{tr["gap_now"]} {T("家（一年前", "(1y ago")} {tr["gap_prev"]}）',
              tr["rising_gap"]),
             (T("壓力指數：信用分項", "Stress index: credit block"), num(tr.get("credit_score"), 0), tr["tight_credit"]),
             (T("10 年期殖利率（3 個月變化）", "10-year yield (3m change)"),
              (f'{tnx[0]:.2f}%（{tnx[1]:+.2f}）' if tnx else "—"), tr["higher_rates"])]
    rows = "".join(f'<tr><td>{a}</td><td class="r"><b>{b}</b></td><td>{"⚠️" if c else "—"}</td></tr>' for a, b, c in items)
    verdict = (T("⚠️ 融資傳導條件成立：越來越多公司要靠外部資金支應資本支出，同時信用收緊或利率上升。這代表壓力正在累積，但歷史上不一定演變成危機——要看營收能否追上支出。",
                 "⚠️ Financing transmission: more companies need outside money while credit tightens or rates rise. Pressure is building; history shows it does not always become a crisis.")
               if tr.get("on") else
               T("目前沒有同時成立：資金缺口增加、和信用收緊或利率上升，至少有一邊沒有發生。", "Not all conditions met right now."))
    body = (f'<table class="mini"><thead><tr><th>{T("條件", "Condition")}</th><th class="r">{T("現況", "Now")}</th><th></th></tr></thead><tbody>{rows}</tbody></table>'
            f'<p><b>{verdict}</b></p><p class="note">{T("規則：資金缺口公司數比一年前多，而且（信用分項 ≥ 60 或 10 年期殖利率 3 個月上升超過 0.25 個百分點）。", "Rule: more funding-gap companies than a year ago AND (credit block ≥ 60 OR 10y yield +0.25pp in 3 months).")}</p>')
    return card("融資傳導：現金流吃緊 × 鷹派利率", "Financing transmission: cash strain × tighter money", body, "wide")


def sec_themes_health(eng) -> str:
    sh = getattr(eng, "sector_health", None) or {}
    th = sh.get("themes") or []
    if not th:
        return ""
    head = "".join(f'<th class="r">{T(zh.split("：")[0], en.split(":")[0])}</th>' for _k, zh, en, _f in FU.RULES)
    rows = ""
    for t in th:
        cells = ""
        for k, *_ in FU.RULES:
            n, c = t["flags"][k], t["cover"][k]
            tip = "、".join(t["names"][k][:8])
            cells += (f'<td class="r" title="{esc(tip)}">' + (f'<b class="{"dn" if n else ""}">{n}</b><span class="muted small">/{c}</span>' if c else '<span class="muted">—</span>') + "</td>")
        rows += f'<tr><td>{esc(t["theme"])} <span class="muted small">({t["n"]})</span></td>{cells}</tr>'
    defs = "".join(f"<li>{T(zh, en)}</li>" for _k, zh, en, _f in FU.RULES)
    p = sh.get("periods")
    note = T(f"每格＝符合該項的公司數／有揭露該項數據的公司數（滑鼠移上去看是哪幾家）。每家公司都和自己一年前比。財報期間 {p[0] if p else '—'} ～ {p[1] if p else '—'}；"
             "本站追蹤名單，不是全市場。這是規則掃描，不是投資建議。",
             "Cell = companies flagged / companies that disclose the metric (hover for names). Each company vs its own year-ago figures.")
    body = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("族群", "Theme")}</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
            f'<details class="sgx"><summary>{T("六項規則的定義", "Rule definitions")}</summary><ul class="small">{defs}</ul></details><p class="note">{note}</p>')
    return card("族群體質：哪些產業的財報開始出現壓力", "Sector health: where filings show strain", body, "wide")


def sec_company_health(eng) -> str:
    sh = getattr(eng, "sector_health", None) or {}
    rows = [r for r in (sh.get("rows") or []) if r["flags"]]
    if not rows:
        return ""
    rows.sort(key=lambda r: (-len(r["flags"]), r["theme"], r["sym"]))
    tr = "".join(f'<tr><td class="nw"><b>{esc(r["sym"])}</b> <span class="muted small">{esc(r["name"])}</span></td><td class="small">{esc(r["theme"])}</td>'
                 f'<td>{_flagchips(r["flags"])}</td><td class="small muted">{esc(r["m"].get("end") or "")}</td></tr>' for r in rows[:80])
    body = (f'<div class="scroll"><table class="mini srt"><thead><tr><th>{T("公司", "Company")}</th><th>{T("族群", "Theme")}</th>'
            f'<th>{T("出現的壓力", "Strain flags")}</th><th>{T("財報期", "Period")}</th></tr></thead><tbody>{tr}</tbody></table></div>'
            f'<p class="note">{T("只列出至少有一項壓力的公司。壓力不等於會出事：資本支出大的成長期公司本來就可能出現資金缺口。", "Companies with at least one flag. A flag is not a prediction.")}</p>')
    return card("個別公司：財報出現哪些壓力", "Companies: which strain shows in the filings", body, "wide")


def sec_real_economy(eng) -> str:
    re_ = getattr(eng, "real_economy", None) or {}
    if not re_.get("available"):
        return ""
    tone = {"worse": ("⚠️ 轉弱", "⚠️ Weakening", "dn"), "better": ("✅ 轉強", "✅ Strengthening", "up"), "mixed": ("➖ 分歧", "➖ Mixed", "muted")}
    st = {"worse": ("轉弱", "Weaker", "dn"), "better": ("轉強", "Stronger", "up"), "neutral": ("持平", "Steady", "muted")}
    body = ""
    for sec in re_["sectors"]:
        tz, te, tc = tone[sec["tone"]]
        rows = ""
        for r in sec["rows"]:
            unit = "%" if r["kind"] == "pct" else T(" 個百分點", "pp")
            lvl = (T("版權資料", "licensed") if r.get("licensed") else num(r["value"], 2))
            sz, se, sc = st[r["state"]]
            rows += (f'<tr><td>{T(r["zh"], r["en"])}</td><td class="r">{lvl}</td>'
                     f'<td class="r"><b>{num(r["yoy"], 2, sign=True)}{unit}</b></td><td class="r">{num(r.get("pct"), 0)}</td>'
                     f'<td class="{sc}">{T(sz, se)}</td><td class="small muted">{esc(r["date"])}</td></tr>')
        body += (f'<h3>{esc(sec["sector"])} <span class="{tc} small">{T(tz, te)}</span></h3>'
                 f'<div class="scroll"><table class="mini"><thead><tr><th>{T("數據", "Series")}</th><th class="r">{T("最新值", "Latest")}</th>'
                 f'<th class="r">{T("一年變化", "1-year change")}</th><th class="r">{T("近 10 年百分位", "10y pctile")}</th>'
                 f'<th>{T("判讀", "Reading")}</th><th>{T("資料月份", "Data for")}</th></tr></thead><tbody>{rows}</tbody></table></div>')
    note = T("資料來源：FRED（聖路易聯邦準備銀行）彙整的官方統計（商務部、勞工統計局、聯準會等）。一年變化：一般數據看年增率，利率和逾期率看變化幾個百分點。"
             "百分位＝這個一年變化在過去 10 年的位置；只有落在最高或最低的四分之一，才判讀為「轉強／轉弱」，其他算持平。"
             "注意：電力產出創高同時電價上升，代表需求強、供給吃緊（AI 資料中心用電），不等於電力產業沒有瓶頸。"
             "官方數據有公布時間差（月資料約晚 1 個月、季資料約晚 1 季），日期標在每一列。描述現況，不是預測。",
             "Official statistics via FRED. One-year change = growth rate (levels) or pp change (rates). 'Stronger/weaker' only when the "
             "change is in the outer quarter of its 10-year history. Published with a lag. Descriptive, not a forecast.")
    return card("產業真實經濟數據：官方統計怎麼說", "The real economy by sector: official statistics", body + f'<p class="note">{note}</p>', "wide")
