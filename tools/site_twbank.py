"""台灣「央行與資金」頁：台灣家庭與銀行壓力卡。資料與規則見 wsb/data/tw_bank.py。"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from tools.sitekit import T, card, esc, num, spark


def _v(eng) -> Dict:
    c = getattr(eng, "_twbank_view", None)
    if c is None:
        try:
            from wsb.data import tw_bank as B
            c = B.view(eng)
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._twbank_view = c
        except Exception:  # noqa: BLE001
            pass
    return c


def _ser(rows) -> pd.Series:
    return pd.Series([r[1] for r in rows], index=pd.to_datetime([r[0] for r in rows]))


def lead(v: Dict) -> str:
    s, q, n = v.get("sme"), v.get("quality"), v.get("npl")
    parts = []
    if n and n.get("ratio") is not None:
        parts.append(f"本國銀行整體逾放比 {n['ratio']:.2f}%")
    if s:
        parts.append(f"中小企業逾放比 {s['now']:.2f}%（{s['since']} 年以來第 {num(s['pct'], 0)} 百分位）")
    if not parts:
        return ""
    tail = ("；" + "、".join(v["hot"]) + "落在自己歷史最高一成，要留意。") if v.get("hot") else "，都在自己歷史的低檔，銀行壞帳壓力現在不高。"
    return "一句話看懂：" + "，".join(parts) + tail


def sec_tw_bank(eng) -> str:
    from wsb.data import tw_bank as B
    v = _v(eng) or {}
    s, q, n, la = (v.get(k) for k in ("sme", "quality", "npl", "land"))
    if not any((s, q, n, la)):
        return ""
    body = f'<p class="rimp big2"><b>{T(lead(v), "")}</b></p>'
    why = ("在美國，壓力先出現在車貸；在台灣，最值得看的是中小企業和不動產。中小企業僱用了台灣大部分的上班族，它們借的錢還不出來，"
           "通常代表訂單變少、老闆在撐；銀行放款又有很大一塊押在土地和房子上，房市一冷，擔保品就縮水。")
    body += f'<p>{T(why, "")}</p>'
    kv = []
    if s:
        kv.append(f'<div><span class="muted">中小企業逾放比</span><b>{s["now"]:.2f}%</b> <span class="small muted">一年前 {num(s["ago"], 2)}%・最高 {s["max"]:.2f}%（{esc(s["max_date"])}）・{esc(s["date"])}</span></div>')
    if q:
        kv.append(f'<div><span class="muted">非「正常」放款占比</span><b>{q["now"]:.2f}%</b> <span class="small muted">一年前 {num(q["ago"], 2)}%・{q["since"]} 年以來第 {num(q["pct"], 0)} 百分位・{esc(q["date"])}</span></div>')
    if la:
        kv.append(f'<div><span class="muted">以土地擔保的放款占比</span><b>{la["share"]:.1f}%</b> <span class="small muted">約 {la["land"] / 1e6:.1f} 兆元'
                  + (f'・一年前 {la["share_1y"]:.1f}%' if la.get("share_1y") is not None else "") + f'・{esc(la["month"])}</span></div>')
    body += f'<div class="kv">{"".join(kv)}</div>'
    det = ""
    if n:
        tr = "".join(f'<tr><td>{esc(b["name"])}</td><td class="r"><b>{b["npl"]:.2f}%</b></td><td class="r">{num(b["cover"], 0)}%</td><td class="r">{b["loans"] / 100:,.0f}</td></tr>'
                     for b in n["top"])
        det += (f'<h3>逾放比最高的 5 家（放款 1,000 億元以上）<span class="muted small">資料月 {esc(n["month"])}</span></h3>'
                f'<div class="scroll"><table class="mini"><thead><tr><th>銀行</th><th class="r">逾放比</th><th class="r">備抵呆帳覆蓋率</th><th class="r">放款（億元）</th></tr></thead><tbody>{tr}</tbody></table></div>'
                '<p class="small">覆蓋率＝先存起來準備打銷壞帳的錢 ÷ 壞帳；超過 100% 代表壞帳全部打掉也還有餘。台灣銀行業普遍好幾倍，是一層很厚的墊子。</p>')
    if la:
        tr = "".join(f'<tr><td>{esc(b["name"])}</td><td class="r"><b>{b["share"]:.1f}%</b></td><td class="r">{b["loans"] / 100:,.0f}</td></tr>' for b in la["top"])
        det += (f'<h3>以土地擔保放款占比最高的 5 家 <span class="muted small">資料月 {esc(la["month"])}</span></h3>'
                f'<div class="scroll"><table class="mini"><thead><tr><th>銀行</th><th class="r">土地擔保占放款</th><th class="r">放款（億元）</th></tr></thead><tbody>{tr}</tbody></table></div>'
                '<p class="small">押土地的放款多半是建商買地、蓋房子的錢（土建融）。房子賣不掉時，建商最先出問題，借錢給它們的銀行跟著受傷。'
                f'官方只公布最新一個月，本站每月存一份，目前存了 {la["months"]} 個月，一年後才能看趨勢。</p>')
    det += ('<p class="small"><b>連帶影響</b>：中小企業逾放上升，通常先出現在出口和內需服務業，接著是裁員、消費變弱；'
            '土建融出問題，建商和建材（水泥、鋼筋）、營造股先受傷，銀行會收緊房貸，房價和交易量跟著冷。'
            '央行的選擇性信用管制（限制第二戶以上房貸成數）就是在壓這一塊。</p>')
    sp = "".join(f'<div><div class="small muted">{lab}</div>{spark(_ser(x["hist"]), 160, 36)}</div>'
                 for lab, x in (("中小企業逾放比（%）", s), ("非正常放款占比（%）", q)) if x and len(x.get("hist") or []) > 5)
    body += (f'<details class="sgx"><summary>{T("看各銀行排行與連帶影響", "Details")}</summary>{det}'
             + (f'<div class="g3">{sp}</div>' if sp else "") + "</details>")
    body += (f'<p class="note">{T("燈號：中小企業逾放比（2008 年起，月）或非「正常」放款占比（2013 年起，季）落在自己歷史最高 10% → 🟡。信用卡逾期的官方檔案停在 2024 年 11 月，太舊所以沒放。", "")}'
             f'資料：<a href="{B.PAGE}" target="_blank" rel="noopener">金管會銀行局統計</a>（開放資料 CSV）。描述現況，不是預測，也不是投資建議。</p>')
    h = card(f"{v.get('emoji', '')} 台灣家庭與銀行壓力：中小企業、壞帳、土地放款", "Taiwan bank stress", body, "wide",
             sub="中小企業逾放比、放款資產品質、各銀行逾放與土地擔保放款")
    return h.replace('<section class="card', '<section id="twbank" class="card', 1)
