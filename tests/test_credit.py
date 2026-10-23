"""信用: company credit grades (net cash, coverage/leverage bands, banks on capital, utilities, missing data, +2pp shock),
credit-vs-rates analysis on synthetic weekly data, and both site cards.
Run: python -m tests.test_credit"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import date

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_cr_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import credit_health as CH, credit_rates as CR  # noqa: E402


def bs(**k):
    base = {"end": "2026-06-30", "assets": 100e9, "liab": 60e9, "equity": 40e9, "cur_assets": 30e9, "cur_liab": 20e9, "re": 20e9,
            "cash": 5e9, "ltd": 30e9, "ltd_cur": 2e9, "debt_cur": 0.0, "ebit_ttm": 10e9, "interest_ttm": 1e9, "da_ttm": 3e9,
            "ocf_ttm": 9e9, "capex_ttm": 4e9}
    base.update(k)
    return base


def test_grades():
    d = date(2026, 10, 23)
    e = pd.Series(dtype=float)
    assert CH.one("A", bs(cash=60e9), e, "XLK", d)["grade"] == "強"                      # net cash
    r = CH.one("B", bs(), e, "XLI", d)                                                 # cover 10×, net debt 25 / EBITDA 13 ≈ 1.9
    assert r["grade"] == "強" and abs(r["cov"] - 10) < 1e-9 and r["due_cover"] == 2.5, r
    assert CH.one("B2", bs(ebit_ttm=5e9, da_ttm=3e9), e, "XLI", d)["grade"] == "穩健"     # cover 5×, lev 25/8 ≈ 3.1
    r = CH.one("C", bs(ebit_ttm=2.5e9, da_ttm=1e9), e, "XLI", d)                         # cover 2.5×, lev 25/3.5 = 7.1
    assert r["grade"] == "偏弱", r
    assert abs(r["cov_shock"] - 2.5e9 / (1e9 + 30e9 * 0.02)) < 1e-6                      # +2pp on all debt
    assert CH.one("D", bs(ebit_ttm=-1e9, da_ttm=0.5e9), e, "XLI", d)["grade"] == "危險"
    assert CH.one("E", bs(interest_ttm=None), e, "XLY", d)["grade"] in ("強", "穩健")      # missing interest never counts against
    bank = CH.one("F", bs(equity=9e9, assets=100e9), e, "XLF", d)
    assert bank["grade"] == "穩健" and "權益／資產" in bank["why"]
    print("ok grades")


def test_build_and_card():
    members = {"sectors": {"XLU": {"members": [["UT", 10.0, "Util Co"]]}, "XLK": {"members": [["TC", 20.0, "Tech Co"]]}}}
    cache = {"UT": {"bs": bs(ebit_ttm=2.2e9, interest_ttm=1e9, da_ttm=1e9)}, "TC": {"bs": bs(cash=80e9)}}
    r = CH.build(members, cache, pd.DataFrame(), date(2026, 10, 23))
    assert r["n"] == 2 and r["rows"][0]["sym"] == "UT" and r["rows"][0]["heavy"] and r["shock_fall"] == ["UT"], r["rows"]
    from tools import site_credit as SCR
    h = SCR.sec_credit_health(types.SimpleNamespace(sector_brief={"credit": r}))
    assert "信用體檢" in h and 'data-sec="XLU"' in h and "靠借錢" in h and "不是信評機構的評等" in h
    print("ok build / card")


class Fred:
    def __init__(self, d):
        self.d = d

    def get(self, k):
        return self.d.get(k, pd.Series(dtype=float))


class Mkt:
    def __init__(self, d):
        self.d = d

    def series(self, k):
        return self.d.get(k, pd.Series(dtype=float))


def test_rates():
    rng = np.random.default_rng(1)
    idx = pd.bdate_range("1990-01-01", "2026-10-22")
    ret = rng.normal(0.0003, 0.01, len(idx))
    spx = pd.Series(100 * np.exp(np.cumsum(ret)), index=idx)
    baa = pd.Series(2 - np.cumsum(ret) * 0.5 + rng.normal(0, 0.02, len(idx)), index=idx)   # spread falls when stocks rise
    y10 = pd.Series(5 + np.cumsum(rng.normal(0, 0.02, len(idx))), index=idx)
    e = types.SimpleNamespace(fred=Fred({"BAA10Y": baa, "DGS10": y10}), market=Mkt({"^GSPC": spx}))
    r = CR.build(e)
    assert r["available"] and r["co"]["baa"]["same"] < -0.3 and r["co"]["baa"]["lead_abs"] < 0.2, r["co"]
    assert -1 <= r["stock_yield"]["now"] <= 1 and r["div"]["base"] > 0
    from tools import site_credit as SCR
    h = SCR.sec_credit_rates(e)
    assert "信用與利率" in h and "同時" in h and "AUC" in h
    print("ok credit vs rates")


if __name__ == "__main__":
    test_grades()
    test_build_and_card()
    test_rates()
    print("all credit tests passed")
