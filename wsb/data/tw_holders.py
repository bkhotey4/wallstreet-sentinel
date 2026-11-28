"""集保戶股權分散表：每週大戶與散戶各持有多少（台灣集中保管結算所開放資料；2026-11-28）。

為什麼：使用者的假設是「台股 2027 下半年泡沫破裂」。泡沫頂部最常見的籌碼樣子是「大戶慢慢賣、散戶一直進」，
但本站只有融資、借券、法人買賣超，沒有「誰持有」的數據。集保每週五公布每檔股票各持股級距的人數與股數，
開放資料只給最新一週（https://opendata.tdcc.com.tw/getOD.ashx?id=1-5），所以本站自己每週存一份，
累積後算週變化。級距：1＝1～999 股（零股），2＝1～5 張，…，8＝30～50 張，15＝1,000 張以上（千張大戶），17＝合計。
雲端抓不到時用電腦端接力的 seed。"""
from __future__ import annotations

import csv
import io
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "tw_holders.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_holders_seed.json"
URL = "https://opendata.tdcc.com.tw/getOD.ashx?id=1-5"
TTL = 12 * 3600
KEEP_WEEKS = 60
HDR = {"User-Agent": "Mozilla/5.0 (WallStreetSentinel research bot)"}
SMALL = range(1, 9)          # 50 張以下＝散戶（級距 1～8）
BIG = 15                     # 1,000 張以上＝千張大戶


def parse(text: str, codes: Optional[set] = None) -> Dict[str, Dict]:
    """CSV → {date: {code: {"big_pct", "small_pct", "small_n", "holders"}}} for 4-digit common stocks (or `codes`)."""
    out: Dict[str, Dict] = {}
    for r in csv.reader(io.StringIO((text or "").lstrip("﻿"))):
        if len(r) < 6 or not r[0].isdigit():
            continue
        day, code, lvl = r[0], r[1].strip(), r[2].strip()
        if codes is not None and code not in codes:
            continue
        if codes is None and not (len(code) == 4 and code.isdigit()):
            continue
        try:
            lv, n, pct = int(lvl), int(r[3]), float(r[5])
        except ValueError:
            continue
        x = out.setdefault(day, {}).setdefault(code, {"big_pct": 0.0, "small_pct": 0.0, "small_n": 0, "holders": 0})
        if lv == BIG:
            x["big_pct"] = pct
        elif lv in SMALL:
            x["small_pct"] = round(x["small_pct"] + pct, 2)
            x["small_n"] += n
        elif lv == 17:
            x["holders"] = n
    return out


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def merge(d: Dict, snap: Dict[str, Dict]) -> Dict:
    """Pure: weekly snapshots keyed by date, newest KEEP_WEEKS kept."""
    weeks = d.setdefault("weeks", {})
    weeks.update(snap)
    for k in sorted(weeks)[:-KEEP_WEEKS]:
        del weeks[k]
    return d


def changes(d: Dict) -> List[Dict]:
    """Pure: per stock, the newest week against the week before — 千張大戶比例 and 散戶人數 changes."""
    ks = sorted(d.get("weeks") or {})
    if len(ks) < 2:
        return []
    a, b = d["weeks"][ks[-2]], d["weeks"][ks[-1]]
    out = []
    for code, x in b.items():
        y = a.get(code)
        if not y:
            continue
        out.append({"code": code, "big": x["big_pct"], "d_big": round(x["big_pct"] - y["big_pct"], 2),
                    "small_n": x["small_n"], "d_small_n": x["small_n"] - y["small_n"],
                    "d_small_pct": round(x["small_pct"] - y["small_pct"], 2)})
    return out


async def refresh(force: bool = False, now: float = 0) -> Dict:
    d = load()
    now = now or time.time()
    if not force and now - float(d.get("ts_try") or 0) < TTL:
        return d
    d["ts_try"] = now
    try:
        snap = parse(await http.get(URL, kind="text", headers=HDR, timeout=60, retries=1))
        if not snap:
            raise ValueError("TDCC CSV parsed empty")
        merge(d, snap)
        d.update(ts=now, relayed=False)
        HEALTH.ok("tw_holders")
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("tw_holders", str(e) or type(e).__name__, every=TTL)
        log.info("TDCC holders: %s", e)
        seed = _seed()
        if seed.get("weeks"):
            merge(d, seed["weeks"])
            if float(seed.get("ts") or 0) > float(d.get("ts") or 0):
                d.update(ts=seed["ts"], relayed=True)
    FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def _seed() -> Dict:
    try:
        return json.loads(SEED.read_text(encoding="utf-8")) if SEED.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def write_seed(path: Path) -> Dict:
    """PC relay: the stored weeks (history the cloud cache may lack)."""
    d = load()
    if not d.get("weeks") or d.get("relayed"):
        return {}
    out = {"ts": d.get("ts"), "weeks": d["weeks"]}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
