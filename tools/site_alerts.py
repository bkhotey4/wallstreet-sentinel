"""VIX 拆解 card + 網頁警示 (bell, pop-up, optional desktop notification).

The alert list is embedded in the page and also written to alerts.json; an open page polls alerts.json every 3 minutes
(even in a background tab, so a desktop notification can fire) and remembers in localStorage which alerts it has shown."""
from __future__ import annotations

import json
from typing import Dict

from tools.sitekit import T, card, cls, esc, num


def sec_vix_explain(eng, only_hot: bool = False) -> str:
    from wsb.analytics import vix_explain as VX
    try:
        r = VX.build(eng)
    except Exception:  # noqa: BLE001
        return ""
    if not r.get("available") or (only_hot and not r.get("hot")):
        return ""
    from tools.site_quant import _takeaways
    body = _takeaways(VX.readings(r)).replace(T("今天的重點", "What matters today"), T("VIX 為什麼動", "Why VIX moved"))
    sv = r.get("spot_vol")
    kv = (f'<div class="kv"><div><span class="muted">VIX</span><b>{num(r["vix"], 2)}</b><span class="small {cls(r["chg_pct"])}">{num(r["chg_pct"], 1, sign=True, pct=True)}</span></div>'
          f'<div><span class="muted">{T("近一年百分位", "1y pctile")}</span><b>{num(r.get("pct_1y"), 0)}</b></div>'
          + (f'<div><span class="muted">{T("大盤跌幅解釋的部分", "Explained by the index")}</span><b>{num(sv["expected"], 2, sign=True)}</b>'
             f'<span class="small muted">{T("額外", "extra")} {num(sv["extra"], 2, sign=True)}（{num(sv.get("z"), 1, sign=True)}σ）</span></div>' if sv else "")
          + (f'<div><span class="muted">VIX9D ÷ VIX</span><b>{num(r.get("r9d"), 2)}</b></div>' if r.get("r9d") is not None else "")
          + (f'<div><span class="muted">VIX ÷ VIX3M</span><b class="{"dn" if (r.get("r3m") or 0) > 1 else ""}">{num(r.get("r3m"), 2)}</b>'
             f'<span class="small muted">{T("> 1 為倒掛", "> 1 = inverted")}</span></div>' if r.get("r3m") is not None else "")
          + (f'<div><span class="muted">VVIX</span><b>{num(r.get("vvix"), 1)}</b><span class="small {cls(r.get("vvix_chg"))}">{num(r.get("vvix_chg"), 1, sign=True, pct=True)}</span></div>' if r.get("vvix") else "")
          + "</div>")

    def rows(items):
        return "".join(f'<tr><td>{T(x["zh"], x["en"])}</td><td class="r {cls(x["chg"])}"><b>{num(x["chg"], 2, sign=True, pct=True)}</b></td>'
                       f'<td class="r">{(num(x["sigma"], 1, sign=True) + "σ") if x.get("sigma") is not None else "—"}</td></tr>' for x in items)
    cross = "".join(f'<tr><td>{T(x["zh"], x["en"])}</td><td class="r {cls(x["chg"])}">'
                    + (f'{num(x["bp"], 0, sign=True)} bp' if x.get("bp") is not None else num(x["chg"], 2, sign=True, pct=True))
                    + f'</td><td class="r">{(num(x["sigma"], 1, sign=True) + "σ") if x.get("sigma") is not None else "—"}</td></tr>' for x in r.get("cross", []))
    head = f'<thead><tr><th></th><th class="r">{T("今天", "Today")}</th><th class="r">{T("自身波動倍數", "σ")}</th></tr></thead>'
    body += kv + ('<div class="cols2" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px">'
                  f'<div><h3>{T("賣壓在哪裡", "Where the selling was")}</h3><table class="mini">{head}<tbody>{rows(r.get("equity", []) + r.get("sectors", [])[:4])}</tbody></table></div>'
                  f'<div><h3>{T("其他市場有沒有跟著", "Did other markets confirm")}</h3><table class="mini">{head}<tbody>{cross}</tbody></table></div></div>')
    wl = VX.watchlist(r)
    if wl:
        def wrow(x):
            mark = ("🔴 " + T("已發生", "on")) if x["on"] and x["side"] == "up" else ("🟢 " + T("已發生", "on")) if x["on"] else ("⏳ " + T("還沒", "not yet"))
            return f'<tr><td>{esc(x["zh"])}</td><td class="r">{esc(x["now"])}</td><td class="r nw">{mark}</td></tr>'
        up, dn = [x for x in wl if x["side"] == "up"], [x for x in wl if x["side"] == "down"]
        th = f'<thead><tr><th>{T("條件", "Condition")}</th><th class="r">{T("目前", "Now")}</th><th class="r">{T("狀態", "Status")}</th></tr></thead>'
        body += (f'<h3>{T("接下來要看的訊號", "What to watch next")}</h3><p class="small muted">'
                 f'{T("上半部出現越多，代表波動在升級；下半部出現，代表恐慌在退潮。這是要觀察的條件，不是買賣建議。", "Top half = escalation, bottom half = calming. Conditions to watch, not advice.")}</p>'
                 f'<table class="mini">{th}<tbody><tr><td colspan="3" class="small muted">{T("⬆ 升級訊號", "⬆ Escalation")}</td></tr>{"".join(wrow(x) for x in up)}'
                 f'<tr><td colspan="3" class="small muted">{T("⬇ 退潮訊號", "⬇ Calming")}</td></tr>{"".join(wrow(x) for x in dn)}</tbody></table>')
    note = T(f"只用價格數據拆解（新聞不列入）。「大盤跌幅解釋的部分」＝{('過去 ' + str(sv['n']) + ' 個交易日') if sv else '近一年'} VIX 點數變動對標普報酬的迴歸；"
             "σ＝今天的漲跌是自己近 60 日日波動的幾倍。VIX 25／35 的回測數字來自「大盤警報規則回測」。報價約延遲 15 分鐘。不是預測，也不是投資建議。",
             "Price data only. Explained part = regression of VIX point changes on S&P returns; σ = today's move in units of its own daily vol. Not a forecast or advice.")
    return card("VIX 拆解：恐慌指數為什麼動", "VIX breakdown: why the fear gauge moved", body + f'<p class="note">{note}　{T("資料日", "As of")} {esc(r.get("asof") or "")}</p>', "wide")


def sec_vix_hot(eng) -> str:
    """總覽: the same card, only on days VIX jumps (≥ vix_explain.hot_pct) or sits above hot_level."""
    return sec_vix_explain(eng, only_hot=True)


def alerts_payload(eng) -> Dict:
    from wsb.analytics import web_alerts as WA
    try:
        return WA.build(eng)
    except Exception:  # noqa: BLE001
        return {"ts": 0, "items": []}


def bell_html(payload: Dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (f'<button class="btn bell" id="bellBtn" type="button" aria-label="alerts">🔔<span id="bellN"></span></button>'
            f'<script type="application/json" id="alert-data">{data}</script>')


MODAL_HTML = '''<div id="almodal" class="almodal" hidden><div class="albox" role="dialog" aria-modal="true" aria-labelledby="alttl">
<div class="alhead"><b id="alttl"></b><button class="btn" id="alclose" type="button">✕</button></div><div id="allist"></div>
<p class="small muted" id="alfoot"></p><div class="albtn"><button class="btn" id="alnotify" type="button"></button><button class="btn" id="alok" type="button"></button></div></div></div>'''

CSS = """.bell{position:relative}.bell #bellN{position:absolute;top:-6px;right:-6px;background:var(--dn);color:#fff;border-radius:9px;font-size:10px;padding:0 5px;line-height:16px;min-width:16px}
.bell #bellN:empty{display:none}.bell.quiet #bellN{background:var(--mu)}
.almodal{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;display:flex;align-items:flex-start;justify-content:center;padding:60px 16px 16px}
.almodal[hidden]{display:none}.albox{background:var(--card);border:1px solid var(--bd);border-radius:14px;max-width:560px;width:100%;max-height:80vh;overflow:auto;padding:14px 16px;box-shadow:0 10px 40px rgba(0,0,0,.5)}
.alhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:16px}
.alit{border-left:3px solid var(--mu);padding:6px 10px;margin:6px 0;background:var(--card2);border-radius:6px}.alit.alert{border-color:var(--dn)}.alit.new{box-shadow:0 0 0 1px var(--dn) inset}
.alit .t{font-weight:600;line-height:1.45}.alit .d{font-size:12px;color:var(--tx2);margin-top:3px;line-height:1.5}.alit a{font-size:12px}
.albtn{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}"""

JS = r"""
// 網頁警示: the alert list rides in the page; alerts.json is polled every 3 min even in a background tab
(function(){var el=document.getElementById('alert-data'),btn=document.getElementById('bellBtn'),md=document.getElementById('almodal');if(!el||!btn||!md)return;
 var SK='wss_alert_seen_v1',cur={items:[]};try{cur=JSON.parse(el.textContent)||cur;}catch(e){}
 function zh(){return document.documentElement.lang!=='en';}
 function seen(){try{return JSON.parse(localStorage.getItem(SK)||'{}');}catch(e){return {};}}
 function save(s){try{var k=Object.keys(s);if(k.length>300){k.sort(function(a,b){return s[a]-s[b];});k.slice(0,k.length-300).forEach(function(x){delete s[x];});}
  localStorage.setItem(SK,JSON.stringify(s));}catch(e){}}
 function esc(t){return String(t||'').replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
 function fresh(d){var s=seen();return (d.items||[]).filter(function(x){return x.lv==='alert'&&!s[x.key];});}
 function badge(d){var s=seen(),it=d.items||[],a=it.filter(function(x){return x.lv==='alert';}).length,
  un=it.filter(function(x){return !s[x.key];}),ua=un.filter(function(x){return x.lv==='alert';}).length;
  document.getElementById('bellN').textContent=un.length?String(ua||un.length):'';btn.classList.toggle('quiet',!ua);
  btn.title=zh()?(a?a+' 則警示':'目前沒有警示'):(a?a+' alerts':'No alerts');}
 function open(d,news){var s=seen(),L=document.getElementById('allist');
  document.getElementById('alttl').textContent=zh()?(news.length?'⚠️ 市場警示（'+news.length+' 則新的）':'🔔 目前的市場警示'):(news.length?'⚠️ Market alerts ('+news.length+' new)':'🔔 Current market alerts');
  L.innerHTML=(d.items||[]).length?(d.items||[]).map(function(x){var nw=x.lv==='alert'&&!s[x.key];
   return '<div class="alit '+x.lv+(nw?' new':'')+'"><div class="t">'+(x.lv==='alert'?'🔴 ':'🟡 ')+esc(zh()?x.zh:(x.en||x.zh))+'</div>'+(x.detail&&zh()?'<div class="d">'+esc(x.detail)+'</div>':'')
    +(x.tab?'<a href="#'+esc(x.tab)+'" class="algo" data-p="'+esc(x.tab)+'">'+(zh()?'看相關卡片 →':'Open the card →')+'</a>':'')+'</div>';}).join('')
   :'<p class="muted">'+(zh()?'目前沒有觸發任何警示規則。':'No alert rule is firing right now.')+'</p>';
  L.querySelectorAll('a.algo').forEach(function(a){a.addEventListener('click',function(ev){ev.preventDefault();close(d);if(typeof page==='function')page(a.dataset.p);else location.hash=a.dataset.p;
   try{history.replaceState(null,'','#'+a.dataset.p);}catch(e){}window.scrollTo(0,0);});});
  document.getElementById('alfoot').textContent=zh()?'規則與 Discord 警報相同、只用公開市場數據（不含持股，新聞不列入）；網站約每 20 分鐘更新、報價約延遲 15 分鐘。這是風險提示，不是預測，也不是買賣建議。'
   :'Same rules as the Discord alerts, public market data only. Updated ~20 min, quotes ~15 min delayed. A risk notice, not a forecast or advice.';
  var nb=document.getElementById('alnotify');
  if(!('Notification' in window)){nb.hidden=true;}else{nb.hidden=Notification.permission==='granted';
   nb.textContent=Notification.permission==='denied'?(zh()?'桌面通知已被瀏覽器封鎖':'Notifications blocked'):(zh()?'開啟桌面通知':'Turn on desktop notifications');nb.disabled=Notification.permission==='denied';}
  document.getElementById('alok').textContent=zh()?'知道了':'Got it';md.hidden=false;}
 function close(d){var s=seen(),t=Date.now();(d.items||[]).forEach(function(x){if(!s[x.key])s[x.key]=t;});save(s);md.hidden=true;badge(d);}
 function notify(list){if(!('Notification' in window)||Notification.permission!=='granted'||!list.length)return;
  try{var n=new Notification(zh()?'⚠️ WallStreet Sentinel 市場警示':'⚠️ WallStreet Sentinel alert',{body:list.map(function(x){return zh()?x.zh:(x.en||x.zh);}).slice(0,4).join('\n'),tag:'wss-'+list[0].key,icon:'favicon-64.png'});
   n.onclick=function(){window.focus();open(cur,list);n.close();};}catch(e){}}
 function show(d){cur=d;badge(d);var nw=fresh(d);if(nw.length){if(document.hidden)notify(nw);open(d,nw);}}
 btn.addEventListener('click',function(){open(cur,fresh(cur));});
 document.getElementById('alok').addEventListener('click',function(){close(cur);});document.getElementById('alclose').addEventListener('click',function(){close(cur);});
 md.addEventListener('click',function(ev){if(ev.target===md)close(cur);});
 document.getElementById('alnotify').addEventListener('click',function(){if(!('Notification' in window))return;Notification.requestPermission().then(function(){open(cur,fresh(cur));});});
 function poll(){if(!window.fetch)return;fetch('alerts.json?t='+Date.now(),{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();})
  .then(function(d){if(d&&+d.ts>=+(cur.ts||0))show(d);}).catch(function(){});}
 setTimeout(function(){show(cur);},600);setInterval(poll,180000);})();
"""


def sec_fomc_drift(eng) -> str:
    from wsb.analytics import fomc_drift as FD
    try:
        r = FD.build(eng)
    except Exception:  # noqa: BLE001
        return ""
    if not r.get("available"):
        return ""
    from tools.site_quant import _takeaways
    body = _takeaways(FD.readings(r)).replace(T("今天的重點", "What matters today"), T("歷史怎麼說", "What history says"))
    head = (f'<thead><tr><th>{T("樣本", "Sample")}</th>' + "".join(f'<th class="r">{T(zh, en)}</th>' for _, zh, en in FD.WINS) + "</tr></thead>")

    def cell(st):
        if not st:
            return '<td class="r">—</td>'
        return (f'<td class="r"><b class="{cls(st["mean"])}">{num(st["mean"], 2, sign=True, pct=True)}</b>'
                f'<span class="small muted"> ↑{num(st["up"], 0)}%｜{T("平常", "base")} {num(st["base_mean"], 2, sign=True, pct=True)}｜t {num(st["t"], 1, sign=True)}</span></td>')
    rows = "".join(f'<tr><td>{T(g["zh"], g["en"])}<span class="small muted"> n={(g.get("pre") or {}).get("n", "—")}</span></td>'
                   + "".join(cell(g.get(w)) for w, _, _ in FD.WINS) + "</tr>" for g in r["stats"].values())
    rec = "".join(f'<tr><td>{esc(x["date"])}</td>' + "".join(f'<td class="r {cls(x[w])}">{num(x[w], 2, sign=True, pct=True)}</td>' for w, _, _ in FD.WINS)
                  + f'<td class="r">{num(x["vix"], 1)}</td></tr>' for x in r["recent"])
    body += (f'<div class="scroll"><table class="mini">{head}<tbody>{rows}</tbody></table></div>'
             f'<details class="hist"><summary class="small">{T("最近 8 次會議", "Last 8 meetings")}</summary><div class="scroll"><table class="mini">'
             f'<thead><tr><th>{T("決議日", "Decision")}</th>' + "".join(f'<th class="r">{T(zh, en)}</th>' for _, zh, en in FD.WINS)
             + f'<th class="r">{T("起點 VIX", "VIX at start")}</th></tr></thead><tbody>{rec}</tbody></table></div></details>'
             f'<p class="note">{T("會前＝決議日前 6 個交易日收盤到前 1 日收盤；平常＝同期間任何同長度窗口；t ≥ 2 才算統計上明顯。只用標普收盤價與聯準會會議日期，新聞不是輸入。歷史頻率、樣本小，不是預測，也不是買賣建議。", "Pre = close T-6 to T-1; base = any window of the same length in the same years; |t| ≥ 2 is meaningful. Closes and Fed dates only. Historical frequencies, not a forecast or advice.")}</p>')
    return card("FOMC 前漂移：會前有沒有上漲慣性", "Pre-FOMC drift", body, "wide")
