"""Website-only extras (built in the GitHub Actions run, not in the Discord bot loop):
個股情報 (analyst consensus, dividends, SEC 8-K, earnings implied move), market mood, alarm-rule backtest, US→TW linkage,
index expected moves, geopolitical heat and the weekly AI bull/bear notes on the growth leaders.

refresh() does the network work (each feed budgeted and cached); build() is pure and fills eng.sx."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR, SETTINGS
from ..data import earnings_data as ED
from ..data import geo as GEO
from ..data import stockinfo as SI
from ..data.econcal import us_today
from ..data.stocks import universe
from . import mood as MO

log = logging.getLogger(__name__)
F_DEBATE = DATA_DIR / "econ_debate.json"


def cfg() -> Dict:
    return SETTINGS.get("site_extras", {}) or {}


def upcoming(ed, syms, days: int = 14, today: Optional[str] = None) -> List[Dict]:
    today = today or us_today().isoformat()
    hi = (date.fromisoformat(today) + timedelta(days=days)).isoformat()
    want, out = set(syms), []
    for d, rec in sorted(((getattr(ed, "days", None) or {}).items())):
        if not (today <= d <= hi):
            continue
        for r in rec.get("rows", []):
            if r["sym"] in want and r.get("eps") is None:
                out.append({"sym": r["sym"], "date": d, "time": r.get("time") or "", "eps_f": r.get("eps_f")})
    return out


def _growth_top(n: int = 10) -> List[Dict]:
    from . import growth as GR
    d = GR.published("us")
    if not d:
        return []
    cols = d["cols"]
    rows = [dict(zip(cols, r)) for r in d["rows"] if r[cols.index("rank")]]
    return sorted(rows, key=lambda r: r["rank"])[:n]


async def refresh(eng, deadline_s: Optional[float] = None) -> Dict:
    """All network feeds under ONE overall deadline (default site_extras.refresh_deadline_s or 360 s).  Each feed gets
    min(its own budget, time left) and is additionally wrapped in asyncio.wait_for(time left), so a hung feed can't overrun."""
    c = cfg()
    total = float(deadline_s if deadline_s is not None else c.get("refresh_deadline_s", 360))
    t_end = time.monotonic() + total
    u = universe()
    us = list((u.get("us") or {}).get("symbols", {}))
    allsyms = us + list((u.get("tw") or {}).get("symbols", {})) + list((u.get("hk") or {}).get("symbols", {}))
    allsyms += [r["sym"] for r in _growth_top() if r["sym"] not in allsyms]
    rep: Dict = {}

    def left() -> float:
        return t_end - time.monotonic()

    async def run(nm: str, mk):
        rem = left()
        if rem < 5:
            log.warning("site extras %s skipped: overall deadline reached", nm)
            return None
        try:
            return await asyncio.wait_for(mk(max(1.0, rem - 3)), rem)   # the feed's own budget ends a little before the hard stop
        except asyncio.TimeoutError:
            log.warning("site extras %s cut off by the overall deadline", nm)
        except Exception as e:  # noqa: BLE001
            log.warning("site extras %s failed: %s", nm, e)
        return None

    for nm, mk in (("yahoo", lambda rem: SI.refresh_yf(allsyms, min(float(c.get("yf_budget_s", 150)), rem))),
                   ("sec8k", lambda rem: SI.refresh_8k(us, min(float(c.get("sec_budget_s", 60)), rem))),
                   ("geo", lambda rem: GEO.refresh())):
        r = await run(nm, mk)
        if r is not None:
            rep[nm] = len(r)
    up = upcoming(getattr(eng, "earnings", None), us)
    await run("earnings history", lambda rem: ED.refresh_surprises([x["sym"] for x in up], {}, min(float(c.get("surprise_budget_s", 40)), rem)))
    await run("CBOE straddles", lambda rem: SI.refresh_options(list(MO.EM_SYMS) + [x["sym"] for x in up], min(float(c.get("cboe_budget_s", 75)), rem)))
    rep["earnings_window"] = len(up)
    return rep


# ------------------------------------------------------------------ pure assembly
def _names(u: Dict) -> Dict[str, tuple]:
    out = {}
    for mk, m in u.items():
        for s, (zh, en) in (m.get("symbols") or {}).items():
            out[s] = (zh, en, mk, (m.get("themes") or {}).get(s, "其他"))
    return out


def _last(sp, s: str) -> Optional[float]:
    x = sp.series(s) if sp is not None else pd.Series(dtype=float)
    return float(x.iloc[-1]) if len(x) else None


# Dividend withholding (%) for a Taiwan resident on foreign ADRs in the US universe (home-country rate, as usually applied
# through a US broker); other non-US issuers show "—".  US-domiciled issuers: 30%.
ADR_TAX = {"TSM": 21.0, "ASML": 15.0, "NVO": 27.0, "CCJ": 25.0}
STALE_DAYS = 7


def _net_yield(s: str, d: Dict, y: float, mk: str):
    """→ (after-withholding yield or None, withholding rate % or None)."""
    if mk != "us":
        return y, None
    if s in ADR_TAX:
        return y * (1 - ADR_TAX[s] / 100), ADR_TAX[s]
    ctry = d.get("country")
    if ctry in (None, "", "United States"):                   # older caches have no country: the US list is US issuers by default
        return y * 0.7, 30.0
    return None, None


def stock_rows(info: Dict, u: Dict, sp, today: str, now: Optional[float] = None) -> Dict:
    nm = _names(u)
    now = now or time.time()
    ana: Dict[str, List[Dict]] = {"us": [], "tw": [], "hk": []}
    div: Dict[str, List[Dict]] = {"us": [], "tw": [], "hk": []}
    soon = (date.fromisoformat(today) + timedelta(days=30)).isoformat()
    for s, (zh, en, mk, th) in nm.items():
        d = info.get(s) or {}
        if not d:
            continue
        ok_ts = d.get("ok_ts") or d.get("ts")
        if not ok_ts or now - float(ok_ts) > STALE_DAYS * 86400:
            continue                                           # last successful Yahoo fetch too old: don't show stale numbers
        px = _last(sp, s) or d.get("px")
        base = {"sym": s, "code": s.split(".")[0], "name": zh, "name_en": en, "theme": th, "px": px}
        if d.get("tm") and px and (d.get("n") or 0) >= 1:
            ana[mk].append({**base, "tm": d["tm"], "th": d.get("th"), "tl": d.get("tl"), "n": d.get("n"), "rm": d.get("rm"),
                            "rk": d.get("rk"), "up": (d["tm"] / px - 1) * 100, "uph": (d["th"] / px - 1) * 100 if d.get("th") else None,
                            "upl": (d["tl"] / px - 1) * 100 if d.get("tl") else None})
        if d.get("div") and px:
            if d.get("fcur") and d.get("cur") and d["fcur"] != d["cur"] and s not in ADR_TAX:
                continue                                       # dividend may be in the reporting currency, price in the trading one
            if d.get("px") and abs(px / d["px"] - 1) > 0.3:
                continue                                       # our price and Yahoo's disagree (split / unit problem)
            y = d["div"] / px * 100
            if y <= 0 or y > 25:
                continue
            net, tax = _net_yield(s, d, y, mk)
            div[mk].append({**base, "yld": y, "net": net, "tax": tax, "rate": d["div"], "ex": d.get("ex"),
                            "ex_soon": bool(d.get("ex") and today <= d["ex"] <= soon), "paid": d.get("paid"), "grow": d.get("grow"),
                            "payout": d["payout"] * 100 if d.get("payout") else None, "y5": d.get("y5")})
    for mk in ana:
        ana[mk].sort(key=lambda r: -(r["up"] if r["up"] is not None else -999))
        div[mk].sort(key=lambda r: -r["yld"])
    return {"analyst": ana, "div": div}


def filings(k8: Dict, u: Dict, today: str, days: int = 30) -> Dict:
    nm = _names(u)
    lo = (date.fromisoformat(today) - timedelta(days=days)).isoformat()
    rows = []
    cur = {s: k8[s] for s in nm if s in k8}                  # current universe only (the cache may hold dropped names)
    for s, rec in cur.items():
        for r in rec.get("rows", []):
            if r["date"] >= lo:
                zh = nm[s]
                rows.append({**r, "name": zh[0], "name_en": zh[1], "theme": zh[3]})
    rows.sort(key=lambda r: r["date"], reverse=True)
    rows.sort(key=lambda r: -r["sev"])
    covered = sum(1 for v in cur.values() if not v.get("na"))
    return {"rows": rows[:60], "n_hi": sum(1 for r in rows if r["sev"] >= 3), "n_mid": sum(1 for r in rows if r["sev"] == 2),
            "covered": covered, "days": days}


def earnings_moves(up: List[Dict], opt: Dict, surp: Dict, sp, u: Dict) -> List[Dict]:
    from .techearn import reaction
    nm = _names(u)
    out = []
    for x in up:
        s = x["sym"]
        # first live expiry on/after report date + 1, for pre-market, after-close and unknown times alike: it covers both
        # sessions of the historical reaction window (close before the report → close the session after it)
        w = SI.straddle_after(opt.get(s) or {}, x["date"], after_close=True)
        past = [r["date"] for r in (surp.get(s) or {}).get("rows", []) if r.get("date") and r["date"] < x["date"]]
        reacts = [v for v in (reaction(sp.series(s), d) if sp is not None else None for d in sorted(past)[-4:]) if v is not None]
        avg = float(np.mean([abs(v) for v in reacts])) if reacts else None
        zh = nm.get(s, (s, s, "us", ""))
        out.append({"sym": s, "name": zh[0], "name_en": zh[1], "theme": zh[3], "date": x["date"], "time": x["time"],
                    "mv": w["mv"] if w else None, "exp": w["exp"] if w else None, "spot": (opt.get(s) or {}).get("spot"),
                    "asof": (opt.get(s) or {}).get("asof") if w else None,
                    "reacts": [round(v, 1) for v in reacts], "avg": avg, "ratio": (w["mv"] / avg) if w and avg else None})
    out.sort(key=lambda r: (r["date"], r["sym"]))
    return out


def geo_view(g: Dict, h: Optional[pd.DataFrame]) -> Dict:
    if not g:
        return {"available": False}
    out = []
    for th, (zh, en, _, tick) in GEO.THEATRES.items():
        v = g.get(th)
        if not v:
            continue
        mk = []
        for t in tick:
            s = MO._s(h, t) if h is not None else None
            if s is None:
                continue
            r = s.pct_change().dropna()
            sd = float(r.iloc[-252:].std()) if len(r) > 60 else None
            d1 = float(r.iloc[-1] * 100)
            d5 = float((s.iloc[-1] / s.iloc[-6] - 1) * 100) if len(s) > 6 else None
            mk.append({"t": t, "d1": d1, "d5": d5, "z": (r.iloc[-1] / sd) if sd else None})
        out.append({"k": th, "zh": zh, "en": en, **v, "mk": mk})
    out.sort(key=lambda r: (-r["level"]["k"], -(r["level"].get("ratio") or 0)))
    return {"available": bool(out), "rows": out}


def _load_debate() -> Dict:
    try:
        if F_DEBATE.exists():
            return json.loads(F_DEBATE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    return {}


def build(eng) -> Dict:
    u = universe()
    today = us_today().isoformat()
    sp = getattr(eng, "stockprices", None)
    h = getattr(getattr(eng, "market", None), "history", None)
    allc = SI.load_all()
    res: Dict = {"asof": today}
    for k, fn in (("stocks", lambda: stock_rows(allc["yf"], u, sp, today)),
                  ("k8", lambda: filings(allc["k8"], u, today)),
                  ("earn", lambda: earnings_moves(upcoming(getattr(eng, "earnings", None), list((u.get("us") or {}).get("symbols", {})), today=today),
                                                  allc["opt"], ED._load(ED.F_SURP), sp, u)),
                  ("fg", lambda: MO.fear_greed(h)), ("rules", lambda: MO.rule_backtest(h)), ("link", lambda: MO.linkage(sp, u, h)),
                  ("em", lambda: MO.expected_move(allc["opt"], h)), ("geo", lambda: geo_view(GEO.load(), h))):
        try:
            res[k] = fn()
        except Exception:  # noqa: BLE001
            log.exception("site extras %s failed", k)
            res[k] = {}
    db = _load_debate()
    top = _growth_top()
    res["debate"] = [{**r, "ai": db.get(r["sym"]) if (db.get(r["sym"]) or {}).get("bull") else None} for r in top]
    res["n_info"] = len(allc["yf"])
    return res


# ------------------------------------------------------------------ weekly AI bull / bear / risk notes
DEBATE_SYS = """你是買方研究部的三人小組，為公開網頁替一檔成長股寫「多方、空方、風控」三段短評，讀者是一般大眾。
【鐵律】
1. 只能使用提供的數字與事實，沒有的就不提；不得編造新聞、產品、客戶、管理層說法或任何未提供的數字。
2. 這不是投資建議：不得出現買進、賣出、加碼、減碼、停損、停利、目標價、部位比例等任何操作字眼。
3. 多方：提供的數據裡最有力的成長或品質證據。空方：估值、獲利品質、成長放緩、燒錢、併購墊高營收等疑慮。
   風控：哪些數字一變就代表論點出問題（例如營收年增跌破多少、現金可撐年數、毛利率），只描述要觀察什麼。
4. 每段 2～3 句、台灣繁體中文。只輸出 JSON：{"bull":"…","bear":"…","risk":"…"}"""


def debate_prompt(r: Dict, info: Dict) -> str:
    def f(k, n=1, suf=""):
        v = r.get(k)
        return "—" if v is None else (f"{v:.{n}f}{suf}" if isinstance(v, (int, float)) else str(v))
    L = [f"公司：{r.get('name')}（{r.get('sym')}），產業：{r.get('ind') or '—'} {r.get('sub') or ''}",
         f"市值：{(r.get('mcap') or 0) / 1e9:.1f} 十億美元；近四季營收：{(r.get('ttm') or 0) / 1e9:.2f} 十億美元",
         f"營收年增（近四季）：{f('g', 0, '%')}；最近一季年增：{f('q_yoy', 0, '%')}；成長加速（百分點）：{f('accel', 0)}",
         f"毛利率：{f('gm', 0, '%')}；營業利益率：{f('om', 0, '%')}；40 法則：{f('r40', 0)}",
         f"估值：P/S {f('ps', 1)}；P/E {f('pe', 1)}；估值÷成長 {f('gav', 3)}（基準 {r.get('basis') or '—'}）",
         f"現金：{(r.get('cash') or 0) / 1e9:.2f} 十億美元；每年燒錢：{(r.get('burn') or 0) / 1e9:.2f} 十億美元；可撐年數：{f('runway', 1)}",
         f"營收含併購（商譽大增）：{'是' if r.get('ma') else '否'}；營收規模尚小：{'是' if r.get('small') else '否'}",
         f"技術面狀態：{r.get('st') or '—'}"]
    if info.get("tm"):
        L.append(f"分析師平均目標價距現價：{(info['up'] if info.get('up') is not None else 0):+.0f}%（{info.get('n') or '—'} 位分析師）")
    return "\n".join(L)


def _save_debate(db: Dict) -> None:
    try:
        F_DEBATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = F_DEBATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(db, ensure_ascii=False), encoding="utf-8")
        tmp.replace(F_DEBATE)                                  # atomic: a killed run never leaves a half-written cache
    except Exception as e:  # noqa: BLE001
        log.warning("debate cache not saved: %s", e)


def _prune_debate(db: Dict, keep: List[str], max_n: int = 30) -> Dict:
    if keep:                                                   # no growth list (screen failed) → leave the cache alone
        ks = set(keep)
        db = {k: v for k, v in db.items() if k in ks}
    if len(db) > max_n:
        db = dict(sorted(db.items(), key=lambda kv: -float(kv[1].get("ts") or kv[1].get("fail_ts") or 0))[:max_n])
    return db


async def generate_debates(limit: int = 10, max_age_days: float = 7, deadline_s: float = 150, max_new: int = 3,
                           fail_backoff_h: float = 24, call_timeout_s: float = 90) -> int:
    """At most max_new new notes per run, inside deadline_s.  A failed call or unparseable answer records {"fail_ts"} and
    that symbol is skipped for fail_backoff_h hours (an existing note is kept)."""
    from ..ai import llm
    from ..ai.econ_ai import scrub
    t_end = time.monotonic() + deadline_s
    top = _growth_top(limit)
    db = _prune_debate(_load_debate(), [r["sym"] for r in top])
    info = SI.load_all()["yf"]
    n = 0

    def failed(sym: str, why: str) -> None:
        db[sym] = {**(db.get(sym) or {}), "fail_ts": time.time()}
        log.info("AI bull/bear note %s failed (%s); retry in %.0fh", sym, why, fail_backoff_h)

    try:
        for r in top:
            if n >= max_new or t_end - time.monotonic() <= 1:
                break
            sym = r["sym"]
            rec = db.get(sym) or {}
            if time.time() - float(rec.get("fail_ts") or 0) < fail_backoff_h * 3600:
                continue
            if rec.get("bull") and time.time() - float(rec.get("ts", 0)) < max_age_days * 86400:
                continue
            wait = min(call_timeout_s, t_end - time.monotonic())
            try:
                text, name = await asyncio.wait_for(llm.complete(DEBATE_SYS, debate_prompt(r, info.get(sym) or {}), 900), wait)
            except asyncio.TimeoutError:
                if wait >= call_timeout_s:                     # the call itself hung (not just the end of this run's budget)
                    failed(sym, "timeout")
                break
            except Exception as e:  # noqa: BLE001
                failed(sym, str(e)[:80])
                continue
            if name == "none":
                break                                          # no AI engine configured: not the symbol's fault
            if not text or text.startswith("⚠️"):
                failed(sym, (text or "empty")[:80])
                break                                          # the engine is failing: stop for this run
            try:
                js = json.loads(text[text.index("{"):text.rindex("}") + 1])
                out = {k: scrub(str(js.get(k, ""))) for k in ("bull", "bear", "risk")}
            except Exception:  # noqa: BLE001
                failed(sym, "unparseable JSON")
                continue
            if not all(out.values()):
                failed(sym, "missing fields")
                continue
            db[sym] = {**out, "engine": name, "ts": time.time(), "date": us_today().isoformat()}
            n += 1
    finally:
        _save_debate(db)
    return n
