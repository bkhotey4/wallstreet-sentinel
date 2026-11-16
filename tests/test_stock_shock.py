"""個股大動警報：門檻、兩個方向、新聞配對、句子、回放、Discord 一天最多 3 則個別＋1 則彙總（不連網）。"""
from __future__ import annotations

import asyncio
import pathlib
import tempfile

import numpy as np
import pandas as pd


def main() -> None:
    from wsb.analytics import stock_shock as ST

    assert ST.level(-6.2, 1.68) == 1 and ST.level(+6.2, 1.68) == 1          # 3.7× either way
    assert ST.level(-9.0, 1.68) == 2
    assert ST.level(-3.9, 0.9) == 0                                        # 4.3× but under 4 %
    assert ST.level(-6.0, 2.0) == 0 and ST.level(None, 2.0) == 0 and ST.level(-6.0, None) == 0
    # Taiwan: a normal day is ~3 %, so 3.0× and ≥ 6 % (台達電 -9.3 % on 11-16 was 3.0×; the US rule would have missed it)
    assert ST.level(-9.27, 3.06, "tw") == 1 and ST.level(-9.27, 3.06) == 0
    assert ST.level(-5.5, 1.5, "tw") == 0                                  # 3.7× but under 6 %
    assert ST.level(+9.9, 2.0, "tw") == 2

    now = 1794500000.0
    news = [{"t": "Cisco shares slide after outlook disappoints", "ts": now - 15 * 3600, "u": "https://x/1"},
            {"t": "Cisco: an old story", "ts": now - 30 * 3600, "u": "https://x/2"},
            {"t": "Nubank posts record profit", "ts": now - 600, "u": "https://x/3"},
            {"t": "A headline from the future", "ts": now + 600, "u": "https://x/4"}]
    names = {"CSCO": ["思科", "Cisco"], "NU": ["Nu Holdings（巴西數位銀行）", "Nu Holdings"], "KO": ["可口可樂", "Coca-Cola"]}
    keys = {"CSCO": ["思科", "Cisco"], "NU": ["Nubank", "Nu Holdings"], "KO": ["可口可樂", "Coca-Cola"]}
    q = {"CSCO": {"chg": -6.24, "t": now}, "NU": {"chg": 11.75, "t": now}, "KO": {"chg": -0.4, "t": now}, "XX": {"chg": -30, "t": now}}
    hits = ST.check(q, {"CSCO": 1.68, "NU": 2.35, "KO": 0.9}, names, news, now, keys)
    assert [h["sym"] for h in hits] == ["NU", "CSCO"], hits                # most unusual first; no σ → never alerts
    assert [n["u"] for n in hits[1]["news"]] == ["https://x/1"]             # 30 h old is left out
    assert [n["u"] for n in hits[0]["news"]] == ["https://x/3"]
    s = ST.sentence(hits[1], lambda ts: "08:00")
    assert s.startswith("思科（CSCO）-6.2%，是它平常一天的 3.7 倍。同時段提到它的新聞：〈Cisco shares"), s
    assert "找不到對得上的新聞" in ST.sentence({**hits[1], "news": []}, lambda ts: "")
    assert ST.check({"CSCO": {"chg": "n/a"}}, {"CSCO": 1.68}, names, [], now) == []

    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2025-06-02", periods=320)
    r = rng.normal(0, 1.5, (320, 2))
    r[-10, 0], r[-3, 1], r[-200, 0] = -9.0, 8.0, -9.0                       # two recent shocks; one outside the window
    cl = pd.DataFrame(100 * np.cumprod(1 + r / 100, axis=0), index=idx, columns=["AAA", "BBB"])
    rp = ST.replay(cl, ["AAA", "BBB", "ZZZ"], days=60)
    assert rp["total"] == 2 and rp["fired_days"] == 2 and rp["max_day"] == 1 and rp["over_cap_days"] == 0, rp
    assert set(ST.sigmas(cl, ["AAA", "ZZZ"])) == {"AAA"}
    top, rest = ST.split([{"sym": str(i)} for i in range(5)])
    assert len(top) == ST.DAY_CAP and len(rest) == 2

    # Discord: at most DAY_CAP single messages a day, then one summary; nothing twice
    import tools.sec_push as P
    P.PUSHED = pathlib.Path(tempfile.mkdtemp()) / "p.json"
    sent = []
    five = [{"sym": f"S{i}", "zh": f"公司{i}", "chg": -5.0 - i, "z": -4.0 - i, "lv": 2 if i else 1, "t": now, "news": [], "day": "2026-11-13"} for i in range(5)]
    five.sort(key=lambda a: a["z"])
    calls = []

    async def fake_stocks(sess, t):
        calls.append(t)
        return [dict(a) for a in five]

    async def none(*a, **k):
        return []

    async def no_sec(watch, now=0):
        return {"alerts": []}

    async def fake_impact(sess, sym, zh):
        return [f"{zh} 今天 -5.0%", "・標普 500：它占 0.5%"]

    async def fake_post(sess, ch, emb, key=None):
        sent.append(emb)
        return True

    async def fake_news(sess):
        return {"bursts": [], "items": []}

    async def no_one(*a, **k):
        return None

    async def no_hold(sess, t, ctx=None):
        return 0

    async def no_health(t, nj, hsent):
        return [], 0

    async def fake_country(sess):
        return {}
    from wsb.data import sec_officers as SOF
    real = (SOF.refresh, P.stock_alerts, P.sector_alerts, P.impact, P.post, P.watch_list, P.DISCORD_TOKEN, P.alert_channel,
            P.news_json, P.tx_night, P.yen_jump, P.holdings_run, P.health_check, P.country_json, P.CATCH_GAP)
    try:
        SOF.refresh, P.stock_alerts, P.sector_alerts, P.impact, P.post, P.watch_list = no_sec, fake_stocks, none, fake_impact, fake_post, lambda: {}
        P.news_json, P.tx_night, P.yen_jump, P.holdings_run, P.health_check, P.country_json = fake_news, no_one, no_one, no_hold, no_health, fake_country
        P.DISCORD_TOKEN, P.alert_channel, P.CATCH_GAP = "t", lambda: "123", 10 ** 12
        P.FISCAL_EVERY = P.FORCED_EVERY = P.KOREA_EVERY = P.RULINGS_EVERY = P.EARNSOON_EVERY = 10 ** 12   # slow official-data checks have their own tests
        assert asyncio.run(P.run_once(now=now)) == ST.DAY_CAP + 1, [e["title"] for e in sent]
        assert sent[0]["title"] == "🔴 個股大跌：公司4 -9.0%（平常一天的 8.0 倍）", sent[0]["title"]
        assert "找不到對得上的新聞" in sent[0]["description"] and "**可能影響**" in sent[0]["description"] and "標普 500" in sent[0]["description"]
        assert sent[3]["title"] == "🟠 今天有 5 檔追蹤的美股大動" and "公司0" in sent[3]["description"] and "公司4" not in sent[3]["description"]
        assert asyncio.run(P.run_once(now=now + 180)) == 0 and len(calls) == 1          # looked at once per 15 minutes
        assert asyncio.run(P.run_once(now=now + 1000)) == 0 and len(calls) == 2         # same day: nothing new
        for a in five:
            a["day"] = "2026-11-16"
        assert asyncio.run(P.run_once(now=now + 2000)) == ST.DAY_CAP + 1                 # a new day starts a new count
        # Taiwan hits keep their own daily count and their own summary, and use the Taiwan impact lines
        tw5 = [{**a, "sym": f"T{i}.TW", "mk": "tw", "day": "2026-11-16"} for i, a in enumerate(five)]
        five[:] = tw5
        sent.clear()
        tw_calls = []

        async def fake_tw_impact(sess, sym, zh):
            tw_calls.append(sym)
            return [f"{zh} 今天 -9.0%", "・台股加權同時 -0.50%"]
        real_tw, P.stock_tw_impact = P.stock_tw_impact, fake_tw_impact
        try:
            assert asyncio.run(P.run_once(now=now + 3000)) == ST.DAY_CAP + 1, [e["title"] for e in sent]
        finally:
            P.stock_tw_impact = real_tw
        assert len(tw_calls) == ST.DAY_CAP and "台股加權" in sent[0]["description"]
        assert sent[3]["title"] == "🟠 今天有 5 檔追蹤的台股大動", sent[3]["title"]
    finally:
        (SOF.refresh, P.stock_alerts, P.sector_alerts, P.impact, P.post, P.watch_list, P.DISCORD_TOKEN, P.alert_channel,
         P.news_json, P.tx_night, P.yen_jump, P.holdings_run, P.health_check, P.country_json, P.CATCH_GAP) = real
    for e in sent:
        for w in ("目標價", "買進", "賣出", "買點", "低估", "高估"):
            assert w not in e["title"] + e["description"]
    print("test_stock_shock ok")


if __name__ == "__main__":
    main()


def test_earnings_reaction_named():
    from wsb.analytics import stock_shock as ST
    cal = {"2026-11-17": {"rows": [{"sym": "NVDA", "time": "after"}, {"sym": "HD", "time": "pre"}]},
           "2026-11-13": {"rows": [{"sym": "AMAT", "time": "after"}]}}
    assert ST.earnings_note("NVDA", "2026-11-18", cal) == "11/17 收盤後公布財報"
    assert ST.earnings_note("HD", "2026-11-17", cal) == "今天開盤前公布財報"
    assert ST.earnings_note("NVDA", "2026-11-17", cal) is None          # the report comes after this session's close
    assert ST.earnings_note("AMAT", "2026-11-16", cal) == "11/13 收盤後公布財報"   # over the weekend
    s = ST.sentence({"zh": "輝達", "sym": "NVDA", "chg": -8.0, "z": -3.9, "earn": "11/17 收盤後公布財報", "news": []}, lambda t: "")
    assert "財報後的反應" in s and "原因還不清楚" not in s


if __name__ == "__main__":
    test_earnings_reaction_named()
    print("ok test_earnings_reaction_named")
