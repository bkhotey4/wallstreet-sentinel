"""華爾街機構觀點（背景）: feed parsing (incl. truncated downloads), BlackRock page, CFTC positioning, site card.
Run: python -m tests.test_street"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_street_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.data import street_views as SV  # noqa: E402

RSS = ("<rss><channel><title>Show</title>"
       "<item><title><![CDATA[AI Boom Faces a Higher-Yield Roadblock]]></title><pubDate>Fri, 16 Oct 2026 21:00:00 -0000</pubDate>"
       "<link>https://example.com/ep1</link></item>"
       "<item><title>Second &amp; Episode</title><pubDate>Mon, 12 Oct 2026 20:30:00 -0000</pubDate></item>"
       "<item><title>Cut off mid-way")                                   # truncated download (Range request)


def main():
    items = SV.parse_feed(RSS)
    assert [i["title"] for i in items] == ["AI Boom Faces a Higher-Yield Roadblock", "Second & Episode"]   # partial item ignored
    assert items[0]["date"] == "Fri, 16 Oct 2026" and items[0]["link"] == "https://example.com/ep1" and items[1]["link"] == ""
    br = SV.parse_blackrock('<html><h1 class="x">French bonds: <span>a lesson</span> in selectivity</h1> Oct 19, 2026 … September 30, 2026</html>')
    assert br == [{"title": "French bonds: a lesson in selectivity", "date": "Oct 19, 2026", "link": SV.BLACKROCK[3]}]
    assert SV.parse_blackrock("<html>nothing</html>") == []
    rows = []
    for i in range(40):                                                   # newest first, as the API returns them
        rows.append({"report_date_as_yyyy_mm_dd": f"2026-{10 - i // 4:02d}-{28 - (i % 4) * 7:02d}T00:00:00.000", "open_interest_all": "1000",
                     "asset_mgr_positions_long": str(600 + (39 - i)), "asset_mgr_positions_short": "100",
                     "lev_money_positions_long": "100", "lev_money_positions_short": str(300 - (39 - i))})
    p = SV.positioning(rows)
    assert abs(p["am"] - 53.9) < 1e-9 and p["am_pct"] == 100.0 and abs(p["am_chg"] - 0.1) < 1e-9     # highest in the window
    assert abs(p["lm"] - (-16.1)) < 1e-9 and p["n_weeks"] == 40
    assert SV.positioning(rows[:10]) is None                              # too short to give a percentile
    from tools import site_quant as SQ
    eng = types.SimpleNamespace(street={"views": {"ms": {"zh": "摩根士丹利", "en": "MS", "home": "https://example.com", "items": items}},
                                        "pos": {"13874A": {"zh": "E-mini 標普 500", "en": "E-mini S&P", **p}}})
    html = SQ.sec_street(eng)
    assert "華爾街機構觀點" in html and "AI Boom Faces" in html and "53.9" in html and "不進入本站任何風險分數" in html
    assert SQ.sec_street(types.SimpleNamespace(street={})) == ""
    print("STREET TESTS PASSED [OK]")


if __name__ == "__main__":
    main()
