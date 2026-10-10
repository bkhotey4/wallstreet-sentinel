"""SQLite persistence: settings set from Discord, alert cooldowns, seen news,
stress-index snapshots (so trends are real history, not guesses)."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from typing import Any, List, Optional, Tuple

from .config import DATA_DIR

_DB = DATA_DIR / "sentinel.db"
_LOCK = threading.Lock()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB, check_same_thread=False)
    return c


_C = _conn()
with _LOCK:
    _C.executescript(
        """
        CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE IF NOT EXISTS alerts (key TEXT PRIMARY KEY, ts REAL, payload TEXT);
        CREATE TABLE IF NOT EXISTS alert_log (ts REAL, key TEXT, severity TEXT, title TEXT);
        CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY, ts REAL);
        CREATE TABLE IF NOT EXISTS stress (ts REAL PRIMARY KEY, score REAL, blocks TEXT);
        CREATE TABLE IF NOT EXISTS price_alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, ticker TEXT,
                                                 op TEXT, value REAL, note TEXT, created REAL, active INTEGER DEFAULT 1,
                                                 fired REAL);
        CREATE TABLE IF NOT EXISTS alert_track (ts REAL, key TEXT, kind TEXT, severity TEXT,
                                                title TEXT, spx REAL, ssi REAL);
        CREATE TABLE IF NOT EXISTS intel_heat (ts REAL, channel TEXT, heat REAL, n INTEGER);
        CREATE INDEX IF NOT EXISTS ix_intel_heat ON intel_heat (channel, ts);
        CREATE TABLE IF NOT EXISTS news_tags (uid TEXT PRIMARY KEY, ts REAL, tags TEXT);
        """
    )
    _C.commit()


def kv_get(k: str, default: Any = None) -> Any:
    with _LOCK:
        row = _C.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    return json.loads(row[0]) if row else default


def kv_set(k: str, v: Any) -> None:
    with _LOCK:
        _C.execute("INSERT OR REPLACE INTO kv VALUES (?,?)", (k, json.dumps(v, ensure_ascii=False)))
        _C.commit()


def alert_allowed(key: str, cooldown_s: float) -> bool:
    now = time.time()
    muted_until = kv_get("mute_until", 0) or 0
    if now < muted_until:
        return False
    with _LOCK:
        row = _C.execute("SELECT ts FROM alerts WHERE key=?", (key,)).fetchone()
    return not row or now - row[0] >= cooldown_s


def alert_mark(key: str, severity: str, title: str, kind: str | None = None,
               spx: float | None = None, ssi: float | None = None) -> None:
    now = time.time()
    with _LOCK:
        _C.execute("INSERT OR REPLACE INTO alerts VALUES (?,?,?)", (key, now, title))
        _C.execute("INSERT INTO alert_log VALUES (?,?,?,?)", (now, key, severity, title))
        if kind:
            _C.execute("INSERT INTO alert_track VALUES (?,?,?,?,?,?,?)", (now, key, kind, severity, title, spx, ssi))
        _C.commit()


def tracked_alerts(days: float = 365) -> List[Tuple]:
    with _LOCK:
        return _C.execute("SELECT ts, key, kind, severity, title, spx, ssi FROM alert_track WHERE ts>? ORDER BY ts",
                          (time.time() - days * 86400,)).fetchall()


def recent_alerts(hours: float = 24) -> List[Tuple[float, str, str]]:
    with _LOCK:
        return _C.execute(
            "SELECT ts, severity, title FROM alert_log WHERE ts>? ORDER BY ts DESC LIMIT 30",
            (time.time() - hours * 3600,),
        ).fetchall()


def alerts_since(hours: float = 168) -> List[Tuple[float, str, str, str]]:
    """(ts, key, severity, title) for every alert sent in the window (no row cap)."""
    with _LOCK:
        return _C.execute("SELECT ts, key, severity, title FROM alert_log WHERE ts>? ORDER BY ts DESC",
                          (time.time() - hours * 3600,)).fetchall()


def seen_check_and_mark(item_id: str) -> bool:
    """Returns True if item is new (and marks it)."""
    with _LOCK:
        if _C.execute("SELECT 1 FROM seen WHERE id=?", (item_id,)).fetchone():
            return False
        _C.execute("INSERT INTO seen VALUES (?,?)", (item_id, time.time()))
        # news ids expire after 14 days; SEC accession ids are kept ~400 days (filings lists go back months)
        _C.execute("DELETE FROM seen WHERE ts<? AND id NOT LIKE 'sec:%'", (time.time() - 14 * 86400,))
        _C.execute("DELETE FROM seen WHERE ts<? AND id LIKE 'sec:%'", (time.time() - 400 * 86400,))
        _C.commit()
    return True


def stress_record(score: float, blocks: dict) -> None:
    with _LOCK:
        _C.execute("INSERT OR REPLACE INTO stress VALUES (?,?,?)",
                   (time.time(), score, json.dumps(blocks, ensure_ascii=False)))
        _C.execute("DELETE FROM stress WHERE ts<?", (time.time() - 120 * 86400,))
        _C.commit()


def stress_at(hours_ago: float) -> Optional[float]:
    with _LOCK:
        row = _C.execute(
            "SELECT score FROM stress WHERE ts<=? ORDER BY ts DESC LIMIT 1",
            (time.time() - hours_ago * 3600,),
        ).fetchone()
    return row[0] if row else None


# ---------------- news-heat history (baseline for the intelligence-fusion layer) ----------------
def heat_record(heats: dict, min_gap_s: float = 1800, keep_days: float = 60) -> bool:
    """Store one snapshot of per-channel news heat, at most every `min_gap_s` (news refreshes every few minutes and
    overlapping 36h windows would otherwise flood the baseline).  Returns True when a row set was written."""
    now = time.time()
    with _LOCK:
        row = _C.execute("SELECT MAX(ts) FROM intel_heat").fetchone()
        if row and row[0] and now - row[0] < min_gap_s:
            return False
        _C.executemany("INSERT INTO intel_heat VALUES (?,?,?,?)",
                       [(now, ch, float(h), int(n)) for ch, (h, n) in heats.items()])
        _C.execute("DELETE FROM intel_heat WHERE ts<?", (now - keep_days * 86400,))
        _C.commit()
    return True


def heat_reset() -> None:
    """Drop the news-heat baseline (used once when the heat method changes, so old and new scales never mix)."""
    with _LOCK:
        _C.execute("DELETE FROM intel_heat")
        _C.commit()


def news_tags_save(tags: dict) -> None:
    now = time.time()
    with _LOCK:
        _C.executemany("INSERT OR REPLACE INTO news_tags VALUES (?,?,?)",
                       [(uid, now, json.dumps(t, ensure_ascii=False)) for uid, t in tags.items()])
        _C.execute("DELETE FROM news_tags WHERE ts<?", (now - 3 * 86400,))     # headlines live ≤36h in the wire
        _C.commit()


def news_tags_load(days: float = 3) -> dict:
    with _LOCK:
        rows = _C.execute("SELECT uid, tags FROM news_tags WHERE ts>?", (time.time() - days * 86400,)).fetchall()
    return {u: json.loads(t) for u, t in rows}


def heat_history(channel: str, days: float = 30) -> List[float]:
    with _LOCK:
        return [r[0] for r in _C.execute("SELECT heat FROM intel_heat WHERE channel=? AND ts>? ORDER BY ts",
                                         (channel, time.time() - days * 86400)).fetchall()]


# ---------------- personal price alerts ----------------
def palert_add(user_id: str, ticker: str, op: str, value: float, note: str = "") -> int:
    with _LOCK:
        cur = _C.execute("INSERT INTO price_alerts (user_id, ticker, op, value, note, created) VALUES (?,?,?,?,?,?)",
                         (str(user_id), ticker.upper(), op, float(value), note, time.time()))
        _C.commit()
        return int(cur.lastrowid)


def palert_list(user_id: str | None = None, active_only: bool = True) -> List[Tuple]:
    q = "SELECT id, user_id, ticker, op, value, note, created, active, fired FROM price_alerts"
    cond, args = [], []
    if user_id is not None:
        cond.append("user_id=?")
        args.append(str(user_id))
    if active_only:
        cond.append("active=1")
    if cond:
        q += " WHERE " + " AND ".join(cond)
    with _LOCK:
        return _C.execute(q + " ORDER BY id", args).fetchall()


def palert_remove(alert_id: int, user_id: str) -> bool:
    with _LOCK:
        cur = _C.execute("UPDATE price_alerts SET active=0 WHERE id=? AND user_id=?", (int(alert_id), str(user_id)))
        _C.commit()
        return cur.rowcount > 0


def palert_fire(alert_id: int) -> None:
    with _LOCK:
        _C.execute("UPDATE price_alerts SET active=0, fired=? WHERE id=?", (time.time(), int(alert_id)))
        _C.commit()


def palert_tickers() -> List[str]:
    with _LOCK:
        return [r[0] for r in _C.execute("SELECT DISTINCT ticker FROM price_alerts WHERE active=1").fetchall()]


def backup(keep: int = 7) -> Optional[str]:
    """Consistent online copy of sentinel.db (sqlite backup API) into data_cache/backups/, one per day; keeps the newest `keep`."""
    d = DATA_DIR / "backups"
    d.mkdir(exist_ok=True)
    dest = d / f"sentinel_{time.strftime('%Y%m%d')}.db"
    if dest.exists():
        return None
    tmp = dest.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    out = sqlite3.connect(tmp)
    try:
        with _LOCK:
            _C.backup(out)
    finally:
        out.close()
    tmp.replace(dest)
    for old in sorted(d.glob("sentinel_*.db"))[:-keep]:
        old.unlink(missing_ok=True)
    return str(dest)
