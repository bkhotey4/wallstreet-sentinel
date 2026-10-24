"""FRED (St. Louis Fed): credit spreads, curve, liquidity, financial-stress,
labour & inflation. Uses the free API key if present, else public CSV."""
from __future__ import annotations

import asyncio
import io
import logging
import time
from datetime import date, timedelta
from typing import Dict

import pandas as pd

from ..config import FRED_API_KEY, SETTINGS, history_start
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)


async def _one(series_id: str, start: str) -> pd.Series:
    if FRED_API_KEY:
        js = await http.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json",
                    "observation_start": start},
            retries=1, timeout=20)
        obs = js.get("observations", [])
        s = pd.Series({o["date"]: o["value"] for o in obs})
    else:
        txt = await http.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv",
            params={"id": series_id, "cosd": start}, kind="text", retries=0, timeout=20)
        df = pd.read_csv(io.StringIO(txt))
        s = pd.Series(df.iloc[:, 1].values, index=df.iloc[:, 0].values)
    s = pd.to_numeric(s, errors="coerce").dropna()   # FRED uses "." for missing
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


_CACHE = None


def _cache_file():
    global _CACHE
    if _CACHE is None:
        from ..config import DATA_DIR
        _CACHE = DATA_DIR / "fred_series.pkl"
    return _CACHE


class FredData:
    def __init__(self) -> None:
        self.series: Dict[str, pd.Series] = {}
        self.ts = 0.0
        # Append-only local archive: some FRED series (ICE BofA OAS) now publish only the last 3 years, so the
        # history we have already seen is kept and merged — the backtest window grows instead of shrinking.
        self._archive: Dict[str, pd.Series] = {}
        try:
            if _cache_file().exists():
                self._archive = pd.read_pickle(_cache_file())
        except Exception as e:  # noqa: BLE001
            log.warning("FRED archive unreadable: %s", e)

    def _merge(self, sid: str, s: pd.Series) -> pd.Series:
        old = self._archive.get(sid)
        if old is not None and len(old):
            s = pd.concat([old[old.index < s.index.min()], s]) if len(s) else old
        self._archive[sid] = s
        return s

    async def refresh(self) -> None:
        from ..analytics.energy_chain import FRED_IDS as EC_IDS
        from ..analytics.rates_radar import FRED_IDS as RR_IDS, LONG_IDS as RR_LONG
        from ..analytics.regime_split import FRED_IDS as RS_IDS
        from ..analytics.vulnerability import FRED_IDS as VU_IDS
        from .stability import FRED_IDS as ST_IDS
        every = SETTINGS["refresh"]["fred"]
        start = history_start().isoformat()
        val = SETTINGS.get("valuation", {}) or {}
        long_start = str(val.get("fred_start", start))
        trs = (SETTINGS.get("treasury", {}) or {}).get("fred") or {}
        ids = list(dict.fromkeys(list(SETTINGS.get("fred_series", {}).keys()) + list((val.get("fred") or {}).keys())
                                 + list(trs.keys())
                                 + [sid for grp in (SETTINGS.get("real_economy") or {}).values() for sid in (grp or {})]
                                 + list(RR_IDS) + list(EC_IDS) + list(RS_IDS) + list(VU_IDS) + list(ST_IDS)))
        # full history only where a module needs it; DGS2 (an SSI input) and the energy-chain series keep the usual start
        starts = {sid: long_start for sid in list(val.get("fred") or {}) + list(RR_LONG) + list(RS_IDS) + list(VU_IDS)}   # 利率衝擊雷達 needs 1962+ (1987 check)
        sem = asyncio.Semaphore(4)
        ok, fails, last_err = 0, 0, ""

        async def run(sid: str):
            nonlocal ok, fails, last_err
            async with sem:
                if ok == 0 and fails >= 4:          # circuit breaker: FRED unreachable → stop early
                    return
                try:
                    self.series[sid] = self._merge(sid, await _one(sid, starts.get(sid, start)))
                    ok += 1
                except Exception as e:  # noqa: BLE001
                    fails += 1
                    last_err = f"{type(e).__name__}: {e}"
                    log.warning("FRED %s failed: %s", sid, last_err)
                await asyncio.sleep(0.3)

        await asyncio.gather(*(run(s) for s in ids))
        for sid in ids:                                   # failed this round → fall back to the archive
            if sid not in self.series and sid in self._archive:
                self.series[sid] = self._archive[sid]
        if ok:
            try:
                tmp = _cache_file().with_suffix(".tmp")
                pd.to_pickle(self._archive, tmp)
                import os
                os.replace(tmp, _cache_file())
            except Exception as e:  # noqa: BLE001
                log.warning("FRED archive not saved: %s", e)
            self.ts = time.time()
            HEALTH.ok("fred", ok, every=every)
        else:
            HEALTH.fail("fred", f"unreachable ({last_err}); 建議設定 FRED_API_KEY", every=every)

    def get(self, sid: str) -> pd.Series:
        return self.series.get(sid, pd.Series(dtype=float))

    def latest(self, sid: str) -> dict | None:
        s = self.get(sid)
        if s.empty:
            return None
        out = {"value": float(s.iloc[-1]), "date": s.index[-1].strftime("%Y-%m-%d")}
        for lbl, months in (("chg_1m", 1), ("chg_3m", 3), ("chg_1y", 12)):
            past = s[s.index <= s.index[-1] - pd.DateOffset(months=months)]   # calendar months (monthly series dated the 1st)
            out[lbl] = float(s.iloc[-1] - past.iloc[-1]) if len(past) else None
        tail = s[s.index >= s.index[-1] - pd.Timedelta(days=365 * 3)]
        if len(tail) > 20:
            out["pctile_3y"] = float((tail < s.iloc[-1]).mean() * 100)
        return out

    def change_pctile(self, sid: str, days: int = 21, years: int = 3) -> float | None:
        """Where the latest `days`-observation change sits among the last `years` of such changes (0–100)."""
        s = self.get(sid).dropna()
        if len(s) <= days + 60:
            return None
        ch = (s - s.shift(days)).dropna()
        tail = ch[ch.index >= ch.index[-1] - pd.Timedelta(days=365 * years)]
        return float((tail < ch.iloc[-1]).mean() * 100) if len(tail) > 60 else None

    def net_liquidity(self) -> pd.Series:
        """Fed balance sheet − TGA − RRP (USD bn). Classic risk-asset liquidity proxy."""
        walcl, tga, rrp = self.get("WALCL"), self.get("WTREGEN"), self.get("RRPONTSYD")
        if walcl.empty or tga.empty or rrp.empty:
            return pd.Series(dtype=float)
        idx = walcl.index.union(tga.index).union(rrp.index)
        df = pd.DataFrame({
            "walcl": walcl.reindex(idx).ffill(limit=10) / 1000.0,   # mn → bn (weekly: at most ~2 weeks of carry)
            "tga": tga.reindex(idx).ffill(limit=10) / 1000.0,        # mn → bn
            "rrp": rrp.reindex(idx).ffill(limit=10),                 # bn
        }).dropna()
        last = min(walcl.index.max(), tga.index.max(), rrp.index.max())   # freshness = the stalest input
        return (df["walcl"] - df["tga"] - df["rrp"]).rename("net_liquidity").loc[:last + pd.Timedelta(days=14)]


def restricted(sid: str) -> bool:
    """Series whose raw values may not be republished (ICE BofA indices, Moody's): show derived figures only."""
    from ..config import SETTINGS
    return sid in set(SETTINGS.get("fred_restricted") or [])


def direction(chg) -> str:
    return "—" if chg is None else ("擴大" if chg > 0 else "收斂" if chg < 0 else "持平")


def restricted_component(c: dict) -> bool:
    """A stress / canary component built on a licensed series (its own series or the other leg of a spread)."""
    import re
    if not c or c.get("src") != "fred":
        return False
    m = re.match(r"spread:([^:]+)", str(c.get("kind") or ""))
    return restricted(str(c.get("series") or "")) or bool(m and restricted(m.group(1)))
