"""即時新聞 (總覽): headlines from /api/news (Cloudflare function, reliable feeds only, keyword market tags), refreshed every
5 minutes in the browser.  When the live bar has lit chips (a market moving unusually), headlines from the last 3 hours whose
tags match that market are marked ⚡ and counted in the lead; if none match, the lead says so instead of guessing a cause.
GitHub Pages has no /api/news: the first failed request hides the card."""
from __future__ import annotations

from tools.sitekit import card


def sec_news_live(eng) -> str:
    body = ('<p class="rimp" id="nl_lead"><b>一句話看懂：</b>讀取最新新聞中…</p>'
            '<div class="nlf" id="nl_f"></div><ul class="nll" id="nl_list"></ul>'
            '<button type="button" class="btn nlmore" id="nl_more" hidden></button>'
            '<p class="note" id="nl_note">來源固定：中央社、BBC 中文、聯準會、歐洲央行、日本央行、BBC Business、MarketWatch、CNBC（市場、財經、頭條、國際、政治），加上美國證交會（SEC）最新 8-K 申報；🔴 是追蹤池或市值 1,000 億美元以上的公司申報第 5.02 項（董事或高階主管離職、任命、薪酬安排），通常比媒體報導早幾十分鐘，置頂 24 小時；「離職／任命」與職位由程式從申報原文判斷，判斷不出來只寫「高層人事異動」；破產、重大資安事件、資產減損、下市通知、財報須重編這幾項也會 🔴。每則 🔴 底下的「影響估算」＝這檔股票現在的漲跌 × 過去的關係：標普 500 權重（State Street SPY 官方持股）、過去 120 個交易日最常一起動的美股（β）、本站台美連動模型裡跟它連動、樣本外驗證過的台股；是平均關係的推算，不是預測。'
            '綜合新聞只留跟市場有關的標題。標籤是用關鍵字自動分類，不是 AI 判斷；⚡ 代表這則新聞的時間和分類，對得上即時燈號裡正在大動的行情（油價大動時，地緣政治新聞也算），'
            '但對得上不等於就是原因。每 5 分鐘自動更新。不構成投資建議。</p>')
    h = card("即時新聞", "Live news", body, "wide", sub="可靠來源的最新標題，自動標上可能牽動哪些行情")
    return h.replace('<section class="card', '<section id="newslive" class="card', 1)


CSS = (".nlf{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}.nlf button{font-size:12px;padding:2px 9px;border-radius:99px;border:1px solid var(--bd);"
       "background:var(--card);color:inherit;cursor:pointer}.nlf button.on{border-color:var(--ac);color:var(--ac)}"
       ".nll{list-style:none;padding:0;margin:4px 0}.nll li{padding:7px 0;border-bottom:1px solid var(--bd);line-height:1.5}"
       ".nll a{color:inherit;text-decoration:none}.nll a:hover{text-decoration:underline}.nll .m{font-size:12px;color:var(--mu)}"
       ".nll .tg{font-size:11px;border:1px solid var(--bd);border-radius:99px;padding:0 6px;margin-left:4px}.nll li.hot{background:var(--wash)}"
       ".nll .imp{font-size:13px;margin-top:4px}.nll .imp ul{margin:2px 0 0 18px;padding:0}.nll .of{color:var(--ac);font-weight:700}.nll li.sec{background:var(--wash);border-left:3px solid var(--dn,#c0392b);padding-left:8px}.nlmore{margin-top:6px}")

# chip words in the live bar → news tags (the bar's own names, so a lit chip finds its headlines)
JS = r"""
(function(){var box=document.getElementById('newslive');if(!box)return;
var MAP=[['標普','美股'],['那斯達克','美股'],['道瓊','美股'],['VIX','美股'],['羅素','美股'],['台股','台股'],['加權','台股'],['台積電','台股'],
 ['殖利率','利率'],['美債','利率'],['公債','利率'],['原油','油價'],['油','油價'],['原油','地緣'],['油','地緣'],['美元','匯率'],['日圓','匯率'],['台幣','匯率'],['黃金','黃金'],
 ['半導體','科技'],['輝達','科技'],['高收益債','利率']];
var items=[],tag='',shown=5,tm=null;
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function ago(ts){var m=Math.max(0,Math.round((Date.now()/1000-ts)/60));return m<60?m+' 分鐘前':m<1440?Math.round(m/60)+' 小時前':Math.round(m/1440)+' 天前';}
function lit(){var t={},n=[];document.querySelectorAll('.lqchip:not(.ok)').forEach(function(c){var x=c.textContent||'';
  MAP.forEach(function(p){if(x.indexOf(p[0])>=0&&!t[p[1]]){t[p[1]]=1;n.push(p[1]);}});});return n;}
function paint(){var hot=lit(),now=Date.now()/1000,list=document.getElementById('nl_list');
  var xs=items.filter(function(x){return !tag||x.tags.indexOf(tag)>=0;});
  var al=function(x){return x.alert&&now-x.ts<24*3600;};          // SEC officer filings of the last day stay pinned on top
  xs=xs.filter(al).concat(xs.filter(function(x){return !al(x);}));
  var isHot=function(x){return now-x.ts<3*3600&&x.tags.some(function(g){return hot.indexOf(g)>=0;});};
  list.innerHTML=xs.slice(0,shown).map(function(x){return '<li'+(al(x)?' class="sec"':isHot(x)?' class="hot"':'')+'>'+(al(x)?'🔴 ':isHot(x)?'⚡ ':'')+
    '<a href="'+esc(x.u)+'" target="_blank" rel="noopener noreferrer">'+esc(x.t)+'</a><div class="m">'+(x.off?'<span class="of">官方</span> ':'')+esc(x.s)+
    (x.lang==='en'?'（英文）':'')+' · '+ago(x.ts)+x.tags.map(function(g){return '<span class="tg">'+esc(g)+'</span>';}).join('')+'</div>'
    +(al(x)&&x.sym?'<div class="imp" data-sym="'+esc(x.sym)+'">影響估算計算中…</div>':'')+'</li>';}).join('')
    ||'<li class="m">這個分類目前沒有新聞。</li>';
  list.querySelectorAll('.imp').forEach(fillImpact);
  var mb=document.getElementById('nl_more');mb.hidden=xs.length<=5;mb.textContent=shown<xs.length?'看更多（共 '+xs.length+' 則）':'收起';
  var lead=document.getElementById('nl_lead'),hn=items.filter(isHot).length;
  var top=items[0],sa=items.filter(al);
  lead.innerHTML='<b>一句話看懂：</b>'+(sa.length?'🔴 '+esc(sa[0].t)+'（'+ago(sa[0].ts)+'，公司向美國證交會的正式申報，點進去看原文）'
    +(sa.length>1?'；過去 24 小時共 '+sa.length+' 家追蹤公司申報高層人事。':'。'):'')+(hot.length?(hn?'正在大動的行情（'+esc(hot.join('、'))+'），最近 3 小時有 '+hn+' 則時間和分類對得上的新聞，標了 ⚡。'
    :'正在大動的行情（'+esc(hot.join('、'))+'）目前找不到時間對得上的新聞，原因還不清楚。')
    :(top?'最新一則（'+ago(top.ts)+'）：'+esc(top.t):'目前沒有新聞。'));}
// 影響估算：impact_map.json（建置時算好的權重與過去關係）× 這檔股票現在的漲跌（盤前盤後優先）
var IM=null;
function pct(v,d){return (v>0?'+':'')+v.toFixed(d==null?1:d)+'%';}
function fillImpact(el){var s=el.getAttribute('data-sym'),m=IM&&IM.map&&IM.map[s];
  if(!m){el.textContent=IM?'這家公司還沒有影響估算資料。':'影響估算計算中…';return;}
  var syms=[s].concat(m.peers.map(function(p){return p.sym;}),m.tw.map(function(p){return p.sym;})).slice(0,25);
  fetch('/api/quote?s='+encodeURIComponent(syms.join(','))+'&ext='+encodeURIComponent(s)).then(function(r){return r.json();}).then(function(d){var q=(d&&d.q)||{};
    var o=q[s]||{},mv=o.ext&&typeof o.ext.chg==='number'?o.ext.chg:o.chg,ses=o.ext&&typeof o.ext.chg==='number'?(o.ext.sess==='pre'?'盤前':'盤後'):'今天';
    if(typeof mv!=='number'){el.textContent='影響估算：還拿不到 '+s+' 的即時價格。';return;}
    var cur=function(t){var x=q[t];return x&&typeof x.chg==='number'?'（現 '+pct(x.chg)+'）':'';};
    var h='<b>影響估算</b>（依過去的平均關係推算，不是預測；重大消息當天常比平均更極端）：'+esc(m.zh)+' '+ses+' <b>'+pct(mv)+'</b>';
    h+='<ul>';
    if(m.w_spx)h+='<li>標普 500：它占 '+m.w_spx.toFixed(1)+'% → 光它本身約讓標普動 <b>'+pct(m.w_spx*mv/100,2)+'</b>（不含連帶效應）</li>';
    if(m.peers.length)h+='<li>過去 '+IM.win+' 個交易日最常一起動的美股：'+m.peers.map(function(p){return esc(p.zh)+' 約 '+pct(p.beta*mv)+cur(p.sym);}).join('、')+'</li>';
    if(m.tw.length)h+='<li>台股隔天（本站台美連動模型，樣本外驗證過的才列）：'+m.tw.map(function(p){return esc(p.zh)+' 約 '+pct(p.beta*mv);}).join('、')+'</li>';
    else h+='<li>台股：沒有和它連動夠穩定的台股（模型驗證沒過的不列）。</li>';
    el.innerHTML=h+'</ul>';}).catch(function(){el.textContent='影響估算：即時價格暫時拿不到。';});}
fetch('/impact_map.json').then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){IM=d;paint();}).catch(function(){IM={map:{}};});
function filters(){var c={};items.forEach(function(x){x.tags.forEach(function(g){c[g]=(c[g]||0)+1;});});
  var f=document.getElementById('nl_f');f.innerHTML=['<button type="button" data-t=""'+(tag?'':' class="on"')+'>全部</button>'].concat(Object.keys(c).sort(function(a,b){return c[b]-c[a];})
    .map(function(g){return '<button type="button" data-t="'+esc(g)+'"'+(tag===g?' class="on"':'')+'>'+esc(g)+' '+c[g]+'</button>';})).join('');}
document.getElementById('nl_f').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;tag=b.getAttribute('data-t');shown=5;filters();paint();});
document.getElementById('nl_more').addEventListener('click',function(){shown=shown>5?5:60;paint();});
function load(){fetch('/api/news',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){
  items=d.items||[];filters();paint();var n=document.getElementById('nl_note');
  n.setAttribute('data-up','1');var st=n.querySelector('.nlup');if(!st){st=document.createElement('span');st.className='nlup';n.prepend(st);}
  st.textContent='最後更新 '+new Date(d.ts*1000).toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit'})+'（'+(d.sources||[]).length+' 個來源有回應）。';
}).catch(function(){if(!items.length){box.hidden=true;clearInterval(tm);}});}
load();tm=setInterval(function(){if(!document.hidden)load();},300000);
setInterval(paint,60000);   // the live bar lights change every minute
})();
"""
