"""國安基金（國家金融安定基金）官方動態（2026-11-22，台股覆蓋清單「國安基金進出」）。

來源：財政部全球資訊網「國家金融安定基金訊息」專區（Claude 11-22 自己從財政部首頁選單找到並逐頁下載驗證）：
  * 新聞稿列表 https://www.mof.gov.tw/multiplehtml/383 ：每則有標題、發布日期、內文連結（singlehtml/383?cntId=…）。
  * 每季收支及資產負債表 https://www.mof.gov.tw/multiplehtml/384 ：每季例會後公布（PDF／XLS），是唯一官方的「花了多少錢」。
Gemini v24 給的 singlehtml/384fb… 網址會被轉回首頁（不存在），它說的 11/21 新聞稿在官方列表上也沒有。
另收 金管會新聞稿列表 https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2 裡「市場穩定措施」類（放空、融券、借券、平盤、市場秩序等），
因為限空、融券保證金、借券召回這些規定改變的是「誰被迫買、誰不能賣」（11-22：11/21 宣布 11/23 起全面平盤以下禁空等 5 項，本站原本只有 11/19 那一項）。
國安基金不即時公布每天買多少；官方只有「啟動／繼續／停止」的委員會決議與每季報表。本站照實寫，不把媒體說的「進場護盤」當成官方金額。"""
from __future__ import annotations

import html as _html
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "tw_nsf.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_nsf_seed.json"
BASE = "https://www.mof.gov.tw"
U_NEWS = BASE + "/multiplehtml/383"
U_REPORT = BASE + "/multiplehtml/384"
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
TTL = 3 * 3600
TPE = timezone(timedelta(hours=8))
ON = re.compile(r"(啟動|繼續執行|持續執行)安定(市場|金融市場)任務")
OFF = re.compile(r"停止執行安定(市場|金融市場)任務")


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def parse_news(page: str) -> List[Dict]:
    """Rows of the press-release table: title, date, link (newest first, as the site lists them)."""
    out = []
    for m in re.finditer(r'<a[^>]+href="(/singlehtml/383\?cntId=[0-9a-f]+)"[^>]*>(.*?)</a>(.*?)(\d{4}-\d{2}-\d{2})', page or "", re.S):
        title = _text(m.group(2))
        if title and len(m.group(3)) < 600:
            out.append({"title": title, "date": m.group(4), "url": BASE + _html.unescape(m.group(1))})
    seen, rows = set(), []
    for r in out:
        if r["url"] not in seen:
            seen.add(r["url"])
            rows.append(r)
    return rows


def parse_body(page: str, title: str) -> str:
    """The release text between its title and the contact line."""
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page or "", flags=re.S)
    lines = [x.strip() for x in _html.unescape(re.sub(r"<[^>]+>", "\n", t)).splitlines() if x.strip()]
    idx = [i for i, x in enumerate(lines) if x == title]
    if not idx:
        return ""
    body = []
    for x in lines[idx[-1] + 1:]:
        if x.startswith(("新聞稿聯絡人", "發布單位", "聯絡電話")):
            break
        body.append(x)
    return "\n".join(body)


def parse_reports(page: str) -> List[Dict]:
    """Quarterly 收支及資產負債情形 / 決算 rows: title, publish date, PDF and XLS links."""
    out = []
    for m in re.finditer(r"(國家金融安定基金\d{2,3}年(?:第\d季收支及資產負債情形|度國家金融安定基金決算)|\d{2,3}年度國家金融安定基金決算)(.*?)\((?:國家金融安定基金管理委員會)-(\d{4}/\d{1,2}/\d{1,2})\)",
                         _html.unescape(page or ""), re.S):
        links = re.findall(r'href="([^"]+)"[^>]*>\s*\(?\s*(PDF|XLS)', m.group(2))
        y, mo, d = m.group(3).split("/")
        out.append({"title": m.group(1), "date": f"{y}-{int(mo):02d}-{int(d):02d}",
                    **{k.lower(): (u if u.startswith("http") else BASE + u) for u, k in links}})
    return out


FSC_BASE = "https://www.fsc.gov.tw/ch/"
U_FSC = FSC_BASE + "home.jsp?id=96&parentpath=0,2"
FSC_MEASURE = re.compile(r"放空|融券|借券|平盤|穩定措施|市場交易秩序|當日沖銷|漲跌幅|穩定市場|資本市場穩定|股市")
FSC_SKIP = re.compile(r"每日新聞|表揚|交流活動|講座|研討會")


def parse_fsc(page: str) -> List[Dict]:
    """金管會 news rows (date, unit, title, url) that are market-stability measures."""
    out = []
    for m in re.finditer(r'<span class="date"[^>]*>(\d{4}-\d{2}-\d{2})</span>\s*<span class="unit"[^>]*>([^<]*)</span>\s*<span class="title"[^>]*>\s*'
                         r'<a href="([^"]*dataserno=\d+[^"]*)"(?:[^>]*title="([^"]*)")?[^>]*>(.*?)</a>', page or "", re.S):
        title = _text(m.group(4) or m.group(5))       # the link text is cut with "......"; the title attribute is whole
        if FSC_MEASURE.search(title) and not FSC_SKIP.search(title):
            out.append({"date": m.group(1), "unit": m.group(2).strip(), "title": title, "url": FSC_BASE + _html.unescape(m.group(3))})
    return out


def parse_fsc_body(page: str, title: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page or "", flags=re.S)
    lines = [x.strip() for x in _html.unescape(re.sub(r"<[^>]+>", "\n", t)).splitlines() if x.strip()]
    idx = [i for i, x in enumerate(lines) if x == title]
    if not idx:
        return ""
    body = []
    for x in lines[idx[-1] + 1:]:
        if x.startswith(("聯絡單位", "聯絡電話", "瀏覽人次")):
            break
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", x):
            body.append(x)
    return "\n".join(body)


def status(news: List[Dict]) -> Dict:
    """Latest committee decision: on (啟動／繼續) or off (停止), and since when."""
    for r in news:
        if OFF.search(r["title"]):
            return {"state": "off", "since": r["date"], "title": r["title"], "url": r["url"]}
        if ON.search(r["title"]):
            return {"state": "on", "since": r["date"], "title": r["title"], "url": r["url"]}
    return {}


def _get(url: str) -> str:
    import requests
    r = requests.get(url, headers=UA, timeout=40)
    r.raise_for_status()
    return r.content.decode("utf-8", errors="replace")


def _load(f) -> Dict:
    try:
        return json.loads(Path(f).read_text(encoding="utf-8")) if Path(f).exists() else {}
    except (OSError, ValueError):
        return {}


def refresh(force: bool = False) -> Dict:
    d = _load(FILE)
    if not force and time.time() - float(d.get("ts") or 0) < TTL and d.get("news"):
        return _with_seed(d)
    d["ts"] = time.time()
    try:
        news = parse_news(_get(U_NEWS))
        if news:
            bodies = d.get("bodies") or {}
            for r in news[:3]:
                if r["url"] not in bodies:
                    try:
                        bodies[r["url"]] = parse_body(_get(r["url"]), r["title"])[:2000]
                    except Exception as e:  # noqa: BLE001
                        log.info("nsf body unavailable: %s", e)
            d["news"], d["bodies"] = news, {u: b for u, b in bodies.items() if u in {r["url"] for r in news}}
            d["fetched"] = datetime.now(TPE).strftime("%Y-%m-%d %H:%M")
    except Exception as e:  # noqa: BLE001
        log.info("nsf news unavailable: %s", e)
    try:
        fsc = parse_fsc(_get(U_FSC))
        if fsc:
            fb = d.get("fsc_bodies") or {}
            for r in fsc[:3]:
                if r["url"] not in fb:
                    try:
                        fb[r["url"]] = parse_fsc_body(_get(r["url"]), r["title"])[:2500]
                    except Exception as e:  # noqa: BLE001
                        log.info("fsc body unavailable: %s", e)
            old = {r["url"]: r for r in d.get("fsc") or []}
            merged = {**old, **{r["url"]: r for r in fsc}}            # the list page only shows the newest ~15 releases
            d["fsc"] = sorted(merged.values(), key=lambda r: r["date"], reverse=True)[:30]
            d["fsc_bodies"] = {u: b for u, b in fb.items() if u in merged}
    except Exception as e:  # noqa: BLE001
        log.info("fsc news unavailable: %s", e)
    try:
        rep = parse_reports(_get(U_REPORT))
        if rep:
            d["reports"] = rep
    except Exception as e:  # noqa: BLE001
        log.info("nsf reports unavailable: %s", e)
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError:
        pass
    return _with_seed(d)


def _with_seed(d: Dict) -> Dict:
    """PC relay when the cloud cannot reach mof.gov.tw: the seed wins if its newest release is newer."""
    s = _load(SEED)
    mine, theirs = d.get("news") or [], s.get("news") or []
    if theirs and (not mine or theirs[0]["date"] > mine[0]["date"]):
        d.update({k: s.get(k) for k in ("news", "bodies", "fetched") if s.get(k)})
    if s.get("reports") and not d.get("reports"):
        d["reports"] = s["reports"]
    mine, theirs = d.get("fsc") or [], s.get("fsc") or []
    if theirs and (not mine or theirs[0]["date"] > mine[0]["date"]):
        d["fsc"], d["fsc_bodies"] = theirs, {**(d.get("fsc_bodies") or {}), **(s.get("fsc_bodies") or {})}
    d["status"] = status(d.get("news") or [])
    return d


def write_seed(path=SEED) -> Dict:
    d = refresh(force=True)
    out = {k: d.get(k) for k in ("fetched", "news", "bodies", "reports", "fsc", "fsc_bodies")}
    if out.get("news"):
        Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
