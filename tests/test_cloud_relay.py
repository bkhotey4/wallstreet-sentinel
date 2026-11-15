"""雲端備援：家裡電腦與雲端用 Discord 上的訊息對帳（標題連結尾端的編號）、雲端先等家裡電腦、第一次啟動只記不送、
電腦沒有動靜時說一聲、雲端不碰持股與系統健康（不連網、不真的送）。
Run: python -m tests.test_cloud_relay"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.sec_push as P  # noqa: E402

T0 = 1_900_000_000.0


def test_tag_and_keys():
    e = {"title": "🔴 SEC 申報", "url": "https://www.sec.gov/a1", "description": "d"}
    t = P.tag(e, "0001045810-26-000123")
    assert t["url"] == "https://www.sec.gov/a1#k=0001045810-26-000123" and e["url"] == "https://www.sec.gov/a1"   # the original is untouched
    assert P.keys_of({"embeds": [t]}) == ["0001045810-26-000123"]
    many = ["mops:2330|ab12", "burst:聯準會,降息", "site:odds:20:2.0:1", "cb:https://www.boj.or.jp/x?a=1&b=2#top"]
    t = P.tag({"title": "x"}, many)
    assert t["url"].startswith(P.SITE + "#k=") and " " not in t["url"] and P.keys_of({"embeds": [t]}) == many
    assert P.keys_of({"embeds": [P.tag({"title": "x", "url": "https://a.b/c#frag"}, "k1")]}) == ["k1"]
    assert P.keys_of({"embeds": [{"url": "https://a.b/c"}, {}]}) == [] and P.keys_of({}) == []
    long = P.tag({"title": "x"}, [f"mops:{i:04d}|" + "z" * 60 for i in range(60)])
    got = P.keys_of({"embeds": [long]})
    assert len(long["url"]) <= 2000 and 20 < len(got) < 60 and all(len(k) == 70 for k in got)   # too many: whole keys are dropped, never half a key


class _R:
    def __init__(self, status, js=None):
        self.status, self._js = status, js

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def json(self):
        return self._js

    async def text(self):
        return "body"


class _S:
    def __init__(self, seq):
        self.seq, self.calls = list(seq), []

    def get(self, url, **kw):
        self.calls.append(("get", kw.get("params")))
        return self.seq.pop(0)

    def post(self, url, **kw):
        self.calls.append(("post", kw["json"]))
        return self.seq.pop(0)


def _msg(i, keys=None):
    mid = str((int((T0 - i * 60) * 1000) - 1420070400000) << 22)
    return {"id": mid, "embeds": [P.tag({"title": "t"}, keys)] if keys else [{"title": "slide"}]}


def test_ledger_reads_two_pages():
    page1 = [_msg(i, ["a%d" % i] if i % 2 else None) for i in range(100)]
    page2 = [_msg(100 + i, ["b%d" % i, "shared"]) for i in range(3)]
    s = _S([_R(200, page1), _R(200, page2)])
    got = asyncio.run(P.ledger(s, "1"))
    assert len(got) == 50 + 3 + 1 and abs(got["a1"] - (T0 - 60)) < 1 and "b2" in got
    assert s.calls[0][1] == {"limit": "100"} and s.calls[1][1]["before"] == page1[-1]["id"]
    assert abs(got["shared"] - (T0 - 100 * 60)) < 1                              # the newest message that carries a key wins
    assert asyncio.run(P.ledger(_S([_R(403)]), "1")) is None                     # unreadable is not the same as empty
    assert asyncio.run(P.ledger(_S([_R(200, page1), _R(500)]), "1")).keys() >= {"a1"}   # the first page alone is still useful
    assert asyncio.run(P.ledger(_S([]), "")) is None


def test_post_carries_key_and_cloud_mark():
    async def no_sleep(_):
        return None
    real, P.asyncio.sleep = P.asyncio.sleep, no_sleep
    real_cloud = P.CLOUD
    try:
        e = {"title": "🟠 族群急跌", "footer": {"text": "Yahoo · 不構成投資建議"}}
        s = _S([_R(200)])
        P.CLOUD = False
        assert asyncio.run(P.post(s, "1", e, "sector:SOXX:2026-11-16:2")) is True
        sent = s.calls[0][1]["embeds"][0]
        assert P.keys_of({"embeds": [sent]}) == ["sector:SOXX:2026-11-16:2"] and sent["footer"]["text"] == "Yahoo · 不構成投資建議"
        assert s.calls[0][1]["content"] == "🟠 族群急跌" and "url" not in e           # the caller's embed is not changed
        s = _S([_R(200)])
        P.CLOUD = True
        assert asyncio.run(P.post(s, "1", e, ["a", "b"])) is True
        sent = s.calls[0][1]["embeds"][0]
        assert sent["footer"]["text"].endswith("☁️ 雲端備援代送") and P.keys_of({"embeds": [sent]}) == ["a", "b"]
    finally:
        P.asyncio.sleep, P.CLOUD = real, real_cloud


def test_grace_and_quiet_notice():
    assert P.grace("sec", 5) == 600 and P.grace("stock", 5) == 900 and P.grace("cr", None) == 2700
    assert P.grace("sec", 45) == P.grace("cr", 300) == 180                       # the PC looks off: wait 3 minutes only
    q = {}
    assert not P.quiet_due(q, None, T0) and not P.quiet_due(q, 50, T0)           # unknown, or not long enough yet
    assert P.quiet_due(q, 61, T0)
    q.update(ts=T0, up=False)
    assert not P.quiet_due(q, 300, T0 + 4 * 3600)                                # same outage: said once
    assert P.quiet_due(q, 9999, T0 + 25 * 3600)                                  # still off a day later: once more
    assert not P.quiet_due(q, 10, T0 + 5 * 3600) and q["up"]                     # it came back
    assert P.quiet_due(q, 70, T0 + 5 * 3600 + 60)                                # a new outage after it came back
    q2 = {"ts": T0, "up": True}
    assert not P.quiet_due(q2, 70, T0 + 3600) and P.quiet_due(q2, 70, T0 + 3 * 3600)   # a new outage, but not within 3 hours of the last notice
    d = P.quiet_embed(75)["description"]
    assert "75 分鐘" in d and "持股" in d and "雲端沒有" in d and "2.0 小時" in P.quiet_embed(120)["description"]
    assert "很久" in P.quiet_embed(9999)["description"]
    for w in ("買進", "賣出", "目標價"):
        assert w not in d


def _run_env():
    """Everything run_once touches, replaced by fakes; returns (state, restore)."""
    from wsb.data import mops_rt as MR
    from wsb.data import sec_officers as SOF
    tmp = pathlib.Path(tempfile.mkdtemp())
    st = {"alerts": [], "sent": [], "led": {}, "led_fail": False, "mops": {"groups": [], "sent": {}, "priv": set()}, "site": {},
          "country": {}, "bursts": [], "health": 0, "hold": 0, "led_calls": 0}
    names = ("impact post dm_channel watch_list alert_channel sector_alerts stock_alerts news_json tx_night holdings_run market_now "
             "yen_jump gap_moves health_check country_json site_alerts_json mops_new tw_impact ledger PUSHED LAG DISCORD_TOKEN CLOUD CATCH_GAP FISCAL_EVERY").split()
    real = {n: getattr(P, n) for n in names}
    real_refresh, real_mr = SOF.refresh, MR.FILE
    real_env = os.environ.get("WSB_BOT_AGE_MIN")

    async def refresh(watch, now=0):
        return {"alerts": list(st["alerts"])}

    async def impact(sess, sym, zh):
        return [zh]

    async def post(sess, ch, emb, key=None):
        st["sent"].append((emb["title"], key))
        return True

    async def dm(sess):
        return "dm"

    async def none(sess, now):
        return None

    async def empty(sess, now):
        return []

    async def news(sess):
        return {"bursts": st["bursts"]}

    async def hold(sess, now, ctx=None):
        st["hold"] += 1
        return 0

    async def mkt(sess, tags, now):
        return ["・行情"]

    async def gap(sess, prev):
        return []

    async def health(now, nj, hsent):
        st["health"] += 1
        return [], 0

    async def country(sess):
        return st["country"]

    async def site(sess, now):
        return st["site"]

    async def mops(sess, now):
        return st["mops"]

    async def twi(sess, code, zh, now):
        return []

    async def led(sess, channel, pages=2):
        st["led_calls"] += 1
        return None if st["led_fail"] else dict(st["led"])

    P.impact, P.post, P.dm_channel, P.watch_list, P.alert_channel = impact, post, dm, (lambda: {}), (lambda: "")
    P.sector_alerts, P.stock_alerts, P.news_json, P.tx_night, P.holdings_run, P.market_now = empty, empty, news, none, hold, mkt
    P.yen_jump, P.gap_moves, P.health_check, P.country_json, P.site_alerts_json, P.mops_new, P.tw_impact, P.ledger = (
        none, gap, health, country, site, mops, twi, led)
    P.PUSHED, P.LAG, P.DISCORD_TOKEN, P.CATCH_GAP = tmp / "p.json", tmp / "lag.json", "t", 10 ** 12
    P.FISCAL_EVERY = 10 ** 12                                   # the fiscal countdown has its own test (tests/test_fiscal_night.py)
    SOF.refresh, MR.FILE = refresh, tmp / "mops.json"

    def restore():
        for n, v in real.items():
            setattr(P, n, v)
        SOF.refresh, MR.FILE = real_refresh, real_mr
        if real_env is None:
            os.environ.pop("WSB_BOT_AGE_MIN", None)
        else:
            os.environ["WSB_BOT_AGE_MIN"] = real_env
    return st, restore


def _sec(acc, ts):
    return {"acc": acc, "ts": ts, "sym": "NVDA", "zh": "輝達", "url": "https://www.sec.gov/" + acc, "item": "5.02",
            "t": f"SEC 申報：輝達（NVDA）執行長離職 {acc}"}


def test_home_pc_skips_what_the_cloud_sent():
    st, restore = _run_env()
    try:
        P.CLOUD = False
        st["alerts"] = [_sec("s1", T0 - 300), _sec("s2", T0 - 200)]
        st["led"] = {"s1": T0 - 100}                                             # the cloud already sent s1 while this PC was asleep
        assert asyncio.run(P.run_once(now=T0)) == 1
        assert [k for _, k in st["sent"]] == ["s2"] and st["led_calls"] == 1     # s1 is not sent again; the channel is read once
        mem = json.loads(P.PUSHED.read_text(encoding="utf-8"))
        assert {"s1", "s2"} <= set(mem["acc"])                                   # both are remembered as done
        st["sent"].clear()
        assert asyncio.run(P.run_once(now=T0 + 180)) == 0 and st["led_calls"] == 1   # nothing to send: the channel is not read at all
        # Discord cannot be read: the home PC sends as it always did
        st["alerts"].append(_sec("s3", T0 + 200))
        st["led_fail"] = True
        assert asyncio.run(P.run_once(now=T0 + 360)) == 1 and st["sent"][-1][1] == "s3"
        assert st["health"] >= 1 and st["hold"] >= 1                             # health check and holdings still run at home
    finally:
        restore()


def test_cloud_waits_then_sends_and_never_touches_holdings():
    st, restore = _run_env()
    try:
        P.CLOUD = True
        os.environ["WSB_BOT_AGE_MIN"] = "5"                                      # the home bot is alive
        st["alerts"] = [_sec("old", T0 - 900)]
        st["site"] = {"ts": T0, "items": [{"key": "odds:1", "lv": "alert", "zh": "甲"}]}
        assert asyncio.run(P.run_once(now=T0)) == 0 and st["sent"] == []         # the very first run only remembers
        assert "old" in json.loads(P.PUSHED.read_text(encoding="utf-8"))["acc"] and st["led_calls"] == 0
        # a new filing: seen, not sent — the home PC gets 10 minutes
        st["alerts"].append(_sec("n1", T0 + 100))
        assert asyncio.run(P.run_once(now=T0 + 150)) == 0 and st["led_calls"] == 1
        assert asyncio.run(P.run_once(now=T0 + 450)) == 0
        # the home PC sent it meanwhile: the cloud drops it
        st["led"] = {"n1": T0 + 500}
        assert asyncio.run(P.run_once(now=T0 + 760)) == 0 and st["sent"] == []
        mem = json.loads(P.PUSHED.read_text(encoding="utf-8"))
        assert "n1" in mem["acc"] and "n1" not in mem["pend"]
        # the next one the home PC never sends: after 10 minutes the cloud does, with its key
        st["alerts"].append(_sec("n2", T0 + 800))
        assert asyncio.run(P.run_once(now=T0 + 900)) == 0
        assert asyncio.run(P.run_once(now=T0 + 1400)) == 0                       # 500 s: still waiting
        assert asyncio.run(P.run_once(now=T0 + 1510)) == 1 and st["sent"][-1][1] == "n2"
        assert asyncio.run(P.run_once(now=T0 + 1700)) == 0                       # once
        # Discord unreadable: the cloud never sends blind
        st["alerts"].append(_sec("n3", T0 + 1800))
        st["led_fail"] = True
        assert asyncio.run(P.run_once(now=T0 + 1900)) == 0 and asyncio.run(P.run_once(now=T0 + 2600)) == 0
        st["led_fail"] = False
        assert asyncio.run(P.run_once(now=T0 + 2700)) == 0                       # first real look at n3 starts its 10 minutes
        assert asyncio.run(P.run_once(now=T0 + 3310)) == 1 and st["sent"][-1][1] == "n3"
        # Taiwan: a public company waits like the rest; a holdings-only company is never sent from the cloud
        t = T0 + 4000
        g1 = [{"code": "2330", "zh": "台積電", "name": "台積電", "market": "上市", "subject": "澄清媒體報導", "ts": t - 60, "when": "11/16 13:45",
               "url": "https://mopsov.twse.com.tw/x", "key": "2330|a", "lv": 2, "kind": "澄清媒體報導"}]
        g2 = [dict(g1[0], code="9999", zh="某持股", key="9999|c")]
        st["mops"].update(groups=[g1, g2], sent={}, priv={"9999"})
        st["sent"].clear()
        assert asyncio.run(P.run_once(now=t)) == 0
        assert asyncio.run(P.run_once(now=t + 610)) == 1 and st["sent"] == [("🔴 台股重大訊息：台積電（2330）澄清媒體報導", ["mops:2330|a"])]
        st["mops"].update(groups=[], sent={}, priv=set())
        # the site's alerts: a kind the bot has no message for waits 15 minutes; the bot's own kinds are left to the bot while it is alive
        st["site"] = {"ts": t + 1300, "items": [{"key": "odds:1", "lv": "alert", "zh": "甲"}, {"key": "rule:vix35:1", "lv": "alert", "zh": "VIX 規則觸發"},
                                                {"key": "ssi:3:w", "lv": "alert", "zh": "壓力指數升級"}]}
        st["sent"].clear()
        assert asyncio.run(P.run_once(now=t + 1300)) == 0
        assert asyncio.run(P.run_once(now=t + 1300 + 600)) == 0
        assert asyncio.run(P.run_once(now=t + 1300 + 910)) == 1 and st["sent"] == [("⚠️ 網站警示：VIX 規則觸發", ["site:rule:vix35:1"])]
        assert st["health"] == 0 and st["hold"] == 0                             # the cloud has no holdings and does no health check
        # the home PC goes quiet: one notice, the wait drops to 3 minutes, and the bot's own kinds are passed on too
        os.environ["WSB_BOT_AGE_MIN"] = "70"
        t2 = t + 4000
        st["site"] = {"ts": t2, "items": st["site"]["items"] + [{"key": "danger:9", "lv": "alert", "zh": "盤中危險"}]}
        st["alerts"].append(_sec("q1", t2 - 30))
        st["sent"].clear()
        assert asyncio.run(P.run_once(now=t2)) == 1 and st["sent"][0][0].startswith("☁️ 家裡電腦沒有動靜")
        assert asyncio.run(P.run_once(now=t2 + 100)) == 0
        assert asyncio.run(P.run_once(now=t2 + 190)) == 2                        # 3 minutes later: the filing and the site alert
        assert [k for _, k in st["sent"][1:]] == ["q1", ["site:danger:9"]]
        assert asyncio.run(P.run_once(now=t2 + 400)) == 0                        # the notice is not repeated
    finally:
        restore()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
