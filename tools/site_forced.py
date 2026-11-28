"""被迫進出的錢（2026-11-16，使用者選的第 1、2、3 項）與休市日曆（第 12 項）。資料與規則在 wsb/data/forced_flows.py、
wsb/data/exchange_cal.py；這裡只講成白話。全部是規則推算或模型估算，卡片都會說是哪一種。"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional

from tools.sitekit import T, card, esc, fold_rows

WD = "一二三四五六日"
US_HOL_ZH = {"New Year's Day": "元旦", "Martin Luther King Jr. Day": "馬丁路德金恩紀念日", "Washington's Birthday": "總統日",
             "Good Friday": "耶穌受難日", "Memorial Day": "陣亡將士紀念日", "Juneteenth National Independence Day": "六月節（解放日）",
             "Independence Day": "美國獨立紀念日", "Labor Day": "勞動節", "Thanksgiving Day": "感恩節", "Christmas Day": "聖誕節"}
EV_WHY = {"sp": "追蹤標普 500 的基金（光是 ETF 就有好幾兆美元）要在當天收盤照新名單調整；新加入的公司被迫買、被剔除的被迫賣。和四巫日同一天時成交量更大。",
          "russell": "追蹤羅素 2000（小型股）與羅素 1000 的基金一起換股，小型股的成交量常是全年最大之一；2026 年起一年兩次（6 月、12 月）。",
          "msci": "全球追蹤 MSCI 新興市場、全世界指數的基金照新權重調整；台股在 MSCI 新興市場的比重一變，外資就得在這天收盤買或賣台股。",
          "tw50": "元大台灣 50（0050）等追蹤台灣 50 指數的基金照新成分股調整，被加入或剔除的台股當天收盤成交量會放大。"}


def _md(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.month}/{d.day}（{WD[d.weekday()]}）"


def _pc(x: Optional[float], d: int = 1, sign: bool = True) -> str:
    return "—" if x is None else f"{x * 100:{'+' if sign else ''}.{d}f}%"


def _view() -> Dict:
    from wsb.data import forced_flows as FF
    return FF.view()


# ------------------------------------------------------------------ 1. 指數調整日曆
def sec_index_events(eng) -> str:
    try:
        from wsb.data import forced_flows as FF
        v = _view()
    except Exception:  # noqa: BLE001
        return ""
    today = date.today()
    # the 4 h cache can be built before midnight: drop dates already past, never print「還有 -1 天」(Gemini CODE-1, 11-26)
    evs = [e for e in (v.get("events") or []) if e["date"] >= today.isoformat()]
    if not evs:
        return ""
    med = v.get("past_med") or {}
    nxt = evs[0]
    days = (date.fromisoformat(nxt["date"]) - today).days
    zh = FF.KIND[nxt["kind"]][0]
    lead = (f"下一個是 <b>{_md(nxt['date'])}{zh}</b>（{'今天' if days == 0 else f'還有 {days} 天'}）"
            + (f"：過去同一種日子，收盤成交量的中位數是平常的 <b>{med[nxt['kind']]:.1f} 倍</b>" if med.get(nxt["kind"]) else "")
            + "。這些錢不管看法、在固定的日子一定要進出，所以那天的價格常被「量」推著走，隔天不一定延續。")
    rows = []
    for e in evs:                                       # all dates; 8 shown, rest folded (user, 11-17)
        k = e["kind"]
        past = (v.get("past") or {}).get(k) or []
        hist = "、".join(f"{d[5:].replace('-', '/')} {r:.1f}×" for d, r in past[-4:])
        tw = (f"<div class='small muted'>台股在 {_md(e['tw_date'])} 收盤調整</div>" if e.get("tw_date") and e["tw_date"] != e["date"] else "")
        rows.append(f'<tr><td class="nw"><b>{_md(e["date"])}</b>{tw}</td><td>{esc(FF.KIND[k][0])}</td>'
                 f'<td class="r">{f"{med[k]:.1f} 倍" if med.get(k) else "—"}</td><td class="small muted">{esc(hist)}</td>'
                 f'<td class="small">{esc(EV_WHY.get(k, ""))}</td></tr>')
    head = (f'<tr><th>{T("日期", "Date")}</th><th>{T("事件", "Event")}</th><th class="r">{T("過去收盤成交量（中位數）", "Past volume (median)")}</th>'
            f'<th>{T("最近幾次", "Recent")}</th><th>{T("誰被迫進出", "Who has to trade")}</th></tr>')
    asof = v.get("asof") or {}
    note = ("日子是照各指數公司的固定規則推算：標普 500 與台灣 50 在 3、6、9、12 月第三個週五收盤後生效（遇休市提前一天）；"
            "羅素指數 6 月第四個週五、2026 年起再加 12 月第二個週五；MSCI 在 2、5、8、11 月最後一個交易日收盤生效"
            "（最後一個交易日是美國感恩節隔天的半天時，MSCI 過去改在那一週的週一）。"
            "每種日子都拿過去幾年實際的成交量驗證過：「倍數」＝那天全市場成交量 ÷ 前 20 個交易日的中位數"
            f"（美股看標普 500 成分股、台股看上市股票；Yahoo，資料到 {esc(asof.get('^GSPC', '—'))}／{esc(asof.get('^TWII', '—'))}）。"
            "加入、剔除哪些公司由指數公司在生效前一到兩週公布，這裡不列名單。")
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{lead}</p>' + fold_rows(rows, 8, head, "個日子")
            + f'<p class="note">{note}</p>')
    return card("指數調整日曆：哪幾天會有被迫買賣的大單", "Index rebalance calendar", body, "wide",
                sub="標普 500、羅素、MSCI、台灣 50 的調整日，和過去同一種日子的成交量")


# ------------------------------------------------------------------ 2. 機械式基金推估
def sec_mech_funds(eng) -> str:
    try:
        v = _view()
    except Exception:  # noqa: BLE001
        return ""
    vc, tr = v.get("volctl") or {}, v.get("trend") or {}
    if not vc and not tr:
        return ""
    parts = []
    if vc:
        drop = (vc["after"] / vc["now"] - 1) if vc.get("after") and vc.get("now") else None
        parts.append(f"「波動控制」基金推估的股票比重現在約 <b>{vc['now'] * 100:.0f}%</b>"
                     + (f"（一週前 {vc['week'] * 100:.0f}%）" if vc.get("week") else "")
                     + (f"，在過去兩年排第 {vc['pct'] * 100:.0f} 百分位" if vc.get("pct") is not None else "")
                     + (f"；如果標普明天再跌 3%，比重會再降約 {abs(drop) * 100:.0f}%，等於還要再減一些股票" if drop is not None and drop < 0 else "")
                     + "。")
    sp = tr.get("^GSPC")
    if sp:
        f1, f3 = sp["flips"]["21"] if "21" in sp["flips"] else sp["flips"].get(21), sp["flips"]["63"] if "63" in sp["flips"] else sp["flips"].get(63)
        state = "偏多" if sp["score"] > 0 else "偏空"
        parts.append(f"「趨勢跟隨」基金看標普 500 目前<b>{state}</b>（分數 {sp['score']:+.2f}，−1 全空～+1 全多）"
                     + (f"；1 個月趨勢的翻轉點在 {f1['price']:,.0f}（離現在 {_pc(f1['dist'])}）" if f1 else "")
                     + (f"、3 個月在 {f3['price']:,.0f}（{_pc(f3['dist'])}）" if f3 else "") + "。")
    rp = v.get("rp") or {}
    if rp.get("corr60") is not None:
        c = rp["corr60"]
        parts.append(f"股債 60 日相關係數 {c:+.2f}：" + ("股票和公債常同漲同跌，「風險平價」基金兩邊都分散不了風險，波動一大就得兩邊一起減碼。"
                                                     if c > 0.3 else "股債還有互相抵銷的效果，風險平價基金比較不用被迫兩邊一起減碼。"))
    rows = ""
    for s, t in tr.items():
        fl = t.get("flips") or {}
        cell = "".join(f'<td class="r {"up" if (fl.get(str(n)) or fl.get(n) or {}).get("up") else "dn"}">'
                       f'{(fl.get(str(n)) or fl.get(n) or {}).get("price", 0):,.2f}<div class="small muted">{_pc((fl.get(str(n)) or fl.get(n) or {}).get("dist"))}</div></td>'
                       for n in (21, 63, 252))
        rows += (f'<tr><td class="nw"><b>{esc(t["name"])}</b><div class="small muted">{esc(s)}・{esc(t.get("asof", ""))}</div></td>'
                 f'<td class="r {"up" if t["score"] > 0 else "dn"}"><b>{t["score"]:+.2f}</b></td>{cell}</tr>')
    head = (f'<tr><th>{T("市場", "Market")}</th><th class="r">{T("趨勢分數", "Trend score")}</th>'
            f'<th class="r">{T("1 個月翻轉點", "1m flip")}</th><th class="r">{T("3 個月翻轉點", "3m flip")}</th><th class="r">{T("12 個月翻轉點", "12m flip")}</th></tr>')
    note = ("這是照公開規則做的模型估算，不是這些基金實際的部位（它們不公布）。波動控制：目標年化波動 10%，股票比重＝10% ÷ 標普 500 近期實際波動"
            "（1 個月與 3 個月取較高者），最多 150%。趨勢跟隨：每個市場看 1、3、12 個月漲跌的方向（漲＝+1、跌＝−1）取平均；"
            "「翻轉點」＝那麼多天前的收盤價，明天收在它下面（或上面），那個期間的趨勢就翻過來。綠色＝現在價格在翻轉點之上。"
            "這些基金加起來規模很大，同時被迫減碼時會把小跌放大；但規則各家不同，實際影響可能更大或更小。資料：Yahoo 日線。")
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{parts[0] if parts else ""}</p>' + "".join(f"<p>{x}</p>" for x in parts[1:])
            + f'<details><summary>各市場的趨勢翻轉點</summary><div class="scroll"><table class="mini"><thead>{head}</thead><tbody>{rows}</tbody></table></div></details>'
            f'<p class="note">{note}</p>')
    return card("機械式基金：照規則自動增減股票的錢", "Rule-based funds (model estimate)", body, "wide",
                sub="波動控制、趨勢跟隨、風險平價基金現在大概站在哪一邊")


# ------------------------------------------------------------------ 3. 季底再平衡＋12 月節稅賣壓
def _tax_loss(eng) -> List[Dict]:
    try:
        from wsb.data.stocks import universe
        cl = eng.stockprices.close
        us = (universe().get("us") or {}).get("symbols") or {}
    except Exception:  # noqa: BLE001
        return []
    y = date.today().year
    out = []
    for s, (zh, _en) in us.items():
        if s not in cl.columns:
            continue
        x = cl[s].dropna()
        base = x[x.index < f"{y}-01-01"]
        if len(base) and len(x):
            out.append({"sym": s, "zh": zh, "ytd": float(x.iloc[-1] / base.iloc[-1] - 1), "asof": str(x.index[-1].date())})
    return sorted(out, key=lambda r: r["ytd"])


def buyback_window(today: date) -> str:
    """Pure: where we are in the usual corporate buyback blackout cycle (rule of thumb, not company data).
    11-28 Wall Street checklist: buybacks are the largest net buyer of US stocks; most companies stop buying about two
    weeks before quarter-end and resume a day or two after their earnings release (about 3–6 weeks after quarter-end)."""
    q_end = date(today.year, ((today.month - 1) // 3 + 1) * 3, 1)
    q_end = (q_end.replace(day=28) + timedelta(days=4))
    q_end = q_end - timedelta(days=q_end.day)                      # last day of this quarter
    start = q_end - timedelta(days=14)
    prev_end = date(today.year, ((today.month - 1) // 3) * 3, 1) if today.month > 3 else date(today.year - 1, 12, 31)
    if today.month > 3:
        prev_end = (prev_end.replace(day=28) + timedelta(days=4))
        prev_end = prev_end - timedelta(days=prev_end.day)
    reopen = prev_end + timedelta(days=45)
    if today <= reopen:
        return (f"企業買回空窗期：上一季（{prev_end.month} 月底結束）的財報還在陸續公布，很多公司要等自己的財報公布後才能恢復買回自家股票，"
                f"大約到 {_md(reopen.isoformat())} 前後大部分恢復。買回是美股最大的買家之一，空窗期少了這股買盤，跌時比較沒有人接（經驗法則，不是公司資料）。")
    if today >= start:
        return (f"企業買回空窗期：多數公司在季底（{_md(q_end.isoformat())}）前約兩週停止買回自家股票，直到財報公布後才恢復，"
                f"現在已進入這段期間，美股少了最大的買家之一，跌時比較沒有人接（經驗法則，不是公司資料）。")
    return (f"企業買回空窗期：現在多數公司可以買回自家股票（上一季財報已公布完）；約從 {_md(start.isoformat())} 起，"
            f"多數公司會在季底前停止買回，直到 1 月下旬到 2 月初財報公布後才恢復（經驗法則，不是公司資料）。" if q_end.month == 12 else
            f"企業買回空窗期：現在多數公司可以買回自家股票；約從 {_md(start.isoformat())} 起，多數公司會在季底前停止買回（經驗法則，不是公司資料）。")


def sec_rebalance(eng) -> str:
    try:
        v = _view()
    except Exception:  # noqa: BLE001
        return ""
    pm = v.get("pension") or {}
    today = date.today()
    parts = []
    if pm:
        q_end = date.fromisoformat(pm["q_end"])
        mv = pm["move"]
        side = "增加" if mv > 0 else "減少"
        parts.append(f"這一季（{pm['q0'][5:].replace('-', '/')} 起）美股 {_pc(pm['r_eq'])}、美國債券 {_pc(pm['r_bd'])}，"
                     f"退休基金的股票比重從 {pm['w0'] * 100:.1f}% 變成 {pm['w1'] * 100:.1f}%。如果全部照規則調回去，季底前（{_md(pm['q_end'])}，"
                     f"還有 {(q_end - today).days} 天）要<b>{side}約 {abs(mv) / 1e8:,.0f} 億美元</b>的股票。")
    tl = _tax_loss(eng) if today >= date(today.year, 10, 15) else []
    losers = [r for r in tl if r["ytd"] < -0.15]          # all of them (user, 11-17: full data)
    if losers:
        parts.append("年底節稅賣壓：美國投資人常在 12 月賣掉今年虧損的股票來抵稅（30 天內不能買回同一檔，否則不能抵）。"
                     f"追蹤的股票裡今年跌最多的：{'、'.join(esc(r['zh']) + ' ' + _pc(r['ytd'], 0) for r in losers)}。"
                     "台灣人買美股不用繳美國的資本利得稅，所以這是「別人」的賣壓，不是你要跟著做的事。")
    bb = buyback_window(today)
    if bb:
        parts.append(bb)
    if not parts:
        return ""
    note = ("退休基金的股票與總資產來自聯準會金融帳（Z.1，FRED：退休基金持有的公司股票市值、金融資產總額"
            + (f"，最新一季 {esc(pm.get('z1_date', ''))}" if pm else "") + "），季初比重用最新一季的實際比重；股票用 SPY、債券用 AGG 的漲跌近似。"
            "「全部照規則調回去」是上限：很多退休金只在偏離超過一定幅度才調、或分好幾天調，實際金額通常小得多。"
            "節稅名單是本站追蹤的美股今年以來漲跌（以去年最後一個收盤為基準），不是預測誰會被賣。")
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{parts[0]}</p>' + "".join(f"<p>{x}</p>" for x in parts[1:]) + f'<p class="note">{note}</p>')
    return card("季底再平衡與年底節稅賣壓", "Quarter-end rebalancing & year-end tax selling", body, "wide",
                sub="退休金照比例調整股債、美國投資人年底賣虧損股抵稅")


# ------------------------------------------------------------------ 12. 休市與提早收盤
def sec_exchange_cal(eng) -> str:
    try:
        from wsb.data import exchange_cal as XC
        d = XC.load()
        rows = XC.upcoming(date.today(), 75, d)
    except Exception:  # noqa: BLE001
        return ""
    if not rows:
        return ""
    first = rows[0]
    if first["us"] == "closed":
        lead = f"下一個美股休市日是 <b>{_md(first['date'])}{US_HOL_ZH.get(first['us_why'], first['us_why'])}</b>。"
    elif first["us"] == "early":
        lead = f"下一個美股提早收盤是 <b>{_md(first['date'])}（{esc(first['us_why'])}）</b>，台北時間 {esc(first['us_hours'])}。"
    else:
        lead = f"下一個台股休市日是 <b>{_md(first['date'])}（{esc(first['tw_why'])}）</b>，美股照常交易。"
    trs = ""
    for r in rows:
        us = ("休市・" + esc(US_HOL_ZH.get(r["us_why"], r["us_why"])) if r["us"] == "closed"
              else f"提早收盤（{esc(r['us_why'])}）<div class='small muted'>台北 {esc(r['us_hours'])}</div>" if r["us"] == "early" else "照常")
        tw = ("休市・" + esc(r["tw_why"]) if r["tw"] == "closed" else "照常" if r["tw"] == "open" else "官方還沒公布")
        trs += (f'<tr><td class="nw"><b>{_md(r["date"])}</b></td><td class="{"dn" if r["us"] == "closed" else "warn" if r["us"] == "early" else ""}">{us}</td>'
                f'<td class="{"dn" if r["tw"] == "closed" else ""}">{tw}</td></tr>')
    from wsb.data.exchange_cal import us_session_tpe
    now = us_session_tpe(date.today())
    note = (f"美股一般交易時間在台北是 {esc(now)}（美國夏令時間時早一小時，系統自動換算）。美股休市與半天依紐約證交所的固定規則推算"
            "（python-holidays 的 NYSE 行事曆；半天＝感恩節隔天、聖誕夜、7/3，美東 13:00 收盤）；國喪、天災等臨時休市算不出來，以交易所公告為準。"
            f'台股讀證交所官方「<a href="{XC.TW_PAGE}" target="_blank" rel="noopener">市場開休市日期</a>」，'
            "只辦理結算交割、沒有交易的日子也算休市。休市日前後成交量較少，價格容易被少數大單推動。")
    body = (f'<p class="rimp big2"><b>一句話看懂：</b>{lead}</p><div class="scroll"><table class="mini"><thead><tr><th>{T("日期", "Date")}</th>'
            f'<th>{T("美股", "US")}</th><th>{T("台股", "Taiwan")}</th></tr></thead><tbody>{trs}</tbody></table></div><p class="note">{note}</p>')
    return card("休市與提早收盤：美股、台股", "Market holidays & early closes", body, "",
                sub="接下來 75 天，美股或台股沒開、或只開半天的日子")
