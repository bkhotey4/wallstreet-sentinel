"""Delivery layer: sends each view as PPT-style slides (default) or classic
embeds, to an interaction or a channel/DM. Falls back to embeds if slide
rendering fails, so nothing is ever lost."""
from __future__ import annotations

import asyncio
import io
import logging
from typing import Callable, List, Optional, Sequence, Union

import discord

from ..config import SETTINGS
from .. import store
from . import embeds as E

log = logging.getLogger(__name__)


def style() -> str:
    return store.kv_get("style") or SETTINGS.get("display", {}).get("mode", "slides")


async def _send(dest, content: Optional[str] = None, **kw):
    if isinstance(dest, discord.Interaction):
        try:
            return await dest.followup.send(content=content, **kw)
        except (discord.NotFound, discord.HTTPException) as e:
            # interaction token expired (>15 min) or webhook error → post to the same channel / DM instead
            log.warning("followup failed (%s) → falling back to channel", e)
            ch = dest.channel if dest.channel is not None else await dest.user.create_dm()
            dest = ch
            for f in kw.get("files") or []:
                try:
                    f.reset()                                  # rewind file buffers consumed by the failed attempt
                except Exception:  # noqa: BLE001
                    pass
    try:
        return await dest.send(content=content, **kw)
    except discord.Forbidden:
        log.warning("no permission to send to %s", dest)
    except Exception as e:  # noqa: BLE001
        log.warning("send failed to %s: %s", dest, e)


async def send_pngs(dest, pngs: Sequence[bytes], content: Optional[str] = None) -> None:
    for i in range(0, len(pngs), 10):
        files = [discord.File(io.BytesIO(b), filename=f"sentinel_{i + j + 1:02d}.png")
                 for j, b in enumerate(pngs[i:i + 10])]
        await _send(dest, content if i == 0 else None, files=files)


async def deliver(dest, *, slides: Optional[Callable[[], List[bytes]]] = None,
                  embeds: Optional[Callable[[], Union[discord.Embed, List[discord.Embed]]]] = None,
                  text: Optional[str] = None, title: str = "AI 研判", engine_name: str = "",
                  content: Optional[str] = None) -> None:
    """Render and send. `text` = AI markdown (becomes slides, or chunked text in classic mode)."""
    if style() == "slides" and (slides or text):
        try:
            from . import slides as S
            pngs: List[bytes] = []
            if slides:
                pngs += await asyncio.to_thread(slides)
            if text:
                pngs += await asyncio.to_thread(S.deck_text, title, text, engine_name)
            if pngs:
                await send_pngs(dest, pngs, content)
                return
        except Exception:  # noqa: BLE001
            log.exception("slide rendering failed → falling back to embeds")
    if embeds:
        em = embeds()
        em = em if isinstance(em, list) else [em]
        for i in range(0, len(em), 10):
            await _send(dest, content if i == 0 else None, embeds=em[i:i + 10])
        content = None
    if text:
        head = f"**🧠 {title}**（{engine_name}）\n" if engine_name else ""
        if content:                                          # never glue content onto a 1900-char chunk
            await _send(dest, content[:2000])
        for part in E.chunks(head + text):
            await _send(dest, part)
    elif content and not embeds:
        await _send(dest, content)


# ---------------------------------------------------------------- extra view decks
def v_market_group(engine, group: str) -> List[bytes]:
    from . import slides as S
    names = SETTINGS.names()
    items = []
    for r in engine.market.returns_table(SETTINGS.group(group)):
        sig = r.get("sigma")
        flag = f"  {sig:+.1f}σ" if sig is not None and abs(sig) >= 2 else ""
        ser = engine.market.series(r["ticker"])
        items.append((names.get(r["ticker"], r["ticker"]), S.fmt(r["price"], 2),
                      f"{S.fmt(r['d1'], 2, pct=True, sign=True)}  月 {S.fmt(r.get('m1'), 1, pct=True, sign=True)}{flag}",
                      S.chg_color(r["ticker"], r["d1"]), [float(x) for x in ser.iloc[-23:].values] if len(ser) >= 5 else None))
    return S.deck_tiles(E.GROUP_TITLES.get(group, group).split(" ", 1)[-1], items,
                        "每格：最新價 ／ 今日漲跌 ／ 近一個月漲跌（σ = 今日波動是平常的幾倍）")


def v_macro(engine) -> List[bytes]:
    from . import slides as S
    rg = engine.regime or {}
    out = S.deck_kpis("總經情勢", [
        ("總經象限", (rg.get("quadrant") or "—").split(" ")[0], S.PURPLE),
        ("成長動能 z", S.fmt(rg.get("growth_z"), 2), S.pn(rg.get("growth_z"))),
        ("通膨動能 z", S.fmt(rg.get("inflation_z"), 2), S.pn(-(rg.get("inflation_z") or 0))),
        ("風險偏好", (rg.get("risk_mode") or "—").split(" ")[0], S.ACCENT)],
        [rg.get("playbook", ""),
         f"聯準會淨流動性：{S.fmt(rg.get('net_liquidity_bn'), 0)} 十億美元，13 週變化 {S.fmt(rg.get('net_liquidity_chg_13w_bn'), 0, sign=True)}（{rg.get('liquidity_mode', '需要 FRED 金鑰')}）"])
    rows = []
    for sid, name in SETTINGS.get("fred_series", {}).items():
        x = engine.fred.latest(sid)
        if x:
            pc = x.get("pctile_3y")
            rows.append([(name, S.TEXT), (S.fmt(x["value"], 2), S.TEXT), (S.fmt(x["chg_1m"], 2, sign=True), S.MUTED),
                         (S.fmt(x["chg_1y"], 2, sign=True), S.MUTED),
                         (S.fmt(pc, 0), S.RED if (pc or 0) > 80 else S.TEXT), (x["date"][5:], S.MUTED)])
    if rows:
        out += S.deck_table("FRED 總經 / 信用 / 流動性", ["指標", "最新", "1個月變化", "1年變化", "3年百分位", "日期"],
                            rows, [0.34, 0.13, 0.14, 0.13, 0.14, 0.12], size=34, per_page=11)
    else:
        out += S.deck_kpis("FRED 資料", [("狀態", "尚未取得", S.ORANGE)],
                           ["FRED 在你的網路上連線逾時。請到 fred.stlouisfed.org 申請免費 API 金鑰，填入 .env 的 FRED_API_KEY。"])
    return out


def v_gamma(engine) -> List[bytes]:
    from . import slides as S
    op = engine.options.spx or {}
    gex = op.get("gex_usd_bn_per_1pct")
    return S.deck_kpis("SPX 選擇權造市商部位（Gamma）", [
        ("SPX 現價", S.fmt(op.get("spot"), 0), S.TEXT),
        ("零 Gamma 翻轉點", S.fmt(op.get("zero_gamma"), 0), S.YELLOW),
        ("現價相對翻轉點", S.fmt(op.get("spot_vs_flip_pct"), 2, pct=True, sign=True), S.pn(op.get("spot_vs_flip_pct"))),
        ("GEX（十億美元/1%）", S.fmt(gex, 2, sign=True), S.pn(gex)),
        ("Call 牆（壓力）", S.fmt(op.get("call_wall"), 0), S.RED),
        ("Put 牆（支撐）", S.fmt(op.get("put_wall"), 0), S.GREEN),
        ("Put/Call 未平倉比", S.fmt(op.get("put_call_oi"), 2), S.TEXT),
        ("Put/Call 成交比", S.fmt(op.get("put_call_volume"), 2), S.TEXT)],
        ["正 Gamma：造市商逆勢避險，波動被壓抑；負 Gamma（現價低於翻轉點）：造市商順勢追殺，波動放大。",
         "資料來源 CBOE 延遲報價，只計 60 天內到期合約。"] if op else ["CBOE 資料載入中或失敗。"])


def v_news(engine, query=None, latest=False) -> List[bytes]:
    from . import slides as S
    items = engine.news.latest(12) if latest else engine.news.top(12, query)
    md = "\n".join(f"- 【風險 {n.score}】{n.title}（{n.source.split('/')[0]}）" if n.score else f"- {n.title}（{n.source.split('/')[0]}）"
                   for n in items) or "暫無資料"
    return S.deck_text("全球金融情報流" + (f"：{query}" if query else ""), md)


def v_calendar(engine) -> List[bytes]:
    from . import slides as S
    kind = {"fomc": ("FOMC 利率決議", S.RED), "macro": ("總經數據", S.YELLOW), "earnings": ("持股財報", S.ACCENT),
            "liquidity": ("流動性事件", S.PURPLE)}
    rows = [[(ev["date"], S.TEXT), (kind.get(ev["type"], ("", S.TEXT))[0], kind.get(ev["type"], ("", S.TEXT))[1]),
             (ev["event"], S.TEXT)] for ev in engine.calendar.upcoming(14)]
    if not rows:
        rows = [[("—", S.MUTED), ("—", S.MUTED), ("暫無事件（總經行事曆需要 FRED 金鑰）", S.MUTED)]]
    return S.deck_table("未來 14 天關鍵事件", ["日期", "類型", "事件"], rows, [0.2, 0.22, 0.58], size=38, per_page=10)


def v_quote(t: str, name: str, st: dict, info: dict) -> List[bytes]:
    from . import slides as S
    notes = []
    if info:
        keep = [("sector", "產業"), ("forwardPE", "預估本益比"), ("trailingPE", "本益比"), ("marketCap", "市值"),
                ("targetMeanPrice", "分析師目標價"), ("recommendationKey", "評等"), ("shortPercentOfFloat", "空單比例")]
        parts = []
        for k, lab in keep:
            v = info.get(k)
            if v is None:
                continue
            if k == "marketCap":
                v = f"{v/1e9:,.0f} 十億美元"
            elif isinstance(v, float):
                v = f"{v*100:.1f}%" if k == "shortPercentOfFloat" else f"{v:,.2f}"
            parts.append(f"{lab} {v}")
        if parts:
            notes.append("　·　".join(parts))
    return S.deck_kpis(f"{name}（{t}）", [
        ("最新價", S.fmt(st["price"], 2), S.TEXT),
        ("今日", S.fmt(st["d1"], 2, pct=True, sign=True), S.pn(st["d1"])),
        ("近 3 個月", S.fmt(st.get("3M"), 1, pct=True, sign=True), S.pn(st.get("3M"))),
        ("距 52 週高點", S.fmt(st["from_52w_high"], 1, pct=True), S.pn(st["from_52w_high"])),
        ("相對 200 日線", S.fmt(st.get("vs_ma200"), 1, pct=True, sign=True), S.pn(st.get("vs_ma200"))),
        ("RSI(14)", S.fmt(st["rsi14"], 0), S.RED if st["rsi14"] > 70 else S.GREEN if st["rsi14"] < 30 else S.TEXT),
        ("20 日年化波動", S.fmt(st["vol20_ann"], 0, pct=True), S.TEXT),
        ("對標普 β", S.fmt(st.get("beta_1y"), 2), S.TEXT)], notes)


def v_earnings_preview(engine, rec: dict) -> List[bytes]:
    from . import slides as S
    im = rec.get("implied") or {}
    risk = (rec.get("value") or 0) * im.get("move_pct", 0) / 100 if im else None
    return S.deck_kpis(f"{rec['ticker']} 財報前預告", [
        ("公布日", rec["date"], S.TEXT),
        ("選擇權隱含波動", f"±{im['move_pct']:.1f}%" if im else "—", S.ORANGE),
        ("你的部位", S.fmt(rec.get("value"), 0, money=True), S.TEXT),
        ("隱含單次風險", f"±{S.fmt(risk, 0, money=True)}" if risk else "—", S.RED)],
        [f"以 {im.get('expiry')} 到期、履約 {S.fmt(im.get('strike'), 0)} 的跨式價格推算（市場預期財報後的平均波動幅度）。"] if im else [])
