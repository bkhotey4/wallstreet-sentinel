"""政府停擺與債務上限倒數（GovInfo 法律原文、財政部每日報表）、夜間分級（靜音訊息），不連網。
Run: python -m tests.test_fiscal_night"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wsb.data import us_fiscal as U  # noqa: E402
from wsb import quiet as Q  # noqa: E402

CR_TEXT = """<html><body><pre>Sec. 106. Unless otherwise provided for in this Act ... shall be available until whichever of the following
first occurs: (1) The enactment into law of an appropriation ... (2) The enactment into law of the applicable appropriations Act
for fiscal year 2027 without any provision for such project or activity. (3) &lt;&lt;NOTE: Expiration date.&gt;&gt; December 11, 2026.
Sec. 107. Expenditures made pursuant to this Act shall be charged ... October 1, 2026 ... September 30, 2027</pre></body></html>"""
FURTHER = """<pre>SEC. 101. The Continuing Appropriations and Extensions Act, 2027 is amended by striking the date specified in
section 106(3) and inserting ... Section 106(3) of division A is amended by striking "December 11, 2026" and inserting
"January 30, 2027".</pre>"""


def test_laws_and_deadline():
    assert U.fiscal_year(date(2026, 11, 15)) == 2027 and U.fiscal_year(date(2026, 9, 30)) == 2026
    assert U.law_kind("Continuing Appropriations and Extensions Act, 2027", 2027) == "cr"
    assert U.law_kind("Further Continuing Appropriations Act, 2027", 2027) == "cr"
    assert U.law_kind("Consolidated Appropriations Act, 2027", 2027) == "full"
    assert U.law_kind("Full-Year Continuing Appropriations Act, 2027", 2027) == "full"
    assert U.law_kind("Continuing Appropriations and Extensions Act, 2027", 2026) is None          # another fiscal year
    assert U.law_kind("National Emergency Medical Services Memorial Extension Act", 2027) is None
    assert U.cr_end(CR_TEXT) == "2026-12-11"
    assert U.cr_end(FURTHER) == "2027-01-30"                                       # an amendment of 106(3) moves the date
    assert U.cr_end("<pre>no dates here</pre>") is None
    t = date(2026, 11, 15)
    cr = {"id": "a", "date": "2026-09-02", "title": "Continuing Appropriations and Extensions Act, 2027", "kind": "cr", "end": "2026-12-11"}
    f = U.funding_view([cr], t)
    assert (f["state"], f["end"], f["days"]) == ("cr", "2026-12-11", 26)
    f = U.funding_view([cr], date(2026, 12, 12))
    assert f["state"] == "lapsed" and f["days"] == -1
    f = U.funding_view([cr, dict(cr, id="b", date="2026-12-10", end="2027-01-30")], date(2026, 12, 12))
    assert (f["state"], f["end"]) == ("cr", "2027-01-30")                          # the newest CR wins
    f = U.funding_view([cr, {"id": "c", "date": "2026-12-05", "title": "Consolidated Appropriations Act, 2027", "kind": "full"}], t)
    assert (f["state"], f["end"]) == ("funded", "2027-09-30")
    assert U.funding_view([], t)["state"] == "unknown"


def _rows(day, public, intra, limit, notsub=(474.0, 194581.0, 3591.0)):
    r = [{"record_date": day, "debt_catg": "Debt Held by the Public", "close_today_bal": str(public)},
         {"record_date": day, "debt_catg": "Intragovernmental Holdings", "close_today_bal": str(intra)},
         {"record_date": day, "debt_catg": "Other Debt Subject to Limit", "close_today_bal": "0"},
         {"record_date": day, "debt_catg": "Statutory Debt Limit", "close_today_bal": str(limit)}]
    return r + [{"record_date": day, "debt_catg": "Debt Not Subject to Limit", "close_today_bal": str(v)} for v in notsub]


def test_debt_limit():
    data = _rows("2026-11-12", 32824386, 7784121, 41103996) + _rows("2026-08-14", 32224386, 7708121, 41103996) \
        + _rows("2025-07-03", 30000000, 7000000, 36103996) + [{"record_date": "2026-11-12", "debt_catg": "x", "close_today_bal": "null"}]
    rows = U.debt_rows(data)
    assert abs(rows["2026-11-12"]["subject"] - 40409861) < 1 and rows["2026-11-12"]["limit"] == 41103996
    v = U.debt_view(rows)
    assert abs(v["room"] - 694135) < 1 and v["asof"] == "2026-11-12" and v["span"] == 90
    assert abs(v["per_day"] - (676000 / 90)) < 1e-6 and 2.9 < v["months"] < 3.2
    assert v["raised"] == "2026-08-14"                                             # the limit changed between the two dates
    falling = U.debt_view(U.debt_rows(_rows("2026-11-12", 32000000, 7700000, 41103996) + _rows("2026-08-14", 32500000, 7700000, 41103996)))
    assert "months" not in falling and falling["per_day"] < 0                      # debt going down (tax season): no run-out date
    assert U.debt_view({}) == {}


def test_alert_stages():
    def view(days=None, state="cr", months=None):
        f = {"state": state, "end": "2026-12-11", "days": days} if days is not None else {}
        return {"funding": f, "debt": {"months": months, "limit": 41103996.0} if months is not None else {}}
    assert U.alerts(view(26)) == []
    assert [a["key"] for a in U.alerts(view(14))] == ["fiscal:cr:2026-12-11:14"]
    assert U.alerts(view(5))[0]["key"].endswith(":7") and U.alerts(view(5))[0]["lv"] == 1
    assert U.alerts(view(2))[0]["key"].endswith(":3") and U.alerts(view(2))[0]["lv"] == 2
    assert U.alerts(view(0))[0]["key"].endswith(":0")
    assert U.alerts(view(-1, "lapsed"))[0]["key"] == "fiscal:cr:2026-12-11:-1"
    assert U.alerts(view(5, "funded")) == []
    assert U.alerts(view(months=7.0)) == []
    assert [a["key"] for a in U.alerts(view(months=3.1))] == ["fiscal:debt:41103996:6"]
    assert U.alerts(view(months=2.0))[0]["key"].endswith(":3") and U.alerts(view(months=0.5))[0]["lv"] == 2


def test_fiscal_card_and_embed():
    from tools import site_fiscal as SF
    from tools import sec_push as P
    f = U.funding_view([{"id": "a", "date": "2026-09-02", "title": "CR 2027", "kind": "cr", "end": "2026-12-11"}], date(2026, 11, 15))
    lead = SF.funding_lead(f)
    assert "🟡" in lead and "2026 年 12 月 11 日到期，還有 26 天" in lead               # 30 days or less: yellow
    assert "🟢" in SF.funding_lead(dict(f, days=40)) and "🔴" in SF.funding_lead(dict(f, days=5))
    assert "可能正在停擺" in SF.funding_lead(dict(f, state="lapsed", days=-1))
    dv = U.debt_view(U.debt_rows(_rows("2026-11-12", 32824386, 7784121, 41103996) + _rows("2026-08-14", 32224386, 7708121, 41103996)))
    d = SF.debt_lead(dv)
    assert "41.10 兆美元" in d and "還剩約 6,941 億美元" in d and "大約 3.0 個月會用完" in d and "非常措施" in d and d.startswith("🟡")
    v = {"funding": dict(f, days=7), "debt": dv}
    e = P.fiscal_embed({"kind": "cr", "lv": 1, "days": 7, "end": "2026-12-11", "key": "k"}, v, ["・相關行情現在：標普 500 +0.1%"])
    assert e["title"] == "🟠 美國政府撥款還有 7 天到期" and "<b>" not in e["description"] and "數據空窗" in e["description"]
    e = P.fiscal_embed({"kind": "debt", "lv": 2, "months": 0.8, "key": "k"}, v, [])
    assert e["title"].startswith("🔴 美國債務上限：照最近速度約 0.8 個月用完") and "非常措施" in e["description"]
    for w in ("買進", "賣出", "目標價", "低估", "高估"):
        assert w not in e["description"] and w not in d


def test_night_tiering():
    tpe = timezone(timedelta(hours=8))
    at = lambda h, m=0: datetime(2026, 11, 16, h, m, tzinfo=tpe).timestamp()  # noqa: E731
    win = ("23:30", "07:00")
    assert Q.is_night(at(23, 45), win) and Q.is_night(at(3), win) and Q.is_night(at(6, 59), win)
    assert not Q.is_night(at(7), win) and not Q.is_night(at(12), win) and not Q.is_night(at(23, 29), win)
    assert Q.is_night(at(13), ("12:00", "14:00")) and not Q.is_night(at(3), ("07:00", "07:00"))   # same start and end: off
    assert Q.loud("🔴 SEC 申報：輝達執行長離職") and Q.loud("🚨 緊急風險警報：比特幣 -6%") and Q.loud("⏱ 延遲送達 🚨 CRITICAL 異常")
    assert not Q.loud("🟠 族群急跌：記憶體 -4%") and not Q.loud("⚠️ 網站警示：崩跌機率升高") and not Q.loud("")
    Q.LOG = pathlib.Path(tempfile.mkdtemp()) / "n.json"
    Q.note("🟠 a", "push", ts=1000.0)
    Q.note("⚠️ b", "bot", ts=2000.0)
    assert [r["t"] for r in Q.since(1500.0)] == ["⚠️ b"] and len(Q.since(0)) == 2


def test_push_is_silent_at_night_unless_red():
    from tools import sec_push as P

    class R:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    class S:
        def __init__(self):
            self.bodies = []

        def post(self, url, **kw):
            self.bodies.append(kw["json"])
            return R()
    real = (Q.is_night, P.CLOUD, Q.LOG)
    try:
        Q.LOG = pathlib.Path(tempfile.mkdtemp()) / "n.json"
        P.CLOUD = False
        Q.is_night = lambda ts=None, win=None: True
        s = S()
        asyncio.run(P.post(s, "1", {"title": "🟠 族群急跌：記憶體 -4%"}))
        asyncio.run(P.post(s, "1", {"title": "🔴 台指期夜盤急跌：-3.0%"}))
        assert s.bodies[0]["flags"] == 4096 and "flags" not in s.bodies[1]                 # yellow: silent; red: rings
        assert [r["t"] for r in Q.since(0)] == ["🟠 族群急跌：記憶體 -4%"]                    # remembered for the morning summary
        Q.is_night = lambda ts=None, win=None: False
        asyncio.run(P.post(s, "1", {"title": "🟠 族群急跌：記憶體 -4%"}))
        assert "flags" not in s.bodies[2]                                                    # daytime: everything rings
        Q.is_night = lambda ts=None, win=None: True
        asyncio.run(P.post(s, "1", {"title": "📊 財報出爐：輝達（NVDA）", "loud": True}))
        assert "flags" not in s.bodies[3] and "loud" not in s.bodies[3]["embeds"][0]          # the user's own earnings: rings at night
        assert P.embed_of({"t": "SEC 申報：X 董事任命", "url": "u", "ts": 0, "item": "5.02"}, [])["title"].startswith("🟠")
    finally:
        Q.is_night, P.CLOUD, Q.LOG = real


def test_bot_night_kw():
    import types
    from wsb.bot import present as PR
    real = (Q.is_night, Q.LOG)
    try:
        Q.LOG = pathlib.Path(tempfile.mkdtemp()) / "n.json"
        Q.is_night = lambda ts=None, win=None: True
        dest = types.SimpleNamespace()
        assert PR.night_kw(dest, "⚠️ 市場警報：金絲雀紅燈") == {"silent": True}
        assert PR.night_kw(dest, "🚨 緊急風險警報：比特幣 -6%") == {}
        Q.is_night = lambda ts=None, win=None: False
        assert PR.night_kw(dest, "⚠️ 市場警報") == {}
    finally:
        Q.is_night, Q.LOG = real


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
