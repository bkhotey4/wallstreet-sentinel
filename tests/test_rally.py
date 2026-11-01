"""盤中全面上漲: σ-based gate (own normal move), breadth (US sector ETFs, Taiwan official close file / 台積電 intraday), level 2 only with a non-equity confirmation,
honest history text, one ribbon item per market (the 2σ index item is not repeated) — and no trading words.
Run: python -m tests.test_rally"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rl_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

DAY = "2026-10-30"
NOW = datetime(2026, 10, 30, 18, 0, tzinfo=timezone.utc)          # 14:00 New York, 02:00 Taipei (next day)
IDX = pd.bdate_range(end=DAY, periods=900)


def _walk(seed):
    rng = np.random.default_rng(seed)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, len(IDX)))), index=IDX)


class M:
    def __init__(self, ser, quotes):
        self.ser, self.quotes = ser, quotes

    def series(self, t):
        return self.ser.get(t, pd.Series(dtype=float))

    def q(self, t):
        return self.quotes.get(t)


class E:
    pass


def _eng(spx_x, vix_x=0.0, heavy_up=9, credit_x=0.0):
    from wsb.analytics import rally as R
    ser = {t: _walk(i) for i, (t, *_r) in enumerate(R.US)}
    sd = {t: R.normal_sd(s) for t, s in ser.items()}
    qt = {"^GSPC": {"chg_pct": spx_x * sd["^GSPC"], "asof": DAY}, "^VIX": {"chg_pct": -vix_x * sd["^VIX"], "asof": DAY},
          "HYG": {"chg_pct": credit_x * sd["HYG"], "asof": DAY}, "KRE": {"chg_pct": credit_x * sd["KRE"], "asof": DAY}}
    for i, t in enumerate(R.SECTORS):
        qt[t] = {"chg_pct": 1.2 if i < heavy_up else -0.4, "asof": DAY}
    e = E()
    e.market = M(ser, qt)
    return e


def test_gate_and_levels():
    from wsb.analytics import rally as R
    e = _eng(1.2)                                       # index up only 1.2x its normal move → nothing
    assert R.score("us", e.market.q, e.market.series, DAY)["level"] == 0
    e = _eng(2.0, heavy_up=6)                           # strong index but only 6 of 11 sectors up → nothing
    assert R.score("us", e.market.q, e.market.series, DAY)["level"] == 0
    e = _eng(2.0)                                       # equities only → level 1
    r = R.score("us", e.market.q, e.market.series, DAY)
    assert r["level"] == 1 and not r["non_eq"], r
    e = _eng(2.0, vix_x=2.0, credit_x=1.2)              # VIX and credit confirm → level 2
    r = R.score("us", e.market.q, e.market.series, DAY)
    assert r["level"] == 2 and set(r["non_eq"]) == {"波動率", "信用"}, r


def test_stale_quote_ignored():
    from wsb.analytics import rally as R
    e = _eng(2.0, vix_x=3.0, credit_x=3.0)
    for t in ("^VIX", "HYG", "KRE"):
        e.market.quotes[t]["asof"] = "2026-10-29"       # yesterday's prints must not confirm today
    assert R.score("us", e.market.q, e.market.series, DAY)["level"] == 1


def test_day_of_session():
    from wsb.analytics import rally as R
    e = _eng(2.0)
    assert R.day_of("us", e.market.q, NOW) == DAY
    assert R.day_of("us", e.market.q, datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)) is None   # 08:00 NY, before the open
    assert R.day_of("us", e.market.q, datetime(2026, 10, 31, 18, 0, tzinfo=timezone.utc)) is None   # Saturday


def test_history_and_text():
    from wsb.analytics import rally as R
    h = R.history(_walk(7))
    assert h and h["n"] > 0 and 0 <= h[20]["up"] <= 100 and "all_up" in h[5]
    e = _eng(2.0, vix_x=2.0, credit_x=1.2)
    r = R.score("us", e.market.q, e.market.series, DAY)
    t = R.detail(r, h)
    assert "平常單日" in t and "類股 9/11" in t and "之後 5 天" in t and "不是買賣建議" in t
    for w in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "加碼", "進場參考區"):
        assert w not in t, w


def test_web_alert_once_per_market():
    from wsb.analytics import web_alerts as W
    e = _eng(2.6, vix_x=2.0, credit_x=1.2)
    out = []
    from wsb.analytics import rally as R
    orig = R._tw_close
    R._tw_close = lambda: {}
    try:
        W._rally(e, out, NOW)
    finally:
        R._tw_close = orig
    assert len(out) == 1 and out[0]["key"] == f"rally:us:{DAY}:2" and out[0]["tone"] == "good" and out[0]["lv"] == "watch"
    assert "全面偏多" in out[0]["zh"] and out[0]["tab"] == "overview"
    W._momentum(e, out, NOW)                            # the 2σ ^GSPC item would repeat the same news
    assert not [x for x in out if x["key"].startswith("mom:^GSPC")]


def test_taiwan_breadth_paths():
    from wsb.analytics import rally as R
    ser = {t: _walk(20 + i) for i, (t, *_r) in enumerate(R.TW)}
    sd = {t: R.normal_sd(s) for t, s in ser.items()}
    qt = {"^TWII": {"chg_pct": 2.0 * sd["^TWII"], "asof": DAY}, "2330.TW": {"chg_pct": 0.5 * sd["2330.TW"], "asof": DAY},
          "TWD=X": {"chg_pct": -1.5 * sd["TWD=X"], "asof": DAY}, "^N225": {"chg_pct": 1.2 * sd["^N225"], "asof": DAY}}
    e = E()
    e.market = M(ser, qt)
    assert R.score("tw", e.market.q, e.market.series, DAY, {})["level"] == 0          # intraday, 台積電 lagging → nothing
    qt["2330.TW"]["chg_pct"] = 1.5 * sd["2330.TW"]
    r = R.score("tw", e.market.q, e.market.series, DAY, {})
    assert r["level"] == 2 and r["breadth"] is None and "收盤後才有" in R.detail(r, None)   # TWD inflow confirms
    close = {f"{1101 + i}.TW": {"chg_pct": (1.0 if i % 10 < 6 else -1.0), "asof": DAY} for i in range(400)}
    close["0050.TW"] = {"chg_pct": 5.0, "asof": DAY}                                   # ETFs are not counted
    r = R.score("tw", e.market.q, e.market.series, DAY, close)
    assert r["breadth"]["n"] == 400 and r["level"] == 0                               # only 60 % of stocks up → nothing


if __name__ == "__main__":
    fails = 0
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            try:
                f()
                print("ok  ", n)
            except Exception as ex:  # noqa: BLE001
                fails += 1
                print("FAIL", n, repr(ex))
    sys.exit(1 if fails else 0)
