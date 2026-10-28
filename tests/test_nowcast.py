"""公布前估算 (GDP / PCE / payrolls) and the FOMC follow-up: estimates come from earlier data with an honest walk-forward
error, the log freezes the estimate once the actual appears, event cards get one plain line, and no trading words.
Run: python -m tests.test_nowcast"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_nc_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import nowcast as NC  # noqa: E402

M = pd.date_range("2010-01-01", "2026-09-01", freq="MS")


def _lv(mm):
    return {d.strftime("%Y-%m-%d"): float(v) for d, v in zip(M[:len(mm)], 100 * np.cumprod(1 + np.asarray(mm) / 100))}


def _data():
    rng = np.random.default_rng(3)
    cpi = 0.25 + rng.normal(0, 0.1, len(M))
    ppi = 0.2 + rng.normal(0, 0.3, len(M))
    pce = 0.02 + 0.6 * cpi + 0.15 * ppi + rng.normal(0, 0.03, len(M))
    adp = rng.normal(150, 60, len(M))
    cl = rng.normal(0, 8, len(M))
    pay = 20 + 0.8 * adp - 3 * cl + rng.normal(0, 40, len(M))
    wk = pd.date_range("2010-01-02", "2026-10-24", freq="W-SAT")
    mcl = pd.Series(np.cumsum(cl), index=M).reindex(wk, method="ffill").fillna(0)
    d = {"CPILFESL": _lv(cpi), "PPIFES": _lv(ppi), "PCEPILFE": _lv(pce[:-1]),           # September PCE still pending
         "CPIAUCSL": _lv(cpi), "PPIFIS": _lv(ppi), "PCEPI": _lv(pce[:-1]),
         "ADPMNUSNERSA": {d.strftime("%Y-%m-%d"): float(v) * 1000 for d, v in zip(M, 120000 + np.cumsum(adp))},
         "PAYEMS": {d.strftime("%Y-%m-%d"): float(v) for d, v in zip(M, 130000 + np.cumsum(pay))},
         "ICSA": {d.strftime("%Y-%m-%d"): float(220 + v) * 1000 for d, v in mcl.items()},
         "GDPNOW": {"2025-07-01": 2.0, "2025-10-01": 1.5, "2026-01-01": 2.2, "2026-04-01": 1.5, "2026-07-01": 3.27},
         "A191RL1Q225SBEA": {"2025-07-01": 2.4, "2025-10-01": 1.2, "2026-01-01": 2.5, "2026-04-01": 1.9}}
    return d


def test_pce_and_gdp_estimates():
    d = _data()
    e = NC.estimates(d)
    p = e["pce:2026-09"]["core"]
    assert p["month"] == "2026-09" and 0 < p["rmse"] < 0.1 and p["yy"] is not None
    assert "gdp:2026Q3" in e and e["gdp:2026Q3"]["est"] == 3.27


def test_nfp_claims_only_when_no_adp():
    d = _data()
    n = NC.nfp(d)
    assert n is None or n["month"] == "2026-10"                # Oct claims exist; ADP for Oct does not
    if n:
        assert n["src"] == "claims" and n["adp"] is None and n["rmse"] > 0


def test_log_freezes_after_actual_and_cards():
    d = _data()
    lg = NC.update_log(d)
    assert lg["pce:2026-09"].get("actual") is None
    d["PCEPILFE"] = _lv(list(np.full(len(M), 0.3)))            # September PCE now published
    d["log"] = lg
    lg2 = NC.update_log(d)
    assert lg2["pce:2026-09"]["actual"]["core"] is not None and lg2["pce:2026-09"]["est"] == lg["pce:2026-09"]["est"]
    up = {"key": "pce", "date": "2026-10-30", "released": False,
          "rows": [{"label": "核心 PCE 月增", "cons": "0.2%", "actual": ""}]}
    NC.attach([up], lg)
    assert "公布前估算" in up["nowcast"]["zh"] and "誤差" in up["nowcast"]["zh"]
    done = dict(up, released=True, rows=[{"label": "核心 PCE 月增", "cons": "0.2%", "actual": "0.3%"}])
    done.pop("nowcast")
    NC.attach([done], lg)
    assert "事前估算" in done["nowcast"]["zh"] and "倍誤差" in done["nowcast"]["zh"]
    g = {"key": "gdp", "date": "2026-10-29", "released": False, "rows": [{"label": "GDP", "cons": "2.8%", "actual": ""}]}
    NC.attach([g], lg)
    assert "GDPNow" in g["nowcast"]["zh"] and "2026Q3" in g["nowcast"]["zh"]
    for x in (up, done, g):
        for w in ("買進", "賣出", "目標價", "低估", "高估", "買點"):
            assert w not in x["nowcast"]["zh"]


def test_target_mapping():
    assert NC.target_for("nfp", "2026-11-06") == "nfp:2026-10"
    assert NC.target_for("pce", "2026-10-30") == "pce:2026-09"
    assert NC.target_for("gdp", "2026-10-29") == "gdp:2026Q3"


def test_fomc_after():
    from wsb.analytics import fomc_drift as FD
    idx = pd.bdate_range(end="2026-10-30", periods=400)
    rng = np.random.default_rng(1)
    ser = {"^GSPC": pd.Series(np.cumprod(1 + rng.normal(0, 0.01, len(idx))) * 5000, index=idx),
           "^VIX": pd.Series(17.0, index=idx), "^TNX": pd.Series(4.99, index=idx), "DX-Y.NYB": pd.Series(102.0, index=idx)}
    ser["^TNX"].iloc[-3:] = 5.045

    class Mk:
        def series(self, t):
            return ser.get(t, pd.Series(dtype=float))

        def q(self, t):
            return None
    st = {"all": {"post": {"mean": 0.02, "up": 56}}, "lo": {"zh": "VIX < 20 時", "post": {"mean": 0.14, "up": 57}}}
    a = FD.after(Mk(), ser["^GSPC"], ser["^VIX"], ["2026-09-16", "2026-10-28"], st)
    assert a["date"] == "2026-10-28" and a["n"] == 2 and abs(a["tnx"]["chg"] - 5.5) < 0.01 and a["hist"]["grp_zh"] == "VIX < 20 時"
    lines = FD.readings({"available": True, "stats": {g: {"pre": None, "day": None, "post": None} for g in ("all", "new", "old", "hi", "lo")}, "first": "1995", "after": a})
    assert any("會後追蹤" in x["zh"] for x in lines)
    assert FD.after(Mk(), ser["^GSPC"], ser["^VIX"], ["2026-09-16"], st) is None     # too long ago


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
