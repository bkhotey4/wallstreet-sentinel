"""企業危機雷達: XBRL TTM / balance parsing, SEC red-flag filings, every metric, the points rule, site card, alerts.
Run: python -m tests.test_distress"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_distress_"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import distress as DZ  # noqa: E402
from wsb.data import distress_data as DD  # noqa: E402

TODAY = date(2026, 10, 16)


def _dur(s, e, v, filed="2026-08-01"):
    return {"start": s, "end": e, "val": v, "filed": filed}


def _ins(e, v, filed="2026-08-01"):
    return {"end": e, "val": v, "filed": filed}


def test_ttm():
    # cash-flow style: FY2025 + 6-month YTD 2026 − 6-month YTD 2025
    f = [_dur("2025-01-01", "2025-12-31", 100.0, "2026-02-20"), _dur("2026-01-01", "2026-06-30", 70.0),
         _dur("2025-01-01", "2025-06-30", 40.0, "2025-08-01"), _dur("2026-04-01", "2026-06-30", 38.0)]
    assert DD.ttm(f) == ("2026-06-30", 130.0)
    assert DD.ttm([_dur("2025-01-01", "2025-12-31", 90.0)]) == ("2025-12-31", 90.0)
    assert DD.ttm([_dur("2026-01-01", "2026-06-30", 70.0)]) is None             # no prior year → no made-up TTM
    # a restated value (later filing) wins
    assert DD.instants([_ins("2026-06-30", 5.0, "2026-08-01"), _ins("2026-06-30", 6.0, "2026-09-01")]) == {"2026-06-30": 6.0}


def _cf(us: dict, dei: dict | None = None) -> dict:
    return {"facts": {"us-gaap": {t: {"units": {"USD": fs}} for t, fs in us.items()},
                      "dei": {t: {"units": {"shares": fs}} for t, fs in (dei or {}).items()}}}


def test_parse_balance_and_flags():
    E = "2026-06-30"
    cf = _cf({"Assets": [_ins(E, 77e9), _ins("2025-06-30", 40e9)], "Liabilities": [_ins(E, 72e9)],
              "AssetsCurrent": [_ins(E, 9.5e9)], "LiabilitiesCurrent": [_ins(E, 20.9e9)],
              "RetainedEarningsAccumulatedDeficit": [_ins(E, -4e9)], "StockholdersEquity": [_ins(E, 5e9)],
              "CashAndCashEquivalentsAtCarryingValue": [_ins(E, 5.5e9)],
              "LongTermDebt": [_ins(E, 24.9e9), _ins("2025-06-30", 11e9)], "LongTermDebtNoncurrent": [_ins(E, 17.3e9)],
              "OperatingIncomeLoss": [_dur("2025-07-01", "2026-06-30", -0.2e9)],
              "InterestExpense": [_dur("2025-07-01", "2026-06-30", 1.6e9)],
              "NetCashProvidedByUsedInOperatingActivities": [_dur("2025-07-01", "2026-06-30", 6.9e9)],
              "PaymentsToAcquirePropertyPlantAndEquipment": [_dur("2025-07-01", "2026-06-30", 20.6e9)],
              "DepreciationDepletionAndAmortization": [_dur("2025-07-01", "2026-06-30", 4.0e9)]},
             {"EntityCommonStockSharesOutstanding": [_ins("2026-07-31", 5.4e8)]})
    b = DD.parse_balance(cf)
    assert b["end"] == E and b["ltd"] == 24.9e9 and b["ltd_yago"] == 11e9 and b["shares"] == 5.4e8
    assert b["capex_ttm"] == 20.6e9 and b["interest_ttm"] == 1.6e9
    assert DD.parse_balance(_cf({})) is None
    js = {"cik": "1769628", "filings": {"recent": {
        "form": ["8-K", "8-K", "NT 10-Q", "8-K", "10-Q"],
        "filingDate": ["2026-10-01", "2026-09-01", "2026-08-15", "2025-01-01", "2026-08-10"],
        "accessionNumber": ["0001-26-000001", "0001-26-000002", "0001-26-000003", "0001-25-000004", "0001-26-000005"],
        "items": ["2.02,9.01", "2.04,1.03", "", "1.03", ""]}}}
    fl = DD.parse_flags(js, TODAY)
    codes = [(f["code"], f["level"]) for f in fl]
    assert codes == [("2.04", "alert"), ("1.03", "alert"), ("NT 10-Q", "watch")], codes      # 2.02 earnings is not a flag; >1y dropped
    assert fl[0]["url"].endswith("/000126000002/")
    return b


def _px(n=300, end=50.0, start=100.0, vol=0.04, seed=1):
    rng = np.random.default_rng(seed)
    path = np.exp(np.linspace(np.log(start), np.log(end), n) + rng.normal(0, vol, n).cumsum() * 0.1)
    return pd.Series(path, index=pd.bdate_range(end="2026-10-15", periods=n))


def test_metrics(b):
    z = DZ.altman(b)
    assert z is not None and z < 1.1                                            # the CoreWeave-like sheet is in the distress zone
    sigs = {s["id"]: s for s in DZ._corp(b, _px())}
    assert sigs["altman"]["state"] == "alert" and sigs["coverage"]["state"] == "alert"
    assert sigs["runway"]["state"] == "alert" and "個月" in sigs["runway"]["txt"]   # FCF −13.7B/yr vs 5.5B cash
    assert sigs["leverage"]["state"] == "alert" and sigs["debt_growth"]["state"] == "watch"
    assert "merton" in sigs and 0 <= sigs["merton"]["pd"] <= 1
    # net-cash company with a GAAP loss: coverage / leverage don't apply
    nc = {**b, "cash": 30e9, "ltd": 1e9, "ltd_nc": 1e9}
    ids = {s["id"] for s in DZ._corp(nc, _px())}
    assert "net_cash" in ids and "coverage" not in ids and "leverage" not in ids
    # bank: SVB at end-2022 (AOCI −1.9B, HTM 91.3B cost vs 76.2B fair value, equity 16.3B)
    svb = {"aoci": -1.9e9, "htm_cost": 91.3e9, "htm_fv": 76.2e9, "equity": 16.3e9, "assets": 211.8e9,
           "deposits": 173.1e9, "deposits_q": 176.8e9}
    bs = {s["id"]: s for s in DZ._bank(svb)}
    assert bs["aoci"]["state"] == "alert" and "持有到期" in bs["aoci"]["txt"]
    assert bs["eq_assets"]["state"] == "ok" and bs["deposits"]["state"] == "ok"
    assert {s["id"]: s for s in DZ._bank({**svb, "htm_loss": 1e9, "htm_gain": 0.0})}["aoci"]["state"] == "ok"   # reported loss tag wins
    assert DZ._bank({**svb, "deposits": 150e9})[-1]["state"] == "alert"         # −15% in a quarter
    assert DZ._credit({"liab": 2.0e9, "equity": 1.0e9})[0]["state"] == "alert"
    # points rule: one bad ratio alone never lights a company
    one = [DZ._sig("altman", "Z", "alert", "")]
    assert DZ.overall(one) == "ok"
    assert DZ.overall(one + [DZ._sig("x", "x", "watch", "")]) == "watch"
    assert DZ.overall(one * 2 + [DZ._sig("x", "x", "watch", "")]) == "alert"
    assert DZ.overall([{**DZ._sig("sec", "SEC", "alert", ""), "hard": True}]) == "alert"


def test_assess_and_build(b):
    rec = {"bs": b, "flags": [{"code": "4.01", "date": "2026-09-30", "level": "watch", "zh": "更換會計師（8-K 4.01）", "url": None}]}
    r = DZ.assess("CRWV", {"zh": "CoreWeave", "kind": "tech"}, rec, _px(), pd.Series(dtype=float), TODAY)
    assert r["state"] == "alert" and r["points"] >= 5 and any(s["id"] == "sec_4_01" for s in r["signals"])
    # an old balance sheet (> 400 days) is not scored, only prices and filings
    old = DZ.assess("OLD", {"zh": "x", "kind": "tech"}, {"bs": {**b, "end": "2025-01-31"}}, _px(), pd.Series(dtype=float), TODAY)
    assert not old["has_bs"] and all(s["id"] in ("drawdown",) for s in old["signals"])
    # bank kind needs deposits > 40 % of assets; vs-KRE signal
    bank = DZ.assess("ZZ", {"zh": "z", "kind": "fin"}, {"bs": {"end": "2026-06-30", "assets": 100.0, "deposits": 80.0, "equity": 9.0}},
                     _px(end=40), _px(end=100, start=100, seed=2), TODAY)
    assert bank["kind"] == "bank" and any(s["id"] == "vs_kre" for s in bank["signals"])
    # end to end through build(): cache file + stock prices
    DD._save({"CRWV": rec})
    close = pd.DataFrame({"CRWV": _px()})
    eng = types.SimpleNamespace(stockprices=types.SimpleNamespace(series=lambda s: close[s].dropna() if s in close else pd.Series(dtype=float)),
                                market=types.SimpleNamespace(history=pd.DataFrame()))
    out = DZ.build(eng)
    assert out["available"] and out["rows"][0]["sym"] == "CRWV" and out["counts"]["alert"] >= 1
    assert "CRWV" in DZ.extra_symbols() and "CRWV" in DZ.watchlist()
    from wsb.data.stocks import all_symbols
    assert "CRWV" in all_symbols()                                              # watch-list prices are downloaded
    return out


def test_discovery():
    # SEC full-text search hits
    js = {"hits": {"total": {"value": 2}, "hits": [
        {"_id": "0001-26-1:a.htm", "_source": {"ciks": ["0000000101"], "display_names": ["Big Co Inc.  (BIGC)  (CIK 0000000101)"],
                                               "form": "8-K", "file_date": "2026-10-14", "items": ["1.03", "9.01"]}},
        {"_id": "0001-26-2:b.htm", "_source": {"ciks": ["0000000102"], "display_names": ["Tiny Corp  (CIK 0000000102)"],
                                               "form": "NT 10-Q", "file_date": "2026-10-10", "items": []}}]}}
    hits = DD.parse_efts(js)
    assert hits[0]["ticker"] == "BIGC" and hits[0]["cik"] == 101 and hits[1]["ticker"] is None
    assert DD.screen_period(date(2026, 10, 17)) == "CY2026Q2" and DD.screen_period(date(2026, 2, 1)) == "CY2025Q3"
    assert DD.ttm_frames("CY2026Q2") == (["CY2025", "CY2026Q1", "CY2026Q2"], ["CY2025Q1", "CY2025Q2"])
    assert DD.ttm_frames("CY2025Q4") == (["CY2025"], [])
    # balance-sheet screen
    names = {1: ("LEVD", "Levered Co"), 2: ("CASH", "Cash Rich"), 3: ("BNKX", "Bank X"), 4: ("SMOL", "Small"), 5: ("FINE", "Fine Co")}
    fr = {"assets": {1: 10e9, 2: 10e9, 3: 50e9, 4: 1e9, 5: 10e9}, "liab": {1: 8e9, 2: 3e9, 3: 46e9, 5: 5e9},
          "equity": {1: 2e9, 2: 7e9, 3: 4e9, 5: 5e9}, "deposits": {3: 40e9}, "aoci": {3: -1.5e9}, "htm_loss": {3: 0.5e9},
          "cash": {1: 0.5e9, 2: 5e9, 5: 1e9}, "ltd": {1: 6e9, 2: 1e9, 5: 2e9},
          "ebit": {1: 0.3e9, 2: -1e9, 4: -1e9, 5: 2e9}, "interest": {1: 0.5e9, 2: 0.05e9, 4: 0.1e9, 5: 0.1e9}}
    c = {x["sym"]: x for x in DD.screen_candidates(fr, names)}
    assert set(c) == {"LEVD", "BNKX"}, c                       # net-cash loss-maker, small and healthy ones are not flagged
    assert c["BNKX"]["kind"] == "bank" and "-50%" in c["BNKX"]["why"]
    # auto list: add, skip fixed names and small filers, expire after auto_keep_days
    DD._jsave(DD.F_AUTO, {"OLDX": {"zh": "Old", "kind": "auto", "why": "x", "src": "screen", "added": "2026-08-01", "last_hit": "2026-09-01"}})
    tmap = {"BIGC": {"cik": 101, "title": "Big Co"}, "TINY": {"cik": 102, "title": "Tiny"}, "LEVD": {"cik": 1, "title": "Levered"},
            "BNKX": {"cik": 3, "title": "Bank X"}, "JPM": {"cik": 19617, "title": "JPMorgan"}}
    scn = {"hits": [{**hits[0], "code": "1.03"}, {**hits[1], "code": "NT 10-Q"}]}
    scr = {"cands": list(c.values()) + [{"sym": "JPM", "cik": 19617, "zh": "JPM", "kind": "bank", "why": "x", "assets": 1}],
           "assets": {"101": 5e9, "102": 1e8, "1": 10e9, "3": 50e9}}
    auto = DD.update_auto(scn, scr, tmap, {"JPM"}, date(2026, 10, 17))
    assert set(auto) == {"BIGC", "LEVD", "BNKX"}, auto
    assert auto["BIGC"]["src"] == "filing" and "破產" in auto["BIGC"]["why"]
    wl = DZ.watchlist()
    assert wl["BIGC"]["src"] == "auto" and wl["JPM"]["src"] == "universe" and "BIGC" in DZ.extra_symbols()
    # pruning: no prices for 30 days → removed with the reason; prices back → restored
    idx_old = pd.bdate_range(end="2026-08-20", periods=200)
    close = {"BIGC": pd.Series(1.0, index=idx_old), "LEVD": _px()}
    sp = types.SimpleNamespace(series=lambda s_: close.get(s_, pd.Series(dtype=float)))
    cache = {"BIGC": {"flags": [{"code": "1.03", "date": "2026-10-14", "level": "alert", "zh": "破產"}]}}
    st = DZ.prune(sp, cache, date(2026, 10, 17))
    assert "BIGC" in st["removed"] and "破產" in st["removed"]["BIGC"]["why"] and "LEVD" not in st["removed"]
    assert "BIGC" not in DZ.watchlist() and "BIGC" in DZ.watchlist(include_removed=True)
    close["BIGC"] = _px()
    assert "BIGC" not in DZ.prune(sp, cache, date(2026, 10, 17))["removed"]
    DD._jsave(DD.F_AUTO, {})
    DZ._save_state({})


def test_site_and_alerts(out):
    from tools import site_sections as S2
    html = S2.sec_distress(types.SimpleNamespace(distress=out))
    assert "企業危機雷達" in html and "CRWV" in html and "Altman" in html and "紅燈" in html
    assert "SEC" in html and "股價" in html and "名單自動維護" in html
    stale = {**out, "n_sec_stale": out["total"], "removed": {"ZZZ": {"date": "2026-10-01", "zh": "Gone", "why": "超過 30 天沒有股價", "last_px": "2026-08-20"}}}
    h2 = S2.sec_distress(types.SimpleNamespace(distress=stale))
    assert "資料更新異常" in h2 and "已移出雷達" in h2 and "ZZZ" in h2
    assert S2.sec_distress(types.SimpleNamespace(distress={})) == ""
    from wsb import store
    from wsb.bot.app import Sentinel
    row = {"sym": "CRWV", "zh": "CoreWeave", "state": "alert", "bs_end": "2026-06-30",
           "signals": [DZ._sig("altman", "Altman Z''", "alert", "-1.09")]}
    bot = types.SimpleNamespace(engine=types.SimpleNamespace(distress={"available": True, "asof": "2026-10-16", "rows": [row]}))
    assert Sentinel._distress_alerts(bot) == []                                # first run = silent baseline
    # a company discovered later that is already red → one digest (not one alert per company)
    nr = {"sym": "NEWX", "zh": "New X", "state": "alert", "bs_end": "2026-06-30", "why": "近四季營業利益不夠付利息",
          "signals": [DZ._sig("altman", "Z", "alert", "0.1")]}
    bot.engine.distress["rows"] = [row, nr]
    a = Sentinel._distress_alerts(bot)
    assert len(a) == 1 and "新加入 1 家" in a[0].title and "NEWX" in a[0].detail
    bot.engine.distress["rows"] = [row]
    row["state"] = "ok"
    assert Sentinel._distress_alerts(bot) == []                                # back to no light → re-armed
    row["state"] = "alert"
    a = Sentinel._distress_alerts(bot)
    assert len(a) == 1 and "CoreWeave" in a[0].title
    store.alert_mark(a[0].key, a[0].severity, a[0].title)
    assert Sentinel._distress_alerts(bot) == []                                # delivered → once
    from datetime import datetime as _dt, timedelta as _td
    d = (_dt.utcnow() - _td(days=1)).strftime("%Y-%m-%d")
    row["signals"].append({**DZ._sig("sec_1_03", "SEC 申報", "alert", f"{d} 破產或接管（8-K 1.03）"), "hard": True, "url": "u"})
    row["signals"].append({**DZ._sig("sec_4_02", "SEC 申報", "alert", "2026-06-01 先前財報不可再依賴（8-K 4.02）"), "hard": True})
    a = Sentinel._distress_alerts(bot)
    assert len(a) == 1 and a[0].severity.startswith("🚨") and "1.03" in a[0].detail   # fresh hard filing alerts even while red;
                                                                                      # a months-old one does not


def main():
    test_ttm()
    b = test_parse_balance_and_flags()
    test_metrics(b)
    out = test_assess_and_build(b)
    test_discovery()
    test_site_and_alerts(out)
    print("distress OK")


if __name__ == "__main__":
    main()
