"""夜間分級（2026-11-15，使用者選的 B-4）：夜裡只有 🔴／🚨 讓手機響，其他照樣即時送到但用 Discord 的「靜音訊息」
（訊息旗標 SUPPRESS_NOTIFICATIONS＝4096：訊息會出現、不跳推播），所以不會晚到，只是不吵你。
時段在 settings.yaml 的 delivery.night（台北時間）。靜音送出的會記在 data_cache/night_silent.json，早安摘要拿來列「夜裡送了什麼」。"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .config import DATA_DIR, SETTINGS

TPE = timezone(timedelta(hours=8))
SILENT_FLAG = 4096
LOG = DATA_DIR / "night_silent.json"
LOUD = ("🔴", "🚨")


def window() -> tuple:
    n = (SETTINGS.get("delivery", {}) or {}).get("night") or {}
    return str(n.get("start", "23:30")), str(n.get("end", "07:00"))


def is_night(ts: Optional[float] = None, win: Optional[tuple] = None) -> bool:
    start, end = win or window()
    if start == end:
        return False
    hm = datetime.fromtimestamp(ts if ts is not None else time.time(), TPE).strftime("%H:%M")
    return (start <= hm < end) if start < end else (hm >= start or hm < end)


def loud(title: str) -> bool:
    """🔴 / 🚨 at the start of the title (after any 'delayed' prefix) always rings."""
    t = str(title or "").lstrip()
    return t.startswith(LOUD) or any(m in t[:40] for m in LOUD)


def silent(title: str, ts: Optional[float] = None) -> bool:
    return is_night(ts) and not loud(title)


def note(title: str, src: str, ts: Optional[float] = None) -> None:
    now = ts if ts is not None else time.time()
    try:
        rows = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    except (OSError, ValueError):
        rows = []
    rows = [r for r in rows if now - float(r.get("ts") or 0) < 2 * 86400][-300:] + [{"ts": now, "t": str(title)[:200], "src": src}]
    try:
        tmp = LOG.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        tmp.replace(LOG)
    except OSError:
        pass


def since(ts: float) -> List[Dict]:
    try:
        return [r for r in json.loads(LOG.read_text(encoding="utf-8")) if float(r.get("ts") or 0) > ts]
    except (OSError, ValueError):
        return []
