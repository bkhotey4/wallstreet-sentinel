"""Off-exchange ('dark pool') short-volume index from FINRA's free daily Reg SHO files.

Source: https://cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt  (consolidated NMS, all FINRA TRFs/ADF —
i.e. trades printed off-exchange, which is where dark pools and internalisers report). Format:
    Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market

Method (same idea as SqueezeMetrics' DIX white paper): when buyers trade off-exchange, market makers usually sell
short to fill them, so a HIGH short-volume share off-exchange tends to mean buying pressure, a LOW share selling
pressure. The index here = equal-weighted short-volume ratio across ~30 large US stocks, plus SPY/QQQ/IWM.

Honesty notes shown on the site: this is published T+1 by FINRA (not real time), it is a proxy (not actual dark-pool
order flow), and its history only covers the days this program has archived (it grows every day)."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d:%Y%m%d}.txt"
_FILE = DATA_DIR / "darkpool.json"
_META = DATA_DIR / "darkpool_meta.json"      # date → symbol-list hash it was fetched with (re-fetch only when the list changes)


def _cfg() -> Dict:
    return SETTINGS.get("darkpool", {}) or {}


def finra_sym(yahoo: str) -> str:
    return yahoo.replace("-", ".")                   # BRK-B (Yahoo) → BRK.B (FINRA)


def symbols() -> List[str]:
    """Index members + ETFs + the US names in the stock-scoring universe (per-stock off-exchange short ratio)."""
    us = list((((SETTINGS.get("stockscore", {}) or {}).get("markets") or {}).get("us") or {}).get("symbols", {}) or {})
    return list(dict.fromkeys(_cfg().get("index_symbols", []) + _cfg().get("etfs", []) + [finra_sym(x) for x in us]))


def parse(text: str, wanted: set) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {}
    for line in (text or "").splitlines()[1:]:
        p = line.split("|")
        if len(p) < 5 or p[1] not in wanted:
            continue
        try:
            sv, tv = float(p[2]), float(p[4])
        except ValueError:
            continue
        if tv > 0:
            out[p[1]] = [sv, tv]
    return out


class DarkPool:
    def __init__(self) -> None:
        self.days: Dict[str, Dict[str, List[float]]] = {}
        self.result: Dict = {}
        self._per: Dict[str, Optional[Dict]] = {}
        try:
            if _FILE.exists():
                self.days = json.loads(_FILE.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            log.warning("darkpool archive unreadable: %s", e)
        self.meta: Dict[str, str] = {}
        try:
            if _META.exists():
                self.meta = json.loads(_META.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            self.meta = {}

    async def refresh(self, market=None) -> None:
        if not _cfg().get("enabled", True):
            return
        every = 6 * 3600
        wanted = set(symbols())
        import hashlib
        ver = hashlib.md5(",".join(sorted(wanted)).encode()).hexdigest()[:10]
        back = int(_cfg().get("backfill_days", 90))
        d, todo = date.today() - timedelta(days=1), []
        for _ in range(back):
            have = self.days.get(d.isoformat())
            # missing day, or archived before the symbol list grew (e.g. per-stock names added) → (re)fetch
            if d.weekday() < 5 and (have is None or (len(wanted & set(have)) < 0.9 * len(wanted)
                                                     and self.meta.get(d.isoformat()) != ver)):
                todo.append(d)
            d -= timedelta(days=1)
        got, miss = 0, 0
        days = dict(self.days)                 # build a new dict: scoring may be reading self.days in a worker thread
        for d in todo[:int(_cfg().get("max_fetch_per_run", 40))]:
            try:
                txt = await http.get(URL.format(d=d), kind="text", timeout=20, retries=0)
                rows = parse(txt, wanted)
                if rows:
                    days[d.isoformat()] = rows
                    self.meta[d.isoformat()] = ver
                    got += 1
            except Exception as e:  # noqa: BLE001  (holidays → 403/404; keep going)
                miss += 1
                log.debug("FINRA %s: %s", d, e)
            await asyncio.sleep(0.2)
        if got:
            self.days = dict(sorted(days.items())[-int(_cfg().get("keep_days", 800)):])
            self.meta = {k: v for k, v in self.meta.items() if k in self.days}
            try:
                _FILE.write_text(json.dumps(self.days, separators=(",", ":")), encoding="utf-8")
                _META.write_text(json.dumps(self.meta), encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                log.warning("darkpool archive not saved: %s", e)
        if self.days:
            self.result = compute(self.days, market)
            self._per = {}
            HEALTH.ok("finra_darkpool", len(self.days), every=every)
        else:
            HEALTH.fail("finra_darkpool", f"no FINRA files fetched ({miss} failed)", every=every)


    def ticker(self, yahoo_sym: str) -> Optional[Dict]:
        """One stock's off-exchange short ratio: 5-day average and its percentile within that stock's own archive.
        High (vs its own history) = dealers shorting to fill buyers off-exchange → buying pressure (DIX logic)."""
        if yahoo_sym in self._per:
            return self._per[yahoo_sym]
        sym = finra_sym(yahoo_sym)
        vals = [(d, rec[sym][0] / rec[sym][1] * 100) for d, rec in sorted(self.days.items()) if sym in rec and rec[sym][1] > 0]
        out = None
        if len(vals) >= 40:                       # need ~2 months of its own history before a percentile means much
            s = pd.Series([v for _, v in vals])
            avg5 = float(s.tail(5).mean())
            roll5 = s.rolling(5).mean().dropna()
            out = {"ratio_5d": avg5, "pctile": float((roll5 < avg5).mean() * 100), "n": len(vals), "asof": vals[-1][0]}
        self._per[yahoo_sym] = out
        return out


def compute(days: Dict[str, Dict[str, List[float]]], market=None) -> Dict:
    idx_syms = _cfg().get("index_symbols", [])
    rows = []
    for ds in sorted(days):
        rec = days[ds]
        ratios = [rec[x][0] / rec[x][1] for x in idx_syms if x in rec and rec[x][1] > 0]
        # equal-weighted across the large caps (no price feed needed; one mega-cap cannot dominate the reading)
        row = {"date": ds, "dpi": float(np.mean(ratios)) * 100 if len(ratios) >= max(5, len(idx_syms) // 2) else None}
        for e in _cfg().get("etfs", []):
            if e in rec and rec[e][1]:
                row[e] = rec[e][0] / rec[e][1] * 100
        rows.append(row)
    df = pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame()
    if df.empty or df["dpi"].dropna().empty:
        return {"available": False}
    dpi = df["dpi"].dropna()
    dpi.index = pd.to_datetime(dpi.index)
    cur = float(dpi.iloc[-1])
    avg5 = float(dpi.tail(5).mean())
    pct = float((dpi < avg5).mean() * 100) if len(dpi) >= 20 else None
    etf = {e: (float(df[e].dropna().iloc[-1]) if e in df and df[e].notna().any() else None) for e in _cfg().get("etfs", [])}
    hi, lo = float(_cfg().get("high_pct", 80)), float(_cfg().get("low_pct", 20))
    state = None if pct is None else ("偏買（場外放空比例高）" if pct >= hi else "偏賣（場外放空比例低）" if pct <= lo else "中性")
    return {"available": True, "asof": dpi.index[-1].strftime("%Y-%m-%d"), "dpi": cur, "dpi_5d": avg5, "pctile": pct,
            "state": state, "n_days": int(len(dpi)), "etf": etf, "history": dpi}
