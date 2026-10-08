"""SPX options positioning from CBOE delayed quotes (free, ~15m delay):
dealer gamma exposure (GEX), zero-gamma flip level, put/call ratios,
largest call/put walls."""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np

from ..config import SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
_SYM = re.compile(r"^([A-Z]+W?)(\d{6})([CP])(\d{8})$")


def _bs_gamma(S: np.ndarray, K: np.ndarray, T: np.ndarray, iv: np.ndarray, r: float = 0.04) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        d1 = (np.log(S / K) + (r + 0.5 * iv ** 2) * T) / (iv * np.sqrt(T))
        g = np.exp(-0.5 * d1 ** 2) / np.sqrt(2 * np.pi) / (S * iv * np.sqrt(T))
    return np.nan_to_num(g)


def parse_chain(js: Dict[str, Any], max_days: int = 60) -> Dict[str, Any]:
    data = js.get("data", {})
    spot = float(data.get("current_price") or data.get("close") or 0)
    now = datetime.now(timezone.utc)
    rows = []
    for o in data.get("options", []):
        m = _SYM.match(o.get("option", ""))
        if not m:
            continue
        exp = datetime.strptime(m.group(2), "%y%m%d").replace(tzinfo=timezone.utc, hour=20)
        days = (exp - now).total_seconds() / 86400
        if days < 0 or days > max_days:
            continue
        rows.append((m.group(3), int(m.group(4)) / 1000, max(days, 0.02) / 365,
                     float(o.get("iv") or 0), float(o.get("open_interest") or 0),
                     float(o.get("volume") or 0), float(o.get("gamma") or 0)))
    if not rows or spot <= 0:
        raise ValueError("empty chain")
    typ = np.array([r[0] for r in rows])
    K, T, iv, oi, vol, gam = (np.array([r[i] for r in rows], dtype=float) for i in range(1, 7))
    sign = np.where(typ == "C", 1.0, -1.0)   # convention: dealers long calls / short puts

    def gex_at(S: float) -> float:
        g = _bs_gamma(np.full_like(K, S), K, T, np.where(iv > 0, iv, 0.2))
        return float(np.sum(sign * g * oi * 100 * S * S * 0.01))

    gex_now = float(np.sum(sign * gam * oi * 100 * spot * spot * 0.01)) if gam.any() else gex_at(spot)
    grid = np.linspace(spot * 0.85, spot * 1.15, 61)
    prof = np.array([gex_at(s) for s in grid])
    flip = None
    crossings = np.where(np.diff(np.sign(prof)) != 0)[0]
    if len(crossings):
        # choose crossing nearest to spot, linear interpolation
        i = crossings[np.argmin(np.abs(grid[crossings] - spot))]
        x0, x1, y0, y1 = grid[i], grid[i + 1], prof[i], prof[i + 1]
        flip = float(x0 - y0 * (x1 - x0) / (y1 - y0)) if y1 != y0 else float(x0)

    near = np.abs(K / spot - 1) < 0.10
    def wall(kind: str) -> Optional[float]:
        mask = (typ == kind) & near
        if not mask.any():
            return None
        strikes = K[mask]
        ois = oi[mask]
        uniq = np.unique(strikes)
        tot = np.array([ois[strikes == k].sum() for k in uniq])
        return float(uniq[np.argmax(tot)])

    pc_oi = oi[typ == "P"].sum() / max(oi[typ == "C"].sum(), 1)
    pc_vol = vol[typ == "P"].sum() / max(vol[typ == "C"].sum(), 1)
    return {
        "spot": spot,
        "gex_usd_bn_per_1pct": gex_now / 1e9,
        "zero_gamma": flip,
        "spot_vs_flip_pct": (spot / flip - 1) * 100 if flip else None,
        "call_wall": wall("C"),
        "put_wall": wall("P"),
        "put_call_oi": float(pc_oi),
        "put_call_volume": float(pc_vol),
        "contracts": len(rows),
    }


class OptionsPositioning:
    def __init__(self) -> None:
        self.spx: Dict[str, Any] = {}
        self.ts = 0.0

    async def refresh(self) -> None:
        every = SETTINGS["refresh"]["options_gamma"]
        try:
            js = await http.get("https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json",
                                headers={"Referer": "https://www.cboe.com/"})
            import asyncio
            self.spx = await asyncio.to_thread(parse_chain, js)
            self.ts = time.time()
            HEALTH.ok("cboe_spx", self.spx.get("contracts", 0), every=every)
        except Exception as e:  # noqa: BLE001
            log.warning("CBOE failed: %s", e)
            HEALTH.fail("cboe_spx", e, every=every)


# ----------------------------------------------------------------------
# Generic single-name / ETF option chains (hedging, earnings implied move)
# ----------------------------------------------------------------------
_CHAIN_CACHE: Dict[str, tuple] = {}


def parse_quotes(js: Dict[str, Any]) -> Dict[str, Any]:
    """CBOE delayed JSON → {'spot', 'rows': [{type, strike, expiry, dte, bid, ask, mid, iv, oi, delta}]}"""
    data = js.get("data", {})
    spot = float(data.get("current_price") or data.get("close") or 0)
    now = datetime.now(timezone.utc)
    rows = []
    for o in data.get("options", []):
        m = _SYM.match(o.get("option", ""))
        if not m:
            continue
        exp = datetime.strptime(m.group(2), "%y%m%d").replace(tzinfo=timezone.utc, hour=20)
        dte = (exp - now).total_seconds() / 86400
        if dte < 0:
            continue
        bid, ask = float(o.get("bid") or 0), float(o.get("ask") or 0)
        last = float(o.get("last_trade_price") or 0)
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else (ask or last or 0)
        rows.append({"type": m.group(3), "strike": int(m.group(4)) / 1000, "expiry": exp.date().isoformat(),
                     "dte": dte, "bid": bid, "ask": ask, "mid": mid, "iv": float(o.get("iv") or 0),
                     "oi": float(o.get("open_interest") or 0), "delta": float(o.get("delta") or 0)})
    if not rows or spot <= 0:
        raise ValueError("empty chain")
    return {"spot": spot, "rows": rows}


async def fetch_chain(symbol: str, max_age: float = 900) -> Dict[str, Any]:
    """Cached CBOE chain for any optionable US symbol (SPY, QQQ, NVDA…); index symbols use '_SPX'."""
    sym = symbol.upper().replace("^", "_")
    hit = _CHAIN_CACHE.get(sym)
    if hit and time.time() - hit[0] < max_age:
        return hit[1]
    js = await http.get(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json",
                        headers={"Referer": "https://www.cboe.com/"}, timeout=30)
    import asyncio
    chain = await asyncio.to_thread(parse_quotes, js)
    _CHAIN_CACHE[sym] = (time.time(), chain)
    HEALTH.ok(f"cboe:{sym}", len(chain["rows"]), every=3600)
    return chain


def implied_move(chain: Dict[str, Any], on_or_after: str) -> Optional[Dict[str, Any]]:
    """ATM straddle / spot for the first expiry on/after a date (earnings implied move)."""
    rows, spot = chain["rows"], chain["spot"]
    # strictly AFTER the report date: an expiry on the report day misses after-close announcements
    exps = sorted({r["expiry"] for r in rows if r["expiry"] > on_or_after})
    if not exps:
        return None
    exp = exps[0]
    sub = [r for r in rows if r["expiry"] == exp and r["mid"] > 0]
    strikes = sorted({r["strike"] for r in sub}, key=lambda k: abs(k - spot))
    for k in strikes[:3]:
        c = next((r for r in sub if r["strike"] == k and r["type"] == "C"), None)
        p = next((r for r in sub if r["strike"] == k and r["type"] == "P"), None)
        if c and p:
            straddle = c["mid"] + p["mid"]
            return {"expiry": exp, "strike": k, "straddle": straddle, "move_pct": straddle / spot * 100,
                    "iv": (c["iv"] + p["iv"]) / 2, "spot": spot}
    return None
