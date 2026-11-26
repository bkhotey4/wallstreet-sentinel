"""TrendForce press list (11-26): parsing, one main industry per report, title direction, reaction vs the index.
Run: python -m tests.test_research_press"""
import pandas as pd

from tools import site_respress as S
from wsb.data import research_press as R

PAGE = ('<a href="/presscenter/news/20261125-13321.html">Cuts to Chinese CSP Demand Weigh on Price Outlook, Slowing Memory '
        'Industry Revenue Growth in 2027, Says TrendForce</a><a href="https://www.trendforce.com/presscenter/news/20261119-13314.html">'
        'NAND Flash Prices Set to Decline in 2027 as Chinese CSP Order Cuts Outweigh North American Demand Growth</a>'
        '<a href="/presscenter/news/20261119-13314.html"><img></a><a href="/presscenter/news/20261126-13324.html">Global NEV Sales Rise 7.6% YoY</a>')


def test_parse_and_classify():
    xs = R.parse_list(PAGE)
    assert [x["date"] for x in xs] == ["2026-11-26", "2026-11-25", "2026-11-19"] and xs[2]["url"].endswith("20261119-13314.html")
    nand = R.classify(xs[2]["title"])
    assert nand["topics"] == ["記憶體（NAND／SSD）"] and nand["dir"] == "down" and "SNDK" in nand["syms"]
    mem = R.classify(xs[1]["title"])                       # "Growth" is not "up"; CSP does not pull in AI servers
    assert mem["topics"] == ["記憶體（整體）"] and mem["dir"] == "down" and "NVDA" not in mem["syms"]
    assert R.classify(xs[0]["title"])["dir"] == "up"
    assert R.parse_lead('<meta name="description" content="TrendForce’s latest memory industry research indicates that NAND will fall.">').startswith("TrendForce")


def test_reaction_vs_index():
    idx = pd.to_datetime(["2026-11-24", "2026-11-25", "2026-11-26"])
    c = pd.DataFrame({"MU": [100.0, 95.0, 96.0], "^GSPC": [100.0, 99.0, 99.5], "2408.TW": [50.0, 50.0, 55.0], "^TWII": [100.0, 100.0, 102.5]}, index=idx)
    us = S.reaction(c, "MU", "2026-11-25")                 # US: the report day itself
    assert us["day"] == "11-25" and round(us["pct"], 1) == -5.0 and round(us["excess"], 1) == -4.0
    tw = S.reaction(c, "2408.TW", "2026-11-25")            # Taiwan: the next day; a market-wide rally is netted out
    assert tw["day"] == "11-26" and round(tw["pct"], 1) == 10.0 and round(tw["excess"], 1) == 7.5
    rows = S.rows_of([{"date": "2026-11-25", "title": "x", "syms": ["MU", "2408.TW"], "topics": ["記憶體（整體）"], "dir": "down"}],
                     c, {"MU": "美光", "2408.TW": "南亞科"})
    from datetime import date
    lead = S._lead(rows, today=date(2026, 11, 26))
    assert "比大盤多漲 1.8" in lead                                 # average excess +1.75 → below 2 points
    assert "看不出市場特別在意" in lead


if __name__ == "__main__":
    test_parse_and_classify()
    test_reaction_vs_index()
    print("ok research press")


def test_whole_words_and_sia():
    assert R.classify("Global OLED Monitor Shipments Double YoY as Rankings Shift Dramatically")["topics"] == ["面板與顯示器"]
    page = ('<a href="https://www.semiconductors.org/global-semiconductor-sales-increase-24-1-from-q2-2026-to-q3-2026/">Global Semiconductor '
            'Sales Increase 24.1% from Q2 2026 to Q3 2026</a><a href="https://www.semiconductors.org/sia-statement-on-x/">SIA Statement on X</a>')
    xs = R.parse_sia(page)
    assert len(xs) == 1 and xs[0]["src"] == "SIA" and R.classify(xs[0]["title"])["topics"] == ["全球半導體銷售（SIA）"]
    assert R.parse_date('<meta property="article:published_time" content="2026-11-03T13:00:00+00:00">') == "2026-11-03"


if __name__ == "__main__":
    test_whole_words_and_sia()
    print("ok sia")
