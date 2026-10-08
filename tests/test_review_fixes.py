"""Regression tests for the 2026-10-08 deep review.  Run: python -m tests.test_review_fixes"""
from __future__ import annotations

import asyncio
import os
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_review_"))

import tests.test_intel as TI  # noqa: E402
import tests.test_offline as T  # noqa: E402
from wsb.analytics import hedge as HG, portfolio as PF, regime as RG, shock as SK, watch as W  # noqa: E402
from wsb.analytics.stress import StressEngine  # noqa: E402


def main():
    st = StressEngine(T.m, T.fr).compute()
    rg = RG.classify(T.m, T.fr)
    pf = PF.analyze(T.m, {"NVDA": {"shares": 15, "cost": 50, "currency": "USD", "name": "NVDA"},
                          "TSM": {"shares": 12, "cost": 60, "currency": "USD", "name": "TSM"}})
    eng = TI.T_engine(st, rg, SK.build(st, T.m.series("^GSPC")), [])
    eng.portfolio = pf

    # 1) public replies never carry the owner's holdings
    from wsb.ai import context
    priv, pub = context.build(eng, "us"), context.build(eng, "us", private=False)
    assert "## 使用者持倉" in priv and "## 使用者持倉" not in pub and "公開模式" in pub
    assert "NVDA 權重" in priv and "NVDA 權重" not in pub

    # 2) de-risk / concentration share counts use the USD price (a TWD price made .TW trims ~32x too small)
    tw = {"total_value_usd": 100000.0, "beta": 1.2, "positions": [
        {"sym": "2330.TW", "shares": 1000, "price": 1000.0, "value_usd": 31250.0, "beta": 1.2, "weight": 31.25,
         "risk_contrib_pct": 40.0}]}                                   # NT$1,000 at 32 TWD/USD → $31.25 per share
    trim = HG.analyze(tw, {}, 50, cut_frac=0.1)["derisk"][0]
    assert abs(trim["shares"] - trim["sell_usd"] / 31.25) < 1.0, trim
    br = [b for b in W.concentration(tw)["breaches"] if b["name"] == "2330.TW"][0]["text"]
    x = (31250 - 0.25 * 100000) / 0.75
    assert f"（{-(-x // 31.25):.0f} 股）" in br, br

    # 3) scheduled jobs: an AI outage is retried, the last try delivers, success marks done
    from wsb.bot import app as APP
    bot = types.SimpleNamespace(_sending=set(), _job_attempts={})
    run_job = APP.Sentinel._run_job.__get__(bot)
    delivered, marks = [], []
    APP.store.kv_set = lambda k, v: marks.append(k)

    async def job():
        APP.Sentinel._ai_gate("none")              # AI down
        delivered.append(1)

    async def scenario():
        await run_job("brief:x", job())            # try 1 → AIUnavailable, nothing delivered / marked
        assert not delivered and not marks
        await run_job("brief:x", job())            # too soon → skipped (coroutine closed, no warning)
        assert bot._job_attempts["brief:x"][0] == 1
        for i in range(2, APP.JOB_MAX_TRIES + 1):
            bot._job_attempts["brief:x"] = (i - 1, 0.0)  # pretend the retry interval passed
            await run_job("brief:x", job())
        assert delivered == [1] and marks == ["brief:x"], (delivered, marks)
        assert APP.JOB_FINAL.get() is True         # context restored for interactive commands
    asyncio.run(scenario())

    # 4) Treasury reopenings are recognised by their ORIGINAL term
    from wsb.data import liquidity as LQ
    import inspect
    assert "originalSecurityTerm" in inspect.getsource(LQ)

    # 5) US-dated events use the New York date
    from wsb.data import calendar as CAL
    from datetime import datetime
    from zoneinfo import ZoneInfo
    assert CAL.us_today() == datetime.now(ZoneInfo("America/New_York")).date()
    print("REVIEW FIX TESTS PASSED ✅")


if __name__ == "__main__":
    main()
