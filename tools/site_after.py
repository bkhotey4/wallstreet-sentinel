"""財報後白話解讀 (top of 財經日曆, and the tech ones on 科技財報): after US companies report, a cloud routine writes
research_feed/earn_after.json — for every company of any sector that reported (market cap ≥ 200 億美元), a plain sentence,
what the numbers say beyond "beat / miss", who else is affected (suppliers, rivals, customers, Taiwan supply chain), the
macro / bond backdrop it lands in, and the after-hours move explained only with news that matches it.  Not advice."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "earn_after.json"   # public repo only
BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出")
TECH = ("科技", "半導體", "通訊", "軟體", "雲端", "AI")


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _esc(x) -> str:
    s = str(x or "")
    for w in BANNED:                                   # the routine is told not to use them; never shown even if it slips
        s = s.replace(w, "—")
    return html.escape(guard_safe(s))


def _list(xs) -> str:
    return "".join(f"<li>{_esc(x)}</li>" for x in (xs or []) if x and isinstance(x, str))


def _item(it: Dict) -> str:
    mv = it.get("move") if isinstance(it.get("move"), dict) else {}
    pct = mv.get("pct")
    cl = "up" if isinstance(pct, (int, float)) and pct > 0 else "dn" if isinstance(pct, (int, float)) and pct < 0 else ""
    head = (f'<h3>{_esc(it.get("name") or it.get("sym"))} <span class="muted small">{_esc(it.get("sym"))}・{_esc(it.get("sector"))}・'
            f'{_esc(it.get("date"))}</span>' + (f' <b class="{cl}">{pct:+.1f}%</b>' if isinstance(pct, (int, float)) else "") + "</h3>")
    spill = "".join(f'<li><b>{_esc(s.get("who"))}</b>：{_esc(s.get("how"))}</li>' for s in (it.get("spill") or []) if isinstance(s, dict))
    src = _list(it.get("sources"))
    parts = [f'<p class="rimp"><b>{_esc(it.get("one"))}</b></p>']
    if mv.get("why"):
        parts.append(f'<p class="small">股價反應：{_esc(mv.get("why"))}</p>')
    det = ""
    if it.get("company"):
        det += f"<h4>公司本身（不只看有沒有賺錢）</h4><ul>{_list(it.get('company'))}</ul>"
    if spill:
        det += f"<h4>連帶影響</h4><ul>{spill}</ul>"
    if it.get("macro"):
        det += f"<h4>大環境（總經、利率、信用、其他財報）</h4><ul>{_list(it.get('macro'))}</ul>"
    if src:
        det += f'<h4>來源</h4><ul class="small">{src}</ul>'
    if det:
        parts.append(f'<details class="sgx"><summary>展開：公司、連帶影響、大環境</summary>{det}</details>')
    return f'<div class="rpt">{head}{"".join(parts)}</div>'


def _items(tech_only: bool = False) -> List[Dict]:
    d = load()
    items = [x for x in (d.get("items") or []) if isinstance(x, dict) and x.get("sym") and x.get("date") and x.get("one")]
    if tech_only:
        items = [x for x in items if any(t in str(x.get("sector") or "") for t in TECH)]
    return sorted(items, key=lambda x: (str(x["date"]), float(x.get("mcap_b") or 0)), reverse=True)


def _card(items: List[Dict], title: str, en: str, n: int) -> str:
    if not items:
        return ""
    d = load()
    day = items[0]["date"]
    latest = [x for x in items if x["date"] == day]
    lead = f'一句話看懂：{day} 公布的 {len(latest)} 家：' + "；".join(f'{x.get("name") or x["sym"]}——{x.get("one")}' for x in latest[:3])
    bg = d.get("backdrop")
    note = ("每天台北早上 7 點與晚上 9 點，由 AI 分析任務讀取公司官方財報新聞稿與可靠報導，替前一段時間公布財報、市值 200 億美元以上的美股公司"
            "（所有產業，不只科技）寫白話解讀：除了有沒有賺錢，還看營收品質、利潤率、財測、現金流，對供應商／競爭對手／客戶／台灣供應鏈的連帶影響，"
            "以及當時的總經、利率、信用環境。股價反應只用時間對得上的新聞解釋。這是解讀，不是投資建議。")
    body = (f'<p class="rimp big2"><b>{_esc(lead)}</b></p>'
            + (f'<p class="small"><b>大環境：</b>{_esc(bg)}</p>' if bg else "")
            + "".join(_item(x) for x in items[:n])
            + f'<p class="note">{note}{"　更新 " + _esc(d.get("updated")) if d.get("updated") else ""}</p>')
    return card(title, en, body, "wide")


def sec_earn_after(eng) -> str:
    return _card(_items(), "財報後白話解讀（所有美股）", "After the report: plain-language reads (all US stocks)", 12)


def sec_earn_after_tech(eng) -> str:
    return _card(_items(True), "財報後白話解讀（科技）", "After the report: tech", 6)
