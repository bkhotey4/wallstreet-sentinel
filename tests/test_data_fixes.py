"""Regression tests for the 2026-11 data-layer audit (offline, synthetic input).  Run: python -m tests.test_data_fixes"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
import types
from datetime import date, timedelta
from pathlib import Path

os.environ["WSB_DATA_DIR"] = tempfile.mkdtemp(prefix="wsb_datafix_")      # never touch the real data_cache
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import tests.test_offline  # noqa: E402,F401  (stubs optional deps)
from wsb.data import http  # noqa: E402
from wsb.health import HEALTH  # noqa: E402


def _fake_http(fn):
    """Route wsb.data.http.get through fn(url, kwargs) for the duration of a test; returns a restore callable."""
    old = http.get

    async def get(url, **kw):
        r = fn(url, kw)
        if isinstance(r, Exception):
            raise r
        return r
    http.get = get
    return lambda: setattr(http, "get", old)


def _state(name):
    s = HEALTH.sources.get(name)
    return None if s is None else ("ok" if (s.last_ok or 0) > (s.last_err or 0) else "fail")


async def _nosleep(*_a, **_k):
    return None


# 1) MOF JGB: Shift-JIS bytes; ts / health only advance when the current-month file is recent
def t_jgb():
    from wsb.data import global_yields as GY
    hist_days = pd.bdate_range(end=pd.Timestamp.now().normalize() - pd.Timedelta(days=60), periods=300)
    head = "国債金利情報,,,,,,\nDate,1Y,2Y,5Y,10Y,20Y,30Y\n"
    hist = (head + "".join(f"{d:%Y/%m/%d},0.1,0.2,0.5,1.0,1.8,2.1\n" for d in hist_days)).encode("shift_jis")
    stale_cur = (head + "".join(f"{d:%Y/%m/%d},0.1,0.2,0.5,1.1,1.8,2.1\n" for d in hist_days[-3:])).encode("shift_jis")
    try:
        hist.decode("utf-8")
        raise AssertionError("fixture should not be valid utf-8")
    except UnicodeDecodeError:
        pass
    assert GY.parse(GY.decode(hist))["10Y"].iloc[-1] == 1.0
    cur = {"b": stale_cur}
    restore = _fake_http(lambda u, kw: hist if "jgbcme_all" in u else cur["b"])
    try:
        g = GY.GlobalYields()
        asyncio.run(g.refresh(force=True))
        assert len(g.jgb) >= 250 and g.ts == 0.0, "stale current-month file → data kept, ts not renewed"
        assert _state("mof_jgb") == "fail"
        recent = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=3)
        cur["b"] = (head + "".join(f"{d:%Y/%m/%d},0.1,0.2,0.5,1.2,1.8,2.1\n" for d in recent)).encode("shift_jis")
        asyncio.run(g.refresh(force=True))
        assert g.ts > 0 and _state("mof_jgb") == "ok" and g.get("10Y").iloc[-1] == 1.2
    finally:
        restore()
    print("  JGB Shift-JIS + honest ts ok")


# 2) TreasuryDirect upcoming: competitiveAuctionCloseDate accepted; rows that never parse fail health
def t_liquidity_auctions():
    from wsb.data import liquidity as LQ
    soon = (date.today() + timedelta(days=5)).isoformat() + "T00:00:00"
    rows = [{"securityType": "Note", "securityTerm": "10-Year", "competitiveAuctionCloseDate": soon, "offeringAmount": "42000000000"}]
    restore = _fake_http(lambda u, kw: rows)
    try:
        ev = asyncio.run(LQ.treasury_auctions())
        assert len(ev) == 1 and "10 年期" in ev[0]["event"], ev
        rows[:] = [{"securityType": "Bond", "securityTerm": "30-Year", "someNewDate": soon}]
        assert asyncio.run(LQ.treasury_auctions()) == [] and _state("treasury_upcoming") == "fail"
    finally:
        restore()
    print("  liquidity auction date fallback ok")


# 3 + 4) Taipei housing CSV in Big5; an all-failed run does not renew twmacro / bondflows ts
def t_twmacro_bondflows():
    from wsb.data import bondflows as BF
    from wsb.data import twmacro as TM
    csv = "類別,期別,月指數\n" + "".join(f"全市,{113 + i // 12}/{i % 12 + 1},{100 + i}\n" for i in range(30))
    big5 = csv.encode("cp950")
    tp = TM.parse_taipei(TM.decode_taipei(big5))
    assert len(tp) == 30 and tp[0] == ["2024-01", 100.0], tp[:2]
    TM._save({"ts": 123.0, "cbc": {"x": [["2026-01", 1]]}})
    old_bf = TM._backfill

    async def nob(d):
        return None
    TM._backfill = nob
    restore = _fake_http(lambda u, kw: RuntimeError("down"))
    try:
        d = asyncio.run(TM.refresh(force=True))
        assert d["ts"] == 123.0 and d["cbc"] == {"x": [["2026-01", 1]]}, "all failed → ts and data kept"
        assert _state("tw_taipei_housing") == "fail" and _state("tw_ndc") == "fail" and _state("tw_cbc") == "fail"
        BF._save({"ts": 456.0, "mof": [[1, 2, 3, 4]]})
        b = asyncio.run(BF.refresh(force=True))
        assert b["ts"] == 456.0 and b["mof"] == [[1, 2, 3, 4]]
        assert _state("mof_flows") == "fail" and _state("tic_holders") == "fail" and _state("ofr_mmf") == "fail"
    except BaseException:
        TM._backfill = old_bf
        raise
    finally:
        restore()
    restore = _fake_http(lambda u, kw: big5 if u == TM.TAIPEI else RuntimeError("down"))
    try:
        d = asyncio.run(TM.refresh(force=True))
        assert d["ts"] > 123.0 and len(d["taipei"]) == 30 and _state("tw_taipei_housing") == "ok"
    finally:
        restore()
        TM._backfill = old_bf
    print("  twmacro Big5 + per-source freshness / bondflows ok")


# 5) crypto: per-feed ts, stale values dropped after ~2 cycles; funding interval from the timestamps
def t_crypto():
    from wsb.data import crypto as CR
    c = CR.CryptoSentiment()
    t = 1_000_000.0
    c.apply({"okx": {"BTC_funding_ann_pct": 10.0}, "cnn_fng": {"cnn_fng": 40}}, every=600, now=t)
    c.apply({"okx": RuntimeError("down"), "cnn_fng": {"cnn_fng": 41}}, every=600, now=t + 700)
    assert c.data["BTC_funding_ann_pct"] == 10.0 and "stale_sources" not in c.data
    c.apply({"okx": RuntimeError("down"), "cnn_fng": {"cnn_fng": 42}}, every=600, now=t + 1300)
    assert "BTC_funding_ann_pct" not in c.data and c.data["stale_sources"] == ["okx"] and c.data["cnn_fng"] == 42
    c.apply({"okx": {"BTC_funding_ann_pct": 11.0}}, every=600, now=t + 1400)
    assert "stale_sources" not in c.data and c.ts == t + 1400
    assert CR.funding_hours({"fundingTime": "1700000000000", "nextFundingTime": str(1700000000000 + 4 * 3600_000)}) == 4
    assert CR.funding_hours({}) == 8.0 and CR.funding_hours({"fundingTime": "1", "nextFundingTime": "1"}) == 8.0
    print("  crypto per-feed staleness + funding interval ok")


# 6) TAIFEX / TWSE: an all-failed fetch keeps the last good data and fails health
def t_taiwan_keep():
    from wsb.data import taiwan as TW
    t = TW.TaiwanData.__new__(TW.TaiwanData)
    t.flows, t.futures, t.revenue, t.ts = [{"date": "2026-11-03", "foreign": 1.0}], {"oi_foreign": 5, "pcr": [1]}, [], 0.0

    async def none(*_a):
        return None

    async def empty():
        return {}

    async def boom():
        raise RuntimeError("down")
    t._bfi82u, t._futures, t._revenue = none, empty, boom
    old = TW.asyncio.sleep
    TW.asyncio.sleep = _nosleep
    try:
        asyncio.run(t.refresh())
    finally:
        TW.asyncio.sleep = old
    assert t.flows == [{"date": "2026-11-03", "foreign": 1.0}] and t.futures == {"oi_foreign": 5, "pcr": [1]}
    assert _state("taifex") == "fail" and _state("twse") == "fail" and t.ts == 0.0

    async def part():
        return {"tx": {"last": 1}}
    t._futures = part
    t._bfi82u = none
    TW.asyncio.sleep = _nosleep
    try:
        asyncio.run(t.refresh())
    finally:
        TW.asyncio.sleep = old
    assert t.futures == {"oi_foreign": 5, "pcr": [1], "tx": {"last": 1}}, "a part missing this time keeps its old values"
    print("  taiwan keeps last good futures / flows ok")


# 7) FOMC dates: notation votes skipped, abbreviated cross-month meetings kept (fomc + calendar share econcal)
def t_fomc_dates():
    from wsb.data import calendar as CAL
    from wsb.data import fomc as F
    page = """<h4>2026 FOMC Meetings</h4>
      <div class="fomc-meeting__month"><strong>Oct/Nov</strong></div><div class="fomc-meeting__date">31-1</div>
      <div class="fomc-meeting__month"><strong>December</strong></div><div class="fomc-meeting__date">22 (notation vote)</div>
      <div class="fomc-meeting__month"><strong>December</strong></div><div class="fomc-meeting__date">8-9*</div>"""
    assert F.decision_dates(page) == [date(2026, 11, 1), date(2026, 12, 9)], F.decision_dates(page)
    today = CAL.us_today()
    ev = CAL.fomc_events([{"date": (today + timedelta(days=10)).isoformat()}, {"date": (today - timedelta(days=1)).isoformat()}])
    assert [e["type"] for e in ev] == ["fomc"]
    print("  FOMC shared parser ok")


# 8) SEC ticker map: stale cache returned when SEC refuses; sec.py uses the same map
def t_ticker_map():
    from wsb.data import edgar_holdings as EH
    from wsb.data import sec as SEC
    EH._MAP_FILE.write_text(json.dumps({"AAPL": {"cik": 320193, "title": "Apple"}}), encoding="utf-8")
    old_t = time.time() - 30 * 86400
    os.utime(EH._MAP_FILE, (old_t, old_t))
    old_get = EH._get

    async def forbidden(url, kind="json"):
        raise RuntimeError("403 Forbidden")
    EH._get = forbidden
    try:
        assert asyncio.run(EH.ticker_map())["AAPL"]["cik"] == 320193
        w = SEC.SecWatcher()
        asyncio.run(w._load_map())
        assert w.cik["AAPL"] == "0000320193"
        EH._MAP_FILE.unlink()
        try:
            asyncio.run(EH.ticker_map())
            raise AssertionError("no cache at all → the error surfaces")
        except RuntimeError:
            pass
    finally:
        EH._get = old_get
    print("  ticker map stale fallback ok")


# 9) SPX gamma asof = CBOE quote time
def t_options_asof():
    from wsb.data.options import parse_chain, quote_time
    exp = (date.today() + timedelta(days=20)).strftime("%y%m%d")
    opts = [{"option": f"SPXW{exp}{t}{k * 1000:08d}", "iv": 0.2, "open_interest": 100, "volume": 10, "gamma": 0.001}
            for k in (5900, 6000, 6100) for t in "CP"]
    js = {"timestamp": "2026-10-30 16:15:03", "data": {"current_price": 6000, "options": opts}}
    assert quote_time(js).strftime("%Y-%m-%d %H:%M") == "2026-10-30 20:15"      # EDT
    r = parse_chain(js)
    assert r["asof"] == "2026-10-30 20:15 UTC" and r["asof_source"] == "cboe"
    js.pop("timestamp")
    assert parse_chain(js)["asof_source"] == "fetch"
    print("  options asof from CBOE timestamp ok")


# 10) FedWatch: late-month meeting without next month's contract → no estimate
def t_fedwatch():
    from wsb.data import fedwatch as FW
    assert FW.implied(["2026-10-28"], {(2026, 10): 96.0}, 4.0) == [], "N−d = 3 days and no Nov contract → stop"
    out = FW.implied(["2026-10-28"], {(2026, 10): 96.0, (2026, 11): 96.25}, 4.0)
    assert out and abs(out[0]["rate_after"] - 3.75) < 1e-9
    assert FW.implied(["2026-09-16"], {(2026, 9): 96.0}, 4.0), "mid-month meeting still uses its own month"
    print("  fedwatch late-month guard ok")


# 11) per-series bundle freshness: one good series no longer renews the bundle; failed ones retried within the hour
def t_bundle_freshness():
    from wsb.data import freshness as FR
    from wsb.data import nowcast as NCD
    from wsb.data import transmission as TRM
    now = 10_000_000.0
    d = {"ts": now - 100, "A": {"x": 1}, "B": {"x": 1}}
    assert FR.due(d, ["A", "B"], 3600, now) == [] and d["ts_each"] == {"A": now - 100, "B": now - 100}
    d["ts_each"]["B"], d["try_each"]["B"] = now - 7200, now - 600
    assert FR.due(d, ["A", "B"], 3600, now) == [], "tried 10 min ago → wait"
    d["try_each"]["B"] = now - 4000
    assert FR.due(d, ["A", "B"], 3600, now) == ["B"]
    assert FR.bundle_ts(d, ["A", "B"]) == now - 7200
    old = TRM._fred
    calls = []

    async def fred(sid, start):
        calls.append(sid)
        if sid == "ICSA":
            raise RuntimeError("down")
        return {"2026-10-01": 1.0}
    TRM._fred = fred
    try:
        NCD._save({})
        d1 = asyncio.run(NCD.refresh())
        assert "ICSA" not in d1["ts_each"] and len(calls) == len(NCD.SERIES)
        calls.clear()
        d2 = asyncio.run(NCD.refresh())
        assert calls == [], "nothing due: fresh series wait a TTL, the failed one waits its retry hour"
        assert _state("nowcast") == "fail", "the still-missing series keeps health red"
        d2["try_each"]["ICSA"] -= 4000
        NCD._save(d2)
        asyncio.run(NCD.refresh())
        assert calls == ["ICSA"]
    finally:
        TRM._fred = old
    print("  per-series bundle freshness ok")


def t_euro_asia_per_series():
    from wsb.data import euro_asia as EA
    old = EA._fred
    ciss = "TIME_PERIOD,OBS_VALUE\n" + "".join(f"{d:%Y-%m-%d},0.1\n" for d in pd.bdate_range(end="2026-10-30", periods=1200))

    async def fred(sid):
        if "DE" in sid:
            raise RuntimeError("down")
        return {"2026-09": 3.0}
    EA._fred = fred
    restore = _fake_http(lambda u, kw: ciss)
    try:
        d = asyncio.run(EA.refresh(force=True))
        assert "y_DE" not in d["ts_each"] and len(d["ciss"]) == 1200
        d["ts_each"] = {k: v - 86400 for k, v in d["ts_each"].items()}
        EA.FILE.write_text(json.dumps(d), encoding="utf-8")
        d2 = asyncio.run(EA.refresh())
        assert d2["ts"] < time.time() - 3600 or not d2["ts_each"].get("y_DE"), "DE never fetched → bundle not renewed by it"
    finally:
        EA._fred = old
        restore()
    print("  euro/asia per-series ok")


# 12) dividend-sized re-basis (0.5%) is applied; non-uniform noise is not
def t_market_rebase():
    from wsb.data import market as MK
    idx = pd.bdate_range(end="2026-10-30", periods=40)
    m = MK.MarketData.__new__(MK.MarketData)
    m.history = pd.DataFrame({"AAA": np.full(38, 100.0)}, index=idx[:38])
    recent = pd.DataFrame({"AAA": np.full(7, 99.5)}, index=idx[-7:])
    assert abs(m._merge(recent)["AAA"].iloc[0] - 99.5) < 1e-9, "0.5% dividend adjustment re-based"
    noisy = pd.DataFrame({"AAA": [99.5, 100.3, 99.9, 100.0, 100.0, 100.0, 100.0]}, index=idx[-7:])
    assert m._merge(noisy)["AAA"].iloc[0] == 100.0, "ratios disagree → no re-base"
    print("  market re-base threshold ok")


# 13) Treasury upcoming list comes from /securities/upcoming
def t_treasury_upcoming():
    from wsb.data import treasury as TR
    soon = (date.today() + timedelta(days=3)).isoformat()
    done = [{"securityType": "Note", "originalSecurityTerm": "10-Year", "securityTerm": "10-Year", "auctionDate": f"2026-10-{d:02d}T00:00:00",
             "competitiveAccepted": "40000000000", "bidToCoverRatio": "2.5", "highYield": "4.1", "primaryDealerAccepted": "4000000000",
             "indirectBidderAccepted": "28000000000", "directBidderAccepted": "8000000000", "offeringAmount": "42000000000",
             "cusip": f"C{d}"} for d in (6, 7, 8, 9)]
    up = [{"securityType": "Note", "securityTerm": "10-Year", "competitiveAuctionCloseDate": soon + "T00:00:00"},
          {"securityType": "Bill", "securityTerm": "4-Week", "auctionDate": soon}]
    restore = _fake_http(lambda u, kw: up if u == TR.UPCOMING_URL else done)
    try:
        t = TR.Treasury()
        asyncio.run(t.refresh(force=True))
        assert t.upcoming == [soon] and t.auctions, t.upcoming
    finally:
        restore()
    print("  treasury upcoming source ok")


# 15) bank screen: no AOCI and no HTM figure → the securities-loss test is skipped (equity test still runs)
def t_distress_bank():
    from wsb.data import distress_data as DD
    names = {1: ("BK", "Bank"), 2: ("BK2", "Bank 2")}
    fr = {"assets": {1: 50e9, 2: 50e9}, "equity": {1: 5e9, 2: 2e9}, "deposits": {1: 40e9, 2: 40e9},
          "aoci": {}, "htm_loss": {}}
    out = DD.screen_candidates(fr, names)
    assert [r.get("sym") or r.get("ticker") for r in out] == ["BK2"] or len(out) == 1, out
    assert all("證券評價損失" not in str(r) for r in out)
    print("  distress missing AOCI/HTM ok")


# 16) TW P/E: a month saved with the TWSE half only is marked partial and its TPEx half is retried
def t_valhist_partial():
    from wsb.data import valhist as VH
    tw = {"stat": "OK", "fields": ["證券代號", "本益比", "股價淨值比", "殖利率(%)"], "data": [["2330", "20", "5", "1.5"]]}
    tp = {"tables": [{"fields": ["股票代號", "本益比", "股價淨值比", "殖利率(%)"], "data": [["6488", "30", "4", "1.0"]]}]}
    tpex_up = {"v": False}

    def route(u, kw):
        if "tpex" in u:
            return tp if tpex_up["v"] else RuntimeError("tpex down")
        return tw
    restore = _fake_http(route)
    old = VH.asyncio
    VH.asyncio = types.SimpleNamespace(sleep=_nosleep)
    try:
        today = date(2026, 11, 4)
        asyncio.run(VH.refresh_tw(budget_s=60, today=today))
        d = VH.load("tw")
        assert d["partial"] and all("6488" not in d["snaps"][k] for k in d["partial"])
        assert d.get("latest_day") != today.isoformat(), "TWSE-only latest is fetched again"
        assert all("_partial" not in r for r in d["snaps"].values())
        tpex_up["v"] = True
        asyncio.run(VH.refresh_tw(budget_s=60, today=today))
        d = VH.load("tw")
        assert d["partial"] == [] and all("6488" in r for r in d["snaps"].values())
        assert d.get("latest_day") == today.isoformat()
    finally:
        restore()
        VH.asyncio = old
    print("  valhist partial TPEx retry ok")


# 17) econ clock: verified offset carried forward; one anchor needs ForexFactory to agree
def t_econ_clock():
    from wsb.data import econcal as EC
    EC._CLOCK = {}
    EC._FF_UTC.clear()
    us = lambda n, t: {"country": "United States", "eventName": n, "gmt": t, "actual": "", "consensus": "", "previous": ""}  # noqa: E731
    js = lambda *r: {"data": {"rows": list(r)}}  # noqa: E731
    # 2026-11-05: two anchors at 08:30 → Nasdaq on EST (UTC−5), recorded
    EC.parse_nasdaq(js(us("Initial Jobless Claims", "08:30"), us("PPI", "08:30")), date(2026, 11, 5))
    assert EC._clock()["2026-11-05"] == -300
    # a later day without anchors keeps EST instead of snapping back to UTC−4
    r = EC.parse_nasdaq(js(us("Fed Speech", "14:00")), date(2026, 11, 9))
    assert r[0]["utc"] == "2026-11-09T19:00:00Z"
    # one anchor that disagrees with the carried clock is not enough to shift the day…
    r = EC.parse_nasdaq(js(us("CPI", "09:30"), us("X", "12:00")), date(2026, 11, 10))
    assert r[1]["utc"] == "2026-11-10T17:00:00Z" and "2026-11-10" not in EC._clock()
    # …unless ForexFactory's time for the same release agrees
    EC._FF_UTC[("cpi", "2026-11-10")] = "2026-11-10T13:30:00Z"
    r = EC.parse_nasdaq(js(us("CPI", "09:30"), us("X", "12:00")), date(2026, 11, 10))
    assert r[0]["utc"] == "2026-11-10T13:30:00Z" and EC._clock()["2026-11-10"] == -240
    ff = EC.parse_ff([{"country": "USD", "title": "CPI m/m", "date": "2026-11-12T08:30:00-05:00"}])
    assert ff[0]["utc"] == "2026-11-12T13:30:00Z"
    EC._CLOCK = None
    EC._FF_UTC.clear()
    print("  econ clock carry-forward / anchors ok")


def main():
    for k, f in list(globals().items()):
        if k.startswith("t_") and callable(f):
            f()
    print("DATA FIXES PASSED")


if __name__ == "__main__":
    main()
