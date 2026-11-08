"""緊急加班車：市場異常大動時叫醒總經口播的加班 routine。

規則（2015 年起回測平均每年約 5 次，抓到的是 2020 年 3 月、2024-08-05、2025 年 4 月這類日子）：
  任一主要行情的單日變動 ≥ 自己近 60 日波動的 5 倍，或同一天有 2 項 ≥ 4 倍。
冷卻 12 小時；台北 05:30–06:30 與 19:00–20:00 不發（早班、晚班馬上就到）。
每次建置寫 breaking.json（公開，只有行情數字），fire=true 時 workflow 才去叫 routine。
狀態存 data_cache/econ_breaking.json（CI 保留 econ_*）。描述現況，不是預測。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np

from ..config import DATA_DIR, SETTINGS

FILE = DATA_DIR / "econ_breaking.json"
ASSETS = ("^GSPC", "^NDX", "^VIX", "^TNX", "HYG", "DX-Y.NYB", "JPY=X", "BZ=F", "GC=F", "^TWII")
ONE, TWO = 5.0, 4.0
COOLDOWN = 12 * 3600
TPE = timezone(timedelta(hours=8))
QUIET = (("05:30", "06:30"), ("19:00", "20:00"))


def _load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def hits(eng, now: Optional[datetime] = None) -> List[Dict]:
    now = now or datetime.now(timezone.utc)
    cut = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    names = SETTINGS.names()
    out = []
    for t in ASSETS:
        sg, x = eng.market.sigma_move(t), eng.market.q(t)
        if sg is None or not x or x.get("chg_pct") is None or str(x.get("asof", "")) < cut:
            continue
        if not (x["chg_pct"] == x["chg_pct"]) or np.sign(sg) != np.sign(x["chg_pct"]):
            continue                                   # quote and history disagree → data glitch
        if abs(sg) >= TWO:
            out.append({"t": t, "name": names.get(t, t), "chg_pct": round(float(x["chg_pct"]), 2), "sigma": round(float(sg), 1),
                        "asof": str(x["asof"])[:10]})
    return sorted(out, key=lambda h: -abs(h["sigma"]))


def decide(hs: List[Dict], state: Dict, now: datetime) -> Dict:
    big = [h for h in hs if abs(h["sigma"]) >= ONE]
    trig = bool(big) or len(hs) >= 2
    key = "brk:" + now.astimezone(TPE).strftime("%Y-%m-%d") + ":" + ",".join(sorted(h["t"] for h in hs)) if trig else ""
    hm = now.astimezone(TPE).strftime("%H:%M")
    quiet = any(a <= hm < b for a, b in QUIET)
    cool = now.timestamp() - float(state.get("last_ts") or 0) < COOLDOWN
    fire = trig and not quiet and not cool
    why = ("沒有達到條件" if not trig else "早班或晚班馬上就到" if quiet else "12 小時內已經加班過" if cool else "發車")
    return {"ts": int(now.timestamp()), "fire": fire, "key": key, "hits": hs, "why": why,
            "rule": f"任一行情 ≥ 平常波動 {ONE:g} 倍，或兩項 ≥ {TWO:g} 倍"}


def build(eng, now: Optional[datetime] = None) -> Dict:
    now = now or datetime.now(timezone.utc)
    try:
        hs = hits(eng, now)
    except Exception:  # noqa: BLE001
        hs = []
    st = _load()
    d = decide(hs, st, now)
    if d["fire"]:
        st.update(last_ts=d["ts"], last_key=d["key"])
        st.setdefault("log", []).append({"ts": d["ts"], "key": d["key"], "hits": hs})
        st["log"] = st["log"][-50:]
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FILE)
    d["last"] = st.get("last_key") or ""
    d["last_ts"] = int(st.get("last_ts") or 0) or None
    return d

