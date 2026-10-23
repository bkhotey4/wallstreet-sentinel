"""能源傳導鏈 card — oil → diesel → inflation expectations → 2-year yield, with plain-language readings from fixed rules."""
from __future__ import annotations

from typing import Dict, List

from tools.sitekit import T, card, cls, esc, num


def readings(r: Dict, c: Dict) -> List[Dict]:
    """🔑 what the numbers add up to (descriptive; percentile thresholds from settings.yaml energy_chain)."""
    out: List[Dict] = []
    hot, ext = float(c.get("hot_pct", 85)), float(c.get("extreme_pct", 95))
    cr = {x["key"]: x for x in r.get("cracks") or []}
    d = cr.get("diesel")
    if d and d.get("pct") is not None and d["pct"] >= hot:
        out.append({"lv": "alert" if d["pct"] >= ext else "watch",
                    "zh": f"柴油裂解價差 {d['now']:.1f} 美元／桶，在 {d['since']} 年以來第 {d['pct']:.0f} 百分位：缺的是柴油這類精煉品，不只是原油。"
                          "柴油是貨運、農業和工業的燃料，價格會比汽油更直接地推高物價。",
                    "en": f"Diesel crack ${d['now']:.1f}/bbl, {d['pct']:.0f}th percentile since {d['since']}: the shortage is in refined products."})
    if r.get("aligned"):
        ch = {x["key"]: x for x in r.get("chain") or []}
        be, y2 = ch.get("be5"), ch.get("y2")
        out.append({"lv": "alert",
                    "zh": "傳導鏈每一環過去 3 個月都在上升：油價、柴油、通膨預期"
                          + (f"（{be['d3m']:+.0f}bp）" if be else "") + "、2 年期殖利率" + (f"（{y2['d3m']:+.0f}bp）" if y2 else "")
                          + "。能源衝擊已經傳到利率市場，市場在定價更緊的 Fed。",
                    "en": "Every link rose over 3 months: crude, diesel, breakevens and the 2-year yield — the energy shock has reached rates."})
    p = r.get("pass") or {}
    if p.get("bp_per_10pct") is not None and p.get("corr") is not None and p["corr"] >= 0.3:
        out.append({"lv": "info",
                    "zh": f"近兩年柴油每漲 10%，5 年期通膨預期平均變動 {p['bp_per_10pct']:+.1f}bp（每 {p['step']} 個交易日的變化，{p['n']} 個樣本，相關係數 {p['corr']:.2f}）。",
                    "en": f"Past two years: {p['bp_per_10pct']:+.1f}bp of 5y breakeven per +10% diesel (corr {p['corr']:.2f}, n={p['n']})."})
    st = r.get("stocks") or {}
    if st.get("vs5_pct") is not None and st["vs5_pct"] <= float(c.get("stocks_low_pct", -8)):
        out.append({"lv": "watch",
                    "zh": f"美國餾分油（柴油）庫存比過去 {st['n_years']} 年同一週平均低 {abs(st['vs5_pct']):.1f}%：緩衝少，供給再出事時價格容易跳。",
                    "en": f"US distillate stocks {st['vs5_pct']:+.1f}% vs the {st['n_years']}-year average for this week."})
    order = {"alert": 0, "watch": 1, "info": 2}
    return sorted(out, key=lambda x: order[x["lv"]])


def sec_energy_chain(eng) -> str:
    r = getattr(eng, "energy_chain", None) or {}
    if not r.get("available"):
        return ""
    from tools.site_quant import _takeaways
    from wsb.analytics import energy_chain as EC
    body = _takeaways(readings(r, EC.cfg()))
    ch = r.get("chain") or []
    if ch:
        def d3(x):
            if x["d3m"] is None:
                return "—"
            return num(x["d3m"], 1, sign=True, pct=True) if x["unit"] == "%" else num(x["d3m"], 0, sign=True) + " bp"
        rows = "".join(f'<tr><td>{T(x["zh"], x["en"])}</td><td class="r"><b>{num(x["now"], 2)}{"%" if x["unit"] == "bp" else ""}</b></td>'
                       f'<td class="r {cls(x["d3m"])}">{d3(x)}</td><td class="small muted">{esc(x["asof"])}</td></tr>' for x in ch)
        body += (f'<h3>{T("1. 傳導鏈：每一環過去 3 個月的變化", "1. The chain: 3-month change of each link")}</h3><table class="mini"><thead><tr><th></th>'
                 f'<th class="r">{T("目前", "Now")}</th><th class="r">{T("3 個月變化", "3-month change")}</th><th>{T("資料日", "As of")}</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table>')
    cr = r.get("cracks") or []
    if cr:
        rows = "".join(f'<tr><td>{T(x["zh"], x["en"])}</td><td class="r"><b>{num(x["now"], 1)}</b></td>'
                       f'<td class="r">{num(x.get("pct"), 0)}</td><td class="r {cls(x.get("d3m"))}">{num(x.get("d3m"), 1, sign=True)}</td>'
                       f'<td class="small muted">{esc(x["since"])}–</td></tr>' for x in cr)
        body += (f'<h3>{T("2. 煉油價差：缺的是原油還是柴油", "2. Crack spreads: crude or refined products?")}</h3><table class="mini"><thead><tr><th></th>'
                 f'<th class="r">{T("美元／桶", "$/bbl")}</th><th class="r">{T("歷史百分位", "pctile")}</th><th class="r">{T("3 個月變化", "3m chg")}</th>'
                 f'<th>{T("資料起點", "Since")}</th></tr></thead><tbody>{rows}</tbody></table>'
                 f'<p class="small muted">{T("期貨每加侖報價 × 42 換成每桶，再減原油。價差越大＝煉油端越緊。", "Product futures ($/gal) × 42 minus crude.")}</p>')
    st = r.get("stocks") or {}
    p = r.get("pass") or {}
    kv = ""
    if st:
        kv += (f'<div><span class="muted">{T("餾分油庫存 vs 5 年同週平均", "Distillate stocks vs 5y same week")}</span>'
               f'<b class="{cls(st["vs5_pct"])}">{num(st["vs5_pct"], 1, sign=True, pct=True)}</b><span class="small muted">{esc(st["asof"])}</span></div>')
    if p.get("bp_per_10pct") is not None:
        kv += (f'<div><span class="muted">{T("柴油每 +10% → 5 年通膨預期", "5y breakeven per +10% diesel")}</span>'
               f'<b>{num(p["bp_per_10pct"], 1, sign=True)} bp</b><span class="small muted">{T("相關係數", "corr")} {num(p.get("corr"), 2)}</span></div>')
    if kv:
        body += f'<h3>{T("3. 庫存緩衝與傳導力道", "3. Buffer and pass-through")}</h3><div class="kv">{kv}</div>'
        if not st:
            body += f'<p class="small muted">{T("庫存需要 EIA 免費金鑰（EIA_API_KEY）才會顯示。", "Stocks need a free EIA_API_KEY.")}</p>'
    note = T("把「原油 → 柴油 → 通膨預期 → Fed 路徑」這條鏈放在一起看。這次油價衝擊最緊的是柴油等精煉品，只看原油會低估對物價的影響。"
             "資料來自 Yahoo 期貨、FRED（EIA 柴油零售價、5 年通膨預期、2 年期殖利率）與 EIA 週庫存；🔑 重點是固定規則的解讀，不是預測，也不是投資建議。",
             "Oil → diesel → inflation expectations → the Fed path, from futures, FRED and EIA data. Readings are fixed rules, not forecasts or advice.")
    return card("能源傳導鏈：原油 → 柴油 → 通膨 → 利率", "Energy chain: oil → diesel → inflation → rates", body + f'<p class="note">{note}</p>', "wide")
