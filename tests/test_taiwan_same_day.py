"""TWSE same-day report fallback (11-21: openapi carried the previous day on a −6.2 % day)."""
from wsb.data import taiwan_quotes as T

DOC = {"stat": "OK", "date": "20261120", "tables": [
    {"title": "115年11月20日 價格指數(臺灣證券交易所)", "fields": ["指數", "收盤指數", "漲跌(+/-)", "漲跌點數", "漲跌百分比(%)", "特殊處理註記"],
     "data": [["寶島股價指數", "1.00", "<p style= color:green>-</p>", "0.10", "-1.00", ""],
              ["發行量加權股價指數", "36,033.29", "<p style= color:green>-</p>", "2,393.60", "-6.23", ""]]},
    {"title": "115年11月20日 每日收盤行情(全部(不含權證、牛熊證、可展延牛熊證))",
     "fields": ["證券代號", "證券名稱", "成交股數", "成交筆數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "漲跌(+/-)", "漲跌價差"],
     "data": [["9999", "測試股", "1,000", "1", "10", "10", "10", "10", "100.00", "<p style= color:green>-</p>", "5.00"],
              ["9998", "測試漲", "1,000", "1", "10", "10", "10", "10", "50.00", "<p style= color:red>+</p>", "2.50"],
              ["9997", "沒比", "1,000", "1", "10", "10", "10", "10", "20.00", "X", "0.00"],
              ["999901", "權證不收", "1", "1", "1", "1", "1", "1", "1.00", "+", "0.10"]]}]}


def test_parse_mi_index():
    o = T.parse_mi_index(DOC)
    assert o["9999.TW"]["prev"] == 105.0 and o["9999.TW"]["asof"] == "2026-11-20"
    assert o["9998.TW"]["prev"] == 47.5
    assert o["9997.TW"]["prev"] == 20.0
    assert "999901.TW" not in o
    ix = o["^TWII"]
    assert ix["price"] == 36033.29 and round(ix["prev"], 2) == 38426.89 and round(ix["chg_pct"], 2) == -6.23
    assert T.parse_mi_index({"stat": "很抱歉，沒有符合條件的資料!"}) == {}


if __name__ == "__main__":
    test_parse_mi_index(); print("ok")
