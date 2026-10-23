"""私募信貸燈號 (rule lights for 金絲雀): redemption wave in the filings, listed-BDC discount to NAV, and the
insurers that hold private credit vs the S&P 500.  Each light is judged against its own history; the cut-offs are
percentiles from settings.yaml (private_credit).  Model data only — no headline enters any light."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from ..data import private_credit as PC

NAV_LAG_DAYS = 45            # a quarter's NAV is public ~45 days after the quarter ends (10-Q deadline): no look-ahead


def _pct(s: pd.Series, v: float) -> Optional[float]:
    s = s.dropna()
    return float((s < v).mean() * 100) if len(s) >= 12 else None


def _state(pct_hi: Optional[float], hot: float) -> str:
    """pct_hi: percentile where a higher value is worse."""
    if pct_hi is None:
        return "warmup"
    return "alert" if pct_hi >= 95 else "watch" if pct_hi >= hot else "ok"


def tender_light(data: Dict, c: Dict) -> Dict:
    row = {"id": "pc_tenders", "group": "私募信貸", "zh": "贖回潮（發行人收購要約申報件數）", "en": "Redemption wave (issuer tender-offer filings)",
           "kind": "rule",
           "why": "非上市 BDC 與區間基金只能用「發行人收購要約」讓投資人贖回。申報件數變多，代表想拿回錢的人變多，會比價格更早出現。",
           "rule": f"看最近 3 個完整月份提到 BDC 的收購要約件數合計，在自身歷史 3 個月合計中的百分位：≥ {c['hot_pct']:.0f} 黃燈、≥ 95 紅燈。"
                   "SEC 全文搜尋，所有發行人的件數一併列出供對照。"}
    t = data.get("tenders") or {}
    full = {k: v for k, v in t.items() if not v.get("partial")}
    if len(full) < 15:
        return {**row, "state": "na" if not t else "warmup", "note": "申報件數累積中" if t else "資料尚未下載"}
    key = "bdc" if all(v.get("bdc") is not None for v in full.values()) else "all"
    s = pd.Series({pd.Timestamp(k + "-01"): float(v[key]) for k, v in full.items()}).sort_index()
    r3 = s.rolling(3).sum().dropna()
    cur = float(r3.iloc[-1])
    pct = _pct(r3.iloc[:-1], cur)
    allm = pd.Series({k: float(v["all"]) for k, v in full.items()}).sort_index()
    yoy = (cur / float(r3.iloc[-13]) - 1) * 100 if len(r3) > 13 and r3.iloc[-13] > 0 else None
    return {**row, "state": _state(pct, float(c["hot_pct"])), "asof": s.index[-1].strftime("%Y-%m"),
            "value_txt": (f"近 3 個月提到 BDC 的收購要約 {cur:.0f} 件" if key == "bdc" else f"近 3 個月收購要約 {cur:.0f} 件")
                         + (f"（一年前同期 {yoy:+.0f}%）" if yoy is not None else "") + (f"，歷史第 {pct:.0f} 百分位" if pct is not None else "")
                         + f"；所有發行人上個月 {allm.iloc[-1]:.0f} 件",
            "history": [f"資料從 {s.index[0]:%Y-%m} 起，共 {len(s)} 個月；最多的 3 個月：" + "、".join(f"{d:%Y-%m} {v:.0f}" for d, v in s.nlargest(3).items())]}


def _discount_series(nav: List[List], px: pd.Series) -> pd.Series:
    """Daily price ÷ (latest NAV already public that day) − 1, in %."""
    if not nav or px is None or not len(px.dropna()):
        return pd.Series(dtype=float)
    n = pd.Series({pd.Timestamp(e) + pd.Timedelta(days=NAV_LAG_DAYS): v for e, v in nav}).sort_index()
    p = px.dropna()
    known = n.reindex(n.index.union(p.index)).ffill().reindex(p.index)
    return ((p / known - 1) * 100).dropna()


def discount_light(data: Dict, series_of, c: Dict) -> Dict:
    row = {"id": "pc_bdc_discount", "group": "私募信貸", "zh": "上市 BDC 股價對淨值折價", "en": "Listed BDCs: price vs NAV", "kind": "rule",
           "why": "BDC 的淨值是自己估的貸款價值，股價是市場給的價。折價越深，代表市場越不相信帳上的貸款價值。",
           "rule": f"看主要上市 BDC 的折價中位數（淨值用財報公布後才知道的那一季，不偷看未來）：落在自身歷史最深的 {100 - c['hot_pct']:.0f}% 黃燈、最深的 5% 紅燈；"
                   f"折價超過 {c['discount_pct']:.0f}% 也亮黃燈。"}
    navs = data.get("nav") or {}
    ds = {s: _discount_series((navs.get(s) or {}).get("nav") or [], series_of(s)) for s in c["bdcs"]}
    ds = {s: v for s, v in ds.items() if len(v) > 250}
    if len(ds) < 3:
        return {**row, "state": "na", "note": "淨值或股價不足（需要至少 3 家 BDC）"}
    df = pd.DataFrame(ds)
    med = df.median(axis=1, skipna=True)[df.notna().sum(axis=1) >= 3].dropna()
    cur = float(med.iloc[-1])
    pct_deep = _pct(-med, -cur)                                   # higher = deeper discount
    st = _state(pct_deep, float(c["hot_pct"]))
    if st == "ok" and cur <= -float(c["discount_pct"]):
        st = "watch"
    last = {s: float(v.iloc[-1]) for s, v in ds.items()}
    return {**row, "state": st, "asof": med.index[-1].strftime("%Y-%m-%d"),
            "value_txt": f"{len(ds)} 家折價中位數 {cur:+.1f}%" + (f"（比 {pct_deep:.0f}% 的歷史日子更深）" if pct_deep is not None else "")
                         + "；" + "、".join(f"{s} {v:+.0f}%" for s, v in sorted(last.items(), key=lambda x: x[1])),
            "history": [f"資料從 {med.index[0]:%Y-%m} 起；最深 {med.min():+.1f}%（{med.idxmin():%Y-%m}）"]}


def insurer_light(series_of, c: Dict) -> Dict:
    row = {"id": "pc_insurers", "group": "私募信貸", "zh": "持有私募信貸的保險／資管股 vs 標普", "en": "Private-credit insurers vs S&P", "kind": "rule",
           "why": "IMF 點名：保險公司與退休金持有更多不易變現的私募信貸。這些公司股價相對大盤走弱，常是市場開始擔心帳上資產。",
           "rule": f"等權重一籃（{'、'.join(c['insurers'])}）{c['rel_days']} 日報酬減標普 500：落在自身歷史最差的 {100 - c['hot_pct']:.0f}% 黃燈、最差的 5% 紅燈。"}
    n = int(c["rel_days"])
    px = {s: series_of(s) for s in c["insurers"]}
    px = {s: v for s, v in px.items() if v is not None and len(v.dropna()) > n + 250}
    spx = series_of("^GSPC")
    if len(px) < 2 or spx is None or len(spx.dropna()) < n + 250:
        return {**row, "state": "na", "note": "股價不足"}
    df = pd.DataFrame(px).dropna(how="all")
    basket = df.pct_change(n, fill_method=None).mean(axis=1, skipna=True) * 100
    rel = (basket - spx.dropna().pct_change(n, fill_method=None).reindex(basket.index) * 100).dropna()
    cur = float(rel.iloc[-1])
    pct_bad = _pct(-rel, -cur)
    return {**row, "state": _state(pct_bad, float(c["hot_pct"])), "asof": rel.index[-1].strftime("%Y-%m-%d"),
            "value_txt": f"{len(px)} 檔一籃 {n} 日相對標普 {cur:+.1f} 個百分點" + (f"（比 {pct_bad:.0f}% 的歷史日子更差）" if pct_bad is not None else ""),
            "history": [f"資料從 {rel.index[0]:%Y-%m} 起；最差 {rel.min():+.1f}（{rel.idxmin():%Y-%m}）"]}


def lights(eng, data: Optional[Dict] = None) -> List[Dict]:
    c = PC.cfg()
    data = data if data is not None else (getattr(eng, "private_credit", None) or PC.load())
    so = eng.market.series
    return [tender_light(data, c), discount_light(data, so, c), insurer_light(so, c)]
