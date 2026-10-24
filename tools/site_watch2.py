"""三張新卡：台股外資台指期淨未平倉（台股頁）、VIX 期限結構（情緒與警報頁）、52 週新高−新低家數（類股寬度頁）。
每張都先白話解釋「它在量什麼」，再寫數字與回測（回測做不了的照實寫）。"""
from __future__ import annotations

import pandas as pd

from tools.sitekit import T, card, num, spark

TW_NOTE = ("什麼是外資台指期淨未平倉：外資在台指期貨還沒平倉的多單減掉空單。負數越大＝空單越多。但外資常拿期貨避險手上的現貨，"
           "而且指數越高、市場越大，口數自然越大，所以只看「破幾萬口」會失真；燈號改用和自己 2018 年以來的歷史比。"
           "3.5 萬、4 萬口兩條線照樣列出供參考。資料：FinMind（期交所三大法人資料）。不是投資建議。")
VIX_NOTE = ("什麼是 VIX 期限結構：VIX9D、VIX、VIX3M 分別是市場預期未來 9 天、30 天、3 個月的波動。平常越遠越貴（正價差）；"
            "恐慌時大家急著買近期保險，近月會飆過遠月（逆價差、倒掛），這比單看 VIX 點數更能看出「現在」有多慌。資料：Cboe（Yahoo Finance）。不是投資建議。")
NH_NOTE = ("什麼是 52 週新高−新低：每天數一數有幾檔股票收盤創一年新高、幾檔創一年新低。指數創新高、但新低比新高多＝只剩少數大型股在撐（頂背離）；"
           "指數破底、但新低家數快速減少＝賣壓變小（底部訊號）。網站建置時用美股全市場約 2,500 檔（只保留約 330 個交易日，所以只描述現況、不做回測）；"
           "全市場資料不在時改用本站追蹤池。「風險模型」頁金絲雀的「市場分裂」燈號也是用同一份全市場資料。不是投資建議。")


def _ser(rows) -> pd.Series:
    return pd.Series([r[1] for r in rows], index=pd.to_datetime([r[0] for r in rows]))


def _tw(eng):
    try:
        from wsb.data import tw_futures as TF
        return TF.view(eng)
    except Exception:  # noqa: BLE001
        return None


def _vb(eng, fn):
    try:
        from wsb.analytics import vol_breadth as VB
        return getattr(VB, fn)(eng)
    except Exception:  # noqa: BLE001
        return None


def sec_tw_foi(eng) -> str:
    v = _tw(eng)
    if not v:
        return ""
    head = f"{v['emoji']} 外資台指期淨未平倉 {v['net']:,.0f} 口：{v['band']}（{v['since']} 年以來第 {v['pct']:.1f} 百分位）"
    cur = next((r for r in v.get("rows") or [] if r["now"]), None)
    lines = [f"資料日 {v['date']}；一天 {v['chg1']:+,.0f} 口、20 天 {v['chg20']:+,.0f} 口；歷史最低是 {v['min_d']} 的 {v['min']:,.0f} 口。",
             "參考線：" + "、".join(f"{abs(x['v']):,} 口空單（{'已跌破' if x['crossed'] else '未跌破'}）" for x in v["lines"]) + "。"]
    if cur and cur.get("p") is not None:
        lines.append(f"回測（{v['since']} 年起）：落在這一檔時，加權指數之後 21 個交易日內跌 ≥5% 的機率 {cur['p']:.0f}%，同期平常 {v['base']:.0f}%。")
    rows = "".join(f'<tr{" class=hl" if r["now"] else ""}><td>{T(r["band"], "")}{" ◀ 現在" if r["now"] else ""}</td>'
                   f'<td class="r"><b>{num(r["p"], 0)}%</b></td><td class="r small muted">{r["n"]:,}</td></tr>' for r in v.get("rows") or [])
    tbl = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("外資淨未平倉落在", "")}</th><th class="r">{T("之後 21 天跌 ≥5%", "")}</th>'
           f'<th class="r">{T("天數", "")}</th></tr></thead><tbody>{rows}</tbody></table></div>') if rows else ""
    body = (f'<p class="rimp big2"><b>{T(head, "")}</b></p>' + "".join(f'<p class="small">{T(x, "")}</p>' for x in lines)
            + spark(_ser(v["hist"])) + tbl + f'<p class="note">{T(TW_NOTE, "")}</p>')
    return card("外資台指期淨未平倉：歷史走勢與燈號", "Foreign net open interest in TAIEX futures", body, "wide")


def sec_vix_term(eng) -> str:
    v = _vb(eng, "vix_term")
    if not v:
        return ""
    head = f"{v['emoji']} VIX 期限結構：{v['state']}（VIX÷VIX3M＝{v['ratio']:.2f}）"
    lines = [f"VIX9D {num(v['vix9d'], 1)}・VIX {v['vix']:.1f}・VIX3M {v['vix3m']:.1f}（{v['date']}）；比值在 {v['since']} 年以來第 {v['pct']:.0f} 百分位，"
             f"近 20 天有 {v['days_inverted']} 天倒掛。"]
    bt = v.get("bt") or {}
    inv, al = bt.get("inv") or {}, bt.get("all") or {}
    if inv.get("n"):
        lines.append(f"回測：倒掛的 {inv['n']:,} 天，之後 3 個月報酬中位數 {num(inv['r63'], 1, sign=True)}%（平常 {num(al['r63'], 1, sign=True)}%），"
                     f"但 3 個月內跌 ≥10% 的機率 {num(inv['crash'], 0)}%（平常 {num(al['crash'], 0)}%）——倒掛代表接下來兩個方向都晃得比較大，"
                     "常出現在恐慌高點附近，不是單純的「還會再跌」。")
    body = (f'<p class="rimp big2"><b>{T(head, "")}</b></p>' + "".join(f'<p class="small">{T(x, "")}</p>' for x in lines)
            + spark(_ser(v["hist"])) + f'<p class="note">{T(VIX_NOTE, "")}</p>')
    return card("VIX 期限結構：近月恐慌有沒有飆過遠月", "VIX term structure", body, "wide")


def sec_nh_nl(eng) -> str:
    v = _vb(eng, "nh_nl")
    if not v:
        return ""
    head = f"{v['emoji']} 52 週新高 {v['nh']} 檔、新低 {v['nl']} 檔，差 {v['diff']:+d}：{v['signal']}"
    line = (f"資料日 {v['date']}，{v.get('src', '')}有一年歷史可比的 {v['n']:,} 檔；近 10 天平均 {v['avg10']:+.1f}"
            + (f"；標普離一年高點 {v['spx_off']:+.1f}%" if v.get("spx_off") is not None else "") + "。")
    bars = _ser(v["hist"])
    mx = max(1, int(bars.abs().max()))
    svg = "".join(f'<rect x="{i * 4}" y="{40 - max(0, x) / mx * 38:.1f}" width="3" height="{abs(x) / mx * 38:.1f}" class="{"nhp" if x >= 0 else "nhn"}"/>'
                  for i, x in enumerate(bars.values))
    chart = (f'<div class="scroll"><svg class="nhc" viewBox="0 0 {len(bars) * 4} 80" role="img" aria-label="近 120 天新高減新低">'
             f'<line x1="0" x2="{len(bars) * 4}" y1="40" y2="40" class="nh0"/>{svg}</svg></div>'
             f'<p class="small muted">{T("近 120 個交易日：綠色＝新高多於新低，紅色＝新低多於新高", "")}</p>')
    body = f'<p class="rimp big2"><b>{T(head, "")}</b></p><p class="small">{T(line, "")}</p>{chart}<p class="note">{T(NH_NOTE, "")}</p>'
    return card("52 週新高−新低：是不是只剩少數股票在撐", "52-week new highs minus new lows", body, "wide")


CSS = (".nhc{width:100%;min-width:360px;height:90px;display:block}.nhc .nhp{fill:var(--up)}.nhc .nhn{fill:var(--dn)}"
       ".nhc .nh0{stroke:var(--bd);stroke-width:1}")
