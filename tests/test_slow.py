"""Fed research data (EBP CSV, Minneapolis Fed MPD CSV), the 累積脆弱度 lights (expanding-window thresholds, R-zone),
and the three cards.  Run: python -m tests.test_slow"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_sl_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.data import fed_research as FR  # noqa: E402
from wsb.analytics import vulnerability as VU  # noqa: E402

EBP_CSV = "date,gz_spread,ebp,est_prob\n" + "\n".join(
    f"{1990 + i // 12}-{i % 12 + 1:02d}-01,{1.5 + 0.1 * np.sin(i / 7):.4f},{0.3 * np.sin(i / 9):.4f},{0.2 + 0.1 * np.sin(i / 5):.4f}" for i in range(400))
MPD_CSV = ('"The data below are statistics"\n"defs"\n""\n'
           '"market","idt","maturity_target","mu","sd","skew","kurt","p10","p50","p90","lg_change_decr","prDec","lg_change_incr","prInc"\n'
           + "\n".join(f'"sp6m","{(pd.Timestamp("2020-01-03") + pd.Timedelta(weeks=i)):%m/%d/%Y}",6,0.02,0.11,-1.2,3,-0.12,0.035,0.14,-20,{0.03 + 0.001 * (i % 30)},20,0.02'
                       for i in range(60))
           + '\n"bac","01/15/2010",3,-0.02,0.18,-0.38,0.85,-0.25,-0.01,0.19,-20,0.15,20,0.09\n')


def test_parse():
    e = FR.parse_ebp(EBP_CSV)
    assert len(e) == 400 and e[0][0] == "1990-01" and 10 <= e[0][3] <= 30           # probability stored in %
    m = FR.parse_mpd(MPD_CSV)
    assert len(m["sp6m"]) == 60 and m["sp12m"] == [] and m["sp6m"][0][0] == "2020-01-03" and abs(m["sp6m"][0][1] - 3.0) < 1e-9
    FR._save({"ts": 1.0, "ebp": e, "mpd": m})
    print("ok parse")


class Fred:
    def __init__(self, d):
        self.d = d

    def get(self, k):
        return self.d.get(k, pd.Series(dtype=float))


class Mkt:
    def __init__(self, d):
        self.d = d

    def series(self, k):
        return self.d.get(k, pd.Series(dtype=float))


def eng_fixture(boom=True):
    q = pd.date_range("1960-01-01", "2026-04-01", freq="QS")
    credit = pd.Series(np.linspace(80, 120, len(q)), index=q)
    if boom:
        credit.iloc[-12:] = np.linspace(credit.iloc[-13], credit.iloc[-13] + 25, 12)      # fastest 3-year rise on record
    hh = pd.Series(np.linspace(40, 70, len(q)), index=q)
    m = pd.date_range("1975-01-01", "2026-09-01", freq="MS")
    hp = pd.Series(np.linspace(50, 300, len(m)), index=m)
    d = pd.bdate_range("1986-01-02", "2026-10-22")
    spx = pd.Series(np.exp(np.linspace(0, 3, len(d))), index=d)
    spx.iloc[-756:] = spx.iloc[-757] * np.exp(np.linspace(0, 0.9, 756))                   # +146 % in 3 years
    baa = pd.Series(2.0 + np.sin(np.arange(len(d)) / 400), index=d)
    baa.iloc[-30:] = 0.5
    return types.SimpleNamespace(fred=Fred({"QUSPAM770A": credit, "HDTGPDUSQ163N": hh, "CSUSHPISA": hp, "BAA10Y": baa,
                                            "DRTSCILM": pd.Series([10.0, -5.0], index=pd.to_datetime(["2026-04-01", "2026-07-01"]))}),
                                 market=Mkt({"^GSPC": spx}))


def test_vulnerability():
    r = VU.build(eng_fixture(), FR.load()["ebp"])
    by = {x["k"]: x for x in r["lights"]}
    assert by["credit"]["state"] == "hot" and by["assets"]["state"] == "hot" and by["rzone"]["state"] == "hot", by
    assert by["spreads"]["state"] == "hot" and by["sloos"]["state"] == "hot" and "放寬" in by["sloos"]["txt"]
    calm = {x["k"]: x for x in VU.build(eng_fixture(boom=False), None)["lights"]}
    assert calm["credit"]["state"] == "ok" and calm["rzone"]["state"] == "ok" and "ebp" not in calm
    print("ok vulnerability")


def test_cards():
    from tools import site_slow as SSL
    e = eng_fixture()
    a, b, c = SSL.sec_ebp(e), SSL.sec_mpd(e), SSL.sec_vulnerability(e)
    assert "超額債券溢酬" in a and "衰退機率" in a and "不是股市大跌" in a
    assert "選擇權隱含的大跌機率" in b and "風險中性" in b and "6 個月內" in b
    assert "累積脆弱度" in c and "R-zone" in c and "擴張視窗" in c
    from tools import site_layout as SLY
    pk = SLY.picks({"outlook": c + b, "bonds": a})
    assert any("累積脆弱度" in x for x in pk["risk"]) and any("6 個月跌" in x for x in pk["risk"]) and any("EBP" in x for x in pk["macro"]), pk
    print("ok cards")


if __name__ == "__main__":
    test_parse()
    test_vulnerability()
    test_cards()
    print("all slow-layer tests passed")
