"""AI 視角 page: the market read only from numbers, through analogies from other sciences (地震、鳥群、亂流) and a
machine-memory search (相似日), then cross-checked against the site's human-built gauges.  Every figure is recomputed
each build and every method shows its own back-test, including the one that fails."""
from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd

from tools.sitekit import T, card, esc, num, spark

TENSE, NEUTRAL, CALM = "緊張", "中性", "平靜"


def _ph(eng):
    from wsb.analytics import physics as PH
    try:
        return PH.build(eng)
    except Exception:  # noqa: BLE001
        return {"available": False}


def _anchor(k: str):
    """Give a card an id so a dashboard block can jump to it."""
    def deco(f):
        def g(eng):
            h = f(eng)
            if not h:
                return h
            back = "" if k == "ai-top" else f'<p class="aiback"><a href="#ai" data-jump="ai-top">{T("↑ 回到重點", "↑ Back to summary")}</a></p>'
            h = h.replace('<section class="card', f'<section id="{k}" class="card', 1)
            return h[:h.rindex("</section>")] + back + "</section>"
        g.__name__ = f.__name__
        return g
    return deco


def _cls(state: Optional[str]) -> str:
    return {TENSE: "dn", CALM: "up"}.get(state or "", "muted")


def _pill(state: Optional[str]) -> str:
    return f'<b class="{_cls(state)}">{T(state, state)}</b>' if state else '<span class="muted">—</span>'


def _bt_line(bt: dict, dd: float, h: int) -> str:
    lo, hi = bt["ci"]
    lift = bt["cond"] / bt["base"] if bt.get("cond") is not None and bt.get("base") else None
    return (f"訊號亮起的日子，之後 {h} 個交易日內標普跌 ≥{dd:.0f}% 的頻率 {num(bt['cond'], 0)}%，平常 {num(bt['base'], 0)}%"
            f"（{num(lift, 1)} 倍）。以「第一次亮起」計算共 {bt['n']} 次，之後真的跌 ≥{dd:.0f}% 的 {bt['hit']} 次"
            f"（95% 區間 {num(lo, 0)}–{num(hi, 0)}%），其餘 {bt['n'] - bt['hit']} 次是假警報。")


def _fold(inner: str, label: str = "看細節、回測與方法") -> str:
    return f'<details class="sgx"><summary>{T(label, "Details, back-test and method")}</summary>{inner}</details>'


def _top(line) -> str:
    emo, txt = line
    return f'<p class="rimp">{emo} <b>{T(txt, txt)}</b></p>'


EMO = {TENSE: "🟠", NEUTRAL: "🟡", CALM: "🟢", None: "⚪"}


def lens_lines(ph: dict) -> dict:
    """One plain sentence per lens: (light, text)."""
    aft, flo, tur, ana = (ph.get(k) or {} for k in ("aftershock", "absorption", "turbulence", "analog"))
    out = {}
    if tur.get("available"):
        st = turb_state(tur)
        out["turb"] = (EMO[st], f"亂流：股、債、匯、商品的走法{'很不尋常' if st == TENSE else '正常' if st == CALM else '有點不尋常'}"
                                f"（2004 年以來第 {tur['pct']:.0f} 百分位）")
    if flo.get("available"):
        st = flock_state(flo)
        out["flock"] = (EMO[st], "鳥群：" + ("各產業開始一起動，衝擊容易擴散" if st == TENSE else
                                            "各產業各走各的，沒有一起逃" if st == CALM else "各產業同步程度普通")
                        + (f"（同步度 {flo['since'][:4]} 年以來最低）" if flo["ar_pct"] < 1 else f"（第 {flo['ar_pct']:.0f} 百分位）"))
    if aft.get("available"):
        st = quake_state(aft)
        out["quake"] = (EMO[st], "地震：" + (f"距上次大震 {aft['days_since']} 個交易日，餘震期已結束" if st == CALM else
                                            f"距上次大震才 {aft['days_since']} 個交易日，還在餘震期")
                        + f"（5 天內出現 ≥2% 單日波動的機率約 {num(aft['p_now'], 0)}%）")
    if ana.get("available"):
        ok = ana.get("auc") is not None and ana["auc"] >= 0.55
        out["analog"] = (EMO[analog_state(ana)] if ok else EMO[None],
                         f"AI 記憶：最像今天的 20 天裡有 {ana['n_bad']} 天之後大跌" + ("" if ok else "，但這方法回測比亂猜還差，不採計"))
    return out


def headline(ph: dict, hs: list) -> str:
    tur, flo = ph.get("turbulence") or {}, ph.get("absorption") or {}
    t, f = turb_state(tur), flock_state(flo)
    if t == TENSE and f == CALM:
        h = "局部衝擊、資金輪動，還不是全面踩踏"
    elif t == TENSE and f == TENSE:
        h = "結構正在一起失衡：系統性風險升高"
    elif f == TENSE:
        h = "各產業開始同步：系統變脆弱，但還沒出現亂流"
    elif t == CALM and f in (CALM, NEUTRAL):
        h = "市場結構平靜，沒有系統性警訊"
    else:
        h = "結構訊號混合，沒有一致的系統性警訊"
    a_t = sum(x == TENSE for x in (t, f, quake_state(ph.get("aftershock") or {})))
    h_t = sum(x[1] == TENSE for x in hs)
    if h_t > a_t:
        h += "；人心比數據更緊張"
    elif a_t > h_t:
        h += "；數據比人心更緊張"
    return h


def watch(ph: dict, ssi) -> list:
    tur, flo, aft = ph.get("turbulence") or {}, ph.get("absorption") or {}, ph.get("aftershock") or {}
    out = []
    if flo.get("available"):
        out.append(f"各產業同步度急升（短期變化 ≥ +1 個標準差，現在 {flo['dar']:+.1f}）→ 代表衝擊開始擴散到整個市場")
    if tur.get("available"):
        out.append(f"亂流持續在第 80 百分位以上（現在第 {tur['pct']:.0f}），而且壓力指數 SSI 升到 55 以上"
                   + (f"（現在 {ssi:.0f}）" if ssi is not None else ""))
    if aft.get("available"):
        out.append(f"出現單日漲跌 ≥4% 的大震 → 歷史上之後 5 天再出現 ≥2% 波動的機率約 {num(aft['rows'][0]['oos'], 0)}%")
    return out


def score_view(sc: dict) -> dict:
    """Which history to read today by: the exact present pattern when it is on and has enough days, else the score band."""
    if not sc.get("available"):
        return {}
    pat = sc.get("pattern") or {}
    row = sc["rows"][sc["cur"]]
    src, by = (pat, "pattern") if pat.get("now") else (row, "band")
    base = sc["base"]["crash"]
    d, pu, cr = src.get("digest"), src.get("pull"), src.get("crash")
    if d is None:
        return {}
    lift = cr / base if base else None
    ep = src.get("episodes") or 0
    ep_rate = src["ep_crash"] / ep * 100 if ep >= 5 else None
    mixed = ep_rate is not None and (cr > base) != (ep_rate > base)      # day-weighted and episode-weighted disagree
    if mixed:
        v = (f"以市場消化為主，大跌機率和平常差不多（按天算 {cr:.0f}%、按獨立事件算 {ep_rate:.0f}%，平常 {base:.0f}%；樣本少）")
    elif cr >= 30 or (lift or 0) >= 2:
        v = "大跌風險明顯偏高"
    elif d >= 50:
        v = "以市場消化為主" + (f"，但大跌機率是平常的 {lift:.1f} 倍" if lift and lift >= 1.2 else "")
    else:
        v = "回檔機率偏高，但多數沒有演變成大跌"
    return {"by": by, "ep_rate": ep_rate, "mixed": mixed, "digest": d, "pull": pu, "crash": cr, "base": base, "lift": lift, "verdict": v,
            "days": src.get("days_med"), "n": src.get("n"), "episodes": src.get("episodes"), "ep_crash": src.get("ep_crash")}


def _bar(d, pu, cr, compact: bool = False) -> str:
    seg = [(d, "up", "消化"), (pu, "muted", "回檔"), (cr, "dn", "大跌")]
    cells = "".join(f'<span class="{c}" style="flex:{max(v, 1):.0f}">{"" if compact else T(z, z) + f" {v:.0f}%"}</span>' for v, c, z in seg)
    return f'<div class="aibar">{cells}</div>'


def score_block(ph: dict) -> str:
    sc = ph.get("score") or {}
    v = score_view(sc)
    if not v:
        return ""
    band = sc["rows"][sc["cur"]]["band"]
    who = ("現在這種組合（亂流高、各產業各走各的）" if v["by"] == "pattern" else f"分數落在「{band}」區間時")
    line1 = f"AI 風險分數 {sc['now']:.0f}／100（{band}；{sc['since'][:4]} 年以來第 {sc['pct']:.0f} 百分位）"
    line2 = (f"{who}，歷史上之後 3 個月：消化（跌不到 5%）{v['digest']:.0f}%、回檔 5–10% {v['pull']:.0f}%、"
             f"大跌 ≥10% {v['crash']:.0f}%（平常 {v['base']:.0f}%）。")
    line3 = (f"如果真的大跌，歷史上中位數是在 {v['days']:.0f} 個交易日（約 {v['days'] / 21:.1f} 個月）內跌到 -10%；"
             "這是「萬一發生」時的時間分布，不是預告會在那天發生。" if v.get("days") else "")
    return (f'<p class="rimp big2"><b>{T(line1, line1)}</b><br>{T("判讀", "Reading")}：<b>{T(v["verdict"], v["verdict"])}</b></p>'
            f'{_bar(v["digest"], v["pull"], v["crash"])}<p class="small">{T(line2, line2)}{T(line3, line3)}</p>')


@_anchor("ai-score")
def sec_ai_score(eng) -> str:
    ph = _ph(eng)
    sc = (ph or {}).get("score") or {}
    if not sc.get("available"):
        return ""
    v = score_view(sc)
    rows = "".join(f'<tr{" class=hl" if k == sc["cur"] else ""}><td>{T(r["band"], r["band"])}（{r["lo"]}–{r["hi"]}）{" ◀ 現在" if k == sc["cur"] else ""}</td>'
                   f'<td class="r">{num(r.get("digest"), 0)}%</td><td class="r">{num(r.get("pull"), 0)}%</td><td class="r"><b>{num(r.get("crash"), 0)}%</b></td>'
                   f'<td class="r">{num(r.get("days_med"), 0)}</td><td class="r small muted">{r["n"]:,}</td></tr>' for k, r in enumerate(sc["rows"]))
    pat = sc.get("pattern") or {}
    pline = (f"「亂流高＋各產業各走各的」這種組合（現在{'正是' if pat.get('now') else '不是'}）共出現 {pat['n']} 天、{pat.get('episodes', 0)} 段，"
             f"之後 3 個月消化 {pat['digest']:.0f}%、回檔 {pat['pull']:.0f}%、大跌 {pat['crash']:.0f}%；"
             f"{pat.get('episodes', 0)} 段裡有 {pat.get('ep_crash', 0)} 段在 3 個月內跌了 10% 以上。") if pat else ""
    since = sc["since"][:4]
    note = T(f"分數＝亂流百分位、產業同步度百分位、餘震階段分數三者平均（都只和自己過去比），{since} 年起每天計算。"
             f"「消化」＝之後 3 個月最多跌不到 5%；「大跌」＝3 個月內從當天跌 10% 以上。分數沒有用結果資料調整任何參數，它對 3 個月內大跌的 AUC 是 {num(sc.get('auc'), 2)}（0.5＝亂猜），"
             "預測力有限，而且分數高低和大跌機率不是一直線：只有最高的區間明顯危險。重疊的日子不是獨立事件，段數比天數更能代表樣本大小。"
             "這是歷史頻率，不是預測，也不是投資建議。",
             "Score = mean of turbulence pct, synchrony pct and aftershock stage. Modest AUC; historical frequencies, not a forecast.")
    body = (score_block(ph) + _fold(
        f'<div class="scroll"><table class="mini"><thead><tr><th>{T("分數區間", "Score band")}</th><th class="r">{T("消化", "Digest")}</th>'
        f'<th class="r">{T("回檔 5–10%", "Pullback")}</th><th class="r">{T("大跌 ≥10%", "Crash")}</th>'
        f'<th class="r">{T("跌到 -10% 的天數中位數", "Median days to -10%")}</th><th class="r">{T("天數", "Days")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
        f'<p>{T(pline, pline)}</p>'
        f'<p class="note">{note}</p>',
        "點開看各分數區間的歷史結果"))
    return card("AI 風險分數：市場消化，還是會大跌？", "AI risk score: digestion or a fall?", body, "wide")


# ---------------------------------------------------------------- 熱度計：健康、偏貪婪、太熱，還是偏冷
def fuel(eng) -> list:
    """(name, hot, reading) for the slow 'fuel' that turns a strong market into an overheated one."""
    out = []
    try:
        from wsb.analytics import vulnerability as VU
        from wsb.data import fed_research as FR
        lt = {x["k"]: x for x in VU.build(eng, FR.load().get("ebp")).get("lights") or []}
    except Exception:  # noqa: BLE001
        lt = {}
    if "credit" in lt or "household" in lt:
        hot = any(lt.get(k, {}).get("state") == "hot" for k in ("credit", "household"))
        out.append(("借款暴增", hot, (lt.get("credit") or lt.get("household"))["txt"]))
    if "spreads" in lt or "ebp" in lt:
        hot = any(lt.get(k, {}).get("state") == "hot" for k in ("spreads", "ebp"))
        out.append(("信用定價太樂觀", hot, "；".join(lt[k]["txt"] for k in ("spreads", "ebp") if k in lt)))
    try:
        from wsb.analytics import valuation as VA
        items = {i["key"]: i for g in VA.build(eng).get("groups") or [] for i in g["items"]}
    except Exception:  # noqa: BLE001
        items = {}
    b = items.get("buffett")
    if b and b.get("pctile") is not None:
        out.append(("估值偏貴", b["pctile"] >= 90, f"巴菲特指標 {b['value']:.0f}%（{b.get('hist_start') or ''} 年以來第 {b['pctile']:.0f} 百分位）"))
    sp = [items[k] for k in ("hibeta", "arkk") if k in items and items[k].get("pctile") is not None]
    if sp:
        out.append(("投機資金追高", any(x["pctile"] >= 90 for x in sp), "；".join(f"{x['label']} 第 {x['pctile']:.0f} 百分位" for x in sp)))
    if "rzone" in lt:
        out.append(("R-zone：借款與資產同時過熱", lt["rzone"]["state"] == "hot", lt["rzone"]["txt"]))
    return out


def heat_status(h: dict, fu: list) -> tuple:
    hv = h.get("now") if h.get("available") else None
    hot = [n for n, x, _t in fu if x]
    rz = any(n.startswith("R-zone") and x for n, x, _t in fu)
    if rz or (len(hot) >= 3 and (hv or 0) >= 60):
        st, txt = "太熱", "漲勢強、底下燃料也多（" + "、".join(hot) + "）"
    elif len(hot) >= 2:
        st, txt = "偏貪婪", "價格走勢還算健康，但" + "、".join(hot)
    elif hv is not None and hv < 30:
        st, txt = "偏冷", "價格動能弱，市場在修正或恐懼中"
    else:
        st, txt = "健康", ("健康的強勢：動能好、燃料不多" if (hv or 0) >= 60 else "動能和燃料都在正常範圍")
    return st, txt, hot


HEAT_EMO = {"太熱": "🔴", "偏貪婪": "🟠", "健康": "🟢", "偏冷": "🔵"}


@_anchor("ai-heat")
def sec_ai_heat(eng) -> str:
    ph = _ph(eng)
    h = (ph or {}).get("heat") or {}
    fu = fuel(eng)
    if not h.get("available") and not fu:
        return ""
    st, txt, hot = heat_status(h, fu)
    top = f"{HEAT_EMO[st]} 熱度計：{st}——{txt}"
    parts = []
    if h.get("available"):
        c = h["comp"]
        lis = [f"離 200 日均線 {h['dev_pct']:+.1f}%（第 {c['dev']:.0f} 百分位）",
               f"上漲加速度第 {c['acc']:.0f} 百分位（越高越像「越漲越快」）",
               f"平靜度第 {c['calm']:.0f} 百分位（越高波動越低）"]
        lab = f"{h['band']} {h['now']:.0f}／100"
        parts.append(f'<div><b>{T("價格動能（AI 視角，只看價格）", "Price momentum (price only)")}</b>：{T(lab, lab)}'
                     f'<ul class="brief">{"".join(f"<li>{T(x, x)}</li>" for x in lis)}</ul></div>')
    if fu:
        lis = "".join(f'<li>{"🔥" if x else "・"} <b>{T(n, n)}</b>：{T(t, t)}</li>' for n, x, t in fu)
        parts.append(f'<div><b>{T("底下的燃料（決定熱是健康還是危險）", "Fuel underneath")}</b>：{len(hot)}／{len(fu)} {T("項偏熱", "hot")}<ul class="brief">{lis}</ul></div>')
    rows = ""
    for r in h.get("rows") or []:
        rows += (f'<tr><td>{r["yrs"]} 年</td><td>{T(r["band"], r["band"])}{"（%d–%d）" % (r["lo"], r["hi"]) if "lo" in r else ""}</td>'
                 f'<td class="r">{num(r["med"], 1, sign=True)}%</td><td class="r">{num(r["crash"], 0)}%（≥{r["dd"]}%）</td><td class="r small muted">{r["n"]:,}</td></tr>')
    table = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("之後", "Horizon")}</th><th>{T("價格熱度", "Heat")}</th>'
             f'<th class="r">{T("報酬中位數", "Median return")}</th><th class="r">{T("期間內大跌機率", "Chance of a big fall")}</th>'
             f'<th class="r">{T("天數", "Days")}</th></tr></thead><tbody>{rows}</tbody></table></div>') if rows else ""
    note = T(f"回測發現（標普 500，{h.get('since', '1932')} 年起）：只看價格的「熱」並不危險，價格最熱的時候，之後 1 年和 3 年的表現反而不差、大跌機率也比較低，"
             "因為強勁又平穩的漲勢通常會延續。所以「太熱」不能只看漲多少，要看底下有沒有燃料：借款暴增、信用定價太樂觀、估值太貴、投機資金追高。"
             "1999 年和 2007 年的問題都在燃料，不在漲勢本身。燃料的判讀依據 Greenwood 等（2022）、López-Salido 等（2017）、Gilchrist & Zakrajšek（2012），"
             "詳見「全方位風險」的累積脆弱度和「估值泡沫」頁。燃料多不代表馬上出事，可能持續好幾年。這是現況描述，不是預測，也不是投資建議。",
             "Price heat alone has not been dangerous since 1932; the fuel (credit, valuation, speculation) decides. Not a forecast or advice.")
    body = (f'<p class="rimp big2"><b>{T(top, top)}</b></p><div class="g2">{"".join(parts)}</div>'
            + _fold(table + f'<p class="note">{note}</p>', "點開看回測：價格熱度之後的表現"))
    return card("熱度計：風險退散後，是健康還是太熱？", "Heat gauge: healthy, greedy or overheated?", body, "wide")


# ---------------------------------------------------------------- 人類是不是在嚇自己
def fear_backtest(eng, pct_cut: float = 80.0, h: int = 63, dd: float = 10.0) -> Optional[dict]:
    """What happened after the days the crowd was scared (VIX in its own top 20 % of the past year), since 1995.
    Past-only percentile: each day is ranked against the 252 days before it."""
    try:
        v = eng.market.series("^VIX").dropna()
        s = eng.market.series("^GSPC").dropna()
    except Exception:  # noqa: BLE001
        return None
    if len(v) < 1500 or len(s) < 1500:
        return None
    import numpy as np
    fwd = s.shift(-h) / s - 1
    low = s[::-1].rolling(h, min_periods=1).min()[::-1].shift(-1) / s - 1
    arr = v.values
    pc = np.full(len(arr), np.nan)
    for k in range(252, len(arr)):
        w = arr[k - 252:k]
        pc[k] = (w < arr[k]).mean() * 100
    df = pd.concat([pd.Series(pc, index=v.index, name="p"), fwd.rename("f"), low.rename("m")], axis=1)
    now_p = df["p"].dropna().iloc[-1] if df["p"].notna().any() else None
    df = df.dropna()
    if len(df) < 1000:
        return None
    sc = df[df["p"] >= pct_cut]
    if len(sc) < 100:
        return None
    return {"since": str(df.index[0].year), "n": len(sc), "now_pct": now_p, "vix": float(arr[-1]),
            "med": float(sc["f"].median() * 100), "med_all": float(df["f"].median() * 100),
            "up": float((sc["f"] > 0).mean() * 100), "up_all": float((df["f"] > 0).mean() * 100),
            "crash": float((sc["m"] <= -dd / 100).mean() * 100), "crash_all": float((df["m"] <= -dd / 100).mean() * 100)}


def human_fear(eng) -> Tuple[Optional[float], List[str]]:
    """How scared people are, 0–100: the mean of (100 − Fear & Greed), VIX's percentile in the past year, and SSI."""
    parts, vals = [], []
    fg = None
    try:
        from wsb.analytics import bottom as BT
        cr = getattr(getattr(eng, "crypto", None), "data", None) or {}
        fg = cr.get("cnn_fng")
        if fg is None:
            s = BT._ser(BT.load(), "fg")
            fg = float(s.iloc[-1]) if len(s) else None
    except Exception:  # noqa: BLE001
        fg = None
    if fg is not None:
        vals.append(100 - float(fg))
        parts.append(f"恐懼與貪婪 {fg:.0f}" + ("（極度恐懼）" if fg < 25 else "（恐懼）" if fg < 45 else ""))
    try:
        v = eng.market.series("^VIX").dropna()
        if len(v) > 252:
            p = float((v.iloc[-253:-1] < v.iloc[-1]).mean() * 100)
            vals.append(p)
            parts.append(f"VIX {v.iloc[-1]:.1f}（近一年第 {p:.0f} 百分位）")
    except Exception:  # noqa: BLE001
        pass
    ssi = getattr(getattr(eng, "stress", None), "score", None)
    if ssi is not None:
        vals.append(float(ssi))
        parts.append(f"壓力指數 SSI {ssi:.0f}")
    return (sum(vals) / len(vals) if vals else None), parts


def _stab(eng) -> dict:
    try:
        from tools import site_stability as SST
        return SST._v(eng) or {}
    except Exception:  # noqa: BLE001
        return {}


# why each slow "fuel" matters, in plain words (the research behind it is in the heat-gauge card)
FUEL_WHY = {"信用定價太樂觀": "借錢的人幾乎不用多付風險補償，大家都覺得不會出事；研究發現這種時候 1–2 年後反而比較容易出問題",
            "估值偏貴": "股價相對整體經濟的規模創新高；估值不決定什麼時候跌，但決定一旦跌下來會跌多深",
            "借款暴增": "企業或家庭借錢的速度比收入快很多；過去的金融危機前幾年幾乎都有這個現象",
            "投機資金追高": "高風險股票被追得很高，代表市場願意為夢想付高價，回檔時跌得最兇",
            "R-zone": "借錢和資產價格同時過熱，學術研究中危機機率最高的組合"}


def ai_verdict(eng, ph: dict) -> dict:
    """The page's conclusion: what people fear that the data does not support, what the data shows that people do not
    fear, and the few readings that would change the conclusion.  Every line is a fixed rule on numbers, no headlines."""
    sc = ph.get("score") or {}
    v = score_view(sc)
    fear, fparts = human_fear(eng)
    ai = float(sc["now"]) if sc.get("available") else None
    tur, flo, aft, ana = (ph.get(k) or {} for k in ("turbulence", "absorption", "aftershock", "analog"))
    over, under, trig = [], [], []
    fb = fear_backtest(eng)
    if fear is not None and fear >= 55 and fb:
        over.append(("「大家都很怕，所以要跌了」",
                     f"1995 年以來，VIX 落在近一年前 20% 高的 {fb['n']:,} 天，之後 3 個月報酬中位數 {fb['med']:+.1f}%（平常 {fb['med_all']:+.1f}%），"
                     f"{fb['up']:.0f}% 的時候是上漲（平常 {fb['up_all']:.0f}%）。恐慌代表接下來晃得比較大，不代表一定往下："
                     f"同一批日子 3 個月內跌 ≥10% 的機率是 {fb['crash']:.0f}%（平常 {fb['crash_all']:.0f}%）。", "ai-cross"))
    if v and not (v["crash"] >= 30 or (v.get("lift") or 0) >= 2):
        over.append(("「要崩盤了」",
                     f"用跨資產結構算的 AI 風險分數是 {sc['now']:.0f}／100；歷史上同樣的狀態，之後 3 個月有 "
                     f"{v['digest']:.0f}% 只是消化（跌不到 5%），大跌 ≥10% 的機率"
                     + (f"按獨立事件算約 {v['ep_rate']:.0f}%" if v.get("ep_rate") is not None else f"約 {v['crash']:.0f}%")
                     + f"，平常是 {v['base']:.0f}%。", "ai-score"))
    if turb_state(tur) == TENSE and flock_state(flo) == CALM:
        over.append(("「到處都在跌，要一起崩」",
                     f"跨資產走法確實很不尋常（亂流第 {tur['pct']:.0f} 百分位），但 9 大產業各走各的"
                     + ("，同步度是 " + flo["since"][:4] + " 年以來最低" if flo["ar_pct"] < 1 else f"（同步度第 {flo['ar_pct']:.0f} 百分位）")
                     + "。衝擊集中在部分資產，資金在輪動，不是全面一起逃。", "ai-flock"))
    if quake_state(aft) == CALM:
        over.append(("「大跌會一波接一波」",
                     f"上次單日 ≥{aft['main']:.0f}% 的大震已經是 {aft['days_since']} 個交易日前，餘震期結束；"
                     f"接下來 5 天出現 ≥2% 單日波動的機率約 {num(aft['p_now'], 0)}%，屬於背景水準。", "ai-quake"))
    hh = ph.get("heat") or {}
    fu = fuel(eng)
    for n, hot, txt in fu:
        if hot:
            under.append((n, FUEL_WHY.get(n.split("：")[0], "") + f"（數據：{txt}）", "ai-heat"))
    stb = _stab(eng)
    for k, lab in (("basis", "美債基差交易"), ("ai", "AI 巨頭靠借錢擴張"), ("funding", "短期資金"), ("refunding", "財政部發債")):
        x = stb.get(k) or {}
        if x.get("emoji") in ("🟡", "🔴"):
            under.append((f"{lab}（{x['state']}）", x.get("read", ""), None))
    if flo.get("available"):
        trig.append(("各產業開始一起動", f"同步度短期變化 ≥ +1 個標準差（現在 {flo['dar']:+.1f}）：衝擊從局部擴散到整個市場，結論會從「消化」改成「系統性」。", "ai-flock"))
    if tur.get("available"):
        ssi = getattr(getattr(eng, "stress", None), "score", None)
        trig.append(("亂流＋壓力一起升", f"亂流維持第 80 百分位以上（現在第 {tur['pct']:.0f}），而且壓力指數 SSI 升破 55"
                     + (f"（現在 {ssi:.0f}）" if ssi is not None else "") + "。", "ai-turb"))
    if stb.get("funding"):
        trig.append(("資金和信用開始緊", "SOFR 連續高於準備金利率、常設回購被大量動用，或投資級（BBB）利差跟著垃圾債擴大：慢慢累積的燃料開始被點燃。", None))
    trig.append(("出現單日 ≥4% 的大震", "餘震計時器歸零，之後幾天再出現大波動的機率會跳升。", "ai-quake"))
    if fear is None or ai is None:
        lab, txt = "資料不足", "人類情緒或 AI 結構指標有缺，暫時無法比較。"
    elif fear - ai >= 20:
        lab = "人類比數據緊張"
        txt = ("現在比較像人類在嚇自己：情緒和新聞的恐慌，沒有反映在價格結構上（局部衝擊、資金輪動，不是全面踩踏）。"
               + ("但真正該注意的是大家沒在怕、正在慢慢累積的燃料：" + "、".join(u[0].split("（")[0] for u in under[:3]) + "。" if under else ""))
    elif ai - fear >= 20:
        lab = "數據比人類緊張"
        txt = "價格結構在變差，但大家還沒反應過來；這是比較需要小心的組合。"
    else:
        lab = "人類和數據差不多"
        txt = "人類的感受和價格結構大致一致，沒有明顯的自己嚇自己，也沒有被忽略的結構警訊。"
    return {"label": lab, "text": txt, "fear": fear, "fparts": fparts, "ai": ai, "over": over, "under": under, "trig": trig, "fb": fb}


def _gauge(fear: Optional[float], ai: Optional[float]) -> str:
    def row(lab, val, cls):
        if val is None:
            return ""
        return (f'<div class="fgrow"><span class="fgl">{T(lab, lab)}</span><span class="fgbar"><i class="{cls}" style="width:{max(2, min(100, val)):.0f}%"></i></span>'
                f'<b class="fgv">{val:.0f}</b></div>')
    return f'<div class="fg">{row("人類的恐懼", fear, "dn")}{row("AI 測到的結構風險", ai, "ac")}</div>'


def _col(title: str, items: list, empty: str) -> str:
    lis = "".join(f'<li><b>{T(a, a)}</b>：{T(b, b)}' + (f' <a href="#ai" data-jump="{k}" class="small">{T("看依據 ›", "Evidence ›")}</a>' if k else "") + "</li>"
                  for a, b, k in items)
    return f'<div class="aicol"><h3>{T(title, title)}</h3>' + (f"<ul>{lis}</ul>" if lis else f'<p class="small muted">{T(empty, empty)}</p>') + "</div>"


@_anchor("ai-top")
def sec_ai_brief(eng) -> str:
    """AI 的結論: is the crowd scaring itself?  Fear vs structure, three columns (over-feared / under-feared / what would
    change the conclusion), then one block per AI gauge that jumps to its detail card."""
    ph = _ph(eng)
    if not ph.get("available"):
        return ""
    rows = cross_rows(eng)
    hs = [r["h"] for r in rows]
    head = headline(ph, hs)
    vd = ai_verdict(eng, ph)
    v = score_view(ph.get("score") or {})
    sc = ph.get("score") or {}
    n_ok = sum(r["v"] == "一致" for r in rows)
    n_split = sum(r["v"] == "分歧" for r in rows)
    cnt = f"AI 視角交叉比對：{n_ok} 項一致、{n_split} 項分歧"
    sline = ((f"AI 風險分數 {sc['now']:.0f}／100：{v['verdict']}" + ("" if v["mixed"] else f"（3 個月內大跌 {v['crash']:.0f}%，平常 {v['base']:.0f}%）")) if v else "")
    aft, flo, tur, ana = (ph.get(k) or {} for k in ("aftershock", "absorption", "turbulence", "analog"))
    tiles = []
    if v:
        band = sc["rows"][sc["cur"]]["band"]
        tiles.append(("ai-score", "📊 AI 風險分數", f"{sc['now']:.0f}<small>／100</small>", f"{band}・{sc['since'][:4]} 年以來第 {sc['pct']:.0f} 百分位", ""))
        short = v["verdict"].split("（")[0].split("，")[0]
        when = (f"消化 {v['digest']:.0f}%・回檔 {v['pull']:.0f}%・大跌 {v['crash']:.0f}%"
                + (f"；萬一大跌，中位數約 {v['days'] / 21:.1f} 個月內跌到 -10%" if v.get("days") else ""))
        tiles.append(("ai-score", "⚖️ 消化還是大跌（3 個月）", short, when, _bar(v["digest"], v["pull"], v["crash"], compact=True)))
    if tur.get("available"):
        st = turb_state(tur)
        tiles.append(("ai-turb", f"{EMO[st]} 亂流", f"第 {tur['pct']:.0f}<small> 百分位</small>",
                      "股債匯商品走法很不尋常" if st == TENSE else "跨資產走法正常" if st == CALM else "跨資產走法有點不尋常", ""))
    if flo.get("available"):
        st = flock_state(flo)
        big = "歷史最低" if flo["ar_pct"] < 1 else f"第 {flo['ar_pct']:.0f}<small> 百分位</small>"
        tiles.append(("ai-flock", f"{EMO[st]} 鳥群同步度", big,
                      "各產業開始一起動" if st == TENSE else "各產業各走各的，沒有一起逃" if st == CALM else "同步程度普通", ""))
    if aft.get("available"):
        st = quake_state(aft)
        tiles.append(("ai-quake", f"{EMO[st]} 地震餘震", f"{aft['days_since']}<small> 天</small>",
                      ("距上次大震，餘震期已結束" if st == CALM else "距上次大震，還在餘震期") + f"・5 天內 ≥2% 波動機率 {num(aft['p_now'], 0)}%", ""))
    if ana.get("available"):
        ok = ana.get("auc") is not None and ana["auc"] >= 0.55
        tiles.append(("ai-analog", f"{EMO[analog_state(ana)] if ok else EMO[None]} AI 記憶（相似日）", "採計" if ok else "不採計",
                      f"回測 AUC {num(ana['auc'], 2)}" + ("" if ok else "，比亂猜還差"), ""))
    hh = ph.get("heat") or {}
    fu = fuel(eng)
    if hh.get("available") or fu:
        hst, htxt, hhot = heat_status(hh, fu)
        tiles.append(("ai-heat", f"{HEAT_EMO[hst]} 熱度計（健康還是太熱）", hst,
                      (f"價格動能 {hh['now']:.0f}／100・" if hh.get("available") else "") + f"燃料 {len(hhot)}／{len(fu)} 項偏熱", ""))
    tiles.append(("ai-cross", "🤝 人類指標 vs AI", f"{n_ok}<small> 一致</small>・{n_split}<small> 分歧</small>", cnt, ""))
    grid = "".join(f'<a class="aitile" href="#ai" data-jump="{k}"><span class="tl">{T(lab, lab)}</span><span class="tv">{big}</span>'
                   f'<span class="tt">{T(txt, txt)}</span>{extra}<span class="go">{T("看細節 ›", "Details ›")}</span></a>'
                   for k, lab, big, txt, extra in tiles)
    fp = "・".join(vd["fparts"])
    note = T("「人類在怕」那一欄，是把群眾情緒和可以回測的歷史放在一起看；「沒在怕」那一欄，是學術研究證實會在 1–3 年後出問題、但平常沒人討論的慢變數。"
             "全部只看數字、不讀新聞標題；描述現在的風險水位，不預告哪一天會跌，也不是投資建議。", "Numbers only; not a timing tool, not advice.")
    body = (f'<p class="rimp big2"><b>{T("AI 判斷：" + vd["label"], "")}</b>——{T(vd["text"], "")}</p>'
            + _gauge(vd["fear"], vd["ai"])
            + f'<p class="small muted">{T("人類的恐懼＝" + fp + " 的平均；AI 結構風險＝下方的 AI 風險分數（只看價格之間的結構）。", "")}</p>'
            f'<div class="aicols">'
            + _col("😨 人類在怕，但數據說還好", vd["over"], "目前沒有明顯被誇大的恐懼。")
            + _col("🙈 人類沒在怕，但數據在累積", vd["under"], "目前沒有被忽略的累積風險。")
            + _col("🎯 出現這些，結論才會改", vd["trig"], "—")
            + "</div>"
            f'<p class="small"><b>{T("市場結構", "Structure")}</b>：{T(head, head)}' + (f'<br>{T(sline, sline)}' if sline else "") + "</p>"
            f'<h3 class="aih">{T("各項 AI 指標（點區塊看細節）", "Each machine gauge (tap for details)")}</h3><div class="aigrid">{grid}</div>'
            f'<p class="note">{note}</p>')
    return card("AI 的結論：人類是不是在嚇自己？", "The machine's verdict: is the crowd scaring itself?", body, "wide")



# ---------------------------------------------------------------- the four lenses
def quake_state(a: dict) -> Optional[str]:
    if not a.get("available"):
        return None
    return TENSE if a["cur"] <= 2 else NEUTRAL if a["cur"] == 3 else CALM


def flock_state(a: dict) -> Optional[str]:
    if not a.get("available"):
        return None
    return TENSE if a["dar"] >= 1 or a["ar_pct"] >= 80 else CALM if a["ar_pct"] <= 20 and a["dar"] < 0 else NEUTRAL


def turb_state(a: dict) -> Optional[str]:
    if not a.get("available"):
        return None
    return TENSE if a["pct"] >= 80 else CALM if a["pct"] <= 40 else NEUTRAL


def analog_state(a: dict) -> Optional[str]:
    if not a.get("available") or not a.get("base"):
        return None
    r = a["p"] / a["base"]
    return TENSE if r >= 1.3 else CALM if r <= 0.7 else NEUTRAL


@_anchor("ai-quake")
def sec_ai_quake(eng) -> str:
    ph = _ph(eng)
    a = (ph or {}).get("aftershock") or {}
    if not a.get("available"):
        return ""
    rows = "".join(f'<tr{" class=hl" if k == a["cur"] else ""}><td>{T(r["band"], r["band"])}{" ◀ 現在" if k == a["cur"] else ""}</td>'
                   f'<td class="r">{num(r["fit"], 0)}%</td><td class="r"><b>{num(r["oos"], 0)}%</b></td><td class="r small muted">{r["n_oos"]:,}</td></tr>'
                   for k, r in enumerate(a["rows"]))
    f = a.get("fit") or {}
    quiet = a["cur"] == len(a["rows"]) - 1
    lead = (f"上一次 ≥{a['main']:.0f}% 的「主震」是 {a['last_main']}（{a['last_main_r']:+.1f}%），已經過了 {a['days_since']} 個交易日，"
            + ("餘震期已經結束，市場回到背景狀態。" if quiet else "仍在餘震期內。")
            + f"最近 20 個交易日最大單日波動 {a['recent_max']:.1f}%（{a['recent_max_d']}），≥{a['after']:.0f}% 的日子 {a['recent_big']} 天。"
            f"照 {a['split']} 年之後的樣本外紀錄，處在這個階段時，接下來 {a['next']} 個交易日出現 ≥{a['after']:.0f}% 單日波動的頻率約 {num(a['p_now'], 0)}%；"
            f"以過去一年的背景頻率估算約 {num(a['p_bg'], 0)}%。")
    body = (f'<p>{T(lead, lead)}</p><div class="scroll"><table class="mini"><thead><tr><th>{T("距離上次主震", "Since last main shock")}</th>'
            f'<th class="r">{T("1950–" + a["split"] + " 年", "In sample")}</th><th class="r">{T(a["split"] + " 年後（樣本外）", "Out of sample")}</th>'
            f'<th class="r">{T("天數", "Days")}</th></tr></thead><tbody>{rows}</tbody></table></div>')
    note = T(f"地震學的大森定律：大地震後，餘震頻率依 K／(t + c)^p 遞減。金融市場也有同樣規律（Lillo & Mantegna 2003；Petersen 等 2010）。"
             f"本站用標普 500 自 1928 年的日線，把單日漲跌 ≥{a['main']:.0f}% 當主震、≥{a['after']:.0f}% 當餘震；"
             f"以 1950–{a['split']} 年擬合的衰減指數 p ≈ {num(f.get('p'), 2)}（{f.get('n_main', 0)} 次主震）。"
             f"樣本外的頻率比樣本內高（近 30 年 ≥{a['after']:.0f}% 的日子變多），但「越接近主震、越容易再震」的排序完全成立。"
             "限制：它只能描述主震之後的餘震，第一次大震本身預測不到；也不分漲跌方向。",
             "Omori law on S&P 500 daily moves since 1928; fitted 1950–split, checked after. It cannot foresee the first shock.")
    return card("地震學：餘震計時器", "Seismology: aftershock clock", _top(lens_lines(ph)["quake"]) + _fold(body + f'<p class="note">{note}</p>'), "wide")


@_anchor("ai-flock")
def sec_ai_flock(eng) -> str:
    ph = _ph(eng)
    a = (ph or {}).get("absorption") or {}
    if not a.get("available"):
        return ""
    c = ph["cfg"]
    st = flock_state(a)
    lead = (f"9 大產業的走勢被前 2 個共同因子解釋了 {a['ar']:.1f}%（過去一年平均 {a['ar_1y']:.1f}%），在 {a['since'][:4]} 年以來第 {a['ar_pct']:.0f} 百分位；"
            f"短期變化 ΔAR = {a['dar']:+.2f} 個標準差。"
            + ("各產業正在越來越一起動：鳥群開始同步，系統比較脆弱。" if st == TENSE else
               "各產業各走各的，同步度偏低：資金在產業間輪動，而不是一起逃。" if st == CALM else "同步度在常態範圍。"))
    body = f'<p>{T(lead, lead)}</p>{spark(a["spark"])}<p>{T(_bt_line(a["bt"], c["dd"], c["horizon"]), _bt_line(a["bt"], c["dd"], c["horizon"]))}</p>'
    note = T("鳥群、魚群越同步，越容易整群一起轉向。金融版是「吸收比率」（Kritzman、Li、Page & Rigobon 2011）："
             "用主成分分析看共同因子能解釋多少變異；比例越高，衝擊越容易一次擴散到所有資產。"
             "原論文用 51 個產業，本站用 9 檔產業 ETF（1998 年起），500 日、半衰期 250 日的加權共變異數；ΔAR ≥ 1 個標準差算「同步升高」。"
             "本站版本的回測預警力偏弱，請和其他指標一起看。",
             "Absorption ratio on the 9 sector SPDRs; weak lift in this site's back-test.")
    return card("鳥群：市場同步度（吸收比率）", "Flocking: absorption ratio", _top(lens_lines(ph)["flock"]) + _fold(body + f'<p class="note">{note}</p>'), "wide")


@_anchor("ai-turb")
def sec_ai_turb(eng) -> str:
    ph = _ph(eng)
    a = (ph or {}).get("turbulence") or {}
    if not a.get("available"):
        return ""
    c = ph["cfg"]
    lead = (f"最近 5 日跨資產亂流指數 {a['t5']:.2f}（1＝平常），在 {a['since'][:4]} 年以來第 {a['pct']:.0f} 百分位"
            + ("：目前處在亂流區，股、債、匯、商品的走法和過去 3 年的常態明顯不同。" if a["pct"] >= c["tb_pct"] else "：不在亂流區。")
            + f"近 20 日最不尋常的一天是 {a['top_d']}（{a['top_v']:.1f}）。")
    body = f'<p>{T(lead, lead)}</p>{spark(a["spark"])}<p>{T(_bt_line(a["bt"], c["dd"], c["horizon"]), _bt_line(a["bt"], c["dd"], c["horizon"]))}</p>'
    note = T("飛機遇到亂流時，接下來幾分鐘通常還會再晃。Kritzman & Li（2010）用 Mahalanobis 距離衡量「今天的跨資產走法有多不正常」，"
             "不只看漲跌大小，也看資產之間的關係有沒有被打亂，例如股債同跌。"
             "本站用 9 大產業、10 年殖利率、黃金、美元、原油，對照過去 3 年的平均與共變異數，5 日平均和自己的歷史比，第 80 百分位以上算亂流。"
             "亂流會延續，適合描述「現在的天氣」，不是預告明天；回測中假警報很多。",
             "Kritzman–Li turbulence (Mahalanobis distance) across sectors, yields, gold, dollar and oil. Persistent; many false alarms.")
    return card("亂流：跨資產異常程度", "Turbulence: how unusual today's cross-asset move is", _top(lens_lines(ph)["turb"]) + _fold(body + f'<p class="note">{note}</p>'), "wide")


@_anchor("ai-analog")
def sec_ai_analog(eng) -> str:
    ph = _ph(eng)
    a = (ph or {}).get("analog") or {}
    if not a.get("available"):
        return ""
    c = ph["cfg"]
    rows = "".join(f'<tr><td class="nw">{esc(x["date"])}</td><td class="r">{x["dist"]:.2f}</td>'
                   f'<td class="r {"dn" if x["drop"] <= -c["dd"] else ""}">{x["drop"]:+.1f}%</td><td class="r">{x["ret"]:+.1f}%</td></tr>'
                   for x in a["nb"][:10])
    odd = "、".join(f"{n}（{v:+.1f} 個標準差）" for n, v in a["unusual"])
    skill = a.get("auc") is not None and a["auc"] >= 0.55
    lead = (f"用 {a['n_feat']} 個市場特徵，從 {a['since'][:4]} 年以來找出和今天最像的 {a['k']} 天："
            f"其中 {a['n_bad']} 天之後 {c['horizon']} 個交易日內跌了 ≥{c['dd']:.0f}%（{a['p']:.0f}%，平常 {a['base']:.0f}%），"
            f"之後 3 個月報酬中位數 {a['med_ret']:+.1f}%，最差 {a['worst']:+.1f}%。今天最突出的特徵：{odd}。")
    verdict = (f"走步回測：2008 年起每 5 天用當時已知的資料預測一次，共 {a['n_test']} 次，AUC {num(a['auc'], 2)}（0.5＝亂猜）"
               + ("，有一定預測力。" if skill else
                  f"，不如亂猜，誤差也比直接用歷史平均（Brier {num(a['brier'], 3)} 對 {num(a['brier0'], 3)}）大。"
                  "所以上面的相似日只能當「歷史上有哪些日子長得像今天」的參考，不能當成機率。"))
    body = (f'<p>{T(lead, lead)}</p><p><b>{T(verdict, verdict)}</b></p><div class="scroll"><table class="mini"><thead><tr>'
            f'<th>{T("最像的日子", "Closest days")}</th><th class="r">{T("距離", "Distance")}</th>'
            f'<th class="r">{T("之後 3 個月最大跌幅", "Worst in next 3m")}</th><th class="r">{T("3 個月後報酬", "3m return")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')
    note = T("這是最直覺的 AI 方法：k 最近鄰（k-NN）記憶搜尋，不用任何人類理論，只問「過去哪些日子看起來最像今天」。"
             "特徵：標普 1 個月與 3 個月漲跌、離高點距離、1 個月波動、VIX 水準與變化、10 年殖利率、美元、油價、金價的 3 個月變化；"
             "每一天都只用「那天以前」的資料標準化，相似日之間至少相隔 10 個交易日，而且只從結果已經知道的日子裡找。"
             "回測失敗本身就是發現：大跌常常從「看起來很平靜」的日子開始，而「看起來很緊張」的日子之後反而常反彈，"
             "所以只比對表面狀態的機器記憶，會系統性猜錯方向。這和學界說的「波動悖論」（低波動時槓桿累積）一致。",
             "k-NN analogue search on 10 features, past-only scaling. Its walk-forward AUC is below 0.5 — shown as a lesson.")
    return card("AI 記憶：歷史上最像今天的日子", "Machine memory: the days most like today", _top(lens_lines(ph)["analog"]) + _fold(body + f'<p class="note">{note}</p>'), "wide")


# ---------------------------------------------------------------- cross-check
def human_states(eng) -> List[Tuple[str, Optional[str], str]]:
    """(label, state, reading) for the site's human-built gauges, in the order of the AI lenses."""
    out = []
    ssi = getattr(getattr(eng, "stress", None), "score", None)
    out.append(("壓力指數 SSI（人類挑選的 20 多個指標合成）", None if ssi is None else TENSE if ssi >= 55 else CALM if ssi < 40 else NEUTRAL,
                "—" if ssi is None else f"{ssi:.0f} 分"))
    fg = None
    try:
        from wsb.analytics import bottom as BT
        cr = getattr(getattr(eng, "crypto", None), "data", None) or {}
        fg = cr.get("cnn_fng")
        if fg is None:
            s = BT._ser(BT.load(), "fg")
            fg = float(s.iloc[-1]) if len(s) else None
    except Exception:  # noqa: BLE001
        fg = None
    out.append(("恐懼與貪婪指數（群眾情緒）", None if fg is None else TENSE if fg < 35 else CALM if fg > 65 else NEUTRAL,
                "—" if fg is None else f"{fg:.0f}"))
    q = eng.market.q("^VIX") or {}
    v = q.get("price")
    if v is None:
        s = eng.market.series("^VIX")
        v = float(s.iloc[-1]) if len(s) else None
    out.append(("VIX 恐慌指數（選擇權買家的恐懼）", None if v is None else TENSE if v >= 25 else CALM if v <= 15 else NEUTRAL,
                "—" if v is None else f"{v:.1f}"))
    h63 = next((h for h in ((getattr(eng, "odds", None) or {}).get("horizons") or []) if h.get("days") == 63), None)
    lift = h63.get("lift_adj") if h63 else None
    out.append(("崩跌機率模型（人類設計的邏輯迴歸）", None if lift is None else TENSE if lift >= 1.15 else CALM if lift <= 0.85 else NEUTRAL,
                "—" if not h63 else f"63 日內跌 ≥10%：{num(h63.get('adjusted'), 1)}%（平常 {num(h63.get('base_rate'), 1)}%）"))
    return out


def agree(a: Optional[str], b: Optional[str]) -> Optional[str]:
    if a is None or b is None:
        return None
    if a == b:
        return "一致"
    return "分歧" if {a, b} == {TENSE, CALM} else "部分一致"


def cross_rows(eng) -> List[dict]:
    ph = _ph(eng)
    if not ph.get("available"):
        return []
    hs = human_states(eng)
    aft, flo, tur, ana = (ph.get(k) or {} for k in ("aftershock", "absorption", "turbulence", "analog"))
    ai = [("亂流指數（跨資產走法有多不正常）", turb_state(tur), f"第 {tur['pct']:.0f} 百分位" if tur.get("available") else "—"),
          ("市場同步度（鳥群）", flock_state(flo), (f"吸收比率第 {flo['ar_pct']:.0f} 百分位" + ("（2000 年以來最低）" if flo['ar_pct'] < 1 else "")) if flo.get("available") else "—"),
          ("餘震計時器（地震學）", quake_state(aft), f"距上次主震 {aft['days_since']} 天" if aft.get("available") else "—"),
          ("相似日搜尋（AI 記憶，回測無預測力）", analog_state(ana), f"{ana['p']:.0f}%（平常 {ana['base']:.0f}%）" if ana.get("available") else "—")]
    dims = ["現在的壓力有多大", "群眾是不是一起動", "是不是剛受過衝擊", "未來 3 個月大跌的機率"]
    out = [{"dim": d, "h": h, "a": x, "v": agree(h[1], x[1])} for d, h, x in zip(dims, hs, ai)]
    if not (ana.get("auc") is not None and ana["auc"] >= 0.55):
        out[-1]["v"] = "不計入"                      # a lens that fails its own back-test does not vote
    return out


def reading(rows: List[dict], ph: dict) -> str:
    n_ok = sum(r["v"] == "一致" for r in rows)
    n_split = sum(r["v"] == "分歧" for r in rows)
    h_t = sum(r["h"][1] == TENSE for r in rows)
    a_t = sum(r["a"][1] == TENSE for r in rows[:3])
    n_vote = sum(r["v"] not in (None, "不計入") for r in rows)
    parts = [f"{n_vote} 個可比較的面向中 {n_ok} 項一致、{n_split} 項分歧（相似日搜尋回測沒有預測力，不計入）。" if n_vote < len(rows) else f"{len(rows)} 個面向中 {n_ok} 項一致、{n_split} 項分歧。"]
    if h_t >= 2 and a_t <= 1:
        parts.append("人類的指標比較緊張，但物理類比指標大多沒有跟著緊張：目前的緊張比較像情緒和局部壓力，還不是整個系統一起失衡。")
    elif a_t >= 2 and h_t <= 1:
        parts.append("物理類比指標在緊張、人類的指標卻還平靜：這是比較需要留意的組合，代表結構在變化但大家還沒反應。")
    elif a_t >= 2 and h_t >= 2:
        parts.append("兩邊都在緊張：各種角度一致，波動通常會持續一段時間。")
    else:
        parts.append("兩邊都只有零星的緊張訊號，沒有形成一致的系統性警訊。")
    tur, flo, aft = ph.get("turbulence") or {}, ph.get("absorption") or {}, ph.get("aftershock") or {}
    if tur.get("available") and tur["pct"] >= 80 and flo.get("available") and flo["ar_pct"] <= 20:
        parts.append("值得注意的組合：跨資產走法很不尋常（亂流高），但各產業卻各走各的（同步度很低），"
                     "代表衝擊集中在某些資產或產業，資金在輪動，還沒有變成全面的一起逃。")
    if aft.get("available") and aft["cur"] == len(aft["rows"]) - 1:
        parts.append("地震學角度：距離上次大震已經超過一年，餘震期結束；但大震本身從來沒有被提前預告過。")
    parts.append("沒有任何一個方法能說出哪一天會跌；它們能說的是現在的風險水位。")
    return "".join(parts)


@_anchor("ai-cross")
def sec_ai_cross(eng) -> str:
    rows = cross_rows(eng)
    if not rows:
        return ""
    ph = _ph(eng)
    vc = {"一致": "up", "分歧": "dn", "部分一致": "muted"}
    tr = "".join(f'<tr><td class="nw"><b>{T(r["dim"], r["dim"])}</b></td>'
                 f'<td>{T(r["h"][0], r["h"][0])}<br>{_pill(r["h"][1])} <span class="small muted">{T(r["h"][2], r["h"][2])}</span></td>'
                 f'<td>{T(r["a"][0], r["a"][0])}<br>{_pill(r["a"][1])} <span class="small muted">{T(r["a"][2], r["a"][2])}</span></td>'
                 f'<td class="{vc.get(r["v"] or "", "muted")}"><b>{T(r["v"] or "—", r["v"] or "—")}</b></td></tr>' for r in rows)
    n_ok = sum(r["v"] == "一致" for r in rows)
    n_split = sum(r["v"] == "分歧" for r in rows)
    head = f"{n_ok} 項一致、{n_split} 項分歧"
    txt = reading(rows, ph)
    body = (f'<p><b>{T(head, head)}</b></p><div class="scroll"><table class="mini"><thead><tr><th>{T("面向", "Question")}</th>'
            f'<th>{T("人類世界觀（本站既有指標）", "Human-built gauges")}</th><th>{T("AI／跨領域視角", "AI / cross-science lens")}</th>'
            f'<th>{T("兩邊一致嗎", "Agree?")}</th></tr></thead><tbody>{tr}</tbody></table></div>'
            f'<p class="rimp"><b>{T("合起來怎麼看", "Putting it together")}</b>：{T(txt, txt)}</p>')
    note = T("左欄是人類設計的指標：人挑選變數、設定門檻，或直接反映人的情緒。右欄不讀新聞、不用經濟理論，只讓價格數字自己說話，"
             "借用地震學（餘震）、生物學（鳥群同步）、流體力學（亂流）和機器記憶（相似日）的方法。"
             "兩邊一致時訊號比較可信；分歧時，代表人的感受和數據結構不一樣。每次網站更新都會重算，這是現況描述，不是預測，也不是投資建議。",
             "Left: human-built gauges. Right: price-only lenses from other sciences. Recomputed each build; not advice.")
    return card("完整比對表：人類指標 × AI 視角", "Full table: human gauges × AI lens", _fold(body + f'<p class="note">{note}</p>', "點開看完整比對表"), "wide")


def sec_ai_intro(eng) -> str:
    ph = _ph(eng)
    if not ph.get("available"):
        return ""
    ana, aft = ph.get("analog") or {}, ph.get("aftershock") or {}
    pts = [("波動有記憶，方向沒有",
            "大波動之後接著大波動，這是最穩定的規律（餘震表的頻率從 1–5 天的 "
            + (f"{num(aft['rows'][0]['oos'], 0)}% 一路降到一年以上的 {num(aft['rows'][-1]['oos'], 0)}%" if aft.get("available") else "高檔一路遞減")
            + "）；但哪一邊先動，所有方法都猜不準。"),
           ("結構指標是天氣預報，不是鬧鐘", "亂流與同步度升高時，之後大跌的頻率比平常高，但大多數亮燈之後並沒有大跌。它們適合拿來判斷「現在該把風險放多大」。"),
           ("機器記憶在這裡失敗了",
            f"只比對表面狀態的相似日搜尋，樣本外 AUC {num(ana.get('auc'), 2)}，不如亂猜：危機常從平靜的日子開始。"
            "這也說明為什麼本站不把任何單一模型當成答案。"),
           ("跳脫新聞的意義", "新聞與自媒體反映的是人的注意力；這一頁只看價格之間的結構。兩者分歧時，先相信可以回測的那一邊，再看它的假警報率。")]
    lis = "".join(f'<li><b>{T(a, a)}</b>：{T(b, b)}</li>' for a, b in pts)
    return card("從回測學到的 4 件事", "What the machine lens learned from its own back-tests",
                _fold(f'<ul class="brief">{lis}</ul>', "點開看"), "wide")


JS = r"""
document.addEventListener('click',function(ev){var a=ev.target.closest('[data-jump]');if(!a)return;ev.preventDefault();
 var t=document.getElementById(a.getAttribute('data-jump'));if(!t)return;var d=t.querySelector('details');if(d)d.open=true;
 t.scrollIntoView({behavior:'smooth',block:'start'});t.classList.add('aiflash');setTimeout(function(){t.classList.remove('aiflash');},1600);});
"""

CSS = (".aigrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:10px 0}"
       ".aitile{display:flex;flex-direction:column;gap:4px;padding:12px;border:1px solid var(--bd);border-radius:10px;"
       "background:var(--wash);color:inherit;text-decoration:none;min-width:0}"
       ".aitile:hover{border-color:var(--ac)}.aitile .tl{font-size:13px;font-weight:700}"
       ".aitile .tv{font-size:24px;font-weight:800;line-height:1.15}.aitile .tv small{font-size:13px;font-weight:600;opacity:.75}"
       ".aitile .tt{font-size:12.5px;opacity:.85}.aitile .go{margin-top:auto;font-size:12px;color:var(--ac)}"
       ".aicols{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin:12px 0}"
       ".aicol{padding:10px 12px;border:1px solid var(--bd);border-radius:10px;background:var(--wash);min-width:0}"
       ".aicol h3{margin:0 0 6px;font-size:14px}.aicol ul{margin:0;padding-left:18px}.aicol li{margin:6px 0;font-size:13px;line-height:1.55}"
       ".aih{font-size:14px;margin:14px 0 0}"
       ".fg{display:grid;gap:6px;margin:10px 0 4px;max-width:560px}.fgrow{display:grid;grid-template-columns:130px 1fr 36px;gap:8px;align-items:center}"
       ".fgl{font-size:13px}.fgv{text-align:right}.fgbar{height:12px;border-radius:6px;background:var(--wash);border:1px solid var(--bd);overflow:hidden}"
       ".fgbar i{display:block;height:100%;background:currentColor}.fgbar i.ac{color:var(--ac)}"
       ".aiwatch{padding:10px 12px;border-left:3px solid var(--ac);background:var(--wash);border-radius:4px}"
       ".aiwatch ol{margin:6px 0 0;padding-left:20px}.aiwatch li{margin:3px 0}"
       "[id^=ai-]{scroll-margin-top:72px}.aiback{margin:8px 0 0;text-align:right;font-size:12.5px}.aiback a{color:var(--ac)}"
       ".aiflash{outline:2px solid var(--ac);outline-offset:2px;transition:outline .3s}"
       ".aibar{display:flex;gap:3px;margin:8px 0 4px;font-size:12px;font-weight:700}"
       ".aibar span{padding:5px 6px;border-radius:4px;background:var(--wash);border-bottom:3px solid currentColor;"
       "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}.aitile .aibar span{padding:3px 0;margin:0}")
