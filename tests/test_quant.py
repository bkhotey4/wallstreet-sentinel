"""Factor model, SEC revenue exposure parser, signal scorecard — synthetic data, no network.
Run: python -m tests.test_quant"""
from __future__ import annotations

import os
import sys
import tempfile
import types

import numpy as np
import pandas as pd

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_quant_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.analytics import factors as FA  # noqa: E402
from wsb.analytics import signal_ledger as SL  # noqa: E402
from wsb.data import segments as SG  # noqa: E402


def _history(n=700, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-02", periods=n)
    m = rng.normal(0.0004, 0.01, n)
    semi = rng.normal(0, 0.012, n)
    size, mom, lowv = (rng.normal(0, 0.006, n) for _ in range(3))
    px = lambda r: 100 * np.cumprod(1 + r)  # noqa: E731
    h = pd.DataFrame({"SPY": px(m), "SMH": px(m + semi), "IWM": px(m + size), "MTUM": px(m + mom), "USMV": px(m + lowv),
                      "DX-Y.NYB": px(rng.normal(0, 0.004, n)), "^TNX": 4 + np.cumsum(rng.normal(0, 0.04, n))}, index=idx)
    # a stock that is 1.0 × market + 2.0 × semis + noise, and one that is pure market
    h["SEMI2X"] = px(m + 2 * semi + rng.normal(0, 0.005, n))
    h["MKT1X"] = px(m + rng.normal(0, 0.005, n))
    return h


def test_factors():
    h = _history()
    F = FA.factor_returns(h)
    assert list(F.columns) == ["mkt", "size", "mom", "lowvol", "rate", "usd", "semi"]      # VTV/VUG/QUAL absent → dropped
    pub = FA.build_public(h)
    assert pub["available"] and "SEMI2X" in pub["sym"] and "SPY" in pub["sym"]
    k = pub["keys"]
    b = dict(zip(k, pub["sym"]["SEMI2X"]))
    assert abs(b["semi"] - 2.0) < 0.25 and abs(b["mkt"] - 1.0) < 0.25, b                  # ridge shrinks a little, not much
    b1 = dict(zip(k, pub["sym"]["MKT1X"]))
    assert abs(b1["mkt"] - 1.0) < 0.15 and abs(b1["semi"]) < 0.15, b1
    p = FA.portfolio({"SEMI2X": 0.5, "MKT1X": 0.3, "NOPE": 0.2}, pub)
    assert p["missing"] == ["NOPE"] and abs(p["covered"] - 0.8) < 1e-9
    assert abs(p["exposure"]["semi"] - (0.5 * b["semi"] + 0.3 * b1["semi"]) / 0.8) < 1e-9     # normalised to the covered part
    assert abs(sum(p["risk_contrib"].values()) - p["factor_share"]) < 1e-9
    assert max(p["risk_contrib"], key=p["risk_contrib"].get) == "semi"
    lines = FA.headline(p, pub)
    assert any("半導體" in x for x in lines) and len(lines) == 3


XML = b"""<?xml version="1.0"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:us-gaap="http://fasb.org/us-gaap/2024">
 <context id="FY"><entity><identifier scheme="x">1</identifier></entity><period><startDate>2025-07-01</startDate><endDate>2026-06-30</endDate></period></context>
 <context id="CN"><entity><identifier scheme="x">1</identifier><segment><xbrldi:explicitMember dimension="srt:StatementGeographicalAxis">country:CN</xbrldi:explicitMember></segment></entity><period><startDate>2025-07-01</startDate><endDate>2026-06-30</endDate></period></context>
 <context id="TW"><entity><identifier scheme="x">1</identifier><segment><xbrldi:explicitMember dimension="srt:StatementGeographicalAxis">country:TW</xbrldi:explicitMember></segment></entity><period><startDate>2025-07-01</startDate><endDate>2026-06-30</endDate></period></context>
 <context id="NA"><entity><identifier scheme="x">1</identifier><segment><xbrldi:explicitMember dimension="srt:StatementGeographicalAxis">srt:NorthAmericaMember</xbrldi:explicitMember></segment></entity><period><startDate>2025-07-01</startDate><endDate>2026-06-30</endDate></period></context>
 <context id="C1"><entity><identifier scheme="x">1</identifier><segment>
   <xbrldi:explicitMember dimension="srt:MajorCustomersAxis">abc:LargestCustomerMember</xbrldi:explicitMember>
   <xbrldi:explicitMember dimension="us-gaap:ConcentrationRiskByBenchmarkAxis">us-gaap:RevenueFromContractWithCustomerMember</xbrldi:explicitMember>
   <xbrldi:explicitMember dimension="us-gaap:ConcentrationRiskByTypeAxis">us-gaap:CustomerConcentrationRiskMember</xbrldi:explicitMember></segment></entity>
   <period><startDate>2025-07-01</startDate><endDate>2026-06-30</endDate></period></context>
 <context id="Q4"><entity><identifier scheme="x">1</identifier></entity><period><startDate>2026-04-01</startDate><endDate>2026-06-30</endDate></period></context>
 <us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax contextRef="FY" unitRef="usd" decimals="-6">1000</us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax>
 <us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax contextRef="Q4" unitRef="usd" decimals="-6">300</us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax>
 <us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax contextRef="CN" unitRef="usd" decimals="-6">300</us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax>
 <us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax contextRef="TW" unitRef="usd" decimals="-6">250</us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax>
 <us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax contextRef="NA" unitRef="usd" decimals="-6">450</us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax>
 <us-gaap:ConcentrationRiskPercentage1 contextRef="C1" unitRef="pure" decimals="2">0.19</us-gaap:ConcentrationRiskPercentage1>
</xbrl>"""


def test_segments():
    r = SG.parse_instance(XML)
    assert r["period"] == "2026-06-30" and r["total"] == 1000 and r["basis"] == "amount"
    assert r["china"] == 0.3 and r["taiwan"] == 0.25
    assert r["us"] is None                                   # only "North America" tagged → not broken out, never 0 %
    assert [g["zh"] for g in r["geo"]] == ["北美", "中國", "台灣"]
    assert r["customers"][0]["share"] == 0.19 and r["customers"][0]["en"] == "Largest Customer"
    for m in ("nvda:UnitedStatesAndEuropeBasedEndCustomersMember", "asml:FourCustomersMember", "x:DistributorsMember"):
        assert not SG.single_customer(m), m                    # groups / regions are not "the largest customer"
    for m in ("tsm:CustomerAMember", "klac:LargestCustomerMember", "avgo:MajorCustomerOneMember"):
        assert SG.single_customer(m), m
    assert SG.label("country:KR")["zh"] == "南韓" and SG.label("klac:EuropeAndIsraelMember")["en"] == "Europe And Israel"
    none = SG.parse_instance(XML.replace(b"srt:StatementGeographicalAxis", b"x:OtherAxis").replace(b"CustomerConcentrationRiskMember", b"XMember"))
    assert not none["geo"] and not none["customers"] and "沒有用標準標籤" in none["note"]
    pub = SG.public({"KLAC": {"form": "10-K", **r}, "EMPTY": {"geo": [], "customers": []}})
    assert set(pub) == {"KLAC"} and pub["KLAC"]["cust"][0][2] == 0.19


def test_scorecard():
    idx = pd.bdate_range("2024-01-01", periods=400)
    rng = np.random.default_rng(5)
    closes = {f"S{i}": pd.Series(100 * np.cumprod(1 + rng.normal(0, 0.01, len(idx))), index=idx) for i in range(20)}
    winner = closes["S0"].copy()
    winner.iloc[200:] *= np.cumprod(np.full(len(idx) - 200, 1.004))          # S0 drifts up after day 200
    closes["S0"] = winner
    # pure noise → no claim; many independent days with a real edge → "works"
    noise = [(d, v) for d, v in zip(idx[:300], rng.normal(0, 0.05, 300))]
    assert SL.summarize(noise, 1, 20, h=20)["verdict"] in ("unclear", "insufficient")
    edge = [(d, v) for d, v in zip(idx[:390], 0.02 + rng.normal(0, 0.01, 390))]
    assert SL.summarize(edge, 1, 20, h=5)["verdict"] == "works"
    assert SL.summarize([(d, -v) for d, v in edge], -1, 20, h=5)["verdict"] == "works"      # a caution flag that lags = works
    few = [(idx[0], 0.1)] * 25                                                              # 25 signals, one day → one observation
    assert SL.summarize(few, 1, 20, h=20)["verdict"] == "insufficient"
    # ledger: record dedupes within 10 days, evaluate scores only matured entries vs the same-day average
    rows = [{"sym": "S0", "tier": "A", "price": 100.0, "patterns": [{"pattern": "high52"}], "strength": 70}]
    led = SL.record([], "us", "2024-11-01", rows, [])
    led = SL.record(led, "us", "2024-11-05", rows, [])
    assert len(led) == 1 and led[0]["kind"] == "A"
    led = SL.record(led, "us", "2024-11-20", rows, [{"sym": "S1", "price": 50.0, "exh": {"n": 2, "flags": ["rsi", "stretch"]}}])
    ev = SL.evaluate(led, "us", closes)
    assert ev["logged"] == 3 and ev["by_kind"]["exh"] == 1
    a5 = ev["h"]["5"]["A"]
    assert a5["n"] >= 1 and a5["verdict"] == "insufficient"


def test_site_sections():
    from tools import site_quant as SQ
    h = _history()
    pub = FA.build_public(h)
    html = SQ.sec_factor_returns(types.SimpleNamespace(factors=pub))
    assert "風格因子報酬" in html and "半導體" in html and " bp" in html
    rp = {"5": {"high52": {"n": 300, "n_eff": 60, "mean": 0.9, "lo": 0.2, "hi": 1.6, "hit": 55, "verdict": "works"},
                "_all": {"n": 2000, "n_eff": 90, "mean": 0.0, "lo": -0.3, "hi": 0.3, "hit": 50, "verdict": "unclear"}}}
    sg = {"available": True, "markets": {"us": {"replay": rp, "ledger": {"logged": 3, "since": "2026-10-21", "by_kind": {"A": 2, "B": 0, "C": 0, "exh": 1}, "h": {}}}}}
    html = SQ.sec_signal_scorecard(types.SimpleNamespace(signals=sg))
    import re
    txt = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", html))                 # visible text, tags and spaces removed
    assert "訊號成績單" in txt and "✅有效" in txt and "➖沒有明顯優勢" in txt and "已記錄3個訊號" in txt
    assert SQ.sec_rev_exposure(types.SimpleNamespace(segments={})) == ""


def test_calendar_and_bp():
    from datetime import datetime, timezone
    from wsb.analytics import premarket as PM
    # Thanksgiving 2026-11-26 (Thu) is skipped: the evening before, the next US open is Friday 11-27
    nxt = PM.next_open(datetime(2026, 11, 26, 2, 0, tzinfo=timezone.utc), PM.NY, 9, 30, "us")
    assert nxt.strftime("%Y-%m-%d %H:%M") == "2026-11-27 09:30", nxt
    # Taiwan Lunar New Year 2027: the next open is a weekday that is not a national holiday
    import holidays
    tw = PM.next_open(datetime(2027, 2, 6, 3, 0, tzinfo=timezone.utc), PM.TPE, 9, 0, "tw")
    assert tw.weekday() < 5 and tw.date() not in holidays.country_holidays("TW", years=2027)
    # a yield quoted 5.036 and down 2.14 % of its level = about −11 bp (not −2.14 points)
    assert abs(PM._bp({"px": 5.036, "ch": -2.14}) - (5.036 - 5.036 / 0.9786) * 100) < 1e-9
    assert abs(PM._bp({"px": 50.36, "ch": -2.14}) - PM._bp({"px": 5.036, "ch": -2.14})) < 1e-9     # ×10 feeds
    small = {"overnight": [{"t": "ES=F", "zh": "", "en": "", "ch": -0.5, "sigma": 0.8},
                           {"t": "^TNX", "zh": "", "en": "", "px": 5.0, "ch": 0.4, "sigma": 1}],      # +2 bp only
             "us_range": {"sigma": 1.0}, "levels": {}, "events": [], "earnings": []}
    assert not any("殖利率卻上升" in x["zh"] for x in PM.takeaways_us(small))                   # noise is not a rates scare
    big = {**small, "overnight": [small["overnight"][0], {"t": "^TNX", "zh": "", "en": "", "px": 5.0, "ch": 2.0, "sigma": 1}]}
    assert any("殖利率卻上升" in x["zh"] for x in PM.takeaways_us(big))                         # ~ +10 bp is


def test_takeaways():
    from wsb.analytics import premarket as PM
    from tools import site_quant as SQ

    def it(t, ch, sig):
        return {"t": t, "zh": t, "en": t, "ch": ch, "sigma": sig}
    rough = {"overnight": [it("ES=F", -0.93, 0.8), it("NQ=F", -1.59, 1.1), it("^TNX", -2.1, 1.2), it("CL=F", 2.3, 2.0),
                           it("GC=F", -1.5, 1.0), it("BTC-USD", -2.8, 2.5), it("^N225", -2.65, 1.1), it("^KS11", -3.5, 1.3),
                           it("^HSI", -3.0, 1.2), it("^TWII", -1.8, 1.0)],
             "us_range": {"sigma": 1.13}, "levels": {"spot": 7728, "zero_gamma": 7738}, "events": [], "earnings": [{"sym": "HON", "mv": 4.5}]}
    t = PM.takeaways_us(rough)
    txt = " ".join(x["zh"] for x in t)
    assert t[0]["lv"] == "alert" and "亞股全面下跌" in txt and "黃金、比特幣同時下跌" in txt and "那指期貨" in txt
    assert "Gamma 翻轉點" in txt and "HON ±4.5%" in txt and "0.8 倍" in txt
    calm = {"overnight": [it("ES=F", 0.1, 0.8), it("NQ=F", 0.2, 1.1), it("^N225", 0.3, 1.1), it("^KS11", -0.2, 1.3)],
            "us_range": {"sigma": 1.0}, "levels": {}, "events": [{"zh": "CPI", "en": "CPI", "tpe": "20:30"}], "earnings": []}
    tc = PM.takeaways_us(calm)
    assert all(x["lv"] != "alert" for x in tc) and any("CPI" in x["zh"] for x in tc)      # a quiet night raises no alarm
    tw = PM.takeaways_tw({"us_close": [{"t": "^SOX", "zh": "", "en": "", "ch": -3.4}, {"t": "TWD=X", "zh": "", "en": "", "ch": 0.4}],
                          "tw_link": {"implied": -1.1, "corr": 0.6}})
    assert tw[0]["lv"] == "alert" and "台幣貶值" in " ".join(x["zh"] for x in tw)
    html = SQ._takeaways(t)
    assert "今天的重點" in html and html.index("🔴") < html.index("🟡")


def test_premarket():
    import math
    from datetime import datetime, timezone
    from wsb.analytics import premarket as PM
    from tools import site_quant as SQ
    # open times in Taipei, across the US daylight-saving switch (11/1) and a weekend
    assert PM.next_open(datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc), PM.NY, 9, 30).astimezone(PM.TPE).strftime("%m-%d %H:%M") == "10-21 21:30"
    assert PM.next_open(datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc), PM.NY, 9, 30).astimezone(PM.TPE).strftime("%m-%d %H:%M") == "11-02 22:30"
    assert PM.next_open(datetime(2026, 10, 24, 1, 0, tzinfo=timezone.utc), PM.TPE, 9, 0).strftime("%m-%d %H:%M") == "10-26 09:00"   # Sat → Mon
    # band record: returns drawn with exactly the stated sigma land inside ±1σ ~68 % of the time
    rng = np.random.default_rng(9)
    idx = pd.bdate_range("2010-01-01", periods=3000)
    sig = pd.Series(1.0, index=idx)
    close = pd.Series(100 * np.cumprod(1 + rng.normal(0, 0.01, len(idx))), index=idx)
    r = PM.band_record(close, sig)
    assert 64 < r["all"]["in1"] < 72 and 93 < r["all"]["in2"] < 97, r
    # the card renders from a small fake engine
    h = _history()
    h["^GSPC"], h["^VIX"] = h["SPY"] * 10, 18.0
    q = {"ES=F": {"price": 5800.0, "chg_pct": 0.3, "asof": "2026-10-21"}, "^VIX": {"price": 18.0, "chg_pct": -2.0}}
    mk = types.SimpleNamespace(q=lambda t: q.get(t), series=lambda t: h[t] if t in h else pd.Series(dtype=float))
    eng = types.SimpleNamespace(market=mk, econ_view={"events": []}, techearn={}, sx={}, options=None)
    d = PM.build(eng, datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc))
    assert abs(d["us_range"]["sigma"] - 18 / math.sqrt(252)) < 1e-9 and d["overnight"][0]["t"] == "ES=F"
    html = SQ.sec_premarket(eng)
    assert 'id="pmbox"' in html and "pmmine" in html and "不預測漲跌方向" in html and "±1.13%" in html


def test_licensing():
    from wsb.data import fred as FR
    from tools import site_legal as LG
    assert FR.restricted("BAMLH0A0HYM2") and FR.restricted("BAA10Y") and not FR.restricted("DGS10")
    assert FR.restricted_component({"src": "fred", "series": "BAMLH0A3HYC", "kind": "level"})
    assert FR.restricted_component({"src": "fred", "series": "DGS10", "kind": "spread:BAMLH0A1HYBB"})   # the other leg counts
    assert not FR.restricted_component({"src": "px", "series": "HYG", "kind": "level"})
    assert FR.direction(0.3) == "擴大" and FR.direction(-0.1) == "收斂" and FR.direction(None) == "—"
    t = LG.sec_terms(None) + LG.sec_privacy(None)
    assert "不是投資建議" in t and "github.com/bkhotey4/wallstreet-sentinel/issues" in t and "drive.appdata" in t and "ICE Data Indices" in t
    assert "&lt;b&gt;" not in t and "&lt;code&gt;" not in t                    # no escaped markup leaking into the text


def test_dispersion():
    from wsb.analytics import dispersion as DS
    from tools import site_quant as SQ
    a = DS.parse_cboe("DATE,OPEN,HIGH,LOW,CLOSE\n01/03/2006,23.5,23.5,23.5,23.5\n01/04/2006,24,24,24,24.1\n")
    b = DS.parse_cboe("DATE,DSPX\n06/19/2014,17.81\n06/20/2014,18.0\n")
    assert list(a.values) == [23.5, 24.1] and str(a.index[0].date()) == "2006-01-03" and b.iloc[-1] == 18.0
    # index flat at its high while 40 stocks slide late in the window → wide, unusual gap
    idx = pd.bdate_range("2023-01-02", periods=600)
    rng = np.random.default_rng(4)
    index = pd.Series(100 + np.linspace(0, 10, 600), index=idx)
    closes = {}
    for i in range(40):
        p_ = 100 * np.cumprod(1 + rng.normal(0.0005, 0.01, 600))
        p_[-60:] *= np.linspace(1, 0.75, 60)                      # every stock −25 % over the last 3 months
        closes[f"S{i}"] = pd.Series(p_, index=idx)
    g = DS.gap(index, closes)
    assert g["index_dd"] > -0.5 and g["median_dd"] < -15 and g["gap"] < -15 and g["gap_pct"] > 95 and g["below10"] > 80
    rd = DS.readings(g, {"rel_3m": -4.0}, {"COR1M": {"pct": 3}, "DSPX": {"pct": 90}},
                     {"episodes": 9, "h": 21, "dc_low": 3.0, "dc_all": -1.0, "rise5_low": 40, "rise5_all": 30, "dd5_low": 10, "dd5_all": 18})
    txt = " ".join(r["zh"] for r in rd)
    assert "少數大型股撐住" in txt and "等權重" in txt and "各走各的" in txt and "並沒有比較常大跌" in txt
    assert not DS.readings(None, None, {"COR1M": {"pct": 50}}, None)
    # what followed low-correlation days: a series that is low then rises
    cidx = pd.bdate_range("2006-01-02", periods=1600)
    cor = pd.Series(np.r_[30 + rng.normal(0, 2, 1300), np.full(100, 5.0), np.linspace(5, 30, 200)], index=cidx)   # normal, dip, recovery
    spx = pd.Series(np.linspace(1000, 2000, 1600), index=cidx)
    af = DS.low_corr_after(cor, spx)
    assert af and af["rise5_low"] > af["rise5_all"] and af["dd5_low"] == 0 and af["episodes"] >= 1
    eng = types.SimpleNamespace(dispersion={"available": True, "us": g, "ew": {"rel_1m": 1.0, "rel_3m": -4.0},
                                            "cboe": {"COR1M": {"now": 8.35, "pct": 2.1, "pct_3y": 12.6, "since": "2006", "asof": "2026-10-20"}}, "readings": rd})
    html = SQ.sec_index_vs_stocks(eng)
    assert "指數 vs 個股" in html and "8.35" in html and "中位數個股" in html


def main():
    test_calendar_and_bp()
    test_takeaways()
    test_dispersion()
    test_licensing()
    test_premarket()
    test_factors()
    test_segments()
    test_scorecard()
    test_site_sections()
    print("QUANT TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
