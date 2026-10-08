"""Tests for weekly report / FOMC diff / per-rule scorecard / portfolio X-ray / hedge structures / TW extras."""
import time
import types
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

import tests.test_offline as T


def test_fomc():
    from wsb.data import fomc as F
    page = """<h4>2026 FOMC Meetings</h4>
      <div class="fomc-meeting__month col-xs-5"><strong>January</strong></div><div class="fomc-meeting__date">27-28</div>
      <div class="fomc-meeting__month col-xs-5"><strong>March</strong></div><div class="fomc-meeting__date">17-18*</div>
      <h4>2025 FOMC Meetings</h4>
      <div class="fomc-meeting__month col-xs-5"><strong>December</strong></div><div class="fomc-meeting__date">9-10</div>"""
    ds = F.decision_dates(page)
    assert ds == [date(2025, 12, 10), date(2026, 1, 28), date(2026, 3, 18)], ds
    assert F.statement_url(date(2026, 3, 18)).endswith("monetary20260318a.htm")
    prev = """<p>Recent indicators suggest that economic activity has been expanding at a solid pace. The Committee seeks to achieve maximum employment and inflation at the rate of 2 percent.</p>
              <p>Inflation remains somewhat elevated. The Committee judges that the risks to achieving its employment and inflation goals are roughly in balance.</p><p>short</p>"""
    new = """<p>Recent indicators suggest that economic activity has been expanding at a moderate pace. The Committee seeks to achieve maximum employment and inflation at the rate of 2 percent.</p>
             <p>Inflation remains somewhat elevated. The Committee judges that the risks to achieving its employment and inflation goals are roughly in balance.</p>
             <p>The Committee decided to slow the pace of balance sheet runoff, noting inflation progress.</p>"""
    a, b = F.extract_text(prev), F.extract_text(new)
    assert a and b and "short" not in a
    d = F.diff(a, b)
    assert d["changed"] and any("solid pace" in x for x in d["removed"]) and any("moderate pace" in x for x in d["added"])
    assert any("balance sheet" in x for x in d["added"]) and 0 < d["similarity"] < 1
    assert not F.diff(a, a)["changed"]
    assert F.extract_text("<html>nothing</html>") is None


def test_scorecard_families():
    from wsb.analytics import scorecard as SC
    assert SC.family("playbook:2:20261004") == "風險劇本升級" and SC.family("shock:div:20261004") == "股債背離"
    assert SC.family("shock:信用事件:20261004") == "衝擊路徑點火" and SC.family("ssi_level_3") == "壓力指數升級"
    spx = T.m.series("^GSPC")
    spx = spx.copy()
    spx.index = pd.bdate_range(end=pd.offsets.BDay().rollback(pd.Timestamp.today().normalize()), periods=len(spx))
    now = time.time()
    rows = [(now - (60 + 3 * i) * 86400, "playbook:2:%d" % i, "risk", "⚠️ WARNING", "劇本", float(spx.iloc[-45 - 3 * i]), 60.0) for i in range(5, -1, -1)]
    rows += [(now - 50 * 86400, "regime:stock_bond:x", "risk", "⚠️ WARNING", "避險", float(spx.iloc[-35]), 60.0)]
    r = SC.evaluate(rows, spx)
    assert "風險劇本升級" in r["families"] and r["families"]["風險劇本升級"]["episodes"] == 6
    assert r["families"]["風險劇本升級"]["verdict"] in ("有用", "反效果", "無明顯差別", "樣本不足")
    assert r["families"]["避險機制失靈"]["verdict"] == "樣本不足"                         # 1 episode → no verdict
    assert SC.verdict({20: {"episodes": 10, "lift": 2.0}}) == "有用" and SC.verdict({20: {"episodes": 10, "lift": 0.4}}) == "反效果"
    assert SC.verdict({20: {"episodes": 3, "lift": 3.0}}) == "樣本不足"


def test_weekly():
    from wsb import weekly as WK
    from wsb import store
    from wsb.analytics import portfolio as PFO
    from wsb.analytics.stress import StressEngine
    from wsb.bot import command as CMD
    st = StressEngine(T.m, T.fr).compute()
    port = PFO.analyze(T.m, {"NVDA": {"shares": 15, "cost": 50, "currency": "USD", "name": "NVDA"},
                             "TSM": {"shares": 12, "cost": 60, "currency": "USD", "name": "TSM"}})
    cal = types.SimpleNamespace(upcoming=lambda d=14: [{"date": (date.today() + timedelta(days=2)).isoformat(), "type": "fomc", "event": "FOMC 利率決議"}])
    eng = types.SimpleNamespace(market=T.m, stress=st, portfolio=port, calendar=cal, shock={}, playbook={"name": "留意", "stage": 1, "points": 2})
    store.alert_mark("playbook:1:weeklytest%d" % int(time.time()), "⚠️ WARNING", "風險劇本升級 → 留意", kind="risk")
    f = WK.facts(eng, {"families": {"風險劇本升級": {"episodes": 6, "verdict": "有用", "by_horizon": {20: {"episodes": 6, "hit_rate": 50.0, "base_rate": 20.0}}}}})
    assert f["spx_week"] is not None and f["pf_week"] is not None and f["alerts_total"] >= 1
    tot = sum(c["contrib"] for c in f["pf_contrib"])
    assert abs(tot - f["pf_week"]) < 1e-9
    txt = WK.facts_text(f)
    assert "持倉週報酬" in txt and "風險劇本升級" in txt and "FOMC" in txt
    deck = CMD.deck_weekly(f)
    assert len(deck) == 3 and all(len(b) > 5000 for b in deck)
    assert CMD.embed_weekly(f).description


def fake_market(n=600, seed=5, crash=False):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=pd.offsets.BDay().rollback(pd.Timestamp.today().normalize()), periods=n)
    mk = rng.normal(0.0004, 0.01, n)
    tnx = 4.0 + np.cumsum(rng.normal(0, 0.05, n))
    rate_d = np.diff(tnx, prepend=tnx[0])
    usd = rng.normal(0, 0.004, n)
    sm = 1.3 * mk + rng.normal(0, 0.008, n)
    a = 1.5 * mk - 0.02 * rate_d + rng.normal(0, 0.004, n)
    b = 1.4 * mk + rng.normal(0, 0.005, n)
    c = rng.normal(0.0003, 0.012, n)                      # independent of everything
    px = lambda r: pd.Series(100 * np.exp(np.cumsum(r)), index=idx)
    d = {"^GSPC": px(mk), "^TNX": pd.Series(tnx, index=idx), "DX-Y.NYB": px(usd), "SMH": px(sm), "AAA": px(a), "BBB": px(b), "CCC": px(c)}
    if crash:
        d["AAA"].iloc[-3:] = d["AAA"].iloc[-4] * np.array([0.97, 0.93, 0.88])      # sharp drop below the stop
    return types.SimpleNamespace(series=lambda t: d.get(t, pd.Series(dtype=float)).copy(), d=d)


def pf_of(m, weights):
    pos = [{"sym": k, "value_usd": v, "weight": v / sum(weights.values()) * 100, "price": float(m.d[k].iloc[-1]), "beta": 1.0} for k, v in weights.items()]
    return {"positions": pos, "total_value_usd": sum(weights.values())}


def test_xray():
    from wsb.analytics import xray as X
    m = fake_market()
    pf = pf_of(m, {"AAA": 4000, "BBB": 4000, "CCC": 2000})
    d = X.diversification(m, pf)
    assert d["available"] and d["n_positions"] == 3
    assert 1.0 <= d["enb"] < 2.5 and d["avg_corr"] > 0.2, d                      # AAA & BBB are one bet
    assert d["clusters"] and set(d["clusters"][0]["members"]) == {"AAA", "BBB"} and abs(d["clusters"][0]["weight"] - 80) < 0.5, d["clusters"]
    ind = X.diversification(m, pf_of(m, {"CCC": 5000, "AAA": 5000}))             # independent pair → ENB ~2, no cluster
    assert ind["enb"] > 1.7 and not ind["clusters"], ind
    # factor scenarios recover the planted betas
    F = X._factors(m)
    e = X.betas(m, "AAA", F)
    assert abs(e["b"]["mkt"] - 1.5) < 0.15 and abs(e["b"]["rate"] + 0.02) < 0.01 and e["r2"] > 0.8, e
    sc = X.scenarios(m, pf)
    mk20 = next(r for r in sc["scenarios"] if r["name"] == "標普 −20%")
    assert -33 < mk20["pnl_pct"] < -17, mk20                                       # ~ -0.2*(1.5*0.4+1.4*0.4+0*0.2... ) ≈ -23%
    rate = next(r for r in sc["scenarios"] if r["name"].startswith("利率"))
    assert rate["pnl_pct"] < 0                                                    # AAA has negative rate beta
    # stops: calm series safe; crashed series breached
    up = types.SimpleNamespace(series=lambda t: pd.Series(np.linspace(100, 130, 100) + np.sin(np.arange(100)), index=pd.bdate_range(end="2026-10-02", periods=100)))
    calm = X.stops(up, {"positions": [{"sym": "UP", "value_usd": 1000, "weight": 100, "price": 130.0}]})
    assert calm and not calm[0]["breached"] and calm[0]["stop"] < calm[0]["high"]
    mc = fake_market(crash=True)
    pc = pf_of(mc, {"AAA": 4000, "BBB": 4000, "CCC": 2000})
    st = {r["sym"]: r for r in X.stops(mc, pc)}
    assert st["AAA"]["breached"] and st["AAA"]["dist_pct"] < -5, st["AAA"]
    # events
    ev = X.event_exposure(pf, [{"date": "2026-10-10", "type": "earnings", "ticker": "AAA"}, {"date": "2026-10-09", "type": "fomc", "event": "FOMC"},
                                {"date": "2026-10-11", "type": "earnings", "ticker": "ZZZ"}])
    assert len(ev["earnings"]) == 1 and abs(ev["earnings_weight"] - 40) < 0.5 and len(ev["macro"]) == 1
    # vol target: tiny target → scale < 1; huge target → 1
    lo, hi = X.vol_target(m, pf, 5.0), X.vol_target(m, pf, 500.0)
    assert lo["scale"] < 0.5 and lo["trim_usd"] > 0 and hi["scale"] == 1.0 and hi["trim_usd"] == 0
    # decks render
    from wsb.bot import command as CMD
    cal = types.SimpleNamespace(upcoming=lambda d=14: [])
    eng = types.SimpleNamespace(market=m, portfolio=pf, calendar=cal)
    eng.xray = X.build(eng)
    deck = CMD.deck_xray(eng)
    assert len(deck) == 4 and all(len(b) > 5000 for b in deck) and CMD.embed_xray(eng).title
    assert len(CMD.deck_xray(types.SimpleNamespace(xray={}))) == 1


def test_hedge_structures():
    from wsb.analytics import hedge as HG
    spot = 500.0
    rows = []
    for dte in (44, 91):
        exp = (date.today() + timedelta(days=dte)).isoformat()
        for k in range(380, 640, 5):
            put = max(k - spot, 0) + 0.2 * spot * (dte / 365) ** 0.5 * 0.4 * np.exp(-abs(k / spot - 1) * 4) + 0.05
            call = max(spot - k, 0) + 0.2 * spot * (dte / 365) ** 0.5 * 0.4 * np.exp(-abs(k / spot - 1) * 4) + 0.05
            rows.append({"type": "P", "strike": float(k), "expiry": exp, "dte": float(dte), "bid": put, "ask": put, "mid": put, "iv": .2, "oi": 1, "delta": 0})
            rows.append({"type": "C", "strike": float(k), "expiry": exp, "dte": float(dte), "bid": call, "ask": call, "mid": call, "iv": .2, "oi": 1, "delta": 0})
    ch = {"spot": spot, "rows": rows}
    sts = HG.structures(ch, 100000.0, "SPY")
    kinds = {x["kind"] for x in sts}
    assert kinds == {"put spread", "collar"}, kinds
    ps = next(x for x in sts if x["kind"] == "put spread")
    # at -20% both puts are in the money → the hedge pays exactly its max cover
    assert abs(ps["pnl"][-20] - ps["max_cover"]) < 1e-6 and ps["pnl"][10] < 0 and abs(ps["pnl"][10] + ps["net_cost"]) < 1e-6, ps
    co = next(x for x in sts if x["kind"] == "collar")
    cheap = HG.put_plans(ch, 100000.0, 1.0, "SPY")[0]["cost"]
    assert abs(co["net_cost"]) < cheap * 0.5, (co["net_cost"], cheap)                # (almost) free vs a naked put
    assert co["pnl"][-20] > 0 and co["pnl"][10] < 0 and co["cap_pct"] > 0            # protects on the way down, gives up the upside
    res = HG.analyze({"total_value_usd": 100000.0, "betas": {"SPY": 1.0}, "positions": [], "beta": 1.0}, {"SPY": ch}, 50.0)
    assert res["underlyings"]["SPY"]["structures"]


MARGN_NEW = {"stat": "OK", "tables": [
    {"fields": ["項目", "買進", "賣出", "現金(券)償還", "前日餘額", "今日餘額"],
     "data": [["融資(交易單位)", "1", "2", "3", "4", "5"],
              ["融資金額(仟元)", "40,000,000", "35,000,000", "1,000,000", "300,000,000", "304,000,000"]]}]}
MARGN_OLD = {"stat": "OK", "fields": ["項目", "買進", "賣出", "現金(券)償還", "前日餘額", "今日餘額"],
             "data": [["融資金額(仟元)", "1", "1", "1", "200,000,000", "194,000,000"]]}


def test_margin_parse():
    from wsb.data.taiwan import TaiwanData
    m = TaiwanData.parse_margin(MARGN_NEW)
    assert abs(m["bal_bn"] - 3040) < 1e-6 and abs(m["chg_pct"] - 1.3333) < 1e-3, m
    m2 = TaiwanData.parse_margin(MARGN_OLD)
    assert m2["chg_bn"] < 0 and abs(m2["chg_pct"] + 3.0) < 1e-6
    assert TaiwanData.parse_margin({"stat": "很抱歉，沒有符合條件的資料!"}) is None
    assert TaiwanData.parse_margin({"stat": "OK", "data": [["其他", "1"]]}) is None
    assert TaiwanData.parse_margin([]) is None


def test_stooq_and_backup_and_web():
    from wsb.data import market as MK
    assert MK.stooq_symbol("NVDA") == "nvda.us" and MK.stooq_symbol("^GSPC") is None and MK.stooq_symbol("2330.TW") is None
    s = MK.parse_stooq("Date,Open,High,Low,Close,Volume\n2026-09-29,1,2,0.5,10.5,100\n2026-09-30,1,2,0.5,11.0,100\n")
    assert list(s.values) == [10.5, 11.0] and s.index[-1] == pd.Timestamp("2026-09-30")
    assert MK.parse_stooq("No data").empty and MK.parse_stooq("").empty
    from wsb import store
    import glob, os
    store.kv_set("backup_probe", {"x": 1})
    path = store.backup(keep=2)
    assert path and os.path.exists(path)
    assert store.backup(keep=2) is None                                  # one per day
    import sqlite3
    c = sqlite3.connect(path)
    assert c.execute("SELECT count(*) FROM kv WHERE k='backup_probe'").fetchone()[0] == 1
    c.close()
    os.remove(path)
    from wsb import web
    eng = types.SimpleNamespace(stress=types.SimpleNamespace(score=51.2, label="留意"),
                                playbook={"emoji": "🟡", "name": "留意", "points": 3, "why": [(1, "<b>x</b>")]}, portfolio={})
    page = web.render(eng)
    assert "51" in page and "&lt;b&gt;" in page and "<b>x</b>" not in page      # HTML-escaped


def main():
    test_margin_parse()
    test_stooq_and_backup_and_web()
    test_fomc()
    test_scorecard_families()
    test_weekly()
    test_xray()
    test_hedge_structures()
    print("EXTRAS TESTS PASSED ✅")


if __name__ == "__main__":
    main()
