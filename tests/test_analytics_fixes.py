"""Analytics-layer audit fixes (synthetic data, no network).  Run: python -m tests.test_analytics_fixes"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from datetime import date, datetime, timezone
from pathlib import Path

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_afix_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import wsb.analytics.sessions as SS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IN_SESSION = datetime(2026, 11, 4, 15, 0, tzinfo=timezone.utc)      # 10:00 New York, Wed 2026-11-04
AFTER_CLOSE = datetime(2026, 11, 4, 22, 0, tzinfo=timezone.utc)     # 17:00 New York


class _Clock:
    """Run sessions.completed with a fixed clock (modules import it lazily, so patching the module attribute works)."""
    def __init__(self, now):
        self.now, self.real = now, SS.completed

    def __enter__(self):
        real, now = self.real, self.now
        SS.completed = lambda px, sym="", now_=None: real(px, sym, now)
        return self

    def __exit__(self, *a):
        SS.completed = self.real


def _px():
    return pd.Series([100.0, 101.0, 110.0], index=pd.to_datetime(["2026-11-02", "2026-11-03", "2026-11-04"]))


def test_isotonic_min_block():
    from wsb.analytics import lab as L
    rng = np.random.default_rng(0)
    p = np.concatenate([rng.uniform(0.01, 0.30, 3000), rng.uniform(0.80, 0.90, 40)])
    y = np.concatenate([(rng.uniform(size=3000) < 0.10).astype(float), np.ones(40)])   # one cluster of overlapping windows
    old = L.isotonic(p, y)                                      # no minimum block: the lone episode calibrates to 100 %
    assert L.apply_iso(old, 0.95) == 1.0
    new = L.isotonic(p, y, min_w=5 * 63)
    top = float(L.apply_iso(new, 0.95))
    assert top < 0.5, top                                       # pooled with a well-populated block
    assert np.all(np.diff(new[1]) >= -1e-12) and np.all(np.diff(new[0]) > 0)
    assert abs(float(L.apply_iso(new, 0.99)) - top) < 1e-12     # flat beyond the last block (no extrapolation)


def test_implied_log_waits_for_final_bar():
    from wsb.analytics import implied_log as IL
    log = {"NVDA|2026-11-03": {"sym": "NVDA", "date": "2026-11-03", "mv": 6.0}}
    with _Clock(IN_SESSION):
        IL.resolve(log, lambda s: _px(), "2026-11-04")
    assert log["NVDA|2026-11-03"].get("act") is None            # the post-report bar is still in progress
    with _Clock(AFTER_CLOSE):
        IL.resolve(log, lambda s: _px(), "2026-11-04")
    assert abs(log["NVDA|2026-11-03"]["act"] - 10.0) < 1e-9


def test_techearn_calendar_react_completed():
    from wsb.analytics import techearn as TE
    ed = types.SimpleNamespace(days={"2026-11-03": {"rows": [{"sym": "NVDA", "name": "Nvidia", "time": "after", "eps_f": 1.0, "n_est": 10,
                                                              "eps_ly": 0.8, "mcap": 4e12, "eps": 1.2, "surprise": 20.0}]}})
    sp = types.SimpleNamespace(series=lambda s: _px())
    with _Clock(IN_SESSION):
        cv = TE.calendar_view(ed, {"NVDA": ("輝達", "Nvidia")}, {"NVDA": "AI"}, sp, "2026-11-04")
    assert cv["past"][0]["react"] is None
    with _Clock(AFTER_CLOSE):
        cv = TE.calendar_view(ed, {"NVDA": ("輝達", "Nvidia")}, {"NVDA": "AI"}, sp, "2026-11-04")
    assert abs(cv["past"][0]["react"] - 10.0) < 1e-9


def test_signals_strip_unfinished_bar():
    from wsb.analytics import signals as SG
    vol = pd.Series([1e6, 1e6, 2e5], index=_px().index)
    sp = types.SimpleNamespace(series=lambda s: _px(), vol=lambda s: vol)
    with _Clock(IN_SESSION):
        cl, vo = SG._closed(sp, "NVDA")
    assert len(cl) == 2 and len(vo) == 2 and vo.index[-1] == cl.index[-1]
    with _Clock(AFTER_CLOSE):
        cl, vo = SG._closed(sp, "NVDA")
    assert len(cl) == 3 and len(vo) == 3


def test_momentum_volume_alignment():
    from wsb.analytics import web_alerts as W
    idx = pd.bdate_range(end="2026-11-04", periods=80)
    v = pd.Series(1e6, index=idx)
    v.iloc[-1] = 1e6                                            # 10:00 NY = 0.5 h of a 6.5 h session → full-day pace 13×
    vx = W._vol_ratio(v, "NVDA", "2026-11-04", datetime(2026, 11, 4, 15, 30, tzinfo=timezone.utc))
    assert vx is not None and abs(vx - 1e6 / (1 / 6.5) / 1e6) < 1e-6, vx
    assert W._vol_ratio(v, "NVDA", "2026-11-04", AFTER_CLOSE) == 1.0
    assert W._vol_ratio(v.iloc[:-1], "NVDA", "2026-11-04", AFTER_CLOSE) is None   # yesterday's volume vs today's move
    assert W._vol_ratio(v, "NVDA", "2026-11-04", datetime(2026, 11, 4, 14, 35, tzinfo=timezone.utc)) is None  # first minutes


def test_adr_pairs_next_us_close():
    from wsb.analytics import mood as MO
    tw = pd.Series([600.0, 610.0, 620.0], index=pd.to_datetime(["2026-01-16", "2026-01-19", "2026-01-20"]))  # Fri, Mon, Tue
    us = pd.Series([200.0, 205.0], index=pd.to_datetime(["2026-01-16", "2026-01-20"]))                          # Mon 19 = US holiday
    fx = pd.Series([31.0, 31.5, 32.0], index=tw.index)
    df = MO.adr_pairs(us, tw, fx)
    assert list(df.index.strftime("%Y-%m-%d")) == ["2026-01-16", "2026-01-20"], df     # Mon's TW close shares Tue's US close → dropped
    assert df["us_d"].iloc[0] == pd.Timestamp("2026-01-16") and df["tw"].iloc[-1] == 620.0 and df["fx"].iloc[-1] == 32.0
    df2 = MO.adr_pairs(us, tw, fx.iloc[:1])                     # no FX print on those dates → no forward-filled rows
    assert list(df2.index.strftime("%Y-%m-%d")) == ["2026-01-16"]


def test_live_history_used():
    from wsb.analytics import cooldown as CD, outlook as OL
    from wsb.analytics.stress import ref_history
    idx = pd.bdate_range(end="2026-11-04", periods=600)
    stale = pd.Series(80.0, index=idx)
    live = pd.Series(30.0, index=idx)
    st = types.SimpleNamespace(score=30.0, history=stale, live_history=live, label="低", pctile_all=10.0, chg_20d=0.0)
    assert ref_history(st, 500) is live and ref_history(types.SimpleNamespace(history=stale, live_history=live.iloc[:100]), 500) is stale
    eng = types.SimpleNamespace(stress=st, market=types.SimpleNamespace(series=lambda t: pd.Series(dtype=float)), rotation=None)
    row = next(r for r in CD.checks(eng) if r["k"] == "ssi")
    assert "一個月前 30" in row["txt"] and "SSI 30" in row["txt"]
    d = OL.crisis(st, {})
    assert d["prev"] == 30.0, d["prev"]                         # stale-component history would give 0.6·80 + 0.4·30 = 60
    src = (ROOT / "wsb" / "engine.py").read_text(encoding="utf-8")
    assert "sk.model_quality, ssi_h" in src and "lb.run, self.market.history, ssi_h" in src


def test_conditional_needs_independent_windows():
    from wsb.analytics import crash_odds as CO, shock as SK
    idx = pd.bdate_range("2010-01-01", periods=2000)
    rng = np.random.default_rng(1)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx)))), index=idx)
    ssi = pd.Series(25.0, index=idx)
    ssi.iloc[1000:1030] = 90.0                                  # 30 days in the zone ≈ 1.4 independent 21-day windows
    odds = CO.crash_odds(ssi, close, 90.0, 0.0)
    for h in odds["horizons"]:
        assert h["obs_in_zone"] == 30 and h["conditional"] is None and h["lift"] is None, h
    ssi.iloc[200:900] = 90.0                                    # plenty of windows → a frequency again (for the 21-day horizon)
    odds = CO.crash_odds(ssi, close, 90.0, 0.0)
    assert odds["horizons"][0]["conditional"] is not None
    # divergence: 40 flagged days on a 63-day horizon ≈ 0.6 windows → no probability
    bh = pd.DataFrame({SK.CREDIT_LIKE[0]: 20.0, SK.EQUITY_LIKE[0]: 20.0}, index=idx)
    bh.iloc[500:540, 0] = 60.0
    st = types.SimpleNamespace(blocks={SK.CREDIT_LIKE[0]: 60.0, SK.EQUITY_LIKE[0]: 20.0}, block_history=bh)
    hs = SK.divergence(st, close)["hist"]
    assert hs["days_flagged"] == 40 and hs["prob_when_flagged"] is None and hs["n_eff"] < 5


def test_fomc_wording_from_results():
    from wsb.analytics import fomc_drift as FD
    old = {"mean": 0.5, "base_mean": 0.03, "t": 3.0, "up": 70}
    gone = FD._day_line(old, {"mean": 0.05, "base_mean": 0.03, "t": 0.4, "up": 52})
    still = FD._day_line(old, {"mean": 0.45, "base_mean": 0.03, "t": 2.6, "up": 68})
    none = FD._day_line({**old, "t": 0.6}, {"mean": 0.05, "base_mean": 0.03, "t": 0.4, "up": 52})
    assert "大致消失" in gone["zh"] and "大致消失" not in still["zh"] and "仍然明顯" in still["zh"]
    assert "學界" not in none["zh"] and "大致消失" not in none["zh"] and "兩段都看不出" in none["zh"]


def test_m1b_release_lag():
    from wsb.analytics import twmacro as TM
    rng = np.random.default_rng(3)
    months = pd.period_range("1990-01", periods=300, freq="M")
    sig = rng.uniform(size=len(months)) < 0.5
    px = [100.0]
    for i in range(1, len(months)):                             # the jump is in month M → M+1, before M's data is out
        px.append(px[-1] * (1.05 if sig[i - 1] else 1.0) * (1 + rng.normal(0, 0.002)))
    lab = [str(m) for m in months]
    d = {"cbc": {"m1b": [[m, 6.0 if s else 4.0] for m, s in zip(lab, sig)], "m2": [[m, 5.0] for m in lab],
                 "taiex": [[m, p] for m, p in zip(lab, px)]}}
    look = TM.m1b_test(d, horizon=1, lag=0)
    real = TM.m1b_test(d, horizon=1)
    assert look["up_med"] - look["dn_med"] > 4                  # the look-ahead version "finds" the edge
    assert abs(real["up_med"] - real["dn_med"]) < 2 and real["lag"] == 1 and real["n_eff_up"] > 0


def test_tw_calendar_marked_approx():
    from wsb.analytics import twmacro as TM
    rows = TM.calendar_rows({}, today=date(2026, 11, 4))
    assert rows and all(r["approx"] and r["when_zh"].startswith("約 ") for r in rows)


def test_release_dates():
    from wsb.analytics import bubble as BU, canary as CA
    idx = pd.bdate_range("2025-01-01", periods=400)
    px = pd.Series(100.0, index=idx)
    tue = pd.Timestamp("2025-03-04")                            # a Tuesday
    px.loc[pd.Timestamp("2025-03-05")] = 80.0                   # crash on Wednesday, gone by Friday's release
    dd = BU.release_dd(px, pd.DatetimeIndex([tue]))
    assert abs(dd.iloc[0]) < 1e-12, dd                          # measured from Friday 03-07, not the Tuesday close
    assert CA.margin_release(pd.Timestamp("2026-09-01")) == pd.Timestamp("2026-10-25")
    assert CA.margin_release(pd.Timestamp("2026-09-30")) == pd.Timestamp("2026-10-25")


def test_canary_us_today():
    from wsb.analytics import canary as CA
    from wsb.data import econcal as EC
    real = EC.us_today
    EC.us_today = lambda: date(2030, 1, 2)
    try:
        eng = types.SimpleNamespace(earnings=types.SimpleNamespace(days={"2030-01-05": {"rows": [{"sym": "AAA", "eps_f": 1.0, "mcap": 2e10}]}}))
        snap = CA.record_revisions(eng)
    finally:
        EC.us_today = real
    assert snap["AAA|2030-01-05"][-1][0] == "2030-01-02"


def test_danger_sigma_scaled():
    from wsb.analytics import danger as DG
    idx = pd.bdate_range(end="2026-11-04", periods=2600)
    rng = np.random.default_rng(4)
    r_avg = rng.normal(0, 0.01, len(idx))
    calm = r_avg.copy()
    calm[-253:] *= 0.4                                          # a calm last year
    s_avg = pd.Series(100 * np.exp(np.cumsum(r_avg)), index=idx)
    s_calm = pd.Series(100 * np.exp(np.cumsum(calm)), index=idx)
    assert 0.85 < DG.vol_scale(s_avg) < 1.15 and DG.vol_scale(s_calm) < 0.6
    q = lambda t: {"chg_pct": -0.8, "price": 100.0, "asof": "2026-11-04"} if t == "^GSPC" else None  # noqa: E731
    assert DG.score("us", q)["points"] == 0                    # fixed thresholds: −0.8 % is not a −1 % day
    hot = DG.score("us", q, series=lambda t: s_calm)
    assert hot["points"] >= 1 and hot["hits"][0]["scale"] < 0.6
    assert DG.score("us", q, series=lambda t: s_avg)["points"] == 0   # average volatility: same meaning as before


def test_verdict_missing_estimate():
    from wsb.analytics import earn_verdict as EV
    v = EV.verdict({"result": "beat", "eps": 1.2, "eps_f": None, "surp": None, "react": None, "accel": {"dir": "??", "now": 10.0, "prev": 8.0}})
    txt = " ".join(v.values()) if isinstance(v, dict) else str(v)
    assert "預期 —" in txt and "營收成長變化" in txt


def test_rsi_flat_is_neutral():
    from wsb.analytics import stockscore as SC
    assert SC.rsi(pd.Series(100.0, index=pd.bdate_range("2026-01-01", periods=40))) == 50.0


def test_compliance_words():
    banned = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")
    for f in ("sector_companies", "macro_events", "canary", "stockscore", "focus", "premarket", "intel", "outlook", "rulebook"):
        src = (ROOT / "wsb" / "analytics" / f"{f}.py").read_text(encoding="utf-8")
        hit = [w for w in banned if w in src]
        assert not hit, (f, hit)
    from wsb.analytics import siteextra as SX
    out = SX.debate_prompt({"name": "X", "sym": "X"}, {"tm": 120.0, "up": 25.0, "n": 30, "rm": 1.8})
    assert "目標價" not in out and "30 位" in out and "1.8" in out


def main():
    for k, f in list(globals().items()):
        if k.startswith("test_") and callable(f):
            f()
            print("  ok", k)
    print("ANALYTICS FIX TESTS PASSED")


if __name__ == "__main__":
    main()
