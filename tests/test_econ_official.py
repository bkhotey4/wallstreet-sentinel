"""財經日曆官方備援（FRED 日程＋資料版本）：新公布判斷、月增年增、和既有 Nasdaq 列合併、日程補列（不連網）。"""
from __future__ import annotations

import asyncio
from datetime import date


def main() -> None:
    from wsb.data import econ_official as EO

    # FRED clamps vintage dates to the queried window [day-1, day]; the 10-01 point only exists from the release day
    obs = [{"realtime_start": "2026-11-09", "realtime_end": "2026-11-10", "date": f"2025-{m:02d}-01", "value": str(300 + m)} for m in range(9, 13)]
    obs += [{"realtime_start": "2026-11-09", "realtime_end": "2026-11-10", "date": f"2026-{m:02d}-01", "value": str(313 + m)} for m in range(1, 10)]
    obs += [{"realtime_start": "2026-11-10", "realtime_end": "2026-11-10", "date": "2026-10-01", "value": "330.0"}]
    v = EO.released_on(obs, "2026-11-10")
    assert v and v[-1] == ("2026-10-01", 330.0)
    assert EO.released_on(obs[:-1], "2026-11-10") is None                      # nothing new on the day → not out yet
    assert EO.released_on([dict(x, value=".") for x in obs], "2026-11-10") is None
    mm = EO.transform(v, "mm")
    assert abs(mm[-1][1] - (330 / 322 - 1) * 100) < 1e-9
    yy = EO.transform(v, "yy")
    assert yy[-1][0] == "2026-10-01" and abs(yy[-1][1] - (330 / 310 - 1) * 100) < 1e-9
    assert EO.transform([("a", 100.0), ("b", 165.0)], "diff")[-1][1] == 65.0
    # a month the agency never published (2025-10 CPI): no y/y for 2026-10 and no m/m for 2025-11, never a 13- or 2-month change
    gap = [x for x in v if x[0] != "2025-10-01"]
    assert [d for d, _ in EO.transform(gap, "yy")] == ["2026-09-01"] and "2025-11-01" not in dict(EO.transform(gap, "mm"))
    assert abs(dict(EO.transform(gap, "mm"))["2026-10-01"] - (330 / 322 - 1) * 100) < 1e-9
    assert EO.fmt(0.4123, "pct") == "0.4%" and EO.fmt(165, "k") == "165K" and EO.fmt(189000, "kn") == "189K"
    assert EO.fmt(7227, "M") == "7.227M" and EO.fmt(51.04, "n") == "51.0"
    assert EO.et_utc("2026-11-10", 8, 30) == "2026-11-10T13:30:00Z" and EO.et_utc("2026-07-15", 8, 30) == "2026-07-15T12:30:00Z"

    # merge: Nasdaq pair keeps its consensus, gets the official actual by size (smaller = m/m)
    old = [{"name": "CPI", "utc": "2026-11-10T13:30:00Z", "actual": "", "cons": "0.3%", "prev": "0.6%"},
           {"name": "CPI", "utc": "2026-11-10T13:30:00Z", "actual": "", "cons": "3.0%", "prev": "3.1%"},
           {"name": "Fed Waller Speaks", "utc": "2026-11-10T09:00:00Z", "actual": "", "cons": "", "prev": ""}]
    new = [{"name": "CPI", "var": "m", "utc": "x", "actual": "0.4%", "cons": "", "prev": "0.6%", "src": "fred"},
           {"name": "CPI", "var": "y", "utc": "x", "actual": "3.2%", "cons": "", "prev": "3.1%", "src": "fred"},
           {"name": "Core CPI", "var": "m", "utc": "2026-11-10T13:30:00Z", "actual": "0.3%", "cons": "", "prev": "0.3%", "src": "fred"}]
    ff = [{"name": "Core CPI", "var": "m", "date": "2026-11-10", "forecast": "0.2%"}]
    out = EO.merge(old, new, ff)
    assert out[0]["actual"] == "0.4%" and out[0]["cons"] == "0.3%" and out[0]["src"] == "fred"
    assert out[1]["actual"] == "3.2%" and out[1]["cons"] == "3.0%"
    assert out[2]["actual"] == ""
    core = [r for r in out if r["name"] == "Core CPI"]
    assert len(core) == 1 and core[0]["cons"] == "0.2%" and "var" not in core[0]          # FF forecast kept in the history
    assert old[0]["actual"] == ""                                                           # input not mutated

    # one existing row (Nasdaq listed only the m/m): y/y must not overwrite it, whatever the order
    one = [{"name": "CPI", "utc": "t", "actual": "", "cons": "0.3%", "prev": "0.6%"}]
    out = EO.merge(one, list(reversed(new[:2])))
    cpi = [r for r in out if r["name"] == "CPI"]
    assert len(cpi) == 2 and cpi[0]["actual"] == "0.4%" and cpi[1]["actual"] == "3.2%", cpi
    # the day holds only the m/m with its actual and the official y/y is blank: no empty twin (it would sort as the m/m row)
    lone = [{"name": "CPI", "utc": "t", "actual": "0.4%", "cons": "0.3%", "prev": "0.6%"}]
    blank_y = [dict(new[0]), dict(new[1], actual="", prev="")]
    assert len(EO.merge(lone, blank_y)) == 1
    # … and a lone row is never shown under the y/y label
    from wsb.analytics import macro_events as ME0
    labs = [r["label"] for e in ME0.events_for_day("2026-11-10", lone, []) if e["key"] == "cpi" for r in e["rows"]]
    assert labs == ["CPI 月增"], labs
    # a Nasdaq actual already there is never replaced
    done = [{"name": "Nonfarm Payrolls", "utc": "t", "actual": "165K", "cons": "100K", "prev": "60K"}]
    assert EO.merge(done, [{"name": "Nonfarm Payrolls", "var": "", "utc": "t", "actual": "170K", "cons": "", "prev": "60K"}])[0]["actual"] == "165K"

    # fill: schedule rows for a future day, values for a released day; no key → no-op
    real = (EO.schedule, EO.values, EO.FRED_API_KEY)
    try:
        EO.FRED_API_KEY = ""
        assert asyncio.run(EO.fill({}, date(2026, 11, 12), 45)) == 0
        EO.FRED_API_KEY = "k"

        async def sched(today, ahead, force=False):
            return {"2026-11-10": [10], "2026-11-20": [91], "2026-12-30": [10]}

        async def vals(day, rid, cache):
            return [dict(r, utc=EO.et_utc(day, 8, 30)) for r in new]
        EO.schedule, EO.values = sched, vals
        days = {"2026-11-10": {"ts": 0, "rows": [dict(r) for r in old], "final": False}}
        n = asyncio.run(EO.fill(days, date(2026, 11, 12), 45, ff))
        assert n == 2, n
        assert days["2026-11-10"]["rows"][0]["actual"] == "0.4%" and days["2026-11-10"]["src_fallback"] == "fred"
        um = days["2026-11-20"]["rows"]
        assert um[0]["name"] == "Michigan Consumer Sentiment" and um[0]["utc"] == "2026-11-20T15:00:00Z" and um[0]["actual"] == ""
        assert "2026-12-30" not in days                                                    # beyond the window
        # a released day that holds only the m/m (with its actual) still asks the official source for the y/y
        days = {"2026-11-10": {"ts": 0, "rows": [{"name": "CPI", "utc": "t", "actual": "0.4%", "cons": "0.3%", "prev": "0.6%"}], "final": False}}
        asyncio.run(EO.fill(days, date(2026, 11, 12), 45, ff))
        got = [r["actual"] for r in days["2026-11-10"]["rows"] if r["name"] == "CPI"]
        assert got == ["0.4%", "3.2%"], got
    finally:
        EO.schedule, EO.values, EO.FRED_API_KEY = real

    # the rows feed macro_events unchanged
    from wsb.analytics import macro_events as ME
    evs = ME.events_for_day("2026-11-10", EO.merge(old, new, ff), [])
    cpi = next(e for e in evs if e["key"] == "cpi")
    assert cpi["released"] and cpi["rows"][0]["label"] == "核心 CPI 月增" and cpi["rows"][0]["a"] == 0.3 and cpi["dir"] == "hot"
    print("test_econ_official ok")


if __name__ == "__main__":
    main()
