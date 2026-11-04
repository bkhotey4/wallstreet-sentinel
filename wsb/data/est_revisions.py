"""分析師獲利預估修正趨勢：每天存一份「下一季每股盈餘（EPS）共識預估」的快照，看預估整體往上修還是往下修、速度多快。

來源：Nasdaq 公開 JSON（資料由 Zacks 提供）。estimate-momentum 給目前、1 週前、1 個月前的共識與 4 週內上修／下修人數；
earnings-forecast 給分析師人數。不用 Yahoo quoteSummary（要 crumb 驗證，不繞過）。只存 EPS 預估，不碰股價預估。

歷史：本站自己的快照從第一次成功抓取那天開始累積，7／30 天比較優先用本站快照（同一財季才比）；快照還不夠久時用 Nasdaq
提供的 1 週前／1 個月前共識，並在頁面標明。Nasdaq 標示的「當季」不一定是下一份要公布的財報（少數公司已往後滾動一季），
所以永遠以它標示的財季為準。

失敗處理：抓不到就保留上一筆，ts 不前進；要有一半以上的公司在最近一天內更新過，ts 才算新。快取 data_cache/earn_estrev.json。"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import date, timedelta
from statistics import median
from typing import Dict, Iterable, List, Optional, Tuple

from ..config import DATA_DIR
from ..health import HEALTH
from . import http
from .econcal import NQ_HDR, num, us_today

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_estrev.json"
BASE = "https://api.nasdaq.com/api/analyst"
DAY_S = 20 * 3600                # one snapshot per symbol per day
RETRY_S = 3600                   # a failed symbol waits this long
WORKERS = 3                      # requests at a time; one by one, 400 names would not finish in a day of passes
N_TTL = 7 * 86400                # analyst counts move slowly: one extra request per symbol per week
NONE_TTL = 7 * 86400             # symbols Nasdaq has no estimates for (e.g. BRK.B) are asked again weekly
FRESH_S = 26 * 3600
HIST_KEEP = 120                  # snapshots per symbol
MAX_SYMS = 400                   # large caps on the earnings calendar, on top of the curated universe
MIN_MCAP = 1e10                  # the size the site already uses for revision tracking (canary.record_revisions)
EPS_PCT = 0.5                    # a change under 0.5% is rounding, not a revision (same line as sector_brief.rev_block)
MIN_BASE = 0.10                  # |EPS| below this makes percentages meaningless: use the sign of the change only
MOVER_BASE, MOVER_N = 0.25, 3    # the biggest-change list needs a real base and at least 3 analysts
HORIZONS = (7, 30)
STALE_DAYS = 3                   # a symbol older than the newest snapshot by more than this leaves the counts


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, FILE)


def parse_momentum(js: Dict) -> Optional[Dict]:
    data = (js or {}).get("data") or {}
    c = data.get("changeInConsensus") or {}
    ec = data.get("estimatesChanged") or {}
    fq = str(c.get("fiscalQtrEndText") or "").replace("Fiscal Quarter End", "").strip()
    cur = num((c.get("currentData") or {}).get("qtrMean"))
    if not fq or cur is None:
        return None
    return {"fq": fq, "eps": cur, "wk": num((c.get("weekData") or {}).get("qtrMean")), "mo": num((c.get("monthData") or {}).get("qtrMean")),
            "up": num((ec.get("quarterDataUp") or {}).get("changeValue")), "dn": num((ec.get("quarterDataDown") or {}).get("changeValue"))}


def parse_forecast(js: Dict) -> Optional[Tuple[str, float]]:
    rows = (((js or {}).get("data") or {}).get("quarterlyForecast") or {}).get("rows") or []
    if not rows:
        return None
    n = num(rows[0].get("noOfEstimates"))
    return (str(rows[0].get("fiscalEnd") or ""), n) if n is not None else None


def symbols(days: Optional[Dict] = None, today: Optional[date] = None) -> List[str]:
    """The earnings universe: the curated US list, then the largest names on the earnings calendar (≥ $10B, one full
    quarterly cycle back, so a name does not drop out the day after it reports)."""
    from .stocks import universe
    cur = list((universe().get("us") or {}).get("symbols", {}))
    today = today or us_today()
    lo, big = (today - timedelta(days=100)).isoformat(), {}
    for d, rec in (days or {}).items():
        if d < lo:
            continue
        for r in rec.get("rows", []):
            if r.get("sym") and (r.get("mcap") or 0) >= MIN_MCAP:
                big[r["sym"]] = max(big.get(r["sym"], 0), r["mcap"])
    top = sorted(big, key=lambda s: -big[s])[:MAX_SYMS]
    return list(dict.fromkeys(cur + top))


async def _get(sym: str, ep: str) -> Dict:
    return await http.get(f"{BASE}/{sym.replace('-', '.')}/{ep}", headers=NQ_HDR, timeout=20, retries=1)


def _snap(d: Dict, sym: str, got: Dict, today: str, now: float) -> None:
    recs, hist = d["syms"], d["hist"]
    old = recs.get(sym) or {}
    rec = {**old, **got, "ts": now, "try": now, "d": today}
    rec.pop("none", None)
    recs[sym] = rec
    h = hist.setdefault(sym, [])
    if h and h[-1][0] == today:
        h.pop()
    h.append([today, got["fq"], got["eps"]])
    del h[:-HIST_KEEP]
    if not d.get("first"):
        d["first"] = today


async def refresh(syms: Iterable[str], budget_s: float = 120, force: bool = False) -> Dict:
    """Pick up where the last pass stopped: each symbol is due once a day.  Nothing a failed request touches changes."""
    d = load()
    d.setdefault("syms", {})
    d.setdefault("hist", {})
    syms = list(syms)
    today, t0 = us_today().isoformat(), time.time()
    ok, bad, empty = 0, 0, []
    gate = asyncio.Semaphore(WORKERS)

    async def one(s: str) -> Tuple[int, int]:
        async with gate:
            r = d["syms"].get(s) or {}
            now = time.time()
            if now - t0 > budget_s:
                return 0, 0
            r["try"] = now
            d["syms"][s] = r
            try:
                got = parse_momentum(await _get(s, "estimate-momentum"))
                if got is None:
                    empty.append(s)                           # judged after the pass: a broken feed is not "no coverage"
                    return 0, 0
                rolled = bool(r.get("fq")) and r["fq"] != got["fq"]
                if rolled:                                    # the analyst count of the old quarter no longer applies
                    r.pop("n", None)
                    r.pop("n_ts", None)
                if rolled or now - float(r.get("n_ts", 0)) > N_TTL:
                    try:
                        f = parse_forecast(await _get(s, "earnings-forecast"))
                        if f and f[0] == got["fq"]:           # the count must belong to the quarter being tracked
                            got.update(n=f[1], n_ts=now)
                    except Exception as e:  # noqa: BLE001
                        log.info("estimate count %s: %s", s, e)
                _snap(d, s, got, today, now)
                return 1, 0
            except Exception as e:  # noqa: BLE001
                log.info("estimate revisions %s: %s", s, e if str(e) else type(e).__name__)
                return 0, 1
            finally:
                await asyncio.sleep(0.25)

    def due(s: str) -> bool:
        r, now = d["syms"].get(s) or {}, time.time()
        wait = NONE_TTL if r.get("none") else RETRY_S
        return force or (now - float(r.get("ts", 0)) >= DAY_S and now - float(r.get("try", 0)) >= wait)
    for a, b in await asyncio.gather(*(one(s) for s in syms if due(s))):
        ok, bad = ok + a, bad + b
    if ok:                                                    # at least one answered: an empty symbol really has no estimates
        for s in empty:
            if not d["syms"][s].get("eps"):
                d["syms"][s]["none"] = True
    now = time.time()
    live = [s for s in syms if not (d["syms"].get(s) or {}).get("none")]
    fresh = sum(1 for s in live if now - float((d["syms"].get(s) or {}).get("ts", 0)) < FRESH_S)
    d["cov"] = [fresh, len(live)]
    if ok and live and fresh * 2 >= len(live):                # a handful of symbols must not make the whole card look current
        d["ts"] = now
    if ok or empty or bad:
        dates = [r["d"] for r in d["syms"].values() if r.get("d")]
        d["asof"] = max(dates) if dates else None
        _save(d)
    if (bad or empty) and not ok:
        HEALTH.fail("est_revisions", f"no estimate answered ({bad} failed, {len(empty)} empty)", every=DAY_S)
    elif ok:
        HEALTH.ok("est_revisions", fresh, every=DAY_S)
    return d


# ------------------------------------------------------------------ the view (pure: tested without a network)
def _dir(new: float, old: float) -> Tuple[int, Optional[float]]:
    """(direction, % change).  Tiny bases have no meaningful percentage: the sign of the change alone counts."""
    diff = new - old
    if abs(diff) < 0.005:
        return 0, 0.0
    if abs(old) < MIN_BASE:
        return (1 if diff > 0 else -1), None
    pct = diff / abs(old) * 100
    return (0 if abs(pct) < EPS_PCT else 1 if pct > 0 else -1), pct


def _baseline(sym: str, rec: Dict, hist: List, days: int, today: date) -> Tuple[Optional[float], str]:
    """Own snapshot of the same fiscal quarter if one is old enough, otherwise Nasdaq's own look-back."""
    cut = (today - timedelta(days=days)).isoformat()
    own = [x for x in hist or [] if x[0] <= cut and x[1] == rec.get("fq")]
    if own:
        return own[-1][2], "own"
    v = rec.get("wk" if days == 7 else "mo")
    return (v, "src") if v is not None else (None, "")


def view(d: Optional[Dict] = None) -> Dict:
    d = load() if d is None else d
    recs = {s: r for s, r in (d.get("syms") or {}).items() if r.get("eps") is not None and r.get("d")}
    asof = d.get("asof") or (max(r["d"] for r in recs.values()) if recs else None)
    if len(recs) < 10 or not asof:
        return {"available": False, "asof": asof, "first": d.get("first"), "n": len(recs)}
    today = date.fromisoformat(asof)
    cut = (today - timedelta(days=STALE_DAYS)).isoformat()
    live = {s: r for s, r in recs.items() if r["d"] >= cut}
    out: Dict = {"available": True, "asof": asof, "first": d.get("first"), "ts": d.get("ts"), "cov": d.get("cov"), "n": len(live),
                 "n_all": len(recs), "days": (today - date.fromisoformat(d["first"])).days if d.get("first") else 0, "h": {}}
    for hz in HORIZONS:
        up, dn, flat, chg, own, src, rows = 0, 0, 0, [], 0, 0, []
        for s, r in live.items():
            base, how = _baseline(s, r, (d.get("hist") or {}).get(s), hz, today)
            if base is None:
                continue
            di, pct = _dir(r["eps"], base)
            up, dn, flat = up + (di > 0), dn + (di < 0), flat + (di == 0)
            own, src = own + (how == "own"), src + (how == "src")
            if pct is not None:
                chg.append(pct)
                if di and abs(base) >= MOVER_BASE and (r.get("n") or 0) >= MOVER_N:
                    rows.append({"sym": s, "fq": r["fq"], "old": base, "new": r["eps"], "pct": pct, "n": r.get("n")})
        n = up + dn + flat
        if not n:
            continue
        rows.sort(key=lambda x: -x["pct"])
        out["h"][hz] = {"n": n, "up": up, "dn": dn, "flat": flat, "up_pct": up / n * 100, "dn_pct": dn / n * 100, "net": (up - dn) / n * 100,
                        "med": median(chg) if chg else None, "own": own, "src": src,
                        "top": [x for x in rows[:5] if x["pct"] > 0], "low": [x for x in rows[::-1][:5] if x["pct"] < 0]}
    a, b = out["h"].get(7), out["h"].get(30)
    if a and b:
        gap = a["net"] - b["net"] * 7 / 30                    # this week's net share vs the 30-day pace per week
        out["speed"] = "steady" if abs(gap) < 2 else "up" if gap > 0 else "down"
    out["available"] = bool(out["h"])
    return out
