"""總經全貌：各面向一起看（2026-11-28）。

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


def pillars(fred, market, extras: Optional[Dict] = None) -> List[Dict]:
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
    out.append({"key": "inflation", "zh": "通膨", "core_up": bool(c3 is not None and c12 is not None and c3 - c12 >= 0.3),
                # core CPI counts twice: 11-28 oil −14% and breakevens −23 bp outvoted core re-accelerating (3.7% vs 2.9%)
                **_st(*([_sgn((c3 - c12) if c3 is not None and c12 is not None else None, 0.3)] * 2), _sgn(be, 0.1), _sgn(oil, 8.0),
                      _sgn(mich_chg, 0.3), _sgn((eci_yoy - eci_prev) if eci_yoy is not None and eci_prev is not None else None, 0.2)),
                "facts": [f for f in (f"核心 CPI 近 3 個月年化 {c3:.1f}%、近 12 個月 {c12:.1f}%" if c3 is not None else "",
                                      f"10 年通膨預期 1 個月 {be * 100:+.0f} 個基點" if be is not None else "",
                                      f"布蘭特原油 1 個月 {oil:+.1f}%" if oil is not None else "",
                                      f"家庭預期一年後通膨 {mich:.1f}%（3 個月 {mich_chg:+.1f} 個百分點）" if mich is not None and mich_chg is not None else "",
                                      f"雇用成本（薪資）年增 {eci_yoy:.1f}%" if eci_yoy is not None else "") if f]})

    # 3 利率與聯準會：2 年、10 年 1 個月變化＋期貨市場押的聯準會路徑（11-28：市場押 12 月升息約九成，卡上原本沒寫）
    y2, y10 = _chg(F("DGS2")), _chg(F("DGS10"))
    fw = (extras or {}).get("fedwatch") or {}
    path = fed_path(fw)
    out.append({"key": "rates", "zh": "利率與聯準會", "hike_next": path.get("p_hike"), "cum_bp": path.get("cum_bp"),
                **_st(_sgn(y2, 0.15), _sgn(y10, 0.15), _sgn(path.get("wk_shift"), 5.0)),
                "facts": [f for f in (f"2 年期殖利率 {(_last(F('DGS2')) or 0):.2f}%，1 個月 {y2 * 100:+.0f} 個基點" if y2 is not None else "",
                                      f"10 年期 {(_last(F('DGS10')) or 0):.2f}%，1 個月 {y10 * 100:+.0f} 個基點" if y10 is not None else "",
                                      path.get("text", "")) if f]})

    # 3b 美債供需與定價（11-28：使用者「你有思考過美債嗎」— 10 年期下降 15 個基點，拆開是通膨預期 −23、實質利率 +7；
    #    外國央行託管三個月 −717 億、聯準會持有 +468 億。只看名目殖利率會以為借錢變便宜）
    real, be10, tp = _chg(F("DFII10")), _chg(F("T10YIE")), _chg(F("THREEFYTP10"))
    y30 = _chg(F("DGS30"))
    cust = F("WMTSECL1").dropna()
    cust_chg = (cust.iloc[-1] / cust.iloc[-14] - 1) * 100 if len(cust) >= 14 else None
    fedt = F("TREAST").dropna()
    fed_chg = (fedt.iloc[-1] - fedt.iloc[-14]) / 1000 if len(fedt) >= 14 else None   # $ billions over ~13 weeks
    curve = curve_regime(y2, y10)
    # 11-28 desk pass: bond-market fear (MOVE) and how the last month's coupon auctions went (bid-to-cover and dealer share
    # against the same tenor's own recent auctions, wsb.data.treasury.judge)
    move = _last(M("^MOVE"))
    at = (extras or {}).get("auctions") or {}
    out.append({"key": "treasury", "zh": "美債供需與定價", "curve": curve, "auct_weak": at.get("weak"),
                **_st(_sgn(real, 0.10), _sgn(tp, 0.15), (1 if curve == "熊市變陡" else -1 if curve == "牛市變平" else 0 if curve else None),
                      _sgn(cust_chg, 2.0, worse_if_up=False),
                      (1 if move is not None and move >= 125 else -1 if move is not None and move < 80 else 0 if move is not None else None),
                      (1 if at.get("weak", 0) >= 2 else -1 if at.get("strong", 0) >= 2 and not at.get("weak") else 0) if at.get("n") else None),
                "facts": [f for f in ((f"10 年期 1 個月 {y10 * 100:+.0f} 個基點＝實質利率 {real * 100:+.0f}＋通膨預期 {be10 * 100:+.0f}"
                                       if y10 is not None and real is not None and be10 is not None else ""),
                                      f"期限溢價 1 個月 {tp * 100:+.0f} 個基點" if tp is not None else "",
                                      f"殖利率曲線：{curve}（2 年 {y2 * 100:+.0f}、10 年 {y10 * 100:+.0f}、30 年 {y30 * 100:+.0f} 個基點）"
                                      if curve and y30 is not None else "",
                                      f"外國央行託管美債 13 週 {cust_chg:+.1f}%" if cust_chg is not None else "",
                                      (f"聯準會持有美債 13 週 {fed_chg * 10:+,.0f} 億美元" if fed_chg is not None else ""),
                                      f"MOVE 美債波動率 {move:.0f}（125 以上＝債市恐慌，80 以下＝很平靜）" if move is not None else "",
                                      (f"近 5 週 {at['n']} 場中長期公債標售：偏弱 {at['weak']}、偏強 {at['strong']}、其餘正常"
                                       f"（和同天期前 6 場比得標倍數與交易商被迫吃下的比例）" if at.get("n") else "")) if f]})

    # 3c 市場在押什麼：交易台每天看的跨資產比值（11-28 使用者：「用華爾街的金融視角」）。比值 1 個月的變化，
    #    往下＝市場在避險或押景氣轉弱。這一欄看的是「價格怎麼定」，和上面的「數據怎麼說」對照，落差就是情報。
    def ratio(a: str, b: str) -> Optional[float]:
        sa, sb = M(a).dropna(), M(b).dropna()
        if sa.empty or sb.empty:
            return None
        r = (sa / sb).dropna()
        return _chg(r, pct=True)
    cg, sm, cy, ew, bk, em = (ratio("HG=F", "GC=F"), ratio("IWM", "SPY"), ratio("XLY", "XLP"), ratio("RSP", "SPY"),
                              ratio("KRE", "SPY"), ratio("EEM", "SPY"))
    btc = _chg(M("BTC-USD"), pct=True)
    out.append({"key": "pricing", "zh": "市場在押什麼（跨資產）",
                **_st(_sgn(cg, 4.0, worse_if_up=False), _sgn(sm, 2.0, worse_if_up=False), _sgn(cy, 2.0, worse_if_up=False),
                      _sgn(bk, 3.0, worse_if_up=False), _sgn(em, 3.0, worse_if_up=False), _sgn(btc, 15.0, worse_if_up=False)),
                "cg": cg, "cy": cy, "ew": ew,
                "facts": [f for f in (f"銅金比 1 個月 {cg:+.1f}%（往下＝押景氣轉弱、買避險）" if cg is not None else "",
                                      f"小型股對大型股 {sm:+.1f}%（往下＝不敢承擔風險）" if sm is not None else "",
                                      f"非必需消費對必需消費 {cy:+.1f}%（往下＝押消費轉弱）" if cy is not None else "",
                                      f"等權重對市值加權 {ew:+.1f}%（往上＝漲勢擴散到更多股票）" if ew is not None else "",
                                      f"區域銀行對大盤 {bk:+.1f}%（往下＝擔心放款與信用）" if bk is not None else "",
                                      f"新興市場對美股 {em:+.1f}%" if em is not None else "",
                                      f"比特幣 1 個月 {btc:+.1f}%（常被當成資金鬆緊的溫度計）" if btc is not None else "") if f]})

    extras = extras or {}
    # 3d 企業獲利預期：分析師 EPS 預估 30 天往上修與往下修的家數差（華爾街看盈餘修正廣度，比股價早反映基本面）
    er = ((extras.get("estrev") or {}).get("h") or {}).get(30) or {}
    net = er.get("net")
    out.append({"key": "earnings", "zh": "企業獲利預期",
                **_st(_sgn(net, 10.0, worse_if_up=False) if net is not None else None),
                "facts": [f for f in ((f"分析師 30 天內上修 {er['up_pct']:.0f}%、下修 {er['dn_pct']:.0f}% 的公司（{er['n']} 家），{'淨上修' if net >= 0 else '淨下修'} {abs(net):.0f} 個百分點"
                                       if net is not None else ""),
                                      ({"up": "這週修正速度比過去一個月快（更樂觀）", "down": "這週下修速度加快", "steady": "這週修正速度和過去一個月差不多"}
                                       .get((extras.get("estrev") or {}).get("speed") or "", ""))) if f]})

    # 3e 部位與脆弱度：借錢買股的擁擠程度、VIX 期限結構、尾部避險需求
    mg = extras.get("margin_yoy")
    v1, v3, sk = _last(M("^VIX")), _last(M("^VIX3M")), _last(M("^SKEW"))
    term = (v1 / v3) if v1 and v3 else None
    out.append({"key": "positioning", "zh": "部位與脆弱度",
                **_st((1 if mg is not None and mg >= 30 else -1 if mg is not None and mg < 0 else 0 if mg is not None else None),
                      (1 if term is not None and term >= 1.0 else 0 if term is not None else None),
                      (1 if sk is not None and sk >= 150 else 0 if sk is not None else None)),
                "facts": [f for f in (f"融資餘額年增 {mg:+.0f}%（30% 以上＝借錢買股很擁擠，跌時被迫賣）" if mg is not None else "",
                                      f"近月 VIX 對三個月 VIX {term:.2f}（1 以上＝短期恐慌高過長期）" if term is not None else "",
                                      f"SKEW {sk:.0f}（150 以上＝大家在買崩盤保險）" if sk is not None else "") if f]})

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
    sofr, iorb = _last(F("SOFR")), _last(F("IORB"))
    spread = (sofr - iorb) * 100 if sofr is not None and iorb is not None else None     # bp; > 0 = repo above the Fed's floor rate
    res = F("WRESBAL").dropna()
    res_chg = (res.iloc[-1] / res.iloc[-5] - 1) * 100 if len(res) >= 5 else None
    m2 = F("M2SL").dropna()
    m2_yoy = (m2.iloc[-1] / m2.iloc[-13] - 1) * 100 if len(m2) >= 13 else None
    out.append({"key": "liquidity", "zh": "市場上的錢（流動性）",
                **_st(_sgn(liq, 1.0, worse_if_up=False), (1 if m2_yoy is not None and m2_yoy < 0 else 0 if m2_yoy is not None else None),
                      (1 if spread is not None and spread >= 3 else -1 if spread is not None and spread <= -8 else 0 if spread is not None else None)),
                "facts": [f for f in (f"聯準會資產扣掉財政部帳戶與逆回購，4 週 {liq:+.1f}%" if liq is not None else "",
                                      f"M2 貨幣供給年增 {m2_yoy:.1f}%" if m2_yoy is not None else "",
                                      (f"SOFR 比準備金利率 {spread:+.0f} 個基點（正＝短期資金開始緊，2019 年 9 月回購市場出事前也是這樣）"
                                       if spread is not None else ""),
                                      f"銀行準備金 4 週 {res_chg:+.1f}%" if res_chg is not None else "") if f]})

    # 6 美元與資金：美元指數、美元兌日圓、美元兌新台幣
    dxy, jpy, twd = _chg(M("DX-Y.NYB"), pct=True), _chg(M("JPY=X"), pct=True), _chg(M("TWD=X"), pct=True)
    out.append({"key": "dollar", "zh": "美元與跨國資金",
                **_st(_sgn(dxy, 1.5), _sgn(twd, 1.5), (1 if jpy is not None and jpy <= -4 else 0 if jpy is not None else None)),
                "facts": [f for f in (f"美元指數 1 個月 {dxy:+.1f}%" if dxy is not None else "",
                                      f"美元兌新台幣 {twd:+.1f}%（正＝台幣貶）" if twd is not None else "",
                                      f"美元兌日圓 {jpy:+.1f}%（大跌＝日圓急升，借日圓的錢會被迫平倉）" if jpy is not None else "") if f]})

    # 6b 海外利率（11-28 desk pass）：日本公債（財務省，日資料）與歐元區金融壓力指數 CISS（歐洲央行）。日本是美債最大的外國持有者，
    #    日本長期利率升、美日利差縮，日本資金比較想留在國內，借日圓買海外資產的部位也可能被迫平倉（2024-08-05 就是這樣）。
    jp = (extras or {}).get("jgb") or {}
    j10, j30 = _chg(jp.get("10Y")), _chg(jp.get("30Y"))
    spread = None
    us10, jp10 = F("DGS10").dropna(), (jp.get("10Y") if jp.get("10Y") is not None else pd.Series(dtype=float)).dropna()
    if len(us10) and len(jp10):
        diff = (us10 - jp10.reindex(us10.index).ffill()).dropna()
        spread = _chg(diff)
    cs = (extras or {}).get("ciss")
    ciss, ciss_chg = _last(cs), _chg(cs)
    out.append({"key": "global", "zh": "海外利率（日本、歐洲）", "j10": j10, "spread_chg": spread,
                **_st(_sgn(j10, 0.10), _sgn(j30, 0.15), (1 if spread is not None and spread <= -0.20 else 0 if spread is not None else None),
                      (1 if ciss is not None and (ciss >= 0.2 or (ciss_chg or 0) >= 0.05) else 0 if ciss is not None else None)),
                "facts": [f for f in ((f"日本 10 年公債 {_last(jp.get('10Y')):.2f}%，1 個月 {j10 * 100:+.0f} 個基點" if j10 is not None else ""),
                                      (f"日本 30 年 {_last(jp.get('30Y')):.2f}%，1 個月 {j30 * 100:+.0f} 個基點" if j30 is not None else ""),
                                      (f"美日 10 年利差 1 個月 {spread * 100:+.0f} 個基點（縮小＝借日圓買美國資產的誘因變小）" if spread is not None else ""),
                                      (f"歐元區金融壓力指數 CISS {ciss:.2f}（0.2 以上＝壓力高）" if ciss is not None else "")) if f]})

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

    # 9 台灣傳導：加權指數＋集保大戶／散戶（11-28：泡沫頂部常見「大戶賣、散戶進」）
    tw = _chg(M("^TWII"), pct=True)
    hold = extras.get("holders") or {}
    out.append({"key": "taiwan", "zh": "台灣（傳導終點）",
                **_st(_sgn(tw, 4.0, worse_if_up=False)),
                "facts": [f for f in (f"加權指數 1 個月 {tw:+.1f}%" if tw is not None else "",
                                      (f"追蹤的 {hold['n']} 檔裡，這週千張大戶減持、散戶人數增加的有 {hold['dist']} 檔，相反的有 {hold['accum']} 檔"
                                       f"（{hold['week']}，集保）" if hold.get("n") else hold.get("note", ""))) if f]})
    for p in out:
        p["facts"] = [f for f in p["facts"] if f]
    return out





def auction_tally(auctions: List[Dict], today: str, days: int = 35) -> Dict:
    """Pure: verdicts of coupon auctions held in the last `days` days (wsb.data.treasury rows, verdict 偏弱/偏強/正常)."""
    cut = (pd.Timestamp(today) - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    rs = [a for a in auctions or [] if (a.get("date") or "") >= cut and a.get("verdict") in ("偏弱", "偏強", "正常")]
    return {"n": len(rs), "weak": sum(a["verdict"] == "偏弱" for a in rs), "strong": sum(a["verdict"] == "偏強" for a in rs),
            "weak_terms": [a["term"] for a in rs if a["verdict"] == "偏弱"]}


REGIME = {(1, -1): ("停滯性通膨的壓力", "成長轉弱、通膨卻在升：央行很難靠降息救經濟，股債常一起跌，是最難的組合。"),
          (1, 1): ("降溫", "成長和通膨一起轉弱：降息的空間變大，債券通常比股票撐得住；要小心的是降溫變成衰退。"),
          (-1, -1): ("過熱", "成長和通膨一起升：企業獲利好，但利率可能被推高，估值高的股票最怕。"),
          (-1, 1): ("金髮女孩", "成長好、通膨降：對股市最友善的組合；要看它能撐多久。")}


def fed_path(fw: Dict) -> Dict:
    """Pure: from fedwatch.view — next meeting's hike probability, the cumulative move priced by the furthest meeting,
    and how the next meeting's pricing moved over a week (bp; > 0 = more hikes priced)."""
    ms = fw.get("meetings") or []
    if not fw.get("available") or not ms:
        return {}
    nxt = ms[0]
    probs = {int(float(k)): float(v) for k, v in (nxt.get("probs") or {}).items()}
    p_hike = sum(v for k, v in probs.items() if k > 0)
    p_cut = sum(v for k, v in probs.items() if k < 0)
    r0 = fw.get("r0")
    last = ms[-1]
    cum = (last["rate_after"] - r0) * 100 if r0 is not None and last.get("rate_after") is not None else None
    wk = nxt.get("week_ago")
    shift = (nxt.get("chg_bp") or 0) - (wk.get("chg_bp") or 0) if wk else None
    txt = (f"期貨市場押 {nxt['date'][5:]} 會議：升息 {p_hike * 100:.0f}%、降息 {p_cut * 100:.0f}%"
           + (f"；到 {last['date'][:7]} 累計 {cum:+.0f} 個基點" if cum is not None else "")
           + (f"；比一週前 {shift:+.0f} 個基點" if shift is not None else ""))
    return {"p_hike": p_hike, "p_cut": p_cut, "cum_bp": cum, "wk_shift": shift, "text": txt}


def curve_regime(d2: Optional[float], d10: Optional[float], band: float = 0.05) -> Optional[str]:
    """Pure: the classic four curve moves from 1-month changes of the 2- and 10-year yields (percentage points).
    牛市＝殖利率下跌；變陡＝10 年 − 2 年的差距擴大。熊市變陡（長端漲得多）最常和財政或期限溢價壓力一起出現。"""
    if d2 is None or d10 is None or (abs(d2) < band and abs(d10) < band):
        return None if d2 is None or d10 is None else "大致不動"
    steep = (d10 - d2) > 0
    if d2 < 0 and d10 < 0:
        return "牛市變陡" if steep else "牛市變平"
    if d2 > 0 and d10 > 0:
        return "熊市變陡" if steep else "熊市變平"
    return "變陡（短降長升）" if steep else "變平（短升長降）"


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
                      "要嘛是估值太高的修正、不是景氣問題。這兩種的後續很不一樣，接下來的就業與消費數據是分辨的關鍵。"
                      + ("目前的線索偏向前者：分析師下修獲利的公司已經比上修多，基本面開始轉弱，不只是估值。" if s.get("earnings") == 1 else
                         "目前的線索偏向後者：分析師還在上修獲利，基本面還撐著。" if s.get("earnings") == -1 else ""))
    pr = next((p for p in ps if p["key"] == "pricing"), {})
    if s.get("growth") == -1 and pr.get("cg") is not None and pr["cg"] <= -4 and (pr.get("cy") or 0) <= -2:
        out.append("數據說景氣還好，但價格在押景氣轉弱（銅金比和消費類股的相對表現都在往下）：通常市場比數據早 1～3 個月，"
                   "如果接下來的就業與消費數據沒有跟著轉弱，這波就是虛驚；跟著轉弱，市場就是對的。")
    if s.get("ai") == 1 and (pr.get("ew") or 0) >= 2:
        out.append("AI 股在跌，但等權重指數比市值加權強：錢從少數大型科技股流向其他股票，比較像輪動，不是全面撤退。")
    tr = next((p for p in ps if p["key"] == "treasury"), {})
    facts = " ".join(tr.get("facts") or [])
    import re as _re
    m = _re.search(r"實質利率 ([+-]\d+)＋通膨預期 ([+-]\d+)", facts)
    if m and int(m.group(1)) >= 5 and int(m.group(2)) < 0:
        out.append("名目殖利率在降，但扣掉通膨後的實質利率在升：看起來借錢變便宜，其實真實成本變貴，對高估值成長股和黃金是壓力。")
    if s.get("dollar") == 1 and "外國央行託管美債 13 週 -" in facts:
        out.append("美元轉強，同時外國央行在減持美債：常見的情況是亞洲央行賣美債換現金來穩住本國貨幣；若持續，長天期美債少了一個買家。")
    if (tr.get("auct_weak") or 0) >= 2 and "外國央行託管美債 13 週 -" in facts:
        out.append("最近的美債標售需求偏弱，外國央行也在減持：長天期美債的買家在變少，殖利率可能因為供需而上升，和經濟好壞無關。")
    gl = next((p for p in ps if p["key"] == "global"), {})
    y10f = _re.search(r"10 年期 1 個月 ([+-]\d+) 個基點", facts)
    if (gl.get("j10") or 0) >= 0.10 and y10f and int(y10f.group(1)) < 0:
        out.append("日本長期利率在升、美債利率在降：美日利差縮小，借日圓買美國資產的部位容易被迫平倉（2024 年 8 月 5 日日股單日跌 12% 就是這樣），"
                   "日本資金也比較想留在國內，美債少一個大買家。")
    rt = next((p for p in ps if p["key"] == "rates"), {})
    if (rt.get("hike_next") or 0) >= 0.5 and (s.get("pricing") == 1 or s.get("growth") == 1):
        out.append("期貨市場押聯準會下次升息，但跨資產價格或數據在押景氣轉弱：這是最怕的組合（景氣轉弱時還在升息），"
                   "要看聯準會會議聲明與點陣圖會不會鬆口。")
    if s.get("earnings") == -1 and (s.get("ai") == 1 or s.get("taiwan") == 1):
        out.append("分析師還在上修獲利，股價卻在跌：要嘛是估值太高在修正（獲利沒問題），要嘛分析師還沒跟上；下修開始出現時，跌勢通常才真正反映基本面。")
    if s.get("positioning") == 1 and s.get("credit") == 1:
        out.append("借錢買股或避險部位很擁擠，信用又在轉緊：這種組合下，小跌容易因為被迫賣出而放大。")
    if s.get("liquidity") == 1 and s.get("credit") == -1:
        out.append("市場上的錢在變少，但信用市場還很平靜：流動性通常比信用利差早反應。")
    return out


def build(fred, market, now: Optional[float] = None, extras: Optional[Dict] = None) -> Dict:
    now = now or time.time()
    ps = pillars(fred, market, extras)
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
