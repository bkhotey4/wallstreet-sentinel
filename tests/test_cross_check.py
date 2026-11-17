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
    test_earn_mismatch_caught()
    print("ok test_earn_mismatch_caught")
    test_wired_into_health()
    print("ok test_wired_into_health")
