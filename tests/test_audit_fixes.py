"""Regression tests for the 2026-10-10 robustness audit (offline).  Run: python -m tests.test_audit_fixes"""
from __future__ import annotations

import asyncio
import os
import tempfile
import time
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_audit_"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import tests.test_offline  # noqa: E402,F401  (stubs optional deps)


def t_fullmarket_splice():
    from wsb.data import fullmarket as FM
    idx = pd.bdate_range(end="2026-10-09", periods=60)
    old = pd.DataFrame({"A": np.linspace(100, 160, 60), "B": np.linspace(10, 20, 60)}, index=idx)
    old = old.iloc[:-5]                                     # stored history ends 5 sessions ago
    new_idx = idx[-25:]
    new = pd.DataFrame({"A": np.linspace(100, 160, 60)[-25:] * 0.5,          # 2:1 split since the last download
                        "B": np.linspace(10, 20, 60)[-25:]}, index=new_idx)
    out, dropped = FM._splice(old, new)
    assert not dropped
    assert abs(out["A"].iloc[0] - 50.0) < 1e-9, out["A"].iloc[0]           # older bars re-based by the split ratio
    assert abs(out["A"].iloc[-1] - 80.0) < 1e-9 and abs(out["B"].iloc[0] - 10.0) < 1e-9   # B untouched
    gap = pd.DataFrame({"A": [1.0, 2.0]}, index=pd.bdate_range(start="2026-12-01", periods=2))
    out2, dropped2 = FM._splice(old, gap)                   # no overlap → dropped for a full re-download
    assert dropped2 == ["A"] and "A" not in out2.columns
    from wsb.data import stocks as STK
    STK._download = lambda part, period: (pd.DataFrame(), pd.DataFrame())     # Yahoo throttling: every batch empty
    st = FM.refresh_prices("zz", [f"S{i:02d}" for i in range(30)], idx[-1], time.time() + 30)
    assert st["failed"] == 0 and st["pending"] == 30, st                       # nothing written off as "no data"
    print("  full-market split splice ok")


def t_market_merge():
    from wsb.data import market as MK
    idx = pd.bdate_range(end="2026-10-09", periods=40)
    m = MK.MarketData.__new__(MK.MarketData)
    m.history = pd.DataFrame({"AAA": np.full(38, 100.0), "^IDX": np.full(38, 100.0), "EUR=X": np.full(38, 1.0)}, index=idx[:38])
    recent = pd.DataFrame({"AAA": np.full(7, 50.0), "^IDX": np.full(7, 50.0), "EUR=X": np.full(7, 0.5)}, index=idx[-7:])
    h = m._merge(recent)
    assert h["AAA"].iloc[0] == 50.0, "equity re-based"
    assert h["^IDX"].iloc[0] == 100.0 and h["EUR=X"].iloc[0] == 1.0, "indices / FX never re-based"
    recent2 = pd.DataFrame({"AAA": np.full(7, 50.0)}, index=idx[32:39])   # 2 overlapping bars once the last one is left out
    m.history = pd.DataFrame({"AAA": np.full(35, 100.0)}, index=idx[:35])
    assert m._merge(recent2)["AAA"].iloc[0] == 100.0, "fewer than 3 overlapping bars → no re-base"
    # failed tickers are remembered and the full rebuild backs off after a failure
    m.hist_failed = {"OLD": time.time() - 8 * 86400, "NEW": time.time()}
    assert m.recently_failed() == {"NEW"}
    assert MK.is_rebaseable("AAPL") and not MK.is_rebaseable("BTC-USD") and not MK.is_rebaseable("^VIX")
    print("  market merge / rebuild backoff ok")


def t_signal_failed_stays_failed():
    from wsb.analytics import signals as SG
    idx = pd.bdate_range(end="2026-10-09", periods=30)
    close = np.full(30, 100.0)
    close[-1] = 101.0
    close[-2] = 94.0                                         # dipped under the give-up line after the trigger…
    df = pd.DataFrame({"flag": False, "inv": 95.0, "close": close, "atr": 2.0, "vol_ratio": 2.0, "rsi": 55.0,
                       "hi20": 99.0, "hi252": 130.0, "ma10": 99.0, "ma20": 98.0, "ma50": 95.0,
                       "ma200": 90.0, "touch50": False, "lo10": 94.0, "hi10": 100.0, "hi252p": 130.0}, index=idx)
    df.loc[idx[-3], "flag"] = True
    assert SG.evaluate({"breakout": df}, 60, SG.base_strengths()) == [], "…so it stays failed after the recovery"
    df["close"] = 100.0
    hits = SG.evaluate({"breakout": df}, 60, SG.base_strengths())
    assert hits and hits[0]["inv"] < hits[0]["plan"]["zone_lo"]
    df["inv"] = 99.5                                         # give-up line inside the zone → clamped under it
    hits = SG.evaluate({"breakout": df}, 60, SG.base_strengths())
    assert hits and hits[0]["inv"] < hits[0]["plan"]["zone_lo"], hits
    print("  signal failure / give-up clamp ok")


def t_site_helpers():
    from tools import build_site as B

    def boom(eng):
        raise RuntimeError("x")
    assert B._safe_section(boom, None) == "" and B._safe_section(lambda e: "<p>", None) == "<p>"
    today = pd.Timestamp.now(tz="America/New_York").date()
    fresh, old = today.isoformat(), (today - pd.Timedelta(days=9)).isoformat()
    q = {t: {"asof": fresh} for t, _, _ in B.STRIP}
    eng = types.SimpleNamespace(market=types.SimpleNamespace(q=lambda t: q.get(t)))
    assert B.data_asof(eng) == (fresh, False)
    q["HYG"] = {"asof": old}                                 # a stuck core US feed makes the page stale…
    assert B.data_asof(eng) == (fresh, True)                 # …while the header still shows the newest date
    print("  site section guard / staleness ok")


def t_insider_retry():
    from wsb.data import edgar_holdings as EH
    EH.us_universe = lambda: {"AAA": ("A", "A")}

    async def tmap():
        return {"AAA": {"cik": 1, "title": "A INC"}}
    EH.ticker_map = tmap
    calls = {"n": 0}

    async def fake_get(url, kind="json"):
        if "submissions" in url:
            return {"filings": {"recent": {"accessionNumber": ["0001-26-000001"], "form": ["4"],
                                           "filingDate": [pd.Timestamp.today().strftime("%Y-%m-%d")], "primaryDocument": ["x.xml"]}}}
        calls["n"] += 1
        raise RuntimeError("boom")
    EH._get = fake_get
    ins = EH.Insiders()
    ins.data = {"ts": 0, "forms": {}}
    for _ in range(4):
        asyncio.run(ins.refresh(force=True))
    f = ins.data["forms"]["0001-26-000001"]
    assert f["error"] and f["tries"] == 3 and calls["n"] == 3, (f, calls)   # retried, but at most 3 times

    class Throttled(Exception):
        status = 429

    async def throttled(url, kind="json"):
        if "submissions" in url:
            return await fake_get(url)
        calls["n"] += 1
        raise Throttled()
    EH._get = throttled
    ins.data = {"ts": 0, "forms": {}}
    asyncio.run(ins.refresh(force=True))
    assert "0001-26-000001" not in ins.data["forms"], "a 429 is not the filing's fault: no try is used up"
    print("  insider retry / throttle ok")


def main():
    t_fullmarket_splice()
    t_market_merge()
    t_signal_failed_stays_failed()
    t_site_helpers()
    t_insider_retry()
    print("AUDIT FIXES PASSED")


if __name__ == "__main__":
    main()
