"""台股頁：規則 v1 紙上交易成績單（2026-11-21 起）。資料：tools/tw_paper.py（每個交易日收盤後重算一次）。
只是規則的紙上記帳（假設本金 100 萬元），不是任何人的持股，也不是建議。"""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from tools.sitekit import T, card, esc, fold_rows, line_chart

ENOUGH = 30


def _p(x: Optional[float], d: int = 1, sign: bool = True) -> str:
    if x is None:
        return "—"
    return f"{x * 100:+.{d}f}%" if sign else f"{x * 100:.{d}f}%"


def _nm(r: Dict) -> str:
    return esc(f'{r["sym"].replace(".TW", "")} {r.get("name") or ""}'.strip())


def _days(d: Dict) -> int:
    return max(len((d.get("main") or {}).get("equity") or []) - 1, 0)


def lead(d: Dict) -> str:
    m = d.get("main") or {}
    n_open, closed = len(m.get("open") or []), m.get("closed") or 0
    start = str(d.get("start") or "")
    if _days(d):
        base = (f"一句話看懂：規則 v1 從 {start} 收盤開始紙上記帳（假設本金 100 萬元），到 {m.get('data_end')} 共 {_days(d)} 個交易日，"
                f"主帳本 {_p(m.get('total'))}，同期 0050 {_p(m.get('bench_total'))}；")
    else:
        base = f"一句話看懂：規則 v1 從 {start} 收盤開始紙上記帳（假設本金 100 萬元），今天是第一天，第一筆紙上成交最快在下一個交易日開盤；"
    if not n_open and not closed:
        mk = d.get("mkt") or {}
        why = (f"加權指數 {mk.get('twii'):,.0f} 點（{mk.get('date', '')}）在 200 日線 {mk.get('ma200'):,.0f} 點之下，創 50 日新高又放量的股票很少"
               if mk.get("ma200") and mk.get("twii") and mk["twii"] < mk["ma200"] else "還沒有股票同時創 50 日新高又放量")
        return base + f"目前還沒有任何進場訊號（{why}）。"
    return base + f"目前紙上持有 {n_open} 檔、已出場 {closed} 筆。"


def _signals(m: Dict) -> str:
    rows = [f'<tr><td>{_nm(x)}</td><td class="num">{x["close"]:,.2f}</td><td>{"這次不會成交（名額滿、濾網關或暫停中）" if x.get("blocked") else "下一個交易日開盤紙上成交"}</td></tr>'
            for x in m.get("next") or []]
    head = "<tr><th>股票</th><th>今天收盤</th><th>下一步</th></tr>"
    return ("<h3>今天收盤出現的進場訊號</h3>" + fold_rows(rows, 8, head, "檔")) if rows else ""


def _open(m: Dict) -> str:
    rows = [f'<tr><td>{_nm(o)}</td><td>{esc(o["since"])}</td><td class="num">{o["entry"]:,.2f}</td><td class="num">{o["stop"]:,.2f}</td>'
            f'<td class="num">{_p(o["ret"])}</td><td class="num">{_p(o.get("w"), 0, False)}</td>'
            f'<td>{"已出一半；" if o.get("half_out") else ""}{esc(o["why"]) + "（下一個交易日開盤）" if o.get("exit_next_open") else ""}</td></tr>'
            for o in m.get("open") or []]
    head = "<tr><th>股票</th><th>進場日</th><th>進場價</th><th>停損</th><th>到今天</th><th>占本金</th><th>狀態</th></tr>"
    return ("<h3>紙上持有中</h3>" + fold_rows(rows, 8, head, "檔")) if rows else "<p class='muted'>目前沒有紙上持有的股票。</p>"


def _fills(m: Dict, kind: Dict[str, str]) -> str:
    rows = []
    for f in reversed(m.get("fills") or []):
        extra = (f'停損 {f["stop"]:,.2f}；占本金 {_p(f.get("w"), 0, False)}；大盤濾網{"開" if f.get("mkt_ok") else "關"}' if f["kind"] == "entry"
                 else (f'這筆整體 {_p(f["ret"])}' if f.get("ret") is not None else ""))
        rows.append(f'<tr><td>{esc(f["date"])}</td><td>{_nm(f)}</td><td>{esc(kind.get(f["kind"], f["kind"]))}</td>'
                    f'<td class="num">{f["px"]:,.2f}</td><td>{esc(extra)}</td></tr>')
    head = "<tr><th>日期</th><th>股票</th><th>動作</th><th>紙上成交價</th><th>說明</th></tr>"
    return ("<h3>每一筆紙上成交</h3>" + fold_rows(rows, 10, head, "筆")) if rows else ""


def _compare(d: Dict) -> str:
    rows = []
    for key, nm in (("main", "主帳本（不加濾網）"), ("filter", "對照（加權指數在 200 日線上才進場）")):
        v = d.get(key) or {}
        rows.append(f'<tr><td>{nm}</td><td class="num">{_p(v.get("total"))}</td><td class="num">{_p(v.get("maxdd"))}</td>'
                    f'<td class="num">{v.get("closed", 0)}</td><td class="num">{_p(v.get("hit"), 0, False)}</td><td class="num">{_p(v.get("avg"))}</td></tr>')
    head = "<tr><th>帳本</th><th>累計</th><th>最大回落</th><th>已出場筆數</th><th>賺錢的比例</th><th>每筆平均</th></tr>"
    return "<h3>兩本帳對照</h3>" + fold_rows(rows, 2, head)


def _chart(m: Dict) -> str:
    eq = m.get("equity") or []
    if len(eq) < 10:
        return f"<p class='muted'>走勢圖要累積 10 個交易日才畫（目前 {max(len(eq) - 1, 0)} 天）。</p>"
    s = pd.Series([v * 100 for _, v in eq], index=pd.to_datetime([d for d, _ in eq]))
    return line_chart("twpaper", s, "紙上帳本淨值（開始＝100）", 1)


def sec_tw_paper(eng=None) -> str:
    try:
        from tools import tw_paper as TP
        d = TP.refresh()
    except Exception:  # noqa: BLE001
        return ""
    if not d.get("main"):
        return ""
    m = d["main"]
    closed = m.get("closed") or 0
    honest = (f"已出場 {closed} 筆，還不到 {ENOUGH} 筆：這段成績主要是運氣，不能拿來判斷規則好壞；要累積到 {ENOUGH} 筆左右才開始有意義。"
              if closed < ENOUGH else f"已出場 {closed} 筆，可以開始和回測的樣本外成績比較。")
    mk = d.get("mkt") or {}
    filt = (f"大盤濾網：加權指數 {mk['twii']:,.0f} 點，200 日線 {mk['ma200']:,.0f} 點 → {'在線上（對照帳本可以開新部位）' if mk['twii'] > mk['ma200'] else '在線下（對照帳本暫停開新部位）'}（{esc(mk.get('date', ''))}）。"
            if mk.get("twii") and mk.get("ma200") else "")
    rules = ("規則（全部來自 tools/tw_rules_backtest.py 的同一套程式）：收盤突破過去 50 日最高、成交量大於 20 日均量 1.5 倍 → 下一個交易日開盤紙上成交；"
             "每筆最多虧本金 1%（由停損距離反推金額）、單檔最多 20%、同時最多 8 檔；停損 −7.5%；漲 20% 先出一半、剩下的停損拉到成本，"
             "收盤跌破 20 日均線或從最高回落 8% 出場；60 個交易日沒漲到 20% 就出場；本金從高點回落 10% 暫停開新部位 10 個交易日。"
             "成本：手續費 0.1425%、證交稅 0.3%。開盤漲停不進、跌停鎖死當天出不掉。"
             f"名單在 {esc((d.get('universe') or {}).get('frozen', ''))} 凍結（{(d.get('universe') or {}).get('n', 0)} 檔），之後不改。"
             "價格用原始日線（不還原權息），除息當天的跌幅會算進去、股利沒加回，所以帳上報酬會比實際少一點。")
    stale = f"<p class='note'>⚠️ 這次更新沒成功（{esc(d['err'])}），下面是 {esc(d.get('computed_at', ''))} 的結果。</p>" if d.get("err") else ""
    body = (f'<p class="rimp big2"><b>{T(lead(d), "")}</b></p>' + stale
            + f'<p class="note">{T(honest, "")}{(" " + filt) if filt else ""}</p>'
            + _chart(m) + _signals(m) + _open(m) + _fills(m, TP.KIND) + _compare(d)
            + f'<details class="sgx"><summary>{T("規則與做法", "Rules")}</summary><p class="note">{T(rules, "")}</p></details>'
            + f'<p class="note">更新：台北 {esc(d.get("computed_at", ""))}；價格資料到 {esc(m.get("data_end", ""))}。來源：{esc(d.get("src", ""))}。'
              "這是規則的紙上記帳，不下單，也不是任何人的持股或建議。</p>")
    return card("規則 v1 紙上交易成績單", "Rule v1 paper-trading record", body, "wide")
