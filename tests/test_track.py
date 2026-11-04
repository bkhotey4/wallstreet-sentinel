"""全站預測成績單 card: counts only below 20 cases, baselines and false alarms from stored records, misses shown, nothing from
holdings-derived alerts, and an honest empty state.  Run: python -m tests.test_track"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import types
from pathlib import Path

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_trk_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from tools import site_preview as SPV  # noqa: E402
from tools import site_track as K  # noqa: E402
from wsb.analytics import implied_log as IL  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")


def _pv(n_hit: int, n_miss: int, n_open: int = 1) -> dict:
    it = [{"sym": f"H{i}", "date": "2026-10-28", "probs": {"上修": 20, "維持": 60, "下修": 20}, "outcome": "維持"} for i in range(n_hit)]
    it += [{"sym": f"M{i}", "name": f"<i>公司{i}", "date": "2026-10-29", "probs": {"上修": 50, "維持": 30, "下修": 20}, "outcome": "維持"} for i in range(n_miss)]
    it += [{"sym": f"O{i}", "date": "2026-11-29", "probs": {"上修": 50, "維持": 30, "下修": 20}} for i in range(n_open)]
    return {"items": it}


def _files(pv=None, log=None):
    d = Path(tempfile.mkdtemp())
    SPV.FILE, IL.FILE = d / "p.json", d / "l.json"
    if pv is not None:
        SPV.FILE.write_text(json.dumps(pv, ensure_ascii=False), encoding="utf-8")
    if log is not None:
        IL.FILE.write_text(json.dumps(log, ensure_ascii=False), encoding="utf-8")


def _eng(lab=None, rules=None):
    return types.SimpleNamespace(lab=lab or {}, sx={"rules": rules} if rules else {}, market=types.SimpleNamespace(series=lambda t: pd.Series(dtype=float)))


def _cells(h: str, label: str) -> list:
    row = next(r for r in re.findall(r"<tr>.*?</tr>", h, re.S) if label in r)
    return re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)


def test_empty():
    a, b, c = SPV.FILE, IL.FILE, K._alert_rows
    try:
        _files()
        K._alert_rows = lambda: []
        h = K.sec_track_record(_eng())
        assert "目前還沒有可以對答案的紀錄" in h and "還沒有紀錄" in h and "%" not in _cells(h, "財報前瞻")[3]
        assert "這次更新讀不到警報紀錄" in h
        for w in BANNED:
            assert w not in h, w
    finally:
        SPV.FILE, IL.FILE, K._alert_rows = a, b, c


def test_small_sample_shows_no_rate():
    a, b, c = SPV.FILE, IL.FILE, K._alert_rows
    try:
        _files(_pv(3, 4))
        K._alert_rows = lambda: []
        h = K.sec_track_record(_eng())
        cs = _cells(h, "財報前瞻")
        assert cs[1] == "7" and cs[2] == "3" and "樣本太少" in cs[3] and "%" not in cs[3]
        assert "7/7" in cs[4] and "%" not in cs[4] and cs[5] == "4"                  # always-維持 got all 7; 4 false alarms
        assert "樣本都太少" in h and "沒猜中" in h and "公司0" in h and "<i>" not in h and "結果是「維持」" in h
    finally:
        SPV.FILE, IL.FILE, K._alert_rows = a, b, c


def test_enough_sample_beats_or_loses_baseline():
    a, b, c = SPV.FILE, IL.FILE, K._alert_rows
    try:
        _files(_pv(30, 10))                                                          # 30/40 vs always 維持 40/40
        K._alert_rows = lambda: []
        r = K.preview_row()
        assert r["v"] == "lose" and r["n"] == 40 and r["hits"] == 30 and r["base"] == 100 and r["false"] == 10
        h = K.sec_track_record(_eng())
        assert "75%" in _cells(h, "財報前瞻")[3] and "100%" in _cells(h, "財報前瞻")[4] and "輸給基準" in h
        # implied move: fair pricing ≈ 57% stay within
        log = {f"S{i}|2026-10-{i + 1:02d}": {"sym": f"S{i}", "date": f"2026-10-{i + 1:02d}", "mv": 5.0, "act": 1.0 if i % 10 else 9.0} for i in range(25)}
        _files(None, log)
        r = K.implied_row()
        assert r["n"] == 25 and r["hits"] == 22 and r["v"] == "win" and r["over"]
        assert K._verdict(11, 20, 50.0) == "tie" and K._verdict(0, 0, 50.0) == "none" and K._verdict(5, 19, 1.0) == "small"
    finally:
        SPV.FILE, IL.FILE, K._alert_rows = a, b, c


def test_crash_rows_and_lab_track():
    from wsb.analytics.lab import track_record
    p = np.array([.9, .1, .1, .9, .1, .1, .9, .1, .1])
    y = np.array([1., 0, 0, 0, 1, 1, 1, 1, 1])
    t = track_record(p, y, np.full(9, .5), 3)                                         # rows 0, 3, 6: one window each
    assert t == {"n": 3, "events": 2, "alarm": 3, "hits": 2, "misses": 0, "base_rate": t["base_rate"]} and abs(t["base_rate"] - 200 / 3) < 1e-9
    lab = {"horizons": [{"days": 21, "drawdown_pct": 5.0, "base_model": {"auc_oos": .66, "skill": .03, "track": {"n": 250, "events": 40, "alarm": 60, "hits": 18, "misses": 22, "base_rate": 16.0},
                                                                         "calibration": [{"pred": 30.0, "actual": 28.0, "n": 300}]}},
                        {"days": 126, "drawdown_pct": 20.0, "base_model": {"track": {"n": 45, "events": 5, "alarm": 8, "hits": 3, "misses": 2, "base_rate": 11.0}}},
                        {"days": 63, "drawdown_pct": 10.0}]}
    a, b, c = SPV.FILE, IL.FILE, K._alert_rows
    try:
        _files()
        K._alert_rows = lambda: []
        h = K.sec_track_record(_eng(lab))
        cs = _cells(h, "21 日內跌 ≥5%（機率偏高時）")
        assert cs[1] == "60" and cs[2] == "18" and "30%" in cs[3] and cs[5] == "42" and "贏過基準" in cs[6] and "22 次大跌" in cs[0]
        assert "樣本太少" in _cells(h, "126 日內跌")[3] and "63 日" not in h.split("<details")[0]
        assert "樣本外 AUC 0.66" in h and "250 段不重疊" in h
        assert K.crash_rows(_eng()) == []
    finally:
        SPV.FILE, IL.FILE, K._alert_rows = a, b, c


def test_rules_and_alerts_keep_holdings_out():
    rules = {"rows": [{"zh": "規則甲", "en": "A", "n": 30, "dd5": 40.0, "base_dd5": 20.0}, {"zh": "規則乙", "en": "B", "n": 5, "dd5": 100.0, "base_dd5": 20.0}, {"zh": "空", "n": 0}]}
    r = K.rules_row(_eng(rules=rules))
    assert r["n"] == 35 and r["hits"] == 17 and abs(r["base"] - 20) < 1e-9 and r["false"] == 18
    assert K.rules_row(_eng()) is None
    d = pd.bdate_range(end="2026-11-03", periods=600)
    spx = pd.Series(np.linspace(4000, 5000, len(d)), index=d)
    ts = d[-60].timestamp() + 72000
    sent = [(ts + i * 200000, "gamma_flip", "risk", "🚨", "t", 4900.0, 40.0) for i in range(3)]
    e = _eng()
    e.market = types.SimpleNamespace(series=lambda t: spx)
    from wsb import store
    orig_t, orig_k = store.tracked_alerts, K._alert_rows
    try:
        store.tracked_alerts = lambda days=365: sent + [(ts, "pf_dd:2026-10-01", "risk", "🚨", "private", 4900.0, 40.0)]
        assert all(not x[1].startswith("pf_dd") for x in K._alert_rows())
        rows = K.alert_rows(e)
        assert rows and rows[0]["n"] == 3 and rows[0]["v"] == "small" and rows[0]["false"] == 3
        assert all("持倉" not in f["name"] for f in rows[0]["fam"])
        h = K.sec_track_record(e)
        assert "持倉" not in h and "private" not in h and "已發出的風險警報" in h
        K._alert_rows = lambda: []
        assert K.alert_rows(e) == []
    finally:
        store.tracked_alerts, K._alert_rows = orig_t, orig_k


def test_wired_in():
    src = (Path(K.__file__).parent / "build_site.py").read_text(encoding="utf-8")
    assert "STK.sec_track_record" in src
    from tools import site_stamp as STP
    assert "sec_track_record" in STP.CARD


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
