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


# ------------------------------------------------------------------ 規則的歷史成績單（1 萬次模擬）
def _rs_cell(x: Dict) -> str:
    if not x:
        return '<td class="r muted">—</td>'
    tip = f'平均 90% 區間 {x["lo"]:+.1f}～{x["hi"]:+.1f}%；上漲比例 {x["win"]:.0f}%；平均持有 {x["days"]:.0f} 天；連做 20 次的中位數 {x["seq_med"]:+.0f}%（最差 5% {x["seq_p5"]:+.0f}%）'
    return (f'<td class="r" title="{esc(tip)}"><b class="{cls(x["avg"])}">{x["avg"]:+.1f}%</b>'
            f'<div class="small muted">{T("最差 5%", "worst 5%")} {x["worst5"]:+.0f}%</div>'
            f'<div class="small">{T("連做 20 次虧", "20-in-a-row loss")} {x["seq_loss"]:.0f}%</div></td>')


def _rs_summary(alls):
    """Span, the stop-vs-hold verdict and the market backdrop, all read from the simulation itself."""
    fr = [a["from"] for _, a in alls if a.get("from")]
    to = [a["to"] for _, a in alls if a.get("to")]
    span = "這段期間"
    if fr and to:
        m = (int(max(to)[:4]) - int(min(fr)[:4])) * 12 + int(max(to)[5:7]) - int(min(fr)[5:7]) + 1
        span = f"約 {m} 個月（{min(fr)}～{max(to)}）"
    lower, smaller, n = 0, 0, 0
    for _, a in alls:
        h, st = a["rules"].get("hold20"), a["rules"].get("stop")
        if h and st:
            n += 1
            lower += st["avg"] <= h["avg"]
            smaller += st["worst5"] > h["worst5"]
    if not n:
        verdict = ""
    else:
        verdict = (f"{n} 個市場裡，失效線停損讓最壞 5% 的虧損縮小的有 {smaller} 個、讓平均報酬變低（或一樣）的有 {lower} 個"
                   + ("：停損主要是在縮小最壞情況，不是提高平均。" if smaller == n and lower == n else "。"))
    bs = [a["rules"]["base"]["avg"] for _, a in alls if a["rules"].get("base")]
    if not bs:
        backdrop = "市場背景未知"
    elif min(bs) > 0:
        backdrop = f"這段期間同名單隨機挑一檔抱 20 天平均都是賺的（{min(bs):+.1f}%～{max(bs):+.1f}%），偏多頭"
    elif max(bs) < 0:
        backdrop = f"這段期間同名單隨機挑一檔抱 20 天平均都是虧的（{min(bs):+.1f}%～{max(bs):+.1f}%），偏空頭"
    else:
        backdrop = f"這段期間各市場有漲有跌（隨機挑一檔平均 {min(bs):+.1f}%～{max(bs):+.1f}%）"
    return span, verdict, backdrop


def sec_rule_sim(eng) -> str:
    from wsb.analytics import rule_sim as RS
    from wsb.analytics.signals import PATTERNS
    sg = getattr(eng, "signals", None) or {}
    if not sg.get("available"):
        return ""
    parts, leads, alls = [], [], []
    for mk, m in sg["markets"].items():
        rs = (m.get("rulesim") or {}).get("patterns") or {}
        if not rs:
            continue
        head = "".join(f'<th class="r">{T(*RS.RULES[r])}</th>' for r in RS.RULES)
        body = ""
        for k in list(PATTERNS) + ["_all"]:
            rec = rs.get(k) or {}
            lab = T("全部型態", "All patterns") if k == "_all" else T(*PATTERNS[k])
            rr = rec.get("rules")
            if not rr:
                body += f'<tr><td>{lab}<div class="small muted">{rec.get("n", 0)} {T("次，樣本不足", "cases, too few")}</div></td>' + '<td class="r muted">—</td>' * len(RS.RULES) + "</tr>"
                continue
            b = rr.get("base") or {}
            body += (f'<tr><td>{lab}<div class="small muted">{rec["n"]} {T("次", "cases")}・{T("隨機挑一檔", "random pick")} {b.get("avg", 0):+.1f}%</div></td>'
                     + "".join(_rs_cell(rr.get(r)) for r in RS.RULES) + "</tr>")
        al = rs.get("_all") or {}
        p = RS.plain(MKT.get(mk, (mk, mk))[0] + "全部型態", al) if al.get("rules") else None
        if p:
            leads.append(f"<li>{esc(p)}</li>")
            alls.append((MKT.get(mk, (mk, mk))[0], al))
        parts.append(f'<h3>{T(*MKT.get(mk, (mk, mk)))}<span class="muted small">（{esc(al.get("from") or "")}～{esc(al.get("to") or "")}）</span></h3>'
                     f'<div class="scroll"><table class="mini"><thead><tr><th>{T("型態", "Pattern")}</th>{head}</tr></thead><tbody>{body}</tbody></table></div>')
    if not parts:
        return ""
    span, verdict, backdrop = _rs_summary(alls)
    lead = T(f"一句話看懂：用過去{span}的資料，把每個型態出現後「照固定規則做」重演一次，再隨機重抽 1 萬次，看平均賺賠、最壞情況，"
             f"和連續照做 20 次最後虧錢的機率。{verdict}",
             f"Each pattern replayed under fixed exit rules over {span}, then resampled 10,000 times.")
    how = T("怎麼看：每格大字＝每次平均報酬（已扣交易成本）；「最差 5%」＝100 次裡最慘的 5 次大概虧多少；「連做 20 次虧」＝照這個規則連續做 20 次（每次全部資金、依序複利），"
            "1 萬次模擬裡最後是虧錢的比例。「隨機挑一檔」＝同一天在同一份名單所有股票的平均（不是單一一檔，所以波動小很多，只拿平均來比）。"
            f"停利＝漲到「起點減失效線」的 {RS.TP_R:g} 倍就出場。滑鼠移到格子上可看 90% 區間與平均持有天數。"
            f"限制：只有{span}資料、{backdrop}（樣本內）；名單是現在的成分股（倖存者偏差：下市的股票不在裡面）；以收盤價成交、沒算跳空滑價；"
            "同一段時間的訊號會一起漲跌，所以以「月份」為單位重抽。這是規則的歷史統計，不是預測，也不是買賣建議。",
            "Cell = average net return; worst 5% = the 5th percentile trade; 20-in-a-row loss = share of 10,000 simulated 20-trade sequences that end negative. "
            f"In-sample ({span}), survivorship bias, close-only fills. Not advice.")
    body = (f'<p><b>{lead}</b></p>' + (f'<ul class="takeaways">{"".join(leads)}</ul>' if leads else "") + "".join(parts)
            + f'<details class="small"><summary>{T("怎麼看、限制", "How to read, limits")}</summary><p class="note">{how}</p></details>')
    return card("規則的歷史成績單：照規則做 1 萬次會怎樣", "Rule record: 10,000 simulated runs", body, "wide")


# ------------------------------------------------------------------ 開盤前 30 秒
def _mv_rows(items, en_=False):
    out = ""
    for x in items:
        ch = x.get("ch")
        px = num(x["px"], 3 if x["t"] in ("^TNX",) else 2)
        if x["t"] in ("^TNX", "^TYX", "^FVX", "^IRX"):         # yields: the move in basis points, not a % of the yield
            from wsb.analytics.premarket import _bp
            bp = _bp(x)
            chg = f'<span class="{cls(bp)}">{num(bp, 1, sign=True)} bp</span>'
        else:
            chg = f'<span class="{cls(ch)}">{num(ch, 2, sign=True, pct=True)}</span>'
        out += (f'<div class="pmi"><span class="muted small">{T(x["zh"], x["en"])}</span><b>{px}</b>{chg}</div>')
    return out


def _rec(r: Dict, zh_band: str, en_band: str) -> str:
    if not r:
        return ""
    a, y = r.get("all") or {}, r.get("y1") or {}
    if a.get("in1") is None or a.get("in2") is None:               # no hit-rate record → say nothing rather than "0%"
        return ""
    yr = (f"（近一年 {y['in1']:.0f}% / {y['in2']:.0f}%；理論值 68% / 95%）。" if y.get("in1") is not None and y.get("in2") is not None
          else "（理論值 68% / 95%）。")
    return T(f"{zh_band}自 {r.get('since', '')[:4]} 年起：收盤落在 ±1σ 內 {a['in1']:.0f}%、±2σ 內 {a['in2']:.0f}%" + yr,
             f"{en_band} since {r.get('since', '')[:4]}: inside ±1σ {a['in1']:.0f}%, ±2σ {a['in2']:.0f}% (theory 68 / 95 %).")


def _takeaways(items) -> str:
    """🔑 今天的重點: the rule readings, most important first (alert → watch → info)."""
    if not items:
        return ""
    ico = {"alert": "🔴", "watch": "🟡", "info": "🔵"}
    lis = "".join(f'<li class="tk-{esc(x["lv"])}">{ico.get(x["lv"], "•")} {T(x["zh"], x["en"])}</li>' for x in items)
    return f'<div class="pmtk"><h4>🔑 {T("今天的重點", "What matters today")}</h4><ul>{lis}</ul></div>'


def sec_premarket(eng) -> str:
    from wsb.analytics import premarket as PM
    try:
        d = PM.build(eng)
    except Exception:  # noqa: BLE001
        return ""
    if not d.get("available"):
        return ""
    # ---- US panel
    ev = "".join(f'<li><b>{esc((e.get("tpe") or "—"))}</b> {T(e["zh"], e["en"])}{"・" + T("含點陣圖", "dots") if e.get("sep") else ""}'
                 f' <span class="muted">{"★" * int(e.get("imp") or 0)}</span></li>' for e in d.get("events", []))
    er = "".join(f'<li><b>{esc(x["sym"])}</b> {esc(x["name"])}・{T({"pre": "盤前", "after": "盤後"}.get(x["time"], "時間未定"), x["time"] or "time n/a")}'
                 + (f'・{T("選擇權預期", "implied")} ±{num(x["mv"], 1)}%' if x.get("mv") else "") + "</li>" for x in d.get("earnings", []))
    rg = d.get("us_range") or {}
    rng = (f'<p>{T("標普今天的預期波動（VIX 換算）", "S&P range priced today (from VIX)")}：<b>±{num(rg["sigma"], 2)}%</b>'
           f'（{T("一個標準差", "1σ")} {num(rg["lo1"], 0)}～{num(rg["hi1"], 0)}；{T("兩個標準差", "2σ")} {num(rg["lo2"], 0)}～{num(rg["hi2"], 0)}，'
           f'{T("基準", "base")} {esc(rg["base_date"][5:])} {T("收盤", "close")} {num(rg["base"], 0)}）</p>'
           f'<p class="small muted">{_rec(rg.get("record") or {}, "這個範圍", "This band")}'
           + ("" if ((rg.get("record") or {}).get("all") or {}).get("in1") is None else
              T("命中率高於理論的 68%，代表 VIX 長期高估實際波動（選擇權賣方收取的風險溢酬）。", "Hit rate above 68%: VIX has overstated realised volatility.")
              if rg["record"]["all"]["in1"] > 68 else
              T("命中率低於理論的 68%，代表實際波動常比 VIX 預期的大。", "Hit rate below 68%: realised moves often exceeded what VIX priced."))
           + '</p>') if rg else ""
    lv = d.get("levels") or {}
    lvl = (f'<p>{T("SPX 選擇權關鍵價位", "SPX option levels")}：{T("Gamma 翻轉", "gamma flip")} <b>{num(lv.get("zero_gamma"), 0)}</b>・'
           f'{T("Call 牆（壓力）", "call wall")} <b>{num(lv.get("call_wall"), 0)}</b>・{T("Put 牆（支撐）", "put wall")} <b>{num(lv.get("put_wall"), 0)}</b>'
           f'<span class="muted small">（{T("現價低於翻轉點時，造市商避險傾向放大波動", "below the flip, dealer hedging tends to amplify moves")}）</span></p>') if lv else ""
    us = (f'<div class="pmp" data-pm="us"><h3>🇺🇸 {T("美股開盤前", "Before the US open")}　<span class="muted small">{T("台北", "Taipei")} {esc(d["us_open_tpe"])}</span></h3>'
          f'{_takeaways(d.get("take_us"))}<div class="pmg">{_mv_rows(d.get("overnight", []))}</div>{rng}{lvl}'
          f'<div class="pm2"><div><h4>{T("今天的數據（台北時間）", "Today’s data (Taipei time)")}</h4><ul class="small">{ev or "<li class=muted>" + (T("沒有重要數據", "No key releases") if d.get("events_ok", True) else T("經濟日曆暫時取不到", "Calendar unavailable")) + "</li>"}</ul></div>'
          f'<div><h4>{T("今天的財報", "Today’s earnings")}</h4><ul class="small">{er or "<li class=muted>" + (T("追蹤名單今天沒有財報", "None in the tracked list") if d.get("earnings_ok", True) else T("財報日曆暫時取不到", "Earnings calendar unavailable")) + "</li>"}</ul></div></div></div>')
    # ---- Taiwan panel
    tr = d.get("tw_range") or {}
    lk = d.get("tw_link") or {}
    tw = (f'<div class="pmp" data-pm="tw"><h3>🇹🇼 {T("台股開盤前", "Before the Taiwan open")}　<span class="muted small">09:00</span></h3>'
          f'{_takeaways(d.get("take_tw"))}<div class="pmg">{_mv_rows(d.get("us_close", []))}</div>'
          + (f'<p>{T("統計推估", "Statistical estimate")}：{esc(lk.get("us_n") or "")} {num(lk.get("us"), 2, sign=True, pct=True)} × Beta {num(lk.get("beta"), 2)} '
             f'→ {esc(lk.get("tw_n") or "")} <b class="{cls(lk.get("implied"))}">{num(lk.get("implied"), 2, sign=True, pct=True)}</b>'
             f'<span class="muted small">（{T("近一年相關係數", "1y corr")} {num(lk.get("corr"), 2)}；{T("只反映美股前一晚，不含台股自己的消息", "US overnight only")}）</span></p>' if lk else "")
          + (f'<p>{T("加權指數的歷史波動範圍（20 日實際波動）", "TAIEX range (20-day realised vol)")}：<b>±{num(tr["sigma"], 2)}%</b>'
             f'（{num(tr["lo1"], 0)}～{num(tr["hi1"], 0)}）</p><p class="small muted">{_rec(tr.get("record") or {}, "這個範圍", "This band")}</p>' if tr else "")
          + '</div>')
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    _tz = _Z("Asia/Taipei")
    lead = int(d.get("lead_min", 90))
    us_from = _dt.fromtimestamp(d["us_open"] - lead * 60, _tz).strftime("%m-%d %H:%M")
    tw_from = _dt.fromtimestamp(d["tw_open"] - lead * 60, _tz).strftime("%m-%d %H:%M")
    note = T("不預測漲跌方向：這裡只整理隔夜變化、今天的時程，以及市場自己定價的波動範圍，並公開這個範圍過去準不準。"
             "「今天的重點」是固定規則對這些數字的解讀（例如跌幅和該指數平常單日波動相比、股債金同步的組合代表什麼），🔴 需要留意、🟡 值得注意、🔵 背景。"
             f"開盤前 {lead} 分鐘起只顯示即將開盤的市場——下一次：美股 {us_from}、台股 {tw_from}（台北時間，已排除週末與交易所休市日，美國夏令／冬令時間自動換算）；"
             f"經濟數據列出重要度 {'★' * int(d.get('min_imp', 2))} 以上；其他時間美股、台股兩邊都顯示。資料每約 20 分鐘更新，期貨等報價約延遲 15 分鐘。",
             "No direction call — overnight changes, today’s schedule and the range the market prices, with that range’s track record. "
             f"From {lead} min before each open only that market is shown (next: US {us_from}, Taiwan {tw_from} Taipei; weekends and exchange holidays skipped).")
    body = (f'<details class="pm" open id="pmbox" data-us="{d["us_open"]}" data-tw="{d["tw_open"]}" data-lead="{lead}" data-after="{int(d.get("after_min", 30))}"><summary><b id="pmhead">{T("隔夜變化與今天時程", "Overnight and today")}</b> '
            f'<span class="muted small" id="pmcount"></span></summary>{us}{tw}'
            f'<div class="pmp" id="pmmine" style="display:none"></div><p class="note">{note}　{T("更新", "Built")} {esc(d["built"])}</p></details>')
    return f'<section class="card wide pmcard"><h2>{T("盤前整理", "Pre-open roundup")}</h2>{body}</section>'


# ------------------------------------------------------------------ 指數 vs 個股
def sec_index_vs_stocks(eng) -> str:
    d = getattr(eng, "dispersion", None) or {}
    if not d.get("available"):
        return ""
    MKN = {"us": ("美股（本站追蹤名單）", "US (tracked list)", "標普 500", "S&P 500"), "tw": ("台股（本站追蹤名單）", "Taiwan (tracked list)", "加權指數", "TAIEX")}
    blocks = ""
    for mk in ("us", "tw"):
        g = d.get(mk)
        if not g:
            continue
        zh, en, iz, ie = MKN[mk]
        gp = f'{T("落差位於", "gap at")} {num(g.get("gap_pct"), 0)} {T("百分位（自", "pctile (since")} {esc((g.get("gap_since") or "")[:7])}）' if g.get("gap_pct") is not None else ""
        blocks += (f'<h3>{T(zh, en)}　<span class="muted small">{g["n"]} {T("檔", "stocks")}・{esc(g["asof"])}</span></h3>'
                   f'<div class="kv"><div><span class="muted">{T(iz + " 離 52 週高點", ie + " from 52w high")}</span><b class="{cls(g["index_dd"])}">{num(g["index_dd"], 1, sign=True, pct=True)}</b></div>'
                   f'<div><span class="muted">{T("中位數個股離自己的高點", "Median stock from its high")}</span><b class="{cls(g["median_dd"])}">{num(g["median_dd"], 1, sign=True, pct=True)}</b></div>'
                   f'<div><span class="muted">{T("跌逾一成／兩成的比例", "Share ≥10% / ≥20% down")}</span><b>{num(g["below10"], 0)}% / {num(g["below20"], 0)}%</b></div>'
                   f'<div><span class="muted">{T("近 3 個月贏過指數的比例", "Beat the index, 3m")}</span><b>{num(g["beat_3m"], 0)}%</b></div></div>'
                   f'<p class="small muted">{T("近 1／3 個月：指數", "1m / 3m: index")} {num(g["idx_1m"], 1, sign=True, pct=True)}／{num(g["idx_3m"], 1, sign=True, pct=True)}，'
                   f'{T("中位數個股", "median stock")} {num(g["med_1m"], 1, sign=True, pct=True)}／{num(g["med_3m"], 1, sign=True, pct=True)}。{gp}</p>')
    ew = d.get("ew") or {}
    if ew:
        blocks += (f'<p>{T("等權重標普（RSP）相對市值加權（SPY）", "Equal-weight (RSP) vs cap-weight (SPY)")}：{T("近 1 個月", "1m")} <b class="{cls(ew["rel_1m"])}">{num(ew["rel_1m"], 1, sign=True)}</b>、'
                   f'{T("近 3 個月", "3m")} <b class="{cls(ew["rel_3m"])}">{num(ew["rel_3m"], 1, sign=True)}</b> {T("個百分點", "pp")}</p>')
    cb = d.get("cboe") or {}
    if cb:
        lab = {"COR1M": ("隱含相關性（1 個月）", "Implied correlation (1m)"), "COR3M": ("隱含相關性（3 個月）", "Implied correlation (3m)"),
               "DSPX": ("S&P 500 分散度指數", "S&P 500 Dispersion Index")}
        rows = "".join(f'<tr><td>{T(*lab.get(k, (k, k)))}</td><td class="r"><b>{num(v["now"], 2)}</b></td><td class="r">{num(v.get("pct"), 0)}</td>'
                       f'<td class="r">{num(v.get("pct_3y"), 0)}</td><td class="small muted">{esc(v.get("since") or "")}–{esc((v.get("asof") or "")[5:])}</td></tr>'
                       for k, v in cb.items())
        blocks += (f'<table class="mini"><thead><tr><th>{T("Cboe 指數", "Cboe index")}</th><th class="r">{T("目前", "Now")}</th>'
                   f'<th class="r">{T("歷史百分位", "Pctile")}</th><th class="r">{T("近 3 年百分位", "3y pctile")}</th><th>{T("資料期間", "Range")}</th></tr></thead><tbody>{rows}</tbody></table>')
    rd = d.get("readings") or []
    if rd:
        blocks += f'<h3>{T("數據怎麼說", "What the data says")}</h3><ul>' + "".join(f"<li>{T(x['zh'], x['en'])}</li>" for x in rd) + "</ul>"
    note = T("「中位數個股」是本站追蹤名單（不是全部上市公司）裡排在正中間的那一檔；落差＝中位數個股離高點 − 指數離高點，越負代表越少數股票在撐指數。"
             "隱含相關性：選擇權市場預期成分股之間會不會一起動（越低＝越各走各的）；分散度指數：預期個股之間報酬差距有多大（越高＝差距越大）。"
             "資料來源：Cboe 公開的指數歷史檔、本站股價資料。描述現況，不是預測。",
             "Median stock = the middle of our tracked list, not the whole market. Implied correlation: how much stocks are expected to move together; "
             "dispersion: how far apart their returns are expected to be. Source: Cboe public index history. Descriptive, not a forecast.")
    return card("指數 vs 個股：為什麼指數沒跌、帳戶在跌", "Index vs stocks: why the index holds while accounts fall", blocks + f'<p class="note">{note}</p>', "wide")


# ------------------------------------------------------------------ 華爾街機構觀點（背景）
def sec_street(eng) -> str:
    st = getattr(eng, "street", None) or {}
    views, pos = st.get("views") or {}, st.get("pos") or {}
    if not views and not pos:
        return ""
    body = ""
    if pos:
        rows = ""
        for code, p in pos.items():
            rows += (f'<tr><td>{T(p["zh"], p["en"])}</td>'
                     f'<td class="r"><b class="{cls(p["am"])}">{num(p["am"], 1, sign=True)}%</b><div class="small muted">{T("近 3 年第", "3y pctile")} {num(p["am_pct"], 0)} {T("百分位", "")}・{T("週變化", "wk")} {num(p["am_chg"], 1, sign=True)}</div></td>'
                     f'<td class="r"><b class="{cls(p["lm"])}">{num(p["lm"], 1, sign=True)}%</b><div class="small muted">{T("近 3 年第", "3y pctile")} {num(p["lm_pct"], 0)} {T("百分位", "")}・{T("週變化", "wk")} {num(p["lm_chg"], 1, sign=True)}</div></td>'
                     f'<td class="small muted">{esc(p["asof"])}</td></tr>')
        unit = T("單位：占未平倉量的百分比（多單減空單）。資產管理機構多半是長期多頭，槓桿資金常拿期貨做避險或套利，所以淨空單不一定代表看空。每週二的部位、週五公布。",
                 "Net long minus short as % of open interest. Leveraged funds often hold shorts as hedges or basis trades. Tuesday positions, published Friday.")
        body += (f'<h3>{T("機構實際怎麼押（CFTC 期貨部位）", "How institutions are positioned (CFTC futures)")}</h3>'
                 f'<table class="mini"><thead><tr><th>{T("合約", "Contract")}</th><th class="r">{T("資產管理機構淨部位", "Asset managers, net")}</th>'
                 f'<th class="r">{T("避險基金等槓桿資金淨部位", "Leveraged funds, net")}</th><th>{T("資料日", "As of")}</th></tr></thead><tbody>{rows}</tbody></table>'
                 f'<p class="small muted">{unit}</p>')
    if views:
        body += f'<h3>{T("機構最近公開的觀點", "Latest public commentary")}</h3>'
        for k in ("ms", "gs", "br"):
            v = views.get(k)
            if not v:
                continue
            items = "".join(f'<li><span class="muted small">{esc(i.get("date") or "")}</span> '
                            + (f'<a href="{esc(i["link"])}" target="_blank" rel="noopener">{esc(i["title"])}</a>' if i.get("link") else esc(i["title"]))
                            + "</li>" for i in v.get("items", []))
            body += f'<p><b><a href="{esc(v["home"])}" target="_blank" rel="noopener">{T(v["zh"], v["en"])}</a></b></p><ul class="small">{items}</ul>'
    note = T("背景資訊：只列各機構自己公開發布的標題、日期與連結（不轉載內容），點進去看原文；這些觀點不進入本站任何風險分數或訊號。"
             "期貨部位來自 CFTC（美國商品期貨交易委員會）公開的 Traders in Financial Futures 週報。完整的券商研究報告屬付費內容，本站不取得也不轉載。",
             "Background only: titles, dates and links to each firm’s own public publications; never used in any score. Positions: CFTC TFF weekly report.")
    return card("華爾街機構觀點（背景）", "What Wall Street firms are saying (background)", body + f'<p class="note">{note}</p>', "wide")


# ------------------------------------------------------------------ 新聞整理（背景）
def sec_news_digest(eng) -> str:
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    from wsb.data import news_digest as ND
    nd = getattr(eng, "news_digest", None) or {}
    items, zh = nd.get("items") or [], nd.get("zh") or {}
    if not items:
        return ""
    tz = _Z("Asia/Taipei")

    def li(i):
        when = _dt.fromtimestamp(i["ts"], tz).strftime("%m-%d %H:%M") if i.get("ts") else ""
        from tools.sitekit import guard_safe
        t = guard_safe(zh[i["title"]]) if zh.get(i["title"]) else None
        title = (f'{esc(t)} <span class="muted small">{esc(i["title"])}</span>' if t else esc(i["title"]))
        a = f'<a href="{esc(i["link"])}" target="_blank" rel="noopener">{title}</a>' if i.get("link") else title
        tags = "".join(f'<span class="pill">{esc(s)}</span> ' for s in i.get("syms") or [])
        return f'<li data-syms="{esc(",".join(i.get("syms") or []))}"><span class="muted small">{when}</span> {tags}{a}</li>'
    groups = ""
    for k, tzh, ten, _rx in ND.TOPICS:
        g = [i for i in items if k in (i.get("topics") or [])][:8]
        if g:
            groups += f'<h3>{T(tzh, ten)}</h3><ul class="small nd">{"".join(li(i) for i in g)}</ul>'
    other = [i for i in items if (i.get("topics") or []) == ["other"]][:8]
    if other:
        groups += f'<h3>{T("其他（提到追蹤名單公司）", "Other (tracked companies)")}</h3><ul class="small nd">{"".join(li(i) for i in other)}</ul>'
    mine = (f'<div id="ndmine" style="display:none"><h3>🔒 {T("和你的持股有關（只在這個瀏覽器比對）", "About your holdings (matched in this browser only)")}</h3>'
            f'<ul class="small nd"></ul></div>')
    upd = _dt.fromtimestamp(nd.get("ts", 0), tz).strftime("%m-%d %H:%M") if nd.get("ts") else "—"
    note = T(f"來源：Business Insider 公開的新聞訂閱（主訂閱只列免費文章；另含市場新聞）。只列標題、時間與連結，點進去看原文；中文標題由 AI 翻譯，可能有誤，英文原標題附在後面。"
             f"依標題關鍵字分類；同一則可能出現在多個分類。最後更新 {upd} 台北。新聞只是背景，不進入本站任何風險分數或訊號。",
             "Business Insider public feeds; titles, times and links only; Chinese titles are AI translations. Background only.")
    return card("新聞整理（Business Insider・背景）", "News digest (Business Insider, background)",
                f'<div id="nddigest">{mine}{groups}</div><p class="note">{note}</p>', "wide")
