"""財報走向判斷: signals use only past data, banks need two signals, the forecast falls back to 'next = this quarter'
when the regression is not better, returns before the price history are skipped, and the card has no trading words.
Run: python -m tests.test_fund_trend"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ft_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import fund_trend as F  # noqa: E402
from wsb.analytics.stock_check import _qs  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "加碼參考區", "進場參考區")
QS = _qs("2026Q2", 60)


def _co(seed, drift=0.02, improve=False):
    rng = np.random.default_rng(seed)
    rev = 100 * np.cumprod(1 + drift + rng.normal(0, 0.02, len(QS)))
    gm = 0.4 + (np.linspace(0, 0.08, len(QS)) if improve else 0) + rng.normal(0, 0.005, len(QS))
    nm = 0.15 + (np.linspace(0, 0.08, len(QS)) if improve else 0) + rng.normal(0, 0.005, len(QS))
    p = {"rev": dict(zip(QS, rev)), "gp": dict(zip(QS, rev * gm)), "ni": dict(zip(QS, rev * nm)),
         "ocf": dict(zip(QS, rev * (nm + 0.05))), "capex": dict(zip(QS, rev * 0.04)), "name": f"CO{seed}"}
    if improve:                                                   # growth speeds up at the end
        for i, q in enumerate(QS[-6:]):
            for k in ("rev", "gp", "ni", "ocf", "capex"):
                p[k][q] *= 1 + 0.04 * (i + 1)
    return p


def test_signals_and_labels():
    df = F.score(F.panel(_co(1, improve=True)))
    assert df["label"].iloc[-1] == "up" and df["n_sig"].iloc[-1] == 4
    b = F.score(F.panel({k: v for k, v in _co(2).items() if k in ("rev", "ni", "name")}, bank=True), bank=True)
    assert b["n_sig"].iloc[-1] == 2 and b["label"].iloc[-1] is not None


def test_forecast_and_track():
    panels = {f"S{i}": F.panel(_co(i)) for i in range(12)}
    m = F.forecast_model(panels)
    assert m and m["rmse"] > 0 and (m["model"] or m["b"] is None)
    if not m["model"]:
        assert F.predict(m, 12.0, 3.0) == 12.0
    idx = pd.date_range("2020-10-26", periods=320, freq="W-MON")
    px = {s: pd.Series(100 * np.cumprod(1 + np.random.default_rng(i).normal(0.002, 0.03, len(idx))), index=idx) for i, s in enumerate(panels)}
    t = F.track({s: F.score(df) for s, df in panels.items()}, px)
    for lab in ("up", "flat", "down"):
        r = t.get(lab) or {}
        if r.get("from"):
            assert r["from"] >= "2020Q3"                              # no return before the prices start


def test_card_plain():
    from tools import site_stockcheck as S
    h = S.sec_fund_trend(None)                                        # empty cache → nothing, no crash
    assert h == "" or "財報走向判斷" in h
    r = {"name": "X", "label": "down", "g": 5.0, "accel": -3.0, "gm": None, "nm": -1.0, "fcf": 0.5, "next_g": 5.0}
    txt = F.plain(r, "某公司", {"model": False, "rmse": 9.0})
    assert "轉弱中" in txt and "放慢 3.0" in txt and "若維持本季速度" in txt and "±9" in txt
    for w in BANNED:
        assert w not in txt + F.watch({"s_accel": -1}, False)


def test_finmind_cashflow_split_and_tw_universe():
    from wsb.data import fund_global as G
    inc = [{"date": f"2025-{m:02d}-{d}", "type": t, "value": v} for (m, d) in ((3, 31), (6, 30), (9, 30), (12, 31))
           for t, v in (("Revenue", 100.0), ("GrossProfit", 40.0), ("IncomeAfterTaxes", 10.0))]
    inc += [{"date": f"{y}-03-31", "type": "Revenue", "value": 90.0} for y in range(2018, 2025)]
    cfl = [{"date": "2025-03-31", "type": "NetCashInflowFromOperatingActivities", "value": 30.0},
           {"date": "2025-06-30", "type": "NetCashInflowFromOperatingActivities", "value": 70.0},
           {"date": "2025-06-30", "type": "PropertyAndPlantAndEquipment", "value": -50.0},
           {"date": "2025-03-31", "type": "PropertyAndPlantAndEquipment", "value": -20.0}]
    p = G.parse_finmind(inc, cfl)
    assert p["ocf"]["2025Q1"] == 30 and p["ocf"]["2025Q2"] == 40          # year-to-date split back into quarters
    assert p["capex"]["2025Q2"] == 30 and p["rev"]["2025Q4"] == 100
    rows = [{"sym": "2330.TW", "code": "2330", "ind": "半導體"}, {"sym": "2881.TW", "code": "2881", "ind": G.TW_FIN},
            {"sym": "1101.TW", "code": "1101", "ind": "水泥"}]
    u = G.tw_universe(rows, {"2330": 26e9, "2881": 13e9, "1101": 7e9}, {"2330": 1000, "2881": 90, "1101": 25}, 5)
    assert [r["code"] for r in u] == ["2330", "1101"]                        # financials kept out, biggest first


def _hk(seed, up):
    rng = np.random.default_rng(seed)
    ys = [f"FY{y}" for y in range(2021, 2026)]
    rev = 100 * np.cumprod(1 + (np.array([0.02, 0.03, 0.05, 0.09, 0.15]) if up else np.array([0.1, 0.06, 0.03, 0.0, -0.04])) + rng.normal(0, 0.005, 5))
    nm = np.linspace(0.1, 0.16, 5) if up else np.linspace(0.16, 0.1, 5)
    return {"rev": dict(zip(ys, rev)), "gp": dict(zip(ys, rev * (nm + 0.3))), "ni": dict(zip(ys, rev * nm)),
            "ocf": dict(zip(ys, rev * (nm + 0.05))), "capex": dict(zip(ys, rev * 0.03))}


def test_hk_annual_uses_peer_scale():
    uni = [{"sym": f"{i:04d}.HK", "name": f"H{i}", "ind": "港股"} for i in range(12)]
    facts = {u["sym"]: _hk(i, i % 2 == 0) for i, u in enumerate(uni)}
    b = F.build_market("hk", uni, facts)
    assert b and b["annual"] and b["model"] is None and not b["track"] and b["scale"]
    lab = {r["sym"]: r["label"] for r in b["rows"]}
    assert lab["0000.HK"] == "up" and lab["0001.HK"] == "down"
    from tools import site_stockcheck as S
    j = S.market_json(b)
    assert j["cols"] == S.FT_COLS and len(j["rows"]) == 12 and "0000" in [r[0] for r in j["rows"]]


def test_card_three_markets(monkeypatch=None):
    from tools import site_stockcheck as S
    uni = [{"sym": f"{i:04d}.HK", "name": f"H{i}", "ind": "港股"} for i in range(12)]
    hk = F.build_market("hk", uni, {u["sym"]: _hk(i, i % 2 == 0) for i, u in enumerate(uni)})
    us_uni = [{"sym": f"S{i}", "name": f"S{i}", "ind": "科技"} for i in range(12)]
    us = F.build_market("us", us_uni, {f"S{i}": _co(i, improve=i < 4) for i in range(12)})
    old = F.build
    F.build = lambda *a, **k: {"markets": {"us": us, "hk": hk}, "skip": {"us": 3}, "tw_fin": 40}
    try:
        h = S.sec_fund_trend(None)
    finally:
        F.build = old
    assert "美股 12 家裡" in h and "港股" in h and "年報" in h and 'data-kind="ftus"' in h and 'data-kind="fthk"' in h
    assert "3 家沒列" in h and "40 家" in h
    for w in BANNED:
        assert w not in h


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
