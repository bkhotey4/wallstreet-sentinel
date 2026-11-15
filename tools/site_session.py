"""Is this market trading today?  Shared browser code for the live cards (開盤後即時盤勢, 台股即時盤勢).

No holiday list: the answer comes from the data.  mktState compares the exchange-local date of the newest quote time (`t`
from /api/quote) with today's exchange-local date.  A quote from an earlier day after the open plus MKT_WAIT minutes means
the exchange did not trade today.  Before the open a holiday cannot be told apart from an ordinary morning, so that stays
"not open yet" — except on the NYSE holidays and early closes passed in MKT_CAL (computed from python-holidays and the
exchange's half-day rules at build time; `us_calendar`).  The wait covers the first minutes of a normal day, when delayed quotes still carry yesterday's time.
Pass several symbols' `t`: one lagging symbol must not read as a closed market.

st: 'open' in session | 'pre' before the open | 'wait' just opened, no quote of today yet | 'post' closed for the day |
'closed' no session today (weekend or holiday)."""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Dict, Optional

WAIT_MIN = 30
EARLY_CLOSE = 13 * 60                 # NYSE half days close at 13:00 New York time


def us_calendar(today: Optional[date] = None, days: int = 400) -> Dict:
    """NYSE full holidays and early closes over the next `days` (rules in wsb/data/exchange_cal.py, shared with the
    休市與提早收盤 card since 2026-11-16)."""
    from wsb.data import exchange_cal as XC
    today = today or date.today()
    end = today + timedelta(days=days)
    hol = XC.us_holidays(today.year, end.year)
    early = XC.us_early(today.year, end.year, hol)
    lo, hi = (today - timedelta(days=1)).isoformat(), end.isoformat()
    return {"hol": sorted(k for k in hol if lo <= k <= hi), "early": {k: EARLY_CLOSE for k in sorted(early) if lo <= k <= hi}}

MKT_JS = r"""
 var MKT_WAIT=__WAIT__,MKT_CAL=__CAL__;
 function mdParts(s,tz){var o={};new Intl.DateTimeFormat('en-US',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit',weekday:'short',hour:'2-digit',minute:'2-digit',hour12:false})
   .formatToParts(new Date(s*1000)).forEach(function(x){o[x.type]=x.value;});var h=+o.hour%24;
   return {date:o.year+'-'+o.month+'-'+o.day,md:o.month+'-'+o.day,wd:o.weekday,m:h*60+(+o.minute),hm:('0'+h).slice(-2)+':'+o.minute};}
 function mktState(ts,tz,open,close){var n=mdParts(Date.now()/1000,tz),t=Math.max.apply(null,ts.filter(Boolean).concat([0])),q=t?mdParts(t,tz):null,
   C=MKT_CAL[tz]||{},hol=(C.hol||[]).indexOf(n.date)>=0,ec=(C.early||{})[n.date];if(ec)close=Math.min(close,ec);
   var wk=n.wd==='Sat'||n.wd==='Sun'||hol,stale=!!q&&q.date!==n.date,
   st=wk?'closed':stale?(n.m<open?'pre':n.m<open+MKT_WAIT?'wait':'closed'):n.m<open?'pre':n.m<close?'open':'post';
   return {st:st,stale:stale,hol:hol,early:!!ec,t:t,date:q?q.date:'',day:q?q.md:'',hm:q?q.hm:''};}
 function mktNote(S,nm){var last='以下是最近一個交易日'+(S.day?'（'+S.day+'）':'');
   return S.st==='closed'?'今天'+nm+'休市，'+last:S.st==='pre'?nm+'尚未開盤，'+last:S.st==='wait'?nm+'剛開盤，今天的報價還沒進來，'+last:S.st==='post'?nm+(S.early?'今天提早在 13:00 收盤（節日前半天），':'已收盤，')+last:S.st==='open'&&S.early?nm+'今天只開半天，13:00 收盤':'';}
 function mktPast(s){return String(s).replace(/今天|今日/g,'當天').replace(/昨天/g,'前一個交易日');}
""".replace("__WAIT__", str(WAIT_MIN)).replace("__CAL__", json.dumps({"America/New_York": us_calendar()}))
