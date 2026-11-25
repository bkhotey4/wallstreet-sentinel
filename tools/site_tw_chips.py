"""台股籌碼深度（台股專業判讀頁）與董監質押（台股財報頁）——2026-11-22 台股覆蓋清單補缺。資料與規則見 wsb/data/tw_chips.py。"""
from __future__ import annotations

from typing import Dict, List, Optional

from tools.sitekit import card, esc, fold_rows


def _d() -> Dict:
    from wsb.data import tw_chips as C
    try:
        return C.refresh()
    except Exception:  # noqa: BLE001
        return {}


def _prev(d: Dict, key, sub) -> Optional[float]:
    from wsb.data import tw_chips as C
    s = C.series(d, key, sub)
    return s[-2][1] if len(s) >= 2 else None


def _chg(now: Optional[float], prev: Optional[float], unit: str = "口") -> str:
    if now is None or prev is None:
        return '<span class="muted">（還在累積前一天）</span>'
    c = now - prev
    return f'（比前一次 {c:+,.0f} {unit}）'


def sec_tw_chips(eng=None) -> str:
    d = _d()
    inst, large, sbl, qfii = d.get("inst") or {}, d.get("large") or {}, d.get("sbl") or {}, d.get("qfii") or []
    if not (inst or large or sbl or qfii):
        return ""
    f = (inst.get("外資及陸資") or {}).get("net_oi")
    fp = _prev(d, "inst", ("外資及陸資", "net_oi"))
    li = (large.get("inst") or {}).get("top10_net")
    lead = []
    if f is not None:
        lead.append(f'外資台指期未平倉淨{"空" if f < 0 else "多"}單 {abs(f):,.0f} 口' + (f'，比前一次{"增加" if abs(f) > abs(fp) else "減少"} {abs(abs(f) - abs(fp)):,.0f} 口' if fp is not None else ""))
    if li is not None:
        lead.append(f'前十大特定法人在台指期淨{"多" if li > 0 else "空"} {abs(li):,.0f} 口')
    if sbl.get("total"):
        lead.append(f'上市借券放空餘額 {sbl["total"] / 1e8:,.2f} 億股（比前一天 {(sbl["total"] - sbl.get("prev", 0)) / 1e4:+,.0f} 萬股）')
    so = d.get("sbl_otc") or {}
    if so.get("total"):
        lead.append(f'上櫃 {so["total"] / 1e8:,.2f} 億股（{(so["total"] - so.get("prev", 0)) / 1e4:+,.0f} 萬股）')
    from wsb.data.tw_margin import floor_on
    mr, dt = d.get("mratio") or {}, d.get("daytrade") or {}
    if mr.get("ratio"):
        mp = _prev(d, "mratio", ("ratio",))
        lead.append(f'上市整體融資維持率約 {mr["ratio"]:.0f}%（{str(mr.get("date"))[4:6]}/{str(mr.get("date"))[6:]} 收盤，估算' + (f'，前一次 {mp:.0f}%' if mp else "") + f'；個別帳戶低於 {floor_on()}% 會被追繳）')
    if dt.get("value_pct") is not None:
        lead.append(f'當沖占成交金額 {dt["value_pct"]:.1f}%')
    warn = d.get("warn") or []
    if warn:
        lead.append(f'注意股 {len(warn)} 檔')
    rows_inst = "".join(f'<tr><td>{esc(k)}</td><td class="r"><b>{(v.get("net_oi") or 0):+,.0f}</b></td><td class="r">{(v.get("net_trade") or 0):+,.0f}</td></tr>'
                        for k, v in inst.items())
    rows_large = "".join(f'<tr><td>{"全部交易人" if k == "all" else "特定法人"}</td><td class="r">{v["top5_net"]:+,.0f}</td><td class="r">{v["top10_net"]:+,.0f}</td>'
                         f'<td class="r">{v["oi"]:,.0f}</td></tr>' for k, v in large.items())
    lo = d.get("large_opt") or {}
    rows_opt = "".join(f'<tr><td>{"全部交易人" if k == "all" else "特定法人"}</td><td class="r">{(v.get("call") or {}).get("top10_net", 0):+,.0f}</td>'
                       f'<td class="r">{(v.get("put") or {}).get("top10_net", 0):+,.0f}</td></tr>' for k, v in lo.items() if isinstance(v, dict))
    th_s = "<tr><th>公司</th><th class=\"r\">借券放空餘額（張）</th><th class=\"r\">一天變化（張）</th></tr>"
    s_rows = [f'<tr><td><b>{esc(x["name"])}</b> <span class="tk">{esc(x["code"])}</span></td><td class="r">{x["bal"] / 1000:,.0f}</td>'
              f'<td class="r">{x["chg"] / 1000:+,.0f}</td></tr>' for x in (sbl.get("add") or []) + (sbl.get("cut") or [])]
    q_prev = {}
    days = sorted((d.get("hist") or {}))
    if len(days) >= 2:
        q_prev = {x["cat"]: x["pct"] for x in (d["hist"][days[-2]].get("qfii") or [])}
    q_rows = [f'<tr><td>{esc(x["cat"])}</td><td class="r">{x["n"]}</td><td class="r"><b>{x["pct"]:.2f}%</b></td><td class="r">'
              + (f'{x["pct"] - q_prev[x["cat"]]:+.2f}' if x["cat"] in q_prev else "—") + "</td></tr>"
              for x in sorted(qfii, key=lambda x: -(x["pct"] or 0))]
    body = (f'<p class="rimp"><b>一句話看懂：{esc("；".join(lead))}。</b></p>'
            '<p class="small">這些是被迫或大型的部位：外資用期貨避險或放空、大額交易人集中在誰手上、借股票來放空的量、外資在各產業的持股比重。'
            '金管會 11/21 鼓勵出借人召回借券，借券放空餘額如果大減，代表放空的人被迫買回。</p>'
            + (f'<h3>台指期三大法人（口；未平倉淨額、當天淨買賣）</h3><div class="scroll"><table class="mini"><thead><tr><th>法人</th><th class="r">未平倉淨額</th>'
               f'<th class="r">當天淨買賣</th></tr></thead><tbody>{rows_inst}</tbody></table></div>' if rows_inst else "")
            + (f'<h3>台指期大額交易人（全部月份；買方減賣方，口）</h3><div class="scroll"><table class="mini"><thead><tr><th></th><th class="r">前五大</th>'
               f'<th class="r">前十大</th><th class="r">全市場未平倉</th></tr></thead><tbody>{rows_large}</tbody></table></div>' if rows_large else "")
            + (f'<h3>臺指選擇權大額交易人（前十大，買方減賣方，口）</h3><p class="small muted">買權淨賣出多＝大戶在收權利金、押注不會大漲；賣權淨買進多＝大戶在買跌的保險。</p>'
               f'<div class="scroll"><table class="mini"><thead><tr><th></th><th class="r">買權</th><th class="r">賣權</th></tr></thead><tbody>{rows_opt}</tbody></table></div>' if rows_opt else "")
            + (f'<h3>借券放空：台灣 50＋中型 100 一天變化最大的</h3>' + fold_rows(s_rows, 10, th_s, "家") if s_rows else "")
            + (f'<h3>注意股（{len(warn)} 檔；連續漲跌或成交異常，再犯可能被處置）</h3>'
               + fold_rows([f'<tr><td><b>{esc(x["name"])}</b> <span class="tk">{esc(x["code"])}</span><div class="small muted">{esc(x["board"])}</div></td>'
                            f'<td class="small">{esc(x["why"][:90])}</td></tr>' for x in warn], 10, "<tr><th>股票</th><th>原因</th></tr>", "檔") if warn else "")
            + (f'<h3>外資持股比率（上市，依產業）</h3>' + fold_rows(q_rows, 12, '<tr><th>產業</th><th class="r">家數</th><th class="r">外資持股</th><th class="r">一天變化（百分點）</th></tr>', "類") if q_rows else "")
            + f'<p class="note">期交所 OpenAPI（三大法人、大額交易人）、證交所信用額度總量管制餘額表與櫃買 OpenAPI（借券放空）、證交所與櫃買注意股、證交所外資持股比率表、證交所信用交易統計與收盤價（融資維持率＝融資股票市值÷融資金額，本站估算）、證交所當日沖銷交易統計；抓取 {esc(d.get("fetched") or "—")}，'
              '每天存一份，變化從第二天起顯示。描述資料，不是投資建議。</p>')
    return card("籌碼深度：期貨法人、大額交易人、借券與外資持股", "Positioning depth", body, "wide")


def sec_tw_pledge(eng=None) -> str:
    d = _d()
    p = d.get("pledge") or []
    if not p:
        return ""
    hi = [x for x in p if x["pct"] >= 30]
    lead = (f'台灣 50＋中型 100 裡，董監本人把三成以上持股拿去質押借錢的有 {len(hi)} 家'
            + (f'（最高：{"、".join(x["name"] for x in hi[:4])}）' if hi else "") + "。")
    th = '<tr><th>公司</th><th class="r">董監持股（張）</th><th class="r">質押（張）</th><th class="r">質押比例</th></tr>'
    rows = [f'<tr><td><b>{esc(x["name"])}</b> <span class="tk">{esc(x["code"])}</span></td><td class="r">{x["held"] / 1000:,.0f}</td>'
            f'<td class="r">{x["pledged"] / 1000:,.0f}</td><td class="r"><b>{x["pct"]:.0f}%</b></td></tr>' for x in p if x["pct"] > 0]
    ym = p[0].get("ym") or ""
    body = (f'<p class="rimp"><b>一句話看懂：{esc(lead)}</b></p>'
            '<p class="small">董監把股票質押給銀行借錢，股價大跌時可能被要求補擔保品或被斷頭，等於多一個被迫賣出的來源；質押比例高不一定有問題（有些是集團融資慣例），'
            '但在大跌時要多看一眼。</p>' + fold_rows(rows, 15, th, "家")
            + f'<p class="note">證交所 OpenAPI 董監事持股餘額明細（資料年月 {esc(ym)}，每月更新）；比例＝董監本人持股中的設質股數 ÷ 目前持股。描述資料，不是投資建議。</p>')
    return card("董監質押：大跌時的另一個被迫賣方", "Insider share pledges", body, "wide")


def _f(x, fmt: str) -> str:
    return "—" if x is None else fmt.format(x)


def sec_tw_quarter(eng=None) -> str:
    """單季財報（11-22，台股覆蓋清單補缺）：台灣 50＋中型 100 最新一季的單季營收、毛利率、營益率、EPS，和上一季比。"""
    import json as _json
    from wsb.data import tw_chips as C
    try:
        seed = _json.loads(C.FIN_SEED.read_text(encoding="utf-8")) if C.FIN_SEED.exists() else {}
    except (OSError, ValueError):
        seed = {}
    snaps = seed.get("snaps") or {}
    if not snaps:
        return ""
    try:
        from wsb.data import tw_desk as D
        codes = set(D.universe(D.load()).get("codes") or []) or None
    except Exception:  # noqa: BLE001
        codes = None
    v = C.fin_view(snaps, codes)
    rows = v.get("rows") or []
    if not rows:
        return ""
    y, q = v["q"].split("Q")
    up = [r for r in rows if (r.get("rev_qoq") or 0) > 0]
    gm_up = [r for r in rows if r.get("gm") is not None and r.get("gm_prev") is not None and r["gm"] > r["gm_prev"]]
    lead = (f'台灣 50＋中型 100 的 {y} 年第 {q} 季（單季）：{len(rows)} 家裡營收比上一季成長的有 {len(up)} 家，'
            f'毛利率比上一季提高的有 {len(gm_up)} 家。')
    pts = lambda a, b: "" if a is None or b is None else f'<div class="small muted">{a - b:+.1f}</div>'  # noqa: E731
    th = ('<tr><th>公司</th><th class="r">單季營收（億元）</th><th class="r">比上季</th><th class="r">毛利率</th><th class="r">營益率</th>'
          '<th class="r">單季 EPS（元）</th></tr>')
    body_rows = [f'<tr><td><b>{esc(r["name"])}</b> <span class="tk">{esc(r["code"])}</span></td><td class="r">{r["rev"] / 1e5:,.0f}</td>'
                 f'<td class="r">{_f(r.get("rev_qoq"), "{:+.0f}%")}</td>'
                 f'<td class="r">{_f(r.get("gm"), "{:.1f}%")}{pts(r.get("gm"), r.get("gm_prev"))}</td>'
                 f'<td class="r">{_f(r.get("om"), "{:.1f}%")}</td>'
                 f'<td class="r"><b>{_f(r.get("eps"), "{:.2f}")}</b>{pts(r.get("eps"), r.get("eps_prev"))}</td></tr>'
                 for r in rows]
    body = (f'<p class="rimp"><b>一句話看懂：{esc(lead)}</b></p>'
            '<p class="small">季報公布的是「今年到這季為止的累計數」，這裡用前後兩季的累計相減，算出這一季自己的數字（第 1 季就是本身）。'
            '毛利率、EPS 下面的小字是比上一季多或少幾個百分點／幾元。金融股沒有毛利率。依營收由大到小排列。</p>'
            + fold_rows(body_rows, 20, th, "家")
            + f'<p class="note">公開資訊觀測站綜合損益表彙總表（上市＋上櫃，累計數，千元；電腦端抓取 {esc(seed.get("fetched") or "—")}）。'
              '單季數字由兩季累計相減，公司若重編前期數字可能有小差異。描述資料，不是投資建議。</p>')
    return card(f"台股單季財報：{y} 年第 {q} 季", "Taiwan quarterly results", body, "wide")


WHERE = {"above": "高於財測上緣", "in": "在財測區間內", "below": "低於財測下緣"}


def _yi(x: Optional[float]) -> str:
    return "—" if x is None else f"{x / 1e5:,.1f}"


def _fc(r: Optional[tuple]) -> str:
    if not r:
        return "—"
    return _yi(r[0]) if r[0] == r[1] else f"{_yi(r[0])}～{_yi(r[1])}"


def sec_tw_forecast(eng=None) -> str:
    """財測達成情形（11-22，台股覆蓋清單最後一項部分）：有公開財測的上市公司，實際數和自己的財測比。"""
    import json as _json
    from wsb.data import tw_chips as C
    d = _d()
    try:
        seed = _json.loads(C.FIN_SEED.read_text(encoding="utf-8")) if C.FIN_SEED.exists() else {}
    except (OSError, ValueError):
        seed = {}
    rows = C.forecast_view(d.get("fc15") or [], d.get("fc16") or [], seed.get("snaps") or {})
    rows = [r for r in rows if r.get("q_where") or r.get("ytd_where")]
    if not rows:
        return ""
    n = {k: sum(r.get("q_where") == k and not r.get("q_close") for r in rows) for k in WHERE}
    close = sum(bool(r.get("q_close")) for r in rows)
    q = rows[0]["q"]
    lead = (f'{q[:3]} 年第 {q[-1]} 季有公開財測的 {len(rows)} 家上市公司，單季獲利 {n["above"]} 家高於自己財測的上緣、'
            f'{n["in"]} 家在區間內、{n["below"]} 家低於下緣' + (f'，{close} 家貼著邊界（近似值，分不出來）' if close else ""))
    tr = []
    for r in rows:
        qw, yw = r.get("q_where"), r.get("ytd_where")
        tr.append(f'<tr><td>{esc(r["name"])}（{esc(r["code"])}）</td><td class="small">{esc(str(r.get("cover") or ""))}</td>'
                  f'<td class="r"><b>{_yi(r.get("q_act"))}</b>{"" if r["exact"] else "<sup>≈</sup>"}</td><td class="r">{_fc(r.get("q_fc"))}</td>'
                  f'<td>{esc(WHERE.get(qw, "—"))}{"<div class=small muted>差距在近似誤差內</div>" if r.get("q_close") else ""}</td>'
                  f'<td class="r">{_yi(r.get("ytd_act"))}</td><td class="r">{_fc(r.get("ytd_fc"))}</td><td>{esc(WHERE.get(yw, "—") if yw else "—")}</td></tr>')
    th = ('<tr><th>公司</th><th>財測涵蓋季別</th><th class="r">本季實際</th><th class="r">本季財測</th><th>本季</th>'
          '<th class="r">累計實際</th><th class="r">累計財測</th><th>累計</th></tr>')
    body = (f'<p class="rimp"><b>一句話看懂：{esc(lead)}。</b></p>'
            '<p class="small">財測是公司自己公開說「這段期間大概賺多少」。實際數高於上緣，代表公司自己都低估了；低於下緣，代表事情比公司預期差。'
            '台灣只有少數公司公開財測（多數只在法說會口頭說），所以這張表很短。單位：億元，綜合損益（含匯兌等其他綜合損益）。</p>'
            + fold_rows(tr, 10, th, "家")
            + f'<p class="note">來源：證交所 OpenAPI t187ap16_L（當季與累計並列，口徑一致）、t187ap15_L（只有單季財測）。'
              '標 ≈ 的公司只在 t187ap15_L：本季實際用公開資訊觀測站累計損益表相減得到的「歸屬母公司淨利」近似，'
              '和財測的綜合損益差在匯兌等其他綜合損益；累計實際是證交所檔案的官方數字。'
              f'抓取 {esc(d.get("fetched") or "—")}。描述資料，不是預測，也不是投資建議。</p>')
    return card("財測達成情形：公司自己說的數字做到了沒", "Financial forecast attainment", body, "wide")


def sec_tw_squeeze(eng=None) -> str:
    """借券放空集中度（11-22）：金管會鼓勵出借人召回借券時，哪些股票的「被迫買回」壓力最大。"""
    from wsb.data import tw_chips as C
    try:
        d = C.squeeze()
    except Exception:  # noqa: BLE001
        return ""
    rows = [r for r in d.get("rows") or [] if r.get("dtc") is not None and (r.get("value") or 0) >= 3]
    if not rows:
        return ""
    by_dtc = sorted(rows, key=lambda r: -r["dtc"])
    cap = [r for r in d["rows"] if r["pct"] >= 9.5]
    top = by_dtc[0]
    lead = (f'上市股票裡，借券放空要「好幾天的成交量」才買得回來的有：{top["name"]}（{top["code"]}）約 {top["dtc"]:.0f} 天'
            + "".join(f'、{r["name"]} {r["dtc"]:.0f} 天' for r in by_dtc[1:3])
            + f'；另有 {len(cap)} 檔借券放空停在發行股數 10% 附近，像是碰到額度上限、不能再借券放空')
    th = ('<tr><th>#</th><th>公司</th><th class="r">借券放空餘額（張）</th><th class="r">占發行股數</th><th class="r">回補天數</th>'
          '<th class="r">市值（億元）</th><th class="r">比前一天（張）</th></tr>')
    tr = [f'<tr><td>{i}</td><td>{esc(r["name"])}（{esc(r["code"])}）</td><td class="r">{r["bal"] / 1000:,.0f}</td>'
          f'<td class="r">{r["pct"]:.2f}%{" ⚠️" if r["pct"] >= 9.5 else ""}</td><td class="r"><b>{r["dtc"]:.1f}</b></td>'
          f'<td class="r">{r["value"]:,.1f}</td><td class="r">{r["chg"] / 1000:+,.0f}</td></tr>' for i, r in enumerate(by_dtc, 1)]
    body = (f'<p class="rimp"><b>一句話看懂：{esc(lead)}。</b></p>'
            '<p class="small">借券放空是先借別人的股票來賣、之後買回來還。出借的人（多半是壽險、投信、外資）把股票召回時，放空的人就得在市場上買回——'
            '「回補天數」＝借券放空餘額 ÷ 最近一天的成交量，數字越大，代表要買回時越難不推高價格（軋空）。'
            '這不是說它一定會漲：召回要照契約分批發生，公司本身的消息與大盤還是比較重要。</p>'
            + fold_rows(tr, 15, th, "檔")
            + f'<p class="note">來源：證交所 TWT93U（借券賣出餘額，股）、STOCK_DAY_ALL（成交量與收盤價）、OpenAPI t187ap03_L（已發行普通股數）。'
              f'資料日 {esc(str(d.get("date") or "—"))}，抓取 {esc(d.get("fetched") or "—")}。只列借券放空市值 3 億元以上；回補天數用最近一天的成交量，'
              '大量的日子會讓天數變小。⚠️＝占發行股數 9.5% 以上（資料裡很多檔剛好停在 10.0% 左右，看起來是借券賣出的額度上限；確切規定以證交所為準）。描述資料，不是建議。</p>')
    return card("借券放空集中度：召回時誰的回補壓力最大", "Borrowed-share short concentration", body, "wide")
