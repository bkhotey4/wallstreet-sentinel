"""Crypto & sentiment: CoinGecko global, stablecoin liquidity (DefiLlama),
perpetual funding (OKX), Crypto Fear&Greed, CNN equity Fear&Greed."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict

from ..config import SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)


def funding_hours(row: Dict) -> float:
    """Funding interval in hours from nextFundingTime − fundingTime (ms); 8h when absent or implausible."""
    try:
        h = (float(row["nextFundingTime"]) - float(row["fundingTime"])) / 3.6e6
        return h if 0.5 <= h <= 24 else 8.0
    except (KeyError, TypeError, ValueError):
        return 8.0


class CryptoSentiment:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}
        self.ts = 0.0
        self.ts_each: Dict[str, float] = {}             # last success per sub-feed
        self.keys_each: Dict[str, set] = {}             # which data keys each sub-feed owns

    async def _global(self):
        js = await http.get("https://api.coingecko.com/api/v3/global")
        d = js.get("data", {})
        return {
            "total_mcap_usd": d.get("total_market_cap", {}).get("usd"),
            "mcap_chg_24h_pct": d.get("market_cap_change_percentage_24h_usd"),
            "btc_dominance": d.get("market_cap_percentage", {}).get("btc"),
            "eth_dominance": d.get("market_cap_percentage", {}).get("eth"),
        }

    async def _stables(self):
        js = await http.get("https://stablecoins.llama.fi/stablecoincharts/all")
        pts = [p for p in js if p.get("totalCirculatingUSD")]
        def tot(p):
            return sum(float(v) for v in p["totalCirculatingUSD"].values())
        now = tot(pts[-1])
        d30 = tot(pts[-31]) if len(pts) > 31 else None
        return {"stablecoin_supply_usd": now,
                "stablecoin_chg_30d_pct": (now / d30 - 1) * 100 if d30 else None}

    async def _funding(self):
        out = {}
        for inst in ("BTC-USDT-SWAP", "ETH-USDT-SWAP"):
            js = await http.get("https://www.okx.com/api/v5/public/funding-rate", params={"instId": inst})
            row = (js.get("data") or [{}])[0]
            fr = row.get("fundingRate")
            if fr is not None:
                # per-interval rate → annualised %; OKX can switch a contract to 4h/2h/1h funding
                out[inst.split("-")[0] + "_funding_ann_pct"] = float(fr) * 365 * 24 / funding_hours(row) * 100
        oi = await http.get("https://www.okx.com/api/v5/public/open-interest",
                            params={"instType": "SWAP", "instId": "BTC-USDT-SWAP"})
        row = (oi.get("data") or [{}])[0]
        if row.get("oiUsd"):
            out["BTC_perp_oi_usd"] = float(row["oiUsd"])
        return out

    async def _crypto_fng(self):
        js = await http.get("https://api.alternative.me/fng/?limit=8")
        d = js.get("data", [])
        return {"crypto_fng": int(d[0]["value"]), "crypto_fng_label": d[0]["value_classification"],
                "crypto_fng_7d_ago": int(d[-1]["value"]) if len(d) > 7 else None}

    async def _cnn_fng(self):
        js = await http.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                            headers={"Referer": "https://www.cnn.com/", "Origin": "https://www.cnn.com"})
        fg = js.get("fear_and_greed", {})
        try:                                               # 抄底四訊號: keep CNN's history (it only serves one year)
            from ..analytics import bottom as BT
            BT.archive(js)
        except Exception as e:  # noqa: BLE001
            log.warning("CNN archive failed: %s", e)
        return {"cnn_fng": round(float(fg.get("score")), 1) if fg.get("score") is not None else None,
                "cnn_fng_label": fg.get("rating"),
                "cnn_fng_1w": fg.get("previous_1_week"), "cnn_fng_1m": fg.get("previous_1_month")}

    async def refresh(self) -> None:
        every = SETTINGS["refresh"]["crypto"]
        tasks = {"coingecko": self._global(), "defillama": self._stables(), "okx": self._funding(),
                 "crypto_fng": self._crypto_fng(), "cnn_fng": self._cnn_fng()}
        res = await asyncio.gather(*tasks.values(), return_exceptions=True)
        self.apply(dict(zip(tasks, res)), every)

    def apply(self, results: Dict[str, Any], every: float, now: float | None = None) -> None:
        """Merge sub-feed results; a feed that has not succeeded for ~2 refresh cycles has its values blanked."""
        now = time.time() if now is None else now
        for name, r in results.items():
            if isinstance(r, Exception):
                log.warning("%s failed: %s", name, r)
                HEALTH.fail(name, r, every=every)
            else:
                self.data.update(r)
                self.ts_each[name] = now
                self.keys_each.setdefault(name, set()).update(r)
                HEALTH.ok(name, len(r), every=every)
        stale = sorted(n for n, t in self.ts_each.items() if now - t > 2 * every)
        for name in stale:
            for k in self.keys_each.get(name, ()):
                self.data.pop(k, None)
        if stale:
            self.data["stale_sources"] = stale
        else:
            self.data.pop("stale_sources", None)
        if any(t == now for t in self.ts_each.values()):
            self.ts = now
