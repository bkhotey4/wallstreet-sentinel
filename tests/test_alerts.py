"""VIX 拆解 + 網頁警示: spot-vol regression, readings, watch list, alert rules (no holdings ever), card + bell HTML.
Run: python -m tests.test_alerts"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_al_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import vix_explain as VX  # noqa: E402
from wsb.analytics import web_alerts as WA  # noqa: E402


class FakeMarket:
    def __init__(self, quotes, hist, sig=None):
        self.quotes, self.hist, self.sig = quotes, hist, sig or {}

    def q(self, t):
        return self.quotes.get(t)

    def series(self, t):
        return self.hist.get(t, pd.Series(dtype=float))

    def sigma_move(self, t):
        return self.sig.get(t)


def market():
    rng = np.random.default_rng(3)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=400)
    r = rng.normal(0, 1, len(idx))                          # S&P daily %
    vix = pd.Series(16 + (-0.9 * r + rng.normal(0, 0.3, len(idx))), index=idx)    # level noise; diffs carry the relation
    spx = pd.Series(5000 * np.cumprod(1 + r / 100), index=idx)
    quotes = {"^VIX": {"price": 22.0, "chg_pct": 20.0, "asof": "2026-10-22"}, "^GSPC": {"price": 7600, "chg_pct": -1.2, "asof": "2026-10-22"},
              "^NDX": {"price": 29000, "chg_pct": -2.4}, "^SOX": {"price": 10800, "chg_pct": -5.8}, "^VIX9D": {"price": 24.0},
              "^VIX3M": {"price": 21.0, "asof": "2026-10-22"}, "^TNX": {"price": 5.0, "chg_pct": -2.5}, "HYG": {"price": 77, "chg_pct": -1.5}, "^MOVE": {"price": 104}}
    return FakeMarket(quotes, {"^VIX": vix, "^GSPC": spx}, {"^SOX": -3.2, "HYG": -2.4, "^GSPC": -3.1})


def test_vix_explain():
    sv = VX.spot_vol(market().hist["^VIX"], market().hist["^GSPC"], 252)
    assert sv and -1.3 < sv["b"] < -0.5, sv                 # VIX points per 1% S&P
    rules = {"base": {"dd5": 16.0}, "rows": [{"zh": "VIX 升破 25", "verdict": "warn", "dd5": 30.0, "n": 93},
                                            {"zh": "VIX 升破 35", "verdict": "warn", "dd5": 46.0, "n": 26}]}
    eng = types.SimpleNamespace(market=market(), options=types.SimpleNamespace(spx={"spot": 7600, "zero_gamma": 7700}), sx={"rules": rules})
    r = VX.build(eng)
    assert r["available"] and r["hot"] and r["r3m"] > 1 and abs(r["chg_pts"] - (22 - 22 / 1.2)) < 1e-9
    txt = " ".join(x["zh"] for x in VX.readings(r))
    assert "倒掛" in txt and "高收益債同步重挫" in txt and "跌勢集中在科技" in txt and "殖利率同時下降" in txt
    assert "還差 3.0 點" in txt and "30%" in txt            # distance to the first useful-warning line, with its back-test
    wl = VX.watchlist(r)
    pick = lambda pre: next(x for x in wl if x["zh"].startswith(pre))  # noqa: E731
    assert pick("期限結構倒掛")["on"] and not pick("VIX 升破 25")["on"] and pick("高收益債")["on"]
    from tools import site_alerts as SA
    h = SA.sec_vix_explain(eng)
    assert "VIX 拆解" in h and "接下來要看的訊號" in h and "不是買賣建議" in h
    eng.market.quotes["^VIX"] = {"price": 15.0, "chg_pct": 1.0, "asof": "2026-10-22"}
    assert SA.sec_vix_hot(eng) == "" and SA.sec_vix_explain(eng) != ""      # 總覽 shows it only on hot days
    print("ok vix explain")


def test_web_alerts():
    st = types.SimpleNamespace(score=72.0, chg_1d=9.0, label="高壓", emoji="🟠", blocks={"信用": 70, "波動率": 68},
                               history=pd.Series([1.0], index=pd.to_datetime(["2026-10-22"])),
                               drivers=lambda n: [types.SimpleNamespace(id="vix", score=80)])
    eng = types.SimpleNamespace(market=market(), stress=st, options=types.SimpleNamespace(spx={"spot": 7600, "zero_gamma": 7700}),
                                canary={"rows": [{"id": "hy", "zh": "高收益債", "state": "alert", "asof": "2026-10-22"}]},
                                playbook={"stage": 3, "name": "防守", "emoji": "🔴", "points": 9, "why": [("x", "VIX 倒掛")]},
                                odds={"horizons": [{"days": 21, "drawdown_pct": 5, "adjusted": 35.0, "base_rate": 17.0, "lift_adj": 2.06}]},
                                sx={"rules": {"base": {"dd5": 16.0}, "rows": [{"k": "vix25", "zh": "VIX 升破 25", "en": "VIX > 25", "verdict": "warn",
                                                                             "now": True, "last": "2026-10-22", "dd5": 30.0, "n": 93}]}},
                                portfolio={"total_value_usd": 1e5, "day_pnl_usd": -9000, "positions": [{"sym": "NVDA", "d1_pct": -9}]})
    eng.market.quotes["^GSPC"]["asof"] = eng.market.hist["^GSPC"].index[-1].strftime("%Y-%m-%d")   # σ only on the quote's own bar
    eng.market.sig["HYG"] = -3.5                              # HYG quote older than its history bar → skipped
    eng.market.hist["HYG"] = eng.market.hist["^GSPC"] / 50
    eng.market.quotes["HYG"]["asof"] = "2020-01-02"
    out = WA.build(eng)
    keys = [x["key"].split(":")[0] for x in out["items"]]
    eng.market.quotes["^VIX3M"]["asof"] = "2026-10-15"          # stale VIX3M must not fake an inversion
    assert not any(x["key"].startswith("vix_back") for x in WA.build(eng)["items"])
    eng.market.quotes["^VIX3M"]["asof"] = "2026-10-22"
    from wsb.analytics import danger as DG                    # a component quote from an earlier day adds no points
    qq = {"^GSPC": {"chg_pct": -2.5, "asof": "2026-10-22"}, "HYG": {"chg_pct": -3.0, "asof": "2026-10-20"}}
    r_old = DG.score("us", lambda t: qq.get(t), day="2026-10-22")
    assert "HYG" not in [h["ticker"] for h in r_old["hits"]] and "^GSPC" in [h["ticker"] for h in r_old["hits"]]
    assert not any(x["key"].startswith("sigma:HYG") for x in out["items"])
    assert any(x["key"].startswith("sigma:^GSPC") for x in out["items"])
    for k in ("ssi", "ssi_jump", "vix_back", "canary", "playbook", "odds", "rule", "gamma"):
        assert k in keys, (k, keys)
    blob = json.dumps(out, ensure_ascii=False)
    assert "NVDA" not in blob and "持倉" not in blob and "pf_" not in blob     # holdings never reach the public page
    assert out["items"][0]["lv"] == "alert" and [x["lv"] for x in out["items"]][-1] == "watch"
    assert len({x["key"] for x in out["items"]}) == len(out["items"])         # stable, unique keys (the browser dedups on them)
    from tools import site_alerts as SA
    b = SA.bell_html(out)
    assert 'id="alert-data"' in b and "</script" in b and "<\\/" not in b.split("</script>")[0][-5:]
    print("ok web alerts")


def test_stability_under_bell():
    eng = types.SimpleNamespace(_stability_view={"funding": {"state": "緊繃", "date": "2026-10-23", "sofr": 4.4, "spread": 12.0, "read": "資金緊"},
                                                 "coverage": {"updated": "2026-10-01", "gaps": [{"risk": "x"}]}})
    out = []
    WA._stability(eng, out, pd.Timestamp("2026-10-26", tz="UTC").to_pydatetime())
    assert len(out) == 1 and out[0]["lv"] == "alert" and out[0]["tab"] == "stability" and "短期資金市場緊繃" in out[0]["zh"]


def test_stale_quote():
    """台股 case 2026-10-22: Yahoo throttled, the day-late TWSE file gave 10-21 (+1.28%) while history had 10-22 (−1.81%)."""
    from wsb.data.market import MarketData
    m = MarketData()
    idx = pd.bdate_range(end="2026-10-22", periods=80)
    px = np.linspace(40000, 46890, len(idx))
    px[-1] = 46041.43
    m.history = pd.DataFrame({"^TWII": px, "^GSPC": np.linspace(7000, 7660, len(idx))}, index=idx)
    m.quotes = {"^TWII": {"price": 46887.77, "prev": 46295.0, "chg_pct": 1.28, "asof": "2026-10-21", "source": "TWSE"},
                "^GSPC": {"price": 7672.0, "prev": 7660.0, "chg_pct": 0.16, "asof": "2026-10-23"}}
    q = m.q("^TWII")
    assert q["asof"] == "2026-10-22" and q["price"] == 46041.43 and q["chg_pct"] < -1.5 and q["src"] == "history", q
    assert m.q("^GSPC")["price"] == 7672.0                    # a quote newer than history is kept as is
    sg = m.sigma_move("^TWII")
    assert sg is not None and sg < 0 and np.sign(sg) == np.sign(q["chg_pct"])
    row = next(r for r in m.returns_table(["^TWII"]) if r["ticker"] == "^TWII")
    assert row["d1"] < 0 and row["asof"] == "2026-10-22"     # the AI context line now describes one day
    assert m.q("NOPE") is None
    print("ok stale quote")


def test_fomc_drift():
    from wsb.analytics import fomc_drift as FD
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=3600)
    rng = np.random.default_rng(5)
    r = rng.normal(0.0003, 0.01, len(idx))
    dates = [d.strftime("%Y-%m-%d") for d in idx[60:-10:40]]
    for d in dates:                                          # +1% on every decision day → day mean must stand out
        r[idx.get_loc(pd.Timestamp(d))] += 0.01
    spx = pd.Series(4000 * np.cumprod(1 + r), index=idx)
    vix = pd.Series(np.where(np.arange(len(idx)) % 80 < 40, 25.0, 15.0), index=idx)
    nxt = (pd.Timestamp.today().normalize() + pd.offsets.BDay(3)).strftime("%Y-%m-%d")
    eng = types.SimpleNamespace(market=FakeMarket({"^GSPC": {"price": float(spx.iloc[-1]) * 1.01, "asof": "2999-01-01"}}, {"^GSPC": spx, "^VIX": vix}),
                                econ=types.SimpleNamespace(fomc=[{"date": d} for d in dates] + [{"date": nxt}]))
    FD.history_dates = lambda: []                            # synthetic dates only
    out = FD.build(eng)
    assert out["available"] and out["n"] == len(dates), out.get("n")
    d = out["stats"]["all"]["day"]
    assert d["mean"] > 0.8 and d["t"] > 2 and abs(d["base_mean"] - 0.03) < 0.1, d
    assert out["stats"]["hi"]["pre"]["n"] + out["stats"]["lo"]["pre"]["n"] == out["n"]
    nx = out["next"]
    assert nx["date"] == nxt and nx["so_far"] is not None and nx["asof"] == "2999-01-01"     # live quote newer than history used
    txt = " ".join(x["zh"] for x in FD.readings(out))
    assert "會前 5 日" in txt and "決議當天" in txt and all(x["lv"] == "info" for x in FD.readings(out))
    from tools import site_alerts as SA
    h = SA.sec_fomc_drift(eng)
    assert "FOMC 前漂移" in h and "不是買賣建議" in h
    print("ok fomc drift")


def test_card_stamps():
    import time as _t
    from tools import site_stamp as STP
    now = _t.time()
    today = pd.Timestamp.now(tz="America/New_York").strftime("%Y-%m-%d")
    m = FakeMarket({"^GSPC": {"price": 1.0, "asof": today}, "^TWII": {"price": 1.0, "asof": "2020-01-02"}}, {})
    m.quotes_ts = now - 600
    eng = types.SimpleNamespace(market=m, fred=types.SimpleNamespace(ts=now - 3600, latest=lambda s: {"date": today}))
    st = STP.stamp(eng, "sec_markets", "markets", now)
    assert "最後更新" in st and "資料日" in st and " old" not in st and f'data-ts="{int(now - 600)}"' in st, st
    assert " old" in STP.stamp(eng, "sec_taiwan", "taiwan", now) and "資料偏舊" in STP.stamp(eng, "sec_taiwan", "taiwan", now)
    eng.fred.ts = now - 3 * 86400                               # a fetch older than 36 h is flagged even without a data date
    assert " old" in STP.stamp(eng, "sec_macro", "risk", now)
    assert "網站產生" in STP.stamp(eng, "sec_fees", "tools", now)   # static cards say when the page was built
    h = '<section class="card"><h2>A</h2><p>x</p></section><section class="card wide"><h2>B</h2></section>'
    out = STP.inject(h, "<p class=\"upd\">S</p>")
    assert out.count('<p class="upd">S</p>') == 2 and out.index("S</p>") > out.index("</h2>"), out
    assert STP.inject("<div>no card</div>", "<p>S</p>") == "<div>no card</div>"
    print("ok card stamps")


if __name__ == "__main__":
    test_card_stamps()
    test_fomc_drift()
    test_stale_quote()
    test_vix_explain()
    test_web_alerts()
    test_stability_under_bell()
    print("ALL OK")
