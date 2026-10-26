"""金融穩定監測: Treasury refunding parsing and change detection, SOFR/IORB, CFTC basis, AI capex, alerts, cards.
Run: python -m tests.test_stability"""
from __future__ import annotations

import os
import re
import sys
import tempfile

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_st_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from wsb.data import stability as ST  # noqa: E402

IDX = ('<meta property="og:description" content="DOCUMENTS RELEASED (The next release is scheduled for November 2, 2026) '
       '(The next release is scheduled for November 4, 2026)">'
       '<a href=/news/press-releases/sb0584>Financing Estimates: 2026 - 3rd Quarter</a>'
       '<a href=/news/press-releases/sb0590>Policy Statement: 2026 - 3rd Quarter</a>'
       '<a href=/system/files/x.pdf>Policy Statement PDF</a>')
EST = ("During the July–September 2026 quarter, Treasury expects to borrow $739 billion in privately-held net marketable debt. "
       "The borrowing estimate is $68 billion higher than announced in May 2026, primarily due to lower cash flows. "
       "During the October–December 2026 quarter, Treasury expects to borrow $628 billion in privately-held net marketable debt.")
KEEP = ("The U.S. Department of the Treasury is offering $125 billion of Treasury securities to refund approximately $96.3 billion of "
        "privately-held notes. Treasury believes its current auction sizes leave it well positioned. Based on current projected "
        "borrowing needs, Treasury anticipates maintaining nominal coupon and FRN auction sizes for at least the next several quarters.")
UP = ("Based on current projected borrowing needs, Treasury anticipates increasing nominal coupon and FRN auction sizes "
      "beginning in the February quarter.")


def test_refunding_parse():
    idx = ST.parse_qr_index(IDX)
    assert idx["links"]["estimates"][0].endswith("sb0584") and idx["links"]["policy"][0].endswith("sb0590")
    assert idx["next"] == ["2026-11-02", "2026-11-04"]
    e = ST.parse_estimates(EST)
    assert [q["bn"] for q in e["quarters"]] == [739.0, 628.0] and e["revision"] == {"bn": 68.0, "vs": "May 2026"}
    p = ST.parse_policy(KEEP)
    assert p["status"] == "keep" and p["offer_bn"] == 125.0 and abs(p["new_cash_bn"] - 28.7) < 1e-9
    assert ST.parse_policy(UP)["status"] == "increase"


def test_refunding_change_detected():
    idx = {"next": ["2026-11-04"]}
    r = ST.merge_refunding({}, idx, None, ST.parse_policy(KEEP), None, ("u1", "Q3", "2026-08-05"))
    assert r["policy"]["changed"] is False and len(r["history"]) == 1
    r = ST.merge_refunding(r, idx, None, ST.parse_policy(KEEP), None, ("u1", "Q3", "2026-08-05"))
    assert len(r["history"]) == 1                                    # same release seen twice → one entry
    r = ST.merge_refunding(r, idx, None, ST.parse_policy(UP), None, ("u2", "Q4", "2026-11-04"))
    assert r["policy"]["changed"] is True and r["policy"]["status"] == "increase"
    v = ST.refunding_view({"refunding": r})
    assert v["state"] == "加量" and v["emoji"] == "🔴"
    al = ST.alerts({"refunding": v}, "2026-11-03")
    keys = [a[0] for a in al]
    assert "stab:refund:u2" in keys and "stab:qrdate:2026-11-04" in keys


class _Fred:
    def __init__(self, iorb):
        self.iorb = iorb

    def get(self, sid):
        return pd.Series([self.iorb] * 60, index=pd.bdate_range(end="2026-10-23", periods=60)) if sid == "IORB" else pd.Series(dtype=float)


class _Eng:
    def __init__(self, iorb):
        self.fred = _Fred(iorb)


def _sofr(rate):
    days = pd.bdate_range(end="2026-10-23", periods=40)
    return [[d.strftime("%Y-%m-%d"), 3.85, 3.90, 2900.0] for d in days[:-1]] + [[days[-1].strftime("%Y-%m-%d"), rate, rate + 0.05, 3000.0]]


def test_funding_states():
    d = {"sofr": _sofr(3.86), "repo": [["2026-10-23", 0.0]]}
    assert ST.funding_view(d, _Eng(3.90))["state"] == "寬鬆"
    d = {"sofr": _sofr(3.92), "repo": [["2026-10-23", 0.0]]}
    v = ST.funding_view(d, _Eng(3.90))
    assert v["state"] == "偏緊" and round(v["spread"]) == 2
    d = {"sofr": _sofr(3.97), "repo": [["2026-10-23", 30.0]]}
    v = ST.funding_view(d, _Eng(3.90))
    assert v["state"] == "緊繃" and any(a[0].startswith("stab:funding:緊繃") for a in ST.alerts({"funding": v}, "2026-10-23"))


def test_cftc_and_basis():
    rows = [{"report_date_as_yyyy_mm_dd": "2026-10-20T00:00:00.000", "cftc_contract_market_code": "042601",
             "lev_money_positions_long": "100", "lev_money_positions_short": "1100"},
            {"report_date_as_yyyy_mm_dd": "2026-10-20T00:00:00.000", "cftc_contract_market_code": "043602",
             "lev_money_positions_long": "0", "lev_money_positions_short": "1000"},
            {"report_date_as_yyyy_mm_dd": "2026-10-20T00:00:00.000", "cftc_contract_market_code": "999999",
             "lev_money_positions_long": "0", "lev_money_positions_short": "1"}]
    p = ST.parse_cftc(rows)
    assert p == [["2026-10-20", 0.3, {"2 年": 0.2, "10 年": 0.1}]]                 # 2Y contract = $200k
    hist = [[f"2020-{i:03d}", float(i), {}] for i in range(100)] + [["2026-10-20", 500.0, {"2 年": 500.0}]]
    v = ST.basis_view({"cftc": hist})
    assert v["record"] and v["state"] == "極大" and v["pct"] == 100.0
    assert any(a[0] == "stab:basis:2026-10-20" for a in ST.alerts({"basis": v}, "2026-10-23"))


def _f(capex, ocf, debt, debt_prev, end="2026-06-30"):
    return {"p": {"capex": {"v": capex, "prev": capex / 2}, "ocf": {"v": ocf}, "debt": {"v": debt, "prev": debt_prev},
                  "cash": {"v": 1.0}, "end": end}, "m": {"capex_ocf_prev": 0.5}}


def test_ai_view():
    fund = {"MSFT": _f(100e9, 200e9, 50e9, 40e9), "AMZN": _f(170e9, 160e9, 140e9, 60e9), "CRWV": _f(20e9, 7e9, 25e9, 9e9)}
    v = ST.ai_view(fund)
    assert abs(v["ratio"] - 290 / 367) < 1e-9 and v["state"] == "吃緊" and v["over1"] == ["亞馬遜", "CoreWeave"]
    assert abs(v["debt_add"] - 106e9) < 1 and abs(v["capex_growth"] - 100) < 1e-9
    v = ST.ai_view({"A": _f(1, 1, 1, 1)})
    assert v is None


def test_cards_and_layout():
    from tools import site_layout as SLY
    from tools import site_stability as SST
    import tools.site_stamp as STP
    st = ST.load()
    st.update({"sofr": _sofr(3.86), "repo": [["2026-10-23", 0.0]],
               "cftc": [[d.strftime("%Y-%m-%d"), float(i), {"2 年": float(i)}] for i, d in enumerate(pd.date_range(end="2026-10-20", periods=80, freq="7D"))],
               "refunding": ST.merge_refunding({}, {"next": ["2026-11-02", "2026-11-04"]}, ST.parse_estimates(EST), ST.parse_policy(KEEP),
                                               ("e", "Financing Estimates", "2026-08-03"), ("u1", "Policy Statement", "2026-08-05"))})
    ST._save(st)
    e = _Eng(3.90)
    h = SST.sec_st_brief(e)
    assert 'id="st-top"' in h and h.count('class="aitile"') >= 4 and re.search(r"金融穩定 [1-4] 項：", h)
    for k in ("st-refund", "st-funding", "st-basis", "st-cover"):
        assert f'data-jump="{k}"' in h
    r = SST.sec_st_refunding(e)
    assert 'id="st-refund"' in r and "anticipates maintaining" in r and "回到重點" in r
    assert SST.sec_st_funding(e) and SST.sec_st_basis(e) and SST.sec_st_coverage(e)
    assert "stability" in SLY.GROUPS[1][5] and SLY.GROUPS[1][5][0] == "ai"
    assert "sec_st_brief" in STP.CARD and "stability" in STP.TAB_DEFAULT
    stamped = STP.inject(h, STP.stamp(e, "sec_st_brief", "stability"))
    assert "🕒" in stamped
    assert "金融穩定：" in " ".join(SLY.picks({"stability": "<p>金融穩定 4 項：1 項紅燈、2 項黃燈 基差交易</p>"})["risk"])
    assert "金融穩定：1 項紅燈、2 項黃燈" in SLY.picks({"stability": "<p>金融穩定 4 項：1 項紅燈、2 項黃燈 基差交易</p>"})["risk"]
    for bad in ("使用者持倉", "持倉總值", "未實現", "data-private"):
        assert bad not in h + r


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
