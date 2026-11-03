"""公布前估算的原始資料（FRED，免費）：CPI／PPI／PCE、ADP（月與週）、非農、初領失業金、GDPNow、GDP 實際值。
快取 data_cache/econ_nowcast.json（CI 保留 econ_*），每 12 小時最多抓一次；"log" 保存每個目標期在公布前的估算與
第一次看到的公布值，給「公布後比對」用（估算模型在 wsb/analytics/nowcast.py）。"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict

from ..config import DATA_DIR
from ..health import HEALTH

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_nowcast.json"
TTL = 12 * 3600
SERIES = ("PCEPILFE", "PCEPI", "CPILFESL", "CPIAUCSL", "PPIFES", "PPIFIS", "ADPMNUSNERSA", "ADPWNUSNERSA", "PAYEMS", "ICSA",
          "GDPNOW", "A191RL1Q225SBEA")


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)


async def refresh(force: bool = False) -> Dict:
    from ..analytics import nowcast as NC
    from .freshness import bundle_ts, due
    from .transmission import _fred
    d = load()
    now = time.time()
    bad = []
    todo = due(d, SERIES, TTL, now, force)                   # per series: a failed one is retried within the hour
    for sid in todo:
        d["try_each"][sid] = now
        try:
            v = await _fred(sid, "2010-01-01")
            if not v:
                raise ValueError("empty")
            d[sid], d["ts_each"][sid] = v, now
        except Exception as e:  # noqa: BLE001
            bad.append(f"{sid}: {e if str(e) else type(e).__name__}")
    # a series still stale from an earlier failure keeps health red while it waits for its retry
    bad += [f"{k}: stale" for k in SERIES if k not in todo and now - float(d["ts_each"].get(k, 0)) > TTL]
    d["ts"] = bundle_ts(d, SERIES)
    try:
        d["log"] = NC.update_log(d)
    except Exception as e:  # noqa: BLE001
        bad.append(f"model: {e}")
    _save(d)
    if bad:
        log.warning("nowcast data: %s", "; ".join(bad))
        HEALTH.fail("nowcast", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("nowcast", len(d.get("log") or {}), every=TTL)
    return d
