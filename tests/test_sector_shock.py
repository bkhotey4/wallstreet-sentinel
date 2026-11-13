"""族群急跌警報：穩健的平常幅度、門檻、新聞配對、句子、Discord 只送一次（不連網）。"""
from __future__ import annotations

import asyncio
import pathlib
import tempfile

import numpy as np
import pandas as pd


def main() -> None:
    from wsb.analytics import sector_shock as SS

    rng = np.random.default_rng(3)
    r = rng.normal(0, 2.0, 300)
    r[-60:-54] = -12                                                   # a few crash days must not inflate "a normal day"
    px = pd.Series(100 * np.cumprod(1 + r / 100), index=pd.bdate_range("2025-08-01", periods=300))
    sd = SS.robust_sd(px)
    plain = float(px.pct_change().dropna().iloc[-252:].std() * 100)
    assert 1.7 < sd < 2.3 and sd < plain, (sd, plain)
    assert SS.robust_sd(px.iloc[:50]) is None

    assert SS.level(-5.5, 2.44) == 1 and SS.level(-7.5, 2.44) == 2
    assert SS.level(-1.2, 0.5) == 0                                # 2.4× but under 1.5 %: not a sector shock
    assert SS.level(-3.0, 2.44) == 0 and SS.level(+6.0, 2.0) == 0 and SS.level(None, 2.0) == 0

    now = 1794500000
    news = [{"t": "Bessent slams Nvidia chip 'leakage' to China", "ts": now - 1800, "u": "https://x/1"},
            {"t": "Chicago Fed's Goolsbee says work to do on inflation", "ts": now - 3600, "u": "https://x/2"},
            {"t": "Old chip story", "ts": now - 8 * 3600, "u": "https://x/3"},
            {"t": "Coca-Cola invests in Hungary", "ts": now - 600, "u": "https://x/4"}]
    q = {"^SOX": {"chg": -5.5, "t": now}, "XLK": {"chg": -3.3, "t": now}, "XLF": {"chg": 0.1, "t": now}}
    hits = SS.check(q, {"^SOX": 2.44, "XLK": 1.64, "XLF": 0.9}, news, now)
    assert [h["sym"] for h in hits] == ["^SOX", "XLK"] and hits[0]["lv"] == 1
    assert [n["u"] for n in hits[0]["news"]] == ["https://x/1"]                     # 8 h old and off-topic are left out
    assert hits[0]["macro"][0]["u"] == "https://x/2"
    s = SS.sentence(hits[0], lambda ts: "23:00")
    assert s.startswith("費城半導體 -5.5%（平常一天的 2.3 倍）；同時段新聞：〈Bessent") and "總經消息" in s
    lone = SS.sentence({**hits[0], "news": [], "macro": []}, lambda ts: "")
    assert "找不到時間和主題都對得上的新聞，原因還不清楚" in lone
    for w in ("買進", "賣出", "目標價", "低估", "高估"):
        assert w not in s

    import tools.sec_push as P
    P.PUSHED = pathlib.Path(tempfile.mkdtemp()) / "p.json"
    sent = []

    async def no_sec(watch, now=0):
        return {"alerts": []}

    async def fake_sectors(sess, now):
        return [dict(hits[0], day="2026-11-13", tw=[{"zh": "台積電", "beta": 0.45}])]

    async def fake_post(sess, ch, emb):
        sent.append(emb)
        return True
    from wsb.data import sec_officers as SOF
    real = (SOF.refresh, P.sector_alerts, P.post, P.watch_list, P.DISCORD_TOKEN, P.alert_channel)
    try:
        SOF.refresh, P.sector_alerts, P.post, P.watch_list = no_sec, fake_sectors, fake_post, lambda: {}
        P.DISCORD_TOKEN, P.alert_channel = "t", lambda: "123"
        assert asyncio.run(P.run_once(now=now)) == 1
        e = sent[0]
        assert e["title"] == "🟠 族群急跌：費城半導體 -5.5%（平常一天的 2.3 倍）" and "台積電 約 -2.5%" in e["description"]
        assert asyncio.run(P.run_once(now=now + 180)) == 0                       # once per sector, day and level
    finally:
        SOF.refresh, P.sector_alerts, P.post, P.watch_list, P.DISCORD_TOKEN, P.alert_channel = real
    print("test_sector_shock ok")


if __name__ == "__main__":
    main()
