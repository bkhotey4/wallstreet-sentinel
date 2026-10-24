"""AI 泡沫計時器：不猜日期，只給「時間分布」。

1. 歷史泡沫統計（Greenwood, Shleifer & You 2019, "Bubbles for Fama"）：Ken French 49 產業月報酬（1926 起，免費）。
   產業 2 年漲幅 ≥ 100% 即為「泡沫候選」（同一產業 24 個月內只算一次）；之後 24 個月內，從「訊號前 12 個月高點或之後的
   最高點」回落 ≥ 40% 算破裂。依條件分組（漲幅、是否已從高點跌 20%、波動率是否放大），列出 6／12／24 個月內破裂的
   比例、破裂的月數中位數，以及沒破的那些之後表現——分 1926、1946、1970 年起三段，樣本少就照實寫。
2. 現在的 AI 族群（半導體 SMH、費城半導體、那斯達克 100）用同一套條件判斷落在哪一組。
3. 大象撤退：CFTC 交易者持倉報告，資產管理機構在 S&P 500／那斯達克 100 期貨的淨多單（占未平倉 %），13 週變化落在
   自身歷史最低 10% 算「大錢在撤」；回測 2010 年起，之後 3 個月內跌 ≥10% 的頻率。避險基金部位回測沒有預測力，照列。
4. 加速度模型（LPPLS，Sornette）試算過：在這組數據上每個視窗都「合格」，代表篩選條件分不出泡沫與否，所以沒有採用。

快取 data_cache/econ_bubble.json（網站 CI 已保留 econ_*）。描述歷史頻率，不是預測，也不是投資建議。"""
from __future__ import annotations

import io
import json
import logging
import os
import time
import zipfile
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_bubble.json"
FF_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_CSV.zip"
CFTC_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
EQ_FUT = {"209742": "那斯達克 100", "13874A": "S&P 500"}
TTL_FF = 15 * 86400
TTL_CFTC = 12 * 3600
H, DD, RUN = 24, 0.40, 1.0
PERIODS = ("1926", "1946", "1970")
BASKETS = (("SMH", "半導體（SMH）"), ("^SOX", "費城半導體"), ("^NDX", "那斯達克 100"))
# condition groups, most specific first: (key, 中文, test(run2y, off_high, vol_up))
GROUPS = (("hot_fall_vol", "2 年漲 ≥100%、已從高點跌 ≥20%、波動放大 ≥1.3 倍", lambda r, o, v: r >= 1.0 and o <= -0.20 and v >= 1.3),
          ("hot_fall", "2 年漲 ≥100%、已從高點跌 ≥20%", lambda r, o, v: r >= 1.0 and o <= -0.20),
          ("very_hot", "2 年漲 ≥150%", lambda r, o, v: r >= 1.5),
          ("hot_vol", "2 年漲 ≥100%、波動放大 ≥1.3 倍", lambda r, o, v: r >= 1.0 and v >= 1.3),
          ("hot", "2 年漲 ≥100%", lambda r, o, v: r >= 1.0))
_CACHE: Dict = {}


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception as e:  # noqa: BLE001
        log.warning("%s unreadable: %s", FILE.name, e)
        return {}


def _save(d: Dict) -> None:
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)


def parse_ff(raw: bytes) -> Dict[str, Dict[str, float]]:
    """{industry: {YYYY-MM: monthly value-weighted return}} from the Ken French 49-industry zip."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    lines = z.read(z.namelist()[0]).decode("latin1").splitlines()
    i0 = next(i for i, ln in enumerate(lines) if "Average Value Weighted Returns -- Monthly" in ln)
    body = []
    for ln in lines[i0 + 1:]:
        if not ln.strip():
            break
        body.append(ln)
    df = pd.read_csv(io.StringIO("\n".join(body)), index_col=0)
    df.columns = [c.strip() for c in df.columns]
    out: Dict[str, Dict[str, float]] = {}
    for c in df.columns:
        s = df[c].replace([-99.99, -999], np.nan).dropna() / 100
        out[c] = {f"{str(k)[:4]}-{str(k)[4:6]}": round(float(v), 6) for k, v in s.items()}
    return out


def parse_cftc(rows: List[Dict]) -> Dict[str, List[List]]:
    """{contract: [[date, asset-manager net % of OI, leveraged-fund net % of OI]]} oldest first."""
    out: Dict[str, List[List]] = {}
    for r in rows:
        code = r.get("cftc_contract_market_code")
        if code not in EQ_FUT:
            continue
        try:
            oi = float(r["open_interest_all"])
            am = (float(r["asset_mgr_positions_long"]) - float(r["asset_mgr_positions_short"])) / oi * 100
            lev = (float(r["lev_money_positions_long"]) - float(r["lev_money_positions_short"])) / oi * 100
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
        out.setdefault(code, []).append([r["report_date_as_yyyy_mm_dd"][:10], round(am, 3), round(lev, 3)])
    return {k: sorted(v) for k, v in out.items()}


async def refresh(force: bool = False) -> Dict:
    from ..data import http
    d = load()
    now = time.time()
    bad = []
    if force or now - float(d.get("ts_ff", 0)) > TTL_FF or not d.get("ff"):
        try:
            ff = parse_ff(await http.get(FF_URL, kind="bytes", timeout=90, retries=1))
            if len(ff) < 40:
                raise ValueError(f"only {len(ff)} industries")
            d["ff"], d["ts_ff"] = ff, now
        except Exception as e:  # noqa: BLE001
            bad.append(f"ff: {e if str(e) else type(e).__name__}")
    if force or now - float(d.get("ts_cftc", 0)) > TTL_CFTC or not d.get("cftc"):
        try:
            codes = ",".join(f"'{c}'" for c in EQ_FUT)
            js = await http.get(CFTC_URL, params={
                "$select": "report_date_as_yyyy_mm_dd,cftc_contract_market_code,open_interest_all,asset_mgr_positions_long,"
                           "asset_mgr_positions_short,lev_money_positions_long,lev_money_positions_short",
                "$where": f"cftc_contract_market_code in({codes})", "$order": "report_date_as_yyyy_mm_dd", "$limit": "6000"},
                timeout=60, retries=1)
            c = parse_cftc(js if isinstance(js, list) else [])
            if not c:
                raise ValueError("no rows")
            d["cftc"], d["ts_cftc"] = c, now
        except Exception as e:  # noqa: BLE001
            bad.append(f"cftc: {e if str(e) else type(e).__name__}")
    d["ts_check"] = now
    if not bad or d.get("ff") or d.get("cftc"):
        _save(d)
    if bad:
        log.warning("bubble data: %s", "; ".join(bad))
        HEALTH.fail("bubble", "; ".join(bad), every=TTL_CFTC)
    else:
        HEALTH.ok("bubble", len(d.get("ff") or {}), every=TTL_CFTC)
    return d


# ───────────────────────── 1. 歷史泡沫統計 ─────────────────────────
def features(px: pd.Series) -> pd.DataFrame:
    """Monthly price index → 2y run-up, distance from the 12-month high, vol (12m) ÷ vol (the 24m before)."""
    r = px.pct_change()
    vol = r.rolling(12).std()
    volp = r.shift(12).rolling(24).std()
    return pd.DataFrame({"run": px / px.shift(24) - 1, "off": px / px.rolling(12).max() - 1,
                         "volup": vol / volp.replace(0, np.nan)})


def episodes(ff: Dict[str, Dict[str, float]], test, start: str = "1926") -> List[Dict]:
    out = []
    for ind, rets in ff.items():
        r = pd.Series(rets)
        r.index = pd.to_datetime(r.index + "-01")
        r = r.sort_index()
        if len(r) < 60:
            continue
        px = (1 + r).cumprod()
        f = features(px)
        hi12 = px.rolling(12).max()
        last = None
        for t in range(36, len(px)):
            x = f.iloc[t]
            if not test(x["run"], x["off"], x["volup"] if x["volup"] == x["volup"] else 0.0):
                continue
            if last is not None and t - last < 24:
                continue
            last = t
            fut = px.iloc[t:t + 1 + H]
            if len(fut) < H + 1 or px.index[t] < pd.Timestamp(f"{start}-01-01"):
                continue
            peak = np.maximum(fut.cummax().values, hi12.iloc[t])
            dd = fut.values / peak - 1
            hit = np.where(dd <= -DD)[0]
            out.append({"ind": ind, "date": px.index[t].strftime("%Y-%m"), "run": float(x["run"]), "off": float(x["off"]),
                        "crash": bool(len(hit)), "months": int(hit[0]) if len(hit) else None,
                        "ret1y": float(fut.iloc[12] / fut.iloc[0] - 1), "ret2y": float(fut.iloc[-1] / fut.iloc[0] - 1)})
    return out


def summarize(eps: List[Dict]) -> Optional[Dict]:
    if not eps:
        return None
    n = len(eps)
    cr = [e for e in eps if e["crash"]]
    ok = [e for e in eps if not e["crash"]]
    mo = sorted(e["months"] for e in cr)
    return {"n": n, "p6": sum(e["months"] <= 6 for e in cr) / n * 100, "p12": sum(e["months"] <= 12 for e in cr) / n * 100,
            "p24": len(cr) / n * 100, "med_months": float(np.median(mo)) if mo else None,
            "ok_ret1y": float(np.median([e["ret1y"] for e in ok]) * 100) if ok else None,
            "ret1y": float(np.median([e["ret1y"] for e in eps]) * 100)}


def history_table(ff: Dict) -> Dict:
    """Per group and period: the summary, plus the 1970+ cases.  Each group is scanned once (from 1926) and the periods are
    filtered by date; the result is cached in memory and in econ_bubble.json keyed by the data's last month."""
    end = max(max(v) for v in ff.values()) if ff else ""
    if _CACHE.get("hist_end") == end and (_CACHE.get("hist") or {}).get("_v") == HIST_V:
        return _CACHE["hist"]
    d = load()
    if (d.get("hist") or {}).get("_end") == end and (d.get("hist") or {}).get("_v") == HIST_V:
        _CACHE.update(hist_end=end, hist=d["hist"])
        return d["hist"]
    out: Dict = {"_end": end, "_v": HIST_V, "scen": scenarios(ff)}
    for gk, _zh, test in GROUPS + (("any", "所有產業、任何時候（基準）", lambda r, o, v: r == r),):
        eps = episodes(ff, test, "1926")
        out[gk] = {p: summarize([e for e in eps if e["date"] >= p]) for p in PERIODS}
        out[gk]["cases"] = sorted([e for e in eps if e["date"] >= "1970"], key=lambda e: e["date"], reverse=True)[:40] if gk != "any" else []
    _CACHE.update(hist_end=end, hist=out)
    try:
        d["hist"] = out
        _save(d)
    except Exception:  # noqa: BLE001
        log.warning("bubble history cache not saved")
    return out


SCEN_RUN, SCEN_OFF, SCEN_START, HIST_V = 1.0, -0.15, "1946", 3


def scenarios(ff: Dict[str, Dict[str, float]]) -> Optional[Dict]:
    """The decision-useful view.  Cases since 1946 (the Depression left out): a 2-year run-up ≥ 100 % that has already
    fallen ≥ 15 % from its 12-month high.  Outcome over the next 24 months: back to the old high within 12 months,
    a ≥ 40 % fall from the high, or neither; the deepest fall from the high; and how the next 3 months split the odds."""
    rows = []
    for ind, rets in ff.items():
        r = pd.Series(rets)
        r.index = pd.to_datetime(r.index + "-01")
        r = r.sort_index()
        if len(r) < 60:
            continue
        px = (1 + r).cumprod()
        f = features(px)
        hi12 = px.rolling(12).max()
        last = None
        for i in range(36, len(px) - H):
            x = f.iloc[i]
            if not (x["run"] >= SCEN_RUN and x["off"] <= SCEN_OFF) or (last is not None and i - last < 24):
                continue
            last = i
            if px.index[i] < pd.Timestamp(f"{SCEN_START}-01-01"):
                continue
            pk, fut = hi12.iloc[i], px.iloc[i:i + H + 1]
            dd = fut.values / np.maximum(fut.cummax().values, pk) - 1
            hit = np.where(dd <= -DD)[0]
            nh = np.where(fut.values >= pk)[0]
            m_c = int(hit[0]) if len(hit) else None
            m_h = int(nh[0]) if len(nh) else None
            first = ("crash" if m_c is not None and (m_h is None or m_c < m_h) else "high" if m_h is not None else "range")
            rows.append({"ind": ind, "date": px.index[i].strftime("%Y-%m"), "crash": m_c is not None, "m": m_c, "m_high": m_h, "first": first,
                         "newhi12": bool(m_h is not None and m_h <= 12), "r3": float(fut.iloc[3] / fut.iloc[0] - 1), "mdd": float(dd.min())})
    if len(rows) < 15:
        return None
    e = pd.DataFrame(rows)
    n = len(e)
    crash, newhi = float(e["crash"].mean() * 100), float(e["newhi12"].mean() * 100)
    both = float((e["crash"] & e["newhi12"]).mean() * 100)

    def split(mask):
        s = e[mask & ~(e["m"].notna() & (e["m"] <= 3))]           # still undecided at the 3-month checkpoint
        return {"n": int(len(s)), "newhi": float(s["newhi12"].mean() * 100) if len(s) else None,
                "crash": float(s["crash"].mean() * 100) if len(s) else None}
    fc = e["first"].value_counts(normalize=True) * 100
    return {"n": n, "since": SCEN_START, "crash": crash, "newhi": newhi, "both": both,
            "first_high": float(fc.get("high", 0)), "first_crash": float(fc.get("crash", 0)), "first_range": float(fc.get("range", 0)),
            "med_m": float(e.loc[e["crash"], "m"].median()) if e["crash"].any() else None,
            "med_m_high": float(e.loc[e["first"] == "high", "m_high"].median()) if (e["first"] == "high").any() else None,
            "mdd_q": [float(x) for x in e["mdd"].quantile([0.25, 0.5, 0.75])],
            "up3": split(e["r3"] > 0), "down3": split(e["r3"] <= 0), "down10": split(e["r3"] <= -0.10),
            "cases": e.sort_values("date", ascending=False).to_dict("records")}


def levels(eng, sym: str, sc: Dict) -> Optional[Dict]:
    """Translate the scenario numbers into index levels for one basket (daily closes)."""
    try:
        s = eng.market.series(sym).dropna()
    except Exception:  # noqa: BLE001
        return None
    if len(s) < 260:
        return None
    hi = float(s.tail(252).max())
    now = float(s.iloc[-1])
    q25, q50, q75 = sc["mdd_q"]
    return {"sym": sym, "now": now, "asof": s.index[-1].strftime("%Y-%m-%d"), "high": hi, "high_d": s.tail(252).idxmax().strftime("%Y-%m-%d"),
            "off": (now / hi - 1) * 100, "crash_line": hi * (1 - DD), "mild": hi * (1 + q75), "typical": hi * (1 + q50), "deep": hi * (1 + q25),
            "check_date": (s.index[-1] + pd.DateOffset(months=3)).strftime("%Y-%m-%d"), "check_down10": now * 0.9}


def current_state(eng) -> List[Dict]:
    out = []
    for sym, zh in BASKETS:
        try:
            s = eng.market.series(sym).dropna()
        except Exception:  # noqa: BLE001
            continue
        if len(s) < 600:
            continue
        m = s.resample("ME").last()
        f = features(m)
        x = f.iloc[-1]
        vu = float(x["volup"]) if x["volup"] == x["volup"] else 0.0
        grp = next((gk for gk, _z, test in GROUPS if test(x["run"], x["off"], vu)), None)
        out.append({"sym": sym, "name": zh, "run": float(x["run"]) * 100, "off": float(x["off"]) * 100, "volup": vu, "group": grp,
                    "asof": s.index[-1].strftime("%Y-%m-%d")})
    return out


# ───────────────────────── 3. 大象撤退（CFTC 資產管理機構） ─────────────────────────
def _auc(score: pd.Series, y: pd.Series) -> Optional[float]:
    s = pd.concat([score, y], axis=1).dropna()
    pos = s.iloc[:, 1] == 1
    npos, nneg = int(pos.sum()), int((~pos).sum())
    if not npos or not nneg:
        return None
    rk = s.iloc[:, 0].rank()
    return float((rk[pos].sum() - npos * (npos + 1) / 2) / (npos * nneg))


def elephants(eng, cftc: Dict[str, List[List]]) -> List[Dict]:
    out = []
    for code, (zh, idx) in (("209742", ("那斯達克 100", "^NDX")), ("13874A", ("S&P 500", "^GSPC"))):
        rows = cftc.get(code) or []
        if len(rows) < 150:
            continue
        d = pd.DataFrame(rows, columns=["d", "am", "lev"]).set_index("d")
        d.index = pd.to_datetime(d.index)
        try:
            px = eng.market.series(idx).dropna()
        except Exception:  # noqa: BLE001
            px = pd.Series(dtype=float)
        ch = d["am"].diff(13)
        pc = ch.expanding(52).apply(lambda x: (x[:-1] < x[-1]).mean() * 100, raw=True)
        rec = {"name": zh, "date": d.index[-1].strftime("%Y-%m-%d"), "am": float(d["am"].iloc[-1]), "chg13": float(ch.iloc[-1]),
               "pct": float(pc.iloc[-1]) if pc.notna().any() else None, "since": str(d.index[0].year),
               "hist": [[i.strftime("%Y-%m-%d"), float(v)] for i, v in d["am"].tail(156).items()]}
        if len(px) > 500:
            low = px[::-1].rolling(63, min_periods=1).min()[::-1].shift(-1)
            dd = (low / px - 1).reindex(d.index, method="ffill")
            y = (dd <= -0.10).astype(float).where(dd.notna())
            y[d.index > px.index[-1] - pd.Timedelta(days=95)] = np.nan
            ex = pc <= 10
            rec.update(base=float(y.mean() * 100), exit_rate=float(y[ex].mean() * 100) if y[ex].notna().any() else None,
                       exit_n=int(y[ex].notna().sum()), auc=_auc(-ch, y), auc_lev=_auc(-d["lev"].diff(13), y))
        rec["state"] = ("撤退" if rec["pct"] is not None and rec["pct"] <= 10 else "減碼" if rec["pct"] is not None and rec["pct"] <= 30
                        else "加碼" if rec["pct"] is not None and rec["pct"] >= 70 else "持平")
        out.append(rec)
    return out


def insider_ai(eng) -> Optional[Dict]:
    """AI-company insiders over the cached Form 4 window: discretionary (not pre-planned 10b5-1) sales vs buys.  Only a
    few months are kept, so this is context, not a back-tested signal."""
    try:
        from ..data.stability import AI_GROUP
        forms = (json.loads((DATA_DIR / "insiders.json").read_text(encoding="utf-8")).get("forms") or {})
    except Exception:  # noqa: BLE001
        return None
    syms = set(AI_GROUP) | {"NVDA", "AVGO", "AMD", "TSM", "MU", "SMCI", "PLTR"}
    sell = buy = sell_plan = 0.0
    names = {}
    dates = []
    for f in forms.values():
        if f.get("sym") not in syms:
            continue
        for tx in f.get("tx") or []:
            usd = float(tx.get("usd") or 0)
            dates.append(tx.get("date") or f.get("filed") or "")
            if tx.get("code") == "S":
                if f.get("plan"):
                    sell_plan += usd
                else:
                    sell += usd
                names[f["sym"]] = names.get(f["sym"], 0) + usd
            elif tx.get("code") == "P":
                buy += usd
    if not dates:
        return None
    return {"from": min(d for d in dates if d), "to": max(dates), "sell": sell, "sell_plan": sell_plan, "buy": buy,
            "top": sorted(names.items(), key=lambda x: -x[1])[:4]}


def build(eng) -> Dict:
    d = load()
    ff, cf = d.get("ff") or {}, d.get("cftc") or {}
    out: Dict = {"available": bool(ff), "ts_ff": d.get("ts_ff"), "ts_cftc": d.get("ts_cftc")}
    if ff:
        out["hist"] = history_table(ff)
        out["ff_end"] = max(max(v) for v in ff.values())
    out["now"] = current_state(eng)
    sc = (out.get("hist") or {}).get("scen")
    if sc:
        for sym in ("^SOX", "SMH"):
            lv = levels(eng, sym, sc)
            if lv:
                out["levels"] = lv
                break
    out["elephants"] = elephants(eng, cf) if cf else []
    out["insiders"] = insider_ai(eng)
    return out


GROUP_ZH = {k: z for k, z, _t in GROUPS}
