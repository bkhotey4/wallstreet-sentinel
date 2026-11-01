"""盤中全面上漲 — the mirror of danger.py for the healthy direction (US and Taiwan, same trading day).

One index up a lot is not "risk-on".  Every move is measured against the asset's OWN normal daily move (one-year std of
daily % changes), never a fixed %, and scored by group: 股市, 市場寬度 (equal-weight / small caps, share of names up),
波動率 (VIX falling), 信用 (high-yield, regional banks), 匯率 (TWD strengthening = foreign inflow), 區域股市.
Breadth: US = the 11 sector ETFs (live quotes); Taiwan = every listed common stock in the official TWSE close file, which
exists only after the close — intraday the Taiwan gate needs 台積電 up >= 1 x its normal move instead.
  gate: the benchmark is up >= 1.5 x its own normal move and >= 70 % of names are up
  level 1 普遍上漲: the gate holds
  level 2 全面偏多: also >= 3 groups move together, at least one of them outside equities (volatility / credit / FX)
History: every past day the benchmark alone was up >= 1.5 x its normal move — the next 5 and 20 sessions' median return
and how often they were up, against all days.  Descriptive, not a forecast."""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from .danger import MARKETS as DMK

GATE = 1.5
BREADTH = 70.0
# (ticker, label, group, direction)  direction +1: rising is healthy, −1: falling is healthy
US = [("^GSPC", "標普500", "股市", 1), ("^NDX", "那斯達克100", "股市", 1), ("^SOX", "費城半導體", "股市", 1),
      ("RSP", "等權重標普", "市場寬度", 1), ("IWM", "小型股", "市場寬度", 1),
      ("^VIX", "VIX 恐慌指數", "波動率", -1), ("HYG", "高收益債", "信用", 1), ("KRE", "區域銀行", "信用", 1)]
TW = [("^TWII", "台灣加權", "股市", 1), ("2330.TW", "台積電", "股市", 1),
      ("TWD=X", "美元兌台幣", "匯率", -1), ("^N225", "日經225", "區域股市", 1), ("^KS11", "韓國KOSPI", "區域股市", 1)]
SECTORS = ("XLK", "XLC", "XLY", "XLP", "XLE", "XLV", "XLF", "XLI", "XLU", "XLB", "XLRE")
RULES = {"us": US, "tw": TW}
NAMES = {1: "普遍上漲", 2: "全面偏多"}
EQ = {"股市", "市場寬度", "區域股市"}


def day_of(mkt: str, q: Callable[[str], Optional[dict]], now: Optional[datetime] = None) -> Optional[str]:
    """Today's local date once the session has opened (so the closing read stays up until midnight), if today's bar exists."""
    m = DMK[mkt]
    loc = (now or datetime.now(ZoneInfo("UTC"))).astimezone(ZoneInfo(m["tz"]))
    if loc.weekday() >= 5 or loc.time() < m["open"]:
        return None
    today = loc.strftime("%Y-%m-%d")
    return today if (q(m["anchor"]) or {}).get("asof") == today else None


def normal_sd(h: pd.Series) -> Optional[float]:
    h = h.dropna()
    r = h[h > 0].pct_change().dropna().iloc[-253:-1] * 100
    return float(r.std()) if len(r) > 120 and r.std() > 0 else None


def breadth(mkt: str, q: Callable[[str], Optional[dict]], day: Optional[str], tw_close: Optional[Dict] = None) -> Optional[Dict]:
    """Share of names up today: US sector ETFs, Taiwan listed common stocks (official close file, only once published)."""
    if mkt == "us":
        xs = [(q(t) or {}) for t in SECTORS]
        xs = [x["chg_pct"] for x in xs if x.get("chg_pct") is not None and (not day or str(x.get("asof", ""))[:10] >= day)]
        lab, need = "類股", 8
    else:
        xs = [x["chg_pct"] for s, x in (tw_close or {}).items()
              if s.endswith(".TW") and len(s) == 7 and s[:4].isdigit() and not s.startswith("0")
              and x.get("asof") == day and x.get("chg_pct") is not None]
        lab, need = "上市股票", 300
    if len(xs) < need:
        return None
    return {"up": int(sum(c > 0 for c in xs)), "n": len(xs), "share": sum(c > 0 for c in xs) / len(xs) * 100, "label": lab}


def score(mkt: str, q: Callable[[str], Optional[dict]], series: Callable[[str], pd.Series], day: Optional[str] = None,
          tw_close: Optional[Dict] = None) -> Dict:
    hits, groups, bench = [], {}, None
    for t, label, grp, d in RULES[mkt]:
        x = q(t) or {}
        c = x.get("chg_pct")
        if c is None or c != c or (day and str(x.get("asof", ""))[:10] < day):
            continue
        sd = normal_sd(series(t))
        if not sd:
            continue
        z = d * float(c) / sd
        if t == DMK[mkt]["anchor"]:
            bench = {"chg": float(c), "sd": sd, "z": z}
        p = 2 if z >= 2 else 1 if z >= 1 else 0
        if p:
            groups[grp] = groups.get(grp, 0) + p
            hits.append({"ticker": t, "label": label, "group": grp, "chg": float(c), "z": z, "pts": p})
    br = breadth(mkt, q, day, tw_close)
    if br and br["share"] >= BREADTH:
        groups["市場寬度"] = groups.get("市場寬度", 0) + 1
    if br:
        wide = br["share"] >= BREADTH
    elif mkt == "tw":                                   # intraday: no per-stock quotes yet → 台積電 must join in
        wide = any(h["ticker"] == "2330.TW" and h["z"] >= 1 for h in hits)
    else:
        wide = False
    lvl = 0
    if bench and bench["z"] >= GATE and wide:
        non_eq = [k for k in groups if k not in EQ]
        lvl = 2 if len(groups) >= 3 and non_eq else 1
    return {"market": mkt, "zh": DMK[mkt]["zh"], "level": lvl, "name": NAMES.get(lvl, "—"), "bench": bench,
            "breadth": br, "groups": groups, "hits": sorted(hits, key=lambda h: -h["z"]),
            "non_eq": [k for k in groups if k not in EQ]}


def history(h: pd.Series, gate: float = GATE) -> Optional[Dict]:
    """Past days the benchmark was up >= gate x its own trailing one-year move: what the next 5 / 20 sessions did."""
    h = h.dropna()
    h = h[h > 0]
    if len(h) < 600:
        return None
    r = h.pct_change() * 100
    sd = r.rolling(252, min_periods=150).std().shift(1)
    big = (r / sd >= gate).fillna(False)
    out: Dict = {"n": int(big.iloc[:-1].sum()), "from": str(h.index[0].date())[:4]}
    for k in (5, 20):
        fw = (h.shift(-k) / h - 1) * 100
        e, a = fw[big].dropna(), fw.dropna()
        if len(e) < 20:
            return None
        out[k] = {"med": float(e.median()), "up": float((e > 0).mean() * 100), "all_med": float(a.median()), "all_up": float((a > 0).mean() * 100)}
    return out


def detail(r: Dict, hist: Optional[Dict]) -> str:
    b = r["bench"]
    br = r.get("breadth")
    s = f"{r['zh']}大盤 {b['chg']:+.2f}%（平常單日 ±{b['sd']:.1f}%，約 {b['z']:.1f} 倍）；"
    s += (f"{br['label']} {br['up']}/{br['n']} 上漲（{br['share']:.0f}%）。" if br else "個股漲跌家數收盤後才有，盤中先看台積電是否同步。")
    other = [h for h in r["hits"] if h["ticker"] != DMK[r["market"]]["anchor"]][:5]
    if other:
        s += "同步：" + "、".join(f"{h['label']} {h['chg']:+.2f}%" for h in other) + "。"
    s += ("股市以外（" + "、".join(r["non_eq"]) + "）也同方向，是比較全面的偏多。" if r["level"] >= 2
          else "目前只在股市，波動率、信用或匯率還沒有一起確認。")
    if hist:
        h5, h20 = hist[5], hist[20]
        s += (f"過去 {hist['from']} 年起這樣的大漲日共 {hist['n']} 天：之後 5 天中位數 {h5['med']:+.1f}%（上漲比例 {h5['up']:.0f}%，"
              f"所有日子 {h5['all_up']:.0f}%）、20 天 {h20['med']:+.1f}%（{h20['up']:.0f}%，所有日子 {h20['all_up']:.0f}%）。")
        s += ("大漲之後並沒有比平常更容易續漲。" if h20["up"] <= h20["all_up"] + 5 else "之後上漲比例比平常高一些，但仍常有回檔。")
    return s + "大漲常伴隨空單回補；免費報價約延遲 15 分鐘。描述現象，不是預測，也不是買賣建議。"


_HIST: Dict = {}


def hist_cached(t: str, h: pd.Series) -> Optional[Dict]:
    key = (t, len(h), str(h.index[-1]) if len(h) else "")
    if _HIST.get(t, (None,))[0] != key:
        _HIST[t] = (key, history(h))
    return _HIST[t][1]


def _tw_close() -> Dict:
    try:
        from ..data import taiwan_quotes as TQ
        return TQ.cached().get("quotes") or {}
    except Exception:  # noqa: BLE001
        return {}


def scan(eng, now: Optional[datetime] = None, tw_close: Optional[Dict] = None) -> List[Dict]:
    q, ser = eng.market.q, eng.market.series
    out = []
    for mkt in ("us", "tw"):
        day = day_of(mkt, q, now)
        if not day:
            continue
        r = score(mkt, q, ser, day, (tw_close if tw_close is not None else _tw_close()) if mkt == "tw" else None)
        if r["level"]:
            a = DMK[mkt]["anchor"]
            r["day"], r["hist"] = day, hist_cached(a, ser(a))
            out.append(r)
    return out
