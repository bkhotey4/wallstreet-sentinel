"""ETF 資金流向: estimated net flow from issuer shares outstanding × NAV, judged against each fund's own history.

A flow is compared as a share of the fund's assets, so a fund that has grown tenfold is not always "historic".  Sums run
over business days; a stored-data gap that crosses the window start gives no sum rather than a sum of the wrong length."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

import numpy as np

from ..data import etf_flows as DF

MIN_BASE = 60                                            # past windows needed before a σ means anything
BASE_MAX = 750                                           # about three years, so old regimes fade out
STALE_BD = 4                                             # business days without a new date → out of the reading
BIG_Z = 2.0
SPLIT_RATIO = 1.4                                        # shares × this with NAV ÷ this: a split, not a flow


def flows(rows: List) -> List[Dict]:
    out = []
    for (d0, s0, n0), (d1, s1, n1) in zip(rows, rows[1:]):
        hi, lo = max(s1, s0) / min(s1, s0), max(n1, n0) / min(n1, n0)
        if hi >= SPLIT_RATIO and lo >= SPLIT_RATIO and (s1 > s0) == (n1 < n0):
            continue
        amt = (s1 - s0) * n1
        out.append({"date": d1, "prev": d0, "amt": amt, "pct": amt / (s0 * n1) * 100, "span": int(np.busday_count(d0, d1))})
    return out


def _window(fl: List[Dict], n: int) -> Optional[List[Dict]]:
    """The intervals covering the last n business days, or None if history is short or a gap crosses the start."""
    if not fl:
        return None
    cut = str(np.busday_offset(fl[-1]["date"], -n, roll="backward"))
    rows = [x for x in fl if x["date"] > cut]
    if not rows or rows[0]["prev"] > cut or np.busday_count(rows[0]["prev"], cut) > 1:
        return None
    return rows


def _z(fl: List[Dict], n: int, cur: float) -> Optional[float]:
    """Current window against past windows of the same length that do not overlap it."""
    ok = fl[:-n][-BASE_MAX:]
    if len(ok) < n:
        return None
    pct = np.array([x["pct"] for x in ok])
    span = np.array([x["span"] for x in ok])
    if n == 1:
        base = pct[span <= 2]
    else:
        c, s = np.convolve(pct, np.ones(n), "valid"), np.convolve(span, np.ones(n), "valid")
        base = c[s <= n + 2]
    if len(base) < MIN_BASE:
        return None
    sd = float(base.std(ddof=1))
    return (cur - float(base.mean())) / sd if sd > 0 else None


def view(f: Dict, rec: Dict, today: date) -> Optional[Dict]:
    rows = (rec or {}).get("rows") or []
    if not rows:
        return None
    fl = flows(rows)
    v = {**f, "asof": rows[-1][0], "aum": rows[-1][1] * rows[-1][2], "n_days": len(rows), "failed": bool(rec.get("err")),
         "age": int(np.busday_count(rows[-1][0], today.isoformat()))}
    v["stale"] = v["age"] > STALE_BD
    for key, n in (("d1", 1), ("d5", 5), ("d20", 20)):
        w = _window(fl, n)
        v[key] = {"amt": sum(x["amt"] for x in w) if w else None, "z": _z(fl, n, sum(x["pct"] for x in w)) if w else None,
                  "need": max(n + 1 - len(rows), 1), "need_z": max(MIN_BASE + 2 * n - 1 - len(fl), 1)}
    return v


def _yi(x: float) -> str:
    return f"{abs(x) / 1e8:,.1f} 億美元"


def _credit(hy: Optional[float], tl: Optional[float], ig: Optional[float]) -> str:
    if hy is None or tl is None:
        return ""
    if hy < 0 < tl:
        s = f"近 5 個交易日，高收益債（垃圾債）ETF 流出 {_yi(hy)}，長天期美債 ETF 流入 {_yi(tl)}：錢從風險較高的債券移向公債，投資人變得比較保守"
    elif tl < 0 < hy:
        s = f"近 5 個交易日，長天期美債 ETF 流出 {_yi(tl)}，高收益債（垃圾債）ETF 流入 {_yi(hy)}：投資人比較願意承擔公司違約的風險"
    elif hy > 0 and tl > 0:
        s = f"近 5 個交易日，高收益債 ETF（{_yi(hy)}）和長天期美債 ETF（{_yi(tl)}）都有錢流入，債券這邊沒有明顯的避險搬家"
    elif hy < 0 and tl < 0:
        s = f"近 5 個交易日，高收益債 ETF（{_yi(hy)}）和長天期美債 ETF（{_yi(tl)}）都有錢流出，資金同時離開這兩種債券"
    else:
        return ""
    if ig is not None and hy < 0 < ig:
        s += "；投資級公司債 ETF 同時流入，錢在往體質較好的公司移動"
    return s + "。"


def reading(vs: List[Dict]) -> str:
    """One plain sentence from what is really available; a fund without a current 5-day sum is simply not mentioned."""
    live = {v["sym"]: v for v in vs if not v["stale"]}
    s5 = {k: v["d5"]["amt"] for k, v in live.items() if v["d5"]["amt"] is not None}
    parts = []
    bond = _credit(s5.get("HYG"), s5.get("TLT"), s5.get("LQD"))
    if bond:
        parts.append(bond)
    eq = [k for k in ("SPY", "QQQ") if k in s5]
    if eq:
        tot = sum(s5[k] for k in eq)
        parts.append(f"{'＋'.join(eq)} 近 5 個交易日合計淨{'流入' if tot >= 0 else '流出'} {_yi(tot)}。")
    if not parts:
        d1 = [v for v in live.values() if v["d1"]["amt"] is not None]
        if not d1:
            return "資料累積中：要有連續兩天的官方份額，才算得出第一筆資金流向。"
        top = max(d1, key=lambda v: abs(v["d1"]["amt"]))
        word = "流入" if top["d1"]["amt"] >= 0 else "流出"
        parts.append(f'{top["sym"]}（{top["zh"]}）最新一日淨{word} {_yi(top["d1"]["amt"])}。')
    big = [v for v in live.values() if v["d5"]["z"] is not None and abs(v["d5"]["z"]) >= BIG_Z]
    if big:
        parts.append("其中 " + "、".join(f'{v["sym"]}（{v["d5"]["z"]:+.1f}σ）' for v in big) + " 比自己平常的規模大很多。")
    if not bond:
        parts.append("債券 ETF 的資料還在累積。")
    elif any(live[k]["d5"]["z"] is None for k in s5):
        parts.append("部分基金的歷史還不夠長，規模算不算大要等資料累積。")
    return "".join(parts)


def build(d: Optional[Dict] = None, today: Optional[date] = None) -> Dict:
    d = DF.load() if d is None else d
    today = today or date.today()
    recs = d.get("funds") or {}
    vs, missing = [], []
    for f in DF.FUNDS:
        v = view(f, recs.get(f["sym"]) or {}, today)
        if v:
            vs.append(v)
        else:
            missing.append(f)
    return {"funds": vs, "missing": missing, "lead": reading(vs)}
