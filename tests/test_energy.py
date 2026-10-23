"""能源傳導鏈: crack spreads, distillate stocks vs 5 years, diesel → breakeven pass-through, the chain, readings,
the EIA parser and the site card.  Run: python -m tests.test_energy"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ec_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import energy_chain as EC  # noqa: E402
from wsb.data import eia as EIA  # noqa: E402
from tools import site_energy as SE  # noqa: E402

IDX = pd.bdate_range("2019-01-01", "2026-10-20")


def lin(a, b, idx=IDX):
    return pd.Series(np.linspace(a, b, len(idx)), index=idx)


def test_cracks():
    ho, bz = lin(2.0, 3.5), lin(70.0, 95.0)                      # diesel 84 → 147 $/bbl vs Brent 70 → 95
    rb, cl = lin(2.0, 2.4), lin(66.0, 90.0)
    cr = {x["key"]: x for x in EC.cracks({"HO=F": ho, "RB=F": rb, "BZ=F": bz, "CL=F": cl})}
    assert abs(cr["diesel"]["now"] - (3.5 * 42 - 95)) < 1e-9
    assert cr["diesel"]["pct"] > 99 and cr["diesel"]["d3m"] > 0       # rising all the way → top of its own history
    assert abs(cr["321"]["now"] - (2 * 2.4 * 42 + 3.5 * 42 - 3 * 90) / 3) < 1e-9
    assert EC.cracks({"HO=F": ho}) == []                              # no Brent → nothing invented
    print("ok cracks")


def test_distillate_and_eia_parse():
    w = pd.date_range("2019-01-04", "2026-10-16", freq="W-FRI")
    s = pd.Series(120_000.0, index=w)
    s.iloc[-1] = 108_000.0                                            # 10% below every earlier year
    st = EC.distillate_vs_5y(s)
    assert st["n_years"] == 5 and abs(st["vs5_pct"] + 10.0) < 1e-9, st
    assert EC.distillate_vs_5y(s.iloc[-100:]) is None                # under 5 years of data → not shown
    js = {"response": {"data": [{"period": d.strftime("%Y-%m-%d"), "value": str(v)} for d, v in s.items()] + [{"period": "x", "value": None}]}}
    p = EIA.parse(js)
    assert len(p) == len(s) and p.index.is_monotonic_increasing and p.iloc[-1] == 108_000.0
    try:
        EIA.parse({"response": {"data": []}})
        raise AssertionError("empty EIA payload must raise")
    except ValueError:
        pass
    print("ok distillate + EIA parser")


def test_pass_through_and_chain():
    rng = np.random.default_rng(3)
    r = rng.normal(0, 1.5, len(IDX))                                  # diesel daily % moves
    ho = pd.Series(2.5 * np.exp(np.cumsum(r) / 100), index=IDX)
    be = pd.Series(2.3 + np.cumsum(r) / 100 * 2.0, index=IDX)         # +10% (log) diesel → +0.2pp = +20bp
    p = EC.pass_through(ho, be, 504, 20)
    assert p and abs(p["bp_per_10pct"] - 20) < 1.0 and p["corr"] > 0.99, p
    get = {"GASDESW": lin(3.6, 4.4), "T5YIE": lin(2.2, 2.7), "DGS2": lin(3.5, 4.1)}.get
    m = types.SimpleNamespace(series=lambda t: {"BZ=F": lin(70, 98), "HO=F": lin(2.2, 3.6), "RB=F": lin(2.0, 2.5), "CL=F": lin(66, 93)}.get(t, pd.Series(dtype=float)))
    out = EC.build(types.SimpleNamespace(market=m, fred=types.SimpleNamespace(get=lambda k: get(k, pd.Series(dtype=float)))))
    assert out["available"] and out["aligned"], out
    ch = {x["key"]: x for x in out["chain"]}
    assert ch["be5"]["unit"] == "bp" and 0 < ch["be5"]["d3m"] < 50 and ch["brent"]["unit"] == "%"
    empty = EC.build(types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: pd.Series(dtype=float)), fred=None))
    assert empty == {"available": False}
    print("ok pass-through + chain")


def test_readings_and_card():
    r = {"available": True, "aligned": True,
         "cracks": [{"key": "diesel", "zh": "柴油", "en": "diesel", "now": 52.0, "pct": 97.0, "d3m": 14.0, "since": "2000", "asof": "2026-10-20"}],
         "chain": [{"key": "be5", "zh": "5 年", "en": "5y", "now": 2.71, "d3m": 31.0, "unit": "bp", "asof": "2026-10-20"},
                   {"key": "y2", "zh": "2 年", "en": "2y", "now": 4.12, "d3m": 44.0, "unit": "bp", "asof": "2026-10-20"},
                   {"key": "brent", "zh": "布蘭特", "en": "Brent", "now": 96.0, "d3m": 22.0, "unit": "%", "asof": "2026-10-20"}],
         "stocks": {"now": 108.0, "avg5": 120.0, "vs5_pct": -10.0, "n_years": 5, "asof": "2026-10-16", "d4w": -3.0},
         "pass": {"bp_per_10pct": 6.2, "corr": 0.45, "n": 25, "step": 20}}
    rd = SE.readings(r, EC.cfg())
    assert [x["lv"] for x in rd][:2] == ["alert", "alert"] and any("精煉品" in x["zh"] for x in rd)
    assert any("+31bp" in x["zh"] and "+44bp" in x["zh"] for x in rd)
    assert any("低 10.0%" in x["zh"] for x in rd) and any("+6.2bp" in x["zh"] for x in rd)
    cool = {**r, "aligned": False, "cracks": [{**r["cracks"][0], "pct": 40.0}], "stocks": {**r["stocks"], "vs5_pct": 2.0},
            "pass": {**r["pass"], "corr": 0.1}}
    assert SE.readings(cool, EC.cfg()) == []                         # nothing tight → no readings
    html = SE.sec_energy_chain(types.SimpleNamespace(energy_chain=r))
    assert "能源傳導鏈" in html and "52.0" in html and "+31 bp" in html, html[:300]
    assert SE.sec_energy_chain(types.SimpleNamespace(energy_chain={})) == ""
    print("ok readings + card")


if __name__ == "__main__":
    test_cracks()
    test_distillate_and_eia_parse()
    test_pass_through_and_chain()
    test_readings_and_card()
    print("ALL OK")
