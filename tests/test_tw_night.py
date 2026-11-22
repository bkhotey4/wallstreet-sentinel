"""台指期夜盤（11-22）。Run: python -m tests.test_tw_night"""
from datetime import datetime, timedelta, timezone

from wsb.data import tw_night as N

ROW = ('<tr><td class="12bk"><div align="center">TX </div></td><td class="12bk"><div align="center">{m} </div></td>'
       '<td>35943</td><td>36396</td><td>33719</td><td>{last}</td><td><span class="green">▼-1881</span></td><td><span class="green">▼-5.25%</span></td>'
       '<TD align=right>{vol}</TD><td>-</td><td> - </td><td>33918</td><td>33979</td><td>50560</td><td>27382</td></tr>')
PAGE = ("<p>2026/11/20&nbsp;&nbsp;15:00~次日05:00 盤後交易時段行情表</p><table>"
        + ROW.format(m="202612", last="33919", vol="82477") + ROW.format(m="202701", last="34036", vol="386")
        + '<tr><td>TX</td><td>202612/202701</td><td>112</td><td>112</td><td>79</td><td>79</td><td>76</td><td>84</td><td>154</td><td>60</td><td>8</td><td>298</td><td>1</td><td>1</td><td>1</td></tr></table>')


def test_parse():
    p = N.parse(PAGE)
    assert p["session"] == "2026-11-20" and len(p["rows"]) == 2
    assert p["near"] == {"month": "202612", "open": 35943.0, "high": 36396.0, "low": 33719.0, "last": 33919.0, "chg": -1881.0, "pct": -5.25, "vol": 82477.0}
    assert N.parse("<p>查無資料</p>") == {}
    assert N.light(-5.25) == "🔴" and N.light(1.6) == "🟡" and N.light(0.4) == "🟢"


def test_query_dates():
    tpe = timezone(timedelta(hours=8))
    assert [d.isoformat() for d in N.query_dates(datetime(2026, 11, 22, 10, tzinfo=tpe))][:2] == ["2026-11-23", "2026-11-24"]   # Sunday → Monday
    assert N.query_dates(datetime(2026, 11, 24, 7, tzinfo=tpe))[0].isoformat() == "2026-11-24"


def test_preopen_gate():
    from tools import site_twpreopen as S
    import tools.site_twpreopen as mod
    from wsb.data import tw_night as TN
    real = TN.refresh
    TN.refresh = lambda *a, **k: N.parse(PAGE)
    try:
        px = {"^TWII": {"c": [["2026-11-19", 38426.9], ["2026-11-20", 36033.29]]}}
        tx = S.tx_night(px)
        assert tx["light"] == "🔴" and abs(tx["implied"] - 36033.29 * (1 - 0.0525)) < 1e-6
        px2 = {"^TWII": {"c": [["2026-11-20", 36033.29], ["2026-11-23", 34500.0]]}}
        assert S.tx_night(px2) == {}            # a day session closed after that night: stale
    finally:
        TN.refresh = real


def test_push_line():
    from tools import sec_push as P
    import calendar
    now = calendar.timegm((2026, 11, 23, 0, 0, 0))   # Monday 08:00 Taipei
    d = {"preopen": {"night": {"light": "🔴", "last": 33919.0, "pct": -5.25, "implied": 34141.5}, "mg": {}, "cal": []}}
    a = P.twal_todo(d, {}, now)
    assert [x["kind"] for x in a] == ["pre"] and "夜盤" in P.twal_embed(a[0])["description"]


if __name__ == "__main__":
    test_parse()
    test_query_dates()
    test_preopen_gate()
    test_push_line()
    print("ok tw night")
