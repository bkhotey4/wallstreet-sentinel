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

NOW = datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc)        # 23:00 台北: not a quiet window


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
    quiet = datetime(2026, 11, 9, 11, 30, tzinfo=timezone.utc)      # 19:30 台北: the evening edition is about to run
    assert not BR.decide(hs, {}, quiet)["fire"]
    assert not BR.decide(hs, {"last_ts": NOW.timestamp() - 3600}, NOW)["fire"]
    assert BR.decide(hs, {"last_ts": NOW.timestamp() - 13 * 3600}, NOW)["fire"]
    d = BR.build(eng({"^GSPC": -6.0}), NOW)
    assert d["fire"] and not BR.build(eng({"^GSPC": -6.0}), NOW)["fire"]   # state saved → cooldown


if __name__ == "__main__":
    test_rule()
    test_guards()
    print("BREAKING TESTS PASSED [OK]")
