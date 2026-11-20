"""Bulk daily download NaN → close from chart meta (11-21 Nikkei / Hang Seng / TAIEX).  Run: python -m tests.test_meta_close"""
import numpy as np
import pandas as pd

from wsb.data import market as MK


def test_fill_meta_close():
    idx = pd.to_datetime(["2026-11-19", "2026-11-20"])
    df = pd.DataFrame({"^N225": [59444.21, np.nan], "^GSPC": [7175.83, 6910.39], "HOLI": [10.0, np.nan], "OPEN": [5.0, np.nan]}, idx)
    fri = pd.Timestamp("2026-11-20 06:45", tz="UTC").timestamp()          # 15:45 Tokyo
    metas = {"^N225": {"regularMarketPrice": 56436.65, "regularMarketTime": fri, "gmtoffset": 32400,
                       "currentTradingPeriod": {"regular": {"end": fri - 900}}},
             "HOLI": {"regularMarketPrice": 9.0, "regularMarketTime": fri - 86400 * 2, "gmtoffset": 0},     # holiday: meta is older
             "OPEN": {"regularMarketPrice": 6.0, "regularMarketTime": fri, "gmtoffset": 0,
                      "currentTradingPeriod": {"regular": {"end": fri + 3600}}}}                         # session still open
    out = MK.fill_meta_close(df.copy(), fetch=lambda t: metas.get(t), now=fri + 60)
    assert out.loc["2026-11-20", "^N225"] == 56436.65
    assert np.isnan(out.loc["2026-11-20", "HOLI"]) and np.isnan(out.loc["2026-11-20", "OPEN"])
    assert out.loc["2026-11-20", "^GSPC"] == 6910.39


if __name__ == "__main__":
    test_fill_meta_close()
    print("ok test_fill_meta_close")
