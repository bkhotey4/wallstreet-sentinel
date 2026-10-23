"""指數 vs 個股 — why the index can hold up while most stocks (and your account) fall.

Two lenses, all from data:
1. The gap: the index's distance from its 52-week high vs the MEDIAN stock's distance from its own high, the share of
   stocks ≥10 % / ≥20 % below their highs, the median 1-month / 3-month return vs the index, and (US) the equal-weight
   S&P 500 (RSP) vs the cap-weighted one (SPY).  A wide gap = a few heavyweights are carrying the index.
2. Dispersion and correlation: Cboe's 1-month implied correlation (COR1M, since 2006) and S&P 500 Dispersion Index
   (DSPX, since 2014) — downloaded from Cboe's public index history files — plus the realised cross-sectional spread of
   one-month returns across our stock list.  Low correlation + high dispersion = stocks moving on their own: which
   stocks you hold matters more than where the index goes.
Each number comes with its percentile in its own history; the reading rules are fixed thresholds stated on the page.
Descriptive only — not a forecast."""
from __future__ import annotations

import io
import json
import logging
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR

log = logging.getLogger(__name__)
CACHE = DATA_DIR / "econ_cboe_idx.json"          # econ_* is already in the site workflow's cache (no cache-key change)
CBOE = {"COR1M": "COR1M_History.csv", "COR3M": "COR3M_History.csv", "DSPX": "DSPX_History.csv"}
URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/"


def pctile(s: pd.Series, v: Optional[float] = None) -> Optional[float]:
    s = s.dropna()
    if len(s) < 60:
        return None
    v = float(s.iloc[-1]) if v is None else v
    return float((s < v).mean() * 100)


# ------------------------------------------------------------------ Cboe index history (public files)
def parse_cboe(text: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text))
    col = "CLOSE" if "CLOSE" in df.columns else df.columns[-1]
    s = pd.Series(pd.to_numeric(df[col], errors="coerce").values, index=pd.to_datetime(df["DATE"], format="%m/%d/%Y", errors="coerce"))
    return s[s.index.notna()].dropna().sort_index()


def load_cboe() -> Dict[str, pd.Series]:
    try:
        raw = json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return {k: pd.Series(v["v"], index=pd.to_datetime(v["d"])) for k, v in raw.get("series", {}).items()}


async def refresh_cboe(max_age_h: float = 6) -> Dict[str, pd.Series]:
    """Re-download the three history files at most every `max_age_h` hours; keep the cache on failure."""
    from ..data import http
    try:
        raw = json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        raw = {}
    if time.time() - float(raw.get("ts", 0)) < max_age_h * 3600:
        return load_cboe()
    out = dict(raw.get("series", {}))
    for k, fn in CBOE.items():
        try:
            txt = await http.get(URL + fn, kind="text", timeout=30, retries=1, headers={"User-Agent": "Mozilla/5.0"})
            s = parse_cboe(txt)
            if len(s) > 100:
                out[k] = {"d": [d.strftime("%Y-%m-%d") for d in s.index], "v": [round(float(x), 3) for x in s.values]}
        except Exception as e:  # noqa: BLE001
            log.warning("Cboe %s history failed: %s", k, e)
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ts": time.time(), "series": out}), encoding="utf-8")
    tmp.replace(CACHE)
    return load_cboe()


# ------------------------------------------------------------------ index vs the median stock
def gap(index: pd.Series, closes: Dict[str, pd.Series], window: int = 252) -> Optional[Dict]:
    index = index.dropna()
    cl = pd.DataFrame({s: c.dropna() for s, c in closes.items() if len(c.dropna()) > 60}).sort_index()
    if len(index) < window or cl.shape[1] < 15:
        return None
    cl = cl.reindex(index.index).ffill(limit=5)
    idx_dd = index / index.rolling(window, min_periods=60).max() - 1
    dd = cl / cl.rolling(window, min_periods=60).max() - 1
    med_dd = dd.median(axis=1)
    g = (med_dd - idx_dd).dropna()                                     # negative = stocks worse than the index
    r1, r3 = cl.pct_change(21, fill_method=None).iloc[-1], cl.pct_change(63, fill_method=None).iloc[-1]
    i1, i3 = float(index.pct_change(21).iloc[-1]), float(index.pct_change(63).iloc[-1])
    last = dd.iloc[-1].dropna()
    return {"asof": index.index[-1].strftime("%Y-%m-%d"), "n": int(len(last)),
            "index_dd": float(idx_dd.iloc[-1] * 100), "median_dd": float(med_dd.iloc[-1] * 100),
            "gap": float(g.iloc[-1] * 100) if len(g) else None, "gap_pct": pctile(-g) if len(g) else None,     # high = unusually wide
            "gap_since": g.index[0].strftime("%Y-%m-%d") if len(g) else None,
            "below10": float((last <= -0.10).mean() * 100), "below20": float((last <= -0.20).mean() * 100),
            "med_1m": float(r1.median() * 100), "med_3m": float(r3.median() * 100), "idx_1m": i1 * 100, "idx_3m": i3 * 100,
            "beat_1m": float((r1.dropna() > i1).mean() * 100), "beat_3m": float((r3.dropna() > i3).mean() * 100)}


def realized_dispersion(closes: Dict[str, pd.Series], days: int = 21) -> Optional[Dict]:
    cl = pd.DataFrame({s: c.dropna() for s, c in closes.items() if len(c.dropna()) > 60}).sort_index()
    if cl.shape[1] < 15:
        return None
    r = cl.pct_change(days, fill_method=None)
    disp = r.std(axis=1).dropna() * 100
    if len(disp) < 60:
        return None
    return {"now": float(disp.iloc[-1]), "pct": pctile(disp), "since": disp.index[0].strftime("%Y-%m-%d")}


def low_corr_after(cor: pd.Series, spx: pd.Series, thr: float = 5, h: int = 21) -> Optional[Dict]:
    """What followed days when COR1M sat in its lowest `thr` % (expanding percentile — no look-ahead):
    the change in correlation h days later, and how often the S&P fell ≥5 % at some point within h days, vs all days."""
    cor = cor.dropna()
    if len(cor) < 1000:
        return None
    pct = cor.expanding(min_periods=500).apply(lambda x: (x[:-1] < x[-1]).mean() * 100, raw=True)
    sp = spx.dropna().reindex(cor.index).ffill()
    dc = cor.shift(-h) - cor
    fm = sp[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1) / sp - 1
    ok = dc.notna() & fm.notna() & pct.notna()
    low = (pct <= thr) & ok
    if low.sum() < 60:
        return None
    d = cor.index[low]
    return {"days": int(low.sum()), "episodes": int(1 + sum((d[1:] - d[:-1]).days > h * 1.4)), "h": h,
            "dc_low": float(dc[low].median()), "dc_all": float(dc[ok].median()),
            "rise5_low": float((dc[low] > 5).mean() * 100), "rise5_all": float((dc[ok] > 5).mean() * 100),
            "dd5_low": float((fm[low] <= -0.05).mean() * 100), "dd5_all": float((fm[ok] <= -0.05).mean() * 100)}


# ------------------------------------------------------------------ reading rules
def readings(us: Optional[Dict], ew: Optional[Dict], cb: Dict[str, Dict], after: Optional[Dict] = None) -> List[Dict]:
    out = []
    if us and us.get("gap") is not None and us["gap"] <= -8 and (us.get("gap_pct") or 0) >= 80:
        out.append({"zh": f"指數被少數大型股撐住：標普離高點 {us['index_dd']:.1f}%，但中位數個股離自己的高點 {us['median_dd']:.1f}%，"
                          f"{us['below20']:.0f}% 的股票已經跌超過兩成——指數平靜不代表你的股票平靜。",
                    "en": "A few heavyweights are holding the index up while the median stock is well off its high."})
    if ew and ew.get("rel_3m") is not None and ew["rel_3m"] <= -3:
        out.append({"zh": f"等權重標普近 3 個月落後市值加權 {abs(ew['rel_3m']):.1f} 個百分點：漲幅集中在大型權值股。",
                    "en": "Equal-weight S&P has lagged the cap-weighted index — gains are concentrated."})
    c1, dx = cb.get("COR1M") or {}, cb.get("DSPX") or {}
    if (c1.get("pct") is not None and c1["pct"] <= 15) or (dx.get("pct") is not None and dx["pct"] >= 85):
        out.append({"zh": "個股各走各的（隱含相關性低、分散度高）：帳戶表現取決於你持有哪些股票和集中度，而不是大盤方向。"
                          "指數的波動被個股之間互相抵銷，但單一個股的波動很大。",
                    "en": "Stocks are moving on their own (low correlation, high dispersion): what you hold matters more than the index."})
    if c1.get("pct") is not None and c1["pct"] <= 5 and after:
        a = after
        out.append({"zh": f"隱含相關性在歷史最低的 5%。過去同樣情況（約 {a['episodes']} 段）之後 {a['h']} 個交易日："
                          f"相關性中位數變化 {a['dc_low']:+.1f} 點（平常 {a['dc_all']:+.1f}），回升超過 5 點的比例 {a['rise5_low']:.0f}%（平常 {a['rise5_all']:.0f}%）——"
                          + ("相關性傾向回升" if a['dc_low'] > a['dc_all'] else "相關性並沒有比平常更容易回升")
                          + f"；標普期間內跌超過 5% 的比例是 {a['dd5_low']:.0f}%（平常 {a['dd5_all']:.0f}%）"
                          + ("，明顯比較常大跌。" if a['dd5_low'] >= a['dd5_all'] * 1.5 else "，並沒有比較常大跌。"),
                    "en": f"Implied correlation in its lowest 5 %: afterwards correlation tended to rise ({a['dc_low']:+.1f} vs {a['dc_all']:+.1f}), "
                          f"but S&P 5 % drawdowns were not more frequent ({a['dd5_low']:.0f}% vs {a['dd5_all']:.0f}%)."})
    return out


def build(eng, cboe: Optional[Dict[str, pd.Series]] = None) -> Dict:
    from ..data.stocks import universe
    m, sp = getattr(eng, "market", None), getattr(eng, "stockprices", None)
    if m is None or sp is None:
        return {"available": False}
    uni = universe()
    out: Dict = {"available": True}
    for mk, ix in (("us", "^GSPC"), ("tw", "^TWII")):
        syms = list(((uni.get(mk) or {}).get("symbols") or {}).keys())
        closes = {s: sp.series(s) for s in syms}
        out[mk] = gap(m.series(ix), closes)
        out[mk + "_disp"] = realized_dispersion(closes)
    rsp, spy = m.series("RSP").dropna(), m.series("SPY").dropna()
    if len(rsp) > 300 and len(spy) > 300:
        j = pd.concat([rsp, spy], axis=1).dropna()
        rel3 = (j.iloc[:, 0].pct_change(63) - j.iloc[:, 1].pct_change(63)).dropna() * 100
        rel1 = (j.iloc[:, 0].pct_change(21) - j.iloc[:, 1].pct_change(21)).dropna() * 100
        out["ew"] = {"rel_1m": float(rel1.iloc[-1]), "rel_3m": float(rel3.iloc[-1]), "pct_3m": pctile(-rel3),
                     "since": rel3.index[0].strftime("%Y")}
    cb = {}
    for k, s in (cboe if cboe is not None else load_cboe()).items():
        if len(s) > 100:
            cb[k] = {"now": float(s.iloc[-1]), "asof": s.index[-1].strftime("%Y-%m-%d"), "pct": pctile(s),
                     "pct_3y": pctile(s[s.index >= s.index[-1] - pd.Timedelta(days=1095)]), "since": s.index[0].strftime("%Y")}
    out["cboe"] = cb
    src = cboe if cboe is not None else load_cboe()
    after = None
    if "COR1M" in src:
        try:
            after = low_corr_after(src["COR1M"], m.series("^GSPC"))
        except Exception:  # noqa: BLE001
            after = None
    out["after_low_corr"] = after
    out["readings"] = readings(out.get("us"), out.get("ew"), cb, after)
    return out
