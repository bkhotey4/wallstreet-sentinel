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
# 11-22: a numbered line quoting a publish time inside an item is not the start of the next (older) batch
_nr = T.replace("其他今天的大事：", "### NR-1｜讀完全文\n1. **原文**：委員會報告（https://example.com/r/1 ，2026-11-20 14:00 發布）\n"
                "報導於 2026-11-20 15:30 更新，標題和內文有落差\n### TWC-1｜覆蓋清單：缺兩項\n- 事實：x https://example.com/twc/1\n其他今天的大事：")
assert [i["sym"] for i in G.parse(_nr)["items"]] == ["TJX", "UNH", "NR-1", "TWC-1"], [i["sym"] for i in G.parse(_nr)["items"]]
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


def test_card_text_passes_deploy_guard():
    """11-20: Gemini wrote 「未實現現金流」; the card printed it as is, the site test failed on the holdings-guard word
    (the cloud deploy guard matches 「未實現損益」 and would block every build until the next reply). Outside text is
    reworded, URLs are not."""
    from tools import site_gemini as S
    i = {"sym": "WIDE-1", "why": "市場對未實現現金流的 AI 估值折價", "facts": [{"t": "軟銀被高估？", "url": "https://a.com/x?q=未實現"}],
         "rumors": [], "missed": [], "guess": ["有人喊買進"]}
    h = S.block(i, {})
    shown = h.replace('href="https://a.com/x?q=未實現"', "")
    assert 'href="https://a.com/x?q=未實現"' in h
    for w in ("未實現", "高估", "買進", "持倉總值"):
        assert w not in shown, (w, shown)
    assert "帳面現金流" in shown
test_card_text_passes_deploy_guard(); print('card guard ok')


def test_stale_note():
    from datetime import datetime
    from tools import site_gemini as S
    now = datetime(2026, 11, 20, 22, 30, tzinfo=S.TPE)
    assert S.stale_note("2026-11-20 21:00", now) == ""
    n = S.stale_note("2026-11-20 10:38", now)
    assert "12 小時" in n and "Claude 代班" in n, n
    assert S.stale_note("", now) == "" and S.stale_note("壞掉", now) == ""
