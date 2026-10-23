"""模型近期失準偵測 — is each model still doing as well lately as it did over its whole test history?

Every check compares a RECENT window with the model's own long-run record, from data already on hand:
* crash model (feature lab, walk-forward out-of-sample predictions): AUC and Brier skill of the latest years with
  known outcomes vs all test years.  Crashes are rare, so "no event lately" is reported as unverifiable, not as fine.
* risk-alert scorecard: hit rate of alert episodes in the last `recent_days` vs all graded episodes.
* earnings implied move (options straddle, used for the NAV-impact estimate): realized next-session move ÷ implied
  move over the latest reports — a median far from 1 means the estimate has been running too low / too high.
* bankruptcy model: outcomes take a year to arrive, so this only reports how long the live record is.
Status per model: ok | watch | drift | insufficient.  A drifting model is not switched off; every place that
shows its number says that it has been less reliable lately ("降低信心")."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import numpy as np

from ..config import SETTINGS

DEFAULTS = {"recent_years": 3, "auc_watch": 0.05, "auc_drift": 0.10, "auc_floor": 0.55, "min_recent_pos": 15,
            "alert_recent_days": 90, "alert_min_n": 5, "earn_min_n": 12, "earn_low": 0.45, "earn_high": 1.6,
            "earn_watch_low": 0.6, "earn_watch_high": 1.3}   # straddles usually price a bit MORE than happens (~0.8 is normal)
LABEL = {"ok": ("正常", "OK"), "watch": ("留意", "Watch"), "drift": ("近期失準", "Drifting"),
         "insufficient": ("樣本不足", "Too few cases")}


def cfg() -> Dict:
    return {**DEFAULTS, **(SETTINGS.get("model_health", {}) or {})}


def _auc(p: np.ndarray, y: np.ndarray) -> Optional[float]:
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order))
    ranks[order] = np.arange(1, len(order) + 1)
    # average ranks for ties
    allv = np.concatenate([pos, neg])
    _, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, weights=ranks)
    ranks = (sums / cnt)[inv]
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def _skill(p: np.ndarray, y: np.ndarray, b: Optional[np.ndarray] = None) -> Optional[float]:
    if not len(y):
        return None
    ref = b if b is not None else np.full(len(y), y.mean())
    bs0 = float(np.mean((ref - y) ** 2))
    return float(1 - np.mean((p - y) ** 2) / bs0) if bs0 > 0 else None


# ------------------------------------------------------------------ crash model (walk-forward OOS)
def crash_drift(p: Iterable[float], y: Iterable[float], yr: Iterable[int], base: Optional[Iterable[float]] = None,
                c: Optional[Dict] = None) -> Dict:
    """p, y, yr: out-of-sample predictions, outcomes (1 = the drawdown happened) and their test year."""
    c = c or cfg()
    p, y, yr = np.asarray(list(p), float), np.asarray(list(y), float), np.asarray(list(yr), int)
    b = np.asarray(list(base), float) if base is not None else None
    if not len(p):
        return {"status": "insufficient", "why": "沒有樣本外紀錄"}
    years = sorted(set(yr.tolist()))
    rec_years = years[-int(c["recent_years"]):]
    m = np.isin(yr, rec_years)
    out = {"overall_auc": _auc(p, y), "overall_skill": _skill(p, y, b), "n": int(len(y)), "pos": int(y.sum()),
           "recent_years": [int(x) for x in rec_years], "recent_auc": _auc(p[m], y[m]),
           "recent_skill": _skill(p[m], y[m], b[m] if b is not None else None), "recent_n": int(m.sum()), "recent_pos": int(y[m].sum())}
    if out["recent_pos"] < int(c["min_recent_pos"]) or out["recent_auc"] is None or out["overall_auc"] is None:
        out["status"] = "insufficient"
        out["why"] = f"最近 {len(rec_years)} 年只有 {out['recent_pos']} 天符合「之後大跌」，事件太少，無法判斷近期準度"
        return out
    gap = out["overall_auc"] - out["recent_auc"]
    if gap >= c["auc_drift"] or out["recent_auc"] < c["auc_floor"]:
        out["status"] = "drift"
    elif gap >= c["auc_watch"] or (out["recent_skill"] is not None and out["recent_skill"] < 0 <= (out["overall_skill"] or 0)):
        out["status"] = "watch"
    else:
        out["status"] = "ok"
    out["why"] = (f"近 {len(rec_years)} 年 AUC {out['recent_auc']:.2f}，全部測試年 {out['overall_auc']:.2f}"
                  + (f"；近期 Brier 技能 {out['recent_skill']:+.2f}" if out["recent_skill"] is not None else ""))
    return out


# ------------------------------------------------------------------ risk alerts
def alert_drift(episodes: List[Dict], now_ts: float, horizon: int, c: Optional[Dict] = None) -> Dict:
    """episodes: scorecard episodes with {"ts", "results": {days: {"hit"} | None}}."""
    c = c or cfg()
    done = [(e["ts"], e["results"][horizon]["hit"]) for e in episodes if (e.get("results") or {}).get(horizon)]
    rec = [h for t, h in done if now_ts - t <= c["alert_recent_days"] * 86400]
    out = {"n": len(done), "recent_n": len(rec), "horizon": horizon,
           "hit": sum(h for _, h in done) / len(done) * 100 if done else None,
           "recent_hit": sum(rec) / len(rec) * 100 if rec else None}
    if len(rec) < c["alert_min_n"] or len(done) < 2 * c["alert_min_n"]:
        out["status"] = "insufficient"
        out["why"] = f"已評分的警報事件 {len(done)} 起（近 {c['alert_recent_days']} 天 {len(rec)} 起），不足以比較"
        return out
    gap = out["hit"] - out["recent_hit"]
    out["status"] = "drift" if gap >= 25 else "watch" if gap >= 12 else "ok"
    out["why"] = f"近 {c['alert_recent_days']} 天命中率 {out['recent_hit']:.0f}%，全部 {out['hit']:.0f}%"
    return out


# ------------------------------------------------------------------ earnings implied move
def earn_drift(pairs: List[Dict], c: Optional[Dict] = None) -> Dict:
    """pairs: [{"sym", "date", "mv": implied ±%, "real": next-session % move}] of past reports, newest last."""
    c = c or cfg()
    ok = [x for x in pairs if x.get("mv") and x.get("real") is not None and x["mv"] > 0]
    ok = ok[-40:]
    out = {"n": len(ok)}
    if len(ok) < c["earn_min_n"]:
        out["status"] = "insufficient"
        out["why"] = f"有選擇權預估、也已公布的財報只有 {len(ok)} 筆"
        return out
    r = np.array([abs(x["real"]) / x["mv"] for x in ok])
    out.update({"median_ratio": float(np.median(r)), "within": float((r <= 1).mean() * 100)})
    lo, hi = c["earn_low"], c["earn_high"]
    med = out["median_ratio"]
    out["status"] = "drift" if (med >= hi or med <= lo) else "watch" if (med >= c["earn_watch_high"] or med <= c["earn_watch_low"]) else "ok"
    out["why"] = (f"最近 {len(ok)} 次財報：實際跳空／預估跳空 中位數 {med:.2f}，{out['within']:.0f}% 落在預估範圍內"
                  + ("（預估偏低）" if med >= c["earn_watch_high"] else "（預估偏高）" if med <= c["earn_watch_low"] else ""))
    return out


# ------------------------------------------------------------------ engine glue
def _alert_input(eng):
    from .. import store
    from . import scorecard as SC
    spx = eng.market.series("^GSPC")
    rows = [r for r in store.tracked_alerts(365) if r[2] == "risk"]
    if not rows or spx is None or len(spx) < 300:
        return None, None
    eps = SC._episodes(rows)
    SC._grade(eps, spx.dropna())
    return eps, max(h["days"] for h in SC.HORIZONS)


def _earn_pairs(eng, today: str) -> List[Dict]:
    from . import earn_verdict as EV
    from . import techearn as TE
    out = []
    for k, v in sorted(EV._load_implied().items(), key=lambda kv: kv[0].split("|")[-1]):
        sym, _, d = k.partition("|")
        if not d or d >= today or not v.get("mv"):
            continue
        real = TE.reaction(EV._series(eng, sym), d)
        if real is not None:
            out.append({"sym": sym, "date": d, "mv": float(v["mv"]), "real": float(real)})
    return out


def build(eng, now_ts: Optional[float] = None) -> Dict:
    import json
    import time
    from datetime import datetime, timezone
    from pathlib import Path
    now_ts = now_ts or time.time()
    today = datetime.fromtimestamp(now_ts, timezone.utc).strftime("%Y-%m-%d")
    models: List[Dict] = []
    for rep in (getattr(eng, "lab", None) or {}).get("horizons", []) or []:
        if rep.get("drift"):
            dd = rep.get("drawdown_pct") or 0
            models.append({"key": f"crash_{rep.get('days')}", "zh": f"崩跌機率模型（{rep.get('days')} 交易日內跌 ≥{dd:.0f}%）",
                           "en": f"Crash model (≥{dd:.0f}% fall within {rep.get('days')}d)", **rep["drift"]})
    try:
        eps, hz = _alert_input(eng)
        if eps:
            models.append({"key": "alerts", "zh": f"風險警報（之後 {hz} 交易日）", "en": f"Risk alerts ({hz}d)", **alert_drift(eps, now_ts, hz)})
    except Exception:  # noqa: BLE001
        pass
    try:
        models.append({"key": "earn_move", "zh": "財報跳空預估（選擇權隱含）", "en": "Earnings implied move", **earn_drift(_earn_pairs(eng, today))})
    except Exception:  # noqa: BLE001
        pass
    try:
        bk = json.loads((Path(__file__).with_name("bankruptcy_model.json")).read_text(encoding="utf-8"))
        models.append({"key": "bankruptcy", "zh": "破產預測模型", "en": "Bankruptcy model", "status": "insufficient",
                       "why": f"{bk.get('trained', '—')} 訓練，樣本外 AUC {format(bk['oos']['auc'], '.2f') if (bk.get('oos') or {}).get('auc') is not None else '—'}（{str(bk.get('eval_years', ''))[:9]}）；"
                              "上線後的實際破產要一年以上才會出現，紀錄累積中"})
    except Exception:  # noqa: BLE001
        pass
    worst = "drift" if any(m["status"] == "drift" for m in models) else "watch" if any(m["status"] == "watch" for m in models) else         "ok" if any(m["status"] == "ok" for m in models) else "insufficient"
    return {"available": bool(models), "models": models, "status": worst, "ts": now_ts}


def flag(health: Optional[Dict], key_prefix: str) -> Optional[Dict]:
    """The worst status among models whose key starts with key_prefix (for a 'less reliable lately' note)."""
    ms = [m for m in (health or {}).get("models", []) if str(m.get("key", "")).startswith(key_prefix)]
    for st in ("drift", "watch"):
        hit = [m for m in ms if m["status"] == st]
        if hit:
            return hit[0]
    return None
