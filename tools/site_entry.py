"""「AI 視角看進場」page (個股 group): the AI read, the cool-down checklist and its history, the healthy-bull gauges, how
expensive the market is, and lump-sum vs phased investing.  Model data only.  It describes the environment and what history
did next; it never names a price to buy at, a stock to buy, or says "buy now"."""
from __future__ import annotations

from tools.sitekit import T, card, cls, esc, num

DISCLAIMER = "描述環境與歷史統計，不是投資建議，也不會告訴你在哪個價位買；本站作者不是持牌投資顧問。"

NOTE_AI = ("三個 AI 工具都只用市場數據：VIX 水準與變化、標普離 200 日線與 52 週高點多遠、6 個月動能、OFR 金融壓力、本站壓力指數 SSI。"
           "兩個模型是每年只用「當時以前」的資料重新訓練的邏輯迴歸，再拿它沒看過的下一年來打分數（AUC：0.5＝丟銅板、1＝完美）；"
           "「相似日記憶」找歷史上指標最像今天的 30 天，同樣用沒看過的年份檢驗。"
           "採計標準：排序能力 AUC ≥ 0.55，而且給出的機率要比「平常的發生率」更準；兩個都過才採計。不採計的工具照樣顯示讀數，但畫成灰色、不納入判讀。"
           "AUC 明顯低於 0.5 代表模型從過去學到的規律（例如「趨勢好就續漲」）在下一年常常反過來，事後把它倒過來用就是拿答案改考卷，所以一樣不採計。"
           "研究上，短期（一年內）的漲跌本來就很難預測，所以「抓不到時點」是誠實的結果，不是程式壞掉。")


def _ai(eng):
    r = getattr(eng, "_entry_ai", None)
    if r is None:
        from wsb.analytics import entry_ai as EA
        try:
            r = EA.build(eng)
        except Exception:  # noqa: BLE001
            r = {"available": False}
        eng._entry_ai = r
    return r


def _cool(eng):
    r = getattr(eng, "_cooldown", None)
    if r is None:
        from wsb.analytics import cooldown as CD
        try:
            r = CD.build(eng)
        except Exception:  # noqa: BLE001
            r = {"available": False}
        eng._cooldown = r
    return r


def _env(eng):
    r = getattr(eng, "_entry_env", None)
    if r is None:
        from wsb.analytics import entry_env as EE
        r = {}
        for k, f in (("bull", EE.bull_env), ("val", EE.valuation_10y), ("phased", EE.phased)):
            try:
                r[k] = f(eng)
            except Exception:  # noqa: BLE001
                r[k] = None
        eng._entry_env = r
    return r


def _val_line(v) -> str:
    if not v:
        return ""
    top = v["rows"][-1]
    if v["above_max"]:
        return (f"價格：巴菲特指標約 {v['now']:.0f}%，比 {v['since']} 年以來任何時候都高；歷史上最貴的四分之一（≥ {top['lo']:.0f}%）之後 10 年，"
                f"股市年化中位數約 {top['med']:.1f}%（平常較便宜時更高）")
    now = next((x for x in v["rows"] if x["now"]), top)
    return f"價格：巴菲特指標約 {v['now']:.0f}%（第 {v['pct']:.0f} 百分位），歷史上這一組之後 10 年股市年化中位數約 {now['med']:.1f}%"


def headline(ai, cool, env) -> str:
    used = [k for k in ("up12", "dd10") if (ai.get(k) or {}).get("used")] + (["memory"] if (ai.get("memory") or {}).get("used") else [])
    bull = env.get("bull") or []
    n_ok = sum(1 for x in bull if x["ok"])
    parts = []
    if cool.get("available"):
        parts.append(f"環境：退燒檢查 {cool['n_ok']}／{cool['n']} 項回到正常、多頭健康度 {n_ok}／{len(bull)} 項")
    v = env.get("val")
    if v:
        parts.append("價格：" + (f"比 {v['since']} 年以來任何時候都貴" if v["above_max"] else f"在自己歷史的第 {v['pct']:.0f} 百分位"))
    parts.append("AI 時點模型：" + ("目前沒有一個比「平常」更準，不採計" if not used else f"{len(used)} 個通過檢驗"))
    return "一句話看懂：" + "；".join(parts) + "。"


def _tool_row(name, x, now_txt, base_txt) -> str:
    if not x:
        return ""
    used = x.get("used")
    a = x.get("auc")
    st = (f'<b class="up">✅ {T("採計", "used")}</b>' if used else f'<span class="muted">⬜ {T("不採計", "not used")}</span>')
    m = "" if used else ' class="muted"'
    return (f'<tr><td>{T(name, "")}</td><td class="r">{num(a, 2)}</td><td>{st}</td>'
            f'<td{m}>{T(now_txt, "")}</td><td class="small muted">{T(base_txt, "")}</td></tr>')


def sec_ai_entry(eng) -> str:
    ai, cool, env = _ai(eng), _cool(eng), _env(eng)
    if not ai.get("available") and not cool.get("available"):
        return ""
    u, d, mem = ai.get("up12"), ai.get("dd10"), ai.get("memory")
    rows = ""
    if u:
        rows += _tool_row("模型 A：12 個月後標普比今天高的機率", u, f"估計 {u['p']:.0f}%", f"平常 {u['base']:.0f}%")
    if d:
        rows += _tool_row("模型 B：半年內從今天再跌 ≥ 10% 的機率", d, f"估計 {d['p']:.0f}%", f"平常 {d['base']:.0f}%")
    if mem:
        rows += _tool_row("相似日記憶：最像今天的 30 天之後 12 個月", mem,
                          f"中位數 {mem['med12']:+.1f}%、上漲 {mem['up12']:.0f}%、半年內再跌 ≥ 10% 有 {mem['dd10']:.0f}%",
                          "相似日：" + "、".join(mem["dates"][:6]))
    bullets = []
    if cool.get("available"):
        from wsb.analytics import cooldown as CD
        ph = {"stress": "壓力還在", "cooling": "退燒中", "mixed": "部分偏緊", "calm": "平時狀態"}[CD.phase(cool)]
        bullets.append(f"市場狀態：{ph}，退燒檢查 {cool['n_ok']}／{cool['n']} 項回到正常（詳見下方檢查表）")
    g = cool.get("gauge")
    if g and g.get("rows"):
        s, b = g["sum"], g["base"]
        bullets.append(f"歷史：五項指標一起退燒的 {len(g['rows'])} 次，之後 12 個月上漲機率 {s['12m']['up']:.0f}%（平常 {b['12m']['up']:.0f}%）、"
                       f"中位數 {s['12m']['med']:+.1f}%（平常 {b['12m']['med']:+.1f}%）：好處在過程較平順，不在賺得更多")
    bull = env.get("bull") or []
    if bull:
        bad = [x["zh"].split("：")[0].split("（")[0] for x in bull if not x["ok"]]
        bullets.append(f"多頭健康度 {sum(1 for x in bull if x['ok'])}／{len(bull)} 項" + (f"，還沒轉好的：{'、'.join(bad[:4])}" if bad else "，全部健康"))
    vl = _val_line(env.get("val"))
    if vl:
        bullets.append(vl)
    ph_ = env.get("phased")
    if ph_:
        bullets.append(f"分批 vs 一次投入：{ph_['since']} 年以來 {ph_['lump_win']:.0f}% 的時候一次投入比較好，但在 2000、2007 這種高點開始時分批明顯少虧")
    lis = "".join(f"<li>{T(x, '')}</li>" for x in bullets)
    body = (f'<p class="rimp big2"><b>{T(headline(ai, cool, env), "")}</b></p>'
            f'<h3>{T("🤖 AI 綜合判讀（只根據數據）", "AI read")}</h3><ul>{lis}</ul>'
            f'<h3>{T("AI 工具成績單：用沒看過的年份檢驗", "Out-of-sample report")}</h3>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("工具", "Tool")}</th><th class="r">AUC</th><th>{T("狀態", "State")}</th>'
            f'<th>{T("今天的讀數", "Now")}</th><th>{T("對照", "Baseline")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<details class="sgx"><summary>{T("AI 怎麼判斷、為什麼不採計", "Method")}</summary><p class="note">{T(NOTE_AI, "")}</p></details>'
            f'<p class="note">{T(DISCLAIMER, "")}</p>')
    return card("AI 視角看進場：環境、價格、時點", "AI view of entry conditions", body, "wide")


def _ok_li(x) -> str:
    return (f'<li><b class="{"up" if x["ok"] else "dn"}">{"✅" if x["ok"] else "⬜"}</b> {T(x["zh"], "")}'
            f'<span class="small muted">　{T(x["txt"], "")}</span><div class="small muted">{T(x["why"], "")}</div></li>')


def sec_bull_env(eng) -> str:
    bull = _env(eng).get("bull") or []
    if not bull:
        return ""
    k = sum(1 for x in bull if x["ok"])
    lv = "多數健康：漲勢有廣度、資金願意承擔風險" if k * 3 >= len(bull) * 2 else "一半一半：環境還在修復" if k * 3 >= len(bull) else "多數還沒轉好：漲勢窄、資金偏防守"
    body = (f'<div class="bth"><span class="bign {"up" if k * 2 > len(bull) else "warn"}">{k} / {len(bull)}</span>'
            f'<b>{T(f"一句話看懂：華爾街常看的多頭健康度 {len(bull)} 項有 {k} 項健康——{lv}。", "")}</b></div>'
            f'<ul class="dlst">{"".join(_ok_li(x) for x in bull)}</ul>'
            f'<p class="small"><a class="golink" href="#rotation" data-p="rotation">{T("類股寬度細節 →", "Breadth →")}</a>　'
            f'<a class="golink" href="#mood" data-p="mood">{T("情緒與部位 →", "Mood →")}</a></p>'
            f'<p class="note">{T("這些是交易台判斷「多頭健不健康」的常用指標：漲勢是否擴散到多數股票、資金偏好景氣股還是防禦股、獲利預估方向、信用與利率。全部健康不代表不會跌，只代表這波上漲的基礎比較廣。" + DISCLAIMER, "")}</p>')
    return card("多頭健康度：漲勢有沒有廣度", "Is the rally healthy?", body, "wide")


def sec_cheap(eng) -> str:
    v = _env(eng).get("val")
    if not v:
        return ""
    rows = "".join(
        f'<tr{NOWCLS if x["now"] else ""}><td>{x["lo"]:.0f}%–{x["hi"]:.0f}%{" ← " + T("現在在這組以上" if v["above_max"] else "現在", "") if x["now"] else ""}</td>'
        f'<td class="r">{x["n"]}</td><td class="r"><b class="{cls(x["med"])}">{x["med"]:+.1f}%</b></td>'
        f'<td class="r">{x["p10"]:+.1f}% ～ {x["p90"]:+.1f}%</td><td class="r">{x["neg"]:.0f}%</td></tr>' for x in v["rows"])
    lead = ("一句話看懂：" + _val_line(v).replace("價格：", "") + "。估值很少能告訴你明年漲跌，但對之後 10 年的平均報酬有參考價值（相關係數 "
            + f"{v['corr']:.2f}）。")
    note = (f"資料：聯準會 Z.1 美國企業股票總市值 ÷ 名目 GDP（{v['since']} 年起，季資料），最新一季用標普漲跌推到今天。報酬用同一個總市值的 10 年年化成長代替（不含股息，也受新上市與買回影響），"
            f"10 年後才知道答案，所以最後一筆是 {v['last']} 年。季資料互相重疊，實際獨立樣本只有幾段。估值高可以維持很多年，它不是時點訊號。" + DISCLAIMER)
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("巴菲特指標（股市總市值／GDP）", "Buffett indicator")}</th><th class="r">{T("季數", "Quarters")}</th>'
            f'<th class="r">{T("之後 10 年年化（中位數）", "Next 10y p.a. (median)")}</th><th class="r">{T("10%～90% 範圍", "10–90% range")}</th>'
            f'<th class="r">{T("10 年後還虧錢", "Negative")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="small"><a class="golink" href="#valuation" data-p="valuation">{T("全部估值指標 →", "Valuation →")}</a>　'
            f'<a class="golink" href="#growth" data-p="growth">{T("個股估值體檢（本益比在自己歷史的位置）→", "Stock check →")}</a></p>'
            f'<p class="note">{T(note, "")}</p>')
    return card("貴不貴：現在的價格對之後 10 年代表什麼", "How expensive, and what it meant for 10 years", body, "wide")


def sec_phased(eng) -> str:
    p = _env(eng).get("phased")
    if not p:
        return ""
    rows = "".join(f'<tr><td>{T(x["label"], "")}（{x["start"]}）</td><td class="r"><b class="{cls(x["lump"])}">{x["lump"]:+.1f}%</b></td>'
                   f'<td class="r"><b class="{cls(x["dca"])}">{x["dca"]:+.1f}%</b></td></tr>' for x in p["named"])
    lead = (f"一句話看懂：{p['since']} 年以來每個月都試一次，{p['lump_win']:.0f}% 的時候「一次全部投入」3 年後比「分 12 個月投入」好（中位數多 {p['diff_med']:.1f} 個百分點），"
            f"因為股市大多時候在漲；但從 2000、2007 這種高點開始時，分批明顯少虧。分批買的是「不後悔」，不是更高的報酬。")
    edu = ("機構常見的三種做法（教學，不是建議）：①事先寫好規則：例如「股票占比偏離目標 5 個百分點就調回來」，下跌時自動多買、上漲時自動少買，避免臨場情緒；"
           "②分批：把一筆錢分 6–12 個月投入，降低剛好買在高點的遺憾；③保留現金與債券部位：讓下跌時不必被迫賣在低點。"
           "回測只用標普指數價格（不含股息），分批期間的現金假設 0% 利息，不含手續費與稅。")
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("從哪個月開始", "Start")}</th><th class="r">{T("一次投入，3 年後", "Lump sum, 3y")}</th>'
            f'<th class="r">{T("分 12 個月投入，3 年後", "12-month phased, 3y")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="note">{T(edu + DISCLAIMER, "")}</p>')
    return card("一次投入還是分批：歷史怎麼說", "Lump sum or phased?", body, "wide")


def sec_entry_links(eng) -> str:
    links = [("mood", "抄底四訊號：恐慌到極點了嗎（情緒與警報頁）"), ("ai", "熱度計：風險退散後，是健康還是太熱（AI 視角看風險頁）"),
             ("growth", "個股估值體檢：每檔本益比在自己 5 年歷史的位置（成長估值頁）"), ("crisis", "歷史危機：每次大跌跌多深、多久才回來")]
    lis = "".join(f'<li><a class="golink" href="#{k}" data-p="{k}">{T(z, "")} →</a></li>' for k, z in links)
    return card("相關卡片", "Related cards", f'<p>{T("其他頁面裡跟「進場環境」有關的卡片：", "")}</p><ul>{lis}</ul>', "")


NOWCLS = ' class="now"'
CSS = "tr.now td{background:var(--wash);font-weight:600}"
