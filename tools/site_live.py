"""即時層：在 Cloudflare 版網址（有 /api/quote）上，頂端行情列每分鐘自己更新、盤中急跌門檻即時亮燈、可查任何股票。
GitHub Pages 版沒有 /api/quote：第一次請求失敗就安靜停用，頁面維持整點建置的數字。模型結論仍每小時更新，即時層只顯示原始數字與簡單門檻。"""
from __future__ import annotations

import html
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
# 異常波動掃描: every market here is judged against its OWN normal daily move (1-year standard deviation, computed at
# each hourly build); |today| >= 2x normal -> yellow, >= 3x -> red.  Index futures trade overnight, so they cover pre-market.
ANOM = [("ES=F", "標普期貨", "S&P futures"), ("NQ=F", "那指期貨", "Nasdaq futures"), ("^GSPC", "標普 500", "S&P 500"), ("^NDX", "那指 100", "Nasdaq 100"),
        ("^SOX", "費城半導體", "SOX"), ("^TWII", "台股加權", "TAIEX"), ("^N225", "日經 225", "Nikkei"), ("^KS11", "韓國股市", "KOSPI"),
        ("^VIX", "VIX", "VIX"), ("^TNX", "美債 10 年殖利率", "10Y yield"), ("DX-Y.NYB", "美元指數", "Dollar index"), ("JPY=X", "美元兌日圓", "USD/JPY"),
        ("TWD=X", "美元兌台幣", "USD/TWD"), ("GC=F", "黃金", "Gold"), ("BZ=F", "布蘭特原油", "Brent"), ("BTC-USD", "比特幣", "Bitcoin"), ("HYG", "高收益債 ETF", "HYG")]
ANOM_Y, ANOM_R = 2.0, 3.0
# which direction is the stress for each market (default: a fall).  A big move the other way is shown green, not as a warning
BAD_UP = ("^VIX", "^TNX", "DX-Y.NYB", "TWD=X", "BZ=F")       # fear, rates, dollar, TWD weakness, oil spikes
NEUTRAL = ("GC=F",)                                           # gold: a spike can be fear or inflation — just shown, never green
# 大量賣壓: volume so far today vs the same time of day on the previous 4 days (5-minute bars), with the price direction
VOLS = [("SPY", "標普 ETF（SPY）", "SPY", "down"), ("QQQ", "那指 ETF（QQQ）", "QQQ", "down"),
        ("SQQQ", "放空那指 3 倍 ETF（SQQQ）", "SQQQ (3x short Nasdaq)", "up"), ("SOXS", "放空半導體 3 倍 ETF（SOXS）", "SOXS (3x short chips)", "up")]
VOL_X = 2.0
# 風向球 baskets (second request; their normal move comes from /api/quote full=1 = one year of daily closes, fetched once
# per page load): private credit, regional banks, and the debt-funded AI data-center names
BASKETS = [("bizd", "私募信貸 BDC ETF（BIZD）", "Private-credit BDCs (BIZD)", ["BIZD"]),
           ("kre", "區域銀行 ETF（KRE）", "Regional banks (KRE)", ["KRE"]),
           ("neo", "AI 算力中心股（CRWV／NBIS／APLD／IREN 平均）", "AI data-center stocks (avg)", ["CRWV", "NBIS", "APLD", "IREN"]),
           ("rsp", "等權重標普（RSP，代表一般股票）", "Equal-weight S&P (RSP)", ["RSP"]),
           ("iwm", "小型股（IWM，羅素 2000）", "Small caps (IWM)", ["IWM"])]
# 組合訊號: patterns across markets, each leg measured in "times its own normal daily move" (z).  One market moving a lot
# can be noise; several moving together in a known pattern is the classic transmission.  (key, zh, en, level 2=red 1=yellow
# 0=information −1=healthy (green), meaning, legs [(symbol or basket key, ">=" / "<=", z)])
COMBOS = [
    ("liq", "股、債、金同時下跌", "Stocks, bonds and gold all down", 2, "資金被抽緊：大家賣掉所有能賣的東西換現金（例如追繳保證金），2020 年 3 月就是這樣",
     [("^GSPC", "<=", -1.5), ("^TNX", ">=", 1.5), ("GC=F", "<=", -1.5)]),
    ("carry", "日圓急升＋日股急跌", "Yen surge + Nikkei drop", 2, "日圓套利交易平倉：借便宜日圓去買海外資產的錢被迫收回，2024 年 8 月 5 日就是這樣",
     [("JPY=X", "<=", -2), ("^N225", "<=", -1.5)]),
    ("ai_credit", "AI 算力中心股＋私募信貸一起跌", "AI data-center stocks + private credit down", 2, "靠借錢買晶片蓋機房的公司和借錢給它們的私募信貸同時被賣：AI 借貸鏈承壓",
     [("neo", "<=", -1.5), ("bizd", "<=", -1.5)]),
    ("flight", "股市下跌＋國債利率下降", "Stocks down, Treasury yields down", 1, "資金從股票逃向國債避險（買債的人多，利率就下降）；如果是股、債一起跌，看上面的「股債金同時下跌」",
     [("^GSPC", "<=", -1.5), ("^TNX", "<=", -1.5)]),
    ("credit_first", "信用先跌、股市還沒反應", "Credit falling before stocks", 1, "高收益債（垃圾債）先被賣、股市還平靜：歷史上信用市場常比股市早一步反應",
     [("HYG", "<=", -2), ("^GSPC", ">=", -1), ("^TNX", "<=", 1)]),       # not a rate spike: HYG has ~3.5y duration
    ("hedge", "VIX 大漲但股市沒跌", "VIX jumps, stocks flat", 1, "有人在買保險（選擇權避險）：大資金預期接下來會有波動",
     [("^VIX", ">=", 2), ("^GSPC", ">=", -0.5)]),
    ("semi", "半導體領跌", "Chips leading the drop", 1, "費城半導體跌得比大盤兇很多：AI 與科技股是這波的壓力來源，台股和韓股通常會跟著受影響",
     [("^SOX", "<=", -2), ("^GSPC", ">=", -1)]),
    ("tw_out", "新台幣貶值＋台股下跌", "TWD weaker + TAIEX down", 1, "外資在賣台股並把錢匯出（新台幣走弱代表美元需求大）",
     [("TWD=X", ">=", 1.5), ("^TWII", "<=", -1.5)]),
    ("usd_em", "美元急升＋韓股下跌", "Dollar spike + KOSPI down", 1, "強勢美元把資金從新興市場吸回美國，亞洲出口國首當其衝",
     [("DX-Y.NYB", ">=", 2), ("^KS11", "<=", -1.5)]),
    ("banks", "區域銀行急跌", "Regional banks sliding", 1, "美國中小銀行股被賣：存款流失或商業不動產壞帳的擔心，2023 年 3 月矽谷銀行事件前後就是這樣",
     [("kre", "<=", -2)]),
    # the other side: risk going away, or a normal shake-out that is not stress
    ("relief", "恐慌退潮的大漲", "Fear receding, strong rally", -1, "VIX 大跌、股市大漲：避險部位在拆掉，資金回到股市（常見於壞消息落地或風險解除）",
     [("^VIX", "<=", -2), ("^GSPC", ">=", 1.5)]),
    ("risk_on", "全面風險偏好", "Broad risk-on", -1, "大盤、半導體、垃圾債一起漲：從股票到信用都願意冒險，屬於健康的上漲",
     [("^GSPC", ">=", 1), ("^SOX", ">=", 1), ("HYG", ">=", 1)]),
    ("broad", "上漲範圍擴大", "Broad-based rally", -1, "等權重標普（一般股票）和大盤一起漲：不是只有幾檔權值股在撐，多數股票都在上漲，是最健康的上漲型態",
     [("rsp", ">=", 1), ("^GSPC", ">=", 0.5)]),
    ("small_caps", "小型股領漲", "Small caps leading", -1, "小型股大漲：市場對美國本土景氣與降息的信心回升，風險偏好擴散到體質較弱的公司",
     [("iwm", ">=", 1.5), ("^GSPC", ">=", 0)]),
    ("tw_in", "外資回流台股", "Foreign money back into Taiwan", -1, "新台幣升值、台股上漲：外資把錢匯進來買台股",
     [("TWD=X", "<=", -1.5), ("^TWII", ">=", 1.5)]),
    ("narrow", "只有權值股撐盤", "Narrow rally", 0, "大盤漲但一般股票（等權重標普）沒漲：上漲集中在少數大型股，基礎比較脆弱",
     [("^GSPC", ">=", 1), ("rsp", "<=", 0)]),
    ("healthy_dip", "健康震盪", "Ordinary pullback", 0, "股市下跌但 VIX 沒有跳升、垃圾債沒有被賣：比較像正常的獲利了結，不是壓力",
     [("^GSPC", "<=", -1), ("^VIX", "<=", 1.5), ("HYG", ">=", -1)]),
]
EXTRA = sorted({r["sym"] for r in RULES} | {r["den"] for r in RULES if r.get("den")} | {a[0] for a in ANOM} | {v[0] for v in VOLS})


def sigmas(eng) -> dict:
    """{symbol: one-year standard deviation of its daily % change} from the hourly price history (empty if unavailable)."""
    out = {}
    try:
        h = eng.market.history
    except Exception:  # noqa: BLE001
        return out
    if h is None or not hasattr(h, "columns"):
        return out
    for sym, _z, _e in ANOM:
        if sym not in h.columns:
            continue
        r = h[sym].dropna()
        r = r[r > 0].pct_change().dropna().iloc[-252:] * 100
        if len(r) >= 120 and r.std() > 0:
            out[sym] = round(float(r.std()), 4)
    return out


def bar_html(eng=None) -> str:
    """Status line + live threshold lights; hidden until the first live quote arrives."""
    sig = html.escape(json.dumps(sigmas(eng) if eng is not None else {}), quote=True)
    note = ("三層即時燈號，每分鐘自動檢查：①固定門檻（上面第一排）；②異常波動掃描：17 個市場（含盤前就在交易的標普／那指期貨），"
            "加上三個風向球（私募信貸 BDC、區域銀行、靠借錢蓋 AI 算力中心的公司），各自和自己過去一年的平常單日波動比，"
            f"再看幾個市場有沒有一起出現已知的組合（股債金同跌、日圓套利平倉、股跌債漲、信用先跌、AI 借貸鏈等 {sum(1 for c in COMBOS if c[3] > 0)} 組壓力型態，"
            "紅色的組合代表歷史上大跌時出現過的型態；另有恐慌退潮的大漲、全面風險偏好、健康震盪等正面型態，用綠色或藍色顯示），"
            "往「好的方向」的大波動（例如股市大漲、VIX 大跌）顯示為綠色，不算警示，"
            "超過平常 2 倍亮黃燈、3 倍亮紅燈；③大量賣壓：SPY、QQQ 成交量是前 4 天同一時段的 2 倍以上而且下跌，或放空型 ETF（SQQQ、SOXS）成交量暴增而且上漲。"
            "這是提醒，不是預測；誰在放空的即時明細沒有免費公開資料，所以用成交量與放空型 ETF 代替。漲跌幅以各市場最近一個交易日計，"
            "模型判斷（AI 判斷、泡沫分組等）仍每小時更新。報價：Yahoo Finance，約有數分鐘延遲。")
    en = ("Three live layers, checked every minute: fixed thresholds; each market vs its own normal daily move (2x yellow, 3x red, "
          "index futures included for pre-market); SPY/QQQ volume vs the same time on prior days, and short-ETF volume. Reminders, not forecasts.")
    return (f'<div class="lqbar" id="lqbar" hidden data-sig="{sig}"><div class="lqhead"><b id="lqone"></b><span id="lqst" class="lqst"></span></div>'
            '<div id="lqal" class="lqal"></div><div id="lqan" class="lqal"></div>'
            f'<details class="lqd"><summary class="lqnote">{T("燈號規則", "Rules")}</summary><p class="lqnote">{T(note, en)}</p></details></div>')


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
       ".lqchip.warn{border-color:#d97706;color:#b45309;font-weight:600}.lqchip.good{border-color:var(--up);color:var(--up);font-weight:600}"
       ".lqchip.info{border-color:var(--ac);color:var(--ac)}.lqd summary{cursor:pointer}"
       ".lqnote{margin:4px 0 0;font-size:11.5px;color:var(--mu)}.tile .asof.lv{color:var(--up)}"
       ".wlt td,.wlt th{white-space:nowrap}.wlx{background:none;border:0;color:var(--mu);cursor:pointer;font-size:14px}.wlx:hover{color:var(--dn)}"
       ".lqf{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}.lqin{flex:1;min-width:0;max-width:260px;padding:6px 10px;border:1px solid var(--bd);"
       "border-radius:8px;background:var(--bg);color:var(--tx);font-size:15px}.lqout{font-size:15px;margin:6px 0}.lqoff{font-size:12.5px;color:var(--mu)}")

_JS = r"""
(function(){var R=__RULES__,EX=__EXTRA__,POLL=__POLL__*1000,AN=__ANOM__,VS=__VOLS__,BK=__BASKETS__,CB=__COMBOS__,BUP=__BUP__,NEU=__NEU__,AY=__AY__,AR=__AR__,VX=__VX__;
 var bar=document.getElementById('lqbar');var tiles=[].slice.call(document.querySelectorAll('.tile[data-lq]'));
 var want={};tiles.forEach(function(t){want[t.getAttribute('data-lq')]=1;});EX.forEach(function(s){want[s]=1;});
 var dead=false,lastOk=0,data={};function en(){return document.documentElement.lang==='en';}
 function f(x,d){return x==null||isNaN(x)?'—':Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
 function sg(x,d){if(x==null||isNaN(x))return '—';if(Math.abs(x)<0.5*Math.pow(10,-d))x=0;return (x>0?'+':x<0?'':'')+f(x,d);}
 function api1(list,full,vol){return fetch('api/quote?s='+encodeURIComponent(list)+(full?'&full=1':'')+(vol?'&vol='+encodeURIComponent(vol):''),{cache:'no-store'}).then(function(r){if(r.status===404||r.status===405){dead=true;throw 0;}if(!r.ok)throw 0;return r.json();});}
 function api(list,full,vol){var a=String(list).split(',').filter(Boolean),ch=[];for(var i=0;i<a.length;i+=20)ch.push(a.slice(i,i+20).join(','));   // the service takes 25 per request
   return Promise.all(ch.map(function(c){return api1(c,full,vol);})).then(function(rs){var o={ts:0,q:{}};rs.forEach(function(r){o.ts=Math.max(o.ts,r.ts||0);Object.keys(r.q||{}).forEach(function(k){o.q[k]=r.q[k];});});return o;});}
 function hhmm(t){if(!t)return '';var d=new Date(t*1000),p=function(n){return ('0'+n).slice(-2);};var tm=p(d.getHours())+':'+p(d.getMinutes());
   return d.toDateString()===new Date().toDateString()?tm:(d.getMonth()+1)+'/'+d.getDate()+' '+tm;}
 function paintTiles(q){tiles.forEach(function(t){var s=t.getAttribute('data-lq'),x=q[s];if(!x)return;var dg=+t.getAttribute('data-dg')||0;
   var v=t.querySelector('.tv'),c=t.querySelector('.tc'),a=t.querySelector('.asof');if(v)v.textContent=f(x.price,dg);
   if(c&&x.chg!=null){c.textContent=sg(x.chg,2)+'%';c.classList.remove('up','dn');if(x.chg>0)c.classList.add('up');else if(x.chg<0)c.classList.add('dn');}
   if(a){a.textContent=hhmm(x.t);a.classList.add('lv');}});}
 function val(r,q){var x=q[r.sym];if(!x)return null;if(r.f==='lvl')return x.price;if(r.f==='chg')return x.chg;
   if(r.f==='ratio'){var y=q[r.den];return y&&y.price?x.price/y.price:null;}return null;}
 var SIG={};try{SIG=JSON.parse((bar&&bar.getAttribute('data-sig'))||'{}');}catch(e){}
 var SD2={},BKS=[];BK.forEach(function(b){b[3].forEach(function(s){if(BKS.indexOf(s)<0)BKS.push(s);});});
 function lvl(s,z){var a=Math.abs(z),big=a>=AR?2:a>=AY?1:0;if(!big)return [0,0];if(NEU.indexOf(s)>=0)return [big,0];
   var bad=BUP.indexOf(s)>=0?z>0:z<0;return bad?[big,0]:[0,big];}
 function scan(q){var out=[];AN.forEach(function(a){var x=q[a[0]],sd=SIG[a[0]];if(!x||x.chg==null||!sd)return;var z=x.chg/sd,L=lvl(a[0],z);
   out.push({s:a[0],zh:a[1],en:a[2],chg:x.chg,z:z,lv:L[0],good:L[1]});});
   BK.forEach(function(b){var c=0,d=0,n=0;b[3].forEach(function(s){var x=q[s];if(x&&x.chg!=null&&SD2[s]){c+=x.chg;d+=SD2[s];n++;}});
   if(!n)return;c/=n;d/=n;var z=c/d,L=lvl(b[0],z);out.push({s:b[0],zh:b[1],en:b[2],chg:c,z:z,lv:L[0],good:L[1]});});
   VS.forEach(function(v){var x=q[v[0]];if(!x||x.volx==null||x.chg==null)return;var dir=v[3]==='down'?x.chg<0:x.chg>0;
   out.push({s:v[0],zh:v[1],en:v[2],chg:x.chg,vx:x.volx,lv:x.volx>=VX&&dir?(x.volx>=VX*1.5?2:1):0});});return out;}
 function combos(sc){var z={};sc.forEach(function(o){if(o.z!=null)z[o.s]=o.z;});var out=[],ev=0;
   CB.forEach(function(c){if(c[5].every(function(l){return z[l[0]]!=null;}))ev++;var ok=c[5].every(function(l){var v=z[l[0]];return v!=null&&(l[1]==='>='?v>=l[2]:v<=l[2]);});
   if(ok)out.push({s:'combo:'+c[0],zh:c[1],en:c[2],lv:c[3]>0?c[3]:0,good:c[3]<0?1:0,info:c[3]===0?1:0,why:c[4],combo:1});});window.__lqcb=ev;return out;}
 function paintScan(q){var el=document.getElementById('lqan');if(!el)return [];var sc0=scan(q),cb=combos(sc0),sc=sc0.concat(cb),hits=sc.filter(function(o){return o.lv>0;}),h='';
   hits.sort(function(a,b){return b.lv-a.lv;}).forEach(function(o){var t=o.combo?(en()?'Pattern: '+o.en:'組合訊號：'+o.zh+'——'+o.why):o.vx!=null?(en()?o.en+': volume '+f(o.vx,1)+'x usual, '+sg(o.chg,2)+'%':o.zh+'：成交量是平常同時段的 '+f(o.vx,1)+' 倍，'+sg(o.chg,2)+'%')
     :(en()?o.en+' '+sg(o.chg,2)+'% ('+f(Math.abs(o.z),1)+'x normal)':o.zh+(o.chg<0?' 異常大跌 ':' 異常大漲 ')+sg(o.chg,2)+'%（平常的 '+f(Math.abs(o.z),1)+' 倍）');
     h+='<span class="lqchip '+(o.lv>=2?'hit':'warn')+'">'+(o.lv>=2?'● ':'▲ ')+t+'</span>';});
   var goods=sc.filter(function(o){return o.good||o.info;});
   goods.forEach(function(o){var t=o.combo?(en()?'Pattern: '+o.en:'組合訊號：'+o.zh+'——'+o.why)
     :(en()?o.en+' '+sg(o.chg,2)+'% ('+f(Math.abs(o.z),1)+'x normal, the healthy direction)':o.zh+(o.chg<0?' 大跌 ':' 大漲 ')+sg(o.chg,2)+'%（平常的 '+f(Math.abs(o.z),1)+' 倍，往好的方向）');
     h+='<span class="lqchip '+(o.info?'info':'good')+'">'+(o.info?'ℹ ':'✓ ')+t+'</span>';});
   window.__lqgood=goods;
   var n=sc.filter(function(o){return o.z!=null;}),top=n.slice().sort(function(a,b){return Math.abs(b.z)-Math.abs(a.z);})[0],
     vms=sc.filter(function(o){return o.vx!=null;}),vm=vms.slice().sort(function(a,b){return b.vx-a.vx;})[0];
   window.__lqcov={sc:n.length,vol:vms.length,cb:window.__lqcb||0};
   if(!hits.length&&n.length)h+='<span class="lqchip ok">○ '+(en()?'Unusual-move scan: '+n.length+' markets all within 2x normal'+(top?' (largest: '+top.en+' '+f(Math.abs(top.z),1)+'x)':'')
     :'異常波動掃描：'+n.length+' 個市場都在平常 2 倍以內'+(top?'（最大：'+top.zh+' '+sg(top.chg,2)+'%，平常的 '+f(Math.abs(top.z),1)+' 倍）':''))+'</span>'
     +(goods.some(function(o){return o.combo;})?'':'<span class="lqchip ok">○ '+(en()?'Cross-market patterns: none of '+(window.__lqcb||0)+'/'+CB.length+' checkable':'組合訊號：'+CB.length+' 組中 '+(window.__lqcb||0)+' 組有資料可判斷，都沒出現')+'</span>')
     +(vm?'<span class="lqchip ok">○ '+(en()?'Volume: no heavy selling (max '+vm.en+' '+f(vm.vx,1)+'x)':'大量賣壓：未出現（成交量最高 '+vm.zh+' 平常的 '+f(vm.vx,1)+' 倍）')+'</span>':'');
   el.innerHTML=h;return hits;}
 function paintRules(q){var hits=[],h='',nr=0;R.forEach(function(r){var v=val(r,q);if(v==null)return;nr++;var hit=r.op==='>='?v>=r.v:v<=r.v;if(hit)hits.push(r);
   h+='<span class="lqchip '+(hit?'hit':'ok')+'">'+(hit?'● ':'○ ')+(en()?r.en:r.zh)+'：'+(r.f==='chg'?sg(v,r.dg)+'%':f(v,r.dg))+'</span>';});
   document.getElementById('lqal').innerHTML=h;var one=document.getElementById('lqone');var sh=paintScan(q),red=sh.filter(function(o){return o.lv>=2;}).length,yel=sh.length-red;
   var all=hits.length+red,gd=(window.__lqgood||[]),gc=gd.filter(function(o){return o.combo;})[0],cv=window.__lqcov||{sc:0,vol:0,cb:0},
     lay=(nr?1:0)+(cv.sc?1:0)+(cv.cb?1:0)+(cv.vol?1:0);
   one.textContent=all?(en()?'Live: '+all+' alert(s) — see the red items':'一句話看懂（即時）：🔴 偵測到異常——'+all+' 項亮紅燈'+(yel?'、'+yel+' 項黃燈':'')+'，看紅色那幾項')
     :yel?(en()?'Live: '+yel+' unusual move(s) worth watching':'一句話看懂（即時）：⚠️ 沒有紅燈，但有 '+yel+' 項波動比平常大（黃燈），值得留意')
     :gc?(en()?'Live: no stress signal — '+gc.en:'一句話看懂（即時）：✅ 目前無偵測到異常；'+gc.zh+'——'+gc.why)
     :gd.length?(en()?'Live: no stress signal; '+gd.length+' big move(s) in the healthy direction':'一句話看懂（即時）：✅ 目前無偵測到異常；'+gd.length+' 個市場往好的方向大幅變動（綠色）')
     :!nr||!cv.sc?(en()?'Live: not enough live data to judge ('+nr+' thresholds, '+cv.sc+' markets with quotes)':'一句話看懂（即時）：⚪ 資料不足，暫時無法判斷——有報價的固定門檻 '+nr+' 項、異常波動 '+cv.sc+' 個市場')
     :lay<4?(en()?'Live: no alert in the '+lay+' of 4 layers that have data':'一句話看懂（即時）：✅ 目前無偵測到異常（四層檢查中 '+lay+' 層有資料'+(cv.vol?'':'，成交量暫缺')+(cv.cb?'':'，組合型態暫缺')+'）')
     :(en()?'Live: no alert — fixed thresholds, unusual-move scan and volume all normal':'一句話看懂（即時）：✅ 目前無偵測到異常——固定門檻、異常波動、組合型態、成交量四層檢查都正常');}
 function ago(){var st=document.getElementById('lqst');if(!st||!lastOk)return;var s=Math.round((Date.now()-lastOk)/1000);
   st.className='lqst on';st.textContent='● '+(en()?'live · updated '+(s<60?s+'s':Math.round(s/60)+'m')+' ago':'即時 · '+(s<60?s+' 秒前':Math.round(s/60)+' 分鐘前')+'更新');}
 function stale(){var st=document.getElementById('lqst');if(st&&lastOk){st.className='lqst';st.textContent=en()?'live paused — showing hourly data':'即時暫停，顯示整點資料';}}
 if(BKS.length)setTimeout(function(){if(!dead)api(BKS.join(','),1).then(function(d){var q=d.q||{};Object.keys(q).forEach(function(s){if(q[s].sd1y)SD2[s]=q[s].sd1y;});if(lastOk)paintRules(data);}).catch(function(){});},800);
 function pull(){if(dead||document.hidden)return;Promise.all([api(Object.keys(want).join(','),0,VS.map(function(v){return v[0];}).join(',')),
   BKS.length?api(BKS.join(',')).catch(function(){return {q:{}};}):Promise.resolve({q:{}})]).then(function(r){var d=r[0];var q=d.q||{},q2=r[1].q||{};
   Object.keys(q2).forEach(function(s){if(!q[s])q[s]=q2[s];});if(!Object.keys(q).length){stale();return;}data=q;lastOk=Date.now();
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
JS = (_JS.replace("__RULES__", json.dumps(RULES, ensure_ascii=False)).replace("__EXTRA__", json.dumps(EXTRA)).replace("__POLL__", str(POLL_S))
      .replace("__ANOM__", json.dumps(ANOM, ensure_ascii=False)).replace("__VOLS__", json.dumps(VOLS, ensure_ascii=False))
      .replace("__BASKETS__", json.dumps(BASKETS, ensure_ascii=False))
      .replace("__COMBOS__", json.dumps(COMBOS, ensure_ascii=False)).replace("__BUP__", json.dumps(BAD_UP)).replace("__NEU__", json.dumps(NEUTRAL))
      .replace("__AY__", str(ANOM_Y)).replace("__AR__", str(ANOM_R)).replace("__VX__", str(VOL_X)))
