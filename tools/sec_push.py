"""SEC 重大申報 → Discord（獨立小程式，不經過 wsb/bot/app.py，也不需要重啟機器人）。

每次執行：
  1. 名單＝本站追蹤池＋市值 ≥ 1,000 億美元的公司（和網站警報同一份規則，用 SEC 官方 ticker → CIK）
  2. 讀 SEC 最新 8-K（wsb/data/sec_officers.refresh：翻頁到上次看過的地方，第 5.02 項會讀原文判斷離職／任命與職位）
  3. 還沒送過、6 小時內的警報：附上影響估算（標普 500 權重、最常一起動的美股、隔天跟著動的台股，乘上現在的漲跌），
     用同一個機器人身分送到警報頻道（和機器人同一個規則：/setchannel 設的，或 ALERT_CHANNEL_ID）；沒有設頻道就私訊你
     （OWNER_USER_ID）；有頻道時，破產、財報重編這類，或執行長／財務長／董事長離職，另外再私訊一份。
  4. （2026-11-14）同一趟順便做三件事，各自失敗不影響別的：
     ・多家媒體同時報導：/api/news 算好的 bursts，3 家以上才推，公司附影響估算，事件附相關行情現在的漲跌；同一件事 12 小時推一次
     ・台指期夜盤急跌：期交所官方即時報價，跌幅 ≥ 台股平常一天的 2 倍且 ≥ 1.5%（規則同族群急跌）
     ・持股晚報與累積跌幅（tools/holdings_watch.py）：只私訊擁有者
     13D/A（舊的大股東申報更新）只列在網站，不推。
  5. （2026-11-14 第二批）央行非例行動作（/api/news 標 kind=cb 的官方公告）與日圓急升（美元兌日圓一天跌 ≥ 平常 3 倍）；
     離線補課：這支程式停了 1 小時以上再啟動時，補一則「這段時間漏了什麼」（超過 6 小時、原本會被略過的重大申報也列進去）。
送過的記在 data_cache/sec_push.json，不會重送。Windows 工作排程每 3 分鐘跑一次：python -m tools.sec_push
影響估算是過去平均關係的推算，不是預測，也不是投資建議。"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import aiohttp  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.config import ALERT_CHANNEL_ID, DATA_DIR, DISCORD_TOKEN, OWNER_USER_ID  # noqa: E402

log = logging.getLogger("sec_push")
PUSHED = DATA_DIR / "sec_push.json"
MAX_AGE = 6 * 3600
API = "https://discord.com/api/v10"
QUOTE = "https://wallstreet-sentinel.pages.dev/api/quote"


def watch_list() -> Dict[str, list]:
    """{cik: [sym, 中文名]} — the site's alert list, built from local caches (no engine)."""
    from wsb.data import earn_official as EO
    from wsb.data import earnings_data as ED
    from wsb.data.edgar_holdings import _MAP_FILE
    from wsb.data.stocks import universe
    names = (universe().get("us") or {}).get("symbols", {})
    big = EO.universe(ED._load(ED.F_DAYS), [], EO.load().get("known"))
    try:
        tmap = json.loads(_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        tmap = {}
    out: Dict[str, list] = {}
    for s in list(names) + [k for k, v in big.items() if (v.get("mcap") or 0) >= 1e11]:
        cik = (tmap.get(s) or tmap.get(s.replace("-", ".")) or {}).get("cik")
        if cik and str(int(cik)) not in out:
            out[str(int(cik))] = [s, names[s][0] if s in names else (big.get(s) or {}).get("name") or s]
    return out


def severity(a: Dict) -> int:
    from wsb.data.sec_officers import severity as sev
    return sev(a)


def _close() -> pd.DataFrame:
    try:
        cl = pd.read_pickle(DATA_DIR / "stock_prices.pkl")
        return cl if isinstance(cl, pd.DataFrame) else cl.get("close", pd.DataFrame())
    except Exception:  # noqa: BLE001
        return pd.DataFrame()


async def impact(sess: aiohttp.ClientSession, sym: str, zh: str) -> List[str]:
    """Plain lines: the stock's move now × S&P weight, peers' beta, Taiwan next-session beta."""
    from wsb.analytics import news_impact as NI
    from wsb.data.stocks import universe
    allu = {}
    for mk in ("us", "tw"):
        for k, v in ((universe().get(mk) or {}).get("symbols") or {}).items():
            allu[k] = (v[0], v[1] if len(v) > 1 else k, mk)
    cl = _close()
    ret = cl.pct_change(fill_method=None) * 100 if not cl.empty else pd.DataFrame()
    peers = NI.peers(ret, sym, [k for k, v in allu.items() if v[2] == "us"], allu) if not ret.empty else []
    tw = NI.tw_direct(cl, sym, [k for k, v in allu.items() if v[2] == "tw" and k in cl.columns], allu) if not cl.empty else []
    w = ((await NI.spy_weights()).get("w") or {}).get(sym)
    syms = [sym] + [p["sym"] for p in peers]
    mv, ses, q = None, "今天", {}
    try:
        async with sess.get(QUOTE, params={"s": ",".join(syms), "ext": sym}, timeout=aiohttp.ClientTimeout(total=20)) as r:
            q = (await r.json()).get("q") or {}
        o = q.get(sym) or {}
        if isinstance((o.get("ext") or {}).get("chg"), (int, float)):
            mv, ses = o["ext"]["chg"], "盤前" if o["ext"].get("sess") == "pre" else "盤後"
        elif isinstance(o.get("chg"), (int, float)):
            mv = o["chg"]
    except Exception as e:  # noqa: BLE001
        log.info("quote %s: %s", sym, e)
    pc = lambda v, d=1: f"{v:+.{d}f}%"  # noqa: E731
    if mv is None:
        out = [f"{zh} 的即時價格暫時拿不到，下面只列關係："]
    else:
        out = [f"{zh} {ses} **{pc(mv)}**"]
    if w:
        out.append(f"・標普 500：它占 {w:.1f}%" + (f" → 光它本身約讓標普動 {pc(w * mv / 100, 2)}（不含連帶效應）" if mv is not None else ""))
    if peers:
        out.append("・過去 120 個交易日最常一起動的美股：" + "、".join(
            p["zh"] + (f" 約 {pc(p['beta'] * mv)}" if mv is not None else f"（β {p['beta']:.2f}）")
            + (f"（現 {pc(q[p['sym']]['chg'])}）" if isinstance((q.get(p["sym"]) or {}).get("chg"), (int, float)) else "") for p in peers))
    if tw:
        out.append("・台股隔天（樣本外驗證過的連動）：" + "、".join(
            p["zh"] + (f" 約 {pc(p['beta'] * mv)}" if mv is not None else f"（β {p['beta']:.2f}）") for p in tw))
    else:
        out.append("・台股：沒有和它連動夠穩定的台股")
    return out


async def post(sess: aiohttp.ClientSession, channel: str, embed: Dict) -> bool:
    h = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    async with sess.post(f"{API}/channels/{channel}/messages", headers=h, json={"embeds": [embed]},
                         timeout=aiohttp.ClientTimeout(total=20)) as r:
        if r.status >= 300:
            log.warning("discord %s: HTTP %s", channel, r.status)
        return r.status < 300


def alert_channel() -> str:
    """The bot's own rule: the channel set with /setchannel (kept in sentinel.db), else ALERT_CHANNEL_ID."""
    try:
        from wsb import store
        return str(store.kv_get("alerts_channel") or ALERT_CHANNEL_ID or "")
    except Exception:  # noqa: BLE001
        return str(ALERT_CHANNEL_ID or "")


def owner_id() -> str:
    try:
        from wsb import store
        return str(store.kv_get("owner_id") or OWNER_USER_ID or "")
    except Exception:  # noqa: BLE001
        return str(OWNER_USER_ID or "")


async def dm_channel(sess: aiohttp.ClientSession) -> Optional[str]:
    if not owner_id():
        return None
    h = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    async with sess.post(f"{API}/users/@me/channels", headers=h, json={"recipient_id": owner_id()},
                         timeout=aiohttp.ClientTimeout(total=20)) as r:
        return (await r.json()).get("id") if r.status < 300 else None


def embed_of(a: Dict, lines: List[str]) -> Dict:
    return {"title": ("🔴 " + a["t"])[:256], "url": a["url"], "color": 0xE5484D,
            "description": ("**影響估算**（依過去的平均關係推算，不是預測；重大消息當天常比平均更極端）\n" + "\n".join(lines))[:4000],
            "footer": {"text": "SEC 官方申報 · WallStreet Sentinel · 不構成投資建議"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(a["ts"]))}


NEWS = "https://wallstreet-sentinel.pages.dev/api/news"


def sector_sigmas() -> Dict[str, float]:
    """One year of daily % changes per sector ETF, from the bot's own price history (same σ the site uses)."""
    from wsb.analytics import sector_shock as SS
    try:
        h = pd.read_pickle(DATA_DIR / "history_close.pkl")
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for sym, *_ in SS.SECTORS:
        if sym in h.columns:
            v = SS.robust_sd(h[sym])
            if v:
                out[sym] = v
    return out


async def sector_alerts(sess: aiohttp.ClientSession, now: float) -> List[Dict]:
    """Sectors down ≥ 2× their normal day (and ≥ 1.5 %), with same-hours headlines and the Taiwan names that follow them."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from wsb.analytics import news_impact as NI
    from wsb.analytics import sector_shock as SS
    from wsb.data.stocks import universe
    syms = [s[0] for s in SS.SECTORS]
    q: Dict = {}
    for i in range(0, len(syms), 20):
        async with sess.get(QUOTE, params={"s": ",".join(syms[i:i + 20])}, timeout=aiohttp.ClientTimeout(total=20)) as r:
            q.update((await r.json()).get("q") or {})
    q = {k: v for k, v in q.items() if v.get("t") and now - float(v["t"]) < 20 * 3600}     # stale quotes never alert
    try:
        async with sess.get(NEWS, timeout=aiohttp.ClientTimeout(total=20)) as r:
            news = (await r.json()).get("items") or []
    except Exception:  # noqa: BLE001
        news = []
    hits = SS.check(q, sector_sigmas(), news, now)
    if not hits:
        return []
    cl = _close()
    try:
        h = pd.read_pickle(DATA_DIR / "history_close.pkl")
    except Exception:  # noqa: BLE001
        h = pd.DataFrame()
    allu = {k: (v[0], v[1] if len(v) > 1 else k, "tw") for k, v in ((universe().get("tw") or {}).get("symbols") or {}).items()}
    for a in hits:
        a["day"] = datetime.fromtimestamp(float(a["t"]), ZoneInfo("America/New_York")).date().isoformat()
        a["tw"] = []
        if not cl.empty and a["sym"] in getattr(h, "columns", []):
            both = cl.join(h[[a["sym"]]], how="outer")
            a["tw"] = NI.tw_direct(both, a["sym"], [k for k in allu if k in cl.columns], allu)
    return hits


def sector_embed(a: Dict) -> Dict:
    from wsb.analytics import sector_shock as SS
    tpe = lambda ts: time.strftime("%m/%d %H:%M", time.gmtime(float(ts) + 8 * 3600))  # noqa: E731
    lines = [SS.sentence(a, tpe)]
    if a.get("tw"):
        lines.append("台股隔天（樣本外驗證過的連動）：" + "、".join(f'{p["zh"]} 約 {p["beta"] * a["chg"]:+.1f}%' for p in a["tw"]))
    return {"title": f'{"🔴" if a["lv"] >= 2 else "🟠"} 族群急跌：{a["zh"]} {a["chg"]:+.1f}%（平常一天的 {abs(a["z"]):.1f} 倍）',
            "color": 0xE5484D if a["lv"] >= 2 else 0xD97706,
            "description": ("\n".join(lines) + "\n新聞只代表同時段、同主題，不等於就是原因；台股估算是過去平均關係，不是預測。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 族群急跌警報 · 不構成投資建議"}}


# ------------------------------------------------------------------ 多家媒體同時報導（/api/news 的 bursts，規則在 functions/api/news.js）
BURST_MIN = 3                    # Discord 只推 3 家以上；2 家的公司消息只在網站上列出
BURST_GAP = 12 * 3600            # 同一件事 12 小時內只推一次
# 新聞分類 → 最直接相關的行情（看「現在動了多少」，不是預測）
TAG_ASSET = {"美股": [("^GSPC", "標普 500")], "科技": [("^SOX", "費城半導體")], "利率": [("^TNX", "美債 10 年殖利率")], "油價": [("BZ=F", "布蘭特原油")],
             "匯率": [("DX-Y.NYB", "美元指數")], "黃金": [("GC=F", "黃金")], "地緣": [("BZ=F", "布蘭特原油"), ("GC=F", "黃金"), ("^VIX", "VIX")],
             "台股": [("^TWII", "台股加權")]}


async def news_json(sess: aiohttp.ClientSession) -> Dict:
    try:
        async with sess.get(NEWS, timeout=aiohttp.ClientTimeout(total=20)) as r:
            return (await r.json()) or {}
    except Exception as e:  # noqa: BLE001
        log.info("news: %s", e)
        return {}


async def market_now(sess: aiohttp.ClientSession, tags: List[str], now: float) -> List[str]:
    """How the markets a headline points at are moving right now, each against its own normal day."""
    from wsb.analytics import sector_shock as SS
    want: Dict[str, str] = {}
    for t in tags:
        for sym, zh in TAG_ASSET.get(t, []):
            want.setdefault(sym, zh)
    if not want:
        return []
    try:
        async with sess.get(QUOTE, params={"s": ",".join(want)}, timeout=aiohttp.ClientTimeout(total=20)) as r:
            q = (await r.json()).get("q") or {}
    except Exception:  # noqa: BLE001
        return []
    try:
        h = pd.read_pickle(DATA_DIR / "history_close.pkl")
    except Exception:  # noqa: BLE001
        h = pd.DataFrame()
    live, shut = [], []
    for sym, zh in want.items():
        x = q.get(sym) or {}
        if not isinstance(x.get("chg"), (int, float)) or not x.get("t"):
            continue
        sd = SS.robust_sd(h[sym]) if sym in getattr(h, "columns", []) else None
        mv = f'{x["chg"]:+.1f}%'
        if sym == "^TNX" and isinstance(x.get("price"), (int, float)):          # a yield moves in basis points, not in % of itself
            mv = f'{(x["price"] - x["price"] / (1 + x["chg"] / 100)) * 100:+.0f} 個基點（現 {x["price"]:.2f}%）'
        txt = f"{zh} {mv}" + (f'（平常一天的 {abs(x["chg"]) / sd:.1f} 倍）' if sd else "")
        (live if now - float(x["t"]) < 2 * 3600 else shut).append(txt)
    if live:
        return ["・相關行情現在：" + "、".join(live)] + (["・其他相關行情休市中。"] if shut else [])
    return ["・相關的行情現在都休市，開盤後才看得到反應。"] if shut else []


def burst_embed(b: Dict, lines: List[str]) -> Dict:
    tpe = lambda ts: time.strftime("%H:%M", time.gmtime(float(ts) + 8 * 3600))  # noqa: E731
    heads = "\n".join(f'・[{x["t"][:140]}]({x["u"]})（{x["s"]} {tpe(x["ts"])}）' for x in b.get("items") or [])
    usual = f'；它前 6 小時最多同時只有 {b["base"]} 家在報' if b.get("base") else "；前 6 小時幾乎沒有人提"
    return {"title": f'🟠 多家媒體同時報導：{b["label"]}（{b["n"]} 家）'[:256], "color": 0xD97706,
            "description": (f'一句話看懂：{tpe(b["first"])} 起 {b["mins"]} 分鐘內，{b["n"]} 家不同的新聞編輯室都在報 {b["label"]}{usual}。\n' + heads
                            + (("\n**影響估算**（過去的平均關係乘上現在的漲跌，不是預測）\n" if b.get("kind") == "co" else
                                "\n**相關行情**（只是現在的漲跌，不代表就是這則消息造成的）\n") + "\n".join(lines) if lines else "")
                            + "\n很多家同時報只代表消息正在擴散，不代表內容已經證實，也不代表市場一定會動。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 多家媒體同時報導 · 不構成投資建議"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(b["first"]))}


def burst_todo(bs: List[Dict], sent: Dict[str, float], now: float) -> List[Dict]:
    return [b for b in bs or [] if b.get("n", 0) >= BURST_MIN and (b["key"] not in sent or now - float(sent[b["key"]]) >= BURST_GAP)]


# ------------------------------------------------------------------ 台指期夜盤急跌（期交所官方即時報價；規則同族群急跌）
async def tx_night(sess: aiohttp.ClientSession, now: float) -> Optional[Dict]:
    """The night session (15:00–05:00 Taipei) down ≥ 2× a normal day of the TAIEX and ≥ 1.5 %; None otherwise or when it is closed."""
    from wsb.analytics import sector_shock as SS
    from wsb.data import taifex_live as TL
    t = time.gmtime(now + 8 * 3600)
    if 5 <= t.tm_hour < 15:
        return None
    q = TL.near(await TL.quotes(sess, night=True))
    if not q or q["status"] == "TC":                       # closed: nothing live to report
        return None
    try:
        sd = SS.robust_sd(pd.read_pickle(DATA_DIR / "history_close.pkl")["^TWII"])
    except Exception:  # noqa: BLE001
        return None
    lv = SS.level(q["pct"], sd)
    if not lv:
        return None
    day = time.strftime("%Y-%m-%d", time.gmtime(now + 8 * 3600 - (86400 if t.tm_hour < 5 else 0)))     # the day the session opened
    return {**q, "z": q["pct"] / sd, "lv": lv, "day": day}


async def tx_embed(sess: aiohttp.ClientSession, a: Dict) -> Dict:
    side = []
    try:
        async with sess.get(QUOTE, params={"s": "TSM,^SOX,^NDX", "ext": "TSM"}, timeout=aiohttp.ClientTimeout(total=20)) as r:
            q = (await r.json()).get("q") or {}
        e = (q.get("TSM") or {}).get("ext") or {}
        if isinstance(e.get("chg"), (int, float)):
            side.append(f'台積電 ADR {"盤前" if e.get("sess") == "pre" else "盤後"} {e["chg"]:+.1f}%')
        for s, zh in (("TSM", "台積電 ADR"), ("^SOX", "費城半導體"), ("^NDX", "那斯達克 100")):
            x = q.get(s) or {}
            if isinstance(x.get("chg"), (int, float)) and x.get("t") and time.time() - float(x["t"]) < 2 * 3600:
                side.append(f'{zh} {x["chg"]:+.1f}%')
    except Exception as e:  # noqa: BLE001
        log.info("tx side quotes: %s", e)
    return {"title": f'{"🔴" if a["lv"] >= 2 else "🟠"} 台指期夜盤急跌：{a["pct"]:+.1f}%（台股平常一天的 {abs(a["z"]):.1f} 倍）',
            "color": 0xE5484D if a["lv"] >= 2 else 0xD97706,
            "description": (f'一句話看懂：台股已經收盤，但台指期夜盤現在 {a["last"]:,.0f} 點，比今天日盤結算價 {a["ref"]:,.0f} 低 {abs(a["chg"]):,.0f} 點。\n'
                            + ("・同一時間：" + "、".join(side) + "\n" if side else "・美股現在沒有即時報價可以對照。\n")
                            + "夜盤的成交量比日盤小，明天開盤不一定照這個幅度；它反映的是台股收盤後才出現的消息。")[:4000],
            "footer": {"text": "期交所官方報價 · WallStreet Sentinel · 不構成投資建議"}}


# ------------------------------------------------------------------ 央行非例行動作（/api/news 標 kind=cb 的官方公告）與日圓急升
def cb_embed(x: Dict, lines: List[str]) -> Dict:
    return {"title": ("🔴 央行非例行動作：" + x["t"])[:256], "url": x["u"], "color": 0xE5484D,
            "description": (f'一句話看懂：{x["s"]}發了一則不在例行時程裡的公告（緊急、臨時、聯合行動這一類，或非會議日的利率聲明）。'
                            "央行很少這樣做，通常代表市場或銀行體系出了狀況，或它要搶在市場前面動作。\n"
                            + ("**相關行情**（只是現在的漲跌，不代表就是這則公告造成的）\n" + "\n".join(lines) + "\n" if lines else "")
                            + "標題是用關鍵字比對的，請點進去看原文確認。")[:4000],
            "footer": {"text": "央行官方公告 · WallStreet Sentinel · 不構成投資建議"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(x["ts"]))}


YEN_Z, YEN_MIN = 3.0, 1.5        # 美元兌日圓一天跌 ≥ 平常 3 倍且 ≥ 1.5%（日圓急升）


async def yen_jump(sess: aiohttp.ClientSession, now: float) -> Optional[Dict]:
    from wsb.analytics import sector_shock as SS
    async with sess.get(QUOTE, params={"s": "JPY=X"}, timeout=aiohttp.ClientTimeout(total=20)) as r:
        x = ((await r.json()).get("q") or {}).get("JPY=X") or {}
    if not isinstance(x.get("chg"), (int, float)) or not x.get("t") or now - float(x["t"]) > 2 * 3600:
        return None
    try:
        sd = SS.robust_sd(pd.read_pickle(DATA_DIR / "history_close.pkl")["JPY=X"])
    except Exception:  # noqa: BLE001
        return None
    if not sd or x["chg"] > -YEN_MIN or x["chg"] / sd > -YEN_Z:
        return None
    return {"chg": float(x["chg"]), "z": x["chg"] / sd, "price": x.get("price"), "day": time.strftime("%Y-%m-%d", time.gmtime(float(x["t"])))}


def yen_embed(a: Dict, lines: List[str]) -> Dict:
    return {"title": f'🔴 日圓急升：美元兌日圓 {a["chg"]:+.1f}%（平常一天的 {abs(a["z"]):.1f} 倍）', "color": 0xE5484D,
            "description": ("一句話看懂：日圓在一天內升值這麼多很少見" + (f'，美元兌日圓現在 {a["price"]:.2f}' if isinstance(a.get("price"), (int, float)) else "")
                            + "。常見原因是日本官方進場買日圓（干預），或避險資金大舉回流；日本財務省通常事後才證實有沒有干預。\n"
                            "・接著會怎樣：借日圓去買其他資產的資金成本變高，可能被迫把手上的股票換回現金來還日圓。\n"
                            + ("\n".join(lines) + "\n" if lines else "") + "這是從匯價推測，不是官方消息。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 日圓急升 · 不構成投資建議"}}


# ------------------------------------------------------------------ 離線補課：這支程式停了一小時以上，重新開始時補一則
CATCH_GAP = 3600
GAP_ASSETS = (("^GSPC", "標普 500"), ("^NDX", "那斯達克 100"), ("^SOX", "費城半導體"), ("^TWII", "台股加權"), ("BZ=F", "布蘭特原油"), ("^TNX", "美債 10 年殖利率"))


async def gap_moves(sess: aiohttp.ClientSession, prev: float) -> List[str]:
    """Each main market: now against its last close on or before the day the program stopped."""
    try:
        h = pd.read_pickle(DATA_DIR / "history_close.pkl")
        async with sess.get(QUOTE, params={"s": ",".join(a for a, _ in GAP_ASSETS)}, timeout=aiohttp.ClientTimeout(total=20)) as r:
            q = (await r.json()).get("q") or {}
    except Exception as e:  # noqa: BLE001
        log.info("gap moves: %s", e)
        return []
    day = pd.Timestamp(time.strftime("%Y-%m-%d", time.gmtime(prev)))
    out = []
    for sym, zh in GAP_ASSETS:
        px = (q.get(sym) or {}).get("price")
        if sym not in h.columns or not isinstance(px, (int, float)):
            continue
        v = h[sym].dropna()
        v = v[v.index <= day]
        if not len(v) or not v.iloc[-1]:
            continue
        if abs(px / v.iloc[-1] - 1) < 0.0005:              # nothing traded in between (a weekend): no line
            continue
        out.append(f"{zh} {(px - v.iloc[-1]) * 100:+.0f} 個基點（現 {px:.2f}%）" if sym == "^TNX" else f"{zh} {(px / v.iloc[-1] - 1) * 100:+.1f}%")
    return out


def catchup_embed(prev: float, now: float, late: List[Dict], cbs: List[Dict], moves: List[str]) -> Dict:
    tpe = lambda ts: time.strftime("%m/%d %H:%M", time.gmtime(float(ts) + 8 * 3600))  # noqa: E731
    hours = (now - prev) / 3600
    lines = [f"一句話看懂：推播程式從 {tpe(prev)} 到 {tpe(now)} 沒有在跑（{hours:.0f} 小時，電腦關機、睡眠或斷網），"
             + (f"這段時間有 {len(late) + len(cbs)} 則重大申報或公告沒有即時通知到你。" if late or cbs else "這段時間沒有漏掉追蹤公司的重大申報。")]
    for a in late[:8]:
        lines.append(f'・{tpe(a["ts"])} [{a["t"][:150]}]({a["url"]})')
    for x in cbs[:4]:
        lines.append(f'・{tpe(x["ts"])} [央行公告：{x["t"][:140]}]({x["u"]})')
    if moves:
        lines.append("**這段時間的行情**（和停止那天的收盤比）：" + "、".join(moves))
    lines.append("多家媒體同時報導的紀錄只留 3 小時，離線期間的補不回來；較新的申報（6 小時內）會照常另外通知。")
    return {"title": f"🔁 離線補課：{hours:.0f} 小時沒有即時通知", "color": 0x6366F1, "description": "\n".join(lines)[:4000],
            "footer": {"text": "WallStreet Sentinel · 不構成投資建議"}}


async def holdings_run(sess: aiohttp.ClientSession, now: float, ctx: Optional[Dict] = None) -> int:
    """tools/holdings_watch.py is private (not copied to the public repo): without it there is simply nothing to send.
    ctx hands over what this round already fetched (SEC alerts, earnings releases, news bursts)."""
    try:
        from tools import holdings_watch as HW
    except ImportError:
        return 0
    return await HW.run(sess, post, dm_channel, now, ctx=ctx)


async def run_once(now: Optional[float] = None) -> int:
    from wsb.data import http
    from wsb.data import sec_officers as SOF
    now = now or time.time()
    chan = alert_channel()
    if not DISCORD_TOKEN or not (chan or owner_id()):
        log.warning("DISCORD_BOT_TOKEN, or both the alert channel and the owner id, not set")
        return 0
    try:
        mem = json.loads(PUSHED.read_text(encoding="utf-8")) if PUSHED.exists() else {}
    except (OSError, ValueError):
        mem = {}
    acc = mem.get("acc") or {}
    # what was sent, with when: kept 10 days (a plain list capped by count would drop new keys before old ones)
    done: Dict[str, float] = ({k: now for k in acc} if isinstance(acc, list) else {k: v for k, v in acc.items() if now - float(v) < 10 * 86400})
    bsent: Dict[str, float] = {k: v for k, v in (mem.get("burst") or {}).items() if now - float(v) < 3 * 86400}
    prev = float(mem.get("ts") or 0)
    st = await SOF.refresh(watch_list(), now=now)
    todo = sorted((a for a in st.get("alerts") or [] if a["acc"] not in done and now - a["ts"] < MAX_AGE
                   and a.get("item") != "13D/A"),          # an update to an old 13D is listed on the site only
                  key=lambda a: (-severity(a), -a["ts"]))
    sent = 0
    async with aiohttp.ClientSession() as sess:
        dm = None
        nj = await news_json(sess)
        cbs = [x for x in nj.get("items") or [] if x.get("kind") == "cb" and "cb:" + x["u"] not in done]
        try:                                               # 離線補課：先講漏掉什麼，較新的再照常通知
            if prev and now - prev >= CATCH_GAP:
                late = [a for a in st.get("alerts") or [] if a["acc"] not in done and prev < a["ts"] and now - a["ts"] >= MAX_AGE
                        and a.get("item") != "13D/A"]
                late_cb = [x for x in cbs if prev < x["ts"] and now - x["ts"] >= MAX_AGE]
                if late or late_cb or now - prev >= 3 * 3600:
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", catchup_embed(prev, now, sorted(late, key=lambda a: -severity(a)), late_cb, await gap_moves(sess, prev))):
                        sent += 1
                        for a in late:
                            done[a["acc"]] = now
                        for x in late_cb:
                            done["cb:" + x["u"]] = now
        except Exception as e:  # noqa: BLE001
            log.warning("catch-up failed: %s", e)
        for a in todo:
            lines = await impact(sess, a["sym"], a["zh"])
            e = embed_of(a, lines)
            if not chan:                                   # no alert channel set (same as the bot): everything goes to the DM
                dm = dm or await dm_channel(sess)
            if await post(sess, chan or dm or "", e):
                done[a["acc"]] = now
                sent += 1
                if chan and severity(a) >= 3:              # the worst ones also reach the owner directly
                    dm = dm or await dm_channel(sess)
                    if dm:
                        await post(sess, dm, e)
            await asyncio.sleep(1)
        try:                                               # 族群急跌（same rules as the site's live bar）
            for a in await sector_alerts(sess, now):
                key = f'sector:{a["sym"]}:{a["day"]}:{a["lv"]}'
                if key in done or (a["lv"] == 1 and f'sector:{a["sym"]}:{a["day"]}:2' in done):
                    continue
                if not chan:
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", sector_embed(a)):
                    done[key] = now
                    sent += 1
                await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("sector check failed: %s", e)
        try:                                               # 央行非例行動作
            for x in cbs:
                if now - x["ts"] >= MAX_AGE or "cb:" + x["u"] in done:
                    continue
                e = cb_embed(x, await market_now(sess, ["利率", "匯率", "美股", "黃金"], now))
                if not chan:
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", e):
                    done["cb:" + x["u"]] = now
                    sent += 1
                    if chan:
                        dm = dm or await dm_channel(sess)
                        if dm:
                            await post(sess, dm, e)
            a = await yen_jump(sess, now)
            if a and f'yen:{a["day"]}' not in done:
                if not chan:
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", yen_embed(a, await market_now(sess, ["美股", "科技", "利率"], now))):
                    done[f'yen:{a["day"]}'] = now
                    sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("central bank check failed: %s", e)
        try:                                               # 多家媒體同時報導（3 家以上）＋影響
            for b in burst_todo(nj.get("bursts") or [], bsent, now):
                lines = (await impact(sess, b["sym"], b["label"].split("（")[0]) if b.get("kind") == "co" and b.get("sym")
                         else await market_now(sess, b.get("tags") or [], now))
                if not chan:
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", burst_embed(b, lines)):
                    bsent[b["key"]] = now
                    sent += 1
                await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("burst check failed: %s", e)
        try:                                               # 台指期夜盤急跌
            a = await tx_night(sess, now)
            if a:
                key = f'txnight:{a["day"]}:{a["lv"]}'
                if key not in done and not (a["lv"] == 1 and f'txnight:{a["day"]}:2' in done):
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", await tx_embed(sess, a)):
                        done[key] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("night futures check failed: %s", e)
        try:                                               # 持股晚報與累積跌幅：只私訊擁有者
            sent += await holdings_run(sess, now, {"alerts": st.get("alerts") or [], "earn": st.get("earn") or [], "bursts": nj.get("bursts") or []})
        except Exception as e:  # noqa: BLE001
            log.warning("holdings watch failed: %s", e)
    PUSHED.write_text(json.dumps({"acc": done, "burst": bsent, "ts": int(now)}), encoding="utf-8")
    try:
        s = await http.session()
        await s.close()
    except Exception:  # noqa: BLE001
        pass
    log.info("SEC push: %d sent", sent)
    return sent


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename=str(DATA_DIR / "sec_push.log"), format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_once())
