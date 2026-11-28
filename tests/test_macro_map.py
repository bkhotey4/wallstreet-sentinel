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
