"""財報日曆的官方備援：Nasdaq 財報日曆擋掉 GitHub Actions 時，「哪家公司哪天公布了財報」改看美國證交會（SEC）的申報。

  * 來源：data.sec.gov/submissions/CIK##########.json（SEC 官方，免金鑰，要帶 User-Agent）
  * 判斷：8-K 申報且項目含 Item 2.02（Results of Operations and Financial Condition，公司公布季度營運結果時依規定申報）
  * 時間：SEC 收件時間（acceptanceDateTime，UTC）換成美東：09:30 前＝盤前、16:00 後＝盤後、其間＝盤中
  * 範圍：追蹤池＋快取裡出現過、市值 ≥ 1,000 億美元的公司（市值沿用最後一次 Nasdaq 紀錄，只用來排序與篩選）

限制（官方沒有，不補）：分析師預期 EPS、預期家數、未來的財報日。外國公司（台積電 ADR、ASML 等）申報 6-K，沒有 Item 2.02，
所以不在備援範圍。實際 EPS 等 10-Q 申報後由 earnings_data.refresh_facts（SEC XBRL）補上。
列的格式和 Nasdaq 的一樣（sym / name / time / fq / eps_f / eps / mcap…），多一個 src="sec" 與申報連結。"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from ..config import DATA_DIR, SEC_USER_AGENT
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "earn_official.json"
SEC_HDR = {"User-Agent": SEC_USER_AGENT, "Accept": "application/json"}
DAY_S = 20 * 3600               # each company's filing list: once a day …
NEAR_S = 3600                   # … hourly while it is expected to report (a cached calendar row within ±2 days)


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except (OSError, ValueError):
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")
    tmp.replace(FILE)


def session_of(accepted: str) -> str:
    """SEC acceptance time (UTC ISO) → pre / after / "" (during the session) on the US-Eastern clock."""
    from zoneinfo import ZoneInfo
    try:
        t = datetime.fromisoformat(accepted.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return ""
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    et = t.astimezone(ZoneInfo("America/New_York"))
    m = et.hour * 60 + et.minute
    return "pre" if m < 9 * 60 + 30 else "after" if m >= 16 * 60 else ""


def et_day(accepted: str, fallback: str) -> str:
    from zoneinfo import ZoneInfo
    try:
        t = datetime.fromisoformat(accepted.replace("Z", "+00:00"))
        return t.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    except (ValueError, AttributeError):
        return fallback


def parse_202(js: Dict, since: str) -> List[Dict]:
    """8-K filings with Item 2.02 on or after `since`: [{date, time, accession, url}] (newest first)."""
    f = ((js or {}).get("filings") or {}).get("recent") or {}
    forms, items = f.get("form") or [], f.get("items") or []
    cik = str(js.get("cik") or "").lstrip("0")
    out, reps = [], []
    for i, form in enumerate(forms):
        is202 = form == "8-K" and "2.02" in str(items[i] if i < len(items) else "")
        if not (is202 or form in ("10-Q", "10-K")):
            continue
        acc = (f.get("acceptanceDateTime") or [""] * len(forms))[i]
        day = et_day(acc, (f.get("filingDate") or [""] * len(forms))[i])
        an = (f.get("accessionNumber") or [""] * len(forms))[i]
        doc = (f.get("primaryDocument") or [""] * len(forms))[i]
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{an.replace('-', '')}/{doc}" if cik and an and doc else ""
        reps.append({"date": day, "time": session_of(acc), "acc": an, "url": url, "form": "8-K" if is202 else form})
    k8 = sorted(r["date"] for r in reps if r["form"] == "8-K")
    for r in reps:
        if r["date"] < since:
            continue
        if r["form"] != "8-K":
            # some companies (e.g. OKLO) publish results without an 8-K Item 2.02: their 10-Q / 10-K day is the report day,
            # but only when no 8-K 2.02 came in the 75 days before it (otherwise the 10-Q is the later, routine filing)
            lo = (date.fromisoformat(r["date"]) - timedelta(days=75)).isoformat()
            if any(lo <= d <= r["date"] for d in k8):
                continue
        out.append(r)
    return out


def universe(days: Dict[str, Dict], extra: List[str], known: Optional[Dict[str, Dict]] = None) -> Dict[str, Dict]:
    """{sym: {name, mcap}} — the tracked list plus every ≥ $100B company the cached calendar has seen. `known` is the list
    saved by earlier runs, so names do not drop out while Nasdaq stays blocked and the calendar window rolls forward."""
    last: Dict[str, Dict] = {k: dict(v) for k, v in (known or {}).items()}
    for d in sorted(days):
        for r in (days[d] or {}).get("rows") or []:
            if r.get("sym"):
                last[r["sym"]] = {"name": r.get("name") or r["sym"], "mcap": r.get("mcap") or last.get(r["sym"], {}).get("mcap")}
    out = {s: last.get(s, {"name": s, "mcap": None}) for s in extra}
    out.update({s: v for s, v in last.items() if (v.get("mcap") or 0) >= 1e11})
    return out


def _near(days: Dict[str, Dict], sym: str, today: date) -> bool:
    for i in range(-2, 3):
        rec = days.get((today + timedelta(days=i)).isoformat()) or {}
        if any(r.get("sym") == sym for r in rec.get("rows") or []):
            return True
    return False


def merge_day(rows: List[Dict], new: Dict) -> bool:
    """Add one SEC-reported company to a day's rows unless the day already lists it (a Nasdaq row keeps its consensus)."""
    if any(r.get("sym") == new["sym"] for r in rows):
        return False
    rows.append(new)
    return True


async def fill(days: Dict[str, Dict], extra: List[str], today: date, back: int, budget_s: float = 60,
               tmap: Optional[Dict] = None) -> int:
    """Add SEC 8-K Item 2.02 reports of the last `back` days to the calendar cache. Returns the number of rows added."""
    if tmap is None:
        from .edgar_holdings import ticker_map
        tmap = await ticker_map()
    st = load()
    seen = st.setdefault("subs", {})                     # sym → {ts, reps}
    since = (today - timedelta(days=back)).isoformat()
    t0, added, calls = time.time(), 0, 0
    uni = universe(days, extra, st.get("known"))
    st["known"] = {k: v for k, v in uni.items() if (v.get("mcap") or 0) >= 1e11}
    # due first: companies expected to report around now, then the oldest checks
    order = sorted(uni, key=lambda s: (not _near(days, s, today), float((seen.get(s) or {}).get("ts", 0))))
    for s in order:
        rec = seen.get(s) or {}
        age = time.time() - float(rec.get("ts", 0))
        if age < (NEAR_S if _near(days, s, today) else DAY_S):
            continue
        if time.time() - t0 > budget_s:
            break
        cik = (tmap.get(s) or tmap.get(s.replace("-", ".")) or {}).get("cik")
        if not cik:
            continue
        try:
            js = await http.get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", headers=SEC_HDR, timeout=30, retries=1)
            calls += 1
            seen[s] = {"ts": time.time(), "reps": parse_202(js, (today - timedelta(days=400)).isoformat())}
        except Exception as e:  # noqa: BLE001
            log.info("SEC submissions %s: %s", s, e)
        await asyncio.sleep(0.15)                         # SEC allows 10 requests a second
    for s, rec in seen.items():
        if s not in uni:
            continue
        for rp in rec.get("reps") or []:
            if not since <= rp["date"] <= today.isoformat():
                continue
            day = days.setdefault(rp["date"], {"ts": time.time(), "rows": [], "final": False})
            rows = day.setdefault("rows", [])
            row = {"sym": s, "name": uni[s].get("name") or s, "time": rp["time"], "fq": "", "eps_f": None, "n_est": None,
                   "eps_ly": None, "mcap": uni[s].get("mcap"), "eps": None, "surprise": None, "src": "sec", "url": rp.get("url", "")}
            if merge_day(rows, row):
                day["src_fallback"] = "sec"
                added += 1
    st["ts"] = time.time()
    _save(st)
    log.info("earnings official (SEC 8-K 2.02): %d requests, %d rows added", calls, added)
    return added
