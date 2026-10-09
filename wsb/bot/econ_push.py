"""Discord：重要經濟數據公布前提醒、公布後即時解讀、精選池科技／半導體財報結果。

由 Sentinel 的 econ 迴圈每分鐘呼叫一次 tick()。去重用 store.kv（同一事件只推一次）；機器人停機期間錯過的事件不補推
（超過 50 分鐘的公布就不再當作「即時」）。"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

import discord

from .. import store
from ..ai import econ_ai as EA
from ..analytics import macro_events as ME
from ..data import earnings_data as ED
from ..data import econcal as EC

log = logging.getLogger(__name__)
FUT = [("ES=F", "標普期"), ("NQ=F", "那指期"), ("^TNX", "10 年殖利率"), ("DX-Y.NYB", "美元指數")]
COL = {"hot": 0xE74C3C, "cool": 0x2FBF71, "inline": 0x95A5A6, None: 0x3498DB}


def _t(utc: str) -> datetime:
    return datetime.fromisoformat(utc.replace("Z", "+00:00"))


def _rows_txt(e: Dict, with_actual: bool) -> str:
    out = []
    for r in e.get("rows", [])[:6]:
        a = f"**{r['actual']}**　" if with_actual and r.get("actual") else ""
        out.append(f"{r['label']}：{a}預期 {r['cons'] or '—'}｜前值 {r['prev'] or '—'}")
    return "\n".join(out) or "（這個事件沒有數字，重點在內容與語氣）"


def _hist_txt(e: Dict, d: Optional[str] = None) -> str:
    st = e.get("stats") or {}
    by = st.get("by") or {}
    lab = {"hot": "高於預期／偏鷹", "inline": "符合預期", "cool": "低於預期／偏鴿"}
    keys = [d] if d else ["hot", "inline", "cool"]
    L = []
    for k in keys:
        x = by.get(k)
        if not x:
            continue
        f = lambda v, n=2: "—" if v is None else f"{v:+.{n}f}"  # noqa: E731
        L.append(f"{lab[k]}（{x['n']} 次）：那指 {f(x.get('^NDX'))}%、費半 {f(x.get('^SOX'))}%、10 年 {f(x.get('^TNX'), 1)}bp")
    return ("過去約兩年當天平均：\n" + "\n".join(L)) if L else ""


def reminder_embed(e: Dict) -> discord.Embed:
    em = discord.Embed(title=f"⏰ {e['zh']}：台北 {e.get('tpe', '')} 公布", color=0x3498DB,
                       description=f"美東 {e['date']} {e.get('et', '')}｜重要度 {'★' * e['imp']}" + ("｜含點陣圖" if e.get("sep") else ""))
    em.add_field(name="預期與前值", value=_rows_txt(e, False)[:1024], inline=False)
    sc = e.get("scen") or {}
    if sc:
        em.add_field(name="為什麼重要", value=sc["why"]["zh"][:1024], inline=False)
        for d, nm in (("hot", "若高於預期／偏鷹"), ("inline", "若符合預期"), ("cool", "若低於預期／偏鴿")):
            em.add_field(name=nm, value=sc[d]["zh"][:1024], inline=False)
    h = _hist_txt(e)
    if h:
        em.add_field(name="歷史反應", value=h[:1024], inline=False)
    if e.get("ctx"):
        em.add_field(name="目前背景", value=e["ctx"][:1024], inline=False)
    em.set_footer(text="規則劇本是判斷框架，不是預測；不構成投資建議")
    return em


def result_embed(e: Dict, quotes: Dict, ai: Optional[str]) -> discord.Embed:
    d = e.get("dir")
    lab = (e.get("dir_label") or ("沒有預期值可比較", ""))[0]
    em = discord.Embed(title=f"📢 {e['zh']} 公布：{lab}", color=COL.get(d, 0x3498DB), description=_rows_txt(e, True)[:2000])
    sc = e.get("scen") or {}
    if sc and d:
        em.add_field(name="對應劇本", value=sc[d]["zh"][:1024], inline=False)
    mv = []
    for t, nm in FUT:
        q = quotes.get(t) or {}
        if q.get("chg_pct") is not None and q["chg_pct"] == q["chg_pct"]:
            mv.append(f"{nm} {q['chg_pct']:+.2f}%")
    if mv:
        em.add_field(name="市場即時（相對前一日收盤）", value="　".join(mv)[:1024], inline=False)
    h = _hist_txt(e, d)
    if h:
        em.add_field(name="過去同類結果", value=h[:1024], inline=False)
    if ai:
        em.add_field(name="🧠 AI 解讀", value=ai[:1024], inline=False)
    if sc:
        em.add_field(name="接下來要看", value=sc["watch"]["zh"][:1024], inline=False)
    em.set_footer(text="資料：Nasdaq 經濟日曆｜不構成投資建議")
    return em


def earnings_embed(row: Dict, tr: Optional[Dict]) -> discord.Embed:
    s = row.get("surprise")
    head = f"EPS {row['eps']:.2f} vs 預期 {row['eps_f']:.2f}" if row.get("eps") is not None and row.get("eps_f") is not None else f"EPS {row.get('eps')}"
    color = 0x2FBF71 if (s or 0) > 0 else 0xE74C3C if (s or 0) < 0 else 0x95A5A6
    name = (tr or {}).get("name") or row.get("name") or row["sym"]
    em = discord.Embed(title=f"📊 {name}（{row['sym']}）財報：{head}" + (f"（{s:+.1f}%）" if s is not None else ""), color=color,
                       description={"pre": "盤前公布", "after": "盤後公布"}.get(row.get("time", ""), "") + f"｜財季 {row.get('fq', '')}")
    if tr:
        su = tr["s"]
        if su.get("n"):
            em.add_field(name="過去紀錄", value=f"前 {su['n']} 季有 {su['beats']} 季優於預期（平均 {su['avg']:+.1f}%）"
                         + (f"；財報前後兩日平均波動 ±{su['react_avg']:.1f}%" if su.get("react_avg") is not None else ""), inline=False)
        if tr.get("rev_yoy") is not None:
            em.add_field(name=f"上一份季報（季末 {tr.get('end')}）", value=tr.get("verdict", "")[:1024], inline=False)
    em.add_field(name="接下來", value="營收、毛利率等細節會在 SEC 季報（10-Q）出來後自動更新到網站「科技財報」頁；股價反應用 /stock 查。", inline=False)
    em.set_footer(text="資料：Nasdaq（Zacks 彙整預期）｜EPS 口徑可能與公司公布的調整後 EPS 不同｜不構成投資建議")
    return em


def detail_embed(r: Dict) -> discord.Embed:
    em = discord.Embed(title=f"🧾 {r['name']}（{r['sym']}）季報數字更新：季末 {r.get('end')}", color=0x8E44AD, description=r.get("verdict", "")[:2000])
    tg = "、".join(t for t, _ in r.get("tags", []))
    if tg:
        em.add_field(name="規則標籤", value=tg[:1024], inline=False)
    if r.get("score") is not None:
        em.add_field(name="財報動能分數", value=f"{r['score']:.0f}（精選池科技／半導體內的百分位綜合）", inline=False)
    em.set_footer(text="資料：SEC XBRL｜不構成投資建議")
    return em


async def _send(bot, em: discord.Embed) -> None:
    from . import present as P
    for t in await bot._targets("alerts"):
        await P.deliver(t, embeds=lambda: em)


def _passed(d: str, tm: str, now: datetime) -> bool:
    from zoneinfo import ZoneInfo
    hh, mm = {"pre": (8, 0), "after": (16, 15)}.get(tm, (16, 45))
    dd = date.fromisoformat(d)
    return now >= datetime(dd.year, dd.month, dd.day, hh, mm, tzinfo=ZoneInfo("America/New_York"))


async def tick(bot) -> None:
    eng = bot.engine
    if not getattr(eng, "full_ready", False):
        return
    c = EC.cfg()
    ev = getattr(eng, "econ_view", None) or {}
    now = datetime.now(timezone.utc)
    min_imp, lead = int(c.get("push_min_imp", 2)), float(c.get("remind_hours", 3))
    if ev.get("available"):
        for e in ev["events"]:
            if e["released"] or e["imp"] < min_imp or not e.get("utc"):
                continue
            dh = (_t(e["utc"]) - now).total_seconds() / 3600
            k = f"econ_rem:{e['id']}"
            if 0 < dh <= lead and not store.kv_get(k):
                store.kv_set(k, True)
                await _send(bot, reminder_embed(e))
        due = sorted({e["date"] for e in ev["events"] if e["imp"] >= min_imp and e.get("utc") and e.get("rows")
                      and -1 <= (now - _t(e["utc"])).total_seconds() / 60 <= 50 and not store.kv_get(f"econ_res:{e['id']}")})
        if due:
            for d in due:
                try:
                    await eng.econ.poll_day(date.fromisoformat(d))
                except Exception as ex:  # noqa: BLE001
                    log.info("econ poll %s: %s", d, ex)
            try:
                eng.econ_view = await asyncio.to_thread(ME.build, eng)
            except Exception:  # noqa: BLE001
                log.exception("econ view rebuild failed")
                return
            for e in eng.econ_view["events"]:
                k = f"econ_res:{e['id']}"
                if e["date"] in due and e["released"] and e["imp"] >= min_imp and e.get("rows") and not store.kv_get(k):
                    store.kv_set(k, True)
                    ai = None
                    if c.get("ai_on_release", True):
                        try:
                            cache = EA.load()
                            got = await EA._gen(e["id"], EA.event_prompt(e), cache)
                            ai = got[0] if got else None
                        except Exception:  # noqa: BLE001
                            log.exception("econ AI note failed")
                    await _send(bot, result_embed(e, eng.market.quotes, ai))
    await earnings_tick(bot, now)


async def earnings_tick(bot, now: datetime) -> None:
    eng = bot.engine
    if not ED.cfg().get("push_results", True):
        return
    ed = eng.earnings
    tech = set(eng.tech_symbols())
    rows_by = {r["sym"]: r for r in (getattr(eng, "techearn", None) or {}).get("rows", [])}
    today = EC.us_today()
    for d in ((today - timedelta(days=1)).isoformat(), today.isoformat()):
        rows = ((ed.days or {}).get(d) or {}).get("rows", [])
        pend = [r for r in rows if r["sym"] in tech and not store.kv_get(f"earn_res:{r['sym']}:{d}")]
        if not pend or not any(_passed(d, r["time"], now) for r in pend):
            continue
        last = float(store.kv_get(f"earn_poll:{d}", 0) or 0)
        if time.time() - last < 600:
            continue
        store.kv_set(f"earn_poll:{d}", time.time())
        try:
            rows = await ed.poll_day(date.fromisoformat(d))
        except Exception as ex:  # noqa: BLE001
            log.info("earnings poll %s: %s", d, ex)
            continue
        for r in rows:
            k = f"earn_res:{r['sym']}:{d}"
            if r["sym"] in tech and r.get("eps") is not None and not store.kv_get(k):
                store.kv_set(k, True)
                await _send(bot, earnings_embed(r, rows_by.get(r["sym"])))
                try:
                    ed.surprise = await ED.refresh_surprises([r["sym"]], {r["sym"]: d}, 20)
                except Exception:  # noqa: BLE001
                    pass
    # SEC quarterly numbers arrived for a curated tech name → one detail push per new quarter
    for s, r in rows_by.items():
        end = r.get("end")
        if not end:
            continue
        k = f"earn_q:{s}"
        seen = store.kv_get(k)
        if seen is None:
            store.kv_set(k, end)                       # first sight: remember silently
        elif end > seen:
            store.kv_set(k, end)
            if (today - date.fromisoformat(end)).days <= 120:
                await _send(bot, detail_embed(r))


def econ_week_embed(ev: Dict) -> discord.Embed:
    today = ev["asof"]
    lim = (date.fromisoformat(today) + timedelta(days=7)).isoformat()
    up = [e for e in ev["events"] if not e["released"] and e["imp"] >= 2 and today <= e["date"] <= lim]
    done = [e for e in ev["events"] if e["released"] and e["imp"] >= 2 and e.get("rows")][-6:]
    em = discord.Embed(title="🗓️ 未來 7 天重要經濟數據", color=0x3498DB, description="時間為台北時間；★ 越多越重要｜/econ 只列 ★★ 以上")
    for e in up[:12]:
        p = e["rows"][0] if e.get("rows") else {}
        em.add_field(name=f"{e['date'][5:]}（台北 {e.get('tpe', '')}）{'★' * e['imp']} {e['zh']}",
                     value=(f"{p.get('label', '')}：預期 {p.get('cons') or '—'}｜前值 {p.get('prev') or '—'}" if p else "看內容與語氣")[:1024], inline=False)
    if done:
        em.add_field(name="最近公布", value="\n".join(
            f"{e['date'][5:]} {e['zh']}：{e['rows'][0]['actual']}（預期 {e['rows'][0]['cons'] or '—'}）→ {(e.get('dir_label') or ('—',))[0]}" for e in done)[:1024], inline=False)
    nx = ev.get("next_fomc")
    if nx:
        em.set_footer(text=f"下次 FOMC：{nx['date']}（台北 {nx.get('tpe', '')}）｜網站「財經日曆」頁有完整影響劇本")
    return em


def tech_embed(r: Dict) -> discord.Embed:
    em = discord.Embed(title=f"🧾 {r['name']}（{r['sym']}）財報分析", color=0x8E44AD, description=r.get("verdict", "")[:2000] or "財報數字尚未取得")
    f = lambda v, n=1, suf="": "—" if v is None else f"{v:,.{n}f}{suf}"  # noqa: E731
    em.add_field(name=f"最新一季（季末 {r.get('end') or '—'}）",
                 value=(f"營收 {f((r.get('rev') or 0) / 1e9, 2)} 十億美元｜年增 {f(r.get('rev_yoy'), 1, '%')}｜季增 {f(r.get('rev_qoq'), 1, '%')}\n"
                        f"毛利率 {f(r.get('gm'), 1, '%')}（年變化 {f(r.get('gm_yoy'), 1, 'pp')}）｜營益率 {f(r.get('om'), 1, '%')}\n"
                        f"EPS {f(r.get('eps'), 2)}（年增 {f(r.get('eps_yoy'), 1, '%')}）｜研發占營收 {f(r.get('rnd'), 1, '%')}"), inline=False)
    su = r["s"]
    if su.get("rows"):
        em.add_field(name="EPS 實際 vs 預期", value="\n".join(f"{x['fq']}：{x['eps']} vs {x['cons']}（{x['surp']:+.1f}%）" for x in su["rows"])[:1024], inline=False)
    if r.get("next"):
        n = r["next"]
        em.add_field(name="下次財報", value=f"{n['date']}（{ {'pre': '盤前', 'after': '盤後'}.get(n['time'], '時間未定') }）EPS 預期 {n['eps_f']}"
                     + (f"，較去年同期 {n['g']:+.0f}%" if n.get("g") is not None else ""), inline=False)
    tg = "、".join(t for t, _ in r.get("tags", []))
    if tg:
        em.add_field(name="規則標籤", value=tg[:1024], inline=False)
    if r.get("ai"):
        em.add_field(name="🧠 AI 解讀", value=r["ai"]["text"][:1024], inline=False)
    em.set_footer(text=f"財報動能分數 {f(r.get('score'), 0)}｜資料：SEC XBRL、Nasdaq｜不構成投資建議")
    return em
