"""卡片互相對答案（11-17）：AI 文字裡的掛牌／財報日期 vs IPO 卡與財報日曆。Run: python -m tests.test_cross_check"""
from datetime import date

from tools import cross_check as X
from tools import sys_health as H

TODAY = date(2026, 11, 17)
ROW = ('<tr><td><b>{n}</b> <span class="tk">T</span></td><td class="nw">$70.00～78.00</td>'
       '<td class="nw"><b><span data-en="~">約</span> {d}</b><div class="small muted">x</div></td></tr>')
IPO = (f'<section class="card"><h2>{H.IPO_CARD}</h2><table><tbody>' + ROW.format(n="Anthropic, PBC", d="11-26")
       + ROW.format(n="Rezera Inc.", d="11-18") + "</tbody></table></section>")


def test_ipo_mismatch_caught():
    ai = "接下來看：CoreWeave 財報細節、Anthropic 11/19 掛牌、10 年期殖利率。Rezera 11/18 掛牌。"
    got = X.ipo_issues(ai, IPO, TODAY)
    assert [(g["name"], g["text_date"], g["card_date"]) for g in got] == [("Anthropic", "2026-11-19", "2026-11-26")], got
    assert X.describe(got) == "Anthropic掛牌：文字寫 11/19，IPO 卡 11/26"
    assert X.ipo_issues(ai, IPO.replace("11-26", "11-18"), TODAY) == []          # within 2 days: fine
    assert X.ipo_issues("Anthropic 11/10 掛牌", IPO, TODAY) == []               # a past date is not checked


def test_company_timetable_shape_read():
    """11-18: a row with the company's own timetable ('<b>11-19 <span>掛牌</span></b>') was read as 'no date'."""
    row = ('<tr><td><b>Anthropic, PBC</b></td><td class="nw">$70.00～78.00</td><td class="nw"><b>11-19 '
           '<span data-en="listing">掛牌</span></b><div class="small muted">公司公布的時間表</div></td></tr>')
    html = f'<section class="card"><h2>{H.IPO_CARD}</h2><table><tbody>{row}</tbody></table></section>'
    assert X.ipo_dates(html) == {"Anthropic": "11-19"}
    assert X.ipo_issues("Anthropic 11/19 掛牌", html, TODAY) == []
    got = X.ipo_issues("Anthropic 11/26 掛牌", html, TODAY)
    assert got and got[0]["card_date"] == "2026-11-19", got


def test_round_trip_with_real_renderer():
    """The class behind 11-18: the card's renderer changed shape and the checker's parser didn't. Render rows with
    tools.site_ipo itself (estimate, stage, company timetable) and parse them back — any new shape breaks here."""
    from tools import site_ipo as S
    base = {"lo": 70, "hi": 78, "win_lo": "2026-11-20", "win_hi": "2026-11-30", "cik": "1", "s1": "2026-10-26",
            "since": 23, "last": "2026-11-17", "amends": 3}
    rows = [dict(base, name="Alpha Inc.", near="2026-11-21"),
            dict(base, name="Beta Corp", near="2026-11-22", stage="交易所核准掛牌", stage_n=8, stage_med=3,
                 stage_p25=2, stage_p75=5, near_lo="2026-11-21", near_hi="2026-11-24"),
            dict(base, name="Gamma, PBC", listing="2026-11-19", stage_src={"url": "u", "filed": "2026-11-12", "tz": "x"})]
    html = f'<section class="card"><h2>{H.IPO_CARD}</h2>{S._us_pending({"pending": rows})}</section>'
    got = X.ipo_dates(html)
    assert got.get("Alpha") == "11-21" and got.get("Beta") == "11-22" and got.get("Gamma") == "11-19", got
    # 11-20: the 已掛牌 table is a third shape (the row moves there the day after listing), with or without the deal fold
    done = [{"name": "Delta, PBC", "sym": "DLT", "priced": "2026-11-19", "offer": 83.0, "lockup": 180, "lock": "2027-05-18",
             "final": {"shares": 9.5e8, "gs_shares": 1.47e8, "gs_days": 30}},
            {"name": "Epsilon Ltd", "sym": "EPS", "priced": "2026-11-12", "offer": None, "lockup": 180}]
    html = f'<section class="card"><h2>{H.IPO_CARD}</h2>{S._us_done({"recent": done})}</section>'
    got = X.ipo_dates(html)
    assert got.get("Delta") == "11-19" and got.get("Epsilon") == "11-12", got
    assert X.ipo_issues("Delta 11/19 掛牌", html, date(2026, 11, 20)) == []


def test_earn_mismatch_caught():
    days = {"2026-11-17": {"rows": [{"sym": "NVDA", "name": "NVIDIA Corporation", "mcap": 4e12}]},
            "2026-11-19": {"rows": [{"sym": "WMT", "name": "Walmart Inc.", "mcap": 1e12}]}}
    zh = {"NVDA": "輝達", "WMT": "沃爾瑪"}
    ok = "輝達 11/18 清晨公布財報；沃爾瑪 11/19 財報。"                         # Taipei date one day later is normal
    assert X.earn_issues(ok, days, zh, TODAY) == []
    bad = "沃爾瑪 11/24 財報要看關稅。"
    got = X.earn_issues(bad, days, zh, TODAY)
    assert got and got[0]["sym"] == "WMT" and got[0]["card_date"] == "2026-11-19", got


def test_wired_into_health():
    days = {"2026-11-19": {"rows": [{"sym": "WMT", "name": "Walmart Inc.", "mcap": 1e12}]}}
    out = H.cross_issues(IPO, "Anthropic 11/19 掛牌", days, TODAY)
    assert out and out[0]["text"].startswith("**卡片互相矛盾**：Anthropic掛牌"), out


if __name__ == "__main__":
    test_ipo_mismatch_caught()
    print("ok test_ipo_mismatch_caught")
    test_company_timetable_shape_read()
    print("ok test_company_timetable_shape_read")
    test_round_trip_with_real_renderer()
    print("ok test_round_trip_with_real_renderer")
    test_earn_mismatch_caught()
    print("ok test_earn_mismatch_caught")
    test_wired_into_health()
    print("ok test_wired_into_health")
