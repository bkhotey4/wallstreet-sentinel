"""每日盤勢解讀: after the US close, the same read the live 開盤後即時盤勢 card gives in the browser — who moved the index,
the strongest / weakest sector with its usual clue, rates / dollar / oil / VIX, today's data releases, headlines that line
up with what moved, and what changed against the last 5 / 20 sessions — computed from daily closes and archived per day
so earlier days can be read back.  The rules mirror tools/site_intraday.py (keep the two in step).  Description, not advice.

Prices: Yahoo daily chart (1 year) for every gauge, plus SPY 5-minute bars for the day's fastest 15-minute swing; fetched by
the site build (refresh) into data_cache/econ_whyday_px.json; records in data_cache/econ_whydays.json (econ_* is kept
between CI builds).  Up to KEEP days."""
from __future__ import annotations

import asyncio
import json
import math
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from ..config import DATA_DIR

PX = DATA_DIR / "econ_whyday_px.json"
DAYS = DATA_DIR / "econ_whydays.json"
KEEP = 90
NY = ZoneInfo("America/New_York")


def _symbols() -> List[str]:
    from tools import site_intraday as SI
    out = []
    for s in ["^GSPC", "^VIX", "^SOX", "SPY"] + [x[0] for x in SI.SECTORS] + SI.CROSS + [m[0] for m in SI.MEGA] + [t[0] for t in SI.TREND]:
        if s not in out:
            out.append(s)
    return out


def _load(p) -> Dict:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(p, d: Dict) -> None:
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


# ------------------------------------------------------------------ prices
def daily_from_chart(js: Dict) -> Optional[Dict]:
    """Yahoo 1-year daily chart → {"d": [dates], "c": [closes]} on the exchange's calendar."""
    try:
        r = js["chart"]["result"][0]
    except (KeyError, IndexError, TypeError):
        return None
    off = int((r.get("meta") or {}).get("gmtoffset") or 0)
    ts = r.get("timestamp") or []
    cl = (((r.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
    rows = [(datetime.utcfromtimestamp(int(t) + off).strftime("%Y-%m-%d"), float(c)) for t, c in zip(ts, cl) if c is not None and t]
    if len(rows) < 30:
        return None
    return {"d": [a for a, _ in rows], "c": [b for _, b in rows]}


def jump_from_chart(js: Dict, day: str) -> Optional[Dict]:
    """The fastest 15-minute (3 five-minute bars) move of `day`, {t, chg}; same rule as /api/quote jumpOf."""
    try:
        r = js["chart"]["result"][0]
    except (KeyError, IndexError, TypeError):
        return None
    off = int((r.get("meta") or {}).get("gmtoffset") or 0)
    ts = r.get("timestamp") or []
    cl = (((r.get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
    pts = [(int(t), float(c)) for t, c in zip(ts, cl)
           if t and c is not None and datetime.utcfromtimestamp(int(t) + off).strftime("%Y-%m-%d") == day]
    best = None
    for i in range(3, len(pts)):
        ch = (pts[i][1] / pts[i - 3][1] - 1) * 100
        if best is None or abs(ch) > abs(best["chg"]):
            best = {"t": pts[i][0], "chg": ch}
    return best


async def refresh() -> Dict:
    """Fetch the daily closes of every gauge and SPY's intraday bars (site build only)."""
    from ..data import http
    out, sem = {}, asyncio.Semaphore(6)

    async def one(s):
        async with sem:
            try:
                js = await http.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?range=1y&interval=1d",
                                    headers={"User-Agent": "Mozilla/5.0"}, timeout=20, retries=1)
                d = daily_from_chart(js)
                if d:
                    out[s] = d
            except Exception:  # noqa: BLE001
                pass
    await asyncio.gather(*(one(s) for s in _symbols()))
    day = (out.get("^GSPC") or {}).get("d", [None])[-1]
    jump = None
    if day:
        try:
            js = await http.get("https://query1.finance.yahoo.com/v8/finance/chart/SPY?range=5d&interval=5m",
                                headers={"User-Agent": "Mozilla/5.0"}, timeout=20, retries=1)
            jump = jump_from_chart(js, day)
        except Exception:  # noqa: BLE001
            jump = None
    d = {"ts": time.time(), "px": out, "jump": jump, "day": day}
    if out:
        _save(PX, d)
    return d


# ------------------------------------------------------------------ the read (mirrors the browser rules)
def quotes(px: Dict, day: str) -> Dict[str, Dict]:
    """Per symbol, the session `day`: price, prev, chg %, the trend up to the day before and the one-year normal day."""
    out = {}
    for s, v in px.items():
        d, c = v["d"], v["c"]
        if day not in d:
            continue
        i = d.index(day)
        if i < 22:
            continue
        r = [(c[j] / c[j - 1] - 1) * 100 for j in range(max(1, i - 252), i)]
        m = sum(r) / len(r)
        sd = math.sqrt(sum((x - m) ** 2 for x in r) / (len(r) - 1)) if len(r) > 60 else None
        out[s] = {"price": c[i], "prev": c[i - 1], "chg": (c[i] / c[i - 1] - 1) * 100, "sd1y": sd,
                  "trend": {"p0": c[i - 1], "p1": c[i - 2], "p5": c[i - 6], "p20": c[i - 21]}}
    return out


def _sg(x: float, d: int = 1) -> str:
    return f"{x:+.{d}f}"


def trend(q: Dict) -> List[Dict]:
    from tools import site_intraday as SI
    out = []
    for s, n in SI.TREND:
        x = q.get(s)
        if not x or not x.get("sd1y"):
            continue
        t, bp = x["trend"], s == "^TNX"
        ch = (lambda a, b: (a - b) * 100) if bp else (lambda a, b: (a / b - 1) * 100)
        td, d1, r5, r20 = ch(x["price"], x["prev"]), ch(t["p0"], t["p1"]), ch(t["p0"], t["p5"]), ch(t["p0"], t["p20"])
        sd = x["sd1y"] * t["p0"] if bp else x["sd1y"]
        zt, z5, z20 = td / sd, r5 / (sd * math.sqrt(5)), r20 / (sd * math.sqrt(20))
        opp = lambda r, z: abs(z) >= 1 and (td > 0) != (r > 0)        # noqa: E731
        rev = abs(zt) >= 1 and (opp(r5, z5) or opp(r20, z20))
        acc = not rev and abs(zt) >= 2 and (td > 0) == (r5 > 0)
        if rev or acc:
            out.append({"s": s, "n": n, "td": td, "d1": d1, "r5": r5, "r20": r20, "sd": sd, "bp": bp, "rev": rev,
                        "sc": abs(zt) * (1.5 if rev else 1)})
    return sorted(out, key=lambda x: -x["sc"])[:6]


def tr_txt(x: Dict) -> str:
    u = " bp" if x["bp"] else "%"
    g = lambda v: _sg(v, 0 if x["bp"] else 1) + u          # noqa: E731
    return (f"{x['n']}：當天 {g(x['td'])}（平常一天 ±{x['sd']:.{0 if x['bp'] else 1}f}{u}）；前一天 {g(x['d1'])}、前 5 天 {g(x['r5'])}、"
            f"前 20 天 {g(x['r20'])} → " + (("由跌轉漲" if x["td"] > 0 else "由漲轉跌") + "，和之前的方向相反。" if x["rev"] else
                                           ("同方向加速上漲" if x["td"] > 0 else "同方向加速下跌") + "，延續之前的走勢而且變快。"))


TOPIC = {"XLE": "power", "XLU": "power", "CL=F": "power", "XLF": "credit", "HYG": "credit", "XLP": "consumer", "XLY": "consumer",
         "XLV": "health", "XLK": "chip", "^SOX": "chip", "^TNX": "fed", "DX-Y.NYB": "fed", "GC=F": "fed", "IWM": "market", "^GSPC": "market"}
STOCK = {"NVDA", "CRWV", "NBIS"}


def news_lines(q: Dict, c: float, sec: List[Dict], mg: List[Dict], why: Dict, jump: Optional[Dict], cut: float, end: float,
               tr: List[Dict]) -> List[Dict]:
    MV = {x["s"]: f"{x['n']} {x['s']} {_sg(x['c'])}%" for x in mg if abs(x["c"]) >= 1}
    TP: Dict[str, list] = {}
    for x in tr:
        lab = x["n"] + " " + (("由跌轉漲" if x["td"] > 0 else "由漲轉跌") if x["rev"] else "加速" + ("上漲" if x["td"] > 0 else "下跌"))
        if x["s"] in STOCK:
            MV[x["s"]] = lab
        elif TOPIC.get(x["s"]) and TOPIC[x["s"]] not in TP:
            TP[TOPIC[x["s"]]] = [lab, 2]
    so = q.get("^SOX")
    if so and abs(so["chg"] - c) >= 0.7:
        TP["chip"] = [f"費城半導體 {_sg(so['chg'])}%", 2]
        TP["ai"] = [f"費城半導體 {_sg(so['chg'])}%", 1]
    tn = q.get("^TNX")
    if tn and abs((tn["price"] - tn["prev"]) * 100) >= 4:
        TP["fed"] = [f"10 年期殖利率 {_sg((tn['price'] - tn['prev']) * 100, 0)} bp", 2]
    if "fed" not in TP and why.get("ev"):
        TP["fed"] = ["當天有經濟數據公布", 2]
    oil = q.get("CL=F")
    if oil and abs(oil["chg"]) >= 2:
        TP["power"] = [f"原油 {_sg(oil['chg'])}%", 2]
    for x in sec:
        if x["s"] in ("XLE", "XLU") and abs(x["c"]) >= 1.2 and "power" not in TP:
            TP["power"] = [f"{x['zh']}類股 {_sg(x['c'])}%", 2]
        if x["s"] == "XLF" and abs(x["c"]) >= 1:
            TP["credit"] = [f"金融類股 {_sg(x['c'])}%", 2]
    if abs(c) >= 0.8:
        TP["market"] = [f"大盤 {_sg(c, 2)}%", 1]
    hits = []
    for n in why.get("news") or []:
        if not (cut <= n["ts"] <= end):
            continue
        sc, w, kk = 0, [], n.get("k") or []
        for s in n.get("s") or []:
            if s in MV:
                sc += 3 if kk else 1
                w.append("提到 " + MV[s])
        for k in kk:
            if k in TP:
                sc += TP[k][1]
                w.append(TP[k][0])
        if "ai" in TP and "ai" in kk and "event" in kk and "chip" not in kk:
            sc += 1
            w.append("AI 產業大事")
        if jump and (sc > 0 or kk) and jump["t"] - 4500 <= n["ts"] <= jump["t"]:
            sc += 2
            w.append(f"發布於最快一波前 {max(1, round((jump['t'] - n['ts']) / 60))} 分鐘")
        if sc >= 2:
            hits.append((sc, n["ts"], {"t": n["t"], "l": n.get("l") or "", "why": list(dict.fromkeys(w))}))
    hits.sort(key=lambda x: (-x[0], -x[1]))
    return [h[2] for h in hits[:3]]


def build_day(q: Dict, why: Dict, jump: Optional[Dict], day: str) -> Optional[Dict]:
    from tools import site_intraday as SI
    spx, vix = q.get("^GSPC"), q.get("^VIX")
    if not spx:
        return None
    c = spx["chg"]
    s = vix["prev"] / math.sqrt(252) if vix else None
    one = ("美股明顯走弱" if s and c <= -s else "美股明顯走強" if s and c >= s else "美股平盤整理" if abs(c) < 0.3
           else "美股小跌" if c < 0 else "美股小漲") + f"（標普 {_sg(c, 2)}%" + (f"，VIX {_sg(vix['chg'])}%" if vix else "") + "）"
    W: List[str] = []
    up, big = c >= 0, abs(c) >= 0.3
    if not big:
        W.append("漲跌幅很小，屬於平常的波動，沒有單一主因；下面是當天比較明顯的變化。")
    mg = [{"s": m[0], "n": m[1], "k": m[2], "c": q[m[0]]["chg"]} for m in SI.MEGA if m[0] in q]
    nm = lambda x: f"{x['k']}・{x['n']} {x['s']} {_sg(x['c'])}%"     # noqa: E731
    w = sorted([x for x in mg if (x["c"] > 0) == up and abs(x["c"]) >= 1], key=lambda x: -abs(x["c"]))
    a = sorted([x for x in mg if (x["c"] > 0) != up and abs(x["c"]) >= 1], key=lambda x: -abs(x["c"]))
    if w or a:
        W.append(f"各產業權值股{'帶頭漲' if up else '帶頭跌'}：" + ("、".join(nm(x) for x in w[:4]) if w else "沒有")
                 + "（25 檔各產業最大的公司中，當天動最大的）" + ("；反方向：" + "、".join(nm(x) for x in a[:3]) if a else "") + "。")
    sec = sorted([{"s": x[0], "zh": x[1], "k": x[3], "c": q[x[0]]["chg"]} for x in SI.SECTORS if x[0] in q], key=lambda x: -x["c"])
    if len(sec) >= 8:
        oil, tn = q.get("CL=F"), q.get("^TNX")
        bp0 = (tn["price"] - tn["prev"]) * 100 if tn else None

        def clue(x):
            if x["s"] == "XLE" and oil and abs(oil["chg"]) >= 1 and (oil["chg"] > 0) == (x["c"] > 0):
                return f"，跟著原油 {_sg(oil['chg'])}%"
            if x["s"] in ("XLF", "XLRE", "XLU") and bp0 is not None and abs(bp0) >= 3:
                return f"，10 年期殖利率 {_sg(bp0, 0)} bp" + ("（利率影響銀行利差）" if x["s"] == "XLF" else "（利率敏感型類股）")
            if x["k"] == "def" and x["c"] > 0 and c < 0:
                return "，大盤跌時資金躲進防禦型"
            if x["k"] == "def" and x["c"] < 0 and c > 0.3:
                return "，大盤漲時資金離開防禦型、轉向景氣循環股"
            return ""
        hi, lo = sec[0], sec[-1]
        if abs(hi["c"]) >= 0.8 or abs(lo["c"]) >= 0.8:
            W.append(f"類股：{hi['zh']} {_sg(hi['c'])}% 漲最多{clue(hi)}；{lo['zh']} {_sg(lo['c'])}% {'跌最多' if lo['c'] < 0 else '漲最少'}{clue(lo)}。")
    tn = q.get("^TNX")
    if tn:
        bp = (tn["price"] - tn["prev"]) * 100
        if abs(bp) >= 4:
            W.append(f"美國 10 年期公債殖利率 {_sg(bp, 0)} bp（{tn['price']:.2f}%）：" + ("利率下降，未來獲利折現回來更值錢，通常有利科技成長股。" if bp < 0
                                                                                  else "利率上升，股票的相對吸引力下降，高本益比的成長股最受壓。"))
    dx = q.get("DX-Y.NYB")
    if dx and abs(dx["chg"]) >= 0.4:
        W.append(f"美元指數 {_sg(dx['chg'])}%：" + ("美元走強，資金偏保守，也不利新台幣與新興市場。" if dx["chg"] > 0 else "美元走弱，資金較願意承擔風險，新台幣與新興市場通常受惠。"))
    oil = q.get("CL=F")
    if oil and abs(oil["chg"]) >= 2:
        W.append(f"原油 {_sg(oil['chg'])}%：" + ("能源股受惠，但油價上漲會加重通膨疑慮。" if oil["chg"] > 0 else "能源股承壓，但油價下跌減輕通膨壓力。"))
    if vix and (vix["chg"] <= -5 if up else vix["chg"] >= 8):
        W.append(f"恐慌指數 VIX {_sg(vix['chg'])}%：" + ("避險需求退潮，買盤回來。" if up else "避險需求升高，市場在找保護。"))
    for e in why.get("ev") or []:
        if e.get("date") == day:
            W.append(f"經濟數據：{e['zh']} {e['lab']}。")
    if jump and abs(jump["chg"]) >= 0.25:
        t = datetime.fromtimestamp(jump["t"], ZoneInfo("Asia/Taipei")).strftime("%H:%M")
        W.append(f"當天最快的一波：台北 {t} 前 15 分鐘，標普 ETF {_sg(jump['chg'], 2)}%。")
    if len(W) == (0 if big else 1):
        W.append("利率、美元、油價和權值股都沒有特別大的變化：比較像一般的資金進出，不是單一事件造成。")
    tr = trend(q)
    close = datetime.strptime(day + " 16:00", "%Y-%m-%d %H:%M").replace(tzinfo=NY)
    prev = close - timedelta(days=3 if close.weekday() == 0 else 1)
    news = news_lines(q, c, sec, mg, why, jump if jump and abs(jump["chg"]) >= 0.25 else None,
                      prev.timestamp(), close.timestamp() + 2 * 3600, tr)
    ru = [x["n"] for x in tr if x["rev"] and x["td"] > 0]
    rd = [x["n"] for x in tr if x["rev"] and x["td"] < 0]
    summ = ("和之前不同的是：" + ("、".join(ru) + " 由跌轉漲" if ru else "") + ("；" if ru and rd else "")
            + ("、".join(rd) + " 由漲轉跌" if rd else "") + "。") if ru or rd else None
    return {"date": day, "one": one, "why": W, "news": news, "trend": ([summ] if summ else []) + [tr_txt(x) for x in tr],
            "chg": c, "ts": time.time()}


def update(eng, now: Optional[datetime] = None) -> Dict:
    """Record the latest finished US session (after 16:15 New York, or any later day); the newest record is rewritten
    each build until the next session starts, so late headlines still make it in.  Returns the archive."""
    arc = _load(DAYS)
    p = _load(PX)
    day = p.get("day")
    now = (now or datetime.now(NY)).astimezone(NY)
    done = day and (day < now.strftime("%Y-%m-%d") or now.hour * 60 + now.minute >= 16 * 60 + 15)
    if done and p.get("px"):
        try:
            from tools.site_intraday import why_ctx
            why = why_ctx(eng)
        except Exception:  # noqa: BLE001
            why = {}
        rec = build_day(quotes(p["px"], day), why, p.get("jump"), day)
        newest = max(arc) if arc else None
        if rec and (day not in arc or day == newest):
            arc[day] = rec
            arc = dict(sorted(arc.items())[-KEEP:])
            _save(DAYS, arc)
    if p.get("px") and len(arc) < 5:                       # first run: back-fill the sessions before it (prices only)
        days = [d for d in (p["px"].get("^GSPC") or {}).get("d", [])[-6:-1] if d not in arc]
        for d in days:
            rec = build_day(quotes(p["px"], d), {}, None, d)
            if rec:
                rec["backfill"] = True
                arc[d] = rec
        if days:
            arc = dict(sorted(arc.items())[-KEEP:])
            _save(DAYS, arc)
    return arc
