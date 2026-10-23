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
    "street": ("華爾街觀點", "Street views", lambda e: (None, _d(_g(e, "street", "asof"))), 10),
    "model": ("模型體檢", "Model check", lambda e: (_ts(_g(e, "_quality_ts")) or _ts(_g(e, "lab", "ts")) or _ts(_g(e, "recompute_ts")), None), 0),
}

TAB_DEFAULT: Dict[str, List[str]] = {
    "overview": ["px", "ssi"], "outlook": ["ssi", "px"], "portfolio": ["px"], "scores": ["stocks"], "signals": ["stocks"],
    "intel": ["stocks", "sec"], "econ": ["econ"], "tech": ["earnings"], "growth": ["earnings", "stocks"], "themes": ["stocks"],
    "industry": ["sec", "fred"], "mood": ["px"], "risk": ["ssi"], "flows": ["options"], "gurus": ["gurus"], "bonds": ["fred", "px"],
    "rotation": ["px"], "energy": ["px", "fred"], "crisis": ["ssi"], "valuation": ["fred", "px"], "markets": ["px"], "taiwan": ["tw", "taiwan"],
    "news": ["news"], "history": ["ssi"], "inputs": ["px", "fred"],
}
CARD: Dict[str, List[str]] = {
    "sec_premarket": ["px"], "sec_focus": ["px", "fedwatch", "econ"], "sec_vix_hot": ["px"], "sec_vix_explain": ["px"],
    "sec_econ_mini": ["econ"], "sec_fg_mini": ["px", "crypto"], "sec_scores_mini": ["stocks"], "sec_trends": ["px"],
    "sec_ssi": ["ssi"], "sec_radar": ["ssi"], "sec_odds": ["ssi"],
    "sec_fomc": ["fedwatch", "econ"], "sec_fomc_drift": ["px", "econ"], "sec_econ_week": ["econ"], "sec_econ_list": ["econ"],
    "sec_canary": ["canary"], "sec_macro": ["fred"], "sec_quality": ["model"], "sec_regime_split": ["model"], "sec_model_health": ["model"], "sec_analogs": ["fred", "px"],
    "sec_sector_brief": ["px", "fred", "earnings"], "sec_sector_table": ["px", "fred", "earnings"],
    "sec_bottom": ["px", "crypto"], "sec_distress": ["sec"], "sec_shock": ["ssi"], "sec_playbook_breaks": ["ssi", "px"],
    "sec_gamma": ["options"], "sec_darkpool": ["darkpool"], "sec_positioning": ["crypto", "px"],
    "sec_gurus": ["gurus"], "sec_insiders": ["insiders"], "sec_rates_radar": ["fred", "px"], "sec_bonds": ["fred", "treasury"],
    "sec_news": ["news"], "sec_calendar": ["calendar"], "sec_news_digest": ["news"], "sec_street": ["street"],
    "sec_fg": ["px", "crypto"], "sec_link": ["tw", "px"], "sec_taiwan": ["tw", "taiwan"], "sec_taiwan_trends": ["tw"],
    "sec_signal_scorecard": ["stocks"], "sec_earn_moves": ["earnings", "stocks"], "sec_analyst": ["earnings"],
    "sec_dividends": ["stocks"], "sec_filings": ["sec"], "sec_rev_exposure": ["sec"],
    "sec_tw_rev": ["earnings"], "sec_earn_cal": ["earnings"], "sec_earn_verdict": ["earnings"], "sec_latest_reports": ["earnings"],
}
NONE = {"sec_fees", "sec_terms", "sec_privacy", "sec_explainer", "sec_timemachine", "sec_crisis"}   # static or self-dated


def sources_for(fname: str, tab: str) -> List[str]:
    if fname in NONE:
        return []
    return CARD.get(fname) or TAB_DEFAULT.get(tab, [])


def stamp(eng, fname: str, tab: str, now: Optional[float] = None) -> str:
    keys = sources_for(fname, tab)
    if not keys:
        return ""
    now = now or time.time()
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
        if ts and now - ts > 36 * 3600:
            old = True
        w = datetime.fromtimestamp(ts, TPE).strftime("%m-%d %H:%M") if ts else "—"
        tips.append(f"{zh}：抓取 {w}" + (f"，資料日 {d}" if d else ""))
    if not fetched and not dates:
        return ""
    ts = min(fetched) if fetched else None
    d = max(dates) if dates else None
    when = datetime.fromtimestamp(ts, TPE).strftime("%m-%d %H:%M") if ts else None
    parts = ([f'{T("最後更新", "Updated")} {when}'] if when else []) + ([f'{T("資料日", "data")} {esc(d[5:])}'] if d else [])
    txt = "🕒 " + "・".join(parts)
    ago = f' <span class="ago" data-ts="{int(ts)}"></span>' if ts else ""
    return (f'<p class="upd{" old" if old else ""}" title="{esc("；".join(tips))}">{txt}{ago}'
            + (f' <b>⚠ {T("資料偏舊", "stale")}</b>' if old else "") + "</p>")


def inject(html: str, st: str) -> str:
    """Put the stamp right under each card's title (every card a section returned)."""
    if not st or "</h2>" not in html:
        return html
    out, i = [], 0
    while True:
        j = html.find('<section class="card', i)
        if j < 0:
            out.append(html[i:])
            break
        k = html.find("</h2>", j)
        nxt = html.find('<section class="card', j + 1)
        if k < 0 or (0 <= nxt < k):
            out.append(html[i:j + 1])
            i = j + 1
            continue
        k += len("</h2>")
        out.append(html[i:k] + st)
        i = k
    return "".join(out)


CSS = (".upd{font-size:11.5px;color:var(--tx2,#8a8f98);margin:-4px 0 8px}.upd.old{color:#e8a33d}.upd.old b{font-weight:700}"
       ".upd .ago{opacity:.8}")
JS = r"""
(function(){function f(){var n=Date.now()/1e3;document.querySelectorAll('.upd .ago').forEach(function(s){var a=n-(+s.dataset.ts);if(!(a>=0))return;
var en=document.documentElement.lang==='en';var t=a<90?(en?'just now':'剛剛'):a<5400?Math.round(a/60)+(en?' min ago':' 分鐘前'):a<172800?Math.round(a/3600)+(en?' h ago':' 小時前'):Math.round(a/86400)+(en?' d ago':' 天前');
s.textContent='（'+t+'）';});}f();setInterval(f,60000);})();
"""
