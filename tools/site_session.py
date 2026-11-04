"""Is this market trading today?  Shared browser code for the live cards (開盤後即時盤勢, 台股即時盤勢).

No holiday list: the answer comes from the data.  mktState compares the exchange-local date of the newest quote time (`t`
from /api/quote) with today's exchange-local date.  A quote from an earlier day after the open plus MKT_WAIT minutes means
the exchange did not trade today.  Before the open a holiday cannot be told apart from an ordinary morning, so that stays
"not open yet"; the wait covers the first minutes of a normal day, when delayed quotes still carry yesterday's time.
Pass several symbols' `t`: one lagging symbol must not read as a closed market.

st: 'open' in session | 'pre' before the open | 'wait' just opened, no quote of today yet | 'post' closed for the day |
'closed' no session today (weekend or holiday)."""
from __future__ import annotations

WAIT_MIN = 30

MKT_JS = r"""
 var MKT_WAIT=__WAIT__;
 function mdParts(s,tz){var o={};new Intl.DateTimeFormat('en-US',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit',weekday:'short',hour:'2-digit',minute:'2-digit',hour12:false})
   .formatToParts(new Date(s*1000)).forEach(function(x){o[x.type]=x.value;});var h=+o.hour%24;
   return {date:o.year+'-'+o.month+'-'+o.day,md:o.month+'-'+o.day,wd:o.weekday,m:h*60+(+o.minute),hm:('0'+h).slice(-2)+':'+o.minute};}
 function mktState(ts,tz,open,close){var n=mdParts(Date.now()/1000,tz),t=Math.max.apply(null,ts.filter(Boolean).concat([0])),q=t?mdParts(t,tz):null,
   wk=n.wd==='Sat'||n.wd==='Sun',stale=!!q&&q.date!==n.date,
   st=wk?'closed':stale?(n.m<open?'pre':n.m<open+MKT_WAIT?'wait':'closed'):n.m<open?'pre':n.m<close?'open':'post';
   return {st:st,stale:stale,t:t,date:q?q.date:'',day:q?q.md:'',hm:q?q.hm:''};}
 function mktNote(S,nm){var last='以下是最近一個交易日'+(S.day?'（'+S.day+'）':'');
   return S.st==='closed'?'今天'+nm+'休市，'+last:S.st==='pre'?nm+'尚未開盤，'+last:S.st==='wait'?nm+'剛開盤，今天的報價還沒進來，'+last:S.st==='post'?nm+'已收盤，'+last:'';}
 function mktPast(s){return String(s).replace(/今天|今日/g,'當天').replace(/昨天/g,'前一個交易日');}
""".replace("__WAIT__", str(WAIT_MIN))
