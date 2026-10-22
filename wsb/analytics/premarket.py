"""開盤前 30 秒 — what changed overnight, what is scheduled today, and the range the market is pricing.

No direction call.  The "range" is the options market's own number: one standard deviation for one day =
VIX ÷ √252 (S&P 500).  For Taiwan there is no free VIX feed, so the TAIEX range uses the index's own 20-day
realised volatility, labelled as such.  Each range comes with its track record computed from history: how often
the next close actually landed inside ±1σ (theory ≈ 68 %) and ±2σ (≈ 95 %), all-time / last year / last 60 days —
the rule is fixed, nothing is fitted, so the record is effectively out-of-sample.  Fat tails show up as a
lower 2σ hit rate than 95 %."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

NY, TPE = ZoneInfo("America/New_York"), ZoneInfo("Asia/Taipei")
OVERNIGHT = [("ES=F", "標普期貨", "S&P futures"), ("NQ=F", "那指期貨", "Nasdaq futures"), ("^TNX", "美債 10 年", "UST 10y"),
             ("DX-Y.NYB", "美元指數", "Dollar index"), ("CL=F", "原油", "Crude oil"), ("GC=F", "黃金", "Gold"),
             ("BTC-USD", "比特幣", "Bitcoin"), ("^N225", "日經", "Nikkei"), ("^KS11", "韓國", "KOSPI"), ("^HSI", "恆生", "Hang Seng"),
             ("^TWII", "台股加權", "TAIEX"), ("^STOXX50E", "歐洲 50", "Euro Stoxx 50"), ("^GDAXI", "德國", "DAX")]
US_CLOSE = [("^GSPC", "標普 500", "S&P 500"), ("^NDX", "那指 100", "Nasdaq 100"), ("^SOX", "費城半導體", "SOX"),
            ("TSM", "台積電 ADR", "TSM ADR"), ("^VIX", "VIX", "VIX"), ("TWD=X", "美元/台幣", "USD/TWD")]


def next_open(now: datetime, tz: ZoneInfo, hh: int, mm: int) -> datetime:
    """Next weekday open at hh:mm local (holidays are not modelled)."""
    loc = now.astimezone(tz)
    d = loc.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if loc > d + timedelta(minutes=30):
        d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def band_record(close: pd.Series, sigma_pct: pd.Series) -> Dict:
    """How often |next-day return| fell within 1σ / 2σ, where σ (%) is known the evening before."""
    j = pd.concat([close.pct_change(fill_method=None).mul(100).rename("r"), sigma_pct.shift(1).rename("s")], axis=1).dropna()
    j = j[j["s"] > 0]
    if len(j) < 60:
        return {}
    z = (j["r"].abs() / j["s"])

    def rate(x):
        return {"in1": float((x <= 1).mean() * 100), "in2": float((x <= 2).mean() * 100), "n": int(len(x))}
    return {"all": rate(z), "y1": rate(z.iloc[-252:]), "d60": rate(z.iloc[-60:]), "since": j.index[0].strftime("%Y-%m-%d")}


def _sigma(m, t, n: int = 20) -> Optional[float]:
    """The asset's own normal daily move (std of the last n daily % changes) — to judge whether today's move is unusual."""
    try:
        s = m.series(t).dropna()
        r = s.pct_change(fill_method=None).dropna().iloc[-n:] * 100
        return float(r.std()) if len(r) >= 10 and r.std() > 0 else None
    except Exception:  # noqa: BLE001
        return None


def _z(item: Dict) -> Optional[float]:
    return item["ch"] / item["sigma"] if item.get("ch") is not None and item.get("sigma") else None


def _lab(x: Dict) -> str:
    return f"{x['zh']} {x['ch']:+.1f}%"


def _mvl(x: Dict) -> str:
    return f"{x['sym']} ±{x['mv']:.1f}%"


ASIA = ("^N225", "^KS11", "^HSI", "^TWII")
EUROPE = ("^STOXX50E", "^GDAXI")


def takeaways_us(d: Dict) -> List[Dict]:
    """Fixed reading rules over the overnight numbers → plain-language points (level: alert / watch / info).
    Each point says what the data is and what it usually means mechanically — not a forecast."""
    o = {x["t"]: x for x in d.get("overnight", [])}
    rg, lv = d.get("us_range") or {}, d.get("levels") or {}
    out: List[Dict] = []
    es, nq = o.get("ES=F"), o.get("NQ=F")
    # 1) futures vs the range the market priced
    if es and es.get("ch") is not None and rg.get("sigma"):
        k = abs(es["ch"]) / rg["sigma"]
        if k >= 0.6:
            out.append({"lv": "alert" if k >= 1 else "watch",
                        "zh": f"標普期貨{'跌' if es['ch'] < 0 else '漲'} {abs(es['ch']):.2f}%，已經用掉今天預期波動（±{rg['sigma']:.2f}%）的 {k:.1f} 倍——開盤前就已經是一個{'大' if k >= 1 else '不小'}的動作。",
                        "en": f"S&P futures {es['ch']:+.2f}%, {k:.1f}× today's priced move (±{rg['sigma']:.2f}%) before the open."})
    # 2) which part of the market leads
    if es and nq and es.get("ch") is not None and nq.get("ch") is not None and abs(nq["ch"] - es["ch"]) >= 0.4:
        tech_down = nq["ch"] < es["ch"]
        out.append({"lv": "watch",
                    "zh": (f"那指期貨（{nq['ch']:+.2f}%）比標普（{es['ch']:+.2f}%）更弱：壓力集中在科技與半導體，大型科技股權重高的帳戶受影響較大。"
                           if tech_down else f"那指期貨（{nq['ch']:+.2f}%）比標普（{es['ch']:+.2f}%）強：科技股相對撐盤。"),
                    "en": "Nasdaq futures weaker than the S&P: pressure is concentrated in tech." if tech_down else "Nasdaq futures stronger than the S&P."})
    # 3) Asia / Europe: how many fell, and how unusual the moves were vs each index's own normal day
    for grp, zh_name, en_name in ((ASIA, "亞股", "Asia"), (EUROPE, "歐股", "Europe")):
        xs = [o[t] for t in grp if t in o and o[t].get("ch") is not None]
        if len(xs) >= 2:
            down = [x for x in xs if x["ch"] < 0]
            big = [x for x in xs if (_z(x) or 0) <= -2]
            if len(down) == len(xs) and big:
                out.append({"lv": "alert",
                            "zh": f"{zh_name}全面下跌，其中 {'、'.join(_lab(x) for x in big)} 跌幅超過自己平常單日波動的 2 倍——不是一般的震盪，而是明顯的賣壓。",
                            "en": f"{en_name} broadly lower; {', '.join(x['en'] for x in big)} fell more than twice their normal daily move."})
            elif len(down) == len(xs):
                out.append({"lv": "watch", "zh": f"{zh_name}全面下跌（{'、'.join(_lab(x) for x in xs)}），但幅度在平常範圍內。",
                            "en": f"{en_name} broadly lower, within normal ranges."})
    # 4) cross-asset: what kind of selling (or buying) it is
    sp_dn = es is not None and (es.get("ch") or 0) < -0.3
    y, g, b, oil = o.get("^TNX"), o.get("GC=F"), o.get("BTC-USD"), o.get("CL=F")
    if sp_dn and g and b and (g.get("ch") or 0) < -0.5 and (b.get("ch") or 0) < -1:
        out.append({"lv": "alert", "zh": "股票、黃金、比特幣同時下跌：投資人連避險資產也一起賣、換回現金——這種「什麼都賣」的情況，常見於投資人被迫降低槓桿的時候。",
                    "en": "Stocks, gold and bitcoin all down: selling across assets for cash — typical of forced de-leveraging."})
    elif sp_dn and y and (y.get("ch") or 0) < -0.5:
        out.append({"lv": "info", "zh": "股票跌、殖利率也跌：資金從股市移到公債避險（典型的避險模式），利率下降對高估值科技股算是一點緩衝。",
                    "en": "Stocks and yields both down: money moving into Treasuries for safety."})
    elif sp_dn and y and (y.get("ch") or 0) > 0.5:
        out.append({"lv": "alert", "zh": "股票跌、殖利率卻上升：市場擔心的是通膨或升息，不是景氣——這種組合對高估值成長股壓力最大，公債也無法避險。",
                    "en": "Stocks down while yields rise: an inflation / rates scare — hardest on high-valuation growth, bonds don't hedge."})
    if oil and (oil.get("ch") or 0) >= 2:
        out.append({"lv": "watch", "zh": f"原油漲 {oil['ch']:.1f}%：推高通膨預期，讓聯準會更難轉鴿；能源股相對受惠。",
                    "en": f"Oil +{oil['ch']:.1f}%: lifts inflation expectations; energy relatively favoured."})
    # 5) dealer gamma
    spot, flip = lv.get("spot"), lv.get("zero_gamma")
    if spot and flip:
        if spot < flip:
            out.append({"lv": "watch", "zh": f"標普在 Gamma 翻轉點（{flip:,.0f}）下方：造市商避險會「追漲殺跌」，今天的漲跌容易被放大；站回翻轉點之上，波動通常會收斂。",
                        "en": f"S&P below the gamma flip ({flip:,.0f}): dealer hedging tends to amplify moves today."})
        else:
            out.append({"lv": "info", "zh": f"標普在 Gamma 翻轉點（{flip:,.0f}）上方：造市商避險傾向「逢高賣、逢低買」，波動較容易被壓住。",
                        "en": f"S&P above the gamma flip ({flip:,.0f}): dealer hedging tends to dampen moves."})
    # 6) the schedule
    ev, er = d.get("events") or [], d.get("earnings") or []
    big = [x for x in er if (x.get("mv") or 0) >= 4]
    if not ev:
        out.append({"lv": "info", "zh": "今天沒有重要經濟數據：走勢主要由隔夜情緒和財報決定。"
                    + (f"選擇權預期波動較大的財報：{'、'.join(_mvl(x) for x in big)}。" if big else ""),
                    "en": "No key data today: overnight mood and earnings drive the session."})
    else:
        out.append({"lv": "watch", "zh": "今天的數據：" + "、".join(f"{e.get('tpe') or ''} {e['zh']}" for e in ev[:3]) + "——公布那一刻波動最大。",
                    "en": "Data today: " + ", ".join(e["en"] for e in ev[:3])})
    order = {"alert": 0, "watch": 1, "info": 2}
    return sorted(out, key=lambda x: order[x["lv"]])


def takeaways_tw(d: Dict) -> List[Dict]:
    c = {x["t"]: x for x in d.get("us_close", [])}
    out: List[Dict] = []
    sox, tsm, twd = c.get("^SOX"), c.get("TSM"), c.get("TWD=X")
    if sox and sox.get("ch") is not None and abs(sox["ch"]) >= 1.5:
        out.append({"lv": "alert" if abs(sox["ch"]) >= 3 else "watch",
                    "zh": f"美股費城半導體昨晚 {sox['ch']:+.1f}%：台股電子權值（台積電、聯發科等）開盤通常跟著反映。",
                    "en": f"SOX {sox['ch']:+.1f}% overnight: Taiwan tech heavyweights usually follow at the open."})
    if tsm and tsm.get("ch") is not None and abs(tsm["ch"]) >= 2:
        out.append({"lv": "watch", "zh": f"台積電 ADR 昨晚 {tsm['ch']:+.1f}%：台積電佔加權指數權重最高，是今天台股開盤方向的主要參考。",
                    "en": f"TSM ADR {tsm['ch']:+.1f}%: TSMC is the TAIEX's largest weight."})
    lk = d.get("tw_link") or {}
    if lk.get("implied") is not None:
        out.append({"lv": "info", "zh": f"依過去一年的連動，美股前一晚換算台股約 {lk['implied']:+.2f}%（相關係數 {lk.get('corr', 0):.2f}）——只算美股帶來的影響，不含台股自己的消息。",
                    "en": f"US-implied TAIEX move {lk['implied']:+.2f}% (corr {lk.get('corr', 0):.2f}); US effect only."})
    if twd and twd.get("ch") is not None and abs(twd["ch"]) >= 0.3:
        weak = twd["ch"] > 0
        out.append({"lv": "watch", "zh": f"台幣{'貶值' if weak else '升值'}（美元兌台幣 {twd['ch']:+.2f}%）：{'外資匯出壓力，對權值股不利' if weak else '外資匯入，對權值股有支撐'}；持有美股換算台幣的損益也會{'增加' if weak else '減少'}。",
                    "en": f"TWD {'weaker' if weak else 'stronger'} ({twd['ch']:+.2f}%)."})
    order = {"alert": 0, "watch": 1, "info": 2}
    return sorted(out, key=lambda x: order[x["lv"]])


def _q(m, t):
    q = m.q(t) if m is not None else None
    if not q or q.get("price") is None:
        return None
    return q


def build(eng, now: Optional[datetime] = None) -> Dict:
    now = now or datetime.now(timezone.utc)
    m = getattr(eng, "market", None)
    if m is None:
        return {"available": False}
    us_open, tw_open = next_open(now, NY, 9, 30), next_open(now, TPE, 9, 0)
    out: Dict = {"available": True, "built": now.astimezone(TPE).strftime("%m-%d %H:%M"),
                 "us_open": int(us_open.timestamp()), "tw_open": int(tw_open.timestamp()),
                 "us_open_tpe": us_open.astimezone(TPE).strftime("%m-%d %H:%M"), "us_date": us_open.strftime("%Y-%m-%d")}
    out["overnight"] = [{"t": t, "zh": zh, "en": en, "px": q["price"], "ch": q.get("chg_pct"), "asof": q.get("asof"), "sigma": _sigma(m, t)}
                        for t, zh, en in OVERNIGHT if (q := _q(m, t))]
    out["us_close"] = [{"t": t, "zh": zh, "en": en, "px": q["price"], "ch": q.get("chg_pct"), "asof": q.get("asof")}
                       for t, zh, en in US_CLOSE if (q := _q(m, t))]
    # today's scheduled events (US date of the next open)
    ev = (getattr(eng, "econ_view", None) or {}).get("events") or []
    out["events"] = [{"zh": e.get("zh"), "en": e.get("en"), "tpe": e.get("tpe"), "imp": e.get("imp"), "sep": bool(e.get("sep"))}
                     for e in ev if e.get("date") == out["us_date"] and not e.get("released") and int(e.get("imp") or 0) >= 2]
    te = getattr(eng, "techearn", None)
    cal = ((te.get("calendar") or {}).get("up") or []) if isinstance(te, dict) else []
    mv = {r.get("sym"): r for r in ((getattr(eng, "sx", None) or {}).get("earn") or []) if isinstance(r, dict)}
    out["earnings"] = [{"sym": c["sym"], "name": c.get("name") or "", "time": c.get("time") or "", "mv": (mv.get(c["sym"]) or {}).get("mv")}
                       for c in cal if str(c.get("date"))[:10] == out["us_date"]][:12]
    # the priced range
    spx, vix = m.series("^GSPC").dropna(), m.series("^VIX").dropna()
    if len(spx) > 300 and len(vix) > 300:
        v = (_q(m, "^VIX") or {}).get("price") or float(vix.iloc[-1])
        s = float(v) / math.sqrt(252)
        base = float(spx.iloc[-1])
        out["us_range"] = {"vix": float(v), "sigma": s, "base": base, "lo1": base * (1 - s / 100), "hi1": base * (1 + s / 100),
                           "lo2": base * (1 - 2 * s / 100), "hi2": base * (1 + 2 * s / 100), "base_date": spx.index[-1].strftime("%Y-%m-%d"),
                           "record": band_record(spx, vix / math.sqrt(252))}
    tw = m.series("^TWII").dropna()
    if len(tw) > 300:
        rv = tw.pct_change(fill_method=None).rolling(20).std() * 100
        s = float(rv.iloc[-1])
        base = float(tw.iloc[-1])
        out["tw_range"] = {"sigma": s, "base": base, "lo1": base * (1 - s / 100), "hi1": base * (1 + s / 100),
                           "base_date": tw.index[-1].strftime("%Y-%m-%d"), "record": band_record(tw, rv)}
    lk = ((getattr(eng, "sx", None) or {}).get("link") or {})
    if lk.get("available"):
        ix = [r for r in lk.get("index", []) if r.get("implied") is not None]
        if ix:
            r = ix[0]
            out["tw_link"] = {"us_n": r.get("us_n"), "tw_n": r.get("tw_n"), "us": r.get("us_ret", r.get("us")), "beta": r.get("beta"),
                              "corr": r.get("corr"), "implied": r.get("implied"), "us_d": r.get("us_d")}
    op = getattr(getattr(eng, "options", None), "spx", None) or {}
    if op.get("zero_gamma"):
        out["levels"] = {k: op.get(k) for k in ("spot", "zero_gamma", "call_wall", "put_wall", "gex_usd_bn_per_1pct")}
    out["take_us"], out["take_tw"] = takeaways_us(out), takeaways_tw(out)
    return out
