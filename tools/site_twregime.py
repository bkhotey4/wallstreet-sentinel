"""台股頁：台股進場環境卡——大環境條件清單，加上「過去同樣條件時，之後 3／6／12 個月加權指數怎麼走」。
不是個人的時點建議：只描述大環境對股市有利或不利，以及歷史上的統計。

回測用 6 項每月條件（央行、國發會、FRED 免費資料，1990 年代中期起）：
  1 趨勢：加權指數 ≥ 自己 10 個月平均（月資料版的 200 日線）
  2 景氣：國發會領先指標比 6 個月前高
  3 出口：海關出口近 3 個月合計比去年同期多
  4 台灣利率：10 年期公債殖利率 ≤ 自己 12 個月平均
  5 美國利率：美國 10 年期公債殖利率 ≤ 自己 12 個月平均
  6 資金：M1B 年增率 ≥ M2 年增率（活錢比定存長得快）
另外 5 項只看現在（歷史不夠長、不進回測）：估值、融資熱度、外資動向、泡沫燈、外銷訂單動向指數。
判斷都和資料自己的歷史或定義比，不用憑感覺定的門檻。"""
from __future__ import annotations

import json
from statistics import mean, median
from typing import Dict, List, Optional, Tuple

from tools.sitekit import T, card, esc, fold_rows

HORIZONS = (3, 6, 12)
BUCKETS = (("0–2 項有利", 0, 2), ("3–4 項有利", 3, 4), ("5–6 項有利", 5, 6))
SRC = {"cbc": "https://cpx.cbc.gov.tw/", "ndc": "https://index.ndc.gov.tw/", "fred": "https://fred.stlouisfed.org/series/GS10",
       "twse": "https://www.twse.com.tw/"}


def _m(rows) -> Dict[str, float]:
    out = {}
    for r in rows or []:
        try:
            if r[1] is not None and not isinstance(r[1], str):
                out[str(r[0])[:7]] = float(r[1])
        except (TypeError, ValueError, IndexError):
            continue
    return out


def _shift(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7]) + k
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}"


def _avg(s: Dict[str, float], ym: str, n: int) -> Optional[float]:
    xs = [s.get(_shift(ym, -i)) for i in range(n)]
    return sum(xs) / n if all(x is not None for x in xs) else None


def conditions(ym: str, S: Dict[str, Dict[str, float]]) -> Dict[str, Optional[bool]]:
    """The six backtested conditions for month `ym`, using only data up to that month (None = data missing)."""
    tx, ld, ex, tw, us, m1, m2 = (S.get(k) or {} for k in ("taiex", "lead", "exports", "tw10y", "us10", "m1b", "m2"))
    out: Dict[str, Optional[bool]] = {}
    a = _avg(tx, ym, 10)
    out["trend"] = None if a is None or ym not in tx else tx[ym] >= a
    out["lead"] = None if ym not in ld or _shift(ym, -6) not in ld else ld[ym] > ld[_shift(ym, -6)]
    now3 = [ex.get(_shift(ym, -i)) for i in range(3)]
    ago3 = [ex.get(_shift(ym, -12 - i)) for i in range(3)]
    out["exports"] = None if None in now3 + ago3 else sum(now3) > sum(ago3)
    a = _avg(tw, ym, 12)
    out["tw10y"] = None if a is None or ym not in tw else tw[ym] <= a
    a = _avg(us, ym, 12)
    out["us10y"] = None if a is None or ym not in us else us[ym] <= a
    out["money"] = None if ym not in m1 or ym not in m2 else m1[ym] >= m2[ym]
    return out


NAMES = {"trend": "趨勢：加權指數在 10 個月平均之上", "lead": "景氣：領先指標比半年前高", "exports": "出口：近 3 個月比去年同期多",
         "tw10y": "台灣利率：10 年債殖利率不高於一年平均", "us10y": "美國利率：10 年債殖利率不高於一年平均",
         "money": "資金：M1B 年增率 ≥ M2（活錢長得比定存快）"}


def backtest(S: Dict[str, Dict[str, float]]) -> Dict:
    """Group every month with all six conditions known by how many were favourable; forward TAIEX returns per group."""
    tx = S.get("taiex") or {}
    months = sorted(tx)
    rows = []
    for ym in months:
        c = conditions(ym, S)
        if any(v is None for v in c.values()):
            continue
        fwd = {h: (tx[_shift(ym, h)] / tx[ym] - 1) * 100 if _shift(ym, h) in tx else None for h in HORIZONS}
        rows.append({"ym": ym, "green": sum(c.values()), "fwd": fwd})
    groups = []
    for label, lo, hi in BUCKETS + (("全部月份", 0, 6),):
        g = [r for r in rows if lo <= r["green"] <= hi]
        st = {}
        for h in HORIZONS:
            xs = [r["fwd"][h] for r in g if r["fwd"][h] is not None]
            st[h] = {"n": len(xs), "med": median(xs) if xs else None, "avg": mean(xs) if xs else None,
                     "up": sum(x > 0 for x in xs) / len(xs) * 100 if xs else None}
        groups.append({"label": label, "lo": lo, "hi": hi, "months": len(g), "stats": st})
    return {"rows": rows, "groups": groups, "since": rows[0]["ym"] if rows else None, "until": rows[-1]["ym"] if rows else None}


def series(tm: Dict, bub: Dict) -> Dict[str, Dict[str, float]]:
    cbc, ndc = tm.get("cbc") or {}, tm.get("ndc") or {}
    S = {k: _m(cbc.get(k)) for k in ("taiex", "tw10y", "m1b", "m2")}
    S.update({k: _m(ndc.get(k)) for k in ("lead", "exports", "orders_idx")})
    S["us10"] = {str(k)[:7]: float(v) for k, v in (bub.get("us10") or {}).items() if v is not None}
    return S


def latest(S: Dict[str, Dict[str, float]]) -> Optional[str]:
    """Newest month where all six conditions are known (data arrive with different lags)."""
    for ym in sorted(S.get("taiex") or {}, reverse=True):
        if all(v is not None for v in conditions(ym, S).values()):
            return ym
    return None


def current(S, bub_view: Dict, flows: List[Dict]) -> Dict:
    ym = latest(S)
    c = conditions(ym, S) if ym else {}
    each = {}                                                  # each condition's own newest month
    for k, key in (("trend", "taiex"), ("lead", "lead"), ("exports", "exports"), ("tw10y", "tw10y"), ("us10y", "us10"), ("money", "m1b")):
        s = S.get(key) or {}
        mx = max(s) if s else None
        each[k] = {"ok": conditions(mx, S).get(k) if mx else None, "month": mx}
    trend_daily = None
    for x in bub_view.get("inds") or []:
        if x.get("key") == "ext":
            trend_daily = {"ok": x["now"] >= 0, "date": x["date"], "pct": x["now"]}
    if trend_daily:
        each["trend"] = {"ok": trend_daily["ok"], "month": trend_daily["date"], "note": f'離 200 日線 {trend_daily["pct"]:+.1f}%（每日資料）'}
    green = sum(1 for v in each.values() if v["ok"])
    extra = []
    inds = {x["key"]: x for x in bub_view.get("inds") or []}
    if inds.get("pe") and inds["pe"].get("pct") is not None:
        p = inds["pe"]
        extra.append(("估值：上市本益比中位數在自己歷史的下半部", p["pct"] < 50, f'{p["now"]:.1f} 倍，第 {p["pct"]} 百分位（{p["date"]}）'))
    if inds.get("mg") and inds["mg"].get("z") is not None:
        g = inds["mg"]
        extra.append(("融資熱度：融資餘額沒有明顯偏高（z < 1）", g["z"] < 1, f'{g["now"]:,.0f} 億元，z {g["z"]:+.1f}（{g["date"]}）'))
    fl = [f for f in flows or [] if f.get("foreign") is not None]
    if fl:
        tot = sum(f["foreign"] for f in fl)
        extra.append((f"外資動向：近 {len(fl)} 個交易日合計買超", tot > 0, f'合計 {tot:+,.1f} 億元（{fl[-1]["date"]}～{fl[0]["date"]}）'))
    if bub_view.get("scored"):
        extra.append(("泡沫燈：偏熱指標不超過 1 項", (bub_view.get("hot_n") or 0) <= 1, f'{bub_view["scored"]} 項裡 {bub_view.get("hot_n", 0)} 項偏熱'))
    oi = S.get("orders_idx") or {}
    if oi:
        mx = max(oi)
        extra.append(("外銷訂單動向指數 ≥ 50（廠商多數看增）", oi[mx] >= 50, f"{oi[mx]:.1f}（{mx}，50 是看增看減各半）"))
    return {"ym": ym, "each": each, "green": green, "extra": extra}


def _v(eng) -> Dict:
    c = getattr(eng, "_twregime_view", None)
    if c is not None:
        return c
    try:
        from wsb.data import tw_bubble as B
        from wsb.data import twmacro as TM
        tm, bub = TM.load(), B.load()
        S = series(tm, bub)
        bt = backtest(S)
        cur = current(S, B.view_from(bub), list(getattr(getattr(eng, "taiwan", None), "flows", None) or []))
        c = {"bt": bt, "cur": cur, "ts": max(float(tm.get("ts") or 0), float(bub.get("ts") or 0))}
    except Exception:  # noqa: BLE001
        c = {}
    try:
        eng._twregime_view = c
    except Exception:  # noqa: BLE001
        pass
    return c


def _pct(x) -> str:
    return "—" if x is None else f"{x:+.1f}%"


def verdict(bt: Dict) -> str:
    """Does the checklist separate good and bad years at all?  Compare the low and high groups' 12-month medians."""
    g = bt.get("groups") or []
    if len(g) < 3:
        return ""
    lo, hi = g[0]["stats"][12], g[2]["stats"][12]
    if lo["med"] is None or hi["med"] is None:
        return ""
    if lo["med"] > hi["med"]:
        return (f"歷史上反而是有利條件少的月份，之後 12 個月漲得比較多（中位數 {_pct(lo['med'])} 對 {_pct(hi['med'])}）："
                "大環境最差時股價常常已經先跌完。這份清單適合用來了解「現在處在什麼環境」，不能拿來抓時點。")
    gap = hi["med"] - lo["med"]
    return (f"有利條件多的月份，之後 12 個月中位數 {_pct(hi['med'])}，比條件少的 {_pct(lo['med'])} 多 {gap:.1f} 個百分點；"
            "差距大小代表這份清單有多少參考價值，樣本重疊，不能當成保證。")


def lead(v: Dict) -> str:
    cur, bt = v.get("cur") or {}, v.get("bt") or {}
    g = cur.get("green")
    if g is None or not bt.get("groups"):
        return ""
    grp = next((x for x in bt["groups"][:3] if x["lo"] <= g <= x["hi"]), None)
    allg = bt["groups"][-1]
    tail = ""
    if grp and grp["stats"][12]["n"]:
        s, a = grp["stats"][12], allg["stats"][12]
        tail = (f"過去 {bt['since'][:4]} 年以來同樣是「{grp['label']}」的 {s['n']} 個月，之後 12 個月加權指數中位數 {_pct(s['med'])}、"
                f"上漲的比例 {s['up']:.0f}%（所有月份是 {_pct(a['med'])}、{a['up']:.0f}%）。")
    mood = "偏有利" if g >= 5 else "好壞參半" if g >= 3 else "偏不利"
    return f"一句話看懂：大環境 6 項條件裡 {g} 項有利，整體{mood}。{tail}"


def sec_tw_regime(eng) -> str:
    v = _v(eng) or {}
    cur, bt = v.get("cur") or {}, v.get("bt") or {}
    if not cur.get("each") or not bt.get("groups"):
        return ""
    body = f'<p class="rimp big2"><b>{T(lead(v), "")}</b></p>'
    body += ('<p>這張卡回答的是「現在的大環境對台股有利還是不利」，不是「什麼時候該進場」。'
             '每項條件都有明確的算法，最後看過去幾十年裡，同樣條件的月份之後股市怎麼走。</p>')
    items = []
    for k, x in cur["each"].items():
        mark = "🟢" if x["ok"] else "🔴" if x["ok"] is False else "⚪"
        items.append(f'<li>{mark} {esc(NAMES[k])} <span class="small muted">{esc(x.get("note") or "")} 資料 {esc(str(x.get("month") or "—"))}</span></li>')
    body += f'<ul class="lines">{"".join(items)}</ul>'
    if cur.get("extra"):
        body += ('<p class="small"><b>另外 5 項（只看現在，歷史不夠長，沒有放進回測）</b></p><ul class="lines">'
                 + "".join(f'<li>{"🟢" if ok else "🔴"} {esc(n)} <span class="small muted">{esc(d)}</span></li>' for n, ok, d in cur["extra"]) + "</ul>")
    head = '<tr><th>條件數</th><th class="r">月數</th>' + "".join(
        f'<th class="r">之後 {h} 個月：中位數／平均／上漲比例</th>' for h in HORIZONS) + "</tr>"
    rows = []
    for gp in bt["groups"]:
        cells = "".join(f'<td class="r">{_pct(gp["stats"][h]["med"])}／{_pct(gp["stats"][h]["avg"])}／'
                        f'{"—" if gp["stats"][h]["up"] is None else format(gp["stats"][h]["up"], ".0f") + "%"}'
                        f'<div class="small muted">{gp["stats"][h]["n"]} 個月</div></td>' for h in HORIZONS)
        here = " ← 現在" if gp["label"] != "全部月份" and gp["lo"] <= cur["green"] <= gp["hi"] else ""
        rows.append(f'<tr><td><b>{esc(gp["label"])}</b>{here}</td><td class="r">{gp["months"]}</td>{cells}</tr>')
    vd = verdict(bt)
    if vd:
        body += f'<p class="small"><b>這份清單準不準</b>：{esc(vd)}</p>'
    det = (f'<h3>歷史證據：{esc(str(bt.get("since")))}～{esc(str(bt.get("until")))} 每個月</h3>' + fold_rows(rows, 6, head, "組")
           + '<p class="small">看法：如果「有利條件多」的月份之後真的漲得比較好，這份清單才有參考價值；如果三組差不多，就代表大環境條件對台股的預測力有限。'
             '這是加權指數（不含股息）的月資料，相鄰月份的「之後 12 個月」大幅重疊，所以實際獨立的樣本比月數少很多。</p>')
    recent = [r for r in bt["rows"]][-24:]
    rr = [f'<tr><td>{esc(r["ym"])}</td><td class="r">{r["green"]} / 6</td>'
          + "".join(f'<td class="r">{_pct(r["fwd"][h])}</td>' for h in HORIZONS) + "</tr>" for r in reversed(recent)]
    det += ('<h4>最近 24 個月的條件數與之後的漲跌</h4>'
            + fold_rows(rr, 12, '<tr><th>月份</th><th class="r">有利條件</th>' + "".join(f'<th class="r">之後 {h} 個月</th>' for h in HORIZONS) + "</tr>", "個月"))
    body += f'<details class="sgx"><summary>{T("看歷史證據與算法", "Details")}</summary>{det}</details>'
    body += ('<p class="note">資料：<a href="' + SRC["cbc"] + '" target="_blank" rel="noopener">中央銀行</a>（加權指數月資料、10 年期公債殖利率、M1B／M2）、'
             '<a href="' + SRC["ndc"] + '" target="_blank" rel="noopener">國發會</a>（領先指標、海關出口、外銷訂單動向指數）、'
             '<a href="' + SRC["fred"] + '" target="_blank" rel="noopener">FRED</a>（美國 10 年期殖利率）、'
             '<a href="' + SRC["twse"] + '" target="_blank" rel="noopener">證交所</a>（每日指數、本益比、融資、三大法人）。'
             '每項資料公布時間不同，條件旁標示各自的資料月份。過去的統計不代表未來，也不是投資建議。</p>')
    h = card("台股進場環境：現在的大環境對股市有利還是不利", "Taiwan market environment", body, "wide",
             sub="6 項可回測的條件＋5 項現況指標，附 1990 年代以來的歷史統計")
    return h.replace('<section class="card', '<section id="twregime" class="card', 1)
