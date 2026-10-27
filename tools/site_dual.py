"""總覽頁：風險雙軌——即時壓力溫度計（今天市場有多緊）vs 累積脆弱度燃料箱（底下累積了多少燃料），以及行情列下的外資台指期小標籤。
溫度計是同步指標，只能說「現在正在緊」；燃料箱是慢變數，研究上能領先 1–3 年但抓不準時點（Greenwood 等 2022、Adrian 等 2019）。兩邊分開看，不合成一個分數。"""
from __future__ import annotations

from tools.sitekit import T, card

NOTE = ("溫度計四項：壓力指數 SSI ≥ 55、VIX 期限結構倒掛（VIX ÷ 3 個月 VIX ≥ 1）、OFR 金融壓力指數 > 0（高於長期平均）、標普跌破零 Gamma 翻轉點（造市商追漲殺跌）。"
        "燃料箱是「全方位風險」頁的累積脆弱度燈號：信用／GDP 擴張、資產價格過熱、兩者同時發生的 R-zone、家庭負債、公司債利差過低、超額債券溢酬 EBP 偏低、銀行放寬放款。"
        "最危險的組合通常是「溫度計很冷、燃料箱很滿」：大家很安心，底下卻累積了很多風險。但燃料箱滿了也常常好幾年沒事，它不是倒數計時。"
        "依據：Giglio, Kelly & Pruitt（2016）、Greenwood 等（2022）、Adrian, Boyarchenko & Giannone（2019）。不是投資建議。")


def thermo(eng) -> list:
    """[(name, hot, reading)] for the real-time stress gauges that have data."""
    out = []
    st = getattr(eng, "stress", None)
    if st is not None and getattr(st, "score", None) is not None:
        out.append(("壓力指數 SSI", st.score >= 55, f"{st.score:.0f}"))
    try:
        from wsb.analytics import vol_breadth as VB
        v = VB.vix_term(eng)
        if v:
            out.append(("VIX 期限結構", v["ratio"] >= 1, f"VIX÷VIX3M {v['ratio']:.2f}"))
    except Exception:  # noqa: BLE001
        pass
    try:
        from tools import site_transmission as STR
        f = (STR._v(eng) or {}).get("fsi")
        if f:
            out.append(("OFR 金融壓力", f["now"] > 0, f"{f['now']:+.2f}"))
    except Exception:  # noqa: BLE001
        pass
    op = getattr(getattr(eng, "options", None), "spx", None) or {}
    if op.get("zero_gamma") and op.get("spot"):
        out.append(("零 Gamma 翻轉點", op["spot"] < op["zero_gamma"], f"{(op['spot'] / op['zero_gamma'] - 1) * 100:+.1f}%"))
    return out


def fuel(eng):
    try:
        from tools.site_slow import _fr
        from wsb.analytics import vulnerability as VU
        r = VU.build(eng, _fr().get("ebp"))
        return r if r.get("available") else None
    except Exception:  # noqa: BLE001
        return None


def combo(hot_t: int, n_t: int, hot_f: int, n_f: int, rzone: bool = False) -> str:
    """Fuel has three levels: full = at least half the lights or the R-zone (credit and asset prices hot together)."""
    if n_t == 0 or (n_f == 0 and not rzone):            # no readings on a side: say so, never "both calm"
        miss = "、".join(x for x, n in (("溫度計", n_t), ("燃料", n_f)) if n == 0)
        return f"{miss}資料暫缺，無法完整判斷"
    need = n_t if n_t <= 2 else max(2, (n_t + 1) // 2)   # one gauge alone can still say "warm"
    warm = hot_t >= need
    fuel_lv = "full" if rzone or hot_f * 2 >= n_f else "some" if hot_f >= 2 else "low"
    return {(False, "full"): "表面平靜、底下燃料多：研究上危機前最常見的組合，但可能還要好幾年才出事",
            (True, "full"): "正在升溫，而且底下燃料多：這種時候下跌比較容易變大",
            (True, "some"): "正在升溫，底下也累積了一些燃料：值得留意，但還不是最危險的組合",
            (True, "low"): "正在升溫，但底下燃料不多：比較像一般的修正或短期驚嚇",
            (False, "some"): "今天不緊，但底下累積了一些燃料",
            (False, "low"): "兩邊都平靜：今天不緊，底下也沒有累積太多燃料"}[(warm, fuel_lv)]


def headline(t: list, f) -> str:
    ht = sum(1 for x in t if x[1])
    s = f"一句話看懂：溫度計 {len(t)} 項有 {ht} 項偏緊"
    if f:
        rz = any(x.get("k") == "rzone" and x["state"] == "hot" for x in f.get("lights") or [])
        s += f"、燃料箱 {f['n']} 盞有 {f['n_hot']} 盞過熱——{combo(ht, len(t), f['n_hot'], f['n'], rz)}。"
    else:
        s += "；燃料箱資料暫缺。"
    return s


def health_line(eng) -> str:
    """The other side of the same card: how healthy the environment is (cool-down checks + healthy-bull gauges), so the
    overview turns positive by itself once the stress passes."""
    try:
        from tools import site_entry as SEN
        from wsb.analytics import cooldown as CD
        cool, bull = SEN._cool(eng), (SEN._env(eng).get("bull") or [])
    except Exception:  # noqa: BLE001
        return ""
    if not cool.get("available"):
        return ""
    ph = {"stress": "🔴 壓力還在", "cooling": "🟡 退燒中", "mixed": "🟡 部分偏緊", "calm": "🟢 平時狀態"}[CD.phase(cool)]
    k = sum(1 for x in bull if x["ok"])
    good = cool["n_ok"] * 2 > cool["n"] and bull and k * 2 > len(bull)
    if good:
        tail = "環境健康：壓力退了，漲勢也有廣度"
    elif cool["n_ok"] * 2 <= cool["n"]:
        tail = "健康度還不夠：壓力指標未全面回穩"
    elif not bull:
        tail = "壓力大致回穩；多頭健康度資料暫缺"
    else:
        tail = "健康度還不夠：漲勢集中、資金偏防守"
    txt = (f"🌤️ 環境健康度：{ph}，退燒檢查 {cool['n_ok']}／{cool['n']} 項回到正常"
           + (f"、多頭健康度 {k}／{len(bull)} 項健康" if bull else "") + f"——{tail}。")
    return (f'<p class="small">{T(txt, "")} <a class="golink" href="#entry" data-p="entry">{T("看「AI 視角看進場」→", "Entry view →")}</a></p>')


def sec_dual(eng) -> str:
    t, f = thermo(eng), fuel(eng)
    if not t and not f:
        return ""
    li = lambda name, hot, txt: (f'<li><b class="{"dn" if hot else "up"}">{"🔥" if hot else "🟢"}</b> {T(name, "")}'  # noqa: E731
                                 f'<span class="small muted">　{T(txt, "")}</span></li>')
    left = "".join(li(n, h, r) for n, h, r in t)
    right = "".join(li(x["zh"], x["state"] == "hot", x["txt"]) for x in (f or {}).get("lights") or [])
    body = (f'<p class="rimp big2"><b>{T(headline(t, f), "")}</b></p>{health_line(eng)}<div class="dual2">'
            f'<div><h3>{T("🌡️ 即時壓力溫度計：今天市場有多緊", "Real-time stress")}</h3><ul class="dlst">{left}</ul></div>'
            f'<div><h3>{T("⛽ 累積脆弱度燃料箱：底下累積了多少燃料", "Built-up vulnerability")}</h3><ul class="dlst">{right or "<li>—</li>"}</ul>'
            f'<p class="small"><a class="golink" href="#outlook" data-p="outlook">{T("看燃料箱每一盞燈的細節 →", "Details →")}</a></p></div></div>'
            f'<details class="sgx"><summary>{T("為什麼要分兩邊看", "Why two tracks")}</summary><p class="note">{T(NOTE, "")}</p></details>')
    return card("風險雙軌：溫度計 vs 燃料箱", "Two tracks: stress now vs fuel built up", body, "wide")


def foi_badge(eng) -> str:
    """One line under the market strip: foreign investors' net TAIEX futures position (FinMind, after the close)."""
    try:
        from tools import site_watch2 as SW2
        v = SW2._tw(eng)
    except Exception:  # noqa: BLE001
        v = None
    if not v:
        return ""
    side = "空單" if v["net"] < 0 else "多單"
    pct = v["pct"] if v["net"] < 0 else 100 - v["pct"]               # how extreme on its own side
    where = (f"{v['since']} 年來最多" if pct <= 5 else f"{v['since']} 年來偏多" if pct <= 20 else "一般水準")
    txt = f"{v['emoji']} 外資台指期{side} {abs(v['net']) / 1e4:.1f} 萬口（{where}・{str(v['date'])[5:]}）"
    return (f'<div class="foib">{T(txt, "")} <a class="golink" href="#taiwan" data-p="taiwan">{T("台股頁 →", "Taiwan →")}</a></div>')


CSS = (".dual2{display:grid;grid-template-columns:1fr 1fr;gap:16px}.dual2>div{min-width:0}.dual2 h3{margin:4px 0 6px;font-size:14.5px}"
       ".dlst{list-style:none;padding:0;margin:0}.dlst li{margin:5px 0;line-height:1.5}@media(max-width:720px){.dual2{grid-template-columns:1fr}}"
       ".foib{font-size:12.5px;margin:6px 2px 0;color:var(--tx)}")
