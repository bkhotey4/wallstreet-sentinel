"""MSCI 台灣指數卡（台股專業判讀頁，2026-11-22 台股覆蓋清單「指數調整（MSCI）」）。資料見 wsb/data/tw_msci.py。

成分股用追蹤 MSCI臺灣指數的元大 006203 每日持股近似；生效日用 wsb/data/forced_flows.index_dates 的規則（和「被迫買賣」頁同一套）。
審查公布的增刪名單在 MSCI 官網（機器人驗證，本站不繞過），所以這裡只寫「生效後持股實際變了什麼」。"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from tools.sitekit import card, esc, fold_rows

SRC = "https://www.yuantaetfs.com/product/detail/006203/ratio"


def reviews(today: date) -> Dict[str, Optional[Dict]]:
    """The most recent past and the next MSCI quarterly-review effective day (US date and the Taiwan trading day)."""
    try:
        from wsb.data import forced_flows as FF
        us, tw, ec = FF._opens()
        ev = [e for e in FF.index_dates(today.year - 1, today.year + 1, us, tw, ec) if e["kind"] == "msci"]
    except Exception:  # noqa: BLE001
        return {"last": None, "next": None}
    past = [e for e in ev if e["tw_date"] < today.isoformat()]
    nxt = [e for e in ev if e["tw_date"] >= today.isoformat()]
    return {"last": past[-1] if past else None, "next": nxt[0] if nxt else None}


def sec_tw_msci(eng=None, today: Optional[date] = None) -> str:
    from wsb.data import tw_msci as M
    try:
        d = M.refresh()
    except Exception:  # noqa: BLE001
        return ""
    snaps = d.get("snaps") or {}
    if not snaps:
        return ""
    today = today or date.today()
    day = max(snaps)
    cur = snaps[day].get("stocks") or {}
    rv = reviews(today)
    nx, ls = rv.get("next"), rv.get("last")
    ch = M.changes(snaps, around=ls["tw_date"]) if ls else {}
    top = sorted(cur.items(), key=lambda kv: -kv[1][1])
    top5 = sum(w for _, (_, w) in top[:5])
    parts = [f'MSCI 台灣指數現在約 {len(cur)} 檔（用追蹤它的 006203 在 {day} 的持股近似），台積電一檔占 {top[0][1][1]:.1f}%、前 5 大合計 {top5:.1f}%']
    if nx:
        days_to = (date.fromisoformat(nx["tw_date"]) - today).days
        parts.append(f'下一次季度審查 {nx["tw_date"]} 台股收盤生效（還有 {days_to} 天），全球追蹤 MSCI 的基金會在那天收盤一起調整')
    if ch and (ch.get("add") or ch.get("rem")):
        parts.append(f'上一次審查（{ls["tw_date"]}）前後持股實際加入 {len(ch["add"])} 檔、刪除 {len(ch["rem"])} 檔')
    body = [f'<p class="rimp"><b>一句話看懂：{esc("；".join(parts))}。</b></p>',
            '<p class="small">MSCI 指數是全球很多被動基金與外資的「台股地圖」：被加進去，追蹤它的錢就得在生效日收盤買；被刪掉就得賣。'
            '台積電占比這麼高，代表外資照 MSCI 配置台股時，有一半以上其實是在買賣台積電；'
            'MSCI 也會調整台灣在新興市場指數裡的比重，那一天外資的台股買賣超常常特別大，但那是規則逼出來的，不代表看法改變。</p>']
    if ch and (ch.get("add") or ch.get("rem")):
        li = lambda xs: "、".join(f'{x["name"]}（{x["code"]}，{x["w"]:.2f}%）' for x in xs) or "無"  # noqa: E731
        body.append(f'<h3>上一次審查實際變動（{esc(ch["from"])} → {esc(ch["to"])} 的持股差異）</h3>'
                    f'<p class="small"><b>加入：</b>{esc(li(ch["add"]))}</p><p class="small"><b>刪除：</b>{esc(li(ch["rem"]))}</p>')
    elif ls:
        body.append(f'<p class="small muted">上一次審查（{esc(ls["tw_date"])}）前後的持股快照本站還沒存到，下一次審查生效後會自動列出加入／刪除的公司。</p>')
    th = '<tr><th>#</th><th>公司</th><th class="r">權重</th></tr>'
    rows = [f'<tr><td>{i}</td><td>{esc(n)}（{esc(c)}）</td><td class="r">{w:.2f}%</td></tr>' for i, (c, (n, w)) in enumerate(top, 1)]
    body.append(f'<h3>成分股與權重（{esc(day)}）</h3>' + fold_rows(rows, 10, th, "檔"))
    body.append(f'<p class="note">來源：<a href="{SRC}" target="_blank" rel="noopener noreferrer">元大 MSCI台灣 ETF（006203）每日持股</a>（發行投信公開；'
                'ETF 持股因申贖、現金與期貨部位和指數權重有小差異）。生效日依 MSCI 規則：2、5、8、11 月最後一個交易日收盤（美國感恩節隔天半天時改那週週一）。'
                f'MSCI 官網的審查公告有機器人驗證，本站不繞過。抓取 {esc(d.get("fetched") or "—")}。描述資料，不是建議。</p>')
    return card("MSCI 台灣指數：成分股與季度審查", "MSCI Taiwan constituents and reviews", "".join(body), "wide")
