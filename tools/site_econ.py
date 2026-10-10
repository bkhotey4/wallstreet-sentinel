"""財經日曆＋科技財報 兩個分頁的區塊（build_site 用）。"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from tools.site_sections import _bar
from tools.sitekit import T, card, cls, esc, num

WD = "一二三四五六日"
DIR_CLS = {"hot": "dhot", "cool": "dcool", "inline": "dinl"}
STARS = {3: "★★★", 2: "★★", 1: "★"}


def _wd(d: str) -> str:
    try:
        return "週" + WD[date.fromisoformat(d).weekday()]
    except ValueError:
        return ""


def _days_to(d: str, today: str) -> Optional[int]:
    try:
        return (date.fromisoformat(d) - date.fromisoformat(today)).days
    except ValueError:
        return None


def _dir_badge(e: Dict) -> str:
    if not e.get("dir_label"):
        return ""
    return f'<span class="dbadge {DIR_CLS.get(e["dir"], "")}">{T(e["dir_label"][0], e["dir_label"][1])}</span>'


def _prim(e: Dict) -> Dict:
    return e["rows"][0] if e.get("rows") else {}


def _val_line(e: Dict) -> str:
    p = _prim(e)
    if not p:
        return f'<span class="muted small">{T("無數值（看內容與語氣）", "no figure — content and tone")}</span>'
    act = (f'{T("公布", "Actual")} <b>{esc(p["actual"])}</b>　' if p.get("actual") else "")
    src = f'<span class="muted small">{T("（FF）", "(FF)")}</span>' if p.get("cons_src") == "ff" else ""
    return (f'<span class="small">{esc(p["label"])}：{act}{T("預期", "Cons.")} <b>{esc(p["cons"] or "—")}</b>{src}　'
            f'{T("前值", "Prev.")} {esc(p["prev"] or "—")}</span>')


# ============================================================ 財經日曆 tab
def sec_econ_week(eng) -> str:
    ev = getattr(eng, "econ_view", None) or {}
    if not ev.get("available"):
        return card("本週重要經濟數據", "This week's key releases", f'<p class="muted">{T("經濟日曆資料暫時取不到", "Calendar unavailable")}</p>', "wide")
    today = ev["asof"]
    byid = {e["id"]: e for e in ev["events"]}
    recent = [e for e in ev["events"] if e["released"] and e["imp"] >= 2 and _days_to(e["date"], today) is not None
              and -4 <= _days_to(e["date"], today) < 0]
    items = recent[-3:] + [byid[i] for i in ev.get("week", []) if i in byid]
    seen, cards = set(), []
    for e in items:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        dd = _days_to(e["date"], today)
        when = (T("已公布", "Released") if e["released"] else T("今天", "Today") if dd == 0 else T("明天", "Tomorrow") if dd == 1
                else T(f"{dd} 天後", f"in {dd}d"))
        sep = f' <span class="pill">{T("含點陣圖", "with dots")}</span>' if e.get("sep") else ""
        cards.append(f'<a class="wk imp{e["imp"]}{" done" if e["released"] else ""}" href="#ev-{esc(e["id"].replace(":", "-"))}" data-ev="{esc(e["id"])}">'
                     f'<div class="wkh"><span class="stars">{STARS[e["imp"]]}</span><b>{T(e["zh"], e["en"])}</b>{sep}</div>'
                     f'<div class="small muted">{esc(e["date"][5:])} {_wd(e["date"])}・{T("台北", "Taipei")} {esc(e.get("tpe") or "—")}・{when}</div>'
                     f'<div>{_val_line(e)}</div>{_dir_badge(e)}</a>')
    body = f'<div class="wkgrid">{"".join(cards)}</div>' if cards else f'<p class="muted">{T("未來 7 天沒有重要數據", "No key releases in the next 7 days")}</p>'
    note = T("時間以台北時間為主（美東 08:30 的數據＝台北晚上 8:30，冬令時間 9:30；FOMC 美東 14:00＝台北隔天凌晨 2:00／3:00）。"
             "預期值來自 Nasdaq 經濟日曆（缺的時候用 ForexFactory 補，標示 FF）。點卡片跳到詳細的影響劇本。",
             "Times in Taipei; consensus from Nasdaq (ForexFactory when missing). Click a card for the scenarios.")
    return card("本週重要經濟數據", "This week's key releases", body + f'<p class="note">{note}</p>', "wide")


def _fed_proxy(eng, rate: Optional[float]) -> str:
    fr = getattr(eng, "fred", None)
    s = (getattr(fr, "series", {}) or {}).get("DGS2") if fr is not None else None
    if rate is None or s is None or not len(s.dropna()):
        return ""
    y2 = float(s.dropna().iloc[-1])
    mid = rate - 0.125
    gap = mid - y2
    if abs(gap) < 0.15:
        txt = T(f"2 年期公債殖利率 {y2:.2f}% 與政策利率中點 {mid:.2f}% 接近：市場大致預期未來一年利率持平。",
                f"2y {y2:.2f}% ≈ policy midpoint {mid:.2f}%: roughly flat path priced.")
    elif gap > 0:
        txt = T(f"2 年期公債殖利率 {y2:.2f}% 低於政策利率中點 {mid:.2f}% 約 {gap * 100:.0f}bp：粗略代表市場預期未來一到兩年再降息約 {gap / 0.25:.0f} 碼。",
                f"2y {y2:.2f}% is {gap * 100:.0f}bp below the midpoint: roughly {gap / 0.25:.0f} more cuts priced.")
    else:
        txt = T(f"2 年期公債殖利率 {y2:.2f}% 高於政策利率中點 {mid:.2f}% 約 {-gap * 100:.0f}bp：市場傾向認為利率會維持高檔或再升息。",
                f"2y {y2:.2f}% is above the midpoint: hikes / higher-for-longer priced.")
    return f'<p class="small">{txt}<span class="muted">{T("（粗估，不是聯邦基金期貨機率）", " (rough proxy)")}</span></p>'


def sec_fomc(eng) -> str:
    ev = getattr(eng, "econ_view", None) or {}
    ec = getattr(eng, "econ", None)
    if not ev.get("available"):
        return ""
    today = ev["asof"]
    past = [e for e in ev["events"] if e["key"] == "fomc" and e["released"] and e.get("rows")]
    stats = (ev.get("stats") or {}).get("fomc") or {}
    last_any = None
    for e in sorted(ev["events"], key=lambda x: x["date"]):
        if e["key"] == "fomc" and e["released"] and e.get("rows"):
            last_any = e
    rate = _prim(last_any).get("a") if last_any else None
    if rate is None:                                 # outside the 7-day window → use the history stats' latest row
        lr = (stats.get("last") or [{}])[0].get("row") or {}
        rate = lr.get("a")
    nx = ev.get("next_fomc")
    parts = []
    if nx:
        dd = _days_to(nx["date"], today)
        c = _prim(nx).get("c")
        exp = ""
        if c is not None and rate is not None:
            exp = T("市場預期：維持不變" if abs(c - rate) < 0.01 else f"市場預期：{'降' if c < rate else '升'}息至 {c:.2f}%",
                    "Consensus: hold" if abs(c - rate) < 0.01 else f"Consensus: {c:.2f}%")
        parts.append(f'<div class="fomc"><div class="big">{esc(nx["date"][5:])} {_wd(nx["date"])}</div>'
                     f'<div>{T("下次 FOMC 決議（美東 14:00）", "Next FOMC decision (14:00 ET)")}・{T("台北", "Taipei")} {esc(nx.get("tpe") or "—")}'
                     f'・<b>{T(f"還有 {dd} 天", f"in {dd} days")}</b>'
                     + (f' <span class="pill">{T("有經濟預測與點陣圖", "SEP + dot plot")}</span>' if nx.get("sep") else "") + "</div>"
                     f'<div>{T("目前政策利率上限", "Current upper bound")} <b>{num(rate, 2)}%</b>　{exp}</div></div>')
    parts.append(_fed_proxy(eng, rate))
    meets = [m for m in (getattr(ec, "fomc", None) or []) if m["date"] >= today][:8]
    if meets:
        parts.append('<p class="small">' + T("之後的會議：", "Upcoming meetings: ") + "、".join(
            f'{esc(m["date"][5:])}{"＊" if m.get("sep") else ""}' for m in meets) + T("（＊＝有點陣圖）", " (* = dots)") + "</p>")
    sc = (ev["events"] and next((e["scen"] for e in ev["events"] if e["key"] == "fomc" and e.get("scen")), None))
    if sc:
        parts.append(_scen_block("fomc", sc, None))
    if stats.get("last"):
        parts.append(_hist_block(stats))
    return card("FOMC 聯準會利率決議", "FOMC", "".join(parts), "wide")


def _scen_block(key: str, sc: Dict, cur: Optional[str]) -> str:
    cols = []
    for d, zh, en in (("hot", "若高於預期／偏鷹", "If hotter / hawkish"), ("inline", "若符合預期", "If in line"), ("cool", "若低於預期／偏鴿", "If cooler / dovish")):
        if key in ("nfp", "gdp", "retail", "ism_mfg", "ism_svc", "jolts", "umich", "durable", "indpro"):
            zh = {"hot": "若強於預期", "inline": "若符合預期", "cool": "若弱於預期"}[d]
        if key == "claims":
            zh = {"hot": "若申請人數少於預期", "inline": "若符合預期", "cool": "若申請人數多於預期"}[d]
        on = " on" if cur == d else ""
        tag = f' <span class="pill inz">{T("這次", "this time")}</span>' if cur == d else ""
        cols.append(f'<div class="scn {DIR_CLS[d]}{on}"><h5>{T(zh, en)}{tag}</h5><p>{T(sc[d]["zh"], sc[d]["en"])}</p></div>')
    return (f'<p class="small"><b>{T("為什麼重要", "Why it matters")}：</b>{T(sc["why"]["zh"], sc["why"]["en"])}</p>'
            f'<div class="scen">{"".join(cols)}</div>'
            f'<p class="small"><b>{T("接下來要看", "Watch")}：</b>{T(sc["watch"]["zh"], sc["watch"]["en"])}</p>')


def _mv(v, kind: str) -> str:
    if v is None:
        return '<td class="r muted">—</td>'
    return f'<td class="r {cls(v)}">{num(v, 1 if kind == "bp" else 2, sign=True)}{"bp" if kind == "bp" else "%"}</td>'


def _hist_block(st: Dict) -> str:
    from wsb.analytics.macro_events import REACT
    by = st.get("by") or {}
    lab = {"hot": ("高於預期／偏鷹", "Hot / hawkish"), "inline": ("符合預期", "In line"), "cool": ("低於預期／偏鴿", "Cool / dovish")}
    rows = "".join(f'<tr><td>{T(*lab[d])}</td><td class="r">{by[d]["n"]}</td>' + "".join(_mv(by[d].get(t), k) for t, _z, _e, k in REACT) + "</tr>"
                   for d in ("hot", "inline", "cool") if d in by)
    head = "".join(f'<th class="r">{T(z, e)}</th>' for _t, z, e, _k in REACT)
    ratio = (T(f"這類數據公布當天，那指 100 平均波動是平常的 {st['absratio']:.1f} 倍（平均 ±{st['abs_ndx']:.2f}%）。",
               f"Release-day Nasdaq-100 moves average {st['absratio']:.1f}× a normal day.") if st.get("absratio") else "")
    last = "".join(f'<li>{esc(x["date"])}：{esc((x.get("row") or {}).get("actual", ""))}（{T("預期", "cons.")} {esc((x.get("row") or {}).get("cons", "") or "—")}）'
                   f' → 那指 {num((x.get("move") or {}).get("^NDX"), 2, sign=True, pct=True)}、10 年 {num((x.get("move") or {}).get("^TNX"), 1, sign=True)}bp</li>'
                   for x in st.get("last", [])[:6])
    n = st["n"]
    return (f'<details class="hist"><summary class="small">{T(f"過去同類數據公布當天的市場反應（{n} 次）", f"Past release-day reactions (n={n})")}</summary>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("結果", "Outcome")}</th><th class="r">{T("次數", "n")}</th>{head}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p class="small muted">{ratio}{T("樣本只有快取中的歷史（約兩年），只是過去平均、不代表這次。", "Small in-sample averages.")}</p>'
            f'<ul class="small lines">{last}</ul></details>')


def _ev_row(e: Dict, today: str) -> str:
    rows = "".join(f'<tr><td>{esc(r["label"])}</td><td class="r"><b>{esc(r["actual"] or "—")}</b></td><td class="r">{esc(r["cons"] or "—")}</td>'
                   f'<td class="r muted">{esc(r["prev"] or "—")}</td><td class="r">'
                   f'{num(r.get("diff"), 2, sign=True) if r.get("diff") is not None else ""}</td></tr>' for r in e.get("rows", []))
    tbl = (f'<div class="scroll"><table class="mini"><thead><tr><th></th><th class="r">{T("公布", "Actual")}</th><th class="r">{T("預期", "Cons.")}</th>'
           f'<th class="r">{T("前值", "Prev.")}</th><th class="r">{T("差距", "Diff")}</th></tr></thead><tbody>{rows}</tbody></table></div>' if rows else "")
    mv = e.get("move") or {}
    mvl = ""
    if any(v is not None for v in mv.values()):
        from wsb.analytics.macro_events import REACT
        mvl = ('<p class="small"><b>' + T("公布當天收盤", "Release-day close") + "：</b>" + "　".join(
            f'{T(z, en)} <span class="{cls(mv.get(t))}">{num(mv.get(t), 1 if k == "bp" else 2, sign=True)}{"bp" if k == "bp" else "%"}</span>'
            for t, z, en, k in REACT) + "</p>")
    ai = ""
    if e.get("ai"):
        ai = (f'<div class="ainote"><b>{T("AI 解讀", "AI read")}</b><span class="muted small">（{esc(e["ai"].get("engine", ""))}）</span>'
              f'<p>{esc(e["ai"]["text"]).replace(chr(10), "<br>")}</p></div>')
    ctx = f'<p class="small"><b>{T("目前背景", "Backdrop")}：</b>{esc(e["ctx"])}</p>' if e.get("ctx") else ""
    body = tbl + mvl + ai + ctx + (_scen_block(e["key"], e["scen"], e.get("dir")) if e.get("scen") else "") + (_hist_block(e["stats"]) if e.get("stats") else "")
    dd = _days_to(e["date"], today)
    st = (_dir_badge(e) if e["released"] and e.get("dir") else
          f'<span class="pill">{T("已公布", "Out")}</span>' if e["released"] else
          f'<span class="pill">{T("今天", "today")}</span>' if dd == 0 else "")
    q = esc((e["zh"] + " " + e["en"]).lower())
    return (f'<details class="ev imp{e["imp"]}" id="ev-{esc(e["id"].replace(":", "-"))}" data-imp="{e["imp"]}" data-q="{q}">'
            f'<summary><span class="tm">{esc((e.get("tpe") or "")[6:] or "—")}<span class="muted small"> {T("台北", "TPE")}</span></span>'
            f'<span class="stars">{STARS[e["imp"]]}</span><b class="evn">{T(e["zh"], e["en"])}</b>'
            + (f'<span class="pill">{T("點陣圖", "dots")}</span>' if e.get("sep") else "") +
            f'<span class="evv">{_val_line(e)}</span>{st}</summary><div class="evb">{body}</div></details>')


def sec_econ_list(eng) -> str:
    ev = getattr(eng, "econ_view", None) or {}
    if not ev.get("available"):
        return ""
    today = ev["asof"]
    by: Dict[str, List[Dict]] = {}
    for e in ev["events"]:
        by.setdefault(e["date"], []).append(e)
    days = []
    for d in sorted(by):
        lab = T("今天", "Today") if d == today else ""
        days.append(f'<div class="evday{" today" if d == today else ""}{" past" if d < today else ""}" data-d="{d}"><h4>{esc(d)} {_wd(d)} '
                    f'<span class="muted small">{T("美東日期", "US date")}</span> {f"<span class=pill>{lab}</span>" if lab else ""}</h4>'
                    + "".join(_ev_row(e, today) for e in by[d]) + "</div>")
    ctl = (f'<div class="fmctl"><select class="btn evimp"><option value="2" data-en="Key (★★+)">重要（★★ 以上）</option>'
           f'<option value="3" data-en="Top (★★★)">最重要（★★★）</option><option value="1" data-en="All">全部</option></select>'
           f'<input type="search" class="btn evq" placeholder="搜尋，例如 CPI、非農、FOMC" aria-label="search">'
           f'<label class="small muted"><input type="checkbox" class="evpast"> {T("顯示過去 7 天", "Show the last 7 days")}</label></div>')
    note = T(f"資料：Nasdaq 經濟日曆（預期值、前值、公布值）、ForexFactory（本週預期補值）、聯準會官網（會議日期）。影響劇本是依總經傳導機制寫成的判斷框架，"
             f"不是預測——實際反應取決於市場事先定價了什麼。歷史反應用快取中的 {ev.get('n_hist', 0)} 筆過去公布（自 {ev.get('hist_from') or '—'} 起）計算。"
             "本頁不構成投資建議。", "Sources: Nasdaq, ForexFactory, federalreserve.gov. Scenarios are a framework, not forecasts. Not advice.")
    return card("美國經濟日曆（未來約 45 天）", "US economic calendar (next ~45 days)", ctl + f'<div class="evlist">{"".join(days)}</div><p class="note">{note}</p>', "wide")


def sec_earn_cal(eng) -> str:
    te = getattr(eng, "techearn", None) or {}
    cal = (te.get("calendar") or {}) if te else {}
    if not cal.get("up") and not cal.get("past"):
        return ""
    def tm(x):
        return {"pre": T("盤前", "pre-mkt"), "after": T("盤後", "after close")}.get(x, T("未定", "tbd"))
    def nm(x):
        th = f'<span class="thc">{esc(x["theme"])}</span>' if x.get("theme") else ""
        return f'<td class="nw"><b>{esc(x["name"])}</b><span class="tk">{esc(x["sym"])}</span>{th}</td>'
    up = "".join(f'<tr data-k="{"t" if x["tech"] else "c" if x["cur"] else "o"}"><td class="nw">{esc(x["date"][5:])} {_wd(x["date"])}</td><td>{tm(x["time"])}</td>{nm(x)}'
                 f'<td class="r">{num(x["eps_f"], 2)}</td><td class="r muted">{num(x["n_est"], 0)}</td><td class="r muted">{num(x["eps_ly"], 2)}</td>'
                 f'<td class="r {cls(x["g"])}">{num(x["g"], 0, sign=True, pct=True)}</td></tr>' for x in cal.get("up", [])[:120])
    past = "".join(f'<tr data-k="{"t" if x["tech"] else "c" if x["cur"] else "o"}"><td class="nw">{esc(x["date"][5:])}</td>{nm(x)}'
                   f'<td class="r">{num(x["eps"], 2)}</td><td class="r muted">{num(x["eps_f"], 2)}</td><td class="r {cls(x["surp"])}">{num(x["surp"], 1, sign=True, pct=True)}</td>'
                   f'<td class="r {cls(x.get("react"))}">{num(x.get("react"), 1, sign=True, pct=True)}</td></tr>' for x in cal.get("past", [])[:80])
    sel = (f'<select class="btn ecf"><option value="" data-en="All">全部（精選池＋市值 200 億美元以上）</option><option value="tc" data-en="Curated">只看精選池</option>'
           f'<option value="t" data-en="Tech &amp; semis">只看科技／半導體</option></select>')
    body = (f'<div class="fmctl">{sel}</div><h4>{T("即將公布（21 天內）", "Upcoming (21 days)")}</h4>'
            f'<div class="scroll"><table class="mini ecal"><thead><tr><th>{T("日期", "Date")}</th><th>{T("時段", "Time")}</th><th>{T("公司", "Company")}</th>'
            f'<th class="r">{T("EPS 預期", "EPS est.")}</th><th class="r">{T("分析師數", "# est.")}</th><th class="r">{T("去年同期", "Last yr")}</th>'
            f'<th class="r">{T("預期年增", "Implied growth")}</th></tr></thead><tbody>{up}</tbody></table></div>'
            f'<h4>{T("最近 7 天已公布", "Reported in the last 7 days")}</h4><div class="scroll"><table class="mini ecal"><thead><tr><th>{T("日期", "Date")}</th>'
            f'<th>{T("公司", "Company")}</th><th class="r">{T("EPS 實際", "EPS")}</th><th class="r">{T("預期", "Est.")}</th><th class="r">{T("驚喜", "Surprise")}</th>'
            f'<th class="r">{T("前後兩日股價", "2-day move")}</th></tr></thead><tbody>{past}</tbody></table></div>')
    note = T("資料：Nasdaq 財報日曆（EPS 預期來自 Zacks 彙整）。日期為美東；盤後公布的股價反應出現在隔天。兩日股價＝財報日前一個交易日收盤到之後第一個交易日收盤（只算精選池）。",
             "Source: Nasdaq earnings calendar (Zacks consensus). US dates.")
    return card("美股財報日曆", "US earnings calendar", body + f'<p class="note">{note}</p>', "wide")


def sec_econ_mini(eng) -> str:
    ev = getattr(eng, "econ_view", None) or {}
    if not ev.get("available"):
        return ""
    today = ev["asof"]
    up = [e for e in ev["events"] if not e["released"] and e["imp"] >= 2 and e["date"] >= today][:6]
    if not up:
        return ""
    lis = "".join(f'<li><span class="dt">{esc(e["date"][5:])} {_wd(e["date"])}</span><span class="stars">{STARS[e["imp"]]}</span>'
                  f'{T(e["zh"], e["en"])} <span class="muted small">{T("台北", "TPE")} {esc((e.get("tpe") or "")[6:])}'
                  + (f'・{T("預期", "cons.")} {esc(_prim(e).get("cons"))}' if _prim(e).get("cons") else "") + "</span></li>" for e in up)
    return card("接下來的重要經濟數據", "Next key releases", f'<ul class="cal">{lis}</ul><p class="note"><a href="#econ" class="golink" data-p="econ">'
                + T("看影響劇本與預期 →", "Scenarios and consensus →") + "</a></p>", "span4")


# ============================================================ 科技財報 tab
def _qchart(series: List[Dict]) -> str:
    """Small bar (revenue) + line (gross margin) chart for up to 8 quarters."""
    s = [x for x in series if x.get("rev")]
    if len(s) < 3:
        return ""
    w, h, pad = 300, 96, 14
    mx = max(x["rev"] for x in s)
    bw = (w - 2 * pad) / len(s)
    bars, labs = [], []
    for i, x in enumerate(s):
        bh = (x["rev"] / mx) * (h - 34)
        bx = pad + i * bw + bw * 0.15
        bars.append(f'<rect x="{bx:.1f}" y="{h - 16 - bh:.1f}" width="{bw * 0.7:.1f}" height="{bh:.1f}" class="qb"/>')
        if i in (0, len(s) - 1):
            labs.append(f'<text x="{bx + bw * 0.35:.1f}" y="{h - 4}" class="ql" text-anchor="middle">{esc(x["end"][2:7].replace("-", "/"))}</text>')
    gm = [(i, x["gm"]) for i, x in enumerate(s) if x.get("gm") is not None]
    line = ""
    if len(gm) >= 2:
        lo, hi = min(v for _, v in gm), max(v for _, v in gm)
        hi = hi if hi > lo else lo + 1
        pts = " ".join(f"{pad + i * bw + bw / 2:.1f},{4 + (1 - (v - lo) / (hi - lo)) * 26:.1f}" for i, v in gm)
        line = (f'<polyline points="{pts}" class="qg"/><text x="{w - 2}" y="10" class="ql" text-anchor="end">'
                f'GM {gm[-1][1]:.1f}%</text>')
    return f'<svg class="qchart" viewBox="0 0 {w} {h}" role="img" aria-label="quarterly revenue">{"".join(bars)}{line}{"".join(labs)}</svg>'


def _sc_color(v: Optional[float]) -> str:
    if v is None:
        return "#6b7280"
    return "#2fbf71" if v >= 65 else "#c9a227" if v >= 45 else "#ec835a"


def sec_tech_season(eng) -> str:
    te = getattr(eng, "techearn", None) or {}
    if not te.get("available"):
        return card("科技／半導體財報季", "Tech earnings season", f'<p class="muted">{T("財報資料暫時取不到", "Earnings data unavailable")}</p>', "wide")
    b = te["season"]
    chips = (f'<div class="chips"><span class="chip">{T("近 45 天公布", "Reported (45d)")} {b["n"]} {T("家", "")}</span>'
             f'<span class="chip">{T("EPS 優於預期", "EPS beats")} {b["beats"]}</span>'
             f'<span class="chip">{T("平均驚喜", "Avg surprise")} {num(b.get("avg_surp"), 1, sign=True, pct=True)}</span>'
             f'<span class="chip">{T("營收年增中位數", "Median revenue growth")} {num(b.get("rev_yoy"), 0, pct=True)}</span>'
             f'<span class="chip">{T("財報後兩日平均", "Avg 2-day move")} {num(b.get("avg_react"), 1, sign=True, pct=True)}</span></div>')
    rows = "".join(f'<tr><td><b>{esc(g["theme"])}</b> <span class="muted small">{g["n"]}</span></td><td class="r {cls(g.get("rev_yoy"))}">{num(g.get("rev_yoy"), 0, pct=True)}</td>'
                   f'<td class="r {cls(g.get("gm_yoy"))}">{num(g.get("gm_yoy"), 1, sign=True)}pp</td><td class="r">{num(g.get("om"), 1, pct=True)}</td>'
                   f'<td class="r">{num(g.get("beat"), 0, pct=True)}</td><td class="r">{num(g.get("score"), 0)}</td><td class="small">{esc("、".join(g["leaders"]))}</td></tr>'
                   for g in te["groups"])
    tbl = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("族群", "Group")}</th><th class="r">{T("營收年增中位數", "Rev y/y (median)")}</th>'
           f'<th class="r">{T("毛利率年變化", "GM Δ y/y")}</th><th class="r">{T("營益率中位數", "Op margin")}</th><th class="r">{T("上季優於預期比例", "Beat share")}</th>'
           f'<th class="r">{T("動能分數", "Score")}</th><th>{T("動能領先", "Leaders")}</th></tr></thead><tbody>{rows}</tbody></table></div>')
    ai = te.get("ai_season")
    ai_h = (f'<div class="ainote"><b>{T("AI 財報季總結", "AI season summary")}</b><span class="muted small">（{esc(ai.get("engine", ""))}）</span>'
            f'<p>{esc(ai["text"]).replace(chr(10), "<br>")}</p></div>' if ai else "")
    return card("科技／半導體財報季", "Tech & semis earnings season", chips + tbl + ai_h, "wide")


def sec_tech_board(eng) -> str:
    te = getattr(eng, "techearn", None) or {}
    if not te.get("available"):
        return ""
    trs = []
    for i, r in enumerate(te["rows"], 1):
        s = r["s"]
        acc = r.get("accel")
        arrow = "" if acc is None else (f' <span class="up small">▲{acc:.0f}</span>' if acc >= 3 else f' <span class="dn small">▼{-acc:.0f}</span>' if acc <= -5 else "")
        nx = r.get("next") or {}
        nxt = (f'{esc(nx["date"][5:])}<span class="muted small"> {num(nx.get("eps_f"), 2)}</span>' if nx else "—")
        sp = (f'<span class="{cls(s.get("last"))}">{num(s.get("last"), 0, sign=True, pct=True)}</span><span class="muted small"> {s["beats"]}/{s["n"]}</span>'
              if s.get("n") else "—")
        tg = "".join(f'<span class="rc {"rcp" if t == "up" else "rcn" if t == "dn" else ""}">{esc(x)}</span>' for x, t in r.get("tags", []))
        ai = (f'<div class="ainote"><b>{T("AI 解讀", "AI read")}</b><span class="muted small">（{esc(r["ai"].get("engine", ""))}）</span>'
              f'<p>{esc(r["ai"]["text"]).replace(chr(10), "<br>")}</p></div>' if r.get("ai") else "")
        surp = "".join(f'<li>{esc(x["fq"] or "")}：EPS {num(x["eps"], 2)} vs {num(x["cons"], 2)}（{num(x["surp"], 1, sign=True, pct=True)}）'
                       f'{T("，公布 ", ", reported ") + esc(x["date"]) if x.get("date") else ""}</li>' for x in s.get("rows", []))
        src = T("（Nasdaq 季報，近 4 季）", " (Nasdaq, 4 quarters)") if r.get("src") == "nasdaq" else ""
        q = esc((r["name"] + " " + r["name_en"] + " " + r["sym"]).lower())
        sc = r.get("score")
        trs.append(f'<tr class="tm" data-q="{q}" data-th="{esc(r["theme"])}"><td class="r muted">{i}</td><td class="nw"><b>{esc(r["name"])}</b><span class="tk">{esc(r["sym"])}</span>'
                   f'<span class="thc">{esc(r["theme"])}</span></td><td class="r muted">{esc((r.get("end") or "")[2:7].replace("-", "/"))}</td>'
                   f'<td class="r">{num((r.get("rev") or 0) / 1e9, 2) if r.get("rev") else "—"}</td>'
                   f'<td class="r {cls(r.get("rev_yoy"))}">{num(r.get("rev_yoy"), 0, pct=True)}{arrow}</td>'
                   f'<td class="r">{num(r.get("gm"), 1, pct=True)}<span class="small {cls(r.get("gm_yoy"))}"> {num(r.get("gm_yoy"), 1, sign=True)}</span></td>'
                   f'<td class="r opt">{num(r.get("om"), 1, pct=True)}<span class="small {cls(r.get("om_yoy"))}"> {num(r.get("om_yoy"), 1, sign=True)}</span></td>'
                   f'<td class="r opt {cls(r.get("eps_yoy"))}">{num(r.get("eps_yoy"), 0, pct=True)}</td><td class="r">{sp}</td>'
                   f'<td class="r opt">{"±" + num(s.get("react_avg"), 1) + "%" if s.get("react_avg") is not None else "—"}</td><td class="r nw">{nxt}</td>'
                   f'<td>{_bar(sc, _sc_color(sc))}</td></tr>'
                   f'<tr class="det" data-th="{esc(r["theme"])}"><td></td><td colspan="11"><div class="detg"><div>{_qchart(r.get("series") or [])}'
                   f'<div class="small muted">{T("長條＝季營收，線＝毛利率", "bars = revenue, line = gross margin")}{src}</div></div>'
                   f'<div><p class="small">{esc(r.get("verdict", ""))}</p><div>{tg}</div><ul class="small lines">{surp}</ul></div></div>{ai}</td></tr>')
    ths = "".join(f'<option value="{esc(t)}">{esc(t)}</option>' for t in dict.fromkeys(r["theme"] for r in te["rows"]))
    ctl = (f'<div class="fmctl"><input type="search" class="btn tbq" placeholder="搜尋，例如 NVDA、超微" aria-label="search">'
           f'<select class="btn tbth"><option value="" data-en="All">全部族群</option>{ths}</select>'
           f'<span class="muted small">{T("點任一列看 8 季走勢、標籤與 EPS 紀錄", "Click a row for 8 quarters and details")}</span></div>')
    head = (f'<tr><th class="r">#</th><th>{T("公司", "Company")}</th><th class="r">{T("季末", "Qtr end")}</th><th class="r">{T("營收（十億美元）", "Revenue ($bn)")}</th>'
            f'<th class="r">{T("營收年增", "Rev y/y")}</th><th class="r">{T("毛利率（年變化 pp）", "GM (Δpp)")}</th><th class="r opt">{T("營益率（年變化）", "OM (Δpp)")}</th>'
            f'<th class="r opt">{T("EPS 年增", "EPS y/y")}</th><th class="r">{T("EPS 驚喜（優於預期季數）", "EPS surprise (beats)")}</th>'
            f'<th class="r opt">{T("財報兩日波動", "2-day move")}</th><th class="r">{T("下次財報（EPS 預期）", "Next report (est.)")}</th>'
            f'<th>{T("財報動能分數", "Momentum score")}</th></tr>')
    note = T("數字來自 SEC XBRL 財報（第 4 季＝全年減前三季；外國公司如台積電 ADR 用 Nasdaq 季報）與 Nasdaq 的 EPS 預期／驚喜。"
             "財報動能分數＝在精選池科技／半導體裡的百分位：營收年增 30%、成長加速 15%、毛利率年變化 15%、營益率年變化 10%、EPS 年增 15%、"
             "近 4 季平均 EPS 驚喜 15%；只描述財報數字的相對強弱，不是投資建議。EPS 為 GAAP 稀釋，可能與市場常看的調整後 EPS 不同。",
             "SEC XBRL (Q4 = FY − Q1..Q3; foreign filers via Nasdaq) + Nasdaq EPS consensus. Score = percentile blend; not advice.")
    return card("科技／半導體財報分析（精選池）", "Tech & semis earnings (curated)",
                ctl + f'<div class="scroll"><table class="score teb"><thead>{head}</thead><tbody>{"".join(trs)}</tbody></table></div><p class="note">{note}</p>', "wide")


def sec_tw_rev(eng) -> str:
    te = getattr(eng, "techearn", None) or {}
    tw = te.get("tw") or {}
    if not tw.get("available"):
        return ""
    inds = "".join(f'<tr><td>{esc(x["ind"])} <span class="muted small">{x["n"]}</span></td><td class="r">{num(x["rev"], 0)}</td>'
                   f'<td class="r {cls(x["yoy"])}">{num(x["yoy"], 1, sign=True, pct=True)}</td></tr>' for x in tw["industries"])
    cur = "".join(f'<tr><td class="nw"><b>{esc(x["name"])}</b><span class="tk">{esc(x["code"])}</span></td><td class="r">{num(x["rev"], 1)}</td>'
                  f'<td class="r {cls(x["mom"])}">{num(x["mom"], 1, sign=True, pct=True)}</td><td class="r {cls(x["yoy"])}">{num(x["yoy"], 1, sign=True, pct=True)}</td>'
                  f'<td class="r {cls(x["cum_yoy"])}">{num(x["cum_yoy"], 1, sign=True, pct=True)}</td></tr>' for x in tw["curated"])
    body = (f'<div class="g2"><div><h4>{T("電子產業合計（" + tw["ym"] + "）", "Electronics by industry (" + tw["ym"] + ")")}</h4>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("產業", "Industry")}</th><th class="r">{T("月營收（億元）", "Revenue (NT$100m)")}</th>'
            f'<th class="r">{T("年增", "y/y")}</th></tr></thead><tbody>{inds}</tbody></table></div></div>'
            f'<div><h4>{T("精選池台股（依年增排序）", "Curated Taiwan names (by y/y)")}</h4><div class="scroll"><table class="mini"><thead><tr><th>{T("公司", "Company")}</th>'
            f'<th class="r">{T("億元", "NT$100m")}</th><th class="r">{T("月增", "m/m")}</th><th class="r">{T("年增", "y/y")}</th><th class="r">{T("累計年增", "YTD y/y")}</th></tr></thead>'
            f'<tbody>{cur}</tbody></table></div></div></div>'
            f'<h4>{T("全部電子股月營收", "All electronics — monthly revenue")}</h4>' + _jt("tw"))
    note = T("資料：證交所與櫃買中心公開資料（每月 10 日前公布上月營收）。產業合計＝當月營收加總對去年同月加總。「連續年增」從本站開始存檔的月份起算。",
             "Source: TWSE / TPEx open data (published by the 10th).")
    return card("台股電子業月營收", "Taiwan electronics monthly revenue", body + f'<p class="note">{note}</p>', "wide")


JT_PH = {"tw": "搜尋代號或名稱，例如 2330、聯發科", "us": "搜尋代號或名稱，例如 NVDA、Snowflake",
         "gus": "搜尋代號或名稱，例如 NU、SMR、HOOD", "gearly": "搜尋代號或名稱，例如 SMR、OKLO、RKLB", "gtw": "搜尋代號或名稱，例如 2330、奇鋐"}


def _jt(kind: str, only: bool = False, autoload: bool = False) -> str:
    chk = (f'<label class="small muted"><input type="checkbox" class="jto" checked> {T("只看排名內（符合成長與營收門檻）", "Ranked only")}</label>'
           if only else "")
    return (f'<div class="jt" data-kind="{kind}"{" data-auto=1" if autoload else ""}><div class="fmctl"><input type="search" class="btn jtq" placeholder="'
            + JT_PH[kind] + '" aria-label="search">'
            f'<select class="btn jtf"><option value="" data-en="All">{"全部子產業" if kind == "us" else "全部產業"}</option></select>'
            f'<select class="btn jts"></select>{chk}<button class="btn jtl" type="button">{T("載入資料", "Load data")}</button>'
            f'<span class="muted small jtst"></span></div><div class="jtb"></div></div>')


def _top_us(d: Dict, n: int = 12) -> str:
    cols = d["cols"]
    rows = [dict(zip(cols, r)) for r in d["rows"] if r[cols.index("rank")]][:n]
    tr = "".join(f'<tr><td class="r muted">{r["rank"]}</td><td class="nw"><b>{esc(r["name"][:28])}</b><span class="tk">{esc(r["sym"])}</span></td>'
                 f'<td class="small muted">{esc(r["ind"] or "")}</td><td class="r">{num((r["mcap"] or 0) / 1e9, 1)}</td>'
                 f'<td class="r {cls(r["g"])}">{num(r["g"], 0, pct=True)}</td><td class="r">{num(r["gm"], 0, pct=True)}</td>'
                 f'<td class="r">{num(r["ps"], 1)}</td><td class="r"><b>{num(r.get("gav"), 3)}</b><span class="muted small"> {esc(r.get("basis") or "")}</span></td><td class="r">{num(r["r40"], 0)}</td>'
                 f'<td class="small">{esc(r.get("st") or "—")}</td></tr>' for r in rows)
    return (f'<div class="scroll"><table class="mini"><thead><tr><th class="r">#</th><th>{T("公司", "Company")}</th><th>{T("產業", "Sector")}</th>'
            f'<th class="r">{T("市值（十億美元）", "Mkt cap ($bn)")}</th><th class="r">{T("營收年增", "Rev growth")}</th><th class="r">{T("毛利率", "GM")}</th>'
            f'<th class="r">P/S</th><th class="r">{T("估值÷成長", "Value ÷ growth")}</th><th class="r">{T("40 法則", "Rule of 40")}</th><th>{T("技術面狀態", "Technical")}</th></tr></thead><tbody>{tr}</tbody></table></div>')


def _top_tw(d: Dict, n: int = 12) -> str:
    cols = d["cols"]
    rows = [dict(zip(cols, r)) for r in d["rows"] if r[cols.index("rank")]][:n]
    tr = "".join(f'<tr><td class="r muted">{r["rank"]}</td><td class="nw"><b>{esc(r["name"])}</b><span class="tk">{esc(r["code"])}</span></td>'
                 f'<td class="small muted">{esc(r["ind"] or "")}</td><td class="r {cls(r["cum_yoy"])}">{num(r["cum_yoy"], 0, pct=True)}</td>'
                 f'<td class="r {cls(r["yoy"])}">{num(r["yoy"], 0, pct=True)}</td><td class="r">{num(r["pe"], 1)}</td>'
                 f'<td class="r"><b>{num(r["peg"], 2)}</b></td><td class="r">{num(r["pb"], 1)}</td><td class="small">{esc(r.get("st") or "—")}</td></tr>' for r in rows)
    return (f'<div class="scroll"><table class="mini"><thead><tr><th class="r">#</th><th>{T("公司", "Company")}</th><th>{T("產業", "Industry")}</th>'
            f'<th class="r">{T("今年累計營收年增", "YTD revenue y/y")}</th><th class="r">{T("單月年增", "Month y/y")}</th><th class="r">{T("本益比", "P/E")}</th>'
            f'<th class="r">PEG</th><th class="r">{T("股價淨值比", "P/B")}</th><th>{T("技術面狀態", "Technical")}</th></tr></thead><tbody>{tr}</tbody></table></div>')


def sec_growth(eng) -> str:
    from wsb.analytics import growth as GR
    us, tw = GR.published("us"), GR.published("tw")
    howto = (f'<details class="sgx" open><summary>{T("這頁在找什麼、怎麼看", "What this page looks for")}</summary><ul class="small">'
             f'<li>{T("技術面買點只看股價型態，抓不到「營收成長很快、但估值還不貴」的公司。這頁反過來從財報找：成長越快、成長調整後的估值越低，排名越前面。", "Finds fast revenue growth at a relatively low growth-adjusted valuation.")}</li>'
             f'<li>{T("美股「估值÷成長」：有毛利率的公司用「市值÷近 4 季毛利」（P/GP，避免低毛利行業只因本銷比低就看起來便宜），沒有毛利資料的（金融等）用本益比，再除以營收年增率；兩種分開比較，數字越低代表每一分成長付的價格越便宜。成長率超過 100% 以 100% 計（避免併購造成的跳增被當成成長），最新一季也要仍在成長。本銷比 P/S 與 PSG 也列出供參考。", "Value ÷ growth: price/gross profit (or P/E without a gross margin) ÷ revenue growth, compared within each basis; growth capped at 100%.")}</li>'
             f'<li>{T("40 法則＝營收年增＋營益率，常用來看成長股「成長與獲利」的平衡（≥ 40 算健康）。", "Rule of 40 = growth + operating margin.")}</li>'
             f'<li>{T("台股 PEG＝本益比÷今年累計營收年增率；營收是每月公布，比季報即時。", "Taiwan PEG = P/E ÷ YTD revenue growth (monthly data).")}</li>'
             f'<li>{T("營收還小的早期公司也一起排名：還沒有毛利或獲利的，估值用本銷比、只跟同類公司比較；成長率超過 100% 以 100% 計，避免小基期的爆發成長把排名洗掉。外國公司（例如 NU）用 Nasdaq 年報補，是年度數字。", "Early-stage companies are ranked too (P/S basis among themselves); growth capped at 100%; foreign filers use annual statements.")}</li>'
             f'<li>{T("下方另有「早期公司（營收 < 2 億美元）」清單，連營收還沒成長、甚至還沒有營收的公司（例如 SMR、核能、太空、生技）都列出，重點看「現金還能撐幾年」。估值低也可能有原因（成長不持續、獲利差、景氣循環高點），只是篩選起點，不是買進建議。", "An early-stage list (revenue < $200m) shows cash runway. A screen, not advice.")}</li>'
             '</ul></details>')
    parts = [howto]
    if us and us.get("available"):
        parts.append(f'<h4>{T("美股：成長價值排名前段", "US: top of the growth-value ranking")}<span class="muted small">　{T("合格", "ranked")} {us.get("ranked", 0)} / {us["n"]} {T("家", "")}・{esc(us.get("asof", ""))}</span></h4>'
                     + _top_us(us) + _jt("gus", only=True)
                     + f'<h4>{T("美股：早期公司（近 4 季營收 < 2 億美元，長期題材）", "US: early-stage companies (revenue < $200m)")}</h4>'
                     f'<p class="small muted">{T("長期投資看的是題材能不能撐到開花結果：「現金跑道」＝現金與短期投資 ÷ 近 4 季營業現金流出，代表照目前燒錢速度還能撐幾年（少於 2 年通常要增資或借錢，股本可能被稀釋）。", "Runway = cash & short-term investments ÷ trailing operating cash burn (years).")}</p>'
                     + _jt("gearly"))
    else:
        parts.append(f'<p class="muted">{T("美股成長估值資料第一次建立中（需要全市場名單與 SEC 財報），稍後再來看。", "US data being built.")}</p>')
    if tw and tw.get("available"):
        parts.append(f'<h4>{T("台股：成長價值排名前段", "Taiwan: top of the growth-value ranking")}<span class="muted small">　{T("營收月份", "Revenue month")} {esc(tw.get("ym", ""))}・'
                     f'{T("合格", "ranked")} {tw.get("ranked", 0)} / {tw["n"]}</span></h4>' + _top_tw(tw) + _jt("gtw", only=True))
    note = T("資料：SEC XBRL frames、Nasdaq（名單、市值、外國公司年報）、證交所與櫃買中心（月營收、本益比、股價淨值比、殖利率）。合格門檻：美股營收年增 ≥ 15%（營收規模不限）；台股今年累計營收年增 ≥ 15%、本益比為正、月營收 ≥ 1 億元。"
             "排名分數＝合格名單內百分位：成長 40%、估值÷成長 40%、毛利率（台股：單月年增）10%、40 法則（台股：股價淨值比）10%。成長率以 100% 為上限計分；商譽一年內大增（代表營收成長多半來自併購）的標「含併購」、不排名；能源、不動產、原物料、公用事業的營收常隨商品價格或併購大幅跳動，列出但不排名；同一家公司的其他股別只留一檔。不構成投資建議。",
             "Sources: SEC frames, Nasdaq, TWSE/TPEx. Thresholds and weights as described. Not advice.")
    return card("成長股估值篩選（美股＋台股）", "Growth at a reasonable price (US + Taiwan)", "".join(parts) + f'<p class="note">{note}</p>', "wide")


def sec_us_tech(eng) -> str:
    te = getattr(eng, "techearn", None) or {}
    n = te.get("ustech_n") or 0
    note = T("資料：SEC XBRL frames（每家公司的最新一個「日曆季」，第 4 季＝全年減前三季），名單為 Nasdaq 分類為科技、市值 10 億美元以上的美股。"
             "不同公司的會計年度不同，所以季別以日曆季對齊。每天更新。",
             "SEC XBRL frames (latest calendar quarter; Q4 derived); Nasdaq tech sector, market cap ≥ $1bn.")
    msg = "" if n else f'<p class="muted small">{T("全市場科技股資料第一次建立中，稍後再來看。", "Being built — check back later.")}</p>'
    return card("美股全市場科技股（最新一季）", "All US tech — latest quarter", msg + _jt("us") + f'<p class="note">{note}</p>', "wide")


CSS = """
.wkgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.wk{display:block;background:var(--card2);border:1px solid var(--bd);border-radius:9px;padding:8px 10px;color:var(--tx);text-decoration:none}
.wk.imp3{border-left:3px solid var(--warn)}.wk.done{opacity:.92}.wk div{margin:2px 0}.wkh{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.stars{color:var(--warn);font-size:11px;letter-spacing:-1px;margin-right:4px}
.dbadge{display:inline-block;border-radius:5px;padding:0 7px;font-size:12px;font-weight:600;margin:3px 0}
.dbadge.dhot{background:color-mix(in srgb,var(--dn) 22%,transparent);color:var(--tx)}.dbadge.dcool{background:color-mix(in srgb,var(--up) 22%,transparent);color:var(--tx)}
.dbadge.dinl{background:var(--card2);border:1px solid var(--bd)}
.fomc{background:var(--card2);border:1px solid var(--bd);border-radius:9px;padding:10px 12px;margin-bottom:8px}.fomc .big{font-size:22px;font-weight:700}.fomc div{margin:3px 0}
.scen{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:6px 0}.scen .scn{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:6px 9px;font-size:12.5px}
.scen .scn h5{margin:0 0 3px;font-size:12.5px}.scen .scn p{margin:0}.scen .scn.dhot{border-top:3px solid var(--dn)}.scen .scn.dcool{border-top:3px solid var(--up)}
.scen .scn.dinl{border-top:3px solid var(--mu)}.scen .scn.on{outline:2px solid var(--ac)}
details.ev{border-bottom:1px solid var(--bd);padding:4px 0}details.ev summary{cursor:pointer;display:flex;gap:8px;align-items:center;flex-wrap:wrap;list-style:none}
details.ev summary::-webkit-details-marker{display:none}details.ev summary::before{content:"▸";color:var(--mu)}details.ev[open] summary::before{content:"▾"}
details.ev .tm{min-width:74px;font-variant-numeric:tabular-nums}.evn{min-width:150px}.evv{flex:1;min-width:220px}.evb{padding:6px 0 8px 18px}
.evday h4{margin:12px 0 2px;border-bottom:1px solid var(--bd);padding-bottom:3px}.evday.today h4{color:var(--ac)}.evday.past{opacity:.85}
.evday.past.hide,.ev.hide{display:none}details.hist{margin:6px 0}details.hist summary{cursor:pointer;color:var(--ac)}
.ainote{background:color-mix(in srgb,var(--ac) 9%,transparent);border:1px solid color-mix(in srgb,var(--ac) 35%,transparent);border-radius:8px;padding:6px 10px;margin:6px 0;font-size:13px}
.ainote p{margin:4px 0 0}.ecal tr.hide{display:none}
table.teb tr.tm{cursor:pointer}table.teb tr.det{display:none}table.teb tr.det.open{display:table-row}table.teb tr.det td{background:var(--card2)}
.detg{display:grid;grid-template-columns:320px 1fr;gap:12px;align-items:start}.qchart{width:300px;height:96px}
.qchart .qb{fill:color-mix(in srgb,var(--ac) 55%,transparent)}.qchart .qg{fill:none;stroke:var(--warn);stroke-width:2}.qchart .ql{font-size:9px;fill:var(--mu)}
.g2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.jt table td,.jt table th{white-space:nowrap}.jt th[data-s]{cursor:pointer}
@media(max-width:760px){.scen,.g2,.detg{grid-template-columns:1fr}.evn{min-width:0}}
"""

JS = r"""
(function(){var en=function(){return document.documentElement.lang==='en';};
document.querySelectorAll('.evlist').forEach(function(L){var card=L.closest('.card'),imp=card.querySelector('.evimp'),q=card.querySelector('.evq'),past=card.querySelector('.evpast');
 function f(){var m=+(imp?imp.value:2),s=(q&&q.value||'').toLowerCase(),sp=past&&past.checked;
  L.querySelectorAll('.evday').forEach(function(d){var any=0;d.querySelectorAll('details.ev').forEach(function(e){var ok=(+e.dataset.imp>=m)&&(!s||e.dataset.q.indexOf(s)>=0);
   e.classList.toggle('hide',!ok);if(ok)any=1;});d.style.display=(any&&(sp||!d.classList.contains('past')))?'':'none';});}
 [imp,q,past].forEach(function(x){if(x)x.addEventListener(x.tagName==='INPUT'&&x.type==='search'?'input':'change',f);});f();});
document.querySelectorAll('.wk[data-ev]').forEach(function(a){a.addEventListener('click',function(){var t=document.getElementById(a.getAttribute('href').slice(1));
 if(t){var d=t.closest('.evday');if(d)d.style.display='';t.classList.remove('hide');t.open=true;}});});
document.querySelectorAll('select.ecf').forEach(function(s){s.addEventListener('change',function(){var v=s.value;s.closest('.card').querySelectorAll('table.ecal tbody tr').forEach(function(tr){
 tr.classList.toggle('hide',!!v&&v.indexOf(tr.dataset.k)<0);});});});
document.querySelectorAll('table.teb').forEach(function(t){t.querySelectorAll('tr.tm').forEach(function(tr){tr.addEventListener('click',function(){tr.nextElementSibling.classList.toggle('open');});});
 var c=t.closest('.card'),q=c.querySelector('.tbq'),th=c.querySelector('.tbth');function f(){var s=(q.value||'').toLowerCase(),v=th.value;
  t.querySelectorAll('tr.tm').forEach(function(tr){var ok=(!s||tr.dataset.q.indexOf(s)>=0)&&(!v||tr.dataset.th===v);tr.style.display=ok?'':'none';if(!ok)tr.nextElementSibling.classList.remove('open');});}
 if(q)q.addEventListener('input',f);if(th)th.addEventListener('change',f);});
var SPEC={tw:{src:'market/twrev.json',filt:'ind',sorts:[['yoy','年增率','y/y'],['rev','月營收','Revenue'],['cum_yoy','累計年增','YTD y/y'],['mom','月增','m/m'],['streak','連續年增月數','Streak']],
  cols:[['code','代號','Code'],['name','公司','Company'],['ind','產業','Industry'],['ym','月份','Month'],['rev','營收（億）','Rev (NT$100m)',2],['mom','月增','m/m',1,'%'],['yoy','年增','y/y',1,'%'],['cum_yoy','累計年增','YTD',1,'%'],['streak','連續年增','Streak']]},
 gus:{src:'market/growth_us.json',filt:'ind',only:'rank',sorts:[['score','排名分數','Score'],['gav','估值÷成長（低→高）','Value÷growth (low→high)','asc'],['psg','PSG（低→高）','PSG (low→high)','asc'],['g','營收年增','Growth'],['ps','本銷比（低→高）','P/S (low→high)','asc'],['mcap','市值','Market cap'],['r40','40 法則','Rule of 40']],
  cols:[['rank','#','#'],['sym','代號','Ticker'],['name','公司','Company'],['ind','產業','Sector'],['per','期間','Period'],['mcap','市值（十億）','Cap ($bn)',1,'',1e9],['ttm','近4季營收（十億）','TTM rev ($bn)',2,'',1e9],
   ['g','營收年增','Growth',1,'%'],['q_yoy','最新季年增','Qtr y/y',1,'%'],['accel','加速','Accel',1,'pp'],['gm','毛利率','GM',1,'%'],['om','營益率','OM',1,'%'],['r40','40法則','R40',0],['ps','P/S','P/S',1],['psg','PSG','PSG',2],['pe','本益比','P/E',1],['gav','估值÷成長','Val÷g',3],['basis','基準','Basis'],['score','分數','Score',0],['st','技術面','Technical']]},
 gearly:{src:'market/growth_us.json',filt:'ind',pre:function(o){return o.ttm!=null&&o.ttm<2e8;},sorts:[['mcap','市值','Market cap'],['runway','現金跑道（長→短）','Runway'],['g','營收年增','Growth'],['cash','現金','Cash']],
  cols:[['sym','代號','Ticker'],['name','公司','Company'],['ind','產業','Sector'],['sub','子產業','Industry'],['mcap','市值（十億）','Cap ($bn)',1,'',1e9],['ttm','近4季營收（百萬）','TTM rev ($m)',1,'',1e6],['g','營收年增','Growth',0,'%'],['ps','P/S','P/S',0],['cash','現金（百萬）','Cash ($m)',0,'',1e6],['burn','年燒錢（百萬）','Burn ($m/yr)',0,'',1e6],['runway','現金跑道（年）','Runway (yrs)',1],['rank','成長排名','Growth rank'],['st','技術面','Technical']]},
 gtw:{src:'market/growth_tw.json',filt:'ind',only:'rank',sorts:[['score','排名分數','Score'],['peg','PEG（低→高）','PEG (low→high)','asc'],['cum_yoy','累計營收年增','YTD growth'],['yoy','單月年增','Month y/y'],['pe','本益比（低→高）','P/E (low→high)','asc'],['rev','月營收','Revenue']],
  cols:[['rank','#','#'],['code','代號','Code'],['name','公司','Company'],['ind','產業','Industry'],['ym','月份','Month'],['rev','月營收（億）','Rev (NT$100m)',1],['cum_yoy','累計年增','YTD y/y',1,'%'],['yoy','單月年增','Month y/y',1,'%'],
   ['streak','連續年增','Streak'],['pe','本益比','P/E',1],['pb','淨值比','P/B',2],['dy','殖利率','Yield',1,'%'],['peg','PEG','PEG',2],['score','分數','Score',0],['st','技術面','Technical']]},
 us:{src:'market/ustech.json',filt:'sub',sorts:[['mcap','市值','Market cap'],['yoy','營收年增','Rev y/y'],['gm','毛利率','Gross margin'],['om','營益率','Op margin'],['eps_yoy','EPS 年增','EPS y/y']],
  cols:[['sym','代號','Ticker'],['name','公司','Company'],['sub','子產業','Industry'],['q','季別','Qtr'],['rev','營收（百萬美元）','Rev ($m)',0,'',1e6],['yoy','年增','y/y',1,'%'],['qoq','季增','q/q',1,'%'],
   ['gm','毛利率','GM',1,'%'],['gm_yoy','毛利率年變化','GM Δ',1,'pp'],['om','營益率','OM',1,'%'],['nm','淨利率','NM',1,'%'],['eps','EPS','EPS',2],['eps_yoy','EPS 年增','EPS y/y',1,'%']]}};
document.querySelectorAll('.jt').forEach(function(w){var sp=SPEC[w.dataset.kind],data=null,shown=100,q=w.querySelector('.jtq'),fs=w.querySelector('.jtf'),ss=w.querySelector('.jts'),
 st=w.querySelector('.jtst'),body=w.querySelector('.jtb'),btn=w.querySelector('.jtl');
 sp.sorts.forEach(function(s){var o=document.createElement('option');o.value=s[0];o.textContent=(en()?'Sort: '+s[2]:'排序：'+s[1]);ss.appendChild(o);});
 function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
 function fm(v,c){if(v==null||v==='')return '—';if(typeof v==='boolean')return v?'★':'';if(c[3]==null)return String(v);var x=+v/(c[5]||1);return x.toLocaleString(undefined,{minimumFractionDigits:c[3],maximumFractionDigits:c[3]})+(c[4]||'');}
 function render(){body.textContent='';if(!data)return;var s=(q.value||'').toLowerCase(),f=fs.value,k=ss.value;
  var oc=w.querySelector('.jto'),only=sp.only&&oc&&oc.checked&&!s,asc=((sp.sorts.filter(function(x){return x[0]===k;})[0])||[])[3]==='asc';
  var its=data.items.filter(function(o){return (!f||o[sp.filt]===f)&&(!s||(String(o.code||o.sym)+' '+o.name).toLowerCase().indexOf(s)>=0)&&(!only||o[sp.only]!=null)&&(!sp.pre||sp.pre(o));});
  its.sort(function(a,b){var x=a[k],y=b[k];if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return -1;return asc?x-y:y-x;});st.textContent=' '+its.length+(en()?' rows':' 筆');
  var sc=el('div','scroll'),t=el('table','mini'),hr=el('tr');sp.cols.forEach(function(c){hr.appendChild(el('th',null,en()?c[2]:c[1]));});var th=el('thead');th.appendChild(hr);t.appendChild(th);
  var tb=el('tbody');its.slice(0,shown).forEach(function(o){var tr=el('tr');sp.cols.forEach(function(c){var v=o[c[0]],td=el('td',(c[3]!=null?'r ':'')+(c[4]==='%'||c[4]==='pp'?(v>0?'up':v<0?'dn':''):''),fm(v,c));
   if(c[0]==='name'&&o.cur)td.appendChild(el('span','pill','精選'));if(c[0]==='name'&&o.small)td.appendChild(el('span','pill',en()?'early stage':'營收尚小'));if(c[0]==='name'&&o.odd&&!o.small)td.appendChild(el('span','pill',en()?'small base':'基期小'));if(c[0]==='name'&&o.ma)td.appendChild(el('span','pill',en()?'acquisition':'含併購'));if(c[0]==='name'&&o.flag)td.appendChild(el('span','pill warn',o.flag));tr.appendChild(td);});tb.appendChild(tr);});t.appendChild(tb);sc.appendChild(t);body.appendChild(sc);
  if(its.length>shown){var m=el('button','btn',en()?'Show 100 more':'再顯示 100 筆');m.type='button';m.addEventListener('click',function(){shown+=100;render();});body.appendChild(m);}}
 function go(){btn.style.display='none';st.textContent=en()?'Loading…':'載入中…';fetch(sp.src,{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){
  d.items=d.rows.map(function(a){var o={};d.cols.forEach(function(k,i){o[k]=a[i];});return o;});data=d;var cnt={};d.items.forEach(function(o){if(sp.pre&&!sp.pre(o))return;var v=o[sp.filt];if(v)cnt[v]=(cnt[v]||0)+1;});
  Object.keys(cnt).sort(function(a,b){return cnt[b]-cnt[a];}).forEach(function(v){var o=el('option',null,v+' ('+cnt[v]+')');o.value=v;fs.appendChild(o);});render();})
  .catch(function(){st.textContent=en()?'Data not available yet.':'資料尚未建立。';});}
 btn.addEventListener('click',go);[q].forEach(function(x){x.addEventListener('input',function(){if(!data)go();else{shown=100;render();}});});
 [fs,ss].forEach(function(x){x.addEventListener('change',function(){shown=100;render();});});
 var oc=w.querySelector('.jto');if(oc)oc.addEventListener('change',function(){shown=100;render();});if(w.dataset.auto)go();});
})();
"""
