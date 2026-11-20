import numpy as np
import pandas as pd

from tools import tw_rules_backtest as B


def _px(closes, highs=None, lows=None, opens=None):
    idx = pd.bdate_range("2020-01-01", periods=len(closes))
    c = pd.DataFrame({"X.TW": closes}, index=idx, dtype=float)
    o = pd.DataFrame({"X.TW": opens if opens is not None else closes}, index=idx, dtype=float)
    h = pd.DataFrame({"X.TW": highs if highs is not None else closes}, index=idx, dtype=float)
    l = pd.DataFrame({"X.TW": lows if lows is not None else closes}, index=idx, dtype=float)
    v = pd.DataFrame({"X.TW": [1e6] * len(closes)}, index=idx, dtype=float)
    return {"Open": o, "High": h, "Low": l, "Close": c, "Volume": v}


def _sig(px, day):
    s = pd.DataFrame(False, index=px["Close"].index, columns=px["Close"].columns)
    s.iloc[day] = True
    return s


def _params(**kw):
    p = B.Params(market_filter=False, time_stop=1000, risk=0.5, cap=1.0, max_pos=1, breaker_dd=0.99, **kw)
    return p


def test_cost_math():
    c = B.Costs()
    assert abs(c.buy_cash(100) - 100.1425) < 1e-9
    assert abs(c.sell_cash(100) - (100 - 0.1425 - 0.3)) < 1e-9
    assert abs(c.round_trip() - (1 - (1 - 0.004425) / 1.001425)) < 1e-12
    assert 0.0058 < c.round_trip() < 0.0059


def test_no_lookahead_entry_next_open():
    closes = [100] * 30
    opens = [100] * 30
    opens[11] = 101                        # 訊號在第 10 天收盤 → 第 11 天開盤 101 進場
    px = _px(closes, opens=opens)
    res = B.backtest(px, _sig(px, 10), _params(tp1=None), "2020-01-01")
    t = res["trades"][0]
    assert t["entry_i"] == 11, t


def test_stop_before_tp_same_day():
    n = 20
    closes = [100.0] * n
    highs = [100.0] * n
    lows = [100.0] * n
    highs[7], lows[7] = 120.0, 90.0       # 進場隔天同時碰到 +15% 與 −7.5%
    px = _px(closes, highs=highs, lows=lows)
    res = B.backtest(px, _sig(px, 5), _params(tp1=0.15), "2020-01-01")
    t = res["trades"][0]
    assert t["tp"] is False and t["exit_i"] == 7
    exp = B.Costs().sell_cash(92.5) / B.Costs().buy_cash(100) - 1
    assert abs(t["ret"] - exp) < 1e-9, (t["ret"], exp)


def test_tp_half_then_trailing():
    closes = [100.0] * 8 + [105, 110, 116, 118, 117, 108, 100, 100, 100, 100]
    px = _px(closes, highs=[x * 1.0 for x in closes], lows=[x * 1.0 for x in closes], opens=closes)
    p = _params(tp1=0.15, trail_ma=3)
    res = B.backtest(px, _sig(px, 6), p, "2020-01-01")
    t = res["trades"][0]
    assert t["tp"] is True
    assert t["ret"] > 0.05, t
    assert not t.get("open_at_end")


def test_signal_d_uses_past_only():
    rng = np.random.default_rng(0)
    c = 100 * np.cumprod(1 + rng.normal(0, 0.01, 400))
    px = _px(list(c))
    s1 = B.signals(px, "D")
    c2 = c.copy()
    c2[-1] = c2[-1] * 0.5                  # 改最後一天，不能影響前面的訊號
    s2 = B.signals(_px(list(c2)), "D")
    assert s1.iloc[:-1].equals(s2.iloc[:-1])


if __name__ == "__main__":
    test_cost_math(); test_no_lookahead_entry_next_open(); test_stop_before_tp_same_day()
    test_tp_half_then_trailing(); test_signal_d_uses_past_only(); print("ok")
