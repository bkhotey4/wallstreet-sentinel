"""BIS 官方新聞稿（11-17）：讀 __NEXT_DATA__、用官方 publishedOn、執法和解不通知、30 小時內才通知、訊息內容。
Run: python -m tests.test_bis_news"""
import json

from wsb.data import bis_news as B


def _page(items):
    return ('<html><script id="__NEXT_DATA__" type="application/json">'
            + json.dumps({"props": {"pageProps": {"pressReleaseTeasers": items}}}) + "</script></html>")


T_RULE = 1794805200                                       # 2026-11-16 05:00 UTC (BIS publishedOn)
ITEMS = [{"path": "/press-release/bis-issues-rule-addressing-remote-access-american-super-intelligence-technology",
          "title": "BIS Issues Rule Addressing Remote Access to American Super Intelligence Technology",
          "created": {"timestamp": T_RULE + 27893}, "publishedOn": {"timestamp": T_RULE}},
         {"path": "/press-release/settlement-x", "title": "BIS Reaches Administrative Enforcement Settlement with X Corp",
          "created": {"timestamp": T_RULE - 86400}}]


def test_parse_classify_alert():
    got = B.parse_page(_page(ITEMS))
    assert got[0]["ts"] == T_RULE and got[0]["url"].startswith("https://www.bis.gov/press-release/"), got   # publishedOn wins
    assert got[1]["ts"] == T_RULE - 86400                                                                 # created as fallback
    assert B.classify(got[0])["topic"] == "出口管制／半導體" and B.classify(got[1]) is None                 # settlements are not policy
    d = {"items": [dict(x, first_seen=T_RULE + 300) for x in got]}
    a = B.alerts(d, T_RULE + 3600)
    assert [x["key"] for x in a] == ["bis:" + ITEMS[0]["path"]]
    assert B.alerts(d, T_RULE + 31 * 3600) == []                                                          # too old
    assert B.parse_page("<html>no data</html>") == []


def test_embed():
    from tools import sec_push as P
    got = B.parse_page(_page(ITEMS))
    e = P.bis_embed({"item": B.classify(got[0])}, ["費城半導體 -3.0%"])
    assert "台北 11/16 13:00（美東 11/16 00:00）" in e["description"] and "費城半導體 -3.0%" in e["description"], e["description"][:200]
    assert e["title"].startswith("🏛️ 美國出口管制：BIS Issues Rule")


if __name__ == "__main__":
    test_parse_classify_alert()
    print("ok test_parse_classify_alert")
    test_embed()
    print("ok test_embed")
