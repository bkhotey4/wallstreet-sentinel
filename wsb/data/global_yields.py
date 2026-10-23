"""Japanese government bond yields (Ministry of Finance, daily constant-maturity, 1974+).

MOF publishes two CSVs at stable URLs: the full history up to last month and the current month.  Both are merged,
downloaded at most every 6 hours and cached.  UK and German 10-year yields come from FRED (monthly OECD series) and
are listed in the 利率衝擊雷達's FRED ids, not here."""
from __future__ import annotations

import io
import json
import logging
import time

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
BASE = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/"
URLS = (BASE + "historical/jgbcme_all.csv", BASE + "jgbcme.csv")
FILE = DATA_DIR / "econ_jgb_yields.json"            # econ_* is kept by the site workflow's cache
KEEP = ("1Y", "2Y", "5Y", "10Y", "20Y", "30Y")


def parse(txt: str) -> pd.DataFrame:
    """MOF CSV → DataFrame indexed by date, columns 1Y…30Y in %.  The first line is a title; '-' marks no data."""
    lines = txt.splitlines()
    head = next(i for i, ln in enumerate(lines[:10]) if "10Y" in ln)
    df = pd.read_csv(io.StringIO("\n".join(lines[head:])), na_values=["-", ""])
    df.columns = [str(c).strip() for c in df.columns]
    df.index = pd.to_datetime(df.iloc[:, 0].astype(str).str.strip(), errors="coerce", format="mixed")
    df = df[df.index.notna()]
    df = df[[c for c in KEEP if c in df.columns]].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    if "10Y" not in df.columns or len(df) < 1:
        raise ValueError("MOF JGB csv: no 10Y column")
    return df.sort_index()


class GlobalYields:
    def __init__(self) -> None:
        self.jgb = pd.DataFrame()
        self.ts = 0.0
        try:
            d = json.loads(FILE.read_text(encoding="utf-8"))
            self.jgb = pd.DataFrame(d["data"]).T
            self.jgb.index = pd.to_datetime(self.jgb.index)
            self.jgb = self.jgb.sort_index().astype(float)
            self.ts = float(d.get("ts", 0))
        except (OSError, ValueError, KeyError):
            pass

    async def refresh(self, force: bool = False) -> None:
        if not force and len(self.jgb) and time.time() - self.ts < 6 * 3600:
            return
        parts = []
        for u in URLS:
            try:
                parts.append(parse(await http.get(u, kind="text", timeout=40, retries=1)))
            except Exception as e:  # noqa: BLE001
                log.warning("MOF JGB %s failed: %s", u.rsplit("/", 1)[-1], e)
        if not parts:
            HEALTH.fail("mof_jgb", "both MOF CSVs failed", every=6 * 3600)
            return
        df = pd.concat([self.jgb] + parts) if len(self.jgb) else pd.concat(parts)
        df = df[~df.index.duplicated(keep="last")].sort_index()
        if len(df) < 250:
            HEALTH.fail("mof_jgb", f"only {len(df)} rows", every=6 * 3600)
            return
        self.jgb, self.ts = df, time.time()
        try:
            tmp = FILE.with_suffix(".tmp")
            data = {k.strftime("%Y-%m-%d"): {c: (None if pd.isna(v) else float(v)) for c, v in r.items()} for k, r in df.iterrows()}
            tmp.write_text(json.dumps({"ts": self.ts, "data": data}), encoding="utf-8")
            tmp.replace(FILE)
        except Exception as e:  # noqa: BLE001
            log.warning("JGB cache not saved: %s", e)
        HEALTH.ok("mof_jgb", len(df), every=6 * 3600)

    def get(self, tenor: str) -> pd.Series:
        return self.jgb[tenor].dropna() if tenor in self.jgb.columns else pd.Series(dtype=float)
