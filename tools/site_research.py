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
    ("Excess Bond Premium 與 Fed 衰退機率", "尚未", "Fed 每月免費 CSV；需自存每月版本（會回溯修正）。"),
    ("累積脆弱度層（R-zone、家庭債務、SLOOS、利差過低反向燈）", "尚未", "季頻、抓不準時點，定位為「底下累積了多少燃料」。"),
    ("明尼亞波利斯 Fed 選擇權隱含大跌機率", "尚未", "資料欄位與更新頻率待實測。"),
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


def sec_research(eng) -> str:
    secs = sections()
    if not secs:
        return ""
    head = T(f"學術界、各國央行（聯準會、ECB、BIS、IMF、英格蘭銀行）對金融風險預警的研究整理，對照本站的做法。整理日期 {COMPILED}；"
             "這是一份有日期的文獻整理，不是即時資料。文中數字來自各篇論文；標明「依網站資料自行計算」的除外。",
             f"Literature review compiled {COMPILED}; a dated document, not live data.")
    cards = [card("學術研究：本站怎麼對照學界與央行", "Research: how this site compares with the literature",
                  f'<p class="sub">{head}</p>' + md_html(secs[0][1]), "wide")]
    for t, b in secs[1:]:
        cards.append(card(t, t, md_html(b), "wide"))
    return "".join(cards)


def sec_research_status(eng) -> str:
    cls = {"已完成": "up", "已符合": "up", "部分完成": "muted", "尚未": "dn"}
    rows = "".join(f'<tr><td>{T(a, a)}</td><td><b class="{cls[s]}">{T(s, s)}</b></td><td class="small">{T(n, n)}</td></tr>' for a, s, n in STATUS)
    body = (f'<table class="mini"><thead><tr><th>{T("研究建議", "Recommendation")}</th><th>{T("本站狀態", "Status")}</th>'
            f'<th>{T("說明", "Notes")}</th></tr></thead><tbody>{rows}</tbody></table>'
            f'<p class="note">{T("每做完一項就更新這張表。", "Updated as items are done.")}</p>')
    return card("研究建議的落實進度", "Progress on the recommendations", body, "wide")
