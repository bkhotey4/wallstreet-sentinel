"""台灣: government bonds, corporate bonds, the economy, the central bank and money, life insurers and housing, and a
plain-language read of all of it.  Every sentence is chosen by rules on the numbers (data from wsb.data.twmacro).
Description and history, not a forecast or advice."""
from __future__ import annotations

import calendar
from datetime import date
from typing import Dict, List, Optional

import pandas as pd

IFRS17 = pd.Timestamp("2026-01-31")   # life insurers' balance sheets moved to IFRS 17 (保險合約負債) from January 2026
GRADES = [("twAAA", "twAAA（最高評等）"), ("twAA", "twAA"), ("twA", "twA"), ("twBBB", "twBBB（投資級最低一級）")]


def _s(rows) -> pd.Series:
    """[[YYYY-MM(-DD), v]] → float Series on a month-end DatetimeIndex (last value of each month)."""
    if not rows:
        return pd.Series(dtype=float)
    try:
        s = pd.Series({pd.Timestamp(p if len(p) > 7 else p + "-01"): v for p, v in rows if isinstance(v, (int, float))}, dtype=float).sort_index()
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)
    return s.groupby(s.index.to_period("M")).last().to_timestamp("M") if len(s) else s


def _ago(s: pd.Series, months: int) -> Optional[float]:
    if not len(s):
        return None
    p = s[s.index <= s.index[-1] - pd.DateOffset(months=months)]
    return float(p.iloc[-1]) if len(p) else None


def _near(s: pd.Series, months: int, tol_days: int = 40) -> Optional[float]:
    """Value about `months` before the last point, only if a point really exists near that date (the TPEx archive has gaps while it fills)."""
    if not len(s):
        return None
    t = s.index[-1] - pd.DateOffset(months=months)
    p = s[(s.index <= t + pd.Timedelta(days=tol_days)) & (s.index >= t - pd.Timedelta(days=tol_days))]
    return float(p.iloc[-1]) if len(p) else None


MIN_CURVE_MONTHS = 60          # percentiles on the TPEx curve archive only once it holds 5 years of months


def _pct(hist: pd.Series, now: float) -> Optional[float]:
    h = hist.dropna()
    return float((h < now).mean() * 100) if len(h) >= 24 else None


def _yoy(s: pd.Series) -> Optional[float]:
    a = _ago(s, 12)
    return (float(s.iloc[-1]) / a - 1) * 100 if a else None


def _ym(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m")


def _tw(d: Dict, k: str) -> pd.Series:
    return _s((d.get("cbc") or {}).get(k))


def _nd(d: Dict, k: str) -> pd.Series:
    return _s((d.get("ndc") or {}).get(k))


def _curves(d: Dict) -> pd.DataFrame:
    """One row per month (month-end TPEx files + the latest daily snapshot): gov 2/5/10y and corporate 5y by grade, in %."""
    rows = {}
    for k, v in (d.get("hist") or {}).items():
        rows[pd.Timestamp(k + "-01") + pd.offsets.MonthEnd(0)] = v
    daily = d.get("daily") or {}
    for k in sorted(daily):                                     # the latest snapshot of each month replaces its month-end file
        rows[pd.Timestamp(k) + pd.offsets.MonthEnd(0)] = daily[k]
    out = []
    for ts in sorted(rows):
        v = rows[ts]
        g, c = v.get("gov") or {}, v.get("corp") or {}
        r = {"ts": ts, "g2": g.get("2"), "g5": g.get("5"), "g10": g.get("10")}
        for gr, _zh in GRADES:
            r[gr] = (c.get(gr) or {}).get("60")
        out.append(r)
    return pd.DataFrame(out).set_index("ts").astype(float) if out else pd.DataFrame()


def _state(pct: Optional[float], chg3: Optional[float], chg_pct: Optional[float]) -> str:
    """Taiwan spreads are dealer quotes and move little, so "rapid" is judged against Taiwan's own history of 3-month moves."""
    if pct is None:                                      # too little history to rank: unknown, not "normal"
        return "資料不足"
    if chg3 is not None and chg3 > 0 and chg_pct is not None and chg_pct >= 90 and (pct or 0) >= 50:
        return "急速擴大"
    if pct is not None and pct >= 80:
        return "緊張"
    if pct is not None and pct <= 20:
        return "利差偏低"
    return "正常"


# ------------------------------------------------------------------ 台灣債市
def gov(d: Dict, us10: Optional[float] = None) -> Optional[Dict]:
    daily = d.get("daily") or {}
    last = sorted(daily)[-1] if daily else None
    cur = dict(daily[last]["gov"]) if last else {}
    asof = last
    hist10 = _tw(d, "tw10y")
    if not cur and len(hist10):
        cur, asof = {"10": float(hist10.iloc[-1])}, _ym(hist10.index[-1])
    if not cur.get("10"):
        return None
    now10 = float(cur["10"])
    past = hist10[hist10.index < pd.Timestamp(asof[:7] + "-01")] if len(hist10) else hist10
    yr = past[past.index <= pd.Timestamp(asof[:7] + "-01") - pd.DateOffset(months=11)] if len(past) else past
    y1 = float(yr.iloc[-1]) if len(yr) else None                # the month a year before today's snapshot
    cv = _curves(d)
    slope = None
    if cur.get("2") is not None:
        slope = {"now": (now10 - float(cur["2"])) * 100}
        if len(cv) and {"g10", "g2"} <= set(cv.columns):
            sl = ((cv["g10"] - cv["g2"]) * 100).dropna()
            slope.update({"pct": _pct(sl.iloc[:-1], slope["now"]) if len(sl) >= MIN_CURVE_MONTHS else None, "since": cv.index[0].strftime("%Y"), "n": len(sl)})
    disc = _tw(d, "disc")
    move = None
    if len(disc) > 2:
        ch = disc.diff().fillna(0)
        nz = ch[ch != 0]
        if len(nz):
            move = {"date": _ym(nz.index[-1]), "by": float(nz.iloc[-1]) * 100, "months": int(len(disc[disc.index > nz.index[-1]]))}
    call = _tw(d, "call")
    out_ = _tw(d, "gov_out")
    return {"asof": asof, "curve": {k: float(v) for k, v in cur.items()}, "now10": now10, "chg1y": None if y1 is None else now10 - y1,
            "pct10": _pct(past, now10), "since10": past.index[0].strftime("%Y") if len(past) else None, "hi10": float(past.max()) if len(past) else None,
            "slope": slope, "disc": float(disc.iloc[-1]) if len(disc) else None, "disc_move": move, "disc_asof": _ym(disc.index[-1]) if len(disc) else None,
            "call": float(call.iloc[-1]) if len(call) else None, "us10": us10, "gap_us": None if us10 is None else us10 - now10,
            "gov_out": float(out_.iloc[-1]) / 1e6 if len(out_) else None, "gov_out_yoy": _yoy(out_), "out_asof": _ym(out_.index[-1]) if len(out_) else None}


# ------------------------------------------------------------------ 台灣公司債
def corp(d: Dict) -> Optional[Dict]:
    cv = _curves(d)
    if not len(cv) or "g5" not in cv.columns or pd.isna(cv["g5"].iloc[-1]):
        return None
    last = cv.iloc[-1]
    rows = []
    for gr, zh in GRADES:
        if gr not in cv.columns or pd.isna(last.get(gr)):
            continue
        sp = ((cv[gr] - cv["g5"]) * 100).dropna()
        now = float(sp.iloc[-1])
        m3 = _near(sp, 3)
        chg3 = None if m3 is None else now - m3
        pct = _pct(sp.iloc[:-1], now) if len(sp) >= MIN_CURVE_MONTHS else None
        d3 = (sp - sp.shift(3)).dropna()
        chg_pct = _pct(d3.iloc[:-1], chg3) if chg3 is not None and len(d3) >= MIN_CURVE_MONTHS else None
        y1 = _near(cv[gr].dropna(), 12)
        rows.append({"k": gr, "zh": zh, "y": float(last[gr]), "y_1y": None if y1 is None else float(last[gr]) - y1, "spread": now,
                     "chg3": chg3, "pct": pct, "n": len(sp), "since": sp.index[0].strftime("%Y-%m"), "chg_pct": chg_pct,
                     "state": _state(pct, chg3, chg_pct)})
    if not rows:
        return None
    tier = None
    if {"twAAA", "twBBB"} <= set(cv.columns):
        t = ((cv["twBBB"] - cv["twAAA"]) * 100).dropna()
        if len(t):
            t3 = _near(t, 3)
            tier = {"now": float(t.iloc[-1]), "pct": _pct(t.iloc[:-1], float(t.iloc[-1])) if len(t) >= MIN_CURVE_MONTHS else None,
                    "chg3": None if t3 is None else float(t.iloc[-1]) - t3}
    o, iss = _tw(d, "corp_out"), _tw(d, "corp_issue")
    i12 = float(iss.iloc[-12:].sum()) if len(iss) >= 12 else None
    i12p = float(iss.iloc[-24:-12].sum()) if len(iss) >= 24 else None
    daily = sorted(d.get("daily") or {})
    return {"asof": cv.index[-1].strftime("%Y-%m"), "date": daily[-1] if daily else cv.index[-1].strftime("%Y-%m"), "filling": len(cv) < MIN_CURVE_MONTHS,
            "g5": float(last["g5"]), "rows": rows, "tier": tier, "months": len(cv), "since": cv.index[0].strftime("%Y-%m"),
            "out": float(o.iloc[-1]) / 1e6 if len(o) else None, "out_yoy": _yoy(o), "out_asof": _ym(o.index[-1]) if len(o) else None,
            "iss12": None if i12 is None else i12 / 1e6, "iss12_chg": (i12 / i12p - 1) * 100 if i12 and i12p else None}


# ------------------------------------------------------------------ 台灣經濟
LIGHT = {"紅": ("🔴", "熱絡"), "黃紅": ("🟠", "轉向熱絡"), "綠": ("🟢", "穩定"), "黃藍": ("🟡", "轉向低迷"), "藍": ("🔵", "低迷")}


def econ(d: Dict) -> Optional[Dict]:
    sc = _nd(d, "light_score")
    lt = (d.get("ndc") or {}).get("light") or []
    if not len(sc) or not lt:
        return None
    cur = lt[-1][1]
    run = 0
    for _p, v in reversed(lt):
        if v != cur:
            break
        run += 1
    lead, coin = _nd(d, "lead"), _nd(d, "coin")

    def six(s):
        a = _ago(s, 6)
        return None if a is None else (float(s.iloc[-1]) / a - 1) * 100

    ex, ip, chip, un, oi = _nd(d, "exports"), _nd(d, "ip"), _nd(d, "chip_tools"), _nd(d, "unemp"), _nd(d, "orders_idx")
    chip3 = None
    if len(chip) >= 15:
        a, b = float(chip.iloc[-3:].sum()), float(chip.iloc[-15:-12].sum())
        chip3 = (a / b - 1) * 100 if b else None
    cpi = _tw(d, "cpi")
    return {"month": lt[-1][0], "light": cur, "ico": LIGHT.get(cur, ("⚪", cur))[0], "mood": LIGHT.get(cur, ("", cur))[1], "score": float(sc.iloc[-1]),
            "score_chg": None if len(sc) < 2 else float(sc.iloc[-1] - sc.iloc[-2]), "run": run, "last12": lt[-12:],
            "red12": sum(1 for _p, v in lt[-12:] if v == "紅"), "blue12": sum(1 for _p, v in lt[-12:] if v == "藍"),
            "lead6": six(lead), "coin6": six(coin), "lead_m": _ym(lead.index[-1]) if len(lead) else None,
            "exports_yoy": _yoy(ex), "ex_m": _ym(ex.index[-1]) if len(ex) else None, "ip_yoy": _yoy(ip), "ip_m": _ym(ip.index[-1]) if len(ip) else None,
            "chip3": chip3, "chip_m": _ym(chip.index[-1]) if len(chip) else None,
            "orders": float(oi.iloc[-1]) if len(oi) else None, "orders_m": _ym(oi.index[-1]) if len(oi) else None,
            "unemp": float(un.iloc[-1]) if len(un) else None, "unemp_chg": None if _ago(un, 12) is None else float(un.iloc[-1]) - _ago(un, 12),
            "cpi": float(cpi.iloc[-1]) if len(cpi) else None, "cpi_m": _ym(cpi.index[-1]) if len(cpi) else None,
            "score_pct": _pct(sc.iloc[:-1], float(sc.iloc[-1])), "since": sc.index[0].strftime("%Y")}


# ------------------------------------------------------------------ 央行與資金
def m1b_test(d: Dict, horizon: int = 6) -> Optional[Dict]:
    """Forward TAIEX returns after months when M1B growth was above vs below M2 growth (1987 onward, overlapping windows)."""
    m1, m2, px = _tw(d, "m1b"), _tw(d, "m2"), _tw(d, "taiex")
    df = pd.concat([m1, m2, px], axis=1, keys=["m1", "m2", "px"]).dropna()
    if len(df) < 120:
        return None
    df["fwd"] = (df["px"].shift(-horizon) / df["px"] - 1) * 100
    t = df.dropna(subset=["fwd"])
    up, dn = t[t["m1"] > t["m2"]], t[t["m1"] <= t["m2"]]
    if len(up) < 24 or len(dn) < 24:
        return None
    return {"h": horizon, "since": df.index[0].strftime("%Y"), "n_up": len(up), "n_dn": len(dn),
            "up_med": float(up["fwd"].median()), "dn_med": float(dn["fwd"].median()), "up_pos": float((up["fwd"] > 0).mean() * 100),
            "dn_pos": float((dn["fwd"] > 0).mean() * 100), "all_med": float(t["fwd"].median())}


def money(d: Dict, twd: Optional[pd.Series] = None) -> Optional[Dict]:
    m1, m2 = _tw(d, "m1b"), _tw(d, "m2")
    if not len(m1) or not len(m2):
        return None
    gap = (m1 - m2).dropna()
    g_now = float(gap.iloc[-1])
    cross = None
    run = 1
    for x in reversed(gap.iloc[:-1].tolist()):
        if (x > 0) != (g_now > 0):
            break
        run += 1
    if run <= 3:
        cross = "黃金交叉" if g_now > 0 else "死亡交叉"
    fx = _tw(d, "fxres")
    npl = _tw(d, "npl")
    fxc = None
    if twd is not None and len(twd) > 70:
        p = twd[twd.index <= twd.index[-1] - pd.Timedelta(days=91)]
        fxc = None if not len(p) else (float(twd.iloc[-1]) / float(p.iloc[-1]) - 1) * 100
    return {"month": _ym(m1.index[-1]), "m1b": float(m1.iloc[-1]), "m2": float(m2.iloc[-1]), "gap": g_now, "run": run, "cross": cross,
            "test": m1b_test(d), "fxres": float(fx.iloc[-1]) / 1e5 if len(fx) else None,       # 百萬美元 → 千億美元
            "fxres_yoy": _yoy(fx), "fx_m": _ym(fx.index[-1]) if len(fx) else None, "npl": float(npl.iloc[-1]) if len(npl) else None,
            "npl_m": _ym(npl.index[-1]) if len(npl) else None,
            "twd": float(twd.iloc[-1]) if twd is not None and len(twd) else None, "twd3m": fxc}


# ------------------------------------------------------------------ 壽險・房市
def insure_house(d: Dict, twd3m: Optional[float] = None) -> Optional[Dict]:
    fo, ta, eq = _tw(d, "life_foreign"), _tw(d, "life_assets"), _tw(d, "life_equity")
    out: Dict = {}
    if len(fo) and len(ta):
        sh = (fo / ta * 100).dropna()
        er = (eq / ta * 100).dropna() if len(eq) else pd.Series(dtype=float)
        e1 = _ago(er, 12) if len(er) else None
        ifrs = len(er) and er.index[-1] >= IFRS17 > er.index[-1] - pd.DateOffset(months=12)
        if ifrs:
            e1 = None                                           # 2026-01 change of accounting: a year-on-year comparison is not like for like
        s1 = None if ifrs or _ago(sh, 12) is None else float(sh.iloc[-1]) - _ago(sh, 12)
        out["life"] = {"month": _ym(sh.index[-1]), "share": float(sh.iloc[-1]), "share_1y": s1,
                       "share_pct": _pct(sh.iloc[:-1], float(sh.iloc[-1])), "since": sh.index[0].strftime("%Y"),
                       "foreign": float(fo.iloc[-1]) / 1e6, "assets": float(ta.iloc[-1]) / 1e6,
                       "eq": float(er.iloc[-1]) if len(er) else None, "eq_1y": None if e1 is None else float(er.iloc[-1]) - e1, "ifrs17": bool(ifrs),
                       "twd3m": twd3m}
    tp = _s(d.get("taipei"))
    if len(tp) > 24:
        out["taipei"] = {"month": _ym(tp.index[-1]), "now": float(tp.iloc[-1]), "yoy": _yoy(tp),
                         "chg3y": None if _ago(tp, 36) is None else (float(tp.iloc[-1]) / _ago(tp, 36) - 1) * 100,
                         "pct": _pct(tp.iloc[:-1], float(tp.iloc[-1])), "since": tp.index[0].strftime("%Y-%m"), "peak": float(tp.max()),
                         "off_peak": (float(tp.iloc[-1]) / float(tp.max()) - 1) * 100}
    my, cy = _tw(d, "mortgage_yoy"), _tw(d, "construct_yoy")
    if len(my):
        out["loans"] = {"month": _ym(my.index[-1]), "mortgage_yoy": float(my.iloc[-1]), "mortgage_yoy_1y": _ago(my, 12),
                        "construct_yoy": float(cy.iloc[-1]) if len(cy) else None}
    return out or None


# ------------------------------------------------------------------ 數據日曆 (approximate, from each release's usual timing)
def _third_thursday(y: int, m: int) -> date:
    c = calendar.Calendar()
    th = [x for x in c.itermonthdates(y, m) if x.month == m and x.weekday() == 3]
    return th[2]


def calendar_rows(d: Dict, today: Optional[date] = None) -> List[Dict]:
    today = today or date.today()

    def nxt(day: int) -> date:
        y, m = today.year, today.month
        x = date(y, m, min(day, calendar.monthrange(y, m)[1]))
        if x < today:
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
            x = date(y, m, min(day, calendar.monthrange(y, m)[1]))
        while x.weekday() >= 5:                                 # releases fall on working days
            x = date.fromordinal(x.toordinal() + 1)
        return x

    def latest(rows) -> Optional[str]:
        return rows[-1][0] if rows else None

    cbc, ndc = d.get("cbc") or {}, d.get("ndc") or {}
    rows = [{"zh": "物價指數 CPI（主計總處）", "when": nxt(6), "last": latest(cbc.get("cpi")), "why": "通膨高低決定央行要不要升息"},
            {"zh": "海關進出口（財政部）", "when": nxt(8), "last": latest(ndc.get("exports")), "why": "台灣經濟最主要的引擎"},
            {"zh": "外銷訂單（經濟部）", "when": nxt(20), "last": latest(ndc.get("orders_idx")), "why": "接單是出口的前一步，領先 1～3 個月"},
            {"zh": "金融統計 M1B／M2（央行）", "when": nxt(25), "last": latest(cbc.get("m1b")), "why": "市場資金是否充沛"},
            {"zh": "景氣對策信號燈號（國發會）", "when": nxt(27), "last": latest(ndc.get("light")), "why": "一個燈號總結整體景氣"}]
    q = [m for m in (3, 6, 9, 12)]
    y = today.year
    cands = [_third_thursday(y, m) for m in q] + [_third_thursday(y + 1, 3)]
    rows.append({"zh": "央行理監事會（利率決策）", "when": next(x for x in cands if x >= today), "last": latest(cbc.get("disc")), "why": "決定台灣的基準利率與房貸管制"})
    return sorted(rows, key=lambda r: r["when"])


# ------------------------------------------------------------------ 一句話 + 白話
def read(r: Dict) -> Dict:
    g, c, e, m, ih = r.get("gov"), r.get("corp"), r.get("econ"), r.get("money"), r.get("ih") or {}
    parts, imp = [], []
    if e:
        parts.append(f"景氣燈號{e['ico']}{e['light']}燈（{e['month']}，{e['score']:.0f} 分）" + ("，" + f"已連續 {e['run']} 個月" if e["run"] >= 3 else ""))
    if g:
        p10 = g.get("pct10")
        lvl = ("歷史位置資料不足" if p10 is None else "在歷史低檔" if p10 <= 20 else "在歷史高檔" if p10 >= 80 else "在歷史中間")
        parts.append(f"台灣 10 年期公債利率 {g['now10']:.2f}%（{lvl}）")
    if c:
        bbb = next((x for x in c["rows"] if x["k"] == "twBBB"), None)
        if bbb:
            parts.append({"急速擴大": "公司債利差急速擴大", "緊張": "公司債利差偏高", "利差偏低": "公司債利差偏低（違約補償偏低，不等於安全）", "正常": "公司債利差正常",
                          "資料不足": "公司債利差歷史資料不足，暫不判斷"}[bbb["state"]])
    head = "一句話看懂：" + "；".join(parts) + "。"
    if e:
        if e["light"] in ("紅", "黃紅"):
            imp.append(f"景氣燈號偏熱（{e['red12']} / 12 個月亮紅燈）：出口與生產很強，但通常也代表央行比較不會降息，過熱時要留意反轉。")
        elif e["light"] in ("藍", "黃藍"):
            imp.append("景氣燈號偏冷：出口或生產轉弱，企業獲利預期可能下修；歷史上藍燈常出現在景氣谷底附近。")
        if e.get("exports_yoy") is not None and e.get("chip3") is not None and e["exports_yoy"] > 15 and e["chip3"] > 0:
            imp.append(f"出口年增 {e['exports_yoy']:.0f}%、半導體設備進口 3 個月年增 {e['chip3']:.0f}%：AI 與先進製程仍在擴產，台灣經濟高度集中在這條供應鏈上，美國 AI 投資一放緩，台灣會很快感受到。")
        if e.get("orders") is not None and e["orders"] < 50 and (e.get("exports_yoy") or 0) > 0:
            imp.append(f"外銷訂單動向指數 {e['orders']:.1f}（低於 50）：接單的廠商家數在減少，和出口還在成長的現況不一致，值得觀察是否只靠少數大廠撐住。")
    if g and g.get("gap_us") is not None:
        imp.append(f"美國 10 年期比台灣高 {g['gap_us']:.2f} 個百分點：台灣的錢有強烈動機往美國債券跑（壽險業就是最大的一群），這也是新台幣容易受美元走勢影響的原因。")
    if m:
        if m.get("cross"):
            imp.append(f"M1B 年增率{'超過' if m['gap'] > 0 else '跌破'} M2（{m['cross']}）：{'活期資金增加，市場資金偏寬鬆' if m['gap'] > 0 else '活期資金相對減少，追價的資金變少'}；"
                       "這是台股常看的資金指標，但歷史上只是背景，不是買賣訊號。")
        if m.get("twd3m") is not None and m["twd3m"] <= -3:
            imp.append(f"新台幣 3 個月升值 {abs(m['twd3m']):.1f}%：出口商與持有大量美元資產的壽險業帳面會受傷。")
        elif m.get("twd3m") is not None and m["twd3m"] >= 3:
            imp.append(f"新台幣 3 個月貶值 {m['twd3m']:.1f}%：常和外資賣超台股同時發生。")
    tp = ih.get("taipei")
    if tp and tp.get("yoy") is not None:
        imp.append(f"臺北市房價指數年{'增' if tp['yoy'] >= 0 else '減'} {abs(tp['yoy']):.1f}%（{tp['month']}）"
                   + ("，離高點不遠" if tp["off_peak"] > -3 else f"，比高點低 {abs(tp['off_peak']):.0f}%") + "；央行選擇性信用管制持續時，房貸成長會被壓住。")
    if c and c.get("tier") and c["tier"].get("pct") is not None and c["tier"]["pct"] >= 80:
        imp.append(f"BBB 和 AAA 的利率差 {c['tier']['now']:.0f} bp，在歷史高檔：市場開始區分好壞公司，體質較弱的企業借錢變貴。")
    return {"head": head, "imp": imp}


def build(eng) -> Dict:
    from ..data import twmacro as TM
    d = TM.load()
    if not d.get("cbc") and not d.get("daily"):
        return {"available": False}
    us10 = None
    try:
        s = eng.fred.get("DGS10").dropna()
        us10 = float(s.iloc[-1]) if len(s) else None
    except Exception:  # noqa: BLE001
        pass
    twd = None
    try:
        h = eng.market.history
        if h is not None and "TWD=X" in h.columns:
            twd = h["TWD=X"].dropna()
            twd = twd[twd > 0]
    except Exception:  # noqa: BLE001
        pass
    out = {"available": True, "ts": d.get("ts"), "cbc_updated": d.get("cbc_updated") or {}}
    for k, f in (("gov", lambda: gov(d, us10)), ("corp", lambda: corp(d)), ("econ", lambda: econ(d)), ("money", lambda: money(d, twd))):
        try:
            out[k] = f()
        except Exception:  # noqa: BLE001
            out[k] = None
    try:
        out["ih"] = insure_house(d, (out.get("money") or {}).get("twd3m"))
    except Exception:  # noqa: BLE001
        out["ih"] = None
    out["cal"] = calendar_rows(d)
    out["read"] = read(out)
    return out
