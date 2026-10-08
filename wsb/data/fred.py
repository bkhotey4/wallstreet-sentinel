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

from ..config import FRED_API_KEY, SETTINGS
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


class FredData:
    def __init__(self) -> None:
        self.series: Dict[str, pd.Series] = {}
        self.ts = 0.0

    async def refresh(self) -> None:
        every = SETTINGS["refresh"]["fred"]
        start = (date.today() - timedelta(days=365 * int(SETTINGS.get("history_years", 20)))).isoformat()
        ids = list(SETTINGS.get("fred_series", {}).keys())
        sem = asyncio.Semaphore(4)
        ok, fails, last_err = 0, 0, ""

        async def run(sid: str):
            nonlocal ok, fails, last_err
            async with sem:
                if ok == 0 and fails >= 4:          # circuit breaker: FRED unreachable → stop early
                    return
                try:
                    self.series[sid] = await _one(sid, start)
                    ok += 1
                except Exception as e:  # noqa: BLE001
                    fails += 1
                    last_err = f"{type(e).__name__}: {e}"
                    log.warning("FRED %s failed: %s", sid, last_err)
                await asyncio.sleep(0.3)

        await asyncio.gather(*(run(s) for s in ids))
        if ok:
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
        for lbl, days in (("chg_1m", 30), ("chg_3m", 91), ("chg_1y", 365)):
            past = s[s.index <= s.index[-1] - pd.Timedelta(days=days)]
            out[lbl] = float(s.iloc[-1] - past.iloc[-1]) if len(past) else None
        tail = s[s.index >= s.index[-1] - pd.Timedelta(days=365 * 3)]
        if len(tail) > 20:
            out["pctile_3y"] = float((tail < s.iloc[-1]).mean() * 100)
        return out

    def net_liquidity(self) -> pd.Series:
        """Fed balance sheet − TGA − RRP (USD bn). Classic risk-asset liquidity proxy."""
        walcl, tga, rrp = self.get("WALCL"), self.get("WTREGEN"), self.get("RRPONTSYD")
        if walcl.empty or tga.empty or rrp.empty:
            return pd.Series(dtype=float)
        idx = walcl.index.union(tga.index).union(rrp.index)
        df = pd.DataFrame({
            "walcl": walcl.reindex(idx).ffill() / 1000.0,   # mn → bn
            "tga": tga.reindex(idx).ffill() / 1000.0,        # mn → bn
            "rrp": rrp.reindex(idx).ffill(),                 # bn
        }).dropna()
        return (df["walcl"] - df["tga"] - df["rrp"]).rename("net_liquidity")
