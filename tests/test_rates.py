"""利率衝擊雷達: yield decomposition, stocks-vs-bonds gap (1987 check), tech beta to yields, watch lines, fiscal strain,
long-end auctions, readings and the site card.  Run: python -m tests.test_rates"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rr_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import rates_radar as RR  # noqa: E402


def daily(vals_from, vals_to, start="2024-01-01", end="2026-10-20"):
    idx = pd.bdate_range(start, end)
    return pd.Series(np.linspace(vals_from, vals_to, len(idx)), index=idx)


def quarterly(vals, start="1962-01-01"):
    return pd.Series(vals, index=pd.date_range(start, periods=len(vals), freq="QS"))


def test_decompose():
    s = {"DGS10": daily(4.0, 5.0), "DFII10": daily(1.8, 2.6), "T10YIE": daily(2.2, 2.4), "THREEFYTP10": daily(0.2, 0.6)}
    d = RR.decompose(s.get)
    assert abs(d["nominal"] - 5.0) < 1e-9 and d["d_nominal"] > 0
    assert d["driver"] == "real", d                          # real moved 0.8 vs breakeven 0.2 over the span
    assert RR.decompose({}.get) is None
    print("ok decompose")


def test_yield_gap_and_1987():
    n = (2026 - 1962) * 4 + 3
    ey = quarterly(np.full(n, 5.0))
    prof, mv = ey * 10.0, pd.Series(np.full(n, 1_000_000.0), index=ey.index)    # 50 bn ×1000 / 1e6 mn ×100 = 5%
    nom = pd.Series(7.0, index=pd.bdate_range("1962-01-01", "2026-10-20"))
    nom[nom.index >= "2000-01-01"] = 4.0
    nom[(nom.index >= "1987-07-01") & (nom.index < "1987-10-01")] = 9.0
    nom[nom.index >= "2026-01-01"] = 6.0
    real = pd.Series(2.0, index=pd.bdate_range("2003-01-01", "2026-10-20"))
    g = RR.yield_gap({"NFCPATAX": prof, "NCBEILQ027S": mv, "DGS10": nom, "DFII10": real}.get, None)
    assert abs(g["ey"] - 5.0) < 1e-9 and abs(g["gap"] + 1.0) < 1e-9
    assert abs(g["y1987"] + 4.0) < 1e-9, g                    # 5 − 9 in Q3 1987
    assert g["neg_share"] > 50 and abs(g["erp"] - 3.0) < 1e-9
    # rolled forward with the index: market up 25% since the last quarter end → earnings yield 4%
    spx = pd.Series([100.0, 125.0], index=pd.to_datetime([str(ey.index[-1].date()), "2026-10-20"]))
    g2 = RR.yield_gap({"NFCPATAX": prof, "NCBEILQ027S": mv, "DGS10": nom, "DFII10": real}.get, spx)
    assert g2["rolled"] and abs(g2["ey"] - 4.0) < 1e-6
    print("ok yield gap")


def test_beta_and_watch():
    rng = np.random.default_rng(1)
    idx = pd.bdate_range("2024-01-01", periods=600)
    dy = rng.normal(0, 5, len(idx))                          # bp
    tnx = pd.Series(42.0 + np.cumsum(dy) / 100 * 10, index=idx)  # ×10 quote, like Yahoo sometimes does
    r = -0.15 * dy + rng.normal(0, 0.3, len(idx))            # −1.5% per +10bp
    px = {"QQQ": pd.Series(100 * np.cumprod(1 + r / 100), index=idx)}
    b = RR.tech_beta(px, tnx, 126)
    assert len(b) == 1 and abs(b[0]["beta"] + 1.5) < 0.3 and b[0]["corr"] < -0.8, b
    ser = {"^TNX": pd.Series([51.2], index=idx[-1:]), "IXG": pd.Series([124.0], index=idx[-1:])}
    w = RR.watch_lines(ser.get, RR.cfg()["watch"])
    by = {x["t"]: x for x in w}
    assert abs(by["^TNX"]["now"] - 5.12) < 1e-9 and not by["^TNX"]["hit"] and abs(by["^TNX"]["dist"] - 0.13) < 1e-9
    assert by["IXG"]["hit"] and "^MOVE" not in by            # missing series are skipped, not invented
    print("ok beta + watch lines")


def test_fiscal_auctions_card():
    q = pd.date_range("1960-01-01", periods=267, freq="QS")
    ip = pd.Series(np.linspace(10, 1100, len(q)), index=q)
    rc = pd.Series(np.linspace(100, 3300, len(q)), index=q)
    f = RR.fiscal({"A091RC1Q027SBEA": ip, "W006RC1Q027SBEA": rc, "GFDEBTN": pd.Series([39_460_000.0], index=q[-1:])}.get)
    assert abs(f["ratio"] - 1100 / 3300 * 100) < 1e-9 and abs(f["debt_tn"] - 39.46) < 1e-9 and f["pct"] > 90
    tr = types.SimpleNamespace(auctions=[{"date": "2026-09-10", "term": "10-Year"}, {"date": "2026-10-09", "term": "30-Year"},
                                         {"date": "2026-10-08", "term": "3-Year"}])
    au = RR.long_auctions(types.SimpleNamespace(treasury=tr))
    assert [a["term"] for a in au] == ["30-Year", "10-Year"], au      # newest first, short tenors dropped
    r = {"available": True,
         "decomp": {"nominal": 5.12, "d_nominal": 0.52, "real": 2.4, "d_real": 0.42, "breakeven": 2.4, "d_breakeven": 0.11,
                    "term_premium": 0.9, "d_term_premium": 0.21, "driver": "real", "date": "2026-10-20"},
         "gap": {"ey": 3.28, "nominal": 5.12, "gap": -1.84, "erp": 0.51, "erp_pct": 0.0, "erp_since": "2003", "y1987": -4.18,
                 "y2000": -4.58, "neg_share": 60.0, "ey_q": "2026-04"},
         "beta": [{"t": "^SOX", "zh": "費城半導體", "en": "SOX", "beta": -1.52, "beta_pct": 1.3, "corr": -0.5}],
         "watch": [{"t": "IXG", "zh": "IXG", "en": "IXG", "line": 125, "side": "below", "now": 129.2, "hit": False, "dist": 4.2, "dist_pct": 3.4}],
         "fiscal": f, "auctions": [], "ai": []}
    rd = RR_site.readings(r)
    assert rd[0]["lv"] == "alert" and any("1987" in x["zh"] and "不是崩盤的時間點" in x["zh"] for x in rd)
    assert any("距離 3.4%" in x["zh"] for x in rd)
    html = RR_site.sec_rates_radar(types.SimpleNamespace(rates_radar=r))
    assert "利率衝擊雷達" in html and ("−1.84" in html or "-1.84" in html), html[:300]
    assert RR_site.sec_rates_radar(types.SimpleNamespace(rates_radar={})) == ""
    print("ok fiscal + auctions + card")


from tools import site_rates as RR_site  # noqa: E402


def test_jgb_parse():
    from wsb.data import global_yields as GY
    txt = ("Interest Rate\n"
           "Date,1Y,2Y,3Y,4Y,5Y,6Y,7Y,8Y,9Y,10Y,15Y,20Y,25Y,30Y,40Y\n"
           "1974/9/24,10.327,9.362,8.83,8.515,8.348,8.29,8.24,8.121,8.127,-,-,-,-,-,-\n"
           "2026/9/30,1.05,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.95,3.2,3.3,3.4,3.5,3.7\n"
           "2026/10/1,1.06,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,3.01,3.2,3.3,3.4,3.55,3.7\n")
    df = GY.parse(txt)
    assert list(df.columns) == ["1Y", "2Y", "5Y", "10Y", "20Y", "30Y"] and len(df) == 3
    assert pd.isna(df["10Y"].iloc[0]) and df["10Y"].iloc[-1] == 3.01 and df.index[-1] == pd.Timestamp("2026-10-01")
    try:
        GY.parse("Interest Rate\nfoo,bar\n1,2\n")
        raise AssertionError("a CSV without 10Y must raise")
    except (ValueError, StopIteration):
        pass
    print("ok MOF JGB parser")


def test_global_long():
    idx = pd.bdate_range("2016-01-01", "2026-10-20")
    flat = lambda v: pd.Series(v, index=idx)  # noqa: E731
    def surge(a):                                             # flat, then +60bp over the last 20 trading days
        s = pd.Series(a, index=idx, dtype=float)
        s.iloc[-20:] = a + np.linspace(0.03, 0.6, 20)
        return s
    fred = {"DGS10": surge(4.6), "DGS1": flat(4.0), "DGS30": surge(5.0)}
    m = pd.date_range("2000-01-01", "2026-09-01", freq="MS")
    fred["IRLTLT01GBM156N"] = pd.Series(np.linspace(4, 4.9, len(m)), index=m)
    jgb = {"10Y": surge(2.4), "30Y": surge(2.9), "1Y": flat(0.9)}
    g = RR.global_long(fred.get, lambda t: jgb.get(t, pd.Series(dtype=float)), 85.0, 20)
    by = {r["key"]: r for r in g["rows"]}
    assert set(by) == {"us10", "us30", "jp10", "jp30", "uk10"}, by.keys()    # Germany missing → left out, not invented
    assert abs(by["jp10"]["chg_bp"] - 60) < 1e-6 and by["jp10"]["chg_pct"] > 99 and by["uk10"]["freq"] == "m"
    assert g["together"]
    hd = g["hedged"]
    assert abs(hd["hedge_cost"] - 3.1) < 1e-9 and abs(hd["hedged"] - (5.2 - 3.1)) < 1e-6 and hd["pickup"] < 0, hd
    calm = RR.global_long({**fred, "DGS10": flat(4.6)}.get, lambda t: jgb.get(t, pd.Series(dtype=float)), 85.0, 20)
    assert not calm["together"]
    assert RR.global_long({}.get, lambda t: pd.Series(dtype=float), 85.0, 20) is None
    r = {"available": True, "global": g}
    rd = RR_site.readings(r)
    assert rd[0]["lv"] == "alert" and "同步上衝" in rd[0]["zh"] and any("避險後" in x["zh"] for x in rd)
    html = RR_site.sec_rates_radar(types.SimpleNamespace(rates_radar=r))
    assert "8. 全球長債" in html and "日本 10 年" in html and "+60 bp" in html, html[:400]
    print("ok global long bonds")

if __name__ == "__main__":
    test_decompose()
    test_yield_gap_and_1987()
    test_beta_and_watch()
    test_fiscal_auctions_card()
    test_jgb_parse()
    test_global_long()
    print("ALL OK")
