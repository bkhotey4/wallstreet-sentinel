"""Daily prices (close + volume) for the stock-scoring universe: ~50 US large caps, 30 Taiwan, 30 Hong Kong names.

Kept apart from the macro price history (which starts in 1995 and has no volume): two years of bars are enough for
200-day trends and 12-month momentum.  Cached in data_cache/stock_prices.pkl and refreshed every few hours."""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Dict, List

import pandas as pd

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH

log = logging.getLogger(__name__)
_FILE = DATA_DIR / "stock_prices.pkl"


def cfg() -> Dict:
    return SETTINGS.get("stockscore", {}) or {}


def universe() -> Dict[str, Dict]:
    """market key → {label, label_en, bench, news_lang, symbols: {sym: (zh, en)}, themes: {sym: theme}}"""
    out = {}
    for k, m in (cfg().get("markets") or {}).items():
        syms, themes = {}, {}
        for s, v in (m.get("symbols") or {}).items():
            zh, en = (v[0], v[1]) if isinstance(v, (list, tuple)) and len(v) >= 2 else (str(v), str(v))
            syms[str(s)] = (str(zh), str(en))
            themes[str(s)] = str(v[2]) if isinstance(v, (list, tuple)) and len(v) >= 3 else "其他"
        out[k] = {**m, "symbols": syms, "themes": themes}
    return out


def theme_names() -> Dict[str, str]:
    """族群 → English name, in display order."""
    return {str(k): str(v) for k, v in (cfg().get("themes") or {}).items()}


def all_symbols() -> List[str]:
    u = universe()
    return list(dict.fromkeys([s for m in u.values() for s in m["symbols"]] + [m["bench"] for m in u.values() if m.get("bench")]))


def _extract(df: pd.DataFrame, field: str, tickers: List[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = df.columns.get_level_values(0)
        out = df[field] if field in lvl0 else df.xs(field, axis=1, level=1)
    else:
        out = df[[field]].rename(columns={field: tickers[0]})
    out = out.copy()
    out.index = pd.to_datetime(out.index).tz_localize(None).normalize()
    return out[~out.index.duplicated(keep="last")].astype(float)


def _download(tickers: List[str], period: str):
    import yfinance as yf
    closes, vols = [], []
    for i in range(0, len(tickers), 40):
        chunk = tickers[i:i + 40]
        df = yf.download(chunk, period=period, interval="1d", auto_adjust=True, progress=False, threads=True,
                         group_by="column")
        closes.append(_extract(df, "Close", chunk))
        vols.append(_extract(df, "Volume", chunk))
        time.sleep(0.5)
    cl = pd.concat([c for c in closes if not c.empty], axis=1) if any(not c.empty for c in closes) else pd.DataFrame()
    vo = pd.concat([v for v in vols if not v.empty], axis=1) if any(not v.empty for v in vols) else pd.DataFrame()
    return cl.sort_index(), vo.sort_index()


class StockPrices:
    def __init__(self) -> None:
        self.close = pd.DataFrame()
        self.volume = pd.DataFrame()
        self.ts = 0.0
        try:
            if _FILE.exists():
                d = pd.read_pickle(_FILE)
                self.close, self.volume, self.ts = d["close"], d["volume"], float(d.get("ts", 0))
        except Exception as e:  # noqa: BLE001
            log.warning("stock price cache unreadable: %s", e)

    def stale(self) -> bool:
        if self.close.empty or time.time() - self.ts > float(cfg().get("refresh_hours", 3)) * 3600:
            return True
        # names added to the universe since the last download → fetch now instead of waiting for the next cycle
        missing = set(all_symbols()) - set(self.close.columns)
        return len(missing) > 2 and time.time() - self.ts > 600

    async def refresh(self, force: bool = False) -> None:
        if not cfg().get("enabled", True) or not (force or self.stale()):
            return
        syms = all_symbols()
        every = float(cfg().get("refresh_hours", 3)) * 3600
        try:
            cl, vo = await asyncio.to_thread(_download, syms, str(cfg().get("period", "2y")))
            if cl.empty:
                raise RuntimeError("empty download")
            good = [s for s in syms if s in cl.columns and cl[s].notna().sum() > 20]
            bad = [s for s in syms if s not in good]
            if bad and not self.close.empty:                      # keep the previous bars for tickers Yahoo skipped this round
                keep = [s for s in bad if s in self.close.columns]
                if keep:
                    cl = cl.drop(columns=[c for c in keep if c in cl.columns]).join(self.close[keep], how="outer")
                    vo = vo.drop(columns=[c for c in keep if c in vo.columns]).join(
                        self.volume[[k for k in keep if k in self.volume.columns]], how="outer")
            self.close, self.volume, self.ts = cl.sort_index(), vo.sort_index(), time.time()
            tmp = _FILE.with_suffix(".tmp")
            pd.to_pickle({"close": self.close, "volume": self.volume, "ts": self.ts}, tmp)
            os.replace(tmp, _FILE)
            HEALTH.ok("yahoo_stocks", len(good), every=every)
            if bad:
                log.warning("stock universe: %d tickers missing: %s", len(bad), ", ".join(bad[:10]))
        except Exception as e:  # noqa: BLE001
            log.warning("stock price refresh failed: %s", e)
            HEALTH.fail("yahoo_stocks", e, every=every)

    def series(self, sym: str) -> pd.Series:
        return self.close[sym].dropna() if sym in self.close.columns else pd.Series(dtype=float)

    def vol(self, sym: str) -> pd.Series:
        return self.volume[sym].dropna() if sym in self.volume.columns else pd.Series(dtype=float)
