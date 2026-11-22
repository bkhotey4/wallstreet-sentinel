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
    assert s == {"date": "1151120", "total": 2384000.0, "prev": 2379000.0}
    w = C.parse_warn([{"Code": "", "Name": ""}], [{"SecuritiesCompanyCode": "1569", "CompanyName": "濱川", "TradingInformation": "跌幅達41.4%"}])
    assert w == [{"code": "1569", "name": "濱川", "why": "跌幅達41.4%", "board": "上櫃", "date": None}]
    from datetime import date
    assert C.latest_quarters(date(2026, 11, 22)) == [(115, 3), (115, 2), (115, 1)]
    assert C.latest_quarters(date(2027, 4, 1)) == [(115, 4), (115, 3), (115, 2)]


if __name__ == "__main__":
    test_parse_and_single_quarter()
    test_otc_and_warn()
    print("ok tw quarter")
