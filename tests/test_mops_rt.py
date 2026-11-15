"""台股重大訊息即時版：官方 RSS 的解析、關鍵字分級、追蹤名單與去重、機器人整批檔略過已送的、通知延遲的自我檢查（不連網）。
Run: python -m tests.test_mops_rt"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wsb.data import mops_rt as MR  # noqa: E402

RSS = """<?xml version='1.0' encoding='big5'?>
<rss version='2.0'><channel><title>公開資訊觀測站重大訊息</title>
<item><title>(2330)台積電-重大訊息</title>
 <link> <![CDATA[https://mopsov.twse.com.tw/mops/web/t05st02?step=1&TYPEK=sii&h01=2330&h02=20261116&h03=134500&pgname=t05st02]]></link>
 <description> <![CDATA[澄清今日媒體報導
本公司說明如下]]></description>
 <pubDate>Mon, 16 Nov 2026 13:45:00 +0800</pubDate></item>
<item><title>(2330)台積電-重大訊息</title>
 <link> <![CDATA[https://mopsov.twse.com.tw/mops/web/t05st02?step=1&TYPEK=sii&h11=2330&h12=20261116&h13=134700]]></link>
 <description> <![CDATA[公告本公司董事會決議股利分派]]></description>
 <pubDate>bad date</pubDate></item>
<item><title>(3324)雙鴻-重大訊息</title>
 <link> <![CDATA[https://mopsov.twse.com.tw/mops/web/t05st02?TYPEK=otc&h21=3324&h22=20261116&h23=90000]]></link>
 <description> <![CDATA[公告本公司受邀參加法人說明會]]></description>
 <pubDate>Mon, 16 Nov 2026 09:00:00 +0800</pubDate></item>
<item><title>壞掉的一則</title><description>x</description></item>
</channel></rss>""".encode("cp950")


def test_parse_and_classify():
    it = MR.parse(RSS)
    assert [x["code"] for x in it] == ["2330", "2330", "3324"]                      # newest first; the broken item is dropped
    a, b, c = it
    assert a["when"] == "11/16 13:47" and a["kind"] == "股利與庫藏股" and a["lv"] == 1  # the time came from the link (h13) when pubDate is unreadable
    assert b["when"] == "11/16 13:45" and b["kind"] == "澄清媒體報導" and b["lv"] == 2 and b["market"] == "上市"
    assert b["subject"] == "澄清今日媒體報導 本公司說明如下" and b["url"].startswith("https://mopsov.twse.com.tw/")
    assert c["market"] == "上櫃" and c["kind"] == "法說會" and c["lv"] == 0
    assert MR.parse(b"<html>FOR SECURITY REASONS</html>") == []
    for s, kind, lv in (("本公司廠區發生火災說明", "營運事故", 2), ("公告本公司財務主管異動", "高層異動", 2), ("本公司董事長辭任", "高層異動", 2),
                        ("公告本公司收到法院民事訴訟起訴狀", "司法與裁罰", 2), ("更正本公司115年第3季財務報告", "更正財報", 2),
                        ("公告本公司存款不足退票", "財務危機", 2), ("公告本公司10月份自結損益", "財報與獲利", 1),
                        ("公告本公司辦理現金增資", "籌資", 1), ("公告本公司取得機器設備", "資產買賣", 1),
                        ("公告本公司股東常會召開日期", "例行公告", 0), ("代子公司公告事項", "其他", 1)):
        got = MR.classify(s)
        assert (got["kind"], got["lv"]) == (kind, lv), (s, got)
    # the same announcement gives the same key whichever feed it came from: line breaks and spaces do not matter
    assert MR.key_of("2330", "澄清今日媒體報導\r\n本公司說明如下") == b["key"] != MR.key_of("2317", "澄清今日媒體報導 本公司說明如下")


def test_fresh_group_and_memory():
    it = MR.parse(RSS)
    now = it[0]["ts"] + 600
    codes = {"2330": "台積電", "9999": "沒公告的公司"}
    fr = MR.fresh(it, codes, {}, now)
    assert [x["kind"] for x in fr] == ["澄清媒體報導", "股利與庫藏股"] and fr[0]["zh"] == "台積電"   # the serious one first; 雙鴻 is not tracked
    assert MR.fresh(it, codes, {fr[0]["key"]: now}, now) == fr[1:]                # already sent
    assert MR.fresh(it, codes, {}, now + 7 * 3600) == []                          # older than 6 hours: left to the catch-up
    assert MR.fresh(it, codes, {}, it[0]["ts"] - 5000) == []                      # a clock that is behind the feed sends nothing
    g = MR.group(MR.fresh(it, {"2330": "台積電", "3324": "雙鴻"}, {}, now, max_age=12 * 3600))
    assert [len(x) for x in g] == [2, 1] and g[0][0]["code"] == "2330"            # one message per company, the most serious company first
    MR.FILE = pathlib.Path(tempfile.mkdtemp()) / "m.json"
    assert MR.load() == {}
    MR.save({"a": now, "old": now - 5 * 86400}, now)
    assert MR.load() == {"a": now}                                                # kept 4 days


def test_bot_batch_skips_what_was_sent():
    from wsb.data import events as EV
    MR.FILE = pathlib.Path(tempfile.mkdtemp()) / "m.json"
    rows = EV.parse_mops([{"公司代號": "2330", "公司名稱": "台積電", "發言日期": "1151116", "發言時間": "134500", "主旨 ": "澄清今日媒體報導\r\n本公司說明如下", "符合條款": "第51款"},
                          {"公司代號": "2317", "公司名稱": "鴻海", "發言日期": "1151116", "發言時間": "150000", "主旨 ": "公告本公司取得設備", "符合條款": "第20款"}], "上市")
    assert len(EV.drop_sent(rows)) == 2                                           # nothing sent in real time: the batch is untouched
    MR.save({MR.key_of("2330", "澄清今日媒體報導 本公司說明如下"): rows[0]["ts"]}, rows[0]["ts"])
    assert [m["code"] for m in EV.drop_sent(rows)] == ["2317"]                    # the one already sent from the RSS is not repeated


def test_lag_check():
    from tools import sys_health as SH
    now = 1_800_000_000.0
    slow = [{"k": "台股重大訊息", "ev": now - 86400 - 12 * 3600, "at": now - 86400 + i} for i in range(6)]
    fast = [{"k": "sec", "ev": now - 3600 - 300, "at": now - 3600} for _ in range(8)]
    few = [{"k": "cb", "ev": now - 9 * 3600, "at": now - 3600}] * 3
    old = [{"k": "mops", "ev": now - 9 * 86400, "at": now - 8 * 86400}] * 9
    out = SH.lag_issues(slow + fast + few + old + [{"k": "x"}], now)
    assert [i["key"] for i in out] == ["lag:台股重大訊息"] and out[0]["urgent"]
    assert "中位數是 12.0 小時" in out[0]["text"] and "6 則" in out[0]["text"] and "不算即時" in out[0]["text"]
    assert SH.lag_issues([{"k": "mops", "ev": now - 4000, "at": now - 100}] * 5, now)[0]["text"].count("65 分鐘") == 1


def test_post_retries_and_text_line():
    from tools import sec_push as P
    e = {"title": "🔴 台股重大訊息：**台積電**（2330）[澄清](https://x.y)", "description": "d"}
    assert P.plain(e) == "🔴 台股重大訊息：台積電（2330）澄清"

    class R:
        def __init__(self, status, js=None):
            self.status, self._js = status, js or {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def json(self):
            return self._js

        async def text(self):
            return "body"

    class S:
        def __init__(self, seq):
            self.seq, self.calls = list(seq), []

        def post(self, url, **kw):
            self.calls.append(kw["json"])
            r = self.seq.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

    async def no_sleep(_):
        return None
    real = P.asyncio.sleep
    P.asyncio.sleep = no_sleep
    try:
        import aiohttp
        s = S([R(429, {"retry_after": 0.2}), R(502), R(200)])
        assert asyncio.run(P.post(s, "1", e)) is True and len(s.calls) == 3
        assert s.calls[0]["content"] == "🔴 台股重大訊息：台積電（2330）澄清" and s.calls[0]["embeds"] == [e]   # the phone shows this line
        s = S([R(403)])
        assert asyncio.run(P.post(s, "1", e)) is False and len(s.calls) == 1      # a refusal is not retried
        s = S([aiohttp.ClientConnectionError(), asyncio.TimeoutError(), R(500)])
        assert asyncio.run(P.post(s, "1", e)) is False and len(s.calls) == 3      # still failing: left for the next run
        assert asyncio.run(P.post(S([]), "", e)) is False                         # no channel: nothing is sent
    finally:
        P.asyncio.sleep = real
    lag = pathlib.Path(tempfile.mkdtemp()) / "lag.json"
    real_lag, P.LAG = P.LAG, lag
    try:
        P.note_lag("mops", 100.0, 400.0)
        P.note_lag("sec", 200.0, 500.0)
        assert [r["k"] for r in json.loads(lag.read_text(encoding="utf-8"))] == ["mops", "sec"]
    finally:
        P.LAG = real_lag


def test_bot_push_headline():
    import types
    from wsb.bot import present as PR
    em = types.SimpleNamespace(title="🚨 緊急風險警報", fields=[types.SimpleNamespace(name="🚨 CRITICAL 異常波動：比特幣 -6.3%"),
                                                              types.SimpleNamespace(name="⚠️ WARNING 金絲雀紅燈")])
    assert PR.headline(lambda: em) == "🚨 緊急風險警報：🚨 CRITICAL 異常波動：比特幣 -6.3%；⚠️ WARNING 金絲雀紅燈"
    assert PR.headline(lambda: [types.SimpleNamespace(title="早安簡報", fields=[])]) == "早安簡報"
    assert PR.headline(lambda: 1 / 0) is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
