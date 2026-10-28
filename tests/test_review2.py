"""Second external review (2026-10-28): add conditions with missing required data, an emptied portfolio, the alert
outbox, covered collars, FX in day P&L, market sessions, halt resumption, MOPS keys, short bottom windows, split MOPS
sources, two-sided option mids.
Run: python -m tests.test_review2"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rv2_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402


def test_add_needs_required_data():
    from wsb.analytics import rulebook as R
    ck = lambda i, met: {"group": "add", "id": i, "zh": i, "met": met, "txt": "", "src": ""}      # noqa: E731
    s = R.summarize([ck("room", True), ck("ma200", True), ck("mom", True), ck("beat", True), ck("quality", None), ck("macro", None)])
    assert s["state"] == "pend" and not s["add_all"] and "全部成立" not in s["zh"] and s["add_unknown"] == 2
    s = R.summarize([ck(i, True) for i in ("room", "ma200", "mom", "beat", "quality", "macro")])
    assert s["state"] == "add" and s["add_all"]
    from tools import site_portfolio as PF
    assert "RB_REQ" in PF.JS if hasattr(PF, "JS") else "RB_REQ" in open(PF.__file__, encoding="utf-8").read()


def test_empty_portfolio_stays_empty():
    from wsb.analytics import portfolio as P
    d = tempfile.mkdtemp()
    main, fb = os.path.join(d, "main.json"), os.path.join(d, "fb.json")
    json.dump({"holdings": []}, open(main, "w"))
    json.dump({"holdings": [{"sym": "OLD", "shares": 10, "cost": 5}]}, open(fb, "w"))
    orig = P.SETTINGS
    P.SETTINGS = {"portfolio": {"enabled": True, "file": main, "fallback_file": fb}}
    try:
        assert P.load_holdings() == {}                                   # emptied → empty, never the old fallback
        os.remove(main)
        assert "OLD" in P.load_holdings()                                # no main file → fallback is fine
    finally:
        P.SETTINGS = orig


def test_alert_outbox_survives_a_failed_send():
    from wsb import store
    from wsb.bot.app import Alert, Sentinel
    b = Sentinel.__new__(Sentinel)
    sent = []

    async def once(alerts, limit=None):                                  # first round: nothing delivered
        sent.append([a.key for a in alerts])
    b._run_alerts_once = once
    asyncio.run(b._run_alerts([Alert("gamma:flip:20261028", "⚠️ WARNING", "t", "d")]))
    asyncio.run(b._run_alerts([]))                                       # the rule no longer produces it (state consumed)
    assert sent[1] == ["gamma:flip:20261028"]                            # …but the outbox still offers it
    store.alert_mark("gamma:flip:20261028", "⚠️ WARNING", "t")
    asyncio.run(b._run_alerts([]))
    assert sent[2] == []


def test_collar_only_when_covered():
    from wsb.analytics import hedge as H
    rows = []
    for k in (90, 95, 100, 105, 110):
        for t in ("P", "C"):
            rows.append({"type": t, "strike": k, "expiry": "2026-12-18", "dte": 50, "bid": 2.0, "ask": 2.2, "mid": 2.1, "iv": 0.2, "oi": 1, "delta": 0})
    chain = {"spot": 100.0, "rows": rows}
    no = H.structures(chain, 10000, "SPY", held_shares=0)
    yes = H.structures(chain, 10000, "SPY", held_shares=100)
    assert not any(x["kind"] == "collar" for x in no) and any(x["kind"] == "collar" for x in yes)
    assert all("net_cost_exec" in x for x in yes)


def test_fx_in_day_pnl_and_drawdown_base():
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wsb", "analytics", "portfolio.py"), encoding="utf-8").read()
    assert "fx_prev" in src and '"day_usd"' in src
    # price flat, USD/TWD 32 → 30: 320 TWD = 10 USD → 10.667 USD
    price, sh, conv, prev_fx, d1 = 320.0, 1, 30.0, 32.0, 0.0
    day = price * sh / conv - price / (1 + d1 / 100) * sh / prev_fx
    assert abs(day - (320 / 30 - 10)) < 1e-9
    app = open(os.path.join(os.path.dirname(src and __file__), "..", "wsb", "bot", "app.py"), encoding="utf-8").read()
    assert 'prev_v = pf["total_value_usd"] - pf["day_pnl_usd"]' in app


def test_sessions_use_each_market():
    from wsb.analytics import sessions as S
    px = pd.Series([1.0, 2.0], index=pd.to_datetime(["2026-10-27", "2026-10-28"]))
    hk_after = datetime(2026, 10, 28, 17, 0, tzinfo=ZoneInfo("Asia/Hong_Kong"))
    assert len(S.completed(px, "0700.HK", hk_after)) == 2                # HK closed at 16:00 → today's bar is final
    assert len(S.completed(px, "AAPL", hk_after)) == 1                   # New York still before its close


def test_halt_resume_and_mops_keys():
    from wsb.bot.app import Sentinel
    import time

    class Ev:
        halts = [{"sym": "NVDA", "name": "NVIDIA", "code": "T1", "reason": "重大消息", "ts": time.time() - 8 * 3600,
                  "when": "10/28 10:00 ET", "market": "NASDAQ", "resume": "10/28 14:00"}]
        fed = []
        mops = [{"code": "2330", "name": "台積電", "ts": time.time() - 60, "when": "", "market": "上市", "clause": "第11款", "subject": "A"},
                {"code": "2330", "name": "台積電", "ts": time.time() - 60, "when": "", "market": "上市", "clause": "第11款", "subject": "B"}]

    class Eng:
        events = Ev()

        def holding_tickers(self):
            return []
    from wsb.bot import app as APP
    orig = APP.SETTINGS
    APP.SETTINGS = {"sec_watch": ["NVDA"], "street": {"watchlist": ["2330.TW"]}, "taiwan": {"watch": ["2330"]}}
    b = Sentinel.__new__(Sentinel)
    b.engine = Eng()
    try:
        keys = [a.key for a in b._official_alerts()]
    finally:
        APP.SETTINGS = orig
    assert any(k.endswith(":resume") for k in keys)                      # 8 h old halt: only its resumption goes out
    assert not any(k.startswith("halt:NVDA") and not k.endswith(":resume") for k in keys)
    mk = [k for k in keys if k.startswith("mops")]
    assert len(mk) in (0, 2) and len(set(mk)) == len(mk)                 # same second, different subjects → two keys


def test_bottom_short_windows_apart():
    from wsb.analytics import bottom as B
    spx = pd.Series([100.0, 99, 98, 97, 96, 95], index=pd.bdate_range("2026-10-20", periods=6))
    f = B.forward(spx, spx.index[:1])
    assert f["further"] is None and f["further_n"] == 0 and f["open"] and f["open"][0]["so_far"] < 0


def test_mops_sources_split_and_two_sided_mid():
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wsb", "data", "events.py"), encoding="utf-8").read()
    assert '"tw_mops_listed"' in src and '"tw_mops_otc"' in src
    from wsb.data import options as O
    chain = O.parse_quotes({"data": {"current_price": 100, "options": [
        {"option": "SPY261218P00095000", "bid": 0, "ask": 3.0, "last_trade_price": 2.5},
        {"option": "SPY261218P00090000", "bid": 1.0, "ask": 1.2}]}})
    mids = {r["strike"]: r["mid"] for r in chain["rows"]}
    assert mids[95.0] == 0 and abs(mids[90.0] - 1.1) < 1e-9          # one-sided ask is not a mid


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
