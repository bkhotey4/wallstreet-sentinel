"""總覽頁：重大事件倒數與歷史震幅（FOMC、CPI、非農就業、四巫日）。倒數在瀏覽器裡每分鐘更新；震幅是 1995 年以來與近 3 年
標普 500 在這些日子的收盤對收盤平均漲跌幅（不分方向），和平常的日子比。"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from tools.sitekit import T, card

TPE = ZoneInfo("Asia/Taipei")
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


def sec_event_clock(eng) -> str:
    ev = _ev(eng)
    if not ev.get("available"):
        return ""
    tiles = ""
    for r in ev["events"]:
        if not r.get("ts"):
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
             "日期：聯準會會議日、FRED 官方發布日（含已排定日期）、四巫日按交易所規則推算。這是歷史上波動有多大的統計，不預測方向，也不是投資建議。",
             "Absolute S&P 500 close-to-close move on the event day vs all days. Historical, not a forecast.")
    body = f'<div class="ecg">{tiles}</div><p class="note">{note}</p>'
    return card("重大事件倒數：下一個會讓市場晃的日子", "Countdown to the next market-moving events", body, "wide")


CSS = (".ecg{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}"
       ".ect{padding:10px 12px;border:1px solid var(--bd);border-radius:10px;background:var(--wash);display:flex;flex-direction:column;gap:3px;min-width:0}"
       ".ecn{font-weight:700;font-size:13.5px}.ecc{font-size:22px;font-weight:800;line-height:1.2}")
JS = r"""
(function(){function tick(){var now=Date.now()/1000;document.querySelectorAll('.ecc[data-ts]').forEach(function(e){var s=+e.dataset.ts-now,en=document.documentElement.lang==='en';
 if(s<=0){e.textContent=en?'now / just out':'進行中／剛公布';return;}var d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);
 e.textContent=en?(d+'d '+h+'h '+m+'m'):(d+' 天 '+h+' 小時 '+m+' 分');});}tick();setInterval(tick,60000);})();
"""
