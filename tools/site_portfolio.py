"""我的持股 tab: the visitor's OWN holdings and cash → today's P&L, market value, unrealized P&L and total assets.

Privacy by construction: the server only publishes public data (FX + quotes for the tracked universe; whole-market
prices are the existing market/{us,tw,hk}.json files).  Holdings are typed in the browser, kept in that browser's
localStorage, and every calculation runs client-side.  Nothing about the holdings is ever sent anywhere — the only
network requests are GETs of those public price files, without any query string."""
from __future__ import annotations

import json
import math
from typing import Dict

from tools.sitekit import T, esc
try:
    from wsb.config import SETTINGS
except Exception:  # noqa: BLE001
    SETTINGS = {}

HKD_PEG = 7.8          # HKD is pegged to the USD inside 7.75–7.85


def _fx(eng) -> Dict[str, float]:
    q = eng.market.q("TWD=X") or {}
    usdtwd = q.get("price") if q.get("price") and q["price"] == q["price"] else None
    if not usdtwd:
        s = eng.market.series("TWD=X")
        usdtwd = float(s.iloc[-1]) if len(s) else 31.5
    return {"TWD": 1.0, "USD": float(usdtwd), "HKD": float(usdtwd) / HKD_PEG, "asof": q.get("asof") or ""}


def _quotes(eng) -> Dict[str, list]:
    """Hourly quotes for every tracked ticker (indices, ETFs, large caps) — fills the ETF gap of the whole-market files."""
    names = {}
    try:
        from wsb.config import SETTINGS
        names = SETTINGS.names()
    except Exception:  # noqa: BLE001
        pass
    out = {}
    for t, q in (getattr(eng.market, "quotes", None) or {}).items():
        px, ch = q.get("price"), q.get("chg_pct")
        if px is None or (isinstance(px, float) and math.isnan(px)):
            continue
        out[t] = [round(float(px), 4), None if ch is None or ch != ch else round(float(ch), 3), q.get("asof") or "", names.get(t, t)]
    return out


def sec_portfolio(eng) -> str:
    gcid = ((SETTINGS.get("site", {}) or {}).get("google_client_id") or "").strip()
    data = json.dumps({"fx": _fx(eng), "q": _quotes(eng), "gcid": gcid}, ensure_ascii=False,
                      separators=(",", ":")).replace("</", "<\\/")
    priv = T("持股與現金預設只存在「這台裝置的這個瀏覽器」，不會上傳、不在程式碼或 GitHub 裡，別人打開同一個網址看不到。"
             "按「用 Google 同步」後，資料會存到你自己 Google 雲端硬碟裡一個只有本網頁能讀的隱藏資料夾，手機和電腦登入同一個 Google 帳號就會自動同步；"
             "這個網站的伺服器（GitHub）從頭到尾碰不到你的持股。也可以用「匯出／匯入」手動搬。",
             "Holdings and cash stay in THIS browser by default — never uploaded, not in the code or on GitHub; nobody else opening the "
             "URL can see them. 'Sync with Google' stores them in a hidden app-only folder of YOUR Google Drive, so every device signed "
             "in to the same Google account stays in sync; GitHub never sees them. Export / Import still works for manual moves.")
    note = T("價格跟著本站每小時更新（免費報價約延遲 15 分鐘，非逐筆即時）；今日損益＝股數 ×（現價 − 昨收）。台股輸入數字代號即可（例 2330），"
             "港股請寫 0700.HK；美股直接輸入代號。新台幣合計用網站的美元兌台幣匯率，港幣以聯繫匯率 7.8 估算。找不到報價的代號可以手動輸入價格。",
             "Prices follow the hourly site build (~15 min delayed, not tick-by-tick); today's P&L = shares × (price − previous close). "
             "Taiwan: type the number (e.g. 2330); Hong Kong: 0700.HK; US: the ticker. TWD totals use the site's USD/TWD rate; HKD via the "
             "7.8 peg (approximate). If a ticker has no price you can type one in manually.")
    return f'''<section class="card wide" id="pfbox"><h2>{T("我的持股與總資產", "My holdings & total assets")}</h2>
<p class="sub">{priv}</p>
<div class="pfsync" id="pfsync"></div>
<div class="pfsum" id="pfsum"></div>
<div class="pfwrap"><table class="pft" id="pft"><thead><tr>
<th>{T("代號", "Ticker")}</th><th>{T("名稱", "Name")}</th><th class="r">{T("股數", "Shares")}</th><th class="r">{T("現價", "Price")}</th>
<th class="r">{T("今日", "Today")}</th><th class="r">{T("今日損益", "Today P&L")}</th><th class="r">{T("市值", "Value")}</th>
<th class="r">{T("市值（台幣）", "Value (TWD)")}</th><th class="r">{T("成本", "Cost")}</th><th class="r">{T("帳面損益", "Unrealized")}</th>
<th class="r">{T("報酬", "Return")}</th><th class="r">{T("權重", "Weight")}</th><th></th></tr></thead><tbody></tbody></table></div>
<div class="pfforms">
<form id="pfadd" class="pfrow" autocomplete="off"><b>{T("新增／更新持股", "Add / update a holding")}</b>
<input name="s" placeholder="NVDA / 2330 / 0700.HK" required maxlength="16" aria-label="ticker">
<input name="n" type="number" step="any" min="0" placeholder="{esc("股數")}" required aria-label="shares">
<input name="c" type="number" step="any" min="0" placeholder="{esc("每股成本（選填）")}" aria-label="cost per share">
<button class="btn" type="submit">{T("儲存", "Save")}</button></form>
<form id="pfcash" class="pfrow" autocomplete="off"><b>{T("現金", "Cash")}</b>
<select name="cur" aria-label="currency"><option>TWD</option><option>USD</option><option>HKD</option></select>
<input name="a" type="number" step="any" placeholder="{esc("金額（0 = 刪除）")}" required aria-label="amount">
<button class="btn" type="submit">{T("儲存", "Save")}</button></form>
<details class="pfbulk"><summary>{T("一次貼上多筆", "Paste many at once")}</summary>
<p class="small muted">{T("每行一筆：代號 股數 成本（成本可省略），用空白或逗號分隔，例如：", "One per line: ticker shares cost (cost optional), e.g.:")}<code>NVDA 15 50</code> · <code>2330 1000 600</code> · <code>0700.HK 200</code></p>
<textarea id="pfpaste" rows="5" spellcheck="false"></textarea><button class="btn" type="button" id="pfpastebtn">{T("加入", "Add")}</button></details>
<div class="pfrow"><button class="btn" type="button" id="pfexp">{T("匯出備份", "Export")}</button>
<label class="btn" for="pfimp">{T("匯入", "Import")}</label><input id="pfimp" type="file" accept="application/json,.json" hidden>
<button class="btn" type="button" id="pfclr">{T("清除全部", "Clear all")}</button><span class="small muted" id="pfmsg" role="status"></span></div>
</div>
<p class="note">{note}</p>
<script type="application/json" id="pf-data">{data}</script></section>'''


CSS = """
.pfsum{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:10px 0}@media(max-width:520px){.pfsum{grid-template-columns:1fr 1fr}.pfk .v{font-size:18px}.pfk.big{grid-column:span 2}.pfk.big .v{font-size:26px}}
.pfk{background:var(--card2);border:1px solid var(--bd);border-radius:10px;padding:10px 12px}.pfk .v{font-size:24px;font-weight:800}
.pfk .s{font-size:12px;color:var(--mu)}.pfk.big .v{font-size:30px}
.pfwrap{overflow-x:auto}table.pft{width:100%;border-collapse:collapse;font-size:13px}
table.pft th,table.pft td{padding:6px 8px;border-bottom:1px solid var(--bd);white-space:nowrap}table.pft .r{text-align:right}
table.pft tfoot td{font-weight:700;border-top:2px solid var(--bd)}table.pft input{width:80px;background:var(--card2);border:1px solid var(--bd);color:var(--tx);border-radius:5px;padding:2px 4px}
.pfforms{display:flex;flex-direction:column;gap:10px;margin-top:12px}.pfrow{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.pfrow input,.pfrow select,.pfbulk textarea{background:var(--card2);border:1px solid var(--bd);color:var(--tx);border-radius:6px;padding:6px 8px;font:inherit;font-size:14px}
.pfrow input{width:150px}.pfbulk textarea{width:100%;max-width:520px;display:block;margin:6px 0}.pfx{background:none;border:0;color:var(--mu);cursor:pointer;font-size:15px}
.pfx:hover{color:var(--dn)}.pfwarn{color:var(--warn)}
.pfsync{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:4px 0 8px;font-size:13px}.pfsync .ok{color:var(--up)}.pfsync .err{color:var(--dn)}
.btn.g{border-color:var(--ac);color:var(--ac)}
"""

JS = r"""
(function(){var box=document.getElementById('pfbox');if(!box)return;
var KEY='wss_portfolio_v1',PUB=JSON.parse(document.getElementById('pf-data').textContent),FX=PUB.fx,Q=PUB.q,MK={};
var en=function(){return document.documentElement.lang==='en';};
function L(zh,e){var s=document.createElement('span');s.dataset.en=e;s.dataset.zh=zh;s.textContent=en()?e:zh;return s;}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
function get(){try{var d=JSON.parse(localStorage.getItem(KEY)||'null');if(d&&Array.isArray(d.h))return d;}catch(e){}return {v:1,h:[],cash:[]};}
function put(d){try{localStorage.setItem(KEY,JSON.stringify(d));return true;}catch(e){msg(['無法儲存（瀏覽器封鎖了本機儲存）','Cannot save (browser storage blocked)']);return false;}}
function msg(m){var x=document.getElementById('pfmsg');x.textContent='';if(m)x.appendChild(L(m[0],m[1]));}
function num(v,d){return (v==null||!isFinite(v))?'—':Number(v).toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d});}
function sgn(v,d,pct){if(v==null||!isFinite(v))return '—';return (v>0?'+':'')+num(v,d)+(pct?'%':'');}
function cl(v){return v>0?'up':(v<0?'dn':'');}
function norm(raw){var x=String(raw||'').trim().toUpperCase().replace(/\s+/g,'');if(!x||x.length>16||!/^[A-Z0-9.\-^=]+$/.test(x))return null;
 var m;if(/^\d{4,6}[A-Z]?$/.test(x))return {key:x,mk:'tw',cands:[x+'.TW',x+'.TWO']};
 if((m=x.match(/^(\d{4,6}[A-Z]?)\.(TW|TWO)$/)))return {key:x,mk:'tw',cands:[x]};
 if((m=x.match(/^(\d{1,5})\.HK$/))){var c=('0000'+m[1]).slice(-4);return {key:c+'.HK',mk:'hk',cands:[c+'.HK',m[1]+'.HK']};}
 return {key:x,mk:'us',cands:[x,x.replace('.','-')]};}
function cur(mk){return mk==='tw'?'TWD':(mk==='hk'?'HKD':'USD');}
function loadMk(mk){if(MK[mk]!==undefined)return MK[mk];MK[mk]=fetch('market/'+mk+'.json',{cache:'no-cache'}).then(function(r){if(!r.ok)throw 0;return r.json();})
 .then(function(d){var c=d.cols,iS=c.indexOf('sym'),iN=c.indexOf('name'),iP=c.indexOf('px'),iR=c.indexOf('r1d'),map={};
  d.rows.forEach(function(a){map[a[iS]]={px:a[iP],ch:a[iR],name:a[iN],asof:d.asof};});return {asof:d.asof,map:map};}).catch(function(){return null;});return MK[mk];}
function price(h,fm){var n=norm(h.s);if(!n)return null;for(var i=0;i<n.cands.length;i++){var s=n.cands[i],q=Q[s],f=fm&&fm.map[s];
  if(q&&q[0]!=null&&(!f||(q[2]||'')>=(f.asof||'')))return {sym:s,px:q[0],ch:q[1],asof:q[2],name:q[3],src:'q'};
  if(f&&f.px!=null)return {sym:s,px:f.px,ch:f.ch,asof:f.asof,name:f.name,src:'fm'};}
 if(h.p>0)return {sym:n.key,px:h.p,ch:null,asof:'',name:'',src:'manual'};return null;}
function ph(){var P={n:['股數','Shares'],c:['每股成本（選填）','Cost per share (optional)'],a:['金額（0 = 刪除）','Amount (0 = delete)']};
 ['pfadd','pfcash'].forEach(function(id){var f=document.getElementById(id);Object.keys(P).forEach(function(k){if(f[k])f[k].placeholder=P[k][en()?1:0];});});}
// ---------------------------------------------------------------- Google Drive sync (appDataFolder: only this page + this account can read it)
var G={cid:PUB.gcid||'',tok:null,exp:0,fid:null,busy:false,on:false,email:''};
var GKEY='wss_portfolio_gsync';
function gmsg(zh,e,cls){var s=document.getElementById('pfsync');if(!s)return;var st=s.querySelector('.st');if(!st){st=el('span','st');s.appendChild(st);}st.className='st '+(cls||'');st.textContent='';st.appendChild(L(zh,e));}
function gbar(){var s=document.getElementById('pfsync');if(!s)return;s.textContent='';if(!G.cid){s.appendChild(L('（跨裝置 Google 同步尚未設定：請在 settings.yaml 的 site.google_client_id 填入 OAuth 用戶端 ID）','(Google sync not configured: set site.google_client_id in settings.yaml)'));s.firstChild.className='muted';return;}
 var b=el('button','btn g');b.type='button';b.appendChild(L(G.on?'立即同步':'用 Google 同步','Sync now'));b.addEventListener('click',function(){gauth(true).then(function(ok){if(ok)gsync();});});s.appendChild(b);
 if(G.on){var o=el('button','btn');o.type='button';o.appendChild(L('停用同步','Stop syncing'));o.addEventListener('click',function(){G.on=false;G.tok=null;try{localStorage.removeItem(GKEY);}catch(e){}gbar();});s.appendChild(o);}
 var st=el('span','st');s.appendChild(st);if(G.on)gmsg('已啟用 Google 同步','Google sync on','ok');}
function gload(){return new Promise(function(res,rej){if(window.google&&google.accounts&&google.accounts.oauth2)return res();var sc=document.createElement('script');sc.src='https://accounts.google.com/gsi/client';sc.async=true;sc.onload=res;sc.onerror=function(){rej(new Error('gsi'));};document.head.appendChild(sc);});}
function gauth(interactive){if(!G.cid)return Promise.resolve(false);if(G.tok&&Date.now()<G.exp-60000)return Promise.resolve(true);
 return gload().then(function(){return new Promise(function(res){var tc=google.accounts.oauth2.initTokenClient({client_id:G.cid,scope:'https://www.googleapis.com/auth/drive.appdata',
  callback:function(r){if(r&&r.access_token){G.tok=r.access_token;G.exp=Date.now()+(r.expires_in||3600)*1000;G.on=true;try{localStorage.setItem(GKEY,'1');}catch(e){}gbar();res(true);}else{gmsg('Google 登入未完成','Google sign-in not completed','err');res(false);}},
  error_callback:function(e){gmsg('Google 登入失敗：'+(e&&e.type||''),'Google sign-in failed: '+(e&&e.type||''),'err');res(false);}});
  tc.requestAccessToken({prompt:interactive?'':''});});}).catch(function(){gmsg('無法載入 Google 登入元件（可能被封鎖）','Cannot load Google sign-in','err');return false;});}
function gfetch(url,opt){opt=opt||{};opt.headers=Object.assign({},opt.headers||{},{Authorization:'Bearer '+G.tok});return fetch(url,opt).then(function(r){if(r.status===401){G.tok=null;throw new Error('401');}if(!r.ok)throw new Error('HTTP '+r.status);return r;});}
function gfind(){return gfetch('https://www.googleapis.com/drive/v3/files?spaces=appDataFolder&fields=files(id,name,modifiedTime)&q='+encodeURIComponent("name='wss_holdings.json'")).then(function(r){return r.json();}).then(function(j){var f=(j.files||[])[0];G.fid=f?f.id:null;return f||null;});}
function gread(){return gfetch('https://www.googleapis.com/drive/v3/files/'+G.fid+'?alt=media').then(function(r){return r.json();});}
function gwrite(d){var body=JSON.stringify(d);if(G.fid)return gfetch('https://www.googleapis.com/upload/drive/v3/files/'+G.fid+'?uploadType=media',{method:'PATCH',headers:{'Content-Type':'application/json'},body:body});
 var bd='-------wss'+Date.now(),meta=JSON.stringify({name:'wss_holdings.json',parents:['appDataFolder']});
 var mp='--'+bd+'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+meta+'\r\n--'+bd+'\r\nContent-Type: application/json\r\n\r\n'+body+'\r\n--'+bd+'--';
 return gfetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',{method:'POST',headers:{'Content-Type':'multipart/related; boundary='+bd},body:mp}).then(function(r){return r.json();}).then(function(j){G.fid=j.id;});}
function gsync(){if(G.busy||!G.on)return;G.busy=true;gmsg('同步中…','Syncing…');
 var local=get();local.updated=local.updated||0;
 gfind().then(function(f){if(!f)return gwrite(local).then(function(){gmsg('已上傳到 Google 雲端硬碟 '+new Date().toLocaleTimeString(),'Uploaded '+new Date().toLocaleTimeString(),'ok');});
  return gread().then(function(remote){remote=remote&&Array.isArray(remote.h)?remote:{v:1,h:[],cash:[],updated:0};
   if((remote.updated||0)>(local.updated||0)){put(remote);render();gmsg('已從 Google 雲端硬碟載入 '+new Date(remote.updated).toLocaleString(),'Loaded from Google Drive '+new Date(remote.updated).toLocaleString(),'ok');}
   else if((local.updated||0)>(remote.updated||0)){return gwrite(local).then(function(){gmsg('已上傳到 Google 雲端硬碟 '+new Date().toLocaleTimeString(),'Uploaded '+new Date().toLocaleTimeString(),'ok');});}
   else gmsg('已同步（無變更）','In sync','ok');});})
 .catch(function(e){gmsg('同步失敗：'+e.message,'Sync failed: '+e.message,'err');if(e.message==='401')G.tok=null;})
 .then(function(){G.busy=false;});}
var _put=put;put=function(d){d.updated=Date.now();var ok=_put(d);if(ok&&G.on){clearTimeout(G._t);G._t=setTimeout(function(){gauth(false).then(function(ok2){if(ok2)gsync();});},800);}return ok;};
try{G.on=!!G.cid&&localStorage.getItem(GKEY)==='1';}catch(e){}
gbar();if(G.on)gauth(false).then(function(ok){if(ok)gsync();});
function render(){ph();var d=get(),need={};d.h.forEach(function(h){var n=norm(h.s);if(n)need[n.mk]=1;});
 var mks=Object.keys(need);Promise.all(mks.map(loadMk)).then(function(res){var FM={};mks.forEach(function(m,i){FM[m]=res[i];});draw(d,FM);});
 if(mks.length&&!document.getElementById('pft').tBodies[0].rows.length)msg(['載入價格中…','Loading prices…']);}
function draw(d,FM){var tb=document.getElementById('pft').tBodies[0];tb.textContent='';var tf=document.getElementById('pft').tFoot;if(tf)tf.remove();
 var rows=[],totV=0,totDay=0,totPrev=0,totCost=0,costV=0,miss=0,dates={};
 d.h.forEach(function(h,i){var n=norm(h.s),mk=n?n.mk:'us',p=price(h,FM[mk]),c=cur(mk),fx=FX[c]||1,r={h:h,i:i,mk:mk,cur:c,p:p};
  if(p){r.v=h.n*p.px;r.vt=r.v*fx;var prev=(p.ch!=null)?p.px/(1+p.ch/100):null;r.day=prev!=null?h.n*(p.px-prev)*fx:null;r.dayc=prev!=null?h.n*(p.px-prev):null;
   totV+=r.vt;if(r.day!=null){totDay+=r.day;totPrev+=r.vt-r.day;}if(h.c>0){r.cost=h.n*h.c;r.un=r.v-r.cost;r.ret=r.un/r.cost*100;totCost+=r.cost*fx;costV+=r.vt;}
   if(p.asof)dates[c]=(dates[c]&&dates[c]>p.asof)?dates[c]:p.asof;}else miss++;rows.push(r);});
 rows.sort(function(a,b){return (b.vt||0)-(a.vt||0);});
 rows.forEach(function(r){var tr=document.createElement('tr'),h=r.h,p=r.p;
  function td(x,c){var t=el('td',c||'r');if(x instanceof Node)t.appendChild(x);else t.textContent=x;tr.appendChild(t);return t;}
  td((p&&p.sym)||h.s,'');td(p?(p.name||''):'','');td(num(h.n,h.n%1?2:0));
  if(p){td(num(p.px,2)+' '+r.cur+(p.src==='manual'?' ✎':''));td(sgn(p.ch,2,true),'r '+cl(p.ch));td(r.dayc!=null?sgn(r.dayc,0):'—','r '+cl(r.dayc));
   td(num(r.v,0));td(num(r.vt,0));td(h.c>0?num(r.cost,0):'—');td(r.un!=null?sgn(r.un,0):'—','r '+cl(r.un));td(r.ret!=null?sgn(r.ret,1,true):'—','r '+cl(r.ret));
   td(totV?num(r.vt/totV*100,1)+'%':'—');}
  else{var t=td('','r pfwarn');t.colSpan=9;t.appendChild(L('找不到報價，請手動輸入價格：','No price found — enter one: '));var inp=el('input');inp.type='number';inp.step='any';inp.min='0';inp.setAttribute('aria-label','manual price');
   inp.addEventListener('change',function(){var dd=get();dd.h[r.i].p=parseFloat(inp.value)||0;put(dd);render();});t.appendChild(inp);}
  var del=el('button','pfx','✕');del.type='button';del.title=en()?'Remove':'刪除';del.addEventListener('click',function(){var dd=get();dd.h.splice(r.i,1);put(dd);render();});td(del,'');
  tb.appendChild(tr);});
 var cashT=0;(d.cash||[]).forEach(function(c){cashT+=c.a*(FX[c.cur]||1);});var tot=totV+cashT,usd=FX.USD||1;
 var S=document.getElementById('pfsum');S.textContent='';
 function k(zh,en_,v,sub,c,big){var x=el('div','pfk'+(big?' big':''));x.appendChild(el('div','s')).appendChild(L(zh,en_));var vv=el('div','v '+(c||''),v);x.appendChild(vv);if(sub)x.appendChild(el('div','s',sub));S.appendChild(x);}
 k('總資產（新台幣）','Total assets (TWD)','NT$ '+num(tot,0),'≈ US$ '+num(tot/usd,0),'',true);
 k('今日損益','Today P&L','NT$ '+sgn(totDay,0),totPrev?sgn(totDay/totPrev*100,2,true):'',cl(totDay));
 k('股票市值','Stocks','NT$ '+num(totV,0),tot?num(totV/tot*100,1)+'%':'');
 k('現金','Cash','NT$ '+num(cashT,0),(d.cash||[]).map(function(c){return c.cur+' '+num(c.a,0);}).join(' · '));
 if(totCost)k('帳面損益（有填成本者）','Unrealized (with cost)','NT$ '+sgn(costV-totCost,0),sgn((costV-totCost)/totCost*100,2,true),cl(costV-totCost));
 var dl=Object.keys(dates).map(function(c){return c+' '+dates[c];}).join(' · ');
 msg(d.h.length||(d.cash||[]).length?[(miss?miss+' 檔找不到報價 · ':'')+'價格日期：'+(dl||'—')+' · 美元兌台幣 '+num(FX.USD,3),(miss?miss+' without price · ':'')+'Prices as of: '+(dl||'—')+' · USD/TWD '+num(FX.USD,3)]
  :['尚未輸入持股：在下方新增，或用「一次貼上多筆」','No holdings yet — add some below or paste many at once']);}
function upsert(d,s,n,c){var k=norm(s);if(!k||!(n>=0))return false;var key=k.key,i=d.h.findIndex(function(h){var x=norm(h.s);return x&&x.key===key;});
 if(n===0){if(i>=0)d.h.splice(i,1);return true;}var row={s:key,n:n,c:(c>0?c:0),p:0};if(i>=0){row.p=d.h[i].p||0;if(!(c>0))row.c=d.h[i].c||0;d.h[i]=row;}else d.h.push(row);return true;}
document.getElementById('pfadd').addEventListener('submit',function(e){e.preventDefault();var f=e.target,d=get();
 if(upsert(d,f.s.value,parseFloat(f.n.value),parseFloat(f.c.value))){put(d);f.reset();render();}else msg(['代號或股數格式不對','Check the ticker / shares']);});
document.getElementById('pfcash').addEventListener('submit',function(e){e.preventDefault();var f=e.target,d=get(),a=parseFloat(f.a.value);if(!isFinite(a))return;
 d.cash=(d.cash||[]).filter(function(c){return c.cur!==f.cur.value;});if(a)d.cash.push({cur:f.cur.value,a:a});put(d);f.a.value='';render();});
document.getElementById('pfpastebtn').addEventListener('click',function(){var d=get(),ok=0,bad=0;
 document.getElementById('pfpaste').value.split(/\r?\n/).forEach(function(line){var p=line.trim().split(/[\s,，\t]+/);if(!p[0])return;
  if(upsert(d,p[0],parseFloat(p[1]),parseFloat(p[2])))ok++;else bad++;});put(d);document.getElementById('pfpaste').value='';render();
 setTimeout(function(){msg(['已加入 '+ok+' 筆'+(bad?'，'+bad+' 行格式不對':''),'Added '+ok+(bad?', '+bad+' lines skipped':'')]);},50);});
document.getElementById('pfexp').addEventListener('click',function(){var b=new Blob([JSON.stringify(get(),null,1)],{type:'application/json'}),a=document.createElement('a');
 a.href=URL.createObjectURL(b);a.download='my_holdings_'+new Date().toISOString().slice(0,10)+'.json';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},500);});
document.getElementById('pfimp').addEventListener('change',function(e){var f=e.target.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){try{var d=JSON.parse(rd.result);
  if(!d||!Array.isArray(d.h))throw 0;var clean={v:1,h:[],cash:[]};d.h.forEach(function(h){if(h&&norm(h.s)&&h.n>=0)clean.h.push({s:norm(h.s).key,n:+h.n,c:+h.c>0?+h.c:0,p:+h.p>0?+h.p:0});});
  (d.cash||[]).forEach(function(c){if(c&&['TWD','USD','HKD'].indexOf(c.cur)>=0&&isFinite(+c.a))clean.cash.push({cur:c.cur,a:+c.a});});
  put(clean);render();setTimeout(function(){msg(['已匯入 '+clean.h.length+' 檔持股','Imported '+clean.h.length+' holdings']);},50);}catch(x){msg(['檔案格式不對','Invalid file']);}};rd.readAsText(f);e.target.value='';});
document.getElementById('pfclr').addEventListener('click',function(){if(confirm(en()?'Delete all holdings and cash stored in this browser?':'確定刪除這個瀏覽器裡的所有持股與現金？（建議先匯出備份）')){try{localStorage.removeItem(KEY);}catch(e){}render();}});
document.getElementById('langBtn')&&document.getElementById('langBtn').addEventListener('click',function(){setTimeout(render,0);});
render();})();
"""
