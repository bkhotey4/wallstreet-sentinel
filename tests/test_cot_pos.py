"""CFTC 期貨部位 (11-29): parse, 3-year percentile, crowding, plain sentence.  Run: python -m tests.test_cot_pos"""
from wsb.data import cot_pos as C


def test_parse_view_text():
    rows = []
    for i in range(160):
        d = f"20{23 + i // 52}-01-01"[:4] + f"-{(i % 52) // 4 + 1:02d}-{(i % 4) * 7 + 1:02d}"
        rows.append({"report_date_as_yyyy_mm_dd": f"{d}T00:00:00.000", "cftc_contract_market_code": "13874A", "open_interest_all": "1000",
                     "asset_mgr_positions_long": str(500 + i), "asset_mgr_positions_short": "100",
                     "lev_money_positions_long": "100", "lev_money_positions_short": str(300 - i)})
    rows.append({"cftc_contract_market_code": "999999", "open_interest_all": "1"})
    p = C.parse(rows)
    assert list(p) == ["ES"] and len(p["ES"]) == 160
    v = C.view({"rows": p})["ES"]
    assert v["am_p"] == 100.0 and "am" in v["crowd"] and round(v["am"]) == 56
    t = C.text(v)
    assert "資產管理人淨多單 56%" in t and "比過去 3 年九成的時候都偏多" in t and "避險基金淨空單 4%" in t
    assert C.view({"rows": {"ES": p["ES"][:40]}}) == {}


if __name__ == "__main__":
    test_parse_view_text()
    print("ok cot pos")
