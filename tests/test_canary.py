"""金絲雀: new SSI transforms, FINRA parsing, every rule light, revision snapshots, site card, alert routing.
Run: python -m tests.test_canary"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import types
from datetime import date, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_canary_"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import canary as CN  # noqa: E402
from wsb.analytics.stress import StressEngine  # noqa: E402


class _Fred:
    def __init__(self, d):
        self.d = d

    def get(self, sid):
        return self.d.get(sid, pd.Series(dtype=float))


class _Mkt:
    def __init__(self, h):
        self.history = h

    def series(self, t):
        return self.history[t].dropna() if t in self.history.columns else pd.Series(dtype=float)


def test_transforms():
    idx = pd.bdate_range("2019-01-01", periods=900)
    rng = np.random.default_rng(0)
    m = rng.normal(0, 0.01, len(idx))
    h = pd.DataFrame({"SPY": 100 * np.cumprod(1 + m), "TLT": 100 * np.cumprod(1 + 0.5 * m + rng.normal(0, 0.002, len(idx))),
                      "^GSPC": 100 * np.cumprod(1 + m)}, index=idx)
    ioer = pd.Series(2.0, index=idx[:400])
    iorb = pd.Series(4.0, index=idx[400:])
    sofr = pd.Series(np.r_[np.full(400, 2.05), np.full(500, 3.98)], index=idx)
    fred = _Fred({"SOFR": sofr, "IORB": iorb, "IOER": ioer, "WLCFLPCL": pd.Series(np.r_[np.full(890, 1000.0), np.full(10, 150000.0)], index=idx)})
    se = StressEngine(_Mkt(h), fred)
    sp = se.raw_series({"src": "fred", "series": "SOFR", "kind": "spread:IORB|IOER:ma5"}, se._base_index())
    assert abs(sp.iloc[200] - 0.05) < 1e-9, sp.iloc[200]                  # IOER era: 2.05 − 2.00
    assert abs(sp.iloc[-1] + 0.02) < 1e-9, sp.iloc[-1]                    # IORB era: 3.98 − 4.00
    lg = se.raw_series({"src": "fred", "series": "WLCFLPCL", "kind": "log"}, se._base_index())
    assert lg.iloc[-1] > lg.iloc[-20] + 4                                 # a spike is visible on the log scale
    pc = se.raw_series({"src": "px", "series": "SPY", "kind": "pcorr:60:TLT"}, se._base_index())
    assert 0.8 < pc.iloc[-1] <= 1.0, pc.iloc[-1]                          # TLT built to co-move → strong positive corr
    assert se.source_last_date({"src": "fred", "series": "SOFR", "kind": "spread:IORB|IOER:ma5"}) == idx[-1]
    from wsb.config import SETTINGS
    assert {"IYT", "XHB", "TLT"} <= set(SETTINGS.all_tickers())            # pcorr / rel tickers are downloaded


def test_finra():
    from wsb.data import finra as F
    rows = [["Year-Month", "Debit Balances in Customers' Securities Margin Accounts", "x", "y"]]
    d = date(2026, 8, 1)
    for i in range(40):
        m = (pd.Timestamp(d) - pd.DateOffset(months=i))
        rows.append([m.strftime("%Y-%m"), 1_000_000 * (1.02 ** (40 - i)), 1, 1])
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, header=False, index=False)
    s = F.parse(buf.getvalue())
    assert len(s) == 40 and s.index[-1] == pd.Timestamp("2026-08-01")
    md = F.MarginDebt()
    md.series = s
    y = md.yoy().dropna()
    assert abs(y.iloc[-1] - (1.02 ** 12 - 1) * 100) < 1e-6


def _eng(h, fred=None, md=None, earnings=None):
    return types.SimpleNamespace(market=_Mkt(h), fred=_Fred(fred or {}), margin_debt=md, earnings=earnings, stress=None)


def test_rule_lights():
    idx = pd.bdate_range("2015-01-01", periods=1500)
    flat = pd.Series(100.0, index=idx)
    h = pd.DataFrame({"^GSPC": flat, "TLT": flat, "GC=F": flat}, index=idx)
    h.iloc[-5:, :] = [[96, 97, 97]] * 5                                   # last week: −4 %, −3 %, −3 % → dash for cash
    eng = _eng(h)
    r = CN.cash_dash_light(eng)
    assert r["state"] == "alert" and "標普 -4.0%" in r["value_txt"], r
    h2 = h.copy()
    h2.iloc[-5:, 2] = 100                                                  # gold flat → only two of three
    assert CN.cash_dash_light(_eng(h2))["state"] == "watch"
    # RRP: depleted + reserves falling at a 3-year extreme
    w = pd.date_range("2022-01-05", periods=200, freq="W-WED")
    rrp = pd.Series(np.r_[np.linspace(2000, 10, 199), [5.0]], index=w)
    res = pd.Series(np.r_[np.full(196, 3000.0), [3000, 2950, 2850, 2700]], index=w)
    r = CN.rrp_light(_eng(h, {"RRPONTSYD": pd.Series(np.interp(np.arange(1000), np.arange(200) * 5, rrp.values),
                                                     index=pd.bdate_range("2022-01-05", periods=1000)), "WRESBAL": res}))
    assert r["state"] == "alert", r
    # margin debt: YoY ≥ 40 % → alert, history computed
    from wsb.data.finra import MarginDebt
    md = MarginDebt()
    mi = pd.date_range("2015-01-01", periods=120, freq="MS")
    md.series = pd.Series(np.r_[np.full(100, 500000.0), 500000 * 1.03 ** np.arange(1, 21)], index=mi)
    r = CN.margin_light(_eng(pd.DataFrame({"^GSPC": pd.Series(np.linspace(100, 200, 4000), index=pd.bdate_range("2014-01-01", periods=4000))}), md=md))
    assert r["state"] == "alert" and "年增率" in r["value_txt"], r
    # split market: highs and lows together while the index is above its 50-day line
    ci = pd.bdate_range("2024-01-01", periods=300)
    cols = {}
    for k in range(400):
        base = 100 + np.sin(np.arange(300) / 20 + k) * 5
        if k < 12:
            base[-1] = 200                                                # new highs (3 %)
        elif k < 24:
            base[-1] = 50                                                 # new lows (3 %)
        cols[f"S{k}"] = base
    close = pd.DataFrame(cols, index=ci)
    up = pd.DataFrame({"^GSPC": pd.Series(np.linspace(100, 130, 300), index=ci)})
    r = CN.split_light(_eng(up), close)
    assert r["state"] == "alert" and "52 週新高 3." in r["value_txt"] and "新低 3." in r["value_txt"], r
    assert CN.split_light(_eng(up), None)["state"] == "na"


def test_revisions():
    t0 = date(2026, 9, 1)
    rows = [{"sym": f"S{k}", "eps_f": 1.0, "mcap": 5e10} for k in range(30)]
    ed = types.SimpleNamespace(days={"2026-11-20": {"rows": rows}})
    eng = _eng(pd.DataFrame(), earnings=ed)
    CN.REV_FILE.unlink(missing_ok=True)
    snap = CN.record_revisions(eng, t0)
    assert CN.revision_light(eng, snap, t0)["state"] == "warmup"
    for k in range(30):                                                    # 4+ weeks later: 15 cut, 3 raised
        rows[k]["eps_f"] = 0.9 if k < 15 else 1.05 if k < 18 else 1.0
    snap = CN.record_revisions(eng, t0 + timedelta(days=30))
    r = CN.revision_light(eng, snap, t0 + timedelta(days=30))
    assert r["state"] == "alert" and "下修 15" in r["value_txt"], r      # (3 − 15) / 30 = −40 %


def test_site_and_alerts():
    from tools import site_sections as S2
    eng = types.SimpleNamespace(canary={"available": True, "n_alert": 1, "n_watch": 0, "rows": [
        {"id": "ccc_bb", "group": "信用品質", "zh": "CCC − BB", "en": "CCC−BB", "why": "w", "kind": "score", "state": "alert", "score": 99.0,
         "value": 10.83, "unit": "pp", "asof": "2026-10-14", "rate": 25.0, "since": "2024-10", "chg_3m": 4.0, "history": ["2023-03 <x>"]},
        {"id": "discount_window", "group": "資金市場", "zh": "貼現窗口", "en": "DW", "why": "w", "kind": "score", "state": "watch", "score": 96.0,
         "value": 9.97, "unit": "$B", "asof": "2026-10-15"},
        {"id": "eps_revisions", "group": "景氣類股", "zh": "獲利預估", "en": "rev", "why": "w", "kind": "rule", "state": "warmup",
         "rule": "r", "note": "累積中"}]})
    html = S2.sec_canary(eng)
    assert "金絲雀" in html and "紅燈" in html and "10.83pp" in html and "&lt;x&gt;" in html and "累積中" in html
    assert "US$9.97B" in html
    from wsb.bot.app import _alert_kind
    assert _alert_kind("canary:ccc_bb:2026-10-14") == "risk"
    # alerts: once on entering red; yellow does not re-arm, green does
    from wsb.bot.app import Sentinel
    bot = types.SimpleNamespace(engine=types.SimpleNamespace(canary={"rows": []}))
    rows = bot.engine.canary["rows"]
    def run(state, asof):
        rows[:] = [{"id": "ccc_bb", "zh": "CCC − BB", "state": state, "asof": asof, "score": 99.0}]
        return Sentinel._canary_alerts(bot)
    from wsb import store
    first = run("alert", "2026-10-14")
    assert len(first) == 1
    assert len(run("alert", "2026-10-14")) == 1            # not delivered yet → still offered (a failed send is retried)
    store.alert_mark(first[0].key, first[0].severity, first[0].title)
    assert run("alert", "2026-10-14") == []                # delivered → disarmed
    assert run("alert", "2026-10-15") == [] and run("watch", "2026-10-16") == [] and run("alert", "2026-10-17") == []
    assert run("ok", "2026-10-18") == [] and len(run("alert", "2026-10-19")) == 1


def test_score_lights_on_engine():
    """Run the score lights against a real StressEngine result (synthetic market) — catches field-name mistakes."""
    import tests.test_offline as T
    st = StressEngine(T.m, T.fr).compute()
    eng = types.SimpleNamespace(market=T.m, fred=T.fr, stress=st, stress_engine=StressEngine(T.m, T.fr))
    rows = CN.score_lights(eng)
    assert {r["id"] for r in rows} == {x[0] for x in CN.SCORE_LIGHTS}
    assert all(r["state"] in ("ok", "watch", "alert", "warmup", "stale", "na") for r in rows)
    out = CN.build(eng)
    assert out["available"] and len(out["rows"]) == len(CN.SCORE_LIGHTS) + 6
    from wsb.config import SETTINGS
    ssi_ids = {c["id"] for c in SETTINGS.get("stress_components", [])}
    assert not ({"sofr_iorb", "cp_tbill", "stock_bond_corr"} & ssi_ids)          # validated wrong-way → out of the SSI
    rows = {r["id"]: r for r in rows}
    assert rows["stock_bond_corr"]["in_ssi"] is False and rows["move" if "move" in rows else "transports"]["in_ssi"] is True
    # rate-hike pricing light
    fv = {"available": True, "asof": "2026-10-16", "meetings": [
        {"date": "2026-10-28", "rate_after": 3.95, "cum_bp": 7}, {"date": "2026-12-09", "rate_after": 4.17, "cum_bp": 29},
        {"date": "2027-01-27", "rate_after": 4.28, "cum_bp": 40, "week_ago": {"rate_after": 4.20}}]}
    h = CN.hike_light(types.SimpleNamespace(fedwatch_view=fv))
    assert h["state"] == "watch" and "+40bp" in h["value_txt"] and "+8bp" in h["value_txt"], h
    fv["meetings"][2]["week_ago"] = {"rate_after": 4.05}
    assert CN.hike_light(types.SimpleNamespace(fedwatch_view=fv))["state"] == "alert"      # +23bp in a week
    assert CN.hike_light(types.SimpleNamespace(fedwatch_view={}))["state"] == "na"


def main():
    test_score_lights_on_engine()
    test_transforms()
    test_finra()
    test_rule_lights()
    test_revisions()
    test_site_and_alerts()
    print("CANARY TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
