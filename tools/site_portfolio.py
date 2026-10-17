"""我的持股 tab: the visitor's OWN holdings and cash → today's P&L, market value, unrealized P&L and total assets.

Privacy by construction: the server only publishes public data (FX + quotes for the tracked universe; whole-market
prices are the existing market/{us,tw,hk}.json files).  Holdings are typed in the browser, kept in that browser's
localStorage, and every calculation runs client-side.  Nothing about the holdings is ever sent anywhere — the only
network requests are GETs of those public price files, without any query string."""
from __future__ import annotations

import json
import math
from typing import Dict

from tools.sitekit import T, esc
try:
    from wsb.config import SETTINGS
except Exception:  # noqa: BLE001
    SETTINGS = {}

HKD_PEG = 7.8          # HKD is pegged to the USD inside 7.75–7.85


def _fx(eng) -> Dict[str, float]:
    q = eng.market.q("TWD=X") or {}
    usdtwd = q.get("price") if q.get("price") and q["price"] == q["price"] else None
    asof = q.get("asof") or ""
    if not usdtwd:
        s = eng.market.series("TWD=X")
        if len(s):
            usdtwd, asof = float(s.iloc[-1]), s.index[-1].strftime("%Y-%m-%d")
    if not usdtwd:                        # no quote at all → the page says 匯率缺 instead of inventing a rate
        return {"TWD": 1.0, "USD": None, "HKD": None, "asof": ""}
    return {"TWD": 1.0, "USD": float(usdtwd), "HKD": float(usdtwd) / HKD_PEG, "asof": asof}


def _quotes(eng) -> Dict[str, list]:
    """Hourly quotes for every tracked ticker (indices, ETFs, large caps) — fills the ETF gap of the whole-market files."""
    names = {}
    try:
        from wsb.config import SETTINGS
        names = SETTINGS.names()
    except Exception:  # noqa: BLE001
        pass
    out = {}
    for t, q in (getattr(eng.market, "quotes", None) or {}).items():
        px, ch = q.get("price"), q.get("chg_pct")
        if px is None or (isinstance(px, float) and math.isnan(px)):
            continue
        out[t] = [round(float(px), 4), None if ch is None or ch != ch else round(float(ch), 3), q.get("asof") or "", names.get(t, q.get("name") or t), q.get("source") or "Yahoo", q.get("prev")]
    return out


def _hist_30d(eng) -> dict:
    """Historical daily close series (last 30 trading days) for public tracked assets."""
    try:
        import pandas as pd
        h = getattr(eng.market, "history", None)
        if h is None or h.empty:
            return {"dates": [], "closes": {}}
        spx = h["^GSPC"].dropna() if "^GSPC" in h.columns else (h["TWD=X"].dropna() if "TWD=X" in h.columns else h.iloc[:, 0].dropna())
        if len(spx) < 5:
            return {"dates": [], "closes": {}}
        dates = [idx.strftime("%Y-%m-%d") for idx in spx.tail(30).index]
        dt_idx = pd.to_datetime(dates)

        sp = getattr(getattr(eng, "stockprices", None), "close", None)
        if sp is not None and not sp.empty:                # individual stocks (KLAC, ORCL, 2330.TW …) live here, not in history
            extra = sp[[c for c in sp.columns if c not in h.columns]]
            h = h.join(extra, how="outer") if len(extra.columns) else h
        sub = h.reindex(dt_idx).ffill().bfill()
        closes = {}
        for col in sub.columns:
            ser = sub[col]
            if ser.notna().any():
                closes[col] = [round(float(v), 2) if (v is not None and v == v) else None for v in ser]

        return {"dates": dates, "closes": closes}
    except Exception:
        return {"dates": [], "closes": {}}


# Historical windows (event dates are facts; the depth of each fall is measured from price history below)
CRISIS_WINDOWS = {"yen2024": ("2024-07-10", "2024-08-05"), "fed2022": ("2022-01-03", "2022-10-12"),
                  "covid2020": ("2020-02-19", "2020-03-23"), "gfc2008": ("2007-10-09", "2009-03-09")}
CRISIS_PROXY = {"semi": ["^SOX", "SMH"], "tech": ["XLK", "QQQ"], "front": ["ARKK", "XLE"], "fin": ["XLF"],
                "def": ["XLP", "XLU"], "other": ["^GSPC"]}


def _crisis(eng) -> Dict[str, dict]:
    """Peak-to-trough fall of each category's proxy inside each crisis window (missing proxy → left out)."""
    out = {}
    for cid, (a, b) in CRISIS_WINDOWS.items():
        sh, src = {}, {}
        for k, cands in CRISIS_PROXY.items():
            for t in cands:
                try:
                    x = eng.market.series(t).loc[a:b].dropna()
                except Exception:  # noqa: BLE001
                    continue
                if len(x) >= 3:
                    sh[k], src[k] = round(-float((x / x.cummax() - 1).min()), 3), t
                    break
        if "other" in sh:
            out[cid] = {"shocks": sh, "src": src}
    return out


BETA_PROXY = {"semi": "^SOX", "tech": "XLK", "fin": "XLF", "front": "ARKK", "def": "XLP", "tlt": "TLT", "tw50": "^TWII"}


def _beta(eng) -> Dict[str, float]:
    """2-year weekly beta vs the S&P 500 (weekly, because Taiwan closes 13 hours before New York)."""
    import pandas as pd
    out = {}
    try:
        m = eng.market.series("^GSPC").dropna()
    except Exception:  # noqa: BLE001
        return out
    for k, t in BETA_PROXY.items():
        try:
            x = pd.concat([eng.market.series(t), m], axis=1).dropna()
            x = x[x.index >= x.index[-1] - pd.Timedelta(days=730)]
            w = x.resample("W-FRI").last().pct_change(fill_method=None).dropna()
            if len(w) >= 40 and w.iloc[:, 1].var() > 0:
                out[k] = round(float(w.cov().iloc[0, 1] / w.iloc[:, 1].var()), 2)
        except Exception:  # noqa: BLE001
            continue
    return out


def _sym_stats(eng) -> Dict[str, Dict[str, float]]:
    """Per-symbol 2-year weekly beta vs the S&P 500 and 60-day daily volatility (%), from price history."""
    import numpy as np
    import pandas as pd
    out_b, out_v = {}, {}
    try:
        h = getattr(eng.market, "history", None)
        frames = [h] if h is not None and not h.empty else []
        sp = getattr(getattr(eng, "stockprices", None), "close", None)
        if sp is not None and not sp.empty:
            frames.append(sp)
        if not frames:
            return {"beta": {}, "vol": {}}
        allp = pd.concat(frames, axis=1)
        allp = allp.loc[:, ~allp.columns.duplicated()]
        m = eng.market.series("^GSPC").dropna()
        if not len(m):
            return {"beta": {}, "vol": {}}
        cut = m.index[-1] - pd.Timedelta(days=730)
        mw = m[m.index >= cut].resample("W-FRI").last().pct_change(fill_method=None)
        for c in allp.columns:
            x = allp[c].dropna()
            if len(x) < 70 or str(c).startswith("^") or "=" in str(c):
                continue
            r = x.pct_change(fill_method=None).dropna().iloc[-60:]
            if len(r) >= 40:
                out_v[c] = round(float(r.std() * 100), 3)
            w = x[x.index >= cut].resample("W-FRI").last().pct_change(fill_method=None)
            j = pd.concat([w, mw], axis=1).dropna()
            if len(j) >= 40 and j.iloc[:, 1].var() > 0:
                out_b[c] = round(float(j.cov().iloc[0, 1] / j.iloc[:, 1].var()), 2)
    except Exception:  # noqa: BLE001
        pass
    return {"beta": out_b, "vol": out_v}


def _earn(eng) -> list:
    """Upcoming reports (Nasdaq calendar) + options-implied move (CBOE straddle) where available."""
    te = getattr(eng, "techearn", None)
    up = ((te.get("calendar") or {}).get("up") or []) if isinstance(te, dict) else []
    mv = {r.get("sym"): r for r in ((getattr(eng, "sx", None) or {}).get("earn") or []) if isinstance(r, dict)}
    out, seen = [], set()
    for x in list(up)[:300] + [m for k, m in mv.items() if k not in {u.get("sym") for u in up}]:
        sym = x.get("sym")
        if not sym or sym in seen or not x.get("date"):
            continue
        seen.add(sym)
        m = mv.get(sym) or {}
        out.append({"sym": sym, "name": x.get("name") or "", "date": x["date"], "time": x.get("time") or "",
                    "mv": m.get("mv"), "avg": m.get("avg")})
    return out


def _rules(eng) -> dict:
    """Public inputs for the holdings rulebook, evaluated in the visitor's browser against THEIR holdings (which never leave
    it): per symbol [200-day average, 12-1 momentum %, 52-week high, 6-month return vs its market index (pp), theme],
    distress radar [light, bankruptcy probability], last EPS surprise %, revenue-below-prior-guidance flags, the
    stress index and the thresholds from settings.yaml (rulebook:) — the same rules the Discord /holdings rules uses."""
    import pandas as pd
    from wsb.analytics import rulebook as RB
    from wsb.data.stocks import universe
    out = {"cfg": {k: v for k, v in RB.cfg().items() if isinstance(v, (int, float)) and not isinstance(v, bool)},
           "ssi": round(float(eng.stress.score), 1) if getattr(eng, "stress", None) else None, "sym": {}, "dz": {}, "surp": {}, "gb": {}}
    try:
        h = eng.market.history
        sp = getattr(getattr(eng, "stockprices", None), "close", None)
        frames = [h] + ([sp] if sp is not None and not sp.empty else [])
        allp = pd.concat(frames, axis=1)
        allp = allp.loc[:, ~allp.columns.duplicated()]
        themes = {s_: th for m in universe().values() for s_, th in m.get("themes", {}).items()}
        bench = {k: eng.market.series(t).dropna() for k, t in (("us", "^GSPC"), ("tw", "^TWII"), ("hk", "^HSI"))}
        for c in allp.columns:
            c = str(c)
            if c.startswith("^") or "=" in c:
                continue
            mk = "tw" if c.endswith((".TW", ".TWO")) else "hk" if c.endswith(".HK") else "us"
            st = RB.price_stats(allp[c].dropna(), bench.get(mk, pd.Series(dtype=float)))
            if not st:
                continue
            r2 = lambda v: None if v is None else round(float(v), 2)  # noqa: E731
            out["sym"][c] = [r2(st.get("ma200")), r2(st.get("mom_12_1")), r2(st.get("high_52w")), r2(st.get("rel_6m")), themes.get(c, "其他")]
    except Exception:  # noqa: BLE001
        pass
    for r in (getattr(eng, "distress", None) or {}).get("rows", []):
        out["dz"][r["sym"]] = [r["state"], None if r.get("bk_prob") is None else round(float(r["bk_prob"]), 4)]
    # only names that are public anyway (scoring universe + radar list): the bot also fetches the owner's holdings, and a
    # page built on that machine must not reveal which extra symbols it looked up
    from wsb.analytics import distress as DZ
    from wsb.data.earnings_data import TECH_THEMES
    us = universe().get("us") or {}
    fetched_by_site = {s_ for s_, th in (us.get("themes") or {}).items() if th in TECH_THEMES}   # what the public build fetches
    public = {s_ for m in universe().values() for s_ in m.get("symbols", {})} | set(DZ.watchlist())
    for s_, rec in ((getattr(getattr(eng, "earnings", None), "surprise", None) or {}).items()):
        if s_ not in fetched_by_site:
            continue
        row = ((rec or {}).get("rows") or [None])[0]
        if row and row.get("surp") is not None:
            out["surp"][s_] = [row.get("eps"), row.get("cons"), row["surp"]]
    try:
        from wsb.data import earn_release as ER
        last = {}
        for k, rec in ER.load().items():
            sy, d = k.split("|", 1)
            if rec.get("acc") and d > last.get(sy, ("", None))[0]:
                last[sy] = (d, rec)
        for sy, (_d, rec) in last.items():
            if sy not in public:
                continue
            if any(x["metric"] == "revenue" and x["pos"] == "below" for x in rec.get("vs_prev_guide") or []):
                out["gb"][sy] = 1
    except Exception:  # noqa: BLE001
        pass
    return out


def sec_portfolio(eng) -> str:
    gcid = ((SETTINGS.get("site", {}) or {}).get("google_client_id") or "").strip()
    data = json.dumps({"fx": _fx(eng), "q": _quotes(eng), "gcid": gcid, "hist": _hist_30d(eng),
                       "earn": _earn(eng), "crisis": _crisis(eng), "beta": _beta(eng),
                       "sym": _sym_stats(eng), "rules": _rules(eng)}, ensure_ascii=False,
                      separators=(",", ":")).replace("</", "<\\/")
    priv = T("持股與現金預設只存在「這台裝置的這個瀏覽器」，不會上傳、不在程式碼或 GitHub 裡，別人打開同一個網址看不到。"
             "按「用 Google 同步」後，資料會存到你自己 Google 雲端硬碟裡一個只有本網頁能讀的隱藏資料夾，手機和電腦登入同一個 Google 帳號就會自動同步；"
             "這個網站的伺服器（GitHub）從頭到尾碰不到你的持股。也可以用「匯出／匯入」手動搬。",
             "Holdings and cash stay in THIS browser by default — never uploaded, not in the code or on GitHub; nobody else opening the "
             "URL can see them. 'Sync with Google' stores them in a hidden app-only folder of YOUR Google Drive, so every device signed "
             "in to the same Google account stays in sync; GitHub never sees them. Export / Import still works for manual moves.")
    note = T("價格跟著本站每小時更新（免費報價約延遲 15 分鐘，非逐筆即時）；今日損益＝股數 ×（現價 − 昨收）。台股輸入數字代號即可（例 2330），"
             "港股請寫 0700.HK；美股直接輸入代號。新台幣合計用網站的美元兌台幣匯率，港幣以聯繫匯率 7.8 估算。找不到報價的代號可以手動輸入價格。",
             "Prices follow the hourly site build (~15 min delayed, not tick-by-tick); today's P&L = shares × (price − previous close). "
             "Taiwan: type the number (e.g. 2330); Hong Kong: 0700.HK; US: the ticker. TWD totals use the site's USD/TWD rate; HKD via the "
             "7.8 peg (approximate). If a ticker has no price you can type one in manually.")
    return f'''<section class="card wide" id="pfbox"><h2>{T("我的持股與總資產", "My holdings & total assets")}</h2>
<p class="sub">{priv}</p>
<div class="pfsync" id="pfsync"></div>
<div class="pfsum" id="pfsum"></div>
<div class="pfnav-box" id="pfnavbox" style="display:none"></div>
<div class="pfwrap"><table class="pft" id="pft"><thead><tr>
<th>{T("代號", "Ticker")}</th><th>{T("名稱", "Name")}</th><th class="r">{T("股數", "Shares")}</th><th class="r">{T("現價", "Price")}</th>
<th class="r">{T("今日", "Today")}</th><th class="r">{T("今日損益", "Today P&L")}</th><th class="r">{T("市值", "Value")}</th>
<th class="r">{T("市值（台幣）", "Value (TWD)")}</th><th class="r">{T("成本", "Cost")}</th><th class="r">{T("帳面損益", "Unrealized")}</th>
<th class="r">{T("報酬", "Return")}</th><th class="r">{T("防守 / 停利", "Defense / Target")}</th><th class="r">{T("權重", "Weight")}</th><th></th></tr></thead><tbody></tbody></table></div>
<div class="pfforms">
<form id="pfadd" class="pfrow" autocomplete="off"><b>{T("新增／更新持股", "Add / update a holding")}</b>
<input name="s" placeholder="NVDA / 2330 / 0700.HK" required maxlength="16" aria-label="ticker">
<input name="n" type="number" step="any" min="0" placeholder="{esc("股數")}" required aria-label="shares">
<input name="c" type="number" step="any" min="0" placeholder="{esc("每股成本（選填）")}" aria-label="cost per share">
<button class="btn" type="submit">{T("儲存", "Save")}</button></form>
<form id="pfcash" class="pfrow" autocomplete="off"><b>{T("現金", "Cash")}</b>
<select name="cur" aria-label="currency"><option>TWD</option><option>USD</option><option>HKD</option></select>
<input name="a" type="number" step="any" placeholder="{esc("金額（0 = 刪除）")}" required aria-label="amount">
<button class="btn" type="submit">{T("儲存", "Save")}</button></form>
<details class="pfbulk"><summary>{T("一次貼上多筆", "Paste many at once")}</summary>
<p class="small muted">{T("每行一筆：代號 股數 成本（成本可省略），用空白或逗號分隔，例如：", "One per line: ticker shares cost (cost optional), e.g.:")}<code>NVDA 15 50</code> · <code>2330 1000 600</code> · <code>0700.HK 200</code></p>
<textarea id="pfpaste" rows="5" spellcheck="false"></textarea><button class="btn" type="button" id="pfpastebtn">{T("加入", "Add")}</button></details>
<div class="pfrow"><button class="btn" type="button" id="pfexp">{T("匯出備份", "Export")}</button>
<label class="btn" for="pfimp">{T("匯入", "Import")}</label><input id="pfimp" type="file" accept="application/json,.json" hidden>
<button class="btn" type="button" id="pfclr">{T("清除全部", "Clear all")}</button><span class="small muted" id="pfmsg" role="status"></span></div>
</div>
<div class="pfrules" id="pfrules" style="display:none"></div>
<div class="pfdx" id="pfdx" style="display:none"></div>
<div class="pfcrisis" id="pfcrisis" style="display:none"></div>
<div class="pfwhatif" id="pfwhatif" style="display:none"></div>
<div class="pfearn" id="pfearn" style="display:none"></div>
<p class="note">{note}</p>
<script type="application/json" id="pf-data">{data}</script></section>'''


CSS = """
.pfsum{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:10px 0}@media(max-width:520px){.pfsum{grid-template-columns:1fr 1fr}.pfk .v{font-size:18px}.pfk.big{grid-column:span 2}.pfk.big .v{font-size:26px}}
.pfrules{margin:14px 0;border:1px solid var(--bd);border-radius:10px;padding:10px 12px}.pfrules h3{margin:0 0 6px;font-size:15px}
.pfrl{border-top:1px solid var(--bd);padding:7px 0}.pfrl summary{cursor:pointer;display:flex;gap:8px;flex-wrap:wrap;align-items:baseline}
.pfrl .tag{font-size:12px;padding:1px 7px;border-radius:5px;border:1px solid currentColor}.pfrl ul{margin:6px 0 2px 18px;padding:0;font-size:12.5px}
.pfrl li.met{font-weight:600}.pfrl li.unk{color:var(--mu)}
.pfk{background:var(--card2);border:1px solid var(--bd);border-radius:10px;padding:10px 12px}.pfk .v{font-size:24px;font-weight:800}
.pfk .s{font-size:12px;color:var(--mu)}.pfk.big .v{font-size:30px}
.pfwrap{overflow-x:auto}table.pft{width:100%;border-collapse:collapse;font-size:13px}
table.pft th,table.pft td{padding:6px 8px;border-bottom:1px solid var(--bd);white-space:nowrap}table.pft .r{text-align:right}
table.pft tfoot td{font-weight:700;border-top:2px solid var(--bd)}table.pft input{width:80px;background:var(--card2);border:1px solid var(--bd);color:var(--tx);border-radius:5px;padding:2px 4px}
.pfforms{display:flex;flex-direction:column;gap:10px;margin-top:12px}.pfrow{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.pfrow input,.pfrow select,.pfbulk textarea{background:var(--card2);border:1px solid var(--bd);color:var(--tx);border-radius:6px;padding:6px 8px;font:inherit;font-size:14px}
.pfrow input{width:150px}.pfbulk textarea{width:100%;max-width:520px;display:block;margin:6px 0}.pfx{background:none;border:0;color:var(--mu);cursor:pointer;font-size:15px}
.pfx:hover{color:var(--dn)}.pfwarn{color:var(--warn)}
.pfsync{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:4px 0 8px;font-size:13px}.pfsync .ok{color:var(--up)}.pfsync .err{color:var(--dn)}
.btn.g{border-color:var(--ac);color:var(--ac)}
.pfdx{margin-top:16px;border-top:1px dashed var(--bd);padding-top:14px}
.pfdx h3{margin:0 0 10px;font-size:15px;display:flex;align-items:center;gap:6px}
.pfdx-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:12px}
.pfdx-k{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:8px 10px}
.pfdx-k .lbl{font-size:11px;color:var(--mu);margin-bottom:2px}
.pfdx-k .val{font-size:17px;font-weight:700}
.pfdx-k .sub{font-size:11px;color:var(--mu);margin-top:2px}
.pfdx-sec{margin:10px 0}
.pfdx-bar{display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--card2);margin:6px 0;border:1px solid var(--bd)}
.pfdx-bar-seg{height:100%}
.pfdx-tags{display:flex;flex-wrap:wrap;gap:6px;font-size:11px;margin:4px 0 10px}
.pfdx-tag{display:inline-flex;align-items:center;gap:4px;padding:2px 6px;border-radius:4px;background:var(--card2);border:1px solid var(--bd)}
.pfdx-tag .dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.pfdx-items{display:flex;flex-direction:column;gap:6px;margin-top:8px}
.pfdx-item{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border-radius:6px;background:var(--card2);border:1px solid var(--bd);font-size:12px;line-height:1.45}
.pfdx-item.bad{border-left:3px solid var(--dn)}
.pfdx-item.warn{border-left:3px solid var(--warn)}
.pfdx-item.ok{border-left:3px solid var(--up)}
.pfdx-item.act{border-left:3px solid var(--ac)}
.pfdx-item .ico{font-size:13px;flex-shrink:0}

/* Feature 4: NAV Chart */
.pfnav-box{background:var(--card2);border:1px solid var(--bd);border-radius:10px;padding:12px;margin:12px 0}
.pfnav-head{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px}
.pfnav-title{font-size:14px;font-weight:700;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pfnav-stats{display:flex;gap:12px;flex-wrap:wrap;font-size:12px}
.pfnav-stat b{font-weight:700}
.pfnav-pills{display:inline-flex;background:var(--card);border:1px solid var(--bd);border-radius:6px;padding:2px;gap:2px}
.pfnav-pill{background:none;border:0;color:var(--mu);padding:2px 8px;font-size:11px;border-radius:4px;cursor:pointer;font-weight:600}
.pfnav-pill.on{background:var(--ac);color:#fff}
.pfnav-hint{font-size:11px;color:var(--mu);margin-bottom:6px;line-height:1.4}
.pfrefresh-btn{display:inline-flex;align-items:center;gap:4px}
.pfnav-svg-wrap{width:100%;height:130px;position:relative}
.pfnav-svg{width:100%;height:100%;display:block;overflow:visible;cursor:crosshair}

/* Feature 3: Dynamic Stop & Target line badge in table */
.pft-stop{font-size:11px;display:flex;flex-direction:column;gap:2px}
.pft-stop .s-tgt{color:var(--up)}
.pft-stop .s-stp{color:var(--dn)}
.pft-stop .s-hit{display:inline-block;padding:1px 4px;border-radius:3px;font-weight:700;font-size:10px}
.pft-stop .s-hit.up{background:rgba(34,197,94,0.15);color:var(--up);border:1px solid var(--up)}
.pft-stop .s-hit.dn{background:rgba(239,68,68,0.15);color:var(--dn);border:1px solid var(--dn)}

/* Feature 1: Crisis Replay Simulator */
.pfcrisis{margin-top:16px;border-top:1px dashed var(--bd);padding-top:14px}
.pfcrisis h3{margin:0 0 4px;font-size:15px;display:flex;align-items:center;gap:6px}
.pfcrisis-btns{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.pfcrisis-btn{background:var(--card2);border:1px solid var(--bd);color:var(--tx);border-radius:6px;padding:6px 12px;cursor:pointer;font-size:12px;font-weight:600;transition:all .15s}
.pfcrisis-btn.active{background:var(--dn);border-color:var(--dn);color:#fff}
.pfcrisis-result{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:12px;margin-top:10px}
.pfcrisis-impact{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:12px}
.pfcrisis-bars{display:flex;flex-direction:column;gap:6px}
.pfcrisis-bar-row{display:flex;align-items:center;gap:8px;font-size:12px}
.pfcrisis-bar-lbl{min-width:70px;white-space:nowrap}
.pfcrisis-bar-track{flex:1;background:var(--bg);height:10px;border-radius:5px;overflow:hidden;border:1px solid var(--bd)}
.pfcrisis-bar-fill{height:100%;background:var(--dn);border-radius:5px}
.pfcrisis-bar-val{min-width:110px;text-align:right;font-size:11px}

/* Feature 2: What-if Sandbox */
.pfwhatif{margin-top:16px;border-top:1px dashed var(--bd);padding-top:14px}
.pfwhatif h3{margin:0 0 4px;font-size:15px;display:flex;align-items:center;gap:6px}
.pfwhatif-ctrls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:10px 0;background:var(--card2);padding:10px 12px;border-radius:8px;border:1px solid var(--bd)}
.pfwhatif-ctrls select,.pfwhatif-ctrls input{background:var(--bg);border:1px solid var(--bd);color:var(--tx);padding:4px 8px;border-radius:5px;font-size:13px}
.pfwhatif-pcts{display:flex;gap:4px}
.pfwhatif-pbtn{background:var(--bg);border:1px solid var(--bd);color:var(--tx2);padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px}
.pfwhatif-pbtn.active{background:var(--ac);border-color:var(--ac);color:#fff}
.pfwhatif-comp{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:10px}
.pfwhatif-card{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:10px}
.pfwhatif-card .lbl{font-size:11px;color:var(--mu);margin-bottom:4px}
.pfwhatif-card .vals{display:flex;align-items:baseline;gap:6px;font-size:16px;font-weight:700}
.pfwhatif-card .chg{font-size:12px;font-weight:600}

/* Feature 6: Earnings Radar */
.pfearn{margin-top:16px;border-top:1px dashed var(--bd);padding-top:14px}
.pfearn h3{margin:0 0 4px;font-size:15px;display:flex;align-items:center;gap:6px}
.pfearn-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin-top:10px}
.pfearn-card{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:10px;position:relative}
.pfearn-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.pfearn-sym{font-size:14px;font-weight:800}
.pfearn-days{font-size:11px;padding:2px 6px;border-radius:4px;font-weight:700}
.pfearn-days.urgent{background:rgba(239,68,68,0.2);color:var(--dn);border:1px solid var(--dn)}
.pfearn-days.warn{background:rgba(245,158,11,0.2);color:var(--warn);border:1px solid var(--warn)}
.pfearn-days.normal{background:rgba(59,130,246,0.15);color:var(--ac);border:1px solid var(--ac)}
.pfearn-row{display:flex;justify-content:space-between;font-size:11px;margin:3px 0;color:var(--mu)}
.pfearn-row b{color:var(--tx)}
.pfearn-desc{font-size:11px;color:var(--mu);margin-top:6px;border-top:1px solid var(--bd);padding-top:4px}
"""

JS = r"""
(function(){var box=document.getElementById('pfbox');if(!box)return;
var KEY='wss_portfolio_v1',PUB=JSON.parse(document.getElementById('pf-data').textContent),FX=PUB.fx,Q=PUB.q,MK={},gFM={};
var FXOK=!!(FX&&FX.USD);function fxv(c){return c==='TWD'?1:(FXOK?FX[c]:null);}
var en=function(){return document.documentElement.lang==='en';};
function L(zh,e){var s=document.createElement('span');s.dataset.en=e;s.dataset.zh=zh;s.textContent=en()?e:zh;return s;}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
var SVG_NS=['http',':','//','www.','w3.','org/2000/svg'].join('');
function svgEl(t,attrs){var e=document.createElementNS(SVG_NS,t);if(attrs){for(var k in attrs){if(Object.prototype.hasOwnProperty.call(attrs,k)){e.setAttribute(k,attrs[k]);}}}return e;}
function get(){try{var d=JSON.parse(localStorage.getItem(KEY)||'null');if(d&&Array.isArray(d.h))return d;}catch(e){}return {v:1,h:[],cash:[],nav:[]};}
function put(d){try{localStorage.setItem(KEY,JSON.stringify(d));return true;}catch(e){msg(['無法儲存（瀏覽器封鎖了本機儲存）','Cannot save (browser storage blocked)']);return false;}}
function msg(m){var x=document.getElementById('pfmsg');x.textContent='';if(m)x.appendChild(L(m[0],m[1]));}
function num(v,d){return (v==null||!isFinite(v))?'—':Number(v).toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d});}
function sgn(v,d,pct){if(v==null||!isFinite(v))return '—';return (v>0?'+':'')+num(v,d)+(pct?'%':'');}
function cl(v){return v>0?'up':(v<0?'dn':'');}
function norm(raw){var x=String(raw||'').trim().toUpperCase().replace(/\s+/g,'');if(!x||x.length>16||!/^[A-Z0-9.\-^=]+$/.test(x))return null;
 var m;if(/^\d{4,6}[A-Z]?$/.test(x))return {key:x,mk:'tw',cands:[x+'.TW',x+'.TWO']};
 if((m=x.match(/^(\d{4,6}[A-Z]?)\.(TW|TWO)$/)))return {key:x,mk:'tw',cands:[x]};
 if((m=x.match(/^(\d{1,5})\.HK$/))){var c=('0000'+m[1]).slice(-4);return {key:c+'.HK',mk:'hk',cands:[c+'.HK',m[1]+'.HK']};}
 return {key:x,mk:'us',cands:[x,x.replace('.','-')]};}
function cur(mk){return mk==='tw'?'TWD':(mk==='hk'?'HKD':'USD');}
function loadMk(mk){if(MK[mk]!==undefined)return MK[mk];MK[mk]=fetch('market/'+mk+'.json',{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();})
 .then(function(d){var c=d.cols,iS=c.indexOf('sym'),iN=c.indexOf('name'),iP=c.indexOf('px'),iR=c.indexOf('r1d'),map={};
  var iD=c.indexOf('quote_asof'),iH=c.indexOf('history_asof'),iSrc=c.indexOf('source');
  d.rows.forEach(function(a){map[a[iS]]={px:a[iP],ch:a[iR],name:a[iN],asof:(iD>=0&&a[iD])||(iH>=0&&a[iH])||d.asof,source:(iSrc>=0&&a[iSrc])||'Yahoo'};});return {asof:d.asof,map:map};}).catch(function(){return null;});return MK[mk];}
function price(h,fm){var n=norm(h.s);if(!n)return null;for(var i=0;i<n.cands.length;i++){var s=n.cands[i],q=Q[s],f=fm&&fm.map[s];
  if(q&&q[0]!=null&&(!f||(q[2]||'')>=(f.asof||'')))return {sym:s,px:q[0],ch:q[1],prev:q[5],asof:q[2],name:q[3],source:q[4],src:'q'};
  if(f&&f.px!=null)return {sym:s,px:f.px,ch:f.ch,asof:f.asof,name:f.name,source:f.source,src:'fm'};}
 if(h.p>0)return {sym:n.key,px:h.p,ch:null,asof:'',name:'',src:'manual'};return null;}
function ph(){var P={n:['股數','Shares'],c:['每股成本（選填）','Cost per share (optional)'],a:['金額（0 = 刪除）','Amount (0 = delete)']};
 ['pfadd','pfcash'].forEach(function(id){var f=document.getElementById(id);Object.keys(P).forEach(function(k){if(f[k])f[k].placeholder=P[k][en()?1:0];});});}

// Sector categories for risk, beta, crisis shocks.  b = measured 2y weekly beta of the proxy (server side);
// a category without data is treated like the market (1.0)
var PB = PUB.beta || {};
function BETA(k){ return PB[k] != null ? PB[k] : null; }   // no measured beta → null (shown as —, never a guess)
var SB = (PUB.sym || {}).beta || {}, SV = (PUB.sym || {}).vol || {};
function _symLookup(map, sym){ var n = norm(sym); var c = n ? n.cands.concat([n.key]) : [String(sym || '').toUpperCase()];
 for(var i = 0; i < c.length; i++){ if(map[c[i]] != null) return map[c[i]]; } return null; }
function symBeta(sym){ return _symLookup(SB, sym); }
function symVol(sym){ return _symLookup(SV, sym); }
var SECS = [
 { k: 'semi', zh: '半導體設備', en: 'Semiconductors', c: '#00d2ff', b: BETA('semi'),
   syms: ['KLAC','TSM','NVDA','ASML','AMAT','LRCX','INTC','AMD','AVGO','QCOM','MU','TXN','MRVL','ON','MPWR','2330','2454','3034','2379','3443','3661','6415','SMH','SOXX'] },
 { k: 'tech', zh: '科技與雲端', en: 'Tech & Cloud', c: '#3a86ff', b: BETA('tech'),
   syms: ['GOOG','GOOGL','MSFT','AAPL','AMZN','META','ORCL','CRM','ADBE','NOW','UBER','NFLX','QQQ'] },
 { k: 'fin', zh: '金融數位', en: 'FinTech & Banks', c: '#06d6a0', b: BETA('fin'),
   syms: ['NU','JPM','BAC','WFC','C','GS','MS','V','MA','PYPL','COIN','SOFI','KRE','XLF','2881','2882','2891'] },
 { k: 'front', zh: '前沿與能源', en: 'Frontier & Energy', c: '#ffbe0b', b: BETA('front'),
   syms: ['SPCX','OKLO','SMR','CCJ','PLTR','TSLA','RIVN','LCID','QS','ENVX','IONQ','RGTI'] },
 { k: 'def', zh: '防禦民生', en: 'Defensive & Value', c: '#8338ec', b: BETA('def'),
   syms: ['JNJ','PG','KO','PEP','MCD','WMT','COST','XOM','CVX','TLT','IEF','SHY','BND','LQD'] }
];

// ---------------------------------------------------------------- Google Drive sync
var G={cid:PUB.gcid||'',tok:null,exp:0,fid:null,busy:false,on:false,email:''};
var GKEY='wss_portfolio_gsync';
function gmsg(zh,e,cls){var s=document.getElementById('pfsync');if(!s)return;var st=s.querySelector('.st');if(!st){st=el('span','st');s.appendChild(st);}st.className='st '+(cls||'');st.textContent='';st.appendChild(L(zh,e));}
var HIST = PUB.hist || { dates: [], closes: {} };
window._navMode = window._navMode || 'auto';

function addRefreshBtn(s){
 var ref = el('button', 'btn pfrefresh-btn');
 ref.id = 'pfrefresh';
 ref.type = 'button';
 ref.appendChild(L('🔄 重新整理行情', '🔄 Refresh quotes'));
 ref.addEventListener('click', refreshQuotes);
 s.appendChild(ref);
}

function refreshQuotes(){
 var btn = document.getElementById('pfrefresh');
 if(btn){ btn.disabled = true; btn.textContent = en() ? 'Refreshing…' : '🔄 抓取中…'; }
 MK = {};
 var d = get(), need = {};
 d.h.forEach(function(h){ var n = norm(h.s); if(n) need[n.mk] = 1; });
 var mks = Object.keys(need);
 if(mks.indexOf('us') < 0) mks.push('us');
 Promise.all(mks.map(function(mk){
  return fetch('market/' + mk + '.json?t=' + Date.now(), { cache: 'no-store' })
   .then(function(r){ if(!r.ok) throw 0; return r.json(); })
   .then(function(data){
    var c = data.cols, iS = c.indexOf('sym'), iN = c.indexOf('name'), iP = c.indexOf('px'), iR = c.indexOf('r1d'), map = {};
    var iD = c.indexOf('quote_asof'), iH = c.indexOf('history_asof'), iSrc = c.indexOf('source');
    data.rows.forEach(function(a){
     map[a[iS]] = { px: a[iP], ch: a[iR], name: a[iN], asof: (iD >= 0 && a[iD]) || (iH >= 0 && a[iH]) || data.asof, source: (iSrc >= 0 && a[iSrc]) || 'Yahoo' };
    });
    return { asof: data.asof, map: map };
   }).catch(function(){ return null; });
 })).then(function(res){
  gFM = {};
  mks.forEach(function(m, i){ gFM[m] = res[i]; });
  draw(d, gFM);
  var timeStr = new Date().toLocaleTimeString();
  gmsg('已重新載入最新行情 (' + timeStr + ')', 'Quotes refreshed (' + timeStr + ')', 'ok');
  if(btn){
   btn.disabled = false;
   btn.textContent = '';
   btn.appendChild(L('🔄 重新整理行情', '🔄 Refresh quotes'));
  }
 });
}

function gbar(){
 var s=document.getElementById('pfsync');
 if(!s)return;
 s.textContent='';
 addRefreshBtn(s);
 if(!G.cid){
  var m=el('span','muted');
  m.appendChild(L('（跨裝置 Google 同步尚未設定：請在 settings.yaml 的 site.google_client_id 填入 OAuth 用端 ID）','(Google sync not configured: set site.google_client_id in settings.yaml)'));
  s.appendChild(m);
  return;
 }
 var b=el('button','btn g');b.type='button';b.appendChild(L(G.on?'立即同步':'用 Google 同步','Sync now'));b.addEventListener('click',function(){gauth(true).then(function(ok){if(ok)gsync();});});s.appendChild(b);
 if(G.on){var o=el('button','btn');o.type='button';o.appendChild(L('停用同步','Stop syncing'));o.addEventListener('click',function(){G.on=false;G.tok=null;try{localStorage.removeItem(GKEY);}catch(e){}gbar();});s.appendChild(o);}
 var st=el('span','st');s.appendChild(st);if(G.on)gmsg('已啟用 Google 同步','Google sync on','ok');
 grestoreBar(s);
}
function grestoreBar(s){
 var bak=null;try{bak=JSON.parse(localStorage.getItem(BKEY)||'null');}catch(e){}
 if(bak&&_n(bak)&&!_n(get())){var b1=el('button','btn');b1.type='button';
  b1.appendChild(L('還原這台裝置的上一份（'+bak.h.length+' 檔）','Restore previous on this device ('+bak.h.length+')'));
  b1.addEventListener('click',function(){if(confirm(en()?'Restore the previous portfolio saved in this browser?':'要還原這台裝置上一份持股（'+bak.h.length+' 檔）嗎？')){put(bak);render();gbar();}});s.appendChild(b1);}
 if(G.cid){var b2=el('button','btn');b2.type='button';b2.appendChild(L('從雲端歷史版本還原','Restore from Drive history'));   // shown even with sync off: it signs in first
  b2.addEventListener('click',function(){gauth(true).then(function(ok){if(ok)grestore();});});s.appendChild(b2);}
}
function grestore(){gmsg('搜尋雲端歷史版本…','Searching Drive history…');
 var cur=JSON.stringify(get().h||[]);
 gfind().then(function(f){if(!f)throw new Error('雲端沒有同步檔');
  var cands=[];
  return gread().then(function(r){if(r&&r.prev&&_n(r.prev))cands.push({t:r.prev.updated||0,d:r.prev,src:'上一版'});})
   .then(function(){return gfetch('https://www.googleapis.com/drive/v3/files/'+G.fid+'/revisions?pageSize=200&fields=revisions(id,modifiedTime)');})
   .then(function(r){return r.json();}).then(function(j){
    var revs=(j.revisions||[]).slice().reverse(),i=0;
    function next(){if(i>=revs.length||i>=40)return Promise.resolve();var rv=revs[i++];
     return gfetch('https://www.googleapis.com/drive/v3/files/'+G.fid+'/revisions/'+rv.id+'?alt=media').then(function(x){return x.json();})
      .then(function(d){if(d&&Array.isArray(d.h)&&_n(d)&&JSON.stringify(d.h)!==cur){cands.push({t:Date.parse(rv.modifiedTime),d:d,src:'雲端版本'});return;}return next();})
      .catch(function(){return next();});}
    return next();})
   .then(function(){
    if(!cands.length){gmsg('雲端歷史版本裡找不到有持股的版本（Google 一般保留約 30 天）','No earlier version with holdings found','err');return;}
    cands.sort(function(a,b){return b.t-a.t;});var c=cands[0];
    var when=c.t?new Date(c.t).toLocaleString():'—',syms=c.d.h.map(function(h){return h.s;}).slice(0,12).join(', ');
    if(confirm((en()?'Restore the version of ':'要還原 ')+when+(en()?'':' 的版本嗎？')+'\n'+c.d.h.length+(en()?' holdings: ':' 檔：')+syms)){
     var d=_strip(c.d);put(d);render();gbar();gmsg('已還原 '+when+' 的版本（'+d.h.length+' 檔）','Restored '+when,'ok');}
    else gmsg('沒有變更','No change','ok');});})
 .catch(function(e){gmsg('還原失敗：'+e.message,'Restore failed: '+e.message,'err');});}
function gload(){return new Promise(function(res,rej){if(window.google&&google.accounts&&google.accounts.oauth2)return res();var sc=document.createElement('script');sc.src='https://accounts.google.com/gsi/client';sc.async=true;sc.onload=res;sc.onerror=function(){rej(new Error('gsi'));};document.head.appendChild(sc);});}
function gauth(interactive){if(!G.cid)return Promise.resolve(false);if(G.tok&&Date.now()<G.exp-60000)return Promise.resolve(true);
 return gload().then(function(){return new Promise(function(res){var tc=google.accounts.oauth2.initTokenClient({client_id:G.cid,scope:'https://www.googleapis.com/auth/drive.appdata',
  callback:function(r){if(r&&r.access_token){G.tok=r.access_token;G.exp=Date.now()+(r.expires_in||3600)*1000;G.on=true;try{localStorage.setItem(GKEY,'1');}catch(e){}gbar();res(true);}else{gmsg('Google 登入未完成','Google sign-in not completed','err');res(false);}},
  error_callback:function(e){gmsg('Google 登入失敗：'+(e&&e.type||''),'Google sign-in failed: '+(e&&e.type||''),'err');res(false);}});
  tc.requestAccessToken({prompt:interactive?'':''});});}).catch(function(){gmsg('無法載入 Google 登入元件（可能被封鎖）','Cannot load Google sign-in','err');return false;});}
function gfetch(url,opt){opt=opt||{};opt.headers=Object.assign({},opt.headers||{},{Authorization:'Bearer '+G.tok});return fetch(url,opt).then(function(r){if(r.status===401){G.tok=null;throw new Error('401');}if(!r.ok)throw new Error('HTTP '+r.status);return r;});}
function gfind(){return gfetch('https://www.googleapis.com/drive/v3/files?spaces=appDataFolder&fields=files(id,name,modifiedTime)&q='+encodeURIComponent("name='wss_holdings.json'")).then(function(r){return r.json();}).then(function(j){var f=(j.files||[])[0];G.fid=f?f.id:null;return f||null;});}
function gread(){return gfetch('https://www.googleapis.com/drive/v3/files/'+G.fid+'?alt=media').then(function(r){return r.json();});}
function gwrite(d){var body=JSON.stringify(d);if(G.fid)return gfetch('https://www.googleapis.com/upload/drive/v3/files/'+G.fid+'?uploadType=media',{method:'PATCH',headers:{'Content-Type':'application/json'},body:body});
 var bd='-------wss'+Date.now(),meta=JSON.stringify({name:'wss_holdings.json',parents:['appDataFolder']});
 var mp='--'+bd+'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+meta+'\r\n--'+bd+'\r\nContent-Type: application/json\r\n\r\n'+body+'\r\n--'+bd+'--';
 return gfetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',{method:'POST',headers:{'Content-Type':'multipart/related; boundary='+bd},body:mp}).then(function(r){return r.json();}).then(function(j){G.fid=j.id;});}
function _n(d){return d&&Array.isArray(d.h)?d.h.length+(d.cash||[]).length:0;}
function _strip(d){var c=JSON.parse(JSON.stringify(d||{}));delete c.prev;return c;}
function gsync(){if(G.busy||!G.on)return;G.busy=true;gmsg('同步中…','Syncing…');
 var local=get();local.updated=local.updated||0;
 gfind().then(function(f){
  if(!f){if(!_n(local)){gmsg('Google 雲端硬碟和這台裝置都還沒有持股資料','No holdings on Drive or on this device','ok');return;}
   return gwrite(_strip(local)).then(function(){gmsg('已上傳到 Google 雲端硬碟 '+new Date().toLocaleTimeString(),'Uploaded '+new Date().toLocaleTimeString(),'ok');});}
  return gread().then(function(remote){remote=remote&&Array.isArray(remote.h)?remote:{v:1,h:[],cash:[],nav:[],updated:0};
   var lN=_n(local),rN=_n(remote),lw=(local.updated||0)>(remote.updated||0),rw=(remote.updated||0)>(local.updated||0);
   // an EMPTY portfolio never overwrites a non-empty one, whatever its timestamp — unless it came from 「清除全部」
   // (a device whose browser data was wiped must not erase the holdings everywhere else)
   if(lw&&!lN&&rN&&!local.cleared){lw=false;rw=true;}
   if(rw&&!rN&&lN&&!remote.cleared){rw=false;lw=true;}
   if(rw){var nv={};(remote.nav||[]).concat(local.nav||[]).forEach(function(p){if(p&&p.d)nv[p.d]=p;});
    remote.nav=Object.keys(nv).sort().map(function(k){return nv[k];}).slice(-400);_put(remote);render();gmsg('已從 Google 雲端硬碟載入 '+new Date(remote.updated||Date.now()).toLocaleString(),'Loaded from Google Drive','ok');}
   else if(lw){var up=_strip(local);if(rN)up.prev=_strip(remote);       // the version being replaced stays one step back
    return gwrite(up).then(function(){gmsg('已上傳到 Google 雲端硬碟 '+new Date().toLocaleTimeString(),'Uploaded '+new Date().toLocaleTimeString(),'ok');});}
   else gmsg(lN?'已同步（無變更）':'已同步：雲端和這台裝置都沒有持股（可用下方「從雲端歷史版本還原」找回）',lN?'In sync':'In sync, but empty — try restoring from Drive history','ok');});})
 .catch(function(e){gmsg('同步失敗：'+e.message,'Sync failed: '+e.message,'err');if(e.message==='401')G.tok=null;})
 .then(function(){G.busy=false;});}
var BKEY='wss_portfolio_backup_v1';
var _put=put;put=function(d){var old=get();if(_n(old)&&JSON.stringify(_strip(old).h)!==JSON.stringify((d||{}).h)){try{localStorage.setItem(BKEY,JSON.stringify(_strip(old)));}catch(e){}}
 if(_n(d))delete d.cleared;d.updated=Date.now();var ok=_put(d);if(ok&&G.on){clearTimeout(G._t);G._t=setTimeout(function(){gauth(false).then(function(ok2){if(ok2)gsync();});},800);}return ok;};
try{G.on=!!G.cid&&localStorage.getItem(GKEY)==='1';}catch(e){}
gbar();if(G.on)gauth(false).then(function(ok){if(ok)gsync();});

function render(){ph();var d=get(),need={};d.h.forEach(function(h){var n=norm(h.s);if(n)need[n.mk]=1;});
 var mks=Object.keys(need);if(mks.indexOf('us')<0)mks.push('us');
 Promise.all(mks.map(loadMk)).then(function(res){gFM={};mks.forEach(function(m,i){gFM[m]=res[i];});draw(d,gFM);});
 if(mks.length&&!document.getElementById('pft').tBodies[0].rows.length)msg(['載入價格中…','Loading prices…']);}

function calcBackcastNav(d, tot, FM){
 if(!HIST.dates || HIST.dates.length < 3) return null;
 var dates = HIST.dates;
 var twdRates = HIST.closes['TWD=X'] || [];
 var liveFxUsd = fxv('USD'), hkUsd = (FXOK && FX.HKD) ? FX.HKD / FX.USD : null;
 if(liveFxUsd == null) return null;                       // no USD/TWD rate → no curve (never an invented rate)
 var rows = [];
 d.h.forEach(function(h){
  var n = norm(h.s);
  if(!n) return;
  var s = n.cands[0];
  var series = HIST.closes[s] || HIST.closes[n.key];
  if(!series){
   for(var i=0; i<n.cands.length; i++){
    if(HIST.closes[n.cands[i]]){ series = HIST.closes[n.cands[i]]; break; }
   }
  }
  rows.push({ h: h, n: h.n, series: series, sym: s, mk: n.mk });
 });
 // only draw when ≥90% of today's value has a real daily history; otherwise the "curve" is mostly today's price
 var covV = 0, allV = 0;
 rows.forEach(function(r){ var p = price(r.h, FM && FM[r.mk]), f = fxv(cur(r.mk)); if(!p || p.px == null || f == null) return;
  r.priced = true; var v = r.n * p.px * f; allV += v; if(r.series) covV += v; });
 if(allV <= 0 || covV / allV < 0.9) return null;

 var cashT = 0;
 (d.cash || []).forEach(function(c){
  var f = fxv(c.cur);
  if(f != null) cashT += c.a * f;                 // same as the live total (negative = borrowing)
 });

 var pts = [];
 for(var t=0; t<dates.length; t++){
  var dayTot = cashT;
  var dayFx = (twdRates[t] != null && twdRates[t] > 0) ? twdRates[t] : liveFxUsd;
  rows.forEach(function(r){
   if(!r.priced) return;                      // same set as today's total: a holding without a current price is left out
   var px = (r.series && r.series[t] != null) ? r.series[t] : null;
   if(px == null){
    var p = price(r.h, FM && FM[r.mk]);
    if(p && p.px != null) px = p.px;
   }
   if(px != null){
    var rate = (r.mk === 'tw') ? 1.0 : (r.mk === 'hk' ? (hkUsd != null ? dayFx * hkUsd : null) : dayFx);
    if(rate == null) return;
    dayTot += r.n * px * rate;
   }
  });
  pts.push({ d: dates[t], v: Math.round(dayTot), mode: 'backcast' });
 }

 var todayStr = new Date().toISOString().slice(0, 10);
 if(dates[dates.length - 1] !== todayStr && tot > 0){
  pts.push({ d: todayStr, v: Math.round(tot), mode: 'live' });
 }
 return pts;
}

// ---------------------------------------------------------------- Feature 4: NAV Chart & HWM Drawdown
function _mktDay(){ try{ return new Date().toLocaleDateString('en-CA', {timeZone: 'America/New_York'}); }catch(e){ return new Date().toISOString().slice(0, 10); } }
function _dms(s){ return Date.parse(s + 'T00:00:00Z'); }
function _addDays(s, n){ return new Date(_dms(s) + n * 86400000).toISOString().slice(0, 10); }
function renderNav(d, tot, FM, complete){
 var x = document.getElementById('pfnavbox');
 if(!x) return;
 x.textContent = '';
 if(!tot || tot <= 0){ x.style.display = 'none'; return; }
 x.style.display = 'block';

 // one record per US trading date (the same calendar the price history uses)
 d.nav = Array.isArray(d.nav) ? d.nav : [];
 var today = _mktDay();
 var last = d.nav[d.nav.length - 1];
 var changed = false;
 // only a complete total (every holding priced, FX available) becomes a daily record — a partial one would look like a crash
 if(complete !== false){
  if(!last || last.d !== today){ d.nav.push({d: today, v: Math.round(tot)}); changed = true; }
  else if(Math.abs((last.v || 0) - tot) >= 1){ last.v = Math.round(tot); changed = true; }
 }
 if(d.nav.length > 400){ d.nav = d.nav.slice(-400); changed = true; }
 if(changed){ _put(d); }

 var rng = (window._navRange === 30 || window._navRange === 0) ? window._navRange : 7;
 var est = calcBackcastNav(d, tot, FM) || [];
 var estBy = {}, liveBy = {};
 est.forEach(function(p){ if(p.mode === 'backcast') estBy[p.d] = p.v; });
 d.nav.forEach(function(p){ liveBy[p.d] = p.v; });
 var start = rng ? _addDays(today, -(rng - 1)) : (d.nav.length ? d.nav[0].d : today);
 var days = {};
 Object.keys(liveBy).forEach(function(k){ if(k >= start && k <= today) days[k] = 1; });
 if(rng){ Object.keys(estBy).forEach(function(k){ if(k >= start && k <= today) days[k] = 1; }); }
 var pts = Object.keys(days).sort().map(function(k){
  return liveBy[k] != null ? {d: k, v: liveBy[k], m: 'live'} : {d: k, v: estBy[k], m: 'est'};
 });
 var nLive = pts.filter(function(p){ return p.m === 'live'; }).length, nEst = pts.length - nLive;

 var head = el('div', 'pfnav-head');
 var tit = el('div', 'pfnav-title');
 tit.appendChild(L('📈 個人資產淨值走勢與回撤追蹤', 'NAV & Drawdown Tracker'));
 var pills = el('div', 'pfnav-pills');
 [[7, '7 天', '7D'], [30, '30 天', '30D'], [0, '全部紀錄（' + d.nav.length + ' 天）', 'All records (' + d.nav.length + 'd)']].forEach(function(o){
  var b = el('button', 'pfnav-pill' + (rng === o[0] ? ' on' : ''));
  b.type = 'button';
  b.appendChild(L(o[1], o[2]));
  b.addEventListener('click', function(){ window._navRange = o[0]; renderNav(d, tot, FM, complete); });
  pills.appendChild(b);
 });
 tit.appendChild(pills);
 head.appendChild(tit);

 var hwm = 0, mdd = 0, peak = 0;
 pts.forEach(function(pt){
  if(pt.v > hwm) hwm = pt.v;
  if(pt.v > peak) peak = pt.v;
  var dd = peak > 0 ? (pt.v - peak) / peak * 100 : 0;
  if(dd < mdd) mdd = dd;
 });
 var curDd = hwm > 0 ? ((tot - hwm) / hwm * 100) : 0;
 var stats = el('div', 'pfnav-stats');
 function addStat(lblZh, lblEn, valText, valCls){
  var s2 = el('div', 'pfnav-stat');
  s2.appendChild(L(lblZh + ': ', lblEn + ': '));
  s2.appendChild(el('b', valCls || '', valText));
  stats.appendChild(s2);
 }
 addStat('區間最高', 'Period high', 'NT$ ' + num(hwm, 0));
 addStat('距區間高點', 'From high', (curDd >= -0.05 ? '0.0% 🏆' : sgn(curDd, 1, true)), cl(curDd));
 addStat('區間最大回撤', 'Max drawdown', (mdd < 0 ? sgn(mdd, 1, true) : '0.0%'), 'dn');
 head.appendChild(stats);
 x.appendChild(head);

 var hint = el('div', 'pfnav-hint');
 if(complete === false){ var hw = el('div', 'pfwarn small'); hw.appendChild(L('⚠️ 今天的總資產不完整（有持股缺報價或匯率），沒有寫入每日紀錄。', '⚠️ Today\'s total is incomplete (missing price/FX); not recorded.')); x.appendChild(hw); }
 if(nEst){
  hint.appendChild(L('💡 實心點＝實際每日紀錄（' + nLive + ' 天）；空心點＝估算：假設目前持股與現金在那幾天都沒變，用當天收盤價回推，不是實際交易紀錄。',
                     'Filled = actual daily record (' + nLive + '); hollow = estimate assuming today\'s holdings were unchanged.'));
 } else if(rng){
  hint.appendChild(L('💡 目前只有實際紀錄（' + nLive + ' 天）。估算需要九成以上持股市值有每日歷史價；不足時只畫實際紀錄，每天造訪會自動累積。',
                     'Actual records only (' + nLive + 'd); estimates need daily price history for ≥90% of the holdings.'));
 } else {
  hint.appendChild(L('💡 全部實際紀錄（' + nLive + ' 天），每天造訪自動累積。', 'All actual records (' + nLive + 'd).'));
 }
 x.appendChild(hint);
 if(!pts.length){ return; }

 var wrap = el('div', 'pfnav-svg-wrap');
 wrap.style.position = 'relative';
 var W = 600, H = 130, pL = 20, pR = 20, pT = 20, pB = 26;
 var svg = svgEl('svg', { viewBox: '0 0 ' + W + ' ' + H, class: 'pfnav-svg', preserveAspectRatio: 'none' });
 var defs = svgEl('defs');
 var grad = svgEl('linearGradient', { id: 'navGrad', x1: '0', y1: '0', x2: '0', y2: '1' });
 grad.appendChild(svgEl('stop', { offset: '0%', 'stop-color': '#3a86ff', 'stop-opacity': '0.35' }));
 grad.appendChild(svgEl('stop', { offset: '100%', 'stop-color': '#3a86ff', 'stop-opacity': '0.0' }));
 defs.appendChild(grad);
 svg.appendChild(defs);

 var minV = Infinity, maxV = -Infinity;
 pts.forEach(function(p){ if(p.v < minV) minV = p.v; if(p.v > maxV) maxV = p.v; });
 if(minV === maxV){ minV *= 0.98; maxV *= 1.02; } else { var pad = (maxV - minV) * 0.15; minV -= pad; maxV += pad; }
 // x axis = real dates: the whole selected window, even where there is no point yet
 var t0 = _dms(rng ? start : pts[0].d), t1 = _dms(today);
 if(t1 <= t0) t1 = t0 + 86400000;
 function X(dstr){ return pL + (_dms(dstr) - t0) / (t1 - t0) * (W - pL - pR); }
 function Y(v){ return H - pB - ((v - minV) / (maxV - minV)) * (H - pT - pB); }
 var coords = pts.map(function(p){ return {x: X(p.d), y: Y(p.v), v: p.v, d: p.d, m: p.m}; });

 // day ticks: every day for 7D, ~6 labels otherwise
 var nDays = Math.round((t1 - t0) / 86400000);
 var step = nDays <= 8 ? 1 : Math.ceil(nDays / 6);
 for(var k = 0; k <= nDays; k += step){
  var ds = _addDays(rng ? start : pts[0].d, k), tx = X(ds);
  svg.appendChild(svgEl('line', { x1: tx, y1: pT, x2: tx, y2: H - pB, stroke: '#888', 'stroke-opacity': '0.15', 'stroke-width': '1' }));
  var tl = svgEl('text', { x: tx, y: H - 8, 'text-anchor': k === 0 ? 'start' : (k + step > nDays ? 'end' : 'middle'), fill: '#888', 'font-size': '10' });
  tl.textContent = ds.slice(5);
  svg.appendChild(tl);
 }
 var hwmY = Y(hwm);
 svg.appendChild(svgEl('line', { x1: pL, y1: hwmY, x2: W - pR, y2: hwmY, stroke: '#f59e0b', 'stroke-dasharray': '4 4', 'stroke-width': '1', opacity: '0.8' }));
 var hwmTxt = svgEl('text', { x: W - pR - 4, y: Math.max(12, hwmY - 4), 'text-anchor': 'end', fill: '#f59e0b', 'font-size': '10', 'font-weight': '600' });
 hwmTxt.textContent = (en() ? 'High NT$' : '區間高點 NT$') + num(hwm, 0);
 svg.appendChild(hwmTxt);
 if(coords.length > 1){
  var dArea = 'M ' + coords[0].x.toFixed(1) + ' ' + (H - pB);
  coords.forEach(function(c){ dArea += ' L ' + c.x.toFixed(1) + ' ' + c.y.toFixed(1); });
  dArea += ' L ' + coords[coords.length - 1].x.toFixed(1) + ' ' + (H - pB) + ' Z';
  svg.appendChild(svgEl('path', { d: dArea, fill: 'url(#navGrad)' }));
  for(var q = 1; q < coords.length; q++){                       // dashed where an estimate is involved
   var a0 = coords[q - 1], a1 = coords[q];
   var seg = { x1: a0.x.toFixed(1), y1: a0.y.toFixed(1), x2: a1.x.toFixed(1), y2: a1.y.toFixed(1), stroke: '#3a86ff', 'stroke-width': '2.2', 'stroke-linecap': 'round' };
   if(a0.m === 'est' || a1.m === 'est') seg['stroke-dasharray'] = '5 4';
   svg.appendChild(svgEl('line', seg));
  }
 }
 coords.forEach(function(c){
  svg.appendChild(svgEl('circle', { cx: c.x.toFixed(1), cy: c.y.toFixed(1), r: c.m === 'live' ? '3.6' : '3',
                                    fill: c.m === 'live' ? '#3a86ff' : 'var(--card)', stroke: '#3a86ff', 'stroke-width': '1.5' }));
 });

 var tipEl = el('div', 'pfnav-tip');
 tipEl.style.cssText = 'position:absolute;display:none;pointer-events:none;background:var(--card);border:1px solid var(--bd);border-radius:6px;padding:4px 7px;font-size:11px;white-space:nowrap;z-index:5';
 svg.addEventListener('mousemove', function(ev){
  var rect = svg.getBoundingClientRect();
  var mx = (ev.clientX - rect.left) / rect.width * W;
  var best = coords[0];
  coords.forEach(function(c){ if(Math.abs(c.x - mx) < Math.abs(best.x - mx)) best = c; });
  var dd = hwm > 0 ? (best.v - hwm) / hwm * 100 : 0;
  tipEl.textContent = best.d + (best.m === 'est' ? (en() ? ' (estimate)' : '（估算）') : (en() ? ' (actual)' : '（實際）')) +
                      '  NT$ ' + num(best.v, 0) + '  ' + (en() ? 'from high ' : '距高點 ') + (dd >= -0.05 ? '0.0%' : sgn(dd, 1, true));
  tipEl.style.display = 'block';
  var left = best.x / W * rect.width + 10;
  tipEl.style.left = Math.min(left, rect.width - 190) + 'px';
  tipEl.style.top = Math.max(0, best.y / H * rect.height - 30) + 'px';
 });
 svg.addEventListener('mouseleave', function(){ tipEl.style.display = 'none'; });
 wrap.appendChild(svg);
 wrap.appendChild(tipEl);
 x.appendChild(wrap);
}
// ---------------------------------------------------------------- Main Draw
function draw(d,FM){var tb=document.getElementById('pft').tBodies[0];tb.textContent='';var tf=document.getElementById('pft').tFoot;if(tf)tf.remove();
 var rows=[],totV=0,totDay=0,totPrev=0,totCost=0,costV=0,miss=0,dates={};
 d.h.forEach(function(h,i){var n=norm(h.s),mk=n?n.mk:'us',p=price(h,FM[mk]),c=cur(mk),fx=fxv(c),r={h:h,i:i,mk:mk,cur:c,p:p};
  if(p){r.v=h.n*p.px;r.vt=fx!=null?r.v*fx:null;var prev=p.prev>0?p.prev:((p.ch!=null)?p.px/(1+p.ch/100):null);r.day=(prev!=null&&fx!=null)?h.n*(p.px-prev)*fx:null;r.dayc=prev!=null?h.n*(p.px-prev):null;
   if(r.vt!=null)totV+=r.vt;if(r.day!=null){totDay+=r.day;totPrev+=r.vt-r.day;}if(h.c>0){r.cost=h.n*h.c;r.un=r.v-r.cost;r.ret=r.un/r.cost*100;if(fx!=null){totCost+=r.cost*fx;costV+=r.vt;}}
   if(p.asof)dates[c]=(dates[c]&&dates[c]>p.asof)?dates[c]:p.asof;}else miss++;rows.push(r);});
 rows.sort(function(a,b){return (b.vt||0)-(a.vt||0);});

 rows.forEach(function(r){var tr=document.createElement('tr'),h=r.h,p=r.p;
  function td(x,c){var t=el('td',c||'r');if(x instanceof Node)t.appendChild(x);else t.textContent=x;tr.appendChild(t);return t;}
  td((p&&p.sym)||h.s,'');td(p?(p.name||''):'','');td(num(h.n,h.n%1?2:0));
  if(p){var pxcell=td(num(p.px,2)+' '+r.cur+(p.src==='manual'?' ✎':''));if(p.source)pxcell.appendChild(el('div','small muted',p.source+' '+(p.asof||'—')));td(sgn(p.ch,2,true),'r '+cl(p.ch));td(r.dayc!=null?sgn(r.dayc,0):'—','r '+cl(r.dayc));
   td(num(r.v,0));td(r.vt!=null?num(r.vt,0):'—');td(h.c>0?num(r.cost,0):'—');td(r.un!=null?sgn(r.un,0):'—','r '+cl(r.un));td(r.ret!=null?sgn(r.ret,1,true):'—','r '+cl(r.ret));
   
   // Feature 3: Dynamic Stop & Profit Targets column
   var stopTd = td('', 'r');
   var box = el('div', 'pft-stop');
   // rule: stop distance = 2.5 × the stock's 60-day daily volatility × √10 (≈ a 2-week 2.5σ move), target = 2 × that
   var sv = symVol((p && p.sym) || h.s);
   var stopPct = sv != null ? Math.min(0.35, Math.max(0.03, 2.5 * sv / 100 * Math.sqrt(10))) : null, tgtPct = stopPct != null ? 2 * stopPct : null;
   if(stopPct == null){ box.appendChild(el('span', 'muted', '—')); }
   else if(h.c > 0){
    var cost = h.c;
    var stopPx = p.px >= cost ? Math.max(cost, p.px * (1 - stopPct)) : (cost * (1 - stopPct));
    var tgtPx = cost * (1 + tgtPct);
    if(p.px <= stopPx){
     var hit = el('span', 's-hit dn');
     hit.appendChild(L('⚠️ 觸及防守', '⚠️ Stop'));
     box.appendChild(hit);
    } else if(p.px >= tgtPx){
     var hit2 = el('span', 's-hit up');
     hit2.appendChild(L('🎯 達第一停利', '🎯 Target'));
     box.appendChild(hit2);
    }
    var stpLine = el('span', 's-stp');
    stpLine.appendChild(L('防 ' + num(stopPx, 1), 'Stp ' + num(stopPx, 1)));
    box.appendChild(stpLine);
    var tgtLine = el('span', 's-tgt');
    tgtLine.appendChild(L('利 ' + num(tgtPx, 1), 'Tgt ' + num(tgtPx, 1)));
    box.appendChild(tgtLine);
   } else {
    var stopPx2 = p.px * (1 - stopPct);
    var stpLine2 = el('span', 's-stp');
    stpLine2.appendChild(L('防 ' + num(stopPx2, 1) + ' (-' + Math.round(stopPct*100) + '%)', 'Stp ' + num(stopPx2, 1) + ' (-' + Math.round(stopPct*100) + '%)'));
    box.appendChild(stpLine2);
   }
   stopTd.appendChild(box);

   td(totV&&r.vt!=null?num(r.vt/totV*100,1)+'%':'—');}
  else{var t=td('','r pfwarn');t.colSpan=10;t.appendChild(L('找不到報價，請手動輸入價格：','No price found — enter one: '));var inp=el('input');inp.type='number';inp.step='any';inp.min='0';inp.setAttribute('aria-label','manual price');
   inp.addEventListener('change',function(){var dd=get();dd.h[r.i].p=parseFloat(inp.value)||0;put(dd);render();});t.appendChild(inp);}
  var del=el('button','pfx','✕');del.type='button';del.title=en()?'Remove':'刪除';del.addEventListener('click',function(){var dd=get();dd.h.splice(r.i,1);put(dd);render();});td(del,'');
  tb.appendChild(tr);});
 var cashT=0,cashMiss=false;(d.cash||[]).forEach(function(c){var f=fxv(c.cur);if(f==null)cashMiss=true;else cashT+=c.a*f;});var tot=totV+cashT,usd=FXOK?FX.USD:null;
 var S=document.getElementById('pfsum');S.textContent='';
 function k(zh,en_,v,sub,c,big){var x=el('div','pfk'+(big?' big':''));x.appendChild(el('div','s')).appendChild(L(zh,en_));var vv=el('div','v '+(c||''),v);x.appendChild(vv);if(sub)x.appendChild(el('div','s',sub));S.appendChild(x);}
 if(!FXOK)k('總資產（新台幣）','Total assets (TWD)','—',en()?'USD/TWD rate unavailable':'美元兌台幣匯率暫缺，無法換算','pfwarn',true);
 else k('總資產（新台幣）','Total assets (TWD)','NT$ '+num(tot,0),'≈ US$ '+num(tot/usd,0),'',true);
 k('今日損益','Today P&L','NT$ '+sgn(totDay,0),totPrev?sgn(totDay/totPrev*100,2,true):'',cl(totDay));
 k('股票市值','Stocks','NT$ '+num(totV,0),tot?num(totV/tot*100,1)+'%':'');
 k('現金','Cash','NT$ '+num(cashT,0),(d.cash||[]).map(function(c){return c.cur+' '+num(c.a,0);}).join(' · '));
 if(totCost)k('帳面損益（有填成本者）','Unrealized (with cost)','NT$ '+sgn(costV-totCost,0),sgn((costV-totCost)/totCost*100,2,true),cl(costV-totCost));
 var dl=Object.keys(dates).map(function(c){return c+' '+dates[c];}).join(' · ');
 msg(d.h.length||(d.cash||[]).length?[(miss?miss+' 檔找不到報價 · ':'')+'價格日期：'+(dl||'—')+' · 美元兌台幣 '+(FXOK?num(FX.USD,3)+'（'+(FX.asof||'日期不明')+'）':'匯率缺'),(miss?miss+' without price · ':'')+'Prices as of: '+(dl||'—')+' · USD/TWD '+(FXOK?num(FX.USD,3)+' ('+(FX.asof||'date n/a')+')':'unavailable')]
  :['尚未輸入持股：在下方新增，或用「一次貼上多筆」','No holdings yet — add some below or paste many at once']);

 renderNav(d, tot, FM, miss === 0 && !cashMiss && rows.every(function(r){ return r.vt != null; }));
 renderDx(rows, tot, totV, cashT);
 renderRules(rows, totV);
}

// ---------------------------------------------------------------- 我的規則檢查（same rules as Discord /holdings rules）
var RBK = PUB.rules || {};
function rbLook(map, sym, h){var n=norm(h.s),c=[sym].concat(n?n.cands:[]);for(var i=0;i<c.length;i++){if(map&&map[c[i]]!==undefined)return map[c[i]];}return undefined;}
function rbCheck(px, cost, w, themeW, S, Z, E, GB, C, ssi){
 var o=[];function ck(g,zh,met,txt){o.push({g:g,zh:zh,met:met,txt:txt});}
 C=C||{};var cap=+C.max_weight_pct||15,tcap=+C.max_theme_pct||30,stopL=+C.stop_loss_pct||25,lag=+C.trend_lag_pp||15,trail=+C.trailing_pct||30,
  bkx=(+C.bk_exit_pct||5)/100,bka=(+C.bk_add_max_pct||2)/100,smax=+C.add_max_ssi||60;
 var ma=S?S[0]:null,mom=S?S[1]:null,hi=S?S[2]:null,rel=S?S[3]:null;
 if(!Z)ck('exit','論點：財務體質',null,'不在危機雷達的掃描名單（或非美國公司）');
 else ck('exit','論點：財務體質',Z[0]==='alert'||(Z[1]!=null&&Z[1]>=bkx),'危機雷達'+({alert:'紅燈',watch:'黃燈',ok:'無燈號'}[Z[0]]||'—')+(Z[1]!=null?'，破產機率 '+(Z[1]*100).toFixed(1)+'%':''));
 if(!E&&!GB)ck('exit','論點：最近財報',null,'沒有可比較的財報數字');
 else ck('exit','論點：最近財報',!!((E&&E[2]<0)||GB),(E?'EPS '+E[0]+' vs 預期 '+E[1]+'（'+(E[2]>=0?'+':'')+(+E[2]).toFixed(1)+'%）':'EPS 無資料')+(GB?'；營收低於上次指引':''));
 if(px>0&&cost>0){var dd=(px/cost-1)*100;ck('exit','停損：低於成本 '+stopL+'%',dd<=-stopL,'相對成本 '+(dd>=0?'+':'')+dd.toFixed(1)+'%');}
 else ck('exit','停損：低於成本 '+stopL+'%',null,'沒有填成本');
 if(ma!=null&&mom!=null&&rel!=null)ck('exit','趨勢破壞（三項同時）',px<ma&&mom<0&&rel<=-lag,(px<ma?'低於':'高於')+' 200 日線 '+ma.toFixed(2)+'｜12-1 動能 '+(mom>=0?'+':'')+Math.round(mom)+'%｜6 個月相對大盤 '+(rel>=0?'+':'')+Math.round(rel)+' 個百分點');
 else ck('exit','趨勢破壞（三項同時）',null,'歷史股價不足一年或不在本站資料');
 if(hi){var tr=(px/hi-1)*100;ck('exit','移動停損：距 52 週高點 '+trail+'%',tr<=-trail,'距高點 '+Math.round(tr)+'%');}
 ck('trim','單一持股 > '+cap+'%',w>cap,'佔比 '+w.toFixed(1)+'%');
 ck('trim','同主題 > '+tcap+'%',themeW>tcap,'主題「'+(S?S[4]:'其他')+'」合計 '+themeW.toFixed(1)+'%');
 ck('trim','風險貢獻上限',null,'網站版不計算（Discord /holdings rules 有）');
 ck('add','部位還在上限內',w<cap,'佔比 '+w.toFixed(1)+'%（上限 '+cap+'%）');
 ck('add','站上 200 日線',ma==null?null:px>ma,ma==null?'—':px.toFixed(2)+' vs '+ma.toFixed(2));
 ck('add','12-1 動能為正',mom==null?null:mom>0,mom==null?'—':(mom>=0?'+':'')+Math.round(mom)+'%');
 if(Z)ck('add','財務體質無警訊',Z[0]==='ok'&&(Z[1]==null||Z[1]<bka),'危機雷達'+(Z[0]==='ok'?'無燈號':'有燈號')+(Z[1]!=null?'，破產機率 '+(Z[1]*100).toFixed(1)+'%':''));
 else ck('add','財務體質無警訊',null,'不在危機雷達的掃描名單');
 ck('add','最近財報不低於預期',E?E[2]>=0:null,E?'EPS 驚喜 '+(E[2]>=0?'+':'')+(+E[2]).toFixed(1)+'%':'—');
 ck('add','壓力指數 < '+smax,ssi==null?null:ssi<smax,ssi==null?'—':'壓力指數 '+Math.round(ssi));
 return o;}
function rbSum(ch){var ex=ch.filter(function(c){return c.g==='exit';}),tr=ch.filter(function(c){return c.g==='trim';}),ad=ch.filter(function(c){return c.g==='add'&&c.met!==null;});
 var nx=ex.filter(function(c){return c.met===true;}).length,nt=tr.filter(function(c){return c.met===true;}).length,na=ad.filter(function(c){return c.met===true;}).length;
 var all=ad.length>=4&&na===ad.length,st=nx>=2?'exit2':nx===1?'exit1':nt?'trim':all?'add':'hold';
 var zh={exit2:'出場檢查：'+nx+' 項觸發',exit1:'出場檢查：1 項觸發',trim:'減碼檢查：'+nt+' 項觸發',add:'加碼條件：全部成立',hold:'沒有規則觸發'}[st];
 return {st:st,zh:zh,nx:nx,nex:ex.length,nt:nt,ntr:tr.length,na:na,nad:ad.length};}
function renderRules(rows, totV){
 var x=document.getElementById('pfrules');if(!x)return;x.textContent='';
 var live=rows.filter(function(r){return r.p&&r.vt!=null;});
 if(!live.length||!totV){x.style.display='none';return;}
 x.style.display='block';
 var hd=el('h3');hd.appendChild(L('我的規則檢查','My rule check'));x.appendChild(hd);
 var sub=el('p','small muted');sub.appendChild(L('用華爾街常用的進出場紀律（論點停損、停損、趨勢、移動停損、部位上限）當作你的規則，逐檔檢查哪些條件成立；門檻和 Discord「/holdings rules」相同（settings.yaml 的 rulebook）。只在你的瀏覽器裡計算，不會上傳。這是規則檢查，不是買賣指令。',
  'Wall Street entry / exit discipline as your own rules, checked per holding in your browser only. A rule check, not a buy / sell instruction.'));x.appendChild(sub);
 var themeW={},items=[];
 live.forEach(function(r){var S=rbLook(RBK.sym,(r.p&&r.p.sym)||r.h.s,r.h);var th=S?S[4]:'其他';r._w=r.vt/totV*100;r._S=S;themeW[th]=(themeW[th]||0)+r._w;});
 live.forEach(function(r){var sym=(r.p&&r.p.sym)||r.h.s,S=r._S;
  var ch=rbCheck(r.p.px,r.h.c>0?r.h.c:0,r._w,themeW[S?S[4]:'其他']||0,S,rbLook(RBK.dz,sym,r.h),rbLook(RBK.surp,sym,r.h),rbLook(RBK.gb,sym,r.h),RBK.cfg,RBK.ssi);
  items.push({sym:sym,name:(r.p&&r.p.name)||'',w:r._w,ch:ch,s:rbSum(ch)});});
 var ord={exit2:0,exit1:1,trim:2,add:3,hold:4},ico={exit2:'🔴',exit1:'🟠',trim:'🟡',add:'🟢',hold:'⚪'},col={exit2:'var(--dn)',exit1:'#ec835a',trim:'var(--warn)',add:'var(--up)',hold:'var(--mu)'};
 items.sort(function(a,b){return ord[a.s.st]-ord[b.s.st]||b.w-a.w;});
 items.forEach(function(it){var d=document.createElement('details');d.className='pfrl';var sm=document.createElement('summary');
  sm.appendChild(el('b','',ico[it.s.st]+' '+it.sym));sm.appendChild(el('span','small muted',it.name+'｜佔比 '+it.w.toFixed(1)+'%'));
  var tg=el('span','tag',it.s.zh);tg.style.color=col[it.s.st];sm.appendChild(tg);
  sm.appendChild(el('span','small muted','出場 '+it.s.nx+'/'+it.s.nex+'・減碼 '+it.s.nt+'/'+it.s.ntr+'・加碼 '+it.s.na+'/'+it.s.nad));d.appendChild(sm);
  [['exit','出場檢查（任一項觸發都值得重新檢視論點）'],['trim','減碼檢查（部位大小）'],['add','加碼條件（全部成立才算）']].forEach(function(g){
   d.appendChild(el('div','small',g[1]));var ul=el('ul');
   it.ch.filter(function(c){return c.g===g[0];}).forEach(function(c){var li=el('li',c.met===true?'met':(c.met===null?'unk':''),(c.met===true?(g[0]==='add'?'✅ ':'⚠️ '):(c.met===null?'－ ':'○ '))+c.zh+'：'+c.txt);ul.appendChild(li);});
   d.appendChild(ul);});
  x.appendChild(d);});
 var ft=el('p','small muted');ft.appendChild(L('自問：如果今天手上是現金，會用現在的價格買這麼多嗎？會 → 續抱；不會或不會買這麼多 → 考慮減碼；會而且想買更多 → 再看加碼條件。「－」＝沒有資料，不算成立。',
  'Ask: with cash today, would I buy this much at this price? "－" = no data, never counted as met.'));x.appendChild(ft);}

// ---------------------------------------------------------------- Diagnostics
function renderDx(rows, tot, totV, cashT){
 var x = document.getElementById('pfdx');
 if(!x) return;
 x.textContent = '';
 if(!rows.length && !cashT){
  x.style.display = 'none';
  renderCrisis([], 0, 0, 0);
  renderWhatif([], 0, 0, 0, 0, {});
  renderEarnings([], 0);
  return;
 }
 x.style.display = 'block';
 if(!tot) tot = 1;

 var secW = {}, pfBeta = 0, covB = 0;
 SECS.forEach(function(s){ secW[s.k] = 0; });
 secW.other = 0;
 secW.cash = cashT / tot;
 rows.forEach(function(r){
  var sym = ((r.p && r.p.sym) || r.h.s || '').toUpperCase();
  var key = sym.replace(/\.(TW|TWO)$/,'');
  var found = null;
  for(var i=0; i<SECS.length; i++){
   if(SECS[i].syms.indexOf(key) >= 0 || SECS[i].syms.indexOf(sym) >= 0){ found = SECS[i]; break; }
  }
  var w = (r.vt || 0) / tot;
  if(found){ secW[found.k] += w; } else { secW.other += w; }
  var b = symBeta(sym); if(b == null && found) b = found.b;
  if(b != null){ pfBeta += w * b; covB += w; }
 });
 covB += secW.cash;                                        // cash: beta 0, known
 pfBeta = covB >= 0.5 ? pfBeta / covB : null;             // beta of the part we can measure; too little → none
 var top1 = rows[0] ? ((rows[0].vt || 0) / tot * 100) : 0;
 var top1Sym = rows[0] ? ((rows[0].p && rows[0].p.sym) || rows[0].h.s) : '—';
 var top3 = 0;
 for(var i=0; i<Math.min(3, rows.length); i++){ top3 += ((rows[i].vt || 0) / tot * 100); }
 var cashPct = cashT / tot * 100;
 var semiTechPct = ((secW.semi || 0) + (secW.tech || 0)) * 100;

 var hd = el('h3', '');
 hd.appendChild(L('持倉健康度診斷與再平衡建議', 'Portfolio Diagnostics & Rebalancing'));
 x.appendChild(hd);

 var grid = el('div', 'pfdx-grid');

 var k1 = el('div', 'pfdx-k');
 k1.appendChild(el('div', 'lbl')).appendChild(L('組合風險屬性', 'Risk Profile'));
 var isAgg = (pfBeta != null && pfBeta >= 1.35) || semiTechPct >= 50;
 var isBal = cashPct >= 15 && top1 <= 25 && pfBeta != null && pfBeta < 1.15;
 var val1 = k1.appendChild(el('div', 'val ' + (isAgg ? 'dn' : (isBal ? 'up' : 'warn'))));
 val1.appendChild(isAgg ? L('高波動進攻型', 'Aggressive Growth') : (isBal ? L('穩健平衡型', 'Balanced Defensive') : L('成長型', 'Moderate Growth')));
 k1.appendChild(el('div', 'sub')).appendChild(L('預估整體 Beta: ' + (pfBeta != null ? num(pfBeta, 2) + '（涵蓋 ' + num(covB * 100, 0) + '% 資產）' : '—（可量測的持股不足一半）'),
                                                'Estimated Beta: ' + (pfBeta != null ? num(pfBeta, 2) + ' (covers ' + num(covB * 100, 0) + '%)' : '— (too few measurable holdings)')));
 grid.appendChild(k1);

 var k2 = el('div', 'pfdx-k');
 k2.appendChild(el('div', 'lbl')).appendChild(L('壓力情境推估', 'Stress Scenario'));
 var val2 = k2.appendChild(el('div', 'val dn', pfBeta != null ? '-' + num(pfBeta * 5, 1) + '%' : '—'));
 k2.appendChild(el('div', 'sub')).appendChild(L('大盤若跌 5% 預估回撤', 'Expected drop if SPX -5%'));
 grid.appendChild(k2);

 var k3 = el('div', 'pfdx-k');
 k3.appendChild(el('div', 'lbl')).appendChild(L('前三大持股集中度', 'Top 3 Concentration'));
 var val3 = k3.appendChild(el('div', 'val ' + (top3 >= 60 ? 'dn' : (top3 >= 45 ? 'warn' : 'up')), num(top3, 1) + '%'));
 k3.appendChild(el('div', 'sub')).appendChild(L('最大單一: ' + top1Sym + ' (' + num(top1, 1) + '%)', 'Top holding: ' + top1Sym + ' (' + num(top1, 1) + '%)'));
 grid.appendChild(k3);

 var k4 = el('div', 'pfdx-k');
 k4.appendChild(el('div', 'lbl')).appendChild(L('防守現金水位', 'Cash Buffer'));
 var val4 = k4.appendChild(el('div', 'val ' + (cashPct < 5 ? 'dn' : (cashPct < 15 ? 'warn' : 'up')), num(cashPct, 1) + '%'));
 k4.appendChild(el('div', 'sub')).appendChild(L(cashPct < 5 ? '無防守緩衝 ⚠️' : (cashPct < 15 ? '緩衝適中' : '充裕'), cashPct < 5 ? 'Low liquidity' : 'Adequate'));
 grid.appendChild(k4);
 x.appendChild(grid);

 var secBox = el('div', 'pfdx-sec');
 secBox.appendChild(el('div', 'lbl')).appendChild(L('產業族群曝險分布', 'Sector Exposure Breakdown'));
 var bar = el('div', 'pfdx-bar');
 var tags = el('div', 'pfdx-tags');
 function addSeg(pct, c, zh, en_){
  if(pct < 0.005) return;
  var seg = el('div', 'pfdx-bar-seg');
  seg.style.width = (pct * 100) + '%';
  seg.style.background = c;
  bar.appendChild(seg);
  var tag = el('span', 'pfdx-tag');
  var dot = el('span', 'dot');
  dot.style.background = c;
  tag.appendChild(dot);
  tag.appendChild(L(zh + ' ' + num(pct * 100, 1) + '%', en_ + ' ' + num(pct * 100, 1) + '%'));
  tags.appendChild(tag);
 }
 SECS.forEach(function(s){ addSeg(secW[s.k], s.c, s.zh, s.en); });
 addSeg(secW.other, '#9e9e9e', '其他標的', 'Others');
 addSeg(secW.cash, '#4caf50', '現金', 'Cash');
 secBox.appendChild(bar);
 secBox.appendChild(tags);
 x.appendChild(secBox);

 var list = el('div', 'pfdx-items');
 function addItem(cls, ico, zh, en_){
  var item = el('div', 'pfdx-item ' + cls);
  item.appendChild(el('span', 'ico', ico));
  var desc = el('div', 'desc');
  desc.appendChild(L(zh, en_));
  item.appendChild(desc);
  list.appendChild(item);
 }
 if(top1 > 25){
  addItem('bad', '🔴',
   '【單一持股集中】' + top1Sym + ' 佔總資產 ' + num(top1, 1) + '%，高於本頁的 25% 參考線（固定規則，非統計）。這檔股價每變動 10%，總資產約變動 ' + num(top1 / 10, 1) + '%。',
   '[Concentration] ' + top1Sym + ' is ' + num(top1, 1) + '% of assets, above this page\'s 25% reference line. A 10% move in it moves the total by ~' + num(top1 / 10, 1) + '%.');
 }
 if(semiTechPct > 50){
  addItem('bad', '🔴',
   '【產業集中】半導體與科技合計 ' + num(semiTechPct, 1) + '%，高於本頁的 50% 參考線。同一族群的股票通常同向漲跌。',
   '[Sector concentration] Semis + tech = ' + num(semiTechPct, 1) + '%, above this page\'s 50% reference line; same-sector stocks tend to move together.');
 }
 if(cashPct < 5){
  addItem('warn', '🟡',
   '【現金比例】現金 ' + num(cashPct, 1) + '%，低於本頁的 5% 參考線。',
   '[Cash] Cash is ' + num(cashPct, 1) + '%, below this page\'s 5% reference line.');
 }
 var deepLoss = rows.filter(function(r){ return r.ret != null && r.ret <= -15; });
 if(deepLoss.length){
  var names = deepLoss.map(function(r){ return ((r.p && r.p.sym) || r.h.s) + ' (' + sgn(r.ret, 1, true) + ')'; }).join('、');
  addItem('warn', '🟠',
   '【帳面虧損超過 15%】' + names + '。',
   '[Unrealized loss over 15%] ' + names + '.');
 }
 addItem('act', 'ℹ️', '以上是依固定參考線的描述，不是買賣建議；要怎麼調整由你自己決定，或與持牌理財顧問討論。下方 What-if 只做試算，不會動到帳戶。',
         'Descriptions against fixed reference lines, not advice. The What-if below is a calculation only.');
 x.appendChild(list);

 renderCrisis(rows, tot, totV, cashT);
 renderWhatif(rows, tot, totV, cashT, pfBeta, secW);
 renderEarnings(rows, tot);
}

// ---------------------------------------------------------------- Feature 1: Crisis Replay Simulator
var curCrisisId = 'yen2024', CS = PUB.crisis || {};
var CRISES = [
 {
  id: 'yen2024',
  zh: '2024.08.05 日圓套息平倉股災', en: '2024 Yen Carry Unwind',
  descZh: '日銀 7 月底升息、日圓急升，引發日圓套利交易平倉；8 月 5 日日經單日重挫逾 12%，半導體與高估值科技跌幅最深。',
  descEn: 'BOJ hike and a sharp yen rally triggered a carry-trade unwind; the Nikkei fell over 12% on Aug 5.',
  shocks: (CS.yen2024 || {}).shocks
 },
 {
  id: 'fed2022',
  zh: '2022 激進升息科技熊市', en: '2022 Fed Tech Bear',
  descZh: '美國 CPI 年增率 2022 年 6 月達 9.1%，聯準會 2022 年全年升息 425bp。跌幅統計期間為 2022-01-03 至 2022-10-12。',
  descEn: 'US CPI peaked at 9.1% (Jun-2022); the Fed hiked 425bp during 2022. Window: 2022-01-03 to 2022-10-12.',
  shocks: (CS.fed2022 || {}).shocks
 },
 {
  id: 'covid2020',
  zh: '2020 疫情流動性熔斷', en: '2020 COVID Liquidity Crash',
  descZh: '美股 2020 年 3 月 9、12、16、18 日四度觸發熔斷；3 月中黃金與長債也一度和股票同步下跌。',
  descEn: 'US circuit breakers tripped on Mar 9, 12, 16 and 18, 2020; gold and long bonds also fell with stocks in mid-March.',
  shocks: (CS.covid2020 || {}).shocks
 },
 {
  id: 'gfc2008',
  zh: '2008 次貸金融海嘯', en: '2008 Global Financial Crisis',
  descZh: '2008 年 9 月雷曼倒閉後全球信用凍結；標普從 2007-10 高點跌到 2009-03 低點，約 17 個月。',
  descEn: 'Credit froze after Lehman (Sep-2008); the S&P fell from its Oct-2007 high to the Mar-2009 low, about 17 months.',
  shocks: (CS.gfc2008 || {}).shocks
 }
].filter(function(c){ return c.shocks && c.shocks.other != null; });   // measured from price history; no data → no scenario
if(CRISES.length && !CRISES.some(function(c){ return c.id === curCrisisId; })) curCrisisId = CRISES[0].id;

function renderCrisis(rows, tot, totV, cashT){
 var x = document.getElementById('pfcrisis');
 if(!x) return;
 x.textContent = '';
 if((!rows.length && !cashT) || !CRISES.length){ x.style.display = 'none'; return; }
 x.style.display = 'block';

 var hd = el('h3', '');
 hd.appendChild(L('🌪️ 歷史危機持倉壓力測試重播器', 'Crisis Replay Simulator'));
 x.appendChild(hd);
 var srcNote = el('p', 'muted small');
 srcNote.appendChild(L('各類股跌幅＝該危機期間代表指數／ETF 的實際最大跌幅（半導體 ^SOX、科技 XLK、前沿 ARKK／能源 XLE、金融 XLF、防禦 XLP、其他 ^GSPC），用本站歷史收盤價計算；沒有資料的類別以大盤跌幅代替。',
  'Category falls = actual peak-to-trough of proxy indices/ETFs in each window, from price history; missing categories use the S&P 500.'));
 x.appendChild(srcNote);
 var sub = el('p', 'muted small');
 sub.appendChild(L('點選經典股災情境，以當前持股精準回放若歷史重演時的資產蒸發金額與各標的回撤衝擊',
                  'Simulate how your current portfolio would have performed during historical market crashes.'));
 x.appendChild(sub);

 var btns = el('div', 'pfcrisis-btns');
 CRISES.forEach(function(c){
  var b = el('button', 'pfcrisis-btn' + (c.id === curCrisisId ? ' active' : ''));
  b.type = 'button';
  b.appendChild(L(c.zh, c.en));
  b.addEventListener('click', function(){
   curCrisisId = c.id;
   renderCrisis(rows, tot, totV, cashT);
  });
  btns.appendChild(b);
 });
 x.appendChild(btns);

 var crisis = CRISES.find(function(c){ return c.id === curCrisisId; }) || CRISES[0];
 var descBox = el('div', 'muted small');
 descBox.style.marginBottom = '8px';
 descBox.appendChild(L('📜 情境背景：' + crisis.descZh, 'Scenario Context: ' + crisis.descEn));
 x.appendChild(descBox);

 var totLoss = 0;
 var holdingLosses = [];
 rows.forEach(function(r){
  var sym = ((r.p && r.p.sym) || r.h.s || '').toUpperCase();
  var key = sym.replace(/\.(TW|TWO)$/,'');
  var found = null;
  for(var i=0; i<SECS.length; i++){
   if(SECS[i].syms.indexOf(key) >= 0 || SECS[i].syms.indexOf(sym) >= 0){ found = SECS[i]; break; }
  }
  var cat = found ? found.k : 'other';
  var rate = crisis.shocks[cat] != null ? crisis.shocks[cat] : crisis.shocks.other;
  var loss = (r.vt || 0) * rate;
  totLoss += loss;
  holdingLosses.push({ sym: sym, vt: r.vt || 0, rate: rate, loss: loss, name: (r.p && r.p.name) || sym });
 });

 holdingLosses.sort(function(a, b){ return b.loss - a.loss; });
 var dropPct = tot > 0 ? (totLoss / tot * 100) : 0;
 var postNAV = Math.max(0, tot - totLoss);
 var cashCover = (cashT > 0 && totLoss > 0) ? Math.min(100, cashT / totLoss * 100) : 0;

 var res = el('div', 'pfcrisis-result');
 var impGrid = el('div', 'pfcrisis-impact');

 function addImp(lblZh, lblEn, val, subZh, subEn, cls){
  var d = el('div', 'pfdx-k');
  d.appendChild(el('div', 'lbl')).appendChild(L(lblZh, lblEn));
  d.appendChild(el('div', 'val ' + (cls || ''), val));
  if(subZh) d.appendChild(el('div', 'sub')).appendChild(L(subZh, subEn));
  impGrid.appendChild(d);
 }
 addImp('預估資產蒸發金額', 'Simulated Drawdown', '-NT$ ' + num(totLoss, 0), '相當於總資產 -' + num(dropPct, 1) + '%', 'NAV drop -' + num(dropPct, 1) + '%', 'dn');
 addImp('情境壓力後淨值', 'Post-Crisis NAV', 'NT$ ' + num(postNAV, 0), '跌後保留率 ' + num(100 - dropPct, 1) + '%', 'Capital preserved ' + num(100 - dropPct, 1) + '%', '');
 addImp('防守現金吸收度', 'Cash Buffer Absorption', (cashCover > 0 ? (num(cashCover, 1) + '%') : '0.0%'),
        (cashCover >= 20 ? '現金有效緩衝部分跌勢' : '⚠️ 現金防守墊過低'), (cashCover >= 20 ? 'Cash partially buffers loss' : 'Low cash cushion'),
        (cashCover >= 20 ? 'up' : 'dn'));
 res.appendChild(impGrid);

 var barsTitle = el('div', 'lbl');
 barsTitle.style.marginBottom = '6px';
 barsTitle.style.fontSize = '12px';
 barsTitle.appendChild(L('個別持股虧損衝擊排行（前 5 大）：', 'Top 5 Holding Drawdown Breakdown:'));
 res.appendChild(barsTitle);

 var maxLoss = holdingLosses[0] ? holdingLosses[0].loss : 1;
 var barList = el('div', 'pfcrisis-bars');
 for(var i=0; i<Math.min(5, holdingLosses.length); i++){
  var item = holdingLosses[i];
  var row = el('div', 'pfcrisis-bar-row');
  var lbl = el('div', 'pfcrisis-bar-lbl', item.sym);
  row.appendChild(lbl);
  var track = el('div', 'pfcrisis-bar-track');
  var fill = el('div', 'pfcrisis-bar-fill');
  fill.style.width = Math.max(3, (item.loss / (maxLoss || 1) * 100)) + '%';
  track.appendChild(fill);
  row.appendChild(track);
  var val = el('div', 'pfcrisis-bar-val dn', '-NT$ ' + num(item.loss, 0) + ' (-' + num(item.rate * 100, 1) + '%)');
  row.appendChild(val);
  barList.appendChild(row);
 }
 res.appendChild(barList);

 var tip = el('div', 'pfdx-item act');
 tip.style.marginTop = '10px';
 tip.appendChild(el('span', 'ico', '💡'));
 var tipDesc = el('div', 'desc');
 var mult = crisis.shocks.other ? dropPct / (crisis.shocks.other * 100) : null;
 tipDesc.appendChild(L(mult == null ? '這個情境沒有大盤跌幅可比較。' :
   '此情境下估計跌幅是大盤（標普 ' + num(crisis.shocks.other * 100, 1) + '%）的 ' + num(mult, 1) + ' 倍' +
   (mult > 1.1 ? '，主要因為下方跌幅較大的類別占比較高。' : (mult < 0.9 ? '，比大盤溫和。' : '，和大盤差不多。')) + '各類別跌幅是當時代表指數的實際最大跌幅。',
   mult == null ? 'No market drop to compare.' : 'Estimated drop is ' + num(mult, 1) + 'x the S&P\'s in this scenario.'));
 tip.appendChild(tipDesc);
 res.appendChild(tip);

 x.appendChild(res);
}

// ---------------------------------------------------------------- Feature 2: What-if Rebalancing Sandbox
var wiState = { trimPct: 50, sym: '', target: 'cash' };

function renderWhatif(rows, tot, totV, cashT, pfBeta, secW){
 var x = document.getElementById('pfwhatif');
 if(!x) return;
 x.textContent = '';
 if(!rows.length){ x.style.display = 'none'; return; }
 x.style.display = 'block';

 if(!wiState.sym && rows[0]){
  wiState.sym = ((rows[0].p && rows[0].p.sym) || rows[0].h.s || '').toUpperCase();
 }

 var hd = el('h3', '');
 hd.appendChild(L('🧪 「What-if」虛擬調倉即時模擬器', 'What-if Rebalancing Sandbox'));
 x.appendChild(hd);
 var sub = el('p', 'muted small');
 sub.appendChild(L('模擬減碼特定持股並轉入現金、公債或大盤 ETF，即時預覽 Beta 降幅、科技集中度改善與少虧金額',
                  'Simulate trimming holdings and reallocating into cash, bonds, or index ETFs.'));
 x.appendChild(sub);

 var ctrls = el('div', 'pfwhatif-ctrls');

 ctrls.appendChild(L('欲減碼：', 'Trim: '));
 var selStock = el('select', '');
 rows.forEach(function(r){
  var s = ((r.p && r.p.sym) || r.h.s || '').toUpperCase();
  var opt = document.createElement('option');
  opt.value = s;
  opt.textContent = s + ' (' + num(r.vt / tot * 100, 1) + '%, NT$' + num(r.vt, 0) + ')';
  if(s === wiState.sym) opt.selected = true;
  selStock.appendChild(opt);
 });
 selStock.addEventListener('change', function(){
  wiState.sym = selStock.value;
  renderWhatif(rows, tot, totV, cashT, pfBeta, secW);
 });
 ctrls.appendChild(selStock);

 ctrls.appendChild(L('幅度：', 'Pct: '));
 var pctsBox = el('div', 'pfwhatif-pcts');
 [25, 50, 75, 100].forEach(function(p){
  var b = el('button', 'pfwhatif-pbtn' + (wiState.trimPct === p ? ' active' : ''));
  b.type = 'button';
  b.textContent = p === 100 ? (en() ? '100% (All)' : '100% 全結') : (p + '%');
  b.addEventListener('click', function(){
   wiState.trimPct = p;
   renderWhatif(rows, tot, totV, cashT, pfBeta, secW);
  });
  pctsBox.appendChild(b);
 });
 ctrls.appendChild(pctsBox);

 ctrls.appendChild(L('轉入：', 'Into: '));
 var selTgt = el('select', '');
 var TGTS = [
  { k: 'cash', b: 0.0, zh: '💵 現金防守墊 (Beta 0.0)', en: '💵 Cash Buffer (Beta 0.0)' },
  { k: 'spy', b: 1.0, zh: '📈 標普 500 (SPY - Beta 1.0)', en: '📈 S&P 500 (SPY - Beta 1.0)' },
  { k: 'tlt', b: symBeta('TLT') != null ? symBeta('TLT') : BETA('tlt'), zh: '🛡️ 美國長天期公債 (TLT - Beta ' + num(symBeta('TLT') != null ? symBeta('TLT') : BETA('tlt'), 2) + ')', en: '🛡️ 20+ Y Treasuries (TLT - Beta ' + num(symBeta('TLT') != null ? symBeta('TLT') : BETA('tlt'), 2) + ')' },
  { k: 'tw50', b: symBeta('0050') != null ? symBeta('0050') : BETA('tw50'), zh: '🇹🇼 元大台灣 50 (0050 - Beta ' + num(symBeta('0050') != null ? symBeta('0050') : BETA('tw50'), 2) + (symBeta('0050') != null ? '' : '，以加權指數代理') + ')', en: '🇹🇼 Taiwan 50 (0050 - Beta ' + num(symBeta('0050') != null ? symBeta('0050') : BETA('tw50'), 2) + ')' }
 ];
 TGTS.forEach(function(t){
  var opt = document.createElement('option');
  opt.value = t.k;
  opt.textContent = en() ? t.en : t.zh;
  if(t.k === wiState.target) opt.selected = true;
  selTgt.appendChild(opt);
 });
 selTgt.addEventListener('change', function(){
  wiState.target = selTgt.value;
  renderWhatif(rows, tot, totV, cashT, pfBeta, secW);
 });
 ctrls.appendChild(selTgt);
 x.appendChild(ctrls);

 var selRow = rows.find(function(r){ return (((r.p && r.p.sym) || r.h.s || '').toUpperCase()) === wiState.sym; }) || rows[0];
 var trimRatio = wiState.trimPct / 100;
 var trimTwd = (selRow.vt || 0) * trimRatio;
 var selSym = ((selRow.p && selRow.p.sym) || selRow.h.s || '').toUpperCase();
 var selKey = selSym.replace(/\.(TW|TWO)$/,'');
 var found = null;
 for(var i=0; i<SECS.length; i++){
  if(SECS[i].syms.indexOf(selKey) >= 0 || SECS[i].syms.indexOf(selSym) >= 0){ found = SECS[i]; break; }
 }
 var stockBeta = symBeta(selSym); if(stockBeta == null && found) stockBeta = found.b;
 var tgtObj = TGTS.find(function(t){ return t.k === wiState.target; }) || TGTS[0];
 var targetBeta = tgtObj.b;

 var weightShift = tot > 0 ? (trimTwd / tot) : 0;
 var curBeta = pfBeta;
 var betaOk = curBeta != null && stockBeta != null && targetBeta != null;
 var newBeta = betaOk ? Math.max(0, curBeta - weightShift * stockBeta + weightShift * targetBeta) : null;
 var betaDiff = betaOk ? newBeta - curBeta : 0;

 var curTechSemi = ((secW.semi || 0) + (secW.tech || 0)) * 100;
 var isTechSemi = found && (found.k === 'semi' || found.k === 'tech');
 var newTechSemi = isTechSemi ? Math.max(0, curTechSemi - weightShift * 100) : curTechSemi;

 var curDrop5 = betaOk ? curBeta * 5 : null;
 var newDrop5 = betaOk ? newBeta * 5 : null;
 var savedLossTwd = betaOk ? Math.max(0, (curDrop5 - newDrop5) / 100 * tot) : 0;

 var comp = el('div', 'pfwhatif-comp');

 function addCompCard(lblZh, lblEn, oldV, newV, diffText, diffCls){
  var c = el('div', 'pfwhatif-card');
  c.appendChild(el('div', 'lbl')).appendChild(L(lblZh, lblEn));
  var vals = el('div', 'vals');
  vals.appendChild(el('span', 'muted', oldV));
  vals.appendChild(el('span', '', ' ➔ '));
  vals.appendChild(el('span', '', newV));
  c.appendChild(vals);
  if(diffText) c.appendChild(el('div', 'chg ' + (diffCls || ''), diffText));
  comp.appendChild(c);
 }

 if(!betaOk){ var nb = el('p', 'small muted'); nb.appendChild(L('缺少可量測的 Beta（這檔、目標或整體持股），Beta 與回撤試算顯示為 —。', 'Beta unavailable for this trade; Beta-based figures show —.')); x.appendChild(nb); }
 addCompCard('整體投資組合 Beta', 'Portfolio Beta', num(curBeta, 2), num(newBeta, 2),
             (betaDiff < 0 ? '🟢 降 ' + num(Math.abs(betaDiff), 2) + ' (波動減 ' + num(Math.abs(betaDiff) / (curBeta || 1) * 100, 0) + '%)' : ''), 'up');
 addCompCard('科技與半導體集中度', 'Tech & Semi Exposure', num(curTechSemi, 1) + '%', num(newTechSemi, 1) + '%',
             (newTechSemi < curTechSemi ? '🟢 降 ' + num(curTechSemi - newTechSemi, 1) + '%' : '無變更'), 'up');
 addCompCard('大盤跌 5% 預估回撤', 'Drop if SPX -5%', curDrop5 != null ? '-' + num(curDrop5, 1) + '%' : '—', newDrop5 != null ? '-' + num(newDrop5, 1) + '%' : '—',
             (savedLossTwd > 0 ? '🛡️ 少虧 NT$ ' + num(savedLossTwd, 0) : ''), 'up');
 addCompCard('釋出／轉移資金', 'Reallocated Capital', 'NT$ ' + num(trimTwd, 0), num(weightShift * 100, 1) + '%',
             '佔總資產比率', '');

 x.appendChild(comp);

 var actRow = el('div', 'pfrow');
 actRow.style.marginTop = '10px';
 var applyBtn = el('button', 'btn g');
 applyBtn.type = 'button';
 applyBtn.appendChild(L('一鍵套用調倉至持股', 'Apply Rebalancing to My Holdings'));
 applyBtn.addEventListener('click', function(){
  var cfmMsg = en()
   ? 'Apply rebalancing? Trim ' + selSym + ' by ' + wiState.trimPct + '% and move NT$' + num(trimTwd, 0) + ' to ' + tgtObj.k + '?'
   : '確定要套用調倉嗎？將 ' + selSym + ' 減碼 ' + wiState.trimPct + '%，並將資金 NT$ ' + num(trimTwd, 0) + ' 轉至 ' + (en()?tgtObj.en:tgtObj.zh) + '。';
  if(!confirm(cfmMsg)) return;

  var d = get();
  var idx = d.h.findIndex(function(h){ return (norm(h.s) && norm(h.s).key) === norm(selSym).key; });
  if(idx < 0) return;
  var origN = d.h[idx].n;
  var cutN = origN * trimRatio;
  var remainN = origN - cutN;
  if(remainN <= 0.0001){ d.h.splice(idx, 1); }
  else { d.h[idx].n = Math.round(remainN * 1000) / 1000; }

  if(tgtObj.k === 'cash'){
   d.cash = d.cash || [];
   var curC = d.cash.find(function(c){ return c.cur === 'TWD'; });
   if(curC){ curC.a += Math.round(trimTwd); }
   else { d.cash.push({ cur: 'TWD', a: Math.round(trimTwd) }); }
  } else {
   var mapTicker = { spy: 'SPY', tlt: 'TLT', tw50: '0050' };
   var addSym = mapTicker[tgtObj.k] || 'SPY';
   var tgtP = price({ s: addSym, p: 0 }, gFM[norm(addSym).mk]);
   var fx = fxv(cur(norm(addSym).mk));
   if(!tgtP || !(tgtP.px > 0) || fx == null){                // never invent a price or an exchange rate
    msg(['找不到 ' + addSym + ' 的報價或匯率，無法換算股數；持股沒有變更。', 'No price / FX for ' + addSym + '; nothing was changed.']);
    return;
   }
   var px = tgtP.px;
   var addShares = Math.round((trimTwd / (px * fx)) * 100) / 100;
   upsert(d, addSym, addShares, px);
  }
  put(d);
  render();
  msg(['已成功套用調倉！', 'Rebalancing applied successfully!']);
 });
 actRow.appendChild(applyBtn);
 x.appendChild(actRow);
}

// ---------------------------------------------------------------- Feature 6: Earnings Radar
var ADR = {'2330': 'TSM', '2303': 'UMC', '3711': 'ASX', '2412': 'CHT'};   // Taiwan names reporting as US ADRs
var EARNINGS_CAL = PUB.earn || [];             // Nasdaq earnings calendar + CBOE implied move (built server-side)

function renderEarnings(rows, tot){
 var x = document.getElementById('pfearn');
 if(!x) return;
 x.textContent = '';
 if(!rows.length){ x.style.display = 'none'; return; }

 var matched = [];
 var now = Date.now();
 rows.forEach(function(r){
  var sym = ((r.p && r.p.sym) || r.h.s || '').toUpperCase();
  var key = sym.replace(/\.(TW|TWO)$/,'');
  var item = EARNINGS_CAL.find(function(c){ return c.sym === key || c.sym === sym || c.sym === ADR[key]; });
  if(item){
   var t = new Date(item.date).getTime();
   var days = Math.ceil((t - now) / (86400 * 1000));
   var mv = item.mv != null ? item.mv : null;
   var dollarImp = mv != null ? (r.vt || 0) * (mv / 100) : null;
   var navPct = (dollarImp != null && tot > 0) ? (dollarImp / tot * 100) : null;
   matched.push({
    sym: sym,
    name: (r.p && r.p.name) || item.name,
    date: item.date,
    days: days,
    move: mv,
    time: item.time,
    vt: r.vt || 0,
    dollarImp: dollarImp,
    navPct: navPct,
    avg: item.avg
   });
  }
 });

 if(!matched.length){ x.style.display = 'none'; return; }
 x.style.display = 'block';

 matched.sort(function(a, b){ return a.days - b.days; });

 var hd = el('h3', '');
 hd.appendChild(L('🎯 個人持股專屬財報倒數與隱含波動雷達', 'Earnings Countdown & Implied Volatility Radar'));
 x.appendChild(hd);
 var sub = el('p', 'muted small');
 sub.appendChild(L('追蹤您目前持有的標的即將發布財報之倒數日程、選擇權隱含跳空幅度 (±%) 與對總資產的跳空震撼度',
                  'Track upcoming earnings dates, options implied moves, and dollar risk for your holdings.'));
 x.appendChild(sub);

 var grid = el('div', 'pfearn-grid');
 matched.forEach(function(m){
  var card = el('div', 'pfearn-card');
  var head = el('div', 'pfearn-head');
  var symEl = el('span', 'pfearn-sym', m.sym + ' ' + m.name);
  head.appendChild(symEl);

  var daysCls = m.days <= 3 ? 'urgent' : (m.days <= 7 ? 'warn' : 'normal');
  var daysText = m.days <= 0 ? (m.days === 0 ? '今日公布！' : '甫公布') : ('倒數 ' + m.days + ' 天');
  var daysTextEn = m.days <= 0 ? (m.days === 0 ? 'Today!' : 'Recent') : (m.days + 'd left');
  var badge = el('span', 'pfearn-days ' + daysCls);
  badge.appendChild(L(daysText, daysTextEn));
  head.appendChild(badge);
  card.appendChild(head);

  function addRow(lblZh, lblEn, valText, valCls){
   var r = el('div', 'pfearn-row');
   r.appendChild(L(lblZh, lblEn));
   var b = el('b', valCls || '', valText);
   r.appendChild(b);
   card.appendChild(r);
  }
  addRow('預計發布日期', 'Date', m.date);
  addRow('選擇權隱含跳空', 'Implied Move', m.move != null ? '±' + num(m.move, 1) + '%' : '—', m.move != null ? 'warn' : '');
  if(m.avg != null) addRow('過去 4 次平均反應', 'Avg past reaction', num(m.avg, 1) + '%');
  addRow('持股總市值', 'Holding Value', 'NT$ ' + num(m.vt, 0));
  addRow('跳空對淨值衝擊', 'NAV Impact', m.dollarImp != null ? '±NT$ ' + num(m.dollarImp, 0) + ' (±' + num(m.navPct, 1) + '%)' : '—', m.navPct >= 3 ? 'dn' : '');

  var desc = el('div', 'pfearn-desc');
  var tz = m.time === 'pre' ? ['盤前', 'pre-market'] : (m.time === 'after' ? ['盤後', 'after close'] : ['時間未定', 'time n/a']);
  desc.appendChild(L('美東日期，' + tz[0] + '。資料：Nasdaq 財報日曆；隱含波動＝CBOE 選擇權跨式價' + (m.move == null ? '（目前無資料）' : ''),
                     'US Eastern date, ' + tz[1] + '. Nasdaq calendar; implied move from CBOE straddles' + (m.move == null ? ' (n/a)' : '')));
  card.appendChild(desc);

  grid.appendChild(card);
 });
 x.appendChild(grid);

 var tip = el('div', 'pfdx-item act');
 tip.style.marginTop = '10px';
 tip.appendChild(el('span', 'ico', '💡'));
 var tipDesc = el('div', 'desc');
 tipDesc.appendChild(L('財報避震提醒：倒數 7 天以內的持股若單檔對淨值衝擊 > ±2.5%，公布當日跳空容易造成總資產劇烈洗盤。可考慮在公布前保留部分現金或設定防守防護。',
                       'Earnings Risk Tip: If implied move impacts NAV by > ±2.5%, consider building cash buffer or setting stops before announcement.'));
 tip.appendChild(tipDesc);
 x.appendChild(tip);
}

// ---------------------------------------------------------------- Form & Events
function upsert(d,s,n,c){var k=norm(s);if(!k||!(n>=0))return false;var key=k.key,i=d.h.findIndex(function(h){var x=norm(h.s);return x&&x.key===key;});
 if(n===0){if(i>=0)d.h.splice(i,1);return true;}var row={s:key,n:n,c:(c>0?c:0),p:0};if(i>=0){row.p=d.h[i].p||0;if(!(c>0))row.c=d.h[i].c||0;d.h[i]=row;}else d.h.push(row);return true;}
document.getElementById('pfadd').addEventListener('submit',function(e){e.preventDefault();var f=e.target,d=get();
 if(upsert(d,f.s.value,parseFloat(f.n.value),parseFloat(f.c.value))){put(d);f.reset();render();}else msg(['代號或股數格式不對','Check the ticker / shares']);});
document.getElementById('pfcash').addEventListener('submit',function(e){e.preventDefault();var f=e.target,d=get(),a=parseFloat(f.a.value);if(!isFinite(a))return;
 d.cash=(d.cash||[]).filter(function(c){return c.cur!==f.cur.value;});if(a)d.cash.push({cur:f.cur.value,a:a});put(d);f.a.value='';render();});
document.getElementById('pfpastebtn').addEventListener('click',function(){var d=get(),ok=0,bad=0,agg={};
 document.getElementById('pfpaste').value.split(/\r?\n/).forEach(function(line){var p=line.trim().split(/[\s,，\t]+/);if(!p[0])return;
  var s=p[0],n=parseFloat(p[1]),c=parseFloat(String(p[2]||'').replace(/\.+/g,'.'));
  var k=norm(s);if(!k||!(n>=0)){bad++;return;}
  var key=k.key;
  if(!agg[key])agg[key]={n:0,cost:0,hasC:false};
  agg[key].n+=n;
  if(c>0){agg[key].cost+=n*c;agg[key].hasC=true;}
  ok++;});
 Object.keys(agg).forEach(function(key){
  var item=agg[key],avgC=item.hasC&&(item.n>0)?(item.cost/item.n):0;
  upsert(d,key,item.n,avgC);
 });
 put(d);document.getElementById('pfpaste').value='';render();
 setTimeout(function(){msg(['已加入 '+ok+' 筆'+(bad?'，'+bad+' 行格式不對':''),'Added '+ok+(bad?', '+bad+' lines skipped':'')]);},50);});
document.getElementById('pfexp').addEventListener('click',function(){var b=new Blob([JSON.stringify(get(),null,1)],{type:'application/json'}),a=document.createElement('a');
 a.href=URL.createObjectURL(b);a.download='my_holdings_'+new Date().toISOString().slice(0,10)+'.json';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},500);});
document.getElementById('pfimp').addEventListener('change',function(e){var f=e.target.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){try{var d=JSON.parse(rd.result);
  if(!d||!Array.isArray(d.h))throw 0;var clean={v:1,h:[],cash:[],nav:[]};d.h.forEach(function(h){if(h&&norm(h.s)&&h.n>=0)clean.h.push({s:norm(h.s).key,n:+h.n,c:+h.c>0?+h.c:0,p:+h.p>0?+h.p:0});});
  (d.cash||[]).forEach(function(c){if(c&&['TWD','USD','HKD'].indexOf(c.cur)>=0&&isFinite(+c.a))clean.cash.push({cur:c.cur,a:+c.a});});
  if(Array.isArray(d.nav))clean.nav=d.nav;
  put(clean);render();setTimeout(function(){msg(['已匯入 '+clean.h.length+' 檔持股','Imported '+clean.h.length+' holdings']);},50);}catch(x){msg(['檔案格式不對','Invalid file']);}};rd.readAsText(f);e.target.value='';});
document.getElementById('pfclr').addEventListener('click',function(){if(confirm(en()?'Delete all holdings and cash stored in this browser?':'確定刪除這個瀏覽器裡的所有持股與現金？（建議先匯出備份）')){put({v:1,h:[],cash:[],nav:[],cleared:true});render();}});   // an explicit clear: the only empty state allowed to sync
document.getElementById('langBtn')&&document.getElementById('langBtn').addEventListener('click',function(){setTimeout(render,0);});
render();})();
"""
