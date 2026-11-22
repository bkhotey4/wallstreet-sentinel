"""借券放空集中度（11-22）。Run: python -m tests.test_tw_squeeze"""
from wsb.data import tw_chips as C


def test_squeeze_view():
    t = {"date": "20261120", "data": [
        ["8996", "高力", "", "", "", "", "", "", "8,816,000", "0", "44,000", "0", "8,772,000", "1", " "],
        ["2330", "台積電", "", "", "", "", "", "", "24,119,514", "39,000", "3,000", "0", "24,155,514", "1", " "],
        ["0050", "元大台灣50", "", "", "", "", "", "", "9,000,000", "0", "0", "0", "9,000,000", "1", " "],     # ETF: no 4-digit company row in basics
        ["1234", "太小", "", "", "", "", "", "", "100", "0", "0", "0", "500", "1", " "]]}
    day = [{"Code": "8996", "TradeVolume": "137,500", "ClosingPrice": "923.00"}, {"Code": "2330", "TradeVolume": "60,000,000", "ClosingPrice": "2000"}]
    basic = [{"公司代號": "8996", "已發行普通股數或TDR原股發行股數": "93,500,000"}, {"公司代號": "2330", "已發行普通股數或TDR原股發行股數": "25,932,733,242"},
             {"公司代號": "1234", "已發行普通股數或TDR原股發行股數": "1000000"}]
    v = C.squeeze_view(t, day, basic)
    r = {x["code"]: x for x in v["rows"]}
    assert set(r) == {"8996", "2330"}                     # ETF without share count and tiny balances are left out
    assert abs(r["8996"]["pct"] - 8772000 / 93500000 * 100) < 1e-9 and abs(r["8996"]["dtc"] - 8772000 / 137500) < 1e-9
    assert r["8996"]["chg"] == -44000 and abs(r["8996"]["value"] - 8772000 * 923 / 1e8) < 1e-9
    assert v["rows"][0]["code"] == "8996"


if __name__ == "__main__":
    test_squeeze_view()
    print("ok tw squeeze")
