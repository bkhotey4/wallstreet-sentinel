"""美股時段快報 (top of 總覽): before the open, mid-session and after the close a cloud routine writes
research_feed/sessions.json in plain words: what happened, why, what it means for the economy, what to watch.
Static content: the routine commits the JSON and the site shows the newest day as written."""
from __future__ import annotations

import html
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from tools.sitekit import card, guard_safe

FILE = Path(__file__).resolve().parents[1] / "research_feed" / "sessions.json"   # public repo only
PHASES = ("盤前", "盤中", "盤後")
FIRST_RUN_UTC = 13                    # the routine's first run of a US trading day (cron 0 13,15,17,19,21,22 * * 1-5 UTC) = 21:00 Taipei
WD = "一二三四五六日"


def next_update(now: Optional[datetime] = None) -> datetime:
    """Next first-of-day run: a weekday that is not an NYSE holiday, at FIRST_RUN_UTC."""
    from tools.site_session import us_calendar
    now = now or datetime.now(timezone.utc)
    hol = set(us_calendar(now.date()).get("hol") or [])
    d = now.date() if now.hour < FIRST_RUN_UTC else now.date() + timedelta(days=1)
    while d.weekday() >= 5 or d.isoformat() in hol:
        d += timedelta(days=1)
    return datetime(d.year, d.month, d.day, FIRST_RUN_UTC, tzinfo=timezone.utc)


def stale_note(day: str, now: Optional[datetime] = None) -> str:
    """When the newest report is from an earlier US date (weekend, holiday, before today's first run), say so."""
    now = now or datetime.now(timezone.utc)
    ny_today = (now - timedelta(hours=5)).date()          # close enough for a date label; the run time below is exact
    try:
        d = date.fromisoformat(day)
    except ValueError:
        return ""
    if d >= ny_today:
        return ""
    nx = next_update(now) + timedelta(hours=8)            # Taipei
    from tools.site_session import us_calendar
    hol = ny_today.isoformat() in set(us_calendar(ny_today).get("hol") or [])
    why = "週末美股休市" if ny_today.weekday() >= 5 else "今天美股休市（節日）" if hol else "今天的第一次更新還沒到"
    return (f'<p class="small muted">⏸ {why}：下面是 {d.month}/{d.day}（週{WD[d.weekday()]}）的內容。'
            f'下一次更新：台北 {nx.month}/{nx.day}（週{WD[nx.weekday()]}）{nx:%H:%M}（美股開盤前）。</p>')


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
        name = _e(s.get("name") or "來源")
        out.append(f'<a href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">{name}</a>' if u.startswith("https://") else name)
    return "、".join(out)


def _mover(m: Dict) -> str:
    try:
        pct = f'{float(m["chg"]):+.1f}%'
    except (KeyError, TypeError, ValueError):
        pct = ""
    return f'<li><b>{_e(m.get("name") or m.get("sym"))}</b>（{_e(m.get("sym"))}）{pct}：{_e(m.get("why"))}</li>'


STEPS = ("發生什麼", "最先動的", "怎麼傳下去", "影響到誰")


def chain(x: Dict) -> str:
    """The causal chain the routine writes (CAUSAL_GUIDE.md): event → first mover → spread → who is hit, as arrows."""
    cs = [c for c in (x.get("chain") or []) if isinstance(c, dict) and c.get("text")][:4]
    if len(cs) < 2:
        return ""
    cells = []
    for i, c in enumerate(cs):
        meta = " ".join(_e(v) for v in (c.get("time"), c.get("src")) if v)
        cells.append(f'<div class="cch"><span class="cst">{_e(c.get("step") or STEPS[min(i, 3)])}</span>{_e(c["text"])}'
                     + (f'<span class="cmt">{meta}</span>' if meta else "") + "</div>")
    return '<div class="cchain">' + '<span class="car">→</span>'.join(cells) + "</div>"


CSS = (".cchain{display:flex;flex-wrap:wrap;align-items:stretch;gap:6px;margin:6px 0 10px}"
       ".cch{flex:1 1 150px;min-width:0;border:1px solid var(--bd);border-radius:8px;padding:6px 8px;background:var(--card2);font-size:13px;line-height:1.45}"
       ".cst{display:block;font-size:11px;color:var(--ac);font-weight:700;margin-bottom:2px}.cmt{display:block;font-size:11px;color:var(--mu);margin-top:3px}"
       ".car{align-self:center;color:var(--mu);font-weight:700}@media(max-width:620px){.car{transform:rotate(90deg);width:100%;text-align:center}}")


def _item(x: Dict, lead: bool = False) -> str:
    told = "".join(f"<p>{_e(p)}</p>" for p in x.get("story") or [] if p)
    macro = "".join(f'<li><b>{_e(m.get("name"))}</b>：{_e(m.get("read"))}</li>' for m in x.get("macro") or []
                    if isinstance(m, dict) and m.get("name") and m.get("read"))
    movers = "".join(_mover(m) for m in x.get("movers") or [] if isinstance(m, dict) and m.get("sym") and m.get("why"))
    more = (told + (f'<p class="small"><b>今天誰動得最大、為什麼</b></p><ul class="small">{movers}</ul>' if movers else "")
            + (f'<p class="small"><b>總經情勢</b></p><ul class="small">{macro}</ul>' if macro else "")
            + (f'<p class="small muted">來源：{_src(x.get("sources"))}</p>' if x.get("sources") else ""))
    return (f'<div class="rpt"><h3>{_e(x.get("phase"))} <span class="muted small">{_e(x.get("at"))} 台北</span></h3>'
            + ("" if lead else f'<p><b>{_e(x.get("one"))}</b></p>')
            + (f'<p class="small"><b>接下來看</b>：{_e(x["next"])}</p>' if x.get("next") else "")
            + (f'<details class="sgx"><summary>看完整解讀：誰動得最大、為什麼</summary>{more}</details>' if more else "") + "</div>")


SPLIT_SYMS = ("^GSPC", "^NDX", "^SOX", "RSP", "IWM", "^VIX")


def split_box(eng) -> str:
    """The live line on top of 美股今天怎麼了 (2026-11-16, user: 「做1」): what fell today — the whole market, chips only, or
    the heavyweights — read every minute from /api/quote by SPLIT_JS.  The one-year highs come from the build's daily closes so
    the browser can say how far each index is from its high.  Public prices only, nothing about anyone's holdings."""
    import json
    hi = {}
    for sym in ("^GSPC", "^SOX"):
        try:
            v = eng.market.series(sym).dropna()
            if len(v) > 200:
                hi[sym] = round(float(v.iloc[-252:].max()), 2)
        except Exception:  # noqa: BLE001
            pass
    from html import escape
    return (f'<div class="split" data-hi="{escape(json.dumps(hi))}" hidden><p class="rimp"><b>今天跌（漲）的是哪一塊：</b><span class="splt"></span></p>'
            '<p class="small muted splm"></p></div>')


SPLIT_JS = r"""
(function(){var box=document.querySelector('.split');if(!box)return;var hi={};try{hi=JSON.parse(box.dataset.hi||'{}');}catch(e){}
 var S=['^GSPC','^NDX','^SOX','RSP','IWM','^VIX'];
 function f(x){return (x>=0?'+':'')+x.toFixed(1)+'%';}
 function run(){fetch('api/quote?s='+encodeURIComponent(S.join(',')),{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(j){
  var q=j.q||{},g=function(s){var x=q[s]||{};return typeof x.chg==='number'?x:null;};
  var sp=g('^GSPC'),nd=g('^NDX'),sox=g('^SOX'),rsp=g('RSP'),iwm=g('IWM'),vix=g('^VIX');if(!sp||!sox)return;
  var d=sox.chg-sp.chg,b=rsp?rsp.chg-sp.chg:0,parts=[];
  if(d<=-2)parts.push('主要是晶片股：費城半導體 '+f(sox.chg)+'，標普 500 只 '+f(sp.chg)+'，不是整個市場一起崩');
  else if(d>=2)parts.push('晶片股領頭：費城半導體 '+f(sox.chg)+'，標普 500 '+f(sp.chg));
  else parts.push('大盤和晶片股差不多：標普 500 '+f(sp.chg)+'、費城半導體 '+f(sox.chg));
  if(rsp&&b<=-1)parts.push('多數股票比大盤更弱（等權重 '+f(rsp.chg)+'），跌得很廣');
  else if(rsp&&b>=1)parts.push('多數股票其實比大盤好（等權重 '+f(rsp.chg)+'），是少數大型股在拖');
  if(nd)parts.push('那斯達克 100 '+f(nd.chg)+(iwm?'、小型股 '+f(iwm.chg):''));
  if(vix){var w=vix.price>=30?'恐慌':vix.price>=20?'擔心，但還不到恐慌':'平靜';parts.push('恐慌指數 VIX '+vix.price.toFixed(1)+'（'+w+'）');}
  var m=[];['^GSPC','^SOX'].forEach(function(s){var x=g(s);if(x&&hi[s]&&x.price)m.push((s==='^GSPC'?'標普 500':'費城半導體')+' 離一年高點 '+f((x.price/hi[s]-1)*100));});
  var t=sp.t?new Date(sp.t*1000):null,old=t&&(Date.now()/1000-sp.t>20*3600);
  box.querySelector('.splt').textContent=parts.join('；')+'。';
  box.querySelector('.splm').textContent=m.join('、')+(t?'。報價時間 '+t.toLocaleString('zh-TW',{timeZone:'Asia/Taipei',hour12:false,month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'})+(old?'（最近一個交易日）':''):'')
   +'。規則：晶片比大盤多跌或多漲 2 個百分點以上、等權重和大盤差 1 個百分點以上才特別說；VIX 20 以上算擔心、30 以上算恐慌。';
  box.hidden=false;}).catch(function(){});}
 run();setInterval(run,60000);})();
"""


def sec_sessions(eng) -> str:
    d = load()
    items = [x for x in (d.get("items") or []) if isinstance(x, dict) and x.get("date") and x.get("one") and x.get("phase") in PHASES]
    if not items:
        return ""
    day = max(str(x["date"]) for x in items)
    today = {x["phase"]: x for x in items if str(x["date"]) == day}
    shown = [today[p] for p in reversed(PHASES) if p in today]
    return card("美股今天怎麼了", "US stocks today", stale_note(day) + split_box(eng) + f'<p class="rimp big2"><b>一句話看懂：{_e(shown[0]["one"])}</b></p>' + chain(shown[0])
                + "".join(_item(x, i == 0) for i, x in enumerate(shown))
                + f'<p class="note">美股開盤前、盤中、收盤後由雲端 AI 用公開資料整理，交易日 {_e(day)}。是對當下的解讀，不是股價預測。不構成投資建議。</p>',
                "wide", sub="開盤前、盤中、收盤後各更新一次")
