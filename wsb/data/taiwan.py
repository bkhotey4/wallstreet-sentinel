"""Taiwan market intelligence (official free sources, verified formats):
  * TWSE BFI82U   — 三大法人買賣金額（每日）
  * TWSE T86      — 個股三大法人買賣超
  * TWSE openapi t187ap05_L — 上市公司月營收
  * TWSE MI_MARGN — 融資融券餘額（融資金額，仟元；格式未在沙盒驗證，採防禦式解析）
  * TAIFEX openapi — 三大法人期貨未平倉、台指期日盤/夜盤、選擇權 Put/Call 比"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..config import DATA_DIR, SETTINGS
from ..health import HEALTH
from .. import store
from . import http

log = logging.getLogger(__name__)
CFG = SETTINGS.get("taiwan", {})
HDR = {"Accept": "application/json, text/plain, */*", "Referer": "https://www.twse.com.tw/"}


def _n(s) -> Optional[float]:
    if s in (None, "", "-", "--", "NULL"):
        return None
    try:
        return float(str(s).replace(",", "").replace("%", "").strip())
    except ValueError:
        return None


def _roc_ym(s: str) -> str:
    """'11508' → '2026/08'"""
    s = str(s)
    return f"{int(s[:-2]) + 1911}/{s[-2:]}" if len(s) >= 4 else s


class TaiwanData:
    def __init__(self) -> None:
        self.flows: List[Dict] = []          # recent days of 三大法人 (億元)
        self.stocks: Dict = {}               # top net buys/sells + watch stocks
        self.futures: Dict = {}              # 期貨法人未平倉、台指期、PC ratio
        self.revenue: List[Dict] = []
        self.margin: Dict = {}               # 融資餘額（億元）與變化
        self.asof = ""
        self.ts = 0.0
        # 個股三大法人每日買賣超（張）存檔：{日期: {代號: [外資, 投信, 三大法人合計]}}，給個股評分算近 5 日籌碼
        self.t86_hist: Dict[str, Dict[str, List[float]]] = {}
        try:
            f = DATA_DIR / "twse_t86.json"
            if f.exists():
                self.t86_hist = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            log.warning("T86 archive unreadable: %s", e)

    # ------------------------------------------------------------ equities
    async def _bfi82u(self, d: date) -> Optional[Dict]:
        js = await http.get("https://www.twse.com.tw/rwd/zh/fund/BFI82U", headers=HDR, timeout=20, retries=1,
                            params={"type": "day", "dayDate": d.strftime("%Y%m%d"), "response": "json"})
        if js.get("stat") != "OK" or not js.get("data"):
            return None
        rows = {r[0]: _n(r[3]) for r in js["data"]}
        def get(prefix):
            vals = [v for k, v in rows.items() if k.startswith(prefix) and v is not None]
            return sum(vals) / 1e8 if vals else None              # missing/renamed row → None, never a fake 0
        out = {"date": d.isoformat(), "foreign": get("外資及陸資"), "trust": get("投信"), "dealer": get("自營商")}
        if out["foreign"] is None:                                 # format changed: skip the day rather than show 0
            log.warning("BFI82U %s: 外資 row not found (format change?)", d)
            return None
        tot = rows.get("合計")
        out["total"] = tot / 1e8 if tot is not None else (None if None in (out["trust"], out["dealer"])
                                                            else out["foreign"] + out["trust"] + out["dealer"])
        return out

    async def _t86(self, d: date) -> Optional[Dict]:
        js = await http.get("https://www.twse.com.tw/rwd/zh/fund/T86", headers=HDR, timeout=30, retries=1,
                            params={"date": d.strftime("%Y%m%d"), "selectType": "ALLBUT0999", "response": "json"})
        return self.parse_t86(js, d)

    def parse_t86(self, js: Dict, d: date) -> Optional[Dict]:
        if js.get("stat") != "OK" or not js.get("data"):
            return None
        f = js["fields"]
        i_code, i_name = 0, 1
        i_for = next(i for i, x in enumerate(f) if x.startswith("外陸資買賣超"))
        i_trust = next(i for i, x in enumerate(f) if x == "投信買賣超股數")
        i_all = next(i for i, x in enumerate(f) if x.startswith("三大法人買賣超"))
        rows = []
        for r in js["data"]:
            code = r[i_code].strip()
            if not re.fullmatch(r"\d{4}", code):          # common stocks only (skip ETFs / warrants)
                continue
            rows.append({"code": code, "name": r[i_name].strip(), "foreign": (_n(r[i_for]) or 0) / 1000,
                         "trust": (_n(r[i_trust]) or 0) / 1000, "all": (_n(r[i_all]) or 0) / 1000})
        # replace the dict instead of mutating it: the stock scorer may be iterating it in a worker thread
        self.t86_hist = {**self.t86_hist, d.isoformat(): {r["code"]: [round(r["foreign"], 1), round(r["trust"], 1),
                                                                      round(r["all"], 1)] for r in rows}}
        watch = set(CFG.get("watch_stocks", ["2330"]))
        return {"date": d.isoformat(),
                "top_buy": sorted([r for r in rows if r["foreign"] > 0], key=lambda x: -x["foreign"])[:8],
                "top_sell": sorted([r for r in rows if r["foreign"] < 0], key=lambda x: x["foreign"])[:8],
                "watch": [r for r in rows if r["code"] in watch]}

    @staticmethod
    def parse_margin(js) -> Optional[Dict]:
        """Find the 融資金額 row anywhere in a MI_MARGN response (old 'data' or new 'tables' layout)."""
        if not isinstance(js, dict) or js.get("stat") not in (None, "OK"):
            return None
        blocks = []
        if isinstance(js.get("data"), list):
            blocks.append((js.get("fields") or [], js["data"]))
        for t in js.get("tables") or []:
            if isinstance(t, dict) and isinstance(t.get("data"), list):
                blocks.append((t.get("fields") or [], t["data"]))
        for fields, rows in blocks:
            for r in rows:
                if r and isinstance(r[0], str) and r[0].replace(" ", "").startswith("融資金額"):
                    nums = [_n(x) for x in r[1:]]
                    if len(nums) >= 5 and nums[3] and nums[4] is not None:
                        prev, today = nums[3], nums[4]
                        return {"bal_bn": today / 1e5, "prev_bn": prev / 1e5,        # 仟元 → 億元
                                "chg_bn": (today - prev) / 1e5, "chg_pct": (today / prev - 1) * 100}
        return None

    async def _margin(self, d: date) -> Optional[Dict]:
        js = await http.get("https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN", headers=HDR, timeout=30, retries=1,
                            params={"date": d.strftime("%Y%m%d"), "selectType": "MS", "response": "json"})
        m = self.parse_margin(js)
        if not m:
            return None
        m["date"] = d.isoformat()
        hist = store.kv_get("tw_margin_hist", {}) or {}
        hist[m["date"]] = m["bal_bn"]
        hist = dict(sorted(hist.items())[-40:])
        store.kv_set("tw_margin_hist", hist)
        old = [(k, v) for k, v in sorted(hist.items()) if k < m["date"]]
        ok = len(old) >= 5 and (date.fromisoformat(m["date"]) - date.fromisoformat(old[-5][0])).days <= 9
        m["chg_5d_pct"] = (m["bal_bn"] / old[-5][1] - 1) * 100 if ok and old[-5][1] else None
        return m

    async def _revenue(self) -> List[Dict]:
        js = await http.get("https://openapi.twse.com.tw/v1/opendata/t187ap05_L", headers=HDR, timeout=40, retries=1)
        watch = CFG.get("revenue_watch", ["2330"])
        order = {c: i for i, c in enumerate(watch)}
        out = []
        for r in js:
            c = r.get("公司代號")
            if c not in order:
                continue
            out.append({"code": c, "name": r.get("公司名稱"), "ym": _roc_ym(r.get("資料年月", "")),
                        "rev_bn": (lambda v: None if v is None else v / 1e5)(_n(r.get("營業收入-當月營收"))),   # 千元 → 億元
                        "mom": _n(r.get("營業收入-上月比較增減(%)")), "yoy": _n(r.get("營業收入-去年同月增減(%)")),
                        "ytd_yoy": _n(r.get("累計營業收入-前期比較增減(%)"))})
        return sorted(out, key=lambda x: order.get(x["code"], 99))

    # ------------------------------------------------------------ futures
    async def _futures(self) -> Dict:
        base = "https://openapi.taifex.com.tw/v1/"
        inst, daily, pcr = await asyncio.gather(
            http.get(base + "MarketDataOfMajorInstitutionalTradersDetailsOfFuturesContractsBytheDate", timeout=40, retries=1),
            http.get(base + "DailyMarketReportFut", timeout=40, retries=1),
            http.get(base + "PutCallRatio", timeout=40, retries=1), return_exceptions=True)
        out: Dict = {}
        if isinstance(inst, list):
            tx = [r for r in inst if r.get("ContractCode") == "臺股期貨"]
            for r in tx:
                who = {"外資及陸資": "foreign", "投信": "trust", "自營商": "dealer"}.get(r.get("Item"))
                if who:
                    out[f"oi_{who}"] = _n(r.get("OpenInterest(Net)"))
                    out[f"vol_{who}"] = _n(r.get("TradingVolume(Net)"))
            if tx:
                out["inst_date"] = tx[0].get("Date")
                # keep a history of foreign net OI to show day-over-day change
                hist = store.kv_get("tw_fut_oi_hist", {}) or {}
                if out.get("oi_foreign") is not None:
                    hist[out["inst_date"]] = out["oi_foreign"]
                    hist = dict(sorted(hist.items())[-30:])
                    store.kv_set("tw_fut_oi_hist", hist)
                prev = [v for k, v in sorted(hist.items()) if k < out["inst_date"]]
                out["oi_foreign_chg"] = out["oi_foreign"] - prev[-1] if prev and out.get("oi_foreign") is not None else None
        if isinstance(daily, list):
            txr = [r for r in daily if r.get("Contract") == "TX" and re.fullmatch(r"\d{6}", str(r.get("ContractMonth(Week)", "")))]
            day = [r for r in txr if r.get("TradingSession") == "一般"]
            if day:
                near = max(day, key=lambda r: _n(r.get("Volume")) or 0)
                m = near["ContractMonth(Week)"]
                night = next((r for r in txr if r.get("TradingSession") == "盤後" and r["ContractMonth(Week)"] == m), None)
                out["tx"] = {"date": near.get("Date"), "month": m, "last": _n(near.get("Last")), "chg": _n(near.get("Change")),
                             "pct": _n(near.get("%")), "oi": _n(near.get("OpenInterest")),
                             "night_last": _n(night.get("Last")) if night else None,
                             "night_chg": _n(night.get("Change")) if night else None,
                             "night_pct": _n(night.get("%")) if night else None}
        if isinstance(pcr, list) and pcr:
            pcr = sorted(pcr, key=lambda r: str(r.get("Date", "")), reverse=True)
            out["pcr"] = [{"date": r.get("Date"), "oi": _n(r.get("PutCallOIRatio%")), "vol": _n(r.get("PutCallVolumeRatio%"))}
                          for r in pcr[:5]]
        return out

    # ------------------------------------------------------------ refresh
    async def refresh(self) -> None:
        every = 1800
        try:
            flows, d = [], date.today()
            tries = 0
            while len(flows) < 5 and tries < 12:
                if d.weekday() < 5:
                    r = await self._bfi82u(d)
                    if r:
                        flows.append(r)
                    await asyncio.sleep(2.5)                         # TWSE rate limit
                d -= timedelta(days=1)
                tries += 1
            self.flows = flows
            if flows:
                self.stocks = await self._t86(date.fromisoformat(flows[0]["date"])) or {}
                self.asof = flows[0]["date"]
                for fl in flows[1:5]:                                 # back-fill the 5-day per-stock flow archive
                    if fl["date"] not in self.t86_hist:
                        await asyncio.sleep(2.5)
                        try:
                            await self._t86(date.fromisoformat(fl["date"]))
                        except Exception as e:  # noqa: BLE001
                            log.info("T86 %s back-fill failed: %s", fl["date"], e)
                self._save_t86()
                try:
                    m = await self._margin(date.fromisoformat(flows[0]["date"]))
                    if m:
                        self.margin = m
                        HEALTH.ok("twse_margin", 1, every=every)
                    else:
                        HEALTH.fail("twse_margin", "response format not recognised", every=every)
                except Exception as e:  # noqa: BLE001
                    log.warning("TWSE margin failed: %s", e)
                    HEALTH.fail("twse_margin", e, every=every)
            HEALTH.ok("twse", len(flows), every=every)
        except Exception as e:  # noqa: BLE001
            log.warning("TWSE failed: %s", e)
            HEALTH.fail("twse", e, every=every)
        try:
            self.futures = await self._futures()
            HEALTH.ok("taifex", len(self.futures), every=every)
        except Exception as e:  # noqa: BLE001
            log.warning("TAIFEX failed: %s", e)
            HEALTH.fail("taifex", e, every=every)
        try:
            self.revenue = await self._revenue()
            HEALTH.ok("twse_revenue", len(self.revenue), every=6 * 3600)
        except Exception as e:  # noqa: BLE001
            log.warning("TWSE revenue failed: %s", e)
            HEALTH.fail("twse_revenue", e, every=6 * 3600)
        self.ts = time.time()

    def _save_t86(self) -> None:
        self.t86_hist = dict(sorted(self.t86_hist.items())[-30:])
        try:
            path = DATA_DIR / "twse_t86.json"
            tmp = path.with_suffix(".json.tmp")                       # atomic: a cancelled run can't truncate it
            tmp.write_text(json.dumps(self.t86_hist, separators=(",", ":")), encoding="utf-8")
            os.replace(tmp, path)
        except Exception as e:  # noqa: BLE001
            log.warning("T86 archive not saved: %s", e)

    def stock_flow(self, code: str, days: int = 5) -> Optional[Dict]:
        """Net buy (張, thousand shares) by 外資 / 投信 / 三大法人 over the last `days` archived sessions."""
        h = self.t86_hist
        ds = sorted(h)[-days:]
        rows = [h[d][code] for d in ds if code in h[d]]
        if not rows:
            return None
        return {"days": len(rows), "foreign": sum(r[0] for r in rows), "trust": sum(r[1] for r in rows),
                "all": sum(r[2] for r in rows), "asof": ds[-1]}

    def summary_lines(self) -> List[str]:
        def sg(x, d=1):
            return "NA" if x is None else f"{x:+,.{d}f}"
        L = []
        if self.flows:
            f = self.flows[0]
            L.append(f"三大法人（{f['date']}）外資 {sg(f['foreign'])} 億、投信 {sg(f.get('trust'))} 億、自營 {sg(f.get('dealer'))} 億；"
                     f"外資近 {len(self.flows)} 日合計 {sum(x['foreign'] for x in self.flows):+.1f} 億")
        fu = self.futures
        if fu.get("oi_foreign") is not None:
            L.append(f"外資台指期未平倉淨額 {sg(fu['oi_foreign'], 0)} 口（日變化 {sg(fu.get('oi_foreign_chg'), 0)}）"
                     f"、投信 {sg(fu.get('oi_trust'), 0)}、自營 {sg(fu.get('oi_dealer'), 0)}")
        if fu.get("tx"):
            t = fu["tx"]
            L.append(f"台指期 {t['month']} 日盤（{t['date']}）{t['last']} ({t['pct']}%)；"
                     f"同日期之盤後場為前一晚交易 {t['night_last']} ({t['night_pct']}%)")
        mg = self.margin
        if mg:
            L.append(f"融資餘額（{mg['date']}）{mg['bal_bn']:,.0f} 億，單日 {sg(mg['chg_pct'], 2)}%"
                     + (f"、近 5 日 {sg(mg['chg_5d_pct'], 2)}%" if mg.get("chg_5d_pct") is not None else "")
                     + "（融資單日大減＝可能出現斷頭賣壓）")
        if fu.get("pcr"):
            L.append(f"台指選擇權 Put/Call 未平倉比 {fu['pcr'][0]['oi']}%")
        for r in self.revenue[:4]:
            L.append(f"{r['name']} {r['ym']} 營收 {'NA' if r['rev_bn'] is None else format(r['rev_bn'], ',.0f')} 億，月增 {sg(r['mom'])}%、年增 {sg(r['yoy'])}%、累計年增 {sg(r['ytd_yoy'])}%")
        return L
