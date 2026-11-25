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


# ------------------------------------------------------------------ 6. tracked stocks that stopped trading (11-17 full check: CCO, RAMP)
def stopped_trading(close, days: int = 14) -> List[Dict]:
    """Tracked tickers whose last price is more than `days` calendar days older than the newest one (delisted, acquired or
    renamed): they keep sitting in lists and alerts with a frozen price."""
    import pandas as pd
    if close is None or close.empty:
        return []
    top = close.index.max()
    last = close.apply(lambda s: s.last_valid_index())
    old = last[last < top - pd.Timedelta(days=days)].sort_values()
    return [{"sym": k, "last": str(v.date())} for k, v in old.items() if v is not None]


STOP_WHY = (("1.03", "聲請破產"), ("3.01", "下市或不符上市標準"), ("2.01", "完成併購"), ("5.01", "控制權變更（被收購）"),
            ("15-12", "撤銷 SEC 登記（不再是上市公司）"), ("25-NSE", "交易所申請下市"))


def stop_reason(sub: Dict) -> List[str]:
    """Why a stock stopped trading, from its SEC submissions (recent 8-K items and forms 15 / 25)."""
    f = (sub or {}).get("filings", {}).get("recent", {})
    forms, items = f.get("form") or [], f.get("items") or []
    out = []
    for i, form in enumerate(forms[:40]):
        it = str(items[i] if i < len(items) else "")
        for code, zh in STOP_WHY:
            hit = (code in it and form.startswith("8-K")) if "." in code else form.startswith(code)
            if hit and zh not in out:
                out.append(zh)
    return out


def explain_stopped(rows: List[Dict]) -> List[Dict]:
    """Add 'why' from SEC for each stopped ticker (company map first; efts entity search when the ticker left the map)."""
    try:
        from wsb.data.edgar_holdings import _MAP_FILE
        cmap = json.loads(_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        cmap = {}
    hdr = {"User-Agent": "WallStreetSentinel daily audit admin@example.invalid"}
    try:
        from wsb.data.stocks import universe
        names = {k: v[1] for k, v in ((universe().get("us") or {}).get("symbols") or {}).items()}
    except Exception:  # noqa: BLE001
        names = {}
    try:
        dcache = json.loads((DATA_DIR / "earn_distress.json").read_text(encoding="utf-8"))
        auto = json.loads((DATA_DIR / "earn_distress_auto.json").read_text(encoding="utf-8"))
        names.update({k: v.get("zh") for k, v in auto.items() if isinstance(v, dict) and v.get("zh") and k not in names})
    except Exception:  # noqa: BLE001
        dcache = {}
    for r in rows:
        cik = (cmap.get(r["sym"]) or {}).get("cik") or (dcache.get(r["sym"]) or {}).get("cik")   # distress radar keeps its own CIKs
        try:
            if not cik:
                js = json.loads(urllib.request.urlopen(urllib.request.Request(
                    f"https://efts.sec.gov/LATEST/search-index?keysTyped={r['sym']}", headers=hdr), timeout=20).read())
                hit = next((h for h in js.get("hits", {}).get("hits", []) if r["sym"] in str(h["_source"].get("tickers") or "").split(", ")), None)
                cik = hit["_id"] if hit else None
            if not cik and names.get(r["sym"]):                 # a delisted ticker leaves SEC's list: search by company name
                from urllib.parse import quote
                q = names[r["sym"]].split(",")[0].replace(" Inc", "").replace(" Corp", "").strip()
                js = json.loads(urllib.request.urlopen(urllib.request.Request(
                    f"https://efts.sec.gov/LATEST/search-index?keysTyped={quote(q)}", headers=hdr), timeout=20).read())
                hit = next((h for h in js.get("hits", {}).get("hits", []) if "Holdings" in h["_source"].get("entity", "")
                            or q.lower() in h["_source"].get("entity", "").lower()), None)
                hits = js.get("hits", {}).get("hits", [])
                hit = next((h for h in hits if "holdings" in h["_source"].get("entity", "").lower()), None) or hit
                cik = hit["_id"] if hit else None
            if cik:
                sub = json.loads(urllib.request.urlopen(urllib.request.Request(
                    f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", headers=hdr), timeout=20).read())
                r["name"], r["why"] = sub.get("name"), stop_reason(sub)
        except Exception as e:  # noqa: BLE001
            r["why_error"] = str(e)[:80]
    return rows


IPO_BLANK_DAYS = 14          # a listing this recent with no offer price on the page is a parser miss, not old history


def ipo_blank_price(html: str, today) -> List[str]:
    """已掛牌 rows (tools.site_ipo._us_done) whose 發行價 cell is 「—」 and whose pricing date is within IPO_BLANK_DAYS.
    11-20: Anthropic, the largest IPO ever, sat there with no offer price / day-1 close and nothing flagged it."""
    from datetime import date as _date
    out = []
    for m in re.finditer(r'<tr><td><b>([^<]{2,80})</b>(?:(?!</tr>).)*?</td><td class="nw">(\d\d)-(\d\d)</td><td class="r">—</td>', html, re.S):
        try:
            d = _date(today.year, int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
        if d > today:                                        # a December row read in January
            d = _date(today.year - 1, d.month, d.day)
        if (today - d).days <= IPO_BLANK_DAYS:
            out.append(f"{m.group(1)}（{m.group(2)}-{m.group(3)} 定價）")
    return out


def lagging_rows(dash: Dict, today) -> List[str]:
    """Price rows of macro_dash.json whose data day is older than the newest row's, once that newest day is over
    everywhere (it is before today, Taipei).  11-21: the card as a whole was fresh, so nothing flagged that the Nikkei,
    Hang Seng and HYG rows still showed 11-19 after a −5% Friday.  A local holiday also lands here: check before fixing."""
    from datetime import date as _date

    def day(md: str):
        try:
            d = _date(today.year, int(md[:2]), int(md[3:5]))
        except (ValueError, TypeError):
            return None
        return _date(today.year - 1, d.month, d.day) if d > today else d
    rs = [(r, day(str(r.get("date") or ""))) for r in dash.get("rows") or [] if r.get("kind") == "pct"]
    rs = [(r, d) for r, d in rs if d]
    if not rs:
        return []
    newest = max(d for _, d in rs)
    if newest >= today:
        return []
    return [f"{r.get('zh')}（{r.get('date')}，其他列 {newest.strftime('%m-%d')}）" for r, d in rs if d < newest]


def gemini_unknown_groups(reply: str) -> List[str]:
    """Section codes in gemini_reply.md (### XYZ-n) that tools.site_gemini.GROUP / HIDE does not know.  11-22: the new TWC
    section fell back to the per-company layout because GROUP lacked it; Gemini found it, nothing automatic did."""
    from tools import site_gemini as G
    known = set(G.GROUP) | {h.rstrip("-") for h in G.HIDE}
    codes = set(re.findall(r"^### ([A-Z]{1,6})-", reply, re.M))
    return sorted(c for c in codes if c not in known)


LAG = re.compile(r"資料期：本站\s*(\d{4}-\d{2}(?:-\d{2})?|\d{4}Q\d)\s*｜\s*官方\s*(\d{4}-\d{2}(?:-\d{2})?|\d{4}Q\d)\s*｜\s*(https?://\S+)")
OFFICIAL = ("stat.gov.tw", "mof.gov.tw", "moea.gov.tw", "cbc.gov.tw", "ndc.gov.tw", "fsc.gov.tw", "twse.com.tw", "tpex.org.tw", "taifex.com.tw",
            "stlouisfed.org", "bea.gov", "bls.gov", "census.gov", "federalreserve.gov", "treasury.gov", "sec.gov", "dgbas.gov.tw")


def read_items(reply: str) -> Dict:
    """Gemini's READ section (11-26, user: 「不希望下次還有甚麼數據還沒修」): the cards it covered this round, the 「然後呢」 wording
    problems, and the 「比官方慢」 lines — only those whose URL is on an issuing agency's own domain (news re-tellings are dropped)."""
    out: Dict = {"scope": "", "lag": [], "wording": []}
    for blk in re.split(r"(?m)^### ", reply or "")[1:]:
        head, _, body = blk.partition("\n")
        if not head.startswith("READ-"):
            continue
        if head.startswith("READ-範圍"):
            out["scope"] = head.split("｜", 1)[-1].strip()
            continue
        card = (re.search(r"#\d\d-\d\d", head) or re.search(r"#\d\d", head))
        lags = [m for m in LAG.finditer(blk) if any(d in m.group(3) for d in OFFICIAL)]
        for m in lags:
            out["lag"].append({"card": card.group(0) if card else "", "site": m.group(1), "official": m.group(2), "url": m.group(3).rstrip("）)。,，")})
        if not lags:
            out["wording"].append({"card": card.group(0) if card else "", "text": head.split("｜", 1)[-1].strip()[:120]})
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
    from wsb.data.econcal import us_today
    rep["ipo_blank"] = ipo_blank_price(html, us_today()) if html else []
    try:
        import asyncio
        from tools import sys_health as H
        sc = DATA_DIR / "selfcheck_site.json"
        if sc.exists():
            sc.unlink()                                       # force a fresh hourly check now
        rep["selfcheck"] = asyncio.run(H.site_shown(time.time()))
        sp = H.read_tail(DATA_DIR / "sec_push.log")
        rep["offline"] = H.offline_issues(sp, time.time())
        rep["overrun"] = [] if rep["offline"] else H.overrun_issues(sp, time.time()) + H.slow_source_issues(sp, time.time())
    except Exception as e:  # noqa: BLE001
        rep["selfcheck"], rep["overrun"] = [], []
        rep["selfcheck_error"] = str(e)
    try:                                                      # 3 routines: documented above but never run until 11-21
        from tools import site_routines as SR
        feed = Path(__file__).resolve().parents[2] / "wallstreet-sentinel" / "research_feed"
        rep["routines"] = [{"file": r["file"], "zh": r["zh"], "st": r["st"],
                            "age_h": None if r["age"] is None else round(r["age"], 1), "every_h": r["every"]}
                           for r in SR.rows(feed_dir=feed if feed.is_dir() else SR.FEED_DIR) if r["st"] not in ("ok", "wait")]
    except Exception as e:  # noqa: BLE001
        rep["routines"], rep["routines_error"] = [], str(e)
    try:                                                      # private: holdings files that disagree (symbols only)
        from tools import holdings_guard as HG
        g = HG.compare(HG.read_all())
        rep["holdings_mismatch"] = [d["sym"] for d in g["diff"]] + (["（機器人主檔不見）"] if g["missing_primary"] else [])
    except ImportError:                                       # the public copy has no holdings_guard
        rep["holdings_mismatch"] = []
    except Exception as e:  # noqa: BLE001
        rep["holdings_mismatch"], rep["holdings_error"] = [], str(e)
    try:
        rep["ahead"] = json.loads(_get(SITE + f"upcoming.json?v={int(time.time())}", 30)).get("items") or []
    except Exception:  # noqa: BLE001
        rep["ahead"] = []
    try:
        from datetime import datetime, timedelta, timezone
        rep["lagging_rows"] = lagging_rows(json.loads(_get(SITE + f"macro_dash.json?v={int(time.time())}", 30)),
                                           datetime.now(timezone(timedelta(hours=8))).date())
    except Exception as e:  # noqa: BLE001
        rep["lagging_rows"], rep["lagging_rows_error"] = [], str(e)
    try:
        import pandas as pd
        rep["stopped"] = explain_stopped(stopped_trading((pd.read_pickle(DATA_DIR / "stock_prices.pkl") or {}).get("close")))
    except Exception:  # noqa: BLE001
        rep["stopped"] = []
    try:                                                      # issuer data the cloud build is refused (Invesco 406 since 11-17)
        from wsb.data import etf_flows as EF
        feed = Path(__file__).resolve().parents[2] / "wallstreet-sentinel" / "research_feed"
        rep["etf_seed"] = EF.write_seed(feed / "etf_flows_seed.json") if feed.is_dir() else 0
    except Exception as e:  # noqa: BLE001
        rep["etf_seed_error"] = str(e)
    try:                                                      # hand-written reads older than the news they explain (11-25)
        feed = Path(__file__).resolve().parents[2] / "wallstreet-sentinel" / "research_feed"
        tj = json.loads(_get(SITE + f"threads.json?v={int(time.time())}", 30))
        rd = {n: json.loads((feed / n).read_text(encoding="utf-8")).get("updated") for n in ("threads_read.json", "dots_read.json", "tw_forecast.json")}
        rep["old_reads"] = old_reads(tj.get("threads") or [], rd, time.time())
    except Exception as e:  # noqa: BLE001
        rep["old_reads"], rep["old_reads_error"] = [], str(e)
    try:
        gr = Path(__file__).resolve().parents[2] / "wallstreet-sentinel" / "research_feed" / "gemini_reply.md"
        rep["gemini_groups"] = gemini_unknown_groups(gr.read_text(encoding="utf-8")) if gr.exists() else []
        rep["read"] = read_items(gr.read_text(encoding="utf-8")) if gr.exists() else {}
    except Exception as e:  # noqa: BLE001
        rep["gemini_groups"], rep["gemini_groups_error"] = [], str(e)
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


READ_MAX_H = 48


def old_reads(threads: List[Dict], updated: Dict[str, str], now: float) -> List[str]:
    """Hand-written reads (no cloud routine rewrites them) that are older than 48 h while a thread is 升溫 or has a new official paper.
    11-25: they still said the NVIDIA chair would not take the CEO back, two days after the board did."""
    from tools.site_routines import parse_updated
    hot = [t.get("id") for t in threads if t.get("state") in ("升溫", "官方新文件")]
    if not hot:
        return []
    out = []
    for name, raw in updated.items():
        ts = parse_updated(raw)
        if ts is None or now - ts > READ_MAX_H * 3600:
            out.append(f"{name}（{raw or '沒有時間'}；升溫主線 {len(hot)} 條）")
    return out


def summary(rep: Dict) -> str:
    # 2026-11-17: the site read timed out (home internet down) and this still printed 「偏舊卡片 0 張」 as if all were fresh
    lines = ([f"⚠ 讀不到網站（{rep['site_error']}）：偏舊卡片無法判斷，不是 0 張"] if rep.get("site_error")
             else [f"偏舊卡片 {len(rep.get('stale') or [])} 張："])
    lines += ["⚠ " + i["text"] for i in rep.get("offline") or []]
    for c in rep.get("stale") or []:
        lines.append("  - " + c["card"] + "｜" + "；".join(
            f"{t['src']}（檢查 {t['checked']}，資料日 {t['data'] or '—'}"
            + ("；⚠ 抓取超過 " + str(t.get("max_hours")) + " 小時" if t.get("why") == "fetch" else "")
            + ("；⚠ 資料日晚 " + str(t.get("data_age_d")) + " 天，容許 " + str(t.get("lag_days")) + " 天" if t.get("why") == "date" else "") + "）"
            for t in c["tips"] if t.get("why")) or ("（標記偏舊，但個別來源都在容許內）" if c["tips"] else ""))
    if rep.get("lagging_rows"):
        lines.append("⚠ 每日總經儀表有幾列的資料日落後其他列（當地休市可忽略，否則查 wsb/data/market.fill_meta_close）：" + "、".join(rep["lagging_rows"]))
    lines.append(f"寫死數字候選 {len(rep.get('hardcode') or [])} 處（最近 26 小時改過的行）：")
    for h in (rep.get("hardcode") or [])[:15]:
        lines.append(f"  - {h['file']}:{h['line']} 「{h['text']}」 {h['context']}")
    lines.append("排程紅黃燈：" + ("、".join(f"{r['zh']}（{r['st']}，{r['age_h']} 小時／應每 {r['every_h']} 小時）"
                                             for r in rep.get("routines") or []) or "沒有"))
    if rep.get("holdings_mismatch"):
        lines.append("⚠ 持股檔對不起來（只列代號）：" + "、".join(rep["holdings_mismatch"]))
    lines.append(f"自我檢查 {len(rep.get('selfcheck') or [])} 項：" + "；".join(i["text"] for i in rep.get("selfcheck") or []))
    if rep.get("ipo_blank"):
        lines.append("⚠ 剛掛牌的 IPO 沒有發行價（424B4 沒讀懂？查 wsb/data/ipo_data.offer_price，修好後把 OFFER_V 加一）：" + "、".join(rep["ipo_blank"]))
    if rep.get("old_reads"):
        lines.append("⚠ 手寫判讀比新聞舊（先讀原文再改寫）：" + "、".join(rep["old_reads"]))
    rd = rep.get("read") or {}
    if rd.get("lag"):
        lines.append("⚠ Gemini READ：官方已公布更新一期、本站還沒有（先點開官方網址確認，再改成讀原始來源）：" + "；".join(
            f"{x['card']} 本站 {x['site']} → 官方 {x['official']} {x['url']}" for x in rd["lag"]))
    if rd.get("wording"):
        lines.append("Gemini READ：寫了等於沒寫（讀卡片原文確認後改寫）：" + "；".join(f"{x['card']} {x['text']}" for x in rd["wording"][:10]))
    if rd.get("scope"):
        lines.append("Gemini READ 本輪範圍：" + rd["scope"])
    if rep.get("gemini_groups"):
        lines.append("⚠ Gemini 回答有網站不認得的段落代碼（加到 tools/site_gemini.py GROUP 和 order）：" + "、".join(rep["gemini_groups"]))
    lines.append(f"即時推送超時：" + ("；".join(i["text"] for i in rep.get("overrun") or []) or "沒有"))
    lines.append("停止交易的追蹤股票：" + ("、".join(f"{x['sym']}（最後 {x['last']}；SEC：{'、'.join(x.get('why') or []) or '查不到原因'}）"
                                                for x in rep.get("stopped") or []) or "沒有"))
    lines.append("接下來 3 天：" + "、".join(f"{x.get('zh')} {x.get('tpe')}" for x in (rep.get("ahead") or [])[:10]))
    return "\n".join(lines)


if __name__ == "__main__":
    r = main()
    print(summary(r))
