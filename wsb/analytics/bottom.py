"""抄底四訊號 — a contrarian checklist: CNN Fear & Greed < 10, VIX > 40, S&P 500 RSI(14) < 30, put/call 5-day average > 0.9.

Sources: CNN's Fear & Greed index and its "put and call options" component (CBOE put/call ratio, 5-day average), VIX and
S&P 500 closes from the market history (RSI is Wilder's 14-day).  CNN only serves one year of history, so every fetch
is merged into data_cache/econ_cnn_fg.json and the archive grows a day at a time.

The back-test uses what has a long history — VIX and RSI since 1990 — and counts each episode once (the first day after
at least 20 trading days without the signal), so one crash does not count as fifty separate "buys".  It reports what the
S&P 500 did next, including how much further it fell first.  History, not a forecast, and not a buy signal."""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS
from .signals import rsi_series

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_cnn_fg.json"


def cfg() -> Dict:
    d = {"fg_max": 10.0, "vix_min": 40.0, "rsi_max": 30.0, "pc_min": 0.9, "episode_gap": 20, "stale_days": 4}
    return {**d, **(SETTINGS.get("bottom") or {})}


# ------------------------------------------------------------------ CNN archive
def _day(ms) -> Optional[str]:
    try:
        return datetime.fromtimestamp(float(ms) / 1000, timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return None


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", FILE.name, e)
        return {}


def archive(js: Dict) -> Dict:
    """Merge CNN's graphdata (one year of daily points per series) into the local archive; returns the archive."""
    a = load()
    for key, src in (("fg", "fear_and_greed_historical"), ("pc", "put_call_options")):
        ser = dict(a.get(key) or {})
        for p in ((js.get(src) or {}).get("data") or []):
            d, y = _day(p.get("x")), p.get("y")
            if d and y is not None:
                ser[d] = round(float(y), 4)
        a[key] = dict(sorted(ser.items()))
    fg = js.get("fear_and_greed") or {}
    if fg.get("score") is not None and fg.get("timestamp"):
        a.setdefault("fg", {})[str(fg["timestamp"])[:10]] = round(float(fg["score"]), 4)
    a["ts"] = datetime.now(timezone.utc).timestamp()
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(a), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError as e:
        log.warning("CNN archive not saved: %s", e)
    return a


def _ser(a: Dict, key: str) -> pd.Series:
    d = a.get(key) or {}
    s = pd.Series({pd.Timestamp(k): float(v) for k, v in d.items()}, dtype=float)
    return s.sort_index()


# ------------------------------------------------------------------ back-test
def episodes(mask: pd.Series, gap: int) -> pd.DatetimeIndex:
    """First day of each run of True, where a run starts only after `gap` days without the signal."""
    m = mask.fillna(False).astype(bool)
    prior = m.shift(1).rolling(gap, min_periods=1).max().fillna(0).astype(bool)
    return m.index[m & ~prior]


def forward(spx: pd.Series, days: pd.DatetimeIndex) -> Dict:
    out: Dict = {"n": len(days), "dates": [d.strftime("%Y-%m-%d") for d in days[-8:]]}
    for lab, n in (("1m", 21), ("3m", 63), ("6m", 126), ("12m", 252)):
        r = [(spx.iloc[i + n] / spx.iloc[i] - 1) * 100 for i in (spx.index.get_loc(d) for d in days) if i + n < len(spx)]
        out[lab] = {"med": float(np.median(r)) if r else None, "win": float(np.mean(np.array(r) > 0) * 100) if r else None, "n": len(r)}
    dd, open_dd = [], []
    for d in days:
        i = spx.index.get_loc(d)
        seg = spx.iloc[i:i + 64]
        if len(seg) == 64:                                           # only signals with a full 3 months after them count
            dd.append((float(seg.min()) / float(seg.iloc[0]) - 1) * 100)
        elif len(seg) > 1:                                           # still running: shown apart, "so far"
            open_dd.append({"date": d.strftime("%Y-%m-%d"), "so_far": (float(seg.min()) / float(seg.iloc[0]) - 1) * 100,
                            "days": len(seg) - 1})
    out["further"] = float(np.median(dd)) if dd else None          # how much lower it went first (median, 3 months)
    out["worst"] = float(np.min(dd)) if dd else None
    out["further_n"] = len(dd)
    out["open"] = open_dd
    return out


# ------------------------------------------------------------------ build
def build(eng, today: Optional[date] = None) -> Dict:
    c = cfg()
    spx = eng.market.series("^GSPC").dropna()
    vix = eng.market.series("^VIX").dropna()
    if len(spx) < 300:
        return {"available": False}
    today = today or date.today()
    a = load()
    rsi = rsi_series(spx, 14)
    cr = getattr(getattr(eng, "crypto", None), "data", None) or {}
    fg_s, pc_s = _ser(a, "fg"), _ser(a, "pc")
    fg_v = cr.get("cnn_fng") if cr.get("cnn_fng") is not None else (float(fg_s.iloc[-1]) if len(fg_s) else None)
    fg_d = (fg_s.index[-1].strftime("%Y-%m-%d") if len(fg_s) else None)
    q = eng.market.q("^VIX") or {}
    vix_v = q.get("price") if q.get("price") is not None else (float(vix.iloc[-1]) if len(vix) else None)
    vix_d = str(q.get("asof") or (vix.index[-1].strftime("%Y-%m-%d") if len(vix) else ""))[:10] or None
    sq = eng.market.q("^GSPC") or {}
    s_now = spx.copy()
    if sq.get("price") and sq.get("asof") and pd.Timestamp(str(sq["asof"])[:10]) > spx.index[-1]:
        s_now.loc[pd.Timestamp(str(sq["asof"])[:10])] = float(sq["price"])     # today's session not in the history yet
    rsi_now = rsi_series(s_now, 14)
    rsi_v, rsi_d = float(rsi_now.iloc[-1]), s_now.index[-1].strftime("%Y-%m-%d")
    pc_v = float(pc_s.iloc[-1]) if len(pc_s) else None
    pc_d = pc_s.index[-1].strftime("%Y-%m-%d") if len(pc_s) else None
    stale = (today - timedelta(days=int(c["stale_days"]))).isoformat()
    sig = [
        {"k": "fg", "zh": "CNN 恐懼與貪婪指數", "en": "CNN Fear & Greed", "rule": f"< {c['fg_max']:g}", "v": fg_v, "fmt": "{:.0f}",
         "hit": fg_v is not None and fg_v < c["fg_max"], "date": fg_d},
        {"k": "vix", "zh": "VIX 恐慌指數", "en": "VIX", "rule": f"> {c['vix_min']:g}", "v": vix_v, "fmt": "{:.2f}",
         "hit": vix_v is not None and vix_v > c["vix_min"], "date": vix_d},
        {"k": "rsi", "zh": "標普 500 RSI(14)", "en": "S&P 500 RSI(14)", "rule": f"< {c['rsi_max']:g}", "v": rsi_v, "fmt": "{:.1f}",
         "hit": rsi_v < c["rsi_max"], "date": rsi_d},
        {"k": "pc", "zh": "Put/Call 比率（5 日平均）", "en": "Put/Call ratio (5-day avg)", "rule": f"> {c['pc_min']:g}", "v": pc_v, "fmt": "{:.2f}",
         "hit": pc_v is not None and pc_v > c["pc_min"], "date": pc_d},
    ]
    for s in sig:
        s["stale"] = bool(s["date"] and s["date"] < stale)
        s["avail"] = s["v"] is not None and not s["stale"]
        s["hit"] = bool(s["hit"] and s["avail"])
    n_hit, n_av = sum(s["hit"] for s in sig), sum(s["avail"] for s in sig)

    # back-test on the long series (VIX and RSI since 1990), one count per episode
    j = pd.concat({"spx": spx, "vix": vix, "rsi": rsi}, axis=1).dropna()
    gap = int(c["episode_gap"])
    tests = {"both": (j["vix"] > c["vix_min"]) & (j["rsi"] < c["rsi_max"]), "vix": j["vix"] > c["vix_min"], "rsi": j["rsi"] < c["rsi_max"]}
    bt = {k: forward(j["spx"], episodes(m, gap)) for k, m in tests.items()}
    allr = {}
    for lab, n in (("1m", 21), ("3m", 63), ("6m", 126), ("12m", 252)):
        r = (j["spx"].shift(-n) / j["spx"] - 1).dropna() * 100
        allr[lab] = {"med": float(r.median()), "win": float((r > 0).mean() * 100)}
    bt["all"] = allr
    # the CNN pair over the archive (one year at first, growing daily)
    cnn = {}
    if len(fg_s):
        cnn["fg_last"] = (fg_s[fg_s < c["fg_max"]].index[-1].strftime("%Y-%m-%d") if (fg_s < c["fg_max"]).any() else None)
        cnn["fg_since"] = fg_s.index[0].strftime("%Y-%m-%d")
    if len(pc_s):
        cnn["pc_last"] = (pc_s[pc_s > c["pc_min"]].index[-1].strftime("%Y-%m-%d") if (pc_s > c["pc_min"]).any() else None)
        cnn["pc_since"] = pc_s.index[0].strftime("%Y-%m-%d")
    both_last = tests["both"][tests["both"]].index
    return {"available": True, "signals": sig, "n_hit": n_hit, "n_avail": n_av, "bt": bt, "cnn": cnn, "since": j.index[0].strftime("%Y"),
            "both_last": both_last[-1].strftime("%Y-%m-%d") if len(both_last) else None, "cfg": c,
            "level": "all" if n_hit >= 4 else "near" if n_hit == 3 else "watch" if n_hit == 2 else "none"}
