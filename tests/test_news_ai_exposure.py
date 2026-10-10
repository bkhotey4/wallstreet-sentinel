"""AI news tagging + holdings × shock-path exposure.  Run: python -m tests.test_news_ai_exposure  (no network)"""
from __future__ import annotations

import asyncio
import os
import tempfile
import time
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_newsai_"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import tests.test_intel as TI  # noqa: E402
from wsb.ai import news_ai as NA  # noqa: E402
from wsb.analytics import exposure as EX  # noqa: E402
from wsb.analytics import intel as I  # noqa: E402


def main():
    now = time.time()
    a = TI.item("Oil jumps after missile strike", 3, 1)          # keyword hit (commodity) …
    b = TI.item("Heavy explosions in Strait of Hormuz", 0, 1)     # … no keyword at all
    c = TI.item("Treasury yields ease as auction goes smoothly", 0, 1)
    d = TI.item("Bank of Japan Accounts (September 30)", 0, 1)

    # ---------------------------------------------------------------- AI tags override keywords
    tags = {a.uid: {"ch": ["商品／地緣能源"], "dir": "neutral", "sev": 1},          # AI: informational → ignored
            b.uid: {"ch": ["商品／地緣能源", "波動率／槓桿去化"], "dir": "risk", "sev": 3},
            c.uid: {"ch": ["利率／債市衝擊"], "dir": "relief", "sev": 2},
            d.uid: {"ch": ["套息拆倉"], "dir": "risk", "sev": 0}}                   # routine → ignored
    h = I.channel_heat([a, b, c, d], now, tags)
    g = h["商品／地緣能源"]
    assert g["n"] == 1 and g["top"][0]["title"].startswith("Heavy explosions"), g
    assert abs(g["heat"] - 3 * 0.5 ** (1 / 12)) < 1e-9
    assert h["波動率／槓桿去化"]["n"] == 1
    assert h["利率／債市衝擊"]["n"] == 0 and h["利率／債市衝擊"]["n_relief"] == 1
    assert h["套息拆倉"]["n"] == 0 and h["套息拆倉"]["heat"] == 0
    # untagged headlines still use keywords
    h2 = I.channel_heat([a], now, {})
    assert h2["商品／地緣能源"]["n"] == 1

    # ---------------------------------------------------------------- classifier output validation
    nc = NA.NewsClassifier.__new__(NA.NewsClassifier)
    nc.tags, nc.ts, nc._client = {}, 0.0, None
    items = [a, b, c]
    rows = [{"id": 0, "channels": ["commodity_geo", "commodity_geo", "bogus"], "direction": "risk", "severity": 2},
            {"id": 1, "channels": ["vol"], "direction": "panic", "severity": 3},       # unknown direction → dropped
            {"id": 7, "channels": ["rates"], "direction": "risk", "severity": 1},      # id out of range → dropped
            {"id": 2, "channels": ["rates"], "direction": "relief", "severity": 9}]    # severity clamped to 3

    async def fake(user, n=None):
        return rows
    nc._claude = fake
    nc._gemini = lambda user: _wrap(rows)
    NA.ANTHROPIC_API_KEY, NA.GEMINI_API_KEY = "", "x"
    NA.CFG["enabled"] = True
    n = asyncio.run(nc.classify(items))
    assert n == 2, nc.tags
    assert nc.tags[a.uid] == {"ch": ["商品／地緣能源"], "dir": "risk", "sev": 2}
    assert nc.tags[c.uid]["sev"] == 3 and b.uid not in nc.tags
    assert asyncio.run(nc.classify(items[:1])) == 0                       # already tagged → no new call
    assert NA.NewsClassifier._parse('{"items": "x"}', "t") is None and NA.NewsClassifier._parse("nope", "t") is None
    # classify_all keeps reading batches until every headline is tagged (fresh process / site build)
    nc2 = NA.NewsClassifier.__new__(NA.NewsClassifier)
    nc2.tags, nc2.ts, nc2._client = {}, 0.0, None
    calls = []

    async def one(user):
        calls.append(1)
        return [{"id": 0, "channels": ["rates"], "direction": "risk", "severity": 1}], "gemini:test"
    nc2._gemini = one
    old = NA.CFG.get("max_per_call")
    NA.CFG["max_per_call"] = 1
    assert asyncio.run(nc2.classify_all([a, b, c, d], 10)) == 4 and len(calls) == 4 and len(nc2.tags) == 4
    assert asyncio.run(nc2.classify_all([a, b, c, d], 10)) == 0 and len(calls) == 4      # nothing left → no call
    NA.CFG["max_per_call"] = old if old is not None else 80
    gs = NA.GEMINI_SCHEMA["properties"]["items"]["items"]
    assert "additionalProperties" not in gs and gs["properties"]["severity"] == {"type": "integer", "minimum": 0, "maximum": 3}

    # ---------------------------------------------------------------- exposure on synthetic data
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2022-01-03", periods=800)
    credit = pd.Series(50 + np.cumsum(rng.normal(0, 2, len(idx))), index=idx).clip(0, 100)
    bh = pd.DataFrame({"信用": credit, "私募信貸": credit, "利率": 50 + rng.normal(0, 3, len(idx))}, index=idx)
    # BANK falls 0.4% per +1 point of credit stress; NOISE is unrelated
    bank = pd.Series(100 * np.exp(np.cumsum(-0.004 * credit.diff().fillna(0).values + rng.normal(0, 0.004, len(idx)))), index=idx)
    noise = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx)))), index=idx)
    lv = EX.path_levels(bh)
    sens = EX.sensitivities({"BANK": bank, "NOISE": noise}, lv)
    s_bank, s_noise = sens["信用事件"]["BANK"], sens["信用事件"]["NOISE"]
    assert abs(s_bank["sens_pct_per10"] - (np.exp(-0.04) - 1) * 100) < 0.6, s_bank
    assert s_bank["t"] < -5 and abs(s_noise["t"]) < 3, (s_bank, s_noise)
    assert 140 <= s_bank["n"] <= 160                                      # ~756/5 non-overlapping weeks

    mk = types.SimpleNamespace(series=lambda s: {"BANK": bank, "NOISE": noise}.get(s, pd.Series(dtype=float)))
    st = types.SimpleNamespace(block_history=bh)
    pf = {"total_value_usd": 20000.0, "positions": [{"sym": "BANK", "value_usd": 10000.0, "weight": 50.0},
                                                     {"sym": "NOISE", "value_usd": 10000.0, "weight": 50.0}]}
    intel = {"channels": [{"channel": "信用事件", "state": "確認", "fused": 70}]}
    eng = types.SimpleNamespace(stress=st, portfolio=pf, market=mk, intel=intel)
    out = EX.build(eng)
    assert out["available"] and out["paths"][0]["path"] == "信用事件"     # active path first
    top = out["paths"][0]["holdings"][0]
    assert top["sym"] == "BANK" and top["significant"] and top["usd_per10"] < -300, top
    line = EX.summary_lines(out)[0]
    assert "信用事件［確認］" in line and "BANK" in line, line
    assert EX.build(types.SimpleNamespace(stress=None, portfolio=pf, market=mk))["available"] is False
    assert out["mode"] == "portfolio"
    # no holdings loaded (public intelligence-station mode) → sector / asset universe, no $ figures
    EX.CFG["universe"] = ["BANK", "NOISE", "MISSING"]
    uni = EX.build(types.SimpleNamespace(stress=st, portfolio={"error": "none"}, market=mk, intel=intel))
    assert uni["available"] and uni["mode"] == "universe" and uni["paths"][0]["port_usd_per10"] is None
    assert [h["sym"] for h in uni["paths"][0]["holdings"]][0] == "BANK"
    assert "最受傷：BANK" in EX.summary_lines(uni)[0]

    # ---------------------------------------------------------------- privacy: exposure only in the private pack
    from wsb.ai import context
    import tests.test_offline as T
    from wsb.analytics import regime as RG, shock as SK
    from wsb.analytics.stress import StressEngine
    st2 = StressEngine(T.m, T.fr).compute()
    full = TI.T_engine(st2, RG.classify(T.m, T.fr), SK.build(st2, T.m.series("^GSPC")), [])
    full.exposure = out
    assert "持倉 × 傳導路徑曝險" in context.build(full, "us")
    assert "持倉 × 傳導路徑曝險" not in context.build(full, "us", private=False)
    print("NEWS-AI / EXPOSURE TESTS PASSED ✅")


async def _wrap(rows):
    return rows, "gemini:test"


if __name__ == "__main__":
    main()
