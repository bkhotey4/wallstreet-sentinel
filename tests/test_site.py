"""Intel-station site: renders from a synthetic engine, contains no holdings, escapes untrusted text."""
import asyncio
import os
import re
import sys
import tempfile
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import tests.test_offline as T
from wsb.analytics.stress import StressEngine
from wsb.data.news import NewsItem
from wsb.engine import Engine
from wsb.health import HEALTH
from tools import build_site as B


def main():
    eng = Engine()
    eng.site_mode = True
    eng.market, eng.fred = T.m, T.fr
    eng.stress_engine = StressEngine(T.m, T.fr)
    eng.news.items = [NewsItem("Bloomberg", "Fed <script>alert(1)</script> signals pause", "javascript:alert(1)", time.time(), 9),
                      NewsItem("CNBC", "Credit spreads widen", "https://example.com/a?b=1&c=2", time.time(), 5)]
    eng.calendar.events = []
    # synthetic slow series for the valuation panel (quarterly Z.1 / BEA, daily Baa spread)
    import numpy as np, pandas as pd
    q = pd.date_range("1990-01-01", periods=146, freq="QS")
    rng = np.random.default_rng(3)
    gdp = pd.Series(np.linspace(6000, 30000, len(q)), index=q)
    eq = gdp * 1000 * (0.6 + 1.2 * np.linspace(0, 1, len(q)) + rng.normal(0, 0.05, len(q)))
    eng.fred.series.update({"GDP": gdp, "NCBEILQ027S": eq, "TNWMVBSNNCB": eq / 1.3,
                            "DRCCLACBS": pd.Series(3 + rng.normal(0, 0.4, len(q)), index=q),
                            "BAA10Y": pd.Series(2 + rng.normal(0, 0.3, 5000), index=pd.bdate_range("2006-01-02", periods=5000))})
    HEALTH.ok("yahoo_quotes", 90, every=300)
    asyncio.run(eng.recompute(skip_quality=True))
    assert not eng.holdings and eng.portfolio.get("error"), "holdings must be disabled in intel-station mode"
    out = Path(tempfile.gettempdir()) / "wsb_site_test"
    from unittest.mock import AsyncMock, patch
    eng.refresh_earnings = AsyncMock()
    with patch("wsb.analytics.siteextra.refresh", AsyncMock(return_value={})):
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
    # new sections: every SSI input, past crises (multi-asset, incl. 1997/2008), valuation & bubble watch
    assert "壓力指數的全部指標" in page and page.count('class="blk"') >= 8
    assert "1997 亞洲金融風暴" in page and "2008 金融海嘯（全程）" in page and 'id="c_ssi_all"' in page and "恆生" in page
    assert "巴菲特指標" in page and "信用卡逾期率" in page and "Baa 公司債利差" in page
    assert eng.valuation["available"] and any(i["key"] == "buffett" and i["estimate"] is not None
                                              for g in eng.valuation["groups"] for i in g["items"])
    assert "行情資料日" in page
    # quant cards: no hard-coded tables / placeholder scores (removed 2026-10-15)
    for bad in ("Copilot 訂閱", "3491.58", "$1.82 兆", "7勝 3負", "DOI) 上升至 98 天", "fcf_burn", "38%~60%", "|| 31.9", "sm_base = 42", "retail_score = 68"):
        assert bad not in page, bad
    import tools.site_sections as S2
    for gone in ("sec_hyperscaler_capex_fcf", "sec_bull_year5_analog", "sec_equity_net_supply"):
        assert not hasattr(S2, gone), gone
    # tabbed layout: every page exists, overview shown first
    for k in ("overview", "risk", "flows", "crisis", "valuation", "markets", "taiwan", "news", "inputs"):
        assert f'id="p-{k}"' in page and f'href="#{k}"' in page, k
    assert 'class="page on" id="p-overview"' in page
    # sidebar layout (2026-10): every page sits in the sidebar once, the overview opens with the 總攬大表
    import tools.site_layout as SLY
    side = page[page.find('<aside class="side"'):page.find("</aside>")]
    keys = re.findall(r'class="page[^"]*" id="p-([a-z]+)"', page)
    tabs_ = re.findall(r'<a class="ptab[^"]*" href="#[a-z]+" data-p="([a-z]+)"', side)
    assert len(keys) == len(set(keys)) and all(tabs_.count(k) == 1 for k in keys), keys
    # each page with ≥2 cards has a fold-out list of its cards in the sidebar; every link points at a real card id
    for cid in re.findall(r'class="pca"[^>]*data-c="([^"]+)"', side):
        assert f'id="{cid}"' in page, cid
    assert [k for k in keys if k in SLY.GROUP_OF] == [k for *_x, ks in SLY.GROUPS for k in ks if k in keys]
    assert page.index('id="c-index"') < page.index('id="p-risk"') and "總攬大表" in page and 'id="crumb"' in page
    _pages = {k: page[page.find(f'id="p-{k}"'):] for k in keys}
    _pk = SLY.picks({k: v[:v.find('class="page', 10)] if 'class="page' in v[10:] else v for k, v in _pages.items()})
    # the index reads its figures off the cards: a reworded card must not silently empty it
    assert len(_pk["home"]) >= 5 and len(_pk["risk"]) >= 4 and len(_pk["sector"]) >= 4 and len(_pk["stock"]) >= 2, _pk
    assert "Gamma 雷達" in page and "暗池指數" in page and "total_mcap_usd" not in page
    # AI commentary: advice lines are scrubbed, market description kept
    txt = "**一句話結論**\n信用利差擴大，SSI 升溫。\n- 建議減碼半導體 20%\n- 避險比例提高到 15%\n- 關注週五非農"
    clean = B.scrub_advice(txt)
    assert "減碼" not in clean and "15%" not in clean and "非農" in clean and "信用利差" in clean
    eng.ai_written = 1792512000.0                      # the card says when the commentary was written (Taipei time)
    html2 = B.render(eng, clean, "test-llm")
    if os.environ.get("WSB_SITE_DUMP"):
        open(os.environ["WSB_SITE_DUMP"], "w", encoding="utf-8").write(html2)
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    assert f"最後更新 {_dt.fromtimestamp(1792512000.0, _Z('Asia/Taipei')):%m-%d %H:%M} 台北" in html2
    # AI text that innocently uses the deploy guard's phrases must not block deployment (same pattern as the workflow)
    _bad = clean + "\n## 使用者持倉 的影響\n銀行債券的未實現損益擴大；持倉總值 data-private"
    _html3 = B.render(eng, _bad, "test-llm")
    assert not re.search(r"## 使用者持倉|持倉總值|未實現損益|data-private", _html3), "AI wording would trip the holdings guard"
    assert "評價損益" in _html3
    _risk = html2[html2.find('id="p-risk"'):]
    _risk = _risk[:_risk.find('id="p-', 10)] if 'id="p-' in _risk[10:] else _risk
    assert _risk.count('<p class="upd') >= 3, _risk.count('class="upd')                # risk cards carry their own update time
    _cards = html2.count('<section class="card')
    assert html2.count('<p class="upd') >= _cards * 0.6, (html2.count('<p class="upd'), _cards)   # most cards say when
    assert 'class="ago" data-ts="' in html2 and "分鐘前" in html2
    assert "AI 市場評論" in html2 and "非農" in html2 and "<h4><b>一句話結論</b></h4>" in html2
    # auto-update: the page carries its build stamp; the script compares it with version.json and reloads
    assert re.search(r'id="liveb" data-b="\d{10}"', html2) and "version.json?t=" in html2 and "location.replace(location.pathname+'?v='+v.b" in html2 and "wss_rl" in html2
    assert "系統性壓力指數" in page and "全球跨資產行情" in page and "衝擊雷達" in page and "風險劇本" in page
    assert "<script>alert" not in page and "&lt;script&gt;" in page, "untrusted headline must be escaped"
    assert 'href="javascript:' not in page, "non-http links must be neutralised"
    assert "https://example.com/a?b=1&amp;c=2" in page
    # no holdings analytics on the public page.  Link URLs are stripped first: Google News links carry random base64
    # tokens that can contain e.g. "ENB" and made this guard fail at random.
    import re as _re
    visible = _re.sub(r'(?:href|src)="[^"]*"', "", page)
    # the 我的持股 page's public market data (every US ticker's EPS, prices …) is checked by its own key whitelist in
    # test_portfolio_page; a public ticker such as Enbridge (ENB) there is not a holding
    visible = _re.sub(r'<script type="application/json" id="pf-data">.*?</script>', "", visible, flags=_re.S)
    for word in ("持倉總值", "未實現", "VaR99", "ENB"):
        assert not _re.search(rf"(?<![A-Za-z0-9]){_re.escape(word)}(?![A-Za-z0-9])", visible), word
    assert not re.search(r"https?://(?!example\.com)[^\"' ]+\.(js|css)\b", page), "page must not load external scripts/styles"
    import json
    d = json.loads((out / "data.json").read_text(encoding="utf-8"))
    assert d["ssi"]["score"] > 0 and "portfolio" not in json.dumps(d).lower()
    # AI market note: reused for 55 min, rewritten sooner when the stress index jumps
    calls = []
    async def fake_ai(e):
        calls.append(1)
        return f"note {len(calls)}", "test"
    with patch.object(B, "ai_commentary", fake_ai):
        B._commentary_cache().unlink(missing_ok=True)
        t0 = time.time()
        assert asyncio.run(B.ai_commentary_cached(eng, now=t0)) == ("note 1", "test")
        assert asyncio.run(B.ai_commentary_cached(eng, now=t0 + 20 * 60)) == ("note 1", "test") and len(calls) == 1
        assert asyncio.run(B.ai_commentary_cached(eng, now=t0 + 56 * 60))[0] == "note 2" and len(calls) == 2
        eng.stress.score += 5
        assert asyncio.run(B.ai_commentary_cached(eng, now=t0 + 60 * 60))[0] == "note 3"
    print(f"  site: {len(page) / 1024:.0f} KB, ssi {d['ssi']['score']:.1f} {d['ssi']['label']}")
    print("SITE TESTS PASSED")


if __name__ == "__main__":
    main()
