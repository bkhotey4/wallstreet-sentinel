"""盤前／盤後跳空 (on the 開盤前 30 秒 page): while US stocks trade before the open or after the close, the browser pulls the
extended-hours price from /api/quote?ext= every minute and compares the move with each stock's normal daily move (one-year
standard deviation, /api/quote?full=1).  Key stocks are fixed; the viewer's own watchlist and holdings are read from this
browser only (never sent anywhere but the symbol to the quote service, never published).  Describes, not advice."""
from __future__ import annotations

import json

from tools.sitekit import T, card

CF_URL = "https://wallstreet-sentinel.pages.dev"
KEY = [("SPY", "標普 500 ETF"), ("QQQ", "那斯達克 100 ETF"), ("SMH", "半導體 ETF"), ("NVDA", "輝達"), ("TSM", "台積電 ADR"),
       ("AAPL", "蘋果"), ("MSFT", "微軟"), ("AMZN", "亞馬遜"), ("GOOGL", "Alphabet"), ("META", "Meta"), ("AVGO", "博通"),
       ("AMD", "超微"), ("TSLA", "特斯拉")]
BIG, WATCH = 2.0, 1.0          # |move| in multiples of the stock's normal daily move: 明顯跳空 / 留意


def sec_ext_gaps(eng) -> str:
    note = ("美股正常交易時間以外（台北時間約 16:00–21:30 盤前、04:00–08:00 盤後，依夏令／冬令時間調整）也有成交，"
            "這裡每分鐘抓一次最新的盤前／盤後成交價，和前一個交易日收盤比較。平常波動＝過去一年每日漲跌幅的標準差；"
            f"跳空超過 {BIG:.0f} 倍平常波動標「明顯跳空」，超過 {WATCH:.0f} 倍標「留意」。盤前盤後成交量小，價格容易誇大，開盤後常常會修正。"
            "「你的持股／自選股」只從你這台瀏覽器讀取，查詢時只把代號送到本站的報價服務，不會公開也不會保存。"
            "報價：Yahoo Finance，約有數分鐘延遲。只描述現況，不是投資建議。")
    body = (f'<div id="xgbox" data-key="{json.dumps(KEY, ensure_ascii=False).replace(chr(34), "&quot;")}">'
            f'<p class="small muted" id="xgst">🕒 {T("等待即時報價…", "Waiting for live quotes…")}</p>'
            f'<p class="rimp big2"><b id="xgone">{T("一句話看懂：美股盤前／盤後的跳空會在這裡每分鐘更新。", "Pre-market / after-hours gaps, live.")}</b></p>'
            '<div class="scroll"><table class="mini" id="xgtab" hidden></table></div></div>'
            f'<p class="lqoff" id="xgoff">{T("即時跳空只在 Cloudflare 版網址可用：", "Live only on the Cloudflare site: ")}'
            f'<a href="{CF_URL}/#premarket" target="_blank" rel="noopener">{CF_URL.replace("https://", "")}</a></p>'
            f'<details class="sgx"><summary>{T("怎麼判讀", "How to read")}</summary><p class="note">{T(note, "")}</p></details>')
    return card("盤前／盤後跳空：開盤前誰在大動", "Pre-market & after-hours gaps", body, "wide")


JS = r"""
(function(){var box=document.getElementById('xgbox');if(!box)return;var KEY=[];try{KEY=JSON.parse(box.dataset.key);}catch(e){}
 var dead=false,SD={},sdAt=0;
 function us(s){return /^[A-Z][A-Z.\-]{0,6}$/.test(s)&&!/\.(TW|TWO|T|HK|KS|L|TO)$/.test(s);}
 function mine(){var o={};try{var p=JSON.parse(localStorage.getItem('wss_portfolio_v1')||'null');(p&&p.h||[]).forEach(function(h){var s=String(h.s||'').trim().toUpperCase();if(us(s))o[s]='持股';});}catch(e){}
  try{(JSON.parse(localStorage.getItem('wss_watch_v1')||'[]')||[]).forEach(function(w){var s=String(typeof w==='string'?w:(w&&w.s)||'').trim().toUpperCase();if(us(s)&&!o[s])o[s]='自選';});}catch(e){}
  return o;}
 function get(list,q){var ch=[];for(var i=0;i<list.length;i+=25)ch.push(list.slice(i,i+25));
  return Promise.all(ch.map(function(c){return fetch('api/quote?s='+encodeURIComponent(c.join(','))+q(c),{cache:'no-store'}).then(function(r){if(r.status===404||r.status===405){dead=true;throw 0;}if(!r.ok)throw 0;return r.json();});}))
   .then(function(a){var q={};a.forEach(function(d){Object.assign(q,d.q||{});});return q;});}
 function f(x,d){return x==null||isNaN(x)?'—':(+x).toFixed(d);}
 function sg(x,d){return x==null?'—':(x>=0?'+':'')+f(x,d)+'%';}
 function pull(){if(dead||document.hidden)return;var my=mine(),names={};KEY.forEach(function(k){names[k[0]]=k[1];});
  var list=KEY.map(function(k){return k[0];});Object.keys(my).forEach(function(s){if(list.indexOf(s)<0)list.push(s);});
  var needSd=Date.now()-sdAt>600000||list.some(function(s){return !(s in SD);});
  Promise.all([get(list,function(c){return '&ext='+encodeURIComponent(c.join(','));}),needSd?get(list,function(){return '&full=1';}):Promise.resolve(null)]).then(function(r){
   var q=r[0];if(r[1]){Object.keys(r[1]).forEach(function(s){SD[s]=r[1][s].sd1y;});sdAt=Date.now();}
   var off=document.getElementById('xgoff');if(off)off.hidden=true;
   var rows=list.filter(function(s){return q[s]&&q[s].ext;}).map(function(s){var e=q[s].ext,sd=SD[s],k=sd?Math.abs(e.chg)/sd:null;
     return {s:s,n:names[s]||q[s].name||s,tag:my[s]||'',e:e,sd:sd,k:k,lv:k==null?'':k>=__BIG__?'big':k>=__WATCH__?'watch':''};});
   var st=document.getElementById('xgst'),one=document.getElementById('xgone'),tb=document.getElementById('xgtab');
   var tp=function(t){return new Date(t*1000).toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Asia/Taipei'});};
   st.textContent='🕒 最後更新 '+tp(Date.now()/1000)+'（台北）・每分鐘自動更新';
   if(!rows.length){one.textContent='一句話看懂：目前不是美股盤前／盤後時段（或還沒有成交），沒有跳空資料；正常交易時間請看下方「開盤後即時盤勢」。';tb.hidden=true;return;}
   var sess=rows[0].e.sess==='pre'?'盤前':'盤後',big=rows.filter(function(x){return x.lv==='big';}),mineBig=big.filter(function(x){return x.tag;});
   var spy=rows.filter(function(x){return x.s==='SPY';})[0],qqq=rows.filter(function(x){return x.s==='QQQ';})[0];
   one.textContent='一句話看懂（'+sess+'）：'+(spy?'標普 ETF '+sg(spy.e.chg,2):'')+(qqq?'、那斯達克 ETF '+sg(qqq.e.chg,2):'')+'；'
     +(big.length?big.length+' 檔明顯跳空（超過 __BIG__ 倍平常波動）：'+big.slice(0,5).map(function(x){return x.s+' '+sg(x.e.chg,1);}).join('、')
       +(mineBig.length?'，其中 '+mineBig.length+' 檔是你的持股／自選':''):'沒有明顯跳空（都在平常單日波動的 __BIG__ 倍以內）')+'。';
   rows.sort(function(a,b){return (b.tag?1:0)-(a.tag?1:0)||(b.k||0)-(a.k||0);});
   tb.textContent='';var h=tb.insertRow();['代號','前一日收盤',sess+'價','跳空','平常單日波動','倍數',''].forEach(function(x,i){var th=document.createElement('th');th.textContent=x;if(i&&i<6)th.className='r';h.appendChild(th);});
   rows.forEach(function(x){var tr=tb.insertRow();var c0=tr.insertCell();c0.textContent=x.s+' '+x.n+(x.tag?'（'+x.tag+'）':'');
    [f(x.e.base,2),f(x.e.px,2)+' · '+tp(x.e.t),sg(x.e.chg,2),x.sd?'±'+f(x.sd,1)+'%':'—',x.k==null?'—':f(x.k,1)+' 倍'].forEach(function(v,i){var c=tr.insertCell();c.className='r'+(i===2?(x.e.chg>0?' up':x.e.chg<0?' dn':''):'');c.textContent=v;});
    var cl=tr.insertCell();cl.textContent=x.lv==='big'?(x.e.chg>0?'🟢 明顯跳空上漲':'🔴 明顯跳空下跌'):x.lv==='watch'?'⚠️ 留意':'';});
   tb.hidden=false;}).catch(function(){});}
 pull();setInterval(pull,60000);document.addEventListener('visibilitychange',function(){if(!document.hidden)pull();});
})();
""".replace("__BIG__", f"{BIG:g}").replace("__WATCH__", f"{WATCH:g}")
