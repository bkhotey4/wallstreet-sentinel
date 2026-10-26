"""財報前瞻 (top of 科技財報): before each big AI-related report a cloud routine writes research_feed/earn_preview.json —
the call (樂觀／中性／悲觀), probabilities for capex raised / held / cut, three scenarios with probabilities and who is
affected, the forward gauges (neocloud bond yields, AI capex ÷ operating cash flow) — and after the report it records
what happened, so the page also shows how often the calls were right (hit rate and Brier score).  Estimates, not advice."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List, Optional

from tools.sitekit import card

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "earn_preview.json"   # public repo only
CALLS = {"樂觀": "up", "中性": "", "悲觀": "dn"}
OUTS = ("上修", "維持", "下修")


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _probs(p) -> Optional[Dict[str, float]]:
    if not isinstance(p, dict):
        return None
    try:
        v = {k: float(p[k]) for k in OUTS if k in p}
    except (TypeError, ValueError):
        return None
    s = sum(v.values())
    return {k: x / s * 100 for k, x in v.items()} if len(v) == 3 and s > 0 else None


def score(items: List[Dict]) -> Optional[Dict]:
    """Hit rate (the most likely outcome happened) and Brier score over the reports already out (0 = perfect, 0.67 = always 1/3)."""
    done = [(it, _probs(it.get("probs"))) for it in items if it.get("outcome") in OUTS]
    done = [(it, p) for it, p in done if p]
    if not done:
        return None
    hits = sum(1 for it, p in done if max(p, key=p.get) == it["outcome"])
    brier = sum(sum((p[k] / 100 - (1.0 if k == it["outcome"] else 0.0)) ** 2 for k in OUTS) for it, p in done) / len(done)
    return {"n": len(done), "hits": hits, "brier": brier}


def _esc(x) -> str:
    return html.escape(str(x or ""))


def _item(it: Dict) -> str:
    p = _probs(it.get("probs"))
    call = str(it.get("call") or "")
    head = (f'<h3>{_esc(it.get("name") or it.get("sym"))} <span class="muted small">{_esc(it.get("sym"))}・{_esc(it.get("date"))}</span> '
            f'<b class="{CALLS.get(call, "")}">{_esc(call)}</b></h3>')
    bar = ""
    if p:
        bar = ('<p>資本支出／財測：' + "、".join(f'{k} <b>{p[k]:.0f}%</b>' for k in OUTS)
               + (f'；選擇權預期財報後股價波動 ±{float(it["implied_move"]):.1f}%' if isinstance(it.get("implied_move"), (int, float)) else "") + "</p>")
    sc = "".join(f'<li><b>{_esc(s.get("name"))}（{_esc(s.get("prob"))}%）</b>：{_esc(s.get("what"))}'
                 + (f'<div class="small muted">影響：{_esc(s.get("impact"))}</div>' if s.get("impact") else "") + "</li>"
                 for s in (it.get("scenarios") or []) if isinstance(s, dict))
    basis = "".join(f"<li>{_esc(b)}</li>" for b in (it.get("basis") or []) if b)
    out = ""
    if it.get("outcome"):
        ok = p and it["outcome"] in OUTS and max(p, key=p.get) == it["outcome"]
        out = (f'<p class="rimp"><b>結果：{_esc(it["outcome"])}</b>' + (" ✅ 猜中" if ok else " ❌ 沒猜中" if p else "")
               + (f'——{_esc(it.get("outcome_note"))}' if it.get("outcome_note") else "") + "</p>")
    return (f'<div class="rpt">{head}{out}{bar}' + (f"<ul>{sc}</ul>" if sc else "")
            + (f'<details class="sgx"><summary>判斷依據</summary><ul class="small">{basis}</ul></details>' if basis else "") + "</div>")


def sec_earn_preview(eng) -> str:
    d = load()
    items = [x for x in (d.get("items") or []) if isinstance(x, dict) and x.get("sym") and x.get("date")]
    if not items:
        return ""
    up = sorted([x for x in items if not x.get("outcome")], key=lambda x: str(x["date"]))
    past = sorted([x for x in items if x.get("outcome")], key=lambda x: str(x["date"]), reverse=True)
    sc = score(items)
    lead = "一句話看懂：" + ("、".join(f'{x.get("name") or x["sym"]} {x.get("call", "")}' for x in up[:4]) + "（財報前的機率估計）。" if up else "最近沒有即將公布的重點財報。")
    gauges = "".join(f'<li><b>{_esc(g.get("name"))}</b>：{_esc(g.get("read"))}</li>' for g in (d.get("gauges") or []) if isinstance(g, dict))
    rec = (f'<p class="rimp">過去 {sc["n"]} 次預估：最可能的情境猜中 {sc["hits"]} 次（{sc["hits"] / sc["n"] * 100:.0f}%）；'
           f'Brier 分數 {sc["brier"]:.2f}（0 是完美、0.67 等於每次都猜三分之一，越低越準）。</p>') if sc else '<p class="small muted">還沒有已公布的結果可以對答案；每次財報公布後會自動記錄猜中與否。</p>'
    note = ("每天晚上 8 點（台北）由 AI 分析任務讀取公開資料（公司上次的財測與管理層說法、供應鏈數據、分析師共識的公開報導、選擇權隱含波動），"
            "替未來 3 天要公布的重點財報寫機率估計，並在公布後記錄實際結果。機率是估計，會猜錯，所以本站公開成績單；不是投資建議。")
    body = (f'<p class="rimp big2"><b>{_esc(lead)}</b></p>' + "".join(_item(x) for x in up[:6])
            + (f'<h3>前瞻指標</h3><ul>{gauges}</ul>' if gauges else "") + f'<h3>成績單</h3>{rec}'
            + ("".join(_item(x) for x in past[:4]) if past else "")
            + f'<p class="note">{note}{"　更新 " + _esc(d.get("updated")) if d.get("updated") else ""}</p>')
    return card("財報前瞻：公布前的機率估計與成績單", "Earnings preview & track record", body, "wide")
