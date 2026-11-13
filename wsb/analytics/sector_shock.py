"""族群急跌警報：一個產業族群今天跌到「自己平常一天波動的 2 倍以上」，就寫一句醒目的警示，並配對同時段的新聞標題。

網站（tools/site_live.py，瀏覽器每分鐘算）和 Discord（tools/sec_push.py，每 3 分鐘）用同一份名單與門檻。
門檻：z ≤ −2（z＝今天漲跌 ÷ 平常一天的幅度；平常一天＝過去一年日漲跌的中位數絕對偏差 × 1.4826，不被少數崩盤日撐大）
而且今天至少跌 1.5%；z ≤ −3 為紅燈。
新聞配對：過去 6 小時的標題裡，命中這個族群關鍵字的列出來；另外列出利率／通膨／聯準會這類總經標題（常是一起跌的原因）。
配對只代表「同時段、同主題」，不等於就是原因；找不到就直說原因還不清楚。描述現況，不是預測。"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

# (symbol, 中文, English, 新聞關鍵字)
SECTORS = [
    ("^SOX", "費城半導體", "Semiconductors (SOX)", r"chip|semiconductor|Nvidia|AMD|Broadcom|TSMC|export control|輝達|晶片|半導體|台積電|出口管制"),
    ("IGV", "軟體股", "Software (IGV)", r"software|SaaS|cloud|Salesforce|Oracle|ServiceNow|軟體|雲端"),
    ("XLK", "科技類股", "Technology (XLK)", r"\btech|Apple|Microsoft|\bAI\b|科技|人工智慧"),
    ("XLF", "金融類股", "Financials (XLF)", r"\bbanks?\b|lender|financial|JPMorgan|Goldman|銀行|金融"),
    ("XLE", "能源類股", "Energy (XLE)", r"\boil\b|crude|OPEC|natural gas|Exxon|Chevron|油價|原油|天然氣|能源"),
    ("XLV", "醫療保健", "Health care (XLV)", r"drug|pharma|FDA|health|Medicare|vaccine|醫療|藥"),
    ("XLY", "非必需消費", "Consumer discretionary (XLY)", r"retail|consumer|Amazon|Tesla|Nike|消費|零售"),
    ("XLI", "工業類股", "Industrials (XLI)", r"industrial|Boeing|defense|airline|tariff|工業|國防|關稅"),
    ("XLU", "公用事業", "Utilities (XLU)", r"utilit|power grid|electricity|電力|公用"),
    ("XLRE", "不動產", "Real estate (XLRE)", r"real estate|REIT|mortgage|housing|房地產|房貸|房市"),
    ("XLB", "原物料", "Materials (XLB)", r"copper|steel|metal|mining|chemical|銅|鋼|原物料"),
    ("XLC", "通訊服務", "Communication (XLC)", r"Meta\b|Google|Alphabet|Netflix|media|telecom|媒體|通訊"),
    ("XLP", "必需消費", "Consumer staples (XLP)", r"staples|Walmart|Costco|Procter|food|必需|食品"),
]
MACRO = r"yield|Treasur|\bFed\b|Federal Reserve|inflation|\bCPI\b|\bPPI\b|rate hike|rate cut|jobs report|payroll|殖利率|公債|聯準會|通膨|升息|降息|物價|非農"
Z_WARN, Z_RED, MIN_DROP = 2.0, 3.0, 1.5
NEWS_H = 6


def robust_sd(close) -> Optional[float]:
    """A normal day's size: 1.4826 × the median absolute deviation of the last year's daily % changes.  The plain standard
    deviation is pulled up by a few crash days (費半 3.05 % vs 2.44 % on 2026-11-13), which hid a −5.5 % day as 1.8×."""
    try:
        r = close.dropna()
        r = r[r > 0].pct_change().dropna().iloc[-252:] * 100
    except Exception:  # noqa: BLE001
        return None
    if len(r) < 120:
        return None
    v = float((r - r.median()).abs().median() * 1.4826)
    return v if v > 0 else None


def level(chg: Optional[float], sd: Optional[float]) -> int:
    """0 = nothing, 1 = 黃燈 (≥ 2× normal and ≥ 1.5 % down), 2 = 紅燈 (≥ 3× normal)."""
    if chg is None or not sd:
        return 0
    z = chg / sd
    if chg > -MIN_DROP or z > -Z_WARN:
        return 0
    return 2 if z <= -Z_RED else 1


def match_news(items: List[Dict], kw: str, now: float, hours: float = NEWS_H, k: int = 2) -> List[Dict]:
    rx = re.compile(kw, re.I)
    hit = [x for x in items if now - x.get("ts", 0) <= hours * 3600 and rx.search(x.get("t", ""))]
    return sorted(hit, key=lambda x: -x["ts"])[:k]


def check(quotes: Dict[str, Dict], sd: Dict[str, float], news: List[Dict], now: float) -> List[Dict]:
    """[{sym, zh, chg, z, lv, news, macro}] for sectors falling unusually hard, worst first."""
    out = []
    macro = match_news(news, MACRO, now, k=2)
    for sym, zh, en, kw in SECTORS:
        x = quotes.get(sym) or {}
        chg = x.get("chg")
        lv = level(chg, sd.get(sym))
        if not lv:
            continue
        out.append({"sym": sym, "zh": zh, "en": en, "chg": chg, "z": chg / sd[sym], "lv": lv, "t": x.get("t"),
                    "news": match_news(news, kw, now), "macro": macro})
    return sorted(out, key=lambda a: a["z"])


def sentence(a: Dict, tz_hhmm) -> str:
    """One plain line: what fell, how unusual, and the headlines from the same hours (or that none were found)."""
    s = f'{a["zh"]} {a["chg"]:+.1f}%（平常一天的 {abs(a["z"]):.1f} 倍）'
    hs = a.get("news") or []
    if hs:
        s += "；同時段新聞：" + "、".join(f'〈{h["t"][:70]}〉（{tz_hhmm(h["ts"])}）' for h in hs)
    else:
        s += "；找不到時間和主題都對得上的新聞，原因還不清楚"
    if a.get("macro"):
        s += "；同時段的總經消息：" + "、".join(f'〈{h["t"][:70]}〉（{tz_hhmm(h["ts"])}）' for h in a["macro"][:1])
    return s
