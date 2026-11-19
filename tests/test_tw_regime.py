"""台股進場環境: the six monthly conditions (no look-ahead), the forward-return backtest, the card wording.
Run: python -m tests.test_tw_regime"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_twrg_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_twregime as R  # noqa: E402


def months(n, start="2000-01"):
    out, ym = [], start
    for _ in range(n):
        out.append(ym)
        ym = R._shift(ym, 1)
    return out


def fake(n=120):
    ms = months(n)
    S = {"taiex": {m: 1000 + i * 10 for i, m in enumerate(ms)}, "lead": {m: 100 + i for i, m in enumerate(ms)},
         "exports": {m: 50 + i for i, m in enumerate(ms)}, "tw10y": {m: 3 - i * 0.01 for i, m in enumerate(ms)},
         "us10": {m: 5 - i * 0.01 for i, m in enumerate(ms)}, "m1b": {m: 6.0 for m in ms}, "m2": {m: 5.0 for m in ms},
         "orders_idx": {m: 52.0 for m in ms}}
    return ms, S


def test_shift_and_conditions():
    assert R._shift("2026-11", 3) == "2027-02" and R._shift("2026-01", -1) == "2025-12" and R._shift("2026-12", -12) == "2025-12"
    ms, S = fake()
    c = R.conditions(ms[-1], S)
    assert all(c.values()), c                              # everything improving → all six favourable
    assert R.conditions(ms[3], S)["trend"] is None         # not 10 months of history yet
    S2 = dict(S, taiex=dict(S["taiex"]))
    S2["taiex"][ms[-1]] = 1                                # a crash this month → trend off, nothing later is used
    assert R.conditions(ms[-1], S2)["trend"] is False and R.conditions(ms[-2], S2)["trend"] is True


def test_backtest_groups_and_card():
    ms, S = fake()
    bt = R.backtest(S)
    assert bt["since"] and bt["groups"][-1]["label"] == "全部月份"
    top = bt["groups"][2]
    assert top["months"] == len(bt["rows"]) and top["stats"][12]["n"] == len(bt["rows"]) - 12
    assert top["stats"][3]["up"] == 100
    assert R.latest(S) == ms[-1]
    bub = {"inds": [{"key": "ext", "now": -7.4, "date": "2026-11-19"},
                    {"key": "pe", "now": 14.8, "pct": 17, "date": "2026-11-19"},
                    {"key": "mg", "now": 4844.0, "z": 1.1, "date": "2026-11-19"}], "scored": 7, "hot_n": 3}
    cur = R.current(S, bub, [{"date": "2026-11-19", "foreign": -100.0}, {"date": "2026-11-18", "foreign": -765.6}])
    assert cur["each"]["trend"]["ok"] is False and "200 日線" in cur["each"]["trend"]["note"] and cur["green"] == 5
    names = [n for n, _, _ in cur["extra"]]
    assert any("外資" in n for n in names) and any("估值" in n for n in names) and any("外銷訂單" in n for n in names)
    v = {"bt": bt, "cur": cur}
    assert R.lead(v).startswith("一句話看懂：大環境 6 項條件裡 5 項有利")
    h = R.sec_tw_regime(types.SimpleNamespace(_twregime_view=v))
    assert 'id="twregime"' in h and "不是「什麼時候該進場」" in h and "過去的統計不代表未來" in h
    for w in ("目標價", "上漲空間", "買進", "賣出", "低估", "高估", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池"):
        assert w not in h, w
    assert R.sec_tw_regime(types.SimpleNamespace(_twregime_view={})) == ""


def test_verdict_both_ways():
    mk = lambda lo, hi: {"groups": [{"stats": {12: {"med": lo}}}, {"stats": {12: {"med": 0}}}, {"stats": {12: {"med": hi}}}]}  # noqa: E731
    assert "不能拿來抓時點" in R.verdict(mk(16.4, 9.8))
    assert "多 10.0 個百分點" in R.verdict(mk(2.0, 12.0))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
