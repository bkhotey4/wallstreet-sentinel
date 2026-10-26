"""Cross-border bond flows for the 全球債市 page.

* Japan MOF weekly "International Transactions in Securities" (designated major investors, 100 million yen):
  residents' net purchases of FOREIGN long-term bonds (Japanese money going out / coming home) and non-residents' net
  purchases of JAPANESE long-term bonds.  2005 onward, published every Thursday.
* US Treasury TIC "Major Foreign Holders of Treasury Securities" (slt_table5, billions of dollars, monthly, ~6 weeks
  late): the file holds the latest 13 months, so every fetch is merged into an archive that grows month by month.
Cached in data_cache/econ_bondflows.json (kept between site builds)."""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import time
from typing import Dict, List, Optional

import numpy as np

from ..config import DATA_DIR
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_bondflows.json"
TTL = 12 * 3600
MOF = "https://www.mof.go.jp/policy/international_policy/reference/itn_transactions_in_securities/week.csv"
TIC = "https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.txt"
# OFR Money Market Fund Monitor (from the funds' SEC N-MFP filings, monthly, 2010 onward, US$): total assets and the
# part held in US Treasuries — the cash parked on the side (free JSON API)
OFR = "https://data.financialresearch.gov/v1/series/timeseries?mnemonic={}"
MMF_IDS = {"tot": "MMF-MMF_TOT-M", "tsy": "MMF-MMF_T_TOT-M"}
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
ZH = {"Japan": "日本", "United Kingdom": "英國", "China, Mainland": "中國", "Belgium": "比利時", "Luxembourg": "盧森堡",
      "Cayman Islands": "開曼群島", "Canada": "加拿大", "Switzerland": "瑞士", "Taiwan": "台灣", "Ireland": "愛爾蘭",
      "France": "法國", "Hong Kong": "香港", "India": "印度", "Singapore": "新加坡", "Brazil": "巴西", "Norway": "挪威",
      "Saudi Arabia": "沙烏地阿拉伯", "Korea, South": "韓國", "Germany": "德國", "Israel": "以色列", "All Other": "其他",
      "Grand Total": "全部外國", "Of which: Foreign Official": "其中：外國官方"}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)


def _num(x: str) -> Optional[float]:
    try:
        return float(str(x).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def parse_mof(text: str) -> List[List]:
    """[[week label, week start ISO, foreign long-term bonds net (residents), Japanese long-term bonds net (non-residents)]]"""
    out = []
    for r in csv.reader(io.StringIO(text)):
        if not r or not re.match(r"\d{4}．", r[0] or ""):
            continue
        m = re.match(r"(\d{4})．\s*(\d+)．\s*(\d+)", r[0])
        if not m or len(r) < 18:
            continue
        # columns: residents' equity 1-3, long-term debt 4-6 (net = 6) …; non-residents' equity 12-14, long-term debt 15-17 (net = 17)
        out.append([r[0].strip(), f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", _num(r[6]), _num(r[17])])
    return out


def parse_tic(text: str) -> Dict[str, Dict[str, float]]:
    """{country: {YYYY-MM: billions}} from the tab-separated slt_table5."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    head = next((ln.split("\t") for ln in lines if ln.startswith("Country")), None)
    if not head:
        return {}
    months = [h.strip() for h in head[1:] if re.fullmatch(r"\d{4}-\d{2}", h.strip())]
    out: Dict[str, Dict[str, float]] = {}
    for ln in lines:
        p = ln.split("\t")
        name = p[0].strip()
        if not name or name == "Country" or len(p) < len(months) + 1:
            continue
        vals = {m: _num(v) for m, v in zip(months, p[1:])}
        vals = {k: v for k, v in vals.items() if v is not None}
        if vals:
            out[name] = vals
    return out


async def refresh(force: bool = False) -> Dict:
    d = load()
    if not force and time.time() - float(d.get("ts", 0)) < TTL and d.get("mof") and d.get("tic") and d.get("mmf"):
        return d
    try:
        raw = await http.get(MOF, kind="bytes", headers=UA, timeout=60, retries=1)
        rows = parse_mof(raw.decode("shift_jis", errors="replace"))
        if len(rows) > 100:
            d["mof"] = rows
    except Exception as e:  # noqa: BLE001
        log.info("MOF weekly flows failed: %s", e)
    try:
        tic = parse_tic(await http.get(TIC, kind="text", headers=UA, timeout=60, retries=1))
        if tic:
            arc = d.get("tic") or {}
            for c, vals in tic.items():
                arc.setdefault(c, {}).update(vals)
            d["tic"] = arc
    except Exception as e:  # noqa: BLE001
        log.info("TIC holders failed: %s", e)
    try:
        mm = {}
        for k, mn in MMF_IDS.items():
            rows = await http.get(OFR.format(mn), headers=UA, timeout=60, retries=1)
            mm[k] = [[str(a)[:7], float(b)] for a, b in rows or [] if b is not None]
        if len(mm.get("tot") or []) > 24:
            d["mmf"] = mm
    except Exception as e:  # noqa: BLE001
        log.info("OFR money market funds failed: %s", e)
    d["ts"] = time.time()
    _save(d)
    return d


def mof_view(d: Dict) -> Optional[Dict]:
    rows = [r for r in d.get("mof") or [] if r[2] is not None]
    if len(rows) < 60:
        return None
    v = np.array([r[2] for r in rows]) / 1e4                                   # 100 million yen → trillion yen
    s5 = np.convolve(v, np.ones(5), "valid")
    run = 0
    for x in v[::-1]:
        if x < 0:
            run += 1
        else:
            break
    if run == 0:
        for x in v[::-1]:
            if x > 0:
                run -= 1
            else:
                break
    jp = [r[3] for r in rows if r[3] is not None]
    return {"week": rows[-1][0], "start": rows[-1][1], "since": rows[0][1][:4], "last": float(v[-1]), "sum5": float(s5[-1]),
            "pct5": float((s5[:-1] < s5[-1]).mean() * 100), "sum13": float(v[-13:].sum()), "sum52": float(v[-52:].sum()),
            "run": run, "weeks": [[r[0], round(r[2] / 1e4, 2)] for r in rows[-8:]],
            "jgb_in13": float(np.sum(jp[-13:]) / 1e4) if len(jp) >= 13 else None}


def mmf_view(d: Dict) -> Optional[Dict]:
    """Money-market fund assets: level, 1- and 3-month change, where the 3-month change ranks since 2010, Treasury share."""
    m = d.get("mmf") or {}
    tot = [r for r in m.get("tot") or [] if r[1]]
    if len(tot) < 36:
        return None
    v = np.array([r[1] for r in tot])
    c3 = v[3:] / v[:-3] - 1
    tsy = dict((r[0], r[1]) for r in m.get("tsy") or [])
    last = tot[-1][0]
    return {"month": last, "since": tot[0][0][:4], "now": float(v[-1]) / 1e12, "chg1": float(v[-1] / v[-2] - 1) * 100,
            "chg3": float(c3[-1]) * 100, "pct3": float((c3[:-1] < c3[-1]).mean() * 100), "chg12": float(v[-1] / v[-13] - 1) * 100,
            "tsy_share": float(tsy[last] / v[-1] * 100) if tsy.get(last) else None, "high": bool(v[-1] >= v.max())}


def tic_view(d: Dict, top: int = 8) -> Optional[Dict]:
    t = d.get("tic") or {}
    tot = t.get("Grand Total") or {}
    if not tot:
        return None
    months = sorted(tot)
    last = months[-1]

    def chg(series: Dict[str, float], k: int) -> Optional[float]:
        ms = sorted(series)
        if len(ms) <= k or ms[-1] != last:
            return None
        a, b = series[ms[-1 - k]], series[ms[-1]]
        return (b / a - 1) * 100 if a else None

    rows = []
    for c, s in t.items():
        if c in ("Grand Total", "All Other") or last not in s:
            continue
        rows.append({"name": c, "zh": ZH.get(c, c), "now": s[last], "chg6": chg(s, 6), "chg12": chg(s, 12), "official": c.lower().startswith("of which")})
    main = sorted([r for r in rows if not r["official"]], key=lambda r: -r["now"])[:top]
    off = next((r for r in rows if r["name"].lower() == "of which: foreign official"), None)
    if off:
        off["zh"] = "外國官方（各國央行等）"
    return {"month": last, "months": len(months), "total": tot[last], "total_chg6": chg(tot, 6), "total_chg12": chg(tot, 12),
            "rows": main, "official": off}
