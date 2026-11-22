"""MSCI 台灣（006203 持股近似，11-22）。Run: python -m tests.test_tw_msci"""
from datetime import date

from wsb.data import tw_msci as M

PAGE = ('<div>交易日期: <br class="d-lg-none">2026/11/20</div><script>window.__NUXT__=(function(a,b,c,d,e){return {x:Array(3),'
        'FundWeights:{Summary:{code:a,stkvalues:1553641777,futvalues:12530000},StockWeights:['
        '{code:b,ym:a,name:"台積電",ename:"TSMC, Ltd.",weights:57.39,qty:447800},'
        '{code:"2317",ym:a,name:c,ename:"Hon Hai",weights:e,qty:222588},{code:"",ym:a,name:"現金",weights:0.1,qty:1}]},'
        'note:"has }( inside a string"}}("","2330","鴻海",void 0,3));</script>')


def test_parse_without_eval():
    p = M.parse(PAGE)
    assert p["date"] == "2026-11-20" and p["stocks_value"] == 1553641777 and p["futures"] == 12530000
    assert [(s["code"], s["name"], s["w"]) for s in p["stocks"]] == [("2330", "台積電", 57.39), ("2317", "鴻海", 3)]
    assert M.parse("<html>no state</html>") == {}
    v, _ = M._value("Array(7)", 0)
    assert v == [None] * 7


def test_changes_around_review():
    s = {"2026-11-27": {"stocks": {"2330": ["台積電", 57.0], "2615": ["萬海", 0.05]}},
         "2026-11-30": {"stocks": {"2330": ["台積電", 57.1], "6789": ["新公司", 0.2]}},
         "2026-12-01": {"stocks": {"2330": ["台積電", 57.1], "6789": ["新公司", 0.2]}}}
    c = M.changes(s, around="2026-11-30")
    assert c["from"] == "2026-11-27" and c["to"] == "2026-12-01"
    assert [x["code"] for x in c["add"]] == ["6789"] and [x["code"] for x in c["rem"]] == ["2615"]
    assert M.changes({"2026-11-20": {"stocks": {}}}) == {}


def test_review_dates():
    from tools import site_tw_msci as S
    r = S.reviews(date(2026, 11, 22))
    assert r["next"]["tw_date"] == "2026-11-30" and r["last"]["tw_date"] == "2026-08-31"


if __name__ == "__main__":
    test_parse_without_eval()
    test_changes_around_review()
    test_review_dates()
    print("ok tw msci")
