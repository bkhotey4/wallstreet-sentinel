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


def make_engine(tmp: Path):
    eng = Engine()
    eng.market, eng.fred = T.m, T.fr
    eng.stress_engine = StressEngine(T.m, T.fr)
    eng.calendar.events = []
    eng.stockprices = FakePrices(T.END)
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
    # site: new tabs, sections, PWA, time machine (snapshot written once, index published)
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
    assert "時光機" in page and 'id="tmSel"' in page and 'rel="manifest"' in page and "serviceWorker" in page
    assert "不是買賣建議" in page or "not investment advice" in page
    for f in ("manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png", "apple-touch-icon.png"):
        assert (out / f).exists(), f
    files = list(snap.glob("20??-??-??.json"))
    assert len(files) == 1, files
    s = json.loads(files[0].read_text())
    assert s["ssi"]["score"] > 0 and s["scores"]["us"]["top"] and s["asof"]
    ix = json.loads((out / "snap" / "index.json").read_text())
    assert len(ix) == 1 and ix[0]["date"] == s["date"] and (out / "snap" / files[0].name).exists()
    asyncio.run(B.build(out, use_ai=False, engine=eng, snapdir=snap))
    assert len(list(snap.glob("20??-??-??.json"))) == 1, "one snapshot per day"
    for word in ("持倉總值", "未實現", "data-private"):
        assert word not in page, word
    import re
    assert not re.search(r"https?://(?!example\.com|e\.com|www\.sec\.gov)[^\"' ]+\.(js|css)", page)
    d = json.loads((out / "data.json").read_text())
    assert d["scores"]["us"], "data.json carries the top of the board"
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
