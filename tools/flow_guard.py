"""外資金額防呆: routine-written text (每日深度研判 etc.) sometimes slips a digit on TWSE 三大法人 figures
(2026-11-18: official 外資賣超 765.6 億 was written as 76.5 億; Gemini caught it).
fix() compares every 「外資…買超/賣超 N 億」 against TWSE BFI82U flows (億元, eng.taiwan.flows) and only
rewrites a clear ×10 / ÷10 slip, tagging it so the correction is visible. Anything else is left alone."""
import re
from typing import Dict, Iterable

RX = re.compile(r"(外資[^，。；、\d]{0,14}?(?:買超|賣超)[^，。；\d]{0,3}?)(\d[\d,]*(?:\.\d+)?)(\s*億)")
TAG = "（依證交所資料更正）"


def _near(a: float, b: float, tol: float = 0.15) -> bool:
    return b > 0 and abs(a - b) / b <= tol


def fix(text: str, flows: Iterable[Dict]) -> str:
    vals = [abs(f["foreign"]) for f in (flows or []) if isinstance(f, dict) and f.get("foreign")]
    if not text or not vals:
        return text

    def sub(m):
        try:
            n = float(m.group(2).replace(",", ""))
        except ValueError:
            return m.group(0)
        if any(_near(n, v) for v in vals):
            return m.group(0)
        for v in vals:
            if _near(n * 10, v) or _near(n / 10, v):
                return f"{m.group(1)}{v:,.1f}{m.group(3)}{TAG}"
        return m.group(0)

    return RX.sub(sub, text)
