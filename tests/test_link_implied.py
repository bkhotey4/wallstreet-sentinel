"""財報跳空成績單 + 個股台美連動: the implied move is kept only while the report is ahead and resolved on the two-session
window; the theoretical fair share is ~42 %; the stock linkage finds a planted US leader, judges it out of sample, rejects
noise, pairs the US night into the next Taiwan session; the cards render without trading words.
Run: python -m tests.test_link_implied"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_li_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "加碼", "進場參考區")


def test_implied_log_cycle():
    from wsb.analytics import implied_log as IL
    assert 41 < IL.FAIR_OVER < 44 and 0.83 < IL.FAIR_MED < 0.87
    log = {}
    rows = [{"sym": "AAA", "name": "甲", "date": "2026-11-03", "time": "after", "mv": 6.0, "exp": "2026-11-06"},
            {"sym": "BBB", "name": "乙", "date": "2026-11-02", "time": "pre", "mv": 4.0},      # report day, pre-market → already out
            {"sym": "CCC", "name": "丙", "date": "2026-11-05", "time": "", "mv": None}]
    IL.record(log, rows, "2026-11-02")
    assert set(log) == {"AAA|2026-11-03"}
    rows[0]["mv"] = 7.0
    IL.record(log, rows, "2026-11-03")                     # after-close report: the same-day snapshot still counts
    assert log["AAA|2026-11-03"]["mv"] == 7.0
    px = pd.Series([100.0, 101.0, 110.0], index=pd.to_datetime(["2026-11-02", "2026-11-03", "2026-11-04"]))
    IL.resolve(log, lambda s: px, "2026-11-05")
    assert abs(log["AAA|2026-11-03"]["act"] - 10.0) < 1e-6   # close before (11-02) → close after (11-04)
    IL.record(log, [{**rows[0], "mv": 3.0}], "2026-11-02")   # never overwritten once resolved
    assert log["AAA|2026-11-03"]["mv"] == 7.0
    st = IL.stats(log)
    assert st["n"] == 1 and st["over"] == 1 and "lo" not in st and st["start"] == "2026-11-03"
    for i in range(30):
        log[f"X{i}|2026-10-{i % 28 + 1:02d}"] = {"sym": f"X{i}", "name": "x", "date": f"2026-10-{i % 28 + 1:02d}", "mv": 5.0, "act": 2.0 if i % 3 else -8.0}
    st = IL.stats(log)
    assert st["n"] == 31 and st["lo"] < st["over_pct"] < st["hi"]


def test_paired_compounds_gap():
    from wsb.analytics import tw_link as L
    us = pd.DataFrame({"u": [1.0, 2.0, -1.0]}, index=pd.to_datetime(["2026-10-29", "2026-10-30", "2026-11-02"]))
    tw = pd.to_datetime(["2026-10-30", "2026-11-02", "2026-11-03"])
    x = L.paired(us, tw)
    assert abs(x.loc["2026-11-02", "u"] - ((1.02 * 1.0) - 1) * 100) < 1e-9          # Friday's US session → Monday Taiwan
    assert abs(x.loc["2026-11-03", "u"] + 1.0) < 1e-9


class SP:
    def __init__(self, close):
        self.close = close


def _world(n=600, seed=5):
    idx = pd.bdate_range(end="2026-10-30", periods=n)
    rng = np.random.default_rng(seed)
    us = {f"U{i}": rng.normal(0, 1.5, n) for i in range(12)}
    lead = us["U3"]
    tw = {"1111.TW": 0.6 * np.roll(lead, 1) + rng.normal(0, 1.0, n), "2222.TW": rng.normal(0, 1.5, n)}
    for i in range(3, 7):
        tw[f"{3333 + i}.TW"] = rng.normal(0, 1.5, n)
    px = {k: 100 * np.cumprod(1 + v / 100) for k, v in {**us, **tw}.items()}
    close = pd.DataFrame(px, index=idx)
    names = {**{k: (k, k, "us", "半導體") for k in us}, **{k: (k, k, "tw", "半導體") for k in tw}}
    return SP(close), names


def test_stock_link_finds_leader_and_rejects_noise():
    from wsb.analytics import tw_link as L
    sp, names = _world()
    r = L.stock_link(sp, names, None)
    a = {x["sym"]: x for x in r["rows"]}
    assert a["1111.TW"]["p"] == "U3" and a["1111.TW"]["ok"] and a["1111.TW"]["corr"] > 0.4 and a["1111.TW"]["r2"] > 0
    assert not a["2222.TW"]["ok"]                          # the best of 12 random partners does not survive the test year
    assert r["n_ok"] == 1 and r["split"] < r["to"]


def test_open_track():
    from wsb.analytics import tw_link as L
    idx = pd.bdate_range(end="2026-10-30", periods=900)
    rng = np.random.default_rng(9)
    u = rng.normal(0, 1.2, 900)
    t = 0.5 * np.roll(u, 1) + rng.normal(0, 0.6, 900)
    tr = L.open_track(pd.Series(100 * np.cumprod(1 + u / 100), index=idx), pd.Series(100 * np.cumprod(1 + t / 100), index=idx))
    assert tr and tr["mae"] < tr["mae0"] and tr["hit"] > 70


def test_cards_render():
    from tools import site_intel as SI
    from wsb.analytics import implied_log as IL, tw_link as L
    sp, names = _world()
    tl = L.stock_link(sp, names, None)
    html = SI._stock_link_html(tl)
    assert "樣本外" in html and "1111" in html and "2222" not in html
    log = {f"X{i}|2026-10-{i + 1:02d}": {"sym": f"X{i}", "name": "x", "date": f"2026-10-{i + 1:02d}", "mv": 5.0, "act": 3.0} for i in range(25)}
    st = IL.stats(log)
    lead = SI._earn_lead([{"name": "甲", "mv": 9.0, "ratio": 1.6}, {"name": "乙", "mv": 2.0, "ratio": 0.7}], st)
    assert "1 家被預期波動比自己過去大" in lead and "偏多" in lead          # 0 of 25 moved more than implied
    assert "剛開始記錄" in SI._earn_lead([], IL.stats({}))
    tab = SI._earn_log_html(st)
    for w in BANNED:
        assert w not in html + lead + tab, w
    eng = types.SimpleNamespace(sx={"earn": [{"sym": "AAA", "name": "甲", "name_en": "A", "theme": "半導體", "date": "2026-11-03", "time": "after",
                                              "mv": 6.0, "exp": "2026-11-06", "reacts": [3.0], "avg": 3.0, "ratio": 2.0, "asof": "x"}], "earn_log": st})
    out = SI.sec_earn_moves(eng)
    assert "一句話看懂" in out and "財報跳空成績單" in out


if __name__ == "__main__":
    fails = 0
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            try:
                f()
                print("ok  ", n)
            except Exception as ex:  # noqa: BLE001
                fails += 1
                import traceback
                traceback.print_exc()
                print("FAIL", n, repr(ex))
    sys.exit(1 if fails else 0)
