"""我的價位追蹤（工具頁，2026-11-20）：使用者自己輸入成本、掛單、已出場的價格與股數，存在自己瀏覽器的 localStorage，
網頁每 45 秒用 /api/quote 抓報價，算距離、碰到掛單價的粗略機率、成交後實拿、帳面盈虧、出場後比現在多拿或少拿。
起因：使用者 11-19 晚上一直要在對話裡問「ORCL 124 有機會嗎」「我是不是賣太早」；這張卡讓網頁自己回答。
只送代號給本站報價服務；價格、股數、匯率都只留在使用者的裝置，不進網站、不進倉庫。"""
from __future__ import annotations

from tools.sitekit import T, card

FEE_US = 0.10          # % per side, the user's real KGI sub-brokerage fee (memory: kgi-actual-fee)
FEE_TW = 0.1425        # % broker fee per side, before any discount
TAX_TW = 0.30          # % securities transaction tax on the exit side (ETF 0.1% — the user can edit the fee box)
POLL_S = 45

NOTE = ("價格、股數與匯率只存在這台裝置的瀏覽器（清除瀏覽資料就不見），本站只收到代號、用來查報價。"
        "「碰到的機率」用近 20 個交易日的實際波動、假設漲跌機會對稱（隨機漫步）推算盤中曾經碰到該價位的機率："
        "2 ×（1 − Φ（|ln(掛單價 ÷ 現價)| ÷（日波動 × √剩餘時間）））。它只說距離和波動相比有多遠，不代表會往哪個方向走；"
        "財報、利率決議這類事件日的波動會比平常大，這時算出來的機率會偏小。剩餘時間：美股以美東 9:30–16:00、台股以 9:00–13:30 計算，已收盤時「今天」顯示 —。"
        "「成交後實拿」以出場方向計算：美股扣你設定的手續費％，台股扣手續費 0.1425％＋證交稅 0.3％（ETF 證交稅是 0.1％，可自行改手續費欄）。"
        "美股的台幣金額用即時美元兌台幣報價換算，抓不到時用你填的匯率。報價來自 Yahoo Finance，約有延遲。不是投資建議。")


def sec_tracker(eng) -> str:
    form = ('<form class="lqf trf" id="trf" autocomplete="off">'
            '<input id="trs" class="lqin" maxlength="15" placeholder="代號，例如 ORCL、2330.TW" aria-label="ticker">'
            '<select id="trk" class="lqin" aria-label="kind"><option value="cost">我持有（成本）</option>'
            '<option value="order">掛單價</option><option value="sold">已出場（成交價）</option></select>'
            '<input id="trp" class="lqin" inputmode="decimal" placeholder="價格" aria-label="price">'
            '<input id="trn" class="lqin" inputmode="numeric" placeholder="股數" aria-label="shares">'
            f'<button class="btn" type="submit">{T("加入", "Add")}</button></form>'
            '<div class="small trset">美股手續費 <input id="trfee" class="lqin trnum" inputmode="decimal" aria-label="US fee %">％　'
            '備用匯率（美元兌台幣）<input id="trfx" class="lqin trnum" inputmode="decimal" aria-label="USD/TWD"></div>')
    body = (f'<p class="rimp big2"><b>{T("一句話看懂：把你的成本、掛單價、已出場的成交價記在這裡，網頁每 45 秒自己算距離多遠、今天碰到的機率、成交後實拿多少，以及出場後比現在多拿或少拿——不用再問人。", "Track your cost, limit and exit prices: distance, rough odds of touching today, net proceeds, and how an exit compares with now.")}</b></p>'
            + form + '<div id="trbox" class="scroll"><p class="small muted">需要開啟 JavaScript 才會顯示。</p></div>'
            + f'<p class="small muted" id="trstamp"></p><details class="sgx"><summary>{T("怎麼算的", "How it works")}</summary><p class="note">{T(NOTE, "")}</p></details>')
    return card("我的價位追蹤（只存在你的瀏覽器）", "My price tracker (kept in your browser)", body, "wide")


CSS = (".trf select.lqin{max-width:170px}.trf #trp,.trf #trn{max-width:110px}.trset{margin:2px 0 6px;color:var(--mu)}"
       ".trnum{max-width:80px;padding:3px 6px;font-size:13px}.trt td,.trt th{white-space:nowrap}.trt .tot td{font-weight:600;border-top:1px solid var(--bd)}")

_JS = r"""
(function(){var box=document.getElementById('trbox');if(!box)return;
 var K='wss_track_v1',KS='wss_track_set_v1',POLL=__POLL__*1000,FUS=__FUS__,FTW=__FTW__,TTW=__TTW__,seq=0,last=null;
 function get(k,d){try{var v=JSON.parse(localStorage.getItem(k)||'null');return v==null?d:v;}catch(e){return d;}}
 function put(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}
 function rows(){var a=get(K,[]);return Array.isArray(a)?a:[];}
 function sets(){var s=get(KS,{});return {fee:isFinite(+s.fee)&&s.fee!==''?+s.fee:FUS,fx:isFinite(+s.fx)&&+s.fx>0?+s.fx:32.8};}
 function tw(s){return /\.(TW|TWO)$/.test(s);}
 function f(x,d){return x==null||!isFinite(x)?'—':Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
 function sg(x,d){return x==null||!isFinite(x)?'—':(x>0?'+':'')+f(x,d);}
 function erf(x){var t=1/(1+0.3275911*Math.abs(x)),y=1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-0.284496736)*t+0.254829592)*t*Math.exp(-x*x);return x>=0?y:-y;}
 function Phi(z){return 0.5*(1+erf(z/Math.SQRT2));}
 function parts(tz){var o={};new Intl.DateTimeFormat('en-US',{timeZone:tz,weekday:'short',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date()).forEach(function(p){o[p.type]=p.value;});return o;}
 function leftToday(s){var tz=tw(s)?'Asia/Taipei':'America/New_York',o=parts(tz),wd=o.weekday,m=(+o.hour%24)*60+(+o.minute);
   if(wd==='Sat'||wd==='Sun')return 0;var a=tw(s)?540:570,b=tw(s)?810:960;if(m>=b)return 0;return (b-Math.max(m,a))/(b-a);}
 function touch(P,L,sd,t){if(!(P>0&&L>0&&sd>0))return null;var d=Math.abs(Math.log(L/P));if(d<1e-9)return 1;if(!(t>0))return null;return Math.min(1,2*(1-Phi(d/(sd*Math.sqrt(t)))));}
 function exitNet(s,v,set){return v*(1-(tw(s)?(FTW+TTW):set.fee)/100);}
 function pct(x){return x==null?'—':Math.round(x*100)+'%';}
 function hm(t){if(!t)return '';return new Intl.DateTimeFormat('zh-TW',{timeZone:'Asia/Taipei',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(t*1000));}
 function td(tr,txt,c){var e=document.createElement('td');e.className=c||'r';e.textContent=txt;tr.appendChild(e);return e;}
 function draw(){var a=rows(),my=++seq,set=sets();
   if(!a.length){box.innerHTML='<p class="small muted">還沒有資料：在上面填代號、選「我持有／掛單價／已出場」、價格與股數後按加入。</p>';return;}
   var syms={};a.forEach(function(r){syms[r.s]=1;});var list=Object.keys(syms);list.push('TWD=X');
   fetch('api/quote?s='+encodeURIComponent(list.slice(0,25).join(','))+'&full=1',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){
    if(my!==seq)return;var q=d.q||{},fx=(q['TWD=X']&&q['TWD=X'].price>20)?q['TWD=X'].price:set.fx,tot={cost:0,order:0,sold:0},ts=0;
    var t=document.createElement('table');t.className='mini trt';t.innerHTML='<thead><tr><th>代號</th><th>類型</th><th class="r">記錄價</th><th class="r">股數</th><th class="r">現價</th><th class="r">距離</th><th class="r">今天碰到</th><th class="r">到明天收盤</th><th class="r">金額（台幣）</th><th>說明</th><th></th></tr></thead>';
    var tb=document.createElement('tbody');
    a.forEach(function(r,i){var x=q[r.s],tr=document.createElement('tr'),P=x&&x.price,lab={cost:'我持有',order:'掛單',sold:'已出場'}[r.k]||r.k,cur=tw(r.s)?1:fx;
     td(tr,r.s,'');td(tr,lab,'');td(tr,f(r.p,2));td(tr,f(r.n,0));
     if(!P){var e=td(tr,'找不到報價','muted');e.colSpan=6;}
     else{if(x.t>ts)ts=x.t;td(tr,f(P,2)+(x.chg!=null?'（'+sg(x.chg,1)+'%）':''));var dist=(r.p/P-1)*100;td(tr,sg(dist,2)+'%');
      var sd=x.vol20?x.vol20/100/Math.sqrt(252):null,lt=leftToday(r.s),amt,txt;
      if(r.k==='order'){var p1=touch(P,r.p,sd,lt),p2=touch(P,r.p,sd,lt+1);td(tr,lt>0?pct(p1):'—');td(tr,pct(p2));
        amt=exitNet(r.s,r.n*r.p,set)*cur;tot.order+=amt;td(tr,f(amt,0));txt='成交後實拿（以出場計，已扣費用）';}
      else if(r.k==='cost'){td(tr,'');td(tr,'');amt=r.n*(P-r.p)*cur;tot.cost+=amt;var c=td(tr,sg(amt,0));c.classList.add(amt>=0?'up':'dn');txt='帳面盈虧（未扣出場費用）';}
      else{td(tr,'');td(tr,'');amt=r.n*(r.p-P)*cur;tot.sold+=amt;var c2=td(tr,sg(amt,0));c2.classList.add(amt>=0?'up':'dn');txt=amt>=0?'比現在才出場多拿':'比現在才出場少拿';}
      td(tr,txt,'small muted');}
     var b=document.createElement('button');b.type='button';b.className='wlx';b.textContent='✕';b.setAttribute('aria-label','remove');
     b.addEventListener('click',function(){var z=rows();z.splice(i,1);put(K,z);draw();});var tdb=document.createElement('td');tdb.appendChild(b);tr.appendChild(tdb);tb.appendChild(tr);});
    [['cost','合計：我持有的帳面盈虧'],['order','合計：掛單全部成交實拿'],['sold','合計：已出場比現在多拿（負數＝少拿）']].forEach(function(k){if(!a.some(function(r){return r.k===k[0];}))return;
     var tr=document.createElement('tr');tr.className='tot';var e=td(tr,k[1],'');e.colSpan=8;var v=td(tr,(k[0]==='order'?f(tot[k[0]],0):sg(tot[k[0]],0)));if(k[0]!=='order')v.classList.add(tot[k[0]]>=0?'up':'dn');td(tr,'');td(tr,'');tb.appendChild(tr);});
    t.appendChild(tb);box.textContent='';box.appendChild(t);
    var st=document.getElementById('trstamp');if(st)st.textContent='報價時間：台北 '+hm(ts)+'　美元兌台幣 '+f(fx,3)+(q['TWD=X']?'（即時）':'（你填的備用匯率）')+'　每 '+(POLL/1000)+' 秒更新';
   }).catch(function(){if(my===seq)box.innerHTML='<p class="small muted">報價來源暫時取不到，稍後再試（這個功能只在 Cloudflare 版網址可用）。</p>';});}
 var fm=document.getElementById('trf');if(fm)fm.addEventListener('submit',function(e){e.preventDefault();
   var s=(document.getElementById('trs').value||'').trim().toUpperCase(),k=document.getElementById('trk').value,p=parseFloat(document.getElementById('trp').value),n=parseFloat(document.getElementById('trn').value);
   if(!/^[A-Z0-9^=.\-]{1,15}$/.test(s)||!(p>0)||!(n>0))return;var a=rows();if(a.length<40){a.push({s:s,k:k,p:p,n:n});put(K,a);}
   ['trs','trp','trn'].forEach(function(id){document.getElementById(id).value='';});draw();});
 var fe=document.getElementById('trfee'),fx=document.getElementById('trfx'),s0=sets();if(fe){fe.value=s0.fee;fe.addEventListener('change',function(){var s=get(KS,{});s.fee=fe.value;put(KS,s);draw();});}
 if(fx){fx.value=s0.fx;fx.addEventListener('change',function(){var s=get(KS,{});s.fx=fx.value;put(KS,s);draw();});}
 setTimeout(draw,1200);setInterval(function(){if(!document.hidden)draw();},POLL);
})();
"""
JS = (_JS.replace("__POLL__", str(POLL_S)).replace("__FUS__", str(FEE_US)).replace("__FTW__", str(FEE_TW)).replace("__TTW__", str(TAX_TW)))
