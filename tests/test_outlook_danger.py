"""全方位風險展望 + 盤中危險訊號.  Run: python -m tests.test_outlook_danger  (no network)"""
from __future__ import annotations

import os
import tempfile
import types
from datetime import datetime
from zoneinfo import ZoneInfo

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_outlook_"))

import tests.test_offline as T  # noqa: E402
from wsb.analytics import crash_odds as CO, danger as DG, outlook as OL, regime as RG, shock as SK  # noqa: E402
from wsb.analytics.stress import StressEngine  # noqa: E402


def quotes(d, asof="2026-10-12"):
    return lambda t: ({"chg_pct": d[t], "price": 100.0, "asof": asof} if t in d else None)


def main():
    # ---------------------------------------------------------------- NY Fed probit (published coefficients)
    assert abs(OL.nyfed_probability(0.0) - 29.7) < 0.2
    assert OL.nyfed_probability(-1.0) > 50 > OL.nyfed_probability(0.5) > OL.nyfed_probability(2.0)

    # ---------------------------------------------------------------- danger scoring
    calm = DG.score("us", quotes({"^GSPC": -0.3, "^VIX": 2.0, "HYG": 0.1}))
    assert calm["level"] == 0
    # broad, multi-asset selloff → systemic, at least 警戒
    sell = DG.score("us", quotes({"^GSPC": -2.1, "^NDX": -2.8, "^SOX": -4.1, "RSP": -1.9, "^VIX": 26.0,
                                  "HYG": -0.9, "KRE": -3.4, "JPY=X": -1.2}), vix_backwardation=True)
    assert sell["level"] >= 2 and sell["systemic"], sell
    assert sell["hits"][0]["pts"] >= sell["hits"][-1]["pts"] and "系統性" in sell["nature"]
    # tech-only drop: equities fall but vol/credit/fx quiet → not systemic
    tech = DG.score("us", quotes({"^GSPC": -1.2, "^NDX": -2.6, "^SOX": -5.5, "^VIX": 4.0, "HYG": -0.1}))
    assert tech["level"] >= 1 and not tech["systemic"] and "集中在股市" in tech["nature"], tech
    # benchmark gate: a VIX spike alone (S&P −0.3%) is not 大盤危險
    assert DG.score("us", quotes({"^GSPC": -0.3, "^VIX": 40.0, "HYG": -0.9}))["level"] == 0
    # crash day → 危險 regardless of points
    assert DG.score("us", quotes({"^GSPC": -4.2}))["level"] == 3
    tw = DG.score("tw", quotes({"^TWII": -2.6, "2330.TW": -3.8, "TWD=X": 0.7, "^N225": -2.4}))
    assert tw["level"] >= 2 and tw["zh"] == "台股"

    # ---------------------------------------------------------------- session detection (time zone + holiday)
    ny = ZoneInfo("America/New_York")
    q_today = quotes({"^GSPC": -1.0}, asof="2026-10-12")
    assert DG.in_session("us", q_today, datetime(2026, 10, 12, 10, 0, tzinfo=ny)) == "2026-10-12"
    assert DG.in_session("us", q_today, datetime(2026, 10, 12, 8, 0, tzinfo=ny)) is None          # pre-market
    assert DG.in_session("us", q_today, datetime(2026, 10, 12, 16, 5, tzinfo=ny)) is None         # after close
    assert DG.in_session("us", quotes({"^GSPC": -1.0}, asof="2026-10-09"),
                         datetime(2026, 10, 12, 10, 0, tzinfo=ny)) is None                        # no bar today = holiday
    assert DG.in_session("us", q_today, datetime(2026, 10, 11, 10, 0, tzinfo=ny)) is None         # Sunday
    tpe = ZoneInfo("Asia/Taipei")
    q_tw = lambda t: {"chg_pct": -2.0, "asof": "2026-10-13"} if t == "^TWII" else None            # noqa: E731
    assert DG.in_session("tw", q_tw, datetime(2026, 10, 13, 10, 30, tzinfo=tpe)) == "2026-10-13"
    assert DG.in_session("tw", q_tw, datetime(2026, 10, 13, 13, 45, tzinfo=tpe)) is None

    # ---------------------------------------------------------------- outlook on the synthetic market
    st = StressEngine(T.m, T.fr).compute()
    odds = CO.crash_odds(st.history, T.m.series("^GSPC"), st.score, st.chg_20d)
    rg = RG.classify(T.m, T.fr)
    val = {"available": True, "hot": ["巴菲特指標"], "groups": [{"key": "value", "items": [
        {"label": "巴菲特指標", "value": 210.0, "unit": "%", "pctile": 96.0, "grade": "極端", "high_is_hot": True}]}]}
    te = {"season": {"n": 20, "beats": 15, "avg_surp": 3.1, "avg_react": -1.2, "rev_yoy": 8.0},
          "groups": [{"theme": "半導體", "beat": 50.0}]}
    rot = {"available": True, "breadth": {"us": {"now": 35.0}},
           "sectors": [{"sym": "XLU", "name": "公用事業", "quad": "領先"}, {"sym": "XLK", "name": "科技", "quad": "轉弱"}],
           "equal_weight": {"chg_3m": -4.0}}
    eng = types.SimpleNamespace(stress=st, odds=odds, fred=T.fr, regime=rg, valuation=val, techearn=te, rotation=rot,
                                intel={}, exposure={})
    o = OL.build(eng)
    d = {x["key"]: x for x in o["dims"]}
    assert o["available"] and 0 <= o["score"] <= 100 and o["top"]
    assert d["valuation"]["score"] == 96.0 and d["valuation"]["label"] == "高"
    assert d["earnings"]["score"] == 50.0 and any("好消息不漲" in e for e in d["earnings"]["evidence"])   # (85-75)*2+20 = 40, +10 beats-but-falls
    assert d["sectors"]["score"] > 55 and any("防禦類股" in e for e in d["sectors"]["evidence"])
    assert d["news"]["score"] is None and o["coverage"] < 1                       # missing pillar excluded, not zero
    w = {k: v for k, v in o["weights"].items() if d[k]["score"] is not None}
    exp = sum(w[k] * d[k]["score"] for k in w) / sum(w.values())
    assert abs(o["score"] - round(exp, 1)) < 0.11
    hz = {h["months"]: h for h in o["horizons"]}
    assert set(hz) >= {1, 3, 6, 12} and hz[12]["model_zh"].startswith("紐約聯準會")
    assert OL.summary_lines(o)[0].startswith("全方位風險")

    # ---------------------------------------------------------------- data pack + embed + site sections
    import tests.test_intel as TI
    from wsb.ai import context
    from wsb.bot import command as CMD
    full = TI.T_engine(st, rg, SK.build(st, T.m.series("^GSPC")), [])
    full.outlook = o
    pack = context.build(full, "full", private=False)
    assert "## 全方位風險展望" in pack and "紐約聯準會" in pack
    em = CMD.embed_outlook(full)
    assert "全方位風險" in em.title and len(em.fields) >= 4
    from tools import site_outlook as SO
    html = SO.sec_outlook_hero(full) + SO.sec_outlook_dims(full) + SO.sec_outlook_mini(full)
    assert "全方位風險展望" in html and "九大面向" in html and "c_recprob" in html
    full.exposure = {"available": True, "mode": "portfolio", "paths": []}
    assert SO.sec_exposure(full) == ""                                             # holdings never published
    print(f"OUTLOOK / DANGER TESTS PASSED ✅  ({o['headline']})")


if __name__ == "__main__":
    main()
