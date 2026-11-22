"""MSCI 台灣指數成分股（以追蹤它的 ETF 持股近似；2026-11-22，台股覆蓋清單「指數調整（MSCI）」）。

MSCI 官網（msci.com 的 index review 頁）有機器人驗證，ir.msci.com 回 403，iShares EWT 持股檔要先選投資人身分——本站都不繞過。
改用台灣上市、追蹤「MSCI臺灣指數」的元大 MSCI台灣 ETF（006203）在發行投信網站公開的每日持股：
  https://www.yuantaetfs.com/product/detail/006203/ratio
頁面 HTML 只直接列前 5 檔，完整持股在頁面內嵌的 window.__NUXT__ 狀態（一個「參數＋引數」的 JS 函式）。
這裡用純文字解析參數與引數清單（不執行下載來的 JavaScript），還原 FundWeights.StockWeights。
每天存一份快照；MSCI 季度審查生效日（2、5、8、11 月最後一個交易日收盤）前後的快照差異＝實際加入／刪除的成分股。
ETF 持股會因申贖、現金與期貨部位和指數權重有小差異，所以叫「近似」。"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import DATA_DIR

log = logging.getLogger(__name__)
FILE = DATA_DIR / "tw_msci.json"
SEED = Path(__file__).resolve().parents[2] / "research_feed" / "tw_msci_seed.json"
URL = "https://www.yuantaetfs.com/product/detail/006203/ratio"
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research site)"}
TTL = 6 * 3600
KEEP = 400            # days of snapshots kept (about five reviews)
TPE = timezone(timedelta(hours=8))


# ------------------------------------------------------------------ a tiny JS-literal reader (no evaluation)
class _Id(str):
    """A bare identifier inside the NUXT function body (stands for one of the function's parameters)."""


def _ws(s: str, i: int) -> int:
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    return i


def _value(s: str, i: int) -> Tuple[Any, int]:
    i = _ws(s, i)
    c = s[i]
    if c == '"':
        j = i + 1
        while s[j] != '"':
            j += 2 if s[j] == "\\" else 1
        return json.loads(s[i:j + 1]), j + 1
    if c == "{":
        out, i = {}, _ws(s, i + 1)
        while s[i] != "}":
            m = re.compile(r'"[^"]*"|[A-Za-z_$][\w$]*').match(s, i)
            if not m:
                raise ValueError(f"bad key at {i}")
            k = json.loads(m.group(0)) if m.group(0).startswith('"') else m.group(0)
            i = _ws(s, m.end())
            if s[i] != ":":
                raise ValueError(f"no colon at {i}")
            out[k], i = _value(s, i + 1)
            i = _ws(s, i)
            if s[i] == ",":
                i = _ws(s, i + 1)
        return out, i + 1
    if c == "[":
        out, i = [], _ws(s, i + 1)
        while s[i] != "]":
            v, i = _value(s, i)
            out.append(v)
            i = _ws(s, i)
            if s[i] == ",":
                i = _ws(s, i + 1)
        return out, i + 1
    if s.startswith("void 0", i):
        return None, i + 6
    m = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?").match(s, i)
    if m:
        t = m.group(0)
        return (float(t) if any(x in t for x in ".eE") else int(t)), m.end()
    m = re.compile(r"Array\((\d+)\)").match(s, i)          # NUXT writes empty sparse arrays as Array(n)
    if m:
        return [None] * int(m.group(1)), m.end()
    m = re.compile(r"[A-Za-z_$][\w$]*").match(s, i)
    if m:
        t = m.group(0)
        return {"true": True, "false": False, "null": None}.get(t, _Id(t)) if t in ("true", "false", "null") else _Id(t), m.end()
    raise ValueError(f"unexpected {c!r} at {i}")


def _args(s: str, i: int) -> List[Any]:
    """Comma-separated literals starting at s[i] (just after the opening parenthesis of the call)."""
    out = []
    i = _ws(s, i)
    while s[i] != ")":
        v, i = _value(s, i)
        out.append(v)
        i = _ws(s, i)
        if s[i] == ",":
            i += 1
    return out


def _resolve(v: Any, env: Dict[str, Any]) -> Any:
    if isinstance(v, _Id):
        return env.get(v, v)
    if isinstance(v, list):
        return [_resolve(x, env) for x in v]
    if isinstance(v, dict):
        return {k: _resolve(x, env) for k, x in v.items()}
    return v


def parse(page: str) -> Dict:
    """→ {date, stocks: [{code, name, w, qty}], futures, stocks_value} or {}."""
    m = re.search(r"window\.__NUXT__=\(function\(([^)]*)\)\{", page or "")
    if not m:
        return {}
    params = [p.strip() for p in m.group(1).split(",")]
    end = page.find("</script>", m.end())
    script = page[m.end():end]
    env: Dict[str, Any] = {}
    for k in range(len(script) - 1, 0, -1):          # the call's '(' comes right after the function body's last '}'
        if script[k] == "(" and script[k - 1] == "}":
            try:
                vals = _args(script, k + 1)
            except (ValueError, IndexError):
                continue
            if len(vals) == len(params):
                env = dict(zip(params, vals))
                break
    if not env:
        return {}
    j = script.find("FundWeights:{")
    sw = script.find("StockWeights:[", j)
    if j < 0 or sw < 0:
        return {}
    try:
        rows, _ = _value(script, sw + len("StockWeights:"))
        summ_at = script.find("Summary:", j)
        summ = _resolve(_value(script, summ_at + len("Summary:"))[0], env) if 0 <= summ_at < sw else {}
    except (ValueError, IndexError) as e:
        log.info("msci parse: %s", e)
        return {}
    stocks = []
    for r in _resolve(rows, env):
        code, w = str(r.get("code") or "").strip(), r.get("weights")
        if re.fullmatch(r"\d{4,6}[A-Z]?", code) and isinstance(w, (int, float)):
            stocks.append({"code": code, "name": str(r.get("name") or "").strip(), "w": float(w), "qty": r.get("qty")})
    dm = re.search(r"交易日期:\s*(?:<[^>]+>\s*)*(\d{4})/(\d{2})/(\d{2})", page)
    return {"date": f"{dm.group(1)}-{dm.group(2)}-{dm.group(3)}" if dm else None, "stocks": sorted(stocks, key=lambda x: -x["w"]),
            "stocks_value": (summ or {}).get("stkvalues"), "futures": (summ or {}).get("futvalues")} if stocks else {}


# ------------------------------------------------------------------ snapshots and changes
def changes(snaps: Dict[str, Dict], around: Optional[str] = None) -> Dict:
    """Constituents added / removed between consecutive snapshots that differ. With `around` (an effective date), compare the last
    snapshot on or before it with the first one after it."""
    days = sorted(snaps)
    if len(days) < 2:
        return {}
    if around:
        before = [d for d in days if d < around]         # the effective day's own file may already be the new list
        after = [d for d in days if d > around]
        if not before or not after:
            return {}
        a, b = before[-1], after[0]
    else:
        a, b = days[-2], days[-1]
    A, B = snaps[a].get("stocks") or {}, snaps[b].get("stocks") or {}
    add = [{"code": c, "name": B[c][0], "w": B[c][1]} for c in B if c not in A]
    rem = [{"code": c, "name": A[c][0], "w": A[c][1]} for c in A if c not in B]
    return {"from": a, "to": b, "add": sorted(add, key=lambda x: -x["w"]), "rem": sorted(rem, key=lambda x: -x["w"])}


def _load(f) -> Dict:
    try:
        return json.loads(Path(f).read_text(encoding="utf-8")) if Path(f).exists() else {}
    except (OSError, ValueError):
        return {}


def _get() -> str:
    import requests
    r = requests.get(URL, headers=UA, timeout=40)
    r.raise_for_status()
    return r.content.decode("utf-8", errors="replace")


def refresh(force: bool = False) -> Dict:
    d = _load(FILE)
    if not force and time.time() - float(d.get("ts") or 0) < TTL and d.get("snaps"):
        return _with_seed(d)
    d["ts"] = time.time()
    try:
        p = parse(_get())
        if p.get("date") and len(p["stocks"]) >= 30:              # a partial page must not look like 60 deletions
            snaps = d.get("snaps") or {}
            snaps[p["date"]] = {"stocks": {s["code"]: [s["name"], s["w"]] for s in p["stocks"]},
                                "stocks_value": p.get("stocks_value"), "futures": p.get("futures")}
            for k in sorted(snaps)[:-KEEP]:
                snaps.pop(k)
            d["snaps"] = snaps
            d["fetched"] = datetime.now(TPE).strftime("%Y-%m-%d %H:%M")
    except Exception as e:  # noqa: BLE001
        log.info("msci taiwan holdings unavailable: %s", e)
    try:
        tmp = FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FILE)
    except OSError:
        pass
    return _with_seed(d)


def _with_seed(d: Dict) -> Dict:
    """The PC keeps the long snapshot history (a cloud build starts with an empty cache); merge both, newer wins per day."""
    s = _load(SEED)
    snaps = {**(s.get("snaps") or {}), **(d.get("snaps") or {})}
    if snaps:
        d["snaps"] = snaps
    if not d.get("fetched"):
        d["fetched"] = s.get("fetched")
    return d


def write_seed(path=SEED) -> Dict:
    d = refresh(force=True)
    old = _load(path).get("snaps") or {}
    snaps = {**old, **(d.get("snaps") or {})}
    out = {"fetched": d.get("fetched"), "snaps": {k: snaps[k] for k in sorted(snaps)[-KEEP:]}}
    if out["snaps"]:
        Path(path).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
