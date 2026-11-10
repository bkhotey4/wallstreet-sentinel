"""能源傳導鏈 card — oil → diesel → inflation expectations → 2-year yield, with plain-language readings from fixed rules."""
from __future__ import annotations

from typing import Dict, List

from tools.sitekit import T, card, cls, esc, num

OIL_SYMS = ("BZ=F", "CL=F", "XLE", "JETS", "6505.TW", "2610.TW")   # crude, energy stocks, airlines, 台塑化, 華航


def oil_sigma(eng) -> float:
    """Brent's usual daily move (% std of the last 60 daily returns), baked into the page for the live line."""
    try:
        s = eng.market.series("BZ=F").dropna()
        return round(float(s.pct_change().dropna().tail(60).std() * 100), 3) if len(s) > 61 else 0.0
    except Exception:  # noqa: BLE001
        return 0.0


def oil_live(eng) -> str:
    """Placeholder filled in the browser from /api/quote and /api/news (hidden if either fails, e.g. on GitHub Pages)."""
    return (f'<div class="oillive" id="oillive" data-sig="{oil_sigma(eng)}" hidden><p class="rimp"><b id="oil_one"></b></p>'
            '<ul class="small" id="oil_news"></ul><p class="small" id="oil_who"></p>'
            '<p class="small muted" id="oil_t"></p></div>')


OIL_CSS = ".oillive{border-left:3px solid var(--ac);padding:2px 10px;margin:4px 0 10px;background:var(--wash);border-radius:6px}"
OIL_JS = r"""
(function(){var box=document.getElementById('oillive');if(!box)return;var sig=parseFloat(box.dataset.sig)||0;
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function ago(ts){var m=Math.max(0,Math.round((Date.now()/1000-ts)/60));return m<60?m+' 分鐘前':m<1440?Math.round(m/60)+' 小時前':Math.round(m/1440)+' 天前';}
function pc(x){return (x>0?'+':'')+x.toFixed(1)+'%';}
function run(){Promise.all([fetch('/api/quote?s=__SYMS__').then(function(r){return r.json();}),fetch('/api/news').then(function(r){return r.json();})]).then(function(a){
  var q=a[0].q||a[0],n=a[1].items||[],b=q['BZ=F'];if(!b||b.chg==null)return;var c=+b.chg,k=sig?Math.abs(c)/sig:null;
  var size=k==null?'':(k>=2?'，是平常一天波動的 '+k.toFixed(1)+' 倍，算大動':k>=1?'，比平常一天的波動大一些（'+k.toFixed(1)+' 倍）':'，在平常的波動範圍內');
  document.getElementById('oil_one').textContent='油價今天怎麼了：布蘭特原油 '+(+b.price).toFixed(2)+' 美元，'+pc(c)+size+'。';
  var now=Date.now()/1000,hit=n.filter(function(x){return now-x.ts<24*3600&&(x.tags.indexOf('油價')>=0||x.tags.indexOf('地緣')>=0);}).slice(0,4);
  var ul=document.getElementById('oil_news');ul.innerHTML=hit.length?hit.map(function(x){return '<li>'+esc(ago(x.ts))+'・'+esc(x.s)+'：<a href="'+esc(x.u)+'" target="_blank" rel="noopener noreferrer">'+esc(x.t)+'</a></li>';}).join('')
   :'<li>過去 24 小時，本站的新聞來源沒有和油價或地緣政治有關的標題，原因還不清楚，不硬猜。</li>';
  var f=function(s){var x=q[s];return x&&x.chg!=null?pc(+x.chg):'—';};
  var who=c<=-1?'油價下跌時，通常航空（美國航空股 '+f('JETS')+'、華航 '+f('2610.TW')+'）、貨運和塑化下游的成本變低；石油公司與能源股（美國能源股 '+f('XLE')+'）收入受壓；通膨預期和利率常跟著往下，對成長股是減壓。'
   :c>=1?'油價上漲時，通常石油公司與能源股（美國能源股 '+f('XLE')+'、台塑化 '+f('6505.TW')+'）受惠；航空（'+f('JETS')+'、華航 '+f('2610.TW')+'）與貨運成本變高；通膨預期和利率容易跟著往上，對成長股是壓力。'
   :'油價今天變化不大，對航空、能源股和通膨預期的影響有限。';
  document.getElementById('oil_who').innerHTML='<b>會牽動誰</b>：'+esc(who);
  document.getElementById('oil_t').textContent='報價約延遲 15 分鐘（'+new Date((b.t||now)*1000).toLocaleString('zh-TW',{hour12:false})+'）；新聞是用時間和關鍵字對上的，對得上不等於就是原因。每 5 分鐘更新。';
  box.hidden=false;}).catch(function(){box.hidden=true;});}
run();setInterval(run,300000);})();
""".replace("__SYMS__", ",".join(s.replace("=", "%3D").replace("^", "%5E") for s in OIL_SYMS))


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


def tw_fuel_block(eng) -> str:
    """4. 台灣加油站：中油每週牌價，和國際油價（換成新台幣）一年的變化比。"""
    try:
        from wsb.data import tw_fuel as TF
        v = TF.view(eng.market.series("BZ=F"), eng.market.series("TWD=X"))
    except Exception:  # noqa: BLE001
        v = None
    if not v:
        return ""
    rows = "".join(f'<tr><td>{esc(r["zh"])}</td><td class="r"><b>{r["price"]:.1f}</b></td>'
                   f'<td class="r {cls(r["wk"])}">{num(r["wk"], 1, sign=True)}</td>'
                   f'<td class="r {cls(r["yoy"])}">{num(r["yoy"], 1, sign=True, pct=True)}</td><td class="small muted">{esc(r["date"])}</td></tr>' for r in v["rows"])
    g = next((r for r in v["rows"] if r["key"] == "95"), v["rows"][0])
    read = ""
    if v.get("brent_yoy") is not None and g.get("yoy") is not None:
        gap = v["brent_yoy"] - g["yoy"]
        read = (f'<p class="small">一年來國際油價（布蘭特換成新台幣）{v["brent_yoy"]:+.0f}%，台灣 95 汽油 {g["yoy"]:+.1f}%。'
                + (f'加油站漲得比國際油價少很多，差的部分由中油和政府的油價平穩機制吸收，所以台灣物價受油價的衝擊比國外小；但中油吸收的成本，最後可能要靠政府補貼，也就是納稅人負擔。'
                   if gap > 5 else f'加油站跌得比國際油價少，平穩機制在油價下跌時也會讓台灣降得比較慢。' if gap < -5 else '兩者差不多，國際油價大致照實反映到加油站。')
                + '</p>')
    return (f'<h3>{T("4. 台灣加油站：國際油價傳到台灣多少", "4. Taiwan pump prices")}</h3>'
            f'<div class="scroll"><table class="mini"><thead><tr><th></th><th class="r">元／公升</th><th class="r">本週調整</th><th class="r">一年</th><th>生效日</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>' + read
            + f'<p class="small muted">中油每週日公布、週一生效（<a href="{TF.PAGE}" target="_blank" rel="noopener">中油歷史牌價</a>）；本站自動抓取，不是預測下週油價。</p>')


def sec_energy_chain(eng) -> str:
    r = getattr(eng, "energy_chain", None) or {}
    if not r.get("available"):
        return ""
    from tools.site_quant import _takeaways
    from wsb.analytics import energy_chain as EC
    body = oil_live(eng) + _takeaways(readings(r, EC.cfg()))
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
    body += tw_fuel_block(eng)
    note = T("把「原油 → 柴油 → 通膨預期 → Fed 路徑」這條鏈放在一起看；柴油等精煉品比原油更直接推高物價，所以兩個都看。"
             "資料來自 Yahoo 期貨、FRED（EIA 柴油零售價、5 年通膨預期、2 年期殖利率）與 EIA 週庫存；🔑 重點是固定規則的解讀，不是預測，也不是投資建議。",
             "Oil → diesel → inflation expectations → the Fed path, from futures, FRED and EIA data. Readings are fixed rules, not forecasts or advice.")
    return card("能源傳導鏈：原油 → 柴油 → 通膨 → 利率", "Energy chain: oil → diesel → inflation → rates", body + f'<p class="note">{note}</p>', "wide")
