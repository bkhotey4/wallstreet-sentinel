"""單季財報、上櫃借券、注意股（11-22）。Run: python -m tests.test_tw_quarter"""
from wsb.data import tw_chips as C

PAGE = ("<table class='hasBorder'><tr><th>公司代號</th><th>公司名稱</th><th>營業收入</th><th>營業毛利（毛損）淨額</th><th>營業利益（損失）</th>"
        "<th>淨利（淨損）歸屬於母公司業主</th><th>基本每股盈餘（元）</th></tr>"
        "<tr class='even'><td>6669</td><td>緯穎</td><td>200,000</td><td>20,000</td><td>15,000</td><td>10,000</td><td>{eps}</td></tr></table>")


def test_parse_and_single_quarter():
    q2 = C.parse_t163(PAGE.format(eps="80.00"))                      # H1: 10,000 net income, EPS 80 on the old share count
    assert q2["6669"] == {"name": "緯穎", "rev": 200000.0, "gross": 20000.0, "op": 15000.0, "ni": 10000.0, "eps": 80.0}
    q3 = {"6669": {"name": "緯穎", "rev": 500000.0, "gross": 45000.0, "op": 35000.0, "ni": 25000.0, "eps": 100.0}}  # split: EPS basis halved
    v = C.fin_view({"115Q2": q2, "115Q3": q3})
    r = v["rows"][0]
    assert v["q"] == "115Q3" and abs(r["rev"] - 300000) < 1e-6 and abs(r["gm"] - 25000 / 300000 * 100) < 1e-9
    assert abs(r["eps"] - 15000 * 100 / 25000) < 1e-9                 # 60 元 on the current basis, not 100 − 80 = 20
    assert r["eps_prev"] is None                                       # Q2 alone needs Q1 too
    v2 = C.fin_view({"115Q1": {"6669": {"name": "緯穎", "rev": 100000.0, "gross": 9000.0, "op": 7000.0, "ni": 4000.0, "eps": 32.0}},
                     "115Q2": q2, "115Q3": q3})
    r2 = v2["rows"][0]
    assert abs(r2["eps_prev"] - 6000 * 100 / 25000) < 1e-9 and abs(r2["rev_qoq"] - 200.0) < 1e-9     # Q2 alone 100,000 → Q3 300,000


def test_otc_and_warn():
    s = C.parse_sbl_otc([{"Date": "1151120", "SecuritiesBorrowingBalanceOfTheMarketDay": "2,384,000", "SecuritiesBorrowingBalancePreviousDay": "2379000"}])
    assert s == {"date": "1151120", "total": 2384000.0, "prev": 2379000.0, "skipped": 0}
    w = C.parse_warn([{"Code": "", "Name": ""}], [{"SecuritiesCompanyCode": "1569", "CompanyName": "濱川", "TradingInformation": "跌幅達41.4%"}])
    assert w == [{"code": "1569", "name": "濱川", "why": "跌幅達41.4%", "board": "上櫃", "date": None}]
    from datetime import date
    assert C.latest_quarters(date(2026, 11, 22)) == [(115, 3), (115, 2), (115, 1)]
    assert C.latest_quarters(date(2027, 4, 1)) == [(115, 4), (115, 3), (115, 2)]


def test_large_json_and_csv():
    """11-26: TAIFEX's large-trader table came back as JSON instead of CSV and the card silently went blank."""
    import json as _j
    js = _j.dumps([{"Date": "20261125", "Contract": "TX", "ContractName": "臺股期貨", "SettlementMonth": "999912", "TypeOfTraders": t,
                    "Top5Buy": "97592", "Top5Sell": "70972", "Top10Buy": b10, "Top10Sell": "98606", "OIOfMarket": "141906"}
                   for t, b10 in (("0", "108908"), ("1", "106853"))]
                  + [{"Date": "20261125", "Contract": "TX", "SettlementMonth": "202612", "TypeOfTraders": "0", "Top5Buy": "1"}], ensure_ascii=False)
    o = C.parse_large(js)
    assert o["all"] == {"date": "20261125", "top5_net": 26620.0, "top10_net": 10302.0, "oi": 141906.0} and o["inst"]["top10_net"] == 8247.0
    csv_text = chr(10).join(["日期,商品,名稱,月份,類別,b5,s5,b10,s10,oi", "20261125,TX,臺股期貨,999912,0,97592,70972,108908,98606,141906", ""])
    assert C.parse_large(csv_text)["all"]["top10_net"] == 10302.0


def test_relay_keeps_last_good_part():
    from tools import relay_push as RP
    old = {"fetched": "11-26 10:43", "large": {"all": {"date": "20261125"}}, "mratio": {"date": "20261125"}, "warn": [1]}
    new = {"fetched": "11-26 22:47", "large": {}, "mratio": None, "warn": [2]}
    assert RP.merge_empty(old, new) == {"fetched": "11-26 22:47", "large": {"all": {"date": "20261125"}}, "mratio": {"date": "20261125"}, "warn": [2]}
    assert RP.keep(["research_feed/tw_chips_seed.json", "research_feed/holdings.json", "site/x_seed.json"]) == ["research_feed/tw_chips_seed.json"]
    from datetime import datetime, timezone, timedelta
    t = lambda h: datetime(2026, 11, 26, h, 0, tzinfo=timezone(timedelta(hours=8))).timestamp()  # noqa: E731
    assert RP.due({}, t(10)) and not RP.due({}, t(3))
    assert not RP.due({"running": True, "started": t(10) - 600}, t(10)) and RP.due({"running": True, "started": t(10) - 4 * 3600}, t(10))
    assert not RP.due({"started": t(10) - 3600}, t(10))


def test_large_opt():
    rows = [{"Contract": "TXO", "CallPut": "買權", "SettlementMonth": "999912", "TypeOfTraders": "1", "Top10Buy": "29116", "Top10Sell": "40854", "OIOfMarket": "95013", "Date": "20261120"},
            {"Contract": "TXO", "CallPut": "賣權", "SettlementMonth": "999912", "TypeOfTraders": "1", "Top10Buy": "7122", "Top10Sell": "8873", "OIOfMarket": "28549", "Date": "20261120"},
            {"Contract": "CA", "CallPut": "買權", "SettlementMonth": "999912", "TypeOfTraders": "1", "Top10Buy": "1", "Top10Sell": "0"}]
    o = C.parse_large_opt(rows)
    assert o["inst"]["call"]["top10_net"] == -11738 and o["inst"]["put"]["top10_net"] == -1751 and "all" not in o


def test_margin_ratio_and_daytrade():
    mg = {"date": "20261120", "tables": [{"data": [["融資(交易單位)", "", "", "", "", "8,398,744"], ["融資金額(仟元)", "", "", "", "484,368,360", "1,000"]]},
                                         {"data": [["2330", "台積電", "", "", "", "", "1", "", "", "", "", "", "", "", "", ""],
                                                   ["9999", "沒收盤", "", "", "", "", "5", "", "", "", "", "", "", "", "", ""]]}]}
    assert C.margin_ratio(mg, [{"Code": "2330", "ClosingPrice": "1,500.00", "Date": "1151119"}]) is None   # 11-25: closes of another day
    r = C.margin_ratio(mg, [{"Code": "2330", "ClosingPrice": "1,500.00", "Date": "1151120"}])
    assert abs(r["ratio"] - 1 * 1000 * 1500 / (1000 * 1000) * 100) < 1e-9          # 1 lot × 1,500 ÷ 1,000 thousand
    dt = C.parse_daytrade({"date": "20261120", "tables": [{"title": "115年11月20日 當日沖銷交易統計資訊", "data": [["4,460,672,000", "26.1", "x", "34.48"]]}]})
    assert dt == {"date": "20261120", "share_pct": 26.1, "value_pct": 34.48}


def test_pmi_and_unemp():
    from wsb.data import tw_macro2 as M
    csv = "﻿" + "\n".join(["Date,PMI,NMI", "201207,47.1,-", "202610,62.5,55.4"]) + "\n"
    assert M.parse_pmi(csv) == [{"ym": "2012-07", "pmi": 47.1, "nmi": None},
                                                                                     {"ym": "2026-10", "pmi": 62.5, "nmi": 55.4}]
    xml = ("<DataCollection><失業率><年月別_Year_and_month>1978</年月別_Year_and_month><總計_Total_百分比>1.67</總計_Total_百分比></失業率>"
           "<失業率><年月別_Year_and_month>2026M09</年月別_Year_and_month><總計_Total_百分比>3.36</總計_Total_百分比>"
           "<age_20-24_百分比>11.85</age_20-24_百分比></失業率></DataCollection>")
    u = M.parse_unemp(xml)
    assert len(u) == 1 and u[0]["ym"] == "2026-09" and u[0]["total"] == 3.36 and u[0]["y20_24"] == 11.85   # annual rows skipped


def test_pulse_months_and_stamp():
    from tools import site_tw_macro2 as S, site_stamp as ST
    # PMI file late (stops at 2026-09) while unemployment already has 2026-10: the newer month still gets a row
    m = S.table_months([{"ym": "2026-09"}], [{"ym": "2026-09"}, {"ym": "2026-10"}], [{"ym": "2026-08"}])
    assert m == ["2026-10", "2026-09", "2026-08"]
    assert S.table_months([], [], [{"ym": f"2020-{i:02d}"} for i in range(1, 13)], n=3) == ["2020-12", "2020-11", "2020-10"]
    assert "twpulse" in ST.CARD["sec_tw_pulse"] and "twpulse" in ST.SOURCES


def test_wage():
    import html, json
    from wsb.data import tw_macro2 as M
    from tools import site_tw_macro2 as S
    series = [{"Title": "工業及服務業每人每月經常性薪資", "data": [{"Date": "2026/9/1", "Value": "49,477"}, {"Date": "2025/9/1", "Value": "48,124"}]},
              {"Title": "工業及服務業每人每月總薪資", "data": [{"Date": "2026/9/1", "Value": "60,297"}, {"Date": "2025/9/1", "Value": "57,520"}]},
              {"Title": "別的", "data": [{"Date": "2026/9/1", "Value": "1"}]}]
    page = f'<input type="hidden" id="ContentPlaceHolder1_hidChartData" value="{html.escape(json.dumps(series, ensure_ascii=False))}" />'
    w = M.parse_wage(page)
    assert w == [{"ym": "2025-09", "reg": 48124.0, "total": 57520.0}, {"ym": "2026-09", "reg": 49477.0, "total": 60297.0}]
    v = S._wage(w, {"2026-09": 2.73})
    r = v["rows"][-1]
    assert abs(r["yoy"] - (49477 / 48124 - 1) * 100) < 1e-9 and abs(r["real"] - ((49477 / 48124) / 1.0273 - 1) * 100) < 1e-9
    assert "幾乎被物價吃掉" in v["lead"] and M.parse_wage("<html></html>") == []


def test_forecast_view():
    a16 = [{"年度": "115", "季別": "3", "公司代號": "2412", "公司名稱": "中華電", "財測序號": "0", "涵蓋期間": "一、二、三、四",
            "當季經會計師查核或核閱數": "11546076", "截至當季經會計師查核或核閱數": "32139221.00",
            "當季稅前(綜合)損益預測數": "9455288~10182350", "截至當季稅前(綜合)損益預測數": "27679757~28442612"}]
    a15 = [{"年度": "115", "季別": "3", "公司代號": "2412", "公司名稱": "中華電", "財測序號": "0", "涵蓋期間": "一、二、三、四",
            "截至該季經會計師查核或核閱數": "32139221.00", "截至該季綜合損益預測數": "9455288~10182350"},
           {"年度": "115", "季別": "3", "公司代號": "3702", "公司名稱": "大聯大", "財測序號": "0", "涵蓋期間": "三",
            "截至該季經會計師查核或核閱數": "27185702.00", "截至該季綜合損益預測數": "10422000~11639000"},
           {"年度": "115", "季別": "3", "公司代號": "2515", "公司名稱": "中工", "財測序號": "0", "截至該季綜合損益預測數": "1"},
           {"年度": "115", "季別": "3", "公司代號": "2515", "公司名稱": "中工", "財測序號": "2", "截至該季綜合損益預測數": "-72844",
            "截至該季經會計師查核或核閱數": "853236"}]
    snaps = {"115Q3": {"3702": {"ni": 24558603.0}}, "115Q2": {"3702": {"ni": 14168686.0}}}
    v = {r["code"]: r for r in C.forecast_view(a15, a16, snaps)}
    c = v["2412"]
    assert c["exact"] and c["q_where"] == "above" and c["ytd_where"] == "above" and not c["q_close"]
    w = v["3702"]
    assert not w["exact"] and w["q_act"] == 24558603.0 - 14168686.0 and w["q_where"] == "below" and w["q_close"] and w["ytd_fc"] is None
    assert v["2515"]["rev"] == "2" and v["2515"]["q_fc"] == (-72844.0, -72844.0)
    assert C._range("9455288~10182350") == (9455288.0, 10182350.0) and C._range("x") is None


def test_stat():
    """主計總處統計資訊網: exact titles only, first value per month wins (CPI page repeats 年增率, export page repeats months)."""
    import html as _h
    import json as _j
    from wsb.data import tw_macro2 as M
    ser = [{"Title": "消費者物價指數", "data": [{"Date": "2026/10/1", "Value": "112.90"}]},
           {"Title": "消費者物價指數年增率", "data": [{"Date": "2026/10/1", "Value": "2.33"}, {"Date": "2026/9/1", "Value": "2.70"}]},
           {"Title": "消費者物價指數年增率", "data": [{"Date": "2026/10/1", "Value": "9.99"}]},
           {"Title": "外銷訂單", "data": [{"Date": "2026/10/1", "Value": "123,820"}, {"Date": "2025/10/1", "Value": "69,434"}]}]
    page = f'<input id="ContentPlaceHolder1_hidChartData" value="{_h.escape(_j.dumps(ser, ensure_ascii=False))}">'
    rows = M.parse_stat(page)
    assert rows["2026-10"]["cpi_yoy"] == 2.33 and "cpi" not in rows["2026-10"] and rows["2026-10"]["orders"] == 123820.0
    d = {"stat": [rows[k] for k in sorted(rows)]}
    assert M.latest_stat(d, "cpi_yoy") == ("2026-10", 2.33) and M.latest_stat(d, "exports") is None


def test_overlay():
    """Official months newer than the CBC / 國發會 series are appended for readers, with unit conversion; older ones never overwrite."""
    from wsb.data import twmacro as TM
    d = {"cbc": {"fxres": [["2026-09", 600745.0]], "m1b": [["2026-09", 7.2]]}, "ndc": {"ip": [["2026-10", 150.0]]}}
    stat = [{"ym": "2026-09", "fxres": 600.74, "m1b_yoy": 7.2, "ip": 141.0}, {"ym": "2026-10", "fxres": 596.44, "m1b_yoy": 7.08, "ip": 151.3}]
    out = TM.overlay(d, stat)
    assert out["cbc"]["fxres"][-1] == ["2026-10", 596440.0] and out["cbc"]["m1b"][-1] == ["2026-10", 7.08]
    assert out["ndc"]["ip"] == [["2026-10", 150.0]] and out["official"] == {"cbc.fxres": ["2026-10"], "cbc.m1b": ["2026-10"]}


if __name__ == "__main__":
    test_large_json_and_csv()
    test_relay_keeps_last_good_part()
    test_overlay()
    test_stat()
    test_forecast_view()
    test_wage()
    test_pulse_months_and_stamp()
    test_pmi_and_unemp()
    test_margin_ratio_and_daytrade()
    test_large_opt()
    test_parse_and_single_quarter()
    test_otc_and_warn()
    print("ok tw quarter")
