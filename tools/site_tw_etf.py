"""台灣 ETF page: what the money is doing (size, creations / redemptions, premium to NAV), each popular ETF's return
with dividends, yield, drawdown and 填息, the ex-dividend calendar, two things ETF holders often miss (leveraged-ETF drag,
the currency part of US-bond ETFs) and a look-back calculator.  Data and rules only (wsb.analytics.tw_etf); not advice."""
from __future__ import annotations

import json

import pandas as pd

from tools.sitekit import T, card, cls, esc, num

KIND_ORDER = ["市值型", "高股息", "主動式", "其他股票型", "債券", "槓桿反向", "商品期貨"]
KIND_EN = {"市值型": "Broad market", "高股息": "High dividend", "主動式": "Active", "其他股票型": "Other equity",
           "債券": "Bonds", "槓桿反向": "Leveraged / inverse", "商品期貨": "Commodity futures"}


def _r(eng):
    r = getattr(eng, "_tw_etf", None)
    if r is None:
        from wsb.analytics import tw_etf as E
        try:
            r = E.build(eng)
        except Exception:  # noqa: BLE001
            r = {"available": False}
        eng._tw_etf = r
    return r


def _how(txt: str, label: str = "這張表怎麼看") -> str:
    return f'<details class="sgx"><summary>{T(label, "How to read")}</summary><p class="note">{T(txt, "")}</p></details>'


def _lead(txt: str) -> str:
    return f'<p class="rimp big2"><b>{T(txt, "")}</b></p>'


def _yi(x, d=0, sign=False) -> str:
    return "—" if x is None else f'<span class="{cls(x) if sign else ""}">{num(x, d, sign=sign)}</span>'


# ------------------------------------------------------------------ 資金流向與折溢價
def sec_etf_flow(eng) -> str:
    from wsb.analytics import tw_etf as E
    r = _r(eng)
    if not r.get("available"):
        return card("台灣 ETF", "Taiwan ETFs", f'<p class="muted">{T("台灣 ETF 資料暫時取不到。", "Taiwan ETF data unavailable.")}</p>')
    k = r.get("kinds") or {}
    rows = []
    for name in KIND_ORDER:
        g = k.get(name)
        if not g:
            continue
        z = g.get("z")
        zt = ("—" if z is None else f'{z:+.1f}σ' + (" ⚠️" if abs(z) >= 3 else ""))
        rows.append(f'<tr><td>{T(name, KIND_EN[name])}</td><td class="r">{g["n"]}</td><td class="r">{num(g["aum"], 0)}</td>'
                    f'<td class="r">{_yi(g["flow"], 1, True)}</td><td class="r">{_yi(g.get("flow20"), 0, True)}</td><td class="r">{zt}</td></tr>')
    tab = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("類型", "Kind")}</th><th class="r">{T("檔數", "N")}</th>'
           f'<th class="r">{T("規模（億元）", "Assets (NT$100m)")}</th><th class="r">{T("今天申贖（億）", "Today net (NT$100m)")}</th>'
           f'<th class="r">{T("近 20 日（億）", "20 days")}</th><th class="r">{T("今天和自己歷史比", "vs own history")}</th></tr></thead>'
           f'<tbody>{"".join(rows)}</tbody></table></div>')
    hist_note = (f"資料日 {r.get('asof') or '—'}。申贖歷史累積 {r['n_days']} 天" +
                 ("（滿 40 天後才和自己的歷史比較，σ＝標準差，超過 ±3σ 標 ⚠️）。" if r["n_days"] < E.MIN_HIST + 1 else "。"))
    pr = r.get("prem") or []
    if pr:
        def _pl(x):
            t = "市價比淨值" + ("貴" if x["prem"] > 0 else "便宜") + " " + format(abs(x["prem"]), ".2f") + "%"
            return (f'<li><b>{esc(x["code"])} {esc(x["name"][:16])}</b>：{T(t, "")}'
                    f'<span class="small muted">（{T("規模", "size")} {num(x["aum"], 0)} {T("億", "")}）</span></li>')
        li = "".join(_pl(x) for x in pr[:10])
        pblock = (f'<h3>{T("⚠️ 市價和淨值差 1% 以上（規模 10 億以上）", "Premium / discount ≥ 1%")}</h3><ul>{li}</ul>'
                  f'<p class="small muted">{T("溢價＝你付的價格比 ETF 裡面的資產還貴；之後溢價收斂時，就算資產沒跌，市價也會跌。常見於額度用完暫停申購、或海外市場休市時。", "")}</p>')
    else:
        pblock = f'<p>{T("規模 10 億以上的 ETF，市價都貼近淨值（差距小於 1%）。" if r.get("n_prem_known") else "淨值資料暫缺，折溢價無法判斷。", "")}</p>'
    how = ("資料來自證交所「ETF 即時淨值」：每檔 ETF 的市價、投信估計的淨值、流通單位數。今天申贖＝流通單位數的變化 × 淨值："
           "正數＝有人拿錢向投信申購（新的錢進來），負數＝贖回（錢流出）。規模＝單位數 × 淨值。"
           "市值型只列台灣 50 類（0050、006208），其他追蹤指數的股票 ETF（科技、海外、台灣 TOP50 等）歸在「其他股票型」。"
           "資金大量流進高股息 ETF 時，這些 ETF 定期換股會讓成分股出現大量買賣，是台股的二階效應之一。")
    body = (_lead("一句話看懂：" + E.headline(r)) + tab + f'<p class="small muted">{T(hist_note, "")}</p>' + pblock + _how(how))
    return card("台灣 ETF：錢往哪裡去", "Taiwan ETFs: where the money goes", body, "wide")


# ------------------------------------------------------------------ 熱門 ETF 一覽
def sec_etf_table(eng) -> str:
    r = _r(eng)
    if not r.get("available") or not r.get("rows"):
        return ""
    rows = sorted(r["rows"], key=lambda x: (KIND_ORDER.index(x["kind"]) if x["kind"] in KIND_ORDER else 9, -(x.get("aum") or 0)))
    tr = []
    for x in rows:
        pw = x.get("prem") is not None and abs(x["prem"]) >= 1
        h1w = x.get("holders_1w")
        ndv = '<div class="small muted">' + str(x["n_div12"]) + " 次</div>" if x.get("n_div12") else ""
        tr.append(
            f'<tr><td><b>{esc(x["code"])}</b> {esc(x["name"][:12])}<div class="small muted">{T(x["kind"], KIND_EN.get(x["kind"], ""))}</div></td>'
            f'<td class="r">{num(x.get("px"), 2)}</td>'
            f'<td class="r">{"<b class=dn>" if pw else ""}{num(x.get("prem"), 2, sign=True)}{"%</b>" if pw else ("%" if x.get("prem") is not None else "")}</td>'
            f'<td class="r">{num(x.get("aum"), 0)}</td><td class="r">{_yi(x.get("flow"), 1, True)}</td>'
            f'<td class="r">{_yi(x.get("tr1y"), 1, True)}</td><td class="r">{_yi(x.get("tr3y"), 0, True)}</td>'
            f'<td class="r">{num(x.get("yld"), 1)}{"%" if x.get("yld") is not None else ""}'
            f'{ndv}</td>'
            f'<td class="r">{_yi(x.get("dd1y"), 1, True)}</td>'
            f'<td class="r">{num((x.get("holders") or 0) / 1e4, 1) if x.get("holders") else "—"}'
            f'{"<div class=small>" + _yi(h1w / 1e4, 1, True) + "</div>" if h1w is not None else ""}</td></tr>')
    head = "".join(f'<th class="r">{T(a, b)}</th>' for a, b in (
        ("價格", "Price"), ("折溢價", "Prem."), ("規模（億）", "Size"), ("今天申贖（億）", "Today net"), ("近 1 年含息", "1y total"),
        ("近 3 年含息", "3y total"), ("近 12 月配息率", "12m yield"), ("1 年最大回落", "1y max fall"), ("受益人（萬）", "Holders (10k)")))
    hi = max((x for x in rows if x.get("yld") and x["kind"] == "高股息"), key=lambda x: x["yld"], default=None)
    big = max(rows, key=lambda x: x.get("aum") or 0)
    lead = (f"一句話看懂：最大的是 {big['code']} {big['name']}（{num(big.get('aum'), 0)} 億元）"
            + (f"；高股息類近 12 個月配息率最高的是 {hi['code']}（{hi['yld']:.1f}%），但配息率高不等於總報酬高，要看「含息」那欄" if hi else "") + "。")
    how = ("近 1／3 年含息＝價格變化加上配息（假設配息在除息日再投入），是持有人實際拿到的報酬；只看價格會少算高股息 ETF 的報酬。"
           "近 12 月配息率＝過去 12 個月的配息加總 ÷ 現價，是過去的數字，不保證未來配一樣多（成立不到一年的不計算）。"
           "1 年最大回落＝過去一年從高點到低點最多跌多少（含息），代表抱著它可能遇到的波動。"
           "受益人＝集保結算所每週公布的持有人數，下面小字是一週變化（萬人）；人數快速增加代表散戶湧入。"
           "清單＝常見的熱門 ETF，加上規模最大的 10 檔（每天自動更新）。價格與配息來自 Yahoo，淨值與規模來自證交所。"
           "這是歷史數據整理，不是投資建議。")
    body = (_lead(lead) + f'<div class="scroll"><table class="mini"><thead><tr><th>{T("ETF", "ETF")}</th>{head}</tr></thead>'
            f'<tbody>{"".join(tr)}</tbody></table></div>' + _how(how))
    return card("熱門台灣 ETF 一覽", "Popular Taiwan ETFs", body, "wide")


# ------------------------------------------------------------------ 配息、除息與填息
def sec_etf_div(eng) -> str:
    r = _r(eng)
    if not r.get("available"):
        return ""
    ex = r.get("exdiv") or []
    xl = "".join(f'<tr><td>{esc(x["date"])}</td><td><b>{esc(x["code"])}</b> {esc(x["name"][:12])}</td>'
                 f'<td class="r">{num(x.get("cash"), 3) if x.get("cash") else T("尚未公布", "TBA")}</td>'
                 f'<td class="r">{num(x.get("yld"), 2) + "%" if x.get("yld") is not None else "—"}</td></tr>' for x in ex)
    cal = (f'<h3>{T("📅 未來 45 天除息", "Ex-dividend in the next 45 days")}</h3>'
           + (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("除息日", "Ex-date")}</th><th>ETF</th>'
              f'<th class="r">{T("每單位配息（元）", "Cash")}</th><th class="r">{T("單次配息率", "This payout")}</th></tr></thead><tbody>{xl}</tbody></table></div>'
              if ex else f'<p class="muted">{T("證交所除息預告表目前沒有 ETF。", "")}</p>'))
    fr = []
    for x in r.get("rows") or []:
        f, fh = x.get("fill"), x.get("fill_hist")
        if not f:
            continue
        gap = abs(f.get("gap") or 0)
        st = ("✅ " + T("除息當天就填息" if f["days"] == 0 else str(f["days"]) + " 天填息", "") if f["done"] else
              "⏳ " + T("尚未填息（已 " + str(f["days"]) + " 天，差 " + format(gap, ".2f" if gap < 0.1 else ".1f") + "%）", ""))
        hs = (T(f"{fh['n']} 次中 {fh['share60']:.0f}% 在 60 天內填息" + (f"，中位數 {fh['median']:.0f} 天" if fh.get("median") is not None else ""), "")
              if fh else "—")
        fr.append(f'<tr><td><b>{esc(x["code"])}</b> {esc(x["name"][:10])}</td><td>{esc(f["ex"])}</td><td class="r">{num(f["amt"], 3)}</td>'
                  f'<td>{st}</td><td class="small">{hs}</td></tr>')
    open_n = sum(1 for x in r.get("rows") or [] if x.get("fill") and not x["fill"]["done"])
    lead = (f"一句話看懂：未來 45 天有 {len(ex)} 檔 ETF 除息；" if ex else "一句話看懂：") + (
        f"追蹤的 ETF 中有 {open_n} 檔最近一次配息還沒填息（股價還沒回到除息前）。" if open_n else "追蹤的 ETF 最近一次配息都已填息。")
    tab = (f'<h3>{T("🔁 填息追蹤", "Dividend recovery")}</h3><div class="scroll"><table class="mini"><thead><tr><th>ETF</th>'
           f'<th>{T("最近除息日", "Last ex-date")}</th><th class="r">{T("配息", "Cash")}</th><th>{T("狀態", "Status")}</th>'
           f'<th>{T("過去紀錄", "History")}</th></tr></thead><tbody>{"".join(fr)}</tbody></table></div>')
    how = ("除息日當天股價會扣掉配息，「填息」＝股價漲回除息前一天的收盤價。沒填息時，你領到的配息其實是從自己的本金拿回來，"
           "還要繳稅與補充保費；所以高配息率不等於賺比較多，要看含息總報酬。過去紀錄＝60 天前的歷次配息中，60 天內填息的比例。"
           "除息預告來自證交所（上櫃的債券 ETF 不在這份表裡）。")
    return card("配息、除息與填息", "Dividends, ex-dates and recovery", _lead(lead) + cal + tab + _how(how), "wide")


# ------------------------------------------------------------------ ETF 常被忽略的兩件事
def sec_etf_traps(eng) -> str:
    r = _r(eng)
    if not r.get("available") or not (r.get("lev") or r.get("fx")):
        return ""
    parts, heads = [], []
    lv = r.get("lev")
    if lv:
        heads.append(f"正 2 一年 {lv['lev']:+.0f}%，不是 0050 的兩倍 {lv['x2']:+.0f}%")
        tx = (f"過去一年 0050 {lv['base']:+.1f}%，兩倍是 {lv['x2']:+.1f}%；00631L（台灣 50 正 2）實際 {lv['lev']:+.1f}%，"
              f"差 {lv['gap']:+.1f} 個百分點" + (f"；00632R（反 1）{lv['inv']:+.1f}%" if lv.get("inv") is not None else "") + "。"
              "槓桿 ETF 是「每天」維持 2 倍，來回震盪時會慢慢耗損（波動越大耗損越多"
              + (f"，0050 這一年的年化波動 {lv['vol']:.0f}%" if lv.get("vol") is not None else "") + "），所以適合短期，長期報酬不會剛好是兩倍。")
        parts.append(f'<h3>{T("⚡ 槓桿 ETF 不是長期兩倍", "Leveraged ETFs are not 2× long-term")}</h3><p>{T(tx, "")}</p>')
    fx = r.get("fx")
    if fx:
        heads.append(f"美債 ETF 的報酬有一部分來自匯率（美元兌台幣一年 {fx['fx']:+.1f}%）")
        tx = (f"過去一年 00679B（元大美債 20 年）價格 {fx['etf']:+.1f}%；同期美國 20 年公債 ETF（TLT，美元計價）{fx['usd']:+.1f}%，"
              f"美元兌台幣 {fx['fx']:+.1f}%，兩者合起來約 {fx['combo']:+.1f}%（和 ETF 的差距來自配息時間、追蹤的指數與費用）。"
              "買台灣掛牌的美債 ETF 等於同時承擔美國利率和美元匯率兩個風險：美國降息時債券漲，但如果新台幣同時升值，台幣報酬會被吃掉一部分。")
        parts.append(f'<h3>{T("💱 美債 ETF：利率＋匯率", "US-bond ETFs: rates + currency")}</h3><p>{T(tx, "")}</p>'
                     f'<p class="small"><a class="golink" href="#bonds" data-p="bonds">{T("看美國公債 →", "US Treasuries →")}</a></p>')
    lead = "一句話看懂：" + "；".join(heads) + "。"
    return card("ETF 常被忽略的兩件事", "Two things ETF holders often miss", _lead(lead) + "".join(parts), "wide")


# ------------------------------------------------------------------ 回顧試算
def tool_data(r) -> dict:
    """Weekly closes (last close of each week) + dividends per tracked ETF for the look-back calculator."""
    from wsb.data import tw_etf as D
    d = D.load()
    out = {}
    for x in r.get("rows") or []:
        p = (d.get("px") or {}).get(x["code"])
        if not p:
            continue
        c = pd.Series({pd.Timestamp(a): b for a, b in p["c"]}).sort_index()
        wk = c.groupby(c.index.to_period("W"))
        out[x["code"]] = {"n": x["name"][:14], "w": [[s.index[-1].strftime("%Y-%m-%d"), round(float(s.iloc[-1]), 3)] for _, s in wk],
                          "dv": p.get("dv") or []}
    return out


def sec_etf_tool(eng) -> str:
    r = _r(eng)
    if not r.get("available"):
        return ""
    data = tool_data(r)
    if not data:
        return ""
    opts = "".join(f'<option value="{esc(k)}">{esc(k)} {esc(v["n"])}</option>' for k, v in data.items())
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = (_lead("一句話看懂：選一檔 ETF 和一個起始日期，看從那天投入到現在，含配息會變多少（例如你以前持有、後來出場的 ETF，現在會是多少）。")
            + f'<form class="lqf" id="etff" autocomplete="off"><select id="etfc" class="lqin">{opts}</select>'
              f'<input id="etfd" class="lqin" type="date" min="{min(v["w"][0][0] for v in data.values())}" aria-label="start">'
              f'<input id="etfa" class="lqin" type="number" min="1000" step="1000" value="100000" aria-label="amount">'
              f'<button class="btn" type="submit">{T("試算", "Calculate")}</button></form><div id="etfo"></div>'
            + f'<script type="application/json" id="etf-data">{js}</script>'
            + _how("用每週最後一個收盤價計算（起始日對到那一週），配息用實際的除息日與金額。「配息領現金」＝配息不再投入；「配息再投入」＝每次配息在除息那週買回同一檔。"
                   "未計手續費、稅與匯費。輸入的金額與日期只在你的瀏覽器計算，不會送出或保存。這是歷史回顧，不代表未來，也不是投資建議。", "怎麼算的"))
    return card("ETF 回顧試算", "ETF look-back calculator", body, "wide")


JS = r"""
(function(){var f=document.getElementById('etff');if(!f)return;var D;try{D=JSON.parse(document.getElementById('etf-data').textContent);}catch(e){return;}
 var dd=document.getElementById('etfd');try{var t=new Date();t.setFullYear(t.getFullYear()-1);dd.value=t.toISOString().slice(0,10);}catch(e){}
 function fm(x,d){return x==null||isNaN(x)?'—':x.toLocaleString('zh-TW',{minimumFractionDigits:d||0,maximumFractionDigits:d||0});}
 function sg(x){return (x>=0?'+':'')+fm(x,1)+'%';}
 f.addEventListener('submit',function(ev){ev.preventDefault();var o=document.getElementById('etfo');o.textContent='';
  var e=D[document.getElementById('etfc').value],s=dd.value,A=+document.getElementById('etfa').value;
  function line(t,c){var p=document.createElement('p');if(c)p.className=c;p.textContent=t;o.appendChild(p);}
  if(!e||!s||!(A>0)){line('請選 ETF、起始日期並輸入金額。','muted');return;}
  var w=e.w,i0=-1;for(var i=0;i<w.length;i++){if(w[i][0]>=s){i0=i;break;}}
  if(i0<0||i0>=w.length-1){line('起始日期太近或超出資料範圍（資料從 '+w[0][0]+' 開始）。','muted');return;}
  if(s<w[0][0])line('這檔的資料從 '+w[0][0]+' 開始，改從那天計算。','muted');
  var p0=w[i0][1],pn=w[w.length-1][1],sh=A/p0,cash=0,shR=sh,peak=0,mdd=0;
  function px(dt){for(var k=i0;k<w.length;k++){if(w[k][0]>=dt)return w[k][1];}return pn;}
  e.dv.forEach(function(v){if(v[0]>w[i0][0]&&v[0]<=w[w.length-1][0]){cash+=sh*v[1];shR+=shR*v[1]/px(v[0]);}});
  for(var k=i0;k<w.length;k++){var val=w[k][1];if(val>peak)peak=val;var dd_=val/peak-1;if(dd_<mdd)mdd=dd_;}
  var v1=sh*pn+cash,v2=shR*pn;
  line('從 '+w[i0][0]+'（每單位 '+fm(p0,2)+' 元）投入 NT$ '+fm(A)+'，到 '+w[w.length-1][0]+'（'+fm(pn,2)+' 元）：','');
  line('• 配息領現金：市值 NT$ '+fm(sh*pn)+' ＋ 領到配息 NT$ '+fm(cash)+' ＝ NT$ '+fm(v1)+'（'+sg((v1/A-1)*100)+'）','');
  line('• 配息再投入：NT$ '+fm(v2)+'（'+sg((v2/A-1)*100)+'）','');
  line('• 期間價格最大回落 '+fm(mdd*100,1)+'%（以週收盤計）','small muted');
  line('歷史回顧，未計手續費與稅，不代表未來，不是投資建議。','small muted');});
})();
"""
