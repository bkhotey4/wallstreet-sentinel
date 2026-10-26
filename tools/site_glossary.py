"""名詞小辭典: the first time a jargon word appears in a card it gets a dotted underline; hover or tap shows one plain sentence.

Runs per page (the visible one, then each page when it is opened), like the keyword highlighter, so it costs nothing for
pages nobody looks at. Chinese only: in English mode the terms are left alone.
"""
import json

# term as it appears on the page -> one plain-language sentence (beginner level, no advice)
GLOSS = {
    "VIX": "恐慌指數：用標普 500 選擇權價格算出市場預期未來 30 天的波動，越高代表大家越緊張；20 以下算平靜，30 以上算恐慌。",
    "VIX3M": "3 個月期的恐慌指數。平常比 VIX 高；VIX 反過來比它高（倒掛）代表眼前的恐慌比長期還重。",
    "SSI": "本站的系統性壓力指數：把信用、波動、資金等多項指標換算成 0–100，越高代表金融體系越緊繃（描述現況，不是預測）。",
    "零 Gamma": "選擇權造市商避險行為轉向的指數位置：在它之上，避險會讓行情變穩；跌破它，避險反而會放大漲跌。",
    "Gamma": "選擇權價格對股價變化有多敏感。這裡指造市商為了避險必須買賣股票的力道，會影響大盤波動大小。",
    "暗池": "不在公開交易所撮合的大額交易場所，多半是機構下單；成交比例變化可以看出大資金的動向。",
    "信用利差": "公司債比同年期公債多付的利息。利差擴大＝市場擔心企業還不出錢，常比股市先反映壓力。",
    "利差": "兩種利率之間的差距，例如公司債減公債，或 10 年期減 2 年期公債。擴大或倒掛常是警訊。",
    "殖利率曲線": "把不同年期公債的利率連成一條線。正常是長天期利率較高；短天期反而較高（倒掛）在歷史上常出現在衰退之前。",
    "倒掛": "本來應該比較低的那個數字反而比較高，例如短期利率高於長期利率，或 VIX 高於 VIX3M；常被視為壓力訊號。",
    "超額債券溢酬": "公司債利差中扣掉違約風險之後剩下的部分（EBP），代表投資人的風險胃口；偏高時經濟常轉弱。",
    "EBP": "超額債券溢酬：公司債利差中扣掉違約風險後剩下的部分，代表投資人的風險胃口；偏高時經濟常轉弱。",
    "本益比": "股價除以每股盈餘：投資人願意為公司每賺 1 元付幾元。越高代表市場期待越高，也越容易失望。",
    "百分位": "在歷史上排第幾：第 90 百分位＝比過去 90% 的時間都高，第 5 百分位＝比過去 95% 的時間都低。",
    "RSI": "相對強弱指標（0–100）：最近漲的力道和跌的力道比較；70 以上常被說過熱，30 以下常被說超賣。",
    "200 日均線": "過去 200 個交易日（約 10 個月）的平均價格，常被當成長期趨勢線；價格在它之上通常代表長期趨勢向上。",
    "乖離": "現在價格離平均線有多遠（%）。乖離太大代表短期漲或跌得太快，常會往平均線拉回。",
    "隱含波動": "從選擇權價格反推出市場預期未來會漲跌多大；越高代表大家預期波動越大。",
    "波動率": "價格上下跳動的幅度，通常以年化 % 表示；越高代表越不穩、風險越大。",
    "融資餘額": "散戶向券商借錢買股票的總金額。暴增代表散戶很樂觀；股價大跌時可能被券商強制賣股（斷頭），讓跌勢加快。",
    "未平倉": "期貨或選擇權還沒結清的契約數量；看外資的淨未平倉可以知道他們押多還是押空、押多大。",
    "空單": "押注價格下跌的部位；也常用來避險（手上有股票，怕跌先買保險）。",
    "多單": "押注價格上漲的部位。",
    "CISS": "歐洲央行的系統性壓力指數（0–1），綜合股、債、匯、貨幣市場與銀行的壓力；越高越緊繃。",
    "金融壓力指數": "把利率、利差、波動、資金市場等指標綜合成一個數字；大於 0 代表壓力高於平常。",
    "R-zone": "研究發現的危險組合：信用（借錢）快速擴張，同時資產價格也過熱；之後 3 年發生金融危機的機率明顯升高。",
    "Altman Z": "用財報算出的破產風險分數；分數越低，代表公司財務越接近危險區。",
    "違約機率": "公司在一段時間內還不出債務的估計機率；本站以股價與負債推算，屬模型估計。",
    "回撤": "從最高點跌下來的幅度（%）。例如從 100 跌到 70＝回撤 30%。",
    "成本殖利率": "一年領到的股息除以你當初的持有成本；股價漲了，它不會變低。",
    "殖利率": "一年的配息（或利息）除以現在的價格（%）。",
    "反向 DCF": "倒過來算：要支撐現在的股價，公司未來 10 年每年大概要成長多少。數字越高，代表市場的期待越高。",
    "折現率": "把未來的錢換算成今天價值時用的年利率；越高，未來的錢在今天就越不值錢。",
    "自由現金流": "公司營業賺進的現金扣掉資本支出之後，真正可以自由運用的錢（配息、還債、買回股票）。",
    "資本支出": "公司花在廠房、機器、資料中心等長期設備上的錢。",
    "每股盈餘": "公司淨利除以股數（EPS）：每一股幫股東賺了多少錢。",
    "EPS": "每股盈餘：公司淨利除以股數，每一股幫股東賺了多少錢。",
    "期限結構": "同一種東西不同到期日的價格排在一起的樣子，例如 1 個月、3 個月 VIX；形狀變化可以看出短期壓力。",
    "高收益債": "信用評等較低的公司發的債（俗稱垃圾債），利息高、對景氣很敏感，常是信用市場的溫度計。",
    "巴菲特指標": "股市總市值除以 GDP。越高代表股價相對經濟規模越貴；它可以很多年都偏高，不適合拿來抓時間點。",
    "SLOOS": "聯準會每季的銀行放款調查：銀行放寬或收緊放款標準。收緊常領先景氣轉弱。",
    "流動性": "資金好不好取得、資產能不能很快以合理價格賣掉；流動性變差時，小賣壓也會造成大跌。",
    "美元指數": "美元對一籃子主要貨幣的強弱。美元急升時，全球資金常收緊、新興市場壓力變大。",
    "費半": "費城半導體指數，美國主要晶片股的指數，和台股（尤其台積電）連動很高。",
    "信賴區間": "考慮樣本太少帶來的誤差後，真實數值大概落在的範圍；範圍越寬，代表結論越不確定。",
    "假警報": "警示亮了，但之後並沒有發生預期中的大跌。",
    "基點": "利率單位，1 個基點＝0.01 個百分點；100 個基點＝1%。",
    "z-score": "離平均值有幾個標準差；+2 代表比平常高很多，−2 代表低很多。",
    "AUC": "預測模型分辨好壞的能力（0.5＝跟丟銅板一樣，1＝完美）。0.7 左右算有一點參考價值。",
}

JS = ("(function(){var G=" + json.dumps(GLOSS, ensure_ascii=False) + ";" + r"""
var keys=Object.keys(G).sort(function(a,b){return b.length-a.length;});
var esc=function(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');};
// ASCII terms must stand alone (VIX must not match inside VIX3M or a ticker)
var RE=new RegExp(keys.map(function(k){var e=esc(k);return /^[A-Za-z]/.test(k)?'(?<![A-Za-z0-9])'+e+'(?![A-Za-z0-9])':e;}).join('|'),'g');
var SKIP='a,button,script,style,svg,h2,h3,summary,th,.upd,.gl,.pill,.tile,.ptab,.crumb,label,select,option,input,textarea,.qtab';
function inPage(el){var p=el.closest('.page');return !p||p.classList.contains('on');}
function run(root,all){
 if(document.documentElement.lang==='en')return;
 (root||document).querySelectorAll('.card').forEach(function(card){
  if(card.dataset.gl==='1'||(!all&&!inPage(card)))return;card.dataset.gl='1';
  var seen={},w=document.createTreeWalker(card,NodeFilter.SHOW_TEXT,null),nodes=[],n;
  while((n=w.nextNode()))nodes.push(n);
  nodes.forEach(function(t){
   if(!t.nodeValue||!t.parentElement||t.parentElement.closest(SKIP))return;
   var cell=t.parentElement.closest('td');if(cell&&cell.textContent.length<24)return;
   RE.lastIndex=0;var s=t.nodeValue,m,f=null,last=0;
   while((m=RE.exec(s))){if(seen[m[0]])continue;seen[m[0]]=1;f=f||document.createDocumentFragment();
    if(m.index>last)f.appendChild(document.createTextNode(s.slice(last,m.index)));
    var g=document.createElement('span');g.className='gl';g.tabIndex=0;g.dataset.g=m[0];g.textContent=m[0];f.appendChild(g);last=m.index+m[0].length;}
   if(!f)return;if(last<s.length)f.appendChild(document.createTextNode(s.slice(last)));t.parentNode.replaceChild(f,t);});});}
var tip=document.createElement('div');tip.className='gltip';tip.hidden=true;tip.setAttribute('role','tooltip');document.body.appendChild(tip);var cur=null;
function show(el){var k=el.dataset.g;if(!G[k])return;cur=el;tip.textContent='';var b=document.createElement('b');b.textContent=k+'：';tip.appendChild(b);
 tip.appendChild(document.createTextNode(G[k]));tip.hidden=false;var r=el.getBoundingClientRect(),w=Math.min(320,window.innerWidth-24);tip.style.width=w+'px';
 var x=Math.max(12,Math.min(r.left,window.innerWidth-w-12)),y=r.bottom+6;if(y+tip.offsetHeight>window.innerHeight-8)y=Math.max(8,r.top-tip.offsetHeight-6);
 tip.style.left=x+'px';tip.style.top=y+'px';}
function hide(){tip.hidden=true;cur=null;}
document.addEventListener('mouseover',function(ev){var g=ev.target.closest&&ev.target.closest('.gl');if(g)show(g);});
document.addEventListener('mouseout',function(ev){var g=ev.target.closest&&ev.target.closest('.gl');if(g&&!(ev.relatedTarget&&g.contains(ev.relatedTarget)))hide();});
document.addEventListener('click',function(ev){var g=ev.target.closest('.gl');if(g){ev.stopPropagation();if(cur===g&&!tip.hidden&&ev.pointerType!=='mouse')hide();else show(g);}else if(!ev.target.closest('.gltip'))hide();},true);
document.addEventListener('focusin',function(ev){if(ev.target.classList&&ev.target.classList.contains('gl'))show(ev.target);});
document.addEventListener('keydown',function(ev){if(ev.key==='Escape')hide();});
window.addEventListener('scroll',hide,{passive:true});
run();
document.addEventListener('wss:page',function(){hide();run();});
var lb=document.getElementById('langBtn');if(lb)lb.addEventListener('click',function(){setTimeout(function(){hide();document.querySelectorAll('.card[data-gl]').forEach(function(c){c.dataset.gl='';});run();},0);});
})();
""")

CSS = (".gl{text-decoration:underline dotted;text-decoration-color:var(--tx2);text-underline-offset:3px;cursor:help}"
       ".gl:hover,.gl:focus{text-decoration-color:var(--ac);outline:none}"
       ".gltip{position:fixed;z-index:90;padding:9px 12px;border:1px solid var(--bd);border-radius:10px;background:var(--card,var(--page));color:var(--tx);"
       "font-size:13px;line-height:1.6;box-shadow:0 6px 24px rgba(0,0,0,.25);pointer-events:none}.gltip b{color:var(--ac)}")
