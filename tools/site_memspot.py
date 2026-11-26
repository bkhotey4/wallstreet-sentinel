"""記憶體現貨價卡（產業體檢）：DRAMeXchange 公開現貨報價 + 本站自己累積的歷史（2026-11-26，wsb/data/mem_spot）。

一句話先講對讀者的意思：現貨通常比合約價早反應，現貨連續走跌 → 合約價跟著鬆動 → 記憶體廠明年毛利預期下修。
每列標自己那張表的更新日（DRAM 現貨每天、模組與晶圓約一週一次），歷史天數不夠就直說，不硬算 30 天變化。"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from tools.sitekit import card, esc, fold_rows

KEY = (("DRAM 現貨", "DDR5 16Gb (2Gx8) 4800/5600", "DDR5 顆粒"), ("DRAM 現貨", "DDR4 16Gb (2Gx8) 3200", "DDR4 顆粒"),
       ("NAND 晶圓", "512Gb TLC", "NAND 512Gb 晶圓"), ("記憶體模組", "DDR5 RDIMM 32GB 4800/5600", "伺服器 DDR5 模組"))


def change(h: List, days: int) -> Optional[float]:
    """Pure: % change from the last point at least `days` calendar days before the newest one; None if history is shorter."""
    if not h or len(h) < 2:
        return None
    end = date.fromisoformat(h[-1][0])
    old = [x for x in h if (end - date.fromisoformat(x[0])).days >= days]
    if not old or not old[-1][1]:
        return None
    return (h[-1][1] / old[-1][1] - 1) * 100


def _lead(snap: Dict, hist: Dict) -> str:
    bits = []
    for tz, item, zh in KEY:
        v = ((snap.get(tz) or {}).get("items") or {}).get(item)
        if not v:
            continue
        c30 = change(hist.get(f"{tz}|{item}") or [], 30)
        upd = ((snap.get(tz) or {}).get("upd") or "")[5:10]
        bits.append(f"{zh} {v['avg']:,.2f} 美元（{upd} 那次 {v['chg']:+.2f}%" + (f"，30 天 {c30:+.1f}%" if c30 is not None else "") + "）")
    if not bits:
        return ""
    # a move under 0.5% is noise in a thin spot market, not "falling" (11-26: −0.2% read as 多數在跌)
    down = [tz for tz, item, _ in KEY if (((snap.get(tz) or {}).get("items") or {}).get(item) or {}).get("chg", 0) <= -0.5]
    s = "一句話看懂：" + "；".join(bits) + "。"
    s += ("多數報價在跌：現貨通常比合約價早 1～2 季反應，現貨持續走跌時，記憶體廠（美光、Sandisk、南亞科、華邦電、旺宏）明年的報價與毛利預期常跟著下修。"
          if len(down) >= max(2, len(bits) // 2 + 1) else
          "報價沒有一致往下：現貨是合約價的前哨，現在還看不出全面轉弱；要看接下來幾週是不是連續下跌。")
    return s


def sec_mem_spot(eng) -> str:
    from wsb.data import mem_spot as MS
    d = MS.load()
    snap, hist = d.get("snap") or {}, d.get("hist") or {}
    if not snap:
        return ""
    trs = []
    for tz, t in snap.items():
        for item, v in (t.get("items") or {}).items():
            h = hist.get(f"{tz}|{item}") or []
            c30 = change(h, 30)
            trs.append(f'<tr><td class="small">{esc(tz)}</td><td>{esc(item)}</td><td class="num"><b>{v["avg"]:,.3f}</b></td>'
                       f'<td class="num">{v["chg"]:+.2f}%</td><td class="num">{"—" if c30 is None else f"{c30:+.1f}%"}</td>'
                       f'<td class="small muted">{esc((t.get("upd") or "")[:16])}</td></tr>')
    days = max((len(h) for h in hist.values()), default=0)
    head = '<tr><th>類別</th><th>品項</th><th>均價（美元）</th><th>最近一次變化</th><th>30 天</th><th>這張表的更新時間</th></tr>'
    note = ("來源：DRAMeXchange（TrendForce 旗下）首頁公開的現貨報價，每 3 小時讀一次；DRAM 現貨每天更新，模組、Flash、晶圓約一週一次，"
            "每列標自己的更新時間。現貨是貿易商之間的即時成交價，量小、波動大，但通常比廠商與大客戶簽的合約價早反應。"
            f"本站從 2026-11-26 開始存歷史，目前最多 {days} 筆，30 天變化要等累積夠才會出現。")
    return card("記憶體現貨價（DRAMeXchange）", "Memory spot prices",
                f'<p class="rimp big2"><b>{esc(_lead(snap, hist))}</b></p>' + fold_rows(trs, 10, head, "項") + f'<p class="note">{note}</p>', "wide")
