"""即時事件與資料品質: quote freshness by market calendar, official event parsers, independent-outlet news scoring,
the event inbox, cross-country yield alignment and the rates-vs-credit split.
Run: python -m tests.test_realtime"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_rt_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_freshness():
    from wsb.data import freshness as F
    tue_pre = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)        # 08:00 New York, before the open
    assert F.expected_bar("AAPL", tue_pre) == "2026-10-26" and not F.stale("AAPL", "2026-10-26", tue_pre)
    tue_mid = datetime(2026, 10, 27, 15, 0, tzinfo=timezone.utc)        # 11:00 New York
    assert F.stale("AAPL", "2026-10-26", tue_mid) and F.session("AAPL", tue_mid) == "regular"
    sun = datetime(2026, 10, 25, 15, 0, tzinfo=timezone.utc)
    assert F.expected_bar("^GSPC", sun) == "2026-10-23" and F.session("^GSPC", sun) == "closed"     # weekend → Friday
    assert F.market_of("2330.TW") == "tw" and F.market_of("BTC-USD") == "crypto" and F.market_of("JPY=X") == "fx"
    assert F.expected_bar("BTC-USD", sun) == "2026-10-25"                                           # crypto trades weekends
    assert F.expected_bar("2330.TW", tue_mid) == "2026-10-27"                                       # 23:00 Taipei


def test_halts_fed_mops():
    from wsb.data import events as EV
    xml = b"""<?xml version="1.0"?><rss version="2.0" xmlns:ndaq="http://www.nasdaqtrader.com/"><channel><title>x</title>
    <item><title>NVDA</title><ndaq:HaltDate>10/26/2026</ndaq:HaltDate><ndaq:HaltTime>10:05:00.000</ndaq:HaltTime>
    <ndaq:IssueSymbol>NVDA</ndaq:IssueSymbol><ndaq:IssueName>NVIDIA Corp</ndaq:IssueName><ndaq:Market>NASDAQ</ndaq:Market>
    <ndaq:ReasonCode>T1</ndaq:ReasonCode><ndaq:ResumptionTradeTime /></item></channel></rss>"""
    h = EV.parse_halts(xml)
    assert len(h) == 1 and h[0]["sym"] == "NVDA" and h[0]["code"] == "T1" and h[0]["reason"] == "重大消息待公布"
    assert datetime.fromtimestamp(h[0]["ts"], timezone.utc).hour == 14            # 10:05 New York (EDT) = 14:05 UTC
    rows = [{"出表日期": "1151027", "發言日期": "1151026", "發言時間": "70004", "公司代號": "2330", "公司名稱": "台積電",
             "主旨 ": "公告董事會決議", "符合條款": "第11款"},
            {"Date": "1151026", "發言日期": "1151025", "發言時間": "191051", "SecuritiesCompanyCode": "3680", "CompanyName": "家登",
             "主旨": "調整配息", "符合條款": "第14款"}, {"公司代號": "", "發言日期": ""}]
    m = EV.parse_mops(rows[:1], "上市") + EV.parse_mops(rows[1:], "上櫃")
    assert [x["code"] for x in m] == ["2330", "3680"] and m[0]["subject"] == "公告董事會決議"     # trailing-space key read
    assert m[0]["when"] == "2026-10-26 07:00" and m[1]["when"] == "2026-10-25 19:10"


def test_news_independent_outlets():
    from wsb.data import news as N
    assert N.publisher("GNews 風險", "Bank run fears grow - Reuters") == "reuters"
    assert N.publisher("CNBC Finance", "x") == N.publisher("CNBC", "y") == "cnbc"          # one house, two feeds
    it = N.NewsItem("CNBC", "t", "", 0)
    assert it.outlets == 1


def test_inbox_and_event_log():
    from wsb import store
    from wsb.bot import embeds as E
    store.event_seen("sec:u1", "SEC 公告", "SEC：AAPL 8-K", 1_000.0)
    store.event_seen("halt_pf:XYZ:1", "停牌", "停牌：XYZ", None)
    store.event_result(["sec:u1"], True)
    store.event_result(["halt_pf:XYZ:1"], False, "no reachable target")
    rows = store.event_rows(24)
    pub = E.inbox(rows, private=False)
    txt = " ".join(f.value for f in pub.fields)
    assert "SEC 公告" in txt and "XYZ" not in txt                       # holdings-derived halt never in a public channel
    dm = " ".join(f.value for f in E.inbox(rows, private=True).fields)
    assert "XYZ" in dm and "待送" in " ".join(f.name for f in E.inbox(rows, private=True).fields)


def test_yield_gap_alignment():
    import pandas as pd
    from wsb.analytics import bonds as B
    us = pd.Series(4.0, index=pd.bdate_range("2026-07-01", "2026-10-26"))
    de = pd.Series([2.5, 2.6, 2.7], index=pd.to_datetime(["2026-07-01", "2026-08-01", "2026-09-01"]))
    v, m = B._gap(de, {"daily": False, "date": "2026-09-01", "now": 2.7}, us, {"daily": True, "date": "2026-10-26", "now": 4.0})
    assert m == "2026-09" and abs(v - (2.7 - 4.0)) < 1e-9                  # compared on September, not Oct vs Sep
    v, m = B._gap(us, {"daily": True, "date": "2026-10-26", "now": 4.0}, us, {"daily": True, "date": "2026-10-23", "now": 3.9})
    assert m is None and abs(v - 0.1) < 1e-9


def test_credit_unknown_not_calm():
    from tools import site_credit as SC
    assert "缺資料不代表平靜" in open(SC.__file__, encoding="utf-8").read()
    import inspect
    from wsb.analytics import credit_rates as CR
    src = inspect.getsource(CR.build)
    assert '"unknown" if lo_q is None or hi_q is None' in src and ".where(dd13.notna())" in src


def test_missing_is_not_calm():
    from tools import site_dual as SD
    assert "正在升溫" in SD.combo(1, 1, 0, 7)                         # one gauge alone can still read warm
    assert "資料暫缺" in SD.combo(0, 0, 0, 7) and "資料暫缺" in SD.combo(0, 4, 0, 0)
    from wsb.analytics import intel as I
    heat = {"景氣衰退": {"level": 10.0, "news_state": "冷", "n": 0, "top": [], "n_relief": 0, "easing": False, "warmup": False}}
    assert I.fuse(heat, {"paths": []}, None)[0]["state"] == "資料缺"   # no price path → unknown, not calm
    from tools import site_live as SL
    assert "資料不足，暫時無法判斷" in SL.JS and "層有資料" in SL.JS


def test_small_fixes():
    from datetime import date
    from wsb.analytics import canary as C
    r = {"id": "dash_for_cash", "kind": "rule", "state": "ok", "asof": "2026-10-01"}
    C._age_check(r, today=date(2026, 10, 27))
    assert r["state"] == "stale" and "2026-10-01" in r["note"]                 # old data cannot say "ok"
    r = {"id": "margin_debt", "kind": "rule", "state": "ok", "asof": "2026-09"}
    C._age_check(r, today=date(2026, 10, 27))
    assert r["state"] == "ok"                                                  # monthly series, normal lag
    from wsb.data import fundamentals as FU
    assert not FU.evaluable({}) and FU.evaluable({"capex_ocf": 0.5, "int_burden": 5, "debt_growth": 2})
    from wsb.analytics import sector_brief as SB
    cache = {f"S{i}": {"p": {"x": 1}, "m": {"rev_growth": 3.0}} for i in range(5)}
    fd = SB.fund_block(list(cache), cache)
    assert fd["n"] == 5 and fd["strain_pct"] is None                           # no data is not "0% strain"
    assert any("暫不判斷" in x for x in SB.risk_text(fd, {}, None))
    import time
    from wsb import store
    from wsb.bot import embeds as E
    store.event_seen("news:old1", "新聞", "舊新聞", None)
    with store._LOCK:
        store._C.execute("UPDATE event_log SET last_ts=? WHERE key='news:old1'", (time.time() - 7200,))
        store._C.commit()
    em = E.inbox(store.event_rows(24), private=True)
    assert any(f.name.startswith("過期未送") and "舊新聞" in f.value for f in em.fields)


def test_extended_gaps():
    import pandas as pd
    from wsb.data import extended as XT
    meta = {"regularMarketPrice": 100.0, "currentTradingPeriod": {"regular": {"start": 1000, "end": 2000}}}
    e = XT.parse({"meta": meta, "timestamp": [500, 900], "indicators": {"quote": [{"close": [99.0, 94.0]}]}})
    assert e["sess"] == "pre" and abs(e["chg"] + 6) < 1e-9
    assert XT.parse({"meta": meta, "timestamp": [1500], "indicators": {"quote": [{"close": [99.0]}]}}) is None
    assert XT.us_ext_session(datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)) == "pre"      # 08:00 New York
    assert XT.us_ext_session(datetime(2026, 10, 27, 16, 0, tzinfo=timezone.utc)) is None       # regular session
    assert XT.us_ext_session(datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)) is None       # Sunday
    from wsb.bot.app import Sentinel
    idx = pd.bdate_range("2025-09-01", periods=300)
    s = pd.Series([100 * (1.01 if i % 2 else 0.99) ** (i % 7) for i in range(300)], index=idx)

    class M:
        def series(self, t):
            return s

    class Eng:
        market = M()

        def holding_tickers(self):
            return ["NVDA", "2330.TW"]
    b = Sentinel.__new__(Sentinel)
    b.engine = Eng()
    assert "2330.TW" not in b._ext_symbols() and "NVDA" in b._ext_symbols()
    sd = float(s.pct_change().dropna().iloc[-252:].std() * 100)
    al = b._ext_gap_alerts({"NVDA": {"px": 90, "chg": -3.5 * sd, "sess": "pre", "t": 1793106535, "base": 100},
                            "SPY": {"px": 100, "chg": 0.5 * sd, "sess": "pre", "t": 1793106535, "base": 100}})
    assert len(al) == 1 and al[0].key.startswith("gap_pf:NVDA:") and al[0].key.endswith(":3")
    from wsb import store
    assert store.is_private_alert(al[0].key)                            # holdings gap → owner DM only
    from tools import site_extgap as X
    assert "盤前／盤後跳空" in X.sec_ext_gaps(None) and "ext=" in X.JS


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
