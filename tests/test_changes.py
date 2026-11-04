"""今天 vs 昨天 card: waits honestly for two sessions, lists a light / band change whatever its size, lists a number only past
its own 1σ daily change, leaves unchanged items out, keeps one row per session, and scales σ when a session was missed.
Run: python -m tests.test_changes"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from pathlib import Path

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_chg_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from tools import site_changes as C  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")


def _s(step: float, last: float, days: int = 300, end: str = "2026-11-04") -> pd.Series:
    """A series whose daily change has a known size (alternating ± step), ending on `last`."""
    x = last + np.where(np.arange(days) % 2 == 0, step, 0.0)
    x[-1] = last
    return pd.Series(x, index=pd.bdate_range(end=end, periods=days))


class Mkt:
    def __init__(self, data, asof):
        self.data, self.asof = data, asof

    def series(self, t):
        return self.data.get(t, pd.Series(dtype=float))

    def q(self, t):
        s = self.data.get(t)
        return {"price": float(s.iloc[-1]), "asof": self.asof} if s is not None and len(s) else None


class Fred:
    def __init__(self, data):
        self.data = data

    def get(self, sid):
        return self.data.get(sid, pd.Series(dtype=float))


def _eng(asof="2026-11-04", vix=20.0, hy=3.0, label="正常", score=40.0, light="ok", stage=1, crash=10.0, fred_end="2026-11-03"):
    mk = {"^VIX": _s(1.0, vix), "^GSPC": _s(10.0, 5000.0), "TWD=X": _s(0.1, 32.0)}
    fr = {"BAMLH0A0HYM2": _s(0.05, hy, end=fred_end)}
    ssi = _s(2.0, score)
    return types.SimpleNamespace(
        market=Mkt(mk, asof), fred=Fred(fr),
        stress=types.SimpleNamespace(score=score, label=label, history=ssi, live_history=None),
        odds={"horizons": [{"days": 21, "drawdown_pct": 5.0, "adjusted": crash}]}, lab={},
        canary={"rows": [{"id": "a", "zh": "測試燈", "en": "Test light", "why": "<b>原因</b>", "state": light}, {"id": "b", "zh": "累積燈", "en": "W", "state": "warmup"}]},
        playbook={"stage": stage, "name": f"階段{stage}"}, outlook={})


def _tmp():
    orig = C.FILE
    C.FILE = Path(tempfile.mkdtemp()) / "econ_daily_changes.json"
    return orig


def test_waits_for_two_snapshots():
    orig = _tmp()
    try:
        h = C.sec_changes(_eng())
        assert "資料累積中" in h and "已存 0 天" in h
        assert C.record(_eng())                                  # today's row alone is not a comparison
        h = C.sec_changes(_eng())
        assert "資料累積中" in h and "已存 1 天" in h
        none = _eng()
        none.market = Mkt({}, None)
        assert "資料累積中" in C.sec_changes(none) and C.record(none) is False
    finally:
        C.FILE = orig


def test_lists_only_what_changed():
    orig = _tmp()
    try:
        assert C.record(_eng(asof="2026-11-03", fred_end="2026-11-02"))
        # light changed, band changed, VIX +3 (> its 1σ ≈ 1), TWD and S&P unchanged, HY same FRED date → not a change
        now = _eng(asof="2026-11-04", vix=23.0, label="升溫", score=41.0, light="watch", stage=2, hy=3.5, fred_end="2026-11-02")
        h = C.sec_changes(now)
        assert "一句話看懂：今天有 4 項變了" in h, h[:300]
        assert "VIX 恐慌指數" in h.split("<details")[0] and "23.00" in h and "測試燈" in h and "階段2" in h
        assert "區間從「正常」變成「升溫」" in h
        head = h.split("<details")[0]
        assert "標普 500" not in head and "美元/台幣" not in head and "高收益債利差" not in head and "累積燈" not in head
        assert "沒變的項目" in h and "<details" in h and "<b>原因</b>" not in h          # escaped
        for w in BANNED:
            assert w not in h, w
        # a small SSI move inside its own band stays out, however large it looks in points
        quiet = C.sec_changes(_eng(asof="2026-11-04", score=41.0, fred_end="2026-11-02"))
        assert "今天沒有明顯變化" in quiet and "SSI 壓力指數" not in quiet.split("<details")[0]
    finally:
        C.FILE = orig


def test_new_fred_day_counts_and_sigma_scales():
    prev = C.readings(_eng(asof="2026-11-03", fred_end="2026-11-02"))
    cur = C.readings(_eng(asof="2026-11-04", hy=3.4, fred_end="2026-11-03"))
    keys = [i["key"] for i in C.compare(_eng(hy=3.4, fred_end="2026-11-03"), cur, prev, [])["items"]]
    assert "hy" in keys
    # a 1.2σ move is news after one session, not after nine
    p = C.readings(_eng(asof="2026-10-23"))
    c = C.readings(_eng(asof="2026-11-04", vix=21.2))
    r = C.compare(_eng(vix=21.2), c, p, [])
    assert r["gap"] == 8 and "vix" not in [i["key"] for i in r["items"]]


def test_crash_sigma_and_unjudged():
    e = _eng()
    e.lab = {"horizons": [{"days": 21, "base_model": {"w": [-2.0, 1.0], "cal": [[0.0, 1.0], [0.0, 1.0]]}}]}
    s = C.sigmas(e, [], ["crash_21", "outlook"])
    assert s["crash_21"] > 0 and "outlook" not in s
    # no model and no snapshots: reported as not judged, never as "changed"
    e.lab = {}
    r = C.compare(e, {"date": "2026-11-04", "v": {"crash_21": 30.0}, "s": {"crash_21": "5"}}, {"date": "2026-11-03", "v": {"crash_21": 10.0}, "s": {}}, [])
    assert not r["items"] and r["unknown"] and "崩跌機率" in r["unknown"][0]


def test_one_row_per_session_and_merge():
    orig = _tmp()
    try:
        C.record(_eng(asof="2026-11-03"))
        down = _eng(asof="2026-11-03")
        down.fred = Fred({})                                     # FRED failed on the later build: keep the earlier value
        C.record(down)
        rows = C.load()
        assert len(rows) == 1 and "hy" in rows[0]["v"]
        C.FILE.write_text("{broken", encoding="utf-8")
        assert C.load() == []
    finally:
        C.FILE = orig


def test_wired_in():
    src = (Path(C.__file__).parent / "build_site.py").read_text(encoding="utf-8")
    assert "SCG.sec_changes" in src and "SCG.record(eng)" in src
    from tools import site_stamp as STP
    assert "sec_changes" in STP.CARD


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
