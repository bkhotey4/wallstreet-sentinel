"""分析師預期修正趨勢 (美股財報 tab): are next-quarter EPS estimates being revised up or down, and how fast.
Data and rules: wsb/data/est_revisions.py.  EPS estimates only; never price estimates."""
from __future__ import annotations

from typing import Dict, List

from tools.sitekit import T, card, cls, esc, num


def _pct(x) -> str:
    return num(x, 0) + "%"


def _movers(rows: List[Dict]) -> str:
    if not rows:
        return f'<p class="small muted">{T("沒有符合條件的公司。", "None qualify.")}</p>'
    tr = "".join(f'<tr><td><b>{esc(x["sym"])}</b></td><td>{esc(x["fq"])}</td><td class="r">{num(x["old"], 2)}</td><td class="r">{num(x["new"], 2)}</td>'
                 f'<td class="r {cls(x["pct"])}">{num(x["pct"], 1, sign=True, pct=True)}</td><td class="r">{num(x.get("n"), 0)}</td></tr>' for x in rows)
    return (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("公司", "Name")}</th><th>{T("財季", "Quarter")}</th><th class="r">{T("之前", "Before")}</th>'
            f'<th class="r">{T("現在", "Now")}</th><th class="r">{T("變化", "Change")}</th><th class="r">{T("分析師數", "Analysts")}</th></tr></thead><tbody>{tr}</tbody></table></div>')


def _hz_row(lab: str, en: str, h: Dict) -> str:
    return (f'<tr><td>{T(lab, en)}</td><td class="r up">{_pct(h["up_pct"])}（{h["up"]}）</td><td class="r dn">{_pct(h["dn_pct"])}（{h["dn"]}）</td>'
            f'<td class="r">{h["flat"]}</td><td class="r {cls(h["net"])}">{num(h["net"], 0, sign=True)}</td>'
            f'<td class="r">{num(h.get("med"), 2, sign=True, pct=True)}</td><td class="r">{h["n"]}</td></tr>')


def sec_est_rev(eng) -> str:
    from wsb.data import est_revisions as ER
    try:
        v = ER.view()
    except Exception:  # noqa: BLE001
        return ""
    if not v.get("available"):
        if not v.get("asof"):
            return ""                                  # never fetched: no card rather than an empty one
        return card("分析師預期修正趨勢", "Analyst estimate revisions",
                    f'<p>{T("可用的資料太少，暫時算不出整體方向。", "Too little data for an overall direction yet.")}'
                    + T("最後一次資料日 " + str(v["asof"]) + "。", "Last data " + str(v["asof"]) + ".") + "</p>", "wide")
    a, b = v["h"].get(7), v["h"].get(30)
    h = a or b
    dire = ("上修比下修多" if h["net"] > 0 else "下修比上修多" if h["net"] < 0 else "上修和下修差不多多")
    dire_en = "more up than down" if h["net"] > 0 else "more down than up" if h["net"] < 0 else "about even"
    span = "7" if a else "30"
    speed = {"up": ("跟過去一個月的速度比，這一週更偏向上修。", "This week leans further up than the 30-day pace."),
             "down": ("跟過去一個月的速度比，這一週更偏向下修。", "This week leans further down than the 30-day pace."),
             "steady": ("跟過去一個月的速度差不多。", "About the same pace as the past 30 days.")}.get(v.get("speed"), ("", ""))
    lead = T(f'一句話看懂：最近 {span} 天，分析師對下一季獲利的預估{dire}（{h["up"]} 家上修、{h["dn"]} 家下修，共 {h["n"]} 家）。{speed[0]}',
             f"In one line: over {span} days next-quarter EPS estimates moved {dire_en} ({h['up']} up, {h['dn']} down of {h['n']}). {speed[1]}")
    rows = "".join(_hz_row(z, e, x) for z, e, x in (("近 7 天", "7 days", a), ("近 30 天", "30 days", b)) if x)
    tbl = (f'<div class="scroll"><table class="mini"><thead><tr><th></th><th class="r">{T("上修", "Up")}</th><th class="r">{T("下修", "Down")}</th>'
           f'<th class="r">{T("沒變", "Flat")}</th><th class="r">{T("淨上修（百分點）", "Net (pts)")}</th><th class="r">{T("變化中位數", "Median change")}</th>'
           f'<th class="r">{T("家數", "Names")}</th></tr></thead><tbody>{rows}</tbody></table></div>')
    mv = ""
    if b:
        mv = (f'<details class="sgx"><summary>{T("近 30 天上修最多", "Largest upward changes, 30 days")}</summary>{_movers(b["top"])}</details>'
              f'<details class="sgx"><summary>{T("近 30 天下修最多", "Largest downward changes, 30 days")}</summary>{_movers(b["low"])}</details>'
              + (f'<p class="small muted">{T("上面的「之前」來自 Nasdaq 的回看數字，還沒有本站快照可以核對。變動特別大的公司，可能是真的改預估，也可能是一次性費用或季度標示調整，請對照公司財報。", "Before values are Nasdaq look-backs not yet checked against our snapshots. A very large change may be a real revision, a one-off charge or a quarter-label shift.")}</p>' if not b["own"] else ""))
    own = (b or a)["own"]
    hist = T(f'本站從 {v.get("first")} 開始每天存快照（已累積 {v["days"]} 天），歷史只從這一天算起。'
             f'目前的比較有 {own} 家用本站自己的快照，其餘 {(b or a)["src"]} 家用 Nasdaq 提供的「1 週前／1 個月前」共識；快照夠久後會全部換成本站紀錄。',
             f'Our own snapshots start {v.get("first")} ({v["days"]} days so far); history begins there. '
             f'{own} names use our snapshot, the rest the week-ago / month-ago consensus Nasdaq reports.')
    cov = v.get("cov") or []
    cvt = (T(f"這一輪有 {cov[0]}／{cov[1]} 家在最近一天內更新。", f"{cov[0]} of {cov[1]} names updated in the last day.") if len(cov) == 2 else "")
    stale, cnt = ER.STALE_DAYS, v["n"]
    how = (f'<details class="sgx"><summary>{T("怎麼算、哪裡要小心", "How it works and what to watch")}</summary><ul class="small">'
           f'<li>{T("共識預估＝分析師對每股盈餘（EPS）預估的平均。本卡只看 EPS，不看股價預估。", "Consensus = the average analyst EPS estimate. EPS only, no price estimates.")}</li>'
           f'<li>{T("變化不到 0.5% 算沒變（多半只是四捨五入）。EPS 接近 0 的公司不算百分比，只看方向；最大變化清單只放 EPS 絕對值 ≥ 0.25、分析師 ≥ 3 位的公司。", "Under 0.5% counts as flat. Near-zero EPS counts by sign only. The lists need |EPS| ≥ 0.25 and 3+ analysts.")}</li>'
           f'<li>{T("「下一季」是 Nasdaq 標示的當季，少數公司已往後滾動一季，不一定是下一份要公布的財報。比較時只比同一財季。", "The quarter is the one Nasdaq labels; a few have rolled ahead. Only the same quarter is compared.")}</li>'
           f'<li>{T("財報季時，已公布的公司換到新的一季，預估變動通常比較大。", "Changes run larger in earnings season as names roll to a new quarter.")}</li>'
           f'<li>{T(f"涵蓋：本站美股追蹤名單加上財報日曆上市值 100 億美元以上的公司。{cnt} 家有近期資料；超過 {stale} 天沒更新的公司不列入。", f"Coverage: our US list plus calendar names ≥ $10B. {cnt} have recent data.")}{cvt}</li>'
           f'<li>{hist}</li></ul></details>')
    body = (f'<p class="rimp big2"><b>{lead}</b></p>{tbl}{mv}{how}'
            f'<p class="note">{T("資料：Nasdaq 公開的分析師預估（Zacks 提供）。預估會變，也可能全錯；只描述分析師怎麼改數字，不是投資建議。", "Source: Nasdaq public analyst data (Zacks). Estimates change and can be wrong; a description only, not advice.")}</p>')
    return card("分析師預期修正趨勢", "Analyst estimate revisions", body, "wide", sub=T("下一季獲利預估往哪邊修、修得多快", "Which way next-quarter EPS estimates are moving, and how fast"))
