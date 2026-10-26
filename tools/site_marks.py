"""全市場體檢標記 (AI 視角看進場 page): every US / Taiwan / Hong Kong stock in the full-market scan with neutral marks —
trend, distance from the 52-week high, RSI, volatility — and where its P/E (or P/B) sits in its own five-year history,
with the prices today's earnings would imply at its historical low / middle / high multiples.
Data is loaded in the browser from market/<mk>.json only when the reader opens it.  Description, not recommendation."""
from __future__ import annotations

from tools.sitekit import T, card

NOTE = ("標記全部由公開數據自動計算，不挑股、不排名好壞。趨勢：現價在 200 日線之上而且 12 個月動能為正＝多頭，兩者都相反＝空頭，其餘＝盤整。"
        "波動：近一年日報酬的年化波動，在同一個市場裡分成低／中／高三等份。"
        "歷史估值：台股用證交所／櫃買中心每天公布的本益比（虧損時改用股價淨值比），每月取一筆、最多 5 年；"
        "美股用 SEC 財報的近四季淨利與當時的流通股數，加上當時的股價，每季一筆、最多 5 年；港股沒有免費的歷史估值資料，所以不顯示。"
        "「歷史本益比區間」＝如果今天的獲利不變，本益比回到它自己過去 5 年的第 25／50／75 百分位時，換算出來的股價；"
        "它描述的是「現在的倍數在自己歷史的哪裡」，不是對未來股價的預測，也不是建議的交易價位。獲利會變、倍數也可能長期改變（產業轉型、成長加速或停滯）。"
        "不是投資建議；本站作者不是持牌投資顧問。")

JS = r"""
(function(){var box=document.getElementById('mkbox');if(!box)return;
var CACHE={},cur='us',shown=200,sortK='vpct',sortD=1,ix={};
var el=function(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;};
var st=box.querySelector('.mkst'),body=box.querySelector('.mkbody'),q=box.querySelector('.mkq'),ft=box.querySelector('.mkt'),fv=box.querySelector('.mkv'),fi=box.querySelector('.mki');
function g(r,k){var i=ix[k];return i==null?null:r[i];}
function fmt(v,d){return v==null?'—':(+v).toLocaleString(undefined,{maximumFractionDigits:d,minimumFractionDigits:d});}
function vlab(p){return p==null?'無資料':p<=25?'歷史低檔':p>=75?'歷史高檔':'歷史中段';}
function load(mk){cur=mk;shown=200;box.querySelectorAll('[data-mk]').forEach(function(b){b.classList.toggle('on',b.dataset.mk===mk);});
 if(CACHE[mk]){draw();return;}st.textContent='載入中…';
 fetch('market/'+mk+'.json',{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){CACHE[mk]=d;draw();})
 .catch(function(){st.textContent='這個市場的資料暫時取不到';body.textContent='';});}
function draw(){var d=CACHE[cur];if(!d)return;ix={};d.cols.forEach(function(c,i){ix[c]=i;});
 var inds={};d.rows.forEach(function(r){var v=g(r,'ind');if(v)inds[v]=1;});var keep=fi.value;fi.textContent='';fi.appendChild(el('option','', '全部產業')).value='';
 Object.keys(inds).sort().forEach(function(k){var o=el('option','',k);o.value=k;fi.appendChild(o);});fi.value=inds[keep]?keep:'';
 var s=(q.value||'').trim().toLowerCase(),t=ft.value,v=fv.value,ind=fi.value;
 var rows=d.rows.filter(function(r){if(s&&(String(g(r,'code')||'')+' '+(g(r,'name')||'')).toLowerCase().indexOf(s)<0)return false;
  if(t&&g(r,'lt')!==t)return false;if(ind&&g(r,'ind')!==ind)return false;if(v){var p=g(r,'vpct');if(v==='none'?p!=null:vlab(p)!==v)return false;}return true;});
 rows.sort(function(a,b){var x=g(a,sortK),y=g(b,sortK);if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return -1;return (x>y?1:x<y?-1:0)*sortD;});
 var withV=d.rows.filter(function(r){return g(r,'vpct')!=null;}).length;
 st.textContent='共 '+d.rows.length.toLocaleString()+' 檔，符合 '+rows.length.toLocaleString()+' 檔；有歷史估值的 '+withV.toLocaleString()+' 檔（資料日 '+(d.asof||'—')+'）';
 body.textContent='';var wrap=el('div','scroll'),tb=el('table','mini mkt2'),th=el('thead'),tr=el('tr');
 [['code','代號'],['name','名稱'],['ind','產業'],['px','現價'],['lt','趨勢'],['ldd','離 52 週高點'],['rsi','RSI'],['lv','波動'],['vpct','估值在自己 5 年的位置'],['vp25','歷史倍數低檔→股價'],['vp50','中位→股價'],['vp75','高檔→股價']]
 .forEach(function(c){var h=el('th',c[0]==='name'||c[0]==='ind'||c[0]==='code'?'':'r',c[1]+(sortK===c[0]?(sortD>0?' ▲':' ▼'):''));h.style.cursor='pointer';
  h.addEventListener('click',function(){if(sortK===c[0])sortD=-sortD;else{sortK=c[0];sortD=1;}draw();});tr.appendChild(h);});
 th.appendChild(tr);tb.appendChild(th);var tbd=el('tbody');
 rows.slice(0,shown).forEach(function(r){var x=el('tr');var px=g(r,'px');
  x.appendChild(el('td','',g(r,'code')));x.appendChild(el('td','',g(r,'name')));x.appendChild(el('td','small muted',g(r,'ind')));
  x.appendChild(el('td','r',fmt(px,2)));
  var lt=g(r,'lt');x.appendChild(el('td','r '+(lt==='多頭'?'up':lt==='空頭'?'dn':''),lt||'—'));
  var dd=g(r,'ldd');x.appendChild(el('td','r '+(dd!=null&&dd<=-30?'dn':''),dd==null?'—':fmt(dd,1)+'%'));
  var rs=g(r,'rsi'),lr=g(r,'lr');x.appendChild(el('td','r',rs==null?'—':fmt(rs,0)+(lr&&lr!=='中性'?' '+lr:'')));
  x.appendChild(el('td','r',g(r,'lv')||'—'));
  var p=g(r,'vpct'),vm=g(r,'vm');var c=el('td','r');if(p==null){c.textContent='—';c.className='r muted';}else{c.appendChild(el('b','',vlab(p)));
   c.appendChild(el('div','small muted',(vm||'')+' '+fmt(g(r,'vnow'),1)+'・第 '+fmt(p,0)+' 百分位'));}x.appendChild(c);
  ['vp25','vp50','vp75'].forEach(function(k){var v=g(r,k);var td=el('td','r',v==null?'—':fmt(v,2));if(v!=null&&px)td.title='比現價 '+((v/px-1)*100).toFixed(0)+'%';x.appendChild(td);});
  tbd.appendChild(x);});
 tb.appendChild(tbd);wrap.appendChild(tb);body.appendChild(wrap);
 if(rows.length>shown){var mb=el('button','btn','再顯示 200 檔（還有 '+(rows.length-shown).toLocaleString()+' 檔）');mb.type='button';mb.addEventListener('click',function(){shown+=200;draw();});body.appendChild(mb);}}
box.querySelectorAll('[data-mk]').forEach(function(b){b.addEventListener('click',function(){load(b.dataset.mk);});});
[q,ft,fv,fi].forEach(function(e){e.addEventListener(e===q?'input':'change',function(){shown=200;draw();});});
box.querySelector('.mkload').addEventListener('click',function(){this.hidden=true;load(cur);});
})();
"""


def sec_marks(eng) -> str:
    btns = "".join(f'<button class="tab{" on" if k == "us" else ""}" data-mk="{k}" type="button">{T(z, e)}</button>'
                   for k, z, e in (("us", "美股（約 2,500 檔）", "US"), ("tw", "台股（上市＋上櫃）", "Taiwan"), ("hk", "港股（主板）", "Hong Kong")))
    ctl = ('<input class="btn mkq" type="search" placeholder="搜尋代號／名稱" data-en-ph="Search" style="min-width:140px">'
           '<select class="btn mkt"><option value="">趨勢：全部</option><option value="多頭">多頭</option><option value="盤整">盤整</option><option value="空頭">空頭</option></select>'
           '<select class="btn mkv"><option value="">估值位置：全部</option><option value="歷史低檔">在自己歷史的低檔</option><option value="歷史中段">中段</option>'
           '<option value="歷史高檔">在自己歷史的高檔</option><option value="none">無歷史估值資料</option></select>'
           '<select class="btn mki"><option value="">全部產業</option></select>')
    lead = T("一句話看懂：美股、台股、港股每一檔都標上趨勢、離高點多遠、RSI、波動，以及「現在的本益比在它自己過去 5 年的哪個位置」；"
             "點欄位名稱可以排序，例如找「估值在自己歷史低檔＋趨勢多頭」的股票。這是體檢標記，不是推薦清單。", "")
    body = (f'<p class="rimp big2"><b>{lead}</b></p><div id="mkbox"><div class="tabs">{btns}</div>'
            f'<div class="fmctl">{ctl}<button class="btn mkload" type="button">{T("載入全市場資料", "Load")}</button>'
            f'<span class="muted small mkst"></span></div><div class="mkbody"></div></div>'
            f'<details class="sgx"><summary>{T("標記怎麼算、歷史估值區間是什麼", "Method")}</summary><p class="note">{T(NOTE, "")}</p></details>')
    return card("全市場體檢標記：美股／台股／港股每一檔", "Every stock: neutral check-up marks", body, "wide")


CSS = ".mkt2 td{vertical-align:top}#mkbox .fmctl{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0}"
