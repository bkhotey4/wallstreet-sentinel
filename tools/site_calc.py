"""工具頁：部位風控試算器。使用者自己輸入資金、價格、型態失效價、每筆可承受虧損比例（選填：目標價、勝率、平均賺賠比、ATR），
瀏覽器裡用固定公式算出股數上限、部位占比、風報比與凱利比例。不送出任何資料、不讀任何持倉，結果完全取決於輸入。"""
from __future__ import annotations

from tools.sitekit import T, card


def sec_sizing(eng) -> str:
    def f(i, zh, en, ph, step="any"):
        return (f'<label class="szf"><span>{T(zh, en)}</span><input id="sz_{i}" type="number" inputmode="decimal" step="{step}" '
                f'placeholder="{ph}" aria-label="{zh}"></label>')
    form = ('<div class="szg">'
            + f("cap", "總資金", "Capital", "例：1000000")
            + f("px", "價格", "Price", "例：150")
            + f("stop", "型態失效價（自訂）", "Invalidation price", "例：138")
            + f("risk", "每筆最多可承受虧損（% 資金）", "Max loss per idea (% of capital)", "例：1")
            + f("tgt", "目標價（選填，用來算風報比）", "Target (optional)", "例：180")
            + f("atr", "ATR（選填；沒填失效價時用 2×ATR）", "ATR (optional)", "例：4.5")
            + f("win", "勝率 %（選填，凱利公式用）", "Win rate % (optional)", "例：45")
            + f("rr", "平均賺賠比（選填，凱利公式用）", "Avg win ÷ avg loss (optional)", "例：2")
            + "</div>")
    out = '<div class="szo" id="sz_out" aria-live="polite"></div>'
    note = T("公式：每股風險＝價格−失效價；可承受虧損＝總資金×比例；股數上限＝可承受虧損÷每股風險（無條件捨去）；風報比＝(目標價−價格)÷每股風險；"
             "凱利比例＝勝率−(1−勝率)÷賺賠比。凱利公式假設勝率和賺賠比都準確，實務上常只用一半或更少，而且估錯時虧損會被放大。"
             "這是純數學試算工具：所有數字都由你自己輸入，只在你的瀏覽器裡計算，不會送出或儲存；結果不是投資建議，也不代表任何標的值得交易。",
             "Pure arithmetic on your own inputs, computed in your browser and never sent. Not investment advice.")
    return card("部位風控試算器：依你設定的風險算股數上限", "Position-size calculator", form + out + f'<p class="note">{note}</p>', "wide")


CSS = (".szg{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:6px 0 10px}"
       ".szf{display:flex;flex-direction:column;gap:4px;font-size:12.5px;min-width:0}.szf input{padding:7px 9px;border:1px solid var(--bd);"
       "border-radius:8px;background:var(--bg,transparent);color:inherit;font-size:14px;min-width:0}"
       ".szo{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}.szo div{padding:8px 10px;border-radius:8px;background:var(--wash)}"
       ".szo b{display:block;font-size:18px}.szo .szwarn{grid-column:1/-1;background:none;color:var(--dn);padding:0}")
JS = r"""
(function(){var o=document.getElementById('sz_out');if(!o)return;var ids=['cap','px','stop','risk','tgt','atr','win','rr'];
 function v(k){var e=document.getElementById('sz_'+k);var x=parseFloat(e&&e.value);return isFinite(x)?x:null;}
 function fm(x,d){return x.toLocaleString(undefined,{maximumFractionDigits:d==null?2:d});}
 function cell(l,val){var d=document.createElement('div');d.appendChild(document.createTextNode(l));var b=document.createElement('b');b.textContent=val;d.appendChild(b);return d;}
 function warn(t){var d=document.createElement('div');d.className='szwarn';d.textContent=t;return d;}
 function calc(){var en=document.documentElement.lang==='en';o.textContent='';var cap=v('cap'),px=v('px'),stop=v('stop'),risk=v('risk'),tgt=v('tgt'),atr=v('atr'),win=v('win'),rr=v('rr');
  if(stop==null&&atr!=null&&px!=null)stop=px-2*atr;
  if(cap==null||px==null||stop==null||risk==null){o.appendChild(warn(en?'Fill in capital, price, invalidation (or ATR) and max loss %.':'請填總資金、價格、型態失效價（或 ATR）和可承受虧損比例。'));return;}
  var ps=px-stop;if(ps<=0){o.appendChild(warn(en?'Invalidation price must be below the price.':'型態失效價要低於價格。'));return;}
  var loss=cap*risk/100,sh=Math.floor(loss/ps),pos=sh*px;
  o.appendChild(cell(en?'Risk per share':'每股風險',fm(ps)+'（'+fm(ps/px*100,1)+'%）'));
  o.appendChild(cell(en?'Max loss':'可承受虧損',fm(loss,0)));
  o.appendChild(cell(en?'Max shares':'股數上限',fm(sh,0)));
  o.appendChild(cell(en?'Position size':'部位金額',fm(pos,0)+'（'+fm(pos/cap*100,1)+'%）'));
  if(tgt!=null&&tgt>px)o.appendChild(cell(en?'Reward ÷ risk':'風報比',fm((tgt-px)/ps,2)+' : 1'));
  if(win!=null&&rr!=null&&rr>0){var w=win/100,k=w-(1-w)/rr;o.appendChild(cell(en?'Kelly (full / half)':'凱利比例（全／半）',k>0?(fm(k*100,1)+'% / '+fm(k*50,1)+'%'):(en?'≤ 0: negative edge':'≤ 0：期望值為負')));}
  if(pos>cap)o.appendChild(warn(en?'Position exceeds capital (would need leverage).':'部位金額超過總資金（需要槓桿）。'));}
 ids.forEach(function(k){var e=document.getElementById('sz_'+k);if(e)e.addEventListener('input',calc);});calc();})();
"""
