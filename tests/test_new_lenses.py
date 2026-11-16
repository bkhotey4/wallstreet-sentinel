"""2026-11-16 使用者選的第 1–8、12 項（被迫進出的錢、債務到期牆、股票供給、韓國出口、中國、法院與監管、休市日曆），不連網。
Run: python -m tests.test_new_lenses"""
from __future__ import annotations

import pathlib
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wsb.data import exchange_cal as XC  # noqa: E402
from wsb.data import forced_flows as FF  # noqa: E402
from wsb.data import korea_exports as KE  # noqa: E402
from wsb.data import china_watch as CW  # noqa: E402
from wsb.data import rulings as RL  # noqa: E402
from wsb.analytics import corp_funding as CF  # noqa: E402

HOL = XC.us_holidays(2022, 2027)
EARLY = XC.us_early(2022, 2027, HOL)


def us(d):
    return d.weekday() < 5 and d.isoformat() not in HOL


def tw(d):
    return d.weekday() < 5


def test_exchange_calendar():
    assert "2026-11-26" in HOL and "2026-11-27" in EARLY and "2026-12-24" in EARLY
    assert "2026-07-03" in HOL and "2026-07-02" not in EARLY            # July 4 on a Saturday: Friday off, no half day
    assert "2025-07-03" in EARLY                                         # Thursday before Independence Day
    assert XC.us_session_tpe(date(2026, 11, 16)) == "22:30–隔天 05:00"   # winter time
    assert XC.us_session_tpe(date(2026, 7, 1)) == "21:30–隔天 04:00"     # summer time
    assert XC.us_session_tpe(date(2026, 11, 27), early=True) == "22:30–隔天 02:00"
    js = {"data": [["2026-12-25", "行憲紀念日", ""], ["2027-01-04", "國曆新年開始交易日", ""], ["2027-02-02", "市場無交易，僅辦理結算交割作業。", ""]]}
    rows = XC.parse_tw(js)
    assert [r["open"] for r in rows] == [False, True, False]
    d = {"tw": {"2026": rows[:1], "2027": rows[1:]}}
    up = XC.upcoming(date(2026, 11, 16), 45, d)
    assert [(r["date"], r["us"], r["tw"]) for r in up][:4] == [("2026-11-26", "closed", "open"), ("2026-11-27", "early", "open"),
                                                                ("2026-12-24", "early", "open"), ("2026-12-25", "closed", "closed")]


def test_index_dates_and_volume():
    ev = FF.index_dates(2024, 2026, us, tw, lambda d: d.isoformat() in EARLY)
    got = {(e["kind"], e["date"]) for e in ev}
    assert ("sp", "2026-12-18") in got and ("tw50", "2026-12-18") in got
    assert ("sp", "2026-06-18") in got                                   # 3rd Friday 6/19 is Juneteenth → Thursday
    assert ("russell", "2026-06-26") in got and ("russell", "2026-12-11") in got and ("russell", "2025-12-12") not in got
    assert ("msci", "2026-11-30") in got and ("msci", "2025-11-24") in got and ("msci", "2024-11-25") in got   # Black Friday rule
    assert ("msci", "2026-02-27") in got
    dts = [f"2026-01-{i:02d}" for i in range(1, 23)]
    vols = [100.0] * 21 + [250.0]
    assert FF.vol_ratio(dts, vols, "2026-01-22") == 2.5 and FF.vol_ratio(dts, vols, "2026-02-01") is None


def test_mechanical_funds():
    calm = [100.0]
    for i in range(299):
        calm.append(calm[-1] * (1.0005 if i % 2 else 0.9995))
    v = FF.vol_control_view(calm)
    assert v["now"] == FF.CAP                                             # tiny volatility → capped at 150 %
    rough = [100.0]
    for i in range(299):
        rough.append(rough[-1] * (1.03 if i % 2 else 0.97))
    assert FF.vol_control(rough) < 0.25                                   # ~48 % annual vol → about a fifth in stocks
    up = [100 + i for i in range(300)]
    t = FF.trend_view(up)
    assert t["score"] == 1 and t["flips"][21]["price"] == up[-21] and t["flips"][21]["dist"] < 0
    down = list(reversed(up))
    assert FF.trend_view(down)["score"] == -1
    pm = FF.pension_move(0.5, 100.0, 0.10, 0.0)
    assert abs(pm["w1"] - 55 / 105) < 1e-9 and pm["move"] < 0              # stocks ran ahead → stocks to reduce
    assert FF.quarter_start(date(2026, 11, 16)) == date(2026, 10, 1)


def test_forced_alerts():
    v = {"events": [{"date": "2026-11-30", "kind": "msci", "market": "us"}, {"date": "2026-12-18", "kind": "sp", "market": "us"}],
         "trend": {"^GSPC": {"score": -1 / 3, "prev": 1 / 3, "asof": "2026-11-13", "flips": {}}},
         "volctl": {"now": 0.4, "week": 0.55}, "asof": {"^GSPC": "2026-11-13"}}
    keys = [a["key"] for a in FF.alerts(v, date(2026, 11, 27))]          # Friday: Monday's MSCI day counts as next
    assert "forced:ev:msci:2026-11-30" in keys and "forced:trend:^GSPC:2026-11-13:-" in keys and "forced:volctl:2026-11-13" in keys
    assert not [k for k in (a["key"] for a in FF.alerts(v, date(2026, 11, 20))) if k.startswith("forced:ev")]


def test_corp_funding():
    ylds = {"ig": 0.05, "bbb": 0.06, "hy": 0.08}
    b = {"mat1": 100.0, "mat2": 50.0, "ltd": 1000.0, "interest_ttm": 30.0, "ebit_ttm": 300.0, "cash": 40.0, "ocf_ttm": 80.0, "capex_ttm": 60.0}
    assert CF.tier(b) == "ig" and CF.tier(dict(b, ebit_ttm=150.0)) == "bbb" and CF.tier(dict(b, ebit_ttm=-5.0)) == "hy"
    r = CF.refi(b, ylds)
    assert abs(r["coupon"] - 0.03) < 1e-9 and abs(r["extra"] - 150 * 0.02) < 1e-9 and abs(r["extra_ebit"] - 0.01) < 1e-9
    assert abs(r["self_pay"] - 0.6) < 1e-9                                 # (40 cash + 20 free cash flow) / 100 due
    cache = {"A": {"bs": b}, "B": {"bs": dict(b, deposits=5.0)}, "C": {"bs": {"wsh": 110.0, "wsh_yago": 100.0, "buyback_ttm": 5.0, "issue_ttm": 1.0},
                                                                    "offer": [{"form": "424B5", "date": "2026-11-01", "url": "u"}]}}
    names = {"A": {"zh": "甲", "kind": "corp"}, "B": {"zh": "乙", "kind": "auto"}, "C": {"zh": "丙", "kind": "corp"}}
    w = CF.wall(cache, names)
    assert w["n"] == 1 and w["tot"]["mat1"] == 100.0                       # B has deposits → a bank → left out
    sp = {r["sym"]: r for r in CF.supply(cache, names, {"C": 400.0})}
    assert abs(sp["C"]["chg"] - 0.10) < 1e-9 and sp["C"]["net"] == 4.0 and sp["C"]["net_yield"] == 0.01


def test_split_safe_shares():
    from wsb.data.distress_data import parse_balance
    f = lambda v, s, e, accn: {"val": v, "start": s, "end": e, "accn": accn, "filed": "2026-11-01"}  # noqa: E731
    cf = {"facts": {"us-gaap": {
        "Assets": {"units": {"USD": [{"val": 10.0, "end": "2026-09-30", "filed": "2026-11-01"}]}},
        "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": [
            f(1000.0, "2026-07-01", "2026-09-30", "Q3"), f(990.0, "2025-07-01", "2025-09-30", "Q3"),   # restated for a 10:1 split
            f(99.0, "2025-07-01", "2025-09-30", "OLD")]}}}}}
    b = parse_balance(cf)
    assert abs(b["wsh"] / b["wsh_yago"] - 1 - 1000 / 990 + 1) < 1e-9


def test_korea():
    page = ('<a href="javascript:" data-mi="2891" data-bbs="1362" data-id="10182926" data-url="f245" class="nttInfoBtn" '
            'title="2026년 11월 1일 ~ 11월 10일 수출입 현황 [잠정치]"></a><a href="javascript:" data-mi="2891" data-bbs="1362" '
            'data-id="1" data-url="ab" class="nttInfoBtn" title="2026년 9월 월간 수출입 현황 [확정치]"></a>')
    rows = KE.parse_list(page)
    assert [r["key"] for r in rows] == ["2026-11-10"] and rows[0]["u"] == "f245"
    assert KE.key_of("2026년 10월 수출입 현황 [잠정치]") == ("2026-10-M", "month")
    det = ("◇ 동기간 수출은 335 억 달러 로 전년동기대비 111.9% 증가 , 수입은 247 억 달러 → 반도체 (166 억 달러 ) 수출 "
           "※ 조업일수 고려 시 일평균수출액 [(’25.11.) 22.6, (’26.11.) 44.6 억 달러 ] 97.7% 증가")
    v = KE.parse_detail(det)
    assert (v["exp"], v["yoy"], v["chip"], v["day_yoy"]) == (335.0, 111.9, 166.0, 97.7)
    assert KE.parse_detail("수출은 158억달러로 전년동기대비 3.2% 감소")["yoy"] == -3.2
    assert KE.released("2026-11-10") == date(2026, 11, 11) and KE.released("2026-12-M") == date(2027, 1, 1)
    att = ("<p>수출현황</p><p>ㅇ (주요품목) 전년동기대비 반도체 (331.2%) , 석유제품 (100.7%) 등 증가, 승용차 (△4.3%) 등 감소 "
           "- 반도체 수출 비중은 49.7%로 25.3%p 증가 ㅇ (주요국가) 중국 (148.0%) , 미국 (163.6%) , 대만 (182.5%) , 일본 (△2.0%) 등</p>")
    a = KE.parse_att(att)
    assert a["chip_yoy"] == 331.2 and a["chip_share"] == 49.7 and a["ctry"] == {"中國": 148.0, "美國": 163.6, "台灣": 182.5, "日本": -2.0}
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Contents/section0.xml", att)
    assert "주요품목" in KE.read_hwpx(buf.getvalue())
    v2 = KE.view({"rel": {"2026-11-10": {"exp": 335.0, "chip_share": 49.7}}})
    assert abs(v2["rows"][0]["chip"] - 335.0 * 0.497) < 1e-9
    vw = {"rows": [{"key": "2026-11-10", "exp": 335.0}]}
    assert KE.alerts(vw, date(2026, 11, 12)) and not KE.alerts(vw, date(2026, 11, 16))


def test_china():
    s = {"2025-06-01": 100.0, "2025-07-01": 100.0, "2025-08-01": 100.0, "2026-06-01": 120.0, "2026-07-01": 110.0, "2026-08-01": 130.0}
    y = CW.yoy(s)
    assert y["date"] == "2026-08-01" and abs(y["yoy"] - 0.30) < 1e-9 and abs(y["yoy3"] - 0.20) < 1e-9
    mk = CW.market_view({"CNY=X": {"d": ["2026-11-13"], "c": [7.0]}, "CNH=X": {"d": ["2026-11-13"], "c": [7.07]}})
    assert abs(mk["gap"]["now"] - 0.01) < 1e-9


def test_rulings():
    page = ("<tr><td style='x'>73</td><td style='x'>9/25/26</td><td style='x'>26A388</td>"
            "<td><a href='/opinions/25pdf/26a388_q86b.pdf' target='_blank' title=\"The Court grants the application.\">People v. Onder</a></td>"
            "<td>PC</td><td>609/2</td></tr>")
    r = RL.parse_scotus(page)
    assert r[0]["date"] == "2026-09-25" and r[0]["title"] == "People v. Onder" and r[0]["url"].startswith("https://www.supremecourt.gov/opinions/")
    xml = ("<rss><channel><item><title>SEC Adopts Amendments to Treasury Clearing</title><link>https://sec.gov/a</link>"
           "<pubDate>Wed, 04 Nov 2026 15:00:00 -0500</pubDate><description>x</description></item>"
           "<item><title>SEC Charges Adviser With Fraud</title><link>https://sec.gov/b</link><pubDate>Wed, 04 Nov 2026 15:00:00 -0500</pubDate></item></channel></rss>")
    it = RL.parse_rss(xml, "sec", RL.FEEDS[0][3])
    assert [x["url"] for x in it] == ["https://sec.gov/a"] and it[0]["date"] == "2026-11-04"
    assert RL.topic("Trump v. Cook: for-cause removal of a Federal Reserve governor")["sym"] == "^TNX"
    assert RL.topic("Learning Resources v. Trump (tariffs under IEEPA)")["sym"] == "^GSPC"
    now = 2_000_000.0
    d = {"items": [dict(it[0], topic="證券與市場規則", sym="^GSPC", sym_zh="標普 500", seen=1_000.0),
                   {"src": "scotus", "date": "2026-11-15", "title": "X v. Y (tariffs)", "url": "https://sc/x", "topic": "關稅與貿易",
                    "sym": "^GSPC", "sym_zh": "標普 500", "seen": now - 600}]}
    assert [a["item"]["url"] for a in RL.alerts(d, now)] == ["https://sc/x"]       # the first fill (seen at 1,000) is never pushed


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
