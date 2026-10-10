"""Google_Financial feature port (website extras): parsers, pattern tags, exhaustion, fear & greed, alarm-rule backtest,
US→TW linkage, expected moves, geopolitical heat, 個股情報 assembly, AI bull/bear notes and the rendered pages.
Offline.   WSB_DATA_DIR=/tmp/x python -m tests.test_siteextra"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import tests.test_expansion as X
from tools import build_site as B
from tools import site_intel as S4
from wsb.analytics import growth as GR
from wsb.analytics import mood as MO
from wsb.analytics import patterns as PT
from wsb.analytics import siteextra as SX
from wsb.data import earnings_data as ED
from wsb.data import geo as GEO
from wsb.data import http
from wsb.data import stockinfo as SI
from wsb.health import HEALTH


def test_patterns():
    idx = pd.bdate_range(end="2026-10-07", periods=300)
    rng = np.random.default_rng(1)
    # volatile, then very quiet → Bollinger squeeze + range
    c = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 300))), index=idx)
    c.iloc[-40:] = c.iloc[-41] * (1 + rng.normal(0, 1, 40) * np.linspace(0.004, 0.0003, 40))
    t = PT.tags(c, pd.Series(1e6, index=idx))
    assert "squeeze" in t and "box" in t, t
    # range breakout on volume, and a failed one
    c2 = c.copy()
    v = pd.Series(1e6, index=idx)
    c2.iloc[-2] = c.iloc[-35:-5].max() * 1.04
    c2.iloc[-1] = c.iloc[-35:-5].max() * 1.05
    v.iloc[-2] = 3e6
    assert "box_break" in PT.tags(c2, v)
    c3 = c2.copy()
    c3.iloc[-1] = c.iloc[-35:-5].max() * 0.99
    assert "box_fail" in PT.tags(c3, v)
    # double bottom: decline, low, bounce +8%, second low, rally through the neckline
    seg = np.concatenate([np.linspace(130, 100, 40), np.linspace(100, 108, 10), np.linspace(108, 100.5, 10), np.linspace(100.5, 109.5, 12)])
    c4 = pd.Series(np.concatenate([np.full(300 - len(seg), 130.0) + rng.normal(0, 0.3, 300 - len(seg)), seg]), index=idx)
    assert "w_break" in PT.tags(c4), PT.tags(c4)
    c5 = c4.copy()
    c5.iloc[-1] = 106.5
    c5.iloc[-2] = 105.0
    c5.iloc[-3] = 104.0
    assert "w_form" in PT.tags(c5), PT.tags(c5)
    # moving-average cross within 5 sessions
    c6 = pd.Series(100.0, index=idx)
    c6.iloc[-3:] = 110.0
    assert "ma_gc" in PT.tags(c6) and "ma_dc" in PT.tags(200 - c6), PT.tags(c6)
    # exhaustion: parabolic run with fading volume
    c7 = pd.Series(np.cumprod(np.concatenate([np.full(1, 100.0), 1 + np.concatenate([rng.normal(0.0005, 0.01, 259), np.full(40, 0.012)])])), index=idx)
    v7 = pd.Series(2e6, index=idx)
    v7.iloc[-5:] = 0.9e6
    e = PT.exhaustion(c7, v7)
    assert {"rsi", "stretch", "vol_div"} <= set(e["flags"]) and e["n"] >= 3, e
    assert "RSI 過熱" in PT.exh_text(e)
    assert PT.exhaustion(c7.iloc[:100])["n"] == 0
    print("  patterns ok")


def cboe_fixture(spot=500.0, days=(4, 11, 32), today=None):
    today = today or date.today()
    opts = []
    for d in days:
        e = (today + timedelta(days=d)).strftime("%y%m%d")
        for k in range(int(spot * 0.9), int(spot * 1.1) + 1, 5):
            intr_c, intr_p = max(spot - k, 0), max(k - spot, 0)
            tv = spot * 0.02 * np.sqrt(d / 7) * np.exp(-((k - spot) / (spot * 0.05)) ** 2)
            for cp, intr in (("C", intr_c), ("P", intr_p)):
                opts.append({"option": f"SPY{e}{cp}{int(k * 1000):08d}", "bid": round(intr + tv * 0.98, 2), "ask": round(intr + tv * 1.02, 2)})
    return {"data": {"current_price": spot, "options": opts}}


def test_parsers():
    info = {"currentPrice": 100, "targetMeanPrice": 120, "targetHighPrice": 150, "targetLowPrice": 90, "numberOfAnalystOpinions": 25,
            "recommendationMean": 1.9, "recommendationKey": "buy", "dividendRate": 2.0, "exDividendDate": int(time.time()) + 86400 * 10,
            "payoutRatio": 0.35}
    y = date.today().year
    ann = {str(y - 6): 1.0, str(y - 5): 1.1, str(y - 4): 1.2, str(y - 3): 1.3, str(y - 2): 1.4, str(y - 1): 1.5, str(y): 0.5}
    d = SI.parse_info(info, ann)
    assert abs(d["up"] - 20) < 1e-9 and abs(d["yld"] - 2.0) < 1e-9 and d["grow"] == 5 and d["paid"] == 6 and d["n"] == 25, d
    assert SI.parse_info({"currentPrice": 10}, {})["yld"] is None
    js = {"cik": "0000320193", "filings": {"recent": {
        "form": ["8-K", "8-K", "4", "NT 10-Q", "8-K"], "filingDate": [date.today().isoformat()] * 4 + ["2000-01-01"],
        "accessionNumber": ["0001-26-1", "0001-26-2", "0001-26-3", "0001-26-4", "0001-26-5"],
        "items": ["2.02,9.01", "4.02,5.02", "", "", "1.03"]}}}
    rows = SI.parse_filings(js, "AAPL")
    assert [r["sev"] for r in rows] == [1, 3, 3] and "先前財報不可再信賴" in rows[1]["labels"] and rows[2]["form"] == "NT 10-Q", rows
    assert all("/320193/" in r["url"] for r in rows)
    ch = SI.parse_cboe(cboe_fixture())
    assert len(ch["rows"]) == 3 and ch["rows"][0]["k"] == 500 and 1 < ch["rows"][0]["mv"] < 10, ch["rows"]
    assert ch["rows"][0]["mv"] < ch["rows"][2]["mv"], "longer expiry → bigger straddle"
    d0 = (date.today() + timedelta(days=4)).isoformat()
    assert SI.straddle_after(ch, d0)["days"] == 4 and SI.straddle_after(ch, d0, after_close=True)["days"] == 11
    assert GEO.grade("China launches live-fire drills around Taiwan")[0] == 2
    assert GEO.grade("Russia begins full-scale invasion")[0] == 3 and GEO.grade("共軍宣布封鎖台海")[0] == 3
    assert GEO.grade("Leaders hold talks")[0] == 1 and GEO.grade("Stocks rally")[0] == 0
    now = time.time()
    cache = {"days": {(date.today() - timedelta(days=i)).isoformat(): {"taiwan": 10.0} for i in range(1, 20)}}
    raw = {"taiwan": [{"t": f"PLA drills near Taiwan {i}", "link": "x", "ts": now - 3600} for i in range(12)]
           + [{"t": "PLA drills near Taiwan 1", "link": "dup", "ts": now - 3600}], "korea": []}
    v = GEO.assemble(raw, cache, now)
    assert v["taiwan"]["n"] == 12 and v["taiwan"]["score"] == 24.0 and v["taiwan"]["level"]["k"] == 2, v["taiwan"]
    assert v["korea"]["level"]["k"] == 0
    print("  parsers ok")


def test_mood():
    import tests.test_offline as T
    h = T.m.history
    fg = MO.fear_greed(h)
    assert fg["available"] and 0 <= fg["score"] <= 100 and len(fg["components"]) >= 5 and len(fg["buckets"]) == 5, fg.get("components")
    assert sum(b["n"] for b in fg["buckets"]) > 500 and fg["hist"]
    rb = MO.rule_backtest(h)
    assert rb["available"] and len(rb["rows"]) >= 8 and rb["base"]["n"] > 1000
    assert all(r["verdict"] in ("warn", "rev", "none", "n") for r in rb["rows"])
    em = MO.expected_move({"SPY": SI.parse_cboe(cboe_fixture())}, h)
    b = em["rows"][0]["bands"]
    assert em["available"] and b[0]["zh"] == "本週" and b[0]["lo"] < 500 < b[0]["hi"] and b[0]["rv_sd"] and b[1]["days"] == 32, b
    print("  mood ok")


def write_caches(eng):
    today = date.today()
    us = list(X.universe()["us"]["symbols"])
    yf = {}
    for i, s in enumerate(list(X.universe()["us"]["symbols"])[:30] + list(X.universe()["tw"]["symbols"])[:10]):
        yf[s] = {**SI.parse_info({"currentPrice": 100, "targetMeanPrice": 100 + i, "targetHighPrice": 140, "targetLowPrice": 80,
                                  "numberOfAnalystOpinions": 10 + i, "recommendationMean": 2.1, "dividendRate": 1.5 if i % 3 == 0 else None,
                                  "exDividendDate": int(time.time()) + 86400 * 5},
                                 {str(today.year - k): 1.5 for k in range(1, 5)}), "ts": time.time()}
    SI._save(SI.F_YF, yf)
    k8 = {"AAPL": {"ts": time.time(), "rows": SI.parse_filings({"cik": "320193", "filings": {"recent": {
        "form": ["8-K", "8-K"], "filingDate": [today.isoformat()] * 2, "accessionNumber": ["1", "2"], "items": ["4.02", "7.01"]}}}, "AAPL")}}
    SI._save(SI.F_8K, k8)
    ed = eng.earnings
    rd = (today + timedelta(days=3)).isoformat()
    ed.days = {rd: {"ts": time.time(), "rows": [{"sym": "NVDA", "name": "NVIDIA", "time": "after", "eps_f": 1.0, "eps": None}]}}
    past = [(today - timedelta(days=91 * k)).isoformat() for k in range(1, 5)]
    ED._save(ED.F_SURP, {"NVDA": {"ts": time.time(), "rows": [{"date": d} for d in past]}})
    SI._save(SI.F_OPT, {"SPY": {**SI.parse_cboe(cboe_fixture()), "ts": time.time()},
                        "NVDA": {**SI.parse_cboe(cboe_fixture(150, (1, 4, 8))), "ts": time.time()}})
    GEO._save({"ts": time.time(), "view": GEO.assemble({"taiwan": [{"t": "China drills near Taiwan", "link": "https://e.com", "ts": time.time()}],
                                                        "mideast": []}, {}), "days": {}})
    GR.OUT_US.write_text(json.dumps(GR.pack([{"rank": i + 1, "sym": s, "name": s + " Inc", "ind": "Tech", "g": 40 - i, "gav": 0.1 * (i + 1),
                                               "basis": "P/GP", "score": 90 - i, "mcap": 5e9, "ttm": 1e9} for i, s in enumerate(us[:12])],
                                             GR.US_COLS, asof=today.isoformat(), listed=12, ranked=12), ensure_ascii=False), encoding="utf-8")
    return us


async def fake_get(url, **kw):
    if "company_tickers" in url:
        return {"0": {"ticker": "AAPL", "cik_str": 320193}, "1": {"ticker": "NVDA", "cik_str": 1045810}}
    if "data.sec.gov/submissions" in url:
        return {"cik": "320193", "filings": {"recent": {"form": ["8-K"], "filingDate": [date.today().isoformat()], "accessionNumber": ["9"], "items": ["5.02"]}}}
    if "cboe.com" in url:
        return cboe_fixture()
    raise RuntimeError("offline")


def main():
    test_patterns()
    test_parsers()
    test_mood()
    tmp = Path("/tmp/wsb_siteextra")
    shutil.rmtree(tmp, ignore_errors=True)
    eng = X.make_engine(tmp)
    HEALTH.ok("yahoo_quotes", 90, every=300)
    asyncio.run(eng.recompute())
    us = write_caches(eng)
    # signals carry pattern tags + exhaustion; the full-market scan carries them as columns
    allr = [r for m in eng.signals["markets"].values() for r in m["all"]]
    assert all("tags" in r and "exh" in r for r in allr) and "exhausted" in eng.signals["markets"]["us"]
    # refresh plumbing with the network mocked
    SI._yf_one = lambda s: SI.parse_info({"currentPrice": 50, "targetMeanPrice": 60, "numberOfAnalystOpinions": 3}, {})
    http.get = fake_get

    async def no_feed(u):
        return [{"t": "Missile strike reported", "link": "x", "ts": time.time()}]
    GEO._feed = no_feed
    (SI.F_8K).unlink()
    rep = asyncio.run(SX.refresh(eng))
    assert rep["sec8k"] >= 1 and rep["earnings_window"] == 1, rep
    assert SI.load_all()["yf"].get(us[40], {}).get("tm") == 60, "stale names refreshed through the (mocked) Yahoo call"
    # AI bull / bear notes (stubbed model), then assemble + render
    from wsb.ai import llm

    async def fake_llm(system, prompt, max_tokens=900):
        assert "不得出現買進" in system and "營收年增" in prompt
        return json.dumps({"bull": "營收年增 40%，成長加速。", "bear": "估值偏高。\n建議買進。", "risk": "觀察營收年增是否跌破 20%。"}), "stub"
    llm.complete = fake_llm
    assert asyncio.run(SX.generate_debates(3)) == 3 and asyncio.run(SX.generate_debates(3)) == 0, "weekly cache"
    cl = eng.stockprices.close                               # a realistic ADR premium (~20%) for the synthetic prices
    fx = eng.market.history["TWD=X"].reindex(cl.index).ffill()
    cl["TSM"] = cl["2330.TW"] * 5 / fx * (1.2 + 0.02 * np.sin(np.arange(len(cl)) / 20))
    eng.sx = SX.build(eng)
    sx = eng.sx
    assert 15 < sx["link"]["adr"]["now"] < 25, sx["link"]["adr"]
    assert sx["stocks"]["analyst"]["us"] and sx["stocks"]["div"]["us"] and sx["k8"]["n_hi"] >= 0 and sx["k8"]["rows"]
    er = sx["earn"][0]
    assert er["sym"] == "NVDA" and er["mv"] and len(er["reacts"]) == 4 and er["ratio"], er
    assert sx["fg"]["available"] and sx["rules"]["available"] and sx["em"]["available"] and sx["geo"]["available"]
    assert sx["link"]["available"] and sx["link"]["rows"] and sx["link"]["adr"] and sx["link"]["index"]
    assert sx["debate"][0]["ai"]["bull"] and "建議買進" not in sx["debate"][0]["ai"]["bear"], "advice lines scrubbed"
    page = B.render(eng, "", "")
    for s in ("個股情報", "情緒與警報", "分析師共識與目標價", "股息雷達", "SEC 重大申報", "高管／董事異動", "財報前隱含波動",
              "恐慌與貪婪指數（多因子）", "期權預期波動區間", "大盤警報規則回測", "地緣風險燈號", "台美連動", "台積電 ADR 溢價",
              "過熱／力竭警示", "硬科技一分鐘科普", "CoWoS", "AI 多空辯論", "交易成本試算", 'class="calc"', 'table class="mini srt"', 'id="p-tools"'):
        assert s in page, s
    assert "data-private" not in page
    out = tmp / "site"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    for k in ("sec_fees", "sec_explainer"):
        assert getattr(S4, k)(eng)
    print(f"  site {len(page) / 1024:.0f} KB")
    print("SITE EXTRAS TESTS PASSED ✅")


if __name__ == "__main__":
    main()
