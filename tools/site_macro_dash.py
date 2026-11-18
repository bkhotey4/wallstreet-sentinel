"""每日總經情勢的「數字儀表」與「接下來 72 小時」（2026-11-18，使用者：「每日總經可以再多補充的吧」）。

語音稿是 AI 寫的解讀；這裡是程式直接從本站資料算出來的數字，讓解讀有對照：
  * 12 個總經指標：當天、5 天變化，和自己過去一年「平常一天」的波動比（≥ 2 倍標 ⚡），一句白話說明它代表什麼
  * 接下來 72 小時：讀 upcoming.json 同一份清單（財報、總經、IPO、指數調整），台北時間
描述現況，不是預測，也不是投資建議。"""
from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

TPE = timezone(timedelta(hours=8))

# (ticker, 中文, kind: pct | bp (yields quoted in %), what a rise means)
ITEMS = [
    ("^TNX", "美國 10 年期殖利率", "bp", "升＝借錢變貴，房貸、成長股與債券價格承壓"),
    ("DX-Y.NYB", "美元指數", "pct", "升＝資金偏保守，新台幣與新興市場通常走弱"),
    ("TWD=X", "美元兌新台幣", "pct", "升＝新台幣貶值，外資可能在賣台股"),
    ("JPY=X", "美元兌日圓", "pct", "急跌＝日圓急升，借日圓去投資的錢可能被迫平倉"),
    ("BZ=F", "布蘭特原油", "pct", "升＝通膨壓力變大，央行更難降息"),
    ("GC=F", "黃金", "pct", "升＝避險需求或實質利率下降"),
    ("HG=F", "銅", "pct", "升＝市場看好全球製造與基建需求"),
    ("^VIX", "VIX 恐慌指數", "pct", "升＝市場預期未來 30 天波動變大，越高越緊張"),
    ("HYG", "高收益債 ETF", "pct", "跌＝借錢給體質較弱公司的人在擔心違約"),
    ("^GSPC", "標普 500", "pct", "美國大型股的整體表現"),
    ("^SOX", "費城半導體", "pct", "AI 與晶片族群的溫度計，台股電子股常跟著動"),
    ("^TWII", "台股加權", "pct", "台灣股市整體表現"),
]


def _row(s, kind: str) -> Optional[Dict]:
    import numpy as np
    s = s.dropna()
    s = s[s > 0]
    if len(s) < 60:
        return None
    last, prev = float(s.iloc[-1]), float(s.iloc[-2])
    p5 = float(s.iloc[-6]) if len(s) > 6 else None
    if kind == "bp":
        d1, d5 = (last - prev) * 100, ((last - p5) * 100 if p5 else None)
        hist = s.diff().dropna().tail(252) * 100
    else:
        d1, d5 = (last / prev - 1) * 100, ((last / p5 - 1) * 100 if p5 else None)
        hist = (s.pct_change(fill_method=None).dropna().tail(252)) * 100
    sd = float(np.std(hist)) if len(hist) > 30 else None
    return {"last": last, "d1": d1, "d5": d5, "sd": sd, "k": abs(d1) / sd if sd else None, "date": s.index[-1].strftime("%m-%d")}


def rows(eng) -> List[Dict]:
    out = []
    for sym, zh, kind, why in ITEMS:
        try:
            r = _row(eng.market.series(sym), kind)
        except Exception:  # noqa: BLE001
            r = None
        if r:
            out.append({"sym": sym, "zh": zh, "kind": kind, "why": why, **r})
    return out


def _fmt(r: Dict) -> str:
    u = "bp" if r["kind"] == "bp" else "%"
    lv = f'{r["last"]:.2f}%' if r["kind"] == "bp" else (f'{r["last"]:,.2f}' if r["last"] < 1000 else f'{r["last"]:,.0f}')
    d1 = "0.0" if round(r["d1"], 1) == 0 else f'{r["d1"]:+.1f}'
    d5 = "—" if r["d5"] is None else ("0.0" if round(r["d5"], 1) == 0 else f'{r["d5"]:+.1f}')
    flag = " ⚡" if (r.get("k") or 0) >= 2 else ""
    sd = f'±{r["sd"]:.1f}{u}' if r.get("sd") else "—"
    return (f'<tr><td><b>{html.escape(r["zh"])}</b>{flag}<div class="small muted">{html.escape(r["why"])}</div></td>'
            f'<td class="r">{lv}</td><td class="r"><b>{d1}{u}</b></td><td class="r">{d5}{u if r["d5"] is not None else ""}</td>'
            f'<td class="r small muted">{sd}</td><td class="r small muted">{r["date"]}</td></tr>')


def ahead(eng, hours: int = 72) -> List[Dict]:
    try:
        from tools import site_events as SEV
        now = datetime.now(TPE)
        items = SEV.upcoming(eng, now, days=4).get("items") or []
        end = (now + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
        return [x for x in items if now.strftime("%Y-%m-%d %H:%M") <= x["tpe"] <= end]
    except Exception:  # noqa: BLE001
        return []


def block(eng) -> str:
    rs = rows(eng)
    if not rs:
        return ""
    hot = [r for r in rs if (r.get("k") or 0) >= 2]
    lead = ("今天動得比平常大（超過平常一天的 2 倍）：" + "、".join(f'{r["zh"]} {r["d1"]:+.1f}{"bp" if r["kind"] == "bp" else "%"}' for r in hot)
            if hot else "今天沒有一項總經指標動得比平常大（都在平常一天的 2 倍以內）。")
    tbl = ('<div class="scroll"><table class="mini"><thead><tr><th>指標</th><th class="r">現在</th><th class="r">當天</th><th class="r">5 天</th>'
           '<th class="r">平常一天</th><th class="r">資料日</th></tr></thead><tbody>' + "".join(_fmt(r) for r in rs) + "</tbody></table></div>")
    up = ahead(eng)
    kind_zh = {"earnings": "財報", "macro": "數據", "ipo": "上市", "index": "指數調整"}
    ul = "".join(f'<li><b>{html.escape(x["tpe"][5:].replace("-", "/"))}</b>・{kind_zh.get(x["kind"], "")}・{html.escape(x["zh"])}</li>' for x in up)
    nxt = (f'<h3>接下來 72 小時（台北時間）</h3><ul class="small">{ul}</ul>' if ul else '<p class="small muted">接下來 72 小時沒有排定的大事。</p>')
    return (f'<details class="sgx"><summary>今天的總經儀表與接下來 72 小時</summary><p class="small"><b>{html.escape(lead)}</b></p>{tbl}{nxt}'
            '<p class="note">數字由程式從本站行情資料直接算出（Yahoo 收盤；殖利率以 bp＝0.01 個百分點計）；⚡＝當天變化超過自己過去一年平常一天波動的 2 倍。'
            '時間表和「接下來的大事」是同一份清單。描述現況，不是預測，也不是投資建議。</p></details>')
