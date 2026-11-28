"""11-28 稽核修正：P1-1 報價前一筆對齊歷史、P2-9 單季財報缺欄、P3-21 借券集中度前日缺值、P3-17 燈號門檻進設定。
Run: python -m tests.test_audit_1128"""
import pandas as pd


def test_quote_change_uses_history_previous_close():
    """日經 11-26：這一輪下載缺 11-25 那筆，價格列 −1.42%、數字儀表 +1.4%。"""
    from wsb.data.market import MarketData
    m = MarketData.__new__(MarketData)
    idx = pd.to_datetime(["2026-11-24", "2026-11-25", "2026-11-26"])
    m.history = pd.DataFrame({"^N225": [58642.0, 57012.0, 57814.0], "^GSPC": [7201.0, 7183.0, 7183.0]}, index=idx)
    m.quotes = {"^N225": {"price": 57814.0, "prev": 58642.0, "chg_pct": -1.41, "asof": "2026-11-26"},
                "^GSPC": {"price": 7190.0, "prev": 7183.0, "chg_pct": 0.1, "asof": "2026-11-28"}}
    q = m.q("^N225")
    assert q["prev"] == 57012.0 and abs(q["chg_pct"] - 1.41) < 0.01 and q.get("prev_from") == "history", q
    g = m.q("^GSPC")                                      # history older than the quote: left alone
    assert g["prev"] == 7183.0 and g["chg_pct"] == 0.1 and "prev_from" not in g, g


def test_single_quarter_missing_field_stays_unknown():
    from wsb.data import tw_chips as C
    from tools import site_tw_qall as Q
    s = {"2026Q2": {"1111": {"name": "A", "rev": 2e6, "gross": 4e5, "op": None, "ni": 1e5, "eps": 1.0}},
         "2026Q3": {"1111": {"name": "A", "rev": 3e6, "gross": 6e5, "op": 1.5e5, "ni": 1.5e5, "eps": 1.5}},
         "2025Q2": {"1111": {"name": "A", "rev": 1.8e6, "gross": 3.6e5, "op": 1.8e5, "ni": 9e4, "eps": 0.9}},
         "2025Q3": {"1111": {"name": "A", "rev": 2.7e6, "gross": 5.4e5, "op": 2.7e5, "ni": 1.35e5, "eps": 1.35}}}
    sq = C.single_quarter(s, "1111", "2026", 3)
    assert sq["op"] is None and sq["rev"] == 1e6 and sq["name"] == "A", sq
    r = C.fin_view(s)["rows"][0]
    assert r["om"] is None and r["gm"] == 20.0                # was 15% (nine-month 營業利益 over one quarter's revenue)
    assert Q.label(r) == "mix"                                 # falls back to gross margin: 20% vs 20% → not 改善中
    s["2026Q2"]["1111"]["op"] = 1.0e5
    assert C.fin_view(s)["rows"][0]["om"] == 5.0


def test_squeeze_unread_previous_balance():
    from wsb.data import tw_chips as C
    row = lambda c, p, t: [c, "X", 0, 0, 0, 0, 0, 0, p, 0, 0, 0, t]     # noqa: E731
    v = C.squeeze_view({"data": [row("2330", "", "2,000,000"), row("2317", "1,000,000", "1,500,000")]},
                       [{"Code": "2330", "TradeVolume": "1,000,000", "ClosingPrice": "1000"},
                        {"Code": "2317", "TradeVolume": "500,000", "ClosingPrice": "200"}],
                       [{"公司代號": "2330", "已發行普通股數或TDR原股發行股數": "25,000,000"},
                        {"公司代號": "2317", "已發行普通股數或TDR原股發行股數": "13,000,000"}])
    rows = {r["code"]: r for r in (v.get("rows") if isinstance(v, dict) else v)}
    assert rows["2330"]["chg"] is None and rows["2317"]["chg"] == 500000.0, rows


def test_entry_think_thresholds_from_settings():
    from tools import site_entry_think as ET
    assert ET.th() == ET.DEFAULT_TH                            # settings.yaml carries the same numbers as the defaults
    import wsb.config as CFG
    old = CFG.SETTINGS
    try:
        CFG.SETTINGS = {"entry_think": {"move_red": 120.0, "move_yellow": 100.0}}
        r = ET.move_check(pd.Series([100.0] * 9 + [125.0]))
        assert r["light"] == "r" and "高於 120" in r["rule"] and "高於 100" in r["rule"], r
    finally:
        CFG.SETTINGS = old
    r = ET.move_check(pd.Series([100.0] * 9 + [125.0]))
    assert r["light"] == "y" and "高於 130" in r["rule"]


def main():
    for f in (test_quote_change_uses_history_previous_close, test_single_quarter_missing_field_stays_unknown,
              test_squeeze_unread_previous_balance, test_entry_think_thresholds_from_settings):
        f()
        print("ok", f.__name__)


if __name__ == "__main__":
    main()
