"""人類溫度計 page: what is happening to people before it reaches markets, from official FRED series.
Household bills against wages, the split between stretched and comfortable households, jobs and young workers,
policy uncertainty, China, and hidden leverage.  It describes the direction of each series; it is not a predictor,
and the thresholds are plain comparisons with a year ago rather than backtested signals."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd

from tools.sitekit import card

# (FRED id, label)
BILLS = [("CUSR0000SEHF01", "電費"), ("CUSR0000SEHA", "房租"), ("CUSR0000SAF11", "在家吃的食物"), ("CUSR0000SETB01", "汽油")]
WAGE = "AHETPI"
# (FRED id, label, unit, higher is worse, what it means)
GROUPS: List[Tuple[str, str, List[Tuple[str, str, str, bool, str]]]] = [
    ("家庭撐不撐得住", "平均數會藏住壓力，這裡看還不出錢和沒信心的人有沒有變多。", [
        ("DRCCLACBS", "信用卡逾期率", "%", True, "還不出卡費的比例"),
        ("DRCLACBS", "消費貸款逾期率", "%", True, "包含車貸等消費借款"),
        ("TDSP", "還債占收入比重", "%", True, "每賺 100 元要拿多少去還債"),
        ("PSAVERT", "個人儲蓄率", "%", False, "太低代表緩衝變薄"),
        ("UMCSENT", "密大消費者信心", "", False, "人們對生活和未來的感覺"),
    ]),
    ("工作與下一代", "看工作好不好找，以及 AI 是否開始影響剛進職場的人。這裡只看得到結果，看不出原因是不是 AI。", [
        ("LNS14024887", "16–24 歲失業率", "%", True, "年輕人最先感受到徵才變少"),
        ("CGBD2024", "20–24 歲大學畢業生失業率", "%", True, "AI 影響入門工作時，這裡可能先有反應"),
        ("LNS11300060", "25–54 歲勞動參與率", "%", False, "壯年人口有多少在工作或找工作"),
        ("JTSQUR", "自願離職率", "%", False, "敢辭職代表對找新工作有信心"),
    ]),
    ("看不見的地方", "過去的危機常從大家沒在看的地方開始。", [
        ("DRCRELEXFACBS", "商用不動產貸款逾期率", "%", True, "辦公室和商場的貸款，地區銀行的壓力來源之一"),
    ]),
]
FLOW = 0.01                                         # a change under 1% of the level counts as flat


def _series(eng, sid: str) -> pd.Series:
    try:
        s = eng.fred.get(sid)
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)
    return s.dropna() if s is not None else pd.Series(dtype=float)


def yoy(s: pd.Series) -> Optional[float]:
    """% change against the reading a year before the latest one."""
    if len(s) < 2:
        return None
    past = s[s.index <= s.index[-1] - pd.DateOffset(years=1)]
    return float((s.iloc[-1] / past.iloc[-1] - 1) * 100) if len(past) and past.iloc[-1] else None


def year_ago(s: pd.Series) -> Optional[float]:
    past = s[s.index <= s.index[-1] - pd.DateOffset(years=1)]
    return float(past.iloc[-1]) if len(past) else None


def rank(s: pd.Series) -> int:
    return int(round((s <= s.iloc[-1]).mean() * 100))


def tone(now: float, then: Optional[float], worse_up: bool) -> str:
    if then is None:
        return "—"
    if abs(now - then) <= abs(then) * FLOW:
        return "持平"
    return "變差" if (now > then) == worse_up else "改善"


def bills(eng) -> Dict:
    wage = yoy(_series(eng, WAGE))
    rows = []
    for sid, label in BILLS:
        s = _series(eng, sid)
        y = yoy(s)
        if y is not None:
            rows.append({"label": label, "yoy": y, "asof": s.index[-1].strftime("%Y-%m"),
                         "over": wage is not None and y > wage})
    return {"wage": wage, "rows": rows, "over": sum(r["over"] for r in rows)}


def group_rows(eng, items) -> List[Dict]:
    out = []
    for sid, label, unit, worse_up, note in items:
        s = _series(eng, sid)
        if s.empty:
            continue
        now, then = float(s.iloc[-1]), year_ago(s)
        out.append({"label": label, "now": now, "then": then, "unit": unit, "rank": rank(s), "note": note,
                    "tone": tone(now, then, worse_up), "asof": s.index[-1].strftime("%Y-%m")})
    return out


def policy(eng) -> Optional[Dict]:
    s = _series(eng, "USEPUINDXD")
    if len(s) < 60:
        return None
    m = s.rolling(30).mean().dropna()
    return {"now": float(m.iloc[-1]), "rank": rank(m), "asof": s.index[-1].strftime("%Y-%m-%d")}


def china(eng) -> List[Dict]:
    out = []
    for sid, label, why in (("QCNR628BIS", "中國實質房價", "房子是中國家庭最大的資產，下跌會壓抑消費"),
                            ("CRDQCNAPABIS", "中國非金融部門信貸", "借錢成長放慢，代表景氣動能變弱")):
        s = _series(eng, sid)
        y = yoy(s)
        if y is not None:
            out.append({"label": label, "yoy": y, "why": why, "asof": s.index[-1].strftime("%Y-%m")})
    return out


def _pill(t: str) -> str:
    cls = {"變差": "down", "改善": "up"}.get(t, "muted")
    return f'<span class="pill {cls}">{t}</span>'


def _table(rows: List[Dict]) -> str:
    def ago(r: Dict) -> str:
        return "" if r["then"] is None else f'{r["then"]:.1f}{r["unit"]}'

    body = "".join(
        f'<tr><td>{r["label"]}<div class="small muted">{r["note"]}</div></td>'
        f'<td class="r">{r["now"]:.1f}{r["unit"]}</td><td class="r">{ago(r)}</td>'
        f'<td>{_pill(r["tone"])}</td><td class="r">{r["rank"]}%</td><td class="r muted">{r["asof"]}</td></tr>' for r in rows)
    return ('<div class="scroll"><table class="mini"><thead><tr><th>指標</th><th class="r">現在</th><th class="r">一年前</th>'
            '<th>方向</th><th class="r">1995 年來位置</th><th class="r">資料月份</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def sec_human(eng) -> str:
    b = bills(eng)
    groups = [(t, d, group_rows(eng, items)) for t, d, items in GROUPS]
    rows = [r for _t, _d, g in groups for r in g]
    if not b["rows"] and not rows:
        return ""
    worse = sum(r["tone"] == "變差" for r in rows)
    lead = (f'{b["over"]}／{len(b["rows"])} 項生活開銷漲得比工資快；家庭、工作等 {len(rows)} 項指標中，{worse} 項比一年前差。'
            if b["rows"] else f'{len(rows)} 項指標中，{worse} 項比一年前差。')
    bill_html = ""
    if b["rows"]:
        wage = "—" if b["wage"] is None else f'{b["wage"]:+.1f}%'
        items = "".join(f'<tr><td>{r["label"]}</td><td class="r">{r["yoy"]:+.1f}%</td>'
                        f'<td>{_pill("變差" if r["over"] else "改善")} {"漲得比工資快" if r["over"] else "沒有超過工資"}</td>'
                        f'<td class="r muted">{r["asof"]}</td></tr>' for r in b["rows"])
        bill_html = (f'<h3>帳單 vs 薪水</h3><p class="small">一般員工時薪一年增加 {wage}。帳單漲得比薪水快時，人們就算有工作也覺得變窮，'
                     f'這種感受常常先反映在選票上。</p><div class="scroll"><table class="mini"><thead><tr><th>開銷</th><th class="r">一年漲幅</th>'
                     f'<th>和工資比</th><th class="r">資料月份</th></tr></thead><tbody>{items}</tbody></table></div>')
    pol = policy(eng)
    pol_html = (f'<h3>政策不確定性</h3><p class="small">近 30 天平均 {pol["now"]:.0f}，在 1995 年以來第 {pol["rank"]} 百分位，資料到 {pol["asof"]}。'
                '數字越高，代表新聞裡談政策風險越多。</p>' if pol else "")
    cn = china(eng)
    cn_html = ('<h3>中國</h3><ul class="lines">' + "".join(
        f'<li><b>{r["label"]}</b>：一年 {r["yoy"]:+.1f}%（資料到 {r["asof"]}）<div class="small muted">{r["why"]}</div></li>' for r in cn)
        + '</ul><p class="small muted">這些國際資料公布很慢，看的是長期方向，不是最近的狀況。</p>' if cn else "")
    body = (f'<p class="rimp big2"><b>一句話看懂：{lead}</b></p>' + bill_html
            + "".join(f'<h3>{t}</h3><p class="small">{d}</p>{_table(g)}' for t, d, g in groups if g) + pol_html + cn_html
            + '<p class="note">資料來自 FRED 官方統計，「方向」只和一年前比較，用來觀察壓力在哪裡累積，沒有經過回測，不是預測。不構成投資建議。</p>')
    return card("人類溫度計：壓力先出現在人身上", "Human thermometer: stress shows up in people first", body, "wide",
                sub="帳單、家庭、工作、政策與中國")
