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
            f'<td class="small">{_watch_text(r)}</td></tr>')


def _watch_text(r: Dict) -> str:
    """這場要看什麼 (11-25, user: 「公司怎麼說這場…我不需要知道受誰邀請參加」): the MOPS 摘要 is mostly 「受邀參加某證券論壇」,
    so the column now says what kind of meeting it is and what the revenue trend makes worth listening for."""
    kind = ("公司自己的財報說明，會有新數字（上一季財報，常有下一季展望）。" if r.get("kind") == "自辦法說"
            else "券商辦的論壇，通常不公布新數字；能聽的是管理層口頭對下一季的看法。")
    p, code = r.get("prog") or {}, str(r.get("code") or "")
    if code.startswith(FIN):
        ask = "金融股：看資產品質與投資損益（股市大跌時，持有的股票債券會有評價損失）。"
    elif not p:
        ask = ""
    else:
        acc, yoy = p.get("accel"), _pct(p.get("yoy"))
        ask = ("" if acc is None else
               f"營收近 3 個月加速（最新年增 {yoy}）：聽它說這是新訂單、會延續，還是客戶提前拉貨的一次性。" if acc > 3 else
               f"營收近 3 個月放緩（最新年增 {yoy}）：聽放緩的原因（客戶延後、價格下降或匯率），和下一季會不會回升。" if acc < -3 else
               f"營收持平（最新年增 {yoy}）：聽下一季的看法有沒有改變。")
    return esc(kind) + (f"<br><b>{esc(ask)}</b>" if ask else "")


HEAD = "<tr><th>日期</th><th>公司</th><th>這一季營收走到哪（程式計算）</th><th>這場要看什麼</th></tr>"


def us_links(eng, now: Optional[datetime] = None, days: int = 21, floor: float = 5e10) -> List[Dict]:
    """美股財報 → 台股誰會跟著動 (11-25, user: 「台股財報前瞻怎麼跟美股財報前瞻的內容差異很大?」): 台股這三週幾乎只有券商論壇，
    真正會在這段時間動到台股的，是美股大公司的財報。每一家接下來 21 天要公布、市值 ≥ 500 億美元、本站有股價的美股公司，
    配上「它晚上漲跌、台股隔天跟著動」的台股——和即時新聞影響估算同一套方法（舊資料估 β，最後 250 組沒看過的資料驗證）。
    金融股排除：它們跟的是整個大盤，不是這家公司。"""
    from tools.site_events import earn_events
    from wsb.analytics import news_impact as NI
    from wsb.data.stocks import universe
    sp = getattr(eng, "stockprices", None)
    cl = getattr(sp, "close", None)
    if cl is None or getattr(cl, "empty", True):
        return []
    allu = {}
    for mk in ("us", "tw"):
        for k, v in ((universe().get(mk) or {}).get("symbols") or {}).items():
            allu[k] = (v[0], v[1] if len(v) > 1 else k, mk)
    tws = [k for k, v in allu.items() if v[2] == "tw" and k in cl.columns and not k.startswith(FIN)]
    calls = {(x.get("sym"), x.get("date")): x.get("call") for x in (_json(FEED / "earn_preview.json").get("items") or []) if isinstance(x, dict)}
    out = []
    for r in earn_events(eng, now or datetime.now(TPE), floor=floor, days=days):
        if r["sym"] not in cl.columns:
            continue
        tw = NI.tw_direct(cl, r["sym"], tws, allu)[:5]
        if not tw:
            continue
        tp = datetime.fromisoformat(r["next"]).astimezone(TPE)
        out.append({"sym": r["sym"], "zh": r["zh"], "tpe": tp.strftime("%m/%d %H:%M"), "exact": "時間未定" not in str(r.get("zh")),
                    "call": calls.get((r["sym"], r["next"][:10])), "tw": tw})
    return out


def _us_links_html(rows: List[Dict]) -> str:
    if not rows:
        return ""
    tr = [f'<tr><td>{esc(r["tpe"])}</td><td><b>{esc(r["zh"])}</b> <span class="tk">{esc(r["sym"])}</span>'
          + (f'<div class="small muted">美股財報前瞻：{esc(r["call"])}</div>' if r.get("call") else "") + '</td><td class="small">'
          + "、".join(f'{esc(t["zh"])}（β {t["beta"]:.2f}）' for t in r["tw"]) + "</td></tr>" for r in rows]
    names = "、".join(r["zh"].split("財報")[0] for r in rows[:3])
    b0 = rows[0]["tw"][0]["beta"]
    return (f'<h3>這三週真正會動到台股的：美股大公司財報</h3>'
            f'<p class="small">台股這段時間多是券商論壇、不公布新數字；會帶動台股的，反而是美股財報（{esc(names)} 等 {len(rows)} 家）。'
            f'下表是「這家美股公司晚上漲跌，隔天台股跟著動」的公司。β {b0:.2f} 代表美股動 5%、台股隔天平均動 {b0 * 5:.1f}%（同方向）；'
            '每一檔都用最後 250 組沒看過的資料驗證過。這是過去的統計關係，不是供貨合約，也不代表這次一定一樣。'
            '美股那邊的機率判斷在「美股財報」頁的「財報前瞻」。</p>'
            + fold_rows(tr, 8, "<tr><th>台北時間</th><th>美股公司</th><th>過去隔天跟著動的台股</th></tr>", "家"))


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
    try:
        links = us_links(eng)
    except Exception:  # noqa: BLE001
        links = []
    body = (f'<p class="rimp big2"><b>一句話看懂：{esc(lead)}</b></p>' + (f'<p class="small">{esc(sub)}</p>' if sub else "")
            + '<p class="small">台股的優勢：每月 10 日前就公布上個月營收，所以季報出來前，已經知道這一季的一兩個月。下表把每場法說會配上'
              '「這一季營收已經走到哪」；⭐＝台灣 50 成分股。「券商論壇」是券商邀請的投資論壇，通常不公布新的財務數字；「自辦法說」才是公司自己的財報說明。</p>'
            + (fold_rows(up_rows, max(nbig, 12), HEAD, "場") if up_rows else '<p class="small muted">接下來 3 週沒有法說會。</p>')
            + _us_links_html(links)
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


def alerts_public() -> Dict:
    """site/tw_alerts.json for three Taiwan Discord pushes (11-22, 台股覆蓋清單「Discord 通知」): the pre-open lights, the newest
    monthly revenue's biggest accelerations / slowdowns, and tomorrow's company-run 法說會."""
    out: Dict = {"made": datetime.now(TPE).strftime("%Y-%m-%d %H:%M")}
    try:
        from wsb.data import tw_preopen as P
        v = P.view()
        mg = (v.get("mg") or [])[-1:] or [{}]
        adr = v.get("adr") or {}
        out["preopen"] = {"adr_light": v.get("adr_light"), "adr_now": adr.get("now"), "adr_pct": adr.get("pct"), "adr_mid": adr.get("mid"),
                          "adr_chg_mid": adr.get("chg_mid"), "mg": mg[0], "cal": [c for c in v.get("cal") or [] if not c.get("void")]}
        from wsb.data.tw_margin import floor_on
        out["preopen"]["floor"] = floor_on()
        try:
            from wsb.data import tw_chips as CH
            out["preopen"]["mratio"] = (CH.refresh().get("mratio") or {}).get("ratio")
        except Exception:  # noqa: BLE001
            pass
        try:
            from tools.site_twpreopen import tx_night
            tx = tx_night(P.load().get("px") or {})
            if tx:
                out["preopen"]["night"] = {"session": tx["session"], "last": tx["near"]["last"], "pct": tx["near"]["pct"],
                                           "light": tx["light"], "implied": tx.get("implied"), "twii": tx.get("twii")}
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001
        pass
    try:
        from wsb.data import tw_desk as D
        ms = months()
        rv = D.rev_view({"months": ms}, D.load(), None) if ms else {}
        tr = [t for t in rv.get("trends") or [] if t.get("accel") is not None and not str(t["code"]).startswith(FIN)
              and abs(t["accel"]) <= 200]                  # project-based revenue (builders) swings by hundreds of points
        out["rev"] = {"latest": rv.get("latest"), "breadth": rv.get("breadth"),
                      "acc": [{k: t[k] for k in ("code", "name", "yoy", "accel")} for t in sorted(tr, key=lambda t: -t["accel"])[:5]],
                      "slow": [{k: t[k] for k in ("code", "name", "yoy", "accel")} for t in sorted(tr, key=lambda t: t["accel"])[:5]]}
    except Exception:  # noqa: BLE001
        pass
    try:
        v = view()
        tmr = (date.fromisoformat(v["today"]) + timedelta(days=1)).isoformat()
        out["irs_next"] = {"date": tmr, "rows": [{k: r.get(k) for k in ("code", "name", "time", "kind", "layer", "summary", "prog")}
                                                for r in v["up"] if r["date"] == tmr and r["big"] and r["kind"] == "自辦法說"]}
    except Exception:  # noqa: BLE001
        pass
    try:
        from wsb.data import tw_nsf as N
        nd = N.refresh()
        if nd.get("news"):
            top = nd["news"][0]
            out["nsf"] = {**top, "status": nd.get("status") or {}, "body": ((nd.get("bodies") or {}).get(top["url"]) or "")[:700]}
        rules = list(nd.get("fsc") or [])
        try:
            from wsb.data import tw_margin as TM
            rules += TM.refresh().get("news") or []        # 證交所自己宣布的措施
        except Exception:  # noqa: BLE001
            pass
        if rules:
            ft = max(rules, key=lambda r: r["date"])
            out["fsc"] = {**ft, "body": ((nd.get("fsc_bodies") or {}).get(ft["url"]) or "")[:900]}
    except Exception:  # noqa: BLE001
        pass
    return out
