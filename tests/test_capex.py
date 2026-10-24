"""AI 資本支出依賴度: quarterly values from year-to-date XBRL facts (incl. tag switches), calendar-quarter alignment, the
regression and "if capex stops growing", the card.  Run: python -m tests.test_capex"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_cx_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from wsb.analytics import capex_link as CL  # noqa: E402


def _cf(tag_a: str, tag_b: str):
    """Fiscal years = calendar years; YTD facts for Q1..Q4; 2018–2021 under tag_a, 2022+ under tag_b (a tag switch)."""
    facts = {tag_a: [], tag_b: []}
    for y in range(2018, 2027):
        tag = tag_a if y < 2022 else tag_b
        q = 100.0 * (1.2 ** (y - 2018))
        for k, end in enumerate(("03-31", "06-30", "09-30", "12-31"), 1):
            facts[tag].append({"start": f"{y}-01-01", "end": f"{y}-{end}", "val": q * k, "filed": f"{y + 1}-02-01"})
    return {"facts": {"us-gaap": {t: {"units": {"USD": v}} for t, v in facts.items()}}}


def test_quarterly():
    q = CL.quarterly(_cf("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"), CL.CAPEX)
    assert q["2018Q1"] == 100 and q["2018Q4"] == 100 and abs(q["2023Q2"] - 100 * 1.2 ** 5) < 1e-6 and "2026Q4" in q
    assert CL._cal_q("2026-07-26") == "2026Q2" and CL._cal_q("2026-01-25") == "2025Q4"


def test_build_and_card():
    qs = [f"{y}Q{k}" for y in range(2018, 2027) for k in range(1, 5)]
    g = np.linspace(1.0, 3.0, len(qs))
    cap = {s: {q: 100 * g[i] ** 2 for i, q in enumerate(qs)} for s in ("MSFT", "GOOGL", "AMZN")}
    rev = {"MU": {q: 50 * g[i] ** 3 for i, q in enumerate(qs)},                     # grows faster when capex grows faster
           "ETN": {q: 80 * (1 + 0.02 * np.sin(i)) for i, q in enumerate(qs)}}      # unrelated
    b = CL.build({"capex": cap, "rev": rev})
    by = {r["sym"]: r for r in b["rows"]}
    assert by["MU"]["corr"] > 0.9 and by["MU"]["slope"] > 1 and by["MU"]["if_flat"] < by["MU"]["rev_yoy"]
    assert abs(by["ETN"]["corr"]) < 0.5
    from tools import site_capex as SC
    assert SC.tier(by["ETN"]) == "數據看不出關係" and SC.tier(by["MU"]).startswith("明確依賴")
    CL._save({"capex": cap, "rev": rev})
    h = SC.sec_ai_capex(None)
    assert 'id="ai-capex"' in h and "最受傷的是" in h and "回到重點" in h and "不是投資建議" in h


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
