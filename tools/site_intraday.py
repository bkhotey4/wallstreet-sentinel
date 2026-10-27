"""開盤後即時盤勢 (on the 開盤前 30 秒 page): during the US session the browser pulls /api/quote every minute and reads the
tape in plain words — where the S&P sits inside the range VIX priced for today, which side of the gamma flip it is on,
which sectors lead or lag (defensive vs. cyclical), volume vs. the same time on earlier days, chips vs. the index, and the
move since the open.  Every sentence is a rule on those numbers; it describes, it does not forecast.  Only on the
Cloudflare site (the GitHub copy has no /api/quote and shows a pointer instead)."""
from __future__ import annotations

import html
import json

from tools.sitekit import T, card

CF_URL = "https://wallstreet-sentinel.pages.dev"
SECTORS = [("XLK", "科技", "Tech", "cyc"), ("XLC", "通訊服務", "Comm services", "cyc"), ("XLY", "非必需消費", "Discretionary", "cyc"),
           ("XLF", "金融", "Financials", "cyc"), ("XLI", "工業", "Industrials", "cyc"), ("XLB", "原物料", "Materials", "cyc"),
           ("XLE", "能源", "Energy", "cyc"), ("XLV", "醫療保健", "Health care", "def"), ("XLP", "必需消費", "Staples", "def"),
           ("XLU", "公用事業", "Utilities", "def"), ("XLRE", "不動產", "Real estate", "def")]
CORE = ["^GSPC", "^VIX", "^SOX", "SPY", "QQQ"]
CROSS = ["^TNX", "DX-Y.NYB", "CL=F"]                 # 10-year yield, dollar index, crude oil: the usual "why" behind a move
MEGA = [("NVDA", "輝達"), ("MSFT", "微軟"), ("AAPL", "蘋果"), ("AMZN", "亞馬遜"), ("GOOGL", "Alphabet"), ("META", "Meta")]


def why_ctx(eng) -> dict:
    """Build-time clues for "why did it move": US data released today / yesterday (beat or miss vs consensus) and the
    newest market headlines of the last 18 hours.  The live page adds same-minute moves in mega caps, rates, dollar, oil."""
    import time
    out = {"ev": [], "news": []}
    try:
        from datetime import timedelta
        from wsb.analytics.macro_events import dir_label
        from wsb.data.econcal import us_today
        t = us_today()
        lo = (t - timedelta(days=1)).isoformat()
        for e in (getattr(eng, "econ_view", None) or {}).get("events") or []:
            if e.get("released") and e.get("dir") and e.get("imp", 0) >= 2 and lo <= e["date"] <= t.isoformat():
                out["ev"].append({"zh": e["zh"], "lab": dir_label(e["key"], e["dir"])[0], "date": e["date"]})
    except Exception:  # noqa: BLE001
        pass
    nd = getattr(eng, "news_digest", None) or {}
    zh = nd.get("zh") or {}
    now = time.time()
    items = [i for i in nd.get("items") or [] if i.get("ts") and now - i["ts"] <= 18 * 3600]
    items.sort(key=lambda i: (-(len(i.get("syms") or []) > 0), -i["ts"]))
    from tools.sitekit import guard_safe
    out["news"] = [{"t": guard_safe(zh.get(i["title"]) or i["title"])[:90], "l": i.get("link") or ""} for i in items[:3]]
    return out


def levels(eng) -> dict:
    """Gamma flip / call wall / put wall from the hourly CBOE options snapshot (empty when unavailable)."""
    op = getattr(getattr(eng, "options", None), "spx", None) or {}
    out = {k: float(op[k]) for k in ("zero_gamma", "call_wall", "put_wall") if op.get(k)}
    try:                                   # measured, not assumed: share of the last year's days outside the 1σ VIX range
        import math
        from wsb.analytics.premarket import band_record
        m = eng.market
        rec = band_record(m.series("^GSPC").dropna(), m.series("^VIX").dropna() / math.sqrt(252))
        if rec.get("y1"):
            out["out1"] = round(100 - rec["y1"]["in1"], 1)
    except Exception:  # noqa: BLE001
        pass
    return out


def sec_intraday(eng) -> str:
    lv = html.escape(json.dumps(levels(eng)), quote=True)
    wy = html.escape(json.dumps(why_ctx(eng), ensure_ascii=False), quote=True)
    note = ("盤中每分鐘自動更新（台北時間約 21:30／22:30 開盤，依美國夏令／冬令時間）。預期範圍＝VIX ÷ √252，代表選擇權市場替「今天」定價的一個標準差，"
            "歷史上約三分之二的日子收在範圍內；Gamma 翻轉點、Call 牆、Put 牆來自每小時更新的 CBOE 選擇權資料。類股用 11 個 SPDR 類股 ETF，"
            "防禦型＝醫療、必需消費、公用事業、不動產。量能＝今天到目前為止的成交量 ÷ 前 4 個交易日同一時段的平均。"
            "這裡只描述盤中現況，不預測收盤，也不是投資建議。報價：Yahoo Finance，約有數分鐘延遲。")
    body = (f'<div id="idbox" data-lv="{lv}" data-why="{wy}"><p class="small muted" id="idst">🕒 {T("等待即時報價…", "Waiting for live quotes…")}</p><p class="rimp big2"><b id="idone">{T("一句話看懂：美股開盤後，這裡每分鐘自動整理盤勢。", "Live read of the US session appears here.")}</b></p>'
            f'<div id="idwhyb" hidden><p><b>{T("🤔 為什麼？同時間發生的事", "Why? What moved at the same time")}</b></p><ul id="idwhy"></ul>'
            f'<p class="small muted">{T("這些是同一時間的變化與新聞，幫助理解盤勢，不是確定的因果。", "Same-time moves and news, not proven causes.")}</p></div>'
            '<ul id="idlist"></ul><div class="scroll"><table class="mini" id="idsec" hidden></table></div></div>'
            f'<p class="lqoff" id="idoff">{T("即時盤勢只在 Cloudflare 版網址可用：", "Live only on the Cloudflare site: ")}'
            f'<a href="{CF_URL}/#premarket" target="_blank" rel="noopener">{CF_URL.replace("https://", "")}</a></p>'
            f'<details class="sgx"><summary>{T("怎麼判讀", "How to read")}</summary><p class="note">{T(note, "Live session read: S&P vs the VIX-priced range, gamma flip, sector leadership, volume vs usual, chips vs index, move since the open. Describes, does not forecast.")}</p></details>')
    return card("開盤後即時盤勢：美股現在怎麼走", "US session, live", body, "wide")


_JS = r"""
(function(){var box=document.getElementById('idbox');if(!box)return;var SEC=__SEC__,CORE=__CORE__,CROSS=__CROSS__,MEGA=__MEGA__,LV={},WHY={};
 try{WHY=JSON.parse(box.getAttribute('data-why')||'{}');}catch(e){}
 try{LV=JSON.parse(box.getAttribute('data-lv')||'{}');}catch(e){}
 function en(){return document.documentElement.lang==='en';}
 function f(x,d){return x==null||isNaN(x)?'—':Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
 function sg(x,d){return x==null||isNaN(x)?'—':(x>0?'+':'')+f(x,d);}
 function et(){var p=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',weekday:'short',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date()),o={};
   p.forEach(function(x){o[x.type]=x.value;});return {wd:o.weekday,m:(+o.hour%24)*60+(+o.minute)};}
 function session(){var t=et();if(t.wd==='Sat'||t.wd==='Sun')return 'closed';if(t.m>=570&&t.m<960)return 'open';return t.m<570?'pre':'post';}
 var dead=false;
 function read(q){var L=[],one='',spx=q['^GSPC'],vix=q['^VIX'],sox=q['^SOX'],spy=q['SPY'],qq=q['QQQ'];if(!spx||spx.chg==null)return null;
   var v0=vix&&(vix.prev||vix.price),c=spx.chg,s=v0?v0/Math.sqrt(252):null,used=s?Math.abs(c)/s*100:null;
   if(s){L.push(en()?'S&P '+sg(c,2)+'%: '+f(used,0)+'% of today’s priced move (±'+f(s,2)+'%).'
     :'標普 '+sg(c,2)+'%，用掉今天預期波動（±'+f(s,2)+'%）的 '+f(used,0)+'%：'+(used<50?'走勢平穩。':used<100?'波動偏大，但還在預期範圍內。':'已經超出選擇權預期的範圍'+(LV.out1!=null?'（過去一年約 '+f(LV.out1,0)+'% 的日子會這樣）。':'。')));}
   if(LV.zero_gamma&&spx.price){var above=spx.price>=LV.zero_gamma;L.push(en()?'S&P '+(above?'above':'below')+' the gamma flip '+f(LV.zero_gamma,0)+'.'
     :'標普 '+f(spx.price,0)+' 在 Gamma 翻轉點 '+f(LV.zero_gamma,0)+(above?' 之上：造市商避險傾向「低買高賣」，波動通常較小。':' 之下：造市商避險傾向「追漲殺跌」，漲跌容易被放大。')
     +(LV.put_wall&&spx.price<=LV.put_wall*1.003?(en()?'':'已接近 Put 牆 '+f(LV.put_wall,0)+'（選擇權最大支撐區）。'):LV.call_wall&&spx.price>=LV.call_wall*0.997?(en()?'':'已接近 Call 牆 '+f(LV.call_wall,0)+'（選擇權最大壓力區）。'):''));}
   var sec=SEC.map(function(x){var y=q[x[0]];return y&&y.chg!=null?{s:x[0],zh:x[1],en:x[2],k:x[3],c:y.chg}:null;}).filter(Boolean).sort(function(a,b){return b.c-a.c;});
   if(sec.length>=8){var top=sec.slice(0,2),bot=sec.slice(-2),avg=function(k){var a=sec.filter(function(x){return x.k===k;});return a.reduce(function(t,x){return t+x.c;},0)/(a.length||1);},
     d=avg('def')-avg('cyc'),up=sec.filter(function(x){return x.c>0;}).length;
     L.push(en()?'Leaders: '+top.map(function(x){return x.en+' '+sg(x.c,1)+'%';}).join(', ')+'; laggards: '+bot.map(function(x){return x.en+' '+sg(x.c,1)+'%';}).join(', ')+'.'
       :'領漲：'+top.map(function(x){return x.zh+' '+sg(x.c,1)+'%';}).join('、')+'；領跌：'+bot.map(function(x){return x.zh+' '+sg(x.c,1)+'%';}).join('、')+'；11 個類股 '+up+' 個上漲。'
       +(d>=0.5?'防禦型類股（醫療、必需消費、公用事業）比景氣循環股強 '+f(d,1)+' 個百分點：資金偏保守。':d<=-0.5?'景氣循環股比防禦型強 '+f(-d,1)+' 個百分點：資金願意冒險。':''));
     var t=document.getElementById('idsec');t.hidden=false;t.innerHTML='<thead><tr><th>'+(en()?'Sector':'類股')+'</th><th class="r">'+(en()?'Today':'今日')+'</th><th>'+(en()?'Type':'類型')+'</th></tr></thead><tbody>'
       +sec.map(function(x){return '<tr><td>'+(en()?x.en:x.zh)+' <span class="muted small">'+x.s+'</span></td><td class="r '+(x.c>0?'up':x.c<0?'dn':'')+'">'+sg(x.c,2)+'%</td><td class="small muted">'+(x.k==='def'?(en()?'defensive':'防禦'):(en()?'cyclical':'景氣循環'))+'</td></tr>';}).join('')+'</tbody>';}
   var vx=[spy,qq].filter(function(x){return x&&x.volx!=null;});
   if(vx.length){var v=Math.max.apply(null,vx.map(function(x){return x.volx;}));L.push(en()?'Volume '+f(v,1)+'x the usual for this time.'
     :'成交量是前幾天同一時段的 '+f(v,1)+' 倍：'+(v>=1.5?(c<0?'量大下跌，賣壓是真的。':'量大上漲，買盤積極。'):v<=0.7?(c<0?'量縮下跌，比較像觀望而不是恐慌。':'量縮上漲，追價意願不強。'):'量能正常。'));}
   if(sox&&sox.chg!=null){var r=sox.chg-c;if(Math.abs(r)>=0.7)L.push(en()?'Chips '+(r>0?'outperform':'underperform')+' the S&P by '+f(Math.abs(r),1)+' pts.'
     :'費城半導體 '+sg(sox.chg,2)+'%，比大盤'+(r>0?'強':'弱')+' '+f(Math.abs(r),1)+' 個百分點：'+(r>0?'AI／科技在帶動盤勢。':'AI／科技是今天的壓力來源，台股與韓股容易受影響。'));}
   if(spx.open&&spx.prev){var g=(spx.open/spx.prev-1)*100,so=(spx.price/spx.open-1)*100;
     if(Math.abs(g)>=0.3&&Math.abs(so)>=0.3)L.push(en()?'Since the open '+sg(so,2)+'% (gap '+sg(g,2)+'%).'
       :'開盤'+(g>0?'跳空上漲 ':'跳空下跌 ')+sg(g,2)+'%，開盤後'+(so>0?'再漲 ':'回落 ')+sg(so,2)+'%：'+(g>0&&so<0?'開高走低，早盤的樂觀被賣掉。':g<0&&so>0?'開低走高，有買盤承接。':g>0?'開高走高，買盤延續。':'開低走低，賣壓延續。'));}
   one=(c<=-s*1&&s?'美股明顯走弱':c>=s&&s?'美股明顯走強':Math.abs(c)<0.3?'美股平盤整理':c<0?'美股小跌':'美股小漲')+'（標普 '+sg(c,2)+'%'+(vix&&vix.chg!=null?'，VIX '+sg(vix.chg,1)+'%':'')+'）';
   return {one:en()?'S&P '+sg(c,2)+'%':'一句話看懂（盤中）：'+one+'。',L:L,W:why(q,c,sec)};}
 // "why": mega caps moving with / against the index, rates, dollar, oil, VIX, then today's data releases and headlines
 function why(q,c,sec){var W=[],up=c>=0,big=Math.abs(c)>=0.3;
   if(!big)W.push(en()?'The move is small: ordinary day-to-day noise, no single driver.':'漲跌幅很小，屬於平常的波動，沒有單一主因；下面是今天比較明顯的變化。');
   var mg=MEGA.map(function(m){var y=q[m[0]];return y&&y.chg!=null?{s:m[0],n:m[1],c:y.chg}:null;}).filter(Boolean);
   var w=mg.filter(function(x){return (x.c>0)===up&&Math.abs(x.c)>=1;}).sort(function(a,b){return Math.abs(b.c)-Math.abs(a.c);}),
       a=mg.filter(function(x){return (x.c>0)!==up&&Math.abs(x.c)>=1;});
   if(w.length)W.push((en()?'Mega caps '+(up?'lifting':'dragging')+': ':'權值大股'+(up?'帶頭漲':'帶頭跌')+'：')+w.slice(0,3).map(function(x){return (en()?x.s:x.n+' '+x.s)+' '+sg(x.c,1)+'%';}).join('、')
     +(en()?'':'（這幾檔佔指數比重大，影響最直接）')+(a.length?(en()?'; against: ':'；反向：')+a.slice(0,2).map(function(x){return x.s+' '+sg(x.c,1)+'%';}).join('、'):'')+(en()?'.':'。'));
   if(sec&&sec.length>=8){var ld=up?sec[0]:sec[sec.length-1];if(Math.abs(ld.c)>=0.8)W.push(en()?'Sector: '+ld.en+' '+sg(ld.c,1)+'%.':'類股：'+ld.zh+' '+sg(ld.c,1)+'% '+(up?'漲最多':'跌最多')+'。');}
   var tn=q['^TNX'];if(tn&&tn.prev){var bp=(tn.price-tn.prev)*100;if(Math.abs(bp)>=4)W.push(en()?'10-year yield '+sg(bp,0)+' bp.'
     :'美國 10 年期公債殖利率 '+sg(bp,0)+' bp（'+f(tn.price,2)+'%）：'+(bp<0?'利率下降，未來獲利折現回來更值錢，通常有利科技成長股。':'利率上升，股票的相對吸引力下降，高本益比的成長股最受壓。'));}
   var dx=q['DX-Y.NYB'];if(dx&&dx.chg!=null&&Math.abs(dx.chg)>=0.4)W.push(en()?'Dollar '+sg(dx.chg,1)+'%.':'美元指數 '+sg(dx.chg,1)+'%：'+(dx.chg>0?'美元走強，資金偏保守，也不利新台幣與新興市場。':'美元走弱，資金較願意承擔風險，新台幣與新興市場通常受惠。'));
   var oil=q['CL=F'];if(oil&&oil.chg!=null&&Math.abs(oil.chg)>=2)W.push(en()?'Oil '+sg(oil.chg,1)+'%.':'原油 '+sg(oil.chg,1)+'%：'+(oil.chg>0?'能源股受惠，但油價上漲會加重通膨疑慮。':'能源股承壓，但油價下跌減輕通膨壓力。'));
   var vx=q['^VIX'];if(vx&&vx.chg!=null&&(up?vx.chg<=-5:vx.chg>=8))W.push(en()?'VIX '+sg(vx.chg,1)+'%.':'恐慌指數 VIX '+sg(vx.chg,1)+'%：'+(up?'避險需求退潮，買盤回來。':'避險需求升高，市場在找保護。'));
   (WHY.ev||[]).forEach(function(e){W.push(en()?'Data: '+e.zh:'經濟數據（'+e.date.slice(5)+' 公布）：'+e.zh+' '+e.lab+'。');});
   (WHY.news||[]).forEach(function(n){W.push({t:(en()?'Headline: ':'新聞：')+n.t,l:n.l});});
   if(W.length===(big?0:1))W.push(en()?'No clear driver in rates, dollar, oil or mega caps.':'利率、美元、油價和權值股都沒有特別大的變化：比較像一般的資金進出，不是單一事件造成。');
   return W;}
 function pull(){if(dead||document.hidden)return;var ss=session(),off=document.getElementById('idoff');
   var syms=CORE.concat(SEC.map(function(x){return x[0];}),CROSS,MEGA.map(function(x){return x[0];})).slice(0,25);
   fetch('api/quote?s='+encodeURIComponent(syms.join(','))+'&vol=SPY,QQQ',{cache:'no-store'}).then(function(r){if(r.status===404||r.status===405){dead=true;throw 0;}if(!r.ok)throw 0;return r.json();}).then(function(d){
     if(off)off.hidden=true;var q=d.q||{},o=read(q),one=document.getElementById('idone'),ul=document.getElementById('idlist');if(!o)return;
     var tag=ss==='open'?'':(en()?' (market closed — last session)':'（美股目前'+(ss==='pre'?'尚未開盤':'已收盤')+'，以下是最近一個交易日）');
     one.textContent=o.one+tag;var st=document.getElementById('idst'),qt=(q['^GSPC']||{}).t;
     if(st){var p=function(n){return ('0'+n).slice(-2);},n=new Date(),tq=qt?new Date(qt*1000):null,tp=function(d){return d.toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Asia/Taipei'});};
      st.textContent='🕒 '+(en()?'Updated '+tp(n)+' Taipei'+(tq?' · S&P quote '+tp(tq):'')+' · refreshes every minute'
        :'最後更新 '+tp(n)+'（台北）'+(tq?'・標普報價時間 '+tp(tq):'')+'・每分鐘自動更新');}var wb=document.getElementById('idwhyb'),wu=document.getElementById('idwhy');if(wb&&wu){wu.textContent='';o.W.forEach(function(x){var li=document.createElement('li');
       if(typeof x==='string')li.textContent=x;else if(x.l){var a=document.createElement('a');a.href=x.l;a.target='_blank';a.rel='noopener';a.textContent=x.t;li.appendChild(a);}else li.textContent=x.t;wu.appendChild(li);});wb.hidden=!o.W.length;}
     ul.innerHTML=o.L.map(function(x){var li=document.createElement('li');li.textContent=x;return li.outerHTML;}).join('');}).catch(function(){});}
 pull();setInterval(pull,60000);document.addEventListener('visibilitychange',function(){if(!document.hidden)pull();});
})();
"""
JS = (_JS.replace("__SEC__", json.dumps(SECTORS, ensure_ascii=False)).replace("__CORE__", json.dumps(CORE))
      .replace("__CROSS__", json.dumps(CROSS)).replace("__MEGA__", json.dumps(MEGA, ensure_ascii=False)))
