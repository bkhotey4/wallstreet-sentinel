"""人類溫度計頁：移民與民意。人變少（移民）和人不滿（民調）怎麼傳到就業、物價和政策。資料與規則見 wsb/data/migration_polls.py。"""
from __future__ import annotations

import html
from typing import Dict

import pandas as pd

from tools.sitekit import card, num, spark


def _e(x) -> str:
    return html.escape(str(x if x is not None else ""))


def _ser(rows) -> pd.Series:
    return pd.Series([r[1] for r in rows], index=pd.to_datetime([r[0] for r in rows]))


def _v(eng) -> Dict:
    c = getattr(eng, "_mig_view", None)
    if c is None:
        try:
            from wsb.data import migration_polls as MP
            c = MP.view(eng)
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._mig_view = c
        except Exception:  # noqa: BLE001
            pass
    return c


def story(m: Dict) -> str:
    """The plain paragraph follows the data's direction instead of assuming immigration fell."""
    base = "很多移民在工地、農場、餐廳和照護機構工作。"
    if m["fb_d"] < 0:
        return (base + "人變少，這些工作找不到人，老闆只好加薪或少接案，最後可能變成房子蓋得慢、外食變貴。"
                "同時每個月新增的工作數也會變少，這不一定是經濟變差，可能只是找工作的人變少了。")
    s = base + "官方家戶調查顯示，外國出生的勞動力反而比一年前多"
    if (m.get("nb_d") or 0) < 0:
        s += "，減少的是本國出生的人（多半是退休的嬰兒潮世代）"
    s += "。所以如果新聞說「移民變少造成缺工」，這份資料目前不支持；不過這個調查樣本有限，也受人口估計影響，看方向比看大小可靠。"
    if m.get("hot"):
        s += f"{'、'.join(m['hot'])}的時薪確實漲得比整體快，原因可能是需求強，不一定是缺移民。"
    return s


def lead(m: Dict, a: Dict) -> str:
    parts = []
    if m:
        w = max(m.get("wages") or [], key=lambda x: x["gap"], default=None)
        parts.append(f"外國出生的勞動力比一年前{'少' if m['fb_d'] < 0 else '多'} {abs(m['fb_d']) / 10:,.0f} 萬人"
                     + (f"，{w['zh']}時薪年增比整體{'高' if w['gap'] >= 0 else '低'} {abs(w['gap']):.1f} 個百分點" if w else ""))
    if a:
        parts.append(f"總統支持度平均 {a['app']:.0f}%（{a['n']} 家民調）" + (f"，比 3 個月前 {a['chg90']:+.0f}" if a.get("chg90") is not None else ""))
    return "一句話看懂：" + "；".join(parts) + "。" if parts else ""


def sec_migration_polls(eng) -> str:
    v = _v(eng) or {}
    m, a = v.get("mig"), v.get("app")
    if not m and not a:
        return ""
    body = f'<p class="rimp big2"><b>{_e(lead(m, a))}</b></p>'
    if m:
        kv = (f'<div><span class="muted">外國出生勞動力</span><b>{m["fb"] / 10:,.0f} 萬人</b> <span class="small muted">一年 {m["fb_d"] / 10:+,.0f} 萬</span></div>'
              f'<div><span class="muted">占全部勞動力</span><b>{m["share"]:.1f}%</b> <span class="small muted">一年前 {m["share_1y"]:.1f}%</span></div>')
        if m.get("nb_d") is not None:
            kv += f'<div><span class="muted">本國出生勞動力</span><b>{m["nb_d"] / 10:+,.0f} 萬</b> <span class="small muted">一年增減</span></div>'
        if m.get("fb_u") is not None:
            kv += f'<div><span class="muted">失業率 外國／本國出生</span><b>{m["fb_u"]:.1f}% ／ {m["nb_u"]:.1f}%</b></div>'
        if m.get("pay3") is not None:
            kv += (f'<div><span class="muted">每月新增工作（3 個月平均）</span><b>{m["pay3"]:+,.0f} 千</b>'
                   f' <span class="small muted">勞動力每月約 {m["lf_m"]:+,.0f} 千</span></div>')
        wr = "".join(f'<tr><td>{_e(w["zh"])}</td><td class="r">{w["yoy"]:.1f}%</td><td class="r"><b>{w["gap"]:+.1f}</b></td></tr>' for w in m.get("wages") or [])
        if m.get("wage_all") is not None:
            wr += f'<tr><td class="muted">民間平均</td><td class="r muted">{m["wage_all"]:.1f}%</td><td class="r muted">—</td></tr>'
        body += (f'<h3>{m["emoji"]} 移民：{_e(m["state"])} <span class="muted small">資料月 {_e(m["asof"])}</span></h3>'
                 + f'<p>{_e(story(m))}</p>'
                 f'<div class="kv">{kv}</div>'
                 + (f'<div class="scroll"><table class="mini"><thead><tr><th>移民比例高的行業</th><th class="r">時薪年增</th><th class="r">比整體多（百分點）</th></tr></thead>'
                    f'<tbody>{wr}</tbody></table></div>' if wr else "")
                 + (f'<div class="small muted">外國出生勞動力一年增減（千人，近 5 年）</div>{spark(_ser(m["fb_hist"]), 160, 36)}' if m.get("fb_hist") else ""))
    if a:
        rec = "".join(f'<li>{_e(p["end"])} {_e(p["who"])}：支持 {p["app"]:.0f}%、不支持 {p["dis"]:.0f}%'
                      + (f'（<a href="{_e(p["url"])}" target="_blank" rel="noopener noreferrer">原文</a>）' if p["url"].startswith("https://") else "") + "</li>"
                      for p in a.get("recent") or [])
        body += (f'<h3>民意：總統支持度 {a["app"]:.0f}%，不支持 {a["dis"]:.0f}% <span class="muted small">最近 {a["win"]} 天 {a["n"]} 家，最新 {_e(a["latest"])}</span></h3>'
                 '<p>支持度本身不會讓股市漲跌，但它會改變政府接下來做什麼：支持度低時，執政者常調整移民、關稅或預算的方向，'
                 '國會也比較難通過法案。政策方向越不清楚，企業越傾向延後招人和投資，這會慢慢傳到就業和獲利。</p>'
                 + (spark(_ser(a["hist"]), 160, 36) if len(a.get("hist") or []) > 5 else "")
                 + (f'<details class="sgx"><summary>看最近 5 筆民調</summary><ul class="small">{rec}</ul></details>' if rec else ""))
    try:
        from tools import site_human as SH
        po = SH.policy(eng)
    except Exception:  # noqa: BLE001
        po = None
    spill = ('<p class="small"><b>連帶影響</b>：缺工先推高營造和餐飲成本，房屋建商、餐廳連鎖的利潤率最先受壓；工資上漲若擴散，通膨降得慢，'
             '聯準會降息就會更謹慎，長天期利率也比較難下來。反過來，如果移民減少讓就業數字變小，市場可能誤以為經濟轉弱。</p>')
    if po:
        spill += (f'<p class="small"><b>政策不確定</b>：經濟政策不確定指數 30 天平均 {po["now"]:.0f}，在自己歷史裡高於 {po["rank"]}% 的時候'
                  f'（資料日 {_e(po["asof"])}，詳見上面的人類溫度計）。</p>')
    body += f'<details class="sgx"><summary>看對市場的連帶影響</summary>{spill}</details>'
    body += ('<p class="note">移民：美國勞工統計局家戶調查（FRED），未季調所以都和一年前比；每年 1 月更新人口估計會讓數字跳一下，看方向比看大小可靠。'
             f'時薪：非農就業調查。黃燈：外國出生勞動力比一年前少，或移民比例高的行業時薪年增比整體高 1 個百分點以上。'
             f'民調：<a href="https://votehub.com/polls/" target="_blank" rel="noopener noreferrer">VoteHub</a> 彙整各家機構，每家取最新一筆再平均，'
             '少於 3 家就逐步放寬到 60、90 天。描述現況，不是預測，也不是投資建議。</p>')
    h = card("移民與民意：人變少、人不滿，怎麼傳到經濟", "Immigration and public opinion", body, "wide",
             sub="移民勞動力、缺工行業時薪、總統支持度")
    return h.replace('<section class="card', '<section id="migration" class="card', 1)
