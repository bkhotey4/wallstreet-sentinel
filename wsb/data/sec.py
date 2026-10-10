"""SEC EDGAR watcher for portfolio holdings: 8-K material events,
Form 4 insider trades, 13D/G activist stakes, S-1/424B dilution."""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Dict, List

from ..config import SEC_USER_AGENT, SETTINGS
from ..health import HEALTH
from .. import store
from . import http

log = logging.getLogger(__name__)
WATCH_FORMS = {"8-K": "重大事件", "4": "內部人交易", "SC 13D": "主動投資人持股", "SC 13G": "大股東持股", "SCHEDULE 13D": "主動投資人持股", "SCHEDULE 13G": "大股東持股",
               "S-1": "增資/上市", "S-3": "儲架增資", "424B5": "增資發行", "10-Q": "季報", "10-K": "年報",
               "6-K": "外國發行人公告", "NT 10-Q": "延遲申報(警訊)", "NT 10-K": "延遲申報(警訊)"}


class SecWatcher:
    def __init__(self) -> None:
        self.cik: Dict[str, str] = {}
        self.recent: List[dict] = []
        self.last_fresh: List[dict] = []
        self.ts = 0.0

    async def _load_map(self) -> None:
        if self.cik:
            return
        js = await http.get("https://www.sec.gov/files/company_tickers.json",
                            headers={"User-Agent": SEC_USER_AGENT})
        self.cik = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in js.values()}

    async def fetch(self, ticker: str) -> List[dict]:
        """Read-only: a ticker's recent watched filings (does not mark them seen or touch self.recent)."""
        await self._load_map()
        cik = self.cik.get(ticker.upper().replace(".", "-"))
        if not cik:
            return []
        js = await http.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers={"User-Agent": SEC_USER_AGENT})
        return self._parse(ticker, cik, js)

    def _parse(self, t: str, cik: str, js: dict) -> List[dict]:
        r = js.get("filings", {}).get("recent", {})
        n = len(r.get("form", []))
        col = lambda k: (r.get(k) or [""] * n)  # noqa: E731
        out = []
        for form, dt, acc, desc, items, doc in list(zip(
                col("form"), col("filingDate"), col("accessionNumber"),
                col("primaryDocDescription"), col("items"), col("primaryDocument")))[:25]:
            if form not in WATCH_FORMS:
                continue
            earnings = (form == "8-K" and "2.02" in (items or "")) or \
                       (form == "6-K" and any(k in (desc or "").lower() for k in ("result", "earning", "quarter")))
            out.append({"ticker": t, "form": form, "label": "財報公布" if earnings else WATCH_FORMS[form],
                        "date": dt, "desc": desc, "items": items, "earnings": earnings,
                        "cik": int(cik), "acc": acc, "doc": doc,
                        "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/"})
        return out

    async def refresh(self, tickers: List[str]) -> List[dict]:
        """Returns newly-seen filings."""
        every = SETTINGS["refresh"]["sec"]
        fresh: List[dict] = []
        try:
            await self._load_map()
            recent = []
            ok = 0
            failed: List[str] = []
            for t in tickers:
                cik = self.cik.get(t.upper().replace(".", "-"))
                if not cik:
                    continue
                try:                     # one ticker's error must not abort the whole round
                    js = await http.get(f"https://data.sec.gov/submissions/CIK{cik}.json",
                                        headers={"User-Agent": SEC_USER_AGENT})
                    items = self._parse(t, cik, js)
                    ok += 1
                except Exception as e:  # noqa: BLE001
                    failed.append(t)
                    log.info("SEC %s failed: %s", t, e)
                    recent.extend(x for x in self.recent if x.get("ticker") == t)     # keep its last known filings
                    await asyncio.sleep(0.12)
                    continue
                for item in items:
                    recent.append(item)
                    if store.seen_check_and_mark(f"sec:{item['acc']}"):
                        fresh.append(item)
                await asyncio.sleep(0.12)  # SEC fair-access: <10 req/s
            recent.sort(key=lambda x: x["date"], reverse=True)
            self.recent = recent[:60]
            self.last_fresh = fresh
            if failed:
                log.warning("SEC: %d ticker(s) failed this round: %s", len(failed), ", ".join(failed[:10]))
            if failed and not ok:
                raise RuntimeError(f"all {len(failed)} SEC lookups failed")
            self.ts = time.time()
            HEALTH.ok("sec_edgar", len(recent), every=every)
        except Exception as e:  # noqa: BLE001
            log.warning("SEC failed: %s", e)
            HEALTH.fail("sec_edgar", e, every=every)
        return fresh


def _html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        txt = BeautifulSoup(html, "html.parser").get_text(" ")
    except Exception:  # noqa: BLE001
        txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"&nbsp;|&#160;", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


async def fetch_press_release(item: dict, max_chars: int = 18000) -> str:
    """Earnings press release text: prefer Exhibit 99.x, else the primary document."""
    base = item["url"]
    hdr = {"User-Agent": SEC_USER_AGENT}
    idx = await http.get(base + "index.json", headers=hdr)
    names = [f["name"] for f in idx.get("directory", {}).get("item", [])]
    ex = [n for n in names if re.search(r"ex-?99|exhibit99|ex99", n, re.I) and n.lower().endswith((".htm", ".html", ".txt"))]
    target = sorted(ex)[0] if ex else item.get("doc")
    if not target:
        return ""
    html = await http.get(base + target, headers=hdr, kind="text")
    return _html_to_text(html)[:max_chars]
