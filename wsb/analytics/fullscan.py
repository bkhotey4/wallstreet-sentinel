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
        "pat", "patl", "str", "zlo", "zhi", "inv", "risk", "tgt", "tgtp", "inz", "px", "pk", "tier", "zb", "tg", "ex", "history_asof", "ma2", "m121", "hi52", "rel6",
        "vol", "lt", "ldd", "lr", "lv", "vm", "vnow", "vpct", "vp25", "vp50", "vp75", "vn", "vasof"]
BENCH = {"us": "^GSPC", "tw": "^TWII", "hk": "^HSI", "jp": "^N225"}
LABEL = {"us": ("美股", "US"), "tw": ("台股", "Taiwan"), "hk": ("港股", "Hong Kong"), "jp": ("日股", "Japan")}


def _r(x, d=2):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), d)


def labels(row: Dict) -> Dict:
    """Neutral check-up marks from price data alone (descriptions, not recommendations)."""
    px, ma, hi, mom, rsi = row.get("px"), row.get("ma2"), row.get("hi52"), row.get("m121"), row.get("rsi")
    out = {}
    if px and ma:
        up = px > ma
        out["lt"] = ("多頭" if up and (mom is None or mom > 0) else "空頭" if not up and (mom is None or mom < 0) else "盤整")
    if px and hi:
        out["ldd"] = _r((px / hi - 1) * 100, 1)
    if rsi is not None:
        out["lr"] = "偏熱" if rsi >= 70 else "偏冷" if rsi <= 30 else "中性"
    return out


def val_fields(z: Optional[Dict]) -> Dict:
    if not z:
        return {}
    return {"vm": z["metric"], "vnow": _r(z["now"], 2), "vpct": _r(z["pct"], 0), "vp25": _r(z["p25"], 3), "vp50": _r(z["p50"], 3),
            "vp75": _r(z["p75"], 3), "vn": z["n"], "vasof": z.get("asof")}


def scan(mk: str, items: List[Dict], close: pd.DataFrame, volume: pd.DataFrame, bench: pd.Series, zones: Optional[Dict] = None) -> Dict:
    cf = FM.cfg()
    zh_names = {s: v[0] for m in universe().values() for s, v in m["symbols"].items()}
    base = SG.base_strengths()
    min_turn = float(cf.get("hk_min_turnover", 5e6)) if mk == "hk" else float(cf.get("min_turnover", 0))
    feats, meta, series, thin = {}, {}, {}, {}
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
        thin[s] = turn < float(cf.get("thin_turnover", {}).get(mk, 0) or 0)
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
        try:                                          # inputs of the holdings rule check (my rule check) for ANY listed stock
            from .rulebook import price_stats
            rs = price_stats(c, bench)
        except Exception:  # noqa: BLE001
            rs = {}
        row = {"ma2": _r(rs.get("ma200"), 3), "m121": _r(rs.get("mom_12_1"), 1), "hi52": _r(rs.get("high_52w"), 3),
               "rel6": _r(rs.get("rel_6m"), 1), "vol": _r(rs.get("vol"), 0),
               "sym": s, "code": it["code"], "name": zh_names.get(s) or it.get("name") or it["code"], "ind": it.get("ind", ""),
               "board": it.get("board", ""), "tech": _r(t, 1), "r1d": _r(f["r1d"], 1), "r1m": _r(f["r1m"], 1), "r6": _r(f["r6"], 0),
               "rsi": _r(f["rsi"], 0), "px": _r(f["price"], 3), "history_asof": f["asof"]}
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
                row.update({"st": "signal", "stl": "型態成立", "pat": h["pattern"], "patl": h["label"], "str": _r(min(100, h["strength"] + 5 * (len(hits) - 1)), 1),
                            "zlo": _r(pl["zone_lo"], 3), "zhi": _r(pl["zone_hi"], 3), "inv": _r(h["inv"], 3), "risk": _r(h["risk_pct"], 1),
                            "tgt": _r(pl.get("target"), 3), "tgtp": _r(pl.get("target_pct"), 0), "inz": bool(pl.get("in_zone")),
                            "why": pl.get("where", "")})
            elif pats is not None:
                df0 = next(iter(pats.values()))
                st = SG.status(df0)
                young = "（上市未滿一年：還沒有 200 日線，只檢查突破、收斂突破與超賣）" if df0["ma200"].isna().iloc[-1] else ""
                row.update({"st": st["status"], "stl": st["label"], "why": st["why"] + young, "when": SG.trigger_text(st["status"], df0)[0],
                            "str": _r(st["base"] + 0.25 * (t - 50), 1)})
                wp = SG.watch_plan(st["status"], df0)
                if wp:                                               # reference zone for adding (no signal yet)
                    row.update({"zlo": _r(wp["zone_lo"], 3), "zhi": _r(wp["zone_hi"], 3), "inv": _r(wp["inv"], 3),
                                "risk": _r(wp["risk_pct"], 1), "inz": bool(wp["in_zone"]), "zb": wp["basis_label"]})
            try:
                from . import patterns as PT
                tg_ = PT.tags(c, v)
                ex_ = PT.exhaustion(c, v)
                row["tg"] = "、".join(PT.TAGS[k][0] for k in tg_) or None
                row["ex"] = PT.exh_text(ex_) if ex_["n"] >= 2 else None
            except Exception:  # noqa: BLE001
                log.exception("full-market patterns %s", s)
        else:
            row.update({"st": "nodata", "stl": "資料不足", "why": "上市未滿約三個月，資料太少", "str": 0})
        if thin.get(s):                     # listed in full (11-21) but a 20-day average turnover this low makes patterns unreliable
            row["tg"] = "成交清淡" + ("、" + row["tg"] if row.get("tg") else "")
        row.update(labels(row))
        row.update(val_fields((zones or {}).get(it["code"] if mk == "tw" else s)))
        rows.append(row)
    vols = sorted(r["vol"] for r in rows if r.get("vol") is not None)       # volatility: thirds within this market
    if len(vols) >= 30:
        lo, hi = vols[len(vols) // 3], vols[2 * len(vols) // 3]
        for r in rows:
            if r.get("vol") is not None:
                r["lv"] = "低" if r["vol"] <= lo else "高" if r["vol"] > hi else "中"
    cfp = SG.pick_cfg()                                              # ★ 條件最齊全: top n per market among qualifying signals
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


def official_fill(close: pd.DataFrame, volume: pd.DataFrame, quotes: Dict, max_age_days: int = 7):
    """台股: the TWSE / TPEx official close and volume replace Yahoo's bar for that date (2026-11-21: Yahoo left 11/20
    empty for many names and gave intraday prices for others, so 1,477 rows were blanked as 技術資料待更新).
    Only recent dates; a symbol not in the price file is not added (it has no history to scan)."""
    if close.empty or not quotes:
        return close, volume, 0
    last = close.index[-1]
    close, volume = close.copy(), volume.copy()
    n = 0
    for sym, q in quotes.items():
        if sym not in close.columns or not q.get("asof") or not q.get("price"):
            continue
        d = pd.Timestamp(str(q["asof"])[:10])
        if (last - d).days > max_age_days:
            continue
        if d not in close.index:
            close.loc[d] = float("nan")
            close = close.sort_index()
        if d not in volume.index:
            volume.loc[d] = float("nan")
            volume = volume.sort_index()
        px = float(q["price"])
        if close.at[d, sym] != px:
            close.at[d, sym] = px
            n += 1
        if q.get("volume") is not None:
            if sym not in volume.columns:
                volume[sym] = float("nan")
            volume.at[d, sym] = float(q["volume"])
    return close, volume, n


async def run(eng, budget_s: Optional[float] = None) -> Dict[str, Dict]:
    """Refresh lists + prices within the time budget, then rescan every market that has data. Returns a status dict."""
    cf = FM.cfg()
    if not cf.get("enabled", True):
        return {}
    budget = float(budget_s if budget_s is not None else cf.get("budget_s", 420))
    t0 = time.time()
    lists = await FM.lists()
    share = cf.get("budget_share") or {"us": 0.35, "tw": 0.25, "hk": 0.2, "jp": 0.2}
    report: Dict[str, Dict] = {}
    for mk in [m for m in FM.MARKETS if m in (cf.get("markets") or FM.MARKETS)]:
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
        if mk == "tw" and not close.empty:
            try:
                from ..data import taiwan_quotes as TQ
                close, volume, nfill = official_fill(close, volume, TQ.cached()["quotes"])
                if nfill:
                    FM.save_prices(mk, close, volume)
                    st["official_fill"] = nfill
            except Exception:  # noqa: BLE001
                log.exception("full-market tw official fill failed")
        zones = {}
        if not close.empty and mk in ("tw", "us"):
            try:
                from ..data import valhist as VH
                last = close.ffill().iloc[-1].dropna()
                if mk == "tw":
                    st["val"] = await VH.refresh_tw(float(cf.get("val_budget_tw", 60)))
                    zones = VH.zones_tw({s.split(".")[0]: float(v) for s, v in last.items()})
                else:
                    st["val"] = await VH.refresh_us(list(last.index), float(cf.get("val_budget_us", 100)))
                    zones = VH.zones_us({s: float(v) for s, v in last.items()})
                st["val_n"] = len(zones)
            except Exception:  # noqa: BLE001
                log.exception("valuation history %s failed", mk)
        if not close.empty:
            try:
                res = await asyncio.to_thread(scan, mk, items, close, volume, b, zones)
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
        result = json.loads(_out(mk).read_text(encoding="utf-8")) if _out(mk).exists() else None
        if mk == "tw":
            from ..data import taiwan_quotes as TQ
            quotes = TQ.cached()["quotes"]
            if quotes:
                return TQ.overlay_published(result, quotes)
        return result
    except Exception:  # noqa: BLE001
        pass
    return None
