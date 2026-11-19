"""台股泡沫觀察: TWSE parsers, sampling plan, z-score lights, the card and its hypothesis section.
Run: python -m tests.test_tw_bubble"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types
from datetime import date, timedelta

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_twbb_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.data import tw_bubble as B  # noqa: E402

B.SEED = B.FILE.with_name("no_seed.json")          # tests never read the real seed


def test_parsers():
    fm = B.parse_fm({"stat": "OK", "fields": ["日期", "成交股數", "成交金額", "成交筆數", "發行量加權股價指數", "漲跌點數"],
                     "data": [["115/11/02", "10", "799,687,507,911", "4", "44,920.14", "-291.69"]]})
    assert fm == [["2026-11-02", 7996.9, 44920.14]]
    assert B.parse_fm({"stat": "很抱歉"}) == []
    dt = B.parse_dt({"stat": "OK", "tables": [{"fields": ["當日沖銷交易總成交股數", "當日沖銷交易總成交股數占市場比重%", "當日沖銷交易總買進成交金額",
                                                           "當日沖銷交易總買進成交金額占市場比重%"], "data": [["4,259", "27.83", "389", "41.29"]]}]})
    assert dt == 41.29
    mg = B.parse_mg({"stat": "OK", "tables": [{"fields": ["項目", "買進", "賣出", "現金(券)償還", "前日餘額", "今日餘額"],
                                               "data": [["融資(交易單位)", "1", "1", "1", "1", "7,522,037"],
                                                        ["融資金額(仟元)", "1", "1", "1", "1", "228,275,510"]]}]})
    assert mg == 2282.8                             # 仟元 → 億元
    rows = [[f"{1000 + i}", "x", "10", "3.0", 114, f"{10 + i % 40}", "1.5", "115/2"] for i in range(400)]
    rows.append(["2330", "台積電", "1000", "1.5", 114, "25.5", "7.1", "115/2"])
    rows.append(["0050", "元大台灣50", "100", "", "", "", "", ""])       # ETF: skipped
    v = B.parse_val({"stat": "OK", "fields": ["證券代號", "證券名稱", "收盤價", "殖利率(%)", "股利年度", "本益比", "股價淨值比", "財報年/季"], "data": rows})
    assert v["tsmc_pe"] == 25.5 and v["n"] == 401 and 0 < v["pe30"] < 50
    assert B.parse_val({"stat": "OK", "fields": ["證券代號"], "data": []}) is None


def test_sampling_and_plan():
    days = []
    d0 = date(2023, 1, 2)
    for i in range(1100):
        d = d0 + timedelta(days=i)
        if d.weekday() < 5:
            days.append(d.isoformat())
    today = date.fromisoformat(days[-1])
    wk = B.weekly(days, 3, today)
    assert wk[0] == days[-1] and len(wk) >= 150 and all(date.fromisoformat(x).weekday() == 4 for x in wk[1:20])
    mo = B.monthly(days, 5, today)
    assert mo[0] == days[-1] and len(mo) == len({x[:7] for x in days})
    assert len(B.months_back(today, 5)) == 61
    p = B.plan({}, today, 1e9)
    assert p and all(k == "fm" for k, _ in p)             # dates come from the monthly files first
    fm = {}
    for s in days:
        fm.setdefault(s[:7], []).append([s, 1000.0, 15000.0])
    p = B.plan({"fm": fm, "fm_ts": {m: 1.0 for m in fm}}, today, 2e9)
    kinds = [k for k, _ in p]
    assert kinds[:3] == ["fm"] * 3 or "dt" in kinds          # missing months still first, then the latest day
    first_daily = [t for t in p if t[0] != "fm"][:3]
    assert all(k == days[-1] for _, k in first_daily)


def test_view_lights_and_card():
    days, fm = [], {}
    d0 = date(2023, 1, 2)
    for i in range(1100):
        d = d0 + timedelta(days=i)
        if d.weekday() < 5:
            days.append(d.isoformat())
    for j, s in enumerate(days):
        fm.setdefault(s[:7], []).append([s, 2000.0 + j * 2, 15000.0 + j * 10])     # steady rise: price far above its 200-day line
    wk = B.weekly(days, 3, date.fromisoformat(days[-1]))
    dt = {s: 30.0 + (5 if i == 0 else (i % 3) * 0.1) for i, s in enumerate(wk)}         # latest week: a spike → 🔴
    mg = {s: 2000.0 for s in wk}                                                         # flat: no z
    val = {s: {"pe_med": 15.0 + (i % 2) * 0.5, "pb_med": 1.6, "tsmc_pe": 20 + (i % 5), "pe30": 10.0, "n": 900}
           for i, s in enumerate(B.monthly(days, 5, date.fromisoformat(days[-1])))}
    B.FILE.write_text(json.dumps({"fm": fm, "dt": dt, "mg": mg, "val": val, "ts": 1.8e9,
                                  "score": {"2026-10": {"hot": 1, "red": 0, "of": 5, "date": "2026-10-01"}}}), encoding="utf-8")
    v = B.view()
    by = {x["key"]: x for x in v["inds"]}
    assert by["dt"]["light"] == "🔴" and by["dt"]["z"] >= 2
    assert by["mg"]["z"] is None and by["mg"]["light"] == "⚪"                          # zero spread: no light, no crash
    assert "當沖占成交金額比重" in v["red"] and v["scored"] >= 3
    from tools import site_twbubble as S
    h = S.sec_tw_bubble(types.SimpleNamespace(_twbubble_view=v))
    assert 'id="twbubble"' in h and "一句話看懂" in h and "2027 年下半年" in h and "證交所" in h and "2026-10" in h
    assert "不是本站的預測" in h
    for w in ("目標價", "上漲空間", "買進", "賣出", "低估", "高估", "買點", "加碼參考區", "進場參考區", "精選池", "未實現"):
        assert w not in h, w
    assert v["peak"]["dd"] == 0 and "高點附近" in S.fall_text(v["peak"])
    fall = {"date": "2026-10-06", "high": 49822.55, "now": 38426.89, "now_date": "2026-11-19", "dd": -22.9, "days": 44}
    assert "空頭市場" in S.fall_text(fall) and "-22.9%" in S.fall_text(fall)
    assert "破裂其實已經開始" in S.hypothesis(dict(v, peak=fall))
    assert "修正" in S.fall_text(dict(fall, dd=-12.0)) and "破裂其實已經開始" not in S.hypothesis(dict(v, peak=dict(fall, dd=-12.0)))
    assert S.sec_tw_bubble(types.SimpleNamespace(_twbubble_view={})) == ""
    assert "暫時不亮燈" in S.lead({"scored": 0})


def test_seed_merge():
    B.FILE.write_text(json.dumps({"dt": {"2026-11-19": 41.0}}), encoding="utf-8")
    seed = B.FILE.with_name("seed_test.json")
    seed.write_text(json.dumps({"dt": {"2026-11-19": 99.0, "2026-11-12": 40.0}, "mg": {"2026-11-12": 3000.0}}), encoding="utf-8")
    old, B.SEED = B.SEED, seed
    try:
        d = B.load()
    finally:
        B.SEED = old
    assert d["dt"] == {"2026-11-19": 41.0, "2026-11-12": 40.0} and d["mg"]["2026-11-12"] == 3000.0   # own cache wins
    B.FILE.write_text(json.dumps({"fm": {"2026-11": [["2026-11-19", 1.0, 2.0]]}, "fm_ts": {"2026-11": 1.79e9}}), encoding="utf-8")
    assert B.stamp() == (1.79e9, "2026-11-19")                     # no own fetch yet: the seed's fetch time
    assert set(B.seed(d)) == {"fm", "fm_ts", "dt", "mg", "val", "us10"}


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
