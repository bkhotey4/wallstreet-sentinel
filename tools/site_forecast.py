"""每日總經情勢 and 一個月預判 (top of 總覽).
- 每日總經情勢: the newest macro notes from research_feed/sessions.json, with a button that reads them aloud in the browser.
- 一個月預判: research_feed/forecast.json, written by a cloud routine twice a week: dated calls with a probability and a
  measure, each scored afterwards, plus what this season's reports say about next quarter.
Static content: the routine commits the JSON and the site shows it as written."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, List

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "forecast.json"   # public repo only
TREND = {"上修": "up", "下修": "dn"}

VOICE_JS = ("<script>(function(){var b=document.querySelector('.mvplay'),t=document.getElementById('mvtext');if(!b||!t)return;"
            "if(!('speechSynthesis' in window)){b.disabled=true;b.textContent='這個瀏覽器不支援朗讀';return;}"
            "var on=0,lab=b.textContent;function stop(){on=0;speechSynthesis.cancel();b.textContent=lab;}"
            "b.addEventListener('click',function(){if(on){stop();return;}speechSynthesis.cancel();"
            "var ps=t.textContent.split('。').filter(function(s){return s.trim();}),i=0,vs=speechSynthesis.getVoices();"
            "var v=vs.filter(function(x){return /zh[-_]TW/i.test(x.lang);})[0]||vs.filter(function(x){return /^zh/i.test(x.lang);})[0];"
            "on=1;b.textContent='■ 停止';function next(){if(!on)return;if(i>=ps.length){stop();return;}"
            "var u=new SpeechSynthesisUtterance(ps[i++]+'。');u.lang='zh-TW';if(v)u.voice=v;u.onend=next;u.onerror=stop;speechSynthesis.speak(u);}"
            "next();});})();</script>")


def _json(f: Path) -> Dict:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def load() -> Dict:
    return _json(FILE)


def _e(x) -> str:
    return html.escape(guard_safe(str(x or "")))


def _src(xs) -> str:
    out = []
    for s in xs or []:
        if not isinstance(s, dict):
            continue
        u = str(s.get("url") or "")
        name = _e(s.get("name") or "來源")
        out.append(f'<a href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">{name}</a>' if u.startswith("https://") else name)
    return "、".join(out)


def _latest_note() -> Dict:
    """The newest session note that carries macro readings: 盤後 before 盤中 before 盤前 within a day."""
    rank = {"盤前": 0, "盤中": 1, "盤後": 2}
    items = [x for x in (_json(FILE.with_name("sessions.json")).get("items") or []) if isinstance(x, dict) and x.get("date") and x.get("one") and x.get("macro")]
    return max(items, key=lambda x: (str(x["date"]), rank.get(x.get("phase"), -1)), default={})


def sec_macro_voice(eng) -> str:
    x = _latest_note()
    rows = [m for m in x.get("macro") or [] if isinstance(m, dict) and m.get("name") and m.get("read")]
    if not rows:
        return ""
    spoken = "。".join([f'{x["date"]} 的總經情勢', str(x["one"]).rstrip("。")] + [f'{m["name"]}：{str(m["read"]).rstrip("。")}' for m in rows]
                      + ([f'接下來看：{str(x["next"]).rstrip("。")}'] if x.get("next") else []) + [str(load().get("one") or "").rstrip("。")])
    body = (f'<p class="rimp big2"><b>一句話看懂：{_e(x["one"])}</b></p>'
            '<p><button class="btn mvplay" type="button">▶ 聽今天的總經</button></p>'
            f'<p id="mvtext" hidden>{_e(spoken)}</p>'
            + "<ul>" + "".join(f'<li><b>{_e(m["name"])}</b>：{_e(m["read"])}</li>' for m in rows) + "</ul>"
            + (f'<p class="small"><b>接下來看</b>：{_e(x["next"])}</p>' if x.get("next") else "") + VOICE_JS
            + f'<p class="note">整理自 {_e(x["date"])} {_e(x.get("phase"))}的美股快報，每個交易日更新。朗讀用你裝置內建的中文語音，聲音依手機或電腦而定。不構成投資建議。</p>')
    return card("每日總經情勢", "Daily macro", body, "wide", sub="可以用聽的")


def _rows(xs, *keys) -> List[Dict]:
    return [x for x in xs or [] if isinstance(x, dict) and all(x.get(k) for k in keys)]


def _call(x: Dict) -> str:
    res = str(x.get("result") or "")
    tag = f'<b class="{"up" if res == "對" else "dn"}">{_e(res)}</b> {_e(x.get("note"))}' if res else f'{_e(x.get("by"))} 對答案'
    extra = (f'<p class="small"><b>現在</b>：{_e(x["now"])}</p>' if x.get("now") else "") + (f'<p class="small"><b>為什麼</b>：{_e(x["why"])}</p>' if x.get("why") else "")
    extra += f'<p class="small"><b>怎樣算對</b>：{_e(x.get("measure"))}</p>' + (f'<p class="small"><b>可能錯在</b>：{_e(x["wrong"])}</p>' if x.get("wrong") else "")
    return (f'<div class="rpt"><h3>{_e(x["name"])} <span class="pill">我估 {_e(x.get("prob"))}%</span></h3><p>{_e(x["call"])}</p>'
            f'<p class="small muted">{tag}</p><details class="sgx"><summary>依據</summary>{extra}</details></div>')


def _score(xs: List[Dict]) -> str:
    done = [x for x in xs if x.get("result") in ("對", "錯")]
    if not done:
        return '<p class="small">還沒有到期的預判，第一批會在到期後對答案，錯了也會留在這裡。</p>'
    hit = sum(x["result"] == "對" for x in done)
    avg = sum(float(x.get("prob") or 0) for x in done) / len(done)
    return f'<p class="small"><b>過去成績</b>：{len(done)} 題對 {hit} 題（{hit / len(done) * 100:.0f}%），當時平均估 {avg:.0f}%。兩個數字越接近，代表機率估得越準。</p>'


def sec_forecast(eng) -> str:
    d = load()
    calls = _rows(d.get("calls"), "name", "call")
    if not calls:
        return ""
    live = [x for x in calls if not x.get("result")]
    paths = "".join(f'<li><b>{_e(p.get("name"))}（約 {_e(p.get("prob"))}%）</b>：{_e(p.get("what"))}</li>' for p in _rows(d.get("paths"), "name"))
    nq = _rows((d.get("nextq") or {}).get("groups"), "name", "read")
    nqh = "".join(f'<div class="rpt"><h3>{_e(g["name"])} <b class="{TREND.get(g.get("trend"), "")}">{_e(g.get("trend"))}</b></h3><p>{_e(g["read"])}</p>'
                  + (f'<p class="small muted">{_e(g["evidence"])}</p>' if g.get("evidence") else "") + "</div>" for g in nq)
    body = (f'<p class="rimp big2"><b>一句話看懂：{_e(d.get("one"))}</b></p>'
            + (f"<h3>接下來一個月的三種走法</h3><ul>{paths}</ul>" if paths else "")
            + "<h3>可以對答案的預判</h3>" + _score(calls) + "".join(_call(x) for x in live)
            + (f'<h3>從財報看下一季</h3><p>{_e((d.get("nextq") or {}).get("one"))}</p>{nqh}' if nq else "")
            + (f'<p class="small muted">來源：{_src(d.get("sources"))}</p>' if d.get("sources") else "")
            + f'<p class="note">機率是 AI 的主觀判斷，不是模型算出的保證。{_e(d.get("updated"))} 更新，每週兩次，到期後公開對答案。不構成投資建議。</p>')
    return card("一個月後的總經，與財報裡的下一季", "One month ahead", body, "wide", sub="有機率、有到期日，到期公開對答案")
