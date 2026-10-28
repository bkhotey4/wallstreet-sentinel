"""我的持股規則檢查: each rule on synthetic data, the summary ordering, the private embed and the edge-triggered DM alerts.
Run: python -m tests.test_rulebook"""
from __future__ import annotations

import os
import sys
import tempfile
import types

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rules_"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import rulebook as RB  # noqa: E402


def _px(start, end, n=400, seed=0):
    rng = np.random.default_rng(seed)
    return pd.Series(np.exp(np.linspace(np.log(start), np.log(end), n) + rng.normal(0, 0.005, n)),
                     index=pd.bdate_range(end="2026-10-16", periods=n))


def test_rules():
    bench = _px(100, 120, seed=1)
    weak = RB.price_stats(_px(300, 120, seed=2), bench)
    strong = RB.price_stats(_px(100, 180, seed=3), bench)
    assert weak["price"] < weak["ma200"] and weak["mom_12_1"] < 0 and weak["rel_6m"] < -15
    assert strong["price"] > strong["ma200"] and strong["mom_12_1"] > 0
    # broken thesis + below cost + trend break + far from the high → several exit checks
    ch = RB.check("AAA", {"weight": 20.0, "risk_contrib_pct": 30.0}, {"cost": 200.0}, weak, {"state": "alert", "bk_prob": 0.06},
                  {"eps": 1.0, "cons": 1.2, "surp": -16.7}, True, 40.0, 63.0, "半導體", "標普 500")
    s = RB.summarize(ch)
    assert s["state"] == "exit2" and s["exit_hits"] == 5 and s["trim_hits"] == 3, s
    assert not any(c["met"] for c in ch if c["group"] == "add" and c["id"] in ("room", "ma200", "mom", "quality", "beat", "macro"))
    # healthy, small, rising, beat, calm market → all add conditions
    ch = RB.check("BBB", {"weight": 5.0, "risk_contrib_pct": 6.0}, {"cost": 100.0}, strong, {"state": "ok", "bk_prob": 0.002},
                  {"eps": 1.2, "cons": 1.0, "surp": 20.0}, False, 10.0, 45.0, "半導體")
    s = RB.summarize(ch)
    assert s["state"] == "add" and s["add_met"] == s["add_n"] == 6, s
    # no SEC data / no earnings → 'unknown', never counted as met
    ch = RB.check("2330.TW", {"weight": 5.0}, {"cost": 100.0}, strong, None, None, None, 10.0, 45.0)
    unk = [c for c in ch if c["met"] is None]
    assert {c["id"] for c in unk} >= {"distress", "earnings", "quality", "beat", "risk"}
    s2 = RB.summarize(ch)
    assert s2["state"] in ("hold", "pend") and not s2["add_all"]          # "quality" unknown → never 全部成立
    # unknown theme → the concentration check is 'no data', never a made-up group; no history → price rules 'no data'
    ch = RB.check("NEWX", {"weight": 5.0}, {"cost": 10.0}, {"price": 12.0}, None, None, None, None, 45.0)
    assert {c["id"]: c["met"] for c in ch}["theme"] is None and {c["id"]: c["met"] for c in ch}["trend"] is None
    assert {c["id"]: c["met"] for c in ch}["trail"] is None and RB.summarize(ch)["state"] in ("hold", "pend")
    assert "標普 500" in next(c["txt"] for c in RB.check("AAA", {"weight": 5.0}, {"cost": 1.0}, weak, None, None, None, 5.0, 40.0, "x", "標普 500") if c["id"] == "trend")
    assert set(RB.DEFAULTS) <= set(RB.cfg())
    # thresholds come from settings
    user = RB.SETTINGS.get("rulebook")                      # settings.yaml overrides the defaults
    old = user.get("max_weight_pct")
    user["max_weight_pct"] = 4
    try:
        assert RB.summarize(RB.check("CCC", {"weight": 5.0}, {"cost": 1.0}, strong, None, None, None, 5.0, 40.0))["state"] == "trim"
    finally:
        user["max_weight_pct"] = old


def test_bot():
    from wsb import store
    from wsb.bot.app import Sentinel, rules_embed
    assert store.is_private_alert("rules:ORCL:exit2:2026-10-16")
    row = {"sym": "ORCL", "name": "Oracle", "weight": 13.0, "pnl_pct": -40.0, "asof": "2026-10-16", "state": "hold", "zh": "沒有規則觸發",
           "add_met": 2, "add_n": 6, "checks": [
               {"group": "exit", "id": "trend", "zh": "趨勢破壞（三項同時）", "met": True, "txt": "低於 200 日線"},
               {"group": "exit", "id": "trail", "zh": "移動停損", "met": True, "txt": "距高點 -58%"},
               {"group": "trim", "id": "weight", "zh": "單一持股 > 15%", "met": False, "txt": "佔比 13%"},
               {"group": "add", "id": "macro", "zh": "壓力指數 < 60", "met": False, "txt": "63"}]}
    rbk = {"available": True, "asof": "2026-10-16", "ssi": 63.0, "rows": [row]}
    bot = types.SimpleNamespace(engine=types.SimpleNamespace(rulebook=rbk))
    assert Sentinel._rule_alerts(bot) == []                                    # first sighting: state recorded only
    row.update(state="exit2", zh="出場檢查：2 項觸發")
    a = Sentinel._rule_alerts(bot)
    assert len(a) == 1 and a[0].key.startswith("rules:ORCL:exit2") and "不是買賣指令" in a[0].detail
    assert Sentinel._rule_alerts(bot) == []                                    # same state → no repeat
    e = rules_embed(rbk)
    assert "僅你可見" in e.title and "ORCL" in e.fields[0].name and "出場檢查 2/2" in e.fields[0].value
    assert "不是買賣指令" in e.footer.text


def main():
    test_rules()
    test_bot()
    print("RULEBOOK TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
