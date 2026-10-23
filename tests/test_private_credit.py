"""私募信貸燈號: tender-offer counts, BDC price vs NAV (no look-ahead), insurers vs S&P, parsers and the canary wiring.
Run: python -m tests.test_private_credit"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import date

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_pc_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import private_credit as PCL  # noqa: E402
from wsb.data import private_credit as PC  # noqa: E402

IDX = pd.bdate_range("2021-01-01", "2026-10-20")


def test_parsers():
    assert PC.months_back(date(2026, 2, 10), 4) == ["2025-11", "2025-12", "2026-01", "2026-02"]
    cf = {"facts": {"us-gaap": {"NetAssetValuePerShare": {"units": {"USD/shares": [
        {"end": "2026-03-31", "val": 19.5, "form": "10-Q", "filed": "2026-05-01"},
        {"end": "2026-03-31", "val": 19.4, "form": "10-Q/A", "filed": "2026-06-01"},      # later amendment wins
        {"end": "2025-12-31", "val": 19.9, "form": "10-K", "filed": "2026-02-20"},
        {"end": "2025-12-31", "val": 1.0, "form": "8-K", "filed": "2026-02-01"},          # not a 10-Q/10-K → ignored
        {"end": "2026-06-30", "val": None, "form": "10-Q"}]}}}}}
    assert PC.nav_history(cf) == [["2025-12-31", 19.9], ["2026-03-31", 19.4]]
    assert PC.nav_history({}) == []
    print("ok parsers")


def test_tender_light():
    c = PC.cfg()
    months = PC.months_back(date(2026, 10, 20), 40)
    t = {m: {"all": 120, "bdc": 30, "partial": False} for m in months[:-1]}
    t[months[-1]] = {"all": 50, "bdc": 15, "partial": True}                # current month is never judged
    calm = PCL.tender_light({"tenders": t}, c)
    assert calm["state"] == "ok", calm
    for m in months[-4:-1]:
        t[m] = {"all": 160, "bdc": 70, "partial": False}
    hot = PCL.tender_light({"tenders": t}, c)
    assert hot["state"] == "alert" and "210 件" in hot["value_txt"], hot
    assert PCL.tender_light({}, c)["state"] == "na"
    assert PCL.tender_light({"tenders": dict(list(t.items())[:5])}, c)["state"] == "warmup"
    print("ok tender light")


def test_discount_no_lookahead():
    px = pd.Series(20.0, index=IDX)
    nav = [["2026-06-30", 25.0]]
    d = PCL._discount_series(nav, px)
    assert d.index[0] >= pd.Timestamp("2026-06-30") + pd.Timedelta(days=PCL.NAV_LAG_DAYS)   # not known before it was filed
    assert abs(d.iloc[-1] + 20.0) < 1e-9


def test_discount_and_insurer_lights():
    c = PC.cfg()
    q = pd.date_range("2020-03-31", "2026-06-30", freq="QE")
    navs = {s: {"nav": [[d.strftime("%Y-%m-%d"), 20.0] for d in q]} for s in c["bdcs"][:4]}
    px = {s: pd.Series(np.r_[np.full(len(IDX) - 40, 20.0), np.full(40, 15.0)], index=IDX) for s in c["bdcs"][:4]}
    so = lambda t: px.get(t, pd.Series(dtype=float))  # noqa: E731
    r = PCL.discount_light({"nav": navs}, so, c)
    assert r["state"] == "alert" and "-25.0%" in r["value_txt"], r
    flat = {s: pd.Series(19.0, index=IDX) for s in c["bdcs"][:4]}
    r2 = PCL.discount_light({"nav": navs}, lambda t: flat.get(t, pd.Series(dtype=float)), c)
    assert r2["state"] == "ok", r2                                     # steady −5% is its normal
    assert PCL.discount_light({"nav": {}}, so, c)["state"] == "na"
    rng = np.random.default_rng(5)
    spx = pd.Series(100 * np.cumprod(1 + rng.normal(0.0004, 0.01, len(IDX))), index=IDX)
    ins = {s: spx * (1 + rng.normal(0, 0.002, len(IDX))) for s in c["insurers"][:3]}
    for s in ins:
        ins[s].iloc[-60:] = ins[s].iloc[-61] * np.linspace(1, 0.7, 60)    # −30% while the index drifts
    so2 = lambda t: spx if t == "^GSPC" else ins.get(t, pd.Series(dtype=float))  # noqa: E731
    r3 = PCL.insurer_light(so2, c)
    assert r3["state"] == "alert", r3
    print("ok discount + insurer lights")


def test_canary_wiring():
    from wsb.analytics import canary as CN
    src = open(CN.__file__, encoding="utf-8").read()
    assert "_pc_lights(eng)" in src
    eng = types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: pd.Series(dtype=float)), private_credit={})
    rows = PCL.lights(eng, {})
    assert [r["id"] for r in rows] == ["pc_tenders", "pc_bdc_discount", "pc_insurers", "pc_pik", "pc_unrealized"] and all(r["state"] == "na" for r in rows)
    print("ok canary wiring")


if __name__ == "__main__":
    test_parsers()
    test_tender_light()
    test_discount_no_lookahead()
    test_discount_and_insurer_lights()
    test_canary_wiring()
    print("ALL OK")


def test_quality():
    from wsb.data import private_credit as PCD
    from wsb.analytics import private_credit as PCL

    def fl(tag, rows):
        return {tag: {"units": {"USD": [{"start": a, "end": b, "val": v, "form": "10-Q", "filed": b} for a, b, v in rows]}}}
    cf = {"facts": {"us-gaap": {**fl("InterestIncomeOperatingPaidInKind", [("2025-01-01", "2025-03-31", 6.0), ("2026-01-01", "2026-03-31", 9.0)]),
                                **fl("GrossInvestmentIncomeOperating", [("2025-01-01", "2025-03-31", 100.0), ("2026-01-01", "2026-03-31", 100.0)]),
                                "TaxBasisOfInvestmentsUnrealizedAppreciationDepreciationNet": {"units": {"USD": [{"end": "2026-03-31", "val": -70.0, "form": "10-Q", "filed": "x"}]}},
                                "StockholdersEquity": {"units": {"USD": [{"end": "2026-03-31", "val": 1000.0, "form": "10-Q", "filed": "x"}]}}}}}
    q = PCD.credit_quality(cf)
    assert q["pik"] == [["2025-03-31", 89, 6.0], ["2026-03-31", 89, 9.0]] and q["unreal"] == [["2026-03-31", -7.0]], q
    data = {"nav": {s: {"quality": q} for s in ("A", "B", "C")}}
    data["nav"]["OLD"] = {"quality": {"pik": [["2023-06-30", 90, 40.0]], "unreal": [["2023-06-30", -50.0]]}}
    c = {"bdcs": ["A", "B", "C", "OLD"]}
    p, u = PCL.pik_light(data, c), PCL.unrealized_light(data, c)
    assert p["state"] == "watch" and "+3.0" in p["value_txt"] and "OLD" not in p["value_txt"], p      # +3pp y/y, stale filer dropped
    assert u["state"] == "alert" and "OLD" not in u["value_txt"], u                                  # median −7 % of NAV
    print("ok bdc quality")


test_quality()
