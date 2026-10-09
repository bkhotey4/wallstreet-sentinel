"""What the famous money is doing, from SEC EDGAR (free, public):

* Gurus    — 13F-HR quarterly holdings of tracked managers (Buffett, Burry, Ackman, Druckenmiller …): top positions,
             new / exited / added / trimmed versus the previous quarter, put & call positions shown separately.
             13F is filed up to 45 days after quarter end, long US positions only — a lagging, partial picture.
* Insiders — Form 4 open-market purchases (code P) and sales (code S) by officers/directors of the US names in the
             stock-scoring universe.  Sales under a pre-arranged Rule 10b5-1 plan are separated from discretionary ones.

Archives (data_cache/gurus.json, insiders.json) mean each filing is downloaded once."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR, SEC_USER_AGENT, SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
HDR = {"User-Agent": SEC_USER_AGENT, "Accept": "application/json, text/xml, */*"}
_GURU_FILE = DATA_DIR / "gurus.json"
_INS_FILE = DATA_DIR / "insiders.json"
_MAP_FILE = DATA_DIR / "sec_tickers.json"
_STOP = {"INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "LTD", "PLC", "LLC", "LP", "THE", "OF", "AND",
         "HLDGS", "HOLDINGS", "HOLDING", "GROUP", "NEW", "DEL", "DE", "CL", "CLASS", "COM", "A", "B", "C", "SHS", "ADR",
         "SPONSORED", "N", "V", "NV", "SA", "AG", "SE", "ORD", "&"}


def _cfg(k: str) -> Dict:
    return SETTINGS.get(k, {}) or {}


_ABBR = {"AMER": "AMERICA", "INTL": "INTERNATIONAL", "MFG": "MANUFACTURING", "FINL": "FINANCIAL", "SVCS": "SERVICES",
         "TECHNOLOGIES": "TECH", "TECHNOLOGY": "TECH", "SYS": "SYSTEMS", "MATLS": "MATERIALS", "PPTYS": "PROPERTIES",
         "COMMUNICATIONS": "COMM", "COMMUNICATION": "COMM", "PHARMACEUTICALS": "PHARMA"}


def norm_name(s: str) -> str:
    """'BANK OF AMER CORP' / 'Bank of America Corp /DE/' → 'BANK AMERICA' (first two meaningful words)."""
    toks = [_ABBR.get(t, t) for t in re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper().replace("&", " ")).split()]
    toks = [t for t in toks if t not in _STOP]
    return " ".join(toks[:2])


def _strip_ns(root: ET.Element) -> ET.Element:
    for el in root.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def _f(el: Optional[ET.Element], path: str) -> Optional[str]:
    x = el.find(path) if el is not None else None
    return x.text.strip() if x is not None and x.text else None


def _num(s) -> Optional[float]:
    try:
        return float(str(s).replace(",", ""))
    except (TypeError, ValueError):
        return None


async def _get(url: str, kind: str = "json"):
    r = await http.get(url, kind=kind, headers=HDR, timeout=30, retries=1)
    await asyncio.sleep(0.15)                       # SEC fair access: stay well under 10 requests / second
    return r


def us_universe() -> Dict[str, Tuple[str, str]]:
    m = ((_cfg("stockscore").get("markets") or {}).get("us") or {}).get("symbols") or {}
    return {str(k): (v[0], v[1]) if isinstance(v, (list, tuple)) else (str(v), str(v)) for k, v in m.items()}


async def ticker_map() -> Dict[str, Dict]:
    """SEC ticker → {cik, title}; cached for a week."""
    try:
        if _MAP_FILE.exists() and time.time() - _MAP_FILE.stat().st_mtime < 7 * 86400:
            return json.loads(_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    js = await _get("https://www.sec.gov/files/company_tickers.json")
    out = {v["ticker"].upper(): {"cik": int(v["cik_str"]), "title": v["title"]} for v in js.values()}
    try:
        _MAP_FILE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log.warning("SEC ticker map not cached: %s", e)
    return out


# ============================================================ 13F
def parse_infotable(xml: str, dollars: Optional[bool] = None) -> List[Dict]:
    """Aggregate an information table by (CUSIP, put/call). Values in USD.
    Since 2023 the <value> field is meant to be whole dollars, but some filers still report thousands — when `dollars`
    is not given it is detected from the implied price per share (median < $2 → the table is in thousands)."""
    root = _strip_ns(ET.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml))
    agg: Dict[Tuple[str, str], Dict] = {}
    for it in root.iter("infoTable"):
        cusip = (_f(it, "cusip") or "").upper()
        pc = (_f(it, "putCall") or "").capitalize()
        val = _num(_f(it, "value")) or 0.0
        sh = _num(_f(it, "shrsOrPrnAmt/sshPrnamt")) or 0.0
        k = (cusip, pc)
        a = agg.setdefault(k, {"name": _f(it, "nameOfIssuer") or cusip, "cls": _f(it, "titleOfClass") or "", "cusip": cusip,
                               "pc": pc, "value": 0.0, "shares": 0.0})
        a["value"] += val
        a["shares"] += sh
    rows = list(agg.values())
    if dollars is None:
        px = sorted(r["value"] / r["shares"] for r in rows if not r["pc"] and r["shares"] > 0 and r["value"] > 0)
        dollars = not px or px[len(px) // 2] >= 2.0
    if not dollars:
        for r in rows:
            r["value"] *= 1000
    return sorted(rows, key=lambda x: -x["value"])


def compare(cur: List[Dict], prev: Optional[List[Dict]]) -> Dict[str, List[Dict]]:
    """New / exited / added (>+10% shares) / trimmed (<−10%) positions versus the previous filing."""
    out = {"new": [], "exit": [], "add": [], "cut": []}
    if prev is None:
        return out
    p = {(x["cusip"], x["pc"]): x for x in prev}
    c = {(x["cusip"], x["pc"]): x for x in cur}
    for k, x in c.items():
        if k not in p:
            out["new"].append(x)
        elif p[k]["shares"] > 0:
            ch = x["shares"] / p[k]["shares"] - 1
            if ch >= 0.10:
                out["add"].append({**x, "chg": ch * 100})
            elif ch <= -0.10:
                out["cut"].append({**x, "chg": ch * 100})
    for k, x in p.items():
        if k not in c:
            out["exit"].append(x)
    for v in out.values():
        v.sort(key=lambda x: -x["value"])
    return out


class Gurus:
    def __init__(self) -> None:
        self.data: Dict = {"ts": 0, "managers": {}}
        self.result: Dict = {}
        try:
            if _GURU_FILE.exists():
                self.data = json.loads(_GURU_FILE.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            log.warning("13F archive unreadable: %s", e)
        self._names: Dict[str, str] = {}
        self._build()

    async def refresh(self, force: bool = False) -> None:
        c = _cfg("gurus")
        if not c.get("enabled", True):
            return
        every = float(c.get("refresh_hours", 24)) * 3600
        if not force and time.time() - float(self.data.get("ts", 0)) < every and self.data.get("managers"):
            self._build()
            return
        ok = fail = 0
        for m in c.get("managers", []):
            cik = int(m["cik"])
            rec = self.data["managers"].setdefault(str(cik), {"filings": []})
            try:
                sub = await _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
                r = sub.get("filings", {}).get("recent", {})
                rows = [(a, d, p) for a, fm, d, p in zip(r.get("accessionNumber", []), r.get("form", []),
                                                           r.get("filingDate", []), r.get("reportDate", [])) if fm == "13F-HR"][:2]
                have = {f["acc"]: f for f in rec["filings"]}
                filings = []
                for acc, filed, period in rows:
                    if acc in have and have[acc].get("holdings") is not None:
                        filings.append(have[acc])
                        continue
                    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/"
                    idx = await _get(base + "index.json")
                    names = [i["name"] for i in idx.get("directory", {}).get("item", [])]
                    xmls = [n for n in names if n.lower().endswith(".xml") and n.lower() != "primary_doc.xml"]
                    if not xmls:
                        continue
                    xml = await _get(base + xmls[0], kind="text")
                    filings.append({"acc": acc, "filed": filed, "period": period, "url": base,
                                    "holdings": parse_infotable(xml, dollars=None if filed >= "2023-01-03" else False)})
                rec.update({"name": sub.get("name"), "filings": filings, "checked": time.time()})
                ok += 1
            except Exception as e:  # noqa: BLE001
                fail += 1
                log.warning("13F %s failed: %s", cik, e)
        if ok:
            self.data["ts"] = time.time()
            try:
                _GURU_FILE.write_text(json.dumps(self.data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                log.warning("13F archive not saved: %s", e)
            HEALTH.ok("sec_13f", ok, every=every)
        else:
            HEALTH.fail("sec_13f", f"{fail} managers failed", every=every)
        self._build()

    def _build(self) -> None:
        c = _cfg("gurus")
        stale = int(c.get("stale_days", 200))
        out = []
        for m in c.get("managers", []):
            rec = self.data.get("managers", {}).get(str(int(m["cik"])))
            if not rec or not rec.get("filings"):
                continue
            cur = rec["filings"][0]
            prev = rec["filings"][1]["holdings"] if len(rec["filings"]) > 1 else None
            hold = cur["holdings"]
            total = sum(h["value"] for h in hold if not h["pc"]) or 0.0
            age = (date.today() - date.fromisoformat(cur["filed"])).days
            out.append({"cik": int(m["cik"]), "name": m["name"], "name_en": m.get("name_en", m["name"]), "style": m.get("style", ""),
                        "filed": cur["filed"], "period": cur["period"], "url": cur.get("url"), "stale": age > stale, "age_days": age,
                        "total": total, "n": len([h for h in hold if not h["pc"]]),
                        "top": [{**h, "w": h["value"] / total * 100 if total and not h["pc"] else None} for h in hold[:12]],
                        "options": [h for h in hold if h["pc"]][:8], "chg": compare(hold, prev)})
        self.result = {"available": bool(out), "managers": out}

    def set_names(self, names: Dict[str, str]) -> None:
        """ticker → normalised SEC company title, for matching 13F issuer names to the scoring universe."""
        self._names = names

    def ticker(self, sym: str) -> Optional[Dict]:
        """How many tracked (non-stale) managers added / cut this name in their latest 13F."""
        key = self._names.get(sym)
        if not key or not self.result.get("available"):
            return None
        add = cut = held = 0
        for m in self.result["managers"]:
            if m["stale"]:
                continue
            ch = m["chg"]
            hit = lambda xs: any(norm_name(x["name"]) == key and not x["pc"] for x in xs)  # noqa: E731
            if hit(ch["new"]) or hit(ch["add"]):
                add += 1
            elif hit(ch["exit"]) or hit(ch["cut"]):
                cut += 1
            if any(norm_name(h["name"]) == key and not h["pc"] for h in m["top"]):
                held += 1
        return {"add": add, "cut": cut, "held_top": held}


# ============================================================ Form 4
def parse_form4(xml: str) -> Dict:
    root = _strip_ns(ET.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml))
    owner = root.find("reportingOwner")
    rel = owner.find("reportingOwnerRelationship") if owner is not None else None
    title = _f(rel, "officerTitle") or ("Director" if (_f(rel, "isDirector") or "").lower() in ("1", "true") else
                                        "10% owner" if (_f(rel, "isTenPercentOwner") or "").lower() in ("1", "true") else "")
    plan = (_f(root, "aff10b5One") or "").lower() in ("1", "true")
    notes = " ".join((n.text or "") for n in root.iter("footnote"))
    if re.search(r"10b5-?1", notes, re.I):
        plan = True
    tx = []
    for t in root.iter("nonDerivativeTransaction"):
        code = _f(t, "transactionCoding/transactionCode")
        if code not in ("S", "P"):
            continue
        sh = _num(_f(t, "transactionAmounts/transactionShares/value")) or 0.0
        px = _num(_f(t, "transactionAmounts/transactionPricePerShare/value")) or 0.0
        tx.append({"code": code, "date": _f(t, "transactionDate/value"), "shares": sh, "price": px, "usd": sh * px})
    return {"owner": _f(owner, "reportingOwnerId/rptOwnerName") or "", "title": title, "plan": plan, "tx": tx,
            "sym": (_f(root, "issuer/issuerTradingSymbol") or "").upper(),
            "issuer": (_f(root, "issuer/issuerTradingSymbol") or "").upper()}


def same_issuer(sym: str, issuer: str) -> bool:
    """A company's EDGAR feed also lists Form 4s it files as an OWNER of other companies (e.g. Berkshire buying
    another stock) — those are not insider trades in its own shares."""
    a = re.sub(r"[^A-Z]", "", sym.upper().split("-")[0].split(".")[0])
    b = re.sub(r"[^A-Z]", "", (issuer or "").upper())
    return bool(a and b) and (a.startswith(b) or b.startswith(a))


class Insiders:
    def __init__(self) -> None:
        self.data: Dict = {"ts": 0, "forms": {}}
        self.summary: Dict[str, Dict] = {}
        try:
            if _INS_FILE.exists():
                self.data = json.loads(_INS_FILE.read_text(encoding="utf-8"))
                # archives written before the issuer check: re-download those filings once
                self.data["forms"] = {a: f for a, f in self.data.get("forms", {}).items() if "issuer" in f}
        except Exception as e:  # noqa: BLE001
            log.warning("insider archive unreadable: %s", e)
        self._build()

    async def refresh(self, force: bool = False, gurus: Optional[Gurus] = None) -> None:
        c = _cfg("insiders")
        if not c.get("enabled", True):
            return
        every = float(c.get("refresh_hours", 12)) * 3600
        uni = us_universe()
        backlog = int(self.data.get("pending", 0) or 0) > 0          # first fill takes several runs → don't wait 12 h between them
        if not force and not backlog and time.time() - float(self.data.get("ts", 0)) < every and self.data.get("forms"):
            self._build()
            if gurus is not None:
                await self._names(gurus, uni)
            return
        look = int(c.get("lookback_days", 90))
        cutoff = (date.today() - timedelta(days=look)).isoformat()
        cap = int(c.get("max_fetch_per_run", 150))
        try:
            tmap = await ticker_map()
        except Exception as e:  # noqa: BLE001
            HEALTH.fail("sec_form4", e, every=every)
            log.warning("SEC ticker map failed: %s", e)
            return
        if gurus is not None:
            gurus.set_names({s: norm_name((tmap.get(s) or tmap.get(s.replace("-", ".")) or {}).get("title", "")) for s in uni})
        todo: List[Tuple[str, int, str, str, str]] = []
        ok = fail = 0
        for sym in uni:
            info = tmap.get(sym) or tmap.get(sym.replace("-", ".")) or tmap.get(sym.replace("-", ""))
            if not info:
                continue
            cik = info["cik"]
            try:
                sub = await _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
                ok += 1
            except Exception as e:  # noqa: BLE001
                fail += 1
                log.info("submissions %s failed: %s", sym, e)
                continue
            r = sub.get("filings", {}).get("recent", {})
            for acc, fm, d, doc in zip(r.get("accessionNumber", []), r.get("form", []), r.get("filingDate", []),
                                       r.get("primaryDocument", [])):
                if d < cutoff:
                    break
                if fm == "4" and acc not in self.data["forms"]:
                    todo.append((sym, cik, acc, d, doc.split("/")[-1]))
        todo.sort(key=lambda x: x[3], reverse=True)
        got = 0
        for sym, cik, acc, d, doc in todo[:cap]:
            try:
                xml = await _get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}", kind="text")
                rec = parse_form4(xml)
                rec.update({"sym": sym, "filed": d, "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/"})
                self.data["forms"][acc] = rec
                got += 1
            except Exception as e:  # noqa: BLE001
                log.info("form4 %s %s failed: %s", sym, acc, e)
                self.data["forms"][acc] = {"sym": sym, "issuer": "", "filed": d, "tx": [], "error": True}
        self.data["forms"] = {a: f for a, f in self.data["forms"].items() if f.get("filed", "") >= cutoff}
        if ok:
            self.data["ts"] = time.time()
            self.data["pending"] = max(0, len(todo) - cap)
            try:
                _INS_FILE.write_text(json.dumps(self.data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                log.warning("insider archive not saved: %s", e)
            HEALTH.ok("sec_form4", got, every=every)
        else:
            HEALTH.fail("sec_form4", f"{fail} submissions failed", every=every)
        self._build()

    async def _names(self, gurus: Gurus, uni) -> None:
        try:
            tmap = await ticker_map()
            gurus.set_names({s: norm_name((tmap.get(s) or tmap.get(s.replace("-", ".")) or {}).get("title", "")) for s in uni})
        except Exception as e:  # noqa: BLE001
            log.info("SEC ticker map for 13F matching failed: %s", e)

    def _build(self) -> None:
        look = int(_cfg("insiders").get("lookback_days", 90))
        cutoff = (date.today() - timedelta(days=look)).isoformat()
        per: Dict[str, Dict] = {}
        for acc, f in self.data.get("forms", {}).items():
            if f.get("filed", "") < cutoff or not f.get("tx") or not same_issuer(f["sym"], f.get("issuer", "")):
                continue
            s = per.setdefault(f["sym"], {"buy_usd": 0.0, "sell_usd": 0.0, "sell_disc_usd": 0.0, "sell_plan_usd": 0.0,
                                          "sellers": set(), "buyers": set(), "big": [], "days": look})
            for t in f["tx"]:
                if t["code"] == "P":
                    s["buy_usd"] += t["usd"]
                    s["buyers"].add(f.get("owner", ""))
                else:
                    s["sell_usd"] += t["usd"]
                    s["sell_plan_usd" if f.get("plan") else "sell_disc_usd"] += t["usd"]
                    s["sellers"].add(f.get("owner", ""))
            usd = sum(t["usd"] for t in f["tx"])
            s["big"].append({"owner": f.get("owner", ""), "title": f.get("title", ""), "plan": f.get("plan", False),
                             "code": "P" if any(t["code"] == "P" for t in f["tx"]) else "S", "usd": usd, "date": f.get("filed"),
                             "url": f.get("url")})
        for s in per.values():
            s["n_sellers"], s["n_buyers"] = len(s.pop("sellers")), len(s.pop("buyers"))
            s["big"] = sorted(s["big"], key=lambda x: -x["usd"])[:3]
        self.summary = per

    def ticker(self, sym: str) -> Optional[Dict]:
        return self.summary.get(sym)

    def board(self, n: int = 15) -> Dict:
        big = float(_cfg("insiders").get("big_sale_usd", 25e6))
        rows = [{"sym": k, **v} for k, v in self.summary.items()]
        sells = sorted([r for r in rows if r["sell_usd"] > 0], key=lambda r: -r["sell_disc_usd"])[:n]
        buys = sorted([r for r in rows if r["buy_usd"] > 0], key=lambda r: -r["buy_usd"])[:n]
        return {"available": bool(self.data.get("forms")), "sells": sells, "buys": buys,
                "big": [r["sym"] for r in rows if r["sell_disc_usd"] >= big],
                "days": int(_cfg("insiders").get("lookback_days", 90)), "pending": self.data.get("pending", 0)}
