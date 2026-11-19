"""python -m tests.test_gemini_reply — parse the Gemini scheduled action's answers in the shared Google Doc."""
from wsb.data import gemini_reply as G

T = """WallStreet Sentinel × Gemini 協作文件
========== 以下是 Gemini 的回答（最新的在最上面） ==========
台北時間 2026-11-19 06:00
### TJX｜財報優於預期並上修全年展望
- 事實：第三季同店銷售成長 5%，上修全年 EPS（https://example.com/news/2026/11/18/tjx-q3 ，2026-11-18 19:30）
- 傳聞：無
- 本站漏掉的：TJX 財報新聞稿
### UNH｜司法部調查傳聞
- 傳聞：WSJ 報導司法部擴大調查（https://example.com/articles/doj-widens-unitedhealth-probe）
- 事實：股價下跌主要因為醫療成本上升
其他今天的大事：
- 日本央行官員暗示升息 https://example.com/2026/boj-hint
台北時間 2026-11-18 23:00
### OLD｜older batch
- 事實：x https://e.com/old
"""
d = G.parse(T)
assert d["when"] == "2026-11-19 06:00", d["when"]
assert [i["sym"] for i in d["items"]] == ["TJX", "UNH"]                    # the older batch is not read
tjx, unh = d["items"]
assert tjx["facts"][0]["url"] == "https://example.com/news/2026/11/18/tjx-q3" and tjx["rumors"] == []     # 「傳聞：無」 is nothing
assert tjx["missed"][0]["t"].startswith("TJX")
assert unh["rumors"][0]["url"] == "https://example.com/articles/doj-widens-unitedhealth-probe"
assert unh["facts"] == [] and unh["guess"] == ["股價下跌主要因為醫療成本上升"]     # a 「fact」 without a link is a guess
assert d["extra"] == [{"t": "日本央行官員暗示升息", "url": "https://example.com/2026/boj-hint"}]
assert G.parse("")["items"] == [] and G.parse("no answers yet")["items"] == []
# 11-19: the first real run cited only home pages — those are not checkable, so they are not "sourced"
h = G.parse(T.replace("https://example.com/news/2026/11/18/tjx-q3", "https://finviz.com").replace(
    "https://example.com/articles/doj-widens-unitedhealth-probe", "https://www.tjx.com/news/news-releases"))
assert h["items"][0]["facts"] == [] and "無法查證" in h["items"][0]["guess"][0]
assert h["items"][1]["rumors"][0]["url"] is None
assert G.specific("https://www.reuters.com/markets/us/tjx-raises-forecast-2026-11-18/") and not G.specific("https://seekingalpha.com")
print("gemini_reply ok")


def test_dead_link_demoted():
    d = {"items": [{"sym": "X", "why": "w", "facts": [{"t": "假新聞", "url": "https://a.com/2026/11/18/some-long-story-name"}],
                    "rumors": [], "missed": [], "guess": []}], "extra": [],
         "link_ok": {"https://a.com/2026/11/18/some-long-story-name": False}}
    out = G.sanitize(d)
    assert out["items"][0]["facts"] == [] and "404" in out["items"][0]["guess"][0]
test_dead_link_demoted(); print('dead link ok')
