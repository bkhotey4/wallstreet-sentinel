"""個股估值體檢: SEC quarter parsing (YTD, Q4 from the annual, splits), TTM with fiscal gaps, the three faces, P/E history,
reverse DCF, historical P/E scenarios and the card's neutral wording.
Run: python -m tests.test_stock_check"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_sck_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from wsb.analytics import stock_check as S  # noqa: E402


def _fact(s, e, v, filed="2026-01-01"):
    return {"start": s, "end": e, "val": v, "filed": filed}


def _cf(facts_by_tag):
    return {"facts": {"us-gaap": {t: {"units": u} for t, u in facts_by_tag.items()}}}


def test_quarters_ytd_q4_and_splits():
    rev = [_fact("2025-01-01", "2025-03-31", 10), _fact("2025-01-01", "2025-06-30", 22), _fact("2025-01-01", "2025-09-30", 36),
           _fact("2025-01-01", "2025-12-31", 52)]
    q = S.q_flow(_cf({"Revenues": {"USD": rev}}), "Revenues")
    assert q == {"2025Q1": 10, "2025Q2": 12, "2025Q3": 14, "2025Q4": 16}
    eps = [_fact("2025-01-01", "2025-03-31", 1.0, "2025-05-01"), _fact("2025-04-01", "2025-06-30", 1.0, "2025-08-01"),
           _fact("2025-07-01", "2025-09-30", 1.2, "2025-11-01"), _fact("2025-01-01", "2025-12-31", 4.6, "2026-02-01")]
    e = S.q_flow(_cf({"EarningsPerShareDiluted": {"USD/shares": eps}}), "EarningsPerShareDiluted", "USD/shares", additive=False)
    assert abs(e["2025Q4"] - 1.4) < 1e-9                                      # FY − Q1..Q3
    e2 = S.q_flow(_cf({"EarningsPerShareDiluted": {"USD/shares": eps}}), "EarningsPerShareDiluted", "USD/shares", False, [("2025-10-01", 10.0)])
    assert abs(e2["2025Q1"] - 0.1) < 1e-9 and abs(e2["2025Q4"] - (4.6 - 0.1 - 0.1 - 1.2)) < 1e-9   # only facts filed before the split shrink


def test_ttm_fiscal_gap():
    s = {"2025Q1": 1, "2025Q3": 1, "2025Q4": 1, "2026Q1": 1, "2026Q3": 1}       # 16-week quarter leaves 2026Q2 empty
    assert S.ttm(s, "2026Q3") == 4 and S.ttm({"2026Q3": 1}, "2026Q3") is None


def _p(eps_q=1.0, n=24):
    qs = S._qs("2026Q2", n)
    return {"name": "X", "rev": {q: 100 * 1.05 ** i for i, q in enumerate(qs)}, "gp": {q: 60 * 1.05 ** i for i, q in enumerate(qs)},
            "ni": {q: 20.0 for q in qs}, "ocf": {q: 30.0 for q in qs}, "capex": {q: 5.0 for q in qs}, "eps": {q: eps_q for q in qs},
            "shares": {q: 100.0 for q in qs}, "equity": {q: 200.0 for q in qs}, "cur_assets": {"2026Q2": 150.0}, "cur_liab": {"2026Q2": 100.0},
            "cash": {"2026Q2": 50.0}, "ltd": {"2026Q2": 20.0}}


def test_faces_and_valuation():
    f = S.faces(_p())
    assert f["g_grade"] == "強" and f["s_grade"] == "穩" and f["p_grade"] == "高" and abs(f["roe"] - 40) < 1e-9
    idx = pd.date_range("2021-06-04", "2026-10-23", freq="W-FRI")
    px = pd.Series([80.0] * (len(idx) - 1) + [100.0], index=idx)
    r = S.one("X", _p(), px, fpe=20.0)
    assert abs(r["pe"] - 25) < 1e-9 and r["pe_pct"] > 95                    # 100 ÷ (4 × 1.0) vs 20× history
    assert r["scen"]["src"] == "分析師預估" and abs(r["scen"]["px"][1] - 20 * 5.0) < 1e-6
    ev = r["ev"]
    assert abs(S.pv_equity(100.0, r["ig"] / 100) - 0) > 0 and abs(S.pv_equity(f["fcf"], r["ig"] / 100) - ev) / ev < 1e-6
    assert r["ig8"] < r["ig"] < r["ig10"]
    thin = _p()
    thin["capex"] = {q: 28.0 for q in thin["capex"]}
    assert S.one("X", thin, px)["ig"] is None and S.one("X", thin, px)["fcf_thin"]
    assert S.faces(_p(), bank=True)["s_grade"] == "銀行不適用"


def test_card_wording():
    from tools import site_stockcheck as C
    idx = pd.date_range("2021-06-04", "2026-10-23", freq="W-FRI")
    px = {d.strftime("%Y-%m-%d"): 80.0 for d in idx}
    d = {"facts": {"AAPL": _p()}, "px": {"AAPL": px}}
    C._b = lambda: S.build(d)
    h = C.sec_stock_check(None)
    assert "一句話看懂" in h and "三面體檢" in h and "歷史本益比情境" in h and "不是投資建議" in h
    for bad in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出"):
        assert bad not in h, bad


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
