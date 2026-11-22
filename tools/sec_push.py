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
  7. 各國危機雷達：每 30 分鐘讀網站的 country_risk.json，新紅燈、3 國以上貨幣兩週內一起貶、或開始擴散時推一則（各一個月一次）。
  6. （A1）系統健康：tools/sys_health.py，每 10 分鐘檢查機器人心跳、連續出錯的資料來源、網站建置、新聞來源數、本機收盤價，
     有新問題才私訊擁有者，同一件事 24 小時說一次。
  8. （2026-11-15）台股重大訊息即時版：公開資訊觀測站官方 RSS（wsb/data/mops_rt.py），追蹤的台股公司一有公告就送，一家公司一則，
     附這檔現在的漲跌與最常一起動的台股；只在持股裡的公司只私訊。原本走機器人的整批檔，實測中位數晚 12 小時。
  9. （2026-11-15）網站警示補位：每 10 分鐘讀網站的 alerts.json，新出現的警示級項目如果機器人沒有對應的通知就補送；
     機器人停了（心跳超過 20 分鐘）則全部代送。
 10. （2026-11-15）送得到、不重送：每則訊息都帶一行文字（手機通知看得到標題）；Discord 忙線或斷線會在同一輪重試兩次；
     每送出一段就存檔；整輪超過 95 秒就把剩下的留到下一輪（Windows 排程 2 分鐘會強制結束）；有發生時間的通知會記下慢了多久。
 12. （2026-11-15）夜間分級：台北 23:30～07:00（settings.yaml delivery.night）標題不是 🔴／🚨 的訊息用 Discord 靜音訊息送
     （照樣即時到、手機不響），記在 data_cache/night_silent.json，早安摘要會說夜裡靜音送了幾則。SEC 申報嚴重度未達 3 的改標 🟠。
 13. （2026-11-16）被迫進出的錢（wsb/data/forced_flows.py）：指數調整日（標普 500、羅素、MSCI、台灣 50）前一天台北 18:00 後、
     標普 500 趨勢跟隨分數翻轉、波動控制股票比重一週掉 2 成，各一次；韓國出口快報（每月 1、11、21 日公布後兩天內）；
     法院與監管（最高法院判決、SEC／CFTC 通過的規則、司法部反壟斷，有市場主題的才送）。每則都附相關行情現在的漲跌。
 11. （2026-11-15）雲端備援：同一支程式也在 GitHub Actions 上跑（公開倉庫的 heartbeat.yml，環境變數 WSB_CLOUD=1）。
     兩邊用 Discord 上的訊息本身對帳：每則訊息的標題連結尾端帶一個看不見的編號（#k=…），送之前先讀頻道最近 200 則，
     對方送過的就不再送。雲端看到一件事後先等 10 分鐘（個股與網站警示 15 分鐘、各國雷達 45 分鐘），家裡電腦沒送才補送；
     機器人超過 45 分鐘沒觸發網站更新（＝電腦多半關了）就只等 3 分鐘，超過 60 分鐘另外說一聲「電腦沒有動靜」。
     雲端沒有持股資料：持股通知、系統健康、離線補課都只在家裡電腦做。雲端第一次啟動只記不送。
送過的記在 data_cache/sec_push.json，不會重送。Windows 工作排程每 3 分鐘跑一次：python -m tools.sec_push
影響估算是過去平均關係的推算，不是預測，也不是投資建議。"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import quote, unquote

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
SITE = "https://wallstreet-sentinel.pages.dev/"

# ------------------------------------------------------------------ 雲端備援（GitHub Actions）與 Discord 對帳
CLOUD = os.environ.get("WSB_CLOUD") == "1"
KEY_RE = re.compile(r"[#&]k=([^&#\s]+)$")
GRACE = {"stock": 900, "site": 900, "cr": 2700}            # 雲端等家裡電腦多久（秒）：電腦多久看一次＋緩衝；其餘 600
GRACE_QUIET = 180                # 電腦看起來關了：只等 3 分鐘
BOT_QUIET_MIN = 45               # 機器人平常每 20 分鐘觸發一次網站更新；連兩次沒來＝多半關機、睡眠或斷網
PC_QUIET_MIN = 60                # 超過這麼久沒動靜：雲端私訊說一聲


def tag(embed: Dict, keys: Union[str, List[str]]) -> Dict:
    """The same embed with the alert's key(s) riding on the title link (…#k=key1,key2).  Nobody sees it, the link still
    opens the same page, and the other machine can read back what was already sent."""
    ks = [keys] if isinstance(keys, str) else list(keys)
    base = str(embed.get("url") or SITE)
    url = base + ("&" if "#" in base else "#") + "k="
    for i, k in enumerate(ks):
        nxt = ("," if i else "") + quote(str(k), safe="")
        if len(url) + len(nxt) > 1990:                     # Discord's limit for a link is 2,048 characters
            break
        url += nxt
    return {**embed, "url": url}


def keys_of(msg: Dict) -> List[str]:
    out: List[str] = []
    for e in msg.get("embeds") or []:
        m = KEY_RE.search(str(e.get("url") or ""))
        if m:
            out += [unquote(k) for k in m.group(1).split(",") if k]
    return out


async def ledger(sess: aiohttp.ClientSession, channel: str, pages: int = 2) -> Optional[Dict[str, float]]:
    """{key: when it was sent} read back from the channel's last 200 messages; None when Discord cannot be read."""
    if not channel:
        return None
    h = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    out: Dict[str, float] = {}
    before = None
    for page in range(pages):
        params = {"limit": "100"}
        if before:
            params["before"] = before
        try:
            async with sess.get(f"{API}/channels/{channel}/messages", headers=h, params=params,
                                timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status >= 300:
                    log.info("ledger: HTTP %s", r.status)
                    return out if page else None
                msgs = await r.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            log.info("ledger: %s", type(e).__name__)
            return out if page else None
        for m in msgs or []:
            try:
                ts = ((int(m["id"]) >> 22) + 1420070400000) / 1000      # a Discord id carries its own time
            except (KeyError, TypeError, ValueError):
                continue
            for k in keys_of(m):
                out.setdefault(k, ts)
        if len(msgs or []) < 100:
            break
        before = msgs[-1]["id"]
    return out


def bot_age_min() -> Optional[float]:
    """Cloud only: minutes since the home bot last started a site build (the workflow works it out and passes it in)."""
    try:
        return float(os.environ["WSB_BOT_AGE_MIN"])
    except (KeyError, ValueError):
        return None


def grace(fam: str, age: Optional[float]) -> float:
    return GRACE_QUIET if age is not None and age >= BOT_QUIET_MIN else GRACE.get(fam, 600)


def quiet_due(q: Dict, age: Optional[float], now: float) -> bool:
    """Say once per outage that the home PC has gone quiet (again only after it came back and 3 hours passed, or a day)."""
    if age is None:
        return False
    if age < BOT_QUIET_MIN:
        q["up"] = True
        return False
    last = float(q.get("ts") or 0)
    return age >= PC_QUIET_MIN and (not last or (q.get("up") and now - last >= 3 * 3600) or now - last >= 86400)


def quiet_embed(age: float) -> Dict:
    how = f"{age / 60:.1f} 小時" if age >= 90 else f"{age:.0f} 分鐘"
    if age >= 9000:
        how = "很久"
    return {"title": "☁️ 家裡電腦沒有動靜，雲端備援已接手", "url": SITE, "color": 0xD97706,
            "description": (f"一句話看懂：家裡電腦上的機器人已經 {how}沒有觸發網站更新（平常每 20 分鐘一次），多半是關機、睡眠或斷網。\n"
                            "・這段時間公開的警報改由雲端送：SEC 重大申報、台股重大訊息、央行公告、多家媒體同時報導、族群與個股大動、"
                            "台指期夜盤、網站警示。會比平常晚幾分鐘到十幾分鐘。\n"
                            "・和你的持股有關的通知（持股晚報、累積跌幅、盤中異常）雲端做不到：雲端沒有、也不該有你的持股資料，要等電腦回來。\n"
                            "・電腦回來後會自動補一則「這段時間漏了什麼」。"),
            "footer": {"text": "WallStreet Sentinel · 雲端備援"}}


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


async def impact(sess: aiohttp.ClientSession, sym: str, zh: str, live: bool = True) -> List[str]:
    """Plain lines: the stock's move now × S&P weight, peers' beta, Taiwan next-session beta.
    live=False: relationships only (a reminder before an event, when today's move is not the point)."""
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
        if not live:
            raise LookupError("relationships only")
        async with sess.get(QUOTE, params={"s": ",".join(syms), "ext": sym}, timeout=aiohttp.ClientTimeout(total=20)) as r:
            q = (await r.json()).get("q") or {}
        o = q.get(sym) or {}
        if isinstance((o.get("ext") or {}).get("chg"), (int, float)):
            mv, ses = o["ext"]["chg"], "盤前" if o["ext"].get("sess") == "pre" else "盤後"
        elif isinstance(o.get("chg"), (int, float)):
            mv = o["chg"]
    except LookupError:
        pass
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
            p["zh"] + (f" 約 {pc(p['beta'] * mv)}" if mv is not None else f"（它動 1%、過去平均跟著動 {p['beta']:.2f}%）")
            + (f"（現 {pc(q[p['sym']]['chg'])}）" if isinstance((q.get(p["sym"]) or {}).get("chg"), (int, float)) else "") for p in peers))
    if tw:
        out.append("・台股隔天（樣本外驗證過的連動）：" + "、".join(
            p["zh"] + (f" 約 {pc(p['beta'] * mv)}" if mv is not None else f"（它動 1%、過去平均跟著動 {p['beta']:.2f}%）") for p in tw))
    else:
        out.append("・台股：沒有和它連動夠穩定的台股")
    return out


def plain(embed: Dict) -> str:
    """The message's own text line = the embed's title.  A message that is only an embed can arrive on the phone as a
    notification with no words in it; with this line the lock screen says what happened."""
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(embed.get("title") or "")).replace("*", "")[:190]


async def post(sess: aiohttp.ClientSession, channel: str, embed: Dict, key: Union[str, List[str], None] = None) -> bool:
    """Send one message; True only when Discord accepted it.  Busy (429) or a server/network error is retried twice in the
    same run — whatever still fails stays unmarked and goes out on the next run 3 minutes later.
    key: the alert's own key(s), carried on the title link so the other machine (home PC ↔ cloud) does not send it again."""
    if not channel:
        return False
    if key:
        embed = tag(embed, key)
    if CLOUD:                                              # say who sent it: a message from the cloud means the PC did not
        embed = {**embed, "footer": {"text": (str((embed.get("footer") or {}).get("text") or "WallStreet Sentinel") + " · ☁️ 雲端備援代送")[:2048]}}
    h = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    loud = bool(embed.get("loud"))                         # 使用者指定一定要響的（2026-11-16：持股財報出爐）
    embed = {k: v for k, v in embed.items() if k != "loud"}
    body = {"content": plain(embed), "embeds": [embed]}
    from wsb import quiet as Q
    hush = not loud and Q.silent(str(embed.get("title") or ""))   # 夜間分級：不是 🔴／🚨 的照樣即時送，但不讓手機響
    if hush:
        body["flags"] = Q.SILENT_FLAG
    for attempt in range(3):
        wait = 2.0
        try:
            async with sess.post(f"{API}/channels/{channel}/messages", headers=h, json=body,
                                 timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status < 300:
                    if hush and not CLOUD:
                        Q.note(str(embed.get("title") or ""), "push")
                    return True
                if r.status == 429:
                    try:
                        wait = min(float((await r.json()).get("retry_after") or 2), 10.0)
                    except Exception:  # noqa: BLE001
                        wait = 3.0
                elif r.status < 500:                       # 400/401/403/404: retrying the same request cannot help
                    log.warning("discord: HTTP %s %s", r.status, (await r.text())[:200])
                    return False
                log.info("discord: HTTP %s, retry %d", r.status, attempt + 1)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            log.info("discord: %s, retry %d", type(e).__name__, attempt + 1)
        if attempt < 2:
            await asyncio.sleep(wait)
    log.warning("discord: not delivered after 3 tries (kept for the next run)")
    return False


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
    try:
        async with sess.post(f"{API}/users/@me/channels", headers=h, json={"recipient_id": owner_id()},
                             timeout=aiohttp.ClientTimeout(total=15)) as r:
            cid = (await r.json()).get("id") if r.status < 300 else None
            if cid and CLOUD:                              # the cloud's log is public: keep the channel id out of it
                print(f"::add-mask::{cid}", flush=True)
            return cid
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:   # no network: nothing is marked sent, the next run tries again
        log.info("dm channel: %s", type(e).__name__)
        return None


def embed_of(a: Dict, lines: List[str]) -> Dict:
    return {"title": (("🔴 " if severity(a) >= 3 else "🟠 ") + a["t"])[:256], "url": a["url"], "color": 0xE5484D if severity(a) >= 3 else 0xD97706,
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


# ------------------------------------------------------------------ 個股大動（網站公開的美股追蹤名單；規則在 wsb/analytics/stock_shock.py）
STOCK_EVERY = 300


async def stock_alerts(sess: aiohttp.ClientSession, now: float, news: Optional[List[Dict]] = None) -> List[Dict]:
    """Tracked US stocks moving ≥ 3.5× their normal day and ≥ 4 %, and tracked Taiwan stocks ≥ 3.0× and ≥ 6 % (either way;
    thresholds in stock_shock.MK), with the headlines that name them.  Each hit carries mk = "us" / "tw"."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from tools import site_secwatch as SW
    from wsb.analytics import stock_shock as ST
    from wsb.data.stocks import universe
    if now < 1.7e9:                                        # a test clock: never fetch live quotes
        return []
    cl, out = _close(), []      # news: the run's /api/news items (11-17: a second 20 s fetch after a failed one cost runs)
    for mk, tz in (("us", "America/New_York"), ("tw", "Asia/Taipei")):
        names = (universe().get(mk) or {}).get("symbols", {})
        sd = ST.sigmas(cl, list(names))
        if not sd:
            continue
        syms, q = list(sd), {}
        for i in range(0, len(syms), 20):
            async with sess.get(QUOTE, params={"s": ",".join(syms[i:i + 20])}, timeout=aiohttp.ClientTimeout(total=20)) as r:
                q.update((await r.json()).get("q") or {})
        q = {k: v for k, v in q.items() if v.get("t") and 0 <= now - float(v["t"]) < 20 * 3600}     # stale quotes never alert
        if news is None:
            news = (await news_json(sess)).get("items") or []
        keys = {s: [k for k in [v[0]] + str(v[1] or "").split("|") if k] for s, v in SW.names_of(names, {}, syms).items()}
        hits = ST.check(q, sd, names, news, now, keys, mk)
        cal = _earn_cal() if mk == "us" else {}
        for a in hits:
            a["day"] = datetime.fromtimestamp(float(a["t"]), ZoneInfo(tz)).date().isoformat()
            a["earn"] = ST.earnings_note(a["sym"], a["day"], cal)
        out += hits
    return out


def earn_due_ciks(wl: Dict[str, list], now: float, floor: float = 5e10) -> Dict[str, list]:
    """{cik: [sym, 中文名]} for watched companies (market cap ≥ floor) whose earnings fall on today or yesterday (US date) —
    their 8-K 2.02 is also checked straight from data.sec.gov, so a slow SEC feed cannot hide a big report (11-17)."""
    from zoneinfo import ZoneInfo
    cal = _earn_cal()
    d = datetime.fromtimestamp(now, ZoneInfo("America/New_York")).date()
    days = {d.isoformat(), (d - timedelta(days=1)).isoformat()}
    syms = {r.get("sym") for k in days for r in (cal.get(k) or {}).get("rows") or [] if (r.get("mcap") or 0) >= floor}
    by_sym = {v[0]: c for c, v in wl.items()}
    return {by_sym[s]: wl[by_sym[s]] for s in syms if s in by_sym}


def _earn_cal() -> Dict:
    """The site's earnings calendar cache (data_cache/earn_days.json): {US date: {rows: [{sym, time}]}}."""
    try:
        return json.loads((DATA_DIR / "earn_days.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


async def stock_tw_impact(sess: aiohttp.ClientSession, sym: str, zh: str) -> List[str]:
    """Plain lines for a Taiwan stock: its move now, 台股加權 now, and the Taiwan names that moved most with it."""
    from wsb.analytics import news_impact as NI
    from wsb.data.stocks import universe
    tw = {k: (v[0], v[1] if len(v) > 1 else k, "tw") for k, v in ((universe().get("tw") or {}).get("symbols") or {}).items()}
    cl = _close()
    ret = cl.pct_change(fill_method=None) * 100 if not cl.empty else pd.DataFrame()
    peers = NI.peers(ret, sym, [k for k in tw if k in ret.columns], tw) if not ret.empty else []
    q = {}
    try:
        async with sess.get(QUOTE, params={"s": ",".join([sym, "^TWII"] + [p["sym"] for p in peers])},
                            timeout=aiohttp.ClientTimeout(total=20)) as r:
            q = (await r.json()).get("q") or {}
    except Exception as e:  # noqa: BLE001
        log.info("quote %s: %s", sym, e)
    pc = lambda v, d=1: f"{v:+.{d}f}%"  # noqa: E731
    mv = (q.get(sym) or {}).get("chg")
    out = [f"{zh} 今天 **{pc(mv)}**" if isinstance(mv, (int, float)) else f"{zh} 的即時價格暫時拿不到，下面只列關係："]
    ix = (q.get("^TWII") or {}).get("chg")
    if isinstance(ix, (int, float)):
        out.append(f"・台股加權同時 {pc(ix, 2)}" + ("：大盤沒怎麼動，多半是這家公司自己的事" if abs(ix) < 1 else "：大盤也在動，先看是不是整體行情"))
    if peers:
        out.append("・過去 120 個交易日最常一起動的台股：" + "、".join(
            p["zh"] + (f"（它動 1%、過去平均跟著動 {p['beta']:.2f}%）")
            + (f"（現 {pc(q[p['sym']]['chg'])}）" if isinstance((q.get(p["sym"]) or {}).get("chg"), (int, float)) else "") for p in peers))
    return out


def stock_embed(a: Dict, lines: List[str]) -> Dict:
    from wsb.analytics import stock_shock as ST
    tpe = lambda ts: time.strftime("%m/%d %H:%M", time.gmtime(float(ts) + 8 * 3600))  # noqa: E731
    up = a["chg"] > 0
    return {"title": f'{"🔴" if a["lv"] >= 2 else "🟠"} 個股大{"漲" if up else "跌"}：{a["zh"]} {a["chg"]:+.1f}%（平常一天的 {abs(a["z"]):.1f} 倍）',
            "color": 0xE5484D if a["lv"] >= 2 else 0xD97706,
            "description": ("\n".join([ST.sentence(a, tpe), "**可能影響**"] + lines[1:])
                            + "\n新聞只代表同時段提到這家公司，不等於就是原因；連動估算是過去平均關係，不是預測。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 個股大動警報 · 不構成投資建議"}}


def stock_many_embed(rest: List[Dict], n_all: int) -> Dict:
    mkt = "台股" if rest and rest[0].get("mk") == "tw" else "美股"
    return {"title": f"🟠 今天有 {n_all} 檔追蹤的{mkt}大動",
            "color": 0xD97706,
            "description": ("同一天這麼多檔一起大動，通常是整體行情或同一個族群的事，不是每家公司各自出事；先看族群急跌警報和即時新聞。\n其餘："
                            + "、".join(f'{a["zh"]} {a["chg"]:+.1f}%（{abs(a["z"]):.1f} 倍）' for a in rest[:25]))[:4000],
            "footer": {"text": "WallStreet Sentinel · 個股大動警報 · 不構成投資建議"}}


# ------------------------------------------------------------------ 多家媒體同時報導（/api/news 的 bursts，規則在 functions/api/news.js）
BURST_MIN = 3                    # Discord 只推 3 家以上；2 家的公司消息只在網站上列出
BURST_GAP = 12 * 3600            # 同一件事 12 小時內只推一次
# 新聞分類 → 最直接相關的行情（看「現在動了多少」，不是預測）
TAG_ASSET = {"美股": [("^GSPC", "標普 500")], "科技": [("^SOX", "費城半導體")], "利率": [("^TNX", "美債 10 年殖利率")], "油價": [("BZ=F", "布蘭特原油")],
             "匯率": [("DX-Y.NYB", "美元指數")], "黃金": [("GC=F", "黃金")], "地緣": [("BZ=F", "布蘭特原油"), ("GC=F", "黃金"), ("^VIX", "VIX")],
             "台股": [("^TWII", "台股加權")],
             "美中科技": [("^SOX", "費城半導體"), ("TSM", "台積電 ADR"), ("CNY=X", "美元兌人民幣")],   # 11-21 new /api/news tag
             "兩岸": [("^TWII", "台股加權"), ("TWD=X", "美元兌新台幣"), ("TSM", "台積電 ADR")],
             "礦產": [("^SOX", "費城半導體"), ("HG=F", "銅")], "電力": [("^TNX", "美債 10 年殖利率")], "記憶體": [("MU", "美光"), ("^SOX", "費城半導體")]}


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


# ------------------------------------------------------------------ 台股重大訊息（即時）：公開資訊觀測站官方 RSS（規則在 wsb/data/mops_rt.py）
def mops_codes() -> tuple:
    """({code: 中文名} for the public Taiwan list + settings.taiwan.watch_stocks, {code: 名稱} held but not public → owner DM only)."""
    from wsb.config import SETTINGS
    from wsb.data.stocks import universe
    pub = {s.split(".")[0]: v[0] for s, v in ((universe().get("tw") or {}).get("symbols") or {}).items()}
    for c in (SETTINGS.get("taiwan", {}) or {}).get("watch_stocks", []) or []:
        pub.setdefault(str(c), str(c))
    priv: Dict[str, str] = {}
    try:
        from wsb.analytics import portfolio as PF
        for t in PF.load_holdings() or {}:
            if str(t).endswith((".TW", ".TWO")) and t.split(".")[0] not in pub:
                priv[t.split(".")[0]] = t.split(".")[0]
    except Exception:  # noqa: BLE001
        pass
    return pub, priv


async def mops_new(sess: aiohttp.ClientSession, now: float) -> Dict:
    """{"groups": [[item…] per company], "sent": {key: ts}, "priv": {codes}}; nothing on a test clock."""
    from wsb.data import mops_rt as MR
    if now < 1.7e9:
        return {"groups": [], "sent": {}, "priv": set()}
    pub, priv = mops_codes()
    sent = MR.load()
    items = await MR.fetch(sess)
    names = {x["code"]: x["name"] for x in items}
    codes = {c: (names.get(c, z) if z == c else z) for c, z in {**priv, **pub}.items()}
    return {"groups": MR.group(MR.fresh(items, codes, sent, now)), "sent": sent, "priv": set(priv)}


async def tw_impact(sess: aiohttp.ClientSession, code: str, zh: str, now: float) -> List[str]:
    """How the stock is moving now (or that Taipei is closed) and the Taiwan names that most often move with it."""
    from wsb.analytics import news_impact as NI
    from wsb.data.stocks import universe
    tw = (universe().get("tw") or {}).get("symbols") or {}
    sym = next((s for s in tw if s.split(".")[0] == code), None)
    if not sym:
        return []
    allu = {k: (v[0], v[1] if len(v) > 1 else k, "tw") for k, v in tw.items()}
    cl = _close()
    ret = cl.pct_change(fill_method=None) * 100 if not cl.empty else pd.DataFrame()
    peers = NI.peers(ret, sym, list(tw), allu) if not ret.empty else []
    q: Dict = {}
    try:
        async with sess.get(QUOTE, params={"s": ",".join([sym] + [p["sym"] for p in peers])}, timeout=aiohttp.ClientTimeout(total=15)) as r:
            q = (await r.json()).get("q") or {}
    except Exception as e:  # noqa: BLE001
        log.info("quote %s: %s", sym, e)
    x = q.get(sym) or {}
    mv = x.get("chg") if isinstance(x.get("chg"), (int, float)) else None
    live = mv is not None and x.get("t") and now - float(x["t"]) < 1800
    if live:
        out = [f"{zh} 現在 **{mv:+.1f}%**"]
    else:
        out = [f"台股現在休市，{zh} 要到下一個交易日開盤才會反應" + (f"（上一個交易日 {mv:+.1f}%）。" if mv is not None else "。")]
    if peers:
        out.append("・過去 120 個交易日最常一起動的台股：" + "、".join(
            p["zh"] + (f" 約 {p['beta'] * mv:+.1f}%" if live else f"（它動 1%，這檔平均動 {p['beta']:.1f}%）") for p in peers))
    return out


def mops_embed(g: List[Dict], lines: List[str]) -> Dict:
    top = max(g, key=lambda x: (x["lv"], x["ts"]))
    red = top["lv"] >= 2
    rows = "\n".join(f'・{x["when"]}【{x["kind"]}】{x["subject"][:170]}' for x in sorted(g, key=lambda x: (-x["lv"], -x["ts"]))[:8])
    return {"title": (f'{"🔴" if red else "🟠"} 台股重大訊息：{top["zh"]}（{top["code"]}）{top["kind"]}' + (f" 等 {len(g)} 則" if len(g) > 1 else ""))[:256],
            "url": top["url"][:2000], "color": 0xE5484D if red else 0xD97706,
            "description": (f'一句話看懂：{top["zh"]} 剛在公開資訊觀測站發布' + (f"{len(g)} 則重大訊息" if len(g) > 1 else "重大訊息")
                            + f'（{top.get("market") or "台股"}）。\n' + rows
                            + ("\n**可能影響**（過去的平均關係，不是預測）\n" + "\n".join(lines) if lines else "")
                            + "\n分類與標紅只看主旨裡的關鍵字（事故、財務危機、司法、高層異動、澄清報導、更正財報會標紅），沒有讀懂內容；請點標題看原文。")[:4000],
            "footer": {"text": "公開資訊觀測站官方 RSS · WallStreet Sentinel · 不構成投資建議"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(top["ts"]))}


# ------------------------------------------------------------------ 網站警示補位：網站算出來、機器人沒有對應通知的警示；機器人停了就全部代送
SITE_ALERTS = "https://wallstreet-sentinel.pages.dev/alerts.json"
SITE_EVERY = 600
SITE_STALE = 3 * 3600            # 網站超過 3 小時沒重建：上面的警示是舊的，不推（系統健康會另外說）
# 機器人自己就有同一類通知的警示（key 的第一段）；不在這裡面的新類別一律補推，寧可多說
BOT_HAS = {"danger", "ssi", "ssi_jump", "vix_back", "sigma", "gamma", "canary", "playbook", "bottom", "stab"}


async def site_alerts_json(sess: aiohttp.ClientSession, now: float) -> Dict:
    if now < 1.7e9:                                        # a test clock: never fetch the live page
        return {}
    try:
        async with sess.get(SITE_ALERTS, timeout=aiohttp.ClientTimeout(total=15)) as r:
            return (await r.json(content_type=None)) or {} if r.status < 300 else {}
    except Exception as e:  # noqa: BLE001
        log.info("site alerts: %s", e)
        return {}


def site_todo(d: Dict, seen: Dict[str, float], now: float, bot_alive: bool) -> List[Dict]:
    """Alert-level items that appeared since the last look.  `seen` is updated in place; the first look only remembers
    (an alert that was already on the page is not news)."""
    items = d.get("items") or []
    if not d.get("ts") or abs(now - float(d["ts"])) > SITE_STALE:
        return []
    first = not seen
    new = [x for x in items if x.get("key") and x["key"] not in seen]
    for x in items:
        if x.get("key"):
            seen[x["key"]] = now
    if first:
        return []
    return [x for x in new if x.get("lv") == "alert" and (not bot_alive or x["key"].split(":")[0] not in BOT_HAS)]


def site_embed(xs: List[Dict], bot_alive: bool) -> Dict:
    rows = "\n".join(f'・**{x.get("zh") or x["key"]}**' + (f'\n　{str(x["detail"]).strip("｜ ")[:260]}' if x.get("detail") else "") for x in xs[:6])
    why = ("這幾項是網站算出來的警示，機器人沒有對應的通知，所以由這裡補上。" if bot_alive
           else "機器人目前沒有在跑，網站上新出現的警示改由這裡代送。")
    return {"title": ("⚠️ 網站警示：" + str(xs[0].get("zh") or xs[0]["key"]) + (f" 等 {len(xs)} 則" if len(xs) > 1 else ""))[:256],
            "url": "https://wallstreet-sentinel.pages.dev/", "color": 0xE5484D,
            "description": ("一句話看懂：網站最近一次重新計算後，新出現了下面的警示。\n" + rows + "\n" + why
                            + "網站大約每 20 分鐘重算一次，所以這類通知會比事情發生晚一些。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 網站警示 · 不構成投資建議"}}


# ------------------------------------------------------------------ 通知慢了多久：有「事情發生時間」的通知，記下發生到送出的秒數（系統健康會看）
LAG = DATA_DIR / "push_lag.json"


def note_lag(kind: str, ev_ts: float, now: float) -> None:
    try:
        rows = json.loads(LAG.read_text(encoding="utf-8")) if LAG.exists() else []
    except (OSError, ValueError):
        rows = []
    rows = [r for r in rows if now - float(r.get("at") or 0) < 7 * 86400][-400:] + [{"k": kind, "ev": float(ev_ts), "at": float(now)}]
    try:
        LAG.write_text(json.dumps(rows), encoding="utf-8")
    except OSError:
        pass


HEALTH_EVERY = 600
FISCAL_EVERY = 6 * 3600          # 政府撥款與債務上限：資料一天才變一次（模組自己 12 小時才真的去抓）


def fiscal_embed(a: Dict, v: Dict, lines: List[str]) -> Dict:
    """One stage of the shutdown / debt-limit countdown (rules in wsb/data/us_fiscal.alerts)."""
    from tools import site_fiscal as SF
    red = a["lv"] >= 2
    if a["kind"] == "cr":
        f = v.get("funding") or {}
        title = (f"{'🔴' if red else '🟠'} 美國政府撥款" + (f"還有 {a['days']} 天到期" if a["days"] > 0 else "已到期，可能停擺"))
        lead = SF.funding_lead(f).replace("<b>", "").replace("</b>", "")
        why = ("到期前國會沒通過新的撥款法律，沒拿到全年預算的機關會停擺：聯邦員工停薪，勞工統計局等機關停止發布就業、物價數據，"
               "聯準會和市場少了最重要的數字。過去停擺時股市通常反應不大，衝擊多半在數據空窗和經濟本身。")
    else:
        dv = v.get("debt") or {}
        title = f"{'🔴' if red else '🟠'} 美國債務上限：照最近速度約 {a['months']:.1f} 個月用完"
        lead = SF.debt_lead(dv).replace("<b>", "").replace("</b>", "")
        why = ("快到期限時，在期限附近到期的短期公債殖利率會被拉高；上限一調高，財政部會大量發債把現金補回來，"
               "吸走銀行體系的資金，這段時間股市和高風險資產比較容易震盪。用完之後財政部還有「非常措施」可以撐一段時間。")
    return {"title": title[:256], "url": SITE + "#bonds", "color": 0xE5484D if red else 0xD97706,
            "description": ("一句話看懂：" + lead + "\n" + why + ("\n**相關行情現在**\n" + "\n".join(lines) if lines else ""))[:4000],
            "footer": {"text": "GovInfo 法律原文・財政部每日報表 · WallStreet Sentinel · 倒數不是預測 · 不構成投資建議"}}
NL = "\n"
FORCED_EVERY = 3600             # 被迫進出的錢：指數調整日前一天、標普趨勢翻轉、波動控制比重一週掉 2 成（模組自己 4 小時才真的去抓）


def forced_embed(a: Dict, v: Dict, lines: List[str]) -> Dict:
    """One forced-flow alert (rules in wsb/data/forced_flows.alerts)."""
    from wsb.data import forced_flows as FF
    from tools import site_forced as SFO
    if a["kind"] == "event":
        e = a["ev"]
        zh = FF.KIND[e["kind"]][0]
        med = (v.get("past_med") or {}).get(e["kind"])
        title = f"🟠 {SFO._md(e['date'])}{zh}：指數基金被迫在收盤調整"
        lead = (f"{SFO._md(e['date'])}{zh}" + (f"，台股在 {SFO._md(e['tw_date'])} 收盤調整" if e.get("tw_date") and e["tw_date"] != e["date"] else "")
                + (f"。過去同一種日子，收盤成交量的中位數是平常的 {med:.1f} 倍。" if med else "。"))
        why = SFO.EV_WHY.get(e["kind"], "") + "這種量是照規則被迫的，價格常在收盤前被推動、隔天不一定延續。"
        url = SITE + "#forced"
    elif a["kind"] == "trend":
        tr = a["tr"]
        f1 = (tr.get("flips") or {}).get("21") or (tr.get("flips") or {}).get(21) or {}
        up = tr["score"] > 0
        title = f"{'🟢' if up else '🟠' if a['lv'] < 2 else '🔴'} 趨勢跟隨基金推估：標普 500 轉為{'偏多' if up else '偏空'}"
        lead = (f"照 1、3、12 個月漲跌方向推算，趨勢分數從 {tr['prev']:+.2f} 變成 {tr['score']:+.2f}（−1 全空～+1 全多）。"
                + (f"1 個月趨勢的翻轉點在 {f1['price']:,.0f}。" if f1.get("price") else ""))
        why = ("趨勢跟隨基金（CTA）照規則跟著趨勢調整部位：轉空時會陸續減少股票、甚至放空，把下跌放大；轉多時反過來。"
               "這是模型估算，不是它們實際的部位。")
        url = SITE + "#forced"
    else:
        vc = a["vc"]
        title = f"🟠 波動控制基金推估：股票比重一週從 {vc['week'] * 100:.0f}% 降到 {vc['now'] * 100:.0f}%"
        lead = f"標普 500 近期實際波動升到年化約 {max(vc['rv21'], vc['rv63']) * 100:.0f}%，目標 10% 的基金得把股票比重往下調。"
        why = "波動越大、這類基金越要減少股票；波動回落後才會慢慢加回來。這是照公開規則的模型估算，不是實際部位。"
        url = SITE + "#forced"
    return {"title": title[:256], "url": url, "color": 0xD97706 if a["lv"] < 2 else 0xE5484D,
            "description": ("一句話看懂：" + lead + NL + why + (NL + "**相關行情現在**" + NL + NL.join(lines) if lines else ""))[:4000],
            "footer": {"text": "指數公司規則推算・Yahoo 日線 · WallStreet Sentinel · 規則推算與模型估算，不是預測 · 不構成投資建議"}}


KOREA_EVERY = 1800               # 韓國出口快報：每月 1、11、21 日（韓國 9:00＝台北 8:00）公布，公布後兩天內送一次


def korea_embed(a: Dict, lines: List[str]) -> Dict:
    from tools import site_korea as SKO
    r = a["row"]
    d = r.get("day_yoy") if r.get("day_yoy") is not None else r.get("yoy")
    lamp = "🟢" if d is not None and d > 0 else "🟠"
    title = f"{lamp} 韓國出口快報（{SKO.period_zh(r['key'])}）：年增 {r['yoy']:+.1f}%"
    why = ("韓國出口大約一半是晶片，每 10 天公布一次，比台灣出口早兩到三週；晶片出口轉弱常是記憶體、AI 伺服器需求變化的早期訊號，"
           "之後才反映到台積電與台灣伺服器供應鏈。")
    return {"title": title[:256], "url": SITE + "#tw_econ", "color": 0x16A34A if lamp == "🟢" else 0xD97706,
            "description": ("一句話看懂：" + SKO.lead_of(r).replace("<b>", "").replace("</b>", "") + NL + why
                            + (NL + "**相關行情現在**" + NL + NL.join(lines) if lines else ""))[:4000],
            "footer": {"text": "韓國關稅廳報導資料 · WallStreet Sentinel · 不構成投資建議"}}


BIS_EVERY = 1800                 # 商務部工業安全局新聞稿：出口管制「宣布」的當下（聯邦公報要等正式刊登，常晚幾天到幾週；11-17）


def bis_embed(a: Dict, lines: List[str]) -> Dict:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    x = a["item"]
    tp = datetime.fromtimestamp(x["ts"], ZoneInfo("Asia/Taipei"))
    et = datetime.fromtimestamp(x["ts"], ZoneInfo("America/New_York"))
    lead = (f"美國商務部工業安全局（BIS）在台北 {tp:%m/%d %H:%M}（美東 {et:%m/%d %H:%M}）發布「{x['title']}」，"
            f"主題是{x.get('topic', '')}，最先會動的通常是{x.get('sym_zh', '相關資產')}。")
    why = ("這是政府「宣布」的當下；正式刊登在聯邦公報常晚幾天到幾週，市場通常在宣布時就反應。"
           "出口管制先打到被管的晶片與設備公司，再傳到台灣的晶圓代工、伺服器與封測供應鏈。")
    return {"title": f"🏛️ 美國出口管制：{x['title']}"[:256], "url": x["url"], "color": 0xDC2626,
            "description": ("一句話看懂：" + lead + NL + why + (NL + "**相關行情現在**" + NL + NL.join(lines) if lines else ""))[:4000],
            "footer": {"text": "美國商務部工業安全局官方新聞稿 · WallStreet Sentinel · 不構成投資建議"}}


RULINGS_EVERY = 3 * 3600         # 法院與監管：最高法院判決、SEC／CFTC 通過的規則、司法部反壟斷（模組 6 小時才真的去抓）


def ruling_embed(a: Dict, lines: List[str]) -> Dict:
    from wsb.data import rulings as RL
    x = a["item"]
    src = RL.SRC_ZH.get(x["src"], x["src"])
    title = f"📜 {src}：{x['title']}"
    lead = f"{src}在 {x['date']} 公布「{x['title']}」，主題是{x.get('topic', '')}，最先會動的是{x.get('sym_zh', '相關資產')}。"
    why = ("判決和監管規則是「規則本身變了」：直接被管到的資產最先動，接著才傳到其他市場。"
           + (NL + f"官方摘要：{x['sum'][:500]}" if x.get("sum") else ""))
    return {"title": title[:256], "url": x["url"], "color": 0x6366F1,
            "description": ("一句話看懂：" + lead + NL + why + (NL + "**相關行情現在**" + NL + NL.join(lines) if lines else ""))[:4000],
            "footer": {"text": "最高法院・SEC・CFTC・司法部官方發布 · WallStreet Sentinel · 不構成投資建議"}}


EARNSOON_EVERY = 1800             # 大公司財報前一晚提醒（市值 5,000 億美元以上；台北 18:00 後，公布前 24 小時內；2026-11-16）
PREVIEW_RAW = "https://raw.githubusercontent.com/bkhotey4/wallstreet-sentinel/main/research_feed/earn_preview.json"


def earnsoon_due(rows: List[Dict], now: float) -> List[Dict]:
    """Reports (from tools.site_events.earn_events) that come out within 24 hours, once it is 18:00 or later in Taipei
    (an after-close US report lands around 05:00 Taipei, so the reminder goes out the evening before)."""
    tpe = time.gmtime(now + 8 * 3600)
    if tpe.tm_hour < 18:
        return []
    return [r for r in rows if 0 < r["ts"] - now <= 24 * 3600]


def earnsoon_embed(r: Dict, lines: List[str], pv: Optional[Dict]) -> Dict:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    tp = datetime.fromisoformat(r["next"]).astimezone(ZoneInfo("Asia/Taipei"))
    when = f"{tp.month}/{tp.day} {'清晨 ' if tp.hour < 8 else ''}{tp:%H:%M} 起（台北）"
    name = r["zh"].split("財報")[0]
    from tools.site_events import cap_txt          # 11-18: small AI-chain names (HP) printed 「0.0 兆美元」
    lead = (f"{name}（{r['sym']}）預計 {when}公布財報，市值約 {cap_txt(r['mcap'])}"
            + (f"，每股盈餘預期 {r['eps_f']} 美元" if r.get("eps_f") else "") + "。")
    if pv and pv.get("probs"):
        pr = pv["probs"]
        lead += f"本站財報前瞻：{pv.get('call', '')}（上修 {pr.get('上修')}%／維持 {pr.get('維持')}%／下修 {pr.get('下修')}%）。"
    from tools.site_events import EARN_FLOOR
    why = ("大公司財報公布後，常帶著整個大盤和台股供應鏈一起動" if r.get("mcap", 0) >= EARN_FLOOR or not r.get("ai") else
           "這家是 AI 供應鏈公司，訂單與財測常牽動同一條鏈上的公司")
    why += "；下面是它占大盤多少、過去最常跟著它動的公司（過去的平均關係，不是預測）。"
    return {"title": f"📊 大公司財報倒數：{name}（{r['sym']}）{when}"[:256], "url": SITE + "#tech", "color": 0x3B82F6,
            "description": ("一句話看懂：" + lead + NL + why + NL + NL.join(lines))[:4000],
            "footer": {"text": "財報日曆・本站財報前瞻 · WallStreet Sentinel · 時間以公司公告為準 · 不構成投資建議"}}


BUDGET = 95.0                    # 這支程式每 3 分鐘跑一次、Windows 排程 2 分鐘就會強制結束：超過 95 秒，剩下的留到下一輪
# ------------------------------------------------------------------ 台股規則 v1 紙上交易（網站每天收盤後算好的 tw_paper.json；tools/tw_paper.py）
PAPER = "https://wallstreet-sentinel.pages.dev/tw_paper.json"
# ------------------------------------------------------------------ 主線追蹤（11-21 盲點檢討；規則 wsb/analytics/threads.py）
THREADS = "https://wallstreet-sentinel.pages.dev/threads.json"
TH_EVERY = 1800
TH_MIN_DAYS = 5          # 「升溫」要先累積幾天新聞才準；官方新文件不用等
TH_GAP = 24 * 3600       # 每條主線一天最多一則


async def threads_json(sess: aiohttp.ClientSession) -> Dict:
    try:
        async with sess.get(THREADS, timeout=aiohttp.ClientTimeout(total=20)) as r:
            return (await r.json(content_type=None)) or {} if r.status < 300 else {}
    except Exception as e:  # noqa: BLE001
        log.info("threads: %s", e)
        return {}


def threads_todo(d: Dict, done: Dict[str, float], now: float) -> List[Dict]:
    out = []
    for t in d.get("threads") or []:
        ok = t.get("state") == "官方新文件" or (t.get("state") == "升溫" and float(d.get("days") or 0) >= TH_MIN_DAYS)
        key = "thread:" + str(t.get("id"))
        if ok and now - float(done.get(key, 0)) >= TH_GAP:
            out.append({**t, "key": key})
    return out


def thread_embed(t: Dict, lines: List[str]) -> Dict:
    tpe = lambda ts: time.strftime("%m/%d %H:%M", time.gmtime(float(ts or 0) + 8 * 3600))  # noqa: E731
    hot = t.get("state") == "升溫"
    heads = NL.join(f'・{"📄 " if x.get("off") else ""}[{str(x["t"])[:130]}]({x["u"]})（{x["s"]} {tpe(x["ts"])}）' for x in (t.get("items") or [])[:5])
    lead = (f'「{t["zh"]}」這條主線 48 小時有 {t["n48"]} 則新聞，平常約 {t["base"]} 則。' if hot else
            f'「{t["zh"]}」這條主線出現官方新文件（📄）。')
    return {"title": f'🧵 主線{"升溫" if hot else "：官方新文件"}：{t["zh"]}'[:256], "color": 0x7C3AED, "url": "https://wallstreet-sentinel.pages.dev/#news",
            "description": ("一句話看懂：" + lead + str(t.get("why") or "") + NL + heads
                            + (NL + "**相關行情**（只是現在的漲跌，不代表就是這些消息造成的）" + NL + NL.join(lines) if lines else "")
                            + NL + "依標題關鍵字歸類，只代表相關新聞變多，不是讀過內文的判斷；完整清單在網站「新聞日曆」頁的主線追蹤。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 主線追蹤 · 不構成投資建議"}}


TH_TAGS = {"uscn_tech": ["美中科技"], "ai_capex": ["科技", "台股"], "fed_path": ["利率", "匯率"], "japan_yen": ["匯率"],
           "tw_leverage": ["台股"], "china_econ": ["匯率", "美股"], "energy_geo": ["地緣"],
           "cross_strait": ["兩岸"], "minerals": ["礦產"], "ai_power": ["電力"], "memory": ["記憶體"]}


# ------------------------------------------------------------------ 台股大型公司宣布庫藏股（11-22；資料 site/tw_corp.json）
TWCORP = "https://wallstreet-sentinel.pages.dev/tw_corp.json"
TB_EVERY = 1800
TB_FRESH_D = 3           # only boards that decided within 3 days (no flood of old ones on the first run)
TB_DAY_CAP = 3


async def twcorp_json(sess: aiohttp.ClientSession) -> Dict:
    try:
        async with sess.get(TWCORP, timeout=aiohttp.ClientTimeout(total=20)) as r:
            return (await r.json(content_type=None)) or {} if r.status < 300 else {}
    except Exception as e:  # noqa: BLE001
        log.info("tw_corp: %s", e)
        return {}


def buyback_todo(d: Dict, done: Dict[str, float], now: float) -> List[Dict]:
    cut = time.strftime("%Y-%m-%d", time.gmtime(now + 8 * 3600 - TB_FRESH_D * 86400))
    out = []
    for x in d.get("buybacks") or []:
        key = f'tsb:{x.get("code")}:{x.get("date")}'
        if x.get("big") and str(x.get("date") or "") >= cut and key not in done:
            out.append({**x, "key": key})
    return out


def buyback_embed(x: Dict) -> Dict:
    sh = float(x.get("shares") or 0) / 1000
    return {"title": f'🏢 庫藏股：{x.get("name")}（{x.get("code")}）'[:256], "color": 0x0EA5E9, "url": "https://wallstreet-sentinel.pages.dev/#tw_earn",
            "description": (f'一句話看懂：{x.get("name")} 董事會 {str(x.get("date") or "")[5:].replace("-", "/")} 決議買回自家股票，'
                            f'目的「{x.get("purpose")}」，預定最多 {sh:,.0f} 張，價格區間 {x.get("lo")}～{x.get("hi")} 元，'
                            f'期間 {str(x.get("start") or "")[5:]}～{str(x.get("end") or "")[5:]}。' + NL +
                            '公司拿自己的錢買回股票，代表董事會覺得股價偏低或想穩住股價；「預定」是上限，不代表一定會買完。'
                            '完整清單與內部人申報轉讓在網站「台股財報」頁。')[:4000],
            "footer": {"text": "WallStreet Sentinel · 台股庫藏股 · 公開資訊觀測站 · 不構成投資建議"}}


# ------------------------------------------------------------------ 台股三種通知（11-22 台股覆蓋清單；資料 site/tw_alerts.json）
TWAL = "https://wallstreet-sentinel.pages.dev/tw_alerts.json"
TWAL_EVERY = 900


async def twal_json(sess: aiohttp.ClientSession) -> Dict:
    try:
        async with sess.get(TWAL, timeout=aiohttp.ClientTimeout(total=20)) as r:
            return (await r.json(content_type=None)) or {} if r.status < 300 else {}
    except Exception as e:  # noqa: BLE001
        log.info("tw_alerts: %s", e)
        return {}


def _tpe(now: float):
    return time.gmtime(now + 8 * 3600)


def twal_todo(d: Dict, done: Dict[str, float], now: float) -> List[Dict]:
    """Pre-open lights (weekdays 07:30–09:05 Taipei, red only), a new month of revenue (once), tomorrow's 法說會 (19:00–23:30)."""
    t = _tpe(now)
    day = time.strftime("%Y-%m-%d", t)
    hm = t.tm_hour * 60 + t.tm_min
    out = []
    p = d.get("preopen") or {}
    due = [c for c in p.get("cal") or [] if day in (c.get("topup"), c.get("dispose"))]
    red = p.get("adr_light") == "🔴" or (p.get("mg") or {}).get("light") == "🔴" or due
    if t.tm_wday < 5 and 450 <= hm <= 545 and red and f"twpre:{day}" not in done:
        out.append({"kind": "pre", "key": f"twpre:{day}", "p": p, "due": due})
    r = d.get("rev") or {}
    pm = time.strftime("%Y-%m", time.gmtime(now + 8 * 3600 - t.tm_mday * 86400))          # the previous calendar month
    if r.get("latest") == pm and t.tm_mday <= 15 and r.get("acc") and f'twrev:{r["latest"]}' not in done:   # fresh only
        out.append({"kind": "rev", "key": f'twrev:{r["latest"]}', "r": r})
    n = d.get("irs_next") or {}
    if n.get("rows") and 1140 <= hm <= 1410 and f'twirs:{n.get("date")}' not in done:
        out.append({"kind": "irs", "key": f'twirs:{n.get("date")}', "n": n})
    return out


def twal_embed(a: Dict) -> Dict:
    url = "https://wallstreet-sentinel.pages.dev/"
    if a["kind"] == "pre":
        p, mg = a["p"], (a["p"].get("mg") or {})
        lines = []
        if p.get("adr_light") == "🔴":
            lines.append(f'・台積電 ADR 價差 {p.get("adr_now")}%，在一年裡的第 {p.get("adr_pct")} 百分位（極端）；價差回到最近 20 天中位數時，台積電約對應 '
                         f'{p.get("adr_mid")} 元（{(p.get("adr_chg_mid") or 0):+.1f}%）。這是算術，不是預測。')
        if mg.get("light") == "🔴":
            lines.append(f'・融資餘額 {str(mg.get("d"))[5:]} 一天 {mg.get("pct")}%（{mg.get("now")} 億元），借錢買股的人還在被迫賣。')
        if p.get("mratio"):
            lines.append(f'・上市整體融資維持率約 {p["mratio"]:.0f}%（本站估算；個別帳戶低於 130% 會被追繳）。')
        for c in a.get("due") or []:
            lines.append(f'・{str(c.get("d"))[5:]} 那天被追繳的融資：' + ("今天是補繳期限" if c.get("topup") == time.strftime("%Y-%m-%d", _tpe(time.time())) else "今天起可能被處分（斷頭）"))
        return {"title": "🚦 台股開盤前紅燈", "color": 0xE5484D, "url": url + "#taiwan",
                "description": ("一句話看懂：開盤前有被迫賣壓或價差極端的訊號。" + NL + NL.join(lines) + NL
                                + "完整的開盤前預估卡在網站「台股」頁。這是現況描述，不是預測或建議。")[:4000],
                "footer": {"text": "WallStreet Sentinel · 台股開盤前 · 不構成投資建議"}}
    if a["kind"] == "rev":
        r = a["r"]
        f = lambda xs: NL.join(f'・{x["name"]}（{x["code"]}）年增 {x["yoy"]:+.0f}%，近 3 個月比前 3 個月 {x["accel"]:+.0f} 個百分點' for x in xs)  # noqa: E731
        return {"title": f'📈 台股 {str(r["latest"])[5:].lstrip("0")} 月營收：加速與放緩最多的公司', "color": 0x2FBF71, "url": url + "#tw_desk",
                "description": (f'一句話看懂：台灣 50＋中型 100 裡，{(r.get("breadth") or 0):.0f}% 的公司近 3 個月營收成長在加速。' + NL
                                + "**加速最多**" + NL + f(r.get("acc") or []) + NL + "**放緩最多**" + NL + f(r.get("slow") or []) + NL
                                + "營收是過去式；加速代表訂單在進來，放緩不一定是壞事（可能是去年基期太高）。完整的月營收熱度在網站「台股專業判讀」。")[:4000],
                "footer": {"text": "WallStreet Sentinel · 台股月營收 · 公開資訊觀測站 · 不構成投資建議"}}
    n = a["n"]
    rows = []
    for x in n.get("rows") or []:
        pr = x.get("prog") or {}
        q = f'本季已公布 {pr.get("months")} 個月，比去年同期 {pr.get("qtd_yoy"):+.0f}%' if pr.get("qtd_yoy") is not None else "沒有本季營收資料"
        rows.append(f'・{x.get("time")} {x.get("name")}（{x.get("code")}）' + (f'・{x.get("layer")}' if x.get("layer") else "") + f'：{q}')
    return {"title": f'🎤 明天（{str(n.get("date"))[5:].replace("-", "/")}）的公司自辦法說', "color": 0x7C3AED, "url": url + "#tw_earn",
            "description": ("一句話看懂：明天有這些台灣 50、中型 100 或 AI 供應鏈公司自己開法說會。" + NL + NL.join(rows) + NL
                            + "前瞻重點與完整清單在網站「台股財報」頁。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 台股法說會 · 不構成投資建議"}}


PAPER_EVERY = 1800
PAPER_DAY_CAP = 5                  # 一天最多 5 則（台北日期）
PAPER_MAX_AGE_D = 3                # 只送 3 天內的成交：快取重建時，舊成交不會整批重送
PAPER_KIND = {"entry": "進場訊號", "tp": "漲 20% 先出一半", "stop": "停損出場", "trail_ma": "跌破 20 日均線出場",
              "trail_dd": "從最高回落 8% 出場", "time": "60 天時間到出場", "trail": "移動停利出場"}


async def paper_json(sess: aiohttp.ClientSession) -> Dict:
    try:
        async with sess.get(PAPER, timeout=aiohttp.ClientTimeout(total=15)) as r:
            return (await r.json(content_type=None)) or {} if r.status < 300 else {}
    except Exception as e:  # noqa: BLE001
        log.info("paper ledger: %s", e)
        return {}


def paper_todo(d: Dict, done: Dict[str, float], now: float) -> List[Dict]:
    """New main-ledger fills, newest last, at most what is left of today's cap (Taipei date)."""
    tpe = datetime.utcfromtimestamp(now) + timedelta(hours=8)
    day0 = (tpe.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=8) - datetime(1970, 1, 1)).total_seconds()
    used = sum(1 for k, v in done.items() if k.startswith("paper:") and float(v) >= day0)
    fresh = []
    for e in d.get("events") or []:
        try:
            age = (tpe.date() - date.fromisoformat(str(e["date"]))).days
        except (KeyError, ValueError):
            continue
        if e.get("key") and e["key"] not in done and 0 <= age <= PAPER_MAX_AGE_D:
            fresh.append(e)
    return fresh[:max(PAPER_DAY_CAP - used, 0)]


def paper_embed(e: Dict) -> Dict:
    nm = f'{str(e["sym"]).replace(".TW", "")} {e.get("name") or ""}'.strip()
    kind = PAPER_KIND.get(e["kind"], e["kind"])
    if e["kind"] == "entry":
        why = (f"前一個交易日收盤突破過去 50 日最高、成交量大於 20 日均量 1.5 倍，規則 v1 在 {e['date']} 開盤紙上成交 {e['px']:,.2f} 元；"
               f"停損 {e.get('stop', 0):,.2f} 元（−7.5%），占假設本金 {float(e.get('w') or 0) * 100:.0f}%；"
               f"當時大盤濾網{'開（加權指數在 200 日線上）' if e.get('mkt_ok') else '關（加權指數在 200 日線下，對照帳本不會進場）'}。")
    else:
        why = (f"{e['date']} 紙上成交 {e['px']:,.2f} 元：{kind}。"
               + (f"這筆整體 {float(e['ret']) * 100:+.1f}%（含手續費與證交稅）。" if e.get("ret") is not None else "剩下一半的停損拉到成本。"))
    return {"title": f"📝 紙上交易｜{kind}：{nm}"[:256], "url": "https://wallstreet-sentinel.pages.dev/#taiwan", "color": 0x6E56CF,
            "description": ("一句話看懂：" + why + "\n這是規則的紙上記帳（假設本金 100 萬元），不下單；成績單在網站台股頁。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 規則 v1 紙上交易（不下單）"}}


# ------------------------------------------------------------------ 各國危機雷達（網站每次建置算好的 country_risk.json；規則在 wsb/data/country_risk.py）
COUNTRY = "https://wallstreet-sentinel.pages.dev/country_risk.json"
CR_EVERY = 1800


async def country_json(sess: aiohttp.ClientSession) -> Dict:
    try:
        async with sess.get(COUNTRY, timeout=aiohttp.ClientTimeout(total=20)) as r:
            return (await r.json(content_type=None)) or {} if r.status < 300 else {}
    except Exception as e:  # noqa: BLE001
        log.info("country risk: %s", e)
        return {}


def country_embed(a: Dict, d: Dict, lines: List[str]) -> Dict:
    rows, sp = d.get("rows") or [], d.get("spread") or {}
    red = [r["zh"] for r in rows if r.get("light") == 2]
    yel = [r["zh"] for r in rows if r.get("light") == 1]
    weak = sp.get("weak") or []
    state = {"spread": "壓力正在擴散", "local": "目前還是個別國家的事", "calm": "整體平靜"}.get(sp.get("state"), "")
    return {"title": (("🔴 " if a.get("lv", 1) >= 2 else "🟠 ") + a["title"])[:256], "color": 0xE5484D if a.get("lv", 1) >= 2 else 0xD97706,
            "url": "https://wallstreet-sentinel.pages.dev/",
            "description": ("一句話看懂：" + a["text"] + "\n"
                            + f'・目前燈號：紅燈 {"、".join(red) or "沒有"}；黃燈 {"、".join(yel) or "沒有"}。{state}。\n'
                            + f'・過去一個月貨幣貶超過 3% 的有 {len(weak)} 國' + (f'（{"、".join(weak)}）' if weak else "") + "。\n"
                            + ("\n".join(lines) + "\n" if lines else "")
                            + "新興市場出事會經由三條路傳到美股和台股：外國銀行的放款、基金被贖回時一起賣台股韓股、全球需求變少。"
                              "燈號是常用的警戒線，不是預測；完整表格在網站「全球行情」。")[:4000],
            "footer": {"text": "Yahoo／國際貨幣基金／世界銀行／FRED · WallStreet Sentinel · 不構成投資建議"}}



async def health_check(now: float, news: Dict, sent: Dict[str, float]):
    from tools import sys_health as SH
    return await SH.check(now, news, sent)


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
    t0 = time.monotonic()
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
    done: Dict[str, float] = ({k: now for k in acc} if isinstance(acc, list)
                              else {k: v for k, v in acc.items() if now - float(v) < (40 if k.startswith("cr:") else 120 if k.startswith("fiscal:") else 10) * 86400})   # cr: per month; fiscal: per deadline / limit
    bsent: Dict[str, float] = {k: v for k, v in (mem.get("burst") or {}).items() if now - float(v) < 3 * 86400}
    prev = float(mem.get("ts") or 0)
    health = mem.get("health") or {}
    hsent: Dict[str, float] = dict(health.get("sent") or {})
    site_seen: Dict[str, float] = {k: v for k, v in (mem.get("site") or {}).items() if now - float(v) < 30 * 86400}
    S = {"cr_ts": float(mem.get("cr_ts") or 0), "st_ts": float(mem.get("st_ts") or 0), "site_ts": float(mem.get("site_ts") or 0),
         "fi_ts": float(mem.get("fi_ts") or 0), "pp_ts": float(mem.get("pp_ts") or 0), "th_ts": float(mem.get("th_ts") or 0), "tb_ts": float(mem.get("tb_ts") or 0), "ta_ts": float(mem.get("ta_ts") or 0), "ff_ts": float(mem.get("ff_ts") or 0), "ko_ts": float(mem.get("ko_ts") or 0), "ru_ts": float(mem.get("ru_ts") or 0), "bi_ts": float(mem.get("bi_ts") or 0), "es_ts": float(mem.get("es_ts") or 0),
         "ts": int(now), "skipped": [], "hold": [h for h in mem.get("hold") or [] if now - float(h.get("first") or 0) < 6 * 3600]}
    pend: Dict[str, float] = {k: v for k, v in (mem.get("pend") or {}).items() if now - float(v) < 86400}
    quiet: Dict = dict(mem.get("quiet") or {})
    age = bot_age_min() if CLOUD else None
    cold = CLOUD and not PUSHED.exists()                   # the cloud's very first run: remember what is there, send nothing
    L: Dict = {"d": None, "fail": False}

    def save() -> None:
        """Written after every section, not only at the end: if Windows ends the run at its 2-minute limit, what was
        already sent is on disk and is not sent a second time."""
        health["sent"] = hsent
        tmp = PUSHED.with_suffix(".tmp")
        tmp.write_text(json.dumps({"acc": done, "burst": bsent, "health": health, "site": site_seen, "cr_ts": S["cr_ts"],
                                   "st_ts": S["st_ts"], "site_ts": S["site_ts"], "fi_ts": S["fi_ts"], "ff_ts": S["ff_ts"], "ko_ts": S["ko_ts"], "ru_ts": S["ru_ts"], "bi_ts": S["bi_ts"], "es_ts": S["es_ts"], "pp_ts": S["pp_ts"], "th_ts": S["th_ts"], "tb_ts": S["tb_ts"], "ta_ts": S["ta_ts"], "ts": S["ts"], "pend": pend, "hold": S["hold"],
                                   "quiet": quiet}), encoding="utf-8")
        tmp.replace(PUSHED)

    def left(name: str) -> bool:
        if time.monotonic() - t0 < BUDGET:
            return True
        S["skipped"].append(name)
        return False

    try:
        wl = watch_list()
        st = await asyncio.wait_for(SOF.refresh(wl, now=now, due=earn_due_ciks(wl, now)), 55)
    except Exception as e:  # noqa: BLE001  (SEC unreachable: the other checks still run; nothing is marked, so nothing is lost)
        log.warning("SEC refresh failed: %s", e)
        st = {}
    todo = sorted((a for a in st.get("alerts") or [] if a["acc"] not in done and now - a["ts"] < MAX_AGE
                   and a.get("item") != "13D/A"),          # an update to an old 13D is listed on the site only
                  key=lambda a: (-severity(a), -a["ts"]))
    sent = 0
    async with aiohttp.ClientSession() as sess:
        dm = None

        async def want(key: str, fam: str = "", private: bool = False) -> str:
            """'go' = send it now · 'known' = it is already in Discord (the other machine sent it) · 'wait' = not yet.
            The channel is read once per run, and only when there is something to send."""
            nonlocal dm
            if private:                                    # holdings-only messages exist on the home PC alone
                return "wait" if CLOUD else "go"
            if cold:
                return "known"
            if L["d"] is None and not L["fail"]:
                if now < 1.7e9:                            # a test clock: never read the live channel
                    L["d"] = {}
                else:
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    L["d"] = await ledger(sess, chan or dm or "")
                    L["fail"] = L["d"] is None
            if L["fail"]:                                  # Discord unreadable: the PC sends as before, the cloud never sends blind
                return "wait" if CLOUD else "go"
            if key in L["d"]:
                pend.pop(key, None)
                return "known"
            if CLOUD and now - pend.setdefault(key, now) < grace(fam, age):
                return "wait"
            return "go"

        nj = await news_json(sess)
        cbs = [x for x in nj.get("items") or [] if x.get("kind") == "cb" and "cb:" + x["u"] not in done]
        try:                                               # 離線補課：先講漏掉什麼，較新的再照常通知
            if not CLOUD and prev and now - prev >= CATCH_GAP:
                late, late_cb = [], []
                for a in st.get("alerts") or []:
                    if a["acc"] not in done and prev < a["ts"] and now - a["ts"] >= MAX_AGE and a.get("item") != "13D/A":
                        if await want(a["acc"], "sec") == "known":      # the cloud sent it while this PC was off
                            done[a["acc"]] = now
                        else:
                            late.append(a)
                for x in cbs:
                    if prev < x["ts"] and now - x["ts"] >= MAX_AGE:
                        if await want("cb:" + x["u"], "cb") == "known":
                            done["cb:" + x["u"]] = now
                        else:
                            late_cb.append(x)
                if late or late_cb or now - prev >= 3 * 3600:
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", catchup_embed(prev, now, sorted(late, key=lambda a: -severity(a)), late_cb, await gap_moves(sess, prev))):
                        sent += 1
                        for a in late:
                            done[a["acc"]] = now
                        for x in late_cb:
                            done["cb:" + x["u"]] = now
                    else:
                        S["ts"] = int(prev)                # not delivered: keep the old stamp so the next run tries the catch-up again
        except Exception as e:  # noqa: BLE001
            log.warning("catch-up failed: %s", e)
            S["ts"] = int(prev)
        save()
        for a in todo:                                     # SEC 重大申報：最嚴重的先送
            if not left("sec"):
                break
            try:
                w = await want(a["acc"], "sec")
                if w != "go":
                    if w == "known":
                        done[a["acc"]] = now
                    continue
                lines = await impact(sess, a["sym"], a["zh"])
                e = embed_of(a, lines)
                if not chan:                               # no alert channel set (same as the bot): everything goes to the DM
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", e, a["acc"]):
                    done[a["acc"]] = now
                    sent += 1
                    note_lag("sec", a["ts"], time.time())
                    save()
                    if chan and severity(a) >= 3:          # the worst ones also reach the owner directly
                        dm = dm or await dm_channel(sess)
                        if dm:
                            await post(sess, dm, e)
            except Exception as e:  # noqa: BLE001  (one bad filing must not stop the rest of the run)
                log.warning("SEC alert %s failed: %s", a.get("acc"), e)
            await asyncio.sleep(1)
        try:                                               # 央行非例行動作、日圓急升
            for x in cbs if left("cb") else []:
                if now - x["ts"] >= MAX_AGE or "cb:" + x["u"] in done:
                    continue
                w = await want("cb:" + x["u"], "cb")
                if w != "go":
                    if w == "known":
                        done["cb:" + x["u"]] = now
                    continue
                e = cb_embed(x, await market_now(sess, ["利率", "匯率", "美股", "黃金"], now))
                if not chan:
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", e, "cb:" + x["u"]):
                    done["cb:" + x["u"]] = now
                    sent += 1
                    note_lag("cb", x["ts"], time.time())
                    if chan:
                        dm = dm or await dm_channel(sess)
                        if dm:
                            await post(sess, dm, e)
            a = await yen_jump(sess, now)
            if a and f'yen:{a["day"]}' not in done:
                w = await want(f'yen:{a["day"]}', "yen")
                if w == "known":
                    done[f'yen:{a["day"]}'] = now
                if w == "go":
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", yen_embed(a, await market_now(sess, ["美股", "科技", "利率"], now)), f'yen:{a["day"]}'):
                        done[f'yen:{a["day"]}'] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("central bank check failed: %s", e)
        save()
        try:                                               # 族群急跌（same rules as the site's live bar）
            for a in await sector_alerts(sess, now) if left("sector") else []:
                key = f'sector:{a["sym"]}:{a["day"]}:{a["lv"]}'
                if key in done or (a["lv"] == 1 and f'sector:{a["sym"]}:{a["day"]}:2' in done):
                    continue
                w = await want(key, "sector")
                if w != "go":
                    if w == "known":
                        done[key] = now
                    continue
                if not chan:
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", sector_embed(a), key):
                    done[key] = now
                    sent += 1
                await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("sector check failed: %s", e)
        save()
        try:                                               # 個股大動：一天最多 3 則個別通知＋1 則彙總（每 5 分鐘看一次）
            if now - S["st_ts"] >= STOCK_EVERY and left("stock"):
                from wsb.analytics import stock_shock as ST
                S["st_ts"] = now
                allhits = await stock_alerts(sess, now, nj.get("items") or [])
                for mk, pre in (("us", "stock"), ("tw", "stocktw")):   # each market keeps its own daily count
                    hits = [a for a in allhits if a.get("mk", "us") == mk]
                    day = hits[0]["day"] if hits else ""
                    n_day = sum(1 for k in done if k.startswith(f"{pre}:{day}:"))
                    for a in hits:
                        key = f'{pre}:{a["day"]}:{a["sym"]}'
                        if key in done or n_day >= ST.DAY_CAP:
                            continue
                        w = await want(key, "stock")
                        if w != "go":
                            if w == "known":
                                done[key] = now
                                n_day += 1
                            continue
                        if not chan:
                            dm = dm or await dm_channel(sess)
                        imp = await (stock_tw_impact if mk == "tw" else impact)(sess, a["sym"], a["zh"])
                        if await post(sess, chan or dm or "", stock_embed(a, imp), key):
                            done[key] = now
                            n_day += 1
                            sent += 1
                            save()
                        await asyncio.sleep(1)
                    rest = [a for a in hits if f'{pre}:{a["day"]}:{a["sym"]}' not in done]
                    mkey = f"{pre}many:{day}"
                    if rest and day and mkey not in done and (n_day >= ST.DAY_CAP or not CLOUD):
                        w = await want(mkey, "stock")
                        if w == "known":
                            done[mkey] = now
                        if w == "go":
                            if not chan:
                                dm = dm or await dm_channel(sess)
                            if await post(sess, chan or dm or "", stock_many_embed(rest, len(hits)), mkey):
                                done[mkey] = now
                                sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("stock check failed: %s", e)
        save()
        try:                                               # 持股晚報、財報出爐、累積跌幅：只私訊擁有者（11-17 移到前面：慢的一輪也不會被擠到下一輪）
            if not CLOUD and left("holdings"):
                sent += await holdings_run(sess, now, {"alerts": st.get("alerts") or [], "earn": st.get("earn") or [], "bursts": nj.get("bursts") or []})
        except Exception as e:  # noqa: BLE001
            log.warning("holdings watch failed: %s", e)
        save()
        try:                                               # 美國商務部 BIS 新聞稿（出口管制宣布的當下；11-17 新增）
            if now - S["bi_ts"] >= BIS_EVERY and now > 1.7e9 and left("bis"):
                from wsb.data import bis_news as BN
                S["bi_ts"] = now
                d = await asyncio.wait_for(BN.refresh(now=now), 45)
                for a in BN.alerts(d, now):
                    if a["key"] in done:
                        continue
                    w = await want(a["key"], "bis")
                    if w != "go":
                        if w == "known":
                            done[a["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    lines = await market_now(sess, ["科技", "台股", "美股"], now)
                    try:
                        lines += await impact(sess, "NVDA", "輝達")
                    except Exception:  # noqa: BLE001
                        pass
                    if await post(sess, chan or dm or "", bis_embed(a, lines), a["key"]):
                        done[a["key"]] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("BIS check failed: %s", e)
        save()
        try:                                               # 台股重大訊息（即時，官方 RSS）：一家公司一則；只有持股才有的公司只私訊
            if left("mops"):
                from wsb.data import mops_rt as MR
                mo = await mops_new(sess, now)
                for g in mo["groups"]:
                    if not left("mops"):
                        break
                    private = g[0]["code"] in mo["priv"]
                    go = []
                    for x in g:
                        w = await want("mops:" + x["key"], "mops", private)
                        if w == "go":
                            go.append(x)
                        elif w == "known":
                            mo["sent"][x["key"]] = now
                            MR.save(mo["sent"], now)
                    g = go
                    if not g:
                        continue
                    top = max(g, key=lambda x: (x["lv"], x["ts"]))
                    if private or not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, (dm if private else chan or dm) or "", mops_embed(g, await tw_impact(sess, top["code"], top["zh"], now)),
                                  None if private else ["mops:" + x["key"] for x in g]):
                        for x in g:
                            mo["sent"][x["key"]] = now
                        MR.save(mo["sent"], now)
                        sent += 1
                        note_lag("mops", min(x["ts"] for x in g), time.time())
                    await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("Taiwan material news check failed: %s", e)
        try:                                               # 多家媒體同時報導（3 家以上）＋影響
            for b in burst_todo(nj.get("bursts") or [], bsent, now) if left("burst") else []:
                w = await want("burst:" + b["key"], "burst")
                if w != "go":
                    if w == "known":
                        bsent[b["key"]] = now
                    continue
                lines = (await impact(sess, b["sym"], b["label"].split("（")[0]) if b.get("kind") == "co" and b.get("sym")
                         else await market_now(sess, b.get("tags") or [], now))
                if not chan:
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", burst_embed(b, lines), "burst:" + b["key"]):
                    bsent[b["key"]] = now
                    sent += 1
                    save()
                await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("burst check failed: %s", e)
        try:                                               # 台指期夜盤急跌
            a = await tx_night(sess, now) if left("txnight") else None
            if a:
                key = f'txnight:{a["day"]}:{a["lv"]}'
                if key not in done and not (a["lv"] == 1 and f'txnight:{a["day"]}:2' in done):
                    w = await want(key, "txnight")
                    if w == "known":
                        done[key] = now
                    if w == "go":
                        if not chan:
                            dm = dm or await dm_channel(sess)
                        if await post(sess, chan or dm or "", await tx_embed(sess, a), key):
                            done[key] = now
                            sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("night futures check failed: %s", e)
        save()
        try:                                               # 各國危機雷達：新紅燈、多國貨幣一起貶、開始擴散（各一個月一次）
            if now - S["cr_ts"] >= CR_EVERY and left("country"):
                S["cr_ts"] = now
                cd = await country_json(sess)
                for a in cd.get("alerts") or []:
                    if a["key"] in done:
                        continue
                    w = await want(a["key"], "cr")
                    if w != "go":
                        if w == "known":
                            done[a["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", country_embed(a, cd, await market_now(sess, ["匯率", "美股", "利率", "台股"], now)), a["key"]):
                        done[a["key"]] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("country risk check failed: %s", e)
        try:                                               # 台股：開盤前紅燈、新一個月營收、明天的自辦法說
            if now - S["ta_ts"] >= TWAL_EVERY and now > 1.7e9 and left("twal"):
                S["ta_ts"] = now
                for a in twal_todo(await twal_json(sess), done, now):
                    w = await want(a["key"], "twal")
                    if w != "go":
                        if w == "known":
                            done[a["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", twal_embed(a), a["key"]):
                        done[a["key"]] = now
                        sent += 1
                    await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("tw alerts check failed: %s", e)
        try:                                               # 台股大型公司宣布庫藏股（一天最多 3 則）
            if now - S["tb_ts"] >= TB_EVERY and now > 1.7e9 and left("buyback"):
                S["tb_ts"] = now
                for x in buyback_todo(await twcorp_json(sess), done, now)[:TB_DAY_CAP]:
                    w = await want(x["key"], "buyback")
                    if w != "go":
                        if w == "known":
                            done[x["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", buyback_embed(x), x["key"]):
                        done[x["key"]] = now
                        sent += 1
                    await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("buyback check failed: %s", e)
        try:                                               # 主線追蹤：升溫或官方新文件（每條主線一天最多一則）
            if now - S["th_ts"] >= TH_EVERY and now > 1.7e9 and left("threads"):
                S["th_ts"] = now
                for th in threads_todo(await threads_json(sess), done, now)[:2]:
                    w = await want(th["key"], "thread")
                    if w != "go":
                        if w == "known":
                            done[th["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    lines = await market_now(sess, TH_TAGS.get(str(th.get("id")), []), now)
                    if await post(sess, chan or dm or "", thread_embed(th, lines), th["key"]):
                        done[th["key"]] = now
                        sent += 1
                    await asyncio.sleep(1)
        except Exception as e:  # noqa: BLE001
            log.warning("threads check failed: %s", e)
        try:                                               # 台股規則 v1 紙上交易：每筆紙上成交一則（一天最多 5 則）
            if now - S["pp_ts"] >= PAPER_EVERY and now > 1.7e9 and left("paper"):
                S["pp_ts"] = now
                for e in paper_todo(await paper_json(sess), done, now):
                    w = await want(e["key"], "paper")
                    if w != "go":
                        if w == "known":
                            done[e["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", paper_embed(e), e["key"]):
                        done[e["key"]] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("paper ledger check failed: %s", e)
        try:                                               # 政府撥款到期、債務上限（各階段一次）
            if now - S["fi_ts"] >= FISCAL_EVERY and now > 1.7e9 and left("fiscal"):
                from wsb.data import us_fiscal as USF
                S["fi_ts"] = now
                v = USF.view(await asyncio.wait_for(USF.refresh(), 60))
                for a in USF.alerts(v):
                    if a["key"] in done:
                        continue
                    w = await want(a["key"], "fiscal")
                    if w != "go":
                        if w == "known":
                            done[a["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", fiscal_embed(a, v, await market_now(sess, ["利率", "美股"], now)), a["key"]):
                        done[a["key"]] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("fiscal check failed: %s", e)
        try:                                               # 網站警示補位：機器人沒有對應通知的，或機器人停了的時候全部代送
            if CLOUD:                                      # no heartbeat file in the cloud: go by the bot's last site build
                alive = age is None or age < BOT_QUIET_MIN
            else:
                from tools import sys_health as SH
                hb = SH.heartbeat_age(now)
                alive = hb is not None and hb < SH.BOT_DOWN_S
            ok = left("site")
            if ok and now - S["site_ts"] >= SITE_EVERY:
                S["site_ts"] = now
                S["hold"] += [{"x": x, "first": now} for x in site_todo(await site_alerts_json(sess, now), site_seen, now, alive)]
            ready, keep = [], []
            for h in S["hold"] if ok else []:
                w = await want("site:" + h["x"]["key"], "site")
                if w == "go":
                    ready.append(h)
                elif w == "wait":
                    keep.append(h)
            if ready:
                if not chan:
                    dm = dm or await dm_channel(sess)
                if await post(sess, chan or dm or "", site_embed([h["x"] for h in ready], alive), ["site:" + h["x"]["key"] for h in ready]):
                    sent += 1
                else:
                    keep += ready                          # not delivered: offered again on the next run
            if ok:
                S["hold"] = keep
        except Exception as e:  # noqa: BLE001
            log.warning("site alert check failed: %s", e)
        save()
        try:                                               # 系統健康（A1）：每 10 分鐘看一次，有新問題才私訊擁有者
            if CLOUD and quiet_due(quiet, age, now):          # 雲端：家裡電腦超過 60 分鐘沒動靜，說一聲（一次停機一則）
                dm = dm or await dm_channel(sess)
                if dm and await post(sess, dm, quiet_embed(age)):
                    quiet.update(ts=now, up=False)
                    sent += 1
            if not CLOUD and now - float(health.get("ts") or 0) >= HEALTH_EVERY and left("health"):
                new, open_n = await health_check(now, nj, hsent)
                health = {"ts": now, "sent": hsent}
                if new:
                    from tools import sys_health as SH
                    dm = dm or await dm_channel(sess)
                    if dm and await post(sess, dm, SH.embed(new, open_n)):
                        sent += 1
                        for i in new:
                            hsent[i["key"]] = now
        except Exception as e:  # noqa: BLE001
            log.warning("health check failed: %s", e)
        save()
        # 2026-11-16: the slow, low-urgency official-data checks run last, so a slow SEC / Yahoo day never pushes
        # Taiwan material news, bursts, night futures or the holdings messages to the next run
        try:                                               # 被迫進出的錢（指數調整日前一天、標普趨勢翻轉、波動控制比重驟降）
            if now - S["ff_ts"] >= FORCED_EVERY and now > 1.7e9 and left("forced"):
                from wsb.data import forced_flows as FF
                from wsb.data import exchange_cal as XC
                S["ff_ts"] = now
                await asyncio.wait_for(XC.refresh(), 40)
                v = FF.view(await asyncio.wait_for(FF.refresh(), 90))
                tpe = time.gmtime(now + 8 * 3600)
                today = date(tpe.tm_year, tpe.tm_mon, tpe.tm_mday)
                for a in FF.alerts(v, today):
                    if a["key"] in done:
                        continue
                    if a["kind"] == "event" and a["ev"]["date"] > today.isoformat() and tpe.tm_hour < 18:
                        continue                           # the evening before (Taipei), not in the small hours
                    w = await want(a["key"], "forced")
                    if w != "go":
                        if w == "known":
                            done[a["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    tags = ["台股", "美股"] if a.get("ev", {}).get("kind") in ("msci", "tw50") else ["美股", "利率"]
                    if await post(sess, chan or dm or "", forced_embed(a, v, await market_now(sess, tags, now)), a["key"]):
                        done[a["key"]] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("forced flows check failed: %s", e)
        try:                                               # 韓國出口快報（公布後兩天內一次）
            tpe = time.gmtime(now + 8 * 3600)
            if tpe.tm_mday in (1, 2, 11, 12, 21, 22) and now - S["ko_ts"] >= KOREA_EVERY and now > 1.7e9 and left("korea"):
                from wsb.data import korea_exports as KE
                S["ko_ts"] = now
                v = KE.view(await asyncio.wait_for(KE.refresh(force=True, per_run=6), 60))
                for a in KE.alerts(v, date(tpe.tm_year, tpe.tm_mon, tpe.tm_mday)):
                    if a["key"] in done:
                        continue
                    w = await want(a["key"], "korea")
                    if w != "go":
                        if w == "known":
                            done[a["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    if await post(sess, chan or dm or "", korea_embed(a, await market_now(sess, ["台股", "科技"], now)), a["key"]):
                        done[a["key"]] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("korea exports check failed: %s", e)
        try:                                               # 法院與監管的決定（有市場主題、30 小時內第一次看到的）
            if now - S["ru_ts"] >= RULINGS_EVERY and now > 1.7e9 and left("rulings"):
                from wsb.data import rulings as RL
                S["ru_ts"] = now
                d = await asyncio.wait_for(RL.refresh(), 60)
                for a in RL.alerts(d, now):
                    if a["key"] in done:
                        continue
                    w = await want(a["key"], "rulings")
                    if w != "go":
                        if w == "known":
                            done[a["key"]] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    tags = {"^TNX": ["利率", "美股"], "^NDX": ["美股", "科技"]}.get(a["item"].get("sym"), ["美股", "利率"])
                    if await post(sess, chan or dm or "", ruling_embed(a, await market_now(sess, tags, now)), a["key"]):
                        done[a["key"]] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("rulings check failed: %s", e)
        try:                                               # 大公司財報前一晚（市值 5,000 億美元以上）
            if now - S["es_ts"] >= EARNSOON_EVERY and now > 1.7e9 and left("earnsoon"):
                import types
                from datetime import datetime, timezone
                from tools import site_events as SEV
                S["es_ts"] = now
                due_rows = earnsoon_due(SEV.earn_events(types.SimpleNamespace(sx={}), datetime.fromtimestamp(now, timezone.utc)), now)
                pv_items = {}
                if due_rows:
                    try:
                        async with sess.get(PREVIEW_RAW, timeout=aiohttp.ClientTimeout(total=20)) as r_:
                            pv_items = {(x.get("sym"), x.get("date")): x for x in (json.loads(await r_.text()).get("items") or [])} if r_.status == 200 else {}
                    except Exception as e:  # noqa: BLE001
                        log.info("preview feed: %s", e)
                for r in due_rows:
                    key = f"earnsoon:{r['sym']}:{r['next'][:10]}"
                    if key in done:
                        continue
                    w = await want(key, "earnsoon")
                    if w != "go":
                        if w == "known":
                            done[key] = now
                        continue
                    if not chan:
                        dm = dm or await dm_channel(sess)
                    lines = await impact(sess, r["sym"], r["zh"].split("財報")[0], live=False)
                    if await post(sess, chan or dm or "", earnsoon_embed(r, lines[1:], pv_items.get((r["sym"], r["next"][:10]))), key):
                        done[key] = now
                        sent += 1
        except Exception as e:  # noqa: BLE001
            log.warning("earnings-soon check failed: %s", e)
    save()
    try:
        s = await http.session()
        await s.close()
    except Exception:  # noqa: BLE001
        pass
    if S["skipped"]:
        log.warning("out of time after %.0f s: %s left for the next run", time.monotonic() - t0, ", ".join(S["skipped"]))
    log.info("SEC push: %d sent (%.0f s)%s", sent, time.monotonic() - t0,
             f" · cloud, bot last seen {age:.0f} min ago, {len(pend)} waiting{', first run: remembered only' if cold else ''}"
             if CLOUD and age is not None else (" · cloud" if CLOUD else ""))
    return sent


if __name__ == "__main__":
    if CLOUD:                                              # GitHub Actions: the log is the job's (public) output, no file
        logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, filename=str(DATA_DIR / "sec_push.log"), format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_once())
