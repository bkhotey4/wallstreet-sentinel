"""每日稽核：偏舊卡片解析與原因分類、寫死數字候選，不連網。Run: python -m tests.test_daily_audit"""
from __future__ import annotations

import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import daily_audit as A  # noqa: E402


def test_stale_and_classify():
    html = ('<section class="card wide"><h2>債務到期牆</h2><p class="upd" title="x">ok</p></section>'
            '<section class="card"><h2><span>財報後白話解讀</span></h2><p class="upd old" title="財報後解讀（雲端 AI） 檢查 11-13 22:47・資料日 2026-11-13">'
            '</p></section>')
    st = A.stale_cards(html)
    assert len(st) == 1 and st[0]["card"] == "財報後白話解讀" and st[0]["tips"][0] == {"src": "財報後解讀（雲端 AI）", "checked": "11-13 22:47", "data": "2026-11-13"}
    from datetime import datetime
    now = datetime(2026, 11, 16, 23, 0).timestamp()
    c = A.classify(st[0]["tips"], now)
    assert c[0]["why"] == "fetch" and c[0]["fetch_age_h"] > 72


def test_hardcode_candidates():
    p = pathlib.Path(tempfile.mkdtemp()) / "x.py"
    p.write_text('a = f"規模約 {x:,.0f} 億美元"\nb = "基差交易約 8,300 億美元"\nc = "每 10 天公布一次"\nd = "目前約 3.2%"\n', encoding="utf-8")
    A.ROOT = p.parent
    got = [h["text"] for h in A.hardcode_candidates(p, [1, 2, 3, 4])]
    assert got == ["8,300 億美元", "約 3.2%"], got


def test_lagging_rows():
    from datetime import date
    dash = {"rows": [{"zh": "標普 500", "kind": "pct", "date": "11-20"}, {"zh": "日經 225", "kind": "pct", "date": "11-19"},
                     {"zh": "日本 10 年期公債殖利率", "kind": "bp", "date": "11-19"}]}
    assert A.lagging_rows(dash, date(2026, 11, 21)) == ["日經 225（11-19，其他列 11-20）"]
    assert A.lagging_rows(dash, date(2026, 11, 20)) == []             # the newest day is not over yet
    assert "日經 225" in A.summary({"lagging_rows": A.lagging_rows(dash, date(2026, 11, 21))})


def test_summary_routines_and_tw_forecast_listed():
    import tools.daily_audit as A
    from tools import site_routines as SR
    assert "tw_forecast.json" in [e[0] for e in SR.EXPECT]          # 11-21: the daily TW outlook missed a run unflagged
    s = A.summary({"routines": [{"zh": "台灣總經展望", "st": "late", "age_h": 50.0, "every_h": 24}], "holdings_mismatch": []})
    assert "排程紅黃燈：台灣總經展望（late" in s and "持股檔" not in s


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)


def test_stopped_trading():
    import pandas as pd
    from tools import daily_audit as A
    idx = pd.date_range("2026-10-01", "2026-11-17", freq="B")
    c = pd.DataFrame({"AAA": 1.0, "CCO": 1.0}, index=idx)
    c.loc[c.index > "2026-10-15", "CCO"] = None
    assert A.stopped_trading(c) == [{"sym": "CCO", "last": "2026-10-15"}]
    assert A.stopped_trading(pd.DataFrame()) == []
    sub = {"filings": {"recent": {"form": ["SCHEDULE 13G", "15-12G", "8-K/A", "4"], "items": ["", "", "5.01,9.01", ""]}}}
    assert A.stop_reason(sub) == ["撤銷 SEC 登記（不再是上市公司）", "控制權變更（被收購）"], A.stop_reason(sub)


def test_ipo_blank_price():
    """11-20: rows rendered by the real renderer; a fresh listing without an offer price is flagged, an old one and a
    priced one are not."""
    from datetime import date
    from tools import site_ipo as S
    rows = [{"name": "Delta, PBC", "sym": "DLT", "priced": "2026-11-19", "offer": None, "lockup": 180},
            {"name": "Epsilon Ltd", "sym": "EPS", "priced": "2026-11-18", "offer": 21.0, "lockup": 180,
             "final": {"shares": 2e7, "gs_shares": 3e6, "gs_days": 30}},
            {"name": "Old Co", "sym": "OLD", "priced": "2026-09-01", "offer": None, "lockup": 180}]
    html = S._us_done({"recent": rows})
    assert A.ipo_blank_price(html, date(2026, 11, 20)) == ["Delta, PBC（11-19 定價）"], A.ipo_blank_price(html, date(2026, 11, 20))
    assert "Delta" in A.summary({"ipo_blank": A.ipo_blank_price(html, date(2026, 11, 20))})
    assert A.ipo_blank_price("", date(2026, 11, 20)) == []


if __name__ == "__main__":
    test_stopped_trading()
    print("ok test_stopped_trading")
    test_ipo_blank_price()
    print("ok test_ipo_blank_price")
