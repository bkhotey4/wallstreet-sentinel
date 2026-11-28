"""美債標售日曆：美國財政部 TreasuryDirect 官方 API 接下來要標售的公債（2026-11-28 總經缺口盤點：美債供需）。

為什麼：長天期美債標售的需求好壞（得標倍數、尾差）常是殖利率急升的導火線；本站有標售結果，卻沒有「接下來哪幾場」。
來源：https://www.treasurydirect.gov/TA_WS/securities/upcoming?format=json（公開、免金鑰）。API 的標售日欄位是空的，
只有「公布日」與「交割日」，所以卡上寫「標售日在兩者之間，以財政部公告為準」，不自己猜。只列中長期公債（Note／Bond），
國庫券每週都有、量大但對長期利率影響小。"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "ust_auctions.json"
URL = "https://www.treasurydirect.gov/TA_WS/securities/upcoming?format=json"
TTL = 6 * 3600
HDR = {"User-Agent": "Mozilla/5.0 (WallStreetSentinel research bot)"}


def parse(rows: List[Dict]) -> List[Dict]:
    """Pure: coupon securities only → [{type, term, announce, issue, amount_b}] sorted by issue date."""
    out = []
    for r in rows or []:
        if r.get("securityType") not in ("Note", "Bond") and "TIPS" not in str(r.get("securityTerm")):
            continue
        amt = r.get("offeringAmount")
        try:
            amt_b = float(amt) / 1e9 if amt else None
        except ValueError:
            amt_b = None
        out.append({"type": r.get("securityType"), "term": r.get("securityTerm"), "announce": str(r.get("announcementDate") or "")[:10],
                    "issue": str(r.get("issueDate") or "")[:10], "amount_b": amt_b, "reopen": r.get("reopening") == "Yes"})
    return sorted(out, key=lambda x: (x["issue"], x["term"] or ""))


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def refresh(force: bool = False, now: float = 0) -> Dict:
    d = load()
    now = now or time.time()
    if not force and now - float(d.get("ts_try") or 0) < TTL:
        return d
    d["ts_try"] = now
    try:
        rows = parse(await http.get(URL, kind="json", headers=HDR, timeout=30, retries=1))
        d.update(items=rows, ts=now)
        HEALTH.ok("ust_auctions", len(rows))
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("ust_auctions", str(e) or type(e).__name__, every=TTL)
        log.info("Treasury auctions: %s", e)
    FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d
