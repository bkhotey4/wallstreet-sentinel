"""國安基金官方動態卡（台股專業判讀頁，2026-11-22 台股覆蓋清單「國安基金進出」）。資料與來源見 wsb/data/tw_nsf.py。

國安基金不公布每天買了多少；這張卡只寫官方說過的：委員會決議（啟動／繼續／停止）、新聞稿原文重點、每季收支報表。"""
from __future__ import annotations

import re
from datetime import date
from typing import Dict, List, Optional

from tools.sitekit import card, esc, fold_rows


def episodes(news: List[Dict]) -> List[Dict]:
    """Pair each 啟動 with the next 停止 after it (the list is newest first): start, stop (None = still on), days."""
    from wsb.data.tw_nsf import OFF
    rows = sorted(news, key=lambda r: r["date"])
    out, start = [], None
    for r in rows:
        if re.search(r"啟動安定(市場|金融市場)任務", r["title"]) and start is None:
            start = r["date"]
        elif OFF.search(r["title"]) and start:
            out.append({"start": start, "stop": r["date"], "days": (date.fromisoformat(r["date"]) - date.fromisoformat(start)).days})
            start = None
    if start:
        out.append({"start": start, "stop": None, "days": None})
    return out[::-1]


def next_report(today: date, last: Optional[str]) -> str:
    """Quarterly meetings publish in mid January / April / July / October."""
    for y in (today.year, today.year + 1):
        for m in (1, 4, 7, 10):
            if date(y, m, 15) > today and (not last or f"{y}-{m:02d}" > last[:7]):
                return f"{y} 年 {m} 月中"
    return "—"


# What each kind of 金管會 measure changes mechanically — shown only when the release mentions it.
MECH = [("平盤以下", "禁止平盤以下放空：當天價格低於前一天收盤時不能新放空，跌的日子少了一股賣壓；但券商、期貨商的避險不受限，所以不是「完全沒有人能賣」。"),
        ("融券保證金", "融券保證金提高：放空要先押更多錢，新放空的人會變少，已經放空的人不受影響。"),
        ("認售權證", "暫停發行認售權證：認售權證是「賭下跌」的權證，發行券商要放空股票避險；不再發新的，這種機械性的賣出就少了。"),
        ("庫藏股", "鼓勵庫藏股：公司自己買回股票，是少數「不看價格、照計畫買」的買方；本站「台股財報」頁會列出新公告的庫藏股。"),
        ("召回", "鼓勵出借人召回借出的股票：借券放空的人被要求還股票，就得買回來還——這是被迫的買單，短期可能讓被放空很多的股票反彈（軋空），"
                 "但召回要照契約、分批發生。借券放空餘額每天的變化在「台股專業判讀」頁的籌碼深度卡。"),
        ("借券賣出委託數量", "限制盤中借券放空的數量：每天能借券放空的量變少，大跌日的賣壓上限跟著降低。")]


def _link(u: str, t: str) -> str:
    return f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(t)}</a>'


def sec_tw_nsf(eng=None, today: Optional[date] = None) -> str:
    from wsb.data import tw_nsf as N
    try:
        d = N.refresh()
    except Exception:  # noqa: BLE001
        return ""
    news, st = d.get("news") or [], d.get("status") or {}
    fsc, fb = d.get("fsc") or [], d.get("fsc_bodies") or {}
    if not news and not fsc:
        return ""
    today = today or date.today()
    reps = d.get("reports") or []
    nxt = next_report(today, (reps[0]["date"] if reps else None))
    if st.get("state") == "on":
        lead = (f'國安基金現在是「執行中」：財政部 {st["since"]} 公告委員會決議授權動用資金護盤；'
                f'官方不公布每天買多少，第一次看到金額要等下一份每季報表（約 {nxt}）。')
    elif st.get("state") == "off":
        lead = f'國安基金現在沒有在執行護盤：{st["since"]} 委員會決議停止。下一份每季報表約 {nxt}。'
    else:
        lead = f'國安基金最新官方新聞稿是 {news[0]["date"]}「{news[0]["title"]}」。'
    if fsc:
        eff = re.search(r"自(\d{2,3})年(\d{1,2})月(\d{1,2})日起", fb.get(fsc[0]["url"]) or "")
        lead += (f'金管會最新的市場措施是 {fsc[0]["date"]}「{fsc[0]["title"]}」'
                 + (f'，{int(eff.group(1)) + 1911}-{int(eff.group(2)):02d}-{int(eff.group(3)):02d} 起實施' if eff else "") + "。")
    body_txt = (d.get("bodies") or {}).get(news[0]["url"]) or ""
    paras = [p for p in body_txt.split("\n") if p.strip()][:3]
    fsc_html = ""
    if fsc:
        top = fb.get(fsc[0]["url"]) or ""
        items = [x for x in top.split("\n") if x.strip()]
        mech = [t for k, t in MECH if k in top]
        rows_f = [f'<tr><td>{esc(r["date"])}</td><td>{_link(r["url"], r["title"])}</td></tr>' for r in fsc]
        fsc_html = (f'<h3>金管會市場穩定措施（{_link(fsc[0]["url"], "最新一則原文")}）</h3>'
                    + "".join(f'<p class="small">{esc(x)}</p>' for x in items[:8])
                    + (f'<p class="small"><b>每一項改變了什麼（白話）：</b></p><ul class="small">' + "".join(f"<li>{esc(t)}</li>" for t in mech) + "</ul>" if mech else "")
                    + '<p class="small muted">研究上，2008 年各國禁止放空時，被禁的股票交易變得比較不順（買賣價差變大），但股價沒有因此比較撐'
                      '（Beber 與 Pagano，2013 年《Journal of Finance》）；限空擋得住「新的放空」，擋不住融資斷頭和外資賣超。</p>'
                    + fold_rows(rows_f, 4, '<tr><th>發布日期</th><th>金管會新聞稿</th></tr>', "則"))
    ep = episodes(news)
    ep_rows = "".join(f'<tr><td>{esc(e["start"])}</td><td>{esc(e["stop"] or "執行中")}</td>'
                      f'<td class="r">{"—" if e["days"] is None else e["days"]}</td></tr>' for e in ep)
    th = '<tr><th>發布日期</th><th>新聞稿</th></tr>'
    rows = [f'<tr><td>{esc(r["date"])}</td><td>{_link(r["url"], r["title"])}</td></tr>' for r in news]
    rep = "".join(f'<li>{esc(r["title"])}（{esc(r["date"])}）'
                  + "".join(f'　{_link(r[k], k.upper())}' for k in ("pdf", "xls") if r.get(k)) + "</li>" for r in reps[:3])
    body = (f'<p class="rimp"><b>一句話看懂：{esc(lead)}</b></p>' + fsc_html + '<h3>國安基金</h3>'
            + (f'<p class="small"><b>最新新聞稿原文重點（{esc(news[0]["date"])}，{_link(news[0]["url"], "財政部原文")}）：</b></p>'
               + "".join(f'<p class="small">{esc(p)}</p>' for p in paras) if paras else "")
            + '<p class="small">國安基金是政府的護盤基金：股市「失序」時委員會可以授權買股。它進場代表政府認為恐慌過頭，'
              '但不保證止跌：決議當天的指數與外資賣超見上面原文，之後的走勢看「台股」頁。'
              '真正要看的是賣的力量有沒有變小——外資賣超有沒有縮小、融資斷頭有沒有結束；國安基金只是其中一股買的力量。</p>'
            + (f'<h3>歷次執行期間（從新聞稿配對）</h3><div class="scroll"><table class="mini"><thead><tr><th>啟動</th><th>停止</th>'
               f'<th class="r">天數</th></tr></thead><tbody>{ep_rows}</tbody></table></div>' if ep_rows else "")
            + '<h3>官方新聞稿</h3>' + fold_rows(rows, 6, th, "則")
            + (f'<h3>每季收支及資產負債表（官方唯一的金額）</h3><ul class="small">{rep}</ul>' if rep else "")
            + f'<p class="note">來源：財政部「國家金融安定基金訊息」專區，{_link(N.U_NEWS, "新聞稿")}、{_link(N.U_REPORT, "每季報表")}。'
              f'；金管會<a href="{N.U_FSC}" target="_blank" rel="noopener noreferrer">新聞稿列表</a>（只收放空、融券、借券、市場秩序等措施）。'
              f'抓取 {esc(d.get("fetched") or "—")}。媒體說的「國安基金進場買了多少」不是官方數字，本站不列。</p>')
    return card("政府穩市場：金管會措施與國安基金", "Market stabilization: FSC measures and the National Stabilization Fund", body, "wide")
