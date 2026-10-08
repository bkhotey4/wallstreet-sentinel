"""Discord layer: slash commands, 24/7 monitor loops, alert engine,
scheduled briefings."""
from __future__ import annotations

import asyncio
import contextvars
import hashlib
import json
import logging
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, List, Optional

import discord
import numpy as np
import pandas as pd
from discord import app_commands
from discord.ext import commands

from ..ai import context, llm, prompts
from ..config import (ALERT_CHANNEL_ID, BRIEFING_CHANNEL_ID, DATA_DIR,
                      OWNER_USER_ID, SETTINGS)
from ..data import http
from ..health import HEALTH
from ..data.market import fetch_info, fetch_single
from ..engine import Engine
from .. import earnings as ER
from .. import morning as MO
from .. import weekly as WK
from .. import store
from ..analytics import hedge as HG
from ..analytics import playbook as PB
from ..analytics import scorecard as SC
from ..analytics import watch as WATCH
from ..data import fomc as FOMC
from ..data.options import fetch_chain
from . import command as CMD
from . import embeds as E
from . import present as P

log = logging.getLogger("sentinel")
R = SETTINGS["refresh"]
A = SETTINGS["alerts"]


ONE_SHOT_S = 10 * 365 * 86400      # 'never again' cooldown for event-keyed alerts
JOB_RETRY_S = 300                  # a failed scheduled job is retried at most every 5 minutes …
JOB_MAX_TRIES = 4                  # … and the last try delivers even if the AI is still down
JOB_FINAL = contextvars.ContextVar("job_final", default=True)   # False while a scheduled job may still be retried


class AIUnavailable(RuntimeError):
    pass


@dataclass
class Alert:
    key: str
    severity: str   # "🚨 CRITICAL" | "⚠️ WARNING" | "ℹ️ INFO"
    title: str
    detail: str


class Sentinel(commands.Bot):
    def __init__(self) -> None:
        self._started = time.time()
        self._ask_hist: dict = {}
        intents = discord.Intents.default()
        super().__init__(
            command_prefix="!", intents=intents, help_command=None,
            # slash commands usable in servers AND in private messages with the bot
            allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
            allowed_installs=app_commands.AppInstallationType(guild=True, user=True))
        self.engine = Engine()
        self._tasks: List[asyncio.Task] = []
        self._bg: set = set()                     # strong refs to fire-and-forget tasks (+ error logging)
        self._sending: set = set()                # scheduled jobs currently in progress
        saved = store.kv_get("delivery")
        if isinstance(saved, dict):
            SETTINGS.raw.setdefault("delivery", {}).update(saved)

    # ------------------------------------------------------------------ setup
    async def setup_hook(self) -> None:
        register_commands(self)
        await self.tree.sync()                 # global: works in the server AND in DMs, no duplicates
        self._tasks.append(asyncio.create_task(self._supervisor()))

    async def close(self) -> None:
        for t in self._tasks:
            t.cancel()
        await http.close()
        if getattr(self, "_web", None):
            try:
                await self._web.cleanup()
            except Exception:  # noqa: BLE001
                pass
        await super().close()

    async def on_guild_join(self, guild: discord.Guild) -> None:
        log.info("joined server: %s (%s)", guild.name, guild.id)

    def spawn(self, coro, name: str = "job") -> asyncio.Task:
        t = asyncio.create_task(coro, name=name)
        self._bg.add(t)

        def _done(task: asyncio.Task) -> None:
            self._bg.discard(task)
            if not task.cancelled() and task.exception():
                log.error("background job %s failed", name, exc_info=task.exception())
        t.add_done_callback(_done)
        return t

    async def on_ready(self) -> None:
        # remove guild-scoped command copies left by older versions (they showed every command twice)
        for g in self.guilds:
            if not store.kv_get(f"guild_cmds_cleaned:{g.id}"):
                try:
                    self.tree.clear_commands(guild=g)
                    await self.tree.sync(guild=g)
                    store.kv_set(f"guild_cmds_cleaned:{g.id}", True)
                    log.info("cleared duplicate guild commands in %s", g.name)
                except Exception as e:  # noqa: BLE001
                    log.warning("guild command cleanup failed: %s", e)
        log.info("Logged in as %s (%s) — in %d server(s): %s", self.user, self.user.id if self.user else "?",
                 len(self.guilds), ", ".join(g.name for g in self.guilds) or "NONE（請先邀請 bot 進伺服器，否則無法私訊）")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                             name="全球市場 24/7"))

    # ------------------------------------------------------------ channels
    async def _channel(self, kind: str) -> Optional[discord.abc.Messageable]:
        cid = store.kv_get(f"{kind}_channel") or (ALERT_CHANNEL_ID if kind == "alerts" else BRIEFING_CHANNEL_ID) \
            or store.kv_get("alerts_channel") or ALERT_CHANNEL_ID
        if not cid:
            return None
        ch = self.get_channel(int(cid))
        if ch is None:
            try:
                ch = await self.fetch_channel(int(cid))
            except Exception:  # noqa: BLE001
                return None
        return ch

    async def _owner_dm(self) -> Optional[discord.abc.Messageable]:
        uid = store.kv_get("owner_id") or OWNER_USER_ID
        if not uid:
            return None
        try:
            u = self.get_user(int(uid)) or await self.fetch_user(int(uid))
            return u.dm_channel or await u.create_dm()
        except Exception as e:  # noqa: BLE001
            log.warning("cannot open DM with owner: %s", e)
            return None

    async def _targets(self, kind: str, critical: bool = False) -> List[discord.abc.Messageable]:
        """Where to deliver: the configured channel and/or the owner's private messages."""
        D = SETTINGS.get("delivery", {})
        out: List[discord.abc.Messageable] = []
        ch = await self._channel(kind)
        if ch:
            out.append(ch)
        mode = D.get("dm_alerts", "critical") if kind == "alerts" else ("all" if D.get("dm_briefings", True) else "none")
        want_dm = mode == "all" or (mode == "critical" and critical) or not out   # no channel → DM fallback
        if want_dm:
            dm = await self._owner_dm()
            if dm and all(getattr(t, "id", None) != getattr(dm, "id", -1) for t in out):
                out.append(dm)
        return out

    # ------------------------------------------------------------ loops
    async def _every(self, name: str, seconds: float, fn: Callable[[], Awaitable[None]],
                     first_delay: float = 0) -> None:
        await asyncio.sleep(first_delay)
        while not self.is_closed():
            t0 = time.time()
            try:
                await fn()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                log.exception("loop %s crashed (continuing)", name)
            await asyncio.sleep(max(5.0, seconds - (time.time() - t0)))

    async def _supervisor(self) -> None:
        await self.wait_until_ready()
        self._tasks.append(asyncio.create_task(self._every("heartbeat", 60, self._heartbeat, 0)))
        # scheduler starts immediately (it waits for engine.ready itself) so a restart never skips a briefing
        self._tasks.append(asyncio.create_task(self._every("briefings", 30, self._briefing_tick, 10)))
        log.info("bootstrapping data engine…")
        try:
            await self.engine.bootstrap()
        except Exception:  # noqa: BLE001
            log.exception("bootstrap partially failed")
        log.info("engine ready: %s", self.engine.stress.score if self.engine.stress else "no stress yet")
        eng = self.engine
        extra = eng.holding_tickers

        async def quotes():
            await eng.market.refresh_quotes(list(dict.fromkeys(extra() + store.palert_tickers())))
            await eng.recompute()
            try:
                await self._run_alerts(self._market_alerts())
            except Exception:  # noqa: BLE001
                log.exception("market alerts failed")
            try:
                await self._check_price_alerts()
            except Exception:  # noqa: BLE001
                log.exception("price alerts failed")

        async def history():
            # rebuild when due, or keep retrying every 10 min if the history is missing/too short
            if eng.market.history_is_stale() or len(eng.market.history) < 300:
                await eng.market.refresh_history(extra())

        async def fred():
            await eng.fred.refresh()

        async def crypto():
            await eng.crypto.refresh()

        async def news_alerts(fresh):
            recent = time.time() - 6 * 3600                  # only genuinely new stories (not old ones seen late)
            await self._run_alerts([
                Alert(f"news:{n.uid}", "⚠️ WARNING" if n.score < A["news_score"] + 4 else "🚨 CRITICAL",
                      f"情報：{n.title[:180]}", f"來源 {n.source} · 風險分數 {n.score} · 關鍵字 {', '.join(n.hits)}\n{n.link}")
                for n in fresh if n.score >= A["news_score"] and n.ts >= recent][:4])

        async def news():
            await news_alerts(await eng.news.refresh())

        async def options():
            await eng.options.refresh()
            await self._run_alerts(self._gamma_alerts())

        async def sec_process(fresh):
            from datetime import date as _date
            cutoff = (_date.today() - timedelta(days=3)).isoformat()
            fresh = [f for f in fresh if f.get("date", "") >= cutoff]      # ignore old filings seen for the first time
            important = {"8-K", "6-K", "SC 13D", "SCHEDULE 13D", "S-1", "S-3", "424B5", "NT 10-Q", "NT 10-K", "4"}
            await self._run_alerts([
                Alert(f"sec:{f['url']}", "ℹ️ INFO", f"SEC：{f['ticker']} 提交 {f['form']}（{f['label']}）",
                      f"{f['date']} {f.get('desc') or ''}\n{f['url']}")
                for f in fresh if f["form"] in important and not f.get("earnings")][:6])
            for f in [x for x in fresh if x.get("earnings")][:3]:
                if store.kv_get(f"earn_done:{f['acc']}"):
                    continue
                store.kv_set(f"earn_done:{f['acc']}", True)
                txt = await ER.analyze_release(eng, f)
                for t in await self._targets("briefings"):
                    await P.deliver(t, text=txt, title=f"{f['ticker']} 財報快評")

        async def sec():
            await sec_process(await eng.sec.refresh([t for t in extra() if "." not in t]))

        async def taiwan():
            await eng.taiwan.refresh()

        async def cal():
            await eng.calendar.refresh(extra())
            await self._run_alerts(self._liquidity_alerts())
            for rec in await ER.upcoming_previews(eng, days=2):
                txt = await ER.preview_text(eng, rec)
                for t in await self._targets("briefings"):
                    await P.deliver(t, slides=lambda r=rec: P.v_earnings_preview(eng, r),
                                    embeds=lambda r=rec: E.earnings_preview(eng, r),
                                    text=txt, title=f"{rec['ticker']} 財報前預告")

        async def fomc():
            await self.fomc_tick()

        async def backup():
            path = await asyncio.to_thread(store.backup, int(SETTINGS.get("backup", {}).get("keep", 7)))
            if path:
                log.info("daily db backup → %s", path)
            HEALTH.ok("db_backup", 1, every=86400)

        try:
            from .. import web as _web
            self._web = await _web.start(eng)
        except Exception:  # noqa: BLE001
            log.exception("web dashboard failed to start")

        loops = [
            ("backup", 6 * 3600, backup, 120),
            ("fomc", 1200, fomc, 300),
            ("quotes", R["quotes"], quotes, R["quotes"]),
            ("history", 600, history, 600),
            ("fred", R["fred"], fred, R["fred"]),
            ("crypto", R["crypto"], crypto, R["crypto"]),
            ("news", R["news"], news, 5),
            ("options", R["options_gamma"], options, R["options_gamma"]),
            ("sec", R["sec"], sec, 30),
            ("calendar", R["calendar"], cal, R["calendar"]),
            ("taiwan", SETTINGS.get("taiwan", {}).get("refresh_seconds", 7200), taiwan,
             SETTINGS.get("taiwan", {}).get("refresh_seconds", 7200)),
        ]
        # items that arrived while the bot was down / bootstrapping are handled once (freshness-filtered)
        try:
            await news_alerts(getattr(eng.news, "last_fresh", []))
            await sec_process(getattr(eng.sec, "last_fresh", []))
        except Exception:  # noqa: BLE001
            log.exception("bootstrap news/SEC processing failed")
        for name, sec_, fn, delay in loops:
            self._tasks.append(asyncio.create_task(self._every(name, sec_, fn, delay)))

    async def _dump(self) -> None:
        """Local trigger (dump.flag): write the live analysis state to data_cache/dump_*.{txt,json} for offline review."""
        eng = self.engine
        try:
            (DATA_DIR / "dump_datapack.txt").write_text(context.build(eng, "full"), encoding="utf-8")
            st = eng.stress
            state = {"asof": datetime.now().isoformat(timespec="seconds"),
                     "portfolio": eng.portfolio, "odds": eng.odds, "regime": eng.regime,
                     "stress": ({"score": st.score, "label": st.label, "blocks": st.blocks, "chg_1d": st.chg_1d,
                                 "chg_5d": st.chg_5d, "chg_20d": st.chg_20d, "pctile": st.pctile_all,
                                 "coverage": st.coverage,
                                 "components": {c.id: {"score": c.score, "z": c.z, "raw": c.raw, "asof": c.asof, "status": c.status}
                                                for c in st.components}} if st else None),
                     "fred": {sid: {"n": int(len(x)), "first": str(x.index.min().date()) if len(x) else None,
                                    "last": str(x.index.max().date()) if len(x) else None}
                             for sid, x in eng.fred.series.items()},
                     "quotes": {k: v for k, v in eng.market.quotes.items()},
                     "returns": eng.market.returns_table(list(eng.market.quotes.keys()))}
            (DATA_DIR / "dump_state.json").write_text(json.dumps(state, ensure_ascii=False, default=str, indent=1), encoding="utf-8")
            log.info("dump.flag → wrote dump_datapack.txt / dump_state.json")
        except Exception:  # noqa: BLE001
            log.exception("dump failed")

    async def _probe(self) -> None:
        """Diagnostics: fetch URLs listed in data_cache/probe_urls.txt ('name|url') → data_cache/probe/<name>.txt"""
        src = DATA_DIR / "probe_urls.txt"
        outdir = DATA_DIR / "probe"
        outdir.mkdir(exist_ok=True)
        if not src.exists():
            return
        for line in src.read_text(encoding="utf-8").splitlines():
            if "|" not in line:
                continue
            name, url = [x.strip() for x in line.split("|", 1)]
            try:
                txt = await http.get(url, kind="text", timeout=30, retries=1,
                                     headers={"Accept": "application/json, text/html, */*"})
                (outdir / f"{name}.txt").write_text(txt[:30000], encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                (outdir / f"{name}.txt").write_text(f"ERROR {type(e).__name__}: {e}", encoding="utf-8")
        log.info("probe done")

    async def _check_price_alerts(self) -> None:
        OPS = {"above": ("價格高於", lambda p, c, v: p >= v), "below": ("價格低於", lambda p, c, v: p <= v),
               "up_pct": ("單日漲幅達", lambda p, c, v: c is not None and c >= v),
               "down_pct": ("單日跌幅達", lambda p, c, v: c is not None and c <= -abs(v))}
        for aid, uid, t, op, val, note, *_ in store.palert_list():
            q = self.engine.market.q(t)
            if not q or op not in OPS:
                continue
            label, fn = OPS[op]
            if not fn(q["price"], q.get("chg_pct"), val):
                continue
            unit = "%" if op.endswith("pct") else ""
            title = f"價格警示觸發：{t} {label} {val:g}{unit}"
            detail = f"現價 {q['price']:.4g}（今日 {(q.get('chg_pct') or 0):+.2f}%）" + (f"｜備註：{note}" if note else "")
            try:
                u = self.get_user(int(uid)) or await self.fetch_user(int(uid))
                dm = u.dm_channel or await u.create_dm()
                await P.deliver(dm, slides=lambda: _S().deck_alert("價格警示", [("⚠️ WARNING", title, detail)],
                                                                   self.engine.stress.score if self.engine.stress else None),
                                embeds=lambda: discord.Embed(title=title, description=detail, color=0xF39C12))
                store.palert_fire(aid)                 # only after the DM went out
                log.info("price alert #%s fired for %s", aid, uid)
            except Exception as e:  # noqa: BLE001
                log.warning("price alert DM failed: %s", e)

    async def _demo(self) -> None:
        eng = self.engine
        targets = await self._targets("briefings")
        chains = {}
        for u in ("SPY", "QQQ"):
            try:
                chains[u] = await fetch_chain(u)
            except Exception as ex:  # noqa: BLE001
                log.warning("demo chain %s failed: %s", u, ex)
        hres = HG.analyze(eng.portfolio, chains, eng.stress.score if eng.stress else None) if chains else {"error": "CBOE 無資料"}
        sres = SC.evaluate(store.tracked_alerts(365), eng.market.series("^GSPC"))
        from . import slides as S
        log.info("demo → chains=%s style=%s", list(chains), P.style())
        for t in targets:
            await P.deliver(t, content="## 新版投影片呈現示範",
                            slides=lambda: (S.deck_risk(eng, ("overview", "blocks", "markets", "trend", "crash"))
                                            + S.deck_portfolio(eng) + S.deck_hedge(eng, hres) + S.deck_scorecard(eng, sres)))

    async def _heartbeat(self) -> None:
        flag = DATA_DIR / "restart.flag"
        if flag.exists():                      # graceful restart request (watchdog relaunches us)
            log.info("restart.flag found → exiting for restart")
            flag.unlink(missing_ok=True)
            logging.shutdown()                 # flush logs; don't await close() (it would cancel this task)
            os._exit(0)
        ff_ = DATA_DIR / "fomc.flag"
        if ff_.exists() and self.engine.ready:
            ff_.unlink(missing_ok=True)
            self.spawn(self.fomc_tick(force=True), "fomc_flag")
        wf_ = DATA_DIR / "weekly.flag"
        if wf_.exists() and self.engine.ready:
            wf_.unlink(missing_ok=True)
            self.spawn(self.send_weekly(await self._targets("briefings")), "weekly_flag")
        tb = DATA_DIR / "testbrief.flag"
        if tb.exists() and self.engine.ready:  # local trigger: send a test briefing to all targets
            tb.unlink(missing_ok=True)
            targets = await self._targets("briefings")
            log.info("testbrief.flag → sending to %d target(s)", len(targets))
            self.spawn(self.send_briefing(targets, "連線測試簡報", "us_pre"), "testbrief")
        for fname, coro in (("morning.flag", lambda tg: self.send_morning(tg, "華爾街晨會簡報", "即時")),
                            ("taiwan.flag", lambda tg: self.send_taiwan(tg)),
                            ("earnboard.flag", lambda tg: self.send_earnings_board(tg))):
            fl = DATA_DIR / fname
            if fl.exists() and self.engine.ready:
                fl.unlink(missing_ok=True)
                tg = await self._targets("briefings")
                log.info("%s → %d target(s)", fname, len(tg))
                self.spawn(coro(tg), fname)
        dp = DATA_DIR / "dump.flag"
        if dp.exists() and self.engine.ready:
            dp.unlink(missing_ok=True)
            self.spawn(self._dump(), "dump")
        pr = DATA_DIR / "probe.flag"
        if pr.exists():
            pr.unlink(missing_ok=True)
            self.spawn(self._probe(), "probe")
        demo = DATA_DIR / "demo.flag"
        if demo.exists() and self.engine.ready:  # local trigger: live demo of hedge + scorecard
            demo.unlink(missing_ok=True)
            self.spawn(self._demo(), "demo")
        st = self.engine.stress
        payload = json.dumps({"ts": time.time(), "iso": datetime.now().isoformat(timespec="seconds"),
                              "ssi": st.score if st else None, "ready": self.engine.ready})
        for attempt in range(4):                    # Windows: the watchdog/antivirus may hold the file for a moment
            try:
                (DATA_DIR / "heartbeat.json").write_text(payload, encoding="utf-8")
                break
            except PermissionError:
                if attempt == 3:
                    log.warning("heartbeat.json locked, skipped this beat")
                else:
                    await asyncio.sleep(0.5)

    # ------------------------------------------------------------ alert rules
    def _market_alerts(self) -> List[Alert]:
        eng, out = self.engine, []
        st = eng.stress
        if st:
            levels = SETTINGS.get("stress_levels", [])
            idx = next((i for i, lv in enumerate(levels) if st.score < lv["max"]), len(levels) - 1)
            ver = hashlib.md5(json.dumps(SETTINGS.get("stress_components", []), sort_keys=True).encode()).hexdigest()[:10]
            if store.kv_get("ssi_model") != ver:        # model changed → re-baseline silently (no fake escalation)
                store.kv_set("ssi_model", ver)
                store.kv_set("ssi_level_idx", idx)
            prev = store.kv_get("ssi_level_idx")
            if A.get("stress_level_cross") and prev is not None and idx > prev and idx >= 2:
                sev = "🚨 CRITICAL" if idx >= 3 else "⚠️ WARNING"
                drv = ", ".join(f"{c.id}({c.score:.0f})" for c in st.drivers(4))
                out.append(Alert(f"ssi_level_{idx}", sev, f"系統性壓力升級 → {st.emoji} {st.label}（SSI {st.score:.1f}）",
                                 f"主要推升：{drv}"))
            # hysteresis: only step down after 3 pts below the boundary
            if prev is None or idx >= prev or st.score < levels[idx]["max"] - 3:
                store.kv_set("ssi_level_idx", idx)
            bar = st.history.index[-1].strftime("%Y%m%d") if len(st.history) else "na"
            if st.chg_1d is not None and st.chg_1d >= A.get("stress_jump_points", 8):
                out.append(Alert(f"ssi_jump:{bar}", "⚠️ WARNING", f"SSI 單日跳升 {st.chg_1d:+.1f} 點 → {st.score:.1f}",
                                 "區塊：" + ", ".join(f"{k} {v:.0f}" for k, v in sorted(st.blocks.items(), key=lambda x: -x[1])[:4])))
        names = SETTINGS.names()
        tickers = A.get("key_assets", []) if A.get("sigma_move_key_only") else list(set(SETTINGS.names()) | set(eng.holding_tickers()))
        thr = float(A.get("sigma_move", 3.0))
        fresh_cut = (datetime.now(timezone.utc) - timedelta(days=4)).strftime("%Y-%m-%d")
        for t in tickers:
            sg = eng.market.sigma_move(t)
            q = eng.market.q(t)
            if sg is None or q is None or abs(sg) < thr or q.get("asof", "") < fresh_cut:
                continue
            if not (q.get("chg_pct") == q.get("chg_pct")) or np.sign(sg) != np.sign(q["chg_pct"]):
                continue                                   # quote and history disagree on direction → data glitch, don't alert
            sev = "🚨 CRITICAL" if abs(sg) >= thr + 1.5 or t in A.get("key_assets", []) else "⚠️ WARNING"
            # keyed on the BAR date → a Friday move alerts once, not again on Sat/Sun/Mon morning
            out.append(Alert(f"sigma:{t}:{q['asof']}:{int(np.sign(sg))}", sev,
                             f"異常波動：{names.get(t, t)} ({t}) {q['chg_pct']:+.2f}%（{sg:+.1f}σ）",
                             f"現價 {q['price']:.4g} · 自身60日波動的 {abs(sg):.1f} 倍"))
        vix, v3 = eng.market.q("^VIX"), eng.market.q("^VIX3M")
        inverted = bool(vix and v3 and vix["price"] > v3["price"])
        was = store.kv_get("vix_inverted")
        if vix and v3:
            store.kv_set("vix_inverted", inverted)
        if A.get("vix_backwardation") and inverted and was is False:        # edge-triggered: only when it flips
            out.append(Alert(f"vix_backwardation:{vix['asof']}", "🚨 CRITICAL", f"VIX 期限結構倒掛：VIX {vix['price']:.2f} > VIX3M {v3['price']:.2f}",
                             "近月恐慌高於遠月 → 市場在為『立即』的尾部風險付費，歷史上多見於急跌階段"))
        for key, sev, title, detail in (WATCH.health_alerts(st, time.time() - self._started) +
                                        WATCH.concentration_alerts(eng.portfolio)):
            out.append(Alert(key, sev, title, detail))
        out += self._intel_alerts()
        out += self._stop_alerts()
        pf = eng.portfolio
        if pf and not pf.get("error") and pf.get("total_value_usd"):
            dd = pf["day_pnl_usd"] / pf["total_value_usd"] * 100
            if dd <= -abs(A.get("portfolio_drawdown_pct", 3)):
                worst = sorted([p for p in pf["positions"] if p.get("d1_pct") is not None], key=lambda p: p["d1_pct"])[:3]
                bar_day = max((q_.get("asof", "") for q_ in (eng.market.q(p["sym"]) for p in pf["positions"]) if q_), default="na")
                out.append(Alert(f"pf_dd:{bar_day}", "🚨 CRITICAL", f"持倉單日回撤 {dd:.2f}%（${pf['day_pnl_usd']:,.0f}）",
                                 "拖累：" + ", ".join(f"{p['sym']} {p['d1_pct']:+.1f}%" for p in worst)))
        return out

    def _intel_alerts(self) -> List[Alert]:
        """Forward-looking alerts: playbook stage rises, credit-vs-equity divergence, shock-path ignition,
        hedge-failure / regime-break flags.  All edge-triggered (alert on the change, not on the level)."""
        eng, out = self.engine, []
        now = datetime.now(timezone.utc)
        day, week = now.strftime("%Y%m%d"), f"{now.isocalendar()[0]}W{now.isocalendar()[1]:02d}"
        pbk = eng.playbook
        if pbk and eng.stress:
            prev = store.kv_get("playbook_stage")
            new = PB.hysteresis(prev, pbk)
            store.kv_set("playbook_stage", new)
            if prev is not None and new > prev and new >= int(SETTINGS.get("playbook", {}).get("alert_min_stage", 2)):
                why = "；".join(w for _, w in pbk["why"])
                acts = "\n".join(f"{i}. {a}" for i, a in enumerate(pbk.get("actions", []), 1))
                out.append(Alert(f"playbook:{new}:{day}", "🚨 CRITICAL" if new >= 3 else "⚠️ WARNING",
                                 f"風險劇本升級 → {PB.STAGES[new]['emoji']} {PB.STAGES[new]['name']}（風險分 {pbk['points']}）",
                                 f"觸發：{why}\n{acts}\n（/command 看完整戰情）"))
        sk = eng.shock or {}
        dv = sk.get("divergence") or {}
        if dv.get("available"):
            was = store.kv_get("shock_div")
            store.kv_set("shock_div", bool(dv["flag"]))
            if dv["flag"] and was is False:
                hs = dv.get("hist") or {}
                pw, base = hs.get("prob_when_flagged"), hs.get("base_rate")
                backed = pw is not None and base and pw >= 1.2 * base
                extra = (f"歷史上背離時 63 日內跌≥10% 機率 {pw:.1f}%（基準 {base:.1f}%）"
                         + ("。" if backed else "——歷史未證實它有預測力，僅供參考。") if pw is not None else "")
                out.append(Alert(f"shock:div:{day}", "⚠️ WARNING" if backed else "ℹ️ INFO", f"股債背離：信用壓力 {dv['credit']:.0f} 領先股市恐慌 {dv['equity']:.0f}（差 {dv['gap']:+.0f}）",
                                 "債市／信用已在定價風險、股市尚未反應；" + extra))
        if sk.get("paths"):
            prev_states = store.kv_get("shock_paths") or {}
            cur = {p["name"]: p["state"] for p in sk["paths"]}
            store.kv_set("shock_paths", cur)
            for p in sk["paths"]:
                if p["state"] == "高度警戒" and prev_states and prev_states.get(p["name"]) not in (None, "高度警戒"):
                    out.append(Alert(f"shock:{p['name']}:{day}", "⚠️ WARNING", f"衝擊路徑點火：{p['name']}（點火分數 {p['ignition']:.0f}）",
                                     f"{p['story']}\n涉及區塊：{'、'.join(p['blocks'])}（/shock 看雷達）"))
        out += self._fusion_alerts(day, week)
        br = eng.breaks or {}
        if br.get("available"):
            prev_flags = store.kv_get("regime_flags")
            cur_flags = [f["key"] for f in br["flags"]]
            store.kv_set("regime_flags", cur_flags)
            if prev_flags is not None:
                for f in br["flags"]:
                    if f["key"] not in prev_flags:
                        out.append(Alert(f"regime:{f['key']}:{week}", "⚠️ WARNING", "避險機制警示：" + f["title"], f["detail"]))
        return out

    def _fusion_alerts(self, day: str, week: str) -> List[Alert]:
        """Intelligence fusion (edge-triggered): a transmission path becomes 『確認』 (news AND prices), the composite
        verdict rises to 高, or the macro quadrant changes."""
        itl, out = self.engine.intel or {}, []
        v = itl.get("verdict") or {}
        if not v.get("available"):
            return out
        cfg = SETTINGS.get("intel", {})
        prev = store.kv_get("intel_states")
        cur = {r["channel"]: r["state"] for r in itl.get("channels", [])}
        store.kv_set("intel_states", cur)
        if prev is not None:
            for r in itl.get("channels", []):
                if r["state"] == "確認" and prev.get(r["channel"]) != "確認":
                    head = f"\n頭條（{r['top'][0]['source']}）：{r['top'][0]['title'][:160]}" if r["top"] else ""
                    out.append(Alert(f"intel:confirm:{r['channel']}:{day}", "⚠️ WARNING",
                                     f"情報確認：{r['channel']}——新聞與價格同時示警（融合 {r['fused']:.0f}）",
                                     f"市場點火 {r['ignition']:.0f}、新聞熱度 {r['news_level']:.0f}（{r['news_n']} 則）{head}\n{r['watch']}（/intel 看完整研判）"))
        was = store.kv_get("intel_label")
        store.kv_set("intel_label", v["label"])
        rank = {"低": 0, "中性": 1, "偏高": 2, "高": 3}
        min_lbl = cfg.get("alert_min_label", "高")
        if was is not None and rank.get(v["label"], 0) > rank.get(was, 0) and rank.get(v["label"], 0) >= rank.get(min_lbl, 3):
            out.append(Alert(f"intel:level:{v['label']}:{day}", "⚠️ WARNING", f"綜合風險升至「{v['label']}」（{v['score']:.0f}）",
                             f"{v['headline']}\n信心 {v['confidence']}，{v['consensus']}（/intel 看證據帳本）"))
        rg = itl.get("regime") or {}
        q_prev = store.kv_get("intel_quadrant")
        if rg.get("quadrant"):
            store.kv_set("intel_quadrant", rg["quadrant"])
            if q_prev and q_prev != rg["quadrant"] and cfg.get("alert_quadrant_change", True):
                out.append(Alert(f"intel:quad:{rg['quadrant']}:{week}", "ℹ️ INFO", f"總經象限轉換：{q_prev} → {rg['quadrant']}",
                                 f"{rg.get('drift') or ''}；{(self.engine.regime or {}).get('playbook', '')}"))
        return out

    def _stop_alerts(self) -> List[Alert]:
        """Edge-triggered: a meaningful position closes below its volatility stop (alert once per breach)."""
        out = []
        min_w = float(SETTINGS.get("xray", {}).get("stop_alert_min_weight", 3))
        for r in (self.engine.xray or {}).get("stops", []):
            k = f"stop_state:{r['sym']}"
            was = store.kv_get(k)
            store.kv_set(k, bool(r["breached"]))
            if r["breached"] and was is False and r["weight"] >= min_w:
                out.append(Alert(f"stop:{r['sym']}:{r['asof']}", "⚠️ WARNING", f"{r['sym']} 跌破波動停損線（{r['price']:.2f} < {r['stop']:.2f}）",
                                 f"權重 {r['weight']:.0f}%；22 日高點 {r['high']:.2f}，停損 = 高點 − 3×平均波幅。這是紀律提醒，不是賣出指令（/xray 看全部）"))
        return out

    def _liquidity_alerts(self) -> List[Alert]:
        """Heads-up the day before (or the day of) high-importance liquidity events."""
        out, today = [], datetime.now().date()
        for ev in self.engine.calendar.events:
            if ev.get("type") != "liquidity" or ev.get("importance", 0) < 3:
                continue
            d = datetime.fromisoformat(ev["date"]).date()
            if 0 <= (d - today).days <= 1:
                when = "明天" if (d - today).days == 1 else "今天"
                out.append(Alert(f"evt:{ev['id']}:{ev['date']}", "ℹ️ INFO", f"{when}：{ev['event']}（{ev['date']}）", ev.get("note", "")))
        return out

    def _gamma_alerts(self) -> List[Alert]:
        op = self.engine.options.spx
        if not A.get("gamma_flip") or not op or not op.get("zero_gamma"):
            return []
        below = op["spot"] < op["zero_gamma"]
        prev = store.kv_get("gamma_below")
        store.kv_set("gamma_below", below)
        if below and prev is False:
            return [Alert("gamma_flip", "⚠️ WARNING", f"SPX 跌破零 Gamma 翻轉點 {op['zero_gamma']:.0f}（現 {op['spot']:.0f}）",
                          "造市商進入負 Gamma：避險行為轉為順勢，日內波動放大機率上升")]
        return []

    async def _run_alerts(self, alerts: List[Alert]) -> None:
        cooldown = float(A.get("cooldown_minutes", 240)) * 60
        # a key that carries a bar-date / news-id / day / week ("sigma:^AXJO:2026-10-01:-1") already says "this event";
        # re-sending it every cooldown period just repeats the same alert → those are one-shot
        fire = [a for a in alerts if store.alert_allowed(a.key, ONE_SHOT_S if ":" in a.key else cooldown)]
        if not fire:
            return
        crit = any(a.severity.startswith("🚨") for a in fire)
        targets = await self._targets("alerts", crit)
        e = discord.Embed(title=("🚨 緊急風險警報" if crit else "⚠️ 市場警報"),
                          color=0xE74C3C if crit else 0xE67E22, timestamp=datetime.now(timezone.utc))
        spx = self.engine.market.q("^GSPC")
        for i, a in enumerate(fire):
            if i < 10:
                e.add_field(name=f"{a.severity} {a.title}"[:256], value=a.detail[:1024] or "—", inline=False)
            store.alert_mark(a.key, a.severity, a.title, kind=_alert_kind(a.key),
                             spx=spx["price"] if spx else None,
                             ssi=self.engine.stress.score if self.engine.stress else None)
        if self.engine.stress:
            st = self.engine.stress
            e.set_footer(text=f"SSI {st.score:.1f} {st.label} · /risk 看完整儀表")
        from . import slides as S
        ssi = self.engine.stress.score if self.engine.stress else None
        rows = [(a.severity, a.title, a.detail) for a in fire]
        links = [ln for a in fire for ln in a.detail.split("\n") if ln.startswith("http")]
        link_txt = ("🔗 " + "\n🔗 ".join(dict.fromkeys(links)))[:1900] if links else None
        for t in targets:
            await P.deliver(t, slides=lambda: S.deck_alert("緊急風險警報" if crit else "市場警報", rows, ssi),
                            embeds=lambda: e, content=link_txt if P.style() == "slides" else None)
        market_crit = [a for a in fire if a.severity.startswith("🚨") and not a.key.startswith("news:")]
        if market_crit and targets:
            self.spawn(self._alert_ai(fire, targets), "alert_ai")          # never block the quotes loop

    async def _alert_ai(self, fire: List[Alert], targets) -> None:
        pack = context.build(self.engine, "full")
        txt, eng_name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.ALERT.format(
            alerts="\n".join(f"- {a.title}: {a.detail}" for a in fire)), 1500)
        for t in targets:
            await P.deliver(t, text=txt, title="AI 緊急研判", engine_name=eng_name)

    async def _safe_send(self, target, **kw) -> None:
        try:
            await target.send(**kw)
            log.info("sent to %s", getattr(target, "recipient", None) or getattr(target, "name", target))
        except discord.Forbidden:
            log.warning("no permission to send to %s (DM closed or missing channel perms)", target)
        except Exception as e:  # noqa: BLE001
            log.warning("send failed to %s: %s", target, e)

    # ------------------------------------------------------------ briefings
    def _due(self, now: datetime, hhmm: str, weekdays, key: str, window_min: int = 60) -> bool:
        if weekdays is not None and now.weekday() not in weekdays:
            return False
        hh, mm = map(int, hhmm.split(":"))
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        return 0 <= (now - target).total_seconds() < window_min * 60 and not store.kv_get(key) and key not in self._sending

    async def _run_job(self, key: str, coro) -> None:
        """Mark a scheduled job as done only after it succeeded.  A failure (including 'AI unavailable') is retried every
        JOB_RETRY_S inside the window; the JOB_MAX_TRIES-th try delivers whatever it has so the day is never empty."""
        attempts = self.__dict__.setdefault("_job_attempts", {})
        n, last = attempts.get(key, (0, 0.0))
        if n and time.time() - last < JOB_RETRY_S:
            coro.close()                                  # not yet time to retry; never leave the coroutine un-awaited
            return
        attempts[key] = (n + 1, time.time())
        tok = JOB_FINAL.set(n + 1 >= JOB_MAX_TRIES)
        self._sending.add(key)
        try:
            await coro
            store.kv_set(key, True)
            attempts.pop(key, None)
        except AIUnavailable:
            log.warning("scheduled job %s: AI unavailable (try %d/%d) -> retry in %ds", key, n + 1, JOB_MAX_TRIES, JOB_RETRY_S)
        except Exception:  # noqa: BLE001
            log.exception("scheduled job %s failed (will retry)", key)
        finally:
            JOB_FINAL.reset(tok)
            self._sending.discard(key)

    @staticmethod
    def _ai_gate(engine_name: str) -> None:
        """Inside a retryable scheduled job, an AI outage must not be delivered (and marked done) as the day's report."""
        if engine_name == "none" and not JOB_FINAL.get():
            raise AIUnavailable()

    async def _briefing_tick(self) -> None:
        if not self.engine.ready:
            return
        if not getattr(self.engine, "full_ready", True) and time.time() - self._started < 900:
            return                                        # phase 2 (macro/news/options) still loading after a restart
        now = datetime.now(E.TZ)
        for b in SETTINGS.get("briefings", []):
            key = f"brief:{b['kind']}:{now:%Y%m%d}"
            if self._due(now, b["time"], b.get("weekdays"), key):
                targets = await self._targets("briefings")
                if targets:
                    self.spawn(self._run_job(key, self.send_briefing(targets, b["title"], b["kind"])), key)

        ew = SETTINGS.get("street", {}).get("weekly_board", {})
        key = f"earnboard:{now:%Y%m%d}"
        if ew and self._due(now, ew.get("time", "08:00"), [ew.get("weekday", 0)], key):
            tg = await self._targets("briefings")
            if tg:                                        # no destination -> don't mark it done
                self.spawn(self._run_job(key, self.send_earnings_board(tg)), key)

        wr = SETTINGS.get("weekly_report", {})
        key = f"weekly:{now:%G%V}"
        if wr and self._due(now, wr.get("time", "20:00"), [wr.get("weekday", 6)], key):
            async def _wk():
                await self.send_weekly(await self._targets("briefings"))
            self.spawn(self._run_job(key, _wk()), key)

        wk = SETTINGS.get("scorecard", {}).get("weekly", {})
        key = f"scorecard:{now:%Y%m%d}"
        if wk and self._due(now, wk.get("time", "20:00"), [wk.get("weekday", 6)], key):
            async def _sc():
                res = SC.evaluate(store.tracked_alerts(365), self.engine.market.series("^GSPC"))
                for t in await self._targets("briefings"):
                    await P.deliver(t, slides=lambda: _S().deck_scorecard(self.engine, res),
                                    embeds=lambda: E.scorecard(self.engine, res))
            self.spawn(self._run_job(key, _sc()), key)

    async def fomc_tick(self, force: bool = False, targets=None) -> Optional[str]:
        """After each FOMC decision: diff the statement against the previous one and send an AI tone read (once)."""
        pair = await FOMC.latest_pair()
        if not pair:
            return None
        d, new, pd_, prev = pair
        key = f"fomc_tone:{d.isoformat()}"
        if not force and store.kv_get(key):
            return None
        if not prev:
            return None
        df = FOMC.diff(prev, new)
        eng = self.engine
        pack = context.build(eng, "full")
        fmt_ = lambda xs: "\n".join(f"- {x}" for x in xs) or "（無）"          # noqa: E731
        txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.FOMC_TONE.format(
            date=d.isoformat(), prev_date=pd_.isoformat(), removed=fmt_(df["removed"][:12]), added=fmt_(df["added"][:12])), 2200)
        if name == "none" and not force:
            log.warning("FOMC tone: AI unavailable -> retry on the next fomc tick")
            return None
        for t in (targets or await self._targets("briefings")):
            await P.deliver(t, content=f"🏦 FOMC {d.isoformat()} 聲明與上次相似度 {df['similarity'] * 100:.0f}%（刪 {len(df['removed'])}／增 {len(df['added'])} 句）",
                            text=txt, title="FOMC 聲明語氣解讀", engine_name=name)
        store.kv_set(key, True)
        return txt

    async def send_weekly(self, targets) -> None:
        eng = self.engine
        sc = SC.evaluate(store.tracked_alerts(365), eng.market.series("^GSPC"))
        f = WK.facts(eng, None if sc.get("error") else sc)
        pack = context.build(eng, "full")
        txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.WEEKLY.format(facts=WK.facts_text(f)), 3000)
        self._ai_gate(name)
        for t in targets:
            await P.deliver(t, slides=lambda: CMD.deck_weekly(f),
                            embeds=lambda: CMD.embed_weekly(f), text=txt, title="每週復盤與下週展望", engine_name=name)
        store.kv_set("weekly_last", {"ts": time.time(), "stage": f.get("stage_idx"), "ssi": f.get("ssi")})

    async def send_morning(self, targets, title: str, session: str) -> None:
        eng = self.engine
        facts, txt, name = await MO.morning_call(eng, title, session)
        self._ai_gate(name)
        theme = MO.first_section(txt)
        for t in targets:
            await P.deliver(t, slides=lambda: _S().deck_morning(eng, facts, theme, title, session),
                            embeds=lambda: E.dashboard(eng), text=txt, title=f"{title}｜交易台觀點", engine_name=name)

    async def send_earnings_board(self, targets, private: bool = True) -> None:
        eng = self.engine
        board, txt, name = await MO.earnings_board(eng, private=private)
        self._ai_gate(name)
        for t in targets:
            await P.deliver(t, slides=lambda: _S().deck_earnings_board(board), text=txt,
                            title="華爾街財報季重點", engine_name=name)

    async def send_taiwan(self, targets, title: str = "台股籌碼情報") -> None:
        eng = self.engine
        if not eng.taiwan.flows and not eng.taiwan.futures:
            await eng.taiwan.refresh()
        pack = context.build(eng, "asia")
        txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.TAIWAN.format(
            title=title, extra="\n".join(eng.taiwan.summary_lines())), 2500)
        self._ai_gate(name)
        for t in targets:
            await P.deliver(t, slides=lambda: _S().deck_taiwan(eng, title), text=txt,
                            title=f"{title}｜AI 台股觀點", engine_name=name)

    async def send_briefing(self, targets, title: str, kind: str) -> None:
        if not isinstance(targets, (list, tuple)):
            targets = [targets]
        if kind == "taiwan":
            await self.send_taiwan(targets, title)
            return
        if kind in ("morning_call", "morning_recap"):
            session = "美股開盤前" if kind == "morning_call" else "美股收盤後・亞洲開盤前"
            await self.send_morning(targets, title, session)
            return
        focus = {"us_close": "us", "us_pre": "us", "asia_open": "asia", "europe": "europe",
                 "weekend": "full"}.get(kind, "full")
        pack = context.build(self.engine, focus)
        txt, eng_name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.FULL_BRIEF.format(title=title), 6000)
        self._ai_gate(eng_name)
        from . import slides as S
        for t in targets:
            await P.deliver(t, content=f"## 📡 {title}",
                            slides=lambda: S.deck_risk(self.engine, ("overview", "markets")),
                            embeds=lambda: [E.risk(self.engine), E.dashboard(self.engine)],
                            text=txt, title=f"{title}｜首席策略師研判", engine_name=eng_name)


def _S():
    from . import slides
    return slides


VOL_LIKE = {"^VIX", "^VIX9D", "^VIX3M", "^VVIX", "^MOVE", "^SKEW", "DX-Y.NYB", "GC=F", "TLT", "IEF", "SHY"}
SAFE_HAVEN_FX = {"JPY=X", "CHF=X"}   # USD/JPY falling = yen strength = risk-off


def _alert_kind(key: str) -> Optional[str]:
    """Classify an alert for the scorecard: 'risk' (should precede weakness), 'news', or None (info)."""
    if key.startswith(("ssi_level", "ssi_jump", "vix_backwardation", "gamma_flip", "pf_dd", "playbook:", "shock:", "regime:",
                       "intel:confirm:", "intel:level:")):
        return "risk"
    if key.startswith("news:"):
        return "news"
    if key.startswith("sigma:"):
        _, t, _, sign = key.split(":", 3) if key.count(":") >= 3 else (None, None, None, "0")
        sign = int(sign)
        if (t in VOL_LIKE and sign > 0) or (t in SAFE_HAVEN_FX and sign < 0) or \
                (t not in VOL_LIKE and t not in SAFE_HAVEN_FX and sign < 0):
            return "risk"
    return None


# ======================================================================
#   Slash commands
# ======================================================================
FOCUS = [app_commands.Choice(name=n, value=v) for n, v in
         [("全球總覽", "full"), ("美國", "us"), ("亞洲", "asia"), ("歐洲", "europe"),
          ("總經/利率", "macro"), ("加密", "crypto"), ("我的持倉", "portfolio")]]
GROUPS = [app_commands.Choice(name=E.GROUP_TITLES[g], value=g) for g in E.GROUP_TITLES]


def _ticker_stats(s: pd.Series, spy: pd.Series) -> dict:
    s = s.dropna()
    r = np.log(s).diff().dropna()
    out = {"price": float(s.iloc[-1]), "d1": float(s.iloc[-1] / s.iloc[-2] - 1) * 100}
    for lbl, n in (("1M", 21), ("3M", 63), ("1Y", 252)):
        if len(s) > n:
            out[lbl] = float(s.iloc[-1] / s.iloc[-n - 1] - 1) * 100
    out["vol20_ann"] = float(r.iloc[-20:].std() * math.sqrt(252) * 100)
    out["sigma"] = float(r.iloc[-1] / r.iloc[-61:-1].std()) if len(r) > 61 else None
    hi = s.iloc[-252:].max()
    out["from_52w_high"] = float(s.iloc[-1] / hi - 1) * 100
    for n in (50, 200):
        if len(s) >= n:
            out[f"vs_ma{n}"] = float(s.iloc[-1] / s.iloc[-n:].mean() - 1) * 100
    d = s.diff()
    up, dn = d.clip(lower=0).ewm(alpha=1 / 14).mean(), (-d.clip(upper=0)).ewm(alpha=1 / 14).mean()
    out["rsi14"] = float(100 - 100 / (1 + up.iloc[-1] / dn.iloc[-1])) if dn.iloc[-1] else 100.0
    if len(spy) > 60:
        j = pd.concat([r, np.log(spy).diff()], axis=1).dropna().iloc[-252:]
        if len(j) > 60:
            out["beta_1y"] = float(j.cov().iloc[0, 1] / j.iloc[:, 1].var())
            out["corr_1y"] = float(j.corr().iloc[0, 1])
    return out


# commands anyone in the server may use; everything else (holdings, AI briefs, control) is owner-only
PUBLIC_COMMANDS = {"dashboard", "risk", "crash", "market", "macro", "gamma", "news", "calendar", "quote",
                   "scorecard", "earnings_week", "shock", "intel", "alert", "alerts", "alert_remove", "status"}


def _owner_id() -> str:
    return str(store.kv_get("owner_id") or OWNER_USER_ID or "")


def is_owner(it: discord.Interaction) -> bool:
    oid = _owner_id()
    if oid:
        return str(it.user.id) == oid
    # no owner configured yet → server admins only
    return bool(it.guild and getattr(it.user, "guild_permissions", None) and it.user.guild_permissions.manage_guild)


def register_commands(bot: Sentinel) -> None:
    tree, eng = bot.tree, bot.engine

    async def _check(it: discord.Interaction) -> bool:
        name = it.command.name if it.command else str((it.data or {}).get("name", ""))
        if name in PUBLIC_COMMANDS or is_owner(it):
            return True
        await it.response.send_message("🔒 這個指令只限 bot 擁有者使用（涉及持倉或 bot 控制）。", ephemeral=True)
        return False
    tree.interaction_check = _check  # type: ignore[assignment]

    @tree.error
    async def _on_error(it: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return
        log.error("command %s failed", it.command.name if it.command else "?", exc_info=error)
        msg = "❌ 指令執行失敗，已記錄錯誤。可用 /status 查看資料源狀態。"
        try:
            if it.response.is_done():
                await it.followup.send(msg, ephemeral=True)
            else:
                await it.response.send_message(msg, ephemeral=True)
        except Exception:  # noqa: BLE001
            pass

    async def ready_or_wait(it: discord.Interaction) -> bool:
        if not eng.ready and eng.stress is None:
            await it.followup.send("⏳ 資料引擎首次啟動中（下載全球 20 年歷史約 1–3 分鐘），請稍後再試。")
            return False
        return True

    @tree.command(name="dashboard", description="全球金融戰情室：壓力指數 + 全資產即時總覽")
    async def dashboard(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: _S().deck_risk(eng, ("overview", "markets")), embeds=lambda: E.dashboard(eng))

    @tree.command(name="risk", description="系統性壓力指數 SSI：區塊、推升因子、崩跌機率")
    async def risk(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: _S().deck_risk(eng, ("overview", "blocks", "trend", "crash")), embeds=lambda: E.risk(eng))

    @tree.command(name="crash", description="崩跌機率實證回測（依目前壓力區間）")
    async def crash(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: _S().deck_risk(eng, ("crash",)), embeds=lambda: E.crash(eng))

    @tree.command(name="command", description="戰情總控台：風險階段、衝擊雷達、風險劇本行動清單、事件日曆")
    async def command(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: CMD.deck_command(eng), embeds=lambda: CMD.embed_command(eng))

    @tree.command(name="shock", description="衝擊雷達：下一次金融衝擊可能從哪裡點火 + 模型歷史準確度")
    async def shock(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: CMD.deck_shock(eng), embeds=lambda: CMD.embed_shock(eng))

    @tree.command(name="intel", description="情報融合：新聞情報 × 市場價格 × 總經象限 → 綜合風險判斷與證據帳本")
    @app_commands.describe(ai="加上 AI 情報融合研判（僅擁有者）")
    async def intel(it: discord.Interaction, ai: bool = False):
        await it.response.defer(thinking=True)
        if not await ready_or_wait(it):
            return
        txt, name = None, ""
        if ai and is_owner(it):
            pack = context.build(eng, "full")
            txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.INTEL, 4000)
        elif ai:
            await it.followup.send("🔒 AI 研判僅限擁有者；以下為數據版。", ephemeral=True)
        await P.deliver(it, slides=lambda: CMD.deck_intel(eng), embeds=lambda: CMD.embed_intel(eng),
                        text=txt, title="情報融合研判", engine_name=name)

    @tree.command(name="market", description="查看某一資產類別的即時全表")
    @app_commands.choices(group=GROUPS)
    async def market(it: discord.Interaction, group: app_commands.Choice[str]):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: P.v_market_group(eng, group.value), embeds=lambda: E.market_group(eng, group.value))

    @tree.command(name="macro", description="總經象限 + FRED 信用/流動性/利率/就業/通膨")
    async def macro(it: discord.Interaction):
        await it.response.defer(thinking=True)
        await P.deliver(it, slides=lambda: P.v_macro(eng), embeds=lambda: E.macro(eng))

    @tree.command(name="gamma", description="SPX 選擇權造市商 Gamma、零Gamma翻轉點、Put/Call 牆")
    async def gamma(it: discord.Interaction):
        await it.response.defer(thinking=True)
        await P.deliver(it, slides=lambda: P.v_gamma(eng), embeds=lambda: E.options(eng))

    @tree.command(name="portfolio", description="持倉風險駕駛艙：VaR、β、風險貢獻、集中度")
    async def portfolio(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: _S().deck_portfolio(eng)[:-1], embeds=lambda: E.portfolio(eng))

    @tree.command(name="xray", description="持倉 X 光：獨立押注數、相關群聚、自訂情境、波動停損線、事件暴露")
    async def xray(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: CMD.deck_xray(eng), embeds=lambda: CMD.embed_xray(eng))

    @tree.command(name="stresstest", description="用真實歷史危機價格重播你的持倉")
    async def stresstest(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if await ready_or_wait(it):
            await P.deliver(it, slides=lambda: _S().deck_portfolio(eng)[-1:], embeds=lambda: E.stress_test(eng))

    @tree.command(name="news", description="全球金融情報流（依風險分數排序，可搜尋）")
    @app_commands.describe(query="關鍵字（選填），例如 Fed、yen、Nvidia", latest="改用最新時間排序")
    async def news(it: discord.Interaction, query: Optional[str] = None, latest: bool = False):
        await it.response.defer(thinking=True)
        await P.deliver(it, slides=lambda: P.v_news(eng, query, latest), embeds=lambda: E.news(eng, query, latest))

    @tree.command(name="calendar", description="未來 14 天：FOMC、CPI/非農等總經數據、持股財報")
    async def calendar(it: discord.Interaction):
        await it.response.defer(thinking=True)
        await P.deliver(it, slides=lambda: P.v_calendar(eng), embeds=lambda: E.calendar(eng))

    @tree.command(name="quote", description="任一標的機構級快速診斷（全球代號，如 NVDA、2330.TW、^N225、BTC-USD）")
    @app_commands.describe(ticker="Yahoo Finance 代號", ai="是否加上 AI 研判")
    async def quote(it: discord.Interaction, ticker: str, ai: bool = False):
        await it.response.defer(thinking=True)
        t = ticker.strip().upper()
        try:
            s = eng.market.series(t)
            if len(s) < 60:
                s = await fetch_single(t, "2y")
            info = await fetch_info(t)
            st = _ticker_stats(s, eng.market.series("SPY"))
        except Exception as ex:  # noqa: BLE001
            await it.followup.send(f"❌ 無法取得 {t}：{ex}")
            return
        e = discord.Embed(title=f"🔎 {info.get('shortName', t)} ({t})", color=0x2980B9)
        f = context.f
        e.description = (f"`{f(st['price'])}` **{f(st['d1'],2,pct=True,sign=True)}** σ{f(st.get('sigma'),1,sign=True)}\n"
                         f"1M {f(st.get('1M'),1,pct=True,sign=True)} · 3M {f(st.get('3M'),1,pct=True,sign=True)} · 1Y {f(st.get('1Y'),1,pct=True,sign=True)}\n"
                         f"距52週高 {f(st['from_52w_high'],1,pct=True)} · vs MA50 {f(st.get('vs_ma50'),1,pct=True,sign=True)} · vs MA200 {f(st.get('vs_ma200'),1,pct=True,sign=True)}\n"
                         f"RSI14 {f(st['rsi14'],0)} · 20日年化波動 {f(st['vol20_ann'],0)}% · β {f(st.get('beta_1y'))} · 相關 {f(st.get('corr_1y'))}")
        if info:
            e.add_field(name="基本面", value="\n".join(f"{k}: {v}" for k, v in info.items() if k != "shortName")[:1024])
        txt, name = None, ""
        if ai and not is_owner(it):                       # AI runs on the owner's credits and sees holdings
            await it.followup.send("🔒 AI 研判僅限擁有者；以下為數據版。", ephemeral=True)
            ai = False
        if ai:
            pack = context.build(eng, "us")
            txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.TICKER.format(
                t=t, extra=json.dumps({**st, **info}, ensure_ascii=False, default=str)), 2000)
        await P.deliver(it, slides=lambda: P.v_quote(t, info.get("shortName", t), st, info),
                        embeds=lambda: E.footer(e, eng), text=txt, title=f"{t} AI 研判", engine_name=name)

    @tree.command(name="brief", description="首席策略師完整研判（AI + 全部即時數據）")
    @app_commands.choices(focus=FOCUS)
    async def brief(it: discord.Interaction, focus: Optional[app_commands.Choice[str]] = None):
        await it.response.defer(thinking=True)
        if not await ready_or_wait(it):
            return
        fv = focus.value if focus else "full"
        pack = context.build(eng, fv)
        txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.FULL_BRIEF.format(
            title=f"{focus.name if focus else '全球總覽'} 戰略簡報"), 6000)
        await P.deliver(it, slides=lambda: _S().deck_risk(eng, ("overview",)), embeds=lambda: E.risk(eng),
                        text=txt, title=f"{focus.name if focus else '全球總覽'}｜首席策略師研判", engine_name=name)

    @tree.command(name="fomc", description="最近一次 FOMC 聲明 vs 上次：逐句差異與 AI 鷹鴿語氣解讀")
    async def fomc(it: discord.Interaction):
        await it.response.defer(thinking=True)
        try:
            pair = await FOMC.latest_pair(max_age_days=200)
        except Exception as e:  # noqa: BLE001
            await it.followup.send(f"❌ 無法取得聯準會行事曆：{str(e)[:80]}")
            return
        if not pair or not pair[3]:
            await it.followup.send("目前抓不到最近兩次 FOMC 聲明（聯準會網站格式或網路問題），稍後再試。")
            return
        d, new, pd_, prev = pair
        df = FOMC.diff(prev, new)
        fmt_ = lambda xs: "\n".join(f"- {x}" for x in xs) or "（無）"          # noqa: E731
        txt, name = await llm.complete(prompts.SYSTEM, context.build(eng, "full") + "\n\n" + prompts.FOMC_TONE.format(
            date=d.isoformat(), prev_date=pd_.isoformat(), removed=fmt_(df["removed"][:12]), added=fmt_(df["added"][:12])), 2200)
        await P.deliver(it, content=f"🏦 FOMC {d.isoformat()} vs {pd_.isoformat()}：相似度 {df['similarity'] * 100:.0f}%",
                        text=txt, title="FOMC 聲明語氣解讀", engine_name=name)

    @tree.command(name="ask", description="用全部即時數據回答你的任何金融問題（可連續追問，reset=True 開新話題）")
    async def ask(it: discord.Interaction, question: str, reset: bool = False):
        await it.response.defer(thinking=True)
        if not await ready_or_wait(it):
            return
        uid = it.user.id
        hist = [] if reset else [h for h in bot._ask_hist.get(uid, []) if time.time() - h[0] < 2700]
        ctx = ""
        if hist:
            ctx = "【先前對話（供追問參考，數據一律以 DATA PACK 為準）】\n" + "\n".join(
                f"Q: {q}\nA: {a[:700]}" for _, q, a in hist[-3:]) + "\n\n"
        pack = context.build(eng, "full")
        txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + ctx + prompts.QA.format(q=question), 2500)
        bot._ask_hist[uid] = (hist + [(time.time(), question, txt)])[-3:]
        await P.deliver(it, content=f"> {question}" + ("（接續上文）" if hist else ""), text=txt, title="你的提問｜AI 解答", engine_name=name)

    @tree.command(name="weekly", description="每週復盤：本週回顧、持倉歸因、警報成績、下週事件（AI 評論）")
    async def weekly(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if not await ready_or_wait(it):
            return
        sc = SC.evaluate(store.tracked_alerts(365), eng.market.series("^GSPC"))
        f = WK.facts(eng, None if sc.get("error") else sc)
        txt, name = await llm.complete(prompts.SYSTEM, context.build(eng, "full") + "\n\n" + prompts.WEEKLY.format(facts=WK.facts_text(f)), 3000)
        await P.deliver(it, slides=lambda: CMD.deck_weekly(f), embeds=lambda: CMD.embed_weekly(f), text=txt,
                        title="每週復盤與下週展望", engine_name=name)

    @tree.command(name="status", description="資料源健康狀態 + 近 24 小時警報")
    async def status(it: discord.Interaction):
        await it.response.send_message(embed=E.status(eng))

    @tree.command(name="setchannel", description="把目前頻道設為 警報 / 定時簡報 推播頻道")
    @app_commands.choices(kind=[app_commands.Choice(name="即時警報", value="alerts"),
                                app_commands.Choice(name="定時簡報", value="briefings")])
    async def setchannel(it: discord.Interaction, kind: app_commands.Choice[str]):
        if it.guild and not it.user.guild_permissions.manage_guild:
            await it.response.send_message("❌ 需要「管理伺服器」權限", ephemeral=True)
            return
        store.kv_set(f"{kind.value}_channel", it.channel_id)
        where = "私訊" if it.guild is None else f"<#{it.channel_id}>"
        await it.response.send_message(f"✅ 已將 {where} 設為 **{kind.name}** 推播目的地")

    @tree.command(name="dmme", description="把我設為私訊收件人：簡報與警報都會私訊給我")
    @app_commands.choices(alerts=[app_commands.Choice(name="全部警報", value="all"),
                                  app_commands.Choice(name="只有緊急警報", value="critical"),
                                  app_commands.Choice(name="不私訊警報", value="none")])
    async def dmme(it: discord.Interaction, alerts: Optional[app_commands.Choice[str]] = None,
                   briefings: bool = True):
        owner = store.kv_get("owner_id") or OWNER_USER_ID
        if owner and str(owner) != str(it.user.id):
            await it.response.send_message("❌ 私訊收件人已設定為其他使用者", ephemeral=True)
            return
        store.kv_set("owner_id", str(it.user.id))
        d = SETTINGS.raw.setdefault("delivery", {})
        d["dm_alerts"] = alerts.value if alerts else d.get("dm_alerts", "all")
        d["dm_briefings"] = briefings
        store.kv_set("delivery", d)
        await it.response.send_message(
            f"✅ 之後會私訊給你：定時簡報 **{'開' if briefings else '關'}**、警報 **{alerts.name if alerts else d['dm_alerts']}**", ephemeral=True)
        try:
            await it.user.send("👋 WallStreet Sentinel 私訊測試：你會在這裡收到簡報與警報。輸入 `/testbrief` 可立即產生一份簡報。")
        except discord.Forbidden:
            await it.followup.send("⚠️ 我無法私訊你：請到該伺服器的「隱私設定」開啟「允許來自伺服器成員的私人訊息」", ephemeral=True)

    @tree.command(name="mute", description="暫停警報推播 N 分鐘（0 = 解除）")
    @app_commands.default_permissions(manage_guild=True)
    async def mute(it: discord.Interaction, minutes: app_commands.Range[int, 0, 1440]):
        store.kv_set("mute_until", time.time() + minutes * 60)
        await it.response.send_message("🔕 已靜音 %d 分鐘" % minutes if minutes else "🔔 警報已恢復")

    @tree.command(name="refresh", description="立即強制刷新全部資料源")
    @app_commands.default_permissions(manage_guild=True)
    async def refresh(it: discord.Interaction):
        await it.response.defer(thinking=True)
        ex = eng.holding_tickers()
        await asyncio.gather(eng.market.refresh_quotes(ex), eng.fred.refresh(), eng.crypto.refresh(),
                             eng.options.refresh(), eng.news.refresh(), return_exceptions=True)
        await eng.recompute()
        await it.followup.send("✅ 已刷新", embed=E.status(eng))

    @tree.command(name="hedge", description="避險成本計算器：保護持倉要花多少、跌 10%/20% 能拿回多少")
    async def hedge(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if not await ready_or_wait(it):
            return
        chains = {}
        for u in ("SPY", "QQQ"):
            try:
                chains[u] = await fetch_chain(u)
            except Exception as ex:  # noqa: BLE001
                log.warning("chain %s failed: %s", u, ex)
        if not chains:
            await it.followup.send("❌ 無法取得 CBOE 選擇權報價，稍後再試")
            return
        res = HG.analyze(eng.portfolio, chains, eng.stress.score if eng.stress else None)
        await P.deliver(it, slides=lambda: _S().deck_hedge(eng, res), embeds=lambda: E.hedge(eng, res))

    @tree.command(name="scorecard", description="警報成績單：警報發出後大盤真的跌了嗎？（對比歷史基準機率）")
    async def scorecard(it: discord.Interaction):
        await it.response.defer(thinking=True)
        res = SC.evaluate(store.tracked_alerts(365), eng.market.series("^GSPC"))
        await P.deliver(it, slides=lambda: _S().deck_scorecard(eng, res), embeds=lambda: E.scorecard(eng, res))

    @tree.command(name="earnings", description="持股財報：即將公布的隱含波動，或最新一次財報的 AI 快評")
    @app_commands.describe(ticker="美股代號，例如 NVDA", mode="preview=財報前預告 / review=最新財報快評")
    @app_commands.choices(mode=[app_commands.Choice(name="財報快評（最新一次）", value="review"),
                                app_commands.Choice(name="財報前預告（隱含波動）", value="preview")])
    async def earnings(it: discord.Interaction, ticker: str, mode: Optional[app_commands.Choice[str]] = None):
        await it.response.defer(thinking=True)
        t = ticker.strip().upper()
        if mode and mode.value == "preview":
            ev = next((e for e in eng.calendar.events if e.get("ticker") == t), None)
            if not ev:
                await it.followup.send(f"找不到 {t} 未來 60 天的財報日期（只追蹤持股）")
                return
            from ..data.options import implied_move
            try:
                im = implied_move(await fetch_chain(t), ev["date"])
            except Exception as ex:  # noqa: BLE001
                im = None
                log.warning("implied %s: %s", t, ex)
            pos = next((p for p in (eng.portfolio or {}).get("positions", []) if p.get("sym") == t), {})
            rec = {"ticker": t, "date": ev["date"], "implied": im, "value": pos.get("value_usd", 0.0),
                   "shares": pos.get("shares")}
            store.kv_set(f"implied_last:{t}", rec)
            ptxt = await ER.preview_text(eng, rec)
            await P.deliver(it, slides=lambda: P.v_earnings_preview(eng, rec), embeds=lambda: E.earnings_preview(eng, rec),
                            text=ptxt, title=f"{t} 財報前預告")
            return
        item = await ER.latest_release(eng, t)
        if not item:
            await it.followup.send(f"找不到 {t} 近期的財報申報（8-K Item 2.02 / 6-K）")
            return
        await P.deliver(it, text=await ER.analyze_release(eng, item), title=f"{t} 財報快評")

    @tree.command(name="morning", description="華爾街晨會簡報：隔夜市場、板塊輪動、異動、今日財報與交易點子")
    async def morning(it: discord.Interaction):
        await it.response.defer(thinking=True)
        if not await ready_or_wait(it):
            return
        await bot.send_morning([it], "華爾街晨會簡報", "即時")

    @tree.command(name="taiwan", description="台股籌碼情報：三大法人、外資期貨、台指期日夜盤、權值股月營收")
    async def taiwan_cmd(it: discord.Interaction):
        await it.response.defer(thinking=True)
        await bot.send_taiwan([it])

    @tree.command(name="earnings_week", description="華爾街財報季看板：本週重要財報 + 上週超預期/不如預期與股價反應")
    async def earnings_week(it: discord.Interaction):
        await it.response.defer(thinking=True)
        await bot.send_earnings_board([it], private=is_owner(it))

    ALERT_OPS = [app_commands.Choice(name="價格高於", value="above"), app_commands.Choice(name="價格低於", value="below"),
                 app_commands.Choice(name="單日漲幅達 %", value="up_pct"), app_commands.Choice(name="單日跌幅達 %", value="down_pct")]

    @tree.command(name="alert", description="設定價格警示（觸發後私訊你一次）例：NVDA 價格低於 165")
    @app_commands.describe(ticker="Yahoo 代號，如 NVDA、2330.TW、^VIX、^TNX", condition="條件", value="數值（價格或 %）",
                           note="備註（選填），例如「跌破就加碼」")
    @app_commands.choices(condition=ALERT_OPS)
    async def alert(it: discord.Interaction, ticker: str, condition: app_commands.Choice[str], value: float,
                    note: Optional[str] = None):
        await it.response.defer(ephemeral=True, thinking=True)
        t = ticker.strip().upper()
        if t.isdigit() and len(t) == 4:
            t += ".TW"                                   # 台股代號自動補 .TW
        q = eng.market.q(t)
        price = q["price"] if q else None
        if price is None:
            try:
                ser = await fetch_single(t, "5d")
                price = float(ser.dropna().iloc[-1]) if len(ser.dropna()) else None
            except Exception:  # noqa: BLE001
                price = None
        if price is None:
            await it.followup.send(f"❌ 找不到 **{t}** 的報價。請用 Yahoo 代號，例如 NVDA、2330.TW、^VIX、BTC-USD。", ephemeral=True)
            return
        aid = store.palert_add(str(it.user.id), t, condition.value, value, note or "")
        await it.followup.send(f"✅ 警示 #{aid} 已設定：**{t} {condition.name} {value:g}**（現價 {price:.4g}）", ephemeral=True)

    @tree.command(name="alerts", description="查看我設定中的價格警示")
    async def alerts_list(it: discord.Interaction):
        rows = store.palert_list(str(it.user.id))
        names = {c.value: c.name for c in ALERT_OPS}
        if not rows:
            await it.response.send_message("目前沒有設定中的價格警示。用 `/alert` 新增。", ephemeral=True)
            return
        lines = []
        for aid, _, t, op, val, note, *_ in rows:
            q = eng.market.q(t)
            lines.append(f"#{aid}　**{t}** {names.get(op, op)} {val:g}" + (f"　現價 {q['price']:.4g}" if q else "") +
                         (f"　_{note}_" if note else ""))
        await it.response.send_message("\n".join(lines) + "\n\n刪除：`/alert_remove 編號`", ephemeral=True)

    @tree.command(name="alert_remove", description="刪除一個價格警示")
    async def alert_remove(it: discord.Interaction, alert_id: int):
        ok = store.palert_remove(alert_id, str(it.user.id))
        await it.response.send_message("🗑️ 已刪除" if ok else "找不到這個編號（或不是你的警示）", ephemeral=True)

    @tree.command(name="style", description="切換呈現方式：投影片大字圖卡 / 傳統 Discord 卡片")
    @app_commands.choices(mode=[app_commands.Choice(name="投影片（大字）", value="slides"),
                                app_commands.Choice(name="傳統卡片", value="classic")])
    async def style_cmd(it: discord.Interaction, mode: app_commands.Choice[str]):
        store.kv_set("style", mode.value)
        await it.response.send_message(f"✅ 之後改用：**{mode.name}**", ephemeral=True)

    @tree.command(name="restart", description="重新啟動 bot（套用新設定/程式碼）")
    async def restart(it: discord.Interaction):
        owner = store.kv_get("owner_id") or OWNER_USER_ID
        if str(it.user.id) != str(owner) and not (it.guild and it.user.guild_permissions.manage_guild):
            await it.response.send_message("❌ 無權限", ephemeral=True)
            return
        (DATA_DIR / "restart.flag").write_text("1", encoding="utf-8")
        await it.response.send_message("♻️ 將在 1 分鐘內重新啟動（由守護程式自動拉起）", ephemeral=True)

    @tree.command(name="testbrief", description="立即產生一次簡報並推播到所有設定的目的地（頻道/私訊）")
    async def testbrief(it: discord.Interaction):
        await it.response.send_message("📡 產生中（AI 研判約需 30–90 秒）…")
        targets = await bot._targets("briefings")
        if it.channel and all(getattr(t, "id", None) != it.channel_id for t in targets):
            targets.append(it.channel)
        await bot.send_briefing(targets, "手動測試簡報", "us_pre")
