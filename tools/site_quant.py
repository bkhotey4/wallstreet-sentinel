"""Site sections for the institutional-style layer: style-factor returns, revenue exposure (SEC), signal scorecard."""
from __future__ import annotations

from typing import Dict

from tools.sitekit import T, card, cls, esc, num

VERDICT = {"works": ("✅ 有效", "✅ Works", "up"), "backfires": ("⚠️ 反效果", "⚠️ Backfires", "dn"),
           "unclear": ("➖ 沒有明顯優勢", "➖ No clear edge", "muted"), "insufficient": ("⏳ 證據不足", "⏳ Not enough evidence", "muted")}
MKT = {"us": ("美股", "US"), "tw": ("台股", "Taiwan"), "hk": ("港股", "Hong Kong")}


# ------------------------------------------------------------------ 風格因子報酬
def sec_factor_returns(eng) -> str:
    f = getattr(eng, "factors", None) or {}
    if not f.get("available"):
        return ""
    rows = []
    for k in f["keys"]:
        zh, en = ("利率（10 年期殖利率變動）", "Rates (10-year yield change)") if k == "rate" else f["labels"][k]
        d, w = f["today"].get(k), f["week"].get(k)
        if k == "rate":                                           # yield change, shown in basis points
            dt, wt = (f"{d * 100:+.1f} bp" if d is not None else "—"), (f"{w * 100:+.1f} bp" if w is not None else "—")
            dc, wc = "", ""
        else:
            dt, wt = num(d * 100 if d is not None else None, 2, sign=True, pct=True), num(w * 100 if w is not None else None, 2, sign=True, pct=True)
            dc, wc = cls(d), cls(w)
        rows.append(f'<tr><td>{T(zh, en)}</td><td class="r {dc}">{dt}</td><td class="r {wc}">{wt}</td></tr>')
    note = T("因子＝用 ETF 組成的「多空組合」：小型股＝IWM−SPY、價值＝VTV−VUG、動能＝MTUM−SPY、品質＝QUAL−SPY、低波動＝USMV−SPY、"
             "半導體＝SMH−SPY；利率＝10 年期殖利率變動。正值代表這種風格今天贏過大盤。「我的持股」頁會用這些因子拆解你的組合曝險與今天的漲跌來源。",
             "Factors are ETF long/short pairs (size IWM−SPY, value VTV−VUG, momentum MTUM−SPY, quality QUAL−SPY, low vol USMV−SPY, "
             "semis SMH−SPY; rates = change in the 10-year yield). Positive = that style beat the market.")
    body = (f'<table class="mini"><thead><tr><th>{T("因子", "Factor")}</th><th class="r">{T("最近一日", "Last day")}</th>'
            f'<th class="r">{T("近 5 日", "5 days")}</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
            f'<p class="note">{note}　{T("資料日", "As of")} {esc(f["asof"])}・{f["n_sym"]} {T("檔有因子曝險", "symbols with loadings")}</p>')
    return card("風格因子報酬：今天哪種股票贏", "Style factors: which kind of stock won", body)


# ------------------------------------------------------------------ 營收曝險（SEC 年報）
def sec_rev_exposure(eng) -> str:
    seg = getattr(eng, "segments", None) or {}
    if not seg:
        return ""
    from wsb.data.stocks import universe
    names = ((universe().get("us") or {}).get("symbols") or {})
    rows = []
    for s, r in sorted(seg.items(), key=lambda kv: -((kv[1].get("china") or 0) + (kv[1].get("taiwan") or 0))):
        if s not in names:
            continue                                             # public table: the curated universe only
        cust = r.get("cust") or []
        top = f'{esc(cust[0][1])} {cust[0][2] * 100:.0f}%' if cust else "—"
        rows.append(f'<tr><td class="nw"><b>{esc(names[s][0])}</b><span class="tk">{esc(s)}</span></td>'
                    + "".join(f'<td class="r">{(num(r[k] * 100, 0) + "%") if r.get(k) is not None else "—"}</td>' for k in ("china", "taiwan", "us"))
                    + f'<td class="r">{top}</td><td class="small muted">{esc(r.get("form") or "")} {esc((r.get("period") or "")[:7])}</td></tr>')
    if not rows:
        return ""
    note = T("來源：各公司最新一份年報（10-K／20-F）的 XBRL 標籤。「—」＝年報沒有單獨揭露這個地區（例如只寫「北美」）或客戶，不代表 0%。"
             "客戶名稱多半匿名（Customer A／Largest customer）。地區是「客戶所在地」，不是最終用途：賣給台積電的設備算台灣。"
             "中國比重高＝出口管制、地緣政治的直接曝險；單一客戶比重高＝那家客戶縮減支出時的集中風險。每次建置補抓幾家，約一天內補齊。",
             "From each company's latest 10-K / 20-F XBRL. '—' = not broken out (not 0 %). Regions are where customers are billed.")
    body = (f'<div class="scroll"><table class="mini srt"><thead><tr><th>{T("公司", "Company")}</th><th class="r">{T("中國", "China")}</th>'
            f'<th class="r">{T("台灣", "Taiwan")}</th><th class="r">{T("美國", "US")}</th><th class="r">{T("最大客戶", "Top customer")}</th>'
            f'<th>{T("年報", "Report")}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div><p class="note">{note}</p>')
    return card("營收曝險：錢從哪裡來", "Revenue exposure: where the money comes from", body, "wide")


# ------------------------------------------------------------------ 訊號成績單
def _vcell(v: Dict, direction: int = 1) -> str:
    if not v or not v.get("n"):
        return '<td class="r muted">—</td>'
    zh, en, c = VERDICT.get(v["verdict"], VERDICT["insufficient"])
    rng = f'{num(v.get("lo"), 1)}～{num(v.get("hi"), 1)}' if v.get("lo") is not None else "—"
    tip = f'{v["n"]} 次訊號，約 {v.get("n_eff", "—")} 個獨立期間；90% 區間 {rng} 個百分點'
    return (f'<td class="r" title="{esc(tip)}"><b class="{cls(v.get("mean"))}">{num(v.get("mean"), 2, sign=True)}</b>'
            f'<div class="small {c}">{T(zh, en)}</div></td>')


def sec_signal_scorecard(eng) -> str:
    from wsb.analytics import signal_ledger as SL
    from wsb.analytics.signals import PATTERNS
    sg = getattr(eng, "signals", None) or {}
    if not sg.get("available"):
        return ""
    parts = []
    for mk, m in sg["markets"].items():
        rp = m.get("replay") or {}
        hs = [h for h in ("5", "20", "60") if h in rp]
        if not hs:
            continue
        head = "".join(f'<th class="r">{T(f"{h} 日", f"{h}d")}</th>' for h in hs)
        body = ""
        for k in list(PATTERNS) + ["_all"]:
            lab = T("全部訊號", "All signals") if k == "_all" else T(*PATTERNS[k])
            body += f'<tr><td>{lab}</td>' + "".join(_vcell(rp[h].get(k) or {}) for h in hs) + "</tr>"
        lg = m.get("ledger") or {}
        live = ""
        if lg.get("logged"):
            bykind = "、".join(f'{T(SL.KINDS[k][0], SL.KINDS[k][1])} {n}' for k, n in (lg.get("by_kind") or {}).items() if n)
            mat = {h: sum((((lg.get("h") or {}).get(h) or {}).get(k) or {}).get("n", 0) for k in SL.KINDS) for h in hs}
            live = (f'<p class="small">{T("實盤紀錄（樣本外）", "Live record (out-of-sample)")}：{T("自", "since")} {esc(lg.get("since") or "—")} '
                    f'{T("已記錄", "logged")} {lg["logged"]} {T("個訊號", "signals")}（{bykind}）；'
                    + "、".join(f'{T(f"滿 {h} 日", f"{h}d matured")} {n}' for h, n in mat.items()) + "。</p>")
            if any(mat.values()):
                lb = "".join(f'<tr><td>{T(SL.KINDS[k][0], SL.KINDS[k][1])}</td>'
                             + "".join(_vcell((((lg.get("h") or {}).get(h) or {}).get(k)) or {}) for h in hs) + "</tr>" for k in SL.KINDS)
                live += (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("實盤訊號", "Live signal")}</th>{head}</tr></thead>'
                         f'<tbody>{lb}</tbody></table></div>')
        parts.append(f'<h3>{T(*MKT.get(mk, (mk, mk)))}</h3>{live}<div class="scroll"><table class="mini"><thead><tr><th>{T("型態（歷史回放）", "Pattern (replay)")}</th>{head}</tr></thead>'
                     f'<tbody>{body}</tbody></table></div>')
    if not parts:
        return ""
    note = T("數字＝訊號出現後 N 個交易日的報酬，減去「同一天在同一份名單隨機挑一檔」的平均報酬，再扣來回交易成本（美股 0.10%、台股 0.45%、港股 0.30%），單位：百分點。"
             "同一天的訊號會一起漲跌、而且持有期間重疊，所以信賴區間是用「每天平均」並把每個持有期間大約算成一次獨立觀察，比單純算筆數保守很多。"
             "✅＝90% 區間整段在 0 以上；⚠️＝整段在 0 以下；➖＝區間跨過 0；⏳＝獨立樣本太少。"
             "「歷史回放」是同一套規則套用到過去約兩年，規則雖然沒有用這段資料調參，仍算樣本內；"
             "「實盤紀錄」從上線當天開始逐筆記錄，持有期滿才評分，是真正的樣本外。這是規則的成績單，不是買賣建議。",
             "Excess return over a random pick from the same list on the same day, net of round-trip cost, in percentage points. "
             "Intervals use daily averages with ~one independent observation per holding period. Replay = in-sample; live record = out-of-sample.")
    return card("訊號成績單：有沒有贏過隨機亂挑", "Signal scorecard: better than a random pick?", "".join(parts) + f'<p class="note">{note}</p>', "wide")
