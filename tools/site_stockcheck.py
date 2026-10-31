"""成長估值頁：個股估值體檢（大型美股）。三面體檢、本益比在自己歷史的位置、股價反推成長、歷史本益比情境，先一句白話，細節收進「點開看」。
情境區間是「如果市場用它過去偏低／中位／偏高的倍數」的換算，不叫目標價、不寫上漲空間、不判斷高估低估。"""
from __future__ import annotations

from tools.sitekit import T, card, esc, num

ZH = {"AAPL": "蘋果", "MSFT": "微軟", "NVDA": "輝達", "GOOGL": "Alphabet", "AMZN": "亞馬遜", "META": "Meta", "AVGO": "博通", "TSM": "台積電 ADR",
      "TSLA": "特斯拉", "AMD": "超微", "ASML": "艾司摩爾", "NFLX": "網飛", "JPM": "摩根大通", "GS": "高盛", "MS": "摩根士丹利", "BAC": "美國銀行",
      "WFC": "富國銀行", "V": "Visa", "MA": "萬事達", "LLY": "禮來", "UNH": "聯合健康", "XOM": "埃克森美孚", "WMT": "沃爾瑪", "COST": "好市多"}
GOOD, BAD = {"強", "穩", "高"}, {"衰退", "要留意", "低"}

NOTE_FACES = ("三面體檢（SEC 財報，近 12 個月合計）：成長＝營收年增率（≥20% 強、5～20% 普通、0～5% 慢、負的衰退）；"
              "安全＝三項各算一分：自由現金流（營運現金流 − 資本支出）為正、流動比率 ≥ 1（一年內要還的錢付得出來）、"
              "淨負債 ≤ 2 年營運現金流或手上現金比借款多；3 分穩、2 分普通、1 分以下要留意。銀行的現金流與流動比率意義不同，不評。"
              "獲利＝ROE（淨利 ÷ 平均股東權益，≥20% 高、10～20% 中）；大量買回庫藏股的公司股東權益很小，ROE 會被放大到 100% 以上，甚至無法計算。")
NOTE_PE = ("本益比位置：每週股價 ÷ 當時已公布的近 12 個月每股盈餘（季末後 45 天才算公布，避免偷看未來），現在的本益比高過過去 5 年多少比例的時間。"
           "財報淨利若含一次性收益（例如持有其他公司股票的帳面增值），本益比會看起來特別低，要對照毛利率與營收成長一起看。股票分割前後已對齊。")
NOTE_DCF = ("股價反推成長（反向 DCF）：把企業價值（市值 + 負債 − 現金）當成答案，倒推「未來 10 年自由現金流每年要成長多少、之後每年 2.5%，以 9% 折現」才划得來。"
            "括號是用 8%～10% 折現的範圍，看假設差一點結果差多少。和「過去實際營收年化成長」比：股價要求的比過去快，代表市場預期更好的未來；比過去慢，代表要求不高。"
            "自由現金流被大量投資壓到營運現金流 15% 以下時（例如正在大舉蓋資料中心），反推出來的數字會失真，所以不算。")
NOTE_SCEN = ("歷史本益比情境：過去 5 年本益比的第 25／50／75 百分位（偏低／中位／偏高），乘上每股盈餘（有分析師預估就用預估，否則用近 12 個月），"
             "換算成「如果市場又用這個倍數」對應的股價。這只是歷史倍數的換算，不是預測，公司體質或利率環境改變時，過去的倍數不一定適用。"
             "資料：SEC EDGAR、Yahoo Finance。不是投資建議。")


def _b():
    try:
        from wsb.analytics import stock_check as SC
        from wsb.data import stockinfo as SI
        yf = SI.load_all().get("yf") or {}
        fpe = {s: v.get("fpe") for s, v in yf.items() if v.get("fpe")}
        return SC.build(fpe=fpe)
    except Exception:  # noqa: BLE001
        return None


def _zh(r: dict) -> str:
    return ZH.get(r["sym"], r["sym"])


def vs_past(r: dict):
    ig, c = r.get("ig"), r.get("cagr")
    if ig is None or c is None:
        return None
    return "要求比過去快" if ig > c + 3 else "要求比過去慢" if ig < c - 3 else "和過去差不多"


def band(r: dict):
    s, p = r.get("scen"), r.get("price")
    if not s or not p:
        return None
    lo, mid, hi = s["px"]
    return "低於偏低" if p < lo else "偏低～中位" if p < mid else "中位～偏高" if p <= hi else "高於偏高"


def headline(b: dict) -> str:
    rows = b["rows"]
    rich = [r for r in rows if r.get("pe_pct") is not None and r["pe_pct"] >= 80]
    fast = [r for r in rows if vs_past(r) == "要求比過去快"]
    green = [r for r in rows if r["g_grade"] in GOOD and r["s_grade"] in GOOD and r["p_grade"] in GOOD]
    parts = []
    if rich:
        parts.append("本益比比自己過去 5 年 80% 以上的時間還高：" + "、".join(_zh(r) for r in rich))
    if fast:
        parts.append("股價已經假設的成長比過去實際成長還快：" + "、".join(_zh(r) for r in fast))
    if green:
        parts.append("成長、安全、獲利三面都亮綠燈：" + "、".join(_zh(r) for r in green))
    return f"一句話看懂：追蹤的 {len(rows)} 家大型美股裡，" + ("；".join(parts) if parts else "沒有特別突出的狀況") + "。"


def _g(x: str) -> str:
    c = "up" if x in GOOD else "dn" if x in BAD else ""
    return f'<b class="{c}">{T(x, "")}</b>' if x else "—"


def sec_stock_check(eng) -> str:
    b = _b()
    if not b or not b.get("rows"):
        return ""
    rows = sorted(b["rows"], key=lambda r: (r.get("pe_pct") is None, -(r.get("pe_pct") or 0)))
    f_rows = "".join(
        f'<tr><td>{T(_zh(r), r["sym"])} <span class="tk">{esc(r["sym"])}</span></td>'
        f'<td>{_g(r["g_grade"])} <span class="small">{num(r["rev_yoy"], 0, sign=True, pct=True)}</span></td>'
        f'<td>{_g(r["s_grade"])} <span class="small muted">{"" if r.get("bank") else T("自由現金流 " + (num(r["fcf"] / 1e8, 0) + " 億美元" if r.get("fcf") is not None else "—"), "")}</span></td>'
        f'<td>{_g(r["p_grade"])} <span class="small">ROE {num(r["roe"], 0, pct=True)}{"、毛利率 " + num(r["gm"], 0, pct=True) if r.get("gm") is not None else ""}</span></td>'
        f'<td class="r small muted">{esc(r["end"])}</td></tr>' for r in rows)
    v_rows = ""
    for r in rows:
        s = r.get("scen")
        ig = (f'{num(r["ig"], 0)}%<span class="small muted">（{num(r["ig8"], 0)}～{num(r["ig10"], 0)}%）</span>' if r.get("ig") is not None
              else T("投資期壓低現金流，不算" if r.get("fcf_thin") else "不適用", ""))
        vp = vs_past(r)
        sc = (f'{num(s["px"][0], 0)}／<b>{num(s["px"][1], 0)}</b>／{num(s["px"][2], 0)}<span class="small muted">（{num(s["pe"][0], 0)}／{num(s["pe"][1], 0)}／{num(s["pe"][2], 0)} 倍）</span>'
              if s else "—")
        bd = band(r)
        v_rows += (f'<tr><td>{T(_zh(r), r["sym"])}</td><td class="r">{num(r.get("pe"), 1)}</td>'
                   f'<td class="r"><b class="{"dn" if (r.get("pe_pct") or 0) >= 80 else ""}">{num(r.get("pe_pct"), 0)}</b></td>'
                   f'<td class="r">{ig}</td><td class="r">{num(r.get("cagr"), 0, pct=True)}<span class="small muted">（{r["cagr_yrs"]} 年）</span></td>'
                   f'<td>{T(vp, "") if vp else "—"}</td><td class="r">{sc}</td><td class="r">{num(r.get("price"), 0)}</td><td>{T(bd, "") if bd else "—"}</td></tr>')
    th = lambda zh, en, c="": f'<th{" class=" + c if c else ""}>{T(zh, en)}</th>'  # noqa: E731
    t1 = (f'<div class="scroll"><table class="mini"><thead><tr>{th("公司", "Company")}{th("成長（營收年增）", "Growth")}{th("安全", "Safety")}'
          f'{th("獲利", "Profitability")}{th("財報季", "Quarter", "r")}</tr></thead><tbody>{f_rows}</tbody></table></div>')
    t2 = (f'<div class="scroll"><table class="mini"><thead><tr>{th("公司", "Company")}{th("本益比", "P/E", "r")}{th("5 年百分位", "5y pct", "r")}'
          f'{th("股價隱含成長", "Implied growth", "r")}{th("過去營收年化成長", "Past growth", "r")}{th("比較", "vs past")}'
          f'{th("歷史本益比情境：偏低／中位／偏高", "Historical P/E scenarios", "r")}{th("現價", "Price", "r")}{th("現價落在", "Price sits")}</tr></thead>'
          f'<tbody>{v_rows}</tbody></table></div>')
    skip = [ZH.get(s, s) for s in b.get("skipped") or []]
    sk = f'<p class="small muted">{T("沒列出：" + "、".join(skip) + "（外國公司用 IFRS 申報，SEC 沒有同格式資料；或財報資料暫缺）。", "")}</p>' if skip else ""
    body = (f'<p class="rimp big2"><b>{T(headline(b), "")}</b></p>'
            f'<h3>{T("① 三面體檢：會不會賺、安不安全、還在不在長", "Health check")}</h3>{t1}'
            f'<h3>{T("② ～ ④ 估值：本益比位置、股價反推成長、歷史倍數情境", "Valuation lenses")}</h3>{t2}{sk}'
            f'<details class="sgx"><summary>{T("看每一欄怎麼算、有什麼限制", "Method and limits")}</summary>'
            f'<p class="note">{T(NOTE_FACES, "")}</p><p class="note">{T(NOTE_PE, "")}</p><p class="note">{T(NOTE_DCF, "")}</p><p class="note">{T(NOTE_SCEN, "")}</p></details>')
    return card("個股估值體檢（大型美股）", "Stock health & valuation check", body, "wide")


# ------------------------------------------------------------------ 財報走向判斷
_ARROW = {1: ('<b class="up">↑</b>', "up"), -1: ('<b class="dn">↓</b>', "dn"), 0: ('<span class="muted">→</span>', "")}


def _sig_cell(r: dict, k: str) -> str:
    v, s = r.get(k), r.get("s_" + k)
    if v is None or s is None:
        return '<td class="r muted">—</td>'
    return f'<td class="r">{_ARROW[s][0]} <span class="small">{num(v, 1, sign=True)}</span></td>'


def sec_fund_trend(eng) -> str:
    """財報走向判斷: only the company's own SEC filings — improving / mixed / weakening, next-quarter revenue growth with
    its measured error, what to watch next time, and how this judgment has done historically."""
    from wsb.analytics import fund_trend as F
    try:
        b = F.build()
    except Exception:  # noqa: BLE001
        b = None
    if not b or not b.get("rows"):
        return ""
    rows, m, tr = b["rows"], b.get("model") or {}, b.get("track") or {}
    cnt = {k: [r for r in rows if r["label"] == k] for k in ("up", "flat", "down")}
    nm = lambda r: ZH.get(r["sym"], r["sym"])  # noqa: E731
    lead = (f"一句話看懂：只看各公司自己的財報，追蹤的 {len(rows)} 家裡，本業正在改善的 {len(cnt['up'])} 家"
            + (f"（{'、'.join(nm(r) for r in cnt['up'])}）" if cnt["up"] else "")
            + f"、轉弱的 {len(cnt['down'])} 家" + (f"（{'、'.join(nm(r) for r in cnt['down'])}）" if cnt["down"] else "")
            + f"，其餘 {len(cnt['flat'])} 家訊號互相抵銷。")
    up, dn = tr.get("up") or {}, tr.get("down") or {}
    hist = ""
    if up.get("nm_hit") is not None and dn.get("nm_hit") is not None:
        hist = (f"過去判斷為「改善中」的，兩季後淨利率真的比較高的有 {up['nm_hit']:.0f}%（「轉弱中」只有 {dn['nm_hit']:.0f}%），"
                "代表本業的方向通常會延續一段時間。")
    if up.get("ex") is not None:
        sig = up["ex_lo"] > 0 or up["ex_hi"] < 0
        hist += (f"但股價不一定跟著走：財報公布後半年，「改善中」平均比同名單 {up['ex']:+.1f}%（90% 區間 {up['ex_lo']:+.1f}～{up['ex_hi']:+.1f}%）"
                 + (f"、「轉弱中」{dn['ex']:+.1f}%" if dn.get("ex") is not None else "")
                 + ("，差異統計上明顯。" if sig else "，區間包含 0，看不出穩定的差別——好財報常常早就反映在股價裡。"))
    trs = ""
    for r in rows:
        lab = F.LABEL.get(r["label"], ("訊號不足", "n/a"))
        c = {"up": "up", "down": "dn"}.get(r["label"], "")
        nx = f'{num(r["next_g"], 0, sign=True)}%' if r.get("next_g") is not None else "—"
        trs += (f'<tr><td>{T(nm(r), r["sym"])} <span class="tk">{esc(r["sym"])}</span><div class="small muted">{esc(r["q"])}</div></td>'
                f'<td><b class="{c}">{T(*lab)}</b></td><td class="r">{num(r["g"], 0, sign=True)}%</td>'
                + "".join(_sig_cell(r, k) for k in F.SIGS)
                + f'<td class="r">{num(r["cx_ocf"], 0) + "%" if r.get("cx_ocf") is not None else "—"}</td><td class="r">{nx}</td>'
                f'<td class="small">{esc(r["watch"])}</td></tr>')
    head = (f'<tr><th>{T("公司", "Company")}</th><th>{T("走向", "Trend")}</th><th class="r">{T("營收年增", "Rev YoY")}</th>'
            + "".join(f'<th class="r">{T(*F.SIGS[k])}</th>' for k in F.SIGS)
            + f'<th class="r">{T("資本支出／營運現金流", "Capex / OCF")}</th><th class="r">{T("下一季營收年增", "Next-Q rev")}</th><th>{T("下次財報看什麼", "Watch next")}</th></tr>')
    fc = (f"下一季營收年增：{'用迴歸估算' if m.get('model') else '迴歸模型在走步測試裡沒有比「下一季＝本季」更準，所以直接用本季年增'}，"
          f"過去 {m.get('n_oos', 0)} 次樣本外的誤差約 ±{m.get('rmse', 0):.0f} 個百分點。" if m else "")
    how = ("四個訊號（近 12 個月合計，避免季節性）：營收成長加速＝最近 2 季營收年增率平均減前 2 季；毛利率、淨利率、自由現金流率＝和一年前比（百分點）。"
           f"每個訊號和這家公司自己過去的平常變動比，小於平常的 {F.DEAD:g} 倍當作持平；加總 +2 以上＝改善中、−2 以下＝轉弱中。"
           "銀行沒有毛利率與自由現金流，只用營收與淨利率。" + fc
           + f"歷史成績用 {tr.get('n', 0)} 次過去的判斷（股價部分只有 {up.get('from', '')}～{up.get('to', '')}，財報公布日以季末後 {F.PUB_LAG} 天估），以季為單位重抽 1 萬次算區間。"
           "限制：名單是現在的大型股（倖存者偏差）、家數少、財報是修正後的數字。這是描述與歷史統計，不是股價預測，也不是買賣建議。")
    body = (f'<p><b>{esc(lead)}</b></p>' + (f'<p>{esc(hist)}</p>' if hist else "")
            + f'<div class="scroll"><table class="mini"><thead>{head}</thead><tbody>{trs}</tbody></table></div>'
            + f'<details class="small"><summary>{T("怎麼判斷、歷史成績、限制", "Method, track record, limits")}</summary><p class="note">{esc(how)}</p></details>')
    return card("財報走向判斷：本業正在變好還是變差", "Earnings trend: is the business getting better?", body, "wide")
