"""台股頁：台股泡沫觀察卡。資料與燈號規則見 wsb/data/tw_bubble.py。
每項指標和自己的歷史比（z 分數），不用寫死的門檻；另外把「台股 2027 下半年泡沫破裂」這個假設拆成可以每月檢查的條件。"""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

from tools.sitekit import T, card, esc, fold_rows, num, spark


def _v(eng) -> Dict:
    c = getattr(eng, "_twbubble_view", None)
    if c is None:
        try:
            from wsb.data import tw_bubble as B
            c = B.view(eng)
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._twbubble_view = c
        except Exception:  # noqa: BLE001
            pass
    return c


def _ser(rows) -> pd.Series:
    return pd.Series([r[1] for r in rows], index=pd.to_datetime([r[0] for r in rows]))


def _fmt(x: Dict) -> str:
    return f'{x["now"]:,.{x["dg"]}f}{"%" if x["unit"] == "%" else " " + x["unit"]}'


def fall_text(pk: Dict) -> str:
    """Plain line about the move since the 3-year high (20 % down is the usual 'bear market' line)."""
    if not pk:
        return ""
    if pk["dd"] <= -20:
        tag = "跌幅已超過 20%，達到一般說的「空頭市場」"
    elif pk["dd"] <= -10:
        tag = "跌幅超過 10%，屬於「修正」"
    elif pk["dd"] < -3:
        tag = "小幅回落"
    else:
        return f"加權指數 {pk['now']:,.0f} 點，在近 3 年高點附近（高點 {pk['high']:,.0f}，{pk['date']}）。"
    return f"加權指數從 {pk['date']} 的近 3 年高點 {pk['high']:,.0f} 點，回落到 {pk['now']:,.0f} 點（{pk['dd']:.1f}%，{pk['days']} 天），{tag}。"


def lead(v: Dict) -> str:
    n = v.get("scored") or 0
    if not n:
        return "一句話看懂：台股熱度指標的歷史還在累積，暫時不亮燈。"
    hot, red = v.get("hot") or [], v.get("red") or []
    if red:
        tail = f"其中 {'、'.join(red)} 已經比自己的歷史平均高出 2 個標準差以上，是歷史上少見的熱度。"
    elif hot:
        tail = f"偏熱的是 {'、'.join(hot)}，還沒有一項到「少見」的程度。"
    else:
        tail = "目前沒有一項明顯偏熱。"
    return f"一句話看懂：{fall_text(v.get('peak') or {})}{n} 項熱度指標裡，{len(hot)} 項偏熱（🟡 或 🔴）。{tail}"


def _row(x: Dict) -> str:
    z = "—" if x["z"] is None else f'{x["z"]:+.1f}'
    pct = "歷史不足" if x["pct"] is None else f'第 {x["pct"]} 百分位'
    return (f'<tr><td>{x["light"]} <b>{esc(x["name"])}</b><div class="small muted">{esc(x["why"])}</div></td>'
            f'<td class="r"><b>{esc(_fmt(x))}</b><div class="small muted">{esc(x["date"])}</div></td>'
            f'<td class="r">{z}</td><td class="r">{pct}<div class="small muted">{esc(x["since"][:7])} 起 {x["n"]} 筆</div></td>'
            f'<td class="r">{x["max"]:,.{x["dg"]}f}<div class="small muted">{esc(x["max_date"])}</div></td>'
            f'<td><a href="{esc(x["src"])}" target="_blank" rel="noopener">證交所</a></td></tr>')


def _score_rows(score: Dict) -> List[str]:
    return [f'<tr><td>{esc(m)}</td><td class="r">{s.get("hot", 0)} / {s.get("of", 0)}</td><td class="r">{s.get("red", 0)}</td>'
            f'<td class="small muted">{esc(s.get("date", ""))}</td></tr>' for m, s in sorted(score.items(), reverse=True)]


def hypothesis(v: Dict) -> str:
    n, hot, red = v.get("scored") or 0, v.get("hot_n") or 0, v.get("red_n") or 0
    now = (f"現在 {n} 項裡 {hot} 項偏熱、{red} 項到 🔴。" if n else "指標歷史還在累積。") + fall_text(v.get("peak") or {})
    pk = v.get("peak") or {}
    early = ""
    if pk.get("dd") is not None and pk["dd"] <= -20:
        early = ('<p class="small"><b>要先面對的事實</b>：指數已經從高點跌了 20% 以上。'
                 '「2027 下半年破裂」和「破裂其實已經開始」是兩個不同的假設；後者的判準是：'
                 '反彈站不回 200 日均線、融資餘額持續下降、外資持續賣超。如果這三樣接下來幾個月都成立，'
                 '比較像泡沫已經在消風，而不是還在等明年。</p>')
    return (
        '<h3>檢驗一個假設：「台股 2027 年下半年泡沫破裂」</h3>'
        '<p class="small"><b>這是假設，不是本站的預測。</b>歷史上泡沫破裂的時間幾乎沒有人能事先定到半年內；'
        '比較可靠的做法是列出「如果這個假設是對的，之前應該會先看到什麼」，每個月對一次。</p>'
        f'<p class="small"><b>事實（本卡數據）</b>：{now}</p>{early}'
        '<p class="small"><b>如果假設越來越像真的，通常會依序看到</b>：'
        '①熱度指標（當沖、成交熱度、離均線距離、估值）多數 🟡→🔴，而且連續好幾個月不退；'
        '②融資餘額創新高後開始快速下降（借錢的人被迫賣）；③外資連續賣超、新台幣急升或急貶；'
        '④央行升息或加強選擇性信用管制、金管會出手限制放空或調整信用交易；⑤台積電與 AI 供應鏈的月營收年增率開始放慢，股價卻還在漲（基本面和價格分岔）。</p>'
        '<p class="small"><b>反過來，下面這些會讓假設變弱</b>：熱度指標回到 🟢 而指數沒有大跌（慢慢消化）；'
        'AI 供應鏈營收持續高成長、估值靠獲利追上；融資餘額隨成交量正常增減，沒有暴衝。</p>'
        '<p class="small"><b>更早破裂的可能</b>也要一起看：信用或流動性的裂縫常常先出現（例如外資單日大賣、融資追繳、限空措施），'
        '觸發點不一定等到 2027 年下半年。本卡每月記錄亮燈數，2027-06 起回頭檢查這條假設。</p>')


def sec_tw_bubble(eng) -> str:
    from wsb.data import tw_bubble as B
    v = _v(eng) or {}
    inds = v.get("inds") or []
    if not inds:
        return ""
    body = f'<p class="rimp big2"><b>{T(lead(v), "")}</b></p>'
    body += ('<p>台股這幾年漲很多，大家擔心是不是泡沫。這張卡不猜時間，只把常見的泡沫徵兆一項一項量出來：'
             '每項都拿來和<b>自己過去幾年</b>比，高出平均 1 個標準差亮 🟡、2 個標準差亮 🔴。</p>')
    kv = "".join(f'<div><span class="muted">{x["light"]} {esc(x["name"])}</span><b>{esc(_fmt(x))}</b>'
                 f'<span class="small muted">{"z " + format(x["z"], "+.1f") if x["z"] is not None else "歷史累積中"}・{esc(x["date"])}</span></div>'
                 for x in inds)
    body += f'<div class="kv">{kv}</div>'
    head = ('<tr><th>指標</th><th class="r">現在</th><th class="r">z（離平均幾個標準差）</th><th class="r">在自己歷史的位置</th>'
            '<th class="r">期間最高</th><th>來源</th></tr>')
    det = fold_rows([_row(x) for x in inds], 10, head, "項")
    vn = v.get("val_now") or {}
    if vn.get("pe30") is not None:
        det += (f'<p class="small">本益比超過 30 倍的上市股票占 {vn["pe30"]:.1f}%（有本益比的 {vn.get("n", 0)} 檔裡）；'
                f'殖利率中位數 {num(vn.get("dy_med"), 2)}%、台積電淨值比 {num(vn.get("tsmc_pb"), 2)} 倍。</p>')
    sp = "".join(f'<div><div class="small muted">{esc(x["name"])}（{esc(x["unit"])}）</div>{spark(_ser(x["hist"]), 160, 36)}</div>'
                 for x in inds if len(x.get("hist") or []) > 5)
    if sp:
        det += f'<div class="g3">{sp}</div>'
    det += hypothesis(v)
    sc = _score_rows(v.get("score") or {})
    if sc:
        det += ('<h4>每月亮燈紀錄</h4>' + fold_rows(sc, 12, '<tr><th>月份</th><th class="r">偏熱 / 有燈號</th><th class="r">🔴</th><th>記錄日</th></tr>', "個月"))
    if v.get("pending"):
        det += f'<p class="small muted">歷史還在補的指標（先顯示數字、不亮燈）：{esc("、".join(v["pending"]))}。每次更新最多向證交所補抓 {B.BUDGET} 筆，避免連太快被擋。</p>'
    body += f'<details class="sgx"><summary>{T("看全部指標、走勢與假設檢驗", "Details")}</summary>{det}</details>'
    body += ('<p class="note">燈號規則：和自己過去的平均差幾個標準差（z），z ≥ 2 → 🔴、z ≥ 1 → 🟡，歷史少於 24 筆不亮燈。'
             '指數與成交看近 3 年每日；當沖與融資每週一筆、近 3 年；估值每月一筆、近 5 年。'
             '本益比與淨值比用全體上市普通股的中位數，不受台積電權重影響；融資與成交金額會隨市場長大，要一起看。'
             '還沒納入：台積電占大盤權重、外資持股比長期走勢、新開戶數（證交所沒有免費的每日資料，待補）。'
             '資料：臺灣證券交易所（每日成交、當日沖銷、信用交易、本益比殖利率淨值比）。描述現況，不是預測，也不是投資建議。</p>')
    h = card(f"{'🔴' if v.get('red_n') else '🟡' if v.get('hot_n') else '🟢'} 台股泡沫觀察：熱度、槓桿、估值和自己的歷史比",
             "Taiwan bubble watch", body, "wide", sub="當沖比重、融資餘額、成交熱度、離均線距離、本益比與淨值比")
    return h.replace('<section class="card', '<section id="twbubble" class="card', 1)
