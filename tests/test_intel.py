"""Tests for the intelligence-fusion layer (news × prices × macro).  Run: python -m tests.test_intel"""
from __future__ import annotations

import os
import tempfile
import time
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_intel_"))   # never touch the live sentinel.db

import tests.test_offline as T  # noqa: E402  (installs synthetic market/FRED stubs)
from wsb.analytics import intel as I  # noqa: E402
from wsb.analytics import regime as RG  # noqa: E402
from wsb.analytics import shock as SK  # noqa: E402
from wsb.analytics.stress import StressEngine  # noqa: E402
from wsb.data.news import NewsItem  # noqa: E402
from wsb import store  # noqa: E402


def item(title, score=0, hours_ago=1.0, source="T"):
    return NewsItem(source, title, "http://x", time.time() - hours_ago * 3600, score)


def fake_paths(**states):
    """shock-radar paths: name → (ignition, state)"""
    blocks = {p["name"]: p["blocks"] for p in SK.DEFAULT_PATHS}
    return {"paths": [{"name": k, "ignition": ign, "state": s, "blocks": blocks[k], "story": ""}
                      for k, (ign, s) in states.items()]}


def main():
    now = time.time()
    # ---------------------------------------------------------------- tagging + decay + relief
    items = [item("Private credit fund gated as redemptions surge", 7, 1),
             item("Regional banks slide on loan losses", 4, 2),
             item("Oil jumps after missile strike in Middle East", 3, 1),
             item("Ceasefire talks: ceasefire and truce agreed", 0, 1),
             item("Stocks rally to record high", 0, 1),
             item("Bank of Japan holds; yen steady", 1, 30)]
    h = I.channel_heat(items, now)
    assert h["信用事件"]["n"] == 2 and h["信用事件"]["top"][0]["title"].startswith("Private credit")
    assert h["商品／地緣能源"]["n"] == 1 and h["商品／地緣能源"]["n_relief"] == 1        # relief headline not counted as risk
    assert h["波動率／槓桿去化"]["n"] == 0 and h["波動率／槓桿去化"]["n_relief"] == 1
    # a 30h-old story weighs ~1/5 of a fresh one (half-life 12h)
    fresh = I.channel_heat([item("yen surges", 1, 0)], now)["套息拆倉"]["heat"]
    old = I.channel_heat([item("yen surges", 1, 30)], now)["套息拆倉"]["heat"]
    assert abs(old / fresh - 0.5 ** 2.5) < 1e-6, (old, fresh)
    assert not I._match("Wonderful results", ["won"])                                    # word boundary
    assert I._match("台海緊張升溫", ["台海"])

    # ---------------------------------------------------------------- baseline percentile vs warm-up
    hist = {c: [0.5] * 60 for c in h}
    hist["信用事件"] = [float(x) for x in range(60)]
    I.news_levels(h, hist)
    assert not h["信用事件"]["warmup"] and h["信用事件"]["baseline"] == 60
    assert h["商品／地緣能源"]["level"] > 90 and h["商品／地緣能源"]["news_state"] == "溫"   # only 1 story → never "熱"
    h2 = I.channel_heat(items, now)
    I.news_levels(h2, {c: [] for c in h2})
    assert all(d["warmup"] for d in h2.values()) and 0 < h2["信用事件"]["level"] < 100
    assert h2["景氣衰退"]["level"] == 0 and h2["景氣衰退"]["news_state"] == "冷"
    # ≥5 risk headlines are never "quiet", whatever the warm-up heat says
    h3 = I.channel_heat([item(f"Treasury yields surge {k}", 0, 20) for k in range(6)], now)
    I.news_levels(h3, {c: [] for c in h3})
    assert h3["利率／債市衝擊"]["n"] == 6 and h3["利率／債市衝擊"]["news_state"] in ("溫", "熱")

    # ---------------------------------------------------------------- fusion states
    hh = {c: {"heat": 0, "n": 0, "relief": 0, "n_relief": 0, "top": [], "level": 10.0, "news_state": "冷",
              "easing": False, "warmup": False} for c in I.DEFAULT_CHANNELS}
    hh["信用事件"].update(level=92.0, n=4, news_state="熱", top=[{"source": "FT", "title": "x", "hits": []}])
    hh["利率／債市衝擊"].update(level=88.0, n=3, news_state="熱")
    sk = fake_paths(**{"信用事件": (74, "高度警戒"), "利率／債市衝擊": (40, "低"), "套息拆倉": (62, "留意"),
                       "波動率／槓桿去化": (30, "低"), "景氣衰退": (35, "低"), "商品／地緣能源": (45, "低")})
    fu = I.fuse(hh, sk, None)
    st_ = {r["channel"]: r["state"] for r in fu}
    assert st_["信用事件"] == "確認" and st_["利率／債市衝擊"] == "敘事領先" and st_["套息拆倉"] == "無聲壓力"
    assert st_["景氣衰退"] == "平靜"
    assert fu[0]["channel"] == "信用事件" and [r["state"] for r in fu][:3] == ["確認", "無聲壓力", "敘事領先"]
    cr = next(r for r in fu if r["channel"] == "信用事件")
    assert abs(cr["fused"] - (0.65 * 74 + 0.35 * 92)) < 1e-9
    assert "≥58" in next(r for r in fu if r["channel"] == "利率／債市衝擊")["watch"]
    # regression (live 2026-10-08): 13 bond-selloff headlines at level 79 (溫) + stressed prices were labelled
    # 無聲壓力 ("headlines quiet").  Warm news + stressed prices point the same way → 確認.
    hh["套息拆倉"].update(level=79.0, n=13, news_state="溫")
    assert {r["channel"]: r["state"] for r in I.fuse(hh, sk, None)}["套息拆倉"] == "確認"
    # …but a single headline is an anecdote, not confirmation
    hh["套息拆倉"].update(level=85.0, n=1, news_state="溫")
    assert {r["channel"]: r["state"] for r in I.fuse(hh, sk, None)}["套息拆倉"] == "無聲壓力"
    hh["套息拆倉"].update(level=10.0, n=0, news_state="冷")
    # a routine headline with no risk keyword weighs half of a score-1 headline
    assert abs(I.channel_heat([item("BOJ accounts", 0, 0)], now)["套息拆倉"]["heat"] * 2
               - I.channel_heat([item("BOJ accounts", 1, 0)], now)["套息拆倉"]["heat"]) < 1e-9

    # ---------------------------------------------------------------- macro pillar
    m, why = I.macro_pillar({"quadrant": "停滯性通膨 Stagflation", "liquidity_mode": "收縮 (逆風)",
                             "net_liquidity_chg_13w_bn": -120, "risk_mode": "Risk-OFF 避險", "risk_appetite_z": -0.8,
                             "quadrant_changed": True, "quadrant_1m": "金髮女孩 Goldilocks", "growth_drift": -0.7,
                             "inflation_drift": 0.6, "growth_z": -0.4})
    assert m == 100 and len(why) == 5, why            # 75+10+10+5+5 → capped; no +8: inflation z unknown → flip not "clear"
    # regression (live 2026-10-08): growth z +0.02 → -0.01 flipped Reflation→Stagflation and the pillar jumped 55 → 98
    assert abs(I.quadrant_base(0.02, 1.29) - I.quadrant_base(-0.01, 1.29)) < 2
    assert I.quadrant_base(2, 2) == 45 and I.quadrant_base(-2, 2) == 75 and abs(I.quadrant_base(0, 2) - 60) < 1e-9
    m3, why3 = I.macro_pillar({"quadrant": "停滯性通膨 Stagflation", "quadrant_1m": "再通膨 Reflation", "quadrant_changed": True,
                               "growth_z": -0.01, "inflation_z": 1.29, "growth_drift": -0.21, "inflation_drift": 1.03,
                               "liquidity_mode": "收縮 (逆風)", "net_liquidity_chg_13w_bn": -46})
    assert 65 <= m3 <= 75 and not any("轉入" in t for _, t in why3), (m3, why3)
    m2, _ = I.macro_pillar({"quadrant": "金髮女孩 Goldilocks", "liquidity_mode": "擴張 (順風)", "risk_mode": "Risk-ON 追價"})
    assert m2 == 20
    assert I.macro_pillar({})[0] is None

    # ---------------------------------------------------------------- full pipeline on the synthetic market
    st = StressEngine(T.m, T.fr).compute()
    rg = RG.classify(T.m, T.fr)
    assert "drift" in rg and "quadrant_1m" in rg and isinstance(rg["quadrant_changed"], bool), rg.keys()
    shock = SK.build(st, T.m.series("^GSPC"))
    news = types.SimpleNamespace(items=items, ts=time.time())
    eng = types.SimpleNamespace(news=news, shock=shock, stress=st, regime=rg, odds={})
    out = I.build(eng, record=True)
    v = out["verdict"]
    assert v["available"] and 0 <= v["score"] <= 100 and v["confidence"] in ("高", "中", "低")
    assert set(v["pillars"]) == {"量化", "總經", "情報"} and v["pillars"]["量化"] == st.score
    assert any("基準仍在累積" in c for c in v["caveats"])                               # fresh DB → warm-up caveat
    assert v["weights"]["情報"] == 0.125                                                 # news pillar half-weighted in warm-up
    exp = sum(v["weights"][k] * x for k, x in v["pillars"].items() if x is not None) / \
        sum(v["weights"][k] for k, x in v["pillars"].items() if x is not None)
    assert abs(v["base"] - exp) < 1e-9 and abs(v["score"] - min(100, exp + v["bonus"])) < 1e-9
    assert len(out["channels"]) == 6 and v["headline"].startswith("綜合風險")
    # baseline recording is throttled (one snapshot per 30 min)
    assert len(store.heat_history("信用事件")) == 1
    I.build(eng, record=True)
    assert len(store.heat_history("信用事件")) == 1
    # a dead news wire must not teach the baseline that "zero" is normal
    I.build(types.SimpleNamespace(news=types.SimpleNamespace(items=[], ts=0), shock=shock, stress=st, regime=rg, odds={}))
    # missing pillars are dropped and re-weighted, never treated as 0
    e2 = types.SimpleNamespace(news=types.SimpleNamespace(items=[], ts=0), shock={}, stress=st, regime={}, odds={})
    v2 = I.build(e2, record=False)["verdict"]
    assert v2["pillars"]["總經"] is None and v2["pillars"]["情報"] is None and abs(v2["score"] - st.score) < 1e-9

    # ---------------------------------------------------------------- data pack + views
    from wsb.ai import context
    from wsb.bot import command as CMD
    full = types.SimpleNamespace(**vars(T_engine(st, rg, shock, items)), intel=out)
    pack = context.build(full, "full")
    assert "## 情報融合" in pack and "信用事件［" in pack and "總經漂移" in pack, pack[:400]
    em = CMD.embed_intel(full)
    assert em.title.startswith("🧩 情報融合") and len(em.fields) >= 2
    try:
        pngs = CMD.deck_intel(full)
        assert len(pngs) == 3 and all(p[:4] == b"\x89PNG" for p in pngs)
    except ImportError:
        print("  (PIL missing: slide rendering skipped)")
    print(f"intel OK — {v['headline']} | 信心 {v['confidence']} | {v['consensus']}")
    for r in out["channels"]:
        print(f"  {r['channel']:<10} {r['state']:<5} fused {r['fused']:5.1f} ign {r['ignition']} news {r['news_level']:.0f}")


def T_engine(st, rg, shock, items):
    """minimal engine for the DATA PACK / views (mirrors tests.test_offline)."""
    nw = types.SimpleNamespace(items=items, top=lambda n=15, q=None: items[:n], latest=lambda n=15: items[:n], ts=time.time())
    return types.SimpleNamespace(
        market=T.m, fred=T.fr, stress=st, odds={}, regime=rg, portfolio={}, shock=shock, xray={}, playbook={}, breaks={},
        lab={}, options=types.SimpleNamespace(spx=None), crypto=types.SimpleNamespace(data={}), news=nw,
        sec=types.SimpleNamespace(recent=[]), taiwan=None,
        calendar=types.SimpleNamespace(events=[], upcoming=lambda d=14: []))


if __name__ == "__main__":
    main()
