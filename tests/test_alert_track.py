"""Site alert record for the scorecard on the Actions-built site: sanitizing, logging first-seen red alerts, seed + site merge.
Run: python -m tests.test_alert_track"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types

os.environ["WSB_DATA_DIR"] = tempfile.mkdtemp(prefix="wsb_atr_")          # fresh store: no bot log, like Actions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from tools import site_track as T  # noqa: E402


def test_sanitize():
    rows = [(1.0, "sigma:4119.TW:2026-11-06:-1", "risk", "⚠️ WARNING", "異常波動：4119.TW", 7000.0, 50.0),
            (2.0, "canary:ccc_bb:2026-11-06", "risk", "🚨 CRITICAL", "金絲雀", 7001.0, 51.0)]
    s = T.sanitize(rows)
    assert s == [[1, "sigma:", "risk", "⚠️", 7000.0], [2, "canary:", "risk", "🚨", 7001.0]]
    assert "4119" not in json.dumps(s, ensure_ascii=False)


def test_log_and_merge():
    spx = pd.Series([7000.0, 7010.0], index=pd.to_datetime(["2026-11-05", "2026-11-06"]))
    eng = types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: spx),
                                web_alerts={"items": [{"key": "ssi:2:2026W45", "lv": "alert", "tone": "risk"},
                                                      {"key": "rally:us:x:1", "lv": "watch", "tone": "good"}]})
    assert T.log_site_alerts(eng, now=2_000_000_000) == 1
    assert T.log_site_alerts(eng, now=2_000_000_100) == 0                    # same key only once
    rows, src = T._alert_rows()
    assert src == "site"
    assert any(r[1] == "ssi:2:2026W45" and r[5] == 7010.0 for r in rows)


if __name__ == "__main__":
    test_sanitize()
    test_log_and_merge()
    print("ALERT TRACK TESTS PASSED [OK]")
