"""財經日曆頁：IPO 觀察（美股／台股）— who is filing to list, where each one is in the process, when it is likely to list
(US: from the timing of past cases; Taiwan: the dates in the 公開申購公告), the prospectus in plain words (AI, numbers only
from the filing), and how past IPOs actually did after listing.  Describes, not advice."""
from __future__ import annotations

from typing import Dict, List, Optional

from tools.sitekit import T, card, cls, esc, num


def _md(s: Optional[str]) -> str:
    return esc(str(s)[5:]) if s else "—"


def _pc(v, d=0) -> str:
    return f'<b class="{cls(v)}">{num(v, max(d, 1) if v is not None and abs(v) < 1 else d, sign=True)}%</b>' if v is not None else "—"


def _p1(v) -> str:
    return f"{num(v, 1)}%" if v is not None else "—"


def _stat(x: Optional[Dict], what: str, pos: str) -> str:
    return f"{what}中位數 {x['med']:+.0f}%（{pos} {x['pos']:.0f}%，{x['n']} 家）" if x else ""


def _us_pending(u: Dict) -> str:
    rows = u.get("pending") or []
    if not rows:
        return f'<p class="muted small">{T("目前沒有說明要在主要交易所掛牌、仍在申請中的公司。", "")}</p>'
    tr = ""
    for r in rows[:40]:
        rng = (f'${num(r["lo"], 2)}～{num(r["hi"], 2)}' if r.get("lo") else T("尚未公布", "Not yet"))
        when = ("—" if not r.get("win_lo") else
                (f'{T("已比過去多數案子久", "Slower than most")}<div class="small muted">{T("常見區間", "Usual")} {_md(r["win_lo"])}～{_md(r["win_hi"])}</div>'
                 if r.get("slow") else f'{_md(r["win_lo"])}～{_md(r["win_hi"])}'))
        if r.get("near"):
            when = f'<b>{T("約", "~")} {_md(r["near"])}</b><div class="small muted">{T("已公布價格區間", "Range set")}</div>'
        ai = r.get("ai") or {}
        det = ""
        if ai:
            det = ('<details class="sgx"><summary class="small">' + T("招股書重點", "Prospectus") + "</summary>"
                   + "".join(f'<p class="small"><b>{esc(k)}</b>：{esc(ai[k])}</p>' for k in ("業務", "財務", "資金用途", "主要風險", "要留意") if ai.get(k))
                   + f'<p class="small muted">{T("AI 依招股書節錄整理，數字照原文；有對不上原文的句子會被拿掉。", "")}</p></details>')
        sec = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={esc(r["cik"])}&type=S-1&dateb=&owner=include&count=40'
        tr += (f'<tr><td><b>{esc(r["name"])}</b>' + (f' <span class="tk">{esc(r["symbol"])}</span>' if r.get("symbol") else "")
               + f'<div class="small muted">{esc(r.get("sicd") or "")}{"・外國公司" if r.get("foreign") else ""}</div>{det}</td>'
               f'<td class="small">{esc(r.get("exchange") or "")}</td>'
               f'<td class="nw">{_md(r["s1"])}<div class="small muted">{T("已過", "")} {r["since"]} {T("天", "d")}</div></td>'
               f'<td class="nw">{_md(r["last"])}<div class="small muted">{T("修正", "amend")} {r["amends"]} {T("次", "")}</div></td>'
               f'<td class="nw">{rng}</td><td class="nw">{when}</td>'
               f'<td><a href="{sec}" target="_blank" rel="noopener">SEC</a></td></tr>')
    head = (f'<thead><tr><th>{T("公司", "Company")}</th><th>{T("預計掛牌", "Exchange")}</th><th>{T("首次公開申請", "First public filing")}</th>'
            f'<th>{T("最近修正", "Latest amendment")}</th><th>{T("價格區間", "Price range")}</th><th>{T("依過去經驗可能定價", "Likely pricing")}</th><th></th></tr></thead>')
    oth = f"另有 {u.get('other', 0)} 家申請中的公司招股書還沒讀到，或沒說明要在 Nasdaq／紐約證交所掛牌（多為小型或場外）。"
    more = f'<p class="small muted">{T(oth, "")}</p>' if u.get("other") else ""
    return f'<div class="scroll"><table class="mini">{head}<tbody>{tr}</tbody></table></div>{more}'


def _us_done(u: Dict) -> str:
    rows = u.get("recent") or []
    tr = "".join(
        f'<tr><td><b>{esc(r["name"])}</b> <span class="tk">{esc(r.get("sym") or "")}</span><div class="small muted">{esc(r.get("sicd") or "")}</div></td>'
        f'<td class="nw">{_md(r["priced"])}</td><td class="r">{("$" + num(r["offer"], 2)) if r.get("offer") else "—"}</td>'
        f'<td class="r">{_pc(r.get("day1"))}</td><td class="r">{_pc(r.get("vs_offer"))}</td>'
        f'<td class="nw">{_md(r.get("lock"))}<div class="small muted">{r.get("lockup")} {T("天", "d")}</div></td></tr>' for r in rows[:30])
    if not tr:
        return ""
    head = (f'<thead><tr><th>{T("公司", "Company")}</th><th>{T("定價", "Priced")}</th><th class="r">{T("發行價", "Offer")}</th>'
            f'<th class="r">{T("第一天收盤", "Day 1")}</th><th class="r">{T("至今 vs 發行價", "Now vs offer")}</th><th>{T("禁售期到期", "Lock-up ends")}</th></tr></thead>')
    return f'<div class="scroll"><table class="mini">{head}<tbody>{tr}</tbody></table></div>'


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
        s += f"，其中 {len(rng)} 家已公布價格區間、最接近定價（" + "、".join(r["name"] for r in rng[:3]) + "）"
    up = t.get("upcoming") or []
    s += f"；台股已公告 {len(up)} 家即將掛牌" + ("（" + "、".join(f"{r['name']} {_md(r.get('list'))}" for r in up[:3]) + "）" if up else "")
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
    soon = u.get("lock_soon") or []
    lock = ("未來 30 天禁售期到期：" + "、".join(f"{r['name']}（{r.get('sym') or ''}）{_md(r['lock'])}" for r in soon[:6])
            + "。禁售期結束後，上市前的股東可以開始賣股。") if soon else ""
    body = (f'<p class="rimp big2"><b>{T(lead(b), "")}</b></p>'
            f'<details class="sgx" open><summary><b>{T("美股：申請中", "US: in registration")}</b> <span class="muted small">{len(u.get("pending") or [])}</span></summary>'
            f'<p class="small">{T(timing, "")}</p>{_us_pending(u)}</details>'
            f'<details class="sgx"><summary><b>{T("美股：最近 120 天已定價", "US: priced in the last 120 days")}</b> <span class="muted small">{len(u.get("recent") or [])}</span></summary>'
            + (f'<p class="small">{T(lock, "")}</p>' if lock else "") + _us_done(u)
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
