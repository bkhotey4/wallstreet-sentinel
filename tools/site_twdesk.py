"""「台股專業判讀」頁（2026-11-21）：交易台每天會看、但散戶看不到的四件事。資料與規則見 wsb/data/tw_desk.py。
1 被迫進出的錢日曆  2 估值在自己歷史的位置  3 月營收與 AI 供應鏈熱度  4 我們的判斷準不準（校準）
每張卡第一句白話、數字附時間、全部列出（多的摺起來）。只描述資料，不給個人買賣時點或價位。"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from tools.sitekit import T, card, esc, fold_rows

TPE = timezone(timedelta(hours=8))
WD = "一二三四五六日"
FEED = Path(__file__).resolve().parents[1] / "research_feed"          # public repo only (absent on the private copy)
KIND_ZH = {"msci": "MSCI 季度審查生效", "tw50": "台灣 50 指數調整生效", "ftse": "富時（FTSE）全球指數季度調整生效"}
KIND_WHY = {"msci": "追蹤 MSCI 新興市場、全世界指數的被動基金在當天收盤照新權重調整；台股權重一變，外資就得在收盤買或賣台股。",
            "tw50": "0050、006208 等追蹤台灣 50 的基金照新成分股調整，被加入或剔除的股票收盤成交量放大。",
            "ftse": "追蹤富時全球、新興市場指數的被動基金在當天收盤照新權重調整。"}


def _md(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    d = date.fromisoformat(iso[:10])
    return f"{d.month}/{d.day}（{WD[d.weekday()]}）"


def _yi(x: Optional[float]) -> str:
    if not x:
        return "—"
    return f"{x / 1e12:,.2f} 兆" if x >= 1e12 else f"{x / 1e8:,.0f} 億"


def _ts(t) -> str:
    try:
        return datetime.fromtimestamp(float(t), TPE).strftime("%m/%d %H:%M")
    except (TypeError, ValueError, OSError):
        return "—"


def _seed() -> Dict:
    try:
        f = FEED / "tw_flow_seed.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _cash(x) -> str:
    return "—" if not x else f"{x:,.2f} 元"


# ============================================================ 1 被迫進出的錢日曆
def flow_lead(v: Dict) -> str:
    ev = []
    for e in v.get("index") or []:
        ev.append((e["date"], KIND_ZH.get(e["kind"], e["kind"]), None))
    for r in v.get("etf") or []:
        if r["next"].get("date"):
            ev.append((r["next"]["date"], f"{r['code']} {r['name']}換股", r.get("per1")))
    ev.sort()
    if not ev:
        return "一句話看懂：接下來 4 個月沒有算得出日期的指數或 ETF 調整。"
    d0 = ev[0][0]
    same = [e for e in ev if e[0] == d0]
    names = "、".join(e[1] for e in same)
    big = max((e for e in ev if e[2]), key=lambda e: e[2], default=None)
    s = f"一句話看懂：下一個「基金不得不在收盤成交」的日子是 {_md(d0)}：{names}。"
    if big:
        s += f"規模最大的是 {_md(big[0])}的{big[1]}：每換掉 1% 的成分，大約有 {_yi(big[2])}元要在當天收盤買賣。"
    return s


def sec_tw_flowcal(eng=None, v: Optional[Dict] = None) -> str:
    if v is None:
        try:
            from wsb.data import tw_desk as D
            v = D.flow_view(seed=_seed())
        except Exception:  # noqa: BLE001
            return ""
    if not (v.get("index") or v.get("etf") or v.get("exdiv") or v.get("punish")):
        return ""
    body = f'<p class="rimp big2"><b>{T(esc(flow_lead(v)), "")}</b></p>'
    # A. index + ETF reviews
    rows = []
    for e in v.get("index") or []:
        rows.append(e["date"] + f'<tr><td>{_md(e["date"])}</td><td>{esc(KIND_ZH.get(e["kind"], e["kind"]))}</td><td>—</td><td class="small">{esc(KIND_WHY.get(e["kind"], ""))}（規則推算）</td></tr>')
    for r in v.get("etf") or []:
        when = _md(r["next"]["date"]) if r["next"].get("date") else f'{int(r["next"]["month"][5:7])} 月（生效日以指數公司公告為準）'
        size = f'規模 {_yi(r.get("aum"))}元（{esc(r.get("asof") or "")}）；每換 1% 成分 ≈ {_yi(r.get("per1"))}元' if r.get("aum") else "規模待更新"
        rows.append((r["next"]["date"] or r["next"]["month"] + "-32") + f'<tr><td>{when}</td><td>{esc(r["code"])} {esc(r["name"])}</td><td class="small">{size}</td>'
                    f'<td class="small">追蹤 <a href="{esc(r["src"])}" target="_blank" rel="noopener">{esc(r["index"])}</a>，每年 {"、".join(str(m) for m in r["months"])} 月調整（{"規則推算" if r["rule"] != "announce" else "依編製規則整理"}）。</td></tr>')
    rows = [x[10:] for x in sorted(rows)]
    body += "<h3>指數與 ETF 調整（被動基金被迫成交）</h3>" + fold_rows(
        rows, 8, "<tr><th>日期</th><th>事件</th><th>估算金額</th><th>為什麼重要</th></tr>", "筆")
    body += ('<p class="small muted">估算方法：ETF 規模＝投信公布的淨值 × 受益權單位數；「每換 1% 成分」＝規模 × 1%。'
             '實際換多少要看指數公司公告的增刪名單。</p>')
    seed = v.get("seed") or {}
    items = seed.get("items") or []
    if items:
        srows = [f'<tr><td>{_md(i.get("date"))}</td><td>{esc(i.get("what", ""))}</td><td class="small">{esc("、".join(i.get("codes") or []))}</td>'
                 f'<td class="small"><a href="{esc(i.get("src", ""))}" target="_blank" rel="noopener">來源</a>（抓取 {esc(i.get("fetched", ""))}）</td></tr>' for i in items]
        body += "<h3>已公告的成分股增刪</h3>" + fold_rows(srows, 8, "<tr><th>生效日</th><th>內容</th><th>股票</th><th>出處</th></tr>", "筆")
    else:
        body += ('<p class="small">已公告的成分股增刪：MSCI 官網有機器人驗證，本站不繞過；改由 Gemini 每週到 MSCI、臺灣指數公司、'
                 '投信官方公告頁核對後寫進本站（附抓取時間）。目前還沒有寫入的公告。</p>')
    # B. quarter-end window
    q = v.get("quarter") or {}
    if q:
        body += (f'<h3>投信季底作帳期間</h3><p class="small">{_md(q["from"])}～{_md(q["to"])}（本季最後 10 個交易日）。'
                 '投信基金按季公布績效，季底前常集中拉抬或調節持股；這是市場慣例，不是法規，只當作背景。</p>')
    # C. ex-dividend in the universe
    u = v.get("univ") or {}
    ex = v.get("exdiv") or []
    erows = [f'<tr><td>{_md(r["date"])}</td><td>{esc(r["code"])} {esc(r["name"])}</td><td>{esc(r["kind"])}</td>'
             f'<td>{_cash(r.get("cash"))}</td></tr>' for r in ex]
    body += (f'<h3>除權息（台灣 50＋中型 100，共 {len(u.get("codes") or [])} 檔）</h3>'
             + (fold_rows(erows, 10, "<tr><th>日期</th><th>股票</th><th>種類</th><th>現金股利</th></tr>", "筆") if erows
                else '<p class="small">這段期間名單內沒有公告的除權息。台股除息多集中在 6～9 月。</p>')
             + f'<p class="small muted">來源：<a href="https://openapi.twse.com.tw/" target="_blank" rel="noopener">證交所 OpenAPI 除權除息預告表</a>'
               f'（更新 {_ts(v.get("exdiv_ts"))}）；名單：{esc(u.get("source") or "—")}（{esc(str(u.get("asof") or "")[:10])}）。</p>')
    # D. disposal stocks
    pun = v.get("punish") or []
    prow = [f'<tr><td>{esc(r["code"])} {esc(r["name"])}</td><td>{esc(r["board"])}</td><td>{_md(r["from"])}～{_md(r.get("to"))}</td>'
            f'<td class="small">{esc(r.get("step") or "")}；{esc(r.get("why") or "")}</td></tr>' for r in pun]
    body += (f'<h3>處置股（目前 {len(pun)} 檔）</h3>'
             + (fold_rows(prow, 10, "<tr><th>股票</th><th>市場</th><th>處置期間</th><th>原因</th></tr>", "檔") if prow else '<p class="small">目前沒有處置中的股票。</p>')
             + '<p class="small muted">處置股要分盤撮合（每 5 或 20 分鐘成交一次）、部分要預收款券，當沖與融資客被迫退出，成交量通常明顯縮小。'
               f'來源：證交所與櫃買中心 OpenAPI（更新 {_ts(v.get("punish_ts"))}）。</p>')
    # E. statutory deadlines
    drow = [f'<tr><td>{_md(r["date"])}</td><td>{esc(r["what"])}</td><td class="small">{esc(r["why"])}</td></tr>' for r in v.get("deadlines") or []]
    body += "<h3>法定公布期限</h3>" + fold_rows(drow, 6, "<tr><th>期限</th><th>內容</th><th>為什麼重要</th></tr>", "筆")
    body += '<p class="small muted">依證券交易法第 36 條（季報 45 天、年報 3 個月）與月營收每月 10 日前公告的規定推算。</p>'
    errs = v.get("errs") or {}
    if errs:
        body += f'<p class="small muted">這次沒抓到：{esc("、".join(errs))}，沿用上一次的資料（時間如上）。</p>'
    return card("被迫進出的錢：台股日曆", "Taiwan forced-flow calendar", body, "wide")
