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
    print("SITE TRIGGER TESTS PASSED ✅")


if __name__ == "__main__":
    main()
