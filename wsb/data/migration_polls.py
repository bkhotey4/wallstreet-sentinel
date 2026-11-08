"""移民與民意：人變少、人不滿，怎麼傳到就業、物價和政策。

移民（美國勞工統計局家戶調查，FRED，月資料，未季調所以都看「和一年前比」）：
  * 外國出生 vs 本國出生的勞動力（LNU01073395 / LNU01073413）一年增減、外國出生占勞動力比重、兩邊失業率。
  * 每月新增非農就業（PAYEMS 3 個月平均）對照勞動力每月增加多少：移民變少時，維持失業率不變需要的新增工作也變少，
    「新增就業變少」不一定代表經濟變差。
  * 移民比例高的行業時薪：營造業（CES2000000003）、休閒餐旅（CES7000000003）對民間平均（CES0500000003）的年增率差距；
    差距拉大代表缺工推高工資，最後可能反映在房價、外食價格。
  * 每年 1 月勞工統計局更新人口估計，數字會跳一下，看方向比看大小可靠。
民意（VoteHub 彙整的各家總統支持度民調，免費 API）：最近 30 天每家民調機構取最新一筆後平均，少於 3 家就放寬到 60、90 天並註明；
和 90 天前同樣算法比。政策不確定指數在「人類溫度計」卡，這裡引用。
快取 data_cache/econ_polls.json（CI 保留 econ_*），12 小時一次。描述現況，不是預測。"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_polls.json"
TTL = 12 * 3600
POLLS_URL = "https://api.votehub.com/polls"
POLLS_PAGE = "https://votehub.com/polls/"
FB, NB, FB_U, NB_U = "LNU01073395", "LNU01073413", "LNU04073395", "LNU04073413"
WAGES = (("CES2000000003", "營造業"), ("CES7000000003", "休閒餐旅"))
WAGE_ALL = "CES0500000003"
FRED_IDS = (FB, NB, FB_U, NB_U, "PAYEMS", WAGE_ALL) + tuple(w for w, _ in WAGES)
WAGE_GAP = 1.0                       # 行業時薪年增率比整體高 1 個百分點以上 → 缺工訊號


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def clean_polls(js) -> List[Dict]:
    out = []
    for p in js if isinstance(js, list) else []:
        try:
            ans = {a["choice"]: float(a["pct"]) for a in p.get("answers") or []}
            if "Approve" not in ans or "Disapprove" not in ans or not p.get("end_date"):
                continue
            out.append({"end": str(p["end_date"])[:10], "who": str(p.get("pollster") or "?"), "pop": str(p.get("population") or ""),
                        "n": p.get("sample_size"), "app": ans["Approve"], "dis": ans["Disapprove"], "url": str(p.get("url") or "")})
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(out, key=lambda x: x["end"])


async def refresh(force: bool = False) -> Dict:
    from .freshness import bundle_ts, due
    d = load()
    now = time.time()
    d["ts_check"] = now
    each = d.setdefault("ts_each", {})
    if due(d, ["approval"], TTL, now, force):
        d["try_each"]["approval"] = now
        try:
            ps = clean_polls(await http.get(POLLS_URL, params={"poll_type": "approval", "subject": "Trump"}, timeout=60, retries=1))
            if len(ps) < 50:
                raise ValueError(f"only {len(ps)} polls")
            d["approval"], each["approval"] = ps, now
            HEALTH.ok("polls", len(ps), every=TTL)
        except Exception as e:  # noqa: BLE001
            log.warning("polls: %s", e)
            HEALTH.fail("polls", str(e) or type(e).__name__, every=TTL)
        d["ts"] = bundle_ts(d, ["approval"])
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def poll_avg(ps: List[Dict], asof: date, days: int = 30) -> Optional[Dict]:
    """Latest poll per pollster within `days` before `asof`, averaged; widened to 60, then 90 days while fewer than 3 pollsters."""
    wins = (days, days * 2, days * 3)
    for win in wins:
        lo, hi = (asof - timedelta(days=win)).isoformat(), asof.isoformat()
        last: Dict[str, Dict] = {}
        for p in ps:
            if lo < p["end"] <= hi:
                last[p["who"]] = p
        if len(last) >= 3 or win == wins[-1]:
            if not last:
                return None
            xs = list(last.values())
            return {"app": sum(x["app"] for x in xs) / len(xs), "dis": sum(x["dis"] for x in xs) / len(xs), "n": len(xs), "win": win,
                    "latest": max(x["end"] for x in xs)}
    return None


def approval(d: Dict, today: Optional[date] = None) -> Optional[Dict]:
    ps = d.get("approval") or []
    if not ps:
        return None
    today = today or date.today()
    now = poll_avg(ps, today)
    if not now:
        return None
    then = poll_avg(ps, today - timedelta(days=90))
    df = pd.DataFrame(ps)
    df["m"] = df["end"].str[:7]
    hist = [[m + "-15", round(float(g["app"].mean()), 1)] for m, g in df.groupby("m")]
    rec = sorted(ps, key=lambda x: x["end"])[-5:][::-1]
    return {**now, "chg90": (now["app"] - then["app"]) if then else None, "net": now["app"] - now["dis"], "hist": hist[-24:], "recent": rec}


def _yoy(s: pd.Series) -> Optional[float]:
    s = s.dropna()
    if len(s) < 13:
        return None
    return float((s.iloc[-1] / s.iloc[-13] - 1) * 100)


def migration(get) -> Optional[Dict]:
    fb, nb = get(FB), get(NB)
    if fb is None or nb is None or len(fb.dropna()) < 36 or len(nb.dropna()) < 36:
        return None
    fb, nb = fb.dropna(), nb.dropna()
    d12 = (fb - fb.shift(12)).dropna()
    nd12 = (nb - nb.shift(12)).dropna()
    out = {"asof": fb.index[-1].strftime("%Y-%m"), "since": fb.index[0].strftime("%Y"), "fb": float(fb.iloc[-1]), "fb_d": float(d12.iloc[-1]),
           "nb_d": float(nd12.iloc[-1]) if len(nd12) else None, "share": float(fb.iloc[-1] / (fb.iloc[-1] + nb.iloc[-1]) * 100),
           "share_1y": float(fb.iloc[-13] / (fb.iloc[-13] + nb.iloc[-13]) * 100),
           "fb_pct": float((d12.iloc[:-1] < d12.iloc[-1]).mean() * 100),
           "fb_hist": [[i.strftime("%Y-%m-%d"), round(float(v), 0)] for i, v in d12.tail(60).items()]}
    fu, nu = get(FB_U), get(NB_U)
    if fu is not None and nu is not None and len(fu.dropna()) and len(nu.dropna()):
        out.update(fb_u=float(fu.dropna().iloc[-1]), nb_u=float(nu.dropna().iloc[-1]))
    pay = get("PAYEMS")
    if pay is not None and len(pay.dropna()) > 4:
        p = pay.dropna()
        out["pay3"] = float(p.diff().tail(3).mean())
        out["lf_m"] = float((d12.iloc[-1] + (nd12.iloc[-1] if len(nd12) else 0)) / 12)
    tot = _yoy(get(WAGE_ALL)) if get(WAGE_ALL) is not None else None
    ws = []
    for sid, zh in WAGES:
        s = get(sid)
        y = _yoy(s) if s is not None else None
        if y is not None and tot is not None:
            ws.append({"zh": zh, "yoy": y, "gap": y - tot})
    out.update(wage_all=tot, wages=ws)
    hot = [w["zh"] for w in ws if w["gap"] >= WAGE_GAP]
    if out["fb_d"] < 0 and hot:
        out["emoji"], out["state"] = "🟡", "移民勞動力減少，缺工行業時薪漲得比較快"
    elif out["fb_d"] < 0:
        out["emoji"], out["state"] = "🟡", "移民勞動力比一年前少"
    elif hot:
        out["emoji"], out["state"] = "🟡", "缺工行業時薪漲得比較快"
    else:
        out["emoji"], out["state"] = "🟢", "勞動力還在增加，缺工行業時薪沒有特別快"
    out["hot"] = hot
    return out


def view(eng=None) -> Dict:
    fr = getattr(eng, "fred", None)
    get = (lambda sid: fr.get(sid)) if fr is not None else (lambda sid: None)
    out = {"ts": load().get("ts")}
    try:
        out["mig"] = migration(get)
    except Exception:  # noqa: BLE001
        log.exception("migration view failed")
        out["mig"] = None
    try:
        out["app"] = approval(load())
    except Exception:  # noqa: BLE001
        log.exception("approval view failed")
        out["app"] = None
    return out
