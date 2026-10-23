"""危機預警成績單: crisis detection from 52-week highs, lead times, false alarms, conditional odds, site card.
Run: python -m tests.test_crisis_track"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ct_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import crisis_track as CT  # noqa: E402


class Mkt:
    def __init__(self, s):
        self.s = s

    def series(self, t):
        return self.s if t == "^GSPC" else pd.Series(dtype=float)


def fixture():
    idx = pd.bdate_range("2000-01-03", periods=4000)
    px = np.full(len(idx), 100.0)
    ssi = np.full(len(idx), 40.0)
    # crisis A at 1000: SSI warns 30 days before the -10% day; crisis B at 2500: no warning; false alarm at 3200
    for st, warn in ((1000, True), (2500, False)):
        px[st:st + 40] = np.linspace(100, 75, 40)
        px[st + 40:st + 120] = np.linspace(75, 100, 80)
        if warn:
            ssi[st - 10:st + 40] = 60.0
    ssi[3200:3210] = 60.0
    s = pd.Series(px, index=idx)
    return types.SimpleNamespace(market=Mkt(s), stress=types.SimpleNamespace(history=pd.Series(ssi, index=idx)))


def main():
    e = fixture()
    cs = CT.crises(e.market.series("^GSPC"), 15, 5)
    assert len(cs) == 2 and all(-26 < c["dd"] < -24 for c in cs), cs
    r = CT.build(e)
    sc = [x for x in r["rows"] if x["scored"]]
    assert len(sc) == 2
    a, b = sc
    assert a["lead"][55] is not None and a["lead"][55] >= 10 and b["lead"][55] is None, (a, b)
    s = r["summary"][55]
    assert s["hit"] == 1 and s["early"] == 1 and s["ups"] == 2 and s["false"] == 1, s
    assert r["odds"][10]["base"] > 0 and r["band"] == 0                       # SSI 40 today → any-day band
    from tools import site_crisis_track as SCT
    h = SCT.sec_crisis_track(e)
    assert "危機預警成績單" in h and "沒先亮" in h and "假警報" in h and "不是預測" in h
    print("all crisis track tests passed")


if __name__ == "__main__":
    main()
