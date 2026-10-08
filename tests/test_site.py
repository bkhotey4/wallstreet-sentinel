"""Intel-station site: renders from a synthetic engine, contains no holdings, escapes untrusted text."""
import asyncio
import re
import time
from pathlib import Path

import tests.test_offline as T
from wsb.analytics.stress import StressEngine
from wsb.data.news import NewsItem
from wsb.engine import Engine
from wsb.health import HEALTH
from tools import build_site as B


def main():
    eng = Engine()
    eng.market, eng.fred = T.m, T.fr
    eng.stress_engine = StressEngine(T.m, T.fr)
    eng.news.items = [NewsItem("Bloomberg", "Fed <script>alert(1)</script> signals pause", "javascript:alert(1)", time.time(), 9),
                      NewsItem("CNBC", "Credit spreads widen", "https://example.com/a?b=1&c=2", time.time(), 5)]
    eng.calendar.events = []
    HEALTH.ok("yahoo_quotes", 90, every=300)
    asyncio.run(eng.recompute())
    assert not eng.holdings and eng.portfolio.get("error"), "holdings must be disabled in intel-station mode"
    out = Path("/tmp/wsb_site_test")
    p = asyncio.run(B.build(out, use_ai=False, engine=eng))
    page = p.read_text(encoding="utf-8")
    # trading-desk layout: strip, hoverable charts, radar, bilingual labels, theme + language toggles
    assert 'class="strip"' in page and 'id="c_ssi"' in page and 'id="c_radar"' in page and 'id="c_t0"' in page
    assert 'id="langBtn"' in page and 'id="themeBtn"' in page and 'data-en="Systemic Stress Index"' in page
    import json as _j, re as _re
    cd = _j.loads(_re.search(r'<script type="application/json" id="chart-data">(.*?)</script>', page, _re.S).group(1))
    assert "c_ssi" in cd and len(cd["c_ssi"]["x"]) == len(cd["c_ssi"]["v"]) > 100
    # no position advice anywhere on the public page (playbook action list is not rendered)
    assert "一般性行動框架" not in page
    # AI commentary: advice lines are scrubbed, market description kept
    txt = "**一句話結論**\n信用利差擴大，SSI 升溫。\n- 建議減碼半導體 20%\n- 避險比例提高到 15%\n- 關注週五非農"
    clean = B.scrub_advice(txt)
    assert "減碼" not in clean and "15%" not in clean and "非農" in clean and "信用利差" in clean
    html2 = B.render(eng, clean, "test-llm")
    assert "AI 市場評論" in html2 and "非農" in html2 and "<h4><b>一句話結論</b></h4>" in html2
    assert "系統性壓力指數" in page and "全球跨資產行情" in page and "衝擊雷達" in page and "風險劇本" in page
    assert "<script>alert" not in page and "&lt;script&gt;" in page, "untrusted headline must be escaped"
    assert 'href="javascript:' not in page, "non-http links must be neutralised"
    assert "https://example.com/a?b=1&amp;c=2" in page
    for word in ("持倉總值", "未實現", "VaR99", "ENB"):
        assert word not in page, word
    assert not re.search(r"https?://(?!example\.com)[^\"' ]+\.(js|css)", page), "page must not load external scripts/styles"
    import json
    d = json.loads((out / "data.json").read_text())
    assert d["ssi"]["score"] > 0 and "portfolio" not in json.dumps(d).lower()
    print(f"  site: {len(page) / 1024:.0f} KB, ssi {d['ssi']['score']:.1f} {d['ssi']['label']}")
    print("SITE TESTS PASSED ✅")


if __name__ == "__main__":
    main()
