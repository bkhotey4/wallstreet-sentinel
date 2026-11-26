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


def test_read_items():
    """Gemini READ (11-26): scope line, official-domain lag lines only, the rest as wording problems."""
    from tools import daily_audit as A
    r = "\n".join(["### READ-範圍｜本輪看了：#39-01～#39-03（共 3 張）",
                   "### READ-1｜#39-03：外銷訂單停在 9 月", "資料期：本站 2026-09｜官方 2026-10｜https://www.stat.gov.tw/Point.aspx?sid=t.5",
                   "### READ-2｜#44-01：燈號說明只有顏色", "文字",
                   "### READ-3｜#01-02：新聞說法", "資料期：本站 2026-09｜官方 2026-10｜https://news.cnyes.com/x", "### SITE-1｜x", ""])
    d = A.read_items(r)
    assert d["scope"].startswith("本輪看了") and [x["card"] for x in d["lag"]] == ["#39-03"]
    assert d["lag"][0]["official"] == "2026-10" and [x["card"] for x in d["wording"]] == ["#44-01", "#01-02"]
    assert "READ" not in A.gemini_unknown_groups(r)


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


def test_gemini_unknown_groups():
    reply = "### TWC-1｜x\n### D-1｜y\n### CODE-2｜z\n### ZZZ-1｜new\n"
    assert A.gemini_unknown_groups(reply) == ["ZZZ"], A.gemini_unknown_groups(reply)
    assert "ZZZ" in A.summary({"gemini_groups": ["ZZZ"]})


def test_old_reads_and_shared_cause():
    import time as _t
    from datetime import datetime, timedelta, timezone
    from tools import daily_audit as A, sys_health as H
    now = _t.time()
    f = lambda h: datetime.fromtimestamp(now - h * 3600, timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")      # noqa: E731
    hot = [{"id": "a", "state": "升溫"}]
    assert len(A.old_reads(hot, {"x.json": f(60), "y.json": f(3)}, now)) == 1
    assert A.old_reads([{"id": "a", "state": "安靜"}], {"x.json": f(60)}, now) == []
    row = lambda i: {"file": f"{i}.json", "zh": str(i), "st": "stop", "age": 30, "every": 6}                             # noqa: E731
    assert "共同原因" in H.routine_issues([row(i) for i in range(4)])[0]["text"]
    assert "共同原因" not in H.routine_issues([row(i) for i in range(3)])[0]["text"]


if __name__ == "__main__":
    test_old_reads_and_shared_cause()
    print("ok test_old_reads_and_shared_cause")
    test_gemini_unknown_groups()
    print("ok test_gemini_unknown_groups")
    test_lagging_rows()
    print("ok test_lagging_rows")
    test_stopped_trading()
    print("ok test_stopped_trading")
    test_ipo_blank_price()
    print("ok test_ipo_blank_price")


def test_blind_movers():
    """11-26: an untracked large cap with a 4σ day is listed; a calm one and a short history are not."""
    import random
    from tools import daily_audit as A
    random.seed(1)
    calm = [100.0]
    for _ in range(120):
        calm.append(calm[-1] * (1 + random.gauss(0, 0.01)))
    shock = calm[:-2] + [calm[-3] * 0.86, calm[-3] * 0.85]
    got = A.blind_movers({"SNDK": shock, "CALM": calm, "NEW": calm[:30]}, {"SNDK": {"name": "Sandisk", "ind": "科技", "mcap": 1e11}})
    assert [x["sym"] for x in got] == ["SNDK"] and got[0]["pct"] == -14.0 and got[0]["z"] < -4, got


if __name__ == "__main__":
    test_blind_movers()
    print("ok test_blind_movers")


def test_tw_clusters():
    """Three untracked names beating the index by ~16% on the same day are one theme; one quiet name is not listed."""
    import random
    from datetime import date, timedelta
    from tools import daily_audit as A
    random.seed(2)
    days = [(date(2026, 6, 1) + timedelta(days=i)).isoformat() for i in range(120)]
    bench = {}
    v = 100.0
    for d in days:
        v *= 1 + random.gauss(0, 0.01)
        bench[d] = v
    def follow(jump):
        s, x = {}, 50.0
        for i, d in enumerate(days):
            r = (bench[d] / bench[days[i - 1]] - 1) if i else 0.0
            x *= 1 + r + random.gauss(0, 0.008) + (jump if i == len(days) - 2 else 0.0)
            s[d] = x
        return s
    ser = {"6614.TW": follow(0.16), "2471.TW": follow(0.16), "7765.TW": follow(0.16), "1101.TW": follow(0.0)}
    meta = {s: {"name": s, "ind": "資訊服務"} for s in ("6614.TW", "2471.TW", "7765.TW")}
    got = A.tw_clusters(ser, bench, meta)
    assert len(got) == 1 and got[0]["day"] == days[-2] and got[0]["n"] == 3 and got[0]["ind"] == "資訊服務", got
    assert "1101.TW" not in [x["sym"] for x in got[0]["names"]]


if __name__ == "__main__":
    test_tw_clusters()
    print("ok test_tw_clusters")
