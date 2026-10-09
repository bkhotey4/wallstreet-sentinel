"""2026-10 expansion: stock scoring board, 13F / Form 4, Treasury zone, sector rotation, time machine, PWA.
Offline (synthetic data + saved SEC/TreasuryDirect/TWSE response shapes).   python -m tests.test_expansion"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import tests.test_offline as T
from wsb.analytics import breadth as BD
from wsb.analytics import signals as SG
from wsb.analytics import stockscore as SS
from wsb.analytics.stress import StressEngine
from wsb.data import edgar_holdings as EH
from wsb.data import stocknews as SN
from wsb.data import treasury as TR
from wsb.data.stocks import all_symbols, universe
from wsb.engine import Engine
from wsb.health import HEALTH
from tools import build_site as B

INFOTABLE = """<informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
<infoTable><nameOfIssuer>APPLE INC</nameOfIssuer><titleOfClass>COM</titleOfClass><cusip>037833100</cusip><value>{a}</value>
<shrsOrPrnAmt><sshPrnamt>{ash}</sshPrnamt><sshPrnamtType>SH</sshPrnamtType></shrsOrPrnAmt></infoTable>
<infoTable><nameOfIssuer>BANK OF AMER CORP</nameOfIssuer><titleOfClass>COM</titleOfClass><cusip>060505104</cusip><value>{b}</value>
<shrsOrPrnAmt><sshPrnamt>{bsh}</sshPrnamt><sshPrnamtType>SH</sshPrnamtType></shrsOrPrnAmt></infoTable>
{extra}</informationTable>"""
PUT = """<infoTable><nameOfIssuer>NVIDIA CORPORATION</nameOfIssuer><titleOfClass>COM</titleOfClass><cusip>67066G104</cusip><value>900000000</value>
<shrsOrPrnAmt><sshPrnamt>5000000</sshPrnamt><sshPrnamtType>SH</sshPrnamtType></shrsOrPrnAmt><putCall>Put</putCall></infoTable>"""
FORM4 = """<?xml version="1.0"?><ownershipDocument><issuer><issuerTradingSymbol>{sym}</issuerTradingSymbol></issuer>
<reportingOwner><reportingOwnerId><rptOwnerName>DOE JANE</rptOwnerName></reportingOwnerId>
<reportingOwnerRelationship><isDirector>false</isDirector><isOfficer>true</isOfficer><officerTitle>CEO</officerTitle></reportingOwnerRelationship></reportingOwner>
<aff10b5One>{plan}</aff10b5One><nonDerivativeTable>
<nonDerivativeTransaction><transactionDate><value>2026-10-01</value></transactionDate><transactionCoding><transactionCode>{code}</transactionCode></transactionCoding>
<transactionAmounts><transactionShares><value>{sh}</value></transactionShares><transactionPricePerShare><value>{px}</value></transactionPricePerShare>
<transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode></transactionAmounts></nonDerivativeTransaction>
<nonDerivativeTransaction><transactionDate><value>2026-10-01</value></transactionDate><transactionCoding><transactionCode>M</transactionCode></transactionCoding>
<transactionAmounts><transactionShares><value>999999</value></transactionShares><transactionPricePerShare><value>1</value></transactionPricePerShare></transactionAmounts></nonDerivativeTransaction>
</nonDerivativeTable><footnotes><footnote id="F1">Weighted average price.</footnote></footnotes></ownershipDocument>"""


class FakePrices:
    """Synthetic close/volume for every symbol in the scoring universe (half trending up, half down)."""
    def __init__(self, end: pd.Timestamp):
        idx = pd.bdate_range(end=end, periods=420)
        rng = np.random.default_rng(5)
        close, vol = {}, {}
        for i, s in enumerate(all_symbols()):
            drift = 0.0012 if i % 2 == 0 else -0.0008
            r = rng.normal(drift, 0.015, len(idx))
            close[s] = 100 * np.exp(np.cumsum(r))
            vol[s] = rng.integers(2_000_000, 9_000_000, len(idx)).astype(float)
        self.close, self.volume, self.ts = pd.DataFrame(close, index=idx), pd.DataFrame(vol, index=idx), time.time()

    async def refresh(self, force=False):
        return None

    def series(self, s):
        return self.close[s].dropna() if s in self.close else pd.Series(dtype=float)

    def vol(self, s):
        return self.volume[s].dropna() if s in self.volume else pd.Series(dtype=float)


def test_parsers():
    assert SN.polarity("Nvidia shares surge after earnings beat") == 1
    assert SN.polarity("Intel stock plunges on weak demand warning") == -1
    assert SN.polarity("台積電營收創新高 外資大舉買超") == 1 and SN.polarity("鴻海重挫 法人下修目標價") == -1
    assert SN.match_names("Meta and Apple rally", [("META", "Meta"), ("AAPL", "Apple"), ("INTC", "Intel")]) == ["META", "AAPL"]
    assert SN.match_names("Intelligence spending rises", [("INTC", "Intel")]) == [], "whole-word match only"
    # 13F: thousands vs dollars auto-detected; puts kept separate
    k = EH.parse_infotable(INFOTABLE.format(a=66000, ash=300000, b=27500, bsh=600000, extra=""))      # thousands
    d = EH.parse_infotable(INFOTABLE.format(a=66000000, ash=300000, b=27500000, bsh=600000, extra=PUT))
    assert abs(k[0]["value"] - 66e6) < 1 and abs(d[0]["value"] - 9e8) < 1 and d[0]["pc"] == "Put"
    prev = EH.parse_infotable(INFOTABLE.format(a=60000000, ash=200000, b=30000000, bsh=900000, extra=""))
    ch = EH.compare(d, prev)
    assert [x["name"] for x in ch["new"]] == ["NVIDIA CORPORATION"] and ch["add"][0]["name"] == "APPLE INC"
    assert ch["cut"][0]["name"] == "BANK OF AMER CORP" and not ch["exit"]
    assert EH.norm_name("BANK OF AMER CORP") == EH.norm_name("Bank of America Corp /DE/") == "BANK AMERICA"
    f = EH.parse_form4(FORM4.format(sym="AAPL", plan="true", code="S", sh=1000, px=200))
    assert f["plan"] and f["title"] == "CEO" and len(f["tx"]) == 1 and f["tx"][0]["usd"] == 200000, "M (exercise) ignored"
    # Treasury: TIPS / not-yet-auctioned rows dropped; judged vs the same tenor's history
    base = {"securityType": "Note", "tips": "No", "floatingRate": "No", "reopening": "No", "offeringAmount": "40000000000"}
    rows = []
    for i in range(7):
        rows.append({**base, "cusip": f"C{i}", "auctionDate": f"2026-0{i + 3}-10T00:00:00", "securityTerm": "10-Year",
                     "originalSecurityTerm": "10-Year", "highYield": "4.5", "bidToCoverRatio": "2.6" if i < 6 else "2.2",
                     "competitiveAccepted": "39000000000", "primaryDealerAccepted": "5000000000" if i < 6 else "9000000000",
                     "indirectBidderAccepted": "26000000000", "directBidderAccepted": "8000000000"})
    rows.append({**base, "cusip": "TIPS", "tips": "Yes", "auctionDate": "2026-09-20", "originalSecurityTerm": "10-Year",
                 "highYield": "2", "bidToCoverRatio": "2", "competitiveAccepted": "1"})
    rows.append({**base, "cusip": "FUT", "auctionDate": "2026-10-20", "originalSecurityTerm": "10-Year", "highYield": "",
                 "bidToCoverRatio": "", "competitiveAccepted": ""})
    j = TR.judge(TR.parse_auctions(rows))
    assert len(j) == 7 and j[0]["verdict"] == "偏弱" and j[1]["verdict"] == "正常" and j[-1]["verdict"] is None
    print("  parsers ok (news tone, 13F, Form 4, auctions)")


def test_signal_patterns():
    idx = pd.bdate_range(end="2026-10-07", periods=400)
    v = pd.Series(1e6, index=idx)
    c = pd.Series(100 * np.exp(np.linspace(0, 0.6, 400)), index=idx)                 # uptrend, dip to the MA, bounce
    c.iloc[-6:-1] = c.iloc[-7] * np.array([0.985, 0.97, 0.96, 0.955, 0.958])
    c.iloc[-1] = c.iloc[-2] * 1.012
    d = SG.detect(c, v)
    assert d["pullback"]["flag"].iloc[-1] and d["pullback"]["inv"].iloc[-1] < c.iloc[-1]
    c2 = pd.Series(100 + np.sin(np.arange(400) / 9) * 2 + np.linspace(0, 10, 400), index=idx)
    c2.iloc[-1] = c2.iloc[-21:-1].max() * 1.03
    v2 = v.copy()
    v2.iloc[-1] = 3e6
    d2 = SG.detect(c2, v2)
    assert d2["breakout"]["flag"].iloc[-1] and not SG.detect(c2, v)["breakout"]["flag"].iloc[-1], "needs volume"
    c3 = pd.Series(100 * np.exp(np.linspace(0, 0.2, 400)), index=idx)
    c3.iloc[-12:-1] = c3.iloc[-13] * np.cumprod([0.97] * 11)
    c3.iloc[-1] = c3.iloc[-2] * 1.04
    assert SG.detect(c3, v)["oversold"]["flag"].iloc[-1]
    c4 = pd.Series(100 * np.exp(np.concatenate([np.linspace(0, -0.3, 250), np.linspace(-0.3, 0.15, 150)])), index=idx)
    assert SG.detect(c4, v)["golden"]["flag"].sum() > 0
    bt = SG.backtest({"A": d, "B": d2})
    assert set(bt) == set(SG.PATTERNS) and bt["pullback"]["base_win"] is not None
    rng = np.random.default_rng(3)
    # 強勢股淺回檔: steady strong uptrend, a ~3% dip to the 10-day, then an up close
    c5 = pd.Series(100 * np.exp(np.linspace(0, 0.9, 400) + rng.normal(0, 0.004, 400)), index=idx)
    c5.iloc[-3] = c5.iloc[-4] * 0.985
    c5.iloc[-2] = c5.iloc[-3] * 0.985
    c5.iloc[-1] = c5.iloc[-2] * 1.03
    d5 = SG.detect(c5, v)
    assert d5["shallow"]["flag"].iloc[-1], d5["shallow"].tail(3)
    # 收斂後突破 + 創 52 週新高: volatile rise, a very quiet 10-day box near the high, then a volume breakout
    c6 = pd.Series(100 * np.exp(np.linspace(0, 0.5, 400) + rng.normal(0, 0.02, 400)), index=idx)
    top = c6.iloc[:-12].max()
    c6.iloc[-12:-1] = top * (1 + rng.normal(0, 0.002, 11))
    c6.iloc[-1] = c6.iloc[-12:-1].max() * 1.03
    v6 = v.copy()
    v6.iloc[-1] = 2.5e6
    d6 = SG.detect(c6, v6)
    assert d6["vcp"]["flag"].iloc[-1] and d6["high52"]["flag"].iloc[-1]
    assert not SG.detect(c6, v)["vcp"]["flag"].iloc[-1], "VCP needs volume"
    # MACD 黃金交叉 only in an uptrend
    assert d5["macd"]["flag"].sum() > 0 and SG.detect(c4.iloc[:250], v)["macd"]["flag"].sum() == 0
    # ATR-scaled zone: a volatile stock gets a wider zone than the 3% floor, a calm one keeps 3%
    assert abs(SG.zone_width(100, 0.03, 1.0) - 3.0) < 1e-9 and SG.zone_width(100, 0.03, 6.0) == 6.0 and SG.zone_width(100, 0.03, 20) == 10.0
    pl = SG.plan("vcp", d6["vcp"], idx[-1], float(d6["vcp"]["inv"].iloc[-1]))
    assert pl["zone_lo"] < pl["zone_hi"] and "收斂區上緣" in pl["zone"]
    print("  signal patterns ok")


def test_fullmarket(eng):
    """Whole-market lists → price queue → scan → published JSON (all offline)."""
    import io as _io
    from wsb.analytics import fullscan as FS
    from wsb.data import fullmarket as FMD
    from wsb.data import stocks as STK
    # HKEX xlsx parsing (header row found by name; only Main Board equities kept)
    df = pd.DataFrame([["List of Securities", None, None, None], [None, None, None, None],
                       ["Stock Code", "Name of Securities", "Category", "Sub-Category"],
                       ["00700", "TENCENT", "Equity", "Equity Securities (Main Board)"],
                       ["08001", "GEM CO", "Equity", "Equity Securities (GEM)"], ["04335", "SOME BOND", "Debt Securities", "x"]])
    buf = _io.BytesIO()
    df.to_excel(buf, header=False, index=False)
    hk = FMD.parse_hkex(buf.getvalue(), "Stock Code")
    assert list(hk["Stock Code"]) == ["00700", "08001", "04335"]
    assert FMD._clean_us_name("Nu Holdings Ltd. Class A Ordinary Shares") == "Nu Holdings Ltd."
    # price queue: missing names are back-filled, failures remembered, everything merged into the archive
    idx = pd.bdate_range(end=T.END, periods=320)
    rng = np.random.default_rng(9)
    syms = [f"U{i:03d}" for i in range(60)] + ["DEAD"]

    def fake_dl(part, period):
        ok = [s for s in part if s != "DEAD"]
        cl = pd.DataFrame({s: 50 * np.exp(np.cumsum(rng.normal(0.0006 * (1 + int(s[1:]) % 3 - 1), 0.02, len(idx)))) for s in ok}, index=idx)
        vo = pd.DataFrame({s: rng.integers(1e5, 1e6, len(idx)).astype(float) for s in ok}, index=idx)
        return cl, vo
    STK._download = fake_dl
    st = FMD.refresh_prices("us", syms, idx[-1], time.time() + 60)
    assert st["backfilled"] == 61 and st["have"] == 60 and st["failed"] == 1 and st["pending"] == 0, st
    st2 = FMD.refresh_prices("us", syms, idx[-1], time.time() + 60)
    assert st2["backfilled"] == 0 and st2["updated"] == 0, "nothing to do on a second run the same day"
    close, volume = FMD.load_prices("us")
    items = [{"sym": s, "code": s, "name": f"Name {s}", "ind": "科技" if i % 2 else "金融"} for i, s in enumerate(syms)]
    res = FS.scan("us", items, close, volume, close.mean(axis=1))
    assert res["available"] and res["n"] == 60 and res["cols"] == FS.COLS
    rows = [dict(zip(res["cols"], r)) for r in res["rows"]]
    assert [r["rank"] for r in rows] == list(range(1, 61)) and all(r["st"] for r in rows)
    sig = [r for r in rows if r["st"] == "signal"]
    assert all(r["zlo"] <= r["zhi"] and r["inv"] < r["px"] for r in sig)
    assert all(r["when"] for r in rows if r["st"] not in ("signal", "nodata"))
    assert all(r["st"] == "signal" and r["inz"] and r["pat"] != "oversold" for r in rows if r.get("pk"))
    assert sorted(r["pk"] for r in rows if r.get("pk")) == list(range(1, 1 + sum(1 for r in rows if r.get("pk"))))
    # run(): lists come from the (patched) list loader, JSON is written and later published under site/market/
    async def fake_lists(force=False):
        return {"us": items, "tw": [], "hk": []}
    FMD.lists = fake_lists
    rep = asyncio.run(FS.run(eng, 30))
    assert rep["us"]["scanned"] == 60 and FS.published("us")["n"] == 60
    print("  full-market ok")


def make_engine(tmp: Path):
    eng = Engine()
    eng.market, eng.fred = T.m, T.fr
    eng.stress_engine = StressEngine(T.m, T.fr)
    eng.calendar.events = []
    eng.stockprices = FakePrices(T.END)
    eng.stockprices.close.loc[eng.stockprices.close.index[:-82], "SPCX"] = np.nan        # a recent IPO: only 82 sessions
    # curve + term premium (FRED), auctions
    di = pd.bdate_range(end=T.END, periods=900)
    for sid, y in TR.TENORS:
        eng.fred.series[sid] = pd.Series(4 + 0.05 * y + np.sin(np.arange(len(di)) / 90) * 0.4, index=di)
    eng.fred.series["THREEFYTP10"] = pd.Series(np.linspace(-0.5, 0.9, len(di)), index=di)
    eng.treasury.auctions = TR.judge([{"date": (date(2026, 3, 1) + timedelta(days=30 * i)).isoformat(), "term": "10-Year", "label": "10-Year",
                                        "reopen": False, "high_yield": 4.5, "btc": 2.6 - (0.5 if i == 6 else 0), "dealer": 12, "indirect": 68,
                                        "direct": 20, "size_bn": 39, "cusip": f"X{i}"} for i in range(7)])
    # news per stock, Taiwan flows, dark-pool per stock, insiders, 13F
    eng.stocknews.items = {"NVDA": [{"t": "Nvidia surges", "l": "https://e.com", "ts": time.time(), "src": "X", "p": 1}] * 3,
                           "INTC": [{"t": "Intel plunges", "l": "https://e.com", "ts": time.time(), "src": "X", "p": -1}] * 2}
    for k in range(5):
        eng.taiwan.t86_hist[f"2026-10-0{k + 1}"] = {"2330": [3000.0, 500.0, 3600.0], "2317": [-4000.0, -200.0, -4300.0]}
    days = {}
    for k, d in enumerate(pd.bdate_range(end=T.END, periods=40)):
        days[d.strftime("%Y-%m-%d")] = {"AAPL": [40 + (k > 34) * 20, 100], "MSFT": [45, 100]}
    eng.darkpool.days = days
    eng.darkpool._per = {}
    today = date.today().isoformat()
    eng.insiders.data = {"ts": time.time(), "forms": {
        "a1": {"sym": "AAPL", "issuer": "AAPL", "filed": today, "owner": "COOK TIM", "title": "CEO", "plan": False,
               "tx": [{"code": "S", "date": today, "shares": 300000, "price": 250.0, "usd": 75e6}], "url": "https://www.sec.gov/x/"},
        "a2": {"sym": "MSFT", "issuer": "MSFT", "filed": today, "owner": "SMITH", "title": "Director", "plan": False,
               "tx": [{"code": "P", "date": today, "shares": 10000, "price": 400.0, "usd": 4e6}], "url": "https://www.sec.gov/y/"}}}
    eng.insiders.data["forms"]["a3"] = {"sym": "BRK-B", "issuer": "OXY", "filed": today, "owner": "BERKSHIRE", "title": "10% owner",
                                        "plan": False, "tx": [{"code": "P", "date": today, "shares": 1e6, "price": 50.0, "usd": 5e7}]}
    eng.insiders._build()
    assert eng.insiders.ticker("BRK-B") is None, "Berkshire buying OXY is not an insider trade in BRK"
    assert EH.same_issuer("BRK-B", "BRKA") and not EH.same_issuer("BRK-B", "OXY")
    cur = EH.parse_infotable(INFOTABLE.format(a=66000000000, ash=300000000, b=27500000000, bsh=600000000, extra=PUT))
    prv = EH.parse_infotable(INFOTABLE.format(a=60000000000, ash=200000000, b=30000000000, bsh=900000000, extra=""))
    eng.gurus.data = {"ts": time.time(), "managers": {
        "1067983": {"filings": [{"acc": "1", "filed": today, "period": "2026-06-30", "url": "https://www.sec.gov/b/", "holdings": cur},
                                {"acc": "0", "filed": "2026-05-15", "period": "2026-03-31", "holdings": prv}]},
        "1649339": {"filings": [{"acc": "9", "filed": "2025-11-03", "period": "2025-09-30", "url": "https://www.sec.gov/s/", "holdings": cur}]}}}
    eng.gurus._build()
    eng.gurus.set_names({"AAPL": "APPLE", "BAC": "BANK AMERICA"})
    return eng


def main():
    test_parsers()
    test_signal_patterns()
    tmp = Path("/tmp/wsb_expansion")
    shutil.rmtree(tmp, ignore_errors=True)
    eng = make_engine(tmp)
    HEALTH.ok("yahoo_quotes", 90, every=300)
    asyncio.run(eng.recompute())
    sc = eng.scores
    assert sc["available"] and set(sc["markets"]) == {"us", "tw", "hk"}, sc.get("markets", {}).keys()
    us = sc["markets"]["us"]["rows"]
    assert len(us) == len(universe()["us"]["symbols"]) and us[0]["score"] >= us[-1]["score"] and us[0]["rank"] == 1
    assert all(0 <= r["score"] <= 100 for m in sc["markets"].values() for r in m["rows"])
    # 5-day change: history keyed by the market's own session dates (weekends never count)
    asof = sc["markets"]["us"]["asof"]
    sess = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(end=pd.Timestamp(asof), periods=7)[:-1]]
    hist = {"us": {d: {"AAPL": 10.0 + i} for i, d in enumerate(sess)}}
    (SS._HIST).write_text(json.dumps(hist))
    asyncio.run(eng.recompute())
    sc = eng.scores
    aapl = next(r for r in sc["markets"]["us"]["rows"] if r["sym"] == "AAPL")
    assert aapl["chg5"] == round(aapl["score"] - 11.0, 1), (aapl["chg5"], aapl["score"])
    by = {r["sym"]: r for m in sc["markets"].values() for r in m["rows"]}
    keys = lambda s: {i["key"] for i in by[s]["intel_inputs"]}  # noqa: E731
    assert "news" in keys("NVDA") and by["NVDA"]["intel"] > 50 and by["INTC"]["intel"] < 50
    assert "insider" in keys("AAPL") and "darkpool" in keys("AAPL") and "gurus" in keys("AAPL")
    assert "tw_flow" in keys("2330.TW") and by["2330.TW"]["intel"] > 50 and by["2317.TW"]["intel"] < 50
    assert by["0700.HK"]["intel"] is None or "news" in keys("0700.HK"), "HK uses news only"
    assert eng.gurus.ticker("AAPL")["add"] == 1 and eng.gurus.ticker("BAC")["cut"] == 1
    gm = eng.gurus.result["managers"]
    assert gm[0]["stale"] is False and gm[1]["stale"] is True and gm[0]["options"][0]["pc"] == "Put"
    board = eng.insiders.board()
    assert board["sells"][0]["sym"] == "AAPL" and board["buys"][0]["sym"] == "MSFT" and "AAPL" in board["big"]
    bd = eng.bonds
    assert bd["available"] and len(bd["curves"]["now"]) == 11 and "10y2y" in bd["spreads"] and bd["auctions"][0]["verdict"] == "偏弱"
    rot = eng.rotation
    assert rot["available"] and rot["sectors"] and {r["quad"] for r in rot["sectors"]} <= {"領先", "轉弱", "落後", "改善"}
    assert set(rot["breadth"]) == {"us", "tw", "hk"} and 0 <= rot["breadth"]["us"]["now"] <= 100
    assert SS.summary_lines(sc) and TR.summary_lines(bd) and BD.summary_lines(rot)
    spx_row = next(r for r in sc["markets"]["us"]["rows"] if r["sym"] == "SPCX")                      # young listing is scored
    spx_all = next(r for r in eng.signals["markets"]["us"]["all"] if r["sym"] == "SPCX")
    assert spx_row["score"] is not None and (spx_all["signal"] or spx_all["status"]["status"] != "nodata"), spx_all
    assert "nan" not in json.dumps(spx_all.get("status") or {}, ensure_ascii=False)
    # ★ 規則精選: rules hold, at most n per market, picks are in zone & trend-following
    from wsb.analytics import signals as SGm
    assert SGm.pick_ok("pullback", 70, True, 2.0, 5) and SGm.pick_ok("breakout", 70, True, None, 5)
    assert not SGm.pick_ok("oversold", 90, True, 3, 3) and not SGm.pick_ok("pullback", 70, False, 3, 3)
    assert not SGm.pick_ok("pullback", 55, True, 3, 3) and not SGm.pick_ok("pullback", 70, True, 1.1, 3) and not SGm.pick_ok("pullback", 70, True, 3, 13)
    assert SGm.pick_ok("macd", 61, True, 1.2, 12)
    for m in eng.signals["markets"].values():
        pk = [r for r in m["rows"] if r.get("pick")]
        assert len(pk) <= 5 and m["picks"] == [r["sym"] for r in pk]
        for r in m["rows"]:                                   # tiers: A = pick, B = in zone, C = outside the zone
            assert r["tier"] == ("A" if r.get("pick") else "B" if r["patterns"][0]["plan"]["in_zone"] else "C")
        assert all(r["tier"] == "D" for r in m["all"] if r["status"]["status"] in SGm.NEAR_D)
        assert sum(m["tiers"].values()) == len(m["rows"]) + sum(1 for r in m["all"] if r["status"]["status"] in SGm.NEAR_D)
        for r in pk:
            assert r["patterns"][0]["plan"]["in_zone"] and r["patterns"][0]["pattern"] != "oversold"
    # themes: every row tagged, per-market and cross-market tables
    assert all(r.get("theme") for m in sc["markets"].values() for r in m["rows"])
    assert any(t["theme"] == "半導體" and len([k for k, v in t["per"].items() if v]) == 3 for t in sc["themes"]), "semis in US/TW/HK"
    assert any(r["sym"] == "KLAC" for r in sc["markets"]["us"]["rows"]) and any(r["theme"] == "國防軍工" for r in sc["markets"]["tw"]["rows"])
    sgr = eng.signals
    assert sgr["available"] and set(sgr["markets"]) == {"us", "tw", "hk"}
    allsig = [r for m in sgr["markets"].values() for r in m["rows"]]
    assert allsig and all(0 <= r["strength"] <= 100 and r["inv"] < r["price"] for r in allsig)
    assert all(m["rows"] == sorted(m["rows"], key=lambda r: -r["strength"]) for m in sgr["markets"].values())
    for k, m in sgr["markets"].items():                     # the table covers the WHOLE universe, not only stocks with a signal
        assert len(m["all"]) == len(universe()[k]["symbols"]) == m["n_universe"], (k, len(m["all"]))
        assert all(r["status"]["label"] for r in m["all"]) and sum(1 for r in m["all"] if r["signal"]) == len(m["rows"])
    # site: new tabs, sections, PWA, time machine (snapshot written once, index published)
    test_fullmarket(eng)
    out, snap = tmp / "site", tmp / "snapdir"
    B.update_snapshots.__globals__["SETTINGS"].raw.setdefault("snapshots", {})["min_hour"] = 0
    p = asyncio.run(B.build(out, use_ai=False, engine=eng, snapdir=snap))
    page = p.read_text(encoding="utf-8")
    for k in ("scores", "gurus", "bonds", "rotation", "history"):
        assert f'id="p-{k}"' in page and f'href="#{k}"' in page, k
    assert "個股評分表（由高到低）" in page and "個股評分前五名" in page and "台積電" in page and "騰訊" in page
    assert "波克夏（巴菲特）" in page and "賣權（看空）" in page and "可能已停止申報" in page
    assert "內部人買賣（Form 4）" in page and "美債專區" in page and 'id="c_curve"' in page and "偏弱" in page
    assert "類股輪動與市場寬度" in page and 'id="c_rot"' in page and 'id="c_br0"' in page
    assert (out / "market" / "us.json").exists() and "全市場排行" in page and "全市場買點訊號" in page and 'id="stockQfm"' in page
    for k in ("signals", "themes"):
        assert f'id="p-{k}"' in page, k
    assert "何時買（規則參考）" in page and "何時才算買點" in page and "進場參考區" in page and 'id="sigQ"' in page and 'id="stockQ"' in page
    hit = next(r for m in eng.signals["markets"].values() for r in m["rows"])
    pl = hit["patterns"][0]["plan"]
    assert pl["zone_lo"] < pl["zone_hi"] and pl["where"] and (pl["target"] is None or pl["target"] > hit["price"])
    assert all(r["status"].get("when") for m in eng.signals["markets"].values() for r in m["all"]
               if not r["signal"] and r["status"]["status"] != "nodata")
    assert "技術面買點訊號（由強到弱）" in page and "不是買進建議" in page and "族群強弱（跨美股／台股／港股）" in page
    assert 'class="btn thf"' in page and 'data-th="半導體"' in page and 'class="small muted onlysig"' in page and 'class="nosig"' in page
    assert "時光機" in page and 'id="tmSel"' in page and 'rel="manifest"' in page and "serviceWorker" in page
    assert "不是買賣建議" in page or "not investment advice" in page
    for f in ("manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png", "apple-touch-icon.png"):
        assert (out / f).exists(), f
    files = list(snap.glob("20??-??-??.json"))
    assert len(files) == 1, files
    s = json.loads(files[0].read_text())
    assert s["ssi"]["score"] > 0 and s["scores"]["us"]["top"] and s["asof"] and "signals" in s
    pub = json.loads((out / "snap" / files[0].name).read_text())
    assert all("since_pct" in r for m in pub["signals"].values() for r in m["rows"]), "published snapshot carries since-returns"
    ix = json.loads((out / "snap" / "index.json").read_text())
    assert len(ix) == 1 and ix[0]["date"] == s["date"] and (out / "snap" / files[0].name).exists()
    asyncio.run(B.build(out, use_ai=False, engine=eng, snapdir=snap))
    assert len(list(snap.glob("20??-??-??.json"))) == 1, "one snapshot per day"
    for word in ("持倉總值", "未實現", "data-private"):
        assert word not in page, word
    import re
    assert not re.search(r"https?://(?!example\.com|e\.com|www\.sec\.gov)[^\"' ]+\.(js|css)", page)
    assert "pickbox" in page and "今日規則精選" in page and "sec_picks" not in page
    npk = sum(len(m["picks"]) for m in eng.signals["markets"].values())
    assert page.count('class="pickrow"') == npk, (page.count('class="pickrow"'), npk)
    print(f"  picks: {npk}")
    d = json.loads((out / "data.json").read_text())
    assert d["scores"]["us"], "data.json carries the top of the board"
    # on-demand lookup of a ticker outside the universe (Discord /stock), plus NU now in the universe
    from wsb.analytics import lookup as LK
    from wsb.data import stocks as STK
    assert LK.normalise("nu") == ("NU", "us") and LK.normalise("2330") == ("2330.TW", "tw") and LK.normalise("0050") == ("0050.TW", "tw")
    assert LK.normalise("700") == ("0700.HK", "hk") and LK.normalise("0700.hk") == ("0700.HK", "hk") and LK.normalise("brk.b") == ("BRK-B", "us")
    assert any(r["sym"] == "NU" for r in sc["markets"]["us"]["rows"])
    idx2 = eng.stockprices.close.index
    STK._download = lambda syms, period: (pd.DataFrame({syms[0]: 50 * np.exp(np.linspace(0, 0.4, len(idx2)))}, index=idx2),
                                          pd.DataFrame({syms[0]: np.full(len(idx2), 1e6)}, index=idx2))
    before = SS._HIST.read_text() if SS._HIST.exists() else ""
    lk = asyncio.run(LK.lookup(eng, "zzzz"))
    assert lk["ok"] and not lk["in_universe"] and lk["row"]["sym"] == "ZZZZ" and lk["n"] == len(sc["markets"]["us"]["rows"]) + 1
    assert lk["signal"] or lk["status"], lk
    assert (SS._HIST.read_text() if SS._HIST.exists() else "") == before, "lookup must not touch saved history"
    assert asyncio.run(LK.lookup(eng, "NU"))["in_universe"]
    from wsb import weekly as WK
    from wsb.bot import command as CMD
    bf = WK.board_facts(eng)
    assert len(bf["board"]) == 3 and bf["board"][0]["top"] and any("13F 新申報" in x for x in bf["board_lines"])
    png = CMD._w_board(bf, "1/1").png()
    Path("/tmp/wsb_expansion/weekly_board.png").write_bytes(png)
    assert len(png) > 5000
    print(f"  site {len(page) / 1024:.0f} KB · US #1 {us[0]['name']} {us[0]['score']:.0f} · breadth US {rot['breadth']['us']['now']:.0f}%")
    print("EXPANSION TESTS PASSED ✅")


if __name__ == "__main__":
    main()
