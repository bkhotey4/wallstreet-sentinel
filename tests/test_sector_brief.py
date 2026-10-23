"""產業簡報: SPDR holdings parsing, sector mapping, season stats, drivers, scoring, text, daily snapshot, site cards.
Run: python -m tests.test_sector_brief"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import types
from datetime import date

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_sb_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import sector_brief as SB  # noqa: E402
from wsb.data import sector_members as SM  # noqa: E402


def xlsx(rows):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in [("Fund Name:", "X"), ("Ticker Symbol:", "XLK"), ("Holdings:", "As of 22-Oct-2026"), (None,),
              ("Name", "Ticker", "Identifier", "SEDOL", "Weight", "Sector", "Shares Held", "Local Currency")] + rows + [(None,), ("Footer text", None)]:
        ws.append(list(r))
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


def test_parse_and_map():
    asof, rows = SM.parse(xlsx([("NVIDIA CORP", "NVDA", "x", "y", 15.4), ("CASH", "-", "", "", 0.1), ("BRK", "BRK.B", "", "", 2.0)]))
    assert asof == "22-Oct-2026" and rows == [["NVDA", 15.4], ["BRK.B", 2.0]], rows
    m = SM.sector_of({"sectors": {"XLK": {"members": [["NVDA", 15.4]]}, "XLF": {"members": [["BRK.B", 12.0], ["NVDA", 0.5]]}}})
    assert m["NVDA"] == "XLK" and m["BRK-B"] == "XLF" and m["BRK.B"] == "XLF"
    print("ok parse / map")


class Mkt:
    def __init__(self, d):
        self.d = d

    def series(self, t):
        return self.d.get(t, pd.Series(dtype=float))


class Fred:
    def __init__(self, d):
        self.d = d

    def get(self, sid):
        return self.d.get(sid, pd.Series(dtype=float))


def eng_fixture():
    idx = pd.bdate_range(end="2026-10-22", periods=400)
    lin = lambda a, b: pd.Series(np.linspace(a, b, len(idx)), index=idx)  # noqa: E731
    px = {"SPY": lin(100, 110), "RSP": lin(100, 104)}
    for e in SB.NAMES:
        px[e] = lin(100, 110)
    px["XLE"] = pd.concat([lin(100, 100).iloc[:-63], pd.Series(np.linspace(100, 125, 63), index=idx[-63:])])   # +25 % in 3 months
    px["XLRE"] = pd.concat([lin(100, 100).iloc[:-63], pd.Series(np.linspace(100, 85, 63), index=idx[-63:])])
    px["CL=F"] = px["XLE"] * 0.7
    m_idx = pd.date_range(end="2026-09-01", periods=150, freq="MS")
    fr = {"MORTGAGE30US": pd.Series(np.r_[np.full(138, 6.0), np.linspace(6.0, 7.5, 12)], index=m_idx),     # sharp one-year rise
          "HOUST": pd.Series(np.r_[np.full(138, 1500.0), np.linspace(1500, 1100, 12)], index=m_idx),
          "DGS10": pd.Series(np.r_[np.full(330, 4.0), np.linspace(4.0, 4.6, 70)], index=idx)}
    return types.SimpleNamespace(market=Mkt(px), fred=Fred(fr), stress=types.SimpleNamespace(score=60.0))


def test_build():
    days = {"2026-10-15": {"rows": [{"sym": f"T{i}", "fq": "Sep/2026", "eps": 1.1, "eps_f": 1.0, "surprise": 10.0, "eps_ly": 0.8} for i in range(6)]
                           + [{"sym": f"F{i}", "fq": "Sep/2026", "eps": 0.9, "eps_f": 1.0, "surprise": -10.0} for i in range(6)]},
            "2026-10-28": {"rows": [{"sym": "T0", "name": "Tech Zero Class A", "mcap": 5e12}, {"sym": "T9", "name": "Tech Zero Class C", "mcap": 4e12}]}}
    SB.DAYS.write_text(json.dumps(days), encoding="utf-8")
    mem = {"sectors": {"XLK": {"asof": "22-Oct-2026", "members": [[f"T{i}", 5.0] for i in range(10)]},
                       "XLF": {"asof": "22-Oct-2026", "members": [[f"F{i}", 5.0] for i in range(6)]}}}
    eng = eng_fixture()
    r = SB.build(eng, mem, today=date(2026, 10, 23))
    by = {s["etf"]: s for s in r["sectors"]}
    assert r["available"] and len(r["sectors"]) == 11
    assert r["market"]["n"] == 12 and abs(r["market"]["beat"] - 50) < 1e-9
    k, f = by["XLK"], by["XLF"]
    assert k["earn"]["beat"] == 100 and abs(k["earn"]["eps_g"] - 37.5) < 1e-9 and k["score"]["earn"] == 1, k["earn"]
    assert f["earn"]["beat"] == 0 and f["score"]["earn"] == -1
    assert len(k["next"]) == 1 and k["next"][0]["sym"] == "T0"                     # GOOG/GOOGL-style duplicate collapsed
    e, re_ = by["XLE"], by["XLRE"]
    assert e["score"]["px"] == 1 and e["score"]["macro"] == 1 and e["verdict"] == "tail", e["score"]
    assert re_["score"]["px"] == -1 and re_["score"]["macro"] == -1 and re_["verdict"] == "head", (re_["score"], re_["drivers"])
    assert "股價、經濟數據同時偏多" in e["text"] and "財報還沒明顯表態" in e["text"], e["text"]
    assert "落後大盤" in re_["text"] and "30 年房貸利率" in re_["text"]
    assert by["XLP"]["drivers"][0]["state"] == "better"                              # SSI 60 ≥ 55: defensive tailwind
    ov = r["overview"]
    assert ov["lines"][0].startswith("近 3 個月領漲：能源") and any("廣度普通。11 個產業有 10 個" in x for x in ov["lines"]), ov["lines"]
    h = json.loads(SB.HIST.read_text(encoding="utf-8"))
    assert h["2026-10-23"]["XLE"] == e["score"]["total"]
    h["2026-10-15"] = {"XLE": -1}
    SB.HIST.write_text(json.dumps(h), encoding="utf-8")
    r2 = SB.build(eng, mem, today=date(2026, 10, 23))
    assert next(s for s in r2["sectors"] if s["etf"] == "XLE")["prev_total"] == -1 and r2["week_ago"]
    print("ok build / score / text / snapshot")
    return r2


def test_site(r):
    from tools import site_industry as SIN
    eng = types.SimpleNamespace(sector_brief=r)
    a, b = SIN.sec_sector_brief(eng), SIN.sec_sector_table(eng)
    assert "產業簡報" in a and "順風" in a and "State Street" in a
    assert b.count("<details") == 11 and "一週前" in b and "能源" in b and "T0" in b
    assert SIN.sec_sector_brief(types.SimpleNamespace(sector_brief={})) == "" == SIN.sec_sector_table(types.SimpleNamespace())
    from tools import site_stamp as STP
    assert STP.sources_for("sec_sector_table", "industry") == ["px", "fred", "earnings"]
    print("ok site cards")


if __name__ == "__main__":
    test_parse_and_map()
    test_site(test_build())
    print("all sector brief tests passed")
