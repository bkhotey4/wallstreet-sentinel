"""研究機構最新報告（產業體檢）：TrendForce 新聞稿 × 相關股票報告後的反應（2026-11-26，wsb/data/research_press）。

使用者 11/26 拿「中國減單、北美加單：TrendForce 和 Sandisk 各自看到了什麼」來問，本站一週一次的產業筆記沒有寫到。
這張卡每 3 小時讀 TrendForce 新聞稿列表，每份報告列出主要產業、標題方向、相關股票在報告後第一個交易日「比大盤多漲／多跌」
多少，讓讀者分得出是這個產業自己在動，還是整個市場一起動（11/26 台股大漲是關稅不疊加，不是記憶體報告）。
漲跌不等於報告造成的，卡上寫明。英文導言折疊在下面；判讀以原文為準。"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from tools.sitekit import card, esc, fold_rows

DIR_ZH = {"down": "標題：價格／需求往下", "up": "標題：價格／需求往上"}
BENCH = {"tw": "^TWII", "us": "^GSPC"}


def _day_move(close, sym: str, day: str):
    """(trading date, % move that day, % from the day before to the latest close) for the first trading day after a report:
    US = the report day itself (TrendForce publishes in Taipei daytime, before the US open); Taiwan = the next day."""
    if close is None or sym not in getattr(close, "columns", []):
        return None
    s = close[sym].dropna()
    if len(s) < 3:
        return None
    d = date.fromisoformat(day)
    tw = sym.endswith(".TW") or sym.endswith(".TWO") or sym == "^TWII"
    idx = [i for i, t in enumerate(s.index) if (t.date() > d if tw else t.date() >= d)]
    if not idx or idx[0] == 0:
        return None
    i = idx[0]
    return s.index[i], (s.iloc[i] / s.iloc[i - 1] - 1) * 100, (s.iloc[-1] / s.iloc[i - 1] - 1) * 100


def reaction(close, sym: str, day: str) -> Optional[Dict]:
    """Pure: the stock's move on that day, the same day's index move, and the gap (stock − index)."""
    m = _day_move(close, sym, day)
    if not m:
        return None
    t, pct, since = m
    b = BENCH["tw" if sym.endswith((".TW", ".TWO")) else "us"]
    bm = None
    if close is not None and b in close.columns:
        s = close[b].dropna()
        if t in s.index:
            j = list(s.index).index(t)
            bm = (s.iloc[j] / s.iloc[j - 1] - 1) * 100 if j > 0 else None
    return {"day": t.strftime("%m-%d"), "pct": pct, "since": since, "bench": bm, "excess": None if bm is None else pct - bm}


def rows_of(items: List[Dict], close, names: Dict[str, str]) -> List[Dict]:
    out = []
    for x in items:
        rs = []
        for s in x.get("syms") or []:
            if s in names:
                r = reaction(close, s, x["date"])
                if r:
                    rs.append({"sym": s, "zh": names[s], **r})
        ex = [r["excess"] for r in rs if r["excess"] is not None]
        out.append({**x, "react": rs, "avg_ex": sum(ex) / len(ex) if ex else None})
    return out


def _lead(rows: List[Dict], today: Optional[date] = None, days: int = 14) -> str:
    today = today or date.today()
    recent = [r for r in rows if (today - date.fromisoformat(r["date"])).days <= days]
    if not recent:
        return "一句話看懂：最近兩週 TrendForce 沒有新的新聞稿。"
    tagged = [r for r in recent if r.get("react") and r.get("avg_ex") is not None]
    if not tagged:
        return f"一句話看懂：最近兩週 TrendForce 發了 {len(recent)} 份新聞稿，和本站追蹤股票對得上的還沒有收盤資料。"
    top = max(tagged, key=lambda r: abs(r["avg_ex"]))
    side = "多跌" if top["avg_ex"] < 0 else "多漲"
    s = (f"一句話看懂：最近兩週 TrendForce 發了 {len(recent)} 份新聞稿；相關股票反應最大的是 {top['date'][5:]} 的"
         f"「{'、'.join(top.get('topics') or ['其他'])}」報告（{DIR_ZH.get(top.get('dir'), '標題沒有明確方向')}），"
         f"相關股票報告後第一個交易日平均比大盤{side} {abs(top['avg_ex']):.1f} 個百分點。")
    if abs(top["avg_ex"]) < 2:
        s += "差距在 2 個百分點以內，比較像跟著大盤動，看不出市場特別在意這份報告。"
    elif (top.get("dir") == "down") != (top["avg_ex"] < 0) and top.get("dir"):
        s += "股價方向和報告方向相反，當天可能有別的消息蓋過報告，不能說是報告造成的。"
    else:
        s += "方向和報告一致；研究機構的報價預測會改變市場對明年毛利的想像，相關股票常在財報前就先反應（同一天也可能有別的消息）。"
    return s


def sec_research_press(eng) -> str:
    from wsb.data import research_press as RP
    from wsb.data.stocks import StockPrices, universe
    d = RP.load()
    items = [x for x in d.get("items") or [] if x.get("date")]
    if not items:
        return ""
    names = {}
    for m in universe().values():
        names.update({s: v[0] for s, v in (m.get("symbols") or {}).items()})
    try:
        close = StockPrices().close
    except Exception:  # noqa: BLE001
        close = None
    rows = rows_of(items[:20], close, names)
    trs = []
    for r in rows:
        cells = []
        for x in r["react"]:
            ex = "" if x["excess"] is None else f'，比大盤 {x["excess"]:+.1f}'
            cells.append(f'{esc(x["zh"])} <b>{x["pct"]:+.1f}%</b>（{x["day"]}{ex}；到現在 {x["since"]:+.1f}%）')
        react = "、".join(cells) or "—"
        lead = (f'<details class="sgx"><summary class="small">英文導言</summary><p class="small">{esc(r.get("lead") or "")}</p></details>'
                if r.get("lead") else "")
        trs.append(f'<tr><td class="nw">{esc(r["date"][5:])}</td><td><a href="{esc(r["url"])}" target="_blank" rel="noopener">{esc(r["title"])}</a>{lead}</td>'
                   f'<td class="small">{esc("、".join(r.get("topics") or ["其他"]))}<div class="muted">{esc(DIR_ZH.get(r.get("dir"), ""))}</div></td>'
                   f'<td class="small">{react}</td></tr>')
    head = '<tr><th>日期</th><th>報告（原文）</th><th>主要產業／標題方向</th><th>相關股票：報告後第一個交易日（比大盤；到現在）</th></tr>'
    note = ("來源：TrendForce（集邦科技）官方新聞稿列表，每 3 小時讀一次。主要產業由標題關鍵字對到本站追蹤名單（只取第一個對到的產業）；"
            "「標題方向」只看標題用字（例如 Decline、Cut＝往下；Rise、Shortage＝往上），內容以原文為準。"
            "美股用報告當天收盤（TrendForce 在台北白天發布，早於美股開盤），台股用隔天收盤（發布時間不一定在收盤前）；"
            "「比大盤」＝個股漲跌減同一天加權指數或標普 500 的漲跌，用來分辨是產業自己動還是整個市場一起動。"
            "同一天可能還有別的消息，漲跌不等於報告造成的。")
    return card("研究機構最新報告（TrendForce）", "Research house releases",
                f'<p class="rimp big2"><b>{esc(_lead(rows))}</b></p>' + fold_rows(trs, 8, head, "份") + f'<p class="note">{note}</p>', "wide")
