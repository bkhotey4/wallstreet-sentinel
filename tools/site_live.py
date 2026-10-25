"""即時層：在 Cloudflare 版網址（有 /api/quote）上，頂端行情列每分鐘自己更新、盤中急跌門檻即時亮燈、可查任何股票。
GitHub Pages 版沒有 /api/quote：第一次請求失敗就安靜停用，頁面維持整點建置的數字。模型結論仍每小時更新，即時層只顯示原始數字與簡單門檻。"""
from __future__ import annotations

import json

from tools.sitekit import T, card

CF_URL = "https://wallstreet-sentinel.pages.dev"
POLL_S = 60

# simple, transparent intraday thresholds — a reminder, not a forecast
RULES = [
    {"k": "vix30", "sym": "^VIX", "f": "lvl", "op": ">=", "v": 30, "dg": 1,
     "zh": "VIX 恐慌指數 ≥ 30（市場很恐慌）", "en": "VIX ≥ 30 (high fear)"},
    {"k": "vixinv", "sym": "^VIX", "den": "^VIX3M", "f": "ratio", "op": ">=", "v": 1, "dg": 2,
     "zh": "VIX ÷ 3 個月 VIX ≥ 1（短期恐慌壓過長期，期限結構倒掛）", "en": "VIX / VIX3M ≥ 1 (term structure inverted)"},
    {"k": "spx2", "sym": "^GSPC", "f": "chg", "op": "<=", "v": -2, "dg": 1,
     "zh": "標普 500 單日跌超過 2%", "en": "S&P 500 down > 2% today"},
    {"k": "sox3", "sym": "^SOX", "f": "chg", "op": "<=", "v": -3, "dg": 1,
     "zh": "費城半導體單日跌超過 3%", "en": "SOX down > 3% today"},
    {"k": "tw3", "sym": "^TWII", "f": "chg", "op": "<=", "v": -3, "dg": 1,
     "zh": "台股加權單日跌超過 3%", "en": "TAIEX down > 3% today"},
    {"k": "ks3", "sym": "^KS11", "f": "chg", "op": "<=", "v": -3, "dg": 1,
     "zh": "韓國股市單日跌超過 3%（記憶體股為主）", "en": "KOSPI down > 3% today"},
    {"k": "hyg1", "sym": "HYG", "f": "chg", "op": "<=", "v": -1, "dg": 1,
     "zh": "高收益債 ETF 單日跌超過 1%（信用市場緊張）", "en": "HYG down > 1% today (credit stress)"},
]
EXTRA = sorted({r["sym"] for r in RULES} | {r["den"] for r in RULES if r.get("den")})


def bar_html() -> str:
    """Status line + live threshold lights; hidden until the first live quote arrives."""
    return ('<div class="lqbar" id="lqbar" hidden><div class="lqhead"><b id="lqone"></b><span id="lqst" class="lqst"></span></div>'
            '<div id="lqal" class="lqal"></div>'
            f'<p class="lqnote">{T("即時門檻是簡單提醒，不是預測；漲跌幅以各市場最近一個交易日計。模型判斷（AI 判斷、泡沫分組等）仍每小時更新。報價：Yahoo Finance，約有數分鐘延遲。", "Simple thresholds, not forecasts; model verdicts still update hourly. Quotes: Yahoo Finance, may be delayed.")}</p></div>')


def sec_lookup(eng) -> str:
    body = (f'<p class="rimp big2"><b>{T("一句話看懂：輸入任何股票代號，抓最新報價（美股直接打代號，台股加 .TW，例如 2330.TW）。", "Type any ticker for a live quote (Taiwan: add .TW).")}</b></p>'
            '<form class="lqf" id="lqf" autocomplete="off"><input id="lqin" class="lqin" maxlength="15" placeholder="NVDA、2330.TW、^SOX" aria-label="ticker">'
            f'<button class="btn" type="submit">{T("查詢", "Look up")}</button></form><div id="lqout" class="lqout"></div>'
            f'<p class="lqoff" id="lqoff">{T("這個功能只在 Cloudflare 版網址可用：", "Only on the Cloudflare site: ")}<a href="{CF_URL}" target="_blank" rel="noopener">{CF_URL.replace("https://", "")}</a></p>'
            f'<p class="note">{T("只顯示公開報價，不是投資建議；查詢不會被記錄。", "Public quotes only, not advice; lookups are not logged.")}</p>')
    return card("查任何股票（即時報價）", "Any ticker (live quote)", body, "wide")


def sec_watch(eng) -> str:
    body = (f'<p class="rimp big2"><b>{T("一句話看懂：加入你想追的任何股票，看它離 200 日均線多遠、RSI 冷熱、離一年高點多遠，以及近一個月的歷史波動區間。", "Your own watchlist: distance from the 200-day average, RSI, drawdown and a one-month volatility range.")}</b></p>'
            '<form class="lqf" id="wlf" autocomplete="off"><input id="wlin" class="lqin" maxlength="15" placeholder="SMR、OKLO、3231.TW" aria-label="ticker">'
            f'<button class="btn" type="submit">{T("加入", "Add")}</button></form><div id="wlbox" class="scroll"></div>'
            f'<p class="lqoff" id="wloff">{T("這個功能只在 Cloudflare 版網址可用：", "Only on the Cloudflare site: ")}<a href="{CF_URL}" target="_blank" rel="noopener">{CF_URL.replace("https://", "")}</a></p>'
            f'<details class="sgx"><summary>{T("每一欄怎麼看", "How to read")}</summary><p class="note">{T(WL_NOTE, "")}</p></details>')
    return card("自選股觀察（存在你的瀏覽器）", "My watchlist (kept in your browser)", body, "wide")


WL_NOTE = ("清單只存在你這台裝置的瀏覽器（換手機或清除瀏覽資料就不見），查詢時只把代號送到本站的報價服務，不留存。"
           "距 200 日線＝現價比過去 200 個交易日平均高或低多少，常用來分辨長期趨勢向上或向下。"
           "RSI(14)＝近 14 天漲跌力道，70 以上偏熱、30 以下偏冷，強勢股可以長期待在 70 以上，不代表會反轉。"
           "近一個月波動區間＝用近 20 天的實際波動推算，一個月後股價約有三分之二的機率落在這個範圍（常態分配假設，極端行情會超出）。"
           "資料：Yahoo Finance，約有延遲。不是投資建議。")


CSS = (".lqbar{margin:8px 0 4px;padding:9px 12px;border:1px solid var(--bd);border-radius:10px;background:var(--card)}"
       ".lqhead{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:baseline}.lqst{font-size:12px;color:var(--mu)}.lqst.on{color:var(--up)}"
       ".lqal{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 2px}.lqchip{font-size:12.5px;padding:2px 9px;border-radius:999px;border:1px solid var(--bd)}"
       ".lqchip.hit{border-color:var(--dn);color:var(--dn);font-weight:600}.lqchip.ok{color:var(--mu)}"
       ".lqnote{margin:4px 0 0;font-size:11.5px;color:var(--mu)}.tile .asof.lv{color:var(--up)}"
       ".wlt td,.wlt th{white-space:nowrap}.wlx{background:none;border:0;color:var(--mu);cursor:pointer;font-size:14px}.wlx:hover{color:var(--dn)}"
       ".lqf{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}.lqin{flex:1;min-width:0;max-width:260px;padding:6px 10px;border:1px solid var(--bd);"
       "border-radius:8px;background:var(--bg);color:var(--tx);font-size:15px}.lqout{font-size:15px;margin:6px 0}.lqoff{font-size:12.5px;color:var(--mu)}")

_JS = r"""
(function(){var R=__RULES__,EX=__EXTRA__,POLL=__POLL__*1000;
 var bar=document.getElementById('lqbar');var tiles=[].slice.call(document.querySelectorAll('.tile[data-lq]'));
 var want={};tiles.forEach(function(t){want[t.getAttribute('data-lq')]=1;});EX.forEach(function(s){want[s]=1;});
 var dead=false,lastOk=0,data={};function en(){return document.documentElement.lang==='en';}
 function f(x,d){return x==null||isNaN(x)?'—':Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
 function sg(x,d){if(x==null||isNaN(x))return '—';if(Math.abs(x)<0.5*Math.pow(10,-d))x=0;return (x>0?'+':x<0?'':'')+f(x,d);}
 function api(list,full){return fetch('api/quote?s='+encodeURIComponent(list)+(full?'&full=1':''),{cache:'no-store'}).then(function(r){if(r.status===404||r.status===405){dead=true;throw 0;}if(!r.ok)throw 0;return r.json();});}
 function hhmm(t){if(!t)return '';var d=new Date(t*1000),p=function(n){return ('0'+n).slice(-2);};var tm=p(d.getHours())+':'+p(d.getMinutes());
   return d.toDateString()===new Date().toDateString()?tm:(d.getMonth()+1)+'/'+d.getDate()+' '+tm;}
 function paintTiles(q){tiles.forEach(function(t){var s=t.getAttribute('data-lq'),x=q[s];if(!x)return;var dg=+t.getAttribute('data-dg')||0;
   var v=t.querySelector('.tv'),c=t.querySelector('.tc'),a=t.querySelector('.asof');if(v)v.textContent=f(x.price,dg);
   if(c&&x.chg!=null){c.textContent=sg(x.chg,2)+'%';c.classList.remove('up','dn');if(x.chg>0)c.classList.add('up');else if(x.chg<0)c.classList.add('dn');}
   if(a){a.textContent=hhmm(x.t);a.classList.add('lv');}});}
 function val(r,q){var x=q[r.sym];if(!x)return null;if(r.f==='lvl')return x.price;if(r.f==='chg')return x.chg;
   if(r.f==='ratio'){var y=q[r.den];return y&&y.price?x.price/y.price:null;}return null;}
 function paintRules(q){var hits=[],h='';R.forEach(function(r){var v=val(r,q);if(v==null)return;var hit=r.op==='>='?v>=r.v:v<=r.v;if(hit)hits.push(r);
   h+='<span class="lqchip '+(hit?'hit':'ok')+'">'+(hit?'● ':'○ ')+(en()?r.en:r.zh)+'：'+(r.f==='chg'?sg(v,r.dg)+'%':f(v,r.dg))+'</span>';});
   document.getElementById('lqal').innerHTML=h;var one=document.getElementById('lqone');
   one.textContent=hits.length?(en()?'Live: '+hits.length+' threshold(s) hit':'一句話看懂（即時）：觸發 '+hits.length+' 項急跌／恐慌門檻，紅色那幾項')
     :(en()?'Live: no stress threshold hit':'一句話看懂（即時）：目前沒有觸發任何急跌／恐慌門檻');}
 function ago(){var st=document.getElementById('lqst');if(!st||!lastOk)return;var s=Math.round((Date.now()-lastOk)/1000);
   st.className='lqst on';st.textContent='● '+(en()?'live · updated '+(s<60?s+'s':Math.round(s/60)+'m')+' ago':'即時 · '+(s<60?s+' 秒前':Math.round(s/60)+' 分鐘前')+'更新');}
 function stale(){var st=document.getElementById('lqst');if(st&&lastOk){st.className='lqst';st.textContent=en()?'live paused — showing hourly data':'即時暫停，顯示整點資料';}}
 function pull(){if(dead||document.hidden)return;api(Object.keys(want).join(',')).then(function(d){var q=d.q||{};if(!Object.keys(q).length){stale();return;}data=q;lastOk=Date.now();
   if(bar)bar.hidden=false;var off=document.getElementById('lqoff');if(off)off.hidden=true;paintTiles(data);paintRules(data);ago();}).catch(function(){if(!dead)stale();});}
 pull();setInterval(pull,POLL);setInterval(ago,5000);document.addEventListener('visibilitychange',function(){if(!document.hidden&&Date.now()-lastOk>POLL)pull();});
 var lb=document.getElementById('langBtn');if(lb)lb.addEventListener('click',function(){setTimeout(function(){if(lastOk){paintRules(data);ago();}},0);});
 var fm=document.getElementById('lqf');if(fm){fm.addEventListener('submit',function(e){e.preventDefault();var s=(document.getElementById('lqin').value||'').trim().toUpperCase();
   var o=document.getElementById('lqout');if(!/^[A-Z0-9^=.\-]{1,15}$/.test(s)){o.textContent=en()?'Invalid ticker':'代號格式不對';return;}
   if(dead){o.textContent='';return;}o.textContent='…';
   api(s).then(function(d){var x=(d.q||{})[s];if(!x){o.textContent=en()?'No quote found':'找不到這個代號';return;}
     var cl=x.chg>0?'up':x.chg<0?'dn':'';o.innerHTML='';var b=document.createElement('b');b.textContent=x.name+'（'+s+'）';o.appendChild(b);
     o.appendChild(document.createTextNode(' '+f(x.price,2)+' '+x.cur+' '));var c=document.createElement('span');c.className=cl;c.textContent=sg(x.chg,2)+'%';o.appendChild(c);
     o.appendChild(document.createTextNode(' · '+hhmm(x.t)));})
   .catch(function(){o.textContent=dead?'':(en()?'Quote source unavailable, try later':'報價來源暫時取不到，稍後再試');});});}
 // watchlist: tickers in localStorage, one-year daily stats from /api/quote?full=1
 var WK='wss_watch_v1',wb=document.getElementById('wlbox');
 function wget(){try{var a=JSON.parse(localStorage.getItem(WK)||'[]');return Array.isArray(a)?a:[];}catch(e){return [];}}
 function wput(a){try{localStorage.setItem(WK,JSON.stringify(a));}catch(e){}}
 function cell(tr,txt,c){var td=document.createElement('td');td.className=c||'r';td.textContent=txt;tr.appendChild(td);return td;}
 var wseq=0;
 function wdraw(){if(!wb)return;var a=wget(),my=++wseq;wb.textContent='';
   if(!a.length){var p=document.createElement('p');p.className='small muted';p.textContent=en()?'Nothing yet — add a ticker above.':'還沒有自選股，在上面輸入代號加入。';wb.appendChild(p);return;}
   if(dead)return;
   api(a.join(','),1).then(function(d){if(my!==wseq)return;wb.textContent='';var q=d.q||{};var off=document.getElementById('wloff');if(off)off.hidden=true;
    var t=document.createElement('table');t.className='mini wlt';var hd=['代號','名稱','現價','今日','距 200 日線','RSI(14)','距 52 週高','近一個月波動區間',''],he=['Ticker','Name','Price','Today','vs 200d','RSI','From high','1-month range',''];
    var tr0=document.createElement('tr');hd.forEach(function(h,i){var th=document.createElement('th');th.textContent=en()?he[i]:h;if(i>1)th.className='r';tr0.appendChild(th);});var th0=document.createElement('thead');th0.appendChild(tr0);t.appendChild(th0);
    var tb=document.createElement('tbody');a.forEach(function(s){var x=q[s],tr=document.createElement('tr');cell(tr,s,'');
     if(!x){var td=cell(tr,en()?'not found':'找不到這個代號','muted');td.colSpan=7;}
     else{cell(tr,x.name,'small');cell(tr,f(x.price,2)+' '+x.cur);var c=cell(tr,sg(x.chg,2)+'%');if(x.chg)c.classList.add(x.chg>0?'up':'dn');
      var g=cell(tr,x.ma_gap!=null?sg(x.ma_gap,1)+'%':'—');if(x.ma_gap!=null)g.classList.add(x.ma_gap>=0?'up':'dn');
      cell(tr,x.rsi14!=null?f(x.rsi14,0)+(x.rsi14>=70?(en()?' hot':' 偏熱'):x.rsi14<=30?(en()?' cold':' 偏冷'):''):'—');
      var dd=x.hi52?(x.price/x.hi52-1)*100:null,h=cell(tr,dd!=null?sg(dd,1)+'%':'—');if(dd!=null&&dd<=-40)h.classList.add('dn');
      cell(tr,x.m1?f(x.m1[0],2)+' ～ '+f(x.m1[1],2):'—');}
     var del=document.createElement('button');del.type='button';del.className='wlx';del.textContent='✕';del.setAttribute('aria-label','remove '+s);
     del.addEventListener('click',function(){wput(wget().filter(function(y){return y!==s;}));wdraw();});var tdd=document.createElement('td');tdd.appendChild(del);tr.appendChild(tdd);tb.appendChild(tr);});
    t.appendChild(tb);wb.appendChild(t);}).catch(function(){var p=document.createElement('p');p.className='small muted';p.textContent=dead?'':(en()?'Quote source unavailable, try later':'報價來源暫時取不到，稍後再試');wb.appendChild(p);});}
 var wf=document.getElementById('wlf');if(wf){wf.addEventListener('submit',function(e){e.preventDefault();var s=(document.getElementById('wlin').value||'').trim().toUpperCase();
   if(!/^[A-Z0-9^=.\-]{1,15}$/.test(s))return;var a=wget();if(a.indexOf(s)<0&&a.length<25){a.push(s);wput(a);}document.getElementById('wlin').value='';wdraw();});
  setTimeout(wdraw,1500);}
})();
"""
JS = _JS.replace("__RULES__", json.dumps(RULES, ensure_ascii=False)).replace("__EXTRA__", json.dumps(EXTRA)).replace("__POLL__", str(POLL_S))
