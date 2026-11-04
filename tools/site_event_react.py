"""重大數據公布後的市場反應統計 (財經日曆 tab).  Numbers and rules: wsb/analytics/event_react.py."""
from __future__ import annotations

from typing import Dict, Optional

from tools.sitekit import T, card, cls, esc, num


def _val(x, kind: str, sign: bool = True) -> str:
    return "—" if x is None else f'{num(x, 1 if kind == "bp" else 2, sign=sign)}{"bp" if kind == "bp" else "%"}'


def _v(key: str) -> str:
    from wsb.analytics.event_react import VERDICT
    return T(*VERDICT.get(key, ("—", "—")))


def _blab(key: str, b: str) -> str:
    from wsb.analytics import event_react as ER, macro_events as ME
    if key == "fomc":
        return T(*ER.LABELS[b])
    return T(*ME.dir_label(key, b))


def _main_table(ev: Dict) -> str:
    rows = ""
    for a in ev["assets"]:
        s, k = a["all"], a["kind"]
        rows += (f'<tr><td>{T(a["zh"], a["en"])}</td><td class="r {cls(s["mean"])}">{_val(s["mean"], k)}</td><td class="r">{_val(s["med"], k)}</td>'
                 f'<td class="r">{num(s["up"], 0)}%</td><td class="r">{s["n"]}</td><td class="r muted">{_val(s["base_mean"], k)}／{num(s["base_up"], 0)}%</td>'
                 f'<td class="r">{num(s["ratio"], 1)}×</td><td>{_v(s["dir"])}</td><td>{_v(s["size"])}</td></tr>')
    return (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("市場", "Market")}</th><th class="r">{T("平均", "Mean")}</th><th class="r">{T("中位數", "Median")}</th>'
            f'<th class="r">{T("上漲比例", "Share up")}</th><th class="r">{T("次數", "n")}</th><th class="r">{T("平常一天（平均／上漲比例）", "Ordinary day (mean / up)")}</th>'
            f'<th class="r">{T("波動是平常幾倍", "Size vs usual")}</th><th>{T("方向", "Direction")}</th><th>{T("波動大小", "Size")}</th></tr></thead><tbody>{rows}</tbody></table></div>')


def _split_table(ev: Dict) -> str:
    from wsb.analytics.event_react import BUCKETS
    if not ev.get("n_split"):
        return f'<p class="small muted">{T("還沒有足夠的「公布值對預期」紀錄。", "Not enough actual-vs-consensus records yet.")}</p>'
    head = "".join(f'<th class="r">{T(a["zh"], a["en"])}</th>' for a in ev["assets"])
    rows = ""
    for b in BUCKETS[ev["key"]]:
        spx = next((a["split"].get(b) for a in ev["assets"] if a["split"].get(b)), None)
        if not spx:
            continue
        cells = ""
        for a in ev["assets"]:
            s: Optional[Dict] = a["split"].get(b)
            if not s or s.get("thin"):
                cells += f'<td class="r muted">{T("樣本太少", "too few")}</td>'
            else:
                cells += (f'<td class="r"><b class="{cls(s["mean"])}">{_val(s["mean"], a["kind"])}</b><span class="small muted">'
                          f' {T("中位", "med")} {_val(s["med"], a["kind"])}｜↑{num(s["up"], 0)}%｜{_v(s["dir"])}</span></td>')
        rows += f'<tr><td>{_blab(ev["key"], b)}</td><td class="r">{spx["n"]}</td>{cells}</tr>'
    gaps = []
    for a in ev["assets"]:
        sp = a.get("spread")
        if sp:
            gaps.append(f'{T(a["zh"], a["en"])} {_val(sp["gap"], a["kind"])}（{_v(sp["dir"])}）')
    hi, lo = BUCKETS[ev["key"]][0], BUCKETS[ev["key"]][2]
    gl = (f'<p class="small"><b>{_blab(ev["key"], hi)}</b> {T("減", "minus")} <b>{_blab(ev["key"], lo)}</b>：' + "、".join(gaps) + "</p>" if gaps else "")
    return (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("結果", "Outcome")}</th><th class="r">{T("次數", "n")}</th>{head}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div>{gl}')


def _recent(ev: Dict) -> str:
    rows = ""
    for x in ev.get("recent") or []:
        r = x.get("row") or {}
        out = _blab(ev["key"], x["b"]) if x.get("b") else "—"
        rows += (f'<tr><td>{esc(x["date"])}</td><td class="r">{esc(r.get("a") or "—")}</td><td class="r">{esc(r.get("c") or "—")}</td><td class="r muted">{esc(r.get("p") or "—")}</td><td>{out}</td>'
                 + "".join(f'<td class="r {cls(x.get(a["key"]))}">{_val(x.get(a["key"]), a["kind"])}</td>' for a in ev["assets"]) + "</tr>")
    head = "".join(f'<th class="r">{T(a["zh"], a["en"])}</th>' for a in ev["assets"])
    return (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("日期", "Date")}</th><th class="r">{T("公布", "Actual")}</th><th class="r">{T("預期", "Cons.")}</th>'
            f'<th class="r">{T("前值", "Prev.")}</th><th>{T("結果", "Outcome")}</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>')


def _one(ev: Dict) -> str:
    """The plain sentence of one event: the S&P result against an ordinary day."""
    a = next((x for x in ev["assets"] if x["key"] == "spx"), ev["assets"][0])
    s = a["all"]
    return T(f'過去 {s["n"]} 次公布後第一個收盤，{a["zh"]}平均 {_plain(s["mean"], a["kind"])}、{num(s["up"], 0)}% 的次數收漲（平常一天 {_plain(s["base_mean"], a["kind"])}、{num(s["base_up"], 0)}%）。'
             f'方向：{_vp(s["dir"])}；波動約平常的 {num(s["ratio"], 1)} 倍：{_vp(s["size"])}。',
             f'{s["n"]} past releases: {a["en"]} averaged {_plain(s["mean"], a["kind"])}, up {num(s["up"], 0)}% (ordinary day {_plain(s["base_mean"], a["kind"])}, {num(s["base_up"], 0)}%).')


def _plain(x, kind: str) -> str:
    return _val(x, kind)


def _vp(key: str) -> str:
    from wsb.analytics.event_react import VERDICT
    return VERDICT.get(key, ("—", "—"))[0]


def _upcoming(u: Dict) -> str:
    when = T("今天", "today") if u["days"] == 0 else T(f'{u["days"]} 天後', f'in {u["days"]} days')
    bits = []
    if u.get("actual"):
        bits.append(T(f'已公布 {u["actual"]}', f'out: {u["actual"]}'))
    if u.get("cons"):
        bits.append(T(f'預期 {u["cons"]}', f'consensus {u["cons"]}'))
    if u.get("prev"):
        bits.append(T(f'上次 {u["prev"]}', f'previous {u["prev"]}'))
    extra = f'（{"、".join(bits)}）' if bits else ""
    return (f'<div class="concl"><b>{T("接下來", "Coming up")}：{esc(u["date"][5:])} {T(u["zh"], u["en"])}，{when}{extra}</b>'
            f'<p>{_one(u["ev"])}</p>{_split_table(u["ev"])}'
            f'<p class="small muted">{T("這是過去的平均，不代表這次會怎麼走。", "Past averages, not what this release will do.")}</p></div>')


def sec_event_react(eng) -> str:
    from wsb.analytics import event_react as ER
    try:
        r = ER.build(eng)
    except Exception:  # noqa: BLE001
        return ""
    if not r.get("available"):
        return ""
    up = "".join(_upcoming(u) for u in r["upcoming"])
    near = {u["key"] for u in r["upcoming"]}
    blocks = ""
    for ev in r["events"]:
        split = "" if ev["key"] in near else (f'<details class="sgx"><summary>{T("依公布結果分組（高於／低於預期）" if ev["key"] != "fomc" else "依決議分組（升息／不變／降息）", "By outcome")}</summary>{_split_table(ev)}</details>')
        blocks += (f'<div class="rpt"><h3>{T(ev["zh"], ev["en"])} <span class="muted small">{T(ev["time"], ev["time_en"])}</span></h3><p>{_one(ev)}</p>'
                   f'<details class="sgx"><summary>{T("三個市場對照平常日子", "Three markets vs an ordinary day")}</summary>{_main_table(ev)}</details>{split}'
                   f'<details class="sgx"><summary>{T("最近幾次", "Latest releases")}</summary>{_recent(ev)}</details></div>')
    cf = r.get("cons_first") or {}
    cs = "、".join(f'{zh} {cf[k]} 起' for k, zh, *_ in ER.EVENTS if k in cf) or "尚無"
    how = (f'<details class="sgx"><summary>{T("怎麼算、怎麼看「雜訊」", "How it works")}</summary><ul class="small">'
           f'<li>{T("公布後第一個收盤：標普與 10 年期殖利率看公布當天收盤對前一天收盤；台股當天已收盤，所以看下一個台股交易日。FOMC 下午 2 點才公布，當天收盤只反映最後 2 小時。", "First close after release: same-day close for the S&P and 10y; next Taiwan session for the TAIEX. FOMC lands at 14:00 ET, so that close holds two hours of trading.")}</li>'
           f'<li>{T("平常一天：同一段期間內，沒有這三種公布的交易日。", "Ordinary day: sessions in the same years with none of the three releases.")}</li>'
           f'<li>{T(f"雜訊判斷：|t| ≥ {ER.T_CLEAR:.0f} 才算明顯不同；|t| 在 {ER.T_MAYBE:.0f}–{ER.T_CLEAR:.0f} 之間標示「可能是巧合」，因為這裡同時看幾十組數字，光靠運氣就會有幾組看起來有差。次數少於 {ER.FEW_N} 不下判斷。", f"|t| ≥ {ER.T_CLEAR:.0f} counts as clear; {ER.T_MAYBE:.0f}–{ER.T_CLEAR:.0f} may be chance given dozens of comparisons. Under {ER.FEW_N} events: no verdict.")}</li>'
           f'<li>{T(f"預期值來自 Nasdaq 經濟日曆的歷史紀錄（{cs}），更早的公布只算進總表、不分組。CPI 用核心 CPI 月增對預期；非農用新增就業對預期；FOMC 的決議幾乎都符合預期，所以改分升息／不變／降息（對前一次利率）。降息常發生在危機中，分組差距不等於利率本身的效果。", f"Consensus history is from the Nasdaq calendar ({cs}); earlier releases count only in the totals. CPI uses core m/m; FOMC splits by hike/hold/cut.")}</li>'
           f'<li>{T("CPI 與非農的日期來自 FRED 發布日；FRED 名單裡的修正日（例如每年 2 月的季節因子修正）已排除，分不清的月份不列入。CPI 或非農剛好和 FOMC 同一天時，兩邊都會算到。", "Dates are FRED release days without revision-only days; months that cannot be resolved are left out. Same-day overlaps count for both events.")}</li>'
           f'<li>{T("只用收盤資料，看不到公布當下幾分鐘的反應，當天其他新聞也混在裡面。", "Closes only: minute-by-minute reactions are invisible and other news is mixed in.")}</li></ul></details>')
    body = (f'<p class="rimp big2"><b>{T("一句話看懂：" + r["lead"]["zh"], "In one line: " + r["lead"]["en"])}</b></p>{up}{blocks}{how}'
            f'<p class="note">{T("歷史統計，只描述過去，不是預測，也不是投資建議。", "Historical statistics, not a forecast or advice.")}</p>')
    return card("重大數據公布後的市場反應統計", "Market reaction after major data", body, "wide", sub=T("CPI、非農、FOMC 公布後，跟平常的一天差多少", "CPI, jobs and FOMC against an ordinary day"))
