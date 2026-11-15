"""美國政府停擺與債務上限倒數（2026-11-15，使用者選的 A-2）。全部官方資料、全部算出來，沒有寫死的日期或金額：

  * 政府撥款到期日：GovInfo 公法（PLAW）清單裡，這個會計年度（10/1 起算）的「Continuing Appropriations」法律，讀原文第 106 條
    第 (3) 款的到期日；之後的法律如果寫「把 106(3) 的某日改成某日」，以最新的為準。標題有「Full-Year」或
    「Consolidated Appropriations Act, 年度」→ 該年度大部分機關已拿到全年預算（到 9/30）。
  * 債務上限：財政部每日報表（Daily Treasury Statement）表 IIIC「Debt Subject to Limit」：法定上限、受上限約束的債務
    （公眾持有＋政府內部持有－不受上限約束的部分），兩者相減＝剩下的空間；最近 90 天平均每天增加多少 → 照這個速度幾個月用完。
    財政部用完空間後還能用「非常措施」再撐一段時間，所以「用完」不等於「違約日」。
  * 財政部現金（TGA）：同一份報表的一般帳戶期末餘額。

GovInfo 用 api.data.gov 的金鑰：沒有設 GOVINFO_API_KEY 就用公開的 DEMO_KEY（每小時 30 次），這裡 12 小時才查一次。
快取 data_cache/econ_us_fiscal.json。"""
from __future__ import annotations

import html as _html
import json
import logging
import os
import re
import time
from datetime import date, datetime
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_us_fiscal.json"
TTL = 12 * 3600
FD = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts"
FD_PAGE = "https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/debt-subject-to-limit"
GI = "https://api.govinfo.gov/collections/PLAW/{since}T00:00:00Z"
GI_PAGE = "https://www.govinfo.gov/app/collection/plaw"
HDR = {"User-Agent": "WallStreetSentinel research (public data reader)"}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DATE_RE = rf"(?:{MONTHS}) \d{{1,2}}, 20\d\d"


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def fiscal_year(d: date) -> int:
    return d.year + 1 if d.month >= 10 else d.year


def _d(s: str) -> Optional[str]:
    try:
        return datetime.strptime(s, "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


# ------------------------------------------------------------------ appropriations (pure, tested)
def law_kind(title: str, fy: int) -> Optional[str]:
    """'cr' | 'full' | None for one public-law title, for fiscal year fy."""
    t = title.lower()
    if str(fy) not in t or "appropriations" not in t:
        return None
    if "full-year" in t or f"consolidated appropriations act, {fy}" in t:
        return "full"
    if "continuing appropriations" in t:
        return "cr"
    return None


def cr_end(text: str) -> Optional[str]:
    """The expiry a continuing-resolution text sets or moves: an amendment of section 106(3) ('striking "X" and inserting
    "Y"') wins over an original 'Sec. 106 … (3) DATE'.  ISO date or None."""
    s = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", text)))
    s = re.sub(r"<<NOTE:[^>]*>>", " ", s)
    for m in re.finditer(r"106\(3\)", s):
        win = s[m.start(): m.start() + 400]
        mm = re.search(rf"striking [\"“]({DATE_RE})[\"”] and inserting [\"“]({DATE_RE})[\"”]", win)
        if mm:
            return _d(mm.group(2))
    m = re.search(r"Sec\. 106\.(.{0,900})", s)
    if m:
        mm = re.search(rf"\(3\)\s*({DATE_RE})", m.group(1))
        if mm:
            return _d(mm.group(1))
    return None


def funding_view(laws: List[Dict], today: date) -> Dict:
    """laws: [{id, date, title, kind, end}] for this fiscal year.  The latest dated CR end, whether a full-year act
    exists, days left, and the state: funded | cr | lapsed | unknown."""
    fy = fiscal_year(today)
    fy_end = date(fy, 9, 30).isoformat()
    crs = sorted((x for x in laws if x.get("kind") == "cr" and x.get("end")), key=lambda x: (x["date"], x["end"]))
    full = [x for x in laws if x.get("kind") == "full"]
    out: Dict = {"fy": fy, "laws": sorted(laws, key=lambda x: x["date"], reverse=True)[:6], "full": bool(full)}
    end = crs[-1]["end"] if crs else None
    if full and (not end or max(x["date"] for x in full) >= crs[-1]["date"]):
        out.update(state="funded", end=fy_end, law=max(full, key=lambda x: x["date"]))
    elif end:
        out.update(state="cr" if end >= today.isoformat() else "lapsed", end=end, law=crs[-1])
    else:
        out.update(state="unknown", end=None, law=None)
    if out.get("end"):
        out["days"] = (date.fromisoformat(out["end"]) - today).days
    return out


# ------------------------------------------------------------------ debt limit (pure, tested)
def debt_rows(data: List[Dict]) -> Dict[str, Dict[str, float]]:
    """fiscaldata rows (millions of dollars) → {date: {limit, subject}} with subject = held by the public + intragovernmental
    − not subject to limit + other debt subject to limit."""
    by: Dict[str, Dict[str, float]] = {}
    for r in data:
        try:
            v = float(r["close_today_bal"])
        except (KeyError, TypeError, ValueError):
            continue
        x = by.setdefault(r["record_date"], {"limit": None, "subject": 0.0, "n": 0})
        c = r.get("debt_catg")
        if c == "Statutory Debt Limit":
            x["limit"] = v
        elif c in ("Debt Held by the Public", "Intragovernmental Holdings", "Other Debt Subject to Limit"):
            x["subject"] += v
            x["n"] += 1
        elif c == "Debt Not Subject to Limit":
            x["subject"] -= v
    return {d: {"limit": x["limit"], "subject": x["subject"]} for d, x in by.items() if x["limit"] and x["n"] >= 2}


def debt_view(rows: Dict[str, Dict[str, float]], days: int = 90) -> Dict:
    if not rows:
        return {}
    ds = sorted(rows)
    last = rows[ds[-1]]
    room = last["limit"] - last["subject"]
    out = {"asof": ds[-1], "limit": last["limit"], "subject": last["subject"], "room": room, "used": last["subject"] / last["limit"]}
    old = [d for d in ds if (date.fromisoformat(ds[-1]) - date.fromisoformat(d)).days >= days]
    if old:
        d0 = old[-1]
        span = (date.fromisoformat(ds[-1]) - date.fromisoformat(d0)).days
        per_day = (last["subject"] - rows[d0]["subject"]) / span
        out.update(per_day=per_day, span=span)
        if per_day > 0 and room > 0:
            out["months"] = room / per_day / 30.44
    # when the limit last changed (a law raised or suspended it)
    for a, b in zip(ds, ds[1:]):
        if rows[a]["limit"] != rows[b]["limit"]:
            out["raised"] = b
    return out


# ------------------------------------------------------------------ alerts (pure, tested)
CR_STEPS = (14, 7, 3, 0)
DEBT_STEPS = (6, 3, 1)


def alerts(v: Dict) -> List[Dict]:
    """Discord-worthy stages, each once: funding deadline 14 / 7 / 3 days away or lapsed; debt-limit room under 6 / 3 / 1
    months at the recent pace.  key carries the deadline or the limit, so a new law starts a new series."""
    out = []
    f = v.get("funding") or {}
    if f.get("state") in ("cr", "lapsed") and f.get("days") is not None:
        st = next((s for s in sorted(CR_STEPS) if f["days"] <= s), None) if f["state"] == "cr" else -1
        if st is not None:
            out.append({"key": f"fiscal:cr:{f['end']}:{st}", "lv": 2 if st <= 3 else 1, "kind": "cr", "days": f["days"], "end": f["end"]})
    dv = v.get("debt") or {}
    if dv.get("months") is not None:
        st = next((s for s in sorted(DEBT_STEPS) if dv["months"] <= s), None)
        if st is not None:
            out.append({"key": f"fiscal:debt:{int(dv['limit'])}:{st}", "lv": 2 if st <= 1 else 1, "kind": "debt", "months": dv["months"]})
    return out


# ------------------------------------------------------------------ fetch
async def _laws(today: date, key: str) -> List[Dict]:
    fy = fiscal_year(today)
    since = f"{fy - 1}-08-01"
    out: List[Dict] = []
    url, params = GI.format(since=since), {"pageSize": "100", "offsetMark": "*", "api_key": key}
    for _ in range(4):
        js = json.loads(await http.get(url, params=params, kind="text", headers=HDR, timeout=40, retries=1))
        for p in js.get("packages") or []:
            k = law_kind(p.get("title") or "", fy)
            if k:
                out.append({"id": p["packageId"], "date": (p.get("dateIssued") or "")[:10], "title": p["title"], "kind": k})
        nxt = js.get("nextPage")
        if not nxt:
            break
        url, params = nxt, {"api_key": key}
    for x in out:
        if x["kind"] == "cr":
            txt = await http.get(f"https://www.govinfo.gov/content/pkg/{x['id']}/html/{x['id']}.htm", kind="text", headers=HDR, timeout=40, retries=1)
            x["end"] = cr_end(txt)
        x["url"] = f"https://www.govinfo.gov/app/details/{x['id']}"
    return out


async def _debt() -> Dict:
    js = json.loads(await http.get(f"{FD}/debt_subject_to_limit", params={"sort": "-record_date", "page[size]": "1500",
                                   "fields": "record_date,debt_catg,close_today_bal"}, kind="text", headers=HDR, timeout=40, retries=1))
    rows = debt_rows(js.get("data") or [])
    if not rows:
        raise ValueError("no debt rows")
    v = debt_view(rows)
    tga = json.loads(await http.get(f"{FD}/operating_cash_balance", params={"sort": "-record_date", "page[size]": "200",
                                    "fields": "record_date,account_type,open_today_bal"}, kind="text", headers=HDR, timeout=40, retries=1))
    bal = {r["record_date"]: float(r["open_today_bal"]) for r in tga.get("data") or []
           if "Closing Balance" in (r.get("account_type") or "") and r.get("open_today_bal") not in (None, "null")}
    if bal:
        ds = sorted(bal)
        v["tga"], v["tga_asof"] = bal[ds[-1]], ds[-1]
        prev = [d for d in ds if (date.fromisoformat(ds[-1]) - date.fromisoformat(d)).days >= 28]
        if prev:
            v["tga_chg"] = bal[ds[-1]] - bal[prev[-1]]
    return v


async def refresh(force: bool = False) -> Dict:
    from .freshness import due
    d = load()
    now = time.time()
    d["ts_check"] = now
    todo = due(d, ["debt", "laws"], TTL, now, force)
    bad = []
    if "debt" in todo:
        d["try_each"]["debt"] = now
        try:
            d["debt"] = await _debt()
            d["ts_each"]["debt"] = now
        except Exception as e:  # noqa: BLE001
            bad.append(f"debt: {e if str(e) else type(e).__name__}")
    if "laws" in todo:
        d["try_each"]["laws"] = now
        try:
            d["laws"] = await _laws(date.today(), os.environ.get("GOVINFO_API_KEY") or "DEMO_KEY")
            d["ts_each"]["laws"] = now
        except Exception as e:  # noqa: BLE001
            bad.append(f"laws: {e if str(e) else type(e).__name__}")
    if todo:
        d["ts"] = min(float(d["ts_each"].get(k, 0)) for k in ("debt", "laws"))
        if bad:
            log.warning("US fiscal: %s", "; ".join(bad))
            HEALTH.fail("us_fiscal", "; ".join(bad), every=TTL)
        else:
            HEALTH.ok("us_fiscal", len(d.get("laws") or []), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def view(d: Optional[Dict] = None, today: Optional[date] = None) -> Dict:
    d = load() if d is None else d
    today = today or date.today()
    return {"funding": funding_view(d.get("laws") or [], today) if d.get("laws") is not None else {},
            "debt": d.get("debt") or {}, "ts": d.get("ts"), "ts_each": d.get("ts_each") or {}}
