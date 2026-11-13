"""緊急加班車：市場異常大動時叫醒總經口播的加班 routine。

規則（2015 年起回測平均每年約 5 次，抓到的是 2020 年 3 月、2024-08-05、2025 年 4 月這類日子）：
  任一主要行情的單日變動 ≥ 自己近 60 日波動的 5 倍，或同一天有 2 項 ≥ 4 倍。
冷卻 12 小時；台北 05:30–06:30、13:10–14:10、19:00–20:00 不發（早班、午班、晚班馬上就到）。
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
QUIET = (("05:30", "06:30"), ("13:10", "14:10"), ("19:00", "20:00"))     # an hour before 早班 / 午班 (11-14) / 晚班


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


SEC_H = 3 * 3600                 # an SEC filing counts for the next 3 hours


def events(eng, now: Optional[datetime] = None) -> List[Dict]:
    """「有事才加班」的另外兩種事（user, 2026-11-14）：
       * 族群急跌：任一族群紅燈（≥ 平常一天 3 倍），或兩個族群同時黃燈（≥ 2 倍且跌逾 1.5%），規則見 sector_shock
       * SEC 重大申報（3 小時內）：破產、資安事件、減損、下市通知、財報重編，或執行長／財務長／董事長離職
    [{kind, key, text}]；text 是給加班口播的白話原因。"""
    now = now or datetime.now(timezone.utc)
    out: List[Dict] = []
    cut = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    try:
        from . import sector_shock as SS
        h = eng.market.history
        lit = []
        for sym, zh, _en, _kw in SS.SECTORS:
            x = eng.market.q(sym)
            if not x or x.get("chg_pct") is None or str(x.get("asof", "")) < cut or h is None or sym not in h.columns:
                continue
            sd = SS.robust_sd(h[sym])
            lv = SS.level(float(x["chg_pct"]), sd)
            if lv:
                lit.append({"sym": sym, "zh": zh, "chg": float(x["chg_pct"]), "z": float(x["chg_pct"]) / sd, "lv": lv})
        if any(a["lv"] >= 2 for a in lit) or len(lit) >= 2:
            for a in sorted(lit, key=lambda a: a["z"]):
                out.append({"kind": "sector", "key": f'sec:{a["sym"]}',
                            "text": f'族群急跌：{a["zh"]} {a["chg"]:+.1f}%（平常一天的 {abs(a["z"]):.1f} 倍）'})
    except Exception:  # noqa: BLE001
        pass
    try:
        from ..data import sec_officers as SOF
        for a in SOF.load().get("alerts") or []:
            if now.timestamp() - a["ts"] <= SEC_H and SOF.severity(a) >= 3:
                out.append({"kind": "sec", "key": f'8k:{a["acc"]}', "text": a["t"], "url": a.get("url", "")})
    except Exception:  # noqa: BLE001
        pass
    return out


def decide(hs: List[Dict], state: Dict, now: datetime, ev: Optional[List[Dict]] = None) -> Dict:
    big = [h for h in hs if abs(h["sigma"]) >= ONE]
    ev = ev or []
    trig = bool(big) or len(hs) >= 2 or bool(ev)
    tags = sorted(h["t"] for h in hs) + sorted(e["key"] for e in ev)
    key = "brk:" + now.astimezone(TPE).strftime("%Y-%m-%d") + ":" + ",".join(tags) if trig else ""
    hm = now.astimezone(TPE).strftime("%H:%M")
    quiet = any(a <= hm < b for a, b in QUIET)
    cool = now.timestamp() - float(state.get("last_ts") or 0) < COOLDOWN
    fire = trig and not quiet and not cool
    why = ("沒有達到條件" if not trig else "早班、午班或晚班馬上就到" if quiet else "12 小時內已經加班過" if cool else "發車")
    return {"ts": int(now.timestamp()), "fire": fire, "key": key, "hits": hs, "why": why, "reasons": ev,
            "rule": (f"任一行情 ≥ 平常波動 {ONE:g} 倍，或兩項 ≥ {TWO:g} 倍；或族群紅燈／兩個族群黃燈；"
                     "或 3 小時內有 SEC 重大申報（破產、資安、減損、下市通知、財報重編、執行長／財務長／董事長離職）")}


def build(eng, now: Optional[datetime] = None) -> Dict:
    now = now or datetime.now(timezone.utc)
    try:
        hs = hits(eng, now)
    except Exception:  # noqa: BLE001
        hs = []
    try:
        ev = events(eng, now)
    except Exception:  # noqa: BLE001
        ev = []
    st = _load()
    d = decide(hs, st, now, ev)
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

