"""積木編號（11-21）: stable numbers, new cards get the next one, digits in titles don't matter.  Run: python -m tests.test_site_blocks"""
from tools import site_blocks as SB


def test_assign_stable():
    cards = {"overview": [("c1", "每日總經情勢", "x"), ("c2", "一個月預判（3 題）", "x")], "taiwan": [("c3", "台股即時", "x")]}
    reg, new = SB.assign({}, ["overview", "taiwan"], cards, {"commands": ["signals", "news"], "alerts": ["stock_embed"]})
    assert reg["pages"] == {"overview": 1, "taiwan": 2}
    assert reg["cards"][SB.key_of("overview", "一個月預判（5 題）")] == "01-02"      # digits don't change the key
    assert reg["discord"]["commands"] == {"signals": "D-C01", "news": "D-C02"} and reg["discord"]["alerts"]["stock_embed"] == "D-A01"
    assert len(new) == 2 + 3 + 3
    # a new page inserted first and a new card at the top of overview: existing numbers stay
    cards2 = {"tw_new": [("c9", "新頁卡", "x")], "overview": [("c0", "新卡", "x")] + cards["overview"], "taiwan": cards["taiwan"]}
    reg2, new2 = SB.assign(reg, ["tw_new", "overview", "taiwan"], cards2, {"commands": ["news", "signals", "help"], "alerts": []})
    assert reg2["pages"]["tw_new"] == 3 and reg2["cards"][SB.key_of("overview", "每日總經情勢")] == "01-01"
    assert reg2["cards"][SB.key_of("overview", "新卡")] == "01-03" and reg2["cards"][SB.key_of("tw_new", "新頁卡")] == "03-01"
    assert reg2["discord"]["commands"]["help"] == "D-C03" and reg2["discord"]["commands"]["signals"] == "D-C01"
    assert SB.assign(reg2, ["tw_new", "overview", "taiwan"], cards2, {"commands": ["news"], "alerts": []})[1] == []


def test_badge_and_inventory():
    cards = {"overview": [("c-overview-1", "每日總經情勢", "Daily macro")]}
    reg, _ = SB.assign({}, ["overview"], cards, {"commands": ["signals"], "alerts": ["stock_embed"]})
    h = SB.badge({"overview": '<section id="c-overview-1" class="card wide"><h2>每日總經情勢</h2><p>x</p></section>'}, cards, reg)["overview"]
    assert '<h2>每日總經情勢 <span class="blk"' in h and "#01-01</span></h2>" in h
    inv = SB.inventory_card(reg, {"overview": ("總覽", "Overview")}, cards)
    assert "積木清單" in inv and "#01-01" in inv and "D-C01" in inv and "/signals" in inv and "D-A01" in inv
    inv_real = SB.discord_inventory()
    assert len(inv_real["commands"]) > 20 and "stock_embed" in inv_real["alerts"]


if __name__ == "__main__":
    test_assign_stable()
    test_badge_and_inventory()
    print("ok site blocks")
