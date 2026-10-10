"""Site sections added in the 2026-10 expansion: stock scoring board (US / Taiwan / Hong Kong), guru 13F holdings and
insider Form 4 activity, US Treasury zone, sector rotation & breadth, and the time machine (daily snapshots)."""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import pandas as pd

from tools.sitekit import T, _CHARTS, card, cls, esc, line_chart, nice_ticks, num, tick_label
from wsb.data.stocks import theme_names


# ----------------------------------------------------------------- small helpers
def _bar(v: Optional[float], color: str = "var(--ac)") -> str:
    if v is None:
        return '<span class="muted">—</span>'
    return (f'<div class="sbar" title="{v:.0f}"><i style="width:{max(0, min(100, v)):.0f}%;background:{color}"></i>'
            f'<b>{v:.0f}</b></div>')


def _heat(v: Optional[float], scale: float = 10.0, d: int = 1) -> str:
    """Diverging cell: tint strength ∝ |v| / scale; the number is always printed (colour is never the only cue)."""
    if v is None:
        return '<td class="r muted">—</td>'
    a = min(abs(v) / scale, 1.0) * 55
    col = "var(--up)" if v > 0 else "var(--dn)"
    return f'<td class="r hm" style="background:color-mix(in srgb,{col} {a:.0f}%,transparent)">{v:+.{d}f}</td>'


def _usd(v: Optional[float]) -> str:
    if v is None:
        return "—"
    a = abs(v)
    if a >= 1e9:
        return f"${v / 1e9:,.1f}B"
    if a >= 1e6:
        return f"${v / 1e6:,.1f}M"
    if a >= 1e3:
        return f"${v / 1e3:,.0f}K"
    return f"${v:,.0f}"


def _tabset(prefix: str, items: List[tuple]) -> str:
    """items: [(zh, en, html)] → button row + panels, scoped to this card (JS toggles within .tabset only)."""
    btn, pan = [], []
    for i, (zh, en, body) in enumerate(items):
        on = " on" if i == 0 else ""
        btn.append(f'<button class="tab{on}" data-t="{prefix}{i}" data-en="{esc(en)}" type="button">{esc(zh)}</button>')
        pan.append(f'<div class="panel{on}" id="{prefix}{i}">{body}</div>')
    return f'<div class="tabset"><div class="tabs">{"".join(btn)}</div>{"".join(pan)}</div>'


# ----------------------------------------------------------------- stock scoring board
SCORE_COLORS = [(70, "#2fbf71"), (55, "#3987e5"), (40, "#8f8d86"), (0, "#e5484d")]


def _score_color(v: float) -> str:
    return next(c for t, c in SCORE_COLORS if v >= t)


def _reason_chips(r: Dict) -> str:
    out = []
    rs = r.get("reasons", [])
    rs = (rs[:1] + sorted(rs[1:], key=lambda x: x.get("s", 0)))[:5]          # warnings (RSI overheat…) never get cut off
    for x in rs + [{"zh": i["zh"], "en": i["en"], "s": 1 if i["val"] > 0.15 else -1 if i["val"] < -0.15 else 0}
                                         for i in r.get("intel_inputs", [])][:3]:
        c = "rcp" if x.get("s", 0) > 0 else "rcn" if x.get("s", 0) < 0 else ""
        out.append(f'<span class="rc {c}">{T(x["zh"], x["en"])}</span>')
    return "".join(out)


def _theme_chip(th: str) -> str:
    return f'<span class="thc">{T(th, theme_names().get(th, th))}</span>'


def _theme_chips(rows: List[Dict], tid: str) -> str:
    """Clickable 族群 buttons (with counts) + a 'group by theme' switch for the entry-signal table."""
    cnt: Dict[str, int] = {}
    for r in rows:
        cnt[r.get("theme", "其他")] = cnt.get(r.get("theme", "其他"), 0) + 1
    order = sorted(cnt, key=lambda t: list(theme_names()).index(t) if t in theme_names() else 99)
    btn = "".join(f'<button type="button" class="sgtb" data-th="{esc(t)}" data-for="{tid}">{T(t, theme_names().get(t, t))} <b>{cnt[t]}</b></button>'
                  for t in order)
    return (f'<div class="sgth"><span class="small muted">{T("族群", "Theme")}</span>'
            f'<button type="button" class="sgtb on" data-th="" data-for="{tid}">{T("全部", "All")}</button>{btn}'
            f'<label class="small muted sggl"><input type="checkbox" class="sgg" data-for="{tid}" checked> {T("依族群分組顯示", "Group by theme")}</label></div>')


def _theme_filter(rows: List[Dict], tid: str) -> str:
    """Dropdown that hides table rows (and their reason rows) of other 族群 — rows carry data-th."""
    ths = sorted({r.get("theme", "其他") for r in rows}, key=lambda t: list(theme_names()).index(t) if t in theme_names() else 99)
    opts = "".join(f'<option value="{esc(t)}" data-en="{esc(theme_names().get(t, t))}">{esc(t)}</option>' for t in ths)
    return (f'<label class="small muted">{T("族群篩選", "Filter by theme")} <select class="btn thf" data-for="{tid}">'
            f'<option value="" data-en="All">全部</option>{opts}</select></label>')


def _score_table(m: Dict) -> str:
    rows = []
    tid = f"st_{m['key']}"
    for r in m["rows"]:
        chg = r.get("chg5")
        th = esc(r.get("theme", "其他"))
        rows.append(
            f'<tr data-th="{th}" data-q="{esc((r["name"] + " " + r["name_en"] + " " + r["code"]).lower())}"><td class="r muted">{r["rank"]}</td>'
            f'<td class="nw"><b>{T(r["name"], r["name_en"])}</b><span class="tk">{esc(r["code"])}</span>{_theme_chip(r.get("theme", "其他"))}</td>'
            f'<td>{_bar(r["score"], _score_color(r["score"]))}</td>'
            f'<td class="r opt">{num(r["tech"], 0)}</td><td class="r opt">{num(r.get("intel"), 0)}</td>'
            f'<td class="r opt {cls(chg)}">{num(chg, 1, sign=True)}</td>'
            f'<td class="r {cls(r.get("r1d"))}">{num(r.get("r1d"), 1, sign=True, pct=True)}</td>'
            f'<td class="r opt {cls(r.get("r1m"))}">{num(r.get("r1m"), 1, sign=True, pct=True)}</td>'
            f'<td class="r {cls(r.get("r6"))}">{num(r.get("r6"), 0, sign=True, pct=True)}</td>'
            f'<td class="r opt">{num(r.get("rsi"), 0)}</td></tr>'
            f'<tr class="why" data-th="{th}"><td></td><td colspan="9">{_reason_chips(r)}</td></tr>')
    br = m.get("breadth") or {}
    chips = (f'<div class="chips"><span class="chip">{T("評分池", "Universe")} {br.get("n", 0)} {T("檔", "names")}</span>'
             f'<span class="chip">{T("站上 200 日線", "Above 200d")} {num(br.get("above200"), 0)}%</span>'
             f'<span class="chip">{T("站上 50 日線", "Above 50d")} {num(br.get("above50"), 0)}%</span>'
             f'<span class="chip">{T("創 52 週新高", "52w highs")} {br.get("new_high", 0)} / {T("新低", "lows")} {br.get("new_low", 0)}</span>'
             f'<span class="chip">{T("資料日", "As of")} {esc(m.get("asof") or "—")}</span></div>')
    miss = (f'<p class="note">{T("暫缺資料：", "Missing: ")}{esc("、".join(m["missing"][:12]))}</p>' if m.get("missing") else "")
    return (chips + _theme_filter(m["rows"], tid) + f'<div class="scroll"><table class="score" id="{tid}"><thead><tr>'
            f'<th class="r">#</th><th>{T("個股", "Stock")}</th><th>{T("綜合分數", "Score")}</th><th class="r opt">{T("技術", "Tech")}</th>'
            f'<th class="r opt">{T("情報", "Intel")}</th><th class="r opt">{T("5日分數變化", "5d Δ")}</th><th class="r">{T("今日", "1D")}</th>'
            f'<th class="r opt">{T("1月", "1M")}</th><th class="r">{T("6月", "6M")}</th><th class="r opt">RSI</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>' + miss)


def sec_scores(eng) -> str:
    sc = getattr(eng, "scores", None) or {}
    if not sc.get("available"):
        return card("個股評分表", "Stock scoring board", f'<p class="muted">{T("個股價格資料暫時取不到", "Stock data unavailable right now")}</p>', "wide")
    items = [(m["label"], m["label_en"], _score_table(m)) for m in sc["markets"].values()]
    note = T("綜合分數 = 技術面 60% ＋ 情報面 40%（情報面資料不足時只用技術面）。技術面在同一市場內排名：趨勢（50／200 日線）、動能（12-1、6、3 個月報酬）、"
             "相對大盤強弱、距 52 週高點、量能（上漲日 vs 下跌日成交量）、波動度，RSI 過熱扣分。情報面 50 為中性：新聞語氣（Google 新聞標題、關鍵字判讀）、"
             "美股場外放空比例（FINRA）、內部人買賣（SEC Form 4）、追蹤大師加減碼（13F）、台股外資＋投信 5 日買賣超（證交所）。"
             "這是依公開資料計算的量化篩選，反映的是「現在的強弱」而不是預測，也不是買賣建議。",
             "Score = 60% technical + 40% intel (technical only when intel inputs are missing). Technical factors are ranked within each "
             "market: trend, momentum, relative strength, distance from 52-week high, up/down volume, volatility, minus an RSI overheat "
             "penalty. Intel (50 = neutral): headline tone, US off-exchange short ratio (FINRA), insider buying/selling (SEC Form 4), "
             "tracked managers' 13F changes, Taiwan foreign + trust 5-day net buying. A rules-based screen of current strength — "
             "not a forecast and not investment advice.")
    search = (f'<div class="sbox"><input type="search" id="stockQ" class="btn" placeholder="搜尋代號或名稱（含全市場），例如 NU、台積電、0700" '
              f'aria-label="search"><span class="muted small" id="stockQn"></span><div class="fmres" id="stockQfm"></div></div>')
    return card("個股評分表（由高到低）", "Stock scoring board (high → low)", search + _tabset("sc", items) + f'<p class="note">{note}</p>', "wide")


def sec_scores_mini(eng) -> str:
    """Overview teaser: top 5 per market, linking to the full board."""
    sc = getattr(eng, "scores", None) or {}
    if not sc.get("available"):
        return ""
    cols = []
    for m in sc["markets"].values():
        lis = "".join(f'<li><span class="nw">{T(r["name"], r["name_en"])}<span class="tk">{esc(r["code"])}</span></span>'
                      f'<b style="color:{_score_color(r["score"])}">{r["score"]:.0f}</b></li>' for r in m["rows"][:5])
        cols.append(f'<div><h4>{T(m["label"], m["label_en"])}</h4><ol class="top5">{lis}</ol></div>')
    return card("個股評分前五名", "Top-5 stock scores",
                f'<div class="g3">{"".join(cols)}</div><p class="note"><a href="#scores" class="golink" data-p="scores">'
                + T("看完整評分表與理由 →", "Full board with reasons →") + "</a></p>", "wide")


# ----------------------------------------------------------------- technical entry signals
PAT_COL = {"pullback": "#2fbf71", "breakout": "#3987e5", "golden": "#c9a227", "oversold": "#ec835a",
           "shallow": "#14b8a6", "vcp": "#8b5cf6", "high52": "#e879f9", "macd": "#94a3b8"}
TIER_COL = {"A": "#c9a227", "B": "#2fbf71", "C": "#3987e5", "D": "#6b7280"}
TIER_T = {"A": ("A ★ 規則精選", "A ★ Top setup"), "B": ("B 在進場區內", "B In the zone"), "C": ("C 有訊號・等拉回", "C Wait for pullback"),
          "D": ("D 快成立", "D Almost there")}


def _tier(t: Optional[str]) -> str:
    return f'<span class="tier t{t}" title="{esc(TIER_T[t][0])}">{t}</span>' if t else ""


def _pat_detail(h: Dict) -> tuple:
    k = h["pattern"]
    if k == "pullback":
        zh, en = f"回測均線後轉強（RSI {num(h.get('rsi'), 0)}）", f"Bounced off its moving average (RSI {num(h.get('rsi'), 0)})"
    elif k == "breakout":
        zh, en = f"突破前 20 日高點，成交量 {num(h.get('vol_ratio'), 1)} 倍", f"Broke the prior 20-day high on {num(h.get('vol_ratio'), 1)}× volume"
    elif k == "golden":
        zh, en = "50 日線上穿 200 日線，或站回 200 日線", "50-day crossed above 200-day, or price reclaimed the 200-day"
    elif k == "shallow":
        zh, en = f"均線多頭排列，回測 10 日線後收紅（RSI {num(h.get('rsi'), 0)}）", "Stacked averages; dipped to the 10-day and closed up"
    elif k == "vcp":
        zh, en = f"波動收斂成窄箱後放量突破，成交量 {num(h.get('vol_ratio'), 1)} 倍", f"Tight range, then a breakout on {num(h.get('vol_ratio'), 1)}× volume"
    elif k == "high52":
        zh, en = f"收盤創 52 週新高，成交量 {num(h.get('vol_ratio'), 1)} 倍", f"Closed at a new 52-week high on {num(h.get('vol_ratio'), 1)}× volume"
    elif k == "macd":
        zh, en = "多頭趨勢中 MACD 線上穿訊號線", "MACD crossed above its signal line in an uptrend"
    else:
        zh, en = f"RSI 跌破 30 後反彈（逆勢，風險較高）", "Bounce after RSI < 30 (counter-trend, higher risk)"
    return zh, en


ST_COL = {"signal": "#2fbf71", "near_pullback": "#3987e5", "near_breakout": "#3987e5", "near_golden": "#3987e5",
          "near_oversold": "#ec835a", "extended": "#c9a227", "uptrend": "#6b7280", "range": "#6b7280", "downtrend": "#d03b3b",
          "nodata": "#6b7280"}


def _q(r: Dict) -> str:
    from wsb.analytics.patterns import TAGS
    tg = " ".join(TAGS[k][0] for k in r.get("tags") or [] if k in TAGS)
    ex = " 過熱 力竭" if (r.get("exh") or {}).get("n", 0) >= 2 else ""
    return esc((r["name"] + " " + r["name_en"] + " " + r["code"] + " " + tg + ex).lower())


def _tagchips(r: Dict) -> str:
    """Chart-pattern tags (blue) and the overheating badge (red) under the stock name in the signal table."""
    from wsb.analytics.patterns import TAGS, TAG_DEF, exh_text
    out = "".join(f'<span class="tagc" title="{esc(TAG_DEF[k])}">{T(*TAGS[k])}</span>' for k in r.get("tags") or [] if k in TAGS)
    ex = r.get("exh") or {}
    if ex.get("n", 0) >= 2:
        out += f'<span class="tagc ex" title="{esc(exh_text(ex))}">{T("過熱 ×%d" % ex["n"], "Overheated ×%d" % ex["n"])}</span>'
    return f"<br>{out}" if out else ""


SG_TIER = {"B": ("在進場區內", "In the zone"), "C": ("等拉回", "Wait for pullback"), "D": ("快成立", "Almost there"), "O": ("其他狀態", "Other")}


LV_T = {"pull": ("回測", "dip to"), "break": ("突破", "break"), "ma200": ("年線", "200-day")}


def _levels(lv) -> str:
    """No signal yet → no entry zone; show the price the rules are waiting for instead (details in the expanded row)."""
    if not lv:
        return '<span class="muted">—</span>'
    return "<br>".join(f'<span class="muted">{T(*LV_T[x["k"]])}</span> {num(x["p"], 2)}' for x in lv[:2])


def _ref_zone(pl: Optional[Dict]) -> str:
    """Table cell for a stock without a signal: its add-on reference zone (muted = not a signal), basis underneath."""
    if not pl:
        return '<span class="muted">—</span>'
    dot = f' <i class="zd{" in" if pl.get("in_zone") else ""}"></i>'
    return (f'<span class="refz">{num(pl["zone_lo"], 2)}–{num(pl["zone_hi"], 2)}</span>{dot}'
            f'<br><span class="muted small">{T(pl.get("basis_label", ""), pl.get("basis_en", ""))}</span>')


def _watch_rows(m: Dict) -> List[str]:
    """Stocks without an active signal: status + the exact condition that would create a signal (detail row on click)."""
    out = []
    for r in [x for x in m.get("all", []) if not x.get("signal")]:
        th = esc(r.get("theme", "其他"))
        st = r["status"]
        tg = r.get("tier") or "O"
        when = (f'<b class="act">▶ {T("何時才算買點", "What would trigger an entry")}：</b>{T(st.get("when", "—"), st.get("when_en", "—"))}'
                if st.get("when") else "")
        lab = (f'<span class="sgb s{tg}">{T(*SG_TIER[tg])}</span>' if tg == "D" else "")
        pl = st.get("plan")
        ref, give = "", '<td class="r muted">—</td>'
        if pl:
            give = f'<td class="r nw muted">{num(pl["inv"], 2)}<span class="small"> -{num(pl["risk_pct"], 1)}%</span></td>'
            ref = ('<b class="act">▶ ' + T("加碼參考區（尚無訊號，非買點）", "Add-on reference zone (no signal yet)") + "：</b>"
                   + T(pl.get("zone", ""), pl.get("zone_en", "")) + "；" + T(pl.get("where", ""), pl.get("where_en", "")) + "。"
                   + '<br><b class="act">▶ ' + T("參考失效線", "Reference give-up") + "：</b>"
                   + T("收盤跌破 %.2f（距參考區中點 -%.1f%%）" % (pl["inv"], pl["risk_pct"]),
                       "a close below %.2f (-%.1f%% from the zone middle)" % (pl["inv"], pl["risk_pct"])) + "。<br>")
        lv = st.get("levels")
        lvt = ('<div class="muted">' + T("觀察價：", "Watch levels: ") + "、".join(
            f'{T(*LV_T[x["k"]])} {num(x["p"], 2)}' for x in lv[:3]) + "</div>") if lv else ""
        out.append(f'<tr class="sm" data-th="{th}" data-q="{_q(r)}" data-tier="{tg}"><td>{lab}</td>'
                   f'<td class="nw"><b>{T(r["name"], r["name_en"])}</b><span class="tk">{esc(r["code"])}</span>{_theme_chip(r.get("theme", "其他"))}{_tagchips(r)}</td>'
                   f'<td><span class="pill"><i class="sw" style="background:{ST_COL.get(st["status"], "#6b7280")}"></i>{T(st["label"], st["label_en"])}</span></td>'
                   f'<td>{_bar(r["strength"], "#6b7280")}</td><td class="r">{num(r.get("price"), 2)}</td>'
                   f'<td class="r nw">{_ref_zone(pl) if pl else _levels(lv)}</td>{give}<td class="r muted">▸</td></tr>'
                   f'<tr class="sd" data-th="{th}" data-tier="{tg}"><td></td><td colspan="7" class="small">{ref}{when}'
                   f'<div class="muted">{T(st.get("why", ""), st.get("why_en", ""))}</div>{lvt}</td></tr>')
    return out


def _edge(b: Dict) -> Optional[float]:
    return None if b.get("win") is None or b.get("base_win") is None else b["win"] - b["base_win"]


def _signal_table(m: Dict) -> str:
    if not m.get("all") and not m["rows"]:
        return f'<p class="muted">{T("目前沒有符合條件的訊號。", "No qualifying signals right now.")}</p>'
    tid = f"sgt_{m['key']}"
    rows = []
    for r in sorted(m["rows"], key=lambda r: ("BC".index(r.get("tier") if r.get("tier") in ("B", "C") else "B"), -r["strength"])):
        th = esc(r.get("theme", "其他"))
        tg = "B" if r.get("tier") in ("A", "B") else "C"
        pills = "".join(f'<span class="pill"><i class="sw" style="background:{PAT_COL[h["pattern"]]}"></i>{T(h["label"], h["label_en"])}</span>'
                        for h in r["patterns"][:2]) + (f'<span class="muted small"> +{len(r["patterns"]) - 2}</span>' if len(r["patterns"]) > 2 else "")
        new = f' <span class="pill newp">{T("新", "NEW")}</span>' if r.get("new") else ""
        det = "；".join(T(*_pat_detail(h)) for h in r["patterns"])
        pl = r["patterns"][0].get("plan") or {}
        zone = (f'{num(pl.get("zone_lo"), 2)}–{num(pl.get("zone_hi"), 2)}' if pl else "—")
        dot = f' <i class="zd{" in" if pl.get("in_zone") else ""}" title="{"in zone" if pl.get("in_zone") else "outside"}"></i>' if pl else ""
        rrv = pl.get("rr")
        rr = T("，報酬／風險約 %.1f 倍" % rrv, ", reward/risk ≈ %.1f×" % rrv) if rrv else ""
        inv_v, risk_v = r["inv"], r["risk_pct"]
        give = T("收盤跌破 %.2f（距現價 -%.1f%%）" % (inv_v, risk_v), "a close below %.2f (-%.1f%%)" % (inv_v, risk_v))
        over = ""
        if pl.get("target"):
            tg_, tp = pl["target"], pl["target_pct"]
            over = ('<b class="act">▶ ' + T("上方壓力", "Overhead") + "：</b>"
                    + T("52 週高點 %.2f（+%.0f%%）" % (tg_, tp), "52-week high %.2f (+%.0f%%)" % (tg_, tp)) + rr + "。")
        action = ('<b class="act">▶ ' + T("何時買（規則參考）", "When (rule reference)") + "：</b>"
                  + T(pl.get("zone", ""), pl.get("zone_en", "")) + "；" + T(pl.get("where", ""), pl.get("where_en", "")) + "。"
                  + '<br><b class="act">▶ ' + T("何時放棄", "Give up if") + "：</b>" + give + "。" + (("<br>" + over) if over else ""))
        rows.append(f'<tr class="sm" data-th="{th}" data-q="{_q(r)}" data-tier="{tg}"><td><span class="sgb s{tg}">{T(*SG_TIER[tg])}</span></td>'
                    f'<td class="nw"><b>{T(r["name"], r["name_en"])}</b><span class="tk">{esc(r["code"])}</span>{_theme_chip(r.get("theme", "其他"))}{_tagchips(r)}</td>'
                    f'<td>{pills}{new}</td><td>{_bar(r["strength"], _score_color(r["strength"]))}</td>'
                    f'<td class="r">{num(r["price"], 2)}</td><td class="r nw">{zone}{dot}</td>'
                    f'<td class="r nw">{num(r["inv"], 2)}<span class="muted small"> -{num(r["risk_pct"], 1)}%</span></td><td class="r muted">▸</td></tr>'
                    f'<tr class="sd" data-th="{th}" data-tier="{tg}"><td></td><td colspan="7" class="small">{action}'
                    f'<div class="muted">{det}　{T("首次出現 " + r["since"], "first seen " + r["since"])}</div></td></tr>')
    rows += _watch_rows(m)
    cnt = {k: 0 for k in SG_TIER}
    for r in m["rows"]:
        cnt["B" if r.get("tier") in ("A", "B") else "C"] += 1
    for r in m.get("all", []):
        if not r.get("signal"):
            cnt[r.get("tier") or "O"] += 1
    first = "all"                                           # default: every stock, grouped by theme
    pills = "".join(f'<button type="button" class="sgp{" on" if k == first else ""}" data-v="{k}" data-for="{tid}">{T(*SG_TIER[k])} <b>{cnt[k]}</b></button>'
                    for k in ("B", "C", "D", "O")) + \
        f'<button type="button" class="sgp{" on" if first == "all" else ""}" data-v="all" data-for="{tid}">{T("全部", "All")} <b>{sum(cnt.values())}</b></button>'
    bt = m.get("backtest") or {}
    brow = "".join(
        f'<tr><td><span class="pill"><i class="sw" style="background:{PAT_COL[k]}"></i>{T(*PATTERNS_T[k])}</span></td><td class="r">{b.get("n", 0)}</td>'
        f'<td class="r">{num(b.get("win"), 0, pct=True)}</td><td class="r {cls(b.get("avg"))}">{num(b.get("avg"), 1, sign=True, pct=True)}</td>'
        f'<td class="r muted">{num(b.get("base_win"), 0, pct=True)} / {num(b.get("base_avg"), 1, sign=True, pct=True)}</td>'
        f'<td class="r {cls(_edge(b))}">{num(_edge(b), 0, sign=True)}</td></tr>'
        for k, b in bt.items())
    bt_html = (f'<details class="sgx"><summary>{T("這些型態在本市場過去約兩年的表現", "How these patterns did here (~2 years)")}</summary>'
               f'<div class="scroll"><table class="mini"><thead><tr><th>{T("型態", "Pattern")}</th><th class="r">{T("次數", "n")}</th>'
               f'<th class="r">{T("20 日後上漲比例", "Up after 20d")}</th><th class="r">{T("平均報酬", "Avg return")}</th>'
               f'<th class="r">{T("任一天（基準）", "Any day (base)")}</th><th class="r">{T("比基準多（百分點）", "Edge (pp)")}</th>'
               f'</tr></thead><tbody>{brow}</tbody></table></div>'
               f'<p class="note">{T("「比基準多」接近 0 代表這個型態在這段期間並沒有比隨便哪一天進場更好；樣本只有約兩年、而且同一段期間同時用來定義規則，僅供參考。", "An edge near 0 means no better than a random day.")}'
               f'　{T("資料日", "As of")} {esc(m["asof"])}・{T("掃描", "Scanned")} {m["n_universe"]} {T("檔", "names")}</p></details>')
    return (f'<div class="sgbar"><div class="sgps">{pills}</div></div>{_theme_chips(m.get("all") or m["rows"], tid)}'
            f'<div class="scroll"><table class="score sgt" id="{tid}"><thead><tr><th>{T("分級", "Tier")}</th>'
            f'<th>{T("個股", "Stock")}</th><th>{T("型態／狀態", "Pattern / status")}</th><th>{T("強度", "Strength")}</th><th class="r">{T("現價", "Price")}</th>'
            f'<th class="r">{T("進場／加碼參考區", "Entry / add-on zone")}</th><th class="r">{T("失效線", "Give-up")}</th><th></th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>' + bt_html)


_ST_T = {"signal": ("有買點訊號", "Signal"), "near_pullback": ("接近回檔買點", "Near pullback"), "near_breakout": ("接近突破", "Near breakout"),
         "near_golden": ("接近黃金交叉", "Near golden cross"), "near_oversold": ("接近超賣", "Near oversold"), "extended": ("多頭但漲多", "Extended"),
         "uptrend": ("多頭整理", "Uptrend"), "range": ("盤整", "Range"), "downtrend": ("空頭趨勢", "Downtrend"), "nodata": ("資料不足", "No data")}


PATTERNS_T = {"pullback": ("多頭回檔到均線", "Pullback to MA in uptrend"), "breakout": ("帶量突破", "Volume breakout"),
              "golden": ("黃金交叉／站回年線", "Golden cross / 200-day reclaim"), "oversold": ("超賣反彈（逆勢）", "Oversold bounce"),
              "shallow": ("強勢股淺回檔", "Shallow dip, strong trend"), "vcp": ("收斂後突破", "Tight-range breakout"),
              "high52": ("創 52 週新高", "New 52-week high"), "macd": ("MACD 黃金交叉", "MACD bullish cross")}


def sec_picks_mini(eng) -> str:          # removed from the page (kept for older imports)
    return ""


def sec_signals(eng) -> str:
    sg = getattr(eng, "signals", None) or {}
    if not sg.get("available"):
        return card("技術面買點訊號", "Technical entry signals", f'<p class="muted">{T("個股價格資料暫時取不到", "Stock data unavailable right now")}</p>', "wide")
    warn = T("⚠️ 規則篩選（均線、動能、量能），只說明現在出現哪種技術型態，不是買進建議；收盤跌破失效線＝型態失敗。",
             "⚠️ Rules-based screen of technical setups — not a recommendation. A close below the give-up line means the setup failed.")
    items = [(m["label"], m["label_en"], _signal_table(m)) for m in sg["markets"].values()]
    howto = (f'<details class="sgx"><summary>{T("怎麼看「何時買」與分級", "How to read it")}</summary><ol class="small">'
             f'<li>{T("「在進場區內」：規則條件已成立、現價也在進場參考區內。點那一列看「▶ 何時買／何時放棄」。", "In the zone: the rule fired and the price is inside the entry zone. Click the row for details.")}</li>'
             f'<li>{T("「等拉回」：訊號已成立，但現價已離開區間；區間價位可當掛單參考，回到區間內才符合規則。", "Wait for pullback: signal fired but price left the zone; the zone works as a limit-order reference.")}</li>'
             f'<li>{T("「快成立」：還沒有訊號，但離成立只差一步；點開會寫要到哪個價位、出現什麼條件。訊號一成立 Discord 會推播。", "Almost there: the exact trigger price/condition is in the detail row.")}</li>'
             f'<li>{T("每一檔都有參考區：有買點訊號的是「進場參考區」（實心字）；還沒有訊號的是「加碼參考區」（虛線底），依目前狀態找最近的支撐——多頭看 20／50 日線、接近突破看突破後回測前高、空頭或接近黃金交叉要先站回 200 日線、接近超賣看 10 日低點（逆勢）。加碼參考區只是「如果要加碼，規則上比較合理的價位」，不是買點；標「需先站上／站回」的代表條件還沒成立。失效線的 % 是從參考區中點算起。點那一列看完整條件與觀察價。", "Every stock has a reference zone: an entry zone for active signals, and an add-on reference zone (dotted) for the rest, built from the nearest support for its status. It is not a signal.")}</li>'
             f'<li>{T("失效線：收盤跌破代表型態失敗。進場區寬度依每檔股票平常的波動調整（3%–10%）。綠點＝現價在區內。", "Give-up line: a close below it fails the setup. Zone width scales with volatility; green dot = price inside.")}</li>'
             f'<li>{T("股名下方的藍色小標籤是技術型態（布林壓縮、W 底、箱型突破／假突破、20／60 日線交叉），紅色「過熱」＝同時出現 2 個以上力竭警示（RSI 過熱、離均線過遠、頂背離、價漲量縮、高檔爆量收黑）；滑鼠移上去看定義。搜尋框也可以直接搜「W 底」「過熱」。", "Blue tags = chart patterns; red = two or more exhaustion flags. Hover for definitions.")}</li>'
             f'<li>{T("技術面規則抓不到「基本面成長、估值便宜」的股票（例如營收快速成長的公司），那類請看「成長估值」頁。", "Fundamental growth-at-a-value names are on the Growth valuation page.")}</li></ol>'
             f'<p class="small muted">{T(SIG_DEFS[0], SIG_DEFS[1])}</p></details>')
    search = (f'<div class="sbox"><input type="search" id="sigQ" class="btn" placeholder="搜尋代號或名稱（含全市場），例如 NU、台積電" aria-label="search">'
              f'<span class="muted small" id="sigQn"></span><div class="fmres" id="sigQfm"></div></div>')
    return card("技術面買點訊號", "Technical entry signals", f'<p class="small muted">{warn}</p>' + search + howto + _tabset("sg", items), "wide")


SIG_DEFS = ("型態定義：多頭回檔＝股價在上升的 200 日線之上、50 日線在 200 日線之上，最近 3 天從 10 日高點拉回 3% 以上、回測 20 或 50 日線後收紅；帶量突破＝收盤突破前 20 日最高價、"
            "量 ≥ 50 日均量 1.5 倍且在 50 日線之上；黃金交叉＝50 日線 10 天內上穿 200 日線，或站回年線；超賣反彈＝RSI 5 天內跌破 30 後站回 5 日線（逆勢）；"
            "強勢股淺回檔＝10＞20＞50＞200 日線且上彎，回測 10 日線後收紅；收斂後突破＝近 10 天波動縮到前 50 天的 6 成以下、箱體 ≤12%，放量（≥1.3 倍）突破箱頂；"
            "創 52 週新高＝收盤超過前 252 日最高且量 ≥1.2 倍；MACD 黃金交叉＝多頭趨勢中 MACD 線上穿訊號線。強度＝型態基礎分＋綜合分數＋量能＋失效線距離＋該型態在本市場的歷史勝率。",
            "Pattern definitions: pullback, volume breakout, golden cross, oversold bounce, shallow dip, tight-range breakout, 52-week high, MACD cross.")


# ----------------------------------------------------------------- full market (全市場)
def _fm_summary() -> str:
    from wsb.analytics import fullscan as FS
    chips = []
    for mk in ("us", "tw", "hk"):
        d = FS.published(mk)
        if not d:
            continue
        pend = d.get("pending") or 0
        extra = T(f"，還有 {pend} 檔資料補抓中", f", {pend} still loading") if pend else ""
        chips.append(f'<span class="chip">{T(d["label"], d["label_en"])} {d["n"]} {T("檔", "names")}'
                     f'（{T("資料日", "as of")} {esc(d["asof"])}{extra}）</span>')
    return f'<div class="chips">{"".join(chips)}</div>' if chips else \
        f'<p class="muted">{T("全市場資料第一次建立中（會分幾次補齊），稍後重新整理即可。", "The full-market database is being built; check back later.")}</p>'


def sec_fullmarket(eng, mode: str = "score") -> str:
    """Shell for the client-side full-market table (data loaded from market/<mk>.json only when opened)."""
    title = ("全市場排行（美股市值 10 億美元以上、台股上市＋上櫃、港股主板）", "Full-market ranking") if mode == "score" else \
        ("全市場個股・進場／加碼參考區（美股約 2,500 檔、台股、港股）", "Every stock: entry / add-on zones")
    note = T("全市場資料每天收盤後更新，只算技術面（情報面只有上方精選池才有）。分數在同一個市場內排名；族群為交易所／Nasdaq 官方產業分類。"
             "搜尋框輸入任何代號或名稱都會一起查全市場。", "Updated daily, technical only; ranks within each market; official industry groups.")
    if mode != "score":
        note = T("列出全市場每一檔：有訊號的顯示進場參考區，其餘顯示加碼參考區（括號註明「參考」）。預設排序：訊號且現價在區內 → 現價在加碼參考區內 → "
                 "訊號等拉回 → 快成立 → 其他（同一類再依強度）。想找「現在價位比較合規則」的股票，選「現價在參考區內」。點任一列看完整條件、技術型態與過熱警示。"
                 "全市場資料每天收盤後更新、只算技術面，不是買賣建議。", "Every stock in the market with its entry or add-on zone. Updated daily; technical only; not advice.")
    btns = "".join(f'<button class="tab{" on" if i == 0 else ""}" data-fmk="{k}" type="button">{T(*FM_LABEL[k])}</button>'
                   for i, k in enumerate(("us", "tw", "hk")))
    return card(*title,
                _fm_summary() + f'<div class="fm" data-mode="{mode}"><div class="tabs">{btns}</div>'
                f'<div class="fmctl">' + (f'<select class="btn fmtier"><option value="ALL" data-en="All stocks">全部個股</option>'
                                          f'<option value="IN" data-en="Price inside its zone">現價在參考區內（訊號＋加碼參考）</option>'
                                          f'<option value="ABC" data-en="With a signal">有訊號（在區內＋等拉回）</option>'
                                          f'<option value="AB" data-en="Signal, in the zone">有訊號・在進場區內</option>'
                                          f'<option value="C" data-en="Wait for pullback">有訊號・等拉回</option><option value="D" data-en="Almost there">快成立</option>'
                                          f'<option value="EX" data-en="Overheating">過熱警示</option></select>'
                                          f'<input class="btn fmq" type="search" placeholder="篩選代號／名稱" data-en-ph="Filter code / name" style="min-width:150px">'
                                          if mode != "score" else "") + f'<select class="btn fmind"><option value="">{T("全部產業", "All industries")}</option></select>'
                f'<button class="btn fmload" type="button">{T("載入全市場資料", "Load full-market data")}</button>'
                f'<span class="muted small fmst"></span></div><div class="fmbody"></div></div><p class="note">{note}</p>', "wide")


FM_LABEL = {"us": ("美股", "US"), "tw": ("台股", "Taiwan"), "hk": ("港股", "Hong Kong")}


# ----------------------------------------------------------------- themes (族群)
def _score_cell(v: Optional[float], n: Optional[int] = None) -> str:
    if v is None:
        return '<td class="r muted">—</td>'
    d = v - 50
    a = min(abs(d) / 30, 1.0) * 50
    col = "var(--up)" if d > 0 else "var(--dn)"
    nn = f'<span class="muted small"> ({n})</span>' if n else ""
    return f'<td class="r hm" style="background:color-mix(in srgb,{col} {a:.0f}%,transparent)">{v:.0f}{nn}</td>'


def sec_themes(eng) -> str:
    sc = getattr(eng, "scores", None) or {}
    if not sc.get("available") or not sc.get("themes"):
        return card("族群強弱", "Theme strength", f'<p class="muted">{T("資料暫時取不到", "Data unavailable")}</p>', "wide")
    mks = list(sc["markets"])
    head = "".join(f'<th class="r">{T(sc["markets"][k]["label"], sc["markets"][k]["label_en"])}</th>' for k in mks)
    rows = []
    for t in sc["themes"]:
        cells = "".join(_score_cell((t["per"].get(k) or {}).get("score"), (t["per"].get(k) or {}).get("n")) for k in mks)
        leaders = sorted([x for k in mks if t["per"].get(k) for x in t["per"][k]["leaders"]], key=lambda x: -x[2])[:4]
        lead = "、".join(f"{esc(n)}" for n, _, _ in leaders)
        r3 = [t["per"][k]["r3"] for k in mks if t["per"].get(k) and t["per"][k].get("r3") is not None]
        rows.append(f'<tr><td class="nw"><b>{T(t["theme"], t["theme_en"])}</b><span class="muted small"> {t["n"]} {T("檔", "")}</span></td>'
                    f'{_score_cell(t["score"])}{cells}<td class="r {cls(sum(r3) / len(r3) if r3 else None)}">'
                    f'{num(sum(r3) / len(r3) if r3 else None, 1, sign=True, pct=True)}</td><td class="small">{lead}</td></tr>')
    cross = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("族群", "Theme")}</th><th class="r">{T("綜合", "All")}</th>{head}'
             f'<th class="r">{T("3 個月平均報酬", "3M avg return")}</th><th>{T("族群內分數最高", "Leaders")}</th></tr></thead>'
             f'<tbody>{"".join(rows)}</tbody></table></div>')
    items = []
    for k, m in sc["markets"].items():
        trs = "".join(
            f'<tr><td class="nw">{T(t["theme"], t["theme_en"])}</td><td class="r">{t["n"]}</td><td>{_bar(t["score"], _score_color(t["score"] or 0))}</td>'
            f'<td class="r {cls(t.get("r1m"))}">{num(t.get("r1m"), 1, sign=True, pct=True)}</td><td class="r {cls(t.get("r3"))}">{num(t.get("r3"), 1, sign=True, pct=True)}</td>'
            f'<td class="r">{num(t.get("above200"), 0)}%</td>'
            f'<td class="small">{"、".join(esc(n) + " " + format(v, ".0f") for n, _, v in t["leaders"])}</td></tr>' for t in m["themes"])
        items.append((m["label"], m["label_en"],
                      f'<div class="scroll"><table class="mini"><thead><tr><th>{T("族群", "Theme")}</th><th class="r">{T("檔數", "n")}</th>'
                      f'<th>{T("平均綜合分數", "Avg score")}</th><th class="r">{T("1月", "1M")}</th><th class="r">{T("3月", "3M")}</th>'
                      f'<th class="r">{T("站上 200 日線", "Above 200d")}</th><th>{T("領頭個股", "Leaders")}</th></tr></thead><tbody>{trs}</tbody></table></div>'))
    note = T("族群分數＝族群內個股綜合分數的平均（括號內為檔數），50 為中性；檔數少的族群（例如港股國防只有 2 檔）參考價值較低。"
             "同一個族群在美、台、港三地一起看，可以看出資金是全球同步追捧，還是只集中在某一個市場。",
             "Theme score = average composite score of its members (count in brackets), 50 = neutral; small themes are less reliable.")
    return card("族群強弱（跨美股／台股／港股）", "Theme strength across US / Taiwan / Hong Kong",
                cross + f'<h3>{T("各市場族群明細", "By market")}</h3>' + _tabset("th", items) + f'<p class="note">{note}</p>', "wide")


# ----------------------------------------------------------------- gurus (13F) & insiders (Form 4)
def _hold_rows(xs: List[Dict], n: int = 6, show_chg: bool = False) -> str:
    if not xs:
        return f'<li class="muted">{T("無", "None")}</li>'
    out = []
    for x in xs[:n]:
        pc = f' <span class="pill">{T("買權", "Call") if x["pc"] == "Call" else T("賣權（看空）", "Put (bearish)")}</span>' if x.get("pc") else ""
        ch = f' <span class="{cls(x.get("chg"))}">{num(x.get("chg"), 0, sign=True, pct=True)}</span>' if show_chg and x.get("chg") is not None else ""
        out.append(f'<li>{esc(x["name"].title())}{pc} <span class="muted">{_usd(x["value"])}</span>{ch}</li>')
    return "".join(out)


def sec_gurus(eng) -> str:
    g = (getattr(eng, "gurus", None) and eng.gurus.result) or {}
    if not g.get("available"):
        return card("大師持倉（13F）", "Guru holdings (13F)", f'<p class="muted">{T("SEC 資料暫時取不到", "SEC data unavailable right now")}</p>', "wide")
    cards = []
    for m in g["managers"]:
        age = m["age_days"]
        stale = ('<span class="pill warn">' + T(f"已 {age} 天未申報（可能已停止申報）", f"No filing for {age} days") + "</span>"
                 if m["stale"] else "")
        top = "".join(
            f'<tr><td>{esc(h["name"].title())}</td>'
            f'<td class="r">{_usd(h["value"])}</td><td class="r">{num(h.get("w"), 1, pct=True)}</td></tr>'
            for h in [x for x in m["top"] if not x["pc"]][:8])
        ch = m["chg"]
        opts = (f'<h4>{T("選擇權部位（名目價值）", "Option positions (notional)")}</h4><ul class="lines">{_hold_rows(m["options"], 6)}</ul>'
                if m["options"] else "")
        cards.append(
            f'<div class="guru"><div class="gh"><b>{T(m["name"], m["name_en"])}</b><span class="pill">{esc(m["style"])}</span>{stale}</div>'
            f'<div class="muted small">{T("持倉期末", "Period")} {esc(m["period"])} · {T("申報", "Filed")} {esc(m["filed"])} · '
            f'{T("美股多頭部位", "US long book")} {_usd(m["total"])}（{m["n"]} {T("檔", "names")}）'
            f' · <a href="{esc(m["url"] or "#")}" target="_blank" rel="noopener noreferrer">SEC</a></div>'
            f'<table class="mini"><thead><tr><th>{T("前幾大持股", "Top holdings")}</th><th class="r">{T("市值", "Value")}</th>'
            f'<th class="r">{T("占比", "Weight")}</th></tr></thead><tbody>{top}</tbody></table>'
            f'<div class="g2 small"><div><h4 class="up">{T("新建倉", "New")}</h4><ul class="lines">{_hold_rows(ch["new"], 5)}</ul>'
            f'<h4 class="up">{T("加碼（股數 +10% 以上）", "Added (>+10% shares)")}</h4><ul class="lines">{_hold_rows(ch["add"], 5, True)}</ul></div>'
            f'<div><h4 class="dn">{T("出清", "Exited")}</h4><ul class="lines">{_hold_rows(ch["exit"], 5)}</ul>'
            f'<h4 class="dn">{T("減碼（股數 −10% 以上）", "Trimmed (>−10% shares)")}</h4><ul class="lines">{_hold_rows(ch["cut"], 5, True)}</ul></div></div>'
            f'{opts}</div>')
    note = T("資料：SEC EDGAR 13F-HR。13F 只揭露季末的美股多頭部位與選擇權（名目價值），最晚在季末後 45 天才申報，看不到空頭股票部位、海外資產與季中交易——"
             "它告訴你「上一季他們做了什麼」，不是現在的部位。賣權（Put）是看空的押注；名目價值不等於實際投入金額。",
             "Source: SEC EDGAR 13F-HR. Quarter-end US long positions and options (notional), filed up to 45 days late; short stock, "
             "non-US assets and intra-quarter trades are not visible. It shows what they did last quarter, not what they hold now.")
    return card("大師持倉（13F）：巴菲特、Burry 與其他知名機構", "Guru holdings (13F)", f'<div class="gurus">{"".join(cards)}</div><p class="note">{note}</p>', "wide")


def sec_insiders(eng) -> str:
    ins = getattr(eng, "insiders", None)
    if ins is None:
        return ""
    b = ins.board(15)
    if not b.get("available"):
        return card("內部人買賣（Form 4）", "Insider trades (Form 4)", f'<p class="muted">{T("SEC 資料暫時取不到", "SEC data unavailable right now")}</p>', "wide")
    names = {}
    sc = getattr(eng, "scores", None) or {}
    for m in (sc.get("markets") or {}).values():
        for r in m["rows"]:
            names[r["sym"]] = (r["name"], r["name_en"])

    def nm(sym):
        zh, en = names.get(sym, (sym, sym))
        return f'{T(zh, en)}<span class="tk">{esc(sym)}</span>'

    def who(r):
        x = r["big"][0] if r.get("big") else None
        if not x:
            return "—"
        return f'{esc(x["owner"].title())}<span class="muted small">（{esc(x["title"] or "—")}）</span>'

    sells = "".join(
        f'<tr><td class="nw">{nm(r["sym"])}</td><td class="r dn">{_usd(r["sell_disc_usd"])}</td><td class="r">{_usd(r["sell_plan_usd"])}</td>'
        f'<td class="r">{r["n_sellers"]}</td><td>{who(r)}</td></tr>' for r in b["sells"])
    buys = "".join(
        f'<tr><td class="nw">{nm(r["sym"])}</td><td class="r up">{_usd(r["buy_usd"])}</td><td class="r">{r["n_buyers"]}</td><td>{who(r)}</td></tr>'
        for r in b["buys"]) or f'<tr><td colspan="4" class="muted">{T("期間內沒有公開市場買進", "No open-market purchases in the window")}</td></tr>'
    npend = b.get("pending") or 0
    pend = ('<p class="note warn">' + T(f"還有 {npend} 份申報待下載，下次更新會補齊。", f"{npend} filings still queued.") + "</p>"
            if npend else "")
    note = T(f"資料：SEC Form 4（最近 {b['days']} 天，評分池內的美股）。只計公開市場買進（P）與賣出（S），不含行使選擇權、扣稅、贈與。"
             "「預先計畫」是依 10b5-1 規則事先排定的賣出，訊號意義較低；「非計畫性」賣出與高層主動買進較值得注意。",
             f"Source: SEC Form 4, last {b['days']} days, US names in the scoring universe. Open-market purchases (P) and sales (S) only. "
             "Pre-arranged 10b5-1 sales carry less signal than discretionary ones.")
    body = (f'<div class="g2"><div><h3>{T("內部人賣出（依非計畫性金額排序）", "Insider selling (by discretionary amount)")}</h3><div class="scroll"><table class="mini">'
            f'<thead><tr><th>{T("個股", "Stock")}</th><th class="r">{T("非計畫性", "Discretionary")}</th><th class="r">{T("預先計畫", "10b5-1")}</th>'
            f'<th class="r">{T("人數", "Sellers")}</th><th>{T("最大一筆", "Largest")}</th></tr></thead><tbody>{sells}</tbody></table></div></div>'
            f'<div><h3>{T("內部人公開市場買進", "Insider open-market buying")}</h3><div class="scroll"><table class="mini">'
            f'<thead><tr><th>{T("個股", "Stock")}</th><th class="r">{T("金額", "Amount")}</th><th class="r">{T("人數", "Buyers")}</th>'
            f'<th>{T("最大一筆", "Largest")}</th></tr></thead><tbody>{buys}</tbody></table></div></div></div>{pend}<p class="note">{note}</p>')
    return card("內部人買賣（Form 4）", "Insider trades (Form 4)", body, "wide")


# ----------------------------------------------------------------- US Treasury zone
def curve_svg(cid: str, curves: Dict[str, List[Dict]], w: int = 560, h: int = 230) -> str:
    sets = [(k, c) for k, c in (("y1", curves.get("y1")), ("m1", curves.get("m1")), ("now", curves.get("now"))) if c]
    if not sets:
        return ""
    pl, pr, pt, pb = 40, 16, 12, 26
    W, H = w - pl - pr, h - pt - pb
    xs_all = [math.log(c["years"] * 12) for _, cs in sets for c in cs]
    ys_all = [c["yield"] for _, cs in sets for c in cs]
    x0, x1 = min(xs_all), max(xs_all)
    lo, hi = min(ys_all), max(ys_all)
    pad = (hi - lo) * 0.12 or 0.2
    ticks = nice_ticks(lo - pad, hi + pad, 4)
    lo, hi = ticks[0], ticks[-1]
    X = lambda yrs: pl + (math.log(yrs * 12) - x0) / (x1 - x0 or 1) * W  # noqa: E731
    Y = lambda v: pt + (1 - (v - lo) / (hi - lo or 1)) * H  # noqa: E731
    parts = []
    for t in ticks:
        parts.append(f'<line x1="{pl}" x2="{pl + W}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" class="grid"/>'
                     f'<text x="{pl - 6}" y="{Y(t) + 4:.1f}" class="axis" text-anchor="end">{tick_label(t)}%</text>')
    for c in sets[-1][1]:
        lab = f'{c["years"]:g}Y' if c["years"] >= 1 else f'{round(c["years"] * 12)}M'
        parts.append(f'<text x="{X(c["years"]):.1f}" y="{h - 6}" class="axis" text-anchor="middle">{lab}</text>')
    style = {"now": ("var(--ac)", "", "最新", "Latest"), "m1": ("var(--tx2)", "4 3", "1 個月前", "1 month ago"),
             "y1": ("var(--mu)", "2 4", "1 年前", "1 year ago")}
    legend = []
    for k, cs in sets:
        col, dash, zh, en = style[k]
        pts = " ".join(f"{X(c['years']):.1f},{Y(c['yield']):.1f}" for c in cs)
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-dasharray="{dash}" stroke-linejoin="round"/>')
        for c in cs:
            parts.append(f'<circle cx="{X(c["years"]):.1f}" cy="{Y(c["yield"]):.1f}" r="{3.5 if k == "now" else 2.5}" fill="{col}"/>'
                         f'<circle cx="{X(c["years"]):.1f}" cy="{Y(c["yield"]):.1f}" r="9" class="thit" fill="transparent" '
                         f'data-tip="{c["yield"]:.2f}%|{esc(zh)} · {c["years"]:g}Y|{esc(c["date"])}"/>')
        legend.append(f'<span><i class="lk" style="background:{col};width:16px;height:2px;display:inline-block"></i>{T(zh, en)} '
                      f'<span class="muted">{esc(cs[-1]["date"])}</span></span>')
    return (f'<div class="legend">{"".join(legend)}</div>'
            f'<svg id="{cid}" class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="yield curve">{"".join(parts)}</svg>')


def sec_bonds(eng) -> str:
    b = getattr(eng, "bonds", None) or {}
    if not b.get("available"):
        return card("美債專區", "US Treasuries", f'<p class="muted">{T("殖利率與標售資料暫時取不到", "Treasury data unavailable right now")}</p>', "wide")
    now = {c["sid"]: c["yield"] for c in b["curves"].get("now", [])}
    sp, tp, mv = b.get("spreads", {}), b.get("term_premium"), b.get("move")
    kv = "".join(f'<div><span class="muted">{T(zh, en)}</span><b>{num(now.get(sid), 2)}%</b></div>'
                 for sid, zh, en in (("DGS3MO", "3 個月", "3M"), ("DGS2", "2 年", "2Y"), ("DGS10", "10 年", "10Y"), ("DGS30", "30 年", "30Y"))
                 if sid in now)
    for k, zh, en in (("10y2y", "10年−2年利差", "10Y−2Y"), ("10y3m", "10年−3月利差", "10Y−3M")):
        if k in sp:
            nd = sp[k]["inverted_days"]
            inv = (' <span class="small warn">' + T(f"倒掛 {nd} 天", f"inverted {nd}d") + "</span>" if nd else "")
            kv += f'<div><span class="muted">{T(zh, en)}</span><b class="{cls(sp[k]["bp"])}">{sp[k]["bp"]:+.0f}bp</b>{inv}</div>'
    if tp:
        kv += (f'<div><span class="muted">{T("10 年期限溢價", "10Y term premium")}</span><b>{tp["value"]:.2f}%</b>'
               f' <span class="small muted">{T("百分位", "pct")} {tp["pctile"]:.0f}</span></div>')
    if mv:
        kv += (f'<div><span class="muted">{T("MOVE 債市波動", "MOVE bond vol")}</span><b>{mv["value"]:.0f}</b>'
               f' <span class="small muted">{T("10 年百分位", "10y pct")} {mv["pctile"]:.0f}</span></div>')
    curve = curve_svg("c_curve", b["curves"])
    charts = []
    if "10y2y" in sp:
        charts.append(f'<div class="trend"><div class="th"><b>{T("10 年 − 2 年利差（bp，近 5 年）", "10Y − 2Y spread (bp, 5y)")}</b>'
                      f'<span class="muted small">{T("低於 0 = 倒掛", "below 0 = inverted")}</span></div>'
                      + line_chart("c_10y2y", _weekly(sp["10y2y"]["hist"]), "10Y-2Y bp", 0, bands=[(-1000, 0, "#d03b3b")]) + "</div>")
    if tp:
        charts.append(f'<div class="trend"><div class="th"><b>{T("10 年期限溢價（Kim-Wright，近 5 年）", "10Y term premium (Kim-Wright, 5y)")}</b></div>'
                      + line_chart("c_tp", _weekly(tp["hist"]), "Term premium %", 2) + "</div>")
    if mv:
        charts.append(f'<div class="trend"><div class="th"><b>{T("MOVE 美債波動率指數（近 5 年）", "MOVE bond volatility (5y)")}</b>'
                      f'<span class="muted small">{T("越高＝債市越不安", "higher = more bond-market stress")}</span></div>'
                      + line_chart("c_move", _weekly(mv["hist"]), "MOVE", 0) + "</div>")
    rows = "".join(
        f'<tr><td class="nw">{esc(a["date"])}</td><td class="nw">{esc(a["label"])}{_REOPEN if a["reopen"] else ""}</td>'
        f'<td class="r">{a["high_yield"]:.3f}%</td><td class="r">{a["btc"]:.2f}<span class="muted small"> / {num(a.get("btc_avg"), 2)}</span></td>'
        f'<td class="r">{a["indirect"]:.0f}%<span class="muted small"> / {num(a.get("indirect_avg"), 0)}%</span></td>'
        f'<td class="r">{a["dealer"]:.0f}%<span class="muted small"> / {num(a.get("dealer_avg"), 0)}%</span></td>'
        f'<td class="r">{a["size_bn"]:.0f}B</td>'
        f'<td>{_verdict(a.get("verdict"))}</td></tr>' for a in b.get("auctions", []))
    table = (f'<h3>{T("最近的公債標售", "Recent coupon auctions")}</h3><div class="scroll"><table class="mini"><thead><tr>'
             f'<th>{T("日期", "Date")}</th><th>{T("天期", "Term")}</th><th class="r">{T("得標殖利率", "High yield")}</th>'
             f'<th class="r">{T("投標倍數／同天期近 6 次均", "Bid-to-cover / avg")}</th><th class="r">{T("海外等間接標／均", "Indirect / avg")}</th>'
             f'<th class="r">{T("交易商承接／均", "Dealers / avg")}</th><th class="r">{T("金額", "Size")}</th><th>{T("需求", "Demand")}</th>'
             f'</tr></thead><tbody>{rows}</tbody></table></div>') if rows else ""
    note = T("殖利率：FRED 固定到期殖利率；期限溢價：Kim-Wright 模型（投資人為了持有長債多要求的報酬，升高代表市場擔心財政與通膨）；"
             "標售：TreasuryDirect 官方結果。需求判斷只和同天期最近 6 次標售比較：投標倍數明顯下降、或初級交易商被迫吃下更多（終端買家縮手）→ 偏弱。"
             "業界常看的「尾差」需要發行前交易（WI）報價，屬付費資料，本站不顯示。",
             "Yields: FRED constant maturity; term premium: Kim-Wright; auctions: TreasuryDirect. Demand is judged against the same tenor's "
             "last 6 auctions (lower bid-to-cover or dealers absorbing more = weaker). The auction 'tail' needs paid when-issued quotes and is not shown.")
    return card("美債專區：殖利率曲線、期限溢價與標售", "US Treasuries: curve, term premium, auctions",
                f'<div class="kv">{kv}</div><div class="g2"><div><h3>{T("殖利率曲線", "Yield curve")}</h3>{curve}</div>'
                f'<div>{"".join(charts[:1])}</div></div><div class="g2">{"".join(charts[1:3])}</div>{table}<p class="note">{note}</p>', "wide")


def _weekly(s: pd.Series, years: int = 5) -> pd.Series:
    """Last `years` of a daily series at weekly resolution (keeps the page light; daily detail adds nothing here)."""
    s = s.dropna()
    if not isinstance(s.index, pd.DatetimeIndex) or s.empty:
        return s
    s = s[s.index >= s.index[-1] - pd.DateOffset(years=years)]
    w = s.resample("W-FRI").last().dropna()
    if len(w):
        w.index = list(w.index[:-1]) + [s.index[-1]]          # the current week ends on the latest observation
        w.index = pd.DatetimeIndex(w.index)
    return w


_REOPEN = ' <span class="pill">' + T("增額", "reopen") + "</span>"


def _verdict(v: Optional[str]) -> str:
    if not v:
        return f'<span class="muted">{T("樣本不足", "n/a")}</span>'
    col = {"偏弱": "#d03b3b", "偏強": "#0ca30c", "正常": "#6b7280"}[v]
    return f'<span class="pill"><i class="sw" style="background:{col}"></i>{T(v, {"偏弱": "Weak", "偏強": "Strong", "正常": "Normal"}[v])}</span>'


# ----------------------------------------------------------------- sector rotation & breadth
QUAD_EN = {"領先": "Leading", "轉弱": "Weakening", "落後": "Lagging", "改善": "Improving"}
SECTOR_EN = {"XLK": "Tech", "XLC": "Comm.", "XLY": "Discretionary", "XLP": "Staples", "XLE": "Energy", "XLV": "Health", "XLF": "Financials",
             "XLI": "Industrials", "XLU": "Utilities", "XLB": "Materials", "XLRE": "Real estate"}


def rotation_svg(cid: str, rows: List[Dict], w: int = 560, h: int = 300) -> str:
    pts = [r for r in rows if r.get("x") is not None and r.get("y") is not None]
    if len(pts) < 3:
        return ""
    pl, pr, pt, pb = 40, 16, 14, 28
    W, H = w - pl - pr, h - pt - pb
    mx = max(max(abs(r["x"]) for r in pts), 1) * 1.3
    my = max(max(abs(r["y"]) for r in pts), 1) * 1.3
    X = lambda v: pl + (v + mx) / (2 * mx) * W  # noqa: E731
    Y = lambda v: pt + (1 - (v + my) / (2 * my)) * H  # noqa: E731
    parts = [f'<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{pt}" y2="{pt + H}" class="zero"/>',
             f'<line x1="{pl}" x2="{pl + W}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" class="zero"/>']
    for zh, ax, ay, anc in (("領先", pl + W - 4, pt + 12, "end"), ("轉弱", pl + W - 4, pt + H - 6, "end"),
                            ("落後", pl + 4, pt + H - 6, "start"), ("改善", pl + 4, pt + 12, "start")):
        parts.append(f'<text x="{ax}" y="{ay}" class="axis" text-anchor="{anc}" data-en="{QUAD_EN[zh]}">{zh}</text>')
    parts.append(f'<text x="{pl + W / 2:.0f}" y="{h - 6}" class="axis" text-anchor="middle" data-en="3-month return vs S&amp;P (pp) →">相對標普 3 個月報酬（百分點）→</text>')
    placed: List[tuple] = []                       # label boxes already drawn → nudge new labels so none overlap
    for r in sorted(pts, key=lambda r: -r["y"]):
        col = {"領先": "var(--up)", "轉弱": "var(--warn)", "落後": "var(--dn)", "改善": "var(--ac)"}[r["quad"]]
        x, y = X(r["x"]), Y(r["y"])
        lw = 12 * len(r["name"]) + 4
        right = x + 7 + lw < pl + W
        lx0 = x + 7 if right else x - 7 - lw
        ly = y + 4
        for _ in range(12):
            if not any(abs(ly - py) < 13 and lx0 < px1 and px0 < lx0 + lw for px0, px1, py in placed):
                break
            ly += 13
        placed.append((lx0, lx0 + lw, ly))
        lead = (f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{(lx0 if right else lx0 + lw):.1f}" y2="{ly - 4:.1f}" class="grid"/>'
                if abs(ly - (y + 4)) > 1 else "")
        parts.append(f'{lead}<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{col}"/>'
                     f'<text x="{lx0 if right else lx0 + lw:.1f}" y="{ly:.1f}" class="rlbl" text-anchor="{"start" if right else "end"}" '
                     f'data-en="{esc(SECTOR_EN.get(r["sym"], r["sym"]))}">{esc(r["name"])}</text>'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" class="thit" fill="transparent" '
                     f'data-tip="{esc(r["name"])} {esc(r["sym"])}|3M {r["x"]:+.1f}pp · {esc(r["quad"])}|{esc("動能 " + format(r["y"], "+.1f"))}"/>')
    return f'<svg id="{cid}" class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="sector rotation">{"".join(parts)}</svg>'


def sec_rotation(eng) -> str:
    b = getattr(eng, "rotation", None) or {}
    if not b.get("available"):
        return card("類股輪動與市場寬度", "Sector rotation & breadth", f'<p class="muted">{T("資料暫時取不到", "Data unavailable")}</p>', "wide")
    wins = b.get("windows", [])
    wen = {"1週": "1W", "1月": "1M", "3月": "3M", "6月": "6M"}
    head = "".join(f'<th class="r">{T(k, wen.get(k, k))}</th>' for k in wins)
    rows = "".join(
        f'<tr><td class="nw">{T(r["name"], SECTOR_EN.get(r["sym"], r["sym"]))}<span class="tk">{esc(r["sym"])}</span></td>'
        + "".join(_heat(r["rel"].get(k), 8 if k != "1週" else 3) for k in wins)
        + f'<td>{T(r["quad"] or "—", QUAD_EN.get(r["quad"] or "", "—"))}</td></tr>' for r in b.get("sectors", []))
    table = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("類股", "Sector")}</th>{head}<th>{T("輪動位置", "Phase")}</th></tr>'
             f'</thead><tbody>{rows}</tbody></table></div>')
    br = []
    for i, (mk, v) in enumerate(b.get("breadth", {}).items()):
        br.append(f'<div class="trend"><div class="th"><b>{T(v["label"] + "評分池站上 200 日線比例", v["label_en"] + " universe above 200-day")}</b>'
                  f'<span class="muted">{v["now"]:.0f}%</span></div>'
                  + line_chart(f"c_br{i}", v["series"], "% > 200d", 0, fixed=(0, 100), bands=[(0, 30, "#d03b3b"), (70, 100, "#0ca30c")]) + "</div>")
    ew = b.get("equal_weight")
    if ew:
        br.append(f'<div class="trend"><div class="th"><b>{T("等權重 ÷ 市值加權標普（起點=100）", "Equal-weight ÷ cap-weight S&P (start = 100)")}</b>'
                  f'<span class="muted">{T("3 個月", "3M")} {num(ew.get("chg_3m"), 1, sign=True, pct=True)}</span></div>'
                  + line_chart("c_ew", ew["series"], "RSP/SPY", 1) + "</div>")
    note = T("相對強弱 = 類股 ETF 報酬 − 標普 500 報酬（百分點），顏色深淺只是輔助，數字才是重點。輪動圖：橫軸是相對標普的 3 個月表現（站在哪），"
             "縱軸是最近 1 個月相對表現減去 3 個月的平均月速度（往哪走）。市場寬度用本站個股評分池計算（美股 52、台股 30、港股 30 檔大型股），"
             "不是全市場；比例跌破 30% 代表多數權值股已轉弱。等權重相對市值加權走低，代表漲勢集中在少數大型股。",
             "Relative strength = sector ETF return minus S&P 500 (pp). Rotation map: x = 3-month relative return, y = last month's "
             "relative return minus the 3-month average pace. Breadth uses this site's scoring universe (large caps), not the whole market.")
    return card("類股輪動與市場寬度", "Sector rotation & breadth",
                f'<div class="g2"><div><h3>{T("類股相對標普強弱（百分點）", "Sector vs S&P (pp)")}</h3>{table}</div>'
                f'<div><h3>{T("輪動圖", "Rotation map")}</h3>{rotation_svg("c_rot", b.get("sectors", []))}</div></div>'
                f'<div class="g2">{"".join(br)}</div><p class="note">{note}</p>', "wide")


# ----------------------------------------------------------------- time machine
def sec_timemachine(eng) -> str:
    note = T("每天美股收盤後（台北時間早上）自動存一份當天的重點數據快照：壓力指數、風險階段、Gamma、暗池、估值分級、各市場評分前段班與 AI 評論。"
             "選一個日期就能看當時的樣子，並對照之後標普 500 的實際走勢，檢驗當時的警示準不準。快照從本功能上線那天開始累積。",
             "A snapshot of the key readings is saved once a day after the US close. Pick a date to see what the page said then and how "
             "the S&P 500 moved afterwards. Snapshots accumulate from the day this feature went live.")
    return card("時光機：回看任何一天", "Time machine",
                f'<div class="tm"><label class="small muted" for="tmSel">{T("選擇日期", "Pick a date")}</label> '
                f'<select id="tmSel" class="btn"><option value="">…</option></select> '
                f'<button class="btn" id="tmPrev" type="button">◀</button><button class="btn" id="tmNext" type="button">▶</button>'
                f'<div id="tmOut" class="tmout"><p class="muted">{T("載入快照清單中…", "Loading snapshots…")}</p></div>'
                f'<div id="tmList"></div></div><p class="note">{note}</p>', "wide")


FM_JS = r"""
(function(){var CACHE={},en=function(){return document.documentElement.lang==='en';};
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
function f(v,d){return (v==null||isNaN(v))?'—':Number(v).toFixed(d);}
function sg(v,d){return (v==null||isNaN(v))?'—':((v>0?'+':'')+Number(v).toFixed(d)+'%');}
function load(mk){if(CACHE[mk])return CACHE[mk];CACHE[mk]=fetch('market/'+mk+'.json',{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();})
 .then(function(d){var c=d.cols;d.items=d.rows.map(function(a){var o={};c.forEach(function(k,i){o[k]=a[i];});o.mk=mk;o.N=d.n;return o;});return d;})
 .catch(function(){CACHE[mk]=null;return null;});return CACHE[mk];}
var TO={A:0,B:1,C:2,D:3};function tb(t){var k=t==='A'?'B':t,L={B:['在區內','In zone'],C:['等拉回','Wait'],D:['快成立','Almost'],R:['參考區內','In ref. zone']}[k]||[t,t];var x=el('span','sgb s'+k,en()?L[1]:L[0]);x.style.marginRight='5px';return x;}
function ord(o){if(o.st==='signal')return o.inz?0:2;if(o.inz)return 1;if(o.tier==='D')return 3;if(o.st==='nodata')return 5;return 4;}
function tag(o){return o.tier||(o.st!=='signal'&&o.inz?'R':null);}
function pass(o,tv){if(tv==='ALL')return true;if(tv==='IN')return !!o.inz;if(tv==='EX')return !!o.ex;return !!o.tier&&tv.indexOf(o.tier)>=0;}
function card(o,lbl){var d=el('div','fmcard'),h=el('div','fmh');if(tag(o))h.appendChild(tb(tag(o)));if(o.pk)h.appendChild(el('span','pill pickp','★ '+(en()?'Top setup':'規則精選')+' '));h.appendChild(el('b',null,o.name+' '));h.appendChild(el('span','tk',o.code));
 h.appendChild(el('span','thc',lbl+(o.board?' '+o.board:'')+' · '+(o.ind||'')));d.appendChild(h);
 d.appendChild(el('div','small',(en()?'Tech score ':'技術分數 ')+f(o.tech,0)+(en()?' — rank ':'（全市場第 ')+o.rank+' / '+o.N+(en()?'':' 名）')
  +'　1M '+sg(o.r1m,1)+'　6M '+sg(o.r6,0)+'　RSI '+f(o.rsi,0)+'　'+(en()?'Price ':'現價 ')+f(o.px,2)));
 var st=el('div','small');st.appendChild(el('b','act',(o.stl||'—')+(o.patl?'：'+o.patl:'')+' '));d.appendChild(st);
 if(o.st==='signal'){d.appendChild(el('div','small','▶ '+(en()?'Entry zone ':'何時買（規則參考）：進場參考區 ')+f(o.zlo,2)+'–'+f(o.zhi,2)+(o.inz?(en()?' (in zone)':'（現價在區內）'):(en()?' (outside)':'（現價在區外）'))));
  d.appendChild(el('div','small','▶ '+(en()?'Give up below ':'何時放棄：收盤跌破 ')+f(o.inv,2)+'（-'+f(o.risk,1)+'%）'+(o.tgt?('　▶ '+(en()?'Overhead ':'上方壓力 52 週高 ')+f(o.tgt,2)+'（+'+f(o.tgtp,0)+'%）'):'')));}
 if(o.tg)d.appendChild(el('div','small','◆ '+(en()?'Patterns: ':'技術型態：')+o.tg));if(o.ex)d.appendChild(el('div','small dn','⚠ '+(en()?'Overheating: ':'過熱警示：')+o.ex));
 if(o.st==='signal'){}else{if(o.zlo!=null){d.appendChild(el('div','small','▶ '+(en()?'Add-on reference zone (no signal yet): ':'加碼參考區（尚無訊號，非買點）：')+(o.zb?o.zb+' ':'')+f(o.zlo,2)+'–'+f(o.zhi,2)+(o.inz?(en()?' (in zone)':'（現價在區內）'):'')));
  d.appendChild(el('div','small','▶ '+(en()?'Reference give-up below ':'參考失效線：收盤跌破 ')+f(o.inv,2)+(en()?' (-':'（距參考區中點 -')+f(o.risk,1)+'%）'));}
  if(o.when)d.appendChild(el('div','small','▶ '+(en()?'Would trigger: ':'何時才算買點：')+o.when));if(o.why)d.appendChild(el('div','small muted',o.why));}
 return d;}
var T0=0;window.FMsearch=function(v,box){if(!box)return;clearTimeout(T0);box.textContent='';if(!v||v.length<1)return;
 T0=setTimeout(function(){box.textContent=en()?'Searching the full market…':'搜尋全市場中…';
  Promise.all(['us','tw','hk'].map(load)).then(function(ds){box.textContent='';var q=v.toLowerCase(),hits=[];
   ds.forEach(function(d,i){if(!d)return;d.items.forEach(function(o){var c=(o.code||'').toLowerCase(),nm=(o.name||'').toLowerCase(),sc=-1;
    if(c===q||(o.sym||'').toLowerCase()===q)sc=3;else if(c.indexOf(q)===0||nm.indexOf(q)===0)sc=2;else if(q.length>=2&&nm.indexOf(q)>=0)sc=1;
    if(sc>=0)hits.push([sc,o,d.label]);});});
   if(!hits.length){if(ds.every(function(d){return !d;}))box.appendChild(el('p','muted small',en()?'Full-market data not available yet.':'全市場資料尚未建立。'));
    else box.appendChild(el('p','muted small',en()?'No match in the full market — try Discord /stock.':'全市場也找不到，可用 Discord 的 /stock 查詢。'));return;}
   hits.sort(function(a,b){return b[0]-a[0]||(b[1].tech||0)-(a[1].tech||0);});
   box.appendChild(el('div','small muted',(en()?'Full market: ':'全市場結果：')+hits.length+(en()?' match(es)':' 筆')+(hits.length>8?(en()?' (top 8)':'（顯示前 8 筆）'):'')));
   hits.slice(0,8).forEach(function(h){box.appendChild(card(h[1],h[2]));});});},250);};
document.querySelectorAll('.fm').forEach(function(w){var mode=w.dataset.mode,mk='us',shown=100,data=null,sel=w.querySelector('.fmind'),body=w.querySelector('.fmbody'),
 stl=w.querySelector('.fmst'),btn=w.querySelector('.fmload'),tsel=w.querySelector('.fmtier'),fq=w.querySelector('.fmq'),qt=0;
 if(tsel)tsel.addEventListener('change',function(){shown=100;render();});
 if(fq){if(en()&&fq.dataset.enPh)fq.placeholder=fq.dataset.enPh;fq.addEventListener('input',function(){clearTimeout(qt);qt=setTimeout(function(){shown=100;render();},200);});}
 function render(){body.textContent='';if(!data){return;}var ind=sel.value,tv=tsel?tsel.value:'ALL',q=fq?fq.value.trim().toLowerCase():'',its=data.items.filter(function(o){return (!ind||o.ind===ind)&&(mode==='score'||pass(o,tv))
   &&(!q||(o.code||'').toLowerCase().indexOf(q)>=0||(o.name||'').toLowerCase().indexOf(q)>=0);});
  if(mode!=='score')its.sort(function(a,b){return ord(a)-ord(b)||(b.str||0)-(a.str||0);});
  stl.textContent=(en()?' ':' ')+its.length+(en()?' names':' 檔')+' · '+(en()?'as of ':'資料日 ')+data.asof;
  var det=el('div','fmres');body.appendChild(det);det.appendChild(el('p','muted small',en()?'Click a row for the entry / give-up levels.':'點表格任一列，這裡會顯示該檔的「何時買／何時放棄」。'));
  var sc=el('div','scroll'),t=el('table','mini'),th=el('tr');
  (mode==='score'?['#',en()?'Stock':'個股',en()?'Industry':'產業',en()?'Tech':'技術分',en()?'1M':'1月',en()?'6M':'6月','RSI',en()?'Status':'狀態']
   :['#',en()?'Stock':'個股',en()?'Industry':'產業',en()?'Pattern / status':'型態／狀態',en()?'Strength':'強度',en()?'Price':'現價',en()?'Entry / add-on zone':'進場／加碼參考區',en()?'Give-up':'失效線'])
   .forEach(function(x){th.appendChild(el('th',null,x));});var hd=el('thead');hd.appendChild(th);t.appendChild(hd);var tbd=el('tbody');
  its.slice(0,shown).forEach(function(o,i){var tr=el('tr');if(o.pk&&mode!=='score')tr.className='pickrow';var nm=el('td','nw');if(tag(o)&&mode!=='score')nm.appendChild(tb(tag(o)));nm.appendChild(el('b',null,o.name+' '));nm.appendChild(el('span','tk',o.code));
   var cells=mode==='score'?[String(o.rank),nm,o.ind||'',f(o.tech,0),sg(o.r1m,1),sg(o.r6,0),f(o.rsi,0),o.stl||'']
    :[String(i+1),nm,o.ind||'',o.patl||o.stl||'',f(o.str,0),f(o.px,2),o.zlo==null?'—':(f(o.zlo,2)+'–'+f(o.zhi,2)+(o.inz?(en()?' ✓':' 區內'):'')+(o.st!=='signal'?(en()?' (ref)':'（參考）'):'')),o.inv==null?'—':(f(o.inv,2)+'（-'+f(o.risk,1)+'%）')];
   cells.forEach(function(c){if(typeof c==='string'){tr.appendChild(el('td',null,c));}else tr.appendChild(c);});
   tr.style.cursor='pointer';tr.title=en()?'Click for details':'點一下看何時買／何時放棄';
   tr.addEventListener('click',function(){det.textContent='';det.appendChild(card(o,data.label));det.scrollIntoView({block:'nearest'});});tbd.appendChild(tr);});
  t.appendChild(tbd);sc.appendChild(t);body.appendChild(sc);
  if(its.length>shown){var more=el('button','btn',en()?'Show 100 more':'再顯示 100 檔');more.type='button';more.addEventListener('click',function(){shown+=100;render();});body.appendChild(more);
   var all=el('button','btn',(en()?'Show all ':'全部顯示（')+its.length+(en()?'':' 檔）'));all.type='button';all.style.marginLeft='6px';all.addEventListener('click',function(){shown=its.length;render();});body.appendChild(all);}}
 function counts(){if(!tsel||!data)return;var c={};[].forEach.call(tsel.options,function(op){var v=op.value;c[v]=data.items.filter(function(o){return pass(o,v);}).length;
  if(!op.dataset.base)op.dataset.base=op.textContent;if(!op.dataset.baseEn)op.dataset.baseEn=op.dataset.en||op.textContent;
  op.textContent=(en()?op.dataset.baseEn:op.dataset.base)+'（'+c[v]+'）';});}
 function go(){btn.style.display='none';stl.textContent=en()?'Loading…':'載入中…';load(mk).then(function(d){data=d;shown=100;
  if(!d){stl.textContent=en()?'Full-market data not available yet.':'全市場資料尚未建立。';return;}
  var inds={};d.items.forEach(function(o){if(o.ind)inds[o.ind]=(inds[o.ind]||0)+1;});sel.length=1;
  Object.keys(inds).sort(function(a,b){return inds[b]-inds[a];}).forEach(function(k){var op=el('option',null,k+' ('+inds[k]+')');op.value=k;sel.appendChild(op);});
  counts();render();});}
 if(mode!=='score'&&'IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&btn.style.display!=='none'){io.disconnect();go();}});});io.observe(w);}
 btn.addEventListener('click',go);sel.addEventListener('change',function(){shown=100;render();});
 w.querySelectorAll('[data-fmk]').forEach(function(b){b.addEventListener('click',function(){w.querySelectorAll('[data-fmk]').forEach(function(x){x.classList.remove('on');});
  b.classList.add('on');mk=b.dataset.fmk;sel.value='';if(btn.style.display==='none')go();});});});
})();
"""

TM_JS = r"""
(function(){var en=function(){return document.documentElement.lang==='en';};
function apply(t){if(!t)return;var bar=t.closest('.panel')||document,p=bar.querySelector('.sgp.on[data-for="'+t.id+'"]'),v=p?p.dataset.v:'all',
 tb=bar.querySelector('.sgtb.on[data-for="'+t.id+'"]'),th=tb?tb.dataset.th:'',q=((document.getElementById('sigQ')||{}).value||'').trim().toLowerCase();
 t.querySelectorAll('tr.sm').forEach(function(tr){var ok=(q?(tr.dataset.q||'').indexOf(q)>=0:(v==='all'||tr.dataset.tier===v))&&(!th||tr.dataset.th===th);
  tr.style.display=ok?'':'none';var d=tr.nextElementSibling;if(d&&d.classList.contains('sd'))d.style.display=(ok&&tr.classList.contains('open'))?'':'none';});
 t.querySelectorAll('tr.gh').forEach(function(h){var n=0,x=h.nextElementSibling;while(x&&!x.classList.contains('gh')){if(x.classList.contains('sm')&&x.style.display!=='none')n++;x=x.nextElementSibling;}
  h.style.display=n?'':'none';var c=h.querySelector('.ghn');if(c)c.textContent=n;});
 var vis=0;t.querySelectorAll('tr.sm').forEach(function(tr){if(tr.style.display!=='none')vis++;});
 var em=t.querySelector('tfoot.sgempty');if(!em){em=document.createElement('tfoot');em.className='sgempty';em.innerHTML='<tr><td colspan="8" class="muted small"></td></tr>';t.appendChild(em);}
 em.style.display=vis?'none':'';em.querySelector('td').textContent=q?(en()?'Not in the curated list - see the full-market result above (entry / add-on zone, give-up line).':'這檔不在精選池，請看上方「全市場結果」卡片（有加碼參考區與失效線）；精選池以外的股票也都列在本頁最下方的全市場表格。')
  :(en()?'No stock matches this filter.':'這個篩選條件下沒有股票。');}
function group(t,on){var tb=t.tBodies[0];if(!t._orig){t._orig=Array.prototype.slice.call(tb.children).filter(function(r){return !r.classList.contains('gh');});}
 tb.querySelectorAll('tr.gh').forEach(function(h){h.remove();});
 if(!on){t._orig.forEach(function(r){tb.appendChild(r);});return;}
 var order=[],g={};t._orig.forEach(function(r){if(!r.classList.contains('sm'))return;var k=r.dataset.th||'';if(!g[k]){g[k]=[];order.push(k);}g[k].push(r);});
 var ths=Array.prototype.map.call((t.closest('.panel')||document).querySelectorAll('.sgtb[data-for="'+t.id+'"]'),function(b){return b.dataset.th;}).filter(Boolean);
 order.sort(function(a,b){return ths.indexOf(a)-ths.indexOf(b);});
 order.forEach(function(k){var h=document.createElement('tr');h.className='gh';var td=document.createElement('td');td.colSpan=8;
  td.innerHTML='<b></b> <span class="muted small ghn"></span>';td.firstChild.textContent=k;h.appendChild(td);tb.appendChild(h);
  g[k].forEach(function(r){var d=r.nextElementSibling&&r.nextElementSibling.classList.contains('sd')?r.nextElementSibling:null;tb.appendChild(r);if(d)tb.appendChild(d);});});}
document.querySelectorAll('table.sgt').forEach(function(t){t.querySelectorAll('tr.sm').forEach(function(tr){tr.addEventListener('click',function(){tr.classList.toggle('open');
  var d=tr.nextElementSibling;if(d&&d.classList.contains('sd'))d.style.display=tr.classList.contains('open')?'':'none';});});
 var gc=(t.closest('.panel')||document).querySelector('input.sgg[data-for="'+t.id+'"]');if(gc&&gc.checked)group(t,true);apply(t);});
document.querySelectorAll('.sgtb').forEach(function(b){b.addEventListener('click',function(){var id=b.dataset.for;
 document.querySelectorAll('.sgtb[data-for="'+id+'"]').forEach(function(x){x.classList.remove('on');});b.classList.add('on');
 if(b.dataset.th){document.querySelectorAll('.sgp[data-for="'+id+'"]').forEach(function(x){x.classList.toggle('on',x.dataset.v==='all');});}
 apply(document.getElementById(id));});});
document.querySelectorAll('input.sgg').forEach(function(c){c.addEventListener('change',function(){var t=document.getElementById(c.dataset.for);
 if(c.checked){document.querySelectorAll('.sgp[data-for="'+t.id+'"]').forEach(function(x){x.classList.toggle('on',x.dataset.v==='all');});}
 group(t,c.checked);apply(t);});});
document.querySelectorAll('.sgp').forEach(function(b){b.addEventListener('click',function(){document.querySelectorAll('.sgp[data-for="'+b.dataset.for+'"]').forEach(function(x){x.classList.remove('on');});
 b.classList.add('on');apply(document.getElementById(b.dataset.for));});});
document.querySelectorAll('select.thf').forEach(function(s){if((s.dataset.for||'').indexOf('sgt_')===0)s.addEventListener('change',function(){apply(document.getElementById(s.dataset.for));});});
var q=document.getElementById('sigQ');if(q){var n=document.getElementById('sigQn');q.addEventListener('input',function(){var v=q.value.trim().toLowerCase(),cnt=0,first=null;
 document.querySelectorAll('table.sgt').forEach(function(t){apply(t);var h=0;if(v)t.querySelectorAll('tr.sm').forEach(function(tr){if(tr.style.display!=='none')h++;});if(h&&!first)first=t;cnt+=h;});
 if(n)n.textContent=v?(cnt?(' '+cnt+(en()?' match(es) in the curated list':' 筆在精選池')):(en()?' not in the curated list':' 不在精選池')):'';
 if(window.FMsearch)window.FMsearch(v,document.getElementById('sigQfm'));
 if(first){var pid=first.closest('.panel').id,b=document.querySelector('.tab[data-t="'+pid+'"]');if(b&&!b.classList.contains('on'))b.click();}});}
})();
[['stockQ','stockQn','st_']].forEach(function(cf){var q=document.getElementById(cf[0]);if(!q)return;var n=document.getElementById(cf[1]);
 q.addEventListener('input',function(){var v=q.value.trim().toLowerCase(),first=null,cnt=0;
  document.querySelectorAll('table.score[id^="'+cf[2]+'"]').forEach(function(t){var hit=0;t.querySelectorAll('tbody tr').forEach(function(tr){
   var main=tr.classList.contains('why')?tr.previousElementSibling:tr;var ok=!v||((main.dataset.q||'').indexOf(v)>=0);tr.style.display=ok?'':'none';
   if(ok&&!tr.classList.contains('why')&&v){hit++;}});if(hit&&!first)first=t;cnt+=hit;});
  n.textContent=v?(cnt?(' '+cnt+(document.documentElement.lang==='en'?' match(es) in the curated list':' 筆在精選池')):(document.documentElement.lang==='en'?' not in the curated list':' 不在精選池')):'';
  if(window.FMsearch)window.FMsearch(v,document.getElementById(cf[0]+'fm'));
  if(first){var pid=first.closest('.panel').id,b=document.querySelector('.tab[data-t="'+pid+'"]');if(b&&!b.classList.contains('on'))b.click();}});});
function tfilter(id){if(id.indexOf('sgt_')===0)return;var t=document.getElementById(id);if(!t)return;var sel=document.querySelector('select.thf[data-for="'+id+'"]'),
 cb=document.querySelector('.onlysig input[data-for="'+id+'"]'),ts=document.querySelector('select.tierf[data-for="'+id+'"]'),
 v=sel?sel.value:'',only=cb&&cb.checked,tv=ts?ts.value:'';
 t.querySelectorAll('tbody tr').forEach(function(tr){var tg=tr.dataset.tier||'';
  tr.style.display=((!v||tr.dataset.th===v)&&!(only&&tr.classList.contains('nosig'))&&(!tv||(tg&&tv.indexOf(tg)>=0)))?'':'none';});}
document.querySelectorAll('select.tierf').forEach(function(sel){sel.addEventListener('change',function(){tfilter(sel.dataset.for);});});
document.querySelectorAll('select.thf').forEach(function(sel){sel.addEventListener('change',function(){tfilter(sel.dataset.for);});});
document.querySelectorAll('.onlysig input').forEach(function(cb){cb.addEventListener('change',function(){tfilter(cb.dataset.for);});});
(function(){var sel=document.getElementById('tmSel');if(!sel)return;var out=document.getElementById('tmOut'),list=document.getElementById('tmList');
var en=function(){return document.documentElement.lang==='en';};var IDX=null;
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
function f(v,d){return (v==null||isNaN(v))?'—':Number(v).toFixed(d);}
function kv(box,k,v){var d=el('div');d.appendChild(el('span','muted',k));d.appendChild(el('b',null,v));box.appendChild(d);}
function render(s,meta){out.textContent='';var h=el('h3',null,(en()?'Snapshot ':'快照 ')+s.date+(s.asof?(en()?' · market data ':' · 行情資料日 ')+s.asof:''));out.appendChild(h);
 var box=el('div','kv');
 if(s.ssi)kv(box,en()?'Stress index':'壓力指數 SSI',f(s.ssi.score,1)+' '+(s.ssi.label||''));
 if(s.stage)kv(box,en()?'Risk stage':'風險階段',(s.stage.name||'—')+' ('+(s.stage.points==null?'—':s.stage.points)+')');
 if(s.gamma)kv(box,'GEX',f(s.gamma.gex,2)+(en()?' · flip ':' · 翻轉點 ')+f(s.gamma.flip,0));
 if(s.darkpool)kv(box,en()?'Dark-pool index':'暗池指數',f(s.darkpool.dpi,1)+'% '+(s.darkpool.state||''));
 if(s.spx)kv(box,'S&P 500',f(s.spx,0));
 if(meta&&meta.after!=null)kv(box,en()?'S&P since then':'之後標普變化',(meta.after>0?'+':'')+f(meta.after,1)+'%');
 out.appendChild(box);
 if(s.valuation&&s.valuation.length){out.appendChild(el('h4',null,en()?'Valuation & credit gauges':'估值與信用分級'));var ul=el('ul','lines');
  s.valuation.forEach(function(v){ul.appendChild(el('li',null,v.label+'：'+f(v.value,2)+'（'+(en()?'pct ':'百分位 ')+f(v.pctile,0)+'，'+v.grade+'）'));});out.appendChild(ul);}
 if(s.scores){out.appendChild(el('h4',null,en()?'Top of the scoring board':'評分前段班'));var g=el('div','g3');
  Object.keys(s.scores).forEach(function(k){var m=s.scores[k],d=el('div');d.appendChild(el('b',null,m.label));var ol=el('ol','lines');
   m.top.forEach(function(r){ol.appendChild(el('li',null,r[1]+' ('+r[0]+') '+f(r[2],0)));});d.appendChild(ol);g.appendChild(d);});out.appendChild(g);}
 if(s.signals){out.appendChild(el('h4',null,en()?'Technical signals that day → since':'當天的技術面訊號 → 之後表現'));var g2=el('div','g3');
  Object.keys(s.signals).forEach(function(k){var m=s.signals[k],d=el('div');d.appendChild(el('b',null,m.label));var ol=el('ol','lines');
   m.rows.forEach(function(r){var li=el('li',null,r.name+' ('+r.code+') '+r.pattern+' ');var sp=el('span',r.since_pct>0?'up':r.since_pct<0?'dn':'',
    r.since_pct==null?'—':((r.since_pct>0?'+':'')+f(r.since_pct,1)+'%'));li.appendChild(sp);if(r.failed)li.appendChild(el('span','muted small',en()?' (invalidated)':'（曾跌破失效線）'));ol.appendChild(li);});
   d.appendChild(ol);g2.appendChild(d);});out.appendChild(g2);}
 if(s.ai){out.appendChild(el('h4',null,en()?'AI commentary that day':'當天的 AI 評論'));var p=el('div','ai small');p.style.whiteSpace='pre-wrap';p.textContent=s.ai;out.appendChild(p);}
}
function load(d){if(!d)return;out.textContent=en()?'Loading…':'載入中…';
 fetch('snap/'+d+'.json',{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(s){
  var m=(IDX||[]).filter(function(x){return x.date===d;})[0];render(s,m);}).catch(function(){out.textContent=en()?'Snapshot unavailable.':'這一天的快照讀不到。';});}
fetch('snap/index.json',{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(ix){IDX=ix;sel.textContent='';
 if(!ix.length){out.textContent=en()?'No snapshots yet — the first one is saved after the next US close.':'還沒有快照——下一次美股收盤後會存第一份。';return;}
 ix.slice().reverse().forEach(function(x){var o=el('option',null,x.date+'  SSI '+f(x.ssi,0)+(x.after!=null?('  →  S&P '+(x.after>0?'+':'')+f(x.after,1)+'%'):''));o.value=x.date;sel.appendChild(o);});
 var t=el('table','mini'),th=el('tr');[en()?'Date':'日期','SSI',en()?'Stage':'階段',en()?'S&P since':'之後標普'].forEach(function(h){th.appendChild(el('th',null,h));});
 var thead=el('thead');thead.appendChild(th);t.appendChild(thead);var tb=el('tbody');
 ix.slice(-30).reverse().forEach(function(x){var tr=el('tr');[x.date,f(x.ssi,1),x.stage||'—',x.after==null?'—':((x.after>0?'+':'')+f(x.after,1)+'%')].forEach(function(v,i){
  var td=el('td',i===3?('r '+(x.after>0?'up':x.after<0?'dn':'')):(i===1?'r':null),v);tr.appendChild(td);});tr.style.cursor='pointer';
  tr.addEventListener('click',function(){sel.value=x.date;load(x.date);});tb.appendChild(tr);});t.appendChild(tb);
 list.textContent='';list.appendChild(el('h4',null,en()?'Last 30 snapshots':'最近 30 份快照'));var sc=el('div','scroll');sc.appendChild(t);list.appendChild(sc);
 sel.value=ix[ix.length-1].date;load(sel.value);}).catch(function(){out.textContent=en()?'No snapshots yet.':'還沒有快照。';});
sel.addEventListener('change',function(){load(sel.value);});
function step(k){var i=sel.selectedIndex+k;if(i>=0&&i<sel.options.length){sel.selectedIndex=i;load(sel.value);}}
document.getElementById('tmPrev').addEventListener('click',function(){step(1);});document.getElementById('tmNext').addEventListener('click',function(){step(-1);});
})();
"""

SECTION_CSS = """
.sbar{position:relative;height:18px;min-width:110px;background:var(--card2);border-radius:4px;overflow:hidden}
.sbar i{position:absolute;left:0;top:0;bottom:0;border-radius:0 4px 4px 0;opacity:.85}.sbar b{position:relative;padding-left:6px;font-size:12px;line-height:18px}
table.score td{padding:5px 6px;font-size:12.5px}table.score{min-width:720px}table.score tr:not(.why) td{border-bottom:0;padding-top:8px}
table.score tr.why td{padding:0 6px 8px}.rc{white-space:nowrap;display:inline-block;margin:1px 3px 1px 0;padding:0 7px;border-radius:99px;
 border:1px solid var(--bd);font-size:11.5px;color:var(--tx2);background:var(--card2)}.rc.rcp{border-color:color-mix(in srgb,var(--up) 45%,transparent)}
.rc.rcn{border-color:color-mix(in srgb,var(--dn) 45%,transparent)}.rc.rcp::before{content:"▲ ";color:var(--up)}.rc.rcn::before{content:"▼ ";color:var(--dn)}
.gurus{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.guru{background:var(--card2);border:1px solid var(--bd);border-radius:10px;padding:12px}
.guru ul.lines{font-size:12.5px}.gh{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:2px}.pill.warn{color:var(--warn)}
table.mini td,table.mini th{padding:4px 6px;font-size:12.5px}.hm{font-variant-numeric:tabular-nums}
.tm select{min-width:240px}.tmout{margin-top:10px}#tmList table tr:hover td{background:var(--card2)}
.install{display:none}.install.show{display:inline-block}
.thc{display:inline-block;margin-left:6px;padding:0 6px;border-radius:4px;background:var(--card2);border:1px solid var(--bd);font-size:11px;color:var(--mu);font-weight:400}
.thf{margin:6px 0 4px;min-width:150px}.fmres{margin-top:6px}.fmcard{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:8px 11px;margin:6px 0}
.fmcard .fmh{margin-bottom:3px}.fmcard div{margin:2px 0}.fmctl{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:6px 0}.act{color:var(--tx);font-weight:600;margin-right:2px}td .act{margin-left:2px}
.pill.inz{color:var(--up);border-color:var(--up)}
.sgbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:6px 0 8px}.sgps{display:flex;gap:6px;flex-wrap:wrap}
.sgp{background:var(--card2);border:1px solid var(--bd);color:var(--tx2);border-radius:99px;padding:3px 12px;font-size:13px;cursor:pointer}
.sgp b{color:var(--tx);margin-left:3px}
.sgth{display:flex;gap:5px;align-items:center;flex-wrap:wrap;margin:0 0 8px}.sgtb{background:none;border:1px solid var(--bd);color:var(--tx2);border-radius:6px;padding:2px 9px;font-size:12.5px;cursor:pointer}
.sgtb b{color:var(--mu);font-weight:500;margin-left:2px}.sgtb.on{border-color:var(--ac);color:var(--tx);background:color-mix(in srgb,var(--ac) 18%,transparent)}.sggl{margin-left:8px}
table.sgt tr.gh td{background:none;border-bottom:1px solid var(--ac);padding-top:12px;font-size:13.5px}.sgp.on{background:var(--ac);border-color:var(--ac);color:#fff}.sgp.on b{color:#fff}
table.sgt tr.sm{cursor:pointer}table.sgt tr.sm:hover td{background:var(--card2)}table.sgt tr.sd td{background:var(--card2);padding:6px 10px 10px}
table.sgt tr.sm.open td:last-child{color:var(--ac)}.sgb{display:inline-block;border-radius:5px;padding:0 7px;font-size:12px;font-weight:600;white-space:nowrap}
.sgb.sB{background:color-mix(in srgb,var(--up) 22%,transparent)}.sgb.sC{background:color-mix(in srgb,#3987e5 25%,transparent)}.sgb.sD{background:var(--card2);border:1px solid var(--bd)}.sgb.sR{background:color-mix(in srgb,var(--up) 10%,transparent);border:1px dashed var(--up)}
span.refz{border-bottom:1px dashed var(--muted,#888)}i.zd{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--bd);margin-left:5px;vertical-align:middle}i.zd.in{background:var(--up)}
details.sgx{margin:6px 0 8px}details.sgx summary{cursor:pointer;color:var(--ac);font-size:13px}details.sgx ol{margin:6px 0;padding-left:20px}details.sgx li{margin:3px 0}
@media(max-width:760px){table.sgt tr.sm td:nth-child(1),table.sgt th:nth-child(1),table.sgt tr.sm td:nth-child(3),table.sgt th:nth-child(3),table.sgt tr.sm td:nth-child(8),table.sgt tr.sd td:nth-child(1){display:none}}
.tier{display:inline-block;min-width:17px;text-align:center;border-radius:4px;font-size:11px;font-weight:700;padding:0 4px;margin-right:5px;color:#111}
.tier.tA{background:#c9a227}.tier.tB{background:#2fbf71}.tier.tC{background:#3987e5;color:#fff}.tier.tD{background:#6b7280;color:#fff}
.tiers{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:8px 0 10px}.tcol{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:6px 9px}
.tcol h5{margin:2px 0;font-size:13px}.tcol p{margin:2px 0 4px}.tcol ul{margin:0;padding-left:16px;font-size:12.5px}.tcol li{margin:3px 0}
@media(max-width:900px){.tiers{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:520px){.tiers{grid-template-columns:1fr}}
.pickbox{border:2px solid #c9a227;border-radius:10px;padding:8px 12px;margin:0 0 12px;background:color-mix(in srgb,#c9a227 8%,transparent)}
.pickbox h4{margin:2px 0 6px;color:#c9a227}.picks{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px;margin:4px 0}
.pick{background:var(--card);border:1px solid #c9a227;border-radius:8px;padding:8px 10px}.pick div{margin:3px 0}
.pkn{display:inline-block;background:#c9a227;color:#111;font-weight:700;border-radius:5px;padding:0 6px;margin-right:6px;font-size:12px}
tr.pickrow td{background:color-mix(in srgb,#c9a227 13%,transparent)}tr.pickrow:not(.why) td:first-child{box-shadow:inset 3px 0 0 #c9a227}
.pill.pickp{color:#111;background:#c9a227;border-color:#c9a227;font-weight:700}.fmstar{color:#c9a227;font-weight:700}.howto{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:8px 12px;font-size:12.5px;margin:0 0 10px}
.howto ol{margin:4px 0 0;padding-left:20px}.howto li{margin:3px 0}.sbox{margin:0 0 8px}.sbox input{min-width:280px;padding:6px 10px;text-align:left}.onlysig{margin-left:14px}tr.nosig td{opacity:.88}.newp{color:var(--up);border-color:var(--up)}
.warnbox{background:color-mix(in srgb,var(--warn) 12%,transparent);border:1px solid color-mix(in srgb,var(--warn) 45%,transparent);border-radius:8px;padding:8px 11px;font-size:12.5px;margin:0 0 10px}
ol.top5{margin:4px 0;padding-left:20px}ol.top5 li{display:flex;justify-content:space-between;gap:8px;padding:2px 0;border-bottom:1px solid var(--bd)}
ol.top5 li{display:list-item}ol.top5 li b{float:right}.golink{color:var(--ac)}
@media(max-width:900px){.gurus{grid-template-columns:1fr}}
@media(max-width:760px){.sbar{min-width:70px}table.score{min-width:0}table.score .opt{display:none}table.score .rc{white-space:normal}}
"""
