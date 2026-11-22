"""台股財報頁（2026-11-22，使用者：「既然有美股財報，怎麼沒有台股財報? 例如台股財報前瞻..等」）。

  1 台股財報前瞻：接下來 3 週的法說會（公開資訊觀測站），每家配上「這一季營收已經走到哪」——台灣獨有的優勢：每月 10 日前
    就公布上個月營收，季報出來前已經知道這季的一兩個月。程式算：本季已公布月份比去年同期、照目前速度推到整季比上一季、
    最新月營收年增與近 3 個月是加速還是放緩。另有每日排程讀法說會簡報與新聞後寫的重點（research_feed/tw_earn_preview.json）。
  2 剛開完的法說會（過去 7 天）。
  3 台股財報後白話解讀：每日排程寫的台股解讀（與美股同一份資料，只列台股）。
  4 期限：月營收每月 10 日、季報與年報的法定期限。
描述資料，不是預測，也不是投資建議。
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from tools.sitekit import T, card, esc, fold_rows, guard_safe

TPE = timezone(timedelta(hours=8))
FEED = Path(__file__).resolve().parents[1] / "research_feed"
AHEAD, BACK = 21, 7


def _json(f: Path) -> Dict:
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except (OSError, ValueError):
        return {}


def months() -> Dict[str, Dict]:
    """Monthly revenue: this machine's MOPS cache, filled from the PC seed (the cloud often can't reach MOPS)."""
    from wsb.data import tw_desk as D
    m = {k: dict(v) for k, v in (D.rev_load().get("months") or {}).items()}
    for ym, rows in (_json(FEED / "tw_rev_seed.json").get("months") or {}).items():
        tgt = m.setdefault(ym, {})
        for c, v in rows.items():
            tgt.setdefault(c, v)
    return m


def progress(ms: Dict[str, Dict], code: str) -> Dict:
    """Quarter-to-date revenue vs last year, the quarter projected vs the previous one, the latest month's yoy and the trend."""
    from wsb.data import tw_desk as D
    if not ms:
        return {}
    order = sorted(ms, reverse=True)
    latest = next((ym for ym in order if code in (ms.get(ym) or {})), None)
    if not latest:
        return {}
    tr = D.stock_trend(ms, code, [ym for ym in order if ym <= latest]) or {}
    nc = D.quarter_nowcast(ms, code, latest) or {}
    return {"ym": latest, "yoy": tr.get("yoy"), "accel": tr.get("accel"), "yoy3": tr.get("yoy3"),
            "qtd_yoy": nc.get("qtd_yoy"), "q_vs_prev": nc.get("q_vs_prev"), "months": nc.get("months")}


def _pct(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:+.0f}%"


FIN = ("28", "5880", "5876", "6005")      # 金融保險: monthly "revenue" swings with investment gains, not comparable


def _prog_text(p: Dict, code: str = "") -> str:
    if not p:
        return '<span class="muted">沒有月營收資料</span>'
    if code.startswith(FIN):
        return (f'<span class="muted">金融股的月營收主要反映投資損益，和一般公司的營收不能比（最新 {p["ym"][5:].lstrip("0")} 月年增 {_pct(p["yoy"])}）；'
                '看每月公布的稅後盈餘與法說會的資產品質比較準。</span>')
    q = (f'本季已公布 {p["months"]} 個月，比去年同期 <b>{_pct(p["qtd_yoy"])}</b>；照這個速度整季比上季 {_pct(p["q_vs_prev"])}（推估）'
         if p.get("months") else f'{p["ym"][5:]} 月是季底，季報會公布整季')
    acc = p.get("accel")
    trend = "" if acc is None else ("，近 3 個月<b class=\"up\">加速</b>" if acc > 3 else "，近 3 個月<b class=\"dn\">放緩</b>" if acc < -3 else "，近 3 個月持平")
    return f'{q}<br><span class="small">最新 {p["ym"][5:].lstrip("0")} 月年增 {_pct(p["yoy"])}{trend}</span>'


def _layers() -> Dict[str, str]:
    from wsb.data import tw_desk as D
    return {c: name for name, cs in D.LAYERS for c in cs}


def _universe() -> Dict:
    from wsb.data import tw_desk as D
    return D.universe(D.load())


def view(today: Optional[date] = None, irs: Optional[Dict] = None, ms: Optional[Dict] = None, univ: Optional[Dict] = None) -> Dict:
    from wsb.data import tw_irs as I
    today = today or datetime.now(TPE).date()
    irs = I.refresh() if irs is None else irs
    ms = months() if ms is None else ms
    u = _universe() if univ is None else univ
    codes, tw50, lay = set(u.get("codes") or []), set(u.get("tw50") or []), _layers()
    rows = [r for r in irs.get("rows") or [] if isinstance(r, dict)]
    up = [r for r in rows if today.isoformat() <= r["date"] <= (today + timedelta(days=AHEAD)).isoformat()]
    past = [r for r in rows if (today - timedelta(days=BACK)).isoformat() <= r["date"] < today.isoformat()]
    for r in up + past:
        r["big"] = r["code"] in codes or r["code"] in lay
        r["tw50"] = r["code"] in tw50
        r["layer"] = lay.get(r["code"])
        r["prog"] = progress(ms, r["code"]) if r["big"] else {}
    key = lambda r: (not r["big"], r["date"], r["time"], r["code"])  # noqa: E731
    return {"today": today.isoformat(), "up": sorted(up, key=key), "past": sorted(past, key=lambda r: (not r["big"], r["date"])),
            "fetched": irs.get("fetched"), "n_univ": len(codes), "rev_latest": max(ms) if ms else None}


def _row(r: Dict, notes: Dict[str, Dict]) -> str:
    d = r["date"][5:].replace("-", "/")
    pill = f'<span class="pill{"" if r["kind"] == "自辦法說" else " muted"}">{esc(r["kind"])}</span>'
    star = "⭐ " if r.get("tw50") else ""
    n = notes.get(r["code"])
    note = (f'<div class="small"><b>📝 前瞻重點</b>：{esc(guard_safe(n.get("one", "")))}'
            + "".join(f"<br>・{esc(guard_safe(w))}" for w in n.get("watch") or []) + "</div>") if n else ""
    return (f'<tr><td>{d}<div class="small muted">{esc(r["time"])}</div></td>'
            f'<td><b>{star}{esc(r["name"])}</b> <span class="tk">{esc(r["code"])}</span><div class="small">{pill} {esc(r["board"])}'
            + (f'・{esc(r["layer"])}' if r.get("layer") else "") + f'</div></td>'
            f'<td class="small">{_prog_text(r["prog"], r["code"]) if r.get("big") else "<span class=muted>不在追蹤範圍</span>"}{note}</td>'
            f'<td class="small muted">{esc(r["summary"][:120])}</td></tr>')


HEAD = "<tr><th>日期</th><th>公司</th><th>這一季營收走到哪（程式計算）</th><th>公司怎麼說這場</th></tr>"


def sec_tw_earn_preview(eng=None) -> str:
    try:
        v = view()
    except Exception:  # noqa: BLE001
        return ""
    if not v["up"] and not v["past"]:
        return ""
    notes = {str(x.get("code")): x for x in (_json(FEED / "tw_earn_preview.json").get("items") or []) if isinstance(x, dict)}
    big = [r for r in v["up"] if r["big"]]
    own = [r for r in big if r["kind"] == "自辦法說"]
    first = big[0] if big else (v["up"][0] if v["up"] else None)
    lead = (f'接下來 {AHEAD} 天有 {len(v["up"])} 場法說會，其中台灣 50、中型 100 或 AI 供應鏈公司 {len({r["code"] for r in big})} 家、{len(big)} 場（公司自辦 {len(own)} 場）'
            + (f'；最近的是 {first["name"]}（{first["date"][5:].replace("-", "/")}）' if first else "") + "。")
    one = list({r["code"]: r for r in reversed(big)}.values())[::-1]          # a company with several meetings counts once
    acc = [r for r in one if (r["prog"].get("accel") or 0) > 3 and not r["code"].startswith(FIN)]
    slow = [r for r in one if (r["prog"].get("accel") or 0) < -3 and not r["code"].startswith(FIN)]
    sub = (f'這些公司裡，月營收近 3 個月加速的有 {len(acc)} 家' + (f'（{"、".join(r["name"] for r in acc[:4])}）' if acc else "")
           + f'，放緩的有 {len(slow)} 家' + (f'（{"、".join(r["name"] for r in slow[:4])}）' if slow else "") + "。") if big else ""
    up_rows = [_row(r, notes) for r in v["up"]]
    nbig = len(big)
    past = [_row(r, notes) for r in v["past"]]
    from wsb.data import tw_desk as D
    dl = "".join(f'<li><b>{x["date"][5:].replace("-", "/")}</b> {esc(x["what"])}</li>' for x in D.deadlines(date.fromisoformat(v["today"]))[:4])
    body = (f'<p class="rimp big2"><b>一句話看懂：{esc(lead)}</b></p>' + (f'<p class="small">{esc(sub)}</p>' if sub else "")
            + '<p class="small">台股的優勢：每月 10 日前就公布上個月營收，所以季報出來前，已經知道這一季的一兩個月。下表把每場法說會配上'
              '「這一季營收已經走到哪」；⭐＝台灣 50 成分股。「券商論壇」是券商邀請的投資論壇，通常不公布新的財務數字；「自辦法說」才是公司自己的財報說明。</p>'
            + (fold_rows(up_rows, max(nbig, 12), HEAD, "場") if up_rows else '<p class="small muted">接下來 3 週沒有法說會。</p>')
            + (f'<details class="sgx"><summary>剛開完的（過去 {BACK} 天，{len(past)} 場）</summary>{fold_rows(past, 15, HEAD, "場")}</details>' if past else "")
            + (f'<p class="small"><b>接下來的期限</b></p><ul class="small">{dl}</ul>' if dl else "")
            + f'<p class="note">法說會來自公開資訊觀測站法人說明會一覽表（抓取 {esc(v.get("fetched") or "—")}）；月營收來自公開資訊觀測站每月營收彙總表'
              f'（最新 {esc(v.get("rev_latest") or "—")}）。「整季比上季」假設這季剩下的月份和已公布月份平均一樣，是推估。'
              '📝 前瞻重點由每日排程讀簡報與新聞後撰寫。描述資料，不是預測，也不是投資建議。</p>')
    return card("台股財報前瞻：接下來的法說會與本季營收進度", "Taiwan earnings preview", body, "wide")


def sec_tw_earn_after(eng=None) -> str:
    try:
        from tools import site_after as SAF
        items = [x for x in SAF._items() if x.get("mk") == "tw"]
        return SAF._card(items, "財報後白話解讀（台股）", "After the report: Taiwan", 8) if items else ""
    except Exception:  # noqa: BLE001
        return ""


# ------------------------------------------------------------------ 公司自己的動作：庫藏股與內部人申報轉讓（11-22 台股覆蓋檢討）
def sec_tw_corp(eng=None) -> str:
    from wsb.data import tw_corp as C
    try:
        d = C.refresh()
    except Exception:  # noqa: BLE001
        return ""
    bb, ins = d.get("buybacks") or [], d.get("insiders") or []
    if not bb and not ins:
        return ""
    today = datetime.now(TPE).date()
    wk = (today - timedelta(days=7)).isoformat()
    u = _universe()
    big = set(u.get("codes") or [])
    new7 = [x for x in bb if (x.get("date") or "") >= wk]
    prot = [x for x in bb if x.get("purpose_id") == "3"]
    lead = (f'最近 45 天有 {len(bb)} 家公司董事會決議買回自家股票（庫藏股），其中「維護公司信用及股東權益」{len(prot)} 家；最近 7 天新增 {len(new7)} 家'
            + (f'（{"、".join(x["name"] for x in new7[:5])}）' if new7 else "") + "。")
    th = "<tr><th>決議日</th><th>公司</th><th>目的</th><th class=\"r\">預定買回股數</th><th class=\"r\">價格區間</th><th>期間</th></tr>"
    rows = [f'<tr><td>{esc((x.get("date") or "")[5:].replace("-", "/"))}</td><td><b>{"⭐ " if x["code"] in big else ""}{esc(x["name"])}</b> '
            f'<span class="tk">{esc(x["code"])}</span><div class="small muted">{esc(x["board"])}</div></td><td class="small">{esc(x["purpose"])}</td>'
            f'<td class="r">{(x.get("shares") or 0) / 1000:,.0f} 張</td><td class="r small">{x.get("lo") or "—"}～{x.get("hi") or "—"}</td>'
            f'<td class="small">{esc((x.get("start") or "")[5:])}～{esc((x.get("end") or "")[5:])}{"（已完成）" if x.get("done") else ""}</td></tr>'
            for x in sorted(bb, key=lambda x: x.get("date") or "", reverse=True)]                  # newest first
    rows.sort(key=lambda r: "⭐" not in r)
    ith = "<tr><th>申報日</th><th>公司</th><th>誰</th><th>方式</th><th class=\"r\">預定轉讓</th><th class=\"r\">占持股</th></tr>"
    irows = [f'<tr><td>{esc((x.get("date") or "")[5:].replace("-", "/"))}</td><td><b>{"⭐ " if x["code"] in big else ""}{esc(x["name"])}</b> '
             f'<span class="tk">{esc(x["code"])}</span></td><td class="small">{esc(x["who"])}</td><td class="small">{esc(x["how"])}</td>'
             f'<td class="r">{x["shares"] / 1000:,.0f} 張</td><td class="r small">'
             + (f'{x["shares"] / x["held"] * 100:.0f}%' if x.get("held") else "—") + "</td></tr>" for x in ins]
    sold = [x for x in ins if "一般交易" in x.get("how", "") or "盤中" in x.get("how", "")]
    body = (f'<p class="rimp"><b>一句話看懂：{esc(lead)}</b></p>'
            '<p class="small">公司拿自己的錢買回股票，代表董事會覺得股價偏低或想穩住股價；內部人（董事、經理人、大股東）要轉讓股票必須事前申報。'
            '股價大跌時，一邊看公司有沒有出手、一邊看內部人是不是還在申報賣出。金管會 11/21 宣布鼓勵上市櫃公司實施庫藏股。⭐＝台灣 50 或中型 100。</p>'
            + fold_rows(rows, 15, th, "家")
            + (f'<h3>內部人申報轉讓（累積 {len({x["date"] for x in ins})} 個申報日、{len(ins)} 筆；在市場上賣的 {len(sold)} 筆）</h3>'
               + fold_rows(irows, 10, ith, "筆") if ins else "")
            + f'<p class="note">庫藏股：公開資訊觀測站買回自己公司股份彙總統計表（抓取 {esc(d.get("bb_fetched") or "—")}）；內部人：證交所 OpenAPI 每日內部人持股轉讓事前申報表'
              f'（只有上市，本站從 {esc(min((x.get("date") or "") for x in ins) if ins else "—")} 起逐日累積，抓取 {esc(d.get("ins_fetched") or "—")}）。'
              '「預定」是申報的上限，不代表一定會買或賣完。描述資料，不是投資建議。</p>')
    return card("公司自己的動作：庫藏股與內部人申報轉讓", "Buybacks and insider filings", body, "wide")


def corp_public() -> Dict:
    """site/tw_corp.json for the Discord push (sec_push reads it from the site, on the PC and in the cloud backup)."""
    from wsb.data import tw_corp as C
    d = C.refresh()
    big = set(_universe().get("codes") or [])
    return {"fetched": d.get("bb_fetched"), "buybacks": [{**x, "big": x["code"] in big} for x in d.get("buybacks") or []]}
