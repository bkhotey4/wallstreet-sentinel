"""情緒與警報頁：崩盤還是錯殺？大跌時用資料逐項檢查四個面向（需求、跌價主因、利潤、市場結構），並公開過去 5 年
這個分類之後的股價表現。只描述，不是買賣建議。"""
from __future__ import annotations

from tools.sitekit import T, card, esc, num


def _rng(x: dict) -> str:
    return f"{x['ex']:+.1f}%（90% 區間 {x['lo']:+.1f}～{x['hi']:+.1f}%）"


def _hist(h: dict) -> str:
    ok, wk = ((h.get(c) or {}).get(26) for c in ("ok", "weak"))
    if not ok or not wk:
        return ""
    sig = lambda x: x["lo"] > 0 or x["hi"] < 0  # noqa: E731
    s = f"過去 {h.get('from', '')[:4]}～{h.get('to', '')[:4]} 年跌深的時候："
    s += (f"「本業也在轉弱」的，之後 26 週平均比同市場名單 {_rng(wk)}" + ("，明顯落後；" if sig(wk) and wk["ex"] < 0 else "；"))
    s += f"「本業沒變差」的 {_rng(ok)}"
    if sig(ok) and ok["ex"] > 0:
        s += "，之後平均比較會漲回來。"
    else:
        s += "，並沒有比較會漲回來。"
    s += "所以「本業沒變差」只代表這次下跌不是財報造成的，不代表會反彈；它比較有用的是幫你排除本業真的轉壞的公司。"
    return s


def _rows(rs: list, daily: bool) -> str:
    from wsb.analytics import drop_check as D
    from wsb.analytics import fund_trend as F
    trs = ""
    for r in rs[:15]:
        c = {"ok": "up", "weak": "dn"}.get(r["cls"], "")
        cash = r["fcf_lv"] if r.get("fcf_lv") is not None else r.get("nm_lv")
        cash_l = "自由現金流率" if r.get("fcf_lv") is not None else "淨利率"
        acc = {-1: "放慢", 1: "加速", 0: "持平"}.get(r.get("s_accel"), "")
        own = (f'<div class="small dn">{T("比同產業多跌很多：可能有公司自己的消息，先找時間對得上的新聞", "")}</div>' if r.get("own") else "")
        trs += (f'<tr><td class="nw"><b>{esc(str(r["name"])[:22])}</b> <span class="tk">{esc(r["sym"].split(".")[0])}</span>'
                f'<div class="small muted">{esc(r["ind"])}</div></td>'
                f'<td class="r dn">{num(r["r"], 0, sign=True)}%<div class="small muted">平常 ±{num(r["sd"], 0)}%</div></td>'
                f'<td class="r">{num(r.get("ind_r"), 0, sign=True) + "%" if r.get("ind_r") is not None else "—"}{own}</td>'
                f'<td class="r">{num(r.get("g"), 0, sign=True) + "%" if r.get("g") is not None else "—"}<div class="small muted">{acc}</div></td>'
                f'<td class="r">{num(cash, 1) + "%" if cash is not None else "—"}<div class="small muted">{cash_l}</div></td>'
                f'<td>{T(F.LABEL.get(r.get("label"), ("—", "—"))[0], "")}</td><td><b class="{c}">{T(*D.CLS[r["cls"]])}</b></td></tr>')
    win = "20 個交易日" if daily else "4 週"
    head = (f'<tr><th>{T("公司", "Company")}</th><th class="r">{T("近" + win + "跌幅", "Drop")}</th><th class="r">{T("同產業中位數", "Industry median")}</th>'
            f'<th class="r">{T("① 營收年增", "① Revenue")}</th><th class="r">{T("③ 現金流／淨利", "③ Cash")}</th>'
            f'<th>{T("財報走向", "Trend")}</th><th>{T("分類", "Class")}</th></tr>')
    return f'<div class="scroll"><table class="mini"><thead>{head}</thead><tbody>{trs}</tbody></table></div>'


def sec_drop_check(eng) -> str:
    from wsb.analytics import drop_check as D
    from wsb.analytics import fund_trend as F
    try:
        b = D.build(eng)
    except Exception:  # noqa: BLE001
        b = None
    if not b:
        return ""
    rt = b.get("rates")
    if rt and rt.get("z") is not None:
        if rt["z"] >= 1.5:
            rate = f"10 年債 20 天升 {rt['chg']:.0f}bp（平常 ±{rt['sd']:.0f}bp），利率急升，估值普遍被壓"
        elif rt["z"] <= -1.5:
            rate = f"10 年債 20 天降 {abs(rt['chg']):.0f}bp（平常 ±{rt['sd']:.0f}bp），下跌不是利率造成的"
        else:
            rate = f"10 年債 20 天 {rt['chg']:+.0f}bp（平常 ±{rt['sd']:.0f}bp），變化不大，下跌主因不是利率"
    else:
        rate = ""
    parts, secs = [], ""
    for mk, v in b["markets"].items():
        zh = F.MARKETS[mk][0]
        st, rows = v.get("struct") or {}, v["rows"]
        cnt = {c: sum(r["cls"] == c for r in rows) for c in D.CLS}
        if st:
            broad = st["pct"] >= 90
            parts.append(f"{zh}名單 {st['share']:.0f}% 的公司跌得比自己平常多（高於過去 {st['pct']:.0f}% 的週），"
                         + ("接近全面下跌" if broad else "屬於分化，不是全面下跌"))
        summ = (f"{zh}：跌深 {len(rows)} 家——本業沒變差 {cnt['ok']}、本業也在轉弱 {cnt['weak']}、訊號不一 {cnt['check']}")
        body = (f'<p>{T(_hist(v.get("hist") or {}), "")}</p>' if _hist(v.get("hist") or {}) else "")
        body += (_rows(rows, v.get("daily")) if rows else f'<p class="small muted">{T("目前沒有跌得比自己平常多的公司。", "")}</p>')
        body += f'<p class="small muted">{T("價格到 " + v["asof"] + ("（每日收盤）" if v.get("daily") else "（每週收盤）"), "")}</p>'
        secs += f'<details class="sgx"{" open" if mk == "us" else ""}><summary><b>{T(summ, "")}</b></summary>{body}</details>'
    lead = "一句話看懂：" + "；".join(parts + ([rate] if rate else [])) + "。"
    how = ("「跌深」＝近 4 週（每日資料用 20 個交易日）報酬低於自己過去 2 年同長度報酬標準差的 −1.5 倍，每家公司自己的門檻。"
           "四個面向：① 終端需求＝營收年增與成長加速（需求轉弱時營收成長會先放慢）；② 跌價主因＝同期間 10 年債殖利率變化（和自己平常 20 天變動比），"
           "以及比同產業多跌多少；③ 企業利潤＝近 12 個月自由現金流率（金融業用淨利率）是正還是負；④ 市場結構＝名單裡跌深公司的比例，和過去 5 年每一週比。"
           "分類：財報走向不是轉弱、營收沒放慢、現金流為正＝本業沒變差；財報走向轉弱，或營收放慢且現金流或淨利為負＝本業也在轉弱；其他＝訊號不一。"
           "歷史成績用當時已公布的財報分類（季末後 45 天，第 4 季美股 60 天、台股 90 天），同一段下跌只算第一週，以週為單位重抽 1 萬次算區間。"
           "名單和財報走向判斷相同（美股市值 200 億美元以上、台股市值前 150 大）；港股只有年報，不列。"
           "限制：名單是現在的大型股（倖存者偏差）、財報是修正後的數字。這是逐項檢查與歷史統計，不是買賣建議。")
    body = (f'<p class="rimp big2"><b>{esc(lead)}</b></p>' + secs
            + f'<details class="small"><summary>{T("怎麼判斷、歷史成績、限制", "Method and limits")}</summary><p class="note">{esc(how)}</p></details>')
    return card("崩盤還是錯殺？大跌時逐項檢查本業", "Crash or oversold? Checking the business behind a drop", body, "wide")
