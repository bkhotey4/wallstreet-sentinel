"""信用 cards: 美國主要公司信用體檢 (產業 page) and 信用與利率：現在的關係 (美債 page)."""
from __future__ import annotations

from tools.sitekit import T, card, esc, num

_G = {"強": "up", "穩健": "up", "普通": "muted", "偏弱": "cr-warn", "危險": "dn"}
_SEC = {"XLK": "資訊科技", "XLC": "通訊服務", "XLY": "非必需消費", "XLP": "必需消費", "XLV": "醫療保健", "XLF": "金融",
        "XLI": "工業", "XLB": "原物料", "XLE": "能源", "XLU": "公用事業", "XLRE": "不動產"}


def _x(v, d=1, suf="") -> str:
    return "—" if v is None else f"{v:.{d}f}{suf}"


def sec_credit_health(eng) -> str:
    ch = (getattr(eng, "sector_brief", None) or {}).get("credit") or {}
    if not ch.get("available"):
        return ""
    c = ch["counts"]
    summ = "".join(f'<span class="pill"><b class="{_G[g]}">{g}</b> {c[g]}</span> ' for g in c)
    secrows = ""
    for etf, cnt in sorted(ch["by_sector"].items(), key=lambda kv: -(kv[1]["偏弱"] + kv[1]["危險"])):
        secrows += (f'<tr><td>{esc(_SEC.get(etf, etf))}</td>' + "".join(f'<td class="r {_G[g] if cnt[g] else "muted"}">{cnt[g]}</td>' for g in cnt) + "</tr>")
    rows = ""
    for r in ch["rows"]:
        g = r["grade"] or "—"
        sh = r.get("cov_shock")
        shock = (f'<b class="dn">{_x(sh)} 倍</b>' if r.get("cov") and sh is not None and r["cov"] >= 2 > sh else _x(sh, 1, " 倍"))
        due = r.get("due_cover")
        rows += (f'<tr data-sec="{esc(r["etf"])}"><td class="nw"><b>{esc(r["sym"])}</b><div class="small muted">{esc(r.get("name") or "")}</div></td>'
                 f'<td class="small">{esc(_SEC.get(r["etf"], r["etf"]))}</td><td><b class="{_G.get(g, "muted")}">{esc(g)}</b></td>'
                 f'<td class="small">{esc(r["why"] or "")}{("<div class=muted>" + esc(r["heavy"]) + "</div>") if r.get("heavy") else ""}</td>'
                 f'<td class="r">{_x(r.get("cov"), 1, " 倍")}</td><td class="r">{_x(r.get("lev"), 1, " 倍")}</td>'
                 f'<td class="r">{("無" if not r.get("due_1y") else _x(due, 1, " 倍"))}</td><td class="r">{shock}</td>'
                 f'<td class="r">{_x((r.get("merton") or 0) * 100 if r.get("merton") is not None else None, 2, "%")}</td>'
                 f'<td class="r">{_x((r.get("bk") or 0) * 100 if r.get("bk") is not None else None, 2, "%")}</td>'
                 f'<td class="small muted">{esc(r.get("end") or "")}</td></tr>')
    opts = "".join(f'<option value="{e}">{_SEC[e]}</option>' for e in _SEC)
    head = (f'<tr><th>{T("公司", "Company")}</th><th>{T("產業", "Sector")}</th><th>{T("信用等級（代理）", "Grade (proxy)")}</th><th>{T("理由", "Why")}</th>'
            f'<th class="r">{T("利息保障", "Interest cover")}</th><th class="r">{T("淨負債／EBITDA", "Net debt / EBITDA")}</th>'
            f'<th class="r">{T("現金 ÷ 一年內到期債", "Cash ÷ debt due 1y")}</th><th class="r">{T("借款成本 +2% 後利息保障", "Cover after +2pp")}</th>'
            f'<th class="r">{T("Merton 一年違約", "Merton 1y PD")}</th><th class="r">{T("破產模型 12 個月", "Bankruptcy model 12m")}</th><th>{T("財報期", "Period")}</th></tr>')
    shock_txt = (f"借款成本全面上升 2 個百分點時，利息保障會從 2 倍以上掉到 2 倍以下的有 {len(ch['shock_fall'])} 家："
                 f"{'、'.join(ch['shock_fall'][:12])}。" if ch["shock_fall"] else "借款成本上升 2 個百分點，沒有公司的利息保障因此掉到 2 倍以下。")
    note = T("每個產業權重最大的 15 家，財報取自 SEC（近 12 個月）。信用等級是依常見信評慣例的代理分級，不是信評機構的評等："
             "強＝淨現金，或利息保障 ≥ 8 倍且淨負債／EBITDA ≤ 2；穩健＝≥ 4 倍且 ≤ 3.5；普通＝≥ 2 倍且 ≤ 5；偏弱＝≥ 1 倍或 ≤ 6；其他、或 Merton 違約機率 ≥ 5% 為危險。"
             "金融業看權益／資產；公用事業、不動產本來就靠借錢經營，負債高是常態。近 12 個月有一次性費用（例如併購減損）時，利息保障會暫時失真。"
             "「借款成本 +2%」假設全部負債都按高 2 個百分點重新借，是壓力測試，不是預測。",
             "Proxy grades from common credit conventions, not agency ratings. SEC filings, trailing 12 months. Stress test, not a forecast.")
    n_txt = f"{ch['n']} 家主要公司："
    body = (f'<p>{T(n_txt, "Companies: ")}{summ}</p><p>{T(shock_txt, shock_txt)}</p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("產業", "Sector")}</th>' + "".join(f"<th class=r>{g}</th>" for g in c)
            + f'</tr></thead><tbody>{secrows}</tbody></table></div>'
            f'<p><label>{T("只看產業", "Sector")} <select class="chsel"><option value="">{T("全部", "All")}</option>{opts}</select></label></p>'
            f'<div class="scroll chbox"><table class="mini srt"><thead>{head}</thead><tbody>{rows}</tbody></table></div><p class="note">{note}</p>')
    return card("美國主要公司信用體檢：誰扛得住債", "Credit check of the largest US companies", body, "wide")


def sec_credit_rates(eng) -> str:
    from wsb.analytics import credit_rates as CR
    try:
        r = CR.build(eng)
    except Exception:  # noqa: BLE001
        return ""
    if not r.get("available"):
        return ""
    pts = []
    co = r["co"]
    if co.get("baa"):
        b = co["baa"]
        pts.append(f"信用利差和股市是「同時」動：{b['since']} 年以來每週 Baa 利差變化和標普報酬的相關係數 {b['same']:+.2f}"
                   + (f"，HYG÷IEF 是 {co['hyief']['same']:+.2f}" if co.get("hyief") else "")
                   + f"；看利差變化和 1–8 週後的股市，相關係數最多 {b['lead_abs']:.2f}。"
                   + ("利差擴大多半是股市下跌的同一件事，不是提前好幾週的預告。" if b["lead_abs"] < abs(b["same"]) / 2 else
                      "提前的關係不算弱，利差變化對之後幾週的股市有一些領先意義。"))
    if r.get("auc_level") is not None:
        lv_better = r["auc_level"] >= (r.get("auc_chg") or 0)
        pts.append(("比較有預警力的是「利差處在高水位」" if lv_better else "比較有預警力的是「利差在擴大」")
                   + f"：Baa 利差在近 3 年的百分位，對之後 3 個月標普跌 ≥10% 的辨識力 AUC {r['auc_level']:.2f}"
                   f"（0.5＝丟銅板），利差的 3 個月變化 {num(r.get('auc_chg'), 2)}。目前 Baa 利差在近 3 年第 {r['baa_pct']:.0f} 百分位。")
    d = r["div"]
    if d.get("p") is not None:
        verdict = "比平常還低，歷史上不是可靠的崩盤前兆" if d["p"] < d["base"] else "比平常高"
        pts.append(f"常被提到的「信用背離」（利差明顯擴大、但標普還在高點 3% 以內）：歷史上 {d['episodes']} 次，之後 3 個月跌 ≥10% 的比例 {d['p']:.0f}%，"
                   f"任何一週是 {d['base']:.0f}%，{verdict}。" + ("目前正處於這種狀態。" if d["now"] else "目前沒有出現。"))
    sy = r["stock_yield"]
    mood = ("利率上升時股市下跌（類似 2022 年的通膨／升息環境）" if sy["now"] < -0.1 else
            "利率上升時股市也上漲（景氣好、利率跟著上升的環境）" if sy["now"] > 0.1 else "股市和利率之間目前沒有明顯方向")
    pts.append(f"股市和利率的關係：標普報酬和 10 年期殖利率變化的 52 週相關係數 {sy['now']:+.2f}（{sy.get('since', '有資料')} 年以來中位數 {sy['median']:+.2f}），{mood}。"
               + (f"10 年期殖利率近 3 個月變化 {r['y10_chg13']:+.2f} 個百分點。" if r.get("y10_chg13") is not None else ""))
    t = r["tiers"]
    lab = {"ccc_bb": "CCC − BB（最弱 vs 次弱）", "hy": "高收益債", "ig": "投資級", "baa": "Baa 公司債"}
    tier_txt = "、".join(f"{lab[k]} 第 {v['pct']:.0f} 百分位" for k, v in t.items() if v.get("pct") is not None)
    pat = {"low": "壓力集中在最弱的公司（低評等先擴大、投資級還平靜）：信用循環早期常見的型態。",
           "broad": "高低評等一起擴大：壓力已經擴散到整個信用市場。",
           "calm": "各評等利差都在常態範圍。", "mixed": "各評等方向不一致。"}[r["pattern"]]
    if tier_txt:
        pts.append(f"壓力在哪一層（3 個月變化在近 3 年的百分位）：{tier_txt}。{pat}")
    lis = "".join(f"<li>{T(x, x)}</li>" for x in pts)
    note = T("每週資料、每次建置重算。ICE BofA 與 Moody's 利差是授權資料，只列方向與百分位，不顯示數值。AUC 是事後回測的辨識力，不是預測準確率。描述現況，不是投資建議。",
             "Weekly data, recomputed each build. Licensed spreads shown as directions and percentiles only. Not advice.")
    return card("信用與利率：現在的關係", "Credit and rates: how they relate now", f'<ul class="brief">{lis}</ul><p class="note">{note}</p>', "wide")


CSS = ".chbox{max-height:620px;overflow:auto}.cr-warn{color:var(--warn)}"
JS = r"""
document.querySelectorAll('.chsel').forEach(function(s){s.addEventListener('change',function(){var v=s.value,box=s.closest('.card');
 box.querySelectorAll('.chbox tbody tr').forEach(function(tr){tr.hidden=!!v&&tr.dataset.sec!==v;});});});
"""
