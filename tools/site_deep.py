"""每日深度研判 (總覽): after each US close a cloud routine writes research_feed/deep.json —
- four lenses on the day: cash flow and physical limits, money and rates, who had to trade, what people are saying.
- 四個訊號: AI capex growth, the Texas permit rules, neocloud customers and funding, long-term money; together they
  say whether an AI sell-off was an overreaction or the market changing how it values these companies.
- 說法查核: popular claims held against data.
- 可驗證的判斷: dated claims the routine scores itself on later runs, so the card shows how often it was right.
Static content: the routine commits the JSON and the site shows it as written."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "deep.json"   # public repo only
VERDICT = {"有數據支持": "up", "部分支持": "", "證據不足": "muted", "與數據不符": "down"}
RESULT = {"對": "up", "錯": "down", "未到期": "muted"}
TREND = {"轉好": "up", "持平": "", "轉壞": "down", "資料不足": "muted"}
MIN_SCORED = 20                                                              # fewer settled calls say nothing yet


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _e(x) -> str:
    return html.escape(guard_safe(str(x or "")))


def _src(xs) -> str:
    out = []
    for s in xs or []:
        if not isinstance(s, dict):
            continue
        u = str(s.get("url") or "")
        name = _e(s.get("name") or "來源") + (f'（{_e(s.get("date"))}）' if s.get("date") else "")
        out.append(f'<a href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">{name}</a>' if u.startswith("https://") else name)
    return "、".join(out)


def _pill(text, tones: Dict[str, str]) -> str:
    t = str(text or "")
    return f'<span class="pill {tones.get(t, "")}">{_e(t)}</span>' if t else ""


def _rows(items, *keys) -> List[Dict]:
    return [x for x in items or [] if isinstance(x, dict) and all(x.get(k) for k in keys)]


def _lens(x: Dict) -> str:
    conf = f'<span class="muted">（把握度：{_e(x["conf"])}）</span>' if x.get("conf") else ""
    return (f'<li><b>{_e(x["name"])}</b>：{_e(x["read"])} {conf}'
            + (f'<div class="small muted">依據：{_e(x["evidence"])}</div>' if x.get("evidence") else "") + "</li>")


def _signal(x: Dict) -> str:
    return (f'<li>{_pill(x.get("trend"), TREND)} <b>{_e(x["name"])}</b>：{_e(x["read"])}'
            + (f'<div class="small muted">依據：{_e(x["evidence"])}</div>' if x.get("evidence") else "")
            + (f'<div class="small muted">下一個觀察點：{_e(x["next"])}</div>' if x.get("next") else "") + "</li>")


def _signals(rows: List[Dict]) -> str:
    if not rows:
        return ""
    count = "、".join(f'{k} {n} 項' for k in TREND if (n := sum(x.get("trend") == k for x in rows)))
    return (f'<h3>這次是過度反應，還是評價標準變了？</h3><p class="small">四個訊號目前：{_e(count)}。</p>'
            f'<ul class="lines">{"".join(_signal(x) for x in rows)}</ul>')


def _check(x: Dict) -> str:
    return (f'<li>{_pill(x.get("verdict"), VERDICT)} <b>{_e(x["claim"])}</b>'
            f'<div class="small">{_e(x["data"])}</div></li>')


def _call(x: Dict) -> str:
    return (f'<li>{_pill(x.get("result") or "未到期", RESULT)} {_e(x["claim"])}'
            + f'<div class="small muted">{_e(x.get("by"))} 前，看 {_e(x.get("measure"))}'
            + (f'：{_e(x["note"])}' if x.get("note") else "") + "</div></li>")


def _score(done: List[Dict]) -> str:
    if not done:
        return "過去的判斷還沒到驗證日，到期後會在這裡顯示對錯。"
    right = sum(c["result"] == "對" for c in done)
    tail = "；樣本還太少，先不下結論" if len(done) < MIN_SCORED else ""
    return f"過去到期的判斷 {len(done)} 筆，對 {right} 筆、錯 {len(done) - right} 筆{tail}。"


def sec_deep(eng) -> str:
    d = load()
    days = [x for x in (d.get("days") or []) if isinstance(x, dict) and x.get("date") and x.get("one")]
    if not days:
        return ""
    days.sort(key=lambda x: str(x["date"]), reverse=True)
    top = days[0]
    lens, checks = _rows(top.get("lens"), "name", "read"), _rows(top.get("checks"), "claim", "data")
    calls = [c for x in days for c in _rows(x.get("calls"), "claim")]
    done = [c for c in calls if c.get("result") in ("對", "錯")]
    open_ = [c for c in calls if c.get("result") not in ("對", "錯")]
    body = (f'<p class="rimp big2"><b>一句話看懂：{_e(top["one"])}</b></p><details class="sgx"><summary>看完整研判</summary>'
            + (f'<ul class="lines">{"".join(_lens(x) for x in lens)}</ul>' if lens else "")
            + _signals(_rows(top.get("signals"), "name", "read"))
            + (f'<p class="small"><b>連帶影響</b>：{_e(top["spill"])}</p>' if top.get("spill") else "")
            + (f'<details class="sgx"><summary>今天的說法查核（{len(checks)} 則）</summary><ul class="lines">'
               + "".join(_check(x) for x in checks) + "</ul></details>" if checks else "")
            + (f'<details class="sgx"><summary>可驗證的判斷（待驗證 {len(open_)} 筆）</summary>'
               f'<p class="small">{_e(_score(done))}</p><ul class="lines">'
               + "".join(_call(x) for x in open_[:8] + done[:12]) + "</ul></details>" if calls else "")
            + (f'<p class="small"><b>學到的教訓</b>：{_e(top["lesson"])}</p>' if top.get("lesson") else "")
            + (f'<p class="small muted">來源：{_src(top.get("sources"))}</p>' if top.get("sources") else "") + "</details>"
            + f'<p class="note">美股收盤後由雲端 AI 用公開資料整理，是對當天市場的解讀，不是股價預測；判斷都附驗證日，錯了也會留著。'
              f'分析日 {_e(top["date"])}，最後更新 {_e(d.get("updated"))}。不構成投資建議。</p>')
    return card("每日深度研判：拿掉情緒，只看數據", "Daily deep read: the data under the noise", body, "wide",
                sub="每個美股交易日收盤後更新")
