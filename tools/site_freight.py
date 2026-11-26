"""貨櫃運價卡（產業體檢）：SCFI 綜合指數 × 長榮／陽明／萬海同一週的股價（2026-11-26，wsb/data/freight）。

先講對讀者的意思：貨櫃航運公司的獲利幾乎直接跟著運價走；運價連跌、航運股卻沒跌，代表市場在等別的消息（例如航道或關稅），
反過來也一樣。週數不夠時直說，不硬算長期變化。"""
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from tools.sitekit import card, esc

SHIPS = (("2603.TW", "長榮"), ("2609.TW", "陽明"), ("2615.TW", "萬海"))


def change(h: List, weeks: int) -> Optional[float]:
    """Pure: % change vs the newest point at least `weeks` weeks before the latest one; None if history is shorter."""
    if len(h or []) < 2:
        return None
    end = date.fromisoformat(h[-1][0])
    old = [x for x in h if (end - date.fromisoformat(x[0])).days >= weeks * 7]
    return (h[-1][1] / old[-1][1] - 1) * 100 if old and old[-1][1] else None


def week_move(close, sym: str, start: str, end: str) -> Optional[float]:
    """Pure: the stock's % move from the last close on or before `start` to the last close on or before `end`."""
    if close is None or sym not in getattr(close, "columns", []):
        return None
    s = close[sym].dropna()
    a = s[s.index.date <= date.fromisoformat(start)]
    b = s[s.index.date <= date.fromisoformat(end)]
    if a.empty or b.empty or a.index[-1] == b.index[-1]:
        return None
    return (b.iloc[-1] / a.iloc[-1] - 1) * 100


def sec_freight(eng) -> str:
    from wsb.data import freight as F
    d = F.load()
    h = d.get("scfi") or []
    if len(h) < 1:
        return ""
    last = h[-1]
    w1, w4, w13 = change(h, 1), change(h, 4), change(h, 13)
    try:
        from wsb.data.stocks import StockPrices
        close = StockPrices().close
    except Exception:  # noqa: BLE001
        close = None
    start = h[-2][0] if len(h) >= 2 else (date.fromisoformat(last[0]) - timedelta(days=7)).isoformat()
    moves = [(zh, week_move(close, s, start, last[0])) for s, zh in SHIPS]
    mv = "、".join(f"{zh} {m:+.1f}%" for zh, m in moves if m is not None)
    lead = f"一句話看懂：上海出口貨櫃運價指數 SCFI {last[0][5:]} 為 {last[1]:,.0f} 點" + (f"，比上週 {w1:+.1f}%" if w1 is not None else "") + "。"
    if mv:
        avg = sum(m for _, m in moves if m is not None) / len([m for _, m in moves if m is not None])
        lead += f"同一週航運股：{mv}。"
        bench = week_move(close, "^TWII", start, last[0])
        if bench is not None and abs(bench) >= 2 and (bench > 0) == (avg > 0) and abs(avg) >= 2:
            # 11-26: SCFI −1.9% while the three fell 9–12% — in a week the TAIEX itself fell 17.5%
            gap = avg - bench
            lead += (f"加權指數同一週 {bench:+.1f}%，航運股平均比大盤{'多' if (gap < 0) == (bench < 0) else '少'}"
                     f"{'跌' if bench < 0 else '漲'} {abs(gap):.1f} 個百分點：這週的漲跌主要是整個市場一起動，運價本身只動了"
                     + (f" {w1:+.1f}%。" if w1 is not None else "一點。"))
        elif w1 is not None and abs(w1) >= 1 and (w1 > 0) != (avg > 0) and abs(avg) >= 1:
            lead += "股價和運價反方向，代表市場這週在看運價以外的消息（航道、關稅、配息），不是運價本身。"
        else:
            lead += "貨櫃航運的獲利幾乎直接跟著運價走，運價方向通常就是航運股獲利預期的方向。"
    rows = [("本週", f"{last[1]:,.1f}", last[0])] + [(f"{n} 週前比", "—" if c is None else f"{c:+.1f}%", "")
                                                     for n, c in ((1, w1), (4, w4), (13, w13))]
    tbl = ('<div class="scroll"><table class="mini"><tbody>' + "".join(f'<tr><td>{esc(a)}</td><td class="num"><b>{esc(b)}</b></td>'
                                                                      f'<td class="small muted">{esc(c)}</td></tr>' for a, b, c in rows)
           + '</tbody></table></div>')
    note = ("來源：上海航運交易所 SCFI 綜合指數（每週五公布；分航線運價要登入，本站只讀公開的綜合指數）。"
            f"本站從 2026-11 開始自己存每週數字，目前 {len(h)} 週；4 週、13 週變化要累積夠才會出現。"
            "航運股漲跌用證交所收盤，從上週公布日到本週公布日。")
    return card("貨櫃運價 SCFI × 航運股", "Container freight (SCFI)",
                f'<p class="rimp big2"><b>{esc(lead)}</b></p>' + tbl + f'<p class="note">{note}</p>', "")
