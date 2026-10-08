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


class CryptoSentiment:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}
        self.ts = 0.0

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
                # 8h rate → annualised %
                out[inst.split("-")[0] + "_funding_ann_pct"] = float(fr) * 3 * 365 * 100
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
        return {"cnn_fng": round(float(fg.get("score")), 1) if fg.get("score") is not None else None,
                "cnn_fng_label": fg.get("rating"),
                "cnn_fng_1w": fg.get("previous_1_week"), "cnn_fng_1m": fg.get("previous_1_month")}

    async def refresh(self) -> None:
        every = SETTINGS["refresh"]["crypto"]
        tasks = {"coingecko": self._global(), "defillama": self._stables(), "okx": self._funding(),
                 "crypto_fng": self._crypto_fng(), "cnn_fng": self._cnn_fng()}
        res = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for name, r in zip(tasks, res):
            if isinstance(r, Exception):
                log.warning("%s failed: %s", name, r)
                HEALTH.fail(name, r, every=every)
            else:
                self.data.update(r)
                HEALTH.ok(name, len(r), every=every)
        self.ts = time.time()
