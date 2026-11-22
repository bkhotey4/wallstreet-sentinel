"""台指期夜盤（盤後交易時段）收盤，開盤前可用（2026-11-22，台股覆蓋清單「夜盤」）。

來源：臺灣期貨交易所「期貨每日交易行情查詢」 https://www.taifex.com.tw/cht/3/futDailyMarketReport
POST queryType=2、marketCode=1（盤後交易時段）、commodity_id=TX、queryDate＝夜盤所屬的「下一個交易日」。
例：週五 15:00～週六 05:00 的夜盤，queryDate 要帶下週一；頁面標題會寫「2026/11/20 15:00~次日05:00 盤後交易時段行情表」。
Gemini v24 TWC-3 給的口徑，Claude 11-22（週日）實測：週五夜盤資料已經可以取得（OpenAPI DailyMarketReportFut 要等下一個交易日才有）。
漲跌是對前一個一般交易時段（日盤）的結算價。這是期貨價格，不是加權指數；換算只是算術，不是預測。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "tw_night.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_night_seed.json"
URL = "https://www.taifex.com.tw/cht/3/futDailyMarketReport"
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
TTL = 1800
TPE = timezone(timedelta(hours=8))


def _num(s: str) -> Optional[float]:
    s = re.sub(r"[▲▼,%\s]", "", s or "")
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def parse(page: str) -> Dict:
    """Session start date from the title, then every TX outright month (spreads like 202612/202701 are skipped)."""
    m = re.search(r"(\d{4})/(\d{2})/(\d{2})(?:&nbsp;|\s)*15:00~次日05:00\s*盤後交易時段行情表", page or "")
    if not m:
        return {}
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S | re.I):
        c = [re.sub(r"<[^>]+>|&nbsp;|\s+", " ", x).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
        if len(c) >= 15 and c[0] == "TX" and re.fullmatch(r"\d{6}(W\d)?", c[1]):
            sign = -1 if "▼" in c[6] else 1
            chg, pct = _num(c[6]), _num(c[7])
            rows.append({"month": c[1], "open": _num(c[2]), "high": _num(c[3]), "low": _num(c[4]), "last": _num(c[5]),
                         "chg": None if chg is None else sign * abs(chg), "pct": None if pct is None else sign * abs(pct),
                         "vol": _num(c[8])})
    if not rows:
        return {}
    near = max((r for r in rows if r["vol"] and not r["month"].endswith(tuple(f"W{i}" for i in range(1, 6)))), key=lambda r: r["vol"], default=rows[0])
    return {"session": f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "rows": rows, "near": near}


def light(pct: Optional[float]) -> str:
    """Self-set: the TX day move has a σ of about 1.3%; ±3% (~2.3σ) is red, ±1.5% yellow."""
    if pct is None:
        return ""
    return "🔴" if abs(pct) >= 3 else "🟡" if abs(pct) >= 1.5 else "🟢"


def query_dates(now: datetime) -> List[date]:
    """The trading date the latest finished night session belongs to: today on a weekday, else next Monday; then a few weekdays after
    (holidays: the page answers empty and we move on)."""
    d = now.date()
    while d.weekday() >= 5:
        d += timedelta(days=1)
    out = []
    while len(out) < 4:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _post(qd: date) -> str:
    import requests
    r = requests.post(URL, headers=UA, timeout=40,
                      data={"queryType": "2", "marketCode": "1", "commodity_id": "TX", "queryDate": qd.strftime("%Y/%m/%d")})
    r.raise_for_status()
    return r.content.decode("utf-8", errors="replace")


def _load(f) -> Dict:
    try:
        return json.loads(Path(f).read_text(encoding="utf-8")) if Path(f).exists() else {}
    except (OSError, ValueError):
        return {}


def refresh(force: bool = False, now: Optional[datetime] = None) -> Dict:
    d = _load(FILE)
    if not force and time.time() - float(d.get("ts") or 0) < TTL and d.get("near"):
        return _with_seed(d)
    now = now or datetime.now(TPE)
    got = {}
    for qd in query_dates(now):
        try:
            got = parse(_post(qd))
        except Exception as e:  # noqa: BLE001
            log.info("tx night %s unavailable: %s", qd, e)
            got = {}
        if got:
            got["for"] = qd.isoformat()
            break
    d = {**d, **got, "ts": time.time()} if got else {**d, "ts": time.time()}
    if got:
        d["fetched"] = now.strftime("%Y-%m-%d %H:%M")
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError:
        pass
    return _with_seed(d)


def _with_seed(d: Dict) -> Dict:
    s = _load(SEED)
    if s.get("session") and s["session"] > str(d.get("session") or ""):
        d = {**d, **{k: s[k] for k in ("session", "rows", "near", "for", "fetched") if k in s}}
    return d


def write_seed(path=SEED) -> Dict:
    d = refresh(force=True)
    out = {k: d.get(k) for k in ("session", "rows", "near", "for", "fetched")}
    if out.get("near"):
        Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
