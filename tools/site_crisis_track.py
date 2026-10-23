"""危機預警成績單 card (歷史危機 page): did the SSI warn before past crises, how early, false alarms, and today's odds."""
from __future__ import annotations

from tools.sitekit import T, card, esc, num


def sec_crisis_track(eng) -> str:
    from wsb.analytics import crisis_track as CT
    try:
        r = CT.build(eng)
    except Exception:  # noqa: BLE001
        return ""
    if not r.get("available"):
        return ""
    lo, hi = r["levels"][0], r["levels"][-1]
    s, s2 = r["summary"][lo], r["summary"][hi]
    head = (f"{r['since'][:4]} 年以來 {s['n']} 次標普從高點跌 {r['cfg']['min_dd']:.0f}% 以上的危機，壓力指數 SSI 在「跌滿 10% 之前」進入升溫（≥ {lo}）的有 "
            f"{s['hit']} 次，其中 {s['early']} 次提前 1 週以上（中位數提前 {s['lead_med'] or 0} 個交易日）。")
    fa = (f"但 SSI 升溫也常是虛驚：同期間 SSI 升上 {lo} 共 {s['ups']} 次，其中 {s['false']} 次之後 6 個月標普沒有跌超過 10%。"
          f"門檻提高到 {hi}（高壓）時假警報少很多（{s2['ups']} 次中 {s2['false']} 次），但 {s2['n']} 次危機只先抓到 {s2['hit']} 次。")
    rows = ""
    for x in r["rows"]:
        if not x["scored"]:
            why = T("壓力指數資料從 " + r["since"] + " 開始，無法評估", "before the SSI history") if not x["ongoing"] else T("進行中", "ongoing")
            rows += (f'<tr class="muted"><td>{esc(x["name"])}</td><td class="small nw">{esc(x["peak"])} → {esc(x["trough"])}</td>'
                     f'<td class="r">{num(x["dd"], 0, pct=True)}</td><td colspan="4" class="small">{why}</td></tr>')
            continue
        cells = ""
        for lv in r["levels"]:
            ld = x["lead"][lv]
            cells += (f'<td class="r">' + (f'<span class="muted">⚠ {T("跌滿 10% 當天才亮", "same day")}</span>' if ld == 0 else
                                           f'<b class="{"up" if ld >= r["cfg"]["early_days"] else "muted"}">✅ {ld} {T("天前", "d")}</b>' if ld is not None
                                           else f'<span class="dn">✗ {T("沒先亮", "missed")}</span>') + "</td>")
        rows += (f'<tr><td>{esc(x["name"])}</td><td class="small nw">{esc(x["peak"])} → {esc(x["trough"])}</td><td class="r">{num(x["dd"], 0, pct=True)}</td>'
                 f'<td class="small nw">{esc(x["t10"])}</td><td class="r">{num(x["max_ssi"], 0)}</td>{cells}</tr>')
    od = r["odds"]
    band_txt = f"SSI ≥ {r['band']:.0f} 時"
    orows = "".join(f'<tr><td>{T(f"6 個月內跌 ≥ {th}%", f"Fall ≥ {th}% within 6 months")}</td><td class="r"><b>{num(od[th]["cond"], 0)}%</b></td>'
                    f'<td class="r">{num(od[th]["base"], 0)}%</td><td class="r">{num(od[th]["cond"] / od[th]["base"] if od[th]["cond"] is not None and od[th]["base"] else None, 1)}×</td></tr>'
                    for th in (10, 15, 20))
    now_txt = (f"目前 SSI {r['now']:.0f}，標普離 52 週高點 {r['dd_now']:+.1f}%。SSI 已經高於 {r['n_scored']} 次危機中 {r['beats']} 次在「跌滿 10% 之前」的最高值。"
               f"歷史上 SSI ≥ {r['band']:.0f} 的 {od[10]['n']:,} 個交易日，之後 6 個月的表現：")
    note = T("危機＝標普從 52 週高點下跌 15% 以上，直到回到高點 5% 以內才算結束。「提前」＝從危機前 3 個月起，到標普第一次跌滿 10% 那天為止，SSI 第一次到達門檻比那天早幾個交易日。"
             "假警報＝SSI 由下往上穿越門檻（之前至少 20 天在門檻下）後 6 個月內，標普沒有從當天再跌 10%。"
             "條件機率用的是每一天（相鄰日子會重疊），所以是歷史頻率，不是獨立的勝率。SSI 的指標是事後挑選的，這是回測，不是即時紀錄，也不是預測。",
             "Back-test with stated rules; not an out-of-sample record or a forecast.")
    body = (f'<p class="lead"><b>{T(head, head)}</b></p><p>{T(fa, fa)}</p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("危機", "Crisis")}</th><th>{T("高點 → 低點", "Peak → trough")}</th>'
            f'<th class="r">{T("最大跌幅", "Max fall")}</th><th>{T("跌滿 10% 那天", "Day it hit -10%")}</th><th class="r">{T("之前最高 SSI", "Max SSI before")}</th>'
            + "".join(f'<th class="r">{T(f"SSI ≥ {lv} 提前", f"SSI ≥ {lv} lead")}</th>' for lv in r["levels"]) + f'</tr></thead><tbody>{rows}</tbody></table></div>'
            f'<h3>{T("現在離危機多近", "How close are we now")}</h3><p>{T(now_txt, now_txt)}</p>'
            f'<table class="mini"><thead><tr><th>{T("之後 6 個月", "Next 6 months")}</th><th class="r">{T(band_txt, "When SSI is this high")}</th>'
            f'<th class="r">{T("任何一天", "Any day")}</th><th class="r">{T("倍數", "Ratio")}</th></tr></thead><tbody>{orows}</tbody></table>'
            f'<p class="note">{note}</p>')
    return card("危機預警成績單：壓力指數過去有沒有先示警", "Early-warning record: did the stress index warn before past crises", body, "wide")
