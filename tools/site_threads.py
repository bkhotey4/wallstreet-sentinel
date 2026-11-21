"""主線追蹤卡（新聞日曆頁，2026-11-21 盲點檢討）：把新聞串成 11 條長期主線，看哪一條正在升溫。規則在 wsb/analytics/threads.py。"""
from __future__ import annotations

import time
import json
from pathlib import Path
from typing import Dict

from tools.sitekit import card, esc, guard_safe

VIEW: Dict = {}            # set by the build (build_site fetches /api/news, archives it, computes the view)
PILL = {"升溫": "🔥 升溫", "官方新文件": "📄 官方新文件", "有消息": "有消息", "安靜": "安靜"}


READ = Path(__file__).resolve().parents[1] / "research_feed" / "threads_read.json"   # public repo: hand-written reads per thread


def reads() -> Dict:
    try:
        d = json.loads(READ.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _read_html(r: Dict) -> str:
    """The analysis written after reading the primary documents: hypothesis, chain, for / against / what would confirm."""
    li = lambda xs: "".join(f"<li>{esc(guard_safe(str(x)))}</li>" for x in xs or [])  # noqa: E731
    src = "、".join(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s.get("name") or "原文")}</a>'
                   for s in r.get("sources") or [] if isinstance(s, dict) and str(s.get("url", "")).startswith("https://"))
    return (f'<div class="rpt"><p class="small"><b>📝 讀過原文的判斷（假設，不是事實）</b>：{esc(guard_safe(r.get("hypothesis", "")))}</p>'
            + (f'<p class="small"><b>事情的先後</b></p><ol class="small">{li(r.get("chain"))}</ol>' if r.get("chain") else "")
            + "".join(f'<p class="small"><b>{lab}</b></p><ul class="small">{li(r.get(k))}</ul>'
                      for k, lab in (("for", "支持的證據"), ("against", "反對或還不確定的地方"), ("confirm", "接下來什麼消息能證實或推翻")) if r.get(k))
            + (f'<p class="small muted">原文：{src}</p>' if src else "") + "</div>")


def _tpe(ts) -> str:
    return time.strftime("%m/%d %H:%M", time.gmtime(float(ts or 0) + 8 * 3600))


def _move(eng, sym: str) -> str:
    try:
        q = eng.market.q(sym) or {}
        c = q.get("chg_pct")
        return f"{c:+.1f}%" if c is not None else ""
    except Exception:  # noqa: BLE001
        return ""


def sec_threads(eng) -> str:
    v = VIEW
    th = v.get("threads") or []
    if not th:
        return ""
    hot = [t for t in th if t["state"] in ("升溫", "官方新文件")]
    lead = ("這 48 小時升溫或有官方新文件的主線：" + "、".join(f'{t["zh"]}（{PILL[t["state"]]}）' for t in hot)) if hot else "這 48 小時沒有主線明顯升溫。"
    young = (f'新聞資料從開始累積到現在只有 {v.get("days", 0)} 天，「平常幾則」要累積滿 14 天才準。' if float(v.get("days") or 0) < 14 else "")
    rd = (reads().get("threads") or {})
    blocks = []
    for t in sorted(th, key=lambda t: ({"升溫": 0, "官方新文件": 1, "有消息": 2, "安靜": 3}[t["state"]], -t["n48"])):
        mv = "、".join(f'{zh} {m}' for sym, zh in t["assets"] for m in [_move(eng, sym)] if m)
        heads = "".join(
            f'<li>{_tpe(x["ts"])}・{"📄 " if x.get("off") else ""}<a href="{esc(x["u"])}" target="_blank" rel="noopener noreferrer">{esc(guard_safe(x["t"]))}</a>'
            f'<span class="muted">（{esc(x["s"])}）</span></li>' for x in t["items"][:8])
        r = rd.get(t["id"]) if isinstance(rd.get(t["id"]), dict) else None
        blocks.append(f'<details class="sgx"{" open" if r and t["state"] != "安靜" else ""}><summary><b>{esc(t["zh"])}</b>　{PILL[t["state"]]}　48 小時 {t["n48"]} 則／平常約 {t["base"]} 則'
                      + ("　📝" if r else "") + f'</summary><p class="small">{esc(t["why"])}' + (f'<br>相關行情今天：{esc(mv)}' if mv else "") + "</p>"
                      + (_read_html(r) if r else "")
                      + (f'<p class="small"><b>最近的新聞（標題）</b></p><ul class="small">{heads}</ul>' if heads else '<p class="small muted">最近 30 天沒有相關新聞。</p>') + "</details>")
    body = (f'<p class="rimp"><b>一句話看懂：{esc(lead)}</b></p>'
            '<p class="small">每天的新聞各看各的，很容易漏掉「一則接一則、每則都不大」的事。這裡把新聞歸到 11 條長期主線，'
            '比較最近 48 小時和平常的則數；📄＝官方來源（央行、國會委員會等）。</p>' + "".join(blocks)
            + f'<p class="note">{esc(young)}依標題關鍵字歸類，只代表「相關新聞變多」，不是讀過內文的判斷，也不代表市場一定會動；'
            '📝＝每日排程讀過原始文件後寫的判斷（假設，附反對理由）；讀過全文的新聞也在每日總經「這班讀過的原文」。升溫＝48 小時 3 則以上而且是平常的 2 倍以上。Discord 在主線升溫或有官方新文件時提醒（每條主線一天最多一次）。</p>')
    return card("主線追蹤：把新聞串成一條線", "Story threads", body, "wide")
