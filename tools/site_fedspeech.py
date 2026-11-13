"""聯準會官員講話卡（美債分頁）：最近誰講了什麼（原文重點句＋字數統計）、同一天 2 年期殖利率怎麼動、接下來兩週誰要講。"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Dict, Optional
from zoneinfo import ZoneInfo

import pandas as pd

from tools.sitekit import T, card, esc

NY, TPE = ZoneInfo("America/New_York"), ZoneInfo("Asia/Taipei")
ROLE = (("Vice Chair for Supervision", "監理副主席"), ("Vice Chair", "副主席"), ("Chair", "主席"), ("Governor", "理事"))
KIND = {"Speech": "演講", "Discussion": "座談", "Testimony": "國會作證", "Remarks": "致詞", "Panel": "座談"}


def _role(title: str) -> str:
    return next((zh for en, zh in ROLE if en in title), "")


def _who(s: Dict) -> str:
    """Board members by name; regional presidents get their bank so a beginner knows who they are."""
    return f'{s["who"]}（{s["role"]}）' if s.get("role") else s["who"]


def _ny_day(iso: str) -> Optional[pd.Timestamp]:
    try:
        dt = datetime.strptime(iso, "%Y-%m-%dT%H:%MZ").replace(tzinfo=ZoneInfo("UTC")).astimezone(NY)
        return pd.Timestamp(dt.date())
    except ValueError:
        return None


def _today():
    return datetime.now(NY).date()


def speech_day(s: Dict) -> Optional[pd.Timestamp]:
    """The day the speech was GIVEN: the Board's URL carries it (…/waller20260928a.htm); the RSS pubDate is when the
    page was posted, often the next day. Regional banks store `day` (pubDate's local date). Falls back to the pubDate's New York date."""
    if s.get("day"):
        try:
            return pd.Timestamp(s["day"])
        except ValueError:
            pass
    m = re.search(r"(20\d{6})[a-z]?\.htm", s.get("url", ""))
    if m:
        try:
            return pd.Timestamp(datetime.strptime(m.group(1), "%Y%m%d").date())
        except ValueError:
            pass
    return _ny_day(s.get("time", ""))


def _dtxt(s: Dict) -> str:
    d = speech_day(s)
    return d.strftime("%m/%d") if d is not None else "—"


def yield_move(dgs2: pd.Series, day: Optional[pd.Timestamp]) -> Optional[Dict]:
    """2-year yield change on the speech day (bp) and how big that is next to a usual day (σ of the prior 60 daily changes)."""
    s = dgs2.dropna() if dgs2 is not None else pd.Series(dtype=float)
    if day is None or len(s) < 70 or day not in s.index:
        return None
    i = s.index.get_loc(day)
    if i < 61:
        return None
    ch = s.diff() * 100
    sig = float(ch.iloc[i - 60:i].std())
    bp = float(ch.iloc[i])
    return {"bp": bp, "sig": sig, "k": abs(bp) / sig if sig else None}


def with_treasury(dgs2: Optional[pd.Series], ust2: Optional[Dict]) -> tuple:
    """FRED DGS2 plus the Treasury days FRED has not posted yet (same number, published the same evening).
    Returns (series, set of days that came from Treasury)."""
    s = dgs2.dropna() if dgs2 is not None else pd.Series(dtype=float)
    last = s.index.max() if len(s) else None
    add = {pd.Timestamp(k): float(v) for k, v in (ust2 or {}).items() if last is None or pd.Timestamp(k) > last}
    if not add or not len(s):
        return s, set()
    return pd.concat([s, pd.Series(add)]).sort_index(), set(add)


def _move_txt(m: Optional[Dict]) -> str:
    if not m:
        return "—"
    size = "，比平常一天大很多" if (m["k"] or 0) >= 2 else "，比平常一天大一些" if (m["k"] or 0) >= 1 else "，在平常範圍內"
    return f'{m["bp"]:+.0f}bp{size}'


def _cal_time(day: str, t: str) -> str:
    """'10:00 a.m.' Eastern on `day` → Taipei 'MM/DD HH:MM'."""
    m = re.match(r"(\d{1,2}):(\d{2})\s*([ap])", t or "")
    if not m:
        return day[5:].replace("-", "/") + "（美東日期，時間未公布）"
    h = int(m.group(1)) % 12 + (12 if m.group(3) == "p" else 0)
    dt = datetime.fromisoformat(day).replace(hour=h, minute=int(m.group(2)), tzinfo=NY).astimezone(TPE)
    return dt.strftime("%m/%d %H:%M") + " 台北"


def sec_fed_speeches(eng) -> str:
    try:
        from wsb.data import fed_speeches as FS
        d = FS.load()
    except Exception:  # noqa: BLE001
        return ""
    sp = d.get("speeches") or []
    if not sp:
        return ""
    try:
        dgs2 = eng.fred.get("DGS2")
    except Exception:  # noqa: BLE001
        dgs2 = pd.Series(dtype=float)
    dgs2, from_ust = with_treasury(dgs2, d.get("ust2"))
    cutoff = pd.Timestamp(_today()) - pd.Timedelta(days=14)   # two weeks back from today, not from the newest item
    recent = [s for s in sp if (speech_day(s) is not None and speech_day(s) >= cutoff)]
    policy = [s for s in recent if FS.lean(s) != "—"]
    for s in sp:
        s["_mv"] = yield_move(dgs2, speech_day(s))
    if policy:
        lead = (f'最近兩週有 {len({s["who"] for s in policy})} 位聯準會官員公開談經濟與利率：'
                + "；".join(f'{esc(_who(s))}（{_dtxt(s)}）{FS.lean(s)}'
                           + (f'，{FS.DIR_ZH[s.get("key_dir", "")]}' if s.get("key_dir") else "") for s in policy[:3]) + "。")
    else:
        lead = ("最近兩週聯準會官員的公開講話都不是談利率，市場沒有新的利率訊號從這裡來。" if recent
                else "最近兩週聯準會官員沒有新的公開講話（下面是更早的紀錄）。")
    quotes = []
    for s in policy[:3]:
        if s.get("key"):
            quotes.append(f'<li><b>{esc(_who(s))}</b> <span class="small muted">{esc(_dtxt(s))} 演講（美東日期）・'
                          f'同一天 2 年期美債殖利率 {esc(_move_txt(s["_mv"]))}</span><br>'
                          f'<span class="small">原文重點句：「{esc(s["key"])}」</span> <a class="small" href="{esc(s["url"])}" target="_blank" rel="noopener">全文</a></li>')
    today_ny = _today().isoformat()
    up = [u for u in (d.get("upcoming") or []) if u.get("date", "") >= today_ny]   # a stale calendar must not list past talks
    up_html = "".join(f'<li>{esc(_cal_time(u["date"], u.get("time", "")))}・{esc(KIND.get(u["title"].split(" - ")[0].strip(), u["title"].split(" - ")[0]))}・'
                      f'{esc(_role(u["title"]))} {esc(u["title"].split(" - ")[-1].split()[-1])}：{esc(u.get("topic", ""))}</li>' for u in up[:6])
    trs = "".join(f'<tr><td>{esc(_dtxt(s))}</td><td>{esc(_who(s))}</td><td class="small">{esc(s.get("topic", ""))}</td>'
                  f'<td>{FS.lean(s)}</td><td class="r small">{s.get("infl", "—")}／{s.get("jobs", "—")}</td>'
                  f'<td class="r small">{esc(_move_txt(s["_mv"]))}</td></tr>' for s in sp[:12])
    table = (f'<div class="scroll"><table class="mini"><thead><tr><th>演講日（美東）</th><th>誰</th><th>題目（原文）</th><th>多談哪邊</th>'
             f'<th class="r">通膨／就業 次數</th><th class="r">當天 2 年期殖利率</th></tr></thead><tbody>{trs}</tbody></table></div>')
    note = (f'資料：<a href="{FS.PAGE}" target="_blank" rel="noopener">聯準會理事會演講</a>與<a href="{FS.CAL_PAGE}" target="_blank" rel="noopener">官方行事曆</a>'
            '（主席、副主席與理事都有 FOMC 永久投票權）'
            + "".join(f'＋<a href="{m["page"]}" target="_blank" rel="noopener">{m["name"]}總裁演講</a>' for m in FS.REGIONAL.values())
            + '（地方聯準會總裁 12 位輪流投票，目前只收有乾淨官方 RSS 的銀行；紐約聯準會的 RSS 會擋自動程式，所以沒有）。「多談哪邊」只是數原文提到通膨和就業的次數，'
            '多 1.5 倍以上算多談那一邊；重點句是第一句「講者自己看法＋利率」的原文，「偏向收緊／放寬／觀望」只看這一句裡的字眼，不是 AI 判讀，也不翻譯以免失真，請點全文確認。'
            '2 年期殖利率最貼近市場對聯準會未來一兩年利率的猜測；同一天常有其他消息，所以只寫「同一天」，不說是演講造成的。資料來源 FRED DGS2，比市場晚一天'
            + (f'；FRED 還沒更新的 {", ".join(x.strftime("%m/%d") for x in sorted(from_ust))} 先用<a href="{FS.UST_PAGE}" target="_blank" rel="noopener">美國財政部當天公布的殖利率曲線</a>補上（FRED 之後刊登的是同一個數字）'
               if from_ust else "") + '。')
    body = (f'<p class="rimp big2"><b>{lead}</b></p>'
            + (f'<ul>{"".join(quotes)}</ul>' if quotes else "")
            + (f'<h3>接下來兩週誰要講</h3><ul class="small">{up_html}</ul>' if up_html else '<p class="small muted">官方行事曆上接下來兩週沒有理事演講。</p>')
            + f'<details class="sgx"><summary>{T("看最近 12 篇講話", "Recent speeches")}</summary>{table}</details>'
            + f'<p class="note">{note}</p>')
    return card("聯準會官員怎麼說：利率的線索", "Fed speakers: clues on rates", body, "wide")
