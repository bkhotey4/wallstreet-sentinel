"""AI 泡沫計時器: Ken French parsing, episode / crash logic, groups, elephants back-test, cards.
Run: python -m tests.test_bubble"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import types
import zipfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_bb_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import bubble as BB  # noqa: E402


def _zip() -> bytes:
    months = pd.date_range("1950-01-01", periods=240, freq="MS")
    a = np.full(240, 0.005)
    a[60:84] = 0.035                       # ~+130% in 2 years …
    a[84:90] = -0.10                       # … then -47%
    b = np.full(240, 0.004)
    lines = ["header", "", "  Average Value Weighted Returns -- Monthly", ",Chips,Food "]
    lines += [f"{m:%Y%m},{x * 100:7.2f},{y * 100:7.2f}" for m, x, y in zip(months, a, b)]
    lines += ["", "  Average Equal Weighted Returns -- Monthly", ",Chips,Food ", "195001, 1, 1"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("49_Industry_Portfolios.csv", "\n".join(lines))
    return buf.getvalue()


def test_parse_and_episodes():
    ff = BB.parse_ff(_zip())
    assert set(ff) == {"Chips", "Food"} and len(ff["Chips"]) == 240 and "1950-01" in ff["Chips"]
    eps = BB.episodes(ff, lambda r, o, v: r >= 1.0)
    assert len(eps) == 1 and eps[0]["ind"] == "Chips" and eps[0]["crash"] and eps[0]["months"] <= 10
    s = BB.summarize(eps)
    assert s["n"] == 1 and s["p24"] == 100 and s["p12"] == 100
    assert BB.summarize([]) is None
    h = BB.history_table(ff)
    assert h["hot"]["1946"]["n"] == 1 and h["hot"]["1970"] is None and h["any"]["1946"]["n"] >= 2


def _eng(series):
    return types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: series.get(t, pd.Series(dtype=float)), q=lambda t: None))


def test_current_state_groups():
    idx = pd.bdate_range("2021-01-01", "2026-10-23")
    n = len(idx)
    rng = np.random.default_rng(3)
    x = np.linspace(0, 1, n)
    hot = pd.Series(100 * np.exp(2.2 * x ** 3) * np.exp(rng.normal(0, 0.004, n).cumsum() * 0.1), index=idx)
    hot.iloc[-80:] = hot.iloc[-81] * np.linspace(1, 0.75, 80)    # then falls 25 % off the high
    calm = pd.Series(100 * np.exp(0.0002 * np.arange(n)), index=idx)
    st = {r["sym"]: r for r in BB.current_state(_eng({"^SOX": hot, "^NDX": calm}))}
    assert st["^SOX"]["run"] >= 100 and st["^SOX"]["off"] <= -20 and st["^SOX"]["group"] in ("hot_fall_vol", "hot_fall")
    assert st["^NDX"]["group"] is None


def test_elephants():
    weeks = pd.date_range("2010-01-05", periods=600, freq="7D")
    am = np.r_[np.full(500, 30.0), np.linspace(30, 10, 100)]     # big money exits at the end
    rows = [[d.strftime("%Y-%m-%d"), float(a), 0.0] for d, a in zip(weeks, am)]
    px = pd.Series(np.linspace(100, 200, 4300), index=pd.bdate_range("2009-06-01", periods=4300))
    el = BB.elephants(_eng({"^NDX": px, "^GSPC": px}), {"209742": rows})
    assert len(el) == 1 and el[0]["state"] == "撤退" and el[0]["chg13"] < 0
    c = BB.parse_cftc([{"report_date_as_yyyy_mm_dd": "2026-10-20T00:00:00.000", "cftc_contract_market_code": "209742",
                        "open_interest_all": "1000", "asset_mgr_positions_long": "500", "asset_mgr_positions_short": "100",
                        "lev_money_positions_long": "100", "lev_money_positions_short": "300"}])
    assert c == {"209742": [["2026-10-20", 40.0, -20.0]]}


def test_cards():
    from tools import site_ai as SAI
    d = BB.load()
    d["ff"] = BB.parse_ff(_zip())
    BB._save(d)
    BB._CACHE.clear()
    idx = pd.bdate_range("2021-01-01", "2026-10-23")
    x = np.linspace(0, 1, len(idx))
    hot = pd.Series(100 * np.exp(2.2 * x ** 3), index=idx)
    hot.iloc[-80:] = hot.iloc[-81] * np.linspace(1, 0.75, 80)
    e = _eng({"^SOX": hot})
    h = SAI.sec_ai_bubble(e)
    assert 'id="ai-bubble"' in h and "不猜日期" in h and "回到重點" in h and "Bubbles for Fama" in h
    assert SAI.sec_ai_elephant(e) == ""                          # no CFTC rows → no card
    assert "持倉總值" not in h and "未實現" not in h
    import time
    from tools import site_stamp as STP
    d = BB.load()
    d["ts_check"] = time.time()
    BB._save(d)
    s = STP.stamp(e, "sec_ai_bubble", "ai")
    assert "各來源最後檢查" in s and "產業歷史" in s and "檢查" in s and "資料日" in s, s


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
