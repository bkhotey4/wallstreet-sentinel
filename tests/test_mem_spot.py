"""DRAMeXchange spot tables (11-26): parsing with each table's own update time, history per table date, 30-day change.
Run: python -m tests.test_mem_spot"""
from tools import site_memspot as S
from wsb.data import mem_spot as M

PAGE = ("<table><tr><td>DRAM Spot Price</td><td>Last Update: Nov.26 2026 18:10 (GMT+8)</td></tr></table>"
        "<table><tr><th>Item</th><th>Daily High</th><th>Daily Low</th><th>Session High</th><th>Session Low</th><th>Session Average</th><th>Session Change</th></tr>"
        "<tr><td>DDR4 16Gb (2Gx8) 3200</td><td>107.00</td><td>42.50</td><td>107</td><td>42.5</td><td>77.500</td><td>-0.32 %</td></tr></table>"
        "<table><tr><td>Wafer Spot Price</td><td>Last Update:Nov.16 2026 14:40 (GMT+8)</td></tr></table>"
        "<table><tr><th>Item</th><th>Weekly High</th><th>Weekly Low</th><th>Session High</th><th>Session Low</th><th>Session Average</th><th>Average Change</th></tr>"
        "<tr><td>512Gb TLC</td><td>1</td><td>1</td><td>1</td><td>1</td><td>14.240</td><td>-0.20 %</td></tr></table>")


def test_parse_and_history():
    snap = M.parse(PAGE)
    assert snap["DRAM 現貨"]["upd"] == "2026-11-26 18:10" and snap["NAND 晶圓"]["upd"] == "2026-11-16 14:40"
    assert snap["DRAM 現貨"]["items"]["DDR4 16Gb (2Gx8) 3200"] == {"avg": 77.5, "chg": -0.32}
    d = M.add_history({}, snap)
    d = M.add_history(d, snap)                                  # same table date again → still one point
    assert d["hist"]["NAND 晶圓|512Gb TLC"] == [["2026-11-16", 14.24]]


def test_change_and_lead():
    h = [["2026-10-20", 100.0], ["2026-10-27", 95.0], ["2026-11-26", 80.0]]
    assert round(S.change(h, 30), 1) == -15.8   # base = the newest point ≥ 30 days back (10-27) and S.change(h[-1:], 30) is None
    snap = M.parse(PAGE)
    lead = S._lead(snap, {})
    assert "DDR4 顆粒 77.50 美元" in lead and "沒有一致往下" in lead     # −0.32% / −0.20% are noise, not 在跌


if __name__ == "__main__":
    test_parse_and_history()
    test_change_and_lead()
    print("ok mem spot")
