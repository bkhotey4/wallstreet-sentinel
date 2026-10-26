"""風險雙軌 + 外資台指期小標籤 + 危機成績單隨機基準 + 2000 網路泡沫情境 + 持股股息/回撤 + 自選股 + 手機常用分頁.
Run: python -m tests.test_dual"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_dual_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_dual as SD  # noqa: E402


def test_combo_and_card():
    assert "表面平靜" in SD.combo(0, 4, 4, 7) and "正在升溫，而且" in SD.combo(3, 4, 4, 7)
    assert "一般的修正" in SD.combo(3, 4, 0, 7) and "兩邊都平靜" in SD.combo(0, 4, 1, 7)
    assert "一些燃料" in SD.combo(2, 4, 3, 7) and "表面平靜" in SD.combo(0, 4, 1, 7, rzone=True)
    SD.thermo = lambda e: [("壓力指數 SSI", True, "60"), ("VIX 期限結構", False, "0.9")]
    SD.fuel = lambda e: {"n": 3, "n_hot": 2, "lights": [{"zh": "信用", "state": "hot", "txt": "高"}, {"zh": "利差", "state": "hot", "txt": "低"},
                                                         {"zh": "放款", "state": "ok", "txt": "收緊"}]}
    h = SD.sec_dual(None)
    assert "一句話看懂" in h and "溫度計 2 項有 1 項偏緊" in h and "燃料箱 3 盞有 2 盞過熱" in h and "不是投資建議" in h
    assert "底下燃料多" in h                                                        # 2 of 3 is at least half


def test_foi_badge():
    from tools import site_watch2 as SW2
    SW2._tw = lambda e: {"emoji": "🔴", "net": -41234, "band": "空方警戒", "since": "2018", "pct": 3.2, "date": "2026-10-23"}
    h = SD.foi_badge(None)
    assert "外資台指期空單 4.1 萬口（2018 年來最多・10-23）" in h and 'data-p="taiwan"' in h
    SW2._tw = lambda e: {"emoji": "🟢", "net": 15000, "band": "", "since": "2018", "pct": 60, "date": "2026-10-23"}
    assert "多單 1.5 萬口（一般水準" in SD.foi_badge(None)


def test_pages_ship_new_parts():
    from tools import site_live as SL, site_portfolio as SP, site_layout as LY
    assert "wss_watch_v1" in SL.JS and "full=1" in SL.JS and "自選股" in SL.sec_watch(None)
    assert "dotcom2000" in SP.JS and "renderDiv" in SP.JS and "paintDD" in SP.JS
    assert "距 52 週高點" in open(SP.__file__, encoding="utf-8").read()
    assert "dotcom2000" in SP.CRISIS_WINDOWS and SP.CRISIS_PROXY_AT["dotcom2000"]["front"][0] == "^NDX"
    assert 'id="qtabs"' in LY.topnav() and "drawQuick" in LY.js({"overview": ("總覽", "Overview")})


def test_gap_line():
    from tools import site_intel as SI
    import pandas as pd
    eng = types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: pd.Series([20000.0])))
    lk = {"index": [{"tw_n": "台股加權", "us_n": "費半", "us_ret": -3.0, "beta": 0.5, "implied": -1.5, "tw": None}]}
    g = SI.gap_line(eng, lk)
    assert "-1.50%" in g and "-300 點" in g
    lk["index"][0]["tw"] = -1.0
    assert SI.gap_line(eng, lk) is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
