"""Discord embed builders (pure formatting; every number comes from Engine)."""
from __future__ import annotations

from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

import discord

from ..ai.context import f
from ..config import SETTINGS
from ..health import HEALTH
from .. import store

TZ = ZoneInfo(SETTINGS.get("timezone", "Asia/Taipei"))
GROUP_TITLES = {"us_equity": "🇺🇸 美股", "volatility": "🌪️ 波動率", "europe": "🇪🇺 歐洲", "asia": "🌏 亞洲",
                "emerging": "🌎 新興市場", "rates": "🏛️ 美債殖利率", "credit": "🏦 信用/銀行/私募信貸",
                "fx": "💱 匯率", "commodities": "🛢️ 商品", "crypto": "₿ 加密", "sectors": "🧩 板塊/因子"}


def color(score: float | None) -> int:
    if score is None:
        return 0x95A5A6
    for lim, c in ((35, 0x2ECC71), (55, 0xF1C40F), (70, 0xE67E22), (85, 0xE74C3C)):
        if score < lim:
            return c
    return 0x8B0000


def bar(v: float | None, n: int = 10) -> str:
    if v is None:
        return "░" * n
    k = max(0, min(n, round(v / 100 * n)))
    return "█" * k + "░" * (n - k)


def arrow(x):
    if x is None:
        return "▫️"
    return "🟩" if x > 0 else "🟥" if x < 0 else "⬜"


def footer(e: discord.Embed, engine) -> discord.Embed:
    e.set_footer(text=f"WallStreet Sentinel · {engine.age_str()} · {datetime.now(TZ):%m/%d %H:%M} 台北 · 非投資建議")
    return e


def group_lines(engine, group: str, limit: int = 14, show_sigma: bool = True) -> str:
    names = SETTINGS.names()
    rows = engine.market.returns_table(SETTINGS.group(group))[:limit]
    lines = []
    for r in rows:
        sig = r.get("sigma")
        flag = " ⚠️" if sig is not None and abs(sig) >= 2 else ""
        s = f" σ{sig:+.1f}" if show_sigma and sig is not None else ""
        lines.append(f"{arrow(r['d1'])} {names.get(r['ticker'], r['ticker'])} `{f(r['price'])}` "
                     f"**{f(r['d1'], 2, pct=True, sign=True)}**{s}{flag}")
    return "\n".join(lines)[:1024] or "資料載入中"


def dashboard(engine) -> discord.Embed:
    st = engine.stress
    e = discord.Embed(title="🌐 全球金融戰情室 Global War Room", color=color(st.score if st else None))
    if st:
        e.description = (f"{st.emoji} **系統性壓力指數 SSI {st.score:.1f}/100 — {st.label}**  `{bar(st.score)}`\n"
                         f"1日 {f(st.chg_1d, 1, sign=True)} · 5日 {f(st.chg_5d, 1, sign=True)} · 20日 {f(st.chg_20d, 1, sign=True)} · "
                         f"歷史百分位 {f(st.pctile_all, 0)}%")
    rg = engine.regime
    if rg.get("quadrant"):
        e.add_field(name="🧭 總經情勢", value=f"**{rg['quadrant']}**\n{rg.get('risk_mode','')}\n流動性：{rg.get('liquidity_mode','NA')}", inline=False)
    for g in ("us_equity", "volatility", "asia", "europe", "rates", "credit", "fx", "commodities", "crypto"):
        e.add_field(name=GROUP_TITLES[g], value=group_lines(engine, g, 7, show_sigma=False), inline=True)
    return footer(e, engine)


def risk(engine) -> discord.Embed:
    st = engine.stress
    if not st:
        return discord.Embed(title="壓力指數計算中…", description="等待歷史資料載入", color=0x95A5A6)
    e = discord.Embed(title=f"{st.emoji} 系統性壓力指數 SSI：{st.score:.1f} / 100（{st.label}）",
                      color=color(st.score))
    e.description = (f"`{bar(st.score, 20)}`\n變化：1日 **{f(st.chg_1d,1,sign=True)}** · 5日 **{f(st.chg_5d,1,sign=True)}** · "
                     f"20日 **{f(st.chg_20d,1,sign=True)}**\n目前處於歷史 **{f(st.pctile_all,0)}%** 百分位 · 資料覆蓋 {st.coverage*100:.0f}%\n"
                     f"*每個因子都以自身 3 年滾動歷史標準化，無固定門檻*")
    blk = "\n".join(f"`{bar(v)}` {v:5.1f} {k}" for k, v in sorted(st.blocks.items(), key=lambda x: -x[1]))
    e.add_field(name="🧱 風險區塊", value=blk[:1024], inline=False)
    drv = "\n".join(f"🔺 `{c.id}` 分數 **{c.score:.0f}** (z {c.z:+.2f}, 值 {f(c.raw, 4)})" for c in st.drivers(6))
    e.add_field(name="主要推升因子", value=drv[:1024] or "—", inline=False)
    rel = "\n".join(f"🔻 `{c.id}` 分數 {c.score:.0f} (z {c.z:+.2f})" for c in st.relief(3))
    e.add_field(name="緩解因子", value=rel[:1024] or "—", inline=False)
    od = engine.odds
    if od.get("horizons"):
        mom = od.get("momentum") or {}
        lines = [f"**{h['days']}日內跌≥{h['drawdown_pct']:.0f}%**：{f(h.get('adjusted'),1)}%（{h.get('lift_adj_text','')}；"
                 f"基準 {f(h['base_rate'],1)}%、僅看水準 {f(h['conditional'],1)}%）"
                 for h in od["horizons"]]
        e.add_field(name=f"📉 經驗崩跌機率（SSI 區間 {od.get('bucket')}・20日 {f(mom.get('chg20'),1,sign=True)} {mom.get('state') or ''}）",
                    value="\n".join(lines), inline=False)
    return footer(e, engine)


def crash(engine) -> discord.Embed:
    od = engine.odds
    e = discord.Embed(title="📉 崩跌機率實證回測", color=color(engine.stress.score if engine.stress else None))
    if not od.get("horizons"):
        e.description = od.get("error", "計算中…")
        return footer(e, engine)
    mom = od.get("momentum") or {}
    e.description = (f"問題：**歷史上 SSI 落在今天的區間（{od['bucket']}）、且升溫速度相同（{mom.get('state') or '—'}）時，標普 500 之後跌到門檻的頻率？**\n"
                     f"SSI 20 日變化 {f(mom.get('chg20'),1,sign=True)} 點（歷史 {f(mom.get('pctile'),0)} 百分位）。"
                     f"倍數 >1 比平常危險、<1 比平常安全。\n"
                     f"樣本起點 {od['sample_start']} · {od['n_days']} 個交易日。重疊視窗會高估樣本數，請看『獨立事件』欄位。")
    for h in od["horizons"]:
        tbl = "\n".join(f"`{t['zone']:>7}` {bar(t['prob'], 8)} {t['prob']:5.1f}% ({t['days']}天)" for t in h["table"])
        e.add_field(
            name=(f"{h['days']}交易日內 −{h['drawdown_pct']:.0f}%：{f(h.get('adjusted'),1)}%（{h.get('lift_adj_text','')}）"
                  f"・僅看水準 {f(h['conditional'],1)}%・基準 {f(h['base_rate'],1)}%")[:256],
            value=(f"區間天數 {h['obs_in_zone']} · 獨立事件 {h['episodes_in_zone']} · 區間中位最深回撤 {f(h['median_fwd_min_in_zone'],1)}%\n{tbl}")[:1024],
            inline=False)
    return footer(e, engine)


def market_group(engine, group: str) -> discord.Embed:
    e = discord.Embed(title=GROUP_TITLES.get(group, group), color=0x3498DB)
    names = SETTINGS.names()
    rows = engine.market.returns_table(SETTINGS.group(group))
    for r in rows[:24]:
        e.add_field(
            name=f"{names.get(r['ticker'], r['ticker'])} ({r['ticker']})",
            value=(f"`{f(r['price'])}` **{f(r['d1'],2,pct=True,sign=True)}** σ{f(r.get('sigma'),1,sign=True)}\n"
                   f"1W {f(r.get('w1'),1,pct=True,sign=True)} · 1M {f(r.get('m1'),1,pct=True,sign=True)} · "
                   f"YTD {f(r.get('ytd'),1,pct=True,sign=True)}\n52週位置 {f(r.get('pct_52w'),0)}%"),
            inline=True)
    return footer(e, engine)


def macro(engine) -> discord.Embed:
    rg = engine.regime
    e = discord.Embed(title="🏛️ 總經 / 信用 / 流動性儀表", color=0x9B59B6)
    if rg.get("quadrant"):
        e.description = (f"**象限：{rg['quadrant']}**（成長 z {f(rg.get('growth_z'))} · 通膨 z {f(rg.get('inflation_z'))}）\n"
                         f"{rg.get('playbook','')}\n風險偏好：**{rg.get('risk_mode','NA')}** · "
                         f"淨流動性 {f(rg.get('net_liquidity_bn'),0)}bn（13週 {f(rg.get('net_liquidity_chg_13w_bn'),0,sign=True)}bn）")
    lines = []
    for sid, name in SETTINGS.get("fred_series", {}).items():
        x = engine.fred.latest(sid)
        if x:
            lines.append(f"**{name}** `{f(x['value'],2)}` 1M {f(x['chg_1m'],2,sign=True)} · 1Y {f(x['chg_1y'],2,sign=True)} "
                         f"· 3Y百分位 {f(x.get('pctile_3y'),0)} ({x['date'][5:]})")
    for i in range(0, len(lines), 8):
        e.add_field(name="FRED 即時序列" if i == 0 else "​", value="\n".join(lines[i:i + 8])[:1024], inline=False)
    return footer(e, engine)


def options(engine) -> discord.Embed:
    op = engine.options.spx
    e = discord.Embed(title="🎯 SPX 選擇權造市商部位 (Gamma)", color=0x1ABC9C)
    if not op:
        e.description = "CBOE 資料載入中或失敗"
        return footer(e, engine)
    regime = "正 Gamma：造市商逆勢避險，波動被壓抑" if (op.get("gex_usd_bn_per_1pct") or 0) > 0 else "負 Gamma：造市商順勢追殺，波動被放大 ⚠️"
    e.description = (f"SPX `{f(op['spot'],0)}` · 零Gamma翻轉點 **{f(op.get('zero_gamma'),0)}**（現價相對 {f(op.get('spot_vs_flip_pct'),2,sign=True,pct=True)}）\n"
                     f"GEX **{f(op.get('gex_usd_bn_per_1pct'),2,sign=True)} bn/1%** → {regime}\n"
                     f"Call Wall {f(op.get('call_wall'),0)} · Put Wall {f(op.get('put_wall'),0)}\n"
                     f"Put/Call OI {f(op.get('put_call_oi'))} · Vol {f(op.get('put_call_volume'))}\n"
                     f"*CBOE 延遲報價，60日內到期合約，假設造市商持有 call 多單 / put 空單*")
    return footer(e, engine)


def portfolio(engine) -> discord.Embed:
    p = engine.portfolio
    if not p or p.get("error"):
        return discord.Embed(title="💼 持倉", description=p.get("error", "計算中") if p else "計算中", color=0x95A5A6)
    e = discord.Embed(title="💼 持倉風險駕駛艙", color=0x2C3E50)
    e.description = (f"總值 **${f(p['total_value_usd'],0)}** · 未實現 **{f(p['pnl_pct'],1,sign=True,pct=True)}** (${f(p['pnl_usd'],0,sign=True)})\n"
                     f"今日 **${f(p['day_pnl_usd'],0,sign=True)}** · β **{f(p['beta'])}** · 年化波動 {f(p['vol_ann_pct'],1)}% · "
                     f"近1年最大回撤 {f(p['max_dd_1y_pct'],1)}%\n"
                     f"VaR95 1日 **${f(p['var95_1d_usd'],0)}** · VaR99 1日 **${f(p['var99_1d_usd'],0)}** · CVaR97.5 ${f(p['cvar975_1d_usd'],0)} · "
                     f"VaR99 10日 ${f(p['var99_10d_usd'],0)}\n集中度：有效檔數 **{f(p['effective_n'],1)}**")
    lines = []
    for r in p["positions"]:
        if "value_usd" not in r:
            lines.append(f"❔ {r['sym']} {r.get('error')}")
            continue
        sig = r.get("sigma")
        lines.append(f"{arrow(r['d1_pct'])} **{r['sym']}** {f(r['weight'],1)}% · 今日 {f(r['d1_pct'],2,pct=True,sign=True)}"
                     f"{' ⚠️σ'+f(sig,1,sign=True) if sig is not None and abs(sig)>=2 else ''} · 損益 {f(r['pnl_pct'],1,pct=True,sign=True)} · "
                     f"β {f(r.get('beta'))} · 風險貢獻 **{f(r.get('risk_contrib_pct'),0)}%**")
    for i in range(0, len(lines), 8):
        e.add_field(name="持股明細" if i == 0 else "​", value="\n".join(lines[i:i + 8])[:1024], inline=False)
    if p.get("proxied"):
        e.add_field(name="ℹ️ 以 β 代理歷史的標的", value=", ".join(p["proxied"]), inline=False)
    return footer(e, engine)


def stress_test(engine) -> discord.Embed:
    p = engine.portfolio
    e = discord.Embed(title="🧨 歷史危機重播壓力測試", color=0xC0392B)
    if not p or p.get("error"):
        e.description = p.get("error", "計算中") if p else "計算中"
        return e
    e.description = "用**真實歷史價格**重播每段危機期間你的持倉表現（標的當時未上市者以 β×大盤代理）"
    for s in p.get("scenarios", []):
        worst = ", ".join(f"{k} {v:+.0f}%" for k, v in s["worst"])
        e.add_field(name=s["name"],
                    value=(f"大盤 {f(s['bench_pct'],1,pct=True,sign=True)} → 持倉 **{f(s['port_pct'],1,pct=True,sign=True)}** "
                           f"(${f(s['pnl_usd'],0,sign=True)})\n最痛：{worst}" + (f"\n代理：{', '.join(s['proxied'])}" if s["proxied"] else ""))[:1024],
                    inline=False)
    if p.get("hypothetical"):
        e.add_field(name="假設情境（β 推算）",
                    value="\n".join(f"標普 {h['spx_pct']}% → 持倉 {f(h['port_pct'],1,pct=True)} (${f(h['pnl_usd'],0,sign=True)})"
                                    for h in p["hypothetical"]), inline=False)
    return footer(e, engine)


def news(engine, query: str | None = None, latest: bool = False) -> discord.Embed:
    items = engine.news.latest(15) if latest else engine.news.top(15, query)
    e = discord.Embed(title="📰 全球金融情報流" + (f"：{query}" if query else ""), color=0x34495E)
    lines = []
    for n in items:
        tag = "🚨" if n.score >= SETTINGS["alerts"]["news_score"] else "⚠️" if n.score >= 4 else "•"
        t = n.title if len(n.title) < 140 else n.title[:137] + "…"
        lines.append(f"{tag} [{t}]({n.link}) `{n.source}` {('風險'+str(n.score)) if n.score else ''}")
    e.description = "\n".join(lines)[:4000] or "暫無資料"
    return footer(e, engine)


def calendar(engine) -> discord.Embed:
    e = discord.Embed(title="🗓️ 未來 14 天關鍵事件", color=0x16A085)
    icons = {"fomc": "🏦", "macro": "📊", "earnings": "💼", "liquidity": "💧"}
    lines = [f"{icons.get(ev['type'],'•')} `{ev['date']}` {ev['event']}" for ev in engine.calendar.upcoming(14)]
    e.description = "\n".join(lines)[:4000] or "暫無事件（FRED 行事曆需 FRED_API_KEY）"
    return footer(e, engine)


def status(engine) -> discord.Embed:
    e = discord.Embed(title="🩺 資料源健康狀態", color=0x7F8C8D)
    icon = {"ok": "🟢", "degraded": "🟡", "stale": "🟠", "down": "🔴", "pending": "⚪"}
    lines = []
    for s in sorted(HEALTH.sources.values(), key=lambda x: x.name):
        age = f"{s.age/60:.0f}分鐘前" if s.age is not None else "—"
        lines.append(f"{icon[s.state]} `{s.name}` {age} · {s.items}筆" + (f" · {s.error[:60]}" if s.state != "ok" and s.error else ""))
    e.description = "\n".join(lines)[:4000] or "尚未開始"
    al = store.recent_alerts(24)
    if al:
        e.add_field(name="近 24h 警報", value="\n".join(f"{datetime.fromtimestamp(ts, TZ):%H:%M} {sev} {t}" for ts, sev, t in al[:10])[:1024])
    return e


def chunks(text: str, n: int = 1900) -> List[str]:
    out: List[str] = []
    buf = ""
    for line in text.split("\n"):
        while len(line) > n:
            if buf:
                out.append(buf)
                buf = ""
            out.append(line[:n])
            line = line[n:]
        if len(buf) + len(line) + 1 > n:
            out.append(buf)
            buf = ""
        buf += line + "\n"
    if buf.strip():
        out.append(buf)
    return [o for o in out if o.strip()]


# ---------------------------------------------------------------- hedge
def hedge(engine, res: dict) -> List[discord.Embed]:
    if res.get("error"):
        return [discord.Embed(title="🛡️ 避險成本計算器", description=res["error"], color=0x95A5A6)]
    ssi = res.get("ssi")
    head = discord.Embed(title="🛡️ 避險成本計算器", color=color(ssi))
    betas = " · ".join(f"β({k}) {f(v)}" for k, v in res["betas"].items() if v is not None)
    head.description = (f"持倉市值 **${f(res['value'],0)}** · {betas} · SSI **{f(ssi,1)}**\n"
                        f"💡 {res['advice']}\n"
                        f"*CBOE 延遲報價（中價），口數 = 持倉 β 加權名目 ÷ (標的價×100)；情境損益假設到期日結算*")
    out = [head]
    for u, d in res["underlyings"].items():
        e = discord.Embed(title=f"{u} 賣權方案（現價 {f(d['spot'],2)} · 需避險名目 ${f(d['notional'],0)} · 理論 {f(d['raw_contracts'],2)} 口）",
                          color=0x2C3E50)
        for pl in d["plans"][:6]:
            pay = " · ".join(f"跌{k}%：未避險 ${f(v['unhedged'],0)} → 避險後 **${f(v['hedged'],0)}**"
                             for k, v in pl["payoff"].items())
            e.add_field(
                name=f"{pl['expiry']}（{pl['dte']}天） 履約 {f(pl['strike'],0)}（價外 {f(pl['otm_pct'],1)}%）",
                value=(f"{pl['contracts']} 口 × ${f(pl['mid'],2)} = **${f(pl['cost'],0)}**（持倉 {f(pl['cost_pct'],2)}%，年化 {f(pl['cost_pct_ann'],1)}%）"
                       f" · IV {f(pl['iv']*100 if pl['iv'] < 3 else pl['iv'],1)}% · 避險比 {f(pl['hedge_ratio'],2)}x\n{pay}")[:1024],
                inline=False)
        inv = d.get("inverse")
        if inv:
            e.add_field(name=f"替代方案：反向 ETF {inv['symbol']}（{inv['name']}）",
                        value=(f"完全對沖買 ${f(inv['full_hedge_usd'],0)}，半對沖 ${f(inv['half_hedge_usd'],0)}。"
                               "無到期日、可小額，但每日再平衡會在震盪市耗損，只適合短期（數週）使用。"), inline=False)
        out.append(footer(e, engine))
    if res.get("derisk"):
        e = discord.Embed(title="✂️ 替代方案：減碼風險最高的持股（目標降低 25% 大盤曝險）", color=0x7F8C8D)
        e.description = "\n".join(
            f"• 賣出 **{d['sym']}** 約 ${f(d['sell_usd'],0)}（≈{d['shares']} 股）— 風險貢獻 {f(d['risk_contrib_pct'],0)}%"
            for d in res["derisk"]) + "\n*零權利金成本，但放棄上漲空間；可與賣權搭配使用*"
        out.append(e)
    return out[:10]


# ---------------------------------------------------------------- scorecard
def scorecard(engine, res: dict) -> discord.Embed:
    e = discord.Embed(title="📋 警報成績單", color=0x8E44AD)
    if res.get("error"):
        e.description = res["error"]
        return e
    hz = res["horizons"]
    e.description = ("衡量方式：警報發出後，標普 500 在未來 N 個交易日內的**最深跌幅**是否達門檻，"
                     "並和過去 10 年任一天的**基準機率**比較（倍數 >1 代表警報有預警價值）。24 小時內的警報合併為一次事件。\n"
                     + " · ".join(f"{h['days']}日內跌≥{h['drawdown']*100:.0f}% 基準 {res['base'][h['days']]:.1f}%" for h in hz))
    if not res["summary"]:
        e.add_field(name="尚無資料", value="目前還沒有可評分的風險警報；警報發出後需等待 5–20 個交易日才能評分。", inline=False)
    for kind, sm in res["summary"].items():
        lines = [f"事件數 {sm['episodes']}（待評 {sm['pending']}）"]
        for h in hz:
            r = sm["by_horizon"].get(h["days"], {})
            if r.get("episodes"):
                lines.append(f"**{h['days']}日**：命中 {r['hit_rate']:.0f}% vs 基準 {r['base_rate']:.1f}%（×{f(r.get('lift'),1)}），"
                             f"平均最深 {r['avg_min']:+.1f}%、期末 {r['avg_end']:+.1f}%（n={r['episodes']}）")
            else:
                lines.append(f"**{h['days']}日**：尚待評分")
        e.add_field(name=SC_KIND.get(kind, kind), value="\n".join(lines)[:1024], inline=False)
    rec = []
    for ep in res.get("recent", []):
        ts = datetime.fromtimestamp(ep["ts"], TZ).strftime("%m/%d %H:%M")
        marks = []
        for h in hz:
            r = ep["results"].get(h["days"])
            marks.append("⏳" if r is None else ("✅" if r["hit"] else "❌") + f"{r['min_ret']:+.1f}%")
        rec.append(f"`{ts}` {'🚨' if ep['critical'] else '⚠️'} {ep['title'][:60]} → " + " / ".join(marks))
    if rec:
        e.add_field(name="最近事件（✅=之後確實下跌 ❌=沒跌 ⏳=待評）", value="\n".join(rec)[:1024], inline=False)
    return footer(e, engine)


SC_KIND = {"risk": "📉 市場風險警報", "news": "📰 新聞風險警報"}


# ---------------------------------------------------------------- earnings
def earnings_preview(engine, rec: dict) -> discord.Embed:
    im = rec.get("implied")
    e = discord.Embed(title=f"📅 {rec['ticker']} 財報前預告 — {rec['date']}", color=0xF39C12)
    if im:
        risk = (rec.get("value") or 0) * im["move_pct"] / 100
        e.description = (f"選擇權隱含波動 **±{im['move_pct']:.1f}%**（{im['expiry']} 到期、履約 {f(im['strike'],0)} 跨式 ${f(im['straddle'],2)}）\n"
                         f"你的部位 ${f(rec.get('value'),0)}（{rec.get('shares') or '—'} 股）→ 隱含單次風險 **±${f(risk,0)}**")
    else:
        e.description = "選擇權隱含波動：資料缺"
    return footer(e, engine)
