"""銀行放款調查（SLOOS，聯準會每季對銀行放款主管的調查）：銀行是在收緊還是放寬借錢的門檻，以及借錢的人多不多。

數字的意思：「淨收緊比例」＝回答「收緊」的銀行占比 − 回答「放寬」的占比（正＝收緊，負＝放寬）；
「淨需求」＝回答「需求變強」的占比 − 「變弱」的占比。全部是 FRED 上聯準會的官方序列，季資料。

燈號只和每一條自己的歷史比（不用網路上流傳的固定門檻，研究筆記 research_risk_2026-10.md 說明過那些門檻只建立在約 8 次事件上）：
  🔴 收緊程度落在自己歷史最高 10% 而且淨收緊至少 10%；🟡 落在最高 25%、或比一年前多收緊 20 個百分點以上，而且淨收緊至少 5%；其餘 🟢
  （接近 0 代表「跟上一季差不多」，即使歷史大多是 0 也不亮燈）。
整體：🔴 至少一項企業或商用不動產紅燈；🟡 有 3 項以上黃燈；其餘 🟢。
描述現況，不是預測。2026-11-17 新增。"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import pandas as pd

# (key, 中文, 標準序列, 需求序列 or None, 白話是誰在借)
ROWS = [
    ("ci_big", "大中型企業放款", "DRTSCILM", "DRSDCILM", "年營收 5,000 萬美元以上的公司借錢做生意"),
    ("ci_small", "小企業放款", "DRTSCIS", "DRSDCIS", "小公司、店家週轉和擴張"),
    ("cre_build", "營建與土地開發", "SUBLPDRCSC", "SUBLPDRCDC", "建商蓋房子、蓋大樓的錢"),
    ("cre_office", "商辦與其他商用不動產", "SUBLPDRCSN", "SUBLPDRCDN", "辦公大樓、商場、倉庫的房東"),
    ("cre_multi", "多戶公寓", "SUBLPDRCSM", None, "出租公寓的房東"),
    ("mort", "一般房貸", "SUBLPDHMSENQ", "SUBLPDHMDENQ", "一般家庭買房（符合房利美／房地美標準）"),
    ("card", "信用卡", "DRTSCLCC", "DEMCC", "家庭刷卡、循環借款"),
    ("auto", "車貸", "STDSAUTO", "DEMAUTO", "家庭買車"),
    ("cons", "其他消費貸款", "STDSOTHCONS", "DEMOTHCONS", "個人信貸等"),
]
FRED_IDS = tuple(dict.fromkeys(x for r in ROWS for x in (r[2], r[3]) if x))
BUSINESS = ("ci_big", "ci_small", "cre_build", "cre_office", "cre_multi")
SOURCE = "https://www.federalreserve.gov/data/sloos.htm"


def _pct(hist: pd.Series, v: float) -> Optional[float]:
    h = hist.dropna()
    if len(h) < 12:
        return None
    return float((h <= v).mean() * 100)


def row_view(key: str, zh: str, std: Optional[pd.Series], dem: Optional[pd.Series], who: str) -> Optional[Dict]:
    if std is None:
        return None
    s = std.dropna()
    if len(s) < 12:
        return None
    v = float(s.iloc[-1])
    p = _pct(s, v)
    yago = s[s.index <= s.index[-1] - pd.DateOffset(months=11)]
    v1 = float(yago.iloc[-1]) if len(yago) else None
    jump = v1 is not None and v - v1 >= 20
    # near zero is "about the same as last quarter" even when the history is mostly zeros: red needs ≥ +10, yellow ≥ +5
    emoji = "🔴" if p is not None and p >= 90 and v >= 10 else "🟡" if (p is not None and p >= 75 and v >= 5) or (jump and v >= 5) else "🟢"
    mx = s.idxmax()
    out = {"key": key, "zh": zh, "who": who, "std": v, "std_1y": v1, "pct": p, "since": s.index[0].year,
           "date": s.index[-1].strftime("%Y-%m"), "max": float(s.max()), "max_date": mx.strftime("%Y-%m"), "emoji": emoji,
           "state": "收緊" if v > 0 else "放寬" if v < 0 else "持平",
           "hist": [[i.strftime("%Y-%m"), round(float(x), 1)] for i, x in s.tail(60).items()]}
    if dem is not None and len(dem.dropna()):
        d = dem.dropna()
        out.update(dem=float(d.iloc[-1]), dem_date=d.index[-1].strftime("%Y-%m"))
    return out


def view(get: Callable[[str], Optional[pd.Series]]) -> Dict:
    rows: List[Dict] = []
    for key, zh, sid, did, who in ROWS:
        try:
            r = row_view(key, zh, get(sid), get(did) if did else None, who)
        except Exception:  # noqa: BLE001
            r = None
        if r:
            rows.append(r)
    if not rows:
        return {}
    red = [r for r in rows if r["emoji"] == "🔴" and r["key"] in BUSINESS]
    yel = [r for r in rows if r["emoji"] != "🟢"]
    emoji = "🔴" if red else "🟡" if len(yel) >= 3 else "🟢"
    tight = [r for r in rows if r["std"] > 0]
    loose = [r for r in rows if r["std"] < 0]
    return {"rows": rows, "emoji": emoji, "date": max(r["date"] for r in rows), "n_tight": len(tight), "n_loose": len(loose),
            "hot": [r["zh"] for r in yel]}


def lead(v: Dict) -> str:
    rows = v.get("rows") or []
    if not rows:
        return ""
    hot = [r for r in rows if r["emoji"] != "🟢"]
    big = next((r for r in rows if r["key"] == "ci_big"), None)
    head = (f"{len(rows)} 類貸款裡，{v['n_tight']} 類銀行在收緊、{v['n_loose']} 類在放寬")
    if not hot:
        tail = "，收緊的程度都還在各自歷史的正常範圍，借錢的門檻沒有明顯變高。"
    else:
        tail = "；收緊得比平常多的是：" + "、".join(f"{r['zh']}（淨 {r['std']:+.0f}%，歷史第 {r['pct']:.0f} 百分位）" for r in hot) + "。"
    if big and big.get("dem") is not None:
        tail += f"企業借錢的需求淨 {big['dem']:+.0f}%（{'變強' if big['dem'] > 0 else '變弱' if big['dem'] < 0 else '持平'}）。"
    return head + tail
