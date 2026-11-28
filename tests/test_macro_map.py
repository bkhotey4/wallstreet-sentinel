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


def test_fed_path_and_hike_into_slowdown():
    """11-28: futures priced a ~90% December hike while cross-asset prices leaned toward a slowdown."""
    fw = {"available": True, "r0": 3.88, "meetings": [
        {"date": "2026-12-09", "probs": {"0": 0.1, "25": 0.9}, "chg_bp": 22.5, "rate_after": 4.105, "week_ago": {"chg_bp": 15.0}},
        {"date": "2027-03-17", "probs": {"25": 0.6, "50": 0.4}, "chg_bp": 35.0, "rate_after": 4.23}]}
    p = M.fed_path(fw)
    assert round(p["p_hike"], 2) == 0.9 and round(p["cum_bp"]) == 35 and p["wk_shift"] == 7.5 and "升息 90%" in p["text"]
    assert M.fed_path({"available": False}) == {}
    ps = P(pricing=1, growth=-1) + [{"key": "rates", "zh": "利率", "state": 1, "facts": [], "hike_next": 0.9}]
    assert any(c.startswith("期貨市場押聯準會下次升息") for c in M.conflicts(ps))


if __name__ == "__main__":
    test_fed_path_and_hike_into_slowdown()
    print("ok fed path")


def test_auction_tally_and_global_conflicts():
    """11-28 desk pass: auction demand over 5 weeks, the yen-carry squeeze (JGB up while US 10y falls)."""
    a = [{"date": "2026-11-25", "term": "7-Year", "verdict": "偏弱"}, {"date": "2026-11-12", "term": "30-Year", "verdict": "偏弱"},
         {"date": "2026-11-10", "term": "10-Year", "verdict": "正常"}, {"date": "2026-10-01", "term": "5-Year", "verdict": "偏強"},
         {"date": "2026-11-20", "term": "2-Year", "verdict": None}]
    t = M.auction_tally(a, "2026-11-28")
    assert t == {"n": 3, "weak": 2, "strong": 0, "weak_terms": ["7-Year", "30-Year"]}
    ps = [{"key": "treasury", "zh": "美債", "state": 1, "auct_weak": 2, "facts": [
              "10 年期 1 個月 -15 個基點＝實質利率 +2＋通膨預期 -17", "外國央行託管美債 13 週 -2.7%"]},
          {"key": "global", "zh": "海外", "state": 1, "j10": 0.12, "facts": []}]
    c = M.conflicts(ps)
    assert any(x.startswith("最近的美債標售需求偏弱") for x in c) and any(x.startswith("日本長期利率在升") for x in c)
    ps[1]["j10"] = -0.12
    assert not any(x.startswith("日本長期利率在升") for x in M.conflicts(ps))


if __name__ == "__main__":
    test_auction_tally_and_global_conflicts()
    print("ok desk pass")


def test_energy_conflicts():
    """11-29: Hormuz at 3% of normal while Brent fell 14% in a month; energy stress during a slowdown = supply stagflation."""
    ps = [{"key": "energy", "zh": "能源", "state": 1, "hz_ratio": 0.03, "oil": -13.9, "facts": []}, {"key": "growth", "zh": "成長", "state": 1, "facts": []}]
    c = M.conflicts(ps)
    assert any(x.startswith("荷姆茲海峽幾乎沒有船通過") for x in c) and any(x.startswith("能源或供應鏈壓力在升，同時經濟在轉弱") for x in c)
    ps[0].update(hz_ratio=0.9)
    assert not any(x.startswith("荷姆茲海峽幾乎沒有船通過") for x in M.conflicts(ps))


if __name__ == "__main__":
    test_energy_conflicts()
    print("ok energy")


def test_tests_ahead():
    ps = [{"key": "growth", "zh": "經濟成長與就業", "state": -1}, {"key": "rates", "zh": "利率與聯準會", "state": 0}]
    it = [{"kind": "macro", "key": "nfp", "zh": "非農就業", "tpe": "2026-12-04 21:30"}, {"kind": "earnings", "sym": "CRM"},
          {"kind": "macro", "key": "fomc", "zh": "FOMC", "tpe": "2026-12-10 03:00"}, {"kind": "macro", "key": "cpi", "zh": "CPI", "tpe": "x"}]
    a = M.tests_ahead(it, ps)
    assert [x["pillar"] for x in a] == ["經濟成長與就業", "利率與聯準會"] and a[0]["state"] == -1


if __name__ == "__main__":
    test_tests_ahead()
    print("ok ahead")
