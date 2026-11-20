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


def _rev_seed() -> Dict:
    try:
        f = FEED / "tw_rev_seed.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _seed() -> Dict:
    try:
        f = FEED / "tw_flow_seed.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _f1(x) -> str:
    return "—" if not x else f"{x:.1f}"


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


# ============================================================ 2 估值在自己歷史的位置
def _bucket(p: float) -> str:
    return "前 20%（自己歷史裡偏貴的一端）" if p >= 80 else "後 20%（自己歷史裡偏便宜的一端）" if p <= 20 else "中間"


def val_lead(v: Dict) -> str:
    b = v.get("bands") or []
    e = v.get("erp_now")
    parts = []
    if b:
        hi = sum(r["pct"] >= 80 for r in b)
        lo = sum(r["pct"] <= 20 for r in b)
        parts.append(f"台灣 50＋中型 100 裡算得出歷史的 {len(b)} 檔，有 {hi} 檔的本益比（虧損公司用淨值比）在自己 5 年歷史的前 20%，{lo} 檔在後 20%")
    if e:
        parts.append(f"中位數公司的盈餘殖利率比 10 年期公債高 {e['erp']:.2f} 個百分點"
                     + (f"，在過去 {len(v.get('erp') or [])} 個月裡是第 {v['erp_pct']:.0f} 百分位（數字越低代表股票相對債券越不划算）" if v.get("erp_pct") is not None else ""))
    if e and e.get("tsmc_pe"):
        parts.append(f"台積電本益比 {e['tsmc_pe']:.1f} 倍" + (f"，在自己 10 年歷史的第 {v['tsmc_pct']:.0f} 百分位" if v.get("tsmc_pct") is not None else ""))
    if not parts:
        return ""
    return "一句話看懂：" + "；".join(parts) + "。"


def sec_tw_valband(eng=None, v: Optional[Dict] = None) -> str:
    if v is None:
        try:
            from wsb.data import tw_desk as D
            v = D.val_view()
        except Exception:  # noqa: BLE001
            return ""
    lead = val_lead(v)
    if not lead:
        return ""
    body = f'<p class="rimp big2"><b>{T(esc(lead), "")}</b></p>'
    e, erp = v.get("erp_now"), v.get("erp") or []
    if e:
        body += ("<h3>大盤：股票對債券划不划算（股權風險溢酬）</h3>"
                 f'<p class="small">{_md(e["date"])}：上市股票本益比中位數 {e["pe_med"]:.2f} 倍 → 盈餘殖利率 {e["ey"]:.2f}%；'
                 f'10 年期公債 {e["y10"]:.2f}% → 差距 {e["erp"]:.2f} 個百分點。'
                 + (f'台積電本益比 {e["tsmc_pe"]:.2f} 倍 → 對公債差距 {e["tsmc_erp"]:.2f} 個百分點。' if e.get("tsmc_erp") is not None else "")
                 + '</p>')
        yrs = {}
        for r in erp:
            yrs[r["date"][:4]] = r
        rows = [f'<tr><td>{esc(k)}</td><td>{r["pe_med"]:.1f}</td><td>{r["ey"]:.2f}%</td><td>{r["y10"]:.2f}%</td><td>{r["erp"]:.2f}</td>'
                f'<td>{_f1(r.get("tsmc_pe"))}</td></tr>' for k, r in sorted(yrs.items(), reverse=True)]
        body += fold_rows(rows, 6, "<tr><th>年（年底；今年為最新）</th><th>本益比中位數</th><th>盈餘殖利率</th><th>10 年公債</th><th>差距（百分點）</th><th>台積電本益比</th></tr>", "年")
        body += ('<p class="small muted">用「中位數公司」而不是加權指數，是因為證交所沒有公布加權指數的本益比；台積電另外列，因為它佔大盤四成。'
                 '來源：證交所 BWIBBU（每月最後一個交易日）、中央銀行 10 年期公債殖利率（月）。</p>')
    rel = v.get("rel")
    if rel:
        body += (f'<h3>台積電 vs 費城半導體指數</h3><p class="small">台積電股價÷費半指數的比值，在過去 {rel["n"]} 個交易日是第 {rel["pct"]:.0f} 百分位'
                 f'（{_md(rel["date"])}）；一年來台積電 {rel["tsmc_1y"]:+.1f}%、費半 {rel["sox_1y"]:+.1f}%。比值高代表台積電比全球半導體股強。'
                 '費半成分股的合計本益比沒有免費來源，所以用股價相對強弱代替。來源：Yahoo Finance 日線。</p>')
    b = v.get("bands") or []
    if b:
        rows = [f'<tr><td>{esc(r["code"])} {esc(r["name"])}</td><td>{esc(r["metric"])}</td><td>{r["now"]:.2f}</td><td>{r["pct"]:.0f}</td>'
                f'<td class="small">{r["lo"]:.1f}～{r["med"]:.1f}～{r["hi"]:.1f}</td><td class="small">{esc(_bucket(r["pct"]))}</td></tr>' for r in b]
        body += (f'<h3>每檔股票在自己 5 年歷史的位置（{len(b)} 檔）</h3>'
                 + fold_rows(rows, 15, "<tr><th>股票</th><th>指標</th><th>現在</th><th>百分位</th><th>最低～中位～最高</th><th>位置</th></tr>", "檔"))
    body += (f'<p class="small muted">每檔股票和自己的歷史比，不和別的公司比；歷史是每月最後一個交易日的本益比（共 {v.get("months", 0)} 個月，最新 {esc(v.get("latest") or "—")}），'
             f'至少 24 個月才列。百分位只描述位置，不代表接下來會漲或跌。資料更新 {_ts(v.get("vh_ts"))}。</p>')
    if v.get("months", 0) < 60:
        body += f'<p class="small muted">5 年歷史還在補（目前 {v.get("months", 0)}／60 個月）；每次更新向證交所補抓幾個月，避免連太快被擋。</p>'
    return card("估值：每檔股票在自己歷史的位置", "Valuation bands", body, "wide")


# ============================================================ 3 月營收與 AI 供應鏈熱度
def _pp(x: Optional[float], d: int = 1) -> str:
    return "—" if x is None else f"{x:+.{d}f}%"


def _p0(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:.0f}%"


def _a1(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:+.1f}"


def _ym(ym: str) -> str:
    return f"{int(ym[:4])} 年 {int(ym[5:7])} 月"


def rev_lead(v: Dict) -> str:
    L = [x for x in v.get("layers") or [] if x.get("yoy3_med") is not None]
    if not L:
        return ""
    hot = max(L, key=lambda x: x["yoy3_med"])
    cold = min(L, key=lambda x: x["yoy3_med"])
    s = f"一句話看懂：{_ym(v['latest'])}營收，台灣 50＋中型 100 有 {v['yoy_pos']:.0f}% 的公司比去年同月成長"
    if v.get("breadth") is not None:
        s += f"、{v['breadth']:.0f}% 的公司近 3 個月成長在加速"
    s += f"；AI 供應鏈裡最熱的是{hot['name']}（近 3 個月年增中位數 {hot['yoy3_med']:+.0f}%）"
    if cold is not hot:
        s += f"，最冷的是{cold['name']}（{cold['yoy3_med']:+.0f}%）"
    c = v.get("capex")
    if c and c.get("yoy") is not None:
        s += f"。美國雲端巨頭近 12 個月資本支出年增 {c['yoy']:+.0f}%（到 {esc(str(c.get('q') or ''))}），是這條鏈的源頭"
    return s + "。"


def sec_tw_revheat(eng=None, v: Optional[Dict] = None) -> str:
    if v is None:
        try:
            from wsb.data import tw_desk as D
            v = D.rev_view(seed=_rev_seed())
        except Exception:  # noqa: BLE001
            return ""
    lead = rev_lead(v or {})
    if not lead:
        return ""
    body = f'<p class="rimp big2"><b>{T(esc(lead), "")}</b></p>'
    rows = []
    for L in v["layers"]:
        rows.append(f'<tr><td>{esc(L["name"])}</td><td>{L["n"]}</td><td>{_pp(L["yoy3_med"], 0)}</td>'
                    f'<td>{_p0(L["acc_share"])}</td>'
                    f'<td class="small">{esc("、".join(t["name"] + " " + _pp(t["yoy3"], 0) for t in L["rows"][:3]))}</td></tr>')
    body += "<h3>AI 供應鏈各層熱度（近 3 個月營收年增）</h3>" + fold_rows(
        rows, 9, "<tr><th>層</th><th>公司數</th><th>年增中位數</th><th>加速中的比例</th><th>最熱的三家</th></tr>", "層")
    det = []
    for L in v["layers"]:
        trs = []
        for t in L["rows"]:
            nc = (L.get("now") or {}).get(t["code"]) or {}
            trs.append(f'<tr><td>{esc(t["code"])} {esc(t["name"])}</td><td>{_pp(t["yoy"])}</td><td>{_pp(t["yoy3"])}</td><td>{_pp(t["prev3"])}</td>'
                       f'<td>{_a1(t["accel"])}</td><td>{_pp(nc.get("qtd_yoy"))}</td><td>{_pp(nc.get("q_vs_prev"))}</td></tr>')
        miss = f'<p class="small muted">營收資料裡找不到：{esc("、".join(L["missing"]))}</p>' if L["missing"] else ""
        det.append(f'<details class="sgx"><summary>{esc(L["name"])}（{L["n"]} 家）</summary>' + fold_rows(
            trs, 10, "<tr><th>公司</th><th>當月年增</th><th>近 3 月年增</th><th>前 3 月年增</th><th>加速（百分點）</th><th>本季至今年增</th><th>本季推估比上季</th></tr>", "家")
                   + miss + "</details>")
    body += "<h3>每家公司（點開看）</h3>" + "".join(det)
    body += ('<p class="small muted">「加速」＝近 3 個月平均年增 − 再往前 3 個月平均年增。「本季推估比上季」是假設：用本季已公布的月份平均推到整季，'
             '再和上一季比；季中最後一個月常有出貨集中或遞延，誤差可能很大。法說會的財測沒有免費的結構化資料，所以這裡不和公司財測比；'
             '台積電等公司的財測請看 Gemini 每週核對。分層是本站依主要業務整理的名單。</p>')
    trs = sorted((t for t in v.get("trends") or [] if t["accel"] is not None), key=lambda t: -t["accel"])
    rows2 = [f'<tr><td>{esc(t["code"])} {esc(t["name"])}</td><td>{_pp(t["yoy"])}</td><td>{_pp(t["yoy3"])}</td><td>{_a1(t["accel"])}</td></tr>' for t in trs]
    if rows2:
        body += (f'<h3>台灣 50＋中型 100：營收加速最多到最少（{len(rows2)} 家）</h3>'
                 + fold_rows(rows2, 10, "<tr><th>公司</th><th>當月年增</th><th>近 3 月年增</th><th>加速（百分點）</th></tr>", "家"))
    body += (f'<p class="small muted">來源：公開資訊觀測站每月營收彙總表（上市、上櫃，共 {v.get("n_months", 0)} 個月）與證交所／櫃買 OpenAPI；'
             f'美國雲端巨頭資本支出：SEC 財報（微軟、Alphabet、亞馬遜、Meta、甲骨文）。更新 {_ts(v.get("ts"))}'
             + (f'；雲端讀不到的月份用本站電腦端 {esc(v["seed_at"])} 抓的同一份資料補上' if v.get("seed_at") else "") + '。</p>')
    return card("月營收：AI 供應鏈哪一層在加速", "Monthly revenue heat map", body, "wide")


# ============================================================ 4 我們的判斷準不準（校準）
def _pc0(x: Optional[float]) -> str:
    return "—" if x is None else f"{x * 100:.0f}%"


def _b3(t: Dict) -> str:
    return f"{t['brier'] / t['np']:.3f}" if t.get("np") else "—"


def calib_lead(v: Dict) -> str:
    e = v.get("earn") or {}
    parts = []
    if e.get("n"):
        bias = {b["k"]: b for b in e.get("bias") or []}
        up = bias.get("上修")
        parts.append(f"財報預覽已有 {e['n']} 筆對得出答案：我們押的最可能結果只對了 {_pc0(e['top_hit'])}，"
                     f"整體分數比「每次都照過去的平均比例猜」還差（技巧分數 {e['skill']:+.2f}，0 代表一樣、負的代表比較差）")
        if up and up["real"] - up["said"] > 0.1:
            parts.append(f"最大的偏差是太悲觀：我們給「財測上修」平均 {_pc0(up['said'])} 的機率，實際上修的比例是 {_pc0(up['real'])}")
    bt = v.get("by_topic") or {}
    nb = sum(t["n"] for t in bt.values())
    if nb:
        parts.append(f"有日期的總經與深度判斷已到期 {nb} 題、對 {sum(t['hit'] for t in bt.values())} 題，另有 {v.get('pending', 0)} 題還沒到期")
    return ("一句話看懂：" + "；".join(parts) + "。") if parts else ""


def sec_calib(eng=None, v: Optional[Dict] = None) -> str:
    if v is None:
        try:
            from wsb.data import tw_desk as D
            v = D.calib_view(FEED)
        except Exception:  # noqa: BLE001
            return ""
    lead = calib_lead(v or {})
    if not lead:
        return ""
    body = f'<p class="rimp big2"><b>{T(esc(lead), "")}</b></p>'
    e = v.get("earn") or {}
    if e.get("n"):
        rows = [f'<tr><td>{esc(b["k"])}</td><td>{_pc0(b["said"])}</td><td>{_pc0(b["real"])}</td>'
                f'<td>{"我們給得太低" if b["real"] - b["said"] > 0.1 else "我們給得太高" if b["said"] - b["real"] > 0.1 else "差不多"}</td></tr>' for b in e["bias"]]
        body += ("<h3>財報預覽：說的機率 vs 實際發生的比例</h3>"
                 + fold_rows(rows, 3, "<tr><th>結果</th><th>我們給的平均機率</th><th>實際比例</th><th>判讀</th></tr>", "項"))
        rows = [f'<tr><td>{b["lo"] * 100:.0f}%～{b["hi"] * 100:.0f}%</td><td>{b["n"]}</td><td>{_pc0(b["said"])}</td><td>{_pc0(b["hit"])}</td></tr>' for b in e["buckets"]]
        body += ("<h3>越有把握的時候越準嗎？（看我們押的最可能結果）</h3>"
                 + fold_rows(rows, 4, "<tr><th>把握程度</th><th>筆數</th><th>平均說的把握</th><th>實際命中</th></tr>", "組"))
        body += (f'<p class="small muted">Brier 分數 {e["brier"]:.3f}（三種結果，0 最好、2 最差）；如果每次都照實際的平均比例猜，分數是 {e["brier_ref"]:.3f}。'
                 '照這個結果，財報預覽給「上修」的機率偏低、「下修」偏高，只有一半把握時命中率最差；這是財報預覽最需要修正的地方。</p>')
    bt = v.get("by_topic") or {}
    if bt:
        rows = [f'<tr><td>{esc(k)}</td><td>{t["n"]}</td><td>{t["hit"]}</td><td>{_pc0(t["hit"] / t["n"])}</td>'
                f'<td>{_pc0(t["said"] / t["np"]) if t["np"] else "沒標機率"}</td><td>{_b3(t)}</td></tr>' for k, t in bt.items()]
        body += ("<h3>有日期的判斷（到期才算）</h3>"
                 + fold_rows(rows, 6, "<tr><th>來源</th><th>已到期</th><th>對</th><th>命中率</th><th>平均說的把握</th><th>Brier</th></tr>", "項"))
        calls = sorted(v.get("binary") or [], key=lambda c: str(c.get("by") or ""), reverse=True)
        crow = [f'<tr><td>{esc(str(c.get("by") or ""))}</td><td class="small">{esc(c["claim"])}</td><td>{"對" if c["hit"] else "錯"}</td>'
                f'<td>{_pc0(c["p"])}</td></tr>' for c in calls]
        body += fold_rows(crow, 5, "<tr><th>到期</th><th>判斷</th><th>結果</th><th>當時的把握</th></tr>", "題")
    body += (f'<p class="small muted">來源：本站 research_feed 的 forecast.json、tw_forecast.json、deep.json、earn_preview.json（最新 {esc(v.get("updated") or "—")}）。'
             '「無法判定」的不算；題數還少時命中率會大幅跳動，30 題以上才比較有意義。</p>')
    return card("我們的判斷準不準", "Call calibration", body, "wide")
