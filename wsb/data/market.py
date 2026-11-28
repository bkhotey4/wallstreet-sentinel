"""Global cross-asset prices via yfinance (equities, rates, FX, commodities,
crypto, vol indices). Two layers:
  * history  — long daily closes (years) → dynamic baselines & backtests
  * quotes   — refreshed every few minutes, merged onto history as 'today'
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import date
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS, history_start
from ..health import HEALTH
from . import rolls as ROLL

YIELDS = ("^TNX", "^FVX", "^TYX", "^IRX")   # Yahoo's Treasury yield indices: still print a number on bond holidays


def _bond_closed(days) -> Dict[str, str]:
    from .exchange_cal import us_bond_closed
    ys = sorted({int(str(d)[:4]) for d in days}) or [date.today().year]
    return us_bond_closed(ys[0], ys[-1])


def _drop_bond_holidays(s: pd.Series) -> pd.Series:
    """Remove the bars Yahoo prints on SIFMA full-close days (2026-11-11 Veterans Day: ^TNX 4.998 while the last real
    close was 11-10's 4.98), so the next day's change is measured against the last real close."""
    if s is None or s.empty:
        return s
    closed = _bond_closed([s.index[0].year, s.index[-1].year])
    if not closed:
        return s
    keep = [d.strftime("%Y-%m-%d") not in closed for d in s.index]
    return s[keep]


def _bond_quote(qt: dict, clean: pd.Series) -> dict:
    """A yield quote on a bond holiday → the last real close, change unknown, bond_closed = holiday name.
    On the day after → the change against the last real close, not against the holiday's number."""
    d = str(qt["asof"])[:10]
    closed = _bond_closed([d[:4]])
    before = clean[clean.index < pd.Timestamp(d)] if clean is not None and len(clean) else pd.Series(dtype=float)
    if d in closed:
        if not len(before):
            return {**qt, "chg_pct": np.nan, "bond_closed": closed[d]}
        last = float(before.iloc[-1])
        prev = float(before.iloc[-2]) if len(before) >= 2 else None
        return {**qt, "price": last, "prev": prev, "chg_pct": np.nan, "asof": before.index[-1].strftime("%Y-%m-%d"),
                "bond_closed": closed[d], "bond_closed_date": d}
    if len(before) and qt.get("price") is not None:
        prev = float(before.iloc[-1])
        if prev and prev != qt.get("prev"):
            qt = {**qt, "prev": prev, "chg_pct": (float(qt["price"]) / prev - 1) * 100}
    return qt

log = logging.getLogger(__name__)
_HIST_FILE = DATA_DIR / "history_close.pkl"
_FAIL_FILE = DATA_DIR / "history_fail.json"       # {ticker: last time a full history download came back without it}
HIST_FAIL_DAYS = 7                                 # such tickers don't trigger another full rebuild for this long
_HIST_BACKOFF = (1800, 7200, 21600)                # after a failed rebuild: next try in 30 min, then 2 h, then 6 h
SPLIT_SIZES = (3, 4, 5, 6, 8, 10, 15, 20, 25, 30, 40, 50, 100)
SPLIT_TOL = 0.15                                   # log distance from an exact split: room for the day's real move


def is_rebaseable(t: str) -> bool:
    """Only equities / ETFs get split / dividend re-basing; indices (^), futures / FX (=) and crypto (-USD) never do."""
    return not (t.startswith("^") or "=" in t or t.endswith("-USD"))


def split_factor(prev: float, last: float) -> Optional[int]:
    """The split a close-to-close jump looks like: 4 = 1→4 (price ÷ 4), −10 = a 10→1 reverse split, None = an ordinary
    move.  Yahoo can print the post-split price a day before it adjusts the old bars or lists the split, so the jump has
    to be read from the prices.  A real day's move is allowed on top; 1→2 is left out, since −50% can be a real crash."""
    if not (prev > 0 and last > 0):
        return None
    x = prev / last if prev > last else last / prev
    n = min(SPLIT_SIZES, key=lambda k: abs(np.log(x / k)))
    if abs(np.log(x / n)) > SPLIT_TOL:
        return None
    return n if prev > last else -n


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
    out = pd.concat(frames, axis=1) if frames else pd.DataFrame()
    try:
        out = fill_meta_close(out)
    except Exception as e:  # noqa: BLE001
        log.warning("meta close fill failed: %s", e)
    return out


def _chart_meta(t: str) -> Optional[dict]:
    import json as _json
    import urllib.parse
    import urllib.request
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(t)}?range=5d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        res = ((_json.load(r).get("chart") or {}).get("result") or [None])[0]
    return (res or {}).get("meta")


_META_TRIED: Dict[tuple, float] = {}       # (ticker, date) → when asked; a holiday NaN is not re-asked every quote cycle


def fill_meta_close(df: pd.DataFrame, fetch=None, now: Optional[float] = None, cap: int = 25) -> pd.DataFrame:
    """2026-11-21: Yahoo's bulk daily download gave NaN for Friday's close of the Nikkei, Hang Seng and TAIEX (its own
    chart endpoint showed the daily bar empty too) while the chart meta already had the final price.  For a ticker whose
    newest row is NaN, take meta.regularMarketPrice when its exchange-local date is that row's date and the regular
    session has ended — a holiday (meta on an earlier date) or a session still open is left alone."""
    if df.empty:
        return df
    now = time.time() if now is None else now
    # 2026-11-21 (daily check): the frame's last row was the only one looked at.  On a Saturday build a crypto ticker adds
    # a weekend row, every other ticker is NaN there, and Friday's NaN for the Nikkei / Hang Seng / HYG was never filled
    # (the live 每日總經 table stayed on 11-19 through a −5% Nikkei day).  Look at the newest weekday row instead.
    wk = [d for d in df.index if d.weekday() < 5]
    if not wk:
        return df
    last = wk[-1]
    if (pd.Timestamp(now, unit="s") - last).days > 5:
        return df
    day = last.strftime("%Y-%m-%d")
    cand = [c for c in df.columns if pd.isna(df.at[last, c]) and df.loc[df.index < last, c].notna().any()]
    if fetch is None:                                  # drop the ones asked in the last 30 minutes before the cap, so
        cand = [c for c in cand if now - _META_TRIED.get((c, day), 0) >= 1800]     # a holiday's NaNs cannot starve the rest
    cand = sorted(cand, key=lambda c: (not str(c).startswith("^"), str(c)))[:cap]   # indices first
    filled = []
    for t in cand:
        _META_TRIED[(t, day)] = now
        try:
            m = (fetch or _chart_meta)(t) or {}
        except Exception:  # noqa: BLE001
            continue
        px, rt, off = m.get("regularMarketPrice"), m.get("regularMarketTime"), m.get("gmtoffset") or 0
        end = ((m.get("currentTradingPeriod") or {}).get("regular") or {}).get("end")
        if not px or not rt or pd.Timestamp(rt + off, unit="s").normalize() != last:
            continue
        # the session of that day still running: not a close yet (a period that belongs to a later day is not this session)
        if end and now < end and pd.Timestamp(end + off, unit="s").normalize() == last:
            continue
        df.loc[last, t] = float(px)
        filled.append(t)
    if filled:
        log.info("daily close filled from chart meta (bulk download had NaN): %s", ", ".join(filled))
    return df


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
        self._hist_fails = 0                       # consecutive failed history rebuilds (in-memory backoff)
        self._hist_next = 0.0                      # don't attempt another full rebuild before this time
        self.hist_failed: Dict[str, float] = {}
        try:
            if _FAIL_FILE.exists():
                self.hist_failed = {str(k): float(v) for k, v in json.loads(_FAIL_FILE.read_text(encoding="utf-8")).items()}
        except Exception as e:  # noqa: BLE001
            log.warning("history failure list unreadable: %s", e)
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

    def recently_failed(self, days: float = HIST_FAIL_DAYS) -> set:
        """Tickers a full history download failed on within `days` → not a reason for another full rebuild yet."""
        cut = time.time() - days * 86400
        return {t for t, ts in self.hist_failed.items() if ts >= cut}

    def _save_failed(self) -> None:
        try:
            tmp = _FAIL_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.hist_failed), encoding="utf-8")
            os.replace(tmp, _FAIL_FILE)
        except Exception as e:  # noqa: BLE001
            log.warning("history failure list not saved: %s", e)

    def _save(self) -> None:
        tmp = _HIST_FILE.with_suffix(".tmp")
        self.history.to_pickle(tmp)
        os.replace(tmp, _HIST_FILE)                   # atomic: a crash mid-write can't corrupt the cache

    async def refresh_history(self, extra: Optional[List[str]] = None, force: bool = False) -> bool:
        tickers = sorted(set(self.tickers + (extra or [])))
        every = SETTINGS["refresh"]["history_hours"] * 3600
        if not force and time.time() < self._hist_next:     # backing off after a failed full rebuild
            log.info("history rebuild skipped: backing off for %.0f more min", (self._hist_next - time.time()) / 60)
            return False
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
            self.hist_failed = {t: time.time() for t in bad}       # remembered so they don't force another rebuild soon
            self._save_failed()
            self._hist_fails, self._hist_next = 0, 0.0
            HEALTH.ok("yahoo_history", df.shape[1] - len(bad) + len(kept), every=every)
            return True
        except Exception as e:  # noqa: BLE001
            log.exception("history refresh failed")
            HEALTH.fail("yahoo_history", e, every=every)
            wait = _HIST_BACKOFF[min(self._hist_fails, len(_HIST_BACKOFF) - 1)]
            self._hist_fails += 1
            self._hist_next = time.time() + wait
            log.warning("history rebuild failed %d time(s) in a row: next attempt in %.1f h", self._hist_fails, wait / 3600)
            return False

    async def add_history(self, syms: List[str]) -> List[str]:
        """Fetch the full history of tickers the cache doesn't have yet (a newly added holding) and merge it in."""
        new = [s for s in dict.fromkeys(syms) if s and (self.history.empty or s not in self.history.columns
                                                        or self.history[s].notna().sum() == 0)]
        if not new:
            return []
        try:
            df = await asyncio.to_thread(_download, new, start=history_start().isoformat(), interval="1d")
        except Exception as e:  # noqa: BLE001
            log.warning("history for new tickers %s failed: %s", new, e)
            return []
        got = [s for s in new if s in df.columns and df[s].notna().sum() > 0]
        if got:
            base = self.history.drop(columns=[c for c in got if c in self.history.columns]) if not self.history.empty else self.history
            self.history = (base.join(df[got], how="outer") if not base.empty else df[got]).sort_index()
            await asyncio.to_thread(self._save)
            log.info("history added for %s", ", ".join(got))
        return got

    async def refresh_quotes(self, extra: Optional[List[str]] = None) -> None:
        from . import taiwan_quotes as TQ
        tracked = set(self.tickers + (extra or []))
        # Yahoo stays the intraday source for Taiwan too: the TWSE/TPEx OpenAPI files are end-of-day only and often
        # publish a day late, so dropping Yahoo froze 台股 quotes at yesterday and silenced the intraday danger check.
        tickers = sorted(tracked)
        official_task = asyncio.create_task(TQ.refresh())
        every = SETTINGS["refresh"]["quotes"]
        backup: set = set()                       # columns filled by the Stooq backup this round
        try:
            df = await asyncio.to_thread(_download, tickers, period="7d", interval="1d") if tickers else pd.DataFrame()
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
                                backup |= set(fill)
                                HEALTH.ok("stooq_backup", len(fill), every=every * 6)
                                log.info("stooq backup filled: %s", ", ".join(fill))
                    except Exception as e:  # noqa: BLE001
                        log.warning("stooq backup failed: %s", e)
                        HEALTH.fail("stooq_backup", e, every=every * 6)
            df = self._unsplit(df)
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
                    "asof": s.index[-1].strftime("%Y-%m-%d"),      # the bar's own date (daily bars carry no time)
                    "fetched": time.time(),                          # when we downloaded it — not the market time
                    "src": "stooq" if t in backup else "yahoo",
                    "fallback": t in backup,
                    "bar": "1d",
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
        finally:
            # Yahoo outages must never prevent official Taiwan prices from being applied.
            try:
                official = await official_task
                # only tracked tickers (the official file has ~2,300 symbols), and only when the official bar is
                # newer than — or the same day as — what Yahoo already gave us
                fresh = {s: {"src": "twse", "fallback": False, "bar": "1d", **q} for s, q in official.items()
                         if s in tracked and q.get("asof", "") >= (self.quotes.get(s) or {}).get("asof", "")}
                self.quotes = {**self.quotes, **fresh}
                index = TQ.index_frame(official)
                if not index.empty:
                    # Index levels are unadjusted on both sources; equity cash prices stay separate.
                    current = self.series("^TWII")
                    if not current.empty:
                        index = index[index.index >= current.index.max()]
                    self.history = self._merge(index) if not self.history.empty else index
            except Exception as e:
                log.warning("Official Taiwan quote application failed: %s", e)

    def _unsplit(self, df: pd.DataFrame) -> pd.DataFrame:
        """Put bars from before an unadjusted split on the new basis.  _merge then re-bases the stored history by the
        same factor, and once Yahoo adjusts its own bars the jump is gone and this does nothing."""
        df = df.copy()
        found = {}
        for t in df.columns:
            s = df[t].dropna()
            if not is_rebaseable(t):
                continue
            for i in range(len(s) - 1, 0, -1):
                n = split_factor(float(s.iloc[i - 1]), float(s.iloc[i]))
                if n:
                    df.loc[df.index < s.index[i], t] *= (1 / n if n > 0 else -n)
                    found[t] = (n, s.index[i].strftime("%Y-%m-%d"))
                    log.warning("%s looks like an unadjusted split (%d) on %s", t, n, found[t][1])
                    break
        self.splits = found
        return df

    def _merge(self, recent: pd.DataFrame) -> pd.DataFrame:
        h = self.history.copy()
        for col in recent.columns:
            if col not in h.columns:
                h[col] = np.nan
                continue
            # split / dividend re-basing: recent auto-adjusted bars may be on a new basis → rescale older history.
            # Equities / ETFs only (an index or FX rate has no splits), and only with ≥3 overlapping bars, leaving out
            # history's last bar (it may be a partial intraday one) so one odd print can't rescale decades of data.
            r = recent[col].dropna()
            if r.empty or not is_rebaseable(col):
                continue
            hc = h[col].dropna().iloc[:-1]
            ov = hc.reindex(r.index).dropna()
            if len(ov) >= 3:
                ratio = r.reindex(ov.index) / ov
                k = float(ratio.median())
                # a dividend re-basis is ~0.2–2% and the same on every overlapping bar; a 1.5% floor left a fake
                # dividend-sized step at the boundary.  Uniform-ratio check keeps quote noise from rescaling history.
                uniform = bool((ratio / k - 1).abs().max() < 0.0005) if np.isfinite(k) and k > 0 else False
                if np.isfinite(k) and k > 0 and abs(k - 1) > 0.002 and uniform:
                    h.loc[h.index < r.index.min(), col] *= k
                    log.warning("%s re-based by factor %.4f (split/dividend adjustment)", col, k)
        new_idx = h.index.union(recent.index)
        h = h.reindex(new_idx)
        h.update(recent)  # recent values overwrite (today's live bar)
        return h.sort_index()

    # ------------------------------------------------------------------
    def series(self, ticker: str) -> pd.Series:
        if ticker in self.history.columns:
            s = self.history[ticker].dropna()
            peer = ROLL.PEERS.get(ticker)
            if peer and peer in self.history.columns:      # oil futures: no contract-roll gap in the history (wsb.data.rolls)
                key = (ticker, len(s), float(s.iloc[-1]) if len(s) else None, len(self.history[peer].dropna()))
                cache = self.__dict__.setdefault("_roll_cache", {})
                hit = cache.get(ticker)
                if not hit or hit[0] != key:
                    hit = (key, ROLL.adjust(s, self.history[peer].dropna(), ticker))
                    cache[ticker] = hit
                return hit[1]
            if ticker in YIELDS:                           # Treasury yields: no bar on a bond-market holiday (SIFMA)
                return _drop_bond_holidays(s)
            return s
        return pd.Series(dtype=float)

    def q(self, ticker: str) -> Optional[dict]:
        """The live quote — unless the history already has a newer bar (e.g. Yahoo throttled this round and the
        TWSE file, a day late, filled in): then the newest bar's close / change, so price, % and σ describe one day."""
        from . import freshness as F
        qt = self.quotes.get(ticker)
        if not qt:
            return qt
        s = self.history[ticker].dropna() if ticker in self.history.columns else pd.Series(dtype=float)   # raw closes, not roll-adjusted
        s = s[s > 0]
        if len(s) >= 2:
            last_d = s.index[-1].strftime("%Y-%m-%d")
            if str(qt.get("asof", ""))[:10] < last_d:
                last, prev = float(s.iloc[-1]), float(s.iloc[-2])
                qt = {**qt, "price": last, "prev": prev, "chg_pct": (last / prev - 1) * 100, "asof": last_d, "src": "history"}
            elif str(qt.get("asof", ""))[:10] == last_d:     # only when the history reaches the quote's day (else it may be older)
                # 11-28 audit P1-1: the round's download can miss a bar (^N225 had no 11-25 row), so its "previous" close is two
                # sessions back and the strip showed −1.42% while the macro dashboard (history) showed +1.4%.  Measure the change
                # against the history's last close before the quote's own day, so the strip and the dashboard describe one move.
                asof = pd.Timestamp(str(qt.get("asof", ""))[:10]) if qt.get("asof") else None
                before = s[s.index < asof] if asof is not None else s.iloc[0:0]
                if len(before) and qt.get("price") is not None:
                    prev = float(before.iloc[-1])
                    if prev and prev != qt.get("prev"):
                        qt = {**qt, "prev": prev, "chg_pct": (float(qt["price"]) / prev - 1) * 100, "prev_from": "history"}
        peer = ROLL.PEERS.get(ticker)
        if peer and qt.get("asof"):
            pq = self.quotes.get(peer) or {}
            if str(pq.get("asof", ""))[:10] == str(qt["asof"])[:10]:
                try:
                    roll = ROLL.is_roll_day(ticker, date.fromisoformat(str(qt["asof"])[:10]), qt.get("chg_pct"), pq.get("chg_pct"))
                except ValueError:
                    roll = False
                if roll:                                    # the change is partly the gap between two contracts: unknown
                    qt = {**qt, "chg_pct": np.nan, "roll": True}
        if ticker in YIELDS and qt.get("asof"):
            qt = _bond_quote(qt, self.series(ticker))
        # stale = the bar is older than the market's last session: shown, but never a "new move" alert
        return {**qt, "stale": F.stale(ticker, qt.get("asof", "")), "session": F.session(ticker)}

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
            lastv = float(s.iloc[-1]) if len(s) else None
            if lastv and q and q.get("prev") and q.get("price") and str(q.get("asof", ""))[:10] > last_d.strftime("%Y-%m-%d"):
                # quote is a newer day than the (dividend-adjusted) history → chain today's move onto the last bar, so
                # 1W/1M/YTD/52W describe the same day as price and 1D and stay on the history's price basis
                lastv *= float(q["price"]) / float(q["prev"])
            for lbl, days in (("w1", 7), ("m1", 30), ("m3", 91), ("ytd", None)):
                try:
                    if days is None:                               # last close of the previous year
                        prev_y = s[s.index.year < last_d.year]
                        base = float(prev_y.iloc[-1]) if len(prev_y) else None
                    else:                                          # calendar offsets: correct for 7-day crypto too
                        past = s[s.index <= last_d - pd.Timedelta(days=days)]
                        base = float(past.iloc[-1]) if len(past) else None
                    row[lbl] = (lastv / base - 1) * 100 if base else None
                except Exception:  # noqa: BLE001
                    row[lbl] = None
            row["sigma"] = self.sigma_move(t)
            yr = s[s.index > last_d - pd.Timedelta(days=365)] if last_d is not None else s
            if len(s) and (s.index[0] <= last_d - pd.Timedelta(days=330)):
                lo, hi = min(float(yr.min()), lastv), max(float(yr.max()), lastv)
                row["pct_52w"] = float((lastv - lo) / max(hi - lo, 1e-12) * 100)
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
