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
    news = {"bursts": []}

    async def fake_news(sess):
        return news

    async def no_night(sess, now):
        return None

    got_ctx = {}

    async def no_hold(sess, now, ctx=None):
        got_ctx.update(ctx or {})
        return 0

    async def no_yen(sess, now):
        return None

    async def fake_mkt(sess, tags, now):
        return ["・相關行情現在：布蘭特原油 +3.0%"]
    hp = {"new": []}

    async def fake_health(now, nj, hsent):
        return hp["new"], len(hp["new"])
    real2 = (P.news_json, P.tx_night, P.holdings_run, P.market_now, P.yen_jump, P.CATCH_GAP, P.gap_moves, P.health_check)
    P.news_json, P.tx_night, P.holdings_run, P.market_now, P.yen_jump, P.health_check = fake_news, no_night, no_hold, fake_mkt, no_yen, fake_health
    P.CATCH_GAP = 10 ** 12                                  # the catch-up message has its own test below
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
        # ---- 2026-11-14: an update to an old 13D is never pushed; a new 13D is, like any other alert
        P.PUSHED.unlink()
        sent.clear(); dms.clear()
        P.alert_channel = lambda: "123"
        d13 = {"acc": "d1", "ts": 1400, "sym": "NVDA", "zh": "輝達", "url": "https://www.sec.gov/d1", "item": "13D",
               "t": "SEC 申報：ICAHN CARL C 申報持有 輝達（NVDA）逾 5% 股權，不排除介入經營（Schedule 13D）"}

        async def refresh13(watch, now=0):
            return {"alerts": [d13, dict(d13, acc="d2", item="13D/A", t="SEC 申報：X 更新對 輝達（NVDA）的大股東持股申報（Schedule 13D/A）")]}
        SOF.refresh = refresh13
        assert asyncio.run(P.run_once(now=1500)) == 1 and "13D）" in sent[0] and len(dms) == 1, (sent, dms)
        # several newsrooms at once: 3 or more are pushed once per 12 hours, 2 stay on the site; a company gets the impact lines, an event the markets
        co = {"key": "co:NVDA", "kind": "co", "sym": "NVDA", "label": "輝達（NVDA）", "n": 3, "base": 0, "first": 1000, "last": 1900, "mins": 15,
              "tags": ["科技"], "items": [{"t": "輝達執行長辭職", "u": "https://x.test/1", "s": "中央社財經", "ts": 1000, "lang": "zh"}]}
        ev = {"key": "攻擊+伊朗", "kind": "topic", "sym": "", "label": "攻擊＋伊朗", "n": 4, "base": 1, "first": 1100, "last": 1900, "mins": 13,
              "tags": ["地緣", "油價"], "items": [{"t": "Iran fires missiles", "u": "https://x.test/2", "s": "CNBC 國際", "ts": 1100, "lang": "en"}]}
        news["bursts"] = [co, ev, dict(co, key="co:MSFT", label="微軟（MSFT）", n=2)]
        sent.clear(); dms.clear()
        assert asyncio.run(P.run_once(now=2000)) == 2 and len(sent) == 2 and "輝達（NVDA）（3 家）" in sent[0] and "攻擊＋伊朗（4 家）" in sent[1], sent
        assert asyncio.run(P.run_once(now=2000 + 3600)) == 0                                   # same story within 12 h
        assert asyncio.run(P.run_once(now=2000 + 13 * 3600)) == 2                              # still listed 13 h later → said again
        e1, e2 = P.burst_embed(co, ["輝達 今天 **-5.6%**"]), P.burst_embed(ev, ["・相關行情現在：布蘭特原油 +3.0%"])
        assert "前 6 小時幾乎沒有人提" in e1["description"] and "影響估算" in e1["description"] and "[輝達執行長辭職](https://x.test/1)" in e1["description"]
        assert "最多同時只有 1 家" in e2["description"] and "不代表內容已經證實" in e2["description"]
        for w in ("買進", "賣出", "目標價", "低估", "高估"):
            assert w not in e1["description"] + e2["description"]
        assert P.burst_todo([co, dict(co, n=2)], {}, 5000) == [co] and P.burst_todo([co], {"co:NVDA": 5000 - 3600}, 5000) == []
        news["bursts"] = []
        # the night session of Taiwan index futures: one alert per session and level; nothing when it is closed or in day hours
        night = {"sym": "TXFK6-M", "last": 42500.0, "ref": 43839.0, "chg": -1339.0, "pct": -3.05, "status": "", "z": -2.4, "lv": 1, "day": "2026-11-13"}

        async def yes_night(sess, now):
            return night

        async def fake_tx_embed(sess, a):
            return {"title": "🟠 台指期夜盤急跌 lv" + str(a["lv"])}
        P.tx_night, real_txe = yes_night, P.tx_embed
        P.tx_embed = fake_tx_embed
        sent.clear()
        assert asyncio.run(P.run_once(now=60000)) == 1 and sent == ["🟠 台指期夜盤急跌 lv1"], sent
        assert asyncio.run(P.run_once(now=60100)) == 0
        night = dict(night, lv=2)
        assert asyncio.run(P.run_once(now=60200)) == 1 and sent[-1].endswith("lv2")            # it got worse → said once more
        night = dict(night, lv=1)
        assert asyncio.run(P.run_once(now=60300)) == 0                                         # back to the lower level: nothing new
        P.tx_embed = real_txe
        P.tx_night = no_night
        assert set(got_ctx) == {"alerts", "earn", "bursts"}                                    # the private part gets what this round fetched
        # ---- second batch: an unscheduled central-bank release (flagged by /api/news), once, and also to the owner directly
        T = 200000
        news["items"] = [{"t": "Federal Reserve issues FOMC statement", "u": "https://www.federalreserve.gov/x", "s": "聯準會", "ts": T - 300, "kind": "cb"},
                         {"t": "Fed speech", "u": "https://www.federalreserve.gov/y", "s": "聯準會", "ts": T - 300}]
        sent.clear(); dms.clear()
        assert asyncio.run(P.run_once(now=T)) == 1 and sent == ["🔴 央行非例行動作：Federal Reserve issues FOMC statement"] and len(dms) == 1, (sent, dms)
        assert asyncio.run(P.run_once(now=T + 180)) == 0
        ce = P.cb_embed(news["items"][0], ["・相關行情現在：美元指數 +1.0%"])
        assert "不在例行時程裡" in ce["description"] and "請點進去看原文確認" in ce["description"] and ce["url"].endswith("/x")
        # a sudden jump in the yen: once per day
        async def yes_yen(sess, now):
            return {"chg": -2.6, "z": -4.1, "price": 148.2, "day": "2026-11-16"}
        P.yen_jump = yes_yen
        sent.clear()
        assert asyncio.run(P.run_once(now=T + 360)) == 1 and sent[0].startswith("🔴 日圓急升：美元兌日圓 -2.6%（平常一天的 4.1 倍）")
        assert asyncio.run(P.run_once(now=T + 540)) == 0
        ye = P.yen_embed({"chg": -2.6, "z": -4.1, "price": 148.2, "day": "x"}, [])
        assert "干預" in ye["description"] and "不是官方消息" in ye["description"]
        P.yen_jump = no_yen
        # the program was off for 10 hours: one catch-up message with what would otherwise have been skipped as too old
        P.CATCH_GAP = 3600

        async def fake_gap(sess, prev):
            return ["標普 500 -3.0%"]
        P.gap_moves = fake_gap
        back = T + 540 + 10 * 3600
        late = {"acc": "L1", "ts": T + 4000, "sym": "NVDA", "zh": "輝達", "url": "https://www.sec.gov/L1", "item": "5.02",
                "t": "SEC 申報：輝達（NVDA）執行長離職（8-K 第 5.02 項）"}
        fresh = dict(late, acc="F1", ts=back - 600, t="SEC 申報：輝達（NVDA）財務長離職（8-K 第 5.02 項）")

        async def refresh_gap(watch, now=0):
            return {"alerts": [late, fresh]}
        SOF.refresh = refresh_gap
        sent.clear(); dms.clear()
        assert asyncio.run(P.run_once(now=back)) == 2 and sent[0].startswith("🔁 離線補課：10 小時") and "財務長離職" in sent[1], sent
        assert asyncio.run(P.run_once(now=back + 180)) == 0                                    # the old filing is not said again
        cu = P.catchup_embed(T, back, [late], [], ["標普 500 -3.0%"])
        assert "有 1 則重大申報或公告沒有即時通知到你" in cu["description"] and "執行長離職" in cu["description"] and "標普 500 -3.0%" in cu["description"]
        assert "沒有漏掉追蹤公司的重大申報" in P.catchup_embed(T, back, [], [], [])["description"]
        SOF.refresh = refresh13
        # a short stop (under an hour) says nothing
        assert asyncio.run(P.run_once(now=back + 180 + 1800)) == 0
        news["items"] = []
        # A1 system health: a new problem goes to the owner's DM only, at most every 10 minutes
        hp["new"] = [{"key": "bot_down", "urgent": True, "text": "**機器人停了**：已經 45 分鐘沒有心跳。"}]
        sent.clear(); dms.clear()
        t9 = back + 180 + 1800 + 700
        assert asyncio.run(P.run_once(now=t9)) == 1 and dms == ["🩺 系統健康：需要處理"] and not sent, (sent, dms)
        dms.clear()
        assert asyncio.run(P.run_once(now=t9 + 180)) == 0 and not dms                         # checked 3 minutes ago: not yet
        import json as _j
        assert "bot_down" in _j.loads(P.PUSHED.read_text(encoding="utf-8"))["health"]["sent"]
        hp["new"] = []
        P.DISCORD_TOKEN = ""
        assert asyncio.run(P.run_once(now=1600)) == 0
    finally:
        SOF.refresh, P.impact, P.post, P.dm_channel, P.watch_list, P.DISCORD_TOKEN, P.alert_channel, P.sector_alerts = real
        P.news_json, P.tx_night, P.holdings_run, P.market_now, P.yen_jump, P.CATCH_GAP, P.gap_moves, P.health_check = real2

    # the front futures contract from the exchange's own rows: largest volume, monthly contracts only
    from wsb.data import taifex_live as TL
    rows = [{"SymbolID": "TXF-P", "CLastPrice": "", "CRefPrice": "43675.12", "CTotalVolume": ""},
            {"SymbolID": "TXFK6-M", "DispCName": "臺指期116", "CLastPrice": "42,500.00", "CRefPrice": "43839.00", "CTotalVolume": "55924", "Status": "", "CTime": "213000"},
            {"SymbolID": "TXFL6-M", "CLastPrice": "42600.00", "CRefPrice": "43917.00", "CTotalVolume": "1472", "Status": ""},
            {"SymbolID": "MXFK6-M", "CLastPrice": "42500.00", "CRefPrice": "43839.00", "CTotalVolume": "999999", "Status": ""}]
    q = TL.near(rows)
    assert q["sym"] == "TXFK6-M" and abs(q["pct"] - (42500 / 43839 - 1) * 100) < 1e-9 and q["chg"] == -1339.0 and q["status"] == ""
    assert TL.near([]) is None and TL.near(rows[:1]) is None

    # A1: what counts as a problem, in plain words, and when it is said again
    from tools import sys_health as SH
    NOW = 1794700000
    from datetime import datetime as _dt
    line = lambda h, lg, msg, lvl="WARNING": _dt.fromtimestamp(NOW - h * 3600).strftime("%Y-%m-%d %H:%M:%S") + f",123 {lvl} {lg}: {msg}"  # noqa: E731
    lines = [line(h, "wsb.data.fred", f"FRED CPILFESL failed: ClientResponseError: 429, try {h}") for h in range(0, 24)]
    lines += [line(h, "wsb.data.taiwan", "TWSE failed: timeout") for h in range(0, 10)]                 # 10 hours only: not persistent
    lines += [line(h, "asyncio", "Exception in callback _ProactorBasePipeTransport", "ERROR") for h in range(0, 24)]   # noise
    lines += [line(30, "wsb.data.fred", "FRED old failure"), "garbage line"]
    li = SH.log_issues(lines, NOW)
    assert len(li) == 1 and li[0]["logger"] == "wsb.data.fred" and li[0]["hours"] >= 23 and li[0]["n"] == 24, li
    assert SH.what_of("wsb.data.fred")["zh"].startswith("聯準會資料庫") and SH.what_of("x.y")["zh"] == "x.y"
    iso = lambda h: _dt.utcfromtimestamp(NOW - h * 3600).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    run = lambda h, c: {"status": "completed", "conclusion": c, "updated_at": iso(h)}  # noqa: E731
    assert SH.build_issue([run(0.5, "success"), run(1.5, "failure")], NOW) is None
    assert "沒有成功重新產生" in SH.build_issue([run(5, "success")], NOW)
    assert "都失敗" in SH.build_issue([run(0.2, "failure"), run(1, "failure"), run(2, "failure"), run(3, "success")], NOW)
    assert SH.build_issue([run(0.2, "cancelled"), run(1, "failure"), run(2, "failure"), run(3, "success")], NOW) is None   # a cancelled run is not a failure
    assert SH.build_issue([{"status": "in_progress"}], NOW) is None
    ok = SH.collect(NOW, [], 60.0, [run(0.5, "success")], 24, 1)
    assert ok == []
    bad = SH.collect(NOW, lines, 45 * 60.0, [run(6, "success")], 9, 6)
    assert [i["key"].split(":")[0] for i in bad] == ["bot_down", "log", "build", "news", "prices"] and bad[0]["urgent"] and not bad[1]["urgent"]
    assert "總經卡片" in bad[1]["text"] and "只有 9 個來源" in bad[3]["text"]
    assert SH.collect(NOW, [], None, [], None, None) == []                                          # nothing readable → nothing claimed
    sent_h = {"bot_down": NOW - 3600, "build": NOW - 25 * 3600}
    assert [i["key"].split(":")[0] for i in SH.due(bad, sent_h, NOW)] == ["log", "build", "news", "prices"]   # said within a day → not again
    e = SH.embed(bad[:2], 5)
    assert e["title"] == "🩺 系統健康：需要處理" and "目前共 5 件沒解決" in e["description"]
    assert SH.embed(bad[1:2], 1)["title"] == "🩺 系統健康：資料來源連續出錯"
    print("test_sec_push ok")


if __name__ == "__main__":
    main()
