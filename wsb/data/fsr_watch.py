"""聯準會《金融穩定報告》點名、本站原本沒在看的四個壓力點（每月盤點 research_feed/coverage.json 找出的缺口）。

  * 避險基金槓桿（OFR 避險基金監測，Form PF 季資料，2013 年起）：總資產÷淨資產（整體槓桿）、前 10 大基金平均槓桿與資產占比，
    加上 FICC 擔保回購量（避險基金借錢做美債基差交易的主要管道，約兩週一筆）。槓桿在自己歷史最高 10% 而且 CFTC 基差交易也偏大 → 黃燈。
  * 家庭貸款（紐約聯準會家庭債務與信用報告，季資料，2003 年起）：每類貸款「這一季新變成逾期 90 天以上」占餘額比率，
    和自己過去 10 年比；車貸或信用卡落在最高 10% → 黃燈。報告沒有 FHA/VA 房貸分項，這裡沒放。
  * 銀行（FDIC 全體銀行申報彙總，季資料，2010 年起）：證券帳面損益（持有到期＋備供出售，公允價值減攤銷成本）占股東權益，
    以及未保險存款占總存款；帳面損失落在 2010 年以來最大 10% → 黃燈。2023 年矽谷銀行就是這兩項同時偏高。
  * 房價租金比（FRED：Case-Shiller 全國房價 ÷ CPI 房租），和 1987 年以來比；落在最高 10% → 黃燈。
快取 data_cache/econ_fsr.json（CI 保留 econ_*），每天一次。描述現況，不是預測。"""
from __future__ import annotations

import io
import json
import logging
import os
import time
from datetime import date
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_fsr.json"
TTL = 24 * 3600
OFR = "https://data.financialresearch.gov/hf/v1/series/timeseries"
OFR_PAGE = "https://www.financialresearch.gov/hedge-fund-monitor/"
HF_IDS = {"gav": "FPF-ALLQHF_GAV_SUM", "nav": "FPF-ALLQHF_NAV_SUM", "top10_lev": "FPF-ALLQHF_GAVN10_LEVERAGERATIO_AVERAGE",
          "top10_share": "FPF-ALLQHF_GAVN10_GAV_SHARE", "repo": "FICC-SPONSORED_REPO_VOL"}
NYF = "https://www.newyorkfed.org/medialibrary/interactives/householdcredit/data/xls/HHD_C_Report_{q}.xlsx"
NYF_PAGE = "https://www.newyorkfed.org/microeconomics/hhdc"
LOANS = (("AUTO", "車貸"), ("CC", "信用卡"), ("MORTGAGE", "房貸"), ("STUDENT LOAN", "學貸"))
FDIC = "https://api.fdic.gov/banks/financials"
FDIC_PAGE = "https://www.fdic.gov/quarterly-banking-profile"
FDIC_FIELDS = "SCHA,SCHF,SCAA,SCAF,EQ,DEPUNINS,DEP"
HPI, RENT = "CSUSHPISA", "CUSR0000SEHA"
FRED_IDS = (HPI, RENT)
HOT = 90.0                           # 自己歷史的第 90 百分位以上 → 偏高


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def quarters(today: date, n: int = 5) -> List[str]:
    """Report names to try, newest first: the quarter before today's, then older ones (the New York Fed posts ~5 weeks after quarter end)."""
    y, q = today.year, (today.month - 1) // 3 + 1
    out = []
    for _ in range(n):
        q -= 1
        if q == 0:
            y, q = y - 1, 4
        out.append(f"{y}Q{q}")
    return out


def _qdate(lab: str) -> Optional[str]:
    """'26:Q2' → '2026-06-30'."""
    try:
        yy, q = str(lab).strip().split(":Q")
        y = 2000 + int(yy)
        return (pd.Timestamp(year=y, month=int(q) * 3, day=1) + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def parse_nyfed(raw: bytes) -> Dict[str, Dict[str, float]]:
    """Page 14 (new 90+ day delinquent balances, % of balance) and Page 12 (stock 90+), by loan type."""
    x = pd.ExcelFile(io.BytesIO(raw))
    out = {}
    for sheet, key in (("Page 14 Data", "flow"), ("Page 12 Data", "stock")):
        df = x.parse(sheet, header=None)
        hdr = next(i for i in range(12) if "AUTO" in [str(v).strip() for v in df.iloc[i].tolist()])
        cols = {str(v).strip(): j for j, v in enumerate(df.iloc[hdr].tolist())}
        for code, _ in LOANS:
            m = {}
            for _, r in df.iloc[hdr + 1:].iterrows():
                d, v = _qdate(r.iloc[0]), pd.to_numeric(r.iloc[cols[code]], errors="coerce")
                if d and pd.notna(v):
                    m[d] = float(v)
            out[f"{key}:{code}"] = m
    if len(out.get("flow:AUTO") or {}) < 40:
        raise ValueError("New York Fed: too few quarters")
    return out


def parse_fdic(js: Dict) -> List[Dict]:
    rows = []
    for x in (js or {}).get("data") or []:
        r = x.get("data") or {}
        try:
            eq = float(r["sum_EQ"])
            rows.append({"date": f'{r["REPDTE"][:4]}-{r["REPDTE"][4:6]}-{r["REPDTE"][6:]}',
                         "unreal": (float(r["sum_SCHF"]) - float(r["sum_SCHA"]) + float(r["sum_SCAF"]) - float(r["sum_SCAA"])) / 1e6,
                         "eq": eq / 1e6, "unins": float(r["sum_DEPUNINS"]) / float(r["sum_DEP"]) * 100})
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    rows.sort(key=lambda r: r["date"])
    if len(rows) < 30:
        raise ValueError(f"FDIC: only {len(rows)} quarters")
    return rows


async def refresh(force: bool = False) -> Dict:
    from .freshness import bundle_ts, due
    d = load()
    now = time.time()
    d["ts_check"] = now
    keys = ["hf", "hh", "bank"]
    each = d.setdefault("ts_each", {})
    todo = due(d, keys, TTL, now, force)
    if todo:
        bad = []
        if "hf" in todo:
            d["try_each"]["hf"] = now
            try:
                hf = {k: await http.get(OFR, params={"mnemonic": m}, timeout=60, retries=1) for k, m in HF_IDS.items()}
                if len(hf["gav"] or []) < 40:
                    raise ValueError("OFR: too few quarters")
                d["hf"], each["hf"] = hf, now
            except Exception as e:  # noqa: BLE001
                bad.append(f"hf: {e if str(e) else type(e).__name__}")
        if "hh" in todo:
            d["try_each"]["hh"] = now
            err = "no report found"
            for q in quarters(date.today()):
                try:
                    raw = await http.get(NYF.format(q=q), kind="bytes", timeout=90, retries=0, headers={"User-Agent": "Mozilla/5.0"})
                    if not raw[:2] == b"PK":
                        continue
                    d["hh"], d["hh_q"], each["hh"] = parse_nyfed(raw), q, now
                    err = ""
                    break
                except Exception as e:  # noqa: BLE001
                    err = f"{q}: {e if str(e) else type(e).__name__}"
            if err:
                bad.append(f"hh: {err}")
        if "bank" in todo:
            d["try_each"]["bank"] = now
            try:
                js = await http.get(FDIC, params={"filters": "REPDTE:[20100101 TO 99991231]", "fields": "REPDTE", "agg_by": "REPDTE",
                                                  "agg_sum_fields": FDIC_FIELDS, "agg_limit": "300", "limit": "1"}, timeout=120, retries=1)
                d["bank"], each["bank"] = parse_fdic(js), now
            except Exception as e:  # noqa: BLE001
                bad.append(f"bank: {e if str(e) else type(e).__name__}")
        bad += [f"{k}: stale" for k in keys if k not in todo and now - float(each.get(k, 0)) > TTL * 3]
        d["ts"] = bundle_ts(d, keys)
        if bad:
            log.warning("FSR watch data: %s", "; ".join(bad))
            HEALTH.fail("fsr_watch", "; ".join(bad), every=TTL)
        else:
            HEALTH.ok("fsr_watch", len(d.get("bank") or []), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def _ser(pairs) -> pd.Series:
    if isinstance(pairs, dict):
        pairs = list(pairs.items())
    s = pd.Series({pd.Timestamp(a): float(b) for a, b in pairs or [] if b is not None}, dtype=float)
    return s.sort_index().dropna()


def _pct(hist: pd.Series, v: float) -> Optional[float]:
    """Share of earlier observations below v (the latest value's rank in its own past)."""
    hist = hist.dropna()
    return float((hist < v).mean() * 100) if len(hist) >= 12 else None


def _hist(s: pd.Series, n: int = 40) -> List[List]:
    return [[i.strftime("%Y-%m-%d"), round(float(v), 3)] for i, v in s.tail(n).items()]


def hedge(hf: Dict, basis_pct: Optional[float] = None) -> Optional[Dict]:
    gav, nav = _ser(hf.get("gav")), _ser(hf.get("nav"))
    lev = (gav / nav).dropna()
    if len(lev) < 12:
        return None
    t10, sh, repo = _ser(hf.get("top10_lev")), _ser(hf.get("top10_share")), _ser(hf.get("repo"))
    out = {"date": lev.index[-1].strftime("%Y-%m-%d"), "since": lev.index[0].strftime("%Y"), "lev": float(lev.iloc[-1]),
           "lev_pct": _pct(lev.iloc[:-1], float(lev.iloc[-1])), "lev_max": float(lev.max()), "lev_max_date": lev.idxmax().strftime("%Y-%m-%d"),
           "gav": float(gav.iloc[-1]) / 1e12, "nav": float(nav.iloc[-1]) / 1e12, "hist": _hist(lev), "basis_pct": basis_pct}
    if len(t10):
        out.update(top10=float(t10.iloc[-1]), top10_pct=_pct(t10.iloc[:-1], float(t10.iloc[-1])))
    if len(sh):
        out["share"] = float(sh.iloc[-1])
    if len(repo) > 30:
        yago = repo[repo.index <= repo.index[-1] - pd.DateOffset(years=1)]
        out.update(repo=float(repo.iloc[-1]) / 1e9, repo_date=repo.index[-1].strftime("%Y-%m-%d"),
                   repo_yoy=float(repo.iloc[-1] / yago.iloc[-1] - 1) * 100 if len(yago) else None)
    hot = (out["lev_pct"] or 0) >= HOT
    if hot and (basis_pct or 0) >= HOT:
        out["emoji"], out["state"] = "🟡", "槓桿偏高，基差交易也偏大"
    elif hot:
        out["emoji"], out["state"] = "🟢", "槓桿偏高，但基差交易不大"
    else:
        out["emoji"], out["state"] = "🟢", "槓桿在歷史常見範圍"
    return out


def household(hh: Dict, q: str = "") -> Optional[Dict]:
    rows = []
    for code, zh in LOANS:
        f, s = _ser(hh.get(f"flow:{code}")), _ser(hh.get(f"stock:{code}"))
        if len(f) < 44:
            continue
        ten = f[f.index > f.index[-1] - pd.DateOffset(years=10)].iloc[:-1]
        yago = f[f.index <= f.index[-1] - pd.DateOffset(years=1)]
        rows.append({"code": code, "zh": zh, "flow": float(f.iloc[-1]), "p10": _pct(ten, float(f.iloc[-1])),
                     "flow_1y": float(yago.iloc[-1]) if len(yago) else None, "max": float(f.max()), "max_date": f.idxmax().strftime("%Y-%m"),
                     "stock": float(s.iloc[-1]) if len(s) else None, "hist": _hist(f)})
    if not rows:
        return None
    f0 = _ser(hh.get("flow:AUTO"))
    hot = [r["zh"] for r in rows if r["code"] in ("AUTO", "CC") and (r["p10"] or 0) >= HOT]
    return {"date": f0.index[-1].strftime("%Y-%m-%d"), "q": q, "rows": rows, "hot": hot,
            "emoji": "🟡" if hot else "🟢", "state": f"{'、'.join(hot)}新增嚴重逾期在 10 年高檔" if hot else "新增嚴重逾期沒有特別高"}


def banks(rows: List[Dict]) -> Optional[Dict]:
    if not rows or len(rows) < 12:
        return None
    df = pd.DataFrame(rows).set_index("date")
    ratio = (df["unreal"] / df["eq"] * 100).astype(float)
    loss = -ratio
    now = float(ratio.iloc[-1])
    yago = ratio.iloc[-5] if len(ratio) > 4 else None
    worst = ratio.idxmin()
    out = {"date": df.index[-1], "since": df.index[0][:4], "unreal": float(df["unreal"].iloc[-1]) / 1e3, "eq": float(df["eq"].iloc[-1]) / 1e3,
           "ratio": now, "ratio_1y": float(yago) if yago is not None else None, "loss_pct": _pct(loss.iloc[:-1], -now),
           "worst": float(ratio.min()), "worst_date": worst, "unins": float(df["unins"].iloc[-1]),
           "unins_pct": _pct(df["unins"].iloc[:-1], float(df["unins"].iloc[-1])),
           "hist": [[k, round(float(v), 2)] for k, v in ratio.tail(40).items()]}
    if (out["loss_pct"] or 0) >= HOT:
        out["emoji"], out["state"] = "🟡", "證券帳面損失在 2010 年以來最大 10%"
    elif now < 0:
        out["emoji"], out["state"] = "🟢", "還有帳面損失，但比高峰時小"
    else:
        out["emoji"], out["state"] = "🟢", "證券沒有帳面損失"
    return out


def rent_ratio(get) -> Optional[Dict]:
    h, r = get(HPI), get(RENT)
    if h is None or r is None:
        return None
    j = pd.concat([h, r], axis=1, join="inner").dropna()
    if len(j) < 120:
        return None
    x = j.iloc[:, 0] / j.iloc[:, 1]
    x = x / x.iloc[0] * 100
    now = float(x.iloc[-1])
    peak = x[x.index < "2010-01-01"]
    out = {"date": x.index[-1].strftime("%Y-%m"), "since": x.index[0].strftime("%Y"), "idx": now, "pct": _pct(x.iloc[:-1], now),
           "peak06": float(peak.max()) if len(peak) else None, "peak06_date": peak.idxmax().strftime("%Y-%m") if len(peak) else None,
           "max": float(x.max()), "max_date": x.idxmax().strftime("%Y-%m"),
           "hist": [[i.strftime("%Y-%m-%d"), round(float(v), 1)] for i, v in x.resample("QE").last().tail(60).items()]}
    out["emoji"], out["state"] = ("🟡", "房價相對房租在歷史高檔") if (out["pct"] or 0) >= HOT else ("🟢", "房價相對房租沒有特別高")
    return out


def view(eng=None, basis_pct: Optional[float] = None) -> Dict:
    d = load()
    fr = getattr(eng, "fred", None)
    get = (lambda sid: fr.get(sid)) if fr is not None else (lambda sid: None)
    out = {"ts": d.get("ts"), "ts_each": d.get("ts_each") or {}}
    for k, fn in (("hedge", lambda: hedge(d.get("hf") or {}, basis_pct)), ("house", lambda: household(d.get("hh") or {}, d.get("hh_q", ""))),
                  ("bank", lambda: banks(d.get("bank") or [])), ("rent", lambda: rent_ratio(get))):
        try:
            out[k] = fn()
        except Exception:  # noqa: BLE001
            log.exception("FSR watch view %s failed", k)
            out[k] = None
    return out


NAMES = {"hedge": "避險基金槓桿", "house": "家庭貸款逾期", "bank": "銀行證券帳面損失", "rent": "房價租金比"}


def alerts(v: Dict) -> List[tuple]:
    """(key, severity, title, detail) — once per section per data date while it is yellow."""
    out = []
    for k, zh in NAMES.items():
        x = v.get(k) or {}
        if x.get("emoji") != "🟡":
            continue
        out.append((f"fsr:{k}:{x['date']}", "ℹ️ INFO", f"金融穩定：{zh}亮黃燈（{x['state']}）",
                    "聯準會《金融穩定報告》點名的壓力點，用自己的歷史百分位判讀。看網站「金融穩定監測」頁的「官方點名的四個壓力點」卡。"))
    return out
