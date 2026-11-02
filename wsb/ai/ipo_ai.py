"""招股書重點（AI）— a plain-language read of each pending US IPO's latest S-1 / F-1 excerpt (cover, summary, summary
financial data, risk summary, use of proceeds).  The model may only use numbers in the excerpt (llm.complete drops any
sentence whose numbers are not in it) and keeps the prospectus units; trading words are scrubbed.  Cached per filing
(accession number), so each amendment is read once.  Skipped when no AI key is set — the card still shows the dates."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Dict, Optional

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_ipo_ai.json"
FIELDS = ("業務", "財務", "資金用途", "主要風險", "要留意")

SYSTEM = """你是華爾街股票研究員，為公開網頁把美國 IPO 招股書（S-1／F-1）的節錄整理成一般大眾看得懂的重點。
【鐵律】
1. 只能使用節錄裡的文字與數字，沒有的就寫「招股書節錄未提供」；不得編造或推算任何數字。
2. 數字照招股書原本的單位寫（例如「營收 4,585 百萬美元」「淨損 (1,529) 百萬美元」），不要換算成億、不要自己算成長率或比率。
3. 這不是投資建議：不得出現買進、賣出、申購建議、加碼、減碼、目標價、合理價、值不值得投資等字眼。
4. 台灣繁體中文、台灣用語，每一項 1～3 句。
只輸出以下 5 行，每行以標籤開頭：
業務：這家公司做什麼、主要客戶或產品。
財務：最近年度與最近期間的營收、營業損益或淨損益、現金（照節錄數字），以及營收是變多還是變少。
資金用途：募到的錢打算拿來做什麼。
主要風險：招股書自己列出的 2～3 個最主要風險。
要留意：股權結構（多種股份類別、投票權集中）、禁售期或其他招股書提到、一般投資人容易忽略的事。"""


def load() -> Dict[str, Dict]:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(d: Dict) -> None:
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError:
        pass


def parse(text: str) -> Optional[Dict[str, str]]:
    from .econ_ai import scrub
    out: Dict[str, str] = {}
    for ln in (text or "").splitlines():
        ln = ln.strip().lstrip("-•* ")
        for f in FIELDS:
            if ln.startswith(f + "：") or ln.startswith(f + ":"):
                v = scrub(ln[len(f) + 1:].strip())
                if v:
                    out[f] = v
    return out if len(out) >= 3 else None


async def generate(rows, docs: Dict[str, str], limit: int = 2, deadline_s: float = 120) -> int:
    from . import llm
    cache = load()
    n, t_end = 0, time.monotonic() + deadline_s
    for r in rows:
        acc = r.get("acc")
        if n >= limit or time.monotonic() >= t_end or not acc or acc in cache or not docs.get(acc):
            continue
        prompt = f"公司：{r.get('name')}（{r.get('sicd') or ''}）\n招股書節錄：\n{docs[acc]}"
        try:
            text, name = await asyncio.wait_for(llm.complete(SYSTEM, prompt, 1200), max(5.0, t_end - time.monotonic()))
        except asyncio.TimeoutError:
            break
        if name == "none" or not text or text.startswith("⚠️"):
            break
        p = parse(text)
        if p:
            cache[acc] = {**p, "engine": name, "ts": time.time()}
            _save(cache)
            n += 1
    keep = {r.get("acc") for r in rows}
    if any(k not in keep for k in cache):
        _save({k: v for k, v in cache.items() if k in keep})
    return n
