"""ETF 資金流向: daily shares outstanding and NAV for major US ETFs, straight from each issuer.

Estimated net flow = change in shares outstanding × NAV (see analytics/etf_flows).  Sources, checked with real requests:
* SPY: State Street's NAV history workbook (date, NAV, shares, net assets, back to 2003).
* QQQ: the JSON behind Invesco's own QQQ page (latest day only).
* HYG / LQD / TLT: the fund data embedded in the iShares product pages (latest day only).
Latest-day sources are stored at every fetch, so their history grows one trading day at a time.  A failed fetch keeps
what is stored and does not move that fund's fetch time.  Nothing is estimated from another source.
Cached in data_cache/econ_etf_flows.json (kept between site builds)."""
from __future__ import annotations

import html
import io
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_etf_flows.json"
TTL = 4 * 3600
KEEP = 1000                                              # about four years of trading days per fund
TNA_TOL = 0.02                                           # shares × NAV must match the issuer's own net assets
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "etf_flows_seed.json"   # public repo root; written by the PC
SEED_ROWS = 30                                           # trading days carried in the seed
SEED_MAX_H = 36                                          # the PC's own fetch must be this fresh to be passed on
_ISH = "https://www.ishares.com/us/products/{}"
FUNDS = (
    {"sym": "SPY", "zh": "標普 500", "en": "S&P 500", "group": "equity", "issuer": "State Street", "kind": "ssga",
     "url": "https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-spy.xlsx"},
    {"sym": "QQQ", "zh": "那斯達克 100", "en": "Nasdaq-100", "group": "equity", "issuer": "Invesco", "kind": "invesco",
     "url": "https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/QQQ?idType=ticker&variationType=fundDetails&productType=ETF"},
    {"sym": "HYG", "zh": "高收益債（垃圾債）", "en": "High-yield bonds", "group": "credit", "issuer": "iShares", "kind": "ishares",
     "url": _ISH.format("239565/ishares-iboxx-high-yield-corporate-bond-etf")},
    {"sym": "LQD", "zh": "投資級公司債", "en": "Investment-grade bonds", "group": "credit", "issuer": "iShares", "kind": "ishares",
     "url": _ISH.format("239566/ishares-iboxx-investment-grade-corporate-bond-etf")},
    {"sym": "TLT", "zh": "20 年以上美國公債", "en": "20+ year Treasuries", "group": "rates", "issuer": "iShares", "kind": "ishares",
     "url": _ISH.format("239454/ishares-20-year-treasury-bond-etf")},
)
Row = List                                               # [date YYYY-MM-DD, shares outstanding, NAV]


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", FILE.name, e)
        return {}
    return d if isinstance(d, dict) else {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)


def _good(day: str, shares: float, nav: float, tna: Optional[float] = None) -> Row:
    """One validated row; raises so a damaged file can never enter the history."""
    if not (shares > 0 and nav > 0):
        raise ValueError(f"bad shares/NAV on {day}")
    if date.fromisoformat(day) > date.today() + timedelta(days=1):
        raise ValueError(f"future date {day}")
    if tna and abs(shares * nav / tna - 1) > TNA_TOL:
        raise ValueError(f"shares × NAV disagrees with net assets on {day}")
    return [day, float(shares), float(nav)]


def parse_ssga(raw: bytes, sym: str) -> List[Row]:
    """State Street NAV history workbook, newest first: Date, NAV, Shares Outstanding, Total Net Assets."""
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True).active
    out, col, tick = [], None, None
    for r in ws.iter_rows(values_only=True):
        if r and str(r[0] or "").startswith("Ticker Symbol"):
            tick = str(r[1] or "").strip()
        elif col is None:
            names = [str(c or "").strip() for c in r]
            if {"Date", "NAV", "Shares Outstanding"} <= set(names):
                col = {n: i for i, n in enumerate(names)}
        elif r[col["Date"]]:
            try:
                day = datetime.strptime(str(r[col["Date"]]).strip(), "%d-%b-%Y").date().isoformat()
                sh, nav = float(r[col["Shares Outstanding"]]), float(r[col["NAV"]])
            except (TypeError, ValueError):
                continue                                 # footnote rows under the table
            tna = r[col["Total Net Assets"]] if "Total Net Assets" in col else None
            try:
                out.append(_good(day, sh, nav, float(tna) if tna else None))
            except ValueError:
                if not out:                              # the newest row must be sound; an old bad row only leaves a gap
                    raise
            if len(out) >= KEEP:
                break
    if tick != sym or col is None or not out:
        raise ValueError(f"not the {sym} NAV history (ticker {tick}, {len(out)} rows)")
    return sorted(out)


def parse_invesco(j: Dict, sym: str) -> List[Row]:
    if not isinstance(j, dict) or j.get("ticker") != sym:
        raise ValueError(f"Invesco answer is not {sym}")
    day, sh, nav = j.get("effectiveBusinessDate"), j.get("sharesOutstanding"), j.get("nav")
    if not day or not sh or not nav:
        raise ValueError("Invesco answer has empty fund data")
    return [_good(str(day)[:10], float(sh), float(nav), float(j.get("shareclassTotalNetAssets") or 0) or None)]


_SO = re.compile(r'"sharesOutstanding":\{[^{}]*?"formattedValue":"([\d,]+)"[^{}]*?"formattedAsOfDate":"([A-Z][a-z]{2} \d{2}, \d{4})"')
_NAV = re.compile(r'"navAmount":\{[^{}]*?"asOfDate":(\d{8})[^{}]*?"value":([\d.]+)')


def parse_ishares(text: str, sym: str) -> List[Row]:
    """Fund facts embedded in the product page; both numbers must carry the same as-of date."""
    t = html.unescape(text)
    if not re.search(r"<title>[^<]*\|\s*" + re.escape(sym) + r"\b", t):
        raise ValueError(f"not the {sym} product page")
    so, nv = _SO.search(t), _NAV.search(t)
    if not so or not nv:
        raise ValueError("fund facts not found on the page")
    d1 = datetime.strptime(so.group(2), "%b %d, %Y").date().isoformat()
    d2 = datetime.strptime(nv.group(1), "%Y%m%d").date().isoformat()
    if d1 != d2:
        raise ValueError(f"shares dated {d1} but NAV dated {d2}")
    return [_good(d1, float(so.group(1).replace(",", "")), float(nv.group(2)))]


async def _fetch(f: Dict) -> List[Row]:
    if f["kind"] == "ssga":
        return parse_ssga(await http.get(f["url"], kind="bytes", timeout=60, retries=1), f["sym"])
    if f["kind"] == "invesco":
        return parse_invesco(await http.get(f["url"], kind="json", timeout=40, retries=1), f["sym"])
    return parse_ishares(await http.get(f["url"], kind="text", timeout=60, retries=1), f["sym"])


def merge(old: List[Row], new: List[Row]) -> List[Row]:
    m = {r[0]: r for r in old or []}
    m.update({r[0]: r for r in new})
    return [m[k] for k in sorted(m)][-KEEP:]


def write_seed(path: Path, now: Optional[float] = None) -> int:
    """Copy the last SEED_ROWS issuer rows of every fund this machine fetched cleanly within SEED_MAX_H into the public
    repo.  2026-11-19: Invesco has answered the cloud build with HTTP 406 since 11-17 while the PC still gets the same
    official JSON, so QQQ froze on the site.  The seed is issuer data fetched elsewhere, never an estimate."""
    d, now = load(), now or time.time()
    each, out = d.get("ts_each") or {}, {"ts_each": {}, "funds": {}}
    for s, fd in (d.get("funds") or {}).items():
        t = float(each.get(s) or 0)
        if fd.get("rows") and not fd.get("err") and not fd.get("via") and now - t < SEED_MAX_H * 3600:
            out["ts_each"][s], out["funds"][s] = t, fd["rows"][-SEED_ROWS:]
    if out["funds"]:
        path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return len(out["funds"])


def _from_seed(s: str, fd: Dict, each: Dict) -> bool:
    """A fund whose own fetch just failed takes the PC's rows when they are newer than what is stored.  The fetch time
    becomes the time the PC fetched them (never now), and every row passes the same validation as a direct fetch."""
    try:
        j = json.loads(SEED.read_text(encoding="utf-8")) if SEED.exists() else {}
        t, raw = float((j.get("ts_each") or {}).get(s) or 0), (j.get("funds") or {}).get(s) or []
        if t <= float(each.get(s) or 0) or t > time.time() + 600:
            return False
        rows = [_good(str(r[0]), float(r[1]), float(r[2])) for r in raw]
    except Exception as e:  # noqa: BLE001
        log.warning("ETF flows seed for %s unusable: %s", s, e)
        return False
    if not rows:
        return False
    fd["rows"], fd["via"], each[s] = merge(fd.get("rows") or [], rows), "seed", t
    fd.pop("err", None)
    return True


async def refresh(force: bool = False) -> Dict:
    d = load()
    funds, each = d.setdefault("funds", {}), d.setdefault("ts_each", {})
    errs, got, t0 = [], 0, time.time()
    for f in FUNDS:
        s = f["sym"]
        fd = funds.setdefault(s, {"rows": []})
        if not force and t0 - float(each.get(s, 0)) < TTL and fd.get("rows") and not fd.get("err") and not fd.get("via"):
            continue
        try:
            rows = await _fetch(f)
            fd["rows"] = merge(fd.get("rows") or [], rows)
            fd.pop("err", None)
            fd.pop("via", None)
            each[s] = time.time()
            d["ts"] = each[s]
            got += 1
            _save(d)                                     # a timeout on a later fund must not lose this one
        except Exception as e:  # noqa: BLE001   the stored history and the fetch time stay as they were
            log.warning("ETF flows %s failed: %s", s, e)
            if _from_seed(s, fd, each):
                d["ts"] = max(float(d.get("ts") or 0), each[s])
                _save(d)
                continue
            if fd.get("via"):                            # still living on an older seed: its date keeps showing, no new error
                continue
            fd["err"] = type(e).__name__
            errs.append(f"{s}: {e}")
    if errs:
        HEALTH.fail("etf_flows", "; ".join(errs)[:300], every=TTL)
    elif got:
        HEALTH.ok("etf_flows", got, every=TTL)
    _save(d)
    return d


def status(d: Optional[Dict] = None) -> Tuple[Optional[float], Optional[str]]:
    """The weakest link across funds with data: the oldest fetch time and the oldest latest-data date, so a card built
    from one stuck fund and four healthy ones still shows the stuck date."""
    d = load() if d is None else d
    fs = {k: v for k, v in (d.get("funds") or {}).items() if v.get("rows")}
    if not fs:
        return None, None
    each = d.get("ts_each") or {}
    ts = [float(each.get(k) or 0) for k in fs]
    return (min(ts) or None), min(v["rows"][-1][0] for v in fs.values())
