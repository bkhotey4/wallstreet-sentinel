"""10-year yield: FRED DGS10 posts a day late, the ^TNX quote is "now" (wsb/data/treasury.live10).  Run: python -m tests.test_live10"""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.data import treasury as TR   # noqa: E402


def _eng(asof):
    return SimpleNamespace(market=SimpleNamespace(q=lambda t: {"price": 4.864, "asof": asof} if t == "^TNX" else None))


def test_live10():
    now = [{"sid": "DGS2", "years": 2, "yield": 4.46, "date": "2026-11-06"}, {"sid": "DGS10", "years": 10, "yield": 4.84, "date": "2026-11-06"}]
    lv = TR.live10(_eng("2026-11-09"), now)
    assert lv == {"yield": 4.864, "date": "2026-11-09", "fred_date": "2026-11-06"}
    assert TR.live10(_eng("2026-11-06"), now) is None                       # FRED already has that day
    assert TR.live10(SimpleNamespace(market=None), now) is None
    t = {"available": True, "curves": {"now": now}, "spreads": {}, "live10": lv, "auctions": []}
    L = TR.summary_lines(t)
    assert L[0].startswith("殖利率曲線（FRED，資料日 2026-11-06）") and "最新報價 4.864%（2026-11-09" in L[1]


if __name__ == "__main__":
    test_live10()
    print("ok test_live10")
