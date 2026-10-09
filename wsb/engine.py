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
from .analytics import techearn as te
from .analytics.stress import StressEngine, StressResult
from .config import SETTINGS
from .data.calendar import EventCalendar
from .data.crypto import CryptoSentiment
from .data.fred import FredData
from .data.market import MarketData
from .data.news import NewsWire
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
        self.xray: Dict = {}
        self.valuation: Dict = {}
        self.scores: Dict = {}            # 個股評分表（美股／台股／港股）
        self.bonds: Dict = {}             # 美債專區（殖利率曲線、期限溢價、標售）
        self.rotation: Dict = {}          # 類股輪動與市場寬度
        self.signals: Dict = {}           # 技術面買點訊號（規則篩選）
        self.econ_view: Dict = {}         # 財經日曆（FOMC、CPI、PPI…＋影響劇本）
        self.techearn: Dict = {}          # 科技／半導體財報分析
        self._quality: Optional[Dict] = None
        self._quality_ts = 0.0
        self.regime: Dict = {}
        self.intel: Dict = {}
        self.breaks: Dict = {}
        self.playbook: Dict = {}
        self.portfolio: Dict = {}
        self.holdings: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self.ready = False
        self.full_ready = False          # phase 2 (macro/news/options/taiwan) loaded

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
        if self.market.history_is_stale() or (missing and self.market.history_age_hours > 1):
            log.info("history rebuild: stale=%s missing=%d (%s)", self.market.history_is_stale(), len(missing),
                     ", ".join(sorted(missing)[:8]))
            await self.market.refresh_history(extra)
        await self.market.refresh_quotes(extra)
        await self.recompute()
        self.ready = True
        log.info("phase 1 ready (prices)")
        names = ("fred", "crypto", "options", "news", "calendar", "sec", "taiwan", "darkpool", "stocks", "stocknews",
                 "treasury", "edgar", "econ")
        res = await asyncio.gather(self.fred.refresh(), self.crypto.refresh(), self.options.refresh(),
                                   self.news.refresh(), self.calendar.refresh(extra),
                                   self.sec.refresh([t for t in extra if "." not in t]),
                                   self.taiwan.refresh(), self.darkpool.refresh(self.market), self.stockprices.refresh(),
                                   self.stocknews.refresh(), self.treasury.refresh(), self.refresh_edgar(), self.econ.refresh(),
                                   return_exceptions=True)
        try:
            await self.refresh_earnings()
        except Exception as e:  # noqa: BLE001
            log.warning("phase-2 refresh earnings failed: %s", e)
        for nm, r in zip(names, res):
            if isinstance(r, Exception):
                log.warning("phase-2 refresh %s failed: %s", nm, r)
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

    async def refresh_earnings(self, force: bool = False, frames: bool = False) -> None:
        """frames (whole-market US tech via SEC frames) is only needed by the website build."""
        await self.earnings.refresh(self.tech_symbols(), force=force, frames=frames)

    async def refresh_extras(self) -> None:
        """Slow feeds behind the stock board / bond zone (each one skips itself until its own refresh interval)."""
        res = await asyncio.gather(self.stockprices.refresh(), self.stocknews.refresh(), self.treasury.refresh(),
                                   self.refresh_edgar(), self.darkpool.refresh(self.market), self.econ.refresh(), return_exceptions=True)
        for nm, r in zip(("stocks", "stocknews", "treasury", "edgar", "darkpool", "econ"), res):
            if isinstance(r, Exception):
                log.warning("extras refresh %s failed: %s", nm, r)
        try:
            await self.refresh_earnings()                       # after the 13F / Form 4 pass: both talk to SEC
        except Exception as e:  # noqa: BLE001
            log.warning("extras refresh earnings failed: %s", e)
        await self.recompute()

    async def recompute(self) -> None:
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
                    if self._quality is None or time.time() - self._quality_ts > hrs * 3600:
                        self._quality = await asyncio.to_thread(sk.model_quality, self.stress.history, close)
                        self._quality_ts = time.time()
                        try:
                            self.lab = await asyncio.to_thread(lb.run, self.market.history, self.stress.history, close)
                        except Exception:  # noqa: BLE001
                            log.exception("feature lab failed")
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
                self.valuation = await asyncio.to_thread(va.build, self)
            except Exception:  # noqa: BLE001
                log.exception("valuation failed")
            for attr, fn, label in (("scores", ss.build, "stock scores"), ("bonds", tsy.build, "treasury"),
                                    ("rotation", bd.build, "breadth"), ("signals", sg.build, "signals"),
                                    ("econ_view", me.build, "econ calendar"), ("techearn", te.build, "tech earnings")):
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

    def age_str(self) -> str:
        if not self.market.quotes_ts:
            return "尚無報價"
        return f"報價 {int((time.time() - self.market.quotes_ts) / 60)} 分鐘前更新"
