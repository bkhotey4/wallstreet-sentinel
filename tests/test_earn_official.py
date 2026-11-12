"""財報日曆官方備援（SEC 8-K Item 2.02 / 10-Q）：公布日、盤前盤後、合併、名單保存、財報結論文字（不連網）。"""
from __future__ import annotations

import asyncio
import pathlib
import tempfile
from datetime import date


def subs(cik, rows):
    keys = ("form", "items", "acceptanceDateTime", "filingDate", "accessionNumber", "primaryDocument")
    return {"cik": str(cik), "filings": {"recent": {k: [r[i] for r in rows] for i, k in enumerate(keys)}}}


def main() -> None:
    from wsb.data import earn_official as EO
    EO.FILE = pathlib.Path(tempfile.mkdtemp()) / "eo.json"

    assert EO.session_of("2026-10-29T20:05:27.000Z") == "after"          # 16:05 EDT
    assert EO.session_of("2026-11-06T11:47:00.000Z") == "pre"            # 06:47 EST
    assert EO.session_of("2026-11-06T16:00:00.000Z") == ""               # 11:00 EST, during the session
    assert EO.et_day("2026-11-05T02:18:00.000Z", "x") == "2026-11-04"    # 21:18 ET the evening before

    js = subs(1018724, [("8-K", "2.02,9.01", "2026-10-29T20:05:27.000Z", "2026-10-29", "0001018724-26-000038", "a.htm"),
                        ("10-Q", "", "2026-10-31T00:29:00.000Z", "2026-10-30", "0001018724-26-000039", "q.htm"),
                        ("8-K", "5.02", "2026-10-20T12:00:00.000Z", "2026-10-20", "x", "x.htm"),
                        ("8-K", "2.02", "2025-07-30T20:00:00.000Z", "2025-07-30", "y", "y.htm")])
    r = EO.parse_202(js, "2026-01-01")
    assert len(r) == 1 and r[0]["date"] == "2026-10-29" and r[0]["time"] == "after", r       # the 10-Q after an 8-K is routine
    assert r[0]["url"] == "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000038/a.htm"
    only_q = subs(1849056, [("10-Q", "", "2026-11-06T12:32:00.000Z", "2026-11-06", "0001849056-26-1", "o.htm")])
    r = EO.parse_202(only_q, "2026-01-01")
    assert len(r) == 1 and r[0]["form"] == "10-Q" and r[0]["time"] == "pre"                  # no 8-K 2.02 → the 10-Q day

    days = {"2026-08-01": {"rows": [{"sym": "AMZN", "name": "Amazon", "mcap": 2.4e12}, {"sym": "SMALL", "name": "S", "mcap": 5e9}]},
            "2026-11-13": {"rows": [{"sym": "AMZN", "name": "Amazon", "mcap": 2.5e12, "eps_f": 1.0}]}}
    u = EO.universe(days, ["NVDA"])
    assert set(u) == {"AMZN", "NVDA"} and u["AMZN"]["mcap"] == 2.5e12
    assert set(EO.universe({}, [], {"AMZN": {"name": "Amazon", "mcap": 2.5e12}})) == {"AMZN"}   # saved list survives

    rows = [{"sym": "AMZN", "eps_f": 2.0}]
    assert not EO.merge_day(rows, {"sym": "AMZN"}) and rows[0]["eps_f"] == 2.0
    assert EO.merge_day(rows, {"sym": "OKLO"}) and len(rows) == 2

    real = EO.http.get
    calls = []

    async def fake(url, **k):
        calls.append(url)
        return js if "1018724" in url else only_q
    try:
        EO.http.get = fake
        tmap = {"AMZN": {"cik": 1018724}, "OKLO": {"cik": 1849056}}
        n = asyncio.run(EO.fill(days, ["OKLO"], date(2026, 11, 12), 15, budget_s=30, tmap=tmap))
        assert n == 2, n
        a = next(x for x in days["2026-10-29"]["rows"] if x["sym"] == "AMZN")
        assert a["src"] == "sec" and a["time"] == "after" and a["eps_f"] is None and a["mcap"] == 2.5e12
        assert days["2026-11-06"]["rows"][0]["sym"] == "OKLO" and days["2026-10-29"]["src_fallback"] == "sec"
        assert "AMZN" in EO.load()["known"]
        k = len(calls)
        assert asyncio.run(EO.fill(days, ["OKLO"], date(2026, 11, 12), 15, budget_s=30, tmap=tmap)) == 0
        assert len(calls) == k, "checked once a day"
    finally:
        EO.http.get = real

    from wsb.analytics.earn_verdict import verdict
    v = verdict({"src": "sec", "result": None, "react": 2.0, "eps": None})
    assert "8-K" in v["zh"] and "不判斷優於或低於預期" in v["zh"], v
    for w in ("買進", "賣出", "目標價", "低估", "高估"):
        assert w not in v["zh"]
    print("test_earn_official ok")


if __name__ == "__main__":
    main()
