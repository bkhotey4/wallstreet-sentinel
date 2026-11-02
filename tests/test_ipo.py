"""IPO 觀察: prospectus cover / 424B4 / submissions parsers, IPO vs follow-on / SPAC / fund, TWSE 公開申購 and TPEx 興櫃 parsers,
the timing window from past cases, the after-listing record, the card (no trading words) and the AI line parser.
Run: python -m tests.test_ipo"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import date

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_ipo_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "加碼", "進場參考區", "值得申購")
TODAY = date(2026, 11, 3)


def test_cover_and_offer():
    from wsb.data import ipo_data as I
    raw = ("<html><p>We are offering 12,500,000 shares of our Class A common stock. We expect the initial public offering price "
           "per share will be between $16.00 and $18.00 per share. We have applied to list our Class A common stock on the "
           "Nasdaq Global Select Market under the symbol &#8220;ACME.&#8221;</p>" + "x " * 9000
           + "<p>Prospectus Summary</p><p>We build widgets.</p><p>Summary Consolidated Financial Data Revenue $ 120 $ 300</p>"
           "<p>lock-up agreements under which they agree for a period of 180 days after the date of this prospectus</p></html>")
    cv = I.parse_cover(I.text_of(raw))
    assert cv["exchange"] == "Nasdaq Global Select Market" and cv["symbol"] == "ACME"
    assert (cv["lo"], cv["hi"]) == (16.0, 18.0) and cv["shares"] == 12_500_000 and cv["lockup"] == 180
    assert "Revenue $ 120" in cv["excerpt"] and "We build widgets" in cv["excerpt"]
    assert I.offer_price("This is the initial public offering of ... The initial public offering price is $17.00 per share.") == 17.0
    assert I.offer_price("The initial public offering price of our ordinary shares is US$4.00 per ordinary share.") == 4.0
    assert I.offer_price("PRICE US$9.25 PER ADS") == 9.25
    assert I.parse_cover("units ... to complete our initial business combination within 24 months")["spac"]
    blank = I.parse_cover(I.text_of("<p>initial public offering price per share will be between $ and $ . Nasdaq Global Market under the symbol “ZZ”</p>"))
    assert "lo" not in blank and blank["symbol"] == "ZZ"


def _sub(forms, name="Acme Corp", sic="7372", tickers=()):
    f = [x[0] for x in forms]
    return {"name": name, "sic": sic, "sicDescription": "Software", "tickers": list(tickers), "exchanges": [],
            "filings": {"recent": {"form": f, "filingDate": [x[1] for x in forms], "accessionNumber": [f"acc{i}" for i in range(len(f))],
                                   "primaryDocument": [f"d{i}.htm" for i in range(len(f))]}}}


def test_timeline_and_kind():
    from wsb.data import ipo_data as I
    t = I.timeline(_sub([("DRS", "2026-03-01"), ("S-1", "2026-06-01"), ("S-1/A", "2026-07-01"), ("S-1/A", "2026-07-20"),
                         ("424B4", "2026-07-30"), ("S-1MEF", "2026-07-29"), ("10-Q", "2026-09-10")], tickers=["ACME"]))
    assert t["drs"] == "2026-03-01" and t["s1"] == "2026-06-01" and t["amends"] == 2 and t["priced"] == "2026-07-30"
    assert t["last_pre"] == "2026-07-20" and not t["prior_public"] and I.kind(t) == "ipo"
    fo = I.timeline(_sub([("10-K", "2025-03-01"), ("S-1", "2026-06-01")]))
    assert fo["prior_public"] and I.kind(fo) == "followon"
    assert I.kind(I.timeline(_sub([("S-1", "2026-06-01")], name="Blue Sky Acquisition Corp II", sic="6770"))) == "spac"
    assert I.kind(I.timeline(_sub([("S-1", "2026-06-01")], name="Grayscale Solana Trust", sic="6221"))) == "fund"
    rw = I.timeline(_sub([("S-1", "2026-01-01"), ("RW", "2026-05-01")]))
    assert rw["rw"] == "2026-05-01"


def test_taiwan_parsers():
    from wsb.data import ipo_data as I
    js = {"fields": ["序號", "抽籤日期", "證券名稱", "證券代號", "發行市場", "申購開始日", "申購結束日", "承銷股數", "實際承銷股數", "承銷價(元)",
                     "實際承銷價(元)", "撥券日期(上市、上櫃日期)", "主辦券商", "申購股數", "總承銷金額(元)", "總合格件", "中籤率(%)", "取消公開抽籤 "],
          "data": [["1", "115/11/13", "宏偉", "4565", "初上櫃", "115/11/09", "115/11/11", "1,449,000", "1,449,000", "90", "未訂出", "115/11/19", "中國信託", "1,000", "未訂出", "0", "0", ""],
                   ["2", "115/11/04", "115央債甲10", "A151JA", "中央登錄公債", "115/10/27", "115/11/02", "60,000", "60,000", "100", "100", "115/11/09", "郵政", "1,000", "", "0", "0", ""],
                   ["3", "115/06/04", "某某", "6999", "初上市", "115/06/01", "115/06/03", "2,000,000", "2,000,000", "50", "55", "115/06/12", "元大", "1,000", "", "1", "1.25", ""]]}
    rows = I.parse_public(js)
    assert [r["code"] for r in rows] == ["4565", "6999"]
    assert rows[0]["list"] == "2026-11-19" and rows[0]["price"] == 90 and not rows[0]["final"] and rows[1]["price"] == 55 and rows[1]["win"] == 1.25
    esb = I.parse_esb([{"SecuritiesCompanyCode": "4565", "CompanyName": "宏偉", "Average": "126.51", "PreviousAveragePrice": "130.18",
                        "TransactionVolume": "171908", "ApplyingDate": "20260826", "ApplyingStatus": "E"},
                       {"SecuritiesCompanyCode": "1260", "CompanyName": "富味鄉", "Average": "31.46", "ApplyingDate": "", "ApplyingStatus": ""}])
    assert esb["4565"]["apply"] == "2026-08-26" and esb["4565"]["to"] == "上櫃" and esb["1260"]["apply"] is None
    inc = []
    for i, q in enumerate(["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"]):
        inc += [{"date": q, "type": "Revenue", "value": 100 + 10 * i}, {"date": q, "type": "IncomeAfterTaxes", "value": 10}]
    f = I.tw_fin(inc)
    assert f["q"] == "2026-06-30" and abs(f["yoy"] - (150 / 110 - 1) * 100) < 1e-9 and abs(f["nm_ttm"] - 40 / (120 + 130 + 140 + 150) * 100) < 1e-9


def _d(**kw):
    return kw


def test_views():
    from wsb.analytics import ipo as IP
    filers = {}
    for i in range(12):                                   # 12 past IPOs: 60 days from S-1 to pricing, 10 from the last amendment
        s1 = date(2025, 1 + i % 10, 5)
        pr = date.fromordinal(s1.toordinal() + 60)
        filers[str(i)] = {"kind": "ipo", "name": f"P{i}", "s1": str(s1), "priced": str(pr), "last_pre": str(date.fromordinal(pr.toordinal() - 10)),
                          "tickers": [f"P{i}"], "offer": 10.0, "offer_shares": 20_000_000 if i % 2 else 1_000_000, "cover": {"lockup": 180}}
    filers["a"] = {"kind": "ipo", "name": "Anthro", "s1": "2026-10-26", "last": "2026-11-02", "amends": 1, "doc": {"acc": "A1"},
                   "cover": {"exchange": "Nasdaq Global Select Market", "symbol": "ANT"}}
    filers["b"] = {"kind": "ipo", "name": "RangeCo", "s1": "2026-09-01", "last": "2026-10-29", "amends": 3, "doc": {"acc": "B1"},
                   "cover": {"exchange": "NYSE", "symbol": "RNG", "lo": 14.0, "hi": 16.0}}
    filers["c"] = {"kind": "ipo", "name": "Shell", "s1": "2026-08-01", "last": "2026-10-01", "cover": {}}
    filers["d"] = {"kind": "followon", "name": "Old", "s1": "2026-08-01", "last": "2026-10-01"}
    idx = pd.bdate_range("2025-01-01", "2026-11-02")
    px = pd.DataFrame({f"P{i}": np.linspace(12, 9, len(idx)) for i in range(12)}, index=idx)
    spx = pd.Series(np.linspace(100, 110, len(idx)), index=idx)
    u = IP.us_view({"us": {"filers": filers}}, px, spx, TODAY)
    assert [r["name"] for r in u["pending"]] == ["RangeCo", "Anthro"] and u["other"] == 1
    assert u["t_first"]["med"] == 60 and u["t_last"]["med"] == 10
    a = next(r for r in u["pending"] if r["name"] == "Anthro")
    assert a["win_lo"] == a["win_hi"] == "2026-12-25" and not a["slow"]
    assert next(r for r in u["pending"] if r["name"] == "RangeCo")["near"] == "2026-11-08"
    st = u["stats"]
    assert st["day1"]["n"] == 12 and st["day1"]["med"] > 0 and st["x120"]["med"] < 0
    assert st["big"]["day1"] is None and st["small"]["day1"] is None          # 6 each: below the 10-company floor
    tw = {"public": {"2026": {"rows": [{"code": "4565", "name": "宏偉", "mk": "初上櫃", "list": "2026-11-19", "price": 90.0, "final": False},
                                      {"code": "6999", "name": "某某", "mk": "初上市", "list": "2025-03-03", "price": 50.0, "final": True, "win": 1.2}]}},
          "esb": {"rows": {"4565": {"name": "宏偉", "avg": 126.5, "apply": "2026-08-26", "to": "上櫃"},
                           "7777": {"name": "排隊", "avg": 40.0, "apply": "2026-09-01", "to": "上市"}}},
          "fin": {"7777": {"ts": 1, "yoy": 12.0, "nm_ttm": 8.0}}, "apply_log": {"6999": {"apply": "2024-10-01"}}}
    px2 = pd.DataFrame({"6999.TW": np.linspace(60, 55, len(idx))}, index=idx)
    t = IP.tw_view({"tw": tw}, px2, None, TODAY)
    assert [r["code"] for r in t["upcoming"]] == ["4565"] and t["upcoming"][0]["disc"] < 0
    assert [r["code"] for r in t["applying"]] == ["7777"] and t["applying"][0]["fin"]["yoy"] == 12.0
    p = t["past"][0]
    assert p["day1"] > 0 and p["wait"] == (date(2025, 3, 3) - date(2024, 10, 1)).days


def test_card_and_ai_parse():
    from tools import site_ipo as S
    from wsb.ai import ipo_ai
    b = {"us": {"pending": [{"cik": "1", "name": "Anthro", "symbol": "ANT", "exchange": "Nasdaq", "s1": "2026-10-26", "last": "2026-11-02",
                             "amends": 1, "since": 8, "win_lo": "2026-11-23", "win_hi": "2027-05-25", "slow": False,
                             "ai": {"業務": "做 AI 模型。", "財務": "營收 4,585 百萬美元。"}}],
                "other": 3, "recent": [], "t_first": {"p25": 28, "med": 78, "p75": 212, "n": 367}, "t_last": {"med": 9, "n": 280},
                "stats": {"big": {"day1": {"n": 40, "med": 15.0, "pos": 70.0}, "x120": {"n": 30, "med": -5.0, "pos": 40.0}}}, "lock_soon": []},
         "tw": {"upcoming": [{"code": "4565", "name": "宏偉", "mk": "初上櫃", "list": "2026-11-19", "price": 90.0, "final": False, "esb_avg": 126.5, "disc": -28.9}],
                "applying": [], "past": [], "stats": {"day1": {"n": 150, "med": 18.0, "pos": 80.0}, "x60": {"n": 140, "med": -19.0, "pos": 19.0}}}}
    out = S.sec_ipo(types.SimpleNamespace(ipo=b))
    assert "一句話看懂" in out and "Anthro" in out and "宏偉" in out and "招股書重點" in out and "不是申購或買賣建議" in out
    assert "第一天收盤比發行價中位數 +15%" in out and "60 天後比加權指數 -19%" in out
    for w in BANNED[:-1]:
        assert w not in out, w
    b["us"]["filling"] = True
    assert "第一次建立" in S.lead(b)
    p = ipo_ai.parse("業務：做 AI 模型。\n財務：營收 4,585 百萬美元。\n資金用途：一般營運。\n主要風險：競爭。\n要留意：建議買進。")
    assert p and set(p) == {"業務", "財務", "資金用途", "主要風險"}                      # the advice sentence is scrubbed


if __name__ == "__main__":
    fails = 0
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            try:
                f()
                print("ok  ", n)
            except Exception as ex:  # noqa: BLE001
                fails += 1
                import traceback
                traceback.print_exc()
                print("FAIL", n, repr(ex))
    sys.exit(1 if fails else 0)
