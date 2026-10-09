"""Shared rendering kit for the intel-station site: bilingual text, number formatting, inline-SVG charts.
Both tools/build_site.py and tools/site_sections.py import from here, so there is exactly one chart registry."""
from __future__ import annotations

import html
import math
from typing import Dict, List, Optional, Tuple

import pandas as pd

esc = html.escape

WORD_EN = {"平靜": "Calm", "正常": "Normal", "升溫": "Elevated", "高壓": "High stress", "極端": "Extreme",
           "點火中": "Igniting", "留意": "Watch", "戒備": "Alert", "防禦": "Defensive", "低": "Low",
           "高度警戒": "High alert", "降溫": "Cooling", "持平": "Flat",
           "信用事件": "Credit event", "利率／債市衝擊": "Rates / bond shock", "套息拆倉": "Carry unwind",
           "波動率／槓桿去化": "Vol / deleveraging", "景氣衰退": "Recession", "商品／地緣能源": "Commodities / geo-energy"}


def T(zh: str, en: Optional[str] = None, tag: str = "span", cls_: str = "") -> str:
    """Bilingual text node: Chinese by default, English swapped in by the toggle."""
    en = WORD_EN.get(zh, zh) if en is None else en
    c = f' class="{cls_}"' if cls_ else ""
    return f'<{tag}{c} data-en="{esc(en)}">{esc(zh)}</{tag}>'


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


_CHARTS: Dict[str, dict] = {}


def line_chart(cid: str, s, label: str, digits: int = 2, w: int = 560, h: int = 190,
               bands: Optional[List[Tuple[float, float, str]]] = None, fixed: Optional[Tuple[float, float]] = None,
               spans: Optional[List[Tuple[str, str, str]]] = None) -> str:
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
    for a, b, lab in spans or []:                      # shaded windows (e.g. past crises), labelled at the top
        ia, ib = s.index.searchsorted(pd.Timestamp(a)), s.index.searchsorted(pd.Timestamp(b))
        if ib <= 0 or ia >= n:
            continue
        xa, xb = pl + min(ia, n - 1) * W / (n - 1), pl + min(ib, n - 1) * W / (n - 1)
        parts.append(f'<rect x="{xa:.1f}" y="{pt}" width="{max(xb - xa, 2):.1f}" height="{H}" class="span"/>'
                     f'<text x="{(xa + xb) / 2:.1f}" y="{pt + 11}" class="spanlbl" text-anchor="middle">{esc(lab)}</text>')
    for t in ticks:
        if lo <= t <= hi:
            y = pt + (1 - (t - lo) / (hi - lo)) * H
            parts.append(f'<line x1="{pl}" x2="{pl + W}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                         f'<text x="{pl - 6}" y="{y + 4:.1f}" class="axis" text-anchor="end">{tick_label(t)}</text>')
    d0, dm, d1 = s.index[0], s.index[n // 2], s.index[-1]
    parts.append(f'<text x="{pl}" y="{h - 6}" class="axis">{d0:%Y-%m}</text>'
                 f'<text x="{pl + W / 2:.0f}" y="{h - 6}" class="axis" text-anchor="middle">{dm:%Y-%m}</text>'
                 f'<text x="{pl + W}" y="{h - 6}" class="axis" text-anchor="end">{d1.strftime("%Y-%m" if (d1 - d0).days > 800 else "%m-%d")}</text>')
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


def card(title_zh: str, title_en: str, body: str, cls_: str = "", sub: str = "") -> str:
    s = f'<p class="sub">{sub}</p>' if sub else ""
    return f'<section class="card {cls_}"><h2>{T(title_zh, title_en)}</h2>{s}{body}</section>'
