"""想進場前，可以從哪裡想（11-21）。Run: python -m tests.test_entry_think"""
import numpy as np
import pandas as pd

from tools import site_entry_think as ET

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")


def test_lights():
    mg = {"2026-11-18": [5087.21, 5080.27], "2026-11-19": [5080.27, 4843.68], "2026-11-20": [4843.68, 4352.27]}
    assert ET.margin_check(mg)["light"] == "r"
    calm = {"2026-11-25": [4300.0, 4290.0], "2026-11-26": [4290.0, 4285.0], "2026-11-27": [4285.0, 4280.0]}
    assert ET.margin_check(calm)["light"] == "g"
    idx = pd.date_range("2026-01-01", periods=60, freq="B")
    vix = pd.Series(np.r_[np.full(40, 18.0), np.linspace(20, 36, 20)], idx)
    assert ET.vix_check(vix)["light"] == "r"
    vix2 = pd.Series(np.r_[np.full(40, 18.0), np.linspace(36, 22, 20)], idx)
    assert ET.vix_check(vix2)["light"] == "g"
    down = pd.Series(np.linspace(100, 80, 60), idx)
    assert ET.low_check(down)["light"] == "r"


def test_drops_and_block():
    idx = pd.date_range("2020-01-01", periods=400, freq="B")
    px = np.full(400, 100.0)
    px[100:] = 94.0                    # one −6 % day, never below it afterwards
    px[250:] = 88.0                    # a second −6.4 % day
    px[260:270] = 80.0                 # …which falls further
    px[270:] = 90.0
    s = pd.Series(px, idx)
    ev = ET.drops(s)
    assert [e["date"] for e in ev] == [idx[100].strftime("%Y-%m-%d"), idx[250].strftime("%Y-%m-%d")]
    assert ev[0]["dd60"] == 0.0 and abs(ev[1]["dd60"] - (80 / 88 - 1)) < 1e-9

    class M:
        quotes = {}

        def series(self, t):
            return s if t == "^TWII" else pd.Series(np.linspace(20, 30, 100), pd.date_range("2025-01-01", periods=100, freq="B"))

    class E:
        market = M()
    h = ET.block(E(), mg={"2026-11-20": [4843.68, 4352.27]})
    assert "想進場前，可以從哪裡想" in h and "🔴" in h and "先問自己四件事" in h
    assert not any(b in h for b in BANNED), [b for b in BANNED if b in h]


if __name__ == "__main__":
    test_lights()
    test_drops_and_block()
    print("ok entry think")
