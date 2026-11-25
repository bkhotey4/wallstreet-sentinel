"""11-25 稽核修正：缺值不要當成 0（P3-15、P3-16、P3-18、P3-20）。Run: python -m tests.test_audit_1125"""
from datetime import date


def test_ipo_selling_holders_seen_but_not_read():
    from wsb.data import ipo_data as I
    from tools import site_ipo as S
    # the selling-holder line in a wording the share-count regex does not know
    raw = ("<p>We are offering 10,000,000 shares of our common stock. The initial public offering price per share will be "
           "between $20.00 and $22.00 per share. Certain shares are being sold by the selling stockholders identified in this "
           "prospectus. We will not receive any proceeds from those shares.</p>")
    cv = I.parse_cover(I.text_of(raw))
    assert "sell_shares" not in cv and cv.get("sell_seen") is True
    h = S.deal_block({**cv, "lo": 20.0, "hi": 22.0, "shares": 10_000_000})
    assert "沒讀到股數" in h
    plain = I.parse_cover(I.text_of("<p>We are offering 10,000,000 shares of our common stock.</p>"))
    assert "sell_seen" not in plain                       # no selling holders at all: say nothing
    assert "沒讀到股數" not in S.deal_block({**plain, "lo": 20.0, "hi": 22.0, "shares": 10_000_000})


def test_health_table_covers_more_ai_files():
    from tools import site_routines as SR
    names = [e[0] for e in SR.EXPECT]
    for f in ("earn_after_more.json", "earn_after_asia.json", "earn_after_rest.json", "event_board.json"):
        assert f in names, f


def test_revenue_yoy_share_counts_only_known():
    from wsb.data import tw_desk as D
    from tools import site_twdesk as S
    months = {}
    for i, ym in enumerate(["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]):
        months[ym] = {"2330": [100.0 + i, 80.0, 10.0, "台積電"], "6999": [10.0, 9.0, None, "新上市"]}   # 6999: no y/y published
    v = D.rev_view(d={"months": months}, desk={"univ": {"codes": ["2330", "6999"]}})
    assert len(v["trends"]) == 2 and v["n_yoy"] == 1
    assert v["yoy_pos"] == 100.0                          # was 50%: the company without a y/y counted as "not growing"
    lead = S.rev_lead({**v, "layers": [{"name": "晶圓代工", "yoy3_med": 10.0}]})
    assert "有年增資料的 1 檔裡" in lead


def test_borrow_and_pledge_blanks_are_not_zero():
    from wsb.data import tw_chips as C
    row = lambda c, p, t: [c, "X", 0, 0, 0, 0, 0, 0, p, 0, 0, 0, t]     # noqa: E731
    s = C.parse_sbl({"date": "x", "data": [row("2330", "1,000", "1,100"), row("9999", "", "50,000")]})
    assert [m["code"] for m in s["add"]] == ["2330"] and s["total"] == 1100.0 and s["prev"] == 1000.0 and s["skipped"] == 1
    o = C.parse_sbl_otc([{"Date": "1", "SecuritiesBorrowingBalanceOfTheMarketDay": "5", "SecuritiesBorrowingBalancePreviousDay": ""}])
    assert o["total"] == 0.0 and o["skipped"] == 1
    p = C.parse_pledge([{"公司代號": "1234", "公司名稱": "A", "目前持股": "", "設質股數": "500"},
                        {"公司代號": "1234", "公司名稱": "A", "目前持股": "1000", "設質股數": "0"}])
    assert p[0]["pct"] == 0.0 and p[0]["partial"] == 1     # was 50%: 500 pledged against someone else's 1,000


def main():
    for f in (test_ipo_selling_holders_seen_but_not_read, test_health_table_covers_more_ai_files,
              test_revenue_yoy_share_counts_only_known, test_borrow_and_pledge_blanks_are_not_zero):
        f()
        print("ok", f.__name__)


if __name__ == "__main__":
    main()
