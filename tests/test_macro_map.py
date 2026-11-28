"""總經全貌 (11-28): regimes, the macro-vs-market conflict, core CPI weight.  Run: python -m tests.test_macro_map"""
from wsb.analytics import macro_map as M


def P(**kw):
    return [{"key": k, "zh": k, "state": v, "facts": []} for k, v in kw.items()]


def test_regime():
    assert M.regime(P(growth=1, inflation=1))["name"] == "停滯性通膨的壓力"
    assert M.regime(P(growth=1, inflation=-1))["name"] == "降溫"
    assert M.regime(P(growth=-1, inflation=1))["name"] == "過熱"
    assert M.regime(P(growth=-1, inflation=-1))["name"] == "金髮女孩"
    assert M.regime(P(growth=-1, inflation=0)) is None


def test_macro_vs_market_conflict():
    c = M.conflicts(P(growth=-1, inflation=0, rates=-1, liquidity=-1, ai=1, taiwan=1, china=1, credit=1))
    assert c and c[0].startswith("經濟數據大致還好")
    assert not any(x.startswith("經濟數據大致還好") for x in M.conflicts(P(growth=1, inflation=1, rates=1, liquidity=0, ai=1, taiwan=1, china=1)))


def test_score_core_counts_twice():
    assert M._score(*([1] * 2), -1, -1) == 0 and M._score(1, -1, -1) == -1 and M._score() is None


if __name__ == "__main__":
    test_regime()
    test_macro_vs_market_conflict()
    test_score_core_counts_twice()
    print("ok macro map")


def test_curve_regime_and_real_rate_conflict():
    """11-28 (「你有思考過美債嗎」): 10y −15 bp was breakevens −23 and real +7; foreign official holdings fell as the dollar rose."""
    assert M.curve_regime(-0.07, -0.15) == "牛市變平" and M.curve_regime(0.05, 0.20) == "熊市變陡"
    assert M.curve_regime(-0.20, -0.05) == "牛市變陡" and M.curve_regime(0.01, -0.02) == "大致不動"
    ps = P(dollar=1) + [{"key": "treasury", "zh": "美債", "state": 0, "facts": [
        "10 年期 1 個月 -15 個基點＝實質利率 +7＋通膨預期 -23", "外國央行託管美債 13 週 -2.7%"]}]
    c = M.conflicts(ps)
    assert any(x.startswith("名目殖利率在降") for x in c) and any(x.startswith("美元轉強，同時外國央行在減持美債") for x in c)


if __name__ == "__main__":
    test_curve_regime_and_real_rate_conflict()
    print("ok treasury pillar")
