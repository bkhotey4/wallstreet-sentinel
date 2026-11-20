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


def test_valuation():
    assert D.pct_rank([1.0] * 10, 2.0) is None                       # < 24 points
    hist = list(range(1, 31))
    assert D.pct_rank(hist, 25.5) == round(25 / 30 * 100, 1)
    snaps = {f"2024-{i:02d}-28" if i <= 12 else f"2025-{i - 12:02d}-28": {"2330": [10.0 + i, 3.0, 2.0], "1101": [None, 0.5 + i / 100, 3.0]}
             for i in range(1, 25)}
    latest = {"date": "2026-11-20", "rows": {"2330": [40.0, 3.0, 2.0], "1101": [None, 0.6, 3.0]}}
    b = D.stock_bands(snaps, latest, ["2330", "1101", "9999"], {"2330": "台積電"})
    assert [r["code"] for r in b] == ["2330", "1101"] and b[0]["pct"] == 100.0 and b[1]["metric"] == "股價淨值比"
    val = {"2026-09-30": {"pe_med": 20.0, "tsmc_pe": 25.0}, "2026-10-30": {"pe_med": 16.0, "tsmc_pe": 20.0}}
    e = D.erp_series(val, [["2026-09", 2.0]])
    assert e[0]["erp"] == 3.0 and e[1]["y10"] == 2.0 and e[1]["erp"] == 4.25 and e[1]["tsmc_erp"] == 3.0
    a = {"d": [(date(2025, 1, 1) + timedelta(days=i)).isoformat() for i in range(300)], "c": [100 + i for i in range(300)]}
    s2 = {"d": a["d"], "c": [100.0] * 300}
    r = D.rel_strength(a, s2)
    assert r["pct"] == round(299 / 300 * 100, 1) and r["sox_1y"] == 0.0
    v = {"bands": b, "erp": e, "erp_now": e[-1], "erp_pct": 50.0, "tsmc_pct": 40.0, "rel": r, "months": 24, "latest": "2026-11-20", "vh_ts": 1.8e9}
    h = S.sec_tw_valband(v=v)
    assert "一句話看懂" in h and "第 50 百分位" in h and "台積電" in h and "還在補" in h
    for w in BANNED:
        assert w not in h, w


def test_revenue():
    html = ("<tr align=right><td align=center>2330</td><td align=left>台積電</td><td nowrap> 442,679,969</td><td nowrap> 416,975,163</td>"
            "<td nowrap> 263,708,978</td><td nowrap> 6.16</td><Td nowrap> 67.86</td><td nowrap> 1</td></tr>")
    r = D.parse_mops(html)
    assert r["2330"][0] == 442679969 and r["2330"][2] == 67.86 and r["2330"][3] == "台積電"
    assert D.months_back(date(2026, 11, 21), 2) == ["2026-10", "2026-09"]
    assert D.months_back(date(2026, 11, 5), 1) == ["2026-09"]
    months = {}
    for i, ym in enumerate(["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]):
        months[ym] = {"2330": [100.0 + i, 80.0, 10.0 + i * 5, "台積電"]}
    months["2025-10"] = {"2330": [50.0, 40.0, 1.0, "台積電"]}
    order = sorted(months, reverse=True)
    t = D.stock_trend(months, "2330", order)
    assert t["yoy3"] == 30.0 and t["prev3"] == 15.0 and t["accel"] == 15.0
    nc = D.quarter_nowcast(months, "2330", "2026-10")
    assert nc["months"] == 1 and abs(nc["qtd_yoy"] - (105 / 50 - 1) * 100) < 1e-9
    assert abs(nc["q_vs_prev"] - (105 * 3 / (102 + 103 + 104) - 1) * 100) < 1e-9
    v = {"latest": "2026-10", "n_months": 7, "yoy_pos": 86.0, "breadth": 56.0, "trends": [t],
         "layers": [{"name": "晶圓代工", "n": 1, "missing": ["2303"], "yoy3_med": 30.0, "acc_share": 100.0, "rows": [t], "now": {"2330": nc}}],
         "capex": {"yoy": 93.4, "q": "2026Q3"}, "ts": 1.8e9}
    h = S.sec_tw_revheat(v=v)
    assert "一句話看懂" in h and "晶圓代工" in h and "+93%" in h and "2303" in h and "假設" in h
    for w in BANNED:
        assert w not in h, w


def test_calibration():
    docs = {"a": {"calls": [{"call": "x", "prob": 80, "result": "對", "by": "2026-11-01"}, {"call": "y", "prob": 60, "result": "錯"},
                            {"call": "z", "prob": 70, "result": "無法判定"}, {"call": "w", "prob": 70}]},
            "b": {"days": [{"calls": [{"claim": "q", "result": "對"}]}]}}
    bc = D.binary_calls(docs)
    assert len(bc) == 3 and bc[0]["p"] == 0.8 and bc[2]["p"] is None
    items = [{"sym": "A", "probs": {"上修": 20, "維持": 60, "下修": 20}, "outcome": "上修"},
             {"sym": "B", "probs": {"上修": 20, "維持": 60, "下修": 20}, "outcome": "維持"},
             {"sym": "C", "probs": {"上修": 50, "維持": 30}, "outcome": "上修"},           # incomplete → skipped
             {"sym": "D", "probs": {"上修": 20, "維持": 60, "下修": 20}, "outcome": None}]
    er = D.earn_calls(items)
    assert [r["sym"] for r in er] == ["A", "B"]
    c = D.calib(er)
    assert c["n"] == 2 and c["top_hit"] == 0.5 and abs(c["brier"] - ((0.8 ** 2 + 0.6 ** 2 + 0.2 ** 2) + (0.2 ** 2 + 0.4 ** 2 + 0.2 ** 2)) / 2) < 1e-9
    assert {b["k"]: round(b["real"], 2) for b in c["bias"]} == {"上修": 0.5, "維持": 0.5, "下修": 0.0}
    v = {"earn": c, "by_topic": {"a": {"n": 2, "hit": 1, "np": 2, "said": 1.4, "brier": 0.04 + 0.36}}, "binary": bc, "pending": 1, "updated": "x"}
    h = S.sec_calib(v=v)
    assert "一句話看懂" in h and "2 筆" in h and "太悲觀" in h and "0.200" in h
    for w in BANNED:
        assert w not in h, w


if __name__ == "__main__":
    test_roc_and_parsers(); test_rules(); test_card(); test_valuation(); test_revenue(); test_calibration(); print("ok")
