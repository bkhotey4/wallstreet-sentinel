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
    idx = pd.bdate_range("2024-01-01", periods=400)
    r = rng.normal(0, 1, len(idx))                          # S&P daily %
    vix = pd.Series(16 + (-0.9 * r + rng.normal(0, 0.3, len(idx))), index=idx)    # level noise; diffs carry the relation
    spx = pd.Series(5000 * np.cumprod(1 + r / 100), index=idx)
    quotes = {"^VIX": {"price": 22.0, "chg_pct": 20.0, "asof": "2026-10-22"}, "^GSPC": {"price": 7600, "chg_pct": -1.2, "asof": "2026-10-22"},
              "^NDX": {"price": 29000, "chg_pct": -2.4}, "^SOX": {"price": 10800, "chg_pct": -5.8}, "^VIX9D": {"price": 24.0},
              "^VIX3M": {"price": 21.0}, "^TNX": {"price": 5.0, "chg_pct": -2.5}, "HYG": {"price": 77, "chg_pct": -1.5}, "^MOVE": {"price": 104}}
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
    eng.market.quotes["^GSPC"]["asof"] = "2099-01-01"        # fresh bar for the σ rule
    out = WA.build(eng)
    keys = [x["key"].split(":")[0] for x in out["items"]]
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


if __name__ == "__main__":
    test_vix_explain()
    test_web_alerts()
    print("ALL OK")
