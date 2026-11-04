"""Three calendar bugs from the 2026-11-04 audit: live cards on a market holiday (the browser code runs under node with a
frozen clock and fake quotes, so no holiday list is involved), the US pre-open briefing in summer and winter, and the
holdings day figure per market.  Run: python -m tests.test_market_holiday"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_hol_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_intraday as SI  # noqa: E402
from tools import site_live as SL  # noqa: E402
from tools import site_twlive as TL  # noqa: E402

NODE = shutil.which("node")
NY, TPE = ZoneInfo("America/New_York"), ZoneInfo("Asia/Taipei")


def unix(y, mo, d, h, mi, tz):
    return datetime(y, mo, d, h, mi, tzinfo=tz).timestamp()


HARNESS = r"""
const NOW = __NOW__, Q = __Q__, BOX = __BOX__;
const R = Date;
globalThis.Date = class extends R { constructor(...a) { if (a.length) super(...a); else super(NOW); } static now() { return NOW; } };
const els = {};
const mk = (id) => els[id] || (els[id] = { id, textContent: "", innerHTML: "", hidden: false, className: "", classList: { add() {}, remove() {} },
  children: [], appendChild(c) { this.children.push(c); return c; }, getAttribute() { return "{}"; }, set outerHTML(v) {}, get outerHTML() { return ""; } });
globalThis.document = { hidden: false, documentElement: { lang: "zh-TW" }, querySelectorAll: () => [], addEventListener() {}, getElementById: mk,
  createElement: () => mk("li" + Object.keys(els).length) };
globalThis.setInterval = () => 0;
globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => ({ ts: 0, q: Q }) });
__JS__
setTimeout(() => { console.log(JSON.stringify(Object.fromEntries(Object.entries(els).map(([k, v]) => [k, v.textContent || v.innerHTML])))); }, 30);
"""


def run_card(js, box, now_ms, q):
    src = HARNESS.replace("__NOW__", str(int(now_ms))).replace("__Q__", json.dumps(q)).replace("__BOX__", json.dumps(box)).replace("__JS__", js)
    r = subprocess.run([NODE, "-e", src], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stderr[-800:]
    return json.loads(r.stdout)


def us_quotes(t):
    q = {s: {"price": 100.0, "prev": 101.0, "chg": -0.99, "t": t, "open": 100.5} for s, *_ in SI.SECTORS}
    for s in ("SPY", "QQQ", "^SOX"):
        q[s] = {"price": 500.0, "prev": 505.0, "chg": -0.99, "t": t, "open": 502.0, "volx": 1.0}
    q["^GSPC"] = {"price": 6800.0, "prev": 6870.0, "chg": -1.02, "t": t, "open": 6850.0}
    q["^VIX"] = {"price": 18.0, "prev": 17.0, "chg": 5.9, "t": t}
    return q


def tw_quotes(tw_t, us_t):
    q = {s: {"price": 100.0, "prev": 101.0, "chg": -0.99, "t": tw_t} for s, *_ in TL.LEAD}
    q["^TWII"] = {"price": 27000.0, "prev": 27200.0, "chg": -0.74, "t": tw_t}
    q["0050.TW"] = {"price": 190.0, "prev": 191.0, "chg": -0.5, "t": tw_t}
    for s in ("^GSPC", "^SOX", "TSM"):
        q[s] = {"price": 300.0, "prev": 303.0, "chg": -2.0, "t": us_t}
    return q


def blob(d):
    return "\n".join(str(v) for v in d.values())


def rows(d):
    """every list line the card drew, plus the sector table"""
    return "\n".join(str(v) for k, v in d.items() if k.startswith("li") or k == "idsec")


US_LAST = unix(2026, 11, 25, 16, 0, NY)                 # the Wednesday before Thanksgiving (Thursday 2026-11-26)
TW_LAST = unix(2026, 11, 25, 13, 30, TPE)


def test_intraday_on_a_us_holiday():
    if not NODE:
        print("skip: node not installed")
        return
    d = run_card(SI.JS, "idbox", unix(2026, 11, 26, 12, 0, NY) * 1000, us_quotes(US_LAST))
    assert "今天美股休市" in d["idone"] and "最近一個交易日（11-25）" in d["idone"], d["idone"]
    assert "盤中" not in d["idone"]
    body = d["idone"].split("以下是最近一個交易日", 1)[1] + rows(d)
    assert "標普 -1.02%" in body and "當天" in body
    assert "今天" not in body and "今日" not in body, body                 # the figures belong to 11-25
    assert "美東 11-25 16:00" in d["idst"], d["idst"]


def test_intraday_ordinary_days_are_not_called_holidays():
    if not NODE:
        return
    d = run_card(SI.JS, "idbox", unix(2026, 11, 25, 12, 0, NY) * 1000, us_quotes(unix(2026, 11, 25, 11, 55, NY)))
    assert d["idone"].startswith("一句話看懂（盤中）") and "休市" not in d["idone"] and "今天" in rows(d) and "今日" in rows(d), d
    y = unix(2026, 11, 24, 16, 0, NY)
    d = run_card(SI.JS, "idbox", unix(2026, 11, 25, 8, 0, NY) * 1000, us_quotes(y))
    assert "美股尚未開盤" in d["idone"] and "休市" not in d["idone"], d["idone"]    # before the open a holiday is unknowable
    d = run_card(SI.JS, "idbox", unix(2026, 11, 25, 9, 35, NY) * 1000, us_quotes(y))
    assert "剛開盤" in d["idone"] and "休市" not in d["idone"], d["idone"]          # delayed quotes in the first minutes
    q = us_quotes(y)
    q["^GSPC"]["t"] = unix(2026, 11, 25, 11, 55, NY)                               # one lagging symbol is not a closed market
    d = run_card(SI.JS, "idbox", unix(2026, 11, 25, 12, 0, NY) * 1000, q)
    assert "休市" not in d["idone"], d["idone"]


def test_intraday_weekend():
    if not NODE:
        return
    d = run_card(SI.JS, "idbox", unix(2026, 11, 28, 12, 0, NY) * 1000, us_quotes(unix(2026, 11, 27, 13, 0, NY)))
    assert "今天美股休市" in d["idone"] and "（11-27）" in d["idone"], d["idone"]


def test_taiwan_card_on_a_us_holiday():
    if not NODE:
        return
    # Thanksgiving 23:30 Taipei = 10:30 New York: Taiwan traded today, New York is not trading
    now = unix(2026, 11, 26, 23, 30, TPE) * 1000
    d = run_card(TL.JS, "twbox", now, tw_quotes(unix(2026, 11, 26, 13, 30, TPE), US_LAST))
    assert "美股盤中" not in blob(d) and "昨晚美股" in blob(d), blob(d)         # 11-25's close is still last night's session
    # the morning after: no US session last night
    now = unix(2026, 11, 27, 10, 0, TPE) * 1000
    d = run_card(TL.JS, "twbox", now, tw_quotes(unix(2026, 11, 27, 9, 55, TPE), US_LAST))
    assert "昨晚美股" not in blob(d) and "美股最近一個交易日（11-25）" in blob(d), blob(d)


def test_taiwan_card_on_a_taiwan_holiday():
    if not NODE:
        return
    now = unix(2026, 11, 26, 11, 0, TPE) * 1000                 # a weekday with no Taiwan session (typhoon day, holiday)
    d = run_card(TL.JS, "twbox", now, tw_quotes(TW_LAST, US_LAST))
    assert "今天台股休市" in d["twone"] and "（11-25）" in d["twone"], d["twone"]
    assert "今天" not in d["twone"].split("以下是最近一個交易日", 1)[1] + rows(d), rows(d)
    assert "台股報價時間 11-25 13:30" in d["twst"], d["twst"]
    now = unix(2026, 11, 26, 8, 0, TPE) * 1000
    d = run_card(TL.JS, "twbox", now, tw_quotes(TW_LAST, US_LAST))
    assert "台股尚未開盤" in d["twone"] and "休市" not in d["twone"]


def test_time_labels_are_taipei_time():
    if not NODE:
        return
    # the viewer's device is in Los Angeles; both labels must still read Taipei time
    h = SL.JS[SL.JS.index("function hhmm(t)"):SL.JS.index(" function paintTiles")]
    now, t = unix(2026, 11, 26, 3, 0, TPE) * 1000, unix(2026, 11, 26, 2, 5, TPE)
    src = f"Date.now=()=>{int(now)};{h};console.log(hhmm({int(t)}));console.log(hhmm({int(US_LAST - 86400)}))"
    r = subprocess.run([NODE, "-e", src], capture_output=True, text=True, env={**os.environ, "TZ": "America/Los_Angeles"}, timeout=30)
    assert r.stdout.split("\n")[:2] == ["02:05", "11/25 05:00"], r.stdout + r.stderr
    d = run_card(TL.JS, "twbox", unix(2026, 11, 26, 11, 0, TPE) * 1000, tw_quotes(unix(2026, 11, 26, 10, 55, TPE), US_LAST))
    assert "最後更新 11:00（台北）" in d["twst"] and "台股報價時間 10:55" in d["twst"], d["twst"]


def test_cards_have_no_fixed_today_wording():
    for h in (SI.sec_intraday(types.SimpleNamespace(options=None)), TL.sec_tw_live(types.SimpleNamespace(taiwan=None))):
        assert "今天哪裡變了方向" not in h and "今天怎麼走" not in h
    assert "__MKT__" not in SI.JS and "__MKT__" not in TL.JS


class _Clock(datetime):
    fixed = None

    @classmethod
    def now(cls, tz=None):
        return cls.fixed.astimezone(tz)


def _due_at(moment):
    """kinds that fire when the briefing tick runs at this Taipei time"""
    from wsb.bot import app as A
    b = A.Sentinel.__new__(A.Sentinel)
    b.__dict__.update(engine=types.SimpleNamespace(ready=True, full_ready=True), _started=0.0, _sending=set())
    fired = []

    async def targets(_k):
        return ["t"]

    def spawn(coro, name):
        coro.close()
        fired.append(name)
    b._targets, b.spawn = targets, spawn
    _Clock.fixed = moment
    real, A.datetime = A.datetime, _Clock
    try:
        asyncio.run(b._briefing_tick())
    finally:
        A.datetime = real
    return [k.split(":")[1] for k in fired if k.startswith("brief:")]


def test_pre_open_briefing_is_the_same_time_before_the_open():
    from wsb.analytics.sessions import before_us_open
    summer, winter = datetime(2026, 7, 15, 12, 0, tzinfo=TPE), datetime(2026, 12, 15, 12, 0, tzinfo=TPE)
    assert before_us_open(summer, 30).strftime("%H:%M") == "21:00" and before_us_open(winter, 30).strftime("%H:%M") == "22:00"
    # the US and Europe change clocks on different days: 2026-03-09 New York is already on summer time
    assert before_us_open(datetime(2026, 3, 6, 12, 0, tzinfo=TPE), 30).strftime("%H:%M") == "22:00"
    assert before_us_open(datetime(2026, 3, 9, 12, 0, tzinfo=TPE), 30).strftime("%H:%M") == "21:00"
    assert "morning_call" in _due_at(datetime(2026, 7, 15, 21, 0, 30, tzinfo=TPE))
    assert "morning_call" not in _due_at(datetime(2026, 12, 16, 21, 0, 30, tzinfo=TPE))     # 90 minutes early in winter
    assert "morning_call" in _due_at(datetime(2026, 12, 16, 22, 0, 30, tzinfo=TPE))
    assert "morning_call" not in _due_at(datetime(2026, 12, 19, 22, 0, 30, tzinfo=TPE))     # Saturday: weekdays still apply


def test_other_briefings_keep_their_fixed_time():
    from wsb.config import SETTINGS
    kinds = {b["kind"]: b for b in SETTINGS.get("briefings", [])}
    assert {k: kinds[k]["time"] for k in ("morning_recap", "taiwan", "europe", "weekend")} == {
        "morning_recap": "07:30", "taiwan": "08:40", "europe": "15:30", "weekend": "10:00"}
    for hh, mm, kind in ((7, 30, "morning_recap"), (8, 40, "taiwan"), (15, 30, "europe")):
        assert kind in _due_at(datetime(2026, 12, 17, hh, mm, 30, tzinfo=TPE)), kind
        assert kind in _due_at(datetime(2026, 7, 16, hh, mm, 30, tzinfo=TPE)), kind


def _pf_alerts(positions, asof):
    from wsb.bot import app as A
    b = A.Sentinel.__new__(A.Sentinel)
    for fn in ("_canary_alerts", "_distress_alerts", "_intel_alerts", "_bottom_alerts", "_danger_alerts", "_stop_alerts", "_rule_alerts"):
        setattr(b, fn, lambda: [])
    b._started = 0.0
    total = sum(p["value_usd"] for p in positions)
    pf = {"total_value_usd": total, "day_pnl_usd": sum(p["day_usd"] for p in positions), "positions": positions}
    market = types.SimpleNamespace(q=lambda s: {"asof": asof[s]} if s in asof else None, sigma_move=lambda s: None)
    b.engine = types.SimpleNamespace(stress=None, market=market, portfolio=pf, holding_tickers=lambda: [])
    return [a for a in b._market_alerts() if a.key.startswith("pf_dd")]


def _pos(sym, value, d1):
    return {"sym": sym, "value_usd": value, "weight": 1.0, "d1_pct": d1, "day_usd": value - value / (1 + d1 / 100)}


def test_drawdown_is_per_market():
    # Taiwan fell 5 % today; last night's US gain in the same blend would have hidden it
    pos = [_pos("2330.TW", 30000.0, -5.0), _pos("NVDA", 70000.0, 2.5)]
    out = _pf_alerts(pos, {"2330.TW": "2026-11-04", "NVDA": "2026-11-03"})
    assert [a.key for a in out] == ["pf_dd:tw:2026-11-04"], [a.key for a in out]
    assert "台股 -5.00%" in out[0].title and "美股 +2.50%" in out[0].detail and "（11-03）" in out[0].detail
    assert "NVDA" not in out[0].title
    # the reverse: each side falls 2 %, on two different sessions -> neither market reached the 3 % line
    assert not _pf_alerts([_pos("2330.TW", 50000.0, -2.0), _pos("NVDA", 50000.0, -2.0)], {"2330.TW": "2026-11-04", "NVDA": "2026-11-03"})
    # both markets over the line: two alerts, one per market, shown separately
    out = _pf_alerts([_pos("2330.TW", 50000.0, -4.0), _pos("NVDA", 50000.0, -6.0)], {"2330.TW": "2026-11-04", "NVDA": "2026-11-03"})
    assert sorted(a.key for a in out) == ["pf_dd:tw:2026-11-04", "pf_dd:us:2026-11-03"]


def test_stale_quote_is_another_session():
    from wsb.analytics.portfolio import day_by_market
    pos = [_pos("NVDA", 50000.0, -4.0), _pos("AMD", 50000.0, 5.0)]
    r = day_by_market(pos, {"NVDA": {"asof": "2026-11-03"}, "AMD": {"asof": "2026-10-30"}}.get)
    assert len(r) == 1 and r[0]["skipped"] == ["AMD"] and abs(r[0]["pct"] + 4.0) < 1e-9
    out = _pf_alerts(pos, {"NVDA": "2026-11-03", "AMD": "2026-10-30"})
    assert len(out) == 1 and "AMD" in out[0].detail and "未計入" in out[0].detail
    assert day_by_market([{"sym": "X", "value_usd": 10.0, "day_usd": None}], lambda s: None) == []       # unknown ≠ flat
    assert day_by_market(None, lambda s: None) == []


def test_drawdown_stays_private():
    from wsb import store
    out = _pf_alerts([_pos("2330.TW", 30000.0, -5.0)], {"2330.TW": "2026-11-04"})
    assert out and all(store.is_private_alert(a.key) for a in out)
    from wsb.bot.app import _alert_kind
    assert _alert_kind(out[0].key) == "risk"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
