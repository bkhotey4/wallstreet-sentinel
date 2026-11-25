"""公司的錢從哪裡來（2026-11-16，使用者選的第 4、5 項）：債務到期牆（美國公司債分頁）、股票供給（個股情報分頁）。
計算在 wsb/analytics/corp_funding.py；這裡只講成白話。ICE 公司債殖利率是授權資料：只用來算「借新還舊多付多少」，不顯示原始殖利率。"""
from __future__ import annotations

from typing import Dict, List, Optional

from tools.sitekit import T, card, esc, fold_rows


def _b(usd: Optional[float]) -> str:
    """dollars → 億美元 / 兆美元."""
    if usd is None:
        return "—"
    if usd == 0:
        return "0"
    if abs(usd) < 1e8:
        return "不到 1 億美元"
    return f"{usd / 1e12:.2f} 兆美元" if abs(usd) >= 1e12 else f"{usd / 1e8:,.0f} 億美元"


def _pc(x: Optional[float], d: int = 1, sign: bool = False) -> str:
    return "—" if x is None else f"{x * 100:{'+' if sign else ''}.{d}f}%"


def _extra(x: Optional[float]) -> str:
    return "—" if x is None else (f"少付 {_b(-x)}" if x < 0 else _b(x))


def _times(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:.1f} 倍"


def _data():
    from wsb.analytics import corp_funding as CF
    from wsb.analytics import distress as DZ
    from wsb.data import distress_data as DD
    cache = DD.load()
    names = DZ.watchlist()                         # public list only: holdings in the local cache never reach the page
    return CF, cache, names


def _mcaps(cache: Dict, names: Dict) -> Dict[str, float]:
    import json
    from wsb.config import DATA_DIR
    try:
        info = json.loads((DATA_DIR / "sinfo_yf.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        info = {}
    out = {}
    for s in names:
        px = (info.get(s) or {}).get("px")
        sh = ((cache.get(s) or {}).get("bs") or {}).get("shares")
        if px and sh and str((info.get(s) or {}).get("cur") or "USD").upper() == "USD":
            out[s] = float(px) * float(sh)
    return out


def sec_maturity_wall(eng) -> str:
    try:
        CF, cache, names = _data()
        yl = CF.yields()
        w = CF.wall(cache, names)
    except Exception:  # noqa: BLE001
        return ""
    if not w["n"]:
        return ""
    tot = w["tot"]
    rows = CF.refi_table(cache, names, yl) if yl else []
    extra = sum(r["extra"] for r in rows if r.get("extra") and r["extra"] > 0)
    tight = sorted((r for r in rows if r.get("self_pay") is not None and r["self_pay"] < 1 and (r["due1"] or 0) > 0), key=lambda r: r["self_pay"])
    heavy = sorted((r for r in rows if r.get("extra_ebit") is not None and r["extra_ebit"] > 0.05), key=lambda r: -r["extra_ebit"])
    lead = (f"追蹤的 {w['n']} 家非金融公司，未來 12 個月要還 <b>{_b(tot['mat1'])}</b> 的債務本金、第 2 年再 {_b(tot['mat2'])}"
            + (f"；如果照現在的市場利率借新還舊，這兩年到期的債一年要多付約 <b>{_b(extra)}</b> 利息" if extra > 0 else "")
            + "。")
    if tight:
        lead += f"手上現金加一年自由現金流還不夠還明年到期本金、得靠再借錢的有 {len(tight)} 家：{'、'.join(esc(r['zh']) for r in tight[:6])}。"
    t10 = (CF.load().get("yields") or {}).get("t10")
    mx = max(tot.values()) or 1.0
    bars = "".join(f'<div class="hb"><span class="hbl">{lbl}</span><span class="hbb" style="width:{max(2, tot[k] / mx * 100):.0f}%"></span>'
                   f'<span class="hbv">{_b(tot[k])}</span></div>' for k, lbl in CF.BUCKETS)
    top = sorted(rows, key=lambda r: -r["due"])[:15]
    trs = "".join(
        f'<tr><td class="nw"><b>{esc(r["sym"])}</b><div class="small muted">{esc(r["zh"])}</div></td>'
        f'<td class="r">{_b(r["due1"])}</td><td class="r">{_b(r["due2"])}</td>'
        f'<td class="r {"dn" if r.get("self_pay") is not None and r["self_pay"] < 1 else ""}">'
        f'{_times(r.get("self_pay"))}</td>'
        f'<td class="r">{_extra(r.get("extra"))}</td>'
        f'<td class="r {"dn" if (r.get("extra_ebit") or 0) > 0.05 else ""}">{_pc(r.get("extra_ebit"))}</td>'
        f'<td class="small">{CF.TIER_ZH[r["tier"]]}</td><td class="small muted">{esc(r.get("mat_end") or "")}</td></tr>' for r in top)
    head = (f'<tr><th>{T("公司", "Company")}</th><th class="r">{T("1 年內到期", "Due < 1y")}</th><th class="r">{T("第 2 年到期", "Due year 2")}</th>'
            f'<th class="r">{T("現金＋一年自由現金流 ÷ 1 年內到期", "Cash + 1y FCF ÷ due < 1y")}</th>'
            f'<th class="r">{T("照現在利率借新還舊，一年多付利息", "Extra interest a year if refinanced now")}</th>'
            f'<th class="r">{T("佔營業利益", "Share of operating income")}</th><th>{T("借錢級別（代理）", "Tier (proxy)")}</th><th>{T("到期表日期", "Schedule as of")}</th></tr>')
    chain = ("<b>為什麼要看</b>：公司幾年前用 2～4% 借的錢陸續到期，現在要用更高的利率借新還舊 → 利息吃掉更多獲利 → "
             "先砍的通常是買回股票、資本支出和招聘 → 獲利預估下修。借錢級別越低（高收益）、到期越集中的公司，越早感覺到。"
             + (f"美國 10 年期公債殖利率現在 {t10[1] * 100:.2f}%（{esc(t10[0])}），公司借錢的利率是在它上面再加風險溢價。" if t10 else ""))
    heavy_txt = (f"<p>多付的利息超過營業利益 5% 的：{'、'.join(esc(r['zh']) + '（' + _pc(r['extra_ebit']) + '）' for r in heavy)}。</p>" if heavy else "")
    note = ("到期金額來自各公司 10-K 附註「未來五年各年到期的長期債務本金」（XBRL：LongTermDebtMaturitiesRepaymentsOfPrincipal…），"
            "是上一個會計年度結束時的數字，之後新借或提前還的不在裡面；商業本票等短期借款不在這張表。"
            "「目前平均利率」＝近 12 個月利息費用 ÷ 負債；「現在的市場利率」依利息保障倍數粗分三級（≥ 8 倍投資級、3～8 倍 BBB、"
            "< 3 倍或虧損高收益），用 ICE 美銀公司債殖利率（FRED；授權資料，只用來計算、不顯示原始數字）。分級是經驗法則，不是信評；"
            "多付利息假設兩年內到期的本金全部照現在利率重借，是估算，不是預測。金融業不列入。")
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{lead}</p><p>{chain}</p>{heavy_txt}'
            f'<div class="hbars">{bars}</div>'
            f'<details><summary>到期最多的 15 家</summary><div class="scroll"><table class="mini srt"><thead>{head}</thead><tbody>{trs}</tbody></table></div></details>'
            f'<p class="note">{note}</p>')
    return card("債務到期牆：誰要用更貴的利率借新還舊", "Debt maturity wall", body, "wide",
                sub="追蹤公司未來五年每年要還多少債，和照現在利率重借要多付多少利息")


def _form_zh(f: str) -> str:
    return {"S-3": "儲架登記（之後可分批增資或發債）", "S-3ASR": "自動生效儲架登記", "424B5": "公開發行說明書補充（常見於分批增資）",
            "424B3": "公開發行說明書補充", "S-1": "首次或大型增資登記"}.get(f, f)


def sec_share_supply(eng) -> str:
    try:
        CF, cache, names = _data()
        rows = CF.supply(cache, names, _mcaps(cache, names))
    except Exception:  # noqa: BLE001
        return ""
    if not rows:
        return ""
    if not any(r.get("chg") is not None for r in rows):      # the SEC parser (v4) has not re-read the filings yet
        return ""
    odd = sorted((r for r in rows if r.get("chg") is not None and abs(r["chg"]) > 1.0), key=lambda r: -abs(r["chg"]))
    rows = [r for r in rows if r not in odd]                  # >100 % in a year: an IPO year, a share-class conversion or a stock deal
    up = sorted((r for r in rows if r.get("chg") is not None and r["chg"] > 0.02), key=lambda r: -r["chg"])
    down = sorted((r for r in rows if r.get("chg") is not None and r["chg"] < -0.01), key=lambda r: r["chg"])
    offers = [r for r in rows if r.get("offers")]
    lead = ("股數一年增加最多（舊股東被稀釋）：" + ("、".join(f"{esc(r['zh'])} {_pc(r['chg'], 1, True)}" for r in up[:5]) or "沒有超過 2% 的")
            + "；減少最多（公司買回自家股票）：" + ("、".join(f"{esc(r['zh'])} {_pc(r['chg'], 1, True)}" for r in down[:5]) or "沒有")
            + "。" + (f"最近 180 天有 {len(offers)} 家向 SEC 申報增資或發債的文件。" if any("offer" in (cache.get(r["sym"]) or {}) for r in rows) else ""))
    odd_txt = ("<p class='small muted'>股數一年變化超過一倍、沒有列進上面排名的："
               + "、".join(f"{esc(r['zh'])} {_pc(r['chg'], 0, True)}" for r in odd)
               + "。這種幅度多半是上市未滿一年、不同股票類別互相轉換或用股票併購，不是一般的增資稀釋，請看公司公告。</p>") if odd else ""

    def tr(r: Dict) -> str:
        last = r["offers"][0] if r.get("offers") else None
        doc = (f'<a href="{esc(last["url"] or "")}" target="_blank" rel="noopener">{esc(last["date"])} {esc(last["form"])}</a>'
               f'<div class="small muted">{esc(_form_zh(last["form"]))}</div>' if last else "—")
        return (f'<tr><td class="nw"><b>{esc(r["sym"])}</b><div class="small muted">{esc(r["zh"])}</div></td>'
                f'<td class="r {"dn" if (r.get("chg") or 0) > 0.02 else "up" if (r.get("chg") or 0) < -0.01 else ""}">{_pc(r.get("chg"), 1, True)}</td>'
                f'<td class="r">{_b(r.get("buyback"))}</td><td class="r">{_b(r.get("issue"))}</td>'
                f'<td class="r">{_pc(r.get("net_yield"), 1, True)}</td><td class="small">{doc}</td>'
                f'<td class="small muted">{esc(r.get("shares_end") or "")}</td></tr>')
    show = up[:12] + down[:8] + [r for r in offers if r not in up[:12] and r not in down[:8]][:6]
    # 11-17 (user: full data): every other tracked company is listed too, folded, biggest change first
    rest = sorted((r for r in rows if r not in show and r.get("chg") is not None), key=lambda r: -abs(r["chg"]))
    head = (f'<tr><th>{T("公司", "Company")}</th><th class="r">{T("股數一年變化", "Share count, 1y")}</th>'
            f'<th class="r">{T("近 12 個月買回", "Buybacks, 12m")}</th><th class="r">{T("近 12 個月發行新股", "New shares sold, 12m")}</th>'
            f'<th class="r">{T("淨買回 ÷ 市值", "Net buyback ÷ market cap")}</th><th>{T("最近的增資／發債文件", "Latest offering filing")}</th>'
            f'<th>{T("股數日期", "Shares as of")}</th></tr>')
    chain = ("<b>為什麼要看</b>：公司賺的錢可以拿來買回股票（每股分到的獲利變多），也可能為了蓋資料中心、還債而發新股（每股被稀釋）。"
             "AI 雲端這類燒錢擴張的公司，常用「儲架登記＋分批在市場上賣新股」籌錢：股價越高越好籌，股價下跌時籌錢變難、變貴，"
             "這也是它們股價波動特別大的原因之一。")
    note = ("股數用最近一季的稀釋後加權平均股數，和同一份財報裡重新表達的去年同期比（股票分割會回溯調整，所以分割不會被算成稀釋）；買回與發行新股取自現金流量表（近 12 個月）。"
            "文件清單來自 SEC 申報索引：S-3／S-3ASR 是先登記、之後可分批發行（股票或債券），424B 是每次實際發行時的補充說明，"
            "不一定是賣股票，可能是發債；點連結看原文。併購用股票付款、上市未滿一年、或不同股票類別互相轉換（例如 B 股轉成 A 股）也會讓股數一次大增，請對照公司公告。")
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{lead}</p><p>{chain}</p>{odd_txt}'
            f'<details><summary>股數變化最大、最近有申報的公司</summary>{fold_rows([tr(r) for r in show + rest], len(show), head, "家公司", "mini srt")}'
            f'</details><p class="note">{note}</p>')
    return card("股票供給：誰在買回、誰在發新股", "Share supply: buybacks vs new shares", body, "wide",
                sub="股數一年變化、買回與發行新股的金額、最近的增資或發債文件")


CSS = (".hbars{display:grid;gap:4px;margin:8px 0}.hb{display:grid;grid-template-columns:5.5em 1fr 7.5em;align-items:center;gap:8px;font-size:13px}"
       ".hbb{display:block;height:12px;border-radius:3px;background:var(--ac)}.hbv{text-align:right;font-variant-numeric:tabular-nums}"
       ".hbl{color:var(--muted)}")
