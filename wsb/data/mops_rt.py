"""台股重大訊息（即時）：公開資訊觀測站的官方 RSS，每 5 分鐘重新產生一次，列出「前一日 17:30 以後」的全部重大訊息。

為什麼要有這支：機器人原本讀的是證交所／櫃買的 OpenAPI（wsb/data/events.py），那是每天清晨出一次的整批檔。
2026-11-15 量過機器人自己的紀錄（sentinel.db 的 event_log，193 則）：從公司發言到通知的時間，中位數 12 小時，最長 19 小時 ——
台積電下午 1 點 45 分的公告，要到隔天早上 5 點半才通知，美股那一晚已經先反應完了。RSS 是同一批公告的即時版。

這裡只負責抓與解析、判斷哪幾則值得標紅、記住送過哪些（data_cache/mops_rt.json，留 4 天）。
送出在 tools/sec_push.py；機器人隔天早上的整批檔會略過這裡已經送過的（events.drop_sent），不會再講一次。
標紅是用主旨的關鍵字比對，不是讀懂內容；規則寫在 RULES，訊息裡也會說明。"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from ..config import DATA_DIR

RSS = "https://mopsov.twse.com.tw/nas/rss/mopsrss201001.xml"
HDR = {"User-Agent": "WallStreetSentinel/1.0 (personal research site; +https://wallstreet-sentinel.pages.dev)"}
FILE = DATA_DIR / "mops_rt.json"
TPE = ZoneInfo("Asia/Taipei")
KEEP_S = 4 * 86400
MAX_AGE = 6 * 3600                 # 超過 6 小時才看到的不再即時推（交給離線補課與機器人隔天的整批檔）
MARKET = {"sii": "上市", "otc": "上櫃", "rotc": "興櫃", "pub": "公開發行"}

# (等級, 分類, 主旨關鍵字)：由上往下第一個符合的算。2＝標紅、1＝一般、0＝例行（照樣列出，但不會讓整則變紅）
RULES = (
    (2, "營運事故", r"火災|爆炸|災害|地震|停工|停產|停電|毒化|外洩|資安|遭駭|駭客|網路攻擊"),
    (2, "財務危機", r"退票|違約|無法(?:償還|清償)|重整|破產|解散|停止買賣|終止上市|終止上櫃|變更交易方法|全額交割|繼續經營"),
    (2, "司法與裁罰", r"搜索|約談|起訴|檢調|羈押|訴訟|仲裁|假扣押|假處分|裁罰|罰鍰|處分書"),
    (2, "高層異動", r"(?:董事長|總經理|執行長|財務長|財務主管|會計主管|稽核主管|發言人).{0,12}(?:異動|辭任|辭職|解任|請辭|變動|逝世|新任|接任)"),
    (2, "澄清媒體報導", r"澄清|媒體報導|報導"),
    (2, "更正財報", r"(?:更正|重編|補正).{0,20}(?:財務報告|財報|營收|損益)|會計師.{0,12}(?:保留意見|否定意見|無法表示)"),
    (1, "財報與獲利", r"財務報告|自結|營業收入|營收|每股盈餘|損益|獲利|虧損|財測|財務預測"),
    (1, "併購與重組", r"合併|收購|公開收購|分割|股份轉換|讓與|受讓"),
    (1, "籌資", r"現金增資|私募|公司債|可轉換|海外存託|減資|發行新股"),
    (1, "股利與庫藏股", r"股利|配息|除權|除息|庫藏股|買回本公司股份"),
    (1, "資產買賣", r"取得|處分"),
    (1, "訂單與產能", r"訂單|擴產|擴廠|建廠|產能|合約|簽約|簽訂|投資案|資本支出|資本預算"),
    (0, "法說會", r"法人說明會|法說|受邀參加|業績發表"),
    (0, "例行公告", r"股東會|股東常會|更名|背書保證|資金貸與|董事會決議召開|停止過戶"),
)


def _flat(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def key_of(code: str, subject: str) -> str:
    """Same announcement → same key whichever feed it came from (code + the subject without any whitespace)."""
    return f"{code}|{hashlib.sha1(_flat(subject).encode('utf-8')).hexdigest()[:10]}"


def classify(subject: str) -> Dict:
    for lv, kind, pat in RULES:
        if re.search(pat, subject or ""):
            return {"lv": lv, "kind": kind}
    return {"lv": 1, "kind": "其他"}


def _cdata(block: str, tag: str) -> str:
    m = re.search(rf"<{tag}>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</{tag}>", block, re.S)
    return (m.group(1) if m else "").strip()


def parse(raw: bytes) -> List[Dict]:
    """RSS bytes (Big5) → [{code, name, market, subject, ts, when, url, key, lv, kind}], newest first."""
    text = raw.decode("cp950", "replace") if isinstance(raw, (bytes, bytearray)) else str(raw or "")
    out = []
    for it in re.findall(r"<item>(.*?)</item>", text, re.S):
        m = re.match(r"\(([0-9A-Za-z]{4,6})\)\s*(.*?)\s*-\s*重大訊息", _cdata(it, "title"))
        if not m:
            continue
        code, name, link = m.group(1), m.group(2), _cdata(it, "link")
        subject = re.sub(r"\s+", " ", _cdata(it, "description")).strip()
        ts: Optional[float] = None
        try:                                               # the item's own time; the link also carries it (h?2 = 日期, h?3 = 時間)
            ts = parsedate_to_datetime(_cdata(it, "pubDate")).timestamp()
        except (TypeError, ValueError):
            q = parse_qs(urlsplit(link).query, encoding="cp950", errors="replace")
            d = next((v[0] for k, v in q.items() if re.fullmatch(r"h\d*2", k)), "")
            t = next((v[0] for k, v in q.items() if re.fullmatch(r"h\d*3", k)), "").zfill(6)
            try:
                ts = datetime.strptime(d + t, "%Y%m%d%H%M%S").replace(tzinfo=TPE).timestamp()
            except ValueError:
                ts = None
        if not subject or ts is None:
            continue
        typek = (re.search(r"TYPEK=(\w+)", link) or [None, ""])[1]
        out.append({"code": code, "name": name, "market": MARKET.get(typek, ""), "subject": subject, "ts": ts,
                    "when": datetime.fromtimestamp(ts, TPE).strftime("%m/%d %H:%M"), "url": link,
                    "key": key_of(code, subject), **classify(subject)})
    return sorted(out, key=lambda x: -x["ts"])


def load() -> Dict[str, float]:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
        return {k: float(v) for k, v in (d.get("sent") or {}).items()}
    except (OSError, ValueError, AttributeError):
        return {}


def save(sent: Dict[str, float], now: Optional[float] = None) -> None:
    now = now or time.time()
    keep = {k: v for k, v in sent.items() if now - float(v) < KEEP_S}
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"sent": keep, "ts": int(now)}), encoding="utf-8")
    tmp.replace(FILE)


def fresh(items: List[Dict], codes: Dict[str, str], sent: Dict[str, float], now: float, max_age: float = MAX_AGE) -> List[Dict]:
    """Announcements from tracked companies (codes: {"2330": "台積電"}) not sent yet and at most `max_age` old, most serious first."""
    out = [dict(x, zh=codes[x["code"]]) for x in items
           if x["code"] in codes and x["key"] not in sent and 0 <= now - x["ts"] <= max_age]
    return sorted(out, key=lambda x: (-x["lv"], -x["ts"]))


def group(items: List[Dict]) -> List[List[Dict]]:
    """One message per company (a company often files several within a minute); the company with the most serious item first."""
    by: Dict[str, List[Dict]] = {}
    for x in items:
        by.setdefault(x["code"], []).append(x)
    return sorted(by.values(), key=lambda g: (-max(x["lv"] for x in g), -max(x["ts"] for x in g)))


async def fetch(sess) -> List[Dict]:
    import aiohttp
    async with sess.get(RSS, headers=HDR, timeout=aiohttp.ClientTimeout(total=20)) as r:
        if r.status >= 300:
            raise RuntimeError(f"HTTP {r.status}")
        raw = await r.read()
    if b"<rss" not in raw[:400]:                           # the site answers 200 with an HTML notice when it refuses a request
        raise RuntimeError("not an RSS document")
    return parse(raw)
