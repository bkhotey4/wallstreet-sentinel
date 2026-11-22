"""台股「公司自己的動作」（2026-11-22 台股覆蓋檢討）：庫藏股與內部人申報轉讓。

* 庫藏股：公開資訊觀測站「買回自己公司股份彙總統計表」（ajax_t35sc09，上市 sii／上櫃 otc，依董事會決議日期查詢）。
  買回目的：1＝轉讓給員工、2＝配合可轉債或認股權轉換、3＝維護公司信用及股東權益（股價大跌時最常見）。
  11/21 金管會鼓勵上市櫃公司實施庫藏股（可納入 ESG 評鑑），之後兩週有多少公司真的宣布，是「公司自己覺得股價太低」的直接證據。
* 內部人申報轉讓：證交所 OpenAPI t187ap12_L（每天只給當天的申報），本站每次存下來累積 60 天。董監、大股東要賣（或贈與、信託）
  必須事前申報；股價大跌時內部人還在申報賣出，和公司宣布庫藏股一起看。
雲端常連不到公開資訊觀測站：庫藏股由電腦端寫進 research_feed/tw_corp_seed.json（附抓取時間），雲端讀不到時用它。
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..config import DATA_DIR

log = logging.getLogger(__name__)
URL_TSB = "https://mopsov.twse.com.tw/mops/web/ajax_t35sc09"
URL_INS = "https://openapi.twse.com.tw/v1/opendata/t187ap12_L"
FILE = DATA_DIR / "econ_tw_corp.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_corp_seed.json"
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
PURPOSE = {"1": "轉讓給員工", "2": "配合轉換或認股", "3": "維護公司信用及股東權益"}
TTL = 6 * 3600
KEEP_DAYS = 60
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)


def roc(d: date) -> str:
    return f"{d.year - 1911}{d.month:02d}{d.day:02d}"


def roc_iso(s: str) -> Optional[str]:
    m = re.match(r"\s*(\d{2,3})/?(\d{2})/?(\d{2})", s or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)) + 1911, int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def _n(s: str) -> Optional[float]:
    try:
        return float(re.sub(r"[,\s]", "", s or ""))
    except ValueError:
        return None


def parse_buybacks(page: str, board: str) -> List[Dict]:
    out = []
    for row in _ROW.findall(page or ""):
        c = [re.sub(r"<[^>]+>", "", x).strip() for x in _TD.findall(row)]
        if len(c) < 12 or not re.fullmatch(r"\d{4}[A-Z]?", c[1]):
            continue
        out.append({"code": c[1], "name": c[2], "date": roc_iso(c[3]), "purpose": PURPOSE.get(c[4], c[4]), "purpose_id": c[4],
                    "max_amt": _n(c[5]), "shares": _n(c[6]), "lo": _n(c[7]), "hi": _n(c[8]),
                    "start": roc_iso(c[9]), "end": roc_iso(c[10]), "done": c[11] == "Y", "board": board})
    return out


def fetch_buybacks(today: Optional[date] = None, days: int = 45) -> List[Dict]:
    import requests
    today = today or date.today()
    rows: List[Dict] = []
    for typek, board in (("sii", "上市"), ("otc", "上櫃")):
        r = requests.post(URL_TSB, data={"encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "TYPEK": typek,
                                         "d1": roc(today - timedelta(days=days)), "d2": roc(today), "RD": 1}, headers=UA, timeout=20)
        r.encoding = "utf-8"
        rows += parse_buybacks(r.text, board) if r.ok else []
        time.sleep(1.0)
    if not rows:
        raise RuntimeError("MOPS buyback list empty (blocked or changed)")
    return sorted(rows, key=lambda x: (x["date"] or "", x["code"]), reverse=True)


def parse_insiders(rows: List[Dict]) -> List[Dict]:
    out = []
    for r in rows or []:
        code = str(r.get("公司代號") or "").strip()
        if not code:
            continue
        out.append({"code": code, "name": str(r.get("公司名稱") or "").strip(), "date": roc_iso(str(r.get("出表日期") or "")),
                    "who": str(r.get("申報人身分") or "").strip(), "how": str(r.get("預定轉讓方式及股數-轉讓方式") or "").strip(),
                    "shares": _n(str(r.get("預定轉讓總股數-自有持股") or "")) or 0.0, "held": _n(str(r.get("目前持有股數-自有持股") or "")),
                    "period": str(r.get("有效轉讓期間") or "").strip()})
    return out


def _load(f: Path) -> Dict:
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except (OSError, ValueError):
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FILE)


def refresh(force: bool = False) -> Dict:
    """Buybacks (MOPS, else the PC seed) + the insider archive (TWSE OpenAPI, accumulated)."""
    import requests
    d = _load(FILE)
    if not force and time.time() - float(d.get("ts") or 0) < TTL and d.get("buybacks") is not None:
        return d
    d["ts"] = time.time()
    try:
        d["buybacks"] = fetch_buybacks()
        d["bb_fetched"] = _tpe_now()
    except Exception as e:  # noqa: BLE001
        log.info("MOPS buybacks unavailable here (%s); using seed", e)
        s = _load(SEED)
        if str(s.get("fetched") or "") > str(d.get("bb_fetched") or ""):
            d["buybacks"], d["bb_fetched"] = s.get("buybacks") or [], s.get("fetched")
    try:
        r = requests.get(URL_INS, headers=UA, timeout=20)
        new = parse_insiders(r.json()) if r.ok else []
        have = {(x["code"], x["date"], x["who"], x["shares"]): x for x in d.get("insiders") or []}
        for x in new:
            have.setdefault((x["code"], x["date"], x["who"], x["shares"]), x)
        cut = (date.today() - timedelta(days=KEEP_DAYS)).isoformat()
        d["insiders"] = sorted((x for x in have.values() if (x.get("date") or "") >= cut), key=lambda x: x.get("date") or "", reverse=True)
        d["ins_fetched"] = _tpe_now()
    except Exception as e:  # noqa: BLE001
        log.info("TWSE insider filings unavailable (%s)", e)
    try:
        _save(d)
    except OSError:
        pass
    return d


def write_seed(path: Path = SEED) -> Dict:
    """PC → cloud relay for the MOPS buyback list (public company announcements)."""
    bb = fetch_buybacks()
    out = {"fetched": _tpe_now(), "source": "公開資訊觀測站買回自己公司股份彙總統計表", "buybacks": bb}
    Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def _tpe_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
