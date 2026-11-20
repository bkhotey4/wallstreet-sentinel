"""今晚大事看板（總覽＋新聞日曆，2026-11-20）：research_feed/event_board.json 列出大事件——時間、要看的代號與參考價位、
事前列出的往上／往下力量與當時的機率、要盯什麼、事後結果。網頁每 45 秒用 /api/quote 填入現價和離參考價位多遠。
起因：11-19 Anthropic 上市當晚，使用者一直要在對話裡問「ANT 現在呢」，而事前分析只寫在對話、網站上沒有。
沒有 JavaScript 時也會照 JSON 印出靜態內容。"""
from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "event_board.json"   # public repo only
TPE = timezone(timedelta(hours=8))
KEEP_DONE_DAYS = 3                       # finished events stay this long, then drop off the board
POLL_S = 45
LIVE_MAX_H = 8                           # a US session is 6.5 h, a Taiwan one 4.5 h: after this a "live" event is over
STATUS = {"live": ("進行中", "dn"), "upcoming": ("即將發生", ""), "done": ("已結束", "muted"),
          "stale": ("已結束，結果待補", "muted")}


def load(path: Optional[Path] = None) -> Dict:
    try:
        d = json.loads((path or FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def _e(x) -> str:
    return html.escape(guard_safe(str(x if x is not None else "")))


def _when(ev: Dict) -> Optional[datetime]:
    try:
        return datetime.strptime(str(ev.get("when_tpe") or "")[:16], "%Y-%m-%d %H:%M").replace(tzinfo=TPE)
    except ValueError:
        return None


def status_of(ev: Dict, now: datetime) -> str:
    """The status the page shows. The file's "live" is typed by hand during the event and nobody is awake to change it at
    the close (11-20: Anthropic's first day still said 進行中 twenty hours later), so the clock ends it: LIVE_MAX_H after
    the start a "live" event is "stale" = finished, result not written yet."""
    st = ev.get("status") or "upcoming"
    w = _when(ev)
    if st == "live" and w and now - w > timedelta(hours=LIVE_MAX_H):
        return "stale"
    return st if st in STATUS else "upcoming"


def pick(events: List[Dict], now: datetime) -> List[Dict]:
    """live first, then upcoming by time, then recently finished; drop finished events older than KEEP_DONE_DAYS."""
    out = []
    for ev in events or []:
        if not isinstance(ev, dict) or not ev.get("name"):
            continue
        w = _when(ev)
        if status_of(ev, now) in ("done", "stale") and w and now - w > timedelta(days=KEEP_DONE_DAYS):
            continue
        out.append(ev)
    rank = {"live": 0, "upcoming": 1, "stale": 2, "done": 2}
    far = datetime(2100, 1, 1, tzinfo=TPE)
    return sorted(out, key=lambda e: (rank[status_of(e, now)], _when(e) or far))


def _syms(ev: Dict) -> str:
    rows = []
    for s in ev.get("symbols") or []:
        if not isinstance(s, dict) or not s.get("s"):
            continue
        ref = s.get("ref")
        rows.append(f'<tr class="evrow" data-evsym="{_e(s["s"])}"' + (f' data-evref="{float(ref)}"' if isinstance(ref, (int, float)) else "") + ">"
                    f'<td><b>{_e(s.get("label") or s["s"])}</b> <span class="tk">{_e(s["s"])}</span></td>'
                    f'<td class="r">{_e(s.get("ref_label") or "")} {"" if ref is None else _e(ref)}</td>'
                    f'<td class="r evpx">—</td><td class="r evchg">—</td><td class="r evvs">—</td><td class="small muted">{_e(s.get("note") or "")}</td></tr>')
    if not rows:
        return ""
    return ('<div class="scroll"><table class="mini evt"><thead><tr><th>看什麼</th><th class="r">參考價位</th><th class="r">現價</th>'
            '<th class="r">今日</th><th class="r">離參考價位</th><th>為什麼看</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def _list(title: str, xs) -> str:
    xs = [x for x in xs or [] if x]
    return f'<p class="small"><b>{_e(title)}</b></p><ul class="small">' + "".join(f"<li>{_e(x)}</li>" for x in xs) + "</ul>" if xs else ""


def _event(ev: Dict, now: Optional[datetime] = None) -> str:
    key = status_of(ev, now or datetime.now(TPE))
    st, tone = STATUS[key]
    b = ev.get("before") or {}
    a = ev.get("after") or {}
    pre = (_list("事前列出的往上力量", b.get("up")) + _list("事前列出的往下力量", b.get("down"))
           + (f'<p class="small"><b>事前的機率</b>：{_e(b["odds"])}</p>' if b.get("odds") else "")
           + _list("要盯什麼", b.get("watch")))
    if not pre:
        pre = '<p class="small muted">待事前分析：事件前一天會寫上往上／往下的力量、機率與要盯的數字。</p>'
    now = (_list("實際發生什麼（記錄）", ev.get("facts"))
           + (f'<p class="small"><b>結果</b>：{_e(a["result"])}</p>' if a.get("result") else "")
           + (f'<p class="small"><b>事前對了／錯了什麼</b>：{_e(a["lesson"])}</p>' if a.get("lesson") else ""))
    src = "、".join(f'<a href="{_e(s["url"])}" target="_blank" rel="noopener noreferrer">{_e(s.get("name") or "來源")}</a>'
                   if str(s.get("url") or "").startswith("https://") else _e(s.get("name") or "")
                   for s in ev.get("sources") or [] if isinstance(s, dict))
    return (f'<div class="evb"><h3><span class="pill {tone}">{st}</span> {_e(ev["name"])} '
            f'<span class="small muted">台北 {_e(ev.get("when_tpe") or "時間待定")}</span></h3>'
            + (f'<p class="small">{_e(ev["one"])}</p>' if ev.get("one") else "")
            + _syms(ev)
            + f'<details class="sgx"{" open" if key == "live" else ""}><summary>事前怎麼看 vs 現在發生什麼</summary>{pre}{now}'
            + (f'<p class="small muted">來源：{src}</p>' if src else "") + "</details></div>")


def render(d: Dict, now: Optional[datetime] = None) -> str:
    now = now or datetime.now(TPE)
    evs = pick(d.get("events") or [], now)
    if not evs:
        return ""
    top = evs[0]
    lead = top.get("one") or f'{top["name"]}（台北 {top.get("when_tpe") or "時間待定"}）'
    body = (f'<p class="rimp big2"><b>一句話看懂：{_e(lead)}</b></p>'
            + "".join(_event(e, now) for e in evs[:2])
            + (f'<details class="sgx"><summary>接下來還有 {len(evs) - 2} 件大事</summary>' + "".join(_event(e, now) for e in evs[2:]) + "</details>" if len(evs) > 2 else "")
            + f'<p class="note">現價每 {POLL_S} 秒從本站報價服務更新（Yahoo Finance，約有延遲）；「離參考價位」＝現價比參考價位高或低多少。'
              f'事前分析與機率是寫在事件之前的解讀，不是預測保證，對錯都會留著。看板最後更新 {_e(d.get("updated") or "—")}。'
              f'<span class="evstamp"></span>不構成投資建議。</p>')
    return card("今晚大事看板：事前怎麼看、現在發生什麼", "Event board", body, "wide")


def sec_event_board(eng) -> str:
    return render(load())


CSS = (".evb{margin:8px 0 10px;padding:8px 10px;border:1px solid var(--bd);border-radius:10px}.evb h3{margin:2px 0 6px}"
       ".evt td,.evt th{white-space:nowrap}.evt .up{color:var(--up)}.evt .dn{color:var(--dn)}")

_JS = r"""
(function(){var rows=document.querySelectorAll('.evrow');if(!rows.length)return;var POLL=__POLL__*1000;
 function f(x,d){return x==null||!isFinite(x)?'—':Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
 function sg(x,d){return x==null||!isFinite(x)?'—':(x>0?'+':'')+f(x,d);}
 function hm(t){return t?new Intl.DateTimeFormat('zh-TW',{timeZone:'Asia/Taipei',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(t*1000)):'';}
 function pull(){if(document.hidden)return;var s={};rows.forEach(function(r){s[r.getAttribute('data-evsym')]=1;});var list=Object.keys(s).slice(0,25);
  fetch('api/quote?s='+encodeURIComponent(list.join(',')),{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(d){var q=d.q||{},ts=0;
   rows.forEach(function(r){var x=q[r.getAttribute('data-evsym')];if(!x||!x.price)return;if(x.t>ts)ts=x.t;
    r.querySelector('.evpx').textContent=f(x.price,2);var c=r.querySelector('.evchg');c.textContent=sg(x.chg,2)+'%';c.className='r evchg '+(x.chg>0?'up':x.chg<0?'dn':'');
    var ref=parseFloat(r.getAttribute('data-evref')),v=r.querySelector('.evvs');if(isFinite(ref)&&ref>0){var g=(x.price/ref-1)*100;v.textContent=(g>=0?'🟢 ':'🔴 ')+sg(g,1)+'%';v.className='r evvs '+(g>=0?'up':'dn');}});
   document.querySelectorAll('.evstamp').forEach(function(e){e.textContent='報價時間：台北 '+hm(ts)+'。';});}).catch(function(){});}
 setTimeout(pull,900);setInterval(pull,POLL);
})();
"""
JS = _JS.replace("__POLL__", str(POLL_S))
