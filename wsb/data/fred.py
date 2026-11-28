"""FRED (St. Louis Fed): credit spreads, curve, liquidity, financial-stress,
labour & inflation. Uses the free API key if present, else public CSV."""
from __future__ import annotations

import asyncio
import io
import re
import logging
import time
from datetime import date, timedelta
from typing import Dict, Optional

import pandas as pd

from ..config import FRED_API_KEY, SETTINGS, history_start
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)


UST_XML = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"   # Treasury daily par yield curve
UST_TENOR = {"BC_1MONTH": "DGS1MO", "BC_3MONTH": "DGS3MO", "BC_6MONTH": "DGS6MO", "BC_1YEAR": "DGS1", "BC_2YEAR": "DGS2",
             "BC_3YEAR": "DGS3", "BC_5YEAR": "DGS5", "BC_7YEAR": "DGS7", "BC_10YEAR": "DGS10", "BC_20YEAR": "DGS20", "BC_30YEAR": "DGS30"}
# Treasury daily REAL (TIPS) yield curve: fills FRED's one-day lag for DFII10/DFII5 too (2026-11-21: the 每日總經 card showed
# Thursday's real yield next to Friday's nominal one).  T10YIE = DGS10 − DFII10, as FRED derives it.
UST_REAL = {"TC_5YEAR": "DFII5", "TC_10YEAR": "DFII10"}
UST_SPREADS = {"T10Y2Y": ("DGS10", "DGS2"), "T10Y3M": ("DGS10", "DGS3MO"), "T10YIE": ("DGS10", "DFII10")}


def parse_ust_all(xml: str, tenors: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, float]]:
    """Treasury daily par yield curve XML → {YYYY-MM-DD: {FRED id: yield %}} for every tenor present."""
    out: Dict[str, Dict[str, float]] = {}
    for blk in re.findall(r"<m:properties>(.*?)</m:properties>", xml, re.S):
        d = re.search(r"<d:NEW_DATE[^>]*>(\d{4}-\d{2}-\d{2})", blk)
        if not d:
            continue
        row = {}
        for tag, sid in (tenors or UST_TENOR).items():
            v = re.search(rf"<d:{tag}[^>]*>([\d.]+)<", blk)
            if v:
                row[sid] = float(v.group(1))
        if row:
            out[d.group(1)] = row
    return out


def _redact(msg: str) -> str:
    """aiohttp errors carry the request URL; never let the API key reach the log."""
    return re.sub(r"(api_key=)[^&\s'\"]+", r"\g<1>***", msg)


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
                # 11-28: fast builds never call refresh(), so ts stayed 0 and 11 cards said 「來源沒標更新時間」. The archive's
                # save time is when these numbers were last fetched; a successful refresh() overwrites it.
                self.ts = _cache_file().stat().st_mtime
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
        from ..analytics.bonds import FRED_IDS as BD_IDS
        from .migration_polls import FRED_IDS as MG_IDS
        from .fsr_watch import FRED_IDS as FW_IDS
        from .rate_pressure import FRED_IDS as RP_IDS
        from ..analytics.macro_events import FRED_IDS as ME_IDS
        from ..analytics.sloos import FRED_IDS as SL_IDS
        every = SETTINGS["refresh"]["fred"]
        start = history_start().isoformat()
        val = SETTINGS.get("valuation", {}) or {}
        long_start = str(val.get("fred_start", start))
        trs = (SETTINGS.get("treasury", {}) or {}).get("fred") or {}
        ids = list(dict.fromkeys(list(SETTINGS.get("fred_series", {}).keys()) + list((val.get("fred") or {}).keys())
                                 + list(trs.keys())
                                 + [sid for grp in (SETTINGS.get("real_economy") or {}).values() for sid in (grp or {})]
                                 + list(RR_IDS) + list(EC_IDS) + list(RS_IDS) + list(VU_IDS) + list(ST_IDS) + list(BD_IDS) + list(MG_IDS) + list(FW_IDS) + list(RP_IDS) + list(ME_IDS) + list(SL_IDS)))
        # full history only where a module needs it; DGS2 (an SSI input) and the energy-chain series keep the usual start
        starts = {sid: long_start for sid in list(val.get("fred") or {}) + list(RR_LONG) + list(RS_IDS) + list(VU_IDS) + list(FW_IDS) + list(SL_IDS)
                  + [i for i in BD_IDS if i.startswith("IRLTLT")]}                      # government bonds: full history for percentiles   # 利率衝擊雷達 needs 1962+ (1987 check)
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
                    last_err = _redact(f"{type(e).__name__}: {e}")
                    log.warning("FRED %s failed: %s", sid, last_err)
                await asyncio.sleep(0.3)

        await asyncio.gather(*(run(s) for s in ids))
        limited = [sid for sid in ids if sid not in self.series] if ok else []
        # FRED allows ~120 calls/min.  11-21: the cap of 30 left whole bursts (40–120 rate-limited series a day, 11-16→11-20)
        # on the archive copy; now every limited series gets one paced second pass (~85/min, at most 200 series).
        if limited:
            limited = limited[:200]
            await asyncio.sleep(30)
            for sid in limited:
                try:
                    self.series[sid] = self._merge(sid, await _one(sid, starts.get(sid, start)))
                    ok += 1
                    fails -= 1
                except Exception as e:  # noqa: BLE001
                    log.warning("FRED %s failed again: %s", sid, _redact(str(e)))
                await asyncio.sleep(0.7)
        for sid in ids:                                   # failed this round → fall back to the archive
            if sid not in self.series and sid in self._archive:
                self.series[sid] = self._archive[sid]
        try:                                              # after the archive fallback, so a FRED outage is filled too
            await self.fill_treasury()
        except Exception as e:  # noqa: BLE001
            log.info("Treasury fill skipped: %s", e)
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


    async def fill_treasury(self, today=None) -> Dict[str, list]:
        """FRED posts the Treasury yields (DGS*) a day or two after Treasury itself; cards then said 「官方值查無」 for
        yesterday (11-17).  Treasury's own daily par-yield XML is the same number — append only the dates FRED does not
        have yet (never overwrite FRED, never written to the archive), plus the spreads FRED derives from them."""
        from datetime import date as _date
        today = today or _date.today()
        months = {today.strftime("%Y%m")}
        if today.day <= 5:
            months.add((today.replace(day=1) - pd.Timedelta(days=1)).strftime("%Y%m"))
        got: Dict[str, Dict[str, float]] = {}
        for m in sorted(months):
            for data, tenors in (("daily_treasury_yield_curve", UST_TENOR), ("daily_treasury_real_yield_curve", UST_REAL)):
                try:
                    xml = await http.get(UST_XML, params={"data": data, "field_tdr_date_value_month": m},
                                         kind="text", timeout=20, retries=1)
                except Exception as e:  # noqa: BLE001
                    log.info("Treasury %s XML %s: %s", data, m, e)
                    continue
                for d, row in parse_ust_all(xml, tenors).items():
                    got.setdefault(d, {}).update(row)
        return self.apply_treasury(got)

    def apply_treasury(self, got: Dict[str, Dict[str, float]]) -> Dict[str, list]:
        filled: Dict[str, list] = {}
        for sid in list(UST_TENOR.values()) + list(UST_REAL.values()):
            s = self.series.get(sid)
            if s is None or s.empty:
                continue
            last = s.index[-1]
            add = {pd.Timestamp(d): row[sid] for d, row in got.items() if sid in row and pd.Timestamp(d) > last}
            if add:
                self.series[sid] = pd.concat([s, pd.Series(add).sort_index()])
                filled[sid] = sorted(x.strftime("%Y-%m-%d") for x in add)
        for sid, (a, b) in UST_SPREADS.items():               # T10Y2Y = DGS10 − DGS2 etc., exactly as FRED computes them
            s = self.series.get(sid)
            if s is None or s.empty:
                continue
            last = s.index[-1]
            add = {pd.Timestamp(d): round(row[a] - row[b], 2) for d, row in got.items()
                   if a in row and b in row and pd.Timestamp(d) > last}
            if add:
                self.series[sid] = pd.concat([s, pd.Series(add).sort_index()])
                filled[sid] = sorted(x.strftime("%Y-%m-%d") for x in add)
        self.treasury_filled = filled
        if filled:
            log.info("Treasury filled FRED lag: %s", {k: v[-1] for k, v in filled.items()})
        return filled

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
