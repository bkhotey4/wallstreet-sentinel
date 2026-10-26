"""台灣 pages: central bank / NDC / TPEx / Taipei parsers, the bond, credit, economy, money and housing views, the data
calendar, the plain-language read, the cards' wording and the sidebar group."""
import io
import os
import re
import sys
import tempfile
import types
import zipfile
from datetime import date
from pathlib import Path

os.environ["WSB_DATA_DIR"] = tempfile.mkdtemp()                       # never touch the real data_cache
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from wsb.analytics import twmacro as A  # noqa: E402
from wsb.data import twmacro as TM  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出")


def _months(n, end="2026-08"):
    return [p.strftime("%Y-%m") for p in pd.period_range(end=end, periods=n, freq="M")]


def _rows(vals, end="2026-08"):
    return [[m, v] for m, v in zip(_months(len(vals), end), vals)]


def test_parse_cbc():
    j = {"meta": {"last_updated": "2026-09-24"},
         "data": {"structure": {"Table1": [{"data": "M1B"}, {"data": "M2"}], "Table2": [{"data": "金額"}, {"data": "年增率"}]},
                  "dataSets": [["2026M07", "10", "5.1", "20", "6.0"], ["2026M08", "11", "-", "21", "6.5"]]}}
    assert TM.cbc_columns(j) == ["M1B|金額", "M1B|年增率", "M2|金額", "M2|年增率"]
    assert TM.parse_cbc(j, "M1B|年增率") == [["2026-07", 5.1]]                 # "-" dropped
    assert TM.parse_cbc(j, "M2") == [["2026-07", 20.0], ["2026-08", 21.0]]       # prefix match
    assert TM.parse_cbc(j, "nope") == []


def test_parse_ndc_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("燈號.csv", ("﻿\"Date\",\"景氣對策信號綜合分數\",\"景氣對策信號\"\n202607,41,紅\n202608,38,黃紅\n").encode("utf-8"))
        z.writestr("領先.csv", "\"Date\",\"外銷訂單動向指數(以家數計)\",\"失業率(%)\"\n202608,49.68,3.41\n".encode("cp950"))
    d = TM.parse_ndc(buf.getvalue())
    assert d["light_score"] == [["2026-07", 41.0], ["2026-08", 38.0]] and d["light"][-1] == ["2026-08", "黃紅"]
    assert d["orders_idx"] == [["2026-08", 49.68]] and d["unemp"] == [["2026-08", 3.41]]


def test_parse_tpex_now_and_taipei():
    j = {"bondCruve": {"data": [{"time": 2, "index": 1.5}, {"time": 10, "index": 2.0}]},
         "bondCoCurve": {"dataDate": "2026/10/22", "data": [{"time": 60, "twAAA": 0.0215, "twAA": 0.0225, "twA": 0.0232, "twBBB": 0.0241}]}}
    n = TM.parse_tpex_now(j)
    assert n["date"] == "2026-10-22" and n["gov"]["10"] == 2.0 and abs(n["corp"]["twBBB"]["60"] - 2.41) < 1e-9
    assert TM.parse_tpex_now({}) is None
    tp = TM.parse_taipei("﻿類別,期別,月指數\n全市,115/05,130.0\n全市,115/06,131.0\n全市小宅,115/06,99\n")
    assert tp == [["2026-05", 130.0], ["2026-06", 131.0]]


def _data(spread_bbb=50.0, months=120, light="紅"):
    ms = _months(months, "2026-09")
    hist = {m: {"gov": {"2": 1.5, "5": 1.8, "10": 2.0}, "corp": {"twAAA": {"60": 2.0}, "twAA": {"60": 2.1}, "twA": {"60": 2.2},
                                                                  "twBBB": {"60": 1.8 + (spread_bbb if i == months - 1 else 40.0) / 100}}}
            for i, m in enumerate(ms)}
    n = 480
    return {"hist": hist, "daily": {},
            "cbc": {"tw10y": _rows([1.0 + i / n for i in range(n)]), "disc": _rows([1.875] * (n - 30) + [2.0] * 30),
                    "call": _rows([0.8] * 24), "m1b": _rows([5.0 + (i % 24) / 4 for i in range(n)]), "m2": _rows([7.0] * n),
                    "taiex": _rows([1000 * (1.004 ** i) for i in range(n)]), "fxres": _rows([500000 + i for i in range(24)]),
                    "npl": _rows([0.14] * 24), "cpi": _rows([2.0] * 24), "gov_out": _rows([6e6] * 24),
                    "corp_out": _rows([4e6] * 24), "corp_issue": _rows([1e5] * 24),
                    "life_foreign": _rows([20e6] * 24), "life_assets": _rows([38e6] * 24), "life_equity": _rows([3e6] * 16 + [4.4e6] * 8),
                    "mortgage_yoy": _rows([5.0] * 24), "construct_yoy": _rows([-0.5] * 24)},
            "ndc": {"light_score": _rows([30] * 20 + [41] * 4), "light": _rows(["綠"] * 20 + [light] * 4), "lead": _rows([100 + i / 10 for i in range(24)]),
                    "coin": _rows([100.0] * 24), "exports": _rows([100.0] * 12 + [150.0] * 12), "ip": _rows([100.0] * 24),
                    "chip_tools": _rows([10.0] * 12 + [20.0] * 12), "orders_idx": _rows([49.0] * 24), "unemp": _rows([3.4] * 24)},
            "taipei": _rows([100 + i for i in range(40)], "2026-06")}


def test_views():
    d = _data()
    g = A.gov(d, us10=4.5)
    assert abs(g["now10"] - (1 + 479 / 480)) < 1e-9 and g["disc_move"]["date"] == "2024-03" and abs(g["gap_us"] - (4.5 - g["now10"])) < 1e-9
    c = A.corp(d)
    bbb = next(x for x in c["rows"] if x["k"] == "twBBB")
    assert abs(bbb["spread"] - 50) < 1e-6 and bbb["state"] == "急速擴大" and not c["filling"]   # 40 → 50 bp: never moved like this before
    assert A.corp(_data(months=24))["filling"] and A.corp(_data(months=24))["rows"][0]["pct"] is None
    e = A.econ(d)
    assert e["light"] == "紅" and e["run"] == 4 and abs(e["exports_yoy"] - 50) < 1e-9 and abs(e["chip3"] - 100) < 1e-9
    m = A.money(d)
    assert m["test"]["n_up"] + m["test"]["n_dn"] > 400 and m["m1b"] > 0
    ih = A.insure_house(d)
    assert ih["life"]["ifrs17"] and ih["life"]["eq_1y"] is None and ih["life"]["share_1y"] is None      # 2026-01 accounting break
    assert ih["taipei"]["off_peak"] == 0 and abs(ih["taipei"]["yoy"] - (139 / 127 - 1) * 100) < 1e-9


def test_calendar():
    rows = A.calendar_rows(_data(), date(2026, 10, 26))
    assert rows == sorted(rows, key=lambda r: r["when"]) and all(r["when"] >= date(2026, 10, 26) for r in rows)
    assert all(r["when"].weekday() < 5 for r in rows)
    cb = next(r for r in rows if "理監事" in r["zh"])
    assert cb["when"] == date(2026, 12, 17) and cb["when"].weekday() == 3


def _eng(d):
    e = types.SimpleNamespace(fred=types.SimpleNamespace(get=lambda k: pd.Series([4.5], index=[pd.Timestamp("2026-10-23")])),
                              market=types.SimpleNamespace(history=pd.DataFrame({"TWD=X": [33.0] * 80 + [31.0] * 20},
                                                                                index=pd.date_range("2026-06-01", periods=100))))
    TM._save(d)
    return e


def test_build_read_and_cards():
    from tools import site_twmacro as ST
    e = _eng(_data())
    r = A.build(e)
    assert r["available"] and r["read"]["head"].startswith("一句話看懂：景氣燈號🔴紅燈")
    assert any("升值" in x for x in r["read"]["imp"])                                    # TWD 33 → 31 in 3 months
    out = ""
    for f in (ST.sec_tw_brief, ST.sec_tw_calendar, ST.sec_tw_gov, ST.sec_tw_corp, ST.sec_tw_econ, ST.sec_tw_money, ST.sec_tw_life):
        h = f(e)
        assert "一句話看懂" in h, f.__name__
        out += h
    txt = re.sub(r"<[^>]+>", " ", out)
    assert not [b for b in BANNED if b in txt]
    assert ST.sec_tw_note(e) == "" or "台灣" in ST.sec_tw_note(e)
    cold = _data(light="藍")
    cold["ndc"]["light_score"] = _rows([30] * 20 + [14] * 4)
    assert any("偏冷" in x for x in A.read({"econ": A.econ(cold)})["imp"])


def test_note_file(tmp=None):
    from tools import site_twmacro as ST
    old = ST.NOTE
    p = Path(tempfile.mkdtemp()) / "tw_note.json"
    p.write_text('{"notes": [{"month": "2026-09", "date": "2026-10-28", "summary": ["出口年增 50%"], "sources": [{"name": "國發會", "url": "https://www.ndc.gov.tw"}, {"name": "x", "url": "javascript:1"}]},'
                 ' {"month": "bad"}]}', encoding="utf-8")
    ST.NOTE = p
    try:
        h = ST.sec_tw_note(None)
        assert "出口年增 50%" in h and "https://www.ndc.gov.tw" in h and "javascript" not in h
    finally:
        ST.NOTE = old


def test_layout_group():
    from tools import site_layout as LY
    assert all(LY.GROUP_OF[k] == "tw" for k in ("tw_ai", "taiwan", "tw_bonds", "tw_credit", "tw_econ", "tw_money", "tw_life"))
    assert LY.GROUP_OF["premarket"] == "home"


def main():
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)


if __name__ == "__main__":
    main()
