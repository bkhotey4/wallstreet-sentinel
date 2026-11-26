"""Every listed company's quarter (11-27): one rule for 改善中／轉弱中, industry shares, YoY single quarter from cumulative.
Run: python -m tests.test_tw_qall"""
from tools import site_tw_qall as S
from wsb.data import tw_chips as C


def test_label():
    assert S.label({"rev_yoy": 12.0, "om": 10.0, "om_ly": 8.0}) == "up"
    assert S.label({"rev_yoy": -5.0, "om": 6.0, "om_ly": 8.0}) == "down"
    assert S.label({"rev_yoy": 5.0, "om": 6.0, "om_ly": 8.0}) == "mix"
    assert S.label({"rev_yoy": 5.0, "om": None, "om_ly": None, "gm": 30.0, "gm_ly": 25.0}) == "up"   # no operating margin → gross
    assert S.label({"rev_yoy": None, "om": 6.0, "om_ly": 8.0}) is None
    assert S.label({"rev_yoy": 173226.0, "rev_ly": 700.0, "om": 18.7, "om_ly": -13633.9}) is None     # tiny base: not judged


def test_yoy_single_quarter():
    c = lambda rev, op, k=1e5: {"name": "X", "rev": rev * k, "gross": rev * k * 0.3, "op": op * k, "ni": op * k * 0.8, "eps": op / 100}   # noqa: E731
    snaps = {"115Q3": {"1234": c(300.0, 30.0)}, "115Q2": {"1234": c(180.0, 15.0)}, "115Q1": {"1234": c(80.0, 5.0)},
             "114Q3": {"1234": c(250.0, 20.0)}, "114Q2": {"1234": c(150.0, 12.0)}}
    r = C.fin_view(snaps)["rows"][0]
    assert r["rev"] == 120.0 * 1e5 and round(r["rev_yoy"], 1) == 20.0            # 120 vs (250 − 150) = 100 (億, in thousand NT$)
    assert round(r["om"], 1) == 12.5 and round(r["om_ly"], 1) == 8.0 and S.label({**r}) == "up"


def test_industry_table():
    rows = [{"ind": "半導體", "lab": "up"}] * 6 + [{"ind": "半導體", "lab": "down"}] * 2 + [{"ind": "航運", "lab": "down"}] * 8
    t = S.industry_table(rows)
    assert [x["ind"] for x in t] == ["半導體", "航運"] and t[0]["up_pct"] == 75 and t[1]["down_pct"] == 100


if __name__ == "__main__":
    test_label()
    test_yoy_single_quarter()
    test_industry_table()
    print("ok tw qall")
