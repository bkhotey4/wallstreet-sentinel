"""每張卡片的「最後更新」標記：這張卡的數字是什麼時候抓到／算出來的，資料是哪一天的。

Each card is mapped to the data sources it is built from.  A source reports two things:
  * when it was last fetched or computed (epoch, from the provider's own ts), and
  * the date of the newest data point it holds (a market's last bar, a FRED observation…).
The card shows the OLDEST fetch time among its sources (the weakest link) and the newest data date, and turns orange
when the data is older than that source normally allows — so a stuck feed is visible on the card itself, not only in
the header.  The page's JS adds "N 分鐘前" from data-ts, so a page opened hours after the build still reads correctly."""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from tools.sitekit import T, esc

TPE = ZoneInfo("Asia/Taipei")
Src = Tuple[Optional[float], Optional[str]]          # (fetched epoch, newest data date YYYY-MM-DD)


def _ts(x) -> Optional[float]:
    try:
        v = float(x or 0)
        return v if v > 1e9 else None
    except (TypeError, ValueError):
        return None


def _d(x) -> Optional[str]:
    if x is None:
        return None
    if hasattr(x, "strftime"):
        return x.strftime("%Y-%m-%d")
    s = str(x)[:10]
    return s if len(s) == 10 and s[4] == "-" else None


def _q(eng, t: str) -> Optional[str]:
    try:
        return _d((eng.market.q(t) or {}).get("asof"))
    except Exception:  # noqa: BLE001
        return None


def _last(df) -> Optional[str]:
    try:
        return _d(df.dropna(how="all").index[-1]) if df is not None and len(df) else None
    except Exception:  # noqa: BLE001
        return None


def _fred_date(eng) -> Optional[str]:
    try:
        ds = [str((eng.fred.latest(sid) or {}).get("date") or "")[:10] for sid in ("DGS10", "DGS2", "T10Y3M", "SOFR", "NFCI")]
        ds = [d for d in ds if d]
        return max(ds) if ds else None
    except Exception:  # noqa: BLE001
        return None


def _fedres() -> Dict:
    try:
        from wsb.data import fed_research as FR
        return FR.load()
    except Exception:  # noqa: BLE001
        return {}


def _fedres_date() -> Optional[str]:
    d = _fedres()
    ds = [(d.get("mpd") or {}).get("sp6m", [[None]])[-1][0], ((d.get("ebp") or [[None]])[-1][0] or "") + "-01" if d.get("ebp") else None]
    ds = [x for x in ds if x]
    return max(ds) if ds else None


def _stab_ts(k: str):
    try:
        from wsb.data import stability as ST
        return (ST.load().get("ts_each") or {}).get(k)
    except Exception:  # noqa: BLE001
        return None


def _fm():
    """Full-market scan: when the newest market file was written, and the price date it holds."""
    try:
        import json as _j
        from wsb.config import DATA_DIR
        fs = [DATA_DIR / f"fullmarket_{m}.json" for m in ("us", "tw", "hk")]
        fs = [f for f in fs if f.exists()]
        if not fs:
            return None, None
        ts = max(f.stat().st_mtime for f in fs)
        asof = max((_j.loads(f.read_text(encoding="utf-8")).get("asof") or "") for f in fs) or None
        return ts, asof
    except Exception:  # noqa: BLE001
        return None, None


def _bondflows():
    """Japan MOF weekly + US TIC: when they were fetched and the newest week covered."""
    try:
        from wsb.data import bondflows as BF
        d = BF.load()
        rows = d.get("mof") or []
        return d.get("ts"), (rows[-1][1] if rows else None)
    except Exception:  # noqa: BLE001
        return None, None


def _twmacro():
    """Taiwan macro (central bank / NDC / TPEx): when fetched and the newest TPEx curve date."""
    try:
        from wsb.data import twmacro as TM
        d = TM.load()
        daily = sorted(d.get("daily") or {})
        return d.get("ts"), (daily[-1] if daily else None)
    except Exception:  # noqa: BLE001
        return None, None


def _fund_ts():
    try:
        from wsb.data import fundamentals as F
        from wsb.data.stability import AI_GROUP
        d = F.load()
        ts = [float((d.get(s) or {}).get("ts") or 0) for s in AI_GROUP]
        return max(ts) or None
    except Exception:  # noqa: BLE001
        return None


def _stab_date(k: str) -> Optional[str]:
    try:
        from wsb.data import stability as ST
        d = ST.load()
        if k == "refunding":
            p = (d.get("refunding") or {}).get("policy") or {}
            return _d(p.get("date"))
        if k == "ai":
            v = ST.ai_view()
            return _d(max(r["end"] for r in v["rows"])) if v else None
        rows = d.get(k) or []
        return _d(rows[-1][0]) if rows else None
    except Exception:  # noqa: BLE001
        return None


def _bub_ts(k: str):
    try:
        from wsb.analytics import bubble as BB
        return BB.load().get(k)
    except Exception:  # noqa: BLE001
        return None


def _bub_end() -> Optional[str]:
    try:
        from wsb.analytics import bubble as BB
        ff = BB.load().get("ff") or {}
        return (max(max(v) for v in ff.values()) + "-28") if ff else None
    except Exception:  # noqa: BLE001
        return None


def _bub_credit_month() -> Optional[str]:
    try:
        from wsb.analytics import bubble as BB
        c = BB.load().get("credit") or {}
        return (max(c) + "-01") if c else None
    except Exception:  # noqa: BLE001
        return None


def _bub_cftc_date() -> Optional[str]:
    try:
        from wsb.analytics import bubble as BB
        c = BB.load().get("cftc") or {}
        return max(v[-1][0] for v in c.values()) if c else None
    except Exception:  # noqa: BLE001
        return None


def _rel_ts():
    try:
        from wsb.analytics import event_clock as EC
        return EC.load().get("ts_check")
    except Exception:  # noqa: BLE001
        return None


def _trm(k: str):
    try:
        from wsb.data import transmission as TRM
        return TRM.load().get(k)
    except Exception:  # noqa: BLE001
        return None


def _trm_date(k: str) -> Optional[str]:
    v = _trm(k)
    if not v:
        return None
    if k == "fsi":
        return (v.get("dates") or [None])[-1]
    return max(v) if isinstance(v, dict) else None


def _ead(k: str):
    try:
        from wsb.data import euro_asia as EAD
        return EAD.load().get(k)
    except Exception:  # noqa: BLE001
        return None


def _ead_date() -> Optional[str]:
    c = _ead("ciss") or {}
    return max(c) if c else None


def _cxl(k: str):
    try:
        from wsb.analytics import capex_link as CXL
        return CXL.load().get(k)
    except Exception:  # noqa: BLE001
        return None


def _sck(k: str):
    try:
        from wsb.analytics import stock_check as SCK
        return SCK.load().get(k)
    except Exception:  # noqa: BLE001
        return None


def _twf(k: str):
    try:
        from wsb.data import tw_futures as TWF
        return TWF.load().get(k)
    except Exception:  # noqa: BLE001
        return None


def _twf_date() -> Optional[str]:
    n = _twf("net") or {}
    return max(n) if n else None


def _obs_date() -> Optional[str]:
    try:
        from tools.site_observer import load
        return _d(load().get("updated"))
    except Exception:  # noqa: BLE001
        return None


def _cover_date() -> Optional[str]:
    try:
        from tools.site_stability import coverage
        return _d(coverage().get("updated"))
    except Exception:  # noqa: BLE001
        return None


def _feed_date() -> Optional[str]:
    try:
        import json
        from tools.site_research import FEED
        return _d(json.loads(FEED.read_text(encoding="utf-8")).get("updated"))
    except Exception:  # noqa: BLE001
        return None


def _g(eng, *path):
    o = eng
    for p in path:
        o = o.get(p) if isinstance(o, dict) else getattr(o, p, None)
        if o is None:
            return None
    return o


# name → (label zh, label en, getter, days the data may lag before it counts as old)
SOURCES: Dict[str, Tuple[str, str, Callable[[object], Src], int]] = {
    "px": ("美股報價", "US quotes", lambda e: (_ts(_g(e, "market", "quotes_ts")), _q(e, "^GSPC")), 4),
    "tw": ("台股報價", "Taiwan quotes", lambda e: (_ts(_g(e, "market", "quotes_ts")), _q(e, "^TWII")), 4),
    "ssi": ("風險模型", "Risk model", lambda e: (_ts(_g(e, "recompute_ts")), _d(_g(e, "stress", "history").index[-1]) if _g(e, "stress", "history") is not None and len(_g(e, "stress", "history")) else None), 4),
    "fred": ("FRED 總經", "FRED", lambda e: (_ts(_g(e, "fred", "ts")), _fred_date(e)), 6),
    "econ": ("財經日曆", "Econ calendar", lambda e: (_ts(_g(e, "econ", "ts")), None), 0),
    "fedwatch": ("利率期貨", "Fed funds futures", lambda e: (_ts(_g(e, "fedwatch", "ts")), _d(_g(e, "fedwatch_view", "asof"))), 4),
    "options": ("CBOE 選擇權", "CBOE options", lambda e: (_ts(_g(e, "options", "ts")), _d(_g(e, "options", "spx", "asof"))), 4),
    "darkpool": ("FINRA 暗池", "FINRA dark pool", lambda e: (None, _d(_g(e, "darkpool", "result", "asof"))), 7),
    "jgb": ("日本財務省公債殖利率", "MOF JGB yields", lambda e: (_ts(_g(e, "global_yields", "ts")),
            _d(e.global_yields.jgb.index[-1]) if getattr(getattr(e, "global_yields", None), "jgb", None) is not None and len(e.global_yields.jgb) else None), 5),
    "bondflows": ("日本財務省週資料／美國 TIC", "MOF weekly / TIC", lambda e: (_ts(_bondflows()[0]), _bondflows()[1]), 14),
    "twmacro": ("台灣央行／國發會／櫃買中心", "Taiwan CBC / NDC / TPEx", lambda e: (_ts(_twmacro()[0]), _twmacro()[1]), 7),
    "fullmkt": ("全市場股價與估值", "Full-market scan", lambda e: (_ts(_fm()[0]), _fm()[1]), 4),
    "stocks": ("個股股價", "Stock prices", lambda e: (_ts(_g(e, "stockprices", "ts")), _last(_g(e, "stockprices", "close"))), 4),
    "earnings": ("財報資料", "Earnings data", lambda e: (_ts(_g(e, "earnings", "ts")), None), 0),
    "sec": ("SEC 申報", "SEC filings", lambda e: (_ts(_g(e, "sec", "ts")), None), 0),
    "news": ("新聞", "News", lambda e: (_ts(_g(e, "news", "ts")), None), 0),
    "calendar": ("事件日曆", "Event calendar", lambda e: (_ts(_g(e, "calendar", "ts")), None), 0),
    "crypto": ("加密情緒", "Crypto sentiment", lambda e: (_ts(_g(e, "crypto", "ts")), None), 0),
    "treasury": ("美債標售", "Treasury auctions", lambda e: (_ts(_g(e, "treasury", "ts")), None), 0),
    "canary": ("金絲雀", "Canary lights", lambda e: (_ts(_g(e, "canary", "ts")), max([str(r.get("asof"))[:10] for r in (_g(e, "canary", "rows") or []) if r.get("asof")] or [None])), 0),
    "gurus": ("13F 持倉", "13F filings", lambda e: (_ts(_g(e, "gurus", "data", "ts")), None), 0),
    "insiders": ("內部人申報", "Form 4", lambda e: (_ts(_g(e, "insiders", "data", "ts")), None), 0),
    "margin": ("FINRA 融資", "FINRA margin", lambda e: (_ts(_g(e, "margin_debt", "ts")), None), 0),
    "taiwan": ("台股籌碼", "Taiwan flows", lambda e: (_ts(_g(e, "taiwan", "ts")), _d(_g(e, "taiwan", "asof"))), 4),
    "street": ("華爾街觀點", "Street views", lambda e: (_ts(_g(e, "street", "ts")), _d(_g(e, "street", "pos", "asof") or _g(e, "street", "asof"))), 10),
    "fedres": ("聯準會研究資料", "Fed research data", lambda e: (_ts(_fedres().get("ts")), _fedres_date()), 40),
    "feed": ("學術動態", "Research feed", lambda e: (None, _feed_date()), 10),
    "refund": ("財政部再融資", "Treasury refunding", lambda e: (_ts(_stab_ts("refunding")), _stab_date("refunding")), 100),
    "funding": ("紐約聯準會 SOFR", "NY Fed SOFR", lambda e: (_ts(_stab_ts("sofr")), _stab_date("sofr")), 4),
    "cftc": ("CFTC 持倉", "CFTC positions", lambda e: (_ts(_stab_ts("cftc")), _stab_date("cftc")), 10),
    "fund": ("SEC 財報（XBRL）", "SEC XBRL", lambda e: (_ts(_fund_ts()), _stab_date("ai")), 120),
    "ff49": ("產業歷史（Ken French，每月更新）", "Ken French industries", lambda e: (_ts(_bub_ts("ts_check")), _bub_end()), 75),
    "baa": ("穆迪公司債利差（FRED，每月）", "Moody's Baa−Aaa", lambda e: (_ts(_bub_ts("ts_check")), _bub_credit_month()), 75),
    "cftc_eq": ("CFTC 股指期貨持倉（每週）", "CFTC equity futures", lambda e: (_ts(_bub_ts("ts_check")), _bub_cftc_date()), 10),
    "rel": ("FRED 發布日程", "FRED release dates", lambda e: (_ts(_rel_ts()), None), 0),
    "ofr": ("OFR 金融壓力指數（每日）", "OFR FSI", lambda e: (_ts(_trm("ts_check")), _trm_date("fsi")), 7),
    "custody": ("紐約聯準會託管美債（每週）", "Fed custody holdings", lambda e: (_ts(_trm("ts_check")), _trm_date("custody")), 14),
    "swpt": ("FRED 換匯額度／GDPNow", "FRED SWPT / GDPNOW", lambda e: (_ts(_trm("ts_check")), _trm_date("swaps")), 14),
    "jpy": ("日圓匯率＋CFTC 日圓部位", "Yen and CFTC", lambda e: (_ts(_trm("ts_check")), _trm_date("jpy")), 10),
    "ecb": ("歐洲央行 CISS＋各國公債（FRED 月資料）", "ECB CISS / FRED", lambda e: (_ts(_ead("ts_check")), _ead_date()), 7),
    "capexq": ("SEC 季報（資本支出／營收）", "SEC quarterly", lambda e: (_ts(_cxl("ts_check")), None), 0),
    "stockchk": ("SEC 季報＋每週股價（個股體檢）", "SEC filings + weekly prices", lambda e: (_ts(_sck("ts_check")), None), 0),
    "twfoi": ("外資台指期部位（FinMind）", "TAIFEX foreign OI", lambda e: (_ts(_twf("ts_check")), _twf_date()), 5),
    "observer": ("獨立 AI 觀察員", "AI observer", lambda e: (_ts(_stab_ts("ai_view")), _obs_date()), 4),
    "cover": ("覆蓋盤點", "Coverage audit", lambda e: (_ts(_stab_ts("coverage")), _cover_date()), 40),
    "model": ("模型體檢", "Model check", lambda e: (_ts(_g(e, "_quality_ts")) or _ts(_g(e, "lab", "ts")) or _ts(_g(e, "recompute_ts")), None), 0),
}

TAB_DEFAULT: Dict[str, List[str]] = {
    "overview": ["px", "ssi"], "premarket": ["px"], "tw_ai": ["twmacro"], "tw_bonds": ["twmacro"], "tw_credit": ["twmacro"], "tw_econ": ["twmacro"], "tw_money": ["twmacro", "tw"], "tw_life": ["twmacro"], "outlook": ["ssi", "px"], "portfolio": ["px"], "scores": ["stocks"], "signals": ["stocks"],
    "intel": ["stocks", "sec"], "econ": ["econ"], "tech": ["earnings"], "growth": ["earnings", "stocks"], "themes": ["stocks"],
    "industry": ["sec", "fred"], "mood": ["px"], "risk": ["ssi"], "flows": ["options"], "gurus": ["gurus"], "bonds": ["fred", "px"],
    "rotation": ["px"], "energy": ["px", "fred"], "crisis": ["ssi"], "valuation": ["fred", "px"], "markets": ["px"], "taiwan": ["tw", "taiwan"],
    "news": ["news"], "history": ["ssi"], "entry": ["px", "ssi"], "gbonds": ["fred"], "jgb": ["fred"], "ebonds": ["fred"], "wbonds": ["fred"], "cbonds": ["fred"],
    "cb_us": ["fred"], "cb_eu": ["fred"], "cb_em": ["fred"], "inputs": ["px", "fred"], "ai": ["px"], "stability": ["funding"],
}
CARD: Dict[str, List[str]] = {
    "sec_premarket": ["px"], "sec_focus": ["px", "fedwatch", "econ"], "sec_vix_hot": ["px"], "sec_vix_explain": ["px"],
    "sec_econ_mini": ["econ"], "sec_fg_mini": ["px", "crypto"], "sec_scores_mini": ["stocks"], "sec_trends": ["px"],
    "sec_ssi": ["ssi"], "sec_radar": ["ssi"], "sec_odds": ["ssi"],
    "sec_ai_entry": ["px", "ssi", "ofr"], "sec_cool_check": ["px", "ssi", "ofr"], "sec_cool_history": ["px"], "sec_bull_env": ["px", "fred", "canary"],
    "sec_cheap": ["fred", "px"], "sec_phased": ["px"], "sec_marks": ["fullmkt"], "sec_gb_brief": ["fred", "bondflows"], "sec_gb_sovereign": ["fred"],
    "sec_gb_corp": ["fred"], "sec_gb_flows": ["bondflows"], "sec_gb_tic": ["bondflows"], "sec_gb_mof": ["bondflows"],
    "sec_gb_jgb": ["jgb"], "sec_gb_europe": ["fred"], "sec_cb_brief": ["fred"], "sec_cb_us": ["fred"], "sec_cb_eu": ["fred"], "sec_cb_em": ["fred"],
    "sec_tw_brief": ["twmacro"], "sec_tw_calendar": ["twmacro"], "sec_tw_gov": ["twmacro", "fred"], "sec_tw_corp": ["twmacro"], "sec_tw_econ": ["twmacro"],
    "sec_tw_money": ["twmacro", "tw"], "sec_tw_life": ["twmacro"],
    "sec_fomc": ["fedwatch", "econ"], "sec_fomc_drift": ["px", "econ"], "sec_econ_week": ["econ"], "sec_econ_list": ["econ"],
    "sec_canary": ["canary"], "sec_macro": ["fred"], "sec_quality": ["model"], "sec_regime_split": ["model"], "sec_model_health": ["model"], "sec_analogs": ["fred", "px"],
    "sec_sector_brief": ["px", "fred", "earnings"], "sec_sector_table": ["px", "fred", "earnings"],
    "sec_bottom": ["px", "crypto"], "sec_crisis_track": ["ssi", "px"], "sec_credit_health": ["px", "sec"], "sec_ebp": ["fedres"], "sec_research_feed": ["feed"], "sec_st_brief": ["refund", "funding", "cftc"], "sec_st_refunding": ["refund", "fred"], "sec_st_funding": ["funding", "fred"], "sec_st_basis": ["cftc"], "sec_st_ai": ["fund"], "sec_st_coverage": ["cover"], "sec_tr_fsi": ["ofr", "px"], "sec_ai_observer": ["observer"], "sec_tw_foi": ["twfoi", "tw"], "sec_vix_term": ["px"], "sec_nh_nl": ["stocks", "px"], "sec_tr_custody": ["custody"], "sec_tr_dollar": ["swpt"], "sec_tr_yen": ["jpy", "px"], "sec_ai_cross": ["px", "ssi"], "sec_ai_brief": ["px", "ssi"], "sec_ai_score": ["px"], "sec_ai_heat": ["px", "fred", "fedres"], "sec_ai_bubble": ["ff49", "baa", "px"], "sec_ai_chain": ["stocks", "px", "ff49"], "sec_ai_capex": ["capexq"], "sec_stock_check": ["stockchk"], "sec_crisis": ["px"], "sec_timemachine": ["ssi"], "sec_dual": ["ssi", "px", "fred", "ofr"], "sec_europe": ["ecb", "px"], "sec_asia": ["px"], "sec_event_clock": ["rel", "econ", "px"], "sec_ai_elephant": ["cftc_eq"], "sec_ai_intro": ["px"], "sec_ai_turb": ["px"], "sec_ai_flock": ["px"], "sec_ai_quake": ["px"], "sec_ai_analog": ["px"], "sec_research_now": ["ssi", "fedres", "fred"], "sec_mpd": ["fedres"], "sec_vulnerability": ["fred", "fedres"], "sec_credit_rates": ["fred", "px"], "sec_distress": ["sec"], "sec_shock": ["ssi"], "sec_playbook_breaks": ["ssi", "px"],
    "sec_gamma": ["options"], "sec_darkpool": ["darkpool"], "sec_positioning": ["crypto", "px"],
    "sec_gurus": ["gurus"], "sec_insiders": ["insiders"], "sec_rates_radar": ["fred", "px"], "sec_bonds": ["fred", "treasury"],
    "sec_news": ["news"], "sec_calendar": ["calendar"], "sec_news_digest": ["news"], "sec_street": ["street"],
    "sec_fg": ["px", "crypto"], "sec_link": ["tw", "px"], "sec_taiwan": ["tw", "taiwan"], "sec_taiwan_trends": ["tw"],
    "sec_signal_scorecard": ["stocks"], "sec_earn_moves": ["earnings", "stocks"], "sec_analyst": ["earnings"],
    "sec_dividends": ["stocks"], "sec_filings": ["sec"], "sec_rev_exposure": ["sec"],
    "sec_tw_rev": ["earnings"], "sec_earn_cal": ["earnings"], "sec_earn_verdict": ["earnings"], "sec_latest_reports": ["earnings"],
}
NONE = {"sec_research", "sec_research_status", "sec_research_points", "sec_fees", "sec_terms", "sec_privacy", "sec_explainer", "sec_sizing", "sec_entry_links", "sec_research_bonds", "sec_tw_note"}   # static content
LIVE = {"sec_lookup", "sec_watch"}
MAX_AGE_H = {"fund": 9 * 24, "capexq": 9 * 24, "stockchk": 9 * 24}      # refreshed weekly by design                                    # fetched in the viewer's browser when the page opens


def sources_for(fname: str, tab: str) -> List[str]:
    if fname in NONE or fname in LIVE:
        return []
    return CARD.get(fname) or TAB_DEFAULT.get(tab, [])


def system_stamp(now: float) -> str:
    """For cards whose content does not come from a feed (explanations, terms, tools): when the page was built."""
    when = datetime.fromtimestamp(now, TPE).strftime("%m-%d %H:%M")
    return (f'<p class="upd" title="{esc("這張卡的內容不隨行情變動；時間是網站最後一次重新產生的時間")}">🕒 {T("說明／工具，不隨行情變動・網站產生", "Static content · built")} {when}'
            f' <span class="ago" data-ts="{int(now)}"></span></p>')


def live_stamp() -> str:
    return (f'<p class="upd">🕒 {T("即時：每次打開頁面時向報價服務抓取（Cloudflare 版），報價約有數分鐘延遲", "Live: fetched when the page opens (Cloudflare site)")}</p>')


def pending_stamp(tips) -> str:
    return (f'<p class="upd old" title="{esc("；".join(tips))}">🕒 {T("尚未取得資料", "No data yet")}'
            f'<span class="updd">{T("（" + "；".join(tips) + "）", "")}</span></p>')


# cards whose sources update on different clocks (daily / weekly / monthly): list each source's last check visibly
DETAIL = {"sec_europe", "sec_tw_foi", "sec_tr_fsi", "sec_tr_custody", "sec_tr_yen", "sec_event_clock", "sec_ai_bubble", "sec_ai_elephant", "sec_st_brief", "sec_st_refunding", "sec_st_funding", "sec_st_basis", "sec_st_ai", "sec_st_coverage"}


def stamp(eng, fname: str, tab: str, now: Optional[float] = None) -> str:
    keys = sources_for(fname, tab)
    now = now or time.time()
    if fname in LIVE:
        return live_stamp()
    if not keys:
        return system_stamp(now)
    try:
        from wsb.data.econcal import us_today
        today = us_today()
    except Exception:  # noqa: BLE001
        today = date.today()
    fetched, dates, old, tips = [], [], False, []
    for k in keys:
        if k not in SOURCES:
            continue
        zh, en, get, lag = SOURCES[k]
        try:
            ts, d = get(eng)
        except Exception:  # noqa: BLE001
            ts, d = None, None
        if ts:
            fetched.append(ts)
        if d:
            dates.append(d)
            if lag and d < (today - timedelta(days=lag)).isoformat():
                old = True
        if ts and now - ts > MAX_AGE_H.get(k, 36) * 3600:
            old = True
        w = datetime.fromtimestamp(ts, TPE).strftime("%m-%d %H:%M") if ts else "—"
        tips.append(f"{zh} 檢查 {w}" + (f"・資料日 {d}" if d else ""))
    if not fetched and not dates:
        return pending_stamp(tips)                    # it has sources but none has reported yet: say so, not the build time
    ts = min(fetched) if fetched else None
    d = max(dates) if dates else None
    when = datetime.fromtimestamp(ts, TPE).strftime("%m-%d %H:%M") if ts else None
    parts = ([f'{T("最後更新", "Updated")} {when}'] if when else []) + ([f'{T("資料日", "data")} {esc(d[5:])}'] if d else [])
    txt = "🕒 " + "・".join(parts)
    if fname in DETAIL and tips:
        txt += f'<span class="updd">{T("（各來源最後檢查：" + "；".join(tips) + "）", "")}</span>'
    ago = f' <span class="ago" data-ts="{int(ts)}"></span>' if ts else ""
    return (f'<p class="upd{" old" if old else ""}" title="{esc("；".join(tips))}">{txt}{ago}'
            + (f' <b>⚠ {T("資料偏舊", "stale")}</b>' if old else "") + "</p>")


def inject(html: str, st: str) -> str:
    """Put the stamp right under each card's title (every card a section returned); a card without a title gets it first."""
    if not st:
        return html
    import re
    starts = [m.start() for m in re.finditer(r'<section\b[^>]*\bclass="card', html)]     # id="…" may come before class
    out, i = [], 0
    for n, j in enumerate(starts):
        k = html.find("</h2>", j)
        nxt = starts[n + 1] if n + 1 < len(starts) else -1
        if k < 0 or (0 <= nxt < k):                    # no title in this card: right after its opening tag
            k = html.find(">", j)
            if k < 0:
                continue
            out.append(html[i:k + 1] + st)
            i = k + 1
            continue
        k += len("</h2>")
        out.append(html[i:k] + st)
        i = k
    out.append(html[i:])
    return "".join(out)


CSS = (".upd{font-size:11.5px;color:var(--tx2,#8a8f98);margin:-4px 0 8px}.updd{display:block;margin-top:2px;line-height:1.5}.upd.old{color:#e8a33d}.upd.old b{font-weight:700}"
       ".upd .ago{opacity:.8}")
JS = r"""
(function(){function f(){var n=Date.now()/1e3;document.querySelectorAll('.upd .ago').forEach(function(s){var a=n-(+s.dataset.ts);if(!(a>=0))return;
var en=document.documentElement.lang==='en';var t=a<90?(en?'just now':'剛剛'):a<5400?Math.round(a/60)+(en?' min ago':' 分鐘前'):a<172800?Math.round(a/3600)+(en?' h ago':' 小時前'):Math.round(a/86400)+(en?' d ago':' 天前');
s.textContent='（'+t+'）';});}f();setInterval(f,60000);})();
"""
