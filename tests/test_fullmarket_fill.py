"""Full-market price repairs (11-21): official 台股 closes replace Yahoo's missing / intraday bar, and a bar downloaded
before the close is re-fetched once.  Run: python -m tests.test_fullmarket_fill"""
import numpy as np
import pandas as pd

from wsb.analytics import fullscan as FS
from wsb.data import fullmarket as FM


def test_official_fill():
    idx = pd.to_datetime(["2026-11-18", "2026-11-19", "2026-11-20"])
    close = pd.DataFrame({"2330.TW": [2175.0, 2100.0, np.nan], "2317.TW": [200.0, 199.0, 191.0], "1101.TW": [30.0, 30.0, 30.0]}, idx)
    vol = pd.DataFrame({"2330.TW": [1e7, 1e7, np.nan], "2317.TW": [5e6, 5e6, 4e6]}, idx)
    q = {"2330.TW": {"price": 2000.0, "asof": "2026-11-20", "volume": 9e7},
         "2317.TW": {"price": 189.5, "asof": "2026-11-20", "volume": 8e6},       # Yahoo's 191 was an intraday price
         "9999.TW": {"price": 10.0, "asof": "2026-11-20"},                         # not in the file → not added
         "1101.TW": {"price": 29.0, "asof": "2026-10-01"}}                         # too old → ignored
    c, v, n = FS.official_fill(close, vol, q)
    assert c.at[pd.Timestamp("2026-11-20"), "2330.TW"] == 2000.0 and c.at[pd.Timestamp("2026-11-20"), "2317.TW"] == 189.5
    assert v.at[pd.Timestamp("2026-11-20"), "2330.TW"] == 9e7 and "9999.TW" not in c.columns
    assert c.at[pd.Timestamp("2026-11-20"), "1101.TW"] == 30.0 and n == 2
    assert np.isnan(close.at[pd.Timestamp("2026-11-20"), "2330.TW"])           # the input frame is not mutated


def test_close_epoch():
    e = FM.close_epoch("tw", pd.Timestamp("2026-11-20"))
    assert e == pd.Timestamp("2026-11-20 05:30", tz="UTC").timestamp()
    assert FM.close_epoch("jp", pd.Timestamp("2026-11-20")) == pd.Timestamp("2026-11-20 06:30", tz="UTC").timestamp()
    assert FM.close_epoch("xx", pd.Timestamp("2026-11-20")) is None


def test_partial_bar_refetched():
    import json
    import tempfile
    import time
    from pathlib import Path
    from unittest.mock import patch
    from wsb.data import stocks as ST
    tmp = Path(tempfile.mkdtemp())
    idx = pd.bdate_range("2026-10-01", "2026-11-20")
    close = pd.DataFrame({"AAA.TW": np.linspace(10, 12, len(idx)), "BBB.TW": np.linspace(20, 22, len(idx))}, idx)
    ref = idx[-1]
    ce = FM.close_epoch("tw", ref)
    calls = []

    def fake(part, period):
        calls.append(list(part))
        cl = close[part].copy()
        cl.iloc[-1] = cl.iloc[-1] + 0.5                     # the final close differs from the intraday bar
        return cl, pd.DataFrame(1.0, index=cl.index, columns=part)
    with patch.object(FM, "DATA_DIR", tmp), patch.object(ST, "_download", fake), patch.object(FM, "cfg", lambda: {"pause_s": 0}):
        FM.save_prices("tw", close, pd.DataFrame(1.0, index=idx, columns=close.columns))
        (tmp / "fullmarket_upd_tw.json").write_text(json.dumps({"AAA.TW": ce - 3600, "BBB.TW": ce + 600}))   # AAA before the close
        with patch.object(time, "time", lambda: ce + 7200):
            st = FM.refresh_prices("tw", ["AAA.TW", "BBB.TW"], ref, ce + 7200 + 60)
        c2, _ = FM.load_prices("tw")
    assert calls == [["AAA.TW"]], calls
    assert abs(c2.at[ref, "AAA.TW"] - (12 + 0.5)) < 1e-9 and c2.at[ref, "BBB.TW"] == 22
    nob = json.loads((tmp / "fullmarket_nobar_tw.json").read_text()) if (tmp / "fullmarket_nobar_tw.json").exists() else {}
    assert "AAA.TW" not in nob and st["updated"] == 1


def test_parse_jpx():
    import io
    df = pd.DataFrame({"日付": ["20261031"] * 5, "コード": ["1301", "1305", "130A", "9984", "2001"],
                       "銘柄名": ["極洋", "ＥＴＦ", "Ｖｅｒｉｔａｓ", "ソフトバンクグループ", "プロ"],
                       "市場・商品区分": ["プライム（内国株式）", "ETF・ETN", "グロース（内国株式）", "プライム（内国株式）", "PRO Market"],
                       "33業種区分": ["水産・農林業", "-", "医薬品", "情報・通信業", "-"]})
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    rows = FM.parse_jpx(buf.getvalue())
    assert [r["sym"] for r in rows] == ["1301.T", "130A.T", "9984.T"]
    assert rows[1]["name"] == "Veritas" and rows[1]["board"] == "東證 Growth" and rows[2]["ind"] == "資訊通信"


if __name__ == "__main__":
    test_parse_jpx()
    test_partial_bar_refetched()
    test_official_fill()
    test_close_epoch()
    print("ok fullmarket fill")
