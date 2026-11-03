"""台灣 ETF part 2: compact price cache, duplicate dividends, total return by kind, payout from capital, bond rate
sensitivity, leveraged decay, active vs benchmark, page cards.
Run: python -m tests.test_tw_etf_perf"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_etfp_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "加碼參考區", "進場參考區")


def _c(s: pd.Series):
    return [[d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in s.items()]


def _fixture():
    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2022-11-01", "2026-10-30")
    n = len(idx)
    r = rng.normal(0, 0.015, n)                                      # choppy, no trend → leverage decays
    base = pd.Series(50 * np.cumprod(1 + r), index=idx)
    lev = pd.Series(20 * np.cumprod(1 + 2 * r), index=idx)
    dy = rng.normal(0, 0.04, n)                                     # 10-year yield, daily change in points
    tnx = pd.Series(4 + np.cumsum(dy), index=idx)
    fx = pd.Series(31 * np.cumprod(1 + rng.normal(0, 0.003, n)), index=idx)
    # bond ETF trades in Taipei the next day: −1.2 % per +0.1 point of the previous US close, +0.7 × USD/TWD
    br = -12 * tnx.diff().shift(1).fillna(0) / 100 + 0.7 * fx.pct_change().shift(1).fillna(0) + rng.normal(0, 0.001, n)
    bond = pd.Series(30 * np.cumprod(1 + br.values), index=idx)
    hd = pd.Series(np.linspace(20, 16, n), index=idx)               # price drifting down while paying 1.0 a quarter
    act = base[idx >= "2025-06-02"] / base[idx >= "2025-06-02"].iloc[0] * 10 * np.linspace(1, 1.2, (idx >= "2025-06-02").sum())
    hdv = [[d.strftime("%Y-%m-%d"), 0.6] for d in idx[::63][1:]]
    px = {"0050": {"c": _c(base), "dv": []}, "00631L": {"c": _c(lev), "dv": []}, "00679B": {"c": _c(bond), "dv": []},
          "00999": {"c": _c(hd), "dv": hdv}, "00981A": {"c": _c(act), "dv": []},
          "^TNX": {"c": _c(tnx), "dv": []}, "TWD=X": {"c": _c(fx), "dv": []}}
    nav = {k: {"name": nm, "units": 1e8, "nav": 10.0} for k, nm in
           (("0050", "元大台灣50"), ("00631L", "元大台灣50正2"), ("00679B", "元大美債20年"), ("00999", "某某高股息"), ("00981A", "主動統一台股增長"))}
    return {"nav": nav, "px": px}


def test_cache_and_dividends():
    from wsb.data import tw_etf as D
    p = {"c": [["2026-01-02", 10.0], ["2026-01-05", 10.5]], "dv": [["2026-01-19", 3.5], ["2026-01-20", 3.5], ["2026-04-20", 3.5]]}
    q = D.unpack(D.pack(p))
    assert q["c"] == p["c"] and D.unpack(D.pack({"c": []}))["c"] == []
    assert D.dedupe_dv(p["dv"]) == [["2026-01-19", 3.5], ["2026-04-20", 3.5]]   # Yahoo's doubled 00917 dividend dropped
    assert "^TNX" in D.REFS and "TWD=X" in D.REFS


def test_analytics():
    from wsb.analytics import tw_etf_perf as P
    assert P.lev_factor("00631L", "元大台灣50正2") == 2 and P.lev_factor("00632R", "元大台灣50反1") == -1
    assert P.lev_factor("00715L", "某原油單日正向2倍") == 2
    r = P.build(_fixture())
    assert r["available"] and r["base"]["code"] == "0050" and r["base"]["vs1y"] == 0
    by = {x["code"]: x for x in r["rows"]}
    assert by["00999"]["tr1y"] > (by["00999"]["vs1y"] + r["base"]["tr1y"]) - 1e-6
    k = r["kinds"]
    assert k["高股息"]["n1"] == 1 and "市值型" not in k                      # 0050 itself is the yardstick, not counted
    pay = {x["code"]: x for x in r["payout"]}
    assert pay["00999"]["cls"] == "capital" and 0 < pay["00999"]["capital_share"] <= 100 and pay["00999"]["yrs"] == 3
    rt = {x["code"]: x for x in r["rate"]}["00679B"]
    assert rt["clear"] and abs(rt["beta10"] + 1.2) < 0.15 and abs(rt["dur"] - 12) < 1.5 and abs(rt["fxb"] - 0.7) < 0.15
    lv = {x["code"]: x for x in r["lev"]}["00631L"]
    assert lv["ref"] == "0050" and lv["L"] == 2 and lv["gap1y"] < 0          # choppy year: 2× daily < 2× the year
    ac = {x["code"]: x for x in r["active"]}["00981A"]
    assert ac["ref"] == "0050" and ac["diff"] > 0


def test_page():
    from wsb.analytics import tw_etf_perf as P
    from tools import site_tw_etf_perf as S

    class Eng:
        pass
    e = Eng()
    e._tw_etf = {"available": True, "fx": {"etf": 1.0, "usd": 2.0, "fx": -1.0, "combo": 1.0}}
    e._tw_etf_perf = P.build(_fixture())
    h = S.sec_etf_rank(e) + S.sec_etf_payout(e) + S.sec_etf_rate(e) + S.sec_etf_lev(e) + S.sec_etf_active(e)
    for t in ("含息報酬", "吃老本", "對利率有多敏感", "不是剛好幾倍", "主動式 ETF 成績單", "利率之外還有匯率"):
        assert t in h, t
    assert h.count("一句話看懂") >= 5                                      # every card leads with one plain sentence
    for w in BANNED:
        assert w not in h, w
    assert S.perf_map(e)["0050"][0] is not None
    assert S.perf_map(e)["00999"][2] == "capital" and S.perf_map(e)["0050"][2] is None   # search table shows 吃老本
    e2 = Eng()
    e2._tw_etf_perf = {"available": False}
    assert S.sec_etf_rank(e2) == S.sec_etf_lev(e2) == ""
    src = open(os.path.join(os.path.dirname(S.__file__), "build_site.py"), encoding="utf-8").read()
    assert "STEP.sec_etf_payout" in src and "sec_etf_traps" not in src


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
