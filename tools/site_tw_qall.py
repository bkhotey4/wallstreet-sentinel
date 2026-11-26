"""全部上市櫃第 N 季財報速讀（台股財報頁；2026-11-27）。

為什麼：「財報後解讀（其他市場）」是 AI 一家一家寫的補寫排程，11-10 為了省用量額度暫停，還剩 3,529 家沒寫，使用者看到沒有新資料。
台股這部分其實不需要 AI：公開資訊觀測站的綜合損益表彙總表（電腦端接力，tw_fin_seed）已經有全部上市櫃公司的累計數，
程式算出單季、和去年同季比，就能替每一家貼上同一套規則的「改善中／轉弱中」。港股小型股仍沒有免費的彙總來源，維持暫停。

規則（每家公司同一套，不靠人判斷）：
  改善中＝單季營收年增 > 0，而且營益率比去年同季高（沒有營益率時看毛利率）
  轉弱中＝營收年增 < 0，而且營益率比去年同季低
  其他＝持平／分歧；去年同季資料不足＝不判斷
卡片只放產業統計和變化最大的公司；全部公司在 market/tw_q_all.html，打開才載入（主頁不變重）。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from tools.sitekit import card, esc, fold_rows

LAB = {"up": "改善中", "down": "轉弱中", "mix": "持平／分歧", None: "資料不足"}


BASE_MIN = 1e5        # last year's single-quarter revenue ≥ NT$1 億 (thousand NT$): below it a % change means little
BIG = 5e6             # NT$50 億 (thousand NT$) for the 「營收年增最多與最少」 lists


def comparable(r: Dict) -> bool:
    """Pure: a year-over-year comparison is meaningful only on a real base (11-27: a builder that booked a whole project in one
    quarter showed revenue +173,226% and an operating margin +13,652 points)."""
    return (r.get("rev_ly") or 0) >= BASE_MIN


def label(r: Dict) -> Optional[str]:
    """Pure: 'up' / 'down' / 'mix', or None when last year's same quarter is missing or too small to compare."""
    if "rev_ly" in r and not comparable(r):
        return None
    yoy = r.get("rev_yoy")
    cur, ly = (r.get("om"), r.get("om_ly")) if r.get("om") is not None and r.get("om_ly") is not None else (r.get("gm"), r.get("gm_ly"))
    if yoy is None or cur is None or ly is None:
        return None
    if yoy > 0 and cur > ly:
        return "up"
    if yoy < 0 and cur < ly:
        return "down"
    return "mix"


def _rows(codes_skip: Optional[set] = None) -> Dict:
    from wsb.data import tw_chips as C
    try:
        seed = json.loads(C.FIN_SEED.read_text(encoding="utf-8")) if C.FIN_SEED.exists() else {}
    except (OSError, ValueError):
        seed = {}
    v = C.fin_view(seed.get("snaps") or {})
    try:
        from wsb.config import DATA_DIR
        lists = (json.loads((DATA_DIR / "fullmarket_lists.json").read_text(encoding="utf-8")).get("markets") or {}).get("tw") or []
        ind = {r.get("code"): r.get("ind") for r in lists}
    except Exception:  # noqa: BLE001
        ind = {}
    rows = [{**r, "ind": ind.get(r["code"]) or "其他", "lab": label(r)} for r in v.get("rows") or []]
    return {"q": v.get("q"), "rows": rows, "fetched": seed.get("fetched")}


def industry_table(rows: List[Dict], min_n: int = 8) -> List[Dict]:
    """Pure: per industry with ≥ min_n judged companies — counts and the share improving / weakening."""
    g: Dict[str, Dict] = {}
    for r in rows:
        if r["lab"] is None:
            continue
        x = g.setdefault(r["ind"], {"ind": r["ind"], "n": 0, "up": 0, "down": 0, "mix": 0})
        x["n"] += 1
        x[r["lab"]] += 1
    out = [x for x in g.values() if x["n"] >= min_n]
    for x in out:
        x["up_pct"], x["down_pct"] = x["up"] / x["n"] * 100, x["down"] / x["n"] * 100
    return sorted(out, key=lambda x: x["up_pct"] - x["down_pct"], reverse=True)


def _pct(x, r: Optional[Dict] = None) -> str:
    if x is None or (r is not None and not comparable(r)):
        return "—"
    return f"{x:+.0f}%"


def _pp(a, b, ok: bool = True) -> str:
    if a is None:
        return "—"
    return f"{a:.1f}%" + (f"（{a - b:+.1f}）" if ok and b is not None else "")


def _eps(x) -> str:
    return "—" if x is None else f"{x:.2f}"


def _tr(r: Dict) -> str:
    return (f'<tr data-q="{esc((r["code"] + " " + (r.get("name") or "") + " " + r["ind"]).lower())}"><td><b>{esc(r.get("name") or "")}</b> '
            f'<span class="tk">{esc(r["code"])}</span></td><td class="small">{esc(r["ind"])}</td><td>{esc(LAB[r["lab"]])}</td>'
            f'<td class="r">{r["rev"] / 1e5:,.1f}</td><td class="r">{_pct(r.get("rev_yoy"), r)}</td>'
            f'<td class="r">{_pp(r.get("om"), r.get("om_ly"), comparable(r))}</td><td class="r">{_pp(r.get("gm"), r.get("gm_ly"), comparable(r))}</td>'
            f'<td class="r">{_eps(r.get("eps"))}</td></tr>')


HEAD = ('<tr><th>公司</th><th>產業</th><th>判斷</th><th class="r">單季營收（億元）</th><th class="r">營收年增</th>'
        '<th class="r">營益率（比去年）</th><th class="r">毛利率（比去年）</th><th class="r">單季 EPS（元）</th></tr>')

ALL_JS = ("<script>(function(){var q=document.querySelector('.twqq'),b=document.getElementById('twqall');if(!q||!b)return;var st=0;"
          "function f(){var v=q.value.trim().toLowerCase();b.querySelectorAll('tr[data-q]').forEach(function(r){"
          "r.style.display=!v||r.dataset.q.indexOf(v)>=0?'':'none';});}"
          "function go(){if(st)return;st=1;b.textContent='載入中…';fetch(b.dataset.src).then(function(r){if(!r.ok)throw 0;return r.text();})"
          ".then(function(t){b.innerHTML=t;f();}).catch(function(){st=0;b.textContent='載入失敗，請重新整理頁面。';});}"
          "q.addEventListener('focus',go);q.addEventListener('input',function(){go();f();});"
          "var o=document.querySelector('.twqopen');if(o)o.addEventListener('click',go);})();</script>")


def sec_tw_qall(eng=None) -> str:
    d = _rows()
    rows = d["rows"]
    if not rows or not d["q"]:
        return ""
    judged = [r for r in rows if r["lab"]]
    y, q = d["q"].split("Q")
    if not judged:
        return card(f"全部上市櫃第 {q} 季財報速讀", "All listed companies, quarterly",
                    f'<p class="rimp"><b>一句話看懂：{y} 年第 {q} 季已有 {len(rows)} 家的數字，去年同季的資料還在補，暫時不判斷改善或轉弱。</b></p>', "wide")
    n = {k: sum(r["lab"] == k for r in judged) for k in ("up", "down", "mix")}
    it = industry_table(judged)
    best, worst = (it[0], it[-1]) if it else (None, None)
    lead = (f"一句話看懂：上市櫃 {len(judged)} 家的 {y} 年第 {q} 季（單季）和去年同季比：改善中 {n['up']} 家、轉弱中 {n['down']} 家、"
            f"持平／分歧 {n['mix']} 家。")
    if best and worst and best is not worst:
        lead += (f"改善比例最高的產業是{best['ind']}（{best['up_pct']:.0f}%），轉弱比例最高的是{worst['ind']}（{worst['down_pct']:.0f}%）。"
                 "產業裡大部分公司一起變好或變差，比較像景氣或報價在動；只有少數公司變化，比較像公司自己的事。")
    trs = [f'<tr><td>{esc(x["ind"])}</td><td class="r">{x["n"]}</td><td class="r">{x["up_pct"]:.0f}%</td><td class="r">{x["down_pct"]:.0f}%</td></tr>'
           for x in it]
    ind_html = fold_rows(trs, 12, '<tr><th>產業</th><th class="r">家數</th><th class="r">改善中</th><th class="r">轉弱中</th></tr>', "個產業")
    big = sorted((r for r in judged if r.get("rev_yoy") is not None and r["rev"] >= BIG and comparable(r)), key=lambda r: r["rev_yoy"])
    movers = fold_rows([_tr(r) for r in big[-10:][::-1]], 10, HEAD, "家") + fold_rows([_tr(r) for r in big[:10]], 10, HEAD, "家")
    body = (f'<p class="rimp big2"><b>{esc(lead)}</b></p><h3>各產業</h3>{ind_html}'
            f'<h3>營收年增最多與最少（單季營收 50 億元以上）</h3>{movers}'
            f'<h3>全部 {len(rows)} 家</h3><p><input class="twqq" type="search" placeholder="輸入代號、公司名或產業" style="width:100%;max-width:420px"> '
            f'<button class="twqopen" type="button">打開全部</button></p><div id="twqall" data-src="market/tw_q_all.html" class="small muted">點上面的框或按鈕才載入。</div>'
            + ALL_JS
            + '<p class="note">規則：改善中＝單季營收年增大於 0、營益率比去年同季高（沒有營益率看毛利率）；轉弱中＝營收年減、營益率也比去年低；其他＝持平／分歧。'
              '季報公布的是累計數，這裡用前後兩季相減算出單季，去年同季也一樣算。去年同季營收不到 1 億元的公司（例如一次認列整個建案的營建股）百分比沒有意義，不判斷。金融業沒有毛利率。'
              f'資料：公開資訊觀測站綜合損益表彙總表（上市＋上櫃，電腦端抓取 {esc(d.get("fetched") or "—")}）。'
              '這是同一套規則的描述，不是個股判讀；寫好的 AI 判讀在「財報後白話解讀」。</p>')
    return card(f"全部上市櫃第 {q} 季財報速讀（程式計算）", "All listed companies, quarterly (computed)", body, "wide")


def publish(dest: Path) -> None:
    d = _rows()
    if not d["rows"]:
        return
    order = {"up": 0, "down": 1, "mix": 2, None: 3}
    rows = sorted(d["rows"], key=lambda r: (order[r["lab"]], -(r["rev"] or 0)))
    (dest / "tw_q_all.html").write_text(f'<div class="scroll"><table class="mini"><thead>{HEAD}</thead><tbody>'
                                         + "".join(_tr(r) for r in rows) + "</tbody></table></div>", encoding="utf-8")
