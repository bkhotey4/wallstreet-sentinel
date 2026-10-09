"""On-demand lookup for ANY ticker (Discord /stock): composite score, rank and technical status / entry signal,
measured against the same market's scoring universe — also for stocks that are not in the universe.

The ticker is scored together with its market's universe (so its technical ranks are comparable) without touching
the saved score history or signal state."""
from __future__ import annotations

import asyncio
import copy
import re
import types
from typing import Dict, Optional, Tuple

import pandas as pd

from ..data import stocks as ST
from . import signals as SG
from . import stockscore as SS


def normalise(t: str) -> Tuple[str, str]:
    """User input → (Yahoo symbol, market key).  2330 → 2330.TW · 700 / 0700 → 0700.HK · brk.b → BRK-B."""
    s = (t or "").strip().upper()
    if re.fullmatch(r"\d{4,6}[A-Z]?", s):
        return s + ".TW", "tw"
    if s.endswith((".TW", ".TWO")):
        return s, "tw"
    m = re.fullmatch(r"(\d{1,5})(\.HK)?", s)
    if m and (m.group(2) or len(m.group(1)) <= 3):         # 4+ bare digits are Taiwan codes (0050, 2330); HK needs .HK or ≤3 digits
        return m.group(1).zfill(4) + ".HK", "hk"
    if s.endswith(".HK"):
        return s, "hk"
    return s.replace(".", "-"), "us"


class _Prices:
    def __init__(self, close: pd.DataFrame, volume: pd.DataFrame):
        self.close, self.volume = close, volume

    def series(self, s):
        return self.close[s].dropna() if s in self.close.columns else pd.Series(dtype=float)

    def vol(self, s):
        return self.volume[s].dropna() if s in self.volume.columns else pd.Series(dtype=float)


def _find(res: Dict, mk: str, sym: str, key: str = "rows") -> Optional[Dict]:
    m = ((res or {}).get("markets") or {}).get(mk) or {}
    return next((r for r in m.get(key, []) if r["sym"] == sym), None)


async def lookup(eng, ticker: str) -> Dict:
    sym, mk = normalise(ticker)
    uni = ST.universe()
    if mk not in uni:
        return {"ok": False, "error": f"不支援的市場：{ticker}"}
    in_uni = sym in uni[mk]["symbols"]
    if in_uni:
        sc_res, sg_res = eng.scores or {}, eng.signals or {}
    else:
        sp = eng.stockprices
        try:
            cl, vo = await asyncio.to_thread(ST._download, [sym], "2y")
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"抓不到 {sym} 的價格：{e}"}
        if cl.empty or sym not in cl.columns or cl[sym].dropna().shape[0] < 60:
            return {"ok": False, "error": f"Yahoo 找不到 {sym} 的足夠價格資料（代號是否正確？台股請用 2330，港股用 0700）"}
        prices = _Prices(sp.close.join(cl[[sym]], how="outer"), sp.volume.join(vo[[sym]] if sym in vo else pd.DataFrame(), how="outer"))
        u2 = {mk: copy.deepcopy(uni[mk])}
        u2[mk]["symbols"][sym] = (sym, sym)
        u2[mk]["themes"][sym] = "自選查詢"
        fake = types.SimpleNamespace(**{k: v for k, v in vars(eng).items()})
        fake.stockprices = prices
        sc_res = await asyncio.to_thread(SS.build, fake, u2, False)
        fake.scores = sc_res
        sg_res = await asyncio.to_thread(SG.build, fake, u2, False)
    row = _find(sc_res, mk, sym)
    if row is None:
        return {"ok": False, "error": f"{sym} 的歷史太短，無法評分（需要約半年以上的日線）"}
    m = sc_res["markets"][mk]
    sig = _find(sg_res, mk, sym, "rows")
    allrow = _find(sg_res, mk, sym, "all")
    return {"ok": True, "sym": sym, "market": mk, "label": m["label"], "in_universe": in_uni, "row": row, "n": len(m["rows"]),
            "signal": sig, "status": (allrow or {}).get("status"), "asof": m["asof"]}
