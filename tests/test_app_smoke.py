"""Smoke test for the bot runtime logic (alerts, scheduling, permissions, delivery) with a fake discord module.
Run: python -m tests.test_app_smoke"""
from __future__ import annotations

import asyncio
import sys
import time
import types
from datetime import datetime


# ---------------------------------------------------------------- fake discord
def _identity_deco(*a, **k):
    def deco(f):
        return f
    return deco


class _Tree:
    def __init__(self):
        self.cmds = {}
        self.on_error = None

    def command(self, name=None, description=None, **k):
        def deco(f):
            self.cmds[name] = f
            return f
        return deco

    def error(self, f):
        self.on_error = f
        return f

    async def sync(self, **k):
        return []

    def clear_commands(self, **k):
        pass

    async def interaction_check(self, it):
        return True


class _Bot:
    def __init__(self, *a, **k):
        self.tree = _Tree()
        self.guilds = []
        self.user = None

    def is_closed(self):
        return False

    def get_user(self, uid):
        return None

    async def fetch_user(self, uid):
        return FakeUser(uid)

    def get_channel(self, cid):
        return None


class FakeUser:
    def __init__(self, uid):
        self.id = int(uid)
        self.dm_channel = FakeDest(f"dm:{uid}")
        self.guild_permissions = types.SimpleNamespace(manage_guild=False)

    async def create_dm(self):
        return self.dm_channel


class FakeDest:
    sent: list = []

    def __init__(self, name):
        self.name, self.id = name, hash(name) % 10**9

    async def send(self, content=None, **kw):
        FakeDest.sent.append((self.name, content, sorted(kw)))


class Embed:
    def __init__(self, **k):
        self.fields = []

    def add_field(self, **k):
        self.fields.append(k)

    def set_footer(self, **k):
        pass


def install():
    d = types.ModuleType("discord")
    d.Embed, d.Intents = Embed, types.SimpleNamespace(default=lambda: None)
    d.Activity = lambda **k: None
    d.ActivityType = types.SimpleNamespace(watching=1)
    d.Interaction = type("Interaction", (), {})
    d.Guild = object
    d.Object = lambda id: types.SimpleNamespace(id=id)
    d.File = lambda fp, filename=None: types.SimpleNamespace(fp=fp, filename=filename, reset=lambda: None)
    for n in ("Forbidden", "NotFound", "HTTPException"):
        setattr(d, n, type(n, (Exception,), {}))
    abc = types.ModuleType("discord.abc")
    abc.Messageable = object
    d.abc = abc
    ac = types.ModuleType("discord.app_commands")

    class Choice:
        def __init__(self, name, value):
            self.name, self.value = name, value

        def __class_getitem__(cls, item):
            return cls
    ac.Choice = Choice
    for n in ("choices", "describe", "default_permissions"):
        setattr(ac, n, _identity_deco)
    ac.Range = type("Range", (), {"__class_getitem__": classmethod(lambda c, i: int)})
    ac.AppCommandContext = lambda **k: None
    ac.AppInstallationType = lambda **k: None
    ac.AppCommandError = type("AppCommandError", (Exception,), {})
    ac.CheckFailure = type("CheckFailure", (ac.AppCommandError,), {})
    d.app_commands = ac
    ext = types.ModuleType("discord.ext")
    cmds = types.ModuleType("discord.ext.commands")
    cmds.Bot = _Bot
    ext.commands = cmds
    sys.modules.update({"discord": d, "discord.abc": abc, "discord.app_commands": ac,
                        "discord.ext": ext, "discord.ext.commands": cmds})


install()
import tests.test_offline as T  # noqa: E402  (synthetic market + other stubs)
from wsb import store  # noqa: E402
from wsb.bot import app as APP  # noqa: E402
from wsb.bot import present as P  # noqa: E402


async def main():
    bot = APP.Sentinel()
    APP.register_commands(bot)
    eng = bot.engine
    eng.market, eng.fred = T.m, T.fr
    eng.stress_engine.market, eng.stress_engine.fred = T.m, T.fr
    eng.holdings = {"NVDA": {"shares": 15, "cost": 50, "currency": "USD", "name": "NVDA"}}
    await eng.recompute()
    assert eng.stress is not None and eng.portfolio and not eng.portfolio.get("error"), eng.portfolio
    eng.ready = True
    dests = [FakeDest("chan")]

    async def fake_targets(kind, critical=False):
        return dests
    bot._targets = fake_targets
    P.style = lambda: "classic"                       # no Pillow rendering needed for this test

    # 1) sigma alerts keyed on bar date → same bar never alerts twice, even across a UTC day change
    q = T.m.quotes["^GSPC"]
    q["asof"] = datetime.utcnow().strftime("%Y-%m-%d")
    q["chg_pct"] = abs(q["chg_pct"]) or 1.0          # must agree with the +4σ below (direction check), not depend on the RNG
    T.m.sigma_move = lambda t, lookback=60: 4.0 if t == "^GSPC" else 0.1
    a1 = [a.key for a in bot._market_alerts() if a.key.startswith("sigma:")]
    assert a1 == [f"sigma:^GSPC:{q['asof']}:1"], a1
    await bot._run_alerts(bot._market_alerts())
    n1 = len(FakeDest.sent)
    await bot._run_alerts(bot._market_alerts())        # same bar → cooldown/key blocks re-send
    assert len(FakeDest.sent) == n1, "duplicate alert sent"
    # stale bar (>4 days) is ignored
    q["asof"] = "2020-01-01"
    assert not [a for a in bot._market_alerts() if a.key.startswith("sigma:")]

    # 2) all fired alerts are marked (not just first 10)
    run_id = int(time.time())                           # unique keys: the sqlite store persists between test runs
    many = [APP.Alert(f"t{run_id}_{i}", "⚠️ WARNING", f"title {i}", "d\nhttps://example.com/{i}") for i in range(14)]
    await bot._run_alerts(many)
    assert all(not store.alert_allowed(f"t{run_id}_{i}", 3600) for i in range(14))
    # event-keyed alerts (key contains ':') are one-shot: not re-sent after the normal cooldown has passed
    k = f"sigma:TEST{run_id}:2026-10-01:-1"
    assert store.alert_allowed(k, APP.ONE_SHOT_S)
    store.alert_mark(k, "⚠️ WARNING", "x")
    assert not store.alert_allowed(k, APP.ONE_SHOT_S)

    # 3) VIX backwardation is edge-triggered
    T.m.quotes["^VIX"] = {"price": 30, "chg_pct": 5, "asof": "2026-09-30"}
    T.m.quotes["^VIX3M"] = {"price": 25, "chg_pct": 1, "asof": "2026-09-30"}
    store.kv_set("vix_inverted", False)
    k1 = [a.key for a in bot._market_alerts() if a.key.startswith("vix_")]
    k2 = [a.key for a in bot._market_alerts() if a.key.startswith("vix_")]
    assert len(k1) == 1 and k2 == [], (k1, k2)

    # 4) briefing scheduler: due inside a 60-min window, marked only after success, failure retries
    now = datetime(2026, 9, 30, 7, 55, tzinfo=APP.E.TZ)          # Wednesday, 25 min after 07:30
    assert bot._due(now, "07:30", [2], "k_test")
    calls = []

    async def ok():
        calls.append(1)

    async def boom():
        raise RuntimeError("x")
    await bot._run_job("k_fail", boom())
    assert not store.kv_get("k_fail")
    await bot._run_job("k_ok", ok())
    assert store.kv_get("k_ok") and not bot._due(now, "07:30", [2], "k_ok")

    # 5) permissions: non-owner blocked from private commands, allowed for public ones
    store.kv_set("owner_id", "111")

    class Resp:
        def __init__(self):
            self.msgs = []

        async def send_message(self, m, **k):
            self.msgs.append(m)

        def is_done(self):
            return False

    def it(name, uid):
        return types.SimpleNamespace(command=types.SimpleNamespace(name=name), data={"name": name},
                                     user=FakeUser(uid), guild=object(), response=Resp())
    assert await bot.tree.interaction_check(it("dashboard", 999))
    assert not await bot.tree.interaction_check(it("portfolio", 999))
    assert await bot.tree.interaction_check(it("portfolio", 111))

    # 6) classic delivery never exceeds 2000 chars per message
    FakeDest.sent.clear()
    await P.deliver(FakeDest("c"), content="Q" * 300, text="段落。" * 2000, title="t", engine_name="x")
    assert all(len(c or "") <= 2000 for _, c, _ in FakeDest.sent)

    # 7) scorecard episode merge + NY-date window already covered in test_offline; SSI model re-baseline:
    store.kv_set("ssi_model", "old")
    store.kv_set("ssi_level_idx", 0)
    bot._market_alerts()
    assert store.kv_get("ssi_model") != "old"
    # 8) forward-looking alerts are edge-triggered (first look = silent baseline, then only on a change)
    from wsb.analytics import playbook as PB
    from datetime import date as _d
    eng_ = bot.engine
    for k in ("playbook_stage", "shock_div", "shock_paths", "regime_flags"):
        store.kv_set(k, None)
    path = lambda st_: [{"name": "信用事件", "state": st_, "ignition": 75.0, "blocks": ["信用"], "story": "x"}]
    div = lambda f: {"available": True, "credit": 60.0, "equity": 40.0, "gap": 20.0, "threshold": 15.0, "flag": f,
                     "hist": {"prob_when_flagged": 8.0, "base_rate": 16.0}}
    eng_.playbook = {"stage": 1, "points": 2, "name": "留意", "why": [(2, "x")], "actions": ["a"], "emoji": "🟡"}
    eng_.shock = {"paths": path("低"), "divergence": div(False)}
    eng_.breaks = {"available": True, "flags": [], "metrics": {}}
    assert not bot._intel_alerts()                                        # baseline run → silent
    eng_.playbook = {"stage": 2, "points": 4, "name": "戒備", "why": [(4, "x")], "actions": ["a", "b"], "emoji": "🟠"}
    eng_.shock = {"paths": path("高度警戒"), "divergence": div(True)}
    eng_.breaks = {"available": True, "metrics": {}, "flags": [{"key": "stock_bond", "title": "t", "detail": "d"}]}
    al = {a.key.split(":")[0] + ":" + a.key.split(":")[1]: a for a in bot._intel_alerts()}
    assert {"playbook:2", "shock:div", "shock:信用事件", "regime:stock_bond"} <= set(al), set(al)
    assert al["shock:div"].severity.startswith("ℹ️")                      # history says divergence is not predictive → INFO only
    assert not bot._intel_alerts()                                        # unchanged state → no repeat
    eng_.playbook = {"stage": 1, "points": 3, "name": "留意", "why": [], "actions": [], "emoji": "🟡"}
    bot._intel_alerts()
    assert store.kv_get("playbook_stage") == 2                            # hysteresis: 3 pts is not ≥2 below stage-2 entry
    # liquidity heads-up: only importance-3 events within 1 day
    tomorrow = (_d.today() + __import__("datetime").timedelta(days=1)).isoformat()
    eng_.calendar.events = [{"date": tomorrow, "type": "liquidity", "id": "t1", "event": "四巫日", "importance": 3, "note": "n"},
                            {"date": tomorrow, "type": "liquidity", "id": "t2", "event": "VIX", "importance": 1}]
    assert [a.key for a in bot._liquidity_alerts()] == [f"evt:t1:{tomorrow}"]
    # intel-station push rules: first run records state silently, then only changes alert
    import types as _t
    for k in ("push_dp_state", "push_val_grades", "push_breadth_below", "push_13f_seen", "push_insider_big"):
        store.kv_set(k, None)
    eng_.darkpool = _t.SimpleNamespace(result={"pctile": 50.0, "dpi_5d": 42.0, "asof": "2026-10-07"})
    eng_.valuation = {"available": True, "groups": [{"items": [{"key": "buffett", "grade": "偏熱", "label": "巴菲特指標", "value": 210.0,
                                                                 "unit": "%", "pctile": 90.0, "hist_start": "1990", "what": "w"}]}]}
    today = _d.today().isoformat()
    eng_.bonds = {"weak": [{"cusip": "C1", "date": today, "label": "10-Year", "high_yield": 4.5, "btc": 2.1, "btc_avg": 2.6,
                            "dealer": 20.0, "dealer_avg": 12.0}]}
    eng_.rotation = {"breadth": {"us": {"now": 55.0}}}
    gm = lambda filed: {"available": True, "managers": [{"cik": 1, "name": "波克夏", "period": "2026-06-30", "filed": filed, "url": "u",  # noqa: E731
                                                          "chg": {"new": [{"name": "APPLE"}], "exit": [], "add": [], "cut": []}}]}
    eng_.gurus = _t.SimpleNamespace(result=gm("2026-08-14"))
    eng_.insiders = _t.SimpleNamespace(board=lambda n=20: {"big": [], "sells": []})
    first = bot._extras_alerts()
    assert [a.key for a in first] == [f"push:auction:C1:{today}"], [a.key for a in first]     # dated event → fires once
    eng_.darkpool.result["pctile"] = 95.0
    eng_.valuation["groups"][0]["items"][0]["grade"] = "極端"
    eng_.rotation = {"breadth": {"us": {"now": 25.0}}}
    eng_.gurus = _t.SimpleNamespace(result=gm("2026-11-14"))
    eng_.insiders = _t.SimpleNamespace(board=lambda n=20: {"big": ["AAPL"], "sells": [{"sym": "AAPL", "sell_disc_usd": 9e7, "n_sellers": 2,
                                                                                         "big": [{"owner": "x", "title": "CEO", "url": "u"}]}]})
    keys = {a.key.split(":")[1] for a in bot._extras_alerts()}
    assert {"dp", "val", "breadth", "13f", "insider", "auction"} <= keys, keys
    assert not [a for a in bot._extras_alerts() if a.key.split(":")[1] in ("dp", "val", "breadth", "13f", "insider")], "no repeats"
    print("APP SMOKE TESTS PASSED ✅")


if __name__ == "__main__":
    asyncio.run(main())
