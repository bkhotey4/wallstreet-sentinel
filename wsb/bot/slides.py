"""PPT-style slide renderer (1920×1080 PNG, large type, dark theme).

Discord embeds use a fixed small font; these slides are images, so text is
as large as we want. Every deck builder returns a list of PNG bytes."""
from __future__ import annotations

import io
import math
import os
import re
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from ..config import SETTINGS

W, H = 1920, 1080
M = 70                                   # outer margin
BG, CARD, BORDER = "#0B0F14", "#151B23", "#2A313C"
TEXT, MUTED, ACCENT = "#E6EDF3", "#9AA4AF", "#58A6FF"
GREEN, RED, ORANGE, YELLOW, PURPLE = "#3FB950", "#FF6B6B", "#F0883E", "#E3B341", "#BC8CFF"

_FONT_CANDIDATES = {
    "regular": [(r"C:\Windows\Fonts\msjh.ttc", 0), (r"C:\Windows\Fonts\msjh.ttf", 0),
                ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 3),
                ("/System/Library/Fonts/PingFang.ttc", 0)],
    "bold": [(r"C:\Windows\Fonts\msjhbd.ttc", 0), (r"C:\Windows\Fonts\msjhbd.ttf", 0),
             ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 3),
             ("/System/Library/Fonts/PingFang.ttc", 0)],
}
_font_cache: dict = {}
# colour-emoji planes only; BMP symbols (↗ ✓ ★ …) are kept if the font has them, else substituted via _SUBS
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\uFE0F\u200D]")


# Characters that some CJK fonts (e.g. Microsoft JhengHei) lack → rendered as "□".
# Each missing char is replaced by the first candidate the font actually has.
_SUBS = {"≥": ["≧", ">="], "≤": ["≦", "<="], "≈": ["≒", "~"], "≠": ["≠", "!="], "–": ["-"], "—": ["—", "-"],
         "−": ["-"], "‑": ["-"], "‒": ["-"], "‐": ["-"], "•": ["‧", "·"], "·": ["‧", "."], "…": ["…", "..."],
         "“": ["「"], "”": ["」"], "‘": ["'"], "’": ["'"], "→": ["→", "->"], "←": ["←", "<-"],
         "↑": ["↑", "^"], "↓": ["↓", "v"], "×": ["×", "x"], "±": ["±", "+/-"], "σ": ["σ", "s"],
         "β": ["β", "B"], "Δ": ["Δ", "d"], "▲": ["▲", "^"], "▼": ["▼", "v"], "℃": ["℃", "C"],
         "✓": ["V"], "✔": ["V"], "✗": ["X"], "✘": ["X"]}
_glyph_ok: dict = {}
_notdef: dict = {}


def _has_glyph(ch: str) -> bool:
    if ch in _glyph_ok:
        return _glyph_ok[ch]
    f = font(40)
    try:
        if "nd" not in _notdef:
            m = f.getmask("\U0010FFFD")
            _notdef["nd"] = (m.size, bytes(m))
        m = f.getmask(ch)
        ok = (m.size, bytes(m)) != _notdef["nd"]
    except Exception:  # noqa: BLE001
        ok = True
    _glyph_ok[ch] = ok
    return ok


def _safe_chars(s: str) -> str:
    out = []
    for ch in s:
        o = ord(ch)
        if o < 128 or 0x4E00 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF:
            out.append(ch)                       # ASCII / CJK / CJK punctuation / full-width: always present
        elif _has_glyph(ch):
            out.append(ch)
        else:
            out.append(next((c for c in _SUBS.get(ch, []) if all(_has_glyph(x) or ord(x) < 128 for x in c)), ""))
    return "".join(out)


def strip_emoji(s: str) -> str:
    """CJK fonts have no colour emoji and miss some math symbols → they would render as boxes."""
    if not isinstance(s, str):
        return s
    return _safe_chars(re.sub(r"\s{2,}", " ", _EMOJI.sub("", s)).strip())


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    for path, idx in _FONT_CANDIDATES["bold" if bold else "regular"]:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size, index=idx)
                _font_cache[key] = f
                return f
            except OSError:
                continue
    f = ImageFont.load_default()
    _font_cache[key] = f
    return f


def _nan(x) -> bool:
    try:
        return x is None or (isinstance(x, (float, int)) and math.isnan(float(x))) or \
            (hasattr(x, "dtype") and math.isnan(float(x)))
    except (TypeError, ValueError):
        return False


def level_color(score: Optional[float]) -> str:
    if _nan(score):
        return MUTED
    for lim, c in ((35, GREEN), (55, YELLOW), (70, ORANGE), (85, RED)):
        if score < lim:
            return c
    return "#FF3B3B"


def pn(x: Optional[float]) -> str:
    return MUTED if _nan(x) else (GREEN if x > 0 else RED if x < 0 else TEXT)


def fmt(x, d=2, pct=False, sign=False, money=False) -> str:
    if _nan(x):
        return "—"
    try:
        if money:
            s = f"{'+' if sign and x > 0 else ''}{'-' if x < 0 else ''}${abs(x):,.{d}f}"
        else:
            s = f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}"
    except (TypeError, ValueError):
        return str(x)
    return s + ("%" if pct else "")


# ------------------------------------------------------------------ canvas
class Slide:
    def __init__(self, title: str, page: str = "", subtitle: str = "") -> None:
        self.im = Image.new("RGB", (W, H), BG)
        self.d = ImageDraw.Draw(self.im)
        _text, _len = self.d.text, self.d.textlength
        self.d.text = lambda xy, text, *a, **k: _text(xy, strip_emoji(str(text).replace("\n", " ")), *a, **k)  # type: ignore
        self.d.textlength = lambda text, *a, **k: _len(strip_emoji(str(text).replace("\n", " ")), *a, **k)   # type: ignore
        tz = SETTINGS.get("timezone", "Asia/Taipei")
        try:
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo(tz))
        except Exception:  # noqa: BLE001
            now = datetime.now()
        x = M
        if page:
            pw = self.text_w(page, font(30, True)) + 48
            self.d.rounded_rectangle((M, 48, M + pw, 112), 14, fill="#238636")
            self.d.text((M + 24, 80), page, font=font(30, True), fill="white", anchor="lm")
            x = M + pw + 28
        self.d.text((x, 80), title, font=self.fit(title, 52, W - M - x - 400, True, 30), fill=ACCENT, anchor="lm")
        self.d.text((W - M, 80), f"{now:%Y-%m-%d %H:%M} 台北", font=font(28), fill=MUTED, anchor="rm")
        self.d.line((M, 138, W - M, 138), fill=BORDER, width=3)
        if subtitle:
            self.d.text((M, 170), subtitle, font=self.fit(subtitle, 32, W - 2 * M, False, 22), fill=MUTED, anchor="lm")
        self.d.text((W / 2, H - 30), "WallStreet Sentinel · 即時數據 · 非投資建議", font=font(22), fill="#5A6470",
                    anchor="mm")

    # -- primitives
    def text_w(self, s: str, f) -> float:
        return self.d.textlength(s, font=f)

    def card(self, box, fill=CARD, outline=BORDER, r=22, width=2):
        self.d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

    def fit(self, s: str, size: int, max_w: float, bold=False, min_size=22):
        while size > min_size and self.text_w(s, font(size, bold)) > max_w:
            size -= 2
        return font(size, bold)

    def kpis(self, items: Sequence[Tuple[str, str, str]], y: int = 175, h: int = 190):
        n = len(items)
        gap = 26
        w = (W - 2 * M - gap * (n - 1)) / n
        for i, (label, value, col) in enumerate(items):
            x0 = M + i * (w + gap)
            self.card((x0, y, x0 + w, y + h))
            self.d.text((x0 + w / 2, y + 48), label, font=self.fit(label, 32, w - 30), fill=MUTED, anchor="mm")
            self.d.text((x0 + w / 2, y + 125), value, font=self.fit(value, 68, w - 30, True), fill=col, anchor="mm")
        return y + h

    def bars(self, rows: Sequence[Tuple[str, float, str]], box, label_w=300, size=36):
        x0, y0, x1, y1 = box
        n = max(len(rows), 1)
        rh = min(84, (y1 - y0) / n)
        for i, (label, v, right) in enumerate(rows):
            cy = y0 + i * rh + rh / 2
            self.d.text((x0, cy), label, font=self.fit(label, size, label_w - 10), fill=TEXT, anchor="lm")
            bx0, bx1 = x0 + label_w, x1 - 150
            self.d.rounded_rectangle((bx0, cy - 16, bx1, cy + 16), 16, fill="#222A35")
            vv = max(0.0, min(100.0, v or 0))
            if vv > 0:
                self.d.rounded_rectangle((bx0, cy - 16, bx0 + (bx1 - bx0) * vv / 100, cy + 16), 16,
                                         fill=level_color(v))
            self.d.text((x1, cy), right, font=font(size, True), fill=level_color(v), anchor="rm")

    def table(self, header: Sequence[str], rows: Sequence[Sequence[Tuple[str, str]]], y: int,
              widths: Sequence[float], size: int = 34, row_h: int = 66, align: Optional[Sequence[str]] = None):
        """rows: list of [(text, color), ...]; widths are fractions of the content width."""
        tw = W - 2 * M
        xs = [M]
        for w in widths[:-1]:
            xs.append(xs[-1] + w * tw)
        align = align or ["l"] + ["r"] * (len(header) - 1)
        self.card((M - 10, y - 10, W - M + 10, y + row_h * (len(rows) + 1) + 10), fill="#10151C")
        for j, h in enumerate(header):
            self._cell(xs[j], widths[j] * tw, y + row_h / 2, h, MUTED,
                       self.fit(h, size - 4, widths[j] * tw - 24, True), align[j])
        self.d.line((M, y + row_h, W - M, y + row_h), fill=BORDER, width=2)
        for i, r in enumerate(rows):
            cy = y + row_h * (i + 1.5)
            if i % 2 == 1:
                self.d.rectangle((M - 4, cy - row_h / 2, W - M + 4, cy + row_h / 2), fill="#131922")
            for j, (txt, col) in enumerate(r):
                self._cell(xs[j], widths[j] * tw, cy, txt, col, self.fit(txt, size, widths[j] * tw - 24, j == 0),
                           align[j])
        return y + row_h * (len(rows) + 1)

    def _cell(self, x, w, cy, txt, col, f, al):
        if al == "l":
            self.d.text((x + 16, cy), txt, font=f, fill=col, anchor="lm")
        elif al == "c":
            self.d.text((x + w / 2, cy), txt, font=f, fill=col, anchor="mm")
        else:
            self.d.text((x + w - 16, cy), txt, font=f, fill=col, anchor="rm")

    def sparkline(self, vals: Sequence[float], box, color: str) -> None:
        v = [x for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x))]
        if len(v) < 3:
            return
        x0, y0, x1, y1 = box
        lo, hi = min(v), max(v)
        span = (hi - lo) or 1
        pts = [(x0 + (x1 - x0) * i / (len(v) - 1), y1 - (y1 - y0) * (p - lo) / span) for i, p in enumerate(v)]
        self.d.line([(x0, pts[0][1]), (x1, pts[0][1])], fill="#2A313C", width=2)      # start-level baseline
        self.d.line(pts, fill=color, width=4, joint="curve")
        self.d.ellipse((pts[-1][0] - 6, pts[-1][1] - 6, pts[-1][0] + 6, pts[-1][1] + 6), fill=color)

    def tiles(self, items: Sequence[tuple], y: int, cols: int = 4, h: int = 190):
        """items: (name, value, change_text, color[, sparkline_values])"""
        gap = 22
        w = (W - 2 * M - gap * (cols - 1)) / cols
        for i, it in enumerate(items):
            name, val, chg, col = it[:4]
            spark = it[4] if len(it) > 4 else None
            r, c = divmod(i, cols)
            x0, y0 = M + c * (w + gap), y + r * (h + gap)
            self.card((x0, y0, x0 + w, y0 + h), outline=col if col in (RED, GREEN) else BORDER, width=3)
            if spark:
                trend = GREEN if spark[-1] >= spark[0] else RED
                self.sparkline(spark, (x0 + w * 0.58, y0 + h * 0.18, x0 + w - 22, y0 + h * 0.62), trend)
            name_w = (w * 0.58 - 40) if spark else (w - 50)          # don't run under the sparkline
            self.d.text((x0 + 26, y0 + h * 0.20), name, font=self.fit(name, 32, name_w), fill=MUTED, anchor="lm")
            self.d.text((x0 + 26, y0 + h * 0.50), val, font=self.fit(val, 46, w - 50, True), fill=TEXT, anchor="lm")
            self.d.text((x0 + 26, y0 + h * 0.79), chg, font=self.fit(chg, 38, w - 50, True), fill=col, anchor="lm")

    def wrap(self, s: str, f, max_w: float) -> List[str]:
        if "\n" in s:                                              # honour explicit line breaks
            out: List[str] = []
            for part in s.split("\n"):
                out += self.wrap(part, f, max_w)
            return out
        tokens = re.findall(r"[A-Za-z0-9$%+\-.,:/()\[\]'’&]+|\s+|.", s)
        lines, cur = [], ""
        for t in tokens:
            if self.text_w(cur + t, f) <= max_w:
                cur += t
                continue
            if cur.strip():
                lines.append(cur.rstrip())
            cur = t.lstrip()
            while self.text_w(cur, f) > max_w and len(cur) > 1:   # very long token → binary-search the cut
                lo, hi = 1, len(cur)
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if self.text_w(cur[:mid], f) <= max_w:
                        lo = mid
                    else:
                        hi = mid - 1
                lines.append(cur[:lo])
                cur = cur[lo:]
        if cur.strip():
            lines.append(cur.rstrip())
        return lines or [""]

    def paragraph(self, s: str, x: int, y: int, max_w: float, size=36, color=TEXT, bold=False, line_gap=1.45):
        f = font(size, bold)
        for ln in self.wrap(s, f, max_w):
            self.d.text((x, y), ln, font=f, fill=color)
            y += int(size * line_gap)
        return y

    def line_chart(self, series: List[Tuple[List[float], str, str]], box, zones: bool = False,
                   labels: Optional[List[str]] = None):
        x0, y0, x1, y1 = box
        self.card((x0 - 20, y0 - 20, x1 + 20, y1 + 60), fill="#10151C")
        if zones:
            for lo, hi, c in ((0, 35, "#11261A"), (35, 55, "#2A2511"), (55, 70, "#2E1D10"), (70, 100, "#331414")):
                yy0 = y1 - (y1 - y0) * hi / 100
                yy1 = y1 - (y1 - y0) * lo / 100
                self.d.rectangle((x0, yy0, x1, yy1), fill=c)
            for v in (35, 55, 70, 85):
                yy = y1 - (y1 - y0) * v / 100
                self.d.text((x0 - 12, yy), str(v), font=font(24), fill=MUTED, anchor="rm")
        for vals, col, name in series:
            vals = [v for v in vals if v is not None and not math.isnan(v)]
            if len(vals) < 2:
                continue
            lo, hi = (0, 100) if zones and name == "SSI" else (min(vals), max(vals))
            span = (hi - lo) or 1
            pts = [(x0 + (x1 - x0) * i / (len(vals) - 1), y1 - (y1 - y0) * (v - lo) / span) for i, v in enumerate(vals)]
            self.d.line(pts, fill=col, width=5, joint="curve")
            self.d.ellipse((pts[-1][0] - 10, pts[-1][1] - 10, pts[-1][0] + 10, pts[-1][1] + 10), fill=col)
        if labels:
            for i, lab in enumerate(labels):
                frac, lab = lab if isinstance(lab, tuple) else (i / max(len(labels) - 1, 1), lab)
                self.d.text((x0 + (x1 - x0) * frac, y1 + 32), lab, font=font(24),
                            fill=MUTED, anchor="mm")

    def png(self) -> bytes:
        buf = io.BytesIO()
        self.im.save(buf, "PNG", optimize=True)
        return buf.getvalue()


# ------------------------------------------------------------------ names
COMP_NAMES = {
    "hy_oas": "高收益債利差", "ccc_oas": "CCC 垃圾債利差", "hyg_ief": "垃圾債 vs 公債", "bizd": "私募信貸 BDC",
    "kre": "區域銀行", "vix_term": "VIX 期限結構", "vix_level": "VIX 水位", "vvix": "VVIX", "move": "美債波動 MOVE",
    "nfci": "芝加哥金融狀況", "stlfsi": "聖路易壓力指數", "net_liq": "聯準會淨流動性", "us2y_drop": "2年債殖利率急跌",
    "curve_steep": "殖利率曲線陡峭化", "dxy": "美元走強", "yen_carry": "日圓套息拆倉", "audjpy": "澳幣/日圓",
    "cnh": "人民幣貶值", "spx_trend": "標普 200 日線", "breadth": "市場廣度", "correlation": "板塊同漲同跌",
    "em_debt": "新興市場債", "eu_banks": "歐洲銀行", "copper_gold": "銅金比", "oil_shock": "油價衝擊",
    "btc": "比特幣",
    "ig_oas": "投資級債利差", "loans": "槓桿貸款 vs 公債", "alt_bx": "黑石（私募）", "alt_apo": "阿波羅（私募）",
    "alt_ares": "Ares（私募信貸）", "real_yield": "10年實質利率上升", "long_bond": "30年債殖利率急升",
    "reserves": "銀行準備金下降", "claims": "初領失業金上升", "sahm": "薩姆衰退指標", "small_caps": "小型股落後",
    "vix_short": "短期恐慌 VIX9D/VIX", "spx_rvol": "標普實際波動", "ai_leaders": "半導體相對走弱",
    "krw": "韓元貶值", "gold_bid": "黃金避險買盤",
}
KEY_TILES = [("^GSPC", "標普500"), ("^NDX", "那指100"), ("^SOX", "費半"), ("^TWII", "台灣加權"),
             ("^N225", "日經225"), ("^HSI", "恆生"), ("^STOXX50E", "歐洲50"), ("^VIX", "VIX 恐慌"),
             ("^TNX", "美10年債"), ("DX-Y.NYB", "美元指數"), ("JPY=X", "美元/日圓"), ("TWD=X", "美元/台幣"),
             ("GC=F", "黃金"), ("BZ=F", "布蘭特原油"), ("HYG", "高收益債"), ("BTC-USD", "比特幣")]


# assets whose RISE is bad for equities → up = red. (USD/JPY & USD/CHF are NOT here: their fall = safe-haven bid = risk-off)
INVERSE = {"^VIX", "^VIX9D", "^VIX3M", "^VVIX", "^MOVE", "^SKEW", "DX-Y.NYB", "TWD=X", "KRW=X", "CNY=X", "MXN=X",
           "^IRX", "^FVX", "^TNX", "^TYX"}


def chg_color(t: str, chg: Optional[float]) -> str:
    if _nan(chg):
        return MUTED
    good = chg < 0 if t in INVERSE else chg > 0
    return GREEN if good else RED if chg != 0 else TEXT


def _q_tile(engine, t: str, name: str):
    q = engine.market.q(t)
    if not q:
        return None
    sig = engine.market.sigma_move(t)
    chg = q.get("chg_pct")
    col = chg_color(t, chg)
    flag = f"  {sig:+.1f}σ" if sig is not None and abs(sig) >= 2 else ""
    s = engine.market.series(t)
    spark = [float(x) for x in s.iloc[-23:].values] if len(s) >= 5 else None
    return name, fmt(q["price"], 2), f"{fmt(chg, 2, pct=True, sign=True)}{flag}", col, spark


# ------------------------------------------------------------------ decks
def deck_risk(engine, pages: Iterable[str] = ("overview", "blocks", "markets", "trend")) -> List[bytes]:
    st = engine.stress
    out = []
    pages = [p for p in pages if not (p == "blocks" and not st) and
             not (p == "trend" and (st is None or len(st.history) <= 30))]
    total = len(pages)
    for i, p in enumerate(pages, 1):
        tag = f"{i}/{total}"
        if p == "overview":
            out.append(_risk_overview(engine, st, tag).png())
        elif p == "blocks" and st:
            out.append(_risk_blocks(st, tag).png())
        elif p == "markets":
            out.append(_markets(engine, tag).png())
        elif p == "trend" and st is not None and len(st.history) > 30:
            out.append(_trend(engine, st, tag).png())
        elif p == "crash":
            out.append(_crash(engine, tag).png())
    return out


def _risk_overview(engine, st, tag) -> Slide:
    s = Slide("系統性風險總覽", tag)
    sc = st.score if st else None
    col = level_color(sc)
    s.card((M, 175, 760, 1000), outline=col, width=4)
    s.d.text((415, 250), "系統性壓力指數 SSI", font=font(40, True), fill=MUTED, anchor="mm")
    s.d.text((415, 440), fmt(sc, 1), font=font(230, True), fill=col, anchor="mm")
    s.d.text((415, 610), st.label if st else "計算中", font=font(64, True), fill=col, anchor="mm")
    if st:
        s.d.rounded_rectangle((130, 690, 700, 730), 20, fill="#222A35")
        s.d.rounded_rectangle((130, 690, 130 + 570 * min(sc, 100) / 100, 730), 20, fill=col)
        s.d.text((415, 800), f"歷史百分位 {fmt(st.pctile_all, 0)}%", font=font(40), fill=TEXT, anchor="mm")
        s.d.text((415, 870), f"1日 {fmt(st.chg_1d, 1, sign=True)}　5日 {fmt(st.chg_5d, 1, sign=True)}　20日 {fmt(st.chg_20d, 1, sign=True)}",
                 font=font(36), fill=MUTED, anchor="mm")
        s.d.text((415, 940), f"資料覆蓋 {st.coverage*100:.0f}%", font=font(28), fill="#6E7781", anchor="mm")
    # right side: 4 big facts
    od = engine.odds or {}
    h63 = next((h for h in od.get("horizons", []) if h["days"] == 63), None)
    rg = engine.regime or {}
    mom = od.get("momentum") or {}
    if h63:
        la = h63.get("lift_adj", h63.get("lift"))
        pbig = h63.get("adjusted", h63.get("conditional"))
        small63 = (f"基準 {fmt(h63['base_rate'], 1)}%｜{h63.get('lift_adj_text') or h63.get('lift_text', '')}",
                   f"僅看水準 {fmt(h63['conditional'], 1)}%・SSI 20日 {fmt(mom.get('chg20'), 1, sign=True)}（{mom.get('state') or '—'}）")
    else:
        la, pbig, small63 = None, None, ("", "")
    facts = [
        ("3 個月內跌 ≥10% 機率", f"{fmt(pbig, 1)}%" if h63 else "—", small63, lift_color(la)),
        ("總經象限", (rg.get("quadrant") or "—").split(" ")[0], rg.get("playbook", "")[:26], PURPLE),
        ("風險偏好", rg.get("risk_mode", "—").split(" ")[0], f"z = {fmt(rg.get('risk_appetite_z'), 2)}", ACCENT),
        ("聯準會淨流動性", (rg.get("liquidity_mode") or "資料缺").split(" ")[0],
         f"13週變化 {fmt(rg.get('net_liquidity_chg_13w_bn'), 0, sign=True)} 十億美元" if rg.get("net_liquidity_chg_13w_bn") is not None else "需要 FRED 金鑰",
         TEXT),
    ]
    x0, gap = 800, 24
    w = (W - M - x0 - gap) / 2
    h = (1000 - 175 - gap) / 2
    for i, (lab, big, small, c) in enumerate(facts):
        r, cc = divmod(i, 2)
        bx, by = x0 + cc * (w + gap), 175 + r * (h + gap)
        s.card((bx, by, bx + w, by + h))
        s.d.text((bx + w / 2, by + 70), lab, font=s.fit(lab, 36, w - 40), fill=MUTED, anchor="mm")
        s.d.text((bx + w / 2, by + 200), big, font=s.fit(big, 76, w - 40, True), fill=c, anchor="mm")
        if isinstance(small, tuple):
            s.d.text((bx + w / 2, by + 295), small[0], font=s.fit(small[0], 32, w - 40, True), fill=lift_color(la, muted=True), anchor="mm")
            s.d.text((bx + w / 2, by + 345), small[1], font=s.fit(small[1], 26, w - 40), fill=MUTED, anchor="mm")
        elif small:
            s.d.text((bx + w / 2, by + 310), small, font=s.fit(small, 30, w - 40), fill=MUTED, anchor="mm")
    return s


def _risk_blocks(st, tag) -> Slide:
    s = Slide("風險來自哪裡？", tag, f"左：{len(st.blocks)} 大風險區塊分數（0 平靜 → 100 極端）　右：推升 / 緩解最多的因子")
    rows = [(k, v, f"{v:.0f}") for k, v in sorted(st.blocks.items(), key=lambda x: -x[1])]
    s.card((M, 220, 1060, 1000))
    s.bars(rows, (M + 40, 250, 1030, 980), label_w=250, size=38)
    s.card((1090, 220, W - M, 1000))
    s.d.text((1130, 270), "▲ 推升風險", font=font(40, True), fill=RED, anchor="lm")
    y = 330
    for c in st.drivers(5):
        s.d.text((1130, y), COMP_NAMES.get(c.id, c.id), font=s.fit(COMP_NAMES.get(c.id, c.id), 36, 480), fill=TEXT, anchor="lm")
        s.d.text((W - M - 40, y), f"{c.score:.0f}", font=font(40, True), fill=level_color(c.score), anchor="rm")
        y += 62
    y += 30
    s.d.text((1130, y), "▼ 緩解風險", font=font(40, True), fill=GREEN, anchor="lm")
    y += 60
    for c in st.relief(3):
        s.d.text((1130, y), COMP_NAMES.get(c.id, c.id), font=s.fit(COMP_NAMES.get(c.id, c.id), 36, 480), fill=TEXT, anchor="lm")
        s.d.text((W - M - 40, y), f"{c.score:.0f}", font=font(40, True), fill=level_color(c.score), anchor="rm")
        y += 62
    return s


def _markets(engine, tag) -> Slide:
    s = Slide("全球市場即時看板", tag, "數字顏色：綠 = 對股市有利、紅 = 不利｜右上小圖：近一個月走勢（綠 = 月漲、紅 = 月跌）")
    items = [t for t in (_q_tile(engine, t, n) for t, n in KEY_TILES) if t]
    s.tiles(items[:16], 215, cols=4, h=180)
    return s


def _trend(engine, st, tag) -> Slide:
    s = Slide("壓力指數近一年走勢", tag, "彩色線 = SSI（背景色帶：綠 平靜 / 黃 正常 / 橘 升溫 / 紅 高壓）　白線 = 標普 500")
    hist = st.history.iloc[-252:]
    spx = engine.market.series("^GSPC").reindex(hist.index).ffill()
    n = len(hist)
    pos = sorted(set([int(i * (n - 1) / 6) for i in range(7)]))
    labels = [(i / max(n - 1, 1), hist.index[i].strftime("%y/%m")) for i in pos]
    s.line_chart([(list(hist.values), level_color(st.score), "SSI"), (list(spx.values), "#DDDDDD", "SPX")],
                 (M + 60, 240, W - M - 20, 940), zones=True, labels=labels)
    return s


def lift_color(lift, muted: bool = False):
    """Colour by how the probability compares with the historical base rate."""
    if lift is None or lift != lift:
        return MUTED if muted else TEXT
    if lift >= 1.5:
        return RED
    if lift >= 1.1:
        return ORANGE
    if lift <= 0.9:
        return GREEN
    return MUTED if muted else TEXT


def _crash(engine, tag) -> Slide:
    od = engine.odds or {}
    mom = od.get("momentum") or {}
    s = Slide("崩跌機率實證回測", tag,
              f"歷史上 SSI 落在目前區間（{od.get('bucket', '—')}）且升溫速度相同（{mom.get('state') or '—'}）時，標普 500 之後跌到門檻的頻率")
    hz = od.get("horizons", [])
    rows = [[(f"{h['days']} 日內跌 ≥{h['drawdown_pct']:.0f}%", TEXT),
             (f"{fmt(h['conditional'], 1)}%", MUTED),
             (f"{fmt(h.get('adjusted'), 1)}%", lift_color(h.get('lift_adj'))),
             (f"{fmt(h['base_rate'], 1)}%", MUTED),
             (f"×{fmt(h.get('lift_adj'), 2)}", lift_color(h.get('lift_adj'))),
             (str(h["episodes_in_zone"]), MUTED)] for h in hz]
    s.table(["情境", "僅看水準", "含升溫速度", "歷史基準", "倍數", "獨立事件"], rows, 230,
            [0.27, 0.15, 0.17, 0.15, 0.12, 0.14], size=42, row_h=105)
    pct = mom.get("pctile")
    th = mom.get("th_rising")
    note = (f"SSI 20 日變化 {fmt(mom.get('chg20'), 1, sign=True)} 點，高於歷史 {fmt(pct, 0)}% 的時間"
            f"（升溫門檻 {fmt(th, 1, sign=True)} 點，依歷史動態計算）。" if mom.get("chg20") is not None else "")
    s.paragraph(note + "倍數 = 含升溫速度的機率 ÷ 歷史基準：>1 比平常危險、<1 比平常安全，≥1.5 倍應考慮避險。"
                "樣本少時會自動向「僅看水準」收斂；樣本自 " + str(od.get("sample_start", "—")) + "。",
                M, 700, W - 2 * M, size=32, color=MUTED)
    return s


def deck_portfolio(engine) -> List[bytes]:
    p = engine.portfolio or {}
    if not p or p.get("error"):
        s = Slide("持倉風險駕駛艙", "1/1")
        s.paragraph(p.get("error", "計算中") if p else "計算中", M, 250, W - 2 * M, size=48)
        return [s.png()]
    pos_all = [x for x in p["positions"] if "value_usd" in x]
    no_quote = [x for x in p["positions"] if "value_usd" not in x]
    first, rest = pos_all[:9], pos_all[9:]
    extra_pages = [rest[i:i + 12] for i in range(0, len(rest), 12)]
    total = 2 + len(extra_pages)
    s = Slide("持倉風險駕駛艙", f"1/{total}")
    y = s.kpis([("持倉市值", fmt(p["total_value_usd"], 0, money=True), TEXT),
                ("未實現損益", fmt(p["pnl_pct"], 1, pct=True, sign=True), pn(p["pnl_pct"])),
                ("今日損益", fmt(p["day_pnl_usd"], 0, money=True, sign=True), pn(p["day_pnl_usd"])),
                ("最壞 1% 單日虧損 VaR99", fmt(p["var99_1d_usd"], 0, money=True), ORANGE)])
    def prow(r):
        return [(r["sym"], TEXT), (f"{r['weight']:.1f}%", TEXT),
                (fmt(r["d1_pct"], 2, pct=True, sign=True), pn(r["d1_pct"])),
                (fmt(r["pnl_pct"], 1, pct=True, sign=True), pn(r["pnl_pct"])),
                (fmt(r.get("beta"), 2), TEXT),
                (f"{fmt(r.get('risk_contrib_pct'), 0)}%", RED if (r.get("risk_contrib_pct") or 0) > 25 else TEXT)]
    rows = [prow(r) for r in first]
    if rest:
        rows.append([(f"…其餘 {len(rest)} 檔見下一頁", MUTED)] + [("", MUTED)] * 5)
    if no_quote:
        rows.append([("無報價：" + "、".join(x["sym"] for x in no_quote)[:40], ORANGE)] + [("", MUTED)] * 5)
    hdr = ["代號", "權重", "今日", "累積損益", "β", "風險貢獻"]
    wid = [0.22, 0.14, 0.16, 0.18, 0.12, 0.18]
    s.table(hdr, rows, y + 35, wid, size=36, row_h=min(72, int((1010 - y - 35) / (len(rows) + 1))))
    out = [s.png()]
    for k, chunk in enumerate(extra_pages, 2):
        sx = Slide("持倉明細（續）", f"{k}/{total}")
        sx.table(hdr, [prow(r) for r in chunk], 190, wid, size=34, row_h=min(66, int(820 / (len(chunk) + 1))))
        out.append(sx.png())
    scen = p.get("scenarios", [])
    s2 = Slide("歷史危機重播：你的持倉會怎樣？", f"{total}/{total}", "用當年真實價格重播（標的當時未上市者以 β × 大盤代理）")
    rows = [[(sc["name"], TEXT), (fmt(sc["bench_pct"], 1, pct=True, sign=True), pn(sc["bench_pct"])),
             (fmt(sc["port_pct"], 1, pct=True, sign=True), pn(sc["port_pct"])),
             (fmt(sc["pnl_usd"], 0, money=True, sign=True), pn(sc["pnl_usd"]))] for sc in scen]
    s2.table(["危機", "大盤", "你的持倉", "損益金額"], rows, 225, [0.40, 0.18, 0.20, 0.22], size=36,
             row_h=min(78, int(780 / (len(rows) + 1))) if rows else 78)
    out.append(s2.png())
    return out


def deck_hedge(engine, res: dict) -> List[bytes]:
    if res.get("error"):
        s = Slide("避險成本計算器", "1/1")
        s.paragraph(res["error"], M, 250, W - 2 * M, size=48)
        return [s.png()]
    b = res["betas"]
    s = Slide("避險成本計算器", "1/3")
    y = s.kpis([("持倉市值", fmt(res["value"], 0, money=True), TEXT),
                ("對標普 β", fmt(b.get("SPY"), 2), TEXT), ("對那指 β", fmt(b.get("QQQ"), 2), TEXT),
                ("壓力指數", fmt(res.get("ssi"), 1), level_color(res.get("ssi")))])
    adv_lines = s.wrap(res["advice"], font(34), W - 2 * M - 72)
    box_h = 70 + 50 * len(adv_lines)
    s.card((M, y + 25, W - M, y + 25 + box_h), outline=ACCENT, width=3)
    s.d.text((M + 36, y + 60), "建議", font=font(36, True), fill=ACCENT, anchor="lm")
    yy = y + 88
    for ln in adv_lines:
        s.d.text((M + 36, yy), ln, font=font(34), fill=TEXT)
        yy += 50
    rows, unh = [], None
    for u, d in res["underlyings"].items():
        plans = d["plans"]
        if not plans:
            continue
        longest = max(p_["dte"] for p_ in plans)                 # show the ~90-day expiry
        for pl in [x for x in plans if x["dte"] == longest][:3]:
            h20 = pl["payoff"].get(20) or next(iter(pl["payoff"].values()))
            unh = h20["unhedged"] if unh is None else unh
            k = "價平" if pl["otm_pct"] < 1 else f"價外 {pl['otm_pct']:.0f}%"
            rows.append([(f"{u} 賣權", TEXT), (f"{pl['dte']} 天", TEXT), (f"{fmt(pl['strike'], 0)}（{k}）", TEXT),
                         (str(pl["contracts"]), TEXT), (fmt(pl["cost"], 0, money=True), ORANGE),
                         (f"{pl['cost_pct']:.1f}%", ORANGE), (fmt(h20["hedged"], 0, money=True, sign=True), pn(h20["hedged"]))])
    ty = y + 25 + box_h + 30
    if unh is not None:
        s.d.text((M, ty + 18), f"對照：不避險時大盤跌 20%，持倉估計損益 {fmt(unh, 0, money=True, sign=True)}",
                 font=font(32, True), fill=RED, anchor="lm")
        ty += 55
    rh = max(50, min(66, int((1005 - ty) / (len(rows[:6]) + 1))))
    s.table(["方案", "期限", "履約價", "口數", "權利金", "占持倉", "大盤跌20%後損益"], rows[:6], ty,
            [0.14, 0.10, 0.21, 0.08, 0.15, 0.12, 0.20], size=32, row_h=rh)
    out = [s.png()]
    srows = []
    for u, d in res["underlyings"].items():
        sts = d.get("structures") or []
        if not sts:
            continue
        longest = max(x["dte"] for x in sts)
        for st_ in [x for x in sts if x["dte"] == longest]:
            cap = f"上檔封頂 +{st_['cap_pct']:.1f}%" if st_.get("cap_pct") is not None else f"最多補 {fmt(st_['max_cover'], 0, money=True)}"
            srows.append([(f"{u} {st_['label']}", TEXT), (f"{st_['dte']}天", TEXT), (st_["legs"], TEXT),
                          (fmt(st_["net_cost"], 0, money=True, sign=True), ORANGE if st_["net_cost"] > 0 else GREEN),
                          (fmt(st_["pnl"][-20], 0, money=True, sign=True), pn(st_["pnl"][-20])),
                          (fmt(st_["pnl"][10], 0, money=True, sign=True), pn(st_["pnl"][10])), (cap, MUTED)])
    if srows:
        s3 = Slide("進階避險結構：賣權價差與領口", "2/3", "損益只算避險部位本身（對指數 −20% ／ +10%）；領口用賣出上檔買權換免費保險")
        s3.table(["方案", "期限", "組合", "淨成本", "指數−20%", "指數+10%", "限制"], srows[:6], 235,
                 [0.16, 0.08, 0.22, 0.12, 0.13, 0.13, 0.16], size=28, row_h=84)
        s3.paragraph("賣權價差：保費比單買賣權便宜，但跌破下方履約價後不再賠償。領口：幾乎零成本，但大漲時上檔被封頂——適合『不想賣股、只怕短期大跌』。",
                     M, 235 + 84 * (len(srows[:6]) + 1) + 40, W - 2 * M, size=30, color=MUTED)
        out.append(s3.png())
    s2 = Slide("其他避險方式", f"{len(out) + 1}/{len(out) + 1}")
    y = 190
    for u, d in res["underlyings"].items():
        inv = d.get("inverse")
        if not inv:
            continue
        s2.card((M, y, W - M, y + 170))
        s2.d.text((M + 36, y + 50), f"反向 ETF {inv['symbol']}（{inv['name']}）", font=font(40, True), fill=ACCENT, anchor="lm")
        s2.d.text((M + 36, y + 115), f"完全對沖買 {fmt(inv['full_hedge_usd'], 0, money=True)}　·　半對沖 {fmt(inv['half_hedge_usd'], 0, money=True)}",
                  font=font(38), fill=TEXT, anchor="lm")
        y += 195
    s2.paragraph("反向 ETF 無到期日、可小額買，但每天再平衡會在震盪市耗損，只適合數週內的短期保護。", M, y + 5, W - 2 * M,
                 size=32, color=MUTED)
    y += 90
    if res.get("derisk"):
        s2.d.text((M, y + 20), "減碼風險最高的持股（目標降低 25% 大盤曝險）", font=font(40, True), fill=YELLOW, anchor="lm")
        room = max(1, int((1000 - (y + 60)) / 70) - 1)
        dr = res["derisk"]
        rows = [[(d["sym"], TEXT), (fmt(d["sell_usd"], 0, money=True), TEXT), (f"{d['shares']} 股", TEXT),
                 (f"{fmt(d['risk_contrib_pct'], 0)}%", RED)] for d in dr[:room if len(dr) <= room else room - 1]]
        if len(dr) > room:
            rows.append([(f"…其餘 {len(dr) - (room - 1)} 檔", MUTED), ("", MUTED), ("", MUTED), ("", MUTED)])
        s2.table(["持股", "賣出金額", "約股數", "風險貢獻"], rows, y + 60, [0.3, 0.25, 0.2, 0.25], size=36, row_h=70)
    out.append(s2.png())
    return out


def deck_scorecard(engine, res: dict) -> List[bytes]:
    s = Slide("警報成績單：警報發出後，大盤真的跌了嗎？", "1/1")
    if res.get("error"):
        s.paragraph(res["error"], M, 250, W - 2 * M, size=48)
        return [s.png()]
    hz = res["horizons"]
    s.paragraph("比較方式：警報後 N 個交易日內，標普 500 最深跌幅是否達門檻；與過去 10 年任意一天的機率（基準）相比。倍數 > 1 才代表警報有用。",
                M, 170, W - 2 * M, size=32, color=MUTED)
    rows = []
    names = {"risk": "市場風險警報", "news": "新聞風險警報"}
    for kind, sm in res["summary"].items():
        for h in hz:
            r = sm["by_horizon"].get(h["days"], {})
            if r.get("episodes"):
                rows.append([(names.get(kind, kind), TEXT), (f"{h['days']}日內跌≥{h['drawdown']*100:.0f}%", TEXT),
                             (f"{r['hit_rate']:.0f}%", ORANGE), (f"{r['base_rate']:.1f}%", MUTED),
                             (f"×{fmt(r.get('lift'), 1)}", GREEN if (r.get("lift") or 0) > 1 else RED),
                             (str(r["episodes"]), TEXT)])
            else:
                rows.append([(names.get(kind, kind), TEXT), (f"{h['days']}日內跌≥{h['drawdown']*100:.0f}%", TEXT),
                             ("待評分", MUTED), (f"{r.get('base_rate', 0):.1f}%", MUTED), ("—", MUTED), ("0", MUTED)])
    if not rows:
        s.card((M, 330, W - M, 700))
        s.d.text((W / 2, 470), "目前還沒有可評分的警報", font=font(60, True), fill=TEXT, anchor="mm")
        s.d.text((W / 2, 570), "警報發出後，需等待 5～20 個交易日才能評分", font=font(40), fill=MUTED, anchor="mm")
        base = " · ".join(f"{h['days']}日內跌≥{h['drawdown']*100:.0f}% 基準 {res['base'][h['days']]:.1f}%" for h in hz)
        s.d.text((W / 2, 780), base, font=font(34), fill=MUTED, anchor="mm")
        return [s.png()]
    s.table(["警報類型", "檢驗期間", "命中率", "基準", "倍數", "事件數"], rows, 290,
            [0.26, 0.2, 0.13, 0.13, 0.13, 0.15], size=36, row_h=74)
    out = [s.png()]
    fam = res.get("families") or {}
    if fam:
        s2 = Slide("各警報規則的成績", "2/2", f"檢驗期間：{hz[-1]['days']} 日內標普跌≥{hz[-1]['drawdown']*100:.0f}%；樣本少於 5 次不下結論")
        frows = []
        for name, fm in sorted(fam.items(), key=lambda kv: -kv[1]["episodes"])[:9]:
            r = fm["by_horizon"].get(hz[-1]["days"], {})
            vcol = GREEN if fm["verdict"] == "有用" else RED if fm["verdict"] == "反效果" else MUTED
            if r.get("episodes"):
                frows.append([(name, TEXT), (str(r["episodes"]), MUTED), (f"{r['hit_rate']:.0f}%", ORANGE),
                              (f"{r['base_rate']:.0f}%", MUTED), (fm["verdict"], vcol)])
            else:
                frows.append([(name, TEXT), ("0", MUTED), ("待評分", MUTED), ("—", MUTED), (fm["verdict"], vcol)])
        s2.table(["警報規則", "事件數", "命中率", "基準", "評語"], frows, 235, [0.34, 0.14, 0.17, 0.15, 0.2], size=34, row_h=72)
        out.append(s2.png())
    return out


def deck_table(title: str, header: Sequence[str], rows, widths, subtitle: str = "", size=36,
               per_page: int = 10, align: Optional[Sequence[str]] = None) -> List[bytes]:
    pages = [rows[i:i + per_page] for i in range(0, max(len(rows), 1), per_page)] or [[]]
    out = []
    for i, chunk in enumerate(pages, 1):
        s = Slide(title, f"{i}/{len(pages)}", subtitle)
        y0 = 225 if subtitle else 180
        rh = min(80, int((1010 - y0) / (len(chunk) + 1))) if chunk else 80
        s.table(header, chunk, y0, widths, size=size, row_h=rh, align=align)
        out.append(s.png())
    return out


def deck_tiles(title: str, items, subtitle: str = "", cols: int = 4) -> List[bytes]:
    out, per = [], cols * 4
    pages = [items[i:i + per] for i in range(0, len(items), per)] or [[]]
    for i, chunk in enumerate(pages, 1):
        s = Slide(title, f"{i}/{len(pages)}", subtitle)
        s.tiles(chunk, 215 if subtitle else 180, cols=cols, h=180)
        out.append(s.png())
    return out


def deck_kpis(title: str, kpis, notes: List[str], subtitle: str = "") -> List[bytes]:
    s = Slide(title, "1/1", subtitle)
    y = s.kpis(kpis[:4], 225 if subtitle else 180)
    if len(kpis) > 4:
        y = s.kpis(kpis[4:8], y + 26)
    y += 50
    for n in notes:
        y = s.paragraph(n, M, y, W - 2 * M, size=36) + 10
    return [s.png()]


# ------------------------------------------------------------------ AI text → slides
_HEADING_MD = re.compile(r"^\s*#{1,6}\s+(.+?)\s*#*\s*$")
_HEADING_BOLD = re.compile(r"^\s*\*\*([^*]+)\*\*\s*[:：]?\s*$")        # the WHOLE line is one bold span
_HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")


def _clean(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"__(.+?)__", r"\1", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)\*(?!\w)", r"\1", s)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return s.strip()


def parse_sections(md: str) -> List[Tuple[str, List[Tuple[str, object]]]]:
    """→ [(heading, [(kind, content)])]; kind ∈ para|bullet|table. Nothing is silently dropped."""
    sections: List[Tuple[str, List]] = [("", [])]
    table: List[List[str]] = []
    in_code = False

    def flush_table():
        nonlocal table
        if table:
            sections[-1][1].append(("table", table))
            table = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            flush_table()
            in_code = not in_code
            continue
        if in_code:
            if line.strip():
                sections[-1][1].append(("para", line.strip()))
            continue
        if not line.strip() or _HR.match(line):
            flush_table()
            continue
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            table.append([_clean(c) for c in cells])
            continue
        flush_table()
        m = _HEADING_MD.match(line) or _HEADING_BOLD.match(line)
        if m and len(_clean(m.group(1))) <= 60:
            sections.append((_clean(m.group(1)), []))
            continue
        b = re.match(r"^\s*([-*•]|\d+[.)])\s+(.*)$", line)
        if b:
            sections[-1][1].append(("bullet", _clean(b.group(2))))
        else:
            sections[-1][1].append(("para", _clean(line)))
    flush_table()
    out = []
    for h, c in sections:
        if c:
            out.append((h, c))
        elif h:                                    # heading with no body (e.g. last bold line) → keep as text
            out.append(("", [("para", h)]))
    return out


BODY_TOP, BODY_BOTTOM = 175, 985


def deck_text(title: str, md: str, engine_name: str = "") -> List[bytes]:
    """Render AI markdown as slides: one section per slide; long sections continue line-by-line,
    long tables are split by rows with the header repeated."""
    slides: List[Slide] = []
    body = font(38)
    lh = int(38 * 1.45)
    width = W - 2 * M

    def new_slide(heading: str, cont: bool) -> Tuple[Slide, int]:
        sl = Slide(title)
        slides.append(sl)
        y = BODY_TOP
        if heading:
            txt = f"{heading}（續）" if cont else heading
            sl.d.text((M, y + 30), txt, font=sl.fit(txt, 58, width, True), fill=YELLOW, anchor="lm")
            y += 100
        return sl, y

    for heading, items in parse_sections(md):
        s, y = new_slide(heading, False)
        for kind, content in items:
            if kind in ("para", "bullet"):
                indent = 42 if kind == "bullet" else 0
                lines = s.wrap(str(content), body, width - indent)
                for i, ln in enumerate(lines):
                    if y + lh > BODY_BOTTOM:
                        s, y = new_slide(heading, True)
                    if kind == "bullet" and i == 0:
                        s.d.ellipse((M + 4, y + 18, M + 20, y + 34), fill=ACCENT)
                    s.d.text((M + indent, y), ln, font=body, fill=TEXT)
                    y += lh
                y += 14
            else:
                rows = content
                ncol = max(len(r) for r in rows)
                rows = [r + [""] * (ncol - len(r)) for r in rows]
                head, data = rows[0], rows[1:]
                rh = 62
                i = 0
                while i < len(data) or (i == 0 and not data):
                    room = int((BODY_BOTTOM - y - 20) / rh) - 1           # rows that fit under the header
                    if room < 2:
                        s, y = new_slide(heading, True)
                        continue
                    chunk = data[i:i + room]
                    y = s.table(head, [[(c, TEXT) for c in r] for r in chunk], y + 10, [1 / ncol] * ncol,
                                size=32, row_h=rh, align=["l"] * ncol) + 30
                    i += len(chunk)
                    if not data:
                        break
                    if i < len(data):
                        s, y = new_slide(heading, True)
    n = len(slides)
    out = []
    for i, s in enumerate(slides, 1):
        s.d.rounded_rectangle((W - M - 150, H - 78, W - M, H - 36), 12, fill="#1F2630")
        s.d.text((W - M - 75, H - 57), f"{i}/{n}", font=font(26, True), fill=MUTED, anchor="mm")
        if engine_name:
            s.d.text((M, H - 57), f"AI：{engine_name}", font=font(24), fill="#5A6470", anchor="lm")
        out.append(s.png())
    return out


def deck_alert(title: str, alerts: List[Tuple[str, str, str]], ssi: Optional[float]) -> List[bytes]:
    """alerts: (severity, title, detail) — 4 per slide, paginated; details wrap to 2 lines (links sent as text)."""
    out: List[bytes] = []
    pages = [alerts[i:i + 4] for i in range(0, len(alerts), 4)] or [[]]
    for pi, chunk in enumerate(pages, 1):
        crit = any(a[0].startswith("🚨") for a in chunk)
        tag = f"{pi}/{len(pages)}" if len(pages) > 1 else ""
        sub = f"目前 SSI {ssi:.1f}" if ssi is not None and not _nan(ssi) else ""
        s = Slide(title, tag, sub)
        s.d.rectangle((0, 140, W, 150), fill=RED if crit else ORANGE)
        y = 205
        for sev, t, detail in chunk:
            col = RED if sev.startswith("🚨") else ORANGE if sev.startswith("⚠️") else ACCENT
            det_lines = [ln for ln in detail.split("\n") if ln.strip() and not ln.startswith("http")]
            det = s.wrap(" ".join(det_lines), font(30), W - 2 * M - 60)[:2]
            s.card((M, y, W - M, y + 185), outline=col, width=4)
            tl = s.wrap(t, font(40, True), W - 2 * M - 60)
            s.d.text((M + 30, y + 42), tl[0] + ("…" if len(tl) > 1 else ""), font=font(40, True), fill=col, anchor="lm")
            for k, ln in enumerate(det):
                s.d.text((M + 30, y + 100 + k * 44), ln, font=font(30), fill=TEXT, anchor="lm")
            y += 200
        out.append(s.png())
    return out


_WD = "一二三四五六日"


def deck_morning(engine, facts: dict, theme: str, title: str, session: str) -> List[bytes]:
    out: List[bytes] = []
    total = 5
    # 1. cover
    s = Slide(title, f"1/{total}", f"{session}｜美股交易日 {facts.get('trade_date', '—')}（紐約）")
    s.card((M, 220, W - M, 600), outline=YELLOW, width=4)
    s.d.text((M + 50, 275), "今日主題", font=font(40, True), fill=YELLOW, anchor="lm")
    y = 330
    for ln in s.wrap(theme or "（AI 研判產生中或暫無）", font(62, True), W - 2 * M - 100)[:3]:
        s.d.text((M + 50, y), ln, font=font(62, True), fill=TEXT)
        y += 84

    def kq(t, d=2):
        q = engine.market.q(t)
        return (fmt(q["price"], d), q.get("chg_pct")) if q else ("—", None)
    items = []
    for t, lab, inv in (("ES=F", "標普期貨", False), ("NQ=F", "那指期貨", False), ("^VIX", "VIX", True), ("^TNX", "美10年殖利率", True)):
        v, c = kq(t)
        col = MUTED if c is None else ((RED if c > 0 else GREEN) if inv else (GREEN if c > 0 else RED))
        items.append((lab, f"{v}  {fmt(c, 2, pct=True, sign=True)}", col))
    st = engine.stress
    items.append(("壓力指數 SSI", fmt(st.score if st else None, 1), level_color(st.score if st else None)))
    s.kpis(items, y=640, h=200)
    out.append(s.png())
    # 2. global tiles
    out.append(_markets(engine, f"2/{total}").png())
    # 3. sector rotation
    s = Slide("板塊與因子輪動", f"3/{total}", "依今日漲跌排序；看資金從哪裡流出、流向哪裡")
    rows = [[(r["name"], TEXT), (fmt(r.get("d1"), 2, pct=True, sign=True), pn(r.get("d1"))),
             (fmt(r.get("w1"), 1, pct=True, sign=True), pn(r.get("w1"))),
             (fmt(r.get("m1"), 1, pct=True, sign=True), pn(r.get("m1"))),
             (fmt(r.get("pct_52w"), 0) + "%", MUTED)] for r in facts.get("sectors", [])[:14]]
    s.table(["板塊 / 因子", "今日", "近1週", "近1月", "52週位置"], rows, 225, [0.32, 0.17, 0.17, 0.17, 0.17],
            size=32, row_h=min(62, int(785 / (len(rows) + 1))) if rows else 60)
    out.append(s.png())
    # 4. movers
    s = Slide("異動雷達：今天誰的波動不尋常？", f"4/{total}", "σ = 今日漲跌是自身平常波動的幾倍；|σ| ≥ 2 值得注意、≥ 3 為異常")
    rows = [[(m["name"] + ("（持股）" if m["holding"] else ""), YELLOW if m["holding"] else TEXT), (m["ticker"], MUTED),
             (fmt(m["chg"], 2, pct=True, sign=True), pn(m["chg"])),
             (f"{m['sigma']:+.1f}σ", RED if abs(m["sigma"]) >= 3 else ORANGE if abs(m["sigma"]) >= 2 else TEXT)]
            for m in facts.get("movers", [])[:10]]
    s.table(["標的", "代號", "今日", "異常程度"], rows, 225, [0.42, 0.2, 0.19, 0.19], size=36,
            row_h=min(70, int(785 / (len(rows) + 1))) if rows else 70)
    out.append(s.png())
    # 5. today's must-watch
    s = Slide("今日必看：數據與財報", f"5/{total}")
    s.card((M, 175, 720, 1000))
    s.d.text((M + 36, 225), "總經 / 央行", font=font(40, True), fill=ACCENT, anchor="lm")
    y = 285
    macro = facts.get("macro", [])
    if not macro:
        y = s.paragraph("今明兩天沒有重大總經數據（或需要 FRED 金鑰才能取得行事曆）", M + 36, y, 610, size=32, color=MUTED)
    for e in macro[:8]:
        y = s.paragraph(f"{e['date'][5:]}  {e['event']}", M + 36, y, 610, size=34) + 6
    er = facts.get("earnings", [])
    rows = [[(r["when"], MUTED), (r["symbol"], TEXT), (r["name"][:14], TEXT), (fmt(r["eps_fc"], 2), TEXT),
             (f"{(r['mcap'] or 0)/1e9:,.0f}B", MUTED)] for r in er[:10]]
    if rows:
        x0 = 750                                # table in the right column
        s.d.text((x0, 225), "重要財報（依市值）", font=font(40, True), fill=ACCENT, anchor="lm")
        cols = [0.14, 0.14, 0.40, 0.16, 0.16]
        width = W - M - x0
        xs = [x0]
        for w_ in cols[:-1]:
            xs.append(xs[-1] + w_ * width)
        rh = min(66, int(700 / (len(rows) + 1)))
        yy = 280
        for j, h in enumerate(["時段", "代號", "公司", "EPS預估", "市值"]):
            s._cell(xs[j], cols[j] * width, yy + rh / 2, h, MUTED, font(28, True), "l" if j < 3 else "r")
        for i, r in enumerate(rows):
            cy = yy + rh * (i + 1.5)
            for j, (txt, col) in enumerate(r):
                s._cell(xs[j], cols[j] * width, cy, txt, col, s.fit(txt, 32, cols[j] * width - 20, j == 1), "l" if j < 3 else "r")
    else:
        s.d.text((750, 225), "重要財報", font=font(40, True), fill=ACCENT, anchor="lm")
        s.paragraph("今日沒有市值 500 億美元以上或觀察名單內的公司公布財報（或 Nasdaq 資料暫時無法取得）。",
                    750, 290, W - M - 790, size=32, color=MUTED)
    out.append(s.png())
    return out


def deck_earnings_board(board: dict) -> List[bytes]:
    out: List[bytes] = []
    rows = []
    for d, lst in board.get("ahead", {}).items():
        wd = _WD[datetime.fromisoformat(d).weekday()]
        for r in lst:
            rows.append([(f"{d[5:]}（{wd}）", TEXT), (r["when"], MUTED), (r["symbol"], ACCENT), (r["name"][:18], TEXT),
                         (fmt(r["eps_fc"], 2), TEXT), (fmt(r["eps_ly"], 2), MUTED), (f"{(r['mcap'] or 0)/1e9:,.0f}B", MUTED)])
    if not rows:
        rows = [[("—", MUTED)] * 7]
    out += deck_table("本週華爾街重要財報", ["日期", "時段", "代號", "公司", "EPS 預估", "去年同期", "市值"], rows,
                      [0.15, 0.09, 0.11, 0.29, 0.12, 0.12, 0.12], subtitle="市值 ≥ 500 億美元或在觀察名單／持股內；時間為紐約時間",
                      size=32, per_page=11, align=["l", "l", "l", "l", "r", "r", "r"])
    prow = []
    for r in board.get("past", []):
        sp, rx = r.get("surprise"), r.get("reaction")
        if sp is None:
            verdict, vc = "資料缺", MUTED
        elif sp > 0 and (rx or 0) > 0:
            verdict, vc = "超預期・獲獎勵", GREEN
        elif sp > 0:
            verdict, vc = "超預期・賣消息", ORANGE
        elif (rx or 0) < 0:
            verdict, vc = "不如預期・受懲罰", RED
        else:
            verdict, vc = "不如預期・已反映", YELLOW
        prow.append([(r["symbol"], ACCENT), (r["name"][:14], TEXT),
                     (f"{fmt(r.get('eps_act'), 2)} / {fmt(r.get('eps_est'), 2)}", TEXT),
                     (fmt(sp, 1, pct=True, sign=True), pn(sp)), (fmt(rx, 1, pct=True, sign=True), pn(rx)), (verdict, vc)])
    if not prow:
        prow = [[("—", MUTED)] * 6]
    out += deck_table("上週財報成績單", ["代號", "公司", "EPS 實際 / 預估", "驚喜", "股價反應", "判定"], prow,
                      [0.10, 0.22, 0.2, 0.13, 0.13, 0.22], subtitle="股價反應 = 財報後第一個交易日漲跌；「賣消息」= 超預期但股價下跌",
                      size=32, per_page=11, align=["l", "l", "r", "r", "r", "r"])
    return out


# ------------------------------------------------------------------ Taiwan
def deck_taiwan(engine, title: str = "台股籌碼情報") -> List[bytes]:
    tw = engine.taiwan
    out: List[bytes] = []
    total = 4
    fu = tw.futures or {}
    # 1. overview
    s = Slide(title, f"1/{total}", f"證交所 / 期交所官方資料｜現貨資料日 {tw.asof or '—'}　期貨資料日 {fu.get('inst_date', '—')}")
    tw_q = engine.market.q("^TWII")
    twd = engine.market.q("TWD=X")
    f0 = tw.flows[0] if tw.flows else {}
    tx = fu.get("tx") or {}
    y = s.kpis([("加權指數", f"{fmt(tw_q['price'], 0)}  {fmt(tw_q.get('chg_pct'), 2, pct=True, sign=True)}" if tw_q else "—",
                 pn(tw_q.get("chg_pct")) if tw_q else MUTED),
                ("外資現貨（億）", fmt(f0.get("foreign"), 1, sign=True), pn(f0.get("foreign"))),
                ("外資期貨淨單（口）" + (f"｜日變化 {fmt(fu.get('oi_foreign_chg'), 0, sign=True)}" if fu.get("oi_foreign_chg") is not None else ""),
                 fmt(fu.get("oi_foreign"), 0, sign=True), pn(fu.get("oi_foreign"))),
                ("美元 / 台幣", f"{fmt(twd['price'], 3)}  {fmt(twd.get('chg_pct'), 2, pct=True, sign=True)}" if twd else "—",
                 (RED if (twd.get("chg_pct") or 0) > 0 else GREEN) if twd else MUTED)], y=225)
    ewt = engine.market.q("EWT")
    tsm, t2330 = engine.market.q("TSM"), engine.market.q("2330.TW")
    prem = None
    if tsm and t2330 and twd and t2330["price"] and twd["price"]:
        prem = (tsm["price"] / (t2330["price"] * 5 / twd["price"]) - 1) * 100      # 1 ADR = 5 common shares
    y = s.kpis([("台指期日盤（" + str(tx.get("date", "—"))[4:] + "）", f"{fmt(tx.get('last'), 0)}  {fmt(tx.get('pct'), 2, pct=True, sign=True)}", pn(tx.get("pct"))),
                ("隔夜美股 台灣ETF EWT", f"{fmt(ewt.get('chg_pct'), 2, pct=True, sign=True)}" if ewt else "—", pn(ewt.get("chg_pct")) if ewt else MUTED),
                ("台積電 ADR 溢價", fmt(prem, 1, pct=True, sign=True), ORANGE if (prem or 0) > 20 else TEXT),
                ("選擇權 P/C 未平倉比", f"{fmt((fu.get('pcr') or [{}])[0].get('oi'), 1)}%", TEXT)], y=y + 30)
    mg = tw.margin or {}
    if mg:
        s.paragraph(f"融資餘額（{mg['date']}）{mg['bal_bn']:,.0f} 億，單日 {mg['chg_pct']:+.2f}%"
                    + (f"、近 5 日 {mg['chg_5d_pct']:+.2f}%" if mg.get("chg_5d_pct") is not None else "")
                    + "；融資單日大減常代表斷頭賣壓。", M, y + 50, W - 2 * M, size=32, color=ORANGE if mg["chg_pct"] < -1.5 else MUTED)
        y += 110
    s.paragraph("解讀：外資期貨淨空單擴大（負值變更負）通常代表外資在避險或看空；P/C 比 > 100% 表示賣權部位較多、市場偏保守。"
                "台幣貶值（美元/台幣上升）常伴隨外資匯出；EWT 是台股收盤後在美股交易的台灣 ETF，可視為隔夜風向。", M, y + 50, W - 2 * M, size=32, color=MUTED)
    out.append(s.png())
    # 2. 5-day flows
    rows = [[(r["date"][5:], TEXT), (fmt(r["foreign"], 1, sign=True), pn(r["foreign"])),
             (fmt(r["trust"], 1, sign=True), pn(r["trust"])), (fmt(r["dealer"], 1, sign=True), pn(r["dealer"])),
             (fmt(r["total"], 1, sign=True), pn(r["total"]))] for r in tw.flows]
    s = Slide("三大法人現貨買賣超（近 5 日，億元）", f"2/{total}")
    if rows:
        tot = [("合計", YELLOW)] + [(fmt(sum(r[k] for r in tw.flows), 1, sign=True), pn(sum(r[k] for r in tw.flows)))
                                    for k in ("foreign", "trust", "dealer", "total")]
        s.table(["日期", "外資", "投信", "自營商", "三大法人合計"], rows + [tot], 200, [0.2, 0.2, 0.2, 0.2, 0.2], size=42, row_h=100)
    else:
        s.paragraph("證交所資料暫時無法取得。", M, 250, W - 2 * M, size=44)
    out.append(s.png())
    # 3. stock-level
    st = tw.stocks or {}
    s = Slide("外資個股買賣超（張）", f"3/{total}", f"資料日 {st.get('date', '—')}　左：外資買超前 8　右：外資賣超前 8")
    for col, key, ttl, c in ((M, "top_buy", "買超", GREEN), (W / 2 + 15, "top_sell", "賣超", RED)):
        s.card((col, 225, col + W / 2 - M - 15, 1000))
        s.d.text((col + 30, 275), f"外資{ttl}", font=font(40, True), fill=c, anchor="lm")
        yy = 350
        for r in st.get(key, [])[:8]:
            nm = f"{r['name']}（{r['code']}）"
            s.d.text((col + 30, yy), nm, font=s.fit(nm, 36, 480), fill=TEXT, anchor="lm")
            s.d.text((col + W / 2 - M - 50, yy), f"{r['foreign']:+,.0f}", font=font(38, True), fill=c, anchor="rm")
            yy += 80
    out.append(s.png())
    # 4. watch stocks + monthly revenue
    rows = []
    wmap = {r["code"]: r for r in st.get("watch", [])}
    for r in tw.revenue[:9]:
        w = wmap.get(r["code"], {})
        rows.append([(f"{r['name']}（{r['code']}）", TEXT), (r["ym"], MUTED), (f"{r['rev_bn']:,.0f}", TEXT),
                     (fmt(r["mom"], 1, pct=True, sign=True), pn(r["mom"])), (fmt(r["yoy"], 1, pct=True, sign=True), pn(r["yoy"])),
                     (fmt(r["ytd_yoy"], 1, pct=True, sign=True), pn(r["ytd_yoy"])),
                     (fmt(w.get("foreign"), 0, sign=True), pn(w.get("foreign")))])
    out += deck_table("權值股月營收 + 今日外資買賣超", ["公司", "營收月份", "月營收(億)", "月增", "年增", "累計年增", "外資(張)"],
                      rows or [[("資料暫缺", MUTED)] + [("—", MUTED)] * 6], [0.24, 0.12, 0.14, 0.12, 0.12, 0.13, 0.13],
                      subtitle="月營收每月 10 日前公布；年增率是 AI 供應鏈需求最直接的訊號", size=34, per_page=9)
    return out
