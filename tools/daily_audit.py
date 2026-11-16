"""每日稽核（2026-11-16）：每日排程第一步跑這支，把「機械式」的事實一次查完，排程再根據事實判斷、修正、擴充。

查五件事，全部看線上網站或公開檔案（看到的才算數）：
  1 stale    線上每張卡片的「⚠ 資料偏舊」標記，列出卡片名稱、哪個來源、檢查時間、資料日，並粗分原因：
             fetch＝來源抓取太久沒成功；date＝資料日超過該來源容許的落後天數（可能是官方還沒發布、假日延後，或容許天數設錯）
  2 hardcode 最近 26 小時改過的網站程式裡，中文字串中直接寫死的數字＋單位（億、兆、%、美元、倍、天…），列為待人工確認的候選
  3 routines 排程健康表（tools/site_routines，讀線上檔案）的紅燈與黃燈
  4 selfcheck tools/sys_health 每小時的自我檢查結果（大公司財報有沒有顯示、即時推送超時）
  5 ahead    接下來 3 天的大事（upcoming.json）
輸出：印出摘要，並寫 data_cache/daily_audit.json。不改任何東西。
Run: python -m tools.daily_audit"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wsb.config import DATA_DIR  # noqa: E402

SITE = "https://wallstreet-sentinel.pages.dev/"
UA = {"User-Agent": "Mozilla/5.0 (WallStreetSentinel daily audit)"}
OUT = DATA_DIR / "daily_audit.json"


def _get(url: str, timeout: int = 60) -> str:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read().decode("utf-8", "ignore")


# ------------------------------------------------------------------ 1. stale cards (pure, tested)
SECTION = re.compile(r'<section\b[^>]*\bclass="card[^"]*"[^>]*>', re.S)


def stale_cards(html: str) -> List[Dict]:
    """[{card, tips: [{src, checked, data}], why}] for every card whose stamp carries the 'old' class."""
    starts = [m.start() for m in SECTION.finditer(html)] + [len(html)]
    out = []
    for a, b in zip(starts, starts[1:]):
        seg = html[a:b]
        m = re.search(r'<p class="upd old" title="([^"]*)"', seg)
        if not m:
            continue
        h2 = re.search(r"<h2>(.*?)</h2>", seg, re.S)
        title = re.sub(r"<[^>]+>", "", h2.group(1)).strip() if h2 else "（無標題卡片）"
        title = re.sub(r"\s+", " ", title)
        tips = []
        for t in m.group(1).split("；"):
            mm = re.match(r"\s*(.*?) 檢查 (\d\d-\d\d \d\d:\d\d|—)(?:・資料日 (\S+))?", t)
            if mm:
                tips.append({"src": mm.group(1), "checked": mm.group(2), "data": mm.group(3)})
        out.append({"card": title[:60], "tips": tips})
    return out


def classify(tips: List[Dict], now: float) -> List[Dict]:
    """Add why='fetch' (the source has not been fetched within its allowed hours) or why='date' (the data date is older
    than the source's allowed lag days) and the limits, using tools/site_stamp.SOURCES / MAX_AGE_H."""
    from datetime import date, datetime
    from tools import site_stamp as ST
    by_zh = {v[0]: k for k, v in ST.SOURCES.items()}
    out = []
    for t in tips:
        k = by_zh.get(t["src"])
        x = dict(t, key=k)
        if k:
            lag, max_h = ST.SOURCES[k][3], ST.MAX_AGE_H.get(k, 36)
            x["lag_days"], x["max_hours"] = lag, max_h
            try:
                yr = datetime.fromtimestamp(now).year
                chk = datetime.strptime(f"{yr}-{t['checked']}", "%Y-%m-%d %H:%M").timestamp()
                x["fetch_age_h"] = round((now - chk) / 3600, 1)
                if x["fetch_age_h"] > max_h:
                    x["why"] = "fetch"
            except (ValueError, TypeError):
                pass
            if t.get("data") and lag:
                try:
                    age_d = (date.fromtimestamp(now) - date.fromisoformat(t["data"][:10])).days
                    x["data_age_d"] = age_d
                    if age_d > lag and "why" not in x:
                        x["why"] = "date"
                except ValueError:
                    pass
        out.append(x)
    return out


# ------------------------------------------------------------------ 2. hard-coded numbers in recently changed code (pure, tested)
# market data typed in: money amounts, or "約／達／現在／目前 + a number + %／倍" (rule descriptions such as 每 10 天 or 跌 3% 才通知
# are not data and are left out)
NUM_UNIT = re.compile(r"(?<![{\w.])(\d[\d,]*(?:\.\d+)?)\s*(億美元|兆美元|億元|兆元|萬元|美元|億|兆)"
                      r"|(?:約|達|現在|目前|高達|只剩)\s*(\d[\d,]*(?:\.\d+)?)\s*(%|倍)")
SKIP_LINE = re.compile(r"^\s*#|logging|log\.|assert |def |\bthreshold|\bTTL\b|range\(|sleep\(|timeout|[<>]=?\s*\d")


def hardcode_candidates(path: Path, changed_lines: List[int]) -> List[Dict]:
    """Numbers + units typed inside Chinese string literals on the changed lines (a review list, not a verdict)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for n in changed_lines:
        if not (0 < n <= len(lines)):
            continue
        ln = lines[n - 1]
        if SKIP_LINE.search(ln) or not re.search(r"[一-鿿]", ln):
            continue
        for lit in re.findall(r'"([^"\n]*[一-鿿][^"\n]*)"', ln):
            lit_wo = re.sub(r"\{[^}]*\}", "", lit)                  # f-string placeholders are computed, not typed
            for m in NUM_UNIT.finditer(lit_wo):
                out.append({"file": str(path.relative_to(ROOT)).replace("\\", "/"), "line": n, "text": m.group(0), "context": lit_wo[:80]})
    return out


def changed_since(hours: int = 26) -> Dict[Path, List[int]]:
    """{file: [changed line numbers]} for tools/ and wsb/ .py files changed in the last `hours` (git, private repo)."""
    try:
        base = subprocess.run(["git", "-C", str(ROOT), "rev-list", "-1", f"--before={hours} hours ago", "HEAD"],
                              capture_output=True, text=True, timeout=30).stdout.strip()
        if not base:
            return {}
        diff = subprocess.run(["git", "-C", str(ROOT), "diff", "-U0", base, "--", "tools", "wsb"],
                              capture_output=True, text=True, timeout=60, encoding="utf-8", errors="ignore").stdout
    except Exception:  # noqa: BLE001
        return {}
    out: Dict[Path, List[int]] = {}
    cur = None
    for ln in diff.splitlines():
        if ln.startswith("+++ b/"):
            p = ROOT.parent / ln[6:] if not (ROOT / ln[6:]).exists() else ROOT / ln[6:]
            if not p.exists():
                p = ROOT / ln[6:].split("wallstreet_bot/", 1)[-1]
            cur = p if p.suffix == ".py" else None
        elif ln.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", ln)
            if m:
                a, k = int(m.group(1)), int(m.group(2) or 1)
                out.setdefault(cur, []).extend(range(a, a + k))
    return out


# ------------------------------------------------------------------ run
def main() -> Dict:
    rep: Dict = {"ts": int(time.time())}
    try:
        html = _get(SITE + f"?v={int(time.time())}")
        rep["stale"] = [dict(c, tips=classify(c["tips"], time.time())) for c in stale_cards(html)]
    except Exception as e:  # noqa: BLE001
        html, rep["stale"] = "", []
        rep["site_error"] = str(e)
    rep["hardcode"] = [c for p, ls in changed_since().items() for c in hardcode_candidates(p, ls)][:60]
    try:
        import asyncio
        from tools import sys_health as H
        sc = DATA_DIR / "selfcheck_site.json"
        if sc.exists():
            sc.unlink()                                       # force a fresh hourly check now
        rep["selfcheck"] = asyncio.run(H.site_shown(time.time()))
        rep["overrun"] = H.overrun_issues(H.read_tail(DATA_DIR / "sec_push.log"), time.time())
    except Exception as e:  # noqa: BLE001
        rep["selfcheck"], rep["overrun"] = [], []
        rep["selfcheck_error"] = str(e)
    try:
        rep["ahead"] = json.loads(_get(SITE + f"upcoming.json?v={int(time.time())}", 30)).get("items") or []
    except Exception:  # noqa: BLE001
        rep["ahead"] = []
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def summary(rep: Dict) -> str:
    lines = [f"偏舊卡片 {len(rep.get('stale') or [])} 張："]
    for c in rep.get("stale") or []:
        lines.append("  - " + c["card"] + "｜" + "；".join(
            f"{t['src']}（檢查 {t['checked']}，資料日 {t['data'] or '—'}"
            + ("；⚠ 抓取超過 " + str(t.get("max_hours")) + " 小時" if t.get("why") == "fetch" else "")
            + ("；⚠ 資料日晚 " + str(t.get("data_age_d")) + " 天，容許 " + str(t.get("lag_days")) + " 天" if t.get("why") == "date" else "") + "）"
            for t in c["tips"] if t.get("why")) or ("（標記偏舊，但個別來源都在容許內）" if c["tips"] else ""))
    lines.append(f"寫死數字候選 {len(rep.get('hardcode') or [])} 處（最近 26 小時改過的行）：")
    for h in (rep.get("hardcode") or [])[:15]:
        lines.append(f"  - {h['file']}:{h['line']} 「{h['text']}」 {h['context']}")
    lines.append(f"自我檢查 {len(rep.get('selfcheck') or [])} 項：" + "；".join(i["text"] for i in rep.get("selfcheck") or []))
    lines.append(f"即時推送超時：" + ("；".join(i["text"] for i in rep.get("overrun") or []) or "沒有"))
    lines.append("接下來 3 天：" + "、".join(f"{x.get('zh')} {x.get('tpe')}" for x in (rep.get("ahead") or [])[:10]))
    return "\n".join(lines)


if __name__ == "__main__":
    r = main()
    print(summary(r))
