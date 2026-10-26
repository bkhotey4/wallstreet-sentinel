"""Whole-market check-up: exchange P/E parsing, month-end sampling, the historical-multiple range, split handling for US
prices, the neutral labels, and the card's wording."""
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

os.environ["WSB_DATA_DIR"] = tempfile.mkdtemp()                       # never touch the real data_cache
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wsb.analytics import fullscan as FS  # noqa: E402
from wsb.data import valhist as VH  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出")


def test_parsers():
    twse = {"stat": "OK", "fields": ["證券代號", "證券名稱", "收盤價", "殖利率(%)", "股利年度", "本益比", "股價淨值比", "財報年/季"],
            "data": [["2330", "台積電", "1,050.00", "1.52", 114, "22.10", "6.80", "115/2"], ["1101", "台泥", "30", "2.8", 114, "-", "0.9", "115/2"]]}
    r = VH.parse_twse(twse)
    assert r["2330"] == [22.1, 6.8, 1.52] and r["1101"][0] is None
    tpex = {"tables": [{"fields": ["股票代號", "公司名稱", "本益比", "每股股利", "股利年度", "殖利率(%)", "股價淨值比"],
                        "data": [["6488", "環球晶", "15.5", "10", 114, "3.1", "2.2"]]}]}
    assert VH.parse_tpex(tpex) == {"6488": [15.5, 2.2, 3.1]}
    assert VH.parse_twse({"stat": "很抱歉，沒有符合條件的資料!"}) == {}


def test_month_ends():
    m = VH.month_ends(date(2026, 3, 10), 3)
    assert m == [date(2026, 2, 28), date(2026, 1, 31), date(2025, 12, 31)]


def test_zone_math():
    hist = [10.0] * 10 + [20.0] * 10 + [30.0] * 10
    z = VH._zone(hist, 15.0, 150.0)
    assert z["m50"] == 20.0 and abs(z["p50"] - 200.0) < 1e-9 and abs(z["pct"] - 100 / 3) < 1e-6
    assert VH._zone(hist[:10], 15.0, 150.0) is None                   # too short a history
    assert VH._zone(hist, -5.0, 150.0) is None                        # losses never get a P/E range


def test_unadjust_splits():
    m = {"2023-06": 40.0, "2025-06": 200.0}
    sp = [["2024-06-10", 10.0]]
    assert VH._unadj(m, sp, "2023-06") == 400.0 and VH._unadj(m, sp, "2025-06") == 200.0


def test_zones_tw_from_archive():
    snaps = {f"20{21 + i // 12}-{i % 12 + 1:02d}-28": {"2330": [10.0 + i % 10, 3.0, 2.0]} for i in range(30)}
    VH.save("tw", {"snaps": snaps, "latest": {"date": "2026-10-23", "rows": {"2330": [12.0, 3.0, 2.0], "9999": [None, 1.0, 0]}}})
    z = VH.zones_tw({"2330": 600.0, "9999": 20.0})
    assert z["2330"]["metric"] == "本益比" and z["2330"]["p25"] < z["2330"]["p50"] < z["2330"]["p75"]
    assert "9999" not in z                                            # P/B history too short for the loss-maker


def test_labels():
    up = FS.labels({"px": 110, "ma2": 100, "hi52": 120, "m121": 15, "rsi": 75})
    assert up == {"lt": "多頭", "ldd": -8.3, "lr": "偏熱"}
    assert FS.labels({"px": 80, "ma2": 100, "m121": -10, "rsi": 25})["lt"] == "空頭"
    assert FS.labels({"px": 105, "ma2": 100, "m121": -3})["lt"] == "盤整"
    v = FS.val_fields({"metric": "本益比", "now": 12.0, "pct": 30.0, "p25": 90.0, "p50": 100.0, "p75": 120.0, "n": 40, "asof": "2026-10-23"})
    assert v["vm"] == "本益比" and v["vp50"] == 100.0 and all(c in FS.COLS for c in v)


def test_card_wording():
    from tools import site_marks as SM
    h = SM.sec_marks(None)
    t = re.sub(r"<[^>]+>", " ", h)
    assert "一句話看懂" in t and "港股沒有免費的歷史估值資料" in t and 'id="mkbox"' in h
    assert not [b for b in BANNED if b in t + SM.JS], [b for b in BANNED if b in t + SM.JS]


def main():
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)


if __name__ == "__main__":
    main()
