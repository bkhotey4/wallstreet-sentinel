"""Discord：重要經濟數據公布前提醒、公布後即時解讀、精選池科技／半導體財報結果。

由 Sentinel 的 econ 迴圈每分鐘呼叫一次 tick()。去重用 store.kv（同一事件只推一次，送出成功後才記錄）；機器人停機期間
錯過的事件不補推（排定時間 60 分鐘後就不再當作「即時」；財報結果超過 1 天不補推）。公布監看從排定時間前 70 分鐘開始，
以「實際值出現」為準，所以日曆時間即使差 1 小時（夏令時間切換）也不會漏推。AI 解讀在規則版訊息送出後才產生，最多等 60 秒。"""
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
WATCH_BEFORE_MIN, WATCH_AFTER_MIN = 70, 60     # poll window around the calendar time (covers a 1-hour clock error)
AI_TIMEOUT_S = 60
EARN_STALE_S = 86400                            # earnings results older than this (e.g. after a restart) are not pushed
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


def _fw_txt(m: Optional[Dict]) -> str:
    """'維持不變 70%、升息 1 碼 30%' from a FedWatch meeting row."""
    if not m:
        return ""
    from ..data.fedwatch import outcome_label
    items = sorted(((int(k), v) for k, v in m["probs"].items()), key=lambda kv: -kv[1])
    return "、".join(f"{outcome_label(k)[0]} {v * 100:.0f}%" for k, v in items) + f"（會後隱含利率 {m['rate_after']:.2f}%）"


def _fwd_txt(e: Dict, d: Optional[str]) -> str:
    """What followed past releases with the same outcome (Nasdaq-100 +5 / +20 sessions, Taiwan next session)."""
    x = (((e.get("stats") or {}).get("by") or {}).get(d) or {}).get("fwd") or {}
    f = lambda v, n=1: "—" if v is None else f"{v:+.{n}f}%"  # noqa: E731
    f5, f20 = (x.get("f5") or {}).get("^NDX"), (x.get("f20") or {}).get("^NDX")
    if f5 is None and f20 is None and x.get("tw") is None:
        return ""
    return (f"台股隔日平均 {f(x.get('tw'), 2)}；那指之後 5 個交易日平均 {f(f5)}、20 個交易日平均 {f(f20)}"
            f"（{x.get('n20', 0)} 次，樣本少只是參考）")


def reminder_embed(e: Dict) -> discord.Embed:
    em = discord.Embed(title=f"⏰ {e['zh']}：台北 {e.get('tpe', '')} 公布", color=0x3498DB,
                       description=f"美東 {e['date']} {e.get('et', '')}｜重要度 {'★' * e['imp']}" + ("｜含點陣圖" if e.get("sep") else ""))
    em.add_field(name="預期與前值", value=_rows_txt(e, False)[:1024], inline=False)
    if e.get("fw"):
        em.add_field(name="期貨隱含機率（CME FedWatch 算法）", value=_fw_txt(e["fw"])[:1024], inline=False)
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
    fw = _fwd_txt(e, d)
    if fw:
        em.add_field(name="過去同類結果之後", value=fw[:1024], inline=False)
    if e.get("fw_pre"):
        em.add_field(name="會前期貨隱含", value=_fw_txt(e["fw_pre"])[:1024], inline=False)
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


def verdict_embed(r: Dict) -> discord.Embed:
    """財報結論 — sent once the two-session price window has closed."""
    from ..analytics.earn_verdict import RES
    res = r.get("result")
    color = 0x2FBF71 if (r.get("react") or 0) > 0 else 0xE74C3C if (r.get("react") or 0) < 0 else 0x95A5A6
    em = discord.Embed(title=f"🧾 {r['name']}（{r['sym']}）財報結論：{RES[res][0] if res else '—'}，兩日股價 {r['react']:+.1f}%",
                       color=color, description=r["verdict"]["zh"][:2000])
    rel = r.get("release") or {}
    if rel.get("lines"):
        em.add_field(name="財報重點（公司 SEC 文件）", value="\n".join(rel["lines"])[:1024], inline=False)
    if (rel.get("ai") or {}).get("text"):
        em.add_field(name="🧠 AI 重點整理（只讀財報原文）", value=rel["ai"]["text"][:1024], inline=False)
    if r.get("impact"):
        em.add_field(name="歷史影響統計", value="\n".join(r["impact"])[:1024], inline=False)
    pe = r.get("peers")
    if pe:
        em.add_field(name=f"同族群（{pe['theme']}）波動最大", value="、".join(f"{n} {x:+.1f}%" for _s, n, x in pe["top"])[:1024], inline=False)
    em.set_footer(text="由數據組成：EPS 對預期、兩日股價、選擇權事前預期、族群與台股、過去財報後走勢｜指引不在數據內｜不構成投資建議")
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


def ai_embed(e: Dict, text: str) -> discord.Embed:
    em = discord.Embed(title=f"🧠 {e['zh']}：AI 解讀", color=COL.get(e.get("dir"), 0x3498DB), description=text[:3000])
    em.set_footer(text="AI 依公布數字與規則劇本撰寫，僅供參考｜不構成投資建議")
    return em


async def _send(bot, em: discord.Embed) -> bool:
    """True when at least one destination got the message (or there is none to send to)."""
    from . import present as P
    targets = await bot._targets("alerts")
    ok = not targets
    for t in targets:
        try:
            await P.deliver(t, embeds=lambda: em)
            ok = True
        except Exception:  # noqa: BLE001
            log.warning("econ push to %s failed", t, exc_info=True)
    return ok


def _report_time(d: str, tm: str) -> datetime:
    from zoneinfo import ZoneInfo
    hh, mm = {"pre": (8, 0), "after": (16, 15)}.get(tm, (16, 45))
    dd = date.fromisoformat(d)
    return datetime(dd.year, dd.month, dd.day, hh, mm, tzinfo=ZoneInfo("America/New_York"))


def _passed(d: str, tm: str, now: datetime) -> bool:
    return now >= _report_time(d, tm)


async def tick(bot, now: Optional[datetime] = None) -> None:
    eng = bot.engine
    import time as _clock                              # (not `_t`: that name is the time-parse helper below)
    if not getattr(eng, "full_ready", False) and _clock.time() - getattr(bot, "_started", _clock.time()) < 900:
        return                                            # phase 2 still loading right after a restart (15-min cap)
    c = EC.cfg()
    ev = getattr(eng, "econ_view", None) or {}
    now = now or datetime.now(timezone.utc)
    min_imp, lead = int(c.get("push_min_imp", 2)), float(c.get("remind_hours", 3))
    if ev.get("available"):
        for e in ev["events"]:
            if e["released"] or e["imp"] < min_imp or not e.get("utc"):
                continue
            dh = (_t(e["utc"]) - now).total_seconds() / 3600
            k = f"econ_rem:{e['id']}"
            if 0 < dh <= lead and not store.kv_get(k):
                if await _send(bot, reminder_embed(e)):
                    store.kv_set(k, True)
        watch = {e["id"]: e["date"] for e in ev["events"] if e["imp"] >= min_imp and e.get("utc") and e.get("rows")
                 and -WATCH_BEFORE_MIN <= (now - _t(e["utc"])).total_seconds() / 60 <= WATCH_AFTER_MIN
                 and not store.kv_get(f"econ_res:{e['id']}")}
        due = sorted(set(watch.values()))
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
            sent = []
            for e in eng.econ_view["events"]:          # 1) the rule-based result first — numbers can't wait for a model
                k = f"econ_res:{e['id']}"
                if e["id"] in watch and e["released"] and e["imp"] >= min_imp and e.get("rows") and not store.kv_get(k):
                    if await _send(bot, result_embed(e, eng.market.quotes, None)):
                        store.kv_set(k, True)          # only after a successful send → a failed send is retried next minute
                        sent.append(e)
            if sent and c.get("ai_on_release", True):  # 2) then the AI note, bounded so the minute loop keeps running
                cache = EA.load()
                for e in sent:
                    try:
                        got = await asyncio.wait_for(EA._gen(e["id"], EA.event_prompt(e), cache), AI_TIMEOUT_S)
                    except asyncio.TimeoutError:
                        log.info("econ AI note for %s timed out → skipped", e["id"])
                        continue
                    except Exception:  # noqa: BLE001
                        log.exception("econ AI note failed")
                        continue
                    if got and got[0]:
                        await _send(bot, ai_embed(e, got[0]))
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
                if (now - _report_time(d, r.get("time", ""))).total_seconds() > EARN_STALE_S:
                    store.kv_set(k, True)              # e.g. first run after a restart: old news, remember silently
                    continue
                if not await _send(bot, earnings_embed(r, rows_by.get(r["sym"]))):
                    continue
                store.kv_set(k, True)
                try:
                    ed.surprise = await ED.refresh_surprises([r["sym"]], {r["sym"]: d}, 20)
                except Exception:  # noqa: BLE001
                    pass
    if time.time() - float(store.kv_get("earn_rel_poll", 0) or 0) > 1200:
        store.kv_set("earn_rel_poll", time.time())
        try:
            from ..analytics import earn_verdict as EVD
            from ..data import earn_release as ER
            lo3 = (today - timedelta(days=3)).isoformat()
            want = [(s, d) for s, d in EVD.release_targets(eng) if d >= lo3]
            if want and await ER.refresh(eng, want, budget_s=60):
                eng.earn_verdict = await asyncio.to_thread(EVD.build, eng)
        except Exception:  # noqa: BLE001
            log.exception("earnings release refresh failed")
    # the two-session reaction window closed → one 財報結論 per report (curated tech names, last 3 US days only)
    lo = (today - timedelta(days=3)).isoformat()
    for r in (getattr(eng, "earn_verdict", None) or {}).get("rows", []):
        if r["sym"] not in tech or r.get("status") != "reported" or r.get("react") is None or r["date"] < lo:
            continue
        k = f"earn_concl:{r['sym']}:{r['date']}"
        if not store.kv_get(k) and await _send(bot, verdict_embed(r)):
            store.kv_set(k, True)
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
            if (today - date.fromisoformat(end)).days > 120 or await _send(bot, detail_embed(r)):
                store.kv_set(k, end)


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
