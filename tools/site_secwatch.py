"""SEC 人事申報警報的名單：每次建置寫 sec_watch.json（公開），給 /api/news 的 Cloudflare 函式比對 SEC 最新 8-K。

名單＝本站追蹤池（公開的那份）＋財報日曆裡出現過、市值 ≥ 1,000 億美元的公司；用 SEC 官方 ticker → CIK 對照。
不含任何持股資料。格式 {"ts":…, "ciks": {"1045810": ["NVDA", "輝達"], …}, "names": {"NVDA": ["輝達", "Nvidia"], …}}。

names 是給「多家媒體同時報導」比對標題用的（2026-11-14）：[中文名, 英文名（可用 | 分隔多個寫法）]。英文名來自追蹤池的英文簡稱，
或財報日曆的公司全名去掉 Inc.／Corp.／Holdings 這類字尾；去掉之後是常見單字的（Target、Visa、Block…）不比對，寧可漏掉也不要認錯。"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Dict, List

log = logging.getLogger(__name__)

# 標題裡常見的另一種寫法（公司自己的品牌名），不是資料，是比對規則
ALIAS = {"GOOGL": "Google|Alphabet", "GOOG": "Google|Alphabet", "META": "Meta|Facebook", "BRK-B": "Berkshire", "TSM": "TSMC|Taiwan Semiconductor",
         "JPM": "JPMorgan|JP Morgan", "XOM": "Exxon", "JNJ": "Johnson & Johnson|J&J", "PG": "Procter & Gamble|P&G", "LLY": "Eli Lilly|Lilly",
         "GS": "Goldman Sachs|Goldman", "ARM": "Arm Holdings", "NU": "Nubank|Nu Holdings", "SMCI": "Super Micro|Supermicro", "BAC": "Bank of America|BofA",
         "C": "Citigroup|Citi", "AXP": "American Express|Amex", "SCHW": "Charles Schwab|Schwab", "PEP": "PepsiCo|Pepsi", "MCD": "McDonald's|McDonald’s",
         "GM": "General Motors|GM", "LMT": "Lockheed Martin|Lockheed", "NOC": "Northrop Grumman|Northrop", "KTOS": "Kratos", "ANET": "Arista",
         "SMR": "NuScale", "LEU": "Centrus", "EOG": "EOG Resources", "NEE": "NextEra", "PANW": "Palo Alto Networks", "V": "", "LOW": "Lowe's|Lowe’s"}
# 去掉字尾後只剩這些字的不比對：開頭大寫時也常常不是那家公司
AMBIG = {"Target", "Visa", "Block", "Gap", "Arm", "Dow", "Nu", "Progressive", "Southern", "Booking", "Williams", "Unity", "Snap", "Match", "Square",
         "Monster", "Capital", "Royal", "Bank", "American", "General", "Canadian", "Western", "National", "United", "First", "Banco", "Automatic"}
TAIL = (r"Inc|Incorporated|Corp|Corporation|Company|Companies|Co|Ltd|Limited|plc|PLC|p\.l\.c|N\.V|NV|S\.A|SA|AG|SE|ASA|Holdings?|Group|"
        r"Technology|Technologies|Pharmaceuticals|Sciences|Laboratories|Motor|Health|Healthcare|Financial|International|US|Ord|Energy")


def short_en(full: str) -> str:
    """'Gilead Sciences, Inc.' → 'Gilead'; '' when what is left is too short or an everyday word."""
    x = re.sub(r"\((?:The)\)", " ", full or "")
    if re.search(r"-\s", x):                               # "Petroleo Brasileiro S.A.- Petrobras" → the name after the dash
        x = x.split("-")[-1]
    x = re.sub(r"\s+", " ", x).strip(" ,.")
    for _ in range(4):
        y = re.sub(r"[,\s]+(?:" + TAIL + r")\.?$", "", x).strip(" ,.")
        if y == x:
            break
        x = y
    if not x or not re.fullmatch(r"[A-Za-z0-9&'’. -]+", x) or x in AMBIG:
        return ""
    if " " not in x and len(x) < 4 and not (x.isupper() and len(x) >= 3):
        return ""
    return x


def zh_key(zh: str) -> str:
    """The Chinese name as headlines write it: '台積電 ADR' → '台積電'; '' when it is not Chinese."""
    x = re.sub(r"（.*?）", "", zh or "")
    x = re.sub(r"[A-Za-z0-9&.\s]+$", "", x).strip()
    return x if len(x) >= 2 and re.search(r"[一-鿿]", x) and not re.search(r"[A-Za-z]", x) else ""


def names_of(names: Dict, big: Dict, syms: List[str]) -> Dict[str, list]:
    out: Dict[str, list] = {}
    for s in syms:
        if s in names:
            v = names[s]
            en = ALIAS[s] if s in ALIAS else (v[1] if len(v) > 1 and v[1] not in AMBIG else "")
            zk = zh_key(v[0])
        else:
            en = ALIAS[s] if s in ALIAS else short_en((big.get(s) or {}).get("name") or "")
            zk = ""
        if en or zk:
            out[s] = [zk, en]
    return out


def build(eng) -> Dict:
    from wsb.data.stocks import universe
    from wsb.data import earn_official as EO
    from wsb.data.edgar_holdings import _MAP_FILE
    names = (universe().get("us") or {}).get("symbols", {})
    ed = getattr(eng, "earnings", None)
    big = EO.universe((getattr(ed, "days", None) or {}) if ed is not None else {}, [], EO.load().get("known"))
    try:
        tmap = json.loads(_MAP_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        tmap = {}
    out: Dict[str, list] = {}
    for s in list(names) + [k for k, v in big.items() if (v.get("mcap") or 0) >= 1e11]:
        cik = (tmap.get(s) or tmap.get(s.replace("-", ".")) or {}).get("cik")
        if cik and str(int(cik)) not in out:
            zh = names[s][0] if s in names else (big.get(s) or {}).get("name") or s
            out[str(int(cik))] = [s, zh]
    return {"ts": int(time.time()), "ciks": out, "names": names_of(names, big, [v[0] for v in out.values()])}
