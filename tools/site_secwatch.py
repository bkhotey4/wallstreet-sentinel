"""SEC 人事申報警報的名單：每次建置寫 sec_watch.json（公開），給 /api/news 的 Cloudflare 函式比對 SEC 最新 8-K。

名單＝本站追蹤池（公開的那份）＋財報日曆裡出現過、市值 ≥ 1,000 億美元的公司；用 SEC 官方 ticker → CIK 對照。
不含任何持股資料。格式 {"ts":…, "ciks": {"1045810": ["NVDA", "輝達"], …}}。"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict

log = logging.getLogger(__name__)


def build(eng) -> Dict:
    from wsb.data.stocks import universe
    from wsb.data import earn_official as EO
    from wsb.data.edgar_holdings import _MAP_FILE
    names = (universe().get("us") or {}).get("symbols", {})
    ed = getattr(eng, "earnings", None)
    big = EO.universe((getattr(ed, "days", None) or {}) if ed is not None else {}, [], EO.load().get("known"))
    try:
        tmap = json.loads(_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        tmap = {}
    out: Dict[str, list] = {}
    for s in list(names) + [k for k, v in big.items() if (v.get("mcap") or 0) >= 1e11]:
        cik = (tmap.get(s) or tmap.get(s.replace("-", ".")) or {}).get("cik")
        if cik and str(int(cik)) not in out:
            zh = names[s][0] if s in names else (big.get(s) or {}).get("name") or s
            out[str(int(cik))] = [s, zh]
    return {"ts": int(time.time()), "ciks": out}
