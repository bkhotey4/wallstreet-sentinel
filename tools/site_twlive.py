"""台股即時盤勢 + 每日台股解讀 (on the 台股 page): the Taiwan version of 開盤後即時盤勢 — the TAIEX move, which industries'
heavyweights carried it (25 names across semis, AI servers, finance, plastics, steel, telecom, food, shipping…), the
strongest / weakest industry with its usual clue (last night's US chips, oil), last night's US session and the TSMC ADR
premium, foreign investors' net buying, headlines that name the movers, and what changed against the last 5 / 20 sessions.
Live in the browser through /api/quote; after the 13:30 close the same read is archived per day (wsb.analytics.daily_why).
Describes, does not forecast; not advice."""
from __future__ import annotations

import html
import json

from tools.sitekit import T, card

CF_URL = "https://wallstreet-sentinel.pages.dev"
# the heaviest names of each industry (one request of 25)
LEAD = [("2330.TW", "台積電", "半導體"), ("2454.TW", "聯發科", "半導體"), ("3711.TW", "日月光投控", "半導體"),
        ("2317.TW", "鴻海", "電子代工"), ("2382.TW", "廣達", "AI 伺服器"), ("3231.TW", "緯創", "AI 伺服器"),
        ("2308.TW", "台達電", "電源零組件"), ("3008.TW", "大立光", "光學"), ("2357.TW", "華碩", "電腦品牌"),
        ("2881.TW", "富邦金", "金融"), ("2882.TW", "國泰金", "金融"), ("2891.TW", "中信金", "金融"), ("2886.TW", "兆豐金", "金融"),
        ("1301.TW", "台塑", "塑化"), ("1303.TW", "南亞", "塑化"), ("6505.TW", "台塑化", "油品"),
        ("2002.TW", "中鋼", "鋼鐵"), ("1101.TW", "台泥", "水泥"), ("2412.TW", "中華電", "電信"),
        ("1216.TW", "統一", "食品"), ("2912.TW", "統一超", "零售"), ("2603.TW", "長榮", "航運"),
        ("2609.TW", "陽明", "航運"), ("2207.TW", "和泰車", "汽車"), ("2105.TW", "正新", "橡膠")]
# gauges: index, last night's US session, the ADR, currency, oil
GAUGE = ["^TWII", "0050.TW", "TSM", "^SOX", "^GSPC", "TWD=X", "CL=F", "^VIX"]
# 和前幾天比
TREND = [("^TWII", "加權指數"), ("0050.TW", "元大台灣50"), ("2330.TW", "台積電"), ("2317.TW", "鴻海"), ("2454.TW", "聯發科"),
         ("2382.TW", "廣達"), ("3231.TW", "緯創"), ("2308.TW", "台達電"), ("2881.TW", "富邦金"), ("2882.TW", "國泰金"),
         ("2603.TW", "長榮"), ("2609.TW", "陽明"), ("1301.TW", "台塑"), ("2002.TW", "中鋼"), ("2412.TW", "中華電"),
         ("1216.TW", "統一"), ("0056.TW", "元大高股息"), ("00878.TW", "國泰永續高股息"), ("TWD=X", "美元兌台幣"), ("TSM", "台積電 ADR")]
CLUE = {"半導體": "chip", "AI 伺服器": "chip", "電子代工": "chip", "電源零組件": "chip", "光學": "chip", "電腦品牌": "chip",
        "塑化": "oil", "油品": "oil"}
NOTE = ("這些是同一時間的變化與新聞，幫助理解盤勢，不是確定的因果。產業強弱用各產業權值股的平均漲跌；昨晚美股與台積電 ADR 溢價來自前一晚收盤；"
        "外資買賣超是證交所前一個交易日的數字（盤中沒有即時資料）。「和前幾天比」：今天的方向和最近 5／20 天相反（反轉）或同向大幅加速才列出，"
        "平常一天＝過去一年每日漲跌的標準差。報價：Yahoo Finance，約有延遲。")


def tw_ctx(eng) -> dict:
    """Build-time clues: foreign investors' last sessions, foreign futures positions, and headline candidates tagged with
    the Taiwan names they mention (Chinese names matched in the title)."""
    tw = getattr(eng, "taiwan", None)
    out = {"flows": [], "news": []}
    if tw is not None:
        out["flows"] = sorted([{"d": f.get("date"), "f": f.get("foreign"), "t": f.get("trust")} for f in (tw.flows or [])
                               if f.get("foreign") is not None], key=lambda x: x["d"] or "")[-5:]      # oldest → newest
        fu = tw.futures or {}
        if fu.get("oi_foreign") is not None:
            out["fut"] = {"oi": fu.get("oi_foreign"), "chg": fu.get("oi_foreign_chg")}
    try:
        from tools.site_intraday import why_ctx
        cand = why_ctx(eng).get("news") or []
    except Exception:  # noqa: BLE001
        cand = []
    names = {n: s for s, n, _k in LEAD} | {"台積": "2330.TW", "鴻海": "2317.TW", "聯發科": "2454.TW", "TSMC": "2330.TW", "Foxconn": "2317.TW"}
    for n in cand:
        tws = [s for nm, s in names.items() if nm in n["t"]]
        if tws or "台股" in n["t"] or "Taiwan" in n["t"]:
            out["news"].append({**n, "s": list(dict.fromkeys((n.get("s") or []) + tws)), "k": (n.get("k") or []) + (["tw"] if "台股" in n["t"] or "Taiwan" in n["t"] else [])})
        elif n.get("k"):
            out["news"].append(n)
    out["news"] = out["news"][:60]
    return out


def sec_tw_live(eng) -> str:
    ctx = html.escape(json.dumps(tw_ctx(eng), ensure_ascii=False), quote=True)
    body = (f'<div id="twbox" data-ctx="{ctx}"><p class="small muted" id="twst">🕒 {T("等待即時報價…", "Waiting for live quotes…")}</p>'
            f'<p class="rimp big2"><b id="twone">{T("一句話看懂：台股盤中（09:00–13:30）這裡每分鐘自動整理盤勢。", "Live read of the Taiwan session.")}</b></p>'
            f'<div id="twwb" hidden><p><b>{T("🤔 為什麼？同時間發生的事", "Why?")}</b></p><ul id="twwhy"></ul>'
            f'<p><b>{T("📅 和前幾天比：今天哪裡變了方向", "Compared with recent days")}</b></p><ul id="twtr"><li class="muted">{T("載入最近 20 天的走勢…", "Loading…")}</li></ul>'
            f'<p class="small muted">{T(NOTE, "Same-time moves and news, not proven causes.")}</p></div></div>'
            f'<p class="lqoff" id="twoff">{T("即時盤勢只在 Cloudflare 版網址可用：", "Live only on the Cloudflare site: ")}'
            f'<a href="{CF_URL}/#taiwan" target="_blank" rel="noopener">{CF_URL.replace("https://", "")}</a></p>')
    return card("台股即時盤勢：今天怎麼走、為什麼", "Taiwan session, live", body, "wide")


def sec_tw_days(eng) -> str:
    """每日台股解讀: archived after-close read of each Taiwan session (newest first)."""
    from datetime import date as _d
    from wsb.analytics import daily_why as DW
    try:
        arc = DW.update_tw(eng)
    except Exception:  # noqa: BLE001
        arc = DW._load(DW.TW_DAYS)
    if not arc:
        return ""
    wd = "一二三四五六日"
    parts = []
    for i, (day, r) in enumerate(sorted(arc.items(), reverse=True)):
        news = "".join(f'<li>{html.escape(n["t"])}<span class="small muted">（對得上：{html.escape("、".join(n["why"]))}）</span></li>' for n in r.get("news") or [])
        body = ("<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in r.get("why") or [])
                + (news or ('<li class="muted">新聞：這一天是開始存檔前補建的，沒有當時的新聞可以比對。</li>' if r.get("backfill")
                            else '<li class="muted">新聞：沒有找到和當天實際大動的股票或產業對得上的新聞。</li>')) + "</ul>"
                + f'<p><b>{T("📅 和之前比", "Against the days before")}</b></p><ul>'
                + ("".join(f"<li>{html.escape(x)}</li>" for x in r["trend"]) if r.get("trend")
                   else "<li>權值股、高股息 ETF 與匯率大致延續之前的走勢，沒有明顯的反轉或加速。</li>") + "</ul>")
        parts.append(f'<details class="sgx"{" open" if i == 0 else ""}><summary><b>{day[5:]}（{wd[_d.fromisoformat(day).weekday()]}）</b> '
                     f'{html.escape(r["one"])}</summary>{body}</details>')
    lead = f"一句話看懂：每天台股收盤後自動存一份當天的盤勢解讀，可以往回對照前幾天（目前 {len(arc)} 天，最多保留 {DW.KEEP} 天）。"
    return card("每日台股解讀（可往回看）", "Daily Taiwan read (archive)", f'<p class="rimp big2"><b>{T(lead, "")}</b></p>' + "".join(parts), "wide")


_JS = r"""
(function(){var box=document.getElementById('twbox');if(!box)return;var LEAD=__LEAD__,GAUGE=__GAUGE__,TREND=__TREND__,CLUE=__CLUE__,C={},TRD={},trAt=0,dead=false;
 try{C=JSON.parse(box.getAttribute('data-ctx')||'{}');}catch(e){}
 function f(x,d){return x==null||isNaN(x)?'—':Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
 function sg(x,d){return x==null||isNaN(x)?'—':(x>0?'+':'')+f(x,d);}
 function tpe(){var p=new Intl.DateTimeFormat('en-US',{timeZone:'Asia/Taipei',weekday:'short',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date()),o={};
   p.forEach(function(x){o[x.type]=x.value;});return {wd:o.weekday,m:(+o.hour%24)*60+(+o.minute)};}
 function session(){var t=tpe();if(t.wd==='Sat'||t.wd==='Sun')return 'closed';return t.m>=540&&t.m<810?'open':t.m<540?'pre':'post';}
 function get(list,extra){return fetch('api/quote?s='+encodeURIComponent(list.join(','))+(extra||''),{cache:'no-store'}).then(function(r){if(r.status===404||r.status===405){dead=true;throw 0;}if(!r.ok)throw 0;return r.json();}).then(function(d){return d.q||{};});}
 // 和前幾天比 (same rule as the US card): reversal = today ≥1 normal day against a ≥1σ 5- or 20-day trend; acceleration = ≥2 normal days with it
 function trend(q){var out=[];TREND.forEach(function(m){var s=m[0],x=TRD[s];if(!x||!x.trend||!x.sd1y)return;var t=x.trend,lq=q[s]||x,pr=lq.price,pv=lq.prev||t.p0;if(pr==null||!pv)return;
   var ch=function(a,b){return (a/b-1)*100;},td=ch(pr,pv),d1=ch(t.p0,t.p1),r5=ch(t.p0,t.p5),r20=ch(t.p0,t.p20),sd=x.sd1y;
   var zt=td/sd,z5=r5/(sd*Math.sqrt(5)),z20=r20/(sd*Math.sqrt(20)),opp=function(r,z){return Math.abs(z)>=1&&(td>0)!==(r>0);};
   var rev=Math.abs(zt)>=1&&(opp(r5,z5)||opp(r20,z20)),acc=!rev&&Math.abs(zt)>=2&&(td>0)===(r5>0);
   if(rev||acc)out.push({s:s,n:m[1],td:td,d1:d1,r5:r5,r20:r20,sd:sd,rev:rev,sc:Math.abs(zt)*(rev?1.5:1)});});
   out.sort(function(a,b){return b.sc-a.sc;});return out.slice(0,6);}
 function trTxt(x){return x.n+'：今天 '+sg(x.td,1)+'%（平常一天 ±'+f(x.sd,1)+'%）；昨天 '+sg(x.d1,1)+'%、近 5 天 '+sg(x.r5,1)+'%、近 20 天 '+sg(x.r20,1)+'% → '
   +(x.rev?(x.td>0?'由跌轉漲':'由漲轉跌')+'，和最近的方向相反。':(x.td>0?'同方向加速上漲':'同方向加速下跌')+'，延續最近的走勢而且變快。');}
 function read(q){var tw=q['^TWII'];if(!tw||tw.chg==null)return null;var c=tw.chg,W=[],up=c>=0;
   var sd=(TRD['^TWII']||{}).sd1y;var one=(sd&&c<=-sd?'台股明顯走弱':sd&&c>=sd?'台股明顯走強':Math.abs(c)<0.3?'台股平盤整理':c<0?'台股小跌':'台股小漲')+'（加權指數 '+sg(c,2)+'%，'+f(tw.price,0)+' 點）';
   var mg=LEAD.map(function(m){var y=q[m[0]];return y&&y.chg!=null?{s:m[0],n:m[1],k:m[2],c:y.chg}:null;}).filter(Boolean);
   var byAbs=function(a,b){return Math.abs(b.c)-Math.abs(a.c);},nm=function(x){return x.k+'・'+x.n+' '+sg(x.c,1)+'%';};
   var w=mg.filter(function(x){return (x.c>0)===up&&Math.abs(x.c)>=1;}).sort(byAbs),a=mg.filter(function(x){return (x.c>0)!==up&&Math.abs(x.c)>=1;}).sort(byAbs);
   if(Math.abs(c)<0.3)W.push('漲跌幅很小，屬於平常的波動，沒有單一主因；下面是今天比較明顯的變化。');
   if(w.length||a.length)W.push('各產業權值股'+(up?'帶頭漲':'帶頭跌')+'：'+(w.length?w.slice(0,4).map(nm).join('、'):'沒有')+(a.length?'；反方向：'+a.slice(0,3).map(nm).join('、'):'')+'。');
   // industries: average of their heavyweights, the best and the worst with the clue that usually goes with them
   var g={};mg.forEach(function(x){(g[x.k]=g[x.k]||[]).push(x.c);});var ind=Object.keys(g).map(function(k){return {k:k,c:g[k].reduce(function(s,v){return s+v;},0)/g[k].length};}).sort(function(a,b){return b.c-a.c;});
   var sox=q['^SOX'],oil=q['CL=F'],tmn0=tpe().m,usNow=tmn0>=1290||tmn0<300,soxB=usNow?null:sox;   // tonight's US session came after this Taiwan session
   var clue=function(x){var t=CLUE[x.k];if(t==='chip'&&soxB&&soxB.chg!=null&&Math.abs(soxB.chg)>=1&&(soxB.chg>0)===(x.c>0))return '，呼應昨晚費城半導體 '+sg(soxB.chg,1)+'%';
     if(t==='oil'&&oil&&oil.chg!=null&&Math.abs(oil.chg)>=1&&(oil.chg>0)===(x.c>0))return '，跟著原油 '+sg(oil.chg,1)+'%';
     if((x.k==='金融'||x.k==='電信'||x.k==='食品')&&x.c>0&&c<0)return '，大盤跌時資金躲進防禦型';return '';};
   if(ind.length>=6){var hi=ind[0],lo=ind[ind.length-1];if(Math.abs(hi.c)>=0.8||Math.abs(lo.c)>=0.8)W.push('產業：'+hi.k+' '+sg(hi.c,1)+'% 最強'+clue(hi)+'；'+lo.k+' '+sg(lo.c,1)+'% 最弱'+clue(lo)+'。');}
   // last night in New York and the TSMC ADR premium (ADR = 5 shares)
   var tsm=q['TSM'],t2=q['2330.TW'],fx=q['TWD=X'],gs=q['^GSPC'];
   var tmn=tpe().m,usLive=tmn>=1290||tmn<300;                          // 21:30–05:00 Taipei: New York is trading now
   if(sox&&sox.chg!=null&&gs&&gs.chg!=null)W.push((usLive?'美股盤中（今晚）':'昨晚美股')+'：標普 '+sg(gs.chg,1)+'%、費城半導體 '+sg(sox.chg,1)+'%'+(tsm&&tsm.chg!=null?'、台積電 ADR '+sg(tsm.chg,1)+'%':'')
     +(Math.abs(sox.chg)>=1.5?'：'+(sox.chg>0?'半導體大漲，台股電子權值股'+(usLive?'明天':'')+'通常跟著開高。':'半導體大跌，台股電子權值股'+(usLive?'明天':'')+'通常跟著承壓。'):'。'));
   if(tsm&&t2&&fx&&t2.price){var pm=(tsm.price*fx.price/(t2.price*5)-1)*100;if(Math.abs(pm)>=8)W.push('台積電 ADR 溢價 '+sg(pm,0)+'%：'+(pm>0?'美國投資人願意付比台股更高的價格，代表外資對台積電看法偏正面。':'ADR 比台股便宜，外資態度偏保守。'));}
   if(fx&&fx.chg!=null&&Math.abs(fx.chg)>=0.3)W.push('美元兌台幣 '+sg(fx.chg,2)+'%：'+(fx.chg>0?'台幣貶值，外資可能在匯出（賣台股換美元）。':'台幣升值，常伴隨外資匯入買台股。'));
   var fl=C.flows||[];if(fl.length){var L=fl[fl.length-1],s5=fl.reduce(function(s,x){return s+(x.f||0);},0),age=(Date.now()-new Date(L.d+'T15:00:00+08:00'))/864e5;
     W.push((age>5?'（外資資料停在 '+String(L.d).slice(5)+'，較舊）':'')+'外資（'+String(L.d).slice(5)+'）買賣超 '+sg(L.f,1)+' 億、近 '+fl.length+' 日合計 '+sg(s5,0)+' 億'+(C.fut&&C.fut.oi!=null?'；外資台指期淨'+(C.fut.oi>=0?'多':'空')+'單 '+f(Math.abs(C.fut.oi),0)+' 口':'')+'。');}
   // headlines that name a mover (Chinese names matched at build time) or a moving theme
   var MV={};mg.forEach(function(x){if(Math.abs(x.c)>=1)MV[x.s]=x.n+' '+sg(x.c,1)+'%';});
   var TP={};if(soxB&&soxB.chg!=null&&Math.abs(soxB.chg)>=1.5){TP.chip=['昨晚費半 '+sg(soxB.chg,1)+'%',2];TP.ai=['昨晚費半 '+sg(soxB.chg,1)+'%',1];}
   if(Math.abs(c)>=1)TP.tw=['台股 '+sg(c,1)+'%',2];if(oil&&oil.chg!=null&&Math.abs(oil.chg)>=2)TP.power=['原油 '+sg(oil.chg,1)+'%',2];
   var tm=tpe(),cut=Date.now()/1000-(tm.m+600)*60;                       // since 13:30 Taipei the day before
   var hit=(C.news||[]).filter(function(n){return n.ts>=cut;}).map(function(n){var sc=0,why=[],kk=n.k||[];
     (n.s||[]).forEach(function(s){if(MV[s]){sc+=kk.length?3:2;why.push('提到 '+MV[s]);}});
     kk.forEach(function(k){if(TP[k]){sc+=TP[k][1];why.push(TP[k][0]);}});return {n:n,sc:sc,why:why};})
     .filter(function(x){return x.sc>=2;}).sort(function(a,b){return b.sc-a.sc||b.n.ts-a.n.ts;}).slice(0,3);
   hit.forEach(function(x){W.push({t:'新聞：'+x.n.t+'（對得上：'+x.why.filter(function(v,i,a){return a.indexOf(v)===i;}).join('、')+'）',l:x.n.l});});
   if(!hit.length)W.push('新聞：沒有找到和今天實際大動的股票或產業對得上的新聞，所以不列。');
   return {one:'一句話看懂（台股）：'+one+'。',W:W};}
 function draw(q){var o=read(q);if(!o)return;var ss=session();
   document.getElementById('twone').textContent=o.one+(ss==='open'?'':'（台股目前'+(ss==='pre'?'尚未開盤':'已收盤')+'，以下是最近一個交易日）');
   var ul=document.getElementById('twwhy');ul.textContent='';o.W.forEach(function(x){var li=document.createElement('li');
     if(typeof x==='string')li.textContent=x;else if(x.l){var a=document.createElement('a');a.href=x.l;a.target='_blank';a.rel='noopener';a.textContent=x.t;li.appendChild(a);}else li.textContent=x.t;ul.appendChild(li);});
   var tu=document.getElementById('twtr'),Tr=trend(q);tu.textContent='';
   var ru=Tr.filter(function(x){return x.rev&&x.td>0;}).map(function(x){return x.n;}),rd=Tr.filter(function(x){return x.rev&&x.td<0;}).map(function(x){return x.n;});
   var L=(ru.length||rd.length?['和最近不同的是：'+(ru.length?ru.join('、')+' 由跌轉漲':'')+(ru.length&&rd.length?'；':'')+(rd.length?rd.join('、')+' 由漲轉跌':'')+'。']:[]).concat(Tr.map(trTxt));
   (L.length?L:[Object.keys(TRD).length?'權值股、高股息 ETF 與匯率大致延續最近的走勢，沒有明顯的反轉或加速。':'最近 20 天的走勢暫時取不到。'])
   .forEach(function(s){var li=document.createElement('li');li.textContent=s;tu.appendChild(li);});
   document.getElementById('twwb').hidden=false;var st=document.getElementById('twst');
   if(st)st.textContent='🕒 最後更新 '+new Date().toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Asia/Taipei'})+'（台北）・盤中每分鐘自動更新';}
 function pull(){if(dead||document.hidden)return;var syms=GAUGE;
   Promise.all([get(LEAD.map(function(x){return x[0];})),get(syms),Date.now()-trAt>600000?get(TREND.map(function(x){return x[0];}),'&full=1'):Promise.resolve(null)])
   .then(function(r){var q={};Object.keys(r[0]).forEach(function(k){q[k]=r[0][k];});Object.keys(r[1]).forEach(function(k){q[k]=r[1][k];});
     if(r[2]){TRD=r[2];trAt=Date.now();}var off=document.getElementById('twoff');if(off)off.hidden=true;draw(q);}).catch(function(){});}
 pull();setInterval(function(){if(session()==='open'||!trAt)pull();},60000);document.addEventListener('visibilitychange',function(){if(!document.hidden)pull();});
})();
"""
JS = (_JS.replace("__LEAD__", json.dumps(LEAD, ensure_ascii=False)).replace("__GAUGE__", json.dumps(GAUGE))
      .replace("__TREND__", json.dumps(TREND, ensure_ascii=False)).replace("__CLUE__", json.dumps(CLUE, ensure_ascii=False)))
