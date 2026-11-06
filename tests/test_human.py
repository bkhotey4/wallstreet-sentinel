"""人類溫度計 and 美股時段快報 cards.  Run: python -m tests.test_human"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點")


def monthly(end_yoy: float, n: int = 60, start: float = 100.0) -> pd.Series:
    idx = pd.date_range("2022-01-01", periods=n, freq="MS")
    return pd.Series(start * (1 + end_yoy / 100) ** (np.arange(n) / 12), index=idx)


def fake(data):
    return types.SimpleNamespace(fred=types.SimpleNamespace(get=lambda sid: data.get(sid, pd.Series(dtype=float))))


def test_human():
    from tools import site_human as H
    s = monthly(10)
    assert abs(H.yoy(s) - 10) < 1e-6
    assert H.tone(10, 8, True) == "變差" and H.tone(10, 8, False) == "改善" and H.tone(10, 10.05, True) == "持平" and H.tone(1, None, True) == "—"
    data = {"AHETPI": monthly(4), "CUSR0000SEHF01": monthly(8), "CUSR0000SEHA": monthly(2), "DRCCLACBS": monthly(5),
            "UMCSENT": monthly(-5), "USEPUINDXD": pd.Series(np.linspace(100, 200, 400), index=pd.date_range("2025-01-01", periods=400)),
            "QCNR628BIS": monthly(-3)}
    h = H.sec_human(fake(data))
    assert "1／2 項生活開銷漲得比工資快" in h and "2 項指標中，2 項比一年前差" in h, h[:300]
    assert "電費" in h and "+8.0%" in h and "信用卡逾期率" in h and "政策不確定性" in h and "中國實質房價" in h
    assert "汽油" not in h and "工作與下一代" not in h                     # a missing series leaves no empty row or heading
    assert "不是預測" in h and not any(w in h for w in BANNED)
    assert H.sec_human(fake({})) == ""


def render(d):
    from tools import site_sessions as S
    f = Path(tempfile.mkdtemp()) / "sessions.json"
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with patch.object(S, "FILE", f):
        return S.sec_sessions(None)


def test_sessions():
    d = {"items": [{"date": "2026-11-05", "phase": "盤後", "one": "昨天的事"},
                   {"date": "2026-11-06", "phase": "盤前", "at": "21:00", "one": "開盤前<b>緊張</b>"},
                   {"date": "2026-11-06", "phase": "盤中", "at": "01:00", "one": "盤中反彈", "story": ["大家鬆一口氣"],
                    "macro": [{"name": "利率", "read": "10 年債小升"}, {"name": "沒寫"}], "next": "收盤",
                    "sources": [{"name": "BBC", "url": "https://example.com/a"}, {"name": "壞", "url": "javascript:x"}]},
                   {"date": "2026-11-06", "phase": "奇怪", "one": "不該出現"}]}
    h = render(d)
    assert "一句話看懂：盤中反彈" in h and h.index("盤中反彈") < h.index("緊張") and "昨天的事" not in h and "不該出現" not in h
    assert "總經情勢" in h and "10 年債小升" in h and "沒寫" not in h and "&lt;b&gt;緊張" in h and 'href="javascript' not in h
    assert render({}) == ""


if __name__ == "__main__":
    test_human()
    test_sessions()
    print("HUMAN TESTS PASSED")
