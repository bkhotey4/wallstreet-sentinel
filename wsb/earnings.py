"""Earnings-season automation for portfolio holdings.

* Preview (1–2 days before): options-implied move, dollar risk on the
  position, AI checklist of what matters.
* Post-release: detect the SEC filing (8-K Item 2.02 / 6-K results), pull the
  press release, combine with actual price reaction, implied move and
  analyst EPS estimate/surprise, and have the AI write a verdict."""
from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from .ai import context, llm, prompts
from .data import sec as secmod
from .data.options import fetch_chain, implied_move
from . import store

log = logging.getLogger(__name__)


def _position(engine, t: str) -> Dict:
    for p in (engine.portfolio or {}).get("positions", []):
        if p.get("sym") == t:
            return p
    return {}


def _eps_surprise(t: str) -> Dict:
    """Latest reported EPS vs estimate from Yahoo (free, may be missing)."""
    try:
        import yfinance as yf
        df = yf.Ticker(t).get_earnings_dates(limit=6)
        if df is None or df.empty:
            return {}
        df = df.dropna(subset=["Reported EPS"])
        if df.empty:
            return {}
        row = df.iloc[0]
        return {"eps_estimate": row.get("EPS Estimate"), "eps_reported": row.get("Reported EPS"),
                "surprise_pct": row.get("Surprise(%)"), "report_date": str(df.index[0].date())}
    except Exception as e:  # noqa: BLE001
        log.info("eps surprise %s unavailable: %s", t, e)
        return {}


async def upcoming_previews(engine, days: int = 2) -> List[Dict]:
    """Holdings reporting within `days`; computes implied move once per event."""
    out = []
    limit = (date.today() + timedelta(days=days)).isoformat()
    for ev in engine.calendar.upcoming(days + 1):
        t = ev.get("ticker")
        if ev.get("type") != "earnings" or not t or ev["date"] > limit or "." in t:
            continue
        key = f"implied:{t}:{ev['date']}"
        if store.kv_get(key):
            continue
        try:
            chain = await fetch_chain(t)
            im = implied_move(chain, ev["date"])
        except Exception as e:  # noqa: BLE001
            log.warning("implied move %s failed: %s", t, e)
            im = None
        pos = _position(engine, t)
        rec = {"ticker": t, "date": ev["date"], "implied": im, "value": pos.get("value_usd", 0.0),
               "shares": pos.get("shares")}
        store.kv_set(key, rec)
        store.kv_set(f"implied_last:{t}", rec)
        out.append(rec)
    return out


async def preview_text(engine, rec: Dict) -> str:
    im = rec.get("implied")
    if not im:
        return f"{rec['ticker']} 將於 {rec['date']} 公布財報（選擇權隱含波動資料缺）。"
    pack = context.build(engine, "portfolio")
    txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.EARNINGS_PREVIEW.format(
        t=rec["ticker"], date=rec["date"], move=im["move_pct"], expiry=im["expiry"],
        value=rec["value"] or 0, risk=(rec["value"] or 0) * im["move_pct"] / 100), 1200)
    return f"🧠（{name}）\n{txt}"


async def analyze_release(engine, item: Dict) -> str:
    t = item["ticker"]
    try:
        text = await secmod.fetch_press_release(item)
    except Exception as e:  # noqa: BLE001
        log.warning("press release fetch failed %s: %s", t, e)
        text = ""
    q = engine.market.q(t) or {}
    sig = engine.market.sigma_move(t)
    im = (store.kv_get(f"implied_last:{t}") or {}).get("implied")
    eps = await asyncio.to_thread(_eps_surprise, t)
    pos = _position(engine, t)
    facts = [
        f"最新價 {q.get('price')}，今日 {q.get('chg_pct'):+.2f}%（{sig:+.1f}σ）" if q.get("chg_pct") is not None and sig is not None
        else f"最新價 {q.get('price', '資料缺')}（盤後/隔日反應可能尚未反映）",
        f"財報前選擇權隱含波動 ±{im['move_pct']:.1f}%（{im['expiry']} 到期）" if im else "財報前隱含波動：資料缺",
        (f"EPS 實際 {eps.get('eps_reported')} vs 預估 {eps.get('eps_estimate')}，驚喜 {eps.get('surprise_pct')}%（Yahoo，{eps.get('report_date')}）"
         if eps else "分析師 EPS 預估：資料缺"),
        f"SEC 文件：{item['form']} {item.get('items') or ''} {item['url']}",
    ]
    pack = context.build(engine, "portfolio")
    txt, name = await llm.complete(prompts.SYSTEM, pack + "\n\n" + prompts.EARNINGS.format(
        t=t, form=item["form"], date=item["date"], facts="\n".join(facts),
        text=text or "（無法取得新聞稿全文）", shares=pos.get("shares", "—"),
        value=f"{pos.get('value_usd', 0):,.0f}"), 2500)
    return f"## 📑 {t} 財報快評\n" + "\n".join(f"> {x}" for x in facts[:3]) + f"\n\n🧠（{name}）\n{txt}"


async def latest_release(engine, t: str) -> Optional[Dict]:
    """Most recent earnings filing for a ticker (for /earnings)."""
    for it in await engine.sec.fetch(t):             # read-only: doesn't disturb the auto-review pipeline
        if it.get("earnings"):
            return it
    return None
