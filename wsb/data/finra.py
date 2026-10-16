"""FINRA customer margin statistics (monthly, since 1997): debit balances in customers' securities margin accounts.

Margin debt is the classic leverage canary — its year-over-year growth ran above +40 % before the 2000, 2007 and 2021
tops.  FINRA publishes one workbook at a stable URL; it is downloaded at most once a day and cached."""
from __future__ import annotations

import io
import json
import logging
import time
from typing import Optional

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
URL = "https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx"
FILE = DATA_DIR / "econ_finra_margin.json"          # econ_* is kept by the site workflow's cache


def parse(xlsx: bytes) -> pd.Series:
    """Workbook → monthly debit balances ($ millions), indexed by month start."""
    df = pd.read_excel(io.BytesIO(xlsx), sheet_name=0, header=None)
    head = next(i for i in range(min(10, len(df))) if str(df.iat[i, 0]).strip().lower().startswith("year"))
    out = {}
    for _, r in df.iloc[head + 1:].iterrows():
        try:
            d = pd.Timestamp(str(r.iloc[0]).strip()[:7] + "-01")
            v = float(str(r.iloc[1]).replace(",", ""))
        except (ValueError, TypeError):
            continue
        if v > 0:
            out[d] = v
    s = pd.Series(out).sort_index()
    if len(s) < 24:
        raise ValueError("FINRA margin workbook: too few rows")
    return s


class MarginDebt:
    def __init__(self) -> None:
        self.series = pd.Series(dtype=float)
        self.ts = 0.0
        try:
            d = json.loads(FILE.read_text(encoding="utf-8"))
            self.series = pd.Series({pd.Timestamp(k): v for k, v in d["data"].items()}).sort_index()
            self.ts = float(d.get("ts", 0))
        except (OSError, ValueError, KeyError):
            pass

    async def refresh(self, force: bool = False) -> None:
        if not force and len(self.series) and time.time() - self.ts < 86400:
            return
        try:
            raw = await http.get(URL, kind="bytes", timeout=40, retries=1, headers={"User-Agent": "Mozilla/5.0"})
            s = parse(raw)
            self.series, self.ts = s, time.time()
            tmp = FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps({"ts": self.ts, "data": {k.strftime("%Y-%m-%d"): v for k, v in s.items()}}), encoding="utf-8")
            tmp.replace(FILE)
            HEALTH.ok("finra_margin", len(s), every=86400)
        except Exception as e:  # noqa: BLE001
            log.warning("FINRA margin statistics failed: %s", e)
            HEALTH.fail("finra_margin", e, every=86400)

    def yoy(self) -> Optional[pd.Series]:
        return (self.series / self.series.shift(12) - 1) * 100 if len(self.series) > 13 else None
