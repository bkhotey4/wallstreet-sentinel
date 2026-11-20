"""財經日曆頁：IPO 觀察（美股／台股）— who is filing to list, where each one is in the process, when it is likely to list
(US: from the timing of past cases; Taiwan: the dates in the 公開申購公告), the prospectus in plain words (AI, numbers only
from the filing), and how past IPOs actually did after listing.  Describes, not advice."""
from __future__ import annotations

from typing import Dict, List, Optional

from tools.sitekit import T, card, cls, esc, num, fold_rows


def _md(s: Optional[str]) -> str:
    return esc(str(s)[5:]) if s else "—"


def _pc(v, d=0) -> str:
    return f'<b class="{cls(v)}">{num(v, max(d, 1) if v is not None and abs(v) < 1 else d, sign=True)}%</b>' if v is not None else "—"


def _p1(v) -> str:
    return f"{num(v, 1)}%" if v is not None else "—"


def _stat(x: Optional[Dict], what: str, pos: str) -> str:
    return f"{what}中位數 {x['med']:+.0f}%（{pos} {x['pos']:.0f}%，{x['n']} 家）" if x else ""


def _money(v: Optional[float]) -> str:
    if v is None:
        return "—"
    a = abs(v)
    return f"{v / 1e8:,.1f} 億美元" if a >= 1e8 else f"{v / 1e6:,.1f} 百萬美元" if a >= 1e6 else f"{v:,.0f} 美元"


CANCEL_SHOW_DAYS = 14    # a cancelled Taiwan offering is named in the lead for two weeks after its planned listing day


def _usd(x: float) -> str:
    if abs(x) < 1e8:                                   # 11-20: a US$7M micro-cap IPO was printed as 「約 0 億美元～0 億美元」
        return f"{x / 1e6:,.1f} 百萬美元"
    return f"{x / 1e8:,.0f} 億美元" if x < 1e12 else f"{x / 1e12:,.2f} 兆美元"


def deal_block(r: Dict) -> str:
    """承銷結構 (11-17, the user had to bring it from a video): deal size at the price range, the over-allotment (greenshoe)
    and the 30-day stabilization it allows, a concurrent private placement, non-binding indications of interest, and a
    share class holding fixed voting control — all read from the prospectus text by tools/../ipo_data.parse_cover."""
    lo, hi, base = r.get("lo"), r.get("hi"), r.get("shares")
    final = bool(r.get("final_price"))                 # priced: lo = hi = the offer price, numbers from the 424B4
    lines = []
    if lo and hi and base:
        sell = r.get("sell_shares") or 0
        gs = r.get("gs_shares") or 0
        tot = base + sell
        txt = (f"公開發行 {tot / 1e6:,.1f} 百萬股" + (f"（公司新股 {base / 1e6:,.1f}、老股東釋出 {sell / 1e6:,.1f}；老股東拿走的錢不進公司）" if sell else "")
               + (f"，以發行價 {num(hi, 2)} 美元算約 {_usd(tot * hi)}" if final else f"，以價格區間算約 {_usd(tot * lo)}～{_usd(tot * hi)}"))
        if gs:
            txt += f"；加上超額配售最多再 {gs / 1e6:,.1f} 百萬股（基本量的 {gs / tot * 100:.0f}%），最高約 {_usd((tot + gs) * hi)}"
        lines.append(txt + "。")
    if r.get("gs_shares"):
        lines.append(f"<b>超額配售（綠鞋）與穩價</b>：承銷商先多賣這些股票；上市後 {r.get('gs_days') or 30} 天內，股價漲就向公司加買（行使選擇權），"
                     "股價跌到發行價附近就在市場買回來撐價格。這段期間結束後，少了這個支撐，常是新股第一個考驗。")
    if r.get("pp"):
        names = "、".join(f"{esc(x['name'])} {_usd(x['usd'])}" for x in r["pp"])
        lines.append(f"<b>同步私募</b>：上市同時，以發行價直接賣股票給 {len(r['pp'])} 家公司，共 {_usd(r.get('pp_total') or 0)}（{names}；"
                     + ("股數已照最終發行價" if final else "招股書以價格區間中點估算，實際股數照最終發行價")
                     + "）。這筆錢進公司、不經過承銷商，也不在公開發行的股數裡。"
                     + (f"公開發行加同步私募合計約 {_usd((base + (r.get('sell_shares') or 0)) * hi + (r.get('pp_total') or 0))}"
                        + (f"，含超額配售約 {_usd((base + (r.get('sell_shares') or 0) + (r.get('gs_shares') or 0)) * hi + (r.get('pp_total') or 0))}" if r.get("gs_shares") else "")
                        + ("（以發行價）。" if final else "（以區間上緣）。") if hi and base else ""))
    if r.get("ioi_usd"):
        lines.append(f"<b>認購意願</b>：部分董事或現有股東表示有意以發行價買最多 {_usd(r['ioi_usd'])}，但不具約束力，可多可少。")
    if r.get("vote_ctrl"):
        lines.append(f"<b>控制權</b>：招股書寫明有一類股票掌握 {r['vote_ctrl']:g}% 的投票權；一般買到的股票投票權有限，重大決定由這一類股東主導。")
    if not lines:
        return ""
    return ('<details class="sgx"><summary class="small">' + T("承銷結構：募多少、超額配售、同步私募、控制權", "Deal structure") + "</summary>"
            + "".join(f'<p class="small">{x}</p>' for x in lines)
            + '<p class="small muted">'
            + (T("全部由程式從定價後的最終公開說明書（424B4）原文讀出（不是 AI）。", "") if final
               else T("全部由程式從招股書原文讀出（不是 AI），金額以價格區間估算，最終以定價後的 424B4 為準。", ""))
            + "</p></details>")


def _final_block(r: Dict) -> str:
    """The same 承銷結構 fold for a priced IPO, from the 424B4 (11-20: it used to vanish the day the deal priced, just
    when the greenshoe / stabilization window starts to matter)."""
    fin = r.get("final") or {}
    if not (fin and r.get("offer")):
        return ""
    return deal_block({**fin, "lo": r["offer"], "hi": r["offer"], "final_price": r["offer"]})


def fin_block(fin: Optional[Dict]) -> str:
    """招股書財務：每季營收、季增（QoQ）、和去年同季比（YoY）、營益率；沒有季度表就用年度／期中數字。只寫數字，不下判斷。"""
    if not fin:
        return ""
    q, sm = fin.get("q") or {}, fin.get("summary") or {}
    parts = []
    if q.get("quarters"):
        qs = q["quarters"][-6:]
        lead = ""
        if q.get("qoq_last") is not None and q.get("qoq_prev") is not None:
            sl = q["qoq_last"] < q["qoq_prev"]
            lead = (f'最新一季營收季增 {q["qoq_last"]:+.0f}%，'
                    + (f'比上一季的 {q["qoq_prev"]:+.0f}% {"放緩" if sl else "加快"}' )
                    + (f'；新增的營收 {_money(q["add_last"])}，上一季新增 {_money(q["add_prev"])}' if q.get("add_last") is not None and q.get("add_prev") is not None else "")
                    + "。")
        rows = "".join(f'<tr><td class="nw">{esc(x["end"][:7])}</td><td class="r">{_money(x.get("rev"))}</td><td class="r">{_pc(x.get("qoq"))}</td>'
                       f'<td class="r">{_pc(x.get("yoy"))}</td><td class="r">{_p1(x.get("gp_m"))}</td><td class="r">{_p1(x.get("op_m"))}</td></tr>' for x in qs)
        parts.append(f'<p class="small"><b>{esc(lead)}</b></p><div class="scroll"><table class="mini"><thead><tr><th>季度（結束月）</th><th class="r">營收</th>'
                     f'<th class="r">季增 QoQ</th><th class="r">年增 YoY</th><th class="r">毛利率</th><th class="r">營益率</th></tr></thead><tbody>{rows}</tbody></table></div>')
    for key, nm in (("interim", "期中"), ("annual", "全年")):
        r = sm.get(key)
        if not r or r.get("rev") is None:
            continue
        span = "全年" if r["months"] == 12 else f'前 {r["months"]} 個月'
        bits = [f'{r["year"]} 年{span}營收 {_money(r["rev"])}' + (f'（年增 {r["rev_yoy"]:+.0f}%）' if r.get("rev_yoy") is not None else "")]
        if r.get("gp_m") is not None:
            bits.append(f'毛利率 {r["gp_m"]:.1f}%' + (f'（去年同期 {r["gp_m_prev"]:.1f}%）' if r.get("gp_m_prev") is not None else ""))
        if r.get("op_m") is not None:
            bits.append(f'營益率 {r["op_m"]:.1f}%' + (f'（去年同期 {r["op_m_prev"]:.1f}%）' if r.get("op_m_prev") is not None else ""))
        if r.get("ni") is not None:
            bits.append(("淨損 " if r["ni"] < 0 else "淨利 ") + _money(abs(r["ni"])))
        parts.append(f'<p class="small">{esc("；".join(bits))}。</p>')
    if not parts:
        return ""
    note = ("數字由程式從招股書的摘要財務表與季度營運表直接讀出（不是 AI），單位照原文換算；季增＝和上一季比，年增＝和去年同一季比。"
            "高速成長的公司，季增從很高的基期往下掉很常見，要同時看「新增的營收金額」與獲利率。")
    return ('<details class="sgx" open><summary class="small">' + T("招股書財務（季增／年增）", "Prospectus financials") + "</summary>"
            + "".join(parts) + f'<p class="small muted">{note}</p></details>')


def _us_pending(u: Dict) -> str:
    rows = u.get("pending") or []
    if not rows:
        return f'<p class="muted small">{T("目前沒有說明要在主要交易所掛牌、仍在申請中的公司。", "")}</p>'
    tr = []
    for r in rows:                                     # all filers; 40 shown, rest folded (user, 11-17: full data)
        rng = (f'${num(r["lo"], 2)}～{num(r["hi"], 2)}' if r.get("lo") else T("尚未公布", "Not yet"))
        when = ("—" if not r.get("win_lo") else
                (f'{T("已比過去多數案子久", "Slower than most")}<div class="small muted">{T("常見區間", "Usual")} {_md(r["win_lo"])}～{_md(r["win_hi"])}</div>'
                 if r.get("slow") else f'{_md(r["win_lo"])}～{_md(r["win_hi"])}'))
        if r.get("near"):
            when = f'<b>{T("約", "~")} {_md(r["near"])}</b><div class="small muted">{T("已公布價格區間", "Range set")}</div>'
        if r.get("listing"):
            src = r.get("stage_src") or {}
            when = (f'<b>{_md(r["listing"])} {T("掛牌", "listing")}</b><div class="small muted">{T("公司公布的時間表", "Company timetable")}'
                    f'（<a href="{esc(src.get("url", ""))}" target="_blank" rel="noopener">{esc(src.get("filed", ""))} 申報</a>，{esc(src.get("tz", ""))}），'
                    f'前一晚定價</div>')
        elif r.get("stage"):
            n, md = r.get("stage_n") or 0, r.get("stage_med")
            span = (f'過去 {n} 家從這一步到定價中位數 {md:.0f} 天（一半在 {r["stage_p25"]:.0f}～{r["stage_p75"]:.0f} 天）'
                    if n >= 5 and md is not None else '已在掛牌前最後幾步')
            rng = f'（{_md(r["near_lo"])}～{_md(r["near_hi"])}）' if r.get("near_lo") and r.get("near_hi") and r["near_lo"] != r["near_hi"] else ""
            when = f'<b>{T("約", "~")} {_md(r["near"])}</b>{rng}<div class="small muted">{esc(r["stage"])}，{span}</div>'
        ai = r.get("ai") or {}
        det = ""
        if ai:
            det = ('<details class="sgx"><summary class="small">' + T("招股書重點", "Prospectus") + "</summary>"
                   + "".join(f'<p class="small"><b>{esc(k)}</b>：{esc(ai[k])}</p>' for k in ("業務", "財務", "資金用途", "主要風險", "要留意") if ai.get(k))
                   + f'<p class="small muted">{T("AI 依招股書節錄整理，數字照原文；有對不上原文的句子會被拿掉。", "")}</p></details>')
        det = fin_block(r.get("fin")) + deal_block(r) + det
        sec = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={esc(r["cik"])}&type=S-1&dateb=&owner=include&count=40'
        tr.append(f'<tr><td><b>{esc(r["name"])}</b>' + (f' <span class="tk">{esc(r["symbol"])}</span>' if r.get("symbol") else "")
               + f'<div class="small muted">{esc(r.get("sicd") or "")}{"・外國公司" if r.get("foreign") else ""}</div>{det}</td>'
               f'<td class="small">{esc(r.get("exchange") or "")}</td>'
               f'<td class="nw">{_md(r["s1"])}<div class="small muted">{T("已過", "")} {r["since"]} {T("天", "d")}</div></td>'
               f'<td class="nw">{_md(r["last"])}<div class="small muted">{T("修正", "amend")} {r["amends"]} {T("次", "")}</div></td>'
               f'<td class="nw">{rng}</td><td class="nw">{when}</td>'
               f'<td><a href="{sec}" target="_blank" rel="noopener">SEC</a></td></tr>')
    head = (f'<tr><th>{T("公司", "Company")}</th><th>{T("預計掛牌", "Exchange")}</th><th>{T("首次公開申請", "First public filing")}</th>'
            f'<th>{T("最近修正", "Latest amendment")}</th><th>{T("價格區間", "Price range")}</th><th>{T("依過去經驗可能定價", "Likely pricing")}</th><th></th></tr>')
    oth = f"另有 {u.get('other', 0)} 家申請中的公司招股書還沒讀到，或沒說明要在 Nasdaq／紐約證交所掛牌（多為小型或場外）。"
    more = f'<p class="small muted">{T(oth, "")}</p>' if u.get("other") else ""
    return fold_rows(tr, 40, head, "家") + more


def _stab(r: Dict) -> str:
    """Stabilization window (greenshoe, ~30 days): when it ends and whether the stock broke the offer price during / after."""
    if not r.get("stab_end"):
        return "—"
    from wsb.data.econcal import us_today              # stab_end is a US trading day; the build machine runs on UTC
    end = r["stab_end"]
    if us_today().isoformat() <= end:
        return f'{T("到", "to")} {_md(end)}<div class="small muted">{T("進行中", "ongoing")}' + ("・曾跌破發行價" if r.get("below_in") else "") + "</div>"
    note = ("期間曾跌破" if r.get("below_in") else "期間守住") + ("、結束後跌破" if r.get("below_after") else "、結束後守住" if r.get("below_after") is False else "")
    return f'{_md(end)} {T("結束", "ended")}<div class="small muted">{note}</div>'


def _us_done(u: Dict) -> str:
    rows = u.get("recent") or []
    tr = [
        f'<tr><td><b>{esc(r["name"])}</b> <span class="tk">{esc(r.get("sym") or "")}</span><div class="small muted">{esc(r.get("sicd") or "")}</div>{_final_block(r)}</td>'
        f'<td class="nw">{_md(r["priced"])}</td><td class="r">{("$" + num(r["offer"], 2)) if r.get("offer") else "—"}</td>'
        f'<td class="r">{_pc(r.get("day1"))}</td><td class="r">{_pc(r.get("vs_offer"))}</td>'
        f'<td class="nw">{_stab(r)}</td>'
        f'<td class="nw">{_md(r.get("lock"))}<div class="small muted">{r.get("lockup")} {T("天", "d")}</div></td></tr>' for r in rows]   # all; 30 shown
    if not tr:
        return ""
    head = (f'<tr><th>{T("公司", "Company")}</th><th>{T("定價", "Priced")}</th><th class="r">{T("發行價", "Offer")}</th>'
            f'<th class="r">{T("第一天收盤", "Day 1")}</th><th class="r">{T("至今 vs 發行價", "Now vs offer")}</th><th>{T("穩價期", "Stabilization")}</th><th>{T("禁售期到期", "Lock-up ends")}</th></tr>')
    return fold_rows(tr, 30, head, "家")


def _tw_up(t: Dict) -> str:
    rows = t.get("upcoming") or []
    if not rows:
        return f'<p class="muted small">{T("目前沒有已公告、還沒掛牌的新股。", "")}</p>'
    tr = ""
    for r in rows:
        f = r.get("fin") or {}
        fin = (f'{T("營收年增", "Rev YoY")} {_pc(f.get("yoy"))}<div class="small muted">{T("近四季淨利率", "TTM margin")} {_p1(f.get("nm_ttm"))}</div>'
               if f.get("yoy") is not None or f.get("nm_ttm") is not None else "—")
        esb = (f'{num(r["esb_avg"], 1)}<div class="small muted">{T("承銷價低", "Offer below by")} {num(-r["disc"], 0)}%</div>' if r.get("disc") is not None else "—")
        pre = "" if r.get("final") else f'<div class="small muted">{T("暫定", "prelim")}</div>'
        tr += (f'<tr><td class="nw"><b>{esc(r["name"])}</b> <span class="tk">{esc(r["code"])}</span><div class="small muted">{esc(r["mk"])}・{esc(r.get("broker") or "")}</div></td>'
               f'<td class="nw">{_md(r.get("sub_lo"))}～{_md(r.get("sub_hi"))}</td><td class="nw">{_md(r.get("draw"))}</td>'
               f'<td class="nw"><b>{_md(r.get("list"))}</b></td><td class="r">{num(r.get("price"), 1)}{pre}</td>'
               f'<td class="r">{esb}</td><td class="r">{num(r.get("win"), 2) + "%" if r.get("win") else "—"}</td><td class="r">{fin}</td></tr>')
    head = (f'<thead><tr><th>{T("公司", "Company")}</th><th>{T("申購期間", "Subscription")}</th><th>{T("抽籤日", "Draw")}</th><th>{T("掛牌日", "Listing")}</th>'
            f'<th class="r">{T("承銷價", "Offer")}</th><th class="r">{T("興櫃均價", "Emerging avg")}</th><th class="r">{T("中籤率", "Win rate")}</th>'
            f'<th class="r">{T("財報", "Financials")}</th></tr></thead>')
    return f'<div class="scroll"><table class="mini">{head}<tbody>{tr}</tbody></table></div>'


def _tw_apply(t: Dict) -> str:
    rows = t.get("applying") or []
    if not rows:
        return ""
    tr = "".join(
        f'<tr><td class="nw"><b>{esc(r["name"])}</b> <span class="tk">{esc(r["code"])}</span></td><td>{esc(r.get("to") or "—")}</td>'
        f'<td class="nw">{esc(r["apply"])}<div class="small muted">{T("已過", "")} {r["since"]} {T("天", "d")}</div></td>'
        f'<td class="r">{num(r.get("avg"), 1) if r.get("avg") else "—"}</td><td class="r">{_pc((r.get("fin") or {}).get("yoy"))}</td>'
        f'<td class="r">{_p1((r.get("fin") or {}).get("nm_ttm"))}</td></tr>' for r in rows)
    head = (f'<thead><tr><th>{T("公司", "Company")}</th><th>{T("申請", "To")}</th><th>{T("申請日", "Applied")}</th><th class="r">{T("興櫃均價", "Emerging avg")}</th>'
            f'<th class="r">{T("營收年增", "Rev YoY")}</th><th class="r">{T("近四季淨利率", "TTM margin")}</th></tr></thead>')
    return f'<div class="scroll"><table class="mini srt">{head}<tbody>{tr}</tbody></table></div>'


def lead(b: Dict) -> str:
    u, t = b["us"], b["tw"]
    pend = u.get("pending") or []
    rng = [r for r in pend if r.get("lo")]
    s = ("一句話看懂：美股的 SEC 申報資料正在第一次建立（每 20 分鐘補一批，約需一天），完成前申請中的名單不完整"
         if u.get("filling") else f"一句話看懂：美股目前 {len(pend)} 家公司公開申請、要在主要交易所掛牌")
    if rng:
        s += f"，其中 {len(rng)} 家已公布價格區間、最接近定價（" + "、".join(r["name"] for r in rng[:3]) + ("等，全部列在下表" if len(rng) > 3 else "") + "）"
    stg = [r for r in pend if r.get("stage")]
    if stg:                                            # 11-17: the 8-A12B / EFFECT step means pricing within days
        s += "；即將定價：" + "、".join(f'{r["name"]}' + (f'（{r["symbol"]}）' if r.get("symbol") else "") + (f' {_md(r["listing"])} 掛牌（公司時間表）' if r.get("listing") else f' 約 {_md(r["near"])}') for r in stg)
    up = t.get("upcoming") or []
    s += f"；台股已公告 {len(up)} 家即將掛牌" + ("（" + "、".join(f"{r['name']} {_md(r.get('list'))}" for r in up) + "）" if up else "")   # every one of them (11-17: said 4, named 3)
    from datetime import date as _date, timedelta as _td
    since = (_date.today() - _td(days=CANCEL_SHOW_DAYS)).isoformat()
    off = [r for r in (t.get("cancelled") or []) if (r.get("list") or "") >= since]
    if off:
        s += "（" + "、".join(r["name"] for r in off) + " 已取消這次承銷，不列入）"
    s += f"、{len(t.get('applying') or [])} 家已申請上市櫃。"
    su, st = u.get("stats") or {}, t.get("stats") or {}
    big = su.get("big") or {}
    if big.get("day1") and big.get("x120"):
        s += (f"過去募資 1 億美元以上的美股 IPO，第一天收盤比發行價中位數 {big['day1']['med']:+.0f}%，但從第一天收盤算起約半年後，"
              f"中位數比標普 {big['x120']['med']:+.1f}%（贏過標普的 {big['x120']['pos']:.0f}%）。")
    if st.get("day1"):
        s += f"台股新股第一天收盤比承銷價中位數 {st['day1']['med']:+.0f}%"
        s += (f"，60 天後比加權指數 {st['x60']['med']:+.0f}%。" if st.get("x60") else "。")
    return s


def sec_ipo(eng) -> str:
    b = getattr(eng, "ipo", None)
    if b is None:
        try:
            from wsb.analytics import ipo as IP
            b = IP.build(eng)
        except Exception:  # noqa: BLE001
            b = None
    if not b:
        return ""
    u, t = b["us"], b["tw"]
    tf, tl = u.get("t_first"), u.get("t_last")
    timing = (f"美股時程（過去 {tf['n']} 家已定價的 IPO）：第一次公開提交 S-1／F-1 到定價中位數 {tf['med']:.0f} 天（一半落在 {tf['p25']:.0f}～{tf['p75']:.0f} 天）"
              + (f"；最後一次修正到定價中位數 {tl['med']:.0f} 天" if tl else "") + "。修正版公布價格區間，通常代表開始路演、接近定價；"
              "超過多數案子的天數還沒定價，常是等市場、或之後撤回。" if tf else "美股時程：已定價的案例還不夠多，暫不估計。")
    su = u.get("stats") or {}

    def us_line(x: Dict) -> str:
        return "；".join(y for y in (_stat(x.get("day1"), "第一天收盤 vs 發行價", "上漲比例"), _stat(x.get("x60"), "60 個交易日後 vs 標普", "贏過標普"),
                                     _stat(x.get("x120"), "120 個交易日後 vs 標普", "贏過標普"), _stat(x.get("vs_offer"), "至今 vs 發行價", "高於發行價"),
                                     _stat(x.get("lockx"), "禁售期到期前後 10 天 vs 標普", "贏過標普")) if y)
    parts = [(lab, us_line(su.get(k) or {})) for k, lab in (("big", "募資 1 億美元以上"), ("small", "募資不到 1 億美元"))]
    hist_us = "。".join(f"{lab}：{ln}" for lab, ln in parts if ln) or us_line(su)
    st = t.get("stats") or {}
    hist_tw = "；".join(x for x in (_stat(st.get("day1"), "第一天收盤 vs 承銷價", "上漲比例"), _stat(st.get("d20"), "20 個交易日後 vs 承銷價", "高於承銷價"),
                                    _stat(st.get("x60"), "60 個交易日後 vs 加權指數", "贏過指數"), _stat(st.get("vs_offer"), "至今 vs 承銷價", "高於承銷價")) if x)
    if t.get("win_med"):
        hist_tw += f"；公開抽籤中籤率中位數 {t['win_med']:.2f}%"
    sb = (su.get("big") or {}).get("stab") or su.get("stab")
    stab_txt = (f"穩價期（上市後約 30 天，承銷商可以在市場買回撐價格）：過去 {sb['n']} 家走完穩價期與之後 30 天的 IPO 中，"
                f"穩價期間曾跌破發行價的占 {sb['in']:.0f}%，穩價期結束後 30 天內跌破的占 {sb['after']:.0f}%，"
                f"其中「期間守住、結束後才跌破」的占 {sb['held_then_broke']:.0f}%。" if sb else "")
    soon = u.get("lock_soon") or []
    lock = ("未來 30 天禁售期到期：" + "、".join(f"{r['name']}（{r.get('sym') or ''}）{_md(r['lock'])}" for r in soon[:6])
            + "。禁售期結束後，上市前的股東可以開始賣股。") if soon else ""
    body = (f'<p class="rimp big2"><b>{T(lead(b), "")}</b></p>'
            f'<details class="sgx" open><summary><b>{T("美股：申請中", "US: in registration")}</b> <span class="muted small">{len(u.get("pending") or [])}</span></summary>'
            f'<p class="small">{T(timing, "")}</p>{_us_pending(u)}</details>'
            f'<details class="sgx"><summary><b>{T("美股：最近 120 天已定價", "US: priced in the last 120 days")}</b> <span class="muted small">{len(u.get("recent") or [])}</span></summary>'
            + (f'<p class="small">{T(lock, "")}</p>' if lock else "") + (f'<p class="small">{T(stab_txt, "")}</p>' if stab_txt else "") + _us_done(u)
            + (f'<p class="small">{T("過去紀錄（" + (u.get("from") or "—") + " 起）：" + hist_us + "。", "")}</p>' if hist_us else "") + "</details>"
            f'<details class="sgx" open><summary><b>{T("台股：即將掛牌", "Taiwan: listing soon")}</b> <span class="muted small">{len(t.get("upcoming") or [])}</span></summary>{_tw_up(t)}</details>'
            f'<details class="sgx"><summary><b>{T("台股：已申請上市櫃（興櫃審查中）", "Taiwan: applied to list")}</b> <span class="muted small">{len(t.get("applying") or [])}</span></summary>{_tw_apply(t)}</details>'
            + (f'<p class="small">{T("台股過去紀錄（" + (t.get("from") or "—") + " 起）：" + hist_tw + "。", "")}</p>' if hist_tw else ""))
    how = ("美股：從 SEC EDGAR 找出提交 S-1／F-1（含修正版）與 424B4（最終招股書，定價時提交）的公司，排除已經在申報季報／年報的公司（那是增資，不是 IPO）、"
           "SPAC 與基金；只列出招股書寫明要在 Nasdaq 或紐約證交所掛牌的。價格區間、代號、禁售天數從最新招股書封面讀取；發行價從 424B4 讀取。"
           "「依過去經驗可能定價」＝第一次公開申請日加上過去案子 25%～75% 的天數，不是公司公布的日期；公司可以隨時延後或撤回。"
           "招股書重點由 AI 依節錄整理，數字照原文單位，對不上原文的句子會被拿掉。上市後表現：第一天收盤和發行價比；60／120 個交易日從第一天收盤算、和標普比；"
           "禁售期到期＝定價日加禁售天數（招股書沒寫用 180 天）。"
           "台股：證交所公開申購公告（承銷價、申購期間、抽籤日、掛牌日、中籤率）、櫃買中心興櫃行情（興櫃均價、申請上市櫃日期）、FinMind 季報。"
           "限制：只有公開資料；已下市或改名的公司股價可能抓不到；樣本不大。這是整理與歷史統計，不是申購或買賣建議。")
    body += f'<details class="small"><summary>{T("資料來源、怎麼算、限制", "Method and limits")}</summary><p class="note">{T(how, "")}</p></details>'
    return card("IPO 觀察：誰要上市、什麼時候、招股書重點（美股／台股）", "IPO watch: US and Taiwan", body, "wide")
