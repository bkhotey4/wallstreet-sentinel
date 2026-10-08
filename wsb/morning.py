"""Wall Street-style morning meeting & earnings-season board.

morning_call(): gathers overnight moves, sector rotation, biggest σ movers,
today's macro events + major earnings (Nasdaq), runs the AI "morning
meeting host", and returns (facts, ai_text, engine_name) for the slide deck.
earnings_board(): week-ahead major reporters + last week's beat/miss and
price reactions, with an AI summary."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

from .ai import context, llm, prompts
from .config import SETTINGS
from .data import street

log = logging.getLogger(__name__)


def movers(engine, n: int = 10) -> List[Dict]:
    names = SETTINGS.names()
    rows = []
    for t in set(names) | set(engine.holding_tickers()):
        sg = engine.market.sigma_move(t)
        q = engine.market.q(t)
        if sg is None or not q or q.get("chg_pct") is None:
            continue
        rows.append({"ticker": t, "name": names.get(t, t), "chg": q["chg_pct"], "sigma": sg, "price": q["price"],
                     "holding": t in engine.holding_tickers()})
    return sorted(rows, key=lambda r: -abs(r["sigma"]))[:n]


def sectors(engine) -> List[Dict]:
    names = SETTINGS.names()
    rows = engine.market.returns_table(SETTINGS.group("sectors"))
    for r in rows:
        r["name"] = names.get(r["ticker"], r["ticker"])
    return sorted(rows, key=lambda r: -(r.get("d1") or -99))


async def morning_call(engine, title: str, session: str) -> Tuple[Dict, str, str]:
    d = street.ny_trade_date()
    try:
        er = street.important(await street.earnings_on(d), engine.holding_tickers())[:10]
    except Exception as e:  # noqa: BLE001
        log.warning("earnings calendar failed: %s", e)
        er = []
    today_macro = [e for e in engine.calendar.events
                   if e["date"] in (d.isoformat(), (d + timedelta(days=1)).isoformat()) and e["type"] != "earnings"]
    mv = movers(engine)
    facts = {"trade_date": d.isoformat(), "earnings": er, "macro": today_macro, "movers": mv,
             "sectors": sectors(engine)}
    extra = [f"美股交易日：{d.isoformat()}（紐約時間）"]
    extra += ["今日重要財報：" + "; ".join(
        f"{r['symbol']} {r['name']}（{r['when']}，EPS 預估 {r['eps_fc']}，去年 {r['eps_ly']}，市值 {((r['mcap'] or 0)/1e9):,.0f}B）"
        for r in er) if er else "今日重要財報：資料缺或無"]
    extra += ["今日/明日總經事件：" + ("; ".join(f"{e['date']} {e['event']}" for e in today_macro) or "無（或需 FRED 金鑰）")]
    extra += ["最大異動（σ）：" + "; ".join(f"{m['name']}({m['ticker']}) {m['chg']:+.2f}% {m['sigma']:+.1f}σ" for m in mv[:8])]
    extra += ["板塊 1 日：" + "; ".join(f"{s['name']} {s.get('d1') or 0:+.2f}%" for s in facts["sectors"])]
    pack = context.build(engine, "us")
    txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.MORNING_CALL.format(
        title=title, session=session, extra="\n".join(extra)), 3500)
    return facts, txt, name


async def earnings_board(engine, private: bool = True) -> Tuple[Dict, str, str]:
    held = engine.holding_tickers() if private else []          # public requests must not reveal which names are held
    ahead = await street.week_ahead(held)
    past = await street.last_week_results(held)
    a_txt = "\n".join(f"{d}: " + ", ".join(f"{r['symbol']}({r['when']}, EPS預估 {r['eps_fc']})" for r in rows)
                      for d, rows in ahead.items() if rows) or "資料缺"
    p_txt = "\n".join(f"{r['symbol']}: 實際 {r.get('eps_act')} vs 預估 {r.get('eps_est')}，驚喜 {r.get('surprise')}%，反應 {r.get('reaction')}%"
                      for r in past) or "資料缺"
    pack = context.build(engine, "us", private=private)
    txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.EARNINGS_WEEK.format(ahead=a_txt, past=p_txt), 2000)
    return {"ahead": ahead, "past": past, "asof": datetime.now().isoformat(timespec="minutes")}, txt, name


def first_section(md: str) -> str:
    """Pull the one-line theme from the AI text for the cover slide."""
    from .bot.slides import parse_sections
    for h, items in parse_sections(md):
        if items and ("主題" in h or not h):
            return " ".join(str(c) for k, c in items if k in ("para", "bullet"))[:80]
    return ""


def today_label() -> str:
    return date.today().strftime("%Y/%m/%d")
