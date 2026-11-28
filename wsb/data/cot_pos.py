"""期貨部位：大戶押哪一邊（CFTC 交易者持倉報告 TFF，2026-11-28 華爾街視角盤點）。

交易台每週五看 CFTC 持倉報告：資產管理人（退休金、共同基金，多半是長期多單）和槓桿基金（避險基金，常是短線、
借錢的部位）在標普 500、那斯達克 100、日圓、比特幣期貨的淨部位。重點不是方向，是「擁擠」：淨部位落在自己過去
3 年的極端（前後 10%），壞消息來時大家同時要平倉，價格會被放大（2024-08 日圓空單擁擠，平倉時日股一天跌 12%）。

來源：https://publicreporting.cftc.gov/resource/gpe5-46if.json（官方公開 API、免金鑰；資料是每週二的部位，
週五公布，假日週會延到下週一）。只用固定規則：淨部位占未平倉量的比例，對自己過去 156 週排百分位。"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Optional

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_cot_pos.json"            # econ_* is kept by the site workflow's cache
URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
TTL = 12 * 3600
UA = {"User-Agent": "Mozilla/5.0 (WallStreet Sentinel research)"}
MARKETS = {"13874A": ("標普 500 期貨", "ES"), "209742": ("那斯達克 100 期貨", "NQ"),
           "097741": ("日圓期貨", "JPY"), "133741": ("比特幣期貨", "BTC")}
WEEKS = 156                                      # 3 years of weekly reports
EXTREME = 10.0                                   # percentile band at either end that counts as crowded


def parse(rows: List[Dict]) -> Dict[str, List[List]]:
    """Pure: {sym: [[date, open interest, asset-manager net, leveraged-fund net], ...] oldest first}."""
    out: Dict[str, Dict[str, List]] = {}
    for r in rows or []:
        m = MARKETS.get(r.get("cftc_contract_market_code"))
        if not m:
            continue
        try:
            oi = float(r["open_interest_all"])
            am = float(r["asset_mgr_positions_long"]) - float(r["asset_mgr_positions_short"])
            lv = float(r["lev_money_positions_long"]) - float(r["lev_money_positions_short"])
        except (KeyError, TypeError, ValueError):
            continue
        if oi <= 0:
            continue
        out.setdefault(m[1], {})[str(r.get("report_date_as_yyyy_mm_dd") or "")[:10]] = [oi, am, lv]
    return {s: [[d, *v] for d, v in sorted(by.items())] for s, by in out.items()}


def _pctile(vals: List[float], v: float) -> Optional[float]:
    return float(sum(x < v for x in vals) / len(vals) * 100) if len(vals) >= 52 else None


def view(d: Dict) -> Dict[str, Dict]:
    """Pure: per market — latest net as % of open interest for both groups, its 3-year percentile, 1-week change, crowding."""
    out = {}
    for code, (zh, sym) in MARKETS.items():
        rows = (d.get("rows") or {}).get(sym) or []
        if len(rows) < 53:
            continue
        hist = rows[-(WEEKS + 1):]
        am = [r[2] / r[1] * 100 for r in hist]
        lv = [r[3] / r[1] * 100 for r in hist]
        v = {"zh": zh, "date": rows[-1][0], "am": am[-1], "lev": lv[-1], "am_p": _pctile(am[:-1], am[-1]), "lev_p": _pctile(lv[:-1], lv[-1]),
             "lev_wk": lv[-1] - lv[-2]}
        v["crowd"] = [k for k, p in (("am", v["am_p"]), ("lev", v["lev_p"])) if p is not None and (p >= 100 - EXTREME or p <= EXTREME)]
        out[sym] = v
    return out


def text(v: Dict) -> str:
    """One plain sentence for a market's positioning (net long/short, how unusual)."""
    def side(x: float) -> str:
        return f"淨多單 {x:.0f}%" if x >= 0 else f"淨空單 {-x:.0f}%"

    def rank(p: Optional[float]) -> str:
        if p is None:
            return ""
        return ("（比過去 3 年九成的時候都偏多）" if p >= 100 - EXTREME else "（比過去 3 年九成的時候都偏空）" if p <= EXTREME
                else f"（3 年第 {p:.0f} 百分位）")
    return (f"{v['zh']}：資產管理人{side(v['am'])}{rank(v['am_p'])}、避險基金{side(v['lev'])}{rank(v['lev_p'])}"
            f"（占未平倉量，{v['date'][5:]}）")


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def refresh(force: bool = False, now: float = 0) -> Dict:
    d = load()
    now = now or time.time()
    if not force and now - float(d.get("ts_try") or 0) < TTL:
        return d
    d["ts_try"] = now
    codes = ",".join(f"'{c}'" for c in MARKETS)
    try:
        js = await http.get(URL, params={"$select": "report_date_as_yyyy_mm_dd,cftc_contract_market_code,open_interest_all,"
                                                    "asset_mgr_positions_long,asset_mgr_positions_short,lev_money_positions_long,lev_money_positions_short",
                                         "$where": f"cftc_contract_market_code in({codes}) AND report_date_as_yyyy_mm_dd >= '2020-01-01'",
                                         "$order": "report_date_as_yyyy_mm_dd", "$limit": "5000"},
                            kind="json", headers=UA, timeout=60, retries=1)
        rows = parse(js if isinstance(js, list) else [])
        if not rows:
            raise ValueError("no rows")
        d.update(rows=rows, ts=now)
        HEALTH.ok("cot_pos", sum(len(v) for v in rows.values()), every=TTL)
    except Exception as e:  # noqa: BLE001
        HEALTH.fail("cot_pos", str(e) or type(e).__name__, every=TTL)
        log.info("CFTC positioning: %s", e)
    FILE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d
