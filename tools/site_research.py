"""學術研究 page: the literature review on early-warning methods (tools/static/research_*.md, dated) rendered as cards,
plus a status card saying which of its recommendations the site already follows.  The review is a dated document, not
live data: its header says when it was compiled and its numbers are the papers' (or marked as the site's own)."""
from __future__ import annotations

import html
import re
from pathlib import Path
from typing import List, Tuple

from tools.sitekit import T, card

STATIC = Path(__file__).parent / "static"
FILE = "research_risk_2026-10.md"
COMPILED = "2026-10-23"

# which of the review's recommendations the site already does (kept by hand: update with each change)
STATUS = [
    ("回測頁改版：命中率與精確率附 95% 信賴區間", "部分完成", "危機預警成績單已列出命中率與精確率的 95% 區間（Wilson）；隨機亮燈基準、擴張視窗選門檻、block bootstrap 尚未做。"),
    ("Excess Bond Premium 與 Fed 衰退機率", "已完成", "「美債」頁；每天抓一次，另存每天看到的最新值（聯準會會回溯修正）。"),
    ("累積脆弱度層（R-zone、家庭債務、SLOOS、利差過低反向燈）", "已完成", "「全方位風險」頁；門檻用擴張視窗，標明抓不準時點。"),
    ("明尼亞波利斯 Fed 選擇權隱含大跌機率", "已完成", "「全方位風險」頁；每週資料，標明是風險中性機率。"),
    ("SSI 加 CISS 式相關性聚合版本並列", "尚未", "沒有勝過現行做法的樣本外證據，只並列、不取代。"),
    ("BDC 燈號加入 PIK 與非應計比率", "尚未", "網站已有 SEC 管線與私募信貸燈號。"),
    ("信用利差：同步不領先、高水位才有預警力", "已完成", "「美債」頁「信用與利率：現在的關係」每週重算。"),
    ("信用背離不是可靠前兆（加註回測）", "已完成", "衝擊雷達的股債背離列出回測機率。"),
    ("VRP、尾端風險放抄底區而非警報區", "已符合", "抄底四訊號與崩跌警報分開呈現。"),
]


def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def md_html(md: str) -> str:
    """Just what the review uses: paragraphs, pipe tables, bold, code, links."""
    out, i, lines = [], 0, md.splitlines()
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip()):
            head = [c.strip() for c in ln.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append('<div class="scroll"><table class="mini"><thead><tr>' + "".join(f"<th>{_inline(h)}</th>" for h in head)
                       + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows)
                       + "</tbody></table></div>")
            continue
        if ln.strip():
            out.append(f"<p>{_inline(ln.strip())}</p>")
        i += 1
    return "".join(out)


def sections() -> List[Tuple[str, str]]:
    """[(title, markdown body)] — the H1 with its lead paragraph first, then each H2."""
    try:
        md = (STATIC / FILE).read_text(encoding="utf-8")
    except OSError:
        return []
    out, title, buf = [], None, []
    for ln in md.splitlines():
        m = re.match(r"^(#{1,2})\s+(.*)$", ln)
        if m:
            if title is not None:
                out.append((title, "\n".join(buf)))
            title, buf = m.group(2).strip(), []
        else:
            buf.append(ln)
    if title is not None:
        out.append((title, "\n".join(buf)))
    return [(("結論" if t == "Conclusion" else t), b) for t, b in out]


# the review in six points: what the research says, and what it implies (compiled with the review, see COMPILED)
POINTS = [
    ("壓力指標是溫度計，不是預言機",
     ["各國央行的壓力指數（OFR、NFCI、聖路易、堪薩斯）彼此高度重疊，本質上都是「同步」反映現在有多緊。",
      "這類指標預測崩跌的準確度，學界實測大約就是 AUC 0.7；本站的崩跌模型 0.67–0.70 已在這個水準。",
      "機器學習在事件少的美股樣本裡，常常樣本外輸給簡單的邏輯迴歸。"],
     "沒有任何模型能精準預告崩盤。值得看的是「現在的風險是平常的幾倍」，不是「會不會崩」的是非題。"),
    ("真正能提前 1–3 年的，是信用循環",
     ["危機前常見的組合：利差異常低、借款快速擴張、資產價格大漲（Greenwood 等 2022：同時出現後 3 年內危機機率約 40–45%，平常約 7%）。",
      "聯準會的超額債券溢酬 EBP 偏低＝投資人對風險要求太少，研究顯示 1–2 年後經濟較易轉弱。"],
     "最危險的時候往往看起來最平靜。利差很低不是「市場很健康」，反而可能是燃料在累積；但它抓不準時點，可能燃燒好幾年才出事。"),
    ("利差暴衝是「確認」，不是「預告」",
     ["Krishnamurthy & Muir（2025）：利差突然大跳，多半代表危機已經開始，而不是提前警告。",
      "本站自己的回測也一樣：信用利差和股市是同一週一起動，提前 1–8 週幾乎看不出關係。"],
     "等到利差暴衝才反應，通常已經在下跌的路上了。真正有用的是「利差水位」和「壓力從低評等擴散到投資級」的過程。"),
    ("恐慌指標多半預告的是「之後報酬偏高」",
     ["變異數風險溢酬（VIX 減實際波動）、尾端風險指標偏高時，之後幾個月的報酬平均較高（Bollerslev 等 2009；Kelly & Jiang 2014）。",
      "CBOE SKEW 這類「黑天鵝指數」沒有可靠的崩跌預測力；CAPE 只說明長期報酬，不能抓時點。"],
     "恐慌高點歷史上常落在相對低點附近，所以本站把這類指標放在「抄底四訊號」，不放進崩跌警報。這是歷史統計，不是買賣建議。"),
    ("看到「準確率九成」先看誤報與樣本數",
     ["本站危機預警「7 次全亮燈」，但只有 7 個樣本，命中率的 95% 區間約 65%–100%；升溫後真的出事的比例只有約 23%。",
      "近年不少論文宣稱崩跌預測 AUC 0.86–0.89，但多半只在單一段期間測試、事件極少，換個期間就可能失效。"],
     "預警指標一定在「漏掉危機」和「狼來了」之間取捨。好的呈現方式是同時講命中、誤報和不確定性，本站正照這個標準調整。"),
    ("官方 2025–2026 年在擔心的地方，已經不在傳統銀行",
     ["聯準會、IMF、BIS 近期報告的重點：避險基金槓桿與美債基差交易（約 8,300 億美元，是 2020 年高峰的兩倍）、私募信貸、AI 權值股集中、政府債務與債市的連動。",
      "這些領域的公開資料大多有延遲或不透明，很難做成即時燈號。"],
     "下一次壓力可能從「看不太到」的地方冒出來，例如美債市場的流動性或私募信貸的贖回，所以本站持續追蹤私募信貸 BDC 與美債市場相關指標。"),
]


def _fr_data():
    try:
        from wsb.data import fed_research as FR
        return FR.load()
    except Exception:  # noqa: BLE001
        return {}


def _rank(vals, v):
    return sum(x < v for x in vals) / len(vals) * 100 if vals else None


def now_reading(eng) -> list:
    """Today's data read through the review's lens: rules on live numbers, no fixed text about the market."""
    out = []
    ssi = getattr(getattr(eng, "stress", None), "score", None)
    fr = _fr_data()
    mp = (fr.get("mpd") or {}).get("sp6m") or []
    mpd_p = _rank([r[1] for r in mp[:-1]], mp[-1][1]) if len(mp) > 20 else None
    eb = fr.get("ebp") or []
    ebp_p = _rank([r[2] for r in eb[:-1]], eb[-1][2]) if len(eb) > 24 else None
    vu = {}
    try:
        from wsb.analytics import vulnerability as VU
        vu = VU.build(eng, eb)
    except Exception:  # noqa: BLE001
        pass
    hot = {x["k"] for x in vu.get("lights") or [] if x["state"] == "hot"}
    tense = ssi is not None and ssi >= 55
    calm_opts = mpd_p is not None and mpd_p <= 30
    fear_opts = mpd_p is not None and mpd_p >= 70
    rich_credit = (ebp_p is not None and ebp_p <= 20) or "spreads" in hot
    if ssi is not None:
        out.append(("即時層（溫度計）", f"壓力指數 SSI {ssi:.0f}，" + ("偏高：市場已經在緊張。" if tense else "在常態範圍。")))
    if mpd_p is not None:
        out.append(("選擇權層（大家花多少錢買保險）", f"選擇權定價標普 6 個月內跌 20% 以上的機率 {mp[-1][1]:.1f}%，在 2007 年以來第 {mpd_p:.0f} 百分位，"
                    + ("偏低：多數人不認為會大跌。" if calm_opts else "偏高：市場在為大跌付高價。" if fear_opts else "中等。")))
    if ebp_p is not None or "spreads" in hot:
        out.append(("信用層（借錢給企業的人有多放心）", (f"超額債券溢酬在 1973 年以來第 {ebp_p:.0f} 百分位" if ebp_p is not None else "公司債利差在歷史低檔")
                    + ("：信用定價非常樂觀。" if rich_credit else "：信用定價正常。")))
    if vu.get("lights"):
        out.append(("累積層（底下的燃料）", f"{vu['n']} 盞燈中 {vu['n_hot']} 盞過熱"
                    + ("，而且信用與資產同時過熱（R-zone）。" if "rzone" in hot else "，但沒有出現信用與資產同時過熱的 R-zone。")))
    if tense and calm_opts and rich_credit:
        m = ("壓力指數在升溫，但選擇權和信用市場都還很放心。這種「溫度計說熱、保險和借貸市場說沒事」的分歧，代表兩種可能："
             "一是壓力只是局部的（例如集中在低評等債或少數產業），之後會自己消退；二是大市場還沒反應，一旦信用跟著轉弱，修正會比較急。"
             "歷史上 SSI 升溫後真正跌 10% 以上的只有約四分之一，所以不必恐慌；要盯的是分歧開始收斂的訊號："
             "投資級利差跟著擴大、選擇權大跌機率升到第 70 百分位以上、超額債券溢酬由負轉正。")
    elif tense and fear_opts:
        m = "壓力指數和選擇權市場同時緊張：各層訊號一致，屬於全面的風險趨避，歷史上這時波動通常會放大。"
    elif not tense and (rich_credit or "rzone" in hot):
        m = ("即時壓力不高，但信用定價樂觀、燃料在累積：這正是研究說的「最危險的平靜」。它抓不準時點，可能持續好幾年，"
             "但代表一旦出事，跌幅可能比平常深。")
    elif not tense:
        m = "各層大致平靜：即時壓力、選擇權和信用市場都沒有明顯警訊。"
    else:
        m = "壓力指數偏高，其他層沒有一致方向：先看壓力是否擴散到信用與選擇權市場。"
    out.append(("合起來怎麼看", m))
    return out


def sec_research(eng) -> str:
    secs = sections()
    head = T(f"學術界與各國央行（聯準會、ECB、BIS、IMF、英格蘭銀行）對金融風險預警的研究，整理成 6 個重點。整理日期 {COMPILED}。",
             f"Six takeaways from the literature, compiled {COMPILED}.")
    pts = ""
    for k, (t, bullets, imp) in enumerate(POINTS, 1):
        lis = "".join(f"<li>{T(b, b)}</li>" for b in bullets)
        pts += (f'<div class="rpt"><h3>{k}. {T(t, t)}</h3><ul class="brief">{lis}</ul>'
                f'<p class="rimp"><b>{T("隱含意義", "So what")}</b>：{T(imp, imp)}</p></div>')
    cards = [card("學術研究重點：6 件事", "Research: six takeaways", f'<p class="sub">{head}</p>{pts}', "wide")]
    now = now_reading(eng)
    if now:
        rows = "".join(f'<tr><td class="nw"><b>{T(a, a)}</b></td><td>{T(b, b)}</td></tr>' for a, b in now[:-1])
        last = now[-1][1]
        note = T("用今天的資料、照上面的研究邏輯自動解讀，每次網站更新都會重算。這是對現況的描述，不是預測，也不是投資建議。",
                 "Recomputed each build. Not a forecast or advice.")
        body = (f'<table class="mini"><tbody>{rows}</tbody></table>'
                f'<p class="rimp"><b>{T("合起來怎麼看", "Putting it together")}</b>：{T(last, last)}</p><p class="note">{note}</p>')
        cards.append(card("套用到現在的市場：各層訊號在說什麼", "Applied to today: what each layer says", body, "wide"))
    if secs:
        full = "".join(f"<h3>{T(t, t)}</h3>" + md_html(b) for t, b in secs)
        intro = T("附錄：這份是當初為了改進本站而做的完整文獻整理，所以文中常出現「網站應該補什麼」的建議口吻；論文出處與資料連結都在這裡。",
                  "Appendix: the full review written to improve this site, with all sources.")
        cards.append(card("附錄：完整研究報告與論文出處", "Appendix: full review and sources",
                          f'<p class="note">{intro}</p><details class="sgx"><summary>{T("點開看完整報告", "Show the full review")}</summary>{full}</details>', "wide"))
    return "".join(cards)


CSS = ".rpt{margin:4px 0 14px}.rpt h3{margin:8px 0 4px;font-size:15px}.rimp{margin:4px 0 0;padding:8px 10px;border-left:3px solid var(--ac);background:var(--wash)}"


def sec_research_status(eng) -> str:
    cls = {"已完成": "up", "已符合": "up", "部分完成": "muted", "尚未": "dn"}
    rows = "".join(f'<tr><td>{T(a, a)}</td><td><b class="{cls[s]}">{T(s, s)}</b></td><td class="small">{T(n, n)}</td></tr>' for a, s, n in STATUS)
    body = (f'<table class="mini"><thead><tr><th>{T("研究建議", "Recommendation")}</th><th>{T("本站狀態", "Status")}</th>'
            f'<th>{T("說明", "Notes")}</th></tr></thead><tbody>{rows}</tbody></table>'
            f'<p class="note">{T("每做完一項就更新這張表。", "Updated as items are done.")}</p>')
    return card("研究建議的落實進度", "Progress on the recommendations", body, "wide")


# ------------------------------------------------------------------ 最新學術動態 (written weekly by a cloud routine)
FEED = Path(__file__).resolve().parents[1] / "research_feed" / "feed.json"   # public site repo root only, never synced over


def load_feed() -> list:
    import json
    try:
        d = json.loads(FEED.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for it in (d.get("items") if isinstance(d, dict) else None) or []:
        if not isinstance(it, dict):
            continue
        url = str(it.get("url") or "")
        if not (url.startswith("https://") or url.startswith("http://")) or not it.get("title") or not it.get("summary"):
            continue                                            # a malformed entry is skipped, never breaks the page
        out.append(it)
    out.sort(key=lambda x: str(x.get("added") or x.get("published") or ""), reverse=True)
    return out


def sec_research_feed(eng) -> str:
    items = load_feed()[:10]
    if not items:
        return ""
    esc_ = lambda x: html.escape(str(x or ""))  # noqa: E731
    rows = ""
    for it in items:
        rows += (f'<div class="rpt"><h3><a href="{esc_(it["url"])}" target="_blank" rel="noopener">{esc_(it["title"])}</a></h3>'
                 f'<p class="small muted">{esc_(it.get("source"))}・{esc_(it.get("authors"))}・{esc_(it.get("published"))}</p>'
                 f'<p>{esc_(it["summary"])}</p>'
                 + (f'<p class="rimp"><b>隱含意義</b>：{esc_(it.get("implication"))}</p>' if it.get("implication") else "")
                 + (f'<p class="small">與本站的關係：{esc_(it.get("site_relevance"))}</p>' if it.get("site_relevance") else "") + "</div>")
    note = ("每週一由 AI 研究任務搜尋聯準會、BIS、IMF、NBER、ECB 等新發表的研究，挑出和本站相關的整理成中文重點。"
            "每篇都附原文連結，請以原文為準；AI 摘要可能有誤，也不是投資建議。")
    return card("最新學術動態（每週自動整理）", "Latest research (weekly)", rows + f'<p class="note">{note}</p>', "wide")
