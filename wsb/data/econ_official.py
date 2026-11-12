"""財經日曆的官方備援：Nasdaq 經濟日曆擋掉 GitHub Actions（2026-11-10 起每次 403）時，改用聖路易聯準會 FRED 的官方資料。

  * 發布日程：FRED releases/dates（一次呼叫拿到各機關排定的發布日；BLS、BEA、Census、聯準會、DOL 的官方日程）
  * 公布值與前值：FRED 的「即時版本」（ALFRED）：查發布前一天到發布當天的資料版本，發布當天才出現的那一期就是這次公布的數字，
    前值＝同一版本裡的上一期。月增／年增從官方指數自己算（CPI、PPI 年增用未季調指數，和官方標題數字同一個算法）。
  * 預期值：官方沒有預期值。ForexFactory 本週預期（econcal.ff_week）照舊補；過去的預期值保留 Nasdaq 擋掉前已存的紀錄。
  * 公布時間：各機關固定的美東時間（BLS 08:30、聯準會工業生產 09:15、JOLTS 10:00…），寫在 SPECS，和官方日程一致。

列的格式和 Nasdaq 的一樣（name / utc / actual / cons / prev），所以 macro_events、event_react 不用改；多一個 src="fred"。
ISM（不在 FRED）與耐久財訂單（FRED 日程沒有預告日）不在備援範圍。"""
from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR, FRED_API_KEY
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_official.json"
API = "https://api.stlouisfed.org/fred/"
SCHED_TTL = 12 * 3600
MAX_CALLS = 16                  # FRED allows ~120 calls/min shared with the rest of the build; a refresh stays well below

# FRED release id → (美東時, 分, [(Nasdaq 列名, variant, FRED series, 算法, 格式)])
#   算法：mm 月增% · yy 年增%（12 期前）· diff 差額（千人）· lvl 原值   格式：pct 一位小數加 % · k 千 · M 百萬（三位）· n 一位小數
SPECS: Dict[int, Tuple[int, int, List[Tuple[str, str, str, str, str]]]] = {
    10: (8, 30, [("CPI", "m", "CPIAUCSL", "mm", "pct"), ("CPI", "y", "CPIAUCNS", "yy", "pct"),
                 ("Core CPI", "m", "CPILFESL", "mm", "pct"), ("Core CPI", "y", "CPILFENS", "yy", "pct")]),
    50: (8, 30, [("Nonfarm Payrolls", "", "PAYEMS", "diff", "k"), ("Unemployment Rate", "", "UNRATE", "lvl", "pct"),
                 ("Average Hourly Earnings", "", "CES0500000003", "mm", "pct"),
                 ("Average Hourly Earnings (YoY)", "", "CES0500000003", "yy", "pct")]),
    46: (8, 30, [("PPI", "m", "PPIFIS", "mm", "pct"), ("PPI", "y", "PPIFID", "yy", "pct"),
                 ("Core PPI", "m", "PPIFES", "mm", "pct"), ("Core PPI", "y", "PPICOR", "yy", "pct")]),
    54: (8, 30, [("Core PCE Price Index", "m", "PCEPILFE", "mm", "pct"), ("Core PCE Price Index", "y", "PCEPILFE", "yy", "pct"),
                 ("PCE price index", "m", "PCEPI", "mm", "pct"), ("PCE price index", "y", "PCEPI", "yy", "pct"),
                 ("Personal Spending", "", "PCE", "mm", "pct"), ("Personal Income", "", "PI", "mm", "pct")]),
    53: (8, 30, [("GDP", "", "A191RL1Q225SBEA", "lvl", "pct"), ("GDP Price Index", "", "A191RI1Q225SBEA", "lvl", "pct")]),
    9: (8, 30, [("Retail Sales", "m", "RSAFS", "mm", "pct"), ("Core Retail Sales", "", "RSFSXMV", "mm", "pct")]),
    13: (9, 15, [("Industrial Production", "m", "INDPRO", "mm", "pct")]),
    192: (10, 0, [("JOLTS Job Openings", "", "JTSJOL", "lvl", "M")]),
    180: (8, 30, [("Initial Jobless Claims", "", "ICSA", "lvl", "kn"), ("Continuing Jobless Claims", "", "CCSA", "lvl", "kn")]),
    91: (10, 0, [("Michigan Consumer Sentiment", "", "UMCSENT", "lvl", "n")]),
}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except (OSError, ValueError):
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")
    tmp.replace(FILE)


def et_utc(day: str, hh: int, mm: int) -> str:
    from zoneinfo import ZoneInfo
    d = date.fromisoformat(day)
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


async def _fred(path: str, **params) -> Dict:
    params.update(api_key=FRED_API_KEY, file_type="json")
    return await http.get(API + path, params=params, timeout=25, retries=1)


async def schedule(today: date, ahead: int, force: bool = False) -> Dict[str, List[int]]:
    """{date: [release ids we cover]} for [today-10, today+ahead], cached 12 h (one FRED call)."""
    d = load()
    sc = d.get("sched") or {}
    if not force and sc and time.time() - float(d.get("ts_sched", 0)) < SCHED_TTL and sc.get("_end", "") >= (today + timedelta(days=ahead - 7)).isoformat():
        return {k: v for k, v in sc.items() if not k.startswith("_")}
    js = await _fred("releases/dates", realtime_start=(today - timedelta(days=10)).isoformat(),
                     realtime_end=(today + timedelta(days=ahead)).isoformat(), include_release_dates_with_no_data="true",
                     limit=1000, order_by="release_date", sort_order="asc")
    out: Dict[str, List[int]] = {}
    for x in js.get("release_dates") or []:
        rid = int(x.get("release_id") or 0)
        if rid in SPECS and x.get("date"):
            out.setdefault(x["date"], [])
            if rid not in out[x["date"]]:
                out[x["date"]].append(rid)
    d["sched"] = {**out, "_end": (today + timedelta(days=ahead)).isoformat()}
    d["ts_sched"] = time.time()
    _save(d)
    return out


def fmt(v: float, f: str) -> str:
    if f == "pct":
        return f"{v:.1f}%"
    if f == "k":
        return f"{v:,.0f}K"
    if f == "kn":                       # a raw count → thousands
        return f"{v / 1000:,.0f}K"
    if f == "M":                        # thousands → millions
        return f"{v / 1000:.3f}M"
    return f"{v:.1f}"


def transform(vals: List[Tuple[str, float]], how: str) -> List[Tuple[str, float]]:
    """[(date, value)] sorted → [(date, transformed)] (mm / yy / diff / lvl)."""
    out = []
    lag = 12 if how == "yy" else 1
    for i, (dt, v) in enumerate(vals):
        if how == "lvl":
            out.append((dt, v))
        elif i >= lag:
            p = vals[i - lag][1]
            if how == "diff":
                out.append((dt, v - p))
            elif p:
                out.append((dt, (v / p - 1) * 100))
    return out


def released_on(obs: List[Dict], day: str) -> Optional[List[Tuple[str, float]]]:
    """Observations of the data version valid on `day`, only if `day` added a new period (else None: not out yet on FRED).
    obs = FRED observations queried with realtime_start=day-1, realtime_end=day (FRED clamps the vintage dates to that window)."""
    def ok(x):
        try:
            float(x["value"])
            return True
        except (KeyError, ValueError, TypeError):
            return False
    now = sorted(((x["date"], float(x["value"])) for x in obs if x.get("realtime_end") == day and ok(x)))
    before = [x["date"] for x in obs if x.get("realtime_start", "") < day and ok(x)]
    if not now or (before and max(before) >= now[-1][0]):
        return None
    return now


async def values(day: str, rid: int, cache: Dict[str, List]) -> List[Dict]:
    """Rows for one release on `day` with actual / prev filled when FRED already carries the new period."""
    hh, mm, spec = SPECS[rid]
    utc = et_utc(day, hh, mm)
    prior = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    start = (date.fromisoformat(day) - timedelta(days=430)).isoformat()
    rows = []
    for name, var, sid, how, f in spec:
        key = f"{sid}|{day}"
        if key not in cache:
            js = await _fred("series/observations", series_id=sid, realtime_start=prior, realtime_end=day, observation_start=start)
            cache[key] = released_on(js.get("observations") or [], day)
        vals = cache[key]
        r = {"name": name, "var": var, "utc": utc, "actual": "", "cons": "", "prev": "", "src": "fred"}
        if vals:
            t = transform(vals, how)
            if t and t[-1][0] == vals[-1][0]:
                r["actual"] = fmt(t[-1][1], f)
                r["period"] = t[-1][0]
                if len(t) >= 2:
                    r["prev"] = fmt(t[-2][1], f)
        rows.append(r)
    return rows


def _mag(r: Dict) -> float:
    from .econcal import num
    for k in ("actual", "cons", "prev"):
        v = num(r.get(k))
        if v is not None:
            return abs(v)
    return 0.0


def merge(old: List[Dict], new: List[Dict], ff: Optional[List[Dict]] = None) -> List[Dict]:
    """Put official rows into a day's existing rows. A Nasdaq row with the same name keeps its consensus and gets the official
    actual / previous only where it is blank; two same-named rows (m/m and y/y) match by size (the smaller is m/m).
    A name the day does not have yet is added; ForexFactory's forecast fills its consensus so the history keeps it."""
    from .econcal import num
    out = [dict(r) for r in old]
    orig = {id(r): r for r in out}

    def ref(r):
        for k in ("prev", "cons", "actual"):
            v = num(r.get(k))
            if v is not None:
                return v
        return None

    for n in new:
        same = [r for r in out if r["name"].lower() == n["name"].lower() and id(r) in orig]
        if len(same) >= 2 and n.get("var"):
            same = sorted(same, key=_mag)
            tgt = same[0] if n["var"] == "m" else same[-1]
        elif len(same) == 1 and n.get("var"):
            # one existing row, official m/m and y/y: it belongs to whichever official row its previous value is closer to
            twins = [x for x in new if x["name"].lower() == n["name"].lower() and x.get("var")]
            e = ref(same[0])
            if e is None or len(twins) < 2:
                tgt = same[0]
            else:
                best = min(twins, key=lambda x: abs((ref(x) if ref(x) is not None else 1e9) - e))
                tgt = same[0] if best is n else None
                if tgt is None:
                    same = []                       # the other variant: added as its own row below
        else:
            tgt = same[0] if len(same) == 1 else None
        if tgt is None and same:
            continue
        if tgt is None:
            row = {k: v for k, v in n.items() if k != "var"}
            f = next((x for x in ff or [] if x["date"] == n["utc"][:10] and x["name"].lower() == n["name"].lower()
                      and (not n["var"] or not x["var"] or x["var"] == n["var"])), None) if ff else None
            if f and f.get("forecast"):
                row["cons"] = f["forecast"]
            out.append(row)
            continue
        if not tgt.get("actual") and n.get("actual"):
            tgt["actual"], tgt["src"] = n["actual"], "fred"
            if not tgt.get("prev"):
                tgt["prev"] = n.get("prev", "")
        if not tgt.get("utc"):
            tgt["utc"] = n["utc"]
    return out


async def fill(days: Dict[str, Dict], today: date, ahead: int, ff: Optional[List[Dict]] = None) -> int:
    """Fill the day cache from official sources: future release days get their rows (no values yet), released days in the
    last 7 days get actual / previous. Returns the number of days changed. Needs FRED_API_KEY."""
    if not FRED_API_KEY:
        return 0
    sc = await schedule(today, ahead)
    calls, changed, cache = 0, 0, {}
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lo, hi = (today - timedelta(days=7)).isoformat(), (today + timedelta(days=ahead)).isoformat()
    for day in sorted(sc):
        if not lo <= day <= hi:
            continue
        rec = days.get(day) or {"ts": time.time(), "rows": [], "final": False}
        rows = rec.get("rows") or []
        for rid in sc[day]:
            hh, mm, spec = SPECS[rid]
            names = {s[0].lower() for s in spec}
            have = [r for r in rows if r["name"].lower() in names]
            out = et_utc(day, hh, mm) <= now
            need = out and (not have or any(not r.get("actual") for r in have))
            if need and calls + len(spec) <= MAX_CALLS:
                try:
                    new = await values(day, rid, cache)
                    calls += len(spec)
                except Exception as e:  # noqa: BLE001
                    log.info("official %s %s: %s", day, rid, e)
                    calls = MAX_CALLS                   # FRED trouble → stop for this round
                    continue
            elif not have:
                new = [{"name": n, "var": v, "utc": et_utc(day, hh, mm), "actual": "", "cons": "", "prev": "", "src": "fred"}
                       for n, v, *_ in spec]
            else:
                continue
            merged = merge(rows, new, ff)
            if merged != rows:
                rows = merged
                rec.update(rows=rows, ts=time.time(), src_fallback="fred")
                days[day] = rec
                changed += 1
    return changed
