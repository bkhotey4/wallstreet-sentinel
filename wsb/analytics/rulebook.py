"""我的持股規則檢查：把華爾街常用的進出場紀律寫成「你的規則」，每天對每一檔持股自動檢查哪些條件成立。

Three groups, each rule a plain test on model data (no news, no AI, no forecast):
  出場檢查  thesis broken (distress radar red / bankruptcy model / earnings miss or guidance below), thesis stop vs cost,
            trend break (below the 200-day line + negative 12-1 momentum + lagging the index), trailing stop from the high
  減碼檢查  position above its cap, theme above its cap, risk contribution above its cap
  加碼條件  ALL must hold: room under the cap, above the 200-day line, positive 12-1 momentum, no distress light and a low
            bankruptcy probability, last earnings at or above consensus, market stress below the user's line
Thresholds live in settings.yaml (rulebook:) and are the user's own choices; the output says which of the user's rules
are met, never "buy" or "sell".  Holdings-derived → owner DM / owner-only command, never the public site."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import SETTINGS

SOURCES = {
    "thesis": "論點停損：基本面投資人的第一條賣出理由（論點不再成立）",
    "stop": "停損紀律：長線基金常用 20–25%（短線如 CANSLIM 用 7–8%）",
    "trend": "趨勢：200 日線（Faber 2007）＋ 12-1 個月動能（Jegadeesh & Titman 1993）",
    "trail": "移動停損：從高點回落一定比例",
    "size": "部位上限與風險預算：基金常見的單一持股／主題上限、風險貢獻上限",
    "macro": "大環境：本站壓力指數",
}


# The one place the default thresholds live (settings.yaml rulebook: overrides any of them; the website receives the
# merged values, so the browser never carries numbers of its own).
DEFAULTS = {"bk_exit_pct": 5, "stop_loss_pct": 25, "trend_lag_pp": 15, "trailing_pct": 30, "max_weight_pct": 15,
            "max_theme_pct": 30, "max_risk_contrib_pct": 25, "bk_add_max_pct": 2, "add_max_ssi": 60, "add_min_known": 4}
BENCH = {"us": ("^GSPC", "標普 500"), "tw": ("^TWII", "加權指數"), "hk": ("^HSI", "恆生指數")}


def cfg() -> Dict:
    return {**DEFAULTS, **(SETTINGS.get("rulebook", {}) or {})}


def market_of(sym: str) -> str:
    return "tw" if sym.endswith((".TW", ".TWO")) else "hk" if sym.endswith(".HK") else "us"


def _theme(sym: str) -> Optional[str]:
    """The scoring universe's theme, else the exchange-listed industry from the whole-market list; None if unknown
    (unknown names are never lumped into one made-up group for the concentration check)."""
    from ..data.stocks import universe
    for m in universe().values():
        if sym in m.get("themes", {}):
            return m["themes"][sym]
    try:                                              # another share class of the same company (GOOG ↔ GOOGL): same SEC CIK
        import json as _json
        from ..data.edgar_holdings import _MAP_FILE
        tm = _json.loads(_MAP_FILE.read_text(encoding="utf-8")) if _MAP_FILE.exists() else {}
        cik = (tm.get(sym) or {}).get("cik")
        if cik:
            for m in universe().values():
                for s2, th in m.get("themes", {}).items():
                    if (tm.get(s2) or {}).get("cik") == cik:
                        return th
    except Exception:  # noqa: BLE001
        pass
    try:
        from ..data import fullmarket as FMK
        for it in (FMK._load_json(FMK._LISTS).get(market_of(sym)) or []):
            if it.get("sym") == sym and it.get("ind"):
                return "產業：" + str(it["ind"])
    except Exception:  # noqa: BLE001
        pass
    return None


def _chk(group: str, rid: str, zh: str, met: Optional[bool], txt: str, src: str) -> Dict:
    """met: True / False / None (no data → not counted either way)."""
    return {"group": group, "id": rid, "zh": zh, "met": met, "txt": txt, "src": src}


def price_stats(px: pd.Series, bench: pd.Series) -> Dict:
    out: Dict = {}
    if len(px) < 30:
        return out
    out["price"] = float(px.iloc[-1])
    out["asof"] = px.index[-1].strftime("%Y-%m-%d")
    if len(px) >= 200:
        out["ma200"] = float(px.iloc[-200:].mean())
    if len(px) >= 253:
        out["mom_12_1"] = float(px.iloc[-22] / px.iloc[-253] - 1) * 100       # 12 months, skipping the latest month
        out["high_52w"] = float(px.iloc[-252:].max())
    if len(px) >= 127 and len(bench) >= 127:
        j = pd.concat([px, bench], axis=1).dropna()
        if len(j) >= 127:
            out["rel_6m"] = float((j.iloc[-1, 0] / j.iloc[-127, 0] - 1) - (j.iloc[-1, 1] / j.iloc[-127, 1] - 1)) * 100
    r = np.log(px).diff().dropna().iloc[-252:]
    if len(r) > 60:
        out["vol"] = float(r.std() * np.sqrt(252) * 100)
    return out


def check(sym: str, pos: Dict, hold: Dict, ps: Dict, dz: Optional[Dict], surp: Optional[Dict], guide_below: Optional[bool],
          theme_w: Optional[float], ssi: Optional[float], theme: Optional[str] = None, bench_name: str = "大盤") -> List[Dict]:
    c = cfg()
    out: List[Dict] = []
    w = float(pos.get("weight") or 0)
    price, cost = ps.get("price"), float(hold.get("cost") or 0)
    # ---------------- 出場檢查
    st = (dz or {}).get("state")
    bk = (dz or {}).get("bk_prob")
    if dz is None:
        out.append(_chk("exit", "distress", "論點：財務體質", None, "沒有 SEC 財報（非美國公司或資料未到）", SOURCES["thesis"]))
    else:
        bad = st == "alert" or (bk is not None and bk * 100 >= float(c["bk_exit_pct"]))
        txt = f"危機雷達{ {'alert': '紅燈', 'watch': '黃燈', 'ok': '無燈號'}.get(st, '—') }" + (f"，破產機率 {bk * 100:.1f}%" if bk is not None else "")
        out.append(_chk("exit", "distress", "論點：財務體質", bool(bad), txt, SOURCES["thesis"]))
    if surp is None and guide_below is None:
        out.append(_chk("exit", "earnings", "論點：最近財報", None, "沒有可比較的財報數字", SOURCES["thesis"]))
    else:
        miss = bool(surp and surp.get("surp") is not None and surp["surp"] < 0)
        txt = (f"EPS {surp['eps']} vs 預期 {surp['cons']}（{surp['surp']:+.1f}%）" if surp and surp.get("surp") is not None else "EPS 無資料")
        if guide_below:
            txt += "；營收低於上次指引"
        out.append(_chk("exit", "earnings", "論點：最近財報", miss or bool(guide_below), txt, SOURCES["thesis"]))
    lim = float(c["stop_loss_pct"])
    if price and cost:
        dd = (price / cost - 1) * 100
        out.append(_chk("exit", "stop", f"停損：低於成本 {lim:.0f}%", dd <= -lim, f"相對成本 {dd:+.1f}%", SOURCES["stop"]))
    else:
        out.append(_chk("exit", "stop", f"停損：低於成本 {lim:.0f}%", None, "沒有成本或價格", SOURCES["stop"]))
    if ps.get("ma200") is not None and ps.get("mom_12_1") is not None and ps.get("rel_6m") is not None:
        lag = float(c["trend_lag_pp"])
        brk = price < ps["ma200"] and ps["mom_12_1"] < 0 and ps["rel_6m"] <= -lag
        out.append(_chk("exit", "trend", "趨勢破壞（三項同時）", brk,
                        f"{'低於' if price < ps['ma200'] else '高於'} 200 日線 {ps['ma200']:.2f}｜12-1 動能 {ps['mom_12_1']:+.0f}%｜6 個月相對{bench_name} {ps['rel_6m']:+.0f} 個百分點",
                        SOURCES["trend"]))
    else:
        out.append(_chk("exit", "trend", "趨勢破壞（三項同時）", None, "歷史股價不足一年", SOURCES["trend"]))
    lim = float(c["trailing_pct"])
    if ps.get("high_52w") and price:
        tr = (price / ps["high_52w"] - 1) * 100
        out.append(_chk("exit", "trail", f"移動停損：距 52 週高點 {lim:.0f}%", tr <= -lim, f"距高點 {tr:+.0f}%", SOURCES["trail"]))
    else:
        out.append(_chk("exit", "trail", f"移動停損：距 52 週高點 {lim:.0f}%", None, "歷史股價不足一年", SOURCES["trail"]))
    # ---------------- 減碼檢查
    cap, tcap, rcap = float(c["max_weight_pct"]), float(c["max_theme_pct"]), float(c["max_risk_contrib_pct"])
    out.append(_chk("trim", "weight", f"單一持股 > {cap:.0f}%", w > cap, f"佔比 {w:.1f}%", SOURCES["size"]))
    out.append(_chk("trim", "theme", f"同主題 > {tcap:.0f}%", None if theme is None or theme_w is None else theme_w > tcap,
                    "沒有族群／產業資料" if theme is None or theme_w is None else f"「{theme}」合計 {theme_w:.1f}%", SOURCES["size"]))
    rc = pos.get("risk_contrib_pct")
    out.append(_chk("trim", "risk", f"風險貢獻 > {rcap:.0f}%", None if rc is None else rc > rcap,
                    "—" if rc is None else f"佔組合風險 {rc:.1f}%（佔比 {w:.1f}%）", SOURCES["size"]))
    # ---------------- 加碼條件（全部成立）
    out.append(_chk("add", "room", "部位還在上限內", w < cap, f"佔比 {w:.1f}%（上限 {cap:.0f}%）", SOURCES["size"]))
    out.append(_chk("add", "ma200", "站上 200 日線", None if ps.get("ma200") is None else price > ps["ma200"],
                    "—" if ps.get("ma200") is None else f"{price:.2f} vs {ps['ma200']:.2f}", SOURCES["trend"]))
    out.append(_chk("add", "mom", "12-1 動能為正", None if ps.get("mom_12_1") is None else ps["mom_12_1"] > 0,
                    "—" if ps.get("mom_12_1") is None else f"{ps['mom_12_1']:+.0f}%", SOURCES["trend"]))
    if dz is not None:
        # no bankruptcy probability = the "low bankruptcy risk" half is unknown, not passed
        ok = None if bk is None and st == "ok" else (st == "ok" and bk * 100 < float(c["bk_add_max_pct"]))
        out.append(_chk("add", "quality", "財務體質無警訊", ok, f"危機雷達{'無燈號' if st == 'ok' else '有燈號'}" +
                        (f"，破產機率 {bk * 100:.1f}%" if bk is not None else ""), SOURCES["thesis"]))
    else:
        out.append(_chk("add", "quality", "財務體質無警訊", None, "沒有 SEC 財報", SOURCES["thesis"]))
    out.append(_chk("add", "beat", "最近財報不低於預期", None if not surp or surp.get("surp") is None else surp["surp"] >= 0,
                    "—" if not surp or surp.get("surp") is None else f"EPS 驚喜 {surp['surp']:+.1f}%", SOURCES["thesis"]))
    lim = float(c["add_max_ssi"])
    out.append(_chk("add", "macro", f"壓力指數 < {lim:.0f}", None if ssi is None else ssi < lim,
                    "—" if ssi is None else f"壓力指數 {ssi:.0f}", SOURCES["macro"]))
    return out


ADD_REQUIRED = ("room", "ma200", "quality", "macro")      # unknown → "待確認", never "全部成立"


def summarize(checks: List[Dict]) -> Dict:
    def g(name):
        return [x for x in checks if x["group"] == name]
    ex, tr, ad = g("exit"), g("trim"), g("add")
    n_ex, n_tr = sum(x["met"] is True for x in ex), sum(x["met"] is True for x in tr)
    ad_known = [x for x in ad if x["met"] is not None]
    n_ad = sum(x["met"] is True for x in ad_known)
    have = {x.get("id") for x in ad}
    req_unknown = [x["zh"] for x in ad if x.get("id") in ADD_REQUIRED and x["met"] is None] +         ([i for i in ADD_REQUIRED if i not in have] if ad else [])     # a required check that is not even listed is missing
    opt = [x for x in ad if x.get("id") not in ADD_REQUIRED]
    opt_known = [x for x in opt if x["met"] is not None]
    all_known_ok = bool(ad_known) and n_ad == len(ad_known)
    all_add = all_known_ok and not req_unknown and len(ad_known) >= int(cfg()["add_min_known"])
    pend = all_known_ok and not all_add                   # nothing failed, but required data are missing
    if n_ex >= 2:
        st, zh = "exit2", f"出場檢查：{n_ex} 項觸發"
    elif n_ex == 1:
        st, zh = "exit1", "出場檢查：1 項觸發"
    elif n_tr:
        st, zh = "trim", f"減碼檢查：{n_tr} 項觸發"
    elif all_add:
        st, zh = "add", (f"加碼條件：{len(ad)} 項全部成立" if len(ad_known) == len(ad) else
                         f"加碼條件：必備 {len(ad) - len(opt)}/{len(ad) - len(opt)} 項成立，參考項 {len(opt_known)}/{len(opt)} 項有資料且成立")
    elif pend:
        st, zh = "pend", (f"加碼條件：已知 {n_ad}/{len(ad)} 項成立，" + (f"必備資料待確認（{'、'.join(req_unknown)}）" if req_unknown
                                                                    else f"有資料的項目不足 {int(cfg()['add_min_known'])} 項"))
    else:
        st, zh = "hold", "沒有規則觸發"
    return {"state": st, "zh": zh, "exit_hits": n_ex, "exit_n": len(ex), "trim_hits": n_tr, "trim_n": len(tr),
            "add_met": n_ad, "add_n": len(ad_known), "add_total": len(ad), "add_unknown": len(ad) - len(ad_known),
            "add_all": all_add, "add_pending": req_unknown}


ORDER = {"exit2": 0, "exit1": 1, "trim": 2, "add": 3, "pend": 4, "hold": 5}


def build(eng) -> Dict:
    if not cfg().get("enabled", True):
        return {"available": False}
    pf = getattr(eng, "portfolio", None) or {}
    holds = getattr(eng, "holdings", None) or {}
    if not pf or pf.get("error") or not holds:
        return {"available": False}
    from ..data import distress_data as DD
    from . import distress as DZ
    from .sessions import completed
    today = date.today()
    cache = DD.load()
    surp_all = (getattr(getattr(eng, "earnings", None), "surprise", None) or {})
    try:
        from ..data import earn_release as ER
        rel = ER.load()
    except Exception:  # noqa: BLE001
        rel = {}
    st_ = getattr(eng, "stress", None)
    ssi = st_.score if st_ and (getattr(st_, "coverage", None) or 0) >= 0.6 else None   # a thin SSI is not a macro all-clear
    pos = {p["sym"]: p for p in pf.get("positions", []) if not p.get("error")}
    themes = {s: _theme(s) for s in pos}
    theme_w: Dict[str, float] = {}
    for s, p in pos.items():
        if themes[s]:
            theme_w[themes[s]] = theme_w.get(themes[s], 0.0) + float(p.get("weight") or 0)
    rows = []
    for s, p in pos.items():
        bsym, bname = BENCH[market_of(s)]
        px = completed(eng.market.series(s).dropna(), s)
        bench = completed(eng.market.series(bsym).dropna(), bsym)
        ps = price_stats(px, bench)
        if not ps:                                     # no history yet (a holding just added): price from the portfolio,
            ps = {"price": p.get("price"), "asof": None}  # every price rule shows "no data" instead of the row vanishing
        elif ps.get("asof") and (today - date.fromisoformat(ps["asof"])).days > 7:   # history stopped updating:
            ps = {"price": p.get("price"), "asof": ps["asof"], "stale": True}       # its MA / momentum are not today's
        dz = None
        rec = cache.get(s) or {}
        if rec.get("bs"):
            a = DZ.assess(s, {"zh": p.get("name") or s, "kind": "auto"}, rec, px, pd.Series(dtype=float), today)
            dz = {"state": a["state"], "bk_prob": a.get("bk_prob")}
        sr = ((surp_all.get(s) or {}).get("rows") or [None])[0]
        keys = sorted(k for k in rel if k.startswith(s + "|"))
        gb = None
        if keys:
            vp = rel[keys[-1]].get("vs_prev_guide") or []
            gb = any(x["metric"] == "revenue" and x["pos"] == "below" for x in vp) if vp else None
        ch = check(s, p, holds.get(s, {}), ps, dz, sr, gb, theme_w.get(themes[s]) if themes[s] else None, ssi, themes[s], bname)
        rows.append({"sym": s, "name": p.get("name") or s, "weight": p.get("weight"), "pnl_pct": p.get("pnl_pct"),
                     "price": ps.get("price"), "asof": ps.get("asof"), "vol": ps.get("vol"), "checks": ch, **summarize(ch)})
    rows.sort(key=lambda r: (ORDER[r["state"]], -(r["weight"] or 0)))
    return {"available": bool(rows), "asof": max((r["asof"] for r in rows if r["asof"]), default=None), "rows": rows, "ssi": ssi}
