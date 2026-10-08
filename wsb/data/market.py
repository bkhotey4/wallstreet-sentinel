"""Global cross-asset prices via yfinance (equities, rates, FX, commodities,
crypto, vol indices). Two layers:
  * history  — long daily closes (years) → dynamic baselines & backtests
  * quotes   — refreshed every few minutes, merged onto history as 'today'
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS, history_start
from ..health import HEALTH

log = logging.getLogger(__name__)
_HIST_FILE = DATA_DIR / "history_close.pkl"


def _yf():
    import yfinance as yf  # lazy: heavy import
    return yf


def _extract_close(df: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = df.columns.get_level_values(0)
        if "Close" in lvl0:
            out = df["Close"]
        else:  # group_by='ticker'
            out = df.xs("Close", axis=1, level=1)
    else:
        out = df[["Close"]].rename(columns={"Close": tickers[0]})
    out = out.copy()
    out.index = pd.to_datetime(out.index).tz_localize(None).normalize()
    out = out[~out.index.duplicated(keep="last")]
    return out.astype(float)


def _download(tickers: List[str], **kw) -> pd.DataFrame:
    yf = _yf()
    frames = []
    # chunk to keep Yahoo happy
    for i in range(0, len(tickers), 40):
        chunk = tickers[i:i + 40]
        df = yf.download(chunk, auto_adjust=True, progress=False, threads=True,
                         group_by="column", **kw)
        frames.append(_extract_close(df, chunk))
        time.sleep(0.5)
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, axis=1) if frames else pd.DataFrame()


def stooq_symbol(t: str) -> Optional[str]:
    """Yahoo ticker → Stooq symbol; only plain US stocks/ETFs are mapped (indices, FX, futures, Taiwan are not)."""
    if not t or any(c in t for c in "^=.-"):
        return None
    return t.lower() + ".us"


def parse_stooq(text: str) -> pd.Series:
    """Stooq daily CSV (Date,Open,High,Low,Close,Volume) → close series; empty on 'No data' / bad format."""
    import io
    if not text or "Date" not in text[:40]:
        return pd.Series(dtype=float)
    df = pd.read_csv(io.StringIO(text))
    if "Close" not in df.columns or df.empty:
        return pd.Series(dtype=float)
    s = pd.Series(pd.to_numeric(df["Close"], errors="coerce").values, index=pd.to_datetime(df["Date"]), dtype=float)
    return s.dropna().sort_index()


async def stooq_fallback(tickers: List[str], days: int = 10) -> pd.DataFrame:
    """Backup quote source for tickers Yahoo failed to return (used only for the gap, never replaces Yahoo)."""
    from . import http
    cols = {}
    for t in tickers:
        sym = stooq_symbol(t)
        if not sym:
            continue
        try:
            txt = await http.get(f"https://stooq.com/q/d/l/?s={sym}&i=d", kind="text", timeout=15, retries=0)
            s = parse_stooq(txt).tail(days)
            if len(s) >= 2:
                cols[t] = s
        except Exception as e:  # noqa: BLE001
            log.debug("stooq %s failed: %s", t, e)
        await asyncio.sleep(0.3)
    return pd.DataFrame(cols).sort_index() if cols else pd.DataFrame()


class MarketData:
    def __init__(self) -> None:
        self.tickers = SETTINGS.all_tickers()
        self.history = pd.DataFrame()
        self.quotes: Dict[str, dict] = {}
        self.history_ts = 0.0
        self.quotes_ts = 0.0
        if _HIST_FILE.exists():
            try:
                self.history = pd.read_pickle(_HIST_FILE)
                self.history_ts = _HIST_FILE.stat().st_mtime
            except Exception as e:  # noqa: BLE001
                log.warning("history cache unreadable: %s", e)

    # ------------------------------------------------------------------
    @property
    def history_age_hours(self) -> float:
        return (time.time() - self.history_ts) / 3600 if self.history_ts else 1e9

    def history_is_stale(self) -> bool:
        """Cache older than the refresh interval, or its last bar is >4 days old → rebuild on start."""
        if self.history.empty:
            return True
        last = self.history.index.max()
        too_short = self.history.index.min() > pd.Timestamp(history_start()) + pd.Timedelta(days=400)
        return too_short or self.history_age_hours > SETTINGS["refresh"]["history_hours"] or \
            (pd.Timestamp.today().normalize() - last).days > 4

    def _save(self) -> None:
        tmp = _HIST_FILE.with_suffix(".tmp")
        self.history.to_pickle(tmp)
        os.replace(tmp, _HIST_FILE)                   # atomic: a crash mid-write can't corrupt the cache

    async def refresh_history(self, extra: Optional[List[str]] = None) -> bool:
        tickers = sorted(set(self.tickers + (extra or [])))
        every = SETTINGS["refresh"]["history_hours"] * 3600
        try:
            df = await asyncio.to_thread(_download, tickers, start=history_start().isoformat(), interval="1d")
            if df.empty:
                raise RuntimeError("empty history download")
            df = df.sort_index()
            old = self.history
            # a ticker Yahoo failed on comes back missing/all-NaN → keep its previous history instead of wiping it
            bad = [t for t in tickers if t not in df.columns or df[t].notna().sum() == 0]
            kept = [t for t in bad if not old.empty and t in old.columns and old[t].notna().any()]
            if kept:
                df = df.drop(columns=[c for c in kept if c in df.columns]).join(old[kept], how="outer").sort_index()
                log.warning("history: kept cached data for %d failed tickers: %s", len(kept), ", ".join(kept[:10]))
            self.history = df
            self.history_ts = time.time()
            await asyncio.to_thread(self._save)
            HEALTH.ok("yahoo_history", df.shape[1] - len(bad) + len(kept), every=every)
            return True
        except Exception as e:  # noqa: BLE001
            log.exception("history refresh failed")
            HEALTH.fail("yahoo_history", e, every=every)
            return False

    async def refresh_quotes(self, extra: Optional[List[str]] = None) -> None:
        tickers = sorted(set(self.tickers + (extra or [])))
        every = SETTINGS["refresh"]["quotes"]
        try:
            df = await asyncio.to_thread(_download, tickers, period="7d", interval="1d")
            if df.empty:
                raise RuntimeError("empty quote download")
            # Yahoo throttles bursts: re-request the tickers that came back empty, once, after a short pause
            miss = [t for t in tickers if t not in df.columns or df[t].dropna().shape[0] < 2]
            if miss and len(miss) < len(tickers):
                await asyncio.sleep(4)
                try:
                    df2 = await asyncio.to_thread(_download, miss, period="7d", interval="1d")
                    if not df2.empty:
                        df = df.drop(columns=[c for c in df2.columns if c in df.columns]).join(df2, how="outer").sort_index()
                except Exception as e:  # noqa: BLE001
                    log.warning("quote retry failed: %s", e)
                still = [t for t in miss if t not in df.columns or df[t].dropna().shape[0] < 2]
                if still:
                    log.warning("quotes: %d/%d tickers unavailable this round (kept last good): %s",
                                len(still), len(tickers), ", ".join(still[:12]))
                    # backup source for plain US tickers (guarded: a failure here never affects the main path)
                    try:
                        # only fill tickers whose last-good quote is stale (>1 day) so Yahoo stays the primary source
                        need = [t for t in still if time.time() - (self.quotes.get(t) or {}).get("fetched", 0) > 86400]
                        if need:
                            sd = await stooq_fallback(need[:15])
                            fill = [c for c in sd.columns if c not in df.columns or df[c].dropna().shape[0] < 2]
                            if not sd.empty and fill:
                                df = df.drop(columns=[c for c in fill if c in df.columns])     # all-NaN yfinance columns
                                df = df.join(sd[fill], how="outer").sort_index()
                                HEALTH.ok("stooq_backup", len(fill), every=every * 6)
                                log.info("stooq backup filled: %s", ", ".join(fill))
                    except Exception as e:  # noqa: BLE001
                        log.warning("stooq backup failed: %s", e)
                        HEALTH.fail("stooq_backup", e, every=every * 6)
            quotes = dict(self.quotes)             # keep last good quote for tickers that failed this round
            fresh = 0
            for t in df.columns:
                s = df[t].dropna()
                if len(s) < 2:
                    continue
                last, prev = float(s.iloc[-1]), float(s.iloc[-2])
                quotes[t] = {
                    "price": last,
                    "prev": prev,
                    "chg_pct": (last / prev - 1) * 100 if prev else np.nan,
                    "asof": s.index[-1].strftime("%Y-%m-%d"),
                    "fetched": time.time(),
                }
                fresh += 1
            self.quotes = quotes
            self.quotes_ts = time.time()
            # merge newest bars onto history so analytics see 'today'
            self.history = self._merge(df) if not self.history.empty else df.sort_index()
            HEALTH.ok("yahoo_quotes", fresh, every=every)
        except Exception as e:  # noqa: BLE001
            log.exception("quote refresh failed")
            HEALTH.fail("yahoo_quotes", e, every=every)

    def _merge(self, recent: pd.DataFrame) -> pd.DataFrame:
        h = self.history.copy()
        for col in recent.columns:
            if col not in h.columns:
                h[col] = np.nan
                continue
            # split / dividend re-basing: recent auto-adjusted bars may be on a new basis → rescale older history
            r = recent[col].dropna()
            if r.empty:
                continue
            ov = h[col].reindex(r.index).dropna()
            if len(ov):
                k = float((r.reindex(ov.index) / ov).median())
                if np.isfinite(k) and k > 0 and abs(k - 1) > 0.015:
                    h.loc[h.index < r.index.min(), col] *= k
                    log.warning("%s re-based by factor %.4f (split/dividend adjustment)", col, k)
        new_idx = h.index.union(recent.index)
        h = h.reindex(new_idx)
        h.update(recent)  # recent values overwrite (today's live bar)
        return h.sort_index()

    # ------------------------------------------------------------------
    def series(self, ticker: str) -> pd.Series:
        if ticker in self.history.columns:
            return self.history[ticker].dropna()
        return pd.Series(dtype=float)

    def q(self, ticker: str) -> Optional[dict]:
        return self.quotes.get(ticker)

    def sigma_move(self, ticker: str, lookback: int = 60) -> Optional[float]:
        """Today's return measured in units of the asset's own recent daily vol."""
        s = self.series(ticker)
        s = s[s > 0]
        if len(s) < lookback + 2:
            return None
        r = np.log(s).diff().dropna()
        q = self.quotes.get(ticker)
        if q and q.get("asof") and q["asof"] > s.index[-1].strftime("%Y-%m-%d") and q.get("prev"):
            # history lags the live quote → measure the quote's own move against the latest `lookback` daily vols
            vol = r.iloc[-lookback:].std()
            now = float(np.log(q["price"] / q["prev"])) if q["price"] > 0 and q["prev"] > 0 else None
        else:
            vol = r.iloc[-lookback - 1:-1].std()
            now = float(r.iloc[-1])
        if now is None or not vol or np.isnan(vol):
            return None
        return float(now / vol)

    def returns_table(self, tickers: List[str]) -> List[dict]:
        rows = []
        for t in tickers:
            s = self.series(t)
            q = self.q(t)
            if s.empty and not q:
                continue
            row = {"ticker": t, "price": q["price"] if q else float(s.iloc[-1]),
                   "d1": q["chg_pct"] if q else None, "asof": q["asof"] if q else None}
            last_d = s.index[-1] if len(s) else None
            for lbl, days in (("w1", 7), ("m1", 30), ("m3", 91), ("ytd", None)):
                try:
                    if days is None:                               # last close of the previous year
                        prev_y = s[s.index.year < last_d.year]
                        base = float(prev_y.iloc[-1]) if len(prev_y) else None
                    else:                                          # calendar offsets: correct for 7-day crypto too
                        past = s[s.index <= last_d - pd.Timedelta(days=days)]
                        base = float(past.iloc[-1]) if len(past) else None
                    row[lbl] = (float(s.iloc[-1]) / base - 1) * 100 if base else None
                except Exception:  # noqa: BLE001
                    row[lbl] = None
            row["sigma"] = self.sigma_move(t)
            yr = s[s.index > last_d - pd.Timedelta(days=365)] if last_d is not None else s
            if len(s) and (s.index[0] <= last_d - pd.Timedelta(days=330)):
                row["pct_52w"] = float((s.iloc[-1] - yr.min()) / max(yr.max() - yr.min(), 1e-12) * 100)
            rows.append(row)
        return rows


async def fetch_single(ticker: str, period: str = "2y") -> pd.Series:
    def _f():
        yf = _yf()
        h = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        s = h["Close"].astype(float)
        s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
        return s
    return await asyncio.to_thread(_f)


async def fetch_info(ticker: str) -> dict:
    def _f():
        yf = _yf()
        try:
            info = yf.Ticker(ticker).info or {}
        except Exception:  # noqa: BLE001
            info = {}
        keep = ["shortName", "sector", "industry", "marketCap", "trailingPE", "forwardPE",
                "priceToBook", "beta", "dividendYield", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
                "targetMeanPrice", "recommendationKey", "shortPercentOfFloat", "currency"]
        return {k: info.get(k) for k in keep if info.get(k) is not None}
    return await asyncio.to_thread(_f)
