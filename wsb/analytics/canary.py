"""金絲雀 — early-warning lights for the places past crises started: funding markets, credit quality, bank deposits,
leverage, hedges failing, a dash for cash, a split market, and analysts cutting estimates.

Two kinds:
  * score lights — the SSI components added for this (same transform as the SSI: own 3-year z-score → 0–100).
    Watch ≥ 90, alert ≥ 97.5.  Their history on past crisis dates is computed live from the data.
  * rule lights — conditions that are not a smooth series (RRP exhausted, margin-debt growth, simultaneous
    stock/bond/gold selling, new highs and new lows together, estimate-revision breadth).  Each rule is stated
    on the page; history (how often it fired, what followed) is computed live too.
Everything is model data; no headline enters any light."""
from __future__ import annotations

from ..data import fred as FR  # noqa: E402

import json
import logging
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS
from .stress import StressEngine, norm_cdf, rolling_z

log = logging.getLogger(__name__)
REV_FILE = DATA_DIR / "earn_revisions.json"           # earn_* is kept by the site workflow's cache
WATCH, ALERT = 90.0, 97.5
EVENTS = [("2007-08-09", "次貸危機開始（BNP 凍結基金）"), ("2008-09-15", "雷曼倒閉"), ("2019-09-17", "回購市場失靈"),
          ("2020-02-19", "疫情崩盤前高點"), ("2022-01-03", "2022 熊市起點"), ("2023-03-10", "矽谷銀行倒閉")]

SCORE_LIGHTS = [
    ("sofr_iorb", "資金市場", ("隔夜融資利率 SOFR − 準備金利率 IORB", "SOFR − IORB"),
     "銀行間缺現金時 SOFR 會高過 IORB。2019 年 9 月回購市場失靈就是這個利差暴衝。", "bp", 100),
    ("sofr99_iorb", "資金市場", ("最貴 1% 隔夜融資 SOFR99 − IORB", "SOFR 99th pct − IORB"),
     "SOFR 是平均，SOFR99 是當天最貴那 1% 的交易：少數機構借不到便宜的錢時，尾端會先跳，平均還沒動。", "bp", 100),
    ("discount_window", "資金市場", ("聯準會貼現窗口借款", "Discount-window borrowing"),
     "銀行在別處借不到錢才會來借。2008 年、2020 年 3 月、2023 年 3 月都暴增。", "$B", None),
    ("cp_tbill", "資金市場", ("商業本票 − 國庫券利差（3 個月）", "CP − T-bill (3m)"),
     "企業短期融資的壓力。2008 年和 2020 年 3 月都比股市更早拉開。", "bp", 100),
    ("ccc_bb", "信用品質", ("CCC − BB 利差（最弱 vs 次弱）", "CCC − BB spread"),
     "只有最弱的公司利差擴大＝信用循環早期；BB 也跟上＝開始擴散。", "pp", 1),
    ("bank_deposits", "信用品質", ("商業銀行存款 4 週變化", "Bank deposits, 4-week change"),
     "存款快速流出是 2023 年銀行危機的起點。", "%", 100),
    ("stock_bond_corr", "避險失效", ("股債 60 日相關性（SPY vs TLT）", "Stock–bond correlation (60d)"),
     "相關性轉正＝股債一起跌，公債不再保護股票（2022 年）。", "", 1),
    ("transports", "景氣類股", ("運輸股 vs 大盤（60 日）", "Transports vs S&P (60d)"),
     "道氏理論：運輸股走弱常先反映貨運與景氣降溫。", "%", 100),
    ("discretionary_staples", "景氣類股", ("非必需 vs 必需消費（60 日）", "Discretionary vs staples (60d)"),
     "消費者開始縮衣節食時，非必需消費相對必需消費走弱。", "%", 100),
    ("vxn_vix", "避險失效", ("科技股恐慌溢價 VXN ÷ VIX", "Tech fear premium: VXN ÷ VIX"),
     "那指的隱含波動相對標普拉高＝恐慌集中在科技股（2000、2022 年科技股領跌前都偏高）。", "", 1),
    ("ovx", "外部衝擊", ("原油波動率 OVX", "Oil volatility (OVX)"),
     "油價隱含波動暴衝通常來自地緣或供給衝擊（2020 年 4 月、2022 年 3 月），會經由通膨與利率傳到股市。", "", 1),
    ("eu_hy_oas", "信用品質", ("歐洲高收益債利差", "Euro high-yield spread"),
     "看信用壓力有沒有擴散到海外。歐美利差同時擴大＝全球性的信用收緊，不只是美國問題。", "%", 1),
    ("infl_5y5y", "外部衝擊", ("5 年後 5 年通膨預期（5y5y）", "5y5y inflation expectation"),
     "市場對「長期通膨」的看法。持續升高＝聯準會的通膨可信度下降，長債與高估值股票最受傷。", "%", 1),
    ("homebuilders", "景氣類股", ("房屋建商 vs 大盤（60 日）", "Homebuilders vs S&P (60d)"),
     "房市對利率最敏感，常是景氣循環最早轉向的產業。", "%", 100),
]


def _comp(cid: str) -> Optional[dict]:
    return next((c for c in SETTINGS.get("stress_components", []) + SETTINGS.get("canary_components", []) if c["id"] == cid), None)


def _in_ssi(cid: str) -> bool:
    return any(c["id"] == cid for c in SETTINGS.get("stress_components", []))


def _auc63(sc: pd.Series, close: pd.Series) -> Optional[float]:
    """Predictive power of the light's score for a ≥10% S&P fall within 63 sessions (AUC, 0.5 = random)."""
    try:
        from .lab import _labels
        from .shock import auc
        hit, valid = _labels(close, 63, 0.10)
        j = pd.concat([sc.rename("x"), hit.rename("y"), valid.rename("v")], axis=1).dropna()
        j = j[j["v"].astype(bool)]
        if len(j) < 500 or j["y"].sum() < 15:
            return None
        return round(float(auc(j["x"], j["y"])), 2)
    except Exception:  # noqa: BLE001
        return None


class _Own:
    """Current reading of a canary-only component (not part of the SSI), with the SSI's own staleness rule."""
    def __init__(self, se, c, raw, sc):
        from .stress import STALE_DAYS, _today
        lv = raw.last_valid_index()
        src_last = se.source_last_date(c)
        max_age = STALE_DAYS.get(c["series"], 7) if c["src"] == "fred" else 7
        stale = lv is None or src_last is None or (_today() - pd.Timestamp(src_last).normalize()).days > max_age
        self.raw = None if lv is None else float(raw.loc[lv])
        self.asof = None if lv is None else lv.strftime("%Y-%m-%d")
        self.score = None if stale or pd.isna(sc.iloc[-1]) else float(sc.iloc[-1])
        self.status = "no_data" if lv is None else (f"stale(最新資料 {pd.Timestamp(src_last).strftime('%Y-%m-%d') if src_last is not None else '—'})"
                                                    if stale else "ok")


def _event_history(sc: pd.Series) -> List[str]:
    """For each past crisis date: the highest score in the 4 months before → 1 month after, and the lead time."""
    out = []
    s = sc.dropna()
    if not len(s):
        return out
    for d, lab in EVENTS:
        t = pd.Timestamp(d)
        if t < s.index[0]:
            continue
        w = s[(s.index >= t - pd.Timedelta(days=120)) & (s.index <= t + pd.Timedelta(days=30))]
        if not len(w):
            continue
        hit = w[w >= WATCH]
        if len(hit):
            lead = (t - hit.index[0]).days
            out.append(f"{d[:7]} {lab}：" + (f"提前 {lead} 天亮燈" if lead > 0 else f"事件後 {-lead} 天才亮燈") + f"（最高 {w.max():.0f} 分）")
        else:
            out.append(f"{d[:7]} {lab}：沒有亮燈（最高 {w.max():.0f} 分）")
    return out


def score_lights(eng) -> List[Dict]:
    se = getattr(eng, "stress_engine", None) or StressEngine(eng.market, eng.fred)
    if se.market.history.empty:
        return []
    idx = se._base_index()
    win, minp = int(SETTINGS.get("stress_zscore_window", 756)), int(SETTINGS.get("stress_zscore_min", 252))
    live = {c.id: c for c in (getattr(getattr(eng, "stress", None), "components", None) or [])}
    rows = []
    for cid, grp, (zh, en), why, unit, mult in SCORE_LIGHTS:
        c = _comp(cid)
        if not c:
            continue
        try:
            raw = se.raw_series(c, idx)
        except Exception as e:  # noqa: BLE001
            rows.append({"id": cid, "group": grp, "zh": zh, "en": en, "why": why, "state": "na", "note": f"資料錯誤：{e}"[:80]})
            continue
        z = rolling_z(raw, win, minp) * float(c.get("direction", 1))
        sc = pd.Series(norm_cdf(z.clip(-6, 6)) * 100, index=idx).where(z.notna())
        comp = live.get(cid) if _in_ssi(cid) else _Own(se, c, raw, sc)
        cur = comp.score if comp else None
        v = comp.raw if comp else None
        if cid == "discount_window" and v is not None:
            v = float(np.expm1(v)) / 1000                         # log of $ millions → $ billions
        elif v is not None and mult:
            v = v * mult
        state = ("na" if comp is None or comp.status.startswith(("error", "no_data")) else
                 "stale" if comp.status.startswith("stale") else "warmup" if cur is None else
                 "alert" if cur >= ALERT else "watch" if cur >= WATCH else "ok")
        s_ok = sc.dropna()
        rows.append({"id": cid, "group": grp, "zh": zh, "en": en, "why": why, "kind": "score", "state": state,
                     "score": None if cur is None else round(cur, 1), "value": None if v is None else round(v, 2), "unit": unit,
                     "licensed": FR.restricted_component(c),          # public page: score only, no raw ICE / Moody's value
                     "asof": comp.asof if comp else None, "status": comp.status if comp else "na",
                     "rate": round(float((s_ok >= WATCH).mean() * 100), 1) if len(s_ok) else None,
                     "since": s_ok.index[0].strftime("%Y-%m") if len(s_ok) else None,
                     "chg_3m": round(float(s_ok.iloc[-1] - s_ok.iloc[-64]), 1) if len(s_ok) > 64 else None,
                     "in_ssi": _in_ssi(cid), "auc63": _auc63(sc, eng.market.series("^GSPC").dropna()),
                     "history": _event_history(sc)})
    return rows


# ------------------------------------------------------------------------------------------------ rule lights
def _fred(eng, sid: str) -> pd.Series:
    s = getattr(eng, "fred", None).get(sid) if getattr(eng, "fred", None) is not None else pd.Series(dtype=float)
    return s.dropna() if s is not None else pd.Series(dtype=float)


def rrp_light(eng) -> Dict:
    rrp, res = _fred(eng, "RRPONTSYD"), _fred(eng, "WRESBAL")
    row = {"id": "rrp_buffer", "group": "資金市場", "zh": "逆回購緩衝與準備金", "en": "RRP buffer & reserves", "kind": "rule",
           "why": "逆回購餘額是市場多餘現金的緩衝。用完之後，縮表與國庫券發行會直接抽走銀行準備金。",
           "rule": "黃燈：逆回購低於近 3 年高點的 5%（緩衝用完）。紅燈：同時銀行準備金 4 週減幅落在近 3 年最差的 2.5%。"}
    if len(rrp) < 300 or len(res) < 60:
        return {**row, "state": "na", "note": "資料不足"}
    hi = rrp[rrp.index >= rrp.index[-1] - pd.Timedelta(days=1095)].max()
    depleted = rrp.iloc[-1] < 0.05 * hi
    ch = res.pct_change(4) * 100                                    # weekly series → 4 weeks
    w = ch[ch.index >= ch.index[-1] - pd.Timedelta(days=1095)].dropna()
    pct = float((w < w.iloc[-1]).mean() * 100) if len(w) else None
    state = "alert" if depleted and pct is not None and pct <= 2.5 else "watch" if depleted else "ok"
    return {**row, "state": state, "asof": min(rrp.index[-1], res.index[-1]).strftime("%Y-%m-%d"),
            "value_txt": f"逆回購 US${rrp.iloc[-1]:,.0f}B（近 3 年高點 US${hi:,.0f}B）；銀行準備金 4 週 {ch.iloc[-1]:+.1f}%（近 3 年百分位 {pct:.0f}%）"}


def margin_light(eng) -> Dict:
    md = getattr(eng, "margin_debt", None)
    row = {"id": "margin_debt", "group": "槓桿", "zh": "融資餘額年增率（FINRA）", "en": "Margin debt, YoY (FINRA)", "kind": "rule",
           "why": "槓桿過熱的經典訊號。2000、2007、2021 年高點前年增率都很高；之後由正轉負＝去槓桿。",
           "rule": "黃燈：年增率 ≥ 25%。紅燈：≥ 40%，或從 ≥ 25% 在 6 個月內轉為負成長（去槓桿）。月資料，約晚 3–4 週公布。"}
    yoy = md.yoy() if md is not None else None
    if yoy is None or yoy.dropna().empty:
        return {**row, "state": "na", "note": "資料尚未下載"}
    y = yoy.dropna()
    cur = float(y.iloc[-1])
    recent_hot = bool((y.iloc[-7:-1] >= 25).any()) if len(y) > 7 else False
    state = "alert" if cur >= 40 or (cur < 0 and recent_hot) else "watch" if cur >= 25 else "ok"
    # history: what the S&P did in the 12 months after months with YoY ≥ 40 %
    g = eng.market.series("^GSPC").dropna()
    fw = []
    for d in y[y >= 40].index:
        a, b = g[g.index >= d], g[g.index >= d + pd.DateOffset(months=12)]
        if len(a) and len(b):
            fw.append(float(b.iloc[0] / a.iloc[0] - 1) * 100)
    hist = []
    if fw:
        hist.append(f"年增率 ≥ 40% 的 {len(fw)} 個月份之後 12 個月，標普中位數 {np.median(fw):+.1f}%、上漲比例 {np.mean([x > 0 for x in fw]) * 100:.0f}%")
    peaks = y[(y >= 40) & (y == y.rolling(25, center=True, min_periods=1).max())]
    if len(peaks):
        hist.append("歷次高峰：" + "、".join(f"{d:%Y-%m} {v:+.0f}%" for d, v in peaks.items()))
    return {**row, "state": state, "asof": y.index[-1].strftime("%Y-%m"), "history": hist,
            "value_txt": f"年增率 {cur:+.1f}%（融資餘額 {md.series.iloc[-1] / 1e6:,.2f} 兆美元）"}


def cash_dash_light(eng) -> Dict:
    row = {"id": "dash_for_cash", "group": "避險失效", "zh": "現金潮（股、長債、黃金同週大跌）", "en": "Dash for cash", "kind": "rule",
           "why": "連避險資產都被賣，代表有人被迫變現（2008 年 10 月、2020 年 3 月）。",
           "rule": "紅燈：5 個交易日內標普 ≤ −3%、長債 TLT ≤ −2%、黃金 ≤ −2% 同時成立。黃燈：三項中兩項成立。"}
    s = {k: eng.market.series(t).dropna() for k, t in (("spx", "^GSPC"), ("tlt", "TLT"), ("gold", "GC=F"))}
    if any(len(v) < 300 for v in s.values()):
        return {**row, "state": "na", "note": "資料不足"}
    df = pd.DataFrame(s).dropna()
    r5 = df.pct_change(5) * 100
    hits = (r5["spx"] <= -3).astype(int) + (r5["tlt"] <= -2).astype(int) + (r5["gold"] <= -2).astype(int)
    cur = int(hits.iloc[-1])
    full = hits[hits == 3]
    grp = (full.index.to_series().diff().dt.days > 20).cumsum() if len(full) else pd.Series(dtype=int)
    eps = [x.index[0] for _, x in full.groupby(grp)] if len(full) else []
    hist = [f"{len(eps)} 次（{df.index[0].year} 年起）：" + "、".join(d.strftime("%Y-%m") for d in eps[-8:])] if eps else ["資料期間內沒有出現過"]
    return {**row, "state": "alert" if cur == 3 else "watch" if cur == 2 else "ok", "asof": df.index[-1].strftime("%Y-%m-%d"),
            "history": hist, "value_txt": f"近 5 日：標普 {r5['spx'].iloc[-1]:+.1f}%、長債 {r5['tlt'].iloc[-1]:+.1f}%、黃金 {r5['gold'].iloc[-1]:+.1f}%"}


def split_light(eng, close: Optional[pd.DataFrame] = None) -> Dict:
    row = {"id": "market_split", "group": "市場結構", "zh": "市場分裂（新高新低同時增加）", "en": "Split market (highs & lows)", "kind": "rule",
           "why": "興登堡凶兆的概念：指數還在漲，但同時有一群股票創新高、一群創新低，代表內部撕裂。",
           "rule": "用美股全市場：創 52 週新高與新低的比例都 ≥ 2.2%、且標普在 50 日均線之上 → 紅燈；都 ≥ 1.5% → 黃燈。"}
    if close is None or close.empty:
        return {**row, "state": "na", "note": "需要全市場股價，只在網站建置時計算"}
    c = close.dropna(axis=1, thresh=200).iloc[-260:]
    if c.shape[1] < 300 or len(c) < 253:
        return {**row, "state": "na", "note": "全市場股價不足"}
    last, hi, lo = c.iloc[-1], c.iloc[-253:-1].max(), c.iloc[-253:-1].min()
    ok = last.notna() & hi.notna()
    nh = float((last[ok] >= hi[ok]).mean() * 100)
    nl = float((last[ok] <= lo[ok]).mean() * 100)
    g = eng.market.series("^GSPC").dropna()
    above = bool(len(g) > 50 and g.iloc[-1] > g.iloc[-50:].mean())
    state = "alert" if nh >= 2.2 and nl >= 2.2 and above else "watch" if nh >= 1.5 and nl >= 1.5 else "ok"
    return {**row, "state": state, "asof": c.index[-1].strftime("%Y-%m-%d"),
            "value_txt": f"{int(ok.sum())} 檔中：52 週新高 {nh:.1f}%、新低 {nl:.1f}%；標普{'在' if above else '不在'} 50 日均線之上"}


def record_revisions(eng, today: Optional[date] = None) -> Dict:
    """Daily snapshot of the consensus EPS for every upcoming report (so revisions can be measured later)."""
    ed = getattr(eng, "earnings", None)
    days = (getattr(ed, "days", None) or {}) if ed is not None else {}
    today = today or date.today()
    try:
        snap = json.loads(REV_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        snap = {}
    td = today.isoformat()
    for d, rec in days.items():
        if d <= td:
            continue
        for r in rec.get("rows", []):
            if r.get("eps_f") is None or (r.get("mcap") or 0) < 1e10:
                continue
            k = f"{r['sym']}|{d}"
            lst = snap.setdefault(k, [])
            if not lst or lst[-1][0] != td:
                lst.append([td, r["eps_f"]])
                del lst[:-60]
    cut = (today - timedelta(days=10)).isoformat()
    snap = {k: v for k, v in snap.items() if k.split("|")[1] >= cut}
    try:
        tmp = REV_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap), encoding="utf-8")
        tmp.replace(REV_FILE)
    except OSError as e:
        log.warning("revision snapshots not saved: %s", e)
    return snap


def revision_light(eng, snap: Optional[Dict] = None, today: Optional[date] = None) -> Dict:
    row = {"id": "eps_revisions", "group": "景氣類股", "zh": "獲利預估修正方向（市值 100 億美元以上）", "en": "EPS revision breadth", "kind": "rule",
           "why": "分析師開始普遍下修即將公布的獲利預估，常比股價先反映景氣轉弱。",
           "rule": "淨上修比例＝（4 週內預估上修 >1% 的家數 − 下修 >1% 的家數）÷ 總數。黃燈 ≤ −20%，紅燈 ≤ −40%。需要累積 4 週快照。"}
    today = today or date.today()
    snap = snap if snap is not None else record_revisions(eng, today)
    ref = (today - timedelta(days=28)).isoformat()
    up = dn = n = 0
    for k, lst in snap.items():
        old = [v for d, v in lst if d <= ref]
        if not old or k.split("|")[1] <= today.isoformat():
            continue
        a, b = old[-1], lst[-1][1]
        if not a:
            continue
        n += 1
        ch = (b - a) / abs(a)
        up += ch > 0.01
        dn += ch < -0.01
    first = min((lst[0][0] for lst in snap.values() if lst), default=None)
    if n < 20:
        return {**row, "state": "warmup", "note": f"快照從 {first or '今天'} 開始累積，滿 4 週後啟用（目前可比較 {n} 家）"}
    net = (up - dn) / n * 100
    return {**row, "state": "alert" if net <= -40 else "watch" if net <= -20 else "ok", "asof": today.isoformat(),
            "value_txt": f"{n} 家中上修 {up}、下修 {dn}，淨上修比例 {net:+.0f}%"}


def hike_light(eng) -> Dict:
    row = {"id": "hike_pricing", "group": "資金市場", "zh": "升息定價（聯邦基金期貨）", "en": "Rate-hike pricing (fed funds futures)", "kind": "rule",
           "why": "期貨押注聯準會在高利率下繼續升息時，最弱的借款人與高估值資產壓力最大。",
           "rule": "看第三次會議後的隱含利率比目前高多少：≥ +25bp（至少一碼）黃燈；≥ +50bp，或一週內再增加 ≥ 15bp 紅燈。期貨歷史仍在累積，資料滿兩年前不回測。"}
    fv = getattr(eng, "fedwatch_view", None) or {}
    ms = fv.get("meetings") or []
    if not fv.get("available") or len(ms) < 1:
        return {**row, "state": "na", "note": "期貨資料不足"}
    m3 = ms[min(2, len(ms) - 1)]
    cum = m3["cum_bp"]
    wk = (m3.get("week_ago") or {})
    d1w = (m3["rate_after"] - wk["rate_after"]) * 100 if wk.get("rate_after") is not None else None
    state = "alert" if cum >= 50 or (d1w is not None and d1w >= 15) else "watch" if cum >= 25 else "ok"
    return {**row, "state": state, "asof": fv.get("asof"),
            "value_txt": f"{m3['date']} 會後隱含利率 {m3['rate_after']:.2f}%，比目前 {cum:+.0f}bp"
                         + (f"；一週變化 {d1w:+.0f}bp" if d1w is not None else "；一週變化：快照累積中")}


def _pc_lights(eng) -> List[Dict]:
    from . import private_credit as pcl
    return pcl.lights(eng)


def vix1d_light(eng) -> Dict:
    row = {"id": "vix1d", "group": "避險失效", "zh": "當日恐慌 VIX1D ÷ VIX", "en": "Same-day fear: VIX1D ÷ VIX", "kind": "rule",
           "why": "VIX1D 是「今天收盤前」的隱含波動。它遠高於 VIX＝市場在為一兩天內的衝擊付費；FOMC、CPI 前偏高是正常的。",
           "rule": "比值落在自己歷史最高的 10% 且 VIX1D ≥ 20 → 黃燈；最高的 2.5% 且 VIX1D ≥ 25 → 紅燈。資料從 2023 年 4 月起。"}
    v1, v = eng.market.series("^VIX1D").dropna(), eng.market.series("^VIX").dropna()
    df = pd.concat([v1.rename("v1"), v.rename("v")], axis=1).dropna()
    df = df[(df["v1"] > 0) & (df["v"] > 0)]
    if len(df) < 250:
        return {**row, "state": "na", "note": "資料不足（VIX1D 歷史累積中）"}
    r = df["v1"] / df["v"]
    a1, a = eng.market.q("^VIX1D"), eng.market.q("^VIX")
    if a1 and a and a1.get("price") and a.get("price") and a1.get("asof") == a.get("asof") and str(a1["asof"])[:10] > df.index[-1].strftime("%Y-%m-%d"):
        cur_v1, cur_r, asof = float(a1["price"]), float(a1["price"]) / float(a["price"]), str(a1["asof"])[:10]
    else:
        cur_v1, cur_r, asof = float(df["v1"].iloc[-1]), float(r.iloc[-1]), df.index[-1].strftime("%Y-%m-%d")
    hist_r = r.iloc[:-1] if asof == df.index[-1].strftime("%Y-%m-%d") else r
    pct = float((hist_r < cur_r).mean() * 100)
    state = "alert" if pct >= 97.5 and cur_v1 >= 25 else "watch" if pct >= 90 and cur_v1 >= 20 else "ok"
    # what followed past top-10% days (S&P 5 sessions later)
    g = eng.market.series("^GSPC").dropna()
    hot = r[(r >= r.quantile(0.9)) & (df["v1"] >= 20)].index
    f5 = [(g[g.index > d].iloc[4] / g[g.index <= d].iloc[-1] - 1) * 100 for d in hot if len(g[g.index > d]) >= 5 and len(g[g.index <= d])]
    hist = [f"{df.index[0]:%Y-%m} 起 {len(f5)} 天亮過黃燈以上；之後 5 日標普中位數 {np.median(f5):+.1f}%、上漲 {np.mean([x > 0 for x in f5]) * 100:.0f}%"] if len(f5) >= 5 else []
    ev = ""
    try:
        from ..data.econcal import us_today
        nx = ((getattr(eng, "econ_view", None) or {}).get("next_fomc") or {}).get("date")
        if nx and 0 <= (date.fromisoformat(nx) - us_today()).days <= 1:
            ev = "（FOMC 在即，偏高屬正常）"
    except Exception:  # noqa: BLE001
        pass
    return {**row, "state": state, "asof": asof, "history": hist,
            "value_txt": f"VIX1D {cur_v1:.1f}、比值 {cur_r:.2f}（自身歷史百分位 {pct:.0f}%）{ev}"}


def build(eng, close: Optional[pd.DataFrame] = None) -> Dict:
    rows = []
    for fn in (lambda: score_lights(eng), lambda: [rrp_light(eng)], lambda: [margin_light(eng)], lambda: [cash_dash_light(eng)],
               lambda: [split_light(eng, close)], lambda: [revision_light(eng)], lambda: [hike_light(eng)],
               lambda: [vix1d_light(eng)], lambda: _pc_lights(eng)):
        try:
            rows += fn()
        except Exception:  # noqa: BLE001
            log.exception("canary light failed")
    order = {"alert": 0, "watch": 1, "ok": 2, "warmup": 3, "stale": 4, "na": 5}
    rows.sort(key=lambda r: (order.get(r["state"], 9), r["group"]))
    return {"available": bool(rows), "rows": rows, "ts": time.time(),
            "n_alert": sum(r["state"] == "alert" for r in rows), "n_watch": sum(r["state"] == "watch" for r in rows)}
