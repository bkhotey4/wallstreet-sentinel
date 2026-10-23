"""EIA weekly petroleum status: US distillate fuel oil stocks (thousand barrels, weekly, since 1982).

Optional: needs a free key from https://www.eia.gov/opendata/ in EIA_API_KEY; without it the feed stays empty and the
能源傳導鏈 card simply leaves the stocks line out.  Downloaded at most once a day and cached."""
from __future__ import annotations

import json
import logging
import time

import pandas as pd

from ..config import DATA_DIR, env
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
URL = "https://api.eia.gov/v2/seriesid/PET.WDISTUS1.W"
FILE = DATA_DIR / "econ_eia_distillate.json"        # econ_* is kept by the site workflow's cache


def parse(js: dict) -> pd.Series:
    rows = ((js or {}).get("response") or {}).get("data") or []
    out = {}
    for r in rows:
        try:
            out[pd.Timestamp(str(r["period"]))] = float(r["value"])
        except (KeyError, TypeError, ValueError):
            continue
    s = pd.Series(out, dtype=float).sort_index()
    if len(s) < 52:
        raise ValueError("EIA distillate stocks: too few rows")
    return s


class EIAData:
    def __init__(self) -> None:
        self.distillate = pd.Series(dtype=float)
        self.ts = 0.0
        try:
            d = json.loads(FILE.read_text(encoding="utf-8"))
            self.distillate = pd.Series({pd.Timestamp(k): v for k, v in d["data"].items()}, dtype=float).sort_index()
            self.ts = float(d.get("ts", 0))
        except (OSError, ValueError, KeyError):
            pass

    async def refresh(self, force: bool = False) -> None:
        key = env("EIA_API_KEY")
        if not key:
            return
        if not force and len(self.distillate) and time.time() - self.ts < 86400:
            return
        try:
            js = await http.get(URL, params={"api_key": key, "length": 5000}, timeout=30, retries=1)
            s = parse(js)
            self.distillate, self.ts = s, time.time()
            tmp = FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps({"ts": self.ts, "data": {k.strftime("%Y-%m-%d"): v for k, v in s.items()}}), encoding="utf-8")
            tmp.replace(FILE)
            HEALTH.ok("eia", len(s), every=86400)
        except Exception as e:  # noqa: BLE001
            log.warning("EIA distillate stocks failed: %s", e)
            HEALTH.fail("eia", e, every=86400)
