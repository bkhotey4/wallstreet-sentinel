"""S&P 500 daily closes since 1927 (Yahoo, period=max) for the 滯脹年代對照 — the main price history starts in 1995.
Downloaded at most once a day and cached."""
from __future__ import annotations

import json
import logging
import time

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_spx_long.json"              # econ_* is kept by the site workflow's cache


class LongHistory:
    def __init__(self) -> None:
        self.spx = pd.Series(dtype=float)
        self.ts = 0.0
        try:
            d = json.loads(FILE.read_text(encoding="utf-8"))
            self.spx = pd.Series({pd.Timestamp(k): v for k, v in d["data"].items()}, dtype=float).sort_index()
            self.ts = float(d.get("ts", 0))
        except (OSError, ValueError, KeyError):
            pass

    async def refresh(self, force: bool = False) -> None:
        if not force and len(self.spx) and time.time() - self.ts < 86400:
            return
        from .market import fetch_single
        try:
            s = (await fetch_single("^GSPC", period="max")).dropna()
            if len(s) < 252 * 50 or s.index[0] > pd.Timestamp("1960-01-01"):
                raise ValueError(f"S&P long history too short ({len(s)} rows from {s.index[0] if len(s) else '—'})")
            self.spx, self.ts = s, time.time()
            tmp = FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps({"ts": self.ts, "data": {k.strftime("%Y-%m-%d"): float(v) for k, v in s.items()}}), encoding="utf-8")
            tmp.replace(FILE)
            HEALTH.ok("spx_long", len(s), every=86400)
        except Exception as e:  # noqa: BLE001
            log.warning("S&P long history failed: %s", e)
            HEALTH.fail("spx_long", e, every=86400)
