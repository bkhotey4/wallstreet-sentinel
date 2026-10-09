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
from tools import site_sections as S2
from tools.sitekit import (WORD_EN, T, _CHARTS, card, cls, esc, line_chart, nice_ticks, num, spark,  # noqa: F401
                           tick_label)

# Intel-station mode is enforced here, whatever settings.yaml says: this site must never carry holdings.
SETTINGS.raw.setdefault("portfolio", {})["enabled"] = False

log = logging.getLogger("build_site")

# ----------------------------------------------------------------- vocabulary (中 → EN)
GROUP_EN = {"us_equity": ("美股指數", "US equities"), "volatility": ("波動率", "Volatility"), "europe": ("歐洲", "Europe"),
            "asia": ("亞洲", "Asia"), "emerging": ("新興市場", "Emerging"), "rates": ("利率／債券", "Rates"),
            "credit": ("信用", "Credit"), "fx": ("外匯", "FX"), "commodities": ("大宗商品", "Commodities"),
            "crypto": ("加密貨幣", "Crypto"), "sectors": ("美股類股", "Sectors")}
BLOCK_EN = {"信用": "Credit", "私募信貸": "Private credit", "全球新興": "Global EM", "匯率套息": "FX carry",
            "利率": "Rates", "波動率": "Volatility", "股市結構": "Equity structure", "流動性": "Liquidity",
            "商品加密": "Commodities & crypto", "景氣就業": "Growth & jobs"}
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

COMP_LABELS = {
    "hy_oas": ("高收益債利差 OAS", "HY OAS"), "baa_spread": ("Baa 公司債利差（長歷史）", "Baa − 10Y spread"), "ccc_oas": ("CCC 級利差", "CCC OAS"), "ig_oas": ("投資級利差 OAS", "IG OAS"),
    "hyg_ief": ("高收益債 vs 公債（20日）", "HYG vs IEF 20d"), "kre": ("區域銀行 vs 大盤（20日）", "Regional banks vs SPY"),
    "bizd": ("私募信貸 BDC vs 大盤", "BDCs vs SPY"), "loans": ("槓桿貸款 vs 公債", "Leveraged loans vs IEF"),
    "alt_bx": ("黑石 vs 大盤", "Blackstone vs SPY"), "alt_apo": ("阿波羅 vs 大盤", "Apollo vs SPY"), "alt_ares": ("Ares vs 大盤", "Ares vs SPY"),
    "vix_term": ("VIX 期限結構（VIX/VIX3M）", "VIX term structure"), "vix_level": ("VIX 水準", "VIX level"),
    "vvix": ("VVIX 波動率的波動率", "VVIX"), "move": ("MOVE 美債波動率", "MOVE index"), "vix_short": ("短天期恐慌（VIX9D/VIX）", "VIX9D / VIX"),
    "spx_rvol": ("標普 20日實現波動", "S&P 20d realized vol"), "nfci": ("芝加哥金融狀況指數", "Chicago NFCI"),
    "stlfsi": ("聖路易金融壓力指數", "St. Louis FSI"), "net_liq": ("聯準會淨流動性（63日）", "Fed net liquidity 63d"),
    "reserves": ("銀行準備金（63日）", "Bank reserves 63d"), "us2y_drop": ("2年殖利率急跌（20日）", "2Y yield drop 20d"),
    "curve_steep": ("10年-3月利差變化（63日）", "10Y-3M curve change 63d"), "real_yield": ("10年實質利率變化（63日）", "10Y real yield 63d"),
    "long_bond": ("30年殖利率變化（20日）", "30Y yield change 20d"), "dxy": ("美元指數（20日）", "DXY 20d"),
    "yen_carry": ("美元/日圓（10日）", "USD/JPY 10d"), "audjpy": ("澳幣/日圓（10日）", "AUD/JPY 10d"), "cnh": ("美元/人民幣（20日）", "USD/CNY 20d"),
    "spx_trend": ("標普距 200日線", "S&P vs 200d MA"), "breadth": ("等權重 vs 市值加權（60日）", "Equal vs cap weight 60d"),
    "correlation": ("類股同漲同跌程度（20日）", "Sector correlation 20d"), "ai_leaders": ("半導體 vs 大盤（20日）", "Semis vs SPY 20d"),
    "em_debt": ("新興市場債 vs 公債", "EM debt vs IEF"), "eu_banks": ("歐洲金融股 vs 大盤", "EU financials vs SPY"),
    "copper_gold": ("銅金比（60日）", "Copper/gold 60d"), "krw": ("美元/韓元（20日）", "USD/KRW 20d"),
    "oil_shock": ("布蘭特原油（20日）", "Brent 20d"), "btc": ("比特幣（20日）", "Bitcoin 20d"), "gold_bid": ("黃金 vs 標普（20日）", "Gold vs S&P 20d"),
    "claims": ("初領失業金（63日）", "Jobless claims 63d"), "sahm": ("薩姆衰退指標", "Sahm rule"), "small_caps": ("小型股 vs 大盤（60日）", "Small caps vs SPY 60d"),
}

# status palette (fixed, never themed) — always shown next to a text label, never colour alone
LEVEL_COLORS = ["#0ca30c", "#fab219", "#ec835a", "#d03b3b", "#a3142f"]
STAGE_COLORS = ["#0ca30c", "#fab219", "#ec835a", "#d03b3b"]


# ----------------------------------------------------------------- number helpers
def level_idx(score) -> int:
    for i, lv in enumerate(SETTINGS.get("stress_levels", [])):
        if score < lv["max"]:
            return min(i, len(LEVEL_COLORS) - 1)
    return len(LEVEL_COLORS) - 1


def data_asof(eng) -> Tuple[Optional[str], bool]:
    """Newest quote date among the headline tickers, and whether it is stale (> 4 calendar days, i.e. older
    than a long weekend) — the page must say when its numbers are from, not only when it was built."""
    ds = [(eng.market.q(t) or {}).get("asof") for t, _, _ in STRIP if not t.endswith("-USD")]
    ds = [d for d in ds if d]
    if not ds:
        return None, True
    last = max(ds)
    ny = datetime.now(ZoneInfo("America/New_York")).date()
    return last, (ny - datetime.fromisoformat(last).date()).days > 4


def ret_since(s, days: int) -> Optional[float]:
    s = s.dropna()
    if s.empty:
        return None
    past = s[s.index <= s.index[-1] - pd.Timedelta(days=days)]
    return (float(s.iloc[-1]) / float(past.iloc[-1]) - 1) * 100 if len(past) and past.iloc[-1] else None


# ----------------------------------------------------------------- charts (inline SVG + JSON for the hover layer)
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
def sec_strip(eng) -> str:
    tiles = []
    for t, zh, dg in STRIP:
        q = eng.market.q(t)
        s = eng.market.series(t)
        if not q and s.empty:
            continue
        price = q["price"] if q else float(s.iloc[-1])
        chg = q.get("chg_pct") if q else None
        asof = q.get("asof") if q else s.dropna().index[-1].strftime("%Y-%m-%d")
        tiles.append(f'<div class="tile" title="{esc(asof)}"><div class="tl">{T(zh, ASSET_EN.get(t, t))}<span class="asof">{esc(asof[5:])}</span></div>'
                     f'<div class="tv">{num(price, dg)}</div><div class="tc {cls(chg)}">{num(chg, 2, sign=True, pct=True)}</div>{spark(s)}</div>')
    return f'<div class="strip" aria-label="market strip">{"".join(tiles)}</div>'


def sec_ssi(eng) -> str:
    st = eng.stress
    if not st:
        return card("系統性壓力指數 SSI", "Systemic Stress Index", '<p class="muted">—</p>', "ssi")
    col = LEVEL_COLORS[level_idx(st.score)]
    pb = eng.playbook or {}
    stg = pb.get("stage")
    sc = STAGE_COLORS[min(int(stg), 3)] if stg is not None else "#6b7280"
    miss = pb.get("missing") or ([] if pb else ["風險劇本"])
    warn = (f'<div class="miss">⚠ {T("資料不足：" + "、".join(miss), "Incomplete inputs: " + ", ".join(miss))}</div>') if miss else ""
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
<div class="stage" style="--sc:{sc}"><div class="sl">{T("風險階段", "Risk stage")}</div>
<div class="sv">{esc(pb.get("emoji", ""))} {T(str(pb.get("name", "—")))}</div><div class="muted">{T("風險分", "Score")} {pb.get("points", "—")}</div>{warn}</div></div>
<div class="gauge"><div class="track">{segs}<b style="left:{min(st.score, 100):.1f}%"></b></div></div>
{chart}<p class="note">{note}</p></section>'''


def sec_radar(eng) -> str:
    st = eng.stress
    if not st or not st.blocks:
        return ""
    nb = len(st.blocks)
    note = T(f"{nb} 個風險區塊的壓力分數（0–100）；越往外越緊張，粗線圈為 50。",
             f"Stress score of {nb} risk blocks (0–100); further out = tighter, bold ring = 50.")
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
            + (f'<td class="r"><div class="pos" title="{num(r.get("pct_52w"), 0)}%"><i style="left:{min(max(r["pct_52w"], 0), 100):.0f}%"></i></div></td></tr>'
               if r.get("pct_52w") is not None else '<td class="r muted">—</td></tr>')
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


SENTIMENT = [("cnn_fng", "CNN 恐懼與貪婪", "CNN Fear & Greed", "{:.0f}", "cnn_fng_label"),
             ("crypto_fng", "加密恐懼與貪婪", "Crypto Fear & Greed", "{:.0f}", "crypto_fng_label"),
             ("total_mcap_usd", "加密總市值", "Crypto market cap", "money", None),
             ("btc_dominance", "比特幣市占", "BTC dominance", "{:.1f}%", None),
             ("BTC_funding_ann_pct", "BTC 永續資金費率（年化）", "BTC perp funding (ann.)", "{:+.1f}%", None),
             ("stablecoin_chg_30d_pct", "穩定幣供給 30 日變化", "Stablecoin supply 30d", "{:+.2f}%", None)]


def _money(v) -> str:
    a = abs(v)
    return f"${v / 1e12:.2f}T" if a >= 1e12 else f"${v / 1e9:.0f}B" if a >= 1e9 else f"${v / 1e6:.0f}M"


def sec_positioning(eng) -> str:
    cd = eng.crypto.data or {}
    cells = []
    for key, zh, en, fmt, lab in SENTIMENT:
        v = cd.get(key)
        if not isinstance(v, (int, float)) or v != v:
            continue
        txt = _money(v) if fmt == "money" else fmt.format(v)
        extra = f' <span class="muted small">{esc(str(cd.get(lab)))}</span>' if lab and cd.get(lab) else ""
        cells.append(f'<div><span class="muted">{T(zh, en)}</span><b>{esc(txt)}</b>{extra}</div>')
    if not cells:
        return ""
    return card("市場情緒", "Sentiment", f'<div class="kv">{"".join(cells)}</div>', "span4")


def sec_gamma(eng) -> str:
    op = eng.options.spx or {}
    if not op:
        return card("Gamma 雷達（SPX 選擇權）", "Gamma radar (SPX options)", f'<p class="muted">{T("CBOE 資料暫時取不到", "CBOE data unavailable")}</p>', "wide")
    gex, flip, spot = op.get("gex_usd_bn_per_1pct"), op.get("zero_gamma"), op.get("spot")
    regime = (T("正 Gamma：造市商傾向「逢高賣、逢低買」，波動被壓抑", "Positive gamma: dealers sell rallies / buy dips — volatility dampened")
              if (gex or 0) > 0 else T("負 Gamma：造市商傾向「追漲殺跌」，波動容易被放大", "Negative gamma: dealers chase moves — volatility amplified"))
    kv = (f'<div class="kv"><div><span class="muted">GEX（十億美元／每 1%）</span><b class="{cls(gex)}">{num(gex, 2, sign=True)}</b></div>'
          f'<div><span class="muted">{T("零 Gamma 翻轉點", "Zero-gamma flip")}</span><b>{num(flip, 0)}</b> <span class="small {cls(op.get("spot_vs_flip_pct"))}">{num(op.get("spot_vs_flip_pct"), 1, sign=True, pct=True)}</span></div>'
          f'<div><span class="muted">SPX</span><b>{num(spot, 0)}</b></div>'
          f'<div><span class="muted">{T("Call 牆（壓力）", "Call wall")}</span><b>{num(op.get("call_wall"), 0)}</b></div>'
          f'<div><span class="muted">{T("Put 牆（支撐）", "Put wall")}</span><b>{num(op.get("put_wall"), 0)}</b></div>'
          f'<div><span class="muted">P/C（OI／量）</span><b>{num(op.get("put_call_oi"), 2)} / {num(op.get("put_call_volume"), 2)}</b></div></div>'
          f'<p><b>{regime}</b></p>')
    # profile: GEX if SPX moved to x
    prof = op.get("profile") or []
    chart1 = ""
    if len(prof) > 10:
        ps = pd.Series([y for _, y in prof], index=pd.Index([x for x, _ in prof]))
        chart1 = gex_profile_svg("c_gexp", ps, spot, flip)
    bars = strike_bars_svg("c_gexs", op.get("by_strike") or [], spot, op.get("call_wall"), op.get("put_wall"))
    note = T("資料：CBOE 延遲報價（約 15 分鐘），60 天內到期合約；慣例假設造市商持有客戶賣出的 Call、買入的 Put（業界常用但不一定準確）。"
             "零 Gamma 翻轉點以下，市場對壞消息的反應通常更劇烈。" + (" 更新 " + str(op.get("asof")) if op.get("asof") else ""),
             "CBOE delayed quotes (~15 min), expiries within 60 days; assumes dealers are long calls / short puts (a common convention, not certain). "
             "Below the zero-gamma flip, markets tend to react more violently.")
    body = (kv + f'<div class="g2"><div><h3>{T("如果 SPX 移動到這個價位，造市商 Gamma 會是多少", "Dealer gamma if SPX moved to this level")}</h3>{chart1}</div>'
            f'<div><h3>{T("各履約價的造市商淨 Gamma（現價 ±8%）", "Net dealer gamma by strike (±8%)")}</h3>{bars}</div></div><p class="note">{note}</p>')
    return card("Gamma 雷達（SPX 選擇權）", "Gamma radar (SPX options)", body, "wide")


def gex_profile_svg(cid, ps, spot, flip, w=560, h=220) -> str:
    pl, pr, pt, pb = 52, 16, 12, 26
    W, H = w - pl - pr, h - pt - pb
    xs, ys = list(ps.index.astype(float)), list(ps.values.astype(float))
    x0, x1 = min(xs), max(xs)
    lo, hi = min(min(ys), 0), max(max(ys), 0)
    pad = (hi - lo) * 0.08 or 1
    lo, hi = lo - pad, hi + pad
    X = lambda v: pl + (v - x0) / (x1 - x0) * W           # noqa: E731
    Y = lambda v: pt + (1 - (v - lo) / (hi - lo)) * H      # noqa: E731
    pts = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in zip(xs, ys))
    parts = [f'<line x1="{pl}" x2="{pl + W}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" class="zero"/>']
    for t in nice_ticks(lo, hi, 4):
        if lo <= t <= hi:
            parts.append(f'<text x="{pl - 6}" y="{Y(t) + 4:.1f}" class="axis" text-anchor="end">{tick_label(t)}</text>')
    for v, lab, c in ((spot, "SPX", "var(--tx)"), (flip, "Flip", "var(--warn)")):
        if v and x0 <= v <= x1:
            parts.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{pt}" y2="{pt + H}" style="stroke:{c};stroke-dasharray:0" class="mk"/>'
                         f'<text x="{X(v) + 4:.1f}" y="{pt + 11}" class="spanlbl">{lab} {v:,.0f}</text>')
    parts.append(f'<polyline points="{pts}" class="gln"/>')
    for t in (x0, (x0 + x1) / 2, x1):
        parts.append(f'<text x="{X(t):.1f}" y="{h - 6}" class="axis" text-anchor="middle">{t:,.0f}</text>')
    _CHARTS[cid] = {"label": "GEX", "d": [f"SPX {a:,.0f}" for a in xs], "v": [round(b, 3) for b in ys],
                    "x": [round(X(a), 1) for a in xs], "y": [round(Y(b), 1) for b in ys], "dg": 2}
    parts.append(f'<g class="hover" visibility="hidden"><line class="xh" y1="{pt}" y2="{pt + H}"/><circle r="4" class="dot"/></g>'
                 f'<rect class="hit" x="{pl}" y="{pt}" width="{W}" height="{H}" fill="transparent"/>')
    return f'<svg id="{cid}" class="chart lc" viewBox="0 0 {w} {h}" role="img" aria-label="GEX profile">{"".join(parts)}</svg>'


def strike_bars_svg(cid, rows, spot, cw, pw, w=560, h=220) -> str:
    if not rows:
        return '<p class="muted">—</p>'
    pl, pr, pt, pb = 52, 10, 12, 26
    W, H = w - pl - pr, h - pt - pb
    vals = [v for _, v in rows]
    m = max(abs(min(vals)), abs(max(vals))) or 1
    Y = lambda v: pt + (1 - (v + m) / (2 * m)) * H         # noqa: E731
    bw = max(1.5, W / len(rows) - 1)
    parts = [f'<line x1="{pl}" x2="{pl + W}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" class="zero"/>',
             f'<text x="{pl - 6}" y="{Y(m) + 8:.1f}" class="axis" text-anchor="end">{tick_label(m)}</text>',
             f'<text x="{pl - 6}" y="{Y(-m):.1f}" class="axis" text-anchor="end">{tick_label(-m)}</text>']
    for i, (k, v) in enumerate(rows):
        x = pl + i * W / len(rows)
        y0, y1 = sorted((Y(0), Y(v)))
        col = "var(--ac)" if v >= 0 else "var(--dn)"
        parts.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(y1 - y0, 0.5):.1f}" fill="{col}" rx="1"/>'
                     f'<rect x="{x:.1f}" y="{pt}" width="{max(bw, 4):.1f}" height="{H}" fill="transparent" class="thit" '
                     f'data-tip="{v:+.2f} bn|{k:,.0f}"/>')
    for k, lab in ((spot, "SPX"), (cw, "Call"), (pw, "Put")):
        if k and rows[0][0] <= k <= rows[-1][0]:
            i = min(range(len(rows)), key=lambda j: abs(rows[j][0] - k))
            x = pl + (i + 0.5) * W / len(rows)
            parts.append(f'<text x="{x:.1f}" y="{h - 6}" class="axis" text-anchor="middle">{lab} {k:,.0f}</text>')
    return f'<svg id="{cid}" class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="gamma by strike">{"".join(parts)}</svg>'


DP_EN = {"偏買（場外放空比例高）": "Buy-side pressure (high off-exchange short share)",
         "偏賣（場外放空比例低）": "Sell-side pressure (low off-exchange short share)", "中性": "Neutral"}


def sec_darkpool(eng) -> str:
    dp = (getattr(eng, "darkpool", None) and eng.darkpool.result) or {}
    if not dp.get("available"):
        return card("暗池指數（場外放空量）", "Dark-pool index (off-exchange short volume)",
                    f'<p class="muted">{T("FINRA 資料暫時取不到或累積天數不足", "FINRA data unavailable or not enough history yet")}</p>', "wide")
    etf = dp.get("etf") or {}
    kv = (f'<div class="kv"><div><span class="muted">{T("暗池指數（30 檔大型股）", "Dark-pool index (30 large caps)")}</span><b>{dp["dpi"]:.1f}%</b></div>'
          f'<div><span class="muted">{T("5 日平均", "5-day avg")}</span><b>{dp["dpi_5d"]:.1f}%</b></div>'
          f'<div><span class="muted">{T("5 日平均的歷史百分位", "5d avg percentile")}（{dp["n_days"]} {T("天", "d")}）</span><b>{num(dp.get("pctile"), 0)}</b></div>'
          + "".join(f'<div><span class="muted">{esc(e)}</span><b>{num(v, 1)}%</b></div>' for e, v in etf.items() if v is not None)
          + f'</div><p><b>{T(str(dp.get("state") or "累積天數不足，暫不判斷"), DP_EN.get(dp.get("state"), "Not enough history yet"))}</b></p>')
    hist = dp.get("history")
    chart = line_chart("c_dpi", hist, "DPI %", 1, w=1100, h=210) if hist is not None and len(hist) >= 10 else ""
    note = T(f"資料：FINRA 每日 Reg SHO 場外成交（含暗池、券商內部撮合）的放空量比例，T+1 公布，資料日 {dp['asof']}。"
             "做法類似 SqueezeMetrics 的 DIX：買家在場外成交時，造市商通常以放空方式供貨，所以「放空比例偏高」反而代表買盤偏強、偏低代表賣壓。"
             "這是代理指標，不是真正的暗池委託單；歷史只涵蓋本站已累積的天數，會逐日變長。",
             f"Source: FINRA daily Reg SHO off-exchange short volume (T+1), as of {dp['asof']}. Same idea as SqueezeMetrics' DIX: a HIGH short "
             "share off-exchange usually reflects dealers filling buyers. A proxy, not actual dark-pool orders; history grows daily.")
    return card("暗池指數（場外放空量）", "Dark-pool index (off-exchange short volume)", kv + chart + f'<p class="note">{note}</p>', "wide")


def sec_taiwan_trends(eng) -> str:
    cells = []
    for i, (t, zh, dg) in enumerate((("^TWII", "台股加權", 0), ("2330.TW", "台積電", 0), ("TWD=X", "美元/台幣", 3), ("EWT", "台灣 ETF（美股盤）", 2))):
        s = eng.market.series(t)
        if s.empty:
            continue
        q = eng.market.q(t)
        chg = q.get("chg_pct") if q else None
        cells.append(f'<div class="trend"><div class="th"><b>{T(zh, ASSET_EN.get(t, t))}</b><span class="muted">{T("今日", "1D")} '
                     f'<span class="{cls(chg)}">{num(chg, 2, sign=True, pct=True)}</span></span></div>{line_chart(f"c_tw{i}", s.tail(260), ASSET_EN.get(t, t), dg)}</div>')
    return card("台股走勢", "Taiwan trends", f'<div class="g2">{"".join(cells)}</div>', "wide") if cells else ""


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


# ----------------------------------------------------------------- 42 indicators / crises / valuation
def fmt_raw(x) -> str:
    if x is None or x != x:
        return "—"
    a = abs(x)
    if a >= 1000:
        return f"{x:,.0f}"
    if a >= 1:
        return f"{x:,.2f}"
    return f"{x:.4f}"


def sec_indicators(eng) -> str:
    st = eng.stress
    if not st or not st.components:
        return ""
    order = sorted(st.blocks, key=lambda b: -(st.blocks.get(b) or 0))
    by: Dict[str, list] = {}
    for c in st.components:
        by.setdefault(c.block, []).append(c)
    cells = []
    for b in order + [k for k in by if k not in order]:
        comps = sorted(by.get(b, []), key=lambda c: -(c.score if c.score is not None else -1))
        if not comps:
            continue
        rows = ""
        for c in comps:
            zh, en = COMP_LABELS.get(c.id, (c.id, c.id))
            if c.score is None:
                stt = str(c.status).split(":")[0]
                rows += (f'<tr class="off"><td>{T(zh, en)}</td><td class="r muted">—</td><td class="r muted">—</td>'
                         f'<td colspan="2" class="muted small">{T("未納入：" + stt, "excluded: " + stt)}</td></tr>')
                continue
            col = LEVEL_COLORS[level_idx(c.score)]
            rows += (f'<tr><td>{T(zh, en)}</td><td class="r">{fmt_raw(c.raw)}</td><td class="r {cls(c.z)}">{num(c.z, 1, sign=True)}</td>'
                     f'<td class="r"><b>{c.score:.0f}</b></td><td><div class="meter"><i style="width:{min(c.score, 100):.0f}%;background:{col}"></i></div></td></tr>')
        bs = st.blocks.get(b)
        head = f'{T(b, BLOCK_EN.get(b))} <span class="muted">{"—" if bs is None else f"{bs:.0f}"}</span>'
        cells.append(f'<div class="blk"><h3>{head}</h3><table><thead><tr><th>{T("指標", "Indicator")}</th><th class="r">{T("數值", "Raw")}</th>'
                     f'<th class="r">z</th><th class="r">{T("分數", "Score")}</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>')
    live = sum(1 for c in st.components if c.score is not None)
    note = T(f"共 {len(st.components)} 項指標，本次納入 {live} 項。z ＝ 與自身近 3 年常態相比偏離幾個標準差（已依「越高越危險」的方向調整），分數 0–100、50 為常態；"
             f"「未納入」代表資料缺或過期，不會被當成 50 分。",
             f"{len(st.components)} indicators, {live} live. z = standard deviations from the indicator's own 3-year norm (signed so higher = riskier); "
             f"score 0–100 with 50 = normal. Excluded inputs are never treated as 50.")
    return card("壓力指數的全部指標", "Every indicator behind the SSI", f'<div class="g2">{"".join(cells)}</div><p class="note">{note}</p>', "wide")


CRISIS_ASSETS = [("^GSPC", "標普", "S&P", "pct"), ("^TNX", "美債10年", "US 10Y", "bp"), ("DX-Y.NYB", "美元", "USD", "pct"),
                 ("GC=F", "黃金", "Gold", "pct"), ("^HSI", "恆生", "Hang Seng", "pct"), ("^N225", "日經", "Nikkei", "pct"),
                 ("^KS11", "韓國", "KOSPI", "pct"), ("^TWII", "台股", "TAIEX", "pct")]


def _window_move(s, a, b, kind):
    s = s.dropna()
    if s.empty:
        return None
    a, b = pd.Timestamp(a), pd.Timestamp(b)
    s0, s1 = s[s.index <= a], s[s.index <= b]
    if not len(s0) or not len(s1) or (a - s0.index[-1]).days > 7:
        return None
    v0, v1 = float(s0.iloc[-1]), float(s1.iloc[-1])
    return (v1 - v0) * 100 if kind == "bp" else ((v1 / v0 - 1) * 100 if v0 else None)


def _mv_cell(v, kind):
    if v is None:
        return '<td class="r muted">—</td>'
    txt = f"{v:+.0f}bp" if kind == "bp" else f"{v:+.1f}%"
    return f'<td class="r {cls(v)}">{txt}</td>'


def sec_crisis(eng) -> str:
    st = eng.stress
    scen = sorted(SETTINGS.get("stress_scenarios", []), key=lambda x: str(x["start"]))
    if not scen:
        return ""
    ssi = st.history.dropna() if st else pd.Series(dtype=float)
    bh = st.block_history if st is not None else pd.DataFrame()
    marks = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
    rows, spans = [], []
    for k, sc in enumerate(scen):
        a, b = sc["start"], sc["end"]
        mk = marks[k] if k < len(marks) else str(k + 1)
        cells = "".join(_mv_cell(_window_move(eng.market.series(t), a, b, kind), kind) for t, _, _, kind in CRISIS_ASSETS)
        win = ssi[(ssi.index >= pd.Timestamp(a)) & (ssi.index <= pd.Timestamp(b))]
        if len(win):
            pk = win.idxmax()
            before = ssi[ssi.index <= pd.Timestamp(a)]
            pre = f"{before.iloc[-21]:.0f}" if len(before) > 21 else "—"
            tops = bh.loc[:pk].iloc[-1].dropna().sort_values(ascending=False).head(3) if len(bh) else pd.Series(dtype=float)
            topb = "、".join(f"{x}" for x in tops.index)
            ssi_cells = f'<td class="r">{pre}</td><td class="r"><b>{win.max():.0f}</b></td><td class="small">{esc(topb)}</td>'
            spans.append((a, b, mk))
        else:
            ssi_cells = f'<td class="r muted" colspan="3">{T("壓力指數尚未涵蓋（資料不足）", "SSI not available for this period")}</td>'
        rows.append(f'<tr><td class="nw">{mk} {esc(sc["name"])}</td><td class="small muted nw">{esc(a)} → {esc(b)}</td>{cells}{ssi_cells}</tr>')
    # today: last 20 trading days, for scale
    today_cells = ""
    for t, _, _, kind in CRISIS_ASSETS:
        s = eng.market.series(t).dropna()
        v = None
        if len(s) > 21:
            v = (float(s.iloc[-1]) - float(s.iloc[-21])) * 100 if kind == "bp" else (float(s.iloc[-1]) / float(s.iloc[-21]) - 1) * 100
        today_cells += _mv_cell(v, kind)
    if st:
        tops = sorted(st.blocks.items(), key=lambda kv: -kv[1])[:3]
        today_cells += (f'<td class="r">{ssi.iloc[-21]:.0f}</td>' if len(ssi) > 21 else '<td class="r">—</td>') + \
            f'<td class="r"><b>{st.score:.0f}</b></td><td class="small">{esc("、".join(k for k, _ in tops))}</td>'
    rows.append(f'<tr class="today"><td class="nw"><b>{T("今天（近 20 日）", "Today (last 20d)")}</b></td><td></td>{today_cells}</tr>')
    head = "".join(f'<th class="r">{T(zh, en)}</th>' for _, zh, en, _ in CRISIS_ASSETS)
    table = (f'<div class="scroll"><table class="crisis"><thead><tr><th>{T("危機", "Crisis")}</th><th>{T("期間", "Window")}</th>{head}'
             f'<th class="r">{T("事前 SSI", "SSI before")}</th><th class="r">{T("期間最高 SSI", "Peak SSI")}</th><th>{T("當時最緊張區塊", "Hottest blocks")}</th>'
             f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    chart = ""
    if len(ssi) > 50:
        wk = ssi.resample("W-FRI").last().dropna()
        lv = SETTINGS.get("stress_levels", [])
        bands, prev = [], 0.0
        for i, l in enumerate(lv):
            bands.append((prev, min(l["max"], 100), LEVEL_COLORS[min(i, 4)]))
            prev = min(l["max"], 100)
        chart = line_chart("c_ssi_all", wk, "SSI", 1, w=1100, h=230, bands=bands, fixed=(0, 100), spans=spans)
    # every ≥10% S&P drawdown the SSI covers: did it warn before the peak?
    ql = ((eng.shock or {}).get("quality") or {})
    eps = ql.get("episodes") or []
    ep_rows = "".join(
        f'<tr><td class="nw">{esc(e["peak"])} → {esc(e["trough"])}</td><td class="r dn">{e["depth_pct"]:.1f}%</td>'
        f'<td class="r">{e["ssi_at_peak"]:.0f}</td><td class="r">{num(e.get("ssi_max_pre"), 0)}</td>'
        f'<td class="nw">{esc(e["first_warn"] or "—")}</td>'
        f'<td class="r">{"—" if e.get("lead_days") is None else (str(e["lead_days"]) + T(" 天", " d"))}</td>'
        f'<td>{T("✓ 高點前已預警", "✓ before the peak") if e.get("warned_before_peak") else (T("期間才預警", "during the fall") if e.get("first_warn") else T("✗ 未預警", "✗ missed"))}</td></tr>'
        for e in eps)
    es = ql.get("episode_summary") or {}
    ep = ""
    if ep_rows:
        summ = T(f"共 {es.get('n', len(eps))} 次，高點前已預警 {es.get('warned_before_peak', 0)} 次"
                 + (f"，領先中位數 {es['median_lead_days']:.0f} 個交易日" if es.get("median_lead_days") is not None else ""),
                 f"{es.get('n', len(eps))} episodes, warned before the peak {es.get('warned_before_peak', 0)} times")
        ep = (f'<h3>{T("壓力指數有沒有提前預警？（標普每次回檔 ≥10%）", "Did the SSI warn ahead of each ≥10% S&P drawdown?")}</h3><p class="small">{summ}</p>'
              f'<div class="scroll"><table><thead><tr><th>{T("高點 → 低點", "Peak → trough")}</th><th class="r">{T("跌幅", "Fall")}</th>'
              f'<th class="r">{T("高點時 SSI", "SSI at peak")}</th><th class="r">{T("高點前最高 SSI", "Max SSI before")}</th><th>{T("首次警示", "First warning")}</th>'
              f'<th class="r">{T("領先", "Lead")}</th><th>{T("結果", "Result")}</th></tr></thead><tbody>{ep_rows}</tbody></table></div>')
    note = T("各資產欄位是危機期間的漲跌（美債 10 年為殖利率變化，bp）；「—」代表當時還沒有該資料。壓力指數需要足夠多的指標才計算，"
             "大約自 2003 年起才有數值，1997、2000 年的危機只能看資產表現。今天那一列是近 20 個交易日，方便和歷次危機比較強度。",
             "Asset columns show the move during each crisis (US 10Y = yield change in bp); '—' = no data then. The SSI needs enough inputs "
             "and starts around 2003, so 1997/2000 show asset moves only. The 'today' row is the last 20 trading days for scale.")
    return card("歷史危機對照：金融海嘯、亞洲金融風暴與歷次崩盤", "Past crises: GFC, Asian crisis and other crashes",
                chart + table + f'<p class="note">{note}</p>' + ep, "wide")


VAL_COLORS = {"極端": "#d03b3b", "偏熱": "#ec835a", "正常": "#6b7280", "偏冷": "#3987e5", "資料缺": "#6b7280",
              "恐慌": "#d03b3b", "緊張": "#ec835a", "自滿": "#fab219", "極度自滿": "#fab219"}
VAL_EN = {"極端": "Extreme", "偏熱": "Hot", "正常": "Normal", "偏冷": "Cool", "資料缺": "n/a",
          "恐慌": "Panic", "緊張": "Stressed", "自滿": "Complacent", "極度自滿": "Very complacent"}


def sec_valuation(eng) -> str:
    val = getattr(eng, "valuation", None) or {}
    if not val.get("available"):
        return ""
    cols = []
    for g in val["groups"]:
        if not g["items"]:
            continue
        rows = ""
        for i in g["items"]:
            v = "—" if i["value"] is None else (f'{i["value"]:.2f}{i["unit"]}' if i["unit"] != "%" or abs(i["value"]) < 1000 else f'{i["value"]:,.0f}%')
            p = i["pctile"]
            mark = f'<i style="left:{p:.0f}%"></i>' if p is not None else ""
            c = VAL_COLORS.get(i["grade"], "#6b7280")
            extra = ""
            if i.get("estimate") is not None:
                extra = T(f"（{i['quarter'][:7]} 季資料 {i['reported']:.2f}，依標普漲跌推估至今）",
                          f"(Q data {i['quarter'][:7]}: {i['reported']:.2f}, rolled forward with the S&P)")
            elif i.get("asof"):
                extra = f'<span class="muted">（{esc(i["asof"])}）</span>'
            rows += (f'<div class="vrow"><div class="vh"><b>{T(i["label"], i["label_en"])}</b>'
                     f'<span class="pill"><i class="sw" style="background:{c}"></i>{T(i["grade"], VAL_EN.get(i["grade"]))}</span></div>'
                     f'<div class="vv"><span class="vnum">{v}</span><span class="small muted">{T("歷史百分位", "Hist. pct")} '
                     f'{"—" if p is None else f"{p:.0f}"}（{T("自", "since")} {esc(str(i["hist_start"]))}）</span></div>'
                     f'<div class="pct">{mark}</div><p class="small muted">{esc(i["what"])} {extra}</p></div>')
        cols.append(f'<div><h3>{T(g["title"], g["title_en"])}</h3>{rows}</div>')
    note = T("這些是「慢變數」：告訴你市場貴不貴、底層信用是否在惡化，但無法告訴你何時反轉——2000 年與 2021 年的估值高點都撐了很久。"
             "百分位是和各指標自己的歷史相比；季資料約晚 10 週公布。",
             "Slow variables: they say how stretched things are and whether credit is deteriorating, not when it turns. "
             "Percentiles are versus each series' own history; quarterly data lag about 10 weeks.")
    return card("估值與泡沫觀察", "Valuation & bubble watch", f'<div class="g3">{"".join(cols)}</div><p class="note">{note}</p>', "wide",
                sub=T("巴菲特指標、信用週期與投機熱度", "Buffett indicator, credit cycle and speculation"))



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
    note = T("AUC 0.5 ＝ 隨機、1.0 ＝ 完美；≥0.65 有鑑別力、0.55–0.65 偏弱、<0.55 接近隨機。請把本站當風險溫度計，而不是預測器。",
             "AUC 0.5 = random, 1.0 = perfect; ≥0.65 useful, 0.55–0.65 weak, <0.55 near random. Treat this as a risk thermometer, not a forecaster.")
    body = (f'<div class="scroll"><table><thead><tr><th>{T("情境", "Horizon")}</th><th class="r">{T("樣本外 AUC", "OOS AUC")}</th>'
            f'<th>{T("鑑別力", "Verdict")}</th></tr></thead><tbody>{rows}</tbody></table></div><ul class="lines">{lis}</ul>'
            f'<p>{T("資料源", "Data sources")} <b>{ok}/{len(HEALTH.sources)}</b> {T("正常", "OK")}{badh}</p><p class="note">{note}</p>')
    return card("模型可信度與資料健康", "Model credibility & data health", body, "wide")


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
5. 一律使用台灣繁體中文與台灣用語，語氣冷靜精準；金融術語可保留英文。
6. 個股評分、大師 13F 持倉、內部人申報只能當作「市場正在發生什麼」來描述（哪些族群強、誰上季新建倉或出清），不得暗示讀者跟進或據此操作。"""

PUBLIC_BRIEF = """根據 DATA PACK 撰寫今日的公開市場評論（Markdown，總長 ≤ 1800 字），結構如下：

**一句話結論**（今天市場最重要的一件事＋整體風險溫度）

**風險儀表**（SSI 與最主要的 3 個推升因子，附數據；崩跌機率相對基準的意義）

**跨資產掃描**（只挑有訊號的市場：美股與類股輪動、美債曲線與標售、信用、匯率、商品、加密、亞洲與台股）

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
.tl{color:var(--mu);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;justify-content:space-between;gap:6px}.tv{font-size:18px;font-weight:700;margin-top:2px}.tc{font-size:12px;font-variant-numeric:tabular-nums}
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
.lc .span{fill:var(--warn);opacity:.13}.spanlbl{fill:var(--tx2);font-size:11px}
.live.stale i{background:var(--mu)}.live.stale{color:var(--warn)}.asof{color:var(--mu);font-size:11px;margin-left:4px}
.miss{margin-top:6px;font-size:11.5px;color:var(--warn);max-width:220px}
.blk h3{margin:6px 0 4px;color:var(--tx)}.blk table{font-size:12.5px}.blk td,.blk th{padding:4px 6px}.blk tr.off td{opacity:.7}
table.crisis td,table.crisis th{padding:6px 6px;font-size:12.5px}.scroll table.crisis{min-width:1000px}.nw{white-space:nowrap}tr.today td{background:var(--card2)}
.g3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.vrow{padding:8px 0;border-bottom:1px solid var(--bd)}
.vh{display:flex;justify-content:space-between;gap:8px;align-items:center}.vv{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:2px 0 4px}
.vnum{font-size:18px;font-weight:700}.pct{position:relative;height:6px;border-radius:99px;margin:4px 0;
background:var(--card2)}
.pct i{position:absolute;top:-4px;width:3px;height:14px;background:var(--tx);border-radius:2px;transform:translateX(-1px)}
.pnav{border-top:1px solid var(--bd)}
.pbar{max-width:1320px;margin:0 auto;padding:0 16px;display:flex;gap:4px;overflow-x:auto;scrollbar-width:none}.pbar::-webkit-scrollbar{display:none}
.ptab{white-space:nowrap;padding:10px 12px;color:var(--tx2);text-decoration:none;border-bottom:2px solid transparent;font-size:13.5px}
.ptab:hover{color:var(--tx);text-decoration:none}.ptab.on{color:var(--tx);border-bottom-color:var(--ac);font-weight:700}
.page{display:none}.page.on{display:block}
.chart .zero{stroke:var(--axis);stroke-width:1}.chart .mk{stroke-width:1}.gln{fill:none;stroke:var(--ac);stroke-width:2}.thit{cursor:crosshair}
#tip{position:fixed;z-index:9;pointer-events:none;background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:6px 9px;font-size:12px;box-shadow:0 6px 18px rgba(0,0,0,.35);display:none}
#tip b{display:block;font-size:14px;color:var(--tx)}#tip span{color:var(--mu)}
footer{color:var(--mu);font-size:12px;padding:16px 0 0;border-top:1px solid var(--bd);margin-top:16px}
@media(max-width:1100px){.card.ssi{grid-column:span 12}.card.span3{grid-column:span 6}.card.span4{grid-column:span 6}.card.span8{grid-column:span 12}}
@media(max-width:1100px){.g3{grid-template-columns:1fr 1fr}}
@media(max-width:760px){.g3{grid-template-columns:1fr}.card,.card.ssi,.card.span3,.card.span4,.card.span8{grid-column:span 12}.g2{grid-template-columns:1fr}.ai{columns:1}
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
function page(k){var ok=document.getElementById('p-'+k);if(!ok){k='overview';}
 document.querySelectorAll('.page').forEach(function(e){e.classList.toggle('on',e.id==='p-'+k);});
 document.querySelectorAll('.ptab').forEach(function(e){e.classList.toggle('on',e.dataset.p===k);});hide();}
document.querySelectorAll('.ptab').forEach(function(a){a.addEventListener('click',function(ev){ev.preventDefault();page(a.dataset.p);
 try{history.replaceState(null,'','#'+a.dataset.p);}catch(e){location.hash=a.dataset.p;}window.scrollTo(0,0);});});
window.addEventListener('hashchange',function(){page(location.hash.slice(1));});if(location.hash)page(location.hash.slice(1));
document.querySelectorAll('.thit').forEach(function(el){function sh(ev){var p=el.dataset.tip.split('|');show(ev.clientX,ev.clientY,p);}
 el.addEventListener('pointermove',sh);el.addEventListener('pointerleave',hide);});
document.querySelectorAll('.tab').forEach(function(b){b.addEventListener('click',function(){var box=b.closest('.tabset')||b.closest('.card')||document;
 box.querySelectorAll('.tab,.panel').forEach(function(e){e.classList.remove('on');});b.classList.add('on');document.getElementById(b.dataset.t).classList.add('on');});});
document.querySelectorAll('a.golink').forEach(function(a){a.addEventListener('click',function(ev){ev.preventDefault();page(a.dataset.p);
 try{history.replaceState(null,'','#'+a.dataset.p);}catch(e){location.hash=a.dataset.p;}window.scrollTo(0,0);});});
if('serviceWorker' in navigator&&location.protocol==='https:'){navigator.serviceWorker.register('sw.js').catch(function(){});}
var dp=null,ib=document.getElementById('installBtn');window.addEventListener('beforeinstallprompt',function(e){e.preventDefault();dp=e;if(ib)ib.classList.add('show');});
if(ib)ib.addEventListener('click',function(){if(dp){dp.prompt();dp=null;ib.classList.remove('show');}});
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
    tabs = [("overview", "總覽", "Overview", [sec_ssi, sec_radar, sec_odds, None, S2.sec_scores_mini, sec_trends]),
            ("scores", "個股評分", "Stock scores", [S2.sec_scores]),
            ("signals", "買點訊號", "Entry signals", [S2.sec_signals]),
            ("themes", "族群", "Themes", [S2.sec_themes]),
            ("risk", "風險模型", "Risk model", [sec_shock, sec_playbook_breaks, sec_macro, sec_quality]),
            ("flows", "Gamma／暗池", "Gamma & flows", [sec_gamma, sec_darkpool, sec_positioning]),
            ("gurus", "大師持倉", "Gurus & insiders", [S2.sec_gurus, S2.sec_insiders]),
            ("bonds", "美債", "Treasuries", [S2.sec_bonds]),
            ("rotation", "類股寬度", "Sectors & breadth", [S2.sec_rotation]),
            ("crisis", "歷史危機", "Past crises", [sec_crisis]),
            ("valuation", "估值泡沫", "Valuation", [sec_valuation]),
            ("markets", "全球行情", "Markets", [sec_markets]),
            ("taiwan", "台股", "Taiwan", [sec_taiwan_trends, sec_taiwan]),
            ("news", "新聞日曆", "News & calendar", [sec_calendar, sec_news]),
            ("history", "時光機", "Time machine", [S2.sec_timemachine]),
            ("inputs", "指標明細", "All inputs", [sec_indicators])]
    nav, panels = [], []
    for i, (key, zh, en, fs) in enumerate(tabs):
        html_ = "".join(sec_ai(ai_text, ai_engine) if f is None else f(eng) for f in fs)
        if not html_.strip():
            html_ = f'<section class="card wide"><p class="muted">{T("這一頁的資料暫時取不到", "No data for this page right now")}</p></section>'
        nav.append(f'<a class="ptab{" on" if i == 0 else ""}" href="#{key}" data-p="{key}" data-en="{esc(en)}">{esc(zh)}</a>')
        panels.append(f'<div class="page{" on" if i == 0 else ""}" id="p-{key}"><div class="grid12">{html_}</div></div>')
    strip = sec_strip(eng)
    asof, stale = data_asof(eng)
    data = json.dumps(_CHARTS, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    foot = T("資料來源：Yahoo Finance、FRED、CBOE、FINRA、SEC EDGAR、TreasuryDirect、證交所／期交所、公開新聞 RSS 與 Google 新聞。平日每小時、週末每 4 小時自動更新。"
             "所有數字由程式自動計算；崩跌機率是歷史頻率而非預測，個股評分是量化篩選而非推薦。本站僅提供市場資訊，不構成任何投資建議。"
             "手機：Android 按「加到主畫面」；iPhone 用 Safari 開啟 → 分享 → 加入主畫面，就能像 App 一樣使用。",
             "Sources: Yahoo Finance, FRED, CBOE, FINRA, SEC EDGAR, TreasuryDirect, TWSE/TAIFEX, public news RSS and Google News. Updated hourly "
             "on weekdays, every 4 hours on weekends. Crash odds are historical frequencies, stock scores are a rules-based screen — "
             "market information only, not investment advice. On iPhone: Safari → Share → Add to Home Screen.")
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><meta name="color-scheme" content="dark light"><title>WallStreet Sentinel｜全球金融風險情報站</title>
<link rel="manifest" href="manifest.webmanifest"><meta name="theme-color" content="#0a0b0d"><link rel="icon" href="favicon-64.png" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="情報站">
<style>{CSS}{S2.SECTION_CSS}</style></head><body>
<header class="top"><div class="bar"><div class="brand">WALLSTREET SENTINEL<small>{T("全球金融風險情報站", "Global financial risk intelligence")}</small></div>
<span class="live{" stale" if stale else ""}"><i></i>{T("行情資料日", "Market data")} {esc(asof or "—")} · {T("頁面產生", "Built")} {now:%m-%d %H:%M} {T("台北", "Taipei")}</span>
<button class="btn install" id="installBtn" type="button" data-en="Install app">加到主畫面</button><button class="btn" id="langBtn" type="button" aria-label="language">EN</button><button class="btn" id="themeBtn" type="button" aria-label="theme">☀</button></div>
<nav class="pnav" aria-label="pages"><div class="pbar">{"".join(nav)}</div></nav></header>
<main class="wrap">{strip}{"".join(panels)}<footer>{foot}</footer></main>
<div id="tip" role="status"></div>
<script type="application/json" id="chart-data">{data}</script><script>{JS}{S2.TM_JS}</script></body></html>'''


def snapshot(eng) -> dict:
    st = eng.stress
    return {
        "generated": datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds"),
        "ssi": None if not st else {"score": round(st.score, 2), "label": st.label, "chg_1d": st.chg_1d, "chg_5d": st.chg_5d,
                                    "chg_20d": st.chg_20d, "coverage": st.coverage, "blocks": st.blocks},
        "playbook": {k: (eng.playbook or {}).get(k) for k in ("stage", "name", "points")},
        "odds": (eng.odds or {}).get("horizons"),
        "scores": {k: [[r["code"], r["name"], r["score"]] for r in m["rows"][:10]]
                   for k, m in ((getattr(eng, "scores", None) or {}).get("markets") or {}).items()},
    }


def daily_snapshot(eng, ai_text: str = "") -> dict:
    """Compact record of what the page said today (time machine)."""
    st, op = eng.stress, (eng.options.spx or {})
    dp = (getattr(eng, "darkpool", None) and eng.darkpool.result) or {}
    spx = eng.market.series("^GSPC")
    asof, _ = data_asof(eng)
    val = [{"label": i["label"], "value": i["value"], "pctile": i["pctile"], "grade": i["grade"]}
           for g in (eng.valuation or {}).get("groups", []) for i in g["items"]]
    sc = {k: {"label": m["label"], "top": [[r["code"], r["name"], r["score"]] for r in m["rows"][:10]]}
          for k, m in ((getattr(eng, "scores", None) or {}).get("markets") or {}).items()}
    return {"date": datetime.now(ZoneInfo(SETTINGS.get("timezone", "Asia/Taipei"))).date().isoformat(), "asof": asof,
            "ssi": None if not st else {"score": round(st.score, 2), "label": st.label, "blocks": {k: round(v, 1) for k, v in st.blocks.items()}},
            "stage": {k: (eng.playbook or {}).get(k) for k in ("stage", "name", "points")},
            "gamma": {"gex": op.get("gex_usd_bn_per_1pct"), "flip": op.get("zero_gamma"), "spot": op.get("spot")} if op else None,
            "darkpool": {"dpi": dp.get("dpi_5d"), "pctile": dp.get("pctile"), "state": dp.get("state")} if dp.get("available") else None,
            "spx": float(spx.iloc[-1]) if len(spx) else None, "valuation": val, "scores": sc, "ai": (ai_text or "")[:6000],
            "signals": {k: {"label": m["label"], "rows": [{"sym": r["sym"], "code": r["code"], "name": r["name"], "pattern": r["patterns"][0]["label"],
                                                           "strength": r["strength"], "price": r["price"], "inv": r["inv"]} for r in m["rows"][:10]]}
                        for k, m in ((getattr(eng, "signals", None) or {}).get("markets") or {}).items()}}


def update_snapshots(eng, snapdir: Path, out: Path, ai_text: str = "") -> Optional[Path]:
    """Write today's snapshot once (after `snapshots.min_hour` Taipei, only when market data moved on since the last one),
    then publish every snapshot + an index (with the S&P 500 move since each date) under <out>/snap/."""
    snapdir.mkdir(parents=True, exist_ok=True)
    tz = ZoneInfo(SETTINGS.get("timezone", "Asia/Taipei"))
    now = datetime.now(tz)
    files = sorted(snapdir.glob("20??-??-??.json"))
    written = None
    snap = daily_snapshot(eng, ai_text)
    target = snapdir / f"{snap['date']}.json"
    last_asof = None
    if files:
        try:
            last_asof = json.loads(files[-1].read_text(encoding="utf-8")).get("asof")
        except Exception:  # noqa: BLE001
            last_asof = None
    min_hour = int((SETTINGS.get("snapshots", {}) or {}).get("min_hour", 6))
    if (now.hour >= min_hour and not target.exists() and snap.get("asof") and snap["asof"] != last_asof
            and snap.get("ssi") is not None):
        target.write_text(json.dumps(snap, ensure_ascii=False, default=str, separators=(",", ":")), encoding="utf-8")
        written = target
        files = sorted(snapdir.glob("20??-??-??.json"))
    spx_now = snap.get("spx")
    idx = []
    dest = out / "snap"
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        sp = getattr(eng, "stockprices", None)
        for m in (d.get("signals") or {}).values():          # how did each signal of that day do since? (filled at publish time)
            for r in m.get("rows", []):
                s_ = sp.series(r["sym"]) if sp is not None else None
                if s_ is not None and len(s_) and r.get("price"):
                    r["now"] = float(s_.iloc[-1])
                    r["since_pct"] = (r["now"] / r["price"] - 1) * 100
                    r["failed"] = bool(r.get("inv") and s_[s_.index > pd.Timestamp(d.get("asof") or d["date"])].lt(r["inv"]).any())
        (dest / f.name).write_text(json.dumps(d, ensure_ascii=False, default=str, separators=(",", ":")), encoding="utf-8")
        after = (spx_now / d["spx"] - 1) * 100 if spx_now and d.get("spx") else None
        idx.append({"date": d.get("date"), "asof": d.get("asof"), "ssi": (d.get("ssi") or {}).get("score"),
                    "stage": (d.get("stage") or {}).get("name"), "spx": d.get("spx"),
                    "after": None if after is None else round(after, 2)})
    (dest / "index.json").write_text(json.dumps(idx, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return written


MANIFEST = {"name": "WallStreet Sentinel 全球金融風險情報站", "short_name": "情報站", "start_url": "./", "scope": "./",
            "display": "standalone", "background_color": "#0a0b0d", "theme_color": "#0a0b0d", "lang": "zh-Hant",
            "description": "全球金融風險、個股評分、Gamma、暗池、美債與大師持倉的公開情報站",
            "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                      {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                      {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}

# network-first: always try for fresh numbers, fall back to the last copy when offline
SW_JS = """const C='wss-v1';
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(['./','index.html','manifest.webmanifest','icon-192.png'])).catch(()=>{}));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET'||new URL(r.url).origin!==location.origin)return;
e.respondWith(fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(C).then(c=>c.put(r,cp));}return res;}).catch(()=>caches.match(r).then(m=>m||caches.match('index.html'))));});
"""


def write_pwa(out: Path) -> None:
    import shutil
    static = Path(__file__).resolve().parent / "static"
    for f in static.glob("*.png"):
        shutil.copyfile(f, out / f.name)
    (out / "manifest.webmanifest").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "sw.js").write_text(SW_JS, encoding="utf-8")


# ----------------------------------------------------------------- main
async def ai_commentary(eng) -> Tuple[str, str]:
    from wsb.ai import context, llm
    try:
        pack = context.build(eng, "full", private=False)
    except TypeError:                                            # older context.build without the public switch
        pack = context.build(eng, "full")
    text, name = await llm.complete(PUBLIC_SYSTEM, pack + "\n\n" + PUBLIC_BRIEF, 4000)
    if name == "none" or text.startswith("⚠️"):
        return "", ""
    text = text.replace("（輸出達長度上限，內容可能不完整）", "").strip()
    return scrub_advice(text), name


async def build(out: Path, use_ai: bool = True, engine=None, snapdir: Optional[Path] = None) -> Path:
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
    write_pwa(out)
    if snapdir is not None:
        try:
            w = update_snapshots(eng, snapdir, out, ai_text)
            log.info("time machine: %s", f"new snapshot {w.name}" if w else "no new snapshot this run")
        except Exception:  # noqa: BLE001
            log.exception("snapshot update failed")
    return out / "index.html"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site")
    ap.add_argument("--no-ai", action="store_true")
    ap.add_argument("--snapdir", default="", help="folder holding the daily time-machine snapshots (data branch checkout)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    t0 = time.time()
    p = asyncio.run(build(Path(a.out), use_ai=not a.no_ai, snapdir=Path(a.snapdir) if a.snapdir else None))
    print(f"wrote {p} ({p.stat().st_size / 1024:.0f} KB) in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
