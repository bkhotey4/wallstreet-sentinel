"""台灣加油站價格: CPC XML parsing and the year-over-year comparison with Brent in NT$.
Run: python -m tests.test_tw_fuel"""
from __future__ import annotations

import json
import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_fuel_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from wsb.data import tw_fuel as F  # noqa: E402


def test_parse_and_view():
    days = pd.date_range("2024-01-01", periods=150, freq="7D")
    xml = "".join(f"<tbTable><牌價生效時間>{d:%Y-%m-%d}T00:00:00+08:00</牌價生效時間><產品名>無鉛汽油95</產品名><參考牌價>{30 + i * 0.02:.2f}</參考牌價></tbTable>"
                  for i, d in enumerate(days))
    p = F.parse(xml)
    assert len(p) == 150
    F.FILE.write_text(json.dumps({"95": p, "diesel": p}), encoding="utf-8")
    idx = pd.date_range("2024-01-01", days[-1], freq="D")
    brent = pd.Series([80.0] * (len(idx) - 365) + [120.0] * 365, index=idx)
    v = F.view(brent, pd.Series(32.0, index=idx))
    assert v["rows"][0]["price"] == p[max(p)] and v["brent_yoy"] == 50.0
    from tools import site_energy as E
    import types
    eng = types.SimpleNamespace(market=types.SimpleNamespace(series=lambda k: brent if k == "BZ=F" else pd.Series(32.0, index=idx)))
    h = E.tw_fuel_block(eng)
    assert "台灣加油站" in h and "平穩機制" in h


if __name__ == "__main__":
    test_parse_and_view()
    print("TW FUEL TESTS PASSED [OK]")
