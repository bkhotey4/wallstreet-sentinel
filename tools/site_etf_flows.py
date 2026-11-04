"""ETF 資金流向 card: estimated net flow per fund with each number judged in its own σ.  Issuer data only."""
from __future__ import annotations

from typing import Dict, Optional

from tools.sitekit import T, card, esc
from wsb.analytics import etf_flows as EF

Z_NOTE = ("σ（標準差）＝這個數字離這檔基金自己平常的水準有多遠。±1σ 以內算平常，超過 ±2σ 才算特別大。"
          "比較時用「流量占基金規模的百分比」，以近 3 年為底，所以基金變大不會讓每個數字都看起來破紀錄。")
HOW = ("估算方式：今天流通份額減上一個資料日的流通份額，再乘以今天的每單位淨值（NAV）。份額增加＝有人申購（錢流入），份額減少＝有人贖回（錢流出）。"
       "這是估算值，不是發行商公布的流量。份額通常要隔一天才反映當天的申購贖回，所以資料日可能比實際成交晚一天。"
       "申購贖回多半由造市商執行，部分只是對沖或調度，不一定代表一般投資人的看法。ETF 也只占債市、股市的一小部分，要和利差、殖利率一起看。")


def _cell(c: Dict) -> str:
    if c["amt"] is None:
        need = c["need"]
        return (f'<td class="r muted small">{T("資料累積中", "Building history")}'
                f'<div>{T(f"還差 {need} 天以上", f"at least {need} more days")}</div></td>')
    need = c["need_z"]
    sub = T(f"σ 資料累積中（還差 {need} 天）", f"σ pending ({need} days)") if c["z"] is None else esc(f'{c["z"]:+.1f}σ')
    big = c["z"] is not None and abs(c["z"]) >= EF.BIG_Z
    color = "up" if c["amt"] > 0 else "dn" if c["amt"] < 0 else ""
    sub = f'<div class="small"><b>{sub}</b></div>' if big else f'<div class="small muted">{sub}</div>'
    return f'<td class="r"><b class="{color}">{c["amt"] / 1e8:+,.1f}</b>{sub}</td>'


def _state(v: Dict) -> str:
    if v["stale"]:
        return T("官方資料已過期，未列入上方判讀", "Source data is out of date")
    if v["failed"]:
        return T("最近一次抓取失敗，顯示上次成功的資料", "Latest fetch failed; last good data shown")
    return ""


def _row(v: Dict) -> str:
    st = _state(v)
    st = f'<div class="dn">{st}</div>' if st else ""
    return (f'<tr><td class="nw"><b>{esc(v["sym"])}</b><div class="small muted">{T(v["zh"], v["en"])}</div></td>'
            f'<td class="small nw">{esc(v["asof"])}{st}</td>' + _cell(v["d1"]) + _cell(v["d5"]) + _cell(v["d20"])
            + f'<td class="r small muted">{v["aum"] / 1e8:,.0f}</td></tr>')


def sec_etf_flows(eng, r: Optional[Dict] = None) -> str:
    r = EF.build() if r is None else r
    drop = ""
    if r["missing"]:
        names = "、".join(f["sym"] for f in r["missing"])
        drop = (f'<p class="small dn">{T(f"{names} 目前沒有驗證成功的官方資料，所以不列入，也不用其他來源估算。", f"{names}: no verified issuer data, so left out rather than estimated.")}</p>')
    table = ""
    if r["funds"]:
        rows = "".join(_row(v) for v in r["funds"])
        table = (f'<div class="scroll"><table class="mini"><thead><tr><th>ETF</th><th>{T("資料日", "Date")}</th>'
                 f'<th class="r">{T("最新一日（億美元）", "Latest day ($100m)")}</th><th class="r">{T("近 5 日合計", "5-day sum")}</th>'
                 f'<th class="r">{T("近 20 日合計", "20-day sum")}</th><th class="r">{T("基金規模（億美元）", "Assets ($100m)")}</th>'
                 f'</tr></thead><tbody>{rows}</tbody></table></div>')
    srcs = "、".join(f'<a href="{esc(f["url"])}" target="_blank" rel="noopener noreferrer">{esc(f["sym"])}（{esc(f["issuer"])}）</a>'
                     for f in EF.DF.FUNDS)
    lead = "一句話看懂：" + r["lead"]
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p>{table}{drop}'
            f'<details class="sgx"><summary>{T("這張表怎麼看", "How to read")}</summary><p class="note">{T(HOW, "")}</p>'
            f'<p class="note">{T(Z_NOTE, "")}</p><p class="note">{T("正數＝淨流入，負數＝淨流出。", "Positive = net inflow, negative = net outflow.")}</p>'
            f'<p class="small muted">{T("官方來源：", "Issuer sources: ")}{srcs}</p></details>')
    return card("ETF 資金流向", "ETF fund flows", body, "wide")
