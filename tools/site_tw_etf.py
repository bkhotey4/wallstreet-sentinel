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


def all_rows(eng) -> list:
    """Every listed ETF from the TWSE NAV feed: [code, name, kind, price, premium, size 億, today net 億, holders]."""
    from wsb.data import tw_etf as D
    d = D.load()
    hd = d.get("holders") or {}
    last = hd[max(hd)] if hd else {}
    out = []
    for k, v in (d.get("nav") or {}).items():
        aum = v["units"] * v["nav"] / 1e8 if v.get("units") and v.get("nav") else None
        fl = (v.get("dunits") or 0) * v["nav"] / 1e8 if v.get("dunits") is not None and v.get("nav") else None
        h = (last.get(k) or [None])[0]
        out.append([k, v.get("name") or k, D.kind_of(k, v.get("name") or ""), v.get("px"), v.get("prem"),
                    round(aum, 1) if aum is not None else None, round(fl, 2) if fl is not None else None, h])
    return sorted(out, key=lambda x: -(x[5] or 0))


def sec_etf_all(eng) -> str:
    r = _r(eng)
    if not r.get("available"):
        return ""
    rows = all_rows(eng)
    if not rows:
        return ""
    from wsb.data import tw_etf as D
    nav = D.load().get("nav") or {}
    asof = max((f"{v['date']} {v.get('time') or ''}".strip() for v in nav.values() if v.get("date")), default="")
    core = {c: k for k, xs in D.CORE.items() for c in xs}
    js = json.dumps({"rows": rows, "core": core, "asof": asof}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = (_lead(f"一句話看懂：台灣目前掛牌的 {len(rows)} 檔 ETF 都在這裡，輸入代號或名稱（例如 00999A、高息、美債）就能查；點「詳情」看一年高低點、配息率和波動。")
            + f'<form class="lqf" id="etsf" autocomplete="off"><input id="etsq" class="lqin" maxlength="20" placeholder="00999A、高息、美債、主動" aria-label="search"></form>'
              f'<p class="small muted" id="etsu">🕒 {T("資料時間：", "Data as of ")}{esc(asof or "—")}{T("（網站更新時）", " (site build)")}</p>'
              f'<p class="small muted" id="etsn"></p><div class="scroll"><table class="mini" id="etst"></table></div>'
            + f'<script type="application/json" id="etf-all">{js}</script>'
            + _how("清單、價格、淨值、規模與今天申贖來自證交所「ETF 即時淨值」：在 Cloudflare 版網址打開時直接即時抓（每 2 分鐘更新，新上市的 ETF 會自動出現），"
                   "其他情況用網站更新時的資料；受益人數來自集保結算所（每週）。"
                   "沒輸入時列出規模最大的 30 檔。「詳情」會即時向本站的報價服務查一年的日資料（Yahoo），只送出 ETF 代號。"
                   "類型依代號與名稱自動判斷（B＝債券、L／R＝槓桿反向、A＝主動式、名稱有「息」＝高股息），可能有少數分錯。不是投資建議。"))
    return card("全部台灣 ETF 查詢", "Search every Taiwan ETF", body, "wide")


def sec_etf_tool(eng) -> str:
    r = _r(eng)
    if not r.get("available"):
        return ""
    data = tool_data(r)
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = (_lead("一句話看懂：輸入任何台灣 ETF 代號和起始日期，看從那天投入到現在，含配息會變多少（例如你以前持有、後來出場的 ETF，現在會是多少）。")
            + f'<form class="lqf" id="etff" autocomplete="off"><input id="etfc" class="lqin" maxlength="10" value="0056" list="etfl" aria-label="ETF">'
              f'<datalist id="etfl"></datalist>'
              f'<input id="etfd" class="lqin" type="date" aria-label="start">'
              f'<input id="etfa" class="lqin" type="number" min="1000" step="1000" value="100000" aria-label="amount">'
              f'<button class="btn" type="submit">{T("試算", "Calculate")}</button></form><div id="etfo"></div>'
            + f'<script type="application/json" id="etf-data">{js}</script>'
            + _how("用每週收盤價計算（起始日對到那一週），配息用實際的除息日與金額，最多回溯 5 年。「配息領現金」＝配息不再投入；「配息再投入」＝每次配息在除息那週買回同一檔。"
                   "熱門 ETF 用網站內建資料；其他代號會即時向本站的報價服務查（Yahoo，只在 Cloudflare 版網址可用）。"
                   "未計手續費、稅與匯費。輸入的金額與日期只在你的瀏覽器計算，不會送出或保存。這是歷史回顧，不代表未來，也不是投資建議。", "怎麼算的"))
    return card("ETF 回顧試算", "ETF look-back calculator", body, "wide")


JS = r"""
(function(){
 function fm(x,d){return x==null||isNaN(x)?'—':(+x).toLocaleString('zh-TW',{minimumFractionDigits:d||0,maximumFractionDigits:d||0});}
 function sg(x,d){return x==null||isNaN(x)?'—':(x>=0?'+':'')+fm(x,d==null?1:d)+'%';}
 function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
 var EA={rows:[],core:{}};try{EA=JSON.parse((document.getElementById('etf-all')||{}).textContent||'{}');}catch(e){}
 var ALL=EA.rows||[],HOLD={};ALL.forEach(function(r){if(r[7])HOLD[r[0]]=r[7];});
 function kindOf(c,n){if(EA.core&&EA.core[c])return EA.core[c];if(/B$/.test(c))return '債券';if(/[LR]$/.test(c))return '槓桿反向';if(/A$/.test(c))return '主動式';
  if(/U$/.test(c)||n.indexOf('期貨')>=0)return '商品期貨';if(n.indexOf('息')>=0||n.indexOf('收益')>=0)return '高股息';return '其他股票型';}
 var dl=document.getElementById('etfl');
 var D={};try{D=JSON.parse((document.getElementById('etf-data')||{}).textContent||'{}');}catch(e){}
 // one live request for both listings (.TW / .TWO); the one Yahoo knows comes back
 function live(code,mode){return fetch('api/quote?s='+encodeURIComponent(code+'.TW,'+code+'.TWO')+'&'+mode+'=1',{cache:'no-store'})
   .then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){var q=d.q||{};return q[code+'.TW']||q[code+'.TWO']||null;});}
 // ---------------- search every ETF
 var qi=document.getElementById('etsq'),tb=document.getElementById('etst'),nn=document.getElementById('etsn');
 if(qi&&tb){
  function draw(){var s=qi.value.trim().toUpperCase(),hit=s?ALL.filter(function(r){return r[0].toUpperCase().indexOf(s)>=0||r[1].toUpperCase().indexOf(s)>=0||r[2].indexOf(s)>=0;}):ALL;
   nn.textContent=s?('找到 '+hit.length+' 檔'+(hit.length>60?'，只列前 60 檔':'')):'規模最大的 30 檔（共 '+ALL.length+' 檔，輸入代號或名稱查詢）';
   hit=hit.slice(0,s?60:30);tb.textContent='';var h=tb.insertRow();
   ['ETF','類型','價格','折溢價','規模（億）','今天申贖（億）','受益人（萬）',''].forEach(function(x,i){var th=el('th',i>1&&i<7?'r':'',x);h.appendChild(th);});
   hit.forEach(function(r){var tr=tb.insertRow(),c0=tr.insertCell();c0.appendChild(el('b','',r[0]));c0.appendChild(document.createTextNode(' '+r[1].slice(0,16)));
    tr.insertCell().textContent=r[2];
    [[fm(r[3],2),''],[r[4]==null?'—':sg(r[4],2),r[4]!=null&&Math.abs(r[4])>=1?'dn':''],[fm(r[5],0),''],[r[6]==null?'—':(r[6]>=0?'+':'')+fm(r[6],1),r[6]>0?'up':r[6]<0?'dn':''],[r[7]?fm(r[7]/1e4,1):'—','']]
     .forEach(function(v){var c=tr.insertCell();c.className='r '+v[1];c.textContent=v[0];});
    var bc=tr.insertCell(),b=el('button','btn','詳情');b.type='button';bc.appendChild(b);
    b.addEventListener('click',function(){var nx=tr.nextSibling;if(nx&&nx.className==='etsd'){nx.remove();return;}
     var dr=tb.insertRow(tr.rowIndex+1);dr.className='etsd';var dc=dr.insertCell();dc.colSpan=8;dc.className='small';dc.textContent='查詢中…';
     live(r[0],'full').then(function(q){if(!q){dc.textContent='報價服務沒有這檔的資料（或只在 Cloudflare 版網址可用）。';return;}
      var y=q.div12&&q.price?q.div12/q.price*100:null,off=q.hi52?(q.price/q.hi52-1)*100:null;
      dc.textContent='現價 '+fm(q.price,2)+'；一年高點 '+fm(q.hi52,2)+'、低點 '+fm(q.lo52,2)+(off!=null?'（離高點 '+sg(off)+'）':'')
       +'；近 12 個月配息 '+fm(q.div12,3)+' 元'+(y!=null?'（配息率約 '+fm(y,1)+'%）':'')+'；近一個月年化波動 '+fm(q.vol20,0)+'%'
       +(q.ma_gap!=null?'；距 200 日均線 '+sg(q.ma_gap):'')+'。上市未滿一年的，一年數字只涵蓋上市以來。';
      var go=el('button','btn','用回顧試算');go.type='button';go.style.marginLeft='8px';dc.appendChild(go);
      go.addEventListener('click',function(){var ci=document.getElementById('etfc');if(ci){ci.value=r[0];ci.scrollIntoView({behavior:'smooth',block:'center'});}});})
     .catch(function(){dc.textContent='查詢失敗（這個功能只在 Cloudflare 版網址可用：wallstreet-sentinel.pages.dev）。';});});});}
  qi.addEventListener('input',draw);document.getElementById('etsf').addEventListener('submit',function(e){e.preventDefault();draw();});draw();
  // live list straight from TWSE through /api/etf: new listings and current prices without waiting for a site build
  var lu=document.getElementById('etsu'),ldead=false;
  function pullAll(){if(ldead||document.hidden)return;fetch('api/etf',{cache:'no-store'}).then(function(r){if(r.status===404||r.status===405){ldead=true;throw 0;}if(!r.ok)throw 0;return r.json();}).then(function(d){
    var rs=(d.rows||[]).map(function(x){var aum=x[2]&&x[5]?x[2]*x[5]/1e8:null,fl=x[3]!=null&&x[5]?x[3]*x[5]/1e8:null;
      return [x[0],x[1],kindOf(x[0],x[1]),x[4],x[6],aum,fl,HOLD[x[0]]||null,(x[7]||'')+' '+(x[8]||'').slice(0,5)];});
    if(!rs.length)throw 0;rs.sort(function(a,b){return (b[5]||0)-(a[5]||0);});ALL=rs;
    var t=rs.map(function(r){return r[8];}).sort().pop()||'';
    if(lu)lu.textContent='🕒 資料時間：證交所 '+t.trim()+'（即時，每 2 分鐘自動更新；共 '+rs.length+' 檔）';
    if(dl&&dl.options.length!==rs.length){dl.textContent='';rs.forEach(function(r){var o=document.createElement('option');o.value=r[0];o.label=r[1].slice(0,16);dl.appendChild(o);});}
    draw();}).catch(function(){});}
  pullAll();setInterval(pullAll,120000);document.addEventListener('visibilitychange',function(){if(!document.hidden)pullAll();});}
 // ---------------- look-back calculator (any code)
 var f=document.getElementById('etff');if(!f)return;
 if(dl)ALL.forEach(function(r){var o=document.createElement('option');o.value=r[0];o.label=r[1].slice(0,16);dl.appendChild(o);});
 var dd=document.getElementById('etfd');try{var t=new Date();t.setFullYear(t.getFullYear()-1);dd.value=t.toISOString().slice(0,10);}catch(e){}
 function calc(e,s,A,o){function line(t,c){o.appendChild(el('p',c||'',t));}
  var w=e.w,i0=-1;for(var i=0;i<w.length;i++){if(w[i][0]>=s){i0=i;break;}}
  if(i0<0||i0>=w.length-1){line('起始日期太近或超出資料範圍（這檔資料從 '+w[0][0]+' 開始）。','muted');return;}
  if(s<w[0][0])line('這檔的資料從 '+w[0][0]+' 開始，改從那天計算。','muted');
  var p0=w[i0][1],pn=w[w.length-1][1],sh=A/p0,cash=0,shR=sh,peak=0,mdd=0;
  function px(dt){for(var k=i0;k<w.length;k++){if(w[k][0]>=dt)return w[k][1];}return pn;}
  (e.dv||[]).forEach(function(v){if(v[0]>w[i0][0]&&v[0]<=w[w.length-1][0]){cash+=sh*v[1];shR+=shR*v[1]/px(v[0]);}});
  for(var k=i0;k<w.length;k++){var val=w[k][1];if(val>peak)peak=val;var x=val/peak-1;if(x<mdd)mdd=x;}
  var v1=sh*pn+cash,v2=shR*pn;
  line((e.n?e.n+'：':'')+'從 '+w[i0][0]+'（每單位 '+fm(p0,2)+' 元）投入 NT$ '+fm(A)+'，到 '+w[w.length-1][0]+'（'+fm(pn,2)+' 元）：');
  line('• 配息領現金：市值 NT$ '+fm(sh*pn)+' ＋ 領到配息 NT$ '+fm(cash)+' ＝ NT$ '+fm(v1)+'（'+sg((v1/A-1)*100)+'）');
  line('• 配息再投入：NT$ '+fm(v2)+'（'+sg((v2/A-1)*100)+'）');
  line('• 期間價格最大回落 '+fm(mdd*100,1)+'%（以週收盤計）','small muted');
  line('歷史回顧，未計手續費與稅，不代表未來，不是投資建議。','small muted');}
 f.addEventListener('submit',function(ev){ev.preventDefault();var o=document.getElementById('etfo');o.textContent='';
  var code=document.getElementById('etfc').value.trim().toUpperCase(),s=dd.value,A=+document.getElementById('etfa').value;
  if(!code||!s||!(A>0)){o.appendChild(el('p','muted','請輸入 ETF 代號、起始日期和金額。'));return;}
  var nm=(ALL.filter(function(r){return r[0]===code;})[0]||[])[1]||'';
  if(D[code]){calc(D[code],s,A,o);return;}
  o.appendChild(el('p','muted','查詢 '+code+' 的歷史資料中…'));
  live(code,'hist').then(function(h){o.textContent='';if(!h||!h.w||h.w.length<2){o.appendChild(el('p','muted','找不到 '+code+' 的歷史價格（請確認代號，或改用 Cloudflare 版網址）。'));return;}
   calc({n:code+' '+nm.slice(0,14),w:h.w,dv:h.dv},s,A,o);})
  .catch(function(){o.textContent='';o.appendChild(el('p','muted','查詢失敗（這檔不在內建清單，需要 Cloudflare 版網址的即時報價服務：wallstreet-sentinel.pages.dev）。'));});});
})();
"""
