"""美股全市場財報判讀: the rules behind each tag, the frame-based extras (margin changes, receivables, inventory, capex),
and the card.  Run: python -m tests.test_usread"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_usread_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.analytics import usread as UR  # noqa: E402
from wsb.data import earnings_data as ED  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出")


def test_rules():
    r = UR.read({"q_yoy": 40.0, "accel": 8.0, "gm_chg": -3.0, "om_chg": 4.0, "ar_yoy": 80.0, "rev_q_yoy": 40.0, "ma": True,
                 "capex_pct": 120.0, "capex_y": "2025", "runway": 1.5, "burn": 1e9, "om": -10.0, "r40": 30.0})
    for t in ("加速成長", "以價換量", "營運槓桿", "應收帳款膨脹"):
        assert t in r["tags"], t
    assert r["tags"].count("・") == 3 and r["read"].count("。") == 4            # at most four tags and four sentences
    assert "年增 40%" in r["read"] and "快 8 個百分點" in r["read"]
    slow = UR.read({"q_yoy": 20.0, "accel": -15.0, "inv_yoy": 70.0, "capex_pct": 45.0, "capex_y": "2025"})
    assert "成長放緩" in slow["tags"] and "庫存堆積" in slow["tags"] and "重資本" in slow["tags"]
    assert "衰退收斂" in UR.read({"q_yoy": -8.0, "accel": 10.0})["tags"]
    assert UR.read({}) == {"tags": "", "read": ""}
    cash = UR.read({"q_yoy": 5.0, "runway": 0.8, "burn": 5e7, "om": -40.0, "r40": 60.0})
    assert "現金吃緊" in cash["tags"] and "虧損但成長夠快" in cash["tags"]
    for x in (r, slow, cash):
        assert not [b for b in BANNED if b in x["read"]]


def test_extras_from_frames():
    qs = ED.cy_quarters(date(2026, 10, 26), 10)                                 # CY2026Q4 … ; latest reported CY2026Q3
    now, ago = "CY2026Q3", "CY2025Q3"
    fr = {f"Revenues/{now}": {"v": {"1": 200.0}}, f"Revenues/{ago}": {"v": {"1": 100.0}},
          f"GrossProfit/{now}": {"v": {"1": 100.0}}, f"GrossProfit/{ago}": {"v": {"1": 60.0}},
          f"OperatingIncomeLoss/{now}": {"v": {"1": 40.0}}, f"OperatingIncomeLoss/{ago}": {"v": {"1": 10.0}},
          f"AccountsReceivableNetCurrent/{now}I": {"v": {"1": 90.0}}, f"AccountsReceivableNetCurrent/{ago}I": {"v": {"1": 30.0}},
          f"InventoryNet/{now}I": {"v": {"1": 1.0}}, f"InventoryNet/{ago}I": {"v": {"1": 1.0}},              # too small to matter
          "PaymentsToAcquirePropertyPlantAndEquipment/CY2025": {"v": {"1": 300.0}}, "Revenues/CY2025": {"v": {"1": 600.0}}}
    x = UR.extras(ED.FrameReader(fr, qs), "1", qs, "2026Q3", ["CY2026", "CY2025"])
    assert abs(x["gm_chg"] - (50 - 60)) < 1e-9 and abs(x["om_chg"] - (20 - 10)) < 1e-9
    assert abs(x["ar_yoy"] - 200) < 1e-9 and "inv_yoy" not in x and abs(x["capex_pct"] - 50) < 1e-9 and x["capex_y"] == "2025"
    assert UR.extras(ED.FrameReader(fr, qs), "1", qs, "2019Q1", ["CY2026"]) == {}


def test_card_and_tags():
    from tools import site_econ as SE
    h = SE.sec_us_read(None)
    assert "一句話看懂" in h and 'data-kind="ur"' in h and "不是投資建議" in h
    assert "ur:{src:'market/growth_us.json'" in SE.JS and "td.wrap" in SE.CSS
    assert "capex" in ED.FRAME_TAGS and UR.AR_TAG in ED.INSTANT_TAGS and UR.INV_TAG in ED.INSTANT_TAGS
    from wsb.analytics import growth as GR
    assert {"tags", "read", "gm_chg", "capex_pct"} <= set(GR.US_COLS)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
