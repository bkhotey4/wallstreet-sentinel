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
    rows_inst = "".join(f'<tr><td>{esc(k)}</td><td class="r"><b>{(v.get("net_oi") or 0):+,.0f}</b></td><td class="r">{(v.get("net_trade") or 0):+,.0f}</td></tr>'
                        for k, v in inst.items())
    rows_large = "".join(f'<tr><td>{"全部交易人" if k == "all" else "特定法人"}</td><td class="r">{v["top5_net"]:+,.0f}</td><td class="r">{v["top10_net"]:+,.0f}</td>'
                         f'<td class="r">{v["oi"]:,.0f}</td></tr>' for k, v in large.items())
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
            + (f'<h3>借券放空：台灣 50＋中型 100 一天變化最大的</h3>' + fold_rows(s_rows, 10, th_s, "家") if s_rows else "")
            + (f'<h3>外資持股比率（上市，依產業）</h3>' + fold_rows(q_rows, 12, '<tr><th>產業</th><th class="r">家數</th><th class="r">外資持股</th><th class="r">一天變化（百分點）</th></tr>', "類") if q_rows else "")
            + f'<p class="note">期交所 OpenAPI（三大法人、大額交易人）、證交所信用額度總量管制餘額表（借券放空，僅上市）、證交所外資持股比率表；抓取 {esc(d.get("fetched") or "—")}，'
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
