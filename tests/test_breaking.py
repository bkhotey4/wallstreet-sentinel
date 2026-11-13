"""緊急加班車: the σ rule, quiet windows around the scheduled editions, the 12-hour cooldown.
Run: python -m tests.test_breaking"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import datetime, timezone

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_brk_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.analytics import breaking as BR  # noqa: E402

NOW = datetime(2026, 11, 9, 14, 0, tzinfo=timezone.utc)        # 22:00 台北: not a quiet window


def eng(sig):
    q = {t: {"chg_pct": (-1 if s < 0 else 1) * abs(s) * 0.8, "asof": "2026-11-09", "price": 1, "prev": 1} for t, s in sig.items()}
    m = types.SimpleNamespace(sigma_move=lambda t: sig.get(t), q=lambda t: q.get(t))
    return types.SimpleNamespace(market=m)


def test_rule():
    assert BR.hits(eng({"^GSPC": 3.9}), NOW) == []
    d = BR.decide(BR.hits(eng({"^GSPC": -4.2}), NOW), {}, NOW)
    assert not d["fire"] and d["why"] == "沒有達到條件"                    # one asset at 4σ is not enough
    d = BR.decide(BR.hits(eng({"^GSPC": -4.2, "^VIX": 4.5}), NOW), {}, NOW)
    assert d["fire"] and d["key"] == "brk:2026-11-09:^GSPC,^VIX"
    d = BR.decide(BR.hits(eng({"BZ=F": 5.3}), NOW), {}, NOW)
    assert d["fire"] and d["hits"][0]["t"] == "BZ=F"


def test_guards():
    hs = BR.hits(eng({"^GSPC": -6.0}), NOW)
    quiet = datetime(2026, 11, 9, 11, 40, tzinfo=timezone.utc)      # 19:40 台北: the evening edition is about to run
    assert not BR.decide(hs, {}, quiet)["fire"]
    assert not BR.decide(hs, {"last_ts": NOW.timestamp() - 3600}, NOW)["fire"]
    assert BR.decide(hs, {"last_ts": NOW.timestamp() - 7 * 3600}, NOW)["fire"]                # 6-hour cooldown
    assert ("19:30", "20:00") in BR.QUIET and ("03:00", "03:30") in BR.QUIET and len(BR.QUIET) == 8
    assert BR.decide(hs, {}, datetime(2026, 11, 9, 11, 0, tzinfo=timezone.utc))["fire"]        # 19:00: 30 min rule, not an hour
    d = BR.build(eng({"^GSPC": -6.0}), NOW)
    assert d["fire"] and not BR.build(eng({"^GSPC": -6.0}), NOW)["fire"]   # state saved → cooldown


def test_events():
    """有事才加班: a red sector, two yellow sectors, or a serious SEC filing in the last 3 hours."""
    import json
    import numpy as np
    import pandas as pd
    from wsb.data import sec_officers as SOF
    idx = pd.bdate_range("2025-09-01", periods=300)
    rng = np.random.default_rng(1)
    hist = pd.DataFrame({s: 100 * np.cumprod(1 + rng.normal(0, 0.012, 300)) for s in ("^SOX", "XLK", "XLF")}, index=idx)
    def mk(q):
        m = types.SimpleNamespace(sigma_move=lambda t: None, q=lambda t: q.get(t), history=hist)
        return types.SimpleNamespace(market=m)
    day = "2026-11-09"
    one_yellow = mk({"^SOX": {"chg_pct": -3.0, "asof": day}})
    assert BR.events(one_yellow, NOW) == []                                         # one yellow sector alone: no extra edition
    two = BR.events(mk({"^SOX": {"chg_pct": -3.0, "asof": day}, "XLK": {"chg_pct": -2.9, "asof": day}}), NOW)
    assert [e["kind"] for e in two] == ["sector", "sector"] and "族群急跌" in two[0]["text"]
    red = BR.events(mk({"^SOX": {"chg_pct": -5.0, "asof": day}}), NOW)
    assert len(red) == 1 and red[0]["key"] == "sec:^SOX"
    assert BR.events(mk({"^SOX": {"chg_pct": -5.0, "asof": "2026-11-01"}}), NOW) == []   # stale quote
    SOF.FILE.write_text(json.dumps({"alerts": [
        {"acc": "a", "ts": NOW.timestamp() - 3600, "item": "5.02", "t": "SEC 申報：輝達（NVDA）執行長離職（8-K 第 5.02 項）", "url": "u"},
        {"acc": "b", "ts": NOW.timestamp() - 3600, "item": "5.02", "t": "SEC 申報：邁威爾（MRVL）董事任命（8-K 第 5.02 項）"},
        {"acc": "c", "ts": NOW.timestamp() - 5 * 3600, "item": "4.02", "t": "SEC 申報：X 財報須重編"}]}), encoding="utf-8")
    ev = BR.events(one_yellow, NOW)
    assert [e["key"] for e in ev] == ["8k:a"]                                       # director appointment and 5 h old: no
    d = BR.decide([], {}, NOW, ev)
    assert d["fire"] and d["key"].endswith(":8k:a") and d["reasons"][0]["text"].startswith("SEC 申報：輝達")
    assert not BR.decide([], {"last_ts": NOW.timestamp() - 3600}, NOW, ev)["fire"]        # same 12-hour cooldown
    SOF.FILE.unlink()


if __name__ == "__main__":
    test_rule()
    test_guards()
    test_events()
    print("BREAKING TESTS PASSED [OK]")
