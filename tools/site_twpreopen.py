"""台股頁：台股開盤前預估＋被迫賣方（2026-11-20）。資料與計算在 wsb/data/tw_preopen.py；這裡只講成白話。
11/20 加權指數 −6.23% 那天，主角是融資斷頭、權證避險與槓桿 ETF 調整，不是外資；這張卡每天先把它們算好，
讓使用者不用再問「明天會怎樣」。全部是換算或官方數字，不預測、不建議。"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Dict, Optional

from tools.sitekit import T, card, esc, fold_rows

WD = "一二三四五六日"
TPE = timezone(timedelta(hours=8))


def _md(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.month}/{d.day}（{WD[d.weekday()]}）"


def _s(x: Optional[float], d: int = 1) -> str:
    return "—" if x is None else f"{x:+,.{d}f}"


def _hm(t: Optional[float]) -> str:
    return datetime.fromtimestamp(t, TPE).strftime("%m/%d %H:%M") if t else "時間不明"


def _cut() -> str:
    """Disposal days before this date are over: today until the 13:30 close, tomorrow after it."""
    n = datetime.now(TPE)
    return (n.date() + timedelta(days=1 if (n.hour, n.minute) >= (13, 30) else 0)).isoformat()


def lead(v: Dict) -> str:
    a, m, lv = v.get("adr"), (v.get("mg") or [None])[-1], v.get("lev")
    parts = []
    if a:
        side = "比台股本尊貴" if a["now"] >= 0 else "比台股本尊便宜"
        rel = ("比平常低很多" if a["pct"] <= 15 else "比平常高很多" if a["pct"] >= 85 else "在平常範圍")
        parts.append(f"台積電 ADR 換算後{side} {abs(a['now']):.1f}%，{rel}（近一年第 {a['pct']} 百分位，中位數 {a['med_1y']:.1f}%）；"
                     f"如果溢價回到近 20 天的常態，換算 2330 約 {a['lo']:,.0f}～{a['hi']:,.0f} 元（中間值 {a['mid']:,.0f}，"
                     f"比 {_md(a['tw'][0])} 收盤 {_s(a['chg_mid'])}%）")
    if m:
        parts.append(f"融資 {_md(m['d'])} 一天{'減少' if m['diff'] < 0 else '增加'} {abs(m['diff']):,.0f} 億元（{_s(m['pct'])}% {m['light']}）")
    cal = [c for c in v.get("cal") or [] if c["dispose"] >= _cut()]
    if cal:
        parts.append("追繳後的處分日落在 " + "、".join(_md(c["dispose"]) for c in cal))
    if lv:
        parts.append(f"00631L 收盤前估計要{'增加' if lv['trade'] > 0 else '減少'}約 {abs(lv['trade']):,.0f} 億元的期貨部位")
    return "一句話看懂：" + ("；".join(parts) if parts else "開盤前資料暫時取不到。") + "。"


def body(v: Dict) -> str:
    out = [f'<p class="rimp big2"><b>{T(esc(lead(v)), "")}</b></p>']
    a = v.get("adr")
    if a:
        out.append(
            f'<h3>{v["adr_light"]} 台積電 ADR 溢價</h3>'
            f'<p class="small">ADR {a["adr"][1]:,.2f} 美元（美股 {_md(a["adr"][0])}，報價時間 {_hm(v.get("adr_t"))} 台北）÷ 5 股 × 美元兌台幣 {a["fx"][1]:.3f}（{_md(a["fx"][0])}）'
            f' = 每股 {a["x"]:,.1f} 元；2330 收盤 {a["tw"][1]:,.1f} 元（{_md(a["tw"][0])}）→ 溢價 {_s(a["now"], 2)}%。</p>'
            f'<p class="small">近一年（{esc(a["since"])} 起 {a["n_1y"]} 個交易日）中位數 {a["med_1y"]:.2f}%，今天在第 {a["pct"]} 百分位；'
            f'近 20 個交易日溢價的四分位 {a["q25"]:.2f}%／{a["med20"]:.2f}%／{a["q75"]:.2f}%。</p>'
            f'<p class="small">換算：2330 ≈ {a["x"]:,.1f} ÷ (1 + 溢價)。溢價回到 {a["q75"]:.2f}% → {a["lo"]:,.1f} 元；{a["med20"]:.2f}% → {a["mid"]:,.1f} 元；'
            f'{a["q25"]:.2f}% → {a["hi"]:,.1f} 元。溢價不一定回到常態，台股開盤還受融資斷頭、國安基金與當天消息影響，這只是換算，不是預測。</p>'
            '<p class="note">燈號（自訂）：溢價在自己近一年的第 5 百分位以下或 95 以上為 🔴，15 以下或 85 以上為 🟡。'
            '溢價偏低代表美國這邊跌得比台股多（台股還沒反映），偏高代表台股跌得比美國多。</p>')
    night = v.get("night") or []
    if night:
        rows = [f'<tr><td>{esc(n["n"])}</td><td class="r">{n["p"]:,.2f}</td><td class="r {"up" if n["chg"] > 0 else "dn" if n["chg"] < 0 else ""}">{_s(n["chg"], 2)}%</td>'
                f'<td>{_md(n["d"])}・{_hm(n.get("t"))}</td></tr>' for n in night]
        out.append("<h3>隔夜與亞洲</h3>" + fold_rows(rows, 6, "<tr><th>項目</th><th class='r'>價格</th><th class='r'>漲跌</th><th>資料日期・報價時間（台北）</th></tr>", "項"))
    mg = v.get("mg") or []
    if mg:
        rows = [f'<tr><td>{_md(m["d"])}</td><td class="r">{m["prev"]:,.1f}</td><td class="r">{m["now"]:,.1f}</td>'
                f'<td class="r {"dn" if m["diff"] < 0 else "up"}">{_s(m["diff"])}</td><td class="r">{_s(m["pct"], 2)}% {m["light"]}</td></tr>' for m in reversed(mg)]
        out.append(f'<h3>融資餘額（借錢買股，億元）</h3>' + fold_rows(rows, 5, "<tr><th>日期</th><th class='r'>前一天</th><th class='r'>當天</th><th class='r'>增減</th><th class='r'>單日 %</th></tr>", "天")
                   + f'<p class="note">來源：<a href="{esc(SRC_MG)}" target="_blank" rel="noopener">證交所信用交易統計（MI_MARGN）</a>，約晚上 9 點公布。燈號（自訂）：單日減 5% 以上 🔴、2.5% 以上 🟡。</p>')
    cal = v.get("cal") or []
    if cal:
        today = _cut()
        rows = [f'<tr><td>{_md(c["d"])}</td><td class="r">{_s(c["ix"], 2)}%</td><td class="r">{_s(c["mg"], 2)}%</td>'
                f'<td>{_md(c["topup"])}</td><td>{_md(c["dispose"])}{"（已過）" if c["dispose"] < today else ""}</td></tr>' for c in reversed(cal)]
        out.append("<h3>追繳與處分日曆（大跌日之後）</h3>"
                   + fold_rows(rows, 5, "<tr><th>大跌日 T</th><th class='r'>加權指數</th><th class='r'>融資</th><th>補繳期限 T+2</th><th>處分 T+3 起</th></tr>", "天")
                   + f'<p class="note">規則：整戶擔保維持率低於 130%，券商在 T 日收盤後通知，T+2 日前要補繳，沒補的從 T+3 日起可以處分（<a href="{esc(SRC_RULE)}" target="_blank" rel="noopener">證交所說明，2026-07 報導</a>）。'
                   '交易日已扣掉證交所休市日。列入條件：加權指數單日跌 2% 以上或融資單日減 2.5% 以上。不知道有多少人被追繳，只知道時間。</p>')
    b = v.get("bfi") or []
    if b:
        rows = [f'<tr><td>{_md(x["d"])}</td><td class="r">{_s(x.get("hedge"))}</td><td class="r">{_s(x.get("self"))}</td>'
                f'<td class="r">{_s(x.get("trust"))}</td><td class="r">{_s(x.get("foreign"))}</td><td class="r">{_s(x.get("total"))}</td></tr>' for x in reversed(b)]
        out.append("<h3>誰在買、誰在賣（億元，正數＝買超）</h3>"
                   + fold_rows(rows, 5, "<tr><th>日期</th><th class='r'>自營商避險</th><th class='r'>自營商自行</th><th class='r'>投信</th><th class='r'>外資</th><th class='r'>合計</th></tr>", "天")
                   + f'<p class="note">來源：<a href="{esc(SRC_BFI)}" target="_blank" rel="noopener">證交所三大法人買賣金額（BFI82U）</a>。'
                   '自營商避險多半是權證發行商跟著權證價值調整持股，是機械性的動作，不代表看法。</p>')
    lv = v.get("lev")
    if lv:
        out.append(f'<h3>槓桿 ETF 收盤前調整（估計）</h3><p class="small">{esc(lv["name"])}（{esc(lv["code"])}）每天重設成 {lv["lev"]:.0f} 倍：'
                   f'{_md(lv["date"])} 標的（用 0050 淨值）{_s(lv["r"], 2)}%，前一天規模約 {lv["size"]:,.0f} 億元 → '
                   f'{lv["lev"]:.0f}×({lv["lev"]:.0f}−1)×{_s(lv["r"], 2)}%×{lv["size"]:,.0f} ≈ {_s(lv["trade"], 0)} 億元的期貨部位要在收盤前調整'
                   f'（跌的日子減少部位、漲的日子增加部位，會放大當天收盤前的走勢）。</p>'
                   f'<p class="note">規模與淨值來自<a href="{esc(SRC_ETF)}" target="_blank" rel="noopener">證交所 ETF 即時淨值檔</a>（發行商估計淨值）；'
                   '實際調整金額、時間與工具（期貨或股票）以發行商為準，這是估計。</p>')
    out.append(f'<p class="note">報價更新 {_hm(v.get("px_ts"))}（台北，Yahoo）；證交所資料更新 {_hm(v.get("ts"))}。不構成投資建議。</p>')
    return "".join(out)


SRC_MG = "https://www.twse.com.tw/zh/trading/margin/mi-margn.html"
SRC_BFI = "https://www.twse.com.tw/zh/trading/foreign/bfi82u.html"
SRC_ETF = "https://mis.twse.com.tw/stock/data/all_etf.txt"
SRC_RULE = "https://money.udn.com/money/story/5607/9658938"


def sec_tw_preopen(eng=None) -> str:
    try:
        from wsb.data import tw_preopen as P
        v = P.view()
    except Exception:  # noqa: BLE001
        return ""
    if not (v.get("adr") or v.get("mg")):
        return ""
    return card("台股開盤前預估＋被迫賣方", "Taiwan pre-open read and forced sellers", body(v), "wide")
