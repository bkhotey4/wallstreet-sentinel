"""個股大動警報：網站追蹤名單裡的美股，今天漲或跌到「自己平常一天波動的好幾倍」，就發一則通知，並配對同時段的新聞標題。

為什麼要有：2026-11-13 思科（CSCO）跌 6.2%，是它平常一天的 3.7 倍，當時沒有任何通知，新聞牆也沒有對得上的標題
（每日缺口檢查 tools/gap_review.py 連兩天列出）。族群警報（sector_shock）只看 ETF，單一大公司自己出事不會響。

門檻（先用 stock_prices.pkl 的歷史收盤回放過，見 replay()；每天則數要在 3 則以內才推 Discord）：
  |z| ≥ Z_MIN 而且 |漲跌| ≥ PCT_MIN；|z| ≥ Z_RED 為紅燈。
  z＝今天漲跌 ÷ 平常一天的幅度；平常一天＝過去一年日漲跌的中位數絕對偏差 × 1.4826（和族群警報同一個算法）。
  同一天最多個別推 DAY_CAP 檔；超過時（通常是整體行情，族群警報已經會響）其餘合成一則只列名字，所以一天最多 DAY_CAP＋1 則。
  回放（2026-11-15，108 檔、近 60 個交易日）：32 天有觸發、共 100 檔次，最多的一天 22 檔；套上限後平均一天約 1 則、最多 4 則。
名單只用網站公開的美股與台股追蹤名單（台股門檻見 MK），不讀持股。新聞配對只代表「同時段有提到這家公司」，不等於就是原因；找不到就直說。
描述現況，不是預測，也不是投資建議。"""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from wsb.analytics.sector_shock import robust_sd

Z_MIN, Z_RED, PCT_MIN = 3.5, 5.0, 4.0
DAY_CAP = 3
# 每個市場自己的門檻（z 下限, 紅燈 z, 漲跌下限 %）。台股平常一天就動約 3%（漲跌停 10%），所以倍數放寬、幅度拉高：
# 回放（2026-11-16，台股追蹤名單 54 檔、近 60 個交易日）3.5×／4% 只抓到 39 次而且漏掉台達電 -9.3%（3.0 倍）；
# 3.0×／6% 共 47 次，套上限後平均一天約 0.8 則、最多 4 則。
MK = {"us": (Z_MIN, Z_RED, PCT_MIN), "tw": (3.0, 4.5, 6.0)}
NEWS_H = 18          # earnings come out after the close: the headline is often 12+ hours older than the move


def level(chg: Optional[float], sd: Optional[float], mk: str = "us") -> int:
    """0 = nothing, 1 = 🟠 (≥ z_min × normal and ≥ pct_min %), 2 = 🔴 (≥ z_red × normal).  Both directions."""
    if chg is None or not sd:
        return 0
    z_min, z_red, pct_min = MK.get(mk, MK["us"])
    z = abs(chg) / sd
    if abs(chg) < pct_min or z < z_min:
        return 0
    return 2 if z >= z_red else 1


def sigmas(cl: pd.DataFrame, syms: List[str]) -> Dict[str, float]:
    out = {}
    for s in syms:
        if s in getattr(cl, "columns", []):
            v = robust_sd(cl[s])
            if v:
                out[s] = v
    return out


def match_news(items: List[Dict], keys: List[str], now: float, hours: float = NEWS_H, k: int = 2) -> List[Dict]:
    """Headlines of the last `hours` that name the company (plain substring on the name-table keys)."""
    keys = [x for x in keys if x]
    hit = [x for x in items if 0 <= now - x.get("ts", 0) <= hours * 3600 and any(key in x.get("t", "") for key in keys)]
    return sorted(hit, key=lambda x: -x["ts"])[:k]


def check(quotes: Dict[str, Dict], sd: Dict[str, float], names: Dict[str, list], news: List[Dict], now: float,
          keys: Optional[Dict[str, List[str]]] = None, mk: str = "us") -> List[Dict]:
    """[{sym, zh, chg, z, lv, t, news, mk}] for tracked stocks moving unusually far, most unusual first."""
    out = []
    for sym, v in sd.items():
        x = quotes.get(sym) or {}
        chg = x.get("chg")
        if not isinstance(chg, (int, float)):
            continue
        lv = level(chg, v, mk)
        if not lv:
            continue
        zh = (names.get(sym) or [sym])[0] or sym
        out.append({"sym": sym, "zh": zh, "chg": float(chg), "z": float(chg) / v, "lv": lv, "t": x.get("t"),
                    "news": match_news(news, (keys or {}).get(sym) or [], now), "mk": mk})
    return sorted(out, key=lambda a: -abs(a["z"]))


def split(hits: List[Dict], cap: int = DAY_CAP) -> tuple:
    """(the `cap` most unusual, the rest): the rest are only named in one line, never pushed one by one."""
    return hits[:cap], hits[cap:]


def sentence(a: Dict, tz_hhmm) -> str:
    """One plain line: what moved, how unusual, and the same-hours headlines that name it (or that none were found)."""
    s = f'{a["zh"]}（{a["sym"]}）{a["chg"]:+.1f}%，是它平常一天的 {abs(a["z"]):.1f} 倍'
    hs = a.get("news") or []
    if hs:
        s += "。同時段提到它的新聞：" + "、".join(f'〈{h["t"][:70]}〉（{tz_hhmm(h["ts"])}）' for h in hs)
    else:
        s += "。找不到對得上的新聞，原因還不清楚"
    return s


def replay(cl: pd.DataFrame, syms: List[str], days: int = 60, z_min: float = Z_MIN, pct_min: float = PCT_MIN) -> Dict:
    """How often the rule would have fired on past closes: each day's σ uses only the year before that day."""
    per: Dict[str, List[str]] = {}
    for s in syms:
        if s not in getattr(cl, "columns", []):
            continue
        v = cl[s].dropna()
        v = v[v > 0]
        if len(v) < 130:
            continue
        r = v.pct_change() * 100
        for i in range(max(121, len(v) - days), len(v)):
            sd = robust_sd(v.iloc[:i])
            chg = float(r.iloc[i])
            if sd and abs(chg) >= pct_min and abs(chg) / sd >= z_min:
                per.setdefault(v.index[i].strftime("%Y-%m-%d"), []).append(s)
    n = [len(x) for x in per.values()]
    return {"days": days, "fired_days": len(per), "total": sum(n), "max_day": max(n) if n else 0,
            "over_cap_days": sum(1 for k in n if k > DAY_CAP), "per": per}
