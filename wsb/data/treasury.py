"""US Treasury zone: yield curve (FRED constant-maturity series), term premium (Kim-Wright), MOVE, and coupon
auction results from TreasuryDirect (free, no key).

Auction demand is judged against the same tenor's own recent auctions (no fixed thresholds):
    bid-to-cover well below its recent average, or primary dealers left holding a larger share than usual
    (= end investors stepped back) → weak.  The classic "tail" needs when-issued quotes, which are not public, so it
    is not shown."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
URL = "https://www.treasurydirect.gov/TA_WS/securities/auctioned"
_FILE = DATA_DIR / "treasury_auctions.json"
TENORS = [("DGS1MO", 1 / 12), ("DGS3MO", 0.25), ("DGS6MO", 0.5), ("DGS1", 1), ("DGS2", 2), ("DGS3", 3), ("DGS5", 5),
          ("DGS7", 7), ("DGS10", 10), ("DGS20", 20), ("DGS30", 30)]


def _cfg() -> Dict:
    return SETTINGS.get("treasury", {}) or {}


def _n(x) -> Optional[float]:
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def parse_auctions(rows: List[Dict]) -> List[Dict]:
    out = []
    for x in rows or []:
        if str(x.get("tips", "No")).lower() == "yes" or str(x.get("floatingRate", "No")).lower() == "yes":
            continue
        comp = _n(x.get("competitiveAccepted"))
        btc, hy = _n(x.get("bidToCoverRatio")), _n(x.get("highYield"))
        if not comp or btc is None or hy is None:          # announced but not yet auctioned
            continue
        share = lambda k: (_n(x.get(k)) or 0) / comp * 100  # noqa: E731
        out.append({"date": str(x.get("auctionDate", ""))[:10], "term": x.get("originalSecurityTerm") or x.get("securityTerm"),
                    "label": x.get("securityTerm"), "reopen": str(x.get("reopening", "No")).lower() == "yes",
                    "high_yield": hy, "btc": btc, "dealer": share("primaryDealerAccepted"),
                    "indirect": share("indirectBidderAccepted"), "direct": share("directBidderAccepted"),
                    "size_bn": (_n(x.get("offeringAmount")) or 0) / 1e9, "cusip": x.get("cusip")})
    return sorted({(a["date"], a["cusip"]): a for a in out}.values(), key=lambda a: a["date"], reverse=True)


def judge(auctions: List[Dict], window: int = 6) -> List[Dict]:
    """Compare each auction with the previous `window` auctions of the same original term."""
    c = _cfg()
    drop, pp = float(c.get("weak_btc_drop", 0.15)), float(c.get("weak_dealer_pp", 5))
    by: Dict[str, List[Dict]] = {}
    out: List[Dict] = []
    for a in sorted(auctions, key=lambda a: a["date"]):
        prev = by.setdefault(a["term"], [])[-window:]
        r = dict(a, n_prev=len(prev), verdict=None)
        if len(prev) >= 3:
            r["btc_avg"] = float(np.mean([p["btc"] for p in prev]))
            r["dealer_avg"] = float(np.mean([p["dealer"] for p in prev]))
            r["indirect_avg"] = float(np.mean([p["indirect"] for p in prev]))
            weak = (r["btc"] <= r["btc_avg"] - drop) + (r["dealer"] >= r["dealer_avg"] + pp)
            strong = (r["btc"] >= r["btc_avg"] + drop) + (r["dealer"] <= r["dealer_avg"] - pp)
            r["verdict"] = "偏弱" if weak and not strong else "偏強" if strong and not weak else "正常"
        by[a["term"]].append(a)
        out.append(r)
    return sorted(out, key=lambda a: a["date"], reverse=True)


class Treasury:
    def __init__(self) -> None:
        self.auctions: List[Dict] = []
        self.ts = 0.0
        try:
            if _FILE.exists():
                d = json.loads(_FILE.read_text(encoding="utf-8"))
                self.auctions, self.ts = d.get("auctions", []), float(d.get("ts", 0))
        except Exception as e:  # noqa: BLE001
            log.warning("auction cache unreadable: %s", e)

    async def refresh(self, force: bool = False) -> None:
        if not _cfg().get("enabled", True):
            return
        every = float(_cfg().get("refresh_hours", 6)) * 3600
        if not force and self.auctions and time.time() - self.ts < every:
            return
        rows: List[Dict] = []
        try:
            for typ in ("Note", "Bond"):
                js = await http.get(URL, params={"format": "json", "type": typ, "pagesize": 120}, timeout=30, retries=1)
                rows += js if isinstance(js, list) else []
            terms = set(_cfg().get("auction_terms") or [])
            parsed = [a for a in parse_auctions(rows) if not terms or a["term"] in terms]
            if not parsed:
                raise RuntimeError("no auctions parsed")
            self.auctions, self.ts = judge(parsed), time.time()
            tmp = _FILE.with_suffix(_FILE.suffix + ".tmp")          # atomic: a cancelled run can't truncate it
            tmp.write_text(json.dumps({"ts": self.ts, "auctions": self.auctions}, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, _FILE)
            HEALTH.ok("treasury_auctions", len(parsed), every=every)
        except Exception as e:  # noqa: BLE001
            log.warning("TreasuryDirect failed: %s", e)
            HEALTH.fail("treasury_auctions", e, every=every)


def curve(fred, when: Optional[pd.Timestamp] = None) -> List[Dict]:
    """[{tenor_years, sid, yield}] at the latest date (or the last value on/before `when`)."""
    out = []
    for sid, yrs in TENORS:
        s = fred.get(sid).dropna()
        if not isinstance(s.index, pd.DatetimeIndex):
            continue
        if when is not None:
            s = s[s.index <= when]
        if len(s):
            out.append({"sid": sid, "years": yrs, "yield": float(s.iloc[-1]), "date": s.index[-1].strftime("%Y-%m-%d")})
    return out


def build(eng) -> Dict:
    fred = eng.fred
    now = curve(fred)
    if len(now) < 5 and not getattr(eng, "treasury", None):
        return {"available": False}
    last = max((pd.Timestamp(c["date"]) for c in now), default=None)
    curves = {"now": now}
    if last is not None:
        for k, off in (("m1", pd.DateOffset(months=1)), ("y1", pd.DateOffset(years=1))):
            curves[k] = curve(fred, last - off)
    get = lambda sid: fred.get(sid).dropna()  # noqa: E731
    s10, s2, s3m = get("DGS10"), get("DGS2"), get("DGS3MO")
    spreads = {}
    for k, a, b in (("10y2y", s10, s2), ("10y3m", s10, s3m)):
        j = pd.concat([a, b], axis=1, join="inner").dropna()
        if len(j):
            sp = (j.iloc[:, 0] - j.iloc[:, 1]) * 100
            inv = sp < 0
            run = 0
            for v in inv.iloc[::-1]:
                if not v:
                    break
                run += 1
            spreads[k] = {"bp": float(sp.iloc[-1]), "hist": sp, "inverted_days": run,
                          "last_inverted": sp[inv].index[-1].strftime("%Y-%m-%d") if inv.any() else None}
    tp = get("THREEFYTP10")
    move = eng.market.series("^MOVE") if getattr(eng, "market", None) is not None else pd.Series(dtype=float)
    tr = getattr(eng, "treasury", None)
    auctions = tr.auctions if tr is not None else []
    return {"available": bool(now) or bool(auctions), "curves": curves, "spreads": spreads,
            "term_premium": {"value": float(tp.iloc[-1]), "date": tp.index[-1].strftime("%Y-%m-%d"), "hist": tp,
                             "pctile": float((tp < tp.iloc[-1]).mean() * 100)} if len(tp) > 20 else None,
            "move": {"value": float(move.iloc[-1]), "hist": move, "pctile": float((move.tail(2520) < move.iloc[-1]).mean() * 100)}
            if len(move) > 20 else None,
            "auctions": auctions[:14], "weak": [a for a in auctions[:8] if a.get("verdict") == "偏弱"]}


def summary_lines(t: Dict) -> List[str]:
    if not t or not t.get("available"):
        return []
    L = []
    c = {x["sid"]: x["yield"] for x in t["curves"].get("now", [])}
    if c:
        lab = {"DGS3MO": "3個月", "DGS2": "2年", "DGS10": "10年", "DGS30": "30年"}
        L.append("殖利率曲線：" + "、".join(f"{lab[k]} {v:.2f}%" for k, v in c.items() if k in lab))
    for k, lab in (("10y2y", "10年-2年"), ("10y3m", "10年-3月")):
        sp = t["spreads"].get(k)
        if sp:
            L.append(f"{lab} 利差 {sp['bp']:+.0f}bp" + (f"（已倒掛 {sp['inverted_days']} 個交易日）" if sp["inverted_days"] else ""))
    if t.get("term_premium"):
        L.append(f"10 年期限溢價 {t['term_premium']['value']:.2f}%（歷史百分位 {t['term_premium']['pctile']:.0f}）")
    for a in t.get("auctions", [])[:4]:
        if a.get("verdict"):
            L.append(f"{a['date']} {a['label']} 標售：得標 {a['high_yield']:.3f}%、倍數 {a['btc']:.2f}（近期均 {a['btc_avg']:.2f}）、"
                     f"交易商承接 {a['dealer']:.0f}%（均 {a['dealer_avg']:.0f}%）→ {a['verdict']}")
    return L
