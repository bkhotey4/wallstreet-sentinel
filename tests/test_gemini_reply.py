"""python -m tests.test_gemini_reply — parse the Gemini scheduled action's answers in the shared Google Doc."""
from wsb.data import gemini_reply as G

T = """WallStreet Sentinel × Gemini 協作文件
========== 以下是 Gemini 的回答（最新的在最上面） ==========
台北時間 2026-11-19 06:00
### TJX｜財報優於預期並上修全年展望
- 事實：第三季同店銷售成長 5%，上修全年 EPS（https://example.com/tjx ，2026-11-18 19:30）
- 傳聞：無
- 本站漏掉的：TJX 財報新聞稿
### UNH｜司法部調查傳聞
- 傳聞：WSJ 報導司法部擴大調查（https://example.com/wsj）
- 事實：股價下跌主要因為醫療成本上升
其他今天的大事：
- 日本央行官員暗示升息 https://example.com/boj
台北時間 2026-11-18 23:00
### OLD｜older batch
- 事實：x https://e.com/old
"""
d = G.parse(T)
assert d["when"] == "2026-11-19 06:00", d["when"]
assert [i["sym"] for i in d["items"]] == ["TJX", "UNH"]                    # the older batch is not read
tjx, unh = d["items"]
assert tjx["facts"][0]["url"] == "https://example.com/tjx" and tjx["rumors"] == []     # 「傳聞：無」 is nothing
assert tjx["missed"][0]["t"].startswith("TJX")
assert unh["rumors"][0]["url"] == "https://example.com/wsj"
assert unh["facts"] == [] and unh["guess"] == ["股價下跌主要因為醫療成本上升"]     # a 「fact」 without a link is a guess
assert d["extra"] == [{"t": "日本央行官員暗示升息", "url": "https://example.com/boj"}]
assert G.parse("")["items"] == [] and G.parse("no answers yet")["items"] == []
print("gemini_reply ok")
