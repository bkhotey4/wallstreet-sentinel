"""台股專業判讀：解析、規則推算與卡片（不連網）。"""
from datetime import date, timedelta

from wsb.data import tw_desk as D
from tools import site_twdesk as S

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")


def _open(d: date) -> bool:
    return d.weekday() < 5


def test_roc_and_parsers():
    assert D.roc("1151202") == "2026-12-02" and D.roc("115/1/5") is None and D.roc("") is None
    ex = D.parse_exdiv([{"Date": "1151202", "Code": "2330", "Name": "台積電", "Exdividend": "息", "CashDividend": "6.0"},
                        {"Date": "1151202", "Code": "9999", "Name": "x", "Exdividend": "息", "CashDividend": ""},
                        {"Date": "bad", "Code": "2317"}], univ={"2330", "2317"})
    assert [r["code"] for r in ex] == ["2330"] and ex[0]["cash"] == 6.0
    p = D.parse_punish([{"Code": "2466", "Name": "冠西電", "DispositionPeriod": "115/11/19～115/11/25", "ReasonsOfDisposition": "連續三次",
                         "DispositionMeasures": "第一次處置"},
                        {"Code": "074692", "Name": "權證", "DispositionPeriod": "115/11/19～115/11/25"}])
    assert [r["code"] for r in p] == ["2466"] and p[0]["from"] == "2026-11-19" and p[0]["to"] == "2026-11-25"
    q = D.parse_punish([{"SecuritiesCompanyCode": "4577", "CompanyName": "達航科技", "DispositionPeriod": "1151123~1151127"}], "上櫃")
    assert q[0]["from"] == "2026-11-23" and q[0]["to"] == "2026-11-27" and q[0]["board"] == "上櫃"


def test_rules():
    t = date(2026, 11, 21)
    dl = D.deadlines(t)
    assert dl[0]["date"] == "2026-12-10" and "11 月營收" in dl[0]["what"]
    assert any(r["date"] == "2027-03-31" for r in dl)
    q = D.quarter_window(t, _open)
    assert q["to"] == "2026-12-31" and q["from"] == "2026-12-18"
    sizes = {"0050": {"name": "元大台灣50", "units": 1e10, "nav": 80.0, "date": "2026-11-20"}}
    er = D.etf_reviews(t, sizes, _open, _open, lambda d: False)
    z = [r for r in er if r["code"] == "0050"][0]
    assert z["next"]["date"] == "2026-12-18" and abs(z["per1"] - 8e9) < 1
    ann = [r for r in er if r["rule"] == "announce"]
    assert ann and all(r["next"]["date"] is None for r in ann)


def test_card():
    t = date(2026, 11, 21)
    v = {"today": t.isoformat(), "univ": {"codes": ["2330"], "source": "MoneyDJ", "asof": "2026-11-20"},
         "exdiv": [{"date": "2026-12-02", "code": "2330", "name": "台積電", "kind": "息", "cash": 6.0}],
         "punish": [{"code": "2466", "name": "冠西電", "from": "2026-11-19", "to": "2026-11-25", "board": "上市", "why": "連續三次", "step": "第一次處置"}],
         "deadlines": D.deadlines(t), "quarter": D.quarter_window(t, _open),
         "etf": D.etf_reviews(t, {"0050": {"name": "元大台灣50", "units": 1e10, "nav": 80.0, "date": "2026-11-20"}}, _open, _open, lambda d: False),
         "index": [{"date": "2026-11-30", "kind": "msci"}], "seed": {}, "ts": 1.8e9, "exdiv_ts": 1.8e9, "punish_ts": 1.8e9, "errs": {}}
    h = S.sec_tw_flowcal(v=v)
    assert "一句話看懂" in h and "11/30（一）" in h and "MSCI" in h and "冠西電" in h and "6.00 元" in h
    assert "80 億" in h                          # 1e10 units × 80 × 1% = 80 億
    for b in BANNED:
        assert b not in h, b


if __name__ == "__main__":
    test_roc_and_parsers(); test_rules(); test_card(); print("ok")
