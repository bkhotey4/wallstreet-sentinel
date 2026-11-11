"""排程健康表 (風險模型): is each cloud-AI card on the site still being written?

Every research_feed/*.json a cloud routine commits carries its own `updated` time.  The card compares that time with the
routine's schedule (EXPECT, copied from the routine's cron — configuration, not market data) and lights:
  🟢 準時   age ≤ 2 × the usual gap
  🟡 晚了   age ≤ 4 × the usual gap
  🔴 停了   older than that, or the file was never written
For US-session routines the weekend hours (Taipei Sat 08:00 → Mon 08:00) are not counted.  Backfill routines that skip the
commit when nothing is new are left out on purpose: an unchanged file there means "nothing to add", not "stopped"."""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from tools.sitekit import T, card, esc

TPE = ZoneInfo("Asia/Taipei")
FEED_DIR = Path(__file__).resolve().parents[1] / "research_feed"
# file, card name (zh, en), usual gap in hours, US-trading-days only
EXPECT = (
    ("sessions.json", "美股今天怎麼了", "US session notes", 6, True),
    ("macro_voice.json", "每日總經情勢（口播）", "Daily macro voice", 12, False),
    ("deep.json", "每日深度研判", "Daily deep read", 24, False),
    ("learn.json", "每日學習筆記", "Daily learning notes", 24, False),
    ("ai_view.json", "獨立 AI 觀察員", "AI observer", 12, False),
    ("earn_preview.json", "財報前瞻", "Earnings previews", 24, False),
    ("earn_after.json", "財報後解讀", "Post-earnings reads", 12, False),
    ("forecast.json", "一個月預判", "One-month calls", 96, False),
    ("feed.json", "學術動態", "Research feed", 168, False),
    ("industry_note.json", "產業筆記", "Industry note", 168, False),
    ("tw_note.json", "台灣每月分析筆記", "Taiwan monthly note", 31 * 24, False),
)
LIGHT = {"ok": ("🟢", "準時", "On time"), "late": ("🟡", "晚了", "Late"), "stop": ("🔴", "停了", "Stopped"),
         "never": ("🔴", "從未產出", "Never written"), "wait": ("⚪", "等第一次排程", "Waiting for first run")}
# First scheduled run (Taipei) of routines that were (re)set up and have not written their file yet (configuration,
# from the routine's cron).  Before that run + 1 day of grace a missing file is ⚪ waiting, not 🔴.
FIRST_RUN = {"tw_note.json": "2026-11-28 12:05"}
GRACE_H = 24


def parse_updated(raw) -> Optional[float]:
    """'YYYY-MM-DD HH:MM 台北', 'YYYY-MM-DDTHH:MM' or a bare date (read as 12:00 Taipei) → epoch."""
    s = str(raw or "").strip().replace("T", " ")
    for fmt, n in (("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            dt = datetime.strptime(s[:n], fmt)
            return (dt.replace(hour=12) if n == 10 else dt).replace(tzinfo=TPE).timestamp()
        except ValueError:
            continue
    return None


def _stamp(name: str, d: Dict) -> Optional[float]:
    if name == "tw_note.json":                        # the monthly note keeps its date on the newest note
        notes = [n for n in d.get("notes") or [] if isinstance(n, dict) and (n.get("date") or n.get("month"))]
        if not notes:                                 # same reading as the note card: newest by date, else month + "-28"
            return None
        n = max(notes, key=lambda n: str(n.get("date") or n.get("month")))
        return parse_updated(n.get("date") or f'{n.get("month")}-28')
    return parse_updated(d.get("updated"))


def weekday_hours(t0: float, t1: float) -> float:
    """Hours between t0 and t1 not counting the US weekend as seen from Taipei (Sat 08:00 → Mon 08:00)."""
    total, cur = 0.0, datetime.fromtimestamp(t0, TPE)
    end = datetime.fromtimestamp(t1, TPE)
    while cur < end:
        nxt = min(end, cur.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        shifted = cur - timedelta(hours=8)            # Sat 08:00 Taipei → Sat 00:00 on the shifted clock
        if shifted.weekday() < 5:
            total += (nxt - cur).total_seconds() / 3600
        cur = nxt
    return total


def status(age_h: Optional[float], every_h: float) -> str:
    if age_h is None:
        return "never"
    return "ok" if age_h <= 2 * every_h else "late" if age_h <= 4 * every_h else "stop"


def rows(now: Optional[float] = None, feed_dir: Path = FEED_DIR) -> List[Dict]:
    now = time.time() if now is None else now
    out = []
    for name, zh, en, every, us_days in EXPECT:
        ts = None
        try:
            p = feed_dir / name
            ts = _stamp(name, json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None
        except Exception:  # noqa: BLE001
            ts = None
        age = None if ts is None else (weekday_hours(ts, now) if us_days else max(0.0, (now - ts) / 3600))
        st, first = status(age, every), None
        if st == "never" and name in FIRST_RUN:
            first = parse_updated(FIRST_RUN[name])
            if first and now < first + GRACE_H * 3600:
                st = "wait"
        out.append({"file": name, "zh": zh, "en": en, "every": every, "us_days": us_days, "ts": ts, "age": age,
                    "st": st, "first": first})
    return out


def newest(rs: List[Dict]) -> Optional[float]:
    ts = [r["ts"] for r in rs if r["ts"]]
    return max(ts) if ts else None


def _gap(h: float) -> str:
    return f"{h / 24:.0f} 天" if h >= 48 else f"{h:.0f} 小時"


def _age(h: Optional[float]) -> str:
    if h is None:
        return "—"
    return f"{h / 24:.1f} 天前" if h >= 48 else f"{h:.0f} 小時前" if h >= 1 else "1 小時內"


def sec_routine_health(eng=None) -> str:
    rs = rows()
    bad = [r for r in rs if r["st"] in ("stop", "never")]
    late = [r for r in rs if r["st"] == "late"]
    if bad:
        lz = f"有 {len(bad)} 張 AI 卡片停了：{'、'.join(r['zh'] for r in bad)}。這些卡片上的內容可能已經過時，看的時候要注意日期。"
        le = f"{len(bad)} AI card(s) stopped updating: " + ", ".join(r["en"] for r in bad) + "."
    elif late:
        lz = f"AI 卡片大致正常，{'、'.join(r['zh'] for r in late)} 比平常晚。"
        le = "AI cards mostly on time; late: " + ", ".join(r["en"] for r in late) + "."
    else:
        n = len([r for r in rs if r["st"] != "wait"])
        lz, le = f"{n} 張 AI 卡片都照排程更新。", f"All {n} AI cards are on schedule."
    wait = [r for r in rs if r["st"] == "wait"]
    if wait:
        lz += f"{'、'.join(r['zh'] for r in wait)}還沒到第一次排程。"
        le += " Not yet due: " + ", ".join(r["en"] for r in wait) + "."
    trs = []
    for r in rs:
        ic, sz, se = LIGHT[r["st"]]
        when = datetime.fromtimestamp(r["ts"], TPE).strftime("%m/%d %H:%M") if r["ts"] else "—"
        if r["st"] == "wait" and r.get("first"):
            when = "第一次排程 " + datetime.fromtimestamp(r["first"], TPE).strftime("%m/%d %H:%M")
        trs.append(f'<tr><td>{T(r["zh"], r["en"])}</td><td>{ic} {T(sz, se)}</td><td class="r">{esc(when)}</td>'
                   f'<td class="r">{esc(_age(r["age"]))}</td><td class="r">{esc(_gap(r["every"]))}'
                   f'{T("（交易日）", " (trading days)") if r["us_days"] else ""}</td></tr>')
    note = T("每張 AI 卡片都由雲端排程定時寫好再上傳，這張表看它們最後一次更新是多久以前，和平常的更新間隔比："
             "不超過 2 倍是準時，2～4 倍是晚了，超過 4 倍或從來沒寫過就是停了；每月一次的排程在第一次執行日之前顯示 ⚪ 等第一次排程。美股相關的卡片不算週末。"
             "補寫型的排程沒有新東西時本來就不會更新，所以不列在這裡。排程停了常見的原因是帳號用量額度用完，或排程的雲端環境連不到資料來源。",
             "Each AI card is written by a scheduled cloud job. Compared with its usual gap: ≤2× on time, 2–4× late, more or never = stopped. "
             "US cards skip weekends. Backfill jobs that only commit when there is something new are not listed.")
    body = (f'<p class="rimp big2"><b>{T(lz, le)}</b></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("卡片", "Card")}</th><th>{T("狀態", "Status")}</th>'
            f'<th class="r">{T("最後更新（台北）", "Last update (Taipei)")}</th><th class="r">{T("距今", "Age")}</th>'
            f'<th class="r">{T("平常間隔", "Usual gap")}</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>'
            f'<p class="note">{note}</p>')
    return card("排程健康表：AI 卡片有沒有照時間更新", "Routine health: are the AI cards on schedule", body, "wide")
