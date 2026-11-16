"""系統健康推播（A1，2026-11-14）：東西壞了卻沒人知道，是最容易漏掉重要訊息的原因。由 tools/sec_push.py 每 10 分鐘檢查一次，
有問題才私訊擁有者，同一件事 24 小時內只說一次。不花 AI 額度，不經過 wsb/bot/app.py。

檢查五件事（全部用本機已經有的紀錄，加一次 GitHub 查詢）：
  1. 機器人還活著嗎：data_cache/heartbeat.json 超過 20 分鐘沒更新 → 馬上說（機器人停了，持股與行情警報都會停）
  2. 同一個資料來源連續出錯：data_cache/sentinel.log 過去 24 小時裡，同一個模組的同一種錯誤在 18 個以上的小時都出現
  3. 網站建置：最近一次成功超過 4 小時，或最近 3 次都失敗
  4. 即時新聞：/api/news 回應的來源少於 15 個
  5. 本機收盤價：超過 4 天沒有新的一天（週末、連假算進去）
  6. 通知慢了多久（2026-11-15）：有「事情發生時間」的通知（SEC 申報、央行公告、台股重大訊息、機器人的官方事件），
     最近 3 天從發生到送出的時間中位數 ≥ 45 分鐘 → 說出來。起因：台股重大訊息晚了 12 小時、連續幾週都沒有人發現。
每一項都用白話寫「哪裡壞了、影響什麼」。只描述狀況，不會自己去修。"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from wsb.config import DATA_DIR

log = logging.getLogger("sys_health")
BOT_DOWN_S = 20 * 60
LOG_HOURS, LOG_MIN_HOURS = 24, 18
BUILD_OK_H, BUILD_FAILS = 4.0, 3
NEWS_MIN = 15
PRICE_DAYS = 4
RESEND_S = 24 * 3600
# 模組 → 白話：是什麼、壞了影響哪裡。沒列到的就直接寫模組名稱
WHAT = (("wsb.data.fred", "聯準會資料庫（FRED）", "總經卡片（物價、就業、利差）可能停在舊資料"),
        ("wsb.data.econcal", "財經日曆", "數據公布時間與結果可能沒更新"),
        ("wsb.data.earnings", "財報日曆", "財報日期與結果可能沒更新，財報前後的私訊會受影響"),
        ("wsb.data.options", "選擇權資料（CBOE）", "財報隱含波動與 Gamma 相關卡片可能缺資料"),
        ("wsb.data.taiwan", "台股官方資料（證交所／期交所）", "台灣頁面的三大法人、期貨資料可能沒更新"),
        ("wsb.data.stocks", "個股價格", "部分股票的價格可能缺漏，連動與跌幅計算會少算"),
        ("wsb.data.market", "行情報價", "即時行情與異常波動警報可能不準"),
        ("wsb.data.sec", "美國證交會資料", "申報相關的卡片與警報可能延遲"),
        ("wsb.data.edgar", "美國證交會資料", "申報相關的卡片與警報可能延遲"),
        ("wsb.ai", "AI 解讀", "卡片上的 AI 文字不會更新（數字不受影響）"),
        ("wsb.news", "新聞抓取", "機器人的新聞警報可能漏掉"),
        ("wsb.site_trigger", "網站建置觸發", "網站可能沒有照時間重新產生"),
        ("wsb.bot", "Discord 機器人本身", "警報可能送不出去"))
IGNORE = ("asyncio",)                                   # Windows 連線關閉時的雜訊，不影響資料


def what_of(logger: str) -> Dict[str, str]:
    for k, zh, eff in WHAT:
        if logger.startswith(k):
            return {"zh": zh, "effect": eff}
    return {"zh": logger, "effect": "影響範圍要看紀錄檔才知道"}


def log_issues(lines: List[str], now: float, hours: int = LOG_HOURS, min_hours: int = LOG_MIN_HOURS) -> List[Dict]:
    """The same error from the same module in at least `min_hours` different hours of the last `hours`: [{key, logger, hours, n, example}]."""
    by: Dict[str, Dict] = {}
    for line in lines:
        m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ (WARNING|ERROR) ([^:]+): (.*)", line)
        if not m:
            continue
        ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
        lg = m.group(3).strip()
        if ts < now - hours * 3600 or ts > now or lg.startswith(IGNORE):
            continue
        k = lg + "｜" + re.sub(r"[\d.]+", "#", m.group(4))[:60]
        d = by.setdefault(k, {"key": k, "logger": lg, "slots": set(), "n": 0, "example": m.group(4)[:160]})
        d["slots"].add(int(ts // 3600))
        d["n"] += 1
    out = [{"key": d["key"], "logger": d["logger"], "hours": len(d["slots"]), "n": d["n"], "example": d["example"]}
           for d in by.values() if len(d["slots"]) >= min_hours]
    return sorted(out, key=lambda d: -d["n"])


def read_tail(path: Path, n: int = 60000) -> List[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()[-n:]
    except OSError:
        return []


def heartbeat_age(now: float) -> Optional[float]:
    try:
        return now - float(json.loads((DATA_DIR / "heartbeat.json").read_text(encoding="utf-8")).get("ts") or 0)
    except (OSError, ValueError):
        return None


def build_issue(runs: List[Dict], now: float) -> Optional[str]:
    """runs: GitHub workflow runs, newest first.  A sentence when the site has not built for 4 hours or the last 3 all failed."""
    done = [r for r in runs if r.get("status") == "completed"]
    if not done:
        return None
    if len(done) >= BUILD_FAILS and all(r.get("conclusion") not in ("success", "cancelled") for r in done[:BUILD_FAILS]):
        return f"網站建置最近 {BUILD_FAILS} 次都失敗：網站停在舊資料，新功能也上不去。"
    ok = [r for r in done if r.get("conclusion") == "success"]
    if ok:
        try:
            age = (now - datetime.fromisoformat(str(ok[0]["updated_at"]).replace("Z", "+00:00")).timestamp()) / 3600
        except (KeyError, ValueError):
            return None
        if age >= BUILD_OK_H:
            return f"網站已經 {age:.0f} 小時沒有成功重新產生（平常每小時一次）：頁面上的數字是 {age:.0f} 小時前的。"
    return None


def price_age_days(now: float) -> Optional[int]:
    try:
        import pandas as pd
        h = pd.read_pickle(DATA_DIR / "history_close.pkl")
        v = h["^GSPC"].dropna()
        return (datetime.fromtimestamp(now).date() - v.index[-1].date()).days
    except Exception:  # noqa: BLE001
        return None


def collect(now: float, lines: List[str], hb_age: Optional[float], runs: List[Dict], n_news: Optional[int], px_days: Optional[int]) -> List[Dict]:
    """Every open problem as {key, text, urgent}."""
    out: List[Dict] = []
    if hb_age is not None and hb_age >= BOT_DOWN_S:
        out.append({"key": "bot_down", "urgent": True,
                    "text": f"**機器人停了**：已經 {hb_age / 60:.0f} 分鐘沒有心跳。持股警報、異常波動、台股重大訊息都會停；SEC、族群急跌、持股晚報這支程式還在跑。"})
    by_mod: Dict[str, List[Dict]] = {}
    for d in log_issues(lines, now):
        by_mod.setdefault(d["logger"], []).append(d)
    for lg, ds in by_mod.items():                          # one line per module, however many of its series fail
        w, d = what_of(lg), ds[0]
        out.append({"key": "log:" + lg, "urgent": False,
                    "text": f'**{w["zh"]}**：過去 24 小時有 {max(x["hours"] for x in ds)} 個小時都在出錯（{len(ds)} 種錯誤，共 {sum(x["n"] for x in ds)} 次）。'
                            f'{w["effect"]}。例如：`{d["example"][:90]}`'})
    b = build_issue(runs, now)
    if b:
        out.append({"key": "build", "urgent": True, "text": "**網站**：" + b})
    if n_news is not None and n_news < NEWS_MIN:
        out.append({"key": "news", "urgent": False,
                    "text": f"**即時新聞**：只有 {n_news} 個來源有回應（平常 24 個）。多家媒體同時報導的偵測會變鈍。"})
    if px_days is not None and px_days > PRICE_DAYS:
        out.append({"key": "prices", "urgent": True,
                    "text": f"**本機收盤價**：已經 {px_days} 天沒有新資料。持股跌幅、晚報、早安摘要的數字會是舊的。"})
    return out


LAG_DAYS, LAG_MIN_N, LAG_LIMIT_S = 3, 5, 45 * 60
LAG_ZH = {"sec": "SEC 重大申報", "cb": "央行公告", "mops": "台股重大訊息", "SEC 公告": "機器人的 SEC 公告", "Fed 公告": "聯準會公告"}
# 機器人的整批來源已經有更快的即時路徑（tools/sec_push.py）在送，慢是已知的，不重複提醒
FASTER = {"台股重大訊息": "mops"}


def lag_issues(rows: List[Dict], now: float) -> List[Dict]:
    """rows: [{k: kind, ev: when it happened, at: when the message went out}].  A kind whose median delay over the last
    3 days (at least 5 messages) is 45 minutes or more: the alerts arrive, but too late to be called timely."""
    by: Dict[str, List[float]] = {}
    for r in rows:
        try:
            if now - float(r["at"]) <= LAG_DAYS * 86400 and float(r["at"]) >= float(r["ev"]):
                by.setdefault(str(r["k"]), []).append(float(r["at"]) - float(r["ev"]))
        except (KeyError, TypeError, ValueError):
            continue
    out = []
    for k, v in by.items():
        v.sort()
        med = v[len(v) // 2]
        if len(v) >= LAG_MIN_N and med >= LAG_LIMIT_S:
            how = f"{med / 3600:.1f} 小時" if med >= 5400 else f"{med / 60:.0f} 分鐘"
            out.append({"key": "lag:" + k, "urgent": True,
                        "text": f"**通知太慢**：{LAG_ZH.get(k, k)} 最近 {LAG_DAYS} 天 {len(v)} 則，從事情發生到通知你的時間中位數是 {how}"
                                f"（最慢 {v[-1] / 3600:.1f} 小時）。消息有送到，但已經不算即時。"})
    return out


def lag_rows(now: float) -> List[Dict]:
    """This program's own delay log plus the bot's (sentinel.db event_log, read-only)."""
    rows: List[Dict] = []
    try:
        rows += json.loads((DATA_DIR / "push_lag.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    own = {r.get("k") for r in rows}
    try:
        import sqlite3
        c = sqlite3.connect(f"file:{(DATA_DIR / 'sentinel.db').as_posix()}?mode=ro", uri=True, timeout=5)
        try:
            for src, ev, sent in c.execute("select src, event_ts, sent_ts from event_log where sent_ts > ? and event_ts is not null",
                                           (now - LAG_DAYS * 86400,)):
                if FASTER.get(src) in own or (src in FASTER and (DATA_DIR / "mops_rt.json").exists()):
                    continue
                rows.append({"k": src, "ev": ev, "at": sent})
        finally:
            c.close()
    except Exception as e:  # noqa: BLE001
        log.info("lag rows: %s", e)
    return rows


def due(issues: List[Dict], sent: Dict[str, float], now: float) -> List[Dict]:
    return [i for i in issues if i["key"] not in sent or now - float(sent[i["key"]]) >= RESEND_S]


def embed(new: List[Dict], open_n: int) -> Dict:
    urgent = any(i["urgent"] for i in new)
    lead = ("一句話看懂：" + ("有東西停了，會直接影響你收到的通知或網站上的數字。" if urgent else "有資料來源連續一天都在出錯，目前靠舊資料撐著。")
            + f"目前共 {open_n} 件沒解決。")
    return {"title": ("🩺 系統健康：" + ("需要處理" if urgent else "資料來源連續出錯"))[:256], "color": 0xE5484D if urgent else 0xD97706,
            "description": (lead + "\n" + "\n".join("・" + i["text"] for i in new[:8])
                            + "\n同一件事 24 小時內不會再提醒；每日排程（10:40）會試著修。")[:4000],
            "footer": {"text": "WallStreet Sentinel · 系統健康 · 只描述狀況，不會自己修"}}


async def build_runs() -> List[Dict]:
    try:
        from wsb.site_trigger import SiteTrigger
        st = SiteTrigger()
        return await st.recent_runs() if st.enabled else []
    except Exception as e:  # noqa: BLE001
        log.info("build runs: %s", e)
        return []


PREVIEW_RAW = "https://raw.githubusercontent.com/bkhotey4/wallstreet-sentinel/main/research_feed/earn_preview.json"


async def preview_issues(now: float) -> List[Dict]:
    """A company worth ≥ $300B reports within two days and the 財報前瞻 card has no preview for it (2026-11-16: NVIDIA's
    was missing from the card and the user had to point it out)."""
    import aiohttp
    from tools.site_preview import missing_big
    try:
        days = json.loads((DATA_DIR / "earn_days.json").read_text(encoding="utf-8"))
        async with aiohttp.ClientSession() as s:
            async with s.get(PREVIEW_RAW, timeout=aiohttp.ClientTimeout(total=20)) as r:
                feed = json.loads(await r.text()) if r.status == 200 else None
    except Exception:  # noqa: BLE001
        return []
    if not feed:
        return []
    from datetime import datetime, timedelta, timezone
    today = (datetime.fromtimestamp(now, timezone.utc) - timedelta(hours=5)).date().isoformat()     # US date
    miss = missing_big(feed.get("items") or [], days, today)
    if not miss:
        return []
    names = "、".join(f"{m['name']}（{m['date'][5:].replace('-', '/')}）" for m in miss[:5])
    return [{"key": "preview:" + ",".join(m["sym"] for m in miss[:5]), "urgent": False,
             "text": f"**財報前瞻**：{names} 兩天內公布，網站上還沒有前瞻預判（每天 20:00 的分析任務沒寫到）。"}]


SITE = "https://wallstreet-sentinel.pages.dev/"
SHOWN_EVERY = 3600
PREVIEW_CARD = "財報前瞻：公布前的機率估計與成績單"


def card_text(html: str, title: str) -> str:
    """Text of the card whose heading is `title` on the built page (the last occurrence: earlier ones are the sidebar)."""
    import re
    i = html.rfind(title)
    if i < 0:
        return ""
    j = html.find("<section", i)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html[i: j if j > 0 else i + 200000]))


def shown_issues(html: str, feed: Dict, days: Dict, today: str) -> List[Dict]:
    """The other half of the 11-16 lesson: the data can be right and still not reach the page.  Every company worth ≥ $300B
    that reports in the next two days and HAS a preview must actually appear on the live card (by ticker)."""
    from tools.site_preview import missing_big
    big = missing_big([], days, today)                      # every big reporter, preview or not
    have = {str(x.get("sym", "")).upper() for x in feed.get("items") or [] if isinstance(x, dict)}
    txt = card_text(html, PREVIEW_CARD)
    if not txt:
        return [{"key": "shown:preview_card", "urgent": False, "text": "**網站自我檢查**：線上網站找不到「財報前瞻」卡。"}]
    lost = [m for m in big if m["sym"] in have and m["sym"] not in txt]
    if not lost:
        return []
    return [{"key": "shown:" + ",".join(m["sym"] for m in lost[:5]), "urgent": False,
             "text": "**網站自我檢查**：" + "、".join(f"{m['name']}（{m['date'][5:].replace('-', '/')}）" for m in lost[:5])
                     + " 有前瞻資料，但線上卡片上看不到（可能被排序或筆數上限擠掉）。"}]


AFTER_CARD = "財報後白話解讀（美股）"


def after_issues(html: str, reads: List[Dict], today: str, days: int = 5, floor_b: float = 300.0) -> List[Dict]:
    """Every US company worth ≥ $300B whose post-earnings read exists (reported in the last few days) must be on the live card."""
    from datetime import date, timedelta
    cut = (date.fromisoformat(today) - timedelta(days=days)).isoformat()
    want = {str(x["sym"]).upper(): x for x in reads if isinstance(x, dict) and x.get("sym") and x.get("one")
            and (x.get("mk") or "us") == "us" and float(x.get("mcap_b") or 0) >= floor_b and str(x.get("date") or "") >= cut}
    if not want:
        return []
    txt = card_text(html, AFTER_CARD)
    lost = [x for s_, x in want.items() if s_ not in txt]
    if not lost:
        return []
    return [{"key": "shown_after:" + ",".join(str(x["sym"]) for x in lost[:5]), "urgent": False,
             "text": "**網站自我檢查**：" + "、".join(f"{x.get('name') or x['sym']}（{str(x['date'])[5:].replace('-', '/')}）" for x in lost[:5])
                     + " 的財報後解讀已經寫好，但線上「財報後白話解讀（美股）」卡上看不到。"}]


RAW_FEED = "https://raw.githubusercontent.com/bkhotey4/wallstreet-sentinel/main/research_feed/"


def routine_issues(rows: List[Dict]) -> List[Dict]:
    """The 排程健康表 rows (tools/site_routines.rows) that are 🔴 stopped / never written, or 🟡 late — so a cloud routine that
    keeps "succeeding" without writing anything (財報後解讀 11-14→11-16: blocked sources, every run gave up) reaches the owner
    instead of sitting red on a page nobody opens.  Same key per routine and state, so each state is reported once a day."""
    out = []
    for r in rows:
        if r.get("st") not in ("stop", "never", "late"):
            continue
        age = r.get("age")
        when = "從來沒有產出" if age is None else (f"{age / 24:.1f} 天沒有更新" if age >= 48 else f"{age:.0f} 小時沒有更新")
        out.append({"key": f"routine:{r['file']}:{r['st']}", "urgent": r["st"] != "late",
                    "text": f"**排程健康**：{'🔴' if r['st'] != 'late' else '🟡'} {r['zh']} {when}（應該每 {r['every']} 小時一次）。"
                            "排程本身可能顯示成功，但沒有寫出檔案；要看執行紀錄找原因。"})
    return out


async def site_shown(now: float) -> List[Dict]:
    """Once an hour: fetch the live page and the preview feed, run shown_issues."""
    import aiohttp
    st_f = DATA_DIR / "selfcheck_site.json"
    try:
        st = json.loads(st_f.read_text(encoding="utf-8")) if st_f.exists() else {}
    except (OSError, ValueError):
        st = {}
    if now - float(st.get("ts", 0)) < SHOWN_EVERY:
        return st.get("issues") or []
    try:
        days = json.loads((DATA_DIR / "earn_days.json").read_text(encoding="utf-8"))
        async with aiohttp.ClientSession() as s:
            async with s.get(PREVIEW_RAW, timeout=aiohttp.ClientTimeout(total=20)) as r:
                feed = json.loads(await r.text()) if r.status == 200 else {}
            async with s.get(SITE, params={"v": str(int(now))}, timeout=aiohttp.ClientTimeout(total=60)) as r:
                html = await r.text() if r.status == 200 else ""
            reads = []
            for f in ("earn_after.json", "earn_after_more.json", "earn_after_rest.json"):
                async with s.get(PREVIEW_RAW.replace("earn_preview.json", f), timeout=aiohttp.ClientTimeout(total=20)) as r:
                    if r.status == 200:
                        js = json.loads(await r.text())
                        reads += js.get("items") if isinstance(js, dict) else (js or [])
    except Exception:  # noqa: BLE001
        return st.get("issues") or []
    if not html or not feed:
        return st.get("issues") or []
    from datetime import datetime, timedelta, timezone
    today = (datetime.fromtimestamp(now, timezone.utc) - timedelta(hours=5)).date().isoformat()
    issues = shown_issues(html, feed, days, today) + after_issues(html, reads, today)
    try:                                                     # 排程健康表 from the live feeds (raw GitHub, the same files the site reads)
        import tempfile
        from pathlib import Path
        from tools import site_routines as R
        tmp = Path(tempfile.mkdtemp(prefix="wsb_feeds_"))
        async with aiohttp.ClientSession() as s:
            for name, *_rest in R.EXPECT:
                async with s.get(RAW_FEED + name, timeout=aiohttp.ClientTimeout(total=20)) as r:
                    if r.status == 200:
                        (tmp / name).write_bytes(await r.read())
        issues += routine_issues(R.rows(now, tmp))
    except Exception as e:  # noqa: BLE001
        log.info("routine health: %s", e)
    st_f.write_text(json.dumps({"ts": now, "issues": issues}, ensure_ascii=False), encoding="utf-8")
    return issues


async def check(now: float, news: Dict, sent: Dict[str, float]) -> tuple:
    """(problems not reported in the last 24 hours, how many are open in all).  The caller marks them in `sent` once the message is out."""
    issues = collect(now, read_tail(DATA_DIR / "sentinel.log"), heartbeat_age(now), await build_runs(),
                     len(news.get("sources") or []) if news and news.get("sources") is not None else None, price_age_days(now))
    issues += lag_issues(lag_rows(now), now)
    issues += await preview_issues(now)
    issues += await site_shown(now)
    for k in [k for k, v in sent.items() if now - float(v) > 7 * 86400]:
        sent.pop(k, None)
    return due(issues, sent, now), len(issues)
