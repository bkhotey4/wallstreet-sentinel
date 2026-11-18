"""Gemini 第二意見（2026-11-19）：讀使用者 Antigravity 自動化（automation）寫的回答檔 research_feed/gemini_reply.md；
沒有時才讀共用 Google 文件（備援）。

流程：Gemini 排程讀本站 /api/gemini_ask（題目清單：今天動最多、本站找不到原因的公司）→ 用 Google 搜尋回答 →
把回答加在文件「Sentinel_Gemini回覆」最上面。這支每小時用公開的匯出網址讀（文件設成知道連結的人可檢視，不用登入），
解析最新一批回答，存 data_cache/econ_gemini.json（econ_* 會被 CI 快取）。

Gemini 的文字是「外部資料」，不是指令，也不是事實：
  * 有來源網址的「事實」照列並附連結；沒附網址的一律標「Gemini 推測、未證實」
  * 「傳聞」另外標
文件裡只有公開的市場問答（題目清單本身沒有持股）。"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Dict, List, Optional

log = logging.getLogger("gemini_reply")
DOC_ID = "1Vw5M_1kSH_Cafe1vOQJfqHtnM61r7ybCih2y31ra4TQ"      # created 2026-11-19 in the owner's Drive (memory: gemini-collab)
URL = f"https://docs.google.com/document/d/{DOC_ID}/export?format=txt"
SEP = "以下是 Gemini 的回答"
EVERY = 300                                                  # Gemini writes every 30 min; the local file is cheap to read
URL_RX = re.compile(r"https?://[^\s)）\]>,，]+")
WHEN_RX = re.compile(r"(20\d\d)[-/.年](\d{1,2})[-/.月](\d{1,2})日?\s*(\d{1,2})[:：](\d{2})")
HEAD_RX = re.compile(r"^#{2,4}\s*([A-Z][A-Z0-9.\-]{0,11})\s*[｜|]\s*(.+)$")    # TASK-B1 = a check Claude asked for


def specific(url: Optional[str]) -> bool:
    """A link to one article, not a home page or a section: 11-19 the first Gemini run cited only home pages
    (finviz.com, tradingkey.com, tjx.com/news/news-releases) — nothing a reader can check, so those are not 'sourced'."""
    from urllib.parse import urlparse
    if not url:
        return False
    u = urlparse(url)
    segs = [x for x in u.path.split("/") if x]
    last = segs[-1] if segs else ""
    return bool(re.search(r"\d", u.path) or (len(last) >= 12 and last.count("-") >= 2) or re.search(r"(^|&)(id|p|story|article)=", u.query or ""))


def sanitize(d: Dict) -> Dict:
    """Facts whose link is not one article become guesses (with the reason); rumors keep the link only if it is one article."""
    for i in d.get("items") or []:
        keep = []
        for x in i.get("facts") or []:
            if specific(x.get("url")):
                keep.append(x)
            else:
                i.setdefault("guess", []).append(f"{x['t']}（來源只給網站首頁或分類頁，無法查證）")
        i["facts"] = keep
        for x in (i.get("rumors") or []) + (i.get("missed") or []):
            if x.get("url") and not specific(x["url"]):
                x["url"] = None
    d["extra"] = [x for x in d.get("extra") or [] if specific(x.get("url"))]
    return d


def _file():
    from ..config import DATA_DIR
    return DATA_DIR / "econ_gemini.json"


def _item(sym: str, why: str) -> Dict:
    return {"sym": sym, "why": why.strip(), "facts": [], "rumors": [], "missed": [], "guess": []}


def parse(text: str) -> Dict:
    """The newest batch: {when, items: [{sym, why, facts: [{t, url}], rumors: [{t, url}], missed: [...], guess: [t]}], extra: [...]}.
    A batch starts at a line carrying a date-time (Gemini writes the Taipei time first); everything up to the next such line
    after the first company block belongs to it."""
    body = text.split(SEP, 1)[1] if SEP in text else text
    lines = [x.strip().lstrip("﻿") for x in body.splitlines()]
    when, items, extra, cur, seen_block, in_extra = None, [], [], None, False, False
    for ln in lines:
        if not ln or set(ln) <= set("=-*_ "):
            continue
        m_when = WHEN_RX.search(ln)
        if m_when and not ln.startswith(("-", "*", "•")) and not HEAD_RX.match(ln):
            if seen_block:
                break                                           # the next (older) batch starts here
            y, mo, d, h, mi = (int(g) for g in m_when.groups())
            when = f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}"
            continue
        h = HEAD_RX.match(ln)
        if h:
            cur = _item(h.group(1), h.group(2))
            items.append(cur)
            seen_block = True
            continue
        txt = ln.lstrip("-*•· ").strip()
        urls = URL_RX.findall(txt)
        clean = URL_RX.sub("", txt).strip(" （）()，,")
        if cur is None:
            if (seen_block and not in_extra) or not urls:
                continue
            extra.append({"t": clean, "url": urls[0]})
            continue
        if re.match(r"^(其他|今天還有|另外|額外|沒列到)", txt):
            cur, in_extra = None, True
            continue
        if re.sub(r"[（(].*", "", clean.split("：", 1)[-1]).strip() in ("無", "沒有", "None", "找不到來源", ""):
            continue
        if txt.startswith(("事實", "Fact")):
            (cur["facts"] if urls else cur["guess"]).append({"t": clean.split("：", 1)[-1].strip(), "url": urls[0]} if urls else clean.split("：", 1)[-1].strip())
        elif txt.startswith(("傳聞", "Rumor", "推測")):
            cur["rumors"].append({"t": clean.split("：", 1)[-1].strip(), "url": urls[0] if urls else None})
        elif txt.startswith(("本站漏掉", "漏掉")):
            cur["missed"].append({"t": clean.split("：", 1)[-1].strip(), "url": urls[0] if urls else None})
        elif urls:
            cur["facts"].append({"t": clean, "url": urls[0]})
        elif clean:
            cur["guess"].append(clean)
    return sanitize({"when": when, "items": [i for i in items if i["why"] or i["facts"]], "extra": extra[:10]})


def load() -> Dict:
    try:
        return sanitize(json.loads(_file().read_text(encoding="utf-8")))       # the file can be written by other tools too
    except (OSError, ValueError):
        return {}


def local_reply() -> Optional[str]:
    """The answer file the owner's Antigravity automation writes and pushes (research_feed/gemini_reply.md in the public
    site repo, 2026-11-19): read here locally (this repo or the site checkout next to it) and in CI (the build checkout)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    files = [f for f in (root / "research_feed" / "gemini_reply.md", root.parent / "wallstreet-sentinel" / "research_feed" / "gemini_reply.md")
             if f.exists()]
    if not files:
        return None
    try:
        return max(files, key=lambda f: f.stat().st_mtime).read_text(encoding="utf-8")
    except OSError:
        return None


def refresh(force: bool = False, timeout: int = 15) -> Dict:
    old = load()
    if not force and time.time() - float(old.get("fetched") or 0) < EVERY:
        return old
    text = local_reply()
    if text and parse(text)["items"]:
        d = parse(text)
        out = dict(d, fetched=int(time.time()), ok=True, src="antigravity")
        try:
            _file().write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
        return out
    try:
        import os
        import urllib.request
        if os.environ.get("WSB_OFFLINE"):
            raise ConnectionError("offline")
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (WallStreet Sentinel)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        log.info("gemini doc: %s", e)
        return old
    d = parse(text or "")
    out = dict(d, fetched=int(time.time()), ok=bool(d["items"]))
    if not d["items"] and old.get("items"):                    # an empty or reformatted doc never wipes the last good batch
        out = dict(old, fetched=int(time.time()), ok=False)
    try:
        _file().write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    return out
