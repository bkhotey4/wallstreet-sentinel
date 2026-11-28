"""總經全貌：九個面向一起看（2026-11-28）。

使用者：「做總經的情報整合，我怕你都蒐集單一資訊，沒辦法看到全貌」。本站有幾十張單點卡片，卻沒有一張把它們放在一起：
現在整體在哪個階段、哪幾個面向在轉壞、哪些訊號互相打架、這週和上週比哪裡變了。這裡只用網站已經有的數據（FRED、行情），
每個面向用一個月的變化判斷方向，規則固定、寫在程式裡，不是 AI 判讀。

方向的寫法統一是「對經濟與市場」：轉好＝壓力變小，轉壞＝壓力變大。"""
from __future__ import annotations

import json
import time
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR

FILE = DATA_DIR / "macro_map.json"


def _chg(s: pd.Series, days: int = 30, pct: bool = False) -> Optional[float]:
    s = s.dropna() if s is not None else pd.Series(dtype=float)
    if len(s) < 3:
        return None
    end = s.index[-1]
    base = s[s.index <= end - pd.Timedelta(days=days)]
    if base.empty or not base.iloc[-1]:
        return None
    a, b = float(base.iloc[-1]), float(s.iloc[-1])
    return (b / a - 1) * 100 if pct else b - a


def _last(s: pd.Series) -> Optional[float]:
    s = s.dropna() if s is not None else pd.Series(dtype=float)
    return float(s.iloc[-1]) if len(s) else None


def _score(*parts: Optional[float]) -> Optional[int]:
    """Pure: each part is +1 (worse), −1 (better) or 0; the pillar is the sign of the sum; None when nothing is known."""
    xs = [p for p in parts if p is not None]
    if not xs:
        return None
    t = sum(xs)
    return 1 if t > 0 else -1 if t < 0 else 0


def _mixed(*parts: Optional[int]) -> bool:
    """Pure: the pillar's signals point both ways (shown as 分歧, not as a calm 持平)."""
    xs = [x for x in parts if x]
    return any(x > 0 for x in xs) and any(x < 0 for x in xs)


def _st(*parts: Optional[int]) -> Dict:
    return {"state": _score(*parts), "mixed": _mixed(*parts)}


def _sgn(x: Optional[float], band: float, worse_if_up: bool = True) -> Optional[int]:
    if x is None:
        return None
    if abs(x) < band:
        return 0
    up = 1 if x > 0 else -1
    return up if worse_if_up else -up


def pillars(fred, market) -> List[Dict]:
    """[{key, zh, state (-1 better / 0 flat / 1 worse / None), facts: [str]}] from the engine's FRED and market data."""
    F = lambda sid: fred.get(sid) if hasattr(fred, "get") else pd.Series(dtype=float)        # noqa: E731
    M = lambda t: market.series(t) if hasattr(market, "series") else pd.Series(dtype=float)  # noqa: E731
    out = []

    # 1 成長：初領失業金 4 週均 vs 13 週均、薩姆衰退指標、零售銷售 3 個月
    icsa = F("ICSA").dropna()
    claims = None
    if len(icsa) >= 13:
        claims = (icsa.iloc[-4:].mean() / icsa.iloc[-13:].mean() - 1) * 100
    sahm = _last(F("SAHMREALTIME"))
    retail = _chg(F("RSAFS"), 92, pct=True)
    # 11-28 gap review: leading parts — permits (housing), core capital-goods orders (business investment), Philly Fed, real income
    permit = _chg(F("PERMIT"), 92, pct=True)
    capex = _chg(F("ANDENO"), 92, pct=True)
    philly = _last(F("GACDFSA066MSFRBPHI"))
    income = _chg(F("DSPIC96"), 92, pct=True)
    out.append({"key": "growth", "zh": "經濟成長與就業",
                **_st(_sgn(claims, 3.0), (1 if sahm is not None and sahm >= 0.5 else 0 if sahm is not None else None),
                      _sgn(retail, 0.5, worse_if_up=False), _sgn(permit, 3.0, worse_if_up=False), _sgn(capex, 1.5, worse_if_up=False),
                      (1 if philly is not None and philly < -10 else -1 if philly is not None and philly > 10 else 0 if philly is not None else None),
                      _sgn(income, 0.5, worse_if_up=False)),
                "facts": [f for f in (f"初領失業金近 4 週平均比近 13 週 {claims:+.1f}%" if claims is not None else "",
                                      f"薩姆衰退指標 {sahm:.2f}（0.5 以上歷史上多在衰退中）" if sahm is not None else "",
                                      f"零售銷售 3 個月 {retail:+.1f}%" if retail is not None else "",
                                      f"建築許可 3 個月 {permit:+.1f}%（房市領先）" if permit is not None else "",
                                      f"核心資本財訂單 3 個月 {capex:+.1f}%（企業投資）" if capex is not None else "",
                                      f"費城聯準會製造業 {philly:+.1f}（正＝擴張）" if philly is not None else "",
                                      f"實質可支配所得 3 個月 {income:+.1f}%" if income is not None else "") if f]})

    # 2 通膨：核心 CPI 3 個月年化 vs 12 個月、10 年通膨預期 1 個月、布蘭特 1 個月
    core = F("CPILFESL").dropna()
    c3 = c12 = None
    if len(core) >= 13:
        c3 = ((core.iloc[-1] / core.iloc[-4]) ** 4 - 1) * 100
        c12 = (core.iloc[-1] / core.iloc[-13] - 1) * 100
    be = _chg(F("T10YIE"))
    oil = _chg(M("BZ=F"), pct=True)
    mich = _last(F("MICH"))                     # households' 1-year expectations (11-28 gap review)
    mich_chg = _chg(F("MICH"), 92)
    eci = F("ECIWAG").dropna()
    eci_yoy = (eci.iloc[-1] / eci.iloc[-5] - 1) * 100 if len(eci) >= 5 else None
    eci_prev = (eci.iloc[-2] / eci.iloc[-6] - 1) * 100 if len(eci) >= 6 else None
    out.append({"key": "inflation", "zh": "通膨", "core_up": c3 is not None and c12 is not None and c3 - c12 >= 0.3,
                # core CPI counts twice: 11-28 oil −14% and breakevens −23 bp outvoted core re-accelerating (3.7% vs 2.9%)
                **_st(*([_sgn((c3 - c12) if c3 is not None and c12 is not None else None, 0.3)] * 2), _sgn(be, 0.1), _sgn(oil, 8.0),
                      _sgn(mich_chg, 0.3), _sgn((eci_yoy - eci_prev) if eci_yoy is not None and eci_prev is not None else None, 0.2)),
                "facts": [f for f in (f"核心 CPI 近 3 個月年化 {c3:.1f}%、近 12 個月 {c12:.1f}%" if c3 is not None else "",
                                      f"10 年通膨預期 1 個月 {be * 100:+.0f} 個基點" if be is not None else "",
                                      f"布蘭特原油 1 個月 {oil:+.1f}%" if oil is not None else "",
                                      f"家庭預期一年後通膨 {mich:.1f}%（3 個月 {mich_chg:+.1f} 個百分點）" if mich is not None and mich_chg is not None else "",
                                      f"雇用成本（薪資）年增 {eci_yoy:.1f}%" if eci_yoy is not None else "") if f]})

    # 3 利率與聯準會：2 年、10 年 1 個月變化
    y2, y10 = _chg(F("DGS2")), _chg(F("DGS10"))
    out.append({"key": "rates", "zh": "利率與聯準會",
                **_st(_sgn(y2, 0.15), _sgn(y10, 0.15)),
                "facts": [f for f in (f"2 年期殖利率 {(_last(F('DGS2')) or 0):.2f}%，1 個月 {y2 * 100:+.0f} 個基點" if y2 is not None else "",
                                      f"10 年期 {(_last(F('DGS10')) or 0):.2f}%，1 個月 {y10 * 100:+.0f} 個基點" if y10 is not None else "") if f]})

    # 4 金融條件與信用：芝加哥聯準會金融條件指數、高收益債利差、VIX
    nfci = _chg(F("NFCI"), 28)
    hy = _chg(F("BAMLH0A0HYM2"))
    vix = _last(M("^VIX"))
    out.append({"key": "credit", "zh": "金融條件與信用",
                **_st(_sgn(nfci, 0.05), _sgn(hy, 0.30), (1 if vix and vix >= 25 else -1 if vix and vix < 16 else 0 if vix else None)),
                "facts": [f for f in (f"芝加哥聯準會金融條件指數 4 週 {nfci:+.2f}（正＝變緊）" if nfci is not None else "",
                                      f"高收益債利差 1 個月 {hy * 100:+.0f} 個基點" if hy is not None else "",
                                      f"VIX {vix:.1f}" if vix else "") if f]})

    # 5 流動性：聯準會資產 − 財政部帳戶 − 逆回購（4 週變化）
    try:
        net = (F("WALCL").resample("W").last() - F("WTREGEN").resample("W").last() - F("RRPONTSYD").resample("W").last() * 1000).dropna()
        liq = (net.iloc[-1] / net.iloc[-5] - 1) * 100 if len(net) >= 5 else None
    except Exception:  # noqa: BLE001
        liq = None
    m2 = F("M2SL").dropna()
    m2_yoy = (m2.iloc[-1] / m2.iloc[-13] - 1) * 100 if len(m2) >= 13 else None
    out.append({"key": "liquidity", "zh": "市場上的錢（流動性）",
                **_st(_sgn(liq, 1.0, worse_if_up=False), (1 if m2_yoy is not None and m2_yoy < 0 else 0 if m2_yoy is not None else None)),
                "facts": [f for f in (f"聯準會資產扣掉財政部帳戶與逆回購，4 週 {liq:+.1f}%" if liq is not None else "",
                                      f"M2 貨幣供給年增 {m2_yoy:.1f}%" if m2_yoy is not None else "") if f]})

    # 6 美元與資金：美元指數、美元兌日圓、美元兌新台幣
    dxy, jpy, twd = _chg(M("DX-Y.NYB"), pct=True), _chg(M("JPY=X"), pct=True), _chg(M("TWD=X"), pct=True)
    out.append({"key": "dollar", "zh": "美元與跨國資金",
                **_st(_sgn(dxy, 1.5), _sgn(twd, 1.5), (1 if jpy is not None and jpy <= -4 else 0 if jpy is not None else None)),
                "facts": [f for f in (f"美元指數 1 個月 {dxy:+.1f}%" if dxy is not None else "",
                                      f"美元兌新台幣 {twd:+.1f}%（正＝台幣貶）" if twd is not None else "",
                                      f"美元兌日圓 {jpy:+.1f}%（大跌＝日圓急升，借日圓的錢會被迫平倉）" if jpy is not None else "") if f]})

    # 7 AI 投資循環：費半相對標普、輝達
    sox, spx, nv = _chg(M("^SOX"), pct=True), _chg(M("^GSPC"), pct=True), _chg(M("NVDA"), pct=True)
    rel = (sox - spx) if sox is not None and spx is not None else None
    out.append({"key": "ai", "zh": "AI 投資循環",
                **_st(_sgn(rel, 3.0, worse_if_up=False), _sgn(nv, 8.0, worse_if_up=False)),
                "facts": [f for f in (f"費城半導體 1 個月 {sox:+.1f}%、標普 500 {spx:+.1f}%" if sox is not None and spx is not None else "",
                                      f"輝達 1 個月 {nv:+.1f}%" if nv is not None else "") if f]})

    # 8 中國與原物料：恆生、人民幣、銅
    hsi, cny, cu = _chg(M("^HSI"), pct=True), _chg(M("CNY=X"), pct=True), _chg(M("HG=F"), pct=True)
    out.append({"key": "china", "zh": "中國與原物料",
                **_st(_sgn(hsi, 5.0, worse_if_up=False), _sgn(cny, 1.0), _sgn(cu, 6.0, worse_if_up=False)),
                "facts": [f for f in (f"恆生指數 1 個月 {hsi:+.1f}%" if hsi is not None else "",
                                      f"美元兌人民幣 {cny:+.1f}%" if cny is not None else "",
                                      f"銅 1 個月 {cu:+.1f}%" if cu is not None else "") if f]})

    # 9 台灣傳導：加權指數
    tw = _chg(M("^TWII"), pct=True)
    out.append({"key": "taiwan", "zh": "台灣（傳導終點）",
                **_st(_sgn(tw, 4.0, worse_if_up=False)),
                "facts": [f"加權指數 1 個月 {tw:+.1f}%" if tw is not None else ""]})
    for p in out:
        p["facts"] = [f for f in p["facts"] if f]
    return out





REGIME = {(1, -1): ("停滯性通膨的壓力", "成長轉弱、通膨卻在升：央行很難靠降息救經濟，股債常一起跌，是最難的組合。"),
          (1, 1): ("降溫", "成長和通膨一起轉弱：降息的空間變大，債券通常比股票撐得住；要小心的是降溫變成衰退。"),
          (-1, -1): ("過熱", "成長和通膨一起升：企業獲利好，但利率可能被推高，估值高的股票最怕。"),
          (-1, 1): ("金髮女孩", "成長好、通膨降：對股市最友善的組合；要看它能撐多久。")}


def regime(ps: List[Dict]) -> Optional[Dict]:
    """Pure: growth state × inflation state → one of four regimes (needs both to have a direction)."""
    g = next((p["state"] for p in ps if p["key"] == "growth"), None)
    i = next((p["state"] for p in ps if p["key"] == "inflation"), None)
    if not g or not i:
        return None
    name, why = REGIME[(g, -i)]          # growth worse (1) and inflation up (worse = 1 → -i = -1) → stagflation
    return {"name": name, "why": why}


def conflicts(ps: List[Dict]) -> List[str]:
    """Pure: pairs that point opposite ways — the places where one of the two markets is probably wrong."""
    s = {p["key"]: p["state"] for p in ps}
    out = []
    if s.get("taiwan") == -1 and s.get("credit") == 1:
        out.append("台股在漲，但信用與金融條件在變緊：股市和借錢給公司的人看法相反，過去多半是股市後來修正。")
    if s.get("ai") == -1 and s.get("rates") == 1:
        out.append("AI 股在漲，但利率也在升：高估值的成長股對利率最敏感，兩者很少能一起走太久。")
    if s.get("growth") == 1 and s.get("rates") == 1:
        out.append("經濟轉弱，利率卻在升：通常代表通膨或財政赤字在推利率，不是景氣好。")
    if s.get("dollar") == 1 and s.get("taiwan") == -1:
        out.append("美元轉強、新台幣轉弱，台股卻在漲：外資若持續把錢換回美元，這種漲勢容易缺乏後續買盤。")
    macro = [s.get(k) for k in ("growth", "inflation", "rates", "liquidity") if s.get(k) is not None]
    mkt = [s.get(k) for k in ("ai", "taiwan", "china", "credit") if s.get(k) is not None]
    if macro and mkt and sum(1 for x in macro if x == 1) <= 1 and sum(1 for x in mkt if x == 1) >= 3:
        # 11-28: claims, retail and yields fine, while SOX −21%, TAIEX −16%, copper −17% and HY spreads +59 bp
        out.insert(0, "經濟數據大致還好，但股市、AI 股、原物料或信用一起轉壞：要嘛市場在提前反應經濟轉弱（之後要看就業和消費會不會跟著變差），"
                      "要嘛是估值太高的修正、不是景氣問題。這兩種的後續很不一樣，接下來的就業與消費數據是分辨的關鍵。")
    if s.get("liquidity") == 1 and s.get("credit") == -1:
        out.append("市場上的錢在變少，但信用市場還很平靜：流動性通常比信用利差早反應。")
    return out


def build(fred, market, now: Optional[float] = None) -> Dict:
    now = now or time.time()
    ps = pillars(fred, market)
    known = [p for p in ps if p["state"] is not None]
    out = {"ts": now, "pillars": ps, "regime": regime(ps), "conflicts": conflicts(ps),
           "worse": [p["zh"] for p in known if p["state"] == 1], "better": [p["zh"] for p in known if p["state"] == -1]}
    try:                                   # weekly memory: which pillars flipped since the snapshot ≥ 6 days old
        hist = json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        hist = {}
    snaps = hist.get("snaps") or []
    prev = next((x for x in reversed(snaps) if now - x["ts"] >= 6 * 86400), None)
    if prev:
        out["flips"] = [{"zh": p["zh"], "from": prev["s"].get(p["key"]), "to": p["state"]} for p in ps
                        if p["state"] is not None and prev["s"].get(p["key"]) is not None and prev["s"][p["key"]] != p["state"]]
        out["prev_ts"] = prev["ts"]
    if not snaps or now - snaps[-1]["ts"] >= 86400:
        snaps.append({"ts": now, "s": {p["key"]: p["state"] for p in ps}})
    try:
        FILE.write_text(json.dumps({"snaps": snaps[-120:]}, ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return out
