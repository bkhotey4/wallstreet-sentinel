"""SEC 重大申報 → Discord（獨立小程式，不經過 wsb/bot/app.py，也不需要重啟機器人）。

每次執行：
  1. 名單＝本站追蹤池＋市值 ≥ 1,000 億美元的公司（和網站警報同一份規則，用 SEC 官方 ticker → CIK）
  2. 讀 SEC 最新 8-K（wsb/data/sec_officers.refresh：翻頁到上次看過的地方，第 5.02 項會讀原文判斷離職／任命與職位）
  3. 還沒送過、6 小時內的警報：附上影響估算（標普 500 權重、最常一起動的美股、隔天跟著動的台股，乘上現在的漲跌），
     用同一個機器人身分送到警報頻道（和機器人同一個規則：/setchannel 設的，或 ALERT_CHANNEL_ID）；沒有設頻道就私訊你
     （OWNER_USER_ID）；有頻道時，破產、財報重編這類，或執行長／財務長／董事長離職，另外再私訊一份。
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


async def run_once(now: Optional[float] = None) -> int:
    from wsb.data import http
    from wsb.data import sec_officers as SOF
    now = now or time.time()
    chan = alert_channel()
    if not DISCORD_TOKEN or not (chan or owner_id()):
        log.warning("DISCORD_BOT_TOKEN, or both the alert channel and the owner id, not set")
        return 0
    try:
        done = set(json.loads(PUSHED.read_text(encoding="utf-8")).get("acc") or []) if PUSHED.exists() else set()
    except (OSError, ValueError):
        done = set()
    st = await SOF.refresh(watch_list(), now=now)
    todo = sorted((a for a in st.get("alerts") or [] if a["acc"] not in done and now - a["ts"] < MAX_AGE),
                  key=lambda a: (-severity(a), -a["ts"]))
    sent = 0
    async with aiohttp.ClientSession() as sess:
        dm = None
        for a in todo:
            lines = await impact(sess, a["sym"], a["zh"])
            e = embed_of(a, lines)
            if not chan:                                   # no alert channel set (same as the bot): everything goes to the DM
                dm = dm or await dm_channel(sess)
            if await post(sess, chan or dm or "", e):
                done.add(a["acc"])
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
                    done.add(key)
                    sent += 1
                await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("sector check failed: %s", e)
    PUSHED.write_text(json.dumps({"acc": sorted(done)[-300:], "ts": int(now)}), encoding="utf-8")
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
