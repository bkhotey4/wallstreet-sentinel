"""SEC → Discord 小程式：嚴重度排序、只送一次、私訊條件、訊息格式（不連網、不真的送）。"""
from __future__ import annotations

import asyncio
import pathlib
import tempfile


def main() -> None:
    import tools.sec_push as P
    from wsb.data import sec_officers as SOF

    ceo = {"acc": "a1", "ts": 1000, "sym": "NVDA", "zh": "輝達", "url": "https://www.sec.gov/a1", "item": "5.02",
           "t": "SEC 申報：輝達（NVDA）執行長離職（8-K 第 5.02 項）"}
    dirs = {"acc": "a2", "ts": 1100, "sym": "MRVL", "zh": "邁威爾", "url": "https://www.sec.gov/a2", "item": "5.02",
            "t": "SEC 申報：邁威爾（MRVL）董事任命（8-K 第 5.02 項）"}
    rst = {"acc": "a3", "ts": 900, "sym": "X", "zh": "某公司", "url": "https://www.sec.gov/a3", "item": "4.02",
           "t": "SEC 申報：某公司（X）過去財報不可再信賴（須重編）（8-K 第 4.02 項）"}
    assert P.severity(rst) > P.severity(ceo) >= 3 > P.severity(dirs)
    e = P.embed_of(ceo, ["輝達 今天 **-5.6%**", "・標普 500：它占 6.4%"])
    assert e["title"].startswith("🔴 SEC 申報：輝達") and e["url"] == ceo["url"] and "不是預測" in e["description"]
    assert "不構成投資建議" in e["footer"]["text"]
    for w in ("買進", "賣出", "目標價", "低估", "高估"):
        assert w not in e["description"]

    P.PUSHED = pathlib.Path(tempfile.mkdtemp()) / "p.json"
    sent, dms = [], []

    async def fake_refresh(watch, now=0):
        return {"alerts": [dirs, ceo, rst, dict(ceo, acc="old", ts=now - 7 * 3600)]}

    async def fake_impact(sess, sym, zh):
        return [f"{zh} 影響"]

    async def fake_post(sess, ch, emb):
        (dms if ch == "dm" else sent).append(emb["title"])
        return True

    async def fake_dm(sess):
        return "dm"
    async def no_sectors(sess, now):
        return []
    real = (SOF.refresh, P.impact, P.post, P.dm_channel, P.watch_list, P.DISCORD_TOKEN, P.alert_channel, P.sector_alerts)
    try:
        SOF.refresh, P.impact, P.post, P.dm_channel, P.watch_list, P.sector_alerts = fake_refresh, fake_impact, fake_post, fake_dm, lambda: {}, no_sectors
        P.DISCORD_TOKEN, P.alert_channel = "t", lambda: "123"
        n = asyncio.run(P.run_once(now=1200))
        assert n == 3 and sent[0].startswith("🔴 SEC 申報：某公司") and sent[1].startswith("🔴 SEC 申報：輝達"), sent   # worst first; 7h-old skipped
        assert len(dms) == 2 and not any("邁威爾" in d for d in dms)                                           # director appointment: channel only
        assert asyncio.run(P.run_once(now=1300)) == 0                                                           # never sent twice
        # no channel set (the bot's current setup): everything goes to the owner's DM, once
        P.PUSHED.unlink()
        sent.clear(); dms.clear()
        P.alert_channel = lambda: ""
        assert asyncio.run(P.run_once(now=1500)) == 3 and len(dms) == 3 and not sent
        P.DISCORD_TOKEN = ""
        assert asyncio.run(P.run_once(now=1600)) == 0
    finally:
        SOF.refresh, P.impact, P.post, P.dm_channel, P.watch_list, P.DISCORD_TOKEN, P.alert_channel, P.sector_alerts = real
    print("test_sec_push ok")


if __name__ == "__main__":
    main()
