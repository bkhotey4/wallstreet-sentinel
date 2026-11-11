"""聯準會官員講話：RSS／行事曆解析、重點句與方向、殖利率反應、卡片輸出（不連網）。"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

RSS = """<rss><channel><item><title>Waller, The Economic Outlook</title>
<link><![CDATA[https://www.federalreserve.gov/newsevents/speech/waller20261110a.htm]]></link>
<description><![CDATA[Speech At a conference, London]]></description><category>Speech</category>
<pubDate><![CDATA[Tue, 10 Nov 2026 09:00:00 GMT]]></pubDate></item></channel></rss>"""
PAGE = ('<html><div id="article"><p>Thank you. Today I will discuss the outlook.</p><p>Inflation remains too high and prices keep rising. '
        'The labor market is solid. I will then turn to monetary policy. '
        'But inflation remains too high, so I believe further tightening of monetary policy will be needed. '
        'Inflation expectations matter.</p></div><div>Last Update: November 10, 2026</div></html>')


def main() -> None:
    from wsb.data import fed_speeches as FS
    it = FS.parse_rss(RSS)
    assert it[0]["who"] == "Waller" and it[0]["time"] == "2026-11-10T09:00Z" and it[0]["topic"] == "The Economic Outlook", it
    t = FS.text_of(PAGE)
    assert "Last Update" not in t and t.startswith("Thank you")
    sc = FS.score(t)
    assert sc["key"].startswith("But inflation remains too high"), sc["key"]          # agenda sentence skipped
    assert sc["key_dir"] == "tight" and sc["infl"] >= 4 and sc["jobs"] == 1
    assert FS.lean(sc) == "多談通膨"
    assert FS.key_dir("My view is that further changes in the policy rate should wait, despite the recent rate increase.") == "hold"
    assert FS.key_dir("I support further rate cuts this year.") == "ease"
    cal = {"events": [{"type": "Speeches", "month": "2026-11", "days": "13", "time": "7:00 p.m.", "title": "Speech - Vice Chair Philip N. Jefferson",
                       "description": "Productivity", "location": "UCSD"},
                      {"type": "Speeches", "month": "2027-01", "days": "5", "title": "too far"}, {"month": "2026-11", "days": "12"}]}
    up = FS.parse_cal(cal, date(2026, 11, 11))
    assert len(up) == 1 and up[0]["date"] == "2026-11-13"

    import tools.site_fedspeech as S
    assert S._cal_time("2026-11-13", "7:00 p.m.") == "11/14 08:00"
    assert S._role("Speech - Vice Chair for Supervision Michelle W. Bowman") == "監理副主席"
    idx = pd.bdate_range("2026-06-01", "2026-11-10")
    y = pd.Series(3.5 + np.cumsum(np.random.default_rng(1).normal(0, 0.03, len(idx))), index=idx)
    y.iloc[-1] = y.iloc[-2] + 0.15                                                   # a 15bp day
    m = S.yield_move(y, pd.Timestamp("2026-11-10"))
    assert round(m["bp"]) == 15 and m["k"] > 2, m
    assert S.yield_move(y, pd.Timestamp("2026-11-08")) is None                      # weekend: no row

    d = {"ts": 1.0, "speeches": [{**it[0], **sc}], "upcoming": up}
    FS.load, real = (lambda: d), FS.load

    class F:
        def get(self, sid):
            return y

    class E:
        fred = F()
    try:
        html = S.sec_fed_speeches(E())
    finally:
        FS.load = real
    assert "Waller" in html and "重點句偏向再收緊" in html and "+15bp，比平常一天大很多" in html, html[:600]
    assert "11/14 08:00 台北" in html
    for w in ("買進", "賣出", "目標價", "低估", "高估"):
        assert w not in html
    print("test_fed_speeches ok")


if __name__ == "__main__":
    main()
