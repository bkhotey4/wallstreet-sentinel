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


@_anchor("ai-top")
def sec_ai_brief(eng) -> str:
    """一眼看懂: one sentence, four lights, three things to watch; the comparison table and lessons folded."""
    ph = _ph(eng)
    if not ph.get("available"):
        return ""
    rows = cross_rows(eng)
    hs = [r["h"] for r in rows]
    ll = lens_lines(ph)
    head = headline(ph, hs)
    lights = "".join(f'<li>{e} {T(t, t)}</li>' for e, t in (ll[k] for k in ("turb", "flock", "quake", "analog") if k in ll))
    ssi = getattr(getattr(eng, "stress", None), "score", None)
    w = "".join(f"<li>{T(x, x)}</li>" for x in watch(ph, ssi))
    n_ok = sum(r["v"] == "一致" for r in rows)
    n_split = sum(r["v"] == "分歧" for r in rows)
    cmp_ = "".join(f'<li><b>{T(r["dim"], r["dim"])}</b>：{T("人類", "Human")} {_pill(r["h"][1])} ／ AI {_pill(r["a"][1])} → '
                   f'{T(r["v"] or "—", r["v"] or "—")}</li>' for r in rows)
    cnt = f"AI 視角交叉比對：{n_ok} 項一致、{n_split} 項分歧"
    v = score_view(ph.get("score") or {})
    sc = ph.get("score") or {}
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
    tiles.append(("ai-cross", "🤝 人類指標 vs AI", f"{n_ok}<small> 一致</small>・{n_split}<small> 分歧</small>", cnt, ""))
    grid = "".join(f'<a class="aitile" href="#ai" data-jump="{k}"><span class="tl">{T(lab, lab)}</span><span class="tv">{big}</span>'
                   f'<span class="tt">{T(txt, txt)}</span>{extra}<span class="go">{T("看細節 ›", "Details ›")}</span></a>'
                   for k, lab, big, txt, extra in tiles)
    body = (f'<p class="rimp big2"><b>{T(head, head)}</b>' + (f'<br>{T(sline, sline)}' if sline else "") + '</p>'
            f'<div class="aigrid">{grid}</div>'
            f'<div class="aiwatch"><b>{T("接下來要盯的 3 件事", "Three things to watch")}</b><ol>{w}</ol></div>'
            f'<p class="note">{T("點任一區塊會跳到下面的細節。只看價格數字、不讀新聞；描述現在的風險水位，不預告哪一天會跌，也不是投資建議。", "Tap a block for details. Price-only; not a timing tool, not advice.")}</p>')
    return card("一眼看懂：AI 怎麼看現在的風險", "At a glance: the machine view of risk now", body, "wide")



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
       ".aiwatch{padding:10px 12px;border-left:3px solid var(--ac);background:var(--wash);border-radius:4px}"
       ".aiwatch ol{margin:6px 0 0;padding-left:20px}.aiwatch li{margin:3px 0}"
       "[id^=ai-]{scroll-margin-top:72px}.aiback{margin:8px 0 0;text-align:right;font-size:12.5px}.aiback a{color:var(--ac)}"
       ".aiflash{outline:2px solid var(--ac);outline-offset:2px;transition:outline .3s}"
       ".aibar{display:flex;gap:3px;margin:8px 0 4px;font-size:12px;font-weight:700}"
       ".aibar span{padding:5px 6px;border-radius:4px;background:var(--wash);border-bottom:3px solid currentColor;"
       "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}.aitile .aibar span{padding:3px 0;margin:0}")
