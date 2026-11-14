"""SEC 重大申報警報（建置端）：追蹤公司申報 8-K 第 5.02 項（董事或高階主管離職、任命、薪酬安排），或少見而本身就是新聞的
項目（1.03 破產、1.05 重大資安事件、2.06 資產減損、3.01 下市通知、4.02 財報須重編；2026-11-14 起加上 2.04 債務被要求提前清償、
5.01 控制權變動、2.05 裁員或關廠重整、2.01 完成重大收購或出售），就記下來，保留 3 天。
另外讀 SEC 最新的 Schedule 13D（有人持股逾 5% 而且不排除介入經營；13D/A 是更新），對象是追蹤公司時也記一則。

即時的部分在 Cloudflare 函式 /api/news（每 2 分鐘看 SEC 最新 100 份 8-K）；SEC 的「最新申報」清單忙的時候 1～2 小時就滾掉，
所以每次建置也翻頁讀到上次看過的地方，記進 data_cache/econ_sec502.json（CI 保留 econ_*），寫成公開的 sec_alerts.json，
函式把它和即時清單合併，警報不會因為清單滾動而消失。
判斷「離職／任命／薪酬」與職位（執行長、財務長…）只看申報原文第 5.02 項開頭的文字，判斷不出來就只寫「高層人事異動」。"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from html import unescape
from typing import Dict, List, Optional

from ..config import DATA_DIR, SEC_USER_AGENT
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_sec502.json"
FEED = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include"
        "&count=100&start={start}&output=atom")
HDR = {"User-Agent": SEC_USER_AGENT}
KEEP_S = 3 * 86400
PAGES = 8
KIND_V = 2                      # bump when kind() changes: stored personnel alerts are read again once
FEED_13D = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SCHEDULE+13D&company=&dateb=&owner=include"
            "&count=100&start={start}&output=atom")
PAGES_13D = 3


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except (OSError, ValueError):
        return {}


def _text(x: str) -> str:
    x = re.sub(r"<!\[CDATA\[(.*?)\]\]>", lambda m: m.group(1), x or "", flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(re.sub(r"<[^>]+>", " ", x)))).strip()   # escaped HTML too


def parse_feed(xml: str) -> List[Dict]:
    """Every 8-K entry: {cik, ts, url, acc, items}."""
    out = []
    for e in re.findall(r"<entry>.*?</entry>", xml or "", re.S):
        title = _text((re.search(r"<title>(.*?)</title>", e, re.S) or [None, ""])[1])
        cm = re.search(r"\((\d{10})\)", title)
        um = re.search(r'<link[^>]*href="([^"]+)"', e)
        tm = re.search(r"<updated>([^<]+)</updated>", e)
        if not (cm and um and tm):
            continue
        try:
            ts = int(datetime.fromisoformat(tm.group(1)).timestamp())
        except ValueError:
            continue
        summ = _text((re.search(r"<summary[^>]*>(.*?)</summary>", e, re.S) or [None, ""])[1])
        am = re.search(r"accession-number=([\d-]+)", e) or re.search(r"AccNo:\s*([\d-]+)", summ)
        acc = am.group(1) if am else ""
        out.append({"cik": str(int(cm.group(1))), "ts": ts, "url": um.group(1).replace("http://", "https://"), "acc": acc,
                    "items": re.findall(r"Item (\d\.\d\d)", summ)})
    return out


def parse_13d(xml: str) -> List[Dict]:
    """Schedule 13D / 13D/A filings, one row each: {cik (the company held), filer, form, ts, url, acc}."""
    by: Dict[str, Dict] = {}
    for e in re.findall(r"<entry>.*?</entry>", xml or "", re.S):
        title = _text((re.search(r"<title>(.*?)</title>", e, re.S) or [None, ""])[1])
        m = re.match(r"SCHEDULE 13D(/A)?\s*-\s*(.*?)\s*\((\d{10})\)\s*\((Subject|Filed by)\)", title)
        am = re.search(r"accession-number=([\d-]+)", e)
        um = re.search(r'<link[^>]*href="([^"]+)"', e)
        tm = re.search(r"<updated>([^<]+)</updated>", e)
        if not (m and am and um and tm):
            continue
        try:
            ts = int(datetime.fromisoformat(tm.group(1)).timestamp())
        except ValueError:
            continue
        d = by.setdefault(am.group(1), {"acc": am.group(1), "ts": ts, "form": "13D/A" if m.group(1) else "13D", "filer": "", "cik": ""})
        if m.group(4) == "Subject":
            d["cik"], d["url"] = str(int(m.group(3))), um.group(1).replace("http://", "https://")
        elif not d["filer"]:
            d["filer"] = m.group(2).strip()
    return [d for d in by.values() if d["cik"] and d.get("url")]


def main_doc(index_html: str) -> str:
    """The 8-K document itself from a filing index page (the row typed 8-K), not an exhibit such as the press release."""
    for row in re.findall(r"<tr.*?</tr>", index_html or "", re.S | re.I):
        m = re.search(r'href="(?:/ix\?doc=)?(/Archives/edgar/data/[^"]+?\.htm)"', row)       # inline-XBRL viewer links too
        if m and re.search(r">\s*8-K\s*<", row):
            return m.group(1)
    return ""


def kind(text: str) -> Dict[str, str]:
    """離職 / 任命 / 薪酬安排 and the seat, from the start of Item 5.02 in the filing."""
    t = text[:12000]
    i = re.search(r"Item\s*5\.02", t, re.I)
    w = t[i.start(): i.start() + 4000] if i else t
    # the item's standard heading names every kind ("Departure of Directors…; Appointment…; Compensatory Arrangements…") — drop it
    w = re.sub(r"Item\s*5\.02[.:]?\s*Departure of Directors.*?Compensatory Arrangements of Certain Officers\.?", " ", w, count=1, flags=re.I | re.S)
    w = re.split(r"Item\s*9\.01", w, maxsplit=1, flags=re.I)[0]
    # the seat comes from the sentence that carries the action, not from biographies further down
    # ("…appointment of three independent directors…"; a new director's bio may say "former Chief Executive Officer of X")
    sents = re.split(r"(?<=[.;])\s+", w)
    leave = r"resign|step(?:ped|s)? down|retire|depart|terminat|will not stand|leave the company"
    join = r"appoint|named|elect|promot"
    pay = r"compensat|bonus|award|salary|incentive"
    what, sent = "", ""
    for lab, rx in (("離職", leave), ("任命", join), ("薪酬安排", pay)):
        sent = next((x for x in sents if re.search(rx, x, re.I)), "")
        if sent:
            what = lab
            break
    seat = ""
    if what in ("離職", "任命"):
        seat = ("執行長" if re.search(r"Chief Executive Officer|\bCEO\b", sent) else "財務長" if re.search(r"Chief Financial Officer|\bCFO\b", sent)
                else "營運長" if re.search(r"Chief Operating Officer|\bCOO\b", sent)
                else "董事長" if re.search(r"Chair(?:man|woman|person)? of the Board|Chair\b", sent)
                else "董事" if re.search(r"independent director|to (?:its|the|our) Board|as (?:a )?director|board of directors", sent, re.I)
                else "總裁" if re.search(r"President", sent) else "董事" if re.search(r"director|Board", sent, re.I) else "")
    return {"what": what, "seat": seat}


# the 8-K items worth an alert: rare, and each one is news on its own (routine items like 7.01 / 8.01 / 9.01 are not;
# 1.01 重大合約 is left out on purpose: big companies file it for every credit line)
ITEMS = {"5.02": "高層人事異動", "1.03": "破產或接管", "1.05": "重大資安事件", "2.06": "重大資產減損",
         "3.01": "收到下市或不符上市規定通知", "4.02": "過去財報不可再信賴（須重編）",
         "2.04": "債務被要求提前清償（觸發違約或加速條款）", "5.01": "公司控制權變動",
         "2.05": "裁員或關廠重整（認列退出成本）", "2.01": "完成重大收購或資產出售"}
# how loud each one is: 4 = the company itself is in question; 3 = a restructuring, or a new 5 % holder who may push for change;
# 2 = a deal closing (usually announced earlier); 1 = an update to an existing 13D
SEV = {"1.03": 4, "1.05": 4, "2.06": 4, "3.01": 4, "4.02": 4, "2.04": 4, "5.01": 4, "2.05": 3, "2.01": 2, "13D": 3, "13D/A": 1}


def pick_item(items: List[str]) -> Optional[str]:
    """The loudest alert item in one 8-K; 5.02 only when none of the rare ones is there."""
    rare = [i for i in items if i in ITEMS and i != "5.02"]
    return max(rare, key=lambda i: SEV[i]) if rare else ("5.02" if "5.02" in items else None)


def severity(a: Dict) -> int:
    """The item's own level (see SEV); for personnel filings +2 a departure, +1 a top seat (CEO / CFO / chair).
    ≥ 3 is a filing worth an extra voice edition and a direct message."""
    t, item = a.get("t", ""), a.get("item", "5.02")
    if item != "5.02":
        return SEV.get(item, 4)
    return (2 if "離職" in t else 0) + (1 if re.search(r"執行長|財務長|董事長", t) else 0)


def title_of(sym: str, zh: str, k: Dict[str, str], item: str = "5.02") -> str:
    if item in ("13D", "13D/A"):
        who = k.get("filer") or "有股東"
        return (f"SEC 申報：{who} 申報持有 {zh}（{sym}）逾 5% 股權，不排除介入經營（Schedule 13D）" if item == "13D"
                else f"SEC 申報：{who} 更新對 {zh}（{sym}）的大股東持股申報（Schedule 13D/A）")
    if item != "5.02":
        return f"SEC 申報：{zh}（{sym}）{ITEMS[item]}（8-K 第 {item} 項）"
    body = f'{k.get("seat") or "高層"}{k["what"]}' if k.get("what") else "高層人事異動"
    return f"SEC 申報：{zh}（{sym}）{body}（8-K 第 5.02 項）"


async def read_kind(index_url: str) -> Optional[Dict[str, str]]:
    """Open the filing index, then the 8-K document, and classify it; None when SEC could not be read."""
    try:
        doc = main_doc(await http.get(index_url, kind="text", headers=HDR, timeout=30, retries=1))
        if not doc:
            return {"what": "", "seat": ""}
        return kind(_text(await http.get("https://www.sec.gov" + doc, kind="text", headers=HDR, timeout=30, retries=1)))
    except Exception as e:  # noqa: BLE001
        log.info("SEC 8-K %s: %s", index_url, e)
        return None


async def refresh(watch: Dict[str, list], now: float = 0) -> Dict:
    """Page the SEC current-8-K feed back to the last entry seen; record 5.02 filings by watched companies."""
    now = now or time.time()
    st = load()
    seen_ts = int(st.get("last_ts") or (now - 6 * 3600))
    alerts = {a["acc"]: a for a in st.get("alerts") or [] if now - a["ts"] < KEEP_S}
    for a in alerts.values():                            # written under older rules → classify again from the filing
        if a.get("item", "5.02") == "5.02" and a.get("v") != KIND_V:
            k = await read_kind(a["url"])
            if k is not None:
                a.update(k, v=KIND_V, t=title_of(a["sym"], a["zh"], k))
    newest = seen_ts
    for p in range(PAGES):
        xml = await http.get(FEED.format(start=p * 100), kind="text", headers=HDR, timeout=30, retries=1)
        rows = parse_feed(xml)
        if not rows:
            break
        for r in rows:
            newest = max(newest, r["ts"])
            hit = watch.get(r["cik"])
            item = pick_item(r["items"])
            if hit and item and r["acc"] and r["acc"] not in alerts and now - r["ts"] < KEEP_S:
                k = {"what": "", "seat": ""}
                if item == "5.02":                           # only personnel filings need the text read
                    k = (await read_kind(r["url"])) or k
                alerts[r["acc"]] = {"acc": r["acc"], "ts": r["ts"], "sym": hit[0], "zh": hit[1], "url": r["url"], **k, "item": item, "v": KIND_V,
                                    "t": title_of(hit[0], hit[1], k, item)}
        if min(r["ts"] for r in rows) <= seen_ts:
            break
    last13 = int(st.get("last_13d") or (now - 6 * 3600))
    new13 = last13
    try:                                                 # 大股東申報：一份申報有兩列（Subject＝被持股的公司、Filed by＝申報人）
        for p in range(PAGES_13D):
            rows = parse_13d(await http.get(FEED_13D.format(start=p * 100), kind="text", headers=HDR, timeout=30, retries=1))
            if not rows:
                break
            for r in rows:
                new13 = max(new13, r["ts"])
                hit = watch.get(r["cik"])
                if hit and r["acc"] not in alerts and now - r["ts"] < KEEP_S:
                    k = {"what": "", "seat": "", "filer": r["filer"]}
                    alerts[r["acc"]] = {"acc": r["acc"], "ts": r["ts"], "sym": hit[0], "zh": hit[1], "url": r["url"], **k, "item": r["form"],
                                        "v": KIND_V, "t": title_of(hit[0], hit[1], k, r["form"])}
            if min(r["ts"] for r in rows) <= last13:
                break
    except Exception as e:  # noqa: BLE001
        log.info("SEC 13D feed: %s", e)
    st = {"last_ts": newest, "last_13d": new13, "alerts": sorted(alerts.values(), key=lambda a: -a["ts"]), "ts": int(now)}
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    tmp.replace(FILE)
    return st


def public(st: Dict) -> Dict:
    """sec_alerts.json: the same item shape /api/news uses."""
    tg = lambda i: "人事" if i == "5.02" else "大股東" if i.startswith("13D") else "重大申報"  # noqa: E731
    return {"ts": st.get("ts", 0), "items": [{"t": a["t"], "u": a["url"], "s": "SEC 申報", "ts": a["ts"], "lang": "zh", "off": True,
                                             "tags": ["美股", tg(a.get("item", "5.02"))], "alert": a.get("item") != "13D/A",   # an update to an old 13D is listed, not pinned
                                             "sym": a["sym"], "kind": a.get("what", ""),
                                             "item": a.get("item", "5.02"), "sev": severity(a)}
                                            for a in st.get("alerts") or []]}
