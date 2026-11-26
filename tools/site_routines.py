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
    ("deep.json", "每日深度研判", "Daily deep read", 24, True),        # runs Mon–Fri (US): weekends do not count
    ("learn.json", "每日學習筆記", "Daily learning notes", 24, False),
    ("ai_view.json", "獨立 AI 觀察員", "AI observer", 12, True),        # trading days 07:00/21:00 (11-22: weekends were flagged late)
    ("earn_preview.json", "財報前瞻", "Earnings previews", 24, False),
    ("earn_after.json", "財報後解讀", "Post-earnings reads", 12, True),  # no reports on weekends, nothing to write (11-22)
    # 11-25 audit P3-16: these three stopped for 7–15 days with no light (earn_after_rest since 11-10)
    ("earn_after_more.json", "財報後解讀（更多公司）", "Post-earnings reads (more)", 48, True),
    ("earn_after_asia.json", "財報後解讀（亞洲）", "Post-earnings reads (Asia)", 48, True),
    ("earn_after_rest.json", "財報後解讀（其他市場）", "Post-earnings reads (rest)", 48, True),
    ("event_board.json", "今晚大事看板", "Tonight's event board", 48, True),   # stopped 11-20 22:15, nothing flagged
    ("forecast.json", "一個月預判", "One-month calls", 96, False),
    ("bonds.json", "債市深度判讀", "Bond deep read", 24, True),        # runs Mon–Fri (US)
    ("feed.json", "學術動態", "Research feed", 168, False),
    ("industry_note.json", "產業筆記", "Industry note", 168, False),
    ("tw_forecast.json", "台灣總經展望", "Taiwan macro outlook", 24, True),  # Mon–Fri 15:40 (added 11-21: the 11-20 run
                                                                                 # stopped at a permission prompt and nothing flagged it)
    ("tw_note.json", "台灣每月分析筆記", "Taiwan monthly note", 31 * 24, False),
)
LIGHT = {"ok": ("🟢", "準時", "On time"), "late": ("🟡", "晚了", "Late"), "stop": ("🔴", "停了", "Stopped"),
         "never": ("🔴", "從未產出", "Never written"), "wait": ("⚪", "等第一次排程", "Waiting for first run"),
         "done": ("⚪", "補寫完成", "Backfill done"), "paused": ("⚪", "暫停中", "Paused")}
# Backfill routines: output file → its backlog.  When every backlog name is already written, skipped or waiting (`later`),
# an old `updated` means "nothing left to add", not "stopped" (11-26: three red lights were finished/paused backfills; the
# US run log said 補寫完成, 1,508 of 1,508).  Key is (mk, sym); US rows have no mk.  earn_after.json counts as written too.
BACKFILL = {"earn_after_more.json": "earn_backlog.json", "earn_after_asia.json": "earn_backlog_asia.json",
            "earn_after_rest.json": "earn_backlog_rest.json"}
# Routines switched off on purpose (configuration, checked with RemoteTrigger get on the date shown).  Shown ⚪ with the
# names still pending instead of 🔴 every day; remove the line when the routine is switched back on.
PAUSED = {"earn_after_rest.json": "2026-11-10 為省用量額度暫停（2026-11-26 確認仍關閉）"}
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
    """Hours between t0 and t1 not counting the US weekend or NYSE holidays as seen from Taipei (Sat 08:00 → Mon 08:00;
    a holiday likewise runs 08:00 → 08:00).  Holidays from the shared calendar (wsb/data/exchange_cal.py, 2026-11-16)."""
    from wsb.data.exchange_cal import us_holidays
    total, cur = 0.0, datetime.fromtimestamp(t0, TPE)
    end = datetime.fromtimestamp(t1, TPE)
    hol = us_holidays(cur.year - 1, end.year)
    while cur < end:
        nxt = min(end, cur.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        shifted = cur - timedelta(hours=8)            # Sat 08:00 Taipei → Sat 00:00 on the shifted clock
        if shifted.weekday() < 5 and shifted.date().isoformat() not in hol:
            total += (nxt - cur).total_seconds() / 3600
        cur = nxt
    return total


def status(age_h: Optional[float], every_h: float) -> str:
    if age_h is None:
        return "never"
    return "ok" if age_h <= 2 * every_h else "late" if age_h <= 4 * every_h else "stop"


def _load(p: Path) -> Optional[Dict]:
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    except Exception:  # noqa: BLE001
        return None


def pending(name: str, feed_dir: Path = FEED_DIR) -> Optional[int]:
    """Backlog names a backfill routine has not written, skipped or parked in `later` yet; None = not a backfill or unreadable."""
    bl = BACKFILL.get(name)
    b, o = (_load(feed_dir / bl) if bl else None), _load(feed_dir / name)
    if not isinstance(b, dict):
        return None
    key = lambda x: (str(x.get("mk") or "us"), str(x.get("sym")))  # noqa: E731
    seen = set()
    for d in (o or {}, _load(feed_dir / "earn_after.json") or {}):
        for k in ("items", "skipped", "later"):
            seen |= {key(x) for x in d.get(k) or [] if isinstance(x, dict)}
    return sum(1 for x in b.get("items") or [] if isinstance(x, dict) and key(x) not in seen)


def rows(now: Optional[float] = None, feed_dir: Path = FEED_DIR) -> List[Dict]:
    now = time.time() if now is None else now
    out = []
    for name, zh, en, every, us_days in EXPECT:
        d = _load(feed_dir / name)
        ts = _stamp(name, d) if isinstance(d, dict) else None
        age = None if ts is None else (weekday_hours(ts, now) if us_days else max(0.0, (now - ts) / 3600))
        st, first, left = status(age, every), None, None
        if st == "never" and name in FIRST_RUN:
            first = parse_updated(FIRST_RUN[name])
            if first and now < first + GRACE_H * 3600:
                st = "wait"
        if st != "ok" and name in BACKFILL:
            left = pending(name, feed_dir)
            if left == 0:
                st = "done"
            elif left and name in PAUSED:            # backlog unreadable → keep the red light
                st = "paused"
        out.append({"file": name, "zh": zh, "en": en, "every": every, "us_days": us_days, "ts": ts, "age": age,
                    "st": st, "first": first, "left": left, "why": PAUSED.get(name) if st == "paused" else None})
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
        n = len([r for r in rs if r["st"] == "ok"])
        lz, le = f"{n} 張 AI 卡片都照排程更新。", f"All {n} AI cards are on schedule."
    off = [r for r in rs if r["st"] in ("done", "paused")]
    if off:
        def _off(r: Dict) -> str:
            return "全部寫完" if r["st"] == "done" else f"暫停，還剩 {r['left'] or 0:,} 家"
        lz += "補寫型的" + "、".join(f"{r['zh']}（{_off(r)}）" for r in off) + "沒有新東西要寫，不算停了。"
        le += " Backfills not expected to update: " + ", ".join(r["en"] for r in off) + "."
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
        if r["st"] == "paused" and r.get("why"):
            when += f"（{r['why']}）"
        trs.append(f'<tr><td>{T(r["zh"], r["en"])}</td><td>{ic} {T(sz, se)}</td><td class="r">{esc(when)}</td>'
                   f'<td class="r">{esc(_age(r["age"]))}</td><td class="r">{esc(_gap(r["every"]))}'
                   f'{T("（交易日）", " (trading days)") if r["us_days"] else ""}</td></tr>')
    note = T("每張 AI 卡片都由雲端排程定時寫好再上傳，這張表看它們最後一次更新是多久以前，和平常的更新間隔比："
             "不超過 2 倍是準時，2～4 倍是晚了，超過 4 倍或從來沒寫過就是停了；每月一次的排程在第一次執行日之前顯示 ⚪ 等第一次排程。美股相關的卡片不算週末。"
             "補寫型的排程（把一份待補清單一家一家寫完）清單都寫完、或刻意暫停時顯示 ⚪，並寫還剩幾家，不算停了。排程停了常見的原因是帳號用量額度用完，或排程的雲端環境連不到資料來源。",
             "Each AI card is written by a scheduled cloud job. Compared with its usual gap: ≤2× on time, 2–4× late, more or never = stopped. "
             "US cards skip weekends. Backfill jobs that only commit when there is something new are not listed.")
    body = (f'<p class="rimp big2"><b>{T(lz, le)}</b></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("卡片", "Card")}</th><th>{T("狀態", "Status")}</th>'
            f'<th class="r">{T("最後更新（台北）", "Last update (Taipei)")}</th><th class="r">{T("距今", "Age")}</th>'
            f'<th class="r">{T("平常間隔", "Usual gap")}</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>'
            f'<p class="note">{note}</p>')
    return card("排程健康表：AI 卡片有沒有照時間更新", "Routine health: are the AI cards on schedule", body, "wide")
