"""各國危機雷達：匯率用中位數算、踩線與燈號、擴散判斷、警報的鍵、資料解析、卡片文字（不連網）。
Run: python -m tests.test_country_risk"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wsb.data import country_risk as CR  # noqa: E402


def _fx(start: float, end: float, n: int = 1300) -> list:
    return [start + (end - start) * i / (n - 1) for i in range(n)]


def test_maths():
    # a steady slide from 15,000 to 18,000 rupiah per dollar: the currency lost value, and today is its weakest
    c = _fx(15000, 18000)
    s = CR.fx_stats(c)
    assert s["rate"] == 18000 and -0.1 < s["weak"] <= 0 and s["fx_y1"] < -3 and s["fx_m1"] < 0 and s["fx_w2"] < 0
    # one wild tick does not move the medians
    c2 = list(c)
    c2[-2] = 30000
    s2 = CR.fx_stats(c2)
    assert abs(s2["fx_m1"] - s["fx_m1"]) < 0.2 and abs(s2["fx_w2"] - s["fx_w2"]) < 0.2
    # prices that jump between two levels for days at a time: the two-week figure stays small
    c3 = [17500.0] * 1280 + [18100, 18100, 18100, 17480, 17500, 17510, 17480, 18095, 18060, 18140, 17490, 17630, 18190, 18100, 17500, 17520, 18100, 18090, 17500, 18150]
    assert abs(CR.fx_stats(c3)["fx_w2"]) < 2.5
    strong = CR.fx_stats(_fx(18000, 15000))
    assert strong["weak"] < -10 and strong["fx_y1"] > 3                       # a rising currency is far from its weakest
    assert CR.fx_stats([1.0] * 50) == {} and CR.smooth([1.0, 2.0]) is None
    e = CR.etf_stats([100.0] * 200 + [50.0] * 100)
    assert e["off"] == -50.0 and CR.etf_stats([1.0] * 10) == {}
    r = CR.res_stats({f"2025-{m:02d}": 100.0 for m in range(1, 13)} | {"2026-01": 70.0})
    assert r["res_month"] == "2026-01" and abs(r["res_y1"] + 30) < 1e-9 and CR.res_stats({"2026-01": 1.0}) == {}
    assert CR.year_val({"2025": 1.0, "2026": 2.0}, 2026) == 2.0 and CR.year_val({"2025": 1.0}, 2026) == 1.0 and CR.year_val({}, 2026) is None


def test_flags_and_spread():
    turkey = {"fx_y1": -15.7, "weak": 0.0, "res_y1": -28.3, "mo": 5.1, "st": None, "ca": -2.9, "off": -26.4}
    assert CR.flags_of(turkey) == ["貨幣一年貶超過 15%", "貨幣在 5 年最弱附近", "外匯存底一年少超過 10%"] and CR.light(3) == 1
    worst = {"fx_y1": -30, "weak": -1, "res_y1": -20, "mo": 2.0, "st": 140.0, "ca": -6.0, "off": -40}
    assert len(CR.flags_of(worst)) == 7 and CR.light(7) == 2 and CR.light(4) == 2 and CR.light(1) == 0
    assert CR.flags_of({}) == []                                              # missing data never lights anything
    rows = [{"zh": "甲", "light": 2, "fx_m1": -4.0}, {"zh": "乙", "light": 1, "fx_m1": -1.0}, {"zh": "丙", "light": 0, "fx_m1": 0.5}]
    sp = CR.spreading(rows, -3.8, -3.0)
    assert sp["state"] == "local" and sp["red"] == ["甲"] and sp["weak"] == ["甲"] and abs(sp["lag"] + 0.8) < 1e-9
    assert CR.spreading(rows, -8.0, -3.0)["state"] == "spread"                # EM dollar bonds 5 points behind Treasuries
    assert CR.spreading([dict(r, light=2) for r in rows], None, None)["state"] == "spread"       # three reds
    assert CR.spreading([dict(r, fx_m1=-5.0) for r in rows] * 2, None, None)["state"] == "spread"  # six currencies down > 3 %
    assert CR.spreading([dict(r, light=0) for r in rows], None, None)["state"] == "calm"


def test_alerts():
    rows = [{"iso3": "TUR", "zh": "土耳其", "cur": "里拉", "light": 2, "flags": ["a", "b", "c", "d"], "fx_w2": -2.5},
            {"iso3": "IDN", "zh": "印尼", "cur": "盧比", "light": 1, "flags": ["a", "b"], "fx_w2": -3.1},
            {"iso3": "BRA", "zh": "巴西", "cur": "雷亞爾", "light": 0, "flags": [], "fx_w2": -2.2},
            {"iso3": "KOR", "zh": "南韓", "cur": "韓元", "light": 0, "flags": [], "fx_w2": 0.4}]
    al = CR.alerts(rows, {"state": "local", "red": ["土耳其"], "weak": [], "lag": None}, "2026-11-14")
    assert [a["key"] for a in al] == ["cr:red:TUR:2026-11", "cr:fx:2026-11"]
    assert "3 國兩週內貶超過 2%" in al[1]["title"] and al[1]["text"].startswith("印尼盧比 -3.1%") and al[1]["lv"] == 1
    assert CR.alerts(rows[2:], {"state": "calm", "red": [], "weak": [], "lag": None}, "2026-11-14") == []
    sp = CR.alerts(rows[3:], {"state": "spread", "red": [], "weak": ["a"] * 5, "lag": -4.0}, "2026-12-01")
    assert sp[0]["key"] == "cr:spread:2026-12" and "5 國貨幣一個月貶超過 3%" in sp[0]["text"] and "多跌 4.0 個百分點" in sp[0]["text"]


def _data() -> dict:
    px = {}
    for iso3, _i2, _zh, _cur, fx, etf in CR.COUNTRIES:
        weak = iso3 in ("IDN", "TUR")
        px[fx] = {"d": ["2026-11-14"] * 1300, "c": _fx(100, 125 if iso3 == "TUR" else 109 if weak else 90)}
        if etf:
            px[etf] = {"d": ["2026-11-14"] * 1300, "c": [100.0] * 1100 + [55.0 if iso3 == "IDN" else 90.0] * 200}
    months = [f"{y}-{m:02d}" for y in (2025, 2026) for m in range(1, 13)][:21]
    res = {c[0]: {m: 100.0 for m in months} for c in CR.COUNTRIES[:6]}
    res["TUR"] = {m: (100.0 if i < 9 else 70.0) for i, m in enumerate(months)}
    gdp = {c[0]: {"2026": 1000.0, "1997": 200.0, "1998": 200.0, "2018": 700.0} for c in CR.COUNTRIES}
    gdp.update({"WEOWORLD": {"2026": 100000.0, "1997": 30000.0, "1998": 30000.0, "2018": 85000.0}, "RUS": {"1998": 270.0}})
    return {"px": px, "res": res, "imf_gdp": gdp, "imf_ca": {c[0]: {"2026": -1.0} for c in CR.COUNTRIES} | {"PHL": {"2025": -4.8}},
            "imf_debt": {c[0]: {"2026": 50.0} for c in CR.COUNTRIES}, "wb_mo": {c[0]: ["2025", 5.0] for c in CR.COUNTRIES} | {"VNM": ["2025", 2.1]},
            "ts_check": 1794672727.0, "ts_each": {"px": 1794672727.0}}


def test_parse_and_view():
    js = {"chart": {"result": [{"timestamp": [1794614400, 1794700800], "indicators": {"quote": [{"close": [18140.0, None]}]}}]}}
    assert CR.parse_yahoo(js) == {"d": ["2026-11-14"], "c": [18140.0]}
    imf = {"values": {"BCA_NGDPD": {"IDN": {"2025": -0.1, "2026": -1.6, "2027": None}, "XXX": {"2026": 1}}}}
    assert CR.parse_imf(imf, "BCA_NGDPD", ["IDN", "TUR"]) == {"IDN": {"2025": -0.1, "2026": -1.6}}
    wb = [{"page": 1}, [{"countryiso3code": "IDN", "date": "2025", "value": 5.5}, {"countryiso3code": "USA", "date": "2025", "value": 2.0},
                        {"countryiso3code": "TUR", "date": "2025", "value": None}]]
    assert CR.parse_wb(wb, ["IDN", "TUR"]) == {"IDN": ["2025", 5.5]} and CR.parse_wb([{"message": "x"}], ["IDN"]) == {}
    v = CR.view(None, _data())
    by = {r["iso3"]: r for r in v["rows"]}
    assert len(v["rows"]) == 14 and v["rows"][0]["iso3"] == "TUR"                          # most flags first
    assert by["TUR"]["flags"] == ["貨幣一年貶超過 15%", "貨幣在 5 年最弱附近", "外匯存底一年少超過 10%"] or len(by["TUR"]["flags"]) >= 2
    assert "股市（美元計價）離高點超過 30%" in by["IDN"]["flags"] and "貨幣在 5 年最弱附近" in by["IDN"]["flags"] and by["IDN"]["light"] == 1
    assert by["VNM"]["flags"] == ["存底不夠付 3 個月進口"] and by["PHL"]["ca"] == -4.8 and "經常帳逆差超過 GDP 的 4%" in by["PHL"]["flags"]
    assert by["EGY"].get("off") is None and abs(by["IDN"]["share"] - 1.0) < 1e-9 and by["KOR"]["light"] == 0
    assert [p["zh"] for p in v["past"]] == ["泰國", "印尼", "南韓", "俄羅斯", "土耳其"] and abs(v["past"][3]["share"] - 0.9) < 1e-9
    assert v["missing"] == ["短期外債對存底"] and v["asof"] == "2026-11-14" and v["spread"]["state"] in ("local", "spread")
    pub = CR.public(v)
    assert set(pub) == {"ts", "asof", "spread", "alerts", "rows"} and pub["rows"][0]["zh"] == "土耳其" and "px" not in json.dumps(pub)
    assert CR.view(None, {}) == {}


def test_card():
    from tools import site_euro_asia as SE
    CR.FILE = pathlib.Path(tempfile.mkdtemp()) / "cr.json"
    CR.FILE.write_text(json.dumps(_data()), encoding="utf-8")
    h = SE.sec_country(types.SimpleNamespace(market=None))
    assert "一句話看懂" in h and "各國危機雷達" in h and "🟡 " in h and "印尼" in h and "還看不到擴散" in h
    assert "每一國的完整數字" in h and "規模夠不夠大到引發海嘯" in h and "1997 年泰國" in h and "現在印尼佔 1.00%" in h
    assert "這次沒抓到的欄位：短期外債對存底" in h and "不是預測模型" in h and "不是投資建議" in h
    for w in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "加碼參考區", "進場參考區", "精選池"):
        assert w not in h, w
    hot = SE.cr_headline({"rows": [{"zh": "甲", "light": 2}] * 3, "spread": {"state": "spread", "weak": ["甲"], "emb3": -8.0, "ief3": -3.0}})
    assert hot.startswith("一句話看懂：新興市場的壓力正在擴散：3 國紅燈") and "新興市場美元債三個月 -8.0%" in hot
    calm = SE.cr_headline({"rows": [{"zh": "甲", "light": 0}], "spread": {"state": "calm", "weak": []}})
    assert "沒有國家踩到兩項以上的警戒線" in calm
    CR.FILE.write_text("{}", encoding="utf-8")
    assert SE.sec_country(types.SimpleNamespace(market=None)) == ""             # no data → no card, never an empty table


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
