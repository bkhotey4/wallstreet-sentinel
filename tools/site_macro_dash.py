"""每日總經情勢的「數字儀表」與「接下來 72 小時」（2026-11-18，使用者：「每日總經可以再多補充的吧」）。

語音稿是 AI 寫的解讀；這裡是程式直接從本站資料算出來的數字，讓解讀有對照：
  * 23 個總經指標，分美國、美債、亞洲（台灣、日本、香港、人民幣）三組：當天、5 天變化，和自己過去一年「平常一天」的波動比（≥ 2 倍標 ⚡），一句白話說明它代表什麼
  * 接下來 72 小時：讀 upcoming.json 同一份清單（財報、總經、IPO、指數調整），台北時間
描述現況，不是預測，也不是投資建議。"""
from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

TPE = timezone(timedelta(hours=8))

# (group, source, id, 中文, kind, what a rise means).  source: px = 本站行情, fred = FRED（2 年期由財政部 XML 補到當天）,
# jgb = 日本財務省.  kind: pct = 漲跌 %, bp = 殖利率（以 % 報價，變化以 bp 計）, sp = 利差（可以是負的，變化以 bp 計）.
# 2026-11-21 使用者：「每日總經是不是少了台股／港股跟日股總經的分析…美債也可以分析一下」→ 分成美國、美債、亞洲三組。
GROUPS = ("美國", "美債", "亞洲")
ITEMS = [
    ("美國", "px", "^GSPC", "標普 500", "pct", "美國大型股的整體表現"),
    ("美國", "px", "^SOX", "費城半導體", "pct", "AI 與晶片族群的溫度計，台股電子股常跟著動"),
    ("美國", "px", "^VIX", "VIX 恐慌指數", "pct", "升＝市場預期未來 30 天波動變大，越高越緊張"),
    ("美國", "px", "HYG", "高收益債 ETF", "pct", "跌＝借錢給體質較弱公司的人在擔心違約"),
    ("美國", "px", "DX-Y.NYB", "美元指數", "pct", "升＝資金偏保守，新台幣與新興市場通常走弱"),
    ("美國", "px", "BZ=F", "布蘭特原油", "pct", "升＝通膨壓力變大，央行更難降息"),
    ("美國", "px", "GC=F", "黃金", "pct", "升＝避險需求或實質利率下降"),
    ("美國", "px", "HG=F", "銅", "pct", "升＝市場看好全球製造與基建需求"),
    ("美債", "fred", "DGS2", "美國 2 年期殖利率", "bp", "最貼近聯準會政策利率的預期：升＝市場覺得降息會變少或變晚"),
    ("美債", "px", "^TNX", "美國 10 年期殖利率", "bp", "升＝借錢變貴，房貸、成長股與債券價格承壓"),
    ("美債", "px", "^TYX", "美國 30 年期殖利率", "bp", "升＝長期借錢變貴，常跟財政赤字與通膨擔憂有關"),
    ("美債", "fred", "T10Y2Y", "10 年減 2 年利差", "sp", "負＝殖利率曲線倒掛，過去常在衰退前出現；由負轉正也常是衰退前夕"),
    ("美債", "fred", "DFII10", "10 年期實質利率", "bp", "扣掉通膨後的真實借錢成本：升＝對黃金、成長股與房市的壓力變大"),
    ("美債", "fred", "T10YIE", "10 年通膨預期", "bp", "債市認為未來十年平均通膨多少：升＝通膨擔憂變大"),
    ("美債", "px", "^MOVE", "MOVE 美債波動率", "pct", "債市的恐慌指數：升＝利率走向越來越難猜，大型機構會減少持債"),
    ("亞洲", "px", "^TWII", "台股加權", "pct", "台灣股市整體表現"),
    ("亞洲", "px", "TWD=X", "美元兌新台幣", "pct", "升＝新台幣貶值，外資可能在賣台股"),
    ("亞洲", "px", "^N225", "日經 225", "pct", "日本大型股；日圓急升時常一起跌"),
    ("亞洲", "px", "JPY=X", "美元兌日圓", "pct", "急跌＝日圓急升，借日圓去投資的錢可能被迫平倉"),
    ("亞洲", "jgb", "10Y", "日本 10 年期公債殖利率", "bp", "升＝日本央行可能繼續升息，日本資金可能從海外搬回家"),
    ("亞洲", "px", "^HSI", "恆生指數", "pct", "香港股市；反映中國經濟與外資對中國的信心"),
    ("亞洲", "px", "HKD=X", "美元兌港幣", "pct", "港幣綁美元在 7.75～7.85 之間：貼近 7.85＝資金在流出香港"),
    ("亞洲", "px", "CNY=X", "美元兌人民幣", "pct", "升＝人民幣走弱，中國出口與資金外流的壓力"),
]


def _row(s, kind: str) -> Optional[Dict]:
    import numpy as np
    s = s.dropna()
    if kind == "pct":
        s = s[s > 0]
    if len(s) < 60:
        return None
    last, prev = float(s.iloc[-1]), float(s.iloc[-2])
    p5 = float(s.iloc[-6]) if len(s) > 6 else None
    if kind in ("bp", "sp"):
        d1, d5 = (last - prev) * 100, ((last - p5) * 100 if p5 is not None else None)
        hist = s.diff().dropna().tail(252) * 100
    else:
        d1, d5 = (last / prev - 1) * 100, ((last / p5 - 1) * 100 if p5 else None)
        hist = (s.pct_change(fill_method=None).dropna().tail(252)) * 100
    sd = float(np.std(hist)) if len(hist) > 30 else None
    return {"last": last, "d1": d1, "d5": d5, "sd": sd, "k": abs(d1) / sd if sd else None, "date": s.index[-1].strftime("%m-%d")}


def _series(eng, src: str, sid: str):
    if src == "fred":
        return eng.fred.get(sid)
    if src == "jgb":
        return eng.global_yields.get(sid)
    return eng.market.series(sid)


def rows(eng) -> List[Dict]:
    out = []
    for grp, src, sym, zh, kind, why in ITEMS:
        try:
            r = _row(_series(eng, src, sym), kind)
        except Exception:  # noqa: BLE001
            r = None
        if r:
            out.append({"grp": grp, "src": src, "sym": sym, "zh": zh, "kind": kind, "why": why, **r})
    return out


def public(eng) -> Dict:
    """macro_dash.json: the same numbers for the voice routines, so their scripts quote what the card shows."""
    rs = rows(eng)
    keep = ("grp", "sym", "zh", "kind", "last", "d1", "d5", "sd", "k", "date")
    return {"updated": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"),
            "note": "kind pct＝漲跌 %；bp／sp＝殖利率或利差（last 以 % 計，d1／d5／sd 以 bp 計）；k＝當天變化是平常一天的幾倍",
            "rows": [{k: (round(r[k], 4) if isinstance(r.get(k), float) else r.get(k)) for k in keep} for r in rs]}


def _fmt(r: Dict) -> str:
    u = "%" if r["kind"] == "pct" else "bp"
    lv = f'{r["last"]:.2f}%' if r["kind"] != "pct" else (f'{r["last"]:,.2f}' if r["last"] < 1000 else f'{r["last"]:,.0f}')
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
    lead = ("今天動得比平常大（超過平常一天的 2 倍）：" + "、".join(f'{r["zh"]} {r["d1"]:+.1f}{"%" if r["kind"] == "pct" else "bp"}' for r in hot)
            if hot else "今天沒有一項總經指標動得比平常大（都在平常一天的 2 倍以內）。")
    tbl = ('<div class="scroll"><table class="mini"><thead><tr><th>指標</th><th class="r">現在</th><th class="r">當天</th><th class="r">5 天</th>'
           '<th class="r">平常一天</th><th class="r">資料日</th></tr></thead><tbody>' + "".join(f'<tr><th colspan="6">{g}</th></tr>' + "".join(_fmt(r) for r in rs if r["grp"] == g)
                     for g in GROUPS if any(r["grp"] == g for r in rs)) + "</tbody></table></div>")
    up = ahead(eng)
    kind_zh = {"earnings": "財報", "macro": "數據", "ipo": "上市", "index": "指數調整"}
    ul = "".join(f'<li><b>{html.escape(x["tpe"][5:].replace("-", "/"))}</b>・{kind_zh.get(x["kind"], "")}・{html.escape(x["zh"])}</li>' for x in up)
    nxt = (f'<h3>接下來 72 小時（台北時間）</h3><ul class="small">{ul}</ul>' if ul else '<p class="small muted">接下來 72 小時沒有排定的大事。</p>')
    return (f'<details class="sgx"><summary>今天的總經儀表與接下來 72 小時</summary><p class="small"><b>{html.escape(lead)}</b></p>{tbl}{nxt}'
            '<p class="note">數字由程式從本站行情資料直接算出（Yahoo 收盤；美國 2 年期、實質利率、通膨預期與利差來自 FRED，2 年期由美國財政部每日殖利率補到當天；日本 10 年期來自日本財務省；殖利率以 bp＝0.01 個百分點計）；⚡＝當天變化超過自己過去一年平常一天波動的 2 倍。'
            '時間表和「接下來的大事」是同一份清單。描述現況，不是預測，也不是投資建議。</p></details>')
