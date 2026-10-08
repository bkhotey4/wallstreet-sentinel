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
