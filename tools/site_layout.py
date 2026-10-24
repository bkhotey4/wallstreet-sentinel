"""Page layout: seven groups in a left sidebar (a drawer on phones), a breadcrumb, and the 總攬大表 at the top of the
overview.  Layout only — every card is rendered exactly as before; the index copies its figures from the cards that
were rendered in the same build, so the two can never disagree.  The page keys (#risk, #industry …) are unchanged, so
links from the bot, alerts and bookmarks keep working."""
from __future__ import annotations

import html as _h
import json
import logging
import re
from typing import Callable, Dict, List, Optional, Tuple

from tools.sitekit import T, esc

log = logging.getLogger(__name__)

# group key, zh, en, the question it answers (zh, en), page keys in order
GROUPS: List[Tuple[str, str, str, str, str, List[str]]] = [
    ("home", "今日總覽", "Today", "今天市場怎樣、該注意什麼", "Where the market stands today", ["overview"]),
    ("risk", "市場風險", "Market risk", "會不會大跌、壓力在哪", "Crash risk and where the stress is",
     ["ai", "outlook", "risk", "mood", "flows", "valuation", "crisis", "history", "research"]),
    ("macro", "總經與利率", "Macro & rates", "經濟、利率、通膨往哪走", "Economy, rates, inflation", ["econ", "bonds", "energy", "markets"]),
    ("sector", "產業", "Sectors", "哪些產業順風、哪裡有財務風險", "Which sectors have tailwinds or financial risk",
     ["industry", "rotation", "themes", "tech", "growth"]),
    ("stock", "個股", "Stocks", "哪些公司值得研究", "Companies worth a closer look", ["scores", "signals", "intel", "gurus", "portfolio"]),
    ("tw", "台股", "Taiwan", "台股資金與籌碼", "Taiwan flows and positioning", ["taiwan"]),
    ("more", "新聞與說明", "News & about", "背景新聞、數據怎麼來", "Background news, how the data is made", ["news", "tools", "inputs", "about"]),
]
GROUP_OF = {k: g for g, *_x, ks in GROUPS for k in ks}


def order(tabs: List[tuple]) -> List[tuple]:
    """Tabs in sidebar order; a tab no group lists (a new page) goes to the end of 新聞與說明 instead of disappearing."""
    by = {t[0]: t for t in tabs}
    out = [by[k] for *_x, ks in GROUPS for k in ks if k in by]
    return out + [t for t in tabs if t[0] not in GROUP_OF]


# ------------------------------------------------------------------ 總攬大表: figures copied from the rendered cards
def _text(h: str) -> str:
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", h or "")))


def _top3(m) -> str:
    return "、".join(t for t, _s in re.findall(r"([A-Z]{1,5}) (\d+)", m[1])[:3])


# group → [(page, pattern, formatter)]; each pattern reads a figure off a card in that page
PICKS: Dict[str, List[Tuple[str, str, Callable]]] = {
    "home": [("overview", r"系統性壓力指數 SSI .*?(\d+(?:\.\d+)?) (\S+) 歷史百分位 (\d+)%", lambda m: f"SSI {m[1]} {m[2]}（歷史百分位 {m[3]}%）"),
             ("overview", r"風險階段 (\S+ \S+)", lambda m: f"風險階段 {m[1]}"),
             ("overview", r"21 日內跌 ≥ 5% ([\d.]+%) 基準 ([\d.]+%)", lambda m: f"21 日內跌 ≥5% 機率 {m[1]}（平常 {m[2]}）"),
             ("overview", r"63 日內跌 ≥ 10% ([\d.]+%) 基準 ([\d.]+%)", lambda m: f"63 日內跌 ≥10% 機率 {m[1]}（平常 {m[2]}）"),
             ("outlook", r"12 個月內美國衰退 ([\d.]+%)", lambda m: f"12 個月內美國衰退機率 {m[1]}"),
             ("mood", r"VIX ([\d.]+) [+-][\d.]+% 近一年百分位 (\d+)", lambda m: f"VIX {m[1]}（近一年第 {m[2]} 百分位）")],
    "risk": [("ai", r"一眼看懂：AI 怎麼看現在的風險 (\S+)", lambda m: f"AI 判斷：{m[1]}"),
             ("ai", r"AI 視角交叉比對：(\d+) 項一致、(\d+) 項分歧", lambda m: f"AI 視角 × 人類指標：{m[1]} 項一致、{m[2]} 項分歧"),
             ("outlook", r"(\d+) 綜合風險：(\S+)", lambda m: f"綜合風險 {m[1]} {m[2]}"),
             ("risk", r"紅燈 (\d+) 黃燈 (\d+)", lambda m: f"金絲雀 紅燈 {m[1]}・黃燈 {m[2]}"),
             ("mood", r"恐慌與貪婪指數（多因子） .*?資料日 \S+ (\d+) (\S+)", lambda m: f"恐慌貪婪 {m[1]} {m[2]}"),
             ("flows", r"零 Gamma 翻轉點 ([\d,]+) \S+ SPX ([\d,]+)", lambda m: f"SPX {m[2]}，Gamma 翻轉點 {m[1]}"),
             ("valuation", r"巴菲特指標（股市總市值／GDP） (\S+) ([\d.]+%)", lambda m: f"巴菲特指標 {m[2]}（{m[1]}）"),
             ("risk", r"衝擊雷達：下一次衝擊可能從哪裡點火 .*?資料日 \S+ (\S+) (高度警戒|警戒|留意|點火中|升溫|平靜) · (\d+)",
              lambda m: f"衝擊雷達最高：{m[1]}（{m[2]} {m[3]}）"),
             ("risk", r"企業危機雷達：.*?紅燈 (\d+) 黃燈 (\d+)", lambda m: f"企業危機雷達 紅燈 {m[1]}・黃燈 {m[2]}"),
             ("risk", r"總經象限 (\S+) \S+ 風險偏好 (\S+)", lambda m: f"總經象限：{m[1]}・{m[2]}"),
             ("flows", r"暗池指數（\d+ 檔大型股） ([\d.]+%)", lambda m: f"暗池指數 {m[1]}"),
             ("mood", r"抄底四訊號：恐慌到極點了嗎 .*?(\d) / 4 (\S+)", lambda m: f"抄底四訊號 {m[1]}/4（{m[2]}）"),
             ("outlook", r"累積脆弱度：(\d+) 盞燈中 (\d+) 盞過熱", lambda m: f"累積脆弱度 {m[2]}/{m[1]} 盞過熱"),
             ("outlook", r"標普 500 在 6 個月內跌 20% 以上的機率 ([\d.]+%)", lambda m: f"選擇權隱含 6 個月跌 ≥20%：{m[1]}"),
             ("crisis", r"(\d+) 次標普從高點跌 \d+% 以上的危機，壓力指數 SSI 在「跌滿 10% 之前」進入升溫（≥ \d+）的有 (\d+) 次.*?SSI 升上 \d+ 共 (\d+) 次，其中 (\d+) 次之後",
              lambda m: f"危機預警紀錄：{m[1]} 次危機先亮燈 {m[2]} 次，假警報 {m[4]}/{m[3]} 次")],
    "macro": [("econ", r"(\d\d-\d\d) 週. 下次 FOMC.*?市場預期：(\S+)", lambda m: f"下次 FOMC {m[1]}，市場預期{m[2]}"),
              ("econ", r"之後幾次會議的隱含利率路徑 .*?該次機率 \d\d-\d\d .*? (\d\d-\d\d)＊? ([\d.]+%) [+-]\d+bp [+-]\d+bp (升息 1 碼|降息 1 碼|維持不變)\S* (\d+)%",
               lambda m: f"再下一次 {m[1]}：{m[3]} {m[4]}%（隱含利率 {m[2]}）"),
              ("econ", r"本週重要經濟數據 .*?★★★ FOMC.*?★★★ (\S+) .*?(\d\d-\d\d) 週", lambda m: f"本週還有 {m[1]}（{m[2]}）"),
              ("bonds", r"美債專區.*?10 年 ([\d.]+%)", lambda m: f"10 年期殖利率 {m[1]}"),
              ("bonds", r"2 年 ([\d.]+%) 10 年 [\d.]+% 30 年 [\d.]+% 10年−2年利差 ([+-]\d+bp)", lambda m: f"2 年期 {m[1]}、10年−2年利差 {m[2]}"),
              ("energy", r"柴油裂解價差 ([\d.]+) 美元／桶，在 2007 年以來第 (\d+) 百分位", lambda m: f"柴油裂解價差第 {m[2]} 百分位"),
              ("energy", r"布蘭特原油 ([\d.]+) ([+-][\d.]+%)", lambda m: f"布蘭特原油 {m[1]}（3 個月 {m[2]}）"),
              ("bonds", r"超額債券溢酬 EBP ([+-][\d.]+) .*?12 個月內衰退機率 ([\d.]+%)", lambda m: f"EBP {m[1]}、聯準會 12 個月衰退機率 {m[2]}")],
    "sector": [("industry", r"規則判讀為順風：([^；]*)；逆風：([^。]*)。", lambda m: f"順風：{m[1]}；逆風：{m[2]}"),
               ("industry", r"財報季：已有 (\d+) 家公布，(\d+)% 優於預估", lambda m: f"財報季 {m[1]} 家、{m[2]}% 優於預估"),
               ("industry", r"近 3 個月領漲：([^；]*)；", lambda m: f"近 3 個月領漲：{m[1]}"),
               ("industry", r"財報壓力最普遍：([^。]*)。", lambda m: f"財報壓力最普遍：{m[1]}"),
               ("rotation", r"標普 500 離 52 週高點 ([-\d.]+%) 中位數個股離自己的高點 ([-\d.]+%)", lambda m: f"標普離高點 {m[1]}，但中位數個股 {m[2]}"),
               ("rotation", r"美股評分池站上 200 日線比例 (\d+%)", lambda m: f"美股站上 200 日線 {m[1]}")],
    "stock": [("overview", r"個股評分前五名 .*?美股 (.*?) 台股", lambda m: f"評分前段（美股）：{_top3(m)}"),
              ("overview", r"個股評分前五名 .*?台股 (.*?) 港股", lambda m: "評分前段（台股）：" + "、".join(n for n, _c, _s in re.findall(r"(\S+) (\d{4}) (\d+)", m[1])[:3])),
              ("gurus", r"內部人賣出（依非計畫性金額排序） .*?最大一筆 \S+ ([A-Z.]+) (\$[\d.]+[BMK])", lambda m: f"內部人賣出最多：{m[1]} {m[2]}")],
    "tw": [("taiwan", r"外資台指期未平倉 ([-\d,]+) 口 \S* ?(\S+)", lambda m: f"外資台指期未平倉 {m[1]} 口（{m[2]}）"),
           ("taiwan", r"近 5 日合計 ([-\d.]+) 億", lambda m: f"外資現貨近 5 日 {m[1]} 億"),
           ("taiwan", r"融資餘額與清洗計 ([\d,]+ 億) \(([-+\d.]+%)\)", lambda m: f"融資餘額 {m[1]}（單日 {m[2]}）"),
           ("taiwan", r"Put/Call 未平倉比 ([\d.]+%) \S+ (\S+)", lambda m: f"台指選擇權 P/C {m[1]}（{m[2]}）"),
           ("taiwan", r"台積電 (\d{4}/\d\d) 營收 [\d,]+ 億，月增 [-+\d.]+%、年增 ([-+\d.]+%)", lambda m: f"台積電 {m[1]} 營收年增 {m[2]}")],
    "more": [("news", r"(\d\d-\d\d) Gross Domestic Product", lambda m: f"GDP 公布 {m[1]}"),
             ("news", r"(\d\d-\d\d) Employment Situation", lambda m: f"非農就業報告 {m[1]}")],
}


def picks(pages: Dict[str, str]) -> Dict[str, List[str]]:
    txt = {k: _text(v) for k, v in pages.items()}
    out: Dict[str, List[str]] = {}
    for g, lst in PICKS.items():
        got = []
        for page, pat, fmt in lst:
            m = re.search(pat, txt.get(page, ""))
            if not m:
                continue
            try:
                got.append(fmt(m))
            except Exception:  # noqa: BLE001
                log.debug("index pick %s failed", pat)
        out[g] = got
    return out


def index_card(pages: Dict[str, str], names: Dict[str, Tuple[str, str]]) -> str:
    pk = picks(pages)
    rows = ""
    for g, zh, en, qz, qe, ks in GROUPS:
        ks = [k for k in ks if k in pages]
        if not ks:
            continue
        pts = "".join(f"<li>{T(x, x)}</li>" for x in pk.get(g, []))
        if g == "more":
            pts += f'<li>{T("新聞只當背景，不計入風險分數", "News is background only; it never enters the risk scores")}</li>'
        chips = "".join(f'<a class="ochip" href="#{k}" data-p="{k}">{T(*names.get(k, (k, k)))}</a>' for k in ks)
        rows += (f'<tr><td class="og"><b>{T(zh, en)}</b><div class="oq">{T(qz, qe)}</div></td>'
                 f'<td><ul class="ol">{pts or "<li>—</li>"}</ul></td><td class="oc">{chips}</td></tr>')
    body = (f'<p class="sub">{T("每一類想回答的問題、今天的重點數字（直接取自同一次產生的各張卡片），點右邊就跳到詳細內容。", "Each group, the key figures for today (copied from the cards below), and where to read more.")}</p>'
            f'<div class="scroll"><table class="mini otab"><thead><tr><th>{T("分類", "Group")}</th><th>{T("今日重點", "Today")}</th>'
            f'<th>{T("詳細在哪", "Where")}</th></tr></thead><tbody>{rows}</tbody></table></div>')
    return f'<section class="card wide ovt" id="c-index"><h2>{T("總攬大表：重點在哪裡", "Index: where the key points are")}</h2>{body}</section>'


# ------------------------------------------------------------------ sidebar, breadcrumb
def sidebar(names: Dict[str, Tuple[str, str]], first: str = "overview") -> str:
    out = ""
    for g, zh, en, qz, qe, ks in GROUPS:
        ks = [k for k in ks if k in names]
        if not ks:
            continue
        links = "".join(f'<a class="ptab{" on" if k == first else ""}" href="#{k}" data-p="{k}" data-en="{esc(names[k][1])}">{esc(names[k][0])}</a>' for k in ks)
        out += f'<div class="sg"><div class="sgt">{T(zh, en)}<span>{T(qz, qe)}</span></div>{links}</div>'
    extra = [k for k in names if k not in GROUP_OF]
    if extra:
        out += '<div class="sg">' + "".join(f'<a class="ptab" href="#{k}" data-p="{k}" data-en="{esc(names[k][1])}">{esc(names[k][0])}</a>' for k in extra) + "</div>"
    return f'<aside class="side" id="side" aria-label="pages">{out}</aside>'


def topnav() -> str:
    return (f'<nav class="pnav" aria-label="pages"><div class="pbar"><button class="btn sidebtn" id="sideBtn" type="button" aria-controls="side">'
            f'☰ {T("目錄", "Pages")}</button><span class="crumb" id="crumb"></span></div></nav>')


def js(names: Dict[str, Tuple[str, str]]) -> str:
    gn = {g: [zh, en] for g, zh, en, *_x in GROUPS}
    nm = {k: list(v) for k, v in names.items()}
    return ("(function(){var GROUP_OF=" + json.dumps(GROUP_OF) + ",GN=" + json.dumps(gn, ensure_ascii=False) + ",NM=" + json.dumps(nm, ensure_ascii=False) + ";"
            + r"""
var side=document.getElementById('side'),crumb=document.getElementById('crumb'),btn=document.getElementById('sideBtn');if(!side)return;
function sync(){var k=((document.querySelector('.page.on')||{}).id||'p-overview').slice(2),en=document.documentElement.lang==='en',i=en?1:0;
 var g=GN[GROUP_OF[k]],n=NM[k];if(crumb)crumb.textContent=(g?g[i]+' › ':'')+(n?n[i]:'');side.classList.remove('open');
 var a=side.querySelector('.ptab.on');if(a&&a.scrollIntoView&&window.innerWidth>900){var r=a.getBoundingClientRect(),s=side.getBoundingClientRect();if(r.top<s.top||r.bottom>s.bottom)a.scrollIntoView({block:'nearest'});}}
window.addEventListener('hashchange',function(){setTimeout(sync,0);});
document.addEventListener('click',function(ev){if(ev.target.closest('[data-p]')||ev.target.closest('#langBtn'))setTimeout(sync,0);
 if(side.classList.contains('open')&&!ev.target.closest('#side')&&!ev.target.closest('#sideBtn'))side.classList.remove('open');});
function lock(){document.documentElement.style.overflow=side.classList.contains('open')?'hidden':'';}
new MutationObserver(lock).observe(side,{attributes:true,attributeFilter:['class']});
if(btn)btn.addEventListener('click',function(ev){ev.stopPropagation();side.classList.toggle('open');});
document.addEventListener('keydown',function(ev){if(ev.key==='Escape')side.classList.remove('open');});
sync();})();
""")


CSS = """
.layout{display:grid;grid-template-columns:232px minmax(0,1fr);gap:18px}
.side{position:sticky;top:96px;align-self:start;max-height:calc(100vh - 110px);overflow:auto;padding:4px 0 20px;border-right:1px solid var(--bd);scrollbar-width:thin}
.sg{margin:0 0 14px}.sgt{font-weight:700;font-size:13.5px;padding:4px 10px;color:var(--tx)}.sgt span{display:block;font-weight:400;font-size:11.5px;color:var(--tx2)}
.side .ptab{display:block;border-bottom:0;border-left:3px solid transparent;padding:6px 14px;font-size:13px}
.side .ptab.on{border-left-color:var(--ac);background:var(--wash);border-bottom:0}
.lmain{min-width:0}.sidebtn{display:none}.crumb{font-size:13px;color:var(--tx2);padding:10px 4px;white-space:nowrap}
.ovt .otab td{vertical-align:top}.og{min-width:120px}.oq{font-size:12px;color:var(--tx2);margin-top:2px}.ol{margin:0;padding-left:16px;line-height:1.7}.oc{min-width:180px}
.ochip{display:inline-block;margin:2px 4px 2px 0;padding:2px 9px;border:1px solid var(--bd);border-radius:99px;font-size:12px;color:var(--tx);text-decoration:none}
.ochip:hover{border-color:var(--ac);color:var(--ac);text-decoration:none}
@media(max-width:900px){.layout{grid-template-columns:minmax(0,1fr)}
 .side{position:fixed;top:0;left:0;bottom:auto;width:min(82vw,300px);height:100vh;height:100dvh;max-height:100dvh;overflow-y:auto;
  overscroll-behavior:contain;-webkit-overflow-scrolling:touch;z-index:60;background:var(--page);border-right:1px solid var(--bd);
  padding:calc(14px + env(safe-area-inset-top,0px)) 0 calc(20px + env(safe-area-inset-bottom,0px));transform:translateX(-105%);transition:transform .2s}
 .side.open{transform:none;box-shadow:0 0 0 100vmax rgba(0,0,0,.35)}.sidebtn{display:inline-block;margin:6px 8px 6px 0}}
@media(max-width:640px){.otab thead{display:none}.otab tr{display:block;border-bottom:1px solid var(--bd);padding:8px 0}.otab td{display:block;border:0;padding:2px 0}.og,.oc{min-width:0}}
@media(prefers-reduced-motion:reduce){.side{transition:none}}
"""


# 重點標示 (bright-blue keywords in running text, switchable from the header)
KW_JS = r"""
(function(){
// 重點標示: judgement words and "where does it sit" figures in running text turn bright blue (layout only, text unchanged)
var WORDS=['偏高','偏低','過熱','紅燈','黃燈','危險','偏弱','逆風','順風','擴散','升溫','高壓','極端','警戒','倒掛','收緊','放寬','背離','分歧',
 '轉弱','轉強','惡化','改善','利潤率擴張','利潤率收縮','明顯上修','明顯下修','上修','下修','非常樂觀','偏樂觀','風險趨避','假警報','沒先亮',
 '最危險','R-zone','同時過熱','落後大盤','領先大盤','跌破 200 日均線','站在 200 日均線之上','資金缺口','財報壓力','違約','套很久',
 '至今仍未回到','歷史低檔','歷史高點','創紀錄','合起來怎麼看','隱含意義'];
WORDS.sort(function(a,b){return b.length-a.length;});
var esc=function(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');};
var RE=new RegExp('('+WORDS.map(esc).join('|')+'|第\\s?\\d+\\s?百分位|\\d+(?:\\.\\d+)?\\s?倍|\\d+\\s?次中\\s?\\d+\\s?次|\\d+\\s?／\\s?\\d+\\s?盞)','g');
var SKIP='th,a,button,script,style,svg,h2,h3,summary,.upd,.kw,.pill,.tile,.ptab,.crumb,label,select,option,input,textarea';
function run(root){
 if(document.documentElement.lang==='en')return;
 var scope=(root||document).querySelectorAll('.card p,.card li,.rimp,.card .d,.card td');
 scope.forEach(function(el){
  var w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null),nodes=[],n;
  while((n=w.nextNode()))nodes.push(n);
  nodes.forEach(function(t){
   if(!t.nodeValue||!t.parentElement||t.parentElement.closest(SKIP))return;
   var cell=t.parentElement.closest('td');if(cell&&cell.textContent.length<24)return;   // short table cells: numbers, not sentences
   RE.lastIndex=0;if(!RE.test(t.nodeValue))return;RE.lastIndex=0;
   var f=document.createDocumentFragment(),s=t.nodeValue,last=0,m;
   while((m=RE.exec(s))){if(m.index>last)f.appendChild(document.createTextNode(s.slice(last,m.index)));
    var b=document.createElement('b');b.className='kw';b.textContent=m[0];f.appendChild(b);last=m.index+m[0].length;}
   if(last<s.length)f.appendChild(document.createTextNode(s.slice(last)));
   t.parentNode.replaceChild(f,t);});});}
function load(){try{return localStorage.getItem('kw');}catch(e){return null;}}
function setKw(on){document.documentElement.classList.toggle('nokw',!on);var b=document.getElementById('kwBtn');
 if(b){b.classList.toggle('on',on);b.setAttribute('aria-pressed',on?'true':'false');b.title=on?'重點標示：開（點一下關閉）':'重點標示：關（點一下開啟）';}
 try{localStorage.setItem('kw',on?'1':'0');}catch(e){}}
setKw(load()!=='0');run();
var lb=document.getElementById('langBtn');if(lb)lb.addEventListener('click',function(){setTimeout(function(){run();},0);});
var kb=document.getElementById('kwBtn');if(kb)kb.addEventListener('click',function(){setKw(document.documentElement.classList.contains('nokw'));});
document.addEventListener('toggle',function(ev){if(ev.target&&ev.target.tagName==='DETAILS')run(ev.target);},true);
})();
"""
KW_CSS = ':root{--kw:#0a66e0}@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--kw:#4db2ff}}:root:not([data-theme="light"]){--kw:#4db2ff}:root[data-theme="light"]{--kw:#0a66e0}.kw{color:var(--kw);font-weight:700}.nokw .kw{color:inherit;font-weight:inherit}#kwBtn{font-weight:700}#kwBtn.on{color:var(--kw);border-color:var(--kw)}'
