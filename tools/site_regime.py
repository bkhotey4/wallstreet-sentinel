"""依環境拆開驗證 (risk-model tab) and 滯脹年代對照 (past-crises tab) cards, with readings from fixed rules."""
from __future__ import annotations

from typing import Dict, List

from tools.sitekit import T, card, cls, esc, num

AUC_WEAK = 0.55          # same cut-off as the site's AUC verdicts (shock._verdict): below this ≈ random


def readings(r: Dict) -> List[Dict]:
    out: List[Dict] = []
    now = r.get("now") or {}
    for h in r.get("by_horizon") or []:
        for g in h.get("regimes") or []:
            if now.get(g["dim"]) != g["key"]:
                continue
            tag = f"{h['days']} 日跌 ≥ {h['drawdown_pct']:.0f}%"
            if g["auc"] is None:
                out.append({"lv": "watch", "zh": f"現在是「{g['zh']}」，模型在這種環境下的樣本外紀錄只有 {g['days']} 天、{g['events']} 次事件，"
                                                 f"不足以判斷準不準（{tag}）。崩跌機率請打折看。",
                            "en": f"Today's regime ({g['key']}) has too little out-of-sample history to judge the model ({tag})."})
            elif g["auc"] < AUC_WEAK:
                out.append({"lv": "alert", "zh": f"現在是「{g['zh']}」，模型在這種環境下的樣本外 AUC 只有 {g['auc']:.2f}（接近隨機，{tag}，{g['days']} 天）。"
                                                 "在這種環境，崩跌機率的參考價值很低。",
                            "en": f"In today's regime ({g['key']}) the out-of-sample AUC is {g['auc']:.2f} — near random ({tag})."})
            elif g.get("share") is not None and g["share"] < 20:
                out.append({"lv": "info", "zh": f"現在是「{g['zh']}」，這種環境只占模型樣本外測試的 {g['share']:.0f}%（AUC {g['auc']:.2f}，{tag}）。",
                            "en": f"Today's regime is {g['share']:.0f}% of the out-of-sample test (AUC {g['auc']:.2f}, {tag})."})
    seen, uniq = set(), []
    for x in out:                                                   # one line per message, strongest first
        if x["zh"] not in seen:
            seen.add(x["zh"])
            uniq.append(x)
    order = {"alert": 0, "watch": 1, "info": 2}
    return sorted(uniq, key=lambda x: order[x["lv"]])


def sec_regime_split(eng) -> str:
    r = getattr(eng, "regime_split", None) or {}
    if not r.get("available") or not any(h.get("regimes") for h in r.get("by_horizon") or []):
        return ""
    from tools.site_quant import _takeaways
    from wsb.analytics.regime_split import FED_ZH, SB_ZH
    now = r.get("now") or {}
    body = _takeaways(readings(r))
    body += (f'<div class="kv"><div><span class="muted">{T("Fed 方向", "Fed direction")}</span><b>{esc(FED_ZH.get(now.get("fed"), "—"))}</b></div>'
             f'<div><span class="muted">{T("股債關係", "Stocks vs bonds")}</span><b>{esc(SB_ZH.get(now.get("sb"), "—"))}</b></div></div>')
    for h in r["by_horizon"]:
        if not h.get("regimes"):
            continue
        rows = "".join(f'<tr{" class=hl" if now.get(g["dim"]) == g["key"] else ""}><td>{esc(g["zh"])}{" ◀ " + T("現在", "now") if now.get(g["dim"]) == g["key"] else ""}</td>'
                       f'<td class="r">{num(g["auc"], 2)}</td><td class="r">{g["days"]:,}</td><td class="r">{g["events"]:,}</td>'
                       f'<td class="r">{num(g.get("share"), 0)}%</td></tr>' for g in h["regimes"])
        dd = format(h["drawdown_pct"], ".0f")
        body += f'<h3>{T(str(h["days"]) + " 日內跌 ≥ " + dd + "%", str(h["days"]) + "d fall ≥" + dd + "%")}</h3>'
        body += (f'<table class="mini"><thead><tr><th>{T("環境", "Regime")}</th><th class="r">{T("樣本外 AUC", "OOS AUC")}</th>'
                 f'<th class="r">{T("天數", "Days")}</th><th class="r">{T("事件天數", "Event days")}</th><th class="r">{T("占比", "Share")}</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table>')
    note = T("同一個崩跌機率模型（走步外樣本：每年只用之前的資料訓練），把測試期間按「Fed 升息／降息／按兵不動」與「股債同向／反向」拆開，各自算 AUC。"
             "Fed 方向看聯邦基金利率 6 個月變化（±0.25 個百分點），股債關係看標普與公債報酬的 60 日相關性。事件太少的環境不算 AUC。"
             "AUC 0.5＝隨機；這是模型可信度的檢查，不是預測。",
             "The walk-forward crash-odds record split by Fed direction and stock–bond sign. AUC 0.5 = random. A credibility check, not a forecast.")
    return card("依環境拆開看模型準不準", "Model accuracy by regime", body + f'<p class="note">{note}</p>', "wide")


def sec_analogs(eng) -> str:
    r = (getattr(eng, "regime_split", None) or {}).get("analogs") or {}
    eps = r.get("episodes") or []
    if not eps:
        return ""

    def cell(v, kind):
        if v is None:
            return '<td class="r muted">—</td>'
        txt = f"{v:+.0f}bp" if kind == "bp" else f"{v:+.1f}%" if kind == "pct" else f"{v:+.2f}" if kind == "pp" else f"{v:.1f}%"
        return f'<td class="r {cls(v) if kind != "lvl" else ""}">{txt}</td>'

    rows = "".join(f'<tr><td class="nw">{esc(e["name"])}</td><td class="small muted nw">{esc(e["start"])} → {esc(e["end"])}</td>'
                   + cell(e.get("spx_pct"), "pct") + cell(e.get("spx_maxdd"), "pct") + cell(e.get("y10_bp"), "bp") + cell(e.get("ff_pp"), "pp")
                   + cell(e.get("oil_pct"), "pct") + cell(e.get("cpi_peak"), "lvl") + cell(e.get("unrate_pp"), "pp")
                   + f'<td class="r"><b>{num(e.get("similarity"), 0)}</b></td></tr>' for e in eps)
    now = r.get("now") or {}
    best = max((e for e in eps if e.get("similarity") is not None), key=lambda e: e["similarity"], default=None)
    lead = ""
    if best is not None:
        zh = ("目前的總經組合（CPI 年增 " + num(now.get("cpi"), 1) + "%、油價年增 " + num(now.get("oil"), 0) + "%、聯邦基金利率 6 個月 "
              + num(now.get("ff6"), 2, sign=True) + "、10 年期 " + num(now.get("y10"), 2) + "%、失業率 12 個月 " + num(now.get("un12"), 1, sign=True)
              + "）最接近「" + best["name"] + "」開始時的狀態。相似不代表會照著走，只是提供對照。")
        lead = "<p>" + T(zh, "Today's macro mix is closest to the start of " + best["name"] + ". Similar is not a forecast.") + "</p>"
    body = (lead + f'<div class="scroll"><table><thead><tr><th>{T("期間", "Episode")}</th><th>{T("日期", "Dates")}</th>'
            f'<th class="r">{T("標普", "S&P")}</th><th class="r">{T("期間最大回撤", "Max drawdown")}</th><th class="r">{T("10 年期", "10-year")}</th>'
            f'<th class="r">{T("聯邦基金利率", "Fed funds")}</th><th class="r">{T("油價", "Oil")}</th><th class="r">{T("CPI 年增高點", "CPI peak y/y")}</th>'
            f'<th class="r">{T("失業率", "Unemployment")}</th><th class="r">{T("和現在的相似度", "Similarity now")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')
    note = T("標普用 1927 年起的日線；10 年期、聯邦基金利率、油價（WTI 月均價）、CPI、失業率來自 FRED。利率與失業率是期間內的變化（百分點），油價是漲跌幅。"
             "相似度：把 CPI 年增、油價年增、聯邦基金利率 6 個月變化、10 年期水準、失業率 12 個月變化各自除以歷史標準差後算距離，換成 0–100（100＝完全一樣）。"
             "期間可在 settings.yaml 的 regime_split.analogs 增減。不是預測，也不是投資建議。",
             "S&P since 1927; FRED macro series. Similarity = distance in historical standard deviations → 0–100. Not a forecast.")
    return card("滯脹與升息年代對照", "Stagflation and tightening analogs", body + f'<p class="note">{note}</p>', "wide")
