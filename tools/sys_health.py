"""系統健康推播（A1，2026-11-14）：東西壞了卻沒人知道，是最容易漏掉重要訊息的原因。由 tools/sec_push.py 每 10 分鐘檢查一次，
有問題才私訊擁有者，同一件事 24 小時內只說一次。不花 AI 額度，不經過 wsb/bot/app.py。

檢查五件事（全部用本機已經有的紀錄，加一次 GitHub 查詢）：
  1. 機器人還活著嗎：data_cache/heartbeat.json 超過 20 分鐘沒更新 → 馬上說（機器人停了，持股與行情警報都會停）
  2. 同一個資料來源連續出錯：data_cache/sentinel.log 過去 24 小時裡，同一個模組的同一種錯誤在 18 個以上的小時都出現
  3. 網站建置：最近一次成功超過 4 小時，或最近 3 次都失敗
  4. 即時新聞：/api/news 回應的來源少於 15 個
  5. 本機收盤價：超過 4 天沒有新的一天（週末、連假算進去）
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


async def check(now: float, news: Dict, sent: Dict[str, float]) -> tuple:
    """(problems not reported in the last 24 hours, how many are open in all).  The caller marks them in `sent` once the message is out."""
    issues = collect(now, read_tail(DATA_DIR / "sentinel.log"), heartbeat_age(now), await build_runs(),
                     len(news.get("sources") or []) if news and news.get("sources") is not None else None, price_age_days(now))
    for k in [k for k, v in sent.items() if now - float(v) > 7 * 86400]:
        sent.pop(k, None)
    return due(issues, sent, now), len(issues)
