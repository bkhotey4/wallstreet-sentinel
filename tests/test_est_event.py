"""分析師預期修正趨勢 + 重大數據公布後的市場反應：parsers, the first-snapshot honesty, same-quarter comparison, failed fetches
keeping the last good data without fake freshness, the time-zone rule for the TAIEX, FRED's revision-only dates, and the
noise verdicts.  Run: python -m tests.test_est_event"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
import types
from datetime import date, timedelta

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ee_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from tools import site_estrev as SE  # noqa: E402
from tools import site_event_react as SR  # noqa: E402
from tools import site_stamp as STP  # noqa: E402
from wsb.analytics import event_clock as CLK  # noqa: E402
from wsb.analytics import event_react as EV  # noqa: E402
from wsb.data import econcal as EC  # noqa: E402
from wsb.data import est_revisions as ER  # noqa: E402
from wsb.data import http as H  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")


def _mom(eps=2.5, wk=2.5, mo=2.4, fq="Oct 2026"):
    return {"data": {"changeInConsensus": {"fiscalQtrEndText": f"Fiscal Quarter End {fq}", "currentData": {"qtrMean": eps}, "weekData": {"qtrMean": wk},
                                           "monthData": {"qtrMean": mo}},
                     "estimatesChanged": {"quarterDataUp": {"changeValue": 3}, "quarterDataDown": {"changeValue": 1}}}}


def _fc(n=12, fq="Oct 2026"):
    return {"data": {"quarterlyForecast": {"rows": [{"fiscalEnd": fq, "consensusEPSForecast": 2.5, "noOfEstimates": n}]}}}


def _clean():
    for f in (ER.FILE, EV.FILE):
        if f.exists():
            f.unlink()


def _patch_http(fn):
    orig, sl = H.get, asyncio.sleep

    async def fake(url, **kw):
        return fn(url, kw)

    async def nosleep(_):
        return None
    H.get, asyncio.sleep = fake, nosleep
    return lambda: (setattr(H, "get", orig), setattr(asyncio, "sleep", sl))


def test_parsers():
    p = ER.parse_momentum(_mom())
    assert p == {"fq": "Oct 2026", "eps": 2.5, "wk": 2.5, "mo": 2.4, "up": 3.0, "dn": 1.0}, p
    assert ER.parse_momentum({"data": {"changeInConsensus": {}}}) is None       # BRK.B answers 200 with nothing
    assert ER.parse_momentum({}) is None and ER.parse_momentum({"data": None}) is None
    assert ER.parse_forecast(_fc()) == ("Oct 2026", 12.0) and ER.parse_forecast({"data": {}}) is None


def test_direction_rules():
    assert ER._dir(1.01, 1.00)[0] == 1 and ER._dir(1.001, 1.00) == (0, 0.0)     # under half a cent: rounding
    assert ER._dir(100.2, 100.0)[0] == 0                                        # 0.2% is not a revision
    assert ER._dir(-0.9, -1.0)[0] == 1 and ER._dir(-1.1, -1.0)[0] == -1         # a smaller loss is an upward revision
    assert ER._dir(0.08, 0.02) == (1, None)                                     # near zero: sign only, no 300% headline


def _rec(eps, mo, wk=None, fq="Dec 2026", d="2026-11-04", n=8):
    return {"eps": eps, "wk": eps if wk is None else wk, "mo": mo, "fq": fq, "d": d, "n": n, "ts": time.time()}


def test_view_first_day_and_own_history():
    syms = {f"S{i}": _rec(2.0, 1.9) for i in range(8)}                           # 8 up over 30 days
    syms.update({f"D{i}": _rec(2.0, 2.2, wk=2.1, n=1) for i in range(3)})        # 3 down, a one-analyst consensus among them
    d = {"syms": syms, "hist": {}, "first": "2026-11-04", "asof": "2026-11-04", "ts": time.time(), "cov": [11, 11]}
    v = ER.view(d)
    b = v["h"][30]
    assert v["available"] and b["up"] == 8 and b["dn"] == 3 and b["n"] == 11 and b["src"] == 11 and b["own"] == 0, b
    assert v["days"] == 0 and b["net"] > 0
    assert not any(x["sym"].startswith("D") for x in b["low"])                   # a single analyst never makes the list
    # an own snapshot of the same quarter wins over the source's look-back; a rolled quarter must not be compared
    d["hist"] = {"S0": [["2026-10-01", "Dec 2026", 1.0]], "S1": [["2026-10-01", "Sep 2026", 9.0]]}
    b = ER.view(d)["h"][30]
    assert b["own"] == 1 and b["top"][0]["sym"] == "S0" and b["top"][0]["old"] == 1.0, b
    assert all(x["old"] != 9.0 for x in b["top"] + b["low"])
    d["syms"]["OLD"] = _rec(5.0, 1.0, d="2026-10-20")                            # stale symbol leaves the counts
    assert ER.view(d)["n"] == 11
    assert ER.view({"syms": {}, "asof": None})["available"] is False


def test_symbols_universe():
    today = date(2026, 11, 4)
    days = {"2026-11-20": {"rows": [{"sym": "BIG", "mcap": 5e10}, {"sym": "TINY", "mcap": 1e9}]}, "2026-01-01": {"rows": [{"sym": "OLD", "mcap": 9e11}]},
            "2026-10-01": {"rows": [{"sym": "DONE", "mcap": 2e10}]}}
    s = ER.symbols(days, today)
    assert "BIG" in s and "DONE" in s and "TINY" not in s and "OLD" not in s    # a name stays after it reported
    from wsb.data.stocks import universe
    assert set((universe().get("us") or {}).get("symbols", {})) <= set(s)


def test_estimate_fetch_failure_keeps_last_good():
    _clean()
    syms = [f"X{i}" for i in range(4)]
    undo = _patch_http(lambda url, kw: _fc() if "earnings-forecast" in url else _mom())
    try:
        d = asyncio.run(ER.refresh(syms))
    finally:
        undo()
    good_ts, asof = d["ts"], d["asof"]
    assert d["syms"]["X1"]["eps"] == 2.5 and d["syms"]["X1"]["n"] == 12 and d["first"] == asof and d["cov"] == [4, 4]
    # a day later every request fails: data and ts stay exactly as they were
    d = ER.load()
    for r in d["syms"].values():
        r["ts"] -= 2 * 86400
        r["try"] = r["ts"]
    d["ts"] = good_ts - 2 * 86400
    ER._save(d)

    def boom(url, kw):
        raise TimeoutError("nasdaq down")
    undo = _patch_http(boom)
    try:
        d2 = asyncio.run(ER.refresh(syms))
    finally:
        undo()
    assert d2["ts"] == good_ts - 2 * 86400 and d2["syms"]["X1"]["eps"] == 2.5 and d2["asof"] == asof
    # a 200 with an empty body (schema change) must not bump freshness or brand known symbols "no coverage"
    undo = _patch_http(lambda url, kw: {"data": None})
    try:
        d3 = asyncio.run(ER.refresh(syms, force=True))
    finally:
        undo()
    assert d3["ts"] == good_ts - 2 * 86400 and not d3["syms"]["X1"].get("none")
    # stale ts on the page: the stamp says old instead of pretending
    eng = types.SimpleNamespace()
    st = STP.stamp(eng, "sec_est_rev", "tech", time.time())
    assert " old" in st and "資料偏舊" in st, st


def test_estimate_partial_pass_is_not_fresh():
    _clean()
    syms = [f"Y{i}" for i in range(10)]
    calls = []

    def some(url, kw):
        sym = url.split("/analyst/")[1].split("/")[0]
        if sym in ("Y0", "Y1"):
            return _fc() if "earnings-forecast" in url else _mom()
        calls.append(sym)
        raise TimeoutError("x")
    undo = _patch_http(some)
    try:
        d = asyncio.run(ER.refresh(syms))
    finally:
        undo()
    assert d["cov"] == [2, 10] and "ts" not in d and len(calls) == 8             # 2 of 10 is not "updated"
    st = STP.stamp(types.SimpleNamespace(), "sec_est_rev", "tech", time.time())
    assert "最後更新" not in st, st


def test_estimate_no_coverage_and_roll():
    _clean()
    state = {"fq": "Oct 2026"}

    def f(url, kw):
        if "/NONE/" in url:
            return {"data": {}}
        return _fc(fq=state["fq"], n=20 if state["fq"] != "Oct 2026" else 5) if "earnings-forecast" in url else _mom(fq=state["fq"])
    undo = _patch_http(f)
    try:
        d = asyncio.run(ER.refresh(["AAA", "NONE"]))
        assert d["syms"]["NONE"].get("none") and d["syms"]["AAA"]["n"] == 5
        x = ER.load()
        x["syms"]["AAA"]["ts"] -= 2 * 86400
        x["syms"]["AAA"]["try"] -= 2 * 86400
        ER._save(x)
        state["fq"] = "Jan 2027"                                                 # the analyst count follows the quarter
        d = asyncio.run(ER.refresh(["AAA", "NONE"]))
        assert d["syms"]["AAA"]["fq"] == "Jan 2027" and d["syms"]["AAA"]["n"] == 20
    finally:
        undo()


def test_estimate_card():
    _clean()
    assert SE.sec_est_rev(None) == ""                                            # no data: no card, no fake freshness
    syms = {f"S{i}": _rec(2.0, 1.9, wk=1.95) for i in range(10)}
    syms["W"] = _rec(1.0, 2.0, wk=1.5)
    d = {"syms": syms, "hist": {}, "first": "2026-11-04", "asof": "2026-11-04", "ts": time.time(), "cov": [11, 11]}
    ER._save(d)
    h = SE.sec_est_rev(None)
    assert "一句話看懂：最近 7 天" in h and "上修比下修多" in h and "分析師預期修正趨勢" in h
    assert "還沒有本站快照可以核對" in h                                         # large look-back moves carry a caution
    assert "2026-11-04 開始" in h and "Nasdaq 提供的" in h                        # says where history begins, and what fills the gap
    assert "分析師" in h and "不是投資建議" in h and "<details" in h
    for w in BANNED:
        assert w not in h, w
    src = open(os.path.join(os.path.dirname(SE.__file__), "build_site.py"), encoding="utf-8").read()
    assert "SER.sec_est_rev" in src and "SEVR.sec_event_react" in src
    assert "sec_est_rev" in STP.CARD and "sec_event_react" in STP.CARD
    _clean()


# ------------------------------------------------------------------ event study
def test_valid_dates_drop_revision_days():
    days = ["2023-01-12", "2023-02-10", "2023-02-14", "2023-03-14", "2024-02-09", "2024-02-13", "2026-11-10"]
    seen = {"2023-01-12": {"a": "0.3%"}, "2023-02-10": {"none": 1}, "2023-02-14": {"a": "0.4%"}}
    v = EV.valid_dates("cpi", days, seen, "2026-11-04")
    assert v == ["2023-01-12", "2023-02-14", "2023-03-14"], v                    # unknown double month is left out; future dropped
    assert EV.valid_dates("fomc", ["2023-02-01", "2023-02-28", "2027-01-01"], {}, "2026-11-04") == ["2023-02-01", "2023-02-28"]


def test_outcome():
    assert EV.outcome("cpi", {"a": "0.4%", "c": "0.3%", "p": "0.2%"}) == "hot"
    assert EV.outcome("cpi", {"a": "0.3%", "c": "0.3%", "p": "0.2%"}) == "inline"
    assert EV.outcome("nfp", {"a": "75K", "c": "185K", "p": "224K"}) == "cool"
    assert EV.outcome("nfp", {"a": "190K", "c": "185K", "p": "224K"}) == "inline"          # inside the macro_events threshold
    assert EV.outcome("nfp", {"a": "190K", "c": "", "p": "224K"}) is None                  # no consensus, no split
    assert EV.outcome("fomc", {"a": "4.00%", "c": "4.00%", "p": "3.75%"}) == "hike"
    assert EV.outcome("fomc", {"a": "4.00%", "c": "", "p": "4.00%"}) == "hold"
    assert EV.outcome("fomc", {"a": "3.75%", "c": "3.75%", "p": "4.00%"}) == "cut"
    assert EV.outcome("cpi", None) is None
    assert EV.outcome("cpi", {"a": "2.6%", "c": "3.0%", "p": "3.0%"}) is None              # a lone y/y row is not the m/m measure


def test_taiex_reacts_next_taiwan_session():
    idx = pd.to_datetime(["2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05", "2026-03-06", "2026-03-09"])
    tw = pd.Series([100.0, 101, 102, 110, 111, 112], index=idx)
    m = EV.react_map(tw, "pct", True, ["2026-03-04", "2026-03-08"])
    assert m["2026-03-04"][0] == pd.Timestamp("2026-03-05") and abs(m["2026-03-04"][1] - (110 / 102 - 1) * 100) < 1e-9   # not the same-date bar
    assert m["2026-03-08"][0] == pd.Timestamp("2026-03-09")                       # Sunday-dated release: Monday's session
    lny = pd.Series([100.0, 101, 90], index=pd.to_datetime(["2026-02-05", "2026-02-06", "2026-02-20"]))
    assert EV.react_map(lny, "pct", True, ["2026-02-06"]) == {}                  # a two-week holiday is not "the next session"
    us = pd.Series([4.0, 4.1, 4.05], index=pd.to_datetime(["2026-03-03", "2026-03-04", "2026-03-05"]))
    m = EV.react_map(us, "bp", False, ["2026-03-04", "2026-03-07"])
    assert abs(m["2026-03-04"][1] - 10) < 1e-9 and "2026-03-07" not in m         # basis points; no bar, no number


def test_verdicts():
    assert EV.verdict(3.2, 40) == "clear" and EV.verdict(-3.2, 40) == "clear"
    assert EV.verdict(2.4, 40) == "maybe" and EV.verdict(1.0, 40) == "noise"
    assert EV.verdict(9.0, 10) == "few" and EV.verdict(None, 40) == "few"
    assert EV.stat(np.ones(3), np.ones(100)) is None                             # too few events: no statistic at all


def _market(seed=7, n=4000):
    """Synthetic closes: event days have double the volatility and no directional edge, except FOMC which adds +1%."""
    idx = pd.bdate_range(end="2026-11-03", periods=n)
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0003, 0.008, n)
    cpi = [d.strftime("%Y-%m-%d") for d in idx[30:-5:21]]
    fomc = [d.strftime("%Y-%m-%d") for d in idx[47:-5:43]]
    for d in cpi:
        r[idx.get_loc(pd.Timestamp(d))] *= 2.5
    for d in fomc:
        r[idx.get_loc(pd.Timestamp(d))] += 0.01
    spx = pd.Series(4000 * np.cumprod(1 + r), index=idx)
    tnx = pd.Series(4 + np.cumsum(rng.normal(0, 0.04, n)) * 0.02, index=idx).clip(lower=0.5)
    tw = pd.Series(10000 * np.cumprod(1 + rng.normal(0.0003, 0.009, n)), index=idx)
    return {"^GSPC": spx, "^TNX": tnx, "^TWII": tw}, cpi, fomc


def test_study_separates_size_from_direction():
    px, cpi, fomc = _market()
    seen = {"cpi": {d: {"a": "0.4%" if i % 2 else "0.2%", "c": "0.3%", "p": "0.3%"} for i, d in enumerate(cpi)}}
    evs = EV.study(px, {"cpi": cpi, "nfp": [], "fomc": fomc}, seen)
    c = next(e for e in evs if e["key"] == "cpi")
    s = next(a for a in c["assets"] if a["key"] == "spx")
    assert s["all"]["n"] == len(cpi) and s["all"]["ratio"] > 1.5 and s["all"]["size"] == "clear", s["all"]
    assert s["all"]["dir"] in ("noise", "maybe"), s["all"]                        # bigger moves, no direction
    assert s["all"]["base_n"] > 3000 and abs(s["all"]["base_mean"]) < 0.2
    assert s["split"]["hot"]["n"] + s["split"]["cool"]["n"] == len(cpi) and s["spread"] is not None
    f = next(e for e in evs if e["key"] == "fomc")
    fs = next(a for a in f["assets"] if a["key"] == "spx")
    assert fs["all"]["mean"] > 0.7 and fs["all"]["dir"] == "clear", fs["all"]     # a real +1% edge is caught
    assert not fs["split"]                                                        # no FOMC records: no invented split
    ld = EV.lead(evs)["zh"]
    assert "波動" in ld and "明顯不同" in ld
    # none of the synthetic windows differs: the sentence says so plainly
    flat = [{"zh": "CPI", "assets": [{"zh": "標普 500", "all": {"size": "noise", "dir": "noise", "ratio": 1.0}}]}]
    assert "分不開" in EV.lead(flat)["zh"] and "看不出" in EV.lead(flat)["zh"]
    near = [{"zh": "FOMC", "en": "FOMC", "assets": [{"zh": "標普 500", "kind": "pct", "all": {"size": "noise", "dir": "maybe", "ratio": 1.0, "t": 2.5}, "spread": None}]}]
    assert "沒有一組" in EV.lead(near)["zh"] and "可能只是巧合" in EV.lead(near)["zh"]
    gap = [{"zh": "CPI", "en": "CPI", "assets": [{"zh": "10 年期美債殖利率", "en": "10y", "kind": "bp", "all": {"size": "noise", "dir": "noise", "ratio": 1.0, "t": 0.2},
                                                  "spread": {"gap": 7.75, "t": 5.2, "dir": "clear"}}]}]
    assert "10 年期殖利率平均差 7.8bp" in EV.lead(gap)["zh"]


def test_unfinished_bar_dropped():
    from wsb.analytics.sessions import completed
    from datetime import datetime
    from zoneinfo import ZoneInfo
    s = pd.Series([1.0, 2.0], index=pd.to_datetime(["2026-11-03", "2026-11-04"]))
    now = datetime(2026, 11, 4, 11, 0, tzinfo=ZoneInfo("America/New_York"))
    assert list(completed(s, "^GSPC", now).index) == [pd.Timestamp("2026-11-03")]


def _eng(px, fomc):
    class M:
        def series(self, t):
            return px.get(t, pd.Series(dtype=float))
    return types.SimpleNamespace(market=M(), econ=types.SimpleNamespace(fomc=[{"date": d} for d in fomc]))


def test_refresh_failure_keeps_last_good():
    _clean()
    rel = CLK.load()
    today = EC.us_today()
    d1, d2 = (today - timedelta(days=40)).isoformat(), (today - timedelta(days=10)).isoformat()
    rel.update(cpi=[d1, d2], nfp=[])
    CLK.FILE.write_text(json.dumps(rel), encoding="utf-8")
    old_ts = time.time() - 5 * 86400
    EV.FILE.write_text(json.dumps({"days": {"cpi": {d1: {"a": "0.3%", "c": "0.2%", "p": "0.3%"}}}, "ts": old_ts, "asof": d1}), encoding="utf-8")
    cal = EC._FILE.read_text(encoding="utf-8") if EC._FILE.exists() else None
    if EC._FILE.exists():
        EC._FILE.unlink()
    orig_fh = EV.CLK.dates_for
    EV.CLK.dates_for = lambda e, k, r: list(r.get(k) or []) if k != "fomc" else []

    def boom(url, kw):
        raise TimeoutError("calendar down")
    undo = _patch_http(boom)
    try:
        d = asyncio.run(EV.refresh(None))
        assert d["ts"] == old_ts and d["days"]["cpi"][d1]["a"] == "0.3%" and d2 not in d["days"]["cpi"] and d["asof"] == d1
        st = STP.stamp(types.SimpleNamespace(), "sec_event_react", "econ", time.time())
        assert " old" in st, st                                                  # a failed pass never reads as fresh
        undo()
        undo = _patch_http(lambda url, kw: {"data": {"rows": []}})               # HTTP 200 with nothing: a hiccup, no verdict yet
        d = asyncio.run(EV.refresh(None))
        assert d["days"]["cpi"][d2].get("tries") == 1 and not d["days"]["cpi"][d2].get("none")
        undo()
        rows = [{"country": "United States", "eventName": "Core CPI", "actual": "0.2%", "consensus": "0.3%", "previous": "0.3%"},
                {"country": "United States", "eventName": "Core CPI", "actual": "2.9%", "consensus": "3.0%", "previous": "3.0%"},
                {"country": "Japan", "eventName": "Core CPI", "actual": "9.9%", "consensus": "1%", "previous": "1%"}]
        seen = []
        undo = _patch_http(lambda url, kw: seen.append(kw["params"]["date"]) or {"data": {"rows": rows}})
        d = asyncio.run(EV.refresh(None))
        assert d["days"]["cpi"][d2] == {"a": "0.2%", "c": "0.3%", "p": "0.3%"} and d["asof"] == d2 and d["ts"] > old_ts
        assert seen == [(date.fromisoformat(d2) + timedelta(days=1)).isoformat()]  # Nasdaq's date parameter is one day ahead
        undo()
        undo = _patch_http(lambda url, kw: {"data": {"rows": [{"country": "United States", "eventName": "ISM", "actual": "1", "consensus": "", "previous": ""}]}})
        x = EV.load()
        del x["days"]["cpi"][d2]
        EV._save(x)
        d = asyncio.run(EV.refresh(None))
        assert d["days"]["cpi"][d2] == {"none": 1}                               # the calendar answered, no CPI that day: a revision date
    finally:
        undo()
        EV.CLK.dates_for = orig_fh
        if cal is not None:
            EC._FILE.write_text(cal, encoding="utf-8")


def test_card_and_upcoming():
    _clean()
    assert SR.sec_event_react(types.SimpleNamespace()) == ""                     # no market: no card
    px, cpi, fomc = _market(seed=11)
    today = EC.us_today()
    nxt = (today + timedelta(days=2)).isoformat()
    rel = CLK.load()
    rel.update(cpi=cpi, nfp=[nxt])
    CLK.FILE.write_text(json.dumps(rel), encoding="utf-8")
    seen = {"cpi": {d: {"a": "0.4%" if i % 3 else "0.2%", "c": "0.3%", "p": "0.3%"} for i, d in enumerate(cpi)}}
    EV.FILE.write_text(json.dumps({"days": seen, "ts": time.time(), "asof": cpi[-1]}), encoding="utf-8")
    orig = EV.CLK.dates_for
    EV.CLK.dates_for = lambda e, k, r: fomc if k == "fomc" else list(r.get(k) or [])
    try:
        h = SR.sec_event_react(_eng(px, fomc))
        assert "接下來" not in h                                                  # the jobs report has no history here: nothing to show
        rel["cpi"] = cpi + [nxt]
        rel["nfp"] = []
        CLK.FILE.write_text(json.dumps(rel), encoding="utf-8")
        cal = EC._FILE.read_text(encoding="utf-8") if EC._FILE.exists() else None
        EC.save({nxt: {"rows": [{"name": "Core CPI", "actual": "", "cons": "0.3%", "prev": "0.2%"}, {"name": "Core CPI", "actual": "", "cons": "3.0%", "prev": "3.1%"}]}})
        h = SR.sec_event_react(_eng(px, fomc))
    finally:
        EV.CLK.dates_for = orig
    if cal is not None:
        EC._FILE.write_text(cal, encoding="utf-8")
    elif EC._FILE.exists():
        EC._FILE.unlink()
    assert "接下來" in h and nxt[5:] in h and "2 天後" in h and "預期 0.3%" in h and "上次 0.2%" in h, h[:600]
    assert "一句話看懂：" in h and "平常一天" in h and "中位數" in h and "<details" in h
    assert "跟雜訊分不開" in h or "有差距，但可能是巧合" in h
    assert "標普 500" in h and "10 年期美債殖利率" in h and "台股加權指數" in h
    assert "不是投資建議" in h and "公布後第一個收盤" in h
    for w in BANNED:
        assert w not in h, w
    _clean()


if __name__ == "__main__":
    for k, fn in list(globals().items()):
        if k.startswith("test_"):
            fn()
            print("ok", k)
