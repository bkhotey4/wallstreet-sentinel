"""Build the static 情報站 (intel station) site from live public market data.

    python -m tools.build_site [--out site] [--no-ai] [--fixture]

Headless: no Discord, no portfolio. Designed to run inside GitHub Actions on a schedule.
Outputs  <out>/index.html  (self-contained, no external requests)  and  <out>/data.json.
"""
from __future__ import annotations

import argparse
import asyncio
import html
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from wsb.config import SETTINGS

# Intel-station mode is enforced here, whatever settings.yaml says: this site must never carry holdings.
SETTINGS.raw.setdefault("portfolio", {})["enabled"] = False

log = logging.getLogger("build_site")
esc = html.escape

GROUP_LABELS = {
    "us_equity": "美股指數", "volatility": "波動率", "europe": "歐洲", "asia": "亞洲", "emerging": "新興市場",
    "rates": "利率／債券", "credit": "信用", "fx": "外匯", "commodities": "大宗商品", "crypto": "加密貨幣",
    "sectors": "美股類股",
}
BLOCK_LABELS = {}                                    # blocks keep the names used in settings.yaml
LEVEL_COLORS = ["#2fbf71", "#e3c53a", "#f0903c", "#e5484d", "#b0143c"]
PATH_STATE_COLORS = {"點火": "#e5484d", "升溫": "#f0903c", "留意": "#e3c53a", "平靜": "#2fbf71"}


# ----------------------------------------------------------------- helpers
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


def level_color(score):
    lv = SETTINGS.get("stress_levels", [])
    for i, l in enumerate(lv):
        if score < l["max"]:
            return LEVEL_COLORS[min(i, len(LEVEL_COLORS) - 1)]
    return LEVEL_COLORS[-1]


def md_to_html(text: str) -> str:
    """Tiny, safe markdown subset (headers, bold, bullets, paragraphs) for the AI brief."""
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
        elif line.strip():
            out.append(f"<p>{line}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def sparkline(series, w=720, h=140, n=500):
    s = series.dropna().tail(n)
    if len(s) < 5:
        return ""
    lo, hi = 0.0, 100.0
    xs = [i / (len(s) - 1) * w for i in range(len(s))]
    ys = [h - (min(max(v, lo), hi) - lo) / (hi - lo) * h for v in s.values]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    bands, prev = [], 0.0
    for i, l in enumerate(SETTINGS.get("stress_levels", [])):
        top = min(l["max"], 100.0)
        y1, y0 = h - top / 100 * h, h - prev / 100 * h
        bands.append(f'<rect x="0" y="{y1:.1f}" width="{w}" height="{y0 - y1:.1f}" fill="{LEVEL_COLORS[min(i, 4)]}" opacity="0.10"/>')
        prev = top
    d0, d1 = s.index[0].strftime("%Y-%m"), s.index[-1].strftime("%Y-%m-%d")
    return (f'<svg viewBox="0 0 {w} {h + 22}" class="spark" role="img" aria-label="SSI 近期走勢">{"".join(bands)}'
            f'<polyline points="{pts}" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>'
            f'<text x="0" y="{h + 16}" class="axis">{d0}</text><text x="{w}" y="{h + 16}" class="axis" text-anchor="end">{d1}</text></svg>')


def bar(value, color, maxv=100):
    v = 0 if value is None else max(0, min(value, maxv))
    return f'<div class="bar"><i style="width:{v / maxv * 100:.0f}%;background:{color}"></i></div>'


# ----------------------------------------------------------------- sections
def sec_hero(eng, now):
    st = eng.stress
    if not st:
        return '<section class="card"><h2>系統性壓力指數</h2><p class="muted">資料載入失敗，請稍後再試。</p></section>'
    col = level_color(st.score)
    pb = eng.playbook or {}
    chips = "".join(f'<span class="chip {cls(-v if v is not None else None)}">{lbl} {num(v, 1, sign=True)}</span>'
                    for lbl, v in (("1日", st.chg_1d), ("5日", st.chg_5d), ("20日", st.chg_20d)))
    stage = (f'<div class="stage"><span class="big">{esc(pb.get("emoji", ""))}</span> 風險階段：<b>{esc(pb.get("name", "—"))}</b>'
             f'<span class="muted">（風險分 {pb.get("points", "—")}；0–1 正常 · 2–3 留意 · 4–5 戒備 · ≥6 防禦）</span></div>') if pb else ""
    lv = SETTINGS.get("stress_levels", [])
    segs = "".join('<i style="background:%s;flex:%s"></i>' % (LEVEL_COLORS[min(i, 4)], min(l["max"], 100) - (lv[i - 1]["max"] if i else 0))
                   for i, l in enumerate(lv))
    return f'''<section class="card hero">
<div class="hero-main"><div class="score" style="color:{col}">{st.score:.0f}</div>
<div><div class="label">{esc(str(st.emoji))} {esc(str(st.label))}</div>
<div class="muted">系統性壓力指數 SSI（0–100）· 歷史百分位 {num(st.pctile_all, 0)}% · 資料涵蓋 {st.coverage * 100:.0f}%</div>
<div class="chips">{chips}</div></div></div>
<div class="gauge"><div class="track">{segs}
<b style="left:{min(st.score, 100):.1f}%"></b></div></div>
{stage}
<div style="color:{col}">{sparkline(st.history)}</div></section>'''


def sec_odds(eng):
    o = eng.odds or {}
    if not o.get("horizons"):
        return ""
    rows = []
    for h in o["horizons"]:
        adj, base = h.get("adjusted"), h.get("base_rate")
        lift = h.get("lift_adj")
        rows.append(f'<tr><td class="nw">{h["days"]} 日內跌 ≥ {h["drawdown_pct"]:.0f}%</td><td class="r"><b>{num(adj, 1)}%</b></td>'
                    f'<td class="r">{num(h.get("conditional"), 1)}%</td><td class="r muted">{num(base, 1)}%</td>'
                    f'<td class="r {("dn" if (lift or 1) > 1.15 else "up" if (lift or 1) < 0.85 else "")}">{num(lift, 2)}×</td>'
                    f'<td class="r muted">{h.get("episodes_in_zone", "—")}</td></tr>')
    mom = o.get("momentum") or {}
    return f'''<section class="card"><h2>經驗崩跌機率</h2>
<p class="muted">SSI 落在「{esc(str(o.get("bucket")))}」區間時，歷史上標普 500 隨後大跌的頻率（樣本自 {esc(str(o.get("sample_start")))}）。升溫狀態：<b>{esc(str(mom.get("state") or "—"))}</b>（20 日 {num(mom.get("chg20"), 1, sign=True)} 點）。</p>
<div class="scroll"><table><thead><tr><th>情境</th><th class="r">含升溫速度</th><th class="r">僅看水準</th><th class="r">平常基準</th><th class="r">倍數</th><th class="r">獨立事件</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p class="note">這是歷史條件頻率，不是預測；倍數 &gt; 1 代表比歷史平常更危險。</p></section>'''


def sec_shock(eng):
    sk = eng.shock or {}
    if not sk.get("radar"):
        return ""
    radar = "".join(
        f'<tr><td>{esc(r["block"])}</td><td class="r">{r["level"]:.0f}</td><td>{bar(r["level"], level_color(r["level"]))}</td>'
        f'<td class="r {cls(-(r["chg20"] or 0))}">{num(r["chg20"], 1, sign=True)}</td><td>{esc(str(r["state"]))}</td>'
        f'<td class="r muted">{num(r.get("auc"), 2)}</td></tr>' for r in sk["radar"])
    paths = ""
    for p in sk.get("paths", [])[:4]:
        c = next((v for k, v in PATH_STATE_COLORS.items() if k in str(p.get("state"))), "#8a94a6")
        paths += (f'<div class="path"><div class="ph"><b>{esc(p["name"])}</b><span class="pill" style="background:{c}">{esc(str(p.get("state")))} · {p["ignition"]:.0f}</span></div>'
                  f'{bar(p["ignition"], c)}<p class="muted">{esc(p.get("story", ""))}</p></div>')
    dv = sk.get("divergence") or {}
    dvh = ""
    if dv.get("available"):
        flag = ' <span class="pill" style="background:#e5484d">背離警示</span>' if dv.get("flag") else ""
        dvh = (f'<p>股債背離：信用／利率／流動性／新興壓力 <b>{dv["credit"]:.0f}</b> vs 股市隱含恐慌 <b>{dv["equity"]:.0f}</b>，差 {dv["gap"]:+.0f}{flag}</p>')
    return f'''<section class="card"><h2>衝擊雷達 — 下一次衝擊可能從哪裡點火</h2>
<div class="grid2"><div>{paths}</div>
<div class="scroll"><table><thead><tr><th>風險區塊</th><th class="r">水準</th><th></th><th class="r">20日變化</th><th>狀態</th><th class="r">預警力 AUC</th></tr></thead><tbody>{radar}</tbody></table></div></div>
{dvh}</section>'''


def sec_playbook(eng):
    pb = eng.playbook or {}
    if not pb:
        return ""
    why = "".join(f'<li><span class="pts">{("+%s" % w[0]) if isinstance(w, (list, tuple)) and w[0] else "0"}</span> {esc(str(w[1] if isinstance(w, (list, tuple)) else w))}</li>'
                  for w in pb.get("why", []))
    acts = [re.sub(r"[（(]?/\w+[）)]?", "", str(a)).strip() for a in (pb.get("actions") or [])
            if not re.search(r"持倉|持股|你的|減碼名單|/hedge", str(a))]
    ah = f'<h3>此階段的一般性行動框架</h3><ul>{"".join(f"<li>{esc(str(a))}</li>" for a in acts)}</ul>' if acts else ""
    return f'''<section class="card"><h2>風險劇本 <span class="muted">規則式、每一分都可追溯</span></h2>
<p class="stage"><span class="big">{esc(pb.get("emoji", ""))}</span> <b>{esc(pb.get("name", ""))}</b> · 風險分 {pb.get("points")}</p>
<ul class="why">{why or "<li class='muted'>目前沒有觸發任何計分項目</li>"}</ul>{ah}</section>'''


def sec_breaks(eng):
    br = eng.breaks or {}
    if not br.get("available"):
        return ""
    m = br["metrics"]
    items = []
    sb = m.get("stock_bond_corr")
    if sb:
        items.append(f'股債 {sb["window"]} 日相關 <b>{sb["value"]:+.2f}</b>（歷史 {sb["pctile"]:.0f}% 分位；≥ {sb["threshold"]:+.2f} 視為債券失去避險功能）')
    if m.get("double_kill_20d"):
        items.append(f'近 20 日股債雙殺日 <b>{m["double_kill_20d"]["value"]}</b> 天')
    if m.get("haven_fail"):
        items.append(f'股票跌 ≥ 1% 的 {m["haven_fail"]["n"]} 天中，長債與黃金同跌比例 <b>{m["haven_fail"]["value"]:.0f}%</b>')
    flags = "".join(f'<li class="warn">⚠ {esc(fl["detail"])}</li>' for fl in br.get("flags", []))
    return f'''<section class="card"><h2>避險有效性 <span class="muted">股債與避險資產還有分散效果嗎？</span></h2>
<ul>{"".join(f"<li>{i}</li>" for i in items)}{flags}</ul></section>'''


def sec_quality(eng):
    sk = eng.shock or {}
    ql = sk.get("quality") or {}
    rows = ""
    for w in ql.get("walk_forward", []):
        if w.get("n_test"):
            rows += (f'<tr><td>{w["days"]} 日跌 ≥ {w["drawdown_pct"]:.0f}%</td><td class="r">{num(w.get("auc_oos"), 2)}</td>'
                     f'<td>{esc(str(w.get("verdict")))}</td><td class="r">{num((w.get("skill") or 0) * 100, 0)}%</td></tr>')
    es = ql.get("episode_summary") or {}
    ep = ""
    if es.get("n"):
        ep = (f'<p>歷史 {es["n"]} 次標普 ≥ 10% 回檔：高點前已預警 <b>{es["warned_before_peak"]}</b> 次'
              + (f'，領先中位數 {es["median_lead_days"]:.0f} 個交易日' if es.get("median_lead_days") is not None else "") + "。</p>")
    lab = eng.lab or {}
    lines = []
    for hz in lab.get("horizons", []):
        if not hz.get("baseline"):
            continue
        e = hz.get("ensemble")
        if e and e.get("accepted"):
            lines.append(f'{hz["days"]} 日：採用 {esc(", ".join(hz["adopted"]))}，AUC {e["auc"]:.2f}（{e["d_auc"]:+.2f}）')
        else:
            lines.append(f'{hz["days"]} 日：沒有候選指標通過走步檢驗與安慰劑對照，沿用原模型（基準 AUC {hz["baseline"]["auc"]:.2f}）')
    if not (rows or ep or lines):
        return ""
    return f'''<section class="card"><h2>模型可信度 <span class="muted">誠實揭露</span></h2>
<div class="scroll"><table><thead><tr><th>情境</th><th class="r">樣本外 AUC</th><th>鑑別力</th><th class="r">Brier 技能</th></tr></thead><tbody>{rows}</tbody></table></div>
{ep}<h3>特徵實驗室</h3><ul>{"".join(f"<li>{l}</li>" for l in lines)}</ul>
<p class="note">AUC 0.5 ＝ 隨機、1.0 ＝ 完美；低於 0.6 代表鑑別力有限，請把這裡當風險溫度計，而不是預測器。</p></section>'''


def sec_markets(eng):
    names = SETTINGS.names()
    tabs, panels = [], []
    for i, g in enumerate(SETTINGS.universe.keys()):
        rows = eng.market.returns_table(SETTINGS.group(g))
        if not rows:
            continue
        body = "".join(
            f'<tr><td>{esc(names.get(r["ticker"], r["ticker"]))}<span class="tk">{esc(r["ticker"])}</span></td><td class="r">{num(r["price"], 2)}</td>'
            f'<td class="r {cls(r["d1"])}">{num(r["d1"], 2, sign=True, pct=True)}</td><td class="r {cls(r.get("w1"))}">{num(r.get("w1"), 1, sign=True, pct=True)}</td>'
            f'<td class="r {cls(r.get("m1"))}">{num(r.get("m1"), 1, sign=True, pct=True)}</td><td class="r {cls(r.get("ytd"))}">{num(r.get("ytd"), 1, sign=True, pct=True)}</td>'
            f'<td class="r muted">{num(r.get("pct_52w"), 0)}%</td></tr>' for r in rows)
        tabs.append(f'<button class="tab{" on" if not tabs else ""}" data-t="g{i}">{esc(GROUP_LABELS.get(g, g))}</button>')
        panels.append(f'<div class="panel{" on" if len(panels) == 0 else ""}" id="g{i}"><div class="scroll"><table><thead><tr><th>標的</th><th class="r">價格</th><th class="r">今日</th><th class="r">1 週</th><th class="r">1 月</th><th class="r">年初至今</th><th class="r">52 週位置</th></tr></thead><tbody>{body}</tbody></table></div></div>')
    return f'<section class="card"><h2>全球跨資產行情</h2><div class="tabs">{"".join(tabs)}</div>{"".join(panels)}<p class="note">報價來自 Yahoo Finance，可能延遲約 15 分鐘；「52 週位置」＝目前價格在一年高低區間的相對位置。</p></section>'


def sec_macro(eng):
    rg = eng.regime or {}
    rows = ""
    for sid, name in SETTINGS.get("fred_series", {}).items():
        x = eng.fred.latest(sid)
        if x:
            rows += (f'<tr><td>{esc(name)}</td><td class="r">{num(x["value"], 3)}</td><td class="r {cls(x.get("chg_1m"))}">{num(x.get("chg_1m"), 3, sign=True)}</td>'
                     f'<td class="r {cls(x.get("chg_3m"))}">{num(x.get("chg_3m"), 3, sign=True)}</td><td class="r muted">{num(x.get("pctile_3y"), 0)}</td><td class="r muted">{x["date"]}</td></tr>')
    reg = ""
    if rg:
        reg = (f'<p>總經象限：<b>{esc(str(rg.get("quadrant", "—")))}</b> · 風險偏好：<b>{esc(str(rg.get("risk_mode", "—")))}</b> · '
               f'淨流動性 {num(rg.get("net_liquidity_bn"), 0)} bn（13 週 {num(rg.get("net_liquidity_chg_13w_bn"), 0, sign=True)} bn，{esc(str(rg.get("liquidity_mode", "")))}）</p>')
    if not (rows or reg):
        return ""
    tbl = (f'<div class="scroll"><table><thead><tr><th>指標</th><th class="r">最新</th><th class="r">1 月變化</th><th class="r">3 月變化</th><th class="r">3 年百分位</th><th class="r">日期</th></tr></thead><tbody>{rows}</tbody></table></div>') if rows else \
        '<p class="muted">未設定 FRED_API_KEY，總經序列略過（壓力指數會改用其餘資料）。</p>'
    return f'<section class="card"><h2>總經與流動性</h2>{reg}{tbl}</section>'


def sec_positioning(eng):
    op = eng.options.spx or {}
    L = []
    if op:
        L.append(f'<li>SPX 選擇權（CBOE）：GEX <b>{num(op.get("gex_usd_bn_per_1pct"), 2, sign=True)}</b> bn／1% · 零 Gamma 翻轉點 {num(op.get("zero_gamma"), 0)}'
                 f'（現價相對 {num(op.get("spot_vs_flip_pct"), 2, sign=True, pct=True)}）· Call 牆 {num(op.get("call_wall"), 0)} · Put 牆 {num(op.get("put_wall"), 0)} · P/C(OI) {num(op.get("put_call_oi"), 2)}</li>')
    cd = eng.crypto.data or {}
    if cd:
        L.append("<li>情緒／加密：" + " · ".join(f"{esc(str(k))} {esc(num(v, 2) if isinstance(v, (int, float)) else str(v))}" for k, v in list(cd.items())[:10]) + "</li>")
    if not L:
        return ""
    return f'<section class="card"><h2>部位與情緒</h2><ul>{"".join(L)}</ul></section>'


def sec_taiwan(eng):
    tw = eng.taiwan
    if not (tw.flows or tw.futures):
        return ""
    return f'<section class="card"><h2>台灣籌碼 <span class="muted">證交所／期交所官方資料</span></h2><ul>{"".join(f"<li>{esc(l)}</li>" for l in tw.summary_lines())}</ul></section>'


def sec_calendar(eng):
    ev = eng.calendar.upcoming(14)
    if not ev:
        return ""
    rows = "".join(f'<tr><td class="nw">{esc(e["date"])}</td><td>{esc(e["event"])}</td><td class="muted">{esc(str(e.get("type", "")))}</td></tr>' for e in ev[:30])
    return f'<section class="card"><h2>未來 14 天事件</h2><div class="scroll"><table><tbody>{rows}</tbody></table></div></section>'


def sec_news(eng):
    items = eng.news.top(20)
    if not items:
        return ""
    tz = ZoneInfo(SETTINGS.get("timezone", "Asia/Taipei"))
    rows = ""
    for n in items:
        link = esc(n.link) if str(n.link).startswith(("http://", "https://")) else "#"
        t = datetime.fromtimestamp(n.ts, tz).strftime("%m/%d %H:%M") if n.ts else ""
        rows += (f'<li><span class="sc">{n.score}</span><a href="{link}" target="_blank" rel="noopener noreferrer">{esc(n.title)}</a>'
                 f'<span class="muted"> · {esc(n.source)} · {t}</span></li>')
    return f'<section class="card"><h2>風險新聞 <span class="muted">依關鍵字風險分數排序</span></h2><ul class="news">{rows}</ul></section>'


def sec_health():
    from wsb.health import HEALTH
    rows = "".join(f'<tr><td>{esc(s.name)}</td><td class="{s.state}">{s.state}</td></tr>'
                   for s in sorted(HEALTH.sources.values(), key=lambda x: (x.state == "ok", x.name)))
    bad = sum(1 for s in HEALTH.sources.values() if s.state not in ("ok",))
    return f'<section class="card"><details><summary><h2 style="display:inline">資料源健康 <span class="muted">{len(HEALTH.sources) - bad}/{len(HEALTH.sources)} 正常</span></h2></summary><div class="scroll"><table><tbody>{rows}</tbody></table></div></details></section>'


def sec_ai(text, engine_name):
    if not text:
        return ""
    return f'<section class="card ai"><h2>AI 研判 <span class="muted">由 {esc(engine_name)} 依上述公開數據自動產生，可能有誤</span></h2>{md_to_html(text)}</section>'


# ----------------------------------------------------------------- page
CSS = """
:root{--bg:#0b0f1a;--card:#121a2b;--bd:#1f2b44;--tx:#e8ecf5;--mu:#8a96ad;--up:#2fbf71;--dn:#e5484d;--ac:#6ea8ff}
@media (prefers-color-scheme: light){:root{--bg:#f4f6fb;--card:#fff;--bd:#dde3ee;--tx:#141b2d;--mu:#5d6b85;--up:#14894c;--dn:#cc2d33;--ac:#2f6fe0}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 system-ui,"Noto Sans TC","Microsoft JhengHei",sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:16px}header{padding:18px 0 6px}h1{margin:0;font-size:24px}h1 small{font-weight:400;color:var(--mu);font-size:13px;display:block;margin-top:4px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px;margin:14px 0}h2{margin:0 0 10px;font-size:17px}h3{font-size:14px;margin:14px 0 6px;color:var(--mu)}h4{margin:12px 0 4px}
.muted{color:var(--mu);font-weight:400;font-size:13px}.note{color:var(--mu);font-size:12.5px;margin:10px 0 0}
.hero-main{display:flex;gap:20px;align-items:center;flex-wrap:wrap}.score{font-size:76px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums}.label{font-size:22px;font-weight:700}
.chips{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}.chip{border:1px solid var(--bd);border-radius:99px;padding:2px 10px;font-size:13px}
.gauge{margin:18px 0 8px}.track{position:relative;display:flex;height:10px;border-radius:99px;overflow:hidden}.track i{display:block}.track b{position:absolute;top:-4px;width:4px;height:18px;background:var(--tx);border-radius:2px;transform:translateX(-2px)}
.stage{margin:8px 0}.big{font-size:20px}.spark{width:100%;height:auto;margin-top:6px}.axis{fill:var(--mu);font-size:11px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:7px 8px;border-bottom:1px solid var(--bd);text-align:left;vertical-align:middle}th{color:var(--mu);font-weight:500;font-size:12.5px;white-space:nowrap}.r{text-align:right;font-variant-numeric:tabular-nums}.nw{white-space:nowrap}
.scroll{overflow-x:auto}.scroll table{min-width:480px}.up{color:var(--up)}.dn{color:var(--dn)}.tk{color:var(--mu);font-size:11.5px;margin-left:6px}
.bar{height:8px;border-radius:99px;background:var(--bd);overflow:hidden;min-width:70px}.bar i{display:block;height:100%;border-radius:99px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media(max-width:760px){.grid2{grid-template-columns:1fr}.score{font-size:60px}}
.path{margin-bottom:14px}.ph{display:flex;justify-content:space-between;gap:8px;margin-bottom:4px}.pill{color:#fff;border-radius:99px;padding:1px 10px;font-size:12px;white-space:nowrap}
.why li{margin:3px 0}.pts{display:inline-block;min-width:26px;color:var(--ac);font-weight:700}.warn{color:var(--dn)}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}.tab{background:none;border:1px solid var(--bd);color:var(--tx);border-radius:99px;padding:4px 12px;cursor:pointer;font:inherit;font-size:13px}.tab.on{background:var(--ac);border-color:var(--ac);color:#fff}
.panel{display:none}.panel.on{display:block}ul{padding-left:20px;margin:6px 0}.news{list-style:none;padding:0}.news li{padding:6px 0;border-bottom:1px solid var(--bd)}.sc{display:inline-block;min-width:28px;text-align:center;background:var(--bd);border-radius:6px;margin-right:8px;font-size:12px}
a{color:var(--ac);text-decoration:none}a:hover{text-decoration:underline}.ok{color:var(--up)}.degraded,.stale{color:#e3a53a}.down{color:var(--dn)}.pending{color:var(--mu)}
summary{cursor:pointer}footer{color:var(--mu);font-size:12.5px;padding:10px 0 40px}.ai p{margin:6px 0}
"""
JS = """document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.tab,.panel').forEach(e=>e.classList.remove('on'));b.classList.add('on');document.getElementById(b.dataset.t).classList.add('on')}));"""


def render(eng, ai_text="", ai_engine="") -> str:
    tz = ZoneInfo(SETTINGS.get("timezone", "Asia/Taipei"))
    now = datetime.now(tz)
    body = "".join(f() for f in (
        lambda: sec_hero(eng, now), lambda: sec_ai(ai_text, ai_engine), lambda: sec_odds(eng), lambda: sec_shock(eng),
        lambda: sec_playbook(eng), lambda: sec_breaks(eng), lambda: sec_quality(eng), lambda: sec_markets(eng),
        lambda: sec_macro(eng), lambda: sec_positioning(eng), lambda: sec_taiwan(eng), lambda: sec_calendar(eng),
        lambda: sec_news(eng), sec_health))
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>全球金融風險情報站</title><style>{CSS}</style></head><body><div class="wrap">
<header><h1>全球金融風險情報站<small>最後更新 {now:%Y-%m-%d %H:%M}（台北時間）· 每小時自動更新 · 只使用公開市場資料</small></h1></header>
{body}
<footer>資料來源：Yahoo Finance、FRED、CBOE、證交所／期交所、公開新聞 RSS。所有數字為程式自動計算，崩跌機率是歷史條件頻率而非預測；本頁不構成任何投資建議。</footer>
</div><script>{JS}</script></body></html>'''


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
async def build(out: Path, use_ai: bool = True, engine=None) -> Path:
    from wsb.engine import Engine
    eng = engine or Engine()
    if engine is None:
        await eng.bootstrap()
    assert not eng.holdings and not eng.portfolio.get("positions"), "intel-station build must not contain holdings"
    ai_text, ai_engine = "", ""
    if use_ai:
        try:
            from wsb.ai import context, llm, prompts
            pack = context.build(eng, "full")
            ai_text, ai_engine = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.FULL_BRIEF.format(title="今日全球風險情報"), 3000)
            if ai_engine == "none" or ai_text.startswith("⚠️"):
                ai_text, ai_engine = "", ""
        except Exception as e:  # noqa: BLE001
            log.warning("AI brief skipped: %s", e)
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
