"""總覽頁：重大事件倒數與歷史震幅（FOMC、CPI、非農就業、四巫日）。倒數在瀏覽器裡每分鐘更新；震幅是 1995 年以來與近 3 年
標普 500 在這些日子的收盤對收盤平均漲跌幅（不分方向），和平常的日子比。"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from tools.sitekit import T, card

TPE = ZoneInfo("Asia/Taipei")
ET = ZoneInfo("America/New_York")
LINKS = {"fomc": (("聯準會會議日程與聲明", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"),
                  ("記者會直播（聯準會 YouTube）", "https://www.youtube.com/@federalreserve")),
         "cpi": (("BLS CPI 發布時間表", "https://www.bls.gov/schedule/news_release/cpi.htm"),),
         "nfp": (("BLS 就業報告發布時間表", "https://www.bls.gov/schedule/news_release/empsit.htm"),),
         "opex": (("Cboe 交易日曆", "https://www.cboe.com/about/hours/"),)}


def _ev(eng) -> dict:
    try:
        from wsb.analytics import event_clock as EC
        return EC.build(eng)
    except Exception:  # noqa: BLE001
        return {"available": False}


def _cmp(s) -> str:
    if not s:
        return "—"
    r = s["mean"] / s["base_mean"] if s["base_mean"] else 1
    word = "通常比平常晃" if r >= 1.2 else "比平常安靜" if r <= 0.85 else "和平常差不多"
    return f"平均 ±{s['mean']:.2f}%（平常 ±{s['base_mean']:.2f}%），≥1% 的機率 {s['big']:.0f}%（平常 {s['base_big']:.0f}%）・{word}"


EARN_FLOOR, EARN_DAYS = 5e11, 10
EARN_TIME = {"after": ((16, 5), "盤後", "after the close"), "pre": ((8, 0), "盤前", "before the open")}


def earn_events(eng, now: datetime, floor: float = EARN_FLOOR, days: int = EARN_DAYS) -> list:
    """Reports of companies worth ≥ $500B in the next 10 days (2026-11-16: NVIDIA, ~6 % of the S&P 500, moves the index
    like a CPI print, so it belongs on this card).  Time: 'after' → 16:05 New York, 'pre' → 08:00, unknown → 16:05 marked 時間未定.
    Implied move and the last four reactions come from the 財報前隱含波動 card's data when it has the company."""
    import json
    from datetime import timedelta
    from wsb.config import DATA_DIR
    try:
        cal = json.loads((DATA_DIR / "earn_days.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    et_now = now.astimezone(ET)
    end = (et_now + timedelta(days=days)).date().isoformat()
    sx = {r.get("sym"): r for r in ((getattr(eng, "sx", None) or {}).get("earn") or []) if isinstance(r, dict)}
    try:
        from wsb.data.stocks import universe
        zh = {k: v[0] for k, v in ((universe().get("us") or {}).get("symbols") or {}).items()}
    except Exception:  # noqa: BLE001
        zh = {}
    out = []
    for day, v in sorted(cal.items()):
        if not (et_now.date().isoformat() <= day <= end):
            continue
        for r in (v.get("rows") if isinstance(v, dict) else None) or []:
            if float(r.get("mcap") or 0) < floor:
                continue
            (hh, mm), tz, ten = EARN_TIME.get(r.get("time") or "", ((16, 5), "時間未定", "time n/a"))
            t = datetime.fromisoformat(day).replace(hour=hh, minute=mm, tzinfo=ET)
            if t <= et_now:
                continue
            x = sx.get(r["sym"]) or {}
            out.append({"key": "earn", "sym": r["sym"], "zh": f"{zh.get(r['sym'], r.get('name') or r['sym'])}財報（{tz}）",
                        "en": f"{r.get('name') or r['sym']} earnings ({ten})", "next": t.isoformat(), "ts": int(t.timestamp()),
                        "days": (t.date() - et_now.date()).days, "mcap": float(r["mcap"]), "eps_f": r.get("eps_f"),
                        "mv": x.get("mv"), "reacts": x.get("reacts") or [], "avg": x.get("avg"), "exact": bool(r.get("time"))})
    return out


def index_events(now: datetime, days: int = 14) -> list:
    """Index rebalance days from 被迫進出的錢 (rule-derived, checked against past closing volume) in the next `days` days.
    MSCI / Taiwan 50 trade at the Taiwan close (13:30 Taipei); S&P / Russell at the New York close.  The S&P rebalance shares
    its day with quad witching, which this card already shows, so it is folded into that tile instead of a second one."""
    try:
        from wsb.data import forced_flows as FF
        v = FF.view()
    except Exception:  # noqa: BLE001
        return []
    med = v.get("past_med") or {}
    out = []
    for e in v.get("events") or []:
        if e["kind"] == "sp":
            continue
        if e["kind"] in ("msci", "tw50"):
            d = e.get("tw_date") or e["date"]
            t = datetime.fromisoformat(d).replace(hour=13, minute=30, tzinfo=TPE)
        else:
            t = datetime.fromisoformat(e["date"]).replace(hour=16, minute=0, tzinfo=ET)
        if not (now < t <= now + timedelta(days=days)):
            continue
        zh = FF.KIND[e["kind"]][0] + ("（台股收盤調整）" if e["kind"] in ("msci", "tw50") else "（美股收盤調整）")
        out.append({"key": "index", "kind": e["kind"], "zh": zh, "en": FF.KIND[e["kind"]][1], "next": t.isoformat(), "ts": int(t.timestamp()),
                    "days": (t.astimezone(TPE).date() - now.astimezone(TPE).date()).days, "med": med.get(e["kind"])})
    return out


def _index_tile(r: dict) -> str:
    t = datetime.fromisoformat(r["next"])
    tp = t.astimezone(TPE)
    return (f'<div class="ect"><div class="ecn">{T(r["zh"], r["en"])}</div>'
            f'<div class="ecc" data-ts="{r["ts"]}">{r["days"]} {T("天", "d")}</div>'
            f'<div class="small muted">{T("台北", "Taipei")} {tp:%m-%d %H:%M}</div>'
            + (f'<div class="small">過去同一種日子，收盤成交量是平常的 {r["med"]:.1f} 倍（指數基金被迫在收盤買賣）</div>' if r.get("med") else "")
            + '<div class="small"><a href="#forced">被迫進出的錢</a></div></div>')


def _earn_tile(r: dict) -> str:
    et = datetime.fromisoformat(r["next"])
    tp = et.astimezone(TPE)
    when = (f'{T("美東", "ET")} {et:%m-%d}{" 收盤後" if "盤後" in r["zh"] else " 開盤前" if "盤前" in r["zh"] else ""}'
            f'・{T("台北", "Taipei")} {tp:%m-%d} {"清晨 " if 0 <= tp.hour < 8 else ""}{tp:%H:%M} 起')
    bits = []
    if r.get("mv") is not None:
        bits.append(f"選擇權預估公布後兩天 ±{r['mv']:.1f}%")
    if r.get("reacts"):
        bits.append("過去 4 次 " + "、".join(f"{v:+.1f}%" for v in r["reacts"]))
    if r.get("eps_f"):
        bits.append(f"每股盈餘預期 {r['eps_f']} 美元")
    return (f'<div class="ect"><div class="ecn">{T(r["zh"], r["en"])}</div>'
            f'<div class="ecc" data-ts="{r["ts"]}">{r["days"]} {T("天", "d")}</div>'
            f'<div class="small muted">{when}</div>'
            + (f'<div class="small">{"；".join(bits)}</div>' if bits else "")
            + f'<div class="small muted">市值約 {r["mcap"] / 1e12:.1f} 兆美元，公布後常牽動整個大盤與台股供應鏈</div></div>')


def sec_event_clock(eng) -> str:
    ev = _ev(eng)
    earn = earn_events(eng, datetime.now(TPE))
    idx = index_events(datetime.now(TPE))
    if not ev.get("available") and not earn and not idx:
        return ""
    tiles = ""
    for r in sorted([x for x in ev.get("events") or [] if x.get("ts")] + earn + idx, key=lambda x: x["ts"]):
        if r.get("key") == "earn":
            tiles += _earn_tile(r)
            continue
        if r.get("key") == "index":
            tiles += _index_tile(r)
            continue
        et = datetime.fromisoformat(r["next"])
        tp = et.astimezone(TPE)
        a, rc = r.get("all"), r.get("recent")
        tiles += (f'<div class="ect"><div class="ecn">{T(r["zh"], r["en"])}</div>'
                  f'<div class="ecc" data-ts="{r["ts"]}">{r["days"]} {T("天", "d")}</div>'
                  f'<div class="small muted">{T("美東", "ET")} {et:%m-%d %H:%M}・{T("台北", "Taipei")} {tp:%m-%d %H:%M}</div>'
                  + (f'<div class="small">{T("1995 年以來（" + str(a["n"]) + " 次）", "Since 1995")}：{T(_cmp(a), "")}</div>' if a else "")
                  + (f'<div class="small muted">{T("近 3 年（" + str(rc["n"]) + " 次）", "Last 3 years")}：{T(_cmp(rc), "")}</div>' if rc else "")
                  + '<div class="small">' + "・".join(f'<a href="{u}" target="_blank" rel="noopener">{T(z, "")}</a>' for z, u in LINKS.get(r["key"], ())) + "</div>"
                  + "</div>")
    if not tiles:
        return ""
    note = T("震幅＝標普 500 在事件當天收盤對前一天收盤的漲跌幅絕對值，不分方向；CPI、非農在美東 8:30 開盤前公布，FOMC 在 14:00 公布，所以都看當天。"
             f"日期：聯準會會議日、FRED 官方發布日（含已排定日期）、四巫日按交易所規則推算；市值 {EARN_FLOOR / 1e8:,.0f} 億美元以上的公司財報讀網站的財報日曆（盤後以美東 16:05 計，實際以公司公告為準）。這是歷史上波動有多大的統計，不預測方向，也不是投資建議。",
             "Absolute S&P 500 close-to-close move on the event day vs all days. Historical, not a forecast.")
    body = f'<div class="ecg">{tiles}</div><p class="note">{note}</p>'
    return card("重大事件倒數：下一個會讓市場晃的日子", "Countdown to the next market-moving events", body, "wide",
                sub=f"聯準會、CPI、非農、四巫日、指數調整日，以及市值 {EARN_FLOOR / 1e8:,.0f} 億美元以上的公司財報")


CSS = (".ecg{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}"
       ".ect{padding:10px 12px;border:1px solid var(--bd);border-radius:10px;background:var(--wash);display:flex;flex-direction:column;gap:3px;min-width:0}"
       ".ecn{font-weight:700;font-size:13.5px}.ecc{font-size:22px;font-weight:800;line-height:1.2}")
JS = r"""
(function(){function tick(){var now=Date.now()/1000;document.querySelectorAll('.ecc[data-ts]').forEach(function(e){var s=+e.dataset.ts-now,en=document.documentElement.lang==='en';
 if(s<=0){e.textContent=en?'now / just out':'進行中／剛公布';return;}var d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);
 e.textContent=en?(d+'d '+h+'h '+m+'m'):(d+' 天 '+h+' 小時 '+m+' 分');});}tick();setInterval(tick,60000);})();
"""


def upcoming(eng, now=None, days: int = 7) -> dict:
    """upcoming.json (2026-11-16): one shared list of what is coming in the next `days` days — every report of a company worth
    ≥ $100B (with the 財報前瞻 call when there is one) and the macro events of the countdown card — with New York and Taipei
    times.  The voice routines read it, so none of them has to say "I don't have the exact date" for a scheduled report again."""
    import json
    from pathlib import Path
    now = now or datetime.now(TPE)
    out = []
    for r in earn_events(eng, now, floor=1e11, days=days):
        tp = datetime.fromisoformat(r["next"]).astimezone(TPE)
        out.append({"kind": "earnings", "sym": r["sym"], "zh": r["zh"], "et": r["next"][:16], "tpe": tp.strftime("%Y-%m-%d %H:%M"),
                    "mcap_t": round(r["mcap"] / 1e12, 2), "eps_f": r.get("eps_f"), "implied": r.get("mv")})
    pv = Path(__file__).resolve().parents[1] / "research_feed" / "earn_preview.json"
    try:
        calls = {(x.get("sym"), x.get("date")): x.get("call") for x in json.loads(pv.read_text(encoding="utf-8")).get("items") or []}
    except (OSError, ValueError):
        calls = {}
    for x in out:
        x["preview"] = calls.get((x["sym"], x["et"][:10]))
    for r in (_ev(eng).get("events") or []):
        if r.get("ts") and r.get("days") is not None and r["days"] <= days:
            tp = datetime.fromisoformat(r["next"]).astimezone(TPE)
            out.append({"kind": "macro", "key": r["key"], "zh": r["zh"], "et": r["next"][:16], "tpe": tp.strftime("%Y-%m-%d %H:%M")})
    for r in index_events(now, days):
        tp = datetime.fromisoformat(r["next"]).astimezone(TPE)
        out.append({"kind": "index", "key": r["kind"], "zh": r["zh"], "et": r["next"][:16], "tpe": tp.strftime("%Y-%m-%d %H:%M"),
                    "volume_x": r.get("med")})
    out.sort(key=lambda x: x["tpe"])
    return {"asof": now.strftime("%Y-%m-%d %H:%M"), "days": days, "items": out,
            "note": "財報時間：盤後以美東 16:05、盤前以 08:00 估，實際以公司公告為準。"}
