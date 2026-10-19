"""華爾街關注焦點：what the market is watching right now, picked and ranked from model data, each with its hidden meaning.

Every item is generated from data (rates futures, the economic calendar, the earnings calendar and SEC filings, market
moves vs their own history, sector rotation, credit spreads, the canary lights, the stress index) and carries
  data   — the numbers that put it on the list
  hidden — what those numbers usually imply, from a stated interpretation rule (never a forecast, never a news headline)
  next   — what would confirm or undo it
Ranking: a 0–100 importance score per item (proximity of the event, size of the move vs its own history, light state).
News headlines are not used (the site's rule: headlines are background only, never risk evidence)."""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS


DEFAULTS = {"show": 6, "event_days": 10, "earnings_days": 14, "megacap_min": 5e11, "move_z": 1.5}   # settings.yaml focus: overrides


def cfg() -> Dict:
    return {**DEFAULTS, **(SETTINGS.get("focus", {}) or {})}


def _item(key: str, score: float, title: str, data: List[str], hidden: List[str], nxt: List[str], src: str) -> Dict:
    return {"key": key, "score": round(float(max(0.0, min(100.0, score))), 1), "title": title,
            "data": [d for d in data if d], "hidden": [h for h in hidden if h], "next": [n for n in nxt if n], "src": src}


def _days_to(d: str, today: date) -> int:
    return (date.fromisoformat(d) - today).days


# ---------------------------------------------------------------- 1) the Fed
def fed(eng, today: date) -> Optional[Dict]:
    ev = (getattr(eng, "econ_view", None) or {}).get("next_fomc")
    fv = getattr(eng, "fedwatch_view", None) or {}
    ms = fv.get("meetings") or []
    if not ev or not ms:
        return None
    m0 = next((m for m in ms if m["date"] == ev["date"]), ms[0])
    lab = lambda bp: "維持不變" if bp == "0" else (f"升息 {int(bp) // 25} 碼" if int(bp) > 0 else f"降息 {-int(bp) // 25} 碼")  # noqa: E731
    p0 = "、".join(f"{lab(k)} {v * 100:.0f}%" for k, v in sorted(m0["probs"].items(), key=lambda kv: -kv[1]))
    data = [f"{m0['date']} 會議（台北 {ev.get('tpe') or '—'}）期貨定價：{p0}"]
    move = [m for m in ms if any(int(k) != 0 and v >= 0.5 for k, v in m["probs"].items())]
    hidden, nxt = [], []
    if move and move[0]["date"] != m0["date"]:
        mm = move[0]
        k, v = max(((k, v) for k, v in mm["probs"].items() if int(k) != 0), key=lambda kv: kv[1])
        data.append(f"第一次「過半機率會動」的會議：{mm['date']}（{lab(k)} {v * 100:.0f}%）")
        hidden.append(f"市場押的不是這一次，而是 {mm['date']}。這次會議真正的看點是聲明與記者會有沒有替那一次鋪路——"
                      "利率決定本身多半已被定價，措辭才是意外的來源。")
        nxt.append("聲明是否提到「進一步調整」、點陣圖（有的話）中位數、主席對通膨的說法")
    last = ms[min(2, len(ms) - 1)]
    if last.get("cum_bp") is not None and abs(last["cum_bp"]) >= 25:
        word = "升息" if last["cum_bp"] > 0 else "降息"
        data.append(f"到 {last['date']} 累計定價 {last['cum_bp']:+.0f}bp")
        hidden.append(f"期貨已經押注一段{word}循環。{'升息循環中，借錢投資的成長股與高負債公司最先承壓。' if word == '升息' else '降息若是因為景氣轉弱，股市常常先漲後跌。'}")
    d = _days_to(m0["date"], today)
    return _item("fed", 95 - 3 * max(0, d), "聯準會：下一次 FOMC", data, hidden or ["期貨與共識一致，決定本身不易意外。"],
                 nxt or ["聲明措辭與記者會"], "芝加哥期交所聯邦基金期貨（CME FedWatch 算法）")


# ---------------------------------------------------------------- 2) top-tier data releases
def releases(eng, today: date) -> List[Dict]:
    view = getattr(eng, "econ_view", None) or {}
    out = []
    hi = (today + timedelta(days=int(cfg()["event_days"]))).isoformat()
    for e in view.get("events") or []:
        if e.get("released") or e["key"] == "fomc" or e.get("imp", 0) < 3 or not (today.isoformat() <= e["date"] <= hi):
            continue
        row = next((r for r in e.get("rows") or [] if r.get("cons") or r.get("prev")), {})
        data = [f"{e['date']}（台北 {e.get('tpe') or '—'}）{e['zh']}"
                + (f"：預期 {row.get('cons') or '—'}，前值 {row.get('prev') or '—'}" if row else "")]
        st = e.get("stats") or {}
        hidden = []
        if e.get("ctx"):
            hidden.append("目前背景：" + e["ctx"])
        if st.get("n") and st.get("abs_ndx") is not None:
            ratio = f"，是平常日子的 {st['absratio']:.1f} 倍" if st.get("absratio") else ""
            hidden.append(f"過去 {st['n']} 次公布當天，那指 100 平均波動 ±{st['abs_ndx']:.2f}%{ratio}（本站快取期間的統計）。")
        sc = e.get("scen") or {}
        for k, lab in (("hot", "若高於預期"), ("cool", "若低於預期")):
            if (sc.get(k) or {}).get("zh"):
                hidden.append(f"{lab}：" + sc[k]["zh"].split("。")[0] + "。")
        out.append(_item("rel:" + e["key"], 80 - 4 * _days_to(e["date"], today), f"重大數據：{e['zh']}", data, hidden,
                         [(sc.get("watch") or {}).get("zh", "")], "經濟日曆（Nasdaq／ForexFactory）"))
    return out


# ---------------------------------------------------------------- 3) megacap earnings and the AI spending question
def earnings(eng, today: date) -> Optional[Dict]:
    ed = getattr(eng, "earnings", None)
    if ed is None:
        return None
    c = cfg()
    hi = (today + timedelta(days=int(c["earnings_days"]))).isoformat()
    big = []
    for d, rec in sorted((ed.days or {}).items()):
        if today.isoformat() <= d <= hi:
            big += [(d, r) for r in rec.get("rows", []) if (r.get("mcap") or 0) >= float(c["megacap_min"]) and r.get("eps") is None]
    if not big:
        return None
    seen, names = set(), []
    for d, r in big:
        co = (r.get("name") or r["sym"]).split(" Class")[0].strip()       # one line per company (GOOG / GOOGL)
        if co not in seen and r["sym"] not in seen:
            seen |= {co, r["sym"]}
            names.append(f"{r['sym']} {d[5:]}")
    data = ["接下來兩週公布的超大型公司：" + "、".join(names[:10])]
    hidden, nxt = [], ["資本支出指引是上調還是下修", "雲端／AI 營收成長能否跟上支出"]
    se = ((getattr(eng, "techearn", None) or {}).get("season")) or {}
    if se.get("n"):
        beat = se["beats"] / se["n"] * 100
        react = se.get("avg_react")
        data.append(f"近 45 天 {se['n']} 家科技公司：{beat:.0f}% 優於預期，財報後平均股價 " + (f"{react:+.1f}%" if react is not None else "—"))
        if react is not None and beat >= 70 and react < 0:
            hidden.append("好消息不漲：大多數優於預期，股價卻下跌——代表期待已經很高，「優於預期」不夠，市場要的是更好的指引。")
    try:
        from ..data import distress_data as DD
        cache = DD.load()
        cap = ocf = 0.0
        used = []
        for s in ("MSFT", "GOOGL", "AMZN", "META", "ORCL"):
            b = (cache.get(s) or {}).get("bs") or {}
            if b.get("capex_ttm") and b.get("ocf_ttm"):
                cap += b["capex_ttm"]
                ocf += b["ocf_ttm"]
                used.append(s)
        if used and ocf > 0:
            r = cap / ocf * 100
            data.append(f"{'、'.join(used)} 近四季資本支出 {cap / 1e9:,.0f}B，是營運現金流的 {r:.0f}%（SEC 財報）")
            if r >= 80:
                hidden.append("AI 支出已逼近或超過自身賺的現金，不能再靠現金流一路翻倍——這幾份財報其實是在回答「AI 投資潮能不能延續」。"
                              "支出成長放慢就會影響整條 AI 供應鏈（晶片、伺服器、電力）。")
    except Exception:  # noqa: BLE001
        pass
    first = _days_to(big[0][0], today)
    return _item("earn", 85 - 2 * max(0, first),
                 f"超大型公司財報（市值 ≥ {float(c['megacap_min']) / 1e8:,.0f} 億美元）", data, hidden, nxt, "Nasdaq 財報日曆、SEC 財報")


# ---------------------------------------------------------------- 4) unusual moves this week
KEY = {"^TNX": ("10 年期美債殖利率", "rate"), "^VIX": ("VIX 恐慌指數", "vol"), "CL=F": ("WTI 原油", "oil"),
       "DX-Y.NYB": ("美元指數", "usd"), "^SOX": ("費城半導體", "semi"), "GC=F": ("黃金", "gold"), "HYG": ("高收益債 ETF", "credit"),
       "BTC-USD": ("比特幣", "crypto"), "^RUT": ("羅素 2000 小型股", "small"), "JPY=X": ("美元／日圓", "yen"), "^GSPC": ("標普 500", "spx")}


def _z5(s: pd.Series) -> Optional[Dict]:
    s = s.dropna()
    if len(s) < 300:
        return None
    ch = s.diff(5) if s.name in ("^TNX",) else s.pct_change(5, fill_method=None) * 100
    hist = ch.iloc[-756:-5].dropna()
    if len(hist) < 200 or hist.std() == 0 or pd.isna(ch.iloc[-1]):
        return None
    return {"chg": float(ch.iloc[-1]), "z": float((ch.iloc[-1] - hist.mean()) / hist.std()), "last": float(s.iloc[-1])}


def _meaning(kind: str, up: bool, ctx: Dict[str, Dict]) -> List[str]:
    """Interpretation rules: the same move means different things depending on what moved with it."""
    rate = (ctx.get("^TNX") or {}).get("chg")
    spx = (ctx.get("^GSPC") or {}).get("chg")
    if kind == "semi":
        if not up:
            return ["半導體是 AI 交易的核心，急跌通常是 AI 預期降溫或擁擠交易獲利了結。"
                    + ("同時殖利率上升 → 主因偏向估值（利率）壓力。" if rate is not None and rate > 0 else
                       "同時殖利率下降 → 主因偏向成長／需求擔憂。" if rate is not None else "")]
        return ["半導體急漲：AI 需求預期升溫，市場風險偏好回升。"]
    if kind == "rate":
        if up:
            return ["殖利率急升：借錢成本上升、遠期獲利折現變小——高估值成長股最受傷。"
                    + ("股市同時下跌 → 股債雙殺，債券失去避險功能。" if spx is not None and spx < 0 else "")]
        return ["殖利率急降：若股市同時上漲＝利率壓力解除；若股市下跌＝資金逃向公債避險、擔心景氣。"]
    if kind == "vol":
        return ["VIX 急升：市場在付錢買保護，短線波動放大；要看是否擴散成期限結構倒掛（近月高於 3 個月）。"] if up else \
               ["VIX 急降：恐慌消退，風險偏好回來。"]
    if kind == "oil":
        return ["油價急漲：通膨預期與停滯性通膨風險上升，聯準會更難降息；能源股受惠、運輸與消費受壓。"] if up else \
               ["油價急跌：通膨壓力減輕，但也可能反映需求轉弱。"]
    if kind == "usd":
        return ["美元急升：全球資金緊縮、新興市場與跨國企業獲利承壓。"] if up else ["美元急貶：全球流動性寬鬆，有利風險資產與新興市場。"]
    if kind == "gold":
        return ["黃金急漲：避險需求或實質利率預期下降。"] if up else ["黃金急跌：實質利率上升或避險需求退潮。"]
    if kind == "credit":
        return ["高收益債急跌：信用市場在對違約風險重新定價，常比股市更早反映壓力。"] if not up else ["高收益債走強：信用風險胃納回升。"]
    if kind == "small":
        return ["小型股急跌：對利率與景氣最敏感，常是景氣降溫或資金緊縮的早期訊號。"] if not up else ["小型股急漲：市場押注景氣與降息。"]
    if kind == "yen":
        return ["日圓急升（美元/日圓下跌）：套息交易平倉的風險，2024 年 8 月曾引發全球急跌。"] if not up else ["日圓急貶：套息交易擴大。"]
    if kind == "crypto":
        return ["比特幣急跌：最投機的風險資產先退場，常反映流動性收縮。"] if not up else ["比特幣急漲：投機性資金活躍。"]
    if kind == "spx":
        return ["標普一週波動異常大：留意是否伴隨信用利差擴大（才是系統性壓力的確認）。"]
    return []


def moves(eng) -> List[Dict]:
    ctx = {}
    for t in KEY:
        s = eng.market.series(t).rename(t)
        z = _z5(s)
        if z:
            ctx[t] = z
    out = []
    thr = float(cfg()["move_z"])
    for t, z in sorted(ctx.items(), key=lambda kv: -abs(kv[1]["z"])):
        if abs(z["z"]) < thr or t == "^GSPC":
            continue
        name, kind = KEY[t]
        unit = "bp" if t == "^TNX" else "%"
        val = z["chg"] * 100 if t == "^TNX" else z["chg"]
        data = [f"{name} 一週 {val:+.1f}{unit}（現值 {z['last']:,.2f}），是自身近 3 年一週變化的 {abs(z['z']):.1f} 個標準差"]
        out.append(_item("move:" + t, 50 + 12 * min(abs(z["z"]), 4), f"本週異常變動：{name}", data, _meaning(kind, z["chg"] > 0, ctx),
                         ["下週是否延續，或很快收回（單週急動常常回測）"], "本站行情（Yahoo）"))
    return out[:3]


# ---------------------------------------------------------------- 5) rotation
def rotation(eng) -> Optional[Dict]:
    s = eng.market.series

    def r(t, n):
        x = s(t).dropna()
        return float(x.iloc[-1] / x.iloc[-1 - n] - 1) * 100 if len(x) > n else None
    defn = [v for v in (r("XLP", 21), r("XLU", 21), r("XLV", 21)) if v is not None]
    cyc = [v for v in (r("XLK", 21), r("XLY", 21), r("XLF", 21)) if v is not None]
    mo, lv = r("MTUM", 5), r("USMV", 5)
    if not defn or not cyc:
        return None
    gap = float(np.mean(defn) - np.mean(cyc))
    data = [f"近 1 個月 防禦類股（必需消費、公用、醫療）平均 {np.mean(defn):+.1f}%，景氣／成長類股（科技、非必需、金融）{np.mean(cyc):+.1f}%"]
    hidden, score = [], 30 + 6 * abs(gap)
    if gap > 2:
        hidden.append("防禦類股領先：資金從成長股轉向避險，市場在為景氣放緩或波動上升做準備——通常不是崩盤訊號，而是風險偏好降低。")
    elif gap < -2:
        hidden.append("景氣／成長類股領先：風險偏好強，市場押注景氣與獲利成長。")
    if mo is not None and lv is not None:
        data.append(f"近 1 週 動能股（MTUM）{mo:+.1f}% vs 低波動股（USMV）{lv:+.1f}%")
        if mo - lv <= -3:
            hidden.append("動能股集中被賣、低波動股抗跌：擁擠交易在平倉（過去漲最多的被先賣），常見於趨勢轉折初期。")
            score += 15
    if not hidden:
        return None
    return _item("rotation", score, "資金輪動", data, hidden, ["防禦領先是否持續 1 個月以上", "動能股是否止跌"], "本站行情（類股 ETF）")


# ---------------------------------------------------------------- 6) credit
def credit(eng) -> Optional[Dict]:
    fr = getattr(eng, "fred", None)
    if fr is None:
        return None
    get = lambda sid: (fr.get(sid) if hasattr(fr, "get") else None)  # noqa: E731
    ccc, bb, hy = get("BAMLH0A3HYC"), get("BAMLH0A1HYBB"), get("BAMLH0A0HYM2")
    if ccc is None or bb is None or not len(ccc.dropna()) or not len(bb.dropna()):
        return None

    def chg(x, n=21):
        x = x.dropna()
        return (float(x.iloc[-1]), float(x.iloc[-1] - x.iloc[-1 - n])) if len(x) > n else (float(x.iloc[-1]), None)
    (c, dc), (b, db) = chg(ccc), chg(bb)
    data = [f"CCC 級利差 {c:.2f}%（1 個月 {dc:+.2f}）、BB 級 {b:.2f}%（{db:+.2f}）" if dc is not None and db is not None else f"CCC {c:.2f}%、BB {b:.2f}%"]
    if hy is not None and len(hy.dropna()):
        h, dh = chg(hy)
        data.append(f"整體高收益債利差 {h:.2f}%" + (f"（1 個月 {dh:+.2f}）" if dh is not None else ""))
    if dc is None or db is None:
        return None
    hidden, score, nxt = [], 35, ["BB 級利差是否跟著擴大", "高收益債 ETF（HYG）是否破底"]
    if dc > 0.5 and db < 0.2:
        hidden.append("只有最弱的 CCC 在擴大、BB 還穩：信用循環早期，壓力集中在最弱的借款人，尚未擴散到一般企業。")
        score = 55 + 5 * min(dc, 3)             # early stage: at most 70, always below the spreading case
    elif dc > 0.3 and db >= 0.2:
        hidden.append("CCC 和 BB 一起擴大：壓力開始從最弱的借款人往上擴散——這是信用壓力變成系統性的關鍵訊號。")
        score = 80 + 5 * min(db, 3)
        nxt = ["投資級（BBB）利差是否也開始擴大", "高收益債 ETF（HYG）是否破底"]
    elif dc < -0.3:
        hidden.append("低評級利差收斂：信用市場風險胃納回升。")
    if not hidden:
        return None
    return _item("credit", score, "信用市場", data, hidden, nxt, "FRED（ICE BofA 利差）")


# ---------------------------------------------------------------- 7) canaries, stress, hedges
def lights(eng) -> List[Dict]:
    out = []
    cn = getattr(eng, "canary", None) or {}
    red = [r for r in cn.get("rows", []) if r.get("state") == "alert"]
    if red:
        out.append(_item("canary", 55 + 8 * len(red), f"金絲雀紅燈 {len(red)} 顆",
                         ["、".join(r["zh"] for r in red)],
                         [r.get("why") or "" for r in red[:3]],
                         ["紅燈是否擴散到資金市場或銀行存款（目前狀況見風險模型分頁）"], "本站金絲雀燈號"))
    st = getattr(eng, "stress", None)
    if st is not None and getattr(st, "chg_20d", None) is not None and abs(st.chg_20d) >= 10:
        up = st.chg_20d > 0
        odds = next((h for h in ((getattr(eng, "odds", None) or {}).get("horizons") or []) if h.get("days") == 63), None)
        data = [f"系統性壓力指數 {st.score:.0f}，20 天 {st.chg_20d:+.1f} 點"]
        if odds and odds.get("adjusted") is not None and odds.get("base_rate"):
            data.append(f"3 個月內跌 ≥10% 的模型機率 {odds['adjusted']:.1f}%（平常 {odds['base_rate']:.1f}%）")
        out.append(_item("stress", 50 + 2 * abs(st.chg_20d), "壓力指數快速" + ("升溫" if up else "降溫"), data,
                         ["多個市場同時出現壓力：單一事件很少造成這種同步，代表風險在擴散。" if up else "壓力從多個市場同步退潮。"],
                         ["是否升破 70（歷史上的高壓區）"], "本站系統性壓力指數"))
    return out


# ---------------------------------------------------------------- build
def build(eng) -> Dict:
    today = date.today()
    items: List[Dict] = []
    for fn in (lambda: [fed(eng, today)], lambda: releases(eng, today), lambda: [earnings(eng, today)], lambda: moves(eng),
               lambda: [rotation(eng)], lambda: [credit(eng)], lambda: lights(eng)):
        try:
            items += [x for x in fn() if x]
        except Exception:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).exception("focus item failed")
    if not items:
        return {"available": False}
    items.sort(key=lambda x: -x["score"])
    return {"available": True, "asof": today.isoformat(), "items": items, "show": int(cfg()["show"])}
