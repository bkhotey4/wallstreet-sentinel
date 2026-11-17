"""人類溫度計：扣掉物價後的實質時薪（年增、連續幾個月、歷史最糟）。Run: python -m tests.test_real_wage"""
import pandas as pd

from tools import site_human as H


class E:
    def __init__(self, d):
        self.fred = d


def _m(vals, start="2020-01-01"):
    return pd.Series(vals, index=pd.date_range(start, periods=len(vals), freq="MS"))


def test_real_wage_beats_and_loses():
    n = 60
    wage = _m([30 * 1.04 ** (i / 12) for i in range(n)])                  # pay +4% a year
    cpi = _m([300 * (1.08 if 24 <= i < 36 else 1.02) ** (i / 12) for i in range(n)])
    rw = H.real_wage(E({"AHETPI": wage, "CPIAUCSL": cpi}))
    assert rw and rw["yoy"] > 1.5 and rw["run"] >= 1 and rw["worst"] < rw["yoy"], rw
    cpi2 = _m([300 * 1.06 ** (i / 12) for i in range(n)])                  # prices +6% → pay loses ~1.9%
    rw2 = H.real_wage(E({"AHETPI": wage, "CPIAUCSL": cpi2}))
    assert -2.5 < rw2["yoy"] < -1.5 and rw2["last_flip"] is None and rw2["run"] == n - 12, rw2
    h = H.sec_human(E({"AHETPI": wage, "CPIAUCSL": cpi2}))
    assert "扣掉物價，一般員工的時薪比一年前少 1.9%" in h and "連續 48 個月輸給物價" in h, h[:400]
    assert H.real_wage(E({})) is None


if __name__ == "__main__":
    test_real_wage_beats_and_loses()
    print("ok test_real_wage_beats_and_loses")
