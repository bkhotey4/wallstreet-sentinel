"""利率衝擊雷達 card — Treasury yields → AI / tech stocks, with plain-language readings from fixed rules."""
from __future__ import annotations

from typing import Dict, List

from tools.sitekit import T, card, cls, esc, num


def _dist(w: Dict) -> str:
    """Yields: distance in bp; everything else: % of the line."""
    if w["t"] in ("^TNX", "^TYX"):
        return f"{abs(w['dist']) * 100:.0f}bp"
    return f"{abs(w['dist_pct']):.1f}%"


def readings(r: Dict) -> List[Dict]:
    """🔑 what the numbers add up to (descriptive; thresholds stated in the note)."""
    out: List[Dict] = []
    d = r.get("decomp") or {}
    if d.get("d_nominal") is not None and abs(d["d_nominal"]) >= 0.25:
        drv = d.get("driver")
        why = {"real": ("實質利率（投資人要求的真實報酬）", "real yields"), "breakeven": ("通膨預期", "inflation expectations")}.get(drv, ("", ""))
        out.append({"lv": "alert" if d["d_nominal"] > 0 else "info",
                    "zh": f"10 年期殖利率 3 個月{'上升' if d['d_nominal'] > 0 else '下降'} {abs(d['d_nominal']) * 100:.0f}bp，主要來自{why[0]}"
                          + (f"（{d['d_real'] * 100:+.0f}bp）；通膨預期只變動 {d['d_breakeven'] * 100:+.0f}bp" if drv == "real" else "")
                          + "。",
                    "en": f"10-year {d['d_nominal'] * 100:+.0f}bp in 3 months, driven by {why[1]}."})
    for b in r.get("beta") or []:
        if b["t"] in ("^SOX", "QQQ") and b.get("beta_pct") is not None and b["beta_pct"] <= 10 and b["beta"] < 0:
            out.append({"lv": "alert", "zh": f"{b['zh']}對殖利率特別敏感：近半年殖利率每升 10bp，平均{'跌' if b['beta'] < 0 else '漲'} {abs(b['beta']):.2f}%，"
                                             f"敏感度在自己歷史最極端的 {max(1, round(b['beta_pct']))}%——現在利率的每一次跳動，都會直接打到這類股票。",
                        "en": f"{b['en']} is unusually rate-sensitive: {b['beta']:+.2f}% per +10bp (bottom {b['beta_pct']:.0f}% of its history)."})
            break
    g = r.get("gap") or {}
    if g.get("erp") is not None and g.get("erp_pct") is not None and g["erp_pct"] <= 10:
        out.append({"lv": "alert", "zh": f"股票風險溢酬只剩 {g['erp']:.2f} 個百分點（企業盈餘殖利率 {g['ey']:.2f}% − 10 年實質利率），是 {g['erp_since']} 年有資料以來第 {g['erp_pct']:.0f} 百分位："
                                         "買股票比買抗通膨公債多拿的報酬，在這段資料裡幾乎是最少——估值對利率上升的緩衝很薄。",
                    "en": f"Equity risk premium {g['erp']:.2f}pp — {g['erp_pct']:.0f}th percentile since {g['erp_since']}."})
    if g.get("gap") is not None and g["gap"] < 0 and g.get("y1987") is not None:
        out.append({"lv": "watch", "zh": f"「像 1987」的量化檢查：10 年期殖利率（{g['nominal']:.2f}%）高於股票盈餘殖利率（{g['ey']:.2f}%），差距 {g['gap']:+.2f} 個百分點，方向和 1987 年一樣；"
                                         f"但 1987 年 7 月的差距是 {g['y1987']:+.2f}、2000 年初是 {g.get('y2000', 0):+.2f}，現在小得多。"
                                         f"而且 1962 年以來有 {g.get('neg_share', 0):.0f}% 的季度差距都是負的，所以它代表「股票相對公債偏貴」，不是崩盤的時間點。",
                    "en": f"'Like 1987' check: bond yield above the earnings yield ({g['gap']:+.2f}pp) — same sign as 1987 ({g['y1987']:+.2f}) but far smaller; "
                          f"negative in {g.get('neg_share', 0):.0f}% of quarters since 1962, so it is a valuation statement, not timing."})
    near = [w for w in (r.get("watch") or []) if not w["hit"] and w["dist_pct"] <= 5]
    hit = [w for w in (r.get("watch") or []) if w["hit"]]
    if hit:
        out.append({"lv": "alert", "zh": "已觸及的警戒線：" + "、".join(f"{w['zh']} {w['now']:,.2f}（線 {w['line']}）" for w in hit) + "。",
                    "en": "Lines crossed: " + ", ".join(w["en"] for w in hit)})
    if near:
        out.append({"lv": "watch", "zh": "接近警戒線（5% 以內）：" + "、".join(f"{w['zh']} {w['now']:,.2f}，距離 {_dist(w)}" for w in near) + "。",
                    "en": "Near a watch line: " + ", ".join(w["en"] for w in near)})
    f = r.get("fiscal") or {}
    if f.get("pct") is not None and f["pct"] >= 70:
        out.append({"lv": "watch", "zh": f"聯邦利息支出已占稅收 {f['ratio']:.1f}%（{f['since']} 年以來第 {f['pct']:.0f} 百分位；歷史最高 {f['max']:.0f}% 在 {f['max_q']} 年）：利息支出越高，赤字越大、需要發行的公債就越多，市場要消化的供給也越多。",
                    "en": f"Federal interest = {f['ratio']:.1f}% of tax receipts ({f['pct']:.0f}th pctile since {f['since']})."})
    order = {"alert": 0, "watch": 1, "info": 2}
    return sorted(out, key=lambda x: order[x["lv"]])


def sec_rates_radar(eng) -> str:
    r = getattr(eng, "rates_radar", None) or {}
    if not r.get("available"):
        return ""
    from tools.site_quant import _takeaways
    body = _takeaways(readings(r))
    d = r.get("decomp") or {}
    if d:
        def row(zh, en, v, dv):
            return (f'<tr><td>{T(zh, en)}</td><td class="r"><b>{num(v, 2)}%</b></td>'
                    f'<td class="r {cls(dv)}">{(num(dv * 100, 0, sign=True) + " bp") if dv is not None else "—"}</td></tr>')
        body += (f'<h3>{T("1. 殖利率為什麼漲", "1. Why yields moved")}</h3><table class="mini"><thead><tr><th></th><th class="r">{T("目前", "Now")}</th>'
                 f'<th class="r">{T("3 個月變化", "3-month change")}</th></tr></thead><tbody>'
                 + row("10 年期名目殖利率", "10-year nominal", d.get("nominal"), d.get("d_nominal"))
                 + row("＝ 實質利率", "= real yield", d.get("real"), d.get("d_real"))
                 + row("＋ 通膨預期", "+ breakeven inflation", d.get("breakeven"), d.get("d_breakeven"))
                 + row("期限溢酬（長債的額外報酬要求）", "Term premium", d.get("term_premium"), d.get("d_term_premium"))
                 + f'</tbody></table><p class="small muted">{T("資料日", "As of")} {esc(d.get("date", ""))}</p>')
    g = r.get("gap") or {}
    if g:
        body += (f'<h3>{T("2. 股票 vs 公債（含 1987 對照）", "2. Stocks vs bonds (with 1987)")}</h3><div class="kv">'
                 f'<div><span class="muted">{T("企業盈餘殖利率", "Earnings yield")}</span><b>{num(g["ey"], 2)}%</b></div>'
                 f'<div><span class="muted">{T("− 10 年期殖利率", "− 10-year yield")}</span><b class="{cls(g["gap"])}">{num(g["gap"], 2, sign=True)}</b></div>'
                 + (f'<div><span class="muted">{T("股票風險溢酬（− 實質利率）", "Equity risk premium")}</span><b>{num(g["erp"], 2)}</b>'
                    f'<span class="small muted">{T("第", "pctile")} {num(g.get("erp_pct"), 0)} {T("百分位", "")}</span></div>' if g.get("erp") is not None else "")
                 + f'<div><span class="muted">{T("1987 年 7 月", "Jul 1987")}</span><b>{num(g.get("y1987"), 2, sign=True)}</b></div>'
                 f'<div><span class="muted">{T("2000 年初", "Early 2000")}</span><b>{num(g.get("y2000"), 2, sign=True)}</b></div></div>'
                 f'<p class="small muted">{T("盈餘殖利率＝非金融企業稅後盈餘 ÷ 其股票市值（官方 Z.1 與 BEA 季資料，市值用標普漲跌推到今天）", "Earnings yield = non-financial corporate after-tax profits ÷ their equity value (Z.1/BEA, rolled forward with the S&P)")}'
                 f'・{T("盈餘季度", "profits quarter")} {esc(g.get("ey_q", ""))}</p>')
    bt = r.get("beta") or []
    if bt:
        rows = "".join(f'<tr><td>{T(b["zh"], b["en"])}</td><td class="r"><b class="{cls(b["beta"])}">{num(b["beta"], 2, sign=True)}%</b></td>'
                       f'<td class="r">{num(b.get("beta_pct"), 0)}</td><td class="r">{num(b.get("corr"), 2)}</td></tr>' for b in bt)
        body += (f'<h3>{T("3. 科技股對利率有多敏感", "3. How rate-sensitive tech is")}</h3><table class="mini"><thead><tr><th></th>'
                 f'<th class="r">{T("殖利率每 +10bp", "per +10bp")}</th><th class="r">{T("歷史百分位", "pctile")}</th><th class="r">{T("相關係數", "corr")}</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table>')
    wl = r.get("watch") or []
    if wl:
        rows = "".join(f'<tr><td>{T(w["zh"], w["en"])}</td><td class="r"><b>{num(w["now"], 2)}</b></td><td class="r">{w["line"]}（{T("向上" if w["side"] == "above" else "向下", w["side"])}）</td>'
                       f'<td class="r {"dn" if w["hit"] else ""}">{T("已觸及", "crossed") if w["hit"] else _dist(w)}</td></tr>' for w in wl)
        body += (f'<h3>{T("4. 警戒線距離", "4. Distance to watch lines")}</h3><table class="mini"><thead><tr><th></th><th class="r">{T("目前", "Now")}</th>'
                 f'<th class="r">{T("警戒線", "Line")}</th><th class="r">{T("距離", "Distance")}</th></tr></thead><tbody>{rows}</tbody></table>'
                 f'<p class="small muted">{T("MOVE 125、IXG 125 是財經媒體引用的警戒線；10 年 5.25%、30 年 5.5% 是本站自訂的整數參考線。全部可以在 settings.yaml 的 rates_radar.watch 調整。這裡用即時報價，上方第 1 項用 FRED 的收盤資料，所以殖利率可能差幾個 bp。", "MOVE/IXG lines are those cited in the media; the yield lines are round-number references set here (editable).")}</p>')
    f = r.get("fiscal") or {}
    if f:
        body += (f'<h3>{T("5. 美國財政壓力", "5. US fiscal strain")}</h3><div class="kv">'
                 f'<div><span class="muted">{T("利息支出 ÷ 稅收", "Interest ÷ tax receipts")}</span><b>{num(f["ratio"], 1)}%</b><span class="small muted">{T("一年前", "1y ago")} {num(f.get("ratio_1y"), 1)}%</span></div>'
                 f'<div><span class="muted">{T("年化利息支出", "Interest (annual)")}</span><b>{num(f["interest_bn"] / 1000, 2)} {T("兆美元", "tn USD")}</b></div>'
                 + (f'<div><span class="muted">{T("聯邦債務總額", "Total public debt")}</span><b>{num(f["debt_tn"], 1)} {T("兆美元", "tn USD")}</b><span class="small muted">{esc(f.get("debt_q", ""))}</span></div>' if f.get("debt_tn") else "")
                 + f'</div><p class="small muted">{T("BEA 季資料（年化），資料季度", "BEA quarterly (annualised), quarter")} {esc(f["q"])}</p>')
    au = r.get("auctions") or []
    if au:
        rows = "".join(f'<tr><td>{esc(a.get("date", ""))}</td><td>{esc(a.get("term", ""))}</td><td class="r">{num(a.get("high_yield"), 3)}%</td>'
                       f'<td class="r">{num(a.get("btc"), 2)}</td><td class="r">{num(a.get("indirect"), 1)}%</td><td>{esc(a.get("verdict") or "—")}</td></tr>' for a in au)
        body += (f'<h3>{T("6. 長天期美債標售", "6. Long-end auctions")}</h3><table class="mini"><thead><tr><th>{T("日期", "Date")}</th><th>{T("年期", "Term")}</th>'
                 f'<th class="r">{T("得標利率", "Yield")}</th><th class="r">{T("投標倍數", "Bid/cover")}</th><th class="r">{T("海外法人", "Indirect")}</th>'
                 f'<th>{T("和近期比", "vs recent")}</th></tr></thead><tbody>{rows}</tbody></table>')
    ai = [a for a in (r.get("ai") or []) if a.get("cost") is not None or a.get("debt_growth") is not None]
    if ai:
        def per(a):
            de = a.get("debt_end")
            return esc(a.get("end") or "") + (f'（{T("負債", "debt")} {esc(de)}）' if de and de != a.get("end") else "")
        rows = "".join(f'<tr><td><b>{esc(a["sym"])}</b></td><td class="r">{T(num(a["debt_bn"] * 10, 0) + " 億", num(a["debt_bn"], 1) + " bn") if a.get("debt_bn") else "—"}</td>'
                       f'<td class="r">{(num(a["cost"], 1) + "%") if a.get("cost") is not None else "—"}</td><td class="r">{num(a.get("debt_growth"), 0, sign=True, pct=True)}</td>'
                       f'<td class="r">{(num(a["int_burden"], 1) + "%") if a.get("int_burden") is not None else "—"}</td><td class="small muted">{per(a)}</td></tr>' for a in ai)
        body += (f'<h3>{T("7. AI 公司的借錢成本", "7. What AI companies pay to borrow")}</h3><table class="mini"><thead><tr><th></th>'
                 f'<th class="r">{T("總負債（美元）", "Total debt (USD)")}</th><th class="r">{T("平均借款成本", "Avg cost of debt")}</th><th class="r">{T("負債年增", "Debt y/y")}</th><th class="r">{T("利息／營業利益", "Interest/EBIT")}</th><th>{T("財報期", "Period")}</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table><p class="small muted">{T("平均借款成本＝近 12 個月利息支出 ÷ 目前負債，反映的是舊債與新債的平均；新發債的利率通常更高。", "Average cost = TTM interest ÷ debt; new issues usually cost more.")}</p>')
    note = T("把「美債殖利率 → AI 科技股」這條鏈放在一起看：殖利率為什麼漲、股票相對公債貴不貴、科技股對利率多敏感、離媒體常說的警戒線多遠、政府付利息的壓力、長債有沒有人買、AI 公司借錢有多貴。"
             "全部來自官方與市場數據（FRED、財政部、SEC、Yahoo）；🔑 重點是固定規則的解讀，不是預測，也不是投資建議。",
             "The Treasury → tech chain in one place, from official and market data. Readings are fixed rules, not forecasts or advice.")
    return card("利率衝擊雷達：美債殖利率 → AI 科技股", "Rates shock radar: Treasury yields → AI / tech", body + f'<p class="note">{note}</p>', "wide")
