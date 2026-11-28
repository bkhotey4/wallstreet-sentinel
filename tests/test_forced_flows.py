

def test_buyback_window():
    """11-28 Wall Street checklist: the usual buyback blackout cycle, labelled as a rule of thumb."""
    from datetime import date
    from tools import site_forced as F
    assert "12/17" in F.buyback_window(date(2026, 11, 28)) and "已進入" in F.buyback_window(date(2026, 12, 20))
    assert "2/14" in F.buyback_window(date(2027, 1, 20)) and "經驗法則" in F.buyback_window(date(2027, 2, 20))


if __name__ == "__main__":
    test_buyback_window()
    print("ok buyback window")
