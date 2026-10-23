"""Post-check of AI text: every number the model writes must trace back to the prompt it was given.

The prompts already say "only use DATA PACK numbers"; this enforces it in code. A sentence carrying a number
that appears nowhere in the prompt (after rounding, sign and unit scaling) is dropped, and the text says how many
were dropped. Counts, horizons, years and dates are not checked — they are not market data."""
from __future__ import annotations

import bisect
import logging
import re
from typing import List, Tuple

log = logging.getLogger(__name__)

_NUM_RX = re.compile(r"(?<![\w.])[-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
_DATE_RX = re.compile(r"\d{4}[-/.]\d{1,2}(?:[-/.]\d{1,2})?|\d{1,2}[-/]\d{1,2}(?![\d.%])|\d{1,2}:\d{2}"
                      r"|\d{1,2}\s*月(?:\s*\d{1,2}\s*日)?|\d{1,2}\s*日|\d{1,2}\s*[號号]")
_SENT_RX = re.compile(r"(?<=[。！？!?；;])")
_APPROX_RX = re.compile(r"(約|近|逾|超過|將近|接近|大約|左右|上下|多)\s*$")
_SCALE_UNIT_RX = re.compile(r"^\s*(億|萬|兆|千|百萬|十億|[BMKT]\b|bn\b|mn\b)", re.I)
# horizons / sample sizes that are part of the method, not data (20 日線、52 週、252 個交易日 …)
_METHOD = {14, 20, 21, 24, 48, 72, 30, 45, 50, 52, 60, 63, 90, 100, 120, 126, 180, 200, 250, 252, 365, 500}
NOTE = "（數字查核：已刪除 {n} 句找不到資料來源的數字）"


def _val(raw: str) -> float:
    return float(raw.replace(",", "").replace("−", "-"))


def _decimals(raw: str) -> int:
    return len(raw.split(".", 1)[1]) if "." in raw else 0


def pool(source: str) -> List[float]:
    """Every number in the prompt, as sorted absolute values (sign is free: 「跌 1.2%」 states −1.2)."""
    return sorted({abs(_val(m.group())) for m in _NUM_RX.finditer(source or "")})


def _exempt(v: float, raw: str) -> bool:
    a = abs(v)
    if "." not in raw and (a <= 12 or a in _METHOD or 1900 <= a <= 2100):
        return True
    return False


def supported(raw: str, src: List[float], after: str = "", before: str = "") -> bool:
    v = abs(_val(raw))
    tol = 0.5 * 10 ** -_decimals(raw) + 1e-9
    if _APPROX_RX.search(before) or after.lstrip().startswith(("左右", "上下", "多")):
        tol = max(tol, v * 0.05)
    scales = (1, 100, 0.01)                                 # fraction ↔ %, % ↔ bp
    if _SCALE_UNIT_RX.match(after):                         # 12 億 ↔ 1.2B, 2,817.7 億 ↔ 281,770,000,000 …
        scales = (1, 100, 0.01, 10, 0.1, 1e4, 1e-4, 1e8, 1e-8, 1e9, 1e-9, 1e12, 1e-12)
    ys = src if isinstance(src, list) else sorted(src)
    for k in scales:                                        # |v − y·k| ≤ tol  ⇔  y within (v ± tol) / k
        i = bisect.bisect_left(ys, (v - tol) / k)
        if i < len(ys) and ys[i] <= (v + tol) / k:
            return True
    return False


def _derived(raw: str, others: List[float]) -> bool:
    """A ratio, difference or sum of two sourced numbers in the same sentence (「24.5% 是基準 17.1% 的 1.43 倍」)."""
    v, tol = abs(_val(raw)), 0.5 * 10 ** -_decimals(raw) + 1e-9
    for i, a in enumerate(others):
        for b in others[i + 1:]:
            cands = [a + b, abs(a - b)] + [x / y for x, y in ((a, b), (b, a)) if y]
            if any(abs(v - c) <= tol for c in cands):
                return True
    return False


def unsupported(sentence: str, src: List[float]) -> List[str]:
    masked = _DATE_RX.sub(lambda m: " " * len(m.group()), sentence)
    ok, bad = [], []
    for m in _NUM_RX.finditer(masked):
        raw = m.group()
        if _exempt(_val(raw), raw):
            continue
        if supported(raw, src, masked[m.end():m.end() + 4], masked[max(0, m.start() - 4):m.start()]):
            ok.append(abs(_val(raw)))
        else:
            bad.append(raw)
    return [r for r in bad if not _derived(r, ok)]


_PCTILE_RX = re.compile(r"((?:歷史|近一年|一年|全期|自\s*\d{4}\s*年?(?:起|以來)?|近?\s*\d+\s*(?:年|個月|日|週))?百分位)(?:\s*(?:為|在|是|達))?\s*(\d+(?:\.\d+)?)")


def fix_periods(text: str, source: str) -> str:
    """「歷史百分位 98」 when the data said 「3年百分位 98」: put the source's window back on the number."""
    labels = {}
    for m in _PCTILE_RX.finditer(source or ""):
        labels.setdefault(round(float(m.group(2))), set()).add(re.sub(r"\s+", "", m.group(1)))

    def sub(m):
        have = labels.get(round(float(m.group(2))), set())
        if not have or re.sub(r"\s+", "", m.group(1)) in have or len(have) != 1:
            return m.group(0)
        return m.group(0).replace(m.group(1).strip(), next(iter(have)), 1)
    return _PCTILE_RX.sub(sub, text)


def check(text: str, source: str) -> Tuple[str, List[str]]:
    """→ (text without unsupported sentences, the dropped sentences). Adds a one-line note when anything was dropped."""
    if not text:
        return text, []
    text = fix_periods(text, source)
    src = pool(source)
    out, dropped = [], []
    for ln in text.split("\n"):
        parts = [p for p in _SENT_RX.split(ln) if p is not None]
        keep = []
        for p in parts:
            if p.strip() and unsupported(p, src):
                dropped.append(p.strip())
            else:
                keep.append(p)
        kept = "".join(keep)
        if kept.strip() or not ln.strip():
            out.append(kept)
    if not dropped:
        return text, []
    log.warning("AI number check dropped %d sentence(s): %s", len(dropped), " | ".join(d[:80] for d in dropped[:5]))
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    return body + "\n\n" + NOTE.format(n=len(dropped)), dropped
