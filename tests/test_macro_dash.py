"""每日總經儀表（11-18）：當天／5 天變化、和平常一天比、⚡ 標記、72 小時清單。Run: python -m tests.test_macro_dash"""
import numpy as np
import pandas as pd

from tools import site_macro_dash as MD


def test_rows_and_flag():
    idx = pd.date_range("2025-06-01", periods=300, freq="B")
    rng = np.random.default_rng(1)
    calm = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300))), index=idx)
    jump = calm.copy()
    jump.iloc[-1] = jump.iloc[-2] * 0.94                       # -6 % on a ~1 %-a-day series
    y = pd.Series(4 + np.cumsum(rng.normal(0, 0.03, 300)), index=idx)

    class M:
        def series(self, t):
            return {"^TWII": jump, "^TNX": y}.get(t, calm)

    spread = pd.Series(np.linspace(-0.5, 0.4, 300), index=idx)        # 10y-2y crosses zero: negatives must be kept

    class Fr:
        def get(self, sid):
            return {"T10Y2Y": spread}.get(sid, y)

    class J:
        def get(self, tenor):
            return y / 2

    class E:
        market = M()
        fred = Fr()
        global_yields = J()
    rs = {r["sym"]: r for r in MD.rows(E())}
    assert rs["^TWII"]["k"] > 2 and abs(rs["^TWII"]["d1"] + 6) < 1e-6
    assert rs["^TNX"]["kind"] == "bp" and abs(rs["^TNX"]["d1"] - (y.iloc[-1] - y.iloc[-2]) * 100) < 1e-9
    assert rs["T10Y2Y"]["kind"] == "sp" and abs(rs["T10Y2Y"]["last"] - 0.4) < 1e-9 and rs["T10Y2Y"]["grp"] == "美債"
    assert rs["10Y"]["grp"] == "亞洲" and "^HSI" in rs and "DGS2" in rs
    pub = MD.public(E())
    assert pub["rows"] and {"grp", "d1", "k"} <= set(pub["rows"][0])
    MD.ahead = lambda eng, hours=72: [{"tpe": "2026-11-19 22:30", "kind": "ipo", "zh": "Anthropic, PBC 上市（公司時間表）"}]
    h = MD.block(E())
    assert "台股加權 -6.0%" in h and "⚡" in h and "11/19 22:30" in h and "上市" in h, h[:300]
    assert '<th colspan="6">美債</th>' in h and '<th colspan="6">亞洲</th>' in h and "日本財務省" in h


if __name__ == "__main__":
    test_rows_and_flag()
    print("ok test_rows_and_flag")
