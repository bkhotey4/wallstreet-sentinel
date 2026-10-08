"""Build the static 情報站 (intel station) site from live public market data.

    python -m tools.build_site [--out site] [--no-ai]

Headless: no Discord, no portfolio. Designed to run inside GitHub Actions on a schedule.
Outputs  <out>/index.html  (self-contained: inline CSS/JS/SVG, no external requests)  and  <out>/data.json.
Layout: trading-desk war room (dark first), bilingual 中/EN toggle, hoverable charts.
"""
from __future__ import annotations

import argparse
import asyncio
import html
import json
import logging
import math
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import pandas as pd

from wsb.config import SETTINGS

# Intel-station mode is enforced here, whatever settings.yaml says: this site must never carry holdings.
SETTINGS.raw.setdefault("portfolio", {})["enabled"] = False

log = logging.getLogger("build_site")
esc = html.escape

# ----------------------------------------------------------------- vocabulary (中 → EN)
GROUP_EN = {"us_equity": ("美股指數", "US equities"), "volatility": ("波動率", "Volatility"), "europe": ("歐洲", "Europe"),
            "asia": ("亞洲", "Asia"), "emerging": ("新興市場", "Emerging"), "rates": ("利率／債券", "Rates"),
            "credit": ("信用", "Credit"), "fx": ("外匯", "FX"), "commodities": ("大宗商品", "Commodities"),
            "crypto": ("加密貨幣", "Crypto"), "sectors": ("美股類股", "Sectors")}
BLOCK_EN = {"信用": "Credit", "私募信貸": "Private credit", "全球新興": "Global EM", "匯率套息": "FX carry",
            "利率": "Rates", "波動率": "Volatility", "股市結構": "Equity structure", "流動性": "Liquidity",
            "商品加密": "Commodities & crypto", "景氣就業": "Growth & jobs"}
WORD_EN = {"平靜": "Calm", "正常": "Normal", "升溫": "Elevated", "高壓": "High stress", "極端": "Extreme",
           "點火中": "Igniting", "留意": "Watch", "戒備": "Alert", "防禦": "Defensive", "低": "Low",
           "高度警戒": "High alert", "降溫": "Cooling", "持平": "Flat",
           "信用事件": "Credit event", "利率／債市衝擊": "Rates / bond shock", "套息拆倉": "Carry unwind",
           "波動率／槓桿去化": "Vol / deleveraging", "景氣衰退": "Recession", "商品／地緣能源": "Commodities / geo-energy"}
ASSET_EN = {"^GSPC": "S&P 500", "^NDX": "Nasdaq 100", "^DJI": "Dow Jones", "^RUT": "Russell 2000", "ES=F": "S&P futures",
            "NQ=F": "Nasdaq futures", "QQQ": "Nasdaq 100 ETF", "RSP": "S&P equal weight", "SMH": "Semiconductor ETF",
            "^SOX": "PHLX Semiconductor", "^VIX": "VIX", "^VIX9D": "VIX 9-day", "^VIX3M": "VIX 3-month", "^VVIX": "VVIX",
            "^MOVE": "MOVE (bond vol)", "^SKEW": "SKEW", "^STOXX50E": "Euro Stoxx 50", "^GDAXI": "DAX", "^FTSE": "FTSE 100",
            "^FCHI": "CAC 40", "EUFN": "Europe financials", "^N225": "Nikkei 225", "^HSI": "Hang Seng",
            "000001.SS": "Shanghai Composite", "^KS11": "KOSPI", "^TWII": "TAIEX", "^BSESN": "Sensex", "^AXJO": "ASX 200",
            "KWEB": "China internet", "EWT": "Taiwan ETF (US)", "2330.TW": "TSMC (TW)", "EEM": "Emerging markets",
            "EMB": "EM USD bonds", "^BVSP": "Bovespa", "^IRX": "US 3M yield", "^FVX": "US 5Y yield", "^TNX": "US 10Y yield",
            "^TYX": "US 30Y yield", "TLT": "Long Treasuries", "IEF": "7-10Y Treasuries", "SHY": "1-3Y Treasuries",
            "HYG": "High yield", "JNK": "Junk bonds", "LQD": "Investment grade", "BKLN": "Leveraged loans",
            "BIZD": "Private credit BDC", "KRE": "Regional banks", "XLF": "Financials", "BX": "Blackstone", "APO": "Apollo",
            "ARES": "Ares", "DX-Y.NYB": "US Dollar Index", "EURUSD=X": "EUR/USD", "JPY=X": "USD/JPY", "CNY=X": "USD/CNY",
            "KRW=X": "USD/KRW", "TWD=X": "USD/TWD", "AUDJPY=X": "AUD/JPY", "CHF=X": "USD/CHF", "MXN=X": "USD/MXN",
            "CL=F": "WTI crude", "BZ=F": "Brent crude", "NG=F": "Natural gas", "GC=F": "Gold", "SI=F": "Silver",
            "HG=F": "Copper", "DBC": "Commodity index", "BTC-USD": "Bitcoin", "ETH-USD": "Ether", "SOL-USD": "Solana",
            "XLK": "Technology", "XLC": "Communication", "XLY": "Discretionary", "XLP": "Staples", "XLE": "Energy",
            "XLV": "Health care", "XLI": "Industrials", "XLU": "Utilities", "XLB": "Materials", "XLRE": "Real estate",
            "IGV": "Software", "IWM": "Small caps", "MTUM": "Momentum factor", "USMV": "Min-vol factor"}
STRIP = [("^GSPC", "標普500", 0), ("^NDX", "那指100", 0), ("^TWII", "台股加權", 0), ("^N225", "日經225", 0),
         ("^VIX", "VIX", 2), ("^TNX", "美債10年", 3), ("DX-Y.NYB", "美元指數", 2), ("TWD=X", "美元/台幣", 3),
         ("GC=F", "黃金", 0), ("BZ=F", "布蘭特", 2), ("BTC-USD", "比特幣", 0), ("HYG", "高收益債", 2)]
TRENDS = [("^GSPC", "標普500", 0), ("^TWII", "台股加權", 0), ("^VIX", "VIX 恐慌指數", 2), ("^TNX", "美債10年殖利率", 3)]

# status palette (fixed, never themed) — always shown next to a text label, never colour alone
LEVEL_COLORS = ["#0ca30c", "#fab219", "#ec835a", "#d03b3b", "#a3142f"]
STAGE_COLORS = ["#0ca30c", "#fab219", "#ec835a", "#d03b3b"]


def T(zh: str, en: Optional[str] = None, tag: str = "span", cls_: str = "") -> str:
    """Bilingual text node: Chinese by default, English swapped in by the toggle."""
    en = WORD_EN.get(zh, zh) if en is None else en
    c = f' class="{cls_}"' if cls_ else ""
    return f'<{tag}{c} data-en="{esc(en)}">{esc(zh)}</{tag}>'


# ----------------------------------------------------------------- number helpers
def num(x, d=2, sign=False, pct=False, na="—"):
    if x is None:
        return na
    try:
        if x != x:
            return na
        s = f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}"
    except (TypeError, ValueError):
        return na
    return s + ("%" if pct else "")


def cls(x):
    if x is None or x != x:
        return ""
    return "up" if x > 0 else ("dn" if x < 0 else "")


def level_idx(score) -> int:
    for i, lv in enumerate(SETTINGS.get("stress_levels", [])):
        if score < lv["max"]:
            return min(i, len(LEVEL_COLORS) - 1)
    return len(LEVEL_COLORS) - 1


def nice_ticks(lo: float, hi: float, n: int = 4) -> List[float]:
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / max(n - 1, 1)
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    v, out = math.floor(lo / step) * step, []
    while v <= hi + step * 0.5:
        out.append(round(v, 10))
        v += step
    return out


def tick_label(v: float) -> str:
    a = abs(v)
    if a >= 10000:
        return f"{v / 1000:,.0f}K"
    if a >= 100:
        return f"{v:,.0f}"
    if a >= 10:
        return f"{v:,.1f}".rstrip("0").rstrip(".")
    return f"{v:,.2f}".rstrip("0").rstrip(".")


def ret_since(s, days: int) -> Optional[float]:
    s = s.dropna()
    if s.empty:
        return None
    past = s[s.index <= s.index[-1] - pd.Timedelta(days=days)]
    return (float(s.iloc[-1]) / float(past.iloc[-1]) - 1) * 100 if len(past) and past.iloc[-1] else None


# ----------------------------------------------------------------- charts (inline SVG + JSON for the hover layer)
_CHARTS: Dict[str, dict] = {}


def line_chart(cid: str, s, label: str, digits: int = 2, w: int = 560, h: int = 190,
               bands: Optional[List[Tuple[float, float, str]]] = None, fixed: Optional[Tuple[float, float]] = None) -> str:
    s = s.dropna()
    if len(s) < 10:
        return '<p class="muted">—</p>'
    pl, pr, pt, pb = 46, 58, 10, 24
    W, H = w - pl - pr, h - pt - pb
    vals = [float(v) for v in s.values]
    if fixed:
        lo, hi = fixed
    else:
        lo, hi = min(vals), max(vals)
        pad = (hi - lo) * 0.08 or 1
        lo, hi = lo - pad, hi + pad
    ticks = nice_ticks(lo, hi, 4)
    if not fixed:
        lo, hi = min(lo, ticks[0]), max(hi, ticks[-1])
    n = len(vals)
    xs = [pl + i * W / (n - 1) for i in range(n)]
    ys = [pt + (1 - (v - lo) / (hi - lo)) * H for v in vals]
    base = pt + H
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"M{xs[0]:.1f},{base:.1f} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys)) + f" L{xs[-1]:.1f},{base:.1f} Z"
    parts = []
    for b0, b1, col in bands or []:
        y1 = pt + (1 - (min(b1, hi) - lo) / (hi - lo)) * H
        y0 = pt + (1 - (max(b0, lo) - lo) / (hi - lo)) * H
        if y0 > y1:
            parts.append(f'<rect x="{pl}" y="{y1:.1f}" width="{W}" height="{y0 - y1:.1f}" fill="{col}" opacity="0.10"/>')
    for t in ticks:
        if lo <= t <= hi:
            y = pt + (1 - (t - lo) / (hi - lo)) * H
            parts.append(f'<line x1="{pl}" x2="{pl + W}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                         f'<text x="{pl - 6}" y="{y + 4:.1f}" class="axis" text-anchor="end">{tick_label(t)}</text>')
    d0, dm, d1 = s.index[0], s.index[n // 2], s.index[-1]
    parts.append(f'<text x="{pl}" y="{h - 6}" class="axis">{d0:%Y-%m}</text>'
                 f'<text x="{pl + W / 2:.0f}" y="{h - 6}" class="axis" text-anchor="middle">{dm:%Y-%m}</text>'
                 f'<text x="{pl + W}" y="{h - 6}" class="axis" text-anchor="end">{d1:%m-%d}</text>')
    parts.append(f'<path d="{area}" class="wash"/><polyline points="{pts}" class="ln"/>'
                 f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="4" class="dot"/>'
                 f'<text x="{xs[-1] + 8:.1f}" y="{ys[-1] + 4:.1f}" class="endlbl">{num(vals[-1], digits)}</text>')
    parts.append(f'<g class="hover" visibility="hidden"><line class="xh" y1="{pt}" y2="{base}"/><circle r="4" class="dot"/></g>'
                 f'<rect class="hit" x="{pl}" y="{pt}" width="{W}" height="{H}" fill="transparent"/>')
    _CHARTS[cid] = {"label": label, "d": [i.strftime("%Y-%m-%d") for i in s.index], "v": [round(v, 4) for v in vals],
                    "x": [round(x, 1) for x in xs], "y": [round(y, 1) for y in ys], "dg": digits}
    return (f'<svg id="{cid}" class="chart lc" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            + "".join(parts) + "</svg>")


def spark(s, w=96, h=28) -> str:
    s = s.dropna().tail(90)
    if len(s) < 5:
        return ""
    v = [float(x) for x in s.values]
    lo, hi = min(v), max(v)
    hi = hi if hi > lo else lo + 1
    pts = " ".join(f"{i * (w - 6) / (len(v) - 1) + 1:.1f},{2 + (1 - (x - lo) / (hi - lo)) * (h - 4):.1f}" for i, x in enumerate(v))
    ly = 2 + (1 - (v[-1] - lo) / (hi - lo)) * (h - 4)
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" aria-hidden="true"><polyline points="{pts}"/>'
            f'<circle cx="{w - 5:.1f}" cy="{ly:.1f}" r="2.5"/></svg>')


def radar(cid: str, blocks: Dict[str, float], size: int = 320) -> str:
    order = list(BLOCK_EN)
    items = sorted(blocks.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)
    if len(items) < 3:
        return ""
    cx = cy = size / 2
    R = size / 2 - 62
    n = len(items)
    ang = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    parts = []
    for ring in (25, 50, 75, 100):
        rr = R * ring / 100
        poly = " ".join(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}" for a in ang)
        parts.append(f'<polygon points="{poly}" class="{"ring hi" if ring == 50 else "ring"}"/>')
    for a in ang:
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + R * math.cos(a):.1f}" y2="{cy + R * math.sin(a):.1f}" class="grid"/>')
    pts = [(cx + R * min(v, 100) / 100 * math.cos(a), cy + R * min(v, 100) / 100 * math.sin(a)) for (_, v), a in zip(items, ang)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    parts.append(f'<polygon points="{poly}" class="rfill"/>')
    for (k, v), (x, y), a in zip(items, pts, ang):
        lx, ly = cx + (R + 14) * math.cos(a), cy + (R + 14) * math.sin(a)
        anchor = "middle" if abs(math.cos(a)) < 0.3 else ("start" if math.cos(a) > 0 else "end")
        en = BLOCK_EN.get(k, k)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="dot"/>'
                     f'<text x="{lx:.1f}" y="{ly + 4:.1f}" class="rlbl" text-anchor="{anchor}" data-en="{esc(en)}">{esc(k)}</text>'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" class="rhit" fill="transparent" tabindex="0" '
                     f'data-tip="{esc(k)}|{esc(en)}|{v:.0f}"/>')
    parts.append(f'<text x="{cx + 3:.1f}" y="{cy - R * 0.5 - 3:.1f}" class="axis">50</text>')
    return f'<svg id="{cid}" class="chart radar" viewBox="0 0 {size} {size}" role="img" aria-label="risk radar">{"".join(parts)}</svg>'


# ----------------------------------------------------------------- sections
def card(title_zh: str, title_en: str, body: str, cls_: str = "", sub: str = "") -> str:
    s = f'<p class="sub">{sub}</p>' if sub else ""
    return f'<section class="card {cls_}"><h2>{T(title_zh, title_en)}</h2>{s}{body}</section>'


def sec_strip(eng) -> str:
    tiles = []
    for t, zh, dg in STRIP:
        q = eng.market.q(t)
        s = eng.market.series(t)
        if not q and s.empty:
            continue
        price = q["price"] if q else float(s.iloc[-1])
        chg = q.get("chg_pct") if q else None
        tiles.append(f'<div class="tile"><div class="tl">{T(zh, ASSET_EN.get(t, t))}</div>'
                     f'<div class="tv">{num(price, dg)}</div><div class="tc {cls(chg)}">{num(chg, 2, sign=True, pct=True)}</div>'
                     f'{spark(s)}</div>')
    return f'<div class="strip" aria-label="market strip">{"".join(tiles)}</div>'


def sec_ssi(eng) -> str:
    st = eng.stress
    if not st:
        return card("系統性壓力指數 SSI", "Systemic Stress Index", '<p class="muted">—</p>', "ssi")
    col = LEVEL_COLORS[level_idx(st.score)]
    pb = eng.playbook or {}
    stg = int(pb.get("stage", 0) or 0)
    lv = SETTINGS.get("stress_levels", [])
    segs = "".join('<i style="background:%s;flex:%s"></i>' % (LEVEL_COLORS[min(i, 4)], min(l["max"], 100) - (lv[i - 1]["max"] if i else 0))
                   for i, l in enumerate(lv))
    chips = "".join(f'<span class="chip"><b class="{cls(-v if v is not None else None)}">{num(v, 1, sign=True)}</b> {T(lbl, en)}</span>'
                    for lbl, en, v in (("1日", "1D", st.chg_1d), ("5日", "5D", st.chg_5d), ("20日", "20D", st.chg_20d)))
    bands, prev = [], 0.0
    for i, l in enumerate(lv):
        bands.append((prev, min(l["max"], 100), LEVEL_COLORS[min(i, 4)]))
        prev = min(l["max"], 100)
    chart = line_chart("c_ssi", st.history.tail(504), "SSI", 1, w=640, h=200, bands=bands, fixed=(0, 100))
    note = T("0–100，越高代表越多市場同時出現壓力；色帶為各等級區間，滑鼠移到圖上可看每日數值。",
             "0–100: higher means stress across more markets at once. Bands mark the levels; hover for daily values.")
    return f'''<section class="card ssi">
<h2>{T("系統性壓力指數 SSI", "Systemic Stress Index")}</h2>
<div class="hero"><div class="big" style="--lv:{col}">{st.score:.0f}</div>
<div><div class="lvl"><i class="sw" style="background:{col}"></i>{T(str(st.label))}</div>
<div class="muted">{T("歷史百分位", "Historical pct")} {num(st.pctile_all, 0)}% · {T("資料涵蓋", "Coverage")} {st.coverage * 100:.0f}%</div>
<div class="chips">{chips}</div></div>
<div class="stage" style="--sc:{STAGE_COLORS[min(stg, 3)]}"><div class="sl">{T("風險階段", "Risk stage")}</div>
<div class="sv">{esc(pb.get("emoji", ""))} {T(str(pb.get("name", "—")))}</div><div class="muted">{T("風險分", "Score")} {pb.get("points", "—")}</div></div></div>
<div class="gauge"><div class="track">{segs}<b style="left:{min(st.score, 100):.1f}%"></b></div></div>
{chart}<p class="note">{note}</p></section>'''


def sec_radar(eng) -> str:
    st = eng.stress
    if not st or not st.blocks:
        return ""
    note = T("十個風險區塊的壓力分數（0–100）；越往外越緊張，粗線圈為 50。",
             "Stress score of ten risk blocks (0–100); further out = tighter, bold ring = 50.")
    return card("風險雷達", "Risk radar", f'<div class="rwrap">{radar("c_radar", st.blocks)}</div><p class="note">{note}</p>', "span3")


def sec_odds(eng) -> str:
    o = eng.odds or {}
    if not o.get("horizons"):
        return ""
    hs = o["horizons"]
    mx = max([h.get("adjusted") or 0 for h in hs] + [h.get("base_rate") or 0 for h in hs] + [10])
    rows = []
    for h in hs:
        adj, base, lift = h.get("adjusted"), h.get("base_rate"), h.get("lift_adj")
        lc = "dn" if (lift or 1) > 1.15 else ("up" if (lift or 1) < 0.85 else "")
        d, dd = h["days"], h["drawdown_pct"]
        lbl = T(f"{d} 日內跌 ≥ {dd:.0f}%", f"Fall ≥{dd:.0f}% within {d}d")
        rows.append(f'<div class="odd"><div class="ol">{lbl}</div>'
                    f'<div class="ob"><div class="obar" style="width:{(adj or 0) / mx * 100:.1f}%"></div><i class="obase" style="left:{(base or 0) / mx * 100:.1f}%"></i></div>'
                    f'<div class="ov"><b>{num(adj, 1)}%</b> <span class="muted">{T("基準", "base")} {num(base, 1)}%</span> <span class="{lc}">{num(lift, 2)}×</span></div></div>')
    mom = o.get("momentum") or {}
    bucket, since, state = o.get("bucket"), o.get("sample_start"), mom.get("state") or "—"
    legend = (f'<div class="legend"><span><i class="lk bar"></i>{T("目前機率（含升溫速度）", "Current odds (with momentum)")}</span>'
              f'<span><i class="lk tick"></i>{T("歷史平常基準", "Historical base rate")}</span></div>')
    note = T(f"SSI 落在「{bucket}」區間時標普 500 之後大跌的歷史頻率（樣本自 {since}），升溫狀態：{state}。倍數 > 1 代表比平常危險；這是歷史頻率，不是預測。",
             f"Historical frequency of S&P 500 drawdowns when SSI sat in the {bucket} zone (since {since}). Multiple > 1 = riskier than usual. Not a forecast.")
    return card("經驗崩跌機率", "Empirical crash odds", legend + "".join(rows) + f'<p class="note">{note}</p>', "span3")


def sec_trends(eng) -> str:
    cells = []
    for i, (t, zh, dg) in enumerate(TRENDS):
        s = eng.market.series(t)
        if s.empty:
            continue
        q = eng.market.q(t)
        chg = q.get("chg_pct") if q else None
        r1 = ret_since(s, 365)
        cells.append(f'<div class="trend"><div class="th"><b>{T(zh, ASSET_EN.get(t, t))}</b>'
                     f'<span class="muted">{T("今日", "1D")} <span class="{cls(chg)}">{num(chg, 2, sign=True, pct=True)}</span> · '
                     f'{T("一年", "1Y")} <span class="{cls(r1)}">{num(r1, 1, sign=True, pct=True)}</span></span></div>'
                     f'{line_chart(f"c_t{i}", s.tail(260), ASSET_EN.get(t, t), dg)}</div>')
    return card("一年走勢", "One-year trends", f'<div class="g2">{"".join(cells)}</div>', "wide") if cells else ""


def sec_shock(eng) -> str:
    sk = eng.shock or {}
    if not sk.get("radar"):
        return ""
    paths = ""
    for p in sk.get("paths", [])[:4]:
        stt = str(p.get("state"))
        c = "#d03b3b" if ("警戒" in stt or "點火" in stt) else ("#fab219" if ("留意" in stt or "升溫" in stt) else "#6b7280")
        paths += (f'<div class="path"><div class="ph"><b>{T(p["name"])}</b><span class="pill"><i class="sw" style="background:{c}"></i>{T(stt)} · {p["ignition"]:.0f}</span></div>'
                  f'<div class="meter"><i style="width:{min(p["ignition"], 100):.0f}%;background:{c}"></i></div>'
                  f'<p class="muted small">{esc(p.get("story", ""))}</p></div>')
    rows = "".join(
        f'<tr><td>{T(r["block"], BLOCK_EN.get(r["block"]))}</td><td class="r">{r["level"]:.0f}</td>'
        f'<td><div class="meter"><i style="width:{min(r["level"], 100):.0f}%;background:{LEVEL_COLORS[level_idx(r["level"])]}"></i></div></td>'
        f'<td class="r {cls(-(r["chg20"] or 0))}">{num(r["chg20"], 1, sign=True)}</td><td>{T(str(r["state"]))}</td>'
        f'<td class="r muted">{num(r.get("auc"), 2)}</td></tr>' for r in sk["radar"])
    dv = sk.get("divergence") or {}
    dvh = ""
    if dv.get("available"):
        flag = f' <span class="pill"><i class="sw" style="background:#d03b3b"></i>{T("背離警示", "Divergence")}</span>' if dv.get("flag") else ""
        dvh = (f'<p>{T("股債背離：信用／利率／流動性／新興壓力", "Divergence: credit / rates / liquidity / EM stress")} <b>{dv["credit"]:.0f}</b> '
               f'vs {T("股市隱含恐慌", "equity-implied fear")} <b>{dv["equity"]:.0f}</b>（{dv["gap"]:+.0f}）{flag}</p>')
    body = (f'<div class="g2"><div>{paths}</div><div class="scroll"><table><thead><tr><th>{T("區塊", "Block")}</th>'
            f'<th class="r">{T("水準", "Level")}</th><th></th><th class="r">{T("20日", "20D")}</th><th>{T("狀態", "State")}</th>'
            f'<th class="r">AUC</th></tr></thead><tbody>{rows}</tbody></table></div></div>{dvh}')
    return card("衝擊雷達：下一次衝擊可能從哪裡點火", "Shock radar: where the next shock may ignite", body, "wide")


def sec_playbook_breaks(eng) -> str:
    pb = eng.playbook or {}
    why = "".join(f'<li><span class="pts">{("+%s" % w[0]) if isinstance(w, (list, tuple)) and w[0] else "0"}</span> '
                  f'{esc(str(w[1] if isinstance(w, (list, tuple)) else w))}</li>' for w in pb.get("why", []))
    br = eng.breaks or {}
    items = []
    if br.get("available"):
        m = br["metrics"]
        sb = m.get("stock_bond_corr")
        if sb:
            win = sb["window"]
            items.append(f'{T(f"股債 {win} 日相關", f"Stock-bond {win}d corr")} <b>{sb["value"]:+.2f}</b> '
                         f'<span class="muted">（{T("歷史", "pct")} {sb["pctile"]:.0f}%）</span>')
        if m.get("double_kill_20d"):
            items.append(f'{T("近 20 日股債雙殺日", "Stock & bond down days (20d)")} <b>{m["double_kill_20d"]["value"]}</b>')
        if m.get("haven_fail"):
            items.append(f'{T("股跌時長債與黃金同跌比例", "Haven failure rate on down days")} <b>{m["haven_fail"]["value"]:.0f}%</b>')
        for fl in br.get("flags", []):
            items.append(f'<span class="warn">⚠ {esc(fl.get("title") or str(fl.get("detail", "")).split("：")[0])}</span>')
    empty = '<li class="muted">—</li>'
    lis = "".join(f"<li>{i}</li>" for i in items) or empty
    body = (f'<p class="stagebig">{esc(pb.get("emoji", ""))} <b>{T(str(pb.get("name", "—")))}</b> · {T("風險分", "Score")} {pb.get("points", "—")}</p>'
            f'<ul class="why">{why or empty}</ul>'
            f'<h3>{T("避險有效性", "Do hedges still work?")}</h3><ul>{lis}</ul>')
    return card("風險劇本", "Risk playbook", body, "span4", sub=T("規則式計分，每一分都可追溯", "Rule-based score; every point is traceable"))


def sec_markets(eng) -> str:
    names = SETTINGS.names()
    tabs, panels = [], []
    for i, g in enumerate(SETTINGS.universe.keys()):
        rows = eng.market.returns_table(SETTINGS.group(g))
        if not rows:
            continue
        body = "".join(
            f'<tr><td>{T(names.get(r["ticker"], r["ticker"]), ASSET_EN.get(r["ticker"], r["ticker"]))}<span class="tk">{esc(r["ticker"])}</span></td>'
            f'<td class="r">{num(r["price"], 2)}</td><td class="r {cls(r["d1"])}">{num(r["d1"], 2, sign=True, pct=True)}</td>'
            f'<td class="r {cls(r.get("w1"))}">{num(r.get("w1"), 1, sign=True, pct=True)}</td><td class="r {cls(r.get("m1"))}">{num(r.get("m1"), 1, sign=True, pct=True)}</td>'
            f'<td class="r {cls(r.get("ytd"))}">{num(r.get("ytd"), 1, sign=True, pct=True)}</td>'
            f'<td class="r"><div class="pos" title="{num(r.get("pct_52w"), 0)}%"><i style="left:{min(max(r.get("pct_52w") or 0, 0), 100):.0f}%"></i></div></td></tr>'
            for r in rows)
        zh, en = GROUP_EN.get(g, (g, g))
        tabs.append(f'<button class="tab{" on" if not tabs else ""}" data-t="g{i}" data-en="{esc(en)}" type="button">{esc(zh)}</button>')
        panels.append(f'<div class="panel{" on" if not panels else ""}" id="g{i}"><div class="scroll"><table><thead><tr><th>{T("標的", "Asset")}</th>'
                      f'<th class="r">{T("價格", "Price")}</th><th class="r">{T("今日", "1D")}</th><th class="r">{T("1週", "1W")}</th>'
                      f'<th class="r">{T("1月", "1M")}</th><th class="r">{T("年初至今", "YTD")}</th><th class="r">{T("52週區間位置", "52W range")}</th>'
                      f'</tr></thead><tbody>{body}</tbody></table></div></div>')
    note = T("Yahoo Finance 報價，可能延遲約 15 分鐘；最右欄是現價在一年高低區間的位置。",
             "Yahoo Finance quotes, may be ~15 min delayed; the last column shows where price sits in its 52-week range.")
    return card("全球跨資產行情", "Global cross-asset board", f'<div class="tabs">{"".join(tabs)}</div>{"".join(panels)}<p class="note">{note}</p>', "span8")


def sec_macro(eng) -> str:
    rg = eng.regime or {}
    rows = ""
    for sid, name in SETTINGS.get("fred_series", {}).items():
        x = eng.fred.latest(sid)
        if x:
            dg = 0 if abs(x["value"]) >= 1000 else 3
            rows += (f'<tr><td>{T(name, sid)}</td><td class="r">{num(x["value"], dg)}</td><td class="r {cls(x.get("chg_1m"))}">{num(x.get("chg_1m"), dg, sign=True)}</td>'
                     f'<td class="r muted">{num(x.get("pctile_3y"), 0)}</td></tr>')
    reg = ""
    if rg:
        reg = (f'<div class="kv"><div><span class="muted">{T("總經象限", "Macro quadrant")}</span><b>{esc(str(rg.get("quadrant", "—")))}</b></div>'
               f'<div><span class="muted">{T("風險偏好", "Risk appetite")}</span><b>{esc(str(rg.get("risk_mode", "—")))}</b></div>'
               f'<div><span class="muted">{T("淨流動性 13 週", "Net liquidity 13w")}</span><b class="{cls(rg.get("net_liquidity_chg_13w_bn"))}">{num(rg.get("net_liquidity_chg_13w_bn"), 0, sign=True)} bn</b></div></div>')
    if not rows and not reg:
        return ""
    tbl = (f'<div class="scroll"><table><thead><tr><th>{T("指標", "Series")}</th><th class="r">{T("最新", "Last")}</th><th class="r">{T("1月", "1M")}</th>'
           f'<th class="r">{T("3年百分位", "3Y pct")}</th></tr></thead><tbody>{rows}</tbody></table></div>') if rows else ""
    return card("總經與流動性", "Macro & liquidity", reg + tbl, "span4")


def sec_positioning(eng) -> str:
    op = eng.options.spx or {}
    L = []
    if op:
        L.append(f'<div class="kv"><div><span class="muted">GEX (bn/1%)</span><b class="{cls(op.get("gex_usd_bn_per_1pct"))}">{num(op.get("gex_usd_bn_per_1pct"), 2, sign=True)}</b></div>'
                 f'<div><span class="muted">{T("零 Gamma 翻轉點", "Zero-gamma flip")}</span><b>{num(op.get("zero_gamma"), 0)}</b></div>'
                 f'<div><span class="muted">{T("Call 牆／Put 牆", "Call / Put wall")}</span><b>{num(op.get("call_wall"), 0)} / {num(op.get("put_wall"), 0)}</b></div>'
                 f'<div><span class="muted">P/C (OI)</span><b>{num(op.get("put_call_oi"), 2)}</b></div></div>')
    cd = eng.crypto.data or {}
    if cd:
        L.append('<div class="kv">' + "".join(f'<div><span class="muted">{esc(str(k))}</span><b>{esc(num(v, 2) if isinstance(v, (int, float)) else str(v))}</b></div>'
                                             for k, v in list(cd.items())[:8]) + '</div>')
    return card("部位與情緒", "Positioning & sentiment", "".join(L), "span4") if L else ""


def sec_taiwan(eng) -> str:
    tw = eng.taiwan
    if not (tw.flows or tw.futures):
        return ""
    lis = "".join(f"<li>{esc(x)}</li>" for x in tw.summary_lines())
    return card("台灣籌碼", "Taiwan flows", f'<ul class="lines">{lis}</ul>', "span4",
                sub=T("證交所／期交所官方資料（僅中文）", "TWSE / TAIFEX official data (Chinese only)"))


def sec_calendar(eng) -> str:
    ev = eng.calendar.upcoming(14)
    if not ev:
        return ""
    lis = "".join(f'<li><span class="dt">{esc(e["date"][5:])}</span>{esc(e["event"])}</li>' for e in ev[:18])
    return card("未來 14 天事件", "Next 14 days", f'<ul class="cal">{lis}</ul>', "span4")


def sec_news(eng) -> str:
    items = eng.news.top(16)
    if not items:
        return ""
    tz = ZoneInfo(SETTINGS.get("timezone", "Asia/Taipei"))
    rows = ""
    for n in items:
        link = esc(n.link) if str(n.link).startswith(("http://", "https://")) else "#"
        t = datetime.fromtimestamp(n.ts, tz).strftime("%m/%d %H:%M") if n.ts else ""
        rows += (f'<li><span class="sc">{n.score}</span><div><a href="{link}" target="_blank" rel="noopener noreferrer">{esc(n.title)}</a>'
                 f'<div class="muted small">{esc(n.source)} · {t}</div></div></li>')
    return card("風險新聞", "Risk news", f'<ul class="news">{rows}</ul>', "span8",
                sub=T("依關鍵字風險分數排序", "Ranked by keyword risk score"))


def sec_quality(eng) -> str:
    from wsb.health import HEALTH
    sk = eng.shock or {}
    ql = sk.get("quality") or {}
    rows = ""
    for w in ql.get("walk_forward", []):
        if w.get("n_test"):
            d, dd = w["days"], w["drawdown_pct"]
            rows += (f'<tr><td>{T(f"{d} 日跌 ≥ {dd:.0f}%", f"{d}d fall ≥{dd:.0f}%")}</td>'
                     f'<td class="r">{num(w.get("auc_oos"), 2)}</td><td>{esc(str(w.get("verdict")))}</td></tr>')
    lines = []
    for hz in (eng.lab or {}).get("horizons", []):
        if not hz.get("baseline"):
            continue
        e = hz.get("ensemble")
        if e and e.get("accepted"):
            lines.append(f'{hz["days"]}d：{esc(", ".join(hz["adopted"]))}（AUC {e["auc"]:.2f}）')
        else:
            lines.append(f'{hz["days"]}d：{T("沒有候選指標通過檢驗，沿用原模型", "no candidate passed; baseline kept")}（AUC {hz["baseline"]["auc"]:.2f}）')
    ok = sum(1 for s in HEALTH.sources.values() if s.state == "ok")
    bad = [s.name for s in HEALTH.sources.values() if s.state != "ok"]
    badh = f'<span class="muted">（{T("異常", "issues")}：{esc(", ".join(bad[:6]))}）</span>' if bad else ""
    lis = "".join(f"<li>{x}</li>" for x in lines)
    note = T("AUC 0.5 ＝ 隨機、1.0 ＝ 完美；低於 0.6 代表鑑別力有限。請把本站當風險溫度計，而不是預測器。",
             "AUC 0.5 = random, 1.0 = perfect; below 0.6 = weak. Treat this as a risk thermometer, not a forecaster.")
    body = (f'<div class="scroll"><table><thead><tr><th>{T("情境", "Horizon")}</th><th class="r">{T("樣本外 AUC", "OOS AUC")}</th>'
            f'<th>{T("鑑別力", "Verdict")}</th></tr></thead><tbody>{rows}</tbody></table></div><ul class="lines">{lis}</ul>'
            f'<p>{T("資料源", "Data sources")} <b>{ok}/{len(HEALTH.sources)}</b> {T("正常", "OK")}{badh}</p><p class="note">{note}</p>')
    return f'<details class="card wide"><summary><h2>{T("模型可信度與資料健康", "Model credibility & data health")}</h2></summary>{body}</details>'


def sec_ai(text: str, engine_name: str) -> str:
    if not text:
        return ""
    sub = T(f"由 {engine_name} 依本頁公開數據自動撰寫；只描述市場、不構成投資建議，可能有誤（僅中文）",
            f"Auto-written by {engine_name} from this page's public data; market description only, not advice (Chinese only)")
    return card("AI 市場評論", "AI market commentary", f'<div class="ai">{md_to_html(text)}</div>', "wide", sub=sub)


# ----------------------------------------------------------------- AI: public market commentary (no position advice)
PUBLIC_SYSTEM = """你是華爾街跨資產策略分析師，正在為一個「公開」的市場情報網頁撰寫評論，讀者是不特定的一般大眾。
【鐵律】
1. 只能使用 DATA PACK 中的數字；沒有的寫「資料缺」，絕不編造。每個結論附上支撐數據。
2. 這是市場描述，不是投資建議：不得提出任何買進、賣出、加碼、減碼、停損、避險比例、目標 β、部位調整幅度等操作建議，也不得針對個股給出價位或操作；不得假設讀者持有任何部位。
3. 可以描述市場正在發生什麼、哪些風險訊號在升溫、歷史上類似情況如何、接下來值得觀察的數據與事件。
4. 機率要誠實；引用崩跌機率時說明那是歷史頻率、不是預測。
5. 一律使用台灣繁體中文與台灣用語，語氣冷靜精準；金融術語可保留英文。"""

PUBLIC_BRIEF = """根據 DATA PACK 撰寫今日的公開市場評論（Markdown，總長 ≤ 1800 字），結構如下：

**一句話結論**（今天市場最重要的一件事＋整體風險溫度）

**風險儀表**（SSI 與最主要的 3 個推升因子，附數據；崩跌機率相對基準的意義）

**跨資產掃描**（只挑有訊號的市場：美股、利率、信用、匯率、商品、加密、亞洲與台股）

**背離與暗流**（最多 3 點：哪裡的數據跟主流敘事不一致）

**情境推演（未來 1–4 週）**（基準／偏空／偏多三種情境，各附觸發條件；只描述市場可能走向，不給操作建議）

**本週觀察清單**（接下來要盯的數據、事件與關鍵水準）"""

ADVICE_RX = re.compile(r"(減碼|加碼|停損|停利|買進|賣出|建議(?:買|賣|持有|布局|配置)|避險.{0,8}\d+\s*[%％]|曝險.{0,8}\d+\s*[%％]"
                       r"|目標\s*[βB]|部位.{0,6}(?:調整|降低|提高))")


def scrub_advice(text: str) -> str:
    """Belt and braces: drop any line that still reads like position advice."""
    return "\n".join(ln for ln in (text or "").splitlines() if not ADVICE_RX.search(ln)).strip()


def md_to_html(text: str) -> str:
    """Tiny, safe markdown subset (headers, bold, bullets, paragraphs)."""
    out, in_ul = [], False
    for raw in (text or "").splitlines():
        line = esc(raw.rstrip())
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        m = re.match(r"^\s*[-*•]\s+(.*)$", line)
        if m:
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{m.group(1)}</li>")
            continue
        if in_ul:
            out.append("</ul>")
            in_ul = False
        h = re.match(r"^#{1,4}\s*(.*)$", line)
        if h:
            out.append(f"<h4>{h.group(1)}</h4>")
        elif re.match(r"^<b>[^<]{1,40}</b>\s*[:：]?$", line.strip()):
            out.append(f"<h4>{line.strip()}</h4>")
        elif line.strip():
            out.append(f"<p>{line}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


# ----------------------------------------------------------------- page
CSS = """
:root{color-scheme:dark;--page:#0a0b0d;--card:#141518;--card2:#1c1d21;--bd:rgba(255,255,255,.08);--tx:#f2f2f0;--tx2:#c3c2b7;--mu:#8f8d86;
--grid:#2c2c2a;--axis:#4a4945;--up:#2fbf71;--dn:#e5484d;--ac:#3987e5;--wash:rgba(57,135,229,.13);--warn:#fab219}
:root[data-theme="light"]{color-scheme:light;--page:#f4f4f1;--card:#fcfcfb;--card2:#f1f0ec;--bd:rgba(11,11,11,.10);--tx:#0b0b0b;--tx2:#52514e;--mu:#6f6d67;
--grid:#e1e0d9;--axis:#c3c2b7;--up:#127a3e;--dn:#c9302c;--ac:#2a78d6;--wash:rgba(42,120,214,.10);--warn:#9a6200}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--page);color:var(--tx);font:14px/1.55 system-ui,-apple-system,"Segoe UI","Noto Sans TC","Microsoft JhengHei",sans-serif}
.top{position:sticky;top:0;z-index:5;background:var(--page);border-bottom:1px solid var(--bd)}
.bar{max-width:1320px;margin:0 auto;padding:10px 16px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.brand{font-weight:800;letter-spacing:.08em;font-size:13px}.brand small{display:block;font-weight:500;letter-spacing:0;color:var(--mu);font-size:12px}
.live{display:inline-flex;align-items:center;gap:6px;color:var(--mu);font-size:12px;margin-left:auto}.live i{width:8px;height:8px;border-radius:50%;background:var(--up)}
.btn{background:var(--card);border:1px solid var(--bd);color:var(--tx);border-radius:8px;padding:5px 10px;font:inherit;font-size:12px;cursor:pointer;min-width:40px}
.wrap{max-width:1320px;margin:0 auto;padding:12px 16px 40px}
.strip{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(148px,1fr);gap:8px;overflow-x:auto;padding-bottom:4px;scrollbar-width:thin}
.tile{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:9px 11px;position:relative;min-height:86px}
.tl{color:var(--mu);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.tv{font-size:18px;font-weight:700;margin-top:2px}.tc{font-size:12px;font-variant-numeric:tabular-nums}
.spark{position:absolute;right:8px;bottom:8px;width:80px;height:24px}.spark polyline{fill:none;stroke:var(--mu);stroke-width:1.5}.spark circle{fill:var(--ac)}
.grid12{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));grid-auto-flow:row dense;gap:12px;margin-top:12px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px;grid-column:span 4;min-width:0}
.card.ssi{grid-column:span 6}.card.span3{grid-column:span 3}.card.span4{grid-column:span 4}.card.span8{grid-column:span 8}.card.wide{grid-column:span 12}
h2{margin:0 0 8px;font-size:12.5px;font-weight:700;letter-spacing:.06em;color:var(--tx2)}h3{font-size:13px;color:var(--tx2);margin:14px 0 6px}h4{margin:12px 0 4px;font-size:14px}
.sub{color:var(--mu);font-size:12px;margin:-4px 0 10px}.muted{color:var(--mu)}.small{font-size:12px}.note{color:var(--mu);font-size:12px;margin:10px 0 0}
.hero{display:flex;gap:18px;align-items:center;flex-wrap:wrap}.big{font-size:64px;font-weight:800;line-height:1;border-left:6px solid var(--lv);padding-left:12px}
.lvl{font-size:20px;font-weight:700;display:flex;align-items:center;gap:6px}.sw{display:inline-block;width:10px;height:10px;border-radius:3px;flex:none}
.chips{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}.chip{background:var(--card2);border:1px solid var(--bd);border-radius:99px;padding:1px 9px;font-size:12px;color:var(--tx2)}
.stage{margin-left:auto;border:1px solid var(--bd);border-left:4px solid var(--sc);border-radius:10px;padding:8px 12px;background:var(--card2)}.sl{font-size:11px;color:var(--mu)}.sv{font-size:18px;font-weight:700}
.gauge{margin:14px 0 4px}.track{position:relative;display:flex;height:8px;gap:2px}.track i{display:block;border-radius:2px}.track b{position:absolute;top:-4px;width:3px;height:16px;background:var(--tx);border-radius:2px;transform:translateX(-1px)}
.chart{width:100%;height:auto;display:block;margin-top:6px;overflow:visible}.chart .grid{stroke:var(--grid);stroke-width:1}.chart .axis{fill:var(--mu);font-size:11px}
.lc .ln{fill:none;stroke:var(--ac);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}.lc .wash{fill:var(--wash)}
.dot{fill:var(--ac);stroke:var(--card);stroke-width:2}.endlbl{fill:var(--tx);font-size:12px;font-weight:600}.xh{stroke:var(--mu);stroke-width:1}
.radar .ring{fill:none;stroke:var(--grid)}.radar .ring.hi{stroke:var(--axis)}.rfill{fill:var(--wash);stroke:var(--ac);stroke-width:2;stroke-linejoin:round}
.rlbl{fill:var(--tx2);font-size:11.5px}.rhit{cursor:pointer;outline:none}.rwrap{max-width:320px;margin:0 auto}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--tx2);margin-bottom:6px}.lk{display:inline-block;vertical-align:middle;margin-right:6px}
.lk.bar{width:16px;height:8px;border-radius:0 3px 3px 0;background:var(--ac)}.lk.tick{width:2px;height:12px;background:var(--tx)}
.odd{margin:12px 0}.ol{font-size:13px;margin-bottom:4px}.ob{position:relative;height:12px;background:var(--card2);border-radius:0 4px 4px 0}
.obar{height:12px;background:var(--ac);border-radius:0 4px 4px 0}.obase{position:absolute;top:-3px;width:2px;height:18px;background:var(--tx)}.ov{font-size:13px;margin-top:3px}
.g2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.trend .th{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;align-items:baseline}
.path{margin-bottom:12px}.ph{display:flex;justify-content:space-between;gap:8px;align-items:center}
.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--bd);border-radius:99px;padding:1px 9px;font-size:12px;white-space:nowrap;color:var(--tx2)}
.meter{height:6px;border-radius:99px;background:var(--card2);overflow:hidden;min-width:60px;margin-top:4px}.meter i{display:block;height:100%;border-radius:99px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:6px 7px;border-bottom:1px solid var(--bd);text-align:left;vertical-align:middle}
th{color:var(--mu);font-weight:500;font-size:12px;white-space:nowrap}.r{text-align:right;font-variant-numeric:tabular-nums}.scroll{overflow-x:auto}
.up{color:var(--up)}.dn{color:var(--dn)}.tk{color:var(--mu);font-size:11px;margin-left:6px}
.pos{position:relative;height:6px;width:70px;margin-left:auto;background:var(--card2);border-radius:99px}.pos i{position:absolute;top:-3px;width:3px;height:12px;background:var(--tx2);border-radius:2px;transform:translateX(-1px)}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}.tab{background:none;border:1px solid var(--bd);color:var(--tx2);border-radius:99px;padding:3px 11px;cursor:pointer;font:inherit;font-size:12px}
.tab.on{background:var(--ac);border-color:var(--ac);color:#fff}.panel{display:none}.panel.on{display:block}
ul{padding-left:18px;margin:6px 0}.why li,.lines li{margin:4px 0}.pts{display:inline-block;min-width:24px;color:var(--ac);font-weight:700}.warn{color:var(--warn)}
.stagebig{font-size:16px;margin:4px 0 8px}.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:10px}
.kv div{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:7px 9px}.kv span{display:block;font-size:11.5px}.kv b{font-size:15px}
.cal{list-style:none;padding:0;margin:0}.cal li{padding:6px 0;border-bottom:1px solid var(--bd);display:flex;gap:10px}.dt{color:var(--ac);font-variant-numeric:tabular-nums;min-width:42px;flex:none}
.news{list-style:none;padding:0;margin:0}.news li{break-inside:avoid;display:flex;gap:10px;padding:7px 0;border-bottom:1px solid var(--bd)}
.sc{flex:none;width:26px;height:22px;text-align:center;line-height:22px;background:var(--card2);border:1px solid var(--bd);border-radius:6px;font-size:12px;color:var(--tx2)}
a{color:var(--tx);text-decoration:none}a:hover{color:var(--ac);text-decoration:underline}
.ai{columns:2;column-gap:28px}.ai p{margin:6px 0}.ai h4{break-after:avoid;color:var(--tx)}.ai ul{margin:4px 0}
details.card summary{cursor:pointer;list-style:none}details.card summary::-webkit-details-marker{display:none}
details.card summary h2{display:inline;margin:0}details.card summary h2::before{content:"▸ ";color:var(--mu)}details.card[open] summary h2::before{content:"▾ "}details.card[open] summary{margin-bottom:10px}
details.card{margin-top:12px}
#tip{position:fixed;z-index:9;pointer-events:none;background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:6px 9px;font-size:12px;box-shadow:0 6px 18px rgba(0,0,0,.35);display:none}
#tip b{display:block;font-size:14px;color:var(--tx)}#tip span{color:var(--mu)}
footer{color:var(--mu);font-size:12px;padding:16px 0 0;border-top:1px solid var(--bd);margin-top:16px}
@media(max-width:1100px){.card.ssi{grid-column:span 12}.card.span3{grid-column:span 6}.card.span4{grid-column:span 6}.card.span8{grid-column:span 12}}
@media(max-width:760px){.card,.card.ssi,.card.span3,.card.span4,.card.span8{grid-column:span 12}.g2{grid-template-columns:1fr}.ai{columns:1}
 .big{font-size:52px}.stage{margin-left:0}.live{margin-left:0;width:100%;order:3}}
"""

JS = r"""
(function(){
var D=JSON.parse(document.getElementById('chart-data').textContent);
var tip=document.getElementById('tip');
function show(x,y,rows){tip.textContent='';rows.forEach(function(r,i){var e=document.createElement(i?'span':'b');e.textContent=r;tip.appendChild(e);});
 tip.style.display='block';var w=tip.offsetWidth,h=tip.offsetHeight;tip.style.left=Math.max(8,Math.min(window.innerWidth-w-8,x+14))+'px';tip.style.top=Math.max(8,y-h-12)+'px';}
function hide(){tip.style.display='none';}
document.querySelectorAll('svg.lc').forEach(function(svg){var c=D[svg.id];if(!c)return;var g=svg.querySelector('.hover'),ln=g.querySelector('line'),dt=g.querySelector('circle'),hit=svg.querySelector('.hit');
 function mv(ev){var r=svg.getBoundingClientRect(),vb=svg.viewBox.baseVal,px=(ev.clientX-r.left)*vb.width/r.width,n=c.x.length,lo=0,hi=n-1;
  while(hi-lo>1){var m=(lo+hi)>>1;if(c.x[m]<px)lo=m;else hi=m;}var i=(px-c.x[lo]<c.x[hi]-px)?lo:hi;
  g.setAttribute('visibility','visible');ln.setAttribute('x1',c.x[i]);ln.setAttribute('x2',c.x[i]);dt.setAttribute('cx',c.x[i]);dt.setAttribute('cy',c.y[i]);
  show(ev.clientX,ev.clientY,[c.v[i].toLocaleString(undefined,{minimumFractionDigits:c.dg,maximumFractionDigits:c.dg}),c.label+' · '+c.d[i]]);}
 hit.addEventListener('pointermove',mv);hit.addEventListener('pointerdown',mv);hit.addEventListener('pointerleave',function(){g.setAttribute('visibility','hidden');hide();});});
document.querySelectorAll('.rhit').forEach(function(el){function sh(ev){var p=el.dataset.tip.split('|'),en=document.documentElement.lang==='en',r=el.getBoundingClientRect();
  show(ev.clientX||r.left+r.width/2,ev.clientY||r.top,[p[2]+' / 100',en?p[1]:p[0]]);}
 el.addEventListener('pointermove',sh);el.addEventListener('focus',sh);el.addEventListener('pointerleave',hide);el.addEventListener('blur',hide);});
document.querySelectorAll('.tab').forEach(function(b){b.addEventListener('click',function(){document.querySelectorAll('.tab,.panel').forEach(function(e){e.classList.remove('on');});b.classList.add('on');document.getElementById(b.dataset.t).classList.add('on');});});
function store(k,v){try{localStorage.setItem(k,v);}catch(e){}}function load(k){try{return localStorage.getItem(k);}catch(e){return null;}}
function setLang(l){document.documentElement.lang=l==='en'?'en':'zh-Hant';document.querySelectorAll('[data-en]').forEach(function(e){if(e.dataset.zh===undefined)e.dataset.zh=e.textContent;e.textContent=l==='en'?e.dataset.en:e.dataset.zh;});
 document.getElementById('langBtn').textContent=l==='en'?'中文':'EN';store('lang',l);}
function setTheme(t){if(t==='light')document.documentElement.setAttribute('data-theme','light');else document.documentElement.removeAttribute('data-theme');
 document.getElementById('themeBtn').textContent=t==='light'?'☾':'☀';store('theme',t);}
document.getElementById('langBtn').addEventListener('click',function(){setLang(document.documentElement.lang==='en'?'zh':'en');});
document.getElementById('themeBtn').addEventListener('click',function(){setTheme(document.documentElement.getAttribute('data-theme')==='light'?'dark':'light');});
if(load('theme')==='light')setTheme('light');if(load('lang')==='en')setLang('en');
})();
"""


def render(eng, ai_text: str = "", ai_engine: str = "") -> str:
    _CHARTS.clear()
    tz = ZoneInfo(SETTINGS.get("timezone", "Asia/Taipei"))
    now = datetime.now(tz)
    sections = (sec_ssi, sec_radar, sec_odds, None, sec_trends, sec_shock, sec_playbook_breaks, sec_macro,
                sec_positioning, sec_markets, sec_taiwan, sec_calendar, sec_news)
    grid = "".join(sec_ai(ai_text, ai_engine) if f is None else f(eng) for f in sections)
    strip, quality = sec_strip(eng), sec_quality(eng)
    data = json.dumps(_CHARTS, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    foot = T("資料來源：Yahoo Finance、FRED、CBOE、證交所／期交所、公開新聞 RSS。平日每小時、週末每 4 小時自動更新。所有數字由程式自動計算；崩跌機率是歷史頻率而非預測。本站僅提供市場資訊，不構成任何投資建議。",
             "Sources: Yahoo Finance, FRED, CBOE, TWSE/TAIFEX, public news RSS. Updated hourly on weekdays, every 4 hours on weekends. "
             "All figures are computed automatically; crash odds are historical frequencies, not forecasts. Market information only, not investment advice.")
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><meta name="color-scheme" content="dark light"><title>WallStreet Sentinel｜全球金融風險情報站</title>
<style>{CSS}</style></head><body>
<header class="top"><div class="bar"><div class="brand">WALLSTREET SENTINEL<small>{T("全球金融風險情報站", "Global financial risk intelligence")}</small></div>
<span class="live"><i></i>{T("更新於", "Updated")} {now:%Y-%m-%d %H:%M} {T("台北", "Taipei")}</span>
<button class="btn" id="langBtn" type="button" aria-label="language">EN</button><button class="btn" id="themeBtn" type="button" aria-label="theme">☀</button></div></header>
<main class="wrap">{strip}<div class="grid12">{grid}</div>{quality}<footer>{foot}</footer></main>
<div id="tip" role="status"></div>
<script type="application/json" id="chart-data">{data}</script><script>{JS}</script></body></html>'''


def snapshot(eng) -> dict:
    st = eng.stress
    return {
        "generated": datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds"),
        "ssi": None if not st else {"score": round(st.score, 2), "label": st.label, "chg_1d": st.chg_1d, "chg_5d": st.chg_5d,
                                    "chg_20d": st.chg_20d, "coverage": st.coverage, "blocks": st.blocks},
        "playbook": {k: (eng.playbook or {}).get(k) for k in ("stage", "name", "points")},
        "odds": (eng.odds or {}).get("horizons"),
    }


# ----------------------------------------------------------------- main
async def ai_commentary(eng) -> Tuple[str, str]:
    from wsb.ai import context, llm
    try:
        pack = context.build(eng, "full", private=False)
    except TypeError:                                            # older context.build without the public switch
        pack = context.build(eng, "full")
    text, name = await llm.complete(PUBLIC_SYSTEM, pack + "\n\n" + PUBLIC_BRIEF, 2600)
    if name == "none" or text.startswith("⚠️"):
        return "", ""
    return scrub_advice(text), name


async def build(out: Path, use_ai: bool = True, engine=None) -> Path:
    from wsb.engine import Engine
    eng = engine or Engine()
    if engine is None:
        await eng.bootstrap()
    assert not eng.holdings and not eng.portfolio.get("positions"), "intel-station build must not contain holdings"
    ai_text, ai_engine = "", ""
    if use_ai:
        try:
            ai_text, ai_engine = await ai_commentary(eng)
        except Exception as e:  # noqa: BLE001
            log.warning("AI commentary skipped: %s", e)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(render(eng, ai_text, ai_engine), encoding="utf-8")
    (out / "data.json").write_text(json.dumps(snapshot(eng), ensure_ascii=False, default=str, indent=1), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    return out / "index.html"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site")
    ap.add_argument("--no-ai", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    t0 = time.time()
    p = asyncio.run(build(Path(a.out), use_ai=not a.no_ai))
    print(f"wrote {p} ({p.stat().st_size / 1024:.0f} KB) in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
