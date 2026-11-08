"""台灣家庭與銀行壓力：金管會銀行局開放資料（https://www.banking.gov.tw，免費 CSV）。

  * 中小企業放款平均逾放比（banking4，月資料，2008 年起）：中小企業撐不住，通常最先出現在這裡。
  * 放款資產品質（banking3，季資料，2013 年起）：「第一類正常放款」以外的比例（應予注意、可望收回、收回困難、收回無望）。
  * 各銀行逾放比與備抵呆帳覆蓋率（banking12，只有最新一個月）。
  * 各銀行以土地為擔保的放款占比（banking16，只有最新一個月）：台灣銀行最大的集中風險是不動產。
後兩項官方只給最新月份，這裡每個月存一份快照，歷史會越存越長。
信用卡逾期（banking14）官方檔案停在 2024 年 11 月，太舊所以不用。
燈號：中小企業逾放比或非正常放款比例落在自己歷史最高 10% → 黃燈。快取 data_cache/econ_tw_bank.json（CI 保留 econ_*），每天一次。
描述現況，不是預測。"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import time
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_tw_bank.json"
TTL = 24 * 3600
URL = "https://www.banking.gov.tw/webdowndoc?file=/stat/itopendata/banking{n}.csv"
PAGE = "https://www.banking.gov.tw/ch/home.jsp?id=157&parentpath=0,4"
HOT = 90.0
BIG = 100_000                         # 放款總額 1,000 億元以上（百萬元）才列進各銀行排行，避免小銀行一筆壞帳就排第一
UA = {"User-Agent": "Mozilla/5.0"}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _rows(raw: bytes) -> List[List[str]]:
    return list(csv.reader(io.StringIO(raw.decode("utf-8-sig", "replace"))))


def _f(x) -> Optional[float]:
    try:
        return float(str(x).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _roc(y, m) -> Optional[str]:
    try:
        return f"{int(y) + 1911:04d}-{int(m):02d}"
    except (TypeError, ValueError):
        return None


def _month(rows: List[List[str]]) -> Optional[str]:
    """'資料月份：115年08月' anywhere in the file → '2026-08'."""
    for r in rows:
        m = re.search(r"資料月份[:：]\s*(\d+)年(\d+)月", ",".join(r))
        if m:
            return _roc(m.group(1), m.group(2))
    return None


def parse_quality(raw: bytes) -> Dict[str, float]:
    """banking3: share of loans outside class 1 (normal), by quarter."""
    out = {}
    for r in _rows(raw)[1:]:
        d, c1 = _roc(*(r[:2] if len(r) >= 2 else (None, None))), _f(r[3]) if len(r) > 3 else None
        if d and c1 is not None:
            out[d] = round(100 - c1, 4)
    if len(out) < 20:
        raise ValueError(f"banking3: only {len(out)} quarters")
    return out


def parse_sme(raw: bytes) -> Dict[str, float]:
    """banking4: SME average NPL ratio by month."""
    out = {}
    for r in _rows(raw)[1:]:
        m = re.match(r"(\d+)年(\d+)月", r[0].strip()) if r else None
        v = _f(r[4]) if m and len(r) > 4 else None
        if m and v is not None:
            out[_roc(m.group(1), m.group(2))] = v
    if len(out) < 60:
        raise ValueError(f"banking4: only {len(out)} months")
    return out


def parse_npl(raw: bytes) -> Dict:
    """banking12: per-bank loans, overdue loans, NPL ratio and coverage for the latest month."""
    rows = _rows(raw)
    mon = _month(rows)
    banks = []
    for r in rows[1:]:
        if len(r) < 9 or not r[0].strip() or _f(r[3]) is None:
            continue
        banks.append({"name": r[0].strip(), "loans": _f(r[3]), "npl_amt": _f(r[4]) or 0.0, "equity": _f(r[6]),
                      "npl": _f(r[7]), "cover": _f(r[8]), "profit": _f(r[2])})
    if not mon or len(banks) < 20:
        raise ValueError("banking12: unexpected layout")
    return {"month": mon, "banks": banks}


def parse_land(raw: bytes) -> Dict:
    """banking16: per-bank loans secured by land, and total loans, for the latest month."""
    rows = _rows(raw)
    mon = _month(rows)
    banks = []
    for r in rows[1:]:
        if len(r) < 3 or _f(r[1]) is None or _f(r[2]) in (None, 0):
            continue
        banks.append({"name": r[0].strip(), "land": _f(r[1]), "loans": _f(r[2])})
    if not mon or len(banks) < 20:
        raise ValueError("banking16: unexpected layout")
    return {"month": mon, "banks": banks}


async def refresh(force: bool = False) -> Dict:
    from .freshness import bundle_ts, due
    d = load()
    now = time.time()
    d["ts_check"] = now
    keys = ["quality", "sme", "npl", "land"]
    each = d.setdefault("ts_each", {})
    todo = due(d, keys, TTL, now, force)
    if todo:
        bad = []
        for k, n, fn in (("quality", 3, parse_quality), ("sme", 4, parse_sme), ("npl", 12, parse_npl), ("land", 16, parse_land)):
            if k not in todo:
                continue
            d["try_each"][k] = now
            try:
                v = fn(await http.get(URL.format(n=n), kind="bytes", headers=UA, timeout=60, retries=1))
                if k in ("npl", "land"):                       # official file holds one month: keep a snapshot per month
                    snaps = d.setdefault(f"{k}_snaps", {})
                    snaps[v["month"]] = v
                    for old in sorted(snaps)[:-36]:
                        snaps.pop(old)
                d[k], each[k] = v, now
            except Exception as e:  # noqa: BLE001
                bad.append(f"{k}: {e if str(e) else type(e).__name__}")
        d["ts"] = bundle_ts(d, keys)
        if bad:
            log.warning("TW bank data: %s", "; ".join(bad))
            HEALTH.fail("tw_bank", "; ".join(bad), every=TTL)
        else:
            HEALTH.ok("tw_bank", len(d.get("sme") or {}), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def _ser(m: Dict) -> pd.Series:
    s = pd.Series(m or {}, dtype=float)
    if s.empty:
        return s
    s.index = pd.to_datetime(s.index)
    return s.sort_index().dropna()


def _pct(hist: pd.Series, v: float) -> Optional[float]:
    hist = hist.dropna()
    return float((hist < v).mean() * 100) if len(hist) >= 12 else None


def _trend(s: pd.Series, back: int) -> Dict:
    now = float(s.iloc[-1])
    return {"now": now, "date": s.index[-1].strftime("%Y-%m"), "since": s.index[0].strftime("%Y"), "pct": _pct(s.iloc[:-1], now),
            "ago": float(s.iloc[-1 - back]) if len(s) > back else None, "max": float(s.max()), "max_date": s.idxmax().strftime("%Y-%m"),
            "hist": [[i.strftime("%Y-%m-%d"), round(float(v), 3)] for i, v in s.tail(60).items()]}


def view(eng=None) -> Dict:
    d = load()
    out = {"ts": d.get("ts")}
    try:
        s = _ser(d.get("sme"))
        out["sme"] = _trend(s, 12) if len(s) >= 24 else None
        q = _ser(d.get("quality"))
        out["quality"] = _trend(q, 4) if len(q) >= 12 else None
        n = d.get("npl") or {}
        if n.get("banks"):
            bs = n["banks"]
            tl, ta = sum(b["loans"] for b in bs), sum(b["npl_amt"] for b in bs)
            big = [b for b in bs if b["loans"] >= BIG and b["npl"] is not None]
            out["npl"] = {"month": n["month"], "ratio": ta / tl * 100 if tl else None, "n": len(bs),
                          "top": sorted(big, key=lambda b: -b["npl"])[:5],
                          "low_cover": sorted([b for b in big if b["cover"] is not None], key=lambda b: b["cover"])[:3]}
        la = d.get("land") or {}
        if la.get("banks"):
            bs = la["banks"]
            tl, tland = sum(b["loans"] for b in bs), sum(b["land"] for b in bs)
            snaps = d.get("land_snaps") or {}
            hist = {m: sum(b["land"] for b in v["banks"]) / sum(b["loans"] for b in v["banks"]) * 100 for m, v in snaps.items()}
            yago = [hist[m] for m in sorted(hist) if m <= f"{int(la['month'][:4]) - 1}{la['month'][4:]}"]
            out["land"] = {"month": la["month"], "share": tland / tl * 100, "land": tland, "months": len(hist),
                           "share_1y": yago[-1] if yago else None,
                           "top": sorted([dict(b, share=b["land"] / b["loans"] * 100) for b in bs if b["loans"] >= BIG], key=lambda b: -b["share"])[:5]}
    except Exception:  # noqa: BLE001
        log.exception("TW bank view failed")
    hot = [zh for k, zh in (("sme", "中小企業逾放比"), ("quality", "非正常放款比例")) if ((out.get(k) or {}).get("pct") or 0) >= HOT]
    out["hot"] = hot
    out["emoji"] = "🟡" if hot else "🟢"
    return out


def alerts(v: Dict) -> List[tuple]:
    out = []
    for k, zh in (("sme", "中小企業逾放比"), ("quality", "非正常放款比例")):
        x = v.get(k) or {}
        if (x.get("pct") or 0) >= HOT:
            out.append((f"twbank:{k}:{x['date']}", "ℹ️ INFO", f"台灣銀行壓力：{zh}在自己歷史最高 10%（{x['now']:.2f}%）",
                        f"{x['since']} 年以來第 {x['pct']:.0f} 百分位。看網站「央行與資金」頁的台灣家庭與銀行壓力卡。"))
    return out
