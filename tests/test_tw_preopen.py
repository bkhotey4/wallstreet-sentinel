"""台股開盤前預估＋被迫賣方：parsers, ADR premium math, T+3 calendar, leveraged-ETF estimate, card wording (no network)."""
from datetime import date, timedelta

from wsb.data import tw_preopen as P


def _series(n, start, f):
    d0 = date(2025, 1, 1)
    out, i, k = [], 0, 0
    while len(out) < n:
        d = d0 + timedelta(days=i)
        i += 1
        if d.weekday() < 5:
            out.append([d.isoformat(), f(k)])
            k += 1
    return out


def test_parsers():
    mg = {"stat": "OK", "tables": [{"data": [["融資(交易單位)", "1", "2", "3", "8,947,612", "8,398,744"],
                                             ["融資金額(仟元)", "20,552,809", "60,170,406", "9,523,496", "484,368,360", "435,227,267"]]}]}
    assert P.parse_mg(mg) == (4843.68, 4352.27)
    assert P.parse_mg({"stat": "很抱歉，沒有符合條件的資料!"}) is None
    bfi = {"stat": "OK", "data": [["自營商(自行買賣)", "8", "13", "-5,067,838,740"], ["自營商(避險)", "54", "83", "-29,015,401,380"],
                                  ["投信", "24", "31", "-7,346,992,003"], ["外資及陸資(不含外資自營商)", "1", "2", "-9,510,543,572"],
                                  ["外資自營商", "0", "0", "0"], ["合計", "1", "2", "-50,940,775,695"]]}
    b = P.parse_bfi(bfi)
    assert b == {"self": -50.7, "hedge": -290.2, "trust": -73.5, "foreign": -95.1, "total": -509.4}, b
    js = {"chart": {"result": [{"meta": {"gmtoffset": 28800, "regularMarketTime": 1795190400, "regularMarketPrice": 2010.0},
                                "timestamp": [1795017600, 1795104000], "indicators": {"quote": [{"close": [2100.0, 2000.0]}]}}]}}
    c = P.parse_chart(js)["c"]
    assert c[-1][1] == 2010.0 and len(c) == 3, c                  # a newer live price is appended as its own day


def test_adr_math():
    tw = _series(300, 0, lambda k: 1000.0)
    fx = _series(300, 0, lambda k: 32.0)
    adr = _series(300, 0, lambda k: 1000 / 32 * 5 * (1.10 if k < 299 else 1.02))   # 10% premium, then 2% today
    v = P.adr_view(adr, tw, fx)
    assert abs(v["now"] - 2.0) < 1e-6 and v["pct"] <= 1 and abs(v["med20"] - 10.0) < 1e-6, v
    # premium back to 10% → 2330 ≈ x / 1.10 where x = 1020
    assert abs(v["mid"] - 1020 / 1.10) < 0.2 and v["chg_mid"] < 0
    assert P.adr_light(v["pct"]) == "🔴" and P.adr_light(50) == "🟢" and P.adr_light(90) == "🟡" and P.adr_light(None) == "⚪"


def test_calendar_and_lights():
    closed = {"2026-11-24": "測試休市"}
    assert P.tw_days_after("2026-11-20", 3, {}) == "2026-11-25"           # Fri + 3 trading days = Wed
    assert P.tw_days_after("2026-11-20", 3, closed) == "2026-11-26"       # a holiday pushes it out
    twii = [["2026-11-19", 38427.0], ["2026-11-20", 36033.0]]
    mg = {"2026-11-20": [4843.68, 4352.27]}
    cal = P.call_calendar(["2026-11-19", "2026-11-20"], twii, mg, {})
    assert len(cal) == 1 and cal[0]["topup"] == "2026-11-24" and cal[0]["dispose"] == "2026-11-25" and cal[0]["mg"] < -10
    assert P.mg_light(-10.1) == "🔴" and P.mg_light(-3) == "🟡" and P.mg_light(1) == "🟢"


def test_lev_etf():
    nav = {"00631L": {"name": "元大台灣50正2", "units": 10852848000.0, "nav": 21.29, "prev_nav": 24.62, "date": "2026-11-20"},
           "0050": {"units": 1.0, "nav": 84.68, "prev_nav": 90.05}}
    v = P.lev_etf(nav)
    assert v["size"] == 2672 and -330 < v["trade"] < -310, v                # 2×1×(−5.96%)×2,672 億
    assert P.lev_etf({}) is None


def test_revised_day_is_read_again():
    """11/25: BFI82U said 投信 +535.3 in the afternoon and +550.3 that night; the card kept the first number."""
    import asyncio
    import tempfile
    from datetime import datetime, timezone
    from pathlib import Path
    ts = lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()   # noqa: E731
    assert not P.settled("2026-11-25", None)                              # old cache without a stamp: read once more
    assert not P.settled("2026-11-25", ts("2026-11-25T08:00:00"))         # 16:00 Taipei, first version
    assert not P.settled("2026-11-25", ts("2026-11-26T03:00:00"))
    assert P.settled("2026-11-25", ts("2026-11-26T04:30:00"))             # 12:30 Taipei the next day: final
    vals, real = [53531942295, 55034724295], (P.FILE, P.http.get, P.time.time)
    clock = [ts("2026-11-25T08:00:00")]
    n = {"bfi": 0}

    async def get(url, **k):
        if url == P.U_BFI:
            n["bfi"] += 1
            return {"stat": "OK", "data": [["自營商(避險)", "0", "0", "-5470364428"], ["投信", "0", "0", str(vals[min(n["bfi"], 2) - 1])]]}
        if url == P.U_MG:
            return {"stat": "x"}
        raise RuntimeError("no yahoo")
    with tempfile.TemporaryDirectory() as td:
        try:
            P.FILE, P.http.get, P.time.time = Path(td) / "x.json", get, lambda: clock[0]
            P._save({"px": {"2330.TW": {"c": [["2026-11-25", 2150.0]]}}})
            assert asyncio.run(P.refresh())["bfi"]["2026-11-25"]["trust"] == 535.3
            clock[0] = ts("2026-11-25T14:00:00")
            assert asyncio.run(P.refresh())["bfi"]["2026-11-25"]["trust"] == 550.3
            clock[0] = ts("2026-11-26T05:00:00")
            asyncio.run(P.refresh())
            clock[0] = ts("2026-11-26T09:00:00")
            asyncio.run(P.refresh())
            assert n["bfi"] == 3, n                                       # final: not read again
        finally:
            P.FILE, P.http.get, P.time.time = real


def test_card_words():
    from tools import site_twpreopen as S
    tw = _series(300, 0, lambda k: 1000.0)
    fx = _series(300, 0, lambda k: 32.0)
    adr = _series(300, 0, lambda k: 1000 / 32 * 5 * 1.10)
    d = {"px": {"TSM": {"c": adr, "t": 1795190400}, "2330.TW": {"c": tw}, "TWD=X": {"c": fx}, "^TWII": {"c": tw}},
         "mg": {tw[-1][0]: [4843.68, 4352.27]}, "bfi": {tw[-1][0]: {"hedge": -290.2, "foreign": -95.1}}, "ts": 1795190400, "px_ts": 1795190400}
    v = P.view_from(d, {}, {})
    h = S.body(v)
    assert "一句話看懂" in h and "百分位" in h and "融資" in h and "T+3" in h, h[:300]
    for bad in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "加碼參考區", "進場參考區", "精選池"):
        assert bad not in h, bad


if __name__ == "__main__":
    test_parsers(); test_adr_math(); test_calendar_and_lights(); test_lev_etf(); test_revised_day_is_read_again(); test_card_words(); print("ok")
