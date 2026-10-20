"""Bot-driven site rebuilds (workflow_dispatch): decision rules + request shape, no network.
Run: python -m tests.test_site_trigger"""
from __future__ import annotations

import asyncio
import os
import tempfile
import time
from datetime import datetime, timedelta, timezone

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_trig_"))

from wsb import site_trigger as ST  # noqa: E402
from wsb import store  # noqa: E402
from wsb.data import http  # noqa: E402


class FakeResp:
    def __init__(self, status, text=""):
        self.status, self._t = status, text

    async def text(self):
        return self._t

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class FakeSession:
    def __init__(self, status):
        self.status, self.calls = status, []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return FakeResp(self.status)


def main():
    now = datetime(2026, 10, 12, 15, 0, tzinfo=timezone.utc)
    young = [{"created_at": (now - timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%SZ")}]
    old = [{"created_at": (now - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")}]
    assert ST.SiteTrigger.running_is_fresh(young, 8, now) and not ST.SiteTrigger.running_is_fresh(old, 8, now)
    assert not ST.SiteTrigger.running_is_fresh([], 8, now) and not ST.SiteTrigger.running_is_fresh([{"x": 1}], 8, now)
    t0 = time.time()
    assert ST.SiteTrigger.gap_ok(None, 20, t0) and ST.SiteTrigger.gap_ok({"ts": t0 - 21 * 60}, 20, t0)
    assert not ST.SiteTrigger.gap_ok({"ts": t0 - 5 * 60}, 20, t0)

    tr = ST.SiteTrigger()
    tr.token = ""
    ok, m = asyncio.run(tr.dispatch("hourly"))
    assert not ok and "GITHUB_SITE_TOKEN" in m                                  # no token → explains, never raises

    tr.token = "ghp_test"
    fake = FakeSession(204)

    async def sess():
        return fake

    async def no_runs():
        return []
    http.session, tr.in_progress = sess, no_runs
    store.kv_set("site_trigger_last", None)
    ok, m = asyncio.run(tr.dispatch("alert:ssi_level_3", fast=True))
    assert ok and "快速" in m, m
    c = fake.calls[-1]
    assert c["url"].endswith("/repos/bkhotey4/wallstreet-sentinel/actions/workflows/update.yml/dispatches")
    assert c["json"] == {"ref": "main", "inputs": {"fast": "true"}}
    assert c["headers"]["Authorization"] == "Bearer ghp_test" and "X-GitHub-Api-Version" in c["headers"]
    assert store.kv_get("site_trigger_last")["reason"] == "alert:ssi_level_3"
    # rate limit: a second trigger right away is skipped (unless forced, e.g. /rebuild)
    ok2, m2 = asyncio.run(tr.dispatch("hourly"))
    assert not ok2 and "分鐘" in m2 and len(fake.calls) == 1
    ok3, _ = asyncio.run(tr.dispatch("manual:1", force=True))
    assert ok3 and len(fake.calls) == 2 and fake.calls[-1]["json"]["inputs"]["fast"] == "false"
    # a fresh in-progress build → skip
    store.kv_set("site_trigger_last", None)

    async def one_young():
        return [{"created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}]
    tr.in_progress = one_young
    ok4, m4 = asyncio.run(tr.dispatch("hourly"))
    assert not ok4 and "進行中" in m4 and len(fake.calls) == 2
    # GitHub errors are explained, not raised
    tr.in_progress = no_runs
    for code, word in ((401, "token"), (403, "Actions"), (404, "repo")):
        fake.status = code
        store.kv_set("site_trigger_last", None)
        okx, mx = asyncio.run(tr.dispatch("hourly"))
        assert not okx and word in mx, (code, mx)

    # a FULL build in progress is protected from fast dispatches for protect_full_minutes
    store.kv_set("site_trigger_last", {"ts": time.time() - 22 * 60, "reason": "hourly", "fast": False})   # gap passed, still protected
    tr.in_progress = no_runs
    fake.status = 204
    okp, mp = asyncio.run(tr.dispatch("alert:danger:us", fast=True))
    assert not okp and "完整建置" in mp, mp
    store.kv_set("site_trigger_last", {"ts": time.time() - 30 * 60, "reason": "hourly", "fast": False})
    okp2, _ = asyncio.run(tr.dispatch("alert:danger:us", fast=True))
    assert okp2
    # the protection is against FAST builds only: the next scheduled FULL build 20 min later is allowed
    store.kv_set("site_trigger_last", {"ts": time.time() - 20 * 60, "reason": "scheduled", "fast": False})
    okf, mf = asyncio.run(tr.dispatch("scheduled", fast=False))
    assert okf, mf
    # the bot's scheduled build defers to a build that started recently (GitHub's own half-hourly cron)
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz
    iso = lambda m: (_dt.now(_tz.utc) - _td(minutes=m)).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    async def recent_10():
        return [{"created_at": iso(10), "event": "schedule"}]
    async def recent_40():
        return [{"created_at": iso(40), "event": "schedule"}]
    tr.recent_runs = recent_10
    assert asyncio.run(tr.started_recently(25)) is True
    tr.recent_runs = recent_40
    assert asyncio.run(tr.started_recently(25)) is False
    # token expiry: header parsing + reminder stages
    exp = ST.SiteTrigger.parse_expiry("2027-10-12 15:34:56 UTC")
    assert exp == datetime(2027, 10, 12, 15, 34, 56, tzinfo=timezone.utc)
    assert ST.SiteTrigger.parse_expiry(None) is None and ST.SiteTrigger.parse_expiry("garbage") is None
    assert [ST.SiteTrigger.expiry_stage(d) for d in (200, 30, 20, 14, 10, 7, 3, 1, 0.5, -1)] ==         [None, "30d", "30d", "14d", "14d", "7d", "7d", "1d", "1d", "expired"]
    # only RISK alerts (not info / news) kick a rebuild
    from wsb.bot.app import _alert_kind
    assert _alert_kind("danger:us:2026-10-12:2") == "risk" and _alert_kind("ssi_level_3") == "risk"
    assert _alert_kind("playbook:2:20261012") == "risk" and _alert_kind("news:abc") != "risk"
    assert _alert_kind("evt:opex:2026-10-16") is None
    # outage watch: alert once, rebuild only when GitHub is clear and nothing is building, notify on recovery
    W, t0 = ST.SiteTrigger.watch_decision, 1_000_000.0
    d = W(20, None, False, None, 60, 30, now=t0)
    assert not (d["alert"] or d["dispatch"] or d["recovered"]) and d["state"] is None          # fresh site
    assert W(None, "x", False, None, 60, 30, now=t0)["alert"] is False                         # unknown age → no noise
    d = W(90, "Degraded Actions", False, None, 60, 30, now=t0)
    assert d["alert"] and not d["dispatch"]                                                    # outage: wait, don't spam
    d = W(100, "Degraded Actions", True, d["state"], 60, 30, now=t0 + 600)
    assert not d["alert"] and not d["dispatch"]                                                # alerted once only
    d = W(110, None, True, d["state"], 60, 30, now=t0 + 1200)
    assert not d["dispatch"]                                                                   # a build is already running
    d = W(120, None, False, d["state"], 60, 30, now=t0 + 1800)
    assert d["dispatch"]                                                                       # GitHub clear, idle → rebuild
    d2 = W(125, None, False, d["state"], 60, 30, now=t0 + 2100)
    assert not d2["dispatch"]                                                                  # retry gap respected
    assert W(130, None, False, d["state"], 60, 30, now=t0 + 1800 + 1800)["dispatch"]
    d = W(5, None, False, d2["state"], 60, 30, now=t0 + 4000)
    assert d["recovered"] and d["state"] is None                                               # fresh again → tell the owner
    assert not W(5, None, False, None, 60, 30, now=t0)["recovered"]
    print("SITE TRIGGER TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
