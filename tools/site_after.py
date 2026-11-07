"""財報後白話解讀 (top of 財經日曆, and the US ones on 美股財報): after US / Taiwan / Hong Kong companies report, a cloud
routine writes research_feed/earn_after.json — for every company of any sector that reported (US market cap ≥ 200 億美元,
the site's Taiwan top-150 and Hong Kong top-100 lists), a plain sentence,
what the numbers say beyond "beat / miss", who else is affected (suppliers, rivals, customers, Taiwan supply chain), the
macro / bond backdrop it lands in, and the after-hours move explained only with news that matches it.  Not advice.
research_feed/earn_after_more / _asia / _rest.json hold the backfilled reports of the season; 財報解讀總表 searches both files."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "earn_after.json"   # public repo only
TECH = ("科技", "半導體", "通訊", "軟體", "雲端", "AI")
MK = {"us": "美股", "tw": "台股", "hk": "港股"}


def load() -> Dict:
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _esc(x) -> str:
    return html.escape(guard_safe(str(x or "")))     # banned words are reworded by guard_safe (sitekit)


def load_all() -> Dict:
    """Newest `updated` across the daily file and the backfill files, for the 財報解讀總表 stamp."""
    stamps = []
    for name in ("earn_after.json", "earn_after_more.json", "earn_after_asia.json", "earn_after_rest.json"):
        try:
            stamps.append(str(json.loads(FILE.with_name(name).read_text(encoding="utf-8")).get("updated") or ""))
        except (OSError, ValueError):
            continue
    return {"updated": max(stamps, default="")}


def _rows(f: Path) -> List[Dict]:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return (d.get("items") or []) if isinstance(d, dict) else []


def _list(xs) -> str:
    return "".join(f"<li>{_esc(x)}</li>" for x in (xs or []) if x and isinstance(x, str))


def _item(it: Dict) -> str:
    mv = it.get("move") if isinstance(it.get("move"), dict) else {}
    pct = mv.get("pct")
    cl = "up" if isinstance(pct, (int, float)) and pct > 0 else "dn" if isinstance(pct, (int, float)) and pct < 0 else ""
    head = (f'<h3>{_esc(it.get("name") or it.get("sym"))} <span class="muted small">{_esc(it.get("sym"))}・{_esc(it.get("sector"))}・'
            f'{_esc(it.get("date"))}・{MK.get(it.get("mk") or "us", "美股")}</span>' + (f' <b class="{cl}">{pct:+.1f}%</b>' if isinstance(pct, (int, float)) else "") + "</h3>")
    spill = "".join(f'<li><b>{_esc(s.get("who"))}</b>：{_esc(s.get("how"))}</li>' for s in (it.get("spill") or []) if isinstance(s, dict))
    src = _list(it.get("sources"))
    parts = [f'<p class="rimp"><b>{_esc(it.get("one"))}</b></p>']
    if mv.get("why"):
        parts.append(f'<p class="small">股價反應：{_esc(mv.get("why"))}</p>')
    tr = it.get("trend") if isinstance(it.get("trend"), dict) else {}
    if tr.get("label"):
        c = {"改善中": "up", "轉弱中": "dn"}.get(tr["label"], "")
        parts.append(f'<p class="small"><b class="{c}">本業走向：{_esc(tr["label"])}</b>'
                     + (f'——{_esc(tr.get("why"))}' if tr.get("why") else "") + "</p>")
    det = ""
    if tr.get("outlook") or tr.get("next"):
        det += ("<h4>接下來（公司財測與要看的事）</h4><ul>" + (f'<li>{_esc(tr["outlook"])}</li>' if tr.get("outlook") else "")
                + (f'<li>下次財報看：{_esc(tr["next"])}</li>' if tr.get("next") else "") + "</ul>")
    if it.get("company"):
        det += f"<h4>公司本身（不只看有沒有賺錢）</h4><ul>{_list(it.get('company'))}</ul>"
    if spill:
        det += f"<h4>連帶影響</h4><ul>{spill}</ul>"
    if it.get("macro"):
        det += f"<h4>大環境（總經、利率、信用、其他財報）</h4><ul>{_list(it.get('macro'))}</ul>"
    if src:
        det += f'<h4>來源</h4><ul class="small">{src}</ul>'
    if det:
        parts.append(f'<details class="sgx"><summary>展開：公司、走向、連帶影響、大環境</summary>{det}</details>')
    return f'<div class="rpt">{head}{"".join(parts)}</div>'


def _items(tech_only: bool = False) -> List[Dict]:
    seen = {}
    for x in _rows(FILE) + _rows(FILE.with_name("earn_after_more.json")) + _rows(FILE.with_name("earn_after_asia.json")) + _rows(FILE.with_name("earn_after_rest.json")):     # the daily file wins
        if isinstance(x, dict) and x.get("sym") and x.get("date") and x.get("one"):
            seen.setdefault((str(x["sym"]), str(x["date"])), x)
    items = list(seen.values())
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
    note = ("每天台北早上 7 點與晚上 9 點，由 AI 分析任務讀取公司官方財報新聞稿、公開資訊觀測站、港交所公告與可靠報導，替前一段時間公布財報的公司"
            "（美股市值 200 億美元以上、台股市值前 150 大、港股成交額前 100 大，所有產業，不只科技）寫白話解讀：除了有沒有賺錢，還看營收品質、利潤率、財測、現金流，對供應商／競爭對手／客戶／台灣供應鏈的連帶影響，"
            "以及當時的總經、利率、信用環境。股價反應只用時間對得上的新聞解釋。這是解讀，不是投資建議。")
    body = (f'<p class="rimp big2"><b>{_esc(lead)}</b></p>'
            + (f'<p class="small"><b>大環境：</b>{_esc(bg)}</p>' if bg else "")
            + "".join(_item(x) for x in items[:n])
            + f'<p class="note">{note}{"　更新 " + _esc(d.get("updated")) if d.get("updated") else ""}</p>')
    return card(title, en, body, "wide")


def sec_earn_after(eng) -> str:
    return _card(_items(), "財報後白話解讀（美股／台股／港股）", "After the report: plain-language reads (US / Taiwan / HK)", 12)


def sec_earn_after_us(eng) -> str:
    """美股財報 tab: every US report the routine read (any sector); items without mk are US (older data)."""
    return _card([x for x in _items() if (x.get("mk") or "us") == "us"], "財報後白話解讀（美股）", "After the report: US", 6)


def _rpt(x: Dict) -> str:
    key = " ".join(str(x.get(k) or "") for k in ("sym", "name", "sector")) + " " + MK.get(x.get("mk") or "us", "美股")
    return _item(x).replace('<div class="rpt">', f'<div class="rpt" data-q="{_esc(key.lower())}">', 1)


def publish(dest: Path) -> None:
    """market/earn_all.html: every read grouped by date, loaded only when 財報解讀總表 is opened (keeps the main page small)."""
    days = {}
    for x in _items():
        days.setdefault(str(x["date"]), []).append(x)
    (dest / "earn_all.html").write_text(
        "".join(f'<details class="sgx eaday"><summary>{_esc(d)}（{len(xs)} 家）</summary>{"".join(_rpt(x) for x in xs)}</details>'
                for d, xs in sorted(days.items(), reverse=True)), encoding="utf-8")


ALL_JS = ("<script>(function(){var q=document.querySelector('.eaq'),b=document.getElementById('eaall');if(!q||!b)return;var st=0;"
          "function f(){var v=q.value.trim().toLowerCase();b.querySelectorAll('.eaday').forEach(function(d){var n=0;"
          "d.querySelectorAll('.rpt').forEach(function(r){var m=!v||r.dataset.q.indexOf(v)>=0;r.style.display=m?'':'none';if(m)n++;});"
          "d.style.display=n?'':'none';d.open=!!v&&n>0;});}"
          "function go(){if(st)return;st=1;b.textContent='載入中…';fetch(b.dataset.src).then(function(r){if(!r.ok)throw 0;return r.text();})"
          ".then(function(t){b.innerHTML=t;f();}).catch(function(){st=0;b.textContent='載入失敗，請重新整理頁面。';});}"
          "q.addEventListener('focus',go);q.addEventListener('input',function(){go();f();});"
          "var o=document.querySelector('.eaopen');if(o)o.addEventListener('click',go);})();</script>")


def sec_earn_all(eng) -> str:
    items = _items()
    if not items:
        return ""
    n = {k: sum((x.get("mk") or "us") == k for x in items) for k in MK}
    body = (f'<p class="rimp big2"><b>一句話看懂：這裡查得到這一季寫過的 {len(items)} 份財報判讀，輸入代號或公司名就能找。</b></p>'
            f'<p class="small">美股 {n["us"]} 份、台股 {n["tw"]} 份、港股 {n["hk"]} 份。範圍是美股市值 20 億美元以上，以及台股、港股全部上市公司，還在陸續補寫。小公司是精簡版，查不到的項目會寫查無。</p>'
            '<p><input class="eaq" type="search" placeholder="輸入代號或名稱，例如 KLAC、台積電、核能" aria-label="搜尋財報判讀"> '
            '<button class="btn eaopen" type="button">顯示全部</button></p>'
            '<div id="eaall" data-src="market/earn_all.html"></div>' + ALL_JS
            + '<p class="note">這是解讀，不是投資建議。</p>')
    return card("財報解讀總表", "All earnings reads", body, "wide", sub="依日期整理，可搜尋")
