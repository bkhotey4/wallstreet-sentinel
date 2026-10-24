"""Taiwan foreign futures OI, VIX term structure, 52-week NH−NL, sidebar search / pins / swipe, event links, calculator fill.
Run: python -m tests.test_watch2"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_w2_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def _mkt(series):
    return types.SimpleNamespace(series=lambda t: series.get(t, pd.Series(dtype=float)), q=lambda t: None)


def test_tw_foi():
    from wsb.data import tw_futures as TF
    days = pd.bdate_range("2018-06-05", "2026-10-22")
    rows = []
    for i, d in enumerate(days):
        net = int(20000 * np.sin(i / 60)) - (90000 if d == days[-1] else 0)
        rows += [{"date": d.strftime("%Y-%m-%d"), "institutional_investors": "外資", "long_open_interest_balance_volume": max(net, 0) + 50000,
                  "short_open_interest_balance_volume": max(-net, 0) + 50000},
                 {"date": d.strftime("%Y-%m-%d"), "institutional_investors": "投信", "long_open_interest_balance_volume": 1, "short_open_interest_balance_volume": 2}]
    net = TF.parse(rows)
    assert len(net) == len(days) and net[days[-1].strftime("%Y-%m-%d")] < -80000
    d = TF.load()
    d["net"] = net
    TF.FILE.write_text(__import__("json").dumps(d), encoding="utf-8")
    tw = pd.Series(np.linspace(10000, 23000, len(days)), index=days)
    v = TF.view(types.SimpleNamespace(market=_mkt({"^TWII": tw})))
    assert v["pct"] < 1 and v["emoji"] == "🔴" and all(x["crossed"] for x in v["lines"]) and sum(r["now"] for r in v["rows"]) == 1
    from tools import site_watch2 as SW
    h = SW.sec_tw_foi(types.SimpleNamespace(market=_mkt({"^TWII": tw})))
    assert "外資台指期淨未平倉" in h and "什麼是外資台指期淨未平倉" in h and "已跌破" in h


def test_vix_term():
    from wsb.analytics import vol_breadth as VB
    idx = pd.bdate_range("2008-01-01", "2026-10-23")
    rng = np.random.default_rng(3)
    v3 = pd.Series(20 + rng.normal(0, 1, len(idx)), index=idx)
    v = v3 * (0.9 + 0.2 * (np.arange(len(idx)) % 50 == 0))
    v.iloc[-1] = v3.iloc[-1] * 1.08
    spx = pd.Series(np.cumprod(1 + rng.normal(0.0003, 0.01, len(idx))) * 100, index=idx)
    e = types.SimpleNamespace(market=_mkt({"^VIX": v, "^VIX3M": v3, "^VIX9D": v * 1.02, "^GSPC": spx}))
    r = VB.vix_term(e)
    assert r["ratio"] > 1 and r["emoji"] == "🔴" and r["bt"]["inv"]["n"] > 50 and r["bt"]["all"]["crash"] is not None
    from tools import site_watch2 as SW
    assert "逆價差" in SW.sec_vix_term(e)


def test_nh_nl():
    from wsb.analytics import vol_breadth as VB
    idx = pd.bdate_range("2024-09-01", periods=520)
    cols = [f"S{i}" for i in range(80)]
    up = np.linspace(100, 200, 520)
    df = pd.DataFrame({c: up * (1 + 0.001 * k) for k, c in enumerate(cols)}, index=idx)
    df.iloc[-1, :60] = df.iloc[:-1, :60].min().values * 0.9                  # 60 stocks crash to new lows on the last day
    spx = pd.Series(up, index=idx)
    e = types.SimpleNamespace(market=_mkt({"^GSPC": spx}), stockprices=types.SimpleNamespace(close=df))
    r = VB.nh_nl(e)
    assert r["nl"] == 60 and r["nh"] == 20 and r["diff"] == -40


def test_sidebar_and_refinements():
    from tools import site_layout as SLY
    from tools import site_calc as SC
    from tools import site_events as SEV
    names = {"overview": ("總覽", "Overview"), "risk": ("風險模型", "Risk")}
    side = SLY.sidebar(names, "overview", {"risk": [("c-risk-1", "金絲雀", "Canary"), ("c-risk-2", "雷達", "Radar")]})
    assert 'id="qsearch"' in side and 'id="pinned"' in side and side.count('class="ppin"') == 2
    js = SLY.js(names)
    assert "wss_pins" in js and "touchend" in js and "key==='/'" in js
    assert 'id="sz_hold"' in SC.sec_sizing(None) and "wss_portfolio_v1" in SC.JS
    assert "federalreserve.gov/monetarypolicy/fomccalendars.htm" in SEV.LINKS["fomc"][0][1]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
