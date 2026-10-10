"""全方位風險 tab: integrated outlook (9 dimensions + forecasts by horizon), news-intelligence fusion and the
sector exposure map.  Public data only — the exposure table is shown only in its sector/asset ('universe') mode."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from tools.sitekit import T, card, esc, line_chart, num

LV_COL = {"高": "#d03b3b", "偏高": "#ec835a", "中性": "#fab219", "低": "#0ca30c", "資料缺": "#6b7280"}
ST_COL = {"確認": "#d03b3b", "無聲壓力": "#ec835a", "敘事領先": "#fab219", "平靜": "#0ca30c"}
ST_EN = {"確認": "Confirmed", "無聲壓力": "Silent stress", "敘事領先": "Narrative only", "平靜": "Calm"}

CSS = """
.olh{display:flex;flex-wrap:wrap;gap:18px;align-items:center}.olbig{font-size:64px;font-weight:800;line-height:1;color:var(--lv)}
.oltop{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.olchip{border:1px solid var(--bd);border-left:4px solid var(--lv);border-radius:6px;padding:2px 8px;font-size:13px}
.olhz{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-top:14px}
.olhzc{background:var(--card2);border:1px solid var(--bd);border-radius:10px;padding:10px 12px}.olhzc .p{font-size:28px;font-weight:800}
.olbar{position:relative;height:8px;border-radius:4px;background:var(--bd);margin:6px 0}.olbar b{position:absolute;left:0;top:0;bottom:0;border-radius:4px;background:var(--lv)}
.olbar i{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--tx)}
.olg{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px}
.oldim{background:var(--card2);border:1px solid var(--bd);border-top:4px solid var(--lv);border-radius:10px;padding:10px 12px}
.oldim h3{margin:0;font-size:15px;display:flex;justify-content:space-between;gap:8px}.oldim .sc{font-size:26px;font-weight:800;color:var(--lv)}
.oldim ul{margin:6px 0 0;padding-left:18px}.oldim li{font-size:13px;margin:3px 0}
.olfc{margin-top:6px;font-size:13px;border-top:1px dashed var(--bd);padding-top:6px}
table.olt{width:100%;border-collapse:collapse}table.olt td,table.olt th{padding:6px 8px;border-bottom:1px solid var(--bd);text-align:left;font-size:13px;vertical-align:top}
.olst{font-weight:700;color:var(--lv)}
"""


def _lv(score: Optional[float], label: str) -> str:
    return LV_COL.get(label, "#6b7280")


def _ol(eng) -> Dict:
    return getattr(eng, "outlook", None) or {}


def _recession_history(eng) -> Optional[pd.Series]:
    from wsb.analytics.outlook import nyfed_probability
    sp = eng.fred.get("T10Y3M").dropna()
    if len(sp) < 300:
        return None
    m = sp.rolling(21, min_periods=15).mean().dropna()
    return m.iloc[-2520:].apply(nyfed_probability)                       # ~10 years of daily values


def sec_outlook_hero(eng) -> str:
    o = _ol(eng)
    if not o.get("available"):
        return ""
    col = LV_COL.get(o["label"], "#6b7280")
    dims = {d["key"]: d for d in o["dims"]}
    chips = "".join(f'<span class="olchip" style="--lv:{LV_COL.get(dims[k]["label"])}">{T(dims[k]["zh"], dims[k]["en"])} '
                    f'<b>{dims[k]["score"]:.0f}</b></span>' for k in o["top"])
    hz = []
    for h in o["horizons"]:
        p, base = h["prob"], h.get("base")
        hot = base is not None and p > base * 1.15 or base is None and p >= 40
        lv = "#d03b3b" if hot else ("#0ca30c" if base is not None and p < base * 0.85 else "#fab219")
        tick = f'<i style="left:{min(base, 100):.0f}%"></i>' if base is not None else ""
        sub = (T(f"平常 {base:.1f}%", f"usual {base:.1f}%") if base is not None else
               T(f"一個月前 {h['prev']:.0f}%", f"1m ago {h['prev']:.0f}%") if h.get("prev") is not None else "")
        hz.append(f'<div class="olhzc" style="--lv:{lv}"><div class="small muted">{T(h["zh"], h["en"])}</div>'
                  f'<div class="p" style="color:{lv}">{p:.1f}%</div><div class="olbar"><b style="width:{min(p, 100):.0f}%"></b>{tick}</div>'
                  f'<div class="small muted">{sub} · {T(h["model_zh"], h["model_en"])}</div></div>')
    rec = _recession_history(eng)
    chart = line_chart("c_recprob", rec, "衰退機率 %", 1, w=640, h=170, fixed=(0, 100),
                       bands=[(0, 30, "#0ca30c"), (30, 50, "#fab219"), (50, 100, "#d03b3b")]) if rec is not None else ""
    note = T("綜合分數是 9 個面向的透明加權平均（不是預測模型）。預測只來自有實證紀錄的模型：1–6 個月崩跌機率＝壓力指數落在目前區間時，"
             "標普之後下跌的歷史頻率；12 個月衰退機率＝紐約聯準會殖利率曲線模型（10 年減 3 個月利差）。下方曲線是該模型近 10 年的數值，"
             "超過 30% 的區域過去多次出現在衰退之前，但也有假警報（例如 2022–2024 長期倒掛）。",
             "The composite is a transparent weighted average of 9 dimensions, not a forecasting model. Forecasts come only from models "
             "with a track record: 1–6 month odds are historical frequencies at the current Stress-Index zone; the 12-month recession "
             "probability is the NY Fed yield-curve model (10y minus 3m). The chart shows that model over 10 years — readings above 30% "
             "preceded past recessions, with false alarms too (e.g. the 2022–24 inversion).")
    return f'''<section class="card wide"><h2>{T("全方位風險展望", "Integrated risk outlook")}</h2>
<p class="sub">{T("總經 × 金融海嘯 × 信用 × 銀行 × 估值 × 財報 × 產業 × 新聞，一頁看完", "Macro × crisis × credit × banks × valuation × earnings × sectors × news, on one page")}</p>
<div class="olh"><div class="olbig" style="--lv:{col}">{o["score"]:.0f}</div><div>
<div class="lvl"><i class="sw" style="background:{col}"></i>{T("綜合風險：" + o["label"], "Overall: " + o["label_en"])}</div>
<div class="small muted">{T(f"資料涵蓋 {o['coverage'] * 100:.0f}% 的面向", f"{o['coverage'] * 100:.0f}% of dimensions available")}</div>
<div class="oltop">{T("最大風險", "Top risks")}：{chips}</div></div></div>
<h3 style="margin-top:14px">{T("預測（依時間長度）", "Forecasts by horizon")}</h3><div class="olhz">{"".join(hz)}</div>
{f'<h3 style="margin-top:14px">{T("12 個月衰退機率（紐約聯準會模型）近 10 年", "12-month recession probability (NY Fed model), 10 years")}</h3>{chart}' if chart else ""}
<p class="note">{note}</p></section>'''


def sec_outlook_dims(eng) -> str:
    o = _ol(eng)
    if not o.get("available"):
        return ""
    cards = []
    for d in sorted(o["dims"], key=lambda d: -(d["score"] if d["score"] is not None else -1)):
        col = LV_COL.get(d["label"], "#6b7280")
        sc = "—" if d["score"] is None else f'{d["score"]:.0f}'
        ev = "".join(f"<li>{esc(e)}</li>" for e in d["evidence"][:5])
        fc = ""
        f = d.get("forecast") or {}
        if f.get("prob") is not None:
            fc = (f'<div class="olfc">{T("預測", "Forecast")}｜{T(f["horizon_zh"] + "內" + f["what_zh"], f["what_en"] + " within " + f["horizon_en"])}：'
                  f'<b>{f["prob"]:.1f}%</b>（{T(f["model_zh"], f["model_en"])}）</div>')
        elif f.get("crash"):
            fc = '<div class="olfc">' + "；".join(
                T(f'{c["days"]} 日跌≥{c["dd"]:.0f}%：{c["prob"]:.1f}%（平常 {c["base"]:.1f}%）',
                  f'≥{c["dd"]:.0f}% fall in {c["days"]}d: {c["prob"]:.1f}% (usual {c["base"]:.1f}%)') for c in f["crash"]) + "</div>"
        w = o["weights"].get(d["key"], 0)
        cards.append(f'<div class="oldim" style="--lv:{col}"><h3><span>{T(d["zh"], d["en"])}</span><span class="sc">{sc}</span></h3>'
                     f'<div class="small muted">{T(d["label"], d["label_en"])} · {T(f"權重 {w:.0%}", f"weight {w:.0%}")}'
                     f'{(" · " + esc(d["note"])) if d.get("note") else ""}</div><ul>{ev}</ul>{fc}</div>')
    note = T("每個面向 0–100，越高越危險；條列的是算出分數的原始證據。灰色＝資料暫缺，該面向不計入綜合分數。",
             "Each dimension is 0–100 (higher = riskier); bullets are the raw evidence behind the score. Grey = data missing, excluded.")
    return card("九大面向", "Nine dimensions", f'<div class="olg">{"".join(cards)}</div><p class="note">{note}</p>', "wide")


def sec_intel(eng) -> str:
    itl = getattr(eng, "intel", None) or {}
    v = itl.get("verdict") or {}
    if not v.get("available"):
        return ""
    rows = []
    for r in itl.get("channels", []):
        col = ST_COL.get(r["state"], "#6b7280")
        head = (f'<div class="small muted">{esc(r["top"][0]["source"])}：{esc(r["top"][0]["title"][:110])}</div>' if r.get("top") else "")
        rows.append(f'<tr><td><b>{T(r["channel"])}</b>{head}</td><td class="olst" style="--lv:{col}">{T(r["state"], ST_EN.get(r["state"]))}</td>'
                    f'<td>{num(r.get("ignition"), 0)}</td><td>{r["news_level"]:.0f}（{r["news_n"]}）</td><td><b>{r["fused"]:.0f}</b></td></tr>')
    cov = itl.get("ai_coverage")
    ai = (T(f"AI 已判讀 {cov * 100:.0f}% 的新聞標題（方向與嚴重度）", f"AI read {cov * 100:.0f}% of headlines (direction & severity)")
          if cov else T("新聞以關鍵字判斷", "Headlines scored by keywords"))
    note = T("確認＝新聞與價格同時示警（最可信）；敘事領先＝只有新聞、價格未跟；無聲壓力＝價格在施壓但新聞安靜（容易被低估）。"
             "市場點火＝衝擊雷達的價格分數；新聞熱度＝該路徑新聞量相對自身 30 日的百分位（括號為則數）。",
             "Confirmed = headlines and prices both flag it; Narrative only = headlines without price confirmation; "
             "Silent stress = prices under stress while headlines are quiet. Ignition = shock-radar price score; heat = news volume "
             "percentile vs its own 30 days (count in brackets).")
    return card("新聞情報 × 價格確認", "News intelligence × price confirmation",
                f'<p class="small muted">{esc(v.get("headline", ""))} · {ai}</p><table class="olt"><thead><tr><th>{T("傳導路徑", "Path")}</th>'
                f'<th>{T("狀態", "State")}</th><th>{T("市場點火", "Ignition")}</th><th>{T("新聞熱度", "News heat")}</th><th>{T("融合", "Fused")}</th>'
                f'</tr></thead><tbody>{"".join(rows)}</tbody></table><p class="note">{note}</p>', "wide")


def sec_exposure(eng) -> str:
    exp = getattr(eng, "exposure", None) or {}
    if not exp.get("available") or exp.get("mode") != "universe":     # holdings are never published
        return ""
    rows = []
    for r in exp["paths"][:6]:
        worst = [h for h in r["holdings"] if h["sens_pct_per10"] < 0][:3]
        best = [h for h in reversed(r["holdings"]) if h["sens_pct_per10"] > 0 and h["significant"]][:2]
        fmt = lambda h: f'{esc(h.get("name", h["sym"]))} {h["sens_pct_per10"]:+.1f}%' + ("" if h["significant"] else "*")  # noqa: E731
        col = ST_COL.get(r.get("state"), "#6b7280")
        rows.append(f'<tr><td><b>{T(r["path"])}</b></td><td class="olst" style="--lv:{col}">{T(r.get("state") or "—", ST_EN.get(r.get("state")))}</td>'
                    f'<td class="dn">{"、".join(fmt(h) for h in worst) or "—"}</td><td class="up">{"、".join(fmt(h) for h in best) or "—"}</td></tr>')
    note = T("每條衝擊路徑壓力上升 10 點時，各產業 ETF／資產過去 3 年的平均每週變動；* = 統計不顯著。這是歷史共同變動，不是因果或預測。",
             "Average weekly move of each sector ETF / asset when a shock path's stress rises 10 points (last 3 years); * = not "
             "statistically significant. Historical co-movement, not causation.")
    return card("產業曝險：每條衝擊最傷哪些產業", "Sector exposure to each shock path",
                f'<table class="olt"><thead><tr><th>{T("傳導路徑", "Path")}</th><th>{T("狀態", "State")}</th><th>{T("最受傷", "Hurt most")}</th>'
                f'<th>{T("相對抗跌", "Held up")}</th></tr></thead><tbody>{"".join(rows)}</tbody></table><p class="note">{note}</p>', "wide")


def sec_outlook_mini(eng) -> str:
    o = _ol(eng)
    if not o.get("available"):
        return ""
    col = LV_COL.get(o["label"], "#6b7280")
    dims = {d["key"]: d for d in o["dims"]}
    top = "".join(f'<li>{T(dims[k]["zh"], dims[k]["en"])} <b style="color:{LV_COL.get(dims[k]["label"])}">{dims[k]["score"]:.0f}</b></li>' for k in o["top"])
    rec = next((h for h in o["horizons"] if h["months"] == 12), None)
    recl = (f'<p class="small">{T("12 個月衰退機率", "12m recession probability")} <b>{rec["prob"]:.0f}%</b></p>' if rec else "")
    body = (f'<div class="olh"><div class="olbig" style="--lv:{col};font-size:48px">{o["score"]:.0f}</div>'
            f'<div><div class="lvl"><i class="sw" style="background:{col}"></i>{T(o["label"], o["label_en"])}</div>'
            f'<ul class="small" style="margin:4px 0 0;padding-left:18px">{top}</ul></div></div>{recl}'
            f'<p class="note"><a href="#outlook" data-p="outlook" class="ptablink">{T("看全方位風險 →", "Full risk outlook →")}</a></p>')
    return card("全方位風險", "Risk outlook", body, "span3")
