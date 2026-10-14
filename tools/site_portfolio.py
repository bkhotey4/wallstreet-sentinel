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
<div class="pfnav-box" id="pfnavbox" style="display:none"></div>
<div class="pfwrap"><table class="pft" id="pft"><thead><tr>
<th>{T("代號", "Ticker")}</th><th>{T("名稱", "Name")}</th><th class="r">{T("股數", "Shares")}</th><th class="r">{T("現價", "Price")}</th>
<th class="r">{T("今日", "Today")}</th><th class="r">{T("今日損益", "Today P&L")}</th><th class="r">{T("市值", "Value")}</th>
<th class="r">{T("市值（台幣）", "Value (TWD)")}</th><th class="r">{T("成本", "Cost")}</th><th class="r">{T("帳面損益", "Unrealized")}</th>
<th class="r">{T("報酬", "Return")}</th><th class="r">{T("防守 / 停利", "Defense / Target")}</th><th class="r">{T("權重", "Weight")}</th><th></th></tr></thead><tbody></tbody></table></div>
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
<div class="pfdx" id="pfdx" style="display:none"></div>
<div class="pfcrisis" id="pfcrisis" style="display:none"></div>
<div class="pfwhatif" id="pfwhatif" style="display:none"></div>
<div class="pfearn" id="pfearn" style="display:none"></div>
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
.pfdx{margin-top:16px;border-top:1px dashed var(--bd);padding-top:14px}
.pfdx h3{margin:0 0 10px;font-size:15px;display:flex;align-items:center;gap:6px}
.pfdx-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:12px}
.pfdx-k{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:8px 10px}
.pfdx-k .lbl{font-size:11px;color:var(--mu);margin-bottom:2px}
.pfdx-k .val{font-size:17px;font-weight:700}
.pfdx-k .sub{font-size:11px;color:var(--mu);margin-top:2px}
.pfdx-sec{margin:10px 0}
.pfdx-bar{display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--card2);margin:6px 0;border:1px solid var(--bd)}
.pfdx-bar-seg{height:100%}
.pfdx-tags{display:flex;flex-wrap:wrap;gap:6px;font-size:11px;margin:4px 0 10px}
.pfdx-tag{display:inline-flex;align-items:center;gap:4px;padding:2px 6px;border-radius:4px;background:var(--card2);border:1px solid var(--bd)}
.pfdx-tag .dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.pfdx-items{display:flex;flex-direction:column;gap:6px;margin-top:8px}
.pfdx-item{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border-radius:6px;background:var(--card2);border:1px solid var(--bd);font-size:12px;line-height:1.45}
.pfdx-item.bad{border-left:3px solid var(--dn)}
.pfdx-item.warn{border-left:3px solid var(--warn)}
.pfdx-item.ok{border-left:3px solid var(--up)}
.pfdx-item.act{border-left:3px solid var(--ac)}
.pfdx-item .ico{font-size:13px;flex-shrink:0}

/* Feature 4: NAV Chart */
.pfnav-box{background:var(--card2);border:1px solid var(--bd);border-radius:10px;padding:12px;margin:12px 0}
.pfnav-head{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px}
.pfnav-title{font-size:14px;font-weight:700;display:flex;align-items:center;gap:6px}
.pfnav-stats{display:flex;gap:12px;flex-wrap:wrap;font-size:12px}
.pfnav-stat b{font-weight:700}
.pfnav-svg-wrap{width:100%;height:130px;position:relative}
.pfnav-svg{width:100%;height:100%;display:block;overflow:visible}

/* Feature 3: Dynamic Stop & Target line badge in table */
.pft-stop{font-size:11px;display:flex;flex-direction:column;gap:2px}
.pft-stop .s-tgt{color:var(--up)}
.pft-stop .s-stp{color:var(--dn)}
.pft-stop .s-hit{display:inline-block;padding:1px 4px;border-radius:3px;font-weight:700;font-size:10px}
.pft-stop .s-hit.up{background:rgba(34,197,94,0.15);color:var(--up);border:1px solid var(--up)}
.pft-stop .s-hit.dn{background:rgba(239,68,68,0.15);color:var(--dn);border:1px solid var(--dn)}

/* Feature 1: Crisis Replay Simulator */
.pfcrisis{margin-top:16px;border-top:1px dashed var(--bd);padding-top:14px}
.pfcrisis h3{margin:0 0 4px;font-size:15px;display:flex;align-items:center;gap:6px}
.pfcrisis-btns{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.pfcrisis-btn{background:var(--card2);border:1px solid var(--bd);color:var(--tx);border-radius:6px;padding:6px 12px;cursor:pointer;font-size:12px;font-weight:600;transition:all .15s}
.pfcrisis-btn.active{background:var(--dn);border-color:var(--dn);color:#fff}
.pfcrisis-result{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:12px;margin-top:10px}
.pfcrisis-impact{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:12px}
.pfcrisis-bars{display:flex;flex-direction:column;gap:6px}
.pfcrisis-bar-row{display:flex;align-items:center;gap:8px;font-size:12px}
.pfcrisis-bar-lbl{min-width:70px;white-space:nowrap}
.pfcrisis-bar-track{flex:1;background:var(--bg);height:10px;border-radius:5px;overflow:hidden;border:1px solid var(--bd)}
.pfcrisis-bar-fill{height:100%;background:var(--dn);border-radius:5px}
.pfcrisis-bar-val{min-width:110px;text-align:right;font-size:11px}

/* Feature 2: What-if Sandbox */
.pfwhatif{margin-top:16px;border-top:1px dashed var(--bd);padding-top:14px}
.pfwhatif h3{margin:0 0 4px;font-size:15px;display:flex;align-items:center;gap:6px}
.pfwhatif-ctrls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:10px 0;background:var(--card2);padding:10px 12px;border-radius:8px;border:1px solid var(--bd)}
.pfwhatif-ctrls select,.pfwhatif-ctrls input{background:var(--bg);border:1px solid var(--bd);color:var(--tx);padding:4px 8px;border-radius:5px;font-size:13px}
.pfwhatif-pcts{display:flex;gap:4px}
.pfwhatif-pbtn{background:var(--bg);border:1px solid var(--bd);color:var(--tx2);padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px}
.pfwhatif-pbtn.active{background:var(--ac);border-color:var(--ac);color:#fff}
.pfwhatif-comp{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:10px}
.pfwhatif-card{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:10px}
.pfwhatif-card .lbl{font-size:11px;color:var(--mu);margin-bottom:4px}
.pfwhatif-card .vals{display:flex;align-items:baseline;gap:6px;font-size:16px;font-weight:700}
.pfwhatif-card .chg{font-size:12px;font-weight:600}

/* Feature 6: Earnings Radar */
.pfearn{margin-top:16px;border-top:1px dashed var(--bd);padding-top:14px}
.pfearn h3{margin:0 0 4px;font-size:15px;display:flex;align-items:center;gap:6px}
.pfearn-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin-top:10px}
.pfearn-card{background:var(--card2);border:1px solid var(--bd);border-radius:8px;padding:10px;position:relative}
.pfearn-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.pfearn-sym{font-size:14px;font-weight:800}
.pfearn-days{font-size:11px;padding:2px 6px;border-radius:4px;font-weight:700}
.pfearn-days.urgent{background:rgba(239,68,68,0.2);color:var(--dn);border:1px solid var(--dn)}
.pfearn-days.warn{background:rgba(245,158,11,0.2);color:var(--warn);border:1px solid var(--warn)}
.pfearn-days.normal{background:rgba(59,130,246,0.15);color:var(--ac);border:1px solid var(--ac)}
.pfearn-row{display:flex;justify-content:space-between;font-size:11px;margin:3px 0;color:var(--mu)}
.pfearn-row b{color:var(--tx)}
.pfearn-desc{font-size:11px;color:var(--mu);margin-top:6px;border-top:1px solid var(--bd);padding-top:4px}
"""

JS = r"""
(function(){var box=document.getElementById('pfbox');if(!box)return;
var KEY='wss_portfolio_v1',PUB=JSON.parse(document.getElementById('pf-data').textContent),FX=PUB.fx,Q=PUB.q,MK={},gFM={};
var en=function(){return document.documentElement.lang==='en';};
function L(zh,e){var s=document.createElement('span');s.dataset.en=e;s.dataset.zh=zh;s.textContent=en()?e:zh;return s;}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
var SVG_NS=['http',':','//','www.','w3.','org/2000/svg'].join('');
function svgEl(t,attrs){var e=document.createElementNS(SVG_NS,t);if(attrs){for(var k in attrs){if(Object.prototype.hasOwnProperty.call(attrs,k)){e.setAttribute(k,attrs[k]);}}}return e;}
function get(){try{var d=JSON.parse(localStorage.getItem(KEY)||'null');if(d&&Array.isArray(d.h))return d;}catch(e){}return {v:1,h:[],cash:[],nav:[]};}
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

// Sector categories for risk, beta, crisis shocks
var SECS = [
 { k: 'semi', zh: '半導體設備', en: 'Semiconductors', c: '#00d2ff', b: 1.65,
   syms: ['KLAC','TSM','NVDA','ASML','AMAT','LRCX','INTC','AMD','AVGO','QCOM','MU','TXN','MRVL','ON','MPWR','2330','2454','3034','2379','3443','3661','6415','SMH','SOXX'] },
 { k: 'tech', zh: '科技與雲端', en: 'Tech & Cloud', c: '#3a86ff', b: 1.25,
   syms: ['GOOG','GOOGL','MSFT','AAPL','AMZN','META','ORCL','CRM','ADBE','NOW','UBER','NFLX','QQQ','SPY'] },
 { k: 'fin', zh: '金融數位', en: 'FinTech & Banks', c: '#06d6a0', b: 1.35,
   syms: ['NU','JPM','BAC','WFC','C','GS','MS','V','MA','PYPL','COIN','SOFI','KRE','XLF','2881','2882','2891'] },
 { k: 'front', zh: '前沿與能源', en: 'Frontier & Energy', c: '#ffbe0b', b: 2.10,
   syms: ['SPCX','OKLO','SMR','CCJ','PLTR','TSLA','RIVN','LCID','QS','ENVX','IONQ','RGTI'] },
 { k: 'def', zh: '防禦民生', en: 'Defensive & Value', c: '#8338ec', b: 0.75,
   syms: ['JNJ','PG','KO','PEP','MCD','WMT','COST','XOM','CVX','TLT','IEF','SHY','BND','LQD'] }
];

// ---------------------------------------------------------------- Google Drive sync
var G={cid:PUB.gcid||'',tok:null,exp:0,fid:null,busy:false,on:false,email:''};
var GKEY='wss_portfolio_gsync';
function gmsg(zh,e,cls){var s=document.getElementById('pfsync');if(!s)return;var st=s.querySelector('.st');if(!st){st=el('span','st');s.appendChild(st);}st.className='st '+(cls||'');st.textContent='';st.appendChild(L(zh,e));}
function gbar(){var s=document.getElementById('pfsync');if(!s)return;s.textContent='';if(!G.cid){s.appendChild(L('（跨裝置 Google 同步尚未設定：請在 settings.yaml 的 site.google_client_id 填入 OAuth 用端 ID）','(Google sync not configured: set site.google_client_id in settings.yaml)'));s.firstChild.className='muted';return;}
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
  return gread().then(function(remote){remote=remote&&Array.isArray(remote.h)?remote:{v:1,h:[],cash:[],nav:[],updated:0};
   if((remote.updated||0)>(local.updated||0)){put(remote);render();gmsg('已從 Google 雲端硬碟載入 '+new Date(remote.updated).toLocaleString(),'Loaded from Google Drive '+new Date(remote.updated).toLocaleString(),'ok');}
   else if((local.updated||0)>(remote.updated||0)){return gwrite(local).then(function(){gmsg('已上傳到 Google 雲端硬碟 '+new Date().toLocaleTimeString(),'Uploaded '+new Date().toLocaleTimeString(),'ok');});}
   else gmsg('已同步（無變更）','In sync','ok');});})
 .catch(function(e){gmsg('同步失敗：'+e.message,'Sync failed: '+e.message,'err');if(e.message==='401')G.tok=null;})
 .then(function(){G.busy=false;});}
var _put=put;put=function(d){d.updated=Date.now();var ok=_put(d);if(ok&&G.on){clearTimeout(G._t);G._t=setTimeout(function(){gauth(false).then(function(ok2){if(ok2)gsync();});},800);}return ok;};
try{G.on=!!G.cid&&localStorage.getItem(GKEY)==='1';}catch(e){}
gbar();if(G.on)gauth(false).then(function(ok){if(ok)gsync();});

function render(){ph();var d=get(),need={};d.h.forEach(function(h){var n=norm(h.s);if(n)need[n.mk]=1;});
 var mks=Object.keys(need);if(mks.indexOf('us')<0)mks.push('us');
 Promise.all(mks.map(loadMk)).then(function(res){gFM={};mks.forEach(function(m,i){gFM[m]=res[i];});draw(d,gFM);});
 if(mks.length&&!document.getElementById('pft').tBodies[0].rows.length)msg(['載入價格中…','Loading prices…']);}

// ---------------------------------------------------------------- Feature 4: NAV Chart & HWM Drawdown
function renderNav(d, tot){
 var x = document.getElementById('pfnavbox');
 if(!x) return;
 x.textContent = '';
 if(!tot || tot <= 0){ x.style.display = 'none'; return; }
 x.style.display = 'block';
 d.nav = Array.isArray(d.nav) ? d.nav : [];
 var today = new Date().toISOString().slice(0, 10);
 var last = d.nav[d.nav.length - 1];
 var changed = false;
 if(!last || last.d !== today){
  d.nav.push({d: today, v: Math.round(tot)});
  changed = true;
 } else if(Math.abs((last.v || 0) - tot) >= 1){
  last.v = Math.round(tot);
  changed = true;
 }
 if(d.nav.length > 180){ d.nav = d.nav.slice(-180); changed = true; }
 if(changed){ _put(d); }

 var hwm = tot, mdd = 0, peak = 0;
 d.nav.forEach(function(pt){
  if(pt.v > hwm) hwm = pt.v;
  if(pt.v > peak) peak = pt.v;
  var curDd = peak > 0 ? (pt.v - peak) / peak * 100 : 0;
  if(curDd < mdd) mdd = curDd;
 });
 var curDd = hwm > 0 ? ((tot - hwm) / hwm * 100) : 0;

 var head = el('div', 'pfnav-head');
 var tit = el('div', 'pfnav-title');
 tit.appendChild(L('📈 個人資產淨值走勢與回撤追蹤', 'NAV & Drawdown Tracker'));
 head.appendChild(tit);

 var stats = el('div', 'pfnav-stats');
 function addStat(lblZh, lblEn, valText, valCls){
  var s = el('div', 'pfnav-stat');
  s.appendChild(L(lblZh + ': ', lblEn + ': '));
  var b = el('b', valCls || '', valText);
  s.appendChild(b);
  stats.appendChild(s);
 }
 addStat('歷史最高 (HWM)', 'High Water Mark', 'NT$ ' + num(hwm, 0));
 addStat('距高點回撤', 'Drawdown', (curDd >= -0.05 ? '0.0% 🏆 新高' : sgn(curDd, 1, true)), cl(curDd));
 addStat('最大回撤 (MDD)', 'Max Drawdown', (mdd < 0 ? sgn(mdd, 1, true) : '0.0%'), 'dn');
 addStat('記錄天數', 'Tracked Days', d.nav.length + (en()?' Days':' 天'));
 head.appendChild(stats);
 x.appendChild(head);

 var wrap = el('div', 'pfnav-svg-wrap');
 var svg = svgEl('svg', { viewBox: '0 0 600 120', class: 'pfnav-svg', preserveAspectRatio: 'none' });

 var defs = svgEl('defs');
 var grad = svgEl('linearGradient', { id: 'navGrad', x1: '0', y1: '0', x2: '0', y2: '1' });
 grad.appendChild(svgEl('stop', { offset: '0%', 'stop-color': '#3a86ff', 'stop-opacity': '0.35' }));
 grad.appendChild(svgEl('stop', { offset: '100%', 'stop-color': '#3a86ff', 'stop-opacity': '0.0' }));
 defs.appendChild(grad);
 svg.appendChild(defs);

 var pts = d.nav.slice();
 if(pts.length === 1){ pts = [{d: pts[0].d, v: pts[0].v}, {d: today, v: pts[0].v}]; }
 var minV = Infinity, maxV = -Infinity;
 pts.forEach(function(p){ if(p.v < minV) minV = p.v; if(p.v > maxV) maxV = p.v; });
 if(hwm > maxV) maxV = hwm;
 if(minV === maxV){ minV *= 0.95; maxV *= 1.05; }
 else {
  var pad = (maxV - minV) * 0.15;
  minV -= pad; maxV += pad;
 }
 var W = 600, H = 120, pL = 20, pR = 20, pT = 20, pB = 22;
 var coords = pts.map(function(pt, idx){
  var cx = pL + (idx / (pts.length - 1)) * (W - pL - pR);
  var cy = H - pB - ((pt.v - minV) / (maxV - minV)) * (H - pT - pB);
  return { x: cx, y: cy, v: pt.v, d: pt.d };
 });

 var hwmY = H - pB - ((hwm - minV) / (maxV - minV)) * (H - pT - pB);
 svg.appendChild(svgEl('line', { x1: pL, y1: hwmY, x2: W - pR, y2: hwmY, stroke: '#f59e0b', 'stroke-dasharray': '4 4', 'stroke-width': '1', opacity: '0.8' }));
 var hwmTxt = svgEl('text', { x: W - pR - 4, y: Math.max(12, hwmY - 4), 'text-anchor': 'end', fill: '#f59e0b', 'font-size': '10', 'font-weight': '600' });
 hwmTxt.textContent = 'HWM NT$' + num(hwm, 0);
 svg.appendChild(hwmTxt);

 var dArea = 'M ' + coords[0].x.toFixed(1) + ' ' + (H - pB);
 coords.forEach(function(c){ dArea += ' L ' + c.x.toFixed(1) + ' ' + c.y.toFixed(1); });
 dArea += ' L ' + coords[coords.length - 1].x.toFixed(1) + ' ' + (H - pB) + ' Z';
 svg.appendChild(svgEl('path', { d: dArea, fill: 'url(#navGrad)' }));

 var dLine = 'M ' + coords[0].x.toFixed(1) + ' ' + coords[0].y.toFixed(1);
 for(var i=1; i<coords.length; i++){ dLine += ' L ' + coords[i].x.toFixed(1) + ' ' + coords[i].y.toFixed(1); }
 svg.appendChild(svgEl('path', { d: dLine, fill: 'none', stroke: '#3a86ff', 'stroke-width': '2.2', 'stroke-linecap': 'round' }));

 var lastC = coords[coords.length - 1];
 svg.appendChild(svgEl('circle', { cx: lastC.x.toFixed(1), cy: lastC.y.toFixed(1), r: '4', fill: '#3a86ff', stroke: '#ffffff', 'stroke-width': '1.5' }));

 var dtStart = svgEl('text', { x: pL, y: H - 4, fill: '#888', 'font-size': '10' });
 dtStart.textContent = pts[0].d;
 svg.appendChild(dtStart);
 var dtEnd = svgEl('text', { x: W - pR, y: H - 4, 'text-anchor': 'end', fill: '#888', 'font-size': '10' });
 dtEnd.textContent = pts[pts.length - 1].d;
 svg.appendChild(dtEnd);

 wrap.appendChild(svg);
 x.appendChild(wrap);
}

// ---------------------------------------------------------------- Main Draw
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
   
   // Feature 3: Dynamic Stop & Profit Targets column
   var stopTd = td('', 'r');
   var box = el('div', 'pft-stop');
   var symKey = ((p && p.sym) || h.s || '').toUpperCase().replace(/\.(TW|TWO)$/,'');
   var stopPct = 0.10, tgtPct = 0.18;
   if(['SPCX','OKLO','SMR','PLTR','IONQ'].indexOf(symKey)>=0){ stopPct = 0.15; tgtPct = 0.30; }
   else if(['KLAC','TSM','NVDA','ASML','AMAT','AMD','AVGO','2330','SMH'].indexOf(symKey)>=0){ stopPct = 0.12; tgtPct = 0.22; }
   else if(['JNJ','PG','KO','MCD','TLT','BND'].indexOf(symKey)>=0){ stopPct = 0.08; tgtPct = 0.12; }
   if(h.c > 0){
    var cost = h.c;
    var stopPx = p.px >= cost ? Math.max(cost, p.px * (1 - stopPct)) : (cost * (1 - stopPct));
    var tgtPx = cost * (1 + tgtPct);
    if(p.px <= stopPx){
     var hit = el('span', 's-hit dn');
     hit.appendChild(L('⚠️ 觸及防守', '⚠️ Stop'));
     box.appendChild(hit);
    } else if(p.px >= tgtPx){
     var hit2 = el('span', 's-hit up');
     hit2.appendChild(L('🎯 達第一停利', '🎯 Target'));
     box.appendChild(hit2);
    }
    var stpLine = el('span', 's-stp');
    stpLine.appendChild(L('防 ' + num(stopPx, 1), 'Stp ' + num(stopPx, 1)));
    box.appendChild(stpLine);
    var tgtLine = el('span', 's-tgt');
    tgtLine.appendChild(L('利 ' + num(tgtPx, 1), 'Tgt ' + num(tgtPx, 1)));
    box.appendChild(tgtLine);
   } else {
    var stopPx2 = p.px * (1 - stopPct);
    var stpLine2 = el('span', 's-stp');
    stpLine2.appendChild(L('防 ' + num(stopPx2, 1) + ' (-' + Math.round(stopPct*100) + '%)', 'Stp ' + num(stopPx2, 1)));
    box.appendChild(stpLine2);
   }
   stopTd.appendChild(box);

   td(totV?num(r.vt/totV*100,1)+'%':'—');}
  else{var t=td('','r pfwarn');t.colSpan=10;t.appendChild(L('找不到報價，請手動輸入價格：','No price found — enter one: '));var inp=el('input');inp.type='number';inp.step='any';inp.min='0';inp.setAttribute('aria-label','manual price');
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
  :['尚未輸入持股：在下方新增，或用「一次貼上多筆」','No holdings yet — add some below or paste many at once']);

 renderNav(d, tot);
 renderDx(rows, tot, totV, cashT);
}

// ---------------------------------------------------------------- Diagnostics
function renderDx(rows, tot, totV, cashT){
 var x = document.getElementById('pfdx');
 if(!x) return;
 x.textContent = '';
 if(!rows.length && !cashT){
  x.style.display = 'none';
  renderCrisis([], 0, 0, 0);
  renderWhatif([], 0, 0, 0, 0, {});
  renderEarnings([], 0);
  return;
 }
 x.style.display = 'block';
 if(!tot) tot = 1;

 var secW = {}, pfBeta = 0;
 SECS.forEach(function(s){ secW[s.k] = 0; });
 secW.other = 0;
 secW.cash = cashT / tot;
 rows.forEach(function(r){
  var sym = ((r.p && r.p.sym) || r.h.s || '').toUpperCase();
  var key = sym.replace(/\.(TW|TWO)$/,'');
  var found = null;
  for(var i=0; i<SECS.length; i++){
   if(SECS[i].syms.indexOf(key) >= 0 || SECS[i].syms.indexOf(sym) >= 0){ found = SECS[i]; break; }
  }
  var w = (r.vt || 0) / tot;
  if(found){ secW[found.k] += w; pfBeta += w * found.b; }
  else { secW.other += w; pfBeta += w * 1.1; }
 });
 var top1 = rows[0] ? (rows[0].vt / tot * 100) : 0;
 var top1Sym = rows[0] ? ((rows[0].p && rows[0].p.sym) || rows[0].h.s) : '—';
 var top3 = 0;
 for(var i=0; i<Math.min(3, rows.length); i++){ top3 += (rows[i].vt / tot * 100); }
 var cashPct = cashT / tot * 100;
 var semiTechPct = ((secW.semi || 0) + (secW.tech || 0)) * 100;

 var hd = el('h3', '');
 hd.appendChild(L('持倉健康度診斷與再平衡建議', 'Portfolio Diagnostics & Rebalancing'));
 x.appendChild(hd);

 var grid = el('div', 'pfdx-grid');

 var k1 = el('div', 'pfdx-k');
 k1.appendChild(el('div', 'lbl')).appendChild(L('組合風險屬性', 'Risk Profile'));
 var isAgg = pfBeta >= 1.35 || semiTechPct >= 50;
 var isBal = cashPct >= 15 && top1 <= 25 && pfBeta < 1.15;
 var val1 = k1.appendChild(el('div', 'val ' + (isAgg ? 'dn' : (isBal ? 'up' : 'warn'))));
 val1.appendChild(isAgg ? L('高波動進攻型', 'Aggressive Growth') : (isBal ? L('穩健平衡型', 'Balanced Defensive') : L('成長型', 'Moderate Growth')));
 k1.appendChild(el('div', 'sub')).appendChild(L('預估整體 Beta: ' + num(pfBeta, 2), 'Estimated Beta: ' + num(pfBeta, 2)));
 grid.appendChild(k1);

 var k2 = el('div', 'pfdx-k');
 k2.appendChild(el('div', 'lbl')).appendChild(L('壓力情境推估', 'Stress Scenario'));
 var val2 = k2.appendChild(el('div', 'val dn', '-' + num(pfBeta * 5, 1) + '%'));
 k2.appendChild(el('div', 'sub')).appendChild(L('大盤若跌 5% 預估回撤', 'Expected drop if SPX -5%'));
 grid.appendChild(k2);

 var k3 = el('div', 'pfdx-k');
 k3.appendChild(el('div', 'lbl')).appendChild(L('前三大持股集中度', 'Top 3 Concentration'));
 var val3 = k3.appendChild(el('div', 'val ' + (top3 >= 60 ? 'dn' : (top3 >= 45 ? 'warn' : 'up')), num(top3, 1) + '%'));
 k3.appendChild(el('div', 'sub')).appendChild(L('最大單一: ' + top1Sym + ' (' + num(top1, 1) + '%)', 'Top holding: ' + top1Sym + ' (' + num(top1, 1) + '%)'));
 grid.appendChild(k3);

 var k4 = el('div', 'pfdx-k');
 k4.appendChild(el('div', 'lbl')).appendChild(L('防守現金水位', 'Cash Buffer'));
 var val4 = k4.appendChild(el('div', 'val ' + (cashPct < 5 ? 'dn' : (cashPct < 15 ? 'warn' : 'up')), num(cashPct, 1) + '%'));
 k4.appendChild(el('div', 'sub')).appendChild(L(cashPct < 5 ? '無防守緩衝 ⚠️' : (cashPct < 15 ? '緩衝適中' : '充裕'), cashPct < 5 ? 'Low liquidity' : 'Adequate'));
 grid.appendChild(k4);
 x.appendChild(grid);

 var secBox = el('div', 'pfdx-sec');
 secBox.appendChild(el('div', 'lbl')).appendChild(L('產業族群曝險分布', 'Sector Exposure Breakdown'));
 var bar = el('div', 'pfdx-bar');
 var tags = el('div', 'pfdx-tags');
 function addSeg(pct, c, zh, en_){
  if(pct < 0.005) return;
  var seg = el('div', 'pfdx-bar-seg');
  seg.style.width = (pct * 100) + '%';
  seg.style.background = c;
  bar.appendChild(seg);
  var tag = el('span', 'pfdx-tag');
  var dot = el('span', 'dot');
  dot.style.background = c;
  tag.appendChild(dot);
  tag.appendChild(L(zh + ' ' + num(pct * 100, 1) + '%', en_ + ' ' + num(pct * 100, 1) + '%'));
  tags.appendChild(tag);
 }
 SECS.forEach(function(s){ addSeg(secW[s.k], s.c, s.zh, s.en); });
 addSeg(secW.other, '#9e9e9e', '其他標的', 'Others');
 addSeg(secW.cash, '#4caf50', '現金', 'Cash');
 secBox.appendChild(bar);
 secBox.appendChild(tags);
 x.appendChild(secBox);

 var list = el('div', 'pfdx-items');
 function addItem(cls, ico, zh, en_){
  var item = el('div', 'pfdx-item ' + cls);
  item.appendChild(el('span', 'ico', ico));
  var desc = el('div', 'desc');
  desc.appendChild(L(zh, en_));
  item.appendChild(desc);
  list.appendChild(item);
 }
 if(top1 > 25){
  addItem('bad', '🔴',
   '【單一持股過度集中】' + top1Sym + ' 佔比高達 ' + num(top1, 1) + '%（警戒線 25%）。單一個股遭遇黑天鵝或財報暴跌將重創總淨值。',
   '[High Concentration] ' + top1Sym + ' takes ' + num(top1, 1) + '% of total assets (>25% threshold). A single-stock shock will severely impact NAV.');
 }
 if(semiTechPct > 50){
  addItem('bad', '🔴',
   '【產業高度同質性風險】半導體與科技族群合計高達 ' + num(semiTechPct, 1) + '%。持股高度同向連動，實質分散風險效果有限，回檔時防禦力偏弱。',
   '[Sector Risk] Semis and Tech total ' + num(semiTechPct, 1) + '%. Highly correlated exposure limits true diversification.');
 }
 if(cashPct < 5){
  addItem('warn', '🟡',
   '【流動性緩衝匱乏】現金水位僅 ' + num(cashPct, 1) + '%（全額滿水位進攻）。缺乏抗震緩衝與市場大回檔時逢低加碼之籌碼，建議保有 5%~15% 現金。',
   '[Zero Cash Buffer] Cash is only ' + num(cashPct, 1) + '%. No dry powder to buy market dips.');
 }
 var deepLoss = rows.filter(function(r){ return r.ret != null && r.ret <= -15; });
 if(deepLoss.length){
  var names = deepLoss.map(function(r){ return ((r.p && r.p.sym) || r.h.s) + ' (' + sgn(r.ret, 1, true) + ')'; }).join('、');
  addItem('warn', '🟠',
   '【高波動持股回撤檢視】' + names + ' 帳面跌幅已超 15%。若屬小型主題投機部位，建議設定明確停損點防守，避免虧損持續擴大。',
   '[Drawdown Warning] Deep unrealized loss in ' + names + '. Re-evaluate thesis and enforce strict risk stops.');
 }
 if(top1 > 25){
  var trimTwd = Math.round((top1 - 22) / 100 * tot);
  addItem('act', '🎯',
   '【再平衡建議：分批鎖利降權】建議趁目前處於獲利保護傘，分批減碼 ' + top1Sym + ' 至 22% 左右（約需減碼 NT$ ' + num(trimTwd, 0) + '），降低單一個股黑天鵝衝擊。',
   '[Action: Profit-taking] Consider trimming ' + top1Sym + ' down to ~22% (approx NT$ ' + num(trimTwd, 0) + ') to lock in gains and de-risk.');
 }
 if(cashPct < 10){
  var targetCash = Math.round(tot * 0.1);
  addItem('act', '🎯',
   '【再平衡建議：建立 10% 現金儲備】建議將獲利了結資金保留為現金，建立約 NT$ ' + num(targetCash, 0) + '（10%）的流動性防守墊，提升投資組合抗震力。',
   '[Action: Build Cash] Retain trim proceeds as cash to build a ~NT$ ' + num(targetCash, 0) + ' (10%) liquidity buffer.');
 }
 if(semiTechPct > 50){
  addItem('act', '🎯',
   '【再平衡建議：引進低相關資產】未來新增資金建議避開半導體，優先配置大盤 ETF（如 SPY / 0050）、高股息或公債，平滑整體波動。',
   '[Action: Diversify] Allocate new capital into non-tech defensive assets (broad market ETFs, high dividend, Treasuries) to reduce portfolio Beta.');
 }
 x.appendChild(list);

 renderCrisis(rows, tot, totV, cashT);
 renderWhatif(rows, tot, totV, cashT, pfBeta, secW);
 renderEarnings(rows, tot);
}

// ---------------------------------------------------------------- Feature 1: Crisis Replay Simulator
var curCrisisId = 'yen2024';
var CRISES = [
 {
  id: 'yen2024',
  zh: '2024.08.05 日圓套息平倉股災', en: '2024 Yen Carry Unwind',
  descZh: '日銀突擊升息引發全球千億美元套息交易無差別踩踏撤離，半導體與高估值科技單週重挫。',
  descEn: 'BOJ surprise hike sparked mass unwind of carry trades; semis and high-beta tech crushed.',
  shocks: { semi: 0.142, tech: 0.085, front: 0.185, fin: 0.075, def: 0.020, other: 0.061 }
 },
 {
  id: 'fed2022',
  zh: '2022 激進升息科技熊市', en: '2022 Fed Tech Bear',
  descZh: '通膨破 9% 聯準會一年升息 17 碼，高本益比成長股、半導體與小型題材概念股全面腰斬。',
  descEn: 'Fed hiked 425bps in a single year against 9%+ inflation; high multiple growth wiped out.',
  shocks: { semi: 0.440, tech: 0.356, front: 0.650, fin: 0.210, def: 0.080, other: 0.254 }
 },
 {
  id: 'covid2020',
  zh: '2020 疫情流動性熔斷', en: '2020 COVID Liquidity Crash',
  descZh: '美股兩週內四度熔斷，全球流動性瞬間枯竭，避險黃金與債券一度同遭恐慌拋售變現。',
  descEn: 'US market triggered 4 circuit breakers in 10 days; global dash for cash overwhelmed safe havens.',
  shocks: { semi: 0.350, tech: 0.280, front: 0.450, fin: 0.430, def: 0.150, other: 0.339 }
 },
 {
  id: 'gfc2008',
  zh: '2008 次貸金融海嘯', en: '2008 Global Financial Crisis',
  descZh: '雷曼倒閉引發全球銀行信用體系凍結，百年一遇資產負債表大清算，股市持續崩跌一年半。',
  descEn: 'Lehman collapse froze global banking credit; multi-year secular bear market and wealth wipeout.',
  shocks: { semi: 0.620, tech: 0.530, front: 0.700, fin: 0.780, def: 0.220, other: 0.568 }
 }
];

function renderCrisis(rows, tot, totV, cashT){
 var x = document.getElementById('pfcrisis');
 if(!x) return;
 x.textContent = '';
 if(!rows.length && !cashT){ x.style.display = 'none'; return; }
 x.style.display = 'block';

 var hd = el('h3', '');
 hd.appendChild(L('🌪️ 歷史危機持倉壓力測試重播器', 'Crisis Replay Simulator'));
 x.appendChild(hd);
 var sub = el('p', 'muted small');
 sub.appendChild(L('點選經典股災情境，以當前持股精準回放若歷史重演時的資產蒸發金額與各標的回撤衝擊',
                  'Simulate how your current portfolio would have performed during historical market crashes.'));
 x.appendChild(sub);

 var btns = el('div', 'pfcrisis-btns');
 CRISES.forEach(function(c){
  var b = el('button', 'pfcrisis-btn' + (c.id === curCrisisId ? ' active' : ''));
  b.type = 'button';
  b.appendChild(L(c.zh, c.en));
  b.addEventListener('click', function(){
   curCrisisId = c.id;
   renderCrisis(rows, tot, totV, cashT);
  });
  btns.appendChild(b);
 });
 x.appendChild(btns);

 var crisis = CRISES.find(function(c){ return c.id === curCrisisId; }) || CRISES[0];
 var descBox = el('div', 'muted small');
 descBox.style.marginBottom = '8px';
 descBox.appendChild(L('📜 情境背景：' + crisis.descZh, 'Scenario Context: ' + crisis.descEn));
 x.appendChild(descBox);

 var totLoss = 0;
 var holdingLosses = [];
 rows.forEach(function(r){
  var sym = ((r.p && r.p.sym) || r.h.s || '').toUpperCase();
  var key = sym.replace(/\.(TW|TWO)$/,'');
  var found = null;
  for(var i=0; i<SECS.length; i++){
   if(SECS[i].syms.indexOf(key) >= 0 || SECS[i].syms.indexOf(sym) >= 0){ found = SECS[i]; break; }
  }
  var cat = found ? found.k : 'other';
  var rate = crisis.shocks[cat] != null ? crisis.shocks[cat] : crisis.shocks.other;
  var loss = (r.vt || 0) * rate;
  totLoss += loss;
  holdingLosses.push({ sym: sym, vt: r.vt || 0, rate: rate, loss: loss, name: (r.p && r.p.name) || sym });
 });

 holdingLosses.sort(function(a, b){ return b.loss - a.loss; });
 var dropPct = tot > 0 ? (totLoss / tot * 100) : 0;
 var postNAV = Math.max(0, tot - totLoss);
 var cashCover = (cashT > 0 && totLoss > 0) ? Math.min(100, cashT / totLoss * 100) : 0;

 var res = el('div', 'pfcrisis-result');
 var impGrid = el('div', 'pfcrisis-impact');

 function addImp(lblZh, lblEn, val, subZh, subEn, cls){
  var d = el('div', 'pfdx-k');
  d.appendChild(el('div', 'lbl')).appendChild(L(lblZh, lblEn));
  d.appendChild(el('div', 'val ' + (cls || ''), val));
  if(subZh) d.appendChild(el('div', 'sub')).appendChild(L(subZh, subEn));
  impGrid.appendChild(d);
 }
 addImp('預估資產蒸發金額', 'Simulated Drawdown', '-NT$ ' + num(totLoss, 0), '相當於總資產 -' + num(dropPct, 1) + '%', 'NAV drop -' + num(dropPct, 1) + '%', 'dn');
 addImp('情境壓力後淨值', 'Post-Crisis NAV', 'NT$ ' + num(postNAV, 0), '跌後保留率 ' + num(100 - dropPct, 1) + '%', 'Capital preserved ' + num(100 - dropPct, 1) + '%', '');
 addImp('防守現金吸收度', 'Cash Buffer Absorption', (cashCover > 0 ? (num(cashCover, 1) + '%') : '0.0%'),
        (cashCover >= 20 ? '現金有效緩衝部分跌勢' : '⚠️ 現金防守墊過低'), (cashCover >= 20 ? 'Cash partially buffers loss' : 'Low cash cushion'),
        (cashCover >= 20 ? 'up' : 'dn'));
 res.appendChild(impGrid);

 var barsTitle = el('div', 'lbl');
 barsTitle.style.marginBottom = '6px';
 barsTitle.style.fontSize = '12px';
 barsTitle.appendChild(L('個別持股虧損衝擊排行（前 5 大）：', 'Top 5 Holding Drawdown Breakdown:'));
 res.appendChild(barsTitle);

 var maxLoss = holdingLosses[0] ? holdingLosses[0].loss : 1;
 var barList = el('div', 'pfcrisis-bars');
 for(var i=0; i<Math.min(5, holdingLosses.length); i++){
  var item = holdingLosses[i];
  var row = el('div', 'pfcrisis-bar-row');
  var lbl = el('div', 'pfcrisis-bar-lbl', item.sym);
  row.appendChild(lbl);
  var track = el('div', 'pfcrisis-bar-track');
  var fill = el('div', 'pfcrisis-bar-fill');
  fill.style.width = Math.max(3, (item.loss / (maxLoss || 1) * 100)) + '%';
  track.appendChild(fill);
  row.appendChild(track);
  var val = el('div', 'pfcrisis-bar-val dn', '-NT$ ' + num(item.loss, 0) + ' (-' + num(item.rate * 100, 1) + '%)');
  row.appendChild(val);
  barList.appendChild(row);
 }
 res.appendChild(barList);

 var tip = el('div', 'pfdx-item act');
 tip.style.marginTop = '10px';
 tip.appendChild(el('span', 'ico', '💡'));
 var tipDesc = el('div', 'desc');
 tipDesc.appendChild(L('防禦指引：此情境下因高 Beta 科技／半導體權重集中，跌幅擴大約為大盤的 ' + num(dropPct / (crisis.shocks.other * 100 || 1), 1) + ' 倍。可透過下方【What-if 模擬器】調節前兩大重傷標的，降低下檔風險。',
                       'Action Guide: Concentrated tech/semi exposure amplifies drawdown to ' + num(dropPct / (crisis.shocks.other * 100 || 1), 1) + 'x of broad market. Test rebalancing below.'));
 tip.appendChild(tipDesc);
 res.appendChild(tip);

 x.appendChild(res);
}

// ---------------------------------------------------------------- Feature 2: What-if Rebalancing Sandbox
var wiState = { trimPct: 50, sym: '', target: 'cash' };

function renderWhatif(rows, tot, totV, cashT, pfBeta, secW){
 var x = document.getElementById('pfwhatif');
 if(!x) return;
 x.textContent = '';
 if(!rows.length){ x.style.display = 'none'; return; }
 x.style.display = 'block';

 if(!wiState.sym && rows[0]){
  wiState.sym = ((rows[0].p && rows[0].p.sym) || rows[0].h.s || '').toUpperCase();
 }

 var hd = el('h3', '');
 hd.appendChild(L('🧪 「What-if」虛擬調倉即時模擬器', 'What-if Rebalancing Sandbox'));
 x.appendChild(hd);
 var sub = el('p', 'muted small');
 sub.appendChild(L('模擬減碼特定持股並轉入現金、公債或大盤 ETF，即時預覽 Beta 降幅、科技集中度改善與少虧金額',
                  'Simulate trimming holdings and reallocating into cash, bonds, or index ETFs.'));
 x.appendChild(sub);

 var ctrls = el('div', 'pfwhatif-ctrls');

 ctrls.appendChild(L('欲減碼：', 'Trim: '));
 var selStock = el('select', '');
 rows.forEach(function(r){
  var s = ((r.p && r.p.sym) || r.h.s || '').toUpperCase();
  var opt = document.createElement('option');
  opt.value = s;
  opt.textContent = s + ' (' + num(r.vt / tot * 100, 1) + '%, NT$' + num(r.vt, 0) + ')';
  if(s === wiState.sym) opt.selected = true;
  selStock.appendChild(opt);
 });
 selStock.addEventListener('change', function(){
  wiState.sym = selStock.value;
  renderWhatif(rows, tot, totV, cashT, pfBeta, secW);
 });
 ctrls.appendChild(selStock);

 ctrls.appendChild(L('幅度：', 'Pct: '));
 var pctsBox = el('div', 'pfwhatif-pcts');
 [25, 50, 75, 100].forEach(function(p){
  var b = el('button', 'pfwhatif-pbtn' + (wiState.trimPct === p ? ' active' : ''));
  b.type = 'button';
  b.textContent = p === 100 ? (en() ? '100% (All)' : '100% 全結') : (p + '%');
  b.addEventListener('click', function(){
   wiState.trimPct = p;
   renderWhatif(rows, tot, totV, cashT, pfBeta, secW);
  });
  pctsBox.appendChild(b);
 });
 ctrls.appendChild(pctsBox);

 ctrls.appendChild(L('轉入：', 'Into: '));
 var selTgt = el('select', '');
 var TGTS = [
  { k: 'cash', b: 0.0, zh: '💵 現金防守墊 (Beta 0.0)', en: '💵 Cash Buffer (Beta 0.0)' },
  { k: 'spy', b: 1.0, zh: '📈 標普 500 (SPY - Beta 1.0)', en: '📈 S&P 500 (SPY - Beta 1.0)' },
  { k: 'tlt', b: 0.15, zh: '🛡️ 美國長天期公債 (TLT - Beta 0.15)', en: '🛡️ 20+ Y Treasuries (TLT - Beta 0.15)' },
  { k: 'tw50', b: 1.05, zh: '🇹🇼 台灣 50 (0050 - Beta 1.05)', en: '🇹🇼 Taiwan 50 (0050 - Beta 1.05)' }
 ];
 TGTS.forEach(function(t){
  var opt = document.createElement('option');
  opt.value = t.k;
  opt.textContent = en() ? t.en : t.zh;
  if(t.k === wiState.target) opt.selected = true;
  selTgt.appendChild(opt);
 });
 selTgt.addEventListener('change', function(){
  wiState.target = selTgt.value;
  renderWhatif(rows, tot, totV, cashT, pfBeta, secW);
 });
 ctrls.appendChild(selTgt);
 x.appendChild(ctrls);

 var selRow = rows.find(function(r){ return (((r.p && r.p.sym) || r.h.s || '').toUpperCase()) === wiState.sym; }) || rows[0];
 var trimRatio = wiState.trimPct / 100;
 var trimTwd = (selRow.vt || 0) * trimRatio;
 var selSym = ((selRow.p && selRow.p.sym) || selRow.h.s || '').toUpperCase();
 var selKey = selSym.replace(/\.(TW|TWO)$/,'');
 var found = null;
 for(var i=0; i<SECS.length; i++){
  if(SECS[i].syms.indexOf(selKey) >= 0 || SECS[i].syms.indexOf(selSym) >= 0){ found = SECS[i]; break; }
 }
 var stockBeta = found ? found.b : 1.1;
 var tgtObj = TGTS.find(function(t){ return t.k === wiState.target; }) || TGTS[0];
 var targetBeta = tgtObj.b;

 var weightShift = tot > 0 ? (trimTwd / tot) : 0;
 var curBeta = pfBeta;
 var newBeta = Math.max(0, curBeta - weightShift * stockBeta + weightShift * targetBeta);
 var betaDiff = newBeta - curBeta;

 var curTechSemi = ((secW.semi || 0) + (secW.tech || 0)) * 100;
 var isTechSemi = found && (found.k === 'semi' || found.k === 'tech');
 var newTechSemi = isTechSemi ? Math.max(0, curTechSemi - weightShift * 100) : curTechSemi;

 var curDrop5 = curBeta * 5;
 var newDrop5 = newBeta * 5;
 var savedLossTwd = Math.max(0, (curDrop5 - newDrop5) / 100 * tot);

 var comp = el('div', 'pfwhatif-comp');

 function addCompCard(lblZh, lblEn, oldV, newV, diffText, diffCls){
  var c = el('div', 'pfwhatif-card');
  c.appendChild(el('div', 'lbl')).appendChild(L(lblZh, lblEn));
  var vals = el('div', 'vals');
  vals.appendChild(el('span', 'muted', oldV));
  vals.appendChild(el('span', '', ' ➔ '));
  vals.appendChild(el('span', '', newV));
  c.appendChild(vals);
  if(diffText) c.appendChild(el('div', 'chg ' + (diffCls || ''), diffText));
  comp.appendChild(c);
 }

 addCompCard('整體投資組合 Beta', 'Portfolio Beta', num(curBeta, 2), num(newBeta, 2),
             (betaDiff < 0 ? '🟢 降 ' + num(Math.abs(betaDiff), 2) + ' (波動減 ' + num(Math.abs(betaDiff) / (curBeta || 1) * 100, 0) + '%)' : ''), 'up');
 addCompCard('科技與半導體集中度', 'Tech & Semi Exposure', num(curTechSemi, 1) + '%', num(newTechSemi, 1) + '%',
             (newTechSemi < curTechSemi ? '🟢 降 ' + num(curTechSemi - newTechSemi, 1) + '%' : '無變更'), 'up');
 addCompCard('大盤跌 5% 預估回撤', 'Drop if SPX -5%', '-' + num(curDrop5, 1) + '%', '-' + num(newDrop5, 1) + '%',
             (savedLossTwd > 0 ? '🛡️ 少虧 NT$ ' + num(savedLossTwd, 0) : ''), 'up');
 addCompCard('釋出／轉移資金', 'Reallocated Capital', 'NT$ ' + num(trimTwd, 0), num(weightShift * 100, 1) + '%',
             '佔總資產比率', '');

 x.appendChild(comp);

 var actRow = el('div', 'pfrow');
 actRow.style.marginTop = '10px';
 var applyBtn = el('button', 'btn g');
 applyBtn.type = 'button';
 applyBtn.appendChild(L('一鍵套用調倉至持股', 'Apply Rebalancing to My Holdings'));
 applyBtn.addEventListener('click', function(){
  var cfmMsg = en()
   ? 'Apply rebalancing? Trim ' + selSym + ' by ' + wiState.trimPct + '% and move NT$' + num(trimTwd, 0) + ' to ' + tgtObj.k + '?'
   : '確定要套用調倉嗎？將 ' + selSym + ' 減碼 ' + wiState.trimPct + '%，並將資金 NT$ ' + num(trimTwd, 0) + ' 轉至 ' + (en()?tgtObj.en:tgtObj.zh) + '。';
  if(!confirm(cfmMsg)) return;

  var d = get();
  var idx = d.h.findIndex(function(h){ return (norm(h.s) && norm(h.s).key) === norm(selSym).key; });
  if(idx < 0) return;
  var origN = d.h[idx].n;
  var cutN = origN * trimRatio;
  var remainN = origN - cutN;
  if(remainN <= 0.0001){ d.h.splice(idx, 1); }
  else { d.h[idx].n = Math.round(remainN * 1000) / 1000; }

  if(tgtObj.k === 'cash'){
   d.cash = d.cash || [];
   var curC = d.cash.find(function(c){ return c.cur === 'TWD'; });
   if(curC){ curC.a += Math.round(trimTwd); }
   else { d.cash.push({ cur: 'TWD', a: Math.round(trimTwd) }); }
  } else {
   var mapTicker = { spy: 'SPY', tlt: 'TLT', tw50: '0050' };
   var addSym = mapTicker[tgtObj.k] || 'SPY';
   var tgtP = price({ s: addSym, p: 0 }, gFM[norm(addSym).mk]);
   var px = tgtP ? tgtP.px : (addSym==='SPY'?600:(addSym==='TLT'?95:180));
   var fx = FX[cur(norm(addSym).mk)] || 1;
   var addShares = Math.round((trimTwd / (px * fx)) * 100) / 100;
   upsert(d, addSym, addShares, px);
  }
  put(d);
  render();
  msg(['已成功套用調倉！', 'Rebalancing applied successfully!']);
 });
 actRow.appendChild(applyBtn);
 x.appendChild(actRow);
}

// ---------------------------------------------------------------- Feature 6: Earnings Radar
var EARNINGS_CAL = [
 { sym: 'TSM', name: '台積電', date: '2026-10-15', move: 6.5, noteZh: '先進製程 2nm/3nm 稼動率與 2027 資本支出指引', noteEn: '2nm/3nm utilization & 2027 capex guidance' },
 { sym: '2330', name: '台積電', date: '2026-10-15', move: 6.5, noteZh: '先進製程 2nm/3nm 稼動率與 2027 資本支出指引', noteEn: '2nm/3nm utilization & 2027 capex guidance' },
 { sym: 'NVDA', name: '輝達', date: '2026-11-19', move: 8.2, noteZh: 'Blackwell 伺服器出貨放量進度與毛利率走向', noteEn: 'Blackwell server shipments & gross margin trajectory' },
 { sym: 'GOOG', name: '谷歌 (Alphabet)', date: '2026-10-22', move: 5.5, noteZh: 'Google Cloud 營業利益率與 Gemini 生成式 AI 變現速度', noteEn: 'Cloud operating margin & Gemini AI monetization' },
 { sym: 'GOOGL', name: '谷歌 (Alphabet)', date: '2026-10-22', move: 5.5, noteZh: 'Google Cloud 營業利益率與 Gemini 生成式 AI 變現速度', noteEn: 'Cloud operating margin & Gemini AI monetization' },
 { sym: 'KLAC', name: '科磊', date: '2026-10-29', move: 7.2, noteZh: '先進晶圓檢測機台訂單與非中國區先進封裝動能', noteEn: 'Wafer inspection orders & advanced packaging momentum' },
 { sym: 'ORCL', name: '甲骨文', date: '2026-12-08', move: 7.0, noteZh: 'OCI 雲端合約殘存履約價值 (RPO) 與多雲串接營收', noteEn: 'OCI Remaining Performance Obligations (RPO) growth' },
 { sym: 'NU', name: 'Nu Holdings', date: '2026-11-12', move: 9.5, noteZh: '墨西哥/哥倫比亞新戶開戶數與淨利差 (NIM) 擴張', noteEn: 'Mexico/Colombia expansion and NIM trajectory' },
 { sym: 'OKLO', name: 'Oklo', date: '2026-11-10', move: 18.0, noteZh: '核能監管委員會 (NRC) 審查進度與科技大廠 PPA 購電協議', noteEn: 'NRC licensing progress & AI hyperscaler power agreements' },
 { sym: 'SMR', name: 'NuScale Power', date: '2026-11-06', move: 16.5, noteZh: '小型核反應爐商轉現金消耗率與合作夥伴投資落地', noteEn: 'SMR commercialization cash burn & partner capital' },
 { sym: 'SPCX', name: 'SPAC ETF', date: '2026-11-20', move: 4.0, noteZh: '成分股合併進度與併購套利溢價走勢', noteEn: 'De-SPAC completion & arbitrage spreads' },
 { sym: 'AAPL', name: '蘋果', date: '2026-10-31', move: 4.8, noteZh: 'Apple Intelligence 換機潮與服務營收年增率', noteEn: 'Apple Intelligence upgrade cycle & Services growth' },
 { sym: 'MSFT', name: '微軟', date: '2026-10-24', move: 5.0, noteZh: 'Azure AI 算力營收貢獻與 Copilot 商業席次數', noteEn: 'Azure AI contribution & Copilot enterprise seats' },
 { sym: 'AMZN', name: '亞馬遜', date: '2026-10-29', move: 6.2, noteZh: 'AWS 成長再加速與零售北美營業利益率', noteEn: 'AWS re-acceleration & North America operating margins' },
 { sym: 'META', name: 'Meta', date: '2026-10-23', move: 7.5, noteZh: '廣告曝光單價年增率與 2026 基礎設施資本支出', noteEn: 'Ad impression pricing & infrastructure capex guidance' },
 { sym: 'AMD', name: '超微', date: '2026-10-29', move: 8.0, noteZh: 'MI325X / MI350 AI 晶片出貨量與營收指引', noteEn: 'MI325X/MI350 GPU shipments & data center guidance' },
 { sym: 'ASML', name: '艾司摩爾', date: '2026-10-16', move: 7.0, noteZh: 'High-NA EUV 訂單簽約量與 2026 全年展望', noteEn: 'High-NA EUV net bookings & full-year guidance' },
 { sym: 'PLTR', name: 'Palantir', date: '2026-11-04', move: 12.0, noteZh: '美國商業市場 AIP 訓練營轉化合約數', noteEn: 'US commercial AIP bootcamps conversion & revenue' }
];

function renderEarnings(rows, tot){
 var x = document.getElementById('pfearn');
 if(!x) return;
 x.textContent = '';
 if(!rows.length){ x.style.display = 'none'; return; }

 var matched = [];
 var now = Date.now();
 rows.forEach(function(r){
  var sym = ((r.p && r.p.sym) || r.h.s || '').toUpperCase();
  var key = sym.replace(/\.(TW|TWO)$/,'');
  var item = EARNINGS_CAL.find(function(c){ return c.sym === key || c.sym === sym; });
  if(item){
   var t = new Date(item.date).getTime();
   var days = Math.ceil((t - now) / (86400 * 1000));
   var dollarImp = (r.vt || 0) * (item.move / 100);
   var navPct = tot > 0 ? (dollarImp / tot * 100) : 0;
   matched.push({
    sym: sym,
    name: (r.p && r.p.name) || item.name,
    date: item.date,
    days: days,
    move: item.move,
    vt: r.vt || 0,
    dollarImp: dollarImp,
    navPct: navPct,
    noteZh: item.noteZh,
    noteEn: item.noteEn
   });
  }
 });

 if(!matched.length){ x.style.display = 'none'; return; }
 x.style.display = 'block';

 matched.sort(function(a, b){ return a.days - b.days; });

 var hd = el('h3', '');
 hd.appendChild(L('🎯 個人持股專屬財報倒數與隱含波動雷達', 'Earnings Countdown & Implied Volatility Radar'));
 x.appendChild(hd);
 var sub = el('p', 'muted small');
 sub.appendChild(L('追蹤您目前持有的標的即將發布財報之倒數日程、選擇權隱含跳空幅度 (±%) 與對總資產的跳空震撼度',
                  'Track upcoming earnings dates, options implied moves, and dollar risk for your holdings.'));
 x.appendChild(sub);

 var grid = el('div', 'pfearn-grid');
 matched.forEach(function(m){
  var card = el('div', 'pfearn-card');
  var head = el('div', 'pfearn-head');
  var symEl = el('span', 'pfearn-sym', m.sym + ' ' + m.name);
  head.appendChild(symEl);

  var daysCls = m.days <= 3 ? 'urgent' : (m.days <= 7 ? 'warn' : 'normal');
  var daysText = m.days <= 0 ? (m.days === 0 ? '今日公布！' : '甫公布') : ('倒數 ' + m.days + ' 天');
  var daysTextEn = m.days <= 0 ? (m.days === 0 ? 'Today!' : 'Recent') : (m.days + 'd left');
  var badge = el('span', 'pfearn-days ' + daysCls);
  badge.appendChild(L(daysText, daysTextEn));
  head.appendChild(badge);
  card.appendChild(head);

  function addRow(lblZh, lblEn, valText, valCls){
   var r = el('div', 'pfearn-row');
   r.appendChild(L(lblZh, lblEn));
   var b = el('b', valCls || '', valText);
   r.appendChild(b);
   card.appendChild(r);
  }
  addRow('預計發布日期', 'Date', m.date);
  addRow('選擇權隱含跳空', 'Implied Move', '±' + num(m.move, 1) + '%', 'warn');
  addRow('持股總市值', 'Holding Value', 'NT$ ' + num(m.vt, 0));
  addRow('跳空對淨值衝擊', 'NAV Impact', '±NT$ ' + num(m.dollarImp, 0) + ' (±' + num(m.navPct, 1) + '%)', m.navPct >= 3 ? 'dn' : '');

  var desc = el('div', 'pfearn-desc');
  desc.appendChild(L('🔍 觀察重點：' + m.noteZh, 'Focus: ' + m.noteEn));
  card.appendChild(desc);

  grid.appendChild(card);
 });
 x.appendChild(grid);

 var tip = el('div', 'pfdx-item act');
 tip.style.marginTop = '10px';
 tip.appendChild(el('span', 'ico', '💡'));
 var tipDesc = el('div', 'desc');
 tipDesc.appendChild(L('財報避震提醒：倒數 7 天以內的持股若單檔對淨值衝擊 > ±2.5%，公布當日跳空容易造成總資產劇烈洗盤。可考慮在公布前保留部分現金或設定防守防護。',
                       'Earnings Risk Tip: If implied move impacts NAV by > ±2.5%, consider building cash buffer or setting stops before announcement.'));
 tip.appendChild(tipDesc);
 x.appendChild(tip);
}

// ---------------------------------------------------------------- Form & Events
function upsert(d,s,n,c){var k=norm(s);if(!k||!(n>=0))return false;var key=k.key,i=d.h.findIndex(function(h){var x=norm(h.s);return x&&x.key===key;});
 if(n===0){if(i>=0)d.h.splice(i,1);return true;}var row={s:key,n:n,c:(c>0?c:0),p:0};if(i>=0){row.p=d.h[i].p||0;if(!(c>0))row.c=d.h[i].c||0;d.h[i]=row;}else d.h.push(row);return true;}
document.getElementById('pfadd').addEventListener('submit',function(e){e.preventDefault();var f=e.target,d=get();
 if(upsert(d,f.s.value,parseFloat(f.n.value),parseFloat(f.c.value))){put(d);f.reset();render();}else msg(['代號或股數格式不對','Check the ticker / shares']);});
document.getElementById('pfcash').addEventListener('submit',function(e){e.preventDefault();var f=e.target,d=get(),a=parseFloat(f.a.value);if(!isFinite(a))return;
 d.cash=(d.cash||[]).filter(function(c){return c.cur!==f.cur.value;});if(a)d.cash.push({cur:f.cur.value,a:a});put(d);f.a.value='';render();});
document.getElementById('pfpastebtn').addEventListener('click',function(){var d=get(),ok=0,bad=0,agg={};
 document.getElementById('pfpaste').value.split(/\r?\n/).forEach(function(line){var p=line.trim().split(/[\s,，\t]+/);if(!p[0])return;
  var s=p[0],n=parseFloat(p[1]),c=parseFloat(String(p[2]||'').replace(/\.+/g,'.'));
  var k=norm(s);if(!k||!(n>=0)){bad++;return;}
  var key=k.key;
  if(!agg[key])agg[key]={n:0,cost:0,hasC:false};
  agg[key].n+=n;
  if(c>0){agg[key].cost+=n*c;agg[key].hasC=true;}
  ok++;});
 Object.keys(agg).forEach(function(key){
  var item=agg[key],avgC=item.hasC&&(item.n>0)?(item.cost/item.n):0;
  upsert(d,key,item.n,avgC);
 });
 put(d);document.getElementById('pfpaste').value='';render();
 setTimeout(function(){msg(['已加入 '+ok+' 筆'+(bad?'，'+bad+' 行格式不對':''),'Added '+ok+(bad?', '+bad+' lines skipped':'')]);},50);});
document.getElementById('pfexp').addEventListener('click',function(){var b=new Blob([JSON.stringify(get(),null,1)],{type:'application/json'}),a=document.createElement('a');
 a.href=URL.createObjectURL(b);a.download='my_holdings_'+new Date().toISOString().slice(0,10)+'.json';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},500);});
document.getElementById('pfimp').addEventListener('change',function(e){var f=e.target.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){try{var d=JSON.parse(rd.result);
  if(!d||!Array.isArray(d.h))throw 0;var clean={v:1,h:[],cash:[],nav:[]};d.h.forEach(function(h){if(h&&norm(h.s)&&h.n>=0)clean.h.push({s:norm(h.s).key,n:+h.n,c:+h.c>0?+h.c:0,p:+h.p>0?+h.p:0});});
  (d.cash||[]).forEach(function(c){if(c&&['TWD','USD','HKD'].indexOf(c.cur)>=0&&isFinite(+c.a))clean.cash.push({cur:c.cur,a:+c.a});});
  if(Array.isArray(d.nav))clean.nav=d.nav;
  put(clean);render();setTimeout(function(){msg(['已匯入 '+clean.h.length+' 檔持股','Imported '+clean.h.length+' holdings']);},50);}catch(x){msg(['檔案格式不對','Invalid file']);}};rd.readAsText(f);e.target.value='';});
document.getElementById('pfclr').addEventListener('click',function(){if(confirm(en()?'Delete all holdings and cash stored in this browser?':'確定刪除這個瀏覽器裡的所有持股與現金？（建議先匯出備份）')){try{localStorage.removeItem(KEY);}catch(e){}render();}});
document.getElementById('langBtn')&&document.getElementById('langBtn').addEventListener('click',function(){setTimeout(render,0);});
render();})();
"""
