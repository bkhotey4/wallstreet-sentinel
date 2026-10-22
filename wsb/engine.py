"""Central intelligence engine: owns every data feed + analytics results and
exposes a single consistent snapshot to the Discord layer and the AI."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List, Optional

from .analytics import crash_odds as co
from .analytics import hedge as hg
from .analytics import intel as it
from .analytics import exposure as ex
from .analytics import outlook as ol
from .analytics import lab as lb
from .analytics import playbook as pb
from .analytics import portfolio as pf
from .analytics import regime as rg
from .analytics import shock as sk
from .analytics import xray as xr
from .analytics import valuation as va
from .analytics import stockscore as ss
from .analytics import breadth as bd
from .analytics import signals as sg
from .analytics import macro_events as me
from .analytics import earn_verdict as ev
from .analytics import canary as cn
from .analytics import distress as dz
from .analytics import rulebook as rb
from .analytics import focus as fc
from .data import fedwatch as fw
from .analytics import techearn as te
from .analytics.stress import StressEngine, StressResult
from .config import SETTINGS
from .data.calendar import EventCalendar
from .data.crypto import CryptoSentiment
from .data.fred import FredData
from .data.market import MarketData
from .data.news import NewsWire
from .ai.news_ai import NewsClassifier
from .data.options import OptionsPositioning
from .data.sec import SecWatcher
from .data.taiwan import TaiwanData
from .data.darkpool import DarkPool
from .data.stocks import StockPrices
from .data.stocknews import StockNews
from .data.edgar_holdings import Gurus, Insiders
from .data.treasury import Treasury
from .data.econcal import EconCalendar
from .data.earnings_data import EarningsData
from .data import treasury as tsy
from . import store

log = logging.getLogger(__name__)


class Engine:
    def __init__(self) -> None:
        self.market = MarketData()
        self.fred = FredData()
        self.crypto = CryptoSentiment()
        self.news = NewsWire()
        self.news_ai = NewsClassifier()
        self.options = OptionsPositioning()
        self.sec = SecWatcher()
        self.calendar = EventCalendar()
        self.taiwan = TaiwanData()
        self.darkpool = DarkPool()
        self.stockprices = StockPrices()
        self.stocknews = StockNews()
        self.gurus = Gurus()
        self.insiders = Insiders()
        self.treasury = Treasury()
        self.econ = EconCalendar()
        self.earnings = EarningsData()
        self.stress_engine = StressEngine(self.market, self.fred)
        self.stress: Optional[StressResult] = None
        self.odds: Dict = {}
        self.shock: Dict = {}
        self.lab: Dict = {}
        self.model_health: Dict = {}
        self.factors: Dict = {}                          # 風格因子模型 (public per-symbol loadings, factor returns)
        self.dispersion: Dict = {}
        self.sector_health: Dict = {}
        self.real_economy: Dict = {}
        try:                                             # 華爾街機構觀點（背景）: cached public titles + CFTC positioning
            from .data import street_views as _sv
            self.street: Dict = _sv.load()
        except Exception:  # noqa: BLE001
            self.street = {}                       # 指數 vs 個股: index-vs-median gap, Cboe implied correlation / dispersion
        try:                                             # 營收曝險 (SEC annual reports): cached parse, refreshed slowly
            from .data import segments as _sg
            self.segments: Dict = _sg.public(_sg.load())
        except Exception:  # noqa: BLE001
            self.segments = {}
        self.xray: Dict = {}
        self.valuation: Dict = {}
        self.scores: Dict = {}            # 個股評分表（美股／台股／港股）
        self.bonds: Dict = {}             # 美債專區（殖利率曲線、期限溢價、標售）
        self.rotation: Dict = {}          # 類股輪動與市場寬度
        self.signals: Dict = {}           # 技術面買點訊號（規則篩選）
        self.econ_view: Dict = {}         # 財經日曆（FOMC、CPI、PPI…＋影響劇本）
        from .data.fedwatch import FedWatch
        self.fedwatch = FedWatch()        # 聯邦基金期貨 → FOMC 結果機率
        self.fedwatch_view: Dict = {}
        self.earn_verdict: Dict = {}      # 財報結論
        from .data.finra import MarginDebt
        self.margin_debt = MarginDebt()   # FINRA 融資餘額（月）
        self.canary: Dict = {}            # 金絲雀燈號
        self.distress: Dict = {}          # 企業危機雷達
        self.rulebook: Dict = {}          # 我的持股規則檢查（私人）
        self.focus: Dict = {}             # 華爾街關注焦點
        self.techearn: Dict = {}          # 科技／半導體財報分析
        self._quality: Optional[Dict] = None
        self._quality_ts = 0.0
        self.regime: Dict = {}
        self.intel: Dict = {}
        self.outlook: Dict = {}          # 全方位風險展望 (all dimensions + forecasts)
        self.exposure: Dict = {}         # holdings × shock-path sensitivity (private)
        self.breaks: Dict = {}
        self.playbook: Dict = {}
        self.portfolio: Dict = {}
        self.holdings: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self.ready = False
        self.full_ready = False          # phase 2 (macro/news/options/taiwan) loaded
        self.site_mode = False           # set by tools.build_site: headless build that runs earnings itself
        self.recompute_ts = 0.0          # when recompute() last finished (heartbeat / health)

    # ------------------------------------------------------------------
    def holding_tickers(self) -> List[str]:
        return list(self.holdings.keys())

    async def bootstrap(self) -> None:
        """Phase 1: prices only → usable within ~1-2 min. Phase 2: everything else."""
        self.holdings = pf.load_holdings()
        extra = self.holding_tickers()
        wanted = set(self.market.tickers) | set(extra)
        h = self.market.history
        missing = {t for t in wanted if t not in h.columns or h[t].notna().sum() == 0}
        missing -= self.market.recently_failed()        # Yahoo had nothing for these lately → no full rebuild over them
        if self.market.history_is_stale() or (missing and self.market.history_age_hours > 1):
            log.info("history rebuild: stale=%s missing=%d (%s)", self.market.history_is_stale(), len(missing),
                     ", ".join(sorted(missing)[:8]))
            await self.market.refresh_history(extra)
        await self.market.refresh_quotes(extra)
        # site build: the model-quality backtest + feature lab run once, after phase 2 (they'd be redone anyway)
        await self.recompute(skip_quality=self.site_mode)
        self.ready = True
        log.info("phase 1 ready (prices)")
        tmo = float(SETTINGS.get("engine", {}).get("feed_timeout_s", 300))
        feeds = (("fred", self.fred.refresh()), ("crypto", self.crypto.refresh()), ("options", self.options.refresh()),
                 ("news", self.news.refresh()), ("calendar", self.calendar.refresh(extra)),
                 ("sec", self.sec.refresh([t for t in extra if "." not in t])),
                 ("taiwan", self.taiwan.refresh()), ("darkpool", self.darkpool.refresh(self.market)),
                 ("stocks", self.stockprices.refresh()), ("stocknews", self.stocknews.refresh()),
                 ("treasury", self.treasury.refresh()), ("edgar", self.refresh_edgar()), ("econ", self.econ.refresh()),
                 ("fedwatch", self.fedwatch.refresh()), ("finra", self.margin_debt.refresh()),
                 ("distress", self.refresh_distress()))
        # each feed gets its own timeout: one hung source can't hold phase 2 (and the bot's loops) forever
        res = await asyncio.gather(*(asyncio.wait_for(c, tmo) for _, c in feeds), return_exceptions=True)
        if not self.site_mode:                           # the site build forces its own (frames) earnings refresh later
            try:
                await asyncio.wait_for(self.refresh_earnings(), float(SETTINGS.get("engine", {}).get("earnings_timeout_s", 240)))
            except Exception as e:  # noqa: BLE001
                log.warning("phase-2 refresh earnings failed: %s", e if str(e) else type(e).__name__)
        for (nm, _), r in zip(feeds, res):
            if isinstance(r, asyncio.TimeoutError):
                log.warning("phase-2 refresh %s timed out after %.0fs", nm, tmo)
            elif isinstance(r, Exception):
                log.warning("phase-2 refresh %s failed: %s", nm, r)
        try:                                              # bounded: a hung AI call must never block the whole bootstrap
            await asyncio.wait_for(self.news_ai.classify_all(self.news.items), 300)
        except asyncio.TimeoutError:
            log.warning("news AI classify timed out at bootstrap (continuing without tags)")
        except Exception:  # noqa: BLE001
            log.exception("news AI classify failed")
        self._quality = None            # phase-1 quality/lab ran without FRED inputs → recompute on the full index
        await self.recompute()
        self.full_ready = True
        log.info("phase 2 ready (macro/news/options/taiwan)")

    async def refresh_edgar(self, force: bool = False) -> None:
        """13F first, then Form 4 (which also hands the 13F matcher the SEC company names of the scoring universe)."""
        try:
            await self.gurus.refresh(force)
        finally:
            await self.insiders.refresh(force, gurus=self.gurus)

    def tech_symbols(self) -> List[str]:
        from .data.earnings_data import TECH_THEMES
        from .data.stocks import universe
        us = universe().get("us") or {}
        return [s for s in us.get("symbols", {}) if us.get("themes", {}).get(s) in TECH_THEMES]

    async def refresh_distress(self) -> None:
        from .data import distress_data
        await distress_data.discover(set(dz.fixed_list()))         # market-wide SEC scan + screen → auto list
        await asyncio.to_thread(dz.prune, self.stockprices)        # names with no prices for 30 days leave the radar
        # US holdings are checked too (rulebook); they stay in this machine's cache and never join the public radar
        mine = [h for h in self.holding_tickers() if "." not in h]
        await distress_data.refresh(list(dict.fromkeys(list(dz.watchlist()) + mine)))

    async def refresh_fundamentals(self, budget_s: float = 60) -> None:
        """產業體檢: SEC companyfacts for the tracked US list + the AI ledger (+ holdings, kept in this machine's cache)."""
        from .data import fundamentals as fu
        from .data.stocks import universe as _uni
        from .analytics import sector_health as sh
        us = list(((_uni().get("us") or {}).get("symbols") or {}).keys())
        mine = [h for h in self.holding_tickers() if "." not in h]
        cache = await fu.refresh(list(dict.fromkeys(us + sh.AI_LEDGER + mine)), budget_s=budget_s)
        self.sector_health = await asyncio.to_thread(sh.build, self, cache)

    async def refresh_street(self) -> None:
        from .data import street_views as sv
        self.street = await sv.refresh()

    async def refresh_dispersion(self) -> None:
        """Cboe COR1M / COR3M / DSPX history (public files, cached 6 h) + the index-vs-median-stock gap."""
        from .analytics import dispersion as ds
        cb = await ds.refresh_cboe()
        self.dispersion = await asyncio.to_thread(ds.build, self, cb)

    async def refresh_segments(self, time_budget_s: float = 120) -> None:
        """Revenue geography / customer concentration from each US company's latest annual report (a few per run)."""
        from .data import segments as sg
        from .data.stocks import universe as _uni
        us = list(((_uni().get("us") or {}).get("symbols") or {}).keys())
        mine = [h for h in self.holding_tickers() if "." not in h]          # private: stays in this machine's cache
        self.segments = sg.public(await sg.refresh_for(list(dict.fromkeys(us + mine)), time_budget_s=time_budget_s))

    async def refresh_earnings(self, force: bool = False, frames: bool = False) -> None:
        """frames (whole-market US tech via SEC frames) is only needed by the website build."""
        mine = [h for h in self.holding_tickers() if "." not in h]          # EPS surprises for the rulebook too
        await self.earnings.refresh(list(dict.fromkeys(self.tech_symbols() + mine)), force=force, frames=frames)

    async def refresh_extras(self) -> None:
        """Slow feeds behind the stock board / bond zone (each one skips itself until its own refresh interval)."""
        res = await asyncio.gather(self.stockprices.refresh(), self.stocknews.refresh(), self.treasury.refresh(),
                                   self.refresh_edgar(), self.darkpool.refresh(self.market), self.econ.refresh(),
                                   self.fedwatch.refresh(), self.margin_debt.refresh(), self.refresh_distress(), self.refresh_segments(),
                                   self.refresh_street(), return_exceptions=True)
        for nm, r in zip(("stocks", "stocknews", "treasury", "edgar", "darkpool", "econ", "fedwatch", "finra", "distress", "segments",
                          "street"), res):
            if isinstance(r, Exception):
                log.warning("extras refresh %s failed: %s", nm, r)
        try:
            await self.refresh_fundamentals()                   # 產業體檢 (SEC companyfacts, weekly per company)
        except Exception as e:  # noqa: BLE001
            log.warning("extras refresh fundamentals failed: %s", e)
        try:
            await self.refresh_dispersion()                     # after stock prices refreshed (same gather above)
        except Exception as e:  # noqa: BLE001
            log.warning("extras refresh dispersion failed: %s", e)
        try:
            await self.refresh_earnings()                       # after the 13F / Form 4 pass: both talk to SEC
        except Exception as e:  # noqa: BLE001
            log.warning("extras refresh earnings failed: %s", e)
        await self.recompute()

    async def recompute(self, skip_quality: bool = False) -> None:
        async with self._lock:
            try:
                self.stress = await asyncio.to_thread(self.stress_engine.compute)
                if self.stress:
                    store.stress_record(self.stress.score, self.stress.blocks)
                    bench = SETTINGS.get("crash_odds", {}).get("benchmark", "^GSPC")
                    self.odds = await asyncio.to_thread(
                        co.crash_odds, getattr(self.stress, "live_history", None) if getattr(self.stress, "live_history", None) is not None
                        and len(self.stress.live_history) > 500 else self.stress.history, self.market.series(bench), self.stress.score,
                        self.stress.chg_20d)
            except Exception:  # noqa: BLE001
                log.exception("stress compute failed")
            try:
                if self.stress:
                    bench = SETTINGS.get("crash_odds", {}).get("benchmark", "^GSPC")
                    close = self.market.series(bench)
                    hrs = float(SETTINGS.get("shock", {}).get("quality_refresh_hours", 6))
                    if not skip_quality and (self._quality is None or time.time() - self._quality_ts > hrs * 3600):
                        self._quality = await asyncio.to_thread(sk.model_quality, self.stress.history, close)
                        self._quality_ts = time.time()
                        try:
                            self.lab = await asyncio.to_thread(lb.run, self.market.history, self.stress.history, close, self.fred)
                        except Exception:  # noqa: BLE001
                            log.exception("feature lab failed")
                    if self.lab and self.odds:                # validated logistic probability for today's SSI
                        self.odds = co.apply_model(self.odds, self.lab, self.stress.score)
                    try:                                       # 模型近期失準: recent record vs each model's own long-run record
                        from .analytics import model_health as mh
                        self.model_health = await asyncio.to_thread(mh.build, self)
                        for h in (self.odds or {}).get("horizons", []):   # each shown probability carries its own flag
                            fl = mh.flag(self.model_health, f"crash_{h.get('days')}")
                            h["drift"] = {"status": fl["status"], "why": fl.get("why")} if fl else None
                    except Exception:  # noqa: BLE001
                        log.exception("model health failed")
                    try:                                       # 產業真實經濟數據 (FRED series already loaded)
                        from .analytics import real_economy as rex
                        self.real_economy = await asyncio.to_thread(rex.build, self)
                    except Exception:  # noqa: BLE001
                        log.exception("real economy failed")
                    try:                                       # style factors: cheap (~2 s), public data only
                        from .analytics import factors as fa
                        sc_ = getattr(getattr(self, "stockprices", None), "close", None)
                        self.factors = await asyncio.to_thread(fa.build_public, self.market.history, sc_)
                    except Exception:  # noqa: BLE001
                        log.exception("factor model failed")
                    self.shock = await asyncio.to_thread(sk.build, self.stress, close, self._quality)
            except Exception:  # noqa: BLE001
                log.exception("shock radar failed")
            try:
                self.regime = await asyncio.to_thread(rg.classify, self.market, self.fred)
            except Exception:  # noqa: BLE001
                log.exception("regime failed")
            try:
                self.intel = await asyncio.to_thread(it.build, self)
            except Exception:  # noqa: BLE001
                log.exception("intel fusion failed")
            try:
                self.holdings = pf.load_holdings() or self.holdings
                self.portfolio = await asyncio.to_thread(pf.analyze, self.market, self.holdings)
            except Exception:  # noqa: BLE001
                log.exception("portfolio failed")
            try:
                self.exposure = await asyncio.to_thread(ex.build, self)
            except Exception:  # noqa: BLE001
                log.exception("exposure failed")
            try:
                self.valuation = await asyncio.to_thread(va.build, self)
            except Exception:  # noqa: BLE001
                log.exception("valuation failed")
            for attr, fn, label in (("scores", ss.build, "stock scores"), ("bonds", tsy.build, "treasury"),
                                    ("rotation", bd.build, "breadth"), ("signals", sg.build, "signals"),
                                    ("fedwatch_view", fw.view, "fedwatch"),
                                    ("econ_view", me.build, "econ calendar"), ("techearn", te.build, "tech earnings"),
                                    ("earn_verdict", ev.build, "earnings verdicts"), ("canary", cn.build, "canary lights"),
                                    ("distress", dz.build, "distress radar"), ("rulebook", rb.build, "holdings rulebook"),
                                    ("focus", fc.build, "market focus")):
                try:
                    setattr(self, attr, await asyncio.to_thread(fn, self))
                except Exception:  # noqa: BLE001
                    log.exception("%s failed", label)
            try:
                from .ai import econ_ai
                econ_ai.attach(self)
            except Exception:  # noqa: BLE001
                log.exception("econ AI attach failed")
            try:
                self.xray = await asyncio.to_thread(xr.build, self)
            except Exception:  # noqa: BLE001
                log.exception("xray failed")
            try:
                self.breaks = await asyncio.to_thread(pb.regime_breaks, self.market)
                if self.stress:
                    cov_ok = self.stress.coverage >= float(SETTINGS.get("health", {}).get("min_coverage", 0.9))
                    pbk = pb.score(self.stress.score, SETTINGS.get("stress_levels", []), self.odds, self.shock,
                                   self.breaks, cov_ok)
                    cut = 1 - pb.BETA_FACTOR[pbk["stage"]] if pbk["stage"] >= 2 else \
                        float(SETTINGS.get("playbook", {}).get("scoring", {}).get("watch_cut_frac", 0.15))
                    der = []
                    if self.portfolio and not self.portfolio.get("error"):
                        der = hg.analyze(self.portfolio, {}, self.stress.score, cut_frac=cut).get("derisk", [])
                    pbk["derisk"] = der
                    pbk["actions"] = pb.actions(pbk["stage"], self.portfolio, der, self.shock)
                    self.playbook = pbk
            except Exception:  # noqa: BLE001
                log.exception("playbook failed")
            try:
                self.outlook = await asyncio.to_thread(ol.build, self)     # last: it reads every other result
            except Exception:  # noqa: BLE001
                log.exception("outlook failed")
            self.recompute_ts = time.time()

    def age_str(self) -> str:
        if not self.market.quotes_ts:
            return "尚無報價"
        return f"報價 {int((time.time() - self.market.quotes_ts) / 60)} 分鐘前更新"
