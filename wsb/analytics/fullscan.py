"""全市場 scan: technical score, rank and entry-signal / watch status for every stock in the full-market lists.

Same rules as the curated board (stockscore.technical_scores, signals.detect/evaluate/status), but technical only —
the intel inputs (news, Form 4, 13F, dark pool, 法人) exist only for the curated ~200 names.  Results are written to
data_cache/fullmarket_<mk>.json and published as site/market/<mk>.json, which the page loads only when searched."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..data import fullmarket as FM
from ..data.stocks import universe
from . import signals as SG
from . import stockscore as SS

log = logging.getLogger(__name__)
COLS = ["sym", "code", "name", "ind", "board", "tech", "rank", "r1d", "r1m", "r6", "rsi", "st", "stl", "why", "when",
        "pat", "patl", "str", "zlo", "zhi", "inv", "risk", "tgt", "tgtp", "inz", "px", "pk", "tier"]
BENCH = {"us": "^GSPC", "tw": "^TWII", "hk": "^HSI"}
LABEL = {"us": ("美股", "US"), "tw": ("台股", "Taiwan"), "hk": ("港股", "Hong Kong")}


def _r(x, d=2):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), d)


def scan(mk: str, items: List[Dict], close: pd.DataFrame, volume: pd.DataFrame, bench: pd.Series) -> Dict:
    cf = FM.cfg()
    zh_names = {s: v[0] for m in universe().values() for s, v in m["symbols"].items()}
    base = SG.base_strengths()
    min_turn = float(cf.get("hk_min_turnover", 5e6)) if mk == "hk" else float(cf.get("min_turnover", 0))
    feats, meta, series = {}, {}, {}
    for it in items:
        s = it["sym"]
        if s not in close.columns:
            continue
        c = close[s].dropna()
        c = c[c > 0]
        if len(c) < SS.MIN_BARS:
            continue
        v = volume[s].reindex(c.index).fillna(0) if s in volume.columns else pd.Series(0.0, index=c.index)
        turn = float((c.tail(20) * v.tail(20)).mean())
        if turn < min_turn:
            continue
        try:
            f = SS.features(c, v, bench)
        except Exception:  # noqa: BLE001
            f = None
        if not f:
            continue
        feats[s], meta[s], series[s] = f, it, (c, v)
    if len(feats) < 10:
        return {"available": False}
    tech = SS.technical_scores(feats)
    rows = []
    for s, f in feats.items():
        it, (c, v) = meta[s], series[s]
        t = tech[s][0]
        row = {"sym": s, "code": it["code"], "name": zh_names.get(s) or it.get("name") or it["code"], "ind": it.get("ind", ""),
               "board": it.get("board", ""), "tech": _r(t, 1), "r1d": _r(f["r1d"], 1), "r1m": _r(f["r1m"], 1), "r6": _r(f["r6"], 0),
               "rsi": _r(f["rsi"], 0), "px": _r(f["price"], 3)}
        if len(c) >= 60:
            try:
                pats = SG.detect(c, v)
                hits = SG.evaluate(pats, t, base)
            except Exception:  # noqa: BLE001
                log.exception("full-market signal %s", s)
                pats, hits = None, []
            if hits:
                h = hits[0]
                pl = h["plan"]
                row.update({"st": "signal", "stl": "有買點訊號", "pat": h["pattern"], "patl": h["label"], "str": _r(min(100, h["strength"] + 5 * (len(hits) - 1)), 1),
                            "zlo": _r(pl["zone_lo"], 3), "zhi": _r(pl["zone_hi"], 3), "inv": _r(h["inv"], 3), "risk": _r(h["risk_pct"], 1),
                            "tgt": _r(pl.get("target"), 3), "tgtp": _r(pl.get("target_pct"), 0), "inz": bool(pl.get("in_zone")),
                            "why": pl.get("where", "")})
            elif pats is not None:
                df0 = next(iter(pats.values()))
                st = SG.status(df0)
                young = "（上市未滿一年：還沒有 200 日線，只檢查突破、收斂突破與超賣）" if df0["ma200"].isna().iloc[-1] else ""
                row.update({"st": st["status"], "stl": st["label"], "why": st["why"] + young, "when": SG.trigger_text(st["status"], df0)[0],
                            "str": _r(st["base"] + 0.25 * (t - 50), 1)})
        else:
            row.update({"st": "nodata", "stl": "資料不足", "why": "上市未滿約三個月，資料太少", "str": 0})
        rows.append(row)
    cfp = SG.pick_cfg()                                              # ★ 規則精選: top n per market among qualifying signals
    cand = sorted([r for r in rows if r.get("st") == "signal" and SG.pick_ok(
        r.get("pat"), r.get("str"), bool(r.get("inz")), (r["tgtp"] / r["risk"]) if r.get("tgtp") and r.get("risk") else None,
        r.get("risk"), cfp)], key=lambda r: -(r.get("str") or 0))
    for i, r in enumerate(cand[:int(cfp["n"]) * 5] if cfp.get("enabled", True) else [], 1):           # full market is much bigger → 5× the curated count
        r["pk"] = i
    for r in rows:
        r["tier"] = SG.tier_fm(r.get("st"), r.get("pk"), r.get("inz"))
    rows.sort(key=lambda r: -(r["tech"] or 0))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r.get("st", "")] = counts.get(r.get("st", ""), 0) + 1
    asof = max(series[s][0].index[-1] for s in series).strftime("%Y-%m-%d")
    return {"available": True, "market": mk, "label": LABEL[mk][0], "label_en": LABEL[mk][1], "asof": asof, "n": len(rows),
            "listed": len(items), "counts": counts, "cols": COLS, "rows": [[r.get(k) for k in COLS] for r in rows]}


def _out(mk: str):
    return DATA_DIR / f"fullmarket_{mk}.json"


async def run(eng, budget_s: Optional[float] = None) -> Dict[str, Dict]:
    """Refresh lists + prices within the time budget, then rescan every market that has data. Returns a status dict."""
    cf = FM.cfg()
    if not cf.get("enabled", True):
        return {}
    budget = float(budget_s if budget_s is not None else cf.get("budget_s", 420))
    t0 = time.time()
    lists = await FM.lists()
    share = cf.get("budget_share") or {"us": 0.45, "tw": 0.3, "hk": 0.25}
    report: Dict[str, Dict] = {}
    for mk in ("us", "tw", "hk"):
        items = lists.get(mk) or []
        if not items:
            continue
        b = eng.market.series(BENCH[mk]) if getattr(eng, "market", None) is not None else pd.Series(dtype=float)
        ref = b.index[-1] if len(b) else None
        deadline = time.time() + budget * float(share.get(mk, 0.33))
        try:
            st = await asyncio.to_thread(FM.refresh_prices, mk, [it["sym"] for it in items], ref, deadline)
        except Exception as e:  # noqa: BLE001
            log.warning("full-market %s prices failed: %s", mk, e)
            st = {"error": str(e)}
        close, volume = FM.load_prices(mk)
        if not close.empty:
            try:
                res = await asyncio.to_thread(scan, mk, items, close, volume, b)
                if res.get("available"):
                    res["pending"] = st.get("pending")
                    _out(mk).write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
                    st["scanned"] = res["n"]
            except Exception:  # noqa: BLE001
                log.exception("full-market %s scan failed", mk)
        report[mk] = {**st, "listed": len(items)}
        log.info("full-market %s: %s", mk, report[mk])
    report["elapsed_s"] = round(time.time() - t0)
    return report


def published(mk: str) -> Optional[Dict]:
    try:
        if _out(mk).exists():
            return json.loads(_out(mk).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    return None
